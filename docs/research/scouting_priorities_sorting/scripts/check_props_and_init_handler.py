import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from dump_headers_fast import dump_fast, pe, image_base, va_to_off, get_usym_dict, root

# 1. Dump StreamedTable property getters/setters (0x015f2000..0x015f2950) and m_initialisationHandler call (0x015e7050..0x015e7300) and 0x015ed250..0x015ed400
dump_fast("StreamedTable_Props_015f2000_015f2600", 0x015f2000, 0x015f2600)
dump_fast("StreamedTable_InitHandler_015e7050_015e7300", 0x015e7050, 0x015e7300)
dump_fast("StreamedTable_1382_015ed250_015ed400", 0x015ed250, 0x015ed400)

# 2. Where are GUIDs f93b92def36a8474fa5798233a6a3fb8 and 446475dd53423864183c52075b8f0e32 in catalog.json?
# Remember in Unity Addressables catalog.json, m_InternalIds or m_KeyDataString (base64) stores GUIDs!
import base64, json
cat_path = root / "fm_Data/StreamingAssets/aa/catalog.json"
cat = json.loads(cat_path.read_text(encoding="utf-8"))
key_data = base64.b64decode(cat["m_KeyDataString"])
bucket_data = base64.b64decode(cat["m_BucketDataString"])
entry_data = base64.b64decode(cat["m_EntryDataString"])
internal_ids = cat["m_InternalIds"]

for guid in ("f93b92def36a8474fa5798233a6a3fb8", "446475dd53423864183c52075b8f0e32", "13a1f18bd93e860488c2cb84abb1168c", "c1a44f7eaa1698a43ab7664b7ce350da", "399c0aa9357f67847b91ba2fe4756083"):
    idx = key_data.find(guid.encode("ascii"))
    print(f"\nGUID {guid} in key_data: offset={idx}")
    if idx != -1:
        # Find which bucket has key_offset == idx - 5 (1 byte type + 4 byte len)
        target_koff = idx - 5
        num_buckets = struct.unpack_from("<I", bucket_data, 0)[0]
        bpos = 4
        for bi in range(num_buckets):
            koff, ecnt = struct.unpack_from("<II", bucket_data, bpos)
            entries = struct.unpack_from(f"<{ecnt}I", bucket_data, bpos + 8)
            bpos += 8 + ecnt * 4
            if koff == target_koff:
                for ei in entries:
                    # each entry in entry_data is 28 bytes (7 ints: internalId, providerIdx, depKeyIdx, depHash, dataIdx, primaryKey, resourceType)
                    eints = struct.unpack_from("<7i", entry_data, 4 + ei * 28)
                    iid = internal_ids[eints[0]] if 0 <= eints[0] < len(internal_ids) else str(eints[0])
                    pkey = eints[5]
                    pk_str = key_data[pkey+5 : pkey+5+struct.unpack_from("<I", key_data, pkey+1)[0]].decode("utf-8", errors="ignore") if 0 <= pkey < len(key_data) else ""
                    print(f"  -> Entry {ei}: internalId={iid}, primaryKey={pk_str!r}, eints={eints}")
