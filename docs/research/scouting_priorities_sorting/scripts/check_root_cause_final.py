import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from dump_headers_fast import dump_fast
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

# 1. Inspect factories in ui-tablefactories_assets_all.bundle
raw_f, trees_f, objs_f, ref_trees_f = parse_bundle_with_reftypes("ui-tablefactories_assets_all.bundle")
for oi, pid, abs_off, bsize, tid in objs_f:
    cid, nodes = trees_f[tid]
    if not nodes:
        continue
    chunk = raw_f[abs_off : abs_off + bsize]
    try:
        _, val = walk_tree(nodes, chunk, 0, 0)
    except Exception:
        continue
    if isinstance(val, dict):
        name = val.get("m_Name") or val.get("common_494") or ""
        if any(k in name.lower() for k in ("specificallyscouted", "scout", "person", "teamreport", "recommendation")):
            print(f"\n--- Factory Obj {oi} [PathID {pid}] ({nodes[0][2]}) {name} ---")
            print(f"  m_parameters: {val.get('m_parameters')}")
            rows = val.get("m_rowData", [])
            print(f"  m_rowData ({len(rows)} entries):")
            for r in rows[:15]:
                print(f"    col={r.get('m_column'):25s} sortBinding={r.get('m_sortBinding')!r:65s} plugin={r.get('m_sortBindingPlugin')} asc={r.get('m_sortAscending')}")

# 2. Disassemble key methods in StreamedListView, Bindings, and SpecificallyScoutedPersonReference
funcs = [
    ("StreamedListView_SortRows_015aab80", 0x015aab80, 0x350),
    ("StreamedListView_015a4040", 0x015a4040, 0x220),
    ("Bindings_Bind_inner_014beef0", 0x014beef0, 0x360),
    ("Bindings_Bind_dotted_014bf250", 0x014bf250, 0x350),
    ("SpecificallyScoutedPersonReference_00696ef0", 0x00696ef0, 0x490),
]
for name, rva, sz in funcs:
    dump_fast(name, rva, rva + sz)
