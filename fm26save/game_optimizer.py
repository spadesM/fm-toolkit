"""Football Manager 27 / 26 Game Optimization Suite & Pre-Game Rules (.edt / .lnc / .dbc) Editor.

Covers:
1. Pillar 2 — Game Optimization:
   - ``fm_Data/boot.config`` parser, preset engine, and live key-value editor with ``.bak`` backup.
   - URP rendering & simulation pipeline inspector.
   - Disk & memory footprint breakdown across installation folders, intro/promo ``.webm`` video
     bypass toggles, and historical database version footprint analysis.
2. Pillar 3 (Pre-Game Rules & Licensing):
   - Visual Sugar Daddy editor (``sugardaddy.edt``: ``FRONT_END``, ``BACK_END``, ``UNDERWRITER``).
   - Transfer Embargo (``transfer_embargo.edt``) & Administration (``start_in_admin.edt``) editors.
   - UTF-16LE / UTF-8 BOM-preserving ``.lnc`` and ``.edt`` editor.
   - 1-click Licensing & Fake Name unlocker for ``.dbc`` and ``.lnc`` files (``germany.dbc``,
     ``japan_fake.dbc``, ``1_japan_removed_clubs.dbc``, ``brazil_kits.dbc``, ``fm_27_italy_kits.dbc``,
     ``licensing_fm27.dbc``, ``Licensing2.dbc``, ``fake.lnc``, ``fake.edt``).
"""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Any

