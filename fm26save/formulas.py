"""FM26 Mathematical Formulas, Role Effectiveness, CA/PA, Valuation, Wage & Engine JSB Decoders."""

from __future__ import annotations

import math
import struct
from pathlib import Path
from typing import Any

import zstandard as zstd

DEFAULT_FM26_INSTALL_DIR = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26")

# ---------------------------------------------------------------------------
# 1. POSITION-SPECIFIC CURRENT ABILITY (CA) WEIGHTS (0..10 Normalized Scale)
#    Derived from FM26 RCA tables & verified on 41,284 players (R² = 0.985..0.996)
# ---------------------------------------------------------------------------
CA_POSITION_WEIGHTS_10: dict[str, dict[str, float]] = {
    "GK": {
        "decisions": 10.0,
        "reflexes": 7.8,
        "agility": 7.7,
        "handling": 7.7,
        "acceleration": 5.9,
        "aerial_reach": 5.5,
        "concentration": 5.4,
        "bravery": 5.1,
        "command_of_area": 4.9,
        "kicking": 4.3,
        "positioning": 4.2,
        "strength": 3.7,
        "communication": 3.7,
        "one_on_ones": 2.9,
        "anticipation": 2.8,
        "throwing": 2.5,
        "passing": 2.0,
        "composure": 1.8,
        "weak_foot": 2.2,
    },
    "DC": {
        "decisions": 10.0,
        "marking": 8.2,
        "positioning": 8.1,
        "jumping_reach": 6.0,
        "strength": 5.6,
        "agility": 5.2,
        "acceleration": 5.0,
        "weak_foot": 4.4,
        "pace": 4.4,
        "tackling": 4.3,
        "anticipation": 4.3,
        "heading": 4.2,
        "concentration": 3.3,
        "bravery": 2.8,
        "composure": 2.6,
        "stamina": 2.3,
        "first_touch": 2.0,
        "passing": 1.9,
    },
    "DL_DR": {
        "acceleration": 10.0,
        "pace": 8.6,
        "decisions": 8.0,
        "agility": 7.3,
        "stamina": 7.1,
        "strength": 6.0,
        "weak_foot": 5.9,
        "concentration": 5.2,
        "positioning": 4.6,
        "anticipation": 4.2,
        "tackling": 4.2,
        "first_touch": 3.9,
        "heading": 3.5,
        "marking": 3.3,
        "crossing": 3.1,
        "work_rate": 3.0,
        "teamwork": 2.6,
        "passing": 2.4,
        "dribbling": 2.2,
    },
    "WBL_WBR": {
        "acceleration": 10.0,
        "pace": 8.0,
        "decisions": 7.4,
        "stamina": 6.9,
        "agility": 6.6,
        "weak_foot": 5.9,
        "strength": 5.1,
        "anticipation": 4.8,
        "first_touch": 4.4,
        "marking": 3.8,
        "concentration": 3.5,
        "passing": 3.5,
        "crossing": 3.4,
        "tackling": 3.4,
        "dribbling": 3.2,
        "work_rate": 3.1,
        "off_the_ball": 2.7,
        "technique": 2.6,
    },
    "DM": {
        "decisions": 10.0,
        "weak_foot": 6.9,
        "agility": 6.7,
        "acceleration": 6.7,
        "strength": 5.9,
        "tackling": 5.8,
        "positioning": 5.6,
        "marking": 5.0,
        "pace": 4.9,
        "anticipation": 4.7,
        "first_touch": 4.2,
        "stamina": 4.0,
        "vision": 3.8,
        "work_rate": 3.7,
        "passing": 3.6,
        "concentration": 3.4,
        "composure": 3.1,
        "teamwork": 2.8,
    },
    "MC": {
        "acceleration": 10.0,
        "weak_foot": 9.2,
        "pace": 8.4,
        "decisions": 7.7,
        "stamina": 7.6,
        "agility": 7.0,
        "first_touch": 6.9,
        "vision": 6.2,
        "passing": 5.8,
        "strength": 5.1,
        "technique": 4.6,
        "anticipation": 4.6,
        "tackling": 3.8,
        "dribbling": 3.5,
        "composure": 3.4,
        "off_the_ball": 3.3,
        "work_rate": 3.1,
        "positioning": 3.0,
    },
    "ML_MR": {
        "acceleration": 10.0,
        "pace": 9.4,
        "agility": 7.2,
        "stamina": 6.4,
        "weak_foot": 6.0,
        "decisions": 4.6,
        "crossing": 4.3,
        "first_touch": 4.0,
        "strength": 3.6,
        "anticipation": 3.3,
        "technique": 3.2,
        "dribbling": 3.1,
        "off_the_ball": 2.6,
        "vision": 2.5,
        "passing": 2.4,
        "work_rate": 2.3,
    },
    "AMC": {
        "acceleration": 10.0,
        "pace": 8.2,
        "weak_foot": 7.8,
        "stamina": 5.7,
        "agility": 5.4,
        "decisions": 5.1,
        "vision": 5.0,
        "technique": 4.4,
        "first_touch": 4.3,
        "passing": 3.3,
        "anticipation": 3.3,
        "strength": 3.0,
        "dribbling": 2.9,
        "off_the_ball": 2.7,
        "composure": 2.6,
        "finishing": 2.5,
    },
    "AML_AMR": {
        "acceleration": 10.0,
        "pace": 9.8,
        "agility": 6.1,
        "stamina": 5.9,
        "weak_foot": 5.5,
        "decisions": 4.4,
        "first_touch": 4.0,
        "crossing": 3.8,
        "dribbling": 3.8,
        "strength": 3.2,
        "anticipation": 2.9,
        "technique": 2.5,
        "concentration": 2.4,
        "off_the_ball": 2.3,
        "finishing": 2.2,
        "passing": 2.1,
    },
    "STC": {
        "acceleration": 10.0,
        "weak_foot": 7.7,
        "finishing": 7.5,
        "pace": 6.6,
        "strength": 5.6,
        "off_the_ball": 5.4,
        "stamina": 5.2,
        "composure": 5.2,
        "agility": 5.2,
        "first_touch": 5.0,
        "heading": 4.8,
        "jumping_reach": 4.5,
        "anticipation": 4.0,
        "dribbling": 3.9,
        "decisions": 3.7,
        "technique": 3.3,
    },
}

ZERO_CA_COST_ATTRIBUTES: tuple[str, ...] = (
    "determination",
    "flair",
    "aggression",
    "natural_fitness",
    "leadership",
    "eccentricity",
)

