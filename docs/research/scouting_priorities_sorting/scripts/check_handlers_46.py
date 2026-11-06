import sys, struct
sys.path.append(r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import rva_to_method_name, rva_to_end, dump_func_details

for target in [0x003fdc41, 0x0046b097, 0x0046cb53]:
    for start, end in rva_to_end.items():
        if start <= target < end:
            print(f"Target 0x{target:08x} is in func 0x{start:08x}..0x{end:08x}: {rva_to_method_name.get(start)}")
            dump_func_details(f"Func at 0x{start:08x}", start, min(end - start, 0x200))
            break
