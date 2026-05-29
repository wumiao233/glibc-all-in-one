from dataclasses import dataclass


@dataclass
class Symbol:
    name: str
    addr: int
    size: int
    type: str
    bind: str
    version: str | None = None

    def __str__(self):
        ver = f"@{self.version}" if self.version else ""
        return f"{self.addr:016x} {self.type:6s} {self.bind:6s} {self.name}{ver}"


def dump_symbols(libc_path: str, filter_pattern: str | None = None) -> list[Symbol]:
    from elftools.elf.elffile import ELFFile

    symbols = []
    try:
        with open(libc_path, "rb") as f:
            elf = ELFFile(f)
            dynsym = elf.get_section_by_name(".dynsym")
            if dynsym is None:
                return []
            for sym in dynsym.iter_symbols():
                name = sym.name
                if not name or not sym.entry.st_value:
                    continue
                if filter_pattern and filter_pattern not in name:
                    continue
                symbols.append(Symbol(
                    name=name,
                    addr=sym.entry.st_value,
                    size=sym.entry.st_size,
                    type=sym.entry.st_info.type,
                    bind=sym.entry.st_info.bind,
                ))
    except FileNotFoundError:
        pass
    return symbols
