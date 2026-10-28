"""Reading the open vacancies out of the `job_centre` section.

The records are back to back, so nothing is searched for: the count in the header says how
many there are and the walk reads them in order, each sized by the id count it stores itself.
What guards that walk is the section's own size, because the records the header claims have
to end exactly where the section does. That identity is the only check a start shifted by a
whole record fails: every per-record test then passes, on the next record's bytes.

Every field of a record comes from the layout, and the two dates are decoded with the scan's
own date reader, which masks the time-of-day bits these dates carry.
"""

from __future__ import annotations

import functools
import struct
from dataclasses import dataclass
from datetime import date

from fm26save._core._frozen import FrozenMapping
from fm26save._core._layouts import JobCentreLayout, find_layout
from fm26save._core._reader_stats import JobVacancyStats
from fm26save._core._scan import decode_date, decode_time_slot
from fm26save._core.models.jobs import JobVacancy
from fm26save._core.readers._common import (
    JOB_CENTRE_SECTION,
    MISSING_REFERENCE,
    build_gap_padded_struct,
    layout_mismatch,
)
from fm26save._core.readers.clubs import ClubIndex
from fm26save._core.readers.competitions import CompetitionIndex

_UINT32 = struct.Struct("<I")
# What a record's team field holds when it names no team. No save measured stores either, but
# every other reader that ships a stored id reads them this way.
_NO_TEAM = frozenset({0, MISSING_REFERENCE})


@dataclass(frozen=True, slots=True)
class _RecordFields:
    """Everything one record read needs from a `JobCentreLayout`, derived once.

    `head_struct` unpacks from the record start and holds every field in front of the id list,
    and `tail_struct` unpacks from the end of the id list and holds every field after it. Each
    `*_index` gives a value's place in the tuple its struct returns. The advertised date is in
    the head struct only so that the build-time overlap check covers its four bytes; its value
    is read by `decode_date`, which masks the time-of-day bits. The second date is read from
    the struct as one little-endian int, because that is what it ships as: its meaning is
    unsettled, so it is not presented as a date.
    """

    head_struct: struct.Struct
    tail_struct: struct.Struct
    tail_start: int
    team_id_index: int
    role_index: int
    date_12_index: int
    b17_index: int
    competition_index: int
    u20_index: int
    league_position_index: int
    reserved_u8_index: int
    flag_index: int


@functools.cache
def _record_fields(layout: JobCentreLayout) -> _RecordFields:
    """The layout's derived structs, built on first use for each layout.

    Raises:
        ValueError: The tag does not start the record, a field before the id count reaches
            it, a field after it starts inside it, two fields overlap, or a field ends past
            the record's own last byte.
    """
    head_specs = [
        (layout.team_id_offset, "I", "team_id"),
        (layout.role_offset, "B", "role"),
        (layout.advertised_offset, "I", "advertised"),
        (layout.date_12_offset, "I", "date_12"),
    ]
    tail_specs = [
        (layout.b17_offset, "B", "b17"),
        (layout.competition_offset, "H", "competition_id"),
        (layout.u20_offset, "H", "u20"),
        (layout.league_position_offset, "B", "league_position"),
        (layout.reserved_u8_offset, "B", "reserved_u8"),
        (layout.flag_offset, "B", "flag"),
    ]
    lowest_offset = min(offset for offset, _code, _name in head_specs)
    if lowest_offset < len(layout.tag):
        raise ValueError(
            f"the job record tag is {len(layout.tag)} bytes, so no field may start before "
            f"offset {len(layout.tag)}"
        )
    for offset, format_code, field_name in head_specs:
        if offset + struct.calcsize(format_code) > layout.id_count_offset:
            raise ValueError(
                f"field {field_name!r} at offset {offset} reaches the id count at offset "
                f"{layout.id_count_offset}"
            )
    tail_start = layout.id_count_offset + 1
    for offset, format_code, field_name in tail_specs:
        if offset < tail_start:
            raise ValueError(
                f"field {field_name!r} at offset {offset} starts before the id list at offset "
                f"{tail_start}"
            )
        if offset + struct.calcsize(format_code) > layout.record_bytes:
            raise ValueError(
                f"field {field_name!r} at offset {offset} ends past the {layout.record_bytes}-byte "
                "job record"
            )
    head_struct, _head_start, head_index = build_gap_padded_struct(head_specs, start_offset=0)
    tail_struct, _tail_start, tail_index = build_gap_padded_struct(
        tail_specs, start_offset=tail_start
    )
    return _RecordFields(
        head_struct=head_struct,
        tail_struct=tail_struct,
        tail_start=tail_start,
        team_id_index=head_index["team_id"],
        role_index=head_index["role"],
        date_12_index=head_index["date_12"],
        b17_index=tail_index["b17"],
        competition_index=tail_index["competition_id"],
        u20_index=tail_index["u20"],
        league_position_index=tail_index["league_position"],
        reserved_u8_index=tail_index["reserved_u8"],
        flag_index=tail_index["flag"],
    )


