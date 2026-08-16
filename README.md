<div align="center">

```
  ██████╗ ███████╗██╗  ██╗██╗██╗     ██╗
  ██╔══██╗██╔════╝██║ ██╔╝██║██║     ██║
  ██████╔╝███████╗█████╔╝ ██║██║     ██║
  ██╔═══╝ ╚════██║██╔═██╗ ██║██║     ██║
  ██║     ███████║██║  ██╗██║███████╗███████╗
  ╚═╝     ╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝
```

**AI-powered pentesting agent. Like Claude Code, but for hacking.**

[![Python](https://img.shields.io/badge/python-3.9+-red.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-red.svg)](LICENSE)

</div>

---

## What is pskill?

`pskill` is an autonomous AI pentesting agent you run in your terminal. You bring your own API key (Anthropic, OpenAI, Gemini, Groq, or Ollama). It reasons about targets, runs tools, tracks findings, and chains the next move — like having a senior red teamer in your shell.

```
pskill
  █ pskill[10.10.10.5] ❯ scan this machine and find web services
```

The agent will:
1. Run `nmap -sV -sC 10.10.10.5`
2. Parse the results, save to `intel.json`
3. Route to the right playbook (web-recon, api-testing, etc.)
4. Suggest and execute next steps
5. Log all evidence automatically

---

## Install

```bash
git clone https://github.com/shubhadeepsec/Pentest-Skill
cd Pentest-Skill
pip install -e .
pskill
```

First run opens a setup wizard — pick your provider and paste your API key. Done.

---

## Supported Providers

| Provider | Models | Key |
|---|---|---|
| **Anthropic** | claude-sonnet-4-5, claude-haiku | `ANTHROPIC_API_KEY` |
| **OpenAI** | gpt-4o, gpt-4o-mini | `OPENAI_API_KEY` |
| **Gemini** | gemini-2.0-flash-exp | `GEMINI_API_KEY` |
| **Groq** | llama-3.1-70b (free, fast) | `GROQ_API_KEY` |
| **Ollama** | llama3.1, mistral (local) | no key needed |

Set via wizard, `/config`, or env var:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
pskill
```

---

## Usage

```bash
pskill              # interactive REPL (recommended)
pskill "scan 10.10.10.5 and find web vulns"   # one-shot
```

### Slash Commands

| Command | Description |
|---|---|
| `/scope lab` | Set scope for local/lab target |
| `/scope ctf <ip>` | Set scope for CTF/HackTheBox target |
| `/scope bounty <domain> <program>` | Set scope for bug bounty |
| `/init` | Initialize new engagement |
| `/intel [target]` | Show target intelligence dashboard |
| `/playbook <skill>` | Load methodology into agent context |
| `/engagements` | List all saved engagements |
| `/report` | Generate Markdown pentest report |
| `/run <cmd>` | Run a shell command directly |
| `/config` | View/edit settings |
| `/config setup` | Re-run setup wizard |
| `/clear` | Clear conversation |
| `/compact` | Summarize + compress conversation |
| `/target <host>` | Switch active target |

### Natural Language

Just type what you want:
```
pskill[10.10.10.5] ❯ run a full port scan
pskill[10.10.10.5] ❯ find all API endpoints and test for IDOR
pskill[10.10.10.5] ❯ what's the highest severity vuln so far?
pskill[10.10.10.5] ❯ generate a bug bounty report
pskill[10.10.10.5] ❯ test the login page for SQL injection
```

---

## Config

Config lives at `~/.pskill/config.json`. Engagements at `~/.pskill/engagements/<target>/`.

```json
{
  "api_provider": "anthropic",
  "api_key": "sk-ant-...",
  "model": "claude-sonnet-4-5",
  "auto_approve": false,
  "max_tokens": 4096,
  "scope_required": true
}
```

`auto_approve: true` skips shell command confirmation (like `claude --dangerously-skip-permissions`).

---

## Playbooks (17 Skills)

The agent auto-selects the right playbook based on target signals. You can also load one manually with `/playbook <skill>`:

`web-recon` `api-testing` `idor-bola` `injection` `http-advanced` `ssrf` `oauth-auth` `business-logic` `js-reverse` `apk-reverse` `mobile-advanced` `binary-reverse` `cloud-security` `ad-pentest` `post-exploit` `ai-llm-security` `reporting`

---

## Ethics

**Authorized targets only.** pskill enforces scope before running tools. Use it for:
- ✅ Bug bounty programs (HackerOne, Bugcrowd, Intigriti)
- ✅ CTF / HackTheBox / TryHackMe
- ✅ Your own infrastructure
- ✅ Authorized client engagements
- ❌ Never on targets without written permission

---

## License

MIT
