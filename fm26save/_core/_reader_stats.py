"""Counts the readers keep while they decode, for the reader checks in fmsave._checks.

Each record holds plain counts from one reader's existing pass; nothing here reads a save.
"""

from __future__ import annotations

from array import array
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlayerStats:
    """What one decode pass counted over the player records.

    `ages` holds every known age, for the median; `heights_median` is the low median of every
    record's height. Relation counts cover every entry of every validated person block. The
    `*_in_range` and `home_near_current` counts use the ranges in `GateBounds`.
    `outfield_players` counts records rated below `GateBounds.natural_goalkeeper_rating` in
    goal, and `outfield_goalkeeper_block_low` those of them whose raw handling and raw throwing
    are both at most `GateBounds.goalkeeper_block_low_maximum`.
    """

    records: int
    markerless: int
    with_person_block: int
    with_resolved_name: int
    relation_entries: int
    relation_sentinel_ok: int
    second_nation_entries: int
    second_nation_qualifier_ok: int
    handling_above_finishing: int
    outfield_players: int
    outfield_goalkeeper_block_low: int
    with_natural_position: int
    height_in_range: int
    condition_sharpness_in_range: int
    with_valid_join_date: int
    world_not_above_current: int
    home_near_current: int
    with_team: int
    team_resolved: int
    aged_in_range: int
    home_grown_club_refs: int
    home_grown_club_refs_resolved: int
    ages: array[int]
    heights_median: int | None


@dataclass(frozen=True, slots=True)
class ContractStats:
    """What one decode pass counted over the players' contract chain records.

    `without_contract_in_effect` counts players with chain records none of which is the
    contract in effect at the in-game date, because every one starts after it, or an
    explicitly unregistered player has only retained nonterms blocks and no current
    independent fallback end date.
    `date_marked_chain_records` counts the chain records found by a date in their tag slot
    rather than by the tag itself. `tails_without_clause_table` counts parsed tails where no
    clause table is found, and
    `clause_tables` those where one is. `clause_tables_ending_at_tail` counts clause tables whose
    bonus lists and zero trailer end exactly at the tail start. `tail_ends` counts parsed tails
    with an end date, and `tail_ends_past` those whose end date is before the save's in-game
    date.
    """

    players: int
    contracts: int
    players_with_chain: int
    without_contract_in_effect: int
    chain_records: int
    date_marked_chain_records: int
    tails_parsed: int
    tails_without_clause_table: int
    clause_tables: int
    clause_tables_ending_at_tail: int
    head_ok: int
    tail_ends: int
    tail_ends_past: int
    chain_teams_resolved: int


@dataclass(frozen=True, slots=True)
class ClubStats:
    """What the club pass counted: records, team lists, status records and affiliate teams.

    `affiliate_lists` counts club records holding an affiliated-team list, `affiliate_refs`
    every team id those lists hold, and `affiliate_refs_linked` the ids linked to a
    controlling club, which needs an id to name a team of another club that no other club has
    already claimed. `reputation_found` counts the clubs whose status record held a
    reputation inside the layout's range, and `reputations_median` is the low median of those
    reputations.
    """

    records: int
    team_lists_found: int
    status_normal: int
    status_confirmed: int
    affiliate_lists: int
    affiliate_refs: int
    affiliate_refs_linked: int
    reputation_found: int
    reputations_median: int | None


@dataclass(frozen=True, slots=True)
class SuspensionStats:
    """What the suspension search counted over the player region.

    `entries_with_known_scope` counts the entries whose scope code the layout lists, which on
    every save measured is all of them. The two date counts are kept apart because a ban
    covering a whole nation is routinely dated ahead of the in-game date and a ban covering
    one competition never is.
    """

    players: int
    entries: int
    players_with_entries: int
    competition_entries: int
    competition_issued_after_clock: int
    nation_issued_after_clock: int
    entries_with_known_scope: int


