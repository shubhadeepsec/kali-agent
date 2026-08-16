"""cli.py — Interactive Claude Code-style REPL and CLI interface for pskill."""
from __future__ import annotations

import argparse
import json
import os
import sys
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

from . import config, intel as intel_mod
from .agent import Agent
from .tools import SKILLS, PLAYBOOKS_DIR, run_shell

console = Console()

VERSION = "3.0.0"

LOGO = """[bold red]
  ██╗  ██╗ █████╗ ██╗     ██╗     █████╗  ██████╗ ███████╗███╗   ██╗████████╗
  ██║ ██╔╝██╔══██╗██║     ██║    ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝
  █████╔╝ ███████║██║     ██║    ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   
  ██╔═██╗ ██╔══██║██║     ██║    ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   
  ██║  ██╗██║  ██║███████╗██║    ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   
  ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝    ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   [/bold red]"""

SLASH_CMDS = {
    "/scope":       "Set or confirm authorization scope (lab, ctf, bounty)",
    "/init":        "Initialize a new engagement target & workspace",
    "/intel":       "Show target intelligence dashboard (hosts, ports, vulns)",
    "/playbook":    "Load a domain skill playbook into agent context",
    "/engagements": "List all saved engagements and findings summary",
    "/report":      "Compile and save Markdown penetration testing report",
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
        "[bold white]Welcome to Kali Agent![/]\n\n"
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

    # /config set <key> <value> OR /config <key> <value>
    cmd_args = args[1:] if args[0] == "set" else args
    if len(cmd_args) >= 2:
        key, value = cmd_args[0], " ".join(cmd_args[1:])
        if key in ("auto_approve", "scope_required"):
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

    # Support flags or positional
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

    # Parse flags if present
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
    target = args[0] if args else agent.current_target
    if not target:
        target = _pick_engagement()
    if not target:
        return

    data = intel_mod.load(target)
    if not data:
        console.print(f"[red]No intelligence found for '{target}'.[/]")
        return

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

    out_file = intel_mod.path(target) / "report.md"
    if not out_file.exists():
        out_file.write_text(result)

    console.print(Markdown(result[:4000]))
    console.print(f"\n[green]✓[/] Report successfully compiled → [bold]{out_file}[/]")


def handle_run(args: list[str], agent: Agent) -> None:
    if not args:
        console.print("[dim]Usage: /run <command>[/]")
        return
    cmd = " ".join(args)
    console.print(f"[dim]$ {cmd}[/]")
    res = run_shell(cmd, timeout=120)
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
    "/init":        handle_init,
    "/intel":       handle_intel,
    "/playbook":    handle_playbook,
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

    turns = len([m for m in agent.history if m.get("role") == "user"])
    if turns:
        parts.append(f"[dim]{turns} turns[/]")

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
        console.print(Panel(table, title="[bold red]Kali Agent — Autonomous AI for Kali Linux[/]",
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
            # Natural language one-shot prompt
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
    session: PromptSession = PromptSession(
        history=FileHistory(str(config.HIST_FILE)),
        auto_suggest=AutoSuggestFromHistory(),
        completer=completer,
        style=PTKStyle.from_dict({"prompt": "ansired bold", "": "ansiwhite"}),
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
                console.print(Panel(table, title="[bold red]pskill Commands[/]",
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
