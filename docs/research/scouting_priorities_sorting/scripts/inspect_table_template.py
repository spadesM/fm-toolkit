import re
with open("docs/decompiled_engine/DecompiledAllGameAssemblies.cs", "r", encoding="utf-8", errors="ignore") as f:
    cs = f.read()

for ti in range(6125, 6145):
    m = re.search(rf"// Assembly: [^\n]+\(TypeIndex: {ti}\)\nnamespace [^\n]+\n\{{.*?\n\}}", cs, re.S)
    if m:
        print(m.group(0))
