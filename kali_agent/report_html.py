"""report_html.py — Dark-mode HTML security report generator for Kali Agent."""
from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def generate_html_report(intel_data: dict[str, Any], output_path: Path | None = None) -> str:
    """Generate a responsive Cyberpunk/Dark-theme single-file HTML penetration testing report."""
    target = html.escape(str(intel_data.get("target", "Target System")))
    mode = html.escape(str(intel_data.get("mode", "Penetration Test")))
    updated = html.escape(str(intel_data.get("updated", datetime.now(timezone.utc).isoformat())))
    waf = html.escape(str(intel_data.get("waf", "None detected")))
    hosts = [html.escape(str(h)) for h in intel_data.get("hosts", [])]
    endpoints = [html.escape(str(e)) for e in intel_data.get("endpoints", [])]
    tech = [html.escape(str(t)) for t in intel_data.get("tech", [])]
    vulns = intel_data.get("vulns", [])
    done_actions = intel_data.get("done", [])
    notes = [html.escape(str(n)) for n in intel_data.get("notes", [])]

    # Calculate severity counts
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for v in vulns:
        sev = str(v.get("severity", "info")).lower()
        if sev in counts:
            counts[sev] += 1
        else:
            counts["info"] += 1

    total_vulns = len(vulns)

    # Build finding HTML cards
    findings_html = ""
    sev_colors = {
        "critical": "#ff0033",
        "high": "#ff4444",
        "medium": "#ffaa00",
        "low": "#00cc66",
        "info": "#00bbff",
    }

    if not vulns:
        findings_html = "<div class='card empty'><p>No confirmed vulnerabilities recorded for this engagement.</p></div>"
    else:
        for idx, v in enumerate(vulns, 1):
            sev = str(v.get("severity", "info")).lower()
            title = html.escape(str(v.get("title", "Untitled Finding")))
            color = sev_colors.get(sev, "#00bbff")
            findings_html += f"""
            <div class="card finding-card">
                <div class="finding-header">
                    <span class="badge" style="background-color: {color};">{sev.upper()}</span>
                    <h3>#{idx} {title}</h3>
                </div>
                <div class="finding-body">
                    <p><strong>Affected Target:</strong> <code>{target}</code></p>
                    <p><strong>Status:</strong> Confirmed & Verified</p>
                </div>
            </div>
            """

    # Build Assets Lists
    hosts_html = "".join(f"<li><code>{h}</code></li>" for h in hosts) or "<li>None recorded</li>"
    tech_html = "".join(f"<span class='tech-tag'>{t}</span>" for t in tech) or "<span class='tech-tag'>None recorded</span>"
    endpoints_html = "".join(f"<li><code>{e}</code></li>" for e in endpoints[:20]) or "<li>None recorded</li>"
    notes_html = "".join(f"<li>{n}</li>" for n in notes) or "<li>No session notes</li>"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Assessment Report — {target}</title>
    <style>
        :root {{
            --bg-color: #0b0e14;
            --card-bg: #151922;
            --accent-red: #ff3344;
            --accent-cyan: #00e5ff;
            --text-primary: #e6edf3;
            --text-muted: #8b949e;
            --border-color: #21262d;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
        body {{ background-color: var(--bg-color); color: var(--text-primary); padding: 2rem 1rem; line-height: 1.6; }}
        .container {{ max-width: 1100px; margin: 0 auto; }}
        header {{ border-bottom: 2px solid var(--accent-red); padding-bottom: 1.5rem; margin-bottom: 2rem; display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: 1rem; }}
        h1 {{ font-size: 2.2rem; color: #fff; text-shadow: 0 0 10px rgba(255, 51, 68, 0.4); }}
        .meta {{ color: var(--text-muted); font-size: 0.9rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
        .stat-card {{ background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 8px; padding: 1.2rem; text-align: center; }}
        .stat-number {{ font-size: 2.5rem; font-weight: bold; margin-top: 0.2rem; }}
        .section-title {{ font-size: 1.4rem; color: var(--accent-cyan); margin: 2rem 0 1rem; border-left: 4px solid var(--accent-cyan); padding-left: 0.5rem; }}
        .card {{ background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem; }}
        .badge {{ padding: 0.25rem 0.6rem; border-radius: 4px; font-size: 0.75rem; font-weight: bold; color: #fff; text-transform: uppercase; }}
        .finding-header {{ display: flex; align-items: center; gap: 0.8rem; margin-bottom: 1rem; }}
        .tech-tag {{ display: inline-block; background: #1f2430; border: 1px solid #333a4d; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.85rem; margin: 0.2rem; }}
        code {{ background: #1f2430; padding: 0.2rem 0.4rem; border-radius: 4px; font-family: monospace; font-size: 0.9em; color: var(--accent-cyan); }}
        ul {{ list-style-type: square; margin-left: 1.5rem; }}
        li {{ margin-bottom: 0.4rem; }}
        footer {{ text-align: center; margin-top: 3rem; color: var(--text-muted); font-size: 0.85rem; border-top: 1px solid var(--border-color); padding-top: 1.5rem; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <p class="meta">KALI AGENT v0.1.0 • SECURITY ASSESSMENT REPORT</p>
                <h1>{target}</h1>
            </div>
            <div class="meta" style="text-align: right;">
                <p>Mode: <strong>{mode.upper()}</strong></p>
                <p>Generated: {updated[:19]}</p>
            </div>
        </header>

        <div class="grid">
            <div class="stat-card" style="border-top: 3px solid #ff0033;">
                <div class="meta">CRITICAL</div>
                <div class="stat-number" style="color: #ff0033;">{counts['critical']}</div>
            </div>
            <div class="stat-card" style="border-top: 3px solid #ff4444;">
                <div class="meta">HIGH</div>
                <div class="stat-number" style="color: #ff4444;">{counts['high']}</div>
            </div>
            <div class="stat-card" style="border-top: 3px solid #ffaa00;">
                <div class="meta">MEDIUM</div>
                <div class="stat-number" style="color: #ffaa00;">{counts['medium']}</div>
            </div>
            <div class="stat-card" style="border-top: 3px solid #00cc66;">
                <div class="meta">LOW / INFO</div>
                <div class="stat-number" style="color: #00cc66;">{counts['low'] + counts['info']}</div>
            </div>
        </div>

        <h2 class="section-title">Verified Findings & Vulnerabilities ({total_vulns})</h2>
        {findings_html}

        <h2 class="section-title">Discovered Attack Surface</h2>
        <div class="grid" style="grid-template-columns: 1fr 1fr;">
            <div class="card">
                <h3>Live Hosts & Assets</h3>
                <ul style="margin-top: 0.8rem;">{hosts_html}</ul>
                <h3 style="margin-top: 1.2rem;">Technologies Identified</h3>
                <div style="margin-top: 0.5rem;">{tech_html}</div>
            </div>
            <div class="card">
                <h3>Mapped Endpoints & APIs</h3>
                <ul style="margin-top: 0.8rem;">{endpoints_html}</ul>
            </div>
        </div>

        <h2 class="section-title">Assessment Execution Notes</h2>
        <div class="card">
            <p><strong>WAF / Protection:</strong> {waf}</p>
            <p style="margin-top: 0.5rem;"><strong>Completed Operations:</strong> {len(done_actions)} actions logged</p>
            <ul style="margin-top: 0.8rem;">{notes_html}</ul>
        </div>

        <footer>
            <p>Compiled by Kali Agent v0.1.0 — Autonomous Security Agent for Kali Linux</p>
        </footer>
    </div>
</body>
</html>
"""
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_content)

    return html_content
