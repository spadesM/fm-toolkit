"""FM26 Game Installation File Reverse-Engineering Extractors (All 12 Systems).

Extracts and decodes official Football Manager 26 installation archives (.fmf, .dat, .jsb, .dbc, .lnc, .edt, .usym):
1. Quick Match Engine (QME) Statistical Distributions (`simatch.fmf` Frames #119, #120 — 3,137 Poisson/Normal/Binned/Zero distributions & 22 stat-relevant attribute sets) & Player Match Ratings (`Frame #118` — 6 versions, start_value = 6.70)
2. Match Momentum Spatial Engine (`simatch.fmf` Frame #113 — 48 event × zone momentum rules)
3. Out-Of-Possession (OP*) Attribute Scoring (`Frame #114` — 39 RolePosition bitmasks) & 2D Pitch Proximity Tactical Grid (`Frame #115` — 118 Role entries × 24 spatial zones)
4. 11 Shot-Type xG Logistic Regression Models (`simatch.fmf` Frames #002..#100 across 9 folder versions `23_1_1_9`..`26_1_4_1`), Frame #116 Ball Physics Table (`simatch/physics/ball/ball_physics_22_0_5_0.bta`, 3,277,236 B), 101 Tactical Presets (`Frames #121..#222`: 90 `.tac` `\x03\x01cat.` dual-formation templates + 11 `.stra` `\x03\x01rts.` style vectors), & AI Team Selection Weights (`Frame #223` — 4 profiles × 40 `TSF_*` factors)
5. 105 Internal Database XML Schemas & Master FourCC Enums (`shared/data/editor.fmf` — 444 enum groups + entity schemas)
6. Pre-Game Master Databases (`client_db.dat` 31 tables + 1 directory, `lang_update_db.dat` 400 tables = 25 languages × 16 tables + 1 directory, `server_db.dat` 77 tables + 1 directory — 58,349 Cities, 96,343 Clubs, 51,118 Stadiums, 7,973 Competitions, 3,884 Awards, 2,527 Local Regions, 1,683 Derbies, 251 Nations, 180 Media Sources, 136 Injuries, 6 Agreements, 7 Continents, 988,091 Person Name Pool records) & `.edt` Permanent Rule Files
7. Press Conference, Backroom Advice, Training Schedules, Palettes & Newgen Demographics (`media.fmf` 650 XMLs, `training.fmf` 300 schedules, `simatchshared.fmf` 74 RGB palette/crowd frames + 135 newgen appearance rules)
8. IL2CPP Metadata & Native Symbol Table (`il2cpp.usym` 1,593,548 symbols & `global-metadata.dat` C# engine symbols)
9. Pre-Game Master People & Career History Databases (`basic_people_db.dat` 723,010 people walked 100%, `people_db.dat` attributes/personalities, `pl_hist_index/id/dt.dat` 4,344,855 × 44B singly-linked list career rows)
10. Compiled `.dbc` Competition Rule Archives (`sicomps/comps.dbc` 1,442 `03 01 cbd.` rule sets + `2620/dbc/*.dbc`) & `.lnc` Licensing / Name Overrides (`2620/lnc/all/*.lnc`)
11. Auxiliary Simulation `.fmf` Archives (`filters.fmf` 2 XML files / 445 filter records, `achievements.fmf` 1 XML file / 50 achievement records, `leaderboards.fmf` 1 XML file / 28 leaderboard records, `settings.fmf` 9 XML files, `store.fmf` 2 XML files, `profanity_filter.fmf` 2 files, `languages.fmf`)
12. Multi-Version Pre-Game Database Evolution (`shared/data/database/db/2300..2620` — all 9 historical & active FM23/FM24/FM26 databases walked 100% across `5,545,819` person records, table counts, wonderkid & star CA/PA trajectories)
"""

from __future__ import annotations

import os
import re
import struct
from collections import Counter
from pathlib import Path
from typing import Any

import zstandard

from fm26save.formulas import (
    DEFAULT_FM26_INSTALL_DIR,
    extract_fmf_frames,
    parse_jsb,
    read_fmf_directory,
)

_CACHED_OFFICIAL_CITY_MAP: dict[int, str] | None = None
_CACHED_MASTER_DB_SUMMARY: dict[str, Any] | None = None


def _resolve_fm26_dir(fm_install_dir: str | os.PathLike[str] | None = None) -> Path:
    return Path(fm_install_dir) if fm_install_dir else DEFAULT_FM26_INSTALL_DIR


def _extract_fmf_directory_strings(dir_raw: bytes) -> list[str]:
    return [s.decode("ascii", errors="ignore") for s in re.findall(rb"[a-zA-Z0-9_\-\. ]{3,64}", dir_raw)]


def _as_jsb_array(obj: Any) -> list[Any]:
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        if "data_array" in obj and isinstance(obj["data_array"], list):
            return list(obj["data_array"])
        for v in obj.values():
            if isinstance(v, list):
                return list(v)
    return []


# ==============================================================================
# 1. QUICK MATCH ENGINE (QME) STATISTICAL DISTRIBUTIONS (simatch.fmf #119, #120)
#    & PLAYER MATCH RATINGS (simatch.fmf #118)
# ==============================================================================
def extract_qme_distributions(
    fm_install_dir: str | os.PathLike[str] | None = None,
    *,
    sample_limit: int | None = None,
) -> dict[str, Any]:
    """Decode `qme_distribution_data.jsb` (Frame #119, 3,137 Normal/Binned distributions),
    `qme_stat_relevant_attribute_data.jsb` (Frame #120, 22 stat -> relevant_attributes mappings),
    and `player_ratings_data.jsb` (Frame #118, 6 versions, start_value = 6.70) from `simatch.fmf`."""
    root = _resolve_fm26_dir(fm_install_dir)
    sim_fmf = root / "shared/data/simatch.fmf"
    if not sim_fmf.exists():
        return {"available": False, "path": str(sim_fmf)}

    frames = extract_fmf_frames(sim_fmf)
    ratings_obj, _ = parse_jsb(frames[118][1], 0)
    dist_obj, _ = parse_jsb(frames[119][1], 0)
    rel_attr_obj, _ = parse_jsb(frames[120][1], 0)

    raw_rel_attrs = _as_jsb_array(rel_attr_obj)
    raw_dists = _as_jsb_array(dist_obj)
    ratings_versions = ratings_obj.get("values", []) if isinstance(ratings_obj, dict) else _as_jsb_array(ratings_obj)

    stat_type_counts: Counter[str] = Counter()
    position_counts: Counter[str] = Counter()
    dist_type_counts: Counter[str] = Counter()
    parsed_dists: list[dict[str, Any]] = []

    for row in raw_dists:
        st = str(row.get("stat_type", ""))
        pos = str(row.get("position", ""))
        dtype = str(row.get("distribution_type", ""))
        stat_type_counts[st] += 1
        position_counts[pos] += 1
        dist_type_counts[dtype] += 1

        if sample_limit is None or len(parsed_dists) < sample_limit:
            parsed_dists.append(
                {
                    "distribution_type": dtype,
                    "stat_type": st,
                    "position": pos,
                    "ability_window": row.get("ability_window"),
                    "attribute_window": row.get("attribute_window"),
                    "mean": round(float(row.get("mean", 0)) / 1e8, 6),
                    "variance": round(float(row.get("variance", 0)) / 1e8, 6),
                    "bins": [round(float(b) / 1e8, 6) for b in (row.get("bins") or [])],
                }
            )

    return {
        "available": True,
        "source": "shared/data/simatch.fmf (Frames #118, #119, #120)",
        "stat_relevant_attributes_count": len(raw_rel_attrs),
        "stat_relevant_attributes": raw_rel_attrs,
        "attribute_combination_weights_count": len(raw_rel_attrs),
        "attribute_combination_weights": raw_rel_attrs,
        "player_ratings_versions_count": len(ratings_versions),
        "player_ratings_latest_start_value": (
            ratings_versions[-1].get("start_value", 6700) / 1000.0 if ratings_versions else 6.70
        ),
        "distributions_total_count": len(raw_dists),
        "distribution_types": dict(dist_type_counts),
        "stat_types_histogram": {str(k): v for k, v in sorted(stat_type_counts.items())},
        "positions_histogram": {str(k): v for k, v in sorted(position_counts.items())},
        "distributions": parsed_dists,
    }


