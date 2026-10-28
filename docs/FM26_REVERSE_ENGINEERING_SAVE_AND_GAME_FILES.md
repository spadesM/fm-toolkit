# Football Manager 26 — Save Binary Architecture & Game File Reverse-Engineering Reference

> **Repository:** [`fm26save`](../)  
> **Core Modules:** [`fm26save/_core/`](../fm26save/_core/__init__.py), [`fm26save/enrichment.py`](../fm26save/enrichment.py), [`fm26save/extra_sections.py`](../fm26save/extra_sections.py), [`fm26save/container.py`](../fm26save/container.py), [`fm26save/game_files.py`](../fm26save/game_files.py)

---

## Part 1: Reverse-Engineering the `.fm` Save Container & Unknown Binary Fields

### 1.1 TADF + Zstandard Container Format (`FM26Container`)
An FM26 `.fm` save file is a custom **TADF (`0x1A 'TADF'`) multi-frame Zstandard archive** containing:
- **81 named `.dat` and `.cmt` binary sections** (indexed in the container directory header with compressed size, decompressed size, frame offset, and 2 trailing metadata integers),
- **Embedded `.apm` and `.scm` match replay/telemetry files** for recently played fixtures.
- **`game_db.dat` (`~186.9 MB` decompressed in `Project_Super_Lig.fm`):** The primary relational memory dump holding Clubs, Players, Staff, Contracts, Finances, Facilities, Stadiums, Injuries, Suspensions, and Season/Match Statistics.

---

### 1.2 Decoded "Unknown" Fields Across Core Tables

