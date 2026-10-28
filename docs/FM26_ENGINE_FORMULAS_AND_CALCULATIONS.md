# Football Manager 26 — Mathematical Formulas, Engine Models & Empirical Derivations

> **Repository:** [`fm26save`](../)  
> **Core Implementation:** [`fm26save/formulas.py`](../fm26save/formulas.py)  
> **Data Sources:**
> 1. **FM26 Game Engine Archives (`.fmf` & `.jsb` Binary JSON):** `shared/data/simatch.fmf`, `shared/data/shared/tables.fmf`, `data/game_simulation/training.fmf`, `shared/data/editor.fmf`, and `fm_Data/il2cpp_data/Metadata/global-metadata.dat` (`Build 26.3.2+2329565`).
> 2. **Empirical Save Database Regressions:** Cross-validated across **41,284 players**, **39,842 active contracts**, and **6,698 staff members** in `Project_Super_Lig.fm`.

---

## 1. Current Ability (CA), Potential Ability (PA) & Recommended Current Ability (RCA)

### 1.1 Internal Representation in `game_db.dat`
Every player record in `game_db.dat` stores ability values in two distinct binary locations:
- **Ability Block (`u16` Little-Endian, `1..200` scale):**
  - `current_ability` (`CA`): Overall current ability points consumed (`1..200`).
  - `potential_ability` (`PA`): Maximum ceiling (`1..200`). In static pre-game databases (`people_db.dat` / `editor.fmf`), negative values (`-1` to `-10` and `-15` to `-100`) encode dynamic random PA ranges rolled upon save creation.
- **Player Record Tail Bytes (`offset +117..+119` from record start):**
  - `offset +117` (`u8`): **Squad/Shirt Number** (`1..99`; `255 / 0xFF` = unassigned).
  - `offset +118` (`u8`): **Recommended Current Ability (`RCA`) / Peak CA Byte** (`r = 0.968` correlation with `CA`).
  - `offset +119` (`u8`): **Mirrored `PA` Byte** (`r = 1.000` identity with `PA`).

---

### 1.2 Position-Specific CA Attribute Weights (`0..10` Normalized Scale)
In FM26, **Current Ability (`CA`) is not a flat sum of attributes**. Each position has its own weight vector $w_{p,i} \in [0, 10]$, and **Weak Foot (`weak_foot = min(left_foot, right_foot)`)** is one of the single most expensive CA consumers for central and two-way positions (`MC`, `AMC`, `STC`, `DM`).

$$
\text{RCA}_{\text{pos}} = \alpha_{\text{pos}} + \beta_{\text{pos}} \sum_{i} w_{\text{pos}, i} \cdot \text{Attr}_i + \gamma_{\text{pos}} \cdot \text{WeakFoot}
$$

Cross-validation across 41,284 players yields **$R^2 = 0.985 \text{ to } 0.996$** across all 10 position lines:

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
| **Jumping Reach** | — | **6.0** | — | — | — | — | — | — | — | 4.5 |
| **Heading** | — | 4.2 | 3.5 | — | — | — | — | — | — | 4.8 |
| **First Touch** | — | 2.0 | 3.9 | 4.4 | 4.2 | **6.9** | 4.0 | 4.3 | 4.0 | 5.0 |
| **Passing** | 2.0 | 1.9 | 2.4 | 3.5 | 3.6 | 5.8 | 2.4 | 3.3 | 2.1 | — |
| **Vision** | — | — | — | — | 3.8 | **6.2** | 2.5 | 5.0 | — | — |
| **Technique** | — | — | — | 2.6 | — | 4.6 | 3.2 | 4.4 | 2.5 | 3.3 |
| **Crossing** | — | — | 3.1 | 3.4 | — | — | 4.3 | — | 3.8 | — |
| **Dribbling** | — | — | 2.2 | 3.2 | — | 3.5 | 3.1 | 2.9 | 3.8 | 3.9 |
| **Finishing** | — | — | — | — | — | — | — | 2.5 | 2.2 | **7.5** |
| **Off The Ball** | — | — | — | 2.7 | — | 3.3 | 2.6 | 2.7 | 2.3 | 5.4 |
| **Composure** | 1.8 | 2.6 | — | — | 3.1 | 3.4 | — | 2.6 | — | 5.2 |
| **Antic. / Conc.** | 2.8 / 5.4 | 4.3 / 3.3 | 4.2 / 5.2 | 4.8 / 3.5 | 4.7 / 3.4 | 4.6 / — | 3.3 / — | 3.3 / — | 2.9 / 2.4 | 4.0 / — |
| **Reflexes / Handling** | **7.8 / 7.7** | — | — | — | — | — | — | — | — | — |
| **Aerial / Cmd Area** | 5.5 / 4.9 | — | — | — | — | — | — | — | — | — |

