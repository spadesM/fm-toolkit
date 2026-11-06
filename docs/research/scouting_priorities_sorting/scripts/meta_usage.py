import struct, sys
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import pe, meta, sections, va_to_off, image_base, types_off, get_mstr

hdr = struct.unpack_from("<64I", meta, 0)
str_lit_off, str_lit_sz = hdr[2], hdr[3]
str_lit_data_off = hdr[4]
types_sz = hdr[41]
n_typedefs = types_sz // 88

def literal(i):
    ln, di = struct.unpack_from("<II", meta, str_lit_off + i * 8)
    return meta[str_lit_data_off + di: str_lit_data_off + di + ln].decode("utf-8", "replace")

_reg = None
def find_metadata_registration():
    global _reg
    if _reg: return _reg
    for name, vaddr, vsize, raddr, rsize in sections:
        if name not in (".data", ".rdata"): continue
        blob = pe[raddr:raddr+rsize]
        pat = struct.pack("<Q", n_typedefs)
        pos = 0
        while True:
            i = blob.find(pat, pos)
            if i < 0: break
            pos = i + 8
            if i % 8: continue
            # check fieldOffsetsCount at [10], typeDefinitionsSizesCount at [12] -> i is either
            try:
                q = struct.unpack_from("<16Q", blob, i - 10*8)
            except struct.error:
                continue
            if q[10] == n_typedefs and q[12] == n_typedefs and 1000 < q[6] < 10_000_000:
                _reg = dict(typesCount=q[6], types=q[7], at=image_base + vaddr + i - 80)
                return _reg
    raise RuntimeError("not found")

def il2cpp_type(idx):
    reg = find_metadata_registration()
    ptr = struct.unpack_from("<Q", pe, va_to_off(reg["types"] + idx * 8))[0]
    o = va_to_off(ptr)
    data, bits = struct.unpack_from("<QI", pe, o)
    t = (bits >> 16) & 0xFF
    return data, t

def type_name(idx):
    data, t = il2cpp_type(idx)
    if t in (0x11, 0x12) and 0 <= data < n_typedefs:
        tu = struct.unpack_from("<22i", meta, types_off + data * 88)
        return f"{get_mstr(tu[1])}.{get_mstr(tu[0])} (typedef {data}, kind {hex(t)})"
    return f"<il2cpp type kind {hex(t)} data {hex(data)}>"

def resolve_slot_value(v):
    kind = (v >> 29) & 7
    idx = (v & 0x1FFFFFFF) >> 1
    if kind == 5: return f"string {literal(idx)!r}"
    if kind in (1, 2): return f"{'TypeInfo' if kind==1 else 'Il2CppType'} {type_name(idx)}"
    return f"kind {kind} idx {idx}"

def resolve_rip_operand(ins_rva, ins_len=7):
    o = va_to_off(image_base + ins_rva)
    disp = struct.unpack_from("<i", pe, o + ins_len - 4)[0]
    slot = image_base + ins_rva + ins_len + disp
    so = va_to_off(slot)
    if so < 0: return f"slot {hex(slot - image_base)} (bss)"
    v = struct.unpack_from("<Q", pe, so)[0]
    return f"slot {hex(slot - image_base)}: " + resolve_slot_value(v)

if __name__ == "__main__":
    print(find_metadata_registration())
    for r in (0x15a8e04, 0x15a8d8a, 0x15a4520, 0x15a44ed, 0x15efe39):
        print(hex(r), resolve_rip_operand(r))
