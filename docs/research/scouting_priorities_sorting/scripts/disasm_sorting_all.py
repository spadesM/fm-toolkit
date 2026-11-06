import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

with open(r'C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\parse_il2cpp_metadata.py') as f:
    code = f.read().split('# Now let\'s find')[0]
exec(code)

rva_to_names = {}
for ti in range(num_types):
    t_name, t_ns, m_first, m_count = get_type_info(ti)
    for mi in range(m_first, m_first + m_count):
        m_name, m_rva = get_method_info(mi)
        if m_rva > 0:
            rva_to_names.setdefault(m_rva, []).append(f"{t_name}.{m_name}")

# Find all methods in StreamedListView and StreamedTable with 'Reorder' or 'Sort' or 'Drag'
for ti in range(num_types):
    t_name, t_ns, m_first, m_count = get_type_info(ti)
    if t_name in ('StreamedListView', 'StreamedTable', 'VirtualisedList'):
        for mi in range(m_first, m_first + m_count):
            m_name, m_rva = get_method_info(mi)
            if any(k in m_name.lower() for k in ['reorder', 'sort', 'drag', 'header']):
                print(f"  0x{m_rva:08x}: {t_name}.{m_name}")

# Check MetaUsage(tag=2, idx=32982) and others
for tag, idx in [(2, 32982), (1, 12128), (1, 23676), (1, 36675), (1, 34369), (6, 135236), (6, 197770), (6, 197775), (6, 198044)]:
    if tag in (1, 2):
        # type index in Il2CppType table
        print(f"MetaUsage(tag={tag}, idx={idx})")

md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

def disasm(name, rva, size=600):
    off = rva_to_offset(rva)
    code_bytes = pe[off:off+size]
    print(f"\n================ {name} (RVA=0x{rva:08x}) ================")
    for insn in md.disasm(code_bytes, rva):
        rel = insn.address - rva
        ann = ""
        if insn.mnemonic in ('call', 'jmp') and insn.operands[0].type == 2:
            target = insn.operands[0].imm
            names = rva_to_names.get(target, [])
            ann = f" -> {', '.join(names[:3])}"
        for op in insn.operands:
            if op.type == 3 and op.mem.base == 41:
                target = insn.address + insn.size + op.mem.disp
                if target in addr_to_usage:
                    kind, info = addr_to_usage[target]
                    if kind == 'str_lit':
                        ann += f" [STR {repr(get_str_lit(info))}]"
                    else:
                        ann += f" [Meta{info}]"
        print(f"  +0x{rel:03x}: {insn.mnemonic:8s} {insn.op_str}{ann}")
        if insn.mnemonic == 'ret' and rel > 0x20:
            # keep going a bit in case of early return
            pass

disasm("StreamedListView.set_Reorderable", 0x015ad4f0, 200)
disasm("StreamedListView.ApplySorting", 0x015a4260, 700)
disasm("StreamedListView.HasSorting", 0x015a5f20, 200)
disasm("StreamedTable.TrySetColumnsAndSort", 0x015f0040, 520)
disasm("StreamedTable.MakeColumnHeader", 0x015eac30, 1000)
disasm("StreamedTable.OnHeaderClicked", 0x015ec910, 600)
disasm("StreamedTable.SetSorting(1)", 0x015efc40, 200)
disasm("StreamedTable.SetSorting(2)", 0x015efce0, 600)
