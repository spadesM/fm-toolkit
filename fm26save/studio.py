"""FM27 / FM26 All-in-One Studio Backend Server & API Engine.

Unifies the 3 Core Pillars + Independent In-Game Term Localization:
1. Pillar 1 — Save (`.fm`) & Pre-Game Installation Databases Visualizer & Live Editor
2. Pillar 2 — Game Optimization Suite (`boot.config`, URP profiles, Video bypass, Disk footprint)
3. Pillar 3 — Game File & Binary/Bundle Patcher (`game_plugin.dll` 50-player limit, 10+ UI table
   sorting patches, all 252 `StreamedTable` sorting unlockers, and `.edt`/`.lnc`/`.dbc` visual editor)
4. Cross-Cutting — Independent In-Game Term Localization (`21` official FM `.ltc` languages).
"""

from __future__ import annotations

import json
import os
import traceback
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from fm26save import ALL_28_TABLES, FM26Editor, FM26Save, serialize_record
from fm26save.dof import build_dof_dashboard, hire_head_coach, recommend_transfer_targets, scan_coach_candidates
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
    # Sort FM27 saves first, named saves before "last save overwrite backup.fm"
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
    """In-memory state manager and cache for the active `.fm` save and FM installation directory."""

    def __init__(self, save_path: Path | None = None, fm_dir: Path | None = None) -> None:
        saves = discover_save_files()
        installs = discover_fm_installations()
        if save_path is None and saves:
            # Prefer a base save over _edited / _DoF copies if available
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
        if "indexed" in self._save_cache:
            return self._save_cache["indexed"]
        if not self.save_path or not self.save_path.exists():
            return {}
        with FM26Save(self.save_path) as sv:
            info = sv.info
            clubs_raw = sv.table("clubs")
            club_map: dict[int, str] = {}
            for c in clubs_raw:
                club_map[c.uid] = c.name or c.short_name or f"Club #{c.uid}"

            contract_by_person: dict[int, Any] = {}
            try:
                for ct in sv.table("contracts"):
                    if ct.player_uid not in contract_by_person:
                        contract_by_person[ct.player_uid] = ct
            except Exception:
                pass

            try:
                finances_by_club = {f.club_uid: f for f in sv.table("finances")}
            except Exception:
                finances_by_club = {}
            try:
                facilities_by_club = {f.club_uid: f for f in sv.table("facilities")}
            except Exception:
                facilities_by_club = {}
            try:
                stadiums_raw = sv.table("stadiums")
            except Exception:
                stadiums_raw = ()
            injuries_by_player: dict[int, list[str]] = {}
            try:
                for inj in sv.table("injuries"):
                    if inj.player_uid is not None and str(inj.kind) == "typed":
                        injuries_by_player.setdefault(inj.player_uid, []).append(
                            inj.type_name or f"Injury #{inj.type_id}"
                        )
            except Exception:
                pass

            players_list: list[dict[str, Any]] = []
            players_by_uid: dict[int, dict[str, Any]] = {}
            for p in sv.table("players"):
                if not p.ability:
                    continue
                ct = p.contract or contract_by_person.get(p.uid)
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
                row = {
                    "uid": p.uid,
                    "name": p.name or f"{p.first_name or ''} {p.last_name or ''}".strip() or f"Player #{p.uid}",
                    "first_name": p.first_name or "",
                    "last_name": p.last_name or "",
                    "age": p.age or 0,
                    "birth_date": str(p.birth_date) if p.birth_date else "",
                    "nationality_id": p.nation_id,
                    "nationality": sv.nation_name(p.nation_id, lang="tr"),
                    "club_uid": club_uid,
                    "club": club_name,
                    "ca": p.ability.current or 0,
                    "pa": p.ability.potential or 0,
                    "best_pos": best_pos,
                    "value": p.transfer_value or 0,
                    "wage": ct.wage if ct and ct.wage else 0,
                    "contract_end": str(ct.end) if ct and ct.end else "",
                    "squad_status": sq_status_raw,
                    "height_cm": p.height_cm or 0,
                    "condition": round((p.raw_condition or 0) / 100),
                    "sharpness": round((p.raw_match_sharpness or 0) / 100),
                    "home_rep": p.reputation.home if p.reputation else 0,
                    "current_rep": p.reputation.current if p.reputation else 0,
                    "world_rep": p.reputation.world if p.reputation else 0,
                    "injuries": injuries_by_player.get(p.uid, []),
                    "suspensions_count": len(p.suspensions) if p.suspensions else 0,
                }
                players_list.append(row)
                players_by_uid[p.uid] = row

            players_list.sort(key=lambda r: (r["ca"], r["pa"]), reverse=True)

            clubs_list: list[dict[str, Any]] = []
            for c in clubs_raw:
                fin = finances_by_club.get(c.uid)
                fac = facilities_by_club.get(c.uid)
                corp_raw = getattr(fac.corporate_facilities, "raw", 0) if fac and fac.corporate_facilities else 0
                clubs_list.append({
                    "uid": c.uid,
                    "name": c.name or c.short_name or f"Club #{c.uid}",
                    "short_name": c.short_name or "",
                    "reputation": c.reputation or 0,
                    "balance": fin.balance if fin and fin.balance is not None else 0,
                    "transfer_budget": fin.transfer_budget_remaining if fin and fin.transfer_budget_remaining is not None else 0,
                    "wage_budget": fin.wage_budget_weekly if fin and fin.wage_budget_weekly is not None else 0,
                    "corporate_facilities": corp_raw,
                })
            clubs_list.sort(key=lambda r: r["reputation"], reverse=True)

            stadiums_list: list[dict[str, Any]] = []
            for st in stadiums_raw:
                st_label = st.name
                if not st_label and st.home_club_names:
                    st_label = f"{st.home_club_names[0]} Stadyumu (#{st.uid})"
                elif not st_label and st.owner_club_name:
                    st_label = f"{st.owner_club_name} Stadyumu (#{st.uid})"
                elif not st_label:
                    st_label = f"Stadium #{st.uid}"
                cap = st.capacity if st.capacity else st.all_seater_capacity
                stadiums_list.append({
                    "uid": st.uid,
                    "name": st_label,
                    "capacity": cap or 0,
                    "all_seater_capacity": st.all_seater_capacity or 0,
                    "expansion_capacity": st.expansion_capacity or 0,
                })
            stadiums_list.sort(key=lambda r: r["all_seater_capacity"], reverse=True)

            try:
                staff_enriched = sv.staff_enriched()
                for s in staff_enriched:
                    cuid = s.get("club_uid")
                    s["club_name"] = club_map.get(cuid, "") if cuid else (s.get("club_name") or "")
                    s["role_name"] = s.get("role_tr") or s.get("role_en") or s.get("departments") or ""
                staff_enriched.sort(key=lambda r: (r.get("ca") or 0, r.get("pa") or 0), reverse=True)
            except Exception:
                staff_enriched = []

            league_rows: list[dict[str, Any]] = []
            try:
                for lt in sv.table("league-tables"):
                    league_rows.append(serialize_record(lt))
            except Exception:
                pass

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
                "clubs": clubs_list,
                "stadiums": stadiums_list,
                "staff": staff_enriched,
                "league_tables": league_rows,
                "sections": sections,
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
            if pu and p["best_pos"] != pu:
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
        if not self.save_path or not self.save_path.exists():
            raise FileNotFoundError("No active save file")
        idx = self._ensure_save_index()
        summary = idx.get("players_by_uid", {}).get(uid, {})
        with FM26Save(self.save_path) as sv:
            target = None
            for p in sv.table("players"):
                if p.uid == uid:
                    target = p
                    break
            if target is None:
                raise KeyError(f"Player UID {uid} not found")
            attrs: dict[str, int] = {}
            if target.attributes:
                for grp_cols in PLAYER_ATTRIBUTE_GROUPS.values():
                    for col in grp_cols:
                        val = getattr(target.attributes, col, None)
                        if val is not None:
                            attrs[col] = int(val)
            # Also map free_kick_taking -> free_kicks if present on model
            if target.attributes and hasattr(target.attributes, "free_kick_taking") and "free_kicks" not in attrs:
                attrs["free_kicks"] = int(getattr(target.attributes, "free_kick_taking") or 0)
            positions: dict[str, int] = {}
            if target.positions:
                for code, term_key, attr_name in POSITION_FIELD_MAP:
                    positions[code] = int(getattr(target.positions, attr_name, 0) or 0)
            role_breakdown = sv.player_role_breakdown(target, top_n_per_group=5)
            traits = [str(t) for t in (getattr(target, "traits", None) or [])]
            return {
                "summary": summary,
                "attributes": attrs,
                "positions": positions,
                "traits": traits,
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
        if sort_by in ("reputation", "balance", "transfer_budget", "wage_budget"):
            filtered.sort(key=lambda r: r.get(sort_by) or 0, reverse=True)
        return {"total": len(filtered), "rows": filtered[:limit]}

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
            if rl and rl not in srole:
                continue
            filtered.append(s)
        return {"total": len(filtered), "rows": filtered[:limit]}

    def query_stadiums(self, q: str = "", limit: int = 100) -> dict[str, Any]:
        idx = self._ensure_save_index()
        stadiums = idx.get("stadiums", [])
        ql = q.strip().lower()
        filtered = [s for s in stadiums if not ql or ql in s["name"].lower() or ql == str(s["uid"])]
        return {"total": len(filtered), "rows": filtered[:limit]}

    def query_any_save_table(self, table_name: str, q: str = "", limit: int = 100) -> dict[str, Any]:
        if not self.save_path or not self.save_path.exists():
            return {"table": table_name, "total": 0, "rows": []}
        with FM26Save(self.save_path) as sv:
            if table_name == "hall_of_fame":
                raw_rows = sv.hall_of_fame(limit=limit * 2)
            elif table_name == "takeovers":
                raw_rows = sv.board_takeovers()
            elif table_name == "shortlists":
                raw_rows = sv.shortlists(limit=limit * 2)
            elif table_name == "offers":
                raw_rows = sv.contract_offers()
            elif table_name == "agents":
                raw_rows = sv.agents()
            elif table_name == "news":
                raw_rows = sv.news_items()
            else:
                raw_rows = [serialize_record(r) for r in sv.table(table_name)]
        ql = q.strip().lower()
        if ql:
            filtered = [r for r in raw_rows if ql in json.dumps(r, ensure_ascii=False).lower()]
        else:
            filtered = raw_rows
        return {"table": table_name, "total": len(filtered), "rows": filtered[:limit]}

    def apply_save_edits(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Apply player, club, stadium, staff, league-table, or game-date edits and write a `.fm` save."""
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

        applied: list[dict[str, Any]] = []
        with FM26Editor(self.save_path) as ed:
            if payload.get("game_date"):
                applied.append(ed.set_game_date(str(payload["game_date"])))

            if payload.get("player_uid") is not None:
                p_uid = int(payload["player_uid"])
                if payload.get("max_out_player"):
                    applied.append(ed.max_out_player(p_uid))
                if payload.get("heal_injuries"):
                    applied.append(ed.heal_player_injuries(p_uid))
                if payload.get("clear_suspensions"):
                    applied.append(ed.edit_player_suspensions(p_uid, clear_all=True))

                p_fields = payload.get("player_fields") or {}
                raw_attrs = payload.get("attributes") or {}
                # Map canonical 'free_kicks' back to editor attribute name if needed
                attrs_clean: dict[str, int] = {}
                for k, v in raw_attrs.items():
                    if v is None or v == "":
                        continue
                    iv = max(1, min(20, int(v)))
                    attrs_clean[k] = iv
                    if k == "free_kicks":
                        attrs_clean["free_kick_taking"] = iv
                pos_clean: dict[str, int] = {}
                for k, v in (payload.get("positions") or {}).items():
                    if v is None or v == "":
                        continue
                    pos_clean[k] = max(1, min(20, int(v)))

                if p_fields or attrs_clean or pos_clean:
                    applied.append(
                        ed.edit_player(
                            p_uid,
                            current_ability=int(p_fields["ca"]) if p_fields.get("ca") is not None else None,
                            potential_ability=int(p_fields["pa"]) if p_fields.get("pa") is not None else None,
                            home_reputation=int(p_fields["home_rep"]) if p_fields.get("home_rep") is not None else None,
                            current_reputation=int(p_fields["current_rep"]) if p_fields.get("current_rep") is not None else None,
                            world_reputation=int(p_fields["world_rep"]) if p_fields.get("world_rep") is not None else None,
                            condition=int(p_fields["condition"]) if p_fields.get("condition") is not None else None,
                            match_sharpness=int(p_fields["sharpness"]) if p_fields.get("sharpness") is not None else None,
                            transfer_value=int(p_fields["value"]) if p_fields.get("value") is not None else None,
                            age=int(p_fields["age"]) if p_fields.get("age") is not None else None,
                            height_cm=int(p_fields["height_cm"]) if p_fields.get("height_cm") is not None else None,
                            squad_number=int(p_fields["squad_number"]) if p_fields.get("squad_number") is not None else None,
                            attributes=attrs_clean or None,
                            positions=pos_clean or None,
                        )
                    )
                ct_fields = payload.get("contract_fields") or {}
                if any(ct_fields.get(k) not in (None, "") for k in ("wage", "contract_end", "squad_status")):
                    applied.append(
                        ed.edit_player_contract(
                            p_uid,
                            wage=int(ct_fields["wage"]) if ct_fields.get("wage") not in (None, "") else None,
                            end_date=str(ct_fields["contract_end"]) if ct_fields.get("contract_end") else None,
                            squad_status=int(ct_fields["squad_status"]) if ct_fields.get("squad_status") not in (None, "") else None,
                        )
                    )

            if payload.get("club_uid") is not None:
                c_uid = int(payload["club_uid"])
                cf = payload.get("club_fields") or {}
                if cf.get("reputation") is not None:
                    applied.append(ed.edit_club(c_uid, reputation=int(cf["reputation"])))
                if any(cf.get(k) is not None for k in ("balance", "transfer_budget", "wage_budget")):
                    tb = int(cf["transfer_budget"]) if cf.get("transfer_budget") is not None else None
                    applied.append(
                        ed.edit_club_finances(
                            c_uid,
                            balance=int(cf["balance"]) if cf.get("balance") is not None else None,
                            transfer_budget_allocated=tb,
                            transfer_budget_remaining=tb,
                            wage_budget_weekly=int(cf["wage_budget"]) if cf.get("wage_budget") is not None else None,
                        )
                    )
                if cf.get("corporate_facilities") is not None:
                    applied.append(ed.edit_club_facilities(c_uid, corporate_facilities=int(cf["corporate_facilities"])))

            if payload.get("stadium_uid") is not None:
                st_uid = int(payload["stadium_uid"])
                sf = payload.get("stadium_fields") or {}
                applied.append(
                    ed.edit_stadium(
                        st_uid,
                        capacity=int(sf["capacity"]) if sf.get("capacity") is not None else None,
                        all_seater_capacity=int(sf["all_seater_capacity"]) if sf.get("all_seater_capacity") is not None else None,
                    )
                )

            if payload.get("staff_uid") is not None:
                s_uid = int(payload["staff_uid"])
                if payload.get("max_out_staff"):
                    applied.append(ed.max_out_staff(s_uid))
                else:
                    stf = payload.get("staff_fields") or {}
                    s_attrs = payload.get("staff_attributes") or {}
                    if stf.get("ca") is not None or stf.get("pa") is not None or s_attrs:
                        applied.append(
                            ed.edit_staff(
                                s_uid,
                                current_ability=int(stf["ca"]) if stf.get("ca") is not None else None,
                                potential_ability=int(stf["pa"]) if stf.get("pa") is not None else None,
                                attributes={k: int(v) for k, v in s_attrs.items() if v is not None} if s_attrs else None,
                            )
                        )

            if payload.get("league_table_edit"):
                lte = payload["league_table_edit"]
                applied.append(
                    ed.edit_league_table_row(
                        lte["team"],
                        won=int(lte["won"]) if lte.get("won") not in (None, "") else None,
                        drawn=int(lte["drawn"]) if lte.get("drawn") not in (None, "") else None,
                        lost=int(lte["lost"]) if lte.get("lost") not in (None, "") else None,
                        goals_for=int(lte["goals_for"]) if lte.get("goals_for") not in (None, "") else None,
                        goals_against=int(lte["goals_against"]) if lte.get("goals_against") not in (None, "") else None,
                        points=int(lte["points"]) if lte.get("points") not in (None, "") else None,
                    )
                )

            save_summary = ed.save(out_path, validate_output=bool(payload.get("validate", True)))

        # Switch active save to the newly written output save so live UI reflects changes immediately!
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
        if "summary" not in self._pregame_cache:
            master = extract_master_db_tables(self.fm_dir, sample_limit=60)
            people = extract_pregame_people_and_history_db(self.fm_dir)
            multi = extract_multi_version_database_evolution(self.fm_dir)
            self._pregame_cache["summary"] = {
                "fm_dir": str(self.fm_dir),
                "master_db": master,
                "people_db": people,
                "multi_version": multi,
            }
        return self._pregame_cache["summary"]


def build_studio_handler(state: StudioState) -> type[BaseHTTPRequestHandler]:
    from fm26save.studio_ui import STUDIO_HTML_PAGE

    class StudioRequestHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            pass

        def _send_json(self, payload: Any, status: int = 200) -> None:
            raw = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(raw)

        def _send_html(self, html: str) -> None:
            raw = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

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

                if path == "/api/staff":
                    res = state.query_staff(
                        q=first("q", ""),
                        role=first("role", ""),
                        limit=int(first("limit", "100") or 100),
                    )
                    self._send_json(res)
                    return

                if path == "/api/stadiums":
                    res = state.query_stadiums(
                        q=first("q", ""),
                        limit=int(first("limit", "100") or 100),
                    )
                    self._send_json(res)
                    return

                if path == "/api/league-tables":
                    idx = state._ensure_save_index()
                    rows = idx.get("league_tables", [])
                    q = first("q", "").strip().lower()
                    if q:
                        rows = [r for r in rows if q in json.dumps(r, ensure_ascii=False).lower()]
                    self._send_json({"total": len(rows), "rows": rows[: int(first("limit", "150") or 150)]})
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
                    self._send_json({"patches": get_all_patches_status(state.fm_dir)})
                    return

                if path == "/api/patches/streamed-tables":
                    only_unsortable = first("only_unsortable", "1") != "0"
                    tables = scan_all_streamed_tables(state.fm_dir, only_unsortable_by_default=only_unsortable)
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
                    res = write_boot_config(state.fm_dir, body.get("values") or {})
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
                    self._send_json({"ok": rc == 0, "rc": rc, "patches": get_all_patches_status(state.fm_dir)})
                    return

                if path == "/api/patches/apply-all-sorting":
                    for p in PATCHES.values():
                        if p.key.endswith("-sorting"):
                            apply_ui_patch(state.fm_dir, p, dry_run=False)
                    self._send_json({"ok": True, "patches": get_all_patches_status(state.fm_dir)})
                    return

                if path == "/api/patches/restore":
                    pkey = str(body.get("key", ""))
                    patch = resolve_patch(pkey)
                    if patch is None:
                        raise KeyError(f"Unknown patch key: {pkey}")
                    rc = restore_ui_patch(state.fm_dir, patch)
                    self._send_json({"ok": rc == 0, "rc": rc, "patches": get_all_patches_status(state.fm_dir)})
                    return

                if path == "/api/patches/streamed-table-toggle":
                    bname = str(body["bundle"])
                    off = int(body["offset"])
                    ds = int(body["disable_sorting"])
                    res = set_streamed_table_sorting(state.fm_dir, bname, off, ds)
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
    """Launch the FM27/FM26 All-in-One Studio Web Application."""
    sp = Path(save_path) if save_path else None
    fd = Path(fm_dir) if fm_dir else None
    state = StudioState(save_path=sp, fm_dir=fd)
    handler_cls = build_studio_handler(state)
    server = HTTPServer((host, port), handler_cls)
    url = f"http://{host}:{port}/"
    print(f"FM Studio Komuta Merkezi başlatıldı: {url}")
    if state.save_path:
        print(f"  Aktif Save Dosyası : {state.save_path}")
    print(f"  Aktif Oyun Dizini  : {state.fm_dir}")
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nFM Studio kapatılıyor...")
    finally:
        server.server_close()
