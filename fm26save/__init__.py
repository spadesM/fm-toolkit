"""fm26save: Comprehensive Football Manager 26 (.fm) Save Parser, Unknown-Field Decoder & Exporter."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fm26save import _core

from fm26save.constants import (
    CONTRACT_UNKNOWN_DESCRIPTIONS,
    FM26_NATIONS,
    KNOWN_CITIES,
    RELATION_PAIR_MAP,
    STAFF_BLOCK40_FIELDS,
    STAFF_DEPT_MAP,
    STAFF_ROLE_MAP,
)
from fm26save.container import FM26Container, RawSectionSummary, extract_length_prefixed_strings
from fm26save.diff import diff_saves
from fm26save.enrichment import (
    build_city_map,
    decode_contracts_enriched,
    decode_facilities_enriched,
    decode_players_enriched_relations,
    decode_staff_enriched,
    decode_tactics_lineup,
    resolve_nation,
    resolve_nation_info,
)
from fm26save.exporter import (
    export_tables_to_sqlite,
    export_to_csv,
    export_to_json,
    flatten_record,
    serialize_record,
)
from fm26save.extra_sections import (
    analyze_any_section,
    parse_agents,
    parse_board_takeovers,
    parse_contract_offers,
    parse_hall_of_fame,
    parse_news_items,
    parse_shortlists,
)
from fm26save.formulas import (
    ATTRIBUTE_CATEGORIES,
    CA_POSITION_WEIGHTS_10,
    DUTY_ATTRIBUTE_DELTAS,
    OUT_OF_POSSESSION_ROLE_CATALOG,
    ROLE_ARCHETYPES,
    TACTICAL_ROLE_DEFINITIONS,
    ZERO_CA_COST_ATTRIBUTES,
    analyze_player_role_breakdown,
    calculate_oop_role_effectiveness,
    calculate_role_effectiveness,
    estimate_transfer_value,
    estimate_wage_and_fees,
    extract_fmf_frames,
    get_role_catalog_breakdown,
    load_engine_formulas,
    parse_jsb,
    position_familiarity_multiplier,
    rank_player_roles,
    read_fmf_directory,
)
from fm26save.game_files import (
    extract_all_game_files_summary,
    extract_dbc_and_lnc_rules,
    extract_editor_schemas_and_enums,
    extract_il2cpp_symbols_and_metadata,
    extract_master_db_tables,
    extract_media_interaction_trees,
    extract_momentum_weightings,
    extract_multi_version_database_evolution,
    extract_oop_pitch_proximity_grid,
    extract_permanent_edt_rules,
    extract_pregame_people_and_history_db,
    extract_qme_distributions,
    extract_simulation_aux_fmf_archives,
    extract_tactical_styles_and_presets,
    extract_training_and_newgen_configs,
    extract_xg_shot_models,
    load_official_city_map,
    load_official_local_region_map,
)

__version__ = "1.0.0"

ALL_28_TABLES: tuple[tuple[str, str], ...] = (
    ("players", "players"),
    ("contracts", "contracts"),
    ("suspensions", "suspensions"),
    ("injuries", "injuries"),
    ("injury-types", "injury_types"),
    ("player-season-stats", "player_season_stats"),
    ("player-season-history", "player_season_history"),
    ("player-match-stats", "player_match_stats"),
    ("clubs", "clubs"),
    ("managed-clubs", "managed_clubs"),
    ("finances", "finances"),
    ("sponsorships", "sponsorships"),
    ("facilities", "facilities"),
    ("stadiums", "stadiums"),
    ("affiliates", "affiliates"),
    ("staff", "staff"),
    ("staff-lists", "staff_lists"),
    ("tactics", "tactics"),
    ("set-pieces", "set_pieces"),
    ("training", "training"),
    ("mentoring", "mentoring"),
    ("job-vacancies", "job_vacancies"),
    ("competitions", "competitions"),
    ("stages", "stages"),
    ("league-tables", "league_tables"),
    ("fixtures", "fixtures"),
    ("competition-rules", "competition_rules"),
    ("transfer-windows", "transfer_windows"),
)


class FM26Save:
    """High-level FM26 Save interface combining all 28 core tables, unknown-field decoders,
    70+ extra .dat/.cmt section parsers, and multi-format exporters."""

    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        competition_names: dict[int, str] | str | os.PathLike[str] | None = None,
    ) -> None:
        self.path = Path(path)
        self.container = FM26Container(self.path)
        self._save = _core.open(self.path, competition_names=competition_names)
        self._city_map: dict[int, str] | None = None

    def __enter__(self) -> FM26Save:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def close(self) -> None:
        self._save.close()

    @property
    def info(self) -> _core.SaveInfo:
        return self._save.info

    @property
    def raw_save(self) -> _core.Save:
        return self._save

    @property
    def city_map(self) -> dict[int, str]:
        if self._city_map is None:
            self._city_map = build_city_map(self._save)
        return self._city_map

    def nation_name(self, nation_id: int | None, lang: str = "tr") -> str:
        """Resolve an FM26 nation_id (1..249) to country name."""
        return resolve_nation(nation_id, lang=lang)

    def city_name(self, city_id: int | None) -> str:
        """Resolve an FM26 city_id to city name."""
        if city_id is None:
            return ""
        return self.city_map.get(city_id, f"City #{city_id}")

    def player_role_ratings(self, player: Any, top_n: int = 5, *, include_all_duties: bool = False) -> list[dict[str, Any]]:
        """Rank a player's best tactical roles using FM26 Key (x2) & Preferable (x1) attributes and position familiarity."""
        return rank_player_roles(player, top_n=top_n, include_all_duties=include_all_duties)

    def player_role_breakdown(self, player: Any, *, top_n_per_group: int = 5) -> dict[str, Any]:
        """Return multi-dimensional breakdown (In-Possession, Out-Of-Possession OP*, Dual Combos, Position Line, Duty, Archetype)."""
        return analyze_player_role_breakdown(player, top_n_per_group=top_n_per_group)

    def role_catalog_breakdown(self) -> dict[str, Any]:
        """Return complete FM26 catalog of In-Possession roles, Duties, Archetypes, and 39 Out-Of-Possession (OP*) roles."""
        return get_role_catalog_breakdown()

    def engine_formulas(self) -> dict[str, Any]:
        """Load and decode official Match Engine, xG, Rating, Height & Training formulas from FM26 .fmf files."""
        return load_engine_formulas()

    def game_files_summary(self, fm_install_dir: str | os.PathLike[str] | None = None) -> dict[str, Any]:
        """Extract all 8 FM26 Game-File Reverse-Engineering Systems (QME, Momentum, OOP Grid, xG, Editor Schemas, Master DBs, Media, IL2CPP)."""
        return extract_all_game_files_summary(fm_install_dir)

    def master_db_tables(
        self, fm_install_dir: str | os.PathLike[str] | None = None, *, sample_limit: int | None = 50
    ) -> dict[str, Any]:
        """Extract Pre-Game Master Databases (`client_db.dat`, `lang_update_db.dat`, `server_db.dat`)."""
        return extract_master_db_tables(fm_install_dir, sample_limit=sample_limit)

    # --- 1. Core 28 Tables ---
    def table(self, name: str) -> Any:
        """Read any of the 28 structured tables by hyphenated or underscored name."""
        method_name = name.replace("-", "_")
        getter = getattr(self._save, method_name, None)
        if getter is None:
            raise KeyError(f"Unknown table name: {name!r}")
        return getter()

    def table_counts(self) -> dict[str, int]:
        """Return row counts for all 28 tables."""
        return {tbl_name: len(self.table(method)) for tbl_name, method in ALL_28_TABLES}

    # --- 2. Unknown-Field Enriched Decoders ---
    def staff_enriched(self, *, club_uid: int | None = None) -> list[dict[str, Any]]:
        """Staff with decoded r4 role, department, and 26 hidden 1..100 block_40 attributes."""
        return decode_staff_enriched(self._save, club_uid=club_uid)

    def contracts_enriched(self, *, club_uid: int | None = None, limit: int = 5000) -> list[dict[str, Any]]:
        """Contracts with decoded money_a (Signing/Loyalty), money_b (Agent Fee), money_c, and e12..e39."""
        return decode_contracts_enriched(self._save, club_uid=club_uid, limit=limit)

    def facilities_enriched(self) -> list[dict[str, Any]]:
        """Club facilities with post-finance attendance & fanbase metrics."""
        return decode_facilities_enriched(self._save)

    def players_enriched_relations(
        self, *, club_uid: int | None = None, limit: int = 250
    ) -> list[dict[str, Any]]:
        """Players with hidden tail bytes (RCA, Squad Number) and all PersonBlock relationships."""
        return decode_players_enriched_relations(self._save, club_uid=club_uid, limit=limit)

    def tactics_lineup(self) -> list[dict[str, Any]]:
        """Managed club's Starting XI, Substitutes, and Set-Piece pool from tactics_man.dat."""
        return decode_tactics_lineup(self._save)

    # --- 3. Extra 70+ .dat / .cmt Section Parsers ---
    def hall_of_fame(self, *, limit: int = 500) -> list[dict[str, Any]]:
        return parse_hall_of_fame(self._save, limit=limit)

    def board_takeovers(self) -> list[dict[str, Any]]:
        return parse_board_takeovers(self._save)

    def shortlists(self, *, limit: int = 500) -> list[dict[str, Any]]:
        return parse_shortlists(self._save, limit=limit)

    def contract_offers(self) -> list[dict[str, Any]]:
        return parse_contract_offers(self._save)

    def agents(self) -> list[dict[str, Any]]:
        return parse_agents(self._save)

    def news_items(self, *, max_scan_bytes: int = 1_500_000) -> list[dict[str, Any]]:
        return parse_news_items(self._save, max_scan_bytes=max_scan_bytes)

    def analyze_section(self, section_name: str, *, max_scan_bytes: int = 500_000) -> dict[str, Any]:
        return analyze_any_section(self._save, section_name, max_scan_bytes=max_scan_bytes)

    # --- 4. Exporters ---
    def export_table(
        self,
        table_name: str,
        output_path: str | os.PathLike[str],
        *,
        fmt: str = "csv",
    ) -> int:
        rows = self.table(table_name)
        if fmt == "csv":
            return export_to_csv(rows, output_path)
        if fmt == "jsonl":
            return export_to_json(rows, output_path, jsonl=True)
        return export_to_json(rows, output_path, jsonl=False)

    def export_sqlite(
        self,
        sqlite_path: str | os.PathLike[str],
        *,
        include_season_history: bool = False,
    ) -> dict[str, int]:
        tables_map: dict[str, Any] = {}
        for tbl_name, method in ALL_28_TABLES:
            if tbl_name == "player-season-history" and not include_season_history:
                continue
            tables_map[tbl_name] = self.table(method)
        tables_map["staff_enriched"] = self.staff_enriched()
        tables_map["facilities_enriched"] = self.facilities_enriched()
        tables_map["hall_of_fame"] = self.hall_of_fame()
        tables_map["board_takeovers"] = self.board_takeovers()
        tables_map["shortlists"] = self.shortlists()
        tables_map["contract_offers"] = self.contract_offers()
        return export_tables_to_sqlite(tables_map, sqlite_path)


