"""FM27 / FM26 All-in-One Pro Studio Web Application UI (Single-Page HTML/CSS/JS).

Designed as a bespoke, ultra-responsive, zero-lag Pro Football Analytics & Binary Studio:
- Pillar 1: Save & Pre-Game Databases Visualizer & Granular Field-by-Field Live Editor
  - Players: 6 Inspector Sub-Tabs (Identity/Club Transfer/Physical/Scale, All 52 Attributes with group controls,
    15 Positional Familiarity & 6D Role Suitability, 8 Personality & 64-bit Traits Bitmask, Full Contract +
    Bonuses + Individual Clauses Editor, Current Season Stats Editor + Optional Quick Presets)
  - Clubs, Finances, Sponsorships & Stadiums: 4 Inspector Sub-Tabs (Club Identity & Facilities, 11 Monthly
    Finance Fields & Monthly Ledger, Sponsorship Contracts Editor, 14-Field Stadium & Pitch Dimensions Editor)
  - Staff & DoF Center: 4 Inspector Sub-Tabs (Identity/Role r4/Contract, 26 Coaching/Scouting/Medical Attributes,
    17 Tactical Preferences & 8 Personality Attributes, DoF Analytics & Head Coach Hiring)
  - World, League Standings (Total/Home/Away), Tactics, 26-Slot Lineup, Transfer Windows, Hall of Fame,
    Name Pools, All 28 Save Tables, 81 Zstd Sections & Pre-Game Master DBs
- Pillar 2: Game Optimization Suite (14 Categorized Unity 6 / IL2CPP `boot.config` keys, Custom Key=Value Adder,
  Direct Raw `boot.config` Text Editor, 4 Optional Presets, Intro Video Bypass, URP & Disk Footprint)
- Pillar 3: Game File & Bundle Patcher (Custom `max_players` input + quick chips, 10 Named UI Sorting Patches,
  252 `StreamedTable` individual `0/1` switches, Visual `sugardaddy.edt` editor + `.edt`/`.lnc` Directive Builder)
- Cross-Cutting: Independent In-Game Term Localization Selector (21 Official `.ltc` Languages).
"""

from __future__ import annotations

STUDIO_HTML_PAGE = r"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FM27 / FM26 Pro Studio — Granular DB Editor, Optimizer & Binary Patcher</title>
<style>
:root {
  --bg-root: #060911;
  --bg-sidebar: #0a0f1c;
  --bg-surface: #0f1628;
  --bg-card: #131c31;
  --bg-card-hover: #18243f;
  --bg-input: #080d18;
  --border: #1e2b48;
  --border-bright: #2e436e;
  --text-main: #f1f5f9;
  --text-muted: #94a3b8;
  --text-dim: #64748b;
  --accent: #10b981;
  --accent-hover: #059669;
  --accent-soft: rgba(16, 185, 129, 0.14);
  --blue: #3b82f6;
  --blue-soft: rgba(59, 130, 246, 0.15);
  --purple: #8b5cf6;
  --purple-soft: rgba(139, 92, 246, 0.15);
  --amber: #f59e0b;
  --amber-soft: rgba(245, 158, 11, 0.15);
  --danger: #ef4444;
  --danger-soft: rgba(239, 68, 68, 0.15);
  --cyan: #06b6d4;
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --shadow: 0 12px 32px -6px rgba(0, 0, 0, 0.6);
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
}

* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--bg-root);
  color: var(--text-main);
  font-family: var(--font-sans);
  font-size: 13px;
  line-height: 1.45;
  overflow: hidden;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

::-webkit-scrollbar { width: 7px; height: 7px; }
::-webkit-scrollbar-track { background: var(--bg-root); }
::-webkit-scrollbar-thumb { background: #243456; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #385082; }

/* TOPBAR */
.topbar {
  height: 58px;
  background: linear-gradient(90deg, #090e1a 0%, #0f182c 50%, #090e1a 100%);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  gap: 12px;
  flex-shrink: 0;
  z-index: 30;
}
.brand {
  display: flex;
  align-items: center;
  gap: 11px;
  min-width: 225px;
}
.brand-badge {
  width: 36px;
  height: 36px;
  border-radius: 9px;
  background: linear-gradient(135deg, #10b981 0%, #2563eb 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 900;
  font-size: 14px;
  color: #fff;
  letter-spacing: -0.5px;
  box-shadow: 0 0 18px rgba(16, 185, 129, 0.4);
}
.brand-title {
  font-size: 14.5px;
  font-weight: 800;
  letter-spacing: -0.3px;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 6px;
}
.brand-sub {
  font-size: 10.5px;
  color: var(--text-muted);
}

.context-strip {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  justify-content: flex-end;
  flex-wrap: wrap;
}
.ctx-pill {
  display: flex;
  align-items: center;
  gap: 7px;
  background: var(--bg-input);
  border: 1px solid var(--border);
  padding: 4px 9px;
  border-radius: var(--radius-sm);
  transition: border-color 0.15s;
}
.ctx-pill:hover { border-color: var(--border-bright); }
.ctx-pill label {
  font-size: 9.5px;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: var(--text-muted);
  font-weight: 700;
  white-space: nowrap;
}
.ctx-pill select, .ctx-pill input {
  background: transparent;
  border: none;
  color: var(--text-main);
  font-size: 12px;
  font-weight: 600;
  outline: none;
  max-width: 240px;
}
.ctx-pill select option {
  background: var(--bg-surface);
  color: var(--text-main);
}
.lang-pill {
  border-color: rgba(16, 185, 129, 0.55);
  background: linear-gradient(90deg, rgba(16, 185, 129, 0.12), rgba(59, 130, 246, 0.08));
}
.lang-pill label { color: #34d399; }

/* WORKSPACE LAYOUT */
.workspace {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* SIDEBAR */
.sidebar {
  width: 238px;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 12px 9px;
  flex-shrink: 0;
  overflow-y: auto;
}
.nav-section-title {
  font-size: 9.5px;
  text-transform: uppercase;
  letter-spacing: 0.9px;
  color: var(--text-dim);
  padding: 10px 10px 5px;
  font-weight: 800;
}
.nav-btn {
  width: 100%;
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-muted);
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  font-size: 12.5px;
  font-weight: 600;
  text-align: left;
  transition: all 0.12s ease;
  margin-bottom: 2px;
}
.nav-btn:hover {
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-main);
}
.nav-btn.active {
  background: var(--accent-soft);
  color: #34d399;
  border-color: rgba(16, 185, 129, 0.35);
  font-weight: 700;
}
.nav-btn .nav-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.nav-badge {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 99px;
  background: rgba(255, 255, 255, 0.07);
  color: var(--text-muted);
  font-family: var(--font-mono);
}
.nav-btn.active .nav-badge {
  background: rgba(16, 185, 129, 0.25);
  color: #6ee7b7;
}
.sidebar-footer {
  border-top: 1px solid var(--border);
  padding: 10px 8px 4px;
  font-size: 11px;
  color: var(--text-dim);
}

/* MAIN CONTENT */
.content-area {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.tab-pane { display: none; flex-direction: column; gap: 14px; height: 100%; }
.tab-pane.active { display: flex; }

/* SPLIT VIEW: TABLE LEFT + GRANULAR INSPECTOR RIGHT */
.split-view {
  display: grid;
  grid-template-columns: minmax(430px, 1.05fr) minmax(520px, 1.35fr);
  gap: 14px;
  flex: 1;
  min-height: 0;
}
.split-col {
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  min-height: 0;
  padding-right: 2px;
}

/* CARDS & GRIDS */
.grid-4 { display: grid; grid-template-columns: repeat(auto-fit, minmax(195px, 1fr)); gap: 11px; }
.grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }
.grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 12px; }

.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 13px 15px;
  box-shadow: var(--shadow);
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  gap: 10px;
  flex-wrap: wrap;
}
.card-title {
  font-size: 13.5px;
  font-weight: 700;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 7px;
}
.card-sub {
  font-size: 11.5px;
  color: var(--text-muted);
}

.stat-card {
  background: linear-gradient(145deg, #131c31 0%, #0d1424 100%);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.stat-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: var(--text-muted);
  font-weight: 700;
}
.stat-val {
  font-size: 20px;
  font-weight: 800;
  color: #fff;
  font-family: var(--font-mono);
}
.stat-meta {
  font-size: 11px;
  color: var(--accent);
}

/* SUB-TABS BAR INSIDE INSPECTORS */
.subtabs {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
  background: var(--bg-input);
  padding: 5px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  margin-bottom: 10px;
}
.subtab-btn {
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-muted);
  padding: 5px 10px;
  border-radius: 5px;
  font-size: 11.5px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.12s;
}
.subtab-btn:hover { color: #fff; background: rgba(255, 255, 255, 0.05); }
.subtab-btn.active {
  background: var(--blue-soft);
  color: #60a5fa;
  border-color: rgba(59, 130, 246, 0.45);
}
.subtab-panel { display: none; flex-direction: column; gap: 11px; }
.subtab-panel.active { display: flex; }

/* FILTER BAR & CONTROLS */
.toolbar {
  display: flex;
  align-items: center;
  gap: 7px;
  flex-wrap: wrap;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  padding: 8px 11px;
  border-radius: var(--radius-md);
}
.input, .select {
  background: var(--bg-input);
  border: 1px solid var(--border);
  color: var(--text-main);
  padding: 6px 9px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  outline: none;
  transition: border-color 0.12s;
}
.input:focus, .select:focus { border-color: var(--accent); }
.input-mono { font-family: var(--font-mono); }
.input-sm { padding: 4px 7px; font-size: 11.5px; }

.btn {
  background: var(--bg-card-hover);
  border: 1px solid var(--border-bright);
  color: var(--text-main);
  padding: 6px 11px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  transition: all 0.12s;
  white-space: nowrap;
}
.btn:hover { background: #233357; border-color: #435f9c; }
.btn-primary {
  background: var(--accent);
  border-color: var(--accent);
  color: #031c13;
  font-weight: 800;
}
.btn-primary:hover { background: var(--accent-hover); color: #fff; }
.btn-blue {
  background: var(--blue);
  border-color: var(--blue);
  color: #fff;
  font-weight: 700;
}
.btn-blue:hover { background: #2563eb; }
.btn-amber {
  background: var(--amber-soft);
  border-color: rgba(245, 158, 11, 0.45);
  color: #fbbf24;
}
.btn-amber:hover { background: rgba(245, 158, 11, 0.28); }
.btn-danger {
  background: var(--danger-soft);
  border-color: rgba(239, 68, 68, 0.45);
  color: #f87171;
}
.btn-danger:hover { background: rgba(239, 68, 68, 0.28); }
.btn-xs { padding: 3px 7px; font-size: 11px; }

/* TABLES */
.table-wrap {
  overflow: auto;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-surface);
  max-height: 620px;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}
th {
  position: sticky;
  top: 0;
  background: #0b1120;
  color: var(--text-muted);
  font-weight: 700;
  text-align: left;
  padding: 8px 9px;
  border-bottom: 1px solid var(--border);
  font-size: 10.5px;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  z-index: 2;
  white-space: nowrap;
}
td {
  padding: 6.5px 9px;
  border-bottom: 1px solid rgba(30, 43, 72, 0.55);
  color: var(--text-main);
  white-space: nowrap;
}
tr:hover td { background: rgba(59, 130, 246, 0.08); cursor: pointer; }
tr.selected-row td {
  background: rgba(16, 185, 129, 0.15) !important;
  border-bottom-color: rgba(16, 185, 129, 0.4);
}

/* BADGES & ATTRIBUTE PILLS */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 7px;
  border-radius: 5px;
  font-size: 10.5px;
  font-weight: 700;
  font-family: var(--font-mono);
}
.badge-green { background: var(--accent-soft); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.35); }
.badge-blue { background: var(--blue-soft); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.35); }
.badge-purple { background: var(--purple-soft); color: #c084fc; border: 1px solid rgba(139, 92, 246, 0.35); }
.badge-amber { background: var(--amber-soft); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.35); }
.badge-red { background: var(--danger-soft); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.35); }

