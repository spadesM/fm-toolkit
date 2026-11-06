import sys
sys.path.append(r"c:\Repos\fm26save\scratch")
import dump_headers_fast as dhf

print("--- Disassembling StreamedTable sorting methods ---")
dhf.dump_fast("OnHeaderClicked", 0x015ec910, 0x015ecc60)
dhf.dump_fast("SetHeaderSortVisuals_and_SetSorting", 0x015efb10, 0x015f0040)
dhf.dump_fast("TrySetColumnsAndSort", 0x015f0040, 0x015f0430)
dhf.dump_fast("CreateTableHeaders", 0x015e9310, 0x015e9a00)