### 1.3 Zero-CA-Cost ("Free") Attributes
The following **6 visible attributes** and **8 hidden personality attributes** consume **zero (or near-zero) CA points** in FM26:
- **Visible (`1..20`):** `Determination`, `Flair`, `Aggression`, `Natural Fitness`, `Leadership`, `Eccentricity` (plus set-piece specialists `Corners`, `Free Kicks`, `Long Throws`, `Penalty Taking` carry minimal weight `< 0.5`).
- **Hidden Personality (`1..20`):** `Professionalism`, `Ambition`, `Loyalty`, `Pressure`, `Sportsmanship`, `Temperament`, `Controversy`, `Adaptability`.

---

## 2. Tactical Role Effectiveness & Dual-Role Scoring Engine

### 2.1 In-Possession Role Score (`calculate_role_effectiveness`)
Each In-Possession role $R$ and duty $D \in \{\text{Defend, Stopper, Cover, Support, Attack, Float}\}$ defines:
- A set of **Key Attributes** $K_{R,D}$ with weight $w_{\text{key}} = 2.0$,
- A set of **Preferable Attributes** $P_{R,D}$ with weight $w_{\text{pref}} = 1.0$.

The raw attribute aptitude on the `1..20` scale is:

$$
S_{\text{raw}, 20}(R, D) = \frac{2.0 \sum_{a \in K_{R,D}} \text{Attr}_a + 1.0 \sum_{b \in P_{R,D}} \text{Attr}_b}{2.0 \cdot |K_{R,D}| + 1.0 \cdot |P_{R,D}|}
$$

This raw aptitude is then modulated by two tactical multipliers:

1. **Position Familiarity Multiplier ($M_{\text{pos}}$):**
   | Position Rating (`1..20`) | Familiarity Tier | Multiplier $M_{\text{pos}}$ |
   | :---: | :--- | :---: |
   | `19..20` | **Natural** | `1.00` |
   | `15..18` | **Accomplished** | `0.93` |
   | `11..14` | **Competent** | `0.84` |
   | `5..10` | **Unconvincing** | `0.72` |
   | `1..4` | **Makeshift** | `0.55` |

2. **Foot Alignment Multiplier ($M_{\text{foot}} \in [0.94, 1.02]$):**
   - `same_side` roles (`Winger`, `Full-Back`, `Wing-Back`, `Wide Centre-Back`) reward strong left foot on the left flank (`DL/WBL/ML/AML`) and strong right foot on the right flank (`DR/WBR/MR/AMR`).
   - `inverted` roles (`Inside Forward`, `Inverted Winger`, `Inverted Wing-Back`, `Wide Playmaker`) reward strong opposite foot (`>= 18` gives `1.02x`, `< 11` gives `0.94x`).
   - `either` central roles reward weak-foot proficiency (`0.98 + 0.002 * min(left_foot, right_foot)`).

$$
S_{\text{eff}, 20} = S_{\text{raw}, 20} \times M_{\text{pos}} \times M_{\text{foot}}, \qquad S_{\text{eff}, 100} = \min(100.0,\; 5.0 \times S_{\text{eff}, 20})
$$

### 2.2 Out-Of-Possession (`OP*`) & Combined Dual-Role Score
FM26 decouples tactical roles into **In-Possession (`IP`)** and **Out-Of-Possession (`OP*`)**. Each of the 39 `OP*` roles is scored via its defensive/transition Key (`x2.0`) and Preferable (`x1.0`) attributes, and the combined Dual-Role synergy score on a position line is:

$$
S_{\text{dual}, 100}(\text{IP}, \text{OOP}) = 0.55 \cdot S_{\text{eff}, 100}(\text{IP}) + 0.45 \cdot S_{\text{eff}, 100}(\text{OOP})
$$