/* ATTRIBUTE GRID & TIER COLORING */
.attr-group-box {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 10px;
}
.attr-group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  padding-bottom: 5px;
  border-bottom: 1px solid var(--border);
}
.attr-group-title {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.7px;
  color: var(--accent);
  font-weight: 800;
}
.attr-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 3px 5px;
  border-radius: 4px;
  margin-bottom: 2px;
}
.attr-row:hover { background: rgba(255, 255, 255, 0.04); }
.attr-name {
  font-size: 11.8px;
  color: var(--text-main);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-right: 6px;
}
.attr-input {
  width: 52px;
  text-align: center;
  background: var(--bg-input);
  border: 1px solid var(--border);
  color: #fff;
  font-family: var(--font-mono);
  font-weight: 800;
  font-size: 12px;
  padding: 2.5px 4px;
  border-radius: 4px;
}
.attr-input.tier-elite { color: #34d399; border-color: rgba(16, 185, 129, 0.65); background: rgba(16, 185, 129, 0.12); }
.attr-input.tier-good { color: #60a5fa; border-color: rgba(59, 130, 246, 0.55); background: rgba(59, 130, 246, 0.10); }
.attr-input.tier-avg { color: #fbbf24; border-color: rgba(245, 158, 11, 0.45); }
.attr-input.tier-low { color: #94a3b8; }

/* FORM GRID */
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 8px;
}
.form-field {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.form-field label {
  font-size: 10px;
  color: var(--text-muted);
  text-transform: uppercase;
  font-weight: 700;
  letter-spacing: 0.3px;
}

/* TRAIT SWITCH CHIPS */
.trait-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 6px;
}
.trait-chip {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 6px 8px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  cursor: pointer;
  font-size: 11.5px;
  user-select: none;
  transition: all 0.12s;
}
.trait-chip.active {
  background: var(--accent-soft);
  border-color: rgba(16, 185, 129, 0.55);
  color: #6ee7b7;
  font-weight: 700;
}

/* PITCH POSITIONS GRID */
.pitch-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 7px;
  background: linear-gradient(180deg, rgba(16, 185, 129, 0.09) 0%, rgba(6, 78, 59, 0.18) 100%);
  border: 1px solid rgba(16, 185, 129, 0.35);
  border-radius: var(--radius-md);
  padding: 10px;
}
.pos-cell {
  background: rgba(8, 13, 24, 0.85);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 6px 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
}
.pos-cell.natural {
  border-color: #10b981;
  box-shadow: inset 0 0 10px rgba(16, 185, 129, 0.2);
}
.pos-code { font-size: 11px; font-weight: 800; color: #fff; }
.pos-term { font-size: 9.5px; color: var(--text-muted); text-align: center; }

/* STICKY SAVE BAR */
.sticky-action-bar {
  position: sticky;
  bottom: 0;
  background: rgba(10, 15, 28, 0.95);
  backdrop-filter: blur(8px);
  border-top: 1px solid var(--border-bright);
  padding: 9px 12px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  z-index: 10;
  margin-top: 6px;
}

/* TOAST */
#toast-box {
  position: fixed;
  bottom: 18px;
  right: 18px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.toast {
  background: #111b30;
  border-left: 4px solid var(--accent);
  border-top: 1px solid var(--border-bright);
  border-right: 1px solid var(--border-bright);
  border-bottom: 1px solid var(--border-bright);
  color: #fff;
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow);
  font-size: 12.5px;
  max-width: 420px;
}
.toast.error { border-left-color: var(--danger); }

code.inline {
  font-family: var(--font-mono);
  font-size: 11px;
  background: rgba(255, 255, 255, 0.07);
  padding: 1px 5px;
  border-radius: 4px;
  color: #93c5fd;
}

.ico {
  width: 15px;
  height: 15px;
  stroke: currentColor;
  stroke-width: 1.9;
  stroke-linecap: round;
  stroke-linejoin: round;
  fill: none;
  flex-shrink: 0;
}
.ico-accent { stroke: var(--accent); }
.ico-blue { stroke: var(--blue); }
.ico-amber { stroke: var(--amber); }
.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  display: inline-block;
  background: var(--accent);
  box-shadow: 0 0 8px var(--accent);
}
</style>
</head>
<body>

<!-- TOPBAR -->
<header class="topbar">
  <div class="brand">
    <div class="brand-badge">FM</div>
    <div>
      <div class="brand-title">FM27 / FM26 PRO STUDIO <span class="badge badge-green" style="font-size:9.5px;">GRANULAR v2</span></div>
      <div class="brand-sub">Canlı DB Editörü • Oyun Optimizasyonu • Binary & Bundle Patcher</div>
    </div>
  </div>

  <div class="context-strip">
    <div class="ctx-pill">
      <label>Aktif Kayıt (.fm)</label>
      <select id="sel-save" onchange="onContextChange()"></select>
    </div>
    <div class="ctx-pill">
      <label>Oyun Dizini</label>
      <select id="sel-fmdir" onchange="onContextChange()"></select>
    </div>
    <div class="ctx-pill lang-pill" title="Arayüz dili sabit kalırken oyuncu/personel nitelik, pozisyon ve rol terimlerini oyunun resmi 21 .ltc dilinden birinde canlı gösterir">
      <label style="display:flex;align-items:center;gap:5px;">
        <svg class="ico" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
        Oyun İçi Terim Dili (.ltc)
      </label>
      <select id="sel-gamelang" onchange="onGameLangChange()"></select>
    </div>
    <button class="btn btn-xs" onclick="refreshAll()" title="Bellek önbelleğini ve görünümü yenile">
      <svg class="ico" viewBox="0 0 24 24"><path d="M21 12a9 9 0 1 1-2.64-6.36"/><polyline points="21 3 21 9 15 9"/></svg>
      Yenile
    </button>
  </div>
</header>

<div class="workspace">
  <!-- SIDEBAR -->
  <aside class="sidebar">
    <div>
      <div class="nav-section-title">1. Kayıt & Oyun DB Editörü</div>
      <button class="nav-btn active" data-tab="tab-overview" onclick="switchTab('tab-overview')">
        <span class="nav-left">
          <svg class="ico" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/></svg>
          Genel Bakış & Tarih
        </span>
      </button>
      <button class="nav-btn" data-tab="tab-players" onclick="switchTab('tab-players')">
        <span class="nav-left">
          <svg class="ico" viewBox="0 0 24 24"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          Oyuncu & Sözleşme Editörü
        </span>
        <span class="nav-badge" id="nav-cnt-players">-</span>
      </button>
      <button class="nav-btn" data-tab="tab-clubs" onclick="switchTab('tab-clubs')">
        <span class="nav-left">
          <svg class="ico" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          Kulüp, Finans & Stadyum
        </span>
        <span class="nav-badge" id="nav-cnt-clubs">-</span>
      </button>
      <button class="nav-btn" data-tab="tab-staff" onclick="switchTab('tab-staff')">
        <span class="nav-left">
          <svg class="ico" viewBox="0 0 24 24"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/></svg>
          Personel, Hoca & DoF
        </span>
        <span class="nav-badge" id="nav-cnt-staff">-</span>
      </button>
      <button class="nav-btn" data-tab="tab-world" onclick="switchTab('tab-world')">
        <span class="nav-left">
          <svg class="ico" viewBox="0 0 24 24"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/></svg>
          Lig, Taktik, 11 & İsimler
        </span>
      </button>
      <button class="nav-btn" data-tab="tab-explorer" onclick="switchTab('tab-explorer')">
        <span class="nav-left">
          <svg class="ico" viewBox="0 0 24 24"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
          28 Tablo & Pre-Game DB
        </span>
        <span class="nav-badge">28+81</span>
      </button>

      <div class="nav-section-title">2. Oyun Optimizasyonu</div>
      <button class="nav-btn" data-tab="tab-optimization" onclick="switchTab('tab-optimization')">
        <span class="nav-left">
          <svg class="ico" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          Motor (boot.config) & Disk
        </span>
        <span class="nav-badge" id="nav-badge-opt">14+</span>
      </button>

      <div class="nav-section-title">3. Oyun Dosyası Yamaları</div>
      <button class="nav-btn" data-tab="tab-patches" onclick="switchTab('tab-patches')">
        <span class="nav-left">
          <svg class="ico" viewBox="0 0 24 24"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg>
          DLL Sınır & 252 Tablo Yaması
        </span>
        <span class="nav-badge" id="nav-badge-patches">262</span>
      </button>
      <button class="nav-btn" data-tab="tab-rules" onclick="switchTab('tab-rules')">
        <span class="nav-left">
          <svg class="ico" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
          Kurallar (.edt / .lnc / .dbc)
        </span>
      </button>
    </div>

    <div class="sidebar-footer">
      <div id="sidebar-save-meta">Yükleniyor...</div>
      <div style="margin-top:4px;color:#34d399;font-family:var(--font-mono);font-size:10px;display:flex;align-items:center;gap:6px;" id="sidebar-perf-pill">
        <span class="status-dot"></span> In-Memory Cache Aktif (&lt;1ms)
      </div>
    </div>
  </aside>

  <!-- CONTENT AREA -->
  <main class="content-area">

    <!-- ==================== TAB 0: OVERVIEW ==================== -->
    <section class="tab-pane active" id="tab-overview">
      <div class="grid-4" id="overview-kpis"></div>

      <div class="grid-2">
        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">
                <svg class="ico ico-accent" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                Oyun İçi Küresel Tarih & Çıktı Ayarları
              </div>
              <div class="card-sub">Kayıt dosyasındaki aktif oyun tarihini veya varsayılan kayıt hedefini doğrudan değiştirin</div>
            </div>
          </div>
          <div class="form-grid">
            <div class="form-field">
              <label>Oyun İçi Tarih (YYYY-MM-DD)</label>
              <input type="text" class="input input-mono" id="ov-game-date" placeholder="2026-02-23">
            </div>
            <div class="form-field">
              <label>Çıktı Kayıt Dosyası (Boş = _edited.fm)</label>
              <input type="text" class="input input-mono" id="global-output-path" placeholder="Otomatik (_edited.fm)">
            </div>
          </div>
          <div style="margin-top:10px;display:flex;gap:8px;align-items:center;">
            <button class="btn btn-primary" onclick="saveGlobalDate()">Oyun Tarihini Kaydet</button>
            <span class="card-sub" id="ov-save-path-label"></span>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">
                <svg class="ico ico-blue" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
                Aktif Oyun İçi Terim Lokalizasyonu Önizlemesi
              </div>
              <div class="card-sub">Üst bardaki <b>Oyun İçi Terim Dili (.ltc)</b> seçimine göre canlı çözümlenen oyun içi karşılıklar</div>
            </div>
            <span class="badge badge-green" id="ov-lang-badge">Turkish</span>
          </div>
          <div id="ov-lang-preview" style="display:flex;flex-wrap:wrap;gap:6px;"></div>
        </div>
      </div>

      <div class="grid-3">
        <div class="card">
          <div class="card-title" style="margin-bottom:6px;">
            <span class="badge badge-green">01</span> Tüm Veritabanları & Tam Kapsamlı Editör
          </div>
          <div class="card-sub" style="margin-bottom:10px;">
            <b>Oyuncu:</b> CA/PA, 3 İtibar, Kulüp Transferi, 52 Nitelik (1-20 veya 1-100 ham ölçek), 15 Pozisyon, 8 Kişilik, 64-bit Oyun Karakteri (Traits), Sözleşme + Bonuslar + Bireysel Maddeler (Clauses) ve Sezon İstatistikleri.<br>
            <b>Kulüp & Stadyum:</b> 11 Aylık Finans Alanı, Sponsorluklar, Tesisler ve 14 Stadyum/Saha Boyutu alanı.<br>
            <b>Personel:</b> CA/PA, 50+ Rol (r4), 26 Antrenörlük/Gözlemcilik Niteliği, 14 Taktiksel Tercih ve 8 Kişilik alanı.
          </div>
          <button class="btn btn-primary" onclick="switchTab('tab-players')">Oyuncu Editörünü Aç →</button>
        </div>
        <div class="card">
          <div class="card-title" style="margin-bottom:6px;">
            <span class="badge badge-blue">02</span> Oyun Optimizasyon Merkezi
          </div>
          <div class="card-sub" style="margin-bottom:10px;">
            Unity 6000.0.55f1-fm <code class="inline">boot.config</code> içerisindeki <b>14 kategorize edilmiş motor parametresi</b> (Job Worker Count, GC Incremental Time Slice, GFX Threading/Jobs, HDR, Direct3D Flip Model), özel anahtar ekleyici, doğrudan ham metin editörü ve başlangıç videoları (<code class="inline">Videos_disabled</code>) kontrolü.
          </div>
          <button class="btn btn-blue" onclick="switchTab('tab-optimization')">Optimizasyon Merkezini Aç →</button>
        </div>
        <div class="card">
          <div class="card-title" style="margin-bottom:6px;">
            <span class="badge badge-amber">03</span> Oyun Dosyası & Bundle Yamalayıcı
          </div>
          <div class="card-sub" style="margin-bottom:10px;">
            <code class="inline">game_plugin.dll</code> içerisindeki 50 oyuncu sınırını istediğiniz herhangi bir tam sayıya (<code class="inline">50..50000</code>) ayarlayın, 10 hazır UI sıralama yamasını veya oyun içindeki <b>252 adet <code class="inline">StreamedTable</code></b> nesnesinin her birinin sıralama kilidini tek tek açın/kapatın.
          </div>
          <button class="btn btn-amber" onclick="switchTab('tab-patches')">Oyun Yamalarını Aç →</button>
        </div>
      </div>
    </section>

    <!-- ==================== TAB 1: PLAYERS GRANULAR EDITOR ==================== -->
    <section class="tab-pane" id="tab-players">
      <div class="toolbar">
        <input type="text" class="input" id="pl-q" placeholder="İsim, UID veya Uyruk ara..." style="width:200px;" oninput="debouncedLoadPlayers()">
        <select class="select" id="pl-pos" onchange="loadPlayers()">
          <option value="">Tüm Pozisyonlar</option>
          <option value="GK">GK</option><option value="DC">DC</option><option value="DL">DL</option><option value="DR">DR</option>
          <option value="WBL">WBL</option><option value="WBR">WBR</option><option value="DM">DM</option><option value="MC">MC</option>
          <option value="ML">ML</option><option value="MR">MR</option><option value="AMC">AMC</option><option value="AML">AML</option>
          <option value="AMR">AMR</option><option value="ST">ST</option>
        </select>
        <input type="text" class="input" id="pl-club" placeholder="Kulüp adı veya UID..." style="width:155px;" oninput="debouncedLoadPlayers()">
        <input type="number" class="input input-mono" id="pl-min-ca" placeholder="Min CA" style="width:82px;" onchange="loadPlayers()">
        <input type="number" class="input input-mono" id="pl-max-age" placeholder="Max Yaş" style="width:85px;" onchange="loadPlayers()">
        <select class="select" id="pl-sort" onchange="loadPlayers()">
          <option value="ca">Sırala: CA (Azalan)</option>
          <option value="pa">Sırala: PA (Azalan)</option>
          <option value="value">Sırala: Piyasa Değeri</option>
          <option value="wage">Sırala: Haftalık Maaş</option>
          <option value="current_rep">Sırala: İtibar</option>
          <option value="age">Sırala: Yaş (Gençten)</option>
        </select>
        <select class="select" id="pl-limit" onchange="loadPlayers()">
          <option value="100">100 Kayıt</option>
          <option value="250">250 Kayıt</option>
          <option value="500">500 Kayıt</option>
        </select>
        <button class="btn btn-primary" onclick="loadPlayers()">Filtrele</button>
        <span class="card-sub" id="pl-count-label" style="margin-left:auto;"></span>
      </div>

      <div class="split-view">
        <!-- Left: Players Table -->
        <div class="split-col">
          <div class="table-wrap" style="flex:1;">
            <table>
              <thead>
                <tr>
                  <th>UID</th>
                  <th>Oyuncu</th>
                  <th>Yaş</th>
                  <th>Poz</th>
                  <th>CA</th>
                  <th>PA</th>
                  <th>Kulüp</th>
                  <th>Maaş</th>
                  <th>Değer</th>
                </tr>
              </thead>
              <tbody id="pl-tbody"></tbody>
            </table>
          </div>
        </div>

        <!-- Right: 6-Subtab Granular Player Inspector -->
        <div class="split-col">
          <div class="card" id="pl-inspector-card" style="flex:1;display:flex;flex-direction:column;">
            <div class="card-header">
              <div>
                <div class="card-title" id="pl-ed-title">Bir oyuncu seçin</div>
                <div class="card-sub" id="pl-ed-sub">Soldaki tablodan bir oyuncuya tıkladığınızda tüm 52 niteliği, 15 pozisyonu, kişiliği, oyun karakteri ve sözleşme maddeleri &lt;1ms içinde burada açılır.</div>
              </div>
              <div style="display:flex;gap:5px;flex-wrap:wrap;" id="pl-quick-presets-bar">
                <button class="btn btn-xs btn-amber" onclick="presetPlayerWonderkid()" title="Opsiyonel Önayar: CA=175, PA=200, Kondisyon=100%">Wonderkid</button>
                <button class="btn btn-xs btn-blue" onclick="presetPlayerFitness()" title="Opsiyonel Önayar: Kondisyon=100%, Keskinlik=100%">%100 Kondisyon</button>
                <button class="btn btn-xs btn-danger" onclick="savePlayerEdits(true)" title="Opsiyonel Önayar: CA/PA=200, Tüm 52 Nitelik=20, 15 Pozisyon=20">Tamamını 20 (Max) Yap</button>
              </div>
            </div>

            <div id="pl-inspector-body" style="display:none;flex-direction:column;flex:1;">
              <!-- 6 Sub-tabs -->
              <div class="subtabs">
                <button class="subtab-btn active" data-subtab="pl-sub-identity" onclick="switchSubTab('pl', 'pl-sub-identity')">1. Kimlik, Transfer & Fiziksel</button>
                <button class="subtab-btn" data-subtab="pl-sub-attrs" onclick="switchSubTab('pl', 'pl-sub-attrs')">2. 52 Nitelik (Tam Kontrol)</button>
                <button class="subtab-btn" data-subtab="pl-sub-pos" onclick="switchSubTab('pl', 'pl-sub-pos')">3. 15 Pozisyon & 6B Rol</button>
                <button class="subtab-btn" data-subtab="pl-sub-pers" onclick="switchSubTab('pl', 'pl-sub-pers')">4. 8 Kişilik & 64-Bit Traits</button>
                <button class="subtab-btn" data-subtab="pl-sub-contract" onclick="switchSubTab('pl', 'pl-sub-contract')">5. Sözleşme & Maddeler</button>
                <button class="subtab-btn" data-subtab="pl-sub-stats" onclick="switchSubTab('pl', 'pl-sub-stats')">6. Sezon İstatistikleri</button>
              </div>

              <!-- Subtab 1: Identity, Club Transfer, Reputation & Physical -->
              <div class="subtab-panel active" id="pl-sub-identity">
                <div class="attr-group-box">
                  <div class="attr-group-header">
                    <span class="attr-group-title">Yetenek (CA/PA), 3 İtibar & Piyasa Değeri</span>
                    <span class="card-sub">Tüm değerleri serbestçe düzenleyebilirsiniz (PA negatif potansiyel `-10..-1` destekler)</span>
                  </div>
                  <div class="form-grid">
                    <div class="form-field"><label id="lbl-ca">Mevcut Yetenek (CA 0-200)</label><input type="number" min="0" max="200" class="input input-mono" id="ed-pl-ca"></div>
                    <div class="form-field"><label id="lbl-pa">Potansiyel (PA -10..200)</label><input type="number" min="-10" max="200" class="input input-mono" id="ed-pl-pa"></div>
                    <div class="form-field"><label>Yerel İtibar (1-10000)</label><input type="number" min="1" max="10000" class="input input-mono" id="ed-pl-hrep"></div>
                    <div class="form-field"><label>Mevcut İtibar (1-10000)</label><input type="number" min="1" max="10000" class="input input-mono" id="ed-pl-crep"></div>
                    <div class="form-field"><label>Dünya İtibarı (1-10000)</label><input type="number" min="1" max="10000" class="input input-mono" id="ed-pl-wrep"></div>
                    <div class="form-field"><label>İtibar Dilimi (Bucket 0-200)</label><input type="number" min="0" max="200" class="input input-mono" id="ed-pl-repbucket"></div>
                    <div class="form-field"><label>Transfer Değeri (£/€)</label><input type="number" min="0" class="input input-mono" id="ed-pl-val"></div>
                    <div class="form-field"><label>Kondisyon % (0-100)</label><input type="number" min="0" max="100" class="input input-mono" id="ed-pl-cond"></div>
                    <div class="form-field"><label>Maç Keskinliği % (0-100)</label><input type="number" min="0" max="100" class="input input-mono" id="ed-pl-sharp"></div>
                  </div>
                </div>

                <div class="attr-group-box">
                  <div class="attr-group-header">
                    <span class="attr-group-title">Kulüp Transferi & Kadro Yuvası</span>
                    <span class="card-sub">Oyuncuyu başka bir kulübe anında transfer edin veya kadro yuvasını değiştirin</span>
                  </div>
                  <div class="form-grid">
                    <div class="form-field" style="grid-column: span 2;">
                      <label>Kulüp Seç (veya UID gir)</label>
                      <select class="select" id="ed-pl-club-select" onchange="document.getElementById('ed-pl-club-uid').value=this.value"></select>
                    </div>
                    <div class="form-field">
                      <label>Kulüp UID</label>
                      <input type="number" class="input input-mono" id="ed-pl-club-uid">
                    </div>
                    <div class="form-field">
                      <label>Kadro Yuvası (Team Slot)</label>
                      <select class="select" id="ed-pl-teamslot">
                        <option value="0">0 — A Takım (Senior Squad)</option>
                        <option value="1">1 — Yedek / B Takımı</option>
                        <option value="2">2 — Altyapı / U21 / U19</option>
                      </select>
                    </div>
                    <div class="form-field">
                      <label>Kulübe Katılış Tarihi</label>
                      <input type="text" class="input input-mono" id="ed-pl-joindate" placeholder="YYYY-MM-DD">
                    </div>
                  </div>
                </div>

                <div class="attr-group-box">
                  <div class="attr-group-header">
                    <span class="attr-group-title">Demografi, Uyruk, Fiziksel & Ayak Kullanımı</span>
                  </div>
                  <div class="form-grid">
                    <div class="form-field"><label>Doğum Tarihi (YYYY-MM-DD)</label><input type="text" class="input input-mono" id="ed-pl-bdate" placeholder="2002-05-15"></div>
                    <div class="form-field"><label>Yaş (Doğrudan Değiştir)</label><input type="number" min="14" max="55" class="input input-mono" id="ed-pl-age"></div>
                    <div class="form-field" style="grid-column: span 2;">
                      <label>Birincil Uyruk (226 Ülke)</label>
                      <select class="select" id="ed-pl-nation"></select>
                    </div>
                    <div class="form-field"><label>Boy (cm, 140-220)</label><input type="number" min="140" max="220" class="input input-mono" id="ed-pl-height"></div>
                    <div class="form-field"><label>Forma Numarası (1-99)</label><input type="number" min="0" max="99" class="input input-mono" id="ed-pl-shirt" placeholder="Değiştirme"></div>
                    <div class="form-field"><label>Vücut Tipi Kodu (1-5)</label><input type="number" min="1" max="5" class="input input-mono" id="ed-pl-bodytype" placeholder="Değiştirme"></div>
                    <div class="form-field"><label id="lbl-lfoot">Sol Ayak (1-20)</label><input type="number" min="1" max="20" class="input input-mono" id="ed-pl-lfoot"></div>
                    <div class="form-field"><label id="lbl-rfoot">Sağ Ayak (1-20)</label><input type="number" min="1" max="20" class="input input-mono" id="ed-pl-rfoot"></div>
                  </div>
                  <div style="margin-top:10px;display:flex;gap:14px;flex-wrap:wrap;align-items:center;">
                    <label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:12px;">
                      <input type="checkbox" id="ed-pl-heal" checked> Tüm Sakatlıkları İyileştir
                    </label>
                    <label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:12px;">
                      <input type="checkbox" id="ed-pl-unsuspend" checked> Tüm Cezaları Temizle
                    </label>
                  </div>
                </div>
              </div>

              <!-- Subtab 2: All 52 Attributes -->
              <div class="subtab-panel" id="pl-sub-attrs">
                <div class="toolbar" style="justify-content:space-between;">
                  <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
                    <label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-weight:700;color:#60a5fa;">
                      <input type="checkbox" id="ed-pl-raw-scale" onchange="togglePlayerAttrScale()">
                      1–100 Ham (Internal Raw) Ölçekte Düzenle
                    </label>
                    <span class="card-sub" id="pl-scale-hint">Şu an: 1–20 Görünür Oyun Ölçeği</span>
                  </div>
                  <div style="display:flex;gap:5px;flex-wrap:wrap;">
                    <button class="btn btn-xs" onclick="adjustAllPlayerAttrs(1)">Tümüne +1</button>
                    <button class="btn btn-xs" onclick="adjustAllPlayerAttrs(-1)">Tümüne -1</button>
                    <button class="btn btn-xs btn-blue" onclick="setAllPlayerAttrsPrompt()">Tümünü Belirli Değere Ayarla...</button>
                  </div>
                </div>
                <div class="grid-3" id="pl-attrs-grid"></div>
              </div>

              <!-- Subtab 3: 15 Positions & 6D Role Suitability -->
              <div class="subtab-panel" id="pl-sub-pos">
                <div class="attr-group-box">
                  <div class="attr-group-header">
                    <span class="attr-group-title">15 Pozisyon Hakimiyeti (1–20, 20 = Doğal / Natural)</span>
                    <div style="display:flex;gap:5px;">
                      <button class="btn btn-xs" onclick="setAllPositions(20)">Tüm Pozisyonları 20 Yap</button>
                    </div>
                  </div>
                  <div class="pitch-grid" id="pl-pos-grid"></div>
                </div>
                <div class="attr-group-box">
                  <div class="attr-group-header">
                    <span class="attr-group-title">6 Boyutlu Taktiksel Rol Uyum Analizi (Canlı Motor Hesabı)</span>
                  </div>
                  <div id="pl-roles-box" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px;"></div>
                </div>
              </div>

              <!-- Subtab 4: 8 Personality & 64-Bit Player Traits -->
              <div class="subtab-panel" id="pl-sub-pers">
                <div class="attr-group-box">
                  <div class="attr-group-header">
                    <span class="attr-group-title">8 Gizli Kişilik Niteliği (1–20)</span>
                    <button class="btn btn-xs btn-amber" onclick="presetModelCitizenPersonality()">Model Vatandaş Kişiliği</button>
                  </div>
                  <div class="form-grid" id="pl-pers-grid"></div>
                </div>

                <div class="attr-group-box">
                  <div class="attr-group-header">
                    <span class="attr-group-title">Oyun Karakteri / Oyun İçi Tercihler (64-Bit Trait Bitmask)</span>
                    <div style="display:flex;align-items:center;gap:6px;">
                      <span class="card-sub">Ham 64-bit Maske:</span>
                      <input type="text" class="input input-sm input-mono" id="ed-pl-trait-raw" style="width:170px;" onchange="syncTraitChipsFromRaw()">
                    </div>
                  </div>
                  <div class="trait-grid" id="pl-traits-grid"></div>
                  <div style="margin-top:8px;display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                    <span class="card-sub">Özel Bit (0..63) Aç/Kapat:</span>
                    <input type="number" min="0" max="63" class="input input-sm input-mono" id="ed-pl-custom-bit" placeholder="Bit (0-63)" style="width:90px;">
                    <button class="btn btn-xs" onclick="toggleCustomTraitBit()">Biti Değiştir (Toggle)</button>
                    <span class="card-sub" id="pl-active-bits-label"></span>
                  </div>
                </div>
              </div>

              <!-- Subtab 5: Contract, Bonuses & Clauses -->
              <div class="subtab-panel" id="pl-sub-contract">
                <div class="attr-group-box">
                  <div class="attr-group-header">
                    <span class="attr-group-title">Sözleşme Ana Alanları & Sadakat/Menajer Bonusları</span>
                  </div>
                  <div class="form-grid">
                    <div class="form-field"><label>Haftalık Maaş (£/€)</label><input type="number" min="0" class="input input-mono" id="ed-ct-wage"></div>
                    <div class="form-field"><label>Başlangıç Tarihi</label><input type="text" class="input input-mono" id="ed-ct-start" placeholder="YYYY-MM-DD"></div>
                    <div class="form-field"><label>Bitiş Tarihi</label><input type="text" class="input input-mono" id="ed-ct-end" placeholder="YYYY-MM-DD"></div>
                    <div class="form-field">
                      <label>Kadro Statüsü (18 Statü)</label>
                      <select class="select" id="ed-ct-status"></select>
                    </div>
                    <div class="form-field">
                      <label>Sözleşme Türü</label>
                      <select class="select" id="ed-ct-type">
                        <option value="1">1 — Tam Zamanlı (Full-Time)</option>
                        <option value="2">2 — Yarı Zamanlı (Part-Time)</option>
                        <option value="3">3 — Genç Sözleşmesi (Youth)</option>
                        <option value="4">4 — Amatör (Non-Contract)</option>
                      </select>
                    </div>
                    <div class="form-field"><label>İmza / Sadakat Bonusu</label><input type="number" min="0" class="input input-mono" id="ed-ct-signfee"></div>
                    <div class="form-field"><label>Menajerlik Ücreti</label><input type="number" min="0" class="input input-mono" id="ed-ct-agentfee"></div>
                    <div class="form-field"><label>Paket / Ek Bonus</label><input type="number" min="0" class="input input-mono" id="ed-ct-pkgbonus"></div>
                    <div class="form-field"><label>Opsiyon Yılı (e12)</label><input type="number" class="input input-mono" id="ed-ct-opyear"></div>
                  </div>
                </div>

                <div class="attr-group-box">
                  <div class="attr-group-header">
                    <span class="attr-group-title">Sözleşme Maddeleri & Bonus Kalemleri (Clauses)</span>
                    <span class="card-sub">Mevcut serbest kalma bedeli, maç başı ücret ve gol/asist bonuslarını tek tek düzenleyin</span>
                  </div>
                  <div id="pl-clauses-box"></div>
                </div>
              </div>

              <!-- Subtab 6: Season Stats Editor -->
              <div class="subtab-panel" id="pl-sub-stats">
                <div class="attr-group-box">
                  <div class="attr-group-header">
                    <span class="attr-group-title">Bu Sezon İstatistikleri Editörü (Lig / Kupa / Avrupa)</span>
                    <select class="select input-sm" id="ed-ss-slot" onchange="populateSeasonStatsSlot()">
                      <option value="league">Lig İstatistikleri (Slot 0)</option>
                      <option value="cup">Yerel Kupa (Slot 1)</option>
                      <option value="continental">Kıta / Avrupa Kupası (Slot 2)</option>
                    </select>
                  </div>
                  <div class="form-grid">
                    <div class="form-field"><label>İlk 11 Maç (Starts)</label><input type="number" min="0" class="input input-mono" id="ed-ss-starts"></div>
                    <div class="form-field"><label>Sonradan Giriş (Sub)</label><input type="number" min="0" class="input input-mono" id="ed-ss-subs"></div>
                    <div class="form-field"><label>Goller (Goals)</label><input type="number" min="0" class="input input-mono" id="ed-ss-goals"></div>
                    <div class="form-field"><label>Asistler (Assists)</label><input type="number" min="0" class="input input-mono" id="ed-ss-assists"></div>
                    <div class="form-field"><label>Sarı Kart</label><input type="number" min="0" class="input input-mono" id="ed-ss-yc"></div>
                    <div class="form-field"><label>Kırmızı Kart</label><input type="number" min="0" class="input input-mono" id="ed-ss-rc"></div>
                    <div class="form-field"><label>Maçın Adamı (PoM)</label><input type="number" min="0" class="input input-mono" id="ed-ss-pom"></div>
                    <div class="form-field"><label>Kullanılan Penaltı</label><input type="number" min="0" class="input input-mono" id="ed-ss-pent"></div>
                    <div class="form-field"><label>Gol Olan Penaltı</label><input type="number" min="0" class="input input-mono" id="ed-ss-pens"></div>
                    <div class="form-field"><label>Oynanan Dakika</label><input type="number" min="0" class="input input-mono" id="ed-ss-mins"></div>
                    <div class="form-field"><label>Pas Denemesi</label><input type="number" min="0" class="input input-mono" id="ed-ss-passa"></div>
                    <div class="form-field"><label>İsabetli Pas</label><input type="number" min="0" class="input input-mono" id="ed-ss-passc"></div>
                  </div>
                </div>
              </div>

              <!-- Sticky Save Action Bar -->
              <div class="sticky-action-bar">
                <div class="card-sub" id="pl-save-status-hint">Değişikliklerinizi kaydettiğinizde aktif kayıt güncellenir.</div>
                <div style="display:flex;gap:8px;">
                  <button class="btn" onclick="selectPlayer(STATE.selectedPlayerUid)">Sıfırla</button>
                  <button class="btn btn-primary" onclick="savePlayerEdits(false)">Oyuncu Değişikliklerini Kaydet (.fm)</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ==================== TAB 2: CLUBS, FINANCES, SPONSORSHIPS & STADIUMS ==================== -->
    <section class="tab-pane" id="tab-clubs">
      <div class="toolbar">
        <input type="text" class="input" id="cl-q" placeholder="Kulüp adı, kısa ad veya UID..." style="width:240px;" oninput="debouncedLoadClubs()">
        <select class="select" id="cl-sort" onchange="loadClubs()">
          <option value="reputation">Sırala: İtibar (Azalan)</option>
          <option value="balance">Sırala: Kasa Bakiyesi</option>
          <option value="transfer_budget">Sırala: Transfer Bütçesi</option>
          <option value="wage_budget">Sırala: Maaş Bütçesi</option>
          <option value="stadium_capacity">Sırala: Stadyum Kapasitesi</option>
        </select>
        <button class="btn btn-primary" onclick="loadClubs()">Kulüpleri Listele</button>
        <span class="card-sub" id="cl-count-label" style="margin-left:auto;"></span>
      </div>

      <div class="split-view">
        <div class="split-col">
          <div class="table-wrap" style="flex:1;">
            <table>
              <thead>
                <tr>
                  <th>UID</th>
                  <th>Kulüp</th>
                  <th>İtibar</th>
                  <th>Bakiye</th>
                  <th>Transfer Büt.</th>
                  <th>Maaş Büt.</th>
                  <th>Stadyum</th>
                </tr>
              </thead>
              <tbody id="cl-tbody"></tbody>
            </table>
          </div>
        </div>

        <div class="split-col">
          <div class="card" style="flex:1;display:flex;flex-direction:column;">
            <div class="card-header">
              <div>
                <div class="card-title" id="cl-ed-title">Bir kulüp seçin</div>
                <div class="card-sub" id="cl-ed-sub">Kulüp kimliği, 11 finans alanı, sponsorluk sözleşmeleri, kurumsal tesisler ve 14 stadyum alanı</div>
              </div>
              <div style="display:flex;gap:5px;">
                <button class="btn btn-xs btn-amber" onclick="presetClubSugarDaddy()">+250M€ Bakiye & Transfer Bütçesi</button>
              </div>
            </div>

            <div id="cl-inspector-body" style="display:none;flex-direction:column;flex:1;">
              <div class="subtabs">
                <button class="subtab-btn active" data-subtab="cl-sub-identity" onclick="switchSubTab('cl', 'cl-sub-identity')">1. Kimlik, İtibar & Tesisler</button>
                <button class="subtab-btn" data-subtab="cl-sub-finances" onclick="switchSubTab('cl', 'cl-sub-finances')">2. 11 Finans Alanı & Bilanço</button>
                <button class="subtab-btn" data-subtab="cl-sub-sponsors" onclick="switchSubTab('cl', 'cl-sub-sponsors')">3. Sponsorluk Sözleşmeleri</button>
                <button class="subtab-btn" data-subtab="cl-sub-stadium" onclick="switchSubTab('cl', 'cl-sub-stadium')">4. Stadyum & Saha (14 Alan)</button>
              </div>

              <div class="subtab-panel active" id="cl-sub-identity">
                <div class="attr-group-box">
                  <div class="attr-group-header"><span class="attr-group-title">Kulüp Kimliği, İtibar & Tesisler</span></div>
                  <div class="form-grid">
                    <div class="form-field" style="grid-column: span 2;"><label>Kulüp Tam Adı</label><input type="text" class="input" id="ed-cl-name"></div>
                    <div class="form-field"><label>Kısa Ad (Short Name)</label><input type="text" class="input" id="ed-cl-short"></div>
                    <div class="form-field"><label>İtibar (1-10000)</label><input type="number" min="1" max="10000" class="input input-mono" id="ed-cl-rep"></div>
                    <div class="form-field"><label>Son Lig Sıralaması (1-255)</label><input type="number" min="1" max="255" class="input input-mono" id="ed-cl-lastpos"></div>
                    <div class="form-field"><label>Ülke (Nation ID)</label><select class="select" id="ed-cl-nation"></select></div>
                    <div class="form-field"><label>Federasyon (FA Nation ID)</label><input type="number" class="input input-mono" id="ed-cl-fanation"></div>
                    <div class="form-field"><label>Şehir ID (City ID)</label><input type="number" class="input input-mono" id="ed-cl-city"></div>
                    <div class="form-field"><label>Kurumsal Tesisler (1-20)</label><input type="number" min="1" max="20" class="input input-mono" id="ed-cl-corpfac"></div>
                  </div>
                </div>
              </div>

              <div class="subtab-panel" id="cl-sub-finances">
                <div class="attr-group-box">
                  <div class="attr-group-header">
                    <span class="attr-group-title">11 Aylık Finans & Bütçe Alanı</span>
                    <span class="card-sub">Hedef Bilanço Ayı (-1 = Güncel Ay)</span>
                  </div>
                  <div class="form-grid">
                    <div class="form-field"><label>Kasa Bakiyesi (Balance)</label><input type="number" class="input input-mono" id="ed-cl-bal"></div>
                    <div class="form-field"><label>Kalan Transfer Bütçesi</label><input type="number" class="input input-mono" id="ed-cl-tbud"></div>
                    <div class="form-field"><label>Tahsis Edilen Transfer Büt.</label><input type="number" class="input input-mono" id="ed-cl-tbud-alloc"></div>
                    <div class="form-field"><label>Haftalık Maaş Bütçesi</label><input type="number" class="input input-mono" id="ed-cl-wbud"></div>
                    <div class="form-field"><label>Haftalık Maaş Bordrosu</label><input type="number" class="input input-mono" id="ed-cl-wpay"></div>
                    <div class="form-field"><label>Transfer Hariç Gelir</label><input type="number" class="input input-mono" id="ed-cl-incex"></div>
                    <div class="form-field"><label>Transfer Hariç Gider</label><input type="number" class="input input-mono" id="ed-cl-expex"></div>
                    <div class="form-field"><label>Net Transfer Bilançosu</label><input type="number" class="input input-mono" id="ed-cl-nettr"></div>
                    <div class="form-field"><label>Aylık Maaş Faturası</label><input type="number" class="input input-mono" id="ed-cl-wbill"></div>
                    <div class="form-field"><label>Toplam Gelir</label><input type="number" class="input input-mono" id="ed-cl-totinc"></div>
                    <div class="form-field"><label>Toplam Gider</label><input type="number" class="input input-mono" id="ed-cl-totexp"></div>
                    <div class="form-field"><label>Bilanço Ay İndeksi (-1=Son)</label><input type="number" class="input input-mono" id="ed-cl-monthidx" value="-1"></div>
                  </div>
                </div>
                <div class="attr-group-box">
                  <div class="attr-group-header"><span class="attr-group-title">Aylık Finansal Zaman Serisi Özeti</span></div>
                  <div class="table-wrap" style="max-height:190px;">
                    <table>
                      <thead><tr><th>Ay</th><th>Bakiye</th><th>Transfer Büt.</th><th>Maaş Büt.</th><th>Toplam Gelir</th><th>Toplam Gider</th></tr></thead>
                      <tbody id="cl-fin-series-tbody"></tbody>
                    </table>
                  </div>
                </div>
              </div>

              <div class="subtab-panel" id="cl-sub-sponsors">
                <div class="attr-group-box">
                  <div class="attr-group-header">
                    <span class="attr-group-title">Sponsorluk Anlaşmaları (Sponsorships)</span>
                    <span class="card-sub">Her anlaşmanın yıllık/toplam değerini ve bitiş tarihini düzenleyin</span>
                  </div>
                  <div id="cl-sponsors-box"></div>
                </div>
              </div>

              <div class="subtab-panel" id="cl-sub-stadium">
                <div class="attr-group-box">
                  <div class="attr-group-header">
                    <span class="attr-group-title">Stadyum & Saha Boyutları (14 Alan — dm: desimetre, 1050 = 105m)</span>
                  </div>
                  <div class="form-grid">
                    <div class="form-field"><label>Stadyum UID</label><input type="number" class="input input-mono" id="ed-st-uid" readonly></div>
                    <div class="form-field" style="grid-column: span 2;"><label>Stadyum Adı</label><input type="text" class="input" id="ed-st-name"></div>
                    <div class="form-field"><label>Toplam Kapasite</label><input type="number" min="0" class="input input-mono" id="ed-st-cap"></div>
                    <div class="form-field"><label>Koltuklu Kapasite</label><input type="number" min="0" class="input input-mono" id="ed-st-seat"></div>
                    <div class="form-field"><label>Genişleme Kapasitesi</label><input type="number" min="0" class="input input-mono" id="ed-st-exp"></div>
                    <div class="form-field"><label>Sahip Kulüp UID</label><input type="number" class="input input-mono" id="ed-st-owner"></div>
                    <div class="form-field"><label>Saha Uzunluğu (dm)</label><input type="number" class="input input-mono" id="ed-st-plen"></div>
                    <div class="form-field"><label>Saha Genişliği (dm)</label><input type="number" class="input input-mono" id="ed-st-pwid"></div>
                    <div class="form-field"><label>Min Uzunluk (dm)</label><input type="number" class="input input-mono" id="ed-st-minlen"></div>
                    <div class="form-field"><label>Max Uzunluk (dm)</label><input type="number" class="input input-mono" id="ed-st-maxlen"></div>
                    <div class="form-field"><label>Min Genişlik (dm)</label><input type="number" class="input input-mono" id="ed-st-minwid"></div>
                    <div class="form-field"><label>Max Genişlik (dm)</label><input type="number" class="input input-mono" id="ed-st-maxwid"></div>
                    <div class="form-field"><label>İnşa Tarihi (YYYY-MM-DD)</label><input type="text" class="input input-mono" id="ed-st-built"></div>
                    <div class="form-field"><label>Yenilenme Tarihi</label><input type="text" class="input input-mono" id="ed-st-rebuilt"></div>
                  </div>
                </div>
              </div>

              <div class="sticky-action-bar">
                <span class="card-sub">Kulüp, finans, sponsorluk ve stadyum alanlarını tek seferde kaydeder.</span>
                <button class="btn btn-primary" onclick="saveClubAndStadiumEdits()">Kulüp & Stadyum Değişikliklerini Kaydet</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ==================== TAB 3: STAFF, COACHES & DOF ==================== -->
    <section class="tab-pane" id="tab-staff">
      <div class="toolbar">
        <input type="text" class="input" id="stf-q" placeholder="Teknik direktör, gözlemci, fizyo veya kulüp ara..." style="width:260px;" oninput="debouncedLoadStaff()">
        <input type="text" class="input" id="stf-role" placeholder="Rol filtrele (Menajer, Gözlemci...)" style="width:200px;" oninput="debouncedLoadStaff()">
        <button class="btn btn-primary" onclick="loadStaff()">Personel Listele</button>
        <button class="btn btn-blue" onclick="loadDofReport()">Futbol Direktörü (DoF) Analizi</button>
        <span class="card-sub" id="stf-count-label" style="margin-left:auto;"></span>
      </div>

      <div class="split-view">
        <div class="split-col">
          <div class="table-wrap" style="flex:1;">
            <table>
              <thead>
                <tr>
                  <th>UID</th>
                  <th>Ad Soyad</th>
                  <th>Rol (r4)</th>
                  <th>Kulüp</th>
                  <th>CA</th>
                  <th>PA</th>
                  <th>Yaş</th>
                </tr>
              </thead>
              <tbody id="stf-tbody"></tbody>
            </table>
          </div>
        </div>

        <div class="split-col">
          <div class="card" style="flex:1;display:flex;flex-direction:column;">
            <div class="card-header">
              <div>
                <div class="card-title" id="stf-ed-title">Bir personel seçin</div>
                <div class="card-sub" id="stf-ed-sub">CA/PA, 50+ Rol (r4), 26 Antrenörlük/Gözlemcilik/Sağlık niteliği, 14 Taktiksel Tercih ve 8 Kişilik</div>
              </div>
              <button class="btn btn-xs btn-danger" onclick="saveStaffEdits(true)">Tüm Personel Niteliklerini 20 Yap</button>
            </div>

            <div id="stf-inspector-body" style="display:none;flex-direction:column;flex:1;">
              <div class="subtabs">
                <button class="subtab-btn active" data-subtab="stf-sub-identity" onclick="switchSubTab('stf', 'stf-sub-identity')">1. Kimlik, Rol (r4) & Sözleşme</button>
                <button class="subtab-btn" data-subtab="stf-sub-attrs" onclick="switchSubTab('stf', 'stf-sub-attrs')">2. 26 Nitelik (block_40)</button>
                <button class="subtab-btn" data-subtab="stf-sub-prefs" onclick="switchSubTab('stf', 'stf-sub-prefs')">3. 14 Taktik Tercih & 8 Kişilik</button>
                <button class="subtab-btn" data-subtab="stf-sub-dof" onclick="switchSubTab('stf', 'stf-sub-dof')">4. DoF Hoca Atama</button>
              </div>

              <div class="subtab-panel active" id="stf-sub-identity">
                <div class="attr-group-box">
                  <div class="attr-group-header"><span class="attr-group-title">Personel Kimlik, Rol Kodu (r4) & Sözleşme</span></div>
                  <div class="form-grid">
                    <div class="form-field"><label>Mevcut Yetenek (CA 1-200)</label><input type="number" min="1" max="200" class="input input-mono" id="ed-stf-ca"></div>
                    <div class="form-field"><label>Potansiyel (PA 1-200)</label><input type="number" min="1" max="200" class="input input-mono" id="ed-stf-pa"></div>
                    <div class="form-field" style="grid-column: span 2;">
                      <label>Görev / Rol (STAFF_ROLE_MAP r4)</label>
                      <select class="select" id="ed-stf-role"></select>
                    </div>
                    <div class="form-field"><label>Doğum Tarihi (YYYY-MM-DD)</label><input type="text" class="input input-mono" id="ed-stf-bdate"></div>
                    <div class="form-field"><label>Yaş</label><input type="number" class="input input-mono" id="ed-stf-age"></div>
                    <div class="form-field" style="grid-column: span 2;"><label>Uyruk</label><select class="select" id="ed-stf-nation"></select></div>
                    <div class="form-field"><label>Haftalık Maaş</label><input type="number" class="input input-mono" id="ed-stf-wage"></div>
                    <div class="form-field"><label>Sözleşme Başlangıç</label><input type="text" class="input input-mono" id="ed-stf-cstart"></div>
                    <div class="form-field"><label>Sözleşme Bitiş</label><input type="text" class="input input-mono" id="ed-stf-cend"></div>
                    <div class="form-field"><label>Takım ID (Team ID)</label><input type="number" class="input input-mono" id="ed-stf-teamid"></div>
                  </div>
                </div>
              </div>

              <div class="subtab-panel" id="stf-sub-attrs">
                <div class="attr-group-box">
                  <div class="attr-group-header">
                    <span class="attr-group-title">26 Antrenörlük, Gözlemcilik, Kaleci & Sağlık Niteliği (1–20)</span>
                    <button class="btn btn-xs" onclick="setAllStaffAttrs(20)">Tümünü 20 Yap</button>
                  </div>
                  <div class="form-grid" id="stf-attrs-grid"></div>
                </div>
              </div>

              <div class="subtab-panel" id="stf-sub-prefs">
                <div class="attr-group-box">
                  <div class="attr-group-header"><span class="attr-group-title">14 Taktiksel & Yönetim Tercihi (1–20)</span></div>
                  <div class="form-grid" id="stf-prefs-grid"></div>
                </div>
                <div class="attr-group-box">
                  <div class="attr-group-header"><span class="attr-group-title">8 Kişilik Niteliği (1–20)</span></div>
                  <div class="form-grid" id="stf-pers-grid"></div>
                </div>
              </div>

              <div class="subtab-panel" id="stf-sub-dof">
                <div class="attr-group-box">
                  <div class="attr-group-header"><span class="attr-group-title">Kulübe Teknik Direktör Olarak Ata (DoF)</span></div>
                  <div class="form-grid">
                    <div class="form-field"><label>Hedef Kulüp UID</label><input type="number" class="input input-mono" id="dof-club-uid" placeholder="1909"></div>
                    <div class="form-field"><label>Sözleşme Süresi (Yıl)</label><input type="number" class="input input-mono" id="dof-years" value="3"></div>
                  </div>
                  <div style="margin-top:8px;display:flex;gap:8px;">
                    <button class="btn btn-amber" onclick="hireSelectedCoach()">Seçili Personeli Teknik Direktör Olarak Ata</button>
                    <button class="btn btn-blue" onclick="loadDofReport()">Kulüp Kadro & DoF Raporu Üret</button>
                  </div>
                  <div id="dof-report-box" style="margin-top:10px;font-size:12px;"></div>
                </div>
              </div>

              <div class="sticky-action-bar">
                <span class="card-sub">Personel nitelik, tercih, kişilik ve sözleşme alanlarını kaydeder.</span>
                <button class="btn btn-primary" onclick="saveStaffEdits(false)">Personel Değişikliklerini Kaydet</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ==================== TAB 4: WORLD, STANDINGS, TACTICS, LINEUP, WINDOWS & NAMES ==================== -->
    <section class="tab-pane" id="tab-world">
      <div class="grid-2">
        <!-- League Table Row Editor (Total + Home + Away) -->
        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">Lig Puan Durumu Editörü (Toplam + İç Saha + Deplasman)</div>
              <div class="card-sub">Bir takımın lig tablosundaki tüm istatistiklerini ayrıntılı olarak değiştirin</div>
            </div>
            <button class="btn btn-xs" onclick="loadLeagueTablePreview()">Tabloyu Yükle</button>
          </div>
          <div class="form-grid">
            <div class="form-field"><label>Takım ID (Team ID)</label><input type="number" class="input input-mono" id="lt-teamid" placeholder="Örn: 1909"></div>
            <div class="form-field"><label>Toplam Galibiyet (W)</label><input type="number" class="input input-mono" id="lt-w"></div>
            <div class="form-field"><label>Toplam Beraberlik (D)</label><input type="number" class="input input-mono" id="lt-d"></div>
            <div class="form-field"><label>Toplam Mağlubiyet (L)</label><input type="number" class="input input-mono" id="lt-l"></div>
            <div class="form-field"><label>Atılan Gol (GF)</label><input type="number" class="input input-mono" id="lt-gf"></div>
            <div class="form-field"><label>Yenilen Gol (GA)</label><input type="number" class="input input-mono" id="lt-ga"></div>
            <div class="form-field"><label>Toplam Puan (Pts)</label><input type="number" class="input input-mono" id="lt-pts"></div>
            <div class="form-field"><label>İç Saha G / B / M</label>
              <div style="display:flex;gap:3px;">
                <input type="number" class="input input-sm input-mono" id="lt-hw" placeholder="G" style="width:33%">
                <input type="number" class="input input-sm input-mono" id="lt-hd" placeholder="B" style="width:33%">
                <input type="number" class="input input-sm input-mono" id="lt-hl" placeholder="M" style="width:33%">
              </div>
            </div>
            <div class="form-field"><label>İç Saha GF / GA / Pts</label>
              <div style="display:flex;gap:3px;">
                <input type="number" class="input input-sm input-mono" id="lt-hgf" placeholder="GF" style="width:33%">
                <input type="number" class="input input-sm input-mono" id="lt-hga" placeholder="GA" style="width:33%">
                <input type="number" class="input input-sm input-mono" id="lt-hpts" placeholder="Pts" style="width:33%">
              </div>
            </div>
            <div class="form-field"><label>Deplasman G / B / M</label>
              <div style="display:flex;gap:3px;">
                <input type="number" class="input input-sm input-mono" id="lt-aw" placeholder="G" style="width:33%">
                <input type="number" class="input input-sm input-mono" id="lt-ad" placeholder="B" style="width:33%">
                <input type="number" class="input input-sm input-mono" id="lt-al" placeholder="M" style="width:33%">
              </div>
            </div>
            <div class="form-field"><label>Deplasman GF / GA / Pts</label>
              <div style="display:flex;gap:3px;">
                <input type="number" class="input input-sm input-mono" id="lt-agf" placeholder="GF" style="width:33%">
                <input type="number" class="input input-sm input-mono" id="lt-aga" placeholder="GA" style="width:33%">
                <input type="number" class="input input-sm input-mono" id="lt-apts" placeholder="Pts" style="width:33%">
              </div>
            </div>
          </div>
          <div style="margin-top:8px;">
            <button class="btn btn-primary" onclick="saveLeagueTableEdit()">Puan Durumu Satırını Kaydet</button>
          </div>
          <div class="table-wrap" style="max-height:170px;margin-top:8px;">
            <table>
              <thead><tr><th>Takım / ID</th><th>Pos</th><th>O</th><th>G</th><th>B</th><th>M</th><th>GF</th><th>GA</th><th>Puan</th></tr></thead>
              <tbody id="lt-preview-tbody"></tbody>
            </table>
          </div>
        </div>

        <!-- Tactics, 26-Man Lineup, Transfer Windows, Hall of Fame & Name Pool -->
        <div class="card" style="display:flex;flex-direction:column;gap:10px;">
          <div class="attr-group-box">
            <div class="attr-group-header"><span class="attr-group-title">Taktik Kaydı & 26 Kişilik Maç Kadrosu (Lineup Slot) Editörü</span></div>
            <div class="form-grid">
              <div class="form-field"><label>Taktik İndeksi</label><input type="number" class="input input-mono" id="tac-idx" value="0"></div>
              <div class="form-field"><label>Mentalite (1-20)</label><input type="number" class="input input-mono" id="tac-ment" placeholder="12"></div>
              <div class="form-field"><label>Stil Kodu</label><input type="text" class="input input-mono" id="tac-style" placeholder="gegenpress"></div>
              <div class="form-field"><label>Taktik Adı</label><input type="text" class="input" id="tac-name" placeholder="Özel 4-2-3-1"></div>
            </div>
            <div class="form-grid" style="margin-top:6px;">
              <div class="form-field"><label>Kadro Slot (0..25)</label><input type="number" min="0" max="25" class="input input-mono" id="lu-slot" placeholder="0 (GK)"></div>
              <div class="form-field"><label>Oyuncu UID veya Adı</label><input type="text" class="input input-mono" id="lu-player" placeholder="Oyuncu UID"></div>
              <div class="form-field"><label>Takım Blok İndeksi</label><input type="number" class="input input-mono" id="lu-block" value="0"></div>
            </div>
            <div style="margin-top:6px;display:flex;gap:6px;">
              <button class="btn btn-xs btn-primary" onclick="saveTacticAndLineupEdit()">Taktik / Kadro Yuvasını Kaydet</button>
            </div>
          </div>

          <div class="attr-group-box">
            <div class="attr-group-header"><span class="attr-group-title">Transfer Penceresi Tarihleri & Hall of Fame / İsim Havuzu</span></div>
            <div class="form-grid">
              <div class="form-field"><label>Pencere İndeksi</label><input type="number" class="input input-mono" id="tw-idx" value="0"></div>
              <div class="form-field"><label>Başlangıç Gün/Ay</label>
                <div style="display:flex;gap:4px;">
                  <input type="number" class="input input-sm input-mono" id="tw-sday" placeholder="Gün" style="width:50%">
                  <input type="number" class="input input-sm input-mono" id="tw-smon" placeholder="Ay" style="width:50%">
                </div>
              </div>
              <div class="form-field"><label>Bitiş Gün/Ay</label>
                <div style="display:flex;gap:4px;">
                  <input type="number" class="input input-sm input-mono" id="tw-eday" placeholder="Gün" style="width:50%">
                  <input type="number" class="input input-sm input-mono" id="tw-emon" placeholder="Ay" style="width:50%">
                </div>
              </div>
              <div class="form-field"><label>Pencere Türü</label><input type="number" class="input input-mono" id="tw-type" placeholder="1"></div>
            </div>
            <div class="form-grid" style="margin-top:6px;">
              <div class="form-field">
                <label>İsim Havuzu (Name Pool)</label>
                <select class="select input-sm" id="np-kind">
                  <option value="first_names">first_names (Ad)</option>
                  <option value="surnames">surnames (Soyad)</option>
                  <option value="common_names">common_names (Lakap)</option>
                </select>
              </div>
              <div class="form-field"><label>İsim ID (Name ID)</label><input type="number" class="input input-sm input-mono" id="np-id" placeholder="Örn: 120"></div>
              <div class="form-field"><label>Yeni İsim Metni</label><input type="text" class="input input-sm" id="np-val" placeholder="Yeni İsim"></div>
            </div>
            <div style="margin-top:6px;display:flex;gap:6px;flex-wrap:wrap;">
              <button class="btn btn-xs btn-blue" onclick="saveTransferWindowEdit()">Transfer Penceresini Kaydet</button>
              <button class="btn btn-xs btn-amber" onclick="saveNamePoolEdit()">İsim Havuzu Kaydını Değiştir</button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ==================== TAB 5: 28 TABLES & PRE-GAME DB EXPLORER ==================== -->
    <section class="tab-pane" id="tab-explorer">
      <div class="toolbar">
        <label style="font-weight:700;color:var(--text-muted);">Kayıt Tablosu (28 Tablo):</label>
        <select class="select" id="exp-table" onchange="loadSaveTable()"></select>
        <input type="text" class="input" id="exp-q" placeholder="Tablo içi JSON arama..." style="width:220px;" oninput="debouncedLoadSaveTable()">
        <select class="select" id="exp-limit" onchange="loadSaveTable()">
          <option value="100">100 Kayıt</option>
          <option value="250">250 Kayıt</option>
          <option value="500">500 Kayıt</option>
        </select>
        <button class="btn btn-primary" onclick="loadSaveTable()">Tabloyu Göster</button>
        <button class="btn" onclick="loadSaveSections()">81 Zstd Bölümü</button>
        <button class="btn btn-blue" onclick="loadPregameDb()">Oyun İçi Pre-Game DB (master_db)</button>
        <span class="card-sub" id="exp-status" style="margin-left:auto;"></span>
      </div>
      <div class="card" style="flex:1;overflow:auto;" id="exp-container"></div>
    </section>

    <!-- ==================== TAB 6: OPTIMIZATION SUITE ==================== -->
    <section class="tab-pane" id="tab-optimization">
      <div class="grid-4" id="opt-kpis"></div>

      <div class="grid-2">
        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">Unity 6000.0.55f1-fm Motor Parametreleri (`boot.config`) — 14+ Ayar</div>
              <div class="card-sub">Önayarları yardımcı olarak kullanabilir veya her bir motor anahtarını / özel anahtarları tek tek düzenleyebilirsiniz</div>
            </div>
            <div style="display:flex;gap:4px;flex-wrap:wrap;">
              <button class="btn btn-xs btn-primary" onclick="applyBootPreset('low_latency_max_fps')">Max FPS</button>
              <button class="btn btn-xs btn-blue" onclick="applyBootPreset('fast_simulation_multicore')">Hızlı Simülasyon</button>
              <button class="btn btn-xs" onclick="applyBootPreset('balanced')">Dengeli</button>
              <button class="btn btn-xs btn-amber" onclick="applyBootPreset('low_vram_laptop')">Düşük VRAM</button>
              <button class="btn btn-xs btn-danger" onclick="restoreBootConfig()">Yedekten Dön</button>
            </div>
          </div>

          <div id="boot-keys-form" style="display:flex;flex-direction:column;gap:8px;max-height:420px;overflow-y:auto;padding-right:4px;"></div>

          <div class="attr-group-box" style="margin-top:8px;">
            <div class="attr-group-header"><span class="attr-group-title">+ Özel `boot.config` Anahtarı Ekle (Custom Key=Value)</span></div>
            <div style="display:flex;gap:6px;align-items:center;">
              <input type="text" class="input input-sm input-mono" id="boot-custom-key" placeholder="Örn: gc-max-time-slice" style="flex:1;">
              <input type="text" class="input input-sm input-mono" id="boot-custom-val" placeholder="Değer (Örn: 2)" style="width:130px;">
              <button class="btn btn-xs btn-blue" onclick="addCustomBootKey()">Anahtar Ekle</button>
            </div>
          </div>

          <div style="margin-top:10px;display:flex;justify-content:flex-end;gap:8px;">
            <button class="btn btn-primary" onclick="saveBootConfigForm()">Formdaki `boot.config` Değerlerini Kaydet</button>
          </div>
        </div>

        <div class="card" style="display:flex;flex-direction:column;gap:12px;">
          <div class="attr-group-box">
            <div class="attr-group-header">
              <span class="attr-group-title">Doğrudan Ham `boot.config` Metin Editörü</span>
              <button class="btn btn-xs btn-primary" onclick="saveBootConfigRaw()">Ham Metni Doğrudan Kaydet</button>
            </div>
            <textarea id="boot-raw-textarea" class="input input-mono" style="width:100%;height:150px;resize:vertical;font-size:11.5px;"></textarea>
          </div>

          <div class="attr-group-box">
            <div class="attr-group-header">
              <span class="attr-group-title">Başlangıç & Lisans Videoları Bypass (`Videos_disabled`)</span>
              <div style="display:flex;gap:6px;">
                <button class="btn btn-xs btn-primary" onclick="toggleVideos(true)">Tüm Videoları Devre Dışı Bırak</button>
                <button class="btn btn-xs" onclick="toggleVideos(false)">Videoları Geri Yükle</button>
              </div>
            </div>
            <div class="table-wrap" style="max-height:145px;">
              <table>
                <thead><tr><th>Video Dosyası (.webm)</th><th>Boyut</th><th>Durum</th></tr></thead>
                <tbody id="opt-videos-tbody"></tbody>
              </table>
            </div>
          </div>

          <div class="attr-group-box">
            <div class="attr-group-header"><span class="attr-group-title">Unity URP Kalite Profilleri & Disk Dağılımı</span></div>
            <div id="opt-urp-badges" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px;"></div>
            <div class="table-wrap" style="max-height:145px;">
              <table>
                <thead><tr><th>Oyun Alt Klasörü</th><th>Dosya Adedi</th><th>Boyut (MB)</th></tr></thead>
                <tbody id="opt-disk-tbody"></tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ==================== TAB 7: GAME FILE & BUNDLE PATCHER ==================== -->
    <section class="tab-pane" id="tab-patches">
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">1. Native `game_plugin.dll` Oyuncu / Gözlemci Sınırı & Hazır UI Sıralama Yamaları</div>
            <div class="card-sub">50 oyuncu sınırını önayarla değil, istediğiniz herhangi bir tam sayıya (<code class="inline">1..100000</code>) ayarlayabilirsiniz. Her işlem öncesi <code class="inline">.bak</code> yedeği alınır.</div>
          </div>
          <div style="display:flex;gap:6px;">
            <button class="btn btn-blue" onclick="loadPatches(true)">Durumları Yeniden Tara</button>
            <button class="btn btn-primary" onclick="applyAllSortingPatches()">10 Hazır Sıralama Yamasını Uygula</button>
          </div>
        </div>
        <div class="table-wrap" style="max-height:310px;">
          <table>
            <thead>
              <tr>
                <th>Yama Anahtarı</th>
                <th>Hedef Dosya</th>
                <th>Açıklama</th>
                <th>Durum / Mevcut Değer</th>
                <th>Özel Değer / İşlem</th>
              </tr>
            </thead>
            <tbody id="patches-tbody"></tbody>
          </table>
        </div>
      </div>

      <div class="card" style="flex:1;display:flex;flex-direction:column;">
        <div class="card-header">
          <div>
            <div class="card-title">2. Evrensel `StreamedTable` Sıralama Kilidi Açıcı (252 Oyun İçi Tablo)</div>
            <div class="card-sub">UI bundle dosyalarındaki tüm <code class="inline">StreamedTable</code> nesnelerinin <code class="inline">m_disableSorting</code> bayrağını (<code class="inline">0 = Sıralanabilir</code>, <code class="inline">1 = Kilitli</code>) tek tek değiştirin</div>
          </div>
          <div style="display:flex;gap:8px;align-items:center;">
            <input type="text" class="input input-sm" id="st-filter-q" placeholder="Tablo veya Bundle ara..." oninput="renderStreamedTables()">
            <label style="display:flex;align-items:center;gap:5px;font-size:12px;cursor:pointer;">
              <input type="checkbox" id="st-only-unsortable" checked onchange="loadStreamedTables(true)"> Sadece Varsayılan Kilitli Tablolar
            </label>
          </div>
        </div>
        <div class="table-wrap" style="flex:1;">
          <table>
            <thead>
              <tr>
                <th>Bundle Dosyası</th>
                <th>Tablo (`m_name` / VTA)</th>
                <th>Ofset</th>
                <th>Veri Bağlantısı (Binding)</th>
                <th>Durum (`m_disableSorting`)</th>
                <th>İşlem</th>
              </tr>
            </thead>
            <tbody id="streamed-tables-tbody"></tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- ==================== TAB 8: RULES (.EDT / .LNC / .DBC) ==================== -->
    <section class="tab-pane" id="tab-rules">
      <div class="grid-2">
        <div class="card" style="display:flex;flex-direction:column;gap:10px;">
          <div class="card-header">
            <div>
              <div class="card-title">Görsel `sugardaddy.edt` Editörü</div>
              <div class="card-sub">Kulüplere <code class="inline">FRONT_END</code>, <code class="inline">BACK_END</code> veya <code class="inline">UNDERWRITER</code> zengin başkan tanımlayın</div>
            </div>
            <div style="display:flex;gap:6px;">
              <button class="btn btn-xs" onclick="addSugarDaddyRow()">+ Yeni Satır Ekle</button>
              <button class="btn btn-xs btn-primary" onclick="saveSugarDaddyEdt()">`sugardaddy.edt` Kaydet</button>
            </div>
          </div>
          <div class="table-wrap" style="max-height:240px;">
            <table>
              <thead><tr><th>Aktif</th><th>Kulüp Adı</th><th>Başkan Tipi</th><th>Başlangıç</th><th>Sil</th></tr></thead>
              <tbody id="sd-tbody"></tbody>
            </table>
          </div>

          <div class="attr-group-box">
            <div class="attr-group-header"><span class="attr-group-title">Tüm `.edt`, `.lnc` ve `.dbc` Kural Dosyaları</span></div>
            <div class="table-wrap" style="max-height:250px;">
              <table>
                <thead><tr><th>Kategori</th><th>Dosya Adı</th><th>Boyut</th><th>Durum</th><th>İşlem</th></tr></thead>
                <tbody id="rules-files-tbody"></tbody>
              </table>
            </div>
          </div>
        </div>

        <div class="card" style="display:flex;flex-direction:column;gap:10px;">
          <div class="card-header">
            <div>
              <div class="card-title">`.edt` & `.lnc` Komut Oluşturucu ve Doğrudan Kod Editörü</div>
              <div class="card-sub" id="rule-editor-path-label">Soldaki listeden bir `.edt` veya `.lnc` dosyasına tıklayın</div>
            </div>
            <button class="btn btn-primary" onclick="saveRuleTextFile()">Dosyayı Kaydet (.bak Yedekli)</button>
          </div>

          <div class="attr-group-box">
            <div class="attr-group-header"><span class="attr-group-title">Hızlı `.edt` / `.lnc` Direktif Ekle (Quick Directive Builder)</span></div>
            <div style="display:flex;gap:6px;flex-wrap:wrap;">
              <button class="btn btn-xs" onclick="insertDirectiveTemplate('BOOST_TEAM')">+ BOOST_TEAM (Bütçe & İtibar)</button>
              <button class="btn btn-xs" onclick="insertDirectiveTemplate('TRANSFER_EMBARGO')">+ TRANSFER_EMBARGO</button>
              <button class="btn btn-xs" onclick="insertDirectiveTemplate('START_IN_ADMIN')">+ START_IN_ADMIN (Kayyum)</button>
              <button class="btn btn-xs" onclick="insertDirectiveTemplate('CLUB_LONG_NAME_CHANGE')">+ CLUB_LONG_NAME_CHANGE (.lnc)</button>
              <button class="btn btn-xs" onclick="insertDirectiveTemplate('COMP_LONG_NAME_CHANGE')">+ COMP_LONG_NAME_CHANGE (.lnc)</button>
            </div>
          </div>

          <textarea id="rule-editor-textarea" class="input input-mono" style="width:100%;flex:1;min-height:360px;resize:vertical;font-size:12px;" placeholder="Bir .edt veya .lnc dosyası seçin..."></textarea>
        </div>
      </div>
    </section>

  </main>
</div>

<div id="toast-box"></div>
<script>
const STATE = {
  overview: null,
  terms: { player_attributes: {}, staff_attributes: {}, positions: {}, general: {}, groups: {} },
  selectedPlayerUid: null,
  selectedPlayerDetail: null,
  selectedClubUid: null,
  selectedClubDetail: null,
  selectedStaffUid: null,
  selectedStaffDetail: null,
  streamedTables: [],
  sugarDaddyEntries: [],
  activeRuleRelPath: null,
  activeRuleDbVersion: null,
  customBootKeys: {},
};

const PLAYER_ATTR_GROUPS_DEF = {
  technical: ["corners","crossing","dribbling","finishing","first_touch","free_kicks","heading","long_shots","long_throws","marking","passing","penalty_taking","tackling","technique"],
  mental: ["aggression","anticipation","bravery","composure","concentration","decisions","determination","flair","leadership","off_the_ball","positioning","teamwork","vision","work_rate"],
  physical: ["acceleration","agility","balance","jumping_reach","natural_fitness","pace","stamina","strength"],
  goalkeeping: ["aerial_reach","command_of_area","communication","eccentricity","handling","kicking","one_on_ones","punching","reflexes","rushing_out","throwing"],
  hidden: ["consistency","important_matches","injury_proneness","versatility","dirtiness"]
};

const POS_LIST_DEF = [
  ["GK","gk"],["SW","sw"],["DL","dl"],["DC","dc"],["DR","dr"],
  ["WBL","wbl"],["DM","dm"],["WBR","wbr"],["ML","ml"],["MC","mc"],
  ["MR","mr"],["AML","aml"],["AMC","amc"],["AMR","amr"],["ST","stc"]
];

let _debounceTimers = {};
function debounce(key, fn, delay = 220) {
  clearTimeout(_debounceTimers[key]);
  _debounceTimers[key] = setTimeout(fn, delay);
}
function debouncedLoadPlayers() { debounce('pl', loadPlayers); }
function debouncedLoadClubs() { debounce('cl', loadClubs); }
function debouncedLoadStaff() { debounce('stf', loadStaff); }
function debouncedLoadSaveTable() { debounce('exp', loadSaveTable); }

function showToast(msg, isError = false) {
  const box = document.getElementById('toast-box');
  const el = document.createElement('div');
  el.className = 'toast' + (isError ? ' error' : '');
  el.innerHTML = msg;
  box.appendChild(el);
  setTimeout(() => { el.remove(); }, 4200);
}

function fmtMoney(val) {
  if (val === null || val === undefined || isNaN(val)) return '-';
  const n = Number(val);
  const abs = Math.abs(n);
  if (abs >= 1e6) return (n / 1e6).toFixed(2) + 'M €';
  if (abs >= 1e3) return (n / 1e3).toFixed(0) + 'K €';
  return n.toLocaleString('tr-TR') + ' €';
}

function attrTierClass(val, rawScale = false) {
  const v = rawScale ? Math.round(Number(val) / 5) : Number(val);
  if (v >= 16) return 'tier-elite';
  if (v >= 12) return 'tier-good';
  if (v >= 8) return 'tier-avg';
  return 'tier-low';
}

async function apiGet(url) {
  const res = await fetch(url, { cache: 'no-store' });
  const data = await res.json();
  if (!res.ok || data.error) throw new Error(data.error || ('HTTP ' + res.status));
  return data;
}

async function apiPost(url, payload) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload || {})
  });
  const data = await res.json();
  if (!res.ok || data.error) throw new Error(data.error || ('HTTP ' + res.status));
  return data;
}

