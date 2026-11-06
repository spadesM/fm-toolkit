import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, va_to_off, off_to_va, image_base,
    types_off, types_sz, fields_off, fields_sz, get_mstr
)

# Let's check StreamedTable.UxmlSerializedData.Deserialize (0x015f36b0)
# Notice how every attribute check in Deserialize (0x015f36b0) has the pattern:
#   movzx edx, byte ptr [rsi + flag_off]
#   ...
#   read value from [rsi + val_off]
#   write to [rdi + target_off]
# Let's extract all (flag_off, val_off, target_off) triples from 0x015f36b0..0x015f4170!

off = va_to_off(image_base + 0x015f36b0)
code = pe[off : off + 0xac0]

import re
# Look for: 0f b6 96 <flag_off:4> (movzx edx, byte ptr [rsi + flag_off])
for m in re.finditer(b"\x0f\xb6\x96(....)", code):
    pos = m.start()
    flag_off = struct.unpack_from("<I", m.group(1))[0]
    chunk = code[pos:pos+100]
    # Find next [rsi + val_off] and [rdi + target_off]
    print(f"At +0x{pos:03x}: flag_off=0x{flag_off:03x} | bytes={chunk[:48].hex(' ')}")
