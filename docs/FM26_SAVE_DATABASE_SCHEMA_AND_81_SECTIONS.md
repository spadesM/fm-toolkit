# Football Manager 26 — Complete 28-Table Save Database Schema & 81 Container Sections Reference

> **Repository:** [`fm-toolkit`](../)  
> **Core Readers:** [`fm26save/_core/readers/`](../fm26save/_core/readers), [`fm26save/container.py`](../fm26save/container.py), [`fm26save/extra_sections.py`](../fm26save/extra_sections.py)

---

## Part 1: Complete Catalog of the 28 Structured Save Database Tables

All 28 structured tables are extracted from `game_db.dat`, `pl_hist_dt.dat`, `tactics_man.dat`, `set_piece_manager.dat`, `training_man.dat`, `mentoring_manager.dat`, `job_centre.dat`, and `fixture_details.dat` via `sv.table("<table_name>")` or `sv.<method_name>()`.

| # | Table Name (`CLI`) | Python Method (`FM26Save`) | Rows (`Project_Super_Lig.fm` — Jul 2025, Build `2603`) | Primary Key / Foreign Keys | Key Fields & Enriched Properties |
| :---: | :--- | :--- | ---: | :--- | :--- |
| **1** | `players` | `sv.table("players")` | `41,284` | `uid`, `db_id`, `club_uid`, `nation_id` | `name`, `first_name`, `last_name`, `date_of_birth`, `height_cm`, `weight_kg`, `ability` (`current`, `potential`), `attributes` (`43` fields on `1..100` & `1..20` scales), `positions` (`11` slots `1..20`), `contract`, `second_nationalities`, plus enriched `shirt_number`, `rca`, `favoured_clubs`, `favoured_people`, `languages`. |
| **2** | `contracts` | `sv.table("contracts")` | `39,842` | `player_uid`, `club_uid` | `wage` (weekly), `start_date`, `expiry_date`, `squad_status`, `clauses` (`list`), `bonuses` (`list`), plus decoded `.signing_or_loyalty_fee` (`money_a`), `.agent_fee` (`money_b`), `.package_bonus` (`money_c`), `.option_or_reference_year` (`e12`, with `1900` null sentinel mapped to `None`). |
| **3** | `suspensions` | `sv.table("suspensions")` | `193` | `player_uid`, `competition_uid` | `matches_remaining`, `reason_code`, `start_date`, `competition_type`. |
| **4** | `injuries` | `sv.table("injuries")` | `1,244` | `player_uid`, `injury_type_id` | `injury_name`, `start_date`, `return_date`, `days_remaining`, `severity`. |
| **5** | `injury-types` | `sv.table("injury_types")` | `93` *(save) / `136` (`server_db`)* | `id`, `uid` | `name`, `sentence_name`, `category`, `min_days`, `extra_days`, `is_contagious`, `career_threatening_age`. |
| **6** | `player-season-stats` | `sv.table("player_season_stats")` | `33,572` | `player_uid`, `club_uid`, `competition_uid` | `appearances`, `sub_appearances`, `goals`, `assists`, `penalties`, `yellow_cards`, `red_cards`, `player_of_the_match`, `average_rating`, `minutes_played`, `xg`. |
| **7** | `player-season-history` | `sv.table("player_season_history")` | `459,908` | `player_uid`, `year`, `club_uid` | Historical career season rows from `pl_hist_dt.dat`: `year`, `club_uid`, `division_uid`, `apps`, `goals`, `assists`, `avg_rating`, `transfer_fee`. |
| **8** | `player-match-stats` | `sv.table("player_match_stats")` | `320` | `fixture_id`, `player_uid`, `club_uid` | Per-match telemetry: `minutes`, `rating`, `goals`, `assists`, `shots`, `key_passes`, `tackles`, `interceptions`, `dribbles`, `xg`. |
| **9** | `clubs` | `sv.table("clubs")` | `28,620` | `uid`, `db_id`, `nation_id`, `city_id`, `stadium_id` | `name`, `short_name`, `six_letter_name`, `three_letter_name`, `reputation` (`0..10000`), `year_founded`, `status` (Pro/Semi-Pro/Amateur), `division_uid`, `morale`, `colours`. |
| **10** | `managed-clubs` | `sv.table("managed_clubs")` | `1` | `club_uid`, `manager_uid` | Detailed active human-managed club state, transfer/wage budgets, and tactical pointers. |
| **11** | `finances` | `sv.table("finances")` | `28,620` | `club_uid` | `balance`, `transfer_budget`, `wage_budget`, `current_wage_spend`, `projected_balance`, `debt`, `ffp_status`, `income_history`, `expenditure_history`. |
| **12** | `sponsorships` | `sv.table("sponsorships")` | `2,437` | `club_uid` | `sponsor_type` (Kit, Main, Stadium, Training), `annual_value`, `start_year`, `end_year`, `is_fixed`. |
| **13** | `facilities` | `sv.table("facilities")` | `28,620` | `club_uid`, `stadium_id` | `training` (`1..20`), `youth_facilities` (`1..20`), `youth_academy` (`1..20`), `youth_recruitment` (`1..20`), plus enriched `corporate_facilities_1_20` (`+50`), `season_ticket_holders` (`+41`), `expected_attendance` (`+45`), `fanbase_commercial_index` (`+33`). |
| **14** | `stadiums` | `sv.table("stadiums")` | `22,944` | `id`, `uid`, `city_id`, `owner_club_uid` | `name`, `capacity`, `seated_capacity`, `expansion_capacity`, `pitch_length_m`, `pitch_width_m`, `surface_type`, `roof_type`, `build_date`. |
| **15** | `affiliates` | `sv.table("affiliates")` | `4,048` | `parent_club_uid`, `affiliate_club_uid` | `affiliation_type` (Loan, First Option, Commercial, Youth, B-Team), `annual_fee`, `start_date`. |
| **16** | `staff` | `sv.table("staff")` | `4,283` | `uid`, `db_id`, `club_uid`, `nation_id` | `name`, `date_of_birth`, `kind` (`contracted`, `listed`, `human`), `current_ability`, `potential_ability`, `tactical_attributes`, `mental_attributes`, plus baked-in `b40_20_0..25` (**26 hidden `1..100` (`5`-step) staff attribute slots mapped to `1..20` scale**) and decoded `r4` job role (`0..88`). |
| **17** | `staff-lists` | `sv.table("staff_lists")` | `1,528` | `club_uid` | Per-club departmental staff roster lists (`0` = Medical, `1` = Coaching, `2` = Scouting/Recruitment). |
| **18** | `tactics` | `sv.table("tactics")` | `1` | `club_uid`, `slot_index` | `formation_name`, `mentality`, `in_possession_instructions`, `out_of_possession_instructions`, `transition_instructions`, `player_slots` (`11` positions & roles), and `selectors` (`Starting XI` + `Bench`). |
| **19** | `set-pieces` | `sv.table("set_pieces")` | `1` | `club_uid`, `routine_type` | Corner, free-kick, and throw-in routines, zone assignments, and taker priority lists. |
| **20** | `training` | `sv.table("training")` | `1` | `club_uid`, `player_uid` | Weekly team training schedule sessions (`day1..day7`) and individual player role/attribute focus & intensity. |
| **21** | `mentoring` | `sv.table("mentoring")` | `3` | `club_uid`, `group_id` | Mentoring group members (`player_uid` list) and estimated personality/trait influence weights. |
| **22** | `job-vacancies` | `sv.table("job_vacancies")` | `122` | `club_uid`, `role_id` | Open managerial and backroom staff vacancies, applicant pools, and board expectations. |
| **23** | `competitions` | `sv.table("competitions")` | `2,230` | `uid`, `db_id`, `nation_id`, `continent_id` | `name`, `short_name`, `three_letter_code`, `reputation` (`0..10000`), `level` (Division Tier), `type` (League, Cup, Supercup, International). |
| **24** | `stages` | `sv.table("stages")` | `1,304` | `competition_uid`, `stage_index` | `stage_name`, `stage_type` (League Table, Group Stage, Knockout Round), `teams_count`, `rounds_count`. |
| **25** | `league-tables` | `sv.table("league_tables")` | `445` | `competition_uid`, `stage_index`, `club_uid` | `position`, `played`, `won`, `drawn`, `lost`, `goals_for`, `goals_against`, `goal_difference`, `points`, `form_string`, `qualification_status`. |
| **26** | `fixtures` | `sv.table("fixtures")` | `904` | `id`, `competition_uid`, `home_club_uid`, `away_club_uid` | `match_date`, `home_score`, `away_score`, `attendance`, `stadium_id`, `referee_uid`, `status` (Scheduled, Played, Postponed). |
| **27** | `competition-rules` | `sv.table("competition_rules")` | `144` | `competition_uid`, `nation_id` | Squad registration limits, foreign/non-EU player caps, home-grown quotas, substitution rules (`3` or `5` subs), prize money, and disciplinary thresholds. |
| **28** | `transfer-windows` | `sv.table("transfer_windows")` | `461` | `nation_id`, `window_index` | `start_date`, `end_date`, `window_type` (Summer / Primary, Winter / Secondary, Domestic-Only, Free Agents). |