@dataclass(frozen=True, slots=True)
class StageStats:
    """What the stage table walk counted.

    `gaps` counts the places the walk had to resynchronise, `steps` the moves from one row to
    the next and `ascending_steps` those that reached a higher stage id.
    `competition_id_rejected` counts rows whose competition id is at or above the layout's
    limit, which is a marker rather than a competition, and `with_competition` the rows left
    holding one. `trailing_sentinel_ok` counts rows whose last word is the missing value, and
    `bytes_after_table` how much of `game_db` follows the table.
    """

    rows: int
    gaps: int
    ascending_steps: int
    steps: int
    with_competition: int
    competition_id_rejected: int
    trailing_sentinel_ok: int
    bytes_after_table: int


@dataclass(frozen=True, slots=True)
class CompetitionStats:
    """What the competition index collected from the stage table.

    `with_database_id` counts the competitions the id-pair records give an editor database id,
    of the `competitions` the stage table names. `database_id_conflicts` counts the competitions
    left without one because another competition claims the same database id. A competition the
    records themselves disagree about reaches neither count: the locator leaves an entity it
    has two database ids for out of the map it hands over.
    """

    competitions: int
    with_database_id: int
    database_id_conflicts: int
    with_name: int


@dataclass(frozen=True, slots=True)
class FixtureStats:
    """What building the fixture calendar counted.

    `span_records` counts calendar candidates after independently owned cache records are
    excluded, including admitted continuations. `cluster_records` counts those in the run
    kept as the calendar, so `clusters` above one means stray copies were dropped.
    `cache_records_excluded` counts strict raw discoveries proved to belong to a separate
    cache; the raw span records remain available for audit.
    `strays_without_a_copy` counts the dropped records the calendar holds no copy of, which is
    what dropping them actually loses: most strays repeat a match the calendar already lists,
    and the rest are the template block every save carries plus, on one save measured, a few
    dozen unplayed matches that predate the calendar.
    `with_stage` counts kept records naming a stage and `stage_resolved` those whose stage the
    stage table holds. `home_team_resolved` and `away_team_resolved` count the team ids a club
    lists. `stub_team_references` counts unresolved sides with validated stub-team objects;
    they remain unnamed and are excluded from the club join population.
    `undated` counts records whose stored date does not decode and
    `bad_kick_off_slots` those whose slot names no time of day. `neutral_venue_votes` counts
    the (club, season) pairs that played enough home matches for a usual ground to be decided.
    `with_stadium` counts kept records storing a ground and `stadium_resolved` those whose
    ground the stadium table holds; the rest store the one value no ordinal ever takes.
    """

    span_records: int
    cluster_records: int
    clusters: int
    strays_without_a_copy: int
    with_stage: int
    stage_resolved: int
    home_team_resolved: int
    away_team_resolved: int
    undated: int
    bad_kick_off_slots: int
    neutral_venue_votes: int
    with_stadium: int
    stadium_resolved: int
    stub_team_references: int = 0
    cache_records_excluded: int = 0


