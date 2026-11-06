import sys
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import rva_to_method_name

for rva, names in sorted(rva_to_method_name.items()):
    for name in names:
        if 'StreamedObjectList' in name or 'Streamed' in name:
            if 'StreamedObjectList' in name or 'Sort' in name or 'Reorder' in name:
                print(f"0x{rva:08x}: {name}")