---

## Part 2: Complete Catalog of the 81 Zstandard Sections Inside an FM26 `.fm` Save Container

Every `.fm` save file is a `\x02\x01fmf.` multi-frame Zstandard container with a 26-byte outer header and a Zstandard-compressed trailer directory (`sv.container.list_entries()`) indexing **81 core sections (`64` `.dat` + `17` `.cmt`)**. Below is the complete reference of those sections grouped by engine subsystem:

### 2.1 Core Database & Historical Ledgers (`8` Sections — `~85%` of Save Size)
| Section Name | Typical Compressed Size | Typical Decompressed Size | Contents & Binary Structure |
| :--- | ---: | ---: | :--- |
| **`game_db.dat`** | `~26–58 MB` | `~88–187 MB` | Primary relational memory dump of all active entities: Clubs, Players, Staff, Contracts, Finances, Facilities, Stadiums, Injuries, Suspensions, Competitions, Stages, and Standings. |
| **`pl_hist_dt.dat`** | `~18–42 MB` | `~140–210 MB` | Complete season-by-season career statistical history (`player-season-history`) for every active and recently retired player. |
| **`pl_hist_id.dat` / `pl_hist_index.dat` / `pl_hist_ls.dat`** | `~1.2–2.4 MB` | `~4.5–9.0 MB` | Binary `(person_uid -> hist_idx -> head_offset, tail_offset)` lookup tables for instant random access into `pl_hist_dt.dat`. |
| **`non_pl_hist_dt.dat` / `non_pl_hist_id.dat` / `non_pl_hist_index.dat`** | `~3–7 MB` | `~20–35 MB` | Complete career history and index tables for managers, coaches, scouts, physios, and club officials. |

