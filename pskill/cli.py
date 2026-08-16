"""cli.py — Interactive Claude Code-style REPL for pskill."""
from __future__ import annotations

import json
import os
import sys
import threading
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

# ── Console ────────────────────────────────────────────────────────────────────
console = Console()

VERSION = "3.0.0"

LOGO = """[bold red]
  ██████╗ ███████╗██╗  ██╗██╗██╗     ██╗
  ██╔══██╗██╔════╝██║ ██╔╝██║██║     ██║
  ██████╔╝███████╗█████╔╝ ██║██║     ██║
  ██╔═══╝ ╚════██║██╔═██╗ ██║██║     ██║
  ██║     ███████║██║  ██╗██║███████╗███████╗
  ╚═╝     ╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝[/bold red]"""

SLASH_CMDS = {
    "/config":      "View or set configuration (API key, model, provider)",
    "/init":        "Initialize a new engagement target",
    "/intel":       "Show target intelligence (hosts, vulns, endpoints)",
    "/scope":       "Set or confirm authorization scope",
    "/playbook":    "Load a skill playbook into context",
    "/engagements": "List all saved engagements",
    "/clear":       "Clear conversation history",
    "/compact":     "Summarize and compress conversation history",
    "/target":      "Switch active target",
    "/report":      "Generate engagement report",
    "/run":         "Run a shell command directly",
    "/help":        "Show this help",
    "/exit":        "Exit pskill",
}


# ── Setup wizard (first run) ──────────────────────────────────────────────────

def setup_wizard() -> None:
    """Interactive first-run config — like Claude Code's onboarding."""
    console.print()
    console.print(Panel(
        "[bold white]Welcome to pskill![/]\n\n"
        "Let's set up your AI provider. You need an API key from one of:\n"
        "  • [cyan]Anthropic[/] (claude-sonnet) — [dim]https://console.anthropic.com[/]\n"
        "  • [cyan]OpenAI[/] (gpt-4o) — [dim]https://platform.openai.com[/]\n"
        "  • [cyan]Gemini[/] (free tier) — [dim]https://aistudio.google.com[/]\n"
        "  • [cyan]Groq[/] (free, fast) — [dim]https://console.groq.com[/]\n"
        "  • [cyan]Ollama[/] (local, no key needed) — [dim]https://ollama.ai[/]",
        title="[bold red]First-time Setup[/]",
        border_style="red",
        padding=(1, 2),
    ))

    provider = Prompt.ask(
        "\n[bold yellow]Provider[/]",
        choices=["anthropic", "openai", "gemini", "groq", "ollama"],
        default="anthropic",
    )

    cfg = config.load()
    cfg["api_provider"] = provider

    defaults = config.PROVIDER_DEFAULTS.get(provider, {})

    if provider != "ollama":
        key = Prompt.ask(f"[bold yellow]API Key[/] for {provider}", password=True)
        cfg["api_key"] = key

    model_default = defaults.get("model", "")
    model = Prompt.ask(f"[bold yellow]Model[/]", default=model_default)
    cfg["model"] = model

    auto = Confirm.ask("[bold yellow]Auto-approve shell commands?[/] (like --dangerously-skip-permissions)", default=False)
    cfg["auto_approve"] = auto

    config.save(cfg)
    console.print(f"\n[bold green]✓[/] Config saved → [dim]{config.CONFIG_FILE}[/]")
    console.print("[dim]You can change these anytime with [bold]/config[/][/]\n")


# ── Slash command handlers ────────────────────────────────────────────────────

def handle_config(args: list[str], agent: Agent) -> None:
    cfg = config.load()

    if not args:
        # Show config
        table = Table(box=box.SIMPLE_HEAD, header_style="bold red", border_style="dim", padding=(0, 2))
        table.add_column("Key", style="yellow", no_wrap=True)
        table.add_column("Value", style="white")
        for k, v in cfg.items():
            val = "***" if k == "api_key" and v else str(v)
            table.add_column if False else None
            table.add_row(k, val)
        console.print(Panel(table, title="[bold red]Configuration[/]", border_style="red", padding=(1, 2)))
        console.print(f"[dim]Config file: {config.CONFIG_FILE}[/]")
        return

    if args[0] == "set" and len(args) >= 3:
        key, value = args[1], " ".join(args[2:])
        if key == "auto_approve":
            value = value.lower() in ("true", "1", "yes")
        config.set_value(key, value)
        console.print(f"[green]✓[/] {key} = {value}")
    elif args[0] == "setup":
        setup_wizard()
    else:
        console.print("[dim]Usage: /config | /config setup | /config set <key> <value>[/]")


