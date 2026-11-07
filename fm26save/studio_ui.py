"""Single-Page Web Application Frontend (`STUDIO_HTML_PAGE`) for FM27 / FM26 Studio."""

from __future__ import annotations

STUDIO_HTML_PAGE = r"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>FM27 / FM26 Studio — Veritabanı, Optimizasyon & Oyun Dosyası Komuta Merkezi</title>
<style>
  :root {
    --bg: #090d16;
    --bg-elev: #0f1624;
    --panel: #131c2e;
    --panel-alt: #19253d;
    --panel-hover: #21304f;
    --border: #263859;
    --border-bright: #3b5586;
    --gold: #f5b731;
    --gold-soft: rgba(245, 183, 49, 0.14);
    --cyan: #38bdf8;
    --cyan-soft: rgba(56, 189, 248, 0.14);
    --green: #22c55e;
    --green-soft: rgba(34, 197, 94, 0.15);
    --amber: #f59e0b;
    --danger: #ef4444;
    --purple: #a855f7;
    --text: #f1f5f9;
    --muted: #94a3b8;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: var(--bg);
    color: var(--text);
    font-size: 13px;
    line-height: 1.45;
  }
  /* Top Global Command Bar */
  .topbar {
    position: sticky;
    top: 0;
    z-index: 100;
    background: linear-gradient(90deg, #0d1526 0%, #141e33 50%, #191724 100%);
    border-bottom: 2px solid var(--gold);
    padding: 10px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    box-shadow: 0 6px 24px rgba(0,0,0,0.45);
  }
  .brand {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .brand-logo {
    width: 38px;
    height: 38px;
    border-radius: 9px;
    background: linear-gradient(135deg, var(--gold) 0%, #d97706 100%);
    color: #090d16;
    font-weight: 900;
    font-size: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 14px rgba(245, 183, 49, 0.35);
  }
  .brand h1 {
    margin: 0;
    font-size: 17px;
    font-weight: 800;
    color: var(--gold);
    letter-spacing: 0.3px;
  }
  .brand p {
    margin: 2px 0 0;
    font-size: 11.5px;
    color: var(--muted);
  }
  .global-controls {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }
  .ctrl-group {
    display: flex;
    align-items: center;
    gap: 6px;
    background: var(--bg-elev);
    border: 1px solid var(--border);
    padding: 5px 10px;
    border-radius: 8px;
  }
  .ctrl-group.highlight-lang {
    border-color: var(--cyan);
    background: rgba(56, 189, 248, 0.08);
  }
  .ctrl-group.highlight-ui {
    border-color: var(--gold);
    background: rgba(245, 183, 49, 0.08);
  }
  .ctrl-label {
    font-size: 11px;
    font-weight: 700;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.4px;
    white-space: nowrap;
  }
  select, input[type="text"], input[type="number"] {
    background: var(--panel);
    color: var(--text);
    border: 1px solid var(--border);
    padding: 5px 8px;
    border-radius: 6px;
    font-size: 12.5px;
    outline: none;
  }
  select:focus, input:focus, textarea:focus {
    border-color: var(--cyan);
  }
  button {
    background: var(--panel-alt);
    color: var(--text);
    border: 1px solid var(--border);
    padding: 6px 12px;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 600;
    font-size: 12.5px;
    transition: all 0.14s ease;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  button:hover {
    background: var(--panel-hover);
    border-color: var(--border-bright);
  }
  button.btn-gold {
    background: var(--gold);
    color: #090d16;
    border-color: var(--gold);
    font-weight: 700;
  }
  button.btn-gold:hover { filter: brightness(1.08); }
  button.btn-green {
    background: rgba(34, 197, 94, 0.18);
    color: #4ade80;
    border-color: #22c55e;
  }
  button.btn-green:hover { background: rgba(34, 197, 94, 0.28); }
  button.btn-cyan {
    background: rgba(56, 189, 248, 0.18);
    color: #38bdf8;
    border-color: #38bdf8;
  }
  button.btn-danger {
    background: rgba(239, 68, 68, 0.16);
    color: #f87171;
    border-color: #ef4444;
  }
  /* Main 3-Pillar Navigation */
  .pillar-nav {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    padding: 12px 20px;
    background: var(--bg-elev);
    border-bottom: 1px solid var(--border);
  }
  .pillar-btn {
    padding: 12px 16px;
    border-radius: 10px;
    background: var(--panel);
    border: 1px solid var(--border);
    text-align: left;
    display: flex;
    flex-direction: column;
    gap: 4px;
    cursor: pointer;
  }
  .pillar-btn.active {
    background: linear-gradient(135deg, rgba(245, 183, 49, 0.16) 0%, rgba(56, 189, 248, 0.10) 100%);
    border-color: var(--gold);
    box-shadow: 0 0 18px rgba(245, 183, 49, 0.16);
  }
  .pillar-title {
    font-size: 14px;
    font-weight: 800;
    color: var(--gold);
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .pillar-sub {
    font-size: 11.5px;
    color: var(--muted);
    font-weight: 500;
  }
  /* Sub-navigation bar */
  .subnav {
    display: flex;
    gap: 8px;
    padding: 10px 20px;
    background: var(--panel);
    border-bottom: 1px solid var(--border);
    flex-wrap: wrap;
  }
  .subnav button.active {
    background: var(--cyan-soft);
    border-color: var(--cyan);
    color: var(--cyan);
  }
  /* Workspace container */
  .workspace {
    padding: 16px 20px 48px;
    max-width: 1820px;
    margin: 0 auto;
  }
  .grid-2 {
    display: grid;
    grid-template-columns: 1.15fr 1fr;
    gap: 16px;
    align-items: start;
  }
  @media (max-width: 1200px) {
    .grid-2 { grid-template-columns: 1fr; }
    .pillar-nav { grid-template-columns: 1fr; }
  }
  .card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 14px;
  }
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
  }
  .card-title {
    margin: 0;
    font-size: 14.5px;
    font-weight: 700;
    color: var(--gold);
  }
  .filter-bar {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    align-items: center;
    margin-bottom: 10px;
  }
  /* Tables */
  .table-wrap {
    overflow-x: auto;
    max-height: 640px;
    overflow-y: auto;
    border: 1px solid var(--border);
    border-radius: 8px;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12.5px;
  }
  th, td {
    padding: 7px 10px;
    border-bottom: 1px solid rgba(38, 56, 89, 0.65);
    text-align: left;
    white-space: nowrap;
  }
  th {
    position: sticky;
    top: 0;
    background: #0e1626;
    color: var(--muted);
    font-weight: 700;
    font-size: 11.5px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    z-index: 2;
  }
  tr:hover td {
    background: rgba(56, 189, 248, 0.07);
  }
  tr.selected-row td {
    background: rgba(245, 183, 49, 0.15) !important;
  }
  /* Badges & Attribute Pills */
  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 5px;
    font-size: 11px;
    font-weight: 700;
    background: var(--panel-alt);
    border: 1px solid var(--border);
  }
  .badge-green { background: var(--green-soft); color: #4ade80; border-color: #22c55e; }
  .badge-gold { background: var(--gold-soft); color: var(--gold); border-color: var(--gold); }
  .badge-cyan { background: var(--cyan-soft); color: var(--cyan); border-color: var(--cyan); }
  .badge-danger { background: rgba(239,68,68,0.15); color: #f87171; border-color: #ef4444; }
  /* FM Attribute Grid (4 columns: Technical, Mental, Physical, Goalkeeping/Hidden) */
  .attr-columns {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(215px, 1fr));
    gap: 10px;
  }
  .attr-box {
    background: var(--bg-elev);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 10px;
  }
  .attr-box h4 {
    margin: 0 0 6px;
    font-size: 12px;
    color: var(--cyan);
    text-transform: uppercase;
    letter-spacing: 0.4px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 4px;
    display: flex;
    justify-content: space-between;
  }
  .attr-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 2.5px 4px;
    border-radius: 4px;
    font-size: 12px;
  }
  .attr-row:hover { background: rgba(255,255,255,0.04); }
  .attr-name {
    display: flex;
    align-items: center;
    gap: 6px;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .attr-abbr {
    font-size: 10px;
    color: var(--muted);
    font-family: monospace;
    background: rgba(255,255,255,0.05);
    padding: 1px 4px;
    border-radius: 3px;
  }
  .attr-input {
    width: 48px !important;
    text-align: center;
    font-weight: 800;
    padding: 2px 4px !important;
    border-radius: 5px;
    font-size: 12px !important;
  }
  .tier-elite { background: rgba(34, 197, 94, 0.25) !important; color: #4ade80 !important; border-color: #22c55e !important; }
  .tier-good  { background: rgba(56, 189, 248, 0.22) !important; color: #38bdf8 !important; border-color: #0284c7 !important; }
  .tier-avg   { background: rgba(245, 158, 11, 0.20) !important; color: #fbbf24 !important; border-color: #d97706 !important; }
  .tier-low   { background: rgba(148, 163, 184, 0.12) !important; color: #94a3b8 !important; border-color: #475569 !important; }
  /* Form Grid */
  .form-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(155px, 1fr));
    gap: 8px;
    margin-bottom: 10px;
  }
  .field-item {
    display: flex;
    flex-direction: column;
    gap: 3px;
  }
  .field-item label {
    font-size: 11px;
    color: var(--muted);
    font-weight: 600;
  }
  .pos-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 6px;
    margin-top: 6px;
  }
  /* Toast notification */
  #toast {
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 9999;
    padding: 12px 18px;
    border-radius: 8px;
    background: #111827;
    border: 2px solid var(--gold);
    color: var(--text);
    font-weight: 600;
    box-shadow: 0 10px 30px rgba(0,0,0,0.65);
    display: none;
    max-width: 520px;
  }
  .stat-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 10px;
    margin-bottom: 14px;
  }
  .stat-card {
    background: var(--bg-elev);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 12px;
  }
  .stat-card .k { font-size: 11px; color: var(--muted); text-transform: uppercase; }
  .stat-card .v { font-size: 18px; font-weight: 800; color: var(--gold); margin-top: 2px; }
  textarea.code-editor {
    width: 100%;
    min-height: 320px;
    background: #070a12;
    color: #e2e8f0;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px;
    font-family: 'Consolas', 'JetBrains Mono', monospace;
    font-size: 12px;
    line-height: 1.5;
  }
</style>
</head>
<body>

<header class="topbar">
  <div class="brand">
    <div class="brand-logo">FM</div>
    <div>
      <h1 id="ui-brand-title">FM27 / FM26 STUDIO — KOMUTA MERKEZİ</h1>
      <p id="ui-brand-sub">Save & Oyun İçi Veritabanı Görselleştirici/Editör • Oyun Optimizasyonu • İkili/Bundle Yamaları • 21 Dilde Oyun İçi Terim Lokalizasyonu</p>
    </div>
  </div>

  <div class="global-controls">
    <!-- Active Save Selector -->
    <div class="ctrl-group">
      <span class="ctrl-label" data-i18n="lbl_save">Save (.fm):</span>
      <select id="sel-save" onchange="onChangeSaveSelect()" style="max-width:210px;"></select>
      <button onclick="promptCustomSave()" title="Özel .fm dosya yolu gir">📂</button>
    </div>

    <!-- Active FM Installation Selector -->
    <div class="ctrl-group">
      <span class="ctrl-label" data-i18n="lbl_install">Oyun Dizini:</span>
      <select id="sel-install" onchange="onChangeInstallSelect()" style="max-width:190px;"></select>
    </div>

    <!-- Independent In-Game Term Language Selector (21 FM .ltc Languages!) -->
    <div class="ctrl-group highlight-lang" title="Arayüz dili ne olursa olsun oyun içi özellik/mevki/statü terimlerini seçilen FM dilinde gösterir!">
      <span class="ctrl-label" style="color:var(--cyan);" data-i18n="lbl_game_lang">🎯 Oyun İçi Terim Dili:</span>
      <select id="sel-game-lang" onchange="onChangeGameLang()"></select>
    </div>

    <!-- UI Interface Language Selector (TR / EN) -->
    <div class="ctrl-group highlight-ui">
      <span class="ctrl-label" style="color:var(--gold);" data-i18n="lbl_ui_lang">🌐 Arayüz (UI):</span>
      <select id="sel-ui-lang" onchange="onChangeUiLang()">
        <option value="tr">Türkçe (TR)</option>
        <option value="en">English (EN)</option>
      </select>
    </div>
  </div>
</header>

<!-- 3 Core Pillars Navigation -->
<div class="pillar-nav">
  <div class="pillar-btn active" id="pillar-btn-1" onclick="switchPillar(1)">
    <div class="pillar-title">
      <span data-i18n="p1_title">1. TÜM VERİTABANLARI & CANLI EDİTÖR</span>
      <span class="badge badge-gold" id="badge-save-summary">Save + Pre-Game DB</span>
    </div>
    <div class="pillar-sub" data-i18n="p1_sub">Save (.fm) Oyuncular, Kulüpler, Finans, Stadyumlar, Personel, DoF, 28 Tablo & Kurulum Pre-Game (2700/2620) DB</div>
  </div>

  <div class="pillar-btn" id="pillar-btn-2" onclick="switchPillar(2)">
    <div class="pillar-title">
      <span data-i18n="p2_title">2. OYUN OPTİMİZASYON MERKEZİ</span>
      <span class="badge badge-cyan">boot.config • URP • Video</span>
    </div>
    <div class="pillar-sub" data-i18n="p2_sub">Unity Çok Çekirdek & GC Ayarları, Hazır FPS Profilleri, Açılış Video Atlama ve Disk/DB Ayak İzi</div>
  </div>

  <div class="pillar-btn" id="pillar-btn-3" onclick="switchPillar(3)">
    <div class="pillar-title">
      <span data-i18n="p3_title">3. OYUN DOSYALARI, YAMALAR & KURALLAR</span>
      <span class="badge badge-green">50 Sınırı • 252 Tablo • .edt/.dbc</span>
    </div>
    <div class="pillar-sub" data-i18n="p3_sub">50 Gözlemci Sınırı, Sıralanamayan Tabloları Sıralanabilir Yapma, Sugar Daddy (.edt) & Gerçek Lisans (.dbc/.lnc)</div>
  </div>
</div>

<!-- Sub-navigation for Pillar 1 -->
<div class="subnav" id="subnav-1">
  <button class="active" data-sub="p1-players" onclick="switchSubTab(1, 'p1-players')" data-i18n="sub_players">⚽ Oyuncu Merkezi & Canlı Editör</button>
  <button data-sub="p1-clubs" onclick="switchSubTab(1, 'p1-clubs')" data-i18n="sub_clubs">🏛️ Kulüpler, Finans, Stadyum & Lig Puanı</button>
  <button data-sub="p1-staff" onclick="switchSubTab(1, 'p1-staff')" data-i18n="sub_staff">👔 Teknik Heyet (26 Gizli Özellik) & DoF</button>
  <button data-sub="p1-tables" onclick="switchSubTab(1, 'p1-tables')" data-i18n="sub_tables">📊 Tüm 28 Save Tablosu & 81 Ham Bölüm</button>
  <button data-sub="p1-pregame" onclick="switchSubTab(1, 'p1-pregame')" data-i18n="sub_pregame">🗄️ Oyun İçi Kurulum DB'leri (2700 / Wonderkids / lang_db)</button>
</div>

<!-- Sub-navigation for Pillar 2 -->
<div class="subnav" id="subnav-2" style="display:none;">
  <button class="active" data-sub="p2-main" onclick="switchSubTab(2, 'p2-main')" data-i18n="sub_opt_main">🚀 Unity boot.config, FPS Profilleri, Video Bypass & URP Analizi</button>
</div>

<!-- Sub-navigation for Pillar 3 -->
<div class="subnav" id="subnav-3" style="display:none;">
  <button class="active" data-sub="p3-patches" onclick="switchSubTab(3, 'p3-patches')" data-i18n="sub_patches">🔧 Hazır İkili & UI Bundle Yamaları (50 Oyuncu Sınırı + 10 Tablo Sıralama)</button>
  <button data-sub="p3-alltables" onclick="switchSubTab(3, 'p3-alltables')" data-i18n="sub_alltables">🔓 Tüm 252 Sıralanamayan Tablo (StreamedTable) Tarayıcısı & Kilit Açıcı</button>
  <button data-sub="p3-rules" onclick="switchSubTab(3, 'p3-rules')" data-i18n="sub_rules">👑 Sugar Daddy (.edt), Gerçek İsim/Milli Takım Lisansları (.dbc/.lnc) & Kural Editörü</button>
</div>

<main class="workspace">

  <!-- ===================================================================== -->
  <!-- PILLAR 1.1: PLAYERS EXPLORER & LIVE LOCALIZED EDITOR                  -->
  <!-- ===================================================================== -->
  <section id="view-p1-players" class="subview">
    <div class="stat-cards" id="save-kpi-bar"></div>
    <div class="grid-2">
      <!-- Left: Searchable Players Table -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title" data-i18n="hdr_player_list">Save İçi Oyuncu Veritabanı</h3>
          <span class="badge badge-cyan" id="players-count-badge">0</span>
        </div>
        <div class="filter-bar">
          <input type="text" id="flt-player-q" placeholder="İsim, UID veya Uyruk ara..." oninput="debouncedLoadPlayers()" style="flex:1; min-width:150px;"/>
          <input type="text" id="flt-player-club" placeholder="Kulüp filtresi (örn. Galatasaray)" oninput="debouncedLoadPlayers()" style="width:155px;"/>
          <select id="flt-player-pos" onchange="loadPlayers()">
            <option value="">Tüm Mevkiler</option>
            <option value="GK">GK</option><option value="DL">DL</option><option value="DC">DC</option><option value="DR">DR</option>
            <option value="WBL">WBL</option><option value="WBR">WBR</option><option value="DM">DM</option>
            <option value="ML">ML</option><option value="MC">MC</option><option value="MR">MR</option>
            <option value="AML">AML</option><option value="AMC">AMC</option><option value="AMR">AMR</option><option value="ST">ST</option>
          </select>
          <input type="number" id="flt-player-minca" placeholder="Min CA" value="0" min="0" max="200" onchange="loadPlayers()" style="width:74px;"/>
          <select id="flt-player-sort" onchange="loadPlayers()">
            <option value="ca">Sırala: CA</option>
            <option value="pa">Sırala: PA</option>
            <option value="value">Sırala: Değer</option>
            <option value="wage">Sırala: Maaş</option>
            <option value="age">Sırala: Yaş (Genç)</option>
          </select>
          <button class="btn-cyan" onclick="loadPlayers()">🔍</button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>UID</th>
                <th id="th-pl-name">İsim</th>
                <th id="th-pl-pos">Mevki</th>
                <th id="th-pl-age">Yaş</th>
                <th>CA</th>
                <th>PA</th>
                <th>Kulüp</th>
                <th id="th-pl-val">Değer (€)</th>
                <th id="th-pl-wage">Maaş (€/h)</th>
              </tr>
            </thead>
            <tbody id="tbody-players"></tbody>
          </table>
        </div>
      </div>

      <!-- Right: Player Detail & Live Localized Attribute Editor -->
      <div class="card" id="player-editor-card">
        <div class="card-header">
          <div>
            <h3 class="card-title" id="pe-title">Oyuncu Seçin</h3>
            <div id="pe-subtitle" style="font-size:11.5px; color:var(--muted);">Tablodan bir oyuncuya tıklayarak seçilen oyun içi dilde tüm özelliklerini görüntüleyin ve düzenleyin.</div>
          </div>
          <div style="display:flex; gap:6px; flex-wrap:wrap;">
            <button class="btn-gold" onclick="saveCurrentPlayerEdits(true)" title="CA/PA 200 ve tüm özellikleri 20 yap!">⚡ Max 200 / 20</button>
            <button class="btn-green" onclick="healCurrentPlayer()" title="Tüm sakatlıkları iyileştir ve cezaları temizle">🏥 İyileştir & Ceza Sil</button>
            <button class="btn-cyan" onclick="saveCurrentPlayerEdits(false)">💾 Değişiklikleri Save'e Yaz</button>
          </div>
        </div>

        <div id="pe-body" style="display:none;">
          <!-- Profile & Contract Fields -->
          <div class="form-grid">
            <div class="field-item"><label id="lbl-pe-ca">Current Ability (CA)</label><input type="number" id="pe-ca" min="1" max="200"/></div>
            <div class="field-item"><label id="lbl-pe-pa">Potential Ability (PA)</label><input type="number" id="pe-pa" min="1" max="200"/></div>
            <div class="field-item"><label id="lbl-pe-val">Value (€)</label><input type="number" id="pe-value" min="0"/></div>
            <div class="field-item"><label id="lbl-pe-wage">Wage (€/w)</label><input type="number" id="pe-wage" min="0"/></div>
            <div class="field-item"><label id="lbl-pe-ctend">Contract Expires</label><input type="text" id="pe-contract-end" placeholder="YYYY-MM-DD"/></div>
            <div class="field-item"><label id="lbl-pe-age">Age</label><input type="number" id="pe-age" min="14" max="55"/></div>
            <div class="field-item"><label id="lbl-pe-height">Height (cm)</label><input type="number" id="pe-height" min="140" max="220"/></div>
            <div class="field-item"><label id="lbl-pe-cond">Condition</label><input type="number" id="pe-condition" min="1" max="10000"/></div>
            <div class="field-item"><label id="lbl-pe-rep">World Reputation</label><input type="number" id="pe-world-rep" min="1" max="10000"/></div>
          </div>

          <!-- Localized 14-Position Familiarity Bar -->
          <div style="margin-bottom:10px;">
            <div style="font-size:11px; color:var(--muted); font-weight:700; margin-bottom:4px;" id="lbl-pe-positions">MEVKİ HAKİMİYETİ (1..20) — Seçilen Oyun İçi Dilde</div>
            <div class="pos-grid" id="pe-positions-grid"></div>
          </div>

          <!-- Localized 4-Column Attribute Sheet (Technical, Mental, Physical, Goalkeeping + Hidden) -->
          <div style="display:flex; justify-content:space-between; align-items:center; margin:8px 0 6px;">
            <span style="font-size:11.5px; font-weight:700; color:var(--gold);" id="lbl-attr-sheet-hdr">OYUN İCİ ÖZELLİK TABLOSU (1..20)</span>
            <span class="badge badge-cyan" id="badge-active-gamelang">Türkçe</span>
          </div>
          <div class="attr-columns" id="pe-attr-columns"></div>

          <!-- Tactical Role Suitability (IP & OOP) -->
          <div style="margin-top:12px; border-top:1px solid var(--border); padding-top:10px;">
            <div style="font-size:12px; font-weight:700; color:var(--gold); margin-bottom:6px;">🎯 En Uygun Taktiksel Roller (Topa Sahipken IP & Top Rakipteyken OOP)</div>
            <div id="pe-roles-box" style="display:flex; gap:8px; flex-wrap:wrap;"></div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- ===================================================================== -->
  <!-- PILLAR 1.2: CLUBS, FINANCES, STADIUMS, LEAGUE TABLES & GAME DATE      -->
  <!-- ===================================================================== -->
  <section id="view-p1-clubs" class="subview" style="display:none;">
    <div class="grid-2">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">🏛️ Kulüpler, Bütçeler & Tesisler</h3>
          <div style="display:flex; gap:6px;">
            <input type="text" id="flt-club-q" placeholder="Kulüp ara..." oninput="loadClubs()"/>
            <select id="flt-club-sort" onchange="loadClubs()">
              <option value="reputation">İtibar</option>
              <option value="balance">Bakiye (€)</option>
              <option value="transfer_budget">Transfer Bütçesi (€)</option>
              <option value="wage_budget">Maaş Bütçesi (€/h)</option>
            </select>
          </div>
        </div>
        <div class="table-wrap" style="max-height:420px;">
          <table>
            <thead>
              <tr><th>UID</th><th>Kulüp</th><th>İtibar</th><th>Bakiye (€)</th><th>Transfer Bütçesi (€)</th><th>Maaş Bütçesi (€/h)</th><th>Kurumsal Tesis</th></tr>
            </thead>
            <tbody id="tbody-clubs"></tbody>
          </table>
        </div>
      </div>

      <div>
        <!-- Selected Club Live Editor -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title" id="ce-title">Kulüp Finans & İtibar Düzenleyici</h3>
            <button class="btn-gold" onclick="saveClubEdits()">💾 Kulüp Değişikliklerini Kaydet</button>
          </div>
          <input type="hidden" id="ce-uid"/>
          <div class="form-grid">
            <div class="field-item"><label>Kulüp İtibarı (1..10000)</label><input type="number" id="ce-rep" min="1" max="10000"/></div>
            <div class="field-item"><label>Banka Bakiyesi (€)</label><input type="number" id="ce-balance"/></div>
            <div class="field-item"><label>Transfer Bütçesi (€)</label><input type="number" id="ce-tbudget"/></div>
            <div class="field-item"><label>Haftalık Maaş Bütçesi (€)</label><input type="number" id="ce-wbudget"/></div>
            <div class="field-item"><label>Kurumsal Tesisler (1..20)</label><input type="number" id="ce-corpfac" min="1" max="20"/></div>
          </div>
          <div style="display:flex; gap:8px; flex-wrap:wrap;">
            <button class="btn-green" onclick="presetRichClub()">💰 +250M € Transfer Bütçesi & 500M € Bakiye Ver</button>
          </div>
        </div>

        <!-- Stadiums & Game Date Editor -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">🏟️ Stadyum Kapasitesi & Oyun Tarihi Editörü</h3>
            <input type="text" id="flt-stadium-q" placeholder="Stadyum ara..." oninput="loadStadiums()"/>
          </div>
          <div class="form-grid">
            <div class="field-item"><label>Seçili Stadyum UID</label><input type="number" id="ste-uid" readonly/></div>
            <div class="field-item"><label>Toplam Kapasite</label><input type="number" id="ste-cap" min="100" max="250000"/></div>
            <div class="field-item"><label>Koltuklu Kapasite</label><input type="number" id="ste-seat" min="100" max="250000"/></div>
            <div class="field-item"><label>Oyun Tarihi (YYYY-MM-DD)</label><input type="text" id="ste-gamedate" placeholder="2025-09-20"/></div>
          </div>
          <button class="btn-cyan" onclick="saveStadiumAndDateEdits()" style="margin-bottom:10px;">💾 Stadyum / Tarih Kaydet</button>
          <div class="table-wrap" style="max-height:210px;">
            <table>
              <thead><tr><th>UID</th><th>Stadyum</th><th>Kapasite</th><th>Koltuklu</th></tr></thead>
              <tbody id="tbody-stadiums"></tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- ===================================================================== -->
  <!-- PILLAR 1.3: STAFF (26 HIDDEN ATTRIBUTES) & DIRECTOR OF FOOTBALL (DoF) -->
  <!-- ===================================================================== -->
  <section id="view-p1-staff" class="subview" style="display:none;">
    <div class="grid-2">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">👔 Teknik Heyet, Menajerler & Gözlemciler</h3>
          <div style="display:flex; gap:6px;">
            <input type="text" id="flt-staff-q" placeholder="İsim, Kulüp veya UID ara..." oninput="loadStaff()"/>
            <input type="text" id="flt-staff-role" placeholder="Rol (Manager, Coach, Scout)" oninput="loadStaff()" style="width:150px;"/>
          </div>
        </div>
        <div class="table-wrap" style="max-height:540px;">
          <table>
            <thead>
              <tr><th>UID</th><th>İsim</th><th>Rol</th><th>Kulüp</th><th>CA</th><th>PA</th></tr>
            </thead>
            <tbody id="tbody-staff"></tbody>
          </table>
        </div>
      </div>

      <div>
        <div class="card">
          <div class="card-header">
            <h3 class="card-title" id="stf-title">Personel Detayı & 26 Gizli Özellik (Seçilen Oyun İçi Dilde)</h3>
            <div style="display:flex; gap:6px;">
              <button class="btn-gold" onclick="saveStaffEdits(true)">⚡ Max 200 Personel</button>
              <button class="btn-cyan" onclick="saveStaffEdits(false)">💾 CA/PA Kaydet</button>
              <button class="btn-green" onclick="hireSelectedStaffAsCoach()">🤝 Kulübe Teknik Direktör Ata (DoF)</button>
            </div>
          </div>
          <input type="hidden" id="stf-uid"/>
          <div class="form-grid">
            <div class="field-item"><label id="lbl-stf-ca">Current Ability (CA)</label><input type="number" id="stf-ca" min="1" max="200"/></div>
            <div class="field-item"><label id="lbl-stf-pa">Potential Ability (PA)</label><input type="number" id="stf-pa" min="1" max="200"/></div>
          </div>
          <div id="stf-attrs-box" class="attr-columns"></div>
        </div>
      </div>
    </div>
  </section>

  <!-- ===================================================================== -->
  <!-- PILLAR 1.4: ALL 28 SAVE TABLES & 81 CONTAINER SECTIONS                -->
  <!-- ===================================================================== -->
  <section id="view-p1-tables" class="subview" style="display:none;">
    <div class="grid-2">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">📊 Tüm 28 Yapılandırılmış Save Tablosu & Ekstra Bölümler</h3>
          <div style="display:flex; gap:6px; flex-wrap:wrap;">
            <select id="sel-any-table" onchange="loadAnySaveTable()">
              <option value="players">players</option>
              <option value="contracts">contracts</option>
              <option value="clubs">clubs</option>
              <option value="managed-clubs">managed-clubs</option>
              <option value="finances">finances</option>
              <option value="sponsorships">sponsorships</option>
              <option value="facilities">facilities</option>
              <option value="stadiums">stadiums</option>
              <option value="affiliates">affiliates</option>
              <option value="staff">staff</option>
              <option value="staff-lists">staff-lists</option>
              <option value="injuries">injuries</option>
              <option value="injury-types">injury-types</option>
              <option value="suspensions">suspensions</option>
              <option value="tactics">tactics</option>
              <option value="set-pieces">set-pieces</option>
              <option value="training">training</option>
              <option value="mentoring">mentoring</option>
              <option value="job-vacancies">job-vacancies</option>
              <option value="competitions">competitions</option>
              <option value="stages">stages</option>
              <option value="league-tables">league-tables</option>
              <option value="fixtures">fixtures</option>
              <option value="competition-rules">competition-rules</option>
              <option value="transfer-windows">transfer-windows</option>
              <option value="player-season-stats">player-season-stats</option>
              <option value="player-match-stats">player-match-stats</option>
              <option value="hall_of_fame">[Extra] hall_of_fame</option>
              <option value="takeovers">[Extra] board_takeovers</option>
              <option value="shortlists">[Extra] shortlists</option>
              <option value="offers">[Extra] contract_offers</option>
              <option value="agents">[Extra] agents</option>
              <option value="news">[Extra] news_items</option>
            </select>
            <input type="text" id="flt-any-table" placeholder="Tablo içi metin filtrele..." oninput="loadAnySaveTable()"/>
          </div>
        </div>
        <div class="table-wrap" style="max-height:540px;">
          <table id="tbl-any-save">
            <thead id="thead-any-save"></thead>
            <tbody id="tbody-any-save"></tbody>
          </table>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">📦 Save Konteyneri Ham Bölümleri (81 Zstd Bölümü)</h3>
        </div>
        <div class="table-wrap" style="max-height:540px;">
          <table>
            <thead><tr><th>Bölüm Adı (.dat / .cmt)</th><th>Sıkıştırılmış (B)</th><th>Açılmış (B)</th><th>Oran</th></tr></thead>
            <tbody id="tbody-save-sections"></tbody>
          </table>
        </div>
      </div>
    </div>
  </section>

  <!-- ===================================================================== -->
  <!-- PILLAR 1.5: PRE-GAME INSTALLATION DATABASES (2700 / 2620)             -->
  <!-- ===================================================================== -->
  <section id="view-p1-pregame" class="subview" style="display:none;">
    <div class="stat-cards" id="pregame-kpi-bar"></div>
    <div class="grid-2">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">🌟 Pre-Game Kişi Veritabanı (`basic_people_db.dat` / `people_db.dat` — 723.010+ Kayıt & Wonderkids)</h3>
        </div>
        <div id="pregame-people-box">Yükleniyor...</div>
      </div>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">🌍 Master DB Tabloları (`client_db.dat` / `server_db.dat`) & Çoklu Sürüm Evrimi (`2300..2700`)</h3>
        </div>
        <div id="pregame-master-box">Yükleniyor...</div>
      </div>
    </div>
  </section>

  <!-- ===================================================================== -->
  <!-- PILLAR 2: GAME OPTIMIZATION SUITE                                     -->
  <!-- ===================================================================== -->
  <section id="view-p2-main" class="subview" style="display:none;">
    <div class="grid-2">
      <div class="card">
        <div class="card-header">
          <div>
            <h3 class="card-title">🚀 Unity Motoru `fm_Data/boot.config` Performans & Çok Çekirdek Ayarlayıcı</h3>
            <div style="font-size:11.5px; color:var(--muted);">Maç simülasyonu, UI tablo akışı ve render iş parçacıklarını donanımınıza göre optimize edin (.bak yedekli).</div>
          </div>
          <div style="display:flex; gap:6px; flex-wrap:wrap;">
            <button class="btn-gold" onclick="applyBootPreset('max_fps_multicore')">⚡ Maksimum FPS & Çok Çekirdek</button>
            <button class="btn-cyan" onclick="applyBootPreset('balanced')">⚖️ Dengeli</button>
            <button class="btn-green" onclick="applyBootPreset('low_latency')">🎯 Düşük Mikro-Takılma</button>
            <button onclick="restoreBootConfig()">↩️ Yedekten Dön</button>
          </div>
        </div>
        <div id="boot-config-form"></div>
        <div style="margin-top:10px; display:flex; justify-content:space-between; align-items:center;">
          <span id="boot-cpu-hint" class="badge badge-cyan"></span>
          <button class="btn-gold" onclick="saveBootConfig()">💾 boot.config Kaydet</button>
        </div>
      </div>

      <div>
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">🎬 Açılış & Tanıtım Video Bundle'ları (`videos_*.bundle` / `promobanner_*.bundle`)</h3>
            <div style="display:flex; gap:6px;">
              <button class="btn-gold" onclick="toggleAllVideos(true)">⏩ Tümünü Devre Dışı Bırak (Hızlı Başlangıç)</button>
              <button class="btn-green" onclick="toggleAllVideos(false)">▶️ Tümünü Etkinleştir</button>
            </div>
          </div>
          <div class="table-wrap" style="max-height:220px;">
            <table>
              <thead><tr><th>Bundle Adı</th><th>Boyut (MB)</th><th>Durum</th></tr></thead>
              <tbody id="tbody-opt-videos"></tbody>
            </table>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h3 class="card-title">🎨 URP Grafik Pipeline Profilleri & Kurulum Veritabanı (`2300..2700`) Ayak İzi</h3>
          </div>
          <div class="table-wrap" style="max-height:200px; margin-bottom:10px;">
            <table>
              <thead><tr><th>URP Profili</th><th>SRP Batcher</th><th>MSAA</th><th>Upscaling</th><th>Gölge Mesafesi</th><th>Ek Işık Sınırı</th></tr></thead>
              <tbody id="tbody-urp-profiles"></tbody>
            </table>
          </div>
          <div class="table-wrap" style="max-height:200px;">
            <table>
              <thead><tr><th>Kurulum DB Sürümü</th><th>Dosya Sayısı</th><th>Toplam Boyut (MB)</th><th>Durum</th></tr></thead>
              <tbody id="tbody-db-footprint"></tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- ===================================================================== -->
  <!-- PILLAR 3.1: BINARY & UI BUNDLE PATCHER (50-PLAYER LIMIT & 10 TABLES)  -->
  <!-- ===================================================================== -->
  <section id="view-p3-patches" class="subview" style="display:none;">
    <div class="card">
      <div class="card-header">
        <div>
          <h3 class="card-title">🎯 Oyuncu Merkezi / Gözlemcilik Çoklu Seçim 50 Oyuncu Sınırı Yaması (`game_plugin.dll`)</h3>
          <div style="font-size:12px; color:var(--muted);">
            <code>EvaluateScoutPlayersAction</code> (<code>VA 0x180FDEBD4: cmp rcx, (N+1)*8</code>) içindeki 50 oyuncu sınırını (51+ seçildiğinde <code>'tmpa'</code> ile gözlemlemeyi kapatan kontrolü) istediğiniz sayıya yükseltir.
          </div>
        </div>
        <span id="scout-limit-badge" class="badge badge-gold">Yükleniyor...</span>
      </div>
      <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
        <label style="font-weight:700;">Yeni Maksimum Oyuncu Sınırı:</label>
        <input type="number" id="inp-max-scout-players" value="5000" min="50" max="100000" style="width:110px; font-weight:800;"/>
        <button onclick="document.getElementById('inp-max-scout-players').value=500">500</button>
        <button onclick="document.getElementById('inp-max-scout-players').value=2500">2.500</button>
        <button onclick="document.getElementById('inp-max-scout-players').value=5000">5.000</button>
        <button onclick="document.getElementById('inp-max-scout-players').value=15000">15.000</button>
        <button class="btn-gold" onclick="applyNamedPatch('scout-player-limit')">🚀 Sınırı Uygula (game_plugin.dll)</button>
        <button class="btn-danger" onclick="restoreNamedPatch('scout-player-limit')">↩️ Orijinal 50 Sınırına Dön</button>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <div>
          <h3 class="card-title">📊 Hazır UI Tablo Sıralama Yamaları (`StreamedTable.DisableSorting = 1 → 0`)</h3>
          <div style="font-size:12px; color:var(--muted);">Oyun içinde sütun başlığına tıklanarak sıralanamayan en kritik 10 tabloyu tek tıkla sıralanabilir (`sortable`) hale getirin.</div>
        </div>
        <button class="btn-gold" onclick="applyAllSortingPatches()">🔓 Tüm 10 Tablo Sıralama Yamasını Tek Tıkla Aç</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>Yama Anahtarı (Key)</th><th>Açıklama</th><th>Hedef Bundle / Dosya</th><th>Durum</th><th>Yedek (.bak)</th><th>İşlem</th></tr>
          </thead>
          <tbody id="tbody-named-patches"></tbody>
        </table>
      </div>
    </div>
  </section>

  <!-- ===================================================================== -->
  <!-- PILLAR 3.2: ALL 252 UNSORTABLE STREAMEDTABLES SCANNER & UNLOCKER      -->
  <!-- ===================================================================== -->
  <section id="view-p3-alltables" class="subview" style="display:none;">
    <div class="card">
      <div class="card-header">
        <div>
          <h3 class="card-title">🔓 Oyun İçindeki Tüm 252 `DisableSorting = 1` (`StreamedTable`) Tablo Tarayıcısı & Kilit Açıcı</h3>
          <div style="font-size:12px; color:var(--muted);">FM27 UI `VisualTreeAsset` bundle'larında `DisableSorting = 1` olarak gelen 252 tablonun tamamını inceleyin ve istediğiniz herhangi bir tablonun sıralama kilidini açın.</div>
        </div>
        <div style="display:flex; gap:8px;">
          <input type="text" id="flt-streamed-q" placeholder="VTA veya tablo adı ara (örn. Recruitment, SetPiece, Squad)..." oninput="renderStreamedTables()" style="width:320px;"/>
          <button class="btn-cyan" onclick="loadStreamedTables(true)">🔄 Yeniden Tara</button>
        </div>
      </div>
      <div class="table-wrap" style="max-height:600px;">
        <table>
          <thead>
            <tr><th>Bundle</th><th>VisualTreeAsset (Ekran / Blok)</th><th>Tablo Adı</th><th>Ofset</th><th>Durum</th><th>İşlem</th></tr>
          </thead>
          <tbody id="tbody-streamed-tables"></tbody>
        </table>
      </div>
    </div>
  </section>

  <!-- ===================================================================== -->
  <!-- PILLAR 3.3: SUGAR DADDY (.edt), REAL LICENSING (.dbc/.lnc) & EDITOR   -->
  <!-- ===================================================================== -->
  <section id="view-p3-rules" class="subview" style="display:none;">
    <div class="grid-2">
      <!-- Left: Visual Sugar Daddy Editor + Licensing File Toggles -->
      <div>
        <div class="card">
          <div class="card-header">
            <div>
              <h3 class="card-title">👑 Görsel Zengin Başkan (`sugardaddy.edt`) Düzenleyici</h3>
              <div style="font-size:11.5px; color:var(--muted);">İstediğiniz kulübe zengin başkan (`FRONT_END` = sınırsız bütçe, `BACK_END` = ligine göre destek, `UNDERWRITER` = sezon sonu borç kapatma) ekleyin!</div>
            </div>
            <button class="btn-gold" onclick="saveSugarDaddyEdt()">💾 sugardaddy.edt Kaydet</button>
          </div>
          <div class="filter-bar">
            <input type="text" id="inp-sd-club" placeholder="Yeni Kulüp Adı (örn. Galatasaray, Fenerbahçe)" style="flex:1;"/>
            <select id="sel-sd-type">
              <option value="FRONT_END">FRONT_END (Tam Bütçe Desteği)</option>
              <option value="BACK_END">BACK_END (Lig Seviyesi Desteği)</option>
              <option value="UNDERWRITER">UNDERWRITER (Zarar/Borç Kapatıcı)</option>
            </select>
            <label style="display:flex; align-items:center; gap:4px; font-size:12px;">
              <input type="checkbox" id="chk-sd-alter" checked/> Başlangıç Bütçesini Artır (1)
            </label>
            <button class="btn-green" onclick="addSugarDaddyClub()">➕ Kulüp Ekle</button>
          </div>
          <div class="table-wrap" style="max-height:280px;">
            <table>
              <thead><tr><th>Aktif</th><th>Kulüp Adı</th><th>Sugar Daddy Tipi</th><th>Başlangıç Bütçesi (1/0)</th><th>Sil</th></tr></thead>
              <tbody id="tbody-sugardaddy"></tbody>
            </table>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div>
              <h3 class="card-title">🌍 Gerçek İsimler, Milli Takım & Forma Lisans Yöneticisi (`.dbc` / `.lnc` / `.edt`)</h3>
              <div style="font-size:11.5px; color:var(--muted);">Almanya/Japonya milli takımı kısıtlamalarını (`germany.dbc`, `japan_fake.dbc`, `fake.lnc`) veya forma/isim kısıtlamalarını tek tıkla devre dışı bırakın veya metin kurallarını düzenleyin.</div>
            </div>
          </div>
          <div class="table-wrap" style="max-height:340px;">
            <table>
              <thead><tr><th>Dosya</th><th>Kategori</th><th>Açıklama</th><th>Durum</th><th>İşlem</th></tr></thead>
              <tbody id="tbody-rules-files"></tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Right: Live .edt / .ddt / .lnc Text Rule Editor -->
      <div class="card">
        <div class="card-header">
          <div>
            <h3 class="card-title" id="rule-ed-title">📝 Canlı Kural Dosyası Editörü (`.edt` / `.ddt` / `.lnc`)</h3>
            <div id="rule-ed-sub" style="font-size:11.5px; color:var(--muted);">Sol tablodan herhangi bir `.edt`, `.ddt` veya `.lnc` dosyasında "Düzenle" butonuna tıklayın (UTF-16LE / UTF-8 BOM otomatik korunur).</div>
          </div>
          <button class="btn-gold" onclick="saveRuleTextFile()">💾 Dosyayı Kaydet (.bak Yedekli)</button>
        </div>
        <input type="hidden" id="rule-ed-relpath"/>
        <textarea class="code-editor" id="rule-ed-content" placeholder="Düzenlemek için soldaki listeden bir .edt veya .lnc dosyası seçin..."></textarea>
      </div>
    </div>
  </section>

</main>

<div id="toast"></div>

<script>
let STATE = {
  uiLang: 'tr',
  gameLang: 'turkish',
  gameTerms: {},
  attrGroups: {},
  staffGroups: {},
  activePlayerUid: null,
  activePlayerDetail: null,
  streamedTables: [],
  sugarDaddyEntries: [],
  pregameLoaded: false,
  streamedLoaded: false,
};

const UI_I18N = {
  tr: {
    lbl_save: "Save (.fm):",
    lbl_install: "Oyun Dizini:",
    lbl_game_lang: "🎯 Oyun İçi Terim Dili:",
    lbl_ui_lang: "🌐 Arayüz (UI):",
    p1_title: "1. TÜM VERİTABANLARI & CANLI EDİTÖR",
    p1_sub: "Save (.fm) Oyuncular, Kulüpler, Finans, Stadyumlar, Personel, DoF, 28 Tablo & Kurulum Pre-Game (2700/2620) DB",
    p2_title: "2. OYUN OPTİMİZASYON MERKEZİ",
    p2_sub: "Unity Çok Çekirdek & GC Ayarları, Hazır FPS Profilleri, Açılış Video Atlama ve Disk/DB Ayak İzi",
    p3_title: "3. OYUN DOSYALARI, YAMALAR & KURALLAR",
    p3_sub: "50 Gözlemci Sınırı, Sıralanamayan Tabloları Sıralanabilir Yapma, Sugar Daddy (.edt) & Gerçek Lisans (.dbc/.lnc)",
    sub_players: "⚽ Oyuncu Merkezi & Canlı Editör",
    sub_clubs: "🏛️ Kulüpler, Finans, Stadyum & Lig Puanı",
    sub_staff: "👔 Teknik Heyet (26 Gizli Özellik) & DoF",
    sub_tables: "📊 Tüm 28 Save Tablosu & 81 Ham Bölüm",
    sub_pregame: "🗄️ Oyun İçi Kurulum DB'leri (2700 / Wonderkids / lang_db)",
    sub_opt_main: "🚀 Unity boot.config, FPS Profilleri, Video Bypass & URP Analizi",
    sub_patches: "🔧 Hazır İkili & UI Bundle Yamaları (50 Oyuncu Sınırı + 10 Tablo Sıralama)",
    sub_alltables: "🔓 Tüm 252 Sıralanamayan Tablo (StreamedTable) Tarayıcısı & Kilit Açıcı",
    sub_rules: "👑 Sugar Daddy (.edt), Gerçek İsim/Milli Takım Lisansları (.dbc/.lnc) & Kural Editörü",
    hdr_player_list: "Save İçi Oyuncu Veritabanı",
  },
  en: {
    lbl_save: "Save (.fm):",
    lbl_install: "Game Dir:",
    lbl_game_lang: "🎯 In-Game Term Language:",
    lbl_ui_lang: "🌐 UI Language:",
    p1_title: "1. ALL DATABASES & LIVE EDITOR",
    p1_sub: "Save (.fm) Players, Clubs, Finances, Stadiums, Staff, DoF, 28 Tables & Pre-Game Installation (2700/2620) DBs",
    p2_title: "2. GAME OPTIMIZATION SUITE",
    p2_sub: "Unity Multi-Core & GC Tuning, Curated FPS Presets, Startup Video Bypass & Disk/DB Footprint",
    p3_title: "3. GAME FILES, BINARY PATCHES & RULES",
    p3_sub: "50 Scout Player Limit, Unlock Unsortable Tables, Sugar Daddy (.edt) & Real Name Licensing (.dbc/.lnc)",
    sub_players: "⚽ Players Explorer & Live Editor",
    sub_clubs: "🏛️ Clubs, Finances, Stadiums & League Tables",
    sub_staff: "👔 Staff (26 Hidden Attributes) & DoF Center",
    sub_tables: "📊 All 28 Save Tables & 81 Raw Sections",
    sub_pregame: "🗄️ Pre-Game Installation DBs (2700 / Wonderkids / lang_db)",
    sub_opt_main: "🚀 Unity boot.config, FPS Presets, Video Bypass & URP Analysis",
    sub_patches: "🔧 Binary & UI Bundle Patches (50-Player Limit + 10 Table Sorting Unlockers)",
    sub_alltables: "🔓 All 252 Unsortable StreamedTables Scanner & Unlocker",
    sub_rules: "👑 Sugar Daddy (.edt), Real Name/National Team Licensing (.dbc/.lnc) & Rule Editor",
    hdr_player_list: "Save Player Database",
  }
};

function showToast(msg, isError=false) {
  const el = document.getElementById('toast');
  el.style.borderColor = isError ? '#ef4444' : '#f5b731';
  el.textContent = msg;
  el.style.display = 'block';
  clearTimeout(window._toastTimer);
  window._toastTimer = setTimeout(() => { el.style.display = 'none'; }, 4200);
}

async function apiGet(url) {
  const r = await fetch(url);
  const d = await r.json();
  if (!r.ok) throw new Error(d.error || 'API Error');
  return d;
}

async function apiPost(url, body) {
  const r = await fetch(url, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body || {})
  });
  const d = await r.json();
  if (!r.ok) throw new Error(d.error || 'API Error');
  return d;
}

