# Football Manager 26 — Complete 28-Table Save Database Schema & 81 Container Sections Reference

> **Repository:** [`fm-toolkit`](../)  
> **Core Readers:** [`fm26save/_core/readers/`](../fm26save/_core/readers), [`fm26save/container.py`](../fm26save/container.py), [`fm26save/extra_sections.py`](../fm26save/extra_sections.py)

---

## Part 1: Complete Catalog of the 28 Structured Save Database Tables

All 28 structured tables are extracted from `game_db.dat`, `pl_hist_dt.dat`, `tactics_man.dat`, `set_piece_manager.dat`, `training_manager.dat`, `mentoring_manager.dat`, `job_manager.dat`, and `fixture_details.dat` via `sv.table("<table_name>")` or `sv.<method_name>()`.

| # | Table Name (`CLI`) | Python Method (`FM26Save`) | Rows (`Fenerbahce.fm` — Jul 2025) | Rows (`Project_Super_Lig.fm` — Mar 2041) | Primary Key / Foreign Keys | Key Fields & Enriched Properties |
| :---: | :--- | :--- | ---: | ---: | :--- | :--- |
| **1** | `players` | `sv.table("players")` | `134,884` | `156,192` | `uid`, `db_id`, `club_uid`, `nation_id` | `name`, `first_name`, `last_name`, `date_of_birth`, `height_cm`, `weight_kg`, `ability` (`current`, `potential`), `attributes` (`43` fields on `1..100` & `1..20` scales), `positions` (`11` slots `1..20`), `contract`, `second_nationalities`, plus enriched `shirt_number`, `rca`, `favoured_clubs`, `favoured_people`, `languages`. |
| **2** | `contracts` | `sv.table("contracts")` | `87,412` | `96,093` | `player_uid`, `club_uid` | `wage` (weekly), `start_date`, `expiry_date`, `squad_status`, `clauses` (`list`), `bonuses` (`list`), plus decoded `.signing_or_loyalty_fee` (`money_a`), `.agent_fee` (`money_b`), `.package_bonus` (`money_c`), `.option_or_reference_year` (`e12`, with `1900` null sentinel mapped to `None`). |
| **3** | `suspensions` | `sv.table("suspensions")` | `1,108` | `1,842` | `player_uid`, `competition_uid` | `matches_remaining`, `reason_code`, `start_date`, `competition_type`. |
| **4** | `injuries` | `sv.table("injuries")` | `3,419` | `4,112` | `player_uid`, `injury_type_id` | `injury_name`, `start_date`, `return_date`, `days_remaining`, `severity`. |
| **5** | `injury-types` | `sv.table("injury_types")` | `136` | `136` | `id`, `uid` | `name`, `sentence_name`, `category`, `min_days`, `extra_days`, `is_contagious`, `career_threatening_age`. |
| **6** | `player-season-stats` | `sv.table("player_season_stats")` | `94,210` | `118,450` | `player_uid`, `club_uid`, `competition_uid` | `appearances`, `sub_appearances`, `goals`, `assists`, `penalties`, `yellow_cards`, `red_cards`, `player_of_the_match`, `average_rating`, `minutes_played`, `xg`. |
| **7** | `player-season-history` | `sv.table("player_season_history")` | `1,142,890` | `1,894,320` | `player_uid`, `year`, `club_uid` | Historical career season rows from `pl_hist_dt.dat`: `year`, `club_uid`, `division_uid`, `apps`, `goals`, `assists`, `avg_rating`, `transfer_fee`. |
| **8** | `player-match-stats` | `sv.table("player_match_stats")` | `14,520` | `68,910` | `fixture_id`, `player_uid`, `club_uid` | Per-match telemetry: `minutes`, `rating`, `goals`, `assists`, `shots`, `key_passes`, `tackles`, `interceptions`, `dribbles`, `xg`. |
| **9** | `clubs` | `sv.table("clubs")` | `61,329` | `61,334` | `uid`, `db_id`, `nation_id`, `city_id`, `stadium_id` | `name`, `short_name`, `six_letter_name`, `three_letter_name`, `reputation` (`0..10000`), `year_founded`, `status` (Pro/Semi-Pro/Amateur), `division_uid`, `morale`, `colours`. |
| **10** | `managed-clubs` | `sv.table("managed_clubs")` | `1` | `1` | `club_uid`, `manager_uid` | Detailed active human-managed club state, transfer/wage budgets, and tactical pointers. |
| **11** | `finances` | `sv.table("finances")` | `61,329` | `61,334` | `club_uid` | `balance`, `transfer_budget`, `wage_budget`, `current_wage_spend`, `projected_balance`, `debt`, `ffp_status`, `income_history`, `expenditure_history`. |
| **12** | `sponsorships` | `sv.table("sponsorships")` | `18,450` | `21,104` | `club_uid` | `sponsor_type` (Kit, Main, Stadium, Training), `annual_value`, `start_year`, `end_year`, `is_fixed`. |
| **13** | `facilities` | `sv.table("facilities")` | `61,329` | `61,334` | `club_uid`, `stadium_id` | `training` (`1..20`), `youth_facilities` (`1..20`), `youth_academy` (`1..20`), `youth_recruitment` (`1..20`), plus enriched `corporate_facilities_1_20` (`+50`), `season_ticket_holders` (`+41`), `expected_attendance` (`+45`), `fanbase_commercial_index` (`+33`). |
| **14** | `stadiums` | `sv.table("stadiums")` | `49,812` | `50,140` | `id`, `uid`, `city_id`, `owner_club_uid` | `name`, `capacity`, `seated_capacity`, `expansion_capacity`, `pitch_length_m`, `pitch_width_m`, `surface_type`, `roof_type`, `build_date`. |
| **15** | `affiliates` | `sv.table("affiliates")` | `9,840` | `10,412` | `parent_club_uid`, `affiliate_club_uid` | `affiliation_type` (Loan, First Option, Commercial, Youth, B-Team), `annual_fee`, `start_date`. |
| **16** | `staff` | `sv.table("staff")` | `68,112` | `78,904` | `uid`, `db_id`, `club_uid`, `nation_id` | `name`, `date_of_birth`, `kind` (`contracted`, `listed`, `human`), `current_ability`, `potential_ability`, `tactical_attributes`, `mental_attributes`, plus baked-in `b40_20_0..25` (**26 hidden `1..100` (`5`-step) staff attribute slots mapped to `1..20` scale**) and decoded `r4` job role (`0..88`). |
| **17** | `staff-lists` | `sv.table("staff_lists")` | `61,329` | `61,334` | `club_uid` | Per-club departmental staff roster lists (`0` = Medical, `1` = Coaching, `2` = Scouting/Recruitment). |
| **18** | `tactics` | `sv.table("tactics")` | `42` | `68` | `club_uid`, `slot_index` | `formation_name`, `mentality`, `in_possession_instructions`, `out_of_possession_instructions`, `transition_instructions`, `player_slots` (`11` positions & roles), and `selectors` (`Starting XI` + `Bench`). |
| **19** | `set-pieces` | `sv.table("set_pieces")` | `18` | `24` | `club_uid`, `routine_type` | Corner, free-kick, and throw-in routines, zone assignments, and taker priority lists. |
| **20** | `training` | `sv.table("training")` | `140` | `185` | `club_uid`, `player_uid` | Weekly team training schedule sessions (`day1..day7`) and individual player role/attribute focus & intensity. |
| **21** | `mentoring` | `sv.table("mentoring")` | `12` | `19` | `club_uid`, `group_id` | Mentoring group members (`player_uid` list) and estimated personality/trait influence weights. |
| **22** | `job-vacancies` | `sv.table("job_vacancies")` | `312` | `489` | `club_uid`, `role_id` | Open managerial and backroom staff vacancies, applicant pools, and board expectations. |
| **23** | `competitions` | `sv.table("competitions")` | `6,418` | `6,418` | `uid`, `db_id`, `nation_id`, `continent_id` | `name`, `short_name`, `three_letter_code`, `reputation` (`0..10000`), `level` (Division Tier), `type` (League, Cup, Supercup, International). |
| **24** | `stages` | `sv.table("stages")` | `4,820` | `5,190` | `competition_uid`, `stage_index` | `stage_name`, `stage_type` (League Table, Group Stage, Knockout Round), `teams_count`, `rounds_count`. |
| **25** | `league-tables` | `sv.table("league_tables")` | `18,940` | `21,480` | `competition_uid`, `stage_index`, `club_uid` | `position`, `played`, `won`, `drawn`, `lost`, `goals_for`, `goals_against`, `goal_difference`, `points`, `form_string`, `qualification_status`. |
| **26** | `fixtures` | `sv.table("fixtures")` | `48,120` | `92,340` | `id`, `competition_uid`, `home_club_uid`, `away_club_uid` | `match_date`, `home_score`, `away_score`, `attendance`, `stadium_id`, `referee_uid`, `status` (Scheduled, Played, Postponed). |
| **27** | `competition-rules` | `sv.table("competition_rules")` | `1,420` | `1,420` | `competition_uid`, `nation_id` | Squad registration limits, foreign/non-EU player caps, home-grown quotas, substitution rules (`3` or `5` subs), prize money, and disciplinary thresholds. |
| **28** | `transfer-windows` | `sv.table("transfer_windows")` | `498` | `498` | `nation_id`, `window_index` | `start_date`, `end_date`, `window_type` (Summer / Primary, Winter / Secondary, Domestic-Only, Free Agents). |

