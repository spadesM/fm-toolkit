import struct, sys, json
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import decompile_gameassembly_bindings, decompile_global_metadata

meta_res = decompile_global_metadata(include_all_methods=True, filter_namespace_or_image="StreamedListView")
for t in meta_res["types"]:
    if t["name"] in ("StreamedListView", "StreamedTable"):
        print(f"=== {t['full_name']} ({t['image']}) ===")
        for i, f in enumerate(t["fields"]):
            print(f"  Field[{i}]: {f['name']}")

ga_res = decompile_gameassembly_bindings()
for k in ("SpecificallyScoutedPersonReference", "SpecificallyScoutedTeamReference", "ScoutPrioritiesReference", "PersonReference"):
    if k in ga_res["reference_classes"]:
        print(f"=== Reference Class: {k} ===")
        print(json.dumps(ga_res["reference_classes"][k], indent=2))
