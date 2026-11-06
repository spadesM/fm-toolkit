import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, sections, va_to_off, off_to_va, image_base, rva_to_method_name, dump_func_details
)

# Let's check string literals in global-metadata.dat
str_lit_off, str_lit_sz, str_lit_data_off, str_lit_data_sz = struct.unpack_from("<IIII", meta, 8)
num_str_lits = str_lit_sz // 8
print(f"Total string literals in global-metadata.dat: {num_str_lits}")

def get_str_lit(idx):
    ln, doff = struct.unpack_from("<II", meta, str_lit_off + idx * 8)
    return meta[str_lit_data_off + doff : str_lit_data_off + doff + ln].decode("utf-8", errors="replace")

# Search string literals for SpecificallyScouted or ScoutPriorities
for i in range(num_str_lits):
    s = get_str_lit(i)
    if any(k in s for k in ("SpecificallyScouted", "ScoutPriorit", "ScoutPlayerPriorit", "OverallReportGrade", "RecruitmentFocus")):
        print(f"  str_lit[{i}] = {s!r}")

# Let's also check where PropertyRegistration.Initialise (0x003ee670) gets its string literals!
dump_func_details("PropertyRegistration.Initialise_start", 0x003ee670, 0x120)
