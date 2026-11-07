"""Binary layouts for FM27 (`27.0.0+2486695`)."""

from __future__ import annotations

from dataclasses import replace

from fm26save._core._layouts import (
    LayoutEntry,
    fm26_26_3_2 as _fm26,
)

MATCH_FILE_REGION_NAME = _fm26.MATCH_FILE_REGION_NAME
SPAN_REGION_NAME = _fm26.SPAN_REGION_NAME

BUILD = "27.0.0+2486695"
KNOWN_BUILDS: tuple[str, ...] = (BUILD, "27.0.0+2493426")

GAME_INFO = replace(
    _fm26.GAME_INFO,
    filename_count_offset_after_db_version=167,
    game_date_offset_after_db_version=174,
    late_build_number_window_after_db_version=(176, 420),
)

SAVE_SUMMARY = _fm26.SAVE_SUMMARY
SUMMARY_STRINGS = _fm26.SUMMARY_STRINGS
NAME_POOLS = _fm26.NAME_POOLS
CLUB_RECORDS = _fm26.CLUB_RECORDS
TEAM_LISTS = _fm26.TEAM_LISTS
CLUB_STATUSES = _fm26.CLUB_STATUSES
PLAYER_RECORDS = _fm26.PLAYER_RECORDS

PERSON_BLOCKS = replace(
    _fm26.PERSON_BLOCKS,
    personality_offset_from_birth=22,
    date_zero_bytes_offset_from_birth=15,
    nation_id_offset_from_birth=14,
    relation_present_offset_from_birth=38,
    relation_count_offset_from_birth=39,
    relation_entries_offset_from_birth=40,
)

CONTRACTS = _fm26.CONTRACTS
FINANCE_CHAINS = _fm26.FINANCE_CHAINS
SPONSOR_CHAINS = _fm26.SPONSOR_CHAINS
FACILITY_BYTE = _fm26.FACILITY_BYTE
SUSPENSIONS = _fm26.SUSPENSIONS
MATCH_RECORDS = _fm26.MATCH_RECORDS
MATCH_SUMMARIES = _fm26.MATCH_SUMMARIES
STADIUM_TABLE = _fm26.STADIUM_TABLE
STAGE_TABLE = _fm26.STAGE_TABLE
COMPETITION_ID_PAIRS = _fm26.COMPETITION_ID_PAIRS
TAGGED_STREAM = _fm26.TAGGED_STREAM
TRANSFER_WINDOWS = _fm26.TRANSFER_WINDOWS
HUMANS = _fm26.HUMANS
AFFILIATE_GROUPS = _fm26.AFFILIATE_GROUPS
INJURY_MANAGER = _fm26.INJURY_MANAGER
JOB_CENTRE = _fm26.JOB_CENTRE

STAFF = replace(
    _fm26.STAFF,
    list_count_bytes=2,
)

TACTICS = replace(
    _fm26.TACTICS,
    selection_end_marker=bytes.fromhex("4400"),
    user_signature=bytes.fromhex("2244001b00000002"),
    alternate_signature=bytes.fromhex("2244001b00000000"),
    preset_signature=bytes.fromhex("2244001b00000001"),
    slot_tag=bytes.fromhex("440002"),
    slot_constant=bytes.fromhex("000101"),
    unit_lead=bytes.fromhex("020202"),
)

TRAINING = replace(
    _fm26.TRAINING,
    block_lead_byte=2,
    block_tail_bytes=32,
    day_block_bytes=8,
    day_block_lead_byte=4,
    week_name_offset=62,
    week_record_fixed_bytes=80,
    group_lead_byte=2,
    group_label_marker=None,
    library_folder_offset=62,
    groups_trailer_bytes=4,
)

INJURY_TYPE_TABLE = _fm26.INJURY_TYPE_TABLE
FIXTURE_CALENDAR = _fm26.FIXTURE_CALENDAR
STAGE_RESULTS = _fm26.STAGE_RESULTS
LEAGUE_TABLES = _fm26.LEAGUE_TABLES
RULES_PREAMBLES = _fm26.RULES_PREAMBLES
SEASON_STATS = _fm26.SEASON_STATS
SEASON_HISTORY = _fm26.SEASON_HISTORY
GATE_BOUNDS = _fm26.GATE_BOUNDS

