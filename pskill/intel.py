"""intel.json — per-target state machine. Tracks hosts, ports, endpoints, vulns, done actions."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from . import config

TEMPLATE: dict = {
    "target": "",
    "mode": "bounty",
    "primary_skill": "web-recon",
    "scope_confirmed": False,
    "updated": "",
    "hosts": [],
    "ports": {},
    "services": [],
    "endpoints": [],
    "tech": [],
    "params": [],
    "vulns": [],
    "done": [],
    "blocked": [],
    "notes": [],
    "waf": "",
}


def slugify(s: str) -> str:
    s = re.sub(r"https?://", "", s.strip().lower())
    return re.sub(r"[^a-z0-9._-]+", "-", s).strip("-") or "target"


def path(target: str) -> Path:
    return config.ENG_DIR / slugify(target)


def intel_file(target: str) -> Path:
    return path(target) / "intel.json"


def evidence_file(target: str) -> Path:
    return path(target) / "evidence.md"


def load(target: str) -> dict:
    fp = intel_file(target)
    if not fp.exists():
        return {}
    return json.loads(fp.read_text())


def save(target: str, data: dict) -> None:
    data["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    intel_file(target).write_text(json.dumps(data, indent=2) + "\n")


def init(target: str, mode: str = "bounty", skill: str = "web-recon") -> dict:
    p = path(target)
    p.mkdir(parents=True, exist_ok=True)
    fp = intel_file(target)
    if fp.exists():
        return load(target)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data = {**TEMPLATE, "target": target, "mode": mode,
            "primary_skill": skill, "updated": now,
            "notes": [f"Engagement initialized {now}"]}
    fp.write_text(json.dumps(data, indent=2) + "\n")
    # init evidence.md
    ef = evidence_file(target)
    if not ef.exists():
        ef.write_text(f"# Evidence Log — {target}\n\n| Time | Skill | Command | Result | Notes |\n|---|---|---|---|---|\n")
    return data


def _uniq(lst: list, item) -> None:
    if item not in lst:
        lst.append(item)


def update(target: str, command: str, value: str,
           severity: str = "info", reason: str = "") -> dict:
    data = load(target)
    if not data:
        raise ValueError(f"No engagement for '{target}'. Run: /init")

    if command == "mark-done":
        _uniq(data.setdefault("done", []), value)
    elif command == "mark-blocked":
        entry = value if not reason else f"{value} ({reason})"
        _uniq(data.setdefault("blocked", []), entry)
    elif command == "note":
        _uniq(data.setdefault("notes", []), value)
    elif command == "add-host":
        _uniq(data.setdefault("hosts", []), value)
    elif command == "add-endpoint":
        _uniq(data.setdefault("endpoints", []), value)
    elif command == "add-tech":
        _uniq(data.setdefault("tech", []), value)
    elif command == "add-param":
        _uniq(data.setdefault("params", []), value)
    elif command == "set-waf":
        data["waf"] = value
    elif command == "add-vuln":
        entry = {"title": value, "severity": severity}
        if entry not in data.setdefault("vulns", []):
            data["vulns"].append(entry)
    elif command == "set-skill":
        data["primary_skill"] = value
    elif command == "scope-confirmed":
        data["scope_confirmed"] = True

    save(target, data)
    return data


def log_evidence(target: str, skill: str, command: str,
                 result: str, notes: str = "") -> None:
    ef = evidence_file(target)
    if not ef.exists():
        ef.write_text(f"# Evidence Log — {target}\n\n| Time | Skill | Command | Result | Notes |\n|---|---|---|---|---|\n")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    row = f"| {now} | {skill} | `{command}` | {result} | {notes} |\n"
    with open(ef, "a") as f:
        f.write(row)


def list_engagements() -> list[dict]:
    if not config.ENG_DIR.exists():
        return []
    results = []
    for p in sorted(config.ENG_DIR.iterdir()):
        fp = p / "intel.json"
        if fp.exists():
            try:
                results.append(json.loads(fp.read_text()))
            except Exception:
                pass
    return results


def ingest_nmap(target: str, text: str) -> dict:
    data = load(target)
    if not data:
        raise ValueError(f"No engagement for '{target}'")
    host = None
    for line in text.splitlines():
        m = re.search(r"Nmap scan report for (.+)$", line)
        if m:
            host = m.group(1).strip()
            _uniq(data.setdefault("hosts", []), host)
            data.setdefault("ports", {}).setdefault(host, [])
            continue
        m = re.search(r"^(\d+)/tcp\s+open\s+(\S+)\s*(.*)$", line)
        if m and host:
            port, svc, rest = int(m.group(1)), m.group(2), m.group(3).strip()
            entry = {"port": port, "proto": "tcp", "service": svc, "version": rest}
            ports = data["ports"].setdefault(host, [])
            if not any(p.get("port") == port for p in ports):
                ports.append(entry)
            _uniq(data.setdefault("services", []), f"{host}:{port}/{svc}")
    save(target, data)
    return data
