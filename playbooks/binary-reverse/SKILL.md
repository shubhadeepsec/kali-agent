# Binary Reverse Engineering

**Prerequisite:** Binary or CTF target is authorized in [`../../AUTHORIZATION.md`](../../AUTHORIZATION.md) — own crackmes, CTF instances, or explicit program scope.

## Methodology

1. **Triage** — file type, arch, stripped, packed, protections.
2. **Static analysis** — strings, imports, xrefs, decompile hot functions.
3. **Dynamic analysis** — when behavior depends on input, anti-debug, or network.
4. **Exploit/dev** — CTF flag or vuln PoC per engagement rules.
5. **Document** — repro steps for [`../reporting/SKILL.md`](../reporting/SKILL.md) if bounty-relevant.

## Triage

```bash
file ./challenge
sha256sum ./challenge
strings -n 8 ./challenge | head -40
strings -n 8 ./challenge | grep -iE 'flag|password|correct|wrong|usage'
readelf -h ./challenge 2>/dev/null
checksec --file=./challenge 2>/dev/null   # if pwntools/checksec installed
```

## radare2 — static workflow

```bash
r2 -A ./challenge          # analyze
# r2 commands:
# aaa          — full analyze
# afl          — list functions
# pdf @ main   — disassemble main
# iz           — strings in data section
# / flag       — search string
# s sym.main; pdf
# VV           — visual graph mode
```

Quick one-liner:

```bash
r2 -q -c 'aaa; afl; pdf @ sym.main' ./challenge
```

## Ghidra

1. Import binary → analyze with default options.
2. Find `main` / entry → decompiler window.
3. Rename variables, follow xrefs to `strcmp`, `memcmp`, crypto imports.
4. Export decompilation snippets for notes.

Headless (if configured):

```bash
analyzeHeadless /tmp/ghidra_proj Proj -import ./challenge -postScript ExportDecompile.java
```

## When to use dynamic analysis

| Signal | Approach |
|--------|----------|
| Packed/obfuscated | Run once, dump memory, or unpack stub first |
| Anti-debug (`ptrace`, `/proc/self/status`) | `ltrace`, `strace`, gdb with care |
| Input-dependent branches | fuzz stdin, use gdb break on `read` |
| Network binary | only connect to **in-scope** host |

```bash
ltrace ./challenge 2>&1 | head -50
strace -f ./challenge 2>&1 | head -50
gdb -batch -ex 'file ./challenge' -ex 'disassemble main'
```

## CTF / pwn quick patterns

```bash
# Buffer overflow check (CTF lab)
python3 -c "print('A'*200)" | ./challenge

# ropper / ROP (if installed)
ropper --file ./challenge --search "pop rdi"
```

Use pwntools only in environments where it is installed and target is authorized.

## Bug bounty native scope (rare)

- Desktop clients, game anti-cheat, thick installers — **confirm** binary is in scope.
- Focus: hardcoded secrets, unsafe update channels, weak license checks — not malware development.

## Exploit development (CTF / authorized)

```bash
# Offset find
python3 -c "from pwn import *; print(cyclic_find(0x61616161))"  # after crash in gdb
gdb -q ./challenge -ex 'run < <(python3 -c "print(\"A\"*200)")' -ex 'info registers' -ex quit

# ROP
ropper --file ./challenge --search "pop rdi"
ropper --file ./challenge --search "execve"

# Remote (in-scope host only)
python3 exploit.py REMOTE HOST=ctf.example.com PORT=9999
```

## Intel hooks

```bash
python3 ../../scripts/intel.py $ENG/intel.json mark-done binary_triage
python3 ../../scripts/intel.py $ENG/intel.json mark-done binary_exploit
python3 ../../scripts/intel.py $ENG/intel.json add-vuln --severity high "Stack overflow PoC on ./challenge"
```

## Output checklist

- [ ] Architecture, protections, stripped Y/N
- [ ] Key functions and logic summary
- [ ] Input that reaches vulnerable/compare logic
- [ ] Flag or PoC with exact command/script
- [ ] If remote service: only document in-scope URLs/IPs
