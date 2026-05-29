import json
import os
import urllib.request
from dataclasses import dataclass, field


@dataclass
class SearchQuery:
    version_substr: str | None = None
    symbols: dict[str, int] = field(default_factory=dict)
    strings: dict[str, int] = field(default_factory=dict)
    buildid: str | None = None
    tol: int = 0

    @classmethod
    def parse_symbol_arg(cls, arg: str) -> tuple[str, int]:
        if "=" not in arg:
            raise ValueError(f"Invalid format: {arg!r}. Expected 'name=0xADDR'")
        name, addr_str = arg.split("=", 1)
        try:
            addr = int(addr_str, 16)
        except ValueError:
            raise ValueError(f"Invalid address: {addr_str!r}. Expected hex (e.g. 0x4c490)")
        return name, addr


def match_version_name(query: str, version_ids: list[str]) -> list[str]:
    q = query.lower()
    return sorted(v for v in version_ids if q in v.lower())


def load_version_list(path: str = "list") -> list[str]:
    """Load unified package list. Handles both new format (with [old] section
    marker) and legacy separate list/old_list files."""
    if not os.path.isfile(path):
        return []
    with open(path) as f:
        return [line.strip() for line in f if line.strip() and line.strip() != "[old]"]


def _query_libc_rip_api(endpoint: str, body: dict) -> list[dict]:
    """Query libc.rip API. Returns list of results, empty on failure."""
    try:
        url = f"https://libc.rip/api/{endpoint}"
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            results = json.loads(resp.read())
            return results if isinstance(results, list) else [results]
    except Exception:
        return []


def search_online_api(query: SearchQuery) -> list[dict]:
    if query.buildid:
        return _query_libc_rip_api("find", {"buildid": query.buildid})

    if query.symbols:
        sym_kwargs = {name: hex(addr) for name, addr in query.symbols.items()}
        return _query_libc_rip_api("find", {"symbols": sym_kwargs})

    return []
