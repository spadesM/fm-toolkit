import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

DLL_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26\GameAssembly.dll"
META_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26\fm_Data\il2cpp_data\Metadata\global-metadata.dat"

with open(DLL_PATH, "rb") as f:
    dll_bytes = f.read()

pe_off = struct.unpack_from("<I", dll_bytes, 0x3C)[0]
num_sec = struct.unpack_from("<H", dll_bytes, pe_off + 6)[0]
opt_sz = struct.unpack_from("<H", dll_bytes, pe_off + 20)[0]
sec_off = pe_off + 24 + opt_sz
sections = []
for i in range(num_sec):
    s = sec_off + i * 40
    vsize, va, rsize, rptr = struct.unpack_from("<4I", dll_bytes, s + 8)
    sections.append((va, vsize, rptr, rsize))

def rva_to_off(rva):
    for va, vsize, rptr, rsize in sections:
        if va <= rva < va + max(vsize, rsize):
            return rptr + (rva - va)
    return None

# Also build a quick RVA -> method name lookup from previous output or metadata if possible
# Let's load RVAs from our known outputs or build a quick symbol map from metadata
with open(META_PATH, "rb") as f:
    meta = f.read()

header_fields = struct.unpack_from("<4I", meta, 0)
string_off, string_size = struct.unpack_from("<2I", meta, 0x18)
methods_off, methods_size = struct.unpack_from("<2I", meta, 0x30)
typedefs_off, typedefs_size = struct.unpack_from("<2I", meta, 0xA0)
images_off, images_size = struct.unpack_from("<2I", meta, 0xA8)

def get_str(idx):
    end = meta.find(b"\x00", string_off + idx)
    return meta[string_off + idx:end].decode("utf-8", errors="replace")

# Let's map known RVAs from our previous scripts
known_rvas = {
    0x015efce0: "StreamedTable.SetSorting(col, dir, shouldSort)",
    0x015ec910: "StreamedTable.OnHeaderClicked",
    0x015eac30: "StreamedTable.MakeColumnHeader",
    0x015f0040: "StreamedTable.TrySetColumnsAndSort",
    0x015a4260: "StreamedListView.ApplySorting",
    0x015aa320: "StreamedListView.<ApplySorting>g__SetupRow|246_0",
    0x015a4850: "StreamedListView.BindSortPathNextDepth",
    0x015a7ff0: "StreamedListView.OnSortingDataChanged",
    0x015a8cb0: "StreamedListView.ProcessSortingDataChanged",
    0x015a8610: "StreamedListView.PostSortingDataChanged",
    0x015a9dd0: "StreamedListView.TryOrderRows",
    0x015a6080: "StreamedListView.FinalizeRowOrdering",
    0x015a3b00: "SortComparer..ctor",
    0x015a3c60: "SortComparer.Compare(x, y)",
    0x015a3d30: "SortComparer.Compare(a, b, dir, col)",
    0x015a3ec0: "SortData..ctor",
    0x015a3ff0: "SortData.GetData",
    0x015a4040: "SortData.HasReceived",
    0x015a40f0: "SortData.SetData",
    0x015a41e0: "SortData.SetExpected",
    0x015ed7f0: "Header..ctor",
    0x015ef290: "Header.SetDirection",
    0x014c1450: "Bindings.GetNthProperty",
    0x014c1310: "Bindings.GetDepth",
    0x014bee30: "Bindings.Bind",
    0x014c0050: "Bindings.CreateUniqueChild",
    0x014c3ae0: "Bindings.SetAlias",
    0x014c3360: "Bindings.Set",
    0x0044b6d0: "il2cpp_codegen_initialize_runtime_metadata",
}

md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

def disasm_func(name, start_rva, size=0x450):
    print("=" * 80)
    print(f"FUNCTION: {name} @ RVA 0x{start_rva:08x}")
    print("=" * 80)
    off = rva_to_off(start_rva)
    code = dll_bytes[off:off+size]
    for insn in md.disasm(code, start_rva):
        comment = ""
        if insn.mnemonic in ("call", "jmp") and insn.op_str.startswith("0x"):
            target = int(insn.op_str, 16)
            if target in known_rvas:
                comment = f" ; -> {known_rvas[target]}"
        elif "[rip +" in insn.op_str or "[rip -" in insn.op_str:
            # calculate RIP target
            for op in insn.operands:
                if op.type == 3 and op.mem.base == 41: # X86_REG_RIP
                    rip_target = insn.address + insn.size + op.mem.disp
                    comment = f" ; [RIP -> 0x{rip_target:08x}]"
        print(f"  0x{insn.address:08x} (+0x{insn.address - start_rva:03x}): {insn.mnemonic:8s} {insn.op_str:35s}{comment}")
        # stop at int3 padding after ret
        if insn.mnemonic == "int3":
            break

funcs = [
    ("Bindings.GetDepth", 0x014c1310, 0x140),
    ("Bindings.GetNthProperty", 0x014c1450, 0x160),
    ("StreamedListView.<ApplySorting>g__SetupRow|246_0", 0x015aa320, 0x260),
    ("StreamedListView.BindSortPathNextDepth", 0x015a4850, 0x220),
    ("StreamedListView.ProcessSortingDataChanged", 0x015a8cb0, 0x260),
    ("StreamedListView.PostSortingDataChanged", 0x015a8610, 0x200),
    ("StreamedListView.TryOrderRows", 0x015a9dd0, 0x180),
    ("StreamedListView.FinalizeRowOrdering", 0x015a6080, 0x220),
    ("SortData.SetExpected", 0x015a41e0, 0x80),
    ("SortData.SetData", 0x015a40f0, 0x100),
    ("SortData.HasReceived", 0x015a4040, 0xb0),
    ("SortComparer.Compare(x,y)", 0x015a3c60, 0xd0),
    ("SortComparer.Compare(a,b,dir,col)", 0x015a3d30, 0x190),
    ("Header..ctor", 0x015ed7f0, 0x450),
    ("StreamedTable.MakeColumnHeader", 0x015eac30, 0x350),
    ("StreamedTable.TrySetColumnsAndSort", 0x015f0040, 0x350),
]

for name, rva, sz in funcs:
    disasm_func(name, rva, sz)
