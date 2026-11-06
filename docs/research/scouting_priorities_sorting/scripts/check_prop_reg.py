import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, va_to_off, image_base, rva_to_end,
    rva_to_method_name, dump_func_details, root
)
from fm26save.binary_decompiler import unpack_unityfs_bundle

# 1. Dump PropertyRegistration.Initialise around 0x004683e1 (ScoutPlayerPriorities) and 0x0046b097 (SpecificallyScoutedPerson)
dump_func_details("PropertyRegistration.Initialise (ScoutPlayerPriorities @ 0x00468300)", 0x00468300, 0x280)
dump_func_details("PropertyRegistration.Initialise (SpecificallyScoutedPerson @ 0x0046b000)", 0x0046b000, 0x300)

# 2. Check ui-tileslayouts_assets_all.bundle for RecruitmentScoutPriorities
raw = unpack_unityfs_bundle(root / "fm_Data/StreamingAssets/aa/StandaloneWindows64/ui-tileslayouts_assets_all.bundle")
data_offset = struct.unpack_from(">Q", raw, 32)[0]
pos = 48
end = raw.find(b"\x00", pos)
pos = end + 1 + 5
type_count = struct.unpack_from("<i", raw, pos)[0]
pos += 4
for ti in range(type_count):
    class_id = struct.unpack_from("<i", raw, pos)[0]
    script_type_index = struct.unpack_from("<h", raw, pos + 5)[0]
    pos += 7
    if class_id == 114 or script_type_index >= 0:
        pos += 16
    pos += 16
    nn, ssz = struct.unpack_from("<II", raw, pos)
    pos += 8 + nn * 32 + ssz
    dep_cnt = struct.unpack_from("<i", raw, pos)[0]
    pos += 4 + dep_cnt * 4
obj_count = struct.unpack_from("<i", raw, pos)[0]
pos += 4
for i in range(obj_count):
    pos = (pos + 3) & ~3
    pid, bstart, bsize, tid = struct.unpack_from("<qQII", raw, pos)
    pos += 24
    chunk = raw[data_offset + bstart : data_offset + bstart + bsize]
    if b"ScoutPriorit" in chunk or pid == 7661162286614362349:
        print(f"\nFound in ui-tileslayouts Obj {i}: pid={pid} (0x{pid & ((1<<64)-1):016x}), size={bsize}")
        for p in range(0, len(chunk) - 4, 4):
            slen = struct.unpack_from("<I", chunk, p)[0]
            if 1 <= slen <= 120 and p + 4 + slen <= len(chunk):
                s = chunk[p + 4 : p + 4 + slen]
                pad = (4 - (slen % 4)) % 4
                if p + 4 + slen + pad <= len(chunk) and chunk[p + 4 + slen : p + 4 + slen + pad] == b"\x00" * pad:
                    if all(32 <= b < 127 for b in s):
                        print(f"  +0x{p:04x}: {s.decode('ascii')!r}")
                if p + 4 + slen + pad + 12 <= len(chunk):
                    # print PPtr if right after or nearby
                    pass
        # Also dump all PPtrs (fileID in 0..10, non-zero pathID)
        for p in range(0, len(chunk) - 12, 4):
            fid, fpid = struct.unpack_from("<iq", chunk, p)
            if 0 <= fid <= 10 and abs(fpid) > 1000000000000:
                print(f"  +0x{p:04x}: PPtr(fileID={fid}, pathID={fpid})")
