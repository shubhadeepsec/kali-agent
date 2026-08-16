"""Config management — ~/.pskill/config.json, like Claude Code's ~/.claude.json"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

CONFIG_DIR  = Path.home() / ".pskill"
CONFIG_FILE = CONFIG_DIR / "config.json"
ENG_DIR     = CONFIG_DIR / "engagements"
HIST_FILE   = CONFIG_DIR / "history"

DEFAULTS: dict[str, Any] = {
    "api_provider": "",       # openai | anthropic | gemini | ollama
    "api_key":      "",
    "model":        "",
    "theme":        "dark",   # dark | light
    "auto_approve": False,    # auto-approve shell commands (like claude --dangerously-skip-permissions)
    "max_tokens":   4096,
    "scope_required": True,   # enforce AUTHORIZATION.md before running tools
}

PROVIDER_DEFAULTS = {
    "openai":    {"model": "gpt-4o",                   "base_url": "https://api.openai.com/v1"},
    "anthropic": {"model": "claude-sonnet-4-5",        "base_url": "https://api.anthropic.com"},
    "gemini":    {"model": "gemini-2.0-flash-exp",     "base_url": "https://generativelanguage.googleapis.com"},
    "ollama":    {"model": "llama3.1",                 "base_url": "http://localhost:11434/v1"},
    "groq":      {"model": "llama-3.1-70b-versatile", "base_url": "https://api.groq.com/openai/v1"},
}


def ensure_dirs() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    ENG_DIR.mkdir(parents=True, exist_ok=True)


def load() -> dict[str, Any]:
    ensure_dirs()
    if not CONFIG_FILE.exists():
        return dict(DEFAULTS)
    try:
        data = json.loads(CONFIG_FILE.read_text())
        return {**DEFAULTS, **data}
    except Exception:
        return dict(DEFAULTS)


def save(cfg: dict[str, Any]) -> None:
    ensure_dirs()
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2) + "\n")


def get(key: str, fallback: Any = None) -> Any:
    cfg = load()
    # env vars override config (like ANTHROPIC_API_KEY, OPENAI_API_KEY)
    env_map = {
        "api_key": {
            "openai":    "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini":    "GEMINI_API_KEY",
            "groq":      "GROQ_API_KEY",
        }
    }
    if key == "api_key":
        provider = cfg.get("api_provider", "")
        env_key = env_map["api_key"].get(provider, "")
        env_val = os.environ.get(env_key, "")
        if env_val:
            return env_val
    return cfg.get(key, fallback)


def set_value(key: str, value: Any) -> None:
    cfg = load()
    cfg[key] = value
    save(cfg)


def is_configured() -> bool:
    cfg = load()
    return bool(cfg.get("api_provider") and (
        cfg.get("api_key") or
        os.environ.get(f"{cfg.get('api_provider','').upper()}_API_KEY", "")
    ))
