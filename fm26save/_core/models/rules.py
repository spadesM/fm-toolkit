"""Competition rules, and the transfer windows the game's rules database carries.

A transfer window is database content rather than career state: the same windows, byte for
byte, are read from every save of one installed database, so they say when a window opens and
closes in a season, not what any one career has done.

The dates are **season-relative**. The save stores a year of 2000 for the season's own start
year and 2001 for the calendar year after it, so a window carries an offset from the season
start rather than a calendar date. Without knowing which season is meant there is no calendar
date to build, so fmsave ships the offset and never a `datetime.date`.
"""

from __future__ import annotations

import datetime
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar

from fm26save._core._status import register_field_statuses


@dataclass(frozen=True, slots=True)
class TransferWindow:
    """One transfer window: when it opens and closes, relative to the season start.

    The window carries no name. The save's rules database does hold description strings, but
    none of them belongs to a window record: on the saves measured only six windows in
    fifty-four have a description ending anywhere near the record, and the rest sit hundreds of
    thousands of bytes away. Attaching the nearest one would put an unrelated label on a
    window, so no label ships and the dates are the whole of what a window says.

    **A save holds more rows than it has distinct windows.** On the saves measured the reader
    returns 54 rows of which 22 are distinct: 17 of those appear twice and 5 appear four times.
    Rows that repeat are equal in every field this record carries, so a caller who wants one
    row per distinct window can drop the repeats and lose nothing it is able to see. A record
    carries a mapping and so is not hashable, which rules out a `set`; equality works as usual,
    so keep the first of each instead::

        distinct_windows: list[TransferWindow] = []
        for window in career_save.transfer_windows():
            if window not in distinct_windows:
                distinct_windows.append(window)

    Why the rules database repeats a window is **not established**. What was measured is that a
    repeat carries no key of its own that fmsave drops: of the 32 repeated records, 26 repeat
    the whole underlying record exactly, tag for tag and value for value, including the id each
    of its two date sub-lists carries, and the other 6 differ only in a description and two
    unidentified tags. Nothing inside a window record tells one copy from another, so whatever
    separates them, if anything does, sits outside the record and this reader does not read it.
    In particular nothing measured here makes them per-competition or per-nation copies; that
    remains a guess. The count is the anchored walk's own, not a decode that counts a record
    twice, and every save measured gives the same 54 rows and the same 22 distinct windows.

    Attributes:
        start_day: Day of the month the window opens, 1 to 31.
        start_month: Month the window opens, 1 to 12.
        start_season_year_offset: Which season year the window opens in: 0 is the season's own
            start year and 1 the calendar year after it. There is no calendar date without a
            season, so this is an offset and never a date.
        end_day: Day of the month the window closes, 1 to 31.
        end_month: Month the window closes, 1 to 12.
        end_season_year_offset: Which season year the window closes in, as
            start_season_year_offset.
        unknown: Numeric fields with no known meaning. "close_time" is the value stored
            against the window's closing-time tag, which looks like an hour and minute on a
            24-hour clock but is not named, because the game's own Rules screen shows no time
            of day to pin it to. "window_type" is a small code the record carries on about two
            windows in five and no displayed label explains (unconfirmed).
    """

    start_day: int
    start_month: int
    start_season_year_offset: int
    end_day: int
    end_month: int
    end_season_year_offset: int
    unknown: Mapping[str, int]

    UNKNOWN_KEYS: ClassVar[tuple[str, ...]] = ("close_time", "window_type")


register_field_statuses(
    TransferWindow,
    verified=(
        "start_day",
        "start_month",
        "start_season_year_offset",
        "end_day",
        "end_month",
        "end_season_year_offset",
    ),
    unconfirmed=("unknown",),
)


class RulesBlockKind(StrEnum):
    """Which structure a competition-rules row was read from.

    Derived by fmsave from where the row came from, never read as a code.

    Every row is `PREAMBLE`. The save's rules database does hold tagged groups of squad and
    financial rules, but nothing readable ties a group to a competition: seven routes were
    measured, including the positional one a preamble row's competition comes from, which does
    not carry over because a group is not stored beside a league table. The groups found carry
    no name either, their content is database content identical on every save of one installed
    database, and no displayed label pins the meaning of the values they hold. So fmsave ships
    none of them rather than shipping guesses, and this enum names no member for them: reading
    them later adds a member and a kind of row, which takes nothing away from a caller.
    """

    PREAMBLE = "preamble"


@dataclass(frozen=True, slots=True)
class RulesRound:
    """One round of a competition's calendar, as the rules block stores it.

    Attributes:
        number: The round's number, counting from one. A round the save does not number
            stores a value that reads here as 256 rather than as a guess (unconfirmed).
        date: The date the round is played on, or None when the stored date does not decode
            (unconfirmed).
        match_count: Unidentified u32 retained unchanged under its legacy field name. It is
            not a dependable fixture count: the same dated row can change from 2 to 10 as
            a career advances, and larger values such as 256 and 8192 occur in complete
            calendars. No bit masks or flag meanings are inferred (unconfirmed).
        unknown: Numeric fields with no known meaning. "kind" and "b5" are the two
            unidentified bytes the round record carries (unconfirmed).
    """

    number: int
    date: datetime.date | None
    match_count: int
    unknown: Mapping[str, int]

    UNKNOWN_KEYS: ClassVar[tuple[str, ...]] = ("kind", "b5")


