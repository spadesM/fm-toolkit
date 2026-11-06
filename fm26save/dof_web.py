"""Interactive Local Web Dashboard (Futbol Direktörü / DoF Komuta Merkezi) for FM27 / FM26 saves."""

from __future__ import annotations

import json
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from fm26save import FM26Save
from fm26save.dof import (
    FM27_TACTICAL_STYLES,
    analyze_coach_squad_fit,
    build_dof_dashboard,
    hire_head_coach,
    recommend_transfer_targets,
    scan_coach_candidates,
)

DOF_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>FM27 Futbol Direktörü (DoF) Komuta Merkezi</title>
<style>
  :root {
    --bg: #0c0e16;
    --panel: #151928;
    --panel-alt: #1c2236;
    --border: #2a3250;
    --accent: #f5b731;
    --accent-red: #c8102e;
    --green: #22c55e;
    --blue: #38bdf8;
    --warn: #f97316;
    --danger: #ef4444;
    --text: #f1f5f9;
    --muted: #94a3b8;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: 'Segoe UI', Inter, system-ui, sans-serif;
    background: var(--bg);
    color: var(--text);
  }
  header {
    background: linear-gradient(90deg, #1b0c1a 0%, #151928 55%, #1f1710 100%);
    border-bottom: 2px solid var(--accent);
    padding: 16px 28px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
  }
  .brand h1 {
    margin: 0;
    font-size: 21px;
    letter-spacing: 0.4px;
    color: var(--accent);
  }
  .brand p {
    margin: 4px 0 0;
    font-size: 13px;
    color: var(--muted);
  }
  .badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    background: var(--panel-alt);
    border: 1px solid var(--border);
  }
  .badge.safe { border-color: var(--green); color: var(--green); }
  .badge.gold { border-color: var(--accent); color: var(--accent); }
  nav {
    display: flex;
    gap: 8px;
    padding: 12px 28px;
    background: var(--panel);
    border-bottom: 1px solid var(--border);
    flex-wrap: wrap;
  }
  nav button {
    background: var(--panel-alt);
    color: var(--text);
    border: 1px solid var(--border);
    padding: 9px 16px;
    border-radius: 7px;
    cursor: pointer;
    font-weight: 600;
    font-size: 13px;
    transition: all 0.15s;
  }
  nav button.active, nav button:hover {
    background: var(--accent);
    color: #0b0d14;
    border-color: var(--accent);
  }
  main { padding: 22px 28px; max-width: 1520px; margin: 0 auto; }
  .grid-4 {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
    gap: 14px;
    margin-bottom: 20px;
  }
  .grid-2 {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(460px, 1fr));
    gap: 18px;
    margin-bottom: 20px;
  }
  .card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 18px;
  }
  .card h3 {
    margin: 0 0 12px;
    font-size: 15px;
    color: var(--accent);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .metric-val {
    font-size: 24px;
    font-weight: 700;
    margin: 6px 0 2px;
  }
  .metric-sub { font-size: 12px; color: var(--muted); }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }
  th, td {
    padding: 8px 10px;
    text-align: left;
    border-bottom: 1px solid var(--border);
  }
  th { color: var(--muted); font-weight: 600; font-size: 12px; text-transform: uppercase; }
  tr:hover td { background: rgba(245, 183, 49, 0.05); }
  .pill {
    padding: 3px 8px;
    border-radius: 5px;
    font-size: 11px;
    font-weight: 700;
  }
  .pill.ELITE { background: rgba(34, 197, 94, 0.18); color: var(--green); }
  .pill.SOLID { background: rgba(56, 189, 248, 0.18); color: var(--blue); }
  .pill.WEAK_LINK { background: rgba(249, 115, 22, 0.22); color: var(--warn); }
  .pill.OUT_OF_POSITION { background: rgba(239, 68, 68, 0.22); color: var(--danger); }
  .controls {
    display: flex;
    gap: 12px;
    align-items: center;
    flex-wrap: wrap;
    margin-bottom: 16px;
  }
  select, input[type="number"], input[type="text"] {
    background: var(--panel-alt);
    color: var(--text);
    border: 1px solid var(--border);
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 13px;
  }
  .btn {
    background: var(--accent);
    color: #0b0d14;
    border: none;
    padding: 8px 15px;
    border-radius: 6px;
    font-weight: 700;
    cursor: pointer;
    font-size: 13px;
  }
  .btn.secondary {
    background: var(--panel-alt);
    color: var(--text);
    border: 1px solid var(--border);
  }
  .tab-pane { display: none; }
  .tab-pane.active { display: block; }
  .alert-caution {
    border-left: 4px solid var(--danger);
    background: rgba(239, 68, 68, 0.1);
    padding: 14px 18px;
    border-radius: 8px;
    margin-bottom: 18px;
    font-size: 13.5px;
    line-height: 1.5;
  }
