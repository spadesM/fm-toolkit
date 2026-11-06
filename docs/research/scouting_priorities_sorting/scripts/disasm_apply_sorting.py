import struct
import capstone

pe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26\GameAssembly.dll"
with open(pe_path, "rb") as f:
    pe_bytes = f.read()

e_lfanew = struct.unpack_from("<I", pe_bytes, 0x3C)[0]
num_sections = struct.unpack_from("<H", pe_bytes, e_lfanew + 6)[0]
opt_hdr_size = struct.unpack_from("<H", pe_bytes, e_lfanew + 20)[0]
sec_off = e_lfanew + 24 + opt_hdr_size
sections = []
for i in range(num_sections):
    s = sec_off + i * 40
    name = pe_bytes[s:s+8].rstrip(b"\x00").decode("ascii", errors="ignore")
    vsize, va, rsize, rptr = struct.unpack_from("<IIII", pe_bytes, s + 8)
    sections.append((name, va, vsize, rptr, rsize))

def rva_to_off(rva):
    for name, va, vsize, rptr, rsize in sections:
        if va <= rva < va + max(vsize, rsize):
            return rptr + (rva - va)
    return None

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

funcs = [
    ("StreamedListView.ApplySorting", 0x015a4260, 1208),
    ("StreamedListView.<ApplySorting>g__SetupRow|246_0", 0x015aa320, 785),
    ("StreamedListView.BindSortPathNextDepth", 0x015a4850, 342),
    ("StreamedListView.OnSortingDataChanged", 0x015a7ff0, 281),
    ("StreamedListView.ProcessSortingDataChanged", 0x015a8cb0, 509),
    ("SortData.HasReceived", 0x015a4040, 200),
    ("Bindings.RemoveFirstProperty_014c1a60", 0x014c1a60, 250),
    ("Bindings.GetNthProperty_014c1450", 0x014c1450, 350),
    ("Bindings.BindProperty_014bee30", 0x014bee30, 200),
    ("Bindings.CreateScope_014bf980", 0x014bf980, 300),
    ("StringExtensions_016545b0", 0x016545b0, 200),
]

out = []
for name, rva, sz in funcs:
    out.append(f"=== {name} (0x{rva:08x}, sz={sz}) ===")
    off = rva_to_off(rva)
    code = pe_bytes[off:off+sz]
    for insn in md.disasm(code, rva):
        out.append(f"  +0x{insn.address - rva:03x} (0x{insn.address:08x}): {insn.mnemonic:8s} {insn.op_str}")
    out.append("")

# Also dump ScoutPrioritiesTable (Obj 766) in ui-tableviews_assets_all.bundle
import UnityPy
bundle_path = r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26\fm_Data\StreamingAssets\aa\StandaloneWindows64\ui-tableviews_assets_all.bundle"
env = UnityPy.load(bundle_path)
for obj in env.objects:
    if obj.path_id in (6820118260298404215, 7446456543218343850):
        tt = obj.read_typetree()
        out.append(f"=== TableView path_id={obj.path_id} ({tt.get('m_Name')}) ===")
        out.append(repr(tt))
        out.append("")

with open(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\disasm_apply_sorting.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("Done")
