"""FM27 / FM26 All-in-One Studio Backend Server & API Engine.

Unifies the 3 Core Pillars + Independent In-Game Term Localization with a multi-threaded,
in-memory cached architecture (<1ms detail lookups, zero UI freeze):
1. Pillar 1 — Save (`.fm`) & Pre-Game Installation Databases Visualizer & Granular Live Editor
2. Pillar 2 — Game Optimization Suite (`boot.config` 14+ keys & raw editor, URP profiles, Video bypass, Disk footprint)
3. Pillar 3 — Game File & Binary/Bundle Patcher (`game_plugin.dll` custom player limit, 10 named UI table
   sorting patches, all 252 `StreamedTable` sorting unlockers, and `.edt`/`.lnc`/`.dbc` visual editor)
4. Cross-Cutting — Independent In-Game Term Localization (`21` official FM `.ltc` languages).
"""

from __future__ import annotations

import json
import os
import threading
import traceback
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping

from fm26save import ALL_28_TABLES, FM26Editor, FM26Save, analyze_player_role_breakdown, serialize_record
from fm26save.constants import FM26_NATIONS, STAFF_BLOCK40_FIELDS, STAFF_ROLE_MAP
from fm26save.dof import build_dof_dashboard, hire_head_coach
from fm26save.game_files import (
    extract_master_db_tables,
    extract_multi_version_database_evolution,
    extract_pregame_people_and_history_db,
)
from fm26save.game_localization import (
    PLAYER_ATTRIBUTE_GROUPS,
    STAFF_ATTRIBUTE_GROUPS,
    get_game_terms,
    list_game_languages,
)
from fm26save.game_optimizer import (
    apply_boot_preset,
    inspect_disk_and_optimization_state,
    list_edt_lnc_dbc_files,
    read_boot_config,
    read_sugardaddy_edt,
    read_text_rule_file,
    restore_boot_config,
    toggle_intro_videos,
    toggle_rule_or_dbc_file,
    write_boot_config,
    write_sugardaddy_edt,
    write_text_rule_file,
)
from fm26save.ui_patches import (
    DEFAULT_FM27_DIR,
    PATCHES,
    apply as apply_ui_patch,
    get_all_patches_status,
    resolve_patch,
    restore as restore_ui_patch,
    scan_all_streamed_tables,
    set_streamed_table_sorting,
)

POSITION_FIELD_MAP: list[tuple[str, str, str]] = [
    ("GK", "pos_gk", "gk"),
    ("SW", "pos_sw", "sw"),
    ("DL", "pos_dl", "dl"),
    ("DC", "pos_dc", "dc"),
    ("DR", "pos_dr", "dr"),
    ("WBL", "pos_wbl", "wbl"),
    ("WBR", "pos_wbr", "wbr"),
    ("DM", "pos_dm", "dm"),
    ("ML", "pos_ml", "ml"),
    ("MC", "pos_mc", "mc"),
    ("MR", "pos_mr", "mr"),
    ("AML", "pos_aml", "aml"),
    ("AMC", "pos_amc", "amc"),
    ("AMR", "pos_amr", "amr"),
    ("ST", "pos_st", "stc"),
]

PERSONALITY_FIELDS: list[tuple[str, str, str]] = [
    ("adaptability", "Uyum (Adaptability)", "Adaptability"),
    ("ambition", "Hırs (Ambition)", "Ambition"),
    ("controversy", "Tartışmacılık (Controversy)", "Controversy"),
    ("loyalty", "Sadakat (Loyalty)", "Loyalty"),
    ("pressure", "Baskıya Dayanıklılık (Pressure)", "Pressure"),
    ("professionalism", "Profesyonellik (Professionalism)", "Professionalism"),
    ("sportsmanship", "Sportmenlik (Sportsmanship)", "Sportsmanship"),
    ("temperament", "Mizaç / Sakinlik (Temperament)", "Temperament"),
]

STAFF_PREFERENCE_FIELDS: list[tuple[str, str, str]] = [
    ("attacking", "Hücum Eğilimi (Attacking)", "Attacking"),
    ("directness", "Direkt Oyun (Directness)", "Directness"),
    ("tempo", "Oyun Temposu (Tempo)", "Tempo"),
    ("width", "Oyun Genişliği (Width)", "Width"),
    ("trigger_press", "Ön Alan Presi (Trigger Press)", "Trigger Press"),
    ("flexibility", "Taktiksel Esneklik (Flexibility)", "Flexibility"),
    ("hardness_of_training", "Antrenman Sertliği (1-20)", "Hardness of Training"),
    ("squad_rotation", "Kadro Rotasyonu (1-20)", "Squad Rotation"),
    ("buying_players", "Oyuncu Transfer Eğilimi", "Buying Players"),
    ("mind_games", "Zihin Oyunları (Mind Games)", "Mind Games"),
    ("business", "Ticari Yaklaşım (Business)", "Business"),
    ("interference", "Müdahalecilik (Interference)", "Interference"),
    ("patience", "Sabır Seviyesi (Patience)", "Patience"),
    ("resources", "Kaynak Kullanımı (Resources)", "Resources"),
]

SQUAD_STATUS_CATALOG: list[dict[str, Any]] = [
    {"code": 1, "tr": "Yıldız Oyuncu (Star Player)", "en": "Star Player"},
    {"code": 2, "tr": "Önemli Oyuncu (Important Player)", "en": "Important Player"},
    {"code": 3, "tr": "Düzenli İlk 11 (Regular Starter)", "en": "Regular Starter"},
    {"code": 4, "tr": "Rotasyon Oyuncusu (Squad Player)", "en": "Squad Player"},
    {"code": 5, "tr": "Hamle Oyuncusu (Impact Sub)", "en": "Impact Sub"},
    {"code": 7, "tr": "Yedek / Kenar Oyuncu (Fringe Player)", "en": "Fringe Player"},
    {"code": 9, "tr": "Acil Durum Yedeği (Emergency Backup)", "en": "Emergency Backup"},
    {"code": 10, "tr": "A Takım Adayı Genç (Breakthrough Prospect)", "en": "Breakthrough Prospect"},
    {"code": 11, "tr": "Gelecek Vaat Eden (Future Prospect)", "en": "Future Prospect"},
    {"code": 13, "tr": "Altyapı Oyuncusu (Youngster)", "en": "Youngster"},
    {"code": 14, "tr": "B Takımı Düzenli Oyuncusu", "en": "B Team Regular"},
    {"code": 15, "tr": "Birinci Kaleci (First Choice GK)", "en": "First Choice Goalkeeper"},
    {"code": 16, "tr": "Kupa Kalecisi (Cup GK)", "en": "Cup Goalkeeper"},
    {"code": 17, "tr": "Yerel Kupa Kalecisi (Domestic Cup GK)", "en": "Domestic Cup Goalkeeper"},
    {"code": 18, "tr": "Kıta Kupası Kalecisi (Continental Cup GK)", "en": "Continental Cup Goalkeeper"},
    {"code": 20, "tr": "Yedek Kaleci (Backup GK)", "en": "Backup Goalkeeper"},
    {"code": 21, "tr": "Acil Durum Yedek Kaleci", "en": "Goalkeeper Emergency Backup"},
    {"code": 22, "tr": "İhtiyaç Fazlası / Kadro Dışı (Surplus)", "en": "Surplus to Requirements"},
]

PLAYER_TRAITS_CATALOG: list[dict[str, Any]] = [
    {"bit": 0, "key": "RUNS_WITH_BALL_DOWN_LEFT", "tr": "Topu Sol Kanattan Sürer", "en": "Runs With Ball Down Left"},
    {"bit": 1, "key": "RUNS_WITH_BALL_DOWN_RIGHT", "tr": "Topu Sağ Kanattan Sürer", "en": "Runs With Ball Down Right"},
    {"bit": 2, "key": "RUNS_WITH_BALL_THROUGH_CENTRE", "tr": "Topu Merkezden Sürer", "en": "Runs With Ball Through Centre"},
    {"bit": 4, "key": "MOVES_INTO_CHANNELS", "tr": "Kanat Aralarına (Boşluklara) Kaçar", "en": "Moves Into Channels"},
    {"bit": 5, "key": "GETS_FORWARD_WHENEVER_POSSIBLE", "tr": "Her Fırsatta İleri Çıkar", "en": "Gets Forward Whenever Possible"},
    {"bit": 7, "key": "TRIES_KILLER_BALLS_OFTEN", "tr": "Sık Sık Ara Pas Dener", "en": "Tries Killer Balls Often"},
    {"bit": 8, "key": "SHOOTS_FROM_DISTANCE", "tr": "Uzaktan Şut Çeker", "en": "Shoots From Distance"},
    {"bit": 13, "key": "LIKES_TO_TRY_TO_BEAT_OFFSIDE_TRAP", "tr": "Ofsayt Tuzağını Kırmayı Sever", "en": "Likes To Try To Beat Offside Trap"},
    {"bit": 19, "key": "COMES_DEEP_TO_GET_BALL", "tr": "Top Almak İçin Derine Gelir", "en": "Comes Deep To Get Ball"},
    {"bit": 22, "key": "DICTATES_TEMPO", "tr": "Oyunun Temposunu Belirler", "en": "Dictates Tempo"},
    {"bit": 27, "key": "KNOCKS_BALL_PAST_OPPONENT", "tr": "Topu Rakibin Yanından Atıp Geçer", "en": "Knocks Ball Past Opponent"},
    {"bit": 34, "key": "AVOIDS_USING_WEAKER_FOOT", "tr": "Zayıf Ayağını Kullanmaktan Kaçınır", "en": "Avoids Using Weaker Foot"},
    {"bit": 37, "key": "DIVES_INTO_TACKLES", "tr": "Topa Kayarak Müdahale Eder", "en": "Dives Into Tackles"},
    {"bit": 43, "key": "TRIES_LONG_RANGE_PASSES", "tr": "Uzun Mesafeli Paslar Dener", "en": "Tries Long Range Passes"},
    {"bit": 51, "key": "RUNS_WITH_BALL_OFTEN", "tr": "Sık Sık Topla Koşu Yapar", "en": "Runs With Ball Often"},
    {"bit": 59, "key": "CROSSES_EARLY", "tr": "Erken Orta Yapar", "en": "Crosses Early"},
]