function switchTab(tabId) {
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tabId));
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.toggle('active', p.id === tabId));
  if (tabId === 'tab-players' && !document.getElementById('pl-tbody').children.length) loadPlayers();
  if (tabId === 'tab-clubs' && !document.getElementById('cl-tbody').children.length) loadClubs();
  if (tabId === 'tab-staff' && !document.getElementById('stf-tbody').children.length) loadStaff();
  if (tabId === 'tab-world' && !document.getElementById('lt-preview-tbody').children.length) loadLeagueTablePreview();
  if (tabId === 'tab-explorer' && !document.getElementById('exp-container').children.length) loadSaveTable();
  if (tabId === 'tab-optimization') loadOptimization();
  if (tabId === 'tab-patches') { loadPatches(false); loadStreamedTables(false); }
  if (tabId === 'tab-rules') loadRules();
}

function switchSubTab(prefix, subTabId) {
  const container = document.getElementById(prefix + '-inspector-body');
  if (!container) return;
  container.querySelectorAll('.subtab-btn').forEach(b => b.classList.toggle('active', b.dataset.subtab === subTabId));
  container.querySelectorAll('.subtab-panel').forEach(p => p.classList.toggle('active', p.id === subTabId));
}

function populateCatalogDropdowns() {
  if (!STATE.overview) return;
  const nations = STATE.overview.nations_catalog || [];
  const nationOpts = `<option value="">-- Ülke Seçin --</option>` + nations.map(n => `<option value="${n.id}">${n.tr} (${n.code || n.id})</option>`).join('');
  ['ed-pl-nation', 'ed-cl-nation', 'ed-stf-nation'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = nationOpts;
  });

  const sqStatuses = STATE.overview.squad_statuses_catalog || [];
  const sqEl = document.getElementById('ed-ct-status');
  if (sqEl) {
    sqEl.innerHTML = `<option value="">-- Statü Seç --</option>` + sqStatuses.map(s => `<option value="${s.code}">${s.code} — ${s.tr}</option>`).join('');
  }

  const stfRoles = STATE.overview.staff_roles_catalog || [];
  const srEl = document.getElementById('ed-stf-role');
  if (srEl) {
    srEl.innerHTML = `<option value="">-- Görev / Rol Seç (r4) --</option>` + stfRoles.map(r => `<option value="${r.code}">${r.code} — ${r.tr} (${r.en})</option>`).join('');
  }
}

