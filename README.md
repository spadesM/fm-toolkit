# `fm-toolkit` — Football Manager Save Parser, Reverse-Engineering Toolkit, Engine Formula Analyzer & Exporter

**`fm-toolkit`** is a standalone, zero-external-dependency Python library and CLI toolkit for parsing, decoding, diffing, analyzing, and exporting **Football Manager (`.fm`) save files** and **installation archives (`.fmf`, `.dat`, `.jsb`, `.edt`, `.usym`)**.

---

## Key Capabilities

1. **All 28 Structured Save Database Tables (`fm26save._core`):**
   - Self-contained binary readers for `players`, `contracts`, `suspensions`, `injuries`, `injury-types`, `player-season-stats`, `player-season-history`, `player-match-stats`, `clubs`, `managed-clubs`, `finances`, `sponsorships`, `facilities`, `stadiums`, `affiliates`, `staff`, `staff-lists`, `tactics`, `set-pieces`, `training`, `mentoring`, `job-vacancies`, `competitions`, `stages`, `league-tables`, `fixtures`, `competition-rules`, and `transfer-windows`.
2. **Decoded "Unknown" & Hidden Binary Fields (`fm26save.enrichment`):**
   - **100% Official Nation (`251` Nations) & City (`58,349` Cities) Resolution:** Combines `FM26_NATIONS` with all `58,349` 0-based `city_id` records from `lang_update_db.dat` (`8_2.dat`) and `client_db.dat` (`table_2.dat`).
   - **Hidden Staff Attributes (`block_40`) & Job Role IDs (`r4`):** Decodes all `26` hidden coaching, scouting, medical, and mental attributes (`1..100` internal scale and `1..20` displayed scale) plus exact job titles (`r4` codes `0..66`) and department memberships (`Medical`, `Coaching`, `Scouting`).
   - **Contract Bonus & Option Fields:** Decodes `money_a` (`signing_or_loyalty_fee`), `money_b` (`agent_fee`), `money_c` (`package_bonus`), `e12` (`option_or_reference_year`), `e38` (Promised Squad Status), `e37`, `e39`, and `e8`.
   - **Post-Finance Club Attendance & Commercial Metrics:** Decodes `offset +33` (Commercial/Fanbase Index), `+41` (Season Ticket Holders), `+45` (Expected/Average Attendance), and `+50` (Corporate Facilities `1..20`).
   - **Player Record Tail Bytes & Full `PersonBlock` Relationships:** Decodes `offset +117` (Squad Shirt Number), `+118` (Recommended Current Ability `RCA`), `+119` (Mirrored `PA`), `+123` (Body Type), and all `16`-byte `(kind, role)` relation pairs (`(1,3)` Favoured Club, `(1,4)` Disliked Club, `(3,1)` Favoured Person, `(3,2)` Disliked Person, `(7,18)` Spoken Language & Proficiency, `(8,9)` Second Nationality, `(8,70)` Home-Grown Status, `(13,19)` Birth Region).
   - **Tactical Starting XI, Substitutes & Set-Piece Selectors:** Resolves `tactics_man.dat` `block.selectors` (`pindex + 1`) to exact player records.
3. **81-Section `TADF` Container Unpacker & Extra `.dat` / `.cmt` Parsers (`fm26save.container`, `fm26save.extra_sections`):**
   - Dedicated binary parsers for `hall_of_fame.dat`, `board_takeover_manager.dat`, `shortlist_man.dat`, `contract_man.dat`, `agent_manager.dat`, `news.dat`, plus universal binary inspector `analyze_any_section()`.
4. **Official Engine Formulas & 6-Dimensional Tactical Role Breakdowns (`fm26save.formulas`):**
   - Evaluates player effectiveness across **50 In-Possession roles (`93` Role × Duty variants)**, **39 Out-Of-Possession (`OP*`) roles**, **Dual-Role (`0.55 × IP + 0.45 × OOP`) combinations**, **10 Position Lines**, **6 Tactical Duties**, and **11 Tactical Archetypes**, plus `CA`/`PA` positional cost weights, Transfer Market Value estimation, and Wage/Agent/Signing Fee models.
