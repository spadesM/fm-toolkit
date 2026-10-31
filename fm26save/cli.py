"""Command-Line Interface for fm26save."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fm26save import FM26Editor, FM26Save, diff_saves


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        prog="fm26save",
        description="FM26 (.fm) Save Parser, Unknown-Field Decoder, 81-Section Unpacker & Save Differ",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # 1. info
    p_info = sub.add_parser("info", help="Show save metadata and 81 Zstd sections")
    p_info.add_argument("save", help="Path to .fm save file")

    # 2. enriched
    p_enr = sub.add_parser("enriched", help="Run enriched decoders (staff, contracts, facilities, relations, lineup)")
    p_enr.add_argument("save", help="Path to .fm save file")
    p_enr.add_argument(
        "--kind",
        choices=["staff", "contracts", "facilities", "relations", "lineup"],
        default="staff",
    )
    p_enr.add_argument("--club-uid", type=int, default=None)
    p_enr.add_argument("--limit", type=int, default=25)

    # 3. extra
    p_ext = sub.add_parser("extra", help="Parse extra .dat/.cmt sections (hall_of_fame, takeovers, shortlists, offers, agents, news, analyze)")
    p_ext.add_argument("save", help="Path to .fm save file")
    p_ext.add_argument(
        "--section",
        default="hall_of_fame",
        help="hall_of_fame | takeovers | shortlists | offers | agents | news | <any section name>",
    )
    p_ext.add_argument("--limit", type=int, default=25)

    # 4. diff
    p_diff = sub.add_parser("diff", help="Diff two .fm save files across all 81 sections")
    p_diff.add_argument("save_a", help="First .fm save file")
    p_diff.add_argument("save_b", help="Second .fm save file")
    p_diff.add_argument("--section", default=None, help="Optional specific section to byte-diff")

    # 5. export
    p_exp = sub.add_parser("export", help="Export a table or full SQLite database")
    p_exp.add_argument("save", help="Path to .fm save file")
    p_exp.add_argument("--table", default="players", help="Table name or 'sqlite'")
    p_exp.add_argument("--out", required=True, help="Output file path (.csv, .json, .jsonl, .db)")

    # 6. roles
    p_rol = sub.add_parser("roles", help="Multi-dimensional FM26 Role Breakdown (In-Possession, OP*, Duty, Archetype)")
    p_rol.add_argument("save", nargs="?", default=None, help="Optional path to .fm save file (omit with --catalog)")
    p_rol.add_argument("--player", default=None, help="Player name substring or UID")
    p_rol.add_argument("--catalog", action="store_true", help="Dump full FM26 In-Possession & OP* Role Catalog")
    p_rol.add_argument("--top", type=int, default=5, help="Top N roles per breakdown group")

    # 7. game-files
    p_gf = sub.add_parser("game-files", help="Reverse-engineer and extract all 12 FM26 Game Installation File Systems")
    p_gf.add_argument(
        "--system",
        choices=[
            "all",
            "qme",
            "momentum",
            "oop_grid",
            "xg",
            "styles",
            "schemas",
            "master_db",
            "edt",
            "media",
            "training",
            "il2cpp",
            "people_db",
            "dbc_lnc",
            "aux_fmfs",
            "multi_version",
        ],
        default="all",
        help="Which game-file system to extract",
    )
    p_gf.add_argument("--fm-dir", default=None, help="Optional custom FM26 installation directory")

    # 8. edit
    p_edit = sub.add_parser(
        "edit",
        help="Manipulate players, contracts, clubs, finances, stadiums, staff, injuries & tables and save to a new .fm file",
    )
    p_edit.add_argument("save", help="Source .fm save file (never modified in place)")
    p_edit.add_argument("--out", required=True, help="Output .fm save file path")
    p_edit.add_argument("--validate", action="store_true", help="Run full reader validation on the saved .fm file")
    p_edit.add_argument("--game-date", default=None, help="Set in-game date (YYYY-MM-DD)")
    p_edit.add_argument("--player", default=None, help="Player UID, pindex, or name")
    p_edit.add_argument("--max-player", action="store_true", help="Max out player CA/PA (200), attributes (20), fitness & feet")
    p_edit.add_argument("--ca", type=int, default=None, help="Player Current Ability (1..200)")
    p_edit.add_argument("--pa", type=int, default=None, help="Player Potential Ability (1..200)")
    p_edit.add_argument("--reputation", type=int, default=None, help="Player reputation (1..10000)")
    p_edit.add_argument("--condition", type=int, default=None, help="Player condition (1..10000)")
    p_edit.add_argument("--sharpness", type=int, default=None, help="Player match sharpness (1..10000)")
    p_edit.add_argument("--transfer-value", type=int, default=None, help="Player transfer value")
    p_edit.add_argument("--age", type=int, default=None, help="Player age")
    p_edit.add_argument("--height", type=int, default=None, help="Player height in cm")
    p_edit.add_argument("--squad-number", type=int, default=None, help="Player squad shirt number (1..99)")
    p_edit.add_argument("--attr", action="append", default=[], help="Attribute override KEY=VAL (1..20), repeatable")
    p_edit.add_argument("--pos", action="append", default=[], help="Position override POS=VAL (1..20), repeatable")
    p_edit.add_argument("--heal", action="store_true", help="Heal all active injuries for --player")
    p_edit.add_argument("--clear-suspensions", action="store_true", help="Clear all suspensions for --player")
    p_edit.add_argument("--wage", type=int, default=None, help="Player weekly contract wage")
    p_edit.add_argument("--contract-end", default=None, help="Player contract expiry date (YYYY-MM-DD)")
    p_edit.add_argument("--squad-status", type=int, default=None, help="Player contract squad status code (0..15)")
    p_edit.add_argument("--club", default=None, help="Club UID, index, or name")
    p_edit.add_argument("--club-reputation", type=int, default=None, help="Club reputation (1..10000)")
    p_edit.add_argument("--balance", type=int, default=None, help="Club bank balance")
    p_edit.add_argument("--transfer-budget", type=int, default=None, help="Club transfer budget (allocated & remaining)")
    p_edit.add_argument("--wage-budget", type=int, default=None, help="Club weekly wage budget")
    p_edit.add_argument("--corporate-facilities", type=int, default=None, help="Club corporate facilities (1..20)")
    p_edit.add_argument("--stadium", default=None, help="Stadium UID, name, or owner club name")
    p_edit.add_argument("--capacity", type=int, default=None, help="Stadium total capacity")
    p_edit.add_argument("--all-seater", type=int, default=None, help="Stadium all-seater capacity")
    p_edit.add_argument("--staff", default=None, help="Staff UID or name")
    p_edit.add_argument("--max-staff", action="store_true", help="Max out staff CA/PA (200) and all 26 attributes (20)")
    p_edit.add_argument("--staff-ca", type=int, default=None, help="Staff Current Ability (1..200)")
    p_edit.add_argument("--staff-pa", type=int, default=None, help="Staff Potential Ability (1..200)")
    p_edit.add_argument("--table-team", type=int, default=None, help="Team ID in league table")
    p_edit.add_argument("--table-won", type=int, default=None, help="League table matches won")
    p_edit.add_argument("--table-drawn", type=int, default=None, help="League table matches drawn")
    p_edit.add_argument("--table-lost", type=int, default=None, help="League table matches lost")
    p_edit.add_argument("--table-gf", type=int, default=None, help="League table goals for")
    p_edit.add_argument("--table-ga", type=int, default=None, help="League table goals against")
    p_edit.add_argument("--table-points", type=int, default=None, help="League table points")

    # 9. repack
    p_repack = sub.add_parser("repack", help="Losslessly repack an .fm save container (optionally replacing raw sections)")
    p_repack.add_argument("save", help="Source .fm save file")
    p_repack.add_argument("--out", required=True, help="Output .fm save file")
    p_repack.add_argument(
        "--replace-section",
        action="append",
        default=[],
        help="Replace section with raw file: SECTION_NAME=PATH_TO_BIN (repeatable)",
    )
    p_repack.add_argument("--validate", action="store_true", help="Validate repacked .fm save")

    args = parser.parse_args(argv)

    if args.cmd == "info":
        with FM26Save(args.save) as sv:
            info = sv.info
            entries = sv.container.list_entries()
            print(
                json.dumps(
                    {
                        "file": Path(args.save).name,
                        "game": info.game,
                        "build": info.build,
                        "game_date": str(info.game_date),
                        "sections_count": len(entries),
                        "sections": [
                            {
                                "name": e.full_name,
                                "compressed": e.compressed_size,
                                "decompressed": e.decompressed_size,
                                "ratio": e.compression_ratio,
                            }
                            for e in entries[:25]
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        return 0

    if args.cmd == "enriched":
        with FM26Save(args.save) as sv:
            if args.kind == "staff":
                data = sv.staff_enriched(club_uid=args.club_uid)[: args.limit]
            elif args.kind == "contracts":
                data = sv.contracts_enriched(club_uid=args.club_uid, limit=args.limit)
            elif args.kind == "facilities":
                data = sv.facilities_enriched()[: args.limit]
            elif args.kind == "relations":
                data = sv.players_enriched_relations(club_uid=args.club_uid, limit=args.limit)
            else:
                data = sv.tactics_lineup()
            print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "extra":
        with FM26Save(args.save) as sv:
            sec = args.section
            if sec == "hall_of_fame":
                data = sv.hall_of_fame(limit=args.limit)
            elif sec == "takeovers":
                data = sv.board_takeovers()[: args.limit]
            elif sec == "shortlists":
                data = sv.shortlists(limit=args.limit)
            elif sec == "offers":
                data = sv.contract_offers()[: args.limit]
            elif sec == "agents":
                data = sv.agents()[: args.limit]
            elif sec == "news":
                data = sv.news_items()[: args.limit]
            else:
                data = sv.analyze_section(sec)
            print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "diff":
        res = diff_saves(args.save_a, args.save_b, specific_section=args.section)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "export":
        with FM26Save(args.save) as sv:
            out_path = Path(args.out)
            if args.table == "sqlite" or out_path.suffix.lower() in (".db", ".sqlite"):
                counts = sv.export_sqlite(out_path)
                print(json.dumps({"sqlite_exported": str(out_path), "tables": counts}, ensure_ascii=False, indent=2))
            else:
                fmt = out_path.suffix.lower().lstrip(".") or "csv"
                cnt = sv.export_table(args.table, out_path, fmt=fmt)
                print(json.dumps({"exported": str(out_path), "table": args.table, "rows": cnt}, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "roles":
        from fm26save.formulas import get_role_catalog_breakdown

        if args.catalog or not args.save:
            print(json.dumps(get_role_catalog_breakdown(), ensure_ascii=False, indent=2))
            return 0
        with FM26Save(args.save) as sv:
            players = sv.table("players")
            q = (args.player or "").strip().lower()
            target = None
            for p in players:
                if not p.ability:
                    continue
                if q and (str(p.uid) == q or (p.name and q in p.name.lower())):
                    target = p
                    break
            if target is None:
                target = max((p for p in players if p.ability), key=lambda x: x.ability.current)
            print(json.dumps(sv.player_role_breakdown(target, top_n_per_group=args.top), ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "game-files":
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
        )

        dispatch = {
            "all": extract_all_game_files_summary,
            "qme": lambda d: extract_qme_distributions(d, sample_limit=25),
            "momentum": extract_momentum_weightings,
            "oop_grid": extract_oop_pitch_proximity_grid,
            "xg": extract_xg_shot_models,
            "styles": extract_tactical_styles_and_presets,
            "schemas": extract_editor_schemas_and_enums,
            "master_db": lambda d: extract_master_db_tables(d, sample_limit=20),
            "edt": extract_permanent_edt_rules,
            "media": lambda d: extract_media_interaction_trees(d, max_frames=60),
            "training": extract_training_and_newgen_configs,
            "il2cpp": extract_il2cpp_symbols_and_metadata,
            "people_db": extract_pregame_people_and_history_db,
            "dbc_lnc": extract_dbc_and_lnc_rules,
            "aux_fmfs": extract_simulation_aux_fmf_archives,
            "multi_version": extract_multi_version_database_evolution,
        }
        print(json.dumps(dispatch[args.system](args.fm_dir), ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "edit":
        with FM26Editor(args.save) as ed:
            applied: list[dict[str, object]] = []
            if args.game_date:
                applied.append(ed.set_game_date(args.game_date))

            if args.player:
                p_key: int | str = int(args.player) if str(args.player).isdigit() else args.player
                if args.max_player:
                    applied.append(ed.max_out_player(p_key))
                attr_map: dict[str, int] = {}
                for item in args.attr:
                    k, v = item.split("=", 1)
                    attr_map[k.strip()] = int(v.strip())
                pos_map: dict[str, int] = {}
                for item in args.pos:
                    k, v = item.split("=", 1)
                    pos_map[k.strip()] = int(v.strip())
                if any(
                    x is not None
                    for x in (
                        args.ca,
                        args.pa,
                        args.reputation,
                        args.condition,
                        args.sharpness,
                        args.transfer_value,
                        args.age,
                        args.height,
                        args.squad_number,
                    )
                ) or attr_map or pos_map:
                    applied.append(
                        ed.edit_player(
                            p_key,
                            current_ability=args.ca,
                            potential_ability=args.pa,
                            home_reputation=args.reputation,
                            current_reputation=args.reputation,
                            world_reputation=args.reputation,
                            condition=args.condition,
                            match_sharpness=args.sharpness,
                            transfer_value=args.transfer_value,
                            age=args.age,
                            height_cm=args.height,
                            squad_number=args.squad_number,
                            attributes=attr_map or None,
                            positions=pos_map or None,
                        )
                    )
                if any(x is not None for x in (args.wage, args.contract_end, args.squad_status)):
                    applied.append(
                        ed.edit_player_contract(
                            p_key,
                            wage=args.wage,
                            end_date=args.contract_end,
                            squad_status=args.squad_status,
                        )
                    )
                if args.heal:
                    applied.append(ed.heal_player_injuries(p_key))
                if args.clear_suspensions:
                    applied.append(ed.edit_player_suspensions(p_key, clear_all=True))

            if args.club:
                c_key: int | str = int(args.club) if str(args.club).isdigit() else args.club
                if args.club_reputation is not None:
                    applied.append(ed.edit_club(c_key, reputation=args.club_reputation))
                if any(x is not None for x in (args.balance, args.transfer_budget, args.wage_budget)):
                    applied.append(
                        ed.edit_club_finances(
                            c_key,
                            balance=args.balance,
                            transfer_budget_allocated=args.transfer_budget,
                            transfer_budget_remaining=args.transfer_budget,
                            wage_budget_weekly=args.wage_budget,
                        )
                    )
                if args.corporate_facilities is not None:
                    applied.append(
                        ed.edit_club_facilities(c_key, corporate_facilities=args.corporate_facilities)
                    )

            if args.stadium and (args.capacity is not None or args.all_seater is not None):
                s_key: int | str = int(args.stadium) if str(args.stadium).isdigit() else args.stadium
                applied.append(
                    ed.edit_stadium(
                        s_key,
                        capacity=args.capacity,
                        all_seater_capacity=args.all_seater,
                    )
                )

            if args.staff:
                st_key: int | str = int(args.staff) if str(args.staff).isdigit() else args.staff
                if args.max_staff:
                    applied.append(ed.max_out_staff(st_key))
                elif args.staff_ca is not None or args.staff_pa is not None:
                    applied.append(
                        ed.edit_staff(
                            st_key,
                            current_ability=args.staff_ca,
                            potential_ability=args.staff_pa,
                        )
                    )

            if args.table_team is not None:
                applied.append(
                    ed.edit_league_table_row(
                        args.table_team,
                        won=args.table_won,
                        drawn=args.table_drawn,
                        lost=args.table_lost,
                        goals_for=args.table_gf,
                        goals_against=args.table_ga,
                        points=args.table_points,
                    )
                )

            save_summary = ed.save(args.out, validate_output=args.validate)
            print(
                json.dumps(
                    {"save_summary": save_summary, "edits": applied},
                    ensure_ascii=False,
                    indent=2,
                )
            )
        return 0

    if args.cmd == "repack":
        with FM26Editor(args.save) as ed:
            for item in args.replace_section:
                sec_name, bin_path = item.split("=", 1)
                ed.set_section_bytes(sec_name.strip(), Path(bin_path.strip()).read_bytes())
            res = ed.save(args.out, validate_output=args.validate)
            print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
