# glibc-all-in-one

**The pwner's glibc Swiss Army knife.** Smart argument detection — no flags to memorize. Download, search, identify, diff, compile. Full glibc lifecycle for exploit development.

> Legacy shell scripts moved to [`legacy/`](legacy/README.md) and are no longer maintained. `glibc-aio` is a ground-up v2 rewrite.

[中文](README.md)

## Install

```bash
git clone https://github.com/matrix1001/glibc-all-in-one.git
cd glibc-all-in-one
pip install -e .
```

Python 3.10+. Installs `pyelftools` (ELF parsing) and `zstandard` (.deb zstd decompression) automatically. No other dependencies.

First run — pull the package list (~5 seconds, generates the `list` file):

```bash
$ glibc-aio mirror update
[+] Saved 32 + 48 old packages to "list"
```

## Quick Start

Three commands cover the most common pwn workflow:

```bash
# 1. Leaked address → identify the libc
$ glibc-aio puts 0x80970 system 0x4f440
[Online (libc.rip)]
  libc6_2.27-3ubuntu1.5_amd64          ← exact match

# 2. Download + look up symbols
$ glibc-aio download 2.27-3ubuntu1_amd64
[+] Downloaded to libs/2.27-3ubuntu1_amd64

$ glibc-aio 2.27 system                ← version prefix + symbol name, searches local downloads
2.27-3ubuntu1_amd64:
  000000000004f440  STT_FUNC  system

# 3. Identify an unknown libc
$ glibc-aio ./unknown-libc.so
Method:    buildid
Version:   2.27-3ubuntu1.5_amd64
BuildID:   4176c5eec6b8c6e04aa1eae2cd4b76b1
```

## Command Reference

### Subcommands (explicit control)

| Command | Description |
|------|------|
| `glibc-aio mirror list` | Show 4 mirrors with type (regular / fallback) |
| `glibc-aio mirror update` | Scrape all mirrors, write unified `list` file |
| `glibc-aio search 2.35` | Fuzzy search by package name |
| `glibc-aio search --symbol system=0x4f440` | Reverse-lookup libc version by symbol offset (libc.rip) |
| `glibc-aio search --symbol a=0x1 --symbol b=0x2` | Multi-symbol AND query |
| `glibc-aio search --symbol ... --tol 5` | Offset tolerance ±N bytes |
| `glibc-aio search --buildid abc123` | Search by BuildID |
| `glibc-aio search --libc ./libc.so --symbol system` | Look up symbol in a specific libc file |
| `glibc-aio search --libc ./libc.so --symbol "*exec*"` | Glob match symbol names |
| `glibc-aio search --libc ./libc.so --ends-with f30` | Filter symbols by address suffix (partial overwrite) |
| `glibc-aio search --libc ./libc.so --str "/bin/sh"` | Search strings in .rodata/.data, returns offset |
| `glibc-aio download 2.27-3ubuntu1_amd64` | Download libc + debug symbols |
| `glibc-aio download <id> --mirror tuna` | Pin a specific mirror |
| `glibc-aio download <id> --no-dbg` | Skip debug symbols |
| `glibc-aio download <id> --keep-deb` | Keep .deb file after extraction |
| `glibc-aio identify ./libc.so` | BuildID (online) → fingerprint (local), dual-path identification |
| `glibc-aio identify --offline ./libc.so` | Local fingerprint only, no network |
| `glibc-aio diff libc-a.so libc-b.so` | Compare two libcs: added/removed/changed symbols, security diff |
| `glibc-aio build 2.29 amd64` | Docker container build (version→image auto-mapping) |
| `glibc-aio build 2.27 i686` | 32-bit cross-compile |
| `glibc-aio build ... --image ubuntu:16.04` | Override Docker image |
| `glibc-aio build ... --no-docker` | Build natively on host |

All subcommands support `--json` output.

### Smart Dispatch (no subcommand)

When no subcommand is given, `glibc-aio` auto-detects argument types:

