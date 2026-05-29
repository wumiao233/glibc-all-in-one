import re
from dataclasses import dataclass


@dataclass
class StringMatch:
    offset: int
    value: str


def search_strings(libc_path: str, pattern: str) -> list[StringMatch]:
    from elftools.elf.elffile import ELFFile

    matches = []
    try:
        regex = re.compile(pattern.encode())
    except re.error as e:
        raise ValueError(f"Invalid regex pattern: {e}") from e

    try:
        with open(libc_path, "rb") as f:
            elf = ELFFile(f)
            for sec_name in (".rodata", ".data"):
                sec = elf.get_section_by_name(sec_name)
                if sec is None:
                    continue
                offset = sec["sh_offset"]
                size = sec["sh_size"]
                f.seek(offset)
                data = f.read(size)
                for m in regex.finditer(data):
                    try:
                        val = m.group().decode("utf-8", errors="replace")
                    except Exception:
                        val = repr(m.group())
                    matches.append(StringMatch(
                        offset=offset + m.start(),
                        value=val,
                    ))
    except FileNotFoundError:
        pass
    return matches
