import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from dump_headers_fast import dump_fast, meta, types_off, types_sz, methods_off, get_mstr

dump_fast("StreamedListView_015aaed0", 0x015aaed0, 0x015ab400)

# List all methods of StreamedListView and StreamedTable
for tidx in range(types_sz // 88):
    tu = struct.unpack_from("<22i", meta, types_off + tidx * 88)
    tname = get_mstr(tu[0])
    if tname in ("StreamedListView", "StreamedTable", "SpecificallyScoutedPerson", "SpecificallyScoutedPersonReference", "ScoutPriorities"):
        ns = get_mstr(tu[1])
        mstart, mcount = tu[7], tu[17] & 0xFFFF
        print(f"\n=== Type {ns}.{tname} (methods={mcount}) ===")
        for mi in range(mstart, mstart + mcount):
            mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
            mname = get_mstr(mu[0])
            print(f"  [{mi}] {mname}")
