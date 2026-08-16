# Claude Code — Project Instructions

This repo is **agent-neutral**. Claude Code reads this file; other clients use [AGENTS.md](AGENTS.md) the same way.

## Entry point

For recon, bug bounty, VDP, CTF, API/IDOR testing, reverse engineering (JS/APK/binary), or reporting:

1. Read **[AGENTS.md](AGENTS.md)** and **[pentest-skill/SKILL.md](pentest-skill/SKILL.md)**.
2. Follow: **AUTHORIZATION.md → routing.md → matched skill SKILL.md**.

Do not run target-facing commands until scope is confirmed in [pentest-skill/AUTHORIZATION.md](pentest-skill/AUTHORIZATION.md) (copy from [AUTHORIZATION.example.md](pentest-skill/AUTHORIZATION.example.md) if needed).

## Constraints

- Authorized targets only — stop and ask if scope is missing or unclear.
- Keep rules and scope files inside this repository only.
