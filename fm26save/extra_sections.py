"""Structured Parsers for the 70+ Extra .dat and .cmt Sections in FM26 Saves."""

from __future__ import annotations

import struct
from typing import Any

from fm26save import _core
from fm26save._core._scan import decode_date

from fm26save.container import FM26Container, extract_length_prefixed_strings
from fm26save.enrichment import resolve_nation

_U32 = struct.Struct("<I")
_U16 = struct.Struct("<H")


def _read_lp_utf8(data: bytes, offset: int, max_len: int = 80) -> tuple[str | None, int]:
    """Read a length-prefixed (<I) UTF-8 string at offset; return (string, next_offset) or (None, -1)."""
    if offset < 0 or offset + 4 > len(data):
        return None, -1
    ln = _U32.unpack_from(data, offset)[0]
    if ln == 0:
        return "", offset + 4
    if ln > max_len or offset + 4 + ln > len(data):
        return None, -1
    raw = data[offset + 4 : offset + 4 + ln]
    try:
        text = raw.decode("utf-8")
        if not all(c.isprintable() or c in "\t\n\r" for c in text):
            return None, -1
        return text, offset + 4 + ln
    except UnicodeDecodeError:
        return None, -1


def parse_hall_of_fame(save: _core.Save, *, limit: int = 500) -> list[dict[str, Any]]:
    """Parse hall_of_fame.dat into structured Hall of Fame manager records, walking each manager's
    variable-length `03 03` trophy-entry array to extract exact major/minor titles and Hall of Fame points."""
    with save._context.section("hall_of_fame") as raw:
        records: list[dict[str, Any]] = []
        pos = 8
        end = len(raw) - 24
        while pos < end and len(records) < limit:
            # Look for 0x01 marker followed by valid first_name (len 2..40), last_name (len 2..40), common_name (len 0..40)
            if raw[pos] == 1:
                fn, next1 = _read_lp_utf8(raw, pos + 1, 45)
                if fn and len(fn) >= 2 and any(c.isalpha() for c in fn):
                    ln, next2 = _read_lp_utf8(raw, next1, 45)
                    if ln and len(ln) >= 2 and any(c.isalpha() for c in ln):
                        cn, next3 = _read_lp_utf8(raw, next2, 45)
                        if cn is not None and next3 + 22 <= len(raw):
                            b_date = decode_date(raw, next3)
                            if b_date is not None and 1900 <= b_date.year <= 2045:
                                manager_uid = struct.unpack_from("<i", raw, next3 + 8)[0]
                                nation_uid = struct.unpack_from("<i", raw, next3 + 13)[0]
                                n_entries = raw[next3 + 17]
                                epos = next3 + 18
                                major_trophies = 0
                                minor_trophies = 0
                                last_win_year: int | None = None
                                valid_walk = True
                                for _ in range(n_entries):
                                    if epos + 24 > len(raw) or raw[epos : epos + 2] != b"\x03\x03":
                                        valid_walk = False
                                        break
                                    wins = _U16.unpack_from(raw, epos + 7)[0]
                                    cat = raw[epos + 21]
                                    ycnt = _U16.unpack_from(raw, epos + 22)[0]
                                    if ycnt > 200 or epos + 24 + 4 * ycnt > len(raw):
                                        valid_walk = False
                                        break
                                    # Categories: 0=Top League, 2=Main Domestic Cup, 4=Club World Cup, 21=UCL/Primary Continental, 22=UEL/Secondary Continental
                                    if cat in (0, 2, 4, 21, 22):
                                        major_trophies += wins
                                    else:
                                        minor_trophies += wins
                                    for y_i in range(ycnt):
                                        w_dt = decode_date(raw, epos + 24 + 4 * y_i)
                                        if w_dt and (last_win_year is None or w_dt.year > last_win_year):
                                            last_win_year = w_dt.year
                                    epos += 24 + 4 * ycnt

                                hof_points = (
                                    _U32.unpack_from(raw, epos)[0]
                                    if (valid_walk and epos + 4 <= len(raw))
                                    else 0
                                )
                                records.append(
                                    {
                                        "offset": pos,
                                        "first_name": fn,
                                        "last_name": ln,
                                        "common_name": cn or None,
                                        "full_name": cn if cn else f"{fn} {ln}",
                                        "birth_date": str(b_date),
                                        "manager_uid": manager_uid if manager_uid > 0 else None,
                                        "nation_uid": nation_uid if nation_uid > 0 else None,
                                        "competition_entries_count": n_entries,
                                        "major_titles_raw": major_trophies,
                                        "minor_titles_raw": minor_trophies,
                                        "total_titles": major_trophies + minor_trophies,
                                        "hall_of_fame_points": hof_points,
                                        "reference_year": last_win_year,
                                    }
                                )
                                pos = epos + 4 if (valid_walk and epos > next3) else next3 + 22
                                continue
            pos += 1
        return records


