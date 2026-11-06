"""FM27 Director of Football (Futbol Direktörü / DoF) Mode Engine.

Provides a complete Director of Football experience on top of FM26/FM27 saves:
1. Autonomous Coach Tactical Identity & Style Profiler (`derive_coach_tactical_profile`):
   Reads any coach's binary `Staff.preferences` and `block_40` coaching attributes to derive
   their natural FM27 tactical style, mentality, preferred formation, training intensity,
   rotation policy, and youth trust index — without forcing tactics onto the coach.
2. Coach Candidate Scouting & Style-Based Selection (`scan_coach_candidates`):
   Allows the Director of Football to search, filter, and rank Head Coach candidates by
   their natural playing style, coaching ability, wage/compensation cost, and compatibility
   with the club's current squad.
3. Coach–Squad Tactical Fit & Autonomous Lineup Engine (`analyze_coach_squad_fit`):
   Evaluates the club's roster against a coach's natural formation and tactical style DNA,
   builds the coach's autonomous 26-man matchday squad (Starting XI + 15 Bench), pinpoints
   weak links (priority transfer needs), and flags surplus/misfitting players.
4. DoF Club Hub, Capology & Transfer Target Recommender (`build_dof_dashboard`,
   `recommend_transfer_targets`):
   Audits club finances, wage capology, expiring contracts, youth/loan pipeline, and scans
   the 54,000+ player database for realistic transfer targets tailored to the coach's system.
5. Safe Working-Copy Save Actions (`hire_head_coach`):
   Applies coach hiring, staff list registration, compensation deduction, and the coach's
   autonomous tactical/lineup setup into a new `.fm` file without ever touching a running
   game or overwriting the active save in place.
"""

from __future__ import annotations

import datetime
import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from fm26save import FM26Save
from fm26save.constants import FM26_NATIONS, STAFF_ROLE_MAP
from fm26save.editor import FM26Editor

# ---------------------------------------------------------------------------
# 1. FM27 Official Tactical Styles & Coach Preference Signatures
# ---------------------------------------------------------------------------

MENTALITY_LABELS_TR: dict[int, str] = {
    1: "Çok Savunmacı (Very Defensive)",
    2: "Savunmacı (Defensive)",
    3: "Temkinli (Cautious)",
    4: "Dengeli (Balanced)",
    5: "Pozitif Futbol (Positive)",
    6: "Hücum Ağırlıklı (Attacking)",
    7: "Çok Hücumcu (Very Attacking)",
}


@dataclass(frozen=True, slots=True)
class TacticalStyleSpec:
    key: str
    name_en: str
    name_tr: str
    style_code: str
    description_tr: str
    ideal_prefs: Mapping[str, float]
    player_dna_weights: Mapping[str, float]
    default_formations: tuple[str, ...]
    base_mentality: int


FM27_TACTICAL_STYLES: dict[str, TacticalStyleSpec] = {
    "gegenpress": TacticalStyleSpec(
        key="gegenpress",
        name_en="Gegenpress",
        name_tr="Gegenpress (Yüksek Ön Alan Presi)",
        style_code="EGEG",
        description_tr="Top kaybedildiği anda şok pres, yüksek savunma çizgisi ve dikey hızlı geçiş.",
        ideal_prefs={
            "trigger_press": 18.0,
            "tempo": 16.5,
            "attacking": 15.5,
            "directness": 12.0,
            "width": 13.5,
            "patience": 9.0,
            "hardness_of_training": 15.5,
        },
        player_dna_weights={
            "work_rate": 2.2,
            "stamina": 2.0,
            "aggression": 1.5,
            "anticipation": 1.6,
            "acceleration": 1.6,
            "pace": 1.4,
            "teamwork": 1.7,
            "decisions": 1.4,
            "pressing_focus": 1.5,
        },
        default_formations=("4-2-3-1", "4-3-3 DM Wide", "3-4-2-1"),
        base_mentality=5,
    ),
    "tiki_taka": TacticalStyleSpec(
        key="tiki_taka",
        name_en="Tiki-Taka",
        name_tr="Tiki-Taka (Kısa Pas & Alan Hakimiyeti)",
        style_code="TAKT",
        description_tr="Aşırı kısa paslaşma, sabırlı hücum inşası, dar alanda üçgenler ve topla savunma.",
        ideal_prefs={
            "directness": 5.5,
            "patience": 17.5,
            "attacking": 14.5,
            "trigger_press": 15.5,
            "tempo": 11.0,
            "width": 11.5,
            "flexibility": 15.0,
        },
        player_dna_weights={
            "passing": 2.3,
            "first_touch": 2.1,
            "technique": 2.0,
            "vision": 1.9,
            "composure": 1.9,
            "decisions": 1.8,
            "off_the_ball": 1.6,
            "agility": 1.4,
            "teamwork": 1.5,
        },
        default_formations=("4-3-3 DM Wide", "4-2-3-1", "3-4-2-1"),
        base_mentality=5,
    ),
    "vertical_tiki_taka": TacticalStyleSpec(
        key="vertical_tiki_taka",
        name_en="Vertical Tiki-Taka",
        name_tr="Dikey Tiki-Taka (Merkez Odaklı Hızlı Pas)",
        style_code="KTID",
        description_tr="Kısa ama dikey paslarla merkezden hızlı delici hücumlar ve dar yerleşim.",
        ideal_prefs={
            "directness": 8.0,
            "tempo": 15.0,
            "width": 8.0,
            "patience": 14.0,
            "trigger_press": 15.0,
            "attacking": 14.5,
            "flexibility": 14.0,
        },
        player_dna_weights={
            "passing": 2.1,
            "first_touch": 2.0,
            "vision": 2.0,
            "decisions": 1.8,
            "off_the_ball": 1.9,
            "anticipation": 1.6,
            "technique": 1.8,
            "acceleration": 1.4,
        },
        default_formations=("4-3-1-2", "4-3-3 DM Wide", "3-4-2-1"),
        base_mentality=5,
    ),
    "control_possession": TacticalStyleSpec(
        key="control_possession",
        name_en="Control Possession",
        name_tr="Topa Sahip Olma (Kontrollü Dominasyon)",
        style_code="TOPK",
        description_tr="Oyunun temposunu ve topu kontrol ederek rakibi kendi yarı sahasına hapseden dengeli sistem.",
        ideal_prefs={
            "patience": 15.5,
            "directness": 8.5,
            "attacking": 13.5,
            "tempo": 12.0,
            "width": 13.5,
            "trigger_press": 14.0,
            "flexibility": 13.5,
        },
        player_dna_weights={
            "passing": 2.0,
            "decisions": 1.9,
            "composure": 1.9,
            "first_touch": 1.8,
            "vision": 1.7,
            "technique": 1.7,
            "positioning": 1.5,
            "teamwork": 1.6,
        },
        default_formations=("4-2-3-1", "4-3-3 DM Wide", "3-4-2-1"),
        base_mentality=5,
    ),
    "wing_play": TacticalStyleSpec(
        key="wing_play",
        name_en="Wing Play",
        name_tr="Kanat Oyunu (Çizgiye İnen Hücum)",
        style_code="KANA",
        description_tr="Topu hızla kanatlara aktaran, bek bindirmeleri ve ceza sahası ortalarıyla sonuç arayan oyun.",
        ideal_prefs={
            "width": 17.5,
            "attacking": 14.5,
            "tempo": 14.5,
            "directness": 13.5,
            "patience": 9.5,
            "trigger_press": 13.0,
        },
        player_dna_weights={
            "crossing": 2.2,
            "dribbling": 1.8,
            "pace": 1.9,
            "acceleration": 1.8,
            "stamina": 1.7,
            "off_the_ball": 1.6,
            "heading": 1.4,
            "work_rate": 1.5,
        },
        default_formations=("4-2-3-1", "4-4-2", "4-3-3 DM Wide"),
        base_mentality=5,
    ),
    "fluid_counter": TacticalStyleSpec(
        key="fluid_counter",
        name_en="Fluid Counter-Attack",
        name_tr="Akıcı Kontra Atak (Esnek Geçiş Oyunu)",
        style_code="AKIC",
        description_tr="Orta/alt blokta rakibi üzerine çekip kazanılan toplarla akıcı ve paslı geçiş hücumları.",
        ideal_prefs={
            "attacking": 10.5,
            "directness": 11.5,
            "tempo": 14.0,
            "patience": 11.5,
            "flexibility": 15.5,
            "trigger_press": 10.5,
            "width": 13.0,
        },
        player_dna_weights={
            "pace": 1.8,
            "acceleration": 1.8,
            "decisions": 1.8,
            "passing": 1.7,
            "dribbling": 1.6,
            "off_the_ball": 1.8,
            "positioning": 1.6,
            "stamina": 1.6,
        },
        default_formations=("4-2-3-1", "4-3-3 DM Wide", "3-5-2"),
        base_mentality=4,
    ),
    "direct_counter": TacticalStyleSpec(
        key="direct_counter",
        name_en="Direct Counter-Attack",
        name_tr="Doğrudan Kontra Atak (Yıldırım Geçiş)",
        style_code="DOGR",
        description_tr="Sağlam savunma bloğu ardından kazanılan topu en az pasla savunma arkasına gönderen dikey geçiş.",
        ideal_prefs={
            "directness": 16.5,
            "tempo": 16.5,
            "attacking": 9.5,
            "patience": 7.0,
            "trigger_press": 9.5,
            "width": 13.5,
        },
        player_dna_weights={
            "pace": 2.1,
            "acceleration": 2.0,
            "work_rate": 1.8,
            "stamina": 1.8,
            "positioning": 1.7,
            "tackling": 1.6,
            "off_the_ball": 1.8,
            "strength": 1.5,
        },
        default_formations=("4-4-2", "3-5-2", "4-2-3-1"),
        base_mentality=3,
    ),
    "route_one": TacticalStyleSpec(
        key="route_one",
        name_en="Route One",
        name_tr="Uzun Top / Direkt Oyun (Route One)",
        style_code="UZUN",
        description_tr="Merkezi hızla geçip hedef santrfor ve ikinci toplar üzerinden sonuca giden fiziksel oyun.",
        ideal_prefs={
            "directness": 18.0,
            "patience": 5.5,
            "tempo": 15.0,
            "attacking": 10.0,
            "trigger_press": 10.0,
            "width": 12.5,
        },
        player_dna_weights={
            "jumping_reach": 2.1,
            "heading": 2.0,
            "strength": 2.0,
            "work_rate": 1.8,
            "aggression": 1.6,
            "bravery": 1.7,
            "anticipation": 1.6,
        },
        default_formations=("4-4-2", "3-5-2"),
        base_mentality=3,
    ),
    "catenaccio": TacticalStyleSpec(
        key="catenaccio",
        name_en="Catenaccio",
        name_tr="Catenaccio (Ceza Sahası Kilit Savunması)",
        style_code="CATE",
        description_tr="Sıkı adam/alan markajı, libero destekli üçlü/beşli savunma hattı ve sıfır riskli savunma disiplini.",
        ideal_prefs={
            "attacking": 6.5,
            "trigger_press": 7.5,
            "patience": 11.0,
            "directness": 12.5,
            "tempo": 9.5,
            "flexibility": 8.0,
        },
        player_dna_weights={
            "positioning": 2.3,
            "marking": 2.2,
            "tackling": 2.0,
            "concentration": 2.0,
            "decisions": 1.8,
            "strength": 1.7,
            "teamwork": 1.7,
        },
        default_formations=("3-5-2", "3-4-2-1"),
        base_mentality=2,
    ),
    "park_the_bus": TacticalStyleSpec(
        key="park_the_bus",
        name_en="Park the Bus",
        name_tr="Katı Savunma (Park the Bus)",
        style_code="PARK",
        description_tr="Tüm hatlarıyla kendi ceza sahası önünde etten duvar ören ultra-savunmacı düzen.",
        ideal_prefs={
            "attacking": 4.5,
            "trigger_press": 5.5,
            "tempo": 7.5,
            "width": 7.5,
            "patience": 9.0,
            "directness": 14.5,
        },
        player_dna_weights={
            "positioning": 2.4,
            "concentration": 2.1,
            "marking": 2.1,
            "tackling": 2.0,
            "bravery": 1.9,
            "strength": 1.8,
            "heading": 1.8,
        },
        default_formations=("4-4-2", "3-5-2"),
        base_mentality=1,
    ),
}