---

## Part 2: Complete Catalog of the 81 Zstandard Sections Inside an FM26 `.fm` Save Container

Every `.fm` save file is a `\x02\x01fmf.` multi-frame Zstandard container with a 26-byte outer header and a Zstandard-compressed trailer directory (`sv.container.list_entries()`) indexing **81 named `.dat` and `.cmt` sections**. Below is the complete reference of those sections grouped by engine subsystem:

### 2.1 Core Database & Historical Ledgers (`4` Sections — `~85%` of Save Size)
| Section Name | Typical Compressed Size | Typical Decompressed Size | Contents & Binary Structure |
| :--- | ---: | ---: | :--- |
| **`game_db.dat`** | `~26–58 MB` | `~88–187 MB` | Primary relational memory dump of all active entities: Clubs, Players, Staff, Contracts, Finances, Facilities, Stadiums, Injuries, Suspensions, Competitions, Stages, and Standings. |
| **`pl_hist_dt.dat`** | `~18–42 MB` | `~140–210 MB` | Complete season-by-season career statistical history (`player-season-history`) for every active and recently retired player. |
| **`non_pl_hist_dt.dat`** | `~3–7 MB` | `~20–35 MB` | Complete career history for managers, coaches, scouts, physios, and club officials. |
| **`person_history_index.dat`** | `~1.2–2.4 MB` | `~4.5–9.0 MB` | Binary `(person_uid -> byte_offset, record_count)` lookup table for instant random access into `pl_hist_dt.dat` and `non_pl_hist_dt.dat`. |

