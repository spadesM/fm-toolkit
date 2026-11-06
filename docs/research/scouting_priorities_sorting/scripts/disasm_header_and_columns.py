import sys
sys.path.append(r"c:\Repos\fm26save\scratch")
import dump_headers_fast as dhf

dhf.dump_fast("StreamedTable_Header_all", 0x015f2d00, 0x015f3900)
dhf.dump_fast("Func_015f51a0", 0x015f5150, 0x015f5300)
dhf.dump_fast("StreamedTable_CreateColumn_and_Columns", 0x015e7d50, 0x015e8900)
