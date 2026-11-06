import struct, sys
sys.stdout.reconfigure(encoding="utf-8")

meta_path = r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26\fm_Data\il2cpp_data\Metadata\global-metadata.dat"
with open(meta_path, "rb") as f:
    meta = f.read()

hdr = struct.unpack_from("<64I", meta, 0)
stringOffset = hdr[6]
fieldsOffset = hdr[24]
fieldsSize = hdr[25]
typeDefinitionsOffset = hdr[40]
typeDefinitionsSize = hdr[41]

def get_str(idx):
    end = meta.find(b"\x00", stringOffset + idx)
    return meta[stringOffset + idx : end].decode("utf-8", errors="replace")

num_tds = typeDefinitionsSize // 88
for ti in range(num_tds):
    off = typeDefinitionsOffset + ti * 88
    tu = struct.unpack_from("<22i", meta, off)
    name = get_str(tu[0])
    ns = get_str(tu[1])
    if name in ("StreamedTable", "StreamedListView", "UxmlSerializedData", "Header", "SpecificallyScoutedPersonReference"):
        first_field = tu[8]
        # Let's check both shorts of tu[16], tu[17], tu[18]
        s16_lo, s16_hi, s17_lo, s17_hi, s18_lo, s18_hi = struct.unpack_from("<6H", meta, off + 64)
        if name == "UxmlSerializedData" and s17_lo < 25:
            continue
        print(f"\n=== TypeDef #{ti}: {ns}.{name} (first_field={first_field}, s16=({s16_lo},{s16_hi}), s17=({s17_lo},{s17_hi})) ===")
        if first_field >= 0 and s17_lo > 0:
            for fi in range(first_field, first_field + s17_lo):
                foff = fieldsOffset + fi * 12
                fn_idx, ftype_idx, ftok = struct.unpack_from("<IiI", meta, foff)
                print(f"  [{fi - first_field:3d}] {get_str(fn_idx)} (typeIdx={ftype_idx})")
