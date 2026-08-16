"""agent.py — Multi-provider LLM backend for Kali Agent with token & cost tracking and session persistence."""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from . import config
from .tools import TOOL_SCHEMAS, execute_tool

SYSTEM_PROMPT = """You are Kali Agent — an autonomous AI OS Controller and Senior Security Operator for Kali Linux.

You have full control over the local Kali Linux system and environment. You can:
1. EXECUTE OS COMMANDS: Run any bash command, script, binary, or utility in any directory. Set background: true for long scans.
2. ORCHESTRATE SECURITY TOOLS: Leverage all pre-installed Kali tools (Nmap, Metasploit, Burp Suite, Wireshark/tshark, Gobuster, ffuf, SQLMap, Hydra, Hashcat, John the Ripper, Ghidra, Radare2, Impacket, NetExec, etc.).
3. AUTO-INSTALL & MANAGE TOOLS: Install missing packages and tools using `manage_packages` (via apt, pip, go, cargo, or git).
4. SYSTEM & SERVICE CONTROL: Manage systemd services (postgresql, docker, apache2, ssh, tor, openvpn), check network sockets, monitor processes, and inspect hardware diagnostics.
5. EXPLOIT & CVE LOOKUP: Query local Exploit-DB and CVE databases using `search_exploits` for service versions.
6. NETWORK & REVERSE SHELLS: Inspect interface IPs (tun0/eth0) with `get_network_info` and craft listener/payload one-liners using `generate_payload`.
7. FILESYSTEM & SCRIPTING: Read, write, search, and edit files, scripts, custom wordlists, and reports.
8. TARGET STATE & METHODOLOGY: Track targets in intel.json and follow 17 specialized security playbooks.

## Core Principles
1. SCOPE & AUTHORIZATION: Confirm target authorization prior to executing intrusive target-facing scans or exploits.
2. EXPLAIN BEFORE EXECUTE: Briefly explain what a command or action does.
3. PROACTIVE PROBLEM SOLVING: If a required tool or dependency is missing, automatically install or configure it. If a command fails, diagnose the error and adapt.
4. RECORD FINDINGS: As soon as an asset, endpoint, service, or vulnerability is identified, record it in target state using update_intel.
5. CONCISE & TECHNICAL: Output direct, clean technical summaries. Format commands in markdown code blocks.
"""

MODEL_PRICING = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
    "claude-haiku": {"input": 0.80, "output": 4.00},
    "gemini-2.0-flash-exp": {"input": 0.00, "output": 0.00},
    "llama-3.1-70b-versatile": {"input": 0.59, "output": 0.79},
    "llama3.1": {"input": 0.00, "output": 0.00},
}


def _format_openai_messages(history: list[dict]) -> list[dict]:
    """Convert unified history into OpenAI/Gemini/Groq/Ollama API messages."""
    formatted = []
    for m in history:
        role = m.get("role")
        if role == "user":
            formatted.append({"role": "user", "content": str(m.get("content", ""))})
        elif role == "assistant":
            msg: dict[str, Any] = {"role": "assistant"}
            if m.get("content"):
                msg["content"] = m["content"]
            if m.get("tool_calls"):
                msg["tool_calls"] = m["tool_calls"]
            if not msg.get("content") and not msg.get("tool_calls"):
                msg["content"] = ""
            formatted.append(msg)
        elif role == "tool":
            formatted.append({
                "role": "tool",
                "tool_call_id": m.get("tool_call_id", ""),
                "content": str(m.get("content", "")),
            })
    return formatted


