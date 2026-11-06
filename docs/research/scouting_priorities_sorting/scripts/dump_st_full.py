import re
import struct
from fm26save.binary_decompiler import resolve_fm_install_dir, unpack_unityfs_bundle

root = resolve_fm_install_dir()
aa = root / "fm_Data/StreamingAssets/aa/StandaloneWindows64"
raw = unpack_unityfs_bundle(aa / "ui-recruitment_assets_all.bundle")

# Let's inspect UxmlSerializedData.Deserialize in GameAssembly.dll completely to see every field offset on rsi and rdi!
pe = (root / "GameAssembly.dll").read_bytes()
e_lfanew = struct.unpack_from("<I", pe, 0x3C)[0]
num_sec = struct.unpack_from("<H", pe, e_lfanew + 6)[0]
opt_size = struct.unpack_from("<H", pe, e_lfanew + 20)[0]
sec_off = e_lfanew + 24 + opt_size
sections = []
for i in range(num_sec):
    s = pe[sec_off + i * 40 : sec_off + (i + 1) * 40]
    name = s[:8].rstrip(b"\x00").decode("ascii", errors="replace")
    vsize, vaddr, rsize, raddr = struct.unpack_from("<IIII", s, 8)
    sections.append((name, vaddr, vsize, raddr, rsize))

def rva_to_off(rva: int) -> int:
    for _, vaddr, vsize, raddr, rsize in sections:
        if vaddr <= rva < vaddr + max(vsize, rsize):
            return raddr + (rva - vaddr)
    return -1

# Let's parse the serialized StreamedTable/UxmlSerializedData in ScoutPrioritiesBlock and ScoutPrioritiesBlock-Small and ShortlistMainBlock
# Wait: where does DragCellID ("drag-column") appear in ScoutPrioritiesBlock's StreamedTable/UxmlSerializedData?
for label, block_pos in [
    ("ScoutPrioritiesBlock", 2350192),
    ("ScoutPrioritiesBlock-Small", 2608944),
    ("ShortlistMainBlock", 1406944),
]:
    chunk = raw[block_pos : block_pos + 10000]
    st_pos = chunk.find(b"StreamedTable/UxmlSerializedData")
    sub = chunk[st_pos : st_pos + 1300]
    print(f"=== {label} (st_pos={block_pos + st_pos}) ===")
    for off in range(0, len(sub), 32):
        h = sub[off:off+32].hex(" ")
        asc = "".join(chr(b) if 32 <= b < 127 else "." for b in sub[off:off+32])
        print(f"  {off:04x}: {h:<95} | {asc}")