@dataclass(frozen=True, slots=True)
class ResultStats:
    """What joining the stage-keyed results onto the calendar counted.

    `candidates` counts every record the locator judged in the span and in the named sections,
    accepted or not, and `accepted` those that passed the record's own tests and fall inside the
    calendar's dates and the stage table. `joined` counts accepted records that found at least
    one fixture on their date and two team ids, so `ambiguous` and `score_for_unplayed` are both
    parts of it and `unjoined` is the rest of `accepted`.

    The same match is stored about 1.8 times over, so far more records join than there are
    fixtures to fill: a later copy carrying the score already written is ordinary and is counted
    in `joined` like any other. `score_disagreements` counts the copies that carry a *different*
    score for a fixture already filled, which is the one case arrival order must not settle;
    such a fixture keeps no score at all. No save measured has held one.

    `played_fixtures` counts the played matches in the calendar and `scored_fixtures` those that
    came out of the score passes carrying a complete score.

    The `summary_` counters describe the separate owned match summaries, without changing the
    stage-result counts above. `summary_records` and `summary_invalid_scores` count raw rows.
    `summary_lists_found` counts qualified header candidates and `summary_lists_decoded` the
    complete objects whose rows and closing collections decoded.
    The rejected join counters count distinct date/competition/team keys. `summary_unsafe_keys`
    counts keys with conflicting or invalid score pairs, and `summary_stage_conflicts` those
    blocked because stage results already contradicted each other. `summary_scored_fixtures`
    counts newly filled fixtures; existing scores are never overwritten.

    The `packet_` counters describe physically owned calendar packets for selected fixture
    positions. Unsafe packets, unplayed fixtures, existing disagreements and stage/summary
    poisons remain visible; `packet_scored_fixtures` counts only newly filled pairs.
    """

    candidates: int
    accepted: int
    joined: int
    unjoined: int
    ambiguous: int
    score_for_unplayed: int
    score_disagreements: int
    played_fixtures: int
    scored_fixtures: int
    summary_lists_found: int = 0
    summary_lists_decoded: int = 0
    summary_records: int = 0
    summary_invalid_scores: int = 0
    summary_unjoined: int = 0
    summary_ambiguous: int = 0
    summary_for_unplayed: int = 0
    summary_unsafe_keys: int = 0
    summary_existing_disagreements: int = 0
    summary_stage_conflicts: int = 0
    summary_scored_fixtures: int = 0
    packet_score_records: int = 0
    packet_unsafe_scores: int = 0
    packet_for_unplayed: int = 0
    packet_stage_conflicts: int = 0
    packet_summary_conflicts: int = 0
    packet_existing_disagreements: int = 0
    packet_scored_fixtures: int = 0


@dataclass(frozen=True, slots=True)
class TransferWindowStats:
    """What the transfer-window pass counted over the tagged stream.

    `markers` counts the start-date sub-lists the search anchored on, of which only a small
    share open a transfer window at all; `windows` counts the records that decoded into one,
    and `incomplete` those that carried a closing time but whose two date groups were missing
    a value or held one outside its range. A decode that has moved leaves `windows` at zero,
    which fails the count check, and one that has moved only inside the date groups pushes
    records from `windows` into `incomplete`, which fails the date-group check.
    """

    markers: int
    windows: int
    incomplete: int


@dataclass(frozen=True, slots=True)
class LeagueTableStats:
    """What building the live league tables counted.

    `blocks` counts the table blocks left after repeated content was dropped, and
    `duplicate_blocks` those dropped: the span stores each block several times over, the copies
    agreeing in every decoded field and differing only in the 19 undecoded head bytes, and
    about 45% of what the span pass finds is such a copy. `block_candidates` counts every
    candidate the span pass judged, accepted or not.

    `groups` counts the tables the kept blocks fall into, split on the index each block stores
    of its own place in its table, and `groups_resolved` those the calendar vote gave a
    competition, with `blocks_in_resolved_groups` the rows they hold. `team_id_in_range` counts
    rows whose team id is inside the layout's range and `team_resolved` those whose team a club
    lists. `double_round_robin_divisions` counts the tables shaped like a division whose clubs
    all play each other twice, which is what collapses if the grouping ever starts running one
    table into the next, since a merged table holds its clubs twice over.
    `started_calendar_divisions` counts the divisions the fixture calendar shows under way, its
    own form of that shape with every member having played; a division not yet under way keeps
    no table of that shape, so this is the population the division count can be judged against.

    The last three count what the fixture calendar had to say about the slot parity the venues
    are read from. `in_sync_tables` counts the tables with a competition whose every row's
    played count equals that club's played calendar fixtures in exactly one season, which is
    the only population entitled to judge the parity: an out-of-step table is compared against
    the wrong meetings, and over every table instead agreement falls from about 0.998 to about
    0.91. `venue_slots_decided` counts the played slots of those tables whose venue the
    calendar settles by itself, and `venue_slots_agreeing` those the parity then names the same
    way. All three are zero when the layout settles no parity, because nothing is checked then.
    """

    blocks: int
    duplicate_blocks: int
    block_candidates: int
    groups: int
    groups_resolved: int
    blocks_in_resolved_groups: int
    team_id_in_range: int
    team_resolved: int
    double_round_robin_divisions: int
    started_calendar_divisions: int
    in_sync_tables: int
    venue_slots_decided: int
    venue_slots_agreeing: int


