import sys, struct, subprocess
sys.path.append(r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch')
from check_deep_sorting import pe, meta, image_base, off_to_va, va_to_off, get_mstr

# Check if fm.exe is running
out = subprocess.check_output(["tasklist", "/FI", "IMAGENAME eq fm.exe"], text=True)
print("Tasklist fm.exe:", out.strip())
