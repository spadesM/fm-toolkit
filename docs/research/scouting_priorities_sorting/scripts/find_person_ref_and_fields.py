import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as dhf

meta = dhf.meta
hdr = dhf.hdr
methods_off, methods_sz = hdr[12], hdr[13]
fields_off, fields_sz = hdr[28], hdr[29]
types_off, types_sz = hdr[40], hdr[41]
images_off, images_sz = hdr[42], hdr[43]

num_images = images_sz // 40
def find_image_for_type(td_idx):
    for i in range(num_images):
        off = images_off + i * 40
        name_idx, asm_idx, t_start, t_count = struct.unpack_from("<IIII", meta, off)
        if t_start <= td_idx < t_start + t_count:
            return dhf.get_mstr(name_idx)
    return None

# Find CodeRegistration in GameAssembly.dll
pe = dhf.pe
pattern = struct.pack("<I", 412516)
pos = 0
mods_rva = 0
mods_count = 0
while True:
    idx = pe.find(pattern, pos)
    if idx == -1: break
    pos = idx + 1
    if idx >= 112:
        cand = struct.unpack_from("<16Q", pe, idx - 112)
        if 50 < cand[12] < 500:
            mods_count = cand[12]
            mods_rva = cand[13] - dhf.image_base
            break

for target_type in ["SpecificallyScoutedPersonReference", "SpecificallyScoutedTeamReference", "StreamedListView", "StreamedTable"]:
    for td_idx in range(types_sz // 88):
        td_off = types_off + td_idx * 88
        tu = struct.unpack_from("<22i", meta, td_off)
        tname = dhf.get_mstr(tu[0])
        if tname == target_type:
            img_name = find_image_for_type(td_idx)
            first_field = tu[7]
            first_method = tu[8]
            f_count = tu[16] & 0xFFFF
            m_count = (tu[16] >> 16) & 0xFFFF
            # Wait, let's check tu indices from previous script
            first_field, first_method = tu[6], tu[7]
            f_count = tu[16] & 0xFFFF
            print(f"=== Type {tname} (td={td_idx}, image={img_name}, tu={tu[:18]}) ===")
            for f_i in range(tu[6], tu[6] + (tu[16] & 0xFFFF)):
                f_name_idx, f_type_idx, f_token = struct.unpack_from("<iii", meta, fields_off + f_i * 12)
                print(f"  Field [{f_i - tu[6]}]: {dhf.get_mstr(f_name_idx)}")
            cgm_rva = None
            for m_idx in range(mods_count):
                ptr_va = struct.unpack_from("<Q", pe, dhf.va_to_off(dhf.image_base + mods_rva + m_idx * 8))[0]
                m_rva = ptr_va - dhf.image_base
                str_va = struct.unpack_from("<Q", pe, dhf.va_to_off(dhf.image_base + m_rva))[0]
                s_off = dhf.va_to_off(str_va)
                end = pe.find(b"\x00", s_off)
                mname = pe[s_off:end].decode("utf-8", errors="ignore")
                if mname == img_name:
                    cgm_rva = m_rva
                    break
            if cgm_rva and target_type in ("SpecificallyScoutedPersonReference", "SpecificallyScoutedTeamReference"):
                mp_count, mp_va = struct.unpack_from("<QQ", pe, dhf.va_to_off(dhf.image_base + cgm_rva + 8))
                mp_rva = mp_va - dhf.image_base
                # Find methods whose declaringType == td_idx
                for m_i in range(methods_sz // 36):
                    mu = struct.unpack_from("<7i4H", meta, methods_off + m_i * 36)
                    if mu[2] == td_idx:
                        m_token = mu[6]
                        rid = (m_token & 0x00FFFFFF) - 1
                        fn_va = struct.unpack_from("<Q", pe, dhf.va_to_off(dhf.image_base + mp_rva + rid * 8))[0]
                        fn_rva = fn_va - dhf.image_base if fn_va else 0
                        print(f"  Method {dhf.get_mstr(mu[0])}: RVA=0x{fn_rva:08x}")
