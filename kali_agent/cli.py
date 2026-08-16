"""cli.py — Interactive Claude Code-style REPL and CLI interface for Kali Agent v0.1.0."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm
from rich.live import Live
from rich.spinner import Spinner
from rich.markdown import Markdown
from rich import box
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style as PTKStyle
from prompt_toolkit.completion import WordCompleter

from . import config, intel as intel_mod, jobs as jobs_mod
from .agent import Agent
from .planner import create_default_plan, render_plan_tree, Plan, Task
from .report_html import generate_html_report
from .tools import (
    SKILLS,
    PLAYBOOKS_DIR,
    run_shell,
    search_exploits,
    get_network_info,
    generate_payload,
)

console = Console()

VERSION = "0.1.0"

LOGO = """[bold red]
  ██╗  ██╗ █████╗ ██╗     ██╗     █████╗  ██████╗ ███████╗███╗   ██╗████████╗
  ██║ ██╔╝██╔══██╗██║     ██║    ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝
  █████╔╝ ███████║██║     ██║    ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   
  ██╔═██╗ ██╔══██║██║     ██║    ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   
  ██║  ██╗██║  ██║███████╗██║    ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   
  ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝    ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   [/bold red]"""

SLASH_CMDS = {
    "/scope":       "Set or confirm target authorization (lab, ctf, bounty)",
    "/plan":        "Draft and execute an autonomous multi-step pentest plan",
    "/init":        "Initialize a new engagement target & workspace",
    "/intel":       "Show target intelligence dashboard (hosts, ports, vulns)",
    "/playbook":    "Load a domain skill playbook into agent context",
    "/jobs":        "List and monitor running background processes & scans",
    "/attach":      "Tail live log output from a background job (/attach <id>)",
    "/kill":        "Terminate an active background job (/kill <id>)",
    "/revshell":    "Generate reverse shell one-liners & netcat listeners",
    "/searchsploit":"Query local Exploit-DB and CVE vulnerability database",
    "/sessions":    "List or resume previous assessment sessions",
    "/report":      "Compile Markdown and Cyberpunk Dark HTML reports",
    "/theme":       "Switch terminal theme (cyberpunk, matrix, stealth, dark)",
    "/config":      "View or update AI provider, API keys, and settings",
    "/target":      "Switch active target context",
    "/run":         "Execute a shell command directly",
    "/compact":     "Compress and summarize conversation history",
    "/clear":       "Clear current conversation history",
    "/help":        "Show available commands and usage guide",
    "/exit":        "Exit Kali Agent",
}


# ── Setup wizard (first run) ──────────────────────────────────────────────────

def setup_wizard() -> None:
    """Interactive first-run config — similar to Claude Code's onboarding."""
    console.print()
    console.print(Panel(
        "[bold white]Welcome to Kali Agent v0.1.0![/]\n\n"
        "Configure your AI provider. You can use an API key from any of:\n"
        "  • [cyan]Anthropic[/] (claude-sonnet-4-5) — [dim]https://console.anthropic.com[/]\n"
        "  • [cyan]OpenAI[/] (gpt-4o) — [dim]https://platform.openai.com[/]\n"
        "  • [cyan]Gemini[/] (gemini-2.0-flash) — [dim]https://aistudio.google.com[/]\n"
        "  • [cyan]Groq[/] (llama-3.1-70b, fast/free) — [dim]https://console.groq.com[/]\n"
        "  • [cyan]Ollama[/] (local models, no API key) — [dim]http://localhost:11434[/]",
        title="[bold red]First-time Setup[/]",
        border_style="red",
        padding=(1, 2),
    ))

    provider = Prompt.ask(
        "\n[bold yellow]Select Provider[/]",
        choices=["anthropic", "openai", "gemini", "groq", "ollama"],
        default="anthropic",
    )

    cfg = config.load()
    cfg["api_provider"] = provider

    defaults = config.PROVIDER_DEFAULTS.get(provider, {})

    if provider != "ollama":
        existing_key = config.get("api_key", "")
        if existing_key:
            use_existing = Confirm.ask(f"Found existing API key. Keep it?", default=True)
            if not use_existing:
                key = Prompt.ask(f"[bold yellow]API Key[/] for {provider}", password=True)
                cfg["api_key"] = key
        else:
            key = Prompt.ask(f"[bold yellow]API Key[/] for {provider}", password=True)
            cfg["api_key"] = key

    model_default = defaults.get("model", "")
    model = Prompt.ask("[bold yellow]Model[/]", default=model_default)
    cfg["model"] = model

    auto = Confirm.ask(
        "[bold yellow]Auto-approve shell commands?[/] (like --dangerously-skip-permissions)",
        default=False
    )
    cfg["auto_approve"] = auto

    config.save(cfg)
    console.print(f"\n[bold green]✓[/] Configuration saved → [dim]{config.CONFIG_FILE}[/]")
    console.print("[dim]Run [bold]/config[/] anytime to modify these settings.[/]\n")