---

## 3. Empirical Market Transfer Value Model (`estimate_transfer_value`)

Fitted via Ordinary Least Squares (OLS) on **11,834 priced players** in `Project_Super_Lig.fm` ($R^2 = 0.805$):

$$
\begin{aligned}
\ln(\text{TransferValue}) &= 5.72207 \\
&\quad + 0.04063 \cdot \text{CA} + 0.00666 \cdot \max(0, \text{CA} - 115) \\
&\quad + 0.16353 \cdot \left(\frac{\text{PlayerRep}}{1000}\right) - 0.07339 \cdot \left(\frac{\text{WorldRep}}{1000}\right) - 0.17025 \cdot \left(\frac{\text{ClubRep}}{1000}\right) \\
&\quad - 0.16164 \cdot \text{Age} + 0.03968 \cdot \max(0, \text{Age} - 28) \\
&\quad + 0.66654 \cdot \ln(\text{RemainingContractYears}) \\
&\quad + 0.82278 \cdot \ln(\text{WeeklyWage}) \\
&\quad + 0.43513 \cdot \frac{\max(0, 24 - \text{Age}) \cdot \max(0, \text{PA} - \text{CA})}{100} \\
&\quad - 0.26591 \cdot \mathbb{I}(\text{StarOrImportantPlayer})
\end{aligned}
$$

### Key Quantitative Insights:
- **Weekly Wage Elasticity (`+0.823`):** Every `10%` increase in a player's weekly wage increases their market valuation by **`+8.2%`**.
- **Remaining Contract Length Elasticity (`+0.667`):** A player with `4.0` years remaining is valued **`2.52x` (`+152%`) higher** than an identical player entering their final `1.0` year ($\exp(0.66654 \cdot \ln 4) = 2.52$).
- **Superlinear CA Premium above 115:** Above `CA = 115`, each additional CA point adds **`+4.84%`** to transfer value (compounding to **`+60.5%`** per `10` CA points).
- **Youth Surplus Potential Premium:** For U-24 players, unfulfilled potential ($\text{PA} - \text{CA}$) multiplied by years under 24 adds up to **`+35% to +80%`** wonderkid premium.

---

## 4. Weekly Wage, Signing/Loyalty Fee (`money_a`) & Agent Fee (`money_b`)

Fitted across **39,842 contracts** in `Project_Super_Lig.fm`:

$$
\begin{aligned}
\ln(\text{WeeklyWage}) &= 1.04103 + 0.01843 \cdot \text{CA} + 0.02248 \cdot \max(0, \text{CA} - 115) - 0.01802 \cdot \max(0, \text{CA} - 145) \\
&\quad + 0.08630 \cdot \left(\frac{\text{PlayerRep}}{1000}\right) + 0.02394 \cdot \left(\frac{\text{WorldRep}}{1000}\right) + 0.19201 \cdot \left(\frac{\text{ClubRep}}{1000}\right) \\
&\quad + 0.09904 \cdot \text{Age} - 0.00302 \cdot \max(0, \text{Age} - 29) + \Delta_{\text{SquadStatus}}
\end{aligned}
$$

where Squad Status premiums $\Delta_{\text{SquadStatus}}$ are:
- `STAR_PLAYER`: **`+0.59182`** (`1.81x` baseline wage)
- `IMPORTANT_PLAYER`: **`+0.54509`** (`1.72x` baseline wage)
- `REGULAR_STARTER`: **`+0.29583`** (`1.34x` baseline wage)
- `YOUNGSTER / FUTURE_PROSPECT`: **`-0.03846`** (`0.96x` baseline wage)

### Hidden Contract Fee Ratios (`contracts.unknown` Decoded):
| Hidden Field | Meaning | Median Ratio to Annual Wage (`52 × Wage`) | Mean Ratio to Annual Wage |
| :--- | :--- | :---: | :---: |
| **`money_a`** | **Total Signing-On / Loyalty Bonus Pool** | **`18.5%`** (`~9.6 weeks' wage`) | **`24.1%`** (`~12.5 weeks' wage`) |
| **`money_b`** | **Agent Commission Fee** | **`5.2%`** (`~2.7 weeks' wage`) | **`5.9%`** (`~3.1 weeks' wage`) |
| **`money_c`** | **Secondary Package / Relocation Bonus** | `0.0%` (present in elite/loan deals) | `1.4%` |
| **`e12`** | **Contract Option / Reference Year (`u16`)** | Matches `2025..2046` | — |

