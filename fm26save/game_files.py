"""FM26 Game Installation File Reverse-Engineering Extractors (All 8 Systems).

Extracts and decodes official Football Manager 26 installation archives (.fmf, .dat, .jsb, .edt, .usym):
1. Quick Match Engine (QME) Statistical Distributions (`simatch.fmf` Frames #118, #119 — 3,137 Normal/Binned distributions)
2. Match Momentum Spatial Engine (`simatch.fmf` Frame #113 — 48 event × zone momentum rules)
3. Out-Of-Possession (OP*) 2D Pitch Proximity Tactical Grid (`simatch.fmf` Frame #115 — 118 Role entries × 24 spatial zones)
4. 11 Shot-Type xG Logistic Regression Models (`simatch.fmf` Frames #90..#100, v26.1.4.1) & 101 Dual-Formation Tactical Presets (`Frames #121..#222`)
5. 106 Internal Database XML Schemas & Master FourCC Enums (`shared/data/editor.fmf` — 444 enum groups + entity schemas)
6. Pre-Game Master Databases (`client_db.dat`, `lang_update_db.dat`, `server_db.dat` — 58,349 Cities with Lat/Lon/Attraction, 96,343 Clubs, 51,118 Stadiums, 7,973 Competitions, 3,884 Awards, 2,527 Regions, 1,683 Derbies, 251 Nations, 136 Injuries) & `.edt` Permanent Rule Files
7. Press Conference, Backroom Advice, Training Schedules & Newgen Demographics (`media.fmf` 650 XMLs, `training.fmf` 300 schedules, `simatchshared.fmf` 135 newgen appearance rules)
8. IL2CPP Metadata & Native Symbol Table (`il2cpp.usym` 1,593,548 symbols & `global-metadata.dat` C# engine symbols)
"""

from __future__ import annotations

import os
import re
import struct
from collections import Counter
from pathlib import Path
from typing import Any

from fm26save.formulas import DEFAULT_FM26_INSTALL_DIR, extract_fmf_frames, parse_jsb

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
# 1. QUICK MATCH ENGINE (QME) STATISTICAL DISTRIBUTIONS (simatch.fmf #118, #119)
# ==============================================================================
def extract_qme_distributions(
    fm_install_dir: str | os.PathLike[str] | None = None,
    *,
    sample_limit: int | None = None,
) -> dict[str, Any]:
    """Decode `qme_distribution_data.jsb` (Frame #119, 3,137 Normal/Binned distributions)
    and `qme_attribute_combination_weights_data.jsb` (Frame #118, 68 weights) from `simatch.fmf`."""
    root = _resolve_fm26_dir(fm_install_dir)
    sim_fmf = root / "shared/data/simatch.fmf"
    if not sim_fmf.exists():
        return {"available": False, "path": str(sim_fmf)}

    frames = extract_fmf_frames(sim_fmf)
    attr_weights_obj, _ = parse_jsb(frames[118][1], 0)
    dist_obj, _ = parse_jsb(frames[119][1], 0)

    raw_weights = _as_jsb_array(attr_weights_obj)
    raw_dists = _as_jsb_array(dist_obj)

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
        "source": "shared/data/simatch.fmf (Frames #118 & #119)",
        "attribute_combination_weights_count": len(raw_weights),
        "attribute_combination_weights": raw_weights,
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
# 3. OUT-OF-POSSESSION (OP*) 2D PITCH PROXIMITY TACTICAL GRID (simatch.fmf #115)
# ==============================================================================
def extract_oop_pitch_proximity_grid(
    fm_install_dir: str | os.PathLike[str] | None = None,
    *,
    role_filter: int | None = None,
) -> dict[str, Any]:
    """Decode `oop_pitch_proximity_scores.jsb` (Frame #115, 93.5 KB, 118 Position+Role entries × 24 spatial zones)."""
    root = _resolve_fm26_dir(fm_install_dir)
    sim_fmf = root / "shared/data/simatch.fmf"
    if not sim_fmf.exists():
        return {"available": False, "path": str(sim_fmf)}

    frames = extract_fmf_frames(sim_fmf)
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
        "source": "shared/data/simatch.fmf (Frame #115 — oop_pitch_proximity_scores.jsb)",
        "total_position_role_entries": len(arr),
        "total_spatial_zone_couples": total_couples,
        "unique_position_codes": sorted(unique_positions),
        "unique_role_codes": sorted(unique_roles),
        "entries": entries,
    }