# ── Slash command handlers ────────────────────────────────────────────────────

def handle_plan(args: list[str], agent: Agent) -> None:
    target = agent.current_target or "Target"
    goal = " ".join(args) if args else f"Comprehensive penetration testing assessment on {target}"

    plan = create_default_plan(goal, target)
    console.print()
    console.print(render_plan_tree(plan))

    start = Confirm.ask("[bold yellow]Execute autonomous plan phases now?[/]", default=True)
    if not start:
        return

    for t in plan.tasks:
        t.status = "running"
        console.print(f"\n[bold yellow]▶ Phase {t.id}: {t.title}[/] [dim]({t.skill})[/]")
        step_prompt = (
            f"AUTONOMOUS PHASE {t.id}: {t.title}\n"
            f"Goal: {t.description}\n"
            f"Target: {plan.target}\n"
            f"Active Playbook: {t.skill}\n"
            "Execute necessary reconnaissance, surface discovery, or security checks. Update intel with findings."
        )

        with Live(Spinner("dots", text=f"[cyan]Executing Phase {t.id}: {t.title}…[/]"), refresh_per_second=20, transient=True):
            try:
                res = agent.chat(step_prompt, confirm_fn=_confirm_command)
                t.output = res
                t.status = "completed"
                console.print(f"[bold green]✓ Phase {t.id} completed.[/]")
            except Exception as e:
                t.status = "failed"
                t.error = str(e)
                console.print(f"[bold red]✗ Phase {t.id} encountered error: {e}[/]")

    console.print("\n[bold green]✓ All plan execution phases processed.[/]")
    console.print(render_plan_tree(plan))


def handle_jobs(args: list[str], agent: Agent) -> None:
    jobs_list = jobs_mod.list_jobs()
    if not jobs_list:
        console.print("[dim]No background jobs active or recorded.[/]")
        return

    table = Table(box=box.SIMPLE_HEAD, header_style="bold red", border_style="dim", padding=(0, 2))
    table.add_column("Job ID", style="yellow", no_wrap=True)
    table.add_column("PID", style="cyan", width=8)
    table.add_column("Status", style="bold white")
    table.add_column("Command", style="white")
    table.add_column("Started", style="dim")

    status_styles = {
        "running": "[bold green]RUNNING[/]",
        "finished": "[dim]FINISHED[/]",
        "killed": "[bold red]KILLED[/]",
    }

    for j in jobs_list:
        st = status_styles.get(j.get("status", ""), j.get("status", ""))
        table.add_row(
            j.get("id", "?"),
            str(j.get("pid", "?")),
            st,
            j.get("command", "")[:45] + ("…" if len(j.get("command", "")) > 45 else ""),
            j.get("started", "")[:19],
        )

    console.print(Panel(table, title="[bold red]Background Scan Jobs[/]", border_style="red", padding=(1, 2)))
    console.print("[dim]Use [bold]/attach <job_id>[/] to tail logs or [bold]/kill <job_id>[/] to stop a job.[/]")


def handle_attach(args: list[str], agent: Agent) -> None:
    if not args:
        console.print("[dim]Usage: /attach <job_id>[/]")
        return
    job_id = args[0]
    log_tail = jobs_mod.tail_job(job_id, lines=40)
    console.print(Panel(log_tail, title=f"[bold cyan]Log Output — Job {job_id}[/]", border_style="cyan", padding=(1, 2)))


def handle_kill(args: list[str], agent: Agent) -> None:
    if not args:
        console.print("[dim]Usage: /kill <job_id>[/]")
        return
    job_id = args[0]
    if jobs_mod.kill_job(job_id):
        console.print(f"[bold red]✓ Job {job_id} terminated.[/]")
    else:
        console.print(f"[red]Failed to terminate job {job_id}. Job not found.[/]")


