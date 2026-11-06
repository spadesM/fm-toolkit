import sys, struct
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details, rva_to_method_name

for rva, name in [
    (0x015e6230, "StreamedTable.BindHeader"),
    (0x0160b6b0, "<>c__DisplayClass234_0.<BindHeader>b__0"),
    (0x0160b850, "<>c__DisplayClass234_0.<BindHeader>b__2"),
    (0x0160b9e0, "<>c__DisplayClass234_1.<BindHeader>b__1"),
    (0x014c1a60, f"sub_14c1a60 ({rva_to_method_name.get(0x014c1a60)})"),
    (0x00e030e0, f"sub_00e030e0 ({rva_to_method_name.get(0x00e030e0)})"),
]:
    dump_func_details(name, rva)