| Input | Auto Behavior | Example Output |
|------|---------|----------|
| `glibc-aio 2.35` | Search available packages | `2.35-0ubuntu3.13_amd64  2.35-0ubuntu3_amd64 ...` |
| `glibc-aio 2.27 system` | Search symbol across local libcs matching version | `2.27-3ubuntu1_amd64:  000000000004f440  system` |
| `glibc-aio 2.35 "*mmap*"` | Glob search across local libcs | Offsets for mmap in all 2.35 downloads |
| `glibc-aio system 0x4f440` | Online reverse-lookup | `[Online] libc6_2.27-3ubuntu1.5_amd64` |
| `glibc-aio puts 0x80970 system 0x4f440` | Multi-symbol AND | Libc matching both offsets |
| `glibc-aio ./libc.so` | Identify | `Method: buildid  Version: 2.27-3ubuntu1.5_amd64` |
| `glibc-aio ./libc.so system` | Look up symbol offset | `000000000004f440  STT_FUNC  system` |
| `glibc-aio ./libc.so "*exec*"` | Glob symbol search | 14 matches (execl, execv, execve...) |
| `glibc-aio ./libc.so 0xf30` | Ends-with filter (3 hex digits = 12-bit mask) | 7 symbols matching `f30` |
| `glibc-aio ./libc.so 0x80` | Ends-with filter (2 hex digits = 1 byte) | Symbols with low byte `80` |
| `glibc-aio ./libc.so system 0x380` | Symbol + ends-with combo | Glob then filter by suffix |

**Detection rules:** existing file paths → libc files; `0x` prefix or ≥5 bare hex digits → addresses; `digit.digit` → version numbers; everything else → symbol names. In file context, bare hex accepts any length (`0x80`, `f30`).

## Detailed Usage

### `search` — Find Versions / Search libc

```bash
# Online — fuzzy name search
$ glibc-aio search 2.35
2.35-0ubuntu3.13_amd64
2.35-0ubuntu3_amd64
[*] 4 result(s)

# Online — reverse-lookup by symbol offset
$ glibc-aio search --symbol system=0x4f440
[Online (libc.rip)]
  libc6_2.27-3ubuntu1.5_amd64
  libc6_2.27-0ubuntu2_amd64
  ...

# Online — multi-symbol AND with tolerance
$ glibc-aio search --symbol puts=0x80970 --symbol system=0x4f440 --tol 5
[Online (libc.rip)]
  libc6_2.27-3ubuntu1.5_amd64
[Local symdb]                                   ← local downloads also searched
  libc6_2.27-3ubuntu1_amd64  (2 symbol(s) matched)

# Online — BuildID
$ glibc-aio search --buildid 4176c5eec6b8c6e04aa1eae2cd4b76b1

# Local — symbol lookup
$ glibc-aio search --libc ./libc.so --symbol system
000000000004f440  STT_FUNC  system

# Local — glob
$ glibc-aio search --libc ./libc.so --symbol "*exec*"
00000000000cbfa0  STT_FUNC  execl
00000000000cbde0  STT_FUNC  execv
...
[*] 14 symbol(s)

# Local — address suffix filter (partial overwrite)
$ glibc-aio search --libc ./libc.so --ends-with f30
00000000000abf30  STT_FUNC  wcpncpy
000000000004f430  STT_FUNC  __libc_system
[*] 7 symbol(s)

# Local — symbol + suffix combo
$ glibc-aio search --libc ./libc.so --symbol "*exec*" --ends-with fa0
00000000000cbfa0  STT_FUNC  execl
[*] 1 symbol(s)

# Local — string search (scans .rodata/.data, not whole-file strings)
$ glibc-aio search --libc ./libc.so --str "/bin/sh"
  0x001b3e9a  /bin/sh
[*] 1 match(es)
```

Online mode queries both libc.rip API and the local symbol database. Local results are unaffected when the network is down. The local index is built automatically on every download.

### `download` — Download libc + Debug Symbols

4 mirrors tried in order: tuna → ustc → ubuntu-archive → old-releases (fallback). Stops on first success, transparent to the user.

After download: extracts `.deb` (supports xz / gz / zstd), indexes symbols for offline `search` and `identify`, cleans up temp files.

