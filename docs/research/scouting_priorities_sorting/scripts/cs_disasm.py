import struct, sys, bisect
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import pe, va_to_off, image_base, rva_to_end, rva_to_method_name
import capstone

_md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
_sorted = sorted(rva_to_method_name.keys())

def name_of(rva):
    n = rva_to_method_name.get(rva)
    return ", ".join(n[:3]) if n else ""

def find_rva(name_sub, exact=False):
    res = []
    for r in _sorted:
        for n in rva_to_method_name[r]:
            if (n == name_sub) if exact else (name_sub in n):
                res.append((r, n))
    return res

def disasm(rva, sz=None, label=None, out=sys.stdout):
    if sz is None:
        sz = rva_to_end.get(rva, rva + 0x200) - rva
    off = va_to_off(image_base + rva)
    code = pe[off:off+sz]
    print(f"\n======== {label or name_of(rva)} @ {hex(rva)} size={sz} ========", file=out)
    for ins in _md.disasm(code, rva):
        extra = ""
        if ins.mnemonic in ("call", "jmp") and ins.op_str.startswith("0x"):
            t = int(ins.op_str, 16)
            nm = name_of(t)
            if nm: extra = f"   ; {nm}"
        elif "rip +" in ins.op_str or "rip -" in ins.op_str:
            pass
        print(f"  {ins.address:08x}: {ins.mnemonic:6s} {ins.op_str}{extra}", file=out)
