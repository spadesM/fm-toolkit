import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir, unpack_unityfs_bundle

root = resolve_fm_install_dir()
raw = unpack_unityfs_bundle(root / "fm_Data/StreamingAssets/aa/StandaloneWindows64/ui-recruitment_assets_all.bundle")

pos = 48
end = raw.find(b"\x00", pos)
pos = end + 1 + 5
type_count = struct.unpack_from("<i", raw, pos)[0]
pos += 4
for ti in range(type_count):
    class_id = struct.unpack_from("<i", raw, pos)[0]
    is_stripped = raw[pos + 4]
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
pos = (pos + 3) & ~3
data_offset = struct.unpack_from(">Q", raw, 32)[0]
objs = []
for oi in range(obj_count):
    path_id, byte_start, byte_size, type_id = struct.unpack_from("<qQIi", raw, pos)
    pos += 24
    abs_off = data_offset + byte_start
    name = ""
    for off_try in (abs_off + 28, abs_off):
        if off_try + 4 <= len(raw):
            nlen = struct.unpack_from("<I", raw, off_try)[0]
            if 0 < nlen < 128 and off_try + 4 + nlen <= len(raw):
                s = raw[off_try + 4 : off_try + 4 + nlen]
                if all(32 <= b < 127 for b in s):
                    name = s.decode("ascii")
                    break
    objs.append((oi, path_id, abs_off, byte_size, type_id, name))

needle = b"\x20\x00\x00\x00StreamedTable/UxmlSerializedData"
st_offs = []
p = 0
while True:
    idx = raw.find(needle, p)
    if idx < 0: break
    st_offs.append(idx)
    p = idx + len(needle)

for st_off in st_offs:
    for oi, path_id, abs_off, byte_size, type_id, name in objs:
        if abs_off <= st_off < abs_off + byte_size:
            print(f"ST at 0x{st_off:06x} ({st_off:7d}) -> Obj {oi:3d} '{name}' (PathID={path_id}, start=0x{abs_off:06x}, size={byte_size})")
            break

print("\nAll objects with 'Scout' or 'Priorit' in name:")
for oi, path_id, abs_off, byte_size, type_id, name in objs:
    if any(k in name.lower() for k in ['scout', 'priorit']):
        print(f"  Obj {oi:3d} '{name}' (PathID={path_id}, start=0x{abs_off:06x}, size={byte_size}, type={type_id})")