function gt(key, fallback='') {
  return STATE.gameTerms[key] || fallback || key;
}

function tierClass(v) {
  const n = Number(v) || 0;
  if (n >= 16) return 'tier-elite';
  if (n >= 11) return 'tier-good';
  if (n >= 6)  return 'tier-avg';
  return 'tier-low';
}

function fmtMoney(n) {
  if (n === null || n === undefined) return '—';
  return Number(n).toLocaleString('tr-TR');
}

function switchPillar(p) {
  [1,2,3].forEach(i => {
    document.getElementById('pillar-btn-' + i).classList.toggle('active', i === p);
    document.getElementById('subnav-' + i).style.display = (i === p) ? 'flex' : 'none';
  });
  if (p === 1) {
    const activeBtn = document.querySelector('#subnav-1 button.active');
    switchSubTab(1, activeBtn ? activeBtn.dataset.sub : 'p1-players');
  } else if (p === 2) {
    switchSubTab(2, 'p2-main');
    loadOptimizationState();
  } else if (p === 3) {
    const activeBtn = document.querySelector('#subnav-3 button.active');
    switchSubTab(3, activeBtn ? activeBtn.dataset.sub : 'p3-patches');
  }
}

function switchSubTab(pillar, subId) {
  document.querySelectorAll('#subnav-' + pillar + ' button').forEach(b => {
    b.classList.toggle('active', b.dataset.sub === subId);
  });
  document.querySelectorAll('.subview').forEach(s => {
    s.style.display = (s.id === 'view-' + subId) ? 'block' : 'none';
  });
  if (subId === 'p1-clubs') { loadClubs(); loadStadiums(); }
  if (subId === 'p1-staff') { loadStaff(); }
  if (subId === 'p1-tables') { loadAnySaveTable(); loadSaveSections(); }
  if (subId === 'p1-pregame' && !STATE.pregameLoaded) { loadPregameDb(); }
  if (subId === 'p3-patches') { loadPatchesStatus(); }
  if (subId === 'p3-alltables' && !STATE.streamedLoaded) { loadStreamedTables(false); }
  if (subId === 'p3-rules') { loadRulesAndDbc(); }
}

