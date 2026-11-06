import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

with open(r'C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26\GameAssembly.dll', 'rb') as f:
    pe = f.read()
with open(r'C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26\fm_Data\il2cpp_data\Metadata\global-metadata.dat', 'rb') as mf:
    meta = mf.read()

hdr = struct.unpack_from('<64I', meta, 0)
str_lit_off, str_lit_sz = hdr[2], hdr[3]
str_lit_data_off, str_lit_data_sz = hdr[4], hdr[5]
str_off, str_sz = hdr[6], hdr[7]

def get_lit(idx):
    if 0 <= idx * 8 < str_lit_sz:
        l, d = struct.unpack_from('<II', meta, str_lit_off + idx * 8)
        return meta[str_lit_data_off + d : str_lit_data_off + d + l].decode('utf-8', errors='replace')
    return ''

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

def resolve_rip(va):
    foff = va_to_off(va)
    if foff < 0 or foff + 8 > len(pe): return ''
    val = struct.unpack_from('<I', pe, foff)[0]
    if (val & 1) == 1:
        tag = val >> 29
        idx = (val & 0x1FFFFFFF) >> 1
        if tag == 5:
            return f'STR "{get_lit(idx)}"'
    return ''

md = Cs(CS_ARCH_X86, CS_MODE_64)

def disasm(name, rva, sz):
    print(f'\n=== {name} (0x{rva:08x}, sz=0x{sz:x}) ===')
    off = va_to_off(image_base + rva)
    code = pe[off : off + sz]
    for insn in md.disasm(code, rva):
        comment = ''
        if '[rip +' in insn.op_str:
            try:
                disp = int(insn.op_str.split('[rip + ')[1].split(']')[0], 16)
                target_va = image_base + insn.address + insn.size + disp
                s = resolve_rip(target_va)
                if s: comment = f' ; {s}'
            except Exception:
                pass
        print(f'  0x{insn.address:08x}: {insn.mnemonic:8s} {insn.op_str}{comment}')

disasm('StreamedTable.<OnBindItem>g__SetBindings|221_0', 0x015f0580, 0x2f0)
disasm('StreamedListView.<ApplySorting>g__SetupRow|246_0', 0x015aa320, 0x260)
disasm('StreamedListView.BindSortPathNextDepth', 0x015a4850, 0x160)
disasm('StreamedListView.ProcessSortingDataChanged', 0x015a8cb0, 0x240)
disasm('Bindings.GetNthProperty', 0x014c1450, 0x1e0)
disasm('SpecificallyScoutedPersonReference.GetPropertyInternal', 0x00696ef0, 0x350)