BOOT_CONFIG_KNOWN_KEYS: list[dict[str, Any]] = [
    {
        "key": "job-worker-count",
        "category": "CPU & Job System",
        "default": "",
        "type": "int_optional",
        "title_tr": "Unity Job System İşçi Çekirdek Sayısı (job-worker-count)",
        "title_en": "Unity Job System Worker Thread Count (job-worker-count)",
        "desc_tr": "Simülasyon ve UI akışı için kullanılan paralel iş parçacığı sayısı (Boş = Otomatik, önerilen: Mantıksal Çekirdek - 2).",
        "desc_en": "Parallel worker threads for simulation & UI streaming (Empty = Auto, recommended: Logical Cores - 2).",
    },
    {
        "key": "job-worker-maximum-count",
        "category": "CPU & Job System",
        "default": "",
        "type": "int_optional",
        "title_tr": "Maksimum Job Worker Üst Sınırı (job-worker-maximum-count)",
        "title_en": "Job Worker Maximum Cap (job-worker-maximum-count)",
        "desc_tr": "Yoğun haftalık simülasyon anlarında Job System'in açabileceği tavan iş parçacığı sayısı (Örn: 16 veya 24).",
        "desc_en": "Upper ceiling of worker threads Unity Job System can spawn during peak simulation bursts.",
    },
    {
        "key": "scripting-runtime-version",
        "category": "CPU & Job System",
        "default": "latest",
        "type": "text",
        "title_tr": "IL2CPP Çalışma Zamanı Sürümü (scripting-runtime-version)",
        "title_en": "IL2CPP Scripting Runtime Version",
        "desc_tr": "IL2CPP yürütme çalışma zamanı profili (Varsayılan: latest).",
        "desc_en": "IL2CPP execution runtime profile (Default: latest).",
    },
    {
        "key": "gc-max-time-slice",
        "category": "Bellek & Garbage Collector",
        "default": "3",
        "type": "int",
        "title_tr": "Artımlı Bellek Temizleyici (GC) Maksimum Dilim Süresi (ms)",
        "title_en": "Incremental GC Max Time Slice (ms)",
        "desc_tr": "Kare başına Garbage Collector'a ayrılan maksimum milisaniye (1 ms = en akıcı maç motoru, 3-5 ms = hızlı ekran geçişi).",
        "desc_en": "Maximum milliseconds per frame spent on incremental garbage collection (1-3 ms reduces micro-stutter).",
    },
    {
        "key": "call-ondisable-when-unloaded-from-bundles",
        "category": "Bellek & Garbage Collector",
        "default": "1",
        "type": "bool01",
        "title_tr": "Bundle Boşaltılırken OnDisable Çağrısı",
        "title_en": "Call OnDisable When Unloaded From Bundles",
        "desc_tr": "UI ve sahne bundle'ları bellekten boşaltılırken temizlik geri çağrısını çalıştırır (1 = Bellek sızıntısını önler).",
        "desc_en": "Runs cleanup callbacks when UI/scene bundles unload (1 = Prevents memory leaks).",
    },
    {
        "key": "gfx-enable-gfx-jobs",
        "category": "GPU & Direct3D Render",
        "default": "1",
        "type": "bool01",
        "title_tr": "Çok İş Parçacıklı Grafik İş Kuyruğu (gfx-enable-gfx-jobs)",
        "title_en": "Multi-Threaded Graphics Jobs (gfx-enable-gfx-jobs)",
        "desc_tr": "Unity render komutlarının birden fazla CPU çekirdeğine dağıtılmasını sağlar (1 = Açık, 0 = Kapalı).",
        "desc_en": "Distributes Unity render command generation across worker threads (1 = Enabled).",
    },
    {
        "key": "gfx-enable-native-gfx-jobs",
        "category": "GPU & Direct3D Render",
        "default": "1",
        "type": "bool01",
        "title_tr": "Yerel (Native) Grafik İş Parçacıkları (gfx-enable-native-gfx-jobs)",
        "title_en": "Native Graphics Jobs (gfx-enable-native-gfx-jobs)",
        "desc_tr": "D3D11/D3D12/Vulkan sürücüsüne yerel C++ iş parçacıklarından doğrudan görev gönderir (1 = Açık).",
        "desc_en": "Submits rendering tasks directly from native C++ worker threads (1 = Enabled).",
    },
    {
        "key": "gfx-threading-mode",
        "category": "GPU & Direct3D Render",
        "default": "6",
        "type": "int",
        "title_tr": "Unity Grafik İş Parçacığı Kipi (gfx-threading-mode)",
        "title_en": "Unity Graphics Threading Mode (gfx-threading-mode)",
        "desc_tr": "Unity 6000.3 dahili render iş parçacığı kipi (FM27 varsayılanı: 6 = Split/Native Jobs, 4 = MultiThreaded).",
        "desc_en": "Unity 6000.3 internal render threading mode (FM27 default: 6 = Split/Native Jobs).",
    },
    {
        "key": "disable-gpu-skinning",
        "category": "GPU & Direct3D Render",
        "default": "0",
        "type": "bool01",
        "title_tr": "GPU İskelet Animasyonunu Devre Dışı Bırak (disable-gpu-skinning)",
        "title_en": "Disable GPU Skinning (disable-gpu-skinning)",
        "desc_tr": "0 = 3D maç motorunda oyuncu iskelet animasyonlarını GPU üzerinde işler (Önerilen: 0; eski GPU'larda 1).",
        "desc_en": "0 = Processes 3D match player skeleton skinning on GPU (Recommended: 0).",
    },
    {
        "key": "force-d3d11-blt-model",
        "category": "GPU & Direct3D Render",
        "default": "0",
        "type": "bool01",
        "title_tr": "D3D11 Blt Sunum Modelini Zorla (force-d3d11-blt-model)",
        "title_en": "Force D3D11 Blt Swapchain Model",
        "desc_tr": "Pencereli modda G-Sync/FreeSync titremesi yaşıyorsanız 1 yaparak klasik BitBlt takas zincirini kullanabilirsiniz.",
        "desc_en": "Set to 1 if experiencing windowed G-Sync/FreeSync flicker.",
    },
    {
        "key": "hdr-display-enabled",
        "category": "Pencere, HDR & Sistem",
        "default": "0",
        "type": "bool01",
        "title_tr": "HDR Ekran Çıkışı Desteği (hdr-display-enabled)",
        "title_en": "HDR Display Output (hdr-display-enabled)",
        "desc_tr": "Destekleyen monitörlerde yüksek dinamik aralık (HDR) çıktısını etkinleştirir (1 = Açık, 0 = Kapalı).",
        "desc_en": "Enables High Dynamic Range display output on supported monitors.",
    },
    {
        "key": "vr-enabled",
        "category": "Pencere, HDR & Sistem",
        "default": "0",
        "type": "bool01",
        "title_tr": "VR Alt Sistemi (vr-enabled)",
        "title_en": "VR Subsystem (vr-enabled)",
        "desc_tr": "0 = VR başlatma kontrollerini kapatarak oyun açılış süresini kısaltır.",
        "desc_en": "0 = Disables VR subsystem initialization checks for faster game startup.",
    },
    {
        "key": "single-instance",
        "category": "Pencere, HDR & Sistem",
        "default": "",
        "type": "bool01_optional",
        "title_tr": "Tek Örnek Kilidi (single-instance)",
        "title_en": "Single Instance Lock (single-instance)",
        "desc_tr": "1 = Aynı anda yalnızca tek bir fm.exe çalışmasına izin verir; boş/0 = birden fazla örnek açılabilir.",
        "desc_en": "1 = Restricts to a single running fm.exe instance.",
    },
    {
        "key": "wait-for-native-debugger",
        "category": "Tanılama & Profiler",
        "default": "0",
        "type": "bool01",
        "title_tr": "Native Debugger Beklemesi (wait-for-native-debugger)",
        "title_en": "Wait For Native Debugger",
        "desc_tr": "Açılışta yerel hata ayıklayıcı bekler (Normal kullanımda mutlaka 0 olmalıdır).",
        "desc_en": "Waits for a native debugger on startup (Should always be 0 in normal use).",
    },
    {
        "key": "player-connection-debug",
        "category": "Tanılama & Profiler",
        "default": "0",
        "type": "bool01",
        "title_tr": "Unity Player Bağlantı Hata Ayıklaması (player-connection-debug)",
        "title_en": "Unity Player Connection Debug",
        "desc_tr": "0 = Arka planda ağ/debug soketi dinlemesini kapatır.",
        "desc_en": "0 = Disables background debug socket listener.",
    },
    {
        "key": "profiler-enable",
        "category": "Tanılama & Profiler",
        "default": "0",
        "type": "bool01",
        "title_tr": "Dahili Profiler Kaydı (profiler-enable)",
        "title_en": "Internal Profiler Recording",
        "desc_tr": "0 = Performans ek yükünü önlemek için dahili profiler'ı kapalı tutar.",
        "desc_en": "0 = Keeps internal profiler disabled to avoid CPU overhead.",
    },
]