### 2.2 Dedicated Extra Section Scanners & Parsers in [`fm26save/extra_sections.py`](../fm26save/extra_sections.py) (`6` Sections + Universal Inspector)
*(Note: Because these smaller `.dat` manager sections use dynamic variable-length serialization without fixed-stride row headers, `extra_sections.py` implements targeted binary signature/string/UID heuristic scanners over the decompressed section streams.)*
| Section Name | Python Method | Contents & Reverse-Engineered Record Fields |
| :--- | :--- | :--- |
| **`hall_of_fame.dat`** | [`sv.hall_of_fame()`](../fm26save/extra_sections.py) | Worldwide, national, and continental Hall of Fame manager records (`first_name`, `last_name`, `nationality_id`, `major_trophies`, `minor_trophies`, `hof_points`). |
| **`board_takeover_man.dat`** | [`sv.board_takeovers()`](../fm26save/extra_sections.py) | Active and historical board takeover negotiations (`buyer_first_name`, `buyer_last_name`, `buyer_city_or_company`, `target_club_uid`, `takeover_type`, `start_date`). |
| **`shortlist_man.dat`** | [`sv.shortlists()`](../fm26save/extra_sections.py) | Manager and Chief Scout shortlists (`shortlist_name`, `player_uid`, resolved `player_name`, `club_uid`, `added_date`, `priority_flags`). |
| **`contract_man.dat`** | [`sv.contract_offers()`](../fm26save/extra_sections.py) | Active in-flight contract offers and renewal negotiations (`player_uid`, `offering_club_uid`, `offered_wage`, `signing_fee`, `agent_fee`, `offer_date`, `state_code`). |
| **`agent_manager.dat`** | [`sv.agents()`](../fm26save/extra_sections.py) | Player agents (`agent_uid`, `first_name`, `last_name`, `nation_id`, `fee_demand_level`, `patience_level`, `client_player_uids`). |
| **`news.dat`** | [`sv.news_items()`](../fm26save/extra_sections.py) | In-game news articles, headlines, template strings, and cross-referenced club/player/competition/stadium UIDs. |
| **Any of the 81 `.dat` / `.cmt` sections** | [`sv.analyze_section(name)`](../fm26save/extra_sections.py) | Universal binary analyzer that extracts decompression metrics, UTF-8 length-prefixed strings, valid FM binary dates (`1990..2050`), and cross-referenced `player_uid` / `club_uid` pointers for any section in the container. |

