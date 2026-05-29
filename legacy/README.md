# glibc-all-in-one (Legacy)

These are the original shell scripts from v1. They still work but are no longer maintained.

**The new v2 tool (`glibc-aio`) replaces all of them with a unified CLI.** See the main [README.md](../README.md).

## Scripts

- `update_list` — scrape Ubuntu mirrors for available libc packages
- `download` — download libc + debug .deb from regular mirrors
- `download_old` — download from old-releases mirror
- `extract` — extract .deb files (requires system `ar`, `tar`)
- `build` — compile glibc from source on host

## Usage (original)

### download

```bash
./update_list                    # refresh package lists
cat list                        # see available versions
./download 2.23-0ubuntu10_i386  # download libc + debug
ls libs/2.23-0ubuntu10_i386/    # extracted files
```

### compile

```bash
./build 2.29 i686               # build glibc 2.29 for i686
```

Change `GLIBC_DIR` in the `build` script to customize install path.