# ---------------------------------------------------------------------------
# 2. Formation Definitions & Slot Role Requirements
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class FormationSlotSpec:
    slot_index: int
    code: str
    label_tr: str
    ip_role_tr: str
    oop_role_tr: str
    primary_pos: tuple[str, ...]
    secondary_pos: tuple[str, ...]
    key_attrs: tuple[str, ...]


FM27_FORMATIONS: dict[str, tuple[FormationSlotSpec, ...]] = {
    "4-2-3-1": (
        FormationSlotSpec(0, "GK", "Kaleci", "Libero Kaleci (SK)", "Çizgi / Alan Kalecisi", ("gk",), (), ("reflexes", "handling", "command_of_area", "kicking", "positioning")),
        FormationSlotSpec(1, "DR", "Sağ Bek", "İki Yönlü / Bindiren Bek", "Presçi Bek", ("dr",), ("wbr",), ("pace", "stamina", "tackling", "crossing", "work_rate", "positioning")),
        FormationSlotSpec(2, "DCR", "Sağ Stoper", "Pasör Stoper (BPD)", "Kesici Stoper", ("dc",), (), ("marking", "tackling", "positioning", "jumping_reach", "passing", "strength")),
        FormationSlotSpec(3, "DCL", "Sol Stoper", "Pasör Stoper (BPD)", "Sigorta Stoper", ("dc",), (), ("marking", "tackling", "positioning", "jumping_reach", "composure", "pace")),
        FormationSlotSpec(4, "DL", "Sol Bek", "İki Yönlü / İç Bek", "Dengeli Bek", ("dl",), ("wbl",), ("pace", "stamina", "tackling", "crossing", "work_rate", "decisions")),
        FormationSlotSpec(5, "DMR", "Sağ Ön Libero (6)", "Derin Oyun Kurucu / 6", "Alan Kapatıcı DOS", ("dm", "mc"), (), ("passing", "positioning", "tackling", "decisions", "vision", "teamwork")),
        FormationSlotSpec(6, "DML", "Sol Merkez (8)", "Box-to-Box / Segundo Volante", "Baskı Yapan Orta Saha", ("dm", "mc"), (), ("work_rate", "stamina", "passing", "tackling", "off_the_ball", "anticipation")),
        FormationSlotSpec(7, "AMR", "Sağ Kanat", "İçe Kat Eden Kanat / Kanat Forvet", "Ön Alan Presçisi", ("amr",), ("mr", "aml"), ("acceleration", "pace", "dribbling", "finishing", "crossing", "off_the_ball")),
        FormationSlotSpec(8, "AMC", "On Numara (10)", "Ofansif Oyun Kurucu / Gölge Forvet", "Merkez Presçisi", ("amc",), ("mc", "stc"), ("vision", "passing", "first_touch", "technique", "flair", "decisions")),
        FormationSlotSpec(9, "AML", "Sol Kanat", "Kanat Forvet (IF)", "Ön Alan Presçisi", ("aml",), ("ml", "amr"), ("acceleration", "pace", "dribbling", "finishing", "first_touch", "agility")),
        FormationSlotSpec(10, "STC", "Santrfor (9)", "Çalışkan / Komple Forvet", "İlk Pres Başlatıcı", ("stc",), ("amc",), ("finishing", "off_the_ball", "composure", "acceleration", "first_touch", "heading")),
    ),
    "4-3-3 DM Wide": (
        FormationSlotSpec(0, "GK", "Kaleci", "Libero Kaleci (SK)", "Alan Kalecisi", ("gk",), (), ("reflexes", "handling", "kicking", "composure", "one_on_ones")),
        FormationSlotSpec(1, "DR", "Sağ Bek", "Kanat Bek / İç Bek", "Dengeli Bek", ("dr",), ("wbr",), ("pace", "stamina", "tackling", "passing", "crossing", "work_rate")),
        FormationSlotSpec(2, "DCR", "Sağ Stoper", "Pasör Stoper (BPD)", "Kesici Stoper", ("dc",), (), ("marking", "tackling", "positioning", "passing", "jumping_reach", "strength")),
        FormationSlotSpec(3, "DCL", "Sol Stoper", "Pasör Stoper (BPD)", "Sigorta Stoper", ("dc",), (), ("marking", "tackling", "positioning", "passing", "composure", "pace")),
        FormationSlotSpec(4, "DL", "Sol Bek", "Hücumcu Bek", "Presçi Bek", ("dl",), ("wbl",), ("pace", "stamina", "tackling", "crossing", "work_rate", "decisions")),
        FormationSlotSpec(5, "DM", "Tek Ön Libero (6)", "Regista / Çapa (Anchor)", "Savunma Önü Kalkanı", ("dm",), ("mc",), ("positioning", "tackling", "passing", "decisions", "anticipation", "concentration")),
        FormationSlotSpec(6, "MCR", "Sağ İç (8)", "Mezzala / İki Yönlü Merkez", "Merkez Presçisi", ("mc",), ("amc", "dm"), ("passing", "vision", "work_rate", "stamina", "technique", "off_the_ball")),
        FormationSlotSpec(7, "MCL", "Sol İç (8)", "Oyun Kurucu (AP)", "Alan Daraltan İç", ("mc",), ("dm", "amc"), ("passing", "first_touch", "decisions", "teamwork", "stamina", "tackling")),
        FormationSlotSpec(8, "AMR", "Sağ Kanat Forvet", "Kanat Forvet (IF)", "Ön Alan Presçisi", ("amr",), ("mr",), ("acceleration", "pace", "dribbling", "finishing", "technique", "off_the_ball")),
        FormationSlotSpec(9, "AML", "Sol Kanat Forvet", "Kanat Forvet (IF)", "Ön Alan Presçisi", ("aml",), ("ml",), ("acceleration", "pace", "dribbling", "finishing", "crossing", "agility")),
        FormationSlotSpec(10, "STC", "Santrfor (9)", "Yaratıcı / Komple Forvet", "Stoper Baskılayıcı", ("stc",), (), ("finishing", "off_the_ball", "composure", "first_touch", "acceleration", "strength")),
    ),
    "3-4-2-1": (
        FormationSlotSpec(0, "GK", "Kaleci", "Libero Kaleci (SK)", "Alan Kalecisi", ("gk",), (), ("reflexes", "handling", "kicking", "command_of_area", "composure")),
        FormationSlotSpec(1, "DCR", "Sağ Kenar Stoper", "Geniş Stoper (WCB)", "Kenar Kapatıcı Stoper", ("dc",), ("dr",), ("pace", "tackling", "marking", "positioning", "passing", "stamina")),
        FormationSlotSpec(2, "DCC", "Merkez Libero Stoper", "Merkez Stoper / Libero", "Süpürücü Stoper", ("dc",), ("dm",), ("positioning", "marking", "jumping_reach", "heading", "composure", "decisions")),
        FormationSlotSpec(3, "DCL", "Sol Kenar Stoper", "Geniş Stoper (WCB)", "Kenar Kapatıcı Stoper", ("dc",), ("dl",), ("pace", "tackling", "marking", "positioning", "passing", "stamina")),
        FormationSlotSpec(4, "WBR", "Sağ Kanat Bek", "Komple Kanat Bek", "Kanat Presçisi", ("wbr", "mr"), ("dr", "amr"), ("stamina", "work_rate", "crossing", "pace", "acceleration", "tackling")),
        FormationSlotSpec(5, "DMR", "Sağ Merkez (6/8)", "Derin Oyun Kurucu", "Merkez Kalkanı", ("dm", "mc"), (), ("passing", "decisions", "positioning", "tackling", "teamwork", "stamina")),
        FormationSlotSpec(6, "DML", "Sol Merkez (8)", "Box-to-Box", "Savaşçı Orta Saha", ("dm", "mc"), (), ("work_rate", "stamina", "tackling", "passing", "anticipation", "aggression")),
        FormationSlotSpec(7, "WBL", "Sol Kanat Bek", "Komple Kanat Bek", "Kanat Presçisi", ("wbl", "ml"), ("dl", "aml"), ("stamina", "work_rate", "crossing", "pace", "acceleration", "tackling")),
        FormationSlotSpec(8, "AMCR", "Sağ Yarı-Alan (10)", "Gölge Forvet / İç 10", "Yarı-Alan Presçisi", ("amc", "amr"), ("mc", "stc"), ("vision", "passing", "dribbling", "first_touch", "off_the_ball", "finishing")),
        FormationSlotSpec(9, "AMCL", "Sol Yarı-Alan (10)", "Ofansif Oyun Kurucu / İç 10", "Yarı-Alan Presçisi", ("amc", "aml"), ("mc", "stc"), ("vision", "passing", "technique", "flair", "decisions", "agility")),
        FormationSlotSpec(10, "STC", "Santrfor (9)", "Yaratıcı / Fırsatçı Forvet", "Ön Pres Lideri", ("stc",), (), ("finishing", "off_the_ball", "composure", "acceleration", "heading", "strength")),
    ),
    "3-5-2": (
        FormationSlotSpec(0, "GK", "Kaleci", "Kaleci", "Çizgi Kalecisi", ("gk",), (), ("reflexes", "handling", "command_of_area", "positioning", "one_on_ones")),
        FormationSlotSpec(1, "DCR", "Sağ Stoper", "Pasör Stoper", "Kesici Stoper", ("dc",), ("dr",), ("marking", "tackling", "positioning", "strength", "pace")),
        FormationSlotSpec(2, "DCC", "Merkez Stoper", "Kule Stoper", "Süpürücü Stoper", ("dc",), (), ("jumping_reach", "heading", "positioning", "marking", "concentration")),
        FormationSlotSpec(3, "DCL", "Sol Stoper", "Pasör Stoper", "Kesici Stoper", ("dc",), ("dl",), ("marking", "tackling", "positioning", "composure", "pace")),
        FormationSlotSpec(4, "WBR", "Sağ Kanat Bek", "Kanat Bek", "Geriye Yardım Eden Bek", ("wbr", "mr", "dr"), (), ("stamina", "work_rate", "crossing", "pace", "tackling")),
        FormationSlotSpec(5, "DM", "Ön Libero (6)", "Regista / DOS", "Savunma Önü Sigortası", ("dm", "mc"), (), ("positioning", "passing", "tackling", "decisions", "vision")),
        FormationSlotSpec(6, "MCR", "Sağ İç (8)", "Mezzala / B2B", "Baskı Yapan İç", ("mc",), ("amc", "dm"), ("work_rate", "stamina", "passing", "off_the_ball", "technique")),
        FormationSlotSpec(7, "MCL", "Sol İç (8)", "Merkez Orta Saha", "Alan Kapatıcı İç", ("mc",), ("dm", "amc"), ("passing", "tackling", "teamwork", "stamina", "decisions")),
        FormationSlotSpec(8, "WBL", "Sol Kanat Bek", "Kanat Bek", "Geriye Yardım Eden Bek", ("wbl", "ml", "dl"), (), ("stamina", "work_rate", "crossing", "pace", "tackling")),
        FormationSlotSpec(9, "STCR", "Sağ Forvet", "Yardımcı / Yaratıcı Forvet", "Ön Blok Presçisi", ("stc",), ("amc", "amr"), ("off_the_ball", "passing", "dribbling", "finishing", "acceleration")),
        FormationSlotSpec(10, "STCL", "Sol Forvet", "Pivot / Bitirici Santrfor", "Ceza Sahası Golcüsü", ("stc",), (), ("finishing", "composure", "heading", "strength", "off_the_ball")),
    ),
    "4-4-2": (
        FormationSlotSpec(0, "GK", "Kaleci", "Kaleci", "Çizgi Kalecisi", ("gk",), (), ("reflexes", "handling", "command_of_area", "kicking", "positioning")),
        FormationSlotSpec(1, "DR", "Sağ Bek", "Standart Bek", "Savunmacı Bek", ("dr",), ("wbr",), ("tackling", "positioning", "stamina", "crossing", "pace")),
        FormationSlotSpec(2, "DCR", "Sağ Stoper", "Stoper", "Kesici Stoper", ("dc",), (), ("marking", "tackling", "jumping_reach", "heading", "strength")),
        FormationSlotSpec(3, "DCL", "Sol Stoper", "Stoper", "Sigorta Stoper", ("dc",), (), ("marking", "tackling", "positioning", "composure", "pace")),
        FormationSlotSpec(4, "DL", "Sol Bek", "Standart Bek", "Savunmacı Bek", ("dl",), ("wbl",), ("tackling", "positioning", "stamina", "crossing", "pace")),
        FormationSlotSpec(5, "MR", "Sağ Kanat", "Klasik Kanat (W)", "Çizgi Kapatıcı Kanat", ("mr", "amr"), ("wbr",), ("crossing", "pace", "acceleration", "dribbling", "stamina")),
        FormationSlotSpec(6, "MCR", "Sağ Merkez", "İki Yönlü Orta Saha", "Merkez Savaşçısı", ("mc", "dm"), (), ("work_rate", "stamina", "tackling", "passing", "teamwork")),
        FormationSlotSpec(7, "MCL", "Sol Merkez", "Oyun Kurucu / Merkez", "Pozisyonel Orta Saha", ("mc", "dm"), (), ("passing", "decisions", "positioning", "vision", "first_touch")),
        FormationSlotSpec(8, "ML", "Sol Kanat", "Klasik Kanat (W)", "Çizgi Kapatıcı Kanat", ("ml", "aml"), ("wbl",), ("crossing", "pace", "acceleration", "dribbling", "stamina")),
        FormationSlotSpec(9, "STCR", "Sağ Forvet", "Çalışkan / İkinci Forvet", "Bağlantı Forveti", ("stc",), ("amc",), ("off_the_ball", "work_rate", "finishing", "passing", "acceleration")),
        FormationSlotSpec(10, "STCL", "Sol Forvet", "Bitirici / Hedef Santrfor", "Ceza Sahası Forveti", ("stc",), (), ("finishing", "heading", "strength", "composure", "jumping_reach")),
    ),
    "4-3-1-2": (
        FormationSlotSpec(0, "GK", "Kaleci", "Libero Kaleci", "Alan Kalecisi", ("gk",), (), ("reflexes", "handling", "kicking", "composure", "positioning")),
        FormationSlotSpec(1, "DR", "Sağ Bek", "Hücumcu Bek", "Genişlik Veren Bek", ("dr", "wbr"), (), ("stamina", "pace", "crossing", "work_rate", "tackling")),
        FormationSlotSpec(2, "DCR", "Sağ Stoper", "Pasör Stoper", "Kesici Stoper", ("dc",), (), ("marking", "tackling", "positioning", "passing", "strength")),
        FormationSlotSpec(3, "DCL", "Sol Stoper", "Pasör Stoper", "Sigorta Stoper", ("dc",), (), ("marking", "tackling", "positioning", "composure", "pace")),
        FormationSlotSpec(4, "DL", "Sol Bek", "Hücumcu Bek", "Genişlik Veren Bek", ("dl", "wbl"), (), ("stamina", "pace", "crossing", "work_rate", "tackling")),
        FormationSlotSpec(5, "DM", "Ön Libero (6)", "Derin Oyun Kurucu", "Merkez Sigortası", ("dm",), ("mc",), ("passing", "positioning", "tackling", "decisions", "vision")),
        FormationSlotSpec(6, "MCR", "Sağ İç (8)", "Carrilero / Mezzala", "Yarı-Alan Kapatıcı", ("mc",), ("dm",), ("stamina", "work_rate", "passing", "tackling", "teamwork")),
        FormationSlotSpec(7, "MCL", "Sol İç (8)", "Box-to-Box", "Merkez Presçisi", ("mc",), ("dm",), ("stamina", "work_rate", "passing", "off_the_ball", "decisions")),
        FormationSlotSpec(8, "AMC", "On Numara (10)", "Enganche / Oyun Kurucu", "Forvet Arkası Presçi", ("amc",), ("mc", "stc"), ("vision", "passing", "first_touch", "technique", "flair")),
        FormationSlotSpec(9, "STCR", "Sağ Forvet", "Gezgin / Yaratıcı Forvet", "Kanatlara Açılan Forvet", ("stc",), ("amr", "amc"), ("acceleration", "pace", "dribbling", "finishing", "off_the_ball")),
        FormationSlotSpec(10, "STCL", "Sol Forvet", "Fırsatçı Golcü (Poacher)", "Stoper Baskılayıcı", ("stc",), (), ("finishing", "composure", "off_the_ball", "first_touch", "acceleration")),
    ),
}


