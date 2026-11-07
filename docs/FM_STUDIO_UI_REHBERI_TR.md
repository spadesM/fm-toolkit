# FM27 / FM26 Studio — Tümleşik Veritabanı, Optimizasyon, Yama ve 21 Dilli Lokalizasyon Komuta Merkezi Rehberi

Bu döküman, `fm26save` projesinin tüm tersine mühendislik, ikili ayrıştırma, veritabanı düzenleme, oyun optimizasyonu ve UI/DLL yamalama yeteneklerini tek bir profesyonel web arayüzünde birleştiren **FM Studio Komuta Merkezi** (`fm26save/studio.py`, `fm26save/studio_ui.py`, `fm26save/game_localization.py`, `fm26save/game_optimizer.py` ve `fm26save/ui_patches.py`) mimarisini ve kullanımını açıklar.

---

## 1. Hızlı Başlangıç

FM Studio arayüzünü tek komutla başlatabilirsiniz:

```bash
python -m fm26save.cli studio
# veya belirli bir save dosyası ve port ile:
python -m fm26save.cli studio --save "Mahmut Çakar - Galatasaray.fm" --port 8780
```

Komut çalıştırıldığında yerel sunucu (`http://127.0.0.1:8780/`) başlatılır ve varsayılan tarayıcınızda otomatik olarak açılır:
- Bilgisayarınızdaki `AppData/Local/Sports Interactive/Football Manager 27`, `Football Manager 26`, `Documents/Sports Interactive` ve çalışma dizinindeki tüm `.fm` kayıt dosyaları otomatik olarak keşfedilir.
- Steam kütüphanenizdeki **Football Manager 27** ve **Football Manager 26** kurulum dizinleri otomatik olarak algılanır.

---

## 2. Bağımsız Çift Katmanlı Lokalizasyon Sistemi (UI Dili vs. 21 Oyun İçi Terim Dili)

FM Studio'nun üst komut çubuğunda birbirinden **tamamen bağımsız** iki ayrı dil seçici bulunur:

1. **🌐 Arayüz Dili (`UI Language`: `Türkçe (TR)` / `English (EN)`)**:
   - Yalnızca Studio uygulamasının kendi menülerini, sekme başlıklarını ve kontrol etiketlerini değiştirir.
2. **🎯 Oyun İçi Terim Dili (`In-Game Term Language`: 21 Resmi FM `.ltc` Dili)**:
   - `data/game_simulation/languages.fmf` içindeki **21 resmi `.ltc` dil dosyasının** (`turkish.ltc`, `english.ltc`, `german.ltc`, `spanish.ltc`, `french.ltc`, `italian.ltc`, `portuguese.ltc`, `dutch.ltc`, `polish.ltc`, `greek.ltc`, `russian.ltc`, `arabic.ltc`, `danish.ltc`, `norwegian.ltc`, `swedish.ltc`, `indonesian.ltc`, `japanese.ltc`, `korean.ltc`, `chinese.ltc`, `english (us).ltc`, `spanish (latam).ltc`) ikili `(uint32 string_id, uint32 payload_offset)` indeks tabloları çözülerek [`fm26save/game_localization.py`](../fm26save/game_localization.py) modülüne gömülmüştür.
   - Bu sayede kullanıcı **arayüzü İngilizce (`EN`) kullanırken bile** Oyun İçi Terim Dili olarak **Türkçe (`turkish`)** seçtiğinde; oyuncu özellikleri (`Finishing` $\rightarrow$ `Bitiricilik` (`Bit`), `Pace` $\rightarrow$ `Hız`, `Vision` $\rightarrow$ `Vizyon`, `Off The Ball` $\rightarrow$ `Topsuz Alan`), personel özellikleri (`Judging Player Ability` $\rightarrow$ `Oyuncu Yeteneği Değerlendirme`), mevkiler (`GK` $\rightarrow$ `KL`, `ST` $\rightarrow$ `SNT`) ve kadro statüleri (`Star Player` $\rightarrow$ `Yıldız Oyuncu`) seçilen oyun içi dilde görüntülenir!

| String ID (`hex`) | Kanonik Anahtar | English (`english.ltc`) | Türkçe (`turkish.ltc`) | Deutsch (`german.ltc`) | Español (`spanish.ltc`) | 日本語 (`japanese.ltc`) |
|---|---|---|---|---|---|---|
| `0x100379E2` | `finishing` | Finishing (`Fin`) | Bitiricilik (`Bit`) | Abschluss | Remate | 決定力 |
| `0x10037A27` | `pace` | Pace (`Pac`) | Hız (`Hız`) | Schnelligkeit | Velocidad | スピード |
| `0x10037A29` | `passing` | Passing (`Pas`) | Pas (`Pas`) | Passen | Pase | パス |
| `0x10038287` | `vision` | Vision | Vizyon | Übersicht | Visión | 視野 |
| `0x10037A25` | `off_the_ball` | Off The Ball (`Off`) | Topsuz Alan (`Tza`) | Ohne Ball | Desmarques | オフザボール |
| `0x1003827A` | `leadership` | Leadership | Liderlik | Führungsqualitäten | Liderazgo | 統率力 |
| `0x10037A69` | `judging_player_ability` | Judging Player Ability | Oyuncu Yeteneği Değerlendirme | Spielerfähigkeiten beurteilen | Juzgar calidad | 選手能力判定 |
| `0x100A7011` | `pos_gk` | GK | KL | TW | Por | GK |
| `0x100A7006` | `pos_st` | ST | SNT | ST | DL | ST |

