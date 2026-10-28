"""Competitions, collected from the stage table, and the editor database id of each.

The save has no competition table: a competition exists here because stages name it. One
`Competition` is built per distinct competition id the stage table carries, in ascending id.

The name is the one field no save can fill, because the game renders competition names from
its own installed database. A name therefore arrives only from a user-supplied map, and that
map is keyed on the **editor database id** rather than on the competition id, since the
database id is what every source outside the save is keyed on and is the same value on every
save. Recovering it is what this module adds: elsewhere in `game_db` the save writes records
that pair a stage-space entity id with its database id, and those records cover every entity
in that space, so the map they give is restricted to the ids the stage table calls
competitions and is never read as a list of competitions in its own right.

`CompetitionIndex.name_for` is the single lookup every other reader uses to denormalise a
`competition_name`, so no reader repeats the rule.
"""

from __future__ import annotations

import functools
import struct
from collections.abc import Mapping
from dataclasses import dataclass

from fm26save._core._layouts import CompetitionIdPairLayout, find_layout
from fm26save._core._reader_stats import CompetitionStats
from fm26save._core.models.competitions import Competition
from fm26save._core.readers._common import GAME_DB_SECTION, build_gap_padded_struct
from fm26save._core.readers.stages import StageIndex


@dataclass(frozen=True, slots=True, repr=False)
class CompetitionIndex:
    """Every competition the stage table names, with the lookups other readers join through.

    One index is cached and shared by every reader of a save: never mutate its mappings.

    Attributes:
        competitions: Every competition, in ascending competition id.
        competition_by_id: The competition for each competition id.
        database_id_by_competition_id: The editor database id of each competition that has
            one, which is about nine competitions in ten.
        stats: What the index counted, for the competition checks.
    """

    competitions: tuple[Competition, ...]
    competition_by_id: Mapping[int, Competition]
    database_id_by_competition_id: Mapping[int, int]
    stats: CompetitionStats

    def name_for(self, competition_id: int | None) -> str | None:
        """The name of a competition, or None for an unknown id, no id, or an unnamed one."""
        if competition_id is None:
            return None
        competition = self.competition_by_id.get(competition_id)
        return None if competition is None else competition.name

    def __repr__(self) -> str:
        return (
            f"<fmsave CompetitionIndex {len(self.competitions)} competitions, "
            f"{len(self.database_id_by_competition_id)} with a database id>"
        )


@dataclass(frozen=True, slots=True)
class _IdPairScan:
    """Everything the id-pair search needs from a `CompetitionIdPairLayout`, derived once.

    `words_struct` unpacks the three words from the record start. `lowest_offset` and
    `highest_offset_end` bound every byte a candidate reads, so one pair of comparisons keeps
    the whole read inside `game_db`.
    """

    marker: bytes
    record_offset_from_marker: int
    words_struct: struct.Struct
    words_start: int
    entity_id_index: int
    database_id_index: int
    database_id_copy_index: int
    lowest_entity_id: int
    highest_entity_id: int
    lowest_database_id: int
    highest_database_id: int
    constant_bytes: tuple[tuple[int, int], ...]
    lowest_offset: int
    highest_offset_end: int


@functools.cache
def _id_pair_scan(layout: CompetitionIdPairLayout) -> _IdPairScan:
    """The layout's derived struct and bounds, built on first use for each layout.

    Raises:
        ValueError: The marker is empty, the record starts inside the marker, two words
            overlap, or an id range's upper bound is below its lower bound.
    """
    if not layout.marker:
        raise ValueError("the id-pair marker must not be empty")
    if layout.record_offset_from_marker < len(layout.marker):
        raise ValueError(
            f"the record starts {layout.record_offset_from_marker} bytes after the marker "
            f"start, which is inside the {len(layout.marker)}-byte marker"
        )
    words_struct, words_start, index_by_name = build_gap_padded_struct(
        [
            (layout.entity_id_offset, "I", "entity_id"),
            (layout.database_id_offset, "I", "database_id"),
            (layout.database_id_copy_offset, "I", "database_id_copy"),
        ]
    )
    lowest_entity_id, highest_entity_id = layout.entity_id_range
    lowest_database_id, highest_database_id = layout.database_id_range
    if highest_entity_id < lowest_entity_id or highest_database_id < lowest_database_id:
        raise ValueError("an id range's upper bound is below its lower bound")
    constant_offsets = [offset for offset, _value in layout.constant_bytes]
    words_end = words_start + words_struct.size
    return _IdPairScan(
        marker=layout.marker,
        record_offset_from_marker=layout.record_offset_from_marker,
        words_struct=words_struct,
        words_start=words_start,
        entity_id_index=index_by_name["entity_id"],
        database_id_index=index_by_name["database_id"],
        database_id_copy_index=index_by_name["database_id_copy"],
        lowest_entity_id=lowest_entity_id,
        highest_entity_id=highest_entity_id,
        lowest_database_id=lowest_database_id,
        highest_database_id=highest_database_id,
        constant_bytes=layout.constant_bytes,
        lowest_offset=min([words_start, *constant_offsets]),
        highest_offset_end=max([words_end, *(offset + 1 for offset in constant_offsets)]),
    )


def find_competition_id_pair_layout(
    game_db_schema: int | None, build: str
) -> CompetitionIdPairLayout:
    """Look up the id-pair layout for a `game_db` schema, falling back to the build."""
    return find_layout(CompetitionIdPairLayout, GAME_DB_SECTION, game_db_schema, build).layout