# ---------------------------------------------------------------------------
# 2. TACTICAL ROLES: KEY ATTRIBUTES (x2.0) & PREFERABLE ATTRIBUTES (x1.0)
# ---------------------------------------------------------------------------
TACTICAL_ROLE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "sweeper_keeper": {
        "tr": "Libero Kaleci (Sweeper Keeper)",
        "pos": "gk",
        "key": ("reflexes", "rushing_out", "command_of_area", "kicking", "one_on_ones", "anticipation", "composure", "concentration", "decisions", "positioning", "agility"),
        "pref": ("aerial_reach", "communication", "first_touch", "handling", "passing", "throwing", "vision", "acceleration"),
    },
    "goalkeeper": {
        "tr": "Kaleci (Goalkeeper)",
        "pos": "gk",
        "key": ("aerial_reach", "command_of_area", "communication", "handling", "kicking", "reflexes", "concentration", "positioning", "agility"),
        "pref": ("one_on_ones", "throwing", "anticipation", "decisions"),
    },
    "central_defender": {
        "tr": "Merkez Stoper (Central Defender)",
        "pos": "dc",
        "key": ("heading", "marking", "tackling", "positioning", "jumping_reach", "strength"),
        "pref": ("aggression", "anticipation", "bravery", "composure", "concentration", "decisions", "pace"),
    },
    "ball_playing_defender": {
        "tr": "Pasör Stoper (Ball-Playing Defender)",
        "pos": "dc",
        "key": ("heading", "marking", "passing", "tackling", "composure", "decisions", "positioning", "jumping_reach", "strength"),
        "pref": ("first_touch", "technique", "aggression", "anticipation", "bravery", "concentration", "vision", "pace"),
    },
    "full_back": {
        "tr": "Bek (Full-Back)",
        "pos": "dl",
        "key": ("marking", "tackling", "anticipation", "concentration", "positioning", "teamwork", "work_rate", "stamina"),
        "pref": ("crossing", "dribbling", "first_touch", "passing", "decisions", "off_the_ball", "acceleration", "agility", "pace"),
    },
    "wing_back": {
        "tr": "Kanat Bek (Wing-Back)",
        "pos": "wbl",
        "key": ("crossing", "dribbling", "marking", "tackling", "off_the_ball", "teamwork", "work_rate", "acceleration", "pace", "stamina"),
        "pref": ("first_touch", "passing", "technique", "anticipation", "concentration", "decisions", "positioning", "agility", "balance"),
    },
    "inverted_wing_back": {
        "tr": "Sahte Kanat Bek (Inverted Wing-Back)",
        "pos": "dl",
        "key": ("first_touch", "passing", "tackling", "decisions", "off_the_ball", "positioning", "teamwork", "work_rate", "stamina"),
        "pref": ("dribbling", "marking", "technique", "anticipation", "composure", "concentration", "vision", "acceleration", "agility"),
    },
    "ball_winning_midfielder": {
        "tr": "Savaşçı Orta Saha (Ball-Winning Midfielder)",
        "pos": "dm",
        "key": ("tackling", "aggression", "anticipation", "bravery", "teamwork", "work_rate", "stamina"),
        "pref": ("marking", "passing", "concentration", "decisions", "positioning", "agility", "pace", "strength"),
    },
    "deep_lying_playmaker": {
        "tr": "Derin Oyun Kurucu (Deep-Lying Playmaker)",
        "pos": "dm",
        "key": ("first_touch", "passing", "technique", "composure", "decisions", "teamwork", "vision"),
        "pref": ("tackling", "anticipation", "off_the_ball", "positioning", "balance"),
    },
    "box_to_box_midfielder": {
        "tr": "İki Yönlü Orta Saha (Box-to-Box Midfielder)",
        "pos": "mc",
        "key": ("passing", "tackling", "off_the_ball", "teamwork", "work_rate", "stamina"),
        "pref": ("dribbling", "finishing", "first_touch", "long_shots", "technique", "aggression", "anticipation", "composure", "decisions", "positioning", "acceleration", "balance", "pace", "strength"),
    },
    "mezzala": {
        "tr": "Mezzala (Yarı Kanat Orta Saha)",
        "pos": "mc",
        "key": ("dribbling", "passing", "technique", "decisions", "off_the_ball", "vision", "work_rate", "acceleration"),
        "pref": ("crossing", "finishing", "first_touch", "long_shots", "anticipation", "composure", "flair", "agility", "balance", "pace", "stamina"),
    },
    "advanced_playmaker": {
        "tr": "Ofansif Oyun Kurucu (Advanced Playmaker)",
        "pos": "amc",
        "key": ("first_touch", "passing", "technique", "composure", "decisions", "off_the_ball", "teamwork", "vision"),
        "pref": ("dribbling", "anticipation", "flair", "agility"),
    },
    "shadow_striker": {
        "tr": "Gizli Forvet (Shadow Striker)",
        "pos": "amc",
        "key": ("dribbling", "finishing", "first_touch", "anticipation", "composure", "off_the_ball", "acceleration"),
        "pref": ("passing", "technique", "concentration", "decisions", "work_rate", "agility", "balance", "pace", "stamina"),
    },
    "winger": {
        "tr": "Kanat Oyuncusu (Winger)",
        "pos": "aml",
        "key": ("crossing", "dribbling", "technique", "off_the_ball", "acceleration", "pace"),
        "pref": ("first_touch", "passing", "work_rate", "agility", "balance", "stamina"),
    },
    "inside_forward": {
        "tr": "İçe Kat Eden Forvet (Inside Forward)",
        "pos": "aml",
        "key": ("dribbling", "finishing", "first_touch", "technique", "off_the_ball", "acceleration", "agility", "pace"),
        "pref": ("long_shots", "passing", "anticipation", "composure", "flair", "vision", "balance", "stamina"),
    },
    "inverted_winger": {
        "tr": "Ters Ayaklı Kanat (Inverted Winger)",
        "pos": "aml",
        "key": ("crossing", "dribbling", "passing", "technique", "off_the_ball", "acceleration", "agility"),
        "pref": ("first_touch", "long_shots", "composure", "decisions", "flair", "vision", "work_rate", "balance", "pace", "stamina"),
    },
    "advanced_forward": {
        "tr": "Yaratıcı / İleri Uç Forvet (Advanced Forward)",
        "pos": "stc",
        "key": ("dribbling", "finishing", "first_touch", "technique", "composure", "off_the_ball", "acceleration"),
        "pref": ("passing", "anticipation", "decisions", "work_rate", "agility", "balance", "pace", "stamina"),
    },
    "poacher": {
        "tr": "Fırsatçı Golcü (Poacher)",
        "pos": "stc",
        "key": ("finishing", "first_touch", "anticipation", "composure", "off_the_ball"),
        "pref": ("heading", "technique", "decisions", "acceleration", "agility", "balance"),
    },
    "target_forward": {
        "tr": "Pivot Santrfor (Target Forward)",
        "pos": "stc",
        "key": ("heading", "bravery", "teamwork", "jumping_reach", "strength"),
        "pref": ("finishing", "first_touch", "aggression", "anticipation", "composure", "decisions", "off_the_ball", "balance"),
    },
    "pressing_forward": {
        "tr": "Çalışkan / Presçi Forvet (Pressing Forward)",
        "pos": "stc",
        "key": ("aggression", "anticipation", "bravery", "decisions", "teamwork", "work_rate", "acceleration", "pace", "stamina"),
        "pref": ("finishing", "first_touch", "composure", "concentration", "off_the_ball", "agility", "balance", "strength"),
    },
    "complete_forward": {
        "tr": "Komple Forvet (Complete Forward)",
        "pos": "stc",
        "pos_line": "STC",
        "archetype": "Scorer",
        "duties": ("Support", "Attack"),
        "foot_pref": "either",
        "key": ("dribbling", "finishing", "first_touch", "heading", "long_shots", "passing", "technique", "anticipation", "composure", "decisions", "off_the_ball", "vision", "acceleration", "agility", "jumping_reach", "pace", "strength"),
        "pref": ("teamwork", "work_rate", "balance", "stamina"),
    },
    # --- Expanded FM26 In-Possession Roles ---
    "no_nonsense_goalkeeper": {
        "tr": "Garantici Kaleci (No-Nonsense Goalkeeper)",
        "pos": "gk",
        "pos_line": "GK",
        "archetype": "Traditional_GK",
        "duties": ("Defend",),
        "foot_pref": "either",
        "key": ("aerial_reach", "command_of_area", "communication", "handling", "kicking", "reflexes", "concentration", "positioning"),
        "pref": ("one_on_ones", "strength", "agility", "bravery", "decisions"),
    },
    "no_nonsense_centre_back": {
        "tr": "Garantici Stoper (No-Nonsense Centre-Back)",
        "pos": "dc",
        "pos_line": "DC",
        "archetype": "Destroyer_Stopper",
        "duties": ("Defend", "Stopper", "Cover"),
        "foot_pref": "either",
        "key": ("heading", "marking", "tackling", "bravery", "positioning", "jumping_reach", "strength"),
        "pref": ("aggression", "anticipation", "concentration", "pace"),
    },
    "wide_centre_back": {
        "tr": "Kenar Stoper (Wide Centre-Back)",
        "pos": "dc",
        "pos_line": "DC",
        "archetype": "BoxToBox_Engine",
        "duties": ("Defend", "Support", "Attack"),
        "foot_pref": "same_side",
        "key": ("heading", "marking", "tackling", "positioning", "jumping_reach", "pace", "stamina", "strength"),
        "pref": ("crossing", "dribbling", "passing", "aggression", "anticipation", "bravery", "composure", "decisions", "off_the_ball", "work_rate", "acceleration", "agility"),
    },
    "overlapping_centre_back": {
        "tr": "Bindiren Stoper (Overlapping Centre-Back)",
        "pos": "dc",
        "pos_line": "DC",
        "archetype": "Wide_Byline",
        "duties": ("Support", "Attack"),
        "foot_pref": "same_side",
        "key": ("crossing", "dribbling", "marking", "passing", "tackling", "off_the_ball", "positioning", "work_rate", "acceleration", "pace", "stamina"),
        "pref": ("first_touch", "heading", "technique", "anticipation", "composure", "decisions", "teamwork", "jumping_reach", "strength"),
    },
    "libero": {
        "tr": "Libero (Oyun Kuran Stoper)",
        "pos": "dc",
        "pos_line": "DC",
        "archetype": "Playmaker",
        "duties": ("Support", "Attack"),
        "foot_pref": "either",
        "key": ("dribbling", "first_touch", "marking", "passing", "tackling", "technique", "composure", "decisions", "positioning", "teamwork", "vision", "acceleration", "agility"),
        "pref": ("heading", "long_shots", "anticipation", "bravery", "concentration", "flair", "balance", "jumping_reach", "pace", "stamina", "strength"),
    },
    "no_nonsense_full_back": {
        "tr": "Çakılı / Garantici Bek (No-Nonsense Full-Back)",
        "pos": "dl",
        "pos_line": "FB",
        "archetype": "Destroyer_Stopper",
        "duties": ("Defend",),
        "foot_pref": "same_side",
        "key": ("marking", "tackling", "anticipation", "bravery", "concentration", "positioning", "teamwork", "strength"),
        "pref": ("heading", "aggression", "decisions", "work_rate", "acceleration", "pace", "stamina"),
    },
    "inverted_full_back": {
        "tr": "Stoperleşen Bek (Inverted Full-Back)",
        "pos": "dl",
        "pos_line": "FB",
        "archetype": "Cover_Holding",
        "duties": ("Defend",),
        "foot_pref": "same_side",
        "key": ("heading", "marking", "tackling", "positioning", "jumping_reach", "strength"),
        "pref": ("first_touch", "passing", "aggression", "anticipation", "bravery", "composure", "concentration", "decisions", "acceleration", "agility", "pace"),
    },
    "playmaking_wing_back": {
        "tr": "Oyun Kurucu Kanat Bek (Playmaking Wing-Back)",
        "pos": "wbl",
        "pos_line": "WB",
        "archetype": "Playmaker",
        "duties": ("Support", "Attack"),
        "foot_pref": "either",
        "key": ("first_touch", "passing", "tackling", "technique", "composure", "decisions", "off_the_ball", "teamwork", "vision", "work_rate", "stamina"),
        "pref": ("crossing", "dribbling", "marking", "anticipation", "concentration", "flair", "positioning", "acceleration", "agility", "balance"),
    },
    "advanced_wing_back": {
        "tr": "Hücumcu Kanat Bek (Advanced Wing-Back)",
        "pos": "wbl",
        "pos_line": "WB",
        "archetype": "Wide_Byline",
        "duties": ("Attack",),
        "foot_pref": "same_side",
        "key": ("crossing", "dribbling", "first_touch", "technique", "flair", "off_the_ball", "work_rate", "acceleration", "agility", "pace", "stamina"),
        "pref": ("marking", "passing", "tackling", "anticipation", "composure", "decisions", "positioning", "teamwork", "balance"),
    },
    "defensive_midfielder": {
        "tr": "Defansif Orta Saha (Defensive Midfielder)",
        "pos": "dm",
        "pos_line": "DM",
        "archetype": "Cover_Holding",
        "duties": ("Defend", "Support"),
        "foot_pref": "either",
        "key": ("tackling", "anticipation", "concentration", "positioning", "teamwork"),
        "pref": ("first_touch", "marking", "passing", "aggression", "composure", "decisions", "work_rate", "stamina", "strength"),
    },
    "anchor_man": {
        "tr": "Çapa / Ön Libero (Anchor Man)",
        "pos": "dm",
        "pos_line": "DM",
        "archetype": "Cover_Holding",
        "duties": ("Defend",),
        "foot_pref": "either",
        "key": ("marking", "tackling", "anticipation", "Composure" if False else "composure", "concentration", "decisions", "positioning"),
        "pref": ("passing", "teamwork", "strength"),
    },
    "half_back": {
        "tr": "Gizli Libero (Half-Back)",
        "pos": "dm",
        "pos_line": "DM",
        "archetype": "Cover_Holding",
        "duties": ("Defend",),
        "foot_pref": "either",
        "key": ("marking", "passing", "tackling", "anticipation", "composure", "concentration", "decisions", "positioning", "teamwork"),
        "pref": ("first_touch", "heading", "aggression", "bravery", "work_rate", "jumping_reach", "stamina", "strength"),
    },
    "regista": {
        "tr": "Regista (Serbest Derin Oyun Kurucu)",
        "pos": "dm",
        "pos_line": "DM",
        "archetype": "Playmaker",
        "duties": ("Support",),
        "foot_pref": "either",
        "key": ("first_touch", "passing", "technique", "composure", "decisions", "flair", "off_the_ball", "teamwork", "vision"),
        "pref": ("dribbling", "long_shots", "anticipation", "balance", "agility"),
    },
    "segundo_volante": {
        "tr": "Segundo Volante (Hücumcu Ön Libero)",
        "pos": "dm",
        "pos_line": "DM",
        "archetype": "BoxToBox_Engine",
        "duties": ("Support", "Attack"),
        "foot_pref": "either",
        "key": ("finishing", "long_shots", "marking", "passing", "tackling", "anticipation", "off_the_ball", "positioning", "work_rate", "pace", "stamina"),
        "pref": ("first_touch", "composure", "concentration", "decisions", "acceleration", "balance", "strength"),
    },
    "central_midfielder": {
        "tr": "Merkez Orta Saha (Central Midfielder)",
        "pos": "mc",
        "pos_line": "MC",
        "archetype": "BoxToBox_Engine",
        "duties": ("Defend", "Support", "Attack"),
        "foot_pref": "either",
        "key": ("first_touch", "passing", "tackling", "decisions", "teamwork"),
        "pref": ("technique", "anticipation", "composure", "concentration", "off_the_ball", "vision", "work_rate", "stamina"),
    },
    "box_to_box_playmaker": {
        "tr": "Gezgin Oyun Kurucu (Roaming / Box-to-Box Playmaker)",
        "pos": "mc",
        "pos_line": "MC",
        "archetype": "Playmaker",
        "duties": ("Support",),
        "foot_pref": "either",
        "key": ("dribbling", "first_touch", "passing", "technique", "anticipation", "composure", "decisions", "off_the_ball", "teamwork", "vision", "work_rate", "acceleration", "stamina"),
        "pref": ("long_shots", "marking", "tackling", "concentration", "positioning", "agility", "balance", "pace"),
    },
    "wide_central_midfielder": {
        "tr": "Carrilero / Kenar Merkez Orta Saha (Wide Central Midfielder)",
        "pos": "mc",
        "pos_line": "MC",
        "archetype": "Cover_Holding",
        "duties": ("Support",),
        "foot_pref": "either",
        "key": ("first_touch", "passing", "tackling", "decisions", "positioning", "teamwork", "work_rate", "stamina"),
        "pref": ("technique", "anticipation", "composure", "concentration", "off_the_ball", "vision", "acceleration", "pace"),
    },
    "channel_midfielder": {
        "tr": "Koridor Orta Sahası (Channel Midfielder)",
        "pos": "amc",
        "pos_line": "AMC",
        "archetype": "BoxToBox_Engine",
        "duties": ("Support", "Attack"),
        "foot_pref": "either",
        "key": ("dribbling", "first_touch", "passing", "technique", "anticipation", "decisions", "off_the_ball", "vision", "work_rate", "acceleration", "pace", "stamina"),
        "pref": ("crossing", "finishing", "composure", "flair", "teamwork", "agility", "balance"),
    },
    "attacking_midfielder": {
        "tr": "Ofansif Orta Saha (Attacking Midfielder)",
        "pos": "amc",
        "pos_line": "AMC",
        "archetype": "Playmaker",
        "duties": ("Support", "Attack"),
        "foot_pref": "either",
        "key": ("dribbling", "first_touch", "long_shots", "passing", "technique", "anticipation", "decisions", "flair", "off_the_ball", "vision"),
        "pref": ("finishing", "composure", "agility"),
    },
    "enganche": {
        "tr": "Enganche (Sabit Kanca Oyun Kurucu)",
        "pos": "amc",
        "pos_line": "AMC",
        "archetype": "Playmaker",
        "duties": ("Support",),
        "foot_pref": "either",
        "key": ("first_touch", "passing", "technique", "composure", "decisions", "vision"),
        "pref": ("dribbling", "anticipation", "flair", "off_the_ball", "teamwork", "agility", "balance"),
    },
    "trequartista": {
        "tr": "Trequartista (Serbest 10 Numara / Hücum Kurucu)",
        "pos": "amc",
        "pos_line": "AMC",
        "archetype": "Playmaker",
        "duties": ("Attack", "Float"),
        "foot_pref": "either",
        "key": ("dribbling", "first_touch", "passing", "technique", "composure", "decisions", "flair", "off_the_ball", "vision", "acceleration"),
        "pref": ("finishing", "anticipation", "agility", "balance"),
    },
    "wide_midfielder": {
        "tr": "Kanat Orta Saha (Wide Midfielder)",
        "pos": "ml",
        "pos_line": "WM",
        "archetype": "BoxToBox_Engine",
        "duties": ("Defend", "Support", "Attack"),
        "foot_pref": "same_side",
        "key": ("crossing", "passing", "tackling", "decisions", "teamwork", "work_rate", "stamina"),
        "pref": ("dribbling", "first_touch", "technique", "anticipation", "composure", "concentration", "off_the_ball", "positioning", "vision", "acceleration", "pace"),
    },
    "wide_playmaker": {
        "tr": "Kanat Oyun Kurucu (Wide Playmaker)",
        "pos": "ml",
        "pos_line": "WM",
        "archetype": "Playmaker",
        "duties": ("Support", "Attack"),
        "foot_pref": "inverted",
        "key": ("dribbling", "first_touch", "passing", "technique", "composure", "decisions", "off_the_ball", "teamwork", "vision"),
        "pref": ("flair", "agility", "acceleration"),
    },
    "defensive_winger": {
        "tr": "Defansif Kanat (Defensive Winger)",
        "pos": "aml",
        "pos_line": "WINGER",
        "archetype": "Pressing_Harrier",
        "duties": ("Defend", "Support"),
        "foot_pref": "same_side",
        "key": ("crossing", "dribbling", "marking", "tackling", "aggression", "anticipation", "off_the_ball", "positioning", "teamwork", "work_rate", "acceleration", "stamina"),
        "pref": ("first_touch", "passing", "technique", "bravery", "concentration", "decisions", "agility", "pace"),
    },
    "wide_target_man": {
        "tr": "Kanat Pivot (Wide Target Forward)",
        "pos": "aml",
        "pos_line": "WINGER",
        "archetype": "Target_Outlet",
        "duties": ("Support", "Attack"),
        "foot_pref": "either",
        "key": ("heading", "bravery", "off_the_ball", "teamwork", "work_rate", "jumping_reach", "strength"),
        "pref": ("crossing", "finishing", "first_touch", "passing", "anticipation", "decisions", "balance", "stamina"),
    },
    "wide_forward": {
        "tr": "Raumdeuter / Gezgin Kanat Forvet (Wide Forward)",
        "pos": "aml",
        "pos_line": "WINGER",
        "archetype": "Scorer",
        "duties": ("Attack",),
        "foot_pref": "either",
        "key": ("finishing", "first_touch", "anticipation", "composure", "concentration", "decisions", "off_the_ball", "balance"),
        "pref": ("technique", "work_rate", "acceleration", "agility", "stamina"),
    },
    "deep_lying_forward": {
        "tr": "Derin Forvet (Deep-Lying Forward)",
        "pos": "stc",
        "pos_line": "STC",
        "archetype": "Target_Outlet",
        "duties": ("Support", "Attack"),
        "foot_pref": "either",
        "key": ("first_touch", "passing", "technique", "composure", "decisions", "off_the_ball", "teamwork"),
        "pref": ("dribbling", "finishing", "anticipation", "flair", "vision", "balance", "strength"),
    },
    "false_nine": {
        "tr": "Sahte Dokuz (False Nine)",
        "pos": "stc",
        "pos_line": "STC",
        "archetype": "Playmaker",
        "duties": ("Support",),
        "foot_pref": "either",
        "key": ("dribbling", "first_touch", "passing", "technique", "composure", "decisions", "off_the_ball", "teamwork", "vision", "acceleration", "agility"),
        "pref": ("finishing", "anticipation", "flair", "balance"),
    },
    "channel_forward": {
        "tr": "Koridor Forveti (Channel Forward)",
        "pos": "stc",
        "pos_line": "STC",
        "archetype": "Scorer",
        "duties": ("Attack",),
        "foot_pref": "either",
        "key": ("dribbling", "finishing", "first_touch", "anticipation", "composure", "off_the_ball", "work_rate", "acceleration", "pace", "stamina"),
        "pref": ("crossing", "passing", "technique", "decisions", "teamwork", "agility", "balance"),
    },
}