# ==============================================================================
# 2. MATCH MOMENTUM SPATIAL ENGINE (simatch.fmf #113)
# ==============================================================================
def extract_momentum_weightings(
    fm_install_dir: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Decode `momentum_weightings_data.jsb` (Frame #113, 48 spatial momentum rules) from `simatch.fmf`."""
    root = _resolve_fm26_dir(fm_install_dir)
    sim_fmf = root / "shared/data/simatch.fmf"
    if not sim_fmf.exists():
        return {"available": False, "path": str(sim_fmf)}

    frames = extract_fmf_frames(sim_fmf)
    mom_obj, _ = parse_jsb(frames[113][1], 0)
    arr = _as_jsb_array(mom_obj)

    by_event: dict[str, list[dict[str, Any]]] = {}
    for item in arr:
        ev = str(item.get("CBE_EVENT_TYPE", "UNKNOWN"))
        by_event.setdefault(ev, []).append(
            {
                "event_type": ev,
                "horizontal_third": item.get("HORIZONTAL_THIRDS"),
                "vertical_zone": item.get("VERTICAL_ZONES"),
                "momentum_delta": item.get("MOMENTUM"),
            }
        )

    return {
        "available": True,
        "source": "shared/data/simatch.fmf (Frame #113 — momentum_weightings_data.jsb)",
        "total_spatial_rules": len(arr),
        "event_types": list(by_event.keys()),
        "rules_by_event": by_event,
        "raw_rules": arr,
    }


# ==============================================================================
# 3. OUT-OF-POSSESSION (OP*) ATTRIBUTE SCORING (#114) & 2D PITCH PROXIMITY GRID (#115)
# ==============================================================================
def extract_oop_pitch_proximity_grid(
    fm_install_dir: str | os.PathLike[str] | None = None,
    *,
    role_filter: int | None = None,
) -> dict[str, Any]:
    """Decode `oop_attributes_scoring.jsb` (Frame #114, 39 RolePosition bitmasks) and
    `oop_pitch_proximity_scores.jsb` (Frame #115, 95,708 B, 118 Position+Role entries × 24 spatial zones)."""
    root = _resolve_fm26_dir(fm_install_dir)
    sim_fmf = root / "shared/data/simatch.fmf"
    if not sim_fmf.exists():
        return {"available": False, "path": str(sim_fmf)}

    frames = extract_fmf_frames(sim_fmf)
    attr_obj, _ = parse_jsb(frames[114][1], 0)
    attr_scoring_list = attr_obj.get("SCORING", []) if isinstance(attr_obj, dict) else _as_jsb_array(attr_obj)
    attr_scores = (
        attr_scoring_list[0].get("SCORES", [])
        if (attr_scoring_list and isinstance(attr_scoring_list[0], dict) and "SCORES" in attr_scoring_list[0])
        else attr_scoring_list
    )

    prox_obj, _ = parse_jsb(frames[115][1], 0)
    scoring_list = prox_obj.get("SCORING", []) if isinstance(prox_obj, dict) else _as_jsb_array(prox_obj)
    arr = scoring_list[0].get("SCORES", []) if (scoring_list and isinstance(scoring_list[0], dict) and "SCORES" in scoring_list[0]) else scoring_list

    entries: list[dict[str, Any]] = []
    unique_positions: set[int] = set()
    unique_roles: set[int] = set()
    total_couples = 0

    for row in arr:
        pos = int(row.get("Position", row.get("POSITION", -1)))
        role = int(row.get("Role", row.get("ROLE", -1)))
        couples = row.get("COUPLES") or row.get("Couples") or []
        unique_positions.add(pos)
        unique_roles.add(role)
        total_couples += len(couples)
        if role_filter is not None and role != role_filter:
            continue
        entries.append(
            {
                "position_code": pos,
                "role_code": role,
                "zones_count": len(couples),
                "zones": [
                    {
                        "target_position": c.get("Position"),
                        "side": c.get("Side"),
                        "min_score": c.get("Min"),
                        "max_score": c.get("Max"),
                    }
                    for c in couples
                ],
            }
        )

    return {
        "available": True,
        "source": "shared/data/simatch.fmf (Frame #114 oop_attributes_scoring.jsb & Frame #115 oop_pitch_proximity_scores.jsb)",
        "oop_role_attribute_scoring_count": len(attr_scores),
        "oop_role_attribute_scoring": attr_scores,
        "total_position_role_entries": len(arr),
        "total_spatial_zone_couples": total_couples,
        "unique_position_codes": sorted(unique_positions),
        "unique_role_codes": sorted(unique_roles),
        "entries": entries,
    }


# ==============================================================================
# 4. ALL 11 SHOT-TYPE xG MODELS (#002..#100, 9 VERSIONS), BALL PHYSICS (#116) & 101 TACTICAL PRESETS (#121..#222)
# ==============================================================================
def extract_xg_shot_models(
    fm_install_dir: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Extract all 11 Shot-Type xG Logistic Regression models from `simatch.fmf` (Frames #002..#100 across 9 folder versions `23_1_1_9`..`26_1_4_1`; active v26.1.4.1 in Frames #090..#100)."""
    root = _resolve_fm26_dir(fm_install_dir)
    sim_fmf = root / "shared/data/simatch.fmf"
    if not sim_fmf.exists():
        return {"available": False, "path": str(sim_fmf)}

    frames = extract_fmf_frames(sim_fmf)
    dir_entries = read_fmf_directory(sim_fmf)
    folder_versions: list[str] = []
    all_versions: list[str] = []
    for e in dir_entries:
        nm = str(e.get("name", ""))
        if nm.startswith("simatch/expected_goals/models/") and nm.endswith(".jsb"):
            parts = nm.split("/")
            if len(parts) >= 5:
                vfolder = parts[3]
                if vfolder and vfolder[0].isdigit() and vfolder not in folder_versions:
                    folder_versions.append(vfolder)
                    all_versions.append(vfolder.replace("_", "."))

    if not all_versions:
        for base_fidx in range(2, 101, 11):
            if base_fidx < len(frames):
                v_obj, _ = parse_jsb(frames[base_fidx][1], 0)
                vn = v_obj.get("version_number", "")
                if isinstance(vn, dict):
                    ver_str = f"{vn.get('version_year', 0)}.{vn.get('version_major', 0)}.{vn.get('version_minor', 0)}.{vn.get('version_release', 0)}"
                else:
                    ver_str = str(vn)
                if ver_str and ver_str not in all_versions:
                    all_versions.append(ver_str)

    models: dict[str, Any] = {}
    for fidx in range(90, 101):
        obj, _ = parse_jsb(frames[fidx][1], 0)
        shot_type = str(obj.get("shot_type", f"frame_{fidx}"))
        raw_int = int(obj.get("intercept", 0))
        coeffs = obj.get("coefficients", {})
        coeffs_1e7 = (
            {k: round(float(v) / 1e7, 8) for k, v in coeffs.items()} if isinstance(coeffs, dict) else coeffs
        )
        coeffs_1e8 = (
            {k: round(float(v) / 1e8, 8) for k, v in coeffs.items()} if isinstance(coeffs, dict) else coeffs
        )
        models[shot_type] = {
            "frame_index": fidx,
            "archive_path": dir_entries[fidx]["name"] if fidx < len(dir_entries) else f"frame_{fidx}",
            "shot_type": shot_type,
            "version": obj.get("version_number", "26.1.4.1"),
            "raw_intercept": raw_int,
            "intercept_1e7": round(float(raw_int) / 1e7, 8),
            "intercept_1e8": round(float(raw_int) / 1e8, 8),
            "intercept": round(float(raw_int) / 1e7, 8),
            "raw_coefficients": coeffs,
            "coefficients_1e7": coeffs_1e7,
            "coefficients_1e8": coeffs_1e8,
            "coefficients": coeffs_1e7,
            "formula": "P(Goal) = 1 / (1 + exp(-(intercept + sum(coeff_i * x_i))))",
        }

    return {
        "available": True,
        "source": "shared/data/simatch.fmf (Frames #002..#100 across 9 versions; active v26.1.4.1 at Frames #090..#100)",
        "versions_available_count": len(all_versions),
        "versions_available": all_versions,
        "version_folders": folder_versions,
        "models_count": len(models),
        "models": models,
    }


def extract_tactical_styles_and_presets(
    fm_install_dir: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Decode `simatch.fmf` Frame #116 (`ball_physics_22_0_5_0.bta`), Frame #192 (`tactical_styles.xml`),
    and the 101 Tactical Presets (`Frames #121..#222`: 90 `.tac` `\x03\x01cat.` dual-formation templates + 11 `.stra` `\x03\x01rts.` style vectors)."""
    root = _resolve_fm26_dir(fm_install_dir)
    sim_fmf = root / "shared/data/simatch.fmf"
    if not sim_fmf.exists():
        return {"available": False, "path": str(sim_fmf)}

    frames = extract_fmf_frames(sim_fmf)
    dir_entries = read_fmf_directory(sim_fmf)
    preset_filenames = (
        [e["name"] for e in dir_entries]
        if dir_entries
        else [s for s in _extract_fmf_directory_strings(frames[-1][1]) if s.endswith((".tac", ".stra", ".bta", ".xml", ".jsb"))]
    )

    # Frame #192 is Tactical Styles XML (simatch/tactics/tactical_styles.xml)
    styles_xml = frames[192][1].decode("utf-8", errors="replace")
    style_blocks: list[dict[str, Any]] = []
    for m in re.finditer(
        r'<record id="(\d+)"\s+folder="([^"]+)"\s+tactical_style_id="([^"]+)">(.*?)(?=<record id="\d+"\s+folder=|\Z)',
        styles_xml,
        re.DOTALL,
    ):
        style_idx = int(m.group(1))
        folder = m.group(2).strip()
        style_id = m.group(3).strip()
        body = m.group(4)
        text_m = re.search(r'<translation id="text"[^>]*value="([^"\[]+)', body)
        hint_m = re.search(r'<translation id="hint"[^>]*value="([^"\[]+)', body)
        attrs = re.findall(r'<record id="([a-z_]+)"\s+weight="([^"]+)"', body)
        if not attrs:
            attrs = [(a, "1") for a in re.findall(r'id="attribute"\s+value="([a-z_]+)"', body)]
        style_blocks.append(
            {
                "style_index": style_idx,
                "folder": folder,
                "tactical_style_id": style_id,
                "display_name": text_m.group(1).strip() if text_m else style_id,
                "tactical_hint": hint_m.group(1).strip() if hint_m else "",
                "template_attributes": [{"attribute": k, "weight": w} for k, w in attrs],
            }
        )

    # Frame #116 is simatch/physics/ball/ball_physics_22_0_5_0.bta (3,277,236 B binary ball physics lookup table)
    ball_physics_table_116: dict[str, Any] = {}
    if len(frames) > 116:
        r116 = frames[116][1]
        ball_physics_table_116 = {
            "frame_index": 116,
            "archive_path": dir_entries[116]["name"] if len(dir_entries) > 116 else "simatch/physics/ball/ball_physics_22_0_5_0.bta",
            "description": "Ball Physics 22.0.5.0 trajectory/bounce lookup table (.bta)",
            "size_bytes": len(r116),
            "header_hex": r116[:40].hex(" "),
            "header_u32s": list(struct.unpack_from("<10I", r116, 0)) if len(r116) >= 40 else [],
        }

    # Decode binary tactical preset frames (#121..#222 excluding #192):
    # - 90 '.tac' (inner magic \x03\x01cat.) dual-formation IP x OOP combination templates
    # - 11 '.stra' (inner magic \x03\x01rts.) tactical style team-instruction vectors
    tactical_frames_summary: list[dict[str, Any]] = []
    cat_presets: list[dict[str, Any]] = []
    rts_style_vectors: list[dict[str, Any]] = []
    for fidx in range(121, min(223, len(frames) - 1)):
        if fidx == 192:
            continue
        raw = frames[fidx][1]
        magic = raw[:8].hex(" ")
        ascii_strings = [
            s.decode("utf-8", errors="ignore")
            for s in re.findall(rb"[a-zA-Z0-9_\- ]{4,48}", raw[:512])
        ]
        archive_path = dir_entries[fidx]["name"] if fidx < len(dir_entries) else f"frame_{fidx}"
        entry: dict[str, Any] = {
            "frame_index": fidx,
            "archive_path": archive_path,
            "extension": Path(archive_path).suffix,
            "size_bytes": len(raw),
            "header_hex": magic,
            "header_strings": ascii_strings[:5],
        }
        if raw[:6] == b"\x03\x01cat." and len(raw) >= 24:
            slen = struct.unpack_from("<I", raw, 16)[0]
            if 0 < slen < 120 and 20 + slen <= len(raw):
                preset_name = raw[20 : 20 + slen].decode("utf-8", errors="replace").strip()
                parts = [p.strip() for p in preset_name.split(" - ")]
                entry["format"] = "cat"
                entry["inner_magic"] = "\\x03\\x01cat."
                entry["preset_name"] = preset_name
                entry["in_possession_label"] = parts[0] if parts else preset_name
                entry["out_of_possession_formation"] = parts[1] if len(parts) > 1 else ""
                cat_presets.append(entry)
        elif raw[:6] == b"\x03\x01rts." and len(raw) >= 40:
            tail_str = ascii_strings[-1] if ascii_strings else ""
            fourcc_rev = tail_str[-4:][::-1] if len(tail_str) >= 4 else ""
            style_label = tail_str[:-4] if len(tail_str) > 4 else tail_str
            entry["format"] = "rts"
            entry["inner_magic"] = "\\x03\\x01rts."
            entry["style_label"] = style_label
            entry["style_fourcc"] = fourcc_rev
            entry["instruction_vector_bytes"] = list(raw[14:38])
            rts_style_vectors.append(entry)
        tactical_frames_summary.append(entry)

    return {
        "available": True,
        "source": "shared/data/simatch.fmf (Frame #116 ball_physics_22_0_5_0.bta + Frames #121..#222 .tac/.stra presets)",
        "ball_physics_table_116": ball_physics_table_116,
        "pitch_positioning_table_116": ball_physics_table_116,
        "tactical_styles_xml_count": len(style_blocks),
        "tactical_styles": style_blocks,
        "binary_tactical_presets_count": len(tactical_frames_summary),
        "cat_formation_combinations_count": len(cat_presets),
        "cat_formation_combinations": cat_presets,
        "rts_style_instruction_vectors_count": len(rts_style_vectors),
        "rts_style_instruction_vectors": rts_style_vectors,
        "directory_filenames": preset_filenames,
        "binary_tactical_presets_sample": tactical_frames_summary[:25],
    }


# ==============================================================================
# 5. 106 INTERNAL DATABASE XML SCHEMAS & MASTER FOURCC ENUMS (editor.fmf)
# ==============================================================================
def extract_editor_schemas_and_enums(
    fm_install_dir: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Decode `shared/data/editor.fmf` (106 XML schemas) into structured FourCC field dictionaries and 444 enum groups."""
    root = _resolve_fm26_dir(fm_install_dir)
    ed_fmf = root / "shared/data/editor.fmf"
    if not ed_fmf.exists():
        return {"available": False, "path": str(ed_fmf)}

    frames = extract_fmf_frames(ed_fmf)
    dir_strings = _extract_fmf_directory_strings(frames[-1][1])

    # Parse Frame #082 (db enums.xml)
    enums_xml = frames[82][1].decode("utf-8", errors="replace")
    enum_groups: dict[str, list[dict[str, Any]]] = {}
    for m in re.finditer(
        r'<record id="([^"]+)">\s*<list id="enum_values">(.*?)</list>\s*</record>',
        enums_xml,
        re.DOTALL,
    ):
        enum_id = m.group(1)
        body = m.group(2)
        items: list[dict[str, Any]] = []
        for rec_m in re.finditer(r'<record enum="([^"]+)">(.*?)</record>', body, re.DOTALL):
            enum_val = rec_m.group(1)
            rbody = rec_m.group(2)
            name_m = re.search(r'value="([^"\[]+)', rbody)
            trans_m = re.search(r'translation_id="(\d+)"', rbody)
            items.append(
                {
                    "enum": enum_val,
                    "label": name_m.group(1).strip() if name_m else enum_val,
                    "translation_id": int(trans_m.group(1)) if trans_m else None,
                }
            )
        enum_groups[enum_id] = items

    # Parse key entity schema frames
    key_schema_frames = {
        "club": 32,
        "comp": 33,
        "contract_offer": 35,
        "injury": 39,
        "nation": 45,
        "non_player": 46,
        "official": 47,
        "person": 49,
        "player": 50,
        "stadium": 52,
        "stage": 53,
        "team": 54,
        "weather": 56,
    }
    entity_schemas: dict[str, dict[str, Any]] = {}
    for entity_name, fidx in key_schema_frames.items():
        if fidx >= len(frames) - 1:
            continue
        xml_txt = frames[fidx][1].decode("utf-8", errors="replace")
        tbl_m = re.search(r'<record id="([a-zA-Z0-9_]{4})">\s*<list id="fields">', xml_txt)
        table_fourcc = tbl_m.group(1) if tbl_m else entity_name
        fields: list[dict[str, Any]] = []
        seen_fourcc: set[str] = set()
        for chunk in re.split(r'(?=<flags id="field"\s+value=")', xml_txt):
            f_m = re.search(r'<flags id="field"\s+value="([^"]+)"\s*/>', chunk)
            if not f_m:
                continue
            fourcc = f_m.group(1)
            if fourcc in seen_fourcc:
                continue
            seen_fourcc.add(fourcc)
            local_chunk = chunk[:900]
            type_m = re.search(r'<flags id="type"\s+value="([^"]+)"', local_chunk)
            name_m = re.search(r'<translation id="name"[^>]*value="([^"\[]+)', local_chunk)
            cat_m = re.search(r'<translation id="category"[^>]*value="([^"\[]+)', local_chunk)
            min_m = re.search(r'id="min_value"\s+value="([^"]+)"', local_chunk)
            max_m = re.search(r'id="max_value"\s+value="([^"]+)"', local_chunk)
            fields.append(
                {
                    "fourcc": fourcc,
                    "type": type_m.group(1) if type_m else "record_or_list",
                    "name": name_m.group(1).strip() if name_m else "",
                    "category": cat_m.group(1).strip() if cat_m else None,
                    "min_value": min_m.group(1) if min_m else None,
                    "max_value": max_m.group(1) if max_m else None,
                }
            )
        entity_schemas[entity_name] = {
            "frame_index": fidx,
            "table_fourcc": table_fourcc,
            "fields_count": len(fields),
            "fields": fields,
        }

    # Also catalog all 105 XML frames (#000..#104) in editor.fmf
    all_xml_frames_summary: list[dict[str, Any]] = []
    xml_filenames = [s for s in dir_strings if s.endswith(".xml")]
    for fidx in range(len(frames) - 1):
        xml_txt = frames[fidx][1].decode("utf-8", errors="replace")
        tbl_m = re.search(r'<record id="([a-zA-Z0-9_]{4})">\s*<list id="fields">', xml_txt)
        f_count = len(set(re.findall(r'<flags id="field"\s+value="([^"]+)"\s*/>', xml_txt)))
        all_xml_frames_summary.append(
            {
                "frame_index": fidx,
                "filename": xml_filenames[fidx] if fidx < len(xml_filenames) else f"frame_{fidx}.xml",
                "size_bytes": len(frames[fidx][1]),
                "table_fourcc": tbl_m.group(1) if tbl_m else None,
                "unique_fields_count": f_count,
            }
        )

    return {
        "available": True,
        "source": "shared/data/editor.fmf (106 XML frames)",
        "total_xml_frames": len(frames) - 1,
        "directory_files": xml_filenames,
        "all_xml_frames_summary": all_xml_frames_summary,
        "enum_groups_count": len(enum_groups),
        "enum_groups": enum_groups,
        "entity_schemas": entity_schemas,
    }


# ==============================================================================
# 6. PRE-GAME MASTER DATABASES (client_db.dat, lang_update_db.dat, server_db.dat)
# ==============================================================================
def _parse_lang_continents(raw: bytes, client_continents_raw: bytes | None = None) -> list[dict[str, Any]]:
    cnt = struct.unpack_from("<I", raw, 8)[0]
    pos = 12
    out: list[dict[str, Any]] = []
    for idx in range(cnt):
        uid, l1 = struct.unpack_from("<II", raw, pos)
        pos += 8
        name = raw[pos : pos + l1].decode("utf-8", errors="replace")
        pos += l1 + 1
        l2 = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        code = raw[pos : pos + l2].decode("utf-8", errors="replace")
        pos += l2
        l3 = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        demonym = raw[pos : pos + l3].decode("utf-8", errors="replace")
        pos += l3
        l4 = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        federation_name = raw[pos : pos + l4].decode("utf-8", errors="replace")
        pos += l4 + 1
        l5 = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        federation_short = raw[pos : pos + l5].decode("utf-8", errors="replace")
        pos += l5 + 2
        out.append(
            {
                "continent_id": idx,
                "uid": uid,
                "name": name,
                "code": code,
                "demonym": demonym,
                "federation_name": federation_name,
                "federation_short_name": federation_short,
            }
        )
    return out


def _parse_lang_nations(
    raw: bytes,
    client_nations_raw: bytes | None = None,
    *,
    continent_map: dict[int, str] | None = None,
    city_map: dict[int, str] | None = None,
) -> list[dict[str, Any]]:
    cnt = struct.unpack_from("<I", raw, 8)[0]
    pos = 12
    out: list[dict[str, Any]] = []
    for idx in range(cnt):
        uid, l1 = struct.unpack_from("<II", raw, pos)
        pos += 8
        name = raw[pos : pos + l1].decode("utf-8", errors="replace")
        pos += l1 + 1
        l2 = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        short_name = raw[pos : pos + l2].decode("utf-8", errors="replace")
        pos += l2 + 1
        l3 = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        code = raw[pos : pos + l3].decode("utf-8", errors="replace")
        pos += l3
        l4 = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        nationality = raw[pos : pos + l4].decode("utf-8", errors="replace")
        pos += l4 + 1
        out.append(
            {
                "index": idx,
                "uid": uid,
                "name": name,
                "short_name": short_name,
                "code": code,
                "nationality": nationality,
            }
        )

    if client_nations_raw is not None:
        c_pos = 12
        dev_labels = {1: "Developed", 2: "Developing", 3: "Third World"}
        imp_labels = {1: "Very Important", 2: "Important", 3: "Less Important", 4: "Unimportant"}
        for idx, entry in enumerate(out):
            tail = struct.pack("<III", idx, entry["uid"], entry["uid"])
            tpos = client_nations_raw.find(tail, c_pos)
            if tpos >= c_pos and (tpos + 12 - c_pos) >= 35:
                rec = client_nations_raw[c_pos : tpos + 12]
                cont_id, reg_id, cap_city_id, curr_id = struct.unpack_from("<iiii", rec, 2)
                dev_state, econ_factor = struct.unpack_from("<BB", rec, 18)
                nat_years, game_imp = struct.unpack_from("<BB", rec, 24)
                db_idx, db_uid = struct.unpack_from("<II", rec, len(rec) - 12)
                entry.update(
                    {
                        "continent_id": cont_id,
                        "continent_name": (continent_map or {}).get(cont_id),
                        "region_id": reg_id,
                        "capital_city_id": cap_city_id if cap_city_id >= 0 else None,
                        "capital_city_name": (city_map or {}).get(cap_city_id) if cap_city_id >= 0 else None,
                        "currency_id": curr_id if curr_id >= 0 else None,
                        "state_of_development_code": dev_state,
                        "state_of_development": dev_labels.get(dev_state, f"Code {dev_state}"),
                        "economic_factor_1_20": econ_factor,
                        "years_to_gain_nationality": nat_years,
                        "game_importance_code": game_imp,
                        "game_importance": imp_labels.get(game_imp, f"Code {game_imp}"),
                        "db_nation_id": db_idx,
                        "db_uid": db_uid,
                    }
                )
                c_pos = tpos + 12
    return out


def _parse_lang_competitions(
    raw: bytes,
    client_comps_26_raw: bytes | None = None,
    *,
    continent_map: dict[int, str] | None = None,
    nation_uid_map: dict[int, str] | None = None,
) -> list[dict[str, Any]]:
    cnt = struct.unpack_from("<I", raw, 8)[0]
    pos = 12
    out: list[dict[str, Any]] = []
    c_pos = 12
    for idx in range(cnt):
        uid, l1 = struct.unpack_from("<II", raw, pos)
        pos += 8
        name = raw[pos : pos + l1].decode("utf-8", errors="replace")
        pos += l1 + 1
        l2 = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        short_name = raw[pos : pos + l2].decode("utf-8", errors="replace")
        pos += l2 + 1
        l3 = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        code = raw[pos : pos + l3].decode("utf-8", errors="replace")
        pos += l3 + 1
        entry: dict[str, Any] = {
            "index": idx,
            "uid": uid,
            "name": name,
            "short_name": short_name,
            "code": code,
        }
        if client_comps_26_raw is not None:
            tail = struct.pack("<III", idx, uid, uid)
            tpos = client_comps_26_raw.find(tail, c_pos)
            if tpos >= c_pos and (tpos + 12 - c_pos) >= 120:
                rec = client_comps_26_raw[c_pos : tpos + 12]
                c_pos = tpos + 12
                end = len(rec)
                # table_25.dat has 4 extra bytes near the tail compared to table_for_old_save_25.dat (127 B vs 123 B; rec #0 is 128 B vs 124 B):
                delta = 4 if end >= 127 else 0
                div_level = rec[end - 107 - delta]
                comp_type = rec[end - 104 - delta]
                cont_id, nat_uid = struct.unpack_from("<ii", rec, end - 70 - delta)
                nat_id = struct.unpack_from("<h", rec, end - 58 - delta)[0]
                db_cid, db_uid = struct.unpack_from("<II", rec, end - 12)
                entry.update(
                    {
                        "division_level": div_level,
                        "comp_type_code": comp_type,
                        "continent_id": cont_id if cont_id >= 0 else None,
                        "continent_name": (continent_map or {}).get(cont_id) if cont_id >= 0 else None,
                        "nation_uid": nat_uid if nat_uid > 0 else None,
                        "nation_name": (nation_uid_map or {}).get(nat_uid) if nat_uid > 0 else None,
                        "nation_id": nat_id if nat_id >= 0 else None,
                        "db_comp_id": db_cid,
                        "db_uid": db_uid,
                    }
                )
        out.append(entry)
    return out


def _parse_lang_clubs(
    raw: bytes,
    client_clubs_raw: bytes | None = None,
    *,
    limit: int | None = None,
    nation_map: dict[int, str] | None = None,
    city_map: dict[int, str] | None = None,
) -> list[dict[str, Any]]:
    cnt = struct.unpack_from("<I", raw, 8)[0]
    pos = 12
    out: list[dict[str, Any]] = []
    target = cnt if limit is None else min(cnt, limit)
    c_pos = 12
    for idx in range(target):
        uid, l1 = struct.unpack_from("<II", raw, pos)
        pos += 8
        name = raw[pos : pos + l1].decode("utf-8", errors="replace")
        pos += l1 + 1
        l2 = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        short_name = raw[pos : pos + l2].decode("utf-8", errors="replace")
        pos += l2 + 1
        l3 = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        six_letter = raw[pos : pos + l3].decode("utf-8", errors="replace")
        pos += l3
        l4 = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        three_letter = raw[pos : pos + l4].decode("utf-8", errors="replace")
        pos += l4
        l5 = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        alt_short = raw[pos : pos + l5].decode("utf-8", errors="replace")
        pos += l5 + 1
        l6 = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        nickname = raw[pos : pos + l6].decode("utf-8", errors="replace")
        pos += l6 + 4
        entry: dict[str, Any] = {
            "index": idx,
            "uid": uid,
            "name": name,
            "short_name": short_name,
            "six_letter_name": six_letter,
            "three_letter_name": three_letter,
            "alt_short_name": alt_short,
            "nickname": nickname,
        }
        if client_clubs_raw is not None:
            tail = struct.pack("<III", idx, uid, uid)
            tpos = client_clubs_raw.find(tail, c_pos)
            if tpos >= c_pos and (tpos + 12 - c_pos) >= 32:
                rec = client_clubs_raw[c_pos : tpos + 12]
                off = 1 if rec[0] == 0 and len(rec) > 36 and rec[1] == 0 and rec[5] != 0xFF else 1
                # Handle Club #0 which has an extra leading 0x00 byte at offset 12
                if idx == 0 and rec[0] == 0 and rec[1] == 0:
                    off = 2
                nat_id, based_nat_id, cont_nat_id, reg_nat_id, city_id = struct.unpack_from("<iiiii", rec, off)
                is_female = bool(rec[-13] == 1)
                db_cid, db_uid = struct.unpack_from("<II", rec, len(rec) - 12)
                entry.update(
                    {
                        "nation_id": nat_id if nat_id >= 0 else None,
                        "nation_name": (nation_map or {}).get(nat_id) if nat_id >= 0 else None,
                        "based_nation_id": based_nat_id if based_nat_id >= 0 else nat_id,
                        "city_id": city_id if city_id >= 0 else None,
                        "city_name": (city_map or {}).get(city_id) if city_id >= 0 else None,
                        "is_womens_club": is_female,
                        "db_club_id": db_cid,
                        "db_uid": db_uid,
                    }
                )
                c_pos = tpos + 12
        out.append(entry)
    return out


def _parse_lang_cities_and_coords(
    lang_cities_raw: bytes,
    client_cities_raw: bytes | None = None,
    *,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Decode all 58,349 official FM26 cities combining `8_2.dat` names with `table_2.dat` 43-byte coordinates."""
    cnt = struct.unpack_from("<I", lang_cities_raw, 8)[0]
    pos = 12
    out: list[dict[str, Any]] = []
    target = cnt if limit is None else min(cnt, limit)
    has_coords = client_cities_raw is not None and len(client_cities_raw) >= 12 + cnt * 43

    for idx in range(target):
        uid, l1 = struct.unpack_from("<II", lang_cities_raw, pos)
        pos += 8
        name = lang_cities_raw[pos : pos + l1].decode("utf-8", errors="replace")
        pos += l1 + 2

        entry: dict[str, Any] = {
            "city_id": idx,
            "uid": uid,
            "name": name,
        }
        if has_coords and client_cities_raw is not None:
            coff = 12 + idx * 43
            rec = client_cities_raw[coff : coff + 43]
            lat, lon, attraction, nation_id, region_id, alt_raw, inhab_code = struct.unpack_from(
                "<ffBIIHB", rec, 3
            )
            weather_id = struct.unpack_from("<H", rec, 27)[0]
            cid_db, uid_db = struct.unpack_from("<II", rec, 32)
            entry.update(
                {
                    "latitude": round(lat, 5),
                    "longitude": round(lon, 5),
                    "attraction_1_20": attraction,
                    "nation_id": nation_id,
                    "local_region_id": region_id,
                    "altitude_ft": alt_raw,
                    "altitude_raw": alt_raw,
                    "inhabitants_bracket": inhab_code,
                    "weather_profile_id": weather_id,
                    "db_city_id": cid_db,
                    "db_uid": uid_db,
                }
            )
        out.append(entry)
    return out


def _parse_lang_injuries(
    raw: bytes,
    client_inj_raw: bytes | None = None,
    server_inj_raw: bytes | None = None,
) -> list[dict[str, Any]]:
    cnt = struct.unpack_from("<I", raw, 8)[0]
    pos = 12
    out: list[dict[str, Any]] = []
    has_server = server_inj_raw is not None and len(server_inj_raw) >= 13 + cnt * 48
    for idx in range(cnt):
        uid, l1 = struct.unpack_from("<II", raw, pos)
        pos += 8
        name = raw[pos : pos + l1].decode("utf-8", errors="replace")
        pos += l1 + 1
        l2 = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        sentence = raw[pos : pos + l2].decode("utf-8", errors="replace")
        pos += l2 + 2
        entry: dict[str, Any] = {
            "index": idx,
            "uid": uid,
            "name": name,
            "sentence_name": sentence,
        }
        if has_server and server_inj_raw is not None:
            soff = 13 + idx * 48
            srec = server_inj_raw[soff : soff + 48]
            cat_code, body_part, is_phys = struct.unpack_from("<BBB", srec, 1)
            min_d, extra_d, inact_min, inact_extra, fit_drop = struct.unpack_from("<HHHHH", srec, 4)
            treat_code, is_rec, can_play_with_inj = struct.unpack_from("<BBB", srec, 14)
            occ_ratio, base_occ = struct.unpack_from("<ff", srec, 18)
            sev_tier = srec[30]
            is_contag = srec[31]
            cause_code = srec[32]
            db_iid, db_uid = struct.unpack_from("<II", srec, 36)
            entry.update(
                {
                    "category_code": cat_code,
                    "body_part_code": body_part,
                    "is_physical_injury": bool(is_phys),
                    "min_days": min_d,
                    "extra_days": extra_d,
                    "max_days_estimate": min_d + extra_d,
                    "inactive_min_days": inact_min,
                    "inactive_extra_days": inact_extra,
                    "match_fitness_drop_pct": fit_drop,
                    "treatment_code": treat_code,
                    "is_recurring": bool(is_rec),
                    "can_play_with_protective_or_injections": bool(can_play_with_inj),
                    "is_contagious_or_special": bool(is_contag),
                    "occurrence_ratio": round(occ_ratio, 6),
                    "base_occurrence_weight": round(base_occ, 6),
                    "severity_tier": sev_tier,
                    "cause_code": cause_code,
                    "db_injury_id": db_iid,
                    "db_uid": db_uid,
                }
            )
        out.append(entry)
    return out


def _parse_lang_awards(
    raw: bytes,
    client_awards_raw: bytes | None = None,
    *,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    cnt = struct.unpack_from("<I", raw, 8)[0]
    pos = 12
    out: list[dict[str, Any]] = []
    target = cnt if limit is None else min(cnt, limit)
    has_client = client_awards_raw is not None and len(client_awards_raw) >= 12 + cnt * 77
    for idx in range(target):
        uid, l1 = struct.unpack_from("<II", raw, pos)
        pos += 8
        name = raw[pos : pos + l1].decode("utf-8", errors="replace")
        pos += l1 + 1
        l2 = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        short_name = raw[pos : pos + l2].decode("utf-8", errors="replace")
        pos += l2 + 2
        entry: dict[str, Any] = {"index": idx, "uid": uid, "name": name, "short_name": short_name}
        if has_client and client_awards_raw is not None:
            coff = 12 + idx * 77
            crec = client_awards_raw[coff : coff + 77]
            db_aid, db_uid = struct.unpack_from("<II", crec, 66)
            entry["db_award_id"] = db_aid
            entry["db_uid"] = db_uid
        out.append(entry)
    return out


def _parse_lang_stadiums(
    raw: bytes,
    client_stad_raw: bytes | None = None,
    server_stad_raw: bytes | None = None,
    *,
    limit: int | None = None,
    city_map: dict[int, str] | None = None,
) -> list[dict[str, Any]]:
    cnt = struct.unpack_from("<I", raw, 8)[0]
    pos = 12
    out: list[dict[str, Any]] = []
    target = cnt if limit is None else min(cnt, limit)
    has_client = client_stad_raw is not None and len(client_stad_raw) >= 12 + cnt * 38
    has_server = server_stad_raw is not None and len(server_stad_raw) >= 12 + cnt * 181
    for idx in range(target):
        uid, l1 = struct.unpack_from("<II", raw, pos)
        pos += 8
        name = raw[pos : pos + l1].decode("utf-8", errors="replace")
        pos += l1
        l2 = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        alt_name = raw[pos : pos + l2].decode("utf-8", errors="replace")
        pos += l2 + 3
        entry: dict[str, Any] = {"index": idx, "uid": uid, "name": name, "alt_name": alt_name}
        if has_client and client_stad_raw is not None:
            coff = 12 + idx * 38
            crec = client_stad_raw[coff : coff + 38]
            city_id, owner_club_id = struct.unpack_from("<ii", crec, 5)
            lat, lon = struct.unpack_from("<ff", crec, 19)
            db_sid, db_uid = struct.unpack_from("<II", crec, 27)
            entry.update(
                {
                    "city_id": city_id if city_id >= 0 else None,
                    "city_name": (city_map or {}).get(city_id) if city_id >= 0 else None,
                    "owner_club_id": owner_club_id if owner_club_id >= 0 else None,
                    "latitude": round(lat, 5),
                    "longitude": round(lon, 5),
                    "db_stadium_id": db_sid,
                    "db_uid": db_uid,
                }
            )
        if has_server and server_stad_raw is not None:
            soff = 12 + idx * 181
            srec = server_stad_raw[soff : soff + 181]
            cap, seat_cap, exp_cap, used_cap = struct.unpack_from("<IIII", srec, 2)
            all_seat_cap = struct.unpack_from("<I", srec, 23)[0]
            pitch_l_dm, pitch_w_dm = struct.unpack_from("<HH", srec, 27)
            build_yr = struct.unpack_from("<H", srec, 49)[0]
            min_l_dm, min_w_dm, max_l_dm, max_w_dm = struct.unpack_from("<HHHH", srec, 56)
            entry.update(
                {
                    "capacity": cap,
                    "seating_capacity": seat_cap,
                    "expansion_capacity": exp_cap,
                    "used_capacity": used_cap,
                    "all_seater_capacity": all_seat_cap,
                    "pitch_length_m": round(pitch_l_dm / 10.0, 1),
                    "pitch_width_m": round(pitch_w_dm / 10.0, 1),
                    "build_year": build_yr if 1800 <= build_yr <= 2035 else None,
                    "min_pitch_length_m": round(min_l_dm / 10.0, 1),
                    "min_pitch_width_m": round(min_w_dm / 10.0, 1),
                    "max_pitch_length_m": round(max_l_dm / 10.0, 1),
                    "max_pitch_width_m": round(max_w_dm / 10.0, 1),
                }
            )
        out.append(entry)
    return out


def _parse_person_name_pool_table(raw: bytes, *, limit: int | None = 50) -> dict[str, Any]:
    """Decode `client_db.dat` person name pool tables (`#17` First Names, `#18` Last Names, `#19` Common Names)."""
    cnt = struct.unpack_from("<I", raw, 8)[0]
    pos = 12
    sample: list[dict[str, Any]] = []
    target = cnt if limit is None else min(cnt, limit)
    for idx in range(target):
        nid, slen = struct.unpack_from("<II", raw, pos)
        pos += 8
        name = raw[pos : pos + slen].decode("utf-8", errors="replace")
        pos += slen
        sample.append({"name_id": nid, "name": name})
    return {
        "total_count": cnt,
        "decompressed_bytes": len(raw),
        "sample": sample,
    }


def _parse_lang_stage_names(raw: bytes) -> list[dict[str, Any]]:
    cnt = struct.unpack_from("<I", raw, 8)[0]
    pos = 12
    out: list[dict[str, Any]] = []
    for idx in range(cnt):
        uid, l1 = struct.unpack_from("<II", raw, pos)
        pos += 8
        name = raw[pos : pos + l1].decode("utf-8", errors="replace")
        pos += l1 + 1
        l2 = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        short_name = raw[pos : pos + l2].decode("utf-8", errors="replace")
        pos += l2 + 1
        l3 = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        plural_name = raw[pos : pos + l3].decode("utf-8", errors="replace")
        pos += l3 + 2
        out.append(
            {"index": idx, "uid": uid, "name": name, "short_name": short_name, "plural_name": plural_name}
        )
    return out


def _parse_lang_media_sources(raw: bytes) -> list[dict[str, Any]]:
    cnt = struct.unpack_from("<I", raw, 8)[0]
    pos = 12
    out: list[dict[str, Any]] = []
    for idx in range(cnt):
        uid, l1 = struct.unpack_from("<II", raw, pos)
        pos += 8
        name = raw[pos : pos + l1].decode("utf-8", errors="replace")
        pos += l1 + 1
        out.append({"index": idx, "uid": uid, "name": name})
    return out


def _parse_lang_local_regions(raw: bytes) -> list[dict[str, Any]]:
    cnt = struct.unpack_from("<I", raw, 8)[0]
    pos = 12
    out: list[dict[str, Any]] = []
    for idx in range(cnt):
        uid, l1 = struct.unpack_from("<II", raw, pos)
        pos += 8
        name = raw[pos : pos + l1].decode("utf-8", errors="replace")
        pos += l1 + 1
        l2 = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        demonym = raw[pos : pos + l2].decode("utf-8", errors="replace")
        pos += l2 + 2
        out.append({"index": idx, "uid": uid, "name": name, "demonym": demonym})
    return out


def _parse_lang_derbies(raw: bytes, *, limit: int | None = None) -> list[dict[str, Any]]:
    cnt = struct.unpack_from("<I", raw, 8)[0]
    pos = 12
    out: list[dict[str, Any]] = []
    target = cnt if limit is None else min(cnt, limit)
    for idx in range(target):
        if pos + 8 > len(raw):
            break
        uid, l1 = struct.unpack_from("<II", raw, pos)
        pos += 8
        if l1 > 500 or pos + l1 + 4 > len(raw):
            break
        name = raw[pos : pos + l1].decode("utf-8", errors="replace")
        pos += l1
        l2 = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        if l2 > 500 or pos + l2 + 4 > len(raw):
            break
        short_name = raw[pos : pos + l2].decode("utf-8", errors="replace")
        pos += l2
        l3 = struct.unpack_from("<I", raw, pos)[0]
        pos += 4 + l3
        l4 = struct.unpack_from("<I", raw, pos)[0]
        pos += 4 + l4 + 5
        out.append({"index": idx, "uid": uid, "name": name, "short_name": short_name})
    return out


def _parse_lang_agreements(raw: bytes) -> list[dict[str, Any]]:
    cnt = struct.unpack_from("<I", raw, 8)[0]
    pos = 12
    out: list[dict[str, Any]] = []
    for idx in range(cnt):
        uid, l1 = struct.unpack_from("<II", raw, pos)
        pos += 8
        name = raw[pos : pos + l1].decode("utf-8", errors="replace")
        pos += l1 + 1
        l2 = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        abbr = raw[pos : pos + l2].decode("utf-8", errors="replace")
        pos += l2 + 2
        out.append({"index": idx, "uid": uid, "name": name, "abbreviation": abbr})
    return out


def load_official_city_map(
    fm_install_dir: str | os.PathLike[str] | None = None,
) -> dict[int, str]:
    """Load all 58,349 official 0-based `city_id -> city_name` mappings from `lang_update_db.dat` Frame #03 (`8_2.dat`)."""
    global _CACHED_OFFICIAL_CITY_MAP
    if _CACHED_OFFICIAL_CITY_MAP is not None and fm_install_dir is None:
        return _CACHED_OFFICIAL_CITY_MAP

    root = _resolve_fm26_dir(fm_install_dir)
    lang_db = root / "shared/data/database/db/2620/2620_fm/lang_update_db.dat"
    if not lang_db.exists():
        return {}

    frames = extract_fmf_frames(lang_db)
    raw = frames[3][1]
    cnt = struct.unpack_from("<I", raw, 8)[0]
    pos = 12
    city_map: dict[int, str] = {}
    for idx in range(cnt):
        _uid, l1 = struct.unpack_from("<II", raw, pos)
        pos += 8
        name = raw[pos : pos + l1].decode("utf-8", errors="replace")
        pos += l1 + 2
        city_map[idx] = name

    if fm_install_dir is None:
        _CACHED_OFFICIAL_CITY_MAP = city_map
    return city_map


def extract_master_db_tables(
    fm_install_dir: str | os.PathLike[str] | None = None,
    *,
    sample_limit: int | None = 50,
) -> dict[str, Any]:
    """Extract and decode FM26 Pre-Game Master Databases (`client_db.dat`, `lang_update_db.dat`, `server_db.dat`)."""
    root = _resolve_fm26_dir(fm_install_dir)
    db_dir = root / "shared/data/database/db/2620/2620_fm"
    client_path = db_dir / "client_db.dat"
    lang_path = db_dir / "lang_update_db.dat"
    server_path = db_dir / "server_db.dat"
    if not client_path.exists() or not lang_path.exists():
        return {"available": False, "path": str(db_dir)}

    c_frames = extract_fmf_frames(client_path)
    l_frames = extract_fmf_frames(lang_path)
    s_frames = extract_fmf_frames(server_path) if server_path.exists() else []

    c_dir_entries = read_fmf_directory(client_path)
    client_tables_summary: list[dict[str, Any]] = []
    for idx in range(len(c_frames) - 1):
        raw = c_frames[idx][1]
        tname = c_dir_entries[idx]["filename"] if idx < len(c_dir_entries) else f"frame_{idx}"
        is_tad = len(raw) >= 12 and raw[:6] == b"\x03\x01tad." and tname != "simple_vars.dat"
        cnt = struct.unpack_from("<I", raw, 8)[0] if is_tad else 1
        body_len = max(0, len(raw) - 12) if is_tad else len(raw)
        rec_size = round(body_len / cnt, 2) if cnt > 0 else 0
        client_tables_summary.append(
            {
                "frame_index": idx,
                "table_name": tname,
                "archive_path": c_dir_entries[idx]["name"] if idx < len(c_dir_entries) else tname,
                "record_count": cnt,
                "decompressed_bytes": len(raw),
                "bytes_per_record": rec_size,
            }
        )

    s_dir_entries = read_fmf_directory(server_path) if server_path.exists() else []
    server_tables_summary: list[dict[str, Any]] = []
    for idx in range(max(0, len(s_frames) - 1)):
        raw = s_frames[idx][1]
        tname = s_dir_entries[idx]["filename"] if idx < len(s_dir_entries) else f"frame_{idx}"
        is_tad = len(raw) >= 12 and raw[:6] == b"\x03\x01tad." and tname != "simple_vars.dat"
        cnt = struct.unpack_from("<I", raw, 8)[0] if is_tad else 1
        body_len = max(0, len(raw) - 12) if is_tad else len(raw)
        rec_size = round(body_len / cnt, 2) if cnt > 0 else 0
        server_tables_summary.append(
            {
                "frame_index": idx,
                "table_name": tname,
                "archive_path": s_dir_entries[idx]["name"] if idx < len(s_dir_entries) else tname,
                "record_count": cnt,
                "decompressed_bytes": len(raw),
                "bytes_per_record": rec_size,
            }
        )

    full_cities_all = _parse_lang_cities_and_coords(l_frames[3][1], c_frames[2][1], limit=None)
    city_map = {c["city_id"]: c["name"] for c in full_cities_all}
    continents = _parse_lang_continents(l_frames[4][1], c_frames[6][1])
    continent_map = {c["continent_id"]: c["name"] for c in continents}
    nations = _parse_lang_nations(
        l_frames[0][1],
        c_frames[11][1],
        continent_map=continent_map,
        city_map=city_map,
    )
    nation_map = {n["index"]: n["name"] for n in nations}
    nation_uid_map = {n["uid"]: n["name"] for n in nations}
    competitions = _parse_lang_competitions(
        l_frames[1][1],
        c_frames[5][1],
        continent_map=continent_map,
        nation_uid_map=nation_uid_map,
    )
    clubs = _parse_lang_clubs(
        l_frames[2][1],
        c_frames[3][1],
        limit=sample_limit,
        nation_map=nation_map,
        city_map=city_map,
    )
    cities = full_cities_all if sample_limit is None else full_cities_all[:sample_limit]
    injuries = _parse_lang_injuries(
        l_frames[5][1],
        c_frames[8][1],
        s_frames[8][1] if len(s_frames) > 8 else None,
    )
    awards = _parse_lang_awards(l_frames[6][1], c_frames[1][1], limit=sample_limit)
    stadiums_all = _parse_lang_stadiums(
        l_frames[7][1],
        c_frames[22][1],
        s_frames[22][1] if len(s_frames) > 22 else None,
        limit=None,
        city_map=city_map,
    )
    stadiums = stadiums_all if sample_limit is None else stadiums_all[:sample_limit]
    stage_names = _parse_lang_stage_names(l_frames[8][1])
    media_sources = _parse_lang_media_sources(l_frames[11][1])
    local_regions = _parse_lang_local_regions(l_frames[12][1])
    derbies = _parse_lang_derbies(l_frames[13][1])
    agreements = _parse_lang_agreements(l_frames[14][1])

    first_names_pool = _parse_person_name_pool_table(c_frames[17][1], limit=20)
    last_names_pool = _parse_person_name_pool_table(c_frames[18][1], limit=20)
    common_names_pool = _parse_person_name_pool_table(c_frames[19][1], limit=20)

    # Specific verified Turkish & major European cities showcase from client_db.dat + lang_update_db.dat
    full_cities_showcase: list[dict[str, Any]] = []
    for target_cid in (7998, 8002, 8008, 1280, 1295, 1955):
        if 0 <= target_cid < len(full_cities_all):
            full_cities_showcase.append(full_cities_all[target_cid])

    stadiums_showcase: list[dict[str, Any]] = []
    for st in stadiums_all:
        if st["name"] in ("Old Trafford", "Wembley Stadium", "Camp Nou", "Santiago Bernabéu", "RAMS Park", "Ülker Stadyumu"):
            stadiums_showcase.append(st)

    nations_showcase: list[dict[str, Any]] = []
    for nt in nations:
        if nt["name"] in ("England", "France", "Germany", "Spain", "Türkiye", "Brazil"):
            nations_showcase.append(nt)

    return {
        "available": True,
        "source": "shared/data/database/db/2620/2620_fm/ (client_db.dat, lang_update_db.dat, server_db.dat)",
        "client_db_total_frames": len(c_frames),
        "client_db_frames_count": len(c_frames) - 1,
        "server_db_total_frames": len(s_frames),
        "server_db_frames_count": max(0, len(s_frames) - 1),
        "lang_update_db_total_frames": len(l_frames),
        "lang_update_db_frames_count": len(l_frames) - 1,
        "lang_update_db_languages_count": (len(l_frames) - 1) // 16 if len(l_frames) >= 17 else 1,
        "lang_update_db_tables_per_language": 16,
        "client_db_tables": client_tables_summary,
        "server_db_tables": server_tables_summary,
        "counts": {
            "continents": len(continents),
            "nations": len(nations),
            "competitions": len(competitions),
            "clubs": struct.unpack_from("<I", l_frames[2][1], 8)[0],
            "cities_with_coords": len(full_cities_all),
            "injuries": len(injuries),
            "awards": struct.unpack_from("<I", l_frames[6][1], 8)[0],
            "stadiums": len(stadiums_all),
            "stage_names": len(stage_names),
            "media_sources": len(media_sources),
            "local_regions": len(local_regions),
            "derbies": len(derbies),
            "international_agreements": len(agreements),
            "first_names_pool": first_names_pool["total_count"],
            "last_names_pool": last_names_pool["total_count"],
            "common_names_pool": common_names_pool["total_count"],
        },
        "cities_coord_showcase": full_cities_showcase,
        "stadiums_showcase": stadiums_showcase,
        "nations_showcase": nations_showcase,
        "injuries_showcase": injuries[:10],
        "person_name_pools": {
            "first_names": first_names_pool,
            "last_names": last_names_pool,
            "common_names": common_names_pool,
        },
        "continents": continents,
        "nations": nations if sample_limit is None else nations[:sample_limit],
        "competitions": competitions if sample_limit is None else competitions[:sample_limit],
        "clubs": clubs,
        "cities": cities,
        "injuries": injuries,
        "awards": awards,
        "stadiums": stadiums,
        "stage_names": stage_names if sample_limit is None else stage_names[:sample_limit],
        "media_sources": media_sources if sample_limit is None else media_sources[:sample_limit],
        "local_regions": local_regions if sample_limit is None else local_regions[:sample_limit],
        "derbies": derbies if sample_limit is None else derbies[:sample_limit],
        "international_agreements": agreements,
    }


def extract_permanent_edt_rules(
    fm_install_dir: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Parse all permanent `.edt` rule files (`sugardaddy.edt`, `eng_youth_grades.edt`, `valid_takeovers_only.edt`, etc.)."""
    root = _resolve_fm26_dir(fm_install_dir)
    edt_dir = root / "shared/data/database/db/2620/edt/permanent"
    if not edt_dir.exists():
        return {"available": False, "path": str(edt_dir)}

    files_out: dict[str, Any] = {}
    for ef in sorted(edt_dir.iterdir()):
        if not ef.is_file():
            continue
        txt = ef.read_text(encoding="utf-8", errors="replace")
        active_lines: list[list[str]] = []
        for raw_ln in txt.splitlines():
            ln = raw_ln.strip()
            if not ln or ln.startswith("#"):
                continue
            tokens = re.findall(r'"([^"]*)"|(\S+)', ln)
            parsed_tokens = [a if a != "" else b for a, b in tokens]
            active_lines.append(parsed_tokens)
        files_out[ef.name] = {
            "size_bytes": ef.stat().st_size,
            "active_rules_count": len(active_lines),
            "rules": active_lines,
        }

    return {
        "available": True,
        "source": "shared/data/database/db/2620/edt/permanent",
        "files_count": len(files_out),
        "files": files_out,
    }


# ==============================================================================
# 7. MEDIA INTERACTION TREES (media.fmf), TRAINING (#2,#3) & NEWGEN DEMOGRAPHICS
# ==============================================================================
def extract_media_interaction_trees(
    fm_install_dir: str | os.PathLike[str] | None = None,
    *,
    max_frames: int = 650,
) -> dict[str, Any]:
    """Parse `data/game_simulation/media.fmf` (650 XML frames) into press conference questions, answers & backroom advice."""
    root = _resolve_fm26_dir(fm_install_dir)
    med_fmf = root / "data/game_simulation/media.fmf"
    if not med_fmf.exists():
        return {"available": False, "path": str(med_fmf)}

    frames = extract_fmf_frames(med_fmf)
    dir_strings = _extract_fmf_directory_strings(frames[-1][1])

    questions_found: list[dict[str, Any]] = []
    backroom_advice_count = 0
    press_question_count = 0

    scan_count = min(len(frames) - 1, max_frames)
    for fidx in range(scan_count):
        xml_txt = frames[fidx][1].decode("utf-8", errors="replace")
        qids = re.findall(r"<!--\s*(QID_[A-Z0-9_]+)\s*-->", xml_txt)
        pcaa_count = xml_txt.count('id="pcaa"')
        barl_count = xml_txt.count('id="barl"')
        press_question_count += len(qids)
        backroom_advice_count += barl_count
        if (qids or pcaa_count > 0) and len(questions_found) < 40:
            questions_found.append(
                {
                    "frame_index": fidx,
                    "size_bytes": len(frames[fidx][1]),
                    "question_ids_count": len(qids),
                    "sample_question_ids": qids[:10],
                    "alternative_answers_pcaa_count": pcaa_count,
                    "backroom_advice_barl_count": barl_count,
                }
            )

    return {
        "available": True,
        "source": "data/game_simulation/media.fmf",
        "total_xml_frames": len(frames) - 1,
        "scanned_frames": scan_count,
        "press_questions_in_scanned_frames": press_question_count,
        "backroom_advice_blocks_in_scanned_frames": backroom_advice_count,
        "directory_sample": dir_strings[:40],
        "sample_frames": questions_found,
    }


def extract_training_and_newgen_configs(
    fm_install_dir: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Decode `training.fmf` (300 weekly schedule templates in Frames #2 & #3)
    and `simatchshared.fmf` (all 75 JSB frames: #000..#073 RGB kit/hair/skin palette & crowd configs
    + Frame #074 135 newgen appearance demographic probability rules)."""
    root = _resolve_fm26_dir(fm_install_dir)
    tr_fmf = root / "data/game_simulation/training.fmf"
    sh_fmf = root / "shared/data/simatchshared.fmf"

    training_schedules: dict[str, Any] = {}
    if tr_fmf.exists():
        tr_frames = extract_fmf_frames(tr_fmf)
        for fidx, label in [(0, "schedule_types"), (1, "schedule_categories"), (2, "standard_weekly_schedules"), (3, "youth_or_parttime_schedules")]:
            if fidx < len(tr_frames) - 1:
                try:
                    obj, _ = parse_jsb(tr_frames[fidx][1], 0)
                    arr = _as_jsb_array(obj)
                    training_schedules[label] = {
                        "frame_index": fidx,
                        "count": len(arr),
                        "sample": arr[:5],
                    }
                except Exception:
                    continue

    newgen_demographics: dict[str, Any] = {}
    palette_and_crowd_frames: list[dict[str, Any]] = []
    if sh_fmf.exists():
        sh_frames = extract_fmf_frames(sh_fmf)
        dir_strings = _extract_fmf_directory_strings(sh_frames[-1][1]) if sh_frames else []
        for fidx in range(len(sh_frames) - 1):
            try:
                obj, _ = parse_jsb(sh_frames[fidx][1], 0)
                if fidx == 74:
                    arr = _as_jsb_array(obj)
                    newgen_demographics = {
                        "frame_index": fidx,
                        "rules_count": len(arr),
                        "rules": arr,
                    }
                else:
                    top_keys = list(obj.keys()) if isinstance(obj, dict) else []
                    color_count = len(obj.get("Colors", [])) if isinstance(obj, dict) and isinstance(obj.get("Colors"), list) else 0
                    palette_and_crowd_frames.append(
                        {
                            "frame_index": fidx,
                            "size_bytes": len(sh_frames[fidx][1]),
                            "top_keys": top_keys,
                            "colors_count": color_count,
                            "sample_colors": (obj.get("Colors", [])[:3] if isinstance(obj, dict) and isinstance(obj.get("Colors"), list) else []),
                        }
                    )
            except Exception:
                continue

    return {
        "available": bool(training_schedules or newgen_demographics or palette_and_crowd_frames),
        "training_schedules": training_schedules,
        "newgen_demographics": newgen_demographics,
        "simatchshared_palette_and_crowd_frames_count": len(palette_and_crowd_frames),
        "simatchshared_palette_and_crowd_sample": palette_and_crowd_frames[:15],
        "simatchshared_directory_strings": dir_strings[:80] if sh_fmf.exists() else [],
    }


# ==============================================================================
# 8. IL2CPP METADATA & NATIVE SYMBOL TABLE (il2cpp.usym & global-metadata.dat)
# ==============================================================================
def extract_il2cpp_symbols_and_metadata(
    fm_install_dir: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Parse `fm_Data/il2cpp_data/il2cpp.usym` header (`1,593,548` symbol records)
    and extract C# engine calculation/valuation/rating/tactical symbols from `global-metadata.dat`."""
    root = _resolve_fm26_dir(fm_install_dir)
    usym_path = root / "fm_Data/il2cpp_data/il2cpp.usym"
    meta_path = root / "fm_Data/il2cpp_data/Metadata/global-metadata.dat"

    usym_info: dict[str, Any] = {"available": False}
    if usym_path.exists():
        with usym_path.open("rb") as f:
            hdr = f.read(64)
        magic = hdr[:4].decode("ascii", errors="replace")
        version, symbol_count = struct.unpack_from("<II", hdr, 4)
        usym_info = {
            "available": True,
            "path": str(usym_path),
            "size_bytes": usym_path.stat().st_size,
            "magic": magic,
            "version": version,
            "symbol_records_count": symbol_count,
        }

    meta_info: dict[str, Any] = {"available": False}
    if meta_path.exists():
        raw = meta_path.read_bytes()
        sanity, version = struct.unpack_from("<II", raw, 0)
        pattern = re.compile(
            rb"[A-Za-z0-9_.]*(?:CurrentAbility|PotentialAbility|TransferValue|AskingPrice|"
            rb"ExpectedGoals|MatchRating|PlayerRating|TacticalRole|RoleSuitability|Momentum|"
            rb"QuickMatch|WageDemand|LoyaltyBonus|SigningOnFee|Fatigue|Jadedness|Sharpness|"
            rb"PitchProximity|OutOfPossession|InPossession)[A-Za-z0-9_.]*"
        )
        matches = sorted({m.decode("ascii", errors="ignore") for m in pattern.findall(raw) if 6 <= len(m) <= 90})
        meta_info = {
            "available": True,
            "path": str(meta_path),
            "size_bytes": len(raw),
            "sanity_hex": hex(sanity),
            "metadata_version": version,
            "matched_engine_symbols_count": len(matches),
            "matched_engine_symbols": matches[:200],
        }

    return {
        "available": usym_info["available"] or meta_info["available"],
        "il2cpp_usym": usym_info,
        "global_metadata": meta_info,
    }


# ==============================================================================
# 9. PRE-GAME PEOPLE & CAREER HISTORY DATABASES
#    (basic_people_db.dat, people_db.dat, pl_hist_index/id/dt.dat, summary.dat)
# ==============================================================================
_PERSON_TYPE_LABELS: dict[int, str] = {
    1: "Non-Player / Staff",
    2: "Player",
    3: "Player / Staff",
    4: "Official / Referee",
    5: "Agent / Journalist",
}

_NEGATIVE_PA_RANGES: dict[int, str] = {
    -10: "170-200 (Generational Wonderkid)",
    -95: "160-190 (World-Class Wonderkid)",
    -9: "150-180 (Elite Wonderkid)",
    -85: "140-170 (Top Division Star Potential)",
    -8: "130-160 (First-Team Regular Potential)",
    -75: "120-150 (Good Top-Flight Potential)",
    -7: "110-140 (Solid Professional Potential)",
    -65: "100-130",
    -6: "90-120",
    -55: "80-110",
    -5: "70-100",
    -45: "60-90",
    -4: "50-80",
    -35: "40-70",
    -3: "30-60",
    -25: "20-50",
    -2: "10-40",
    -15: "5-30",
    -1: "1-20",
}


def _decompress_concat_zstd_stream(path: Path, zstd_offset: int | None = None) -> bytes:
    """Decompress a file containing one or more concatenated Zstd frames (auto-detecting first Zstd magic `28 B5 2F FD`,
    and falling back to multi-frame chunk extraction for FM23 `2300..2340` databases)."""
    raw = path.read_bytes()
    if zstd_offset is None or raw[zstd_offset : zstd_offset + 4] != b"\x28\xb5\x2f\xfd":
        detected = raw.find(b"\x28\xb5\x2f\xfd", 0, 128)
        if detected != -1:
            zstd_offset = detected
        else:
            if b"\x28\xb5\x2f\xfd" not in raw:
                return raw
            frames = extract_fmf_frames(path)
            return b"".join(fb for _, fb in frames)
    dctx = zstandard.ZstdDecompressor()
    try:
        with dctx.stream_reader(memoryview(raw)[zstd_offset:], read_across_frames=True) as reader:
            return reader.read()
    except Exception:
        frames = extract_fmf_frames(path)
        return b"".join(fb for _, fb in frames)


def _resolve_person_details_from_people_db(
    pdb_data: bytes,
    target_uids: set[int],
    first_names: list[str],
    last_names: list[str],
    common_names: list[str],
    nation_names: dict[int, str],
    club_names: dict[int, str],
) -> dict[int, dict[str, Any]]:
    """Locate and decode full person blocks (`name`, `DOB`, `8 hidden personality attributes`,
    `height_cm`, `weight_kg`, `birth_city_uid`) from decompressed `people_db.dat` for `target_uids`."""
    resolved: dict[int, dict[str, Any]] = {}
    anchor_pat = b"\x01\x00\x6c\x07\xff\xff\xff\xff\xff\xff\xff\xff\x01\x00\x6c\x07"
    for uid in target_uids:
        tail_pat = struct.pack("<II", uid, uid)
        idx = 0
        while True:
            pos = pdb_data.find(tail_pat, idx)
            if pos == -1:
                break
            idx = pos + 4
            if pos < 40:
                continue
            window_start = max(0, pos - 1400)
            window = pdb_data[window_start:pos]
            anc_rel = window.rfind(anchor_pat)
            if anc_rel == -1:
                continue
            anc = window_start + anc_rel
            if anc + 48 > pos:
                continue
            person_id = struct.unpack_from("<I", pdb_data, pos - 4)[0]
            fn_id = struct.unpack_from("<i", pdb_data, anc + 25)[0]
            ln_id = struct.unpack_from("<i", pdb_data, anc + 30)[0]
            cn_id = struct.unpack_from("<i", pdb_data, anc + 35)[0]
            slen = struct.unpack_from("<I", pdb_data, anc + 40)[0]
            full_name = ""
            after_str = anc + 44
            if 0 < slen < 160 and anc + 44 + slen <= pos:
                full_name = pdb_data[anc + 44 : anc + 44 + slen].decode("utf-8", errors="replace")
                after_str = anc + 44 + slen

            dob_day_of_year, dob_year = (
                struct.unpack_from("<HH", pdb_data, after_str) if after_str + 4 <= pos else (0, 0)
            )
            personality: dict[str, int] = {}
            birth_city_id, birth_city_uid = -1, -1
            if after_str + 37 <= pos:
                p_bytes = list(pdb_data[after_str + 21 : after_str + 29])
                p_labels = (
                    "adaptability",
                    "ambition",
                    "controversy",
                    "loyalty",
                    "pressure",
                    "professionalism",
                    "sportsmanship",
                    "temperament",
                )
                personality = dict(zip(p_labels, p_bytes))
                birth_city_id, birth_city_uid = struct.unpack_from("<ii", pdb_data, after_str + 29)

            fn = first_names[fn_id] if 0 <= fn_id < len(first_names) else ""
            ln = last_names[ln_id] if 0 <= ln_id < len(last_names) else ""
            cn = common_names[cn_id] if 0 <= cn_id < len(common_names) else ""
            display_name = cn if cn else f"{fn} {ln}".strip()
            if not display_name:
                display_name = full_name

            # Look for player header (`person_id` + `\x02` or `\x03`) ~140-320 bytes before `anc`
            height_cm = 0
            weight_kg = 0
            hdr_search_start = max(0, anc - 320)
            for ptype_b in (b"\x02", b"\x03"):
                h_rel = pdb_data[hdr_search_start:anc].find(struct.pack("<I", person_id) + ptype_b)
                if h_rel != -1:
                    h_pos = hdr_search_start + h_rel
                    if h_pos + 137 <= anc:
                        weight_kg = pdb_data[h_pos + 130]
                        height_cm = struct.unpack_from("<H", pdb_data, h_pos + 135)[0]
                    break

            resolved[uid] = {
                "person_id": person_id,
                "uid": uid,
                "display_name": display_name,
                "first_name": fn,
                "last_name": ln,
                "common_name": cn,
                "legal_full_name": full_name,
                "dob_year": dob_year,
                "dob_day_of_year": dob_day_of_year,
                "height_cm": height_cm if 130 <= height_cm <= 220 else None,
                "weight_kg": weight_kg if 40 <= weight_kg <= 130 else None,
                "hidden_personality_1_to_20": personality,
                "birth_city_id": birth_city_id,
                "birth_city_uid": birth_city_uid,
            }
            break
    return resolved


def _decode_player_career_history_chain(
    uid: int,
    uid_to_hist_idx: dict[int, int],
    pl_hist_id_bytes: bytes,
    pl_hist_dt_bytes: bytes,
    club_uid_to_name: dict[int, str],
    comp_uid_to_name: dict[int, str],
) -> list[dict[str, Any]]:
    """Follow the 44-byte singly-linked list career history chain in `pl_hist_dt.dat` for a given `uid`."""
    hist_idx = uid_to_hist_idx.get(uid)
    if hist_idx is None or hist_idx * 8 + 8 > len(pl_hist_id_bytes):
        return []
    head_off, _tail_off = struct.unpack_from("<II", pl_hist_id_bytes, hist_idx * 8)
    rows: list[dict[str, Any]] = []
    cur = int(head_off)
    visited: set[int] = set()
    while 0 <= cur < len(pl_hist_dt_bytes) - 43 and cur not in visited and len(rows) < 60:
        visited.add(cur)
        rec = pl_hist_dt_bytes[cur : cur + 44]
        year_start, year_end = struct.unpack_from("<HH", rec, 0)
        flags = rec[4]
        apps = struct.unpack_from("<b", rec, 5)[0]
        goals = struct.unpack_from("<b", rec, 6)[0]
        club_id = struct.unpack_from("<i", rec, 7)[0]
        club_uid, _club_uid2, comp_uid, _comp_uid2 = struct.unpack_from("<iiii", rec, 11)
        next_off = struct.unpack_from("<i", rec, 40)[0]
        rows.append(
            {
                "byte_offset": cur,
                "season_start_year": year_start,
                "season_end_year": year_end,
                "is_loan": bool(flags & 0x02),
                "appearances": apps,
                "goals": goals,
                "club_id": club_id,
                "club_uid": club_uid,
                "club_name": club_uid_to_name.get(club_uid, ""),
                "comp_uid": comp_uid,
                "comp_name": comp_uid_to_name.get(comp_uid, ""),
                "next_byte_offset": next_off,
            }
        )
        if next_off < 0:
            break
        cur = next_off
    return rows


def _build_person_name_pool_list(raw: bytes) -> list[str]:
    """Decode all 0-based indexed names from a `client_db.dat` person name pool frame (`#17, #18, #19`)."""
    cnt = struct.unpack_from("<I", raw, 8)[0]
    pos = 12
    pool: list[str] = []
    for _ in range(cnt):
        if pos + 8 > len(raw):
            break
        _nid, slen = struct.unpack_from("<II", raw, pos)
        pos += 8
        pool.append(raw[pos : pos + slen].decode("utf-8", errors="replace"))
        pos += slen
    return pool


def extract_pregame_people_and_history_db(
    fm_install_dir: str | os.PathLike[str] | None = None,
    *,
    include_full_people_lookup: bool = True,
) -> dict[str, Any]:
    """Deterministically walk all `723,010` people in `basic_people_db.dat` (`84`/`34`/`22`-byte records),
    compute wonderkid negative `PA` distributions (`-10`, `-95`, `-9`, etc.), resolve names and
    8 hidden personality attributes from `people_db.dat`, and decode the 3-file linked-list career
    history (`pl_hist_index.dat` -> `pl_hist_id.dat` -> `pl_hist_dt.dat`)."""
    root = _resolve_fm26_dir(fm_install_dir)
    db_dir = root / "shared/data/database/db/2620/2620_fm"
    basic_path = db_dir / "basic_people_db.dat"
    if not basic_path.exists():
        return {"available": False, "path": str(basic_path)}

    basic_data = _decompress_concat_zstd_stream(basic_path, zstd_offset=12)
    total_people = struct.unpack_from("<I", basic_data, 0)[0]

    type_length_map = {1: 84, 2: 84, 3: 84, 4: 34, 5: 22}
    person_type_counts: dict[str, int] = {}
    negative_pa_counts: dict[str, int] = {}
    mens_players = 0
    womens_players = 0

    minus_10_records: list[dict[str, Any]] = []
    minus_95_records: list[dict[str, Any]] = []
    top_ca_mens: list[dict[str, Any]] = []
    top_ca_womens: list[dict[str, Any]] = []

    pos = 5
    walked = 0
    while walked < total_people and pos + 22 <= len(basic_data):
        ptype = basic_data[pos + 1]
        rlen = type_length_map.get(ptype)
        if rlen is None or pos + rlen > len(basic_data):
            break
        rec = basic_data[pos : pos + rlen]
        label = _PERSON_TYPE_LABELS.get(ptype, f"type_{ptype}")
        person_type_counts[label] = person_type_counts.get(label, 0) + 1

        if ptype in (2, 3):
            nation_id, nation_uid, club_id, club_uid = struct.unpack_from("<iiii", rec, 2)
            based_nation_id, based_nation_uid = struct.unpack_from("<ii", rec, 26)
            home_rep, cur_rep, world_rep, ca, pa, birth_year = struct.unpack_from("<HHHHhH", rec, 42)
            is_female = bool(rec[65] & 0x10)
            person_id, uid, _uid2 = struct.unpack_from("<III", rec, 72)

            if is_female:
                womens_players += 1
            else:
                mens_players += 1

            entry = {
                "person_id": person_id,
                "uid": uid,
                "person_type": label,
                "gender": "Women" if is_female else "Men",
                "birth_year": birth_year,
                "ca": ca,
                "pa": pa,
                "home_reputation": home_rep,
                "current_reputation": cur_rep,
                "world_reputation": world_rep,
                "nation_id": nation_id,
                "nation_uid": nation_uid,
                "based_nation_id": based_nation_id,
                "based_nation_uid": based_nation_uid,
                "club_id": club_id,
                "club_uid": club_uid,
            }

            if pa < 0:
                pa_key = str(pa)
                negative_pa_counts[pa_key] = negative_pa_counts.get(pa_key, 0) + 1
                if pa == -10:
                    minus_10_records.append(entry)
                elif pa == -95:
                    minus_95_records.append(entry)

            if not is_female and ca >= 176:
                top_ca_mens.append(entry)
            elif is_female and ca >= 168:
                top_ca_womens.append(entry)

        pos += rlen
        walked += 1

    top_ca_mens.sort(key=lambda r: (r["ca"], r["world_reputation"]), reverse=True)
    top_ca_womens.sort(key=lambda r: (r["ca"], r["world_reputation"]), reverse=True)
    minus_10_records.sort(key=lambda r: (r["ca"], r["world_reputation"]), reverse=True)
    minus_95_records.sort(key=lambda r: (r["ca"], r["world_reputation"]), reverse=True)

    # Resolve names from client_db (#17, #18, #19) + lang_update_db (#0 Nations, #1 Comps, #2 Clubs) + people_db.dat
    client_path = db_dir / "client_db.dat"
    lang_path = db_dir / "lang_update_db.dat"
    pdb_path = db_dir / "people_db.dat"

    first_names: list[str] = []
    last_names: list[str] = []
    common_names: list[str] = []
    nation_id_to_name: dict[int, str] = {}
    club_id_to_name: dict[int, str] = {}
    club_uid_to_name: dict[int, str] = {}
    comp_uid_to_name: dict[int, str] = {}

    if client_path.exists():
        c_frames = extract_fmf_frames(client_path)
        if len(c_frames) > 19:
            first_names = _build_person_name_pool_list(c_frames[17][1])
            last_names = _build_person_name_pool_list(c_frames[18][1])
            common_names = _build_person_name_pool_list(c_frames[19][1])
        if len(c_frames) > 26 and lang_path.exists():
            l_frames = extract_fmf_frames(lang_path)
            for n in _parse_lang_nations(l_frames[0][1], c_frames[11][1]):
                nation_id_to_name[n.get("db_nation_id", n["index"])] = n["name"]
            for c in _parse_lang_clubs(l_frames[2][1], limit=None):
                club_id_to_name[c["index"]] = c["name"]
                club_uid_to_name[c["uid"]] = c["name"]
            for comp in _parse_lang_competitions(l_frames[1][1]):
                comp_uid_to_name[comp["uid"]] = comp["name"]

    target_uids: set[int] = set()
    for grp in (minus_10_records, minus_95_records, top_ca_mens[:25], top_ca_womens[:15]):
        for r in grp:
            target_uids.add(r["uid"])

    pdb_resolved: dict[int, dict[str, Any]] = {}
    pdb_decompressed_size = 0
    if include_full_people_lookup and pdb_path.exists() and target_uids:
        pdb_bytes = _decompress_concat_zstd_stream(pdb_path, zstd_offset=12)
        pdb_decompressed_size = len(pdb_bytes)
        pdb_resolved = _resolve_person_details_from_people_db(
            pdb_bytes,
            target_uids,
            first_names,
            last_names,
            common_names,
            nation_id_to_name,
            club_id_to_name,
        )

    def _enrich(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for r in records:
            item = dict(r)
            item["nation_name"] = nation_id_to_name.get(r["nation_id"], "")
            item["club_name"] = club_uid_to_name.get(r["club_uid"], club_id_to_name.get(r["club_id"], ""))
            details = pdb_resolved.get(r["uid"])
            if details:
                item["name"] = details["display_name"]
                item["legal_full_name"] = details["legal_full_name"]
                item["height_cm"] = details["height_cm"]
                item["weight_kg"] = details["weight_kg"]
                item["hidden_personality_1_to_20"] = details["hidden_personality_1_to_20"]
            out.append(item)
        return out

    # Career history 3-file linked list (`pl_hist_index.dat` -> `pl_hist_id.dat` -> `pl_hist_dt.dat`)
    hist_index_path = db_dir / "pl_hist_index.dat"
    hist_id_path = db_dir / "pl_hist_id.dat"
    hist_dt_path = db_dir / "pl_hist_dt.dat"
    non_pl_hist_path = db_dir / "non_pl_hist_dt.dat"
    summary_path = db_dir / "summary.dat"

    career_history_info: dict[str, Any] = {"available": False}
    if hist_index_path.exists() and hist_id_path.exists() and hist_dt_path.exists():
        idx_bytes = _decompress_concat_zstd_stream(hist_index_path, zstd_offset=12)
        id_bytes = _decompress_concat_zstd_stream(hist_id_path, zstd_offset=12)
        dt_bytes = _decompress_concat_zstd_stream(hist_dt_path, zstd_offset=12)

        idx_entries = struct.unpack_from("<I", idx_bytes, 0)[0]
        half_entries = idx_entries // 2
        uid_to_hist_idx: dict[int, int] = {}
        for i in range(half_entries):
            u, h_idx = struct.unpack_from("<II", idx_bytes, 4 + i * 8)
            uid_to_hist_idx[u] = h_idx

        showcase_careers: list[dict[str, Any]] = []
        for star in (_enrich(top_ca_mens[:5]) + _enrich(minus_10_records[:3])):
            chain = _decode_player_career_history_chain(
                star["uid"],
                uid_to_hist_idx,
                id_bytes,
                dt_bytes,
                club_uid_to_name,
                comp_uid_to_name,
            )
            if chain:
                showcase_careers.append(
                    {
                        "name": star.get("name", f"UID {star['uid']}"),
                        "uid": star["uid"],
                        "person_id": star["person_id"],
                        "ca": star["ca"],
                        "pa": star["pa"],
                        "seasons_count": len(chain),
                        "career_rows": chain,
                    }
                )

        non_pl_decompressed_size = 0
        if non_pl_hist_path.exists():
            non_pl_decompressed_size = len(_decompress_concat_zstd_stream(non_pl_hist_path, zstd_offset=12))

        summary_bytes = _decompress_concat_zstd_stream(summary_path, zstd_offset=12) if summary_path.exists() else b""
        career_history_info = {
            "available": True,
            "pl_hist_index_decompressed_bytes": len(idx_bytes),
            "pl_hist_index_total_pairs": idx_entries,
            "unique_players_with_history": half_entries,
            "pl_hist_id_decompressed_bytes": len(id_bytes),
            "pl_hist_dt_decompressed_bytes": len(dt_bytes),
            "pl_hist_dt_row_stride_bytes": 44,
            "pl_hist_dt_estimated_season_rows": len(dt_bytes) // 44,
            "non_pl_hist_dt_decompressed_bytes": non_pl_decompressed_size,
            "summary_dat_decompressed_bytes": len(summary_bytes),
            "summary_dat_hex": summary_bytes.hex() if summary_bytes else "",
            "showcase_player_careers": showcase_careers,
        }

    return {
        "available": True,
        "source_dir": str(db_dir),
        "basic_people_db_decompressed_bytes": len(basic_data),
        "people_db_decompressed_bytes": pdb_decompressed_size,
        "total_people_declared": total_people,
        "total_people_walked": walked,
        "walk_coverage_pct": round(100.0 * walked / max(1, total_people), 4),
        "person_type_counts": person_type_counts,
        "players_by_gender": {
            "mens_players": mens_players,
            "womens_players": womens_players,
        },
        "negative_pa_wonderkid_distribution": {
            k: {
                "count": negative_pa_counts.get(str(k), 0),
                "pa_range_description": desc,
            }
            for k, desc in _NEGATIVE_PA_RANGES.items()
            if negative_pa_counts.get(str(k), 0) > 0
        },
        "wonderkids_pa_minus_10": _enrich(minus_10_records),
        "wonderkids_pa_minus_95": _enrich(minus_95_records),
        "top_mens_players_by_ca": _enrich(top_ca_mens[:25]),
        "top_womens_players_by_ca": _enrich(top_ca_womens[:15]),
        "career_history_linked_list": career_history_info,
    }


# ==============================================================================
# 10. COMPILED .DBC COMPETITION RULES & .LNC LICENSING / NAME OVERRIDES
# ==============================================================================
def extract_dbc_and_lnc_rules(
    fm_install_dir: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Decode `shared/data/sicomps/comps.dbc` (`1,442` Zstd frames of `03 01 cbd.` binary TLV
    competition rule sets), database `.dbc` patches (`2620/dbc/*.dbc`), and `.lnc` licensing
    & name-override directives (`2620/lnc/all/*.lnc`)."""
    root = _resolve_fm26_dir(fm_install_dir)
    comps_dbc = root / "shared/data/sicomps/comps.dbc"
    db_dbc_dir = root / "shared/data/database/db/2620/dbc"
    lnc_dir = root / "shared/data/database/db/2620/lnc/all"

    comps_info: dict[str, Any] = {"available": False}
    if comps_dbc.exists():
        frames = extract_fmf_frames(comps_dbc)
        dir_strings = _extract_fmf_directory_strings(frames[-1][1]) if frames else []
        cbd_frames = 0
        total_decompressed_bytes = 0
        sample_frames: list[dict[str, Any]] = []
        for idx, (_off, fbytes) in enumerate(frames[:-1]):
            total_decompressed_bytes += len(fbytes)
            magic = fbytes[:6].decode("latin1", errors="replace") if len(fbytes) >= 6 else ""
            if fbytes[:6] == b"\x03\x01cbd.":
                cbd_frames += 1
            if idx < 15:
                ascii_tokens = [
                    m.decode("utf-8", errors="replace")
                    for m in re.findall(rb"[A-Za-z0-9_/\- ]{4,60}", fbytes[:2048])[:8]
                ]
                sample_frames.append(
                    {
                        "frame_index": idx,
                        "decompressed_bytes": len(fbytes),
                        "magic_hex": fbytes[:6].hex(),
                        "magic_ascii": repr(magic),
                        "sample_tokens": ascii_tokens,
                    }
                )
        comps_info = {
            "available": True,
            "path": str(comps_dbc),
            "compressed_size_bytes": comps_dbc.stat().st_size,
            "total_zstd_frames": len(frames),
            "competition_rule_frames_count": len(frames) - 1,
            "cbd_magic_frames_count": cbd_frames,
            "total_decompressed_bytes": total_decompressed_bytes,
            "directory_strings_sample": dir_strings[:50],
            "sample_frames": sample_frames,
        }

    db_dbc_files: list[dict[str, Any]] = []
    if db_dbc_dir.exists():
        for p in sorted(db_dbc_dir.rglob("*.dbc")):
            try:
                decompressed = _decompress_concat_zstd_stream(p, zstd_offset=12)
                tokens = [
                    m.decode("utf-8", errors="replace")
                    for m in re.findall(rb"[A-Za-z0-9_.\- ]{5,80}", decompressed)[:10]
                ]
                db_dbc_files.append(
                    {
                        "file": str(p.relative_to(db_dbc_dir)).replace("\\", "/"),
                        "compressed_bytes": p.stat().st_size,
                        "decompressed_bytes": len(decompressed),
                        "magic_hex": decompressed[:6].hex(),
                        "sample_strings": tokens,
                    }
                )
            except Exception:
                continue

    lnc_files_summary: list[dict[str, Any]] = []
    lnc_command_counts: dict[str, int] = {}
    if lnc_dir.exists():
        cmd_re = re.compile(r'^"([A-Z0-9_]+)"', re.MULTILINE)
        for p in sorted(lnc_dir.glob("*.lnc")):
            raw = p.read_bytes()
            if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
                txt = raw.decode("utf-16", errors="replace")
            else:
                txt = raw.decode("utf-8", errors="replace")
            cmds = cmd_re.findall(txt)
            for c in cmds:
                lnc_command_counts[c] = lnc_command_counts.get(c, 0) + 1
            lnc_files_summary.append(
                {
                    "file": p.name,
                    "size_bytes": len(raw),
                    "directives_count": len(cmds),
                }
            )

    return {
        "available": comps_info["available"] or bool(db_dbc_files) or bool(lnc_files_summary),
        "sicomps_comps_dbc": comps_info,
        "db_2620_dbc_files_count": len(db_dbc_files),
        "db_2620_dbc_files": db_dbc_files,
        "lnc_2620_files_count": len(lnc_files_summary),
        "lnc_command_counts": dict(sorted(lnc_command_counts.items(), key=lambda kv: kv[1], reverse=True)),
        "lnc_files_summary": lnc_files_summary,
    }


# ==============================================================================
# 11. AUXILIARY SIMULATION .FMF ARCHIVES
#     (filters.fmf, achievements.fmf, leaderboards.fmf, settings.fmf, store.fmf, profanity_filter.fmf)
# ==============================================================================
def extract_simulation_aux_fmf_archives(
    fm_install_dir: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Decode the remaining simulation `.fmf` archives under `data/game_simulation/`:
    - `filters.fmf` (`2` XML files containing `445` `<record>` filter definitions),
    - `achievements.fmf` (`1` XML file containing `50` Steam/Epic/Xbox achievement `<record>` rules),
    - `leaderboards.fmf` (`1` XML file containing `28` leaderboard scoring `<record>` items),
    - `settings.fmf` (`9` user/game preference schema XML files across platforms),
    - `store.fmf` (`2` in-game store item XML files),
    - `profanity_filter.fmf` (`2` files: `config.xml` + `microsoft.txt`),
    - `languages.fmf` (`205.6 MB` multi-language localization archive metadata)."""
    root = _resolve_fm26_dir(fm_install_dir)
    sim_dir = root / "data/game_simulation"
    if not sim_dir.exists():
        return {"available": False, "path": str(sim_dir)}

    result: dict[str, Any] = {"available": True, "archives": {}}
    archive_names = (
        "filters.fmf",
        "achievements.fmf",
        "leaderboards.fmf",
        "settings.fmf",
        "store.fmf",
        "profanity_filter.fmf",
    )
    for name in archive_names:
        fpath = sim_dir / name
        if not fpath.exists():
            continue
        frames = extract_fmf_frames(fpath)
        dir_entries = read_fmf_directory(fpath)
        archive_files = [e["name"] for e in dir_entries] if dir_entries else _extract_fmf_directory_strings(frames[-1][1])
        total_decompressed = sum(len(fb) for _, fb in frames[:-1])
        sample_items: list[str] = []
        xml_record_items_count = 0
        for _off, fb in frames[:-1]:
            txt = fb.decode("utf-8-sig", errors="replace")
            xml_record_items_count += len(re.findall(r"<record\b", txt))
            if not sample_items:
                sample_items = re.findall(r'value="([^"]{3,60})"', txt)[:10]
        result["archives"][name] = {
            "compressed_bytes": fpath.stat().st_size,
            "archive_files_count": len(dir_entries) if dir_entries else max(0, len(frames) - 1),
            "archive_files": archive_files,
            "content_frames_count": max(0, len(frames) - 1),
            "xml_record_items_count": xml_record_items_count,
            "total_decompressed_bytes": total_decompressed,
            "directory_strings_sample": archive_files[:25],
            "first_frame_sample_values": sample_items,
        }

    lang_fmf = sim_dir / "languages.fmf"
    if lang_fmf.exists():
        result["archives"]["languages.fmf"] = {
            "compressed_bytes": lang_fmf.stat().st_size,
            "note": "Master localization string archive (.ltc tables for 22+ languages)",
        }

    return result


# ==============================================================================
# 12. MULTI-VERSION PRE-GAME DATABASE EVOLUTION (2300..2620: FM23 / FM24 / FM26)
# ==============================================================================
_DB_VERSION_LABELS: dict[str, str] = {
    "2300": "FM23.0 Base Database",
    "2310": "FM23.1 Update (Delta)",
    "2320": "FM23.2 Update (Delta)",
    "2330": "FM23.3 Winter Transfer Update",
    "2340": "FM23.4 Final Update",
    "2400": "FM24.0 Base Database",
    "2430": "FM24.3 Winter Transfer Update",
    "2600": "FM26.0 Base Database",
    "2620": "FM26.2 Winter Transfer Update (Active)",
}

_SHOWCASE_EVOLUTION_PLAYERS: dict[int, str] = {
    85139014: "Kylian Mbappé",
    28049320: "Harry Kane",
    85140178: "Ousmane Dembélé",
    29179241: "Erling Haaland",
    28106491: "Declan Rice",
    28122642: "Bukayo Saka",
    67217524: "Rodri",
    29232937: "Jude Bellingham",
    19302146: "Vinícius Júnior",
    2000256231: "Lamine Yamal",
    2000115202: "Désiré Doué",
    2000138835: "Kenan Yıldız",
    2000077193: "Arda Güler",
    2000179712: "Warren Zaïre-Emery",
    2000296497: "Pau Cubarsí",
    2000220941: "Endrick",
    2000263999: "Estêvão",
    92026209: "Hakan Çalhanoğlu",
    37061602: "Orkun Kökçü",
    37060600: "Ferdi Kadıoğlu",
    70112874: "Barış Alper Yılmaz",
    70097248: "Zeki Çelik",
    2000103330: "Can Uzun",
}


def extract_multi_version_database_evolution(
    fm_install_dir: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Decode and compare all 9 historical and active database versions (`2300`, `2310`, `2320`,
    `2330`, `2340`, `2400`, `2430`, `2600`, `2620`) under `shared/data/database/db/`:
    - Walks `100%` of `basic_people_db.dat` across all 9 versions (`83`-byte records in `2300..2430`,
      `84`-byte records in `2600..2620` with Women's Football bit `0x10` at `+65`),
    - Extracts `client_db.dat` table counts (`30` tables in FM23 `2300..2340`, `31` tables in FM24/FM26 `2400..2620`),
    - Tracks `-10` and `-95` wonderkid cohorts and `CA`/`PA` trajectories across `2300..2620`."""
    root = _resolve_fm26_dir(fm_install_dir)
    db_root = root / "shared/data/database/db"
    if not db_root.exists():
        return {"available": False, "path": str(db_root)}

    versions = sorted(p.name for p in db_root.iterdir() if p.is_dir() and (p / f"{p.name}_fm").exists())

    # Load 2620 club names for clean club resolution
    clubs_uid_map: dict[int, str] = {}
    l2620_path = db_root / "2620/2620_fm/lang_update_db.dat"
    if l2620_path.exists():
        l2620_frames = extract_fmf_frames(l2620_path)
        for c in _parse_lang_clubs(l2620_frames[2][1], limit=None):
            clubs_uid_map[c["uid"]] = c["name"]

    versions_summary: dict[str, dict[str, Any]] = {}
    player_trajectories: dict[str, dict[str, Any]] = {
        name: {"uid": uid, "versions": {}} for uid, name in _SHOWCASE_EVOLUTION_PLAYERS.items()
    }
    total_people_walked_all_versions = 0

    for ver in versions:
        fm_dir = db_root / ver / f"{ver}_fm"
        bp_path = fm_dir / "basic_people_db.dat"
        c_path = fm_dir / "client_db.dat"
        l_path = fm_dir / "lang_update_db.dat"
        s_path = fm_dir / "server_db.dat"

        # 1. Extract client_db.dat table counts
        table_counts: dict[int, int] = {}
        if c_path.exists():
            c_frames = extract_fmf_frames(c_path)
            if len(c_frames) == 32:
                for idx, (_off, raw) in enumerate(c_frames[:-1]):
                    if len(raw) >= 12 and raw[:6] == b"\x03\x01tad.":
                        table_counts[idx] = struct.unpack_from("<I", raw, 8)[0]
            else:
                full_c = b"".join(fb for _, fb in c_frames[:-1])
                pos_c = 0
                t_idx = 0
                while True:
                    idx_c = full_c.find(b"\x03\x01tad.", pos_c)
                    if idx_c == -1:
                        break
                    table_counts[t_idx] = struct.unpack_from("<I", full_c, idx_c + 8)[0]
                    t_idx += 1
                    pos_c = idx_c + 12

        is_30_table_fm23 = len(table_counts) == 30
        db_entity_counts = {
            "tables_count": len(table_counts),
            "awards": table_counts.get(1, 0),
            "cities": table_counts.get(2, 0),
            "clubs": table_counts.get(3, 0),
            "competitions": table_counts.get(5, 0),
            "continents": table_counts.get(6, 0),
            "stage_flags_or_rules": table_counts.get(7, 0),
            "injuries": table_counts.get(8, 0),
            "media_sources": table_counts.get(9, 0),
            "nations": table_counts.get(11, 0),
            "languages": table_counts.get(12, 0),
            "first_names_pool": table_counts.get(14, 0),
            "last_names_pool": table_counts.get(15, 0),
            "common_names_pool": table_counts.get(16, 0),
            "local_regions": table_counts.get(20 if is_30_table_fm23 else 21, 0),
            "stadiums": table_counts.get(21 if is_30_table_fm23 else 22, 0),
            "stage_names": table_counts.get(23 if is_30_table_fm23 else 24, 0),
            "agreements": table_counts.get(24 if is_30_table_fm23 else 25, 0),
            "weather": table_counts.get(26 if is_30_table_fm23 else 28, 0),
            "currencies": table_counts.get(27 if is_30_table_fm23 else 29, 0),
            "derbies": table_counts.get(28 if is_30_table_fm23 else 30, 0),
        }

        # 2. Deterministically walk basic_people_db.dat
        dec = _decompress_concat_zstd_stream(bp_path) if bp_path.exists() else b""
        declared_cnt = struct.unpack_from("<I", dec, 0)[0] if len(dec) >= 4 else 0
        rec123_len = 84 if ver.startswith("26") else 83
        type_map = {1: rec123_len, 2: rec123_len, 3: rec123_len, 4: 34, 5: 22}

        pos = 5
        walked = 0
        players = 0
        mens_players = 0
        womens_players = 0
        staff = 0
        officials = 0
        agents = 0
        pa_minus_10_count = 0
        pa_minus_95_count = 0

        while walked < declared_cnt and pos + 22 <= len(dec):
            pt = dec[pos + 1]
            rl = type_map.get(pt)
            if rl is None or pos + rl > len(dec):
                break
            if pt == 1:
                staff += 1
            elif pt in (2, 3):
                players += 1
                is_fem = bool(rec123_len == 84 and (dec[pos + 65] & 0x10))
                if is_fem:
                    womens_players += 1
                else:
                    mens_players += 1
                _nat_id, _nat_uid, _club_id, club_uid = struct.unpack_from("<iiii", dec, pos + 2)
                _h_rep, _c_rep, w_rep, ca, pa, _byear = struct.unpack_from("<HHHHhH", dec, pos + 42)
                _pid, uid, _ = struct.unpack_from("<III", dec, pos + rl - 12)
                if pa == -10:
                    pa_minus_10_count += 1
                elif pa == -95:
                    pa_minus_95_count += 1
                if uid in _SHOWCASE_EVOLUTION_PLAYERS:
                    pname = _SHOWCASE_EVOLUTION_PLAYERS[uid]
                    player_trajectories[pname]["versions"][ver] = {
                        "ca": ca,
                        "pa": pa,
                        "world_reputation": w_rep,
                        "club_uid": club_uid,
                        "club_name": clubs_uid_map.get(club_uid, ""),
                    }
            elif pt == 4:
                officials += 1
            elif pt == 5:
                agents += 1
            pos += rl
            walked += 1

        total_people_walked_all_versions += walked
        versions_summary[ver] = {
            "version": ver,
            "label": _DB_VERSION_LABELS.get(ver, ver),
            "player_staff_record_stride_bytes": rec123_len,
            "has_lang_update_db": l_path.exists(),
            "has_server_db": s_path.exists(),
            "total_people_declared": declared_cnt,
            "total_people_walked": walked,
            "walk_coverage_pct": round(100.0 * walked / max(1, declared_cnt), 2),
            "players_total": players,
            "mens_players": mens_players,
            "womens_players": womens_players,
            "staff": staff,
            "officials": officials,
            "agents": agents,
            "wonderkids_pa_minus_10_count": pa_minus_10_count,
            "wonderkids_pa_minus_95_count": pa_minus_95_count,
            "client_db_counts": db_entity_counts,
        }

    return {
        "available": True,
        "versions_count": len(versions),
        "versions_list": versions,
        "total_people_walked_across_all_versions": total_people_walked_all_versions,
        "versions": versions_summary,
        "showcase_player_trajectories": player_trajectories,
    }


# ==============================================================================
# MASTER AGGREGATOR FOR ALL 12 REVERSE-ENGINEERED GAME-FILE SYSTEMS
# ==============================================================================
def extract_all_game_files_summary(
    fm_install_dir: str | os.PathLike[str] | None = None,
    *,
    include_pregame_people_db: bool = True,
    include_multi_version_db: bool = True,
) -> dict[str, Any]:
    """Run all 12 FM26 Game-File Reverse-Engineering Extractors and return a unified summary."""
    qme = extract_qme_distributions(fm_install_dir, sample_limit=5)
    momentum = extract_momentum_weightings(fm_install_dir)
    oop_grid = extract_oop_pitch_proximity_grid(fm_install_dir)
    xg_models = extract_xg_shot_models(fm_install_dir)
    styles = extract_tactical_styles_and_presets(fm_install_dir)
    schemas = extract_editor_schemas_and_enums(fm_install_dir)
    master_db = extract_master_db_tables(fm_install_dir, sample_limit=5)
    edt_rules = extract_permanent_edt_rules(fm_install_dir)
    media = extract_media_interaction_trees(fm_install_dir, max_frames=650)
    training_newgen = extract_training_and_newgen_configs(fm_install_dir)
    il2cpp = extract_il2cpp_symbols_and_metadata(fm_install_dir)
    people_hist = (
        extract_pregame_people_and_history_db(fm_install_dir, include_full_people_lookup=True)
        if include_pregame_people_db
        else {"available": False}
    )
    dbc_lnc = extract_dbc_and_lnc_rules(fm_install_dir)
    aux_fmfs = extract_simulation_aux_fmf_archives(fm_install_dir)
    multi_ver = (
        extract_multi_version_database_evolution(fm_install_dir)
        if include_multi_version_db
        else {"available": False}
    )

    return {
        "1_qme_statistical_distributions": {
            "total_distributions": qme.get("distributions_total_count", 0),
            "stat_relevant_attributes_count": qme.get("stat_relevant_attributes_count", 0),
            "attribute_combination_weights": qme.get("attribute_combination_weights_count", 0),
            "player_ratings_versions_count": qme.get("player_ratings_versions_count", 0),
            "player_ratings_latest_start_value": qme.get("player_ratings_latest_start_value", 6.70),
            "distribution_types": qme.get("distribution_types", {}),
            "sample": qme.get("distributions", []),
        },
        "2_match_momentum_spatial_engine": {
            "total_spatial_rules": momentum.get("total_spatial_rules", 0),
            "event_types": momentum.get("event_types", []),
            "rules_by_event": momentum.get("rules_by_event", {}),
        },
        "3_oop_2d_pitch_proximity_grid": {
            "oop_role_attribute_scoring_count": oop_grid.get("oop_role_attribute_scoring_count", 0),
            "total_position_role_entries": oop_grid.get("total_position_role_entries", 0),
            "total_spatial_zone_couples": oop_grid.get("total_spatial_zone_couples", 0),
            "unique_position_codes": oop_grid.get("unique_position_codes", []),
            "unique_role_codes": oop_grid.get("unique_role_codes", []),
            "sample_entry": (oop_grid.get("entries") or [None])[0],
        },
        "4_xg_shot_models_and_tactical_presets": {
            "xg_versions_available_count": xg_models.get("versions_available_count", 0),
            "xg_versions_available": xg_models.get("versions_available", []),
            "xg_shot_models_count": xg_models.get("models_count", 0),
            "xg_shot_models": xg_models.get("models", {}),
            "tactical_styles_xml_count": styles.get("tactical_styles_xml_count", 0),
            "binary_tactical_presets_count": styles.get("binary_tactical_presets_count", 0),
            "cat_formation_combinations_count": styles.get("cat_formation_combinations_count", 0),
            "rts_style_instruction_vectors_count": styles.get("rts_style_instruction_vectors_count", 0),
            "tactical_pitch_positioning_table": styles.get("tactical_pitch_positioning_table", {}),
            "tactical_styles": styles.get("tactical_styles", []),
        },
        "5_editor_schemas_and_fourcc_enums": {
            "total_xml_frames": schemas.get("total_xml_frames", 0),
            "enum_groups_count": schemas.get("enum_groups_count", 0),
            "entity_schemas_counts": {
                k: v.get("fields_count", 0) for k, v in schemas.get("entity_schemas", {}).items()
            },
        },
        "6_pregame_master_databases_and_edt_rules": {
            "client_db_total_frames": master_db.get("client_db_total_frames", 0),
            "lang_update_db_total_frames": master_db.get("lang_update_db_total_frames", 0),
            "lang_update_db_languages_count": master_db.get("lang_update_db_languages_count", 0),
            "server_db_total_frames": master_db.get("server_db_total_frames", 0),
            "counts": master_db.get("counts", {}),
            "cities_coord_showcase": master_db.get("cities_coord_showcase", []),
            "stadiums_showcase": master_db.get("stadiums_showcase", []),
            "injuries_showcase": master_db.get("injuries_showcase", []),
            "edt_files": {
                k: v.get("active_rules_count", 0) for k, v in edt_rules.get("files", {}).items()
            },
        },
        "7_media_interactions_training_and_newgen": {
            "media_total_xml_frames": media.get("total_xml_frames", 0),
            "press_questions_in_sample": media.get("press_questions_in_scanned_frames", 0),
            "backroom_advice_in_sample": media.get("backroom_advice_blocks_in_scanned_frames", 0),
            "training_schedules": {
                k: v.get("count", 0) for k, v in training_newgen.get("training_schedules", {}).items()
            },
            "newgen_demographic_rules": training_newgen.get("newgen_demographics", {}).get("rules_count", 0),
            "simatchshared_palette_and_crowd_frames_count": training_newgen.get(
                "simatchshared_palette_and_crowd_frames_count", 0
            ),
        },
        "8_il2cpp_symbols_and_metadata": {
            "usym_symbol_records_count": il2cpp.get("il2cpp_usym", {}).get("symbol_records_count", 0),
            "global_metadata_version": il2cpp.get("global_metadata", {}).get("metadata_version"),
            "matched_engine_symbols_count": il2cpp.get("global_metadata", {}).get("matched_engine_symbols_count", 0),
            "sample_engine_symbols": il2cpp.get("global_metadata", {}).get("matched_engine_symbols", [])[:25],
        },
        "9_pregame_people_and_career_history_db": {
            "total_people_walked": people_hist.get("total_people_walked", 0),
            "walk_coverage_pct": people_hist.get("walk_coverage_pct", 0.0),
            "person_type_counts": people_hist.get("person_type_counts", {}),
            "players_by_gender": people_hist.get("players_by_gender", {}),
            "negative_pa_wonderkid_distribution": people_hist.get("negative_pa_wonderkid_distribution", {}),
            "wonderkids_pa_minus_10": people_hist.get("wonderkids_pa_minus_10", []),
            "wonderkids_pa_minus_95": people_hist.get("wonderkids_pa_minus_95", []),
            "top_mens_players_by_ca": people_hist.get("top_mens_players_by_ca", [])[:10],
            "top_womens_players_by_ca": people_hist.get("top_womens_players_by_ca", [])[:10],
            "career_history_linked_list": people_hist.get("career_history_linked_list", {}),
        },
        "10_dbc_competition_rules_and_lnc_licensing": {
            "sicomps_comps_dbc_frames": dbc_lnc.get("sicomps_comps_dbc", {}).get("competition_rule_frames_count", 0),
            "sicomps_comps_dbc_decompressed_bytes": dbc_lnc.get("sicomps_comps_dbc", {}).get(
                "total_decompressed_bytes", 0
            ),
            "db_2620_dbc_files_count": dbc_lnc.get("db_2620_dbc_files_count", 0),
            "lnc_2620_files_count": dbc_lnc.get("lnc_2620_files_count", 0),
            "lnc_command_counts": dbc_lnc.get("lnc_command_counts", {}),
        },
        "11_simulation_auxiliary_fmf_archives": aux_fmfs.get("archives", {}),
        "12_multi_version_database_evolution": {
            "versions_count": multi_ver.get("versions_count", 0),
            "versions_list": multi_ver.get("versions_list", []),
            "total_people_walked_across_all_versions": multi_ver.get("total_people_walked_across_all_versions", 0),
            "versions": multi_ver.get("versions", {}),
            "showcase_player_trajectories": multi_ver.get("showcase_player_trajectories", {}),
        },
    }

