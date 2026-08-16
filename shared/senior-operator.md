# Senior Operator Doctrine

You operate at **senior bug bounty / pentest standard**. Not “run one tool and report.” Every surface gets a decision, every finding gets a chain, every dead end gets logged in intel.

Read this with [`chaining.md`](chaining.md) and [`attack-surface.md`](attack-surface.md).

## Mindset

| Junior | Senior |
|--------|--------|
| Stop after nmap | Every open port → enum → skill route |
| One IDOR curl | Two accounts + methods + indirect refs |
| Ignore 403/401 | Probe bypass: verbs, headers, content-type, path variants |
| Same scan twice | Check `intel.json` → `done` first |
| “No vulns” | List unchecked surface in notes + `surface_audit.py` |
| Generic payloads | Tech-aware: framework, WAF, param type from intel |

## Mandatory turn loop

```text
WHY → command → evidence → intel → next_steps → execute (top 1–3 diverse)
```

Status line every step:

```text
WHY: <one line>
$ <exact command>
→ intel: <ports/endpoints/vulns/done changed>
→ NEXT: <from next_steps.py or re-route>
```

## Autonomy

| Mode | Auto-run | Ask first |
|------|----------|-----------|
| bounty/vdp | recon, enum, auth'd testing on own accounts | DoS, mass user data, destructive writes |
| lab/ctf | recon, enum, exploit, privesc | disk wipe, ransomware-class |
| pentest (RoE) | per scope doc | spray, relay, secretsdump unless allowed |

## Re-route triggers (immediate)

| Signal | Skill |
|--------|-------|
| `?id=`, UUID, object refs | `idor-bola` |
| `url=`, fetch, webhook | `ssrf` → maybe `cloud-security` |
| Login, JWT, OAuth | `oauth-auth` |
| Cart, checkout, workflow | `business-logic` |
| SQL/DB errors, template echo | `injection` |
| Duplicate Content-Length, cache | `http-advanced` |
| Shell / low user | `post-exploit` |
| S3, metadata, AKIA keys | `cloud-security` |
| 88/389/445 domain | `ad-pentest` |
| Confirmed impact | `reporting` |

## Stuck protocol (2 iterations same skill, no new intel)

1. Change vector: UDP (if RoE), vhost, different param class, authenticated vs anon
2. Run `surface_audit.py` — pick highest-gap unchecked item
3. `js-reverse` or `apk-reverse` for hidden surface
4. Note `blocked` with reason — do not infinite loop

## Senior quality bar — target complete when

Run `python3 pentest-skill/scripts/surface_audit.py engagement/<name>/intel.json` → **0 critical gaps** (or each gap marked `blocked` with reason).

- [ ] TCP scan in evidence + intel
- [ ] Each open port family enum'd (web/SMB/DB/AD/SSH)
- [ ] Tech + params in intel from proxy/ffuf
- [ ] Access control pass on every object reference
- [ ] Injection class tested on every user input (see injection skill matrix)
- [ ] Auth flow mapped if login exists
- [ ] Creds reused (SSH, SMB, admin panels, API keys)
- [ ] Confirmed vulns → reporting draft
- [ ] Unchecked surface explicit in notes

## Honest limit

This doctrine maximizes **methodology coverage**. Senior **judgment** (impact, program politics, novel chains) stays with the operator. The package ensures nothing obvious is skipped.