# Backfill metadata (pos_line, archetype, duties, foot_pref) onto initial 21 roles
_INITIAL_ROLE_METADATA: dict[str, dict[str, Any]] = {
    "sweeper_keeper": {"pos_line": "GK", "archetype": "Sweeper_ModernGK", "duties": ("Defend", "Support", "Attack"), "foot_pref": "either"},
    "goalkeeper": {"pos_line": "GK", "archetype": "Traditional_GK", "duties": ("Defend",), "foot_pref": "either"},
    "central_defender": {"pos_line": "DC", "archetype": "Destroyer_Stopper", "duties": ("Defend", "Stopper", "Cover"), "foot_pref": "either"},
    "ball_playing_defender": {"pos_line": "DC", "archetype": "Playmaker", "duties": ("Defend", "Stopper", "Cover"), "foot_pref": "either"},
    "full_back": {"pos_line": "FB", "archetype": "Cover_Holding", "duties": ("Defend", "Support", "Attack"), "foot_pref": "same_side"},
    "wing_back": {"pos_line": "WB", "archetype": "Wide_Byline", "duties": ("Defend", "Support", "Attack"), "foot_pref": "same_side"},
    "inverted_wing_back": {"pos_line": "FB", "archetype": "Inverted_Inside", "duties": ("Defend", "Support", "Attack"), "foot_pref": "inverted"},
    "ball_winning_midfielder": {"pos_line": "DM", "archetype": "Destroyer_Stopper", "duties": ("Defend", "Support"), "foot_pref": "either"},
    "deep_lying_playmaker": {"pos_line": "DM", "archetype": "Playmaker", "duties": ("Defend", "Support"), "foot_pref": "either"},
    "box_to_box_midfielder": {"pos_line": "MC", "archetype": "BoxToBox_Engine", "duties": ("Support",), "foot_pref": "either"},
    "mezzala": {"pos_line": "MC", "archetype": "Inverted_Inside", "duties": ("Support", "Attack"), "foot_pref": "either"},
    "advanced_playmaker": {"pos_line": "AMC", "archetype": "Playmaker", "duties": ("Support", "Attack"), "foot_pref": "either"},
    "shadow_striker": {"pos_line": "AMC", "archetype": "Scorer", "duties": ("Attack",), "foot_pref": "either"},
    "winger": {"pos_line": "WINGER", "archetype": "Wide_Byline", "duties": ("Support", "Attack"), "foot_pref": "same_side"},
    "inside_forward": {"pos_line": "WINGER", "archetype": "Inverted_Inside", "duties": ("Support", "Attack"), "foot_pref": "inverted"},
    "inverted_winger": {"pos_line": "WINGER", "archetype": "Inverted_Inside", "duties": ("Support", "Attack"), "foot_pref": "inverted"},
    "advanced_forward": {"pos_line": "STC", "archetype": "Scorer", "duties": ("Attack",), "foot_pref": "either"},
    "poacher": {"pos_line": "STC", "archetype": "Scorer", "duties": ("Attack",), "foot_pref": "either"},
    "target_forward": {"pos_line": "STC", "archetype": "Target_Outlet", "duties": ("Support", "Attack"), "foot_pref": "either"},
    "pressing_forward": {"pos_line": "STC", "archetype": "Pressing_Harrier", "duties": ("Defend", "Support", "Attack"), "foot_pref": "either"},
}
for _rk, _rmeta in _INITIAL_ROLE_METADATA.items():
    if _rk in TACTICAL_ROLE_DEFINITIONS:
        TACTICAL_ROLE_DEFINITIONS[_rk].update(_rmeta)

