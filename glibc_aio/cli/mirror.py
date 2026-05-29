import json
from glibc_aio.mirrors.sources import MIRRORS
from glibc_aio.mirrors.fetcher import update_list


def run(args) -> bool:
    if args.action == "list":
        if args.json:
            mirrors_data = [{"name": m.name, "url": m.url, "type": m.type} for m in MIRRORS]
            print(json.dumps(mirrors_data, indent=2))
        else:
            for m in MIRRORS:
                print(f"  {m.name:20s} {m.url:60s} [{m.type}]")
        return True

    if args.action == "update":
        update_list()
        return True

    return False
