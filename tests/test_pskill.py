"""Comprehensive automated test suite for pskill AI agent."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pskill import config, intel
from pskill.agent import Agent, _format_openai_messages, _format_anthropic_messages
from pskill.tools import execute_tool, run_shell, SKILLS, PLAYBOOKS_DIR


def test_config():
    print("[*] Testing config module...")
    with tempfile.TemporaryDirectory() as tmpdir:
        config.CONFIG_DIR = Path(tmpdir)
        config.CONFIG_FILE = Path(tmpdir) / "config.json"
        config.ENG_DIR = Path(tmpdir) / "engagements"

        cfg = config.load()
        assert cfg["api_provider"] == ""
        assert not config.is_configured()

        # Test Ollama without key
        config.set_value("api_provider", "ollama")
        assert config.is_configured()

        # Test Anthropic with key
        config.set_value("api_provider", "anthropic")
        config.set_value("api_key", "sk-ant-test123456")
        assert config.is_configured()
        assert config.get("api_key") == "sk-ant-test123456"
        assert config.get("model") == "claude-sonnet-4-5"

    print("  [✓] Config tests passed")


def test_intel():
    print("[*] Testing intel module...")
    with tempfile.TemporaryDirectory() as tmpdir:
        config.ENG_DIR = Path(tmpdir) / "engagements"

        target = "test.example.com"
        d = intel.init(target, "bounty", "web-recon")
        assert d["target"] == target
        assert d["primary_skill"] == "web-recon"

        # Test updates
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
        assert "recon_scan" in d2["done"]
        assert d2["waf"] == "Cloudflare"

        # Test evidence logging
        intel.log_evidence(target, "web-recon", "httpx -l hosts.txt", "2 hosts live", "all up")
        ev_file = intel.evidence_file(target)
        assert ev_file.exists()
        assert "httpx -l hosts.txt" in ev_file.read_text()

        # Test Nmap ingestion
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


def test_tools():
    print("[*] Testing tools module...")
    # Shell execution
    res = run_shell("echo 'hello pskill'", timeout=5)
    assert res.ok
    assert "hello pskill" in res.stdout

    # Tool dispatch
    with tempfile.TemporaryDirectory() as tmpdir:
        config.ENG_DIR = Path(tmpdir) / "engagements"
        target = "tool-test.com"
        intel.init(target)

        # Update intel tool
        out = execute_tool("update_intel", {"target": target, "command": "add-host", "value": "192.168.1.5"})
        assert "updated" in out.lower()

        # Get intel tool
        intel_out = execute_tool("get_intel", {"target": target})
        assert "192.168.1.5" in intel_out

        # Playbook tool
        pb_out = execute_tool("get_playbook", {"skill": "web-recon"})
        assert "Web Recon" in pb_out

        # Write & Read file tool
        test_file = Path(tmpdir) / "test_out.txt"
        execute_tool("write_file", {"path": str(test_file), "content": "PSKILL_TEST_DATA"})
        read_out = execute_tool("read_file", {"path": str(test_file)})
        assert read_out == "PSKILL_TEST_DATA"

    print("  [✓] Tools tests passed")


def test_message_formatting():
    print("[*] Testing message serialization for AI providers...")
    history = [
        {"role": "user", "content": "Scan 10.0.0.1"},
        {
            "role": "assistant",
            "content": "I will run nmap.",
            "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {"name": "run_command", "arguments": json.dumps({"command": "nmap 10.0.0.1", "description": "scan"})},
                }
            ],
        },
        {
            "role": "tool",
            "tool_call_id": "call_123",
            "name": "run_command",
            "content": "Port 80 open",
        },
    ]

    # Test OpenAI formatting
    openai_msgs = _format_openai_messages(history)
    assert len(openai_msgs) == 3
    assert openai_msgs[0]["role"] == "user"
    assert openai_msgs[1]["role"] == "assistant"
    assert "tool_calls" in openai_msgs[1]
    assert openai_msgs[2]["role"] == "tool"
    assert openai_msgs[2]["tool_call_id"] == "call_123"

    # Test Anthropic formatting
    anthropic_msgs = _format_anthropic_messages(history)
    assert len(anthropic_msgs) == 3
    assert anthropic_msgs[0]["role"] == "user"
    assert anthropic_msgs[1]["role"] == "assistant"
    assert isinstance(anthropic_msgs[1]["content"], list)
    assert anthropic_msgs[1]["content"][1]["type"] == "tool_use"
    assert anthropic_msgs[2]["role"] == "user"
    assert anthropic_msgs[2]["content"][0]["type"] == "tool_result"
    assert anthropic_msgs[2]["content"][0]["tool_use_id"] == "call_123"

    print("  [✓] Message serialization tests passed")


def test_cli_flags():
    print("[*] Testing CLI executable and flags...")
    res = subprocess.run([sys.executable, str(ROOT / "pskill.py"), "--version"], capture_output=True, text=True)
    assert "pskill v3.0.0" in res.stdout

    res_help = subprocess.run([sys.executable, str(ROOT / "pskill.py"), "--help"], capture_output=True, text=True)
    assert "pskill" in res_help.stdout
    assert "/scope" in res_help.stdout

    print("  [✓] CLI flags tests passed")


def main():
    print("=" * 60)
    print("RUNNING PSKILL VERIFICATION SUITE")
    print("=" * 60)
    test_config()
    test_intel()
    test_tools()
    test_message_formatting()
    test_cli_flags()
    print("=" * 60)
    print("ALL TESTS PASSED WITH 0 ERRORS")
    print("=" * 60)


if __name__ == "__main__":
    main()
