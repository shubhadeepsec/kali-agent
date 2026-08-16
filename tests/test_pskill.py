"""Comprehensive test suite for Kali Agent v0.1.0."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pskill import config, intel, jobs, planner
from pskill.agent import Agent, _format_openai_messages, _format_anthropic_messages
from pskill.report_html import generate_html_report
from pskill.tools import (
    execute_tool,
    run_shell,
    search_exploits,
    get_network_info,
    generate_payload,
    SKILLS,
    PLAYBOOKS_DIR,
)


def test_config():
    print("[*] Testing config module...")
    with tempfile.TemporaryDirectory() as tmpdir:
        config.CONFIG_DIR = Path(tmpdir)
        config.CONFIG_FILE = Path(tmpdir) / "config.json"
        config.ENG_DIR = Path(tmpdir) / "engagements"
        config.JOBS_DIR = Path(tmpdir) / "jobs"
        config.SESSIONS_DIR = Path(tmpdir) / "sessions"

        cfg = config.load()
        assert cfg["api_provider"] == ""
        assert not config.is_configured()

        config.set_value("api_provider", "ollama")
        assert config.is_configured()

        config.set_value("theme", "matrix")
        theme_style = config.get_theme_style()
        assert theme_style["primary"] == "bold green"

    print("  [✓] Config & theme tests passed")


def test_intel():
    print("[*] Testing intel module...")
    with tempfile.TemporaryDirectory() as tmpdir:
        config.ENG_DIR = Path(tmpdir) / "engagements"

        target = "test.example.com"
        d = intel.init(target, "bounty", "web-recon")
        assert d["target"] == target
        assert d["primary_skill"] == "web-recon"

        intel.update(target, "add-host", "10.0.0.1")
        intel.update(target, "add-endpoint", "/api/v1/users")
        intel.update(target, "add-tech", "FastAPI")
        intel.update(target, "add-vuln", "IDOR on user endpoint", severity="high")
        intel.update(target, "mark-done", "recon_scan")
        intel.update(target, "set-waf", "Cloudflare")

        d2 = intel.load(target)
        assert "10.0.0.1" in d2["hosts"]
        assert "/api/v1/users" in d2["endpoints"]
        assert "FastAPI" in d2["tech"]
        assert d2["vulns"][0]["title"] == "IDOR on user endpoint"
        assert d2["vulns"][0]["severity"] == "high"

        intel.log_evidence(target, "web-recon", "httpx -l hosts.txt", "2 hosts live", "all up")
        ev_file = intel.evidence_file(target)
        assert ev_file.exists()

        nmap_sample = """