5. **All 8 Game Installation File Reverse-Engineering Systems (`fm26save.game_files`):**
   - Extracts Quick Match Engine (`QME`) statistical distributions (`3,137` entries), Match Momentum spatial rules (`48` entries), Out-Of-Possession 2D Pitch Proximity grids (`118` Role entries × `24` zones = `2,832` intervals), all `11` Shot-Type `xG` Logistic Regression models (`v26.1.4.1`), `10` Tactical Style XML templates & `101` binary `.tac`/`.cat` presets, `106` internal `editor.fmf` XML schemas (`2,405` FourCC fields + `32` enum groups), Pre-Game Master Databases (`96,343` Clubs, `58,349` Cities with exact Lat/Lon/Attraction, `51,118` Stadiums, `7,973` Competitions, `3,884` Awards, `2,527` Regions, `1,683` Derbies, `136` Injuries) & `16` `.edt` rule files, `3,934` Press Conference questions (`media.fmf`) & `300` Training Schedules (`training.fmf`), and `1,593,548` IL2CPP native symbols (`il2cpp.usym` & `global-metadata.dat`).
6. **Byte-Level Save Differ (`fm26save.diff`) & Multi-Format Exporters (`fm26save.exporter`):**
   - Diff any two `.fm` saves across all 81 compressed sections (`diff_saves()`) and export any table or full save to **CSV (UTF-8-BOM)**, **JSON**, **JSONL**, or **SQLite (`.db`)**.

---

## Documentation & Reverse-Engineering Reports (`docs/`)

All technical documentation and empirical reports are written in **English** under [`docs/`](./docs):

| Document | Contents |
| :--- | :--- |
| **[`docs/FM26_REVERSE_ENGINEERING_METHODOLOGY_AND_FILE_TREE.md`](./docs/FM26_REVERSE_ENGINEERING_METHODOLOGY_AND_FILE_TREE.md)** | Step-by-step reverse-engineering methodology (TADF/Zstd framing, `.jsb` binary opcodes, FourCC alignment, differential save analysis, `client_db.dat` record cracking) and **complete annotated file trees** for the game installation directory, `.fm` save container, and library architecture. |
| **[`docs/FM26_REVERSE_ENGINEERING_SAVE_AND_GAME_FILES.md`](./docs/FM26_REVERSE_ENGINEERING_SAVE_AND_GAME_FILES.md)** | Complete specification of all decoded "unknown" save binary fields and empirical tables for all 8 reverse-engineered game installation systems. |
| **[`docs/FM26_ENGINE_FORMULAS_AND_CALCULATIONS.md`](./docs/FM26_ENGINE_FORMULAS_AND_CALCULATIONS.md)** | Exact mathematical formulations for Role Suitability, `CA`/`PA` attribute cost weights, Transfer Value, Wage/Bonus/Agent Fee demands, Expected Goals (`xG`), Match Rating (`6.6` baseline), and Quick Match Engine (`QME`). |
| **[`docs/FM26_TACTICAL_ROLES_AND_BREAKDOWNS.md`](./docs/FM26_TACTICAL_ROLES_AND_BREAKDOWNS.md)** | Complete 6-dimensional breakdown of all 50 In-Possession roles (`93` Role+Duty variants), 39 Out-Of-Possession (`OP*`) roles, Dual-Role combinations, Duties, and 11 Archetypes. |
| **[`docs/FM26_SAVE_DATABASE_SCHEMA_AND_81_SECTIONS.md`](./docs/FM26_SAVE_DATABASE_SCHEMA_AND_81_SECTIONS.md)** | Complete catalog of all 28 structured tables, their columns/types, and all 81 `.dat` / `.cmt` Zstandard sections inside an `.fm` save file. |

---

## Installation

