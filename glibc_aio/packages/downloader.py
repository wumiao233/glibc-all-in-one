import os
import shutil
import urllib.request
from glibc_aio import paths
from glibc_aio.mirrors.sources import MIRRORS, Mirror
from glibc_aio.packages.extractor import extract_deb


def build_deb_url(base_url: str, prefix: str, version_id: str) -> str:
    return f"{base_url}/{prefix}_{version_id}.deb"


def resolve_mirror_order(mirror_name: str | None) -> list[Mirror]:
    if mirror_name:
        m = next((m for m in MIRRORS if m.name == mirror_name), None)
        if m is None:
            raise ValueError(f"Unknown mirror: {mirror_name}")
        return [m]
    regulars = [m for m in MIRRORS if m.type == "regular"]
    fallbacks = [m for m in MIRRORS if m.type == "fallback"]
    return regulars + fallbacks


def download_single(version_id: str, mirror_name: str | None = None,
                    dbg: bool = True, keep_deb: bool = False) -> str:
    if os.path.isabs(version_id) or ".." in version_id:
        raise ValueError(f"Invalid version_id: {version_id!r}")

    libs_dir = paths.libs()
    debs_dir = paths.debs()
    libs_dir.mkdir(parents=True, exist_ok=True)
    debs_dir.mkdir(parents=True, exist_ok=True)

    out_dir = libs_dir / version_id
    if out_dir.is_dir():
        raise FileExistsError(f"Already downloaded: {out_dir}")

    mirrors = resolve_mirror_order(mirror_name)
    prefixes = ["libc6"]
    if dbg:
        prefixes.append("libc6-dbg")

    try:
        for prefix in prefixes:
            deb_name = f"{prefix}_{version_id}.deb"
            deb_path = debs_dir / deb_name
            downloaded = False
            for mirror in mirrors:
                url = build_deb_url(mirror.url, prefix, version_id)
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "glibc-aio"})
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        with open(deb_path, "wb") as f:
                            f.write(resp.read())
                    downloaded = True
                    break
                except Exception:
                    continue
            if not downloaded:
                if not dbg:
                    raise RuntimeError(f"Failed to download {deb_name} from all mirrors")
                for mirror in MIRRORS:
                    if mirror.type == "fallback":
                        url = build_deb_url(mirror.url, prefix, version_id)
                        try:
                            req = urllib.request.Request(url, headers={"User-Agent": "glibc-aio"})
                            with urllib.request.urlopen(req, timeout=30) as resp:
                                with open(deb_path, "wb") as f:
                                    f.write(resp.read())
                            downloaded = True
                            break
                        except Exception:
                            continue
                if not downloaded:
                    raise RuntimeError(f"Failed to download {deb_name} from all mirrors")

            if prefix == "libc6":
                extract_deb(deb_path, out_dir)
            else:
                dbg_dir = out_dir / ".debug"
                extract_deb(deb_path, dbg_dir)
    except Exception:
        if out_dir.is_dir():
            shutil.rmtree(out_dir, ignore_errors=True)
        raise

    if not keep_deb:
        for prefix in prefixes:
            deb_name = f"{prefix}_{version_id}.deb"
            deb_path = debs_dir / deb_name
            if deb_path.is_file():
                deb_path.unlink()

    return out_dir