---

## 5. Match Engine Expected Goals (xG) — All 11 Shot-Type Logistic Models

Decoded from `shared/data/simatch.fmf` (`Frames #90..#100`, Model Version `26.1.4.1`). All coefficients are stored as fixed-point `Int32` scaled by $10^{-8}$:

$$
\text{xG} = \sigma(z) = \frac{1}{1 + e^{-z}}, \qquad z = \beta_0 + \sum_{k} \beta_k \cdot x_k
$$

| Shot Type (`shot_type`) | Intercept $\beta_0$ | `norm_dist_to_goal` | `frac_goal_visible` | `norm_players_between` | `norm_dist_closest_occ` | `norm_ball_height` | `angle_shot_to_goal` | `angle_facing_to_goal` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`regular`** | `-1.209590` | `+1.311615` | `-0.204429` | `-0.464878` | `-0.113698` | — | `+0.175101` | `+0.094974` |
| **`obscured_regular`** | `-1.437583` | `+1.501676` | `+0.070595` | `-0.670923` | `-0.114715` | — | `+0.278406` | `+0.009460` |
| **`open_goal_regular`** | `-1.086731` | `+1.019833` | `+0.164382` | `-0.988886` | `-0.100821` | — | `+0.108076` | `+0.047703` |
| **`headers`** | `-2.852457` | `+3.169746` | `+0.005067` | `-0.418449` | `+0.004884` | `-0.127358` | `-0.030559` | `+0.072824` |
| **`obscured_headers`** | `-3.211159` | `+3.553041` | `-0.016380` | `-0.486708` | `+0.000658` | `-0.062777` | `+0.044915` | `+0.005243` |
| **`open_goal_headers`** | `-1.590770` | `+1.672350` | `+0.153844` | `-0.640985` | `-0.058121` | `-0.109948` | `-0.033603` | `+0.084336` |
| **`volleys`** | `-1.126503` | `+1.218222` | `-0.122370` | `-0.387561` | `-0.084118` | `-0.148597` | `+0.129495` | `+0.059656` |
| **`obscured_volleys`** | `-1.112239` | `+1.159443` | `+0.057677` | `-0.887851` | `-0.062049` | `-0.189403` | `+0.226442` | `+0.011218` |
| **`open_goal_volleys`** | `-1.027918` | `+0.962217` | `+0.180644` | `-0.804227` | `+0.000223` | `-0.028136` | `+0.048043` | `+0.044859` |
| **`free_kicks`** | `-0.434045` | `+0.371943` | — | `+0.129082` | `-0.708200` | — | `+0.042362` | `+0.093573` |
| **`penalties`** | `+0.119847` | — | — | — | `0.000000` | — | — | — |

*(Note: `normalised_distance_to_goal` is an inverted proximity score where `1.0` = goal line and `0.0` = far distance; for penalties, $z = +1.19847 \Rightarrow \sigma(1.19847) \approx 0.768$ (`76.8%` base conversion rate).)*

---

## 6. Match Engine Player Ratings (`player_ratings_data.jsb`)

Decoded from `simatch.fmf` (`Frame #118`, `348,584` bytes):
- **Starting Match Rating:** `start_value = 6500` $\rightarrow$ **`6.50`** on the `1.0–10.0` scale.
- **Team Result & Expectation Multipliers (`expected_score_data`):**
  - `Exceed Significant with Win` / `Draw`: Positive actions multiplied by **`1.20x`** (`1200`), negative actions by `1.00x`.
  - `Exceed with Win` / `Draw`: Positive actions multiplied by **`1.10x`** (`1100`).
  - `Below Significant with Loss`: Negative actions multiplied by **`1.20x`**, positive actions by `1.00x`.
- **Per-Action Rating Deltas (`role_data` coefficients, divided by `1000` for `0.0–10.0` rating points):**