def handle_revshell(args: list[str], agent: Agent) -> None:
    net_info = get_network_info()
    tun0 = net_info.get("tun0_vpn_ip")
    eth0 = net_info.get("eth0_ip")
    suggested_ip = tun0 if tun0 != "(not connected)" else (eth0 if eth0 != "(not assigned)" else "10.10.14.x")

    lhost = args[0] if args else Prompt.ask("[bold yellow]LHOST (Listening IP)[/]", default=suggested_ip)
    lport = int(args[1]) if len(args) > 1 else int(Prompt.ask("[bold yellow]LPORT (Listening Port)[/]", default="9001"))

    payload_data = generate_payload("bash", lhost, lport)

    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold yellow", no_wrap=True, min_width=16)
    grid.add_column()

    grid.add_row("Netcat Listener", f"[bold green]{payload_data['listener_netcat']}[/]")
    grid.add_row("Pwncat Listener", f"[bold green]{payload_data['listener_pwncat']}[/]")
    grid.add_row("Bash One-Liner", f"[cyan]{payload_data['payload']}[/]")

    py_payload = generate_payload("python", lhost, lport, "python")["payload"]
    grid.add_row("Python One-Liner", f"[cyan]{py_payload}[/]")

    ps_payload = generate_payload("powershell", lhost, lport, "powershell")["payload"]
    grid.add_row("PowerShell One-Liner", f"[cyan]{ps_payload[:100]}…[/]")

    console.print(Panel(grid, title=f"[bold red]Reverse Shell Generator — {lhost}:{lport}[/]", border_style="red", padding=(1, 2)))


def handle_searchsploit(args: list[str], agent: Agent) -> None:
    if not args:
        query = Prompt.ask("[bold yellow]Search Query / CVE[/]")
    else:
        query = " ".join(args)

    console.print(f"[dim]Searching Exploit-DB for: {query}…[/]")
    out = search_exploits(query)
    console.print(Panel(out, title=f"[bold red]searchsploit: {query}[/]", border_style="red", padding=(1, 2)))


def handle_sessions(args: list[str], agent: Agent) -> None:
    config.ensure_dirs()
    session_files = sorted(config.SESSIONS_DIR.glob("*.json"), reverse=True)

    if not session_files:
        console.print("[dim]No saved sessions found.[/]")
        return

    if args and args[0] == "load" and len(args) > 1:
        sid = args[1]
        loaded_agent = Agent.load_session(sid)
        if loaded_agent:
            agent.session_id = loaded_agent.session_id
            agent.history = loaded_agent.history
            agent.current_target = loaded_agent.current_target
            agent.total_input_tokens = loaded_agent.total_input_tokens
            agent.total_output_tokens = loaded_agent.total_output_tokens
            console.print(f"[bold green]✓ Loaded session {sid} (Target: {agent.current_target})[/]")
            return
        else:
            console.print(f"[red]Failed to load session {sid}[/]")
            return

    table = Table(box=box.SIMPLE_HEAD, header_style="bold red", border_style="dim", padding=(0, 2))
    table.add_column("Session ID", style="yellow", no_wrap=True)
    table.add_column("Target", style="bold white")
    table.add_column("Turns", style="cyan")
    table.add_column("Updated", style="dim")

    for sf in session_files[:15]:
        try:
            d = json.loads(sf.read_text())
            sid = d.get("session_id", sf.stem)
            tgt = d.get("target", "None")
            turns = len([m for m in d.get("history", []) if m.get("role") == "user"])
            table.add_row(sid, tgt, str(turns), d.get("updated_at", "")[:19])
        except Exception:
            pass

    console.print(Panel(table, title="[bold red]Saved Assessment Sessions[/]", border_style="red", padding=(1, 2)))
    console.print("[dim]Run [bold]/sessions load <session_id>[/] to resume a session.[/]")


