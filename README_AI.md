# README_AI.md — senior operator bootstrap

1. [AGENTS.md](AGENTS.md) + [pentest-skill/shared/senior-operator.md](pentest-skill/shared/senior-operator.md)
2. [pentest-skill/SKILL.md](pentest-skill/SKILL.md)
3. Scope: [pentest-skill/AUTHORIZATION.md](pentest-skill/AUTHORIZATION.md) or **STOP**
4. Init: `python3 pentest-skill/scripts/engagement_init.py --target TARGET --mode bounty`
5. Route: [pentest-skill/routing.md](pentest-skill/routing.md)
6. After **each** tool: [pentest-skill/shared/chaining.md](pentest-skill/shared/chaining.md)
7. Finish: `python3 pentest-skill/scripts/surface_audit.py pentest-skill/engagement/TARGET/intel.json`

## Senior rules

- Run `next_steps.py` — execute top 1–3 **diverse** skills
- Never skip `injection_pass` / `idor_pass` when web/API exists
- Never repeat `done` actions
- Confirmed vuln → intel `add-vuln` → `reporting`

## 16 skills

web-recon, idor-bola, api-testing, js-reverse, apk-reverse, mobile-advanced, binary-reverse, injection, http-advanced, ssrf, oauth-auth, business-logic, cloud-security, ad-pentest, post-exploit, reporting