# ---------------------------------------------------------------------------
# 2B. ATTRIBUTE CATEGORIES, DUTY MODIFIERS & OUT-OF-POSSESSION (OP*) CATALOG
# ---------------------------------------------------------------------------
ATTRIBUTE_CATEGORIES: dict[str, tuple[str, ...]] = {
    "goalkeeping": (
        "aerial_reach", "command_of_area", "communication", "eccentricity",
        "handling", "kicking", "one_on_ones", "punching", "reflexes",
        "rushing_out", "throwing",
    ),
    "technical": (
        "corners", "crossing", "dribbling", "finishing", "first_touch",
        "free_kicks", "heading", "long_shots", "long_throws", "marking",
        "passing", "penalty_taking", "tackling", "technique",
    ),
    "mental": (
        "aggression", "anticipation", "bravery", "composure", "concentration",
        "decisions", "determination", "flair", "leadership", "off_the_ball",
        "positioning", "teamwork", "vision", "work_rate",
    ),
    "physical": (
        "acceleration", "agility", "balance", "jumping_reach",
        "natural_fitness", "pace", "stamina", "strength",
    ),
}

ROLE_ARCHETYPES: dict[str, dict[str, str]] = {
    "Playmaker": {"tr": "Oyun Kurucu (Playmaker)", "focus": "Pas, Vizyon, İlk Kontrol, Soğukkanlılık ve Karar Alma"},
    "Scorer": {"tr": "Bitirici / Golcü (Scorer)", "focus": "Bitiricilik, Topsız Alan, Ön Sezi ve Hızlanma"},
    "Destroyer_Stopper": {"tr": "Kesici / Durdurucu (Destroyer / Stopper)", "focus": "Top Kapma, Cesaret, Agresiflik, Güç ve Hava Hakimiyeti"},
    "Cover_Holding": {"tr": "Alan Kapatıcı / Sigorta (Cover / Holding)", "focus": "Pozisyon Alma, Konsantrasyon, Ön Sezi, Markaj ve Hız"},
    "BoxToBox_Engine": {"tr": "İki Yönlü Dinamo (Box-to-Box Engine)", "focus": "Çalışkanlık, Dayanıklılık, Takım Oyunu ve Çift Yönlü Katkı"},
    "Wide_Byline": {"tr": "Çizgi / Kanat Bindirici (Wide / Byline)", "focus": "Orta Yapma, Dripling, Hız, Hızlanma ve Dayanıklılık"},
    "Inverted_Inside": {"tr": "İçe Kat Eden / Ters Ayaklı (Inverted / Inside)", "focus": "Dripling, Teknik, Çeviklik, Vizyon ve Uzaktan/İçeriden Şut"},
    "Target_Outlet": {"tr": "Pivot / Bağlantı İstasyonu (Target / Outlet)", "focus": "Güç, Zıplama, Kafa Vuruşu, İlk Kontrol ve Sırtı Dönük Oyun"},
    "Pressing_Harrier": {"tr": "Şok Presçi / Çalışkan (Pressing / Harrier)", "focus": "Çalışkanlık, Agresiflik, Hızlanma, Cesaret ve Takım Oyunu"},
    "Sweeper_ModernGK": {"tr": "Modern Libero Kaleci (Sweeper GK)", "focus": "Ani Çıkış, Refleks, Ayak Kalitesi ve Ön Sezi"},
    "Traditional_GK": {"tr": "Geleneksel Çizgi Kalecisi (Line GK)", "focus": "Elle Kontrol, Hava Hakimiyeti, Refleks ve Pozisyon Alma"},
}

DUTY_ATTRIBUTE_DELTAS: dict[str, dict[str, tuple[str, ...]]] = {
    "Defend": {
        "promote_to_key": ("positioning", "concentration", "marking"),
        "add_to_pref": ("tackling", "anticipation"),
    },
    "Stopper": {
        "promote_to_key": ("aggression", "bravery", "decisions", "strength"),
        "add_to_pref": ("heading", "jumping_reach"),
    },
    "Cover": {
        "promote_to_key": ("anticipation", "decisions", "pace", "acceleration"),
        "add_to_pref": ("concentration", "positioning"),
    },
    "Support": {
        "promote_to_key": ("teamwork", "decisions", "passing"),
        "add_to_pref": ("first_touch", "work_rate", "stamina"),
    },
    "Attack": {
        "promote_to_key": ("off_the_ball", "dribbling", "acceleration"),
        "add_to_pref": ("finishing", "flair", "composure", "pace"),
    },
    "Float": {
        "promote_to_key": ("off_the_ball", "vision", "flair", "decisions"),
        "add_to_pref": ("composure", "agility", "first_touch"),
    },
}

