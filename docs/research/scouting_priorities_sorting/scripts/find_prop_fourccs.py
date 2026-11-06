import sys, struct
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
sys.path.insert(0, r"c:\Repos\fm26save")
sys.stdout.reconfigure(encoding="utf-8")

import check_deep_sorting as cds
import dump_headers_fast as dhf

# Find string literal Metadata Usages in PropertyRegistration.Initialise (0x003e4f30..0x00490000)
# Let's scan 0x003e4f30..0x00490000 for RIP references that resolve to STR containing ScoutPriorities or SpecificallyScouted
pe = cds.pe
start_off = cds.va_to_off(cds.image_base + 0x003e4f30)
end_off = cds.va_to_off(cds.image_base + 0x00490000)
code = pe[start_off:end_off]

for i in range(len(code) - 7):
    # 4c 8b 05 disp32 (mov r8, [rip + disp32])
    if code[i] == 0x4C and code[i+1] == 0x8B and code[i+2] == 0x05:
        disp = struct.unpack_from("<i", code, i + 3)[0]
        rva = 0x003e4f30 + i
        rip_rva = rva + 7 + disp
        info = dhf.resolve_rip(cds.image_base + rip_rva)
        if info and any(w in info for w in ["ScoutPriorit", "SpecificallyScouted", "OverallReportGrade", "positioncombined", "ClubRecruitmentReport"]):
            print(f"RVA 0x{rva:08x}: {info}")
            dhf.dump_fast(f"PropReg @ 0x{rva-0x80:08x}", rva - 0x80, rva + 0x40)
