# Contributing

Thanks for improving **pentest-skill**. This project stays **client-neutral** — contributions should work for any LLM agent without vendor lock-in.

## Principles

1. **Authorization first** — never add shortcuts that bypass `AUTHORIZATION.md`.
2. **Practical skills** — methodology + real commands, not filler.
3. **Markdown only** — no required runtime, no auto-install scripts in core skills.
4. **No global config** — do not add steps that modify IDE or agent settings outside this repo.

## Adding a skill

1. Create `pentest-skill/skills/<skill-name>/SKILL.md`.
2. Add a row to [pentest-skill/routing.md](pentest-skill/routing.md).
3. Add a row to the quick reference in [pentest-skill/SKILL.md](pentest-skill/SKILL.md).
4. Update [README.md](README.md) skills table.
5. Add a section stub in [pentest-skill/field-journal/_index.md](pentest-skill/field-journal/_index.md).

## Scripts

| Script | Purpose |
|--------|---------|
| `engagement_init.py` | Create `engagement/<target>/intel.json` |
| `intel.py` | Update intel (nmap ingest, endpoints, done/blocked) |
| `next_steps.py` | Rank next commands from intel |
| `append_evidence.py` | Append evidence table row |
| `test_chaining.py` | Smoke test intel + chaining |

## Pull requests

- One skill or focused change per PR when possible.
- No live targets, credentials, or real program scope in committed files.
- Use placeholders (`example.com`) in examples.

## License

By contributing, you agree your changes are licensed under the project [MIT License](LICENSE).