# All 33 Official FM26 Out-Of-Possession (OP*) Roles from global-metadata.dat & oop_attributes_scoring.jsb
OUT_OF_POSSESSION_ROLE_CATALOG: dict[str, dict[str, Any]] = {
    "OPGoalkeeper": {
        "tr": "Topsuz: Standart Kaleci (OP Goalkeeper)",
        "pos": "gk", "pos_line": "GK", "oop_style": "Standard_Shape",
        "key": ("handling", "reflexes", "command_of_area", "positioning", "concentration"),
        "pref": ("aerial_reach", "communication", "decisions", "agility"),
    },
    "OPSweeperKeeper": {
        "tr": "Topsuz: Süpürücü Libero Kaleci (OP Sweeper Keeper)",
        "pos": "gk", "pos_line": "GK", "oop_style": "Cover_Sweeper",
        "key": ("rushing_out", "one_on_ones", "anticipation", "decisions", "acceleration", "pace", "positioning"),
        "pref": ("reflexes", "command_of_area", "composure", "concentration", "agility"),
    },
    "OPLineKeeper": {
        "tr": "Topsuz: Çizgi Kalecisi (OP Line Keeper)",
        "pos": "gk", "pos_line": "GK", "oop_style": "Screening_Holding",
        "key": ("reflexes", "handling", "aerial_reach", "positioning", "concentration", "agility"),
        "pref": ("command_of_area", "communication", "bravery", "strength"),
    },
    "OPCentreBack": {
        "tr": "Topsuz: Dengeli Stoper (OP Centre-Back)",
        "pos": "dc", "pos_line": "DC", "oop_style": "Standard_Shape",
        "key": ("marking", "tackling", "heading", "positioning", "jumping_reach", "strength"),
        "pref": ("anticipation", "bravery", "concentration", "decisions", "pace"),
    },
    "OPStoppingCentreBack": {
        "tr": "Topsuz: Kesici / Basan Stoper (OP Stopping Centre-Back)",
        "pos": "dc", "pos_line": "DC", "oop_style": "Stopper_Aggressive",
        "key": ("tackling", "heading", "aggression", "bravery", "decisions", "jumping_reach", "strength"),
        "pref": ("marking", "anticipation", "concentration", "positioning", "acceleration"),
    },
    "OPCoveringCentreBack": {
        "tr": "Topsuz: Kademe / Süpürücü Stoper (OP Covering Centre-Back)",
        "pos": "dc", "pos_line": "DC", "oop_style": "Cover_Sweeper",
        "key": ("marking", "tackling", "anticipation", "concentration", "decisions", "positioning", "acceleration", "pace"),
        "pref": ("heading", "composure", "agility", "jumping_reach"),
    },
    "OPWideCentreBack": {
        "tr": "Topsuz: Kenar Stoper (OP Wide Centre-Back)",
        "pos": "dc", "pos_line": "DC", "oop_style": "Wide_Cover_Tracking",
        "key": ("marking", "tackling", "positioning", "acceleration", "pace", "stamina", "strength"),
        "pref": ("heading", "anticipation", "concentration", "decisions", "work_rate", "agility", "jumping_reach"),
    },
    "OPStoppingWideCentreBack": {
        "tr": "Topsuz: Basan Kenar Stoper (OP Stopping Wide Centre-Back)",
        "pos": "dc", "pos_line": "DC", "oop_style": "Stopper_Aggressive",
        "key": ("marking", "tackling", "aggression", "bravery", "decisions", "acceleration", "strength"),
        "pref": ("heading", "anticipation", "positioning", "work_rate", "jumping_reach", "pace"),
    },
    "OPCoveringWideCentreBack": {
        "tr": "Topsuz: Kademeci Kenar Stoper (OP Covering Wide Centre-Back)",
        "pos": "dc", "pos_line": "DC", "oop_style": "Cover_Sweeper",
        "key": ("marking", "tackling", "anticipation", "concentration", "decisions", "positioning", "acceleration", "pace"),
        "pref": ("agility", "stamina", "strength", "work_rate"),
    },
    "OPFullBack": {
        "tr": "Topsuz: Standart Bek (OP Full-Back)",
        "pos": "dl", "pos_line": "FB", "oop_style": "Standard_Shape",
        "key": ("marking", "tackling", "anticipation", "concentration", "positioning", "teamwork", "stamina"),
        "pref": ("decisions", "work_rate", "acceleration", "agility", "pace", "strength"),
    },
    "OPPressingFullBack": {
        "tr": "Topsuz: Presçi Bek (OP Pressing Full-Back)",
        "pos": "dl", "pos_line": "FB", "oop_style": "High_Pressing",
        "key": ("tackling", "aggression", "anticipation", "bravery", "work_rate", "acceleration", "pace", "stamina"),
        "pref": ("marking", "concentration", "decisions", "positioning", "teamwork", "agility", "strength"),
    },
    "OPHoldingFullBack": {
        "tr": "Topsuz: Çakılı / Daralan Bek (OP Holding Full-Back)",
        "pos": "dl", "pos_line": "FB", "oop_style": "Screening_Holding",
        "key": ("marking", "tackling", "anticipation", "concentration", "decisions", "positioning", "strength"),
        "pref": ("heading", "bravery", "teamwork", "jumping_reach", "pace"),
    },
    "OPWingBack": {
        "tr": "Topsuz: Standart Kanat Bek (OP Wing-Back)",
        "pos": "wbl", "pos_line": "WB", "oop_style": "Wide_Cover_Tracking",
        "key": ("marking", "tackling", "positioning", "teamwork", "work_rate", "acceleration", "pace", "stamina"),
        "pref": ("anticipation", "concentration", "decisions", "agility"),
    },
    "OPPressingWingBack": {
        "tr": "Topsuz: Önde Basan Kanat Bek (OP Pressing Wing-Back)",
        "pos": "wbl", "pos_line": "WB", "oop_style": "High_Pressing",
        "key": ("tackling", "aggression", "anticipation", "bravery", "teamwork", "work_rate", "acceleration", "pace", "stamina"),
        "pref": ("marking", "decisions", "positioning", "agility", "strength"),
    },
    "OPHoldingWingBack": {
        "tr": "Topsuz: Geri Çekilen Kanat Bek (OP Holding Wing-Back)",
        "pos": "wbl", "pos_line": "WB", "oop_style": "Screening_Holding",
        "key": ("marking", "tackling", "anticipation", "concentration", "positioning", "teamwork", "stamina"),
        "pref": ("decisions", "work_rate", "acceleration", "pace", "strength"),
    },
    "OPDefensiveMidfielder": {
        "tr": "Topsuz: Dengeli Ön Libero (OP Defensive Midfielder)",
        "pos": "dm", "pos_line": "DM", "oop_style": "Standard_Shape",
        "key": ("marking", "tackling", "anticipation", "concentration", "positioning", "teamwork"),
        "pref": ("aggression", "decisions", "work_rate", "stamina", "strength"),
    },
    "OPDroppingDefensiveMidfielder": {
        "tr": "Topsuz: Stoperlerin Arasına Giren Ön Libero (OP Dropping DM)",
        "pos": "dm", "pos_line": "DM", "oop_style": "Cover_Sweeper",
        "key": ("heading", "marking", "tackling", "anticipation", "concentration", "decisions", "positioning", "jumping_reach", "strength"),
        "pref": ("bravery", "composure", "teamwork", "pace"),
    },
    "OPPressingDefensiveMidfielder": {
        "tr": "Topsuz: Şok Presçi Ön Libero (OP Pressing DM)",
        "pos": "dm", "pos_line": "DM", "oop_style": "High_Pressing",
        "key": ("tackling", "aggression", "anticipation", "bravery", "teamwork", "work_rate", "acceleration", "stamina"),
        "pref": ("marking", "concentration", "decisions", "positioning", "agility", "pace", "strength"),
    },
    "OPScreeningDefensiveMidfielder": {
        "tr": "Topsuz: Pas Kanallarını Kapatan Ön Libero (OP Screening DM)",
        "pos": "dm", "pos_line": "DM", "oop_style": "Screening_Holding",
        "key": ("marking", "anticipation", "concentration", "decisions", "positioning", "teamwork"),
        "pref": ("tackling", "composure", "work_rate", "agility", "stamina"),
    },
    "OPWideCoverDefensiveMidfielder": {
        "tr": "Topsuz: Kanat Kademesine Giren Ön Libero (OP Wide Cover DM)",
        "pos": "dm", "pos_line": "DM", "oop_style": "Wide_Cover_Tracking",
        "key": ("marking", "tackling", "anticipation", "positioning", "teamwork", "work_rate", "acceleration", "pace", "stamina"),
        "pref": ("concentration", "decisions", "agility", "strength"),
    },
    "OPCentralMidfielder": {
        "tr": "Topsuz: Dengeli Merkez Orta Saha (OP Central Midfielder)",
        "pos": "mc", "pos_line": "MC", "oop_style": "Standard_Shape",
        "key": ("tackling", "anticipation", "decisions", "positioning", "teamwork", "work_rate", "stamina"),
        "pref": ("marking", "aggression", "concentration", "acceleration", "pace", "strength"),
    },
    "OPPressingCentralMidfielder": {
        "tr": "Topsuz: Presçi Merkez Orta Saha (OP Pressing CM)",
        "pos": "mc", "pos_line": "MC", "oop_style": "High_Pressing",
        "key": ("tackling", "aggression", "anticipation", "bravery", "teamwork", "work_rate", "acceleration", "pace", "stamina"),
        "pref": ("marking", "decisions", "positioning", "agility", "strength"),
    },
    "OPScreeningCentralMidfielder": {
        "tr": "Topsuz: Alan Tutucu Merkez Orta Saha (OP Screening CM)",
        "pos": "mc", "pos_line": "MC", "oop_style": "Screening_Holding",
        "key": ("marking", "tackling", "anticipation", "concentration", "decisions", "positioning", "teamwork"),
        "pref": ("work_rate", "agility", "stamina", "strength"),
    },
    "OPWideCoverCentralMidfielder": {
        "tr": "Topsuz: Kanat Kapatıcı Merkez Orta Saha (OP Wide Cover CM)",
        "pos": "mc", "pos_line": "MC", "oop_style": "Wide_Cover_Tracking",
        "key": ("marking", "tackling", "positioning", "teamwork", "work_rate", "acceleration", "pace", "stamina"),
        "pref": ("anticipation", "concentration", "decisions", "agility"),
    },
    "OPAtackingMidfielder": {
        "tr": "Topsuz: Standart Ofansif Orta Saha (OP Attacking Midfielder)",
        "pos": "amc", "pos_line": "AMC", "oop_style": "Standard_Shape",
        "key": ("anticipation", "decisions", "teamwork", "work_rate", "acceleration", "stamina"),
        "pref": ("tackling", "aggression", "off_the_ball", "positioning", "agility", "pace"),
    },
    "OPTrackingAtackingMidfielder": {
        "tr": "Topsuz: Adam Takip Eden 10 Numara (OP Tracking AM)",
        "pos": "amc", "pos_line": "AMC", "oop_style": "Wide_Cover_Tracking",
        "key": ("marking", "tackling", "anticipation", "concentration", "positioning", "teamwork", "work_rate", "stamina"),
        "pref": ("aggression", "bravery", "decisions", "acceleration", "pace"),
    },
    "OPCentralOutletMidfielder": {
        "tr": "Topsuz: Merkez Kontra İstasyonu 10 Numara (OP Central Outlet AM)",
        "pos": "amc", "pos_line": "AMC", "oop_style": "Central_Counter_Outlet",
        "key": ("dribbling", "first_touch", "passing", "anticipation", "composure", "decisions", "off_the_ball", "vision", "acceleration", "pace"),
        "pref": ("technique", "flair", "agility", "balance"),
    },
    "OPSplittingOutletAtackingMidfielder": {
        "tr": "Topsuz: Koridorlara Kaçan Kontra 10 Numara (OP Splitting Outlet AM)",
        "pos": "amc", "pos_line": "AMC", "oop_style": "Splitting_Wide_Outlet",
        "key": ("dribbling", "first_touch", "anticipation", "off_the_ball", "acceleration", "agility", "pace"),
        "pref": ("passing", "technique", "composure", "decisions", "vision", "balance", "stamina"),
    },
    "OPWideMidfielder": {
        "tr": "Topsuz: Dengeli Kanat Orta Saha (OP Wide Midfielder)",
        "pos": "ml", "pos_line": "WM", "oop_style": "Standard_Shape",
        "key": ("marking", "tackling", "positioning", "teamwork", "work_rate", "stamina"),
        "pref": ("anticipation", "concentration", "decisions", "acceleration", "pace"),
    },
    "OPTrackingWideMidfielder": {
        "tr": "Topsuz: Bek Kovalayan Kanat Orta Saha (OP Tracking WM)",
        "pos": "ml", "pos_line": "WM", "oop_style": "Wide_Cover_Tracking",
        "key": ("marking", "tackling", "anticipation", "concentration", "positioning", "teamwork", "work_rate", "acceleration", "pace", "stamina"),
        "pref": ("aggression", "bravery", "decisions", "strength"),
    },
    "OPWideOutletWideMidfielder": {
        "tr": "Topsuz: Kanat Kontra İstasyonu (OP Wide Outlet WM)",
        "pos": "ml", "pos_line": "WM", "oop_style": "Splitting_Wide_Outlet",
        "key": ("crossing", "dribbling", "first_touch", "anticipation", "off_the_ball", "acceleration", "pace"),
        "pref": ("passing", "technique", "decisions", "agility", "balance", "stamina"),
    },
    "OPWinger": {
        "tr": "Topsuz: Standart Hücum Kanadı (OP Winger)",
        "pos": "aml", "pos_line": "WINGER", "oop_style": "Standard_Shape",
        "key": ("anticipation", "positioning", "teamwork", "work_rate", "acceleration", "pace", "stamina"),
        "pref": ("marking", "tackling", "aggression", "decisions", "off_the_ball", "agility"),
    },
    "OPTrackingWinger": {
        "tr": "Topsuz: Geri Yardıma Gelen Kanat (OP Tracking Winger)",
        "pos": "aml", "pos_line": "WINGER", "oop_style": "Wide_Cover_Tracking",
        "key": ("marking", "tackling", "anticipation", "concentration", "positioning", "teamwork", "work_rate", "acceleration", "pace", "stamina"),
        "pref": ("aggression", "bravery", "decisions", "agility"),
    },
    "OPInvertingOutletWinger": {
        "tr": "Topsuz: Merkeze Kaçan Kontra Kanat (OP Inverting Outlet Winger)",
        "pos": "aml", "pos_line": "WINGER", "oop_style": "Central_Counter_Outlet",
        "key": ("dribbling", "finishing", "first_touch", "technique", "anticipation", "composure", "off_the_ball", "acceleration", "agility", "pace"),
        "pref": ("passing", "decisions", "flair", "vision", "balance"),
    },
    "OPWideOutletWinger": {
        "tr": "Topsuz: Çizgide Bekleyen Kontra Kanat (OP Wide Outlet Winger)",
        "pos": "aml", "pos_line": "WINGER", "oop_style": "Splitting_Wide_Outlet",
        "key": ("crossing", "dribbling", "first_touch", "anticipation", "off_the_ball", "acceleration", "agility", "pace"),
        "pref": ("technique", "composure", "decisions", "flair", "balance"),
    },
    "OPCentreForward": {
        "tr": "Topsuz: Dengeli Santrfor (OP Centre Forward)",
        "pos": "stc", "pos_line": "STC", "oop_style": "Standard_Shape",
        "key": ("anticipation", "decisions", "teamwork", "work_rate", "acceleration", "pace", "stamina"),
        "pref": ("aggression", "bravery", "off_the_ball", "positioning", "strength"),
    },
    "OPTrackingCentreForward": {
        "tr": "Topsuz: Orta Sahaya Basan / Takipçi Santrfor (OP Tracking CF)",
        "pos": "stc", "pos_line": "STC", "oop_style": "High_Pressing",
        "key": ("tackling", "aggression", "anticipation", "bravery", "decisions", "positioning", "teamwork", "work_rate", "acceleration", "pace", "stamina"),
        "pref": ("marking", "concentration", "agility", "strength"),
    },
    "OPCentralOutletCentreForward": {
        "tr": "Topsuz: Merkez Kontra İstasyonu Santrfor (OP Central Outlet CF)",
        "pos": "stc", "pos_line": "STC", "oop_style": "Central_Counter_Outlet",
        "key": ("first_touch", "finishing", "heading", "anticipation", "composure", "off_the_ball", "acceleration", "jumping_reach", "pace", "strength"),
        "pref": ("dribbling", "passing", "technique", "decisions", "balance"),
    },
    "OPSplittingOutletCentreForward": {
        "tr": "Topsuz: Kanat Koridorlarına Kaçan Kontra Santrfor (OP Splitting Outlet CF)",
        "pos": "stc", "pos_line": "STC", "oop_style": "Splitting_Wide_Outlet",
        "key": ("dribbling", "finishing", "first_touch", "anticipation", "composure", "off_the_ball", "acceleration", "agility", "pace"),
        "pref": ("crossing", "passing", "technique", "decisions", "balance", "stamina"),
    },
}


