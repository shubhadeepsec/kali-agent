<div align="center">

<img src="assets/logo.png" alt="Pentest-Skill Logo" width="220" />

# Pentest-Skill

### **Autonomous Senior-Grade Methodology Router & Continuous Engagement Framework for AI Coding Agents**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Skills: 17 Modules](https://img.shields.io/badge/Playbooks-17%20Specialized%20Skills-red.svg?style=for-the-badge)](#the-17-skill-playbooks)
[![Agent: Neutral](https://img.shields.io/badge/Agent-Agnostic%20(Claude%20%7C%20Cursor%20%7C%20AGY)-purple.svg?style=for-the-badge)](AGENTS.md)
[![Scope: Gated](https://img.shields.io/badge/Scope-Strictly%20Gated-success.svg?style=for-the-badge)](pentest-skill/AUTHORIZATION.example.md)

<br/>

[Key Features](#key-features) • [System Architecture](#system-architecture--workflow) • [Quick Start](#quick-start) • [The 17 Skill Playbooks](#the-17-skill-playbooks) • [The Senior ACT Loop](#the-senior-act-loop-methodology) • [CLI Scripts](#cli-scripts-reference) • [Tool Index](#supported-tools--environment) • [Verification](#testing--verification)

</div>

---

## 📖 Executive Summary & Overview

Standard Large Language Model (LLM) coding agents frequently fail at real-world penetration testing and bug bounty engagements. When prompted to test a web target or investigate a system, generalist agents often execute a single superficial `curl` or generic `nmap` scan, encounter a standard HTTP `403 Forbidden` response, and terminate their effort with incomplete conclusions.

**Pentest-Skill** solves this fundamental limitation. It is a zero-global-footprint, repository-local methodology controller that enforces senior offensive security discipline onto AI agents (including Google Antigravity, Claude Code, Cursor, Windsurf, Codex, and terminal LLM runtimes).

### Why Pentest-Skill?

- 🛡️ **Mandatory Scope Gate**: Hard authorization boundaries prevent agents from sending unauthorized packets or scanning out-of-scope targets.
- 🎯 **17 Battle-Tested Playbooks**: Deep, technical instructions and verified command sequences covering Web, API, Mobile, Reverse Engineering, Cloud, Active Directory, AI/LLM Security, and Post-Exploitation.
- 🧠 **Persistent Stateful Memory (`intel.json`)**: Eliminates agent amnesia by tracking hosts, open ports, discovered endpoints, parameter matrices, tech stacks, and confirmed vulnerabilities.
- 🔄 **The Senior ACT Loop**: Automatically chains evidence capture, intelligence ingestion, and heuristic-ranked next steps after every single tool execution.
- 🚦 **Coverage & Surface Auditor (`surface_audit.py`)**: Prevents premature completion by auditing attack surface coverage and highlighting overlooked vulnerability classes.

---

## 🌟 Key Features

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PENTEST-SKILL CORE                               │
├──────────────────┬──────────────────┬──────────────────┬────────────────────┤
│  Scope Gatekeeper│ Intelligent Router│ Stateful Intel   │ Coverage Auditor   │
│  Hard boundary   │ 17 domain skills │ Continuous JSON  │ Zero critical gaps │
│  authorization   │ mapped by signal │ memory across    │ verified prior to  │
│  validation      │ & tech indicators│ execution loops  │ final reporting    │
└──────────────────┴──────────────────┴──────────────────┴────────────────────┘
```

1. **Unified `pskill` CLI Dispatcher**: Single master CLI to orchestrate scope, engagement lifecycle, tooling ingestion, chaining, and reporting.
2. **Agent-Neutral Architecture**: Zero vendor lock-in. Reads cleanly through `AGENTS.md`, `CLAUDE.md`, `README_AI.md`, or direct prompt bootstrapping (`pentest-skill/SKILL.md`).
3. **Heuristic Next-Step Ranking Engine**: Evaluates gathered target intelligence to recommend mathematically prioritized, diversified technical actions.
4. **Automated Report Generator**: One command compiles executive markdown reports with CVSS severity distributions, PoC logs, and remediation roadmaps.
5. **Multi-Tool Ingestion Pipelines**: Built-in parsers for `Nmap`, `ffuf`, `httpx`, `Nuclei`, and `Swagger/OpenAPI` JSON/YAML specifications.
6. **Formal Evidence Logging**: Chronological markdown ledger maintaining command execution records, timestamps, tool results, and notes for audit compliance.

---

## 🏗 System Architecture & Workflow

Pentest-Skill orchestrates the entire penetration testing lifecycle through a structured pipeline:

```mermaid
flowchart TD
    A[Start Engagement] --> B{Check AUTHORIZATION.md}
    B -- Missing / Incomplete --> C[STOP: Request User Scope]
    B -- Authorized & In-Scope --> D[Initialize Engagement: engagement_init.py]
    
    D --> E[Identify Target Signal]
    E --> F[Route to Skill via routing.md]
    
    subgraph Senior_ACT_Loop [The Senior ACT Loop]
        G[Execute Tool / Command] --> H[Log Row: append_evidence.py]
        H --> I[Update State: intel.py / Ingestion Parsers]
        I --> J[Rank Next Actions: next_steps.py]
        J --> K[Select Highest Priority Diversified Step]
        K --> G
    end
    
    F --> G
    J --> L[Run Surface Audit: surface_audit.py]
    
    L -- Gaps Remaining --> G
    L -- 0 Critical Gaps --> M[Generate Report: report_gen.py]
    M --> N[Engagement Complete]
```

---

## 🚀 Quick Start

### 1. Clone or Add to Your Project

Clone Pentest-Skill into your target workspace:

```bash
# Clone the repository
git clone https://github.com/shubhadeepsec/Pentest-Skill.git my-engagement
cd my-engagement
```

### 2. Configure Scope & Legal Authorization

Quickly configure authorization in one command using the `scope.py` CLI helper (or `pskill scope`):

```bash
# Option A: Quick setup for local labs / Docker / localhost
python3 pentest-skill/scripts/scope.py quick-lab --target "127.0.0.1"

# Option B: Quick setup for CTF challenges
python3 pentest-skill/scripts/scope.py quick-ctf --target "10.10.10.50" --name "HTB-Machine"

# Option C: Quick setup for authorized Bug Bounty program
python3 pentest-skill/scripts/scope.py quick-bounty \
  --target "app.example.com" \
  --name "Acme Corp Bounty" \
  --source "https://hackerone.com/acme"

# Option D: View current active scope
python3 pentest-skill/scripts/scope.py show
```

> [!IMPORTANT]
> The `pentest-skill/AUTHORIZATION.md` file is gitignored by default to prevent accidental leakage of confidential customer or bounty scopes into version control.

### 3. Initialize Target Engagement

Generate the engagement folder, stateful database, and evidence ledger:

```bash
python3 pentest-skill/scripts/engagement_init.py \
  --target "app.example.com" \
  --mode bounty \
  --skill web-recon
```

This creates the directory `pentest-skill/engagement/app.example.com/` containing:
- `intel.json` — Target state machine
- `evidence.md` — Chronological evidence log
- `evidence/` — Directory for raw tool outputs (`.nmap`, `.json`, `.txt`)

### 4. Direct Your AI Agent

Prompt your agent with simple, direct instructions:

```text
Follow pentest-skill/SKILL.md. Scope is defined in AUTHORIZATION.md.
Engagement is initialized for app.example.com.
Execute the web-recon methodology, ingest findings into intel.json, and chain next_steps.py.
```

---

## 📚 The 17 Skill Playbooks

Pentest-Skill organizes offensive security methodology into 17 specialized playbooks located in `pentest-skill/skills/`.

| Category | Skill | Core Focus & Methodology | Primary Tools |
| :--- | :--- | :--- | :--- |
| **Reconnaissance** | [`web-recon`](pentest-skill/skills/web-recon/SKILL.md) | Subdomain discovery, open port scanning, service versioning, directory fuzzing, tech fingerprinting | `nmap`, `ffuf`, `subfinder`, `httpx`, `whatweb` |
| **API Security** | [`api-testing`](pentest-skill/skills/api-testing/SKILL.md) | REST/GraphQL audits, OpenAPI/Swagger ingestion, mass assignment, hidden parameter fuzzing | `curl`, `jq`, `ffuf`, `Burp Suite` |
| **Authorization** | [`idor-bola`](pentest-skill/skills/idor-bola/SKILL.md) | Horizontal/vertical privilege escalation, BFLA, parameter swap across GET/PUT/DELETE | `Burp Repeater`, `curl`, custom PoCs |
| **Injection** | [`injection`](pentest-skill/skills/injection/SKILL.md) | SQLi (Union, Error, Blind, Time), SSTI, Command Injection, XXE, Deserialization | `sqlmap`, `curl`, `Burp Intruder` |
| **Web Infrastructure** | [`http-advanced`](pentest-skill/skills/http-advanced/SKILL.md) | HTTP Request Smuggling (CL.TE / TE.CL), Cache Poisoning, Host header injection, 403 bypasses | `curl`, `Burp Repeater`, custom python |
| **Network Pivoting** | [`ssrf`](pentest-skill/skills/ssrf/SKILL.md) | Server-Side Request Forgery, cloud metadata interrogation (AWS/GCP/Azure), internal service probing | `curl`, `interactsh`, `Burp Collaborator` |
| **Authentication** | [`oauth-auth`](pentest-skill/skills/oauth-auth/SKILL.md) | OAuth2/OIDC flaw analysis, CSRF on login, JWT secret brute-forcing, algorithm confusion | `jwt_tool`, `Burp Suite`, `curl` |
| **Logic & Workflows** | [`business-logic`](pentest-skill/skills/business-logic/SKILL.md) | Multi-step transaction bypasses, coupon stacking, race conditions, price manipulation | `Turbo Intruder`, `curl`, `Burp Suite` |
| **Frontend Reverse** | [`js-reverse`](pentest-skill/skills/js-reverse/SKILL.md) | Webpack bundle deobfuscation, sourcemap extraction, API key discovery, hidden endpoint mining | `sourcemapper`, `grep`, `nodejs` |
| **Android Static** | [`apk-reverse`](pentest-skill/skills/apk-reverse/SKILL.md) | APK decompilation, AndroidManifest component audit, hardcoded cryptographic secrets | `jadx`, `apktool`, `apkid` |
| **Mobile Runtime** | [`mobile-advanced`](pentest-skill/skills/mobile-advanced/SKILL.md) | Dynamic hooking, SSL pinning bypass, root detection evasion, biometric bypass | `frida`, `objection`, `adb` |
| **Binary Exploitation** | [`binary-reverse`](pentest-skill/skills/binary-reverse/SKILL.md) | ELF/PE analysis, Ghidra decompilation, buffer overflow triage, ROP gadgets, checksec | `ghidra`, `radare2`, `gdb-pwndbg`, `checksec` |
| **Cloud Security** | [`cloud-security`](pentest-skill/skills/cloud-security/SKILL.md) | AWS S3 bucket permissions, Azure Blob audits, GCP IAM role privilege escalation | `awscli`, `scoutsuite`, `trufflehog` |
| **Active Directory** | [`ad-pentest`](pentest-skill/skills/ad-pentest/SKILL.md) | Internal domain recon, Kerberoasting, AS-REP roasting, BloodHound attack path graph | `impacket`, `bloodhound-python`, `crackmapexec` |
| **Post-Exploitation** | [`post-exploit`](pentest-skill/skills/post-exploit/SKILL.md) | Linux/Windows privilege escalation checks, credential harvesting, persistence, cleanup | `linpeas`, `winpeas`, native CLI |
| **AI & LLM Security** | [`ai-llm-security`](pentest-skill/skills/ai-llm-security/SKILL.md) | OWASP LLM Top 10, direct/indirect prompt injection, tool calling SSRF, markdown XSS | `curl`, `jq`, custom agent probes |
| **Deliverables** | [`reporting`](pentest-skill/skills/reporting/SKILL.md) | Executive summaries, technical reproduction steps, CVSS scoring, remediation guidance | Markdown, JSON templates |

---

## 🔄 The Senior ACT Loop Methodology

The hallmark of a senior penetration tester is methodical progression: **Never run a tool without capturing output, never capture output without updating intelligence, and never pick a next step at random.**

```bash
ENG=pentest-skill/engagement/app.example.com
```

### 1. Execute & Save Raw Evidence
Run the chosen security assessment tool, redirecting or outputting findings into the target's `evidence/` directory:

```bash
nmap -sV -sC -T4 --open -oA $ENG/evidence/nmap_quick app.example.com
```

### 2. Append Evidence Entry
Log the exact command and concise outcome in `evidence.md`:

```bash
python3 pentest-skill/scripts/append_evidence.py $ENG/evidence.md \
  --skill web-recon \
  --command "nmap -sV -sC -T4 --open app.example.com" \
  --result "80/http, 443/https (nginx 1.18.0)" \
  --notes "Standard web ports open. Next: Web tech stack & directory fuzzing."
```

### 3. Ingest Findings & Update State
Update `intel.json` with open ports, endpoints, technologies, or parameters discovered:

```bash
# Ingest Nmap output directly
python3 pentest-skill/scripts/intel.py $ENG/intel.json ingest-nmap $ENG/evidence/nmap_quick.nmap

# Mark the specific recon task as completed
python3 pentest-skill/scripts/intel.py $ENG/intel.json mark-done nmap_quick

# Add newly identified endpoints and parameters
python3 pentest-skill/scripts/intel.py $ENG/intel.json add-endpoint "https://app.example.com/api/v2"
python3 pentest-skill/scripts/intel.py $ENG/intel.json add-param "GET /api/v2/items?search="
python3 pentest-skill/scripts/intel.py $ENG/intel.json add-tech "nginx 1.18.0"
```

### 4. Multi-Tool Ingestion Automation
Automatically parse scan outputs from your favorite tools:

```bash
# Ingest ffuf directory fuzzing output
python3 pentest-skill/scripts/ingest_ffuf.py $ENG/intel.json $ENG/evidence/ffuf_dirs.json --base-url https://app.example.com

# Ingest httpx web probe & technology identification
python3 pentest-skill/scripts/ingest_httpx.py $ENG/intel.json $ENG/evidence/httpx.json

# Ingest Nuclei vulnerability scanner findings
python3 pentest-skill/scripts/ingest_nuclei.py $ENG/intel.json $ENG/evidence/nuclei.json

# Ingest Swagger / OpenAPI specification endpoints & parameters
python3 pentest-skill/scripts/ingest_swagger.py $ENG/intel.json $ENG/evidence/openapi.json
```

### 5. Calculate Ranked Next Steps & Audit
Query the heuristics engine to determine the highest-impact subsequent actions:

```bash
python3 pentest-skill/scripts/next_steps.py $ENG/intel.json -n 5
python3 pentest-skill/scripts/surface_audit.py $ENG/intel.json
```

### 6. Generate Complete Security Assessment Report
Compile an executive-ready Markdown report with CVSS severity distributions, asset tables, and finding writeups:

```bash
python3 pentest-skill/scripts/report_gen.py $ENG -o $ENG/report.md
```

---

## 🛠 CLI Scripts Reference

| Script | Purpose | Key Arguments / Example |
| :--- | :--- | :--- |
| `pskill` | Unified master CLI dispatcher | `pskill <command> [options]` |
| `scope.py` | Configures & manages `AUTHORIZATION.md` in one command | `quick-lab`, `quick-ctf`, `quick-bounty`, `set`, `show` |
| `engagement_init.py` | Initializes new target engagement directory & JSON state | `--target <host> [--mode bounty\|vdp\|lab\|ctf] [--skill <skill>]` |
| `intel.py` | Query & manipulate target state in `intel.json` | `intel.json <subcommand> [args]` |
| `append_evidence.py` | Appends structured row to `evidence.md` | `--skill <skill> --command "<cmd>" --result "<summary>"` |
| `report_gen.py` | Compiles Markdown security assessment report | `<engagement_dir_or_intel> [-o <report_file>]` |
| `ingest_httpx.py` | Parses httpx JSON probe data into `intel.json` | `<intel_json> <httpx_file>` |
| `ingest_nuclei.py` | Ingests Nuclei vulnerability findings into `intel.json` | `<intel_json> <nuclei_file>` |
| `ingest_swagger.py` | Parses OpenAPI / Swagger spec into endpoints & params | `<intel_json> <swagger_file> [--base-url <url>]` |
| `ingest_ffuf.py` | Parses ffuf JSON output into `intel.json` endpoints | `<intel_json> <ffuf_json> [--base-url <url>]` |
| `next_steps.py` | Heuristically scores and displays prioritized next actions | `<intel_json> [-n LIMIT] [--no-diversify] [--json]` |
| `surface_audit.py` | Audits coverage gaps prior to completion gate | `<intel_json> [--json]` |
| `test_chaining.py` | Smoke test suite verifying end-to-end chaining | `python3 pentest-skill/scripts/test_chaining.py` |

### `intel.py` Subcommands

```bash
# Mark action completed or blocked
python3 pentest-skill/scripts/intel.py $ENG/intel.json mark-done <action_id>
python3 pentest-skill/scripts/intel.py $ENG/intel.json mark-blocked <action_id> --reason "<reason>"

# Record findings and notes
python3 pentest-skill/scripts/intel.py $ENG/intel.json add-vuln --severity high "BOLA on GET /api/v2/orders/{id}"
python3 pentest-skill/scripts/intel.py $ENG/intel.json note "WAF blocks 'UNION SELECT' - try inline comments"

# Update attack surface components
python3 pentest-skill/scripts/intel.py $ENG/intel.json add-host "admin.example.com"
python3 pentest-skill/scripts/intel.py $ENG/intel.json add-endpoint "https://app.example.com/auth/callback"
python3 pentest-skill/scripts/intel.py $ENG/intel.json add-param "POST /api/export format="
python3 pentest-skill/scripts/intel.py $ENG/intel.json add-tech "GraphQL (Apollo)"
python3 pentest-skill/scripts/intel.py $ENG/intel.json set-waf "Cloudflare"
python3 pentest-skill/scripts/intel.py $ENG/intel.json set-skill "idor-bola"
```

---

## 🤖 Agentic Tool & MCP Server Integration

Beyond prompt rules and CLI scripts, **Pentest-Skill** operates natively as an **Agentic Tool Server** using the standard **Model Context Protocol (MCP)** and Python SDK. This allows autonomous AI agents to invoke pentest methodology tools directly via structured function calling.

### 1. Model Context Protocol (MCP) Server

Connect Pentest-Skill to any MCP client (**Antigravity IDE**, **Claude Desktop**, **Cursor**, **Windsurf**):

```json
{
  "mcpServers": {
    "pentest-skill": {
      "command": "python3",
      "args": ["/path/to/pentest-skill/mcp/server.py"]
    }
  }
}
```

#### Available Agent Tool Functions:

| Tool Function | Description | Parameters |
| :--- | :--- | :--- |
| `pskill_check_scope` | Validates target authorization against `AUTHORIZATION.md` | `target: str` |
| `pskill_set_scope` | Automatically configures scope records | `target, name, source, in_scope, mode` |
| `pskill_init_engagement` | Creates target directory & state machine | `target, mode, primary_skill` |
| `pskill_get_next_steps` | Returns prioritized next technical actions | `target, limit` |
| `pskill_update_intel` | Updates intelligence (ports, tech, vulns) | `target, command, value, severity` |
| `pskill_audit_surface` | Audits coverage checklist for critical gaps | `target` |
| `pskill_log_evidence` | Appends record to `evidence.md` ledger | `target, skill, command_run, result` |
| `pskill_ingest` | Parses outputs from Nmap, ffuf, httpx, Nuclei, Swagger | `target, tool_type, file_path` |
| `pskill_generate_report` | Compiles Markdown security report | `target` |
| `pskill_get_playbook` | Returns complete methodology markdown | `skill_name` |

### 2. Python Agent SDK

Integrate Pentest-Skill directly into your custom Python agents, LangChain, or OpenAI Function Calling pipelines:

```python
from pentest_skill.agent import PentestSkillAgent

# Initialize Agent interface
agent = PentestSkillAgent(default_target="app.example.com")

# Check Scope
scope = agent.check_scope()
if not scope["authorized"]:
    agent.set_scope(target="app.example.com", name="Acme Bounty", source="https://hackerone.com/acme")

# Initialize engagement
agent.init_engagement(mode="bounty", primary_skill="web-recon")

# Query heuristic next steps
next_actions = agent.get_next_steps(limit=3)
print(next_actions)

# Ingest tool output & update state
agent.ingest(tool_type="httpx", file_path="evidence/httpx.json")
agent.update_intel(command="add-vuln", value="IDOR on /invoices", severity="high")

# Run coverage audit & compile report
audit = agent.audit_surface()
report_text = agent.generate_report()
```

---

## 🧰 Supported Tools & Environment

Pentest-Skill integrates with standard security tooling available out of the box in **Kali Linux**, **Parrot OS**, or standard Linux/macOS security distributions.

```bash
# Verify environment readiness
for cmd in nmap curl python3 ffuf jadx apktool frida r2; do
  command -v "$cmd" >/dev/null && echo "✅ OK: $cmd" || echo "❌ MISSING: $cmd"
done
```

| Tool | Category | Primary Function | Installation Check |
| :--- | :--- | :--- | :--- |
| **Nmap** | Port Scanner | Port discovery & banner grabbing | `nmap --version` |
| **Burp Suite** | HTTP Proxy | Interception, Repeater, Intruder | Check proxy on `127.0.0.1:8080` |
| **curl / jq** | CLI HTTP & JSON | Scripted API queries & JSON parsing | `curl --version && jq --version` |
| **ffuf** | Web Fuzzer | Directory & parameter brute-forcing | `ffuf -V` |
| **subfinder / amass** | OSINT | Passive subdomain enumeration | `subfinder -version` |
| **jadx / apktool** | Mobile Reverse | APK decompilation & resource decoding | `jadx --version && apktool -version` |
| **Frida** | Dynamic Hooking | Mobile runtime instrumentation & pinning bypass | `frida --version` |
| **Radare2 / Ghidra** | Binary Analysis | Decompilation, disassembly, ELF/PE triage | `r2 -v` |
| **Impacket / CrackMapExec** | AD / Windows | Active Directory protocol inspection | `crackmapexec --version` |

---

## 📁 Repository Layout

```text
.
├── AGENTS.md                          # Universal Agent entry point (Cursor, Antigravity, Windsurf)
├── CLAUDE.md                          # Native instructions for Claude Code
├── README.md                          # Comprehensive project documentation & architecture guide
├── README_AI.md                       # Condensed machine-readable agent checklist
├── CONTRIBUTING.md                    # Guidelines for contributing new skills & scripts
├── LICENSE                            # MIT License
├── assets/
│   └── logo.png                       # Official Pentest-Skill emblem & logo
└── pentest-skill/
    ├── SKILL.md                       # Senior operator controller entry point
    ├── AUTHORIZATION.example.md       # Scope template (must be filled before scanning)
    ├── routing.md                     # Keyword and indicator to skill routing matrix
    ├── tool-index.md                  # Supported tool directory and sanity checkers
    ├── shared/                        # Universal operational doctrine
    │   ├── senior-operator.md         # Mindset, validation rules, quality gates
    │   ├── attack-surface.md          # Surface mapping & parameter taxonomy
    │   └── chaining.md                # Tool chaining & ACT loop execution rules
    ├── scripts/                       # Automation, state management, and ranking engine
    │   ├── engagement_init.py         # Engagement folder & intel generator
    │   ├── intel.py                   # State machine interface (CLI)
    │   ├── next_steps.py              # Heuristic prioritized next-step engine
    │   ├── surface_audit.py           # Pre-completion coverage audit validator
    │   ├── ingest_ffuf.py             # Ffuf JSON parser
    │   ├── append_evidence.py         # Structured evidence ledger appender
    │   └── test_chaining.py           # Unit & smoke test suite
    ├── skills/                        # 16 Specialized skill playbooks
    │   ├── web-recon/                 # Port scan, directory fuzzing, subdomain discovery
    │   ├── idor-bola/                 # Broken Object Level Authorization & IDOR testing
    │   ├── api-testing/               # REST/GraphQL endpoints & mass assignment
    │   ├── injection/                 # SQLi, SSTI, Command Injection, XXE
    │   ├── http-advanced/             # Request smuggling, cache poisoning, 403 bypass
    │   ├── ssrf/                      # Internal probing & cloud metadata extraction
    │   ├── oauth-auth/                # OAuth2/OIDC flows, JWT tampering
    │   ├── business-logic/            # Transaction bypasses, race conditions
    │   ├── js-reverse/                # JavaScript bundle mining & sourcemap analysis
    │   ├── apk-reverse/               # Android static reverse engineering
    │   ├── mobile-advanced/           # Frida instrumentation & SSL pinning bypass
    │   ├── binary-reverse/            # ELF/PE disasm, Ghidra analysis, ROP
    │   ├── cloud-security/            # S3/Azure/GCP misconfigurations & IAM
    │   ├── ad-pentest/                # Active Directory & Kerberos exploitation
    │   ├── post-exploit/              # Privilege escalation & persistence checks
    │   └── reporting/                 # Executive summaries & CVSS v3.1 reports
    ├── engagement/                    # Target data directory (gitignored)
    └── field-journal/                 # Reusable engagement notes & templates
```

---

## 🧪 Testing & Verification

Run the built-in smoke test suite to verify engagement bootstrapping, JSON state parsing, and recommendation chaining:

```bash
python3 pentest-skill/scripts/test_chaining.py
```

Expected output:
```text
OK chaining smoke test passed
```

You can also run bytecode compilation across all internal tools:

```bash
python3 -m py_compile pentest-skill/scripts/*.py
```

---

## ⚖️ Legal, Ethics & Responsible Disclosure

> [!CAUTION]
> **Strictly for Authorized Testing Only**
> 
> Pentest-Skill is engineered exclusively for authorized bug bounty programs, formal penetration testing engagements under contract, Vulnerability Disclosure Programs (VDPs), Capture The Flag (CTF) challenges, and self-hosted security research labs.
> 
> Unauthorized scanning, probing, or exploitation of computer systems without explicit written permission is illegal and strictly prohibited.

1. **Verify Authorization**: Never execute commands against targets not explicitly documented in `pentest-skill/AUTHORIZATION.md`.
2. **Respect Program Rules**: Abide by rate limits, excluded targets, and safe-harbor clauses.
3. **No Disruptive Testing**: Avoid denial-of-service attacks, destructive payloads, or data destruction.
4. **Responsible Disclosure**: Report vulnerabilities promptly and securely to the target organization following coordinated vulnerability disclosure policies.

---

## 🤝 Contributing

Contributions of new playbooks, tool ingestion parsers, and methodology improvements are welcome! Please review [CONTRIBUTING.md](CONTRIBUTING.md) before submitting pull requests.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