function applyUiTranslations() {
  const dict = UI_I18N[STATE.uiLang] || UI_I18N.tr;
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const k = el.getAttribute('data-i18n');
    if (dict[k]) el.textContent = dict[k];
  });
}

function applyGameTermLabels() {
  // Update column headers & labels that use in-game localization terms!
  document.getElementById('th-pl-pos').textContent = gt('position', 'Mevki');
  document.getElementById('th-pl-age').textContent = gt('age', 'Yaş');
  document.getElementById('th-pl-val').textContent = gt('value', 'Değer');
  document.getElementById('th-pl-wage').textContent = gt('wage', 'Maaş');
  document.getElementById('lbl-pe-ca').textContent = gt('current_ability', 'Current Ability') + ' (CA)';
  document.getElementById('lbl-pe-pa').textContent = gt('potential_ability', 'Potential Ability') + ' (PA)';
  document.getElementById('lbl-pe-val').textContent = gt('value', 'Value') + ' (€)';
  document.getElementById('lbl-pe-wage').textContent = gt('wage', 'Wage') + ' (€/w)';
  document.getElementById('lbl-pe-ctend').textContent = gt('contract_expires', 'Contract Expires');
  document.getElementById('lbl-pe-age').textContent = gt('age', 'Age');
  document.getElementById('lbl-pe-height').textContent = gt('height', 'Height') + ' (cm)';
  document.getElementById('lbl-pe-cond').textContent = gt('condition', 'Condition');
  document.getElementById('lbl-pe-rep').textContent = gt('world_reputation', 'World Reputation');
  document.getElementById('lbl-stf-ca').textContent = gt('current_ability', 'Current Ability') + ' (CA)';
  document.getElementById('lbl-stf-pa').textContent = gt('potential_ability', 'Potential Ability') + ' (PA)';

  const sel = document.getElementById('sel-game-lang');
  const opt = sel.options[sel.selectedIndex];
  document.getElementById('badge-active-gamelang').textContent = opt ? opt.textContent : STATE.gameLang;

  if (STATE.activePlayerDetail) {
    renderPlayerDetail(STATE.activePlayerDetail);
  }
}

