# JavaScript Reverse Engineering (Frontend)

**Prerequisite:** Target web app origin is in [`../../AUTHORIZATION.md`](../../AUTHORIZATION.md).

## Methodology

1. **Collect bundles** — main app JS, chunks, service worker, webpack runtime.
2. **Map surface** — routes, API base URLs, WebSocket endpoints, feature flags.
3. **Deobfuscate if needed** — beautify, unpack strings, trace webpack modules.
4. **Sourcemaps** — fetch `.map` files if exposed (common misconfig).
5. **Validate in Burp** — hidden endpoints may still require auth; test under RoE.
6. **Handoff** — API paths → `api-testing` / `idor-bola`.

## Download bundles

```bash
# From page source or DevTools Network tab
curl -sk "https://app.example.com/static/js/main.abc123.js" -o main.js

# Guess common paths
for p in static/js/main.js assets/index.js _next/static/chunks/main.js build/static/js/main.*.js; do
  curl -sk -o /dev/null -w "%{http_code} $p\n" "https://app.example.com/$p"
done
```

## Beautify & search

```bash
# js-beautify if installed: js-beautify main.js > main.pretty.js
# Or use an online beautifier locally in editor

grep -oE 'https?://[^"'\'' ]+' main.js | sort -u
grep -oE '/api/[a-zA-Z0-9_./-]+' main.js | sort -u
grep -iE 'password|secret|api[_-]?key|token|authorization|admin|graphql' main.js
```

## Sourcemaps

```bash
# Check JS footer for sourceMappingURL
tail -5 main.js

curl -sk "https://app.example.com/static/js/main.abc123.js.map" -o main.js.map
python3 -c "import json; m=json.load(open('main.js.map')); print('\n'.join(m.get('sources',[])[:30]))"
```

If maps exist, recover original file names and often clear route/API strings.

## Browser DevTools workflow

1. **Sources** — pretty-print `{ }`, set breakpoints on `fetch` / `axios` / `XMLHttpRequest`.
2. **Network** — filter JS; disable cache; reload.
3. **Search (Ctrl+Shift+F)** — project-wide: `"/api/`, `Bearer`, `graphql`, `ws://`.
4. **Overrides** (optional) — local patch for debugging; do not deploy malicious JS to production users.

Console hook (manual inspection only):

```javascript
// Paste in DevTools console on in-scope origin
(function () {
  const orig = window.fetch;
  window.fetch = function (...args) {
    console.log('fetch', args[0], args[1]);
    return orig.apply(this, args);
  };
})();
```

## Webpack / chunk patterns

- Look for `webpackJsonp`, `__webpack_require__`, lazy `import()` chunk IDs.
- Dynamic chunks: `static/js/1234.chunk.js` — download adjacent numbered chunks.

```bash
grep -oE '[a-f0-9]{8,}\.chunk\.js' main.js | sort -u
```

## Deobfuscation basics

- String array rotators: search for large string arrays + decoder function; use browser debugger to log decoder output at callsites.
- Control-flow flattening: beautify first, rename `var _0x` identifiers in editor, focus on `fetch`/`axios` call sites.

## Common finds

| Pattern | Next step |
|---------|-----------|
| Hardcoded API key in JS | Verify key scope; report if production secret |
| `/internal/admin` path | Repeater with your session |
| GraphQL operation names | POST to `/graphql` with introspection off — copy operation from bundle |
| Client-side-only auth check | Bypass by calling API directly |

## Output checklist

- [ ] List of API/base URLs extracted from JS
- [ ] Hidden or undocumented routes
- [ ] Sourcemap exposure (if any)
- [ ] Secrets flagged (with evidence, no exfil beyond PoC)
