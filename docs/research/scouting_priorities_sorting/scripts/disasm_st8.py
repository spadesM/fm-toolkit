import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_sorting_details import dump_fast, pe, meta, hdr, str_off, str_sz, methods_off, methods_sz, types_off, types_sz, get_mstr

dump_fast("StreamedTable_015f14d0_015f1930", 0x015f14d0, 0x015f1930)
dump_fast("StreamedTableColumn_01610d00_01611500", 0x01610d00, 0x01611500)
dump_fast("StreamedTableView_01620000_01622200", 0x01620000, 0x01622200)

# Search types and methods for ScoutPriorities / SpecificallyScouted
ntypes = types_sz // 88
for ti in range(ntypes):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    tname = get_mstr(tu[0])
    tns = get_mstr(tu[1])
    full = f"{tns}.{tname}"
    if any(k in full.lower() for k in ["scoutpriorit", "specificallyscouted", "scoutedperson"]):
        mstart = tu[9]
        mcount = tu[16] & 0xFFFF
        print(f"=== Type {ti}: {full} (methods {mstart}..{mstart+mcount}) ===")
        for mi in range(mstart, mstart + mcount):
            mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
            mname = get_mstr(mu[0])
            print(f"  Method {mi}: {mname}")