def handle_theme(args: list[str], agent: Agent) -> None:
    if not args:
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        table.add_column(style="bold yellow", no_wrap=True)
        table.add_column(style="white")
        table.add_row("cyberpunk", "Neon Red & Cyan (Default)")
        table.add_row("matrix", "Matrix Hacker Green")
        table.add_row("stealth", "Monochrome Stealth Dark")
        table.add_row("dark", "Vibrant Purple / Dark")
        console.print(Panel(table, title="[bold red]Available Themes[/]", border_style="red"))
        choice = Prompt.ask("[bold yellow]Select Theme[/]", choices=list(config.THEMES.keys()), default="cyberpunk")
    else:
        choice = args[0].lower()

    if choice in config.THEMES:
        config.set_value("theme", choice)
        console.print(f"[bold green]✓ Theme set to: {choice}[/]")
    else:
        console.print(f"[red]Unknown theme. Available: {list(config.THEMES.keys())}[/]")


def handle_config(args: list[str], agent: Agent) -> None:
    cfg = config.load()

    if not args:
        table = Table(box=box.SIMPLE_HEAD, header_style="bold red", border_style="dim", padding=(0, 2))
        table.add_column("Setting", style="yellow", no_wrap=True)
        table.add_column("Value", style="white")
        for k, v in cfg.items():
            val = "********" if k == "api_key" and v else str(v)
            table.add_row(k, val)
        console.print(Panel(table, title="[bold red]Configuration[/]", border_style="red", padding=(1, 2)))
        console.print(f"[dim]Config file: {config.CONFIG_FILE}[/]")
        return

    if args[0] in ("setup", "wizard", "init"):
        setup_wizard()
        return

    cmd_args = args[1:] if args[0] == "set" else args
    if len(cmd_args) >= 2:
        key, value = cmd_args[0], " ".join(cmd_args[1:])
        if key in ("auto_approve", "scope_required", "stream_output", "track_tokens"):
            val_bool = value.lower() in ("true", "1", "yes", "on")
            config.set_value(key, val_bool)
            console.print(f"[green]✓[/] {key} = {val_bool}")
        elif key == "max_tokens":
            try:
                config.set_value(key, int(value))
                console.print(f"[green]✓[/] {key} = {int(value)}")
            except ValueError:
                console.print("[red]max_tokens must be an integer.[/]")
        else:
            config.set_value(key, value)
            console.print(f"[green]✓[/] {key} = {value}")
    else:
        console.print("[dim]Usage: /config | /config setup | /config <key> <value>[/]")


def handle_init(args: list[str], agent: Agent) -> None:
    target = ""
    mode = "bounty"
    skill = "web-recon"

    if args:
        if "--target" in args:
            idx = args.index("--target")
            if idx + 1 < len(args): target = args[idx + 1]
        if "--mode" in args:
            idx = args.index("--mode")
            if idx + 1 < len(args): mode = args[idx + 1]
        if "--skill" in args:
            idx = args.index("--skill")
            if idx + 1 < len(args): skill = args[idx + 1]
        if not target and args[0] and not args[0].startswith("-"):
            target = args[0]
            if len(args) > 1 and not args[1].startswith("-"): mode = args[1]
            if len(args) > 2 and not args[2].startswith("-"): skill = args[2]

    if not target:
        target = Prompt.ask("[bold yellow]Target[/] (domain, IP, or hostname)")
        mode = Prompt.ask("[bold yellow]Mode[/]", choices=["bounty", "vdp", "lab", "ctf"], default="bounty")
        skill = Prompt.ask("[bold yellow]Primary skill[/]", default="web-recon")

    data = intel_mod.init(target, mode, skill)
    agent.current_target = target
    console.print(
        Panel(
            f"[bold white]{target}[/]\n"
            f"Mode: [cyan]{mode}[/]  |  Skill: [yellow]{skill}[/]\n"
            f"Directory: [dim]{intel_mod.path(target)}[/]",
            title="[bold green]✓ Engagement Initialized[/]",
            border_style="green",
            padding=(1, 2),
        )
    )
    agent.inject_context(
        f"Target engagement initialized:\nTarget: {target}\nMode: {mode}\nInitial Skill: {skill}\n"
        f"Intel state: {json.dumps(data, indent=2)}"
    )


