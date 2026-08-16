# API Testing (REST / GraphQL)

**Prerequisite:** API base URL/host is in [`../../AUTHORIZATION.md`](../../AUTHORIZATION.md).

## Methodology

1. **Discover surface** — OpenAPI/Swagger, GraphQL introspection, mobile app traffic, JS bundles.
2. **Auth model** — API keys, JWT, OAuth, session cookies; note expiry and refresh.
3. **Baseline** — authenticated vs unauthenticated behavior per endpoint.
4. **Test classes** — authZ (see [`../idor-bola/SKILL.md`](../idor-bola/SKILL.md)), authN bypass, mass assignment, injection, rate limits, verbose errors.
5. **GraphQL-specific** — introspection, batching, depth, field auth.
6. **Document** findings via [`../reporting/SKILL.md`](../reporting/SKILL.md).

## Decision tree

```text
API surface mapped?
├─ No spec → proxy traffic, js-reverse, apk-reverse paths
├─ Unauthenticated 200? → auth bypass candidate
├─ JWT/session → oauth-auth skill
├─ Object IDs in responses → idor-bola pass
├─ url/link params → ssrf skill
└─ Each finding → intel add-vuln → next_steps
```

## Intel hooks

```bash
ENG=engagement/app.example.com
python3 ../../scripts/intel.py $ENG/intel.json add-endpoint "https://app.example.com/api/v1/users"
python3 ../../scripts/intel.py $ENG/intel.json mark-done api_surface
python3 ../../scripts/next_steps.py $ENG/intel.json
```

## Discovery

```bash
# Common spec locations
curl -sk "https://app.example.com/swagger.json" | jq .info
curl -sk "https://app.example.com/openapi.json" | head
curl -sk "https://app.example.com/v2/api-docs" | jq .paths | head

# GraphQL introspection (if enabled — may be out of scope on some programs; check RoE)
curl -sk -X POST "https://app.example.com/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ __schema { queryType { name } } }"}'
```

Burp: filter Proxy by `api`, `graphql`, `v1`, `application/json`.

## Auth bypass checks

```bash
# No token
curl -sk "https://app.example.com/api/v1/me"

# Empty / malformed Bearer
curl -sk "https://app.example.com/api/v1/me" -H "Authorization: Bearer"
curl -sk "https://app.example.com/api/v1/me" -H "Authorization: Bearer null"

# Alternate methods
curl -sk -X POST "https://app.example.com/api/v1/admin/users" -H "Content-Type: application/json" -d '{}'
```

JWT (in-scope only):

- Decode at jwt.io locally or `python3 -c "import base64,json,sys; p=sys.argv[1].split('.')[1]; print(json.loads(base64.urlsafe_b64decode(p+'===')))" "$JWT"`
- Test alg none / key confusion **only** if program permits and you have approval for active exploitation techniques.

## Mass assignment

```bash
curl -sk -X PATCH "https://app.example.com/api/v1/profile" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"test","role":"admin","isAdmin":true,"credit_limit":99999}'
```

Compare response and subsequent `GET /me`.

## BFLA on endpoints

Build a matrix in Burp:

| Endpoint | GET (user) | POST | DELETE | Admin token | User token |
|----------|------------|------|--------|-------------|------------|

Automate row diffs with Intruder or copy to Repeater tabs.

## Rate limiting

```bash
# Simple loop — stay within program rules; stop if DoS-like behavior is prohibited
for i in $(seq 1 50); do
  code=$(curl -sk -o /dev/null -w "%{http_code}" "https://app.example.com/api/v1/login" \
    -H "Content-Type: application/json" -d '{"user":"test","pass":"wrong"}')
  echo "$i $code"
done
```

Note: missing 429, CAPTCHA bypass, account lockout behavior.

## GraphQL tests

```bash
# List types (introspection)
curl -sk -X POST "https://app.example.com/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query":"query IntrospectionQuery { __schema { types { name } } }"}'

# Batch query (if supported)
curl -sk -X POST "https://app.example.com/graphql" \
  -H "Content-Type: application/json" \
  -d '[{"query":"{ user(id:1){ email } }"},{"query":"{ user(id:2){ email } }"}]'
```

Field-level BOLA: request another user's fields with your token.

## Burp workflow

1. **Logger / HTTP history** — group by host + path prefix.
2. **Repeater** — mutate JSON body keys, HTTP method, content-type (`application/json` vs `application/x-www-form-urlencoded`).
3. **Intruder** — fuzz param names for hidden fields (`admin`, `debug`, `internal`).
4. **Scanner** (if licensed) — passive first; active only with permission.

## Output checklist

- [ ] Endpoint inventory (method + path + auth required)
- [ ] Unauthenticated access list
- [ ] Mass-assignment / BFLA results
- [ ] Rate limit / error verbosity notes
- [ ] Handoff to `idor-bola` for object-level issues
