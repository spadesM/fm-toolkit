"""
FM27 Performans, P-Core/E-Core Hibrit Çekirdek ve Anlık Arayüz Hızlandırıcı
---------------------------------------------------------------------------
Intel Core Ultra 7 155H (Meteor Lake) işlemcide:
- P-Core (Performans Çekirdekleri): Mantıksal CPU 0, 1 ve 10..19 (Bitmask: 0x0FFC03)
- E-Core (Verimlilik Çekirdekleri): Mantıksal CPU 2..9
- LP-E (Düşük Güçlü L3 Önbelleksiz SoC Çekirdekleri): Mantıksal CPU 20, 21

Bu araç:
1. fm.exe çalışırken işlem önceliğini 'High' (Yüksek) yapar.
2. Akıllı Hibrit Çekirdek Dağıtımı uygular:
   - L3 önbelleği olmayan LP-E çekirdeklerini (CPU 20, 21) devre dışı bırakır (Maske: 0x0FFFFF).
   - En çok yük çeken 12 ana Unity UI, GC ve Render iş parçacığını %100 P-Core'lara (0x0FFC03) çiviler.
   - Düşük öncelikli arka plan simülasyon işçi parçacıklarının (Continue / Maç simülasyonu) 8 adet E-Core'dan da
     ek hesaplama gücü olarak yararlanmasına izin verir.
3. Canlı RAM üzerinde PanelLayerSettings ve SaveSettings.s_boolCache tablolarını güncelleyerek
   Menu, Report, Card ve ModalDialog katmanlarındaki 100-400 ms'lik yapay geçiş animasyonlarını
   ve girdi kilitlerini (BlockAllInput) sıfırlar; 3B Regen portre üretim yükünü devre dışı bırakır.
"""

import ctypes
from ctypes import wintypes
import struct
import time
import sys
import subprocess

PROCESS_SET_INFORMATION = 0x0200
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_VM_OPERATION = 0x0008
HIGH_PRIORITY_CLASS = 0x00000080

THREAD_SET_INFORMATION = 0x0020
THREAD_QUERY_INFORMATION = 0x0040
TH32CS_SNAPTHREAD = 0x00000004
TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010

# Intel Core Ultra 7 155H Masks
PROCESS_MASK_HYBRID = 0x0FFFFF   # CPU 0..19 (12 P-Core + 8 E-Core aktif, LP-E CPU 20-21 kapalı)
PCORE_MASK = 0x0FFC03            # CPU 0, 1, 10..19 (6 Fiziksel P-Core / 12 Mantıksal İş Parçacığı)
PCORE_LOGICAL_INDICES = [0, 10, 12, 14, 16, 18, 1, 11, 13, 15, 17, 19]

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

class THREADENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ThreadID", wintypes.DWORD),
        ("th32OwnerProcessID", wintypes.DWORD),
        ("tpBasePri", wintypes.LONG),
        ("tpDeltaPri", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
    ]

class MODULEENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("th32ModuleID", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("GlblcntUsage", wintypes.DWORD),
        ("ProccntUsage", wintypes.DWORD),
        ("modBaseAddr", ctypes.c_void_p),
        ("modBaseSize", wintypes.DWORD),
        ("hModule", wintypes.HMODULE),
        ("szModule", ctypes.c_char * 256),
        ("szExePath", ctypes.c_char * 260),
    ]

class PROCESSOR_NUMBER(ctypes.Structure):
    _fields_ = [
        ("Group", wintypes.WORD),
        ("Number", ctypes.c_ubyte),
        ("Reserved", ctypes.c_ubyte),
    ]

class FILETIME(ctypes.Structure):
    _fields_ = [
        ("dwLowDateTime", wintypes.DWORD),
        ("dwHighDateTime", wintypes.DWORD),
    ]

def filetime_to_int(ft):
    return (ft.dwHighDateTime << 32) | ft.dwLowDateTime

def find_fm_pid():
    out = subprocess.check_output(
        ["tasklist", "/FI", "IMAGENAME eq fm.exe", "/FO", "CSV", "/NH"],
        text=True, encoding="utf-8", errors="ignore"
    ).strip()
    for line in out.splitlines():
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) >= 2 and parts[0].lower() == "fm.exe":
            try:
                return int(parts[1])
            except ValueError:
                pass
    return None

def get_module_base(pid, mod_name):
    snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid)
    if snap == wintypes.HANDLE(-1).value:
        return None
    me = MODULEENTRY32()
    me.dwSize = ctypes.sizeof(MODULEENTRY32)
    base = None
    try:
        if kernel32.Module32First(snap, ctypes.byref(me)):
            while True:
                if me.szModule.decode("latin1", errors="ignore").lower() == mod_name.lower():
                    base = me.modBaseAddr
                    break
                if not kernel32.Module32Next(snap, ctypes.byref(me)):
                    break
    finally:
        kernel32.CloseHandle(snap)
    return base