def find_job_centre_layout(schema: int | None, build: str) -> JobCentreLayout:
    """Look up the job-centre layout for a `job_centre` schema, falling back to the build."""
    return find_layout(JobCentreLayout, JOB_CENTRE_SECTION, schema, build).layout


def _record_starts(job_centre: bytes, layout: JobCentreLayout, file_name: str) -> list[int]:
    """Where each stored record starts, once the section's size confirms the stored count.

    Raises:
        ReaderCheckError: The section is too short to hold its header, a record runs past its
            end, or the records the header claims do not end exactly where the section does.
    """
    header_end = max(layout.count_offset + _UINT32.size, layout.records_offset)
    section_bytes = len(job_centre)
    if header_end > section_bytes:
        raise layout_mismatch(
            file_name,
            f"the section holds {section_bytes} bytes, too few for its {header_end}-byte header",
            section_name=JOB_CENTRE_SECTION,
        )
    (stored_count,) = _UINT32.unpack_from(job_centre, layout.count_offset)
    shortest_bytes = layout.records_offset + layout.record_bytes * stored_count
    if shortest_bytes > section_bytes:
        raise layout_mismatch(
            file_name,
            f"the header claims {stored_count} records, which need at least {shortest_bytes} "
            f"bytes rather than {section_bytes}",
            section_name=JOB_CENTRE_SECTION,
        )
    starts: list[int] = []
    cursor = layout.records_offset
    for _position in range(stored_count):
        if cursor + layout.record_bytes > section_bytes:
            break
        starts.append(cursor)
        cursor += (
            layout.record_bytes + layout.id_bytes * job_centre[cursor + layout.id_count_offset]
        )
    if len(starts) != stored_count or cursor != section_bytes:
        raise layout_mismatch(
            file_name,
            f"the header claims {stored_count} records, which would end at byte "
            f"{max(cursor, shortest_bytes)} of a section of {section_bytes} bytes",
            section_name=JOB_CENTRE_SECTION,
        )
    return starts


