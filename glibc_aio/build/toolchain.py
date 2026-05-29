import re

TOOLCHAIN = {
    (2, 19): "ubuntu:14.04",
    (2, 23): "ubuntu:16.04",
    (2, 24): "ubuntu:16.04",
    (2, 25): "ubuntu:16.04",
    (2, 26): "ubuntu:16.04",
    (2, 27): "ubuntu:16.04",
    (2, 28): "ubuntu:18.04",
    (2, 29): "ubuntu:18.04",
    (2, 30): "ubuntu:20.04",
    (2, 31): "ubuntu:20.04",
    (2, 32): "ubuntu:20.04",
    (2, 33): "ubuntu:20.04",
    (2, 34): "ubuntu:20.04",
    (2, 35): "ubuntu:22.04",
    (2, 36): "ubuntu:22.04",
    (2, 37): "ubuntu:22.04",
    (2, 38): "ubuntu:24.04",
    (2, 39): "ubuntu:24.04",
}

SOURCE_BASE = "https://mirrors.ustc.edu.cn/gnu/libc"


def _sanitize_version(version: str) -> str:
    """Extract major.minor from a version string, rejecting shell metacharacters."""
    if re.search(r'[$`;|&><(){}!\[\]~\\\n\r]', version):
        raise ValueError(f"Invalid version: {version!r} contains shell metacharacters")
    m = re.match(r'^(\d+\.\d+)', version)
    if not m:
        raise ValueError(f"Invalid version format: {version!r}. Expected e.g. '2.29' or '2.29-0ubuntu3'")
    return m.group(1)


def resolve_image(version: str, arch: str) -> str:
    ver = _sanitize_version(version)
    major, minor = int(ver.split(".")[0]), int(ver.split(".")[1])

    if (major, minor) in TOOLCHAIN:
        return TOOLCHAIN[(major, minor)]

    for (vmajor, vminor), image in sorted(TOOLCHAIN.items(), reverse=True):
        if (major, minor) >= (vmajor, vminor):
            return image

    return "ubuntu:latest"


def source_url(version: str) -> str:
    return f"{SOURCE_BASE}/glibc-{version}.tar.gz"


def build_script(version: str, arch: str, prefix: str) -> str:
    _sanitize_version(version)
    lines = [
        "set -e",
        "apt-get update -qq",
        "apt-get install -y -qq build-essential gawk bison python3 wget",
    ]
    if arch == "i686":
        lines.append("apt-get install -y -qq gcc-multilib g++-multilib")

    lines += [
        f'wget -q "{source_url(version)}" -O /tmp/src.tar.gz',
        "mkdir -p /tmp/src /tmp/build",
        "cd /tmp/src && tar xf /tmp/src.tar.gz --strip-components=1",
        "cd /tmp/build",
    ]

    if arch == "amd64":
        lines.append(
            "../src/configure --prefix=/out "
            "--disable-werror --enable-debug=yes"
        )
    elif arch == "i686":
        lines.append(
            "../src/configure --prefix=/out "
            '--disable-werror --enable-debug=yes '
            "--host=i686-linux-gnu --build=i686-linux-gnu "
            'CC="gcc -m32" CXX="g++ -m32"'
        )
    else:
        raise ValueError(f"Unsupported arch: {arch}")

    lines.append("make -j$(nproc)")
    lines.append("make install")
    return "\n".join(lines)