| Match Action | GK Delta | Defender (`DC/FB`) | Midfielder (`DM/MC/AM`) | Forward (`Winger/STC`) |
| :--- | :---: | :---: | :---: | :---: |
| **Goal (`goals`)** | `+1.000` | `+1.000` | `+0.900` | `+0.800` |
| **Penalty Scored (`penalties_scored`)** | `+0.400` | `+0.400` | `+0.400` | `+0.400` |
| **Assist (`assists`)** | `+0.600` | `+0.600` | `+0.600` | `+0.600` |
| **Key Pass (`key_passes`)** | `+0.180` | `+0.200` | `+0.200` | `+0.200` |
| **Created Clear-Cut Chance (`created_ccc`)** | `+0.250` | `+0.250` | `+0.250` | `+0.250` |
| **Missed Clear-Cut Chance (`missed_ccc`)** | `-0.200` | `-0.200` | `-0.250` | `-0.300` |
| **Successful Tackle / Key Tackle** | `+0.050` | `+0.060 / +0.250` | `+0.050 / +0.200` | `+0.040 / +0.150` |
| **Interception (`interceptions`)** | `+0.030` | `+0.045` | `+0.040` | `+0.030` |
| **Mistake Leading to Goal** | `-1.000` | `-1.000` | `-1.000` | `-1.000` |
| **Own Goal (`own_goals`)** | `-0.600` | `-0.600` | `-0.600` | `-0.600` |
| **Penalty Conceded (`penalties_conceded`)** | `-0.500` | `-0.500` | `-0.500` | `-0.500` |
| **Red Card (`red_card`)** | `-1.500` | `-1.500` | `-1.500` | `-1.500` |
| **Save Held / Parried / Tipped (GK)** | `+0.15 / +0.10 / +0.12` | — | — | — |
| **Penalty Save (GK)** | `+0.800` | — | — | — |

---

## 7. Quick Match Engine (QME) Statistical Distributions (`qme_distribution_data.jsb` & `qme_stat_relevant_attribute_data.jsb`)

