import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_sorting_details import dump_fast

dump_fast("StreamedTable_Header_015df450_015dfe00", 0x015df450, 0x015dfe00)
dump_fast("StreamedTable_CreateHeader_015e8f00_015e90b0", 0x015e8f00, 0x015e90b0)
dump_fast("StreamedTable_CreateColumnsFrom_015e8170_015e83b0", 0x015e8170, 0x015e83b0)
dump_fast("StreamedTable_ApplyPersistedSortingState_015e58c0_015e59b0", 0x015e58c0, 0x015e59b0)
dump_fast("StreamedListView_Deserialize_015b0b50_015b1500", 0x015b0b50, 0x015b1500)