---

## 3. Üç Ana Kalem (3 Core Pillars) Mimarisi

### Kalem 1 — Tüm Veritabanları Görselleştirme ve Canlı Düzenleme (`Save .fm` + `Pre-Game Kurulum DB`)
1. **⚽ Oyuncu Merkezi & Canlı Özellik Editörü**:
   - Save içindeki tüm oyuncuları isim, UID, uyruk, kulüp, mevki (`GK..ST`) ve minimum CA kriterlerine göre anlık filtreleme ve sıralama.
   - Seçilen oyuncunun **47 özelliğini** (`14 Teknik`, `14 Zihinsel`, `8 Fiziksel`, `11 Kalecilik`) + `13 Gizli/Kişilik` özelliğini (`Süreklilik`, `Önemli Maçlar`, `Sakatlanma Eğilimi`, `Çok Yönlülük`, `Hırs`, `Profesyonellik`, `Baskıya Dayanıklılık`, vb.) seçilen **Oyun İçi Terim Dilinde** ve FM kademe renkleriyle (`16-20` Yeşil, `11-15` Mavi, `6-10` Sarı, `1-5` Gri) görüntüleme ve canlı düzenleme (`1..20`).
   - **CA / PA (`1..200`)**, İtibar, Yaş, Boy, Kondisyon, Piyasa Değeri (`€`), Haftalık Maaş (`€/h`), Sözleşme Bitiş Tarihi ve **14 Mevki Hakimiyeti (`GK..ST` `1..20`)** düzenleme.
   - Oyuncunun en uygun **Topa Sahipken (`IP`)** ve **Top Rakipteyken (`OOP`)** taktiksel rol uygunluk puanları.
   - Tek tıkla **⚡ Max 200 / 20**, **🏥 Sakatlıkları İyileştir & Cezaları Sil** ve **💾 Save Dosyasına Yaz (`.fm`)**.
2. **🏛️ Kulüpler, Finans, Stadyumlar & Oyun Tarihi Editörü**:
   - Kulüplerin **Banka Bakiyesi (`Balance`)**, **Transfer Bütçesi (`Transfer Budget`)**, **Haftalık Maaş Bütçesi (`Wage Budget`)**, **Kulüp İtibarı (`1..10000`)** ve **Kurumsal Tesis (`1..20`)** değerlerini canlı düzenleme (+ tek tıkla `+250M € Transfer Bütçesi & 500M € Bakiye` hazır butonu).
   - Stadyumların toplam ve koltuklu kapasitelerini ve aktif oyun tarihini (`YYYY-MM-DD`) düzenleme.
3. **👔 Teknik Heyet (`Staff`), 26 Gizli Özellik & Futbol Direktörü (`DoF`)**:
   - Menajer, antrenör, gözlemci ve fizyoterapistlerin CA/PA değerlerini ve `block_40` içindeki **26 gizli personel özelliğini** seçilen oyun içi dilde inceleme, **⚡ Max 200 Personel** yapma veya **🤝 Kulübe Teknik Direktör Ata (`hire_head_coach`)** aksiyonu ile kulübün başına getirme.
4. **📊 Tüm 28 Save Tablosu & 81 Ham Bölüm (`Container Sections`) Gezgini**:
   - 28 yapılandırılmış tablonun ve ekstra bölümlerin (`hall_of_fame`, `takeovers`, `shortlists`, `offers`, `agents`, `news`) tamamını tablo görünümünde arama ve 81 Zstd konteyner bölümünün sıkıştırma istatistiklerini inceleme.
5. **🗄️ Oyun İçi Kurulum Veritabanları (`Pre-Game Installation DBs`: `2700` / `2620`)**:
   - `basic_people_db.dat` / `people_db.dat` (`723.010+` kişi, `-10` ve `-95` Wonderkid potansiyel dağılımı), `client_db.dat` / `server_db.dat` (`96.343` kulüp, `58.349` şehir, `51.118` stadyum, `7.973` turnuva) ve `2300..2700` çoklu veritabanı sürüm evrimini görselleştirme.

---