@dataclass(frozen=True, slots=True)
class RulesStats:
    """What the competition-rules reader counted over the span's preamble blocks.

    `markers` counts the markers the span pass judged and `blocks` the blocks they yielded.
    Every judged marker yields a block, so the two are equal by construction: the marker count
    is the denominator for the share of blocks that parsed, never a rejection rate.

    `fully_parsed` counts the blocks whose promotion quad was written twice identically **and**
    whose tie-break list, prize list and every round record decoded. That is stricter than
    counting only the lists and the rounds, and it therefore holds on a smaller share of blocks
    than a count that ignores the quad; the check that judges it says which of the two it
    means. `quad_doubled` counts the blocks whose quad was doubled, which is the part of that
    conjunction the four promotion fields depend on. `rows` counts the rows the reader returned.

    The last six count the positional competition link. `blocks_with_run` counts the blocks
    the span stores at least one table block after, before the next preamble block;
    `blocks_linked` those whose run is exactly one league table's set of clubs, which is what
    the link requires, and `blocks_linked_with_competition` those whose table also carries a
    voted competition, which is the only case a row is given one in.

    `linked_rounds` counts the dated rounds those blocks hold and `linked_rounds_in_calendar`
    the ones falling on a date that competition plays a fixture on. That is the corroboration
    the link is judged by, because it separates from its own misalignment: taking the run
    before each block instead of the run after it leaves 0.55 to 0.58 against 0.74 to 0.78 on
    the saves measured. `linked_round_shape` counts the blocks whose number of rounds is what
    a table of that many clubs playing each other once or twice would hold. That one is a
    count and **not** a gate: it scores 0.71 to 0.77 linked against 0.56 to 0.62 misaligned, so
    a floor that both fails the misalignment and keeps its margin has to sit in a window two
    points wide, which is not one to rest a gate on given the saves tested.
    """

    markers: int
    blocks: int
    fully_parsed: int
    quad_doubled: int
    rows: int
    blocks_with_run: int
    blocks_linked: int
    blocks_linked_with_competition: int
    linked_rounds: int
    linked_rounds_in_calendar: int
    linked_round_shape: int


@dataclass(frozen=True, slots=True)
class SeasonStatsStats:
    """What the season-statistics walk counted.

    `records` counts every record the section holds and `records_keyed_to_players` those whose
    key is a player's pindex plus one; `players` counts the player records and
    `players_with_record` those a record belongs to. `records_with_overall` counts records
    holding an overall line and `overall_sums_competitions` those whose overall line's
    appearances, minutes, goals and assists equal the league, cup and continental lines added
    up. `lines` counts every line of every record and `minutes_in_range` the lines whose minutes
    are at most the layout's bound per appearance. `teams_resolved` counts rows whose team a
    club lists, of `rows`. `repeated_keys` counts records whose key an earlier record already
    had, which build no rows; no save measured holds one.
    """

    records: int
    records_keyed_to_players: int
    players: int
    players_with_record: int
    records_with_overall: int
    overall_sums_competitions: int
    lines: int
    minutes_in_range: int
    rows: int
    teams_resolved: int
    repeated_keys: int