def patch_live_ui_transitions(pid):
    ga_base = get_module_base(pid, "GameAssembly.dll")
    if not ga_base:
        return 0

    h_proc = kernel32.OpenProcess(
        PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION | PROCESS_QUERY_INFORMATION,
        False, pid
    )
    if not h_proc:
        return 0

    def read_mem(addr, size):
        if not addr or addr < 0x10000:
            return b""
        buf = ctypes.create_string_buffer(size)
        nread = ctypes.c_size_t(0)
        if kernel32.ReadProcessMemory(h_proc, ctypes.c_void_p(addr), buf, size, ctypes.byref(nread)):
            return buf.raw[:nread.value]
        return b""

    def write_mem(addr, data: bytes) -> bool:
        nwritten = ctypes.c_size_t(0)
        ok = kernel32.WriteProcessMemory(h_proc, ctypes.c_void_p(addr), data, len(data), ctypes.byref(nwritten))
        return bool(ok and nwritten.value == len(data))

    def read_u64(addr):
        b = read_mem(addr, 8)
        return struct.unpack("<Q", b)[0] if len(b) == 8 else 0

    def read_il2cpp_string(addr):
        if not addr or addr < 0x10000:
            return None
        b = read_mem(addr + 0x10, 4)
        if len(b) < 4:
            return None
        length = struct.unpack("<i", b)[0]
        if length < 0 or length > 300:
            return None
        raw = read_mem(addr + 0x14, length * 2)
        return raw.decode("utf-16-le", errors="ignore")

    patched_count = 0
    try:
        # 1. Patch SaveSettings.s_boolCache
        code_ss = read_mem(ga_base + 0x018E0B60, 64)
        pos_ss = code_ss.find(b"\x48\x8b\x05")
        if pos_ss != -1:
            disp_ss = struct.unpack_from("<i", code_ss, pos_ss + 3)[0]
            ss_typeinfo_rva = 0x018E0B60 + pos_ss + 7 + disp_ss
            ss_klass = read_u64(ga_base + ss_typeinfo_rva)
            ss_static = read_u64(ss_klass + 0xB8)
            bool_dict = read_u64(ss_static + 0x20)
            entries_arr = read_u64(bool_dict + 0x18)
            count_b = read_mem(bool_dict + 0x20, 4)
            if len(count_b) == 4:
                count = struct.unpack("<i", count_b)[0]
                target_bools = {
                    "AnimateMenus": 0,
                    "AnimateReports": 0,
                    "AnimateCards": 0,
                    "UsePregeneratedNewgenPortraits": 1,
                }
                for i in range(min(count + 5, 60)):
                    entry_addr = entries_arr + 0x20 + i * 24
                    eb = read_mem(entry_addr, 24)
                    if len(eb) == 24:
                        hc, nxt, kptr, val = struct.unpack("<iiQB7x", eb)
                        if hc >= 0 and kptr:
                            kname = read_il2cpp_string(kptr)
                            if kname in target_bools:
                                write_mem(entry_addr + 16, struct.pack("<B", target_bools[kname]))
                                patched_count += 1

        # 2. Patch PanelLayerSettings LayerDescriptions (Menu, Report, Card, ModalDialog)
        code_pls = read_mem(ga_base + 0x01945990, 64)
        pos_pls = code_pls.find(b"\x48\x8b\x05")
        if pos_pls != -1:
            disp_pls = struct.unpack_from("<i", code_pls, pos_pls + 3)[0]
            pls_typeinfo_rva = 0x01945990 + pos_pls + 7 + disp_pls
            pls_klass = read_u64(ga_base + pls_typeinfo_rva)
            pls_static = read_u64(pls_klass + 0xB8)
            pls_instance = read_u64(pls_static + 0)
            layers_arr = read_u64(pls_instance + 0x18)
            lcount_b = read_mem(layers_arr + 0x18, 8)
            if len(lcount_b) == 8:
                lcount = struct.unpack("<Q", lcount_b)[0]
                target_layers = {
                    "MenuTitle", "MenuBody", "Menu",
                    "ReportBody", "Report",
                    "CardBody", "Card",
                    "Tutorial", "ModalDialog",
                }
                for i in range(min(lcount, 30)):
                    pair_addr = layers_arr + 0x20 + i * 24
                    pb = read_mem(pair_addr, 24)
                    if len(pb) == 24:
                        layer_str_ptr, layer_id, desc_ptr = struct.unpack("<QQQ", pb)
                        layer_name = read_il2cpp_string(layer_str_ptr)
                        if layer_name in target_layers and desc_ptr:
                            write_mem(desc_ptr + 0x23, b"\x00\x00")
                            patched_count += 1
    finally:
        kernel32.CloseHandle(h_proc)

    return patched_count