</style>
</head>
<body>
<header>
  <div class="brand">
    <h1>FM27 FUTBOL DİREKTÖRÜ (DoF) KOMUTA MERKEZİ</h1>
    <p id="subHeader">Yükleniyor...</p>
  </div>
  <div style="display:flex; gap:10px; align-items:center;">
    <span class="badge safe">CANLI OYUN GÜVENLİ (Salt-Okunur Analiz + İzole _DoF.fm Çıktısı)</span>
    <span class="badge gold" id="activeCoachBadge">Hoca: -</span>
  </div>
</header>
<nav>
  <button class="active" onclick="switchTab('hub', this)">1. Kulüp Bütçe & Maaş Tavanı (Capology)</button>
  <button onclick="switchTab('coaches', this)">2. Teknik Direktör Radarı & Felsefe Seçimi</button>
  <button onclick="switchTab('fit', this)">3. Hoca–Kadro Uyumu & Otonom İlk 11</button>
  <button onclick="switchTab('targets', this)">4. Hocanın Sistemine Göre Transfer Hedefleri</button>
  <button onclick="switchTab('final', this)">5. Hoca Atama (_DoF.fm) & Son Faz Rehberi</button>
</nav>
<main>
  <!-- TAB 1: HUB -->
  <div id="tab-hub" class="tab-pane active">
    <div class="grid-4" id="financeCards"></div>
    <div class="grid-2">
      <div class="card">
        <h3>En Yüksek Maaşlı Oyuncular & İlk 11 Durumu</h3>
        <table id="topEarnersTable">
          <thead><tr><th>Oyuncu</th><th>Yaş</th><th>CA/PA</th><th>Haftalık Maaş</th><th>Sözleşme</th><th>Statü</th><th>Hocanın 11'inde mi?</th></tr></thead>
          <tbody></tbody>
        </table>
      </div>
      <div class="card">
        <h3>Sözleşmesi Bitmek Üzere Olan Kritik Oyuncular (12-24 Ay)</h3>
        <table id="expiringTable">
          <thead><tr><th>Oyuncu</th><th>Yaş</th><th>CA</th><th>Kalan Ay</th><th>Bitiş</th><th>Haftalık Maaş</th><th>Serbest Kalma</th></tr></thead>
          <tbody></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- TAB 2: COACHES -->
  <div id="tab-coaches" class="tab-pane">
    <div class="card" style="margin-bottom:16px;">
      <h3>Futbol Direktörü Vizyonu: Hangi Oyun Felsefesinde Hoca Arıyorsun?</h3>
      <div class="controls">
        <label>Oyun Tarzı Felsefesi:</label>
        <select id="styleFilter">
          <option value="">Tüm Oyun Tarzları (En Yüksek DoF Puanı)</option>
          <option value="gegenpress">Gegenpress (Önde Şok Baskı)</option>
          <option value="tiki_taka">Tiki-Taka (Kısa Pas & Top Hakimiyeti)</option>
          <option value="vertical_tiki_taka">Dikey Tiki-Taka (Merkezden Hızlı Pas)</option>
          <option value="control_possession">Kontrollü Topa Sahip Olma</option>
          <option value="wing_play">Kanat Oyunu (Wing Play)</option>
          <option value="fluid_counter">Akıcı Kontra Atak</option>
          <option value="direct_counter">Direkt Kontra Atak</option>
          <option value="catenaccio">Catenaccio / Katı Savunma</option>
        </select>
        <label>Min CA:</label>
        <input type="number" id="minCaFilter" value="130" min="90" max="195" style="width:80px;"/>
        <button class="btn" onclick="loadCoaches()">Hocaları Tara</button>
      </div>
      <p style="margin:0; font-size:12.5px; color:var(--muted);">
        Not: Futbol Direktörü hocaya taktik dayatmaz. Seçtiğiniz hocanın kendi doğal oyun tarzı, dizilişi ve zihniyeti kadronuzla simüle edilir. Tablodan herhangi bir hocanın <b>"Kadroyu Simüle Et"</b> butonuna basarak o hocanın mevcut kadronuzdan çıkaracağı İlk 11'i ve isteyeceği transferleri görebilirsiniz.
      </p>
    </div>
    <div class="card">
      <h3>Aday Teknik Direktörler Sıralaması</h3>
      <table id="coachesTable">
        <thead>
          <tr>
            <th>#</th><th>Teknik Direktör</th><th>Yaş</th><th>Mevcut Kulüp</th><th>CA / PA</th>
            <th>Doğal Oyun Tarzı</th><th>Diziliş</th><th>Kadro Uyumu</th><th>Eksik Bölgeler</th>
            <th>Tahmini Tazminat</th><th>DoF Puanı</th><th>İşlem</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>
  </div>

  <!-- TAB 3: SQUAD FIT -->
  <div id="tab-fit" class="tab-pane">
    <div class="grid-4" id="fitSummaryCards"></div>
    <div class="grid-2">
      <div class="card">
        <h3 id="xiTitle">Hocanın Otonom İlk 11 Seçimi</h3>
        <table id="xiTable">
          <thead><tr><th>Mevki</th><th>Rol (Top Bizdeyken)</th><th>Oyuncu</th><th>CA</th><th>Mevki</th><th>Stil DNA</th><th>Uyum</th><th>Durum</th></tr></thead>
          <tbody></tbody>
        </table>
      </div>
      <div>
        <div class="card" style="margin-bottom:16px;">
          <h3>Hocanın Futbol Direktöründen İstediği Öncelikli Transfer Bölgeleri</h3>
          <table id="needsTable">
            <thead><tr><th>Mevki</th><th>İstenen Rol</th><th>Mevcut Oyuncu</th><th>Aciliyet</th><th>Gerekçe</th></tr></thead>
            <tbody></tbody>
          </table>
        </div>
        <div class="card">
          <h3>Hocanın Sisteminde Kadro Dışı / Kiralık / Satış Adayları</h3>
          <table id="surplusTable">
            <thead><tr><th>Oyuncu</th><th>Yaş</th><th>CA/PA</th><th>Maaş</th><th>Stil DNA</th><th>DoF Karar Önerisi</th></tr></thead>
            <tbody></tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <!-- TAB 4: TRANSFER TARGETS -->
  <div id="tab-targets" class="tab-pane">
    <div class="card" style="margin-bottom:16px;">
      <h3>Hocanın Oyun Tarzına ve Eksik Bölgelerine Göre Scout Hedefleri</h3>
      <div class="controls">
        <label>Maksimum Bonservis Değeri:</label>
        <input type="number" id="maxValFilter" value="35000000" step="5000000" style="width:140px;"/>
        <button class="btn" onclick="loadTargets()">Transfer Hedeflerini Yenile</button>
      </div>
    </div>
    <div id="slotTargetsContainer" class="grid-2"></div>
    <div class="grid-2">
      <div class="card">
        <h3>Hocanın Sistemine Uygun Wonderkid Adayları (≤21 Yaş)</h3>
        <table id="wonderkidsTable">
          <thead><tr><th>Oyuncu</th><th>Yaş</th><th>Kulüp</th><th>Mevki</th><th>CA / PA</th><th>Değer</th><th>Stil DNA</th><th>Hedef Puanı</th></tr></thead>
          <tbody></tbody>
        </table>
      </div>
      <div class="card">
        <h3>Sözleşmesi Son Yılına Giren Fırsat Transferleri (≤12 Ay)</h3>
        <table id="bargainsTable">
          <thead><tr><th>Oyuncu</th><th>Yaş</th><th>Kulüp</th><th>Mevki</th><th>CA / PA</th><th>Kalan Ay</th><th>Değer</th><th>Hedef Puanı</th></tr></thead>
          <tbody></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- TAB 5: HIRE COACH & FINAL PHASE -->
  <div id="tab-final" class="tab-pane">
    <div class="alert-caution">
      <b>⚠️ DİKKAT — SON FAZ UYARISI (OYUN AÇIKKEN DİKKAT EDİLECEKLER):</b><br/>
      1. Şu an FM27 açıkken yaptığınız tüm analizler <b>%100 güvenlidir</b> ve çalışan oyuna dokunmaz.<br/>
      2. Aşağıdaki <b>"Yeni _DoF.fm Kaydı Üret"</b> butonu, orijinal kaydınızın üzerine <b>ASLA yazmaz</b>; yanına yeni bir <code>*_DoF.fm</code> dosyası oluşturur.<br/>
      3. Üretilen yeni <code>*_DoF.fm</code> kaydını oyunda açmak istediğinizde: önce FM27'de mevcut oyununuzu kaydedin, ardından <b>Load Game (Oyun Yükle)</b> ekranından üretilen <code>*_DoF.fm</code> dosyasını yükleyin.
    </div>
    <div class="grid-2">
      <div class="card">
        <h3>Teknik Direktör Atama & Otonom Kadro/Taktik Kurulumu</h3>
        <p style="font-size:13px; color:var(--muted);">
          Seçtiğiniz teknik direktörü kulübünüze atar, tazminatını bütçeden düşer ve hocanın doğal taktik felsefesini, zihniyetini ve 26 kişilik kadro seçimini yeni bir <code>_DoF.fm</code> dosyasına yazar.
        </p>
        <div class="controls" style="flex-direction:column; align-items:stretch;">
          <label>Atanacak Teknik Direktör (UID veya İsim):</label>
          <input type="text" id="hireCoachInput" placeholder="Örn: Okan Buruk veya 2. sekmeden seçilen hoca"/>
          <label>Sözleşme Süresi (Yıl):</label>
          <input type="number" id="hireYearsInput" value="3" min="1" max="5"/>
          <label>Çıktı Dosyası Yolu (Orijinal kaydın üzerine yazmaz):</label>
          <input type="text" id="hireOutPathInput" value=""/>
          <button class="btn" onclick="executeHireCoach()" style="margin-top:8px; padding:12px;">Yeni _DoF.fm Kaydı Oluştur</button>
        </div>
        <pre id="hireResultBox" style="background:var(--bg); padding:12px; border-radius:8px; font-size:12px; overflow:auto; max-height:260px; display:none;"></pre>
      </div>
      <div class="card">
        <h3>Oyun İçi Futbol Direktörü (DoF) Sorumluluk Rehberi</h3>
        <table>
          <thead><tr><th>Sorumluluk Alanı</th><th>Kimde Olmalı?</th><th>FM27 Menüsü</th></tr></thead>
          <tbody>
            <tr><td>Transfer Gelen / Giden Teklifler & Kontratlar</td><td><span class="pill ELITE">SİZDE (Futbol Direktörü)</span></td><td>Staff &gt; Responsibilities &gt; Transfers</td></tr>
            <tr><td>Teknik Direktör & Gözlemci Atamaları</td><td><span class="pill ELITE">SİZDE (Futbol Direktörü)</span></td><td>Staff &gt; Responsibilities &gt; Staff</td></tr>
            <tr><td>Scout Görevlendirmeleri & Kısa Listeler</td><td><span class="pill ELITE">SİZDE (Futbol Direktörü)</span></td><td>Staff &gt; Responsibilities &gt; Scouting</td></tr>
            <tr><td>A Takım Antrenmanları & Bireysel Gelişim</td><td><span class="pill SOLID">BAŞANTRENÖR / ASİSTAN</span></td><td>Staff &gt; Responsibilities &gt; Training</td></tr>
            <tr><td>Basın Toplantıları & Medya Görüşmeleri</td><td><span class="pill SOLID">BAŞANTRENÖR / ASİSTAN</span></td><td>Staff &gt; Responsibilities &gt; Media</td></tr>
            <tr><td>Maç Günü (90 Dk) & Takım Konuşmaları</td><td><span class="pill SOLID">Instant Result (Hocanın Maç Planı)</span></td><td>Maç Öncesi &gt; Instant Result</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</main>

