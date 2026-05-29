from dataclasses import dataclass, field
from glibc_aio.analyze.symbols import Symbol, dump_symbols
from glibc_aio.analyze.security import SecurityReport, check_security


@dataclass
class DiffReport:
    a_path: str
    b_path: str
    added_symbols: list[Symbol] = field(default_factory=list)
    removed_symbols: list[Symbol] = field(default_factory=list)
    offset_changed: list[tuple[Symbol, Symbol]] = field(default_factory=list)
    security_diff: list[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not any([
            self.added_symbols, self.removed_symbols,
            self.offset_changed, self.security_diff,
        ])

    def __str__(self):
        lines = [f"--- {self.a_path}", f"+++ {self.b_path}", ""]
        for s in self.added_symbols:
            lines.append(f"+ {s}")
        for s in self.removed_symbols:
            lines.append(f"- {s}")
        for old, new in self.offset_changed:
            lines.append(f"~ {old.name}: {old.addr:#x} -> {new.addr:#x}")
        for sd in self.security_diff:
            lines.append(f"! {sd}")
        return "\n".join(lines) if len(lines) > 2 else "(no differences)"


def diff(a_path: str, b_path: str) -> DiffReport:
    report = DiffReport(a_path=a_path, b_path=b_path)

    a_syms = {s.name: s for s in dump_symbols(a_path)}
    b_syms = {s.name: s for s in dump_symbols(b_path)}

    for name, sym in b_syms.items():
        if name not in a_syms:
            report.added_symbols.append(sym)
    for name, sym in a_syms.items():
        if name not in b_syms:
            report.removed_symbols.append(sym)
        elif a_syms[name].addr != b_syms[name].addr:
            report.offset_changed.append((a_syms[name], b_syms[name]))

    a_sec = check_security(a_path)
    b_sec = check_security(b_path)
    if a_sec and b_sec:
        for attr in ("relro", "nx", "canary", "pie", "runpath"):
            av = getattr(a_sec, attr)
            bv = getattr(b_sec, attr)
            if av != bv:
                report.security_diff.append(f"{attr}: {av} -> {bv}")

    return report