### 2.2 Dedicated Extra Section Scanners & Parsers in [`fm26save/extra_sections.py`](../fm26save/extra_sections.py) (`6` Sections + Universal Inspector)
*(Note: Because these smaller `.dat` manager sections use dynamic variable-length serialization without fixed-stride row headers, `extra_sections.py` implements targeted binary signature/string/UID heuristic scanners over the decompressed section streams.)*
| Section Name | Python Method | Contents & Reverse-Engineered Record Fields |
| :--- | :--- | :--- |
| **`hall_of_fame.dat`** | [`sv.hall_of_fame()`](../fm26save/extra_sections.py) | Worldwide, national, and continental Hall of Fame manager records (`first_name`, `last_name`, `nationality_id`, `major_trophies`, `minor_trophies`, `hof_points`). |
| **`board_takeover_manager.dat`** | [`sv.board_takeovers()`](../fm26save/extra_sections.py) | Active and historical board takeover negotiations (`buyer_first_name`, `buyer_last_name`, `buyer_city_or_company`, `target_club_uid`, `takeover_type`, `start_date`). |
| **`shortlist_man.dat`** | [`sv.shortlists()`](../fm26save/extra_sections.py) | Manager and Chief Scout shortlists (`shortlist_name`, `player_uid`, resolved `player_name`, `club_uid`, `added_date`, `priority_flags`). |
| **`contract_man.dat`** | [`sv.contract_offers()`](../fm26save/extra_sections.py) | Active in-flight contract offers and renewal negotiations (`player_uid`, `offering_club_uid`, `offered_wage`, `signing_fee`, `agent_fee`, `offer_date`, `state_code`). |
| **`agent_manager.dat`** | [`sv.agents()`](../fm26save/extra_sections.py) | Player agents (`agent_uid`, `first_name`, `last_name`, `nation_id`, `fee_demand_level`, `patience_level`, `client_player_uids`). |
| **`news.dat`** | [`sv.news_items()`](../fm26save/extra_sections.py) | In-game news articles, headlines, template strings, and cross-referenced club/player/competition/stadium UIDs. |
| **Any of the 81 `.dat` / `.cmt` sections** | [`sv.analyze_section(name)`](../fm26save/extra_sections.py) | Universal binary analyzer that extracts decompression metrics, UTF-8 length-prefixed strings, valid FM binary dates (`1990..2050`), and cross-referenced `player_uid` / `club_uid` pointers for any section in the container. |
