# Mobile Advanced (Frida, SSL Pinning, Runtime)

**Prerequisite:** In-scope app in [`../../AUTHORIZATION.md`](../../AUTHORIZATION.md). Static pass first: [`../apk-reverse/SKILL.md`](../apk-reverse/SKILL.md).

## Decision tree

```text
Static done?
├─ Pinning blocks proxy → Frida ssl bypass (local device/emulator only)
├─ Root detection → Frida hide / patched APK local install
├─ Hidden API calls → hook okhttp/NSURLSession/fetch
├─ Local storage → SharedPreferences, Keychain dumps
└─ Backend hosts → api-testing / idor-bola on in-scope URLs
```

## Frida SSL pinning bypass (authorized)

```javascript
// ssl_bypass.js — use only on in-scope app
Java.perform(function () {
  var TrustManager = Java.registerClass({
    name: 'com.custom.TrustAll',
    implements: [Java.use('javax.net.ssl.X509TrustManager')],
    methods: {
      checkClientTrusted: function () {},
      checkServerTrusted: function () {},
      getAcceptedIssuers: function () { return []; },
    },
  });
});
```

```bash
frida -U -f com.example.app -l ssl_bypass.js
# Proxy device to Burp after bypass
```

## Hook API URLs

```javascript
Java.perform(function () {
  var OkHttpClient = Java.use('okhttp3.OkHttpClient');
  var RealCall = Java.use('okhttp3.RealCall');
  RealCall.execute.implementation = function () {
    var req = this.request();
    console.log('[OKHTTP]', req.url().toString());
    return this.execute();
  };
});
```

## Runtime secrets

```bash
adb shell run-as com.example.app cat shared_prefs/*.xml 2>/dev/null
grep -ri "token\|secret\|password" evidence/frida_log.txt
```

## Intel hooks

```bash
python3 ../../scripts/intel.py $ENG/intel.json mark-done apk_static
python3 ../../scripts/intel.py $ENG/intel.json mark-done mobile_runtime
python3 ../../scripts/intel.py $ENG/intel.json add-endpoint "https://api.example.com/v2"
```

## Handoff

- Endpoints → `api-testing`, `idor-bola`
- Hardcoded AWS keys → `cloud-security`
