import argparse
import json
import os
import re
import sys


def _is_libc_path(s: str) -> bool:
    return os.path.isfile(s) or s.endswith(".so")


def _is_hex(s: str) -> bool:
    """True if arg looks like a hex address (0x prefix, or 5+ hex digits)."""
    if s.startswith("0x") or s.startswith("0X"):
        s = s[2:]
        return bool(re.fullmatch(r'[0-9a-fA-F]+', s))
    # Bare hex: need 5+ digits to avoid ambiguity with symbol names
    # like dead, face, cafe, beef (all valid symbol names)
    return len(s) >= 5 and bool(re.fullmatch(r'[0-9a-fA-F]+', s))


def _is_hex_lenient(s: str) -> bool:
    """True if arg is any valid hex string (used in file context where
    ambiguity with symbol names is resolved by file detection)."""
    raw = s[2:] if s.startswith("0x") or s.startswith("0X") else s
    return bool(re.fullmatch(r'[0-9a-fA-F]+', raw))


def _is_version(s: str) -> bool:
    return bool(re.match(r'^\d+\.\d+', s))


def _is_symbol(s: str) -> bool:
    return bool(re.fullmatch(r'[a-zA-Z_*?][a-zA-Z0-9_*?]*', s))


def _smart_dispatch(args_list: list[str], json_output: bool) -> bool:
    files = []
    symbols = []
    hex_addrs = []
    version = None

    for arg in args_list:
        if _is_libc_path(arg):
            files.append(arg)
        elif files and _is_hex_lenient(arg):
            hex_addrs.append(arg)
        elif not files and _is_hex(arg):
            hex_addrs.append(arg)
        elif _is_version(arg) and not files and not symbols and not hex_addrs:
            version = arg
        elif _is_symbol(arg):
            symbols.append(arg)
        else:
            print(f"[-] Cannot interpret argument: {arg!r}", file=sys.stderr)
            return False

    # Case: version + symbol(s) → search downloaded libcs matching version
    if version and symbols and not files and not hex_addrs:
        from glibc_aio.packages.manager import list_downloaded
        from glibc_aio.analyze.symbols import dump_symbols
        libs = [d for d in list_downloaded() if version in d]
        if not libs:
            print(f"[-] No downloaded libcs matching '{version}'", file=sys.stderr)
            return False
        for lib_id in sorted(libs):
            import glob
            candidates = glob.glob(f"libs/{lib_id}/**/libc[-.]*.so*", recursive=True)
            candidates += glob.glob(f"libs/{lib_id}/**/libc.so*", recursive=True)
            if not candidates:
                continue
            libc_path = candidates[0]
            syms = dump_symbols(libc_path)
            results = list(syms)
            for pat in symbols:
                if "*" in pat or "?" in pat:
                    import fnmatch
                    results = [s for s in results if fnmatch.fnmatch(s.name, pat)]
                else:
                    results = [s for s in results if s.name == pat]
            if json_output:
                pass  # handled below
            else:
                print(f"\n{lib_id}:")
                for s in results:
                    print(f"  {s.addr:016x}  {s.type:8s}  {s.name}")
        if json_output:
            out = {}
            for lib_id in sorted(libs):
                import glob
                candidates = glob.glob(f"libs/{lib_id}/**/libc[-.]*.so*", recursive=True)
                candidates += glob.glob(f"libs/{lib_id}/**/libc.so*", recursive=True)
                if not candidates:
                    continue
                syms = dump_symbols(candidates[0])
                results = list(syms)
                for pat in symbols:
                    if "*" in pat or "?" in pat:
                        import fnmatch
                        results = [s for s in results if fnmatch.fnmatch(s.name, pat)]
                    else:
                        results = [s for s in results if s.name == pat]
                out[lib_id] = [{"name": s.name, "addr": hex(s.addr), "type": s.type} for s in results]
            print(json.dumps(out, indent=2))
        return True

    # Case: version only → version search
    if version and not symbols and not files and not hex_addrs:
        from glibc_aio.search.searcher import match_version_name, load_version_list
        ids = load_version_list("list")
        results = match_version_name(version, ids)
        if json_output:
            print(json.dumps(results, indent=2))
        else:
            for r in results:
                print(r)
            print(f"[*] {len(results)} result(s)")
        return True

    # Case: file only → identify
    if len(files) == 1 and not symbols and not hex_addrs:
        from glibc_aio.identify import identify
        result = identify(files[0])
        if result:
            if json_output:
                print(json.dumps(result, indent=2))
            else:
                print(f"Method:    {result['method']}")
                print(f"Version:   {result.get('id', 'unknown')}")
                if "buildid" in result:
                    print(f"BuildID:   {result['buildid']}")
            return True
        else:
            print("[-] Could not identify this libc", file=sys.stderr)
            return False

    # Case: file + symbol(s) → search --libc
    if files and symbols and not hex_addrs:
        if len(files) > 1:
            print("[-] Only one libc file supported in smart mode", file=sys.stderr)
            return False
        from glibc_aio.analyze.symbols import dump_symbols
        syms = dump_symbols(files[0])
        results = list(syms)
        for pat in symbols:
            if "*" in pat or "?" in pat:
                import fnmatch
                results = [s for s in results if fnmatch.fnmatch(s.name, pat)]
            else:
                results = [s for s in results if s.name == pat]
        if json_output:
            out = [{"name": s.name, "addr": hex(s.addr), "type": s.type} for s in results]
            print(json.dumps(out, indent=2))
        else:
            for s in results:
                print(f"{s.addr:016x}  {s.type:8s}  {s.name}")
            print(f"[*] {len(results)} symbol(s)")
        return True

    # Case: file + hex → search --ends-with
    if files and hex_addrs and not symbols:
        if len(files) > 1:
            print("[-] Only one libc file supported in smart mode", file=sys.stderr)
            return False
        from glibc_aio.analyze.symbols import dump_symbols
        syms = dump_symbols(files[0])
        for h in hex_addrs:
            val = int(h.replace("0x", "").replace("0X", ""), 16)
            # Mask: match by hex digit count (2-digit = byte, 3-digit = 12-bit, etc)
            mask = (1 << (len(h.replace("0x", "").replace("0X", "")) * 4)) - 1
            results = [s for s in syms if (s.addr & mask) == (val & mask)]
            syms = results
        if json_output:
            out = [{"name": s.name, "addr": hex(s.addr), "type": s.type} for s in syms]
            print(json.dumps(out, indent=2))
        else:
            for s in syms:
                print(f"{s.addr:016x}  {s.type:8s}  {s.name}")
            print(f"[*] {len(syms)} symbol(s)")
        return True

    # Case: file + symbol + hex → filter symbols, then ends-with
    if files and symbols and hex_addrs:
        if len(files) > 1:
            print("[-] Only one libc file supported in smart mode", file=sys.stderr)
            return False
        from glibc_aio.analyze.symbols import dump_symbols
        import fnmatch
        syms = dump_symbols(files[0])
        results = list(syms)
        for pat in symbols:
            if "*" in pat or "?" in pat:
                results = [s for s in results if fnmatch.fnmatch(s.name, pat)]
            else:
                results = [s for s in results if s.name == pat]
        for h in hex_addrs:
            val = int(h.replace("0x", "").replace("0X", ""), 16)
            mask = (1 << (len(h.replace("0x", "").replace("0X", "")) * 4)) - 1
            results = [s for s in results if (s.addr & mask) == (val & mask)]
        if json_output:
            out = [{"name": s.name, "addr": hex(s.addr), "type": s.type} for s in results]
            print(json.dumps(out, indent=2))
        else:
            for s in results:
                print(f"{s.addr:016x}  {s.type:8s}  {s.name}")
            print(f"[*] {len(results)} symbol(s)")
        return True

    # Case: symbol + hex pairs → online search
    if symbols and hex_addrs and not files:
        if len(symbols) != len(hex_addrs):
            print("[-] Symbol and hex args must be paired (same count)", file=sys.stderr)
            return False
        sym_dict = {}
        for name, addr in zip(symbols, hex_addrs):
            sym_dict[name] = int(addr.replace("0x", "").replace("0X", ""), 16)

        from glibc_aio.search.searcher import SearchQuery, search_online_api
        from glibc_aio.search.symdb import search_local
        query = SearchQuery(symbols=sym_dict)
        online = search_online_api(query)
        local = search_local(query.symbols)
        if json_output:
            print(json.dumps({"online": online, "local": local}, indent=2))
        else:
            if online:
                print("[Online (libc.rip)]")
                for r in online:
                    print(f"  {r.get('id', 'unknown')}")
            if local:
                print("[Local symdb]")
                for r in local:
                    print(f"  {r['id']}  ({r['match_count']} symbol(s) matched)")
            if not online and not local:
                print("[*] No matches found")
        return True

    # Case: file only (handled above), rest is ambiguous
    print("[-] Could not determine what to do with these arguments", file=sys.stderr)
    print("[*] Try: glibc-aio --help", file=sys.stderr)
    return False


