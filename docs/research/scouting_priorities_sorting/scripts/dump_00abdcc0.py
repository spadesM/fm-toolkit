from check_deep_sorting import rva_to_method_name, dump_func_details

print("0x00abdcc0 names:", rva_to_method_name.get(0x00abdcc0))
dump_func_details("Sub_00abdcc0 (called by SetSortingBinding)", 0x00abdcc0, 0x300)
