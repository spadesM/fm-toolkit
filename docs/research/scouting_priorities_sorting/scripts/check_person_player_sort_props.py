import struct, sys

sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
out_path = r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\person_player_sort_props_utf8.txt"
out_file = open(out_path, "w", encoding="utf-8")
sys.stdout = out_file

from check_deep_sorting import (
    pe, meta, sections, images_off, images_sz, types_off, fields_off, methods_off,
    get_mstr, modules, va_to_off, off_to_va, image_base, rva_to_end,
    rva_to_method_name, dump_func_details
)

# Pre-index method_name -> list of RVAs in O(N)
method_to_rvas = {}
for rva, nms in rva_to_method_name.items():
    for nm in nms:
        method_to_rvas.setdefault(nm, []).append(rva)

hdr = struct.unpack_from("<80I", meta, 0)
types_sz = hdr[41]
num_types = types_sz // 88

target_types = (
    "BindingProperty", "BindingPath", "Bindings",
    "PersonReference", "PlayerReference", "SpecificallyScoutedPersonReference",
    "TeamReference", "DivisionReference", "TransferValueRangeReference",
    "ClubRecruitmentReportReference", "OverallReportGradeInfoReference"
)

for ti in range(num_types):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    tns = get_mstr(tu[1])
    if tname in target_types or "RecruitmentReport" in tname or "ScoutPriorit" in tname or "TransferValue" in tname:
        m_start = tu[9]
        m_cnt = tu[16] & 0xFFFF
        print(f"\nType {ti}: {tns}.{tname} (methods={m_cnt})")
        for mi in range(m_start, m_start + m_cnt):
            mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
            mname = get_mstr(mu[0])
            rvas = method_to_rvas.get(f"{tname}.{mname}", [])
            print(f"  Method {mi - m_start}: {mname} RVAs={[hex(r) for r in rvas]}")

# Dump BindingProperty methods
for nm, rvas in sorted(method_to_rvas.items()):
    if nm.startswith("BindingProperty.") or nm.startswith("BindingPath."):
        for r in rvas:
            sz = min(rva_to_end.get(r, r + 256) - r, 512)
            dump_func_details(nm, r, sz)

out_file.close()