def handle_init(args: list[str], agent: Agent) -> None:
    if args:
        target = args[0]
        mode = args[1] if len(args) > 1 else "bounty"
        skill = args[2] if len(args) > 2 else "web-recon"
    else:
        target = Prompt.ask("[bold yellow]Target[/] (hostname/IP/domain)")
        mode = Prompt.ask("[bold yellow]Mode[/]", choices=["bounty", "vdp", "lab", "ctf"], default="bounty")
        skill = Prompt.ask("[bold yellow]Primary skill[/]", default="web-recon")

    data = intel_mod.init(target, mode, skill)
    agent.current_target = target
    console.print(
        Panel(
            f"[bold white]{target}[/]\n"
            f"Mode: [cyan]{mode}[/]  Skill: [yellow]{skill}[/]\n"
            f"Path: [dim]{intel_mod.path(target)}[/]",
            title="[bold green]✓ Engagement Ready[/]",
            border_style="green",
            padding=(1, 2),
        )
    )
    # Inject context to agent
    agent.inject_context(
        f"New engagement initialized.\nTarget: {target}\nMode: {mode}\nPrimary skill: {skill}\n"
        f"Intel: {json.dumps(data, indent=2)}"
    )


def handle_intel(args: list[str], agent: Agent) -> None:
    target = args[0] if args else agent.current_target
    if not target:
        target = _pick_engagement()
    if not target:
        return

    data = intel_mod.load(target)
    if not data:
        console.print(f"[red]No engagement for '{target}'. Run /init[/]"); return

    sev_color = {"critical": "bold red", "high": "red", "medium": "yellow", "low": "green", "info": "dim"}

    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold dim", no_wrap=True, min_width=12)
    grid.add_column()
    grid.add_row("Target",  f"[bold white]{data.get('target','?')}[/]")
    grid.add_row("Mode",    f"[cyan]{data.get('mode','?')}[/]")
    grid.add_row("Skill",   f"[yellow]{data.get('primary_skill','?')}[/]")
    grid.add_row("Updated", f"[dim]{data.get('updated','?')}[/]")
    if data.get("waf"):
        grid.add_row("WAF",  f"[red]{data['waf']}[/]")

    def lst(items: list, style: str = "white", limit: int = 12) -> str:
        if not items: return "[dim]none[/]"
        return "\n".join(f"[{style}]• {i}[/]" for i in items[:limit]) + \
               (f"\n[dim]  … +{len(items)-limit} more[/]" if len(items) > limit else "")

    grid.add_row("Hosts",     lst(data.get("hosts", []),     "green"))
    grid.add_row("Endpoints", lst(data.get("endpoints", []), "blue"))
    grid.add_row("Tech",      lst(data.get("tech", []),      "magenta"))

    vulns = data.get("vulns", [])
    vuln_text = "\n".join(
        f"[{sev_color.get(v.get('severity','info'),'white')}]• [{v.get('severity','?').upper()}] {v.get('title','?')}[/]"
        for v in vulns
    ) if vulns else "[dim]none[/]"
    grid.add_row("Vulns",  vuln_text)
    grid.add_row("Done",   f"[dim]{len(data.get('done',[]))} actions completed[/]")

    console.print(Panel(grid, title=f"[bold red]Intel — {target}[/]",
                        border_style="red", padding=(1, 2)))


def handle_scope(args: list[str], agent: Agent) -> None:
    if not args:
        console.print(Panel(
            "[bold yellow]Set authorization before testing:[/]\n\n"
            "  [white]/scope lab[/]     [dim]→ local/lab target (127.0.0.1, localhost)[/]\n"
            "  [white]/scope ctf <ip>[/]  [dim]→ CTF/HackTheBox target[/]\n"
            "  [white]/scope bounty <domain> <program>[/]  [dim]→ bug bounty target[/]",
            title="[bold red]Scope[/]",
            border_style="red",
        ))
        return

    mode = args[0].lower()
    cfg = config.load()

    if mode == "lab":
        target = args[1] if len(args) > 1 else "127.0.0.1"
        console.print(f"[green]✓[/] Scope set: Local Lab → [bold]{target}[/]")
        if not intel_mod.load(target):
            intel_mod.init(target, "lab", "web-recon")
        intel_mod.update(target, "scope-confirmed", "true")
        agent.current_target = target
        agent.inject_context(f"Scope confirmed: Local Lab — target {target}. Proceed with testing.")

    elif mode == "ctf":
        target = args[1] if len(args) > 1 else Prompt.ask("[bold yellow]Target IP[/]")
        console.print(f"[green]✓[/] Scope set: CTF → [bold]{target}[/]")
        if not intel_mod.load(target):
            intel_mod.init(target, "ctf", "web-recon")
        intel_mod.update(target, "scope-confirmed", "true")
        agent.current_target = target
        agent.inject_context(f"Scope confirmed: CTF/Practice — target {target}. Proceed with testing.")

    elif mode == "bounty":
        target  = args[1] if len(args) > 1 else Prompt.ask("[bold yellow]Target domain[/]")
        program = args[2] if len(args) > 2 else Prompt.ask("[bold yellow]Program name[/]")
        console.print(f"[green]✓[/] Scope set: Bug Bounty — [bold]{program}[/] → [bold]{target}[/]")
        if not intel_mod.load(target):
            intel_mod.init(target, "bounty", "web-recon")
        intel_mod.update(target, "scope-confirmed", "true")
        intel_mod.update(target, "note", f"Bug bounty program: {program}")
        agent.current_target = target
        agent.inject_context(
            f"Scope confirmed: Bug Bounty program '{program}', target '{target}'. "
            "In scope: main domain and subdomains. Out of scope: DoS, social engineering, third-party infra. Proceed."
        )
    else:
        console.print("[red]Unknown scope mode. Use: lab | ctf | bounty[/]")


