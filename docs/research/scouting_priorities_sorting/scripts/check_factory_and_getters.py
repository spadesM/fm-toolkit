import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir
from dump_headers_fast import dump_fast

dump_fast("StreamedListView_getters", 0x015acc00, 0x015acec0)
dump_fast("StreamedTable_getters", 0x015f20f0, 0x015f2380)
dump_fast("StreamedTable_ApplyPersistedSortingState", 0x015e58c0, 0x015e5ae0)
dump_fast("StreamedTable_RecreateHeaders_CreateHeader", 0x015e8f00, 0x015e90b0)
