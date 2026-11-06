import sys
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from cs_disasm import disasm, find_rva
out = open(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\cs_header_chain.txt", "w", encoding="utf-8")
for rva, label in [
    (0x15eac30, "StreamedTable.MakeColumnHeader"),
    (0x160bb80, "MakeColumnHeader b__0 (click lambda)"),
    (0x15e8f00, "StreamedTable.CreateHeader"),
    (0x15df7e0, "Header.SetupClickHandler"),
    (0x15f2ea0, "Header ctor b__0"),
    (0x15dfab0, "Header..ctor"),
    (0x15a3c60, "SortComparer.Compare(int,int)"),
    (0x15a3d30, "SortComparer.Compare(Data,Data)"),
    (0x15e9450, "StreamedTable.EntryForColumn"),
    (0x15f1380, "StreamedTable.UpdateSortColum"),
]:
    disasm(rva, label=label, out=out)
out.close()
