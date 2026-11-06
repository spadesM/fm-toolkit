import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
from fm26save.binary_decompiler import resolve_fm_install_dir

root = resolve_fm_install_dir()
pe = (root / "GameAssembly.dll").read_bytes()
meta = (root / "fm_Data/il2cpp_data/Metadata/global-metadata.dat").read_bytes()

hdr = struct.unpack_from("<64I", meta, 0)
str_off, str_sz = hdr[6], hdr[7]
methods_off, methods_sz = hdr[12], hdr[13]
params_off, params_sz = hdr[16], hdr[17]
fields_off, fields_sz = hdr[24], hdr[25]
types_off, types_sz = hdr[40], hdr[41]
images_off, images_sz = hdr[42], hdr[43]

def get_mstr(off: int) -> str:
    if off < 0 or off >= str_sz:
        return ""
    end = meta.find(b"\x00", str_off + off)
    return meta[str_off + off : end].decode("utf-8", errors="replace")

# Print methods of Bindings, StreamedListView, SortData, SortComparer in SI.Bindable.dll
for img_i in range(images_sz // 40):
    iu = struct.unpack_from("<10i", meta, images_off + img_i * 40)
    iname = get_mstr(iu[0])
    if iname == "SI.Bindable.dll":
        t_start, t_cnt = iu[2], iu[3]
        for ti in range(t_start, t_start + t_cnt):
            tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
            tname = get_mstr(tu[0])
            if tname in ("Bindings", "StreamedListView", "SortData", "SortComparer", "StreamedTable"):
                m_start = tu[9]
                m_cnt = tu[16] & 0xFFFF
                for mi in range(m_start, m_start + m_cnt):
                    mu = struct.unpack_from("<7i4H", meta, methods_off + mi * 36)
                    mname = get_mstr(mu[0])
                    if any(k in mname for k in ("Nth", "Depth", "Bind", "Sort", "Alias", "Set", "Compare", "Cell", "Value", "Received", "Reorder", "Indices")):
                        p_start = mu[4]
                        p_cnt = mu[10]
                        pnames = []
                        for pi in range(p_start, p_start + p_cnt):
                            pu = struct.unpack_from("<3i", meta, params_off + pi * 12)
                            pnames.append(f"{get_mstr(pu[0])}")
                        print(f"{tname}.{mname}({', '.join(pnames)})")

sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
from check_deep_sorting import dump_func_details

dump_func_details("SortComparer.Compare(int,int)", 0x015a3c60, 208)
dump_func_details("SortComparer.Compare(2)", 0x015a3d30, 642)
dump_func_details("SortData..ctor", 0x015a4190, 136)
dump_func_details("SortData.GetCell", 0x015a3fc0, 46)
dump_func_details("SortData.GetValue", 0x015a4000, 43)
dump_func_details("SortData.HasReceived", 0x015a4040, 310)