async function initStudio() {
  const ov = await apiGet('/api/overview?game_lang=' + encodeURIComponent(STATE.gameLang));
  STATE.gameTerms = ov.active_game_terms.terms || {};
  STATE.attrGroups = ov.active_game_terms.player_attribute_groups || {};
  STATE.staffGroups = ov.active_game_terms.staff_attribute_groups || {};

  // Populate saves dropdown
  const selSave = document.getElementById('sel-save');
  selSave.innerHTML = '';
  (ov.available_saves || []).forEach(s => {
    const o = document.createElement('option');
    o.value = s.path;
    o.textContent = `${s.name} (${s.size_mb} MB)`;
    if (ov.active_save && ov.active_save.path === s.path) o.selected = true;
    selSave.appendChild(o);
  });

  // Populate installs dropdown
  const selInst = document.getElementById('sel-install');
  selInst.innerHTML = '';
  (ov.available_installs || []).forEach(ins => {
    const o = document.createElement('option');
    o.value = ins.path;
    o.textContent = `${ins.label} — ${ins.name}`;
    if (ov.active_fm_dir === ins.path) o.selected = true;
    selInst.appendChild(o);
  });

  // Populate 21 official FM languages dropdown
  const selLang = document.getElementById('sel-game-lang');
  selLang.innerHTML = '';
  (ov.game_languages || []).forEach(l => {
    const o = document.createElement('option');
    o.value = l.code;
    o.textContent = `${l.name} (${l.code})`;
    if (l.code === STATE.gameLang) o.selected = true;
    selLang.appendChild(o);
  });

  renderSaveKpiBar(ov.active_save);
  applyUiTranslations();
  applyGameTermLabels();
  await loadPlayers();
}

