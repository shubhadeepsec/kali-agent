# OAuth / Auth / Session Testing

**Prerequisite:** Auth endpoints on in-scope hosts in [`../../AUTHORIZATION.md`](../../AUTHORIZATION.md).

## Decision tree

```text
Login or token flow seen?
├─ OAuth/OIDC → redirect_uri, state, PKCE, code reuse
├─ JWT → alg, kid, exp, role claims, none/confusion (RoE permitting)
├─ Session cookie → fixation, HttpOnly/Secure, scope after logout
└─ SAML → AssertionConsumer URL, signature (if in scope)
```

## Map the flow (Burp)

1. Capture full login → callback → token exchange.
2. Note: `client_id`, `redirect_uri`, `scope`, `state`, `nonce`, `code_challenge`.

```bash
curl -sk "https://app.example.com/.well-known/openid-configuration" | jq .
curl -sk "https://app.example.com/oauth/authorize?response_type=code&client_id=CLIENT&redirect_uri=https://app.example.com/callback&scope=openid"
```

## redirect_uri tests

- Substitute attacker URI (exact match bypass variants: `@`, `\`, `#`, subdomain, path traversal)
- Open redirect on callback → token theft chain

## state / PKCE

- Omit `state` — login CSRF?
- Reuse `code` twice — replay?
- Swap `code_verifier` — PKCE bypass?

## JWT quick checks

```bash
TOKEN="eyJ..."
python3 -c "import base64,json,sys; p=sys.argv[1].split('.')[1]; print(json.dumps(json.loads(base64.urlsafe_b64decode(p+'===')),indent=2))" "$TOKEN"
```

Burp JWT Editor or manual:

- `alg:none` (only if program allows active tampering)
- Weak `secret` brute (hashcat/jwt_tool) on **test** tokens
- Role claim bump: `"role":"user"` → `"admin"`

## Session

```bash
# Before login
curl -sk -c cookies.txt "https://app.example.com/login"
# After login — compare session ID rotation
curl -sk -b cookies.txt "https://app.example.com/api/me"
# After logout — old cookie still valid?
```

## Password / MFA (careful)

- Rate limit on `/login`, `/forgot-password` (see `api-testing`)
- MFA bypass: step skip, `mfaVerified:true` in JSON, backup codes

## Intel hooks

```bash
python3 ../../scripts/intel.py engagement/TARGET/intel.json add-endpoint "https://app.example.com/oauth/authorize"
python3 ../../scripts/intel.py engagement/TARGET/intel.json mark-done oauth_review
```

## Handoff

- Object access after auth → `idor-bola`
- API mass assignment on profile → `api-testing`
- Confirmed issue → `reporting`