| Table | Previously Unknown / Opaque Binary Field | Reverse-Engineered Meaning & Binary Layout | Implementation |
| :--- | :--- | :--- | :--- |
| **`staff`** | `s.unknown['r4']` (`u8`) & `list_indexes` | **Exact Staff Job Role ID (`0..66`)** (`1`=Chair, `2`=Managing Director, `4`=Director of Football, `6`=Technical Director, `7`=Manager, `8`=Assistant Manager, `11`=Head of Youth Dev, `12`=Coach, `14`=Fitness Coach, `15`=GK Coach, `19`=Chief Scout, `20`=Scout, `22`=Head Physio, `26`=Physio, `33`=Loan Manager, `56`=Set Piece Coach, `64`=Chief Doctor, `66`=Recruitment Analyst) and **Department Membership (`0`=Medical, `1`=Coaching, `2`=Scouting/Recruitment)**. | [`STAFF_ROLE_MAP`](../fm26save/constants.py), [`decode_staff_enriched()`](../fm26save/enrichment.py#L98-L161) |
| **`staff`** | `block_40` (`26` bytes at `ability_base + 40`) | **All 26 Hidden Staff Coaching, Scouting, Medical & Mental Attributes** stored on FM's internal `1..100` scale (`(raw + 2) // 5` $\rightarrow$ `1..20` scale), including `Judging Player Ability`, `Judging Player Potential`, `Judging Staff Ability`, `Negotiating`, `Tactical Knowledge`, `Physiotherapy`, `Sports Science`, `Outfield/GK/Fitness Coaching`, `Working With Youngsters`, `Adaptability`, `Determination`, `People Management`, `Level of Discipline`, and `Motivating`. Extracted in a single pass inside `_core/readers/staff.py`. | [`_read_ability_block()`](../fm26save/_core/readers/staff.py#L455-L499), [`STAFF_BLOCK40_FIELDS`](../fm26save/constants.py) |
| **`contracts`** | `money_a`, `money_b`, `money_c` (`i32`) | **`money_a`** = Signing-On / Loyalty Bonus Pool (`~18.5%` of annual wage); **`money_b`** = Agent Commission Fee (`~5.2%` of annual wage); **`money_c`** = Secondary Package / Relocation Bonus. Exposed directly on `_core.Contract` as `.signing_or_loyalty_fee`, `.agent_fee`, `.package_bonus`. | [`Contract`](../fm26save/_core/models/contracts.py#L42-L90), [`decode_contracts_enriched()`](../fm26save/enrichment.py#L164-L205) |
| **`contracts`** | `e12` (`u16`), `e37`, `e38`, `e39`, `e8` (`u8`) | **`e12`** = Contract Option / Reference Year (`2025..2046`); **`e38`** = Promised Future Squad Status; **`e37`** = Playing Time Pathway Sub-Code; **`e39`** = Transfer/Loan Contract Status Flags; **`e8`** = Registration / Work Permit Status Code. | [`decode_contracts_enriched()`](../fm26save/enrichment.py#L164-L205) |
| **`facilities`** | Post-Finance Chain Block (`chain_end + 0..140`) | `offset +33` (`u32`) = **Commercial / Fanbase Index**; `offset +41` (`u32`) = **Season Ticket / Base Attendance**; `offset +45` (`u32`) = **Expected / Average Attendance**; `offset +49` (`u8`) = **Facility Block Tag (`0x02`)**; `offset +50` (`u8`) = **Corporate Facilities (`1..20`)**. | [`decode_facilities_enriched()`](../fm26save/enrichment.py#L208-L260) |
| **`players`** | Record Tail Bytes (`rec_off + 117..123`) | `offset +117` (`u8`) = **Squad Shirt Number (`1..99`, `255`=None)**; `offset +118` (`u8`) = **Recommended Current Ability (`RCA`) Peak Byte**; `offset +119` (`u8`) = **Mirrored `PA` Byte**; `offset +123` (`u8`) = **Body Type / Mesh Code (`1..5`)**. | [`decode_players_enriched_relations()`](../fm26save/enrichment.py#L263-L402) |
| **`players`** | `PersonBlock` `16`-byte Relation Entries (`sentinel = 0xFF`) | Decoded all `(kind, role)` pairs beyond `(8, 9)` Second Nationality: **`(1, 3)` Favoured Club**, **`(1, 4)` Disliked Club**, **`(3, 1)` Favoured Person** (Idol/Mentor/Friend), **`(3, 2)` Disliked Person**, **`(7, 18)` Spoken Language & Proficiency (`1..20`)**, **`(8, 70)` Home-Grown / Nation Trained Status**, **`(13, 19)` Birth/Formation Region**. | [`RELATION_PAIR_MAP`](../fm26save/constants.py), [`decode_players_enriched_relations()`](../fm26save/enrichment.py#L263-L402) |
| **`tactics`** | `tactics_man.dat` `block.selectors` (`u32[]`) | Resolved raw `pindex + 1` selectors via `player_records.position_by_pindex` into **Starting XI (`slots 1..11`)**, **Substitutes/Squad (`slots 12..26`)**, and **Set-Piece Taker Pools**. | [`decode_tactics_lineup()`](../fm26save/enrichment.py#L405-L468) |
| **`clubs.city_id`** | `0`-Based Master City Index (`0..58,348`) | Linked directly to `lang_update_db.dat` Frame `#03` (`8_2.dat`) and `client_db.dat` Frame `#02` (`table_2.dat`), resolving **100% of all 58,349 cities worldwide** with exact official names, latitude, longitude, altitude, and city attraction (`1..20`). | [`load_official_city_map()`](../fm26save/game_files.py#L698-L723), [`build_city_map()`](../fm26save/enrichment.py#L63-L97) |

---

## Part 2: Complete Reverse-Engineering of All 8 FM26 Game Installation File Systems (`fm26save/game_files.py`)

All 8 game-file systems have been decoded and implemented in [`fm26save/game_files.py`](../fm26save/game_files.py) (and exposed via CLI `python -m fm26save.cli game-files --system all`).

---

### System 1: Quick Match Engine (`QME`) Statistical Distributions (`simatch.fmf` Frames `#118` & `#119`)
- **Extractor:** [`extract_qme_distributions()`](../fm26save/game_files.py#L45-L96)
- **Binary Fix:** Cracked the `0x00` (`kind == 0`) 1-byte zero literal tag in `.jsb` binary streams ([`parse_jsb()`](../fm26save/formulas.py#L1537-L1616)), unlocking all **3,137 statistical distributions** in `qme_distribution_data.jsb`:
  - **Distribution Types:** `1,803` Poisson distributions, `630` Normal distributions, `580` Binned empirical distributions, `124` Zero distributions.
  - **Dimensions:** Indexed by `(stat_type, position, ability_window, attribute_window)` where `ability_window` partitions `CA` (`[0, 99]`, `[100, 129]`, `[130, 159]`, `[160, 200]`) and `attribute_window` partitions the weighted composite attribute score (`1..20` scale) computed from Frame `#118` (`qme_attribute_combination_weights_data.jsb`).

---

### System 2: Match Momentum Spatial Engine (`simatch.fmf` Frame `#113` — `momentum_weightings_data.jsb`)
- **Extractor:** [`extract_momentum_weightings()`](../fm26save/game_files.py#L102-L133)
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

### System 3: Out-Of-Possession (`OP*`) 2D Pitch Proximity Tactical Grid (`simatch.fmf` Frame `#115` — `oop_pitch_proximity_scores.jsb`)
- **Extractor:** [`extract_oop_pitch_proximity_grid()`](../fm26save/game_files.py#L139-L194)
- **Decoded Structure:**
  - **`118` `(Position, Role)` entries** covering `24` unique position codes (`-15..10`) and `40` unique role codes (`0..57`).
  - Each `(Position, Role)` entry contains **`24` spatial zone couples (`2,832` total coordinate intervals)** specifying `{target_position, side (-1=Left, 0=Center, +1=Right), min_score, max_score}` (`0..20` proximity score).

---

### System 4: All 11 Shot-Type xG Logistic Regression Models (`Frames #90..#100`, `v26.1.4.1`) & 101 Tactical Style Presets (`Frames #121..#222`)
- **Extractors:** [`extract_xg_shot_models()`](../fm26save/game_files.py#L200-L230), [`extract_tactical_styles_and_presets()`](../fm26save/game_files.py#L233-L299)
- **All 11 Official FM26 (`v26.1.4.1`) Expected Goals (`xG`) Logistic Regression Models:**
  $$\text{xG} = \frac{1}{1 + \exp\!\left(-\left(\beta_0 + \sum_i \beta_i x_i\right)\right)}$$

| Frame | `shot_type` | Intercept ($\beta_0$) | `norm_dist_to_goal` | `norm_players_between` | `fraction_goal_visible` | `norm_dist_closest_occluding` | `norm_height_of_ball` | `angle_shot_to_goal` | `angle_facing_to_goal` |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `#90` | **`free_kicks`** | `-0.434045` | `+0.371943` | `+0.129082` | — | `-0.708200` | — | `+0.042362` | `+0.093573` |
| `#91` | **`headers`** | `-2.852457` | `+3.169746` | `-0.418449` | `+0.005067` | `+0.004884` | `-0.127358` | `-0.030559` | `+0.072824` |
| `#92` | **`obscured_headers`** | `-3.211159` | `+3.553041` | `-0.486708` | `-0.016380` | `+0.000658` | `-0.062777` | `+0.044915` | `+0.005243` |
| `#93` | **`obscured_regular`** | `-1.437583` | `+1.501676` | `-0.670923` | `+0.070595` | `-0.114715` | — | `+0.278406` | `+0.009460` |
| `#94` | **`obscured_volleys`** | `-1.112239` | `+1.159443` | `-0.887851` | `+0.057677` | `-0.062049` | `-0.189403` | `+0.226442` | `+0.011218` |
| `#95` | **`open_goal_headers`** | `-1.590770` | `+1.672350` | `-0.640985` | `+0.153844` | `-0.058121` | `-0.109948` | `-0.033603` | `+0.084336` |
| `#96` | **`open_goal_regular`** | `-1.086731` | `+1.019833` | `-0.988886` | `+0.164382` | `-0.100821` | — | `+0.108076` | `+0.047703` |
| `#97` | **`open_goal_volleys`** | `-1.027919` | `+0.962217` | `-0.804227` | `+0.180644` | `+0.000223` | `-0.028136` | `+0.048043` | `+0.044859` |
| `#98` | **`penalties`** | `+0.119847` | — | — | — | `+0.00000019` | — | — | — |
| `#99` | **`regular`** | `-1.209590` | `+1.311615` | `-0.464878` | `-0.204429` | `-0.113698` | — | `+0.175101` | `+0.094974` |
| `#100` | **`volleys`** | `-1.126503` | `+1.218222` | `-0.387561` | `-0.122370` | `-0.084118` | `-0.148597` | `+0.129495` | `+0.059656` |

- **10 Tactical Style Templates (`Frame #192` XML) + `101` Binary Dual-Formation Presets (`Frames #121..#222`):**
  - `Control Possession`, `Gegenpress`, `Tiki-Taka`, `Vertical Tiki-Taka`, `Wing Play`, `Route One`, `Fluid Counter-Attack`, `Direct Counter-Attack`, `Catenaccio`, and `Park the Bus`.

---

### System 5: 106 Internal Database XML Schemas & Master FourCC Enums (`shared/data/editor.fmf`)
- **Extractor:** [`extract_editor_schemas_and_enums()`](../fm26save/game_files.py#L305-L410)
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
  - Plus **`32` Master Enum Groups (`Frame #82` — `db enums.xml`)**.

---

### System 6: Pre-Game Master Databases (`client_db.dat`, `lang_update_db.dat`, `server_db.dat`) & Permanent `.edt` Rules
- **Extractors:** [`extract_master_db_tables()`](../fm26save/game_files.py#L726-L819), [`load_official_city_map()`](../fm26save/game_files.py#L698-L723), [`extract_permanent_edt_rules()`](../fm26save/game_files.py#L822-L853)
- **Master Lookup Table Record Counts (`lang_update_db.dat` + `client_db.dat`):**
  - **`96,343` Clubs (`8_3.dat` + `table_3.dat`)** with `uid`, `name`, `short_name`, `six_letter_name`, `three_letter_name`, `alt_short_name`, and `nickname`.
  - **`58,349` Cities (`8_2.dat` + `table_2.dat` `43`-byte records)** with 0-based `city_id` (`0..58,348`, matching `.fm` save `club.city_id` 1-to-1!), `uid`, `name`, `latitude` (`float32` at `+3`), `longitude` (`float32` at `+7`), `attraction_1_20` (`u8` at `+11`), `nation_id` (`u32` at `+12`), `local_region_id` (`u32` at `+16`), `altitude_raw` (`u16` at `+20`), `inhabitants_bracket` (`u8` at `+22`), and `weather_profile_id` (`u16` at `+27`):
    - Example `city_id = 7998` (**Ankara**): `uid = 1301230`, `lat = 39.92077`, `lon = 32.85411`, `attraction = 19/20`, `nation_id = 173` (Turkey), `region_id = 253`
    - Example `city_id = 8002` (**Trabzon**): `uid = 1301234`, `lat = 41.00145`, `lon = 39.71780`, `attraction = 12/20`, `nation_id = 173` (Turkey), `region_id = 251`, `altitude = 121m`
  - **`51,118` Stadiums (`8_21.dat` + `table_21.dat`)**
  - **`7,973` Competitions (`8_25.dat` + `table_25.dat`)**
  - **`3,884` Awards (`8_0.dat` + `table_0.dat`)**
  - **`2,527` Local Regions (`8_47.dat` + `table_47.dat`)**
  - **`1,683` Derbies (`8_18.dat` + `table_18.dat`)**
  - **`286` Stage Names (`8_23.dat` + `table_23.dat`)**
  - **`251` Nations (`8_9.dat` + `table_9.dat`)**
  - **`180` Media Sources (`8_7.dat` + `table_7.dat`)**
  - **`136` Injuries (`8_6.dat` + `table_6.dat`)**
  - **`6` International Agreements (`8_56.dat` + `table_56.dat`: `EU`, `EEA`, `OACPS`, `Overseas Territories`, `Mercosur`, `Andean Community`)**
- **16 Permanent `.edt` / `.ddt` Rule Files (`shared/data/database/db/2620/edt/permanent/`):**
  - `sugardaddy.edt` (`14` clubs), `eng_youth_grades.edt` (`95` clubs), `valid_takeovers_only.edt` (`69` rules), `transfer_embargo.edt` (`35` rules), `support_staff.edt` (`12` rules), `alliteration_adjectives.edt` (`123` rules), etc.

---

### System 7: Press Conference Trees (`media.fmf`), Training Schedules (`training.fmf`) & Newgen Demographics (`simatchshared.fmf`)
- **Extractors:** [`extract_media_interaction_trees()`](../fm26save/game_files.py#L859-L911), [`extract_training_and_newgen_configs()`](../fm26save/game_files.py#L914-L961)
- **Empirical Totals:**
  - **`media.fmf` (`649` XML frames):** `3,934` press conference / player interaction question definitions (`QID_*`), `pcaa` alternative answer branches, and `barl` backroom advice condition blocks.
  - **`training.fmf` (`Frames #1..#3`):** `62` training schedule categories, `164` full-time standard weekly training schedules (`day1..day7` × `session1, session2, extra`), and `136` youth/part-time weekly schedules (`300` total schedule templates).
  - **`simatchshared.fmf` (`Frame #74`):** `135` newgen hair length/colour demographic probability rules by ethnicity/region tag.

---

### System 8: IL2CPP Metadata & Native Symbol Table (`il2cpp.usym` & `global-metadata.dat`)
- **Extractor:** [`extract_il2cpp_symbols_and_metadata()`](../fm26save/game_files.py#L967-L1016)
- **Empirical Totals:**
  - **`fm_Data/il2cpp_data/il2cpp.usym` (`38.54 MB`):** Magic `sym-`, Version `2`, containing **`1,593,548` native symbol/line mapping records** for `GameAssembly.dll`.
  - **`fm_Data/il2cpp_data/Metadata/global-metadata.dat` (`15.58 MB`):** Sanity `0xFAB11BAF`, IL2CPP Metadata Version `31`, with `106+` extracted C# engine symbols (`EventFmxMatchFocusSelectInPossessionType`, `EventFmxMatchFocusSelectOutOfPossessionType`, `EventFmxRecruitmentFocusCurrentAbilityUpdated`, `EventFmxRecruitmentFocusPotentialAbilityUpdated`, `EventFmxRequestQuickMatch`, `FMMatchMomentumChart`, `FMPlayerRating`, `DebugTransferValueReference`, `AcceptAllOffersOverAskingPrice`, etc.).
