import struct

with open(r'C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26\GameAssembly.dll', 'rb') as f:
    pe = f.read()
with open(r'C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26\fm_Data\il2cpp_data\Metadata\global-metadata.dat', 'rb') as mf:
    meta = mf.read()

hdr = struct.unpack_from('<64I', meta, 0)
str_lit_off, str_lit_sz = hdr[2], hdr[3]
str_lit_data_off, str_lit_data_sz = hdr[4], hdr[5]
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

print('=== StreamedListView (5791) sort/reorder methods ===')
for midx in range(47153, 47153 + 185):
    mu = struct.unpack_from('<7i4H', meta, methods_off + midx * 36)
    mname = get_mstr(mu[0])
    rid = (mu[6] & 0xFFFFFF) - 1
    m_va = struct.unpack_from('<Q', pe, ptrs_off + rid * 8)[0]
    m_rva = m_va - image_base if m_va else 0
    if any(k in mname for k in ('Sort', 'Reorder', 'List', 'Build', 'Bind', 'Dirty', 'State')):
        print(f'  [{midx}] 0x{m_rva:08x} {mname}')

targets = [
    ('get_DisableSorting', 0x015f2190, 0x20),
    ('set_DisableSorting', 0x015f2420, 0x40),
    ('get_SortedColumn', 0x015f2360, 0x20),
    ('set_SortedColumn', 0x015f2930, 0x50),
    ('OnHeaderClicked', 0x015ec910, 0x160),
    ('OnSortColumn', 0x015ee250, 0x40),
    ('MakeColumnHeader', 0x015eac30, 0x250),
    ('SetSorting_1', 0x015efc40, 0xa0),
    ('SetSorting_2', 0x015efce0, 0x290),
    ('TrySetColumnsAndSort', 0x015f0040, 0x260),
    ('UpdateSortColum', 0x015f1380, 0x150),
    ('SetNoSorting', 0x015ef750, 0x90),
]

for name, rva, sz in targets:
    print(f'\n================ {name} (0x{rva:08x}, sz=0x{sz:x}) ================')
    off = va_to_off(image_base + rva)
    code = pe[off : off + sz]
    for k in range(0, len(code), 16):
        chunk = code[k : k + 16]
        print(f'  +0x{k:03x}: ' + ' '.join(f'{b:02x}' for b in chunk))
    for i in range(len(code) - 5):
        if code[i] in (0xE8, 0xE9):
            rel = struct.unpack_from('<i', code, i + 1)[0]
            t = rva + i + 5 + rel
            if 0x1000 <= t < 0x3000000:
                op_s = 'CALL' if code[i] == 0xE8 else 'JMP'
                print(f'  +0x{i:03x}: {op_s} 0x{t:08x} ({rva_to_name.get(t, "")})')
