# AGENTS.md

**pentest-skill** — senior-grade methodology router for authorized bug bounty, VDP, CTF, and pentest work.

## Mission

Route → scope gate → skill → **senior ACT loop** (evidence → intel → next_steps → surface_audit) → report.

## Mandatory flow

1. [pentest-skill/SKILL.md](pentest-skill/SKILL.md) + [pentest-skill/shared/senior-operator.md](pentest-skill/shared/senior-operator.md)
2. [pentest-skill/AUTHORIZATION.md](pentest-skill/AUTHORIZATION.md) — filled or **STOP**
3. `python3 pentest-skill/scripts/engagement_init.py --target "HOST" --mode bounty`
4. Route → skill → after **each** tool: [pentest-skill/shared/chaining.md](pentest-skill/shared/chaining.md)
5. Complete: `python3 pentest-skill/scripts/surface_audit.py engagement/.../intel.json`

## 16 skills

web-recon, idor-bola, api-testing, js-reverse, apk-reverse, mobile-advanced, binary-reverse, **injection**, **http-advanced**, ssrf, oauth-auth, business-logic, cloud-security, ad-pentest, post-exploit, reporting

## Scripts

| Script | Purpose |
|--------|---------|
| `engagement_init.py` | New engagement folder |
| `intel.py` | Ports, endpoints, params, done/blocked |
| `next_steps.py` | Senior-ranked diverse next commands |
| `surface_audit.py` | Critical gap audit — senior-complete gate |
| `ingest_ffuf.py` | ffuf JSON → intel endpoints |
| `append_evidence.py` | Evidence log |
| `test_chaining.py` | Smoke test |

## Tests

```bash
python3 pentest-skill/scripts/test_chaining.py
```

Client-neutral: load this file + [README_AI.md](README_AI.md).
