import sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import dump_func_details

dump_func_details("Bindings.HashPath", 0x014c1d40, 0x300)
dump_func_details("Bindings.Bind_0x014beef0", 0x014beef0, 0x360)
dump_func_details("Bindings.Bind_0x014bf250", 0x014bf250, 0x360)
dump_func_details("Bindings.SetInternal_part2", 0x014c3770 + 0x300, 0x500)
dump_func_details("VirtualisedList.set_Reorderable", 0x014dada0, 0x100)
dump_func_details("StreamedListView.set_Reorderable", 0x015ad4f0, 0x100)
