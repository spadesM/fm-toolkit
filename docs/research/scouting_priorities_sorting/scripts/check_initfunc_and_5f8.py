import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from dump_headers_fast import (
    dump_fast, pe, meta, hdr, str_lit_off, str_lit_sz, str_lit_data_off, str_lit_data_sz,
    str_off, str_sz, methods_off, methods_sz, types_off, types_sz, get_mstr, get_lit,
    image_base, sections, va_to_off, resolve_rip, get_usym_dict, root
)

# 1. Search for 0x5f8 (f8 05 00 00) in StreamedListView (RVA 0x015a3000..0x015b2000)
s_off = va_to_off(image_base + 0x015a3000)
e_off = va_to_off(image_base + 0x015b2000)
chunk = pe[s_off:e_off]
pos = 0
print("=== References to +0x5f8 in StreamedListView ===")
while True:
    idx = chunk.find(b"\xf8\x05\x00\x00", pos)
    if idx == -1:
        break
    rva = 0x015a3000 + idx
    umap = get_usym_dict(rva - 16, 32)
    uinfo = []
    for k in sorted(umap):
        uinfo.extend(umap[k])
    print(f"  RVA 0x{rva:08x}: bytes={chunk[idx-4:idx+8].hex(' ')} | USYM={uinfo[:3]}")
    pos = idx + 1

# 2. Search for 0x5c0 (c0 05 00 00 = Reorderable in VirtualisedList) across SI.Bindable & SI.UI (0x014b0000..0x016d0000)
s_off2 = va_to_off(image_base + 0x014b0000)
e_off2 = va_to_off(image_base + 0x016d0000)
chunk2 = pe[s_off2:e_off2]
pos = 0
print("\n=== References to +0x5c0 (Reorderable) in SI.Bindable / SI.UI ===")
while True:
    idx = chunk2.find(b"\xc0\x05\x00\x00", pos)
    if idx == -1:
        break
    rva = 0x014b0000 + idx
    umap = get_usym_dict(rva - 16, 32)
    uinfo = []
    for k in sorted(umap):
        uinfo.extend(umap[k])
    print(f"  RVA 0x{rva:08x}: bytes={chunk2[idx-4:idx+8].hex(' ')} | USYM={uinfo[:3]}")
    pos = idx + 1

# 3. Check catalog.json or bundles for GUIDs f93b92def36a8474fa5798233a6a3fb8 and 446475dd53423864183c52075b8f0e32
aa_dir = root / "fm_Data/StreamingAssets/aa"
cat_path = aa_dir / "catalog.json"
if cat_path.exists():
    cat_text = cat_path.read_text(encoding="utf-8", errors="ignore")
    for guid in ("f93b92def36a8474fa5798233a6a3fb8", "446475dd53423864183c52075b8f0e32", "13a1f18bd93e860488c2cb84abb1168c", "c1a44f7eaa1698a43ab7664b7ce350da", "399c0aa9357f67847b91ba2fe4756083"):
        idx = cat_text.find(guid)
        print(f"GUID {guid} in catalog.json: idx={idx}")
