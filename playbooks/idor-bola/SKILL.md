# IDOR / BOLA / Broken Access Control

**Prerequisite:** Target and test accounts are in [`../../AUTHORIZATION.md`](../../AUTHORIZATION.md). Only access **your own** or **program-provided** test objects unless the program explicitly allows cross-user testing.

## Methodology

1. **Map object references** — IDs in URLs, JSON bodies, headers, cookies, WebSocket messages.
2. **Classify reference type** — sequential int, UUID, opaque token, composite key (`userId` + `orderId`).
3. **Test horizontal** — same role, different user: can User A read/update User B's object?
4. **Test vertical** — lower role accessing admin objects or actions.
5. **Test HTTP methods** — GET read, PUT/PATCH update, DELETE destroy; method tunneling (`X-HTTP-Method-Override`).
6. **Test indirect references** — export, share links, report IDs, file download tokens.
7. **Document** with request/response pairs; route to [`../reporting/SKILL.md`](../reporting/SKILL.md) when confirmed.

## Decision tree

```text
Object reference found?
├─ Sequential int → range swap + Intruder (small range)
├─ UUID → collect from two accounts, swap only
├─ Composite (userId+orderId) → vary each independently
├─ GraphQL node(id) → api-testing + idor pass
└─ Confirmed → intel add-vuln → reporting
```

## Intel hooks

```bash
ENG=engagement/app.example.com
python3 ../../scripts/intel.py $ENG/intel.json add-vuln --severity high "IDOR on GET /api/v1/invoices/{id}"
python3 ../../scripts/intel.py $ENG/intel.json mark-done idor_pass
python3 ../../scripts/next_steps.py $ENG/intel.json
```

## Identify object references

Look for parameter names:

```
id, user_id, uid, accountId, orderId, invoice_id, file_id, docId,
uuid, guid, ref, token, key, profile_id, message_id, ticket_id
```

In Burp: **Proxy history → filter by param** or search response bodies for `"id":`.

## Systematic ID-swapping

### Manual (Repeater)

1. Capture request as **User A** (session/cookie or JWT for A).
2. Note object ID for A's resource.
3. Replace ID with **User B's** object ID (from B's session or enum).
4. Compare status, body length, and content.

```http
GET /api/v1/orders/12345 HTTP/1.1
Host: app.example.com
Authorization: Bearer <USER_A_TOKEN>
```

→ change `12345` to `12346`, keep User A's token.

### curl quick check

```bash
# User A token accessing B's resource ID
curl -s "https://app.example.com/api/users/999/profile" \
  -H "Authorization: Bearer $TOKEN_USER_A" | jq .

curl -s "https://app.example.com/api/users/1000/profile" \
  -H "Authorization: Bearer $TOKEN_USER_A" | jq .
```

## Burp Intruder (authorized targets only)

1. Send request to **Intruder**.
2. Mark only the **object ID** position (Sniper).
3. Payload: list of IDs (sequential range or collected UUIDs).
4. Filter responses: different length, 200 vs 403, unique JSON keys.

**Grep - Match:** `"email"`, `"ssn"`, `"password"` — flag leaks.

For UUIDs, use Intruder with **custom iterator** or collected IDs from sitemap — avoid massive blind UUID spray unless RoE allows.

## BOLA on APIs

| Test | Example |
|------|---------|
| Missing auth | Remove `Authorization` header |
| Wrong user context | User A token + User B `userId` in path/body |
| Mass assignment | PATCH profile with `"role":"admin"` |
| Nested objects | `GET /api/orgs/1/members/2` — swap org or member ID |
| GraphQL | Change `node(id: "...")` or variable `$id` |

## Vertical escalation signals

- `/admin/*`, `/internal/*`, `?role=admin`, `isAdmin:true`
- Response fields you shouldn't see: `permissions`, `billing`, `allUsers`

## False positive checks

- Same 200 but generic empty object
- ID belongs to shared/public resource
- CDN cache returning stale content — add cache-buster query param

## Evidence to capture

- Two account labels (A/B) and which ID belongs to whom
- Full HTTP request/response for unauthorized access
- Impact statement (PII fields exposed, write access, etc.)