```bash
$ glibc-aio download 2.27-3ubuntu1_amd64
[+] Downloaded to libs/2.27-3ubuntu1_amd64
$ ls libs/2.27-3ubuntu1_amd64/
x86_64-linux-gnu/  .debug/                            ← libc + debug symbols

# Options
$ glibc-aio download 2.35-0ubuntu3_amd64 --mirror tuna    # Specific mirror only
$ glibc-aio download 2.35-0ubuntu3_amd64 --keep-deb        # Keep .deb file
$ glibc-aio download 2.31-0ubuntu9_i386 --no-dbg            # Skip debug symbols
```

### `identify` — Identify Unknown libc

Dual-path fallback. First extracts the BuildID from `.note.gnu.build-id` and queries libc.rip online. On failure, computes a symbol-table hash fingerprint and matches against a local database. The local database grows automatically with every `download`.

```bash
$ glibc-aio identify ./libc.so
Method:    buildid
Version:   2.27-3ubuntu1.5_amd64
BuildID:   4176c5eec6b8c6e04aa1eae2cd4b76b1

$ glibc-aio identify --offline ./libc.so          # No network, local fingerprint only
Method:    fingerprint
Version:   2.27-3ubuntu1_amd64
```

### `diff` — Compare Two libc Versions

Shows added/removed symbols, offset changes, and security hardening diffs (RELRO/NX/Canary/PIE/RUNPATH).

```bash
$ glibc-aio diff libs/2.27/libc.so libs/2.35/libc.so.6
--- libs/2.27/libc.so
+++ libs/2.35/libc.so.6
+ 000000000012e3f0 STT_FUNC STB_GLOBAL posix_spawn_file_actions_addtcsetpgrp_np
- 0000000000091d40 STT_FUNC STB_GLOBAL __strspn_c1
~ system: 0x4f440 -> 0x50d60                        ← offset changed
~ puts: 0x80970 -> 0x80ed0
! relro: full -> partial                            ← security degraded
```

### `build` — Compile glibc from Source

Default mode: builds inside a Docker container with automatic image selection (2.19→14.04, 2.23-2.27→16.04, 2.28-2.29→18.04, 2.30-2.34→20.04, 2.35+→22.04). Output goes to `libs/build/<version>/<arch>/`. Falls back to host-native build when Docker is unavailable.

```bash
$ glibc-aio build 2.29 amd64                     # Docker ubuntu:18.04 container
$ glibc-aio build 2.27 i686                       # 32-bit cross-compile
$ glibc-aio build 2.35 amd64 --no-docker          # Host-native build
$ glibc-aio build ... --prefix /opt/glibc         # Custom install prefix
```

### `mirror` — Mirror Management

```bash
$ glibc-aio mirror list
  tuna                 https://mirror.tuna.tsinghua.edu.cn/... [regular]
  ustc                 https://mirrors.ustc.edu.cn/...         [regular]
  ubuntu-archive       http://archive.ubuntu.com/...           [regular]
  old-releases         http://old-releases.ubuntu.com/...      [fallback]

$ glibc-aio mirror update
[+] Saved 32 + 48 old packages to "list"           ← unified file, [old] section marker
```

## JSON

All commands support `--json` for scripting:

```bash
$ glibc-aio ./libc.so system --json | jq '.[0].addr'
"0x45380"

$ glibc-aio identify ./libc.so --json | jq -r '.id'
2.27-3ubuntu1_amd64

$ glibc-aio mirror list --json | jq '.[].name'
tuna
ustc
ubuntu-archive
old-releases
```

## Scale

| Item | Value |
|---|-----|
| Python | 3.10+ |
| Dependencies | `pyelftools` + `zstandard` (2) |
| Tests | 28 passed |
| Commands | 6 subcommands + 11 smart dispatch modes |
| Mirrors | 4 (tuna / ustc / ubuntu-archive / old-releases) |
| Online API | libc.rip |
| Local cache | `~/.cache/glibc-aio/` (symbol index + fingerprint DB) |
| .deb formats | xz / gz / zstd auto-detect |

## Legacy

Original shell scripts preserved in [`legacy/`](legacy/README.md) as reference.

```
update_list  → mirror update                unified list file (no more old_list)
download     → download (single entry)       no more download/download_old split
download_old → auto fallback to old-releases
extract      → built-in Python (ar + tarfile + zstd)
build        → Docker containerized build
```
