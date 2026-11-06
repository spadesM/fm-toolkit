import struct, sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
out_path = Path(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\sorting_disasm8.txt")
out_file = out_path.open("w", encoding="utf-8")
sys.stdout = out_file

from check_deep_sorting import rva_to_end
from dump_headers_fast import dump_fast

targets = [
    ("StreamedTable.BindHeader", 0x015e6230),
    ("StreamedTable.BindHeaders", 0x015e6ca0),
    ("StreamedTable.CreateHeader", 0x015e8f00),
    ("StreamedTable.RecreateHeaders", 0x015eecb0),
    ("StreamedTable.CreateColumn", 0x015e7dc0),
    ("StreamedTable.CreateColumns", 0x015e83b0),
    ("StreamedTable.InitialiseColumns", 0x015ea870),
    ("StreamedTable.TrySetColumnsAndSort", 0x015f0040),
    ("StreamedTable.ApplyPersistedSortingState", 0x015e58c0),
    ("StreamedTable.SetSorting_overload1", 0x015efc40),
    ("StreamedTable.SetNoSorting", 0x015ef750),
    ("StreamedTable.SetList", 0x015ef610),
    ("StreamedTable.RebuildInternal", 0x015ee9c0),
    ("StreamedTable.RefreshInternal", 0x015eed80),
    ("StreamedTable.OnSortColumn", 0x015ee250),
    ("StreamedListView.set_Reorderable", 0x015ad4f0),
    ("StreamedListView.BindToData", 0x015a49b0),
    ("StreamedListView.UpdateSortingBinding", 0x015ab800),
    ("StreamedListView.RefreshInternal", 0x015a9060),
    ("StreamedListView.Rebuild", 0x015a8eb0),
    ("StreamedListView.ResetIndices", 0x015a9420),
    ("StreamedListView.SetList", 0x015a9880),
    ("StreamedListView.StateChanged", 0x015a9c80),
    ("StreamedListView.ResolveStateChanges", 0x015a9620),
    ("StreamedListView.EndStateChange", 0x015a5350),
]

for name, rva in targets:
    end_rva = rva_to_end.get(rva, rva + 0x200)
    dump_fast(name, rva, end_rva)

out_file.close()
print("Done!", file=sys.__stdout__)
