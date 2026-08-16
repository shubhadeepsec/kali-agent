# Authorization Record

**Do not start work on any target until this file is filled in for that target.**  
If anything below is blank or unclear for the asset you are about to test → **STOP and ask the user.**

Copy this file to `AUTHORIZATION.md` in the same directory and fill it in locally (`AUTHORIZATION.md` is gitignored).

---

## Program / client

| Field | Value |
|-------|-------|
| **Name** | *(e.g. Acme Corp VDP, HackerOne program, HTB machine, own lab app)* |
| **Authorization source** | *(bug bounty program page URL, signed SOW/engagement letter, VDP policy, CTF platform rules, "own asset" with owner confirmation)* |
| **Valid from** | *(YYYY-MM-DD)* |
| **Valid until** | *(YYYY-MM-DD or "ongoing")* |

## In scope

List every asset you are allowed to test. Be specific (hostnames, IP ranges, app IDs, package names).

```
# Examples — replace with real scope
https://app.example.com
*.example.com (if program allows wildcard)
com.example.mobileapp (Android package)
10.10.10.10 (HTB box)
```

## Out of scope

```
# Examples
*.example.net
production payment flows (if prohibited)
social engineering
third-party SaaS not operated by client
```

## Rules of engagement (summary)

- Allowed: *(e.g. automated scanning, Burp, cred stuffing on own test accounts)*
- Not allowed: *(e.g. DoS, physical access, testing other users' data without program approval)*
- Rate limits / disclosure: *(program-specific)*

## Current target (this session)

| Field | Value |
|-------|-------|
| **Target** | *(URL, IP, APK path, binary path — must appear in In scope above)* |
| **Confirmed in-scope?** | *(yes / no — if no, stop)* |
| **Notes** | *(program tier, test account creds location, special headers)* |

---

## Agent checklist

Before running recon, exploits, or reverse engineering:

1. [ ] Program/client name is filled in
2. [ ] Authorization source is documented (link or reference)
3. [ ] Current target appears explicitly in **In scope**
4. [ ] Out-of-scope items reviewed — current work does not violate them
5. [ ] Dates are still valid

If any box is unchecked → ask the user. **Never assume authorization.**