### 2.3 Complete Index of All 81 Container Section Names (`64` `.dat` + `17` `.cmt`)
- **64 `.dat` Sections:** `achievements.dat`, `agent_manager.dat`, `award_man.dat`, `basic_comps.dat`, `board_takeover_man.dat`, `career_stat_man.dat`, `Central Server Interface.dat`, `ChallengeManager.dat`, `clear_house_man.dat`, `club_expectations.dat`, `CompetitionHistory.dat`, `comps.dat`, `contract_man.dat`, `country_trouble_man.dat`, `cup_draw_man.dat`, `discipline_man.dat`, `disciplinary_manager.dat`, `draft_man.dat`, `dynamic_manager.dat`, `event_man.dat`, `extra_data_man.dat`, `fantasy_draft_man.dat`, `financial_fair_play_man.dat`, `fixture_details.dat`, `fmf_file_data.dat`, `friendly_instructions.dat`, `game_db.dat`, `game_pairing_man.dat`, `hall_of_fame.dat`, `header.dat`, `human_manager_list.dat`, `injury_manager.dat`, `international_man.dat`, `job_centre.dat`, `leaderboard_man.dat`, `league_body_man.dat`, `local_derbies.dat`, `mail_man.dat`, `match_Hyped_fixtures_man.dat`, `media_man.dat`, `mentoring_manager.dat`, `news.dat`, `non_pl_hist_dt.dat`, `non_pl_hist_id.dat`, `non_pl_hist_index.dat`, `note_man.dat`, `options.dat`, `pl_hist_dt.dat`, `pl_hist_id.dat`, `pl_hist_index.dat`, `pl_hist_ls.dat`, `player_form_man.dat`, `recruitment_focus_manager.dat`, `referees_manager.dat`, `set_piece_manager.dat`, `shortlist_man.dat`, `social_network_man.dat`, `Stage Rules Manager.dat`, `tactics_man.dat`, `temp_ban_man.dat`, `training_man.dat`, `transfer_centre_man.dat`, `transfer_man.dat`, `VersusModeManager.dat`.
- **17 `.cmt` Commentary Sections:** `dan.cmt`, `dut.cmt`, `eng.cmt`, `enu.cmt`, `fre.cmt`, `ger.cmt`, `gre.cmt`, `ita.cmt`, `jpn.cmt`, `kor.cmt`, `nor.cmt`, `pol.cmt`, `por.cmt`, `rus.cmt`, `sch.cmt`, `spa.cmt`, `swe.cmt`, `tch.cmt`, `tur.cmt` *(17 active localized match commentary streams per save)*.
