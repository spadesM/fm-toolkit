import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
import dump_headers_fast as dhf

start_rva = 0x003e4f30
end_rva = 0x004c5d06
start_off = dhf.va_to_off(dhf.image_base + start_rva)
end_off = dhf.va_to_off(dhf.image_base + end_rva)
chunk = dhf.pe[start_off:end_off]

for i in range(len(chunk) - 7):
    if chunk[i] == 0x4c and chunk[i+1] == 0x8b and chunk[i+2] == 0x05:
        rel = struct.unpack_from("<i", chunk, i+3)[0]
        target_va = dhf.image_base + start_rva + i + 7 + rel
        s = dhf.resolve_rip(target_va)
        if any(k in s for k in ("SpecificallyScouted", "ScoutPriorit")):
            hit_rva = start_rva + i
            print(f"Found {s} at RVA 0x{hit_rva:08x}")
            dhf.dump_fast(f"Ref_{s}", hit_rva - 0x60, hit_rva + 0x20)
