import os, struct, sys
sys.stdout.reconfigure(encoding="utf-8")
scratch_dir = r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch"
sys.path.insert(0, scratch_dir)
print("Scratch files:", [f for f in os.listdir(scratch_dir) if f.endswith(".py")])

from check_deep_sorting import pe, meta, hdr, image_base, va_to_off, off_to_va, rva_to_end, rva_to_method_name
from check_j1ct_and_nth_prop import get_mstr, get_str_literal, dump_with_strings
from disasm_sorting_callbacks import resolve_meta_usage, byval_to_type

# Let's check what resolve_meta_usage gives for 0x02e06ea8 (in ProcessSortingDataChanged) and 0x02e21500 (in Bindings.GetNthProperty)
print("0x02e06ea8:", resolve_meta_usage(0x02e06ea8))
print("0x02e21500:", resolve_meta_usage(0x02e21500))

# Also let's check how Il2CppType table is mapped in Il2CppMetadataRegistration in GameAssembly.dll!
# In disasm_sorting_callbacks.py, byval_to_type mapped tu[5] (byvalTypeIndex) -> tname.
# Wait: what if idx=32982 is a TypeIndex in Il2CppMetadataRegistration.types, and some TypeDefinition has tu[5] == 32982 or tu[6] == 32982?
types_off, types_sz = hdr[40], hdr[41]
for ti in range(types_sz // 88):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    if 32982 in tu[:10]:
        print(f"Found 32982 in TypeDef {ti}: {get_mstr(tu[1])}.{get_mstr(tu[0])} -> tu[:10]={tu[:10]}")

# And what about MethodSpec / GenericMethod / MethodInfo for tag=6, idx=184959?
# Wait: in IL2CPP MetadataUsage, what are the tags?
# 1 = kIl2CppMetadataUsageTypeInfo (index into Il2CppMetadataRegistration.types)
# 2 = kIl2CppMetadataUsageIl2CppType (index into Il2CppMetadataRegistration.types)
# 3 = kIl2CppMetadataUsageMethodDef (index into global-metadata methods table)
# 4 = kIl2CppMetadataUsageFieldInfo (index into Il2CppMetadataRegistration.fieldRefs)
# 5 = kIl2CppMetadataUsageStringLiteral (index into global-metadata stringLiterals)
# 6 = kIl2CppMetadataUsageMethodRef (index into Il2CppMetadataRegistration.methodSpecs)
methods_off, methods_sz = hdr[12], hdr[13]
print(f"methods count = {methods_sz // 36}")

# Let's dump Bindings.Create, Bindings.SetAlias, Bindings.Bind, Bindings.Unbind, Bindings.Set
dump_with_strings("Bindings.Create", 0x014bf980, 0x280)
dump_with_strings("Bindings.SetAlias", 0x014c3050, 0x180)
dump_with_strings("Bindings.Bind", 0x014bee30, 0x350)
dump_with_strings("Bindings.Unbind", 0x014c63d0, 0x200)
dump_with_strings("Bindings.Set", 0x014c5740, 0x200)
