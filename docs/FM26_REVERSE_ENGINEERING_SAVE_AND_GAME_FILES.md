# Football Manager 26 — Save Binary Architecture & Game File Reverse-Engineering Reference

> **Repository:** [`fm-toolkit`](../)  
> **Core Modules:** [`fm26save/_core/`](../fm26save/_core/__init__.py), [`fm26save/enrichment.py`](../fm26save/enrichment.py), [`fm26save/extra_sections.py`](../fm26save/extra_sections.py), [`fm26save/container.py`](../fm26save/container.py), [`fm26save/game_files.py`](../fm26save/game_files.py)

---

## Part 1: Reverse-Engineering the `.fm` Save Container & Unknown Binary Fields

### 1.1 `\x02\x01fmf.` + Zstandard Trailer Directory Container Format (`FM26Container`)
An FM26 `.fm` save file is a **`\x02\x01fmf.` (`02 01 66 6D 66 2E`) multi-frame Zstandard archive** ([`_core/_container.py`](../fm26save/_core/_container.py#L32-L49), [`FM26Container`](../fm26save/container.py)) containing:
- **26-Byte Header:** Magic `\x02\x01fmf.` at bytes `0..6`, `<Q` (`u64`) `directory_offset` at bytes `9..17` (`trailer_offset = 9 + directory_offset`) pointing to the Zstandard-compressed trailer directory at the end of the file, and `<I` (`u32`) `content_end_rel` at bytes `22..26`.
- **81 named `.dat` (`64`) and `.cmt` (`17`) binary sections** (indexed in the compressed trailer directory alongside `.apm`/`.scm` telemetry files, where each entry ends with a 40-byte tail of `5 × u64`: `rel_offset`, `compressed_size`, `decompressed_size`, and 2 trailing metadata integers; `44` decompressed `.dat` sections begin with inner magic `03 01 'tad.'`),
- **Embedded `.apm` and `.scm` match replay/telemetry files** for recently played fixtures.
- **`game_db.dat` (`~88–187 MB` decompressed):** The primary relational memory dump holding Clubs, Players, Staff, Contracts, Finances, Facilities, Stadiums, Injuries, Suspensions, and Season/Match Statistics.

---

### 1.2 Decoded "Unknown" Fields Across Core Tables

| Table | Previously Unknown / Opaque Binary Field | Reverse-Engineered Meaning & Binary Layout | Implementation |
| :--- | :--- | :--- | :--- |
| **`staff`** | `s.unknown['r4']` (`u8`) & `list_indexes` | **Staff Job Role ID (`0..88`)** (`2`=Assistant Manager, `6`=Director/Board, `8`=Managing Director, `10`=Youth/Reserve Manager, `12`=Physio, `14`=Scout, `16`=Manager, `20`=Coach, `22`=Fitness Coach, `26`=Goalkeeping Coach, `34`=Youth Coach, `38`=Youth Physio, `40`=Youth Sports Scientist, `44`=Chief Scout, `46`=Head Physio/Club Doctor, `48`=Head of Sports Science, `50`=Sports Scientist, `58`=Director of Football, `60`=Head of Youth Development, `62`=Loan Manager/Technical Director, `64`=Set Piece Coach, `80`=Performance Analyst, `86`=Recruitment Analyst, `88`=Chief Recruitment Analyst) and **Department Membership (`0`=Medical, `1`=Coaching, `2`=Scouting/Recruitment)**. | [`STAFF_ROLE_MAP`](../fm26save/constants.py#L283-L309), [`decode_staff_enriched()`](../fm26save/enrichment.py#L105-L170) |
| **`staff`** | `block_40` (`26` bytes at `ability_base + 40`) | **26 Hidden Staff `1..100` (`5`-step) Attribute Slots** (`(raw + 2) // 5` $\rightarrow$ `1..20` scale). The 26-byte block is 100% verified as a `1..100` attribute array extracted inside `_core/readers/staff.py`; individual slot names in `STAFF_BLOCK40_FIELDS` are heuristic role-cluster mappings. | [`_read_ability_block()`](../fm26save/_core/readers/staff.py#L455-L499), [`STAFF_BLOCK40_FIELDS`](../fm26save/constants.py#L315-L342) |
| **`contracts`** | `money_a`, `money_b`, `money_c` (`i32`) | **`money_a`** = Signing-On / Loyalty Bonus Pool (`53.3%–61%` non-zero across saves; `13.5%–18.5%` conditional median of annual wage among non-zero contracts); **`money_b`** = Agent Commission Fee (`29%–38.4%` non-zero; `5.2%–7.1%` conditional median among non-zero contracts); **`money_c`** = Secondary Package Bonus (`2.6%–8.9%` non-zero). Exposed on `_core.Contract` as `.signing_or_loyalty_fee`, `.agent_fee`, `.package_bonus`. | [`Contract`](../fm26save/_core/models/contracts.py#L266-L286), [`decode_contracts_enriched()`](../fm26save/enrichment.py#L173-L216) |
| **`contracts`** | `e12` (`u16`), `e37`, `e38`, `e39`, `e8` (`u8`) | **`e12`** = Contract Option / Reference Year (`1900` is FM's null-date sentinel `(1, 1900)` in `10.7%–39%` of rows depending on save setup and is mapped to `None`; active years `2012..2030+` in `61%–89.3%`); **`e38`** = Promised Future Squad Status; **`e37`** = Playing Time Pathway Sub-Code; **`e39`** = Contract Status Flags; **`e8`** = Registration Code. | [`decode_contracts_enriched()`](../fm26save/enrichment.py#L173-L216) |
| **`facilities`** | Post-Finance Chain Block (`chain_end + 0..140`) | `offset +50` (`u8`) = **Corporate Facilities (`1..20`)** (verified in `_core/readers/facilities.py`); `offset +49` (`u8`) = **Facility Block Tag (`0x02`)**; `offset +33`, `+41`, `+45` (`u32`) = `raw_post_finance_u32_33`, `raw_post_finance_u32_41`, `raw_post_finance_u32_45` (unconfirmed post-finance chain words). | [`decode_facilities_enriched()`](../fm26save/enrichment.py#L220-L272) |
| **`players`** | Record Tail Bytes (`rec_off + height_offset - 5 .. +1`) | On builds where `pl_layout.height_offset >= 122` (`26.3.2`) and `raw_pa_copy == player.ability.potential`, `height_offset - 5` (`+117` `u8`) = **Squad Shirt Number (`1..99`, `255`=None)**, `height_offset - 4` (`+118` `u8`) = **Peak/RCA Byte**, `height_offset - 3` (`+119` `u8`) = **Mirrored `PA` Byte**, `height_offset + 1` (`+123` `u8`) = **Body Type Byte**. Gated on `height_offset >= 122` and `PA` match so `26.1.x` builds (`height_offset == 113`) return `None`. | [`decode_players_enriched_relations()`](../fm26save/enrichment.py#L332-L355) |
| **`players`** | `PersonBlock` `16`-byte Relation Entries (`sentinel = 0xFF`) | Decodes all `(kind, role)` pairs (`ref` `u32` at `+0`, `kind` `u8` at `+10`, `role` `u8` at `+11`, `qualifier` `u8` at `+12`, `0xFF` at `+15`): **`(1, 72)` Home-Grown Club** (`club_index`), **`(1, 3)` Favoured Club** (`club_index`), **`(1, 4)` Disliked Club** (`club_index`), **`(3, 1)` Favoured Person** (`ref = pindex`, resolved via `player_records.position_by_pindex`), **`(3, 2)` Disliked Person** (`ref = pindex`), **`(7, 18)` Spoken Language & Proficiency**, **`(8, 9)` Second Nationality**, **`(8, 70)` Home-Grown Nation**, **`(4, 67)` / `(4, 25)` / `(4, 56)` Local Region (`0..2,526`, resolved via `8_47.dat` `load_official_local_region_map()`)**. | [`RELATION_PAIR_MAP`](../fm26save/constants.py#L347-L363), [`decode_players_enriched_relations()`](../fm26save/enrichment.py#L275-L445) |
| **`tactics`** | `tactics_man.dat` `block.selectors` (`u32[]`) | Resolves raw `pindex + 1` selectors via `player_records.position_by_pindex` into **Starting XI (`slots 1..11`)**, **Substitutes/Squad (`slots 12..26`)**, and **Set-Piece Taker Pools**. | [`decode_tactics_lineup()`](../fm26save/enrichment.py#L431-L494) |
| **`clubs.city_id`** | `0`-Based Master City Index (`0..58,348`) | Linked directly to `lang_update_db.dat` Frame `#03` (`8_2.dat`) and `client_db.dat` Frame `#02` (`table_2.dat`), resolving **100% of all 58,349 cities worldwide** with exact official names, latitude, longitude, altitude (`ft`), city attraction (`1..20`), and `100%` verified `db_city_id`/`db_uid` at offset `+32`/`+36`. | [`load_official_city_map()`](../fm26save/game_files.py#L734-L761), [`build_city_map()`](../fm26save/enrichment.py#L63-L97) |

---

## Part 2: Complete Reverse-Engineering of All 12 FM26 Game Installation File Systems (`fm26save/game_files.py`)

All 12 game-file systems have been decoded and implemented in [`fm26save/game_files.py`](../fm26save/game_files.py) (and exposed via CLI `fm-toolkit game-files --system all`).

---

### System 1: Quick Match Engine (`QME`) Statistical Distributions (`simatch.fmf` Frames `#119` & `#120`) & Player Match Ratings (`Frame #118`)
- **Extractor:** [`extract_qme_distributions()`](../fm26save/game_files.py#L53-L119)
- **Decoded Frames:**
  - **`Frame #119` (`simatch/qme_distribution_data.jsb`, `571,829` B):** Contains **3,137 statistical distributions** (**`1,803` `poisson`** distributions, **`630` `normal`** distributions, **`580` `binned`** empirical 10-bin histograms, and **`124` `zero`** distributions) indexed by `(stat_type, position, ability_window, attribute_window)` across **`14` positions** and **`3` CA windows (`[0, 99]`, `[100, 129]`, `[130, 200]`)**.
  - **`Frame #120` (`simatch/qme_stat_relevant_attribute_data.jsb`, `1,608` B):** Maps all **`22` simulated `stat_type` keys** (`passes_attempted`, `pass_completion`, `key_passes`, `crosses_attempted`, `cross_completion`, `tackles_attempted`, `tackle_completion`, `key_tackles`, `interceptions`, `blocks`, `clearances`, `headers_attempted`, `header_completion`, `key_headers`, `fouls_made`, `dribbles`, `offsides`, `distance_run`, `progressive_passes`, `sprints`, `pressures_attempted`, `pressures_completion`) to their exact `relevant_attributes` list.
  - **`Frame #118` (`simatch/player_ratings_data.jsb`, `348,584` B):** Contains **6 versions** (`2120`, `2200`, `2220`, `2300`, `2320`, `2400`) of the Player Match Rating engine (`start_value = 6700` = **`6.70`** across all 6 versions, `40` `RolePosition` lookup entries mapped to `30` role coefficient tables × `52` match actions).

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
  - **`Frame #114` (`simatch/oop_attributes_scoring.jsb`, `2,115` B):** **`39` Out-Of-Possession `RolePosition` bitmasks** ($2^0..2^{45}$) mapped to their official engine `ATTRIBUTES` ID lists (`[20, 21, 24, 32, 33, 35, 44, 47, 51, 52, 53, 60, 68]`).
  - **`Frame #115` (`simatch/oop_pitch_proximity_scores.jsb`, `93,500` B):** **`118` `(Position, Role)` entries** covering `24` unique position codes (`-15..10`) and `40` unique role codes (`0..57`), each containing **`24` spatial zone couples (`2,832` total coordinate intervals)** specifying `{target_position, side (-1=Left, 0=Center, +1=Right), min_score, max_score}` (`0..20` proximity score).

---

### System 4: All 11 Shot-Type xG Logistic Regression Models (`Frames #002..#100`, 9 Versions up to `26_1_4_1`), Ball Physics Table (`Frame #116`), 101 Tactical Presets (`Frames #121..#222`), & AI Team Selection (`Frame #223`)
- **Extractors:** [`extract_xg_shot_models()`](../fm26save/game_files.py#L245-L315), [`extract_tactical_styles_and_presets()`](../fm26save/game_files.py#L318-L440), [`load_engine_formulas()`](../fm26save/formulas.py#L1770-L1840)
- **9 Engine Version Folders (`Frames #002..#100` in `simatch/expected_goals/models/`):** `23_1_1_9`, `23_7_0_5`, `23_9_9_1`, `24_1_2_3`, `24_5_2_2`, `25_0_0_4`, `25_0_5_13`, `26_0_5_1`, and active **`26_1_4_1` (`Frames #090..#100`)**.
- **Active `26_1_4_1` Expected Goals (`xG`) Models (`1e7` Fixed-Point Scale):**
  $$\text{xG} = \frac{1}{1 + \exp\!\left(-\left(\beta_0 + \sum_i \beta_i x_i\right)\right)}$$

| Frame | `shot_type` | Raw Intercept (`int32`) | Intercept $\beta_0$ (`÷ 1e7`) | `norm_dist_to_goal` (`÷ 1e7`) | `norm_players_between` (`÷ 1e7`) | `fraction_goal_visible` (`÷ 1e7`) | `norm_dist_closest_occ` (`÷ 1e7`) | `norm_height_of_ball` (`÷ 1e7`) | `angle_shot_to_goal` (`÷ 1e7`) | `angle_facing_to_goal` (`÷ 1e7`) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `#90` | **`free_kicks`** | `-43,404,507` | `-4.340451` | `+3.719432` | `+1.290821` | — | `-7.081997` | — | `+0.423622` | `+0.935728` |
| `#91` | **`headers`** | `-285,245,658` | `-28.524566` | `+31.697463` | `-4.184486` | `+0.050670` | `+0.048844` | `-1.273580` | `-0.305586` | `+0.728238` |
| `#92` | **`obscured_headers`** | `-321,115,868` | `-32.111587` | `+35.530408` | `-4.867079` | `-0.163795` | `+0.006584` | `-0.627774` | `+0.449147` | `+0.052431` |
| `#93` | **`obscured_regular`** | `-143,758,299` | `-14.375830` | `+15.016758` | `-6.709227` | `+0.705953` | `-1.147154` | — | `+2.784056` | `+0.094596` |
| `#94` | **`obscured_volleys`** | `-111,223,868` | `-11.122387` | `+11.594430` | `-8.878511` | `+0.576773` | `-0.620493` | `-1.894032` | `+2.264416` | `+0.112183` |
| `#95` | **`open_goal_headers`** | `-159,077,046` | `-15.907705` | `+16.723500` | `-6.409850` | `+1.538443` | `-0.581208` | `-1.099482` | `-0.336031` | `+0.843360` |
| `#96` | **`open_goal_regular`** | `-108,673,064` | `-10.867306` | `+10.198332` | `-9.888864` | `+1.643823` | `-1.008213` | — | `+1.080761` | `+0.477030` |
| `#97` | **`open_goal_volleys`** | `-102,791,850` | `-10.279185` | `+9.622170` | `-8.042267` | `+1.806438` | `+0.002231` | `-0.281359` | `+0.480432` | `+0.448593` |
| `#98` | **`penalties`** | `+11,984,673` | `+1.198467` | — | — | — | `0.000000` | — | — | — |
| `#99` | **`regular`** | `-120,959,039` | `-12.095904` | `+13.116154` | `-4.648781` | `-2.044286` | `-1.136978` | — | `+1.751011` | `+0.949736` |
| `#100` | **`volleys`** | `-112,650,254` | `-11.265025` | `+12.182221` | `-3.875611` | `-1.223699` | `-0.841180` | `-1.485970` | `+1.294951` | `+0.596560` |

- **Ball Physics Lookup Table (`Frame #116` — `simatch/physics/ball/ball_physics_22_0_5_0.bta`, `3,277,236` B = `3.125 MB`):**
  - Identified in the `.fmf` trailer directory as `simatch/physics/ball/ball_physics_22_0_5_0.bta` (`939,547` B compressed $\rightarrow$ `3,277,236` B decompressed), storing pre-computed 3D ball trajectory, aerodynamic drag/Magnus spin, and surface bounce lookup tables (`22.0.5.0`).
- **10 Tactical Style Templates (`Frame #192` — `simatch/tactics/tactical_styles.xml`) + `101` Binary Presets (`Frames #121..#222`):**
  - **`90` `.tac` (inner magic `\x03\x01cat.`) Dual-Formation Combinations:** Stored under `simatch/tactics/<style>/*.tac`, pairing an In-Possession (`IP`) formation with an Out-Of-Possession (`OOP`) formation (e.g., `4-2-3-1 DM AM Wide / 4-4-2`).
  - **`11` `.stra` (inner magic `\x03\x01rts.`) Tactical Style Instruction Vectors:** Stored under `simatch/tactics/*.stra` (`control_possession.stra`, `gegenpress.stra`, `tiki_taka.stra`, `vertical_tiki_taka.stra`, `wing_play.stra`, `route_one.stra`, `fluid_counter_attack.stra`, `direct_counter_attack.stra`, `catenaccio.stra`, `park_the_bus.stra`, `default.stra`).
- **AI Team Selection Weights (`Frame #223` — `simatch/weights.jsb`, `6,547` B):**
  - `4` `TEAM_PICKING_STYLE` profiles (`TPS_FIRST_TEAM_PICKING`, `TPS_SEMI_RESERVE_PICKING`, `TPS_SLIGHTLY_RESERVE_PICKING`, `TPS_TOTAL_RESERVE_PICKING`) × `40` `TSF_*` weights.

---

### System 5: 105 Internal Database XML Schemas & Master FourCC Enums (`shared/data/editor.fmf`)
- **Extractor:** [`extract_editor_schemas_and_enums()`](../fm26save/game_files.py#L445-L530)
- **Cataloged Archive (`106` Zstd Frames = `105` XML Schema Files `#000..#104` + `1` Directory `#105`):**
  - All `105` XML schema frames (`agreements`, `award`, `city`, `club`, `comp`, `continent`, `contract_offer`, `currency`, `derby`, `injury`, `language`, `local_region`, `media_source`, `nation`, `non_player`, `official`, `person`, `player`, `retired_person`, `sponsor`, `stadium`, `stage_name`, `team`, `weather`, rule group schemas, UI schemas, and `db enums.xml`) are cataloged with root tags, property counts, and enum counts.
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
- **Extractors:** [`extract_master_db_tables()`](../fm26save/game_files.py#L1185-L1345), [`load_official_city_map()`](../fm26save/game_files.py#L1150-L1182), [`extract_permanent_edt_rules()`](../fm26save/game_files.py#L1348-L1381)
- **Archive Frame Counts & Embedded `.fmf` Trailer Directory:**
  - Each `.dat` file has a 12-byte outer header (`54 00 00 00 ...`) followed at `base = 12` by a standard `\x02\x01fmf.` container with its own Zstd-compressed trailer directory (`read_fmf_directory()`).
  - **`client_db.dat` (`31` directory entries `#00..#30` + `1` trailer directory `#31`):**
    - `#00 simple_vars.dat` (`36 B`), `#01 table_0.dat` (`3,884` Awards), `#02 table_2.dat` (`58,349` Cities), `#03 table_3.dat` + `#04 table_extra_3.dat` (`96,343` Clubs), `#05 table_25.dat` + `#26 table_for_old_save_25.dat` (`7,973` Competitions), `#06 table_5.dat` (`7` Continents), `#07 table_41.dat` (`173` Stage Flags/Rules), `#08 table_6.dat` (`136` Injuries), `#09 table_7.dat` (`180` Media Sources), `#10 table_8.dat` (`126`), `#11 table_10.dat` (`251` Nations), `#12 table_9.dat` + `#13 table_extra_9.dat` (`502` Languages), `#14..#16 name_table_0..2.dat` + `#17..#19 name_table_extra_0..2.dat` (`294,103` First / `599,900` Last / `94,088` Common Names), `#20 table_19.dat` (`28`), `#21 table_47.dat` (`2,527` Local Regions), `#22 table_21.dat` (`51,118` Stadiums), `#23 table_22.dat` (`668`), `#24 table_23.dat` + `#27 table_for_old_save_23.dat` (`286` Stage Names), `#25 table_56.dat` (`6` International Agreements), `#28 table_27.dat` (`373` Weather Profiles), `#29 table_35.dat` (`924` Currencies/Descriptions), `#30 table_18.dat` (`1,683` Derbies).
  - **`lang_update_db.dat` (`400` directory entries `#000..#399` + `1` trailer directory `#400`):** **`25` languages × `16` localized tables** (frames `#00..#15` are Language `8` = English: `#00 8_9.dat` Nations `251`, `#01 8_25.dat` Competitions `7,973`, `#02 8_3.dat` Clubs `96,343`, `#03 8_2.dat` Cities `58,349`, `#04 8_5.dat` Continents `7`, `#05 8_6.dat` Injuries `136`, `#06 8_0.dat` Awards `3,884`, `#07 8_21.dat` Stadiums `51,118`, `#08 8_23.dat` Stage Names `286`, `#09 8_19.dat` `12 B`, `#10 8_35.dat` Currencies/Descriptions `186`, `#11 8_7.dat` Media Sources `180`, `#12 8_47.dat` Local Regions `2,527`, `#13 8_18.dat` Derbies `1,683`, `#14 8_56.dat` Agreements `6`, `#15 8person_names.dat` `12 B`).
  - **`server_db.dat` (`77` directory entries `#00..#76` + `1` trailer directory `#77`):** Contains the 31 core tables plus 46 simulation-only tables (`table_11.dat` `1,916` Currencies, `table_16.dat` `5,594` Sponsors, `table_31..46.dat`, etc.).
- **Exact Binary Record Layouts & Cross-Database Joins (`100%` Record Alignment Verified):**
  - **`7` Continents (`8_5.dat` `#04` + `client_db/table_5.dat` `#06` `260 B = 15B hdr + 7 × 35B` + `server_db/table_5.dat` `#06` `49` B/rec):** `uid`, `name`, `short_name`, `three_letter_code`, `continentality`, `federation_name`, `federation_short_name`, `regional_strength_factor` (`f64`).
  - **`251` Nations (`8_9.dat` `#00` + `client_db/table_10.dat` `#11` `27,899 B` + `server_db/table_10.dat` `#11` `538,107 B`):** `db_nation_id` (`0..250`), `db_uid`, `name`, `short_name`, `three_letter_code`, `nationality`, `continent_id`, `capital_city_id`, `economic_factor_1_20`, `years_to_gain_nationality`, `game_importance_code` (`1..4`).
  - **`58,349` Cities (`8_2.dat` `#03` + `client_db/table_2.dat` `#02` `2,509,029 B = 22B hdr/tail + 58,349 × 43B`):** 0-based `city_id` (`0..58,348`, matching `.fm` save `club.city_id` 1-to-1), `uid`, `name`, `latitude` (`float32` at `+3`), `longitude` (`float32` at `+7`), `attraction_1_20` (`u8` at `+11`), `nation_id` (`u32` at `+12`), `local_region_id` (`u32` at `+16`), `altitude_ft` (`u16` in feet at `+20`), `inhabitants_bracket` (`u8` at `+22`), `weather_profile_id` (`u16` at `+27`), `db_city_id` (`u32` at `+32`, verified `100%`), and `db_uid` (`u32` at `+36`, verified `100%`).
  - **`51,118` Stadiums (`8_21.dat` `#07` + `client_db/table_21.dat` `#22` `1,942,506 B = 22B hdr/tail + 51,118 × 38B` + `server_db/table_21.dat` `#22` `9,252,380 B = 22B hdr/tail + 51,118 × 181B`):**
    - `client_db/table_21.dat` (`38` B/rec): `city_id:i32@+5`, `owner_club_id:i32@+9`, `latitude:f32@+19`, `longitude:f32@+23`, `db_stadium_id:u32@+27` (`100%`), `db_uid:u32@+31` (`100%`).
    - `server_db/table_21.dat` (`181` B/rec): `capacity:u32@+2`, `seating_capacity:u32@+6`, `expansion_capacity:u32@+10`, `used_capacity:u32@+14`, `all_seater_capacity:u32@+23`, `pitch_length_m:u16@+27` (decimeters ÷ 10), `pitch_width_m:u16@+29` (decimeters ÷ 10), `build_year:u16@+49`, `min_pitch_length_m:u16@+56`, `min_pitch_width_m:u16@+58`, `max_pitch_length_m:u16@+60`, `max_pitch_width_m:u16@+62`.
  - **`96,343` Clubs (`8_3.dat` `#02` + `client_db/table_3.dat` `#03`):** `db_club_id` (`0..96,342`, `100%`), `db_uid` (`100%`), `name`, `short_name`, `six_letter_name`, `three_letter_name`, `alt_short_name`, `nickname`, `nation_id`, `based_nation_id`, `city_id`, `is_womens_club`.
  - **`7,973` Competitions (`8_25.dat` `#01` + `client_db/table_25.dat` `#05` `127` B/rec & `table_for_old_save_25.dat` `#26` `123` B/rec; record `#0` has 1 extra leading byte):** Tail-aligned on `<III(idx, uid, uid)` (`7,973 / 7,973 = 100%`), decoding `db_comp_id`, `db_uid`, `name`, `short_name`, `code`, `division_level`, `comp_type_code`, `continent_id`, `nation_uid`, and `nation_id`.
  - **`3,884` Awards (`8_0.dat` `#06` + `client_db/table_0.dat` `#01` `77` B/rec):** `db_award_id` (`0..3,883`, `100%`), `db_uid` (`100%`), `name`, `short_name`.
  - **`136` Injuries (`8_6.dat` `#05` + `client_db/table_6.dat` `#08` `2,198 B = 22B hdr/tail + 136 × 16B` + `server_db/table_6.dat` `#08` `6,550 B = 22B hdr/tail + 136 × 48B`):**
    - `server_db/table_6.dat` (`48` B/rec starting at offset `13`): `category:u8@+1`, `body_part:u8@+2`, `is_physical:u8@+3`, `min_days:u16@+4`, `extra_days:u16@+6`, `inactive_min_days:u16@+8`, `inactive_extra_days:u16@+10`, `treatment_type:u8@+13`, `is_recurring:u8@+14`, `can_play_with_protective_or_injections:u8@+15`, `match_sharpness_drop_pct:u8@+16`, `flag_17:u8@+17`, `occurrence_ratio:f32@+18`, `base_occurrence:f32@+22`, `severity_tier:u8@+30`, `is_contagious:u8@+31` (`1` exclusively for `cold`, `flu`, `virus`), `cause_bitmask:u8@+32`, `db_injury_id:u32@+36` (`100%`), `db_uid:u32@+40` (`100%`).
  - **`988,091` Pre-Game Person Name Pool Records (`client_db #17, #18, #19` `name_table_extra_0..2.dat`):**
    - **`#17` First Names (`name_table_extra_0.dat`):** `294,103` records (`[name_id:u32][slen:u32][utf8_bytes:slen]`, `0` padding bytes)
    - **`#18` Last / Surnames (`name_table_extra_1.dat`):** `599,900` records
    - **`#19` Common / Mononym Names (`name_table_extra_2.dat`):** `94,088` records
  - Plus **`2,527` Local Regions (`#21 table_47.dat`)**, **`1,683` Derbies (`#30 table_18.dat`)**, **`924` Currencies/Descriptions (`#29 table_35.dat`)**, **`373` Weather Profiles (`#28 table_27.dat`)**, **`286` Stage Names (`#24 table_23.dat`)**, **`180` Media Sources (`#09 table_7.dat`)**, and **`6` International Agreements (`#25 table_56.dat`)**.
- **16 Permanent `.edt` / `.ddt` Rule Files (`shared/data/database/db/2620/edt/permanent/`):**
  - `sugardaddy.edt` (`14` clubs: `Manchester City`, `AS Monaco`, `Al-Ain`, `Al-Wahda` as `FRONT_END`; `Chelsea`, `Hoffenheim`, `Shanghai Shenhua`, `Sepahan`, `Busan I'Park`, `Jeonnam Dragons`, `Ulsan Hyundai`, `Suwon Samsung Bluewings` as `UNDERWRITER`; `Buriram United`, `Jeonbuk Hyundai Motors` as `BACK_END`), `eng_youth_grades.edt` (`95` clubs), `valid_takeovers_only.edt` (`69` rules), `transfer_embargo.edt` (`35` rules), `support_staff.edt` (`12` rules), `alliteration_adjectives.edt` (`123` rules), etc.

---

### System 7: Press Conference Trees (`media.fmf`), Training Schedules (`training.fmf`) & `simatchshared.fmf` RGB Palettes + Newgen Demographics
- **Extractors:** [`extract_media_interaction_trees()`](../fm26save/game_files.py#L1337-L1384), [`extract_training_and_newgen_configs()`](../fm26save/game_files.py#L1387-L1456)
- **Empirical Totals:**
  - **`media.fmf` (`649` XML frames + `1` directory):** `3,934` press conference / player interaction question definitions (`QID_*`), `pcaa` alternative answer branches, and `barl` backroom advice condition blocks.
  - **`training.fmf` (`Frames #1..#4`):** `training_item_effects.jsb` (`Frame #1`), `164` full-time standard weekly training schedules (`Frame #2`, `day1..day7` × `session1, session2, extra`), `136` youth/part-time weekly schedules (`Frame #3`, `300` total schedule templates), and `training_sessions_weights.jsb` (`Frame #4`).
  - **`simatchshared.fmf` (`75` JSB Frames `#000..#074` + `1` Directory `#075`):**
    - **`Frames #000..#073` (`74` Frames):** RGB kit/hair/skin/eye/accessory color palette definitions (`Colors` arrays) and 3D stadium crowd density/animation configuration blocks.
    - **`Frame #074`:** `135` newgen hair length/colour demographic probability rules by ethnicity/region tag.

---

### System 8: IL2CPP Metadata & Native Symbol Table (`il2cpp.usym` & `global-metadata.dat`)
- **Extractor:** [`extract_il2cpp_symbols_and_metadata()`](../fm26save/game_files.py#L1462-L1511)
- **Empirical Totals:**
  - **`fm_Data/il2cpp_data/il2cpp.usym` (`38.54 MB`):** Magic `sym-`, Version `2`, containing **`1,593,548` native symbol/line mapping records** for `GameAssembly.dll`.
  - **`fm_Data/il2cpp_data/Metadata/global-metadata.dat` (`15.58 MB`):** Sanity `0xFAB11BAF`, IL2CPP Metadata Version `31`, with `106+` extracted C# engine symbols (`EventFmxMatchFocusSelectInPossessionType`, `EventFmxMatchFocusSelectOutOfPossessionType`, `EventFmxRecruitmentFocusCurrentAbilityUpdated`, `EventFmxRecruitmentFocusPotentialAbilityUpdated`, `EventFmxRequestQuickMatch`, `FMMatchMomentumChart`, `FMPlayerRating`, `DebugTransferValueReference`, `AcceptAllOffersOverAskingPrice`, etc.).

---

### System 9: Pre-Game Master People & Career History Databases (`basic_people_db.dat`, `people_db.dat`, `pl_hist_index/id/dt.dat`, `non_pl_hist_dt.dat`, `summary.dat`)
- **Extractor:** [`extract_pregame_people_and_history_db()`](../fm26save/game_files.py#L1737-L1984)
- **`basic_people_db.dat` (`12.79 MB` Zstd@12 $\rightarrow$ `60,147,370` B decompressed, `723,010 / 723,010` People = `100.0%` Walked):**
  - Header at offset `0..5`: `u32 count = 723,010`, `u8 version = 1`.
  - Byte `pos + 1` (`person_type`) deterministically sets record byte length across all `723,010` records:
    - `1` (**Non-Player / Staff:** `174,504` records): **`84` bytes**
    - `2` (**Player:** `532,742` records): **`84` bytes**
    - `3` (**Player / Staff:** `4,410` records): **`84` bytes** (`537,152` total playable players: **`495,248` Men's Players** + **`41,904` Women's Players** via `bool(rec[65] & 0x10)`)
    - `4` (**Official / Referee:** `9,872` records): **`34` bytes**
    - `5` (**Agent / Journalist:** `1,482` records): **`22` bytes**
  - **84-Byte Player/Staff Binary Record Layout:**
    - `+2..+18` (`<iiii`): `nation_id, nation_uid, club_id, club_uid`
    - `+26..+34` (`<ii`): `based_nation_id, based_nation_uid`
    - `+42..+54` (`<HHHHhH`): `home_reputation (1..200), current_reputation (1..200), world_reputation (1..200), ca (1..200), pa (signed i16: 1..200 or negative PA tier -1..-10 / -15..-95), birth_year`
    - `+62..+65`: positional bitmask; `+65`: `is_female = bool(rec[65] & 0x10)`
    - `+72..+84` (`<III`): `person_id (0..723009), uid, uid`
  - **Pre-Game Negative `PA` Wonderkid Distribution across all `537,152` Players (`2620` Active DB):**
    - **`PA = -10` (`170–200`, Generational Wonderkids — `6` Players in `2620`):**
      1. **Endrick** (`UID 2000220941`, Real Madrid, Brazil, Men, b. `2006`, `CA = 142`, `PA = -10`)
      2. **Estêvão** (`UID 2000263999`, Chelsea, Brazil, Men, b. `2007`, `CA = 138`, `PA = -10`)
      3. **Lily Yohannes** (`UID 2000346894`, OL Lyonnes, United States, Women, b. `2007`, `CA = 135`, `PA = -10`)
      4. **Kennedy Fuller** (`UID 2000341118`, Angel City FC, United States, Women, b. `2007`, `CA = 131`, `PA = -10`)
      5. **Ayyoub Bouaddi** (`UID 2000381365`, LOSC Lille, France, Men, b. `2007`, `CA = 130`, `PA = -10`)
      6. **Trinity Armstrong** (`UID 2000458565`, San Diego Wave FC, United States, Women, b. `2007`, `CA = 130`, `PA = -10`)
    - **`PA = -95` (`160–190`, World-Class Wonderkids — `22` Players in `2620`):** **Désiré Doué** (`UID 2000115202`, PSG, `CA=159`), **Kenan Yıldız** (`UID 2000138835`, Juventus, `CA=158`), **Warren Zaïre-Emery** (`UID 2000179712`, PSG, `CA=154`), **Pau Cubarsí** (`UID 2000296497`, Barcelona, `CA=153`), **Claire Hutton** (`UID 2000328886`, Bay FC, `CA=148`), **Louna Ribadeira** (`UID 2000212812`, Chelsea, `CA=141`), **Ethan Nwaneri** (`UID 2000283271`, Arsenal, `CA=140`), **Marc Bernal** (`UID 2000295603`, Barcelona, `CA=140`), **Gisele Thompson** (`UID 2000328884`, Angel City FC, `CA=140`), **Felicia Schröder** (`UID 2000272171`, BK Häcken, `CA=137`), **Melween N'Dongala** (`UID 2000343037`, Paris FC, `CA=137`), **Jordyn Bugg** (`UID 2000408243`, Seattle Reign, `CA=134`), **Sydney Schertenleib** (`UID 2000374647`, Barcelona, `CA=132`), **Rodrigo Mora** (`UID 2000265865`, FC Porto, `CA=131`), **Kimmi Ascanio** (`UID 2000408233`, San Diego Wave, `CA=131`), **Franco Mastantuono** (`UID 2000183231`, Real Madrid, `CA=131`), **Veerle Buurman** (`UID 2000374740`, Chelsea, `CA=130`), **Indiana Dos Santos** (`UID 2000307825`, Sydney FC, `CA=116`), **Micayla Johnson** (`UID 2000453427`, Chicago Stars, `CA=112`), **Lola Brown** (`UID 2000367453`, Chelsea, `CA=111`), **Luca Williams-Barnett** (`UID 2000485992`, Tottenham, `CA=105`), **KK Ream** (`UID 2000507739`, Utah Royals, `CA=105`).
    - **Remaining Negative `PA` Tiers:** `-9` (`92`), `-85` (`273`), `-8` (`709`), `-75` (`1,776`), `-7` (`4,459`), `-65` (`8,924`), `-6` (`16,576`), `-55` (`19,749`), `-5` (`27,845`), `-45` (`22,164`), `-4` (`20,667`), `-35` (`14,048`), `-3` (`12,559`), `-25` (`6,437`), `-2` (`4,941`), `-15` (`1,345`), `-1` (`1,146`).
- **`people_db.dat` (`76.55 MB` Concatenated Zstd@12 $\rightarrow$ `451,072,539` B = `430.18 MB` decompressed):**
  - Resolves `first_name_id`, `last_name_id`, `common_name_id`, UTF-8 legal full name, exact `dob_day_of_year` + `dob_year`, `height_cm` (`u16` at `+135` from player header), `weight_kg` (`u8` at `+130`), **8 Hidden Personality Attributes (`1..20` bytes: `Adaptability`, `Ambition`, `Controversy`, `Loyalty`, `Pressure`, `Professionalism`, `Sportsmanship`, `Temperament`)** at `+21..+29` after legal name, and `birth_city_id` / `birth_city_uid`.
- **3-File Singly-Linked List Career History Architecture (`pl_hist_index.dat` + `pl_hist_id.dat` + `pl_hist_dt.dat`):**
  - **`pl_hist_index.dat` (`8,352,068` B decompressed):** `u32 count = 1,044,008` at offset `0`, followed by `522,004` `(uid: u32, hist_idx: u32)` pairs (`0..522,003`) and `522,004` `(person_id: u32, hist_idx: u32)` pairs.
  - **`pl_hist_id.dat` (`8,352,064` B decompressed):** Indexed by `hist_idx * 8`, storing `(head_byte_offset: u32, tail_byte_offset: u32)` into `pl_hist_dt.dat`.
  - **`pl_hist_dt.dat` (`191,173,655` B decompressed = `4,344,855` season rows × `44` bytes):**
    - `+0` (`u16`): `season_start_year`
    - `+2` (`u16`): `season_end_year`
    - `+4` (`u8`): `flags` (`0x02` = loan spell)
    - `+5` (`i8`): `league_appearances`
    - `+6` (`i8`): `league_goals`
    - `+7..+15` (`<ii`): `club_id, club_uid`
    - `+15..+23` (`<ii`): `comp_id, comp_uid`
    - `+40..+44` (`i32`): `next_row_byte_offset` (`-1` marks the end of the player's career linked list).
  - **`non_pl_hist_dt.dat` (`31,722,389` B decompressed):** Non-player/staff historical career nodes.
  - **`summary.dat` (`21` B decompressed):** Master database build header.

---

### System 10: Compiled `.dbc` Competition Rule Archives & `.lnc` Licensing / Name Overrides
- **Extractor:** [`extract_dbc_and_lnc_rules()`](../fm26save/game_files.py#L1989-L2120)
- **`shared/data/sicomps/comps.dbc` (`8.20 MB` $\rightarrow$ `74.46 MB` decompressed across `1,443` Zstd Frames):**
  - **`1,442` `\x03\x01cbd.` Binary TLV Competition Rule Sets** + `1` directory index (`Frame #1442`), governing league structures, playoff brackets, prize money, TV revenue distribution, squad registration rules, work permits, and continental qualification slots across all playable and background nations.
- **Database Patch `.dbc` Files (`shared/data/database/db/2620/dbc/`):**
  - `fifa_wc26_squads.dbc`, `homegrown.dbc`, `saudi_manager_change.dbc`, and `language/Licensing2.dbc`.
- **Plaintext `.lnc` Licensing & Name Override Directives (`shared/data/database/db/2620/lnc/all/`):**
  - **`41` `.lnc` files in `2620` (`178` across all DB versions)** containing `1,500+` active directives across `COMP_LONG_NAME_CHANGE`, `COMP_SHORT_NAME_CHANGE`, `CLUB_LONG_NAME_CHANGE`, `CLUB_SHORT_NAME_CHANGE`, `CHANGE_PLAYER_NAME`, `STADIUM_NAME_CHANGE`, `FAKE_NATIONAL_TEAM`, `AWARD_NAME_CHANGE`, etc.

---

### System 11: Auxiliary Simulation `.fmf` Archives (`filters.fmf`, `achievements.fmf`, `leaderboards.fmf`, `settings.fmf`, `store.fmf`, `profanity_filter.fmf`, `languages.fmf`)
- **Extractor:** [`extract_simulation_aux_fmf_archives()`](../fm26save/game_files.py#L2126-L2185)
- **Empirical Archive Breakdown (`data/game_simulation/`):**
  - **`filters.fmf` (`2` XML files in directory: `filters/config.xml` + `filters/person_filter_metadata.xml`; `445` filter `<record id="...">` definitions / `892` total `<record>` tags):** Official scouting, player search, staff search, and shortlist filter metadata.
  - **`achievements.fmf` (`1` XML file in directory: `achievements/achievements.xml`; `50` achievement `<record>` rules / `95` total `<record>` tags):** Steam / Epic / Xbox achievement trigger rules (`achv`).
  - **`leaderboards.fmf` (`1` XML file in directory: `leaderboards/leaderboards.xml`; `28` leaderboard `<record>` definitions / `57` total `<record>` tags):** Online leaderboard point calculation definitions.
  - **`settings.fmf` (`9` XML files in directory: `settings/config.xml` + `8` platform `application_settings.xml` files):** User interface, match camera, and processing preference schemas across Windows, Mac, iOS, Switch, Console, and Handheld.
  - **`store.fmf` (`2` XML files in directory: `store/store.xml` + `store/epic/store.xml`, `37` `<record>` items):** In-game store item definitions.
  - **`profanity_filter.fmf` (`2` files in directory: `profanity_filter/config.xml` + `profanity_filter/microsoft.txt`):** Text moderation wordlists and regex patterns.
  - **`languages.fmf` (`205.61 MB`):** Master `.ltc` UI localization string archive for 22+ languages.

---

### System 12: Multi-Version Pre-Game Database Evolution (`2300`..`2620` — FM23 / FM24 / FM26)
- **Extractor:** [`extract_multi_version_database_evolution()`](../fm26save/game_files.py#L2198-L2349)
- **Structural Evolution Across All 9 Database Versions (`4,945,820 / 4,945,820` Total People Walked = `100.0%`):**
  - In **FM23 (`2300..2340`)** and **FM24 (`2400..2430`)**, Player/Staff records in `basic_people_db.dat` are **`83` bytes** (`type 1, 2, 3`), Official records are `34` bytes (`type 4`), and Agent records are `22` bytes (`type 5`).
  - In **FM26 (`2600..2620`)**, Sports Interactive expanded Player/Staff records by `+1` byte to **`84` bytes** to add the Women's Football gender/metadata byte (`rec[65] & 0x10`).
  - In `client_db.dat`, **FM23 (`2300..2340`)** contains **`30` `.dat` tables**, whereas **FM24 (`2400..2430`)** and **FM26 (`2600..2620`)** contain **`31` `.dat` tables**.

| DB Version | Release Label | `basic_people_db` Stride | Total People (`100%` Walked) | Total Players (`Men` / `Women`) | Staff | Officials | Agents | `PA = -10` | `PA = -95` | Cities (`#02`) | Clubs (`#03`) | Stadiums | Comps | First Names | Last Names |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`2300`** | FM23.0 Base | `83 B` | `618,042` | `459,075` (`459,075` / `0`) | `148,079` | `9,762` | `1,126` | `1` | `5` | `54,689` | `80,758` | `46,435` | `6,928` | `237,477` | `519,842` |
| **`2310`** | FM23.1 Delta | `83 B` | `164,709` | `3,978` (`3,978` / `0`) | `149,510` | `9,783` | `1,438` | `0` | `0` | `54,708` | `80,878` | `46,476` | `6,928` | `235,088` | `514,946` |
| **`2320`** | FM23.2 Delta | `83 B` | `165,986` | `4,225` (`4,225` / `0`) | `150,519` | `9,785` | `1,457` | `0` | `1` | `54,741` | `81,162` | `46,593` | `6,931` | `236,527` | `518,024` |
| **`2330`** | FM23.3 Winter | `83 B` | `624,217` | `461,787` (`461,787` / `0`) | `151,505` | `9,784` | `1,141` | `1` | `5` | `54,742` | `81,176` | `46,599` | `6,932` | `237,168` | `519,372` |
| **`2340`** | FM23.4 Final | `83 B` | `623,215` | `460,515` (`460,515` / `0`) | `151,775` | `9,780` | `1,145` | `1` | `5` | `54,742` | `81,180` | `46,603` | `6,932` | `237,510` | `520,144` |
| **`2400`** | FM24.0 Base | `83 B` | `652,619` | `478,970` (`478,970` / `0`) | `162,526` | `9,931` | `1,192` | `1` | `10` | `56,018` | `83,837` | `48,158` | `7,035` | `242,800` | `536,209` |
| **`2430`** | FM24.3 Winter | `83 B` | `658,011` | `480,915` (`480,915` / `0`) | `166,064` | `9,839` | `1,193` | `2` | `8` | `56,293` | `84,259` | `48,413` | `7,047` | `245,981` | `542,060` |
| **`2600`** | FM26.0 Base | `84 B` | `716,011` | `531,952` (`491,943` / `40,009`) | `172,724` | `9,860` | `1,475` | `7` | `19` | `58,329` | `96,045` | `50,907` | `7,947` | `292,394` | `597,675` |
| **`2620`** | FM26.2 Active | `84 B` | `723,010` | `537,152` (`495,248` / `41,904`) | `174,504` | `9,872` | `1,482` | `6` | `22` | `58,349` | `96,343` | `51,118` | `7,973` | `294,103` | `599,900` |

- **Empirical `CA / PA` Trajectory Across `2300` $\rightarrow$ `2620` (World & Turkish Stars):**
  - **Kylian Mbappé (`UID 85139014`):** `2300: 188/197` $\rightarrow$ `2400: 188/197` $\rightarrow$ `2600: 191/197` $\rightarrow$ `2620: 195/197`
  - **Lamine Yamal (`UID 2000256231`):** `2400: 125/-10` $\rightarrow$ `2430: 130/-10` $\rightarrow$ `2600: 165/-10` $\rightarrow$ `2620: 175/194` *(graduated from `-10` to fixed `PA = 194` in `2620`)*
  - **Jude Bellingham (`UID 29232937`):** `2300: 155/-95` $\rightarrow$ `2330: 157/-95` $\rightarrow$ `2400: 168/188` $\rightarrow$ `2430: 177/188` $\rightarrow$ `2600: 181/188` $\rightarrow$ `2620: 176/188`
  - **Ousmane Dembélé (`UID 85140178`):** `2300: 162/176` $\rightarrow$ `2430: 167/174` $\rightarrow$ `2600: 186/188` $\rightarrow$ `2620: 186/188`
  - **Désiré Doué (`UID 2000115202`):** `2300: 109/-9` $\rightarrow$ `2430: 123/-9` $\rightarrow$ `2600: 159/-95` $\rightarrow$ `2620: 159/-95`
  - **Kenan Yıldız (`UID 2000138835`):** `2300: 99/-85` $\rightarrow$ `2330: 100/-85` $\rightarrow$ `2400: 110/-85` $\rightarrow$ `2430: 133/-9` $\rightarrow$ `2600: 156/-95` $\rightarrow$ `2620: 158/-95`
  - **Arda Güler (`UID 2000077193`):** `2300: 100/-9` $\rightarrow$ `2330: 105/-9` $\rightarrow$ `2400: 125/-9` $\rightarrow$ `2430: 125/-9` $\rightarrow$ `2600: 144/173` $\rightarrow$ `2620: 144/173`
  - **Hakan Çalhanoğlu (`UID 92026209`):** `2300: 153/159` $\rightarrow$ `2400: 157/160` $\rightarrow$ `2430: 160/160` $\rightarrow$ `2600: 161/164` $\rightarrow$ `2620: 162/164`
  - **Barış Alper Yılmaz (`UID 70112874`):** `2300: 115/130` $\rightarrow$ `2330: 120/145` $\rightarrow$ `2400: 125/140` $\rightarrow$ `2430: 130/140` $\rightarrow$ `2600: 145/148` $\rightarrow$ `2620: 145/148`
  - **Can Uzun (`UID 2000103330`):** `2330: 76/-65` $\rightarrow$ `2400: 104/-8` $\rightarrow$ `2430: 116/-85` $\rightarrow$ `2600: 136/-9` $\rightarrow$ `2620: 138/168`
