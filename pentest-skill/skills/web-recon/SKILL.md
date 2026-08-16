# Web Recon

**Prerequisite:** Target hostname/IP is listed in [`../../AUTHORIZATION.md`](../../AUTHORIZATION.md).

## Decision tree

```text
Start recon
├─ Subdomain scope allowed? → passive enum → httpx
├─ Host live? → nmap -sV -sC (mark nmap_quick done)
│   ├─ 80/443/8080 → whatweb, ffuf, api paths
│   ├─ 445/389/88 → note in intel → route ad-pentest (if lab/RoE)
│   └─ 3306/5432/6379 → service enum (RoE), never destructive
├─ JS-heavy app? → flag js-reverse in next_steps
├─ s3/azure in DNS/CNAME? → cloud-security
└─ Ingest all → next_steps.py
```

## Methodology

1. **Passive asset discovery** — subdomains, historical URLs (stay within program rules).
2. **DNS** — A/AAAA/CNAME, wildcard behavior.
3. **Port & service scan** — TCP top ports or full scan per RoE; version detection on interesting ports.
4. **Fingerprint** — web stack, CDN, WAF hints.
5. **Content discovery** — dirs, files, vhosts, common API paths.
6. **Intel + chain** — ingest results, run `next_steps.py`, execute top steps across skills.

## Subdomain enumeration

```bash
subfinder -d example.com -silent -o evidence/subs.txt
amass enum -passive -d example.com -o evidence/amass_subs.txt
sort -u evidence/subs.txt evidence/amass_subs.txt -o evidence/all_subs.txt
httpx -l evidence/all_subs.txt -status-code -title -tech-detect -o evidence/live.txt
```

## Nmap

```bash
nmap -sV -sC -T4 --open -oA evidence/nmap_quick TARGET
# Full TCP if RoE allows:
nmap -p- -T4 --open -oA evidence/nmap_all TARGET
nmap -p 80,443,8080,8443 -sV --script http-title,http-headers,ssl-cert -oA evidence/nmap_web TARGET
```

## Directory / endpoint discovery

```bash
ffuf -u https://app.example.com/FUZZ -w /usr/share/seclists/Discovery/Web-Content/common.txt \
  -mc 200,301,302,403 -fc 404 -o evidence/ffuf_dirs.json -of json

for path in api v1 v2 graphql swagger.json openapi.json .well-known/security.txt; do
  curl -sk -o /dev/null -w "%{http_code} $path\n" "https://app.example.com/$path"
done
```

## Intel hooks (after each phase)

```bash
ENG=engagement/app.example.com
python3 ../../scripts/intel.py $ENG/intel.json ingest-nmap evidence/nmap_quick.nmap
python3 ../../scripts/intel.py $ENG/intel.json mark-done nmap_quick
python3 ../../scripts/intel.py $ENG/intel.json add-endpoint "https://app.example.com/api/v1"
python3 ../../scripts/intel.py $ENG/intel.json add-tech "nginx"
python3 ../../scripts/next_steps.py $ENG/intel.json
```

## Output checklist

- [ ] Live hosts + ports in intel.json
- [ ] Stack/WAF in intel `tech`
- [ ] Endpoints list populated
- [ ] `next_steps.py` run — top 3 steps executed or marked blocked

