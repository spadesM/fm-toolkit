import sys
sys.path.append(r"c:\Repos\fm26save\scratch")
import dump_headers_fast as dhf

dhf.dump_fast("StreamedTable.get_DisableSorting", 0x015f2190, 0x015f21c0)
dhf.dump_fast("StreamedTable.set_DisableSorting", 0x015f2420, 0x015f2450)
dhf.dump_fast("StreamedTable.CreateColumn", 0x015e7dc0, 0x015e8150)
dhf.dump_fast("StreamedTable.CreateColumns", 0x015e83b0, 0x015e8700)
dhf.dump_fast("StreamedListView.<ApplySorting>g__SetupRow|246_0", 0x015aa320, 0x015aa631)
dhf.dump_fast("StreamedListView.BindSortPathNextDepth", 0x015a4850, 0x015a49a6)
dhf.dump_fast("StreamedListView.OnSortingDataChanged", 0x015a7ff0, 0x015a8109)
dhf.dump_fast("StreamedListView.ProcessSortingDataChanged", 0x015a8cb0, 0x015a8ead)
