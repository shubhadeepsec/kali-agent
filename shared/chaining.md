# Chaining — Senior ACT Loop

Read with [`senior-operator.md`](senior-operator.md).

## Every tool run

```bash
ENG=pentest-skill/engagement/<name>

# 1. Save raw output
mkdir -p $ENG/evidence && your-command | tee $ENG/evidence/step.log

# 2. Evidence table
python3 pentest-skill/scripts/append_evidence.py $ENG/evidence.md \
  --skill web-recon --command "nmap -sV TARGET" --result "443/https nginx"

# 3. Update intel
python3 pentest-skill/scripts/intel.py $ENG/intel.json ingest-nmap $ENG/evidence/nmap_quick.nmap
python3 pentest-skill/scripts/intel.py $ENG/intel.json add-endpoint "https://app.example.com/api/v1"
python3 pentest-skill/scripts/intel.py $ENG/intel.json add-param "GET /search?q"
python3 pentest-skill/scripts/intel.py $ENG/intel.json mark-done nmap_quick

# 4. Rank next (diverse skills)
python3 pentest-skill/scripts/next_steps.py $ENG/intel.json

# 5. Execute top 1–3 — different skill families when possible

# 6. Periodically
python3 pentest-skill/scripts/surface_audit.py $ENG/intel.json
```

## ffuf ingest

```bash
python3 pentest-skill/scripts/ingest_ffuf.py $ENG/intel.json $ENG/evidence/ffuf_dirs.json --base-url https://TARGET
```

## Senior-complete

`surface_audit.py` reports **0 critical gaps** → draft report → optional field-journal.

## Never

- Repeat action in `intel.done`
- Stop after one port / one param
- Skip `injection_pass` and `idor_pass` when web/API exists
- Assume authorization
