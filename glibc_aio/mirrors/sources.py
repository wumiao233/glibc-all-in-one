from dataclasses import dataclass
from typing import Literal

MirrorType = Literal["regular", "fallback"]


@dataclass
class Mirror:
    name: str
    url: str
    type: MirrorType

    def __str__(self):
        return f"{self.name} [{self.type}]"


MIRRORS = [
    Mirror("tuna", "https://mirror.tuna.tsinghua.edu.cn/ubuntu/pool/main/g/glibc", "regular"),
    Mirror("ustc", "https://mirrors.ustc.edu.cn/ubuntu/pool/main/g/glibc", "regular"),
    Mirror("ubuntu-archive", "http://archive.ubuntu.com/ubuntu/pool/main/g/glibc", "regular"),
    Mirror("old-releases", "http://old-releases.ubuntu.com/ubuntu/pool/main/g/glibc", "fallback"),
]