@dataclass(frozen=True, slots=True)
class MatchStats:
    """What the per-match player record search counted over the player region.

    `records` counts every accepted record and `with_stats` those the save still holds the
    match's statistics for, which is the denominator of everything those carry.
    `players_with_records`
    counts the players at least one record belongs to, and `unowned` the records that lie before
    the first player's window and so belong to none, which the search region puts out of reach:
    it is zero on every save measured and guards against a record ever being credited to the
    wrong player.

    `competition_in_stage_space` counts records whose competition id the stage table names,
    `minutes_in_range` and `rating_in_range` the records with statistics whose minutes and
    stored rating are at most the layout's maximum, and `stats_in_range` those whose statistics
    are inside every one of those bounds. `opponent_resolved` counts records whose opponent a club
    lists.
    `lists_found` counts recognized nonempty counted histories, and `lists_decoded`
    counts histories whose declared records were walked completely. These counts include
    records outside the output year/identity window. None means structural metadata was
    not supplied by a caller; actual save reads always supply both counts.

    The optional `history_*` counts describe independently located declarations in
    accepted player records. `history_slots` is the accepted player population;
    a null containing property, null history or explicitly empty array proves absence
    for that slot. Unsupported or malformed predecessor fields remain unknown.
    These counts do not depend on whether a present history produces output rows.
    """

    records: int
    with_stats: int
    players_with_records: int
    competition_in_stage_space: int
    minutes_in_range: int
    rating_in_range: int
    stats_in_range: int
    opponent_resolved: int
    unowned: int
    lists_found: int | None = None
    lists_decoded: int | None = None
    history_slots: int | None = None
    history_containing_null: int | None = None
    history_null: int | None = None
    history_empty: int | None = None
    history_nonempty: int | None = None
    history_unknown: int | None = None


@dataclass(frozen=True, slots=True)
class FinanceStats:
    """What one pass over the club records counted for the finance and sponsorship checks.

    `records_searched` counts the club records long enough to hold a chain, which is where the
    search runs at all, and `clubs_with_series` those that held one; most clubs of a save hold
    none. `clubs_with_two_chains` counts the records where a second chain was accepted behind
    the first, which no save measured holds and which means the locator has started accepting
    bytes it should not.

    `rows` counts every month row returned. `net_identity_rows` counts the rows whose net equals
    total income less total expenditure, and `expenditure_split_rows` those whose expenditure
    excluding transfers lies between zero and the total. `balance_steps` counts consecutive row
    pairs inside one club, and `balance_continuous_steps` those where the later balance is the
    earlier one plus the later month's net. A club's first step also counts as continuous when
    the later balance is the earlier one plus both months' nets: on the saves measured, a series
    that begins with the career stores in its oldest row the balance before that month's net,
    and `opening_balance_steps` counts the first steps accepted that way.

    `clubs_with_sponsors` counts the clubs with a series that also hold a sponsor run, and
    `sponsor_rows` the rows those runs hold. `clubs_with_empty_sponsor_lists` counts primary
    lists whose prefix decoded correctly and whose stored count explicitly says zero. `managed_club_exists` says whether the save lists a
    managed club, which is what decides whether the series floor applies at all.
    """

    records_searched: int
    clubs_with_series: int
    clubs_with_two_chains: int
    rows: int
    net_identity_rows: int
    balance_steps: int
    balance_continuous_steps: int
    expenditure_split_rows: int
    clubs_with_sponsors: int
    sponsor_rows: int
    managed_club_exists: bool
    clubs_with_empty_sponsor_lists: int = 0
    opening_balance_steps: int = 0


@dataclass(frozen=True, slots=True)
class FacilityStats:
    """What one pass over the club records counted for the facilities checks.

    `clubs_with_series` counts the clubs whose record holds a finance chain, which are the only
    clubs that carry a facilities rating, `rows` those whose record reaches the rating,
    `in_range` those whose rating lies inside the layout's range, and `unset` those whose
    rating is a zero in an all-zero block, which store no rating rather than one outside the
    range. `managed_club_exists` says whether the save lists a managed club, which is what
    decides whether the count floor applies at all.
    """

    clubs_with_series: int
    rows: int
    in_range: int
    managed_club_exists: bool
    unset: int = 0