def handle_intel(args: list[str], agent: Agent) -> None:
    target = args[0] if args else agent.current_target
    if not target:
        target = _pick_engagement()
    if not target:
        return

    data = intel_mod.load(target)
    if not data:
        console.print(f"[red]No engagement found for '{target}'. Run /init first.[/]")
        return

    sev_color = {"critical": "bold red", "high": "red", "medium": "yellow", "low": "green", "info": "dim"}

    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold dim", no_wrap=True, min_width=14)
    grid.add_column()
    grid.add_row("Target",  f"[bold white]{data.get('target','?')}[/]")
    grid.add_row("Mode",    f"[cyan]{data.get('mode','?')}[/]")
    grid.add_row("Skill",   f"[yellow]{data.get('primary_skill','?')}[/]")
    grid.add_row("Updated", f"[dim]{data.get('updated','?')}[/]")
    if data.get("waf"):
        grid.add_row("WAF/CDN", f"[red]{data['waf']}[/]")

    def lst(items: list, style: str = "white", limit: int = 10) -> str:
        if not items: return "[dim]none[/]"
        formatted = "\n".join(f"[{style}]• {i}[/]" for i in items[:limit])
        if len(items) > limit:
            formatted += f"\n[dim]  … (+{len(items)-limit} more)[/]"
        return formatted

    grid.add_row("Hosts",     lst(data.get("hosts", []),     "green"))
    grid.add_row("Endpoints", lst(data.get("endpoints", []), "blue"))
    grid.add_row("Tech Stack", lst(data.get("tech", []),     "magenta"))
    grid.add_row("Parameters", lst(data.get("params", []),   "cyan"))

    vulns = data.get("vulns", [])
    vuln_text = "\n".join(
        f"[{sev_color.get(v.get('severity','info'),'white')}]• [{v.get('severity','?').upper()}] {v.get('title','?')}[/]"
        for v in vulns
    ) if vulns else "[dim]none recorded yet[/]"
    grid.add_row("Vulnerabilities", vuln_text)
    grid.add_row("Actions Completed", f"[dim]{len(data.get('done',[]))} done, {len(data.get('blocked',[]))} blocked[/]")

    console.print(Panel(grid, title=f"[bold red]Intelligence — {target}[/]",
                        border_style="red", padding=(1, 2)))


def handle_scope(args: list[str], agent: Agent) -> None:
    if not args:
        console.print(Panel(
            "[bold yellow]Configure Target Authorization Scope:[/]\n\n"
            "  [white]/scope lab [target][/]                    [dim]→ Local test lab (default: 127.0.0.1)[/]\n"
            "  [white]/scope ctf <target_ip>[/]                 [dim]→ CTF Challenge / HackTheBox IP[/]\n"
            "  [white]/scope bounty <domain> <program_name>[/]  [dim]→ Authorized Bug Bounty program[/]",
            title="[bold red]Scope Management[/]",
            border_style="red",
            padding=(1, 2),
        ))
        return

    mode = args[0].lower()
    rest = args[1:]
    target = ""

    if "--target" in rest:
        idx = rest.index("--target")
        if idx + 1 < len(rest): target = rest[idx + 1]
    elif rest and not rest[0].startswith("-"):
        target = rest[0]

    if mode == "lab":
        target = target or "127.0.0.1"
        console.print(f"[green]✓[/] Scope confirmed: Local Lab → [bold]{target}[/]")
        if not intel_mod.load(target):
            intel_mod.init(target, "lab", "web-recon")
        intel_mod.update(target, "scope-confirmed", "true")
        agent.current_target = target
        agent.inject_context(f"Scope authorization confirmed: Local Lab environment (Target: {target}).")

    elif mode == "ctf":
        target = target or Prompt.ask("[bold yellow]Target IP/Hostname[/]")
        console.print(f"[green]✓[/] Scope confirmed: CTF / Lab → [bold]{target}[/]")
        if not intel_mod.load(target):
            intel_mod.init(target, "ctf", "web-recon")
        intel_mod.update(target, "scope-confirmed", "true")
        agent.current_target = target
        agent.inject_context(f"Scope authorization confirmed: CTF Challenge (Target: {target}).")

    elif mode == "bounty":
        target = target or Prompt.ask("[bold yellow]Target Domain[/]")
        program = rest[1] if len(rest) > 1 and not rest[1].startswith("-") else Prompt.ask("[bold yellow]Program Name[/]")
        console.print(f"[green]✓[/] Scope confirmed: Bug Bounty → [bold]{program}[/] ([bold]{target}[/])")
        if not intel_mod.load(target):
            intel_mod.init(target, "bounty", "web-recon")
        intel_mod.update(target, "scope-confirmed", "true")
        intel_mod.update(target, "note", f"Program: {program}")
        agent.current_target = target
        agent.inject_context(
            f"Scope authorization confirmed: Bug Bounty Program '{program}', Target '{target}'. "
            "In scope: primary domain and declared subdomains. Out of scope: DoS, social engineering, third-party infrastructure."
        )
    else:
        console.print(f"[red]Unknown scope mode '{mode}'. Use: /scope lab | /scope ctf | /scope bounty[/]")


