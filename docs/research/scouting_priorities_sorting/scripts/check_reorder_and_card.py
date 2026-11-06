import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir, unpack_unityfs_bundle

root = resolve_fm_install_dir()
pe = (root / "GameAssembly.dll").read_bytes()

e_lfanew = struct.unpack_from("<I", pe, 0x3C)[0]
num_sec = struct.unpack_from("<H", pe, e_lfanew + 6)[0]
opt_size = struct.unpack_from("<H", pe, e_lfanew + 20)[0]
image_base = struct.unpack_from("<Q", pe, e_lfanew + 24 + 24)[0]
sec_off = e_lfanew + 24 + opt_size
sections = []
for i in range(num_sec):
    s = pe[sec_off + i * 40 : sec_off + (i + 1) * 40]
    name = s[:8].rstrip(b"\x00").decode("ascii", errors="replace")
    vsize, vaddr, rsize, raddr = struct.unpack_from("<IIII", s, 8)
    sections.append((name, vaddr, vsize, raddr, rsize))

def va_to_off(va: int) -> int:
    rva = va - image_base
    for _, vaddr, vsize, raddr, rsize in sections:
        if vaddr <= rva < vaddr + max(vsize, rsize):
            off = raddr + (rva - vaddr)
            return off if off < raddr + rsize else -2
    return -1

# Check set_Reorderable (0x015ad4f0) and set_DisableSorting (0x015f2420)
for name, rva, sz in [
    ("StreamedListView.set_Reorderable", 0x015ad4f0, 33),
    ("StreamedTable.set_DisableSorting", 0x015f2420, 32),
    ("StreamedTable.UxmlSerializedData.Deserialize", 0x015f3cd0, 1200),
]:
    off = va_to_off(image_base + rva)
    print(f"=== {name} (0x{rva:08x}) ===")
    print(pe[off : off + min(sz, 128)].hex(" "))

# Also check RecruitmentScoutPrioritiesCard in ui-recruitment_assets_all.bundle
rec_raw = unpack_unityfs_bundle(root / "fm_Data/StreamingAssets/aa/StandaloneWindows64/ui-recruitment_assets_all.bundle")
for needle in [b"RecruitmentScoutPrioritiesCard", b"ScoutPrioritiesBlock", b"SpecificallyScoutedPlayers"]:
    pos = 0
    while True:
        idx = rec_raw.find(needle, pos)
        if idx < 0:
            break
        print(f"Found {needle.decode()} in ui-recruitment at {idx} (0x{idx:x})")
        pos = idx + 1