def locate_competition_database_ids(
    game_db: bytes, layout: CompetitionIdPairLayout
) -> dict[int, int]:
    """The editor database id of every stage-space entity the save pairs with exactly one.

    The keys are **stage-space entity ids**, of which competitions are a subset: these records
    cover stages and other entities of that space too, so the result holds about three times
    as many entries as a save has competitions. Only `build_competition_index` reads it, and
    only at the ids the stage table calls competitions.

    A record is accepted only when it lies whole inside `game_db`, stores its database id
    twice identically, keeps both ids inside the layout's ranges, and matches every one of the
    layout's constant bytes. An entity that two accepted records disagree about is left out
    altogether, so a caller reads no value rather than one of two guesses.

    Raises:
        ValueError: The layout is inconsistent (see `_id_pair_scan`).
    """
    scan = _id_pair_scan(layout)
    buffer_length = len(game_db)
    marker = scan.marker
    record_offset_from_marker = scan.record_offset_from_marker
    unpack_words = scan.words_struct.unpack_from
    words_start = scan.words_start
    entity_id_index = scan.entity_id_index
    database_id_index = scan.database_id_index
    database_id_copy_index = scan.database_id_copy_index
    lowest_entity_id = scan.lowest_entity_id
    highest_entity_id = scan.highest_entity_id
    lowest_database_id = scan.lowest_database_id
    highest_database_id = scan.highest_database_id
    constant_bytes = scan.constant_bytes
    lowest_offset = scan.lowest_offset
    highest_offset_end = scan.highest_offset_end

    database_ids_by_entity: dict[int, set[int]] = {}
    find_marker = game_db.find
    marker_at = find_marker(marker)
    while marker_at >= 0:
        record_start = marker_at + record_offset_from_marker
        # This marker cannot begin again inside itself, since a match puts its `01` byte where
        # a second match would need a fill byte, so stepping one byte on rather than past the
        # match is what keeps the search right for a marker that can; `bytes.find` runs in C,
        # so the positions it looks at again cost nothing worth saving.
        marker_at = find_marker(marker, marker_at + 1)
        if record_start + lowest_offset < 0 or record_start + highest_offset_end > buffer_length:
            continue
        field_values = unpack_words(game_db, record_start + words_start)
        database_id: int = field_values[database_id_index]
        if database_id != field_values[database_id_copy_index]:
            continue
        entity_id: int = field_values[entity_id_index]
        if not lowest_entity_id <= entity_id <= highest_entity_id:
            continue
        if not lowest_database_id <= database_id <= highest_database_id:
            continue
        if any(game_db[record_start + offset] != value for offset, value in constant_bytes):
            continue
        claimed = database_ids_by_entity.get(entity_id)
        if claimed is None:
            database_ids_by_entity[entity_id] = {database_id}
        else:
            claimed.add(database_id)
    return {
        entity_id: next(iter(database_ids))
        for entity_id, database_ids in database_ids_by_entity.items()
        if len(database_ids) == 1
    }


def build_competition_index(
    stage_index: StageIndex,
    database_ids: Mapping[int, int],
    competition_names: Mapping[int, str],
) -> CompetitionIndex:
    """Collect one competition per distinct competition id in the stage table.

    A database id that two competitions claim names neither of them: both are left without
    one and counted as conflicts, because nothing says which of the two it belongs to and a
    wrong database id would name the wrong competition. An entity the id-pair records
    disagreed about has already been left out of `database_ids` for the same reason.

    Args:
        stage_index: The walked stage table.
        database_ids: The editor database id of each stage-space entity id that has one, as
            `locate_competition_database_ids` gives it. Entities the stage table does not call
            competitions are ignored here.
        competition_names: Names keyed by **database** id, as a user-supplied name map is,
            so a competition is named only once its database id resolves.
    """
    competition_ids = sorted(stage_index.stage_ids_by_competition_id)
    competitions_by_database_id: dict[int, list[int]] = {}
    for competition_id in competition_ids:
        database_id = database_ids.get(competition_id)
        if database_id is not None:
            competitions_by_database_id.setdefault(database_id, []).append(competition_id)
    contested_competition_ids = {
        competition_id
        for claimants in competitions_by_database_id.values()
        if len(claimants) > 1
        for competition_id in claimants
    }

    competitions: list[Competition] = []
    competition_by_id: dict[int, Competition] = {}
    database_id_by_competition_id: dict[int, int] = {}
    named_count = 0
    for competition_id in competition_ids:
        database_id = (
            None
            if competition_id in contested_competition_ids
            else database_ids.get(competition_id)
        )
        name = None if database_id is None else competition_names.get(database_id)
        if database_id is not None:
            database_id_by_competition_id[competition_id] = database_id
        if name is not None:
            named_count += 1
        competition = Competition(
            id=competition_id,
            database_id=database_id,
            name=name,
            stage_ids=stage_index.stage_ids_by_competition_id[competition_id],
        )
        competitions.append(competition)
        competition_by_id[competition_id] = competition
    stats = CompetitionStats(
        competitions=len(competitions),
        with_database_id=len(database_id_by_competition_id),
        database_id_conflicts=len(contested_competition_ids),
        with_name=named_count,
    )
    return CompetitionIndex(
        competitions=tuple(competitions),
        competition_by_id=competition_by_id,
        database_id_by_competition_id=database_id_by_competition_id,
        stats=stats,
    )
