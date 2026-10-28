"""Unknown-Field Decoders & Binary Enrichers for FM26 Save Files."""

from __future__ import annotations

import re
import struct
from bisect import bisect_left
from collections import Counter, defaultdict
from typing import Any

from fm26save import _core
from fm26save._core._layouts import PlayerRecordLayout, find_layout
from fm26save._core.readers.facilities import find_facility_layout
from fm26save._core.readers.finances import find_finance_layouts, locate_finance_chain, searched_record
from fm26save._core.readers.staff import (
    find_staff_layouts,
    locate_contracted_header,
    locate_human_header,
    locate_listed_header,
)
from fm26save._core.readers.tactics import find_tactics_layout, walk_tactic_blocks

from fm26save.constants import (
    FM26_NATIONS,
    KNOWN_CITIES,
    RELATION_PAIR_MAP,
    STAFF_BLOCK40_FIELDS,
    STAFF_DEPT_MAP,
    STAFF_ROLE_MAP,
)

_U32 = struct.Struct("<I")
_U16 = struct.Struct("<H")
_STRIP_CLUB_WORDS = re.compile(
    r"\b(FC|CF|SC|SK|FK|NK|AC|AS|CD|UD|SD|AD|SV|BV|VfL|VfB|TSV|FSV|1\.|"
    r"Football|Futbol|Futebol|Club|Clube|Klubu|Kulübü|Spor|Sportif|Sporting|"
    r"Athletic|Atlético|Atletico|United|City|Town|Rovers|Wanderers|Albion|"
    r"A\.Ş\.|A\.S\.|S\.A\.|S\.A\.D\.|Belediyespor|Belediye|İdman|Yurdu|Gençlik)\b",
    re.IGNORECASE,
)


def resolve_nation(nation_id: int | None, lang: str = "tr") -> str:
    """Resolve an FM26 nation_id (1..249) to its human-readable country name."""
    if nation_id is None:
        return ""
    entry = FM26_NATIONS.get(nation_id)
    if entry is None:
        return f"Nation #{nation_id}"
    return entry.get(lang, entry["en"])


def resolve_nation_info(nation_id: int | None) -> dict[str, Any]:
    """Return full nation dictionary (id, tr, en, code, confederation)."""
    if nation_id is None:
        return {"id": None, "tr": "", "en": "", "code": "", "conf": ""}
    entry = FM26_NATIONS.get(nation_id)
    if entry is None:
        return {"id": nation_id, "tr": f"Ülke #{nation_id}", "en": f"Nation #{nation_id}", "code": "UNK", "conf": ""}
    return {"id": nation_id, **entry}


def build_city_map(save: _core.Save) -> dict[int, str]:
    """Build a city_id -> city_name map combining official 58,349 `lang_update_db.dat` cities,
    known cities, and club-name inference fallback."""
    from fm26save.game_files import load_official_city_map

    city_map: dict[int, str] = {}
    official = load_official_city_map()
    if official:
        city_map.update(official)
    city_map.update(KNOWN_CITIES)
    by_city: dict[int, list[str]] = defaultdict(list)
    for club in save.clubs():
        if club.city_id is not None:
            by_city[club.city_id].append(club.short_name or club.name)

    for cid, names in by_city.items():
        if cid in city_map:
            continue
        cleaned_tokens: Counter[str] = Counter()
        for nm in names:
            stripped = _STRIP_CLUB_WORDS.sub(" ", nm)
            words = [w.strip(" .,-()'") for w in stripped.split() if len(w.strip(" .,-()'")) >= 3]
            if words:
                cleaned_tokens[words[0]] += 1
                if len(words) >= 2:
                    cleaned_tokens[f"{words[0]} {words[1]}"] += 1
        if cleaned_tokens:
            best_word, best_count = cleaned_tokens.most_common(1)[0]
            if best_count >= 2 or len(names) == 1:
                city_map[cid] = best_word
            else:
                city_map[cid] = f"{best_word} (#{cid})"
        else:
            city_map[cid] = f"City #{cid}"
    return city_map