<script>
let currentCoachQuery = "";

function fmtMoney(n) {
  if (n === null || n === undefined) return "-";
  return "€" + Number(n).toLocaleString("tr-TR");
}

function switchTab(name, btn) {
  document.querySelectorAll(".tab-pane").forEach(el => el.classList.remove("active"));
  document.querySelectorAll("nav button").forEach(el => el.classList.remove("active"));
  document.getElementById("tab-" + name).classList.add("active");
  if (btn) btn.classList.add("active");
}

async function loadDashboard(coachQuery = "") {
  currentCoachQuery = coachQuery;
  const url = "/api/dashboard" + (coachQuery ? "?coach=" + encodeURIComponent(coachQuery) : "");
  const res = await fetch(url);
  const data = await res.json();

  const info = data.save_info;
  document.getElementById("subHeader").textContent =
    `${info.club_name} (UID: ${info.club_uid}) | Tarih: ${info.game_date} | Sürüm: ${info.game} (${info.build})`;

  const fit = data.coach_squad_fit;
  const coach = fit.coach;
  document.getElementById("activeCoachBadge").textContent =
    `Simüle Edilen Hoca: ${coach.name} (${coach.primary_style_tr} • ${fit.formation})`;
  document.getElementById("hireCoachInput").value = coach.name;
  if (!document.getElementById("hireOutPathInput").value && data.default_out_path) {
    document.getElementById("hireOutPathInput").value = data.default_out_path;
  }

  const fin = data.finances;
  document.getElementById("financeCards").innerHTML = `
    <div class="card"><h3>Kulüp Kasası (Balance)</h3><div class="metric-val">${fmtMoney(fin.balance)}</div><div class="metric-sub">Net Kulüp Bakiyesi</div></div>
    <div class="card"><h3>Kalan Transfer Bütçesi</h3><div class="metric-val" style="color:var(--green)">${fmtMoney(fin.transfer_budget_remaining)}</div><div class="metric-sub">Tahsis: ${fmtMoney(fin.transfer_budget_allocated)}</div></div>
    <div class="card"><h3>Haftalık Maaş Bütçesi</h3><div class="metric-val">${fmtMoney(fin.wage_budget_weekly)}/hf</div><div class="metric-sub">Harcanan: ${fmtMoney(fin.wage_payroll_weekly)}/hf</div></div>
    <div class="card"><h3>Boş Maaş Limiti</h3><div class="metric-val" style="color:${fin.wage_free_weekly >= 0 ? 'var(--blue)' : 'var(--danger)'}">${fmtMoney(fin.wage_free_weekly)}/hf</div><div class="metric-sub">Yıllık Boşluk: ${fmtMoney(fin.wage_free_weekly * 52)}</div></div>
  `;

  const teBody = document.querySelector("#topEarnersTable tbody");
  teBody.innerHTML = data.capology.top_earners.map(p => `
    <tr>
      <td><b>${p.name}</b></td><td>${p.age || '-'}</td><td>${p.ca} / ${p.pa}</td>
      <td>${fmtMoney(p.wage_weekly)}/hf</td><td>${p.contract_end || '-'} (${p.months_left} ay)</td>
      <td>${p.squad_status}</td>
      <td><span class="pill ${p.in_coach_starting_xi ? 'ELITE' : 'WEAK_LINK'}">${p.in_coach_starting_xi ? 'İLK 11' : 'YEDEK/ROTASYON'}</span></td>
    </tr>
  `).join("");

  const expList = [...data.capology.expiring_12m, ...data.capology.expiring_24m];
  const exBody = document.querySelector("#expiringTable tbody");
  exBody.innerHTML = expList.map(p => `
    <tr>
      <td><b>${p.name}</b></td><td>${p.age || '-'}</td><td>${p.ca}</td>
      <td><span class="pill ${p.months_left <= 12 ? 'OUT_OF_POSITION' : 'WEAK_LINK'}">${p.months_left} ay</span></td>
      <td>${p.contract_end || '-'}</td><td>${fmtMoney(p.wage_weekly)}/hf</td>
      <td>${p.release_clause ? fmtMoney(p.release_clause) : '-'}</td>
    </tr>
  `).join("");

  renderSquadFit(fit);
}

