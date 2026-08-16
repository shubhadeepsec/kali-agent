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

[![Version](https://img.shields.io/badge/version-v0.1.0-red.svg)](https://github.com/shubhadeepsec/Pentest-Skill)
[![Python](https://img.shields.io/badge/python-3.9+-red.svg)](https://python.org)
[![Kali Linux](https://img.shields.io/badge/OS-Kali%20Linux-blue.svg)](https://www.kali.org)
[![License](https://img.shields.io/badge/license-MIT-red.svg)](LICENSE)

</div>

---

## What is Kali Agent v0.1.0?

**Kali Agent** is an autonomous terminal AI assistant built for **Kali Linux**. Bring your own API key (Anthropic, OpenAI, Gemini, Groq, or local Ollama). It gives AI models full terminal and OS-level control to:
- 🖥️ **Control the whole Kali Linux OS**: Execute bash commands, manage systemd services, inspect network interfaces and listening sockets, monitor processes, and search the filesystem.
- 📋 **Autonomous Multi-Step Planner (`/plan`)**: Break high-level assessment goals into an automated execution plan with live status tracking.
- 🔄 **Background Scan & Process Manager (`/jobs`)**: Launch long-running scans in the background, tail logs in real-time, or kill jobs on demand.
- 🧰 **Orchestrate any security tool**: Native command chaining for Nmap, Metasploit (`msfconsole`), Burp Suite, Wireshark / `tshark`, Gobuster, ffuf, SQLMap, Hydra, Hashcat, John the Ripper, Ghidra, Impacket, and custom scripts.
- 🎯 **Exploit-DB & CVE Lookup (`/searchsploit`)**: Query local Kali `searchsploit` database for known vulnerabilities and exploit PoCs.
- 🌐 **Reverse Shell & Listener Helper (`/revshell`)**: Detects active VPN interface (`tun0`/`eth0`) and generates listener commands & payload one-liners.
- 📦 **Auto-install missing dependencies**: Automatically checks for tools and installs them on the fly via `apt`, `pip`, `go install`, `cargo`, or `git clone`.
- 💾 **Session Persistence & Resumption (`/sessions`)**: Save and resume assessment sessions across reboots.
- 📊 **Cyberpunk Dark HTML & Markdown Reports (`/report`)**: Generate executive reports with CVSS severity matrices, asset tables, and verified PoC write-ups.
- 🛡️ **17 Senior security playbooks**: Deep domain methodologies loaded directly into agent memory (web-recon, api-testing, idor-bola, injection, oauth-auth, ai-llm-security, etc.).

```
kali-agent
  █ kali-agent[10.10.10.5] ❯ /plan audit web application on 10.10.10.5
```

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

| Provider | Recommended Model | Environment Variable |
|---|---|---|
| **Anthropic** | claude-sonnet-4-5 | `ANTHROPIC_API_KEY` |
| **OpenAI** | gpt-4o | `OPENAI_API_KEY` |
| **Gemini** | gemini-2.0-flash-exp | `GEMINI_API_KEY` / `GOOGLE_API_KEY` |
| **Groq** | llama-3.1-70b-versatile (free/fast) | `GROQ_API_KEY` |
| **Ollama** | llama3.1 (local, offline) | no key required |

---

## Usage

```bash
kali-agent              # interactive REPL (recommended)
kali-agent "scan 10.10.10.5 and find web vulns"   # one-shot command
```

### Slash Commands

| Command | Description |
|---|---|
| `/plan <goal>` | Draft & execute an autonomous multi-step pentest plan |
| `/scope lab\|ctf\|bounty` | Set or confirm authorization scope |
| `/jobs` | List & monitor active background processes & scans |
| `/attach <id>` | Tail live stdout log for a background job |
| `/kill <id>` | Terminate a background job |
| `/revshell [ip] [port]` | Generate reverse shell one-liners & netcat listeners |
| `/searchsploit <query>` | Search local Exploit-DB and CVE vulnerability database |
| `/sessions` | List and resume previous assessment sessions |
| `/report` | Compile Markdown & Cyberpunk Dark HTML reports |
| `/theme <name>` | Switch terminal theme (`cyberpunk`, `matrix`, `stealth`, `dark`) |
| `/init` | Initialize new engagement & state machine |
| `/intel [target]` | Show target intelligence dashboard |
| `/playbook <skill>` | Load methodology playbook into agent context |
| `/engagements` | List all saved engagements |
| `/run <cmd>` | Execute a shell command directly |
| `/config` | View/edit settings & API keys |
| `/compact` | Summarize + compress conversation history |
| `/clear` | Clear conversation history |
| `/target <host>` | Switch active target context |
| `/help` | Display command guide |
| `/exit` | Exit Kali Agent |

### Natural Language Examples

```
kali-agent ❯ check listening ports and active network interfaces
kali-agent ❯ start postgresql service and verify msfconsole connectivity
kali-agent ❯ searchsploit Apache 2.4.49
kali-agent ❯ generate a bash reverse shell for tun0 on port 9001
kali-agent[10.10.10.5] ❯ scan all ports in the background with nmap
kali-agent[10.10.10.5] ❯ find all API endpoints and test for IDOR
kali-agent[10.10.10.5] ❯ /report
```

---

## Configuration

Config is stored in `~/.pskill/config.json`. Data lives in `~/.pskill/engagements/<target>/`.

```json
{
  "api_provider": "anthropic",
  "api_key": "sk-ant-...",
  "model": "claude-sonnet-4-5",
  "theme": "cyberpunk",
  "auto_approve": false,
  "max_tokens": 4096,
  "scope_required": true,
  "stream_output": true,
  "track_tokens": true
}
```

`auto_approve: true` skips shell command confirmation prompts (like `claude --dangerously-skip-permissions`).

---

## License

MIT
