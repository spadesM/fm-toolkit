import struct

with open(r'C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26\GameAssembly.dll', 'rb') as f:
    pe = f.read()
with open(r'C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26\fm_Data\il2cpp_data\Metadata\global-metadata.dat', 'rb') as mf:
    meta = mf.read()

hdr = struct.unpack_from('<64I', meta, 0)
str_off, str_sz = hdr[6], hdr[7]
methods_off, methods_sz = hdr[12], hdr[13]
types_off, types_sz = hdr[40], hdr[41]

def get_mstr(off):
    return meta[str_off + off : meta.find(b'\x00', str_off + off)].decode('utf-8', errors='replace')

e_lfanew = struct.unpack_from('<I', pe, 0x3C)[0]
num_sec = struct.unpack_from('<H', pe, e_lfanew + 6)[0]
opt_size = struct.unpack_from('<H', pe, e_lfanew + 20)[0]
image_base = struct.unpack_from('<Q', pe, e_lfanew + 24 + 24)[0]
sec_off = e_lfanew + 24 + opt_size
sections = [struct.unpack_from('<IIII', pe, sec_off + i * 40 + 8) for i in range(num_sec)]

def va_to_off(va):
    rva = va - image_base
    for vsize, vaddr, rsize, raddr in sections:
        if vaddr <= rva < vaddr + max(vsize, rsize):
            return raddr + (rva - vaddr)
    return -1

ptrs_off = va_to_off(0x182f7ad30)
rva_to_name = {}
for midx in range(methods_sz // 36):
    mu = struct.unpack_from('<7i4H', meta, methods_off + midx * 36)
    tidx = mu[2]
    if 5700 <= tidx <= 6600:
        tu = struct.unpack_from('<22i', meta, types_off + tidx * 88)
        tname = get_mstr(tu[0])
        mname = get_mstr(mu[0])
        rid = (mu[6] & 0xFFFFFF) - 1
        if 0 <= rid < 9785:
            m_va = struct.unpack_from('<Q', pe, ptrs_off + rid * 8)[0]
            if m_va:
                rva_to_name[m_va - image_base] = f'{tname}.{mname}'

for rva, name in sorted(rva_to_name.items()):
    if 0x015df000 <= rva <= 0x015f5000:
        print(f'0x{rva:08x}: {name}')

for label, s_rva, sz in [
    ('Around_0x015ec322', 0x015ec280, 0x120),
    ('CreateHeader_0x015e8f00', 0x015e8f00, 0x100),
    ('UxmlTraits_0x015f3a50', 0x015f3a50, 0x200),
]:
    print(f'\n=== {label} (0x{s_rva:08x}) ===')
    off = va_to_off(image_base + s_rva)
    code = pe[off : off + sz]
    for k in range(0, len(code), 16):
        chunk = code[k : k + 16]
        print(f'  +0x{k:03x} (0x{s_rva+k:08x}): ' + ' '.join(f'{b:02x}' for b in chunk))
    for i in range(len(code) - 5):
        if code[i] in (0xE8, 0xE9):
            rel = struct.unpack_from('<i', code, i + 1)[0]
            t = s_rva + i + 5 + rel
            if 0x1000 <= t < 0x3000000:
                print(f'  +0x{i:03x}: CALL/JMP 0x{t:08x} ({rva_to_name.get(t, "")})')