async function initStudio() {
  try {
    const langSel = document.getElementById('sel-gamelang');
    const chosenLang = langSel.value || 'turkish';
    const ov = await apiGet('/api/overview?game_lang=' + encodeURIComponent(chosenLang));
    STATE.overview = ov;
    STATE.terms = ov.active_game_terms || STATE.terms;

    // Saves selector
    const selSave = document.getElementById('sel-save');
    selSave.innerHTML = (ov.available_saves || []).map(s =>
      `<option value="${s.path}" ${ov.active_save && ov.active_save.path === s.path ? 'selected' : ''}>${s.is_fm27 ? '[FM27] ' : ''}${s.name} (${s.size_mb} MB)</option>`
    ).join('');

    // FM Dir selector
    const selFm = document.getElementById('sel-fmdir');
    selFm.innerHTML = (ov.available_installs || []).map(i =>
      `<option value="${i.path}" ${ov.active_fm_dir === i.path ? 'selected' : ''}>[${i.label}] ${i.path}</option>`
    ).join('');

    // Game Languages selector
    if (!langSel.children.length) {
      langSel.innerHTML = (ov.game_languages || []).map(l =>
        `<option value="${l.code}" ${l.code === chosenLang ? 'selected' : ''}>${l.label} (${l.native})</option>`
      ).join('');
    }

    // Explorer tables
    const expTbl = document.getElementById('exp-table');
    if (expTbl && !expTbl.children.length) {
      expTbl.innerHTML = (ov.tables_catalog || []).map(t => `<option value="${t}">${t}</option>`).join('');
    }

    populateCatalogDropdowns();
    renderOverview();
    applyLocalizedLabels();
  } catch (err) {
    showToast('Başlatma hatası: ' + err.message, true);
  }
}

