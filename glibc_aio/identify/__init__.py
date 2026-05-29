from .buildid import read_buildid, lookup_buildid
from .hashdb import lookup_fingerprint, index_for_hashdb


def identify(libc_path: str, offline: bool = False) -> dict | None:
    buildid = read_buildid(libc_path)

    if buildid and not offline:
        result = lookup_buildid(buildid)
        if result:
            return {"method": "buildid", "buildid": buildid, "id": result.get("id", "unknown")}

    result = lookup_fingerprint(libc_path)
    if result:
        return {"method": "fingerprint", "id": result["id"]}

    return None
