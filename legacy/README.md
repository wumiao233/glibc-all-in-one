# glibc-all-in-one (Legacy)

These are the original shell scripts from v1. They still work but are no longer maintained.

**The new v2 tool (`glibc-aio`) replaces all of them with a unified CLI.** See the main [README.md](../README.md).

## Scripts

In this directory:

- `update_list` — scrape Ubuntu mirrors for available libc packages
- `build` — compile glibc from source on host

In the [repository root](../):

- `download` — download libc + debug .deb (tuna, falling back to old-releases)
- `download_old` — download from old-releases mirror only
- `extract` — extract .deb files (requires system `ar`, `tar`)

## Paths

Output always lands in the repository root (`libs/`, `debs/`, `srcs/`, `list`),
no matter which directory you run a script from. Set `GLIBC_AIO_ROOT` to point
the data directories somewhere else.

```bash
cd /tmp && ~/glibc-all-in-one/legacy/update_list   # still writes <repo>/list
GLIBC_AIO_ROOT=/data/glibc ~/glibc-all-in-one/download 2.23-0ubuntu3_amd64
```

## Usage (original)

### download

```bash
./legacy/update_list            # refresh package lists
cat list                        # see available versions
./download 2.23-0ubuntu10_i386  # download libc + debug
ls libs/2.23-0ubuntu10_i386/    # extracted files
```

`download` tries tuna first and falls back to old-releases, so old versions no
longer need `download_old`.

### compile

```bash
./legacy/build 2.29 i686        # build glibc 2.29 for i686
```

Change `GLIBC_DIR` in the `build` script to customize install path.