# ---------------------------------------------------------------------------
# 3. Data Structures for DoF Reports
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class CoachTacticalProfile:
    staff_uid: int
    name: str
    age: int | None
    nation_id: int | None
    nation_tr: str
    club_uid: int | None
    club_name: str | None
    role_code: int
    role_tr: str
    current_ability: int
    potential_ability: int
    wage_weekly: int
    contract_end: str | None
    primary_style_key: str
    primary_style_tr: str
    primary_style_en: str
    style_code: str
    style_description_tr: str
    secondary_style_key: str
    secondary_style_tr: str
    preferred_formation: str
    natural_mentality: int
    mentality_tr: str
    archetype_tr: str
    training_style_tr: str
    rotation_style_tr: str
    youth_trust_score: int
    coaching_score: float
    tactical_score: float
    man_management_score: float
    style_scores: Mapping[str, float]
    preferences: Mapping[str, int]
    key_attributes_20: Mapping[str, int]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SquadSlotAssignment:
    slot_index: int
    slot_code: str
    slot_label_tr: str
    ip_role_tr: str
    oop_role_tr: str
    player_uid: int
    player_name: str
    age: int | None
    ca: int
    pa: int
    wage_weekly: int
    pos_rating: int
    style_dna_score: float
    role_attr_score: float
    slot_fit_score: float
    status: str  # "ELITE", "SOLID", "WEAK_LINK", "OUT_OF_POSITION"
    note_tr: str


@dataclass(frozen=True, slots=True)
class CoachSquadFitReport:
    club_uid: int
    club_name: str
    coach: CoachTacticalProfile
    formation: str
    overall_compatibility: float
    formation_coverage_score: float
    style_dna_score: float
    starting_xi_avg_ca: float
    starting_xi: tuple[SquadSlotAssignment, ...]
    bench: tuple[dict[str, Any], ...]
    priority_transfer_needs: tuple[dict[str, Any], ...]
    surplus_candidates: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CoachCandidateRow:
    rank: int
    profile: CoachTacticalProfile
    squad_compatibility: float
    weak_positions_count: int
    weak_positions_summary: str
    style_match_score: float
    estimated_compensation: int
    estimated_weekly_wage: int
    dof_total_score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# 4. Field Access Helpers (`Staff`, `Player`, `Contract`)
