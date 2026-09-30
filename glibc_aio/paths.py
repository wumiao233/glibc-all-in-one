"""Repo-root-relative paths.

`libs/`, `debs/`, `srcs/` and `list` always live in the repository root,
never next to whatever directory the command happened to run from.
Resolution order:

1. ``GLIBC_AIO_ROOT`` environment variable
2. nearest parent directory containing ``pyproject.toml``
3. the current working directory
"""

import os
from pathlib import Path

ROOT_ENV = "GLIBC_AIO_ROOT"


def _find_root() -> Path:
    env = os.environ.get(ROOT_ENV)
    if env:
        return Path(env).expanduser()

    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").is_file():
            return parent

    return Path.cwd()


ROOT_DIR = _find_root().resolve()


def root() -> Path:
    return ROOT_DIR


def libs() -> Path:
    return ROOT_DIR / "libs"


def debs() -> Path:
    return ROOT_DIR / "debs"


def srcs() -> Path:
    return ROOT_DIR / "srcs"


def libs_build() -> Path:
    return libs() / "build"


def list_path() -> Path:
    return ROOT_DIR / "list"