def parse_board_takeovers(save: _core.Save) -> list[dict[str, Any]]:
    """Scan board_takeover_manager.dat (or board_takeover_man.dat) for investor name blocks & target clubs."""
    club_index = save._context.club_index()
    sec_name = (
        "board_takeover_manager"
        if "board_takeover_manager" in save.info.section_schemas
        else "board_takeover_man"
    )
    with save._context.section(sec_name) as raw:
        records: list[dict[str, Any]] = []
        pos = 8
        end = len(raw) - 20
        while pos < end:
            # Pattern in board_takeover_manager: [8, 1, 11] before first_name, last_name, common_name
            if raw[pos : pos + 3] == b"\x08\x01\x0b":
                fn, next1 = _read_lp_utf8(raw, pos + 3, 45)
                if fn and len(fn) >= 2:
                    ln, next2 = _read_lp_utf8(raw, next1, 45)
                    if ln and len(ln) >= 2:
                        cn, next3 = _read_lp_utf8(raw, next2, 45)
                        if cn is not None:
                            # Look back ~52 bytes for club_index and nation_id
                            club_idx = None
                            nat_id = None
                            if pos >= 52:
                                c_cand = _U32.unpack_from(raw, pos - 51)[0]
                                n_cand = _U32.unpack_from(raw, pos - 47)[0]
                                if 1 <= n_cand <= 250:
                                    nat_id = n_cand
                                    club_idx = c_cand + 1
                            c_uid = club_index.uid_by_club_index.get(club_idx) if club_idx else None
                            c_obj = club_index.club_by_uid.get(c_uid) if c_uid else None
                            records.append(
                                {
                                    "offset": pos,
                                    "investor_first_name": fn,
                                    "investor_last_name": ln,
                                    "investor_full_name": f"{fn} {ln}",
                                    "nation_id": nat_id,
                                    "nation_name": resolve_nation(nat_id),
                                    "club_index": club_idx,
                                    "club_uid": c_uid,
                                    "club_name": c_obj.name if c_obj else None,
                                }
                            )
                            pos = next3
                            continue
            pos += 1
        return records


