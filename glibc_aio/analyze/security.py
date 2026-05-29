from dataclasses import dataclass


@dataclass
class SecurityReport:
    relro: str = "unknown"
    nx: bool = False
    canary: bool = False
    pie: bool = False
    runpath: str | None = None

    def __str__(self):
        lines = [
            f"RELRO:     {self.relro}",
            f"NX:        {'enabled' if self.nx else 'disabled'}",
            f"Canary:    {'enabled' if self.canary else 'disabled'}",
            f"PIE:       {'enabled' if self.pie else 'disabled'}",
        ]
        if self.runpath:
            lines.append(f"RUNPATH:   {self.runpath}")
        return "\n".join(lines)


def check_security(libc_path: str) -> SecurityReport | None:
    from elftools.elf.elffile import ELFFile

    try:
        with open(libc_path, "rb") as f:
            elf = ELFFile(f)
            report = SecurityReport()

            report.pie = elf.header.e_type == "ET_DYN"

            dynamic = elf.get_section_by_name(".dynamic")
            has_bind_now = False
            has_relro = False

            if dynamic:
                for tag in dynamic.iter_tags():
                    d_tag = tag.entry.d_tag
                    if d_tag == "DT_BIND_NOW" or d_tag == "DT_FLAGS_BIND_NOW":
                        has_bind_now = True
                    if d_tag == "DT_FLAGS":
                        if int(tag.entry.d_val) & 2:
                            has_bind_now = True
                    if d_tag in ("DT_RUNPATH", "DT_RPATH"):
                        report.runpath = tag.rpath if hasattr(tag, "rpath") else str(tag.entry.d_val)

            for seg in elf.iter_segments():
                if seg.header.p_type == "PT_GNU_RELRO":
                    has_relro = True
                if seg.header.p_type == "PT_GNU_STACK":
                    report.nx = not bool(seg.header.p_flags & 1)

            if has_bind_now and has_relro:
                report.relro = "full"
            elif has_relro:
                report.relro = "partial"
            else:
                report.relro = "none"

            dynsym = elf.get_section_by_name(".dynsym")
            if dynsym:
                for sym in dynsym.iter_symbols():
                    if sym.name == "__stack_chk_fail":
                        report.canary = True
                        break

            return report
    except FileNotFoundError:
        return None