# ==============================================================================
# 4. ALL 11 SHOT-TYPE xG MODELS (#90..#100) & 101 TACTICAL STYLE PRESETS (#121..#222)
# ==============================================================================
def extract_xg_shot_models(
    fm_install_dir: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Extract all 11 Shot-Type xG Logistic Regression models (Frames #90..#100, Version 26.1.4.1) from `simatch.fmf`."""
    root = _resolve_fm26_dir(fm_install_dir)
    sim_fmf = root / "shared/data/simatch.fmf"
    if not sim_fmf.exists():
        return {"available": False, "path": str(sim_fmf)}

    frames = extract_fmf_frames(sim_fmf)
    models: dict[str, Any] = {}
    for fidx in range(90, 101):
        obj, _ = parse_jsb(frames[fidx][1], 0)
        shot_type = str(obj.get("shot_type", f"frame_{fidx}"))
        coeffs = obj.get("coefficients", {})
        scaled_coeffs = (
            {k: round(float(v) / 1e8, 8) for k, v in coeffs.items()} if isinstance(coeffs, dict) else coeffs
        )
        models[shot_type] = {
            "frame_index": fidx,
            "shot_type": shot_type,
            "version": obj.get("version_number", "26.1.4.1"),
            "intercept": round(float(obj.get("intercept", 0)) / 1e8, 8),
            "coefficients": scaled_coeffs,
            "formula": "P(Goal) = 1 / (1 + exp(-(intercept + sum(coeff_i * x_i))))",
        }

    return {
        "available": True,
        "source": "shared/data/simatch.fmf (Frames #90..#100)",
        "models_count": len(models),
        "models": models,
    }


def extract_tactical_styles_and_presets(
    fm_install_dir: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Decode `simatch.fmf` Frame #192 (Tactical Styles XML) and the 101 Dual-Formation `.cat`/`.rts`/`.tac` presets."""
    root = _resolve_fm26_dir(fm_install_dir)
    sim_fmf = root / "shared/data/simatch.fmf"
    if not sim_fmf.exists():
        return {"available": False, "path": str(sim_fmf)}

    frames = extract_fmf_frames(sim_fmf)
    dir_strings = _extract_fmf_directory_strings(frames[-1][1])
    preset_filenames = [
        s for s in dir_strings if s.endswith((".tac", ".cat", ".rts", ".xml", ".jsb"))
    ]

    # Frame #192 is Tactical Styles XML
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
                " tactical_hint": hint_m.group(1).strip() if hint_m else "",
                "template_attributes": [{"attribute": k, "weight": w} for k, w in attrs],
            }
        )

    # Summarize binary tactical preset frames (#121..#222 excluding #192)
    tactical_frames_summary: list[dict[str, Any]] = []
    for fidx in range(121, min(223, len(frames) - 1)):
        if fidx == 192:
            continue
        raw = frames[fidx][1]
        magic = raw[:8].hex(" ")
        ascii_strings = [
            s.decode("utf-8", errors="ignore")
            for s in re.findall(rb"[a-zA-Z0-9_\- ]{4,40}", raw[:512])
        ]
        tactical_frames_summary.append(
            {
                "frame_index": fidx,
                "size_bytes": len(raw),
                "header_hex": magic,
                "header_strings": ascii_strings[:5],
            }
        )

    return {
        "available": True,
        "source": "shared/data/simatch.fmf (Frames #121..#222)",
        "tactical_styles_xml_count": len(style_blocks),
        "tactical_styles": style_blocks,
        "binary_tactical_presets_count": len(tactical_frames_summary),
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

    return {
        "available": True,
        "source": "shared/data/editor.fmf (106 XML frames)",
        "total_xml_frames": len(frames) - 1,
        "directory_files": [s for s in dir_strings if s.endswith(".xml")],
        "enum_groups_count": len(enum_groups),
        "enum_groups": enum_groups,
        "entity_schemas": entity_schemas,
    }


# ==============================================================================
# 6. PRE-GAME MASTER DATABASES (client_db.dat, lang_update_db.dat) & .EDT RULES
# ==============================================================================
def _parse_lang_nations(raw: bytes) -> list[dict[str, Any]]:
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
    return out


def _parse_lang_competitions(raw: bytes) -> list[dict[str, Any]]:
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
        pos += l3 + 1
        out.append({"index": idx, "uid": uid, "name": name, "short_name": short_name, "code": code})
    return out


def _parse_lang_clubs(raw: bytes, *, limit: int | None = None) -> list[dict[str, Any]]:
    cnt = struct.unpack_from("<I", raw, 8)[0]
    pos = 12
    out: list[dict[str, Any]] = []
    target = cnt if limit is None else min(cnt, limit)
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
        out.append(
            {
                "index": idx,
                "uid": uid,
                "name": name,
                "short_name": short_name,
                "six_letter_name": six_letter,
                "three_letter_name": three_letter,
                "alt_short_name": alt_short,
                "nickname": nickname,
            }
        )
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
            cid_db, uid_db = struct.unpack_from("<II", rec, 33)
            entry.update(
                {
                    "latitude": round(lat, 5),
                    "longitude": round(lon, 5),
                    "attraction_1_20": attraction,
                    "nation_id": nation_id,
                    "local_region_id": region_id,
                    "altitude_raw": alt_raw,
                    "inhabitants_bracket": inhab_code,
                    "weather_profile_id": weather_id,
                    "db_city_id": cid_db,
                    "db_uid": uid_db,
                }
            )
        out.append(entry)
    return out


def _parse_lang_injuries(raw: bytes) -> list[dict[str, Any]]:
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
        sentence = raw[pos : pos + l2].decode("utf-8", errors="replace")
        pos += l2 + 2
        out.append({"index": idx, "uid": uid, "name": name, "sentence_name": sentence})
    return out


def _parse_lang_awards(raw: bytes, *, limit: int | None = None) -> list[dict[str, Any]]:
    cnt = struct.unpack_from("<I", raw, 8)[0]
    pos = 12
    out: list[dict[str, Any]] = []
    target = cnt if limit is None else min(cnt, limit)
    for idx in range(target):
        uid, l1 = struct.unpack_from("<II", raw, pos)
        pos += 8
        name = raw[pos : pos + l1].decode("utf-8", errors="replace")
        pos += l1 + 1
        l2 = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        short_name = raw[pos : pos + l2].decode("utf-8", errors="replace")
        pos += l2 + 2
        out.append({"index": idx, "uid": uid, "name": name, "short_name": short_name})
    return out


def _parse_lang_stadiums(raw: bytes, *, limit: int | None = None) -> list[dict[str, Any]]:
    cnt = struct.unpack_from("<I", raw, 8)[0]
    pos = 12
    out: list[dict[str, Any]] = []
    target = cnt if limit is None else min(cnt, limit)
    for idx in range(target):
        uid, l1 = struct.unpack_from("<II", raw, pos)
        pos += 8
        name = raw[pos : pos + l1].decode("utf-8", errors="replace")
        pos += l1
        l2 = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        alt_name = raw[pos : pos + l2].decode("utf-8", errors="replace")
        pos += l2 + 3
        out.append({"index": idx, "uid": uid, "name": name, "alt_name": alt_name})
    return out


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

    c_dir = [s for s in _extract_fmf_directory_strings(c_frames[-1][1]) if s.startswith("table_")]
    client_tables_summary: list[dict[str, Any]] = []
    for idx in range(len(c_frames) - 1):
        raw = c_frames[idx][1]
        cnt = struct.unpack_from("<I", raw, 8)[0] if len(raw) >= 12 else 0
        body_len = max(0, len(raw) - 12)
        rec_size = round(body_len / cnt, 2) if cnt > 0 else 0
        client_tables_summary.append(
            {
                "frame_index": idx,
                "table_name": c_dir[idx] if idx < len(c_dir) else f"frame_{idx}",
                "record_count": cnt,
                "decompressed_bytes": len(raw),
                "bytes_per_record": rec_size,
            }
        )

    nations = _parse_lang_nations(l_frames[0][1])
    competitions = _parse_lang_competitions(l_frames[1][1])
    clubs = _parse_lang_clubs(l_frames[2][1], limit=sample_limit)
    cities = _parse_lang_cities_and_coords(l_frames[3][1], c_frames[2][1], limit=sample_limit)
    injuries = _parse_lang_injuries(l_frames[5][1])
    awards = _parse_lang_awards(l_frames[6][1], limit=sample_limit)
    stadiums = _parse_lang_stadiums(l_frames[7][1], limit=sample_limit)
    stage_names = _parse_lang_stage_names(l_frames[8][1])
    media_sources = _parse_lang_media_sources(l_frames[11][1])
    local_regions = _parse_lang_local_regions(l_frames[12][1])
    derbies = _parse_lang_derbies(l_frames[13][1])
    agreements = _parse_lang_agreements(l_frames[14][1])

    # Specific verified Turkish & major European cities showcase from client_db.dat + lang_update_db.dat
    full_cities_showcase: list[dict[str, Any]] = []
    full_cities_all = _parse_lang_cities_and_coords(l_frames[3][1], c_frames[2][1], limit=None)
    for target_cid in (7998, 8002, 8008, 1280, 1295, 1955):
        if 0 <= target_cid < len(full_cities_all):
            full_cities_showcase.append(full_cities_all[target_cid])

    return {
        "available": True,
        "source": "shared/data/database/db/2620/2620_fm/ (client_db.dat, lang_update_db.dat, server_db.dat)",
        "client_db_frames_count": len(c_frames) - 1,
        "server_db_frames_count": max(0, len(s_frames) - 1),
        "lang_update_db_frames_count": len(l_frames) - 1,
        "client_db_tables": client_tables_summary,
        "counts": {
            "nations": len(nations),
            "competitions": len(competitions),
            "clubs": struct.unpack_from("<I", l_frames[2][1], 8)[0],
            "cities_with_coords": len(full_cities_all),
            "injuries": len(injuries),
            "awards": struct.unpack_from("<I", l_frames[6][1], 8)[0],
            "stadiums": struct.unpack_from("<I", l_frames[7][1], 8)[0],
            "stage_names": len(stage_names),
            "media_sources": len(media_sources),
            "local_regions": len(local_regions),
            "derbies": len(derbies),
            "international_agreements": len(agreements),
        },
        "cities_coord_showcase": full_cities_showcase,
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
    and `simatchshared.fmf` (Frame #74 — 135 newgen appearance demographic probability rules)."""
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
    if sh_fmf.exists():
        sh_frames = extract_fmf_frames(sh_fmf)
        for fidx in (74, 73, 75):
            if fidx < len(sh_frames) - 1:
                try:
                    obj, _ = parse_jsb(sh_frames[fidx][1], 0)
                    arr = _as_jsb_array(obj)
                    if arr:
                        newgen_demographics = {
                            "frame_index": fidx,
                            "rules_count": len(arr),
                            "rules": arr,
                        }
                        break
                except Exception:
                    continue

    return {
        "available": bool(training_schedules or newgen_demographics),
        "training_schedules": training_schedules,
        "newgen_demographics": newgen_demographics,
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
# MASTER AGGREGATOR FOR ALL 8 REVERSE-ENGINEERED GAME-FILE SYSTEMS
# ==============================================================================
def extract_all_game_files_summary(
    fm_install_dir: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Run all 8 FM26 Game-File Reverse-Engineering Extractors and return a unified summary."""
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

    return {
        "1_qme_statistical_distributions": {
            "total_distributions": qme.get("distributions_total_count", 0),
            "attribute_combination_weights": qme.get("attribute_combination_weights_count", 0),
            "distribution_types": qme.get("distribution_types", {}),
            "sample": qme.get("distributions", []),
        },
        "2_match_momentum_spatial_engine": {
            "total_spatial_rules": momentum.get("total_spatial_rules", 0),
            "event_types": momentum.get("event_types", []),
            "rules_by_event": momentum.get("rules_by_event", {}),
        },
        "3_oop_2d_pitch_proximity_grid": {
            "total_position_role_entries": oop_grid.get("total_position_role_entries", 0),
            "total_spatial_zone_couples": oop_grid.get("total_spatial_zone_couples", 0),
            "unique_position_codes": oop_grid.get("unique_position_codes", []),
            "unique_role_codes": oop_grid.get("unique_role_codes", []),
            "sample_entry": (oop_grid.get("entries") or [None])[0],
        },
        "4_xg_shot_models_and_tactical_presets": {
            "xg_shot_models_count": xg_models.get("models_count", 0),
            "xg_shot_models": xg_models.get("models", {}),
            "tactical_styles_xml_count": styles.get("tactical_styles_xml_count", 0),
            "binary_tactical_presets_count": styles.get("binary_tactical_presets_count", 0),
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
            "counts": master_db.get("counts", {}),
            "cities_coord_showcase": master_db.get("cities_coord_showcase", []),
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
        },
        "8_il2cpp_symbols_and_metadata": {
            "usym_symbol_records_count": il2cpp.get("il2cpp_usym", {}).get("symbol_records_count", 0),
            "global_metadata_version": il2cpp.get("global_metadata", {}).get("metadata_version"),
            "matched_engine_symbols_count": il2cpp.get("global_metadata", {}).get("matched_engine_symbols_count", 0),
            "sample_engine_symbols": il2cpp.get("global_metadata", {}).get("matched_engine_symbols", [])[:25],
        },
    }