def read_job_vacancies(
    job_centre: bytes,
    club_index: ClubIndex,
    competition_index: CompetitionIndex,
    clock: date,
    layout: JobCentreLayout,
    file_name: str,
) -> tuple[tuple[JobVacancy, ...], JobVacancyStats]:
    """One row per stored record, in stored order, with its club and competition joined.

    A record that fails one of the per-record checks is still returned: those checks judge the
    feed as a whole, so a single odd record is counted and reported rather than dropped, and
    what stops a wrong decode is the section's size identity and the shares those counts feed.

    The competition id is the record's own, so the competition index supplies a name and
    nothing else. The team id is looked up in the team-to-club map rather than the club index:
    a vacancy names a team, and the club is whichever one fields it. A stored 0 or the
    missing-reference word is no team at all and ships as None, as every other reader that
    hands out a stored id reads them.

    Raises:
        ReaderCheckError: The section is too short to hold its header, or the records the
            header claims, each sized by its own id count, do not end where the section does.
    """
    record_starts = _record_starts(job_centre, layout, file_name)
    stored_count = len(record_starts)
    fields = _record_fields(layout)
    unpack_head = fields.head_struct.unpack_from
    unpack_tail = fields.tail_struct.unpack_from
    tag = layout.tag
    tag_bytes = len(tag)
    club_for_team = club_index.team_to_club.get
    club_for_uid = club_index.club_by_uid.get
    competition_for = competition_index.competition_by_id.get
    vacancies: list[JobVacancy] = []
    tagged = 0
    dates_ordered = 0
    advertised_steps = 0
    advertised_ascending_steps = 0
    reserved_zero = 0
    competitions_known = 0
    teams_resolved = 0
    with_competition = 0
    with_league_position = 0
    flagged = 0
    previous_advertised: date | None = None
    for record_offset in record_starts:
        if job_centre[record_offset : record_offset + tag_bytes] == tag:
            tagged += 1
        head_values = unpack_head(job_centre, record_offset)
        id_count = job_centre[record_offset + layout.id_count_offset]
        tail_values = unpack_tail(
            job_centre, record_offset + fields.tail_start + layout.id_bytes * id_count
        )
        advertised_offset = record_offset + layout.advertised_offset
        advertised_date = decode_date(job_centre, advertised_offset)
        advertised_slot = decode_time_slot(job_centre, advertised_offset)
        second_date = decode_date(job_centre, record_offset + layout.date_12_offset)
        if (
            advertised_date is not None
            and advertised_date <= clock
            and second_date is not None
            and second_date >= advertised_date
        ):
            dates_ordered += 1
        if advertised_date is not None:
            if previous_advertised is not None:
                advertised_steps += 1
                if advertised_date >= previous_advertised:
                    advertised_ascending_steps += 1
            previous_advertised = advertised_date
        if tail_values[fields.reserved_u8_index] == 0 and tail_values[fields.b17_index] <= 1:
            reserved_zero += 1

        stored_team_id: int = head_values[fields.team_id_index]
        team_id = None if stored_team_id in _NO_TEAM else stored_team_id
        team_club = None if team_id is None else club_for_team(team_id)
        if team_club is None:
            club_uid: int | None = None
            team_slot: int | None = None
            club_name: str | None = None
        else:
            club_uid, team_slot = team_club
            teams_resolved += 1
            club = club_for_uid(club_uid)
            club_name = None if club is None else club.name

        stored_competition_id: int = tail_values[fields.competition_index]
        competition_id = (
            None if stored_competition_id == layout.no_competition else stored_competition_id
        )
        if competition_id is None or competition_id in competition_index.competition_by_id:
            competitions_known += 1
        if competition_id is not None:
            with_competition += 1
        competition = None if competition_id is None else competition_for(competition_id)
        competition_name = None if competition is None else competition.name

        stored_position: int = tail_values[fields.league_position_index]
        league_position = stored_position or None
        if league_position is not None:
            with_league_position += 1
        flag: int = tail_values[fields.flag_index]
        if flag:
            flagged += 1

        vacancies.append(
            JobVacancy(
                team_id=team_id,
                club_uid=club_uid,
                club_name=club_name,
                team_slot=team_slot,
                advertised_date=advertised_date,
                competition_id=competition_id,
                competition_name=competition_name,
                league_position=league_position,
                unknown=FrozenMapping(
                    {
                        "role": head_values[fields.role_index],
                        "advertised_slot": advertised_slot,
                        "date_12": head_values[fields.date_12_index],
                        "u20": tail_values[fields.u20_index],
                        "b24": flag,
                    }
                ),
            )
        )
    stats = JobVacancyStats(
        records=stored_count,
        tagged=tagged,
        dates_ordered=dates_ordered,
        advertised_steps=advertised_steps,
        advertised_ascending_steps=advertised_ascending_steps,
        reserved_zero=reserved_zero,
        competitions_known=competitions_known,
        teams_resolved=teams_resolved,
        with_competition=with_competition,
        with_league_position=with_league_position,
        flagged=flagged,
    )
    return tuple(vacancies), stats
