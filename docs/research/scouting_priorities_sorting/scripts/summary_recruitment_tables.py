import sys
sys.path.insert(0, r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from dump_all_recruitment_tables import data, offsets, parse_st

for idx, off in enumerate(offsets):
    d = parse_st(data, off)
    if d['Binding']:
        print(f"[{idx:2d}] off=0x{off:x} Binding={d['Binding']!r} SortBinding={d['SortBinding']!r} Reorderable={d['Reorderable']} DisableSorting={d['DisableSorting']} SelMode={d['SelectionMode']} DragCell={d['DragCellID']!r}")
