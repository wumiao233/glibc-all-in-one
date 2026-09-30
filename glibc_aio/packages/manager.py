import os
import shutil

from glibc_aio import paths


def list_downloaded(libs_dir=None) -> list[str]:
    if libs_dir is None:
        libs_dir = paths.libs()
    if not os.path.isdir(libs_dir):
        return []
    return sorted(
        d for d in os.listdir(libs_dir)
        if os.path.isdir(os.path.join(libs_dir, d))
    )


def remove_version(path: str) -> None:
    if os.path.isdir(path):
        shutil.rmtree(path)


def get_disk_usage(libs_dir=None) -> int:
    total = 0
    if libs_dir is None:
        libs_dir = paths.libs()
    if not os.path.isdir(libs_dir):
        return 0
    for root, dirs, files in os.walk(libs_dir):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def format_size(bytes_: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if bytes_ < 1024:
            return f"{bytes_:.1f} {unit}"
        bytes_ /= 1024
    return f"{bytes_:.1f} TB"
