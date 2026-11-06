import struct, sys, os
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import meta, types_off, types_sz, fields_off, get_mstr, root

targets = {5791, 5796, 5814, 6196, 6693, 23620, 23780, 27003, 37147, 48605}
for ti in range(types_sz // 88):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    if tu[5] in targets or tu[6] in targets:
        print(f"byval={tu[5]} -> TypeDef[{ti}] {get_mstr(tu[1])}.{get_mstr(tu[0])}")
        f_start = tu[8]
        f_cnt = tu[17] & 0xFFFF
        for i in range(f_cnt):
            fu = struct.unpack_from("<3i", meta, fields_off + (f_start + i) * 12)
            print(f"  Field[{i}]: {get_mstr(fu[0])} (type_idx={fu[1]})")

aa_dir = root / "fm_Data/StreamingAssets/aa"
for dirpath, dirnames, filenames in os.walk(aa_dir):
    for fn in filenames:
        if any(k in fn.lower() for k in ("catalog", "function", "visualscript", "table", "context")):
            print("File:", os.path.join(dirpath, fn))
