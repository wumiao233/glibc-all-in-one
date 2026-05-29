import json
import urllib.request


def read_buildid(libc_path: str) -> str | None:
    from elftools.elf.elffile import ELFFile

    try:
        with open(libc_path, "rb") as f:
            elf = ELFFile(f)
            for sect in elf.iter_sections():
                if sect.name == ".note.gnu.build-id" and hasattr(sect, "note"):
                    bid = sect.note["n_desc"]
                    return bid.hex() if isinstance(bid, bytes) else bid
    except (FileNotFoundError, Exception):
        pass
    return None


def lookup_buildid(buildid: str) -> dict | None:
    try:
        url = "https://libc.rip/api/find"
        body = json.dumps({"buildid": buildid}).encode()
        req = urllib.request.Request(url, data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            if isinstance(data, list) and data:
                return data[0]
            return data if isinstance(data, dict) else None
    except Exception:
        return None