def _compute_foot_alignment_multiplier(player: Any, pos_attr: str, foot_pref: str) -> float:
    """Compute a subtle multiplier (0.94..1.03) based on player's left/right foot vs flank & role preference."""
    left_f = getattr(player, "left_foot", 15) or 15
    right_f = getattr(player, "right_foot", 15) or 15
    pos_l = pos_attr.lower()
    is_left_flank = pos_l in ("dl", "wbl", "ml", "aml")
    is_right_flank = pos_l in ("dr", "wbr", "mr", "amr")

    if foot_pref == "either":
        # Central roles slightly reward two-footedness
        weak = min(left_f, right_f)
        return round(0.98 + 0.002 * min(20, weak), 3)

    if is_left_flank:
        same_foot, opp_foot = left_f, right_f
    elif is_right_flank:
        same_foot, opp_foot = right_f, left_f
    else:
        same_foot = max(left_f, right_f)
        opp_foot = min(left_f, right_f)

    target_foot = opp_foot if foot_pref == "inverted" else same_foot
    if target_foot >= 18:
        return 1.02
    if target_foot >= 15:
        return 1.00
    if target_foot >= 11:
        return 0.97
    return 0.94


def _compute_category_subscores(attrs: Any, key_set: set[str], pref_set: set[str]) -> dict[str, float]:
    """Calculate weighted 1..20 sub-scores per attribute category (technical, mental, physical, goalkeeping)."""
    out: dict[str, float] = {}
    for cat_name, cat_attrs in ATTRIBUTE_CATEGORIES.items():
        w_sum = 0.0
        w_tot = 0.0
        for a in cat_attrs:
            if not hasattr(attrs, a):
                continue
            val = float(getattr(attrs, a))
            if a in key_set:
                w_sum += 2.0 * val
                w_tot += 2.0
            elif a in pref_set:
                w_sum += 1.0 * val
                w_tot += 1.0
        if w_tot > 0:
            out[cat_name] = round(w_sum / w_tot, 2)
    return out


