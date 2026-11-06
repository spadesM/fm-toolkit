import struct
import sys
sys.path.append(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from dump_fast import pe, meta, rva_to_off, get_str, disasm_range, types_off, types_cnt

# Let's check MetaUsage(tag=1, idx=38755) and MetaUsage(tag=2, idx=32982)
# Remember in Il2CppMetadataRegistration, types array is at some address. Let's find how dump_fast resolves MetaUsage or look at dump_fast.py
with open(r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\dump_fast.py", "r") as f:
    print("dump_fast.py snippet:")
    print(f.read()[:2000])