def _scale_1_to_20(raw_1_to_100: int) -> int:
    """Convert FM's internal 1..100 attribute byte to the displayed 1..20 rating."""
    return max(1, min(20, (raw_1_to_100 + 2) // 5))


def decode_staff_enriched(save: _core.Save, *, club_uid: int | None = None) -> list[dict[str, Any]]:
    """Decode all staff records with resolved r4 role, department, and 26 hidden block_40 attributes."""
    staff_rows = list(save.staff())
    if club_uid is not None:
        staff_rows = [s for s in staff_rows if s.club_uid == club_uid or s.listed_club_uid == club_uid]

    results: list[dict[str, Any]] = []
    for s in staff_rows:
        uk = dict(s.unknown)
        r4 = uk.get("r4", 0)
        role_info = STAFF_ROLE_MAP.get(
            r4,
            {"tr": f"Teknik Ekip (Kod #{r4})", "en": f"Staff (Code #{r4})", "dept": "Unknown"},
        )
        dept_labels = [STAFF_DEPT_MAP[idx]["tr"] for idx in s.list_indexes if idx in STAFF_DEPT_MAP]
        if not dept_labels:
            dept_labels = [role_info["dept"]]

        role_tr = role_info["tr"]
        role_en = role_info["en"]
        if r4 == 0 and s.list_indexes:
            first_idx = s.list_indexes[0]
            if first_idx == 0:
                role_tr, role_en = "Sağlık Ekibi Üyesi (Doktor/Fizyoterapist)", "Medical Staff"
            elif first_idx == 1:
                role_tr, role_en = "Antrenör / Teknik Ekip", "Coaching Staff"
            elif first_idx == 2:
                role_tr, role_en = "Gözlemci / İşe Alım Ekibi", "Scouting / Recruitment Staff"

        block40_20: dict[str, int] = {}
        block40_raw: dict[str, int] = {}
        if "b40_raw_0" in uk:
            for idx, field_key, _tr_label in STAFF_BLOCK40_FIELDS:
                val_raw = uk.get(f"b40_raw_{idx}", 0)
                block40_raw[field_key] = val_raw
                block40_20[field_key] = uk.get(f"b40_20_{idx}", _scale_1_to_20(val_raw))

        results.append(
            {
                "uid": s.uid,
                "unique_id": s.unique_id,
                "name": s.name,
                "age": s.age,
                "birth_date": str(s.birth_date) if s.birth_date else None,
                "nation_id": s.nation_id,
                "nation_name": resolve_nation(s.nation_id),
                "club_uid": s.club_uid,
                "club_name": s.club_name,
                "role_code_r4": r4,
                "role_tr": role_tr,
                "role_en": role_en,
                "departments": ", ".join(dept_labels),
                "ca": s.ability.current if s.ability else None,
                "pa": s.ability.potential if s.ability else None,
                "wage": s.wage,
                "contract_start": str(s.contract_start) if s.contract_start else None,
                "contract_end": str(s.contract_end) if s.contract_end else None,
                "coaching_and_scouting_20": block40_20,
                "coaching_and_scouting_raw100": block40_raw,
                "role_suitability_codes": {f"r{k}": uk.get(f"r{k}") for k in range(5, 13) if f"r{k}" in uk},
                "unnamed_preferences": {
                    k: v for k, v in uk.items() if k.startswith("preference_slot_")
                },
            }
        )
    return results


def decode_contracts_enriched(
    save: _core.Save, *, club_uid: int | None = None, limit: int = 5000
) -> list[dict[str, Any]]:
    """Decode contracts with resolved money_a (Signing/Loyalty), money_b (Agent Fee), money_c (Bonus), and e12..e39."""
    rows: list[dict[str, Any]] = []
    for c in save.contracts():
        if club_uid is not None and c.club_uid != club_uid:
            continue
        uk = dict(c.unknown)
        rows.append(
            {
                "player_uid": c.player_uid,
                "player_name": c.player_name,
                "club_uid": c.club_uid,
                "club_name": c.club_name,
                "wage_weekly": c.wage,
                "start": str(c.start) if c.start else None,
                "end": str(c.end) if c.end else None,
                "squad_status": c.squad_status.label.name if c.squad_status else None,
                "contract_type": c.kind.label.name if c.kind else None,
                "signing_or_loyalty_fee_money_a": uk.get("money_a", 0),
                "agent_fee_money_b": uk.get("money_b", 0),
                "package_bonus_money_c": uk.get("money_c", 0),
                "reference_or_option_year_e12": uk.get("e12"),
                "promised_squad_status_e38": uk.get("e38"),
                "squad_status_subcode_e37": uk.get("e37"),
                "contract_status_flags_e39": uk.get("e39"),
                "registration_code_e8": uk.get("e8"),
                "clauses_count": len(c.clauses),
                "clauses": [
                    {
                        "kind": cl.kind.label.name if cl.kind and cl.kind.label.value != -1 else f"CODE_{cl.kind.raw}",
                        "value": cl.value,
                        "parameter": cl.parameter,
                    }
                    for cl in c.clauses
                ],
            }
        )
        if len(rows) >= limit:
            break
    return rows


def decode_facilities_enriched(save: _core.Save) -> list[dict[str, Any]]:
    """Decode club facilities and post-finance chain attendance/club block metrics from game_db."""
    info = save.info
    build = info.build
    club_index = save._context.club_index()
    spans = save._context.own_club_record_spans()
    fin_layouts = find_finance_layouts(info.section_schemas.get("game_db"), build)
    fac_layout = find_facility_layout(info.section_schemas.get("game_db"), build)
    city_map = build_city_map(save)

    span_by_uid = {s.club_uid: s for s in spans}
    results: list[dict[str, Any]] = []

    with save._context.section("game_db") as game_db:
        for club in club_index.clubs:
            span = span_by_uid.get(club.uid)
            if span is None or not searched_record(span, fin_layouts.chains):
                continue
            loc = locate_finance_chain(game_db, span, fin_layouts.chains)
            if loc is None:
                continue
            head, row_count, _ = loc
            chain_end = head + fin_layouts.chains.row_bytes * row_count
            if chain_end + 64 > min(span.record_end, len(game_db)):
                continue

            post = game_db[chain_end : min(span.record_end, chain_end + 140)]
            corp_raw = post[fac_layout.offset_after_chain]
            metric_33 = _U32.unpack_from(post, 33)[0]
            att_min_or_season_ticket_41 = _U32.unpack_from(post, 41)[0]
            att_avg_or_capacity_45 = _U32.unpack_from(post, 45)[0]
            tag_49 = post[49]
            tail_byte = post[139] if len(post) >= 140 else None

            results.append(
                {
                    "club_uid": club.uid,
                    "club_name": club.name,
                    "nation_id": club.nation_id,
                    "nation_name": resolve_nation(club.nation_id),
                    "city_id": club.city_id,
                    "city_name": city_map.get(club.city_id, "") if club.city_id else "",
                    "reputation": club.reputation,
                    "corporate_facilities_1_20": corp_raw,
                    "facility_block_tag_49": tag_49,
                    "season_ticket_or_base_attendance_41": att_min_or_season_ticket_41,
                    "expected_or_avg_attendance_45": att_avg_or_capacity_45,
                    "commercial_or_fanbase_index_33": metric_33,
                    "post_chain_byte_139": tail_byte,
                    "finance_months_tracked": row_count,
                }
            )
    return results


def decode_players_enriched_relations(
    save: _core.Save, *, club_uid: int | None = None, limit: int = 250
) -> list[dict[str, Any]]:
    """Decode player hidden tail bytes (RCA, Squad Number) and all PersonBlock relationships."""
    info = save.info
    schemas = info.section_schemas
    build = info.build
    pl_layout = find_layout(PlayerRecordLayout, "game_db", schemas.get("game_db"), build).layout
    staff_layouts = find_staff_layouts(schemas, build)
    pb_lay = staff_layouts.person_blocks
    player_records = save._context.player_records()
    club_index = save._context.club_index()
    city_map = build_city_map(save)

    players_by_uid = {p.uid: p for p in save.players()}
    person_name_by_id: dict[int, str] = {}
    for p in players_by_uid.values():
        if p.name:
            person_name_by_id[p.uid] = p.name
            person_name_by_id[p.uid - 1] = p.name
    for s in save.staff():
        if s.name:
            person_name_by_id[s.uid] = s.name
            person_name_by_id[s.uid - 1] = s.name

    results: list[dict[str, Any]] = []
    with save._context.section("game_db") as game_db:
        offsets = player_records.record_offsets
        uids = player_records.uids
        for idx in range(len(offsets)):
            uid = uids[idx] + 1
            p_obj = players_by_uid.get(uid)
            if p_obj is None:
                continue
            if club_uid is not None and p_obj.club_uid != club_uid:
                continue

            rec_off = offsets[idx]
            w_end = (
                offsets[idx + 1] + pl_layout.pindex_offset
                if idx + 1 < len(offsets)
                else len(game_db)
            )

            # 1. Hidden tail bytes around height_offset (112..130)
            squad_num_raw = game_db[rec_off + 117] if rec_off + 122 <= len(game_db) else 255
            rca_byte = game_db[rec_off + 118] if rec_off + 122 <= len(game_db) else None
            pa_copy_byte = game_db[rec_off + 119] if rec_off + 122 <= len(game_db) else None
            body_type_byte = game_db[rec_off + 123] if rec_off + 124 <= len(game_db) else None

            # 2. All PersonBlock relation entries
            w_start = rec_off + pb_lay.window_start_offset
            pos = w_start + pb_lay.personality_offset_from_birth - 1
            relations_decoded: list[dict[str, Any]] = []
            while pos < min(w_end - 45, len(game_db) - 45):
                if game_db[pos] == 0 and all(1 <= game_db[pos + 1 + k] <= 20 for k in range(8)):
                    b_off = pos - (pb_lay.personality_offset_from_birth - 1)
                    z_start = b_off + pb_lay.date_zero_bytes_offset_from_birth
                    if game_db[z_start : z_start + 7] == b"\x00" * 7:
                        pres = game_db[b_off + pb_lay.relation_present_offset_from_birth]
                        cnt = game_db[b_off + pb_lay.relation_count_offset_from_birth]
                        if pres and 0 < cnt <= 50:
                            ent_at = b_off + pb_lay.relation_entries_offset_from_birth
                            if ent_at + cnt * 16 <= w_end:
                                for r_i in range(cnt):
                                    e_off = ent_at + r_i * 16
                                    ref = _U32.unpack_from(game_db, e_off)[0]
                                    kind = game_db[e_off + 10]
                                    role = game_db[e_off + 11]
                                    qual = game_db[e_off + 12]
                                    sent = game_db[e_off + 15]
                                    if sent != 255:
                                        continue
                                    rel_meta = RELATION_PAIR_MAP.get(
                                        (kind, role),
                                        {
                                            "name": f"relation_{kind}_{role}",
                                            "tr": f"İlişki ({kind}, {role})",
                                            "target": "unknown",
                                        },
                                    )
                                    target_type = rel_meta["target"]
                                    resolved_target = str(ref)
                                    if target_type == "club_index":
                                        c_uid = club_index.uid_by_club_index.get(ref)
                                        c_obj = club_index.club_by_uid.get(c_uid) if c_uid else None
                                        resolved_target = c_obj.name if c_obj else f"ClubIndex #{ref}"
                                    elif target_type == "person_id":
                                        resolved_target = person_name_by_id.get(ref, f"Person #{ref + 1}")
                                    elif target_type == "nation_id":
                                        resolved_target = resolve_nation(ref)
                                    elif target_type == "city_or_region_id":
                                        resolved_target = city_map.get(ref, f"Region/City #{ref}")

                                    relations_decoded.append(
                                        {
                                            "kind": kind,
                                            "role": role,
                                            "type_key": rel_meta["name"],
                                            "type_tr": rel_meta["tr"],
                                            "referenced_id": ref,
                                            "target_name": resolved_target,
                                            "level_or_qualifier": qual,
                                        }
                                    )
                        break
                pos += 1

            fav_clubs = [r["target_name"] for r in relations_decoded if (r["kind"], r["role"]) == (1, 3)]
            dis_clubs = [r["target_name"] for r in relations_decoded if (r["kind"], r["role"]) == (1, 4)]
            fav_people = [r["target_name"] for r in relations_decoded if (r["kind"], r["role"]) == (3, 1)]
            dis_people = [r["target_name"] for r in relations_decoded if (r["kind"], r["role"]) == (3, 2)]

            results.append(
                {
                    "uid": p_obj.uid,
                    "name": p_obj.name,
                    "age": p_obj.age,
                    "nation_id": p_obj.nation_id,
                    "nation_name": resolve_nation(p_obj.nation_id),
                    "second_nations": [resolve_nation(nid) for nid in p_obj.second_nation_ids],
                    "club_uid": p_obj.club_uid,
                    "club_name": p_obj.club_name,
                    "ca": p_obj.ability.current if p_obj.ability else None,
                    "pa": p_obj.ability.potential if p_obj.ability else None,
                    "rca_peak_byte_118": rca_byte,
                    "pa_copy_byte_119": pa_copy_byte,
                    "squad_number": None if squad_num_raw == 255 else squad_num_raw,
                    "body_type_code_123": body_type_byte,
                    "height_cm": p_obj.height_cm,
                    "favoured_clubs": fav_clubs,
                    "disliked_clubs": dis_clubs,
                    "favoured_people": fav_people,
                    "disliked_people": dis_people,
                    "all_relations": relations_decoded,
                }
            )
            if len(results) >= limit:
                break
    return results


def decode_tactics_lineup(save: _core.Save) -> list[dict[str, Any]]:
    """Resolve tactics_man.dat player selectors into Starting XI & Squad Selection."""
    info = save.info
    schemas = info.section_schemas
    build = info.build
    managed = list(save.managed_clubs())
    if not managed:
        return []
    m_club_uid = managed[0].club_uid
    club_index = save._context.club_index()
    m_club = club_index.club_by_uid.get(m_club_uid)
    if m_club is None:
        return []

    player_records = save._context.player_records()
    players_by_uid = {p.uid: p for p in save.players()}
    tac_lay = find_tactics_layout(schemas.get("tactics_man"), build)

    with save._context.section("tactics_man") as tac_raw:
        team_ids = [t.team_id for t in m_club.teams]
        blocks, _counts = walk_tactic_blocks(tac_raw, team_ids, tac_lay, info.file_name)

    out: list[dict[str, Any]] = []
    for block in blocks:
        resolved_players: list[dict[str, Any]] = []
        seen_uids: set[int] = set()
        for slot_idx, sel in enumerate(block.selectors):
            if sel == 0 or sel == 0xFFFFFFFF:
                continue
            pindex = sel - 1
            pos_idx = player_records.position_by_pindex.get(pindex)
            if pos_idx is None:
                continue
            p_uid = player_records.uids[pos_idx] + 1
            if p_uid in seen_uids:
                continue
            seen_uids.add(p_uid)
            p_obj = players_by_uid.get(p_uid)
            resolved_players.append(
                {
                    "order": len(resolved_players) + 1,
                    "raw_selector_slot": slot_idx,
                    "player_uid": p_uid,
                    "player_name": p_obj.name if p_obj else f"Player #{p_uid}",
                    "positions": ", ".join(p_obj.natural_positions) if p_obj else "",
                    "ca": p_obj.ability.current if p_obj and p_obj.ability else None,
                    "pa": p_obj.ability.potential if p_obj and p_obj.ability else None,
                    "role_group": "İlk 11 (Starting XI)" if len(resolved_players) < 11 else (
                        "Yedek / Kadro Seçimi (Bench/Squad)" if len(resolved_players) < 26 else "Duran Top / Görev Havuzu"
                    ),
                }
            )
        out.append(
            {
                "team_id": block.team_id,
                "club_uid": m_club_uid,
                "club_name": m_club.name,
                "tactic_names": [t.name for t in block.tactics],
                "routine_names": [r for r in block.routine_names if r],
                "selected_players_count": len(resolved_players),
                "selected_players": resolved_players,
            }
        )
    return out