def _boot_config_path(fm_dir: Path) -> Path:
    return fm_dir / "fm_Data/boot.config"


def _build_known_keys_schema() -> dict[str, dict[str, Any]]:
    schema: dict[str, dict[str, Any]] = {}
    for item in BOOT_CONFIG_KNOWN_KEYS:
        d = dict(item)
        d["label_tr"] = item.get("title_tr", item["key"])
        d["label_en"] = item.get("title_en", item["key"])
        schema[item["key"]] = d
    return schema


def read_boot_config(fm_dir: Path) -> dict[str, Any]:
    """Read and parse ``fm_Data/boot.config`` along with hardware recommendations."""
    path = _boot_config_path(fm_dir)
    bak = path.with_name(path.name + ".bak")
    cpu_threads = os.cpu_count() or 8
    recommended_workers = max(2, cpu_threads - 2)
    schema = _build_known_keys_schema()
    if not path.exists():
        return {
            "exists": False,
            "path": str(path),
            "backup_exists": False,
            "raw": "",
            "raw_text": "",
            "values": {},
            "known_keys": BOOT_CONFIG_KNOWN_KEYS,
            "known_keys_schema": schema,
            "cpu_logical_cores": cpu_threads,
            "recommended_job_workers": recommended_workers,
        }
    raw = path.read_text(encoding="utf-8", errors="replace")
    values: dict[str, str] = {}
    for line in raw.splitlines():
        line_s = line.strip()
        if not line_s or line_s.startswith("#"):
            continue
        if "=" in line_s:
            k, v = line_s.split("=", 1)
            values[k.strip()] = v.strip()
    return {
        "exists": True,
        "path": str(path),
        "backup_exists": bak.exists(),
        "raw": raw,
        "raw_text": raw,
        "values": values,
        "known_keys": BOOT_CONFIG_KNOWN_KEYS,
        "known_keys_schema": schema,
        "cpu_logical_cores": cpu_threads,
        "recommended_job_workers": recommended_workers,
    }