function renderOverview() {
  const ov = STATE.overview;
  if (!ov) return;
  const s = ov.active_save;
  document.getElementById('nav-cnt-players').textContent = s ? s.players_count.toLocaleString('tr-TR') : '-';
  document.getElementById('nav-cnt-clubs').textContent = s ? s.clubs_count.toLocaleString('tr-TR') : '-';
  document.getElementById('nav-cnt-staff').textContent = s ? s.staff_count.toLocaleString('tr-TR') : '-';

  const kpis = document.getElementById('overview-kpis');
  if (s) {
    kpis.innerHTML = `
      <div class="stat-card">
        <span class="stat-label">Aktif Kayıt & Oyun Tarihi</span>
        <span class="stat-val">${s.game_date}</span>
        <span class="stat-meta">${s.file} • Build ${s.build}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Oyuncu & Sözleşme Havuzu</span>
        <span class="stat-val">${s.players_count.toLocaleString('tr-TR')}</span>
        <span class="stat-meta">52 Nitelik + 15 Pozisyon + 64-bit Traits</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Kulüp, Finans & Stadyumlar</span>
        <span class="stat-val">${s.clubs_count.toLocaleString('tr-TR')} / ${s.stadiums_count.toLocaleString('tr-TR')}</span>
        <span class="stat-meta">Yönetilen: ${s.managed_club_name || ('#' + s.managed_club_uid)}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Teknik Heyet & Zstd Blokları</span>
        <span class="stat-val">${s.staff_count.toLocaleString('tr-TR')} / ${s.sections_count}</span>
        <span class="stat-meta">26 Nitelik + 17 Tercih + 50+ Rol</span>
      </div>
    `;
    document.getElementById('ov-game-date').value = s.game_date || '';
    document.getElementById('ov-save-path-label').textContent = s.path;
    document.getElementById('sidebar-save-meta').innerHTML = `<b>${s.file}</b><br>Tarih: ${s.game_date} • ${s.managed_club_name}`;
    const dofClub = document.getElementById('dof-club-uid');
    if (dofClub && !dofClub.value) dofClub.value = s.managed_club_uid || 1909;
  }

  renderLangPreview();
}

function renderLangPreview() {
  const t = STATE.terms || {};
  const pa = t.player_attributes || {};
  const pos = t.positions || {};
  const gen = t.general || {};
  document.getElementById('ov-lang-badge').textContent = (t.language_label || t.language || 'Turkish');
  const samples = [
    ['finishing', pa.finishing],
    ['passing', pa.passing],
    ['dribbling', pa.dribbling],
    ['tackling', pa.tackling],
    ['decisions', pa.decisions],
    ['anticipation', pa.anticipation],
    ['pace', pa.pace],
    ['stamina', pa.stamina],
    ['reflexes', pa.reflexes],
    ['GK', pos.gk],
    ['AMC', pos.amc],
    ['ST', pos.stc],
    ['CA', gen.current_ability],
    ['PA', gen.potential_ability],
  ];
  document.getElementById('ov-lang-preview').innerHTML = samples.map(([k, v]) =>
    `<span class="badge badge-blue"><b style="color:#fff;margin-right:4px;">${k}:</b> ${v || k}</span>`
  ).join('');
}

function applyLocalizedLabels() {
  const gen = (STATE.terms && STATE.terms.general) || {};
  if (gen.current_ability) document.getElementById('lbl-ca').textContent = `${gen.current_ability} (CA 0-200)`;
  if (gen.potential_ability) document.getElementById('lbl-pa').textContent = `${gen.potential_ability} (PA -10..200)`;
  if (gen.left_foot) document.getElementById('lbl-lfoot').textContent = `${gen.left_foot} (1-20)`;
  if (gen.right_foot) document.getElementById('lbl-rfoot').textContent = `${gen.right_foot} (1-20)`;
  renderLangPreview();
  if (STATE.selectedPlayerDetail) renderPlayerInspector(STATE.selectedPlayerDetail);
  if (STATE.selectedStaffDetail) renderStaffInspector(STATE.selectedStaffDetail);
}

async function onContextChange() {
  try {
    const save_path = document.getElementById('sel-save').value;
    const fm_dir = document.getElementById('sel-fmdir').value;
    const ov = await apiPost('/api/context', { save_path, fm_dir });
    STATE.overview = ov;
    if (ov.active_game_terms) STATE.terms = ov.active_game_terms;
    populateCatalogDropdowns();
    renderOverview();
    applyLocalizedLabels();
    const activePane = document.querySelector('.tab-pane.active');
    if (activePane) switchTab(activePane.id);
    showToast('Aktif kayıt / oyun dizini güncellendi.');
  } catch (err) {
    showToast('Bağlam değiştirilemedi: ' + err.message, true);
  }
}

async function onGameLangChange() {
  try {
    const lang = document.getElementById('sel-gamelang').value;
    const terms = await apiGet('/api/game-terms?lang=' + encodeURIComponent(lang));
    STATE.terms = terms;
    applyLocalizedLabels();
    showToast(`Oyun içi terim dili "${terms.language_label || lang}" olarak güncellendi.`);
  } catch (err) {
    showToast('Dil değiştirilemedi: ' + err.message, true);
  }
}

async function refreshAll() {
  await initStudio();
  const activePane = document.querySelector('.tab-pane.active');
  if (activePane) switchTab(activePane.id);
  showToast('Bellek önbelleği ve veriler yenilendi.');
}

async function saveGlobalDate() {
  try {
    const game_date = document.getElementById('ov-game-date').value.trim();
    const output_path = document.getElementById('global-output-path').value.trim();
    if (!game_date) return showToast('Lütfen geçerli bir YYYY-MM-DD tarihi girin.', true);
    const res = await apiPost('/api/save-edit', { game_date, output_path });
    showToast(`Oyun tarihi ${game_date} olarak kaydedildi → ${res.output_path}`);
    await initStudio();
  } catch (err) {
    showToast('Tarih kaydedilemedi: ' + err.message, true);
  }
}

/* ==================== TAB 1: PLAYERS ==================== */
async function loadPlayers() {
  try {
    const q = document.getElementById('pl-q').value.trim();
    const pos = document.getElementById('pl-pos').value;
    const club = document.getElementById('pl-club').value.trim();
    const min_ca = document.getElementById('pl-min-ca').value || '0';
    const max_age = document.getElementById('pl-max-age').value || '99';
    const sort_by = document.getElementById('pl-sort').value;
    const limit = document.getElementById('pl-limit').value || '100';

    const qs = new URLSearchParams({ q, pos, club, min_ca, max_age, sort_by, limit });
    const data = await apiGet('/api/players?' + qs.toString());
    document.getElementById('pl-count-label').textContent = `Eşleşen: ${data.total.toLocaleString('tr-TR')} oyuncu (Gösterilen: ${data.rows.length})`;

    const tbody = document.getElementById('pl-tbody');
    tbody.innerHTML = data.rows.map(p => `
      <tr id="pl-row-${p.uid}" class="${STATE.selectedPlayerUid === p.uid ? 'selected-row' : ''}" onclick="selectPlayer(${p.uid})">
        <td style="font-family:var(--font-mono);color:var(--text-muted);">${p.uid}</td>
        <td><b>${p.name}</b> <span style="color:var(--text-dim);font-size:10.5px;">(${p.nationality || ''})</span></td>
        <td>${p.age}</td>
        <td><span class="badge badge-blue">${p.best_pos || '-'}</span></td>
        <td><span class="badge badge-green">${p.ca}</span></td>
        <td><span class="badge badge-purple">${p.pa}</span></td>
        <td>${p.club || 'Serbest'}</td>
        <td style="font-family:var(--font-mono);">${fmtMoney(p.wage)}</td>
        <td style="font-family:var(--font-mono);">${fmtMoney(p.value)}</td>
      </tr>
    `).join('');

    if (!STATE.selectedPlayerUid && data.rows.length > 0) {
      selectPlayer(data.rows[0].uid);
    }
  } catch (err) {
    showToast('Oyuncular yüklenemedi: ' + err.message, true);
  }
}

async function selectPlayer(uid) {
  if (!uid) return;
  try {
    const t0 = performance.now();
    STATE.selectedPlayerUid = uid;
    document.querySelectorAll('#pl-tbody tr').forEach(tr => tr.classList.toggle('selected-row', tr.id === 'pl-row-' + uid));
    const detail = await apiGet('/api/player-detail?uid=' + uid);
    const dt = (performance.now() - t0).toFixed(1);
    document.getElementById('sidebar-perf-pill').innerHTML = `<span class="status-dot"></span> Son Detay Sorgusu: ${dt} ms`;
    STATE.selectedPlayerDetail = detail;
    renderPlayerInspector(detail);
  } catch (err) {
    showToast('Oyuncu detayı alınamadı: ' + err.message, true);
  }
}

function renderPlayerInspector(d) {
  const s = d.summary;
  document.getElementById('pl-inspector-body').style.display = 'flex';
  document.getElementById('pl-ed-title').innerHTML = `${s.name} <span class="badge badge-green">CA ${s.ca} / PA ${s.pa}</span> <span class="badge badge-blue">${s.best_pos}</span>`;
  document.getElementById('pl-ed-sub').textContent = `UID: ${s.uid} • Kulüp: ${s.club || 'Serbest'} (#${s.club_uid}) • Uyruk: ${s.nationality} • Doğum: ${s.birth_date}`;

  // Subtab 1: Identity & Physical
  document.getElementById('ed-pl-ca').value = s.ca ?? 0;
  document.getElementById('ed-pl-pa').value = s.pa ?? 0;
  document.getElementById('ed-pl-hrep').value = s.home_rep ?? 0;
  document.getElementById('ed-pl-crep').value = s.current_rep ?? 0;
  document.getElementById('ed-pl-wrep').value = s.world_rep ?? 0;
  document.getElementById('ed-pl-repbucket').value = s.reputation_bucket ?? 0;
  document.getElementById('ed-pl-val').value = s.value ?? 0;
  document.getElementById('ed-pl-cond').value = s.condition ?? 100;
  document.getElementById('ed-pl-sharp').value = s.sharpness ?? 100;
  document.getElementById('ed-pl-club-uid').value = s.club_uid ?? 0;
  document.getElementById('ed-pl-teamslot').value = String(s.team_slot ?? 0);
  document.getElementById('ed-pl-joindate').value = s.club_join_date || '';
  document.getElementById('ed-pl-bdate').value = s.birth_date || '';
  document.getElementById('ed-pl-age').value = s.age ?? 20;
  document.getElementById('ed-pl-nation').value = String(s.nation_id ?? s.nationality_id ?? '');
  document.getElementById('ed-pl-height').value = s.height_cm ?? 180;
  document.getElementById('ed-pl-shirt').value = s.squad_number != null ? s.squad_number : '';
  document.getElementById('ed-pl-bodytype').value = s.body_type_code != null ? s.body_type_code : '';
  document.getElementById('ed-pl-lfoot').value = s.left_foot ?? 10;
  document.getElementById('ed-pl-rfoot').value = s.right_foot ?? 20;

  // Populate club dropdown if needed
  populatePlayerClubSelect(s.club_uid);

  // Subtab 2: 52 Attributes
  renderPlayerAttributesGrid();

  // Subtab 3: 15 Positions & 6D Roles
  const posTerms = (STATE.terms && STATE.terms.positions) || {};
  const posVals = d.positions || {};
  document.getElementById('pl-pos-grid').innerHTML = POS_LIST_DEF.map(([code, tkey]) => {
    const val = posVals[code] ?? 1;
    const isNat = val >= 18;
    return `
      <div class="pos-cell ${isNat ? 'natural' : ''}">
        <span class="pos-code">${code}</span>
        <span class="pos-term">${posTerms[tkey] || code}</span>
        <input type="number" min="1" max="20" class="attr-input ${attrTierClass(val)} ed-pos-input" data-pos="${code}" value="${val}">
      </div>
    `;
  }).join('');

  const rb = d.role_breakdown || {};
  const renderRoleList = (title, arr) => `
    <div style="background:var(--bg-input);padding:8px;border-radius:6px;border:1px solid var(--border);">
      <div style="font-size:10.5px;font-weight:800;color:var(--accent);margin-bottom:5px;text-transform:uppercase;">${title}</div>
      ${(arr || []).map(r => `<div style="display:flex;justify-content:space-between;font-size:11.5px;padding:2px 0;"><span>${r.role_tr || r.role}</span><b style="color:#34d399;font-family:var(--font-mono);">${Number(r.score || r.combined_score || 0).toFixed(1)}</b></div>`).join('')}
    </div>
  `;
  document.getElementById('pl-roles-box').innerHTML =
    renderRoleList('Top 5 Topla Oyun (IP)', rb.top_in_possession) +
    renderRoleList('Top 5 Topsuz Oyun (OOP)', rb.top_out_of_possession) +
    renderRoleList('Top 5 Çift Yönlü Kombinasyon', rb.top_combinations);

  // Subtab 4: 8 Personality & 64-Bit Traits
  const persCatalog = (STATE.overview && STATE.overview.personality_fields) || [];
  const persVals = d.personality || {};
  document.getElementById('pl-pers-grid').innerHTML = persCatalog.map(([key, tr, en]) => {
    const v = persVals[key] ?? 10;
    return `
      <div class="form-field">
        <label>${tr}</label>
        <input type="number" min="1" max="20" class="input input-mono ed-pers-input" data-pers="${key}" value="${v}">
      </div>
    `;
  }).join('');

  const traitMaskStr = d.trait_bits_str != null ? String(d.trait_bits_str) : String(d.trait_bits ?? '0');
  document.getElementById('ed-pl-trait-raw').value = traitMaskStr;
  renderTraitChips(BigInt(traitMaskStr || '0'));

  // Subtab 5: Contract & Clauses
  const ct = d.contract || {};
  document.getElementById('ed-ct-wage').value = ct.wage ?? 0;
  document.getElementById('ed-ct-start').value = ct.start_date || '';
  document.getElementById('ed-ct-end').value = ct.end_date || '';
  document.getElementById('ed-ct-status').value = ct.squad_status != null ? String(ct.squad_status) : '';
  document.getElementById('ed-ct-type').value = String(ct.contract_type ?? 1);
  document.getElementById('ed-ct-signfee').value = ct.signing_or_loyalty_fee ?? 0;
  document.getElementById('ed-ct-agentfee').value = ct.agent_fee ?? 0;
  document.getElementById('ed-ct-pkgbonus').value = ct.package_bonus ?? 0;
  document.getElementById('ed-ct-opyear').value = ct.option_or_reference_year ?? '';

  const clauses = ct.clauses || [];
  const clauseCatalog = (STATE.overview && STATE.overview.clause_kinds_catalog) || [];
  const clauseBox = document.getElementById('pl-clauses-box');
  if (!clauses.length) {
    clauseBox.innerHTML = `<div class="card-sub">Bu oyuncunun sözleşmesinde tanımlı özel madde (clause) bulunmuyor.</div>`;
  } else {
    clauseBox.innerHTML = clauses.map((cl, idx) => {
      const opts = clauseCatalog.map(ck => `<option value="${ck.code}" ${ck.code === cl.kind ? 'selected' : ''}>0x${ck.code.toString(16).toUpperCase()} — ${ck.tr}</option>`).join('');
      return `
        <div class="form-grid ed-clause-row" data-index="${cl.index}" style="margin-bottom:6px;padding:6px;background:var(--bg-input);border-radius:6px;border:1px solid var(--border);">
          <div class="form-field" style="grid-column: span 2;">
            <label>Madde #${idx + 1} Türü (${cl.kind_name})</label>
            <select class="select input-sm cl-kind">${opts}<option value="${cl.kind}" ${!clauseCatalog.some(c=>c.code===cl.kind)?'selected':''}>Kod ${cl.kind} (${cl.kind_name})</option></select>
          </div>
          <div class="form-field">
            <label>Tutar / Bedel (£/€)</label>
            <input type="number" class="input input-sm input-mono cl-val" value="${cl.value ?? 0}">
          </div>
          <div class="form-field">
            <label>Parametre / Maç Sayısı</label>
            <input type="number" class="input input-sm input-mono cl-param" value="${cl.parameter ?? ''}">
          </div>
        </div>
      `;
    }).join('');
  }

  // Subtab 6: Season Stats
  populateSeasonStatsSlot();
}