```bash
pip install -e .
```

---

## Python API Quickstart

```python
from fm26save import (
    open_save,
    diff_saves,
    resolve_nation,
    extract_all_game_files_summary,
    extract_master_db_tables,
)

save_path = r"path/to/MyCareerSave.fm"

with open_save(save_path) as sv:
    print("In-Game Date:", sv.info.game_date, "| Build:", sv.info.build)

    # 1. Official Nation (251) & City (58,349) Name Resolution
    print("Nation 173 ->", resolve_nation(173, lang="en"))  # Turkiye
    print("City 8002  ->", sv.city_name(8002))              # Trabzon

    # 2. Enriched Staff Decoder (Resolved r4 Job Role + 26 Hidden block_40 Attributes)
    ts_staff = sv.staff_enriched(club_uid=1879)
    for st in ts_staff[:5]:
        print(st["name"], "->", st["role_en"], "| JPA/JPP/Physio (1-20):", st["coaching_and_scouting_20"])

    # 3. 6-Dimensional Tactical Role Breakdown (In-Possession, OP*, Dual-Role, Duty, Archetype)
    players = [p for p in sv.table("players") if p.ability]
    best_player = max(players, key=lambda p: p.ability.current)
    role_report = sv.player_role_breakdown(best_player, top_n_per_group=5)
    print("Top Dual Role (IP + OOP):", role_report["top_dual_combinations"][0])

    # 4. Enriched Player Relationships (Favoured Clubs/People, Languages, RCA, Shirt Number)
    ts_rels = sv.players_enriched_relations(club_uid=1879, limit=10)

    # 5. Starting XI, Substitutes & Set-Piece Lineup (tactics_man.dat)
    lineups = sv.tactics_lineup()

    # 6. Extra Container Sections (Hall of Fame, Board Takeovers, Shortlists, Contract Offers, News)
    hof = sv.hall_of_fame(limit=20)
    takeovers = sv.board_takeovers()
    shortlist = sv.shortlists(limit=50)
    offers = sv.contract_offers()

    # 7. Export Full Save to SQLite (.db), CSV, JSON, or JSONL
    sv.export_sqlite("career_export.db")

# 8. Extract Official Game Installation Files (All 8 Systems)
summary = extract_all_game_files_summary()
master_db = extract_master_db_tables(sample_limit=10)
```

---

## Command-Line Interface (CLI) Usage

```bash
# 1. Inspect save metadata and list all 81 Zstd container sections
fm-toolkit info "MyCareerSave.fm"

# 2. Run enriched unknown-field decoders (staff | contracts | facilities | relations | lineup)
fm-toolkit enriched "MyCareerSave.fm" --kind staff --club-uid 1879
fm-toolkit enriched "MyCareerSave.fm" --kind relations --club-uid 1879

# 3. Multi-dimensional tactical role & duty breakdown (In-Possession, OP*, Dual-Role, Archetypes)
fm-toolkit roles "MyCareerSave.fm" --player "Onuralp" --top 5
fm-toolkit roles --catalog

# 4. Extract any of the 8 Game Installation File Systems
#    (all | qme | momentum | oop_grid | xg | styles | schemas | master_db | edt | media | training | il2cpp)
fm-toolkit game-files --system all
fm-toolkit game-files --system master_db

# 5. Parse extra .dat/.cmt sections (hall_of_fame | takeovers | shortlists | offers | agents | news)
fm-toolkit extra "MyCareerSave.fm" --section takeovers
fm-toolkit extra "MyCareerSave.fm" --section shortlists --limit 20

# 6. Byte-diff two .fm save files across all 81 sections
fm-toolkit diff "career_before.fm" "career_after.fm"

# 7. Export a table to CSV/JSON/JSONL or the entire save to SQLite (.db)
fm-toolkit export "MyCareerSave.fm" --table players --out players.csv
fm-toolkit export "MyCareerSave.fm" --table sqlite --out full_save.db
```