function renderSquadFit(fit) {
  const c = fit.coach;
  document.getElementById("fitSummaryCards").innerHTML = `
    <div class="card"><h3>Simüle Edilen Hoca</h3><div class="metric-val" style="font-size:19px;">${c.name}</div><div class="metric-sub">CA: ${c.current_ability} | ${c.role_tr} (${c.club_name})</div></div>
    <div class="card"><h3>Hocanın Doğal Oyun Tarzı</h3><div class="metric-val" style="font-size:18px; color:var(--accent)">${c.primary_style_tr}</div><div class="metric-sub">Diziliş: ${fit.formation} | Zihniyet: ${c.mentality_label_tr}</div></div>
    <div class="card"><h3>Genel Kadro Uyumu</h3><div class="metric-val" style="color:var(--green)">%${fit.overall_compatibility}</div><div class="metric-sub">Diziliş Uyumu: %${fit.formation_coverage_score} | Stil DNA: %${fit.style_dna_score}</div></div>
    <div class="card"><h3>İlk 11 Kalite Ortalaması</h3><div class="metric-val">${fit.starting_xi_avg_ca} CA</div><div class="metric-sub">Gençlere Güven: ${c.youth_trust_score}/100 | Taktik: ${c.tactical_score}/100</div></div>
  `;
  document.getElementById("xiTitle").textContent = `${c.name} — Otonom İlk 11 (${fit.formation} • ${c.primary_style_tr})`;
  document.querySelector("#xiTable tbody").innerHTML = fit.starting_xi.map(s => `
    <tr>
      <td><b>${s.slot_code}</b> <span style="color:var(--muted);font-size:11px;">(${s.slot_label_tr})</span></td>
      <td>${s.ip_role_tr}</td>
      <td><b>${s.player_name}</b> (${s.age})</td>
      <td>${s.ca}</td><td>${s.pos_rating}/20</td><td>${s.style_dna_score}</td><td><b>${s.slot_fit_score}</b></td>
      <td><span class="pill ${s.status}">${s.status}</span></td>
    </tr>
  `).join("");

  document.querySelector("#needsTable tbody").innerHTML = fit.priority_transfer_needs.map(n => `
    <tr>
      <td><b>${n.slot_code}</b> (${n.slot_label_tr})</td>
      <td>${n.required_role_tr}</td>
      <td>${n.current_starter} (CA ${n.current_starter_ca})</td>
      <td><span class="pill ${n.urgency === 'KRİTİK' ? 'OUT_OF_POSITION' : 'WEAK_LINK'}">${n.urgency}</span></td>
      <td>${n.reason_tr}</td>
    </tr>
  `).join("");

  document.querySelector("#surplusTable tbody").innerHTML = fit.surplus_candidates.map(s => `
    <tr>
      <td><b>${s.player_name}</b></td><td>${s.age || '-'}</td><td>${s.ca}/${s.pa}</td>
      <td>${fmtMoney(s.wage_weekly)}/hf</td><td>${s.style_dna_score}</td>
      <td><span class="pill WEAK_LINK">${s.action_tr}</span></td>
    </tr>
  `).join("");
}

