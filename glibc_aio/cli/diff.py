import json
from glibc_aio.diff.comparator import diff


def run(args) -> bool:
    report = diff(args.libc_a, args.libc_b)
    if args.json:
        output = {
            "added_symbols": [s.name for s in report.added_symbols],
            "removed_symbols": [s.name for s in report.removed_symbols],
            "offset_changed": [
                {"name": old.name, "old": hex(old.addr), "new": hex(new.addr)}
                for old, new in report.offset_changed
            ],
            "security_diff": report.security_diff,
        }
        print(json.dumps(output, indent=2))
    else:
        print(report)
    return True
