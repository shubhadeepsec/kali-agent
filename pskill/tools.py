"""tools.py — Shell execution and built-in agent tools."""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

from . import config, intel as intel_mod

PLAYBOOKS_DIR = Path(__file__).resolve().parents[1] / "playbooks"

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


def run_shell(cmd: str, timeout: int = 60) -> CommandResult:
    """Execute a shell command and return result."""
    try:
        proc = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return CommandResult(cmd, proc.stdout, proc.stderr, proc.returncode)
    except subprocess.TimeoutExpired:
        return CommandResult(cmd, "", f"Command timed out after {timeout}s", 124)
    except Exception as e:
        return CommandResult(cmd, "", str(e), 1)


def run_shell_stream(cmd: str, timeout: int = 300) -> str:
    """Execute a shell command, streaming output line by line. Returns full output."""
    output_lines = []
    try:
        proc = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        for line in proc.stdout:  # type: ignore
            print(line, end="", flush=True)
            output_lines.append(line)
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        output_lines.append(f"\n[Timed out after {timeout}s]")
    except Exception as e:
        output_lines.append(f"\n[Error: {e}]")
    return "".join(output_lines)


# ── Built-in tools the agent can call ────────────────────────────────────────

TOOL_SCHEMAS = [
    {
        "name": "run_command",
        "description": (
            "Execute a shell command on the target or locally. Use for nmap, ffuf, curl, "
            "whatweb, sqlmap, hydra, gobuster, dirsearch, nuclei, httpx, etc. "
            "Always explain what the command does before running it."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The exact shell command to run"},
                "description": {"type": "string", "description": "Brief explanation of what this does"},
                "timeout": {"type": "integer", "description": "Timeout in seconds (default 60)"},
            },
            "required": ["command", "description"],
        },
    },
    {
        "name": "update_intel",
        "description": "Save findings to the engagement's intel.json state file.",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {"type": "string"},
                "command": {
                    "type": "string",
                    "enum": ["add-host", "add-endpoint", "add-tech", "add-vuln",
                             "add-param", "mark-done", "set-waf", "note"],
                },
                "value": {"type": "string"},
                "severity": {"type": "string", "enum": ["critical", "high", "medium", "low", "info"]},
            },
            "required": ["target", "command", "value"],
        },
    },
    {
        "name": "get_intel",
        "description": "Read current engagement intelligence for a target.",
        "parameters": {
            "type": "object",
            "properties": {"target": {"type": "string"}},
            "required": ["target"],
        },
    },
    {
        "name": "get_playbook",
        "description": "Load methodology instructions for a specific security skill.",
        "parameters": {
            "type": "object",
            "properties": {
                "skill": {"type": "string", "enum": SKILLS}
            },
            "required": ["skill"],
        },
    },
    {
        "name": "read_file",
        "description": "Read a local file (tool output, config, etc.)",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a local file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
]


def execute_tool(name: str, args: dict[str, Any],
                 confirm_fn=None) -> str:
    """
    Dispatch a tool call. confirm_fn(cmd, desc) -> bool is called for shell commands.
    Returns string result to feed back to the model.
    """
    if name == "run_command":
        cmd = args["command"]
        desc = args.get("description", "")
        timeout = int(args.get("timeout", 60))

        if confirm_fn and not config.get("auto_approve", False):
            approved = confirm_fn(cmd, desc)
            if not approved:
                return "Command was denied by user."

        result = run_shell(cmd, timeout=timeout)
        output = str(result)
        if len(output) > 8000:
            output = output[:8000] + "\n... [truncated]"
        return f"Exit {result.returncode}:\n{output}"

    elif name == "update_intel":
        target = args["target"]
        try:
            intel_mod.update(
                target,
                args["command"],
                args["value"],
                args.get("severity", "info"),
            )
            return f"Intel updated: {args['command']} → {args['value']}"
        except Exception as e:
            return f"Error: {e}"

    elif name == "get_intel":
        target = args["target"]
        data = intel_mod.load(target)
        if not data:
            return f"No engagement found for '{target}'. Use /init to create one."
        return json.dumps(data, indent=2)

    elif name == "get_playbook":
        skill = args["skill"]
        md = PLAYBOOKS_DIR / skill / "SKILL.md"
        if not md.exists():
            return f"Playbook not found: {skill}"
        content = md.read_text()
        if len(content) > 12000:
            content = content[:12000] + "\n... [truncated]"
        return content

    elif name == "read_file":
        try:
            p = Path(args["path"]).expanduser()
            content = p.read_text(errors="replace")
            if len(content) > 8000:
                content = content[:8000] + "\n... [truncated]"
            return content
        except Exception as e:
            return f"Error reading file: {e}"

    elif name == "write_file":
        try:
            p = Path(args["path"]).expanduser()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(args["content"])
            return f"Written: {p}"
        except Exception as e:
            return f"Error writing file: {e}"

    return f"Unknown tool: {name}"