@dataclass(frozen=True, slots=True)
class StaffStats:
    """What one pass over the club staff lists and the staff objects counted.

    The club lists: `clubs_checked` counts the club records carrying a team list, which is
    where the staff lists follow, and `clubs_lists_fit` those whose lists all ended inside the
    record with every value in range. `list_values` counts the values those lists hold and
    `player_values_in_lists` the few that turn out to be player pindexes, which are dropped.
    `unset_list_values` counts zero selectors that name no person and are also dropped.
    `listed_persons` counts the distinct people the lists name and `listed_persons_staff` those
    whose header is a staff object with a name block.

    The objects: `staff_objects` counts the staff objects the rows were built from, and
    `ability_signatures`, `preference_slots_in_range`, `codes_in_set` and `block_40_in_range`
    how many of them read as the layout says. `persons` counts the people a row was built for,
    the human manager included, and `persons_with_block` those with a name block.

    Discovery: `discovery_hits` counts the filtered contract-tag hits, `club_record_hits`
    those inside closed club records, and `untailed_hits` those
    whose record has no tail, which no person owns, `unowned_tailed_hits` those with a tail
    whose person has no header in front of them, and `owned_records` the records a person was
    found to own.

    Membership: `listed_pairs` counts the (club, person) pairs the lists give, and
    `listed_pairs_contracted_here` those whose person holds a contract at the listing club or
    at its parent. `merged_affiliate_pairs` counts the pairs an affiliate side listed that
    became a row at its parent instead. `ambiguous_headers` counts the people with more than
    one header that passes the test and `unlocated_persons` those with none; neither gets a
    row. `unresolved_contract_teams` counts the own records whose team no club lists, and
    `repeat_contracts` the people holding more than one record at one club, of which the latest
    to start is taken. `human_found` says whether the save's human manager was located, and
    `rows` and `list_rows` count the rows the two tables returned.
    """

    clubs_checked: int
    clubs_lists_fit: int
    list_values: int
    player_values_in_lists: int
    unset_list_values: int
    listed_persons: int
    listed_persons_staff: int
    staff_objects: int
    ability_signatures: int
    preference_slots_in_range: int
    codes_in_set: int
    block_40_in_range: int
    persons: int
    persons_with_block: int
    discovery_hits: int
    untailed_hits: int
    club_record_hits: int
    unowned_tailed_hits: int
    owned_records: int
    listed_pairs: int
    listed_pairs_contracted_here: int
    merged_affiliate_pairs: int
    ambiguous_headers: int
    unlocated_persons: int
    unresolved_contract_teams: int
    repeat_contracts: int
    human_found: bool
    rows: int
    list_rows: int
    non_staff_tailed_hits: int = 0


@dataclass(frozen=True, slots=True)
class ManagedStats:
    """What the managed-club reader found: human managers, resolved routes (0 or 1) and rows."""

    human_count: int
    route_one_resolved: int
    route_two_resolved: int
    rows: int


@dataclass(frozen=True, slots=True)
class StadiumStats:
    """What walking the stadium table and voting the home grounds counted.

    `table_end_reached` is 1 when the walk stopped on the closing header after the last
    row and 0 when it stopped inside the table, which costs every ground after that point: they
    are missing from the rows returned and from the denominators of every share here, so a
    short walk has to be visible rather than merely lowering a rate.

    `pitch_within_limits` counts the checked rows whose pitch is a plausible length and fits
    inside the ground's own stored minimum and maximum. `owners_set` counts the rows naming an
    owning club and `owners_resolved` those whose club the save lists. `capacity_set` counts
    the rows storing a capacity at all, which is about one in five, and
    `capacity_within_all_seater` every row whose capacity is no larger than its all-seater
    capacity.

    The last three come from the fixture calendar rather than the table:
    `clubs_with_home_ground` counts the clubs the calendar gave a home ground,
    `owning_clubs_with_home_ground` those of them that also own a ground, and
    `owning_clubs_home_ground_owned` those whose home ground is one they own themselves. All
    three are zero on the counts the shared index is enforced on, which are the table's alone.
    """

    rows: int
    table_end_reached: int
    named_rows: int
    owners_set: int
    owners_resolved: int
    capacity_set: int
    capacity_within_all_seater: int
    pitch_checked: int
    pitch_within_limits: int
    clubs_with_home_ground: int
    owning_clubs_with_home_ground: int
    owning_clubs_home_ground_owned: int


@dataclass(frozen=True, slots=True)
class InjuryTypeStats:
    """What reading the injury-type name table out of a per-match entry counted.

    `match_entries` counts the per-match entries the save lists, `entries_with_magic_tried`
    those read looking for the table and `entries_without_magic` those read that are not
    per-match files at all. `table_entries` counts the records of the table that was found,
    which is zero on a save that lists no per-match entry and on one whose entries hold no
    table.
    """

    match_entries: int
    entries_with_magic_tried: int
    entries_without_magic: int
    table_entries: int


