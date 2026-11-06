import struct, sys, re
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as dhf
from fm26save.binary_decompiler import decompile_gameassembly_bindings

dhf.dump_fast("SpecificallyScoutedPersonReference", 0x00696ef0, 0x00697380)
dhf.dump_fast("ScoutPlayerPrioritiesReference", 0x0067d2e0, 0x0067d670)
