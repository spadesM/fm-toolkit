import sys
sys.path.append(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import dump_func_details
from annotate_sorting_usym import dump_annotated

regions = [
    ("PropertyRegistration_ScoutPriorities", 0x003fdb90, 0x003fdd60 - 0x003fdb90),
    ("PropertyRegistration_plyr", 0x0046ed90, 0x100),
    ("PropertyRegistration_axMd", 0x0046b040, 0x100),
    ("PropertyRegistration_EEYc", 0x0046cb00, 0x100),
    ("PropertyRegistration_ScoutedPersonRest", 0x00468b60, 0x00468e00 - 0x00468b60),
]

for name, rva, size in regions:
    dump_func_details(name, rva, size)
    dump_annotated(name, rva, size)
