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
    "api_provider": "",       # openai | anthropic | gemini | groq | ollama
    "api_key":      "",
    "model":        "",
    "theme":        "dark",   # dark | light
    "auto_approve": False,    # auto-approve shell commands
    "max_tokens":   4096,
    "scope_required": True,   # enforce scope confirmation before running active tools
}

PROVIDER_DEFAULTS = {
    "openai":    {"model": "gpt-4o",                   "base_url": "https://api.openai.com/v1"},
    "anthropic": {"model": "claude-sonnet-4-5",        "base_url": "https://api.anthropic.com"},
    "gemini":    {"model": "gemini-2.0-flash-exp",     "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/"},
    "groq":      {"model": "llama-3.1-70b-versatile", "base_url": "https://api.groq.com/openai/v1"},
    "ollama":    {"model": "llama3.1",                 "base_url": "http://localhost:11434/v1"},
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
    provider = cfg.get("api_provider", "")

    # Check environment variable fallbacks
    if key == "api_key":
        env_map = {
            "openai":    ["OPENAI_API_KEY"],
            "anthropic": ["ANTHROPIC_API_KEY"],
            "gemini":    ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
            "groq":      ["GROQ_API_KEY"],
            "ollama":    [],
        }
        for env_var in env_map.get(provider, []):
            val = os.environ.get(env_var, "")
            if val:
                return val
        if provider == "ollama":
            return "ollama"

    if key == "model" and not cfg.get("model"):
        return PROVIDER_DEFAULTS.get(provider, {}).get("model", fallback)

    return cfg.get(key, fallback)


def set_value(key: str, value: Any) -> None:
    cfg = load()
    cfg[key] = value
    save(cfg)


def is_configured() -> bool:
    cfg = load()
    provider = cfg.get("api_provider", "")

    if provider == "ollama":
        return True

    if provider:
        api_key = get("api_key", "")
        if api_key:
            return True

    # Auto-detect from environment if not yet configured
    for p, env_keys in [
        ("anthropic", ["ANTHROPIC_API_KEY"]),
        ("openai",    ["OPENAI_API_KEY"]),
        ("gemini",    ["GEMINI_API_KEY", "GOOGLE_API_KEY"]),
        ("groq",      ["GROQ_API_KEY"]),
    ]:
        for k in env_keys:
            if os.environ.get(k):
                cfg["api_provider"] = p
                cfg["api_key"] = os.environ[k]
                cfg["model"] = PROVIDER_DEFAULTS[p]["model"]
                save(cfg)
                return True

    return False
