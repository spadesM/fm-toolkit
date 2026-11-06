import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as dhf
from fm26save.binary_decompiler import decompile_global_metadata

meta_res = decompile_global_metadata(include_all_methods=True)
for t in meta_res["types"]:
    if any(k in t["full_name"] for k in ("ScoutPriorit", "ScoutPlayerPriorit", "SpecificallyScouted", "PrioritiseFuture")):
        print(f"Type: {t['full_name']} ({t['image']}) methods={[m['name'] for m in t['methods']]} fields={[f['name'] for f in t['fields']]}")
    else:
        for m in t["methods"]:
            if any(k in m["name"] for k in ("ScoutPriorit", "SpecificallyScouted")):
                print(f"Method: {t['full_name']}.{m['name']} ({t['image']})")

dhf.dump_fast("StreamedListView.BindElement", 0x015a43e0, 0x015a4850)
dhf.dump_fast("StreamedListView.SetSourceData", 0x015aa000, 0x015aa320)
dhf.dump_fast("StreamedListView.ResetSorting", 0x015a8e40, 0x015a9090)
dhf.dump_fast("StreamedListView.GetOrCreateElementForIndex", 0x015a5da0, 0x015a6080)