Nmap scan report for test.example.com (10.0.0.1)
Host is up (0.001s latency).
PORT     STATE SERVICE VERSION
80/tcp   open  http    nginx 1.18.0
443/tcp  open  https   nginx 1.18.0
"""
        intel.ingest_nmap(target, nmap_sample)
        d3 = intel.load(target)
        assert len(d3["ports"].get("test.example.com", [])) == 2

    print("  [✓] Intel tests passed")


def test_jobs():
    print("[*] Testing background jobs module...")
    with tempfile.TemporaryDirectory() as tmpdir:
        config.JOBS_DIR = Path(tmpdir) / "jobs"
        jobs.JOBS_METADATA_FILE = config.JOBS_DIR / "jobs.json"

        # Start a background job
        job = jobs.start_job("echo 'BG_JOB_OUTPUT' && sleep 1", desc="test echo")
        job_id = job["id"]
        assert job["status"] == "running"

        time.sleep(0.3)
        log_content = jobs.tail_job(job_id)
        assert "BG_JOB_OUTPUT" in log_content

        job_list = jobs.list_jobs()
        assert any(j["id"] == job_id for j in job_list)

        # Kill job
        jobs.kill_job(job_id)
        killed_job = jobs.get_job(job_id)
        assert killed_job["status"] == "killed"

    print("  [✓] Background jobs tests passed")


def test_planner():
    print("[*] Testing planner module...")
    plan = planner.create_default_plan("Full assessment", "target.com")
    assert len(plan.tasks) == 5
    assert plan.tasks[0].status == "pending"

    panel = planner.render_plan_tree(plan)
    assert panel is not None

    print("  [✓] Planner tests passed")


def test_html_report():
    print("[*] Testing HTML report generation...")
    intel_data = {
        "target": "acme.corp",
        "mode": "bounty",
        "hosts": ["10.0.0.5"],
        "endpoints": ["/api/v1/auth"],
        "tech": ["Node.js", "Express"],
        "vulns": [{"title": "SQL Injection on /search", "severity": "critical"}],
        "notes": ["Target authenticated"],
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "report.html"
        html_out = generate_html_report(intel_data, output_path=out_path)
        assert out_path.exists()
        assert "SQL Injection on /search" in html_out
        assert "CRITICAL" in html_out

    print("  [✓] HTML report tests passed")


def test_tools():
    print("[*] Testing tools and payloads...")
    # Shell execution
    res = run_shell("echo 'hello kali-agent'", timeout=5)
    assert res.ok
    assert "hello kali-agent" in res.stdout

    # Network info
    net = get_network_info()
    assert "default_gateway" in net

    # Payload generator
    p = generate_payload("bash", "10.10.14.5", 9001)
    assert "10.10.14.5" in p["payload"]
    assert "nc -lvnp 9001" in p["listener_netcat"]

    # Tool dispatch
    with tempfile.TemporaryDirectory() as tmpdir:
        config.ENG_DIR = Path(tmpdir) / "engagements"
        target = "tool-test.com"
        intel.init(target)

        out = execute_tool("update_intel", {"target": target, "command": "add-host", "value": "192.168.1.5"})
        assert "updated" in out.lower()

        intel_out = execute_tool("get_intel", {"target": target})
        assert "192.168.1.5" in intel_out

        pb_out = execute_tool("get_playbook", {"skill": "web-recon"})
        assert "Web Recon" in pb_out

        test_file = Path(tmpdir) / "test_out.txt"
        execute_tool("write_file", {"path": str(test_file), "content": "KALI_AGENT_DATA"})
        read_out = execute_tool("read_file", {"path": str(test_file)})
        assert read_out == "KALI_AGENT_DATA"

        find_out = execute_tool("find_files", {"path": tmpdir, "pattern": "test_out.txt"})
        assert "test_out.txt" in find_out

    print("  [✓] Tools & OS control tests passed")


def test_agent_sessions():
    print("[*] Testing agent sessions and token metrics...")
    with tempfile.TemporaryDirectory() as tmpdir:
        config.SESSIONS_DIR = Path(tmpdir) / "sessions"

        agent = Agent(session_id="test_session_1")
        agent.current_target = "10.10.10.5"
        agent.total_input_tokens = 5000
        agent.total_output_tokens = 2000
        agent.history = [{"role": "user", "content": "scan target"}]
        agent.save_session()

        loaded = Agent.load_session("test_session_1")
        assert loaded is not None
        assert loaded.current_target == "10.10.10.5"
        assert loaded.total_input_tokens == 5000
        assert loaded.total_output_tokens == 2000
        assert len(loaded.history) == 1

    print("  [✓] Agent session persistence tests passed")


def test_cli_flags():
    print("[*] Testing CLI flags...")
    res = subprocess.run([sys.executable, str(ROOT / "kali_agent.py"), "--version"], capture_output=True, text=True)
    assert "kali-agent v0.1.0" in res.stdout

    res_help = subprocess.run([sys.executable, str(ROOT / "kali_agent.py"), "--help"], capture_output=True, text=True)
    assert "Kali Agent" in res_help.stdout
    assert "/plan" in res_help.stdout
    assert "/jobs" in res_help.stdout
    assert "/revshell" in res_help.stdout

    print("  [✓] CLI flags tests passed")


def main():
    print("=" * 60)
    print("KALI AGENT v0.1.0 VERIFICATION SUITE")
    print("=" * 60)
    test_config()
    test_intel()
    test_jobs()
    test_planner()
    test_html_report()
    test_tools()
    test_agent_sessions()
    test_cli_flags()
    print("=" * 60)
    print("ALL v0.1.0 TESTS PASSED WITH 0 ERRORS")
    print("=" * 60)


if __name__ == "__main__":
    main()
