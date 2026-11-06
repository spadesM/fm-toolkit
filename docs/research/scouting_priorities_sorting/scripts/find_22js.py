import sys, os, glob
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
import dump_headers_fast as dhf
from check_deep_sorting import rva_to_end, rva_to_method_name, off_to_va
import bisect

all_starts = sorted(rva_to_end.keys())

for pat in [b"22js", b"Ha7v", b"CPss", b"p9yb"]:
    pos = 0
    print(f"=== GameAssembly.dll hits for {pat!r} ===")
    while True:
        idx = dhf.pe.find(pat, pos)
        if idx == -1: break
        rva = off_to_va(idx) - dhf.image_base
        m_idx = bisect.bisect_right(all_starts, rva) - 1
        m_rva = all_starts[m_idx] if m_idx >= 0 else 0
        m_name = rva_to_method_name.get(m_rva)
        print(f"  RVA 0x{rva:08x} in {m_name} (0x{m_rva:08x}..0x{rva_to_end.get(m_rva,0):08x})")
        pos = idx + 1

# Also check all .dll and .exe files in Football Manager 26 folder
for root_dir, dirs, files in os.walk(str(dhf.root)):
    for fn in files:
        if fn.lower().endswith((".dll", ".exe")) and fn != "GameAssembly.dll":
            fpath = os.path.join(root_dir, fn)
            try:
                data = open(fpath, "rb").read()
            except Exception:
                continue
            for pat in [b"22js", b"Ha7v", b"J1Ct", b"SpecificallyScouted"]:
                if pat in data:
                    print(f"Found {pat!r} in {fpath}!")