function renderSaveKpiBar(info) {
  const box = document.getElementById('save-kpi-bar');
  if (!info) {
    box.innerHTML = '<div class="stat-card"><div class="k">Aktif Save</div><div class="v">Yok</div></div>';
    return;
  }
  document.getElementById('badge-save-summary').textContent = `${info.file} (${info.game_date})`;
  document.getElementById('ste-gamedate').value = info.game_date || '';
  box.innerHTML = `
    <div class="stat-card"><div class="k">Aktif Save Dosyası</div><div class="v" style="font-size:14px;">${info.file}</div></div>
    <div class="stat-card"><div class="k">Oyun Tarihi & Sürüm</div><div class="v">${info.game_date} <span class="badge">${info.build}</span></div></div>
    <div class="stat-card"><div class="k">Yönetilen Kulüp</div><div class="v">${info.managed_club_name || ('#' + info.managed_club_uid)}</div></div>
    <div class="stat-card"><div class="k">Oyuncu Sayısı</div><div class="v">${fmtMoney(info.players_count)}</div></div>
    <div class="stat-card"><div class="k">Kulüp & Stadyum</div><div class="v">${fmtMoney(info.clubs_count)} / ${fmtMoney(info.stadiums_count)}</div></div>
    <div class="stat-card"><div class="k">Teknik Heyet (Staff)</div><div class="v">${fmtMoney(info.staff_count)}</div></div>
  `;
}

async function onChangeGameLang() {
  const code = document.getElementById('sel-game-lang').value;
  STATE.gameLang = code;
  const data = await apiGet('/api/game-terms?lang=' + encodeURIComponent(code));
  STATE.gameTerms = data.terms || {};
  STATE.attrGroups = data.player_attribute_groups || {};
  STATE.staffGroups = data.staff_attribute_groups || {};
  applyGameTermLabels();
  loadPlayers();
  showToast(`Oyun içi terim dili '${data.name}' (${code}) olarak güncellendi!`);
}

function onChangeUiLang() {
  STATE.uiLang = document.getElementById('sel-ui-lang').value;
  applyUiTranslations();
}

async function onChangeSaveSelect() {
  const sp = document.getElementById('sel-save').value;
  showToast('Save dosyası yükleniyor...');
  const ov = await apiPost('/api/context', {save_path: sp});
  renderSaveKpiBar(ov.active_save);
  await loadPlayers();
  showToast('Aktif save değiştirildi: ' + sp);
}

async function promptCustomSave() {
  const p = prompt('Tam .fm save dosya yolunu girin:');
  if (!p) return;
  try {
    const ov = await apiPost('/api/context', {save_path: p});
    renderSaveKpiBar(ov.active_save);
    await loadPlayers();
    showToast('Save yüklendi: ' + p);
  } catch (e) {
    showToast(e.message, true);
  }
}

async function onChangeInstallSelect() {
  const fd = document.getElementById('sel-install').value;
  STATE.pregameLoaded = false;
  STATE.streamedLoaded = false;
  await apiPost('/api/context', {fm_dir: fd});
  showToast('Aktif oyun kurulum dizini değiştirildi: ' + fd);
}

// ============================================================================
// PILLAR 1.1: PLAYERS & LOCALIZED ATTRIBUTE SHEET
// ============================================================================
let _plTimer = null;
function debouncedLoadPlayers() {
  clearTimeout(_plTimer);
  _plTimer = setTimeout(loadPlayers, 200);
}

