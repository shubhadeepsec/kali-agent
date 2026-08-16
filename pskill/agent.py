"""agent.py — LLM backend. Supports OpenAI, Anthropic, Gemini, Groq, Ollama."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable, Generator

from . import config
from .tools import TOOL_SCHEMAS, execute_tool

PLAYBOOKS_DIR = Path(__file__).resolve().parents[1] / "playbooks"

SYSTEM_PROMPT = """You are pskill — an expert autonomous AI penetration tester and bug bounty hunter.

You operate like a senior red teamer: methodical, precise, evidence-driven. You have access to:
- Shell command execution (nmap, ffuf, nuclei, httpx, sqlmap, burp, curl, etc.)
- Target intel tracking (hosts, ports, endpoints, tech, vulnerabilities)
- 17 specialized security playbooks (web-recon, api-testing, idor-bola, injection, etc.)
- File read/write for saving outputs and reports

## Mandatory Rules
1. SCOPE FIRST — Never run target-facing tools until scope is confirmed. Check with user.
2. EXPLAIN before execute — Always describe what a command does before running it.
3. LOG findings — After each tool execution, update intel with discovered hosts, endpoints, tech, vulns.
4. CHAIN intelligently — After recon, route to the right skill. After finding APIs, test IDOR. After finding auth, test OAuth.
5. REPORT — Document every critical/high finding with: title, severity, endpoint, PoC, impact, remediation.

## Workflow
1. Confirm scope and authorization
2. Initialize engagement → track state in intel.json
3. Execute tools → parse output → update intel → chain next step
4. Audit surface coverage before reporting
5. Generate comprehensive Markdown report

## Style
- Be direct and technical. No fluff.
- Show commands in code blocks.
- Highlight findings in structured format: [SEVERITY] Finding title → endpoint → impact.
- Ask for approval before running any active/intrusive tools.
"""


def _build_openai_messages(history: list[dict]) -> list[dict]:
    """Convert internal history to OpenAI messages format."""
    return [{"role": m["role"], "content": m["content"]} for m in history]


class Agent:
    """LLM-backed agent. Auto-selects provider from config."""

    def __init__(self):
        self.history: list[dict] = []
        self.current_target: str = ""

    def _get_client(self):
        provider = config.get("api_provider", "")
        api_key = config.get("api_key", "")
        base_url = config.PROVIDER_DEFAULTS.get(provider, {}).get("base_url", "")
        model = config.get("model", "") or config.PROVIDER_DEFAULTS.get(provider, {}).get("model", "")

        if provider == "anthropic":
            try:
                import anthropic
                return "anthropic", anthropic.Anthropic(api_key=api_key), model
            except ImportError:
                raise RuntimeError("Run: pip install anthropic")

        # OpenAI-compatible (openai, groq, ollama, gemini via openai compat)
        if provider in ("openai", "groq", "ollama", "gemini"):
            try:
                from openai import OpenAI
                if provider == "ollama":
                    client = OpenAI(api_key="ollama", base_url=base_url + "/v1")
                elif provider == "gemini":
                    client = OpenAI(
                        api_key=api_key,
                        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
                    )
                    model = config.get("model", "") or "gemini-2.0-flash-exp"
                elif provider == "groq":
                    client = OpenAI(api_key=api_key, base_url=base_url)
                else:
                    client = OpenAI(api_key=api_key)
                return "openai", client, model
            except ImportError:
                raise RuntimeError("Run: pip install openai")

        raise RuntimeError(
            f"Provider '{provider}' not configured. Run: pskill /config"
        )

    def _tools_for_provider(self, provider: str) -> list[dict]:
        """Format tools for each provider's API."""
        if provider == "anthropic":
            return [
                {
                    "name": t["name"],
                    "description": t["description"],
                    "input_schema": t["parameters"],
                }
                for t in TOOL_SCHEMAS
            ]
        # OpenAI format
        return [
            {"type": "function", "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
            }}
            for t in TOOL_SCHEMAS
        ]

    def chat(
        self,
        user_msg: str,
        confirm_fn: Callable[[str, str], bool] | None = None,
        stream_fn: Callable[[str], None] | None = None,
    ) -> str:
        """Send a message, handle tool calls, return final assistant response."""
        self.history.append({"role": "user", "content": user_msg})

        provider, client, model = self._get_client()
        max_tokens = int(config.get("max_tokens", 4096))
        full_response = ""

        # Agentic loop — keep going until model stops calling tools
        for _ in range(20):  # max 20 tool call rounds
            if provider == "anthropic":
                response = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=SYSTEM_PROMPT,
                    messages=_build_openai_messages(self.history),
                    tools=self._tools_for_provider("anthropic"),
                )
                # Extract text and tool calls
                text_parts = []
                tool_calls = []
                for block in response.content:
                    if block.type == "text":
                        text_parts.append(block.text)
                    elif block.type == "tool_use":
                        tool_calls.append(block)

                text = "".join(text_parts)
                if text:
                    full_response = text
                    if stream_fn:
                        stream_fn(text)

                if not tool_calls or response.stop_reason == "end_turn":
                    break

                # Execute tools
                self.history.append({"role": "assistant", "content": response.content})
                tool_results = []
                for tc in tool_calls:
                    result = execute_tool(tc.name, tc.input, confirm_fn)
                    if stream_fn:
                        stream_fn(f"\n[tool:{tc.name}] → {result[:200]}…\n" if len(result) > 200 else f"\n[tool:{tc.name}] → {result}\n")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tc.id,
                        "content": result,
                    })
                self.history.append({"role": "user", "content": tool_results})

            else:
                # OpenAI-compatible
                messages = [{"role": "system", "content": SYSTEM_PROMPT}] + \
                           _build_openai_messages(self.history)
                response = client.chat.completions.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=messages,
                    tools=self._tools_for_provider("openai"),
                    tool_choice="auto",
                )
                msg = response.choices[0].message
                text = msg.content or ""
                if text:
                    full_response = text
                    if stream_fn:
                        stream_fn(text)

                tool_calls = msg.tool_calls or []
                if not tool_calls or response.choices[0].finish_reason == "stop":
                    break

                # Execute tools
                self.history.append({"role": "assistant", "content": msg})
                for tc in tool_calls:
                    args = json.loads(tc.function.arguments)
                    result = execute_tool(tc.function.name, args, confirm_fn)
                    if stream_fn:
                        result_preview = result[:200] + "…" if len(result) > 200 else result
                        stream_fn(f"\n[tool:{tc.function.name}] → {result_preview}\n")
                    self.history.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })

        self.history.append({"role": "assistant", "content": full_response})
        return full_response

    def clear_history(self) -> None:
        self.history = []

    def inject_context(self, text: str) -> None:
        """Inject context as a system-style message."""
        self.history.append({
            "role": "user",
            "content": f"[CONTEXT LOADED]\n{text}"
        })
        self.history.append({
            "role": "assistant",
            "content": "Context received. Ready."
        })
