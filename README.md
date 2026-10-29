# `fm-toolkit` — Football Manager Save Parser, Reverse-Engineering Toolkit, Engine Formula Analyzer & Exporter

**`fm-toolkit`** is a Python library and CLI toolkit for parsing, decoding, diffing, analyzing, and exporting **Football Manager (`.fm`) save files** and **installation archives (`.fmf`, `.dat`, `.jsb`, `.edt`, `.usym`)**.

---

## Key Capabilities

1. **All 28 Structured Save Database Tables (`fm26save._core`):**
   - Built upon a vendored and extended copy of **[`rhiever/fmsave` v0.6.0](https://github.com/rhiever/fmsave)** (MIT License), providing binary readers for `players`, `contracts`, `suspensions`, `injuries`, `injury-types`, `player-season-stats`, `player-season-history`, `player-match-stats`, `clubs`, `managed-clubs`, `finances`, `sponsorships`, `facilities`, `stadiums`, `affiliates`, `staff`, `staff-lists`, `tactics`, `set-pieces`, `training`, `mentoring`, `job-vacancies`, `competitions`, `stages`, `league-tables`, `fixtures`, `competition-rules`, and `transfer-windows`.
2. **Decoded "Unknown" & Hidden Binary Fields (`fm26save.enrichment`):**
   - **Official Nation (`251` in `lang_update_db.dat` / `226` in `FM26_NATIONS`) & City (`58,349` Cities) Resolution:** Combines `FM26_NATIONS` with all `58,349` 0-based `city_id` records from `lang_update_db.dat` (`8_2.dat`) and `client_db.dat` (`table_2.dat`).
   - **Hidden Staff Attributes (`block_40`) & Job Role IDs (`r4`):** Decodes all `26` hidden `1..100` (`5`-step) staff attribute slots in `block_40` (mapped to `1..20` displayed scale via role-cluster heuristics) plus job role codes (`r4` in `constants.STAFF_ROLE_MAP`) and department memberships (`Medical`, `Coaching`, `Scouting`).
   - **Contract Bonus & Option Fields:** Decodes `money_a` (`signing_or_loyalty_fee`), `money_b` (`agent_fee`), `money_c` (`package_bonus`), `e12` (`option_or_reference_year`, with `1900` null-date sentinel handled), `e38` (Promised Squad Status), `e37`, `e39`, and `e8`.
   - **Post-Finance Club Attendance & Commercial Metrics:** Decodes `offset +33` (Commercial/Fanbase Index), `+41` (Season Ticket Holders), `+45` (Expected/Average Attendance), and `+50` (Corporate Facilities `1..20`).
   - **Player `PersonBlock` Relationships:** Resolves all `16`-byte `(kind, role)` relation pairs (`(1,72)` Home-Grown Club, `(1,3)` Favoured Club, `(1,4)` Disliked Club, `(3,1)` Favoured Person via `pindex` lookup, `(3,2)` Disliked Person via `pindex` lookup, `(7,18)` Spoken Language & Proficiency, `(8,9)` Second Nationality, `(8,70)` Home-Grown Nation, `(4,67)` Birth/Local Region).
   - **Tactical Starting XI, Substitutes & Set-Piece Selectors:** Resolves `tactics_man.dat` `block.selectors` (`pindex + 1`) to exact player records.
3. **81-Section `\x02\x01fmf.` Container Unpacker & Extra `.dat` / `.cmt` Parsers (`fm26save.container`, `fm26save.extra_sections`):**
   - Unpacks the 26-byte `\x02\x01fmf.` container header and Zstandard trailer directory (`5 × u64` entry tail), with binary parsers/scanners for `hall_of_fame.dat`, `board_takeover_man.dat`, `shortlist_man.dat`, `contract_man.dat`, `agent_manager.dat`, `news.dat`, plus universal binary inspector `analyze_any_section()`.
4. **Official `.fmf` Engine Formulas & Empirical Save Estimators (`fm26save.formulas`):**
   - **Official Extracted `.fmf` / `.jsb` Models (`simatch.fmf`, `tables.fmf`, `training.fmf`):** 11 Shot-Type `xG` Logistic Regression models across 9 engine versions (`23_1_1_9`..`26_1_4_1`), Player Match Ratings (`start_value = 6.70`, 6 versions, 30 role coefficient profiles), Out-Of-Possession (`OP*`) `RolePosition` attribute bitmasks (`Frame #114`, `39` roles) & 2D Pitch Proximity grids (`Frame #115`, `118` entries), Match Momentum (`Frame #113`, `48` spatial rules), Quick Match Engine (`QME`) statistical distributions (`Frame #119`, `3,137` Poisson/Normal/Binned/Zero entries) & relevant attributes (`Frame #120`, `22` stat types), AI Team Selection Weights (`Frame #223`, `4` `TPS_*` profiles × `40` `TSF_*` factors), Height-to-Jumping/Aerial Reach tables (`tables.fmf`), and Training Item Effects (`training.fmf`).
   - **Heuristic & Empirical Save-Fitted Models:** Evaluates player suitability across **50 In-Possession roles (`93` Role × Duty variants)**, **39 Out-Of-Possession (`OP*`) roles**, **Dual-Role (`0.55 × IP + 0.45 × OOP`) combinations**, **10 Position Lines**, **6 Tactical Duties**, and **11 Tactical Archetypes**, plus empirical `CA`/`PA` positional weights and 80/20 train/test-validated log-linear OLS estimators for Transfer Value and Weekly Wage.
5. **All 12 Game Installation File Reverse-Engineering Systems (`fm26save.game_files`):**
   - **Systems 1–4 (`simatch.fmf`):** Quick Match Engine (`QME`) statistical distributions (`3,137` entries) & stat-relevant attributes (`22` stat types), Match Momentum spatial rules (`48` entries), Out-Of-Possession Role Attribute Scoring (`39` bitmasks) & 2D Pitch Proximity grids (`118` Role entries × `24` zones = `2,832` intervals), all `11` Shot-Type `xG` Logistic Regression models (`9` versions up to `26_1_4_1`), Frame `#116` Pre-Computed Ball Physics Table (`simatch/physics/ball/ball_physics_22_0_5_0.bta`, `3.28 MB`), `10` Tactical Style XML templates, `90` `.tac` (`\x03\x01cat.`) dual-formation presets & `11` `.stra` (`\x03\x01rts.`) strategy files (`Frames #121..#222`), and AI Team Selection Weights (`Frame #223`).
   - **System 5 (`editor.fmf`):** All `105` internal XML schema files (`#000..#104`), `444` Master Enum Groups (`#082`), and `2,405` FourCC entity properties.
   - **System 6 (`client_db.dat`, `lang_update_db.dat`, `server_db.dat`, `.edt`):** `100%` record-aligned joins across `client_db.dat` (`31` tables), `lang_update_db.dat` (`25` languages × `16` tables), and `server_db.dat` (`77` tables) — decoding **`96,343` Clubs** (reputation, facilities `1..20`, kits, year founded), **`58,349` Cities** (exact Lat/Lon, Altitude in feet, Attraction `1..20`, `100%` verified `city_id`/`uid` at `+32`), **`51,118` Stadiums** (capacity, seating, expansion, pitch dimensions in decimeters, build year, Lat/Lon, owner club), **`7,973` Competitions**, **`3,884` Awards**, **`2,527` Local Regions**, **`1,683` Derbies**, **`251` Nations** (reputation, FIFA points, development state, economic factor, EU status), **`136` Injuries** (min/extra days, sharpness drop %, occurrence ratio, severity tier, contagious flag at `+31`), **`7` Continents**, **`988,091` Person Name Pool records** (`294,103` First + `599,900` Last + `94,088` Common names), and `16` permanent `.edt` rule files.
   - **System 7 (`media.fmf`, `training.fmf`, `simatchshared.fmf`):** `3,934` Press Conference questions (`media.fmf`), `300` Weekly Training Schedules (`training.fmf`), `74` RGB kit/hair/skin palette & crowd config frames (`simatchshared.fmf` `#000..#073`), and `135` Newgen appearance demographic rules (`#074`).
   - **System 8 (`il2cpp.usym`, `global-metadata.dat`):** `1,593,548` native symbol mappings and extracted C# engine symbols.
   - **System 9 (`basic_people_db.dat`, `people_db.dat`, `pl_hist_index/id/dt.dat`):** `100%` deterministic walk of all **`723,010` pre-game people** (`532,742` Players, `174,504` Staff, `9,872` Officials, `4,410` Player/Staff, `1,482` Agents), negative `PA` wonderkid distributions (`6` `PA = -10` and `22` `PA = -95` wonderkids with resolved names, clubs, nations, height/weight, and **8 hidden personality attributes** from `people_db.dat`), and the **3-file singly-linked list career history** (`522,004` indexed players and `4,344,855` × `44`-byte season rows in `pl_hist_dt.dat`).
   - **System 10 (`sicomps/comps.dbc`, `2620/dbc/*.dbc`, `2620/lnc/all/*.lnc`):** `1,442` `\x03\x01cbd.` binary TLV competition rule sets (`74.46 MB` decompressed), database `.dbc` patches, and `41` `.lnc` licensing/name-override files (`1,500+` directives).
   - **System 11 (`filters.fmf`, `achievements.fmf`, `leaderboards.fmf`, `settings.fmf`, `store.fmf`, `profanity_filter.fmf`, `languages.fmf`):** `445` `<record>` scouting/search filters (`2` XML files), `50` `<record>` achievement rules (`1` XML file), `28` `<record>` leaderboards (`1` XML file), `10` `<record>` preference schemas (`9` XML files), `3` `<record>` store configs (`2` XML files), `2` profanity filter wordlists, and `205.61 MB` master localization archive.
   - **System 12 (`shared/data/database/db/2300..2620` — Multi-Version Evolution):** Walks `100%` of all **`9` database versions** (`2300`, `2310`, `2320`, `2330`, `2340`, `2400`, `2430`, `2600`, `2620` — **`4,945,820` total person records** across `83`-byte FM23/FM24 structs and `84`-byte FM26 structs), comparing entity growth, `-10`/`-95` wonderkid cohorts, and player `CA`/`PA` trajectories across FM23 $\rightarrow$ FM24 $\rightarrow$ FM26.
6. **Byte-Level Save Differ (`fm26save.diff`) & Multi-Format Exporters (`fm26save.exporter`):**
   - Diff any two `.fm` saves across all 81 compressed sections (`diff_saves()`) and export any table or full save to **CSV (UTF-8-BOM)**, **JSON**, **JSONL**, or **SQLite (`.db`)**.

---

## Documentation & Reverse-Engineering Reports (`docs/`)

All technical documentation and empirical reports are written in **English** under [`docs/`](./docs):

| Document | Contents |
| :--- | :--- |
| **[`docs/FM26_REVERSE_ENGINEERING_METHODOLOGY_AND_FILE_TREE.md`](./docs/FM26_REVERSE_ENGINEERING_METHODOLOGY_AND_FILE_TREE.md)** | Step-by-step reverse-engineering methodology (`\x02\x01fmf.` trailer directory & Zstd framing, `.jsb` binary opcodes, FourCC alignment, differential save analysis, `client_db.dat` 43-byte city record layout) and **complete annotated file trees** for the game installation directory, `.fm` save container, and library architecture. |
| **[`docs/FM26_INTERNAL_GAME_LOGICS_AND_MECHANICS.md`](./docs/FM26_INTERNAL_GAME_LOGICS_AND_MECHANICS.md)** | Deep-dive reference into **22 core internal simulation logics** extracted from the engine files: Youth Intake & Newgen Pipeline (`NYRt`, `Crcb`, `Cytv`, `Cyfb`, `HOYD`, Height-to-Jumping caps), AI Team Selection (`4` `TPS_*` × `40` `TSF_*` weights), Match Rating (`6.70` base & `52` action deltas), Weekly Training (`44` sessions & `62` item effects), Player Progression & Coaching Stars, `xG`/`Momentum`/`QME`, `OOP` 24-zone grid, Medical/Injuries (`136`), Sugar Daddy/Takeovers/Work Permits, and Dynamics/Mentoring. |
| **[`docs/FM26_REVERSE_ENGINEERING_SAVE_AND_GAME_FILES.md`](./docs/FM26_REVERSE_ENGINEERING_SAVE_AND_GAME_FILES.md)** | Complete specification of all decoded "unknown" save binary fields and empirical tables for all 12 reverse-engineered game installation systems. |
| **[`docs/FM26_ENGINE_FORMULAS_AND_CALCULATIONS.md`](./docs/FM26_ENGINE_FORMULAS_AND_CALCULATIONS.md)** | Exact mathematical formulations for Official `.fmf` Engine Models (`xG`, Match Rating `6.70` baseline, Momentum, `QME`, `OP*` attribute bitmasks & proximity grids, AI Team Selection weights) and Empirical/Heuristic Save Models (Role Suitability, `CA`/`PA` attribute weights, Transfer Value & Wage OLS). |
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
    print("Top Dual Role (IP + OOP):", role_report["best_dual_role_combinations"][0])

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

# 8. Extract Official Game Installation Files (All 12 Systems)
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

# 4. Extract any of the 12 Game Installation File Systems
#    (all | qme | momentum | oop_grid | xg | styles | schemas | master_db | edt | media | training | il2cpp | people_db | dbc_lnc | aux_fmfs | multi_version)
fm-toolkit game-files --system all
fm-toolkit game-files --system master_db
fm-toolkit game-files --system people_db
fm-toolkit game-files --system multi_version

# 5. Parse extra .dat/.cmt sections (hall_of_fame | takeovers | shortlists | offers | agents | news)
fm-toolkit extra "MyCareerSave.fm" --section takeovers
fm-toolkit extra "MyCareerSave.fm" --section shortlists --limit 20

# 6. Byte-diff two .fm save files across all 81 sections
fm-toolkit diff "career_before.fm" "career_after.fm"

# 7. Export a table to CSV/JSON/JSONL or the entire save to SQLite (.db)
fm-toolkit export "MyCareerSave.fm" --table players --out players.csv
fm-toolkit export "MyCareerSave.fm" --table sqlite --out full_save.db
```
---

## License & Legal Disclaimer

- **License:** Distributed under the **[MIT License](./LICENSE)**. The 28-table core database reader layer in [`fm26save/_core/`](./fm26save/_core) is adapted and extended from **[`rhiever/fmsave` v0.6.0](https://github.com/rhiever/fmsave)** (MIT License).
- **Disclaimer:** This repository is an **unofficial open-source research, interoperability, and analytics toolkit** created for educational purposes. It is **not** affiliated with, endorsed by, or sponsored by **Sports Interactive** or **SEGA**. *Football Manager*, *Sports Interactive*, and *SEGA* are registered trademarks of their respective owners. No proprietary game binaries, assets, or save files are distributed in this repository.
