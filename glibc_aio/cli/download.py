import json
import os
import sys
import glob
from glibc_aio.packages.downloader import download_single
from glibc_aio.search.symdb import index_libc
from glibc_aio.identify.hashdb import index_for_hashdb


def run(args) -> bool:
    try:
        out_dir = download_single(
            args.id,
            mirror_name=args.mirror,
            dbg=not args.no_dbg,
            keep_deb=args.keep_deb,
        )
        candidates = glob.glob(f"{out_dir}/**/libc[-.]*.so*", recursive=True)
        candidates += glob.glob(f"{out_dir}/**/libc.so*", recursive=True)
        for libc in candidates:
            base = os.path.basename(libc)
            if "libcrypto" in base or "libcidn" in base:
                continue
            index_libc(libc, args.id)
            index_for_hashdb(libc, args.id)
            break

        if args.json:
            print(json.dumps({"status": "ok", "path": out_dir}))
        else:
            print(f"[+] Downloaded to {out_dir}")
        return True
    except FileExistsError as e:
        print(f"[!] {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[-] {e}", file=sys.stderr)
        return False
