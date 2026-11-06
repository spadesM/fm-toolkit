import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as dhf

# Find how metadata usages work or inspect 0x014c2040, 0x011235d0, 0x014d1c30, 0x014c3770
dhf.dump_fast("Bindings_0x014c2040 (Bindings.cs:2098)", 0x014c2040, 0x014c2200)
dhf.dump_fast("Bindings_0x014d1c30 (Bindings.cs:557)", 0x014d1c30, 0x014d1d80)
dhf.dump_fast("Bindings_0x014c3770 (Bindings.cs:2630)", 0x014c3770, 0x014c3b00)
dhf.dump_fast("VirtualisedList_SetIndices (0x016abc90)", 0x016abc90, 0x016abea0)
dhf.dump_fast("VirtualisedList_Refresh (0x016a9350)", 0x016a9350, 0x016a9600)
