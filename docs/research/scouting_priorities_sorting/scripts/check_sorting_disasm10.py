import UnityPy
import struct
from dump_headers_fast import FastIl2CppDumper

out = []

# 1. Dump Obj 766 (ScoutPrioritiesTable) and Obj 791 (ScoutPrioritiesTable-Small) in ui-tableviews_assets_all.bundle
bundle_path = r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26\fm_Data\StreamingAssets\aa\StandaloneWindows64\ui-tableviews_assets_all.bundle"
env = UnityPy.load(bundle_path)
for obj in env.objects:
    if obj.path_id in (6820118260298404215, 7446456543218343850, -4578880645778034831, -1273320983569231142):
        tree = obj.read_typetree()
        out.append(f"=== PathID {obj.path_id}: {tree.get('m_Name')} ===")
        import json
        out.append(json.dumps(tree, indent=2))

# Also dump a working table view for comparison, e.g., Shortlist or PlayerDatabase or RecruitmentTeamReportPriorities
for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        try:
            tree = obj.read_typetree()
            name = tree.get("m_Name", "")
            if any(k in name for k in ("ScoutPriorities", "TeamReportPriorities", "PlayerDatabase", "Shortlist")):
                if "m_tableConfig" in tree:
                    out.append(f"=== TableView PathID {obj.path_id}: {name} ===")
                    out.append(json.dumps(tree, indent=2))
        except Exception:
            pass

# 2. Disassemble the remaining StreamedTable and Bindings methods
dumper = FastIl2CppDumper(
    r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26\GameAssembly.dll",
    r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26\fm_Data\il2cpp_data\Metadata\global-metadata.dat",
    r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26\fm_Data\il2cpp_data\Symbols\GameAssembly.usym"
)

target_methods = [
    ("StreamedTable.Method_015f1760 (cs:2333)", 0x015f1760),
    ("StreamedTable.Method_015ef1e0 (cs:2377)", 0x015ef1e0),
    ("StreamedTable.Method_015e9f40 (cs:3324)", 0x015e9f40),
    ("StreamedTable.Method_015eead0 (cs:1952)", 0x015eead0),
    ("StreamedTable.Method_015e9220 (cs:1930)", 0x015e9220),
    ("StreamedTable.Method_015f0f50 (cs:1922)", 0x015f0f50),
    ("StreamedListView.Method_015a9ee0 (cs:1911)", 0x015a9ee0),
    ("StreamedListView.Method_015aab80 (cs:705)", 0x015aab80),
    ("Bindings.GetNthProperty (0x014c1450)", 0x014c1450),
    ("Bindings.RemoveFirstProperty (0x014c1a60)", 0x014c1a60),
    ("Bindings.CreateScope (0x014bf980)", 0x014bf980),
    ("Bindings.OpenChannel (0x014c3050)", 0x014c3050),
]

for label, rva in target_methods:
    out.append(dumper.disasm_function(rva, label, max_size=1200))

with open(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\sorting_disasm10.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("Wrote sorting_disasm10.txt")
