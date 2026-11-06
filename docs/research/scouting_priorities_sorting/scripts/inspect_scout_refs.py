import json
import re
import struct
from fm26save.binary_decompiler import resolve_fm_install_dir, unpack_unityfs_bundle

with open("docs/decompiled_engine/entity_reference_graph.json", "r", encoding="utf-8") as f:
    erg = json.load(f)

for k in ["ScoutPlayerPrioritiesReference", "ScoutTeamPrioritiesReference", "SpecificallyScoutedPersonReference", "SpecificallyScoutedTeamReference", "HumanPersonSearchReference"]:
    if k in erg["reference_classes"]:
        print(f"=== {k} ===")
        print(json.dumps(erg["reference_classes"][k], indent=2))

root = resolve_fm_install_dir()
aa = root / "fm_Data/StreamingAssets/aa/StandaloneWindows64"
raw = unpack_unityfs_bundle(aa / "ui-recruitment_assets_all.bundle")

print("\n=== ALL StreamedTable/UxmlSerializedData in ui-recruitment_assets_all.bundle ===")
for m in re.finditer(b"StreamedTable/UxmlSerializedData", raw):
    pos = m.start()
    # Find nearest preceding UXML name
    before = raw[max(0, pos - 12000) : pos]
    uxml_names = re.findall(rb"[A-Za-z0-9_-]{8,45}(?=\x00.*UnityEngine\.UIElements\.UXML)", before, re.S)
    strings_in_st = [s.decode("ascii", errors="replace") for s in re.findall(rb"[ -~]{4,}", raw[pos : pos + 1150])]
    print(f"\nOffset {pos}: strings={strings_in_st[:15]}")
    sub = raw[pos : pos + 1150]
    # Print non-zero 32-bit integers and strings in sub
    for off in range(0x100, min(0x460, len(sub)), 4):
        val = struct.unpack_from("<I", sub, off)[0]
        if val != 0 and not (0x20 <= (val & 0xFF) < 0x7F and 0x20 <= ((val >> 8) & 0xFF) < 0x7F):
            print(f"  +0x{off:03x}: 0x{val:08x} ({val})")
        elif 0x20 <= (val & 0xFF) < 0x7F and 0x20 <= ((val >> 8) & 0xFF) < 0x7F:
            pass
