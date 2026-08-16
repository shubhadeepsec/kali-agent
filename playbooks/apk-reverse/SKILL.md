# Android APK Reverse Engineering

**Prerequisite:** App package name or APK is in scope in [`../../AUTHORIZATION.md`](../../AUTHORIZATION.md). Use **your own installs**, emulator, or program-provided builds — not pirated or third-party repacks.

## Methodology

1. **Obtain APK** — pull from device, download from program, or use supplied build.
2. **Static pass** — manifest, permissions, exported components, hardcoded secrets.
3. **Decompile** — jadx (Java) + apktool (smali/resources).
4. **Network** — API base URLs, cert pinning config, deep links.
5. **Dynamic (if needed)** — Frida hooks on authorized device/emulator.
6. **Handoff** — backend hosts → `web-recon` / `api-testing` / `idor-bola`.

## Verify tools

See [`../../tool-index.md`](../../tool-index.md): `jadx`, `apktool`, `frida`, `adb`.

## Extract / pull APK

```bash
# List packages
adb shell pm list packages | grep -i example

# Pull installed APK path
adb shell pm path com.example.app
# output: package:/data/app/~~xxx/com.example.app-yyy/base.apk
adb pull /data/app/~~xxx/com.example.app-yyy/base.apk app.apk
```

## apktool — resources & smali

```bash
apktool d app.apk -o app_apktool
cat app_apktool/AndroidManifest.xml
grep -r "android:exported=\"true\"" app_apktool/AndroidManifest.xml
grep -riE "api\.|http|password|secret|apikey|token" app_apktool/res/ app_apktool/smali/ | head -50
```

## jadx — Java source

```bash
jadx -d app_jadx app.apk
grep -riE "http[s]?://|api\.|Bearer|password|secret|api[_-]?key" app_jadx/sources/ | head -50
grep -r "certificatePinner\|TrustManager\|ssl" app_jadx/sources/ | head -20
```

## Manifest review checklist

- [ ] `android:exported="true"` activities/services/receivers
- [ ] Deep links (`intent-filter` with `VIEW` + `http`)
- [ ] `usesCleartextTraffic`, `networkSecurityConfig`
- [ ] Backup allowed (`allowBackup="true"`)
- [ ] Debuggable flag (`android:debuggable="true"`)

## Hardcoded secrets

Search patterns:

```bash
grep -riE "(AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|sk_live_|api[_-]?key\s*[=:])" app_jadx/
```

Validate keys minimally (scope-permitted) — e.g. check if AWS key returns `InvalidClientTokenId` vs valid, without accessing unrelated resources.

## Frida — basic hooking (authorized testing)

```javascript
// frida -U -f com.example.app -l hook.js --no-pause
Java.perform(function () {
  var URL = Java.use('java.net.URL');
  URL.openConnection.implementation = function () {
    console.log('URL: ' + this.toString());
    return this.openConnection();
  };
});
```

```bash
frida -U -f com.example.app -l hook.js
# SSL pinning bypass scripts exist — use only on in-scope app you are allowed to test
```

## Common next steps

| Finding | Action |
|---------|--------|
| API base URL | Confirm host in AUTHORIZATION.md → curl/Burp |
| Exported content provider | `adb shell content query --uri ...` (careful, read-only) |
| Hardcoded JWT/API key | Test least-privilege impact |
| Pinning only in Java | Frida or patch APK for **local** analysis only |

## Output checklist

- [ ] Package version + hash of APK analyzed
- [ ] Exported components list
- [ ] Network endpoints & secrets (with file/line refs)
- [ ] Dynamic notes if Frida was used
