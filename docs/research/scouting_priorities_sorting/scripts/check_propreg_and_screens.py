import struct
from pathlib import Path
from check_deep_sorting import dump_func_details

# 1. Dump PropertyRegistration around hits
hits = [
    ("0x72692047 ('G ir')", 0x478164),
    ("0x67393649 ('I69g')", 0x4683e0),
    ("0x736a3232 ('22js')", 0x3fdcb6),
    ("0x73735043 ('CPss')", 0x3fdc40),
    ("0x706c7972 ('rylp')", 0x46ede4),
    ("0x644d7861 ('axMd')", 0x46b096),
    ("0x63594545 ('EEYc')", 0x46cb52),
    ("0x75446333 ('3cDu')", 0x468d8e),
    ("0x71754c76 ('vLuq')", 0x468ca2),
    ("0x73714e20 (' Nqs')", 0x468c2c),
    ("0x6e475773 ('sWGn')", 0x468bb6),
]

for label, rva in hits:
    dump_func_details(f"PropReg_{label}", rva - 0x40, 0x80)

# 2. Dump GetValueInternal of ScoutPlayerPrioritiesReference (0x0067d750) and SpecificallyScoutedPersonReference (0x00690540)
dump_func_details("ScoutPlayerPrioritiesReference.GetValueInternal", 0x0067d750, 0x350)
dump_func_details("SpecificallyScoutedPersonReference.GetValueInternal", 0x00690540, 0x450)
