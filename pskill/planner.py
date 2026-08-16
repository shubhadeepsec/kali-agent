"""planner.py — Autonomous multi-step execution planner and task DAG for Kali Agent."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Callable

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich import box


@dataclass
class Task:
    id: str
    title: str
    description: str
    skill: str
    status: str = "pending"  # pending | running | completed | failed | skipped
    output: str = ""
    error: str = ""


@dataclass
class Plan:
    id: str
    goal: str
    target: str
    tasks: list[Task] = field(default_factory=list)
    created_at: str = ""
    status: str = "pending"  # pending | running | completed | failed


def create_default_plan(goal: str, target: str) -> Plan:
    """Generate a standard senior-grade 5-phase penetration testing plan for a target."""
    plan_id = str(uuid.uuid4())[:8]
    tasks = [
        Task(
            id="1",
            title="Scope & Target Reconnaissance",
            description=f"Passive DNS, port discovery, and service fingerprinting for {target}.",
            skill="web-recon",
        ),
        Task(
            id="2",
            title="Attack Surface Mapping & Crawling",
            description="Discover web directories, endpoints, API routes, and hidden parameter matrices.",
            skill="api-testing",
        ),
        Task(
            id="3",
            title="Vulnerability Probing & Exploit Validation",
            description="Probe for critical OWASP Top 10 vulnerabilities (SQLi, IDOR, SSRF, Auth bypass).",
            skill="injection",
        ),
        Task(
            id="4",
            title="Attack Surface Coverage Audit",
            description="Verify all identified services have completed thorough security passes.",
            skill="reporting",
        ),
        Task(
            id="5",
            title="Executive Report Compilation",
            description="Compile comprehensive Markdown and HTML assessment reports with PoCs.",
            skill="reporting",
        ),
    ]
    return Plan(id=plan_id, goal=goal, target=target, tasks=tasks)


def render_plan_tree(plan: Plan) -> Panel:
    """Render an interactive tree showing task statuses."""
    status_icons = {
        "pending": "[dim]○ Pending[/]",
        "running": "[bold cyan]⏳ Running…[/]",
        "completed": "[bold green]✓ Completed[/]",
        "failed": "[bold red]✗ Failed[/]",
        "skipped": "[dim yellow]↷ Skipped[/]",
    }

    table = Table(box=box.SIMPLE_HEAD, header_style="bold red", border_style="dim", padding=(0, 2))
    table.add_column("#", style="yellow", no_wrap=True, width=4)
    table.add_column("Phase / Task", style="bold white")
    table.add_column("Playbook", style="cyan")
    table.add_column("Status", no_wrap=True)

    for t in plan.tasks:
        table.add_row(
            t.id,
            f"[bold]{t.title}[/]\n[dim]{t.description}[/]",
            t.skill,
            status_icons.get(t.status, t.status),
        )

    return Panel(
        table,
        title=f"[bold red]Autonomous Plan — {plan.goal}[/] [dim]({plan.target or 'Local OS'})[/]",
        border_style="red",
        padding=(1, 2),
    )
