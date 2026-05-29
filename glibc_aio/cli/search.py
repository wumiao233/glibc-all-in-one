import fnmatch
import json
import sys
from glibc_aio.search.searcher import (
    SearchQuery,
    match_version_name,
    load_version_list,
    search_online_api,
)
from glibc_aio.search.symdb import search_local
from glibc_aio.analyze.symbols import dump_symbols
from glibc_aio.analyze.strings import search_strings


def _search_local_libc(args) -> bool:
    symbols = dump_symbols(args.libc)
    results = []

    sym_patterns = args.symbol if args.symbol else []
    if sym_patterns:
        results = list(symbols)
        for pat in sym_patterns:
            if "*" in pat or "?" in pat:
                results = [s for s in results if fnmatch.fnmatch(s.name, pat)]
            else:
                results = [s for s in results if s.name == pat]

        if args.ends_with:
            suffix = int(args.ends_with, 16)
            results = [s for s in results if (s.addr & 0xFFF) == suffix]

        if args.json:
            out = [{"name": s.name, "addr": hex(s.addr), "type": s.type} for s in results]
            print(json.dumps(out, indent=2))
        else:
            for s in results:
                print(f"{s.addr:016x}  {s.type:8s}  {s.name}")
            print(f"[*] {len(results)} symbol(s)")
        return True

    # String search (always runs independently of symbol filter)
    str_pattern = getattr(args, 'str_pattern_local', None)
    if str_pattern:
        try:
            matches = search_strings(args.libc, str_pattern)
        except ValueError as e:
            print(f"[-] {e}", file=sys.stderr)
            return False
        if args.json:
            out = [{"offset": hex(m.offset), "value": m.value} for m in matches]
            print(json.dumps(out, indent=2))
        else:
            for m in matches:
                print(f"  {m.offset:#010x}  {m.value}")
            print(f"[*] {len(matches)} match(es)")
        return True

    # If no symbol pattern, apply ends-with filter to all symbols
    if not sym_patterns and args.ends_with:
        suffix = int(args.ends_with, 16)
        results = [s for s in symbols if (s.addr & 0xFFF) == suffix]

    if args.json:
        out = [{"name": s.name, "addr": hex(s.addr), "type": s.type} for s in (results or symbols)]
        print(json.dumps(out, indent=2))
    else:
        for s in (results or symbols):
            print(f"{s.addr:016x}  {s.type:8s}  {s.name}")
        print(f"[*] {len(results or symbols)} symbol(s)")
    return True


def run(args) -> bool:
    if getattr(args, 'libc', None):
        return _search_local_libc(args)

    symbols = {}
    for s in args.symbol:
        try:
            name, addr = SearchQuery.parse_symbol_arg(s)
        except ValueError as e:
            print(f"[-] {e}", file=sys.stderr)
            return False
        symbols[name] = addr

    if args.query is not None and not symbols and not args.buildid:
        ids = load_version_list("list")
        results = match_version_name(args.query, ids)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            for r in results:
                print(r)
            print(f"[*] {len(results)} result(s)")
        return True

    query = SearchQuery(
        version_substr=args.query,
        symbols=symbols,
        buildid=args.buildid,
        tol=args.tol,
    )

    online_results = search_online_api(query)
    local_results = search_local(query.symbols, query.tol) if query.symbols else []

    if args.json:
        output = {"online": online_results, "local": local_results}
        print(json.dumps(output, indent=2))
    else:
        if online_results:
            print("[Online (libc.rip)]")
            for r in online_results:
                print(f"  {r.get('id', 'unknown')}")
        if local_results:
            print("[Local symdb]")
            for r in local_results:
                print(f"  {r['id']}  ({r['match_count']} symbol(s) matched)")
        if not online_results and not local_results:
            print("[*] No matches found")

    return True
