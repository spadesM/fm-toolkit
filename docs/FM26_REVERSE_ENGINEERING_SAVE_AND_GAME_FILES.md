# Football Manager 26 — Save Binary Architecture & Game File Reverse-Engineering Reference

> **Repository:** [`fm-toolkit`](../)  
> **Core Modules:** [`fm26save/_core/`](../fm26save/_core/__init__.py), [`fm26save/enrichment.py`](../fm26save/enrichment.py), [`fm26save/extra_sections.py`](../fm26save/extra_sections.py), [`fm26save/container.py`](../fm26save/container.py), [`fm26save/game_files.py`](../fm26save/game_files.py)

---

## Part 1: Reverse-Engineering the `.fm` Save Container & Unknown Binary Fields

### 1.1 `\x02\x01fmf.` + Zstandard Trailer Directory Container Format (`FM26Container`)
An FM26 `.fm` save file is a **`\x02\x01fmf.` (`02 01 66 6D 66 2E`) multi-frame Zstandard archive** ([`_core/_container.py`](../fm26save/_core/_container.py#L32-L49), [`FM26Container`](../fm26save/container.py)) containing:
- **26-Byte Header:** Magic `\x02\x01fmf.` at bytes `0..6`, `<Q` (`u64`) `directory_offset` at bytes `9..17` pointing to the Zstandard-compressed trailer directory at the end of the file, and `<I` (`u32`) `entry_count` at bytes `22..26`.
- **81 named `.dat` and `.cmt` binary sections** (indexed in the compressed trailer directory, where each entry ends with a 40-byte tail of `5 × u64`: `compressed_size`, `decompressed_size`, `frame_offset`, and 2 trailing metadata integers; decompressed database table streams begin with inner magic `03 01 'tad.'`),
- **Embedded `.apm` and `.scm` match replay/telemetry files** for recently played fixtures.
- **`game_db.dat` (`~88–187 MB` decompressed):** The primary relational memory dump holding Clubs, Players, Staff, Contracts, Finances, Facilities, Stadiums, Injuries, Suspensions, and Season/Match Statistics.

---

### 1.2 Decoded "Unknown" Fields Across Core Tables

| Table | Previously Unknown / Opaque Binary Field | Reverse-Engineered Meaning & Binary Layout | Implementation |
| :--- | :--- | :--- | :--- |
| **`staff`** | `s.unknown['r4']` (`u8`) & `list_indexes` | **Staff Job Role ID (`0..88`)** (`2`=Assistant Manager, `6`=Director/Board, `8`=Managing Director, `10`=Youth/Reserve Manager, `12`=Physio, `14`=Scout, `16`=Manager, `20`=Coach, `22`=Fitness Coach, `26`=Goalkeeping Coach, `34`=Youth Coach, `38`=Youth Physio, `40`=Youth Sports Scientist, `44`=Chief Scout, `46`=Head Physio/Club Doctor, `48`=Head of Sports Science, `50`=Sports Scientist, `58`=Director of Football, `60`=Head of Youth Development, `62`=Loan Manager/Technical Director, `64`=Set Piece Coach, `80`=Performance Analyst, `86`=Recruitment Analyst, `88`=Chief Recruitment Analyst) and **Department Membership (`0`=Medical, `1`=Coaching, `2`=Scouting/Recruitment)**. | [`STAFF_ROLE_MAP`](../fm26save/constants.py#L283-L309), [`decode_staff_enriched()`](../fm26save/enrichment.py#L105-L170) |
| **`staff`** | `block_40` (`26` bytes at `ability_base + 40`) | **26 Hidden Staff `1..100` (`5`-step) Attribute Slots** (`(raw + 2) // 5` $\rightarrow$ `1..20` scale). The 26-byte block is 100% verified as a `1..100` attribute array extracted inside `_core/readers/staff.py`; individual slot names in `STAFF_BLOCK40_FIELDS` are heuristic role-cluster mappings. | [`_read_ability_block()`](../fm26save/_core/readers/staff.py#L455-L499), [`STAFF_BLOCK40_FIELDS`](../fm26save/constants.py#L315-L342) |
| **`contracts`** | `money_a`, `money_b`, `money_c` (`i32`) | **`money_a`** = Signing-On / Loyalty Bonus Pool (`61%` non-zero; `5.0%` unconditional median of annual wage across all contracts, `18.5%` conditional median among non-zero contracts); **`money_b`** = Agent Commission Fee (`29%` non-zero; `5.2%` conditional median among non-zero contracts); **`money_c`** = Secondary Package Bonus (`2.6%` non-zero). Exposed on `_core.Contract` as `.signing_or_loyalty_fee`, `.agent_fee`, `.package_bonus`. | [`Contract`](../fm26save/_core/models/contracts.py#L266-L286), [`decode_contracts_enriched()`](../fm26save/enrichment.py#L173-L216) |
| **`contracts`** | `e12` (`u16`), `e37`, `e38`, `e39`, `e8` (`u8`) | **`e12`** = Contract Option / Reference Year (`1900` is FM's null-date sentinel `(1, 1900)` in `~39%` of rows and is mapped to `None`; active years `2012..2030+` in `~61%`); **`e38`** = Promised Future Squad Status; **`e37`** = Playing Time Pathway Sub-Code; **`e39`** = Contract Status Flags; **`e8`** = Registration Code. | [`decode_contracts_enriched()`](../fm26save/enrichment.py#L173-L216) |
| **`facilities`** | Post-Finance Chain Block (`chain_end + 0..140`) | `offset +33` (`u32`) = **Commercial / Fanbase Index**; `offset +41` (`u32`) = **Season Ticket / Base Attendance**; `offset +45` (`u32`) = **Expected / Average Attendance**; `offset +49` (`u8`) = **Facility Block Tag (`0x02`)**; `offset +50` (`u8`) = **Corporate Facilities (`1..20`)**. | [`decode_facilities_enriched()`](../fm26save/enrichment.py#L217-L270) |
| **`players`** | Record Tail Bytes (`rec_off + 117..123`) | In builds where `raw_b119 == player.ability.potential` (e.g. `26.3.2`), `offset +117` (`u8`) = **Squad Shirt Number (`1..99`, `255`=None)**, `+118` (`u8`) = **Peak/RCA Byte**, `+119` (`u8`) = **Mirrored `PA` Byte**. Validated against `PA` so shifted tail offsets on earlier builds (`26.1.0`/`26.1.1`) return `None`. | [`decode_players_enriched_relations()`](../fm26save/enrichment.py#L316-L327) |
| **`players`** | `PersonBlock` `16`-byte Relation Entries (`sentinel = 0xFF`) | Decodes all `(kind, role)` pairs (`ref` `u32` at `+0`, `kind` `u8` at `+10`, `role` `u8` at `+11`, `qualifier` `u8` at `+12`, `0xFF` at `+15`): **`(1, 72)` Home-Grown Club** (`club_index`), **`(1, 3)` Favoured Club** (`club_index`), **`(1, 4)` Disliked Club** (`club_index`), **`(3, 1)` Favoured Person** (`ref = pindex`, resolved via `player_records.position_by_pindex`), **`(3, 2)` Disliked Person** (`ref = pindex`), **`(7, 18)` Spoken Language & Proficiency**, **`(8, 9)` Second Nationality**, **`(8, 70)` Home-Grown Nation**, **`(4, 67)` Birth/Local Region**. | [`RELATION_PAIR_MAP`](../fm26save/constants.py#L347-L363), [`decode_players_enriched_relations()`](../fm26save/enrichment.py#L272-L428) |
| **`tactics`** | `tactics_man.dat` `block.selectors` (`u32[]`) | Resolves raw `pindex + 1` selectors via `player_records.position_by_pindex` into **Starting XI (`slots 1..11`)**, **Substitutes/Squad (`slots 12..26`)**, and **Set-Piece Taker Pools**. | [`decode_tactics_lineup()`](../fm26save/enrichment.py#L431-L494) |
| **`clubs.city_id`** | `0`-Based Master City Index (`0..58,348`) | Linked directly to `lang_update_db.dat` Frame `#03` (`8_2.dat`) and `client_db.dat` Frame `#02` (`table_2.dat`), resolving **100% of all 58,349 cities worldwide** with exact official names, latitude, longitude, altitude (`ft`), city attraction (`1..20`), and `100%` verified `db_city_id`/`db_uid` at offset `+32`/`+36`. | [`load_official_city_map()`](../fm26save/game_files.py#L734-L761), [`build_city_map()`](../fm26save/enrichment.py#L63-L97) |

---

## Part 2: Complete Reverse-Engineering of All 8 FM26 Game Installation File Systems (`fm26save/game_files.py`)

All 8 game-file systems have been decoded and implemented in [`fm26save/game_files.py`](../fm26save/game_files.py) (and exposed via CLI `fm-toolkit game-files --system all`).

---

### System 1: Quick Match Engine (`QME`) Statistical Distributions (`simatch.fmf` Frames `#119` & `#120`) & Player Match Ratings (`Frame #118`)
- **Extractor:** [`extract_qme_distributions()`](../fm26save/game_files.py#L53-L119)
- **Decoded Frames:**
  - **`Frame #119` (`qme_distribution_data.jsb`, `585,551` B):** Contains **3,137 statistical distributions** (`1,257` `normal` distributions, `1,300` `binned` empirical distributions, and `580` `zero` distributions) indexed by `(stat_type, position, ability_window, attribute_window)`.
  - **`Frame #120` (`qme_stat_relevant_attribute_data.jsb`, `1,608` B):** Maps all **`22` simulated `stat_type` keys** (`passes_attempted`, `pass_completion`, `key_passes`, `crosses_attempted`, `cross_completion`, `tackles_attempted`, `tackle_completion`, `interceptions`, `blocks`, `clearances`, `headers_attempted`, `header_completion`, `dribbles`, `shots`, `shots_on_target_ratio`, `fouls_made`, `fouls_won`, `offsides`, `yellow_cards`, `red_cards`, `mistakes`, `distance_covered`) to their exact `relevant_attributes` list.
  - **`Frame #118` (`player_ratings_data.jsb`, `348,584` B):** Contains **6 versions** (`v24.2.5.1..v26.4.10.1`) of the Player Match Rating engine (`start_value = 6700` = **`6.70`** across all 6 versions, `40` `RolePosition` lookup entries mapped to `30` role coefficient tables × `52` match actions).

---

### System 2: Match Momentum Spatial Engine (`simatch.fmf` Frame `#113` — `momentum_weightings_data.jsb`)
- **Extractor:** [`extract_momentum_weightings()`](../fm26save/game_files.py#L125-L157)
- **Empirical Rules (`48` Spatial Event Rules across `7` Match Event Types):**

| Match Event (`CBE_EVENT_TYPE`) | Vertical Zone (`FOURTH_SIXTH`) | Vertical Zone (`FIVTH_SIXTH` — Left / Central / Right) | Vertical Zone (`FINAL_SIXTH` — Left / Central / Right) |
| :--- | :---: | :---: | :---: |
| **`CBE_TOUCH`** | `+2 / +2 / +2` | `+2 / +3 / +2` | `+2 / +4 / +2` |
| **`CBE_END_PASS_COMPLETED`** | `+2 / +2 / +2` | `+2 / +4 / +3` | `+3 / +5 / +3` |
| **`CBE_END_SHOT_MISSED_TARGET`** | — | `+5 / +10 / +5` | `+5 / +20 / +5` |
| **`CBE_END_SHOT_SAVED`** | — | `+5 / +10 / +5` | `+10 / +30 / +10` |
| **`CBE_END_SHOT_BLOCKED`** | — | `+5 / +10 / +5` | `+10 / +30 / +10` |
| **`CBE_END_SHOT_HIT_WOODWORK`** | — | `+5 / +15 / +5` | `+10 / +35 / +10` |
| **`CBE_END_SHOT_GONE_IN` (Goal)** | — | `+10 / +15 / +10` | **`+25 / +50 / +25`** |

---

### System 3: Out-Of-Possession (`OP*`) Role Attribute Scoring (`Frame #114`) & 2D Pitch Proximity Grid (`Frame #115`)
- **Extractor:** [`extract_oop_pitch_proximity_grid()`](../fm26save/game_files.py#L163-L227)
- **Decoded Structures:**
  - **`Frame #114` (`oop_attributes_scoring.jsb`, `2,115` B):** **`39` Out-Of-Possession `RolePosition` bitmasks** ($2^0..2^{45}$) mapped to their official engine `ATTRIBUTES` ID lists (`[20, 21, 24, 32, 33, 35, 44, 47, 51, 52, 53, 60, 68]`).
  - **`Frame #115` (`oop_pitch_proximity_scores.jsb`, `95,708` B):** **`118` `(Position, Role)` entries** covering `24` unique position codes (`-15..10`) and `40` unique role codes (`0..57`), each containing **`24` spatial zone couples (`2,832` total coordinate intervals)** specifying `{target_position, side (-1=Left, 0=Center, +1=Right), min_score, max_score}` (`0..20` proximity score).

---

### System 4: All 11 Shot-Type xG Logistic Regression Models (`Frames #002..#100`, 9 Versions up to `v26.1.4.1`), 101 Tactical Presets (`Frames #121..#222`), & AI Team Selection (`Frame #223`)
- **Extractors:** [`extract_xg_shot_models()`](../fm26save/game_files.py#L233-L280), [`extract_tactical_styles_and_presets()`](../fm26save/game_files.py#L283-L354), [`load_engine_formulas()`](../fm26save/formulas.py#L1678-L1735)
- **9 Engine Versions (`Frames #002..#100`):** `v23.1.1.9`, `v23.2.0.0`, `v23.3.0.1`, `v24.1.2.3`, `v24.2.2.2`, `v25.0.0.0`, `v26.0.0.2`, `v26.1.1.1`, and active **`v26.1.4.1` (`Frames #090..#100`)**.
- **Active `v26.1.4.1` Expected Goals (`xG`) Models (`1e7` Fixed-Point Scale):**
  $$\text{xG} = \frac{1}{1 + \exp\!\left(-\left(\beta_0 + \sum_i \beta_i x_i\right)\right)}$$

| Frame | `shot_type` | Raw Intercept (`int32`) | Intercept $\beta_0$ (`÷ 1e7`) | `norm_dist_to_goal` (`÷ 1e7`) | `norm_players_between` (`÷ 1e7`) | `fraction_goal_visible` (`÷ 1e7`) | `norm_dist_closest_occ` (`÷ 1e7`) | `norm_height_of_ball` (`÷ 1e7`) | `angle_shot_to_goal` (`÷ 1e7`) | `angle_facing_to_goal` (`÷ 1e7`) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `#90` | **`free_kicks`** | `-4,340,446` | `-0.434045` | `+3.719432` | `+1.290821` | — | `-7.081997` | — | `+0.423622` | `+0.935728` |
| `#91` | **`headers`** | `-28,524,565` | `-2.852457` | `+31.697463` | `-4.184486` | `+0.050670` | `+0.048844` | `-1.273580` | `-0.305586` | `+0.728238` |
| `#92` | **`obscured_headers`** | `-32,111,593` | `-3.211159` | `+35.530408` | `-4.867079` | `-0.163795` | `+0.006584` | `-0.627774` | `+0.449147` | `+0.052431` |
| `#93` | **`obscured_regular`** | `-14,375,833` | `-1.437583` | `+15.016758` | `-6.709227` | `+0.705953` | `-1.147154` | — | `+2.784056` | `+0.094596` |
| `#94` | **`obscured_volleys`** | `-11,122,386` | `-1.112239` | `+11.594430` | `-8.878511` | `+0.576773` | `-0.620493` | `-1.894032` | `+2.264416` | `+0.112183` |
| `#95` | **`open_goal_headers`** | `-15,907,703` | `-1.590770` | `+16.723500` | `-6.409850` | `+1.538443` | `-0.581208` | `-1.099482` | `-0.336031` | `+0.843360` |
| `#96` | **`open_goal_regular`** | `-10,867,306` | `-1.086731` | `+10.198332` | `-9.888864` | `+1.643823` | `-1.008213` | — | `+1.080761` | `+0.477030` |
| `#97` | **`open_goal_volleys`** | `-10,279,187` | `-1.027919` | `+9.622170` | `-8.042267` | `+1.806438` | `+0.002231` | `-0.281359` | `+0.480432` | `+0.448593` |
| `#98` | **`penalties`** | `+11,984,673` | `+1.198467` | — | — | — | `0.000000` | — | — | — |
| `#99` | **`regular`** | `-12,095,895` | `-1.209590` | `+13.116154` | `-4.648781` | `-2.044286` | `-1.136978` | — | `+1.751011` | `+0.949736` |
| `#100` | **`volleys`** | `-11,265,032` | `-1.126503` | `+12.182221` | `-3.875611` | `-1.223699` | `-0.841180` | `-1.485970` | `+1.294951` | `+0.596560` |

- **10 Tactical Style Templates (`Frame #192` XML) + `101` Binary Dual-Formation Presets (`Frames #121..#222`):**
  - `Control Possession`, `Gegenpress`, `Tiki-Taka`, `Vertical Tiki-Taka`, `Wing Play`, `Route One`, `Fluid Counter-Attack`, `Direct Counter-Attack`, `Catenaccio`, and `Park the Bus`.
- **AI Team Selection Weights (`Frame #223` — `weights.jsb`, `6,547` B):**
  - `4` `TEAM_PICKING_STYLE` profiles (`TPS_FIRST_TEAM_PICKING`, `TPS_SEMI_RESERVE_PICKING`, `TPS_SLIGHTLY_RESERVE_PICKING`, `TPS_TOTAL_RESERVE_PICKING`) × `40` `TSF_*` weights.

---

### System 5: 106 Internal Database XML Schemas & Master FourCC Enums (`shared/data/editor.fmf`)
- **Extractor:** [`extract_editor_schemas_and_enums()`](../fm26save/game_files.py#L360-L462)
- **Decoded Entity FourCC Property Schemas (`2,405` Total Properties across 13 Core Entities):**
  - **`club.xml` (`Frame #32`, `club`):** `595` FourCC fields
  - **`person.xml` (`Frame #49`, `pers`):** `396` FourCC fields
  - **`nation.xml` (`Frame #45`, `natc`):** `376` FourCC fields
  - **`comp.xml` (`Frame #33`, `comp`):** `297` FourCC fields
  - **`player.xml` (`Frame #50`, `play`):** `291` FourCC fields (e.g., `PShN` Shirt Name, `PCAB` Current Ability `0..200`, `PPAB` Potential Ability `-10..200`, `PRCA` Recommended CA)
  - **`non_player.xml` (`Frame #46`, `nnpl`):** `150` FourCC fields
  - **`weather.xml` (`Frame #56`, `weat`):** `94` FourCC fields
  - **`stadium.xml` (`Frame #52`, `stad`):** `76` FourCC fields
  - **`contract_offer.xml` (`Frame #35`, `CntF`):** `66` FourCC fields
  - **`injury.xml` (`Frame #39`, `inju`):** `29` FourCC fields
  - Plus **`444` Master Enum Groups (`Frame #82` — `db enums.xml`)**.

---

### System 6: Pre-Game Master Databases (`client_db.dat` 32 Frames, `lang_update_db.dat` 401 Frames, `server_db.dat` 78 Frames) & Permanent `.edt` Rules
- **Extractors:** [`extract_master_db_tables()`](../fm26save/game_files.py#L764-L893), [`load_official_city_map()`](../fm26save/game_files.py#L734-L761), [`extract_permanent_edt_rules()`](../fm26save/game_files.py#L896-L929)
- **Archive Frame Counts:**
  - **`client_db.dat`:** `32` Zstd frames (`31` `table_*.dat` data tables + `1` directory index).
  - **`lang_update_db.dat`:** `401` Zstd frames (**`25` languages × `16` localized tables** + `1` directory index; frames `#00..#15` are Language `8` = English `8_*.dat`).
  - **`server_db.dat`:** `78` Zstd frames (`77` data tables + `1` directory index).
- **Master Lookup Table Record Counts (`lang_update_db.dat` + `client_db.dat`):**
  - **`96,343` Clubs (`8_3.dat` + `table_3.dat`)** with `uid`, `name`, `short_name`, `six_letter_name`, `three_letter_name`, `alt_short_name`, and `nickname`.
  - **`58,349` Cities (`8_2.dat` + `table_2.dat` `43`-byte records)** with 0-based `city_id` (`0..58,348`, matching `.fm` save `club.city_id` 1-to-1!), `uid`, `name`, `latitude` (`float32` at `+3`), `longitude` (`float32` at `+7`), `attraction_1_20` (`u8` at `+11`), `nation_id` (`u32` at `+12`), `local_region_id` (`u32` at `+16`), `altitude_ft` (`u16` in feet at `+20`), `inhabitants_bracket` (`u8` at `+22`), `weather_profile_id` (`u16` at `+27`), `db_city_id` (`u32` at `+32`, verified `58,349 / 58,349` = `100%`), and `db_uid` (`u32` at `+36`, verified `58,349 / 58,349` = `100%`):
    - Example `city_id = 7998` (**Ankara**): `uid = 1301230`, `lat = 39.92077`, `lon = 32.85411`, `attraction = 19/20`, `nation_id = 173` (Türkiye), `region_id = 253`, `altitude_ft = 2853` (`~870 m`)
    - Example `city_id = 8002` (**Trabzon**): `uid = 1301234`, `lat = 41.00145`, `lon = 39.71780`, `attraction = 12/20`, `nation_id = 173` (Türkiye), `region_id = 251`, `altitude_ft = 121`
  - **`51,118` Stadiums (`8_21.dat` + `table_21.dat`)**
  - **`7,973` Competitions (`8_25.dat` + `table_25.dat`)**
  - **`3,884` Awards (`8_0.dat` + `table_0.dat`)**
  - **`2,527` Local Regions (`8_47.dat` + `table_47.dat`)**
  - **`1,683` Derbies (`8_18.dat` + `table_18.dat`)**
  - **`286` Stage Names (`8_23.dat` + `table_23.dat`)**
  - **`251` Nations (`8_9.dat` + `table_9.dat`)** (`226` active nation IDs `1..249` mapped in `constants.FM26_NATIONS`)
  - **`180` Media Sources (`8_7.dat` + `table_7.dat`)**
  - **`136` Injuries (`8_6.dat` + `table_6.dat`)**
  - **`6` International Agreements (`8_56.dat` + `table_56.dat`: `EU`, `EEA`, `OACPS`, `Overseas Territories`, `Mercosur`, `Andean Community`)**
- **16 Permanent `.edt` / `.ddt` Rule Files (`shared/data/database/db/2620/edt/permanent/`):**
  - `sugardaddy.edt` (`14` clubs), `eng_youth_grades.edt` (`95` clubs), `valid_takeovers_only.edt` (`69` rules), `transfer_embargo.edt` (`35` rules), `support_staff.edt` (`12` rules), `alliteration_adjectives.edt` (`123` rules), etc.

---

### System 7: Press Conference Trees (`media.fmf`), Training Schedules (`training.fmf`) & Newgen Demographics (`simatchshared.fmf`)
- **Extractors:** [`extract_media_interaction_trees()`](../fm26save/game_files.py#L935-L982), [`extract_training_and_newgen_configs()`](../fm26save/game_files.py#L985-L1032)
- **Empirical Totals:**
  - **`media.fmf` (`649` XML frames + `1` directory):** `3,934` press conference / player interaction question definitions (`QID_*`), `pcaa` alternative answer branches, and `barl` backroom advice condition blocks.
  - **`training.fmf` (`Frames #1..#4`):** `training_item_effects.jsb` (`Frame #1`), `164` full-time standard weekly training schedules (`Frame #2`, `day1..day7` × `session1, session2, extra`), `136` youth/part-time weekly schedules (`Frame #3`, `300` total schedule templates), and `training_sessions_weights.jsb` (`Frame #4`).
  - **`simatchshared.fmf` (`Frame #74`):** `135` newgen hair length/colour demographic probability rules by ethnicity/region tag.

---

### System 8: IL2CPP Metadata & Native Symbol Table (`il2cpp.usym` & `global-metadata.dat`)
- **Extractor:** [`extract_il2cpp_symbols_and_metadata()`](../fm26save/game_files.py#L1038-L1093)
- **Empirical Totals:**
  - **`fm_Data/il2cpp_data/il2cpp.usym` (`38.54 MB`):** Magic `sym-`, Version `2`, containing **`1,593,548` native symbol/line mapping records** for `GameAssembly.dll`.
  - **`fm_Data/il2cpp_data/Metadata/global-metadata.dat` (`15.58 MB`):** Sanity `0xFAB11BAF`, IL2CPP Metadata Version `31`, with `106+` extracted C# engine symbols (`EventFmxMatchFocusSelectInPossessionType`, `EventFmxMatchFocusSelectOutOfPossessionType`, `EventFmxRecruitmentFocusCurrentAbilityUpdated`, `EventFmxRecruitmentFocusPotentialAbilityUpdated`, `EventFmxRequestQuickMatch`, `FMMatchMomentumChart`, `FMPlayerRating`, `DebugTransferValueReference`, `AcceptAllOffersOverAskingPrice`, etc.).
