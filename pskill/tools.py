"""tools.py — OS-level execution, Kali Linux tool orchestration, and system management tools."""
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
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
    def __init__(self, cmd: str, stdout: str, stderr: str, returncode: int, cwd: str = ""):
        self.cmd = cmd
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.cwd = cwd
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


def run_shell(cmd: str, timeout: int = 180, cwd: str | None = None) -> CommandResult:
    """Execute any bash shell command on Kali Linux with custom cwd and timeout."""
    working_dir = os.path.expanduser(cwd) if cwd else os.getcwd()
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=working_dir,
            errors="replace",
            executable="/bin/bash",
        )
        return CommandResult(cmd, proc.stdout, proc.stderr, proc.returncode, cwd=working_dir)
    except subprocess.TimeoutExpired:
        return CommandResult(cmd, "", f"Command timed out after {timeout}s", 124, cwd=working_dir)
    except KeyboardInterrupt:
        return CommandResult(cmd, "", "Command cancelled by user", 130, cwd=working_dir)
    except Exception as e:
        return CommandResult(cmd, "", str(e), 1, cwd=working_dir)


# ── Kali OS Management Helpers ────────────────────────────────────────────────

def get_system_diagnostics() -> dict[str, Any]:
    """Get rich OS diagnostics from Kali Linux."""
    def _run(c: str) -> str:
        return run_shell(c, timeout=10).stdout.strip()

    return {
        "os": _run("cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"'"),
        "kernel": _run("uname -r"),
        "architecture": _run("uname -m"),
        "user": _run("whoami"),
        "hostname": _run("hostname"),
        "ip_interfaces": _run("ip -brief address || ifconfig"),
        "listening_ports": _run("ss -tuln | head -n 25 || netstat -tuln | head -n 25"),
        "memory_usage": _run("free -h"),
        "disk_usage": _run("df -h /"),
        "active_services": _run("systemctl list-units --type=service --state=running | head -n 20"),
    }


def manage_system_service(service_name: str, action: str) -> str:
    """Start, stop, restart, enable, or inspect system services."""
    action = action.lower().strip()
    if action not in ("status", "start", "stop", "restart", "enable", "disable", "reload"):
        return f"Invalid action: {action}. Supported: status, start, stop, restart, enable, disable, reload."

    cmd = f"sudo systemctl {action} {shlex.quote(service_name)}" if action != "status" else f"systemctl status {shlex.quote(service_name)}"
    res = run_shell(cmd, timeout=30)
    return str(res)


def manage_packages(manager: str, action: str, package_name: str) -> str:
    """Install, update, or remove software using apt, pip, go, cargo, or git."""
    manager = manager.lower().strip()
    action = action.lower().strip()
    pkg = shlex.quote(package_name)

    if manager == "apt":
        if action == "install":
            cmd = f"sudo apt-get update && sudo apt-get install -y {pkg}"
        elif action == "remove":
            cmd = f"sudo apt-get remove -y {pkg}"
        elif action == "search":
            cmd = f"apt-cache search {pkg}"
        else:
            return f"Unsupported apt action: {action}"
    elif manager == "pip":
        if action == "install":
            cmd = f"pip install {pkg}"
        elif action == "remove":
            cmd = f"pip uninstall -y {pkg}"
        elif action == "list":
            cmd = f"pip list | grep -i {pkg}"
        else:
            return f"Unsupported pip action: {action}"
    elif manager == "go":
        cmd = f"go install {pkg}@latest"
    elif manager == "git":
        cmd = f"git clone {pkg}"
    elif manager == "cargo":
        cmd = f"cargo install {pkg}"
    else:
        return f"Unknown package manager: {manager}. Supported: apt, pip, go, cargo, git."

    res = run_shell(cmd, timeout=300)
    return str(res)


def find_files(path: str, pattern: str = "", content_search: str = "", max_results: int = 50) -> str:
    """Search for files and directories or grep for content across Kali filesystem."""
    search_dir = os.path.expanduser(path)
    if not os.path.exists(search_dir):
        return f"Directory does not exist: {search_dir}"

    if content_search:
        cmd = f"grep -rnI --exclude-dir=.git --exclude-dir=__pycache__ {shlex.quote(content_search)} {shlex.quote(search_dir)} | head -n {max_results}"
    elif pattern:
        cmd = f"find {shlex.quote(search_dir)} -name {shlex.quote(pattern)} | head -n {max_results}"
    else:
        cmd = f"ls -la {shlex.quote(search_dir)} | head -n {max_results}"

    res = run_shell(cmd, timeout=30)
    return str(res)


# ── Built-in tools the agent can call ────────────────────────────────────────

TOOL_SCHEMAS = [
    {
        "name": "run_command",
        "description": (
            "Execute any bash shell command on Kali Linux. You have full OS access to run security tools "
            "(nmap, ffuf, nuclei, sqlmap, hydra, metasploit/msfconsole, john, hashcat, gobuster, burp, "
            "wireshark/tshark, aircrack-ng, ghidra, radare2, impacket, netexec, docker, etc.), "
            "write scripts, inspect network interfaces, and automate tasks. "
            "Always include a concise description of what the command does."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The exact shell command line string to execute"},
                "description": {"type": "string", "description": "Brief explanation of what this command accomplishes"},
                "cwd": {"type": "string", "description": "Optional working directory to execute in"},
                "timeout": {"type": "integer", "description": "Timeout in seconds (default 180)"},
            },
            "required": ["command", "description"],
        },
    },
    {
        "name": "get_system_info",
        "description": "Inspect Kali Linux system diagnostics: OS version, kernel, IP addresses/interfaces, listening ports/sockets, memory, disk, and active services.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "manage_service",
        "description": "Manage Linux systemd services (start, stop, restart, status, enable) such as postgresql, docker, apache2, ssh, tor, openvpn.",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Name of the systemd service (e.g. postgresql, docker, ssh, apache2)"},
                "action": {"type": "string", "enum": ["status", "start", "stop", "restart", "enable", "disable", "reload"], "description": "Action to perform"},
            },
            "required": ["service_name", "action"],
        },
    },
    {
        "name": "manage_packages",
        "description": "Install, update, or search for software packages and security tools using apt, pip, go, cargo, or git.",
        "parameters": {
            "type": "object",
            "properties": {
                "manager": {"type": "string", "enum": ["apt", "pip", "go", "cargo", "git"], "description": "Package manager to use"},
                "action": {"type": "string", "enum": ["install", "remove", "search", "list"], "description": "Action to perform"},
                "package_name": {"type": "string", "description": "Name of the package, tool, or git repository URL"},
            },
            "required": ["manager", "action", "package_name"],
        },
    },
    {
        "name": "find_files",
        "description": "Search for files by name pattern or search inside file contents (grep) across the filesystem.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Base directory to search from (e.g. /home/kali, /var/log, /etc)"},
                "pattern": {"type": "string", "description": "File name pattern to find (e.g. '*.conf', '*.php', 'id_rsa*')"},
                "content_search": {"type": "string", "description": "Text or regex string to search inside file contents"},
                "max_results": {"type": "integer", "description": "Maximum results to return (default 50)"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "read_file",
        "description": "Read contents of any local file from the Kali filesystem.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Path to file to read"}},
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write or create a file on the Kali filesystem (e.g. custom scripts, payloads, wordlists, configuration files, reports).",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Destination file path"},
                "content": {"type": "string", "description": "Text or code content to write"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "update_intel",
        "description": "Save target assets, endpoints, technologies, notes, or confirmed vulnerabilities to target state in intel.json.",
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
                "value": {"type": "string", "description": "Value to record"},
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
]