def _resolve_duty_attributes(
    base_key: tuple[str, ...],
    base_pref: tuple[str, ...],
    duty: str | None,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Apply duty-specific attribute promotions (Defend/Stopper/Cover/Support/Attack/Float)."""
    if not duty or duty not in DUTY_ATTRIBUTE_DELTAS:
        return base_key, base_pref
    delta = DUTY_ATTRIBUTE_DELTAS[duty]
    key_list = list(base_key)
    pref_list = [a for a in base_pref if a not in key_list]
    for a in delta.get("promote_to_key", ()):
        if a in pref_list:
            pref_list.remove(a)
        if a not in key_list:
            key_list.append(a)
    for a in delta.get("add_to_pref", ()):
        if a not in key_list and a not in pref_list:
            pref_list.append(a)
    return tuple(key_list), tuple(pref_list)


def position_familiarity_multiplier(pos_rating_1_to_20: int) -> float:
    """Return FM26's Decision/Effective-Ability multiplier from position familiarity (1..20)."""
    if pos_rating_1_to_20 >= 19:
        return 1.00  # Natural (19..20)
    if pos_rating_1_to_20 >= 15:
        return 0.93  # Accomplished (15..18)
    if pos_rating_1_to_20 >= 11:
        return 0.84  # Competent (11..14)
    if pos_rating_1_to_20 >= 5:
        return 0.72  # Unconvincing (5..10)
    return 0.55      # Makeshift (1..4)


def _best_flank_position(player: Any, default_pos: str) -> tuple[str, int]:
    """Resolve the best matching position slot (e.g., dl vs dr, aml vs amr) for a role."""
    pos_obj = getattr(player, "positions", None)
    if pos_obj is None:
        return default_pos, 20
    mirror_pairs = {
        "dl": ("dl", "dr"),
        "wbl": ("wbl", "wbr"),
        "ml": ("ml", "mr"),
        "aml": ("aml", "amr"),
    }
    candidates = mirror_pairs.get(default_pos.lower(), (default_pos.lower(),))
    best_slot = candidates[0]
    best_val = getattr(pos_obj, best_slot, 1)
    for cand in candidates[1:]:
        v = getattr(pos_obj, cand, 1)
        if v > best_val:
            best_slot, best_val = cand, v
    return best_slot, best_val


def calculate_role_effectiveness(
    player: Any,
    role_key: str,
    position_slot: str | None = None,
    *,
    duty: str | None = None,
    key_weight: float = 2.0,
    pref_weight: float = 1.0,
) -> dict[str, Any]:
    """Calculate a player's effectiveness (1..20, 0..100, 0.5..5.0 Stars) and sub-breakdowns in an In-Possession role."""
    if role_key not in TACTICAL_ROLE_DEFINITIONS:
        raise KeyError(f"Unknown role_key '{role_key}'. Valid keys: {list(TACTICAL_ROLE_DEFINITIONS)}")
    role_def = TACTICAL_ROLE_DEFINITIONS[role_key]
    avail_duties: tuple[str, ...] = role_def.get("duties", ("Support",))
    active_duty = duty if duty in avail_duties else avail_duties[0]

    if position_slot is not None:
        pos_attr = position_slot.lower()
        pos_rating = getattr(player.positions, pos_attr, 20) if player.positions else 20
    else:
        pos_attr, pos_rating = _best_flank_position(player, role_def["pos"])

    eff_key, eff_pref = _resolve_duty_attributes(role_def["key"], role_def["pref"], active_duty)
    attrs = player.attributes
    key_vals = {a: getattr(attrs, a) for a in eff_key if hasattr(attrs, a)}
    pref_vals = {a: getattr(attrs, a) for a in eff_pref if hasattr(attrs, a)}

    key_avg = sum(key_vals.values()) / len(key_vals) if key_vals else 10.0
    pref_avg = sum(pref_vals.values()) / len(pref_vals) if pref_vals else 10.0

    total_w = key_weight * len(key_vals) + pref_weight * len(pref_vals)
    weighted_sum = key_weight * sum(key_vals.values()) + pref_weight * sum(pref_vals.values())
    raw_score_20 = weighted_sum / total_w if total_w > 0 else 10.0

    pos_mult = position_familiarity_multiplier(pos_rating)
    foot_pref = role_def.get("foot_pref", "either")
    foot_mult = _compute_foot_alignment_multiplier(player, pos_attr, foot_pref)

    effective_score_20 = raw_score_20 * pos_mult * foot_mult
    effective_score_100 = min(100.0, effective_score_20 * 5.0)
    star_rating = round(max(0.5, min(5.0, (effective_score_20 - 5.0) / 3.0)), 1)

    cat_subscores = _compute_category_subscores(attrs, set(key_vals), set(pref_vals))
    sorted_keys_desc = sorted(key_vals.items(), key=lambda kv: (-kv[1], kv[0]))
    sorted_keys_asc = sorted(key_vals.items(), key=lambda kv: (kv[1], kv[0]))

    archetype_key = role_def.get("archetype", "BoxToBox_Engine")
    archetype_info = ROLE_ARCHETYPES.get(archetype_key, {"tr": archetype_key, "focus": ""})

    return {
        "role_key": role_key,
        "role_name_tr": role_def["tr"],
        "duty": active_duty,
        "available_duties": list(avail_duties),
        "position_line": role_def.get("pos_line", pos_attr.upper()),
        "position_slot": pos_attr.upper(),
        "position_rating_1_20": pos_rating,
        "position_familiarity_multiplier": pos_mult,
        "foot_preference_mode": foot_pref,
        "foot_alignment_multiplier": foot_mult,
        "archetype": archetype_key,
        "archetype_tr": archetype_info["tr"],
        "raw_attribute_score_20": round(raw_score_20, 2),
        "effective_role_score_20": round(effective_score_20, 2),
        "effective_role_score_100": round(effective_score_100, 1),
        "star_rating_5": star_rating,
        "key_vs_preferable_breakdown": {
            "key_attributes_count": len(key_vals),
            "key_attributes_avg_20": round(key_avg, 2),
            "preferable_attributes_count": len(pref_vals),
            "preferable_attributes_avg_20": round(pref_avg, 2),
            "key_weight_share_pct": round(100.0 * (key_weight * len(key_vals)) / total_w, 1) if total_w else 0.0,
        },
        "category_breakdown_20": cat_subscores,
        "strengths_top3_key": [{"attribute": k, "value": v} for k, v in sorted_keys_desc[:3]],
        "bottlenecks_low3_key": [{"attribute": k, "value": v} for k, v in sorted_keys_asc[:3]],
        "key_attributes": key_vals,
        "preferable_attributes": pref_vals,
    }


def calculate_oop_role_effectiveness(
    player: Any,
    oop_role_key: str,
    position_slot: str | None = None,
    *,
    key_weight: float = 2.0,
    pref_weight: float = 1.0,
) -> dict[str, Any]:
    """Calculate a player's effectiveness in an FM26 Out-Of-Possession (OP*) role."""
    if oop_role_key not in OUT_OF_POSSESSION_ROLE_CATALOG:
        raise KeyError(f"Unknown oop_role_key '{oop_role_key}'. Valid keys: {list(OUT_OF_POSSESSION_ROLE_CATALOG)}")
    role_def = OUT_OF_POSSESSION_ROLE_CATALOG[oop_role_key]

    if position_slot is not None:
        pos_attr = position_slot.lower()
        pos_rating = getattr(player.positions, pos_attr, 20) if player.positions else 20
    else:
        pos_attr, pos_rating = _best_flank_position(player, role_def["pos"])

    attrs = player.attributes
    key_vals = {a: getattr(attrs, a) for a in role_def["key"] if hasattr(attrs, a)}
    pref_vals = {a: getattr(attrs, a) for a in role_def["pref"] if hasattr(attrs, a)}

    key_avg = sum(key_vals.values()) / len(key_vals) if key_vals else 10.0
    pref_avg = sum(pref_vals.values()) / len(pref_vals) if pref_vals else 10.0
    total_w = key_weight * len(key_vals) + pref_weight * len(pref_vals)
    weighted_sum = key_weight * sum(key_vals.values()) + pref_weight * sum(pref_vals.values())
    raw_score_20 = weighted_sum / total_w if total_w > 0 else 10.0

    pos_mult = position_familiarity_multiplier(pos_rating)
    effective_score_20 = raw_score_20 * pos_mult
    effective_score_100 = min(100.0, effective_score_20 * 5.0)
    star_rating = round(max(0.5, min(5.0, (effective_score_20 - 5.0) / 3.0)), 1)

    cat_subscores = _compute_category_subscores(attrs, set(key_vals), set(pref_vals))
    sorted_keys_desc = sorted(key_vals.items(), key=lambda kv: (-kv[1], kv[0]))
    sorted_keys_asc = sorted(key_vals.items(), key=lambda kv: (kv[1], kv[0]))

    return {
        "oop_role_key": oop_role_key,
        "oop_role_name_tr": role_def["tr"],
        "oop_style": role_def["oop_style"],
        "position_line": role_def["pos_line"],
        "position_slot": pos_attr.upper(),
        "position_rating_1_20": pos_rating,
        "position_familiarity_multiplier": pos_mult,
        "raw_attribute_score_20": round(raw_score_20, 2),
        "effective_oop_score_20": round(effective_score_20, 2),
        "effective_oop_score_100": round(effective_score_100, 1),
        "star_rating_5": star_rating,
        "key_attributes_avg_20": round(key_avg, 2),
        "preferable_attributes_avg_20": round(pref_avg, 2),
        "category_breakdown_20": cat_subscores,
        "strengths_top3_key": [{"attribute": k, "value": v} for k, v in sorted_keys_desc[:3]],
        "bottlenecks_low3_key": [{"attribute": k, "value": v} for k, v in sorted_keys_asc[:3]],
        "key_attributes": key_vals,
        "preferable_attributes": pref_vals,
    }


def rank_player_roles(player: Any, top_n: int = 5, *, include_all_duties: bool = False) -> list[dict[str, Any]]:
    """Rank tactical roles for a player from highest effective score to lowest."""
    scores: list[dict[str, Any]] = []
    for rkey, rdef in TACTICAL_ROLE_DEFINITIONS.items():
        duties = rdef.get("duties", ("Support",))
        if include_all_duties:
            for d in duties:
                scores.append(calculate_role_effectiveness(player, rkey, duty=d))
        else:
            best_for_role = max(
                (calculate_role_effectiveness(player, rkey, duty=d) for d in duties),
                key=lambda x: (x["effective_role_score_100"], x["raw_attribute_score_20"]),
            )
            scores.append(best_for_role)
    scores.sort(key=lambda x: (-x["effective_role_score_100"], -x["raw_attribute_score_20"]))
    return scores[:top_n]


def analyze_player_role_breakdown(player: Any, *, top_n_per_group: int = 5) -> dict[str, Any]:
    """Comprehensive multi-dimensional FM26 Role Breakdown for a player:
    1. Top In-Possession (IP) Roles + Duties
    2. Top Out-Of-Possession (OP*) Roles
    3. Best Dual-Role Combinations (IP Role+Duty paired with matching Position-Line OP* Role)
    4. Breakdown by Position Line (GK, DC, FB, WB, DM, MC, WM, AMC, WINGER, STC)
    5. Breakdown by Duty (Defend, Stopper, Cover, Support, Attack, Float)
    6. Breakdown by Tactical Archetype (Playmaker, Scorer, Destroyer_Stopper, Cover_Holding, etc.)
    """
    ip_all: list[dict[str, Any]] = []
    for rkey, rdef in TACTICAL_ROLE_DEFINITIONS.items():
        for d in rdef.get("duties", ("Support",)):
            ip_all.append(calculate_role_effectiveness(player, rkey, duty=d))
    ip_all.sort(key=lambda x: (-x["effective_role_score_100"], -x["raw_attribute_score_20"]))

    oop_all: list[dict[str, Any]] = [
        calculate_oop_role_effectiveness(player, oop_key)
        for oop_key in OUT_OF_POSSESSION_ROLE_CATALOG
    ]
    oop_all.sort(key=lambda x: (-x["effective_oop_score_100"], -x["raw_attribute_score_20"]))

    # Group by Position Line
    by_pos_line: dict[str, dict[str, Any]] = {}
    pos_lines_order = ("GK", "DC", "FB", "WB", "DM", "MC", "WM", "AMC", "WINGER", "STC")
    for pline in pos_lines_order:
        line_ip = [r for r in ip_all if r["position_line"] == pline]
        line_oop = [r for r in oop_all if r["position_line"] == pline]
        if not line_ip and not line_oop:
            continue
        best_ip = line_ip[0] if line_ip else None
        best_oop = line_oop[0] if line_oop else None
        dual_score = (
            round(0.55 * best_ip["effective_role_score_100"] + 0.45 * best_oop["effective_oop_score_100"], 1)
            if (best_ip and best_oop)
            else None
        )
        by_pos_line[pline] = {
            "position_line": pline,
            "position_familiarity_1_20": best_ip["position_rating_1_20"] if best_ip else 1,
            "best_dual_role_score_100": dual_score,
            "best_in_possession": (
                f"{best_ip['role_name_tr']} [{best_ip['duty']}] ({best_ip['effective_role_score_100']})"
                if best_ip else None
            ),
            "best_out_of_possession": (
                f"{best_oop['oop_role_name_tr']} ({best_oop['effective_oop_score_100']})"
                if best_oop else None
            ),
            "top_in_possession_roles": [
                {
                    "role_key": r["role_key"],
                    "role_name_tr": r["role_name_tr"],
                    "duty": r["duty"],
                    "archetype": r["archetype"],
                    "effective_score_100": r["effective_role_score_100"],
                    "raw_score_20": r["raw_attribute_score_20"],
                    "star_rating_5": r["star_rating_5"],
                    "category_breakdown_20": r["category_breakdown_20"],
                }
                for r in line_ip[:top_n_per_group]
            ],
            "top_out_of_possession_roles": [
                {
                    "oop_role_key": r["oop_role_key"],
                    "oop_role_name_tr": r["oop_role_name_tr"],
                    "oop_style": r["oop_style"],
                    "effective_score_100": r["effective_oop_score_100"],
                    "raw_score_20": r["raw_attribute_score_20"],
                    "star_rating_5": r["star_rating_5"],
                }
                for r in line_oop[:top_n_per_group]
            ],
        }

    # Group by Duty
    by_duty: dict[str, list[dict[str, Any]]] = {}
    for duty_name in ("Defend", "Stopper", "Cover", "Support", "Attack", "Float"):
        duty_matches = [r for r in ip_all if r["duty"] == duty_name]
        if duty_matches:
            by_duty[duty_name] = [
                {
                    "role_key": r["role_key"],
                    "role_name_tr": r["role_name_tr"],
                    "position_line": r["position_line"],
                    "position_slot": r["position_slot"],
                    "effective_score_100": r["effective_role_score_100"],
                    "raw_score_20": r["raw_attribute_score_20"],
                    "star_rating_5": r["star_rating_5"],
                }
                for r in duty_matches[:top_n_per_group]
            ]

    # Group by Archetype
    by_archetype: dict[str, dict[str, Any]] = {}
    for arch_key, arch_meta in ROLE_ARCHETYPES.items():
        arch_matches = [r for r in ip_all if r["archetype"] == arch_key]
        if not arch_matches:
            continue
        best_r = arch_matches[0]
        by_archetype[arch_key] = {
            "archetype_tr": arch_meta["tr"],
            "focus": arch_meta["focus"],
            "best_effective_score_100": best_r["effective_role_score_100"],
            "best_raw_aptitude_20": max(r["raw_attribute_score_20"] for r in arch_matches),
            "top_roles": [
                {
                    "role_key": r["role_key"],
                    "role_name_tr": r["role_name_tr"],
                    "duty": r["duty"],
                    "position_slot": r["position_slot"],
                    "effective_score_100": r["effective_role_score_100"],
                    "raw_score_20": r["raw_attribute_score_20"],
                }
                for r in arch_matches[:top_n_per_group]
            ],
        }

    # Best Dual-Role Combinations (IP + OOP on same position_line)
    dual_combos: list[dict[str, Any]] = []
    oop_by_line: dict[str, list[dict[str, Any]]] = {}
    for oop_r in oop_all:
        oop_by_line.setdefault(oop_r["position_line"], []).append(oop_r)

    for ip_r in ip_all[:12]:
        pline = ip_r["position_line"]
        matching_oops = oop_by_line.get(pline, [])
        for oop_r in matching_oops[:2]:
            combined_100 = round(0.55 * ip_r["effective_role_score_100"] + 0.45 * oop_r["effective_oop_score_100"], 1)
            dual_combos.append(
                {
                    "position_line": pline,
                    "position_slot": ip_r["position_slot"],
                    "in_possession_role": ip_r["role_key"],
                    "in_possession_tr": ip_r["role_name_tr"],
                    "in_possession_duty": ip_r["duty"],
                    "in_possession_score_100": ip_r["effective_role_score_100"],
                    "out_of_possession_role": oop_r["oop_role_key"],
                    "out_of_possession_tr": oop_r["oop_role_name_tr"],
                    "out_of_possession_style": oop_r["oop_style"],
                    "out_of_possession_score_100": oop_r["effective_oop_score_100"],
                    "combined_dual_score_100": combined_100,
                    "combined_star_rating_5": round(max(0.5, min(5.0, (combined_100 / 5.0 - 5.0) / 3.0)), 1),
                }
            )
    dual_combos.sort(key=lambda x: -x["combined_dual_score_100"])

    return {
        "player_uid": getattr(player, "uid", None),
        "player_name": getattr(player, "name", None),
        "natural_positions": list(getattr(player, "natural_positions", ())),
        "ca": player.ability.current if getattr(player, "ability", None) else None,
        "pa": player.ability.potential if getattr(player, "ability", None) else None,
        "left_foot_20": getattr(player, "left_foot", None),
        "right_foot_20": getattr(player, "right_foot", None),
        "overall_top_in_possession": ip_all[:top_n_per_group],
        "overall_top_out_of_possession": oop_all[:top_n_per_group],
        "best_dual_role_combinations": dual_combos[:top_n_per_group],
        "by_position_line": by_pos_line,
        "by_duty": by_duty,
        "by_archetype": by_archetype,
    }


def get_role_catalog_breakdown() -> dict[str, Any]:
    """Return a structured breakdown of all FM26 In-Possession roles, Duties, Archetypes, and Out-Of-Possession (OP*) roles."""
    by_pos_line: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for rkey, rdef in TACTICAL_ROLE_DEFINITIONS.items():
        pline = rdef.get("pos_line", rdef["pos"].upper())
        by_pos_line.setdefault(pline, {"in_possession": [], "out_of_possession": []})
        by_pos_line[pline]["in_possession"].append(
            {
                "role_key": rkey,
                "tr": rdef["tr"],
                "archetype": rdef.get("archetype", ""),
                "duties": list(rdef.get("duties", ("Support",))),
                "foot_pref": rdef.get("foot_pref", "either"),
                "key_attributes": list(rdef["key"]),
                "preferable_attributes": list(rdef["pref"]),
            }
        )
    for oop_key, oop_def in OUT_OF_POSSESSION_ROLE_CATALOG.items():
        pline = oop_def["pos_line"]
        by_pos_line.setdefault(pline, {"in_possession": [], "out_of_possession": []})
        by_pos_line[pline]["out_of_possession"].append(
            {
                "oop_role_key": oop_key,
                "tr": oop_def["tr"],
                "oop_style": oop_def["oop_style"],
                "key_attributes": list(oop_def["key"]),
                "preferable_attributes": list(oop_def["pref"]),
            }
        )
    total_ip_duty_variants = sum(len(r.get("duties", ("Support",))) for r in TACTICAL_ROLE_DEFINITIONS.values())
    return {
        "in_possession_roles_count": len(TACTICAL_ROLE_DEFINITIONS),
        "in_possession_role_duty_variants_count": total_ip_duty_variants,
        "out_of_possession_roles_count": len(OUT_OF_POSSESSION_ROLE_CATALOG),
        "archetypes": ROLE_ARCHETYPES,
        "duty_attribute_deltas": {
            k: {dk: list(dv) for dk, dv in v.items()}
            for k, v in DUTY_ATTRIBUTE_DELTAS.items()
        },
        "by_position_line": by_pos_line,
    }


def estimate_transfer_value(
    *,
    ca: int,
    pa: int,
    age: int,
    weekly_wage: int,
    remaining_contract_years: float = 2.5,
    player_reputation: int = 5000,
    player_world_reputation: int = 3500,
    club_reputation: int = 6000,
    is_star_or_important: bool = False,
) -> dict[str, Any]:
    """Estimate FM26 Market / Transfer Value using the empirical log-linear model (R² = 0.805)."""
    rem_y = max(0.08, float(remaining_contract_years))
    wage = max(50.0, float(weekly_wage))
    youth_pot = max(0.0, 24.0 - float(age)) * max(0.0, float(pa - ca)) / 100.0
    log_v = (
        5.72207
        + 0.04063 * float(ca)
        + 0.00666 * max(0.0, float(ca) - 115.0)
        + 0.16353 * (float(player_reputation) / 1000.0)
        - 0.07339 * (float(player_world_reputation) / 1000.0)
        - 0.17025 * (float(club_reputation) / 1000.0)
        - 0.16164 * float(age)
        + 0.03968 * max(0.0, float(age) - 28.0)
        + 0.66654 * math.log(rem_y)
        + 0.82278 * math.log(wage)
        + 0.43513 * youth_pot
        - 0.26591 * (1.0 if is_star_or_important else 0.0)
    )
    mid_val = int(round(math.exp(log_v), -3))
    min_val = int(round(mid_val * 0.85, -3))
    max_val = int(round(mid_val * 1.20, -3))
    return {
        "estimated_value": mid_val,
        "estimated_range_min": min_val,
        "estimated_range_max": max_val,
    }


def estimate_wage_and_fees(
    *,
    ca: int,
    age: int,
    club_reputation: int = 6000,
    player_reputation: int = 5000,
    player_world_reputation: int = 3500,
    squad_status: str = "REGULAR_STARTER",
) -> dict[str, Any]:
    """Estimate FM26 Weekly Wage, Signing/Loyalty Fee (money_a) & Agent Fee (money_b)."""
    st = squad_status.upper()
    log_w = (
        1.04103
        + 0.01843 * float(ca)
        + 0.02248 * max(0.0, float(ca) - 115.0)
        - 0.01802 * max(0.0, float(ca) - 145.0)
        + 0.08630 * (float(player_reputation) / 1000.0)
        + 0.02394 * (float(player_world_reputation) / 1000.0)
        + 0.19201 * (float(club_reputation) / 1000.0)
        + 0.09904 * float(age)
        - 0.00302 * max(0.0, float(age) - 29.0)
        + (0.59182 if st == "STAR_PLAYER" else 0.0)
        + (0.54509 if st == "IMPORTANT_PLAYER" else 0.0)
        + (0.29583 if st == "REGULAR_STARTER" else 0.0)
        - (0.03846 if st in ("YOUNGSTER", "FUTURE_PROSPECT", "BREAKTHROUGH_PROSPECT") else 0.0)
    )
    weekly_wage = int(round(math.exp(log_w), -1))
    annual_wage = weekly_wage * 52
    return {
        "estimated_weekly_wage": weekly_wage,
        "estimated_annual_wage": annual_wage,
        "estimated_signing_or_loyalty_fee_median": int(round(annual_wage * 0.185, -2)),
        "estimated_signing_or_loyalty_fee_mean": int(round(annual_wage * 0.241, -2)),
        "estimated_agent_fee_median": int(round(annual_wage * 0.052, -2)),
        "estimated_agent_fee_mean": int(round(annual_wage * 0.059, -2)),
    }


# ---------------------------------------------------------------------------
# 3. SPORTS INTERACTIVE .JSB BINARY JSON PARSER & ENGINE EXTRACTOR
# ---------------------------------------------------------------------------
def parse_jsb(buf: bytes, pos: int = 0) -> tuple[Any, int]:
    """Parse Sports Interactive's proprietary .jsb Binary JSON format into Python objects."""
    b = buf[pos]
    pos += 1
    kind = b & 0x0F
    hi = (b >> 4) & 0x0F

    if kind == 0x0A:  # Object / Dict
        if hi == 0:
            count = struct.unpack_from("<I", buf, pos)[0]
            pos += 4
        else:
            count = hi - 1
        out: dict[str, Any] = {}
        for _ in range(count):
            klen = buf[pos]
            pos += 1
            key = buf[pos : pos + klen].decode("utf-8", errors="replace")
            pos += klen
            val, pos = parse_jsb(buf, pos)
            out[key] = val
        return out, pos
    if kind == 0x09:  # Array / List
        if hi == 0:
            count = struct.unpack_from("<I", buf, pos)[0]
            pos += 4
        else:
            count = hi - 1
        arr: list[Any] = []
        for _ in range(count):
            val, pos = parse_jsb(buf, pos)
            arr.append(val)
        return arr, pos
    if kind == 0x08:  # String
        if hi == 0:
            slen = struct.unpack_from("<I", buf, pos)[0]
            pos += 4
        else:
            slen = hi - 1
        s = buf[pos : pos + slen].decode("utf-8", errors="replace")
        pos += slen
        return s, pos
    if kind == 0x02:  # Int32
        if hi == 0:
            val = struct.unpack_from("<i", buf, pos)[0]
            pos += 4
        else:
            val = hi - 8
        return val, pos
    if kind == 0x04:  # UInt32
        if hi == 0:
            val = struct.unpack_from("<I", buf, pos)[0]
            pos += 4
        else:
            val = hi - 8
        return val, pos
    if kind == 0x05:  # UInt64
        if hi == 0:
            val = struct.unpack_from("<Q", buf, pos)[0]
            pos += 8
        else:
            val = hi - 8
        return val, pos
    if kind == 0x06:  # Float32
        if hi == 0:
            val = struct.unpack_from("<f", buf, pos)[0]
            pos += 4
            return round(val, 6), pos
        return float(hi - 8), pos
    if kind == 0x07:  # Float64
        if hi == 0:
            val = struct.unpack_from("<d", buf, pos)[0]
            pos += 8
            return round(val, 6), pos
        return float(hi - 8), pos
    if kind == 0x01:  # Bool
        return bool(hi - 8 if hi >= 8 else hi), pos
    if kind == 0x00:  # Zero / Null literal (1 byte)
        return 0, pos
    raise ValueError(f"Unsupported JSB tag 0x{b:02x} at offset {pos - 1}")


def extract_fmf_frames(fmf_path: str | Path) -> list[tuple[int, bytes]]:
    """Decompress all Zstandard frames inside an FM26 .fmf archive."""
    raw = Path(fmf_path).read_bytes()
    zstd_magic = b"\x28\xb5\x2f\xfd"
    idx = 0
    frames: list[tuple[int, bytes]] = []
    while True:
        pos = raw.find(zstd_magic, idx)
        if pos == -1:
            break
        try:
            dec = zstd.ZstdDecompressor().stream_reader(raw[pos:]).read(50_000_000)
            frames.append((pos, dec))
        except Exception:
            pass
        idx = pos + 4
    return frames


def load_engine_formulas(fm_install_dir: str | Path = DEFAULT_FM26_INSTALL_DIR) -> dict[str, Any]:
    """Load and decode official Match Engine, xG, Rating, Height & Training formulas from FM26 .fmf files."""
    root = Path(fm_install_dir)
    out: dict[str, Any] = {
        "ca_position_weights_10": CA_POSITION_WEIGHTS_10,
        "zero_ca_cost_attributes": list(ZERO_CA_COST_ATTRIBUTES),
        "tactical_role_definitions": TACTICAL_ROLE_DEFINITIONS,
    }
    simatch_path = root / "shared" / "data" / "simatch.fmf"
    if simatch_path.exists():
        sframes = extract_fmf_frames(simatch_path)
        if len(sframes) > 223:
            xg_models_v26: dict[str, Any] = {}
            for fidx in range(90, 101):
                m_obj, _ = parse_jsb(sframes[fidx][1], 0)
                st = m_obj.get("shot_type", f"frame_{fidx}")
                xg_models_v26[st] = {
                    "version": m_obj.get("version_number"),
                    "intercept": round(m_obj.get("intercept", 0) / 1e8, 6),
                    "coefficients": {
                        k: round(v / 1e8, 6) for k, v in m_obj.get("coefficients", {}).items()
                    } if isinstance(m_obj.get("coefficients"), dict) else m_obj.get("coefficients"),
                }
            out["xg_models_all_11_shot_types_v26"] = xg_models_v26
            out["momentum_weightings"], _ = parse_jsb(sframes[113][1], 0)
            out["oop_role_attribute_scoring"], _ = parse_jsb(sframes[114][1], 0)
            out["oop_pitch_proximity_scores"], _ = parse_jsb(sframes[115][1], 0)
            p_rat, _ = parse_jsb(sframes[118][1], 0)
            out["player_match_ratings_formula"] = {
                "start_value": p_rat["values"][0]["start_value"] / 1000.0,
                "expected_score_multipliers": p_rat["values"][0]["expected_score_data"],
                "action_coefficients": p_rat["values"][0]["role_data"][0]["coefficients"],
            }
            out["qme_stat_distributions"], _ = parse_jsb(sframes[119][1], 0)
            out["qme_stat_relevant_attributes"], _ = parse_jsb(sframes[120][1], 0)
            out["ai_team_selection_weights"], _ = parse_jsb(sframes[223][1], 0)

    tables_path = root / "shared" / "data" / "shared" / "tables.fmf"
    if tables_path.exists():
        tframes = extract_fmf_frames(tables_path)
        if len(tframes) >= 3:
            out["height_to_aerial_reach"], _ = parse_jsb(tframes[0][1], 0)
            out["height_to_jumping_reach"], _ = parse_jsb(tframes[2][1], 0)

    training_path = root / "data" / "game_simulation" / "training.fmf"
    if training_path.exists():
        trframes = extract_fmf_frames(training_path)
        if len(trframes) >= 5:
            out["training_item_effects"], _ = parse_jsb(trframes[1][1], 0)
            out["training_sessions_weights"], _ = parse_jsb(trframes[4][1], 0)

    return out
