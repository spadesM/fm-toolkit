import re
import struct
from fm26save.binary_decompiler import resolve_fm_install_dir

with open("docs/decompiled_engine/DecompiledAllGameAssemblies.cs", "r", encoding="utf-8", errors="ignore") as f:
    cs = f.read()

for m in re.finditer(r"// Assembly: [^\n]+\nnamespace [^\n]+\n\{\n    public (?:class|struct) \w*StreamedList\w*.*?\n\}", cs, re.S):
    print(m.group(0))
