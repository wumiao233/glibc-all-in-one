import re
import urllib.request
from .sources import MIRRORS

LIBC_PATTERN = re.compile(r'libc6_(2\.[0-9][0-9]-[0-9]ubuntu[0-9.]*_(?:amd64|i386))\.deb')


def parse_deb_listing(html: bytes) -> list[str]:
    ids = LIBC_PATTERN.findall(html.decode(errors='replace'))
    return sorted(set(ids))


def fetch_packages(mirror_name: str | None = None) -> dict[str, list[str]]:
    mirrors = [m for m in MIRRORS if mirror_name is None or m.name == mirror_name]
    result: dict[str, list[str]] = {}
    for m in mirrors:
        try:
            with urllib.request.urlopen(m.url, timeout=30) as resp:
                result[m.name] = parse_deb_listing(resp.read())
        except Exception:
            result[m.name] = []
    return result


def update_list() -> None:
    regular_ids: set[str] = set()
    fallback_ids: set[str] = set()
    for m in MIRRORS:
        try:
            with urllib.request.urlopen(m.url, timeout=30) as resp:
                ids = parse_deb_listing(resp.read())
        except Exception:
            continue
        if m.type == "regular":
            regular_ids.update(ids)
        else:
            fallback_ids.update(ids)
    # Dedup: fallback-only packages
    fallback_only = fallback_ids - regular_ids
    with open("list", "w") as f:
        for i in sorted(regular_ids):
            f.write(i + "\n")
        f.write("[old]\n")
        for i in sorted(fallback_only):
            f.write(i + "\n")
    print(f'[+] Saved {len(regular_ids)} + {len(fallback_only)} old packages to "list"')