@dataclass(frozen=True, slots=True)
class InjuryStats:
    """What the `injury_manager` walk and the joins on its two kinds of row counted.

    `section_bytes` is the decompressed section, which is what says whether these counts come
    from a full save. `window_a_rows`, `window_b_rows` and `list_entries` are all that is kept
    of the five parts of the section no row comes from.

    Of the log rows: `log_lead_ok` counts those whose first byte is the constant the layout
    expects, `log_dates_ok` those whose date decodes and is on or before the in-game date,
    `log_players_resolved` those whose stored person is still a player and
    `log_teams_resolved` those whose team id a club lists. `log_steps` counts the moves from
    one dated row to the next and `log_ascending_steps` those that did not reach an earlier
    date: the save stores the log oldest first, so a step backwards is a decode that has moved
    rather than a quirk of the career. `recent_log_rows` counts the rows from the last
    `recent_log_days` whose player resolves and has a team, and `recent_log_team_matches`
    those storing exactly the team that player is registered with now.

    Of the typed rows: `typed_lead_ok` and `typed_dated` count the same two shapes,
    `typed_dated_near_clock` the dated rows whose date lands within the layout's band either
    side of the in-game date and `typed_dated_over_a_week_old` those more than seven days
    behind it, which is career state and no gate's business,
    `typed_players_resolved` those whose stored person is still a player and
    `typed_types_resolved` those whose injury type the name table holds.
    `type_table_entries` is how many names that table held at all, which is zero on a save
    carrying no per-match file and is what excuses the type check there.
    """

    section_bytes: int
    window_a_rows: int
    window_b_rows: int
    list_entries: tuple[int, ...]
    log_rows: int
    log_lead_ok: int
    log_dates_ok: int
    log_steps: int
    log_ascending_steps: int
    log_players_resolved: int
    log_teams_resolved: int
    recent_log_rows: int
    recent_log_team_matches: int
    typed_rows: int
    typed_lead_ok: int
    typed_dated: int
    typed_dated_near_clock: int
    typed_dated_over_a_week_old: int
    typed_players_resolved: int
    typed_types_resolved: int
    type_table_entries: int


@dataclass(frozen=True, slots=True)
class AffiliateStats:
    """What the affiliate-group walk and its club join counted.

    `groups` counts the groups the walk consumed, `members` every stored club index they hold,
    and `members_resolved` those a club record claims. A section storing no group leaves all
    three at zero, which is why the resolve share is judged only where there is a member.
    """

    groups: int
    members: int
    members_resolved: int


@dataclass(frozen=True, slots=True)
class JobVacancyStats:
    """What reading the job-centre feed counted.

    `records` counts every record the section holds. `tagged` counts those carrying the record
    tag, and `reserved_zero` those whose reserved byte is zero and whose unnamed byte flag at
    `JobCentreLayout.b17_offset` is 0 or 1.

    `dates_ordered` counts records whose advertised date decodes and is on or before the save's
    in-game date **and** whose second date decodes and is on or after the advertised one.
    `advertised_steps` counts the moves from one record with a decodable advertised date to the
    next, and `advertised_ascending_steps` those that did not reach an earlier date: the save
    stores the feed in advertised order, so a step backwards is a decode that has moved rather
    than a quirk of the career.

    `competitions_known` counts records naming no competition or one the stage table holds, and
    `teams_resolved` those whose team id a club lists. Neither carries a gate: team ids are
    dense enough over the feed's range that the second cannot fail, and the first is 1.0 both
    read correctly and with the record start shifted four bytes. Both are reported instead.

    `with_competition` counts records that name a competition at all, `with_league_position`
    those storing a position in its table, and `flagged` those whose 0/1 flag is set.
    """

    records: int
    tagged: int
    dates_ordered: int
    advertised_steps: int
    advertised_ascending_steps: int
    reserved_zero: int
    competitions_known: int
    teams_resolved: int
    with_competition: int
    with_league_position: int
    flagged: int