def execute_tool(name: str, args: dict[str, Any], confirm_fn=None) -> str:
    """
    Dispatch a tool call. confirm_fn(cmd, desc) -> bool is called for shell commands.
    Returns string result to feed back to the model.
    """
    if name == "run_command":
        cmd = args.get("command", "")
        desc = args.get("description", "")
        cwd = args.get("cwd")
        timeout = int(args.get("timeout", 180))

        if not cmd:
            return "Error: No command provided."

        if confirm_fn and not config.get("auto_approve", False):
            approved = confirm_fn(cmd, desc)
            if not approved:
                return "Command execution was denied by user."

        result = run_shell(cmd, timeout=timeout, cwd=cwd)
        output = str(result)
        if len(output) > 12000:
            output = output[:12000] + "\n... [truncated for token limit]"
        return f"Exit code {result.returncode}:\n{output}"

    elif name == "get_system_info":
        try:
            diag = get_system_diagnostics()
            return json.dumps(diag, indent=2)
        except Exception as e:
            return f"Error gathering diagnostics: {e}"

    elif name == "manage_service":
        svc = args.get("service_name", "")
        action = args.get("action", "")
        if confirm_fn and action != "status" and not config.get("auto_approve", False):
            approved = confirm_fn(f"sudo systemctl {action} {svc}", f"{action} system service {svc}")
            if not approved:
                return "Service action was denied by user."
        return manage_system_service(svc, action)

    elif name == "manage_packages":
        mgr = args.get("manager", "")
        act = args.get("action", "")
        pkg = args.get("package_name", "")
        if confirm_fn and act in ("install", "remove") and not config.get("auto_approve", False):
            approved = confirm_fn(f"{mgr} {act} {pkg}", f"{act} package {pkg} using {mgr}")
            if not approved:
                return "Package operation was denied by user."
        return manage_packages(mgr, act, pkg)

    elif name == "find_files":
        p = args.get("path", "")
        pattern = args.get("pattern", "")
        content = args.get("content_search", "")
        max_r = int(args.get("max_results", 50))
        return find_files(p, pattern, content, max_r)

    elif name == "read_file":
        try:
            p = Path(args.get("path", "")).expanduser()
            if not p.exists():
                return f"File does not exist: {p}"
            content = p.read_text(errors="replace")
            if len(content) > 15000:
                content = content[:15000] + "\n... [truncated]"
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
            return f"Intel updated for '{target}': {args.get('command')} → {args.get('value')}"
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

    return f"Unknown tool: {name}"
