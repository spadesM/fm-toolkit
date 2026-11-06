import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir

root = resolve_fm_install_dir()
pe = (root / "GameAssembly.dll").read_bytes()
meta = (root / "fm_Data/il2cpp_data/Metadata/global-metadata.dat").read_bytes()

hdr = struct.unpack_from("<64I", meta, 0)
str_off, str_sz = hdr[6], hdr[7]
methods_off, methods_sz = hdr[12], hdr[13]
types_off, types_sz = hdr[40], hdr[41]
images_off, images_sz = hdr[42], hdr[43]

def get_mstr(off: int) -> str:
    if off < 0 or off >= str_sz:
        return ""
    end = meta.find(b"\x00", str_off + off)
    return meta[str_off + off : end].decode("utf-8", errors="replace")

e_lfanew = struct.unpack_from("<I", pe, 0x3C)[0]
num_sec = struct.unpack_from("<H", pe, e_lfanew + 6)[0]
opt_size = struct.unpack_from("<H", pe, e_lfanew + 20)[0]
image_base = struct.unpack_from("<Q", pe, e_lfanew + 24 + 24)[0]
sec_off = e_lfanew + 24 + opt_size
sections = []
for i in range(num_sec):
    s = pe[sec_off + i * 40 : sec_off + (i + 1) * 40]
    name = s[:8].rstrip(b"\x00").decode("ascii", errors="replace")
    vsize, vaddr, rsize, raddr = struct.unpack_from("<IIII", s, 8)
    sections.append((name, vaddr, vsize, raddr, rsize))

def va_to_off(va: int) -> int:
    rva = va - image_base
    for _, vaddr, vsize, raddr, rsize in sections:
        if vaddr <= rva < vaddr + max(vsize, rsize):
            off = raddr + (rva - vaddr)
            return off if off < raddr + rsize else -2
    return -1

# Let's check SortComparer and SortData methods in SI.Bindable.dll (around TypeIndex 5788..5791)
for ti in range(5785, 5795):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    m_start = tu[9]
    m_cnt = tu[16] & 0xFFFF
    print(f"Type {ti}: {tname} (methods={m_cnt})")
    for mi in range(m_start, m_start + m_cnt):
        mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
        mname = get_mstr(mu[0])
        print(f"  Method {mi}: {mname}")

# Let's also check what is at [rip + disp] in ProcessSortingDataChanged (0x015a8cb0)
# Specifically:
# +0x14c: 48 8b 0d bf 2a a9 01 -> target RVA = 0x015a8cb0 + 0x153 + 0x01a92abf = 0x0303b8c2
# +0x156: 48 8b 1d 9d e0 85 01 -> target RVA = 0x015a8cb0 + 0x15d + 0x0185e09d = 0x02e06eaa
# Let's check where Il2CppMetadataRegistration.metadataUsages points in GameAssembly.dll!

# Also print full rowData (including m_valueBindings and m_uxmlRef) of SpecificallyScoutedPersonTableFactory!
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from compare_factories import walk_tree, tf_nodes, tf_raw
_, obj = walk_tree(tf_nodes, tf_raw, 461792)
print("\n=== Full SpecificallyScoutedPersonTableFactory rows ===")
for rd in obj["m_rowData"]:
    print(f"Row {rd['m_id']!r}:")
    print(f"  sortBinding={rd['m_sortBinding']['m_path']!r}, plugin={rd['m_sortBindingPlugin']}, asc={rd['m_sortAscending']}")
    print(f"  valueBindings={rd['m_valueBindings']}")
    print(f"  uxmlRef={rd['m_uxmlRef']}")