def _format_anthropic_messages(history: list[dict]) -> list[dict]:
    """Convert unified history into Anthropic API messages."""
    formatted = []
    i = 0
    while i < len(history):
        m = history[i]
        role = m.get("role")
        if role == "user":
            formatted.append({"role": "user", "content": str(m.get("content", ""))})
            i += 1
        elif role == "assistant":
            blocks: list[dict[str, Any]] = []
            if m.get("content"):
                blocks.append({"type": "text", "text": m["content"]})
            if m.get("tool_calls"):
                for tc in m["tool_calls"]:
                    fn = tc.get("function", {})
                    args = fn.get("arguments", {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except Exception:
                            args = {}
                    blocks.append({
                        "type": "tool_use",
                        "id": tc.get("id", ""),
                        "name": fn.get("name", ""),
                        "input": args,
                    })
            formatted.append({"role": "assistant", "content": blocks if blocks else ""})
            i += 1
        elif role == "tool":
            tool_results = []
            while i < len(history) and history[i].get("role") == "tool":
                tm = history[i]
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tm.get("tool_call_id", ""),
                    "content": str(tm.get("content", "")),
                })
                i += 1
            formatted.append({"role": "user", "content": tool_results})
        else:
            i += 1
    return formatted


class Agent:
    """Multi-provider LLM Agent with automated tool calling, token metrics, and session persistence."""

    def __init__(self, session_id: str | None = None):
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.history: list[dict] = []
        self.current_target: str = ""
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.created_at: str = datetime.now(timezone.utc).isoformat()

    def _get_client(self):
        provider = config.get("api_provider", "")
        api_key = config.get("api_key", "")
        base_url = config.PROVIDER_DEFAULTS.get(provider, {}).get("base_url", "")
        model = config.get("model", "") or config.PROVIDER_DEFAULTS.get(provider, {}).get("model", "")

        if not provider:
            raise RuntimeError("No AI provider configured. Run /config setup to configure.")

        if provider == "anthropic":
            try:
                import anthropic
                return "anthropic", anthropic.Anthropic(api_key=api_key), model
            except ImportError:
                raise RuntimeError("Anthropic package missing. Run: pip install anthropic")

        if provider in ("openai", "groq", "ollama", "gemini"):
            try:
                from openai import OpenAI
                if provider == "ollama":
                    client = OpenAI(api_key="ollama", base_url=base_url)
                elif provider == "gemini":
                    client = OpenAI(
                        api_key=api_key,
                        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                    )
                elif provider == "groq":
                    client = OpenAI(api_key=api_key, base_url=base_url)
                else:
                    client = OpenAI(api_key=api_key)
                return "openai", client, model
            except ImportError:
                raise RuntimeError("OpenAI package missing. Run: pip install openai")

        raise RuntimeError(f"Unsupported provider '{provider}'. Run /config setup to configure.")

    def _tools_for_provider(self, provider: str) -> list[dict]:
        if provider == "anthropic":
            return [
                {
                    "name": t["name"],
                    "description": t["description"],
                    "input_schema": t["parameters"],
                }
                for t in TOOL_SCHEMAS
            ]
        return [
            {"type": "function", "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
            }}
            for t in TOOL_SCHEMAS
        ]

    def estimate_cost(self) -> float:
        """Calculate estimated USD cost for the session based on model rates."""
        provider, _, model = self._get_client()
        pricing = MODEL_PRICING.get(model, {"input": 1.00, "output": 3.00})
        cost = (self.total_input_tokens / 1_000_000) * pricing["input"] + \
               (self.total_output_tokens / 1_000_000) * pricing["output"]
        return round(cost, 5)

    def chat(
        self,
        user_msg: str,
        confirm_fn: Callable[[str, str], bool] | None = None,
        stream_fn: Callable[[str], None] | None = None,
    ) -> str:
        """Send user message, resolve tool calls autonomously, track token metrics, and return final output."""
        self.history.append({"role": "user", "content": user_msg})

        provider, client, model = self._get_client()
        max_tokens = int(config.get("max_tokens", 4096))
        final_text = ""

        # Autonomous tool calling loop (up to 20 rounds)
        for _ in range(20):
            if provider == "anthropic":
                messages = _format_anthropic_messages(self.history)
                response = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=SYSTEM_PROMPT,
                    messages=messages,
                    tools=self._tools_for_provider("anthropic"),
                )

                if hasattr(response, "usage") and response.usage:
                    self.total_input_tokens += getattr(response.usage, "input_tokens", 0)
                    self.total_output_tokens += getattr(response.usage, "output_tokens", 0)

                text_blocks = []
                tool_uses = []
                for block in response.content:
                    if block.type == "text":
                        text_blocks.append(block.text)
                    elif block.type == "tool_use":
                        tool_uses.append(block)

                round_text = "".join(text_blocks)
                if round_text:
                    final_text = round_text
                    if stream_fn:
                        stream_fn(round_text)

                if not tool_uses or response.stop_reason == "end_turn":
                    self.history.append({"role": "assistant", "content": final_text})
                    break

                stored_tool_calls = []
                for tu in tool_uses:
                    stored_tool_calls.append({
                        "id": tu.id,
                        "type": "function",
                        "function": {
                            "name": tu.name,
                            "arguments": tu.input,
                        }
                    })

                self.history.append({
                    "role": "assistant",
                    "content": round_text,
                    "tool_calls": stored_tool_calls,
                })

                for tu in tool_uses:
                    if stream_fn:
                        stream_fn(f"\n[Running tool: {tu.name}]")
                    res = execute_tool(tu.name, tu.input, confirm_fn)
                    self.history.append({
                        "role": "tool",
                        "tool_call_id": tu.id,
                        "name": tu.name,
                        "content": res,
                    })

            else:
                # OpenAI / Gemini / Groq / Ollama
                messages = [{"role": "system", "content": SYSTEM_PROMPT}] + _format_openai_messages(self.history)
                response = client.chat.completions.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=messages,
                    tools=self._tools_for_provider("openai"),
                    tool_choice="auto",
                )

                if hasattr(response, "usage") and response.usage:
                    self.total_input_tokens += getattr(response.usage, "prompt_tokens", 0)
                    self.total_output_tokens += getattr(response.usage, "completion_tokens", 0)

                msg = response.choices[0].message
                round_text = msg.content or ""
                if round_text:
                    final_text = round_text
                    if stream_fn:
                        stream_fn(round_text)

                tool_calls = msg.tool_calls or []
                if not tool_calls or response.choices[0].finish_reason == "stop":
                    self.history.append({"role": "assistant", "content": final_text})
                    break

                stored_tool_calls = []
                for tc in tool_calls:
                    stored_tool_calls.append({
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    })

                self.history.append({
                    "role": "assistant",
                    "content": round_text,
                    "tool_calls": stored_tool_calls,
                })

                for tc in tool_calls:
                    args = {}
                    if tc.function.arguments:
                        try:
                            args = json.loads(tc.function.arguments)
                        except Exception:
                            args = {}
                    if stream_fn:
                        stream_fn(f"\n[Running tool: {tc.function.name}]")
                    res = execute_tool(tc.function.name, args, confirm_fn)
                    self.history.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tc.function.name,
                        "content": res,
                    })

        self.save_session()
        return final_text

    def clear_history(self) -> None:
        self.history = []

    def inject_context(self, text: str) -> None:
        self.history.append({
            "role": "user",
            "content": f"[SYSTEM CONTEXT UPDATE]\n{text}"
        })
        self.history.append({
            "role": "assistant",
            "content": "Context received. I will incorporate this into the assessment."
        })

    def save_session(self) -> None:
        """Persist session state and history to disk."""
        config.ensure_dirs()
        session_file = config.SESSIONS_DIR / f"{self.session_id}.json"
        data = {
            "session_id": self.session_id,
            "target": self.current_target,
            "created_at": self.created_at,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "history": self.history,
        }
        session_file.write_text(json.dumps(data, indent=2))

    @classmethod
    def load_session(cls, session_id: str) -> Agent | None:
        """Load a previous session from disk."""
        session_file = config.SESSIONS_DIR / f"{session_id}.json"
        if not session_file.exists():
            return None
        try:
            data = json.loads(session_file.read_text())
            agent = cls(session_id=session_id)
            agent.current_target = data.get("target", "")
            agent.total_input_tokens = data.get("total_input_tokens", 0)
            agent.total_output_tokens = data.get("total_output_tokens", 0)
            agent.history = data.get("history", [])
            agent.created_at = data.get("created_at", "")
            return agent
        except Exception:
            return None
