# Attack Surface Checklist

Map intel → required actions. `surface_audit.py` implements this list.

## Per-port family

| Port(s) | Required actions (mark in `done`) |
|---------|-----------------------------------|
| 80/443/8080/8443 | `nmap_quick`, `whatweb`, `ffuf_dirs`, `js_bundle`, `api_surface`, `injection_pass`, `oauth_review` (if auth) |
| 445/139 | `smb_enum` (lab/RoE only) |
| 22 | `ssh_banner`, cred reuse if keys/passwords in intel |
| 3306/5432/1433/6379 | `db_enum` — never destructive; version + auth test only if allowed |
| 88/389/636 | `ad_enum` — lab/internal scope only |
| 53 | `dns_zone` if AXFR allowed |

## Per-endpoint class

| Pattern | Skills to run |
|---------|---------------|
| `/api/*`, GraphQL | `api-testing`, `idor-bola`, `injection` |
| `/oauth`, `/login`, JWT | `oauth-auth` |
| `?id=`, `/users/{id}` | `idor-bola` |
| `url=`, import, webhook | `ssrf`, `injection` |
| `/admin`, `/internal` | `idor-bola` vertical + `http-advanced` bypass |
| Upload | `injection` (polyglot), `idor-bola` on file id |
| Multi-step form | `business-logic` |

## Injection matrix (every unique param)

For each param in intel `params[]`:

| Class | Tests |
|-------|-------|
| String reflect | XSS context check, SSTI `{{7*7}}`, SQLi `' OR '1'='1` |
| Numeric | SQLi, IDOR boundary |
| JSON body keys | mass assignment, injection, type confusion |
| XML/SOAP | XXE |
| Filename/path | traversal, LFI |
| URL | SSRF |

## HTTP advanced triggers

- Front-end vs back-end desync possible → `http-advanced` smuggling probe
- Same path different cache headers → cache poisoning
- Host header reflected in links → password reset poisoning

## Completion

```bash
python3 pentest-skill/scripts/surface_audit.py engagement/TARGET/intel.json
```

Critical gap without matching `done` or `blocked` → not senior-complete.
