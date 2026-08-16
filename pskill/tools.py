"""tools.py — Shell execution, intelligence tools, and tool schemas for LLMs."""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

from . import config, intel as intel_mod


def _find_playbooks_dir() -> Path:
    candidates = [
        Path(__file__).resolve().parents[1] / "playbooks",
        Path.cwd() / "playbooks",
        Path.home() / ".pskill" / "playbooks",
    ]
    for c in candidates:
        if c.exists() and c.is_dir():
            return c
    return candidates[0]


PLAYBOOKS_DIR = _find_playbooks_dir()

SKILLS = [
    "web-recon", "api-testing", "idor-bola", "injection", "http-advanced",
    "ssrf", "oauth-auth", "business-logic", "js-reverse", "apk-reverse",
    "mobile-advanced", "binary-reverse", "cloud-security", "ad-pentest",
    "post-exploit", "ai-llm-security", "reporting",
]


# ── Shell execution ───────────────────────────────────────────────────────────

class CommandResult:
    def __init__(self, cmd: str, stdout: str, stderr: str, returncode: int):
        self.cmd = cmd
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.ok = returncode == 0

    def __str__(self) -> str:
        out = self.stdout.strip()
        err = self.stderr.strip()
        parts = []
        if out:
            parts.append(out)
        if err and not self.ok:
            parts.append(f"[stderr] {err}")
        return "\n".join(parts) or "(no output)"


def run_shell(cmd: str, timeout: int = 120) -> CommandResult:
    """Execute a shell command and return result."""
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            errors="replace",
        )
        return CommandResult(cmd, proc.stdout, proc.stderr, proc.returncode)
    except subprocess.TimeoutExpired:
        return CommandResult(cmd, "", f"Command timed out after {timeout}s", 124)
    except KeyboardInterrupt:
        return CommandResult(cmd, "", "Command cancelled by user", 130)
    except Exception as e:
        return CommandResult(cmd, "", str(e), 1)


# ── Built-in tools the agent can call ────────────────────────────────────────

TOOL_SCHEMAS = [
    {
        "name": "run_command",
        "description": (
            "Execute a shell command on the target or locally (nmap, ffuf, curl, "
            "whatweb, sqlmap, hydra, gobuster, dirsearch, nuclei, httpx, etc.). "
            "Always provide a brief description of what the command does."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The exact shell command to execute"},
                "description": {"type": "string", "description": "Brief explanation of what this command accomplishes"},
                "timeout": {"type": "integer", "description": "Timeout in seconds (default 120)"},
            },
            "required": ["command", "description"],
        },
    },
    {
        "name": "update_intel",
        "description": "Record discovered assets, endpoints, technologies, or confirmed vulnerabilities to target state in intel.json.",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target domain, IP, or name"},
                "command": {
                    "type": "string",
                    "enum": ["add-host", "add-endpoint", "add-tech", "add-vuln",
                             "add-param", "mark-done", "mark-blocked", "set-waf", "note"],
                    "description": "State update operation",
                },
                "value": {"type": "string", "description": "Value to record (e.g. host IP, URL, tech name, vulnerability title)"},
                "severity": {"type": "string", "enum": ["critical", "high", "medium", "low", "info"], "description": "Severity if recording a vulnerability"},
                "reason": {"type": "string", "description": "Reason text if marking an action blocked"},
            },
            "required": ["target", "command", "value"],
        },
    },
    {
        "name": "get_intel",
        "description": "Read the current engagement intelligence state for a target (hosts, open ports, endpoints, technologies, findings).",
        "parameters": {
            "type": "object",
            "properties": {"target": {"type": "string", "description": "Target name or domain"}},
            "required": ["target"],
        },
    },
    {
        "name": "get_playbook",
        "description": "Load the methodology instructions, commands, and checklists for a specific security skill playbook.",
        "parameters": {
            "type": "object",
            "properties": {
                "skill": {"type": "string", "enum": SKILLS, "description": "Name of the skill playbook to load"}
            },
            "required": ["skill"],
        },
    },
    {
        "name": "read_file",
        "description": "Read content from a local file (e.g., tool output, wordlist, config).",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "File path to read"}},
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write or save content to a local file (e.g., reports, scripts, custom wordlists).",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write to"},
                "content": {"type": "string", "description": "Text content to save"},
            },
            "required": ["path", "content"],
        },
    },
]


def execute_tool(name: str, args: dict[str, Any], confirm_fn=None) -> str:
    """
    Dispatch a tool call. confirm_fn(cmd, desc) -> bool is called for shell commands.
    Returns string result to feed back to the model.
    """
    if name == "run_command":
        cmd = args.get("command", "")
        desc = args.get("description", "")
        timeout = int(args.get("timeout", 120))

        if not cmd:
            return "Error: No command provided."

        if confirm_fn and not config.get("auto_approve", False):
            approved = confirm_fn(cmd, desc)
            if not approved:
                return "Command execution was denied by user."

        result = run_shell(cmd, timeout=timeout)
        output = str(result)
        if len(output) > 10000:
            output = output[:10000] + "\n... [truncated for token limit]"
        return f"Exit code {result.returncode}:\n{output}"

    elif name == "update_intel":
        target = args.get("target", "")
        if not target:
            return "Error: Target is required for update_intel."
        try:
            intel_mod.update(
                target,
                args.get("command", ""),
                args.get("value", ""),
                args.get("severity", "info"),
                args.get("reason", ""),
            )
            return f"Intel updated successfully for '{target}': {args.get('command')} → {args.get('value')}"
        except Exception as e:
            return f"Error updating intel: {e}"

    elif name == "get_intel":
        target = args.get("target", "")
        data = intel_mod.load(target)
        if not data:
            return f"No engagement found for target '{target}'. Use /init to create one."
        return json.dumps(data, indent=2)

    elif name == "get_playbook":
        skill = args.get("skill", "")
        playbook_dir = _find_playbooks_dir()
        md = playbook_dir / skill / "SKILL.md"
        if not md.exists():
            return f"Playbook not found for '{skill}'. Available: {SKILLS}"
        content = md.read_text(errors="replace")
        if len(content) > 15000:
            content = content[:15000] + "\n... [truncated]"
        return content

    elif name == "read_file":
        try:
            p = Path(args.get("path", "")).expanduser()
            if not p.exists():
                return f"File does not exist: {p}"
            content = p.read_text(errors="replace")
            if len(content) > 10000:
                content = content[:10000] + "\n... [truncated]"
            return content
        except Exception as e:
            return f"Error reading file: {e}"

    elif name == "write_file":
        try:
            p = Path(args.get("path", "")).expanduser()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(args.get("content", ""))
            return f"File written successfully: {p}"
        except Exception as e:
            return f"Error writing file: {e}"

    return f"Unknown tool: {name}"