# ---------------------------------------------------------------------------

def _staff_ca(st: Any) -> int:
    ab = getattr(st, "ability", None)
    return int(ab.current) if ab is not None and ab.current is not None else 0


def _staff_pa(st: Any) -> int:
    ab = getattr(st, "ability", None)
    return int(ab.potential) if ab is not None and ab.potential is not None else 0


def _player_ca(p: Any) -> int:
    ab = getattr(p, "ability", None)
    return int(ab.current) if ab is not None and ab.current is not None else 0


def _player_pa(p: Any) -> int:
    ab = getattr(p, "ability", None)
    return int(ab.potential) if ab is not None and ab.potential is not None else 0


def _player_pos(p: Any, pos_name: str) -> int:
    pos_obj = getattr(p, "positions", None)
    if pos_obj is not None:
        return int(getattr(pos_obj, pos_name, 1) or 1)
    return int(getattr(p, pos_name, 1) or 1)


def _player_attr(p: Any, attr_name: str, default: int = 10) -> int:
    attr_obj = getattr(p, "attributes", None)
    if attr_obj is not None:
        v = getattr(attr_obj, attr_name, None)
        if v is not None:
            return int(v)
    v = getattr(p, attr_name, None)
    return int(v) if v is not None else default


def _b40_20(staff_member: Any, index: int, default: int = 10) -> int:
    uk = getattr(staff_member, "unknown", {})
    val = uk.get(f"b40_20_{index}")
    if val is not None:
        return int(val)
    raw = uk.get(f"b40_raw_{index}")
    if raw is not None:
        return max(1, min(20, (int(raw) + 2) // 5))
    return default


def _pref(staff_member: Any, name: str, default: int = 10) -> int:
    prefs = getattr(staff_member, "preferences", None)
    if prefs is None:
        return default
    v = getattr(prefs, name, None)
    return int(v) if v is not None else default


# ---------------------------------------------------------------------------
# 5. Coach Tactical Identity Derivation
# ---------------------------------------------------------------------------

def derive_coach_tactical_profile(staff_member: Any) -> CoachTacticalProfile:
    """Derive a coach's natural tactical identity, formation, and management style from binary data."""
    prefs_map: dict[str, int] = {
        "attacking": _pref(staff_member, "attacking", 11),
        "directness": _pref(staff_member, "directness", 10),
        "tempo": _pref(staff_member, "tempo", 11),
        "width": _pref(staff_member, "width", 11),
        "trigger_press": _pref(staff_member, "trigger_press", 11),
        "patience": _pref(staff_member, "patience", 11),
        "flexibility": _pref(staff_member, "flexibility", 11),
        "squad_rotation": _pref(staff_member, "squad_rotation", 11),
        "hardness_of_training": _pref(staff_member, "hardness_of_training", 11),
        "buying_players": _pref(staff_member, "buying_players", 11),
        "business": _pref(staff_member, "business", 11),
        "interference": _pref(staff_member, "interference", 10),
        "resources": _pref(staff_member, "resources", 11),
        "mind_games": _pref(staff_member, "mind_games", 10),
    }

    attrs_20: dict[str, int] = {
        "tactical_style_knowledge": _b40_20(staff_member, 0),
        "judging_player_ability": _b40_20(staff_member, 2),
        "judging_player_potential": _b40_20(staff_member, 3),
        "level_of_discipline": _b40_20(staff_member, 5),
        "tactical_knowledge": _b40_20(staff_member, 7),
        "attacking_coaching": _b40_20(staff_member, 8),
        "defending_coaching": _b40_20(staff_member, 9),
        "tactical_coaching": _b40_20(staff_member, 11),
        "technical_coaching": _b40_20(staff_member, 12),
        "mental_coaching": _b40_20(staff_member, 13),
        "people_management": _b40_20(staff_member, 14),
        "determination": _b40_20(staff_member, 15),
        "motivating": _b40_20(staff_member, 16),
        "adaptability": _b40_20(staff_member, 17),
        "working_with_youngsters": _b40_20(staff_member, 18),
        "set_pieces_coaching": _b40_20(staff_member, 22),
        "fitness_coaching": _b40_20(staff_member, 25),
    }

    # Score all 10 official FM27 tactical styles based on coach's binary preferences
    style_scores: dict[str, float] = {}
    for s_key, spec in FM27_TACTICAL_STYLES.items():
        sq_err = 0.0
        weight_sum = 0.0
        for p_name, ideal_val in spec.ideal_prefs.items():
            actual_val = float(prefs_map.get(p_name, 10))
            w = 1.6 if p_name in ("trigger_press", "directness", "attacking", "patience", "width", "tempo") else 1.0
            diff = (actual_val - ideal_val) / 19.0
            sq_err += w * (diff * diff)
            weight_sum += w
        rms = math.sqrt(sq_err / max(1.0, weight_sum))
        score = max(15.0, min(99.0, round((1.0 - rms * 1.35) * 100.0, 1)))
        style_scores[s_key] = score

    ranked_styles = sorted(style_scores.items(), key=lambda kv: kv[1], reverse=True)
    primary_key = ranked_styles[0][0]
    secondary_key = ranked_styles[1][0]
    primary_spec = FM27_TACTICAL_STYLES[primary_key]
    secondary_spec = FM27_TACTICAL_STYLES[secondary_key]

    width_v = prefs_map["width"]
    att_v = prefs_map["attacking"]
    flex_v = prefs_map["flexibility"]
    dir_v = prefs_map["directness"]

    if primary_key in ("catenaccio",):
        preferred_formation = "3-5-2" if dir_v >= 12 else "3-4-2-1"
    elif primary_key == "vertical_tiki_taka" and width_v <= 9:
        preferred_formation = "4-3-1-2"
    elif flex_v >= 15 and width_v >= 13 and att_v >= 13 and (staff_member.uid % 3 == 0):
        preferred_formation = "3-4-2-1"
    elif primary_key in ("route_one", "direct_counter", "park_the_bus"):
        preferred_formation = "4-4-2" if width_v >= 11 else "3-5-2"
    elif primary_key in ("tiki_taka", "control_possession"):
        preferred_formation = "4-3-3 DM Wide" if prefs_map["patience"] >= 15 else "4-2-3-1"
    else:
        preferred_formation = "4-2-3-1" if att_v >= 13 else primary_spec.default_formations[0]

    if att_v >= 18:
        mentality = 7
    elif att_v >= 15:
        mentality = 6
    elif att_v >= 12:
        mentality = 5
    elif att_v >= 9:
        mentality = 4
    elif att_v >= 6:
        mentality = 3
    elif att_v >= 4:
        mentality = 2
    else:
        mentality = 1

    wwy = attrs_20["working_with_youngsters"]
    jpp = attrs_20["judging_player_potential"]
    rot = prefs_map["squad_rotation"]
    buy = prefs_map["buying_players"]
    youth_trust = int(
        max(
            10,
            min(
                99,
                round((wwy * 3.0 + jpp * 1.2 + rot * 1.0 + (21 - buy) * 0.8) / 6.0 * 5.0),
            ),
        )
    )

    coaching_score = round(
        (
            attrs_20["attacking_coaching"]
            + attrs_20["defending_coaching"]
            + attrs_20["tactical_coaching"]
            + attrs_20["technical_coaching"]
            + attrs_20["mental_coaching"]
        )
        / 5.0
        * 5.0,
        1,
    )
    tactical_score = round(
        (attrs_20["tactical_knowledge"] * 0.6 + attrs_20["tactical_style_knowledge"] * 0.4) * 5.0,
        1,
    )
    man_mgmt_score = round(
        (
            attrs_20["people_management"] * 0.4
            + attrs_20["motivating"] * 0.35
            + attrs_20["level_of_discipline"] * 0.25
        )
        * 5.0,
        1,
    )

    if youth_trust >= 78 and coaching_score >= 65:
        archetype_tr = "Genç Gelişim & Sistem İnşacısı"
    elif prefs_map["trigger_press"] >= 15 and prefs_map["tempo"] >= 14:
        archetype_tr = "Modern Yüksek Pres & Geçiş Taktisyeni"
    elif prefs_map["patience"] >= 15 and prefs_map["directness"] <= 9:
        archetype_tr = "Topa Sahip Olma & Pozisyonel Oyun Hocası"
    elif attrs_20["people_management"] >= 15 and attrs_20["motivating"] >= 15:
        archetype_tr = "Karizmatik Lider & Yıldız Yöneticisi"
    elif attrs_20["level_of_discipline"] >= 15 and prefs_map["attacking"] <= 10:
        archetype_tr = "Disiplinli & Pragmatik Sonuç Hocası"
    else:
        archetype_tr = "Dengeli Taktisyen & Saha İçi Teknik Direktör"

    hot = prefs_map["hardness_of_training"]
    if hot >= 15:
        training_tr = f"Yüksek Yoğunluklu / Fiziksel ({hot}/20)"
    elif hot >= 10:
        training_tr = f"Dengeli / Taktik Odaklı ({hot}/20)"
    else:
        training_tr = f"Hafif / Teknik & Top Odaklı ({hot}/20)"

    if rot >= 15:
        rotation_tr = f"Geniş Rotasyoncu ({rot}/20)"
    elif rot >= 10:
        rotation_tr = f"Dengeli Kadro İstikrarı ({rot}/20)"
    else:
        rotation_tr = f"Sabit İlk 11 Tercihli ({rot}/20)"

    r4 = int(staff_member.unknown.get("r4", 0))
    role_info = STAFF_ROLE_MAP.get(r4, {"tr": f"Teknik Ekip (Kod {r4})", "en": "Staff"})
    role_tr = role_info["tr"]
    if r4 == 0 and getattr(staff_member, "list_indexes", ()):
        first_idx = staff_member.list_indexes[0]
        if first_idx == 1:
            role_tr = "Antrenör / Teknik Ekip"
    nat_id = getattr(staff_member, "nation_id", None)
    nat_tr = FM26_NATIONS.get(nat_id, {}).get("tr", f"Ülke #{nat_id}") if nat_id else "-"

    return CoachTacticalProfile(
        staff_uid=staff_member.uid,
        name=staff_member.name or f"Staff #{staff_member.uid}",
        age=getattr(staff_member, "age", None),
        nation_id=nat_id,
        nation_tr=nat_tr,
        club_uid=getattr(staff_member, "club_uid", None),
        club_name=getattr(staff_member, "club_name", None),
        role_code=r4,
        role_tr=role_tr,
        current_ability=_staff_ca(staff_member),
        potential_ability=_staff_pa(staff_member),
        wage_weekly=int(staff_member.wage or 0),
        contract_end=str(staff_member.contract_end) if getattr(staff_member, "contract_end", None) else None,
        primary_style_key=primary_key,
        primary_style_tr=primary_spec.name_tr,
        primary_style_en=primary_spec.name_en,
        style_code=primary_spec.style_code,
        style_description_tr=primary_spec.description_tr,
        secondary_style_key=secondary_key,
        secondary_style_tr=secondary_spec.name_tr,
        preferred_formation=preferred_formation,
        natural_mentality=mentality,
        mentality_tr=MENTALITY_LABELS_TR.get(mentality, "Dengeli"),
        archetype_tr=archetype_tr,
        training_style_tr=training_tr,
        rotation_style_tr=rotation_tr,
        youth_trust_score=youth_trust,
        coaching_score=coaching_score,
        tactical_score=tactical_score,
        man_management_score=man_mgmt_score,
        style_scores=style_scores,
        preferences=prefs_map,
        key_attributes_20=attrs_20,
    )


# ---------------------------------------------------------------------------
# 6. Player Style DNA & Slot Evaluation Helpers
# ---------------------------------------------------------------------------

def score_player_for_style(player: Any, style_key: str) -> float:
    """Compute how well a player's attributes (`1..20` scale) fit a given FM27 tactical style (`0..100`)."""
    spec = FM27_TACTICAL_STYLES.get(style_key, FM27_TACTICAL_STYLES["gegenpress"])
    if _player_pos(player, "gk") >= 15:
        kicking = _player_attr(player, "kicking", 10)
        rushing = _player_attr(player, "rushing_out", 10)
        comp = _player_attr(player, "composure", 10)
        refl = _player_attr(player, "reflexes", 10)
        cmd = _player_attr(player, "command_of_area", 10)
        if style_key in ("gegenpress", "tiki_taka", "vertical_tiki_taka", "control_possession"):
            val = (refl * 1.8 + kicking * 1.6 + comp * 1.5 + rushing * 1.3 + cmd * 1.2) / 7.4
        else:
            val = (refl * 2.0 + cmd * 1.8 + _player_attr(player, "handling", 10) * 1.6 + _player_attr(player, "positioning", 10) * 1.5) / 6.9
        return round(min(99.0, max(20.0, val * 5.0)), 1)

    total = 0.0
    w_sum = 0.0
    for attr_name, w in spec.player_dna_weights.items():
        if attr_name == "pressing_focus":
            v = (_player_attr(player, "aggression", 10) + _player_attr(player, "bravery", 10)) / 2.0
        else:
            v = float(_player_attr(player, attr_name, 10))
        total += v * w
        w_sum += w
    avg_20 = total / max(1.0, w_sum)
    return round(min(99.0, max(20.0, avg_20 * 5.0)), 1)


def score_player_for_slot(
    player: Any,
    slot: FormationSlotSpec,
    coach_profile: CoachTacticalProfile,
) -> tuple[int, float, float, float]:
    """Return `(pos_rating, style_dna_score, role_attr_score, composite_slot_score)` for a player in a slot."""
    best_pri = max((_player_pos(player, p) for p in slot.primary_pos), default=1)
    best_sec = max((_player_pos(player, p) for p in slot.secondary_pos), default=1) if slot.secondary_pos else 1
    pos_rating = max(best_pri, best_sec - 2)

    if best_pri >= 18:
        pos_mult = 1.0
    elif best_pri >= 15:
        pos_mult = 0.94
    elif best_sec >= 17:
        pos_mult = 0.89
    elif pos_rating >= 12:
        pos_mult = 0.78
    elif pos_rating >= 8:
        pos_mult = 0.55
    else:
        pos_mult = 0.25

    style_dna = score_player_for_style(player, coach_profile.primary_style_key)

    role_vals = [float(_player_attr(player, a, 10)) for a in slot.key_attrs]
    role_attr_score = round((sum(role_vals) / max(1, len(role_vals))) * 5.0, 1)

    ca = float(_player_ca(player) or 100)
    pa = float(_player_pa(player) or ca)
    age = getattr(player, "age", 25) or 25

    youth_bonus = 0.0
    if age <= 21 and pa > ca and coach_profile.youth_trust_score >= 65:
        youth_bonus = min(6.0, (pa - ca) * 0.12 * (coach_profile.youth_trust_score / 100.0))

    ca_norm = min(99.0, (ca / 180.0) * 100.0)
    raw_composite = (ca_norm * 0.50 + role_attr_score * 0.28 + style_dna * 0.22 + youth_bonus) * pos_mult
    return pos_rating, style_dna, role_attr_score, round(min(99.0, raw_composite), 1)


# ---------------------------------------------------------------------------
# 7. Coach–Squad Tactical Fit & Autonomous 26-Man Lineup Selector
# ---------------------------------------------------------------------------

def _resolve_coach(save: FM26Save, coach_uid_or_name: int | str | None, club_uid: int) -> CoachTacticalProfile:
    staff_rows = save.table("staff")
    if coach_uid_or_name is not None:
        if isinstance(coach_uid_or_name, int) or str(coach_uid_or_name).strip().isdigit():
            q_uid = int(str(coach_uid_or_name).strip())
            for st in staff_rows:
                if st.uid == q_uid:
                    return derive_coach_tactical_profile(st)
        q_str = str(coach_uid_or_name).strip().lower()
        exact = None
        partial = None
        for st in staff_rows:
            for nm in (st.name, st.full_name, st.common_name):
                if nm:
                    nml = nm.lower()
                    if nml == q_str:
                        exact = st
                        break
                    if partial is None and q_str in nml:
                        partial = st
            if exact is not None:
                break
        chosen = exact or partial
        if chosen is not None:
            return derive_coach_tactical_profile(chosen)
        raise KeyError(f"Teknik direktör / antrenör bulunamadı: {coach_uid_or_name!r}")

    club_staff = [
        st
        for st in staff_rows
        if st.club_uid == club_uid
        and not st.is_human_manager
        and st.preferences is not None
        and (st.unknown.get("r4") in (16, 2, 20, 10) or (1 in (st.list_indexes or ())))
    ]
    if not club_staff:
        club_staff = [st for st in staff_rows if st.club_uid == club_uid and st.preferences is not None]
    if club_staff:
        club_staff.sort(
            key=lambda s: (
                1 if s.unknown.get("r4") in (16, 2) else 0,
                _staff_ca(s),
            ),
            reverse=True,
        )
        return derive_coach_tactical_profile(club_staff[0])

    valid = [st for st in staff_rows if st.preferences is not None]
    valid.sort(key=lambda s: _staff_ca(s), reverse=True)
    return derive_coach_tactical_profile(valid[0])


def _ensure_save(save_or_path: FM26Save | str | Path) -> FM26Save:
    if isinstance(save_or_path, FM26Save):
        return save_or_path
    return FM26Save(Path(save_or_path))


def analyze_coach_squad_fit(
    save: FM26Save | str | Path,
    *,
    club_uid: int | None = None,
    coach_uid_or_name: int | str | None = None,
    coach_profile: CoachTacticalProfile | None = None,
    club_players: Sequence[Any] | None = None,
    wage_by_uid: Mapping[int, int] | None = None,
) -> CoachSquadFitReport:
    """Evaluate a club's roster against a coach's natural tactical identity and pick their autonomous 26-man squad."""
    save = _ensure_save(save)
    if club_uid is None:
        mc = save.table("managed-clubs")
        club_uid = mc[0].club_uid if mc else 1871

    clubs = {c.uid: c for c in save.table("clubs")}
    club_name = clubs[club_uid].name if club_uid in clubs else f"Club #{club_uid}"

    profile = coach_profile or _resolve_coach(save, coach_uid_or_name, club_uid)
    formation_slots = FM27_FORMATIONS.get(profile.preferred_formation, FM27_FORMATIONS["4-2-3-1"])

    if club_players is None:
        all_players = save.table("players")
        club_players = [
            p
            for p in all_players
            if p.club_uid == club_uid and (p.team_slot is None or p.team_slot == 0 or _player_ca(p) >= 115)
        ]
        if len(club_players) < 18:
            club_players = [p for p in all_players if p.club_uid == club_uid]

    if wage_by_uid is None:
        wage_by_uid = {}
        for p in club_players:
            if p.contract and p.contract.wage:
                wage_by_uid[p.uid] = int(p.contract.wage)

    player_by_uid = {p.uid: p for p in club_players}
    slot_candidates: dict[int, list[tuple[int, int, float, float, float]]] = {}
    for slot in formation_slots:
        scored: list[tuple[int, int, float, float, float]] = []
        for p in club_players:
            pos_r, s_dna, r_attr, comp = score_player_for_slot(p, slot, profile)
            scored.append((p.uid, pos_r, s_dna, r_attr, comp))
        scored.sort(key=lambda x: x[4], reverse=True)
        slot_candidates[slot.slot_index] = scored

    slot_order = sorted(
        range(len(formation_slots)),
        key=lambda idx: (
            0 if idx == 0 else 1,
            sum(1 for item in slot_candidates[idx] if item[1] >= 15),
        ),
    )
    used_uids: set[int] = set()
    assigned_by_slot: dict[int, SquadSlotAssignment] = {}

    sorted_cas = sorted((_player_ca(p) for p in club_players), reverse=True)
    club_xi_baseline_ca = sum(sorted_cas[:11]) / max(1, min(11, len(sorted_cas)))

    for s_idx in slot_order:
        slot = formation_slots[s_idx]
        picked = None
        for cand in slot_candidates[s_idx]:
            if cand[0] not in used_uids:
                picked = cand
                break
        if picked is None and slot_candidates[s_idx]:
            picked = slot_candidates[s_idx][0]
        if picked is None:
            continue

        p_uid, pos_r, s_dna, r_attr, comp = picked
        used_uids.add(p_uid)
        p_obj = player_by_uid[p_uid]
        p_ca = _player_ca(p_obj)
        p_pa = _player_pa(p_obj)

        if pos_r < 14:
            status = "OUT_OF_POSITION"
            note_tr = f"Doğal mevki uyumu düşük ({pos_r}/20) — bu bölgeye doğal oyuncu şart"
        elif p_ca < club_xi_baseline_ca - 9 or comp < 64.0:
            status = "WEAK_LINK"
            note_tr = f"İlk 11 kalite ortalamasının ({club_xi_baseline_ca:.0f} CA) altında — transferle güçlendirilmeli"
        elif p_ca >= club_xi_baseline_ca + 4 and s_dna >= 72.0:
            status = "ELITE"
            note_tr = "Hocanın sisteminin kilit yıldızı"
        else:
            status = "SOLID"
            note_tr = "Hocanın oyun planına uyumlu ilk 11 oyuncusu"

        assigned_by_slot[s_idx] = SquadSlotAssignment(
            slot_index=s_idx,
            slot_code=slot.code,
            slot_label_tr=slot.label_tr,
            ip_role_tr=slot.ip_role_tr,
            oop_role_tr=slot.oop_role_tr,
            player_uid=p_uid,
            player_name=p_obj.name or f"Player #{p_uid}",
            age=p_obj.age,
            ca=p_ca,
            pa=p_pa,
            wage_weekly=wage_by_uid.get(p_uid, 0),
            pos_rating=pos_r,
            style_dna_score=s_dna,
            role_attr_score=r_attr,
            slot_fit_score=comp,
            status=status,
            note_tr=note_tr,
        )

    starting_xi = tuple(assigned_by_slot[i] for i in sorted(assigned_by_slot))

    remaining = [p for p in club_players if p.uid not in used_uids]
    rem_gks = sorted(
        [p for p in remaining if _player_pos(p, "gk") >= 15],
        key=_player_ca,
        reverse=True,
    )
    bench_list: list[dict[str, Any]] = []
    if rem_gks:
        bgk = rem_gks[0]
        used_uids.add(bgk.uid)
        bench_list.append({
            "bench_slot": 12,
            "player_uid": bgk.uid,
            "player_name": bgk.name,
            "age": bgk.age,
            "position": "GK",
            "ca": _player_ca(bgk),
            "pa": _player_pa(bgk),
            "style_dna_score": score_player_for_style(bgk, profile.primary_style_key),
            "wage_weekly": wage_by_uid.get(bgk.uid, 0),
        })

    outfield_rem = [p for p in club_players if p.uid not in used_uids]
    outfield_scored: list[tuple[float, Any, float]] = []
    for p in outfield_rem:
        s_dna = score_player_for_style(p, profile.primary_style_key)
        ca_v = float(_player_ca(p))
        pa_v = float(_player_pa(p) or ca_v)
        y_bonus = 8.0 if (p.age and p.age <= 21 and pa_v >= ca_v + 15 and profile.youth_trust_score >= 65) else 0.0
        b_score = ca_v * 0.65 + s_dna * 0.35 + y_bonus
        outfield_scored.append((b_score, p, s_dna))
    outfield_scored.sort(key=lambda x: x[0], reverse=True)

    for b_idx, (_bs, p, s_dna) in enumerate(outfield_scored[: (15 - len(bench_list))], start=12 + len(bench_list)):
        used_uids.add(p.uid)
        best_pos = max(
            ("GK", "DL", "DC", "DR", "WBL", "WBR", "DM", "ML", "MC", "MR", "AML", "AMC", "AMR", "STC"),
            key=lambda code: _player_pos(p, code.lower()),
        )
        bench_list.append({
            "bench_slot": b_idx,
            "player_uid": p.uid,
            "player_name": p.name,
            "age": p.age,
            "position": best_pos,
            "ca": _player_ca(p),
            "pa": _player_pa(p),
            "style_dna_score": s_dna,
            "wage_weekly": wage_by_uid.get(p.uid, 0),
        })

    if starting_xi:
        formation_cov = sum(min(20, s.pos_rating) / 20.0 * 100.0 for s in starting_xi) / len(starting_xi)
        style_dna_avg = sum(s.style_dna_score for s in starting_xi) / len(starting_xi)
        slot_fit_avg = sum(s.slot_fit_score for s in starting_xi) / len(starting_xi)
        xi_avg_ca = sum(s.ca for s in starting_xi) / len(starting_xi)
        overall_compat = round(formation_cov * 0.35 + style_dna_avg * 0.35 + slot_fit_avg * 0.30, 1)
    else:
        formation_cov = style_dna_avg = xi_avg_ca = overall_compat = 0.0

    sorted_slots_by_weakness = sorted(
        starting_xi,
        key=lambda s: (
            0 if s.status == "OUT_OF_POSITION" else (1 if s.status == "WEAK_LINK" else 2),
            s.slot_fit_score,
        ),
    )
    transfer_needs: list[dict[str, Any]] = []
    for s in sorted_slots_by_weakness:
        if s.status in ("OUT_OF_POSITION", "WEAK_LINK") or len(transfer_needs) < 2:
            spec = formation_slots[s.slot_index]
            transfer_needs.append({
                "slot_index": s.slot_index,
                "slot_code": s.slot_code,
                "slot_label_tr": s.slot_label_tr,
                "required_role_tr": s.ip_role_tr,
                "current_starter": s.player_name,
                "current_starter_ca": s.ca,
                "current_slot_fit": s.slot_fit_score,
                "urgency": "KRİTİK" if s.status == "OUT_OF_POSITION" else ("YÜKSEK" if s.status == "WEAK_LINK" else "ORTA"),
                "reason_tr": s.note_tr,
                "target_positions": spec.primary_pos,
                "key_attributes": spec.key_attrs,
            })
        if len(transfer_needs) >= 4:
            break

    surplus_list: list[dict[str, Any]] = []
    xi_uids = {s.player_uid for s in starting_xi}
    for p in club_players:
        if p.uid in xi_uids:
            continue
        p_ca = _player_ca(p)
        p_pa = _player_pa(p)
        p_wage = wage_by_uid.get(p.uid, 0)
        s_dna = score_player_for_style(p, profile.primary_style_key)
        best_slot_pos = max(
            (max(_player_pos(p, pos) for pos in sl.primary_pos) for sl in formation_slots),
            default=1,
        )
        if best_slot_pos < 14 and p_ca >= 115:
            surplus_list.append({
                "player_uid": p.uid,
                "player_name": p.name,
                "age": p.age,
                "ca": p_ca,
                "pa": p_pa,
                "wage_weekly": p_wage,
                "style_dna_score": s_dna,
                "action_tr": "Satış Listesi (Formasyonda Doğal Mevkisi Yok)",
            })
        elif p.age and p.age <= 21 and p_pa >= p_ca + 20 and p.uid not in used_uids:
            surplus_list.append({
                "player_uid": p.uid,
                "player_name": p.name,
                "age": p.age,
                "ca": p_ca,
                "pa": p_pa,
                "wage_weekly": p_wage,
                "style_dna_score": s_dna,
                "action_tr": "Kiralık Gönder (Düzenli İlk 11 Oynamalı)",
            })
        elif p_wage >= 35_000 and p.uid not in used_uids and (p.age or 25) >= 24:
            surplus_list.append({
                "player_uid": p.uid,
                "player_name": p.name,
                "age": p.age,
                "ca": p_ca,
                "pa": p_pa,
                "wage_weekly": p_wage,
                "style_dna_score": s_dna,
                "action_tr": "Satış / Maaş Yükü Azaltma Adayı",
            })

    surplus_list.sort(key=lambda x: (x["wage_weekly"], x["ca"]), reverse=True)

    return CoachSquadFitReport(
        club_uid=club_uid,
        club_name=club_name,
        coach=profile,
        formation=profile.preferred_formation,
        overall_compatibility=overall_compat,
        formation_coverage_score=round(formation_cov, 1),
        style_dna_score=round(style_dna_avg, 1),
        starting_xi_avg_ca=round(xi_avg_ca, 1),
        starting_xi=starting_xi,
        bench=tuple(bench_list),
        priority_transfer_needs=tuple(transfer_needs),
        surplus_candidates=tuple(surplus_list[:12]),
    )


# ---------------------------------------------------------------------------
# 8. Head Coach Scouting & Candidate Ranking Engine
# ---------------------------------------------------------------------------

def scan_coach_candidates(
    save: FM26Save | str | Path,
    *,
    club_uid: int | None = None,
    desired_style: str | None = None,
    min_ca: int = 125,
    max_age: int = 72,
    max_wage_weekly: int | None = None,
    only_available: bool = False,
    top_n: int = 20,
) -> list[CoachCandidateRow]:
    """Scan all coaches/managers in the save and rank them by style fit, coaching quality, and squad compatibility."""
    save = _ensure_save(save)
    if club_uid is None:
        mc = save.table("managed-clubs")
        club_uid = mc[0].club_uid if mc else 1871

    all_players = save.table("players")
    club_players = [
        p
        for p in all_players
        if p.club_uid == club_uid and (p.team_slot is None or p.team_slot == 0 or _player_ca(p) >= 115)
    ]
    wage_by_uid: dict[int, int] = {}
    for p in club_players:
        if p.contract and p.contract.wage:
            wage_by_uid[p.uid] = int(p.contract.wage)

    norm_style: str | None = None
    if desired_style:
        ds = desired_style.strip().lower().replace("-", "_").replace(" ", "_")
        for k, spec in FM27_TACTICAL_STYLES.items():
            if ds in (k, spec.name_en.lower().replace(" ", "_"), spec.style_code.lower()) or ds in spec.name_tr.lower():
                norm_style = k
                break

    is_womens_club = club_uid >= 2_000_000_000
    staff_rows = save.table("staff")
    pre_candidates: list[tuple[float, CoachTacticalProfile]] = []

    for st in staff_rows:
        if st.is_human_manager or st.preferences is None:
            continue
        if st.club_uid is not None and (st.club_uid >= 2_000_000_000) != is_womens_club:
            continue
        if not is_womens_club and 2_000_090_000 <= st.uid < 2_000_500_000:
            continue
        ca = _staff_ca(st)
        if ca < min_ca:
            continue
        if st.age is not None and st.age > max_age:
            continue
        r4 = int(st.unknown.get("r4", 0))
        if r4 not in (16, 2, 10, 20, 0):
            continue
        if r4 == 0 and st.list_indexes and 1 not in st.list_indexes:
            continue
        if only_available and st.has_contract:
            continue
        if max_wage_weekly is not None and (st.wage or 0) > max_wage_weekly:
            continue

        prof = derive_coach_tactical_profile(st)
        if norm_style is not None:
            style_match = prof.style_scores.get(norm_style, 50.0)
            if prof.primary_style_key != norm_style and prof.secondary_style_key != norm_style and style_match < 74.0:
                continue
        else:
            style_match = prof.style_scores.get(prof.primary_style_key, 80.0)

        pre_score = (ca / 200.0) * 45.0 + prof.tactical_score * 0.25 + prof.coaching_score * 0.15 + style_match * 0.15
        pre_candidates.append((pre_score, prof))

    pre_candidates.sort(key=lambda x: x[0], reverse=True)
    shortlist = pre_candidates[: max(top_n * 3, 45)]

    clock_year = (save.info.game_date or datetime.date(2027, 11, 1)).year
    results: list[CoachCandidateRow] = []
    for _pre, prof in shortlist:
        fit = analyze_coach_squad_fit(
            save,
            club_uid=club_uid,
            coach_profile=prof,
            club_players=club_players,
            wage_by_uid=wage_by_uid,
        )
        style_match = prof.style_scores.get(norm_style, prof.style_scores[prof.primary_style_key]) if norm_style else prof.style_scores[prof.primary_style_key]
        weak_slots = [w for w in fit.priority_transfer_needs if w["urgency"] in ("KRİTİK", "YÜKSEK")]
        weak_summary = ", ".join(f"{w['slot_code']} ({w['slot_label_tr']})" for w in weak_slots[:3]) or "Tam Uyum (Kritik Eksik Yok)"

        cur_wage = prof.wage_weekly
        est_wage = max(12_000, int(round((cur_wage * 1.15 if cur_wage > 0 else (prof.current_ability ** 2) * 1.4) / 500.0) * 500))
        if not prof.contract_end or prof.club_uid == club_uid:
            est_comp = 0
        else:
            end_yr = int(prof.contract_end[:4]) if prof.contract_end[:4].isdigit() else (clock_year + 1)
            years_left = max(0.5, min(4.0, float(end_yr - clock_year)))
            est_comp = int(round((cur_wage * 52 * years_left * 0.65) / 10_000.0) * 10_000)

        dof_score = round(
            (prof.current_ability / 200.0 * 100.0) * 0.32
            + fit.overall_compatibility * 0.28
            + style_match * 0.20
            + prof.tactical_score * 0.12
            + prof.coaching_score * 0.08,
            1,
        )
        results.append(
            CoachCandidateRow(
                rank=0,
                profile=prof,
                squad_compatibility=fit.overall_compatibility,
                weak_positions_count=len(weak_slots),
                weak_positions_summary=weak_summary,
                style_match_score=round(style_match, 1),
                estimated_compensation=est_comp,
                estimated_weekly_wage=est_wage,
                dof_total_score=dof_score,
            )
        )

    results.sort(key=lambda r: r.dof_total_score, reverse=True)
    return [
        CoachCandidateRow(
            rank=idx + 1,
            profile=r.profile,
            squad_compatibility=r.squad_compatibility,
            weak_positions_count=r.weak_positions_count,
            weak_positions_summary=r.weak_positions_summary,
            style_match_score=r.style_match_score,
            estimated_compensation=r.estimated_compensation,
            estimated_weekly_wage=r.estimated_weekly_wage,
            dof_total_score=r.dof_total_score,
        )
        for idx, r in enumerate(results[:top_n])
    ]


# ---------------------------------------------------------------------------
# 9. Coach-Aligned Transfer Target Recommender
# ---------------------------------------------------------------------------

def recommend_transfer_targets(
    save: FM26Save | str | Path,
    *,
    club_uid: int | None = None,
    coach_uid_or_name: int | str | None = None,
    slot_code: str | None = None,
    max_transfer_value: int | None = None,
    max_wage_weekly: int | None = None,
    top_n_per_slot: int = 8,
) -> dict[str, Any]:
    """Recommend realistic transfer targets tailored to the coach's tactical style and weakest squad slots."""
    save = _ensure_save(save)
    if club_uid is None:
        mc = save.table("managed-clubs")
        club_uid = mc[0].club_uid if mc else 1871

    fin_rows = [f for f in save.table("finances") if f.club_uid == club_uid]
    latest_fin = fin_rows[-1] if fin_rows else None
    rem_budget = int(latest_fin.transfer_budget_remaining or 25_000_000) if latest_fin else 25_000_000
    if max_transfer_value is None:
        max_transfer_value = max(35_000_000, int(rem_budget * 1.5))

    fit_report = analyze_coach_squad_fit(save, club_uid=club_uid, coach_uid_or_name=coach_uid_or_name)
    coach = fit_report.coach
    formation_slots = FM27_FORMATIONS.get(coach.preferred_formation, FM27_FORMATIONS["4-2-3-1"])

    if slot_code:
        sc_upper = slot_code.strip().upper()
        target_slots = [sl for sl in formation_slots if sl.code == sc_upper or sc_upper.lower() in sl.primary_pos]
        if not target_slots:
            target_slots = [formation_slots[0]]
    else:
        need_indices = [n["slot_index"] for n in fit_report.priority_transfer_needs[:3]]
        target_slots = [formation_slots[i] for i in need_indices] if need_indices else list(formation_slots[:3])

    starter_by_slot = {s.slot_index: s for s in fit_report.starting_xi}
    min_starter_ca = max(122, int(fit_report.starting_xi_avg_ca - 6))

    is_womens_club = club_uid >= 2_000_000_000
    clock = save.info.game_date or datetime.date(2027, 11, 6)
    all_players = save.table("players")

    recommendations_by_slot: list[dict[str, Any]] = []
    wonderkids: list[dict[str, Any]] = []
    expiring_bargains: list[dict[str, Any]] = []
    seen_wk: set[int] = set()
    seen_bg: set[int] = set()

    for slot in target_slots:
        current_starter = starter_by_slot.get(slot.slot_index)
        baseline_ca = current_starter.ca if current_starter else min_starter_ca
        slot_targets: list[dict[str, Any]] = []

        for p in all_players:
            if p.club_uid == club_uid:
                continue
            if p.club_uid is not None and (p.club_uid >= 2_000_000_000) != is_womens_club:
                continue
            if not is_womens_club and 2_000_090_000 <= p.uid < 2_000_500_000:
                continue
            if p.club_uid is None and p.contract and any(
                e.club_uid is not None and (e.club_uid >= 2_000_000_000) != is_womens_club
                for e in p.contract.chain
            ):
                continue
            ca = _player_ca(p)
            pa = _player_pa(p)
            if ca < max(115, baseline_ca - 8) and not (p.age and p.age <= 21 and pa >= baseline_ca + 8):
                continue

            best_pri = max((_player_pos(p, pos) for pos in slot.primary_pos), default=1)
            if best_pri < 16:
                continue

            t_val = int(p.transfer_value or 0)
            if t_val > max_transfer_value:
                continue

            c_row = p.contract
            p_wage = int(c_row.wage or 0) if c_row else 0
            if max_wage_weekly is not None and p_wage > max_wage_weekly:
                continue

            pos_r, s_dna, r_attr, slot_fit = score_player_for_slot(p, slot, coach)
            if s_dna < 65.0 or slot_fit < 64.0:
                continue

            c_end = c_row.end if c_row else None
            months_left = ((c_end.year - clock.year) * 12 + (c_end.month - clock.month)) if c_end else 36

            value_efficiency = max(0.0, 100.0 - (t_val / max(1, max_transfer_value)) * 40.0)
            target_score = round(slot_fit * 0.45 + s_dna * 0.25 + (ca / 200.0 * 100.0) * 0.20 + value_efficiency * 0.10, 1)

            row_dict = {
                "player_uid": p.uid,
                "name": p.name,
                "age": p.age,
                "club_name": p.club_name or "Serbest",
                "ca": ca,
                "pa": pa,
                "transfer_value": t_val,
                "wage_weekly": p_wage,
                "contract_end": str(c_end) if c_end else None,
                "months_left": months_left,
                "slot_code": slot.code,
                "slot_label_tr": slot.label_tr,
                "pos_rating": pos_r,
                "style_dna_score": s_dna,
                "role_attr_score": r_attr,
                "slot_fit_score": slot_fit,
                "target_score": target_score,
                "upgrade_vs_starter_ca": ca - baseline_ca,
            }

            if ca >= baseline_ca - 2:
                slot_targets.append(row_dict)

            if p.age and p.age <= 21 and pa >= max(148, baseline_ca + 4) and p.uid not in seen_wk:
                seen_wk.add(p.uid)
                wonderkids.append(row_dict)

            if months_left <= 12 and ca >= baseline_ca - 3 and p.uid not in seen_bg:
                seen_bg.add(p.uid)
                expiring_bargains.append(row_dict)

        slot_targets.sort(key=lambda x: x["target_score"], reverse=True)
        recommendations_by_slot.append({
            "slot_index": slot.slot_index,
            "slot_code": slot.code,
            "slot_label_tr": slot.label_tr,
            "ip_role_tr": slot.ip_role_tr,
            "current_starter": current_starter.player_name if current_starter else "-",
            "current_starter_ca": baseline_ca,
            "targets": slot_targets[:top_n_per_slot],
        })

    wonderkids.sort(key=lambda x: (x["pa"], x["style_dna_score"]), reverse=True)
    expiring_bargains.sort(key=lambda x: (x["target_score"], -x["months_left"]), reverse=True)

    return {
        "club_uid": club_uid,
        "club_name": fit_report.club_name,
        "coach_name": coach.name,
        "coach_style_tr": coach.primary_style_tr,
        "coach_formation": coach.preferred_formation,
        "transfer_budget_remaining": rem_budget,
        "max_transfer_value_filter": max_transfer_value,
        "slots": recommendations_by_slot,
        "wonderkids": wonderkids[:10],
        "expiring_bargains": expiring_bargains[:10],
    }


# ---------------------------------------------------------------------------
# 10. Full DoF Club Hub & Capology Audit
# ---------------------------------------------------------------------------

def build_dof_dashboard(
    save: FM26Save | str | Path,
    *,
    club_uid: int | None = None,
    coach_uid_or_name: int | str | None = None,
) -> dict[str, Any]:
    """Build the comprehensive Director of Football Club Hub, Capology, Contract Risk, and Squad Fit summary."""
    save = _ensure_save(save)
    if club_uid is None:
        mc = save.table("managed-clubs")
        club_uid = mc[0].club_uid if mc else 1871

    clock = save.info.game_date or datetime.date(2027, 11, 6)
    clubs = {c.uid: c for c in save.table("clubs")}
    club = clubs.get(club_uid)

    fin_rows = [f for f in save.table("finances") if f.club_uid == club_uid]
    latest_fin = fin_rows[-1] if fin_rows else None
    finances_summary = {
        "balance": int(latest_fin.balance or 0) if latest_fin else 0,
        "transfer_budget_allocated": int(latest_fin.transfer_budget_allocated or 0) if latest_fin else 0,
        "transfer_budget_remaining": int(latest_fin.transfer_budget_remaining or 0) if latest_fin else 0,
        "wage_budget_weekly": int(latest_fin.wage_budget_weekly or 0) if latest_fin else 0,
        "wage_payroll_weekly": int(latest_fin.wage_payroll_weekly or 0) if latest_fin else 0,
        "wage_free_weekly": (
            int(latest_fin.wage_budget_weekly or 0) - int(latest_fin.wage_payroll_weekly or 0)
            if latest_fin
            else 0
        ),
    }

    club_players = [p for p in save.table("players") if p.club_uid == club_uid]
    wage_by_uid = {p.uid: int(p.contract.wage or 0) for p in club_players if p.contract and p.contract.wage}

    fit_report = analyze_coach_squad_fit(
        save,
        club_uid=club_uid,
        coach_uid_or_name=coach_uid_or_name,
        club_players=[
            p for p in club_players if (p.team_slot is None or p.team_slot == 0 or _player_ca(p) >= 115)
        ],
        wage_by_uid=wage_by_uid,
    )
    xi_uids = {s.player_uid for s in fit_report.starting_xi}

    expiring_12m: list[dict[str, Any]] = []
    expiring_24m: list[dict[str, Any]] = []
    top_earners: list[dict[str, Any]] = []

    for p in club_players:
        c_row = p.contract
        if c_row is None or p.on_loan:
            continue
        w = int(c_row.wage or 0)
        c_end = c_row.end
        months_left = ((c_end.year - clock.year) * 12 + (c_end.month - clock.month)) if c_end else 99
        in_xi = p.uid in xi_uids
        rel_clause = None
        for cl in c_row.clauses:
            if cl.value and cl.kind.raw in (0x00, 0x10, 0x11, 0x12):
                rel_clause = int(cl.value)
                break
        entry = {
            "player_uid": p.uid,
            "name": p.name,
            "age": p.age,
            "ca": _player_ca(p),
            "pa": _player_pa(p),
            "wage_weekly": w,
            "contract_end": str(c_end) if c_end else None,
            "months_left": months_left,
            "squad_status": c_row.squad_status.label.name if c_row.squad_status else "-",
            "in_coach_starting_xi": in_xi,
            "release_clause": rel_clause,
        }
        top_earners.append(entry)
        if months_left <= 12 and _player_ca(p) >= 115:
            expiring_12m.append(entry)
        elif 12 < months_left <= 24 and _player_ca(p) >= 122:
            expiring_24m.append(entry)

    top_earners.sort(key=lambda x: x["wage_weekly"], reverse=True)
    expiring_12m.sort(key=lambda x: x["ca"], reverse=True)
    expiring_24m.sort(key=lambda x: x["ca"], reverse=True)

    club_staff = [st for st in save.table("staff") if st.club_uid == club_uid and not st.is_human_manager]
    club_staff.sort(key=_staff_ca, reverse=True)
    key_staff: list[dict[str, Any]] = []
    for st in club_staff[:12]:
        r4 = int(st.unknown.get("r4", 0))
        role_info = STAFF_ROLE_MAP.get(r4, {"tr": f"Teknik Ekip ({r4})", "dept": "Coaching"})
        key_staff.append({
            "uid": st.uid,
            "name": st.name,
            "role_code": r4,
            "role_tr": role_info["tr"],
            "ca": _staff_ca(st),
            "pa": _staff_pa(st),
            "wage_weekly": int(st.wage or 0),
            "contract_end": str(st.contract_end) if st.contract_end else None,
        })

    return {
        "save_info": {
            "game": save.info.game,
            "build": save.info.build,
            "game_date": str(clock),
            "club_uid": club_uid,
            "club_name": club.name if club else f"Club #{club_uid}",
            "reputation": club.reputation if club else None,
        },
        "finances": finances_summary,
        "capology": {
            "top_earners": top_earners[:15],
            "expiring_12m": expiring_12m,
            "expiring_24m": expiring_24m,
        },
        "key_staff": key_staff,
        "coach_squad_fit": fit_report.to_dict(),
    }


# ---------------------------------------------------------------------------
# 11. Safe Working-Copy DoF Save Actions (Hire Coach & Autonomous Setup)
# ---------------------------------------------------------------------------

def hire_head_coach(
    save_path: str | Path,
    coach_uid_or_name: int | str,
    output_path: str | Path,
    *,
    club_uid: int | None = None,
    weekly_wage: int | None = None,
    contract_years: int = 3,
    deduct_compensation: bool = True,
    apply_autonomous_tactics_and_lineup: bool = True,
) -> dict[str, Any]:
    """Hire a Head Coach for the managed club and autonomously sync their tactical style, mentality,
    and 26-man lineup into a NEW output `.fm` save file (never modifying the source save in place).
    """
    src_path = Path(save_path).resolve()
    out_path = Path(output_path).resolve()
    if src_path == out_path:
        raise ValueError(
            "Güvenlik Koruması: Oyun açıkken veya orijinal kayıt üzerinde doğrudan üzerine yazma yapılamaz. "
            "Lütfen farklı bir çıktı yolu (ör. `*_DoF.fm`) belirtin."
        )

    save = FM26Save(src_path)
    if club_uid is None:
        mc = save.table("managed-clubs")
        club_uid = mc[0].club_uid if mc else 1871

    clubs = {c.uid: c for c in save.table("clubs")}
    club = clubs[club_uid]
    first_team_id = club.teams[0].team_id if club.teams else 1464

    fit_report = analyze_coach_squad_fit(save, club_uid=club_uid, coach_uid_or_name=coach_uid_or_name)
    coach = fit_report.coach
    clock = save.info.game_date or datetime.date(2027, 11, 6)

    new_wage = weekly_wage or max(15_000, int(round((coach.wage_weekly * 1.15 if coach.wage_weekly > 0 else (coach.current_ability ** 2) * 1.4) / 500.0) * 500))
    if not coach.contract_end or coach.club_uid == club_uid:
        compensation = 0
    else:
        end_yr = int(coach.contract_end[:4]) if coach.contract_end[:4].isdigit() else (clock_year := clock.year) + 1
        years_left = max(0.5, min(4.0, float(end_yr - clock.year)))
        compensation = int(round((coach.wage_weekly * 52 * years_left * 0.65) / 10_000.0) * 10_000)

    c_end_date = datetime.date(clock.year + contract_years, 6, 30)

    editor = FM26Editor(src_path)
    actions_log: list[dict[str, Any]] = []

    staff_mod = editor.edit_staff(
        coach.staff_uid,
        team_id=first_team_id,
        role_r4=2,
        wage=new_wage,
        contract_start=clock,
        contract_end=c_end_date,
    )
    actions_log.append({"step": "hire_coach_contract", **staff_mod})

    if coach.club_uid != club_uid:
        try:
            list_mod = editor.edit_club_staff_list(club_uid, slot=1, entry_index=0, new_staff_person_uid=coach.staff_uid)
            actions_log.append({"step": "register_club_staff_list", **list_mod})
        except Exception as exc:
            actions_log.append({"step": "register_club_staff_list_skipped", "reason": str(exc)})

    if deduct_compensation and compensation > 0:
        fin_rows = [f for f in save.table("finances") if f.club_uid == club_uid]
        if fin_rows:
            latest = fin_rows[-1]
            new_bal = int(latest.balance or 0) - compensation
            new_rem = max(0, int(latest.transfer_budget_remaining or 0) - compensation)
            fin_mod = editor.edit_club_finances(
                club_uid,
                balance=new_bal,
                transfer_budget_remaining=new_rem,
            )
            actions_log.append({"step": "deduct_compensation", "compensation": compensation, **fin_mod})

    if apply_autonomous_tactics_and_lineup:
        tactic_title = f"[DoF: {coach.name}] {coach.preferred_formation} {coach.primary_style_en}"
        try:
            tac_mod = editor.edit_tactic_record(
                0,
                mentality=coach.natural_mentality,
                style_code=coach.style_code,
                name=tactic_title,
            )
            actions_log.append({"step": "apply_coach_tactical_identity", **tac_mod})
        except Exception as exc:
            actions_log.append({"step": "apply_coach_tactical_identity_skipped", "reason": str(exc)})

        lineup_uids = [s.player_uid for s in fit_report.starting_xi] + [b["player_uid"] for b in fit_report.bench]
        lineup_applied = 0
        for slot_i, p_uid in enumerate(lineup_uids[:26]):
            try:
                editor.edit_tactics_lineup(slot_i, p_uid, team_block_index=0)
                lineup_applied += 1
            except Exception:
                break
        actions_log.append({"step": "apply_coach_autonomous_lineup", "slots_updated": lineup_applied})

    repack_info = editor.save(out_path, validate_output=False)
    return {
        "output_path": str(out_path),
        "club_uid": club_uid,
        "club_name": club.name,
        "hired_coach": coach.to_dict(),
        "weekly_wage": new_wage,
        "contract_end": str(c_end_date),
        "compensation_paid": compensation if deduct_compensation else 0,
        "squad_compatibility": fit_report.overall_compatibility,
        "autonomous_starting_xi": [asdict(s) for s in fit_report.starting_xi],
        "actions_log": actions_log,
        "repack_info": repack_info,
    }
