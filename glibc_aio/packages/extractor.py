import io
import os
import shutil
import tarfile
import tempfile
import zstandard

AR_MAGIC = b"!<arch>\n"
AR_HEADER_LEN = 60


def parse_ar(data: bytes) -> list[tuple[bytes, bytes]]:
    """Parse ar archive. Returns [(name, content), ...]."""
    if not data.startswith(AR_MAGIC):
        raise ValueError("Not an ar archive")
    entries = []
    pos = len(AR_MAGIC)
    while pos < len(data):
        if pos + AR_HEADER_LEN > len(data):
            break
        header = data[pos:pos + AR_HEADER_LEN]
        name = header[0:16].rstrip(b" ")
        if not name:
            break
        size_str = header[48:58].rstrip(b" ")
        if not size_str:
            break
        size = int(size_str)
        pos += AR_HEADER_LEN
        if pos + size > len(data):
            break
        content = data[pos:pos + size]
        entries.append((name, content))
        pos += size
        if size % 2:
            pos += 1
    return entries


def _copy_tree(src: str, dst: str) -> None:
    """Copy files/dirs/links from src into dst, merging directories."""
    if not os.path.isdir(src):
        return
    os.makedirs(dst, exist_ok=True)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.islink(s):
            if not os.path.lexists(d):
                os.symlink(os.readlink(s), d)
        elif os.path.isdir(s):
            _copy_tree(s, d)
        else:
            shutil.copy2(s, d)


def extract_deb(deb_path: str, out_dir: str) -> None:
    """Extract libc files from a .deb into out_dir. Pure Python."""
    with open(deb_path, "rb") as f:
        data = f.read()

    entries = parse_ar(data)
    data_tar = None
    for name, content in entries:
        base = name.rstrip(b"/").decode(errors="replace")
        if base.startswith("data.tar"):
            data_tar = content
            break

    if data_tar is None:
        raise ValueError("No data.tar.* found in .deb")

    os.makedirs(out_dir, exist_ok=True)

    try:
        dctx = zstandard.ZstdDecompressor()
        decompressed = dctx.decompress(data_tar, max_output_size=256 * 1024 * 1024)
    except (zstandard.ZstdError, ValueError):
        decompressed = data_tar

    with tempfile.TemporaryDirectory() as tmpdir:
        with tarfile.open(fileobj=io.BytesIO(decompressed), mode='r:*') as tf:
            tf.extractall(tmpdir)

        lib_roots = [
            os.path.join(tmpdir, "lib"),
            os.path.join(tmpdir, "lib32"),
            os.path.join(tmpdir, "usr", "lib"),
            os.path.join(tmpdir, "usr", "lib", "debug", "lib"),
            os.path.join(tmpdir, "usr", "lib", "debug", "lib32"),
        ]

        found = False
        for root in lib_roots:
            if not os.path.isdir(root):
                continue
            _copy_tree(root, out_dir)
            found = True

        buildid_dir = os.path.join(tmpdir, "usr", "lib", "debug", ".build-id")
        if os.path.isdir(buildid_dir):
            _copy_tree(buildid_dir, os.path.join(out_dir, ".build-id"))

        if not found:
            raise ValueError(f"No lib files found in {tmpdir}")
