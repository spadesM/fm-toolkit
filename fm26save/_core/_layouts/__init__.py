"""Private layout tables: where fields sit inside each region.

Layouts are keyed by (region, schema number) with the game build as a fallback,
because some regions carry no schema number and a build can change a region without
changing its schema. Modules are organised per game year and build.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class GameInfoLayout:
    """Offsets inside `game_info`.

    Offsets named `*_after_db_version` count from the end of the length-prefixed
    database version string, whose length varies. Clock and late-build offsets assume an
    empty filename list; stored filenames shift both by their length-prefixed byte sizes.
    The last build number follows another variable field and is searched for in a window.
    """

    db_version_length_offset: int
    max_db_version_bytes: int
    build_number_offsets_after_db_version: tuple[int, ...]
    game_date_offset_after_db_version: int
    late_build_number_window_after_db_version: tuple[int, int]
    filename_count_offset_after_db_version: int | None = None
    max_filenames: int = 256
    max_filename_bytes: int = 4096


@dataclass(frozen=True, slots=True)
class SaveSummaryLayout:
    """Version detection and the structured date in `save_game_summary`.

    `version_pattern` must match a whole length-prefixed string, so it carries no anchors
    or lookarounds. The date follows the setup and build strings, counted division names,
    the manager header, manager and club strings, and the club uid.
    """

    version_pattern: str
    max_version_bytes: int
    structured_strings_offset: int = 8
    max_setup_string_bytes: int = 65_536
    max_summary_name_bytes: int = 1_024
    max_divisions: int = 4_096
    manager_header_bytes: int = 8
    club_uid_bytes: int = 4


@dataclass(frozen=True, slots=True)
class SummaryStringsLayout:
    """How to pick the length-prefixed strings out of `save_game_summary`.

    Every offset from `strings_start_offset` is tried in order. A string is a u32 byte length
    within `string_length_range` (inclusive) followed by that many bytes of valid UTF-8 with
    no character below `lowest_code_point`. After a string the search continues at its end;
    anywhere else it moves on by one byte.
    """

    strings_start_offset: int
    string_length_range: tuple[int, int]
    lowest_code_point: int


@dataclass(frozen=True, slots=True)
class HumansLayout:
    """Where the human managers are named in `humans`, and how their person header is found.

    The u16 at `human_count_offset` is the number of human managers, and the u32 at
    `first_selector_offset` is the first human manager's person id plus 1. In `game_db`, that
    person's header is the u32 person id followed by the same uid at `person_uid_offset` and at
    `person_uid_copy_offset`, both counted from the person id; a uid of 0 or FFFFFFFF does not
    count.
    """

    human_count_offset: int
    first_selector_offset: int
    person_uid_offset: int
    person_uid_copy_offset: int


# Count checks (such as the name pool minimum) apply only to a decompressed `game_db` at
# least this large; smaller sections come from fragments that cannot meet full-save counts.
FULL_SAVE_MINIMUM_GAME_DB_BYTES = 16 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class NamePoolLayout:
    """How to find and check the three name pools in `game_db`.

    `signature` sits immediately before the first pool's entry count. Its three capacity
    words may scale together up to `max_signature_scale`. The bytes at
    `unchecked_signature_bytes` may hold any value; they are read as zero. Pools have no
    minimum size, since databases differ in size; every entry's id and length are checked
    instead. `max_name_bytes` bounds each name's byte length independently of section bounds;
    it is a parser safety ceiling, not a verified limit on names stored by the game.
    """

    signature: bytes
    max_name_bytes: int
    max_signature_scale: int = 1
    unchecked_signature_bytes: tuple[int, ...] = ()


@dataclass(frozen=True, slots=True)
class ClubRecordLayout:
    """How to recognise club records in `game_db` and where their fields sit.

    A candidate record starts `anchor_offset` bytes before each `anchor` hit, and every other
    offset counts from that start. The nation reference at `nation_copy_offset` may differ
    from both other nation references; only the uid is required to match its copy. Ranges
    are inclusive (lowest, highest). Once a record has been accepted, the scan ends at the
    first candidate `stop_gap_bytes` or more past the last accepted record start; that point
    also ends the last record.
    """

    anchor: bytes
    anchor_offset: int
    club_index_offset: int
    uid_offset: int
    uid_copy_offset: int
    zero_byte_offset: int
    nation_offset: int
    fa_nation_offset: int
    nation_copy_offset: int
    city_offset: int
    long_name_offset: int
    nation_id_range: tuple[int, int]
    max_name_bytes: int
    stop_gap_bytes: int


@dataclass(frozen=True, slots=True)
class TeamListLayout:
    """How to find and parse the team list inside one club record.

    The list starts at the record's first `null_date_triple`. When that does not parse, each
    `float_anchor` hit at least `minimum_float_anchor_record_offset` bytes into the record is
    tried, with the list starting `float_anchor_offset` bytes before it. Offsets count from
    the list start. At `counts_offset` comes a count of `first_entry_bytes`-byte entries that
    each begin with `first_entry_lead_byte`, then a count of `second_entry_bytes`-byte entries
    that each begin with `second_entry_lead_byte`, then `filler_bytes` bytes, then the team
    count and that many u32 team ids. Right after those ids comes the affiliated-team list:
    a count within `affiliate_count_range` and that many u32 team ids, each a team another
    club record stores. Ranges are inclusive (lowest, highest).
    """

    null_date_triple: bytes
    float_anchor: bytes
    float_anchor_offset: int
    minimum_float_anchor_record_offset: int
    counts_offset: int
    first_entry_bytes: int
    first_entry_lead_byte: int
    second_entry_bytes: int
    second_entry_lead_byte: int
    filler_bytes: int
    team_count_range: tuple[int, int]
    team_id_range: tuple[int, int]
    affiliate_count_range: tuple[int, int]


@dataclass(frozen=True, slots=True)
class ClubStatusLayout:
    """Where a club's reputation and last league position sit in the club-status table.

    Offsets count from a hit of the club's stored uid (uid minus 1) written twice, so
    `ordinal_offset` is negative. A hit counts when its ordinal is above the last accepted
    ordinal and below `ordinal_limit`, and its kind byte is `normal_kind` or `stub_kind`. Only
    normal records hold a position and a reputation. Ranges are inclusive (lowest, highest).

    Clubs are searched in club index order from a cursor that moves past each accepted hit.
    Until the first hit is accepted a search runs to the end of `game_db`, and when the first
    `maximum_leading_misses` clubs all miss, the walk stops with no status for any club. After
    that, a club's hit must start at most `search_window_bytes` past the cursor.

    A normal status record is confirmed, for the club checks only, when the u32 at
    `confirmation_offset` (from the hit, so negative) holds the club's stored index (the public
    index minus 1) and the `confirmation_zero_bytes` bytes after it are zero. The confirmation
    never decides which record is accepted.
    """

    ordinal_offset: int
    ordinal_limit: int
    kind_offset: int
    normal_kind: int
    stub_kind: int
    position_offset: int
    reputation_offset: int
    reputation_range: tuple[int, int]
    search_window_bytes: int
    confirmation_offset: int
    confirmation_zero_bytes: int
    maximum_leading_misses: int = 16


@dataclass(frozen=True, slots=True)
class FinanceChainLayout:
    """How to find a club's chain of monthly finance snapshots inside its own record.

    The chain sits inside one club record and is found by its head: a `tag` byte at `h` opens a
    chain when the u32 at `h + count_offset` is a row count inside `count_range` (inclusive),
    the whole chain fits in the record, and every one of those rows carries `tag` at its own
    start, a balance inside `balance_range` and a weekly wage budget and payroll of at most
    `weekly_maximum`. Rows are `row_bytes` long and every field offset counts from a row's
    start. Only records of at least `minimum_record_bytes` are searched at all, which no club
    holding a chain falls below.

    A record holding no such chain may still hold a short one, whose count is inside
    `short_count_range` (inclusive): the series a career keeps on its first days. Those rows
    pass the same tests and must also balance, each with a net equal to its total income less
    its total expenditure and an income and an expenditure excluding transfers each between
    zero and its total, and money must move in at least one of them, since a count this small
    is no evidence on its own.

    Rows run oldest first. `month_lag` is how many months before the save's clock month the
    last row's month is, so a lag of 1 makes the last row the month before the clock's. A clock
    on a month's last day counts as the day after it, since the game has closed that month.
    """

    row_bytes: int
    tag: int
    count_offset: int
    count_range: tuple[int, int]
    short_count_range: tuple[int, int]
    balance_range: tuple[int, int]
    weekly_maximum: int
    balance_offset: int
    transfer_allocated_offset: int
    transfer_remaining_offset: int
    wage_budget_offset: int
    wage_payroll_offset: int
    income_excluding_transfers_offset: int
    net_transfers_offset: int
    wage_bill_offset: int
    net_offset: int
    expenditure_excluding_transfers_offset: int
    total_income_offset: int
    total_expenditure_offset: int
    minimum_record_bytes: int
    month_lag: int


@dataclass(frozen=True, slots=True)
class SponsorChainLayout:
    """A club's primary sponsor list after its monthly finance chain.

    The prefix starts at the finance chain's end: a null-date marker, two dates, and a
    counted collection of fixed-size entries. A fixed-size suffix follows those entries;
    its dates and reserved bytes establish the primary sponsor count's position. An
    explicit zero count is a decoded empty list. Later sponsor-shaped data cannot replace
    an empty or malformed primary list.

    Nonempty lists retain the row tag, flag, date and monetary checks. Row field offsets
    count from each sponsor row; prefix offsets count from the finance chain's end, and
    suffix offsets count from the end of the preceding counted entries.
    """

    prefix_marker: bytes
    prefix_date_offsets: tuple[int, ...]
    prefix_count_offset: int
    prefix_entry_bytes: int
    prefix_entry_reserved_offset: int
    prefix_entry_reserved: bytes
    prefix_suffix_bytes: int
    prefix_suffix_fixed: tuple[tuple[int, bytes], ...]
    prefix_suffix_date_offsets: tuple[int, ...]

    row_bytes: int
    tag: int
    count_offset: int
    type_offset: int
    start_offset: int
    end_offset: int
    flag10_offset: int
    flag10_maximum: int
    total_offset: int
    u15_offset: int
    b17_offset: int
    enum18_offset: int
    b19_offset: int
    annual_offset: int
    value_maximum: int


@dataclass(frozen=True, slots=True)
class FacilityByteLayout:
    """Where a club's corporate facilities rating sits behind its finance chain.

    The rating is the byte at `offset_after_chain` past the end of the club's monthly snapshot
    chain, so it moves with the chain as a career adds months to it and only a club with a
    chain has one at all. `value_range` is the inclusive range the rating takes, which the
    checks count against: it is the range every club with a stored rating reads inside, and the
    bytes either side of the rating read inside it on a few clubs in a hundred.

    `unset_margin` says when a club stores no rating at all: a zero rating whose
    `unset_margin` bytes on either side are all zero too sits in a block the club never
    filled, so it is counted as unset rather than as a rating outside the range. The margin is
    wider than any misalignment the checks guard against, so a read a few bytes off still
    lands next to a real rating and is never taken for an unset one.
    """

    offset_after_chain: int
    value_range: tuple[int, int]
    unset_margin: int


@dataclass(frozen=True, slots=True)
class PersonBlockLayout:
    """How to locate and parse a player's person block inside its record window.

    The block is found by searching the window `[record_offset + window_start_offset,
    record_window_end)` for `personality_count` consecutive bytes in `personality_range`
    (the personality profile) starting at `r`; the birth date sits at
    `birth_date_offset_from_run = r - personality_offset_from_birth`. Offsets suffixed
    `_from_birth` count from the birth date position `p`; offsets suffixed `_from_block_start`
    count from the block start `q`, found by walking backwards from `p`. `relation_pairs`
    maps a `(kind, role)` pair to the person field it fills.

    Every position inside a `relation_entry_bytes`-byte relation entry comes from this layout,
    counted from the entry start: the u32 referenced id at `relation_referenced_offset_in_entry`,
    the kind byte then the role byte at `relation_kind_role_offset_in_entry`, the qualifier byte
    at `relation_qualifier_offset_in_entry` and the sentinel byte at
    `relation_sentinel_offset_in_entry`. The person checks count second-nation entries whose
    qualifier is one of `second_nation_qualifiers` and entries whose sentinel byte equals
    `relation_sentinel_value`.
    """

    window_start_offset: int
    personality_offset_from_birth: int
    personality_count: int
    personality_range: tuple[int, int]
    date_zero_bytes_offset_from_birth: int
    date_zero_bytes_count: int
    legal_name_length_min: int
    legal_name_length_max: int
    name_id_limit: int
    first_name_id_offset_from_block_start: int
    surname_id_offset_from_block_start: int
    common_name_id_offset_from_block_start: int
    legal_name_length_offset_from_block_start: int
    legal_name_offset_from_block_start: int
    trait_bits_offset_from_block_start: int
    nation_id_offset_from_birth: int
    relation_present_offset_from_birth: int
    relation_count_offset_from_birth: int
    relation_entries_offset_from_birth: int
    relation_entry_bytes: int
    second_nation_pair: tuple[int, int]
    home_grown_nation_pair: tuple[int, int]
    home_grown_club_pair: tuple[int, int]
    relation_referenced_offset_in_entry: int
    relation_kind_role_offset_in_entry: int
    relation_qualifier_offset_in_entry: int
    relation_sentinel_offset_in_entry: int
    second_nation_qualifiers: tuple[int, ...]
    relation_sentinel_value: int


@dataclass(frozen=True, slots=True)
class PlayerRecordLayout:
    """How to recognise player records in `game_db` and where their fields sit.

    A marker candidate starts `marker_offset` bytes before each `marker` hit. A completeness
    candidate starts `ratings_offset` bytes before a match of `ratings_count` bytes in
    `rating_range` followed by `attribute_count` bytes in `attribute_range`, searched only in
    the region after the name pools. Every other offset counts from the record start. Ranges
    are inclusive (lowest, highest). `attribute_field_order` names the 52 non-foot attributes
    in the order the bytes at `attributes_offset` store them, skipping the byte at
    `left_foot_index` and at `right_foot_index` (indexes into that 54-byte span, not
    record offsets); `position_codes` names the 15 position ratings in the order stored at
    `ratings_offset`. `decode_extent` is the offset, from the record start, one past the
    last byte a full decode reads: a candidate that passes every acceptance check but whose
    record does not reach `record_offset + decode_extent` is a truncated record, not a
    rejected one.

    Ordinary identity words match. In the allocated namespace starting at
    `allocated_uid_minimum`, a distinct second word also requires one of `player_kinds` at
    `object_kind_offset`, together with every ability, reputation and attribute check.
    The distinct word's meaning is not inferred.

    Edited records may exceed the ordinary ability and attribute maxima up to the optional
    edited maxima. They require matching identity words and the player object kind as well
    as the complete ratings and attributes structure; no values are clamped during decoding.
    """

    marker: bytes
    marker_offset: int
    pindex_offset: int
    uid_offset: int
    uid_copy_offset: int
    allocated_uid_minimum: int
    object_kind_offset: int
    player_kinds: tuple[int, ...]
    home_reputation_offset: int
    current_reputation_offset: int
    world_reputation_offset: int
    current_ability_offset: int
    current_ability_range: tuple[int, int]
    potential_ability_offset: int
    potential_ability_range: tuple[int, int]
    reputation_bucket_offset: int
    reputation_bucket_range: tuple[int, int]
    team_id_offset: int
    ratings_offset: int
    ratings_count: int
    rating_range: tuple[int, int]
    attributes_offset: int
    attribute_count: int
    attribute_range: tuple[int, int]
    left_foot_index: int
    right_foot_index: int
    transfer_value_offset: int
    transfer_value_placeholder: int
    club_join_date_offset: int
    match_sharpness_offset: int
    condition_offset: int
    height_offset: int
    decode_extent: int
    position_codes: tuple[str, ...]
    attribute_field_order: tuple[str, ...]
    edited_ability_maximum: int | None = None
    edited_attribute_maximum: int | None = None


@dataclass(frozen=True, slots=True)
class ContractLayout:
    """How to locate and parse a player's contract chain in `game_db`.

    A chain record for pindex `x` at record start `record_offset` (next record start
    `next_record_offset`, or the end of `game_db` for the last record) is a hit of `tag`
    in `[record_offset + chain_window_start_offset, next_record_offset +
    chain_window_end_offset)` (the end of `game_db` for the last record's window) whose
    `u32` at `selector_offset` equals `x + 1`. Every other chain, tail, clause and head
    offset counts from the tag hit `M` (chain fields, `team_id_offset`, `wage_offset`) or
    from a tail start `E` (`tail_*`) or a clause-table base `base` (`clause_*`, `head_*`).

    The tail is found by trying `E = M - tail_base_offset - tail_step_bytes * event_count`
    for `event_count` from 0 to `tail_max_event_count`, accepted when the byte at
    `E + tail_sentinel_byte_offset` equals `tail_sentinel_byte_value` and the `u32` at
    `E + tail_sentinel_word_offset` equals `tail_sentinel_word_value` (`tail_sentinel_word_offset`
    is always `tail_sentinel_byte_offset + 1`, so the two sentinels form one contiguous
    signature) and the stored event count at `tail_event_count_offset` matches.

    A record whose tail does not parse is still preceded by a tail-shaped block, which is
    where a loan's dates and marker sit. That block is looked for the same way, without
    the sentinel checks and only up to `loan_block_max_event_count` steps back, and is
    accepted when the count byte at `tail_event_count_offset` matches the step and the end
    at `tail_end_offset` is a game date or the missing-date marker; its `tail_e24_offset`
    word marks a loan, and its `tail_printed_start_offset` date is the loan's start. A
    parsed tail stores a printed start date in the same place, which the contract fields
    take from the record itself instead, so the tail struct skips it.

    A clause table holds, from `base + clause_ff_offset`: an 8-byte marker
    (`clause_ff_count` bytes), `clause_zero_count` zero bytes, the clause count byte at
    `base + clause_count_offset`, and that many entries from `base + clause_entries_offset`,
    each `clause_entry_bytes` long. After the last entry come two bonus lists and a trailer:
    a competition count (`clause_competition_count_bytes` wide) and that many
    `clause_competition_item_bytes`-byte items, each starting with
    `clause_competition_item_prefix`; an award flag (`clause_award_flag_bytes` wide) that is 0
    for no award list, or 1 followed by an award count (`clause_award_count_bytes` wide) and
    that many `clause_award_item_bytes`-byte items, each starting with
    `clause_award_item_prefix`; then `clause_trailer_bytes` zero bytes, which end at `E`. With
    both lists empty, the bytes after the entries are `-clause_entries_offset` zero bytes.

    Once a tail is found, the clause table is looked for first by trying
    `base = E - clause_step_bytes * count` for `count` from 0 to `clause_max_count`, accepted
    when the marker is `FF` x `clause_ff_count` and the zero run and the count byte equal to
    `count` follow it: the position of a table whose bonus lists are empty. When that finds
    nothing, the table is taken to be the one nearest `E` whose entries, bonus lists (up to
    `clause_competition_max_count` competition items and `clause_award_max_count` award items)
    and trailer end exactly at `E`, whose zero run and count byte check, and whose marker is
    either `FF` x `clause_ff_count` or a `clause_team_marker_id_bytes`-byte team id that is
    neither all `FF` nor all zero, followed by zero bytes. The head fields are read only when
    the `u16` at
    `base + head_gate_offset` equals `head_gate_value`.

    The fallback reader walks `FF FF FF FF` hits in `[record_offset +
    fallback_start_from_record, limit)`, where `limit` is `max(record_offset +
    fallback_start_from_record, next_record_offset - fallback_end_margin)` (`next_record_offset`
    the end of `game_db` for the last record). For a hit at `i`, `j = i + 8`; when `j +
    fallback_gate_length <= limit` and the `fallback_nonzero_length` bytes at `j +
    fallback_nonzero_offset` are not all zero, an end date sits at `j +
    fallback_end_date_offset` and a start date at `j + fallback_start_date_offset`.
    """

    tag: bytes
    chain_window_start_offset: int
    chain_window_end_offset: int
    selector_offset: int
    start_offset: int
    team_id_offset: int
    wage_offset: int

    tail_base_offset: int
    tail_step_bytes: int
    tail_max_event_count: int
    tail_sentinel_byte_offset: int
    tail_sentinel_byte_value: int
    tail_sentinel_word_offset: int
    tail_sentinel_word_value: int
    tail_e2_offset: int
    tail_e8_offset: int
    tail_e12_offset: int
    tail_e16_offset: int
    tail_e20_offset: int
    tail_e24_offset: int
    tail_end_offset: int
    tail_printed_start_offset: int
    tail_squad_status_offset: int
    tail_e37_offset: int
    tail_e38_offset: int
    tail_e39_offset: int
    tail_event_count_offset: int
    loan_block_max_event_count: int
    nonterms_block_prefix: bytes

    clause_step_bytes: int
    clause_max_count: int
    clause_ff_offset: int
    clause_ff_count: int
    clause_zero_offset: int
    clause_zero_count: int
    clause_count_offset: int
    clause_entries_offset: int
    clause_entry_bytes: int
    clause_value_offset: int
    clause_parameter_offset: int
    clause_kind_offset: int
    clause_team_marker_id_bytes: int
    clause_competition_count_bytes: int
    clause_competition_item_bytes: int
    clause_competition_item_prefix: bytes
    clause_competition_max_count: int
    clause_award_flag_bytes: int
    clause_award_count_bytes: int
    clause_award_item_bytes: int
    clause_award_item_prefix: bytes
    clause_award_max_count: int
    clause_trailer_bytes: int

    head_gate_offset: int
    head_gate_value: int
    head_type_offset: int
    head_money_a_offset: int
    head_money_b_offset: int
    head_money_c_offset: int

    fallback_start_from_record: int
    fallback_end_margin: int
    fallback_nonzero_offset: int
    fallback_nonzero_length: int
    fallback_end_date_offset: int
    fallback_start_date_offset: int
    fallback_gate_length: int


@dataclass(frozen=True, slots=True)
class SuspensionLayout:
    """How to find unserved suspension entries in `game_db` and where their fields sit.

    Every offset counts from an entry's start. An entry sits wherever, for each `(offset,
    value)` pair in `signature`, the byte at that offset equals `value`; the bytes between
    signature bytes may hold anything. One search runs from `owner_back_offset` bytes before
    the first player record's start to the end of `game_db`. An entry belongs to the player
    with the greatest record start `record_offset` for which `record_offset -
    owner_back_offset` is at or before the entry's start; an entry before the first player's
    window belongs to no player. An entry is kept only when the date at `issued_date_offset`
    is a valid game date and the u16 at `scope_id_offset` lies strictly between the
    (lower, upper) values of `scope_id_exclusive_range`.

    The u16 at `scope_id_offset` is **not always a competition id**. The byte at
    `scope_code_offset` says which id space it belongs to: `competition_scope_code` means a
    competition id in the stage id space, and each code in `nation_scope_codes` means a nation
    id. A code in neither list leaves the id unread, because nothing then says what it is.

    The standalone signature remains supported. Additional attached forms require a complete
    parent beginning with `parent_prefix` and a u8 child count. Each child has
    `entry_core_bytes` followed by either `null_suffix` or an attachment extending through
    `linked_entry_bytes`. Attachment offsets count from the child's start; its signature,
    date and flag constrain framing without assigning meanings to its other raw fields.
    """

    signature: tuple[tuple[int, int], ...]
    unknown_e7_offset: int
    issued_date_offset: int
    scope_code_offset: int
    scope_id_offset: int
    owner_back_offset: int
    scope_id_exclusive_range: tuple[int, int]
    competition_scope_code: int
    nation_scope_codes: tuple[int, ...]
    parent_prefix: bytes
    entry_core_bytes: int
    null_suffix: bytes
    linked_entry_bytes: int
    linked_signature: tuple[tuple[int, int], ...]
    linked_date_offset: int
    linked_flag_offset: int
    linked_flag_values: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class MatchCacheLayout:
    """Bounded field geometry preceding an owned nullable match cache.

    These fields describe serialization, not the meanings of the intervening properties.
    The initial offset counts from an independently accepted player's ability field.
    Unknown tags or incomplete fields do not establish an empty cache.
    """

    header_offset: int
    header_suffix_bytes: int
    header_marker_offset: int
    header_marker: bytes
    fixed_row_bytes: int
    fixed_row_marker: bytes
    fixed_row_dates: tuple[int, ...]
    tagged_scalar_bytes: tuple[tuple[int, int], ...]
    tagged_expression_prefix: bytes
    tagged_expression_bytes: int
    tagged_child_bytes: int
    nullable_prefix_bytes: tuple[int, int, int]
    raw_body_bytes: int
    reference_bytes: int
    reference_dates: tuple[int, ...]
    raw_suffix_bytes: int
    attribute_block_bytes: int
    medical_row_bytes: int
    medical_optional_bytes: int
    dated_child_widths: tuple[tuple[int, int], ...]
    dated_child_marker_offset: int
    dated_child_date_offset: int
    dated_child_type_offset: int
    dated_attachment_bytes: int
    nullable_suffix_bytes: tuple[int, int, int, int, int]


@dataclass(frozen=True, slots=True)
class MatchRecordLayout:
    """How to find a player's per-match records in `game_db`, and where their fields sit.

    A parent marker and byte count enclose contiguous team lists. All declared children
    must frame completely before any rows are emitted. Record offsets count from the lead
    byte. A child list starts with one of the observed
    `list_markers`, followed by its team word and declared record count inside
    `list_header_bytes`. The meaning of each marker's first byte remains unconfirmed.
    Every declared record must be walked within its player's ownership window before
    output is accepted. `years_before_clock`, `years_after_clock`, `team_id_range` and
    `competition_id_range` then bound emitted records; they do not change the list's stride.

    A record whose body flag is zero is `header_bytes` long; one with a body is
    `record_bytes` long, including trailing bytes whose field meanings remain unknown.
    Body fields are not read from records without a body. Statistics outside their sanity
    bounds remain visible for validation rather than being used to select record framing.

    Ownership windows start `owner_back_offset` before each player's record offset and
    end at the next window. Both the counted-list header and its complete body must fit.

    `position_bits` names the bits of the u16 at `position_mask_offset`, as `(bit index, enum
    member name)` pairs. The mask belongs to this structure alone and shares its meanings with
    no other: a bit named here says nothing about the same bit anywhere else. Every bit the
    pairs leave out stays unnamed and keeps its raw mask.

    `maximum_minutes`, `maximum_rating` and `maximum_goals` bound what fmsave's own sanity flag
    accepts as a sound body, and `rating_scale` is what the stored rating is divided by.
    """

    lead_byte_offset: int
    lead_byte_value: int
    date_offset: int
    opponent_team_id_offset: int
    competition_id_offset: int
    tag_offset: int
    body_flag_offset: int
    position_mask_offset: int
    role_code_offset: int
    goals_offset: int
    assists_offset: int
    left_at_offset: int
    minutes_offset: int
    rating_offset: int
    passes_attempted_offset: int
    passes_completed_offset: int
    header_bytes: int
    record_bytes: int
    owner_back_offset: int
    team_id_range: tuple[int, int]
    competition_id_range: tuple[int, int]
    years_before_clock: int
    years_after_clock: int
    maximum_minutes: int
    maximum_rating: int
    maximum_goals: int
    rating_scale: int
    position_bits: tuple[tuple[int, str], ...]
    list_markers: tuple[bytes, ...]
    list_header_bytes: int
    list_team_id_offset: int
    list_count_offset: int
    parent_marker: bytes
    parent_header_bytes: int
    parent_count_offset: int
    cache_layout: MatchCacheLayout | None = None


@dataclass(frozen=True, slots=True)
class MatchSummaryLayout:
    """Complete counted match summaries inside a distinct person-object kind.

    Header offsets start at the object's index word. Row offsets start at its lead byte.
    The object kind and the remaining header fields' meanings are unconfirmed. Two counted
    word arrays and a null or valid packed date close the summary collection. Goal sanity
    never determines its framing; invalid scores block enrichment of their fixture key.
    """

    header_bytes: int
    uid_offset: int
    uid_copy_offset: int
    kind_offset: int
    kind_value: int
    header_word_offset: int
    header_word_values: tuple[int, ...]
    ability_offsets: tuple[int, ...]
    ability_range: tuple[int, int]
    attributes_offset: int
    attributes_count: int
    attributes_range: tuple[int, int]
    flag_offsets: tuple[int, ...]
    count_offset: int
    record_bytes: int
    lead_byte_offset: int
    lead_byte_value: int
    date_offset: int
    competition_id_offset: int
    home_goals_offset: int
    away_goals_offset: int
    home_team_id_offset: int
    away_team_id_offset: int
    goals_maximum: int
    trailing_array_count: int
    null_date_bytes: bytes


# Count and distribution checks on the unnamed span apply only to a span at least this
# large; a smaller span comes from a fragment that cannot meet full-save counts.
FULL_SAVE_MINIMUM_SPAN_BYTES = 16 * 1024 * 1024

# How many bytes of the previous window each span window keeps in front of its frame, so a
# record lying across a frame boundary is whole in one window. Far above the longest record
# the span holds: a fixture is 68 bytes and the largest league-table block 1,447.
SPAN_CARRY_OVER_BYTES = 65_536


@dataclass(frozen=True, slots=True)
class FixtureCalendarLayout:
    """How to recognise fixture calendar records in the unnamed span, and where fields sit.

    Every offset counts from the record start, which is where the home team id sits, so the
    offsets of the locator byte, the stage id and the stadium ordinal are negative. Records
    are found by a pattern built from this layout and the save's in-game date: the first
    sentinel byte, the bytes up to the second sentinel byte, then the bytes up to the low
    byte of the kick-off year, which must be one of the years from `years_before_clock`
    before the in-game year to `years_after_clock` after it, and then that year's high byte.

    A candidate is accepted when the whole record lies inside the window, the byte at
    `marker_byte_offset` equals `marker_byte_value`, every `(offset, value)` pair in
    `sentinel_offsets` holds, and both team ids lie inside the inclusive `team_id_range`.
    The stadium ordinal is stored as the ordinal plus one.

    `played_offset` is a legacy locator offset: it follows the 67-byte core and belongs
    to the next fixture's optional-result prefix, or the following collection after a
    terminal core. Standalone anchors retain that fallback reading. Complete sibling
    paths instead associate each preceding 0/1 prefix with its own fixture; a present
    result has the counted `secondary_` header and payload before that fixture's core.

    `round_index_none_value`, `kick_off_slot_offset`, `kick_off_slot_minutes`,
    `cluster_gap_bytes` and `neutral_venue_minimum_home_fixtures` are for the fixtures reader
    rather than the span pass: a kick-off time is `(stored slot + kick_off_slot_offset) *
    kick_off_slot_minutes` minutes into the day, a round index of `round_index_none_value`
    means no round, a gap of `cluster_gap_bytes` or more between records separates the
    calendar from a stray copy, and a club needs `neutral_venue_minimum_home_fixtures` home
    matches in a season before the ground it used most counts as its usual one.
    """

    record_bytes: int
    marker_byte_offset: int
    marker_byte_value: int
    sentinel_offsets: tuple[tuple[int, int], ...]
    stage_id_offset: int
    stadium_ordinal_offset: int
    home_team_id_offset: int
    away_team_id_offset: int
    kick_off_date_offset: int
    date2_offset: int
    season_start_year_offset: int
    match_record_id_offset: int
    phase_offset: int
    leg_offset: int
    round_index_offset: int
    r39_42_offset: int
    match_rules_template_offset: int
    match_rules_template_bytes: int
    r47_54_offset: int
    played_offset: int
    team_id_range: tuple[int, int]
    years_before_clock: int
    years_after_clock: int
    round_index_none_value: int
    kick_off_slot_offset: int
    kick_off_slot_minutes: int
    cluster_gap_bytes: int
    neutral_venue_minimum_home_fixtures: int
    secondary_marker: int
    secondary_header_bytes: int
    secondary_count_offset: int
    secondary_item_bytes: int
    secondary_home_goals_offset: int
    secondary_away_goals_offset: int
    secondary_optional_home_goals_offset: int
    secondary_optional_away_goals_offset: int
    secondary_missing_goals: int
    secondary_goals_maximum: int
    cache_vector_count_offset: int
    cache_vector_count_copy_offsets: tuple[int, ...]
    cache_vector_constant_offset: int
    cache_vector_constant: bytes
    cache_vector_entries_offset: int
    cache_dates_prefix: bytes
    cache_vector_tail_bytes: int
    cache_primary_bytes: int
    cache_primary_suffix_offset: int
    cache_primary_suffix: bytes
    cache_next_prefix: bytes
    cache_next_header_bytes: int
    cache_next_tag_offset: int
    cache_next_tag_bytes: int
    cache_next_constant_offset: int
    cache_next_constant: bytes


@dataclass(frozen=True, slots=True)
class LeagueTableLayout:
    """How to recognise league-table blocks in the unnamed span, and where fields sit.

    A block is found by its `aggregate_count` aggregate rows, each `row_bytes` long and each
    keyed `unplayed_key`; the first of them is the block head, and every offset counts from
    there, so `team_id_offset` and `head_bytes_offset` are negative. After the aggregates
    come the u16 at `rounds_per_venue_offset` and, at `matches_offset`, twice that many
    match rows, whose venue alternates with the slot's parity.

    Each row holds a u32 key, the played count twice, the won, drawn and lost counts, a zero
    byte, the u16 goals for, goals against and points, and a flag byte. On an aggregate row,
    and in a match slot that was never played, the key is `unplayed_key`; otherwise it is the
    opponent's first-team id.

    A candidate is accepted when the whole block lies inside the window, `rounds_per_venue`
    lies inside the inclusive `rounds_per_venue_range`, every aggregate row has both played
    counts equal and played equal to won plus drawn plus lost, the home and away rows'
    played counts add up to the total row's, so do the two half rows', and the total row has
    played at least one match. `team_id_range`, `stored_index_head_byte`,
    `division_club_range` and `home_slot_parity` are for the league-tables reader rather than
    the span pass. The byte at `stored_index_head_byte` inside the head blob is the block's
    own place in its table, running 0 to n-1 and starting again at the next table, so it is
    what separates two tables; a group of `division_club_range` clubs each playing the others
    twice is a division.

    `home_slot_parity` is the slot parity played at home, and None when no parity is settled,
    in which case the reader returns None for every venue rather than guessing one and checks
    nothing. The save alternates venue with the slot's parity and never says which parity is
    home; the fixture calendar is what says it, because a calendar record stores its home team
    outright. On the tables whose rows account for exactly one season of that calendar, the
    slots the calendar can decide by itself agree with the even slot being home on at least
    99.76% of them on every save measured, and with the odd slot being home on at most 0.24%.
    """

    row_bytes: int
    aggregate_count: int
    team_id_offset: int
    head_bytes_offset: int
    head_bytes_count: int
    rounds_per_venue_offset: int
    matches_offset: int
    rounds_per_venue_range: tuple[int, int]
    key_offset: int
    played_offset: int
    played_copy_offset: int
    won_offset: int
    drawn_offset: int
    lost_offset: int
    zero_offset: int
    goals_for_offset: int
    goals_against_offset: int
    points_offset: int
    flag_offset: int
    unplayed_key: int
    team_id_range: tuple[int, int]
    stored_index_head_byte: int
    division_club_range: tuple[int, int]
    home_slot_parity: int | None


@dataclass(frozen=True, slots=True)
class RulesPreambleLayout:
    """How to read a competition-rules preamble block in the unnamed span.

    A block is found by `marker`. The promotion quad sits at `promotion_quad_offset` and is
    `promotion_quad_bytes` long, written twice back to back and ending where the marker
    starts: promotion places, playoff places, an unidentified byte, relegation places. When
    the two copies differ, none of the four is read.

    The body starts `body_offset` bytes after the marker and holds, in order, a u32
    tie-break count of at most `tie_break_count_max` and that many bytes, a u32 prize count
    of at most `prize_count_max` and that many u32 prizes, and a u32 round count of at least
    one and at most `round_count_max`. The round records follow, each `round_record_bytes`
    long, anchored on the first of the `round_anchor_search_bytes` offsets after the count
    whose date decodes; the first record's `round_kind_offset` byte is the count's own high
    byte, which is always zero.

    Inside a round record the unidentified `kind` byte sits at `round_kind_offset`, the date
    at `round_date_offset`, a second unidentified byte at `round_b5_offset`, the round
    number minus one (or `round_no_number_value` for a round the save does not number) at
    `round_number_offset`, and an unidentified u32 at `round_match_count_offset`. The
    legacy walk limits that word to `round_match_count_max`. A complete indexed calendar
    instead requires `round_indexed_kind_value` at `round_kind_offset` and the zero-based
    parent-list ordinal at `round_ordinal_offset` on every record; it retains the word
    unchanged without interpreting it as a count.

    Between round records the save writes moved or reserved matches as blocks of
    `moved_match_bytes` bytes, recognised by `moved_match_sentinel_value` at
    `moved_match_sentinel_offset` and `moved_match_tail` at `moved_match_tail_offset`; up to
    `moved_match_max_per_round` of them follow one round. Stepping over them is what keeps
    the round records in step: on the corpus a plain stride reads about 65% of blocks
    correctly and this stride about 96%. A second interstitial shape carries
    `round_interstitial_tag_value` at `round_interstitial_tag_offset` and the same tail.
    Its contents are unidentified; this shape is accepted only when the bounded walk
    completes the entire declared calendar. Date, calendar-size and interstitial bounds
    apply to every walk.
    """

    marker: bytes
    promotion_quad_offset: int
    promotion_quad_bytes: int
    body_offset: int
    tie_break_count_max: int
    prize_count_max: int
    round_count_max: int
    round_record_bytes: int
    round_anchor_search_bytes: int
    round_kind_offset: int
    round_date_offset: int
    round_b5_offset: int
    round_number_offset: int
    round_no_number_value: int
    round_match_count_offset: int
    round_match_count_max: int
    round_ordinal_offset: int
    round_indexed_kind_value: int
    moved_match_bytes: int
    moved_match_sentinel_offset: int
    moved_match_sentinel_value: int
    round_interstitial_tag_offset: int
    round_interstitial_tag_value: int
    moved_match_tail_offset: int
    moved_match_tail: bytes
    moved_match_max_per_round: int


@dataclass(frozen=True, slots=True)
class StageResultLayout:
    """How to recognise a stage-keyed result record, and where its fields sit.

    One record is `record_bytes` long and carries one match's score. Every offset counts from
    the record start, where the lead byte sits. The same record occurs in the unnamed span and
    in the sections `regions` names, and one locator reads it in both.

    The locator anchors on the two-byte `sentinel_value` at `sentinel_offset`, which is far
    more selective than the single lead byte, and then requires `lead_byte_value` at
    `lead_byte_offset` and a zero byte at `zero_byte_offset`. **`zero_byte_offset` is a locator
    constraint and nothing more.** It is required because it is zero on every record the corpus
    accepted and so costs no record while rejecting look-alikes; it is not evidence about what
    that byte means, and it must not be described as such.

    A candidate is accepted when the whole record lies inside the window, those three locator
    bytes hold, both team ids lie inside the inclusive `team_id_range`, neither goal byte is
    above `goals_maximum`, and the date at `date_offset` decodes. Those tests are structural, so
    the span pass can apply them before any other reader has run.

    Two further tests decide whether an accepted record is in scope, and they are not part of
    this layout because neither is known until the fixture calendar and the stage table have
    been read: the stage id at `stage_id_offset` must be one the stage table holds, and the
    match date must fall inside the calendar's own first and last date. **The acceptance window
    is the calendar's own range, so this layout carries no year window of its own.** A record
    dated outside the range the calendar covers can never join a fixture, whatever the reader
    does with it.

    `regions` names the sections scanned besides the span. A section a save does not list is
    skipped. The layout itself is registered under the span, which is the one region it is
    always scanned in.
    """

    record_bytes: int
    lead_byte_offset: int
    lead_byte_value: int
    date_offset: int
    stage_id_offset: int
    sentinel_offset: int
    sentinel_value: int
    zero_byte_offset: int
    home_team_id_offset: int
    away_team_id_offset: int
    home_goals_offset: int
    away_goals_offset: int
    r22_offset: int
    team_id_range: tuple[int, int]
    goals_maximum: int
    regions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CompetitionIdPairLayout:
    """How to find the records in `game_db` that pair a stage-space id with a database id.

    A record starts `record_offset_from_marker` bytes after the start of `marker`, and every
    other offset counts from the record start, so the constants in front of it are negative.
    The record holds the stage-space entity id at `entity_id_offset` and the editor database
    id twice, at `database_id_offset` and `database_id_copy_offset`.

    The marker is a run of `0xFF` bytes and a `0x01`, which is weak on its own: such a run is
    common, and the marker alone hits about ten times as often as a record occurs. A candidate
    is accepted only when the whole record lies inside `game_db`, the two database id words
    are equal, the entity id and the database id lie inside their inclusive ranges, and every
    `(offset, value)` pair in `constant_bytes` holds.

    `constant_bytes` holds an offset only when its byte takes one value on at least 99% of the
    records of every save measured **and** requiring it costs no competition its database id.
    Several further offsets are that constant and are deliberately left out, because each of
    them rejects records the save really does pair: a lost pair is worse than a kept false one,
    and the records they reject are ordinary competitions rather than noise.

    The records cover the whole stage-space entity space, of which competitions are a subset,
    so the map is restricted to competitions by its caller and is never a competition list.
    """

    marker: bytes
    record_offset_from_marker: int
    entity_id_offset: int
    database_id_offset: int
    database_id_copy_offset: int
    entity_id_range: tuple[int, int]
    database_id_range: tuple[int, int]
    constant_bytes: tuple[tuple[int, int], ...]


@dataclass(frozen=True, slots=True)
class StadiumTableLayout:
    """Where the stadium table sits in `game_db`, and where a stadium row's fields sit.

    The table is found by its own first rows: a locator pattern built from `row_bytes` matches
    the words 1, 2 and 3 one stride apart, and a hit is accepted only when `locator_rows` rows
    from there each store their own ordinal, the stadium uid twice, and a zero byte. The head
    is at no fixed fraction of the section, so nothing here is an offset into `game_db`.

    The walk then steps row by row and stops at the first row that does not decode, so it
    never resynchronises: a row whose ordinal is not the next one ends the table.

    Every other offset counts from a row start. A row is `row_bytes` long unless bit
    `inline_name_flag` of the byte at `flags_offset` is set, and then the u32 at
    `name_length_offset` is a name length inside `name_length_range`, that many UTF-8 bytes
    follow at `name_offset`, and the row is `row_bytes + named_row_extra_bytes` plus the name:
    the bytes an unnamed row holds from `name_length_offset` on follow the name instead. A name
    that is not valid UTF-8, or a length outside the range, ends the walk.

    The owner at `owner_offset` is a public club index, and the uid words hold the uid minus
    one, the same convention club uids use. Ranges are inclusive (lowest, highest).

    `pitch_length_range` is the pitch length the pitch check accepts, and
    `home_ground_minimum_fixtures` how many first-team home matches of a club the calendar must
    record before the ground it used most counts as that club's home ground.

    A closing header stores the next ordinal and allocation uid twice, then
    `closing_marker` at `closing_marker_offset` and a third uid at `closing_uid_offset`.
    It is metadata rather than a stadium row and is recognised before the row walk.
    """

    row_bytes: int
    ordinal_offset: int
    uid_offset: int
    uid_copy_offset: int
    zero_byte_offset: int
    all_seater_offset: int
    u17_offset: int
    expansion_offset: int
    u25_offset: int
    owner_offset: int
    b33_offset: int
    capacity_offset: int
    pitch_length_offset: int
    pitch_width_offset: int
    built_offset: int
    rebuilt_offset: int
    date_58_offset: int
    pitch_min_length_offset: int
    pitch_min_width_offset: int
    pitch_max_length_offset: int
    pitch_max_width_offset: int
    flags_offset: int
    inline_name_flag: int
    name_length_offset: int
    name_offset: int
    named_row_extra_bytes: int
    name_length_range: tuple[int, int]
    locator_rows: int
    pitch_length_range: tuple[int, int]
    home_ground_minimum_fixtures: int
    closing_marker_offset: int
    closing_marker: bytes
    closing_uid_offset: int


@dataclass(frozen=True, slots=True)
class StageTableLayout:
    """Where the stage table sits in `game_db`, and where a stage row's fields sit.

    The table is found in the last `search_bytes` of `game_db`, at the first offset where
    `chain_rows` rows in a row all decode `row_bytes` apart. When none does, the window doubles
    until it reaches `max_search_bytes`, or the start of `game_db` when that is None,
    searching only the stretch each doubling adds, so a save whose table sits near the end
    pays for the first window alone. The head of that chain is then reached by stepping back
    a row at a time. A row decodes when the byte at
    `zero_byte_offset` is zero, the stage id at `stage_id_offset` is repeated at
    `stage_id_copy_offset` and lies strictly between the bounds of
    `stage_id_exclusive_range`, and the word at `previous_stage_id_offset` is either that id
    minus 1 or the missing value. Where a row does not decode, the walk scans forward at most
    `resynchronisation_bytes` for the next one that does.

    Every other offset counts from the row start. A competition id at or above
    `competition_id_limit` is a marker or a malformed row rather than a competition, and is
    read as no competition.
    """

    row_bytes: int
    previous_stage_id_offset: int
    stage_id_offset: int
    stage_id_copy_offset: int
    zero_byte_offset: int
    competition_id_offset: int
    group_id_offset: int
    round_offset: int
    unknown_s25_offset: int
    unknown_s29_offset: int
    stage_id_exclusive_range: tuple[int, int]
    competition_id_limit: int
    search_bytes: int
    max_search_bytes: int | None
    chain_rows: int
    resynchronisation_bytes: int


@dataclass(frozen=True, slots=True)
class SeasonHistoryLayout:
    """Archive and list envelopes, plus the selector relative to a validated person block."""

    archive_header: bytes
    index_header: bytes
    unit_bytes: int
    footer: bytes
    selector_offset_from_block_start: int
    kind_names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SeasonStatsLayout:
    """The season-statistics section: one unlisted frame of the span region, one record per player.

    The frame's body is a section header carrying `section_schema`, then records back to back,
    then a zero byte ending the list and `footer_bytes` that end the frame. A record is a `01`
    byte, a u32 key (the player's pindex plus one), `header_bytes` of header, `own_slots` slots,
    `block_bytes` of block, a u32 count of other teams, each `other_team_lead_bytes` then a u32
    team id and `other_team_slots` slots, a u32 count of `rating_item_bytes` items, and a form
    list: a count byte then `form_entry_bytes` per entry. A slot is a zero byte when absent, or
    a `line_bytes` line starting with `line_marker`. The three counts are rejected above
    `maximum_other_teams`, `maximum_rating_items` and `maximum_form_entries`.

    Each entry of `fields`, `outfield_fields` and `goalkeeper_fields` is (field name, offset
    from the line start, little-endian struct format code, stored units per public unit); a
    unit of 1 reads a count and any other unit a float. `outfield_fields` and
    `goalkeeper_fields` share their words: a
    line reads one set or the other depending on whether its player is a natural goalkeeper.
    `rating_sum_offset` holds ten times the sum of the player's match ratings, which divided by
    the rated appearances at `rated_appearances_offset` gives his average rating.
    `maximum_minutes_per_appearance` bounds a line's minutes for the checks. `slot_kinds` names
    the kind of match each slot counts, in slot order, by `fmsave.SeasonStatsKind` value; another
    team's slots are the first `other_team_slots` of them.
    """

    section_schema: int
    header_bytes: int
    own_slots: int
    other_team_slots: int
    line_bytes: int
    line_marker: bytes
    block_bytes: int
    other_team_lead_bytes: int
    maximum_other_teams: int
    rating_item_bytes: int
    maximum_rating_items: int
    form_entry_bytes: int
    maximum_form_entries: int
    footer_bytes: int
    rating_sum_offset: int
    rated_appearances_offset: int
    rating_scale: int
    fields: tuple[tuple[str, int, str, int], ...]
    outfield_fields: tuple[tuple[str, int, str, int], ...]
    goalkeeper_fields: tuple[tuple[str, int, str, int], ...]
    maximum_minutes_per_appearance: int
    slot_kinds: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TaggedStreamLayout:
    """The repeating record shape of the game's tagged stream.

    One record is `<tag_bytes bytes: the tag, byte-reversed><separator_value><type><value>`.
    The type byte says how the value is stored: `u8_types` one byte, `u16_types` two,
    `u32_types` four, `string_type` a `u32` byte length of at most `max_string_bytes`
    followed by that many UTF-8 bytes, `list_type` a `u32` count that opens a sub-list of
    that many following records, and `nil_type` no value bytes at all.

    Any other type byte ends a walk, as does a tag byte outside printable ASCII, a
    separator that is not `separator_value`, and a value that would run past the walk's end.
    The walk is deliberately strict and never resynchronises: a walk that stepped over bytes
    it could not read would turn a layout that has moved into a shorter, quietly wrong
    result instead of a visibly empty one.
    """

    tag_bytes: int
    separator_value: int
    u8_types: tuple[int, ...]
    u16_types: tuple[int, ...]
    u32_types: tuple[int, ...]
    string_type: int
    list_type: int
    nil_type: int
    max_string_bytes: int


@dataclass(frozen=True, slots=True)
class TransferWindowLayout:
    """How to find a transfer window in the tagged stream of `game_db`.

    A window record opens with its start-date sub-list, so `marker` is that list's own stored
    bytes: the `start_tag` reversed, the separator and the list type. From each hit the reader
    walks tagged values forward for at most `window_scan_bytes` and collects the `start_tag`
    and `end_tag` sub-lists, each carrying `day_tag`, `month_tag` and `year_tag`, and then the
    `close_time_tag` value, which ends the record.

    A sub-list holds more members than the three dates (an id and a day-of-week among them,
    and the day-of-week is sometimes the nil type), so the reader counts nothing down: it
    keeps the date tags it sees while a sub-list is open and lets the next sub-list or the
    closing time close it.

    **The closing time is what makes a window a window.** The date tags alone are shared by
    many kinds of record in this stream: on the saves measured over a thousand start-date
    sub-lists carry a complete date pair and only 54 of them also carry a closing time.
    Accepting on the
    dates alone would return every dated record in the rules database, so a record without a
    closing time is not a window.

    Acceptance is structural and never textual. The window carries no description of its own,
    and an English word in a nearby string would be a localisation risk besides.

    A record is kept only when both sub-lists were found, each holds all three of day, month
    and year, and each value lies inside `day_range`, `month_range` and `year_range`
    (inclusive). `season_year_base` is the stored year that means the season's own start year,
    so a stored year becomes an offset by subtracting it.
    """

    marker: bytes
    start_tag: str
    end_tag: str
    day_tag: str
    month_tag: str
    year_tag: str
    close_time_tag: str
    window_type_tag: str
    window_scan_bytes: int
    day_range: tuple[int, int]
    month_range: tuple[int, int]
    year_range: tuple[int, int]
    season_year_base: int


type BoundPair = tuple[float | None, float | None]


@dataclass(frozen=True, slots=True)
class InjuryTypeTableLayout:
    """The injury-type name table's record shape, and how much of a save is read to find it.

    The table sits inside a per-match directory entry rather than in any section, and every
    such entry of a save holds the same copy of it. A payload whose first bytes are not
    `payload_prefix` is not a per-match file and holds no table.

    One record is `lead_byte`, then the u16 type id at `id_offset`, the u32 name length at
    `length_offset`, that many text bytes at `text_offset`, and `trailer_bytes` of trailer (the
    flag byte, then the u32 second id). A record is accepted when its lead byte matches, its
    length is inside `length_range`, its text is valid UTF-8 containing only printable
    characters or Unicode space separators within `text_byte_range`, and its flag
    is one of `flag_values`; a chain of records is accepted while each record's type id is
    higher than the one before it. The table is the longest chain of at least
    `minimum_chain_entries` records, and entries are read until one holds a table: at most
    `maximum_entries_tried` of those carrying the magic, and at most `maximum_entries_opened`
    entries decompressed at all, so a save whose entries are none of them per-match files is
    still not read whole.

    Ranges are inclusive (lowest, highest).
    """

    lead_byte: int
    id_offset: int
    length_offset: int
    text_offset: int
    trailer_bytes: int
    length_range: tuple[int, int]
    text_byte_range: tuple[int, int]
    flag_values: tuple[int, ...]
    minimum_chain_entries: int
    maximum_entries_tried: int
    maximum_entries_opened: int
    payload_prefix: bytes

    @property
    def record_overhead_bytes(self) -> int:
        """The bytes of one record that are not its text."""
        return self.text_offset + self.trailer_bytes


# Count and share checks on the injury history apply only to a decompressed `injury_manager`
# at least this large; a smaller section comes from a fragment that cannot meet full-save
# counts. Every save measured carries between 1.4 MB and 2.3 MB.
FULL_SAVE_MINIMUM_INJURY_MANAGER_BYTES = 256 * 1024


@dataclass(frozen=True, slots=True)
class InjuryManagerLayout:
    """How the injury history is laid out in the `injury_manager` section.

    From `arrays_offset`, one array per entry of `array_strides`: a u32 row count and then
    that many rows of that stride, back to back. Then one list per entry of
    `list_entry_bytes`, each a u32 entry count and that many entries of that size, and last
    `tail`. The section ends on the tail's last byte, with nothing after it.
    `typed_array_index` and `log_array_index` say which two arrays carry the rows fmsave
    ships; the other two are walked and counted only.

    **The walk is the structural check.** Every count is judged against the bytes left before
    it is used, so a wrong start offset or a single wrong stride reads a count out of the
    middle of a row and fails on the first part that does not fit. There is no signature to
    search for and no way to resynchronise, which is why nothing here is a range or a cap.

    Inside a row, `lead_byte` sits at offset 0, the 4-byte date at `date_offset` and the u32
    person selector (the person's index plus one) at `selector_offset`. A log row carries a
    u32 team id at `log_team_offset` and the two coded bytes at `log_cause_offset` and
    `log_severity_offset`; a typed row carries a u16 injury type at `typed_type_offset` and
    two unnamed bytes at `typed_r11_offset` and `typed_r12_offset`.

    Both dates carry time-slot bits in the high bits of their first word, so they are decoded
    with `fmsave._scan.decode_date` rather than any validator that wants those bits clear.
    `typed_clock_band_days` is how far either side of the in-game date a typed row's date may
    sit before the check that judges those dates counts it as unsound, and `recent_log_days`
    how far back a log row counts as recent for the check that compares its team with the
    player's current one. The band is not a rule the game keeps to: it is wide enough to hold
    every dated typed row of every save measured with room to spare, and narrow enough that a
    date read from neighbouring bytes falls outside it.
    """

    arrays_offset: int
    array_strides: tuple[int, ...]
    typed_array_index: int
    log_array_index: int
    list_entry_bytes: tuple[int, ...]
    tail: bytes
    lead_byte: int
    date_offset: int
    selector_offset: int
    log_team_offset: int
    log_cause_offset: int
    log_severity_offset: int
    typed_type_offset: int
    typed_r11_offset: int
    typed_r12_offset: int
    typed_clock_band_days: int
    recent_log_days: int


@dataclass(frozen=True, slots=True)
class AffiliateGroupLayout:
    """Where the groups of clubs sit in the `feeder_man` section.

    The u32 at `count_offset` is how many groups the section holds, and the groups follow back
    to back from `groups_offset`: each is a u32 member count and that many u32 public club
    indexes, in the space `ClubIndex.uid_by_club_index` is keyed on and with no offset of one.

    The walk consumes exactly the stored count and must end on the section's last byte.
    `group_size_range` is an inclusive corruption cap and nothing more: it is far wider than
    the largest group any save measured holds, and its only job is to stop a count read from
    the wrong bytes from claiming megabytes of members.
    """

    count_offset: int
    groups_offset: int
    group_size_range: tuple[int, int]


@dataclass(frozen=True, slots=True)
class JobCentreLayout:
    """Where the open vacancies sit in the `job_centre` section, and where a record's fields do.

    The u32 at `count_offset` is how many records the section holds, and they follow back to
    back from `records_offset` with no trailer after the last. A record is `record_bytes` long
    plus `id_bytes` for each id in its own id list: the byte at `id_count_offset` is how many
    u32 ids follow it. **That the stored count of records, each sized by its own id count,
    ends exactly at the section's end is structural**: a start shifted by a whole record
    satisfies every per-record check below, and only that identity fails.

    Every other offset counts from a record's start, where `tag` sits, as it stands in a record
    with no ids; an offset past `id_count_offset` moves on by the bytes of the record's id list.
    The u32 at `team_id_offset` is a team id, in the space `ClubIndex.team_to_club` is keyed
    on. The dates at `advertised_offset` and `date_12_offset` both carry non-zero time-slot
    bits, so they are decoded with `fmsave._scan.decode_date` rather than any validator that
    wants those bits clear. The u16 at `competition_offset` is a competition id in the stage id
    space, and `no_competition` is the value that means the record names none. The byte at
    `b17_offset` is 0 or 1 on every record of every save measured, and the byte at
    `reserved_u8_offset` is zero: both are counted for the reader's checks and neither, nor the
    ids, is shipped.
    """

    count_offset: int
    records_offset: int
    record_bytes: int
    tag: bytes
    team_id_offset: int
    role_offset: int
    advertised_offset: int
    date_12_offset: int
    id_count_offset: int
    id_bytes: int
    b17_offset: int
    competition_offset: int
    no_competition: int
    u20_offset: int
    league_position_offset: int
    reserved_u8_offset: int
    flag_offset: int


@dataclass(frozen=True, slots=True)
class StaffLayout:
    """Where a club lists its staff, and how one staff person's object is laid out.

    **The club lists.** From `ClubRecordSpan.team_list_end`, a club record holds a count byte
    and that many affiliated-team ids, and then exactly `list_count` staff lists, each its own
    count byte followed by that many u32 values, each a person id plus one. The bytes after the
    last list are other data and are never read as a fourth list. A club's lists are read only
    when they all end at or before the record's end and every value lies inside
    `list_value_range` or is zero, which names no person.

    **The person object.** `header` is the offset of the u32 person id. The uid sits twice, at
    `uid_offset` and `uid_copy_offset` on ordinary headers. At or above
    `allocated_uid_minimum`, distinct identity words also require the complete staff ability
    and preference structure. `kind_offset` holds `staff_kind` for a staff member
    and `human_kind` for the human manager. `entry_count_offset` holds how many `entry_bytes`
    entries the object carries; they start two bytes later, behind a zero byte, and nothing
    reads either of those two positions. Three
    reputation words follow the entries, so the ability block starts at

        ability = header + ability_base_offset + entry_bytes * entry_count

    and every offset below counts from there: the current ability, the potential ability, the
    role-like byte at `r4_offset`, `code_count` bytes from `codes_offset`, the sentinel byte,
    `preference_count` preference slots from `preferences_offset`, and `block_40_count` further
    bytes from `block_40_offset`.

    An object carries a readable **ability signature** when both abilities lie inside
    `ability_range` and the sentinel byte equals `sentinel_value`. Without one, nothing read
    from the ability block is shipped: the block's position rests on the entry count, and an
    object whose signature does not read is an object whose position is not to be trusted. The
    human manager's object has no readable signature at all.

    `named_preference_slots` pairs each named preference with its slot;
    `unnamed_preference_slots` are the slots that ship as raw numbers, and
    `range_checked_preference_slots` the slots whose value is counted for the checks, which is
    every slot but the one holding a number outside `preference_range`.

    **Discovery.** A staff member's contract record sits inside his own object, so it is found
    by one filtered pass over the section for the contract tag followed by a selector no larger
    than `discovery_selector_maximum` and a team id inside the contract layout's range. From a
    hit's tag the person's header is searched for backwards inside
    `contract_header_search_bytes`; the largest distance measured is 8,161 bytes.

    **Person blocks.** A contracted person's name block follows his own contract record, so it
    is searched for from `person_block_offset_after_tag` past the tag, for at most
    `person_block_search_bytes` and never past the next header. A person with no contract is
    searched for from just past his header for at most `list_only_block_search_bytes`.
    """

    kind_offset: int
    staff_kind: int
    human_kind: int
    uid_offset: int
    uid_copy_offset: int
    allocated_uid_minimum: int
    entry_count_offset: int
    entry_bytes: int
    ability_base_offset: int
    current_ability_offset: int
    potential_ability_offset: int
    ability_range: tuple[int, int]
    r4_offset: int
    codes_offset: int
    code_count: int
    code_set: frozenset[int]
    sentinel_offset: int
    sentinel_value: int
    preferences_offset: int
    preference_count: int
    preference_range: tuple[int, int]
    named_preference_slots: tuple[tuple[str, int], ...]
    unnamed_preference_slots: tuple[int, ...]
    range_checked_preference_slots: tuple[int, ...]
    block_40_offset: int
    block_40_count: int
    block_40_range: tuple[int, int]
    list_count: int
    list_value_range: tuple[int, int]
    discovery_selector_maximum: int
    contract_header_search_bytes: int
    person_block_offset_after_tag: int
    person_block_search_bytes: int
    list_only_block_search_bytes: int
    preference_slot_sentinels: tuple[tuple[int, int], ...] = ()
    non_staff_contract_kinds: tuple[int, ...] = ()


@dataclass(frozen=True, slots=True)
class TacticsLayout:
    """Where the manager's team blocks sit in `tactics_man`, and how one tactic is laid out.

    **Header.** The byte at `header_marker_offset` is `header_marker`, the u32 at
    `selector_offset` is the human manager's own selector (his person id plus 1, the value
    `humans` stores) and the u32 at `block_count_offset` is how many team blocks follow from
    `first_block_offset`. The u16 in front of the marker is 1 on every save measured and is
    read by nothing: "the number of human managers" is a hypothesis with no second case to
    test, and a save with two humans is not in the corpus.

    **Team blocks.** Stored blocks for teams of the managed club, in ascending team id, found
    by searching for the team's own id followed by `block_marker`. Not every club team has a
    stored block; a team id those six bytes match
    at several places, or none, gets no block. A block starts with that id and marker, then a
    length-prefixed selection label, then `selection_slot_count` selector words, then
    `selection_end_marker`, two selector lists, `list_item_lead_byte` and one selector,
    one of `taker_markers`, `taker_list_count` lists, `order_marker`, `order_list_count` lists,
    a zero byte, the u32 the manager's choice of tactic may sit in (`no_tactics_value` on a block with
    no tactic) and the u16 count of tactic records. A selector list is a u32 count and that
    many `list_item_lead_byte` plus u32 pairs; nothing caps a count but the bytes left in the
    section, because one list of 99 selectors exists.

    **Tactic records** are bounded by the next signature, never by the walk: the bytes after a
    record's last slot block are not decoded, so the record after it starts at the next
    `user_signature`, `alternate_signature` or `preset_signature` hit, and the count says how
    many to read. A record is its signature, a length-prefixed name within `name_length_range`, `name_zero_bytes`
    zero bytes, `team_instruction_bytes` instruction bytes of which `mentality_index` is the
    mentality code, a length-prefixed style label, `style_code_bytes` of style code, and then
    `slot_count` **pairs** of slot blocks: the in-possession block and then the
    out-of-possession block, which is the one carrying the extra per-position index byte. The
    22 blocks of a record are pairs and not two runs of eleven: walked as two runs the walk
    stops at the third block on every record of every save measured, and walked as pairs it
    completes on all of them with the index bytes a permutation of 0 to `slot_count` less one.

    **A slot block** is `slot_tag`, a u32 position mask whose bits 0 to `position_bit_count`
    less one are positions and whose higher bits are column flags, `slot_constant`, a u32
    count of setting units inside `unit_count_range`, `role_bits_bytes` of role bits, that many
    `unit_bytes` units and `trail_bytes` of trailing bits. A unit is `unit_lead`, a head byte,
    `unit_first_field_bytes` of one bit field, `unit_separator` and
    `unit_second_field_bytes` of another.

    **Set-piece routines** follow a block's tactic records. The area header occupies
    `routine_area_header_bytes`, including `routine_area_marker`. Default runs alternate with
    counted user groups; `routine_group_sizes` gives both the default run sizes and the number
    of counted groups following each run. Counts inside `routine_group_count_range` determine
    how many user records to read. Each record ends with a length-prefixed UTF-8 name, a flag
    byte inside `routine_tail_flag_range`, a `routine_code_bytes` code and one trailer byte.
    The flag and the code's bytes, which fall inside `routine_code_byte_range`, can each vary
    between routines; the two ranges do not meet, so a tail never overlaps another. Names decode
    backwards from that tail and an unnamed routine stores a zero length. The bounded search
    for a record tail never exceeds `routine_record_max_bytes`.
    """

    header_marker_offset: int
    header_marker: int
    selector_offset: int
    block_count_offset: int
    first_block_offset: int
    block_marker: bytes
    selection_slot_count: int
    selection_end_marker: bytes
    list_item_lead_byte: int
    taker_markers: tuple[bytes, ...]
    taker_list_count: int
    order_marker: bytes
    order_list_count: int
    no_tactics_value: int
    tactic_count_lead_byte: int
    user_signature: bytes
    alternate_signature: bytes
    preset_signature: bytes
    name_zero_bytes: int
    team_instruction_bytes: int
    mentality_index: int
    style_code_bytes: int
    slot_count: int
    slot_tag: bytes
    slot_constant: bytes
    role_bits_bytes: int
    unit_bytes: int
    unit_lead: bytes
    unit_first_field_bytes: int
    unit_separator: int
    unit_second_field_bytes: int
    trail_bytes: int
    unit_count_range: tuple[int, int]
    position_bit_count: int
    routine_tail_flag_range: tuple[int, int]
    routine_code_bytes: int
    routine_code_byte_range: tuple[int, int]
    routine_area_marker: bytes
    routine_area_header_bytes: int
    routine_group_sizes: tuple[int, ...]
    routine_group_count_range: tuple[int, int]
    routine_record_max_bytes: int
    routine_name_length_range: tuple[int, int]
    name_length_range: tuple[int, int]


@dataclass(frozen=True, slots=True)
class TrainingLayout:
    """Where the training calendars, mentoring groups and saved schedules sit in `training_man`.

    **The header.** The u32 at `header_count_offset` is how many `header_entry_bytes` entries
    the per-person list at `header_list_offset` holds. `header_gap_bytes` bytes then sit between
    that list and the first team block; they are not decoded. The first of them is the number of
    blocks that follow on every save measured, but whether it is one byte, two or three is not
    pinned, so nothing reads it and the block walk is judged by its own check instead.

    **A team block** is a u32 team id, the byte `block_lead_byte`, a u32 count of
    `block_entry_bytes` entries, each of which the walk requires to start with
    `block_entry_lead_byte` although nothing else in it is decoded, a u32 count of weekly
    records, those records, `block_tail_bytes` of tail (not decoded), a u32 count of mentoring
    groups, those groups, and the byte `block_terminator` -- except after the last block, which
    is followed by unrelated data. The walk reads a block only while the stored team id is a
    team of the managed club it has not already read, which is what ends it on the last block.

    **A weekly record** is the byte `week_lead_byte`, a 4-byte date at `week_date_offset`
    carrying time-of-day bits, the byte `week_marker_value` at `week_marker_offset`,
    `day_block_count` blocks of `day_block_bytes` at `day_blocks_offset` each starting
    `day_block_lead_byte` (session codes, not decoded), then at `week_name_offset` a u32 length
    of at most `longest_name_bytes` and that many text bytes. **The record is
    `week_record_fixed_bytes` plus that length**, so `week_trailer_bytes` follow the name:
    that length was measured on every record of every save by walking to the next record's lead
    byte, because reading it four bytes short lands a record's end inside the next one.

    The date comes **first**, before the name it belongs to, so a name pairs with the date
    written before it rather than with the following record's.

    **A mentoring group** is the byte `group_lead_byte`, a u32 group number, the byte
    `group_label_marker`, a u32 length and that many label bytes, then a u32 member count of at
    most `most_members_per_group` and that many u32 selectors, each a player's record index plus
    one. `most_members_per_group`, `longest_name_bytes` and `most_library_entries` are
    corruption caps and nothing more: each is far wider than anything a save measured holds (3
    members, 18 name bytes, 4 entries a group), and their one job is to stop a count read from
    the wrong bytes claiming megabytes. Tightening one to what a save holds today would be an
    unmeasured bound, so each is pinned by a test at its own boundary rather than by a saved
    figure.

    **The schedule library** sits somewhere after the last block, at no fixed distance from it
    or from the section's end, so it is found by shape. `library_group_prefix` is the run of
    bytes that sits immediately before a group's u32 entry count on every group of every save
    measured; a group is accepted only when its count is at most `most_library_entries` and
    every one of its entries decodes. An entry is `library_entry_lead_byte`, a u32
    `library_entry_word_value` at `library_entry_word_offset`, the byte
    `library_entry_marker_value` at `library_entry_marker_offset`, `day_block_count` day blocks
    at `library_day_blocks_offset`, then at `library_folder_offset` a folder name, a u32
    schedule id and a schedule name.

    `seven_day_step` is how many days apart consecutive weeks are, which the reader counts.
    """

    header_count_offset: int
    header_list_offset: int
    header_entry_bytes: int
    header_gap_bytes: int
    block_lead_byte: int
    block_entry_bytes: int
    block_entry_lead_byte: int
    block_tail_bytes: int
    block_terminator: int
    week_lead_byte: int
    week_date_offset: int
    week_marker_offset: int
    week_marker_value: int
    day_blocks_offset: int
    day_block_count: int
    day_block_bytes: int
    day_block_lead_byte: int
    week_name_offset: int
    week_record_fixed_bytes: int
    group_lead_byte: int
    group_label_marker: int
    longest_name_bytes: int
    most_members_per_group: int
    seven_day_step: int
    library_group_prefix: bytes
    most_library_entries: int
    library_entry_lead_byte: int
    library_entry_word_offset: int
    library_entry_word_value: int
    library_entry_marker_offset: int
    library_entry_marker_value: int
    library_day_blocks_offset: int
    library_folder_offset: int

    @property
    def week_trailer_bytes(self) -> int:
        """The bytes of a weekly record that follow its schedule name."""
        return self.week_record_fixed_bytes - self.week_name_offset - 4


@dataclass(frozen=True, slots=True)
class GateBounds:
    """Loose bounds for the reader checks on what the `game_db` readers decode.

    Each `BoundPair` is an inclusive `(minimum, maximum)` pair; None leaves that side open.
    Rates are shares from 0 to 1, and the other bounds are counts or medians. The checks apply
    only when `game_db` is at least `minimum_applies_from_bytes` long, because smaller sections
    come from fragments that cannot meet full-save counts; the checks on what the span pass
    reads apply only from `span_minimum_applies_from_bytes` of decompressed span, for the same
    reason.

    The readers count values inside these inclusive ranges: `height_range_cm` (heights),
    `age_range_years` (known ages), `home_reputation_window` (the largest difference between
    home and current reputation counted as near), `condition_sharpness_maximum` (the
    largest condition and match sharpness on their stored scale), `natural_goalkeeper_rating`
    (the lowest goalkeeper rating that marks a natural goalkeeper, left out of the outfield
    count) and `goalkeeper_block_low_maximum` (the highest raw handling and raw throwing counted
    as low).

    Players: `players_minimum` (records), `person_blocks` (records with a person block),
    `names_resolved` (of person blocks), `relation_sentinel` (relation entries ending in the
    sentinel byte), `second_nation_qualifier` (second-nation entries with a known qualifier),
    `handling_above_finishing` (all records), `outfield_goalkeeper_block_low` (outfield
    players whose raw handling and raw throwing are both low, of outfield players),
    `with_natural_position`, `height_in_range`,
    `height_median`, `age_median`, `aged_in_range` (of known ages),
    `condition_sharpness_in_range`, `join_date_valid`, `world_not_above_current`,
    `home_near_current`, `team_resolved` (of players with a team) and
    `home_grown_club_refs_resolved` (of home-grown club references).

    Contracts: `players_with_chain` (of players), `no_contract_in_effect` (players whose
    chain records all start after the in-game date, of players with a chain),
    `date_marked_chain_records` (chain records
    found by a date in their tag slot, of chain records), `tails_parsed` (of chain records),
    `tails_without_clause_table` (parsed tails where no clause table is found, of parsed tails),
    `clause_terminator` (clause tables whose bonus lists and zero trailer end exactly at the
    tail start, of clause tables), `contract_head` (of clause tables), `past_dated_tail_ends`
    (of parsed tails with an end date) and `chain_teams_resolved` (of chain records). Only
    tables found by the first search can fail `clause_terminator`, since the search that works
    back from the tail accepts a table only when it ends there; a table that search cannot find
    at all counts towards `tails_without_clause_table` instead, so the two together cover every
    way a clause table can go missing or stop short.

    Clubs: `clubs_minimum` (records), `team_lists_found` and `status_normal` (of clubs),
    `status_confirmation` (of normal status records), `affiliate_lists_found` (club records
    holding an affiliated-team list, of club records), `affiliate_teams_linked` (listed
    affiliate teams that belong to one other club, of listed affiliate teams),
    `reputation_found` (clubs whose status record held a reputation inside the layout's
    range, of club records) and `reputation_median` (the low median of those reputations).
    `affiliate_teams_linked` is not applied when no club lists a team, so
    `affiliate_lists_found` is what fails when the affiliate decode finds nothing at all. The
    reputation pair is what fails when the reputation moves inside the status record: read a
    byte out, most clubs hold no readable reputation at all and the median of the rest climbs
    far above its band, so either bound catches the shift on its own.

    Suspensions: `suspension_share_of_players` (players with an entry, of players),
    `issued_after_clock` (entries issued after the in-game date, of entries) and
    `suspension_scopes_known` (entries whose scope code the layout lists, of entries). The
    first two apply whenever the section is large enough, so a search that finds no entry
    fails the first on its lower bound and the second for want of a rate;
    `suspension_scopes_known` judges the entries that were found, so it is not applied when
    there are none.

    Stages: `stage_rows_minimum` (rows walked), `stage_walk_gaps` (places the walk had to
    resynchronise), `stage_ids_ascending` (steps that reached a higher stage id, of steps),
    `stage_rows_with_competition` (of rows), `stage_trailing_sentinel` (rows whose last word
    is the missing value, of rows) and `stage_table_tail_bytes` (bytes of `game_db` after the
    table, which is near its end).

    Competitions: `competitions_minimum` (distinct competitions the stage table names),
    `competition_database_ids_mapped` (competitions the id-pair records give a database id, of
    competitions), `competition_database_id_conflicts` (competitions dropped because another
    competition claims the same database id, of competitions) and
    `competition_names_within_database_ids` (competitions a user-supplied name map named, of
    competitions that have a database id). There is no lower bound on competitions named,
    because no save stores a competition name and the share is zero until a reader supplies a
    map; the upper bound is what holds a name to the only key it may arrive through.

    Fixtures: `fixtures_minimum` (records in the run kept as the calendar),
    `fixture_cluster_share` (that run, of every fixture record in the span),
    `fixture_strays_minimum` (records the span holds outside that run),
    `fixture_stage_resolved` (kept records whose stage the stage table holds, of kept records
    naming a stage) and `fixture_teams_resolved` (team ids a club lists, of the two per kept
    record). These five are judged against the span rather than `game_db`, so they apply from
    `span_minimum_applies_from_bytes`. A span pass that finds no fixture at all fails the
    first two on their lower bounds and leaves the other three without a rate, so a calendar
    layout that has moved fails here rather than reporting a career with no matches.

    The share and the stray count bound the same split from opposite sides. The share falls
    when the calendar shatters into fragments; the stray count falls to zero when nothing is
    separated from the calendar at all, which the share cannot see, because a reader that kept
    every stray copy scores a perfect 1.0 on it.

    Stage-keyed results: `result_records_minimum` (records accepted in the regions scanned),
    `results_joined` (accepted records that found a fixture on their date and two team ids, of
    accepted records) and `results_for_unplayed` (records whose one fixture is not marked
    played, of joined records). These judge the same pass the calendar does, so they apply from
    `span_minimum_applies_from_bytes` alongside the fixture bounds.

    `results_joined` is the one that says the record shape is still being read correctly. The
    records are found by one locator and the calendar by an entirely different one, in another
    region, so a decode that has moved stops matching a calendar it never shared an offset
    with: joining on a key wrong by a single day, or with the two sides swapped, was measured at
    zero joins. The bound is a floor under a rate observed near 0.97, low enough that a career
    holding more unjoinable history clears it.

    Transfer windows: `transfer_windows_minimum` (windows decoded) and `transfer_window_dates`
    (windows whose two date groups both decoded inside their ranges, of the records that
    carried a closing time). Windows are database content rather than career state, so both
    bounds rest on **one** installed database and are kept loose: a database with
    fewer nations loaded legitimately carries fewer windows. A decode that finds nothing fails
    the count on its lower bound, and one that has moved only inside the date groups leaves
    the count alone and drops the share instead.

    League tables: `table_blocks_minimum` (blocks left after repeated content is dropped),
    `table_block_duplicates_minimum` (blocks dropped as repeats),
    `table_block_team_in_range` (of the blocks kept), `table_groups_resolved` (of groups),
    `double_round_robin_divisions` (groups shaped like a division whose clubs play each other
    twice; applied only once the fixture calendar shows at least that many divisions under
    way) and `table_venue_calendar_agreement` (slots whose venue the calendar decides and
    the slot parity names the same way, of the slots the calendar decides). These judge the
    span pass, so they apply from `span_minimum_applies_from_bytes`.

    `table_venue_calendar_agreement` is what keeps the slot parity honest, and it is the one
    league-table gate an empty population leaves unjudged rather than failed: a layout that
    settles no parity decides nothing, and so does a career whose tables are all out of step
    with its calendar, which is a fact about the save. The count gates beside it are what fail
    when the table decode itself has found nothing.

    Competition rules: `rules_markers_minimum` (rules preamble blocks the span pass judged),
    `rules_fully_parsed` (of those blocks), `rules_linked_blocks_minimum` (blocks whose
    following run of table blocks is exactly one league table with a competition of its own)
    and `rules_link_round_dates` (dated rounds falling on a date the linked competition plays a
    fixture on, of the dated rounds linked blocks hold). These judge the span pass, so they
    apply from `span_minimum_applies_from_bytes`.
    `rules_fully_parsed` counts the **strict** sense of a
    parsed block, the one `RawRulesBlock.fully_parsed` carries: the promotion quad written
    twice identically and the tie-break list, the prize list and every round record decoded.
    A count that ignored the quad would sit about ten points higher, so this floor must not be
    read against a figure measured the other way. A marker search that has moved finds nothing
    and fails the count on its floor; a body decode that has moved keeps the markers and drops
    the share instead, so the two fail on different faults.

    The last two judge the positional competition link, and the pair is deliberate: **one is a
    count precisely because no share of this link can fail when it stops linking.** The
    misalignment a share could catch is taking the table run before a block instead of the run
    after it, and that permutes the same runs among the same blocks, so every share built from
    the link is invariant under it by construction: the share of blocks that link at all is
    0.55 to 0.68 whichever run is taken. `rules_link_round_dates` escapes that because it is a
    share of *round dates* rather than of blocks, and it separates cleanly (0.74 to 0.78
    against 0.55 to 0.58) -- but it is a share with no population of its own to fall back on,
    so the empty-population rule leaves it unjudged when nothing links at all. `rules_linked_blocks_minimum` is what
    closes that hole: a link that quietly stops linking scores zero on it, which no share here
    would notice. It applies only above `rules_link_minimum_applies_from_runs` blocks with a
    run, so a save holding few divisions is not held to a count measured on saves holding many.

    A third measure was dropped rather than shipped: the round-count shape separates only from
    0.62 to 0.64, a window two points wide, which is too little to rest a bound on given the
    saves tested, and the round dates already judge the same alignment with room to spare. It
    ships as an anomaly count.

    The duplicate floor is what fails when the deduplication stops deduplicating. Every save
    measured repeats about 45% of its table blocks, so the count is always in the thousands and
    a floor cannot trouble a healthy save; a reader that kept every copy would score zero on it
    while passing everything else, because the copies are real blocks with sound arithmetic.
    The division count is what fails when the grouping stops separating one table from the
    next: the copies pad the gaps between tables, so grouping them ungrouped collapses dozens
    of tables into one run that is division shaped no longer. Neither failure is visible to
    `table_groups_resolved`, which a single huge group scores 1.0 on.

    Per-match player stats: `per_match_competition_in_stage_space` (records whose competition id
    the stage table names, of records) and `per_match_minutes_in_range` and
    `per_match_rating_in_range` (records with a body whose minutes and whose stored rating are
    at most the layout's maximum, of records with a body). There is deliberately **no** count
    bound: the search is held to a window of years around the save's own clock, so the number of
    records moves with the window and with how long the career has run rather than with the
    layout, and a bound on it would say nothing. The three shares judge each record's shape
    instead, and all three apply whenever the section is large enough, so a search that finds
    nothing leaves every one of them without a denominator and fails here rather than reporting
    a career whose players have played no matches.

    Season stats: `season_stats_records_keyed_to_players` (records whose key names a player, of
    records), `season_stats_players_with_record` (players with a record, of players),
    `season_stats_overall_sums_competitions` (records with an overall line whose appearances,
    minutes, goals and assists equal the league, cup and continental lines added up, of records
    with an overall line) and `season_stats_minutes_in_range` (lines whose minutes are at most
    the layout's maximum per appearance times their appearances, of lines). They apply from
    `minimum_applies_from_bytes` of `game_db`.

    Stadiums: `stadium_rows_minimum` (rows walked), `stadium_pitch_within_limits` (rows whose
    pitch length is inside the layout's range and inside their own stored minimum and maximum
    for both length and width, of the rows that are not the template the table ends with),
    `stadium_owners_resolved` (of rows naming an owning club), `stadium_capacity_within_all_seater`
    (of all rows) and `stadium_home_grounds_owned` (clubs whose calendar home ground is a ground
    they own, of the clubs that own a ground and have a calendar home ground). The four shares
    apply only where their own population is not empty, since a table of grounds no club owns,
    or a career whose calendar gives no club a home ground, is a fact about the save; the row
    count is what fails when the walk finds nothing.

    Stadium joins: `fixture_stadiums_resolved` (kept fixtures whose stored ground the stadium
    table holds, of kept fixtures storing one) judges the fixture reader, so it applies from
    `span_minimum_applies_from_bytes` alongside the other fixture bounds, and only when some
    fixture stores a ground. Its floor sits deliberately above the share a table that lost its
    named tail resolves at, which is the one misalignment this join has: a floor low enough to
    let that control pass would be a check that cannot fail.

    Injury types: `injury_type_entries_minimum` (records of the name table read out of a
    per-match entry). It applies only on a full-size `game_db` **and** when the save lists at
    least one per-match entry, because a save listing none holds these names nowhere at all,
    which is a fact about the save rather than a layout that has moved. The floor sits far
    below the 93 records every save measured carries: what it catches is a record shape read
    from the wrong offset, which decodes a handful of records at most before its chain breaks.
    Injury history: `injury_log_lead_byte`,
    `injury_log_dates` (rows whose date decodes and is on or before the in-game date) and
    `injury_log_teams_resolved` (rows whose team id a club lists), all as shares of the log
    rows; `injury_log_ascending` (steps from one dated row to the next that did not reach an
    earlier date, of those steps); `injury_log_recent_team_matches` (recent rows whose stored
    team is the player's current team, of recent rows whose player resolves and has a team);
    `injury_typed_lead_byte`, `injury_typed_dates_near_clock` (rows whose date decodes **and**
    lands within `typed_clock_band_days` of the in-game date) and
    `injury_typed_types_resolved` (rows
    whose injury type the name table holds), all as shares of the typed rows. They apply from
    `injury_manager_minimum_applies_from_bytes` of decompressed section, because the checks
    judge full-save counts and a fragment carries none.

    The walk itself is the structural check and it raises rather than scoring: a start or a
    stride read wrong cannot consume the section exactly. What these shares add is a judgement
    of each row's own shape, and each one separates a sound decode from the same rows read one
    or four bytes late: the lead byte falls to at most 0.012, the dated-and-near-the-clock
    share to zero and the injury types to zero, teams to at most 0.21, and the ascending share
    to at most 0.82. `injury_log_recent_team_matches` is the one join to a table read from
    another section entirely, and putting a random player in place of the stored one scores at
    most 0.0003 on it. `injury_log_ascending` is judged on the steps between dated rows and is
    deliberately **not** excused when there are no such steps: a section holding ten thousand
    log rows from which not one date decodes is what a decode read one byte out looks like, so
    it fails there for want of a rate.

    `injury_typed_dates_near_clock` counts over **every** typed row rather than over the dated
    ones, and that denominator is the whole reason it can fail. Over the dated rows the share
    is 1.0 read correctly and 1.0 read one byte late too, because the handful of dates that
    still decode there land near the clock as well; over every typed row it falls from 0.988
    to 0.0. It subsumes a plain check on how many rows carry a date and catches what that
    check cannot: a date read from neighbouring bytes that decodes to a year the game has
    long passed, which is where every date that still decodes one byte late lands.

    What the band does **not** claim is a retention rule. How far behind the in-game date a
    typed row may sit is career state, not layout: on seven save states measured the oldest
    dated typed row was seven days behind the clock on five of them and eight days behind on
    the other two, with a full day's worth of rows at that age rather than a remnant, so a
    bound drawn tight around either figure fails a save the reader reads correctly. The band
    is `typed_clock_band_days` either side of the clock instead: 2.7 times the widest
    deviation measured (66 days, ahead of the clock), while every date read one byte late
    lands more than a thousand days away. The counts behind the tail are reported as
    anomalies.

    One counted share carries no gate: how many log rows still name a player is 0.94 to 0.96,
    and it is career state rather than layout, since a person the save no longer keeps as a
    player is a real row the game still shows. It is reported as an anomaly instead.

    Club finances: `finance_net_identity` (rows whose net equals total income less total
    expenditure, of rows), `finance_balance_continuity` (consecutive row pairs where the later
    balance is the earlier one plus the later month's net, of such pairs; a club's first pair
    also counts when its oldest row holds an opening balance),
    `finance_expenditure_split` (rows whose expenditure excluding transfers lies between zero
    and the total, of rows), `finance_clubs_with_two_chains` (clubs holding a second snapshot
    chain), `finance_series_minimum` (clubs with a series) and, in `sponsorships()`,
    `finance_clubs_with_sponsors` (clubs with a decoded primary sponsor list, including an
    explicitly empty list, of clubs with a series) and
    `sponsor_clubs_minimum` (clubs with a decoded primary sponsor list).

    Only some of a save's clubs keep a finance series at all -- those of the one or two league
    nations the save tracks, which changes during a career -- so `finance_series_minimum` bounds
    it at one and applies only where a managed club exists, whose club held a series on every
    save measured. The three shares and the sponsor share each apply only where they have a
    denominator, because a save whose clubs keep no series is a save with nothing to judge
    rather than a broken decode; the series floor is what catches a locator that has stopped
    finding chains, and on a save with no human manager nothing does.

    `sponsor_clubs_minimum` is the sponsor share's own numerator judged without a denominator.
    It distinguishes a table that is empty because valid primary lists contain zero rows
    from a table that is empty because no lists were decoded. The floor applies where a
    managed club exists, as the series floor does. An invalid or missing positive list still
    lowers the coverage share even when a later sponsor-shaped run exists.


    Club facilities: `facility_byte_in_range` (clubs whose rating lies inside the layout's
    range, of clubs with a finance series and a rating that is not unset),
    `facility_unset_ratings` (clubs whose rating is unset, of clubs with a finance series) and
    `facility_clubs_minimum` (clubs with a rating). The shares apply only where a club has a
    series, as the finance shares do, and the count floor applies only where the save lists a
    managed club, whose own club held a series on every save measured. The in-range share is
    what catches a rating read from the wrong offset: the byte one before the rating reads
    inside the range on at most 0.02 of the clubs, the byte one after on at most 0.09, and four
    bytes after -- the worst control measured -- on at most 0.63, all far below the floor. The
    unset share keeps a read that lands in a zeroed stretch for most clubs from passing by
    leaving the in-range share almost nothing to judge.

    Affiliate groups: `affiliate_members_resolved` (group members the public club index names,
    of group members). It applies on a full-size `game_db` **and** only when a group holds a
    member at all, because a save whose section stores no group has no member to resolve and
    an empty population is not a failure. What it catches is the index space: read one index
    out and the share falls from 0.9836 to 0.859.

    Job vacancies: `job_vacancy_tag` (records carrying the record tag), `job_vacancy_dates_ordered`
    (records whose advertised date is on or before the in-game date and whose second date is on
    or after the advertised one), `job_vacancy_advertised_ascending` (steps from one record's
    advertised date to the next that did not go backwards, of those steps),
    `job_vacancy_reserved_zero` (records whose reserved byte is zero and whose unnamed flag
    byte is 0 or 1), all as shares of the records read. They apply from
    `job_vacancy_minimum_applies_from_records` records, which is what leaves a legitimately
    short or empty feed alone: the feed is career state, a manager between jobs may see very
    little of it, and no floor under its size could tell a quiet job market from a layout that
    has moved. The structural size identity in
    `JobCentreLayout` is what catches a start shifted by a whole record, which every share here
    passes. There is no gate on how many team ids resolve: ids are about 92% dense over the
    range the feed uses, so that share cannot fail. There is none on how many competition ids
    the stage table names either: it is 1.0 read correctly **and** 1.0 with the record start
    shifted four bytes on every save measured, so it cannot fail.

    Staff: `staff_lists_fit` (club records whose affiliated-team list and three staff lists end
    inside the record with every value in range, of club records carrying a team list) and
    `staff_list_ids_are_staff` (listed people whose header is a staff object with a name block,
    of listed people), both in `staff_lists()`; and in `staff()` `staff_ability_signature`,
    `staff_preference_slots`, `staff_codes_in_set` and `staff_block_40_in_range`, each of the
    staff objects the rows were built from, `staff_person_blocks` (people with a name block, of
    people), `staff_minimum` (people), `staff_listed_contracted_here` (listed pairs whose
    person holds a contract at the listing club or at its parent, of listed pairs) and
    `staff_unowned_tailed_contracts` (contract records with a tail whose person has no header
    in front of them).

    The four object shares apply only where a staff object was read, and the block share and
    the count floor only on a full-size `game_db`; the list shares apply only where a club
    record carries a team list and where a club lists somebody. Each separates a sound read
    from a wrong one under a different misalignment: the fit share fails on a list start read
    one or four bytes late, the id share on a start read one byte early, the four object shares
    on an ability block read one byte either way or four bytes late or on the entry count read
    one byte late, the block share on a name-block window that starts past the block, and the
    unowned count on a kind byte read one byte out. `staff_block_40_in_range` holds at 1.0 with
    the ability block read one byte early, which the three shares beside it catch instead.

    Tactics: `tactics_manager_selector_matches` (1 when the section header names the same human
    manager as `humans`), `tactics_team_blocks_match_club` (blocks found, of structurally
    located blocks naming managed-club teams, and 0 when the header or inventory disagrees),
    `tactic_records_count_matching` (blocks whose declared records were all found),
    `tactic_slot_walks_complete` and `tactic_oop_index_permutations` (stored tactic records whose
    22 slot blocks walked, and whose out-of-possession index bytes are a permutation, of stored
    tactic records), `tactic_selection_selectors_resolved` (selectors the player records name,
    of selectors) and `tactic_selection_selectors_at_club` (of those, the ones at the managed
    club); in `set_pieces()`, `set_piece_blocks_complete` (blocks whose default runs and counted routine groups
    decoded completely, of blocks). They apply on a full-size `game_db` and
    only where the save lists a managed club, because a manager between jobs has no team block
    to read and an empty result is a fact about the career.

    The two walk shares apply when a team block claims tactics or records were decoded.
    Explicitly empty lists need no slot walk, while a nonempty count with no decoded records
    fails both shares and the record-count check. The two selector shares and the routine
    share are excused without a denominator, since a block can store no selection at all.
    Mentality in 1 to 7 is **not** a gate: instruction byte 3 is 6 on every record of every save
    measured, so a record read one byte late passes it.

    Training and mentoring: `training_blocks_match_club_teams` (blocks walked, of the managed
    club's teams), `training_week_steps` (steps from one week to the next that step seven days,
    of those steps) and `mentoring_members_at_club` (group members whose own club is the managed
    club, of the members that resolve to a player). All three apply on a full-size `game_db`
    where the save lists a managed club, since a save with no manager has no calendar to read.

    Only the first is applied whatever the walk found, because its denominator is the club's own
    team count: it is what fails when the block walk has moved, since a shifted walk parses no
    block at all. The other two judge what was read and are not applied on an empty population,
    which is what a club whose teams hold one week or fewer, and a manager who mentors nobody,
    legitimately look like; every save measured has teams with no mentoring group.

    There is **no** check on how many members resolve to a player: the player index is dense
    over the range a squad occupies, so a selector read one too high still resolves most or all
    members on every save measured, and no floor separates that from the 1.0 a correct read
    scores. `mentoring_members_at_club` is what catches that read instead, because the players
    it wrongly resolves to belong to other clubs: the share falls to at most 0.18.
    """

    minimum_applies_from_bytes: int
    span_minimum_applies_from_bytes: int
    height_range_cm: tuple[int, int]
    age_range_years: tuple[int, int]
    home_reputation_window: int
    condition_sharpness_maximum: int
    natural_goalkeeper_rating: int
    goalkeeper_block_low_maximum: int
    players_minimum: BoundPair
    person_blocks: BoundPair
    names_resolved: BoundPair
    relation_sentinel: BoundPair
    second_nation_qualifier: BoundPair
    handling_above_finishing: BoundPair
    outfield_goalkeeper_block_low: BoundPair
    with_natural_position: BoundPair
    height_in_range: BoundPair
    height_median: BoundPair
    age_median: BoundPair
    aged_in_range: BoundPair
    condition_sharpness_in_range: BoundPair
    join_date_valid: BoundPair
    world_not_above_current: BoundPair
    home_near_current: BoundPair
    team_resolved: BoundPair
    home_grown_club_refs_resolved: BoundPair
    players_with_chain: BoundPair
    no_contract_in_effect: BoundPair
    date_marked_chain_records: BoundPair
    tails_parsed: BoundPair
    tails_without_clause_table: BoundPair
    clause_terminator: BoundPair
    contract_head: BoundPair
    past_dated_tail_ends: BoundPair
    chain_teams_resolved: BoundPair
    clubs_minimum: BoundPair
    team_lists_found: BoundPair
    status_normal: BoundPair
    status_confirmation: BoundPair
    affiliate_lists_found: BoundPair
    affiliate_teams_linked: BoundPair
    reputation_found: BoundPair
    reputation_median: BoundPair
    suspension_share_of_players: BoundPair
    suspension_scopes_known: BoundPair
    issued_after_clock: BoundPair
    stage_rows_minimum: BoundPair
    stage_walk_gaps: BoundPair
    stage_ids_ascending: BoundPair
    stage_rows_with_competition: BoundPair
    stage_trailing_sentinel: BoundPair
    stage_table_tail_bytes: BoundPair
    competitions_minimum: BoundPair
    competition_database_ids_mapped: BoundPair
    competition_database_id_conflicts: BoundPair
    competition_names_within_database_ids: BoundPair
    fixtures_minimum: BoundPair
    fixture_cluster_share: BoundPair
    fixture_strays_minimum: BoundPair
    fixture_stage_resolved: BoundPair
    fixture_teams_resolved: BoundPair
    fixture_stadiums_resolved: BoundPair
    result_records_minimum: BoundPair
    results_joined: BoundPair
    results_for_unplayed: BoundPair
    transfer_windows_minimum: BoundPair
    transfer_window_dates: BoundPair
    table_blocks_minimum: BoundPair
    table_block_duplicates_minimum: BoundPair
    table_block_team_in_range: BoundPair
    table_groups_resolved: BoundPair
    double_round_robin_divisions: BoundPair
    rules_markers_minimum: BoundPair
    rules_fully_parsed: BoundPair
    per_match_competition_in_stage_space: BoundPair
    per_match_minutes_in_range: BoundPair
    per_match_rating_in_range: BoundPair
    per_match_lists_complete: BoundPair
    injury_type_entries_minimum: BoundPair
    injury_manager_minimum_applies_from_bytes: int
    injury_log_lead_byte: BoundPair
    injury_log_dates: BoundPair
    injury_log_ascending: BoundPair
    injury_log_teams_resolved: BoundPair
    injury_log_recent_team_matches: BoundPair
    injury_typed_lead_byte: BoundPair
    injury_typed_dates_near_clock: BoundPair
    injury_typed_types_resolved: BoundPair
    finance_net_identity: BoundPair
    finance_balance_continuity: BoundPair
    finance_expenditure_split: BoundPair
    finance_clubs_with_two_chains: BoundPair
    finance_series_minimum: BoundPair
    finance_clubs_with_sponsors: BoundPair
    sponsor_clubs_minimum: BoundPair
    facility_byte_in_range: BoundPair
    facility_unset_ratings: BoundPair
    facility_clubs_minimum: BoundPair
    affiliate_members_resolved: BoundPair
    job_vacancy_minimum_applies_from_records: int
    job_vacancy_tag: BoundPair
    job_vacancy_dates_ordered: BoundPair
    job_vacancy_advertised_ascending: BoundPair
    job_vacancy_reserved_zero: BoundPair
    stadium_rows_minimum: BoundPair
    stadium_pitch_within_limits: BoundPair
    stadium_owners_resolved: BoundPair
    stadium_capacity_within_all_seater: BoundPair
    stadium_home_grounds_owned: BoundPair
    staff_lists_fit: BoundPair
    staff_list_ids_are_staff: BoundPair
    staff_ability_signature: BoundPair
    staff_preference_slots: BoundPair
    staff_codes_in_set: BoundPair
    staff_block_40_in_range: BoundPair
    staff_person_blocks: BoundPair
    staff_minimum: BoundPair
    staff_listed_contracted_here: BoundPair
    staff_unowned_tailed_contracts: BoundPair
    tactics_manager_selector_matches: BoundPair
    tactics_team_blocks_match_club: BoundPair
    tactic_slot_walks_complete: BoundPair
    tactic_records_count_matching: BoundPair
    tactic_oop_index_permutations: BoundPair
    tactic_selection_selectors_resolved: BoundPair
    tactic_selection_selectors_at_club: BoundPair
    set_piece_blocks_complete: BoundPair
    training_blocks_match_club_teams: BoundPair
    training_week_steps: BoundPair
    mentoring_members_at_club: BoundPair
    table_venue_calendar_agreement: BoundPair
    rules_linked_blocks_minimum: BoundPair
    rules_link_minimum_applies_from_runs: int
    rules_link_round_dates: BoundPair
    season_stats_records_keyed_to_players: BoundPair
    season_stats_players_with_record: BoundPair
    season_stats_overall_sums_competitions: BoundPair
    season_stats_minutes_in_range: BoundPair


type Layout = (
    GameInfoLayout
    | SaveSummaryLayout
    | SummaryStringsLayout
    | NamePoolLayout
    | ClubRecordLayout
    | TeamListLayout
    | ClubStatusLayout
    | PlayerRecordLayout
    | PersonBlockLayout
    | ContractLayout
    | FinanceChainLayout
    | SponsorChainLayout
    | FacilityByteLayout
    | SuspensionLayout
    | MatchRecordLayout
    | MatchSummaryLayout
    | StadiumTableLayout
    | StageTableLayout
    | CompetitionIdPairLayout
    | HumansLayout
    | InjuryTypeTableLayout
    | InjuryManagerLayout
    | AffiliateGroupLayout
    | JobCentreLayout
    | StaffLayout
    | TrainingLayout
    | FixtureCalendarLayout
    | StageResultLayout
    | LeagueTableLayout
    | RulesPreambleLayout
    | TaggedStreamLayout
    | TransferWindowLayout
    | TacticsLayout
    | SeasonStatsLayout
    | SeasonHistoryLayout
    | GateBounds
)


@dataclass(frozen=True, slots=True)
class LayoutEntry:
    region: str
    schema: int | None
    build: str
    layout: Layout


@dataclass(frozen=True, slots=True)
class LayoutMatch[LayoutT]:
    layout: LayoutT
    exact: bool


FALLBACK_BUILD = "26.3.2+2329565"


class _BuildModule(Protocol):
    """A per-build layout module: its build, the builds all its layouts fit, and its layouts."""

    @property
    def BUILD(self) -> str: ...

    @property
    def KNOWN_BUILDS(self) -> tuple[str, ...]: ...

    @property
    def LAYOUTS(self) -> tuple[LayoutEntry, ...]: ...


def _build_modules() -> tuple[_BuildModule, ...]:
    from fm26save._core._layouts import fm26_26_1_0, fm26_26_3_2

    return (fm26_26_3_2, fm26_26_1_0)


def registered_layouts() -> tuple[LayoutEntry, ...]:
    return tuple(entry for module in _build_modules() for entry in module.LAYOUTS)


def known_builds() -> frozenset[str]:
    """Builds whose saves every region's layout fits; other builds borrow layouts."""
    return frozenset(build for module in _build_modules() for build in module.KNOWN_BUILDS)


def _layout_build(build: str) -> str:
    """The build whose layouts a save of `build` is read with: itself, or the one it shares."""
    for module in _build_modules():
        if build in module.KNOWN_BUILDS:
            return module.BUILD
    return build


def find_layout[LayoutT: Layout](
    layout_type: type[LayoutT], region: str, schema: int | None, build: str
) -> LayoutMatch[LayoutT]:
    """The layout for a region, by schema and build, then schema, then build, then fallback.

    A layout registered for the save's own build and schema wins. Failing that, a schema match
    counts only among builds every region's layout fits, so one build's override of a shared
    schema is never applied to another build's save.
    """
    layout_build = _layout_build(build)
    full_builds = known_builds()
    candidates = [
        entry
        for entry in registered_layouts()
        if entry.region == region and isinstance(entry.layout, layout_type)
    ]
    for entry in candidates:
        if (
            schema is not None
            and entry.schema == schema
            and entry.build == layout_build
            and isinstance(entry.layout, layout_type)
        ):
            return LayoutMatch(entry.layout, exact=True)
    for entry in candidates:
        if (
            schema is not None
            and entry.schema == schema
            and entry.build in full_builds
            and isinstance(entry.layout, layout_type)
        ):
            return LayoutMatch(entry.layout, exact=True)
    for entry in candidates:
        if entry.build == layout_build and isinstance(entry.layout, layout_type):
            return LayoutMatch(entry.layout, exact=entry.schema is None)
    for entry in candidates:
        if entry.build == FALLBACK_BUILD and isinstance(entry.layout, layout_type):
            return LayoutMatch(entry.layout, exact=False)
    raise LookupError(f"no {layout_type.__name__} registered for region {region!r}")
