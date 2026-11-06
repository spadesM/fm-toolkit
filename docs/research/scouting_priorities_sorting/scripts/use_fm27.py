"""Import this FIRST to redirect all helper scripts to the Football Manager 27 installation."""
import sys
from pathlib import Path
sys.path.insert(0, r"c:\Repos\fm26save")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import fm26save.binary_decompiler as _bd
FM27 = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 27")
_bd.DEFAULT_FM_PATHS = (FM27,)
