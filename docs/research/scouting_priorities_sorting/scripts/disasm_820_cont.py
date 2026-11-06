import sys
sys.path.append(r"c:\Repos\fm26save\scratch")
import dump_headers_fast as dhf

dhf.dump_fast("StreamedListView_820_cont", 0x00abde00, 0x00abe000)
dhf.dump_fast("Bindings_2098", 0x014c2040, 0x014c2300)
dhf.dump_fast("Bindings_TryGetProperty", 0x014d0b50, 0x014d1000)