async function populatePlayerClubSelect(selectedUid) {
  const sel = document.getElementById('ed-pl-club-select');
  if (!sel) return;
  if (!sel.children.length) {
    try {
      const data = await apiGet('/api/clubs?limit=300');
      sel.innerHTML = `<option value="0">0 — Serbest Oyuncu (Free Agent)</option>` +
        (data.rows || []).map(c => `<option value="${c.uid}">${c.name} (#${c.uid})</option>`).join('');
    } catch (_) {}
  }
  sel.value = String(selectedUid || 0);
}

function renderPlayerAttributesGrid() {
  const d = STATE.selectedPlayerDetail;
  if (!d) return;
  const rawScale = document.getElementById('ed-pl-raw-scale').checked;
  document.getElementById('pl-scale-hint').textContent = rawScale
    ? 'Şu an: 1–100 Ham (Internal Raw) Ölçek (Oyunda /5 olarak görünür)'
    : 'Şu an: 1–20 Görünür Oyun Ölçeği';

  const attrTerms = (STATE.terms && STATE.terms.player_attributes) || {};
  const grpTerms = (STATE.terms && STATE.terms.groups) || {};
  const srcAttrs = rawScale ? (d.raw_attributes || {}) : (d.attributes || {});
  const maxVal = rawScale ? 100 : 20;

  const groupTitles = {
    technical: grpTerms.technical || 'Teknik (14)',
    mental: grpTerms.mental || 'Zihinsel (14)',
    physical: grpTerms.physical || 'Fiziksel (8)',
    goalkeeping: grpTerms.goalkeeping || 'Kalecilik (11)',
    hidden: grpTerms.hidden || 'Gizli Nitelikler (5)',
  };

  document.getElementById('pl-attrs-grid').innerHTML = Object.entries(PLAYER_ATTR_GROUPS_DEF).map(([grpKey, cols]) => {
    const rowsHtml = cols.map(col => {
      const val = srcAttrs[col] ?? (rawScale ? 50 : 10);
      const label = attrTerms[col] || col;
      return `
        <div class="attr-row">
          <span class="attr-name" title="${col}">${label}</span>
          <input type="number" min="1" max="${maxVal}" class="attr-input ${attrTierClass(val, rawScale)} ed-attr-input"
            data-attr="${col}" data-group="${grpKey}" value="${val}"
            oninput="this.className='attr-input ' + attrTierClass(this.value, ${rawScale}) + ' ed-attr-input'">
        </div>
      `;
    }).join('');
    return `
      <div class="attr-group-box">
        <div class="attr-group-header">
          <span class="attr-group-title">${groupTitles[grpKey]}</span>
          <div style="display:flex;gap:3px;">
            <button class="btn btn-xs" onclick="setGroupAttrs('${grpKey}', ${rawScale ? 80 : 16})">16</button>
            <button class="btn btn-xs btn-primary" onclick="setGroupAttrs('${grpKey}', ${maxVal})">${maxVal}</button>
          </div>
        </div>
        ${rowsHtml}
      </div>
    `;
  }).join('');
}

function togglePlayerAttrScale() {
  renderPlayerAttributesGrid();
}

function setGroupAttrs(grpKey, val) {
  const rawScale = document.getElementById('ed-pl-raw-scale').checked;
  document.querySelectorAll(`.ed-attr-input[data-group="${grpKey}"]`).forEach(inp => {
    inp.value = val;
    inp.className = 'attr-input ' + attrTierClass(val, rawScale) + ' ed-attr-input';
  });
}

function adjustAllPlayerAttrs(delta) {
  const rawScale = document.getElementById('ed-pl-raw-scale').checked;
  const maxVal = rawScale ? 100 : 20;
  const step = rawScale ? delta * 5 : delta;
  document.querySelectorAll('.ed-attr-input').forEach(inp => {
    const nv = Math.max(1, Math.min(maxVal, ( parseInt(inp.value, 10) || 10 ) + step));
    inp.value = nv;
    inp.className = 'attr-input ' + attrTierClass(nv, rawScale) + ' ed-attr-input';
  });
}

function setAllPlayerAttrsPrompt() {
  const rawScale = document.getElementById('ed-pl-raw-scale').checked;
  const maxVal = rawScale ? 100 : 20;
  const v = prompt(`Tüm 52 niteliği hangi değere ayarlamak istiyorsunuz? (1..${maxVal})`, String(maxVal));
  if (!v) return;
  const nv = Math.max(1, Math.min(maxVal, parseInt(v, 10) || maxVal));
  document.querySelectorAll('.ed-attr-input').forEach(inp => {
    inp.value = nv;
    inp.className = 'attr-input ' + attrTierClass(nv, rawScale) + ' ed-attr-input';
  });
}

function setAllPositions(val) {
  document.querySelectorAll('.ed-pos-input').forEach(inp => {
    inp.value = val;
    inp.className = 'attr-input ' + attrTierClass(val) + ' ed-pos-input';
  });
}

function presetModelCitizenPersonality() {
  const ideal = { adaptability: 20, ambition: 20, controversy: 1, loyalty: 20, pressure: 20, professionalism: 20, sportsmanship: 20, temperament: 20 };
  document.querySelectorAll('.ed-pers-input').forEach(inp => {
    const k = inp.dataset.pers;
    if (ideal[k] !== undefined) inp.value = ideal[k];
  });
  showToast('Model Vatandaş kişilik değerleri forma aktarıldı.');
}

function renderTraitChips(maskBig) {
  const traits = (STATE.overview && STATE.overview.player_traits_catalog) || [];
  document.getElementById('pl-traits-grid').innerHTML = traits.map(t => {
    const on = ((maskBig >> BigInt(t.bit)) & 1n) === 1n;
    return `
      <div class="trait-chip ${on ? 'active' : ''}" onclick="toggleTraitBit(${t.bit})">
        <input type="checkbox" ${on ? 'checked' : ''} style="pointer-events:none;">
        <span><b>Bit ${t.bit}:</b> ${t.tr}</span>
      </div>
    `;
  }).join('');

  const activeBits = [];
  for (let b = 0n; b <= 63n; b++) {
    if (((maskBig >> b) & 1n) === 1n) activeBits.push(Number(b));
  }
  document.getElementById('pl-active-bits-label').textContent = activeBits.length
    ? `Aktif Bitler: [${activeBits.join(', ')}]`
    : 'Aktif bit yok (0)';
}

function toggleTraitBit(bit) {
  const rawEl = document.getElementById('ed-pl-trait-raw');
  let mask = BigInt(rawEl.value || '0');
  mask ^= (1n << BigInt(bit));
  rawEl.value = mask.toString();
  renderTraitChips(mask);
}

function toggleCustomTraitBit() {
  const bit = parseInt(document.getElementById('ed-pl-custom-bit').value, 10);
  if (isNaN(bit) || bit < 0 || bit > 63) return showToast('Lütfen 0 ile 63 arasında bir bit numarası girin.', true);
  toggleTraitBit(bit);
}

function syncTraitChipsFromRaw() {
  const rawEl = document.getElementById('ed-pl-trait-raw');
  renderTraitChips(BigInt(rawEl.value || '0'));
}

function populateSeasonStatsSlot() {
  const d = STATE.selectedPlayerDetail;
  if (!d) return;
  const slotName = document.getElementById('ed-ss-slot').value;
  const slotMap = { league: 0, cup: 1, continental: 2 };
  const idx = slotMap[slotName] ?? 0;
  const list = d.season_stats || [];
  const row = list[idx] || {};
  document.getElementById('ed-ss-starts').value = row.starts ?? '';
  document.getElementById('ed-ss-subs').value = row.substitute_appearances ?? '';
  document.getElementById('ed-ss-goals').value = row.goals ?? '';
  document.getElementById('ed-ss-assists').value = row.assists ?? '';
  document.getElementById('ed-ss-yc').value = row.yellow_cards ?? '';
  document.getElementById('ed-ss-rc').value = row.red_cards ?? '';
  document.getElementById('ed-ss-pom').value = row.player_of_the_match ?? '';
  document.getElementById('ed-ss-pent').value = row.penalties_taken ?? '';
  document.getElementById('ed-ss-pens').value = row.penalties_scored ?? '';
  document.getElementById('ed-ss-mins').value = row.minutes ?? '';
  document.getElementById('ed-ss-passa').value = row.passes_attempted ?? '';
  document.getElementById('ed-ss-passc').value = row.passes_completed ?? '';
}

function presetPlayerWonderkid() {
  document.getElementById('ed-pl-ca').value = 175;
  document.getElementById('ed-pl-pa').value = 200;
  document.getElementById('ed-pl-cond').value = 100;
  document.getElementById('ed-pl-sharp').value = 100;
  showToast('Wonderkid değerleri forma dolduruldu — istediğiniz alanı değiştirip Kaydet\'e basabilirsiniz.');
}

function presetPlayerFitness() {
  document.getElementById('ed-pl-cond').value = 100;
  document.getElementById('ed-pl-sharp').value = 100;
  document.getElementById('ed-pl-heal').checked = true;
  document.getElementById('ed-pl-unsuspend').checked = true;
  showToast('%100 Kondisyon & Keskinlik forma dolduruldu.');
}

async function savePlayerEdits(maxOut = false) {
  if (!STATE.selectedPlayerUid) return;
  try {
    const rawScale = document.getElementById('ed-pl-raw-scale').checked;
    const attributes = {};
    document.querySelectorAll('.ed-attr-input').forEach(inp => {
      attributes[inp.dataset.attr] = parseInt(inp.value, 10);
    });
    const positions = {};
    document.querySelectorAll('.ed-pos-input').forEach(inp => {
      positions[inp.dataset.pos] = parseInt(inp.value, 10);
    });
    const personality = {};
    document.querySelectorAll('.ed-pers-input').forEach(inp => {
      personality[inp.dataset.pers] = parseInt(inp.value, 10);
    });

    const clause_updates = [];
    document.querySelectorAll('.ed-clause-row').forEach(row => {
      clause_updates.push({
        index: parseInt(row.dataset.index, 10),
        kind: parseInt(row.querySelector('.cl-kind').value, 10),
        value: parseInt(row.querySelector('.cl-val').value || '0', 10),
        parameter: row.querySelector('.cl-param').value !== '' ? parseInt(row.querySelector('.cl-param').value, 10) : null,
      });
    });

    const payload = {
      output_path: document.getElementById('global-output-path').value.trim(),
      player_uid: STATE.selectedPlayerUid,
      max_out_player: maxOut,
      heal_injuries: document.getElementById('ed-pl-heal').checked,
      clear_suspensions: document.getElementById('ed-pl-unsuspend').checked,
      raw_attribute_scale: rawScale,
      trait_bits: document.getElementById('ed-pl-trait-raw').value,
      player_fields: {
        ca: document.getElementById('ed-pl-ca').value,
        pa: document.getElementById('ed-pl-pa').value,
        home_rep: document.getElementById('ed-pl-hrep').value,
        current_rep: document.getElementById('ed-pl-crep').value,
        world_rep: document.getElementById('ed-pl-wrep').value,
        reputation_bucket: document.getElementById('ed-pl-repbucket').value,
        value: document.getElementById('ed-pl-val').value,
        condition: document.getElementById('ed-pl-cond').value,
        sharpness: document.getElementById('ed-pl-sharp').value,
        club_uid: document.getElementById('ed-pl-club-uid').value,
        team_slot: document.getElementById('ed-pl-teamslot').value,
        club_join_date: document.getElementById('ed-pl-joindate').value,
        birth_date: document.getElementById('ed-pl-bdate').value,
        age: document.getElementById('ed-pl-age').value,
        nation_id: document.getElementById('ed-pl-nation').value,
        height_cm: document.getElementById('ed-pl-height').value,
        squad_number: document.getElementById('ed-pl-shirt').value,
        body_type_code: document.getElementById('ed-pl-bodytype').value,
        left_foot: document.getElementById('ed-pl-lfoot').value,
        right_foot: document.getElementById('ed-pl-rfoot').value,
      },
      attributes,
      positions,
      personality,
      contract_fields: {
        wage: document.getElementById('ed-ct-wage').value,
        start_date: document.getElementById('ed-ct-start').value,
        end_date: document.getElementById('ed-ct-end').value,
        squad_status: document.getElementById('ed-ct-status').value,
        contract_type: document.getElementById('ed-ct-type').value,
        signing_or_loyalty_fee: document.getElementById('ed-ct-signfee').value,
        agent_fee: document.getElementById('ed-ct-agentfee').value,
        package_bonus: document.getElementById('ed-ct-pkgbonus').value,
        option_or_reference_year: document.getElementById('ed-ct-opyear').value,
      },
      clause_updates,
      season_stats_fields: {
        slot: document.getElementById('ed-ss-slot').value,
        starts: document.getElementById('ed-ss-starts').value,
        substitute_appearances: document.getElementById('ed-ss-subs').value,
        goals: document.getElementById('ed-ss-goals').value,
        assists: document.getElementById('ed-ss-assists').value,
        yellow_cards: document.getElementById('ed-ss-yc').value,
        red_cards: document.getElementById('ed-ss-rc').value,
        player_of_the_match: document.getElementById('ed-ss-pom').value,
        penalties_taken: document.getElementById('ed-ss-pent').value,
        penalties_scored: document.getElementById('ed-ss-pens').value,
        minutes: document.getElementById('ed-ss-mins').value,
        passes_attempted: document.getElementById('ed-ss-passa').value,
        passes_completed: document.getElementById('ed-ss-passc').value,
      }
    };

    const res = await apiPost('/api/save-edit', payload);
    showToast(`Oyuncu düzenlemeleri kaydedildi: ${res.output_path}`);
    await initStudio();
    await loadPlayers();
    await selectPlayer(STATE.selectedPlayerUid);
  } catch (err) {
    showToast('Oyuncu kaydedilemedi: ' + err.message, true);
  }
}

/* ==================== TAB 2: CLUBS, FINANCES, SPONSORSHIPS & STADIUMS ==================== */
async function loadClubs() {
  try {
    const q = document.getElementById('cl-q').value.trim();
    const sort_by = document.getElementById('cl-sort').value;
    const data = await apiGet(`/api/clubs?q=${encodeURIComponent(q)}&sort_by=${encodeURIComponent(sort_by)}&limit=150`);
    document.getElementById('cl-count-label').textContent = `Toplam: ${data.total.toLocaleString('tr-TR')} kulüp`;

    document.getElementById('cl-tbody').innerHTML = data.rows.map(c => `
      <tr id="cl-row-${c.uid}" class="${STATE.selectedClubUid === c.uid ? 'selected-row' : ''}" onclick="selectClub(${c.uid})">
        <td style="font-family:var(--font-mono);color:var(--text-muted);">${c.uid}</td>
        <td><b>${c.name}</b> <span style="color:var(--text-dim);font-size:10.5px;">(${c.nationality || ''})</span></td>
        <td><span class="badge badge-blue">${c.reputation}</span></td>
        <td style="font-family:var(--font-mono);">${fmtMoney(c.balance)}</td>
        <td style="font-family:var(--font-mono);color:#34d399;">${fmtMoney(c.transfer_budget)}</td>
        <td style="font-family:var(--font-mono);">${fmtMoney(c.wage_budget)}</td>
        <td>${c.stadium_name ? `${c.stadium_name} (${c.stadium_capacity.toLocaleString('tr-TR')})` : '-'}</td>
      </tr>
    `).join('');

    if (!STATE.selectedClubUid && data.rows.length > 0) {
      selectClub(data.rows[0].uid);
    }
  } catch (err) {
    showToast('Kulüpler yüklenemedi: ' + err.message, true);
  }
}

async function selectClub(uid) {
  try {
    STATE.selectedClubUid = uid;
    document.querySelectorAll('#cl-tbody tr').forEach(tr => tr.classList.toggle('selected-row', tr.id === 'cl-row-' + uid));
    const d = await apiGet('/api/club-detail?uid=' + uid);
    STATE.selectedClubDetail = d;
    const c = d.club;
    document.getElementById('cl-inspector-body').style.display = 'flex';
    document.getElementById('cl-ed-title').innerHTML = `${c.name} <span class="badge badge-blue">İtibar ${c.reputation}</span>`;
    document.getElementById('cl-ed-sub').textContent = `UID: ${c.uid} • Ülke: ${c.nationality} • Kadro: ${(d.squad || []).length} Oyuncu • Stadyum: ${c.stadium_name || '-'}`;

    document.getElementById('ed-cl-name').value = c.name || '';
    document.getElementById('ed-cl-short').value = c.short_name || '';
    document.getElementById('ed-cl-rep').value = c.reputation ?? 0;
    document.getElementById('ed-cl-lastpos').value = c.last_league_pos ?? '';
    document.getElementById('ed-cl-nation').value = String(c.nation_id ?? '');
    document.getElementById('ed-cl-fanation').value = c.fa_nation_id ?? '';
    document.getElementById('ed-cl-city').value = c.city_id ?? '';
    document.getElementById('ed-cl-corpfac').value = c.corporate_facilities ?? '';

    // 11 Finance fields
    document.getElementById('ed-cl-bal').value = c.balance ?? '';
    document.getElementById('ed-cl-tbud').value = c.transfer_budget ?? '';
    document.getElementById('ed-cl-tbud-alloc').value = c.transfer_budget_allocated ?? '';
    document.getElementById('ed-cl-wbud').value = c.wage_budget ?? '';
    document.getElementById('ed-cl-wpay').value = c.wage_payroll ?? '';
    document.getElementById('ed-cl-incex').value = c.income_excluding_transfers ?? '';
    document.getElementById('ed-cl-expex').value = c.expenditure_excluding_transfers ?? '';
    document.getElementById('ed-cl-nettr').value = c.net_transfers ?? '';
    document.getElementById('ed-cl-wbill').value = c.wage_bill ?? '';
    document.getElementById('ed-cl-totinc').value = c.total_income ?? '';
    document.getElementById('ed-cl-totexp').value = c.total_expenditure ?? '';
    document.getElementById('ed-cl-monthidx').value = -1;

    document.getElementById('cl-fin-series-tbody').innerHTML = (d.finance_series || []).slice(-12).reverse().map(f => `
      <tr>
        <td style="font-family:var(--font-mono);">${f.month}</td>
        <td style="font-family:var(--font-mono);">${fmtMoney(f.balance)}</td>
        <td style="font-family:var(--font-mono);">${fmtMoney(f.transfer_budget_remaining)}</td>
        <td style="font-family:var(--font-mono);">${fmtMoney(f.wage_budget_weekly)}</td>
        <td style="font-family:var(--font-mono);">${fmtMoney(f.total_income)}</td>
        <td style="font-family:var(--font-mono);">${fmtMoney(f.total_expenditure)}</td>
      </tr>
    `).join('');

    // Sponsorships
    const sps = d.sponsorships || [];
    const spBox = document.getElementById('cl-sponsors-box');
    if (!sps.length) {
      spBox.innerHTML = `<div class="card-sub">Bu kulüp için kayıtlı sponsorluk anlaşması bulunamadı.</div>`;
    } else {
      spBox.innerHTML = sps.map(sp => `
        <div class="form-grid ed-sponsor-row" data-index="${sp.index}" style="margin-bottom:6px;padding:6px;background:var(--bg-input);border-radius:6px;border:1px solid var(--border);">
          <div class="form-field"><label>Anlaşma #${sp.index + 1} Tür Kodu</label><input type="number" class="input input-sm input-mono sp-kind" value="${sp.kind}"></div>
          <div class="form-field"><label>Başlangıç</label><input type="text" class="input input-sm input-mono sp-start" value="${sp.start}"></div>
          <div class="form-field"><label>Bitiş</label><input type="text" class="input input-sm input-mono sp-end" value="${sp.end}"></div>
          <div class="form-field"><label>Yıllık Değer (£/€)</label><input type="number" class="input input-sm input-mono sp-annual" value="${sp.annual_value ?? 0}"></div>
          <div class="form-field"><label>Toplam Değer (£/€)</label><input type="number" class="input input-sm input-mono sp-total" value="${sp.total_value ?? 0}"></div>
        </div>
      `).join('');
    }

    // Stadium
    const st = d.stadium || {};
    document.getElementById('ed-st-uid').value = st.uid ?? '';
    document.getElementById('ed-st-name').value = st.name || '';
    document.getElementById('ed-st-cap').value = st.capacity ?? '';
    document.getElementById('ed-st-seat').value = st.all_seater_capacity ?? '';
    document.getElementById('ed-st-exp').value = st.expansion_capacity ?? '';
    document.getElementById('ed-st-owner').value = st.owner_club_uid ?? '';
    document.getElementById('ed-st-plen').value = st.pitch_length_dm ?? '';
    document.getElementById('ed-st-pwid').value = st.pitch_width_dm ?? '';
    document.getElementById('ed-st-minlen').value = st.pitch_min_length_dm ?? '';
    document.getElementById('ed-st-maxlen').value = st.pitch_max_length_dm ?? '';
    document.getElementById('ed-st-minwid').value = st.pitch_min_width_dm ?? '';
    document.getElementById('ed-st-maxwid').value = st.pitch_max_width_dm ?? '';
    document.getElementById('ed-st-built').value = st.built_date || '';
    document.getElementById('ed-st-rebuilt').value = st.rebuilt_date || '';
  } catch (err) {
    showToast('Kulüp detayı alınamadı: ' + err.message, true);
  }
}

