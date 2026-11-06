import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from dump_headers_fast import dump_fast

targets = [
    ("StreamedTable.UxmlSerializedData.Deserialize (0x015f36b0..0x015f3d00)", 0x015f36b0, 0x015f3d00),
    ("StreamedTable +0x9b8 @ 0x015e8f75 (StreamedTable.cs:2110)", 0x015e8f00, 0x015e9050),
    ("StreamedTable +0x9b8 @ 0x015eb02e (StreamedTable.cs:2110)", 0x015eafe0, 0x015eb120),
    ("StreamedTable +0x9b8 @ 0x015ec322 (StreamedTable.cs:2172-2264)", 0x015ec280, 0x015ec400),
    ("StreamedTable +0x9b8 @ 0x015f00b6 (TrySetColumnsAndSort, StreamedTable.cs:1212)", 0x015f0040, 0x015f0300),
    ("StreamedTable +0x9b8 @ 0x015f14f4 (StreamedTable.cs:802-803)", 0x015f14c0, 0x015f1600),
    ("StreamedTable +0x958 @ 0x015ecfa9 (StreamedTable.cs:1337-1340)", 0x015ecf40, 0x015ed150),
    ("StreamedListView +0x5c1 @ 0x015ac55a & 0x015ad502 & 0x015b1009", 0x015ac500, 0x015ac600),
    ("StreamedListView.set_Reorderable (0x015ad4e0..0x015ad580)", 0x015ad4e0, 0x015ad580),
    ("StreamedListView.UxmlSerializedData.Deserialize (0x015b0f50..0x015b1150)", 0x015b0f50, 0x015b1150),
    ("VirtualisedList +0x5c1 @ 0x016a85cc..0x016a8b9b", 0x016a8580, 0x016a8c00),
]

for name, s, e in targets:
    dump_fast(name, s, e)