async function loadCoaches() {
  const style = document.getElementById("styleFilter").value;
  const minCa = document.getElementById("minCaFilter").value || 130;
  const res = await fetch(`/api/coaches?style=${encodeURIComponent(style)}&min_ca=${minCa}`);
  const data = await res.json();
  document.querySelector("#coachesTable tbody").innerHTML = data.candidates.map(c => `
    <tr>
      <td><b>#${c.rank}</b></td>
      <td><b>${c.profile.name}</b></td>
      <td>${c.profile.age || '-'}</td>
      <td>${c.profile.club_name}</td>
      <td><b>${c.profile.current_ability}</b> / ${c.profile.potential_ability}</td>
      <td><span class="pill SOLID">${c.profile.primary_style_tr}</span></td>
      <td><b>${c.profile.preferred_formation}</b></td>
      <td><b>%${c.squad_compatibility}</b></td>
      <td style="font-size:12px; color:var(--muted);">${c.weak_positions_summary}</td>
      <td>${fmtMoney(c.estimated_compensation)}</td>
      <td><b style="color:var(--accent)">${c.dof_total_score}</b></td>
      <td>
        <button class="btn secondary" onclick="simulateCoach('${c.profile.staff_uid}')">Kadroyu Simüle Et</button>
      </td>
    </tr>
  `).join("");
}