function presetClubSugarDaddy() {
  document.getElementById('ed-cl-bal').value = 250000000;
  document.getElementById('ed-cl-tbud').value = 250000000;
  document.getElementById('ed-cl-tbud-alloc').value = 250000000;
  document.getElementById('ed-cl-wbud').value = 6000000;
  showToast('+250M€ Bakiye ve Transfer Bütçesi forma dolduruldu.');
}

async function saveClubAndStadiumEdits() {
  if (!STATE.selectedClubUid) return;
  try {
    const sponsorship_updates = [];
    document.querySelectorAll('.ed-sponsor-row').forEach(row => {
      sponsorship_updates.push({
        index: parseInt(row.dataset.index, 10),
        kind: row.querySelector('.sp-kind').value,
        start_date: row.querySelector('.sp-start').value,
        end_date: row.querySelector('.sp-end').value,
        annual_value: row.querySelector('.sp-annual').value,
        total_value: row.querySelector('.sp-total').value,
      });
    });

    const stUid = document.getElementById('ed-st-uid').value;
    const payload = {
      output_path: document.getElementById('global-output-path').value.trim(),
      club_uid: STATE.selectedClubUid,
      club_fields: {
        name: document.getElementById('ed-cl-name').value,
        short_name: document.getElementById('ed-cl-short').value,
        reputation: document.getElementById('ed-cl-rep').value,
        last_league_position: document.getElementById('ed-cl-lastpos').value,
        nation_id: document.getElementById('ed-cl-nation').value,
        fa_nation_id: document.getElementById('ed-cl-fanation').value,
        city_id: document.getElementById('ed-cl-city').value,
        corporate_facilities: document.getElementById('ed-cl-corpfac').value,
        balance: document.getElementById('ed-cl-bal').value,
        transfer_budget: document.getElementById('ed-cl-tbud').value,
        transfer_budget_allocated: document.getElementById('ed-cl-tbud-alloc').value,
        wage_budget: document.getElementById('ed-cl-wbud').value,
        wage_payroll: document.getElementById('ed-cl-wpay').value,
        income_excluding_transfers: document.getElementById('ed-cl-incex').value,
        expenditure_excluding_transfers: document.getElementById('ed-cl-expex').value,
        net_transfers: document.getElementById('ed-cl-nettr').value,
        wage_bill: document.getElementById('ed-cl-wbill').value,
        total_income: document.getElementById('ed-cl-totinc').value,
        total_expenditure: document.getElementById('ed-cl-totexp').value,
        month_index: document.getElementById('ed-cl-monthidx').value,
      },
      sponsorship_updates,
    };

    if (stUid) {
      payload.stadium_uid = parseInt(stUid, 10);
      payload.stadium_fields = {
        name: document.getElementById('ed-st-name').value,
        capacity: document.getElementById('ed-st-cap').value,
        all_seater_capacity: document.getElementById('ed-st-seat').value,
        expansion_capacity: document.getElementById('ed-st-exp').value,
        owner_club_uid: document.getElementById('ed-st-owner').value,
        pitch_length_dm: document.getElementById('ed-st-plen').value,
        pitch_width_dm: document.getElementById('ed-st-pwid').value,
        pitch_min_length_dm: document.getElementById('ed-st-minlen').value,
        pitch_max_length_dm: document.getElementById('ed-st-maxlen').value,
        pitch_min_width_dm: document.getElementById('ed-st-minwid').value,
        pitch_max_width_dm: document.getElementById('ed-st-maxwid').value,
        built_date: document.getElementById('ed-st-built').value,
        rebuilt_date: document.getElementById('ed-st-rebuilt').value,
      };
    }

    const res = await apiPost('/api/save-edit', payload);
    showToast(`Kulüp, finans ve stadyum değişiklikleri kaydedildi: ${res.output_path}`);
    await initStudio();
    await loadClubs();
    await selectClub(STATE.selectedClubUid);
  } catch (err) {
    showToast('Kulüp kaydedilemedi: ' + err.message, true);
  }
}

/* ==================== TAB 3: STAFF, COACHES & DOF ==================== */
async function loadStaff() {
  try {
    const q = document.getElementById('stf-q').value.trim();
    const role = document.getElementById('stf-role').value.trim();
    const data = await apiGet(`/api/staff?q=${encodeURIComponent(q)}&role=${encodeURIComponent(role)}&limit=150`);
    document.getElementById('stf-count-label').textContent = `Eşleşen: ${data.total.toLocaleString('tr-TR')} personel`;

    document.getElementById('stf-tbody').innerHTML = data.rows.map(s => `
      <tr id="stf-row-${s.uid}" class="${STATE.selectedStaffUid === s.uid ? 'selected-row' : ''}" onclick="selectStaff(${s.uid})">
        <td style="font-family:var(--font-mono);color:var(--text-muted);">${s.uid}</td>
        <td><b>${s.name || ('Staff #' + s.uid)}</b></td>
        <td><span class="badge badge-blue">${s.role_name || '-'}</span></td>
        <td>${s.club_name || 'Boşta'}</td>
        <td><span class="badge badge-green">${s.ca || 0}</span></td>
        <td><span class="badge badge-purple">${s.pa || 0}</span></td>
        <td>${s.age || '-'}</td>
      </tr>
    `).join('');

    if (!STATE.selectedStaffUid && data.rows.length > 0) {
      selectStaff(data.rows[0].uid);
    }
  } catch (err) {
    showToast('Personel listesi alınamadı: ' + err.message, true);
  }
}

async function selectStaff(uid) {
  try {
    STATE.selectedStaffUid = uid;
    document.querySelectorAll('#stf-tbody tr').forEach(tr => tr.classList.toggle('selected-row', tr.id === 'stf-row-' + uid));
    const d = await apiGet('/api/staff-detail?uid=' + uid);
    STATE.selectedStaffDetail = d;
    renderStaffInspector(d);
  } catch (err) {
    showToast('Personel detayı alınamadı: ' + err.message, true);
  }
}

function renderStaffInspector(d) {
  const s = d.summary || {};
  document.getElementById('stf-inspector-body').style.display = 'flex';
  document.getElementById('stf-ed-title').innerHTML = `${s.name || ('Staff #' + s.uid)} <span class="badge badge-green">CA ${s.ca || 0} / PA ${s.pa || 0}</span>`;
  document.getElementById('stf-ed-sub').textContent = `UID: ${s.uid} • Görev: ${s.role_name || '-'} (r4=${s.role_code_r4 ?? '-'}) • Kulüp: ${s.club_name || 'Boşta'}`;

  document.getElementById('ed-stf-ca').value = s.ca ?? 0;
  document.getElementById('ed-stf-pa').value = s.pa ?? 0;
  document.getElementById('ed-stf-role').value = s.role_code_r4 != null ? String(s.role_code_r4) : '';
  document.getElementById('ed-stf-bdate').value = s.birth_date || '';
  document.getElementById('ed-stf-age').value = s.age ?? '';
  document.getElementById('ed-stf-nation').value = String(s.nation_id ?? '');
  document.getElementById('ed-stf-wage').value = s.wage ?? '';
  document.getElementById('ed-stf-cstart').value = s.contract_start || '';
  document.getElementById('ed-stf-cend').value = s.contract_end || '';
  document.getElementById('ed-stf-teamid').value = s.team_id ?? '';

  const stfTerms = (STATE.terms && STATE.terms.staff_attributes) || {};
  const b20 = d.block40_20 || {};
  document.getElementById('stf-attrs-grid').innerHTML = Object.entries(b20).map(([k, v]) => `
    <div class="form-field">
      <label title="${k}">${stfTerms[k] || k}</label>
      <input type="number" min="1" max="20" class="input input-mono ed-stf-attr" data-attr="${k}" value="${v ?? 10}">
    </div>
  `).join('');

  const prefCatalog = (STATE.overview && STATE.overview.staff_preference_fields) || [];
  const prefs = d.preferences || {};
  document.getElementById('stf-prefs-grid').innerHTML = prefCatalog.map(([k, tr, en]) => `
    <div class="form-field">
      <label>${tr}</label>
      <input type="number" min="1" max="20" class="input input-mono ed-stf-pref" data-pref="${k}" value="${prefs[k] ?? 10}">
    </div>
  `).join('');

  const persCatalog = (STATE.overview && STATE.overview.personality_fields) || [];
  const pers = d.personality || {};
  document.getElementById('stf-pers-grid').innerHTML = persCatalog.map(([k, tr, en]) => `
    <div class="form-field">
      <label>${tr}</label>
      <input type="number" min="1" max="20" class="input input-mono ed-stf-pers" data-pers="${k}" value="${pers[k] ?? 10}">
    </div>
  `).join('');
}

function setAllStaffAttrs(val) {
  document.querySelectorAll('.ed-stf-attr').forEach(inp => inp.value = val);
}

async function saveStaffEdits(maxOut = false) {
  if (!STATE.selectedStaffUid) return;
  try {
    const staff_attributes = {};
    document.querySelectorAll('.ed-stf-attr').forEach(inp => staff_attributes[inp.dataset.attr] = parseInt(inp.value, 10));
    const staff_preferences = {};
    document.querySelectorAll('.ed-stf-pref').forEach(inp => staff_preferences[inp.dataset.pref] = parseInt(inp.value, 10));
    const staff_personality = {};
    document.querySelectorAll('.ed-stf-pers').forEach(inp => staff_personality[inp.dataset.pers] = parseInt(inp.value, 10));

    const payload = {
      output_path: document.getElementById('global-output-path').value.trim(),
      staff_uid: STATE.selectedStaffUid,
      max_out_staff: maxOut,
      staff_fields: {
        ca: document.getElementById('ed-stf-ca').value,
        pa: document.getElementById('ed-stf-pa').value,
        role_r4: document.getElementById('ed-stf-role').value,
        birth_date: document.getElementById('ed-stf-bdate').value,
        age: document.getElementById('ed-stf-age').value,
        nation_id: document.getElementById('ed-stf-nation').value,
        wage: document.getElementById('ed-stf-wage').value,
        contract_start: document.getElementById('ed-stf-cstart').value,
        contract_end: document.getElementById('ed-stf-cend').value,
        team_id: document.getElementById('ed-stf-teamid').value,
      },
      staff_attributes,
      staff_preferences,
      staff_personality,
    };

    const res = await apiPost('/api/save-edit', payload);
    showToast(`Personel değişiklikleri kaydedildi: ${res.output_path}`);
    await initStudio();
    await loadStaff();
    await selectStaff(STATE.selectedStaffUid);
  } catch (err) {
    showToast('Personel kaydedilemedi: ' + err.message, true);
  }
}

async function hireSelectedCoach() {
  if (!STATE.selectedStaffUid) return showToast('Önce soldan bir teknik direktör seçin.', true);
  try {
    const club_uid = document.getElementById('dof-club-uid').value || 1909;
    const years = document.getElementById('dof-years').value || 3;
    const res = await apiPost('/api/dof-hire', { coach: STATE.selectedStaffUid, club_uid, years });
    showToast(`Personel #${STATE.selectedStaffUid} kulüp #${club_uid} teknik direktörü olarak atandı.`);
    await initStudio();
    await loadStaff();
  } catch (err) {
    showToast('Teknik direktör atanamadı: ' + err.message, true);
  }
}

async function loadDofReport() {
  try {
    switchSubTab('stf', 'stf-sub-dof');
    const club_uid = document.getElementById('dof-club-uid').value || '';
    const coach = STATE.selectedStaffUid || '';
    const d = await apiGet(`/api/dof?club_uid=${encodeURIComponent(club_uid)}&coach=${encodeURIComponent(coach)}`);
    const box = document.getElementById('dof-report-box');
    const sinfo = d.save_info || {};
    const cap = d.capology || {};
    const fit = d.coach_squad_fit || {};
    const topFit = (fit.best_fits || []).slice(0, 5);
    const misfits = (fit.misfits || []).slice(0, 3);
    box.innerHTML = `
      <div style="padding:10px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;display:flex;flex-direction:column;gap:6px;">
        <div><b>Kulüp:</b> ${sinfo.managed_club_name || ('#' + (sinfo.managed_club_uid || club_uid))} • <b>Kadro Boyutu:</b> ${cap.squad_size ?? '-'} • <b>Yıllık Maaş:</b> ${fmtMoney(cap.total_annual_payroll)}</div>
        ${fit.coach ? `
          <div><b>Analiz Edilen Hoca:</b> ${fit.coach.name} (CA ${fit.coach.ca || '-'}) • <b>Diziliş:</b> ${fit.preferred_formation || '-'} • <b>Stil:</b> ${fit.tactical_style || '-'} • <span class="badge badge-green">Kadro Uyum: ${fit.average_squad_fit ?? '-'}/100</span></div>
          <div style="font-weight:700;color:var(--accent);margin-top:2px;">En Yüksek Taktiksel Uyumlu Oyuncular:</div>
          ${topFit.map(p => `<div style="display:flex;justify-content:space-between;padding:2px 0;"><span>${p.name} (${p.best_role || p.position || '-'})</span><span class="badge badge-green">Uyum ${p.fit_score ?? p.score ?? '-'}</span></div>`).join('')}
          ${misfits.length ? `<div style="font-weight:700;color:var(--amber);margin-top:2px;">Sistem Uyumsuzluğu Riski Olanlar:</div>` + misfits.map(p => `<div style="display:flex;justify-content:space-between;padding:2px 0;"><span>${p.name}</span><span class="badge badge-amber">Uyum ${p.fit_score ?? p.score ?? '-'}</span></div>`).join('') : ''}
        ` : `<div class="card-sub">Taktiksel kadro uyum analizi için soldaki tablodan bir teknik direktör seçin.</div>`}
      </div>
    `;
  } catch (err) {
    showToast('DoF raporu oluşturulamadı: ' + err.message, true);
  }
}