async function loadPlayers() {
  const q = document.getElementById('flt-player-q').value;
  const club = document.getElementById('flt-player-club').value;
  const pos = document.getElementById('flt-player-pos').value;
  const minCa = document.getElementById('flt-player-minca').value || '0';
  const sort = document.getElementById('flt-player-sort').value;
  const url = `/api/players?q=${encodeURIComponent(q)}&club=${encodeURIComponent(club)}&pos=${encodeURIComponent(pos)}&min_ca=${minCa}&sort_by=${sort}&limit=120`;
  const data = await apiGet(url);
  document.getElementById('players-count-badge').textContent = `${data.total} kayıt`;
  const tbody = document.getElementById('tbody-players');
  tbody.innerHTML = '';
  (data.rows || []).forEach((p, idx) => {
    const tr = document.createElement('tr');
    if (p.uid === STATE.activePlayerUid) tr.className = 'selected-row';
    tr.style.cursor = 'pointer';
    tr.onclick = () => selectPlayer(p.uid);
    const posLoc = gt('pos_' + (p.best_pos || '').toLowerCase(), p.best_pos);
    const injBadge = (p.injuries && p.injuries.length) ? ` <span class="badge badge-danger" title="${p.injuries.join(', ')}">🏥</span>` : '';
    const susBadge = p.suspensions_count ? ` <span class="badge badge-gold">🟨${p.suspensions_count}</span>` : '';
    tr.innerHTML = `
      <td><code>${p.uid}</code></td>
      <td><strong>${p.name}</strong>${injBadge}${susBadge}<div style="font-size:10.5px;color:var(--muted);">${p.nationality}</div></td>
      <td><span class="badge badge-cyan">${posLoc}</span></td>
      <td>${p.age}</td>
      <td><span class="badge badge-green">${p.ca}</span></td>
      <td><span class="badge badge-gold">${p.pa}</span></td>
      <td>${p.club || '—'}</td>
      <td>${fmtMoney(p.value)}</td>
      <td>${fmtMoney(p.wage)}</td>
    `;
    tbody.appendChild(tr);
    if (idx === 0 && !STATE.activePlayerUid) {
      selectPlayer(p.uid);
    }
  });
}

async function selectPlayer(uid) {
  STATE.activePlayerUid = uid;
  const detail = await apiGet('/api/player-detail?uid=' + uid);
  STATE.activePlayerDetail = detail;
  renderPlayerDetail(detail);
  document.querySelectorAll('#tbody-players tr').forEach(tr => {
    tr.classList.toggle('selected-row', tr.innerHTML.includes(`>${uid}<`));
  });
}

function renderPlayerDetail(d) {
  const s = d.summary || {};
  document.getElementById('pe-body').style.display = 'block';
  document.getElementById('pe-title').textContent = `${s.name} (#${s.uid})`;
  document.getElementById('pe-subtitle').textContent = `${s.club || 'Serbest'} • ${s.nationality || ''} • Doğum: ${s.birth_date || ''}`;

  document.getElementById('pe-ca').value = s.ca || 0;
  document.getElementById('pe-pa').value = s.pa || 0;
  document.getElementById('pe-value').value = s.value || 0;
  document.getElementById('pe-wage').value = s.wage || 0;
  document.getElementById('pe-contract-end').value = s.contract_end || '';
  document.getElementById('pe-age').value = s.age || 0;
  document.getElementById('pe-height').value = s.height_cm || 0;
  document.getElementById('pe-condition').value = s.condition || 0;
  document.getElementById('pe-world-rep').value = s.world_rep || 0;

  // Render 14 positions with localized labels
  const posGrid = document.getElementById('pe-positions-grid');
  posGrid.innerHTML = '';
  const posOrder = ['GK','DL','DC','DR','WBL','WBR','DM','ML','MC','MR','AML','AMC','AMR','ST'];
  posOrder.forEach(code => {
    const val = (d.positions && d.positions[code]) || 1;
    const locCode = gt('pos_' + code.toLowerCase(), code);
    const div = document.createElement('div');
    div.className = 'field-item';
    div.innerHTML = `
      <label title="${code}">${locCode} <span style="opacity:0.6">(${code})</span></label>
      <input type="number" class="attr-input ${tierClass(val)}" data-pos="${code}" value="${val}" min="1" max="20"
             oninput="this.className='attr-input ' + tierClass(this.value)"/>
    `;
    posGrid.appendChild(div);
  });

  // Render 4 Attribute Columns in the selected In-Game Term Language!
  const colsBox = document.getElementById('pe-attr-columns');
  colsBox.innerHTML = '';
  const groupDefs = [
    {key: 'technical', titleKey: 'cat_technical', fallback: 'Technical'},
    {key: 'mental', titleKey: 'cat_mental', fallback: 'Mental'},
    {key: 'physical', titleKey: 'cat_physical', fallback: 'Physical'},
    {key: 'goalkeeping', titleKey: 'cat_goalkeeping', fallback: 'Goalkeeping'},
    {key: 'hidden', titleKey: 'cat_hidden', fallback: 'Hidden / Personality'},
  ];

  groupDefs.forEach(g => {
    const attrKeys = (STATE.attrGroups && STATE.attrGroups[g.key]) || [];
    if (!attrKeys.length) return;
    const box = document.createElement('div');
    box.className = 'attr-box';
    const gTitle = gt(g.titleKey, g.fallback);
    let rowsHtml = `<h4><span>${gTitle}</span><span>1..20</span></h4>`;
    attrKeys.forEach(ak => {
      if (d.attributes[ak] === undefined) return;
      const val = d.attributes[ak];
      const locName = gt(ak, ak);
      const locAbbr = gt(ak + '_abbr', '');
      rowsHtml += `
        <div class="attr-row" title="Canonical key: ${ak}">
          <div class="attr-name">
            ${locAbbr ? `<span class="attr-abbr">${locAbbr}</span>` : ''}
            <span>${locName}</span>
          </div>
          <input type="number" class="attr-input ${tierClass(val)}" data-attr="${ak}" value="${val}" min="1" max="20"
                 oninput="this.className='attr-input ' + tierClass(this.value)"/>
        </div>
      `;
    });
    box.innerHTML = rowsHtml;
    colsBox.appendChild(box);
  });

  // Render Top IP & OOP Roles
  const rBox = document.getElementById('pe-roles-box');
  rBox.innerHTML = '';
  const rb = d.role_breakdown || {};
  const ipRoles = rb.top_in_possession_roles || [];
  const oopRoles = rb.top_out_of_possession_roles || [];
  ipRoles.slice(0, 4).forEach(r => {
    const sp = document.createElement('span');
    sp.className = 'badge badge-green';
    sp.textContent = `[IP] ${r.role_name || r.role} (${r.duty || ''}): ${r.score || r.rating || ''}`;
    rBox.appendChild(sp);
  });
  oopRoles.slice(0, 4).forEach(r => {
    const sp = document.createElement('span');
    sp.className = 'badge badge-cyan';
    sp.textContent = `[OOP] ${r.role_name || r.code || ''}: ${r.score || ''}`;
    rBox.appendChild(sp);
  });
}

async function saveCurrentPlayerEdits(maxOut=false) {
  if (!STATE.activePlayerUid) return;
  const attrs = {};
  document.querySelectorAll('#pe-attr-columns input[data-attr]').forEach(inp => {
    attrs[inp.getAttribute('data-attr')] = Number(inp.value);
  });
  const positions = {};
  document.querySelectorAll('#pe-positions-grid input[data-pos]').forEach(inp => {
    positions[inp.getAttribute('data-pos')] = Number(inp.value);
  });
  const payload = {
    player_uid: STATE.activePlayerUid,
    max_out_player: maxOut,
    player_fields: {
      ca: Number(document.getElementById('pe-ca').value),
      pa: Number(document.getElementById('pe-pa').value),
      value: Number(document.getElementById('pe-value').value),
      age: Number(document.getElementById('pe-age').value),
      height_cm: Number(document.getElementById('pe-height').value),
      condition: Number(document.getElementById('pe-condition').value),
      world_rep: Number(document.getElementById('pe-world-rep').value),
    },
    contract_fields: {
      wage: Number(document.getElementById('pe-wage').value),
      contract_end: document.getElementById('pe-contract-end').value,
    },
    attributes: maxOut ? null : attrs,
    positions: maxOut ? null : positions,
  };
  showToast('Save dosyası düzenleniyor ve doğrulanıyor...');
  const res = await apiPost('/api/save-edit', payload);
  renderSaveKpiBar(res.active_save);
  await loadPlayers();
  await selectPlayer(STATE.activePlayerUid);
  showToast(`Kaydedildi -> ${res.output_path}`);
}

async function healCurrentPlayer() {
  if (!STATE.activePlayerUid) return;
  showToast('Sakatlıklar ve cezalar temizleniyor...');
  const res = await apiPost('/api/save-edit', {
    player_uid: STATE.activePlayerUid,
    heal_injuries: true,
    clear_suspensions: true,
  });
  renderSaveKpiBar(res.active_save);
  await loadPlayers();
  await selectPlayer(STATE.activePlayerUid);
  showToast(`Oyuncu iyileştirildi ve cezaları silindi -> ${res.output_path}`);
}

// ============================================================================
// PILLAR 1.2: CLUBS, FINANCES & STADIUMS
// ============================================================================
async function loadClubs() {
  const q = document.getElementById('flt-club-q').value;
  const sort = document.getElementById('flt-club-sort').value;
  const d = await apiGet(`/api/clubs?q=${encodeURIComponent(q)}&sort_by=${sort}&limit=100`);
  const tb = document.getElementById('tbody-clubs');
  tb.innerHTML = '';
  (d.rows || []).forEach((c, idx) => {
    const tr = document.createElement('tr');
    tr.style.cursor = 'pointer';
    tr.onclick = () => selectClub(c);
    tr.innerHTML = `
      <td><code>${c.uid}</code></td>
      <td><strong>${c.name}</strong></td>
      <td><span class="badge badge-gold">${c.reputation}</span></td>
      <td>${fmtMoney(c.balance)}</td>
      <td><span class="badge badge-green">${fmtMoney(c.transfer_budget)}</span></td>
      <td>${fmtMoney(c.wage_budget)}</td>
      <td>${c.corporate_facilities || '—'}</td>
    `;
    tb.appendChild(tr);
    if (idx === 0 && !document.getElementById('ce-uid').value) selectClub(c);
  });
}

function selectClub(c) {
  document.getElementById('ce-uid').value = c.uid;
  document.getElementById('ce-title').textContent = `🏛️ ${c.name} (#${c.uid}) — Finans & Tesis Editörü`;
  document.getElementById('ce-rep').value = c.reputation || 0;
  document.getElementById('ce-balance').value = c.balance || 0;
  document.getElementById('ce-tbudget').value = c.transfer_budget || 0;
  document.getElementById('ce-wbudget').value = c.wage_budget || 0;
  document.getElementById('ce-corpfac').value = c.corporate_facilities || 10;
}

function presetRichClub() {
  document.getElementById('ce-balance').value = 500000000;
  document.getElementById('ce-tbudget').value = 250000000;
  document.getElementById('ce-wbudget').value = 6000000;
  document.getElementById('ce-rep').value = 9500;
  document.getElementById('ce-corpfac').value = 20;
}

async function saveClubEdits() {
  const uid = document.getElementById('ce-uid').value;
  if (!uid) return;
  showToast('Kulüp finans ve tesis bilgileri kaydediliyor...');
  const res = await apiPost('/api/save-edit', {
    club_uid: Number(uid),
    club_fields: {
      reputation: Number(document.getElementById('ce-rep').value),
      balance: Number(document.getElementById('ce-balance').value),
      transfer_budget: Number(document.getElementById('ce-tbudget').value),
      wage_budget: Number(document.getElementById('ce-wbudget').value),
      corporate_facilities: Number(document.getElementById('ce-corpfac').value),
    }
  });
  renderSaveKpiBar(res.active_save);
  await loadClubs();
  showToast(`Kulüp güncellendi -> ${res.output_path}`);
}

async function loadStadiums() {
  const q = document.getElementById('flt-stadium-q').value;
  const d = await apiGet(`/api/stadiums?q=${encodeURIComponent(q)}&limit=80`);
  const tb = document.getElementById('tbody-stadiums');
  tb.innerHTML = '';
  (d.rows || []).forEach((s, idx) => {
    const tr = document.createElement('tr');
    tr.style.cursor = 'pointer';
    tr.onclick = () => {
      document.getElementById('ste-uid').value = s.uid;
      document.getElementById('ste-cap').value = s.capacity;
      document.getElementById('ste-seat').value = s.all_seater_capacity;
    };
    tr.innerHTML = `<td><code>${s.uid}</code></td><td><strong>${s.name}</strong></td><td>${fmtMoney(s.capacity)}</td><td>${fmtMoney(s.all_seater_capacity)}</td>`;
    tb.appendChild(tr);
    if (idx === 0 && !document.getElementById('ste-uid').value) {
      document.getElementById('ste-uid').value = s.uid;
      document.getElementById('ste-cap').value = s.capacity;
      document.getElementById('ste-seat').value = s.all_seater_capacity;
    }
  });
}

