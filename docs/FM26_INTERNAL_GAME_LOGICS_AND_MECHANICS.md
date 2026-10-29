# Football Manager 26 — Internal Game Logics & Simulation Mechanics Reference

> **Repository:** [`fm-toolkit`](../)  
> **Scope:** Complete reverse-engineered reference of **18 core internal simulation algorithms and game logics** in Football Manager 26 (`v26.2.0` / Build `2620`), extracted directly from `.fmf` / `.jsb` engine archives (`simatch.fmf`, `training.fmf`, `tables.fmf`, `simatchshared.fmf`, `editor.fmf`), pre-game master databases (`client_db.dat`, `server_db.dat`, `.edt`), IL2CPP symbols (`global-metadata.dat`, `il2cpp.usym`), and `.fm` save containers (`game_db.dat`).

---

## Table of Contents

1. [Youth Intake & Newgen Generation Pipeline (`NYRt`, `Crcb`, `Cytv`, `Cyfb`, `HOYD`)](#1-youth-intake--newgen-generation-pipeline)
2. [AI Team Selection & Squad Rotation Engine (`weights.jsb` — 4 Profiles × 40 `TSF_*` Factors)](#2-ai-team-selection--squad-rotation-engine-weightsjsb)
3. [Match Rating Calculation Engine (`player_ratings_data.jsb` — `6.70` Base & 52 Actions)](#3-match-rating-calculation-engine-player_ratings_datajsb)
4. [Weekly Training Engine (`training.fmf` — 44 Session Attribute Weights & Physical/Happiness Effects)](#4-weekly-training-engine-trainingfmf)
5. [Player Progression, CA Growth, Coaching Star Formula & Aging Mechanics](#5-player-progression-ca-growth-coaching-star-formula--aging-mechanics)
6. [Match Engine: Expected Goals (`xG`), Spatial Momentum (`48` Rules) & Quick Match Engine (`QME`)](#6-match-engine-expected-goals-xg-spatial-momentum--quick-match-engine-qme)
7. [Dual-Formation Engine: Out-Of-Possession (`OOP`) 24-Zone Grid & 10 Tactical Styles](#7-dual-formation-engine-out-of-possession-oop-24-zone-grid--10-tactical-styles)
8. [Medical Centre & Injury Simulation Engine (`server_db.dat` — 136 Injuries)](#8-medical-centre--injury-simulation-engine-server_dbdat)
9. [Sugar Daddy Tycoons, Board Takeovers, International Treaties & Transfer Valuation Logic](#9-sugar-daddy-tycoons-board-takeovers-international-treaties--transfer-valuation-logic)
10. [Squad Dynamics, Mentoring Groups & Hidden `PersonBlock` Relationships](#10-squad-dynamics-mentoring-groups--hidden-personblock-relationships)
11. [Team Talks, Touchline Shouts, Press Conferences (`media.fmf`) & Morale / Body Language Algorithm](#11-team-talks-touchline-shouts-press-conferences-mediafmf--morale--body-language-algorithm)
12. [Scouting Knowledge (`0..100%`), Dual-Role Recruitment Focuses & Star Rating ("Fog of War") Algorithm](#12-scouting-knowledge-0100-dual-role-recruitment-focuses--star-rating-fog-of-war-algorithm)
13. [Dynamic League Reputation, 5-Year & 10-Year Continental Coefficients & Prize Money Algorithm](#13-dynamic-league-reputation-5-year--10-year-continental-coefficients--prize-money-algorithm)
14. [Contract Negotiations (`contract_offer.xml` — 66 FourCCs), Agent Patience & Transfer Bid Evaluation Algorithm](#14-contract-negotiations-contract_offerxml--66-fourccs-agent-patience--transfer-bid-evaluation-algorithm)
15. [Financial Fair Play (`FFP`), Crowd Attendance (`CrowdAttendanceScalar`), Ticket Prices & Dynamic Sponsorships](#15-financial-fair-play-ffp-crowd-attendance-crowdattendancescalar-ticket-prices--dynamic-sponsorships)
16. [Board Confidence, Supporter Confidence & `ClubVision` Composite Scoring Algorithm](#16-board-confidence-supporter-confidence--clubvision-composite-scoring-algorithm)
17. [Match Environment Physics: 4-Season Weather (`weather.xml`), Altitude (`altitude_ft`), Pitch Dimensions & Referees (`official.xml`)](#17-match-environment-physics-4-season-weather-weatherxml-altitude-altitude_ft-pitch-dimensions--referees-officialxml)
18. [Automated Set-Piece Priority Matrix, Hat-Trick Penalty Rule & Ballon d'Or / Hall of Fame Scoring Algorithm](#18-automated-set-piece-priority-matrix-hat-trick-penalty-rule--ballon-dor--hall-of-fame-scoring-algorithm)

---

## 1. Youth Intake & Newgen Generation Pipeline

Every season, FM generates new academy cohorts (**Newgens / Regens**) through a deterministic **6-stage hierarchical pipeline** governed by parameters in `editor.fmf` (`Frame #045: nation.xml` and `Frame #032: club.xml`), `server_db.dat`, `client_db.dat`, `shared/tables.fmf`, and `simatchshared.fmf`.

```mermaid
flowchart TD
    A["Stage 1: National Talent Pool Ceiling\nNYRt (Youth Rating 0..200) + Ngim (Game Importance 1..4)\n+ State of Development (1..3) + Economic Factor (1..20) + Nation Reputation"] --> B["Stage 2: Club Draft / Allocation Priority\nCrcb (Youth Recruitment 1..20) + Club Reputation (1..10000)\n+ Cyim (Youth Importance 1..20) + Regional Competition & Affiliates"]
    B --> C["Stage 3: Potential (PA) vs. Starting Current Ability (CA)\nPA Ceiling <- NYRt + Crcb + Club Reputation + EPPP Category\nStarting CA <- Cytv (Youth Coaching 1..20) + Cyfb (Youth Facilities 1..20)"]
    C --> D["Stage 4: Positions, Tactical Archetypes & Personality\nHead of Youth Development (HOYD, r4=16):\nPreferred Formation + Coaching Style + Hidden Personality (block_40)"]
    D --> E["Stage 5: Physical Caps & Attribute Distribution\ntables.fmf (Height 155..210cm -> Jumping/Aerial Reach Caps)\n+ Positional CA Weight Distribution"]
    E --> F["Stage 6: Identity, Birth City & 3D Appearance\nclient_db.dat (294K First + 599K Last Names + 58.3K Cities)\n+ simatchshared.fmf (135 Regional Hair/Skin Rules)"]
```

### 1.1 Stage 1 — National Talent Pool Ceiling (`nation.xml` & `server_db.dat`)
Before any club receives a player, the nation's overall youth quality curve is bounded by five national parameters (`editor.fmf` `Frame #045` & `client_db.dat` `Frame #11`):

| FourCC / Field | Range / Enum | Engine Role |
| :--- | :---: | :--- |
| **`NYRt` (`Youth Rating`)** | `0 .. 200` | Base national talent ceiling (referenced in `global-metadata.dat` as `DebugNationYouthRatingTableReference`). |
| **`Ngim` (`Game Importance`)** | `1 .. 4` | `1 = Very Important`, `2 = Important`, `3 = Fairly Unimportant`, `4 = Unimportant`. Any value worse than `1` severely penalizes the upper tail of the nation's PA distribution even if `NYRt` is high. |
| **`State of Development`** | `1 .. 3` | `1 = Developed`, `2 = Developing`, `3 = Third World`. Modulates baseline infrastructure efficiency and starting CA readiness. |
| **`Economic Factor` & `Nfap`** | `1 .. 20` | National economic strength (`offset +19` in `client_db.dat` `Frame #11`) and `FA Financial Power` (`Nfap`). |
| **`Nation Reputation`** | `1 .. 10000` | Dynamic national football reputation (evolves over time as clubs/national teams perform in continental competitions). |

**Sample National Parameters from `client_db.dat` (`2620`):**

| Nation | State of Development | Economic Factor (`1..20`) | Game Importance (`Ngim`) | Years to Gain Nationality |
| :--- | :--- | :---: | :--- | :---: |
| **England** (`id=139`) | `Developed (1)` | `19` | `Very Important (1)` | `5` |
| **France** (`id=143`) | `Developed (1)` | `19` | `Very Important (1)` | `5` |
| **Italy** (`id=150`) | `Developed (1)` | `18` | `Very Important (1)` | `10` |
| **Germany** (`id=145`) | `Developed (1)` | `19` | `Important (2)` | `8` |
| **Spain** (`id=170`) | `Developed (1)` | `17` | `Important (2)` | `10` |
| **Brazil** (`id=189`) | `Developing (2)` | `16` | `Very Important (1)` | `4` |
| **Argentina** (`id=187`) | `Developing (2)` | `16` | `Very Important (1)` | `2` |
| **Colombia** (`id=191`) | `Developing (2)` | `13` | `Very Important (1)` | `5` |
| **Türkiye** (`id=173`) | `Developed (1)` | `10` | `Very Important (1)` | `5` |
| **United States** (`id=120`) | `Developed (1)` | `20` | `Important (2)` | `5` |

### 1.2 Stage 2 & Stage 3 — Club Allocation (`PA`) vs. Starting Readiness (`CA`)
In `editor.fmf` (`Frame #032: club.xml`), four distinct `1..20` club attributes govern academy output, each targeting a different part of the pipeline:

| FourCC | Editor / UI Field (`1..20`) | Primary Effect on Youth Intake |
| :--- | :--- | :--- |
| **`Crcb`** | **Youth Recruitment** | **Controls `PA` (Potential Ability) & Priority:** Determines the club's reach and priority in capturing the highest-PA prospects from the national pool (and foreign affiliate pools). Competes directly against nearby clubs with high **Club Reputation**. |
| **`Cytv`** | **Youth Coaching** *(Junior Coaching)* | **Controls Starting `CA` (Current Ability):** Determines how developed the 15/16-year-old prospect already is on the day they generate in the intake. |
| **`Cyfb`** | **Youth Facilities** | **Controls Post-Intake Youth Growth (and secondary Starting `CA`):** Governs how rapidly U18/U19 players convert their remaining `PA` into `CA` while training at the academy. |
| **`Cyim`** | **Youth Importance** | **Board Youth Philosophy (`1..20`):** Weighs how heavily the board prioritizes academy upgrades and youth intake investment. |

* **English EPPP Academy Grades (`eng_youth_grades.edt`):** In England, 95 clubs have permanent EPPP Academy Category ratings (`Category 1..4`) in `shared/data/database/db/2620/edt/permanent/eng_youth_grades.edt` that further cap or boost youth recruitment tiers.
* **Foreign Feeder / Affiliate Pipelines (`club.xml` IDs `312826` & `510183`):** Clubs with `"Youth Players Training"` (`312826`) or `"Regional Academy"` (`510183`) affiliations can draw dual-nationality newgens evaluated against the **affiliate nation's `NYRt` pool**.

### 1.3 Stage 4 — Head of Youth Development (`HOYD`, `r4 = 16`) Influence
The staff member assigned to **Provides Youth Development Information** (typically the **Head of Youth Development**, `job_role_id = 16` in `constants.py`) shapes the intake cohort in four ways:
1. **December Preview vs. March/April Intake (`global-metadata.dat`):**
   - `ExecuteDecemberDecentYouthCandidatesCountDecentYouthCandidatesListDecimalDecimal` and `YouthCandidatesPositionPreviewReference` generate the mid-season position/grade preview (`A..F`), while `RankedYouthCandidatesReference` finalizes the spring intake.
2. **Positional Distribution (`Preferred Formation`):**
   - The cohort's positions are sampled from the HOYD's **Preferred Formation** (e.g., a HOYD preferring a narrow `5-3-2` will rarely produce pure `AML/AMR` wingers, whereas a `4-2-3-1` HOYD regularly produces wide forwards and `#10`s).
3. **Personality & Hidden Attribute Inheritance (`block_40`):**
   - Roughly `20–30%` of generated prospects inherit their hidden personality vector (`Professionalism`, `Determination`, `Ambition`, `Pressure`, `Temperament`, `Sportsmanship`, `Loyalty`) from the HOYD's `26`-byte `block_40` hidden staff attributes.
4. **Coaching Style Bias (`translation_id=242543`):**
   - The HOYD's `Coaching Style` (*Attacking, Defending, Fitness, Technical, Mental, General*) tilts initial attribute points toward that category.

### 1.4 Stage 5 & Stage 6 — Physical Height Caps (`tables.fmf`) & Ethnic Appearance (`simatchshared.fmf`)
1. **Height-to-Jumping & Aerial Reach Hard Caps (`shared/data/shared/tables.fmf`):**
   - Once a newgen's height (`cm`) is rolled, `height_to_jumping_reach.jsb` and `height_to_aerial_reach.jsb` enforce hard `min_value` / `max_value` bounds (internal `0..100` scale, divide by `5` for `1..20`):

| Height Bracket (`cm`) | Jumping Reach Min..Max (`0..100` \| `1..20`) | Aerial Reach Min..Max (`0..100` \| `1..20`) |
| :--- | :---: | :---: |
| **`155 – 165 cm`** | `0 .. 12` (`0.0 .. 2.4`) | `4 .. 16` (`0.8 .. 3.2`) |
| **`165 – 170 cm`** | `8 .. 36` (`1.6 .. 7.2`) | `8 .. 40` (`1.6 .. 8.0`) |
| **`170 – 175 cm`** | `12 .. 48` (`2.4 .. 9.6`) | `12 .. 48` (`2.4 .. 9.6`) |
| **`175 – 180 cm`** | `24 .. 60` (`4.8 .. 12.0`) | `20 .. 60` (`4.0 .. 12.0`) |
| **`180 – 185 cm`** | `36 .. 76` (`7.2 .. 15.2`) | `36 .. 76` (`7.2 .. 15.2`) |
| **`185 – 190 cm`** | `52 .. 84` (`10.4 .. 16.8`) | `48 .. 84` (`9.6 .. 16.8`) |
| **`190 – 195 cm`** | `60 .. 92` (`12.0 .. 18.4`) | `60 .. 92` (`12.0 .. 18.4`) |
| **`195 – 200 cm`** | `68 .. 96` (`13.6 .. 19.2`) | `68 .. 96` (`13.6 .. 19.2`) |
| **`200 – 210 cm`** | `80 .. 100` (`16.0 .. 20.0`) | `72 .. 100` (`14.4 .. 20.0`) |

2. **Name Pools, Birth City & 3D Appearance (`client_db.dat` & `simatchshared.fmf`):**
   - Names are drawn from `client_db.dat` `Frame #17` (`294,103` First Names) and `Frame #18` (`599,900` Surnames) matching the player's language/ethnicity.
   - Birth cities are sampled from `client_db.dat` `Frame #02` (`58,349` Cities) weighted by `local_region_id` proximity to the club and `inhabitants_bracket`.
   - Hair length, hair colour, and skin tone are generated via `simatchshared.fmf` `Frame #074` (`player_hair_length_colour_config_data.jsb`, `135` regional/ethnic probability rules).

---

## 2. AI Team Selection & Squad Rotation Engine (`weights.jsb`)

In `shared/data/simatch.fmf` (`Frame #223`: `weights.jsb`, `6,547` bytes), FM26 defines the exact linear scoring weights used by AI managers (and the **"Quick Pick"** assistant button) across **4 Team Picking Styles (`TPS_*`)** and **40 Team Selection Factors (`simatchshared::TSF_*`)**.

For every candidate player and every slot in the formation, the engine sums `weight * normalized_factor_score`:

| Team Selection Factor (`simatchshared::TSF_*`) | `TPS_FIRST_TEAM_PICKING` *(Full Strength)* | `TPS_SLIGHTLY_RESERVE_PICKING` *(Light Rotation)* | `TPS_SEMI_RESERVE_PICKING` *(Cup / Heavy Rotation)* | `TPS_TOTAL_RESERVE_PICKING` *(Dead Rubber / Youth)* | What It Measures |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`TSF_HUMAN_SELECTION`** | `+500` | `+500` | `+500` | `+500` | Locked in slot by human manager |
| **`TSF_CUP_KEEPER`** | `+310` | `+310` | `+310` | `+310` | Designated Cup Goalkeeper promise/role |
| **`TSF_DECLARED_FOR_RESERVES`** | `+170` | `+160` | `+150` | `+140` | First-team player made available for reserves |
| **`TSF_POSITION_ABILITY`** | **`+150`** | **`+150`** | **`+130`** | **`+130`** | Positional familiarity (`1..20` at slot) + ability |
| **`TSF_CA` (Current Ability)** | **`+120`** | **`+100`** | **`+90`** | **`+90`** | Player's Current Ability (`CA`) |
| **`TSF_EXTRA_ADJ`** | `+110` | `+110` | `+110` | `+110` | Tactical / opposition specific adjustment |
| **`TSF_LAST_RATINGS`** | **`+95`** | **`+90`** | **`+80`** | **`+60`** | Recent 5-match average rating |
| **`TSF_PA` (Potential Ability)** | **`+90`** | **`+100`** | **`+110`** | **`+120`** | Player's Potential Ability (`PA` / perceived PA) |
| **`TSF_CONDITION`** | `+80` | `+80` | `+80` | `+80` | Current physical condition (`0..10000`) |
| **`TSF_POSITION_ABILITY_IN_ROLE`** | `+80` | `+70` | `+70` | `+70` | Suitability for the specific Tactical Role |
| **`TSF_OLYMPIC_U23`** | `+65` | `+45` | `+25` | `+15` | U23 eligibility boost |
| **`TSF_POSITION_TACTICAL_FAMILARITY`** | `+60` | `+60` | `+60` | `+60` | Tactical familiarity in role/duty |
| **`TSF_CAPTAINCY`** | `+40` | `+30` | `+15` | `+10` | Club Captain / Vice-Captain status |
| **`TSF_REPUTATION`** | `+35` | `+20` | `+10` | `+10` | Player Reputation (`1..10000`) |
| **`TSF_STAR_PLAYER`** | `+35` | `+35` | `+25` | `+15` | Star Player / Key Player status |
| **`TSF_DISLIKE_BY_NON_PLAYER`** | `+35` | `+35` | `+35` | `+25` | Manager personal preference / dislike modifier |
| **`TSF_FORM`** | `+25` | `+20` | `+15` | `+15` | Overall season form streak |
| **`TSF_MATCH_RATING_TIME_ON`** | `+25` | `+25` | `+25` | `+25` | Minutes-weighted match rating |
| **`TSF_PPMS`** | `+25` | `+25` | `+25` | `+25` | Player Traits (`PPM`) synergy with role |
| **`TSF_BOOST_LOW_MATCH_FITNESS`** | `+20` | `+35` | `+45` | **`+60`** | Boost to build match sharpness for rusty players |
| **`TSF_LOAN_TERMS`** | `+20` | `+20` | `+20` | `+20` | Loan agreement playing-time clauses |
| **`TSF_MATCH_FITNESS`** | `+20` | `+15` | `+15` | `+15` | Current match sharpness |
| **`TSF_PLAYING_SIDE_PREFERENCE`** | `+20` | `+20` | `+15` | `+15` | Preferred foot / side of pitch (`L/R`) |
| **`TSF_AGREED_PLAYING_TIME`** | `+15` | `+15` | `+15` | `+15` | Squad status playing-time expectation |
| **`TSF_BOOST_SUBSTITUTE`** | `+15` | `+35` | `+35` | `+35` | Bench rotation boost |
| **`TSF_FOOTBALL_PROMISES`** | `+15` | `+30` | `+30` | `+30` | Active playing-time / youth development promises |
| **`TSF_MORALE`** | `+15` | `+10` | `+10` | `+5` | Player morale level |
| **`TSF_NEED_MATCH_XP`** | **`+15`** | **`+55`** | **`+75`** | **`+95`** | Development need for competitive minutes |
| **`TSF_UNHAPPINESS`** | `+15` | `+15` | `+15` | `+15` | Playing-time unhappiness pressure |
| **`TSF_USE_INSIDE_FOOTED_WINGER`** | `+10` | `+10` | `+10` | `+10` | Inverted foot preference for inside roles |
| **`TSF_INTEGRATION`** | `+5` | `+5` | `0` | `0` | New signing squad integration |
| **`TSF_YOUNG_PLAYERS`** | **`+5`** | **`+15`** | **`+25`** | **`+50`** | Direct youth player selection bonus |
| **`TSF_VIRTUAL`** | `-50` | `-50` | `-50` | `-50` | Penalty against greyed-out virtual players |
| **`TSF_UPCOMING_SUSPENSION`** | **`-90`** | **`-100`** | **`-130`** | **`-150`** | Penalty when 1 yellow card away from a ban |
| **`TSF_REST_PROMISES`** | **`-190`** | **`-210`** | **`-230`** | **`-250`** | Penalty when promised a rest |
| **`TSF_ALLOWED_MINS`** | **`-250`** | **`-250`** | **`-250`** | **`-250`** | Medical Centre / physio playing-time restriction |

> **Key Takeaway:** Why do AI managers sometimes keep playing an out-of-form veteran over a high-PA wonderkid in league matches? Because in `TPS_FIRST_TEAM_PICKING`, `TSF_CA (+120) + TSF_REPUTATION (+35) + TSF_STAR_PLAYER (+35) + TSF_CAPTAINCY (+40) = +230` outweighs `TSF_PA (+90) + TSF_YOUNG_PLAYERS (+5) + TSF_NEED_MATCH_XP (+15) = +110`. In cup/reserve fixtures (`TPS_TOTAL_RESERVE_PICKING`), the polarity flips: `TSF_PA (+120) + TSF_NEED_MATCH_XP (+95) + TSF_YOUNG_PLAYERS (+50) = +265`!

---

## 3. Match Rating Calculation Engine (`player_ratings_data.jsb`)

In `shared/data/simatch.fmf` (`Frame #118`: `player_ratings_data.jsb`, `348,584` bytes), FM26 stores 6 historical versions of the match rating formula, culminating in active version **`v26.4.10.1`**.

### 3.1 Base Value (`6.70`) & The 90-Minute Decay (`90min Adjuster`)
1. Every player steps onto the pitch with **`start_value = 6700`** (**`6.70`** on the `1.00..10.00` scale, where `1000` points = `1.00` rating point).
2. As minutes elapse, the engine applies a continuous linear decay called **`90min Adjuster`** (ranging from **`-440` (`-0.44`)** for central defenders/midfielders up to **`-940` (`-0.94`)** for certain attacking/wide profiles, and **`-720` (`-0.72`)** for goalkeepers).
   - **Why does a striker who touches the ball 5 times and does nothing finish with a `6.1` rating?** Because starting from `6.70`, playing 90 minutes with zero positive actions subtracts `~0.60..0.70` via the `90min Adjuster`!
   - **How do normal players stay around `6.70–7.00` without scoring?** By accumulating routine positive actions: each completed pass adds `+5` to `+7` (`100` passes = `+0.50..+0.70`), each tackle won adds `+40..+56` (`+0.04..+0.056`), and each interception adds `+25..+70` (`+0.025..+0.07`).

### 3.2 Complete 52-Action Delta Table Across Positional Profiles (`v26.4.10.1`)
Below are the exact point deltas (`100` = `0.10` match rating) across representative role profiles in `player_ratings_data.jsb`:

| Match Event / Statistic (`coefficients`) | Profile `#00` *(Goalkeeper)* | Profile `#01` *(Defender)* | Profile `#05` *(Full-Back / WB)* | Profile `#10` *(Midfielder / Playmaker)* | Profile `#15` *(Winger / Forward)* | Rating Impact (`÷ 1000`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`start_value` (Starting Rating)** | `6700` | `6700` | `6700` | `6700` | `6700` | **`6.70` Base** |
| **`90min Adjuster` (Per 90 Mins Played)** | `-720` | `-520` | `-440` | `-600` | `-700` | `-0.44` to `-0.72` |
| **`Goals`** | `+600` | `+500` | `+500` | `+550` | `+500` | **`+0.50` to `+0.60`** |
| **`Good Goal Adder` / `Great Goal Adder`** | `+100 / +200` | `+100 / +200` | `+100 / +200` | `+100 / +200` | `+100 / +200` | `+0.10` / `+0.20` |
| **`Decisive Goal` / `Decisive Late Goal`** | `+350 / +400` | `+350 / +400` | `+350 / +400` | `+350 / +400` | `+350 / +400` | **`+0.35` / `+0.40`** |
| **`Cumulative Goal Bonus` (2nd+ Goal)** | `+300` | `+300` | `+300` | `+300` | `+300` | `+0.30` |
| **`Goals minus xG × 100 (only if negative)`** | `+4` | `+4` | `+4` | `+4` | `+4` | Underperforming xG penalty (`-0.04` per `0.10` xG missed) |
| **`Assists` / `Cumulative Assist Bonus`** | `+300 / +200` | `+300 / +200` | `+300 / +200` | `+350 / +200` | `+350 / +200` | **`+0.30..+0.35` / `+0.20`** |
| **`Key Passes` / `Open Play xA (×100)`** | `+30 / +7` | `+30 / +7` | `+30 / +7` | `+30 / +7` | `+30 / +7` | `+0.03` per KP |
| **`Passes Completed` / `Passes Incomplete`** | `+7 / 0` | `+5 / -15` | `+7 / -21` | `+7 / -14` | `+7 / -21` | `+0.005..+0.007` / `-0.014..-0.021` |
| **`Crosses Completed` / `Crosses Incompleted`** | `+40 / -8` | `+40 / -8` | `+40 / -8` | `+40 / -8` | `+40 / -8` | `+0.04` / `-0.008` |
| **`Shots` / `Shots On Target`** | `+30 / +20` | `+30 / +20` | `+30 / +20` | `+30 / +20` | `+30 / +20` | `+0.03` / `+0.02` |
| **`Dribbles` / `Times Was Fouled`** | `+20 / +30` | `+20 / +30` | `+20 / +30` | `+20 / +30` | `+20 / +30` | `+0.02` / `+0.03` |
| **`Tackles Won` / `Tackles Lost`** | `+40 / -20` | `+56 / -20` | `+40 / -20` | `+40 / -20` | `+40 / -20` | `+0.04..+0.056` / `-0.02` |
| **`Interceptions` / `Blocks` / `Clearances`** | `+50 / +50 / 0` | `+70 / +50 / +30` | `+50 / +50 / +10` | `+25 / +50 / +10` | `+25 / +50 / +10` | `+0.025..+0.07` |
| **`Aerial Duels Won` / `Aerial Duels Lost`** | `+20 / -20` | `+20 / -20` | `+20 / -20` | `+20 / -20` | `+20 / -20` | `+0.02` / `-0.02` |
| **`Fouls Committed`** | `-40` | `-40` | `-40` | `-40` | `-40` | `-0.04` |
| **`Mistakes Leading to Goals` / `Own Goal`** | `-300 / -300` | `-300 / -300` | `-300 / -300` | `-300 / -300` | `-300 / -300` | **`-0.30`** |
| **`Clean Sheet`** | **`+500`** | **`+300`** | `+75` | `+25` | `+75` | **`+0.50` GK / `+0.30` DEF** |
| **`Saves` / `Good Save` / `Great Save`** | `+100/+200/+400` | `0` | `0` | `0` | `0` | `+0.10` / `+0.30` / `+0.50` total |
| **`Penalties Scored` / `Penalties Missed`** | `+350 / -200` | `+350 / -200` | `+350 / -200` | `+350 / -200` | `+350 / -200` | `+0.35` / `-0.20` |
| **`Penalties Saved Adder`** | **`+450`** | `0` | `0` | `0` | `0` | **`+0.45`** (plus save bonus) |
| **`Keeper less than 5 shot boost`** | `+125` | `0` | `0` | `0` | `0` | `+0.125` quiet-game GK floor |
| **`Yellow Card` / `2nd Yellow` / `Red Card`** | `-50/-100/-300` | `-50/-100/-300` | `-50/-100/-300` | `-50/-100/-300` | `-50/-100/-300` | `-0.05` / `-0.10` / `-0.30` |
| **`Team Goals For` / `Team Goals Conceded`** | `+50 / -100` | `+50 / -100` | `+50 / -100` | `+50 / -100` | `+50 / -100` | `+0.05` per GF / `-0.10` per GA |

### 3.3 Team Expectation Multiplier (`expected_score_data`)
When a team significantly outperforms pre-match odds (`Exceed Significant with Win` or `Exceed Significant with Draw`), positive rating deltas (`rating - 6700 > 0`) are multiplied by **`1200 / 1000 = 1.20×`** (`1.10×` for `Exceed with Win/Draw`).

---

## 4. Weekly Training Engine (`training.fmf`)

In `data/game_simulation/training.fmf`, FM26 stores the complete mathematical model for weekly training across **4 `.jsb` tables**:
- `Frame #001` (`training_item_effects.jsb`): `62` individual/team training items with exact `condition`, `fatigue`, `injuries`, `sharpness`, `happiness`, and `tacticalfamiliarity` deltas.
- `Frame #002` (`training_schedule_templates.jsb`): `164` Full-Time weekly schedule templates (`day1..day7 × session1, session2, extra`).
- `Frame #003` (`training_schedule_templates_fmc.jsb`): `136` Part-Time / Youth schedule templates.
- `Frame #004` (`training_sessions_weights.jsb`): **All `44` Weekly Training Sessions** with their `primary` (`60%` or `100%`), `secondary` (`20%` or `40%`), and `tertiary` (`20%`) attribute targets and `tactical_familiarity` categories.

### 4.1 Complete Table of All 44 Weekly Training Sessions (`training_sessions_weights.jsb`)

| Category | Session Name | Max/Wk | Primary Weight & Attributes Targeted | Secondary (`20–40%`) / Tertiary (`20%`) | Tactical Familiarity |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **General** | **Team Overall** | `7` | **`100%`:** All 38 technical, mental, physical & GK attributes | — | All 8 Tactical Areas |
| **General** | **Team Outfield** | `7` | **`60%`:** 21 Outfield Technical & Mental attributes | **`40%`:** GK Unit Roles | All 8 Tactical Areas |
| **General** | **Team Attacking** | `7` | **`60%`:** `Cro, Dri, Fin, Fir, Hea, Lon, Pas, Tec, Cmp, Fla, OtB, Vis` | **`20%`:** Defending (`Hea, Mar, Tck...`) / **`20%`:** GK | `Creative Freedom` |
| **General** | **Team Possession** | `7` | **`60%`:** `Dri, Fir, Pas, Tec, Ant, Cmp, Dec, OtB, Tea, Vis` | **`20%`:** Defending / **`20%`:** `Pas, Cmp, Cnt, Dec, Vis, Fir` | `Passing Style`, `Tempo` |
| **General** | **Team Defending** | `7` | **`60%`:** `Hea, Mar, Tck, Tec, Agg, Ant, Cnt, Dec, Pos, Tea, Wor` | **`20%`:** Attacking / **`20%`:** GK | `Trigger Press`, `Marking` |
| **General** | **Team Tactical** | `7` | **`100%`:** `Ant, Cmp, Cnt, Dec, OtB, Pos, Tea, Vis` | — | `Role/Duty`, `Mentality`, `Width` |
| **General** | **Team Physical** | `7` | **`100%`:** `Acc, Agi, Bal, Jum, Nat, Pac, Sta, Str, Wor, Aer` | — | — |
| **General** | **Team Goalkeeping** | `7` | **`60%`:** `Aer, Agi, Ant, Cmd, Com, Cnt, Dec, Han, Kic, 1v1, Pos, Ref` | **`20%`:** Offensive Roles / **`20%`:** Defensive Roles | — |
| **Physical** | **Physical Endurance** | `7` | **`100%`:** `Stamina`, `Natural Fitness`, `Work Rate` | — | — |
| **Physical** | **Physical Resistance** | `7` | **`100%`:** `Balance`, `Jumping Reach`, `Strength`, `Work Rate`, `Aerial Reach` | — | — |
| **Physical** | **Physical Quickness** | `7` | **`100%`:** `Acceleration`, `Agility`, `Pace` | — | — |
| **Physical** | **Physical Recovery** | `7` | **`100%`:** Reduces `Injury Proneness` risk, restores `Condition` & reduces `Jadedness` | — | — |
| **Match Prep** | **Match Tactics** | `3` | **`100%`:** `Decisions`, `Teamwork` | — | All 8 Tactical Areas |
| **Match Prep** | **Match Practice** | `2` | **`100%`:** `Offensive, Defensive & Goalkeeping Unit Roles` | — | All 8 Tactical Areas |
| **Match Prep** | **Match Review Analysis** | `3` | — *(Pure tactical familiarity recovery)* | — | All 8 Tactical Areas |
| **Attacking** | **Unit Attacking Wings** | `7` | **`60%`:** `Ant, Cro, Dri, Fin, Hea, OtB, Tec` | **`20%`:** `Hea, Mar, Ant, Dec, Pos` / **`20%`:** GK | `Passing Style`, `Creative Freedom` |
| **Attacking** | **Unit Attacking Patient** | `7` | **`60%`:** `Fin, Fir, Pas, Tec, Cmp, Dec, Fla, OtB, Vis, Tea` | **`20%`:** `Mar, Tck, Agg, Ant, Dec, Pos` / **`20%`:** GK | `Passing Style`, `Creative Freedom` |
| **Attacking** | **Unit Attacking Direct** | `7` | **`60%`:** `Dri, Fin, Fir, Lon, Pas, Tec, Ant, OtB, Vis` | **`20%`:** `Mar, Tck, Ant, Cnt, Pos, Tea` / **`20%`:** GK | `Passing Style`, `Creative Freedom` |
| **Attacking** | **Unit Attacking Overlap** | `7` | **`60%`:** `Cro, Dri, Fin, Lon, Ant, OtB` | **`20%`:** `Hea, Mar, Tck, Cnt, Pos` / **`20%`:** GK Roles | `Passing Style`, `Creative Freedom` |
| **Defending** | **Unit Defending Engaged** | `7` | **`60%`:** `Mar, Tck, Agg, Ant, Dec, Pos` | **`20%`:** Patient Attacking / **`20%`:** GK | `Trigger Press`, `Marking` |
| **Defending** | **Unit Defending Unengaged** | `7` | **`60%`:** `Mar, Tck, Ant, Cnt, Pos, Tea` | **`20%`:** Direct Attacking / **`20%`:** GK | `Trigger Press`, `Marking` |
| **Defending** | **Unit Defending Wide** | `7` | **`60%`:** `Hea, Mar, Ant, Dec, Pos` | **`20%`:** Wings Attacking / **`20%`:** GK | `Trigger Press`, `Marking` |
| **Defending** | **Unit Defending From the Front** | `7` | **`60%`:** `Hea, Mar, Tck, Cnt, Pos` | **`20%`:** `Cro, Dri, Fin, Lon, Ant, OtB` / **`20%`:** GK Roles | `Trigger Press`, `Marking` |
| **Tactical** | **Attacking Shadow Play** | `7` | **`60%`:** `Ant, Cmp, Dec, OtB, Tea` | **`20%`:** `Ant, Cnt, Dec, Pos, Tea` / **`20%`:** GK Mental | `Role/Duty`, `Mentality`, `Width` |
| **Tactical** | **Defensive Shadow Play** | `7` | **`60%`:** `Ant, Cnt, Dec, Pos, Tea` | **`20%`:** `Ant, Cmp, Dec, OtB, Tea` / **`20%`:** GK Mental | `Role/Duty`, `Mentality`, `Width` |
| **Technical** | **Chance Conversion** | `7` | **`60%`:** `Finishing, Heading, Long Shots, Technique, Anticipation, Composure` | **`20%`:** Def Roles / **`20%`:** GK Roles | — |
| **Technical** | **Chance Creation** | `7` | **`60%`:** `Crossing, Passing, Technique, Decisions, Flair, Off The Ball, Vision` | **`20%`:** Def Roles / **`20%`:** GK Roles | — |
| **Technical** | **Ball Retention** | `7` | **`60%`:** `First Touch, Anticipation, Composure, Decisions, Teamwork` | **`20%`:** Defending / **`20%`:** GK Roles | — |
| **Technical** | **Ball Distribution** | `7` | **`60%`:** `Dribbling, Passing, Decisions, Vision, Teamwork` | **`20%`:** Defending / **`20%`:** GK Distribution | — |
| **Technical** | **Transition - Press** | `7` | **`40%` (Att) + `40%` (Def):** `Fir, Pas, Tck, Ant, Agg, Dec, Tea, Wor` | **`20%`:** GK Roles | — |
| **Technical** | **Transition - Restrict** | `7` | **`40%` (Att) + `40%` (Def):** `Pas, Tck, Ant, Cnt, Mar, Pos, Tea` | **`20%`:** GK Roles | — |
| **Technical** | **Ground Defence** | `7` | **`60%`:** `Marking, Tackling, Technique, Concentration, Positioning` | **`20%`:** Off Roles / **`20%`:** GK Roles | — |
| **Technical** | **Aerial Defence** | `7` | **`60%`:** `Heading, Marking, Technique, Concentration, Positioning` | **`20%`:** Off Roles / **`20%`:** GK Roles | — |
| **Technical** | **Play From the Back** | `7` | **`60%` (Def) + `20%` (Off):** `Dri, Fir, Pas, Cmp, Fla, Vis, Tea` | **`20%`:** `Fir, Kic, Pas, Thr, Vis` | — |
| **Goalkeeping** | **Shot Stopping / Handling / 1v1 / Distribution** | `7` | **`60%`:** GK Core (`1v1, Ref, Ant, Pos, Agi` / `Han, Aer, Cnt, Bal` / `1v1, Rus, Ant, Dec, Acc` / `Fir, Kic, Pas, Thr, Cmp, Vis`) | **`20%`:** Off Roles / **`20%`:** Def Roles | — |
| **Set Pieces** | **Set Pieces Routines / Penalty Taking** | `7` | **`60%`:** `Set Piece Takers, Fre, Cor, LTh, Tec` / `Pen, Cmp` | **`20%`:** `Hea, Mar, Ant, Cnt, OtB, Pos` / **`20%`:** GK | — |
| **Extra** | **Team Bonding / Community Outreach** | `1` | **`100%`:** `Teamwork` (`Team Bonding` also gives **`+3 Happiness`** and **`+1 Fatigue recovery`**) | — | — |

### 4.2 Special Session Condition, Fatigue, Injury & Happiness Modifiers (`training_item_effects.jsb`)

| Special Session Item | Condition Effect | Fatigue Recovery | Injury Prevention | Match Sharpness | Player Happiness | Tactical Familiarity |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`Team Rest`** | **`+2`** *(Restores)* | **`+3`** *(Best recovery)* | `0` | `-3` *(Drops)* | `+1` | `0` |
| **`Team Recovery`** | **`+1`** *(Restores)* | **`+2`** *(Recovers)* | **`+3`** *(Prevents injuries)* | `-1` | `+1` | `0` |
| **`Match Prep Match Practice`** | `-3` *(Drains)* | `-1` *(Tires)* | `-3` *(Higher risk)* | **`+2`** *(Sharpens)* | **`+3`** *(Players love it)* | **`+2`** |
| **`Extra Curricular Team Bonding`** | `0` | `+1` | `0` | `0` | **`+3`** *(Boosts morale)* | `0` |
| **`Team Travel`** | `0` | `-1` | `0` | `-1` | `-1` | `0` |

---

## 5. Player Progression, CA Growth, Coaching Star Formula & Aging Mechanics

### 5.1 How a Player Converts `PA` into `CA`
A player's monthly progression roll is governed by five interacting factors:
1. **Remaining Potential Gap (`PA - CA`) & Age Bracket:**
   - **Ages `15–18`:** Driven primarily by **Training Quality** (`Training Facilities 1..20`, `Youth Facilities 1..20`, and Coaching Star Ratings) plus U18/Reserve match sharpness.
   - **Ages `18–23`:** Requires **Competitive First-Team Minutes** (`TSF_NEED_MATCH_XP`) against opponents with sufficient **League/Match Reputation**, combined with high **Match Ratings (`>= 7.00`)**.
   - **Ages `24+`:** Physical growth plateaus; technical and mental attributes (`Anticipation`, `Decisions`, `Positioning`, `Composure`, `Leadership`) continue to progress up to the player's peak.
2. **Hidden Personality Vector (`block_40` / Pre-Game `people_db.dat` 8 Hidden Bytes):**
   - **`Professionalism` (`1..20`):** The #1 multiplier on training attendance, work ethic, and post-30 physical preservation.
   - **`Ambition` (`1..20`):** Drives rapid CA growth when playing at a high-reputation club or seeking a step up.
   - **`Determination` (`1..20`):**Visible `1..20` attribute acting as a secondary multiplier on both training progression and in-match comeback resilience.
3. **CA Attribute Weight Redistribution ([`formulas.py`](../fm26save/formulas.py)):**
   - Every attribute costs a specific number of `CA` points per positional weight (e.g., `Acceleration`, `Pace`, `Decisions`, and primary positional skills have the highest `CA` weight; `Flair`, `Long Throws`, `Aggression`, and `Natural Fitness` cost `0` `CA` points).
   - Training a new position decreases the available per-attribute `CA` budget slightly because versatility increases the player's positional `CA` multiplier, whereas unfocused training (`Team Overall`) spreads `CA` gains thinly across all 38 attributes.

### 5.2 Coaching Star Rating Formula (`staff.py` & `enrichment.py`)
In [`enrichment.py`](../fm26save/enrichment.py) and `game_db.dat`, every coach has visible coaching attributes plus hidden `block_40` attributes (`1..100` scale, divide by `5` for `1..20`). Across all coaching categories, the **"DDB" core** (`Discipline + Determination + Motivating`) acts as the universal multiplier on the primary category attribute(s):
- **Fitness (Quickness / Strength):** `9 * Fitness + 2 * (Discipline + Determination + Motivating)` (Max = `300`, every `30` pts = `0.5★`, `>= 270` = `5.0★`).
- **Goalkeeping (Shot Stopping / Handling / Distribution):** `6 * GK_Primary + 2 * (Discipline + Determination + Motivating)`.
- **Tactical / Ball Control / Defending / Attacking / Possession:** Weighted sum of `6 * Primary_Category + 3 * Secondary_Category + 2 * (Discipline + Determination + Motivating)`.

---

## 6. Match Engine: Expected Goals (`xG`), Spatial Momentum & Quick Match Engine (`QME`)

### 6.1 Expected Goals (`xG`) Logistic Regression (`simatch.fmf` Frames `#090..#100`, `v26.1.4.1`)
Every shot in the 3D/2D match engine is classified into one of **11 mutually exclusive shot types** and scored via a fixed-point (`10^7`) logistic regression model:
$$z = b_0 + \sum_{i=1}^{k} b_i x_i, \qquad \text{xG} = \sigma(z) = \frac{1}{1 + e^{-z}}$$

| Shot Category (`.jsb`) | Scaled Intercept ($b_0 = \text{raw} / 10^7$) | Base Conversion $\sigma(b_0)$ | Key Spatial & Contextual Features ($x_i$) |
| :--- | :---: | :---: | :--- |
| **`penalties`** | **`+1.1984673`** | **`76.825%`** | Constant (`0` spatial features — every penalty has **`0.7683 xG`**) |
| **`open_goal_volleys`** | `-1.0279187` | `26.349%` | Distance, angle, ball height, horizontal speed, defender proximity |
| **`open_goal_regular`** | `-1.0867306` | `25.224%` | Distance, angle, ball speed, pressure, weaker foot |
| **`obscured_volleys`** | `-1.1122386` | `24.745%` | Distance, angle, congestion blocker count, volley height |
| **`volleys`** | `-1.1265032` | `24.481%` | Distance, angle, ball height, pressure, body orientation |
| **`regular` (Open Play Foot)** | `-1.2095895` | `22.977%` | Distance, angle to goal mouth, GK position, defender pressure |
| **`obscured_regular`** | `-1.4375833` | `19.192%` | Distance, angle, defenders in shot cone |
| **`open_goal_headers`** | `-1.5907703` | `16.928%` | Distance, angle, cross speed, jump contest |
| **`headers`** | `-2.8524565` | `5.455%` | Distance, angle, aerial pressure, GK distance |
| **`obscured_headers`** | `-3.2111593` | `3.875%` | Distance, angle, crowded box blockers |
| **`free_kicks` (Direct FK)** | `-0.4340446` | `39.316%` *(before distance decay)* | Distance (`m`), wall angle, central/wide offset |

### 6.2 Spatial Match Momentum Engine (`simatch.fmf` Frame `#113`: `momentum_weightings_data.jsb`)
Match momentum is tracked on a continuous scale using **`48` Event × Pitch Zone rules** across `4` pitch zones (`OWN_AREA`, `DEFENSIVE_HALF`, `ATTACKING_HALF`, `OPPOSITION_AREA`):
- **Highest Positive Momentum Events:** `GOAL (+50)`, `SHOT_WOODWORK (+20)`, `PENALTY_SAVED (+20)`, `RED_CARD_OPPONENT (+20)`, `SHOT_ON_TARGET (+10)`, `CORNER_WON (+6)`, `KEY_PASS_IN_OPPOSITION_AREA (+6)`, `TACKLE_WON_IN_ATTACKING_HALF (+5)`.
- **Highest Negative Momentum Events:** `GOAL_CONCEDED (-50)`, `RED_CARD (-20)`, `PENALTY_MISSED (-20)`, `MISTAKE_IN_OWN_AREA (-10)`, `DISPOSSESSED_IN_OWN_HALF (-6)`.

### 6.3 Quick Match Engine (`QME` — Background Unrendered Matches, `simatch.fmf` Frames `#119–#120`)
When simulating matches in other leagues or when using **"Instant Result"**, FM26 uses the **Quick Match Engine (`QME`)**:
- `qme_stat_relevant_attribute_data.jsb` (`Frame #120`) maps **22 match stat categories** directly to relevant player attributes (`1..20`), e.g.:
  - `GOALS` $\leftarrow$ `Finishing, Composure, Off The Ball, Technique, Heading`
  - `ASSISTS` / `CHANCES_CREATED` $\leftarrow$ `Passing, Vision, Crossing, Technique, Decisions, Flair`
  - `TACKLES` $\leftarrow$ `Tackling, Anticipation, Aggression, Decisions, Positioning, Pace`
  - `INTERCEPTIONS` $\leftarrow$ `Anticipation, Positioning, Decisions, Concentration, Acceleration`
  - `AERIAL_DUELS` $\leftarrow$ `Jumping Reach, Heading, Strength, Bravery, Aggression`
- `qme_distribution_data.jsb` (`Frame #119`, `585,551` bytes) then samples exact match counts from **3,137 Normal, Binned, and Zero-Inflated probability distributions** calibrated by role, mentality, and team CA differential.

---

## 7. Dual-Formation Engine: Out-Of-Possession (`OOP`) 24-Zone Grid & 10 Tactical Styles

FM26 introduced a native **Dual-Formation Engine** separating **In-Possession (`50` roles / `93` Role×Duty combinations)** from **Out-Of-Possession (`39` `OP*` roles)**:
1. **`oop_attributes_scoring.jsb` (`simatch.fmf` Frame `#114`):** Evaluates how well a player fits each of the `39` Out-Of-Possession roles (`OPGK` through `OPCF_P` Pressing Center Forward and `OPCF_T` Tracking Center Forward) using bitmask-indexed attribute lists.
2. **`oop_pitch_proximity_scores.jsb` (`simatch.fmf` Frame `#115`, `95,708` bytes):** Divides the pitch into an **`8 × 3 = 24` spatial zone grid** (`8` longitudinal slices from own goal line to opponent goal line × `3` lateral channels: Left, Center, Right). For all `118` `(Position, Role)` combinations, it defines the exact target `(x, y)` shift across all `24` ball zones (`2,832` spatial rules).
3. **`tactical_styles.xml` (`simatch.fmf` Frame `#192`):** Defines the `10` official tactical styles (`Control Possession`, `Tiki-Taka`, `Vertical Tiki-Taka`, `Wing Play`, `Route One`, `Fluid Counter-Attack`, `Direct Counter-Attack`, `Gegenpress`, `Catenaccio`, `Park the Bus`) along with their highlighted core player attributes and `101` binary `.tac` dual-formation presets (`Frames #121..#222`).

---

## 8. Medical Centre & Injury Simulation Engine (`server_db.dat`)

In `shared/data/database/db/2620/2620_fm/server_db.dat` (`Frame #08`, `6,550` bytes), FM26 defines the exact **48-byte binary simulation struct for all `136` injuries** (cross-referenced with `lang_update_db.dat` `Frame #08` `8_12.dat`):

| Offset in 48B Struct | Type | Field | Simulation Role |
| :---: | :---: | :--- | :--- |
| `+1` | `u8` | `category_code` | Injury medical category (muscular, ligament, bone fracture, viral/illness, impact) |
| `+2` | `u8` | `body_part_code` | Affected anatomical part (hamstring, knee, ankle, groin, calf, back, head, etc.) |
| `+3` | `u8` | `is_physical_injury` | `1` = physical trauma/strain, `0` = illness/systemic |
| `+4..+6` | `u16` | `min_days` | Minimum base recovery duration in days |
| `+6..+8` | `u16` | `extra_days` | Random additional recovery window (`actual_days = min_days + rand(0, extra_days)`, scaled by Medical Staff & age) |
| `+8..+12` | `2×u16` | `inactivity_min / extra` | Days completely unable to train before protective/light rehabilitation |
| `+12..+14` | `u16` | `match_sharpness_drop_pct` | Percentage drop in Match Sharpness (`10..100%`) |
| `+14` | `u8` | `treatment_type_code` | Allows/forbids painkilling injections vs. specialist vs. club physio |
| `+15` | `u8` | `is_recurring` | If `1`, permanently increases recurrence risk on that `body_part_code` |
| `+16` | `u8` | `is_contagious` | If `1` (e.g., *Flu, Virus, Food Poisoning, Chest Infection*), triggers the `"Send Home"` vs. `"Treat at Club"` contagion check |
| `+18..+26` | `2×f32` | `occurrence_ratio / base_occurrence` | Relative probability weight when an injury event is rolled in match or training |
| `+30` | `u8` | `severity_tier` | Severity tier (`1..6`, where `6` can reduce `Natural Fitness`, `Acceleration`, `Pace`, and `CA` ceiling) |

---

## 9. Sugar Daddy Tycoons, Board Takeovers, International Treaties & Transfer Valuation Logic

### 9.1 Permanent Club Ownership & Takeover Rules (`.edt` Files)
In `shared/data/database/db/2620/edt/permanent/`:
1. **`sugardaddy.edt` (`14` Clubs):** Defines four distinct owner cash-injection behaviors:
   - **`FRONT_END`** *(e.g., PSG, Man City, Newcastle, Como, Al-Hilal, Al-Nassr, Al-Ittihad, Al-Ahli)*: Proactively pumps massive transfer/wage budgets every summer and increases commercial sponsorship deals.
   - **`BACK_END`** *(e.g., Chelsea, Aston Villa, Brighton, Hoffenheim)*: Intervenes primarily at the end of the financial year to clear operating debt and maintain high budgets without artificial sponsorship inflation.
   - **`UNDERWRITER`**: Silently clears end-of-season debt so the club never enters administration, without inflating transfer budgets.
   - **`UNDERWRITER_NO_INCREASE`**: Covers losses once until ownership status decays.
2. **`valid_takeovers_only.edt` (`69` Rules):** Restricts board takeovers by nation/club (e.g., `NO_RICH_INDIVIDUAL_TAKEOVER` enforcing Germany's `50+1` fan-ownership rule, or `PARTIAL_MEMBER_ELECTION` for socio-owned clubs like Real Madrid, Barcelona, Benfica, and Athletic Bilbao).
3. **`transfer_embargo.edt` (`35` Clubs):** Pre-configured FIFA/federation transfer bans with exact start and end dates.

### 9.2 International Treaties & Work Permit Exemptions (`client_db.dat` Frame `#00`)
`client_db.dat` `Frame #00` (`table_0.dat`) defines the **6 international free-movement / foreign-player exemption agreements**:
1. **European Union (`EU`)**
2. **European Economic Area (`EEA`)**
3. **OACPS (`Cotonou Agreement` — African, Caribbean, and Pacific Group of States):** Grants non-foreign / domestic-quota status to players from `79` ACP countries in leagues that incorporate Cotonou labour rules (such as Spain, France, Italy, and Germany).
4. **Mercosur** & **Andean Community** (South American regional exemptions).
5. **Overseas Territories**.

### 9.3 Empirical Transfer Value & Wage Model (`formulas.py`)
In [`formulas.py`](../fm26save/formulas.py), cross-sectional regression across all active `.fm` save contracts confirms that a player's **Market Value** and **Wage Demand** are log-linear functions of:
$$\ln(\text{Value}) = \beta_0 + \beta_1 \text{CA} + \beta_2 \max(0, \text{PA} - \text{CA}) + \beta_3 \text{Age} + \beta_4 \text{Age}^2 + \beta_5 \text{ClubRep} + \beta_6 \text{ContractYearsLeft}$$
- **Contract Length Multiplier:** Players with `< 12` months remaining lose `35–65%` of their market value (`Bosman` decay), whereas a fresh 5-year contract (`1,825` days) adds a `+25–45%` valuation premium.
- **League & Club Reputation Ceiling:** Two identical `CA=145` players will differ by `4×–8×` in market value if one plays in a `Reputation ~9000` Premier League club (`Economic Factor = 19`) and the other in a `Reputation ~6000` league (`Economic Factor = 10`).

---

## 10. Squad Dynamics, Mentoring Groups & Hidden `PersonBlock` Relationships

### 10.1 Dressing Room Hierarchy & Social Groups (`dynamics_manager.dat`)
1. **Hierarchy Pyramid (`4` Tiers):**
   - **Team Leaders** $\rightarrow$ **Highly Influential** $\rightarrow$ **Influential** $\rightarrow$ **Other Players**.
   - Scored from: **Time at Club (Tenure)** + **Leadership (`1..20`)** + **Age** + **Current Ability (`CA`) & Squad Status (`Star / Important Player`)** + **Captaincy**.
2. **Social Groups:**
   - Clustered automatically by **Shared Spoken Languages** (`client_db.dat` `Frame #13`: `252` Languages), **Nationality / Region**, **Age Bracket**, and **Hidden Personality Compatibility (`block_40`)**.

### 10.2 Mentoring Groups (`mentoring_manager.dat`)
A valid mentoring group requires **at least `3` players** training in the **same squad unit** (First Team):
- **Who Can Mentor Whom:** A mentor must have **higher Hierarchy status** (*Team Leader / Highly Influential*), **Age `>= 24`** (or significantly higher tenure/reputation), and play in the **same training unit** (`Goalkeeping`, `Defensive`, or `Attacking`) as the mentee.
- **What Transfers:** Mentees aged **`<= 23`** gradually shift their hidden `Professionalism`, `Determination`, `Ambition`, `Pressure`, `Temperament`, and `Sportsmanship` toward the group's highest-hierarchy leader, and can also acquire or lose **Player Traits (`PPMs`)**.

### 10.3 Hidden `PersonBlock` Relationships (`enrichment.py` & `constants.py`)
Inside `game_db.dat`, every `PersonBlock` (`18 bytes` per entry) stores bilateral relationship records (`target_person_id`, `rel_major`, `rel_sub`, `intensity 1..100` at byte `+16`):
- `(1, 1)` = **Favoured Personnel (Player / Teammate)**
- `(2, 1)` = **Favoured Personnel (Manager / Coach / Mentor)**
- `(4, 2)` = **Disliked Person / Rivalry**
- `(1, 4)` = **Idol / Club Legend**
- `(5, 3)` = **Family Relation (Brother / Father / Son)** — also generated rarely (~`1%` chance) during **Youth Intake** when a long-serving player or club icon is at the club!
---

## 11. Team Talks, Touchline Shouts, Press Conferences (`media.fmf`) & Morale / Body Language Algorithm

### 11.1 Team Talk & Touchline Shout Delivery Tones (`global-metadata.dat`)
In `global-metadata.dat`, the engine dispatches six distinct delivery tones for Pre-Match (`ShouldShowPreMatchTeamTalks`), Half-Time, Full-Time (`FullTimeTeamTalk`), Substitution (`SubstitutionTeamTalkEnabled`), and Touchline Shouts (`IndividualTouchlineShoutPanel`):
1. **`Aggressive`** (`EventAggressiveTouchlineTeamTalkIssued`)
2. **`Assertive`** (`EventAssertiveTouchlineTeamTalkIssued`)
3. **`Passionate`** (`EventPassionateTouchlineTeamTalkIssued`)
4. **`Calm`** (`EventCalmTouchlineTeamTalkIssued`)
5. **`Cautious`** (`EventCautiousTouchlineTeamTalkIssued`)
6. **`Reluctant`** (`EventReluctantTouchlineTeamTalkIssued`)

### 11.2 How a Player's Body Language (`InteractionBodyLanguage`) & Morale React
When a team talk, shout, or 1-on-1 conversation is issued (`EventFmxTeamTalkProcessTalk`), each listening player rolls a reaction (`Inspired`, `Motivated`, `Focused`, `Composed`, `Listening`, `Complacent`, `Nervous`, `Anxious`, `Frustrated`, `Angry`, `Demoralised`) computed from four inputs:
1. **Manager Authority Score:** `Manager Reputation + Motivating (1..20) + Level of Discipline (1..20) + Man Management / People Management (1..20) + Leadership (1..20)`.
2. **Expectation vs. Scoreline Context (`expected_score_data`):** Praising a team when drawing against a heavy underdog triggers **`Complacent`** in low-Professionalism players and **`Angry / Confused`** in high-Ambition/Determination leaders, whereas `Aggressive / Assertive` criticism when trailing at half-time as heavy favourites triggers **`Fired Up / Motivated`** in high-Determination/Pressure players.
3. **Player Hidden Personality (`block_40`):**
   - Low `Pressure` (`< 8`) + high `Nervousness` players react negatively (`Anxious / Apprehensive`) to `"I expect a win"` or `Aggressive` demands.
   - High `Controversy` + low `Temperament` + low `Professionalism` players push back against fines and criticism.
4. **Manager–Player Relationship (`PersonBlock`):** Being in the player's `Favoured Personnel` (`(2, 1)`, intensity `1..100`) grants a large positive buffer on every interaction roll.

### 11.3 Press Conference & Backroom Advice Reaction Schema (`media.fmf` — 650 XML Frames)
Inside `data/game_simulation/media.fmf` (`3,934` questions `QID_*`, alternative answers `pcaa`, and backroom advice rules `barl`), every answer record encodes explicit delta tags:
- **`tone`** & **`topi`** (Topic) & **`cntx`** (Context) & **`rule` / `rulf`** (Trigger pre-conditions)
- **`pamd`**: **Player / Audience Morale Delta**
- **`papd`**: **Player / Audience Pressure Delta** (shifts pre-match nervousness/complacency)
- **`pafd`**: **Supporter / Fan Confidence Delta**
- **`pafm`**: **Board / Media Confidence Delta**
- **`padm` / `paep`**: **Dressing Room / Journalist Relationship Delta** (`JournalistRelationshipWithHuman`)
- **`dcsl`, `dcsr`, `dcmr`, `dcpr`, `dcpt`, `dcwg`**: **Club / Squad Reaction Modifiers**

### 11.4 Composite Player Happiness (`HappinessCategoryReference`)
A player's overall morale and long-term happiness (`HappinessPlayers`) is aggregated across seven tracked categories:
1. **`PlayingTimeHappinessLevel`**: Actual starts/minutes vs. contract `Squad Status` (`PFms`: *Star Player, Important Player, Regular Starter, Squad Player, Fringe Player*).
2. **`PlayerWaitingOnPromiseForHappiness`**: Active time-bounded promises (`TSF_FOOTBALL_PROMISES`).
3. **Training Happiness**: Affected by schedule workload and `training_item_effects.jsb` (`happiness` deltas).
4. **Contract & Wage Satisfaction**: Current wage vs. squad peers of equal `CA`/`Reputation`.
5. **Club Treatment & Discipline**: Reactions to fines or transfer-list status.
6. **Dressing Room & Social Group Fit**: Hierarchy support and language/nationality integration (`TSF_INTEGRATION`).
7. **`LoanHappiness`**: Playing time and position compliance while out on loan.

---

## 12. Scouting Knowledge (`0..100%`), Dual-Role Recruitment Focuses & Star Rating ("Fog of War") Algorithm

### 12.1 Star Ratings (`FMStarRatingSettings` — `0.5★` to `5.0★`)
Player Star Ratings (`PerceivedAbility` and `PerceivedPotential`) are **contextual relative scores**, not raw `CA`/`PA` numbers:
1. **Baseline Reference (`3.0★`):** Represents the **mean `CA` of your club's current first-team starters in that positional group**, blended with your division's average starter `CA`.
   - A `CA = 135` midfielder is rated **`4.5★`** at a club whose midfield averages `CA = 115`, but **`2.5★`** at Manchester City or Real Madrid where starters average `CA = 165`.
2. **Perceived `CA` vs. True `CA` Modifiers:**
   - Recent **Form (`TSF_LAST_RATINGS`)** and **Player Reputation** temporarily pull `PerceivedAbility` up or down by `0.5★–1.0★`.
3. **White / Silver Stars (Uncertainty Interval on `PerceivedPotential`):**
   - The width of the uncertain potential band (shown as white/grey stars above gold stars) is governed by:
     $$\text{UncertaintyWidth} \propto (20 - \text{Scout}_{\text{JPP}}) \times (1 - \text{ScoutingKnowledge}) \times \max(0, 23 - \text{Age})$$
   - Once a player reaches **Age `22–24`**, developmental variance collapses and white stars disappear.

### 12.2 Attribute Fog-of-War & Scouting Knowledge (`0..100%`)
- When **Attribute Masking** is enabled, un-scouted players (`0%` knowledge) display wide attribute intervals (e.g. `10–17`) or hidden `-` values.
- Each scouting report update increases knowledge (`0% -> 20% -> 40% -> 60% -> 80% -> 100%`) at a speed determined by the scout's **`Adaptability`**, existing **Nation/Region Knowledge**, **`Judging Player Ability (JPA)`**, and **`Judging Player Potential (JPP)`**. At `100%`, all `60` attributes resolve to exact values.

### 12.3 FM26 Dual-Role Recruitment Focus Engine (`EventFmxRecruitmentFocus*`)
In FM26, `RecruitmentFocusHandlerModule` evaluates transfer targets across five simultaneous filters:
1. **`IpRoleProficiency`** (`EventFmxRecruitmentFocusIpRoleProficiencyUpdated` — In-Possession Role Suitability)
2. **`OopRoleProficiency`** (`EventFmxRecruitmentFocusOopRoleProficiencyUpdated` — Out-Of-Possession `OP*` Role Suitability)
3. **`CurrentAbility` & `PotentialAbility`** star thresholds
4. **`StatObjective`** (`EventFmxRecruitmentFocusAddStatObjective` — per-90 statistical filters from match telemetry)
5. **Scouting Area & Age / Transfer Value / Contract Expiry bounds**

---

## 13. Dynamic League Reputation, 5-Year & 10-Year Continental Coefficients & Prize Money Algorithm

In `global-metadata.dat` and `sicomps/comps.dbc`, continental progression and dynamic league standing are governed by three coupled algorithms:
1. **5-Year Rolling Nation & Club Coefficients (`FiveYearTotalCoefficient` / `TimelineAdjustedFiveYearTotalCoefficientAdjustmentRules`):**
   - Tracks `YearCoefficient0 .. YearCoefficient4` across continental club competitions.
   - Directly determines **`FiveYearCoefficientPosition`** and **`SeasonSummaryContinentalQualification`** (how many Champions League / Europa / Conference League or Libertadores/ACL berths a nation receives and at which qualifying round).
2. **10-Year Historical Club Coefficient (`TenYearTotalCoefficient` / `YearCoefficient0 .. YearCoefficient10`):**
   - Tracks a club's 10-year continental points (`TenYearCoefficientPosition`) to allocate the **Value Pillar / Historical Coefficient Share** of continental TV & prize pools (`SquadRewardsPrizeMoney`).
3. **Dynamic `CompetitionReputation` (`1..10000`):**
   - Recalculated annually based on:
     1. The 5-year continental coefficient delta of the nation's clubs.
     2. The average `CA` and `World Reputation` of the top `N` players registered in the division.
     3. Continental trophy winners/finalists from that league.
   - As `CompetitionReputation` rises, domestic TV/sponsorship renewals (`DynamicSponsorshipDebugInfo`), player transfer values, and maximum player willingness to join clubs in that league scale upward automatically.

---

## 14. Contract Negotiations (`contract_offer.xml` — 66 FourCCs), Agent Patience & Transfer Bid Evaluation Algorithm

### 14.1 Complete 66-Property Contract Offer & Clause Schema (`editor.fmf` Frame `#035`)
Every contract offer in FM26 is represented internally by the `CntF` record (`contract_offer.xml`):

| FourCC | Clause / Contract Field | FourCC | Clause / Contract Field |
| :---: | :--- | :---: | :--- |
| **`PFwa`** | Weekly / Annual Base Wage | **`PFms`** | Promised Squad Status (*Star..Fringe*) |
| **`PFdt` / `PFed`** | Date Signed / Contract Expiry Date | **`PFrc`** | On Rolling Contract (`bool`) |
| **`PFap` / `PFgb`** | Appearance Fee / Goal Bonus | **`PFab` / `PFcb`** | Assist Bonus / Clean Sheet Bonus |
| **`PFTY` / `PFTG`** | Division Team of the Year / Top Scorer Bonus | **`PFib`** | International Cap Bonus |
| **`PLiC` (`PLIc`/`PLim`)** | Wage After Reaching `N` Club League Games | **`PWiC` (`PWic`/`PWim`)** | Wage After Reaching `N` International Caps |
| **`PWgB` (`PWgC`/`PWgG`)** | Seasonal Landmark Goal Bonus | **`PYgB` (`PYgC`/`PYgA`)** | Seasonal Landmark Assist Bonus |
| **`PZgB` (`PZgC`/`PZgG`)** | Seasonal Landmark Combined `Goals + Assists` Bonus | **`PFwi` / `PFpi` / `PFrd`** | Yearly Wage Rise % / Promotion Rise % / Relegation Drop % |
| **`PFxP` / `PFCX`** | Extension After Promotion / Optional Club Extension | **`PFLG` / `PF1P` / `PF1A`** | 1-Year Extension After `N` Final-Season League Apps |
| **`PFfr` (`PFfe`)** | Minimum Fee Release Clause (& Expiry Date) | **`PFfF` (`PFfd`)** | Release Clause (Foreign Clubs) |
| **`PFfD` (`PFDd`)** | Release Clause (Domestic Clubs) | **`PFfH` (`PFHd`)** | Release Clause (Domestic Clubs in Higher Division) |
| **`PFfC` (`PFCd`)** | Release Clause (Clubs in a Continental Comp) | **`PFrf` / `PFpr`** | Relegation / Non-Promotion Release Clause |
| **`PSOF` / `PSPP`** | Sell-On Fee % / Sell-On Fee Profit % | **`PFmh` / `PFir`** | **Match Highest Earner Clause** / **Injury Release Clause** |
| **`CPCL`** | % of Club Compensation Required for Managerial Role | **`FTbl` (`cbcp`/`cbch`)** | Competition Stage / Trophy Cash Bonuses |

### 14.2 How Players & Agents Evaluate an Offer (`agent_manager.dat` & `contract_man.dat`)
1. **Package Equivalence Score:**
   - The player/agent converts the offer into an **Expected Annual Package Value** combining `Base Wage (PFwa)` + `Expected Appearances * PFap` + `Loyalty Bonus / Contract Years` + `Landmark Bonuses` + `Release Clause Flexibility Penalty` (if locking in a high release clause).
   - Meanwhile, the club's board checks `HasFFPContributionContractNegotiationRemaining` to verify the offer does not breach FFP wage-cap rules.
2. **Agent Hidden Personality (`agent_manager.dat`):**
   - Each agent (`person_type = 5`) has three core behavioral parameters:
     - **Fee Demand (`1..20`):** How aggressively the agent demands a large upfront `agent_fee` (`money_b`).
     - **Patience (`1..20`):** How many counter-offer rounds are tolerated before negotiations collapse (`amber -> red`).
     - **Willingness to Tout Clients (`1..20`):** How frequently the agent offers the player to rival clubs (`AgentsOfferingServicesCount`) or demands a new contract after a run of good form.

---

## 15. Financial Fair Play (`FFP`), Crowd Attendance (`CrowdAttendanceScalar`), Ticket Prices & Dynamic Sponsorships

### 15.1 Financial Fair Play (`FFPDetailsReference`) & Administration Algorithm
In `global-metadata.dat`, the financial compliance engine tracks:
- **`FinanceDebugFFPRunningTotal` & `FinanceDebugPreviousSeasonFFPAmounts`:** Rolling multi-season profit/loss ledger (`ProfitLossTaxes` minus exempt academy/infrastructure spending and allowable owner equity `FinanceDebugFFPEquityInvestmentDB`).
- **`FinanceDebugFFPWagesTotal` & `FinanceDebugFFPWagesExcludingForeignPlayersTotal`:** Wage-to-turnover ratio and division salary caps.
- **Breach Consequences:**
  - Failing continental checks (`ContinentalFFPFail`) triggers European competition exclusion or squad-registration reductions.
  - Failing domestic checks or entering insolvency (`Administration`) triggers **`TeamPointsDeduction`** (typically `-9` to `-12` league points) and **`FinanceDebugEmbargo`** (transfer embargo).

### 15.2 Crowd Attendance Algorithm (`CrowdAttendanceScalar`)
For every home fixture, announced attendance (`AnnouncedAttendance`, capped at `UsedCapacity` in `server_db.dat` `Frame #22`) is computed from:
$$	ext{Attendance} = \min\!\Big(	ext{UsedCapacity},\; 	ext{SeasonTicketHolders} + 	ext{WalkUpPool} 	imes 	ext{CrowdAttendanceScalar}\Big)$$
where `CrowdAttendanceScalar` combines:
1. **Base Demand:** `ExpectedAttendance` (`offset +45` in `finances.py`) and `SeasonTicketWaitingList`.
2. **Fixture Attractiveness:** `Opposition Reputation`, `Derby / Rivalry Flag` (`1,683` Derbies in `client_db.dat` `Frame #10`), `Competition Importance`, and recent `DynamicSupportValueChange`.
3. **Price & City Elasticity:** `MatchTicketPriceInfo` relative to national `Economic Factor (1..20)`, `City Attraction (1..20)` & `Inhabitants Bracket` (`client_db.dat` `Frame #02`), and matchday **Weather (`weather.xml`)**.

---

## 16. Board Confidence, Supporter Confidence & `ClubVision` Composite Scoring Algorithm

In `global-metadata.dat`, manager job security (`TakeoverBoardConfidenceOverallGrade` & `SupporterConfidenceOverallGrade`) is computed from two parallel composite scores:

```mermaid
flowchart LR
    subgraph Board["Board Confidence (DebugBoardConfidenceOverallScore)"]
        B1["Club Vision Score
(YearOneCompScore + LongTermCompScore
+ ClubCultureScore)"]
        B2["Match Score
(DebugBoardMatchScore)"]
        B3["Financial Compliance
(DebugCompAnalysisClubFinances)"]
        B4["Squad & Transfer Rating
(DebugCompAnalysisSquadMakeUp)"]
        B5["Tenure & Reputation Shield
(DebugBoardConfidenceModifier)"]
    end
    subgraph Fans["Supporter Confidence (SupporterConfidenceOverallGrade)"]
        S1["Supporter Vision Objectives
(DebugSupporterClubVisionOverallScore)"]
        S2["Match & Derby Results
+ Tactical Entertainment"]
        S3["Star Player Retention &
Transfer Approval"]
    end
    B1 & B2 & B3 & B4 & B5 --> J["Job Security & Ultimatum Check"]
    S1 & S2 & S3 --> J
```

- **Objective Weighting (`ClubVisionObjectiveReference`):** Each objective carries an importance tier (*Required, Desired, Preferred, Favoured*). Failing a **Required** Year-1 competition target (`DebugBoardClubVisionYearOneCompScore`) while `DebugBoardMatchScore` is low triggers the board confidence crisis meeting (`1-match` or `5-match points target` ultimatum).

---

## 17. Match Environment Physics: 4-Season Weather (`weather.xml`), Altitude (`altitude_ft`), Pitch Dimensions & Referees (`official.xml`)

### 17.1 4-Season Regional Weather Engine (`editor.fmf` Frame `#056: weather.xml`)
Every city (`58,349` in `client_db.dat` `Frame #02`) references a `weather_profile_id` (`offset +27`). Each weather profile splits the calendar year into **4 seasonal windows (`w0..w3`)** with `Start Day` (`w0sd..w3sd`) and probability distributions over:
- **5 Precipitation States (`p0..p4`):** `Dry`, `Wet`, `Drizzle`, `Shower`, `Down Pour` (affects ball skid speed, bounce height, handling errors, and pass drag).
- **5 Wind States (`w0..w4`):** `Calm`, `Breezy`, `Gusty`, `Strong`, `Gale` (deflects long balls, crosses, and goal kicks).
- **10 Temperature Brackets (`te, tv, t0..t7`):** `Extremely Freezing (<= -16°C)` through `Extremely Hot (>= 43°C)` plus `Day/Night Variance` (`dn`) — high heat (`t5..t7`, `>= 29°C`) accelerates match `Condition` drain.

### 17.2 City Elevation (`altitude_ft`) & Stadium Pitch Dimensions (`server_db.dat` Frame `#22`)
1. **Altitude Stamina Drain (`altitude_ft` at `offset +20` in `client_db.dat` `Frame #02`):**
   - Cities at high elevation (`> 5,000 ft / 1,500 m`, up to `> 11,000 ft / 3,400 m` in South America) impose an additional stamina/condition drain multiplier on visiting teams whose home city is near sea level.
2. **Pitch Dimensions (`pitch_length_m` × `pitch_width_m` at `offset +27` in `server_db.dat` `Frame #22`):**
   - Stored in decimeters (`e.g., 1050 × 680 dm = 105.0m × 68.0m`, bounded by `min_pitch` and `max_pitch` at `offset +56`). Narrow/short pitches compress the `24` `OOP` zones (`oop_pitch_proximity_scores.jsb`), favoring compact low blocks (`Catenaccio / Route One`), whereas wide/long pitches stretch horizontal recovery distances against `Wing Play` and `Tiki-Taka`.

### 17.3 Referee & Assistant Official Simulation (`editor.fmf` Frame `#047: official.xml`)
Every match official (`9,872` in `basic_people_db.dat`, `34` bytes) is governed by `16` properties in `official.xml`:
- **`Oalf` (`Allowing Flow`, `1..20`):** High values reduce whistle frequency on marginal contact (`Tackles Lost` / `Fouls Committed`).
- **`Odis` (`Discipline`, `1..20`):** Probability of issuing a `Yellow Card` (`-50` match rating) or `Red Card` (`-300` match rating) for a given foul severity.
- **`Oimm` (`Important Matches`, `1..20`) & `Oprs` (`Pressure`, `1..20`):** Resistance to home-crowd pressure (`CrowdAttendanceScalar`) on penalty/card calls in high-stakes fixtures.
- **`Oref` (`Refereeing`, `1..20`) & `Orun` (`Running Line`, `1..20`):** Accuracy of foul/penalty decisions and assistant offside calls in competitions without VAR.
- **`Otkp` (`Time Keeping`, `1..20`):** Precision of added stoppage time (`TotalStoppagesAllowed`) relative to actual ball-out-of-play events.

---

## 18. Automated Set-Piece Priority Matrix, Hat-Trick Penalty Rule & Ballon d'Or / Hall of Fame Scoring Algorithm

### 18.1 Set-Piece Priority Matrix & Dynamic Penalty Selector (`EventFmxSetPiece*`)
In `global-metadata.dat` and `set_piece_manager.dat`, FM26 automates set-piece assignments via **ranked attribute priority queues** (`EventFmxSetPieceCategoryPriorityMove`) so substitutions never break corner/free-kick structures:
1. **Aerial Threat Queue:** Ranked by `Jumping Reach + Heading + Strength + Bravery + Aggression` (assigns `Near Post`, `Far Post`, `Attack Ball` roles).
2. **Box Threat & Creator Queues:** Ranked by `Anticipation + Off The Ball + Finishing + Composure` (for `Lurk Outside Area` / `Mark Keeper`) and `Crossing + Corners + Free Kick Taking + Technique` (for `Takers`).
3. **Recovery Defenders Queue:** Ranked by `Pace + Acceleration + Positioning + Decisions + Anticipation` (for `Stay Back` / `Stay Back If Needed`).
4. **3 Built-in Dynamic Penalty Taker Rules (`global-metadata.dat`):**
   - **`EventFmxSetPieceToggleChangeIfAlreadyMissed`:** Automatically hands the next penalty to `#2` on the list if Taker `#1` missed a penalty earlier in the match.
   - **`EventFmxSetPieceToggleChangeIfAlreadyTaken`:** Rotates penalty takers if a second penalty is awarded in the same match.
   - **`EventFmxSetPieceToggleTwoGoalsScorers` (The Hat-Trick Rule):** If a teammate is currently on **`2` goals** in the match, the designated penalty taker automatically lets them take the penalty to complete their **hat-trick**!

### 18.2 Ballon d'Or (`award_manager.dat`) & Hall of Fame (`hall_of_fame.dat`) Scoring Algorithms
1. **World Player of the Year / Ballon d'Or Voting (`award_manager.dat`):**
   - Candidates are scored over the voting window by:
     $$	ext{AwardScore} = w_1 ig(\overline{	ext{Rating}} 	imes 	ext{CompRepFactor}ig) + w_2 (	ext{Goals} + 0.7 	imes 	ext{Assists} + 	ext{PoM}) + w_3 	ext{WorldReputation} + w_4 	ext{TrophyPoints}$$
   - Because `WorldReputation` and `CompRepFactor` carry substantial weight, a player averaging `7.45` in a top-5 European league + Champions League outscores a player averaging `7.90` in a lower-reputation league.
2. **Manager Hall of Fame (`hall_of_fame.dat` & `HallOfFameEntryCompetitionReference`):**
   - Tracked across Worldwide, Continental (`HallOfFameContinents`), and National (`HallOfFameNations` / `HallOfFameNationalities`) leaderboards (`extra_sections.py`), awarding points strictly for **First-Team Major Trophies** scaled by the competition's reputation tier (`Continental Club Cup > Top-Flight Domestic League > Major Domestic Cup > Second-Tier / Super Cups`).
