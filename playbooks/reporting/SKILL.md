# Vulnerability Reporting

**Prerequisite:** Finding is on a target confirmed in [`../../AUTHORIZATION.md`](../../AUTHORIZATION.md). Do not include out-of-scope assets or unrelated third-party data.

## Report structure (VDP / bug bounty)

Use this order unless the program template says otherwise.

### 1. Title

Short, specific, impact-oriented.

```
IDOR on GET /api/v1/invoices/{id} exposes other users' billing details
```

### 2. Summary (2–4 sentences)

What is broken, who can exploit it, and what they gain — no hype.

### 3. Severity / impact

- **Confidentiality / Integrity / Availability** affected
- Business impact: account takeover, PII exposure, financial fraud, etc.
- Use program severity matrix if provided (CVSS optional).

### 4. Affected asset

```
https://app.example.com/api/v1/invoices/{id}
```

Must match in-scope list.

### 5. Steps to reproduce

Numbered, minimal, copy-paste friendly.

```
1. Log in as User A (test account provided by program).
2. Open Burp and capture: GET /api/v1/invoices/1001
3. Replace invoice ID with 1002 (belongs to User B).
4. Observe HTTP 200 with User B's invoice PDF metadata and address.
```

Include HTTP method, path, required headers/cookies.

### 6. Proof of concept

- Redacted screenshots or sanitized HTTP request/response
- curl/Burp export — **redact** session tokens in public drafts; submit full detail through platform

```http
GET /api/v1/invoices/1002 HTTP/1.1
Host: app.example.com
Authorization: Bearer [REDACTED]
```

```json
{"id":1002,"email":"victim@example.com","total":499.00}
```

### 7. Evidence

- Timestamps (UTC)
- Account IDs used (test accounts only)
- Response codes and distinguishing body fields

### 8. Suggested fix

Concrete and actionable.

```
Authorize every invoice read against the authenticated user's ID server-side;
do not rely on opaque IDs alone. Return 404 for unauthorized IDs.
Use unpredictable UUIDs plus server-side ownership checks.
```

### 9. References (optional)

- OWASP API Top 10: API1 Broken Object Level Authorization
- CWE-639: Authorization Bypass Through User-Controlled Key

## Quality bar

| Good | Avoid |
|------|-------|
| One clear vuln per report | Kitchen-sink submissions |
| Demonstrated impact on real object type | Theoretical "might be IDOR" |
| Program-legal test accounts | Real user data dumps |
| Minimal PoC | Full database exfil |

## After submission

Offer to log lessons in [`../../field-journal/_template.md`](../../field-journal/_template.md).