@dataclass(frozen=True, slots=True)
class CompetitionRules:
    """One competition-rules block: promotion and relegation, prize money and the calendar.

    **The block stores no competition. Its competition comes from where the save keeps it.**
    No field inside a block names one: every `u32` in the 256 bytes before the marker and the
    256 bytes after the block's end was tested against the competition ids the stage table
    holds, over 200 blocks of every save measured, and no offset named a known competition on
    even 90% of blocks while varying from block to block. What does work is position. The span
    alternates rules blocks and league-table blocks, and the run of table blocks stored after
    a block is the table that block's rules govern: on the saves measured about seven blocks in
    ten have such a run, nearly all of those runs are exactly one `league_tables()` table's set
    of clubs, and nearly all of those tables carry a voted competition. A run matching two
    tables at once names neither.

    **That link is corroborated, and is no stronger than the vote behind it.** 0.74 to 0.78 of
    a linked block's dated rounds fall on a date its competition plays a fixture on, against
    0.55 to 0.58 when each block is linked to the run stored *before* it instead, and about
    0.13 against a competition drawn at random for each block.
    On the one division whose Rules screen was read in game, the linked block holds 20 clubs,
    38 rounds and 3 relegation places and its last round is the date that screen gives as the
    season's end. The competition it hands over is itself a vote on the fixture calendar rather
    than a stored value, so these two fields are exactly as strong as
    `LeagueTable.competition_id`: unconfirmed.

    **The other field meanings are weakly sourced.** They come from checks against one
    division's Rules screen in another tool, never re-verified here. The link above does now
    reach the one division that screen describes, and the values of that block match it, but a
    shape that matches a screen is corroboration rather than a field read back, so every field
    here is unconfirmed.

    A block's club count and its points deduction for administration are **not** read: no
    fixed position in the block carries either, so no field ships for them rather than a field
    that is empty on every row. The linked table's own `club_count` is where a club count comes
    from.

    The squad and financial rules the save's rules database holds (a home-grown minimum, a
    maximum squad size, a salary cap and a wage-bill percentage) are **not** read. They live in
    tagged groups that nothing readable ties to a competition -- seven routes were measured,
    including the positional one this record uses, and a group is not stored beside a table --
    and whose content is database content, identical on every save of one installed database.
    So fmsave ships no field for them rather than a field whose meaning rests on another tool's
    guess. Adding them later adds columns and renames nothing.

    Transfer windows are their own table: see `Save.transfer_windows()`.

    Attributes:
        kind: Which structure the row was read from. Every row is PREAMBLE, since the tagged
            rules groups are not read (unconfirmed).
        competition_id: The competition of the league table the save stores right after this
            block, in the stage id space; None where that run is not exactly one table with a
            competition of its own, which is 32% to 45% of rows. Not a stored link: a position
            in the span, resolved through a vote on the fixture calendar (unconfirmed).
        competition_name: Denormalised name of competition_id, which is None unless a name map
            is supplied, because the save stores no competition names (unconfirmed).
        fixtures_per_club: How many matches each club plays, which is the number of rounds the
            block holds; None when no round decoded (unconfirmed).
        promotion_places: How many clubs are promoted, or None when the block's two copies of
            the promotion quad differ (unconfirmed).
        playoff_places: How many clubs enter a promotion play-off, or None as promotion_places
            (unconfirmed).
        relegation_places: How many clubs are relegated, or None as promotion_places
            (unconfirmed).
        prize_money: Prize money by finishing position, in the save's base currency, in
            finishing order. Empty on most blocks: only about one block in eight carries a
            prize list at all (unconfirmed).
        rounds: The competition's calendar, in stored order (unconfirmed).
        unknown: Numeric fields with no known meaning. "promotion_byte2" is the third byte of
            the promotion quad. "tie_break_00" to "tie_break_15" are the tie-break codes the
            block lists, in order, and are absent past the end of that list; no displayed
            label names any of them, so they ship as raw numbers (unconfirmed).
    """

    kind: RulesBlockKind
    competition_id: int | None
    competition_name: str | None
    fixtures_per_club: int | None
    promotion_places: int | None
    playoff_places: int | None
    relegation_places: int | None
    prize_money: tuple[int, ...]
    rounds: tuple[RulesRound, ...]
    unknown: Mapping[str, int]

    UNKNOWN_KEYS: ClassVar[tuple[str, ...]] = ("promotion_byte2",) + tuple(
        f"tie_break_{index:02d}" for index in range(16)
    )


# Nothing this reader returns has been read back off a screen. The Rules screen the field
# meanings come from describes one division; the positional link does now reach that division's
# block, whose clubs, rounds, relegation places and season end all match what the screen shows,
# but a shape that matches a screen is corroboration rather than a field read back. The
# competition the link hands over is a vote on the fixture calendar, so it takes the weaker of
# its inputs and cannot be stronger than that vote. Every field here is unconfirmed.
register_field_statuses(
    RulesRound,
    unconfirmed=("number", "date", "match_count", "unknown"),
)
register_field_statuses(
    CompetitionRules,
    unconfirmed=(
        "kind",
        "competition_id",
        "competition_name",
        "fixtures_per_club",
        "promotion_places",
        "playoff_places",
        "relegation_places",
        "prize_money",
        "rounds",
        "unknown",
    ),
)