### Kalem 2 — Oyun Optimizasyon Merkezi (`fm26save/game_optimizer.py`)
1. **🚀 Unity Motoru `fm_Data/boot.config` Performans & Çok Çekirdek Ayarlayıcı**:
   - Donanımınızdaki mantıksal CPU çekirdek sayısını otomatik algılar ve en uygun `job-worker-count` değerini önerir.
   - **Tek Tık Hazır Performans Profilleri**:
     - `⚡ Maksimum FPS & Çok Çekirdek (max_fps_multicore)`
     - `⚖️ Dengeli (balanced)`
     - `🎯 Düşük Mikro-Takılma / Akıcı UI (low_latency)`
     - `↩️ Yedekten Dön (boot.config.bak)`
   - Düzenlenebilir anahtarlar: `gfx-enable-gfx-jobs`, `gfx-enable-native-gfx-jobs`, `gfx-threading-mode`, `gc-max-time-slice`, `job-worker-count`, `vr-enabled`, `wait-for-native-debugger`, `hdr-display-enabled`, `call-ondisable-when-unloaded-from-bundles`.
2. **🎬 Açılış & Tanıtım Video Bundle'ları (`videos_*.bundle` / `promobanner_*.bundle`) Atlama**:
   - Tek tıkla video/tanıtım paketlerini `.disabled` olarak işaretleyip oyun açılışını hızlandırma veya tekrar etkinleştirme.
3. **🎨 URP Grafik Pipeline Profilleri (`HighFidelity`, `Balanced`, `Performant`) ve Kurulum DB (`2300..2700`) Disk Ayak İzi Analizi**.

---

### Kalem 3 — Oyun Dosyaları, İkili/Bundle Yamaları ve Kural (`.edt`/`.lnc`/`.dbc`) Düzenleyici
1. **🎯 50 Oyuncu Gözlemleme Sınırı Yaması (`scout-player-limit` — `game_plugin.dll`)**:
   - `EvaluateScoutPlayersAction` (`VA 0x180FDEBD4: cmp rcx, (N+1)*8`) içindeki 50 oyuncu sınırını arayüzdeki sayı kutusundan veya hızlı butonlardan (`500`, `2.500`, `5.000`, `15.000`) istediğiniz değere tek tıkla yükseltir veya `.bak` yedeğinden orijinal 50 sınırına döndürür.
2. **📊 Hazır 10 UI Tablo Sıralama Yaması (`StreamedTable.DisableSorting = 1 → 0`)**:
   - `scout-priorities-sorting`: Gözlemcilik > Gözlemci Öncelikleri tablosu
   - `dof-transfer-targets-sorting`: Futbol Direktörü (DoF) > Transfer Hedefleri ana tablosu
   - `dof-transfer-targets-global-sorting`: Futbol Direktörü (DoF) > Transfer Hedefleri global bloğu
   - `set-piece-takers-sorting`: Taktikler > Duran Top Kullanıcıları (`StreamedTable_TakersList`)
   - `penalty-takers-sorting`: Taktikler > Penaltı Kullanıcıları (`SetPiecePenaltyTakersTable`)
   - `contract-similar-players-sorting`: Sözleşme > Benzer Süre Alan Oyuncular (`TablePlayersWithSimilarPlayingTime`)
   - `club-all-staff-sorting`: Kulüp > Tüm Personel / Görev Listesi (`StreamedTable_JobsList`)
   - `squad-planner-sorting`: Kadro Planlayıcı (`RecruitmentSquadPlannerTableBlock`)
   - `team-reserves-compact-sorting`: Takım > Yedek / Alt Kadro Kompakt tablosu
   - `welcome-pack-best-xi-sorting`: Kulüp Karşılama Paketi > En İyi 11 (`WelcomePackBestXIBlock`)
3. **🔓 Tüm 252 `DisableSorting = 1` (`StreamedTable`) Derin Tablo Tarayıcısı ve Kilit Açıcı**:
   - Oyun içindeki 5 `VisualTreeAsset` preload bundle dosyasını tarayarak `DisableSorting = 1` olan **252 tablonun tamamını** listeler ve istediğiniz herhangi bir tabloda tek tıkla sıralamayı açmanıza (`1 -> 0`) veya kapatmanıza (`0 -> 1`) olanak tanır.
4. **👑 Görsel Zengin Başkan (`sugardaddy.edt`) & Gerçek Lisans (`.dbc` / `.lnc` / `.edt`) Editörü**:
   - `sugardaddy.edt` içindeki kulüpleri görsel tabloda düzenleme ve **istediğiniz kulübü (örn. Galatasaray, Fenerbahçe, Beşiktaş, Trabzonspor) tek tıkla `FRONT_END` / `BACK_END` / `UNDERWRITER` zengin başkan listesine ekleme**.
   - `germany.dbc`, `japan_fake.dbc`, `1_japan_removed_clubs.dbc`, `licensing_fm27.dbc`, `Licensing2.dbc`, `brazil_kits.dbc`, `fm_27_italy_kits.dbc`, `fake.lnc`, `fake.edt` gibi 38 lisans ve kural dosyasını tek tıkla etkinleştirme/devre dışı bırakma ve `.edt`/`.ddt`/`.lnc` dosyalarını UTF-16LE / UTF-8 kodlamasını koruyarak canlı metin editöründe düzenleme.