async function saveStadiumAndDateEdits() {
  const stUid = document.getElementById('ste-uid').value;
  const gDate = document.getElementById('ste-gamedate').value;
  const payload = {};
  if (stUid) {
    payload.stadium_uid = Number(stUid);
    payload.stadium_fields = {
      capacity: Number(document.getElementById('ste-cap').value),
      all_seater_capacity: Number(document.getElementById('ste-seat').value),
    };
  }
  if (gDate) payload.game_date = gDate;
  showToast('Stadyum / Oyun tarihi kaydediliyor...');
  const res = await apiPost('/api/save-edit', payload);
  renderSaveKpiBar(res.active_save);
  await loadStadiums();
  showToast(`Kaydedildi -> ${res.output_path}`);
}

// ============================================================================
// PILLAR 1.3: STAFF (26 HIDDEN ATTRIBUTES) & DoF
// ============================================================================
async function loadStaff() {
  const q = document.getElementById('flt-staff-q').value;
  const role = document.getElementById('flt-staff-role').value;
  const d = await apiGet(`/api/staff?q=${encodeURIComponent(q)}&role=${encodeURIComponent(role)}&limit=100`);
  const tb = document.getElementById('tbody-staff');
  tb.innerHTML = '';
  (d.rows || []).forEach((s, idx) => {
    const tr = document.createElement('tr');
    tr.style.cursor = 'pointer';
    tr.onclick = () => selectStaff(s);
    tr.innerHTML = `
      <td><code>${s.uid}</code></td>
      <td><strong>${s.name || ('#' + s.uid)}</strong></td>
      <td><span class="badge badge-cyan">${s.role_name || 'Staff'}</span></td>
      <td>${s.club_name || '—'}</td>
      <td><span class="badge badge-green">${s.ca || 0}</span></td>
      <td><span class="badge badge-gold">${s.pa || 0}</span></td>
    `;
    tb.appendChild(tr);
    if (idx === 0 && !document.getElementById('stf-uid').value) selectStaff(s);
  });
}

function selectStaff(s) {
  document.getElementById('stf-uid').value = s.uid;
  document.getElementById('stf-title').textContent = `👔 ${s.name || ('#' + s.uid)} (${s.role_name || ''}) — ${s.club_name || 'Serbest'}`;
  document.getElementById('stf-ca').value = s.ca || 0;
  document.getElementById('stf-pa').value = s.pa || 0;
  const box = document.getElementById('stf-attrs-box');
  const b40 = s.block_40_attributes_1_20 || s.attributes_1_20 || s.block_40 || {};
  let html = '<div class="attr-box"><h4><span>Personel Özellikleri (1..20)</span><span>Seçilen Dilde</span></h4>';
  Object.entries(b40).forEach(([k, v]) => {
    const loc = gt(k, k);
    const val20 = v > 20 ? Math.max(1, Math.round(v / 5)) : v;
    html += `
      <div class="attr-row">
        <div class="attr-name"><span>${loc}</span></div>
        <span class="badge ${tierClass(val20)}">${val20} <span style="opacity:0.65">(${v})</span></span>
      </div>
    `;
  });
  html += '</div>';
  box.innerHTML = html;
}

async function saveStaffEdits(maxOut=false) {
  const uid = document.getElementById('stf-uid').value;
  if (!uid) return;
  showToast('Personel bilgileri kaydediliyor...');
  const res = await apiPost('/api/save-edit', {
    staff_uid: Number(uid),
    max_out_staff: maxOut,
    staff_fields: {
      ca: Number(document.getElementById('stf-ca').value),
      pa: Number(document.getElementById('stf-pa').value),
    }
  });
  renderSaveKpiBar(res.active_save);
  await loadStaff();
  showToast(`Personel güncellendi -> ${res.output_path}`);
}

async function hireSelectedStaffAsCoach() {
  const uid = document.getElementById('stf-uid').value;
  if (!uid) return;
  showToast('Teknik direktör kulübe atanıyor (DoF)...');
  const res = await apiPost('/api/dof-hire', {coach: Number(uid), years: 3});
  renderSaveKpiBar(res.active_save);
  await loadStaff();
  showToast(`Teknik direktör atandı! Çıktı: ${res.active_save.path}`);
}

// ============================================================================
// PILLAR 1.4: ALL 28 SAVE TABLES & 81 SECTIONS
// ============================================================================
async function loadAnySaveTable() {
  const tbl = document.getElementById('sel-any-table').value;
  const q = document.getElementById('flt-any-table').value;
  const d = await apiGet(`/api/save-table?table=${encodeURIComponent(tbl)}&q=${encodeURIComponent(q)}&limit=80`);
  const thead = document.getElementById('thead-any-save');
  const tbody = document.getElementById('tbody-any-save');
  const rows = d.rows || [];
  if (!rows.length) {
    thead.innerHTML = '<tr><th>Sonuç Yok</th></tr>';
    tbody.innerHTML = '';
    return;
  }
  const cols = Object.keys(rows[0]).slice(0, 12);
  thead.innerHTML = '<tr>' + cols.map(c => `<th>${c}</th>`).join('') + '</tr>';
  tbody.innerHTML = rows.map(r => {
    return '<tr>' + cols.map(c => {
      let v = r[c];
      if (v && typeof v === 'object') v = JSON.stringify(v);
      return `<td>${v !== null && v !== undefined ? String(v).slice(0, 75) : '—'}</td>`;
    }).join('') + '</tr>';
  }).join('');
}

async function loadSaveSections() {
  const d = await apiGet('/api/save-sections');
  const tb = document.getElementById('tbody-save-sections');
  tb.innerHTML = (d.sections || []).map(s => `
    <tr>
      <td><code>${s.name}</code></td>
      <td>${fmtMoney(s.compressed_size)}</td>
      <td>${fmtMoney(s.decompressed_size)}</td>
      <td><span class="badge">${s.ratio}x</span></td>
    </tr>
  `).join('');
}

// ============================================================================
// PILLAR 1.5: PRE-GAME INSTALLATION DATABASES (2700 / 2620)
// ============================================================================
async function loadPregameDb() {
  showToast('Kurulum Pre-Game veritabanları (2700/2620) okunuyor...');
  const d = await apiGet('/api/pregame-db');
  STATE.pregameLoaded = true;
  const p = d.people_db || {};
  const m = d.master_db || {};
  const mv = d.multi_version || {};

  const bStats = p.basic_people_db || {};
  document.getElementById('pregame-kpi-bar').innerHTML = `
    <div class="stat-card"><div class="k">Pre-Game Kişi Sayısı (2700)</div><div class="v">${fmtMoney(bStats.total_people_records || 723010)}</div></div>
    <div class="stat-card"><div class="k">Oyuncu / Personel (basic_people_db)</div><div class="v">${fmtMoney(bStats.player_records || 532775)}</div></div>
    <div class="stat-card"><div class="k">-10 / -95 Wonderkid Adayları</div><div class="v">${fmtMoney((bStats.negative_pa_tiers || {})['-10 (170-200 PA)'] || 0)} / ${fmtMoney((bStats.negative_pa_tiers || {})['-95 (160-190 PA)'] || 0)}</div></div>
    <div class="stat-card"><div class="k">Master DB Kulüp & Stadyum</div><div class="v">96.343 / 51.118</div></div>
    <div class="stat-card"><div class="k">Şehir & Turnuva</div><div class="v">58.349 / 7.973</div></div>
  `;

  const wk = bStats.sample_wonderkids_or_high_pa || [];
  let pHtml = `<div style="margin-bottom:8px;font-size:12px;color:var(--muted);">Negatif PA Dağılımı: <code>${JSON.stringify(bStats.negative_pa_tiers || {})}</code></div>`;
  pHtml += `<div class="table-wrap" style="max-height:420px;"><table><thead><tr><th>UID</th><th>Doğum Yılı</th><th>CA</th><th>PA / Kod</th><th>Ülke ID</th></tr></thead><tbody>`;
  wk.slice(0, 50).forEach(w => {
    pHtml += `<tr><td><code>${w.uid || w.db_id || ''}</code></td><td>${w.birth_year || ''}</td><td><span class="badge badge-green">${w.ca || ''}</span></td><td><span class="badge badge-gold">${w.pa_raw || w.pa || ''}</span></td><td>${w.nation_id || ''}</td></tr>`;
  });
  pHtml += `</tbody></table></div>`;
  document.getElementById('pregame-people-box').innerHTML = pHtml;

  const tables = m.client_db_tables || m.tables || {};
  let mHtml = `<div class="table-wrap" style="max-height:240px;margin-bottom:10px;"><table><thead><tr><th>Master DB Tablosu (client_db.dat)</th><th>Kayıt / Çerçeve Bilgisi</th></tr></thead><tbody>`;
  Object.entries(tables).forEach(([tk, tv]) => {
    mHtml += `<tr><td><strong>${tk}</strong></td><td><code>${JSON.stringify(tv).slice(0, 110)}</code></td></tr>`;
  });
  mHtml += `</tbody></table></div>`;

  const vers = mv.versions || {};
  mHtml += `<h4 style="margin:8px 0 6px;color:var(--cyan);">Tarihsel DB Sürüm Evrimi (2300 .. 2700)</h4><div class="table-wrap" style="max-height:200px;"><table><thead><tr><th>Sürüm</th><th>Dosya Detayı</th></tr></thead><tbody>`;
  Object.entries(vers).forEach(([vk, vv]) => {
    mHtml += `<tr><td><span class="badge badge-gold">${vk}</span></td><td><code>${JSON.stringify(vv).slice(0, 110)}</code></td></tr>`;
  });
  mHtml += `</tbody></table></div>`;
  document.getElementById('pregame-master-box').innerHTML = mHtml;
}

// ============================================================================
// PILLAR 2: GAME OPTIMIZATION SUITE
// ============================================================================
async function loadOptimizationState() {
  const d = await apiGet('/api/optimization');
  renderBootConfigForm(d.boot_config);

  const vtb = document.getElementById('tbody-opt-videos');
  vtb.innerHTML = (d.videos || []).map(v => `
    <tr>
      <td><code>${v.name}</code></td>
      <td>${v.size_mb} MB</td>
      <td>${v.disabled ? '<span class="badge badge-gold">DEVRE DIŞI (.disabled)</span>' : '<span class="badge badge-green">AKTİF</span>'}</td>
    </tr>
  `).join('');

  const utb = document.getElementById('tbody-urp-profiles');
  utb.innerHTML = (d.urp_profiles || []).map(u => `
    <tr>
      <td><strong>${u.profile}</strong></td>
      <td><span class="badge badge-green">${u.srp_batcher ? 'Açık' : 'Kapalı'}</span></td>
      <td>${u.msaa}</td>
      <td>${u.upscaling_filter}</td>
      <td>${u.shadow_distance}</td>
      <td>${u.additional_lights_limit}</td>
    </tr>
  `).join('');

  const dtb = document.getElementById('tbody-db-footprint');
  dtb.innerHTML = (d.db_versions || []).map(v => `
    <tr>
      <td><strong>${v.version}</strong></td>
      <td>${v.file_count} dosya</td>
      <td>${v.size_mb} MB</td>
      <td>${v.is_latest ? '<span class="badge badge-green">Aktif Ana DB</span>' : '<span class="badge">Eski / Miras DB</span>'}</td>
    </tr>
  `).join('');
}