def optimize_fm_process(pid, top_n_threads=12):
    h_proc = kernel32.OpenProcess(PROCESS_SET_INFORMATION | PROCESS_QUERY_INFORMATION, False, pid)
    if not h_proc:
        print(f"[!] fm.exe (PID {pid}) erişilemedi. Hata kodu: {ctypes.get_last_error()}")
        return False

    try:
        # 1. Set High Priority Class
        kernel32.SetPriorityClass(h_proc, HIGH_PRIORITY_CLASS)
        # 2. Hybrid Process Affinity: Allow 12 P-Cores + 8 E-Cores (0x0FFFFF), exclude L3-less LP-E cores (CPU 20, 21)
        kernel32.SetProcessAffinityMask(h_proc, ctypes.c_size_t(PROCESS_MASK_HYBRID))
    finally:
        kernel32.CloseHandle(h_proc)

    # 3. Enumerate all threads of fm.exe and measure their CPU times
    snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
    if snap == wintypes.HANDLE(-1).value:
        return False

    threads = []
    try:
        te = THREADENTRY32()
        te.dwSize = ctypes.sizeof(THREADENTRY32)
        if kernel32.Thread32First(snap, ctypes.byref(te)):
            while True:
                if te.th32OwnerProcessID == pid:
                    tid = te.th32ThreadID
                    ht = kernel32.OpenThread(THREAD_SET_INFORMATION | THREAD_QUERY_INFORMATION, False, tid)
                    if ht:
                        c_ft, e_ft, k_ft, u_ft = FILETIME(), FILETIME(), FILETIME(), FILETIME()
                        if kernel32.GetThreadTimes(ht, ctypes.byref(c_ft), ctypes.byref(e_ft), ctypes.byref(k_ft), ctypes.byref(u_ft)):
                            total_time = filetime_to_int(k_ft) + filetime_to_int(u_ft)
                            threads.append((total_time, tid, te.tpBasePri))
                        kernel32.CloseHandle(ht)
                if not kernel32.Thread32Next(snap, ctypes.byref(te)):
                    break
    finally:
        kernel32.CloseHandle(snap)

    threads.sort(reverse=True)
    pinned = []
    for idx, (cpu_time, tid, base_pri) in enumerate(threads):
        ht = kernel32.OpenThread(THREAD_SET_INFORMATION | THREAD_QUERY_INFORMATION, False, tid)
        if ht:
            try:
                if idx < top_n_threads or base_pri >= 14:
                    # Pin main UI, Render, GC & high-priority threads strictly to P-Cores (0x0FFC03)
                    kernel32.SetThreadAffinityMask(ht, ctypes.c_size_t(PCORE_MASK))
                    target_cpu = PCORE_LOGICAL_INDICES[idx % len(PCORE_LOGICAL_INDICES)]
                    pn = PROCESSOR_NUMBER(0, target_cpu, 0)
                    kernel32.SetThreadIdealProcessorEx(ht, ctypes.byref(pn), None)
                    if len(pinned) < top_n_threads:
                        pinned.append((tid, target_cpu, round(cpu_time / 1e7, 2)))
                else:
                    # Allow background simulation workers to use P-Cores + E-Cores (0x0FFFFF, no LP-E)
                    kernel32.SetThreadAffinityMask(ht, ctypes.c_size_t(PROCESS_MASK_HYBRID))
            finally:
                kernel32.CloseHandle(ht)

    patched_ui = patch_live_ui_transitions(pid)

    print(f"[OK] fm.exe (PID: {pid}) optimize edildi:")
    print(f"     - İşlem Önceliği       : YÜKSEK (High Priority)")
    print(f"     - Hibrit İşlem Maskesi : 0x{PROCESS_MASK_HYBRID:06X} (12 P-Core + 8 E-Core aktif, LP-E CPU 20-21 kapalı)")
    print(f"     - Anlık UI & Portre    : {patched_ui} katman/önbellek ayarı canlı RAM'de sıfır gecikmeye çekildi")
    print(f"     - P-Core Sabitlenen Ana İş Parçacıkları ({len(pinned)} adet, Maske 0x{PCORE_MASK:06X}):")
    for tid, cpu_idx, secs in pinned[:6]:
        print(f"       * Thread {tid:<6d} -> P-Core CPU {cpu_idx:<2d} (CPU Süresi: {secs}s)")
    return True

def main():
    watch_mode = "--watch" in sys.argv
    print("=================================================================")
    print(" FM27 Performans, Hibrit P-Core & Anlık Arayüz Hızlandırıcı")
    print("=================================================================")

    pid = find_fm_pid()
    if not pid and not watch_mode:
        print("[*] fm.exe şu an çalışmıyor. Oyunu başlatmanız bekleniyor (60 sn)...")
        for _ in range(30):
            time.sleep(2)
            pid = find_fm_pid()
            if pid:
                print(f"[*] fm.exe algılandı (PID: {pid})! İş parçacıklarının yüklenmesi için 8 sn bekleniyor...")
                time.sleep(8)
                break

    if pid:
        optimize_fm_process(pid)
        if watch_mode:
            print("[*] İzleme modu aktif. Her 30 saniyede bir P-Core sabitlemesi güncelleniyor...")
            while True:
                time.sleep(30)
                pid = find_fm_pid()
                if not pid:
                    print("[*] Oyun kapatıldı, çıkılıyor.")
                    break
                optimize_fm_process(pid)
    else:
        print("[!] fm.exe bulunamadı. Oyunu açtıktan sonra bu aracı tekrar çalıştırabilirsiniz.")

if __name__ == "__main__":
    main()
