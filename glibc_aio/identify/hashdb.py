import hashlib
import json
import os

CACHE_DIR = os.path.expanduser("~/.cache/glibc-aio/hashdb")


def compute_fingerprint(libc_path: str) -> str | None:
    from elftools.elf.elffile import ELFFile

    try:
        with open(libc_path, "rb") as f:
            elf = ELFFile(f)
            dynsym = elf.get_section_by_name(".dynsym")
            if dynsym is None:
                return None
            names = []
            for sym in dynsym.iter_symbols():
                if sym.name and sym.entry.st_value:
                    names.append(sym.name)
            canonical = "\n".join(sorted(set(names)))
            return hashlib.sha256(canonical.encode()).hexdigest()
    except FileNotFoundError:
        return None


def index_for_hashdb(libc_path: str, version_id: str) -> None:
    fp = compute_fingerprint(libc_path)
    if fp is None:
        return
    os.makedirs(CACHE_DIR, exist_ok=True)
    entry = {"id": version_id, "fingerprint": fp, "path": os.path.abspath(libc_path)}
    filepath = os.path.join(CACHE_DIR, f"{fp[:16]}.json")
    with open(filepath, "w") as f:
        json.dump(entry, f)


def lookup_fingerprint(libc_path: str) -> dict | None:
    fp = compute_fingerprint(libc_path)
    if fp is None:
        return None
    filepath = os.path.join(CACHE_DIR, f"{fp[:16]}.json")
    if os.path.isfile(filepath):
        with open(filepath) as f:
            return json.load(f)
    return None
