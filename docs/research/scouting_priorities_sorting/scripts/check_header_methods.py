import sys
sys.path.append(r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details

funcs = [
    ("Header.Bind", 0x015df4f0),
    ("Header.OnBindingChanged", 0x015df600),
    ("Header.ResetSortingIcons", 0x015df720),
    ("Header.SetupClickHandler", 0x015df7e0),
    ("Header.Unbind", 0x015df880),
    ("Header.UpdateSortingIcons", 0x015df970),
]

for name, rva in funcs:
    dump_func_details(name, rva)