@dataclass(frozen=True, slots=True)
class TacticStats:
    """What the walk over the manager's team blocks counted.

    `managed_club_exists` is False on a save that lists no human manager with a club, which is
    what decides whether any of these counts is judged at all: there is then no team block to
    read and both tables are empty.

    `club_team_count` is how many teams the managed club fields, `header_blocks` the number of
    blocks the section header claims, `stored_blocks` how many blocks the section holds when
    found by structure (national teams the manager also runs included; 0 when the first is
    not where the header ends) and `blocks_found` how many teams the section stores exactly
    one block for. `stored_club_blocks` independently counts structurally located blocks
    naming club teams, including duplicates, which the team-id locator must cover. Club
    teams without a stored block are excluded from that count. `selector_matches` is whether
    the section header names the same human manager as the `humans` section.

    `selection_selectors` counts every player selector the blocks store, over the selection
    slots, the two selector lists, the single selector, the ten set-piece lists and the eight
    order lists; `selection_selectors_resolved` those a player record names, and
    `selection_selectors_at_club` those of them registered with the managed club. Nothing of
    the selection itself is shipped: these counts are what says the selectors are still being
    read where they sit.

    `tactic_blocks` counts the blocks whose stored count claims a tactic record and
    `tactic_blocks_count_matching` those where every record it claims was found.
    `stored_tactics` counts all records in the managed teams' lists. `preset_tactics` counts
    the subset carrying the preset signature; those are decoded too. `slot_walks_complete`
    counts records whose 22 slot blocks walked and `oop_index_permutations` those whose
    out-of-possession index bytes are a permutation of the slot numbers.

    `routine_blocks` counts the blocks whose routines were searched for,
    `routine_blocks_complete` those whose default runs and counted user groups
    decoded completely, `routines` the rows built from them and `named_routines` those with a
    name.
    """

    managed_club_exists: bool
    club_team_count: int
    header_blocks: int
    stored_blocks: int
    stored_club_blocks: int
    blocks_found: int
    selector_matches: bool
    selection_selectors: int
    selection_selectors_resolved: int
    selection_selectors_at_club: int
    tactic_blocks: int
    tactic_blocks_count_matching: int
    stored_tactics: int
    preset_tactics: int
    slot_walks_complete: int
    oop_index_permutations: int
    routine_blocks: int
    routine_blocks_complete: int
    routines: int
    named_routines: int


@dataclass(frozen=True, slots=True)
class TrainingStats:
    """What the training block walk and its club and player joins counted.

    `managed_club_exists` says whether the save lists a club for its manager at all; without
    one the section holds no calendar and every count below is zero. `club_team_count` is how
    many teams that club fields, its own and those at the clubs it controls, and `blocks` how
    many blocks the walk read: the two are equal on every save measured, and a walk started
    one byte or four bytes late reads none.

    `header_entries` counts the per-person entries of the section header, which are not
    decoded. `weeks` counts every weekly record read, `undated_weeks` those whose stored date
    does not decode, `week_steps` the moves from one week of a block to the next where both
    carry a date, and `seven_day_steps` those that stepped exactly a week.

    `library_entries` counts the saved schedules found after the last block. `groups` counts
    the mentoring groups, `members` their members, `members_resolved` those whose stored
    selector names a player record, and `members_at_club` the resolved members who are
    players of the managed club.
    """

    managed_club_exists: bool
    club_team_count: int
    blocks: int
    header_entries: int
    weeks: int
    week_steps: int
    seven_day_steps: int
    undated_weeks: int
    library_entries: int
    groups: int
    members: int
    members_resolved: int
    members_at_club: int


@dataclass(frozen=True, slots=True)
class SeasonHistoryStats:
    """Archive and ownership counts; sparse imported statistics have no current-season gates."""

    rows: int
    archive_units: int
    unowned_units: int
    lists: int
    unowned_lists: int
    players_without_history: int
    unresolved_teams: int
