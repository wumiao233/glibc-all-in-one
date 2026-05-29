import json
import sys
from glibc_aio.build.compiler import build


def run(args) -> bool:
    try:
        out = build(
            version=args.version,
            arch=args.arch,
            image=args.image,
            prefix=args.prefix,
            no_docker=args.no_docker,
        )
        if args.json:
            print(json.dumps({"status": "ok", "output": out}))
        else:
            print(f"[+] Build complete: {out}")
        return True
    except Exception as e:
        print(f"[-] Build failed: {e}", file=sys.stderr)
        return False
