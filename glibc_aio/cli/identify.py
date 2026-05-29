import json
import sys
from glibc_aio.identify import identify


def run(args) -> bool:
    result = identify(args.libc, offline=args.offline)
    if result:
        if args.json:
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