def handle_playbook(args: list[str], agent: Agent) -> None:
    if not args:
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        table.add_column(style="bold yellow", no_wrap=True)
        table.add_column(style="dim")
        for s in SKILLS:
            table.add_row(s, f"/playbook {s}")
        console.print(Panel(table, title="[bold red]Playbooks[/]", border_style="red"))
        skill = Prompt.ask("[bold yellow]Load playbook[/]", choices=SKILLS)
    else:
        skill = args[0]

    md = PLAYBOOKS_DIR / skill / "SKILL.md"
    if not md.exists():
        console.print(f"[red]Playbook not found: {skill}[/]"); return

    content = md.read_text()
    # inject into agent context
    agent.inject_context(f"PLAYBOOK LOADED: {skill}\n\n{content}")
    console.print(f"[green]✓[/] Playbook [bold]{skill}[/] loaded into context.")
    console.print(Syntax(content[:3000], "markdown", theme="monokai",
                          word_wrap=True, background_color="default"))


def handle_engagements(_: list[str], agent: Agent) -> None:
    engs = intel_mod.list_engagements()
    if not engs:
        console.print("[dim]No engagements yet. Use /init to create one.[/]"); return

    table = Table(box=box.SIMPLE_HEAD, header_style="bold red", border_style="dim", padding=(0, 2))
    table.add_column("Target",  style="bold white")
    table.add_column("Mode",    style="cyan")
    table.add_column("Skill",   style="yellow")
    table.add_column("Hosts",   style="green")
    table.add_column("Vulns",   style="red")
    table.add_column("Updated", style="dim")

    for d in engs:
        table.add_row(
            d.get("target", "?"),
            d.get("mode", "?"),
            d.get("primary_skill", "?"),
            str(len(d.get("hosts", []))),
            str(len(d.get("vulns", []))),
            d.get("updated", "?")[:10],
        )
    console.print(Panel(table, title="[bold red]Engagements[/]", border_style="red", padding=(1, 2)))


def handle_report(args: list[str], agent: Agent) -> None:
    target = args[0] if args else agent.current_target
    if not target:
        target = _pick_engagement()
    if not target:
        return

    data = intel_mod.load(target)
    if not data:
        console.print(f"[red]No intel for '{target}'[/]"); return

    # Ask agent to write the report
    prompt = (
        f"Generate a full penetration testing report for target '{target}'. "
        f"Use this intel: {json.dumps(data, indent=2)}\n\n"
        "Format: Executive Summary, Scope, Findings (severity/title/endpoint/PoC/impact/remediation), "
        "Attack Surface Coverage, Recommendations. Save as report.md using write_file."
    )
    with Live(Spinner("dots", text="[cyan]Generating report…[/]"), refresh_per_second=20):
        result = agent.chat(prompt)

    console.print(Markdown(result[:5000]))
    out = intel_mod.path(target) / "report.md"
    console.print(f"\n[green]✓[/] Report saved → {out}")


def handle_run(args: list[str], agent: Agent) -> None:
    if not args:
        console.print("[dim]Usage: /run <command>[/]"); return
    cmd = " ".join(args)
    console.print(f"[dim]$ {cmd}[/]")
    result = run_shell(cmd, timeout=120)
    console.print(str(result) or "[dim](no output)[/]")


def _pick_engagement() -> str | None:
    engs = intel_mod.list_engagements()
    if not engs:
        console.print("[red]No engagements. Run /init first.[/]")
        return None
    if len(engs) == 1:
        return engs[0]["target"]
    for i, e in enumerate(engs, 1):
        console.print(f"  [bold yellow]{i}[/] {e.get('target','?')}")
    try:
        return engs[int(Prompt.ask("Select")) - 1]["target"]
    except Exception:
        return None