def write_boot_config(fm_dir: Path, updates: dict[str, Any], raw_text: str | None = None) -> dict[str, Any]:
    """Update ``fm_Data/boot.config`` with automatic ``.bak`` backup."""
    path = _boot_config_path(fm_dir)
    if not path.exists():
        raise FileNotFoundError(f"boot.config not found at {path}")
    bak = path.with_name(path.name + ".bak")
    if not bak.exists():
        shutil.copy2(path, bak)

    if raw_text is not None:
        path.write_text(raw_text.strip() + "\n", encoding="utf-8")
        return read_boot_config(fm_dir)

    cur = read_boot_config(fm_dir)["values"]
    for k, v in updates.items():
        ks = str(k).strip()
        if not ks:
            continue
        if v is None or str(v).strip() == "":
            cur.pop(ks, None)
        else:
            cur[ks] = str(v).strip()

    lines = [f"{k}={v}" for k, v in cur.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return read_boot_config(fm_dir)


def apply_boot_preset(fm_dir: Path, preset: str) -> dict[str, Any]:
    """Apply a curated optimization preset to ``fm_Data/boot.config``."""
    cpu_threads = os.cpu_count() or 8
    rec_workers = max(2, cpu_threads - 2)
    max_workers = max(4, cpu_threads)
    presets: dict[str, dict[str, Any]] = {
        "default": {
            "gfx-enable-gfx-jobs": "1",
            "gfx-enable-native-gfx-jobs": "1",
            "wait-for-native-debugger": "0",
            "hdr-display-enabled": "0",
            "gc-max-time-slice": "3",
            "job-worker-count": "",
            "job-worker-maximum-count": "",
            "vr-enabled": "",
        },
        "balanced": {
            "gfx-enable-gfx-jobs": "1",
            "gfx-enable-native-gfx-jobs": "1",
            "wait-for-native-debugger": "0",
            "hdr-display-enabled": "0",
            "gc-max-time-slice": "2",
            "job-worker-count": "",
            "vr-enabled": "0",
            "player-connection-debug": "0",
            "profiler-enable": "0",
        },
        "max_fps_multicore": {
            "gfx-enable-gfx-jobs": "1",
            "gfx-enable-native-gfx-jobs": "1",
            "wait-for-native-debugger": "0",
            "hdr-display-enabled": "0",
            "gc-max-time-slice": "2",
            "job-worker-count": str(rec_workers),
            "job-worker-maximum-count": str(max_workers),
            "vr-enabled": "0",
            "player-connection-debug": "0",
            "profiler-enable": "0",
        },
        "low_latency": {
            "gfx-enable-gfx-jobs": "1",
            "gfx-enable-native-gfx-jobs": "1",
            "wait-for-native-debugger": "0",
            "hdr-display-enabled": "0",
            "gc-max-time-slice": "1",
            "job-worker-count": str(rec_workers),
            "vr-enabled": "0",
            "player-connection-debug": "0",
            "profiler-enable": "0",
        },
        "low_latency_max_fps": {
            "gfx-enable-gfx-jobs": "1",
            "gfx-enable-native-gfx-jobs": "1",
            "wait-for-native-debugger": "0",
            "hdr-display-enabled": "0",
            "gc-max-time-slice": "1",
            "job-worker-count": str(rec_workers),
            "job-worker-maximum-count": str(max_workers),
            "vr-enabled": "0",
            "player-connection-debug": "0",
            "profiler-enable": "0",
        },
        "fast_simulation_multicore": {
            "gfx-enable-gfx-jobs": "1",
            "gfx-enable-native-gfx-jobs": "1",
            "wait-for-native-debugger": "0",
            "hdr-display-enabled": "0",
            "gc-max-time-slice": "4",
            "job-worker-count": str(rec_workers),
            "job-worker-maximum-count": str(max_workers),
            "vr-enabled": "0",
            "player-connection-debug": "0",
            "profiler-enable": "0",
        },
        "low_vram_laptop": {
            "gfx-enable-gfx-jobs": "1",
            "gfx-enable-native-gfx-jobs": "0",
            "wait-for-native-debugger": "0",
            "hdr-display-enabled": "0",
            "gc-max-time-slice": "3",
            "job-worker-count": str(max(2, cpu_threads // 2)),
            "vr-enabled": "0",
            "call-ondisable-when-unloaded-from-bundles": "1",
            "player-connection-debug": "0",
            "profiler-enable": "0",
        },
    }
    if preset not in presets:
        raise ValueError(f"Unknown preset {preset!r}; choose from {list(presets)}")
    return write_boot_config(fm_dir, presets[preset])


def restore_boot_config(fm_dir: Path) -> dict[str, Any]:
    """Restore ``fm_Data/boot.config`` from ``boot.config.bak``."""
    path = _boot_config_path(fm_dir)
    bak = path.with_name(path.name + ".bak")
    if bak.exists():
        shutil.copy2(bak, path)
    return read_boot_config(fm_dir)


def _find_db_root(fm_dir: Path) -> Path:
    for cand in (fm_dir / "shared/data/database/db", fm_dir / "data/database/db"):
        if cand.exists():
            return cand
    return fm_dir / "shared/data/database/db"


def inspect_disk_and_optimization_state(fm_dir: Path) -> dict[str, Any]:
    """Inspect installation disk usage, video/promo bundles, historical DBs, and URP graphics profile."""
    aa_dir = fm_dir / "fm_Data/StreamingAssets/aa/StandaloneWindows64"
    videos: list[dict[str, Any]] = []
    if aa_dir.exists():
        for p in sorted(aa_dir.iterdir()):
            if p.name.startswith(("videos_", "promobanner_")) and (p.name.endswith(".bundle") or p.name.endswith(".bundle.disabled")):
                is_disabled = p.name.endswith(".disabled")
                base_name = p.name[: -len(".disabled")] if is_disabled else p.name
                videos.append({
                    "name": base_name,
                    "filename": p.name,
                    "size_mb": round(p.stat().st_size / (1024 * 1024), 2),
                    "disabled": is_disabled,
                    "status": "disabled" if is_disabled else "active",
                })

    db_root = _find_db_root(fm_dir)
    db_versions: list[dict[str, Any]] = []
    if db_root.exists():
        for d in sorted(db_root.iterdir()):
            if d.is_dir():
                files = [f for f in d.rglob("*") if f.is_file()]
                total_bytes = sum(f.stat().st_size for f in files)
                db_versions.append({
                    "version": d.name,
                    "file_count": len(files),
                    "size_mb": round(total_bytes / (1024 * 1024), 2),
                    "is_latest": d.name in ("2700", "2630"),
                })

    # Compute top-level subdirectory disk footprint
    subdirs_info: list[dict[str, Any]] = []
    total_dir_bytes = 0
    if fm_dir.exists():
        for child in sorted(fm_dir.iterdir()):
            try:
                if child.is_file():
                    sz = child.stat().st_size
                    total_dir_bytes += sz
                elif child.is_dir():
                    cfiles = [f for f in child.rglob("*") if f.is_file()]
                    sz = sum(f.stat().st_size for f in cfiles)
                    total_dir_bytes += sz
                    subdirs_info.append({
                        "name": child.name,
                        "files": len(cfiles),
                        "size_mb": round(sz / (1024 * 1024), 1),
                    })
            except OSError:
                continue
    subdirs_info.sort(key=lambda r: r["size_mb"], reverse=True)

    # Check active .bak files across the installation
    bak_files: list[dict[str, Any]] = []
    for sub in ("fm_Data/boot.config.bak", "fm_Data/Plugins/x86_64/game_plugin.dll.bak"):
        bp = fm_dir / sub
        if bp.exists():
            bak_files.append({"path": sub, "size_mb": round(bp.stat().st_size / (1024 * 1024), 2)})
    if aa_dir.exists():
        for bp in sorted(aa_dir.glob("*.bak")):
            bak_files.append({
                "path": f"StreamingAssets/aa/StandaloneWindows64/{bp.name}",
                "size_mb": round(bp.stat().st_size / (1024 * 1024), 2),
            })

    urp_profiles = [
        {
            "profile": "URP-HighFidelity (Yüksek Kalite)",
            "tier": "URP-HighFidelity (Yüksek Kalite)",
            "bundle": "MSAA 4x • Scale 1.0 • 150m Gölge",
            "srp_batcher": True,
            "dynamic_batching": False,
            "msaa": "4x",
            "render_scale": 1.0,
            "upscaling_filter": "FSR 1.0 (Sharpness 0.92)",
            "shadow_distance": "150m (4 Cascades)",
            "additional_lights_limit": 8,
        },
        {
            "profile": "URP-Balanced (Dengeli)",
            "tier": "URP-Balanced (Dengeli)",
            "bundle": "MSAA 2x • Scale 1.0 • 80m Gölge",
            "srp_batcher": True,
            "dynamic_batching": False,
            "msaa": "2x",
            "render_scale": 1.0,
            "upscaling_filter": "Bilinear / FSR",
            "shadow_distance": "80m (2 Cascades)",
            "additional_lights_limit": 4,
        },
        {
            "profile": "URP-Performant (Maksimum FPS / Laptop)",
            "tier": "URP-Performant (Maksimum FPS / Laptop)",
            "bundle": "MSAA 1x • Scale 0.85 • 40m Gölge",
            "srp_batcher": True,
            "dynamic_batching": False,
            "msaa": "1x (Kapalı)",
            "render_scale": 0.85,
            "upscaling_filter": "FSR 1.0",
            "shadow_distance": "40m (1 Cascade)",
            "additional_lights_limit": 2,
        },
    ]

    disabled_cnt = sum(1 for v in videos if v["disabled"])
    active_cnt = len(videos) - disabled_cnt

    return {
        "fm_dir": str(fm_dir),
        "boot_config": read_boot_config(fm_dir),
        "videos": videos,
        "videos_total_mb": round(sum(v["size_mb"] for v in videos), 2),
        "videos_disabled_count": disabled_cnt,
        "intro_videos": {
            "videos": videos,
            "bypass_active": disabled_cnt > 0 and active_cnt == 0,
            "active_count": active_cnt,
            "disabled_count": disabled_cnt,
        },
        "disk_footprint": {
            "total_gb": round(total_dir_bytes / (1024 ** 3), 2),
            "subdirectories": subdirs_info,
        },
        "db_versions": db_versions,
        "backups": bak_files,
        "urp_profiles": urp_profiles,
        "urp_quality_tiers": urp_profiles,
    }


def toggle_intro_videos(fm_dir: Path, disable: bool, video_names: list[str] | None = None) -> dict[str, Any]:
    """Safely enable or disable video/promo bundles by renaming ``<name>.bundle`` <-> ``<name>.bundle.disabled``."""
    aa_dir = fm_dir / "fm_Data/StreamingAssets/aa/StandaloneWindows64"
    if not aa_dir.exists():
        raise FileNotFoundError(f"Addressables folder not found: {aa_dir}")
    target_set = set(video_names) if video_names else None
    changed = 0
    for p in sorted(aa_dir.iterdir()):
        if not p.name.startswith(("videos_", "promobanner_")):
            continue
        if p.name.endswith(".bundle"):
            base = p.name
            if target_set is not None and base not in target_set:
                continue
            if disable:
                p.rename(p.with_name(p.name + ".disabled"))
                changed += 1
        elif p.name.endswith(".bundle.disabled"):
            base = p.name[: -len(".disabled")]
            if target_set is not None and base not in target_set:
                continue
            if not disable:
                p.rename(p.with_name(base))
                changed += 1
    state = inspect_disk_and_optimization_state(fm_dir)
    state["changed_count"] = changed
    return state


# ==============================================================================
# Pillar 3 — Pre-Game .edt, .lnc, and .dbc Rules & Licensing Manager
# ==============================================================================

DBC_LICENSING_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "germany.dbc": {
        "tr": "Almanya Milli Takımı sahte oyuncu/kadro kısıtlaması (Devre dışı bırakıldığında gerçek oyuncular seçilir)",
        "en": "Germany National Team fake player restriction (Disabling unlocks real German national team calls)",
    },
    "japan_fake.dbc": {
        "tr": "Japonya Milli Takımı ve J-League sahte isim kısıtlaması",
        "en": "Japan National Team & club fake name restriction",
    },
    "1_japan_removed_clubs.dbc": {
        "tr": "Japonya kaldırılan kulüp lisans kısıtlamaları",
        "en": "Japan removed clubs licensing restriction",
    },
    "licensing_fm27.dbc": {
        "tr": "FM27 kulüp/turnuva ad ve logo lisans kısıtlamaları",
        "en": "FM27 club/competition name and logo licensing restrictions",
    },
    "Licensing2.dbc": {
        "tr": "İkincil kulüp/lig lisans kısıtlamaları (İtalya/Brezilya/Avrupa kulüp kısaltmaları)",
        "en": "Secondary club/league licensing restrictions",
    },
    "Licensing2_chn.dbc": {
        "tr": "Bölgesel (CHN) lisans kısıtlamaları",
        "en": "Regional (CHN) licensing restrictions",
    },
    "brazil_kits.dbc": {
        "tr": "Brezilya kulüpleri forma/renk lisans kısıtlaması",
        "en": "Brazilian clubs kit/color licensing restriction",
    },
    "fm_27_italy_kits.dbc": {
        "tr": "İtalya Serie A kulüpleri forma lisans kısıtlaması",
        "en": "Italy Serie A clubs kit licensing restriction",
    },
    "fake.lnc": {
        "tr": "Sahte milli takım ve turnuva/kulüp isim zorlamaları (FAKE_NATIONAL_TEAM)",
        "en": "Fake national team and competition/club name overrides (FAKE_NATIONAL_TEAM)",
    },
    "fake.edt": {
        "tr": "Sahte personel/gazeteci eklentileri",
        "en": "Fake staff/journalist entries",
    },
    "person_name_changes.lnc": {
        "tr": "Kişi isim değişiklikleri (.lnc kuralları)",
        "en": "Person name changes (.lnc rules)",
    },
}


def _latest_db_version_dir(fm_dir: Path, db_version: str | None = None) -> Path:
    db_root = _find_db_root(fm_dir)
    if not db_root.exists():
        raise FileNotFoundError(f"Database root not found: {db_root}")
    if db_version and (db_root / db_version).exists():
        return db_root / db_version
    for candidate in ("2700", "2630", "2620", "2600"):
        if (db_root / candidate).exists():
            return db_root / candidate
    dirs = sorted([d for d in db_root.iterdir() if d.is_dir()])
    if not dirs:
        raise FileNotFoundError(f"No DB version directories inside {db_root}")
    return dirs[-1]


def _read_text_auto_encoding(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    if raw.startswith(b"\xff\xfe"):
        return raw.decode("utf-16-le", errors="replace").lstrip("\ufeff"), "utf-16-le-bom"
    if raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16-be", errors="replace").lstrip("\ufeff"), "utf-16-be-bom"
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw[3:].decode("utf-8", errors="replace"), "utf-8-sig"
    return raw.decode("utf-8", errors="replace"), "utf-8"


def _write_text_preserve_encoding(path: Path, content: str, encoding_tag: str) -> None:
    if encoding_tag == "utf-16-le-bom":
        path.write_bytes(b"\xff\xfe" + content.encode("utf-16-le"))
    elif encoding_tag == "utf-16-be-bom":
        path.write_bytes(b"\xfe\xff" + content.encode("utf-16-be"))
    elif encoding_tag == "utf-8-sig":
        path.write_bytes(b"\xef\xbb\xbf" + content.encode("utf-8"))
    else:
        path.write_bytes(content.encode("utf-8"))


def _find_sugardaddy_path(vdir: Path) -> Path:
    for rel in (
        "edt/permanent/sugardaddy.edt",
        "edt/sugardaddy.edt",
        "edt/permanent/sugardaddy.edt.disabled",
        "edt/sugardaddy.edt.disabled",
    ):
        cand = vdir / rel
        if cand.exists():
            return cand
    return vdir / "edt/permanent/sugardaddy.edt"


def list_edt_lnc_dbc_files(fm_dir: Path, db_version: str | None = None) -> dict[str, Any]:
    """List all ``.edt``, ``.ddt``, ``.lnc``, and ``.dbc`` files in the selected DB version directory."""
    vdir = _latest_db_version_dir(fm_dir, db_version)
    items: list[dict[str, Any]] = []
    for root_cat in ("edt", "lnc", "dbc"):
        folder = vdir / root_cat
        if not folder.exists():
            continue
        for p in sorted(folder.rglob("*")):
            if not p.is_file() or p.name.endswith(".bak"):
                continue
            is_disabled = p.name.endswith(".disabled")
            clean_name = p.name[: -len(".disabled")] if is_disabled else p.name
            ext = Path(clean_name).suffix.lower()
            if ext not in (".edt", ".ddt", ".lnc", ".dbc"):
                continue
            desc = DBC_LICENSING_DESCRIPTIONS.get(
                clean_name,
                {"tr": f"{clean_name} oyun kural/veri dosyası", "en": f"{clean_name} game rule/data file"},
            )
            rel_path = p.relative_to(vdir).as_posix()
            sz = p.stat().st_size
            items.append({
                "name": clean_name,
                "filename": p.name,
                "rel_path": rel_path,
                "category": root_cat,
                "ext": ext,
                "size_bytes": sz,
                "size_kb": round(sz / 1024, 1),
                "disabled": is_disabled,
                "enabled": not is_disabled,
                "editable_text": ext in (".edt", ".ddt", ".lnc"),
                "backup_exists": p.with_name(clean_name + ".bak").exists(),
                "desc_tr": desc["tr"],
                "desc_en": desc["en"],
            })
    sd = read_sugardaddy_edt(fm_dir, vdir.name)
    return {
        "db_version": vdir.name,
        "active_version": vdir.name,
        "db_version_path": str(vdir),
        "files": items,
        "sugar_daddy": sd,
        "sugardaddy": sd,
    }


def read_sugardaddy_edt(fm_dir: Path, db_version: str | None = None) -> dict[str, Any]:
    """Parse ``sugardaddy.edt`` into structured Sugar Daddy club records."""
    vdir = _latest_db_version_dir(fm_dir, db_version)
    p = _find_sugardaddy_path(vdir)
    if not p.exists():
        return {"exists": False, "entries": []}
    text, enc = _read_text_auto_encoding(p)
    line_re = re.compile(r'^(#?)\s*"SUGAR_DADDY"\s+"([^"]+)"\s+"([^"]+)"\s+"([^"]+)"')
    entries: list[dict[str, Any]] = []
    for line in text.splitlines():
        m = line_re.match(line.strip())
        if m:
            commented, sd_type, club, flag = m.groups()
            if sd_type not in ("FRONT_END", "BACK_END", "UNDERWRITER"):
                continue
            if club == "Charlton Athletic" and commented == "#":
                continue
            entries.append({
                "enabled": commented == "",
                "type": sd_type,
                "club": club,
                "alter_starting_finances": flag == "1",
                "start_flag": 1 if flag == "1" else 0,
            })
    return {
        "exists": True,
        "path": str(p),
        "rel_path": p.relative_to(vdir).as_posix(),
        "encoding": enc,
        "backup_exists": p.with_name("sugardaddy.edt.bak").exists(),
        "entries": entries,
    }


def write_sugardaddy_edt(fm_dir: Path, entries: list[dict[str, Any]], db_version: str | None = None) -> dict[str, Any]:
    """Write structured Sugar Daddy entries back to ``sugardaddy.edt`` with automatic ``.bak`` backup."""
    vdir = _latest_db_version_dir(fm_dir, db_version)
    p = _find_sugardaddy_path(vdir)
    if not p.exists():
        raise FileNotFoundError(f"sugardaddy.edt not found at {p}")
    bak = p.with_name("sugardaddy.edt.bak")
    if not bak.exists():
        shutil.copy2(p, bak)
    orig_text, enc = _read_text_auto_encoding(p)
    header_lines: list[str] = []
    for line in orig_text.splitlines():
        if line.strip().startswith('"SUGAR_DADDY"'):
            break
        header_lines.append(line)

    body_lines: list[str] = []
    for item in entries:
        club = str(item.get("club", "")).strip()
        if not club:
            continue
        sd_type = str(item.get("type", "FRONT_END")).strip().upper()
        if sd_type not in ("FRONT_END", "BACK_END", "UNDERWRITER"):
            sd_type = "FRONT_END"
        enabled = bool(item.get("enabled", True))
        sflag = item.get("start_flag")
        if sflag is not None:
            alter = "1" if str(sflag) == "1" or bool(sflag) else "0"
        else:
            alter = "1" if item.get("alter_starting_finances", item.get("keep_after_departure", False)) else "0"
        prefix = "" if enabled else "#"
        body_lines.append(f'{prefix}"SUGAR_DADDY" "{sd_type}" "{club}" "{alter}"')

    new_text = "\n".join(header_lines + body_lines) + "\n"
    _write_text_preserve_encoding(p, new_text, enc)
    return read_sugardaddy_edt(fm_dir, vdir.name)


def read_text_rule_file(fm_dir: Path, rel_path: str, db_version: str | None = None) -> dict[str, Any]:
    """Read a ``.edt`` or ``.lnc`` file preserving UTF-16LE / UTF-8 encoding."""
    vdir = _latest_db_version_dir(fm_dir, db_version)
    target = (vdir / rel_path).resolve()
    if not str(target).startswith(str(vdir.resolve())):
        raise ValueError("Invalid relative path")
    if not target.exists():
        raise FileNotFoundError(f"File not found: {target}")
    text, enc = _read_text_auto_encoding(target)
    clean_name = target.name[: -len(".disabled")] if target.name.endswith(".disabled") else target.name
    return {
        "rel_path": rel_path,
        "path": str(target),
        "name": clean_name,
        "encoding": enc,
        "backup_exists": target.with_name(clean_name + ".bak").exists(),
        "content": text,
    }


def write_text_rule_file(fm_dir: Path, rel_path: str, content: str, db_version: str | None = None) -> dict[str, Any]:
    """Write a ``.edt`` or ``.lnc`` file preserving its original BOM/encoding, creating a ``.bak`` backup first."""
    vdir = _latest_db_version_dir(fm_dir, db_version)
    target = (vdir / rel_path).resolve()
    if not str(target).startswith(str(vdir.resolve())):
        raise ValueError("Invalid relative path")
    if not target.exists():
        raise FileNotFoundError(f"File not found: {target}")
    clean_name = target.name[: -len(".disabled")] if target.name.endswith(".disabled") else target.name
    bak = target.with_name(clean_name + ".bak")
    if not bak.exists():
        shutil.copy2(target, bak)
    _, enc = _read_text_auto_encoding(target)
    _write_text_preserve_encoding(target, content, enc)
    return read_text_rule_file(fm_dir, rel_path, vdir.name)


def toggle_rule_or_dbc_file(fm_dir: Path, rel_path: str, disable: bool, db_version: str | None = None) -> dict[str, Any]:
    """Enable or disable a ``.dbc``, ``.lnc``, or ``.edt`` file by renaming ``<file>`` <-> ``<file>.disabled``."""
    vdir = _latest_db_version_dir(fm_dir, db_version)
    target = (vdir / rel_path).resolve()
    if not str(target).startswith(str(vdir.resolve())):
        raise ValueError("Invalid relative path")
    if not target.exists():
        # Check if its counterpart exists
        if rel_path.endswith(".disabled"):
            alt = vdir / rel_path[: -len(".disabled")]
        else:
            alt = vdir / (rel_path + ".disabled")
        if alt.exists():
            target = alt
        else:
            raise FileNotFoundError(f"File not found: {target}")

    is_cur_disabled = target.name.endswith(".disabled")
    clean_name = target.name[: -len(".disabled")] if is_cur_disabled else target.name
    if disable and not is_cur_disabled:
        new_target = target.with_name(clean_name + ".disabled")
        target.rename(new_target)
    elif not disable and is_cur_disabled:
        new_target = target.with_name(clean_name)
        target.rename(new_target)
    return list_edt_lnc_dbc_files(fm_dir, vdir.name)