def parse_shortlists(save: _core.Save, *, limit: int = 500) -> list[dict[str, Any]]:
    """Parse shortlist_man.dat header table of shortlisted/tracked player selectors."""
    player_records = save._context.player_records()
    players_by_uid = {p.uid: p for p in save.players()}

    with save._context.section("shortlist_man") as raw:
        if len(raw) < 16:
            return []
        declared_count = _U32.unpack_from(raw, 8)[0]
        max_items = min(declared_count, (len(raw) - 12) // 8, limit)
        results: list[dict[str, Any]] = []
        for idx in range(max_items):
            off = 12 + idx * 8
            val_a, val_b = struct.unpack_from("<II", raw, off)
            # Either val_a or val_b can be a player selector (pindex + 1)
            resolved_player = None
            metric_val = val_a
            for candidate_sel, other_val in ((val_b, val_a), (val_a, val_b)):
                pindex = candidate_sel - 1
                pos_idx = player_records.position_by_pindex.get(pindex)
                if pos_idx is not None:
                    p_uid = player_records.uids[pos_idx] + 1
                    resolved_player = players_by_uid.get(p_uid)
                    metric_val = other_val
                    break

            results.append(
                {
                    "slot": idx + 1,
                    "raw_word_a": val_a,
                    "raw_word_b": val_b,
                    "score_or_priority": metric_val,
                    "player_uid": resolved_player.uid if resolved_player else None,
                    "player_name": resolved_player.name if resolved_player else None,
                    "club_name": resolved_player.club_name if resolved_player else None,
                    "age": resolved_player.age if resolved_player else None,
                    "positions": ", ".join(resolved_player.natural_positions) if resolved_player else "",
                    "ca": resolved_player.ability.current if resolved_player and resolved_player.ability else None,
                    "pa": resolved_player.ability.potential if resolved_player and resolved_player.ability else None,
                    "transfer_value": resolved_player.transfer_value if resolved_player else None,
                }
            )
        return results


def parse_contract_offers(save: _core.Save) -> list[dict[str, Any]]:
    """Parse contract_man.dat into active contract negotiations/events with resolved players & dates."""
    player_records = save._context.player_records()
    players_by_uid = {p.uid: p for p in save.players()}
    staff_by_pid = {s.uid - 1: s for s in save.staff()}

    with save._context.section("contract_man") as raw:
        if len(raw) < 12:
            return []
        count = _U32.unpack_from(raw, 8)[0]
        max_items = min(count, (len(raw) - 12) // 8, 1000)
        results: list[dict[str, Any]] = []
        for idx in range(max_items):
            off = 12 + idx * 8
            selector = _U32.unpack_from(raw, off)[0]
            dt = decode_date(raw, off + 4)
            pindex = selector - 1
            pos_idx = player_records.position_by_pindex.get(pindex)
            person_kind = "Unknown"
            p_uid = None
            p_name = None
            c_name = None
            wage = None
            if pos_idx is not None:
                p_uid = player_records.uids[pos_idx] + 1
                p_obj = players_by_uid.get(p_uid)
                person_kind = "Player"
                if p_obj:
                    p_name = p_obj.name
                    c_name = p_obj.club_name
                    wage = p_obj.contract.wage if p_obj.contract else None
            elif pindex in staff_by_pid:
                s_obj = staff_by_pid[pindex]
                person_kind = "Staff"
                p_uid = s_obj.uid
                p_name = s_obj.name
                c_name = s_obj.club_name
                wage = s_obj.wage

            results.append(
                {
                    "index": idx + 1,
                    "selector": selector,
                    "person_type": person_kind,
                    "person_uid": p_uid,
                    "person_name": p_name,
                    "club_name": c_name,
                    "current_wage": wage,
                    "event_date": str(dt) if dt else None,
                }
            )
        return results


def parse_agents(save: _core.Save) -> list[dict[str, Any]]:
    """Parse agent_manager.dat for registered player agent person selectors."""
    with save._context.section("agent_manager") as raw:
        if len(raw) < 12:
            return []
        count = _U32.unpack_from(raw, 8)[0]
        max_items = min(count, (len(raw) - 12) // 4, 2000)
        return [
            {
                "agent_slot": i + 1,
                "agent_person_selector": _U32.unpack_from(raw, 12 + i * 4)[0],
            }
            for i in range(max_items)
        ]


def parse_news_items(save: _core.Save, *, max_scan_bytes: int = 1_500_000) -> list[dict[str, Any]]:
    """Extract readable news strings (competitions, stadiums, people, headlines) from news.dat."""
    with save._context.section("news") as raw:
        return extract_length_prefixed_strings(raw, min_len=3, max_len=100, max_scan_bytes=max_scan_bytes, max_results=300)


def analyze_any_section(
    save: _core.Save,
    section_name: str,
    *,
    max_scan_bytes: int = 500_000,
    max_matches: int = 200,
) -> dict[str, Any]:
    """Universal binary inspector for any of the 81 .dat/.cmt sections.

    Extracts header metadata, length-prefixed UTF-8 strings, valid FM dates, and cross-references
    u32 selectors against players and clubs.
    """
    container = FM26Container(save._container_index.path)
    raw = container.read_raw(section_name)
    magic = raw[:6].decode("latin1", errors="replace") if len(raw) >= 6 else ""
    schema = _U16.unpack_from(raw, 6)[0] if len(raw) >= 8 else None
    first_words = list(struct.unpack_from(f"<{min(16, len(raw)//4)}I", raw, 0)) if len(raw) >= 4 else []

    lp_strings = extract_length_prefixed_strings(
        raw, min_len=3, max_len=80, max_scan_bytes=max_scan_bytes, max_results=max_matches
    )

    # Scan for valid dates and player/club selector references in the first 64 KB
    player_records = save._context.player_records()
    players_by_uid = {p.uid: p for p in save.players()}
    dates_found: list[dict[str, Any]] = []
    player_refs: list[dict[str, Any]] = []
    seen_p_uids: set[int] = set()

    scan_lim = min(len(raw) - 4, 65536)
    for off in range(8, scan_lim, 4):
        word = _U32.unpack_from(raw, off)[0]
        if len(dates_found) < 50:
            year = word >> 16
            packed = word & 0xFFFF
            if 1990 <= year <= 2060 and (packed >> 9) == 0 and 1 <= (packed & 0x1FF) <= 366:
                dt = decode_date(raw, off)
                if dt is not None:
                    dates_found.append({"offset": off, "date": str(dt)})

        if len(player_refs) < 100 and 1 <= word <= 16_000_000:
            pindex = word - 1
            pos_idx = player_records.position_by_pindex.get(pindex)
            if pos_idx is not None:
                p_uid = player_records.uids[pos_idx] + 1
                if p_uid not in seen_p_uids:
                    seen_p_uids.add(p_uid)
                    p_obj = players_by_uid.get(p_uid)
                    if p_obj and p_obj.name:
                        player_refs.append(
                            {
                                "offset": off,
                                "selector": word,
                                "player_uid": p_uid,
                                "player_name": p_obj.name,
                                "club_name": p_obj.club_name,
                            }
                        )

    return {
        "section": section_name,
        "decompressed_size": len(raw),
        "header_magic": magic,
        "schema": schema,
        "first_u32_words": first_words,
        "strings_count": len(lp_strings),
        "strings": lp_strings,
        "dates_sample": dates_found,
        "player_references_sample": player_refs,
    }
