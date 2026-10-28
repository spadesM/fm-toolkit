"""Command-Line Interface for fm26save."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fm26save import FM26Save, diff_saves


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
    p_gf = sub.add_parser("game-files", help="Reverse-engineer and extract all 8 FM26 Game Installation File Systems")
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
        ],
        default="all",
        help="Which game-file system to extract",
    )
    p_gf.add_argument("--fm-dir", default=None, help="Optional custom FM26 installation directory")

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
            extract_editor_schemas_and_enums,
            extract_il2cpp_symbols_and_metadata,
            extract_master_db_tables,
            extract_media_interaction_trees,
            extract_momentum_weightings,
            extract_oop_pitch_proximity_grid,
            extract_permanent_edt_rules,
            extract_qme_distributions,
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
        }
        print(json.dumps(dispatch[args.system](args.fm_dir), ensure_ascii=False, indent=2))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
