# Cloud Security

**Prerequisite:** Cloud assets are in [`../../AUTHORIZATION.md`](../../AUTHORIZATION.md). Only test accounts/buckets explicitly in scope.

## Decision tree

```text
S3/Azure/GCP URL or subdomain found?
├─ YES → bucket/blob public? ACL/policy misconfig?
│        └─ creds in JS/APK? → test key scope (minimal)
└─ SSRF param exists? → route also to ssrf/ (metadata 169.254.169.254 only if RoE allows)
```

## S3 bucket checks

```bash
# Known bucket name (in scope)
aws s3 ls s3://bucket-name --no-sign-request 2>&1
curl -sI "https://bucket-name.s3.amazonaws.com/"
curl -sI "https://s3.amazonaws.com/bucket-name/"

# List objects if listing allowed (stop at PoC — don't mass download)
aws s3 ls s3://bucket-name --no-sign-request | head
```

## Azure blob (pattern)

```bash
curl -sI "https://account.blob.core.windows.net/container?restype=container&comp=list"
```

## GCP storage

```bash
curl -sI "https://storage.googleapis.com/bucket-name/"
```

## DNS / asset hints

```bash
dig +short s3.example.com CNAME
# Look for amazonaws.com, cloudfront.net, azurefd.net in intel tech/endpoints
```

## Metadata via SSRF (lab / explicit RoE only)

If app fetches user URLs, test (one controlled callback or metadata — program rules first):

```bash
# In Burp Repeater — url/link parameter
http://169.254.169.254/latest/meta-data/
http://127.0.0.1:80/
```

Full SSRF playbook: [`../ssrf/SKILL.md`](../ssrf/SKILL.md).

## IAM / key exposure

If APK/JS yields `AKIA*` key:

```bash
# Minimal validation — do not pivot outside scope
AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... aws sts get-caller-identity 2>&1
```

Document scope of identity; report over-permissioned keys.

## Intel hooks

```bash
python3 ../../scripts/intel.py engagement/TARGET/intel.json add-tech "aws-s3"
python3 ../../scripts/intel.py engagement/TARGET/intel.json add-endpoint "https://bucket.s3.amazonaws.com/"
python3 ../../scripts/intel.py engagement/TARGET/intel.json mark-done cloud_enum
```

## Handoff

- Fetch param + cloud host → `ssrf`
- Keys → verify impact, then `reporting`