def main():
    parser = argparse.ArgumentParser(
        prog="glibc-aio",
        description="All-in-one glibc analysis toolkit",
    )
    parser.add_argument("--version", action="version", version="glibc-aio 2.0.0")
    parser.add_argument("--json", action="store_true", default=False,
                        help="Output in JSON format")
    subparsers = parser.add_subparsers(dest="command")

    def _add_json(p):
        p.add_argument("--json", action="store_true", default=False,
                       help="Output in JSON format")

    # mirror
    mirror_p = subparsers.add_parser("mirror", help="Manage mirror sources")
    _add_json(mirror_p)
    mirror_sp = mirror_p.add_subparsers(dest="action")
    mirror_list_p = mirror_sp.add_parser("list", help="Show all mirrors")
    _add_json(mirror_list_p)
    mirror_update_p = mirror_sp.add_parser("update", help="Refresh package lists")
    _add_json(mirror_update_p)

    # search
    search_p = subparsers.add_parser("search", help="Search for glibc versions / local libc symbols")
    _add_json(search_p)
    search_p.add_argument("query", nargs="?", default=None,
                          help="Version name substring to search")
    search_p.add_argument("--libc", default=None,
                          help="Local libc file to search (enables local lookup mode)")
    search_p.add_argument("--symbol", action="append", default=[],
                          help="Symbol name/glob (local) or name=addr (online)")
    search_p.add_argument("--str", default=None,
                          dest="str_pattern_local", help="Search strings in local libc")
    search_p.add_argument("--ends-with", default=None,
                          help="Filter symbols whose address ends with this hex value")
    search_p.add_argument("--buildid", default=None, help="BuildID hash (online)")
    search_p.add_argument("--tol", type=int, default=0,
                          help="Offset tolerance for online --symbol (+/- bytes)")

    # download
    dl_p = subparsers.add_parser("download", help="Download libc + debug symbols")
    _add_json(dl_p)
    dl_p.add_argument("id", help="Version ID (e.g. 2.35-0ubuntu3.8_amd64)")
    dl_p.add_argument("--mirror", default=None, help="Pin a specific mirror")
    dl_p.add_argument("--no-dbg", action="store_true", help="Skip debug package")
    dl_p.add_argument("--keep-deb", action="store_true", help="Keep .deb files")

    # identify
    id_p = subparsers.add_parser("identify", help="Identify libc version")
    _add_json(id_p)
    id_p.add_argument("libc", help="Path to libc.so")
    id_p.add_argument("--offline", action="store_true", help="Skip online lookup")

    # diff
    diff_p = subparsers.add_parser("diff", help="Compare two libc binaries")
    _add_json(diff_p)
    diff_p.add_argument("libc_a", help="First libc")
    diff_p.add_argument("libc_b", help="Second libc")

    # build
    build_p = subparsers.add_parser("build", help="Build glibc from source")
    _add_json(build_p)
    build_p.add_argument("version", help="Glibc version (e.g. 2.29)")
    build_p.add_argument("arch", choices=["amd64", "i686"], help="Target architecture")
    build_p.add_argument("--image", default=None, help="Override Docker image")
    build_p.add_argument("--prefix", default=None, help="Install prefix")
    build_p.add_argument("--no-docker", action="store_true", help="Force host build")

    # Check if first positional arg is a known subcommand
    KNOWN = {"mirror", "search", "download", "identify", "diff", "build"}
    argv = sys.argv[1:]
    json_flag = "--json" in argv

    # Filter out --json for subcommand detection
    positional = [a for a in argv if not a.startswith("-")]
    if positional and positional[0] in KNOWN:
        args = parser.parse_args()
        from . import mirror, search, download, identify, diff, build as build_mod
        mods = {
            "mirror": mirror, "search": search, "download": download,
            "identify": identify, "diff": diff,
            "build": build_mod,
        }
        handler = getattr(mods[args.command], "run", None)
        if handler:
            if handler(args) is False:
                sys.exit(1)
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            sys.exit(1)
    elif positional:
        if not _smart_dispatch(positional, json_flag):
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