def handle_playbook(args: list[str], agent: Agent) -> None:
    if not args:
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        table.add_column(style="bold yellow", no_wrap=True)
        table.add_column(style="dim")
        for s in SKILLS:
            table.add_row(s, f"/playbook {s}")
        console.print(Panel(table, title="[bold red]17 Available Playbooks[/]", border_style="red"))
        skill = Prompt.ask("[bold yellow]Select Playbook[/]", choices=SKILLS)
    else:
        skill = args[0].strip().lower()

    md = PLAYBOOKS_DIR / skill / "SKILL.md"
    if not md.exists():
        console.print(f"[red]Playbook '{skill}' not found. Available: {SKILLS}[/]")
        return

    content = md.read_text(errors="replace")
    agent.inject_context(f"PLAYBOOK LOADED: {skill}\n\n{content}")
    console.print(f"[green]✓[/] Playbook [bold]{skill}[/] loaded into agent context.")
    console.print(Syntax(content[:2500], "markdown", theme="monokai",
                          word_wrap=True, background_color="default"))


def handle_engagements(_: list[str], agent: Agent) -> None:
    engs = intel_mod.list_engagements()
    if not engs:
        console.print("[dim]No engagements recorded yet. Use /init to create one.[/]")
        return

    table = Table(box=box.SIMPLE_HEAD, header_style="bold red", border_style="dim", padding=(0, 2))
    table.add_column("Target",   style="bold white")
    table.add_column("Mode",     style="cyan")
    table.add_column("Skill",    style="yellow")
    table.add_column("Hosts",    style="green")
    table.add_column("Vulns",    style="red")
    table.add_column("Updated",  style="dim")

    for d in engs:
        table.add_row(
            d.get("target", "?"),
            d.get("mode", "?"),
            d.get("primary_skill", "?"),
            str(len(d.get("hosts", []))),
            str(len(d.get("vulns", []))),
            d.get("updated", "?")[:10],
        )
    console.print(Panel(table, title="[bold red]Saved Engagements[/]", border_style="red", padding=(1, 2)))


def handle_report(args: list[str], agent: Agent) -> None:
    target = args[0] if (args and not args[0].startswith("-")) else agent.current_target
    if not target:
        target = _pick_engagement()
    if not target:
        return

    data = intel_mod.load(target)
    if not data:
        console.print(f"[red]No intelligence found for '{target}'.[/]")
        return

    html_out = intel_mod.path(target) / "report.html"
    generate_html_report(data, output_path=html_out)

    prompt = (
        f"Generate a professional, executive-ready Penetration Testing Report for target '{target}'.\n"
        f"Use this engagement state:\n{json.dumps(data, indent=2)}\n\n"
        "Include:\n"
        "1. Executive Summary & Risk Assessment Matrix\n"
        "2. Scope & Target Information\n"
        "3. Technical Findings (Severity, Title, Affected Endpoints, Proof of Concept, Impact, Remediation)\n"
        "4. Attack Surface Coverage & Methodology Summary\n"
        "5. Remediation Roadmap\n"
        f"Save the report to {intel_mod.path(target)}/report.md using write_file."
    )

    with Live(Spinner("dots", text=f"[cyan]Compiling assessment report for {target}…[/]"), refresh_per_second=20):
        result = agent.chat(prompt)

    md_out = intel_mod.path(target) / "report.md"
    if not md_out.exists():
        md_out.write_text(result)

    console.print(Markdown(result[:3500]))
    console.print(f"\n[bold green]✓ Reports generated:[/]")
    console.print(f"  • Markdown: [bold]{md_out}[/]")
    console.print(f"  • Dark HTML: [bold cyan]{html_out}[/]")


def handle_run(args: list[str], agent: Agent) -> None:
    if not args:
        console.print("[dim]Usage: /run <command>[/]")
        return
    cmd = " ".join(args)
    console.print(f"[dim]$ {cmd}[/]")
    res = run_shell(cmd, timeout=180)
    console.print(str(res) or "[dim](no output)[/]")


