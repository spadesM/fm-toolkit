import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import dump_func_details, pe, va_to_off, off_to_va, image_base, meta, images_off, images_sz, types_off, methods_off, get_mstr, modules, rva_to_end, rva_to_method_name

dump_func_details("Func_0x002ae590", 0x002ae590)

# Search in global-metadata.dat (both UTF-8 and UTF-16LE) and GameAssembly.dll (both UTF-8 and UTF-16LE)
for label, blob in [("PE", pe), ("META", meta)]:
    for pat_str in ["SpecificallyScouted", "ScoutPriorit", "itemmoved", "axMd", "EEYc", "3cDu", "vLuq", " Nqs", "sWGn", "J1Ct"]:
        for enc in ["utf-8", "utf-16le"]:
            pat = pat_str.encode(enc)
            pos = 0
            hits = []
            while True:
                idx = blob.find(pat, pos)
                if idx == -1: break
                rva = (off_to_va(idx) - image_base) if label == "PE" else idx
                s = blob[max(0, idx-16):min(len(blob), idx+64)]
                hits.append((rva, idx, s))
                pos = idx + 1
                if len(hits) >= 20: break
            if hits:
                print(f"\n[{label} {enc}] Pattern {pat_str!r}: {len(hits)} hits")
                for rva, idx, s in hits[:10]:
                    print(f"  RVA/off=0x{rva:08x}: {s!r}")
