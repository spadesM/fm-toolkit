import struct, sys

sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
out_path = r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\sorting_chain_details_utf8.txt"
out_file = open(out_path, "w", encoding="utf-8")
sys.stdout = out_file

from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)

method_to_rvas = {}
for rva, nms in rva_to_method_name.items():
    for nm in nms:
        method_to_rvas.setdefault(nm, []).append(rva)

hdr = struct.unpack_from("<80I", meta, 0)
types_sz = hdr[41]
num_types = types_sz // 88

print("=== 1. Check Type 785 and other Reference / SortComparer / Header / StreamedListView types ===")
for ti in range(num_types):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    tns = get_mstr(tu[1])
    if ti == 785 or tname in ("Header", "SortComparer", "StreamedListView", "VirtualisedList", "StreamedTable") or "SortComparer" in tname or ("Header" in tname and "Bindable" in tns):
        m_start = tu[9]
        m_cnt = tu[16] & 0xFFFF
        f_start = tu[8]
        f_cnt = tu[17] & 0xFFFF
        print(f"\nType {ti}: {tns}.{tname} (fields={f_cnt}, methods={m_cnt})")
        for fi in range(f_start, f_start + f_cnt):
            fu = struct.unpack_from("<3i", meta, fields_off + fi * 12)
            fname = get_mstr(fu[0])
            print(f"  Field {fi - f_start}: {fname}")
        for mi in range(m_start, m_start + m_cnt):
            mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
            mname = get_mstr(mu[0])
            rvas = method_to_rvas.get(f"{tname}.{mname}", [])
            print(f"  Method {mi - m_start}: {mname} RVAs={[hex(r) for r in rvas]}")

print("\n=== 2. Find all lambdas / display classes of StreamedTable and Header ===")
for nm, rvas in sorted(method_to_rvas.items()):
    if "MakeColumnHeader" in nm or "SortComparer" in nm or (nm.startswith("Header.") and any(r > 0x1500000 and r < 0x1650000 for r in rvas)):
        for r in rvas:
            if 0x1400000 <= r <= 0x1700000:
                sz = min(rva_to_end.get(r, r + 512) - r, 1024)
                dump_func_details(nm, r, sz)

print("\n=== 3. Dump StreamedListView sorting & state change & reorderable methods ===")
slv_methods = [
    "StreamedListView.SetSortingBinding",
    "StreamedListView.BeginStateChange",
    "StreamedListView.EndStateChange",
    "StreamedListView.Sort",
    "StreamedListView.SetupRow",
    "StreamedListView.get_Reorderable",
    "StreamedListView.set_Reorderable",
    "StreamedListView.RebuildInternal",
    "StreamedListView.RefreshInternal",
    "StreamedListView.SetList",
    "StreamedListView.OnEnable",
]
for nm in slv_methods:
    for r in method_to_rvas.get(nm, []):
        sz = min(rva_to_end.get(r, r + 512) - r, 1500)
        dump_func_details(nm, r, sz)

print("\n=== 4. Dump SpecificallyScoutedPersonReference & Type 785 & PersonReference property methods ===")
ref_dumps = [
    ("SpecificallyScoutedPersonReference.AcceptsPropertyInternal", 0x00696ef0),
    ("SpecificallyScoutedPersonReference.GetPropertyTypeInternal", 0x00697200),
    ("SpecificallyScoutedPersonReference.GetPropertiesInternal", 0x00696f80),
]
# Add Type 785 methods
tu785 = struct.unpack_from("<22i", meta, types_off + 785 * 88)
tname785 = get_mstr(tu785[0])
m_start785 = tu785[9]
m_cnt785 = tu785[16] & 0xFFFF
for mi in range(m_start785, m_start785 + m_cnt785):
    mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
    mname = get_mstr(mu[0])
    if "Property" in mname or "Properties" in mname:
        for r in method_to_rvas.get(f"{tname785}.{mname}", []):
            ref_dumps.append((f"{tname785}.{mname}", r))

for label, rva in ref_dumps:
    sz = min(rva_to_end.get(rva, rva + 512) - rva, 2000)
    dump_func_details(label, rva, sz)

out_file.close()