def _pick_engagement() -> str | None:
    engs = intel_mod.list_engagements()
    if not engs:
        console.print("[red]No engagements found. Run /init first.[/]")
        return None
    if len(engs) == 1:
        return engs[0].get("target")
    for i, e in enumerate(engs, 1):
        console.print(f"  [bold yellow]{i}[/] {e.get('target','?')}")
    try:
        idx = int(Prompt.ask("Select target index")) - 1
        return engs[idx].get("target")
    except Exception:
        return None


SLASH_HANDLERS = {
    "/scope":       handle_scope,
    "/plan":        handle_plan,
    "/init":        handle_init,
    "/intel":       handle_intel,
    "/playbook":    handle_playbook,
    "/jobs":        handle_jobs,
    "/attach":      handle_attach,
    "/kill":        handle_kill,
    "/revshell":    handle_revshell,
    "/searchsploit":handle_searchsploit,
    "/sessions":    handle_sessions,
    "/theme":       handle_theme,
    "/engagements": handle_engagements,
    "/report":      handle_report,
    "/config":      handle_config,
    "/run":         handle_run,
}


# ── Confirmation & Status Bar ─────────────────────────────────────────────────

def _confirm_command(cmd: str, desc: str) -> bool:
    """Claude Code-style command execution approval prompt."""
    console.print()
    console.print(Panel(
        f"[dim]{desc}[/]\n\n[bold white]$ {cmd}[/]",
        title="[bold yellow]⚡ Execute Shell Command?[/]",
        border_style="yellow",
        padding=(1, 2),
    ))
    return Confirm.ask("[bold yellow]Allow execution?[/]", default=True)


def _status_bar(agent: Agent) -> str:
    parts = []
    if agent.current_target:
        parts.append(f"[bold cyan]target: {agent.current_target}[/]")
    else:
        parts.append("[dim]no target[/]")

    provider = config.get("api_provider", "")
    model = config.get("model", "")
    if provider:
        parts.append(f"[dim]{provider}/{model}[/]")
    else:
        parts.append("[red]no provider configured[/]")

    # Active jobs count
    running_jobs = len([j for j in jobs_mod.list_jobs() if j.get("status") == "running"])
    if running_jobs:
        parts.append(f"[bold green]⚡ {running_jobs} bg jobs[/]")

    # Token stats
    total_tokens = agent.total_input_tokens + agent.total_output_tokens
    if total_tokens > 0:
        cost = agent.estimate_cost()
        parts.append(f"[dim]{total_tokens:,} tokens (~${cost:.4f})[/]")

    return "  [dim]│[/]  ".join(parts)


# ── Interactive REPL and CLI Entry Point ─────────────────────────────────────

