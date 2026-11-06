import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from fm26save.binary_decompiler import unpack_unityfs_bundle
from check_refs_and_grid import walk_tree
from check_deep_sorting import root, dump_func_details

aa_dir = root / "fm_Data" / "StreamingAssets" / "aa" / "StandaloneWindows64"

# 1. Dump Bindings.GetProperties and Bindings.GetNthProperty
dump_func_details("Bindings.GetProperties", 0x014c1a60, 0x250)
dump_func_details("Bindings.GetNthProperty", 0x014c1450, 0x250)
dump_func_details("func_0x00e030e0", 0x00e030e0, 0x200)
dump_func_details("func_0x00abdcc0", 0x00abdcc0, 0x350)