CLAUSE_KINDS_CATALOG: list[dict[str, Any]] = [
    {"code": 0x00, "tr": "Serbest Kalma Bedeli (Minimum Fee Release)", "en": "Minimum Fee Release Clause"},
    {"code": 0x01, "tr": "Küme Düşme Serbest Kalma Bedeli", "en": "Relegation Release Clause"},
    {"code": 0x02, "tr": "Üst Lige Çıkamama Serbest Kalma Bedeli", "en": "Non-Promotion Release Clause"},
    {"code": 0x0F, "tr": "Küme Düşmede Maaş İndirimi (%)", "en": "Top Division Relegation Salary Drop (%)"},
    {"code": 0x10, "tr": "Yabancı Kulüplere Serbest Kalma Bedeli", "en": "Minimum Fee Release (Foreign Clubs)"},
    {"code": 0x11, "tr": "Üst Ligdeki Yerli Kulüplere Serbest Kalma", "en": "Minimum Fee Release (Higher Division)"},
    {"code": 0x12, "tr": "Yerli Kulüplere Serbest Kalma Bedeli", "en": "Minimum Fee Release (Domestic)"},
    {"code": 0x16, "tr": "Kulüp Taraflı Sözleşme Uzatma Opsiyonu (Yıl)", "en": "Optional Extension by Club (Years)"},
    {"code": 0x20, "tr": "Maç Başı Ücret (Appearance Fee)", "en": "Appearance Fee"},
    {"code": 0x22, "tr": "Gol Yememe Bonusu (Clean Sheet Bonus)", "en": "Clean Sheet / Shutout Bonus"},
    {"code": 0x25, "tr": "Milli Maç Bonusu (International Cap Bonus)", "en": "International Cap Bonus"},
    {"code": 0x26, "tr": "Kullanılmayan Yedek Ücreti (Unused Sub Fee)", "en": "Unused Substitute Fee"},
    {"code": 0x29, "tr": "Sezonluk Toplam Gol + Asist Hedef Bonusu", "en": "Seasonal Landmark Combined Goals & Assists"},
]


def _build_nations_catalog() -> list[dict[str, Any]]:
    rows = [
        {"id": nid, "tr": info.get("tr", info["en"]), "en": info["en"], "code": info.get("code", "")}
        for nid, info in FM26_NATIONS.items()
    ]
    rows.sort(key=lambda r: r["tr"])
    return rows


def _build_staff_roles_catalog() -> list[dict[str, Any]]:
    rows = [
        {"code": code, "tr": info["tr"], "en": info["en"], "dept": info.get("dept", "")}
        for code, info in sorted(STAFF_ROLE_MAP.items())
    ]
    return rows


def discover_save_files() -> list[dict[str, Any]]:
    """Auto-discover `.fm` save files in workspace, AppData/Local/Sports Interactive, and user Documents folders."""
    candidates: list[Path] = []
    cwd = Path.cwd()
    candidates.extend(sorted(cwd.glob("*.fm")))
    appdata_si = Path.home() / "AppData" / "Local" / "Sports Interactive"
    if appdata_si.exists():
        for gname in ("Football Manager 27", "Football Manager 26"):
            gdir = appdata_si / gname
            if gdir.exists():
                candidates.extend(sorted(gdir.rglob("*.fm")))
    docs = Path.home() / "Documents" / "Sports Interactive"
    if docs.exists():
        for gname in ("Football Manager 27", "Football Manager 26"):
            gdir = docs / gname
            if gdir.exists():
                candidates.extend(sorted(gdir.rglob("*.fm")))
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for p in candidates:
        try:
            rp = str(p.resolve())
            if rp in seen or not p.is_file():
                continue
            seen.add(rp)
            is_fm27 = "football manager 27" in rp.lower()
            out.append({
                "name": p.name,
                "path": rp,
                "size_mb": round(p.stat().st_size / (1024 * 1024), 2),
                "is_fm27": is_fm27,
            })
        except OSError:
            continue
    out.sort(key=lambda s: (0 if s.get("is_fm27") else 1, 1 if "backup" in s["name"].lower() else 0, s["name"]))
    return out