SLASH_HANDLERS = {
    "/config":      handle_config,
    "/init":        handle_init,
    "/intel":       handle_intel,
    "/scope":       handle_scope,
    "/playbook":    handle_playbook,
    "/engagements": handle_engagements,
    "/report":      handle_report,
    "/run":         handle_run,
}


# ── Main REPL ─────────────────────────────────────────────────────────────────

def _confirm_command(cmd: str, desc: str) -> bool:
    """Ask user to approve a shell command — like Claude Code's approval UI."""
    console.print()
    console.print(Panel(
        f"[dim]{desc}[/]\n\n[bold white]$ {cmd}[/]",
        title="[bold yellow]⚡ Run Command?[/]",
        border_style="yellow",
        padding=(1, 2),
    ))
    return Confirm.ask("[bold yellow]Allow[/]", default=True)


def _stream_token(text: str) -> None:
    """Print streaming token without newline."""
    console.print(text, end="", markup=False)


def _status_bar(agent: Agent) -> str:
    parts = []
    if agent.current_target:
        parts.append(f"[cyan]target: {agent.current_target}[/]")
    else:
        parts.append("[dim]no target[/]")
    provider = config.get("api_provider", "")
    model = config.get("model", "")
    if provider:
        parts.append(f"[dim]{provider}/{model}[/]")
    else:
        parts.append("[red]no model configured[/]")
    turns = len([m for m in agent.history if m.get("role") == "user"])
    if turns:
        parts.append(f"[dim]{turns} turns[/]")
    return "  [dim]│[/]  ".join(parts)


def run() -> None:
    """Entry point — interactive REPL."""
    # First-run setup
    if not config.is_configured():
        console.print(LOGO)
        setup_wizard()

    console.print(LOGO)
    agent = Agent()

    # Status bar
    console.print(Panel(
        _status_bar(agent),
        border_style="dim",
        padding=(0, 2),
    ))
    console.print(
        "[dim]Type your task naturally, or use [bold]/help[/] for slash commands.[/]\n"
    )

    # prompt_toolkit REPL
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
            # Compact prompt like Claude Code
            target_part = f"[{agent.current_target}]" if agent.current_target else ""
            prompt_parts = [
                ("class:prompt", f" pskill{target_part} "),
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
                console.print("[dim]bye.[/]"); break

            if cmd == "/clear":
                agent.clear_history()
                console.clear()
                console.print(LOGO)
                console.print("[green]✓[/] Conversation cleared.\n")
                continue

            if cmd == "/compact":
                # Summarize and trim
                if len(agent.history) > 4:
                    console.print("[dim]Compacting history…[/]")
                    summary = agent.chat(
                        "Summarize the entire conversation so far into a concise context block "
                        "with: target, confirmed findings, completed actions, and current status. "
                        "Be technical and precise."
                    )
                    agent.clear_history()
                    agent.inject_context(f"[COMPACTED CONTEXT]\n{summary}")
                    console.print("[green]✓[/] History compacted.\n")
                else:
                    console.print("[dim]History too short to compact.[/]")
                continue

            if cmd == "/target":
                if args:
                    agent.current_target = args[0]
                    console.print(f"[green]✓[/] Active target: [bold]{args[0]}[/]")
                else:
                    t = _pick_engagement()
                    if t: agent.current_target = t
                continue

            if cmd == "/help":
                table = Table(box=box.SIMPLE_HEAD, header_style="bold red",
                              border_style="dim", padding=(0, 2))
                table.add_column("Command", style="bold yellow", no_wrap=True)
                table.add_column("Description", style="white")
                for c, d in SLASH_CMDS.items():
                    table.add_row(c, d)
                console.print(Panel(table, title="[bold red]pskill commands[/]",
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

        # Natural language → agent
        console.print()
        response_parts = []

        def stream(text: str) -> None:
            response_parts.append(text)

        with Live(Spinner("dots", text="[red dim]thinking…[/]"), refresh_per_second=20,
                  transient=True):
            try:
                result = agent.chat(line, confirm_fn=_confirm_command, stream_fn=stream)
            except Exception as e:
                console.print(f"\n[red]Agent error: {e}[/]")
                if "api_key" in str(e).lower() or "auth" in str(e).lower():
                    console.print("[dim]Check your API key with [bold]/config[/][/]")
                continue

        console.print()
        console.print(Panel(
            Markdown(result),
            border_style="dim red",
            padding=(1, 2),
        ))
        console.print()
