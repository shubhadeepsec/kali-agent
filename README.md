<div align="center">

```
  ██╗  ██╗ █████╗ ██╗     ██╗     █████╗  ██████╗ ███████╗███╗   ██╗████████╗
  ██║ ██╔╝██╔══██╗██║     ██║    ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝
  █████╔╝ ███████║██║     ██║    ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   
  ██╔═██╗ ██╔══██║██║     ██║    ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   
  ██║  ██╗██║  ██║███████╗██║    ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   
  ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝    ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   
```

**Autonomous AI OS Controller & Security Agent for Kali Linux. Like Claude Code, but for hacking and system administration.**

[![Python](https://img.shields.io/badge/python-3.9+-red.svg)](https://python.org)
[![Kali Linux](https://img.shields.io/badge/OS-Kali%20Linux-blue.svg)](https://www.kali.org)
[![License](https://img.shields.io/badge/license-MIT-red.svg)](LICENSE)

</div>

---

## What is Kali Agent?

**Kali Agent** is an autonomous terminal agent built for **Kali Linux**. Bring your own API key (Anthropic, OpenAI, Gemini, Groq, or local Ollama). It gives AI models full terminal and OS-level control to:
- 🖥️ **Control the whole Kali Linux OS**: Execute bash commands, manage systemd services, inspect network interfaces and listening sockets, monitor processes, and search the filesystem.
- 🧰 **Orchestrate any security tool**: Native command chaining for Nmap, Metasploit (`msfconsole`), Burp Suite, Wireshark / `tshark`, Gobuster, ffuf, SQLMap, Hydra, Hashcat, John the Ripper, Ghidra, Impacket, and custom scripts.
- 📦 **Auto-install missing dependencies**: Automatically checks for tools and installs them on the fly via `apt`, `pip`, `go install`, `cargo`, or `git clone`.
- 🧠 **Maintain persistent engagement state**: Automatically updates target `intel.json` with discovered hosts, ports, endpoints, technologies, and vulnerabilities.
- 🛡️ **17 Senior security playbooks**: Deep domain methodologies loaded directly into agent memory (web-recon, api-testing, idor-bola, injection, oauth-auth, ai-llm-security, etc.).

```
kali-agent
  █ kali-agent[10.10.10.5] ❯ scan this target, enumerate web directories, and check for SQL injection
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
kali-agent
```

*(You can launch it via `kali-agent` or `pskill`)*

First run opens an interactive setup wizard — pick your provider and paste your API key. Done.

---

## Supported Providers

| Provider | Models | Key |
|---|---|---|
| **Anthropic** | claude-sonnet-4-5, claude-haiku | `ANTHROPIC_API_KEY` |
| **OpenAI** | gpt-4o, gpt-4o-mini | `OPENAI_API_KEY` |
| **Gemini** | gemini-2.0-flash-exp | `GEMINI_API_KEY` / `GOOGLE_API_KEY` |
| **Groq** | llama-3.1-70b (free, fast) | `GROQ_API_KEY` |
| **Ollama** | llama3.1, mistral (local) | no key needed |

Set via wizard, `/config`, or env var:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
kali-agent
```

---

## Usage

```bash
kali-agent              # interactive REPL (recommended)
kali-agent "scan 10.10.10.5 and find web vulns"   # one-shot
```

### Slash Commands

| Command | Description |
|---|---|
| `/scope lab` | Set scope for local/lab target |
| `/scope ctf <ip>` | Set scope for CTF/HackTheBox target |
| `/scope bounty <domain> <program>` | Set scope for bug bounty |
| `/init` | Initialize new engagement & state machine |
| `/intel [target]` | Show target intelligence dashboard |
| `/playbook <skill>` | Load methodology into agent context |
| `/engagements` | List all saved engagements |
| `/report` | Generate Markdown pentest report |
| `/run <cmd>` | Run a shell command directly |
| `/config` | View/edit settings |
| `/config setup` | Re-run setup wizard |
| `/clear` | Clear conversation history |
| `/compact` | Summarize + compress conversation |
| `/target <host>` | Switch active target |

### Natural Language OS Control

Just type what you want to do:
```
kali-agent ❯ check listening ports and active network interfaces
kali-agent ❯ start postgresql service and verify msfconsole connectivity
kali-agent ❯ install subfinder via go install
kali-agent[10.10.10.5] ❯ scan for open ports and identify services
kali-agent[10.10.10.5] ❯ find all API endpoints and test for IDOR
kali-agent[10.10.10.5] ❯ generate a bug bounty report
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

## Ethics & Authorization

**Authorized targets only.** Kali Agent enforces scope before running target-facing tools. Use it for:
- ✅ Bug bounty programs (HackerOne, Bugcrowd, Intigriti)
- ✅ CTF / HackTheBox / TryHackMe / Lab sandboxes
- ✅ Your own infrastructure & systems
- ✅ Authorized penetration testing engagements
- ❌ Never against unauthorized third-party targets

---

## License

MIT