def run() -> None:
    """Main CLI entry point — handles one-shot commands, flags, or drops into interactive REPL."""
    raw_args = sys.argv[1:]

    # CLI flag checks
    if raw_args and raw_args[0] in ("-v", "--version"):
        print(f"kali-agent v{VERSION}")
        return

    if raw_args and raw_args[0] in ("-h", "--help"):
        console.print(LOGO)
        table = Table(box=box.SIMPLE_HEAD, header_style="bold red", border_style="dim", padding=(0, 2))
        table.add_column("Command", style="bold yellow", no_wrap=True)
        table.add_column("Description", style="white")
        for c, d in SLASH_CMDS.items():
            table.add_row(c, d)
        console.print(Panel(table, title="[bold red]Kali Agent v0.1.0 — Autonomous AI for Kali Linux[/]",
                            border_style="red", padding=(1, 2)))
        return

    # First-run setup if no provider configured
    if not config.is_configured():
        console.print(LOGO)
        setup_wizard()

    agent = Agent()

    # One-shot command execution via CLI args
    if raw_args:
        first = raw_args[0]
        if first.startswith("/"):
            cmd = first.lower()
            args = raw_args[1:]
            if cmd in SLASH_HANDLERS:
                SLASH_HANDLERS[cmd](args, agent)
            else:
                console.print(f"[red]Unknown command: {cmd}[/]")
            return
        else:
            prompt = " ".join(raw_args)
            console.print(f"[dim]kali-agent ❯ {prompt}[/]\n")
            with Live(Spinner("dots", text="[red dim]thinking…[/]"), refresh_per_second=20, transient=True):
                try:
                    res = agent.chat(prompt, confirm_fn=_confirm_command)
                    console.print(Panel(Markdown(res), border_style="dim red", padding=(1, 2)))
                except Exception as e:
                    console.print(f"[red]Agent error: {e}[/]")
            return

    # Interactive REPL
    console.print(LOGO)
    console.print(Panel(_status_bar(agent), border_style="dim", padding=(0, 2)))
    console.print("[dim]Type your objective naturally, or use [bold]/help[/] for slash commands.[/]\n")

    all_completions = list(SLASH_CMDS.keys()) + SKILLS
    completer = WordCompleter(all_completions, ignore_case=True, sentence=True)
    style_info = config.get_theme_style()
    prompt_cls = style_info.get("prompt_class", "ansired bold")

    session: PromptSession = PromptSession(
        history=FileHistory(str(config.HIST_FILE)),
        auto_suggest=AutoSuggestFromHistory(),
        completer=completer,
        style=PTKStyle.from_dict({"prompt": prompt_cls, "": "ansiwhite"}),
    )

    while True:
        try:
            target_part = f"[{agent.current_target}]" if agent.current_target else ""
            prompt_parts = [
                ("class:prompt", f" kali-agent{target_part} "),
                ("",             " ❯ "),
                ("",             " "),
            ]
            line = session.prompt(prompt_parts).strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]bye.[/]")
            break

        if not line:
            continue

        # Slash commands
        if line.startswith("/"):
            parts = line.split()
            cmd, args = parts[0].lower(), parts[1:]

            if cmd in ("/exit", "/quit", "/q"):
                console.print("[dim]bye.[/]")
                break

            if cmd == "/clear":
                agent.clear_history()
                console.clear()
                console.print(LOGO)
                console.print("[green]✓[/] Conversation cleared.\n")
                continue

            if cmd == "/compact":
                if len(agent.history) > 4:
                    with Live(Spinner("dots", text="[dim]Compacting conversation history…[/]"), refresh_per_second=20, transient=True):
                        summary = agent.chat(
                            "Summarize the entire engagement state and conversation into a concise technical context summary: "
                            "Target, verified assets, confirmed findings, and next planned action."
                        )
                    agent.clear_history()
                    agent.inject_context(f"COMPACTED SUMMARY:\n{summary}")
                    console.print("[green]✓[/] Conversation history compacted successfully.\n")
                else:
                    console.print("[dim]Conversation history is already compact.[/]")
                continue

            if cmd == "/target":
                if args:
                    agent.current_target = args[0]
                    console.print(f"[green]✓[/] Active target set to: [bold]{args[0]}[/]")
                else:
                    t = _pick_engagement()
                    if t:
                        agent.current_target = t
                        console.print(f"[green]✓[/] Active target set to: [bold]{t}[/]")
                continue

            if cmd == "/help":
                table = Table(box=box.SIMPLE_HEAD, header_style="bold red", border_style="dim", padding=(0, 2))
                table.add_column("Command", style="bold yellow", no_wrap=True)
                table.add_column("Description", style="white")
                for c, d in SLASH_CMDS.items():
                    table.add_row(c, d)
                console.print(Panel(table, title="[bold red]Kali Agent v0.1.0 Commands[/]",
                                    border_style="red", padding=(1, 2)))
                continue

            if cmd in SLASH_HANDLERS:
                try:
                    SLASH_HANDLERS[cmd](args, agent)
                except Exception as e:
                    console.print(f"[red]Error: {e}[/]")
            else:
                console.print(f"[red]Unknown command: {cmd}[/]  — type [yellow]/help[/]")
            continue

        # Natural language interaction
        console.print()
        with Live(Spinner("dots", text="[red dim]thinking…[/]"), refresh_per_second=20, transient=True):
            try:
                res = agent.chat(line, confirm_fn=_confirm_command)
            except Exception as e:
                console.print(f"[red]Agent error: {e}[/]")
                if "api_key" in str(e).lower() or "auth" in str(e).lower():
                    console.print("[dim]Verify your API key using [bold]/config[/][/]")
                continue

        console.print(Panel(Markdown(res), border_style="dim red", padding=(1, 2)))
        console.print()
