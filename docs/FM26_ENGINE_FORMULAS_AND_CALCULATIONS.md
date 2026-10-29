# Football Manager 26 — Mathematical Formulas, Official `.fmf` Engine Models & Empirical Save Estimators

> **Repository:** [`fm-toolkit`](../)  
> **Core Implementation:** [`fm26save/formulas.py`](../fm26save/formulas.py) & [`fm26save/game_files.py`](../fm26save/game_files.py)  
> **Data Provenance Classification:**
> To maintain strict scientific and reverse-engineering clarity, this document separates all models into two explicit categories:
> 1. **Part I — Official Extracted `.fmf` / `.jsb` Engine Models (`100%` Game Archive Data):** Decoded byte-for-byte via [`parse_jsb()`](../fm26save/formulas.py#L1577-L1655) from `shared/data/simatch.fmf` (`225` frames), `shared/data/shared/tables.fmf` (`4` frames), and `data/game_simulation/training.fmf` (`6` frames).
> 2. **Part II — Heuristic & Empirical Save-Fitted Models:** Statistical OLS regressions and tactical suitability models fitted and cross-validated (`80/20` train/test split) against decoded `.fm` save databases (`game_db.dat`).

---

# Part I — Official Extracted `.fmf` / `.jsb` Engine Models

## 1. Match Engine Expected Goals (`xG`) — All 11 Shot-Type Logistic Models (`simatch.fmf` Frames `#002..#100`)

`shared/data/simatch.fmf` contains **9 historical and current versions** of the 11 shot-type Expected Goals (`xG`) logistic regression models (`11 × 9 = 99` `.jsb` frames at `#002..#100`, followed by `expected_goals_model_config.xml` at `#101` and 11 zeroed template configs at `#102..#112`):
- `23_1_1_9` (`#002..#012`), `23_7_0_5` (`#013..#023`), `23_9_9_1` (`#024..#034`), `24_1_2_3` (`#035..#045`), `24_5_2_2` (`#046..#056`), `25_0_0_4` (`#057..#067`), `25_0_5_13` (`#068..#078`), `26_0_5_1` (`#079..#089`), and **active `26_1_4_1` (`#090..#100`)**.

$$
\text{xG} = \sigma(z) = \frac{1}{1 + e^{-z}}, \qquad z = \beta_0 + \sum_{k} \beta_k \cdot x_k
$$

### Fixed-Point Scaling (`1e7` vs `1e8`):
All raw parameters in `Frames #002..#100` are stored as signed 32-bit integers (`int32`, `.jsb` tag `0x02`).
- In `Frame #098` (`penalties`), the raw integer is `intercept = +11,984,673` (with `normalised_distance_to_closest_occluder = 0`).
- **Dividing by $10^7$ (`1e7`):** $z = +1.1984673 \implies \sigma(+1.1984673) = \mathbf{0.76825}$ (**`76.83%`** penalty conversion probability, matching real-world and FM penalty conversion rates; whereas `23_1_1_9` `#010` had `raw = +13,297,078` $\implies \sigma(+1.3297078) = 79.08\%$).
- **Dividing by $10^8$ (`1e8`):** $z = +0.11984673 \implies \sigma(+0.11984673) = 0.52993$ (`52.99%`).
- Therefore, [`extract_xg_shot_models()`](../fm26save/game_files.py#L230-L280) and [`load_engine_formulas()`](../fm26save/formulas.py#L1770-L1839) expose `raw_intercept`, `intercept_1e7` (default), and `intercept_1e8` (alongside `raw_coefficients`, `coefficients_1e7`, and `coefficients_1e8`).

### Active `26_1_4_1` Coefficients (`Frames #090..#100`, Scaled by $10^{-7}$):

| Frame & Shot Type (`shot_type`) | Raw Intercept (`int32`) | Intercept $\beta_0$ (`÷ 1e7`) | `norm_dist_to_goal` | `frac_goal_visible` | `norm_players_between` | `norm_dist_closest_occ` | `norm_ball_height` | `angle_shot_to_goal` | `angle_facing_to_goal` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`#099 regular`** | `-120,959,039` | `-12.095904` | `+13.116154` | `-2.044286` | `-4.648781` | `-1.136978` | — | `+1.751011` | `+0.949736` |
| **`#093 obscured_regular`** | `-143,758,299` | `-14.375830` | `+15.016758` | `+0.705953` | `-6.709227` | `-1.147154` | — | `+2.784056` | `+0.094596` |
| **`#096 open_goal_regular`** | `-108,673,064` | `-10.867306` | `+10.198332` | `+1.643823` | `-9.888864` | `-1.008213` | — | `+1.080761` | `+0.477030` |
| **`#091 headers`** | `-285,245,658` | `-28.524566` | `+31.697463` | `+0.050670` | `-4.184486` | `+0.048844` | `-1.273580` | `-0.305586` | `+0.728238` |
| **`#092 obscured_headers`** | `-321,115,868` | `-32.111587` | `+35.530408` | `-0.163795` | `-4.867079` | `+0.006584` | `-0.627774` | `+0.449147` | `+0.052431` |
| **`#095 open_goal_headers`** | `-159,077,046` | `-15.907705` | `+16.723500` | `+1.538443` | `-6.409850` | `-0.581208` | `-1.099482` | `-0.336031` | `+0.843360` |
| **`#100 volleys`** | `-112,650,254` | `-11.265025` | `+12.182221` | `-1.223699` | `-3.875611` | `-0.841180` | `-1.485970` | `+1.294951` | `+0.596560` |
| **`#094 obscured_volleys`** | `-111,223,868` | `-11.122387` | `+11.594430` | `+0.576773` | `-8.878511` | `-0.620493` | `-1.894032` | `+2.264416` | `+0.112183` |
| **`#097 open_goal_volleys`** | `-102,791,850` | `-10.279185` | `+9.622170` | `+1.806438` | `-8.042267` | `+0.002231` | `-0.281359` | `+0.480432` | `+0.448593` |
| **`#090 free_kicks`** | `-43,404,507` | `-4.340451` | `+3.719432` | — | `+1.290821` | `-7.081997` | — | `+0.423622` | `+0.935728` |
| **`#098 penalties`** | `+11,984,673` | `+1.198467` | — | — | — | `0.000000` | — | — | — |

---

## 2. Match Engine Player Ratings (`simatch.fmf` Frame `#118` — `player_ratings_data.jsb`)

Decoded from `simatch.fmf` `Frame #118` (`340,752` bytes). The file stores **6 model versions** (`v24.2.5.1`, `v25.1.0.0`, `v25.5.14.0`, `v26.1.7.0`, `v26.6.0.0`, and `v26.4.10.1`):
- **Starting Match Rating (`start_value`):** Across **all 6 versions**, `start_value = 6700` $\implies$ **`6.70`** on the `1.0–10.0` scale (`÷ 1000`).
- **Role Lookup Table (`role_lookup_data` & `role_data`):** Maps `40` `RolePosition` bitmasks (`1, 2, 4, 8, 16, 32, 64, 128, 512, 1024, ...`) into **`30` role-specific coefficient tables (`role_data[0..29]`)**, each defining `52` match action coefficients.
- **Team Expectation Multipliers (`expected_score_data` in `v26.4.10.1`):**
  - `Exceed Significant with Win` / `Exceed Significant with Draw`: `positive_multiplier = 1200` (**`1.20x`**), `negative_multiplier = 1000` (`1.00x`).
  - `Exceed with Win` / `Exceed with Draw`: `positive_multiplier = 1100` (**`1.10x`**), `negative_multiplier = 1000` (`1.00x`).
  - `Exceed Same Result` / `Neutral` / `Deceed *`: `positive_multiplier = 1000` (`1.00x`), `negative_multiplier = 1000` (`1.00x`).

### Exact Per-Action Rating Coefficients (`v26.4.10.1`, Raw Values & `÷ 1000` Rating Points):

| Match Action (`name` in `role_data`) | GK (`role_data[0]`) | Defender (`role_data[1..2]`) | Wing-Back (`role_data[4]`) | Def. Mid (`role_data[5]`) | Central/Wide Mid (`role_data[6]`) | Att. Mid / Striker (`role_data[8, 10]`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`start_value` (Baseline)** | `6700` (**`6.70`**) | `6700` (**`6.70`**) | `6700` (**`6.70`**) | `6700` (**`6.70`**) | `6700` (**`6.70`**) | `6700` (**`6.70`**) |
| **`90min Adjuster` (Role-Specific)** | `-720` (`-0.720`) | `-520 / -530` | `-680` (`-0.680`) | `-440` (`-0.440`) | `-750` (`-0.750`) | `-810` (AM) / `-600` (ST) |
| **`Goals`** | `600` (`+0.600`) | `500` (`+0.500`) | `500` (`+0.500`) | `500` (`+0.500`) | `500` (`+0.500`) | `550` (`+0.550`) |
| **`Good Goal Adder` / `Great Goal Adder`** | `+100 / +200` | `+100 / +200` | `+100 / +200` | `+100 / +200` | `+100 / +200` | `+100 / +200` |
| **`Decisive Goal` / `Decisive Late Goal`** | `+350 / +400` | `+350 / +400` | `+350 / +400` | `+350 / +400` | `+350 / +400` | `+350 / +400` |
| **`Cumulative Goal Bonus`** | `300` (`+0.300`) | `300` (`+0.300`) | `300` (`+0.300`) | `300` (`+0.300`) | `300` (`+0.300`) | `300` (`+0.300`) |
| **`Goals minus xG times 100 (only if negative)`** | `4` (`+0.004`) | `4` (`+0.004`) | `4` (`+0.004`) | `4` (`+0.004`) | `4` (`+0.004`) | `4` (`+0.004`) |
| **`Assists` / `Cumulative Assist Bonus`** | `300 / 200` | `300 / 200` | `300 / 200` | `300 / 200` | `350 / 200` | `350 / 200` |
| **`Shots` / `Shots On Target`** | `30 / 20` | `30 / 20` | `30 / 20` | `30 / 20` | `30 / 20` | `30 / 20` |
| **`Penalties Scored` / `Penalties Missed`** | `+350 / -200` | `+350 / -200` | `+350 / -200` | `+350 / -200` | `+350 / -200` | `+350 / -200` |
| **`Key Passes` / `Open Play xA`** | `30 / 7` | `30 / 7` | `30 / 7` | `30 / 7` | `40 / 7` | `40 / 7` |
| **`Passes Completed` / `Passes Incomplete`** | `7 / 0` | `5 / -15` | `7 / -21` | `7 / -21` | `7 / -21` | `7 / -21` (AM) / `-14` (ST) |
| **`Crosses Completed` / `Crosses Incompleted`** | `40 / -8` | `40 / -8` | `40 / -8` | `40 / -8` | `40 / -8` | `40 / -8` |
| **`Dribbles` / `Times Was Fouled`** | `20 / 30` | `20 / 30` | `20 / 30` | `20 / 30` | `20 / 30` | `20 / 30` |
| **`Tackles Won` / `Tackles Lost`** | `+40 / -20` | `+56 / -20` | `+56 / -20` | `+40 / -20` | `+40 / -20` | `+40 / -20` |
| **`Interceptions` / `Blocks` / `Clearances`** | `50 / 50 / 0` | `70 / 50 / 30` | `70 / 50 / 10` | `50 / 50 / 10` | `25 / 50 / 10` | `50/25 / 50 / 10` |
| **`Aerial Duels Won` / `Aerial Duels Lost`** | `+20 / -20` | `+20 / -20` | `+20 / -20` | `+20 / -20` | `+20 / -20` | `+20 / -20` |
| **`Fouls Committed`** | `-40` (`-0.040`) | `-40` (`-0.040`) | `-40` (`-0.040`) | `-40` (`-0.040`) | `-40` (`-0.040`) | `-40` (`-0.040`) |
| **`Mistakes Leading to Goals` / `Own Goal`** | `-300 / -300` | `-300 / -300` | `-300 / -300` | `-300 / -300` | `-300 / -300` | `-300 / -300` |
| **`Clean Sheet`** | `500` (`+0.500`) | `300` (`+0.300`) | `250` (`+0.250`) | `75` (`+0.075`) | `75` (`+0.075`) | `75` (AM) / `25` (ST) |
| **`Saves` / `Good Saves Adder` / `Great Saves Adder`** | `100 / 200 / 400` | `0` | `0` | `0` | `0` | `0` |
| **`Penalties Saved Adder` / `Keeper <5 Shot Boost`** | `450 / 125` | `0` | `0` | `0` | `0` | `0` |
| **`Yellow Card` / `Second Yellow Card` / `Red Card`** | `-50 / -100 / -300` | `-50 / -100 / -300` | `-50 / -100 / -300` | `-50 / -100 / -300` | `-50 / -100 / -300` | `-50 / -100 / -300` |
| **`Team Goals For` / `Team Goals Conceded`** | `+50 / -100` | `+50 / -100` | `+50 / -100` | `+50 / -100` | `+50 / -100` | `+50 / -100` |

---

## 3. Quick Match Engine (`QME`) Statistical Distributions (`simatch.fmf` Frames `#119` & `#120`)

When simulating background matches (other leagues or Instant Result), FM26 uses **3,137 Poisson (`1,803`), Normal (`630`), Binned (`580`), and Zero (`124`) probability distributions** (`Frame #119`, `qme_distribution_data.jsb`, `571,829` B) paired with **22 stat-relevant attribute sets** (`Frame #120`, `qme_stat_relevant_attribute_data.jsb`, `1,608` B):
1. `position` (`14` slots: `attacker_centre`, `attacking_midfielder_centre`, `attacking_midfielder_left`, `attacking_midfielder_right`, `defender_centre`, `defender_left`, `defender_right`, `defensive_midfielder`, `goalkeeper`, `midfielder_centre`, `midfielder_left`, `midfielder_right`, `wingback_left`, `wingback_right`),
2. `ability_window` (`3` `CA` brackets: `[0, 99]`, `[100, 129]`, `[130, 200]`),
3. `attribute_window` (`4` brackets on the `1..20` average of the stat's relevant attributes from `Frame #120`: `[0, 7]`, `[8, 11]`, `[12, 15]`, `[16, 20]`),
4. `stat_type` (`22` match stats).

### Complete 22 `stat_type -> relevant_attributes` Mappings (`Frame #120` — `qme_stat_relevant_attribute_data.jsb`):

| `stat_type` | Official `relevant_attributes` (`Frame #120`) |
| :--- | :--- |
| **`passes_attempted`** | `passing`, `work_rate` |
| **`pass_completion`** | `passing`, `decisions` |
| **`key_passes`** | `passing`, `vision` |
| **`progressive_passes`** | `passing`, `vision` |
| **`crosses_attempted`** | `crossing`, `work_rate` |
| **`cross_completion`** | `crossing`, `vision`, `technique` |
| **`tackles_attempted`** | `tackling`, `positioning`, `work_rate` |
| **`tackle_completion`** | `tackling`, `positioning` |
| **`key_tackles`** | `tackling`, `positioning`, `work_rate` |
| **`interceptions`** | `anticipation`, `positioning` |
| **`blocks`** | `anticipation`, `positioning`, `bravery` |
| **`clearances`** | `positioning` |
| **`headers_attempted`** | `positioning`, `jumping` |
| **`header_completion`** | `heading`, `strength`, `jumping` |
| **`key_headers`** | `positioning`, `jumping` |
| **`fouls_made`** | `dirtiness`, `aggression` |
| **`dribbles`** | `dribbling`, `flair`, `pace`, `acceleration` |
| **`offsides`** | `movement`, `work_rate`, `acceleration`, `concentration` |
| **`distance_run`** | `work_rate`, `stamina`, `pace` |
| **`sprints`** | `work_rate`, `stamina` |
| **`pressures_attempted`** | `work_rate`, `anticipation` |
| **`pressures_completion`** | `work_rate`, `anticipation`, `acceleration` |

---

## 4. AI Starting XI Team Selection Formula (`simatch.fmf` Frame `#223` — `weights.jsb`)

Decoded from `simatch.fmf` `Frame #223` (`6,547` bytes). AI managers score each candidate player across **4 `TEAM_PICKING_STYLE` profiles** (`TPS_FIRST_TEAM_PICKING`, `TPS_SLIGHTLY_RESERVE_PICKING`, `TPS_SEMI_RESERVE_PICKING`, `TPS_TOTAL_RESERVE_PICKING`) using **40 `simatchshared::TSF_*` factors**:

| AI Selection Factor (`simatchshared::TSF_*`) | `TPS_FIRST_TEAM_PICKING` | `TPS_SLIGHTLY_RESERVE_PICKING` | `TPS_SEMI_RESERVE_PICKING` | `TPS_TOTAL_RESERVE_PICKING` |
| :--- | :---: | :---: | :---: | :---: |
| **`TSF_HUMAN_SELECTION`** | `+500` | `+500` | `+500` | `+500` |
| **`TSF_CUP_KEEPER`** | `+310` | `+310` | `+310` | `+310` |
| **`TSF_DECLARED_FOR_RESERVES`** | `+170` | `+160` | `+150` | `+140` |
| **`TSF_POSITION_ABILITY` (Positional Familiarity)** | **`+150`** | **`+150`** | **`+130`** | **`+130`** |
| **`TSF_CA` (Current Ability)** | **`+120`** | **`+100`** | **`+90`** | **`+90`** |
| **`TSF_EXTRA_ADJ`** | `+110` | `+110` | `+110` | `+110` |
| **`TSF_LAST_RATINGS` (Recent Match Ratings)** | **`+95`** | **`+90`** | **`+80`** | **`+60`** |
| **`TSF_PA` (Potential Ability)** | **`+90`** | **`+100`** | **`+110`** | **`+120`** |
| **`TSF_CONDITION` (Physical Condition)** | **`+80`** | `+80` | `+80` | `+80` |
| **`TSF_POSITION_ABILITY_IN_ROLE` (Role Suitability)** | **`+80`** | `+70` | `+70` | `+70` |
| **`TSF_OLYMPIC_U23` / `TSF_POSITION_TACTICAL_FAMILARITY`** | `+65 / +60` | `+45 / +60` | `+25 / +60` | `+15 / +60` |
| **`TSF_CAPTAINCY`** | **`+40`** | `+30` | `+15` | `+10` |
| **`TSF_REPUTATION` / `TSF_STAR_PLAYER` / `TSF_DISLIKE_BY_NON_PLAYER`** | `+35 / +35 / +35` | `+20 / +35 / +35` | `+10 / +25 / +35` | `+10 / +15 / +25` |
| **`TSF_FORM` / `TSF_MATCH_RATING_TIME_ON` / `TSF_PPMS`** | `+25 / +25 / +25` | `+20 / +25 / +25` | `+15 / +25 / +25` | `+15 / +25 / +25` |
| **`TSF_BOOST_LOW_MATCH_FITNESS`** | `+20` | `+35` | `+45` | **`+60`** |
| **`TSF_LOAN_TERMS` / `TSF_MATCH_FITNESS` / `TSF_PLAYING_SIDE_PREFERENCE`** | `+20 / +20 / +20` | `+20 / +15 / +20` | `+20 / +15 / +15` | `+20 / +15 / +15` |
| **`TSF_AGREED_PLAYING_TIME` / `TSF_BOOST_SUBSTITUTE` / `TSF_FOOTBALL_PROMISES`** | `+15 / +15 / +15` | `+15 / +35 / +30` | `+15 / +35 / +30` | `+15 / +35 / +30` |
| **`TSF_MORALE` / `TSF_UNHAPPINESS` / `TSF_USE_INSIDE_FOOTED_WINGER`** | `+15 / +15 / +10` | `+10 / +15 / +10` | `+10 / +15 / +10` | `+5 / +15 / +10` |
| **`TSF_NEED_MATCH_XP` / `TSF_YOUNG_PLAYERS` / `TSF_INTEGRATION`** | `+15 / +5 / +5` | `+55 / +15 / +5` | `+75 / +25 / 0` | **`+95 / +50 / 0`** |
| **`TSF_VIRTUAL` / `TSF_UPCOMING_SUSPENSION`** | `-50 / -90` | `-50 / -100` | `-50 / -130` | `-50 / -150` |
| **`TSF_REST_PROMISES` / `TSF_ALLOWED_MINS`** | **`-190 / -250`** | `-210 / -250` | `-230 / -250` | **`-250 / -250`** |

---

## 5. Out-Of-Possession (`OP*`) Role Attribute Scoring (`simatch.fmf` Frame `#114`) & Pitch Proximity Grid (`Frame #115`)

- **`Frame #114` (`oop_attributes_scoring.jsb`, `2,115` B):** Defines **39 Out-Of-Possession `RolePosition` bitmasks** ($2^0=1$ through $2^{45}=35,184,372,088,832$) and maps each bitmask to its official engine `ATTRIBUTES` ID list (from the 13 core defensive/transition attribute IDs `[20, 21, 24, 32, 33, 35, 44, 47, 51, 52, 53, 60, 68]`).
- **`Frame #115` (`oop_pitch_proximity_scores.jsb`, `93,429` B):** Defines **118 `(Position, Role)` entries × `24` target `(Position, Side)` zones = `2,832` `[Min, Max]` spatial proximity intervals** used by the match engine to position players when the team is out of possession.

---

## 6. Anthropometric Height → Jumping Reach & Aerial Reach Tables (`tables.fmf`) & Training Effects (`training.fmf`)

- **`shared/data/shared/tables.fmf` (`Frames #0 & #2`):**
  - `Frame #0` (`tables/aerial_reach.jsb`, `3,721` B) defines `female_data` (`23` height steps from `max_height = 147 cm` to `199 cm`) and `male_data` (`23` height steps from `max_height = 158 cm` to `210 cm`), mapping each height step to `5` attribute tiers (`poor`, `below_average`, `average`, `above_average`, `good` on the `1..20` scale; e.g., for `male_data` at `158 cm`: `1..5`, at `180 cm`: `7..15`, at `210 cm`: `16..20`).
  - `Frame #2` (`tables/jumping_reach.jsb`, `3,242` B) defines `female_data` (`23` height steps from `max_height = 147 cm` to `195 cm`) and `male_data` (`17` height steps from `max_height = 161 cm` to `200 cm`) across the same `5` quality tiers (`poor..good` on `1..20`; e.g., for `male_data` at `161 cm`: `1..5`, at `180 cm`: `7..14`, at `200 cm`: `16..20`).
- **`data/game_simulation/training.fmf` (`Frames #1..#4`):** Defines `training_item_effects.jsb` (`Frame #1`), `164` Full-Time weekly schedules (`Frame #2`), `136` Youth/Part-Time weekly schedules (`Frame #3`), and `training_sessions_weights.jsb` (`Frame #4`, `60%` primary / `20–40%` secondary / `20%` tertiary attribute progression weights).

---

# Part II — Heuristic & Empirical Save-Fitted Models

> **Important Note on Provenance:** The formulas in Part II below are **empirical statistical regressions and domain heuristics** fitted and cross-validated on `.fm` save databases (`game_db.dat`), not `.jsb` tables from `.fmf` archives.

## 7. Current Ability (`CA`) & Potential Ability (`PA`) Positional Attribute Weights

### 7.1 Internal Representation in `game_db.dat`
Every player record in `game_db.dat` stores ability values in its `Ability` block (`u16` Little-Endian, `1..200` scale: `current` and `potential`). In specific save builds (e.g., `26.3.2`), tail bytes after `height_offset` (`+117..+119`) also hold `squad_number`, a peak/recommended `CA` byte, and a mirrored `PA` byte; [`decode_players_enriched_relations()`](../fm26save/enrichment.py#L316-L327) validates `raw_b119 == player.ability.potential` before exposing `rca_peak_byte_118` so it never misreads shifted offsets on earlier builds (`26.1.0`/`26.1.1`).

### 7.2 Empirical Position-Specific `CA` Attribute Weights (`0..10` Normalized Scale)
In FM, **Current Ability (`CA`) is a position-weighted function of visible `1..20` attributes and `WeakFoot = min(left_foot, right_foot)`**:

$$
\widehat{\text{CA}}_{\text{pos}} = \alpha_{\text{pos}} + \beta_{\text{pos}} \sum_{i} w_{\text{pos}, i} \cdot \text{Attr}_i + \gamma_{\text{pos}} \cdot \text{WeakFoot}
$$

| Attribute | `GK` | `DC` | `DL/DR` | `WBL/WBR` | `DM` | `MC` | `ML/MR` | `AMC` | `AML/AMR` | `STC` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Decisions** | **10.0** | **10.0** | **8.0** | **7.4** | **10.0** | **7.7** | 4.6 | 5.1 | 4.4 | 3.7 |
| **Acceleration** | 5.9 | 5.0 | **10.0** | **10.0** | **6.7** | **10.0** | **10.0** | **10.0** | **10.0** | **10.0** |
| **Pace** | — | 4.4 | **8.6** | **8.0** | 4.9 | **8.4** | **9.4** | **8.2** | **9.8** | **6.6** |
| **Weak Foot (`1..20`)** | 2.2 | 4.4 | 5.9 | 5.9 | **6.9** | **9.2** | **6.0** | **7.8** | 5.5 | **7.7** |
| **Agility** | **7.7** | 5.2 | **7.3** | **6.6** | **6.7** | **7.0** | **7.2** | 5.4 | **6.1** | 5.2 |
| **Stamina** | — | 2.3 | **7.1** | **6.9** | 4.0 | **7.6** | **6.4** | 5.7 | 5.9 | 5.2 |
| **Strength** | 3.7 | 5.6 | **6.0** | 5.1 | 5.9 | 5.1 | 3.6 | 3.0 | 3.2 | 5.6 |
| **Positioning** | 4.2 | **8.1** | 4.6 | — | 5.6 | 3.0 | — | — | — | — |
| **Marking** | — | **8.2** | 3.3 | 3.8 | 5.0 | — | — | — | — | — |
| **Tackling** | — | 4.3 | 4.2 | 3.4 | 5.8 | 3.8 | — | — | — | — |
| **Jumping Reach / Heading** | — | **6.0 / 4.2** | — / 3.5 | — | — | — | — | — | — | 4.5 / 4.8 |
| **First Touch / Passing** | — / 2.0 | 2.0 / 1.9 | 3.9 / 2.4 | 4.4 / 3.5 | 4.2 / 3.6 | **6.9 / 5.8** | 4.0 / 2.4 | 4.3 / 3.3 | 4.0 / 2.1 | 5.0 / — |
| **Vision / Technique** | — | — | — | — / 2.6 | 3.8 / — | **6.2 / 4.6** | 2.5 / 3.2 | 5.0 / 4.4 | — / 2.5 | — / 3.3 |
| **Finishing / Off The Ball** | — | — | — | — / 2.7 | — | — / 3.3 | — / 2.6 | 2.5 / 2.7 | 2.2 / 2.3 | **7.5 / 5.4** |
| **Reflexes / Handling** | **7.8 / 7.7** | — | — | — | — | — | — | — | — | — |

- **Zero-CA-Cost Attributes:** `Determination`, `Flair`, `Aggression`, `Natural Fitness`, `Leadership`, `Eccentricity`, and all 8 hidden personality attributes (`Professionalism`, `Ambition`, `Loyalty`, `Pressure`, `Sportsmanship`, `Temperament`, `Controversy`, `Adaptability`).

---

## 8. Heuristic Tactical Role Effectiveness & Dual-Role Scoring (`calculate_role_effectiveness`)

To evaluate player suitability across **50 In-Possession roles (`93` Role × Duty variants)** and **39 Out-Of-Possession (`OP*`) roles**:
- Key Attributes $K_{R,D}$ carry weight $w_{\text{key}} = 2.0$, and Preferable Attributes $P_{R,D}$ carry weight $w_{\text{pref}} = 1.0$:

$$
S_{\text{raw}, 20}(R, D) = \frac{2.0 \sum_{a \in K_{R,D}} \text{Attr}_a + 1.0 \sum_{b \in P_{R,D}} \text{Attr}_b}{2.0 \cdot |K_{R,D}| + 1.0 \cdot |P_{R,D}|}, \qquad S_{\text{eff}, 100} = \min\bigl(100.0,\; 5.0 \times S_{\text{raw}, 20} \times M_{\text{pos}} \times M_{\text{foot}}\bigr)
$$

- **Combined Dual-Role Score:** $S_{\text{dual}, 100}(\text{IP}, \text{OOP}) = 0.55 \cdot S_{\text{eff}, 100}(\text{IP}) + 0.45 \cdot S_{\text{eff}, 100}(\text{OOP})$.

---

## 9. Empirical Market Transfer Value OLS Models (`estimate_transfer_value`)

Fitted via Ordinary Least Squares (OLS) with an **80/20 train/test split** across **$N = 22,744$ priced players** ($N_{\text{train}} = 18,195$, $N_{\text{test}} = 4,549$). To avoid circular dependency when weekly wage is also being estimated, [`estimate_transfer_value()`](../fm26save/formulas.py#L1456-L1531) provides two explicit models:

### 9.1 Model A — Non-Circular Fundamental Transfer Value Model (No `weekly_wage` Input; $R^2_{\text{train}} = 0.6603$, $R^2_{\text{test}} = 0.6483$)

$$
\begin{aligned}
\ln(\text{TransferValue}_{\text{fund}}) &= 5.00991 + 0.06394 \cdot \text{CA} + 0.00870 \cdot \max(0, \text{CA} - 115) \\
&\quad + 0.37803 \cdot \left(\frac{\text{PlayerRep}}{1000}\right) - 0.15045 \cdot \left(\frac{\text{WorldRep}}{1000}\right) - 0.10709 \cdot \left(\frac{\text{ClubRep}}{1000}\right) \\
&\quad - 0.02096 \cdot \text{Age} - 0.01051 \cdot \max(0, \text{Age} - 28) + 0.88464 \cdot \ln(\text{RemainingContractYears}) \\
&\quad + 0.50407 \cdot \frac{\max(0, 24 - \text{Age}) \cdot \max(0, \text{PA} - \text{CA})}{100} - 0.10433 \cdot \mathbb{I}(\text{StarOrImportant})
\end{aligned}
$$

### 9.2 Model B — Wage-Augmented Transfer Value Model (When Observed `weekly_wage` Is Provided; $R^2_{\text{train}} = 0.7807$, $R^2_{\text{test}} = 0.7713$)

$$
\begin{aligned}
\ln(\text{TransferValue}_{\text{aug}}) &= 5.04580 + 0.05068 \cdot \text{CA} + 0.00288 \cdot \max(0, \text{CA} - 115) \\
&\quad + 0.15565 \cdot \left(\frac{\text{PlayerRep}}{1000}\right) - 0.11417 \cdot \left(\frac{\text{WorldRep}}{1000}\right) - 0.19934 \cdot \left(\frac{\text{ClubRep}}{1000}\right) \\
&\quad - 0.13142 \cdot \text{Age} + 0.07498 \cdot \max(0, \text{Age} - 28) + 0.56851 \cdot \ln(\text{RemainingContractYears}) \\
&\quad + 0.74275 \cdot \ln(\text{WeeklyWage}) + 0.53800 \cdot \frac{\max(0, 24 - \text{Age}) \cdot \max(0, \text{PA} - \text{CA})}{100} \\
&\quad - 0.18352 \cdot \mathbb{I}(\text{StarOrImportant})
\end{aligned}
$$

*(Note: In multiple regression with `CA`, `PlayerRep`, and `WeeklyWage` controlled simultaneously, `ClubRep` and `WorldRep` take small negative partial slopes due to collinearity with `CA`/`Wage`; their univariate correlations with `ln(TransferValue)` are strongly positive.)*

---

## 10. Empirical Weekly Wage, Signing/Loyalty Fee (`money_a`) & Agent Fee (`money_b`) (`estimate_wage_and_fees`)

$$
\begin{aligned}
\ln(\text{WeeklyWage}) &= 1.04103 + 0.01843 \cdot \text{CA} + 0.02248 \cdot \max(0, \text{CA} - 115) - 0.01802 \cdot \max(0, \text{CA} - 145) \\
&\quad + 0.08630 \cdot \left(\frac{\text{PlayerRep}}{1000}\right) + 0.02394 \cdot \left(\frac{\text{WorldRep}}{1000}\right) + 0.19201 \cdot \left(\frac{\text{ClubRep}}{1000}\right) \\
&\quad + 0.09904 \cdot \text{Age} - 0.00302 \cdot \max(0, \text{Age} - 29) + \Delta_{\text{SquadStatus}}
\end{aligned}
$$

### Empirical Distribution of Decoded Contract Unknowns (`contracts.unknown`):
| Hidden Field | Meaning | Non-Zero Share | Unconditional Median (`All Contracts`) | Conditional Median (`Non-Zero Contracts`) | Conditional Mean (`Non-Zero`) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **`money_a`** | **Signing-On / Loyalty Bonus Pool** | `61.0%` (`39.0%` zero) | **`5.0%`** of annual wage | **`18.5%`** of annual wage | **`24.1%`** of annual wage |
| **`money_b`** | **Agent Commission Fee** | `29.0%` (`71.0%` zero) | **`0.0%`** | **`5.2%`** of annual wage | **`5.9%`** of annual wage |
| **`money_c`** | **Secondary Package Bonus** | `2.6%` (`97.4%` zero) | `0.0%` | `1.4%` of annual wage | — |
| **`e12`** | **Contract Option / Reference Year (`u16`)** | `61.0%` (`39.0%` `1900` null sentinel) | Mapped to `None` when `<= 1900`; `2012..2030+` when active | — | — |
