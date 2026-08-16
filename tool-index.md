# Tool Index

Verify tools before use. **No auto-install** — if missing, tell the user and suggest their package manager.

| Tool | Purpose | Verify installed |
|------|---------|------------------|
| **Nmap** | Port scan, service/version detection | `nmap --version` |
| **Burp Suite** | Proxy, Repeater, Intruder, API testing | `which burpsuite` or launch from menu; check proxy on `127.0.0.1:8080` |
| **curl** | HTTP requests, header/cookie tests | `curl --version` |
| **Python 3** | Scripts, parsing, quick PoCs | `python3 --version` |
| **Bash** | Shell one-liners, loops | `bash --version` |
| **ffuf** | Directory/parameter fuzzing | `ffuf -V` |
| **subfinder** | Passive subdomain enum | `subfinder -version` |
| **amass** | Subdomain enum / asset discovery | `amass -version` |
| **whatweb** | Tech stack fingerprint | `whatweb --version` |
| **dig / host** | DNS lookups | `dig -v` |
| **jq** | JSON parsing in shell | `jq --version` |
| **jadx** | APK/DEX decompile to Java | `jadx --version` |
| **apktool** | APK decode resources/smali | `apktool --version` |
| **frida** | Dynamic instrumentation (mobile) | `frida --version` |
| **adb** | Android device/emulator interaction | `adb version` |
| **radare2** | Binary disasm/debug | `r2 -v` |
| **Ghidra** | Decompiler (GUI/headless) | `which ghidraRun` or check install path |
| **file / strings / ltrace / strace** | Binary triage & dynamic trace | `file --version` |
| **objdump / readelf** | ELF inspection | `objdump -v` |
| **httpx** | Probe live HTTP hosts | `httpx -version` |
| **crackmapexec** | SMB/AD cred testing (lab) | `crackmapexec --version` |
| **impacket** | GetNPUsers, psexec, etc. | `python3 -c "import impacket; print('ok')"` |
| **bloodhound-python** | AD path collection | `bloodhound-python -h` |
| **aws CLI** | S3/cloud checks (optional) | `aws --version` |

## Kali Linux

Most CLI tools above ship with Kali. Burp Community/Pro and Ghidra are often preinstalled or available via `apt`.

```bash
# Quick sanity check — counts how many core tools respond
for cmd in nmap curl python3 ffuf jadx apktool frida r2; do
  command -v "$cmd" >/dev/null && echo "OK $cmd" || echo "MISSING $cmd"
done
```

## Burp workflow reminder

1. Browser/system proxy → `127.0.0.1:8080`
2. Import CA if testing HTTPS
3. Scope tab: restrict to in-scope hosts from `AUTHORIZATION.md`
