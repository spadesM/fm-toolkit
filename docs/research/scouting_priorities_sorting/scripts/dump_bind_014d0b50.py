import struct
from dump_headers_fast import dump_fast, meta, hdr, get_mstr

types_off, types_sz = hdr[40], hdr[41]
type_specs_off, type_specs_sz = hdr[28], hdr[29]

# Check what idx=32982 is in Il2CppType table or TypeDefinitions
# Wait: in il2cpp metadata, tag=2 is Il2CppType index!
# Let's check where Il2CppType array or TypeDefinitions are.
for i in range(types_sz // 88):
    if i == 32982:
        tu = struct.unpack_from("<22i", meta, types_off + i * 88)
        print("TypeDef 32982:", get_mstr(tu[1]), get_mstr(tu[0]))

dump_fast("Bindings.ScopeNode_Bind_014d0b50", 0x014d0b50, 0x014d12f0)
