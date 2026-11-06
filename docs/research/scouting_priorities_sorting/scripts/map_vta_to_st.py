import sys, struct, os, re
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir, unpack_unityfs_bundle

root = resolve_fm_install_dir()
aa_dir = root / "fm_Data/StreamingAssets/aa/StandaloneWindows64"
raw = unpack_unityfs_bundle(aa_dir / "ui-recruitment_assets_all.bundle")

needle = b"\x20\x00\x00\x00StreamedTable/UxmlSerializedData"
offsets = []
pos = 0
while True:
    idx = raw.find(needle, pos)
    if idx < 0:
        break
    offsets.append(idx)
    pos = idx + len(needle)

pattern = re.compile(rb'([\x05-\x40]\x00\x00\x00)([A-Za-z0-9_-]{5,64})')
vta_list = []
for m in pattern.finditer(raw):
    slen = struct.unpack_from("<I", m.group(1), 0)[0]
    s = raw[m.start() + 4 : m.start() + 4 + slen]
    if all(32 <= b < 127 for b in s):
        name = s.decode('ascii')
        if any(w in name for w in ['Block', 'Card', 'Tile', 'Panel', 'View', 'Table', 'Modal', 'Popup', 'Priorit', 'Scout', 'Recruitment', 'Shortlist']):
            vta_list.append((m.start(), name))

for st_off in offsets:
    prev = [x for x in vta_list if x[0] < st_off and st_off - x[0] < 60000]
    prev_names = [f"{n} (+{st_off - p})" for p, n in prev[-4:]]
    print(f"ST at 0x{st_off:06x} ({st_off:7d}): {prev_names}")
