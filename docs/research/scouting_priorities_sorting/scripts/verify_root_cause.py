import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree
import dump_headers_fast as dhf

print("=== 1. ScoutPrioritiesTable & Related TableViews in ui-tableviews_assets_all.bundle ===")
raw_v, trees_v, objs_v, _ = parse_bundle_with_reftypes("ui-tableviews_assets_all.bundle")
for oi in (236, 400, 766, 791, 729):
    _, pid, abs_off, bsize, tid = objs_v[oi]
    _, nodes = trees_v[tid]
    chunk = raw_v[abs_off : abs_off + bsize]
    _, val = walk_tree(nodes, chunk, 0, 0)
    print(f"\n--- TableView Obj {oi} (pid={pid}) ---")
    for k, v in val.items():
        if k != "m_tableConfig":
            print(f"  {k}: {v}")
        else:
            print(f"  m_tableConfig ({len(v)} cols):")
            for col in v:
                print(f"    {col}")

print("\n=== 2. SpecificallyScoutedPersonTableFactory (Obj 92) vs PrioritiseFutureTransferItemTableFactory (Obj 118) ===")
raw_f, trees_f, objs_f, _ = parse_bundle_with_reftypes("ui-tablefactories_assets_all.bundle")
for oi in (92, 118):
    _, pid, abs_off, bsize, tid = objs_f[oi]
    _, nodes = trees_f[tid]
    chunk = raw_f[abs_off : abs_off + bsize]
    _, val = walk_tree(nodes, chunk, 0, 0)
    print(f"\n--- Factory Obj {oi} (pid={pid}) ---")
    for k, v in val.items():
        if k != "m_rowData":
            print(f"  {k}: {v}")
        else:
            print(f"  m_rowData ({len(v)} cols):")
            for r in v:
                print(f"    {r}")

print("\n=== 3. Disassemble Key StreamedTable & StreamedListView Methods ===")
targets = [
    ("StreamedTable.InitialiseColumns", 0x015ea870, 0x015eac30),
    ("StreamedTable.RecreateHeaders", 0x015eecb0, 0x015ef000),
    ("StreamedTable.TrySetColumns", 0x015f0d10, 0x015f1100),
    ("StreamedTable.SetList", 0x015ef610, 0x015ef900),
    ("StreamedListView.SetList", 0x015a9880, 0x015a9ae0),
    ("StreamedListView.ProcessStateChanges", 0x015a8b60, 0x015a8cb0),
    ("StreamedListView.BindToDataInternal", 0x015a49b0, 0x015a4d50),
    ("StreamedListView.UxmlSerializedData.Deserialize", 0x015ad530, 0x015ad750),
    ("StreamedTable.UxmlSerializedData.Deserialize", 0x015f36b0, 0x015f3900),
    ("Bindings.GetProperty", 0x014bf980, 0x014bfd00),
    ("Bindings.GetNthProperty", 0x014c1450, 0x014c1600),
    ("Bindings.BindProperty", 0x014bee30, 0x014bf150),
]

for name, s, e in targets:
    dhf.dump_fast(name, s, e)
