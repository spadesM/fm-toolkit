import sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import dump_func_details, pe, va_to_off, image_base, rva_to_method_name
from compare_full_st_serialized_data import parse_bundle_with_reftypes
from check_refs_and_grid import walk_tree

dump_func_details("StreamedListView.UpdateEnabledState", 0x015aab80)
dump_func_details("StreamedListView.CanBuild", 0x015a50b0)
dump_func_details("StreamedTable.CanBuild", 0x015e7580)
dump_func_details("StreamedListView.HasSorting", 0x015a5f20)
dump_func_details("StreamedListView.ClearSortingState", 0x015a5180)
dump_func_details("StreamedListView.SetNoSorting", 0x015a99d0)
dump_func_details("StreamedTable.ApplyPersistedSortingState", 0x015e58c0)
dump_func_details("StreamedTable.UpdateSortColumn", 0x015f1380)
