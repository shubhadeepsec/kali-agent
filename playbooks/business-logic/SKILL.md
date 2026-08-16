# Business Logic

**Prerequisite:** Application workflows on in-scope assets in [`../../AUTHORIZATION.md`](../../AUTHORIZATION.md). Use **two test accounts**; do not manipulate real users' orders.

## Decision tree

```text
Multi-step workflow?
├─ Cart/checkout → price qty coupon race double-spend
├─ Registration/invite → reuse token, skip email verify
├─ Role/workflow → approve own request, skip manager step
├─ Rate/limit → coupon brute, reward farming
└─ File/upload flow → type confusion after logic gate
```

## Methodology

1. **Map workflow** — draw states (cart → pay → confirm → ship).
2. **Two accounts** — A and B; note IDs at each step.
3. **Skip steps** — call step N API without N-1.
4. **Replay** — reuse payment/confirm token.
5. **Tamper** — negative qty, zero price, currency swap, client-side total.
6. **Race** — parallel redeem/transfer (only if RoE allows).

## Examples (Burp Repeater)

```http
POST /api/checkout HTTP/1.1
{"cartId":"abc","total":0.01,"coupon":"SAVE50","paid":true}
```

Try: remove coupon after discount applied; change `total` after server quote; `paid:true` without payment callback.

## Invite / verify bypass

```bash
# Step 1: register
# Step 2: skip /verify-email — jump to /api/onboarding/complete
curl -sk -X POST "https://app.example.com/api/onboarding/complete" \
  -H "Authorization: Bearer $TOKEN_NEW_USER"
```

## Approval workflows

- Submit expense as User A → approve as User A (should fail)
- Change `approverId` in JSON to self
- Re-open closed ticket via status regression

## Intel-driven retest

Check `intel.json` endpoints for: `cart`, `checkout`, `order`, `coupon`, `invite`, `approve`, `transfer`.

```bash
python3 ../../scripts/intel.py engagement/TARGET/intel.json note "Workflow: cart→checkout→payment webhook"
python3 ../../scripts/intel.py engagement/TARGET/intel.json mark-done biz_logic
```

## Handoff

- Access control on objects → `idor-bola`
- Payment callback URL → `ssrf`
- Finding ready → `reporting`
