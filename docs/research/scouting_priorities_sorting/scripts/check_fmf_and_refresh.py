import struct, sys, zstandard
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import root, dump_func_details

fmf_path = root / "data" / "game_simulation" / "languages.fmf"
with open(fmf_path, "rb") as f:
    hdr = f.read(64)
    f.seek(-64, 2)
    tail = f.read(64)
print("FMF hdr:", hdr.hex(" "))
print("FMF tail:", tail.hex(" "))
# Usually FMF has an offset to directory at the end or beginning:
# Let's check last 8 bytes or hdr bytes:
for off in range(0, 32, 4):
    print(f"  hdr+{off}: u32={struct.unpack_from('<I', hdr, off)[0]} u64={struct.unpack_from('<Q', hdr, off)[0] if off<=24 else 0}")
for off in range(0, 60, 4):
    val = struct.unpack_from("<I", tail, off)[0]
    if 100_000_000 < val < 210_578_206:
        print(f"  tail+{off}: possible dir offset {val}")

dump_func_details("StreamedListView.StateChanged", 0x015a9c80, 0x200)
dump_func_details("StreamedListView.RefreshInternal", 0x015a9060, 0x200)
dump_func_details("StreamedTable.RefreshInternal", 0x015eed80, 0x200)
dump_func_details("VirtualisedList.Refresh", 0x016a93f0, 0x100)
dump_func_details("VirtualisedList.ResetView", 0x016a9420, 0x100)
dump_func_details("VirtualisedList.UpdateView", 0x016aa730, 0x100)