def discover_fm_installations() -> list[dict[str, str]]:
    """Auto-discover Football Manager 27 & 26 installation directories."""
    roots = [
        Path(r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 27"),
        Path(r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26"),
        Path(r"D:\SteamLibrary\steamapps\common\Football Manager 27"),
        Path(r"D:\SteamLibrary\steamapps\common\Football Manager 26"),
    ]
    env_dir = os.environ.get("FM_INSTALL_DIR")
    if env_dir:
        roots.insert(0, Path(env_dir))
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for r in roots:
        if r.exists() and r.is_dir():
            rp = str(r.resolve())
            if rp not in seen:
                seen.add(rp)
                label = "FM27" if "27" in r.name else ("FM26" if "26" in r.name else r.name)
                out.append({"label": label, "name": r.name, "path": rp})
    return out


class StudioState:
    """Thread-safe in-memory state manager and cache for the active `.fm` save and FM installation directory."""

    def __init__(self, save_path: Path | None = None, fm_dir: Path | None = None) -> None:
        self._lock = threading.RLock()
        saves = discover_save_files()
        installs = discover_fm_installations()
        if save_path is None and saves:
            primary = [s for s in saves if not s["name"].endswith(("_DoF.fm", "_edited.fm"))]
            save_path = Path((primary[0] if primary else saves[0])["path"])
        if fm_dir is None:
            if installs:
                fm_dir = Path(installs[0]["path"])
            else:
                fm_dir = DEFAULT_FM27_DIR
        self.save_path: Path | None = save_path.resolve() if save_path and save_path.exists() else None
        self.fm_dir: Path = fm_dir.resolve() if fm_dir.exists() else fm_dir
        self._save_cache: dict[str, Any] = {}
        self._pregame_cache: dict[str, Any] = {}

    def set_context(self, save_path: str | None = None, fm_dir: str | None = None) -> dict[str, Any]:
        with self._lock:
            if save_path:
                sp = Path(save_path).expanduser().resolve()
                if not sp.exists():
                    raise FileNotFoundError(f"Save file not found: {sp}")
                if sp != self.save_path:
                    self.save_path = sp
                    self._save_cache.clear()
            if fm_dir:
                fd = Path(fm_dir).expanduser().resolve()
                if not fd.exists():
                    raise FileNotFoundError(f"FM installation directory not found: {fd}")
                if fd != self.fm_dir:
                    self.fm_dir = fd
                    self._pregame_cache.clear()
            return self.get_overview()

    def _ensure_save_index(self) -> dict[str, Any]:
        with self._lock:
            if "indexed" in self._save_cache:
                return self._save_cache["indexed"]
            if not self.save_path or not self.save_path.exists():
                return {}
            with FM26Save(self.save_path) as sv:
                info = sv.info
                clubs_raw = sv.table("clubs")
                club_map: dict[int, str] = {}
                clubs_raw_by_uid: dict[int, Any] = {}
                for c in clubs_raw:
                    club_map[c.uid] = c.name or c.short_name or f"Club #{c.uid}"
                    clubs_raw_by_uid[c.uid] = c

                finances_by_club: dict[int, Any] = {}
                finances_series_by_club: dict[int, list[dict[str, Any]]] = {}
                try:
                    for f in sv.table("finances"):
                        finances_by_club[f.club_uid] = f
                        finances_series_by_club.setdefault(f.club_uid, []).append({
                            "month": str(f.month),
                            "balance": f.balance,
                            "transfer_budget_allocated": f.transfer_budget_allocated,
                            "transfer_budget_remaining": f.transfer_budget_remaining,
                            "wage_budget_weekly": f.wage_budget_weekly,
                            "wage_payroll_weekly": f.wage_payroll_weekly,
                            "income_excluding_transfers": f.income_excluding_transfers,
                            "expenditure_excluding_transfers": f.expenditure_excluding_transfers,
                            "net_transfers": f.net_transfers,
                            "wage_bill": f.wage_bill,
                            "total_income": f.total_income,
                            "total_expenditure": f.total_expenditure,
                            "net": f.net,
                        })
                except Exception:
                    pass

                sponsorships_by_club: dict[int, list[dict[str, Any]]] = {}
                try:
                    for sp in sv.table("sponsorships"):
                        lst = sponsorships_by_club.setdefault(sp.club_uid, [])
                        lst.append({
                            "index": len(lst),
                            "kind": sp.kind.raw if sp.kind else 0,
                            "start": str(sp.start) if sp.start else "",
                            "end": str(sp.end) if sp.end else "",
                            "total_value": sp.total_value,
                            "annual_value": sp.annual_value,
                            "unknown": dict(sp.unknown) if sp.unknown else {},
                        })
                except Exception:
                    pass

                try:
                    facilities_by_club = {f.club_uid: f for f in sv.table("facilities")}
                except Exception:
                    facilities_by_club = {}

                try:
                    stadiums_raw = sv.table("stadiums")
                except Exception:
                    stadiums_raw = ()

                injuries_by_player: dict[int, list[dict[str, Any]]] = {}
                try:
                    for inj in sv.table("injuries"):
                        if inj.player_uid is not None:
                            injuries_by_player.setdefault(inj.player_uid, []).append({
                                "kind": str(inj.kind),
                                "type_id": inj.type_id,
                                "name": inj.type_name or f"Injury #{inj.type_id}",
                                "date": str(inj.date) if inj.date else "",
                            })
                except Exception:
                    pass

                season_stats_by_player: dict[int, list[dict[str, Any]]] = {}

                players_list: list[dict[str, Any]] = []
                players_by_uid: dict[int, dict[str, Any]] = {}
                raw_players_by_uid: dict[int, Any] = {}
                for p in sv.table("players"):
                    if not p.ability:
                        continue
                    raw_players_by_uid[p.uid] = p
                    ct = p.contract
                    club_uid = p.club_uid or (ct.club_uid if ct else 0) or 0
                    club_name = p.club_name or (club_map.get(club_uid, "") if club_uid else "")
                    best_pos = p.natural_positions[0] if p.natural_positions else "—"
                    if best_pos == "—" and p.positions:
                        best_score = -1
                        for code, _, attr_name in POSITION_FIELD_MAP:
                            val = getattr(p.positions, attr_name, 0) or 0
                            if val > best_score:
                                best_score = val
                                best_pos = code
                    sq_status_raw = ct.squad_status.raw if ct and ct.squad_status is not None else None
                    p_injs = injuries_by_player.get(p.uid, [])
                    typed_injs = [x["name"] for x in p_injs if x["kind"] == "typed"]
                    row = {
                        "uid": p.uid,
                        "unique_id": p.unique_id,
                        "name": p.name or f"{p.first_name or ''} {p.last_name or ''}".strip() or f"Player #{p.uid}",
                        "first_name": p.first_name or "",
                        "last_name": p.last_name or "",
                        "common_name": p.common_name or "",
                        "age": p.age or 0,
                        "birth_date": str(p.birth_date) if p.birth_date else "",
                        "nation_id": p.nation_id,
                        "nationality_id": p.nation_id,
                        "nationality": sv.nation_name(p.nation_id, lang="tr"),
                        "second_nation_ids": list(p.second_nation_ids) if p.second_nation_ids else [],
                        "club_uid": club_uid,
                        "club": club_name,
                        "team_id": p.team_id,
                        "team_slot": p.team_slot,
                        "club_join_date": str(p.club_join_date) if p.club_join_date else "",
                        "ca": p.ability.current or 0,
                        "pa": p.ability.potential if p.ability.potential is not None else (p.ability.potential_range_code or 0),
                        "best_pos": best_pos,
                        "natural_positions": list(p.natural_positions) if p.natural_positions else [],
                        "value": p.transfer_value or 0,
                        "wage": ct.wage if ct and ct.wage else 0,
                        "contract_start": str(ct.start) if ct and ct.start else "",
                        "contract_end": str(ct.end) if ct and ct.end else "",
                        "squad_status": sq_status_raw,
                        "height_cm": p.height_cm or 0,
                        "left_foot": p.left_foot or 1,
                        "right_foot": p.right_foot or 1,
                        "raw_left_foot": p.raw_left_foot or 1,
                        "raw_right_foot": p.raw_right_foot or 1,
                        "condition": round((p.raw_condition or 0) / 100),
                        "sharpness": round((p.raw_match_sharpness or 0) / 100),
                        "raw_condition": p.raw_condition or 0,
                        "raw_match_sharpness": p.raw_match_sharpness or 0,
                        "home_rep": p.reputation.home if p.reputation else 0,
                        "current_rep": p.reputation.current if p.reputation else 0,
                        "world_rep": p.reputation.world if p.reputation else 0,
                        "reputation_bucket": p.reputation.bucket if p.reputation else 0,
                        "injuries": typed_injs,
                        "all_injuries": p_injs,
                        "suspensions_count": len(p.suspensions) if p.suspensions else 0,
                        "trait_bits": p.trait_bits or 0,
                        "trait_bits_str": str(p.trait_bits or 0),
                    }
                    players_list.append(row)
                    players_by_uid[p.uid] = row

                players_list.sort(key=lambda r: (r["ca"], r["pa"]), reverse=True)

                stadiums_list: list[dict[str, Any]] = []
                stadium_by_uid: dict[int, dict[str, Any]] = {}
                stadium_by_club_uid: dict[int, dict[str, Any]] = {}
                for st in stadiums_raw:
                    st_label = st.name
                    if not st_label and st.home_club_names:
                        st_label = f"{st.home_club_names[0]} Stadyumu (#{st.uid})"
                    elif not st_label and st.owner_club_name:
                        st_label = f"{st.owner_club_name} Stadyumu (#{st.uid})"
                    elif not st_label:
                        st_label = f"Stadium #{st.uid}"
                    cap = st.capacity if st.capacity else st.all_seater_capacity
                    st_dict = {
                        "uid": st.uid,
                        "name": st_label,
                        "inline_name": st.name or "",
                        "capacity": cap or 0,
                        "raw_capacity": st.capacity or 0,
                        "all_seater_capacity": st.all_seater_capacity or 0,
                        "expansion_capacity": st.expansion_capacity or 0,
                        "owner_club_uid": st.owner_club_uid,
                        "owner_club_name": st.owner_club_name or "",
                        "home_club_uids": list(st.home_club_uids),
                        "home_club_names": list(st.home_club_names),
                        "pitch_length_dm": st.pitch_length_dm,
                        "pitch_width_dm": st.pitch_width_dm,
                        "pitch_min_length_dm": st.pitch_min_length_dm,
                        "pitch_min_width_dm": st.pitch_min_width_dm,
                        "pitch_max_length_dm": st.pitch_max_length_dm,
                        "pitch_max_width_dm": st.pitch_max_width_dm,
                        "built_date": str(st.built_date) if st.built_date else "",
                        "rebuilt_date": str(st.rebuilt_date) if st.rebuilt_date else "",
                    }
                    stadiums_list.append(st_dict)
                    stadium_by_uid[st.uid] = st_dict
                    if st.owner_club_uid and st.owner_club_uid not in stadium_by_club_uid:
                        stadium_by_club_uid[st.owner_club_uid] = st_dict
                    for hc_uid in st.home_club_uids:
                        stadium_by_club_uid[hc_uid] = st_dict
                stadiums_list.sort(key=lambda r: r["all_seater_capacity"], reverse=True)

                clubs_list: list[dict[str, Any]] = []
                clubs_by_uid: dict[int, dict[str, Any]] = {}
                for c in clubs_raw:
                    fin = finances_by_club.get(c.uid)
                    fac = facilities_by_club.get(c.uid)
                    corp_raw = getattr(fac.corporate_facilities, "raw", 0) if fac and fac.corporate_facilities else 0
                    st_info = stadium_by_club_uid.get(c.uid)
                    nat_str = sv.nation_name(c.nation_id, lang="tr")
                    c_dict = {
                        "uid": c.uid,
                        "unique_id": c.unique_id,
                        "name": c.name or c.short_name or f"Club #{c.uid}",
                        "short_name": c.short_name or "",
                        "reputation": c.reputation or 0,
                        "last_league_position": c.last_league_position,
                        "last_league_pos": c.last_league_position,
                        "nation_id": c.nation_id,
                        "nation_name": nat_str,
                        "nationality": nat_str,
                        "fa_nation_id": c.fa_nation_id,
                        "city_id": c.city_id,
                        "parent_club_uid": c.parent_club_uid,
                        "parent_club_name": c.parent_club_name or "",
                        "teams": [
                            {"team_id": t.team_id, "slot": t.slot, "club_uid": t.club_uid, "is_affiliate": t.is_affiliate}
                            for t in (c.teams or ())
                        ],
                        "balance": fin.balance if fin and fin.balance is not None else 0,
                        "transfer_budget_allocated": fin.transfer_budget_allocated if fin and fin.transfer_budget_allocated is not None else 0,
                        "transfer_budget": fin.transfer_budget_remaining if fin and fin.transfer_budget_remaining is not None else 0,
                        "wage_budget": fin.wage_budget_weekly if fin and fin.wage_budget_weekly is not None else 0,
                        "wage_payroll": fin.wage_payroll_weekly if fin and fin.wage_payroll_weekly is not None else 0,
                        "income_excluding_transfers": fin.income_excluding_transfers if fin else 0,
                        "expenditure_excluding_transfers": fin.expenditure_excluding_transfers if fin else 0,
                        "net_transfers": fin.net_transfers if fin else 0,
                        "wage_bill": fin.wage_bill if fin else 0,
                        "total_income": fin.total_income if fin else 0,
                        "total_expenditure": fin.total_expenditure if fin else 0,
                        "corporate_facilities": corp_raw,
                        "stadium_uid": st_info["uid"] if st_info else None,
                        "stadium_name": st_info["name"] if st_info else "",
                        "stadium_capacity": st_info["all_seater_capacity"] if st_info else 0,
                    }
                    clubs_list.append(c_dict)
                    clubs_by_uid[c.uid] = c_dict
                clubs_list.sort(key=lambda r: r["reputation"], reverse=True)

                staff_by_uid: dict[int, dict[str, Any]] = {}
                raw_staff_by_uid: dict[int, Any] = {}
                try:
                    for raw_s in sv.table("staff"):
                        raw_staff_by_uid[raw_s.uid] = raw_s
                    staff_enriched = sv.staff_enriched()
                    for s in staff_enriched:
                        cuid = s.get("club_uid")
                        rs = raw_staff_by_uid.get(s["uid"])
                        s["club_name"] = club_map.get(cuid, "") if cuid else (s.get("club_name") or "")
                        s["role_name"] = s.get("role_tr") or s.get("role_en") or s.get("departments") or ""
                        s["team_id"] = rs.team_id if rs else s.get("team_id")
                        staff_by_uid[s["uid"]] = s
                    staff_enriched.sort(key=lambda r: (r.get("ca") or 0, r.get("pa") or 0), reverse=True)
                except Exception:
                    staff_enriched = []

                league_rows: list[dict[str, Any]] = []

                sections = [
                    {
                        "name": e.full_name,
                        "compressed_size": e.compressed_size,
                        "decompressed_size": e.decompressed_size,
                        "ratio": round(e.compression_ratio, 2),
                    }
                    for e in sv.container.list_entries()
                ]

                try:
                    managed = sv.table("managed-clubs")
                    managed_uid = managed[0].club_uid if managed else 1909
                except Exception:
                    managed_uid = 1909

                indexed = {
                    "save_info": {
                        "file": self.save_path.name,
                        "path": str(self.save_path),
                        "game": info.game,
                        "build": info.build,
                        "game_date": str(info.game_date),
                        "managed_club_uid": managed_uid,
                        "managed_club_name": club_map.get(managed_uid, ""),
                        "players_count": len(players_list),
                        "clubs_count": len(clubs_list),
                        "staff_count": len(staff_enriched),
                        "stadiums_count": len(stadiums_list),
                        "sections_count": len(sections),
                    },
                    "players": players_list,
                    "players_by_uid": players_by_uid,
                    "raw_players_by_uid": raw_players_by_uid,
                    "season_stats_by_player": season_stats_by_player,
                    "clubs": clubs_list,
                    "clubs_by_uid": clubs_by_uid,
                    "finances_series_by_club": finances_series_by_club,
                    "sponsorships_by_club": sponsorships_by_club,
                    "stadiums": stadiums_list,
                    "stadium_by_uid": stadium_by_uid,
                    "stadium_by_club_uid": stadium_by_club_uid,
                    "staff": staff_enriched,
                    "staff_by_uid": staff_by_uid,
                    "raw_staff_by_uid": raw_staff_by_uid,
                    "league_tables": league_rows,
                    "sections": sections,
                    "table_cache": {},
                }
                self._save_cache["indexed"] = indexed
                return indexed

    def get_overview(self, game_lang: str = "turkish") -> dict[str, Any]:
        idx = self._ensure_save_index()
        return {
            "active_save": idx.get("save_info") if idx else None,
            "active_fm_dir": str(self.fm_dir),
            "available_saves": discover_save_files(),
            "available_installs": discover_fm_installations(),
            "game_languages": list_game_languages(),
            "active_game_terms": get_game_terms(game_lang, self.fm_dir),
            "tables_catalog": [t[0] for t in ALL_28_TABLES],
            "nations_catalog": _build_nations_catalog(),
            "squad_statuses_catalog": SQUAD_STATUS_CATALOG,
            "player_traits_catalog": PLAYER_TRAITS_CATALOG,
            "staff_roles_catalog": _build_staff_roles_catalog(),
            "clause_kinds_catalog": CLAUSE_KINDS_CATALOG,
            "personality_fields": PERSONALITY_FIELDS,
            "staff_preference_fields": STAFF_PREFERENCE_FIELDS,
        }

    def query_players(
        self,
        q: str = "",
        pos: str = "",
        club: str = "",
        min_ca: int = 0,
        max_age: int = 99,
        sort_by: str = "ca",
        limit: int = 100,
    ) -> dict[str, Any]:
        idx = self._ensure_save_index()
        players = idx.get("players", [])
        ql = q.strip().lower()
        cl = club.strip().lower()
        pu = pos.strip().upper()
        filtered = []
        for p in players:
            if ql and ql not in p["name"].lower() and ql != str(p["uid"]) and ql not in p["nationality"].lower():
                continue
            if cl and cl not in p["club"].lower() and cl != str(p["club_uid"]):
                continue
            if pu and p["best_pos"] != pu and pu not in p.get("natural_positions", []):
                continue
            if p["ca"] < min_ca:
                continue
            if p["age"] > max_age and p["age"] > 0:
                continue
            filtered.append(p)
        if sort_by in ("ca", "pa", "value", "wage", "age", "current_rep"):
            filtered.sort(key=lambda r: r.get(sort_by) or 0, reverse=(sort_by != "age"))
        return {"total": len(filtered), "rows": filtered[:limit]}

    def get_player_detail(self, uid: int) -> dict[str, Any]:
        """Instant <1ms in-memory player detail lookup (all 52 attributes, 15 positions, 8 personality,
        64-bit traits, full contract + clauses, season stats, and 6D tactical role suitability)."""
        idx = self._ensure_save_index()
        summary = idx.get("players_by_uid", {}).get(uid)
        target = idx.get("raw_players_by_uid", {}).get(uid)
        if target is None or summary is None:
            raise KeyError(f"Player UID {uid} not found")

        attrs: dict[str, int] = {}
        raw_attrs: dict[str, int] = {}
        if target.attributes:
            for grp_cols in PLAYER_ATTRIBUTE_GROUPS.values():
                for col in grp_cols:
                    attr_key = "free_kick_taking" if col == "free_kicks" else col
                    val = getattr(target.attributes, attr_key, None)
                    if val is not None:
                        attrs[col] = int(val)
                    if target.raw_attributes:
                        rval = getattr(target.raw_attributes, attr_key, None)
                        if rval is not None:
                            raw_attrs[col] = int(rval)

        personality: dict[str, int] = {}
        if target.personality:
            for pk, _, _ in PERSONALITY_FIELDS:
                personality[pk] = int(getattr(target.personality, pk, 10) or 10)
        else:
            for pk, _, _ in PERSONALITY_FIELDS:
                personality[pk] = 10

        positions: dict[str, int] = {}
        if target.positions:
            for code, _term_key, attr_name in POSITION_FIELD_MAP:
                positions[code] = int(getattr(target.positions, attr_name, 1) or 1)

        ct = target.contract
        contract_detail: dict[str, Any] = {
            "has_contract": ct is not None,
            "wage": ct.wage if ct and ct.wage else 0,
            "start_date": str(ct.start) if ct and ct.start else "",
            "end_date": str(ct.end) if ct and ct.end else "",
            "team_id": ct.team_id if ct else target.team_id,
            "squad_status": ct.squad_status.raw if ct and ct.squad_status is not None else None,
            "contract_type": ct.kind.raw if ct and ct.kind is not None else 1,
            "signing_or_loyalty_fee": ct.signing_or_loyalty_fee if ct else 0,
            "agent_fee": ct.agent_fee if ct else 0,
            "package_bonus": ct.package_bonus if ct else 0,
            "option_or_reference_year": ct.option_or_reference_year if ct else None,
            "on_loan": bool(target.on_loan),
            "loan_parent_club_uid": target.loan_parent_club_uid,
            "loan_parent_club_name": target.loan_parent_club_name or "",
            "clauses": [],
        }
        if ct and ct.clauses:
            for ci, cl in enumerate(ct.clauses):
                k_raw = cl.kind.raw if cl.kind is not None else 0
                k_name = str(cl.kind.value.name) if cl.kind and hasattr(cl.kind, "value") else f"CLAUSE_{k_raw}"
                contract_detail["clauses"].append({
                    "index": ci,
                    "kind": k_raw,
                    "kind_name": k_name,
                    "value": cl.value or 0,
                    "parameter": cl.parameter,
                })

        trait_bits = int(target.trait_bits or 0)
        active_bits = [b for b in range(64) if (trait_bits >> b) & 1]
        role_breakdown = analyze_player_role_breakdown(target, top_n_per_group=5)
        role_breakdown["top_in_possession"] = [
            {
                **r,
                "role_tr": r.get("role_name_tr") or r.get("role_name_en") or "",
                "score": r.get("effective_role_score_20") or 0,
            }
            for r in role_breakdown.get("overall_top_in_possession", [])
        ]
        role_breakdown["top_out_of_possession"] = [
            {
                **r,
                "role_tr": r.get("oop_role_name_tr") or r.get("oop_role_name_en") or "",
                "score": r.get("effective_oop_score_20") or 0,
            }
            for r in role_breakdown.get("overall_top_out_of_possession", [])
        ]
        role_breakdown["top_combinations"] = [
            {
                **r,
                "role_tr": f"{r.get('in_possession_tr', '')} + {r.get('out_of_possession_tr', '')}".strip(" +"),
                "score": r.get("combined_dual_score_20") or 0,
            }
            for r in role_breakdown.get("best_dual_role_combinations", [])
        ]
        season_stats = idx.get("season_stats_by_player", {}).get(uid, [])

        return {
            "summary": summary,
            "attributes": attrs,
            "raw_attributes": raw_attrs,
            "personality": personality,
            "positions": positions,
            "contract": contract_detail,
            "season_stats": season_stats,
            "trait_bits": trait_bits,
            "trait_bits_str": str(trait_bits),
            "active_trait_bits": active_bits,
            "role_breakdown": role_breakdown,
        }

    def query_clubs(self, q: str = "", sort_by: str = "reputation", limit: int = 100) -> dict[str, Any]:
        idx = self._ensure_save_index()
        clubs = idx.get("clubs", [])
        ql = q.strip().lower()
        filtered = [
            c for c in clubs
            if not ql or ql in c["name"].lower() or ql in c["short_name"].lower() or ql == str(c["uid"])
        ]
        if sort_by in ("reputation", "balance", "transfer_budget", "wage_budget", "stadium_capacity"):
            filtered.sort(key=lambda r: r.get(sort_by) or 0, reverse=True)
        return {"total": len(filtered), "rows": filtered[:limit]}

    def get_club_detail(self, uid: int) -> dict[str, Any]:
        """Instant <1ms in-memory club detail lookup (club header, 11 finance fields, monthly finance series,
        sponsorship contracts, corporate facilities, home/owned stadium, squad players, and club staff)."""
        idx = self._ensure_save_index()
        club = idx.get("clubs_by_uid", {}).get(uid)
        if club is None:
            raise KeyError(f"Club UID {uid} not found")
        fin_series = idx.get("finances_series_by_club", {}).get(uid, [])
        sponsorships = idx.get("sponsorships_by_club", {}).get(uid, [])
        stadium = idx.get("stadium_by_club_uid", {}).get(uid)
        squad = [p for p in idx.get("players", []) if p.get("club_uid") == uid]
        staff = [s for s in idx.get("staff", []) if s.get("club_uid") == uid]
        return {
            "club": club,
            "finance_series": fin_series,
            "sponsorships": sponsorships,
            "stadium": stadium,
            "squad": squad[:60],
            "staff": staff[:40],
        }

    def query_staff(self, q: str = "", role: str = "", limit: int = 100) -> dict[str, Any]:
        idx = self._ensure_save_index()
        staff = idx.get("staff", [])
        ql = q.strip().lower()
        rl = role.strip().lower()
        filtered = []
        for s in staff:
            name = (s.get("name") or "").lower()
            club = (s.get("club_name") or "").lower()
            srole = (s.get("role_name") or "").lower()
            if ql and ql not in name and ql not in club and ql != str(s.get("uid")):
                continue
            if rl and rl not in srole and rl != str(s.get("role_code_r4")):
                continue
            filtered.append(s)
        return {"total": len(filtered), "rows": filtered[:limit]}

    def get_staff_detail(self, uid: int) -> dict[str, Any]:
        """Instant <1ms in-memory staff detail lookup (all 26 block_40 attributes, 17 tactical preferences,
        8 personality attributes, role_code_r4, and contract)."""
        idx = self._ensure_save_index()
        st = idx.get("staff_by_uid", {}).get(uid)
        raw_s = idx.get("raw_staff_by_uid", {}).get(uid)
        if st is None:
            raise KeyError(f"Staff UID {uid} not found")
        prefs: dict[str, int] = {}
        if raw_s and raw_s.preferences:
            for pk, _, _ in STAFF_PREFERENCE_FIELDS:
                val = getattr(raw_s.preferences, pk, None)
                if val is not None:
                    prefs[pk] = int(val)
        personality: dict[str, int] = {}
        if raw_s and getattr(raw_s, "personality", None):
            for pk, _, _ in PERSONALITY_FIELDS:
                personality[pk] = int(getattr(raw_s.personality, pk, 10) or 10)
        else:
            for pk, _, _ in PERSONALITY_FIELDS:
                personality[pk] = 10
        return {
            "summary": st,
            "block40_20": st.get("coaching_and_scouting_20") or {},
            "block40_raw": st.get("coaching_and_scouting_raw100") or st.get("coaching_and_scouting_raw") or {},
            "preferences": prefs,
            "personality": personality,
        }

    def query_stadiums(self, q: str = "", limit: int = 100) -> dict[str, Any]:
        idx = self._ensure_save_index()
        stadiums = idx.get("stadiums", [])
        ql = q.strip().lower()
        filtered = [
            s for s in stadiums
            if not ql
            or ql in s["name"].lower()
            or ql in (s.get("owner_club_name") or "").lower()
            or ql == str(s["uid"])
        ]
        return {"total": len(filtered), "rows": filtered[:limit]}

    def query_any_save_table(self, table_name: str, q: str = "", limit: int = 100) -> dict[str, Any]:
        if not self.save_path or not self.save_path.exists():
            return {"table": table_name, "total": 0, "rows": []}
        idx = self._ensure_save_index()
        tcache: dict[str, list[dict[str, Any]]] = idx.setdefault("table_cache", {})
        if table_name not in tcache:
            with self._lock:
                if table_name not in tcache:
                    with FM26Save(self.save_path) as sv:
                        if table_name == "hall_of_fame":
                            raw_rows = sv.hall_of_fame(limit=500)
                        elif table_name == "takeovers":
                            raw_rows = sv.board_takeovers()
                        elif table_name == "shortlists":
                            raw_rows = sv.shortlists(limit=500)
                        elif table_name == "offers":
                            raw_rows = sv.contract_offers()
                        elif table_name == "agents":
                            raw_rows = sv.agents()
                        elif table_name == "news":
                            raw_rows = sv.news_items()
                        elif table_name == "tactics_lineup":
                            raw_rows = sv.tactics_lineup()
                        else:
                            raw_rows = [serialize_record(r) for r in sv.table(table_name)]
                    tcache[table_name] = raw_rows
        rows = tcache[table_name]
        ql = q.strip().lower()
        if ql:
            filtered = [r for r in rows if ql in json.dumps(r, ensure_ascii=False, default=str).lower()]
        else:
            filtered = rows
        return {"table": table_name, "total": len(filtered), "rows": filtered[:limit]}

    def query_league_table_rows(self, q: str = "", limit: int = 150) -> dict[str, Any]:
        """Return flattened LeagueTableRow entries across all league tables in the save."""
        raw_res = self.query_any_save_table("league-tables", q="", limit=5000)
        flat_rows: list[dict[str, Any]] = []
        for ti, tbl in enumerate(raw_res.get("rows", [])):
            if isinstance(tbl, dict) and isinstance(tbl.get("rows"), list):
                for row in tbl["rows"]:
                    if isinstance(row, dict):
                        total_split = row.get("total") or {
                            "played": row.get("played", 0),
                            "won": row.get("won", 0),
                            "drawn": row.get("drawn", 0),
                            "lost": row.get("lost", 0),
                            "goals_for": row.get("goals_for", 0),
                            "goals_against": row.get("goals_against", 0),
                            "points": row.get("points", 0),
                        }
                        flat_rows.append(
                            {
                                "table_index": ti,
                                "competition_id": tbl.get("competition_id"),
                                "competition_name": tbl.get("competition_name"),
                                "total": total_split,
                                **row,
                            }
                        )
            elif isinstance(tbl, dict):
                flat_rows.append(tbl)
        ql = q.strip().lower()
        if ql:
            filtered = [
                r for r in flat_rows
                if ql in (r.get("club_name") or "").lower()
                or ql == str(r.get("team_id"))
                or ql == str(r.get("club_uid"))
            ]
        else:
            filtered = flat_rows
        return {"table": "league-tables", "total": len(filtered), "rows": filtered[:limit]}

    def get_patches_cached(self, force_refresh: bool = False) -> list[dict[str, Any]]:
        with self._lock:
            if force_refresh or "patches" not in self._pregame_cache:
                self._pregame_cache["patches"] = get_all_patches_status(self.fm_dir)
            return self._pregame_cache["patches"]

    def get_streamed_tables_cached(self, only_unsortable: bool = True, force_refresh: bool = False) -> list[dict[str, Any]]:
        cache_key = f"streamed_tables_{int(only_unsortable)}"
        with self._lock:
            if force_refresh or cache_key not in self._pregame_cache:
                self._pregame_cache[cache_key] = scan_all_streamed_tables(
                    self.fm_dir, only_unsortable_by_default=only_unsortable
                )
            return self._pregame_cache[cache_key]

    def invalidate_patch_caches(self) -> None:
        with self._lock:
            self._pregame_cache.pop("patches", None)
            self._pregame_cache.pop("streamed_tables_0", None)
            self._pregame_cache.pop("streamed_tables_1", None)

    def apply_save_edits(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Apply granular player, contract, season-stats, club, finance, sponsorship, facility, stadium,
        staff, tactic, lineup, league-table, fixture, transfer-window, or extra-section edits and save."""
        with self._lock:
            if not self.save_path or not self.save_path.exists():
                raise FileNotFoundError("No active save file loaded")
            out_path_str = (payload.get("output_path") or "").strip()
            if out_path_str:
                out_path = Path(out_path_str).expanduser().resolve()
            else:
                stem = self.save_path.stem
                if not stem.endswith("_edited"):
                    out_path = self.save_path.with_name(f"{stem}_edited.fm")
                else:
                    out_path = self.save_path

            def _opt_int(d: Mapping[str, Any], key: str) -> int | None:
                val = d.get(key)
                if val is None or val == "":
                    return None
                return int(val)

            def _opt_str(d: Mapping[str, Any], key: str) -> str | None:
                val = d.get(key)
                if val is None or str(val).strip() == "":
                    return None
                return str(val).strip()

            applied: list[dict[str, Any]] = []
            with FM26Editor(self.save_path) as ed:
                if payload.get("game_date"):
                    applied.append(ed.set_game_date(str(payload["game_date"])))

                # 1. Player Edits
                if payload.get("player_uid") is not None:
                    p_uid = int(payload["player_uid"])
                    if payload.get("max_out_player"):
                        applied.append(ed.max_out_player(p_uid))
                    if payload.get("heal_injuries"):
                        applied.append(ed.heal_player_injuries(p_uid))
                    if payload.get("clear_suspensions"):
                        applied.append(ed.edit_player_suspensions(p_uid, clear=True))

                    p_fields = payload.get("player_fields") or {}
                    raw_scale = bool(payload.get("raw_attribute_scale", False))
                    raw_attrs = payload.get("attributes") or {}
                    attrs_clean: dict[str, int] = {}
                    max_attr_bound = 100 if raw_scale else 20
                    for k, v in raw_attrs.items():
                        if v is None or v == "":
                            continue
                        iv = max(1, min(max_attr_bound, int(v)))
                        if k == "free_kicks":
                            attrs_clean["free_kick_taking"] = iv
                        else:
                            attrs_clean[k] = iv

                    pos_clean: dict[str, int] = {}
                    for k, v in (payload.get("positions") or {}).items():
                        if v is None or v == "":
                            continue
                        pos_clean[k] = max(1, min(20, int(v)))

                    pers_clean: dict[str, int] = {}
                    for k, v in (payload.get("personality") or {}).items():
                        if v is None or v == "":
                            continue
                        pers_clean[k] = max(1, min(20, int(v)))

                    trait_bits_val = _opt_int(p_fields, "trait_bits")
                    if payload.get("trait_bits") is not None and payload.get("trait_bits") != "":
                        trait_bits_val = int(payload["trait_bits"])

                    if p_fields or attrs_clean or pos_clean or pers_clean or trait_bits_val is not None:
                        cond_pct = _opt_int(p_fields, "condition")
                        sharp_pct = _opt_int(p_fields, "sharpness")
                        applied.append(
                            ed.edit_player(
                                p_uid,
                                current_ability=_opt_int(p_fields, "ca"),
                                potential_ability=_opt_int(p_fields, "pa"),
                                home_reputation=_opt_int(p_fields, "home_rep"),
                                current_reputation=_opt_int(p_fields, "current_rep"),
                                world_reputation=_opt_int(p_fields, "world_rep"),
                                reputation_bucket=_opt_int(p_fields, "reputation_bucket"),
                                club_uid=_opt_int(p_fields, "club_uid"),
                                team_id=_opt_int(p_fields, "team_id"),
                                team_slot=_opt_int(p_fields, "team_slot") or 0,
                                club_join_date=_opt_str(p_fields, "club_join_date"),
                                transfer_value=_opt_int(p_fields, "value"),
                                condition_pct=float(cond_pct) if cond_pct is not None else None,
                                sharpness_pct=float(sharp_pct) if sharp_pct is not None else None,
                                age=_opt_int(p_fields, "age"),
                                birth_date=_opt_str(p_fields, "birth_date"),
                                nation_id=_opt_int(p_fields, "nation_id"),
                                height_cm=_opt_int(p_fields, "height_cm"),
                                squad_number=_opt_int(p_fields, "squad_number"),
                                body_type_code=_opt_int(p_fields, "body_type_code"),
                                left_foot=_opt_int(p_fields, "left_foot"),
                                right_foot=_opt_int(p_fields, "right_foot"),
                                raw_attribute_scale=raw_scale,
                                attributes=attrs_clean or None,
                                positions=pos_clean or None,
                                personality=pers_clean or None,
                                traits=trait_bits_val,
                            )
                        )

                    ct_fields = payload.get("contract_fields") or {}
                    clause_updates = payload.get("clause_updates") or ct_fields.get("clause_updates")
                    if any(
                        ct_fields.get(k) not in (None, "")
                        for k in (
                            "wage",
                            "start_date",
                            "contract_end",
                            "end_date",
                            "team_id",
                            "squad_status",
                            "contract_type",
                            "signing_or_loyalty_fee",
                            "agent_fee",
                            "package_bonus",
                            "option_or_reference_year",
                        )
                    ) or clause_updates:
                        try:
                            applied.append(
                                ed.edit_player_contract(
                                    p_uid,
                                    wage=_opt_int(ct_fields, "wage"),
                                    start_date=_opt_str(ct_fields, "start_date"),
                                    end_date=_opt_str(ct_fields, "end_date") or _opt_str(ct_fields, "contract_end"),
                                    team_id=_opt_int(ct_fields, "team_id"),
                                    squad_status=_opt_int(ct_fields, "squad_status"),
                                    contract_type=_opt_int(ct_fields, "contract_type"),
                                    signing_or_loyalty_fee=_opt_int(ct_fields, "signing_or_loyalty_fee"),
                                    agent_fee=_opt_int(ct_fields, "agent_fee"),
                                    package_bonus=_opt_int(ct_fields, "package_bonus"),
                                    option_or_reference_year=_opt_int(ct_fields, "option_or_reference_year"),
                                    clause_updates=clause_updates,
                                )
                            )
                        except KeyError:
                            pass

                    ss_fields = payload.get("season_stats_fields") or {}
                    if any(
                        ss_fields.get(k) not in (None, "")
                        for k in (
                            "starts",
                            "substitute_appearances",
                            "goals",
                            "assists",
                            "yellow_cards",
                            "red_cards",
                            "player_of_the_match",
                            "penalties_taken",
                            "penalties_scored",
                            "minutes",
                            "passes_attempted",
                            "passes_completed",
                        )
                    ):
                        try:
                            applied.append(
                                ed.edit_player_season_stats(
                                    p_uid,
                                    slot=str(ss_fields.get("slot") or "league"),
                                    start_appearances=_opt_int(ss_fields, "starts"),
                                    sub_appearances=_opt_int(ss_fields, "substitute_appearances"),
                                    goals=_opt_int(ss_fields, "goals"),
                                    assists=_opt_int(ss_fields, "assists"),
                                    yellow_cards=_opt_int(ss_fields, "yellow_cards"),
                                    red_cards=_opt_int(ss_fields, "red_cards"),
                                    player_of_the_match=_opt_int(ss_fields, "player_of_the_match"),
                                    penalties_taken=_opt_int(ss_fields, "penalties_taken"),
                                    penalties_scored=_opt_int(ss_fields, "penalties_scored"),
                                    minutes=_opt_int(ss_fields, "minutes"),
                                    passes_attempted=_opt_int(ss_fields, "passes_attempted"),
                                    passes_completed=_opt_int(ss_fields, "passes_completed"),
                                )
                            )
                        except Exception:
                            pass

                # 2. Club, Finance, Sponsorship & Facility Edits
                if payload.get("club_uid") is not None:
                    c_uid = int(payload["club_uid"])
                    cf = payload.get("club_fields") or {}
                    if any(
                        cf.get(k) not in (None, "")
                        for k in ("reputation", "last_league_position", "nation_id", "fa_nation_id", "city_id", "name", "short_name")
                    ):
                        applied.append(
                            ed.edit_club(
                                c_uid,
                                reputation=_opt_int(cf, "reputation"),
                                last_league_position=_opt_int(cf, "last_league_position"),
                                nation_id=_opt_int(cf, "nation_id"),
                                fa_nation_id=_opt_int(cf, "fa_nation_id"),
                                city_id=_opt_int(cf, "city_id"),
                                name=_opt_str(cf, "name"),
                                short_name=_opt_str(cf, "short_name"),
                            )
                        )
                    if any(
                        cf.get(k) not in (None, "")
                        for k in (
                            "balance",
                            "transfer_budget",
                            "transfer_budget_allocated",
                            "wage_budget",
                            "wage_payroll",
                            "income_excluding_transfers",
                            "expenditure_excluding_transfers",
                            "net_transfers",
                            "wage_bill",
                            "total_income",
                            "total_expenditure",
                        )
                    ):
                        tb_rem = _opt_int(cf, "transfer_budget")
                        tb_alloc = _opt_int(cf, "transfer_budget_allocated")
                        if tb_alloc is None and tb_rem is not None:
                            tb_alloc = tb_rem
                        try:
                            applied.append(
                                ed.edit_club_finances(
                                    c_uid,
                                    balance=_opt_int(cf, "balance"),
                                    transfer_budget_allocated=tb_alloc,
                                    transfer_budget_remaining=tb_rem,
                                    wage_budget_weekly=_opt_int(cf, "wage_budget"),
                                    wage_payroll_weekly=_opt_int(cf, "wage_payroll"),
                                    income_excluding_transfers=_opt_int(cf, "income_excluding_transfers"),
                                    expenditure_excluding_transfers=_opt_int(cf, "expenditure_excluding_transfers"),
                                    net_transfers=_opt_int(cf, "net_transfers"),
                                    wage_bill=_opt_int(cf, "wage_bill"),
                                    total_income=_opt_int(cf, "total_income"),
                                    total_expenditure=_opt_int(cf, "total_expenditure"),
                                    month_index=_opt_int(cf, "month_index") if _opt_int(cf, "month_index") is not None else -1,
                                )
                            )
                        except KeyError:
                            pass

                    if cf.get("corporate_facilities") not in (None, ""):
                        try:
                            applied.append(ed.edit_club_facilities(c_uid, corporate_facilities=int(cf["corporate_facilities"])))
                        except KeyError:
                            pass

                    for sp_upd in payload.get("sponsorship_updates") or []:
                        applied.append(
                            ed.edit_club_sponsorships(
                                c_uid,
                                sponsor_index=int(sp_upd.get("index", 0)),
                                kind=_opt_int(sp_upd, "kind"),
                                start_date=_opt_str(sp_upd, "start_date"),
                                end_date=_opt_str(sp_upd, "end_date"),
                                total_value=_opt_int(sp_upd, "total_value"),
                                annual_value=_opt_int(sp_upd, "annual_value"),
                            )
                        )

                # 3. Stadium Edits (all 14 fields)
                if payload.get("stadium_uid") is not None:
                    st_uid = int(payload["stadium_uid"])
                    sf = payload.get("stadium_fields") or {}
                    applied.append(
                        ed.edit_stadium(
                            st_uid,
                            capacity=_opt_int(sf, "capacity"),
                            all_seater_capacity=_opt_int(sf, "all_seater_capacity"),
                            expansion_capacity=_opt_int(sf, "expansion_capacity"),
                            owner_club_uid=_opt_int(sf, "owner_club_uid"),
                            pitch_length_dm=_opt_int(sf, "pitch_length_dm"),
                            pitch_width_dm=_opt_int(sf, "pitch_width_dm"),
                            pitch_min_length_dm=_opt_int(sf, "pitch_min_length_dm"),
                            pitch_min_width_dm=_opt_int(sf, "pitch_min_width_dm"),
                            pitch_max_length_dm=_opt_int(sf, "pitch_max_length_dm"),
                            pitch_max_width_dm=_opt_int(sf, "pitch_max_width_dm"),
                            built_date=_opt_str(sf, "built_date"),
                            rebuilt_date=_opt_str(sf, "rebuilt_date"),
                            name=_opt_str(sf, "name"),
                        )
                    )

                # 4. Staff Edits (CA, PA, Role r4, Contract, 26 block_40 attributes, 17 preferences, 8 personality)
                if payload.get("staff_uid") is not None:
                    s_uid = int(payload["staff_uid"])
                    if payload.get("max_out_staff"):
                        applied.append(ed.max_out_staff(s_uid))
                    else:
                        stf = payload.get("staff_fields") or {}
                        b40_key_to_idx = {key: idx for idx, key, _ in STAFF_BLOCK40_FIELDS}
                        s_attrs: dict[int | str, int] = {}
                        for k, v in (payload.get("staff_attributes") or {}).items():
                            if v not in (None, ""):
                                mapped_k = b40_key_to_idx.get(str(k), k)
                                s_attrs[mapped_k] = int(v)
                        s_prefs = {
                            k: int(v)
                            for k, v in (payload.get("staff_preferences") or {}).items()
                            if v not in (None, "")
                        }
                        s_pers = {
                            k: int(v)
                            for k, v in (payload.get("staff_personality") or {}).items()
                            if v not in (None, "")
                        }
                        if any(
                            stf.get(k) not in (None, "")
                            for k in ("ca", "pa", "role_r4", "birth_date", "age", "nation_id", "wage", "contract_start", "contract_end", "team_id")
                        ) or s_attrs or s_prefs or s_pers:
                            applied.append(
                                ed.edit_staff(
                                    s_uid,
                                    current_ability=_opt_int(stf, "ca"),
                                    potential_ability=_opt_int(stf, "pa"),
                                    role_r4=_opt_int(stf, "role_r4"),
                                    birth_date=_opt_str(stf, "birth_date"),
                                    age=_opt_int(stf, "age"),
                                    nation_id=_opt_int(stf, "nation_id"),
                                    wage=_opt_int(stf, "wage"),
                                    contract_start=_opt_str(stf, "contract_start"),
                                    contract_end=_opt_str(stf, "contract_end"),
                                    team_id=_opt_int(stf, "team_id"),
                                    block_40_attributes=s_attrs or None,
                                    preferences=s_prefs or None,
                                    personality=s_pers or None,
                                )
                            )

                # 5. League Table Edits (Total + Home + Away)
                if payload.get("league_table_edit"):
                    lte = payload["league_table_edit"]
                    applied.append(
                        ed.edit_league_table_row(
                            int(lte["team_id"] if "team_id" in lte else lte["team"]),
                            won=_opt_int(lte, "won"),
                            drawn=_opt_int(lte, "drawn"),
                            lost=_opt_int(lte, "lost"),
                            goals_for=_opt_int(lte, "goals_for"),
                            goals_against=_opt_int(lte, "goals_against"),
                            points=_opt_int(lte, "points"),
                            home_won=_opt_int(lte, "home_won"),
                            home_drawn=_opt_int(lte, "home_drawn"),
                            home_lost=_opt_int(lte, "home_lost"),
                            home_goals_for=_opt_int(lte, "home_goals_for"),
                            home_goals_against=_opt_int(lte, "home_goals_against"),
                            home_points=_opt_int(lte, "home_points"),
                            away_won=_opt_int(lte, "away_won"),
                            away_drawn=_opt_int(lte, "away_drawn"),
                            away_lost=_opt_int(lte, "away_lost"),
                            away_goals_for=_opt_int(lte, "away_goals_for"),
                            away_goals_against=_opt_int(lte, "away_goals_against"),
                            away_points=_opt_int(lte, "away_points"),
                        )
                    )

                # 6. Tactic & Lineup Edits
                if payload.get("tactic_edit"):
                    te = payload["tactic_edit"]
                    applied.append(
                        ed.edit_tactic_record(
                            tactic_index=int(te.get("tactic_index", 0)),
                            mentality=_opt_int(te, "mentality"),
                            style_code=_opt_str(te, "style_code"),
                            name=_opt_str(te, "name"),
                        )
                    )
                if payload.get("lineup_edit"):
                    le = payload["lineup_edit"]
                    applied.append(
                        ed.edit_tactics_lineup(
                            slot_index=int(le["slot_index"]),
                            player_uid_or_name=le.get("player"),
                            team_block_index=int(le.get("team_block_index", 0)),
                        )
                    )

                # 7. Transfer Window Edits
                if payload.get("transfer_window_edit"):
                    twe = payload["transfer_window_edit"]
                    applied.append(
                        ed.edit_transfer_window(
                            window_index=int(twe.get("window_index", 0)),
                            start_day=_opt_int(twe, "start_day"),
                            start_month=_opt_int(twe, "start_month"),
                            end_day=_opt_int(twe, "end_day"),
                            end_month=_opt_int(twe, "end_month"),
                            window_type=_opt_int(twe, "window_type"),
                        )
                    )

                # 8. Extra Sections (Hall of Fame, Takeovers, Shortlist, Name Pool)
                if payload.get("hall_of_fame_edit"):
                    hfe = payload["hall_of_fame_edit"]
                    applied.append(
                        ed.edit_hall_of_fame_entry(
                            entry_index=int(hfe.get("entry_index", 0)),
                            first_name=_opt_str(hfe, "first_name"),
                            last_name=_opt_str(hfe, "last_name"),
                            common_name=_opt_str(hfe, "common_name"),
                            hall_of_fame_points=_opt_int(hfe, "hall_of_fame_points"),
                        )
                    )
                if payload.get("name_pool_edit"):
                    npe = payload["name_pool_edit"]
                    applied.append(
                        ed.rename_name_pool_entry(
                            pool_kind=str(npe["pool_kind"]),
                            name_id=int(npe["name_id"]),
                            new_name=str(npe["new_name"]),
                        )
                    )

                save_summary = ed.save(out_path, validate_output=bool(payload.get("validate", True)))

            self.save_path = out_path
            self._save_cache.clear()
            return {
                "ok": True,
                "output_path": str(out_path),
                "save_summary": save_summary,
                "edits": applied,
                "active_save": self._ensure_save_index().get("save_info"),
            }

    def get_pregame_db_summary(self) -> dict[str, Any]:
        with self._lock:
            if "summary" not in self._pregame_cache:
                master = extract_master_db_tables(self.fm_dir, sample_limit=60)
                if isinstance(master, dict) and "tables" not in master:
                    master["tables"] = master.get("client_db_tables") or master.get("server_db_tables") or []
                people = extract_pregame_people_and_history_db(self.fm_dir)
                multi = extract_multi_version_database_evolution(self.fm_dir)
                self._pregame_cache["summary"] = {
                    "fm_dir": str(self.fm_dir),
                    "master_db": master,
                    "people_db": people,
                    "multi_version": multi,
                }
            return self._pregame_cache["summary"]


class _StudioThreadingHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 64


def build_studio_handler(state: StudioState) -> type[BaseHTTPRequestHandler]:
    from fm26save.studio_ui import STUDIO_HTML_PAGE

    class StudioRequestHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            pass

        def _send_json(self, payload: Any, status: int = 200) -> None:
            try:
                raw = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(raw)
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                pass

        def _send_html(self, html: str) -> None:
            try:
                raw = html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                pass

        def _read_body_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0") or 0)
            if length <= 0:
                return {}
            body = self.rfile.read(length).decode("utf-8", errors="replace")
            return json.loads(body) if body.strip() else {}

        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path
            qs = urllib.parse.parse_qs(parsed.query)
            first = lambda k, d="": qs.get(k, [d])[0]

            try:
                if path in ("/", "/index.html"):
                    self._send_html(STUDIO_HTML_PAGE)
                    return

                if path == "/api/overview":
                    lang = first("game_lang", "turkish")
                    self._send_json(state.get_overview(game_lang=lang))
                    return

                if path == "/api/game-terms":
                    lang = first("lang", "turkish")
                    self._send_json(get_game_terms(lang, state.fm_dir))
                    return

                if path == "/api/players":
                    res = state.query_players(
                        q=first("q", ""),
                        pos=first("pos", ""),
                        club=first("club", ""),
                        min_ca=int(first("min_ca", "0") or 0),
                        max_age=int(first("max_age", "99") or 99),
                        sort_by=first("sort_by", "ca"),
                        limit=int(first("limit", "100") or 100),
                    )
                    self._send_json(res)
                    return

                if path == "/api/player-detail":
                    uid = int(first("uid", "0"))
                    self._send_json(state.get_player_detail(uid))
                    return

                if path == "/api/clubs":
                    res = state.query_clubs(
                        q=first("q", ""),
                        sort_by=first("sort_by", "reputation"),
                        limit=int(first("limit", "100") or 100),
                    )
                    self._send_json(res)
                    return

                if path == "/api/club-detail":
                    uid = int(first("uid", "0"))
                    self._send_json(state.get_club_detail(uid))
                    return

                if path == "/api/staff":
                    res = state.query_staff(
                        q=first("q", ""),
                        role=first("role", ""),
                        limit=int(first("limit", "100") or 100),
                    )
                    self._send_json(res)
                    return

                if path == "/api/staff-detail":
                    uid = int(first("uid", "0"))
                    self._send_json(state.get_staff_detail(uid))
                    return

                if path == "/api/stadiums":
                    res = state.query_stadiums(
                        q=first("q", ""),
                        limit=int(first("limit", "100") or 100),
                    )
                    self._send_json(res)
                    return

                if path == "/api/league-tables":
                    q = first("q", "")
                    limit = int(first("limit", "150") or 150)
                    self._send_json(state.query_league_table_rows(q=q, limit=limit))
                    return

                if path == "/api/save-sections":
                    idx = state._ensure_save_index()
                    self._send_json({"sections": idx.get("sections", [])})
                    return

                if path == "/api/save-table":
                    tbl = first("table", "players")
                    q = first("q", "")
                    limit = int(first("limit", "100") or 100)
                    self._send_json(state.query_any_save_table(tbl, q=q, limit=limit))
                    return

                if path == "/api/dof":
                    if not state.save_path or not state.save_path.exists():
                        self._send_json({"error": "No active save file"}, status=400)
                        return
                    club_uid_str = first("club_uid", "")
                    club_uid = int(club_uid_str) if club_uid_str.isdigit() else None
                    coach_q = first("coach", "") or None
                    if coach_q and coach_q.isdigit():
                        coach_q = int(coach_q)  # type: ignore[assignment]
                    with FM26Save(state.save_path) as sv:
                        dash = build_dof_dashboard(sv, club_uid=club_uid, coach_uid_or_name=coach_q)
                    self._send_json(dash)
                    return

                if path == "/api/pregame-db":
                    self._send_json(state.get_pregame_db_summary())
                    return

                if path == "/api/optimization":
                    self._send_json(inspect_disk_and_optimization_state(state.fm_dir))
                    return

                if path == "/api/patches":
                    force = first("refresh", "0") == "1"
                    self._send_json({"patches": state.get_patches_cached(force_refresh=force)})
                    return

                if path == "/api/patches/streamed-tables":
                    only_unsortable = first("only_unsortable", "1") != "0"
                    force = first("refresh", "0") == "1"
                    tables = state.get_streamed_tables_cached(only_unsortable=only_unsortable, force_refresh=force)
                    self._send_json({"total": len(tables), "tables": tables})
                    return

                if path == "/api/rules":
                    ver = first("db_version", "") or None
                    self._send_json(list_edt_lnc_dbc_files(state.fm_dir, db_version=ver))
                    return

                if path == "/api/rules/text-file":
                    rel = first("rel_path", "")
                    ver = first("db_version", "") or None
                    self._send_json(read_text_rule_file(state.fm_dir, rel, db_version=ver))
                    return

                self._send_json({"error": f"Unknown endpoint: {path}"}, status=404)
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                pass
            except Exception as exc:
                self._send_json({"error": str(exc), "trace": traceback.format_exc()}, status=500)

        def do_POST(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path
            try:
                body = self._read_body_json()

                if path == "/api/context":
                    res = state.set_context(
                        save_path=body.get("save_path"),
                        fm_dir=body.get("fm_dir"),
                    )
                    self._send_json(res)
                    return

                if path == "/api/save-edit":
                    res = state.apply_save_edits(body)
                    self._send_json(res)
                    return

                if path == "/api/dof-hire":
                    if not state.save_path:
                        raise FileNotFoundError("No active save file")
                    coach_key = body.get("coach")
                    if str(coach_key).isdigit():
                        coach_key = int(coach_key)
                    club_uid = int(body["club_uid"]) if body.get("club_uid") else None
                    years = int(body.get("years", 3))
                    out_p = state.save_path.with_name(f"{state.save_path.stem}_DoF.fm")
                    res = hire_head_coach(state.save_path, coach_key, out_p, club_uid=club_uid, contract_years=years)
                    state.save_path = out_p
                    state._save_cache.clear()
                    self._send_json({"ok": True, "result": res, "active_save": state._ensure_save_index().get("save_info")})
                    return

                if path == "/api/optimization/boot-config":
                    res = write_boot_config(
                        state.fm_dir,
                        body.get("values") or {},
                        raw_text=body.get("raw_text"),
                    )
                    self._send_json(res)
                    return

                if path == "/api/optimization/boot-preset":
                    res = apply_boot_preset(state.fm_dir, str(body.get("preset", "balanced")))
                    self._send_json(res)
                    return

                if path == "/api/optimization/boot-restore":
                    res = restore_boot_config(state.fm_dir)
                    self._send_json(res)
                    return

                if path == "/api/optimization/videos-toggle":
                    disable = bool(body.get("disable", True))
                    names = body.get("video_names")
                    res = toggle_intro_videos(state.fm_dir, disable=disable, video_names=names)
                    self._send_json(res)
                    return

                if path == "/api/patches/apply":
                    pkey = str(body.get("key", ""))
                    max_p = int(body["max_players"]) if body.get("max_players") not in (None, "") else None
                    patch = resolve_patch(pkey)
                    if patch is None:
                        raise KeyError(f"Unknown patch key: {pkey}")
                    rc = apply_ui_patch(state.fm_dir, patch, dry_run=False, max_players=max_p)
                    state.invalidate_patch_caches()
                    self._send_json({"ok": rc == 0, "rc": rc, "patches": state.get_patches_cached()})
                    return

                if path == "/api/patches/apply-all-sorting":
                    for p in PATCHES.values():
                        if p.key.startswith("ui-sort-") or p.key.endswith("-sorting"):
                            apply_ui_patch(state.fm_dir, p, dry_run=False)
                    state.invalidate_patch_caches()
                    self._send_json({"ok": True, "patches": state.get_patches_cached(force_refresh=True)})
                    return

                if path == "/api/patches/restore":
                    pkey = str(body.get("key", ""))
                    patch = resolve_patch(pkey)
                    if patch is None:
                        raise KeyError(f"Unknown patch key: {pkey}")
                    rc = restore_ui_patch(state.fm_dir, patch)
                    state.invalidate_patch_caches()
                    self._send_json({"ok": rc == 0, "rc": rc, "patches": state.get_patches_cached()})
                    return

                if path == "/api/patches/streamed-table-toggle":
                    bname = str(body["bundle"])
                    off = int(body["offset"])
                    ds = int(body["disable_sorting"])
                    res = set_streamed_table_sorting(state.fm_dir, bname, off, ds)
                    state.invalidate_patch_caches()
                    self._send_json(res)
                    return

                if path == "/api/rules/sugardaddy":
                    ver = body.get("db_version") or None
                    entries = body.get("entries") or []
                    res = write_sugardaddy_edt(state.fm_dir, entries, db_version=ver)
                    self._send_json(res)
                    return

                if path == "/api/rules/text-file":
                    ver = body.get("db_version") or None
                    rel = str(body["rel_path"])
                    content = str(body.get("content", ""))
                    res = write_text_rule_file(state.fm_dir, rel, content, db_version=ver)
                    self._send_json(res)
                    return

                if path == "/api/rules/toggle-file":
                    ver = body.get("db_version") or None
                    rel = str(body["rel_path"])
                    disable = bool(body.get("disable", True))
                    res = toggle_rule_or_dbc_file(state.fm_dir, rel, disable=disable, db_version=ver)
                    self._send_json(res)
                    return

                self._send_json({"error": f"Unknown POST endpoint: {path}"}, status=404)
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                pass
            except Exception as exc:
                self._send_json({"error": str(exc), "trace": traceback.format_exc()}, status=500)

    return StudioRequestHandler


def serve_studio(
    save_path: str | os.PathLike[str] | None = None,
    *,
    fm_dir: str | os.PathLike[str] | None = None,
    host: str = "127.0.0.1",
    port: int = 8780,
    open_browser: bool = True,
) -> None:
    """Start the local multi-threaded All-in-One FM27 / FM26 Studio Web Application."""
    sp = Path(save_path).expanduser().resolve() if save_path else None
    fd = Path(fm_dir).expanduser().resolve() if fm_dir else None
    state = StudioState(save_path=sp, fm_dir=fd)
    handler_cls = build_studio_handler(state)
    server = _StudioThreadingHTTPServer((host, port), handler_cls)
    threading.Thread(target=state._ensure_save_index, daemon=True).start()
    url = f"http://{host}:{port}"
    print("=" * 78)
    print("  FM27 / FM26 ALL-IN-ONE STUDIO — KONTROL & VERİTABANI MERKEZİ")
    print("=" * 78)
    print(f"  Web Arayüzü URL      : {url}")
    print(f"  Aktif Kayıt (.fm)    : {state.save_path or '(Otomatik bulunamadı — UI üzerinden seçin)'}")
    print(f"  Aktif Oyun Dizini    : {state.fm_dir}")
    print("  Durdurmak için       : Ctrl+C")
    print("=" * 78)
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nFM Studio sunucusu kapatıldı.")
    finally:
        server.server_close()