When simulating background matches (other leagues or Instant Result), FM26 uses **3,137 Normal & Binned probability distributions** (`simatch.fmf` `Frame #119`) indexed by:
1. `position` (`goalkeeper`, `central_defender`, `full_back`, `wing_back`, `defensive_midfielder`, `central_midfielder`, `wide_midfielder`, `attacking_midfielder`, `winger`, `centre_forward`),
2. `ability_window` (`CA` brackets: `[0, 99]`, `[100, 129]`, `[130, 159]`, `[160, 200]`),
3. `attribute_window` (`0.5`-wide brackets on the `1..20` average of the stat's relevant attributes from `Frame #120`),
4. `stat_type` (`22` match stats, e.g., `passes_attempted`, `pass_completion`, `key_passes`, `tackles_attempted`, `tackles_won`, `interceptions`, `headers_won`, `dribbles`, `shots`, `shots_on_target`).

### Relevant Attributes per Simulated Match Stat (`Frame #120`):
- **`passes_attempted`:** `passing`, `work_rate`
- **`pass_completion`:** `passing`, `decisions`
- **`key_passes`:** `passing`, `vision`
- **`crosses_attempted` / `cross_completion`:** `crossing`, `decisions`, `technique`
- **`tackles_attempted` / `tackles_won`:** `tackling`, `aggression`, `decisions`, `anticipation`
- **`interceptions`:** `anticipation`, `positioning`
- **`headers_attempted` / `headers_won`:** `heading`, `jumping_reach`, `strength`, `bravery`
- **`dribbles`:** `dribbling`, `flair`, `acceleration`, `agility`
- **`shots` / `shots_on_target`:** `finishing`, `long_shots`, `composure`, `technique`, `off_the_ball`
- **`fouls_committed`:** `aggression`, `tackling`, `decisions`

---

## 8. AI Starting XI Team Selection Formula (`weights.jsb`)

Decoded from `simatch.fmf` (`Frame #223`, `6,547` bytes). AI managers score each candidate player for each starting lineup slot across 9 `TEAM_PICKING_STYLE` profiles (`TPS_FIRST_TEAM_PICKING`, `TPS_CUP_PICKING`, `TPS_ROTATION`, `TPS_YOUTH`, `TPS_PRE_SEASON`, etc.):

| AI Selection Factor (`simatchshared::TSF_*`) | First Team (`TPS_FIRST_TEAM_PICKING`) | Cup (`TPS_CUP_PICKING`) | Youth (`TPS_YOUTH`) | Pre-Season (`TPS_PRE_SEASON`) |
| :--- | :---: | :---: | :---: | :---: |
| **`TSF_CA` (Current Ability)** | **`+120`** | `+100` | `+50` | `+40` |
| **`TSF_PA` (Potential Ability)** | `+15` | `+20` | **`+120`** | `+35` |
| **`TSF_POSITIONAL_RATING` (Role/Pos Suitability)** | **`+80`** | `+80` | `+70` | `+50` |
| **`TSF_CONDITION` (Physical Condition)** | **`+90`** | `+85` | `+90` | **`+140`** |
| **`TSF_FATIGUE` (Accumulated Fatigue)** | **`-90`** | `-85` | `-90` | **`-150`** |
| **`TSF_MATCH_FITNESS` (Match Sharpness)** | `+30` | `+30` | `+25` | **`+120`** |
| **`TSF_MORALE`** | `+25` | `+25` | `+20` | `+10` |
| **`TSF_FORM` (Recent Match Ratings)** | **`+55`** | `+50` | `+30` | `+5` |
| **`TSF_CAPTAINCY`** | `+40` | `+35` | `+15` | `+10` |
| **`TSF_AGREED_PLAYING_TIME` (Squad Status)** | `+15` | `+10` | `+5` | `+5` |
| **`TSF_ALLOWED_MINS` (Medical Minute Restriction)** | **`-250`** | `-250` | `-250` | `-300` |

---

## 9. Anthropometric Height → Jumping Reach & Aerial Reach Tables (`tables.fmf`)

Decoded from `shared/data/shared/tables.fmf` (`Frames #0 & #2`). FM26 enforces hard minimum/maximum bounds and Gaussian distributions (`mean`, `std`) on `Jumping Reach` and `Aerial Reach` (on the internal `1..100` scale, where `÷ 5` = `1..20` displayed attribute) as a function of `height_cm`:

| Height (`cm`) | Male Jumping Reach (`1..20` Min–Max) | Male Jumping Reach Mean (`1..20`) | Male GK Aerial Reach (`1..20` Min–Max) | Female Jumping Reach (`1..20` Min–Max) |
| :---: | :---: | :---: | :---: | :---: |
| `<= 165 cm` | `1 – 12` | `5.0` | `1 – 10` | `2 – 14` |
| `170 cm` | `2 – 14` | `7.2` | `2 – 12` | `4 – 16` |
| `175 cm` | `4 – 16` | `9.4` | `4 – 14` | `6 – 18` |
| `180 cm` | `6 – 17` | `11.6` | `6 – 16` | `9 – 19` |
| `185 cm` | `8 – 18` | `13.6` | `9 – 18` | `12 – 20` |
| `190 cm` | `11 – 19` | `15.4` | `12 – 19` | `14 – 20` |
| `195 cm` | `13 – 20` | `17.0` | `14 – 20` | `16 – 20` |
| `>= 200 cm` | `15 – 20` | `18.4` | `16 – 20` | `17 – 20` |

---

## 10. Training Session Attribute Weights & Physical Impact (`training.fmf`)

Decoded from `data/game_simulation/training.fmf` (`Frames #1..#4`):
- **Every Training Session (`44` sessions in `training_sessions.jsb`)** distributes development points across:
  - `primary` attributes (**`60%` weight**),
  - `secondary` attributes (**`30%` weight**),
  - `tertiary` attributes (**`10%` weight**).
- **Session Item Physical & Morale Modifiers (`62` items in `session_item_effects.jsb`):**
  Each drill applies integer delta ticks to `condition`, `fatigue`, `injuries` (injury risk), `sharpness`, `happiness`, and `tacticalfamiliarity`. For example:
  - `Endurance` / `Resistance`: High `condition` drain (`-3`), high `fatigue` accumulation (`+2`), elevated `injuries` risk (`+2`), negative `happiness` (`-1`), high physical attribute progression.
  - `Recovery` / `Team Bonding`: Restores `condition` (`+2`), reduces `fatigue` (`-2`) and `injuries` (`-2`), boosts `happiness` (`+2`).