async function simulateCoach(staffUid) {
  await loadDashboard(staffUid);
  await loadTargets();
  const btns = document.querySelectorAll("nav button");
  switchTab("fit", btns[2]);
}

async function loadTargets() {
  const maxVal = document.getElementById("maxValFilter").value || 35000000;
  const url = `/api/targets?max_val=${maxVal}` + (currentCoachQuery ? `&coach=${encodeURIComponent(currentCoachQuery)}` : "");
  const res = await fetch(url);
  const data = await res.json();

  document.getElementById("slotTargetsContainer").innerHTML = data.slots.map(sl => `
    <div class="card">
      <h3>${sl.slot_code} (${sl.slot_label_tr}) — İstenen Rol: ${sl.ip_role_tr} <span style="font-size:12px;color:var(--muted);">Mevcut: ${sl.current_starter} (${sl.current_starter_ca} CA)</span></h3>
      <table>
        <thead><tr><th>Hedef Oyuncu</th><th>Yaş</th><th>Kulüp</th><th>CA/PA</th><th>Değer</th><th>Maaş</th><th>Stil DNA</th><th>Uyum</th></tr></thead>
        <tbody>
          ${sl.targets.map(t => `
            <tr>
              <td><b>${t.name}</b></td><td>${t.age}</td><td>${t.club_name}</td>
              <td><b>${t.ca}</b>/${t.pa} <span style="color:var(--green);font-size:11px;">(${t.upgrade_vs_starter_ca >= 0 ? '+' + t.upgrade_vs_starter_ca : t.upgrade_vs_starter_ca})</span></td>
              <td>${fmtMoney(t.transfer_value)}</td><td>${fmtMoney(t.wage_weekly)}/hf</td>
              <td>${t.style_dna_score}</td><td><b style="color:var(--accent)">${t.target_score}</b></td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `).join("");

  document.querySelector("#wonderkidsTable tbody").innerHTML = data.wonderkids.map(w => `
    <tr>
      <td><b>${w.name}</b></td><td>${w.age}</td><td>${w.club_name}</td><td>${w.slot_code}</td>
      <td>${w.ca} / <b>${w.pa}</b></td><td>${fmtMoney(w.transfer_value)}</td><td>${w.style_dna_score}</td><td><b>${w.target_score}</b></td>
    </tr>
  `).join("");

  document.querySelector("#bargainsTable tbody").innerHTML = data.expiring_bargains.map(b => `
    <tr>
      <td><b>${b.name}</b></td><td>${b.age}</td><td>${b.club_name}</td><td>${b.slot_code}</td>
      <td><b>${b.ca}</b> / ${b.pa}</td><td><span class="pill OUT_OF_POSITION">${b.months_left} ay</span></td>
      <td>${fmtMoney(b.transfer_value)}</td><td><b>${b.target_score}</b></td>
    </tr>
  `).join("");
}

async function executeHireCoach() {
  const coach = document.getElementById("hireCoachInput").value.trim();
  const years = Number(document.getElementById("hireYearsInput").value || 3);
  const outPath = document.getElementById("hireOutPathInput").value.trim();
  const box = document.getElementById("hireResultBox");
  box.style.display = "block";
  box.textContent = "Yeni _DoF.fm kaydı oluşturuluyor, lütfen bekleyin...";
  const res = await fetch("/api/hire", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({coach, years, out_path: outPath})
  });
  const data = await res.json();
  box.textContent = JSON.stringify(data, null, 2);
}

window.addEventListener("DOMContentLoaded", async () => {
  await loadDashboard();
  await loadCoaches();
  await loadTargets();
});
</script>
</body>
</html>
"""


def serve_dof_dashboard(
    save_path: str | Path,
    *,
    club_uid: int | None = None,
    host: str = "127.0.0.1",
    port: int = 8765,
    open_browser: bool = True,
) -> None:
    """Launch the local interactive FM27 Director of Football (DoF) Web Command Center."""
    resolved_save = Path(save_path).resolve()
    save = FM26Save(resolved_save)
    default_out = str(resolved_save.with_name(f"{resolved_save.stem}_DoF.fm"))

    class DoFRequestHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return

        def _send_json(self, payload: Any, status: int = 200) -> None:
            raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self) -> None:  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)

            if parsed.path in ("/", "/index.html"):
                raw = DOF_HTML_TEMPLATE.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
                return

            if parsed.path == "/api/dashboard":
                coach_q = qs.get("coach", [None])[0]
                c_arg: int | str | None = int(coach_q) if (coach_q and coach_q.isdigit()) else coach_q
                data = build_dof_dashboard(save, club_uid=club_uid, coach_uid_or_name=c_arg)
                data["default_out_path"] = default_out
                self._send_json(data)
                return

            if parsed.path == "/api/coaches":
                style = qs.get("style", [None])[0] or None
                min_ca = int(qs.get("min_ca", ["125"])[0])
                cands = scan_coach_candidates(
                    save,
                    club_uid=club_uid,
                    desired_style=style,
                    min_ca=min_ca,
                    top_n=25,
                )
                self._send_json({
                    "styles": {k: v.name_tr for k, v in FM27_TACTICAL_STYLES.items()},
                    "candidates": [c.to_dict() for c in cands],
                })
                return

            if parsed.path == "/api/targets":
                coach_q = qs.get("coach", [None])[0]
                c_arg = int(coach_q) if (coach_q and coach_q.isdigit()) else coach_q
                max_val = int(qs.get("max_val", ["35000000"])[0])
                data = recommend_transfer_targets(
                    save,
                    club_uid=club_uid,
                    coach_uid_or_name=c_arg,
                    max_transfer_value=max_val,
                )
                self._send_json(data)
                return

            self._send_json({"error": "Not found"}, status=404)

        def do_POST(self) -> None:  # noqa: N802
            if self.path == "/api/hire":
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                coach_q = body.get("coach")
                c_arg: int | str = int(coach_q) if (isinstance(coach_q, str) and coach_q.isdigit()) else str(coach_q)
                years = int(body.get("years", 3))
                out_path = body.get("out_path") or default_out
                try:
                    res = hire_head_coach(
                        resolved_save,
                        c_arg,
                        out_path,
                        club_uid=club_uid,
                        contract_years=years,
                    )
                    self._send_json(res)
                except Exception as exc:
                    self._send_json({"error": str(exc)}, status=400)
                return
            self._send_json({"error": "Not found"}, status=404)

    server = HTTPServer((host, port), DoFRequestHandler)
    url = f"http://{host}:{port}"
    print(f"FM27 Futbol Direktörü (DoF) Komuta Merkezi çalışıyor: {url}")
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        save.close()
