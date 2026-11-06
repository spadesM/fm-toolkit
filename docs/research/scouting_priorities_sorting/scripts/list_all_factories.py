import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir, unpack_unityfs_bundle

root = resolve_fm_install_dir()
tf_raw = unpack_unityfs_bundle(root / "fm_Data/StreamingAssets/aa/StandaloneWindows64/ui-tablefactories_assets_all.bundle")

# Find all StreamedTableFactory names in tf_raw
pos = 48
end = tf_raw.find(b"\x00", pos)
pos = end + 1 + 5
type_count = struct.unpack_from("<i", tf_raw, pos)[0]
pos += 4
for ti in range(type_count):
    class_id = struct.unpack_from("<i", tf_raw, pos)[0]
    is_stripped = tf_raw[pos + 4]
    script_type_index = struct.unpack_from("<h", tf_raw, pos + 5)[0]
    pos += 7
    if class_id == 114 or script_type_index >= 0:
        pos += 16
    pos += 16
    nn, ssz = struct.unpack_from("<II", tf_raw, pos)
    pos += 8 + nn * 32 + ssz
    dep_cnt = struct.unpack_from("<i", tf_raw, pos)[0]
    pos += 4 + dep_cnt * 4

# In SerializedFile v22, after types: bigIdEnabled(4)? No, in v22 bigIdEnabled is 0, then object_count(4), align 4, then object info table!
obj_count = struct.unpack_from("<i", tf_raw, pos)[0]
pos += 4
pos = (pos + 3) & ~3
print(f"tf_raw object count: {obj_count}")
data_offset = struct.unpack_from(">Q", tf_raw, 32)[0]
for oi in range(obj_count):
    path_id, byte_start, byte_size, type_id = struct.unpack_from("<qQIi", tf_raw, pos)
    pos += 24
    abs_off = data_offset + byte_start
    # If MonoBehaviour (type_id == 0), read m_Name at abs_off + 28
    if type_id == 0:
        nlen = struct.unpack_from("<I", tf_raw, abs_off + 28)[0]
        name = tf_raw[abs_off + 32 : abs_off + 32 + nlen].decode("utf-8", errors="replace")
        print(f"  Obj {oi:2d}: PathID={path_id:20d} off={abs_off:7d} size={byte_size:6d} name={name}")