def open_save(
    path: str | os.PathLike[str],
    *,
    competition_names: dict[int, str] | str | os.PathLike[str] | None = None,
) -> FM26Save:
    """Open an FM26 .fm save file with full enriched & extra-section parsing support."""
    return FM26Save(path, competition_names=competition_names)


__all__ = [
    "ALL_28_TABLES",
    "ATTRIBUTE_CATEGORIES",
    "CA_POSITION_WEIGHTS_10",
    "CONTRACT_UNKNOWN_DESCRIPTIONS",
    "DUTY_ATTRIBUTE_DELTAS",
    "FM26Container",
    "FM26Save",
    "FM26_NATIONS",
    "KNOWN_CITIES",
    "OUT_OF_POSSESSION_ROLE_CATALOG",
    "RELATION_PAIR_MAP",
    "ROLE_ARCHETYPES",
    "RawSectionSummary",
    "STAFF_BLOCK40_FIELDS",
    "STAFF_DEPT_MAP",
    "STAFF_ROLE_MAP",
    "TACTICAL_ROLE_DEFINITIONS",
    "ZERO_CA_COST_ATTRIBUTES",
    "analyze_any_section",
    "analyze_player_role_breakdown",
    "build_city_map",
    "calculate_oop_role_effectiveness",
    "calculate_role_effectiveness",
    "decode_contracts_enriched",
    "decode_facilities_enriched",
    "decode_players_enriched_relations",
    "decode_staff_enriched",
    "decode_tactics_lineup",
    "diff_saves",
    "estimate_transfer_value",
    "estimate_wage_and_fees",
    "export_tables_to_sqlite",
    "export_to_csv",
    "export_to_json",
    "extract_all_game_files_summary",
    "extract_dbc_and_lnc_rules",
    "extract_editor_schemas_and_enums",
    "extract_fmf_frames",
    "extract_il2cpp_symbols_and_metadata",
    "extract_length_prefixed_strings",
    "extract_master_db_tables",
    "extract_media_interaction_trees",
    "extract_momentum_weightings",
    "extract_multi_version_database_evolution",
    "extract_oop_pitch_proximity_grid",
    "extract_permanent_edt_rules",
    "extract_pregame_people_and_history_db",
    "extract_qme_distributions",
    "extract_simulation_aux_fmf_archives",
    "extract_tactical_styles_and_presets",
    "extract_training_and_newgen_configs",
    "extract_xg_shot_models",
    "flatten_record",
    "get_role_catalog_breakdown",
    "load_engine_formulas",
    "load_official_city_map",
    "open_save",
    "parse_agents",
    "parse_board_takeovers",
    "parse_contract_offers",
    "parse_hall_of_fame",
    "parse_jsb",
    "parse_news_items",
    "parse_shortlists",
    "position_familiarity_multiplier",
    "rank_player_roles",
    "read_fmf_directory",
    "resolve_nation",
    "resolve_nation_info",
    "serialize_record",
]
