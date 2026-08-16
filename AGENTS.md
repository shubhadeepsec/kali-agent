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

## 17 skills

web-recon, idor-bola, api-testing, js-reverse, apk-reverse, mobile-advanced, binary-reverse, **injection**, **http-advanced**, ssrf, oauth-auth, business-logic, cloud-security, ad-pentest, post-exploit, **ai-llm-security**, reporting

## Scripts & CLI

| Script | Purpose |
|--------|---------|
| `pskill` | Unified master CLI dispatcher |
| `scope.py` | Quick scope setup & management |
| `engagement_init.py` | New engagement folder |
| `intel.py` | Ports, endpoints, params, done/blocked |
| `next_steps.py` | Senior-ranked diverse next commands |
| `surface_audit.py` | Critical gap audit — senior-complete gate |
| `report_gen.py` | Markdown report compiler |
| `ingest_httpx.py` | Ingest live HTTP probe & tech data |
| `ingest_nuclei.py` | Ingest Nuclei vulnerability findings |
| `ingest_swagger.py` | Ingest OpenAPI / Swagger specs |
| `ingest_ffuf.py` | ffuf JSON → intel endpoints |
| `append_evidence.py` | Evidence log |
| `test_chaining.py` | Smoke test |

## Tests

```bash
python3 pentest-skill/scripts/test_chaining.py
```

Client-neutral: load this file + [README_AI.md](README_AI.md).
