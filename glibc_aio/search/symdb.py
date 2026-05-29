import json
import os

CACHE_DIR = os.path.expanduser("~/.cache/glibc-aio/symdb")


def _db_path(version_id: str) -> str:
    safe_id = version_id.replace("/", "_").replace("\\", "_")
    return os.path.join(CACHE_DIR, f"{safe_id}.json")


def index_libc(libc_path: str, version_id: str) -> None:
    from elftools.elf.elffile import ELFFile

    os.makedirs(CACHE_DIR, exist_ok=True)

    symbols: dict[str, int] = {}
    with open(libc_path, "rb") as f:
        elf = ELFFile(f)
        dynsym = elf.get_section_by_name(".dynsym")
        if dynsym:
            for sym in dynsym.iter_symbols():
                if sym.entry.st_value and sym.name:
                    symbols[sym.name] = sym.entry.st_value

    with open(_db_path(version_id), "w") as f:
        json.dump({"id": version_id, "symbols": symbols}, f, indent=2)


def search_local(symbols: dict[str, int], tol: int = 0) -> list[dict]:
    if not os.path.isdir(CACHE_DIR):
        return []

    results = []
    for filename in os.listdir(CACHE_DIR):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(CACHE_DIR, filename)
        try:
            with open(filepath) as f:
                entry = json.load(f)
        except (json.JSONDecodeError, KeyError):
            continue

        match_count = 0
        for name, target_addr in symbols.items():
            local_addr = entry.get("symbols", {}).get(name)
            if local_addr is not None and abs(local_addr - target_addr) <= tol:
                match_count += 1

        if match_count == len(symbols):
            results.append({"id": entry["id"], "match_count": match_count})

    return sorted(results, key=lambda r: r["match_count"], reverse=True)
