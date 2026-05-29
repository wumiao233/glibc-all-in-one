import os
import tempfile
from glibc_aio.packages.manager import list_downloaded, remove_version, get_disk_usage


def test_list_downloaded():
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "libs", "2.35-0ubuntu3_amd64"))
        os.makedirs(os.path.join(tmp, "libs", "2.27-3ubuntu1_i386"))
        result = list_downloaded(os.path.join(tmp, "libs"))
        assert "2.35-0ubuntu3_amd64" in result
        assert "2.27-3ubuntu1_i386" in result


def test_list_downloaded_empty():
    with tempfile.TemporaryDirectory() as tmp:
        libs_dir = os.path.join(tmp, "libs")
        os.makedirs(libs_dir)
        assert list_downloaded(libs_dir) == []


def test_remove_version():
    with tempfile.TemporaryDirectory() as tmp:
        libs_dir = os.path.join(tmp, "libs")
        ver_dir = os.path.join(libs_dir, "2.35-0ubuntu3_amd64")
        os.makedirs(ver_dir)
        remove_version(ver_dir)
        assert not os.path.exists(ver_dir)


def test_get_disk_usage():
    with tempfile.TemporaryDirectory() as tmp:
        libs_dir = os.path.join(tmp, "libs")
        os.makedirs(libs_dir)
        with open(os.path.join(libs_dir, "test.so"), "wb") as f:
            f.write(b"\x00" * 1024)
        usage = get_disk_usage(libs_dir)
        assert usage >= 1024