/* ==================== TAB 4: WORLD, STANDINGS, TACTICS, LINEUP, WINDOWS & NAMES ==================== */
async function loadLeagueTablePreview() {
  try {
    const data = await apiGet('/api/league-tables?limit=100');
    const tbody = document.getElementById('lt-preview-tbody');
    tbody.innerHTML = (data.rows || []).map(r => {
      const tot = r.total || {};
      const hm = r.home || {};
      const aw = r.away || {};
      return `
        <tr onclick='fillLeagueRowForm(${JSON.stringify({team_id:r.team_id, tot, hm, aw})})'>
          <td><b>${r.club_name || ('#' + r.team_id)}</b> <span style="font-family:var(--font-mono);color:var(--text-muted);font-size:10.5px;">(#${r.team_id})</span></td>
          <td>${r.position ?? '-'}</td>
          <td>${tot.played ?? '-'}</td>
          <td>${tot.won ?? '-'}</td>
          <td>${tot.drawn ?? '-'}</td>
          <td>${tot.lost ?? '-'}</td>
          <td>${tot.goals_for ?? '-'}</td>
          <td>${tot.goals_against ?? '-'}</td>
          <td><span class="badge badge-green">${tot.points ?? '-'}</span></td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    showToast('Puan durumu yüklenemedi: ' + err.message, true);
  }
}

function fillLeagueRowForm(d) {
  document.getElementById('lt-teamid').value = d.team_id ?? '';
  document.getElementById('lt-w').value = d.tot.won ?? '';
  document.getElementById('lt-d').value = d.tot.drawn ?? '';
  document.getElementById('lt-l').value = d.tot.lost ?? '';
  document.getElementById('lt-gf').value = d.tot.goals_for ?? '';
  document.getElementById('lt-ga').value = d.tot.goals_against ?? '';
  document.getElementById('lt-pts').value = d.tot.points ?? '';
  document.getElementById('lt-hw').value = d.hm.won ?? '';
  document.getElementById('lt-hd').value = d.hm.drawn ?? '';
  document.getElementById('lt-hl').value = d.hm.lost ?? '';
  document.getElementById('lt-hgf').value = d.hm.goals_for ?? '';
  document.getElementById('lt-hga').value = d.hm.goals_against ?? '';
  document.getElementById('lt-hpts').value = d.hm.points ?? '';
  document.getElementById('lt-aw').value = d.aw.won ?? '';
  document.getElementById('lt-ad').value = d.aw.drawn ?? '';
  document.getElementById('lt-al').value = d.aw.lost ?? '';
  document.getElementById('lt-agf').value = d.aw.goals_for ?? '';
  document.getElementById('lt-aga').value = d.aw.goals_against ?? '';
  document.getElementById('lt-apts').value = d.aw.points ?? '';
}

async function saveLeagueTableEdit() {
  try {
    const team_id = document.getElementById('lt-teamid').value;
    if (!team_id) return showToast('Takım ID girin veya tablodan bir satıra tıklayın.', true);
    const res = await apiPost('/api/save-edit', {
      output_path: document.getElementById('global-output-path').value.trim(),
      league_table_edit: {
        team_id,
        won: document.getElementById('lt-w').value,
        drawn: document.getElementById('lt-d').value,
        lost: document.getElementById('lt-l').value,
        goals_for: document.getElementById('lt-gf').value,
        goals_against: document.getElementById('lt-ga').value,
        points: document.getElementById('lt-pts').value,
        home_won: document.getElementById('lt-hw').value,
        home_drawn: document.getElementById('lt-hd').value,
        home_lost: document.getElementById('lt-hl').value,
        home_goals_for: document.getElementById('lt-hgf').value,
        home_goals_against: document.getElementById('lt-hga').value,
        home_points: document.getElementById('lt-hpts').value,
        away_won: document.getElementById('lt-aw').value,
        away_drawn: document.getElementById('lt-ad').value,
        away_lost: document.getElementById('lt-al').value,
        away_goals_for: document.getElementById('lt-agf').value,
        away_goals_against: document.getElementById('lt-aga').value,
        away_points: document.getElementById('lt-apts').value,
      }
    });
    showToast(`Puan durumu kaydedildi: ${res.output_path}`);
    loadLeagueTablePreview();
  } catch (err) {
    showToast('Puan durumu kaydedilemedi: ' + err.message, true);
  }
}

async function saveTacticAndLineupEdit() {
  try {
    const body = { output_path: document.getElementById('global-output-path').value.trim() };
    const ment = document.getElementById('tac-ment').value;
    const style = document.getElementById('tac-style').value.trim();
    const tname = document.getElementById('tac-name').value.trim();
    if (ment || style || tname) {
      body.tactic_edit = {
        tactic_index: document.getElementById('tac-idx').value || 0,
        mentality: ment,
        style_code: style,
        name: tname,
      };
    }
    const slot = document.getElementById('lu-slot').value;
    const player = document.getElementById('lu-player').value.trim();
    if (slot !== '' && player !== '') {
      body.lineup_edit = {
        slot_index: slot,
        player,
        team_block_index: document.getElementById('lu-block').value || 0,
      };
    }
    const res = await apiPost('/api/save-edit', body);
    showToast(`Taktik / Kadro yuvası kaydedildi: ${res.output_path}`);
  } catch (err) {
    showToast('Taktik kaydedilemedi: ' + err.message, true);
  }
}

async function saveTransferWindowEdit() {
  try {
    const res = await apiPost('/api/save-edit', {
      output_path: document.getElementById('global-output-path').value.trim(),
      transfer_window_edit: {
        window_index: document.getElementById('tw-idx').value || 0,
        start_day: document.getElementById('tw-sday').value,
        start_month: document.getElementById('tw-smon').value,
        end_day: document.getElementById('tw-eday').value,
        end_month: document.getElementById('tw-emon').value,
        window_type: document.getElementById('tw-type').value,
      }
    });
    showToast(`Transfer penceresi kaydedildi: ${res.output_path}`);
  } catch (err) {
    showToast('Transfer penceresi kaydedilemedi: ' + err.message, true);
  }
}

async function saveNamePoolEdit() {
  try {
    const pool_kind = document.getElementById('np-kind').value;
    const name_id = document.getElementById('np-id').value;
    const new_name = document.getElementById('np-val').value.trim();
    if (!name_id || !new_name) return showToast('İsim ID ve Yeni İsim girin.', true);
    const res = await apiPost('/api/save-edit', {
      output_path: document.getElementById('global-output-path').value.trim(),
      name_pool_edit: { pool_kind, name_id, new_name }
    });
    showToast(`İsim havuzu (${pool_kind} #${name_id} → ${new_name}) kaydedildi: ${res.output_path}`);
  } catch (err) {
    showToast('İsim havuzu değiştirilemedi: ' + err.message, true);
  }
}

/* ==================== TAB 5: 28 TABLES & PRE-GAME DB EXPLORER ==================== */
async function loadSaveTable() {
  try {
    const tbl = document.getElementById('exp-table').value || 'players';
    const q = document.getElementById('exp-q').value.trim();
    const limit = document.getElementById('exp-limit').value || '100';
    document.getElementById('exp-status').textContent = `${tbl} tablosu yükleniyor...`;
    const data = await apiGet(`/api/save-table?table=${encodeURIComponent(tbl)}&q=${encodeURIComponent(q)}&limit=${encodeURIComponent(limit)}`);
    document.getElementById('exp-status').textContent = `Tablo: ${data.table} • Toplam Kayıt: ${data.total.toLocaleString('tr-TR')}`;
    renderGenericJsonTable(data.rows || []);
  } catch (err) {
    showToast('Tablo yüklenemedi: ' + err.message, true);
  }
}

async function loadSaveSections() {
  try {
    const data = await apiGet('/api/save-sections');
    document.getElementById('exp-status').textContent = `81 Zstd Blok Listesi (${(data.sections || []).length} bölüm)`;
    renderGenericJsonTable(data.sections || []);
  } catch (err) {
    showToast('Zstd blokları alınamadı: ' + err.message, true);
  }
}

async function loadPregameDb() {
  try {
    document.getElementById('exp-status').textContent = 'Pre-Game Master DB taranıyor...';
    const data = await apiGet('/api/pregame-db');
    const mdb = data.master_db || {};
    const tables = mdb.tables || mdb.client_db_tables || mdb.server_db_tables || [];
    document.getElementById('exp-status').textContent = `Pre-Game Master DB (${tables.length} TPKB Tablosu)`;
    renderGenericJsonTable(tables);
  } catch (err) {
    showToast('Pre-game DB alınamadı: ' + err.message, true);
  }
}

function renderGenericJsonTable(rows) {
  const box = document.getElementById('exp-container');
  if (!rows || !rows.length) {
    box.innerHTML = `<div class="card-sub">Kayıt bulunamadı.</div>`;
    return;
  }
  const cols = Object.keys(rows[0]).slice(0, 14);
  box.innerHTML = `
    <div class="table-wrap" style="max-height:100%;">
      <table>
        <thead><tr>${cols.map(c => `<th>${c}</th>`).join('')}</tr></thead>
        <tbody>
          ${rows.map(r => `<tr>${cols.map(c => {
            const v = r[c];
            const txt = (v !== null && typeof v === 'object') ? JSON.stringify(v).slice(0, 90) : String(v ?? '');
            return `<td style="font-family:var(--font-mono);font-size:11.5px;">${txt}</td>`;
          }).join('')}</tr>`).join('')}
        </tbody>
      </table>
    </div>
  `;
}

/* ==================== TAB 6: OPTIMIZATION SUITE ==================== */
async function loadOptimization() {
  try {
    const d = await apiGet('/api/optimization');
    const bc = d.boot_config || {};
    const vids = d.intro_videos || {};
    const disk = d.disk_footprint || {};

    document.getElementById('opt-kpis').innerHTML = `
      <div class="stat-card">
        <span class="stat-label">Toplam Kurulum Boyutu</span>
        <span class="stat-val">${disk.total_gb || 0} GB</span>
        <span class="stat-meta">${(disk.subdirectories || []).length} Alt Klasör</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Motor Parametreleri (boot.config)</span>
        <span class="stat-val">${Object.keys(bc.values || {}).length} Anahtar</span>
        <span class="stat-meta">${bc.backup_exists ? '.bak Yedeği Mevcut' : 'Orijinal Dosya'}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Başlangıç Videoları</span>
        <span class="stat-val">${vids.bypass_active ? 'Bypass Aktif' : 'Açık'}</span>
        <span class="stat-meta">${vids.active_count || 0} Aktif / ${vids.disabled_count || 0} Devre Dışı</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Unity 6 URP Profilleri</span>
        <span class="stat-val">${(d.urp_quality_tiers || []).length} Profil</span>
        <span class="stat-meta">Very Low → High</span>
      </div>
    `;

    // Render categorized 14+ boot.config keys
    const schema = bc.known_keys_schema || {};
    const curVals = bc.values || {};
    const byCat = {};
    Object.entries(schema).forEach(([k, meta]) => {
      const cat = meta.category || 'Diğer';
      (byCat[cat] = byCat[cat] || []).push([k, meta]);
    });

    // Also include any custom keys present in boot.config not in schema
    Object.keys(curVals).forEach(k => {
      if (!schema[k]) {
        (byCat['Özel (Kullanıcı Tanımlı) Anahtarlar'] = byCat['Özel (Kullanıcı Tanımlı) Anahtarlar'] || []).push([
          k, { label_tr: k, desc_tr: 'Kullanıcı tanımlı özel Unity boot.config parametresi', default: curVals[k] }
        ]);
      }
    });

    document.getElementById('boot-keys-form').innerHTML = Object.entries(byCat).map(([cat, items]) => `
      <div class="attr-group-box">
        <div class="attr-group-header"><span class="attr-group-title">${cat}</span></div>
        ${items.map(([k, meta]) => `
          <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;padding:4px 0;border-bottom:1px solid rgba(30,43,72,0.4);">
            <div style="flex:1;">
              <div style="font-weight:700;font-size:12px;color:#fff;">${meta.label_tr || k} <code class="inline">${k}</code></div>
              <div style="font-size:10.5px;color:var(--text-muted);">${meta.desc_tr || ''}</div>
            </div>
            <input type="text" class="input input-sm input-mono ed-boot-key" data-key="${k}" value="${curVals[k] ?? ''}" placeholder="${meta.default ?? ''}" style="width:135px;text-align:right;">
          </div>
        `).join('')}
      </div>
    `).join('');

    document.getElementById('boot-raw-textarea').value = bc.raw_text || '';

    document.getElementById('opt-videos-tbody').innerHTML = (vids.videos || []).map(v => `
      <tr>
        <td style="font-family:var(--font-mono);">${v.name}</td>
        <td>${v.size_mb} MB</td>
        <td><span class="badge ${v.status === 'disabled' ? 'badge-green' : 'badge-amber'}">${v.status === 'disabled' ? 'Devre Dışı (Hızlı Açılış)' : 'Aktif'}</span></td>
      </tr>
    `).join('');

    document.getElementById('opt-urp-badges').innerHTML = (d.urp_quality_tiers || []).map(t =>
      `<span class="badge badge-purple">${t.tier} (${t.bundle})</span>`
    ).join('');

    document.getElementById('opt-disk-tbody').innerHTML = (disk.subdirectories || []).map(s => `
      <tr>
        <td><b>${s.name}</b></td>
        <td style="font-family:var(--font-mono);">${s.files}</td>
        <td style="font-family:var(--font-mono);">${s.size_mb.toLocaleString('tr-TR')} MB</td>
      </tr>
    `).join('');
  } catch (err) {
    showToast('Optimizasyon verisi alınamadı: ' + err.message, true);
  }
}

function addCustomBootKey() {
  const k = document.getElementById('boot-custom-key').value.trim();
  const v = document.getElementById('boot-custom-val').value.trim();
  if (!k) return showToast('Lütfen bir anahtar adı girin.', true);
  const rawArea = document.getElementById('boot-raw-textarea');
  rawArea.value = (rawArea.value.trim() + `\n${k}=${v}\n`).trim() + '\n';
  saveBootConfigRaw();
}

async function saveBootConfigForm() {
  try {
    const values = {};
    document.querySelectorAll('.ed-boot-key').forEach(inp => {
      const v = inp.value.trim();
      if (v !== '') values[inp.dataset.key] = v;
    });
    await apiPost('/api/optimization/boot-config', { values });
    showToast('`boot.config` parametreleri kaydedildi (.bak yedekli).');
    loadOptimization();
  } catch (err) {
    showToast('boot.config kaydedilemedi: ' + err.message, true);
  }
}

async function saveBootConfigRaw() {
  try {
    const raw_text = document.getElementById('boot-raw-textarea').value;
    await apiPost('/api/optimization/boot-config', { raw_text });
    showToast('Ham `boot.config` metni doğrudan kaydedildi.');
    loadOptimization();
  } catch (err) {
    showToast('Ham boot.config kaydedilemedi: ' + err.message, true);
  }
}

async function applyBootPreset(preset) {
  try {
    await apiPost('/api/optimization/boot-preset', { preset });
    showToast(`"${preset}" önayarı uygulandı — tüm alanları aşağıdan özelleştirmeye devam edebilirsiniz.`);
    loadOptimization();
  } catch (err) {
    showToast('Önayar uygulanamadı: ' + err.message, true);
  }
}

async function restoreBootConfig() {
  try {
    await apiPost('/api/optimization/boot-restore', {});
    showToast('Orijinal `boot.config` yedekten geri yüklendi.');
    loadOptimization();
  } catch (err) {
    showToast('Geri yüklenemedi: ' + err.message, true);
  }
}

async function toggleVideos(disable) {
  try {
    await apiPost('/api/optimization/videos-toggle', { disable });
    showToast(disable ? 'Başlangıç videoları devre dışı bırakıldı.' : 'Başlangıç videoları geri yüklendi.');
    loadOptimization();
  } catch (err) {
    showToast('Video işlemi başarısız: ' + err.message, true);
  }
}

/* ==================== TAB 7: GAME FILE & BUNDLE PATCHER ==================== */
async function loadPatches(force = false) {
  try {
    const data = await apiGet('/api/patches' + (force ? '?refresh=1' : ''));
    const patches = data.patches || [];
    document.getElementById('patches-tbody').innerHTML = patches.map(p => {
      const isLimit = (p.key === 'scout-player-limit' || p.key === 'custom-Work-Space-player-limit');
      const isPatched = Boolean(p.is_patched || p.state === 'patched' || p.status === 'patched');
      const curValText = p.current_value || p.current_max_players || (isPatched ? 'Aktif' : 'Varsayılan');
      const statusBadge = isPatched
        ? `<span class="badge badge-green">Yamalı (${curValText})</span>`
        : `<span class="badge badge-amber">Varsayılan (${curValText})</span>`;

      const numMatch = String(curValText).match(/\d+/);
      const curLimitNum = numMatch ? parseInt(numMatch[0], 10) : 500;
      const targetFile = p.target_file || p.bundle || '-';
      const descText = p.title || p.description || p.key;

      const controls = isLimit ? `
        <div style="display:flex;gap:5px;align-items:center;flex-wrap:wrap;">
          <input type="number" min="1" max="100000" class="input input-sm input-mono" id="patch-max-players-input" value="${curLimitNum}" style="width:90px;" title="İstediğiniz herhangi bir tam sayıyı girin">
          <button class="btn btn-xs" onclick="document.getElementById('patch-max-players-input').value=250">250</button>
          <button class="btn btn-xs" onclick="document.getElementById('patch-max-players-input').value=1000">1000</button>
          <button class="btn btn-xs" onclick="document.getElementById('patch-max-players-input').value=5000">5000</button>
          <button class="btn btn-xs" onclick="document.getElementById('patch-max-players-input').value=25000">25000</button>
          <button class="btn btn-xs btn-primary" onclick="applyPatch('${p.key}', document.getElementById('patch-max-players-input').value)">Uygula</button>
          ${p.backup_exists ? `<button class="btn btn-xs btn-danger" onclick="restorePatch('${p.key}')">Yedek</button>` : ''}
        </div>
      ` : `
        <div style="display:flex;gap:6px;">
          <button class="btn btn-xs btn-primary" onclick="applyPatch('${p.key}', null)">Yamayı Uygula</button>
          ${p.backup_exists ? `<button class="btn btn-xs btn-danger" onclick="restorePatch('${p.key}')">Yedekten Dön</button>` : ''}
        </div>
      `;

      return `
        <tr>
          <td><code class="inline">${p.key}</code></td>
          <td style="font-family:var(--font-mono);font-size:11px;">${targetFile}</td>
          <td style="white-space:normal;max-width:340px;">${descText}</td>
          <td>${statusBadge}</td>
          <td>${controls}</td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    showToast('Yamalar yüklenemedi: ' + err.message, true);
  }
}

async function applyPatch(key, maxPlayers) {
  try {
    const body = { key };
    if (maxPlayers !== null && maxPlayers !== undefined && maxPlayers !== '') {
      body.max_players = parseInt(maxPlayers, 10);
    }
    await apiPost('/api/patches/apply', body);
    showToast(`"${key}" yaması başarıyla uygulandı.`);
    loadPatches(true);
  } catch (err) {
    showToast('Yama uygulanamadı: ' + err.message, true);
  }
}

async function applyAllSortingPatches() {
  try {
    await apiPost('/api/patches/apply-all-sorting', {});
    showToast('10 hazır UI tablo sıralama yamasının tamamı uygulandı.');
    loadPatches(true);
  } catch (err) {
    showToast('Toplu yama hatası: ' + err.message, true);
  }
}

async function restorePatch(key) {
  try {
    await apiPost('/api/patches/restore', { key });
    showToast(`"${key}" orijinal yedeğinden geri yüklendi.`);
    loadPatches(true);
  } catch (err) {
    showToast('Geri yükleme hatası: ' + err.message, true);
  }
}

async function loadStreamedTables(force = false) {
  try {
    const onlyUnsort = document.getElementById('st-only-unsortable').checked ? '1' : '0';
    const data = await apiGet(`/api/patches/streamed-tables?only_unsortable=${onlyUnsort}${force ? '&refresh=1' : ''}`);
    STATE.streamedTables = data.tables || [];
    renderStreamedTables();
  } catch (err) {
    showToast('StreamedTable listesi alınamadı: ' + err.message, true);
  }
}

function renderStreamedTables() {
  const q = (document.getElementById('st-filter-q').value || '').trim().toLowerCase();
  const rows = (STATE.streamedTables || []).filter(t =>
    !q
    || (t.table_name || '').toLowerCase().includes(q)
    || (t.vta_name || '').toLowerCase().includes(q)
    || (t.binding || '').toLowerCase().includes(q)
    || (t.bundle || '').toLowerCase().includes(q)
  );
  document.getElementById('streamed-tables-tbody').innerHTML = rows.slice(0, 260).map(t => {
    const locked = Number(t.disable_sorting) === 1;
    const tName = t.vta_name || t.table_name || '-';
    const bindText = t.binding || t.table_name || '-';
    const offText = t.offset_hex ? `${t.offset_hex} (${t.offset})` : t.offset;
    return `
      <tr>
        <td style="font-family:var(--font-mono);font-size:11px;">${t.bundle}</td>
        <td><b>${tName}</b></td>
        <td style="font-family:var(--font-mono);">${offText}</td>
        <td style="font-family:var(--font-mono);color:var(--text-muted);">${bindText}</td>
        <td>
          <span class="badge ${locked ? 'badge-amber' : 'badge-green'}">
            ${locked ? '1 — Sıralama Kilitli' : '0 — Sıralanabilir'}
          </span>
        </td>
        <td>
          <button class="btn btn-xs ${locked ? 'btn-primary' : 'btn-amber'}"
            onclick="toggleStreamedTable('${t.bundle}', ${t.offset}, ${locked ? 0 : 1})">
            ${locked ? 'Sıralamayı Aç (0 Yap)' : 'Kilitle (1 Yap)'}
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

async function toggleStreamedTable(bundle, offset, disable_sorting) {
  try {
    await apiPost('/api/patches/streamed-table-toggle', { bundle, offset, disable_sorting });
    showToast(`${bundle} @ ${offset} → m_disableSorting=${disable_sorting} uygulandı.`);
    loadStreamedTables(true);
  } catch (err) {
    showToast('StreamedTable değiştirilemedi: ' + err.message, true);
  }
}

/* ==================== TAB 8: RULES (.EDT / .LNC / .DBC) ==================== */
async function loadRules() {
  try {
    const d = await apiGet('/api/rules');
    STATE.activeRuleDbVersion = d.active_version || '2630';
    STATE.sugarDaddyEntries = (d.sugardaddy && d.sugardaddy.entries) || [];
    renderSugarDaddyTable();

    document.getElementById('rules-files-tbody').innerHTML = (d.files || []).map(f => `
      <tr>
        <td><span class="badge badge-blue">${f.category}</span></td>
        <td style="font-family:var(--font-mono);">${f.name}</td>
        <td>${f.size_kb} KB</td>
        <td><span class="badge ${f.enabled ? 'badge-green' : 'badge-red'}">${f.enabled ? 'Aktif' : 'Devre Dışı'}</span></td>
        <td style="display:flex;gap:5px;">
          ${f.editable_text ? `<button class="btn btn-xs btn-blue" onclick="openRuleTextFile('${f.rel_path.replace(/\\/g, '/')}')">Düzenle</button>` : ''}
          <button class="btn btn-xs ${f.enabled ? 'btn-danger' : 'btn-primary'}" onclick="toggleRuleFile('${f.rel_path.replace(/\\/g, '/')}', ${f.enabled})">
            ${f.enabled ? 'Devre Dışı Bırak' : 'Aktifleştir'}
          </button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    showToast('Kural dosyaları alınamadı: ' + err.message, true);
  }
}

function renderSugarDaddyTable() {
  document.getElementById('sd-tbody').innerHTML = STATE.sugarDaddyEntries.map((e, i) => `
    <tr>
      <td><input type="checkbox" ${e.enabled ? 'checked' : ''} onchange="STATE.sugarDaddyEntries[${i}].enabled=this.checked"></td>
      <td><input type="text" class="input input-sm" value="${e.club || ''}" oninput="STATE.sugarDaddyEntries[${i}].club=this.value" style="width:160px;"></td>
      <td>
        <select class="select input-sm" onchange="STATE.sugarDaddyEntries[${i}].type=this.value">
          <option value="FRONT_END" ${e.type==='FRONT_END'?'selected':''}>FRONT_END</option>
          <option value="BACK_END" ${e.type==='BACK_END'?'selected':''}>BACK_END</option>
          <option value="UNDERWRITER" ${e.type==='UNDERWRITER'?'selected':''}>UNDERWRITER</option>
        </select>
      </td>
      <td><input type="number" class="input input-sm input-mono" value="${e.start_flag ?? 1}" oninput="STATE.sugarDaddyEntries[${i}].start_flag=parseInt(this.value||1,10)" style="width:65px;"></td>
      <td><button class="btn btn-xs btn-danger" onclick="STATE.sugarDaddyEntries.splice(${i},1);renderSugarDaddyTable()">Sil</button></td>
    </tr>
  `).join('');
}

function addSugarDaddyRow() {
  STATE.sugarDaddyEntries.unshift({ club: 'Galatasaray', type: 'FRONT_END', start_flag: 1, enabled: true });
  renderSugarDaddyTable();
}

async function saveSugarDaddyEdt() {
  try {
    await apiPost('/api/rules/sugardaddy', {
      db_version: STATE.activeRuleDbVersion,
      entries: STATE.sugarDaddyEntries,
    });
    showToast('`sugardaddy.edt` kaydedildi (.bak yedekli).');
    loadRules();
  } catch (err) {
    showToast('sugardaddy.edt kaydedilemedi: ' + err.message, true);
  }
}

async function openRuleTextFile(rel_path) {
  try {
    const d = await apiGet(`/api/rules/text-file?rel_path=${encodeURIComponent(rel_path)}&db_version=${encodeURIComponent(STATE.activeRuleDbVersion || '')}`);
    STATE.activeRuleRelPath = d.rel_path;
    document.getElementById('rule-editor-path-label').textContent = `Açık Dosya: ${d.rel_path} (${d.path})`;
    document.getElementById('rule-editor-textarea').value = d.content || '';
  } catch (err) {
    showToast('Dosya açılamadı: ' + err.message, true);
  }
}

function insertDirectiveTemplate(kind) {
  const ta = document.getElementById('rule-editor-textarea');
  const templates = {
    BOOST_TEAM: `"BOOST_TEAM" "Galatasaray" 150000000 8500 50000`,
    TRANSFER_EMBARGO: `"TRANSFER_EMBARGO" "Club Name" "01.07.2025" "01.01.2026" "Appeal"`,
    START_IN_ADMIN: `"START_IN_ADMIN" "Club Name"`,
    CLUB_LONG_NAME_CHANGE: `"CLUB_LONG_NAME_CHANGE" 1909 "Galatasaray Spor Kulübü" ""`,
    COMP_LONG_NAME_CHANGE: `"COMP_LONG_NAME_CHANGE" 1301396 "Trendyol Süper Lig" ""`,
  };
  const line = templates[kind] || '';
  ta.value = (ta.value.trim() + '\n' + line + '\n').trim() + '\n';
}

async function saveRuleTextFile() {
  if (!STATE.activeRuleRelPath) return showToast('Önce soldaki listeden bir .edt veya .lnc dosyası seçin.', true);
  try {
    const content = document.getElementById('rule-editor-textarea').value;
    await apiPost('/api/rules/text-file', {
      db_version: STATE.activeRuleDbVersion,
      rel_path: STATE.activeRuleRelPath,
      content,
    });
    showToast(`${STATE.activeRuleRelPath} kaydedildi (.bak yedekli).`);
  } catch (err) {
    showToast('Kural dosyası kaydedilemedi: ' + err.message, true);
  }
}

async function toggleRuleFile(rel_path, currentlyEnabled) {
  try {
    await apiPost('/api/rules/toggle-file', {
      db_version: STATE.activeRuleDbVersion,
      rel_path,
      disable: currentlyEnabled,
    });
    showToast(`Dosya durumu değiştirildi: ${rel_path}`);
    loadRules();
  } catch (err) {
    showToast('Dosya durumu değiştirilemedi: ' + err.message, true);
  }
}

window.addEventListener('DOMContentLoaded', initStudio);
</script>
</body>
</html>
"""
