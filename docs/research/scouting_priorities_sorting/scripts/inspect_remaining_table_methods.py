import os
import json
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
import UnityPy

SCRATCH = r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch"
GAME_DIR = r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26"
DLL_PATH = os.path.join(GAME_DIR, "GameAssembly.dll")
BUNDLE_DIR = os.path.join(GAME_DIR, r"fm_Data\StreamingAssets\aa\StandaloneWindows64")

pe = pefile.PE(DLL_PATH, fast_load=True)
md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = False

# Load symbol map if available in scratch
sym_by_rva = {}
for fname in os.listdir(SCRATCH):
    if fname.endswith(".json"):
        print("Found json in scratch:", fname)

with open(DLL_PATH, "rb") as f:
    dll_bytes = f.read()

def rva_to_offset(rva):
    return pe.get_offset_from_rva(rva)

def disasm_func(name, rva, size, out_lines):
    out_lines.append(f"=== {name} (RVA 0x{rva:08x}, size={size}) ===")
    off = rva_to_offset(rva)
    code = dll_bytes[off:off+size]
    for insn in md.disasm(code, rva):
        out_lines.append(f"  0x{insn.address:08x}: {insn.mnemonic:<8} {insn.op_str}")
    out_lines.append("")

targets = [
    ("StreamedTable.SetList", 0x015ef610, 311),
    ("StreamedTable.TrySetColumnsAndSort", 0x015f0040, 494),
    ("StreamedTable.ApplyPersistedSortingState", 0x015e58c0, 229),
    ("StreamedTable.UpdateSortColum", 0x015f1380, 322),
    ("StreamedTable.SetNoSorting", 0x015ef750, 307),
    ("StreamedTable.TryFindSortedColumn", 0x015eff70, 204),
    ("StreamedTable.RefreshInternal", 0x015eed80, 450),
    ("StreamedTable.RebuildInternal", 0x015ee9c0, 259),
    ("StreamedTable.OnFactoryAssetLoaded", 0x015ec640, 713),
    ("StreamedTable.InitialiseColumns", 0x015ea870, 386),
    ("StreamedTable.CreateColumns", 0x015e83b0, 541),
    ("StreamedTable.UpdateStreamedTableView", 0x015f1650, 270),
    ("StreamedListView.BindToData", 0x015a49b0, 1786),
    ("StreamedListView.SetList", 0x015a9880, 324),
    ("StreamedListView.ResetIndices", 0x015a9420, 504),
    ("StreamedListView.Rebuild", 0x015a8eb0, 167),
    ("SpecificallyScoutedPersonReference.AcceptsPropertyInternal", 0x00696ef0, 128),
    ("SpecificallyScoutedPersonReference.GetInstance", 0x00696f70, 16),
    ("SpecificallyScoutedPersonReference.GetPropertiesInternal", 0x00696f80, 640),
    ("SpecificallyScoutedPersonReference.GetPropertyTypeInternal", 0x00697200, 128),
]

out = []
for name, rva, sz in targets:
    disasm_func(name, rva, sz, out)

with open(os.path.join(SCRATCH, "sorting_disasm18.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("Wrote sorting_disasm18.txt with", len(out), "lines")