function renderBootConfigForm(bc) {
  const box = document.getElementById('boot-config-form');
  const vals = bc.values || {};
  document.getElementById('boot-cpu-hint').textContent = `Donanım: ${bc.cpu_logical_cores} Mantıksal Çekirdek (Önerilen job-worker-count: ${bc.recommended_job_workers})`;
  box.innerHTML = (bc.known_keys || []).map(k => {
    const cur = vals[k.key] !== undefined ? vals[k.key] : '';
    const title = STATE.uiLang === 'en' ? k.title_en : k.title_tr;
    const desc = STATE.uiLang === 'en' ? k.desc_en : k.desc_tr;
    return `
      <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid var(--border); gap:12px;">
        <div>
          <div style="font-weight:700; color:var(--text);">${title} <code style="color:var(--cyan);">(${k.key})</code></div>
          <div style="font-size:11.5px; color:var(--muted);">${desc}</div>
        </div>
        <input type="text" data-boot-key="${k.key}" value="${cur}" placeholder="Varsayılan: ${k.default}" style="width:110px; text-align:center; font-weight:700;"/>
      </div>
    `;
  }).join('');
}

async function saveBootConfig() {
  const values = {};
  document.querySelectorAll('[data-boot-key]').forEach(inp => {
    values[inp.getAttribute('data-boot-key')] = inp.value;
  });
  const bc = await apiPost('/api/optimization/boot-config', {values});
  renderBootConfigForm(bc);
  showToast('fm_Data/boot.config güncellendi (.bak yedeği korundu)!');
}

async function applyBootPreset(preset) {
  const bc = await apiPost('/api/optimization/boot-preset', {preset});
  renderBootConfigForm(bc);
  showToast(`boot.config '${preset}' performans profili uygulandı!`);
}

async function restoreBootConfig() {
  const bc = await apiPost('/api/optimization/boot-restore', {});
  renderBootConfigForm(bc);
  showToast('boot.config orijinal yedeğinden (.bak) geri yüklendi!');
}

async function toggleAllVideos(disable) {
  await apiPost('/api/optimization/videos-toggle', {disable});
  await loadOptimizationState();
  showToast(disable ? 'Video/Promo paketleri devre dışı bırakıldı!' : 'Video/Promo paketleri tekrar etkinleştirildi!');
}

// ============================================================================
// PILLAR 3.1 & 3.2: BINARY & UI BUNDLE PATCHER + 252 STREAMEDTABLES
// ============================================================================
async function loadPatchesStatus() {
  const d = await apiGet('/api/patches');
  const patches = d.patches || [];
  const tb = document.getElementById('tbody-named-patches');
  tb.innerHTML = '';
  patches.forEach(p => {
    if (p.key === 'scout-player-limit') {
      const badge = document.getElementById('scout-limit-badge');
      badge.textContent = `Durum: ${p.state} (Aktif Sınır: ${p.current_value || 50} oyuncu)`;
      badge.className = 'badge ' + (p.is_patched ? 'badge-green' : 'badge-gold');
      if (p.current_value) document.getElementById('inp-max-scout-players').value = p.current_value;
    }
    const tr = document.createElement('tr');
    const stBadge = p.is_patched
      ? `<span class="badge badge-green">${p.state}</span>`
      : `<span class="badge badge-gold">${p.state}</span>`;
    tr.innerHTML = `
      <td><code>${p.key}</code></td>
      <td style="white-space:normal; max-width:440px;"><strong>${p.title}</strong><div style="font-size:11px;color:var(--muted);">${p.notes || ''}</div></td>
      <td><code>${p.target_file}</code></td>
      <td>${stBadge}</td>
      <td>${p.backup_exists ? '<span class="badge badge-cyan">Var (.bak)</span>' : '—'}</td>
      <td>
        <button class="btn-green" onclick="applyNamedPatch('${p.key}')">Uygula</button>
        <button class="btn-danger" onclick="restoreNamedPatch('${p.key}')">Geri Yükle</button>
      </td>
    `;
    tb.appendChild(tr);
  });
}

async function applyNamedPatch(key) {
  const body = {key};
  if (key === 'scout-player-limit') {
    body.max_players = Number(document.getElementById('inp-max-scout-players').value || 5000);
  }
  showToast(`'${key}' yaması uygulanıyor ve doğrulanıyor...`);
  await apiPost('/api/patches/apply', body);
  await loadPatchesStatus();
  showToast(`'${key}' başarıyla uygulandı!`);
}

async function applyAllSortingPatches() {
  showToast('Tüm 10 UI tablo sıralama yaması uygulanıyor...');
  await apiPost('/api/patches/apply-all-sorting', {});
  await loadPatchesStatus();
  showToast('Tüm 10 UI tablo sıralama yaması başarıyla açıldı!');
}

async function restoreNamedPatch(key) {
  showToast(`'${key}' yedekten geri yükleniyor...`);
  await apiPost('/api/patches/restore', {key});
  await loadPatchesStatus();
  showToast(`'${key}' orijinal haline döndürüldü!`);
}

async function loadStreamedTables(force=false) {
  showToast('UI VisualTreeAsset bundle dosyalarındaki tüm StreamedTable tabloları taranıyor...');
  const d = await apiGet('/api/patches/streamed-tables?only_unsortable=1');
  STATE.streamedTables = d.tables || [];
  STATE.streamedLoaded = true;
  renderStreamedTables();
  if (force) showToast(`${STATE.streamedTables.length} adet tablo tarandı!`);
}

function renderStreamedTables() {
  const q = (document.getElementById('flt-streamed-q').value || '').toLowerCase();
  const tb = document.getElementById('tbody-streamed-tables');
  const filtered = STATE.streamedTables.filter(t =>
    !q || t.vta_name.toLowerCase().includes(q) || (t.table_name || '').toLowerCase().includes(q) || t.bundle.toLowerCase().includes(q)
  );
  tb.innerHTML = filtered.map(t => `
    <tr>
      <td><code>${t.bundle.replace('ui-visualtreeassets_assets_', '')}</code></td>
      <td><strong>${t.vta_name}</strong></td>
      <td><code>${t.table_name || '—'}</code></td>
      <td><code>${t.offset_hex}</code></td>
      <td>${t.sorting_enabled ? '<span class="badge badge-green">Sıralama Açık (0)</span>' : '<span class="badge badge-gold">Sıralama Kilitli (1)</span>'}</td>
      <td>
        ${t.sorting_enabled
          ? `<button class="btn-danger" onclick="toggleStreamedTable('${t.bundle}', ${t.offset}, 1)">Kilitle (1)</button>`
          : `<button class="btn-green" onclick="toggleStreamedTable('${t.bundle}', ${t.offset}, 0)">🔓 Sıralamayı Aç (0)</button>`
        }
      </td>
    </tr>
  `).join('');
}

async function toggleStreamedTable(bundle, offset, disableSorting) {
  showToast(`${bundle} @ 0x${offset.toString(16)} güncelleniyor...`);
  await apiPost('/api/patches/streamed-table-toggle', {bundle, offset, disable_sorting: disableSorting});
  await loadStreamedTables(false);
  showToast('Tablo sıralama baytı güncellendi!');
}

// ============================================================================
// PILLAR 3.3: SUGAR DADDY (.edt) & LICENSING (.dbc / .lnc) EDITOR
// ============================================================================
async function loadRulesAndDbc() {
  const d = await apiGet('/api/rules');
  STATE.sugarDaddyEntries = (d.sugar_daddy && d.sugar_daddy.entries) || [];
  renderSugarDaddyTable();

  const tb = document.getElementById('tbody-rules-files');
  tb.innerHTML = (d.files || []).map(f => {
    const desc = STATE.uiLang === 'en' ? f.desc_en : f.desc_tr;
    return `
      <tr>
        <td><strong>${f.name}</strong><div style="font-size:10.5px;color:var(--muted);">${f.rel_path}</div></td>
        <td><span class="badge">${f.category.toUpperCase()}</span></td>
        <td style="white-space:normal; max-width:290px;">${desc}</td>
        <td>${f.disabled ? '<span class="badge badge-gold">DEVRE DIŞI</span>' : '<span class="badge badge-green">AKTİF</span>'}</td>
        <td>
          ${f.editable_text ? `<button class="btn-cyan" onclick="openRuleTextFile('${f.rel_path}')">📝 Düzenle</button>` : ''}
          ${f.disabled
            ? `<button class="btn-green" onclick="toggleRuleFile('${f.rel_path}', false)">Etkinleştir</button>`
            : `<button class="btn-danger" onclick="toggleRuleFile('${f.rel_path}', true)">Devre Dışı Bırak</button>`
          }
        </td>
      </tr>
    `;
  }).join('');
}

function renderSugarDaddyTable() {
  const tb = document.getElementById('tbody-sugardaddy');
  tb.innerHTML = STATE.sugarDaddyEntries.map((e, i) => `
    <tr>
      <td><input type="checkbox" ${e.enabled ? 'checked' : ''} onchange="STATE.sugarDaddyEntries[${i}].enabled=this.checked"/></td>
      <td><input type="text" value="${e.club}" onchange="STATE.sugarDaddyEntries[${i}].club=this.value" style="width:180px;"/></td>
      <td>
        <select onchange="STATE.sugarDaddyEntries[${i}].type=this.value">
          <option value="FRONT_END" ${e.type==='FRONT_END'?'selected':''}>FRONT_END</option>
          <option value="BACK_END" ${e.type==='BACK_END'?'selected':''}>BACK_END</option>
          <option value="UNDERWRITER" ${e.type==='UNDERWRITER'?'selected':''}>UNDERWRITER</option>
        </select>
      </td>
      <td><input type="checkbox" ${e.alter_starting_finances ? 'checked' : ''} onchange="STATE.sugarDaddyEntries[${i}].alter_starting_finances=this.checked"/></td>
      <td><button class="btn-danger" onclick="STATE.sugarDaddyEntries.splice(${i},1); renderSugarDaddyTable();">🗑️</button></td>
    </tr>
  `).join('');
}

function addSugarDaddyClub() {
  const club = document.getElementById('inp-sd-club').value.trim();
  if (!club) return;
  const sdType = document.getElementById('sel-sd-type').value;
  const alter = document.getElementById('chk-sd-alter').checked;
  STATE.sugarDaddyEntries.unshift({
    enabled: true,
    club: club,
    type: sdType,
    alter_starting_finances: alter,
  });
  document.getElementById('inp-sd-club').value = '';
  renderSugarDaddyTable();
}

async function saveSugarDaddyEdt() {
  const res = await apiPost('/api/rules/sugardaddy', {entries: STATE.sugarDaddyEntries});
  STATE.sugarDaddyEntries = res.entries || [];
  renderSugarDaddyTable();
  showToast('sugardaddy.edt başarıyla kaydedildi (.bak yedeği oluşturuldu)!');
}

async function openRuleTextFile(relPath) {
  const d = await apiGet('/api/rules/text-file?rel_path=' + encodeURIComponent(relPath));
  document.getElementById('rule-ed-relpath').value = d.rel_path;
  document.getElementById('rule-ed-title').textContent = `📝 ${d.name} (${d.encoding})`;
  document.getElementById('rule-ed-sub').textContent = `Göreli yol: ${d.rel_path} • Yedek (.bak): ${d.backup_exists ? 'Mevcut' : 'İlk kayıtta oluşturulacak'}`;
  document.getElementById('rule-ed-content').value = d.content || '';
}

async function saveRuleTextFile() {
  const rel = document.getElementById('rule-ed-relpath').value;
  if (!rel) return;
  const content = document.getElementById('rule-ed-content').value;
  const d = await apiPost('/api/rules/text-file', {rel_path: rel, content});
  showToast(`${d.name} başarıyla kaydedildi (${d.encoding})!`);
  await loadRulesAndDbc();
}

async function toggleRuleFile(relPath, disable) {
  await apiPost('/api/rules/toggle-file', {rel_path: relPath, disable});
  await loadRulesAndDbc();
  showToast(`${relPath} durumu güncellendi!`);
}

window.addEventListener('DOMContentLoaded', () => {
  initStudio().catch(e => showToast(e.message, true));
});
</script>
</body>
</html>
"""
