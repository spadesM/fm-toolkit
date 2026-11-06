import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as dhf
from check_deep_sorting import rva_to_method_name, meta, types_off, types_sz, methods_off, get_mstr
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

md = Cs(CS_ARCH_X86, CS_MODE_64)

def disasm_func(name, rva, sz):
    print(f"\n==================== {name} (0x{rva:08x}, sz=0x{sz:x}) ====================")
    off = dhf.va_to_off(dhf.image_base + rva)
    code = dhf.pe[off : off + sz]
    umap = dhf.get_usym_dict(rva, sz)
    for insn in md.disasm(code, rva):
        cur = insn.address
        rel = cur - rva
        if cur in umap:
            print(f"  ; USYM: {', '.join(umap[cur])}")
        comment = ""
        raw = insn.bytes
        if len(raw) == 5 and raw[0] in (0xE8, 0xE9):
            disp = struct.unpack_from("<i", raw, 1)[0]
            trva = cur + 5 + disp
            mnames = rva_to_method_name.get(trva, [])
            if mnames:
                comment = f" ; -> {', '.join(mnames[:3])}"
        elif len(raw) == 7 and raw[0] in (0x48, 0x4C) and raw[1] in (0x8B, 0x8D) and (raw[2] & 0xC7) == 0x05:
            disp = struct.unpack_from("<i", raw, 3)[0]
            tva = dhf.image_base + cur + 7 + disp
            rinfo = dhf.resolve_rip(tva)
            if rinfo:
                comment = f" ; {rinfo}"
        # Check for 4-byte immediate in mov ecx/edx or cmp edx
        if insn.mnemonic in ("mov", "cmp") and ", 0x" in insn.op_str:
            try:
                imm_str = insn.op_str.split(", 0x")[1]
                imm = int(imm_str, 16)
                if 0x20202020 <= imm <= 0x7E7E7E7E:
                    b4 = struct.pack("<I", imm)
                    if all(32 <= b <= 126 for b in b4):
                        comment += f" ; 4CC={list(b4)}"
            except Exception:
                pass
        print(f"  +0x{rel:03x} (0x{cur:08x}): {insn.mnemonic:<8} {insn.op_str}{comment}")

if __name__ == "__main__":
    for name, rva, sz in [
        ("StreamedListView.ApplySorting", 0x015a4260, 0x4A6),
        ("StreamedListView.<ApplySorting>g__SetupRow|246_0", 0x015aa320, 0x311),
        ("StreamedListView.BindSortPathNextDepth", 0x015a4850, 0x156),
        ("StreamedListView.ProcessSortingDataChanged", 0x015a8cb0, 0x1FD),
        ("SpecificallyScoutedPersonReference.GetPropertiesInternal", 0x00696f80, 0x268),
        ("SpecificallyScoutedPersonReference.GetPropertyTypeInternal", 0x00697200, 0x164),
        ("ScoutPlayerPrioritiesReference.GetPropertiesInternal", 0x0067d360, 0x18A),
        ("ScoutPlayerPrioritiesReference.GetPropertyTypeInternal", 0x0067d500, 0x10F),
    ]:
        disasm_func(name, rva, sz)

    # Also find all methods on Type [6298..6305]
    for ti in range(6298, 6306):
        tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
        tname = get_mstr(tu[0])
        mstart = tu[9]
        mcnt = tu[16] & 0xFFFF
        print(f"\nType [{ti}] {tname} (methods={mcnt}):")
        for mi in range(mstart, mstart + mcnt):
            mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
            mname = get_mstr(mu[0])
            for rva, names in rva_to_method_name.items():
                if f"{tname}.{mname}" in names:
                    disasm_func(f"{tname}.{mname}", rva, 0x250)