LAYOUTS: tuple[LayoutEntry, ...] = (
    LayoutEntry(region="game_info", schema=47, build=BUILD, layout=GAME_INFO),
    LayoutEntry(region="save_game_summary", schema=31, build=BUILD, layout=SAVE_SUMMARY),
    LayoutEntry(region="save_game_summary", schema=31, build=BUILD, layout=SUMMARY_STRINGS),
    LayoutEntry(region="game_db", schema=4000, build=BUILD, layout=NAME_POOLS),
    LayoutEntry(region="game_db", schema=4000, build=BUILD, layout=CLUB_RECORDS),
    LayoutEntry(region="game_db", schema=4000, build=BUILD, layout=TEAM_LISTS),
    LayoutEntry(region="game_db", schema=4000, build=BUILD, layout=CLUB_STATUSES),
    LayoutEntry(region="game_db", schema=4000, build=BUILD, layout=PLAYER_RECORDS),
    LayoutEntry(region="game_db", schema=4000, build=BUILD, layout=PERSON_BLOCKS),
    LayoutEntry(region="game_db", schema=4000, build=BUILD, layout=CONTRACTS),
    LayoutEntry(region="game_db", schema=4000, build=BUILD, layout=FINANCE_CHAINS),
    LayoutEntry(region="game_db", schema=4000, build=BUILD, layout=SPONSOR_CHAINS),
    LayoutEntry(region="game_db", schema=4000, build=BUILD, layout=FACILITY_BYTE),
    LayoutEntry(region="game_db", schema=4000, build=BUILD, layout=SUSPENSIONS),
    LayoutEntry(region="game_db", schema=4000, build=BUILD, layout=MATCH_RECORDS),
    LayoutEntry(region="game_db", schema=4000, build=BUILD, layout=MATCH_SUMMARIES),
    LayoutEntry(region="game_db", schema=4000, build=BUILD, layout=STADIUM_TABLE),
    LayoutEntry(region="game_db", schema=4000, build=BUILD, layout=STAGE_TABLE),
    LayoutEntry(region="game_db", schema=4000, build=BUILD, layout=COMPETITION_ID_PAIRS),
    LayoutEntry(region="game_db", schema=4000, build=BUILD, layout=TAGGED_STREAM),
    LayoutEntry(region="game_db", schema=4000, build=BUILD, layout=TRANSFER_WINDOWS),
    LayoutEntry(region="humans", schema=24, build=BUILD, layout=HUMANS),
    LayoutEntry(region="feeder_man", schema=5, build=BUILD, layout=AFFILIATE_GROUPS),
    LayoutEntry(region="injury_manager", schema=8, build=BUILD, layout=INJURY_MANAGER),
    LayoutEntry(region="job_centre", schema=1, build=BUILD, layout=JOB_CENTRE),
    LayoutEntry(region="game_db", schema=4000, build=BUILD, layout=STAFF),
    LayoutEntry(region="tactics_man", schema=26, build=BUILD, layout=TACTICS),
    LayoutEntry(region="training_man", schema=32, build=BUILD, layout=TRAINING),
    LayoutEntry(region=MATCH_FILE_REGION_NAME, schema=None, build=BUILD, layout=INJURY_TYPE_TABLE),
    LayoutEntry(region=SPAN_REGION_NAME, schema=None, build=BUILD, layout=FIXTURE_CALENDAR),
    LayoutEntry(region=SPAN_REGION_NAME, schema=None, build=BUILD, layout=STAGE_RESULTS),
    LayoutEntry(region=SPAN_REGION_NAME, schema=None, build=BUILD, layout=LEAGUE_TABLES),
    LayoutEntry(region=SPAN_REGION_NAME, schema=None, build=BUILD, layout=RULES_PREAMBLES),
    LayoutEntry(region=SPAN_REGION_NAME, schema=None, build=BUILD, layout=SEASON_STATS),
    LayoutEntry(region=SPAN_REGION_NAME, schema=None, build=BUILD, layout=SEASON_HISTORY),
    LayoutEntry(region="game_db", schema=4000, build=BUILD, layout=GATE_BOUNDS),
)
