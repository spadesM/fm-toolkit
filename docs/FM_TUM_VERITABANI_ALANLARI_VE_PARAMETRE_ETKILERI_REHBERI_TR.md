# Football Manager (FM26 / FM27) Tüm Veritabanı Tabloları, Kolonları ve Parametrelerin Oyun Motoru Etkileri Rehberi

Bu doküman; [`fm26save`](../fm26save/__init__.py) kod tabanındaki tüm ikili (`.fm` / `.dat`) çözücüler, [`formulas.py`](../fm26save/formulas.py), [`constants.py`](../fm26save/constants.py), [`dof.py`](../fm26save/dof.py), [`game_files.py`](../fm26save/game_files.py) ve doğrudan oyun motoru arşivleri (`editor.fmf`, `tables.fmf`, `simatch.fmf`, `simatchviewer-pc.fmf`, `QuickMatchEngine.fmf`, `training.fmf`) taranarak hazırlanmıştır.

Veritabanındaki **28 kayıtlı oyun (`.fm` save) tablosu**, **81/75 `.dat` konteyner bölümü** ve **33 ana veritabanı (`editor.fmf`) şemasındaki** her bir kolonun/parametrenin oyun motorunda **tam olarak hangi alt sistemlere dokunduğu, hangi katsayılarla çarpıldığı ve ne işe yaradığı** eksiksiz olarak belgelenmiştir. Tekrara düşmemek adına birden fazla kolonun ortaklaşa girdiği ana motor denklemleri **Bölüm 1 (`[REF-*]`)** altında toplanmış ve kolon açıklamalarından doğrudan bu merkeze referans verilmiştir.

---

## Bölüm 1 — Ortak Motor Denklem ve Referans Merkezi (`[REF-*]`)

Veritabanındaki yüzlerce kolon; aşağıdaki 8 çekirdek motor denklemine doğrudan girdi sağlar. Kolon tablolarında `[REF-CA]`, `[REF-ROL]`, `[REF-ME]` gibi etiketler gördüğünüzde ilgili kolonun buradaki matematiksel modele bağlandığını anlayabilirsiniz.

### 1.1. `[REF-CA]` Pozisyona Göre Mevcut Yetenek (`CA`) Maliyet Denklemi ve 10 Pozisyon Ağırlık Matrisi
Kaynak: [`CA_POSITION_WEIGHTS_10`](../fm26save/formulas.py#L46-L155), [`ZERO_CA_COST_ATTRIBUTES`](../fm26save/formulas.py#L158-L176), [`estimate_player_used_ca()`](../fm26save/formulas.py#L186-L246).

Oyuncunun `1..20` ölçeğindeki görünür özellikleri (`Attributes`) ve zayıf ayak (`Weak Foot`) yetkinliği, oyuncunun oynayabildiği pozisyonların (`Positions`) ağırlık vektörü $w_p(a) \in [0, 10]$ ile çarpılarak **Mevcut Yetenek (`CA` `1..200`)** bütçesini tüketir:

$$\text{Ham Pozisyon Skoru } S_p = \frac{\sum_{a} w_p(a) \cdot (\text{Attr}_a - 1)}{\sum_{a} w_p(a)} + 0.18 \cdot (\text{WeakFoot}_{1..20} - 1)$$

$$\text{Tahmini Tüketilen CA } (\text{RCA}) = \text{clamp}\left(10.8 \cdot S_p - 12.0 + \Delta_{\text{çoklu pozisyon}}, \; 1, \; 200\right)$$

- **Çoklu Pozisyon Maliyeti ($\Delta_{\text{çoklu pozisyon}}$):** Oyuncunun birincil doğal pozisyonu (`>= 15`) dışındaki her ek yetkin pozisyon (`>= 15`), yeni pozisyonda daha yüksek ağırlığa sahip olan özelliklerin farkı kadar ekstra `CA` bütçesi tüketir.
- **Sıfır `CA` Maliyetli Özellikler (`ZERO_CA_COST_ATTRIBUTES` — 15 Özellik):** Aşağıdaki 15 özellik **hiçbir pozisyonda `CA` bütçesi tüketmez (`w = 0.0`)**; yani `1` olmaları ile `20` olmaları arasında oyuncunun `CA` kotası açısından hiçbir fark yoktur:
  - **Görünür Zihinsel/Fiziksel/Teknik (10 adet):** `determination` (Kararlılık), `flair` (Özel Yetenek), `leadership` (Liderlik), `aggression` (Agresiflik), `natural_fitness` (Doğal Kondisyon), `corners` (Korner), `free_kick_taking` (Serbest Vuruş), `penalty_taking` (Penaltı), `long_throws` (Uzun Taç), `long_shots` (Uzaktan Şut).
  - **Kaleci Eğilimleri (3 adet):** `eccentricity` (Eksantriklik), `rushing_out` (Çıkış Eğilimi), `punching` (Yumruklama Eğilimi).
  - **Gizli Maç/Sakatlık Özellikleri (4 adet):** `consistency` (İstikrar), `important_matches` (Önemli Maçlar), `injury_proneness` (Sakatlığa Eğilim), `versatility` (Çok Yönlülük), `dirtiness` (Çirkeflik / Rekabetçi Çizgi). *(Not: `balance` da taban 10'luk tabloda `0` maliyetlidir).*

| Özellik (`Attribute`) | `GK` | `DC` | `DL_DR` | `WBL_WBR` | `DM` | `MC` | `ML_MR` | `AMC` | `AML_AMR` | `STC` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `decisions` (Karar Alma) | **10.0** | **10.0** | **8.0** | **7.4** | **10.0** | **7.7** | 4.6 | 5.1 | 4.4 | 3.7 |
| `acceleration` (Hızlanma) | 5.9 | 5.0 | **10.0** | **10.0** | 6.7 | **10.0** | **10.0** | **10.0** | **10.0** | **10.0** |
| `pace` (Hız) | — | 4.4 | **8.6** | **8.0** | 4.9 | **8.4** | **9.4** | **8.2** | **9.8** | 6.6 |
| `agility` (Çeviklik) | **7.7** | 5.2 | **7.3** | 6.6 | 6.7 | **7.0** | **7.2** | 5.4 | 6.1 | 5.2 |
| `stamina` (Dayanıklılık) | — | 2.3 | **7.1** | 6.9 | 4.0 | **7.6** | 6.4 | 5.7 | 5.9 | 5.2 |
| `strength` (Güç) | 3.7 | 5.6 | 6.0 | 5.1 | 5.9 | 5.1 | 3.6 | 3.0 | 3.2 | 5.6 |
| `jumping_reach` (Zıplama) | — | 6.0 | — | — | — | — | — | — | — | 4.5 |
| `anticipation` (Önsezi) | 2.8 | 4.3 | 4.2 | 4.8 | 4.7 | 4.6 | 3.3 | 3.3 | 2.9 | 4.0 |
| `composure` (Soğukkanlılık) | 1.8 | 2.6 | — | — | 3.1 | 3.4 | — | 2.6 | — | 5.2 |
| `concentration` (Konsantrasyon) | 5.4 | 3.3 | 5.2 | 3.5 | 3.4 | — | — | — | 2.4 | — |
| `positioning` (Pozisyon Alma) | 4.2 | **8.1** | 4.6 | — | 5.6 | 3.0 | — | — | — | — |
| `off_the_ball` (Topsuz Alan) | — | — | — | 2.7 | — | 3.3 | 2.6 | 2.7 | 2.3 | 5.4 |
| `vision` (Vizyon) | — | — | — | — | 3.8 | 6.2 | 2.5 | 5.0 | — | — |
| `teamwork` (Takım Oyunu) | — | — | 2.6 | — | 2.8 | — | — | — | — | — |
| `work_rate` (Çalışkanlık) | — | — | 3.0 | 3.1 | 3.7 | 3.1 | 2.3 | — | — | — |
| `bravery` (Cesaret) | 5.1 | 2.8 | — | — | — | — | — | — | — | — |
| `first_touch` (İlk Kontrol) | — | 2.0 | 3.9 | 4.4 | 4.2 | 6.9 | 4.0 | 4.3 | 4.0 | 5.0 |
| `passing` (Pas) | 2.0 | 1.9 | 2.4 | 3.5 | 3.6 | 5.8 | 2.4 | 3.3 | 2.1 | — |
| `technique` (Teknik) | — | — | — | 2.6 | — | 4.6 | 3.2 | 4.4 | 2.5 | 3.3 |
| `dribbling` (Dripling) | — | — | 2.2 | 3.2 | — | 3.5 | 3.1 | 2.9 | 3.8 | 3.9 |
| `finishing` (Bitiricilik) | — | — | — | — | — | — | — | 2.5 | 2.2 | **7.5** |
| `heading` (Kafa Vuruşu) | — | 4.2 | 3.5 | — | — | — | — | — | — | 4.8 |
| `crossing` (Orta Yapma) | — | — | 3.1 | 3.4 | — | — | 4.3 | — | 3.8 | — |
| `marking` (Markaj) | — | **8.2** | 3.3 | 3.8 | 5.0 | — | — | — | — | — |
| `tackling` (Top Kapma) | — | 4.3 | 4.2 | 3.4 | 5.8 | 3.8 | — | — | — | — |
| `reflexes` / `handling` / `aerial_reach` | **7.8 / 7.7 / 5.5** | — | — | — | — | — | — | — | — | — |
| `command_of_area` / `kicking` / `communication` | **4.9 / 4.3 / 3.7** | — | — | — | — | — | — | — | — | — |
| `one_on_ones` / `throwing` | **2.9 / 2.5** | — | — | — | — | — | — | — | — | — |

---

### 1.2. `[REF-ROL]` Toplu Oyun (`IP` 50 Rol × 6 Görev), Topsuz Oyun (`OOP` 39 Rol) ve Stil Uyum Denklemleri
Kaynak: [`TACTICAL_ROLE_DEFINITIONS`](../fm26save/formulas.py#L249-L510), [`DUTY_ATTRIBUTE_DELTAS`](../fm26save/formulas.py#L513-L552), [`OUT_OF_POSSESSION_ROLE_CATALOG`](../fm26save/formulas.py#L583-L860), [`score_player_for_role()`](../fm26save/formulas.py#L863-L945).

1. **Birincil (`Key`) ve İkincil (`Pref`) Rol Uyumu (`0..100`):**
   - Her `IP` (Toplu Oyun) ve `OOP` (Topsuz Oyun) rolü; birincil (`key`, ağırlık **`2.0`**) ve ikincil (`pref`, ağırlık **`1.0`**) özellik kümelerinden oluşur.
   - Seçilen görev (`Duty`: `Defend`, `Support`, `Attack`, `Stopper`, `Cover`, `Float`), [`DUTY_ATTRIBUTE_DELTAS`](../fm26save/formulas.py#L513-L552) üzerinden bazı özellikleri `pref` listesinden `key` listesine terfi ettirir veya `pref` listesine ekler:
     - **`Defend`:** `positioning`, `concentration`, `marking` $\rightarrow$ `Key`; `tackling`, `anticipation` $\rightarrow$ `Pref`.
     - **`Support`:** `teamwork`, `decisions`, `passing` $\rightarrow$ `Key`; `work_rate`, `stamina`, `first_touch` $\rightarrow$ `Pref`.
     - **`Attack`:** `off_the_ball`, `acceleration`, `dribbling` $\rightarrow$ `Key`; `finishing`, `composure`, `pace`, `flair` $\rightarrow$ `Pref`.
     - **`Stopper`:** `aggression`, `bravery`, `decisions`, `strength` $\rightarrow$ `Key`; `tackling`, `heading`, `jumping_reach` $\rightarrow$ `Pref`.
     - **`Cover`:** `acceleration`, `pace`, `anticipation`, `decisions` $\rightarrow$ `Key`; `positioning`, `concentration` $\rightarrow$ `Pref`.
     - **`Float` (Serbest):** `off_the_ball`, `vision`, `decisions`, `flair` $\rightarrow$ `Key`; `first_touch`, `composure`, `agility` $\rightarrow$ `Pref`.
2. **Pozisyon Yetkinlik Çarpanı ($M_{\text{pos}}$):**
   - Oyuncunun o koltuktaki pozisyon puanı (`1..20`) rol skorunu doğrudan çarpar:
     - `18..20` (`Natural` / Doğal): **`1.00x`**
     - `15..17` (`Accomplished` / İyi): **`0.93x`**
     - `12..14` (`Competent` / Yeterli): **`0.84x`**
     - `9..11` (`Unconvincing` / İdare Eder): **`0.72x`**
     - `1..8` (`Makeshift` / Yabancı): **`0.55x`**
3. **FM26/FM27 Birleşik Slot Skoru:**
   $$\text{Slot Skoru} = \left(0.60 \cdot \text{IP\_Score} + 0.40 \cdot \text{OOP\_Score}\right) \cdot M_{\text{pos}}$$
4. **24 Bölgeli Topsuz/Toplu Yakınlık Cezası (`OOP_PROXIMITY_MATRIX_24`):**
   - Oyuncunun `IP` pozisyonu ile `OOP` pozisyonu arasındaki saha içi geçiş mesafesi `24×24` matristen (`1..12` birim) okunur. Mesafe arttıkça geçiş anındaki pozisyon kaybı ve kondisyon tüketimi doğrusal olarak artar.

---

### 1.3. `[REF-TE]` FM27 Taktiksel Karmaşıklık (`Complexity`), Etkinlik (`Effectiveness`) ve `Player Buy-In`
Kaynak: [`docs/FM27_VS_FM26_COMPLETE_DIFFERENCES_AND_ALGORITHMS_TR.md`](./FM27_VS_FM26_COMPLETE_DIFFERENCES_AND_ALGORITHMS_TR.md#L130-L310), `simatch.fmf/config/tactical_effectiveness_config.json`.

- **Taktiksel Karmaşıklık (`Tactical Complexity` $\in [0.0, 3.0]$):**
  $$\text{Complexity} = 0.25 \cdot C_{\text{TeamInstructions}} + 0.25 \cdot C_{\text{PlayerInstructions}} + 0.25 \cdot C_{\text{Roles}} + 0.25 \cdot C_{\text{FormationTransitions}}$$
- **Maç İçi Taktiksel Etkinlik (`Tactical Effectiveness` $\in [0, 100]$):**
  $$\text{TE} = \text{clamp}\left(50.0 + \text{TrainingContribution}_{-20..+20} + \text{InstructionBonus}_{-5..+5} + \text{MentalityMod}_{-10..+5} + \text{BuyInMod}_{-15..+15}, \; 0, \; 100\right)$$
- **Oyuncu İkna / Benimseme Skoru (`Player Buy-In` $\in [0, 100]$):**
  $$\text{Buy-In} = \text{clamp}\left(50 + 0.80 \cdot \text{Relationships} + 0.40 \cdot \text{ReputationDiff} + 0.60 \cdot \text{PromiseImpact} + 0.30 \cdot \text{RecentResults} + 0.20 \cdot \text{PlayingTimeHappiness}, \; 0, \; 100\right)$$
- **Antrenman Katkısı (`Training Contribution`) ve 251 Günlük Sönümlenme (`Decay`):**
  - Son **251 gün** içindeki her antrenman seansı ve maç dakikası `0.985^gün` üstel sönümlenme ile toplanır.
  - Kadrodaki her oyuncunun katkısı kıdem çarpanıyla ağırlıklandırılır: **`Team Leader = 1.00x`**, **`Highly Influential = 0.90x`**, **`Influential = 0.80x`**, **`Other = 0.60x`**.

---

### 1.4. `[REF-ME]` 3B Maç Motoru, `xG` (11 Lojistik Model), Maç Reytingi (`6.70` Baz) ve Hızlı Maç Motoru (`QME`)
Kaynak: `simatch.fmf` (`match_stats_extract.jsb`, `spatial_momentum_rules.json`), `QuickMatchEngine.fmf/qme_stat_distributions.json`.

1. **Maç İçi Beklenen Gol (`xG` — 11 Lojistik Regresyon Modeli):**
   $$P(\text{Gol}) = \frac{1}{1 + \exp\left(-(\beta_0 + \sum_k \beta_k x_k)\right)}$$
   - Şutun türüne göre (`Penaltı = sabit 0.785`, `Serbest Vuruş`, `Korner Kafa`, `Korner Ayak`, `Orta Kafa`, `Orta Ayak`, `Açık Oyun Kafa`, `Açık Oyun Ayak 1v1`, `Açık Oyun Ayak Normal`, `Dar Açı`, `Uzaktan >25m`) 11 ayrı katsayı tablosu çalışır. Girdiler: Kaleye mesafe ($d$), görüş açısı ($\theta$), kaleci pozisyon sapması, en yakın savunmacı baskı mesafesi, top yüksekliği ve oyuncunun o ayağının (`left_foot` / `right_foot`) gücü.
2. **Maç Reytingi (`Match Rating` `0.10..10.00`):**
   - Her oyuncu maça **`6.70` (`67` iç puan)** ile başlar.
   - `52` aksiyon vektörü (`gol`, `asist`, `anahtar pas`, `top kapma`, `hatalı pas`, `penaltı yaptırma`, `xG üstü/altı bitiriş` vb.) oyuncunun pozisyon grubuna göre (`GK`, `DEF`, `MID`, `ATT`) puan ekler/çıkarır ve dakika çarpanı (`90min Adjuster`) ile normalize edilir.
3. **Uzamsal Momentum (`Spatial Momentum` — 48 Kural):**
   - Saha `3×3` bölgeye ayrılır; üst üste isabetli paslar, kazanılan ikili mücadeleler ve şutlar hücum momentumunu artırarak savunma hattının `concentration` ve `positioning` hata olasılığını yükseltir.
4. **Hızlı Maç Motoru (`QME` — Simüle Edilen Maçlar):**
   - Arka plandaki lig maçları `QuickMatchEngine.fmf` içindeki **`22` istatistik türü × `3.420` olasılık dağılımı** ile çözülür. İki takımın `CA`, `Condition`, `Tactical Familiarity`, `Morale`, `Home Advantage (Attendance + Altitude + Weather)` farkları gol ve istatistik dağılımlarını belirler.

---

### 1.5. `[REF-ANT]` Haftalık Antrenman Motoru (`44` / `59` Seans) ve Koç Yıldız (`DDB`) Denklemi
Kaynak: [`FM26_TRAINING_SESSIONS`](../fm26save/formulas.py#L1120-L1350), [`FM27_TRAINING_SESSIONS`](../fm26save/formulas.py#L1352-L1620), [`calculate_coach_stars()`](../fm26save/formulas.py#L948-L1035).

- **Koç Yıldız Hesabı (`DDB` = `Determination + Discipline + Motivating`):**
  $$\text{DDB} = \text{Determination}_{1..20} + \text{Discipline}_{1..20} + \text{Motivating}_{1..20} \quad (\text{Maks } 60)$$
  - Her antrenman kategorisi (`Defending Tactical`, `Defending Technical`, `Attacking Tactical`, `Attacking Technical`, `Possession Tactical`, `Possession Technical`, `Shot Stopping`, `Handling & Distribution`, `Quickness`, `Strength`) için ana özellik ağırlığı (`6` veya `9`) + `DDB × 2` toplanarak `0.5★ .. 5.0★` (`270+` puan = `5.0★`) üretilir.
- **Birim Bazlı Gelişim (`Attacking`, `Midfield`, `Defensive`, `Goalkeeping` Units):**
  - Her antrenman seansı (FM26'da `44`, FM27'de `59` seans) bu birimlere farklı ağırlıklarla (`0.60` birincil birim, `0.25` ikincil birim, `0.15` üçüncül birim) dağılır ve seansın hedeflediği spesifik oyuncu özelliklerine (`Attributes`) gelişim puanı (`XP`) yazar; aynı zamanda sakatlık riskini (`injury_risk`), yorgunluğu (`fatigue`) ve kondisyon kaybını (`condition_drop`) tetikler.

---

### 1.6. `[REF-AI]` Yapay Zeka Kadro Seçimi (`weights.jsb` 4×40 Faktör) ve Duran Top Öncelik Kuyrukları
Kaynak: `tables.fmf/weights.jsb`, [`docs/FM26_INTERNAL_GAME_LOGICS_AND_MECHANICS.md`](./FM26_INTERNAL_GAME_LOGICS_AND_MECHANICS.md#L150-L340).

Yapay zeka (ve "Hızlı Seçim / Ask Assistant"), her oyuncu×koltuk çifti için 40 adet `TSF_*` faktörünü 4 farklı maç önem profiline (`TPS_FIRST_TEAM`, `TPS_CUP`, `TPS_YOUTH`, `TPS_RESERVE`) göre toplar:

| `TSF_*` Kadro Seçim Faktörü | `TPS_FIRST_TEAM` (As Maç) | Açıklama / Dokunduğu Veritabanı Kolonları |
| :--- | :---: | :--- |
| `TSF_POSITION_ABILITY` | **`+150`** | Oyuncunun o koltuktaki pozisyon yetkinliği (`Positions` `1..20`). |
| `TSF_CA_AND_ATTRIBUTES` | **`+95`** | `ca`, rol uyum skoru (`[REF-ROL]`) ve koçun `JPA` (`block_40`) algısı. |
| `TSF_CONDITION` | **`+80`** | `raw_condition` (`Pcon`) ve `Pjad` (Yorgunluk/Jadedness). |
| `TSF_TACTICAL_FAMILIARITY` | **`+50`** | Oyuncunun taktiğe aşinalığı ve FM27 `Tactical Effectiveness` (`[REF-TE]`). |
| `TSF_AGREED_PLAYING_TIME` | **`+45`** | `Contract.squad_status` (`Star Player` $\rightarrow$ `Fringe Player`) sözü. |
| `TSF_FORM` / `TSF_MATCH_RATING` | **`+35` / `+30`** | Son 5 maç ortalaması (`average_rating`) ve form. |
| `TSF_MORALE` | **`+25`** | Oyuncu morali (`morale` `1..20`). |
| `TSF_PPMS` | **`+25`** | Oyuncunun `Trait` (`PPM`) bitlerinin o koltuktaki rolle uyumu. |
| `TSF_MATCH_SHARPNESS` | **`+20`** | `raw_match_sharpness` (`Pfit`). |
| `TSF_LEFT_RIGHT_FOOT` | **`+20`** | `left_foot` / `right_foot` (`Inverted Winger` ters ayak, `Winger` aynı ayak vb.). |
| `TSF_INTEGRATION` | **`+15`** | Konuşulan diller (`spoken_languages`) ve takım uyumu. |
| `TSF_DISLIKE` | **`-30`** | Teknik direktörün oyuncuyu sevmemesi (`disliked_people` `(10, 2)`). |
| `TSF_INJURY_RISK` | **`-60`** | Sağlık ekibi raporu, `injury_proneness` ve düşük `raw_condition`. |

---

### 1.7. `[REF-EKO]` Piyasa Değeri (`Transfer Value`), Maaş (`Wage`), İmza/Sadakat (`money_a`) ve Menajer Ücreti (`money_b`)
Kaynak: [`estimate_market_value()`](../fm26save/formulas.py#L1038-L1118), [`docs/FM26_ENGINE_FORMULAS_AND_CALCULATIONS.md`](./FM26_ENGINE_FORMULAS_AND_CALCULATIONS.md#L1-L150).

1. **Piyasa Değeri (`Market Value` — OLS Log-Lineer Model, $R^2 = 0.785$):**
   $$\ln(\text{Value}) = 5.4105 + 0.0684 \cdot \text{CA} + 0.0142 \cdot \text{PA} - 0.1412 \cdot \text{Age} + 0.00051 \cdot \text{WorldRep} + 0.3120 \cdot \ln(\text{Wage} + 1) + 0.1850 \cdot \text{YearsLeft} + 0.00038 \cdot \text{ClubRep}$$
2. **Haftalık Maaş (`wage_per_week`) Talebi:**
   - Oyuncunun `CA`, `world_reputation`, `age`, kulübün `reputation` + `FinanceMonth.wage_budget`, oyuncunun kişiliği (`ambition` $\uparrow$, `loyalty` $\downarrow$, `greed`) ve temsilcisinin (`Agent`) `Agre` (`Business/Greed`) parametresiyle belirlenir.
3. **Sadakat Primi (`Contract.unknown.money_a`) ve Temsilci Komisyonu (`Contract.unknown.money_b`):**
   - `money_a` (Sadakat/İmza Primi): Yıllık maaşın $\approx 0.4\text{x}..1.2\text{x}$ katıdır; oyuncunun `loyalty` özelliği düşük, `ambition` özelliği yüksekse talep edilen peşin imza parası yükselir.
   - `money_b` (Menajer Ücreti): Transfer/sözleşme büyüklüğünün ve temsilcinin `Agre` (`Business`) + `Asoa` (`Size of Agency`) değerlerinin fonksiyonudur.

---

## Bölüm 2 — Oyuncu (`players` / `Player` / `person.xml` / `player.xml`) Tablosundaki Tüm Kolonlar ve Parametreler

Kaynak modeller: [`Player`](../fm26save/_core/models/players.py#L406-L520), [`Ability`](../fm26save/_core/models/players.py#L12-L21), [`Reputation`](../fm26save/_core/models/players.py#L24-L35), [`Personality`](../fm26save/_core/models/players.py#L38-L55), [`Attributes`](../fm26save/_core/models/players.py#L58-L168), [`Positions`](../fm26save/_core/models/players.py#L171-L208), [`Trait`](../fm26save/_core/models/players.py#L211-L250) ve [`enrichment.py`](../fm26save/enrichment.py).

### 2.1. Kimlik, Biyometrik, Uyruk ve Altyapı (`Home-Grown`) Kolonları

| Kolon Adı (`Player`) | FourCC (`editor.fmf`) | Tip / Aralık | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :---: | :---: | :--- |
| `id` / `unique_id` | `dbid` / `Puid` | `int` (`uint32`) | Tüm tablolarda (`contracts`, `injuries`, `player_season_stats`, `mentoring`, `shortlist_man.dat`) birincil/yabancı anahtar; yüz/forma grafik paketlerinde (`config.xml`) eşleşme ID'si. |
| `first_name`, `last_name`, `common_name` | `Pfna`, `Psna`, `Pcna` | `str` (`person_name_dt.dat`) | Arayüz, haber metinleri (`news.dat`), forma arkası isim (`shirt_name`) ve arama dizini. Ülkenin `Nsnf` (`Name Style`) kuralına göre sıralanır. |
| `birth_date` / `age` | `Pdba` / `Page` | `date` / `int` (`14..55`) | **1) Gelişim Eğrisi:** `15..23` yaş arası hızlı `CA` gelişimi; `24..28` zirve; `30+` yaşta (`natural_fitness` ile ters orantılı) `acceleration`, `pace`, `stamina`, `agility` düşüşü.<br>**2) Ekonomi:** `[REF-EKO]` denkleminde her yaş `ln(Value)` değerini `-0.1412` düşürür.<br>**3) Kural & Kıdem:** U19/U21/U23 uygunluğu, FM27 antrenman kıdem çarpanı (`[REF-TE]`) ve `Nygd` (Genç Kontrat Yaşı) sınırı. |
| `height_cm` | `Phei` | `int` (`150..210` cm) | **1) `Jumping Reach` (`Zıplama Erişimi`) Tavan/Taban Sınırı (`tables.fmf`):** Motor yeni oyuncu (`newgen`) üretirken veya `0` girilen zıplama değerini doldururken boya göre sıkı bir dağılım uygular (`<170 cm` oyuncunun `jumping_reach` tavanı düşükken, `195+ cm` oyuncunun tabanı yüksektir).<br>**2) 3B Maç Motoru Çarpışma Kutusu:** Kaleci `aerial_reach` erişim zarfını ve kafa topu temas yüksekliğini doğrudan belirler. |
| `weight_kg` & `body_type_code_123` | `Pwei` | `int` (`50..115` kg) / `uint8` (`1..5`) | **1) İkili Mücadele Momentumu:** Omuz omuza mücadelelerde `strength` ve `balance` ile birlikte fiziksel itme/devrilme eşiğini belirler.<br>**2) 3B Görsel:** `body_type_code_123` (`Ectomorph`, `Mesomorph`, `Endomorph`) 3B oyuncu modelinin omuz/gövde kalınlığını çizer. |
| `nation_id` & `second_nation_ids` | `Pnat` / `Psnt` | `int` / `tuple[int, ...]` | **1) Yabancı Sınırı & Çalışma İzni:** `competition_rules` yabancı kontenjanı, AB (`EU`) serbest dolaşımı ve İngiltere `Work Permit` puanlaması.<br>**2) Dil & Uyum:** Ülkenin resmi dillerini (`nation.xml` $\rightarrow$ `Nlan`) otomatik ata; vatandaşlık süresi (`nation.xml` $\rightarrow$ `Nygc` `Years to Gain Nationality`) dolduğunda `second_nation_ids` listesine eklenir.<br>**3) Vergi:** Bazı ülkelerde (`nation.xml` $\rightarrow$ `Ntxr`) yerli vs yabancı vergi dilimi farkı. |
| `international_apps`, `international_goals`, `u21_apps`, `u21_goals` | `Pcap`, `Pigo`, `Pu21`, `Pu2g` | `int16` | **1) Çalışma İzni (`Work Permit`):** Son 2 yıldaki milli maç yüzdesi çalışma izni puanının ana girdisidir.<br>**2) Sözleşme Maddeleri:** `International Appearances Bonus` ve `Wage After International Appearances` (`contract.xml`) maddelerini tetikler.<br>**3) İtibar:** Her A milli maç `world_reputation` değerini artırır. |
| `home_grown_nation_ids` & `home_grown_club_uids` | `Phgn` / `Phgc` | `tuple[int, ...]` | `15..21` yaşları arasında kulüpte/ülkede **36 ay (1095 gün)** geçiren oyunculara atanır. UEFA ve yerel lig kadro kayıtlarında (**minimum 4 kulüp altyapısı + 8 ülke altyapısı**) zorunlu kotaları doldurur; `TSF_SQUAD_REGISTRATION` üzerinden AI transfer değerini `%15..%35` artırır. |
| `preferred_squad_number` & `squad_number` | `Ppsn` / `Psnu` | `int8` (`1..99`) | Oyuncunun tercih ettiği forma numarası. Sözleşmede `Preferred Squad Number` vaadi verilmişse ve bu numara başka oyuncuya verilirse `PromiseImpact` (`[REF-TE]`) ve `morale` düşer. Forma satış (`merchandising`) haberlerinde yıldız numaraları (`7`, `9`, `10`, `11`) satışı artırır. |

---

### 2.2. Yetenek (`Ability`) ve İtibar (`Reputation`) Kolonları

| Kolon Adı | FourCC | Tip / Aralık | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :---: | :---: | :--- |
| `ability.ca` (`ca`) | `Pcab` | `int16` (`1..200`) | **Mevcut Yetenek (`Current Ability`):**<br>**1) Özellik Bütçesi:** `[REF-CA]` denklemiyle 37 ağırlıklı görünür özelliğin ve zayıf ayağın alabileceği toplam üst sınırı belirler. Antrenmanda özellikler arttıkça `ca` tüketilir; `ca == pa` olduğunda gelişim durur.<br>**2) Yapay Zeka & Ekonomi:** `TSF_CA_AND_ATTRIBUTES (+95)` (`[REF-AI]`), `QME` simülasyon gücü (`[REF-ME]`) ve `[REF-EKO]` piyasa değeri denkleminde en büyük pozitif katsayı (`+0.0684 × CA`). |
| `ability.pa` (`pa`) | `Ppab` | `int16` (`1..200` veya `-10..-1`) | **Potansiyel Yetenek (`Potential Ability`):**<br>**1) Gelişim Tavanı:** Oyuncunun kariyeri boyunca ulaşabileceği maksimum `CA` sınırıdır. Antrenman gelişim hızı $\propto (\text{PA} - \text{CA})$ farkıyla doğru orantılıdır.<br>**2) Negatif `PA` (`editor.fmf`):** Veritabanında `-10` (`170..200`), `-95` (`160..190`), `-9` (`150..180`), `-85` (`140..170`), `-8` (`130..160`), ..., `-1` (`0..20`) olarak girilen değerler yeni kariyer kurulurken bu aralıktan rastgele bir sabit `PA` sayısına dönüştürülür.<br>**3) Ekonomi:** Genç oyuncularda `[REF-EKO]` piyasa değerini `+0.0142 × PA` artırır. |
| `rca_peak_byte_118` & `pa_copy_byte_119` | — (Save `+118`, `+119`) | `uint8` (`1..200`) | Kayıt dosyasında oyuncunun o ana kadar ulaştığı **en yüksek (Peak) `CA`** izini (`+118`) ve başlangıç `PA` kopyasını (`+119`) tutar. Yaşlı oyuncularda fiziksel düşüş sonrası antrenör/gözlemci raporlarında *"eskiden çok daha üst düzey bir oyuncuydu"* kıyaslamasını ve emeklilik (`retirement`) kararını tetikler (`CA`, `rca_peak_byte_118` değerinin çok altına düştüğünde oyuncu emeklilik kararı alır). |
| `reputation.home` | `Phre` | `int16` (`1..10000`, UI `1..200`) | Oyuncunun **kendi ülkesindeki** bilinirliği. Yerel lig kulüplerinin transfer ilgisini, yerel medya haber sıklığını ve milli takım çağrı önceliğini belirler. |
| `reputation.current` | `Pcre` | `int16` (`1..10000`, UI `1..200`) | Oyuncunun **anlık performansa duyarlı** itibarı:<br>**1) Transfer & Maaş:** Oyuncunun kendisinden daha düşük itibarlı kulüplere (`Club.reputation < Player.current_reputation`) gitmeyi reddetmesini ve maaş/oynama süresi (`Star Player` vs `Squad Player`) talebini belirler.<br>**2) Soyunma Odası & `Buy-In`:** `[REF-TE]` denkleminde teknik direktörün itibarı ile oyuncunun `current` itibarı arasındaki fark (`0.40 × ReputationDiff`) oyuncunun hocaya saygısını belirler. |
| `reputation.world` | `Pwre` | `int16` (`1..10000`, UI `1..200`) | Oyuncunun **küresel/tarihsel** şöhreti:<br>**1) Piyasa Değeri:** `[REF-EKO]` denkleminde `+0.00051 × WorldRep` katkısı.<br>**2) Ticari Gelir (`Merchandising`):** Kulübün yurt dışı forma satışlarını ve ticari sponsorluk (`Sponsorship`) çekiciliğini artırır.<br>**3) Ödüller:** `Ballon d'Or` / `World Player of the Year` (`award.xml`) oylamalarında taban ağırlık. |
| `reputation.bucket` | — | `uint8` (`0..10`) | Kayıt dosyasındaki hızlı arama/indeksleme kovası (`current_reputation // 1000`). Gözlemcilik (`Scouting`) filtrelerinde hızlı ön eleme için kullanılır. |

---

### 2.3. 52 Görünür Oyuncu Özelliği (`Attributes`) + Sağ/Sol Ayak (`left_foot`, `right_foot`) — Tek Tek Tam Katalog

Kaynak: [`Attributes`](../fm26save/_core/models/players.py#L58-L168). Kayıt dosyasında içsel olarak `1..100` (`uint8`, `deci-scale` veya `×5`) tutulur ve arayüzde `1..20` olarak gösterilir.

> [!IMPORTANT]
> **Kullanıcının Özel Örneği — `finishing` (Bitiricilik) Nerede ve Ne Kadar İşe Yarıyor?**
> Aşağıdaki tabloda `finishing` satırında görüldüğü üzere Bitiricilik:
> 1. **`CA` Maliyeti (`[REF-CA]`):** Sadece **3 pozisyonda** `CA` tüketir: **`STC` (Santrfor) = `7.5`** (çok yüksek maliyet), **`AMC` = `2.5`**, **`AML/AMR` = `2.2`**. Orta saha (`MC/DM/ML/MR`) ve savunma (`DC/DL/DR/WB`) pozisyonlarında **`CA` maliyeti `0.0`'dır**!
> 2. **Toplu Oyun Rolleri (`[REF-ROL]`):** **8 rolde Birincil (`Key`, `2.0x` ağırlık)** (`shadow_striker`, `inside_forward`, `advanced_forward`, `poacher`, `complete_forward`, `segundo_volante`, `wide_forward`, `channel_forward`) ve **10 rolde İkincil (`Pref`, `1.0x` ağırlık)** (`box_to_box_midfielder`, `mezzala`, `target_forward`, `pressing_forward`, `channel_midfielder`, `attacking_midfielder`, `trequartista`, `wide_target_man`, `deep_lying_forward`, `false_nine`) özelliktir. Ayrıca **`Attack` görevi** seçilen herhangi bir rolde otomatik olarak `Pref` listesine eklenir.
> 3. **Topsuz Oyun Rolleri (`OOP`):** **3 kontra-çıkış (`Outlet`) rolünde Birincil (`Key`)** (`OPInvertingOutletWinger`, `OPCentralOutletCentreForward`, `OPSplittingOutletCentreForward`) özelliktir (`oop_attributes_scoring.jsb` ID `5`).
> 4. **3B Maç Motoru & `xG` Sonrası Şut Fiziği (`[REF-ME]`):** Dikkat! `xG` (`Expected Goals`) şutun çekildiği konumun kalitesini ölçer (`finishing` `xG` değerini **değiştirmez**); `finishing` ise (`composure` ve `technique` ile birlikte) çekilen şutun **kale çerçevesi içindeki hedef köşeye sapma açısını (hedef varyansını)** daraltır. Yani yüksek `finishing`, oyuncunun `xG` değerinin **üzerinde (`Goals > xG`)** gol atmasını ve kalecinin `reflexes`/`handling` erişim zarfının dışına vuruş yapmasını sağlar.
> 5. **Hızlı Maç Motoru (`QME`):** `SHOTS_ON_TARGET` ve `GOALS_FROM_INSIDE_BOX` dönüşüm oranlarını doğrudan çarpar.
> 6. **Antrenman (`[REF-ANT]`):** `Chance Conversion` (Gol Çevirme), `Shooting` (Şut) ve `Attacking Patient` seanslarında `Attacking` birimi üzerinden gelişir.

#### 2.3.1. Teknik Özellikler (`Technical Attributes` — 14 Kolon)

| Kolon (`Attributes`) | FourCC | `CA` Maliyet Ağırlıkları (`[REF-CA]`) | `IP` Rolleri (`Key` / `Pref` / `Duty`) (`[REF-ROL]`) | `OOP` Rolleri & Stil DNA (`[REF-ROL]`) | Maç Motoru (`3D ME` & `QME`) ve Antrenman (`[REF-ANT]`) Etkisi |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **`crossing`**<br>*(Orta Yapma)* | `Pcro` | `ML_MR:4.3`, `AML_AMR:3.8`, `WBL_WBR:3.4`, `DL_DR:3.1` | **Key (7):** `wing_back`, `winger`, `inverted_winger`, `overlapping_cb`, `advanced_wb`, `wide_mid`, `defensive_winger`<br>**Pref (7):** `full_back`, `mezzala`, `wide_cb`, `playmaking_wb`, `channel_mid`, `wide_tm`, `channel_fwd` | **OOP Key (2):** `OPWideOutletWideMid`, `OPWideOutletWinger`<br>**OOP Pref (1):** `OPSplittingOutletCF`<br>**Stil:** `wing_play (2.2)` | Açık oyunda ve duran toplarda kanattan ceza sahasına gönderilen ortaların hedef bölge/oyuncu isabetini belirler. Duran top `Creator` kuyruğunda (`corners` ve `free_kick_taking` ile) ana çarpan. `Wing Play` ve `Attacking Wings` antrenmanlarında gelişir. |
| **`dribbling`**<br>*(Dripling)* | `Pdri` | `STC:3.9`, `AML_AMR:3.8`, `MC:3.5`, `WBL_WBR:3.2`, `ML_MR:3.1`, `AMC:2.9`, `DL_DR:2.2` | **Key (19):** `wing_back`, `mezzala`, `shadow_striker`, `winger`, `inside_fwd`, `inverted_winger`, `advanced_fwd`, `complete_fwd`, `overlapping_cb`, `libero`, `advanced_wb`, `b2b_pm`, `channel_mid`, `am`, `trequartista`, `wide_pm`, `def_winger`, `false_nine`, `channel_fwd`<br>**Pref (10)** \| **Duty Key:** `Attack` | **OOP Key (6):** Tüm `Outlet` (`Central`, `Splitting`, `Wide`, `Inverting`) rolleri<br>**Stil:** `wing_play (1.8)`, `fluid_counter (1.6)` | Oyuncu topla koşarken topun ayağa yakınlık frekansını (dokunuş sıklığını) ve hız kaybı oranını belirler; savunmacının `tackling` müdahale penceresini daraltır. `QME` içinde `DRIBBLES_MADE` istatistiğinin birincil girdisidir. |
| **`finishing`**<br>*(Bitiricilik)* | `Pfin` | **`STC:7.5`**, `AMC:2.5`, `AML_AMR:2.2` *(Diğer 7 pozisyonda `0.0`)* | **Key (8):** `shadow_striker`, `inside_fwd`, `advanced_fwd`, `poacher`, `complete_fwd`, `segundo_volante`, `wide_fwd`, `channel_fwd`<br>**Pref (10):** `b2b`, `mezzala`, `target_fwd`, `pressing_fwd`, `channel_mid`, `am`, `trequartista`, `wide_tm`, `dlf`, `false_nine`<br>**Duty Pref:** `Attack` | **OOP Key (3):** `OPInvertingOutletWinger`, `OPCentralOutletCF`, `OPSplittingOutletCF` | Ceza sahası içi ve 1v1 vuruşlarda şut vektörünün hedef köşe sapmasını minimize eder (`composure` baskı etkisini, `technique` vuruş zorluğunu, `finishing` ise hedef isabetini yönetir). Penaltılarda `penalty_taking` ile birlikte ikincil çarpan. |
| **`first_touch`**<br>*(İlk Kontrol)* | `Pftc` | `MC:6.9`, `STC:5.0`, `WBL_WBR:4.4`, `AMC:4.3`, `DM:4.2`, `ML_MR:4.0`, `AML_AMR:4.0`, `DL_DR:3.9`, `DC:2.0` | **Key (24):** Tüm oyun kurucu, hücum orta saha ve teknik forvet rolleri<br>**Pref (18)** \| **Duty Pref:** `Support`, `Float` | **OOP Key (7):** Tüm 7 `Outlet` kontra rolü<br>**Stil:** `tiki_taka (2.1)`, `vertical_tiki_taka (2.0)`, `control_possession (1.8)` | Gelen pasın/uzun topun kontrol edilirken sekme yarıçapını ve oyuncunun bir sonraki aksiyona (`pas`/`şut`/`dripling`) geçiş süresini (ms) belirler. Yüksek pres (`gegenpress`) altında top kaybını önleyen en kritik teknik özelliktir. |
| **`free_kick_taking`**<br>*(Serbest Vuruş)* | `Pfkt` | **`0.0` (`Zero-CA`)** | Rollerde yer almaz (`0`) | Rollerde yer almaz (`0`) | Doğrudan kaleye çekilen frikiklerde baraj üstü kavis (`technique` ile) ve isabeti; dolaylı frikiklerde (`crossing` ile) hedef bölge isabetini belirler. Duran top frikik atıcısı seçiminde 1 numaralı kriterdir. |
| **`heading`**<br>*(Kafa Vuruşu)* | `Phea` | `STC:4.8`, `DC:4.2`, `DL_DR:3.5` | **Key (8):** `cd`, `bpd`, `target_fwd`, `complete_fwd`, `nncb`, `wide_cb`, `ifb`, `wide_tm`<br>**Pref (5)** \| **Duty Pref:** `Stopper` | **OOP Key (4):** `OPCentreBack`, `OPStoppingCB`, `OPDroppingDM`, `OPCentralOutletCF`<br>**Stil:** `route_one (2.0)`, `park_the_bus (1.8)`, `wing_play (1.4)` | Hava topuna ulaşıldıktan sonra (`jumping_reach` + `height_cm` ulaşıp ulaşamayacağını belirler) kafa vuruşunun **isabetini ve yönünü** (şut, pas veya güvenli uzaklaştırma) belirler. Duran top `Aerial Threat` kuyruğunun ana girdisidir. |
| **`long_shots`**<br>*(Uzaktan Şut)* | `Plsh` | **`0.0` (`Zero-CA`)** | **Key (3):** `complete_fwd`, `segundo_volante`, `am`<br>**Pref (7):** `b2b`, `mezzala`, `inside_fwd`, `inverted_winger`, `libero`, `regista`, `b2b_pm` | — | Ceza sahası dışından (`>18m`) çekilen şutların isabet ve kaleyi bulma olasılığını belirler. Düşük `decisions` + yüksek `long_shots` kombinasyonu oyuncunun uygun pas opsiyonu varken uzaktan şut denemesine yol açar. |
| **`long_throws`**<br>*(Uzun Taç)* | `Plth` | **`0.0` (`Zero-CA`)** | Rollerde yer almaz (`0`) | Rollerde yer almaz (`0`) | Taç atışlarının maksimum menzilini ve ceza sahası içine korner gibi paralel/sert gönderilebilmesini (`strength` ile birlikte) sağlar. Hücum bölgesindeki taç atıcısı kuyruğunu belirler. |
| **`marking`**<br>*(Markaj)* | `Pmar` | **`DC:8.2`**, `DM:5.0`, `WBL_WBR:3.8`, `DL_DR:3.3` | **Key (14):** Tüm stoper, bek ve savunma ön libero rolleri<br>**Pref (6)** \| **Duty Key:** `Defend` | **OOP Key (19):** Tüm `CB`, `FB`, `WB`, `DM`, `Screening/Tracking` rolleri<br>**Stil:** `catenaccio (2.2)`, `park_the_bus (2.1)` | Savunmacının topsuz oyunda ve duran toplarda rakip hücumcuya olan mesafesini koruma, koşu yolunu kapatma ve rakibin `off_the_ball` sıyrılma denemelerini nötralize etme başarısını belirler. |
| **`passing`**<br>*(Pas)* | `Ppas` | `MC:5.8`, `DM:3.6`, `WBL_WBR:3.5`, `AMC:3.3`, `DL_DR:2.4`, `ML_MR:2.4`, `AML_AMR:2.1`, `GK:2.0`, `DC:1.9` | **Key (25):** Tüm oyun kurucu, merkez orta saha, `bpd`, `libero`, `iwb`, `dlf`, `f9` rolleri<br>**Pref (16)** \| **Duty Key:** `Support` | **OOP Key (1):** `OPCentralOutletMid`<br>**OOP Pref (5)**<br>**Stil:** `tiki_taka (2.3)`, `vertical_tiki_taka (2.1)`, `control_possession (2.0)`, `fluid_counter (1.7)` | Pasın hızını, şiddetini ve hedef oyuncunun koşu yoluna (`vision` ve `technique` ile birlikte) hatasız ulaşma olasılığını belirler. `QME` içinde `PASSES_COMPLETED` ve `KEY_PASSES` istatistiklerinin birincil girdisidir. |
| **`penalty_taking`**<br>*(Penaltı)* | `Ppen` | **`0.0` (`Zero-CA`)** | Rollerde yer almaz (`0`) | Rollerde yer almaz (`0`) | Penaltı vuruşlarında (`composure` ve `finishing` ile birlikte) kaleciyi ters köşeye yatırma ve köşe isabetini belirler. *(Not: Maçta `2` golü olan oyuncu `Hat-Trick` için penaltı sırasını devralabilir — taktik ayarından kapatılabilir).* |
| **`tackling`**<br>*(Top Kapma)* | `Ptac` | `DM:5.8`, `DC:4.3`, `DL_DR:4.2`, `MC:3.8`, `WBL_WBR:3.4` | **Key (22):** Tüm savunma, bek ve çift yönlü orta saha rolleri<br>**Pref (3)** \| **Duty Pref:** `Defend` | **OOP Key (25):** Neredeyse tüm savunma ve pres rolleri<br>**Stil:** `catenaccio (2.0)`, `park_the_bus (2.0)`, `direct_counter (1.6)` | Ayakta veya kayarak yapılan müdahalelerde faul yapmadan (`decisions` ve `dirtiness` ile birlikte) topu kazanma olasılığını belirler. `QME` içinde `TACKLES_WON` ve `FOULS_COMMITTED` (ters) oranlarını yönetir. |
| **`technique`**<br>*(Teknik)* | `Ptec` | `MC:4.6`, `AMC:4.4`, `STC:3.3`, `ML_MR:3.2`, `WBL_WBR:2.6`, `AML_AMR:2.5` | **Key (20):** Tüm oyun kurucu, kanat, `mezzala`, `af`, `cf`, `dlf`, `f9` rolleri<br>**Pref (13)** | **OOP Key (1):** `OPInvertingOutletWinger`<br>**OOP Pref (6)**<br>**Stil:** `tiki_taka (2.0)`, `vertical_tiki_taka (1.8)`, `control_possession (1.7)` | Oyuncunun **repertuar tavanı ve zorluk çarpanıdır**: vole, yarım vole, dış ayak pası, falsolu şut (`curls ball`), tek pas ve zor açılardan yapılan tüm teknik aksiyonlarda (`passing`, `finishing`, `first_touch`, `dribbling`, `crossing`) hata payını düşürür. |
| **`corners`**<br>*(Korner)* | `Pcor` | **`0.0` (`Zero-CA`)** | Rollerde yer almaz (`0`) | Rollerde yer almaz (`0`) | Köşe vuruşlarında topun istenen bölgeye (`Near Post`, `Far Post`, `Centre`, `Edge of Area`) istenen kavisle (`In-swinger` / `Out-swinger`) düşme isabetini belirler. |

#### 2.3.2. Zihinsel Özellikler (`Mental Attributes` — 14 Kolon)

| Kolon (`Attributes`) | FourCC | `CA` Maliyet Ağırlıkları (`[REF-CA]`) | `IP` Rolleri (`Key` / `Pref` / `Duty`) (`[REF-ROL]`) | `OOP` Rolleri & Stil DNA (`[REF-ROL]`) | Maç Motoru (`3D ME` & `QME`) ve Antrenman (`[REF-ANT]`) Etkisi |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **`aggression`**<br>*(Agresiflik)* | `Pagg` | **`0.0` (`Zero-CA`)** | **Key (3):** `bwm`, `pressing_fwd`, `def_winger`<br>**Pref (10)** \| **Duty Key:** `Stopper` | **OOP Key (7):** Tüm `Stopping` ve `Pressing` rolleri<br>**Stil:** `route_one (1.6)`, `gegenpress (1.5)` | Oyuncunun ikili mücadeleye girme ve rakibe basma **isteğini/sıklığını** belirler. *(Dikkat: `aggression` tek başına kart/faul demek değildir; yüksek `aggression` + yüksek `tackling`/`decisions` top kazandırır; yüksek `aggression` + düşük `decisions` + yüksek `dirtiness` kırmızı kart üretir).* |
| **`anticipation`**<br>*(Önsezi)* | `Pant` | `WBL_WBR:4.8`, `DM:4.7`, `MC:4.6`, `DC:4.3`, `DL_DR:4.2`, `STC:4.0`, `ML_MR:3.3`, `AMC:3.3`, `AML_AMR:2.9`, `GK:2.8` | **Key (18)**, **Pref (28)** *(46/50 rolde aktif!)*<br>**Duty Key:** `Cover` \| **Duty Pref:** `Defend` | **OOP Key (30)**, **OOP Pref (7)** *(37/39 OOP rolünde aktif!)*<br>**Stil:** `gegenpress (1.6)`, `vertical_tiki_taka (1.6)`, `route_one (1.6)` | Rakibin veya takım arkadaşının bir sonraki pasını/hareketini top ayaktan çıkmadan **kaç milisaniye önce** okuyacağını belirler. Savunmada pas arası (`interceptions`), hücumda (`poacher`/`af`) seken toplara ve ara paslara ilk tepkiyi veren özelliktir. |
| **`bravery`**<br>*(Cesaret)* | `Pbra` | `GK:5.1`, `DC:2.8` *(Diğer 8 pozisyonda `0.0`)* | **Key (6):** `bwm`, `target_fwd`, `pressing_fwd`, `nncb`, `nnfb`, `wide_tm`<br>**Pref (8)** \| **Duty Key:** `Stopper` | **OOP Key (7):** Tüm `Stopping` ve `Pressing` rolleri<br>**Stil:** `park_the_bus (1.9)`, `route_one (1.7)` | Sakatlanma riski olan pozisyonlarda (kalecinin forvetin ayağına yatması, kafa topuna tekmeye karşı uzanma, şutun önüne 몸 koyma / `blocks`) oyuncunun geri çekilmemesini sağlar. |
| **`composure`**<br>*(Soğukkanlılık)* | `Pcmp` | `STC:5.2`, `MC:3.4`, `DM:3.1`, `DC:2.6`, `AMC:2.6`, `GK:1.8` | **Key (21)**, **Pref (19)** *(40/50 rolde aktif!)*<br>**Duty Pref:** `Attack`, `Float` | **OOP Key (4)**, **OOP Pref (6)**<br>**Stil:** `tiki_taka (1.9)`, `control_possession (1.9)` | **Rakip baskısı (`Pressing`) ve kritik pozisyon (`1v1` / son dakika) altında** oyuncunun `finishing`, `passing`, `first_touch` ve `decisions` özelliklerinin **ne kadar kırpılacağını (ceza alacağını)** belirler. Düşük `composure`, baskı altında panik şut/pas üretir. |
| **`concentration`**<br>*(Konsantrasyon)* | `Pcon` | `GK:5.4`, `DL_DR:5.2`, `WBL_WBR:3.5`, `DM:3.4`, `DC:3.3`, `AML_AMR:2.4` | **Key (9):** Tüm kaleci, bek ve `dm`/`anchor`/`half_back` rolleri<br>**Pref (17)** \| **Duty Key:** `Defend` | **OOP Key (14)**, **OOP Pref (12)**<br>**Stil:** `park_the_bus (2.1)`, `catenaccio (2.0)` | `decisions` ve `positioning` özelliklerinin **maçın 1. dakikasından 90+ dakikasına kadar dalgalanmadan** korunmasını sağlar. Düşük `concentration`, özellikle `75.+` dakikada ve uzamsal momentum (`[REF-ME]`) aleyhte iken bireysel markaj/pozisyon hatası yaptırır. |
| **`decisions`**<br>*(Karar Alma)* | `Pdec` | **`GK:10.0`, `DC:10.0`, `DM:10.0`**, `DL_DR:8.0`, `MC:7.7`, `WBL_WBR:7.4`, `AMC:5.1`, `ML_MR:4.6`, `AML_AMR:4.4`, `STC:3.7` | **Key (25)**, **Pref (22)** *(47/50 rolde aktif!)*<br>**Duty Key:** `Stopper`, `Cover`, `Support`, `Float` | **OOP Key (14)**, **OOP Pref (24)**<br>**Stil:** 6 stilde (`1.4..1.9`) ana DNA | **Oyun motorunun merkez işlemcisidir (`CA` ağırlığı en yüksek zihinsel özellik):** Her `tick` içinde oyuncunun *"pas mı atayım, şut mu çekeyim, çalım mı deneyeyim, kademeye mi gireyim?"* karar ağacında doğru dalı seçme olasılığını belirler. |
| **`determination`**<br>*(Kararlılık)* | `Pdet` | **`0.0` (`Zero-CA`)** | Rollerde yer almaz (`0`) *(Saf sıfır maliyetli çarpan!)* | Rollerde yer almaz (`0`) | **1) Maç İçi Geri Dönüş:** Takım geriye düştüğünde (`0-1`, `0-2`) oyuncunun performans/çaba çarpanını yükseltir.<br>**2) Gelişim (`CA` Growth):** `professionalism` ve `ambition` ile birlikte antrenman gelişim hızının 3 ana sütunundan biridir.<br>**3) Koçluk (`[REF-ANT]`):** Personelde `DDB` yıldız formülünün 1/3'üdür. |
| **`flair`**<br>*(Özel Yetenek)* | `Pfla` | **`0.0` (`Zero-CA`)** | **Key (4):** `advanced_wb`, `regista`, `am`, `trequartista`<br>**Pref (11)** \| **Duty Key:** `Float` \| **Duty Pref:** `Attack` | **OOP Pref (3):** `Outlet` rolleri | Oyuncunun **öngörülemezliğini (yaratıcı sürpriz katsayısını)** belirler; rakip savunmanın `anticipation` özelliğini kırarak beklenmedik topuk pası, rabona, aşırtma veya ani çalım denemelerini (`technique` ve `vision` destekliyorsa başarıyla) tetikler. |
| **`leadership`**<br>*(Liderlik)* | `Plea` | **`0.0` (`Zero-CA`)** | Rollerde yer almaz (`0`) | Rollerde yer almaz (`0`) | **1) Kaptanlık & Hiyerarşi:** Kulüp kaptanı seçiminde ve soyunma odası hiyerarşisinde (`Team Leader`) birincil etkendir.<br>**2) Antrenman Çarpanı (`[REF-TE]`):** `Team Leader` olan oyuncular takımın taktiksel antrenman katkısını `1.00x` (`Other = 0.60x` yerine) çarpar.<br>**3) Saha İçi Etki:** Kaptanın yüksek `leadership` değeri, kriz anlarında takım arkadaşlarının `composure` ve `concentration` kayıplarını azaltır. |
| **`off_the_ball`**<br>*(Topsuz Alan)* | `Potb` | `STC:5.4`, `MC:3.3`, `WBL_WBR:2.7`, `AMC:2.7`, `ML_MR:2.6`, `AML_AMR:2.3` | **Key (28)**, **Pref (9)** *(Tüm hücum/destek rollerinde `Key`!)*<br>**Duty Key:** `Attack`, `Float` | **OOP Key (7):** Tüm 7 `Outlet` kontra rolü<br>**Stil:** `vertical_tiki_taka (1.9)`, `fluid_counter (1.8)`, `direct_counter (1.8)`, `tiki_taka (1.6)`, `wing_play (1.6)` | Hücumdayken top oyuncuda değilken savunmacının `marking` ve `positioning` denetiminden sıyrılıp boş koridora/pas açısına hareketlenme kalitesini belirler. Gol pozisyonuna girme sıklığının (`xG per 90`) en büyük belirleyicisidir. |
| **`positioning`**<br>*(Pozisyon Alma)* | `Ppos` | **`DC:8.1`**, `DM:5.6`, `DL_DR:4.6`, `GK:4.2`, `MC:3.0` | **Key (19)**, **Pref (8)** *(Tüm savunma ve kaleci rollerinde `Key`!)*<br>**Duty Key:** `Defend` \| **Duty Pref:** `Cover` | **OOP Key (24)**, **OOP Pref (8)**<br>**Stil:** `park_the_bus (2.4)`, `catenaccio (2.3)`, `direct_counter (1.7)`, `fluid_counter (1.6)`, `control_possession (1.5)` | **Savunmadaki `off_the_ball` karşılığıdır:** Top rakipteyken oyuncunun savunma çizgisini bozmama, pas koridorunu kapatma ve doğru açıda durma becerisidir. *(Dikkat: Hücum pozisyon alması `off_the_ball`, savunma pozisyon alması `positioning`'dir).* |
| **`teamwork`**<br>*(Takım Oyunu)* | `Ptea` | `DM:2.8`, `DL_DR:2.6` *(Diğer 8 pozisyonda `0.0`!)* | **Key (24)**, **Pref (7)**<br>**Duty Key:** `Support` | **OOP Key (20)**, **OOP Pref (3)**<br>**Stil:** `gegenpress (1.7)`, `catenaccio (1.7)`, `control_possession (1.6)`, `tiki_taka (1.5)` | Oyuncunun **verilen taktiksel talimatlara (`Team/Player Instructions`) ne kadar sadık kalacağını** ve kendi bencil aksiyonu (zor açıdan şut) yerine daha müsait takım arkadaşına pas vermeyi seçme oranını belirler. |
| **`vision`**<br>*(Vizyon)* | `Pvis` | `MC:6.2`, `AMC:5.0`, `DM:3.8`, `ML_MR:2.5` | **Key (14):** Tüm oyun kurucu (`dlp`, `ap`, `regista`, `enganche`, `trequartista`, `wp`, `b2b_pm`), `mezzala`, `cf`, `libero`, `f9`<br>**Pref (9)** \| **Duty Key:** `Float` | **OOP Key (1):** `OPCentralOutletMid`<br>**Stil:** `vertical_tiki_taka (2.0)`, `tiki_taka (1.9)`, `control_possession (1.7)` | Oyuncu topu aldığında sahadaki **potansiyel pas/koşu koridorlarının kaç tanesini görebildiğini** belirler (`vision` pası görür, `decisions` en doğrusunu seçer, `passing` + `technique` ise o pası adrese teslim eder). |
| **`work_rate`**<br>*(Çalışkanlık)* | `Pwor` | `DM:3.7`, `WBL_WBR:3.1`, `MC:3.1`, `DL_DR:3.0`, `ML_MR:2.3` | **Key (18)**, **Pref (11)**<br>**Duty Pref:** `Support` | **OOP Key (16)**, **OOP Pref (8)**<br>**Stil:** `gegenpress (2.2)`, `direct_counter (1.8)`, `route_one (1.8)`, `wing_play (1.5)` | Oyuncunun maç boyunca **fiziksel kapasitesini (`stamina` / `pace`) ne sıklıkla devreye soktuğunu** (pres yapma, geriye koşma, bindirme yapma) belirler. Yüksek `work_rate` + düşük `stamina` oyuncunun 65. dakikada tükenmesine yol açar. |

#### 2.3.3. Fiziksel Özellikler (`Physical Attributes` — 8 Kolon)

| Kolon (`Attributes`) | FourCC | `CA` Maliyet Ağırlıkları (`[REF-CA]`) | `IP` Rolleri (`Key` / `Pref` / `Duty`) (`[REF-ROL]`) | `OOP` Rolleri & Stil DNA (`[REF-ROL]`) | Maç Motoru (`3D ME` & `QME`) ve Antrenman (`[REF-ANT]`) Etkisi |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **`acceleration`**<br>*(Hızlanma)* | `Pacc` | **7 pozisyonda (`DL_DR`, `WBL_WBR`, `MC`, `ML_MR`, `AMC`, `AML_AMR`, `STC`) tam `10.0`!**, `DM:6.7`, `GK:5.9`, `DC:5.0` | **Key (18)**, **Pref (14)**<br>**Duty Key:** `Cover`, `Attack` | **OOP Key (25)**, **OOP Pref (6)**<br>**Stil:** `direct_counter (2.0)`, `wing_play (1.8)`, `fluid_counter (1.8)`, `gegenpress (1.6)`, `vertical_tiki_taka (1.4)` | **3B Maç Motorunun en baskın fiziksel özelliğidir:** Durur halden veya yön değiştirdikten sonra maksimum hıza (`pace`) kaç saniyede ulaşıldığını belirler. İlk 5–10 metrelik patlayıcılıkta (çalım, kademe, pres, ofsayt çizgisi arkasına sarkma) `pace`'ten daha etkilidir. |
| **`agility`**<br>*(Çeviklik)* | `Pagi` | `GK:7.7`, `DL_DR:7.3`, `ML_MR:7.2`, `MC:7.0`, `DM:6.7`, `WBL_WBR:6.6`, `AML_AMR:6.1`, `AMC:5.4`, `DC:5.2`, `STC:5.2` | **Key (8)**, **Pref (25)**<br>**Duty Pref:** `Float` | **OOP Key (5)**, **OOP Pref (21)**<br>**Stil:** `tiki_taka (1.4)` | Oyuncunun hız kaybetmeden yön değiştirme, kendi etrafında dönme ve kalecilerde yere yatıp kalkma süresini belirler. `dribbling` ve `acceleration` ile doğrudan çarpımsal çalışır. |
| **`balance`**<br>*(Denge)* | `Pbal` | **`0.0` (`Zero-CA`)** | **Key (1):** `wide_fwd`<br>**Pref (26):** Neredeyse tüm hücum, kanat ve orta saha rolleri | **OOP Pref (7):** Tüm `Outlet` kontra rolleri | Oyuncu omuz omuza darbe aldığında (`strength` mücadelesinde) veya yüksek hızda yön değiştirirken tökezlemeden/düşmeden topu sürmeye ve şut/pas çıkarmaya devam edebilmesini sağlar (`0 CA` maliyetli gizli cevher!). |
| **`jumping_reach`**<br>*(Zıplama Erişimi)* | `Pjum` | `DC:6.0`, `STC:4.5` *(Diğer 8 pozisyonda `0.0`)* | **Key (8):** `cd`, `bpd`, `target_fwd`, `complete_fwd`, `nncb`, `wide_cb`, `ifb`, `wide_tm`<br>**Pref (3)** \| **Duty Pref:** `Stopper` | **OOP Key (4)**, **OOP Pref (4)**<br>**Stil:** `route_one (2.1)` | Oyuncunun havadaki bir topa **kafasıyla ulaşabildiği maksimum yerden yüksekliği** (`height_cm` ile entegre olarak) ifade eder. Hava topu ikili mücadelesini kimin kazanacağını `jumping_reach` (+ `bravery` + `strength` + `anticipation`), topun nereye gideceğini ise `heading` belirler. |
| **`natural_fitness`**<br>*(Doğal Kondisyon)* | `Pnat` | **`0.0` (`Zero-CA`)** | Rollerde yer almaz (`0`) | Rollerde yer almaz (`0`) | **1) Maçlar Arası Yenilenme:** Maç bittikten sonra `raw_condition` (`Pcon`) değerinin bir sonraki maça kadar ne kadar hızlı `%100`'e döneceğini belirler.<br>**2) Sakatlık Sonrası:** Sakatlıktan döndükten sonra `raw_match_sharpness` kazanım hızını artırır.<br>**3) Yaşlanma Direnci:** `30+` yaş sonrasında fiziksel özelliklerin (`pace`, `acceleration`, `stamina`) erime hızını yavaşlatır. |
| **`pace`**<br>*(Hız)* | `Ppac` | `AML_AMR:9.8`, `ML_MR:9.4`, `DL_DR:8.6`, `MC:8.4`, `AMC:8.2`, `WBL_WBR:8.0`, `STC:6.6`, `DM:4.9`, `DC:4.4` | **Key (11)**, **Pref (17)**<br>**Duty Key:** `Cover` \| **Duty Pref:** `Attack` | **OOP Key (22)**, **OOP Pref (11)**<br>**Stil:** `direct_counter (2.1)`, `wing_play (1.9)`, `fluid_counter (1.8)`, `gegenpress (1.4)` | Oyuncunun topsuz ve toplu oyunda ulaşabildiği **maksimum son sürati (m/s)** belirler (top sürerken `dribbling` özelliğine bağlı olarak hız bir miktar kırpılır). Savunma arkası uzun koşularda ve kontra geri dönüşlerinde belirleyicidir. |
| **`stamina`**<br>*(Dayanıklılık)* | `Psta` | `MC:7.6`, `DL_DR:7.1`, `WBL_WBR:6.9`, `ML_MR:6.4`, `AML_AMR:5.9`, `AMC:5.7`, `STC:5.2`, `DM:4.0`, `DC:2.3` | **Key (17)**, **Pref (14)**<br>**Duty Pref:** `Support` | **OOP Key (19)**, **OOP Pref (7)**<br>**Stil:** `gegenpress (2.0)`, `direct_counter (1.8)`, `wing_play (1.7)`, `fluid_counter (1.6)` | Maç içinde yapılan her sprint ve ikili mücadelenin `raw_condition` (`Pcon`) değerinden ne kadar götüreceğini belirler. *(Not: Maç içinde `Condition < %65` altına indiğinde oyuncunun anlık `acceleration`, `pace`, `decisions` ve `concentration` değerleri kademeli olarak `%15..%40` kırpılır; rakip stadyumun rakımı `altitude_ft` yüksekse `stamina` önemi ikiye katlanır).* |
| **`strength`**<br>*(Güç)* | `Pstr` | `DL_DR:6.0`, `DM:5.9`, `DC:5.6`, `STC:5.6`, `WBL_WBR:5.1`, `MC:5.1`, `GK:3.7`, `ML_MR:3.6`, `AML_AMR:3.2`, `AMC:3.0` | **Key (9)**, **Pref (11)**<br>**Duty Key:** `Stopper` | **OOP Key (7)**, **OOP Pref (15)**<br>**Stil:** `route_one (2.0)`, `park_the_bus (1.8)`, `catenaccio (1.7)`, `direct_counter (1.5)` | Top saklama (`Hold Up Ball`), sırtı dönük oyun (`Target Forward`), kornerlerde alan koruma ve omuz omuza ikili mücadelelerde rakibi fiziksel olarak ekarte etme gücünü belirler. |

#### 2.3.4. Kaleci Özellikleri (`Goalkeeping Attributes` — 11 Kolon)

*(Not: Kaleci özelliklerinin tamamı saha oyuncularında `0.0 CA` ağırlığındadır; yalnızca `GK` pozisyonunda `CA` tüketir).*

| Kolon (`Attributes`) | FourCC | `GK CA` Ağırlığı | `IP` & `OOP` Rolleri | Maç Motoru (`3D ME` & `QME`) Etkisi |
| :--- | :---: | :---: | :--- | :--- |
| **`reflexes`** *(Refleksler)* | `Pref` | **`7.8`** | **IP Key:** `sk`, `gk`, `nngk` \| **OOP Key:** `OPGK`, `OPLineGK` | Yakın mesafe şutlarda, seken/yön değiştiren toplarda ve 1v1 vuruşlarda kalecinin reaksiyon süresini (ms) belirleyen en kritik kurtarış özelliğidir. |
| **`handling`** *(Elle Kontrol)* | `Phan` | **`7.7`** | **IP Key:** `gk`, `nngk` (`Pref: sk`) \| **OOP Key:** `OPGK`, `OPLineGK` | Kurtarılan şutun kalecinin elinden **sekip (`rebound` / ikinci şans) rakip forvetin önüne düşmeme**, tek hamlede tutulma olasılığını belirler (yağmurlu/ıslak zeminde `weather` nedeniyle önemi artar). |
| **`aerial_reach`** *(Hava Hakimiyeti)* | `Paer` | **`5.5`** | **IP Key:** `gk`, `nngk` (`Pref: sk`) \| **OOP Key:** `OPLineGK` | Kalecinin yan toplarda ve kornerlerde (`height_cm` ile birlikte) elleriyle ulaşabildiği maksimum dikey/yatay zarfı belirler. |
| **`command_of_area`** *(Alan Hakimiyeti)* | `Pcoa` | **`4.9`** | **IP Key:** `sk`, `gk`, `nngk` \| **OOP Key:** `OPGK` | Kalecinin ceza sahası içindeki yan toplara çıkıp çıkmama kararını ve savunma oyuncularıyla çarpışmadan alanı sahiplenme otoritesini belirler. |
| **`kicking`** *(Degaj)* | `Pkic` | **`4.3`** | **IP Key:** `sk`, `gk`, `nngk` | Kalecinin aut ve degaj vuruşlarındaki **maksimum mesafesini** ve uzun topun hedef bölgeye gitmesini (`passing` ve `vision` isabeti tamamlar) belirler. |
| **`communication`** *(İletişim)* | `Pcom` | **`3.7`** | **IP Key:** `gk`, `nngk` (`Pref: sk`) \| **OOP Pref:** `OPGK`, `OPLineGK` | Kalecinin önündeki savunma dörtlüsünü/beşlisini organize etme becerisidir; savunma hattının ofsayt tuzağı ve `positioning`/`marking` hatalarını azaltır (**ortak dil `spoken_languages` yoksa etkisi kırpılır!**). |
| **`one_on_ones`** *(Bire Bir)* | `Pooo` | **`2.9`** | **IP Key:** `sk` (`Pref: gk, nngk`) \| **OOP Key:** `OPSweeperKeeper` | Rakip hücumcu savunma arkasına sarkıp kaleciyle karşı karşıya kaldığında kalecinin açıyı daraltma, doğru anda açılma ve vücudunu büyütme başarısını belirler. |
| **`throwing`** *(Elle Oyun Kurma)* | `Pthr` | **`2.5`** | **IP Pref:** `sk`, `gk` | Kalecinin topu eliyle hızlıca kanatlara/beklere (`Counter-Attack` / `Distribute Quickly`) atarkenki menzil ve isabetini belirler. |
| **`eccentricity`** *(Eksantriklik)* | `Pecc` | **`0.0` (`Zero-CA`)** | Rollerde yer almaz (`0`) | Kalecinin ceza sahası dışına çıkıp çalım deneme, sürpriz pas atma gibi beklenmedik/riskli hareketler yapma eğilimidir (`Sweeper Keeper (Attack)` rolünde yüksek `decisions` ile birleşirse oyun kurulumuna katkı verir, düşük `decisions` ile birleşirse boş kaleye gol yedirir). |
| **`rushing_out`** *(Çıkış Eğilimi)* | `Prus` | **`0.0` (`Zero-CA`)** | **IP/OOP Key:** `sweeper_keeper` / `OPSweeperKeeper` | Savunma arkasına atılan ara paslarda ve uzun toplarda kalecinin çizgisini terk edip süpürücü olarak topa koşma eğilimini (`acceleration` ve `decisions` ile birlikte) belirler. |
| **`punching`** *(Yumruklama Eğilimi)* | `Ppun` | **`0.0` (`Zero-CA`)** | Rollerde yer almaz (`0`) | Kalabalık yan toplarda kalecinin topu tutmayı denemek (`handling`) yerine güvenli şekilde yumruklayarak uzaklaştırmayı seçme eğilimidir (düşük `handling` olan kalecilerde yüksek `punching` avantajlıdır). |

#### 2.3.5. `Attributes` İçindeki 5 Gizli Maç/Sakatlık Özelliği + Sağ/Sol Ayak (`left_foot`, `right_foot`)

| Kolon | FourCC | `CA` Maliyeti | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :---: | :---: | :--- |
| **`consistency`**<br>*(İstikrar)* | `Pcon` / `Pcst` | **`0.0` (`Zero-CA`)** | **Maç Öncesi Zar Atışı (Teknik & Zihinsel Tavan Çarpanı):** Her maçın başında motor her oyuncu için `consistency` (`1..20`) değerine bağlı bir olasılık dağılımından zar atar. *(Dikkat: `consistency` fiziksel özellikleri etkilemez!)*:<br>- `consistency = 20` olan oyuncu maçların `%85`'inde kendi tam `technical`/`mental` özellikleriyle oynar.<br>- `consistency <= 8` olan oyuncu maçların büyük kısmında teknik ve zihinsel özelliklerinden **`-1` ila `-3` puan (`-5..15` iç birim) kırpılmış** olarak sahaya çıkar! Maç oynadıkça çok yavaş (`+1..2`) gelişebilir. |
| **`important_matches`**<br>*(Önemli Maçlar)* | `Pimp` | **`0.0` (`Zero-CA`)** | **Kupa Finalleri, Derbiler (`derby.xml`), Şampiyonluk/Küme Düşme Maçları ve K플레이-Off Maçlarında** devreye girer: Yüksek `important_matches` (`15..20`) oyuncunun `composure`, `decisions` ve `concentration` performansına pozitif çarpan verirken; düşük değer (`1..7`) oyuncunun büyük maçlarda sahada kaybolmasına ve bireysel hata yapmasına neden olur. Gözlemci raporunda `Likes/Dislikes Big Matches` olarak görünür. |
| **`injury_proneness`**<br>*(Sakatlığa Eğilim)* | `Pinj` | **`0.0` (`Zero-CA`)** | Antrenmanlarda (`[REF-ANT]`) ve maç içi ikili mücadelelerde yapılan her **Sakatlık Zar Atışında (`Injury Roll`)** doğrudan olasılık çarpanıdır. `18..20` olan oyuncu yüksek yoğunluklu antrenmanda veya sert zeminde (`stadium.pitch_condition`) sık sık kas/bağ sakatlığı yaşar. `TSF_INJURY_RISK (-60)` üzerinden AI seçimini etkiler. |
| **`versatility`**<br>*(Çok Yönlülük)* | `Pver` | **`0.0` (`Zero-CA`)** | **1) Yeni Pozisyon Öğrenme (`Retraining`):** Bireysel antrenmanda oyuncuya yeni bir pozisyon çalıştırıldığında o pozisyonun `1` den `20` (`Natural`) seviyesine çıkma hızını doğrudan belirler.<br>**2) Yabancı Pozisyonda Oynama:** Oyuncu bilmediği (`Makeshift`/`Unconvincing`) bir pozisyona konulduğunda aldığı `decisions` ve `positioning` cezasını hafifletir. |
| **`dirtiness`**<br>*(Çirkeflik / Competitive Streak)* | `Pdir` | **`0.0` (`Zero-CA`)** | Oyuncunun kazanmak için kural dışı yollara başvurma (formasından çekme, hakem görmeden vurma, taktik faul, zaman geçirme) eğilimidir. Hakemin `Oref` ve `Odis` (`official.xml`) değerleri yüksekse ve `VAR` varsa sarı/kırmızı kart olasılığını ciddi oranda artırır. |
| **`left_foot` & `right_foot`**<br>*(Sol ve Sağ Ayak)* | `Plft`, `Prft` | **Zayıf ayak `[REF-CA]` içinde `0.18 × (WF - 1)`** (Çok yüksek `CA` maliyeti!) | **1) `CA` Maliyeti:** Güçlü ayak `20` iken zayıf ayağın `1` yerine `20` (`Either Footed`) olması, pozisyona bağlı olarak **`8` ila `18` `CA` puanı** tüketir!<br>**2) Maç Motoru Açısı:** Oyuncu zayıf ayağıyla pas/şut/orta yaptığında `passing`, `finishing`, `crossing` ve `technique` özellikleri `(WeakFoot / 20)` oranında kırpılır; zayıf ayağı çok düşükse (`1..6`) oyuncu topu güçlü ayağına çekmek için ekstra zaman harcar ve savunmacıya kapanma fırsatı verir.<br>**3) AI Seçimi:** `TSF_LEFT_RIGHT_FOOT (+20)` (`[REF-AI]`). |


---

### 2.4. 8 Gizli Kişilik Özelliği (`Personality` — `1..20`) ve Oyuncu Karakter Arketipleri

Kaynak: [`Personality`](../fm26save/_core/models/players.py#L38-L55), [`classify_player_personality()`](../fm26save/formulas.py#L1622-L1698). Hiçbiri `CA` bütçesi tüketmez (`0 CA`), ancak oyuncunun gelişim hızından sözleşme pazarlığına, soyunma odası isyanlarından maç içi kart görmesine kadar tüm davranışsal motoru yönetirler. Mentorluk (`MentoringGroup`) yoluyla yaşlı liderlerden genç oyunculara (`14..23` yaş) aktarılabilirler.

> [!IMPORTANT]
> **Kullanıcının Özel Örneği — `loyalty` (Aidiyet / Sadakat) Nerede ve Ne Kadar İşe Yarıyor?**
> `Personality.loyalty` (`Ploy`, `1..20`) oyun motorunda tam olarak şu **6 alt sisteme** dokunur:
> 1. **Transfer İsteme ve Büyük Kulüp Aklını Çelmesi (`Unsettled by Transfer Speculation`):** Daha yüksek itibarlı (`Club.reputation`) veya Şampiyonlar Ligi'nde oynayan bir kulüp oyuncuyu izlemeye (`Declare Interest`) ya da teklif yapmaya başladığında motor `(Ambition × 1.5 - Loyalty × 1.2)` farkına bakar. Yüksek `loyalty` (`16..20`) olan oyuncu teklif reddedildiğinde teknik direktöre isyan etmez; düşük `loyalty` (`1..7`) + yüksek `ambition` (`15+`) olan oyuncu derhal transfer listesine konulmak ister ve `morale` / `Player Buy-In` (`[REF-TE]`) çöküşü yaşar (`Mercenary` / Paragöz davranışı).
> 2. **Sözleşme Yenileme ve Sadakat Primi (`[REF-EKO]` `Contract.unknown.money_a`):** Yüksek `loyalty` olan oyuncu mevcut kulübüyle sözleşme yenilerken daha makul maaş artışı (`wage_per_week`) ve daha düşük peşin imza/sadakat primi (`money_a`) kabul eder; ayrıca rakip kulübün daha yüksek maaş teklifine rağmen kendi kulübünde kalmayı tercih edebilir (`TSF_CLUB_FAVOURITE` ile birleşir).
> 3. **Serbest Kalma ve `Bosman` Kararı:** Sözleşmesinin son 6 ayına giren yüksek `loyalty` sahibi oyuncu, kulübünün yeni sözleşme teklifini beklemeye öncelik verir; düşük `loyalty` sahibi oyuncu hemen `Explore Options` / `Sign Pre-Contract` yoluna gider.
> 4. **Yedek Kalma Toleransı (`Playing Time Happiness`):** Sözleşmesindeki `squad_status` (`Star Player` / `Regular Starter`) süresinin altında oynatıldığında, yüksek `loyalty` + yüksek `professionalism` oyuncunun şikayet etme eşiğini geciktirir.
> 5. **Kulüp İkonu / Efsanesi (`Favoured Personnel`) Kazanımı:** Bir kulüpte uzun yıllar kalarak `favoured_clubs` (`(1, 10)`) ve kulübün `Favoured Personnel` listesine girme hızını çarpar.
> 6. **Kişilik Etiketi (`Personality Label`):** `loyalty >= 18` (ve `ambition` `6..7` civarı) ise `Devoted` (Adanmış) veya `Very Loyal`; `loyalty >= 15` ise `Loyal` (Sadık); `loyalty <= 6` ve `ambition >= 16` ise `Mercenary` (Paragöz); `loyalty >= 15` tüm diğer pozitif özelliklerle birleştiğinde ise en üst seviye olan **`Model Citizen` (Örnek Vatandaş)** etiketini açar.

| Kişilik Kolonu (`Personality`) | FourCC | Tip / Aralık | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :---: | :---: | :--- |
| **`adaptability`**<br>*(Uyum Yeteneği)* | `Pada` | `uint8` (`1..20`) | **1) Yabancı Ülkeye/Kültüre Transfer:** Oyuncu farklı dil/kültür/yaşam standardındaki (`nation.xml` $\rightarrow$ `Nsod` `State of Development`) bir ülkeye transfer olduğunda ilk **3–12 aydaki** saha içi performans cezasını (`consistency` ve `decisions` kırpılması) ve **"Vatan Hasreti (`Homesickness`)"** krizini önler.<br>**2) Dil Öğrenme Hızı:** Yeni ülkenin dilini (`spoken_languages`) öğrenme süresini (`language.xml` $\rightarrow$ `Ldff` zorluğuna karşı) doğrudan kısaltır (`intelligence` ile birlikte). |
| **`ambition`**<br>*(Hırs)* | `Pamb` | `uint8` (`1..20`) | **1) `CA` Gelişim Hızı:** `professionalism` (`%50` ağırlık), `determination` (`%25`) ve `ambition` (`%25`) üçlüsü oyuncunun antrenman ve maçlardan `CA` kazanma hızını belirler.<br>**2) Transfer & Maaş Talebi:** Yüksek `ambition` (`16..20`), oyuncunun sürekli daha üst lig/kupa hedefleyen kulüplere gitmek istemesine ve sözleşmede yüksek maaş/bonus (`[REF-EKO]`) talep etmesine yol açar (`loyalty` düşükse kriz çıkarır). |
| **`loyalty`**<br>*(Aidiyet / Sadakat)* | `Ploy` | `uint8` (`1..20`) | Yukarıdaki özel kutuda detaylandırıldığı üzere: Transfer spekülasyonlarına direnç, sözleşme yenileme kolaylığı, `money_a` (sadakat primi) indirimi, yedek kalma sabrı ve `Model Citizen` / `Loyal` / `Mercenary` arketip sınıflandırması. |
| **`pressure`**<br>*(Baskıya Dayanıklılık)* | `Ppre` | `uint8` (`1..20`) | **1) Medya ve Şampiyonluk Stresi:** Basın toplantılarındaki (`journalist.xml`) sert yorumlarda, taraftar (`Cspt` düşük `Patience`, `Cste` düşük `Temperament`) protestolarında ve şampiyonluk/küme düşme yarışının son haftalarında oyuncunun `morale` ve saha içi `composure` çöküşünü engeller.<br>**2) Maç İçi Konuşmalar (`Team Talks`):** Devre arası ve maç sonu sert/talepkar konuşmalarda (`Demand More`, `Berate`) düşük `pressure` sahibi oyuncu `Stressed` / `Anxious` olurken, yüksek `pressure` sahibi oyuncu `Fired Up` / `Motivated` olur. |
| **`professionalism`**<br>*(Profesyonellik)* | `Ppro` | `uint8` (`1..20`) | **Oyuncu Gelişiminin En Önemli Gizli Sütunu (`~%50` ağırlık):**<br>**1) Antrenman Puanı:** Haftalık antrenman gelişim çarpanının en büyük belirleyicisidir; `professionalism >= 18` (`Model Professional` / `Professional`) olan oyuncu `PA` tavanına en hızlı ulaşan oyuncudur.<br>**2) Maç Dışı Disiplin:** Antrenman kaçırma (`AWOL`), gece hayatı skandalları ve tatil dönüşü kilo/kondisyon kaybını sıfırlar.<br>**3) Yaşlılıkta Koruma:** `30+` yaş sonrasında `CA` erimesini yavaşlatır. |
| **`sportsmanship`**<br>*(Sportmenlik)* | `Pspo` | `uint8` (`1..20`) | **Saha İçi Fair-Play:** Düşük `sportsmanship` (`1..6`) oyuncunun ceza sahasında **kendini yere atma (`Diving` / aldatmaya yönelik sarı kart)**, sakatlık numarası yapma, topu rakibe geri vermeme ve zaman geçirme eğilimini artırır. `dirtiness` ile birleştiğinde hakem (`official.xml`) kararlarında cezalandırılma riskini büyütür. |
| **`temperament`**<br>*(Mizaç / Sinir Kontrolü)* | `Ptem` | `uint8` (`1..20`) | **1) Kart ve İhraç Riski:** Rakip sert faul yaptığında veya hakem aleyhte karar verdiğinde düşük `temperament` (`1..7`) oyuncunun **hakeme itirazdan sarı kart** veya **rakibe kafa/tekme atmaktan doğrudan kırmızı kart (`Violent Conduct`)** görme olasılığını katlar.<br>**2) Eleştiriye Tepki:** Teknik direktör oyuncuyu antrenman/performans düşüklüğü veya para cezası (`Fine Player`) nedeniyle uyardığında düşük `temperament` oyuncunun kavga çıkarmasına yol açar. |
| **`controversy`**<br>*(Tartışmacılık / Medya Polemiği)* | `Pcnt` | `uint8` (`1..20`) | *(Ters ölçek: `1` en uyumlu, `20` en проблемli!)* Yüksek `controversy` (`15..20` — `Outspoken` / `Volatile` / `Confrontational`) olan oyuncu mutsuz olduğunda bunu soyunma odası içinde tutmak yerine **doğrudan basına (`media_source.xml`) sızdırır**, teknik direktörü medyada eleştirir ve sosyal gruplarda (`Social Groups`) kutuplaşma yaratır. |

---

### 2.5. 15 Pozisyon Yetkinliği (`Positions` — `1..20`) ve Yan Kolonlar

Kaynak: [`Positions`](../fm26save/_core/models/players.py#L171-L208).

| Kolon Adı (`Positions`) | FourCC | Tip / Aralık | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :---: | :---: | :--- |
| `gk`, `sw`, `dl`, `dc`, `dr`, `wbl`, `wbr`, `dm`, `ml`, `mc`, `mr`, `aml`, `amc`, `amr`, `st` | `Ppgk`, `Ppsw`, `Ppdl`, `Ppdc`, `Ppdr`, `Ppwl`, `Ppwr`, `Ppdm`, `Ppml`, `Ppmc`, `Ppmr`, `Ppal`, `Ppam`, `Ppar`, `Ppst` | `uint8` (`1..20`) | **1) `CA` Maliyet Ağırlığı (`[REF-CA]`):** Oyuncunun `>= 15` olduğu her pozisyon, o pozisyonun `CA_POSITION_WEIGHTS_10` tablosundaki ağırlıklarını aktif hale getirir.<br>**2) Maç Motoru `Decisions` ve `Positioning` Çarpanı (`[REF-ROL]`):** Oyuncu `20` (`Natural`) olmadığı bir koltuğa konulduğunda rol uyum skoru ve maç içi `decisions`/`positioning`/`off_the_ball` özellikleri yetkinlik çarpanıyla (`Accomplished 0.93x`, `Competent 0.84x`, `Unconvincing 0.72x`, `Makeshift 0.55x`) kırpılır.<br>**3) Yapay Zeka Seçimi (`[REF-AI]`):** `TSF_POSITION_ABILITY (+150)` ile kadro seçiminin **1 numaralı** belirleyicisidir. *(Not: `sw` / Libero-Sweeper eski uyumluluk kolonu olup modern motorda `dc` + `libero` rolüyle birleşmiştir).* |

---

### 2.6. Oyuncu Oyun İçi Tercihleri (`Trait` / `PPM` — 64-Bit Bitmask & `player.xml` `PM01..PM63`)

Kaynak: [`Trait`](../fm26save/_core/models/players.py#L211-L250) (`uint64` bitmask) ve `editor.fmf/player.xml` (`PM01..PM63`).
**Genel Kural:** `PPM` (`Player Preferred Moves`) oyuncuya ekstra yetenek **vermez**, ancak 3B Maç Motorunun karar ağacında (`Decision Tree`) belirli bir aksiyon dalının seçilme olasılığını (`prior probability`) **`+25%` ila `+60%`** artırır veya azaltır! Ayrıca `[REF-AI]` içinde `TSF_PPMS (+25)` faktörüyle rol uyumuna puan katar.

| Bit / FourCC Grubu | Kayıt İsimleri (`Trait` / `player.xml`) | 3B Maç Motoru Karar Ağacındaki (`simatch.fmf`) Tam Etkisi |
| :--- | :--- | :--- |
| **Koşu ve Koridor Tercihleri**<br>(`PM01..PM11`, `PM59`) | `runs_with_ball_down_left` (`Bit 0`), `runs_with_ball_down_right` (`Bit 1`), `runs_with_ball_through_centre` (`Bit 2`), `gets_into_opposition_area` (`Bit 3`), `moves_into_channels` (`Bit 4`), `gets_forward_whenever_possible` (`Bit 5`), `stays_back_at_all_times` (`PM08`), `cuts_inside` (`PM09`/`PM56`/`PM57`), `hugs_line` (`PM11`), `arrives_late_in_box` (`PM10`), `plays_with_back_to_goal` (`PM59`) | Taktiksel rolün (`IP Role`) varsayılan koşu vektörlerini ezer/modifiye eder: Örn. `gets_into_opposition_area` ve `arrives_late_in_box` orta saha oyuncusunun `off_the_ball` tetiklemesini ceza sahası içine yönlendirir; `cuts_inside` kanat oyuncusunun çizgiye inmek (`crossing`) yerine iç koridora (`finishing`/`long_shots`) yönelme olasılığını artırır; `moves_into_channels` stoper ile bek arasındaki yarı-uzaya (`half-space`) koşu attırır. |
| **Top Sürme ve Çalım Tercihleri**<br>(`PM06`, `PM07`, `PM32..PM36`) | `runs_with_ball_often` (`Bit 11`), `runs_with_ball_rarely` (`Bit 12`), `knocks_ball_past_opponent` (`PM35`), `stops_play` (`Bit 9`), `dwells_on_ball` (`PM09`) | `runs_with_ball_often` dripling frekansını artırırken; `knocks_ball_past_opponent` oyuncunun teknik çalım (`dribbling`) yerine topu rakibin yanından atıp saf `acceleration`/`pace` farkıyla geçmeyi denemesini sağlar. `dwells_on_ball` karar süresini uzatarak rakip prese yakalanma riskini artırır. |
| **Pas ve Oyun Kurma Tercihleri**<br>(`PM12..PM16`, `PM38`, `PM47`, `PM52`, `PM60`) | `plays_short_simple_passes` (`Bit 6`), `tries_killer_balls_often` (`Bit 7`), `plays_one_twos` (`PM12`), `dictates_tempo` (`Bit 10`), `switches_ball_to_other_flank` (`PM47`), `comes_deep_to_get_ball` (`Bit 9`), `looks_for_pass_rather_than_shooting` (`Bit 10`), `plays_no_through_balls` (`PM15`), `tries_long_range_passes` (`PM38`), `bring_ball_out_of_defence` (`PM60`) | `tries_killer_balls_often` ara pas (`through ball`) deneme eşiğini düşürür (`vision` ve `passing` yüksekse asist patlaması yapar, düşükse top kaybı üretir). `dictates_tempo` takımın tempo ayarını oyuncunun kendi `decisions` kararına bırakır. `comes_deep_to_get_ball` forveti ön libero bölgesine çekerek rakip stoperi peşinden sürükler. |
| **Bitiricilik ve Şut Tercihleri**<br>(`PM17..PM23`, `PM37`, `PM39..PM42`, `PM53`) | `shoots_from_distance` (`Bit 8`), `shoots_with_power` (`Bit 9`), `places_shots` (`Bit 10`), `curls_ball` (`Bit 11`), `likes_to_round_keeper` (`Bit 12`), `likes_to_lob_keeper` (`PM21`), `tries_first_time_shots` (`PM39`), `refrains_from_taking_long_shots` (`PM53`), `hits_free_kicks_with_power` (`PM40`) | **1v1 ve Şut Fiziğini Değiştirir:**<br>- `places_shots` (Plase Şut): Şut hızını azaltıp köşe isabetini artırır (`finishing + composure + technique >= 15` ise `xG` üstü gol oranını en çok artıran `PPM`'dir!).<br>- `shoots_with_power` (Sert Şut): Köşe isabeti yerine top hızını maksimize eder (`finishing` orta ama `strength`/`technique` yüksekse etkilidir).<br>- `likes_to_round_keeper`: 1v1'de şut çekmek yerine `dribbling` + `acceleration` ile kaleciyi çalımlamayı dener.<br>- `curls_ball`: Şut ve ortalara ekstra falso (`Magnus` kuvveti) verir. |
| **Savunma, Fiziksel ve Karakter Tercihleri**<br>(`PM24..PM31`, `PM43..PM58`, `PM61..PM63`) | `dives_into_tackles` (`Bit 13`), `does_not_dive_into_tackles` (`Bit 14`), `marks_opponent_tightly` (`PM24`), `argues_with_officials` (`PM26`), `winds_up_opponents` (`PM25`), `likes_to_try_to_beat_offside_trap` (`Bit 13`), `uses_outside_of_foot` (`PM30`), `avoids_using_weaker_foot` (`PM31`), `possesses_long_flat_throw` (`PM55`), `uses_long_throw_to_start_counters` (`PM62`) | - `dives_into_tackles`: Kayarak müdahale sıklığını artırır (düşük `tackling`/`decisions` varsa penaltı ve kart yaptırır).<br>- `does_not_dive_into_tackles`: Oyuncunun ayakta kalmasını sağlar (hızlı kanatlara karşı bekler için çok değerlidir).<br>- `likes_to_try_to_beat_offside_trap`: Savunma arkasına koşu zamanlamasını (`anticipation` + `off_the_ball` + `acceleration`) tetikler.<br>- `uses_outside_of_foot` (Trivela): Zayıf ayağı kullanmak yerine güçlü ayağın dışıyla pas/şut atarak zayıf ayak cezasını bypass eder! |

---

### 2.7. Konuşulan Diller (`spoken_languages`) ve Tüm `PersonBlock` İlişki Çiftleri (`(kind, role)`)

Kaynak: [`enrichment.py`](../fm26save/enrichment.py#L1-L260) (`PersonBlock` `(kind, role)` kayıtları) ve `editor.fmf/language.xml` (`12` alan).

> [!IMPORTANT]
> **Kullanıcının Özel Örneği — Oyuncunun Konuştuğu Diller (`spoken_languages` `(7, 18)`) ve Dil Tablosu (`language.xml`) Nerede ve Ne Kadar İşe Yarıyor?**
> Kayıt dosyasında her kişinin `PersonBlock` dizisinde **`(kind=7, role=18)`** çifti altında konuştuğu dil ID'leri ve **yetkinlik seviyesi (`1..100` iç ölçek / `1..10` editör ölçeği: `Basic` `<40` vs `Fluent` `>=70`)** tutulur. Ayrıca `editor.fmf/language.xml` tablosunda her dilin **5 kritik parametresi** vardır:
> - **`Ldff` (`Language Difficulty` — Dil Zorluğu `1..20`):** Bir oyuncunun o dili sıfırdan öğrenmesinin kaç gün/ay süreceğini belirler. Süre formülü: $\text{Öğrenme Süresi} \propto \text{Ldff} / (\text{Adaptability} + \text{Intelligence})$. Kulüp oyuncuyu **"Dil Kursuna Gönder (`Send on Intensive Language Course`)"** aksiyonuna sokarsa öğrenme hızı **`2.0x`** katlanır (`~2.000£–5.000£` maliyetle).
> - **`Linf` (`Language Influence` — Dil Etkisi `1..20`) & `Lfam`/`Lgro`/`Lsub` (Dil Ailesi / Grubu / Alt Grubu):** Ortak dil ailesindeki diller (örn. İspanyolca $\leftrightarrow$ Portekizce $\leftrightarrow$ İtalyanca) birbirini öğrenirken **`0.50x..0.65x` zorluk indirimi** alır ve temel seviyede anlaşabilir!
>
> **Dil Bilmenin / Bilmemenin Oyun Motorunda Dokunduğu 6 Doğrudan Alan:**
> 1. **3B Maç Motoru Saha İçi İletişim Cezası (`simatch.fmf`):** Kalecinin (`communication` özelliği) ve savunma liderinin (`leadership`) önündeki savunma hattıyla ortak bir dili (en az `Basic` seviyesinde) **konuşamaması**, savunma çizgisinin uyumunu, ofsayt tuzağı zamanlamasını ve kademe (`positioning` / `marking`) paylaşımını doğrudan kırpar!
> 2. **Yapay Zeka Kadro Seçimi (`[REF-AI]` `TSF_INTEGRATION` `+15`):** Takım diliyle hiç ortak dili olmayan yeni transfer, dil öğrenene kadar `TSF_INTEGRATION` puanından mahrum kalır.
> 3. **FM27 `Player Buy-In` ve Antrenman Katkısı (`[REF-TE]`):** Dil bilmeyen oyuncu teknik direktörün takım konuşmalarını (`Team Talks`) ve karmaşık taktiksel talimatları (`Tactical Complexity`) tam anlayamadığı için `Buy-In` ve `Training Contribution` kazanımı ilk aylarda düşüktür; kadroda aynı dili konuşan bir takım arkadaşı varsa (`Send Player to Help Settle`) bu ceza `%50` azalır.
> 4. **Soyunma Odası Sosyal Grupları (`Social Groups`):** Oyuncular soyunma odasında `Core Social Group` ve `Secondary Social Group` kümelerine ayrılırken **1 numaralı kümeleme kriteri ortak dildir (`spoken_languages`)** (ardından yaş, uyruk ve `Personality` benzerliği gelir).
> 5. **Gözlemcilik (`Scouting Knowledge`) ve Koçluk:** Bir gözlemcinin (`Scout`) veya antrenörün bildiği her dil, o dili konuşan ülkelerdeki **Ülke Bilgisi (`Nation Knowledge %`)** tabanını yükseltir ve o bölgedeki gizli özellikleri daha hızlı açmasını sağlar.
> 6. **Vatandaşlık Kazanımı (`Gain Nationality`):** Bazı ülkelerde (`nation.xml`) vatandaşlık süresini (`Nygc`) dolduran oyuncunun pasaport alabilmesi için ülkenin resmi dilini (`Nlan`) en az `Basic` seviyesinde konuşması şarttır.

#### `PersonBlock` İlişki ve Bağlantı Çiftleri Tablosu (`enrichment.py`)

| `(kind, role)` Çifti | Kolon / İlişki Adı | Değer (`target_id`, `level_1_100`) | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :--- | :---: | :--- |
| **`(7, 18)`** | `spoken_languages` *(Konuşulan Diller)* | `language_id`, `proficiency` (`1..100`) | Yukarıda detaylandırılan 6 motor alanı (Saha içi iletişim, `TSF_INTEGRATION`, `Buy-In`, Sosyal Gruplar, Gözlemcilik bilgisi, Vatandaşlık). |
| **`(1, 10)`** | `favoured_clubs` *(Tuttuğu / Sevdiği Kulüpler)* | `club_uid`, `level` (`1..100`) | **1) Transfer & Maaş İndirimi:** Oyuncu sevdiği kulübe transfer olurken daha düşük maaş/itibar eşiğini kabul eder.<br>**2) Sadakat:** Kulüpteyken ayrılma isteği düşüktür; taraftar (`Supporter Confidence`) oyuncuyu daha çok sever. |
| **`(2, 10)`** | `disliked_clubs` *(Sevmediği / Ezeli Rakip Kulüpler)* | `club_uid`, `level` (`1..100`) | `level >= 70` ise oyuncu o kulüpten gelen transfer/sözleşme görüşmesini **doğrudan reddeder** (`"Has no intention of joining fierce rivals"`). |
| **`(1, 2)` / `(2, 2)` / `(4, 2)`** | `favoured_people` *(Sevdiği Kişiler: İdol, Arkadaş, Hoca)* | `person_uid`, `level` (`1..100`) + `Pfpr` (`Reason`) | **1) Transfer Çekimi:** Sevdiği teknik direktörün veya takım arkadaşının olduğu kulübe gelmeye sıcak bakar.<br>**2) `[REF-TE]` `Player Buy-In`:** Teknik direktör oyuncunun `favoured_people` listesindeyse `0.80 × Relationships` üzerinden **`+10..+15` `Buy-In`** bonusu verir ve oyuncu hocayı kovulma krizlerinde yönetime karşı savunur.<br>**3) Mentorluk:** Mentor ile öğrenci arasında pozitif ilişki varsa `Personality` ve `PPM` aktarım hızı artar. |
| **`(10, 2)`** | `disliked_people` *(Sevmediği Kişiler)* | `person_uid`, `level` (`1..100`) | **1) `[REF-AI]` `TSF_DISLIKE (-30)`:** Teknik direktör oyuncuyu sevmiyorsa kadro seçim puanından `-30` kırpar.<br>**2) Soyunma Odası & Transfer:** Aynı takımdaki iki oyuncu birbirini sevmiyorsa saha içi paslaşma tercihi ve takım uyumu (`Team Cohesion`) düşer; teknik direktörle `disliked` ilişkisi yüksekse oyuncu yeni sözleşme imzalamaz ve transfer ister. |
| **`(3, 18)` / `(4, 18)`** | `local_region_knowledge` / `nation_knowledge` | `region_id` / `nation_id`, `1..100` | Personelin (`Scout` / `Coach` / `Manager`) ülke ve bölge hakimiyet yüzdesi. Gözlemcilik ağının (`Scouting Range`) genişliğini ve önerilen oyuncuların isabetini belirler. |

---

### 2.8. Fiziksel Durum, Kondisyon, Keskinlik ve Yorgunluk Kolonları (`Player` & `player.xml`)

| Kolon Adı | FourCC | Tip / Aralık | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :---: | :---: | :--- |
| **`raw_condition`**<br>*(Anlık Kondisyon)* | `Pcon` | `int16` (`1..10000`, UI `%1..%100`) | **1) Maç İçi Fiziksel/Zihinsel Kırpılma:** Maç esnasında her koşu ve mücadeleyle (`stamina`, `work_rate`, `tempo`, `trigger_press` ve stadyumun `altitude_ft` / `weather` değerlerine bağlı olarak) azalır. `%75` altında hız/ivme, `%60` altında `decisions`/`concentration`/`technique` ciddi ceza alır.<br>**2) Sakatlık Çarpanı:** `%80` altında maça başlayan veya maç içinde `%55` altına düşen oyuncunun sakatlık zar atışı olasılığı üstel olarak (`2x..5x`) katlanır.<br>**3) AI Seçimi:** `TSF_CONDITION (+80)` (`[REF-AI]`). |
| **`raw_match_sharpness`**<br>*(Maç Keskinliği / Fitliği)* | `Pfit` | `int16` (`1..10000`, UI `%1..%100`) | Sadece maçta süre alarak yükselir (antrenmanda çok az korunur). Düşük `match_sharpness` (`<%75`), oyuncunun maç içindeki `first_touch`, `anticipation`, `decisions` reaksiyon süresini yavaşlatır ve maç içi kondisyonunun (`raw_condition`) daha hızlı tükenmesine yol açar. AI seçiminde `TSF_MATCH_SHARPNESS (+20)` ağırlığındadır. |
| **`jadedness` / `fatigue`**<br>*(Birikmiş Yorgunluk)* | `Pjad` | `int16` (`-500..+1000`, `0` = Dinç) | Sezon boyunca üst üste dinlenmeden oynanan maçlar, milli takım seyahatleri (`latitude`/`longitude` mesafesi) ve yüksek yoğunluklu antrenmanlarla **arka planda birikir** (`raw_condition` `%100` görünse bile `Pjad` yüksek olabilir!). `Pjad >= 400` olduğunda oyuncu **"Bitkin (`Jaded` / `In Need of a Rest`)"** durumuna düşer; tatile gönderilmezse (`Send on Holiday 1–2 Weeks`) hastalık/uzun süreli kas sakatlığı ve form çöküşü kaçınılmaz olur. |
| **`morale`**<br>*(Moral)* | `Pmor` | `uint8` (`1..20`) | Maç sonuçları, oynama süresi (`Playing Time`), sözleşme memnuniyeti, takım konuşmaları ve övgülerle değişir. Maç motorunda tüm zihinsel kararların (`composure`, `decisions`, `determination`, `flair`) üzerine **`-10%` ila `+10%`** genel güven çarpanı uygular; AI seçiminde `TSF_MORALE (+25)` puan verir. |

---

## Bölüm 3 — Başkan (`Chairperson`), Yönetim (`Board`), Teknik Ekip (`Staff`), Temsilci (`Agent`), Hakem (`Official`) ve Gazeteci (`Journalist`) Kolonları

Kaynak modeller: [`Staff`](../fm26save/_core/models/staff.py#L72-L125), [`StaffPreferences`](../fm26save/_core/models/staff.py#L18-L45), [`STAFF_BLOCK40_FIELDS`](../fm26save/constants.py#L140-L185), [`STAFF_ROLE_MAP`](../fm26save/constants.py#L110-L138) ve `editor.fmf` (`non player.xml`, `agent.xml`, `official.xml`, `journalist.xml`, `club.xml`).

---

### 3.1. Başkan (`Chairperson` / `Owner`) ve Yönetim (`Board`) Karakteri Nerede ve Ne Kadar İşe Yarıyor?

> [!IMPORTANT]
> **Kullanıcının Özel Örneği — Başkanın Karakteri (`StaffPreferences` + `club.xml` Sahiplik/Sugar Daddy + `NT27..NT94`) Nerede ve Ne Kadar İşe Yarıyor?**
> Bir kulübün başkanının (`job_role == "Chairperson"` / `Owner` / `President`, `r4 == 1`) karakteri oyun motorunda **4 ayrı tablodaki** parametrelerin birleşimiyle çalışır ve kulübün kaderini şu **7 mekanizma** üzerinden doğrudan belirler:

#### 1. Başkanın 4 Ana Yönetim Özelliği (`StaffPreferences` / `non player.xml` `1..20` veya `1..100`)

| Başkan Kolonu (`StaffPreferences`) | FourCC | Tip / Aralık | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :---: | :---: | :--- |
| **`resources`**<br>*(Kaynaklar / Zenginlik)* | `NDrs` | `uint8` (`1..20` / `1..100`) | **Başkanın Kişisel Finansal Gücü:** Kulübün `Chsd` (`Sugar Daddy`) bayrağıyla birlikte çalışır. Yüksek `resources` (`16..20`) olan başkan; kulüp zarar ettiğinde (`FinanceMonth.balance < 0`) kendi cebinden sermaye enjeksiyonu (`Cash Injection`) yapar, banka kredisi yerine faizsiz/düşük faizli sahip borcu (`Owner Debt`) verir ve her sezon başında `transfer_budget` ile `wage_budget` tavanını yüksek belirler. Düşük `resources` (`1..7`) olan başkan ise kulüp borca girdiğinde yıldız oyuncuları satmaya zorlar veya kulübü satışa (`board_takeover_manager.dat`) çıkarır. |
| **`business`**<br>*(Ticari Zeka / İş Yönetimi)* | `NDbs` | `uint8` (`1..20` / `1..100`) | **1) Sponsorluk ve Stadyum Gelirleri:** Yeni sponsorluk anlaşmaları (`Sponsorship`) imzalanırken veya yenilenirken anlaşma bedelini (`annual_amount`) kulüp itibarına göre optimize eder.<br>**2) Bütçe Disiplini ve Tesis Onayı:** Yüksek `business` (`15..20`) olan başkan kulübün nakit akışını (`FinanceMonth`) riske atacak aşırı maaş bütçesi artışlarını reddeder, ancak geri dönüşü yüksek olan **Altyapı (`Youth Facilities` / `Youth Recruitment`) ve Stadyum Büyütme (`Expansion Capacity`)** taleplerini finansal durum uygunsa onaylar.<br>**3) Kulüp Satışı (`Takeover`):** Kulüp devir görüşmelerinde (`board_takeover_manager.dat`) pazarlık süresini ve kulüp satış fiyatını belirler. |
| **`interference`**<br>*(Müdahalecilik)* | `NDin` | `uint8` (`1..20` / `1..100`) | **Teknik Direktörün İşine Karışma Katsayısı:**<br>- **Yüksek `interference` (`15..20`):** Başkan bir oyuncuya gelen yüksek bir transfer teklifini teknik direktöre sormadan **"Reddedilemeyecek kadar iyi bir teklif (`Too good to refuse`)"** diyerek **doğrudan kabul eder**! Ayrıca kendi kafasına göre yüksek itibarlı ("Galactico") oyuncu transfer edebilir, teknik direktörün sözleşme/transfer bütçesi taleplerine sert müdahale eder.<br>- **Düşük `interference` (`1..6`):** Tüm futbol operasyonunu teknik direktöre ve Futbol Direktörüne (`DoF`) bırakır. |
| **`patience`**<br>*(Sabır)* | `NDpt` | `uint8` (`1..20` / `1..100`) | **Teknik Direktörü Kovma Eşiği (`Sacking Threshold`):** Yönetim güveni (`Board Confidence` `0..100` / `F..A+`, `DebugBoardConfidence*` bayraklarıyla test edilir) düştüğünde başkanın hocayı kovmadan önce kaç maç/hafta bekleyeceğini belirler:<br>- **`patience <= 6` (Sabırsız Başkan):** Beklentilerin (`Season Expectations`) altında geçen 4–6 maçlık bir seri veya tek bir kupa elenişi sonrasında doğrudan **"Ultimatom / Sonraki Maçta X Puan Al (`Must Win Next Match`)"** toplantısı açar ve kovar.<br>- **`patience >= 16` (Sabırlı Başkan):** Kötü sonuçlara rağmen hocaya sezon sonuna kadar kredi tanır ve yönetim kurulu (`Board Request`) taleplerinde hocanın ültimatomlarını daha toleranslı karşılar. |

#### 2. Kulüp Sahiplik Modeli (`Cown`) ve `Sugar Daddy` (`Chsd`) Bayrakları (`club.xml` & `sugardaddy.edt`)

| Kulüp Sahiplik Kolonu | FourCC | Enum Değerleri (`db enums.xml`) | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :---: | :--- | :--- |
| **`sugar_daddy`**<br>*(Zengin Sahip Tipi)* | `Chsd` | `0`: `NONE`<br>`1`: **`FRONT_END`** *(Önden Harcayan)*<br>`2`: **`BACK_END`** *(Arkadan Destekleyen)*<br>`3`: **`UNDERWRITER`** *(Zarar Kapatan)* | **`FRONT_END` (Örn. PSG / Man City / Suudi Kulüpleri tipi):** Kulüp itibarını ve hedeflerini hızla zirveye taşımak için her sezon devasa `transfer_budget` ve `wage_budget` pompalar, şişkin sponsorluklar (`Sponsorship`) getirir.<br>**`BACK_END`:** Kulüp bir üst lige çıktığında veya kıtasal kupaya katıldığında bütçeyi artırır.<br>**`UNDERWRITER`:** Transfer bütçesini abartmaz ama sezon sonunda oluşan tüm işletme zararını (`FinanceMonth` negatif bakiye) FFP sınırları dahilinde sıfırlar. |
| **`sugar_daddy_increases_starting_finances`** | `Csdi` | `bool` | Kariyer başlangıcında kulübün açılış kasasını ve transfer bütçesini otomatik olarak üst dilime taşır. |
| **`ownership_type`**<br>*(Sahiplik & Seçim Modeli)* | `Cown` / `Cmeb` / `Cmel` | `Chairman` (Özel Sahip), `Socios / Member Owned` (Üye/Taraftar Sahipli — örn. Real Madrid, Barcelona, Türk Kulüpleri, Arjantin/Portekiz kulüpleri), `Fan Trust`, `PLC` | **Başkanlık Seçimleri (`Club Elections`):** Üye sahipli (`Member Owned`) kulüplerde belirli periyotlarla (`Cmel` seçim aralığı) **Başkanlık Seçimi** yapılır! Yeni seçilen başkan kendi `resources`, `business`, `interference`, `patience` profiliyle gelir; seçim vaadi olarak yıldız transferi sözü verebilir veya mevcut teknik direktörü kendi istediği hocayla (`NT27..NT40`) değiştirebilir! |

#### 3. Başkanın İşe Alım, Kulüp Vizyonu ve Taraftar Etkileşimi Eğilimleri (`non player.xml` `NT27..NT94`)

Başkanın (`Chairperson`) ve Futbol Direktörünün (`DoF`) `non player.xml` içindeki `NT*` eğilim bayrakları, kulübün **Kulüp Vizyonu (`Club Vision`)** hedeflerini ve kimi işe alacağını belirler:
- **Teknik Direktör / DoF İşe Alım Tercihleri (`NT27..NT40`):**
  - `NT27` (`Tendency to Appoint Domestic Manager`): Yerli teknik direktör tercih eder.
  - `NT28` (`Appoint Foreign Manager`): Yabancı hoca tercih eder.
  - `NT29` (`Appoint Club Icon`): Kulübün eski efsanesini (`Favoured Personnel`) hoca yapar.
  - `NT30` (`Appoint High Profile Manager`): Yüksek itibarlı (`world_reputation`) ünlü hoca arar.
  - `NT31` (`Appoint Youthful Manager`): Genç/modern hoca tercih eder.
  - `NT32` (`Appoint Attacking Manager`) vs `NT33` (`Defensive Manager`): Başkanın kendi `StaffPreferences.attacking` (`NDat`) değeriyle birleşerek Kulüp Vizyonuna **"Hücum Futbolu Oyna (`Play Attacking Football`)"** veya **"Savunma Güvenliği"** şartı koyar!
  - `NT34` (`Possession Manager`) vs `NT35` (`Direct Manager`): Kulüp Vizyonuna **"Topa Sahip Ol (`Play Possession Football`)"** şartı koyar.
  - `NT36` (`Hire Director of Football`): Kulüpte mutlaka bir Futbol Direktörü (`DoF`) çalıştırır.
- **Başkanın Transfer ve Sözleşme Müdahale Eğilimleri (`NT58..NT64`):**
  - `NT58` (`Sign High Profile Players`): Kulüp Vizyonuna **"Yüksek Profilli / Yıldız Oyuncu Transfer Et"** şartı ekler.
  - `NT59` (`Sign Young Players for First Team`) & `NT60` (`Sign Young Players for Future`): Kulüp Vizyonuna **`23` yaş altı / `U20` oyuncu transfer etme** zorunluluğu koyar.
  - `NT61` (`Use Youth System`): Altyapıdan (`Youth Intake`) oyuncu çıkarma şartı koyar ve altyapı tesis (`Cytv`) taleplerini kolayca onaylar.
  - `NT62` (`Strict Wage Structure`): Sıkı maaş tavanı uygular.
- **Taraftar Baskısından Etkilenme (`NT94` — `Influenced by Supporters`):**
  - Başkanın `NT94` eğilimi yüksekse ve kulüp taraftarının (`club.xml`) **`Cspt` (`Supporter Patience` — Sabır)** değeri düşük, **`Cspe` (`Supporter Expectations` — Beklenti)** değeri yüksekse; taraftarın sosyal medyada ve stadyumda yaptığı protestolar başkanın `Board Confidence` puanını doğrudan aşağı çeker ve hocanın kovulmasını hızlandırır!

---

### 3.2. Teknik Direktör, Antrenör, Gözlemci ve Sağlık Ekibi (`Staff` / `StaffPreferences` / `block_40`) Kolonları

Kaynak: [`Staff`](../fm26save/_core/models/staff.py#L72-L125), [`STAFF_BLOCK40_FIELDS`](../fm26save/constants.py#L140-L185), [`calculate_coach_stars()`](../fm26save/formulas.py#L948-L1035).

#### 3.2.1. `StaffPreferences` (14 Taktiksel ve Yönetimsel Tercih Kolonu — `1..20` / `1..100`)

| Kolon Adı (`StaffPreferences`) | FourCC | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :---: | :--- |
| `attacking` (`NDat`), `directness` (`NDdi`), `flexibility` (`NDfx`), `trigger_press` (`NDpr`), `tempo` (`NDto`), `width` (`NDwd`), `marking` (`NDmk`), `offside` (`NDof`) | `NDat`..`NDof` | **1) Yapay Zeka Maç İçi Taktik Üretimi:** AI teknik direktörlerin sahaya sürdüğü taktiğin `mentality`, `passing_directness`, `tempo`, `width` ve `pressing` kaydırıcılarını doğrudan bu 8 kolon belirler.<br>**2) Başkan Kulüp Vizyonu:** Kişi `Chairperson` ise Kulüp Vizyonuna hangi futbol felsefesini (`Attacking`, `Possession`, `High Tempo`, `Counter`) dayatacağını belirler. |
| `buying_players` (`NDbp`) | `NDbp` | AI hocanın ve `DoF`'un altyapıdan oyuncu çıkarmak yerine dış transferde bonservis harcama eğilimini belirler. |
| `hardness_of_training` (`NDht`) | `NDht` | AI hocanın (veya antrenman devredildiğinde Asistan Menajerin) haftalık antrenman takviminde (`[REF-ANT]`) `Physical`/`Endurance` yüklemesini ne kadar ağır tutacağını belirler. |
| `mind_games` (`NDmg`) | `NDmg` | Basın toplantılarında rakip teknik direktörlere sataşma, hakem baskısı kurma ve rakip oyuncuların `pressure` özelliğini test etme sıklığını belirler. |
| `squad_rotation` (`NDsr`) | `NDsr` | `[REF-AI]` kadro seçiminde kupa ve fikstür sıkışıklığında (`TPS_CUP`) as oyuncuları dinlendirip yedeklere şans verme oranını belirler. |
| `preferred_formation_1`, `preferred_formation_2`, `defensive_formation`, `attacking_formation` | `Npf1`, `Npf2`, `Npdf`, `Npaf` | AI teknik direktörün (ve **`Head of Youth Development` / Altyapı Sorumlusunun!**) tercih ettiği dizilişler (`4-2-3-1`, `4-3-3`, `3-4-2-1` vb.). **Kritik HOYD Etkisi:** Kulübün `Head of Youth Development` (`r4 == 18`) personelinin `preferred_formation` dizilişi neyse, her yıl Mart/Nisan ayında gelen **Altyapı Oyuncu Çıkışında (`Youth Intake` / `Newgens`)** o dizilişin mevkilerine uygun genç oyuncular üretilir (örn. HOYD `4-4-2 Diamond` seviyorsa kanat oyuncusu yerine `AMC`/`DM` ve çift santrfor ağırlıklı `newgen` çıkar!). |

#### 3.2.2. `STAFF_BLOCK40_FIELDS` (26 Gizli/Görünür Personel Özelliği — Kayıt Dosyası `1..100`, UI `1..20`)

Kaynak: [`STAFF_BLOCK40_FIELDS`](../fm26save/constants.py#L140-L185), [`dof.py`](../fm26save/dof.py).

| `block_40` Ofset / Kolon Adı | FourCC | Dokunduğu Antrenman Yıldızı (`[REF-ANT]`) ve Oyun Motoru Etkisi |
| :--- | :---: | :--- |
| **`attacking`** *(Hücum Antrenörlüğü)* | `Natt` | **Antrenman Yıldızı:** `Attacking Tactical` (`×6` + `tactical ×3` + `DDB ×2`) ve `Attacking Technical` (`×6` + `technical ×3` + `DDB ×2`) yıldızlarını üretir. |
| **`defending`** *(Savunma Antrenörlüğü)* | `Ndef` | **Antrenman Yıldızı:** `Defending Tactical` (`×6` + `tactical ×3` + `DDB ×2`) ve `Defending Technical` (`×6` + `technical ×3` + `DDB ×2`) yıldızlarını üretir. |
| **`tactical`** *(Taktik Antrenörlüğü)* | `Ntac` | **Antrenman Yıldızı:** `Possession Tactical` (`×6` + `mental ×3` + `DDB ×2`) ana sütunu ve diğer tüm `Tactical` kategorilerin ikincil (`×3`) çarpanıdır. Ayrıca Asistan Menajerin maç içi **Taktiksel Tavsiye (`Tactical Advice`)** isabetini belirler. |
| **`technical`** *(Teknik Antrenörlüğü)* | `Ntec` | **Antrenman Yıldızı:** `Possession Technical` (`×6` + `mental ×3` + `DDB ×2`), `Attacking Technical` (`×3`) ve `Defending Technical` (`×3`) yıldızlarını üretir. |
| **`mental`** *(Zihinsel Antrenörlük)* | `Nmen` | `Possession Tactical` ve `Possession Technical` kategorilerinde `×3` ağırlığındadır. |
| **`fitness`** *(Kondisyon Antrenörlüğü)* | `Nfit` | **Antrenman Yıldızı:** `Quickness` (`fitness ×9` + `DDB ×2`) ve `Strength` (`fitness ×9` + `DDB ×2`) kategorilerinin **tek** teknik girdisidir (`×9` ağırlık!). |
| **`goalkeepers`** / `gk_shot_stopping` / `gk_handling` / `gk_distribution` | `Ngkp`, `Ngss`, `Nghd` | **Antrenman Yıldızı:** Kaleci antrenmanlarında `Shot Stopping` ve `Handling & Distribution` yıldızlarını (`×6..9` + `DDB ×2`) üretir. |
| **`determination`**, **`level_of_discipline`**, **`motivating`** *(DDB Üçlüsü)* | `Pdet`, `Ndis`, `Nmot` | **1) `[REF-ANT]` Koç Yıldız Çarpanı:** **10 antrenman kategorisinin tamamında** `(Det + Dis + Mot) × 2` olarak doğrudan yıldız formülüne girer!<br>**2) Maç Konuşmaları (`Team Talks`):** Asistan menajerin devre arası konuşma başarısını `motivating` ve `man_management` belirler.<br>**3) Disiplin:** Yüksek `level_of_discipline`, oyuncuların antrenman yoğunluğundan şikayet etme oranını düşürür. |
| **`judging_player_ability` (`JPA`)** *(Oyuncu Yeteneği Değerlendirme)* | `Njpa` | **1) Gözlemcilik (`Scout`):** Gözlemlenen oyuncunun gerçek `CA` değerini ve gizli özelliklerini (`consistency`, `important_matches`, `injury_proneness`) ne kadar hatasız (`±0` sapma ile) raporlayacağını belirler.<br>**2) Asistan & DoF:** Kadrodaki oyuncuların yıldız (`★`) değerlendirmesini ve `[REF-AI]` kadro seçim isabetini belirler. |
| **`judging_player_potential` (`JPP`)** *(Oyuncu Potansiyeli Değerlendirme)* | `Njpp` | Genç bir oyuncunun gerçek `PA` (`1..200`) tavanını beyaz/altın yıldızlarla ne kadar doğru tahmin edeceğini ve **`Head of Youth Development` (`HOYD`)** koltuğunda çıkan `Youth Intake` oyuncularının potansiyel kalitesini belirler. |
| **`working_with_youngsters`** *(Gençlerle Çalışma)* | `Nwwy` | **1) `U18`/`U21` Gelişimi:** `23` yaş altı oyuncuların antrenman verimini çarpar.<br>**2) `HOYD` (`Altyapı Sorumlusu`) Etkisi:** `HOYD` personelinin `working_with_youngsters`, `JPP` ve kendi **`Personality` (`Model Citizen` / `Professional`)** profili, her yıl kulüp altyapısından çıkan `newgen` oyuncuların kişiliklerini (`Personality` `professionalism`, `ambition`, `determination`) doğrudan kopyalar/şekillendirir! |
| **`people_management` (`man_management`)** *(İnsan Yönetimi)* | `Nman` | Teknik direktörün, Asistanın, `DoF`'un ve `Loan Manager`'ın oyuncu mutsuzluklarını çözme, antrenman organizasyonu ve kiralık oyuncuları takip etme başarısını belirler. |
| **`negotiating`** *(Müzakere / Pazarlık)* | `Nneg` | **`Director of Football` (`DoF`)** veya Başkan transfer/sözleşme görüşmesi yürütürken bonservis bedelini düşürme ve oyuncuyu/temsilciyi daha düşük maaş/bonus (`[REF-EKO]`) paketine ikna etme gücünü belirler. |
| **`physiotherapy`** *(Fizyoterapi)* | `Nphy` | **`Head Physio` / `Physio`:** Oyuncu sakatlandığında (`InjuryRecord`) iyileşme süresini (`injury.xml` `Min Days .. Max Days` aralığının **alt sınırına** çekme) ve tedavi kalitesini doğrudan belirler. |
| **`sports_science`** *(Spor Bilimi)* | `Nsps` | **`Head of Sports Science` / `Sports Scientist`:** Sakatlık oluştuktan sonra değil, **sakatlık oluşmadan önce** devreye girer! Oyuncuların `Pjad` (`Jadedness`/Yorgunluk) birikimini azaltır, tıbbi risk raporlarının (`Medical Centre` `Injury Risk`) doğruluğunu artırır ve antrenman kaynaklı kas sakatlığı olasılığını (`[REF-ANT]`) düşürür. |
| **`tactical_knowledge`** *(Taktiksel Bilgi)* | `Ntkn` | Maç öncesi **Rakip Analizi (`Opposition Instructions`)** önerilerinin doğruluğunu ve AI hocanın maç içinde rakibin taktiğine karşı hamle üretme hızını belirler. |
| **`set_pieces`** *(Duran Top Antrenörlüğü)* | `Nspc` | **`Set Piece Coach`:** Duran top antrenman seanslarının (`Attacking/Defending Set Pieces`, `Delivery`) verimini ve maç içi duran top rutini (`SetPieceRoutine`) organizasyon başarısını çarpar. |
| **`data_analysis` / `judging_staff_ability`** | `Ndan`, `Njsa` | **`Performance Analyst` & `Technical Director`:** Maç önü/sonu veri raporlarının derinliğini ve `Technical Director`'ün personel (`Staff`) değerlendirme doğruluğunu belirler. |

---

### 3.3. Temsilci (`Agent`), Hakem (`Official`) ve Gazeteci (`Journalist`) Tablolarının Tüm Kolonları

Kaynak: `editor.fmf` (`agent.xml`, `official.xml`, `journalist.xml`, `media source.xml`).

#### 3.3.1. Temsilci / Menajer (`agent.xml` & `agent_manager.dat` — 7 Kolon)

| Kolon Adı (`Agent`) | FourCC | Tip / Aralık | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :---: | :---: | :--- |
| **`business` (`greed`)**<br>*(Ticari Hırs / Açgözlülük)* | `Agre` | `uint8` (`1..20`) | **Sözleşme ve Komisyon Çarpanı (`[REF-EKO]`):** Yüksek `Agre` (`15..20`) olan temsilci, müvekkili için maksimum haftalık maaş (`wage_per_week`), yüksek yıllık maaş artışı (`Yearly Wage Rise`), düşük serbest kalma maddesi (`Minimum Fee Release Clause`) ve kendisi için çok yüksek **Menajer Komisyonu (`Contract.unknown.money_b`)** ile sonraki satıştan pay (`Sell-On Fee %`) talep eder. |
| **`patience`**<br>*(Pazarlık Sabrı)* | `Apat` | `uint8` (`1..20`) | Sözleşme görüşmelerinde (`Contract Negotiation`) karşı teklif reddedildiğinde temsilcinin masayı devirmeden önce **kaç tur pazarlığa devam edeceğini** belirler (`Apat <= 6` olan temsilci 2. düşük teklifte görüşmeyi anında sonlandırır ve kırmızıya döner!). |
| **`touting_clients` (`pimping`)**<br>*(Oyuncu Pazarlama Eğilimi)* | `Apim` | `uint8` (`1..20`) | Yüksek `Apim` (`15..20`) olan temsilci, müvekkili form yakaladığında sürekli diğer kulüplere **"Temsilci Önerisi (`Agent Offer`)"** mesajı gönderir ve kulüpten yılda bir yeni zamlı sözleşme talep eder. |
| **`size_of_agency`**<br>*(Ajans Büyüklüğü)* | `Asoa` | `uint8` (`1..20`) | Temsilcinin portföyündeki maksimum oyuncu sayısını ve küresel transfer ağındaki gücünü belirler. |
| **`based_nation` & `clients`** | `Abna`, `Acli` | `int`, `list[int]` | Temsilcinin merkez ülkesi (o ülkedeki oyuncularla çalışma olasılığı yüksektir) ve temsil ettiği oyuncu UID listesi. *(Not: Teknik direktör bir temsilcinin `disliked_people` `(10, 2)` listesine girerse, o temsilcinin **tüm `Acli` oyuncuları** sözleşme görüşmelerinde ekstra zorluk çıkarır!).* |

#### 3.3.2. Hakem (`official.xml` — 16 Kolon)

| Kolon Adı (`Official`) | FourCC | Tip / Aralık | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :---: | :---: | :--- |
| **`refereeing`** *(Hakemlik Kalitesi)* | `Oref` | `uint8` (`1..200`) | Hakemin penaltı, faul ve bariz gol şansı (`DOGSO`) pozisyonlarında **doğru kararı verme** olasılığını belirler (`VAR` olmayan liglerde kritik öneme sahiptir; `VAR` olan maçlarda orta hakemin monitöre gitme ve ilk karar doğruluğunu etkiler). |
| **`running_line`** *(Çizgi Hakemliği)* | `Orun` | `uint8` (`1..200`) | Yardımcı hakemin milimetrik ofsayt (`likes_to_try_to_beat_offside_trap`) ve taç/korner kararlarındaki isabetini belirler. |
| **`discipline`** *(Disiplin / Kart Sıklığı)* | `Odis` | `uint8` (`1..20`) | Hakemin cebinden sarı ve kırmızı kart çıkarma eşiğini belirler (`Odis >= 16` olan hakem yapılan ilk sert faulde veya `argues_with_officials` itirazında doğrudan kart gösterir; maç öncesi haberlerde *"Strict Referee"* olarak uyarılır). |
| **`allowing_flow`** *(Oyunu Akıtma / Avantaj)* | `Oalf` | `uint8` (`1..20`) | Yüksek `Oalf` (`15..20`) olan hakem ufak temaslarda düdük çalmaz ve avantaj kuralını sık uygular (fiziksel/sert oynayan `gegenpress` ve `route_one` takımlarına yarar); düşük `Oalf` olan hakem her temasta oyunu durdurur (duran top takımlarına yarar). |
| **`pressure`** *(Baskıya Dayanıklılık)* | `Oprs` | `uint8` (`1..20`) | Ev sahibi stadyumun taraftar baskısı (`attendance` + `Supporter Passion` `Csps`), derbi atmosferi (`derby.xml`) ve oyuncuların hakemin etrafını sarması karşısında hakemin **ev sahibi lehine (`Home Bias`)** eyyam yapıp yapmayacağını belirler! |
| **`timekeeping`** *(Süre Yönetimi)* | `Otkp` | `uint8` (`1..20`) | Hakemin zaman geçirme (`Time Wasting`) davranışlarını uzatma dakikalarına (`+4..+10 dk`) ne kadar eksiksiz ekleyeceğini ve maçı tam zamanında bitirme hassasiyetini belirler. |
| **`important_matches`** *(Önemli Maçlar)* | `Oimm` | `uint8` (`1..20`) | Kupa finalleri ve derbilerde hakemin kendi `Oref` standardını koruma becerisi. |

#### 3.3.3. Gazeteci ve Medya Kaynağı (`journalist.xml` 10 Kolon & `media source.xml` 21 Kolon)

| Kolon Adı | FourCC | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :---: | :--- |
| `honesty` (`Jhon`), `temperament` (`Jtem`), `pressure` (`Jprs`) | `Jhon`, `Jtem`, `Jprs` | Basın toplantılarında (`Press Conferences`) gazetecinin teknik direktörün sözlerini çarpıtıp sansasyonel manşet atma (`low honesty`), ters cevaba sinirlenip üst üste sıkıştırıcı soru sorma (`low temperament`) ve kulüp yasağına (`Ban Journalist`) tepki verme davranışını yönetir. |
| `style_of_writing` (`Jsow`) & `media_type` (`Mmty`) | `Jsow`, `Mmty` | Haberin tonunu (`Tabloid / Sensationalist` vs `Broadsheet / Analytical`) ve transfer dedikodularının (`Transfer Rumours`) gerçeklik payını belirler. |
| `club_covered` (`Jccn`), `media_scope` (`Mmsc`), `period` (`Mper`) | `Jccn`, `Mmsc`, `Mper` | Gazetecinin hangi kulübün muhabiri olduğunu, medya kaynağının kapsamını (`Local`, `Regional`, `National`, `Global`) ve yayın periyodunu belirler. |


---

## Bölüm 4 — Kulüp (`clubs`), Finans (`finances`), Sponsorluk (`sponsorships`), Tesisler (`facilities`), Ortaklıklar (`affiliates`) ve Taraftar (`club.xml`) Tablolarının Tüm Kolonları

Kaynak modeller: [`Club`](../fm26save/_core/models/clubs.py#L12-L42), [`ManagedClub`](../fm26save/_core/models/clubs.py#L45-L60), [`FinanceMonth`](../fm26save/_core/models/finances.py#L12-L38), [`Sponsorship`](../fm26save/_core/models/finances.py#L41-L58), [`ClubFacilities`](../fm26save/_core/models/finances.py#L61-L72), [`AffiliateGroup`](../fm26save/_core/models/stadiums.py#L45-L58) ve `editor.fmf/club.xml` (`597` FourCC alanı).

---

### 4.1. Kulüp Kimlik, İtibar, Moral ve Taraftar Karakteri (`Club` & `club.xml`) Kolonları

| Kolon Adı | FourCC | Tip / Aralık | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :---: | :---: | :--- |
| `id`, `unique_id`, `name`, `short_name`, `six_letter_name`, `three_letter_name` | `dbid`, `Cuid`, `Cnam`, `Csna`, `C6ln`, `C3ln` | `int` / `str` | Kulübün birincil anahtarları, fikstür/skor tabelası kısaltmaları (`3` ve `6` harfli adlar) ve logo/forma grafik paketi ID'si. |
| `reputation` | `Crep` | `int16` (`1..10000`, UI `1..200`) | **1) Oyuncu & Personel Çekim Tavanı:** Bir oyuncunun kulüple transfer masasına oturup oturmayacağını belirleyen **1 numaralı** filtredir (`Player.current_reputation > Club.reputation + Tolerans` ise oyuncu görüşmeyi reddeder).<br>**2) Piyasa Değeri (`[REF-EKO]`):** Kulüpteki tüm oyuncuların piyasa değerine `+0.00038 × ClubRep` ekler.<br>**3) Sponsorluk & Seyirci:** Ticari gelir tavanını ve deplasman seyirci cazibesini belirler. |
| `morale` | `Cmor` | `uint8` (`1..20`) | Kulüp genel atmosferini ve yeni başlayan sezonda oyuncuların başlangıç moral tabanını belirler. |
| `average_attendance`, `minimum_attendance`, `maximum_attendance` | `Cava`, `Cmia`, `Cmaa` | `int32` | **Gişe Geliri (`Gate Receipts`) ve Ev Sahibi Avantajı (`[REF-ME]`):** Her iç saha maçında bilet satış sayısını (rakibin `reputation`, derbi durumu `derby.xml`, hava durumu `weather.xml`, bilet fiyatı `Ctkp` ve kulübün lig sırası ile modüle ederek) belirler. |
| `ticket_price` & `season_ticket_price` & `season_ticket_holders` | `Ctkp`, `Cstp`, `Csth` | `float` / `int32` | Sezon başında kasaya giren toplu kombine gelirini (`Season Tickets`) ve maç başı gişe hasılatını (`Matchday Income`) doğrudan çarpar. |
| **Taraftar Sadakati (`Supporter Loyalty`)** | `Csly` | `uint8` (`1..20`) | Takım kötü gittiğinde veya alt lige düştüğünde stadyum doluluk oranının (`average_attendance` $\rightarrow$ `minimum_attendance` yönünde) ne kadar az düşeceğini belirler (`Csly >= 18` olan kulüpte küme düşülse bile tribünler dolu kalır). |
| **Taraftar Tutkusu (`Supporter Passion`)** | `Csps` | `uint8` (`1..20`) | **1) Saha İçi Ev Sahibi Avantajı (`Home Advantage`):** Yüksek `Csps` (`16..20`), iç saha maçlarında rakip oyuncuların `composure` ve hakemin `pressure` (`Oprs`) özelliklerine ekstra baskı uygular!<br>**2) Ticari Gelir:** Taraftar başına forma/ürün (`Merchandising`) satın alma oranını artırır. |
| **Taraftar Sabrı (`Supporter Patience`)** | `Cspt` | `uint8` (`1..20`) | Kötü sonuçlarda veya sıkıcı futbolda taraftar memnuniyetinin (`Supporter Confidence`) ne kadar hızlı çöküp ıslıklama/istifa tezahüratına dönüşeceğini belirler (`NT94` ile başkanı etkiler). |
| **Taraftar Refahı (`Supporter Affluence`)** | `Csaf` | `uint8` (`1..20`) | Taraftarın bilet fiyat artışlarına (`Ctkp`) toleransını, VIP/kurumsal loca gelirini ve forma satış birim gelirini çarpar. |
| **Taraftar Mizacı (`Supporter Temperament`)** | `Cste` | `uint8` (`1..20`) | Düşük `Cste` (ateşli/agresif taraftar), derbilerde olay çıkarma, meşale/saha kapatma cezası ve sosyal medyada sert tepki verme olasılığını artırır. |
| **Taraftar Beklentisi (`Supporter Expectations`)** | `Cspe` | `uint8` (`1..20`) | Taraftarın sezon sonu lig sıralaması ve kupa beklenti çıtasını belirler. |
| **Taraftar Profil Dağılımı (`Supporter Profile %`)** | `TCct` | `%` (`Hardcore`, `Core`, `Family`, `Fairweather`, `Corporate`, `Casual`) | FM26/FM27 **Taraftar Profili (`Supporter Profile`)** ekranındaki 6 dilimin yüzdesini tutar (`Hardcore` atmosferi ve deplasman tribününü, `Corporate` gişe/loca gelirini, `Fairweather` ise başarıya göre değişen seyirci dalgalanmasını yönetir). |

---

### 4.2. Kulüp Tesisleri ve Altyapı (`ClubFacilities` & `club.xml` / Kayıt Sonrası `+33..+50` Ofsetleri)

Kaynak: [`ClubFacilities`](../fm26save/_core/models/finances.py#L61-L72) ve `editor.fmf/club.xml`.

| Tesis Kolonu | FourCC | Tip / Aralık | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :---: | :---: | :--- |
| **`training_facilities`**<br>*(Antrenman Tesisleri)* | `Ctlv` | `uint8` (`1..20`) | **1) Haftalık Antrenman Çarpanı (`[REF-ANT]`):** As takım ve yedek takım oyuncularının haftalık antrenman seanslarından aldığı `CA` gelişim puanını doğrudan çarpar (`1` = `%40` verim $\rightarrow$ `20` `State of the Art` = `%100+` tavan verim).<br>**2) Sakatlık Riski:** Yüksek tesis kalitesi antrenman sahası kaynaklı sakatlıkları azaltır. *(Zamanla teknolojik eskime `degradation` yaşar ve yönetimden yenileme gerekir).* |
| **`youth_facilities`**<br>*(Altyapı Tesisleri)* | `Cytv` | `uint8` (`1..20`) | **1) U18/U19 Gelişim Hızı:** Altyapı takımındaki oyuncuların antrenman gelişim hızını belirler.<br>**2) `Newgen` Başlangıç `CA` Bonusu:** Mart/Nisan ayında kulübe katılan `Youth Intake` (`15..16` yaş) oyuncularının akademiden çıkarken sahip olduğu **başlangıç `CA` (`Current Ability`)** seviyesini yükseltir. |
| **`youth_coaching` (`junior_coaching`)**<br>*(Altyapı Antrenörlüğü / Akademi Koçluğu)* | `Cyfb` | `uint8` (`1..20`) | Oyuncu henüz **`15` yaşına gelip `Youth Intake` listesine girmeden önceki** akademi eğitim kalitesidir: Çıkan `newgen` oyuncuların **hem başlangıç `CA` değerini hem de `PA` (`Potansiyel Yetenek`) dağılım ortalamasını** doğrudan yukarı çeker! |
| **`youth_recruitment`**<br>*(Genç Yetiştirme Ağı / Altyapı Alımı)* | `Crcb` | `uint8` (`1..20`) | **Altyapıdan `Wonderkid` (`PA >= 150..200`) Çıkma Olasılığının En Büyük Çarpanıdır:**<br>- Kulübün bulunduğu şehirdeki (`city.xml` `Cinh` nüfus) ve ülkedeki (`nation.xml` `NYRt` `Youth Rating`) en yetenekli çocukları rakip kulüplerden önce yakalama yarıçapını belirler.<br>- Aynı şehirde/bölgede birden fazla kulüp varsa, en yüksek `(Crcb × 0.60 + Club.reputation × 0.40)` puanına sahip kulüp o bölgenin en yüksek `PA`'lı `newgen` adayını ilk sıradan kapar; ayrıca `Crcb >= 18` olan kulüpler yabancı ülkelerden de (`AffiliateGroup` bağlantılarıyla) `newgen` çekebilir! |
| **`youth_importance`**<br>*(Altyapı Önemi)* | `Cyim` | `uint8` (`1..20`) | AI yönetimin ve başkanın altyapı tesis yatırımlarını (`Cytv`, `Cyfb`, `Crcb`) ne kadar önceliklendireceğini ve `Youth Intake` bütçesini kesmeme kararlılığını belirler. |
| **`corporate_facilities`**<br>*(Kurumsal Tesisler)* | `Ccfa` | `uint8` (`1..20`) | Stadyumun VIP locaları, ağırlama alanları ve kurumsal kapasitesidir: Her iç saha maçında gişe gelirinin (`Gate Receipts`) üzerine eklenen **`Matchday Corporate Income`** kalemini ve kurumsal taraftar (`Corporate %`) memnuniyetini doğrudan çarpar. |
| **`data_analysis_facilities`** *(Veri Analiz Tesisleri)* | — (`+49`) | `uint8` (`1..20`) | Kulübün veri merkezi altyapısı. Gözlemcilik ve maç analiz (`Data Hub`) grafiklerinin doğruluğunu ve kapsamını belirler. |

---

### 4.3. Finans (`FinanceMonth`), Borçlar (`Cdbt`) ve Sponsorluk (`Sponsorship`) Kolonları

Kaynak: [`FinanceMonth`](../fm26save/_core/models/finances.py#L12-L38), [`Sponsorship`](../fm26save/_core/models/finances.py#L41-L58).

| Tablo & Kolon Adı | FourCC | Tip | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :---: | :---: | :--- |
| **`FinanceMonth.balance`**<br>*(Genel Bakiye / Kasa)* | `Cbal` | `int64` (£/€/\$) | Kulübün anlık nakit kasası. Negatife (`< 0`) düştüğünde:<br>1) Yönetim `pct_revenue_available` (satıştan transfere aktarılan yüzdeyi) `%100`'den `%10..%30`'a düşürür.<br>2) Aşırı negatif bakiyede kulüp **Kayyuma (`Administration`)** düşer; ligde **`-9` ila `-12` puan silme cezası** (`LeagueTableRow.points_deducted`) ve transfer yasağı (`Transfer Embargo`) alır! |
| **`FinanceMonth.transfer_budget_remaining` & `transfer_budget_original`** | `Ctrb` | `int64` | Yapılabilecek maksimum bonservis/kiralama harcaması. `wage_budget` ile kaydırıcı (`slider`) üzerinden birbirine dönüştürülebilir (`1£ haftalık maaş = 52£ yıllık transfer bütçesi`). |
| **`FinanceMonth.wage_budget` & `current_wage_bill`** | `Cwab` | `int64` | Haftalık/yıllık toplam maaş tavanı. `current_wage_bill > wage_budget` olduğunda yönetim yeni transferlerde önerilebilecek maksimum maaşı (`Max Allowed Wage`) sert şekilde kısıtlar ve `Board Confidence -> Financial Management` notunu düşürür. |
| **`FinanceMonth.pct_revenue_available`** | `Cptf` | `uint8` (`0..100%`) | Oyuncu satışından elde edilen bonservis gelirinin yüzde kaçının `transfer_budget_remaining` hesabına ekleneceğini belirler. |
| **`FinanceMonth.youth_grant` / `merchandising` / `gate_receipts` / `tv_revenue`** | — | `int64` | Aylık gelir/gider kırılım sütunları: **UEFA Finansal Fair Play (`FFP`)** ve yerel lig harcama limiti (`Salary Cap`) hesaplamalarında **"Futbol Geliri (`Relevant FFP Income`)"** toplamını oluşturur. |
| **`Club Debt` (`Cdbt`: `Bank Loan`, `Owner Debt`, `State Loan`)** | `Cdbt` | `int64` + `% faiz` + `bitiş tarihi` | Kulübün aylık nakit akışından her ay düzenli olarak düşülen **Kredi Taksit Ödemelerini (`Loan Repayments`)** üretir (`Owner Debt` ise yalnızca kulüp kar ettiğinde veya başkan değiştiğinde ödenir). |
| **`Sponsorship`** (`kind`, `annual_amount`, `start_year`, `end_year`, `is_fixed`, `kit_sponsor`) | `Cspl` | `8 kolon` | Kulübün forma göğüs, kol, stadyum isim hakkı ve genel ticari sponsorluk sözleşmeleri. `end_year` geldiğinde başkanın `business` (`NDbs`) ve kulübün `reputation` değerine göre yeni bedelle yenilenir (`is_fixed == True` ise yenilenmez/sabit kalır). |

---

### 4.4. Bağlı Kulüpler (`AffiliateGroup` & `club.xml` `Cafl` 25 Bayrak) Kolonları

Kaynak: [`AffiliateGroup`](../fm26save/_core/models/stadiums.py#L45-L58) ve `editor.fmf/club.xml` (`Cafl`).

| Kolon / Bayrak Adı | Tip | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :---: | :--- |
| `parent_club_uid` & `affiliated_club_uids` & `affiliation_type` | `int` / `tuple` | Ana kulüp (`Senior Affiliate`) ile pilot kulüp (`Feeder / Junior Affiliate`) arasındaki hiyerarşik bağ. |
| **`Players Go On Loan` & `Loan Players Wages Paid by Parent`** | `bool` | Ana kulüp, genç oyuncularını pilot kulübe **maaşının `%100`'ünü kendisi ödeyerek** kiralık gönderebilir; pilot kulüp teklifi reddedemez (oyuncunun ikna olması yeterlidir). |
| **`First Option to Buy` *(Ön Alım Hakkı)*** | `bool` | Pilot kulübün bir oyuncusuna üçüncü bir kulüpten teklif geldiğinde, ana kulübe otomatik bildirim gider ve aynı bedelle teklifi eşitleyip oyuncuyu alma önceliği tanınır. |
| **`Work Permit / Gain Nationality Affiliate`** | `bool` | Çalışma izni (`Work Permit`) alamayan veya AB dışı (`Non-EU`) olan oyuncunun daha kısa vatandaşlık süresi olan (`nation.xml` `Nygc`, örn. İspanya'da Güney Amerikalılar için `2 yıl`) bir pilot kulüpte kiralık oynatılarak pasaport almasını sağlar. |
| **`Youth Coaching / Youth Intake Link` *(Altyapı Bağlantısı)*** | `bool` | Ana kulübün her yıl kendi **`Youth Intake` (`Newgen`)** havuzuna pilot kulübün ülkesinden **1–2 yabancı uyruklu genç yetenek** katmasını ve o ülkenin `Scouting Knowledge` bilgisini kazanmasını sağlar! |
| **`Financial Benefits / Commercial Link` *(Ticari Ortaklık)*** | `bool` | ABD, Japonya, Güney Kore, Çin veya Avustralya'daki bir pilot kulüple kurulan bağ, ana kulübün `Merchandising` (yurt dışı forma satış) gelirini **`+%10..%25`** artırır (`annual_fee` karşılığında). |
| **`Same Board` *(Aynı Yönetim / Multi-Club Ownership)*** | `bool` | İki kulübün aynı sahibe/gruba (örn. City Football Group, Red Bull, BlueCo) ait olduğunu belirtir: **UEFA kuralları gereği** aynı sezon aynı Avrupa kupasına katılırlarsa aralarında transfer/kiralama kısıtlaması devreye girebilir! |

---

## Bölüm 5 — Stadyum (`stadiums`), Şehir (`city.xml`), Hava Durumu (`weather.xml`), Ülke (`nation.xml`), Kıta, Bölge, Derbi ve Anlaşmalar Tablolarının Tüm Kolonları

Kaynak modeller: [`Stadium`](../fm26save/_core/models/stadiums.py#L12-L42), `server_db/table_21.dat` (`181` baytlık tam kayıt) ve `editor.fmf` (`stadium.xml` `77` alan, `city.xml` `15` alan, `weather.xml` `94` alan, `nation.xml` `64` alan, `derby.xml` `16` alan, `agreement.xml` `8` alan).

---

### 5.1. Şehir (`city.xml` — 15 Kolon) ve Stadyum Rakımı (`altitude_ft` / `Calt`) Nerede ve Ne Kadar İşe Yarıyor?

> [!IMPORTANT]
> **Kullanıcının Özel Örneği — Bir Stadyumun / Şehrin Rakımı (`altitude_ft` / `Calt`) ve Coğrafi Parametreleri Nerede ve Ne Kadar İşe Yarıyor?**
> Veritabanında her stadyum bağlı olduğu şehrin (`city_id` $\rightarrow$ `city.xml`) **`Calt` (`Altitude (ft)` — Rakım, `0..15000 feet` / `0..4572 metre`)**, **`Clat`/`Clon` (Enlem/Boylam)**, **`Catt` (Çekicilik)**, **`Cinh` (Nüfus)** ve **`Cwea` (Hava Durumu Profili)** değerlerini miras alır:
> 1. **Rakımın (`altitude_ft` / `Calt`) Maç Motorundaki Kondisyon ve Fiziksel Cezası (`simatch.fmf` & `QME`):**
>    - Rakım **`1.500 metre` (`~4.920 feet`)** eşiğini aştığında (örn. Bolivya La Paz / El Alto `3.640m–4.150m`, Ekvador Quito `2.850m`, Kolombiya Bogota `2.640m`, Meksika Mexico City `2.240m`, Türkiye Erzurum `1.900m` / Sivas `1.285m`, Güney Afrika Johannesburg `1.753m`) maç motorunda **Yüksek Rakım Hipoksi (Oksijen Azlığı) Çarpanı** devreye girer!
>    - **Kim Etkilenir?** Ev sahibi kulübün oyuncuları (ve kendi stadyumu benzer yüksek rakımda olan deplasman takımları) yüksek rakıma **adapte (`Acclimatised`)** kabul edilir ve ceza almazlar. Ancak **deniz seviyesinden / düşük rakımdan gelen deplasman takımının** oyuncularında:
>      1. Maç içi **`raw_condition` (`Pcon`) tükenme hızı (her sprint ve pres aksiyonunun maliyeti)** rakım farkıyla orantılı olarak **`+15%` ila `+45%` arasında hızlanır!**
>      2. Deplasman oyuncularının **`stamina` ve `natural_fitness`** özelliklerinin ağırlığı ikiye katlanır; `60. dakikadan` itibaren kondisyonu `%60` altına düşen deplasman oyuncularının `acceleration`, `pace`, `decisions` ve `concentration` değerleri çöker.
>      3. **Top Fiziği (Hava Direnci):** Yüksek rakımda hava yoğunluğu ($\rho$) daha düşük olduğu için uzaktan şutlarda (`long_shots`) ve uzun degajlarda (`kicking`) top havada daha az sürtünmeye maruz kalır ve daha hızlı/uzağa gider.
>    - **Hızlı Maç Motoru (`QME`):** Simüle edilen maçlarda (özellikle Güney Amerika `CONMEBOL` Dünya Kupası Elemeleri ve `Copa Libertadores` maçlarında) yüksek rakımlı ev sahibi takımın 2. yarı gol beklentisine (`Home Advantage Multiplier`) doğrudan pozitif bonus ekler!

| Şehir Kolonu (`city.xml`) | FourCC | Tip / Aralık | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :---: | :---: | :--- |
| **`altitude_ft`**<br>*(Rakım — Feet/Metre)* | `Calt` | `int16` (`0..15000 ft` / `0..4572 m`) | Yukarıda detaylandırılan **Yüksek Rakım Kondisyon Tükenme Çarpanı (`+15%..+45%` deplasman yorgunluğu)**, top hava direnci fiziği ve `QME` ev sahibi avantajı. |
| **`attraction`**<br>*(Şehir Çekiciliği / Yaşam Kalitesi)* | `Catt` | `uint8` (`1..20`) | **Transfer ve Sözleşme İkna Çarpanı:** Oyuncunun (ve ailesinin) o şehirde yaşama isteğini belirler. Londra, Madrid, Paris, Milano, İstanbul gibi `Catt = 18..20` olan şehirlerdeki kulüpler yabancı yıldızları (`adaptability` düşük olsa bile) daha kolay ikna ederken; `Catt <= 6` olan küçük/sanayi/uzak şehirlerdeki kulüpler aynı oyuncuyu getirmek için **`+10%..+25%` daha yüksek maaş (`wage_per_week`)** teklif etmek zorunda kalır! |
| **`inhabitants`**<br>*(Nüfus Dilimi)* | `Cinh` | `enum` (`0: 0–1.000` $\rightarrow$ `20: 10.000.000+`) | **1) `Newgen` (`Youth Intake`) Havuzu:** Şehir nüfusu ne kadar büyükse o şehirden her yıl çıkan genç oyuncu adayı sayısı ve yüksek `PA` olasılığı (`youth_recruitment` ile çarpılarak) o kadar artar.<br>**2) Stadyum Büyütme Potansiyeli:** Kulüp büyüdüğünde maksimum seyirci (`maximum_attendance`) ve yeni stadyum kapasite tavanını sınırlar. |
| **`latitude` & `longitude`**<br>*(Enlem ve Boylam)* | `Clat`, `Clon` | `float` (`-90..+90`, `-180..+180`) | **1) Küresel Mesafe (`Haversine` Formülü) ve Seyahat Yorgunluğu (`Pjad`):** İki şehir arasındaki gerçek kuş uçuşu kilometre mesafesini hesaplar! Uzak deplasmanlar (örn. Avrupa kupasında Kazakistan/Azerbaycan deplasmanı veya Güney Amerika/Asya milli takım seyahati) oyuncuların **`Pjad` (`Jadedness` / Yorgunluk)** değerini artırır ve antrenman gününü yolda (`Travel Day`) harcatır.<br>**2) Bölgesel Lig Kümeleme:** Alt liglerde (`Regional Divisions` — Kuzey/Güney/Doğu/Batı grupları) takımları her sezon sonunda coğrafi koordinatlarına göre otomatik olarak doğru gruba yerleştirir!<br>**3) Seyahat Maliyeti:** Kulübün deplasman ulaşım giderlerini (`Other / Travel Costs`) belirler. |
| **`weather`**<br>*(İklim / Hava Durumu Profili)* | `Cwea` | `int` (`weather.xml` FK) | Şehrin 4 mevsimlik (`Spring`, `Summer`, `Autumn`, `Winter`) rüzgar, yağış ve sıcaklık olasılık dağılımına bağlanır (bkz. Bölüm 5.3). |
| **`language`** & **`local_region`** | `Clan`, `Clre` | `int` | Şehirde konuşulan yerel dili (aynı ülkede farklı dil konuşulan şehirler için: örn. İspanya'da Katalanca/Baskça, İsviçre/Belçika/Kanada şehirleri) ve şehrin bağlı olduğu yerel bölgeyi (`local region.xml`) belirler. |

---

### 5.2. Stadyum (`Stadium` 18 Kolon & `stadium.xml` 77 Alan) Tablosunun Tüm Kolonları

Kaynak: [`Stadium`](../fm26save/_core/models/stadiums.py#L12-L42) ve `editor.fmf/stadium.xml`.

| Stadyum Kolonu | FourCC | Tip / Aralık | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :---: | :---: | :--- |
| **`capacity`**, **`seating_capacity`**, **`used_capacity`**, **`all_seater_capacity`** | `Scap`, `Ssea`, `Susc`, `Sasc` | `int32` | **1) Maksimum Gişe Tavanı:** Bir maçta satılabilecek maksimum bilet sayısını sınırlar.<br>**2) UEFA / Lig Tam Koltuklu (`All-Seater`) Kuralı:** Kıtasal kupalarda ve üst liglerde ayakta seyirci (`capacity - seating_capacity`) kabul edilmez; yalnızca `seating_capacity` (veya `all_seater_capacity`) kadar bilet satılabilir! |
| **`expansion_capacity`**<br>*(Genişletme Kapasite Tavanı)* | `Sexp` | `int32` | Mevcut stadyumun mimari olarak büyütülebileceği **maksimum nihai kapasitedir**. Yönetimden *"Stadyumu Büyüt (`Expand Stadium`)"* talep edildiğinde `capacity < expansion_capacity` ise mevcut stadyuma tribün eklenir; `capacity == expansion_capacity` ise daha fazla büyütülemez, yalnızca **"Yeni Stadyum İnşa Et (`Build New Stadium`)"** seçeneği kalır! |
| **`pitch_length_m` & `pitch_width_m`** (+ `min/max_pitch_*`) | `Spln`, `Spwd`, `Smpl`, `Smpw`, `Sxpl`, `Sxpw` | `int` (`90..120m` × `45..90m`) | **3B Maç Motoru Saha Geometrisi (`simatch.fmf`):** Her sezon başında zemin bakım görevlisi (`Groundsman`) teknik direktöre saha boyutlarını (`Standart 105×68m`, `Dar/Kısa`, `Geniş/Uzun`) sorar:<br>- **Geniş ve Uzun Saha (Örn. `105×68m` veya `110×70m`):** `tiki_taka`, `wing_play` ve hızlı (`pace`/`acceleration`) takımlara boş alan açar; rakibin `gegenpress` yoğunluğunu düşürür (koşulacak alan büyür).<br>- **Dar ve Kısa Saha (Örn. `100×64m`):** `park_the_bus`, `catenaccio`, `route_one` ve merkezden oynayan fiziksel (`strength`/`jumping_reach`) takımların alanı kolayca kapatmasını sağlar; `long_throws` (uzun taç) menzilini altıpas içine sokar! |
| **`pitch_type`**<br>*(Çim / Zemin Türü)* | `Spty` | `enum` (`1..7`: `Grass` Doğal Çim, `Synthetic New/Old` Suni Çim, `Hybrid / Desso GrassMaster` Hibrit, `Gravel/Clay/Sand` Toprak) | **1) Top Sekme Hizi ve Yuvarlanma Sürtünmesi:** Hibrit (`Hybrid`) ve Doğal Çim (`Grass`) standart fizik sunarken; **Suni Çim (`Synthetic`)** üzerinde top daha hızlı seker ve kayar (`first_touch` zorlaşır), ayrıca oyuncuların maç içi **`raw_condition` kaybını ve eklem/bağ sakatlığı (`Injury Roll`) olasılığını `%15..%25` artırır**!<br>**2) Lig Kuralları:** Birçok üst lig (`competition_rules`) suni çime izin vermez; kulüp üst lige çıktığında zorunlu olarak doğal/hibrit çime geçme maliyeti öder. |
| **`pitch_condition`** (`1..200`), **`pitch_deterioration_rate`** (`Sdtr`), **`pitch_recovery_rate`** (`Sprr`) | `Sptc`, `Sdtr`, `Sprr` | `uint8` (`1..200` / `1..20`) | **Zemin Bozulması ve Çamur Fiziği:** Yağmurlu/karlı maçlar ve yoğun fikstürde (stadyumu 2 takım paylaşıyorsa veya alt yaş takımları da kullanıyorsa) zemin `Sdtr` hızıyla bozulur (`Terrible` / `Poor` / Çamurlu zemin):<br>- Bozuk zeminde yerden kısa pas (`passing`) ve top sürme (`dribbling`) sırasında **topun rastgele sekme (`bobble`) olasılığı fırlar**, `tiki_taka` takımları felç olurken uzun top (`route_one` / `direct`) avantaj kazanır.<br>- Bozuk zemin **ayak bileği ve diz burkulması (`twisted ankle` / `knee ligament`) sakatlıklarını katlar**! Yönetimden *"Zemini Yenile (`Relay Pitch`)"* isteyerek düzeltilir. |
| **`undersoil_heating`**<br>*(Alttan Isıtma)* | `Sush` | `bool` | Kış aylarında (`weather.xml` `Freezing` / `Snow`) zeminin donmasını (`Frozen Pitch`) ve maçın yoğun kar/buzlanma nedeniyle **Ertelenmesini (`Match Postponed - Waterlogged/Frozen Pitch`)** engeller! Birçok üst ligde stadyum lisans şartıdır. |
| **`is_covered` & `retractable_roof`**<br>*(Kapalı Çatı / Açılır-Kapanır Çatı)* | `Scov`, `Srrf` | `bool` | Yağmurlu, karlı ve fırtınalı havalarda çatı kapatılarak maçın **tamamen kuru/rüzgarsız (`Dry / No Wind`)** ideal zeminde oynanmasını sağlar ve taraftar akustiğini (`Home Advantage`) güçlendirir. |
| **`owner_club_uid` / `owner_type` & `annual_rent`** | `Sowi`, `Soty` | `int` / `enum` (`Club`, `Council/Belediye`, `Private`) | Stadyum kulübe ait değilse (`Council` / Belediye veya kiralıksa), kulüp her yıl stadyum kirası öder, gişe/kurumsal gelirlerin bir kısmını paylaşır ve stadyum büyütme taleplerinde belediye engeline takılabilir (`Buy Stadium` ile satın alınabilir). |
| **`build_date` & `decay`**<br>*(İnşa Tarihi ve Eskime)* | `Sbld`, `Sdcy` | `date`, `1..20` | **25 Yıl Kuralı:** Oyun motorunda bir kulüp son **20–25 yıl içinde** yeni stadyum yapmışsa yönetim yeni bir stadyum inşasını neredeyse her zaman reddeder! Çok eski (`build_date < 1970`) ve `Sdcy` (yıpranma) değeri yüksek stadyumlarda ise yıllık bakım gideri (`Stadium Maintenance`) yüksektir ve yeni stadyum talebi kolayca onaylanır. |
| **`used_by_national_team`** | `Subn` | `enum` (`All`, `Major`, `U21`, `None`) | Milli takım maçlarının ve kupa finallerinin (`Neutral Venue`) bu stadyuma atanmasını sağlar. |

---

### 5.3. Hava Durumu (`weather.xml` — 94 Kolon: 4 Mevsim × Yağış, Rüzgar, Sıcaklık)

Kaynak: `editor.fmf/weather.xml` (`Wsp*` İlkbahar, `Wsu*` Yaz, `Wau*` Sonbahar, `Wwi*` Kış dağılımları).

| Hava Durumu Parametresi | FourCC Önekleri | 3B Maç Motoru (`simatch.fmf`) Fiziği ve Oyuncu Kondisyonuna Etkisi |
| :--- | :---: | :--- |
| **Yağış (`Precipitation`: `Dry`, `Wet/Rain`, `Drizzle`, `Shower`, `Downpour`, `Snow/Sleet`)** | `W*dr`, `W*we`, `W*sn` | **1) Islak Zemin (`Wet` / `Drizzle`):** Top çim üzerinde suya çarpıp hızlanır (`skidding ball`); yerden paslar hız kazanır ama kalecinin topu tek hamlede tutma (`handling`) olasılığı düşer, seken top (`rebound`) artar.<br>**2) Sağanak Yağış (`Downpour` / `Waterlogged`) ve Kar (`Snow`):** Su birikintileri topun hızını aniden keser; yerden kısa pas ve dripling neredeyse imkansızlaşır, kondisyon (`raw_condition`) çok hızlı erir ve maçın ertelenme olasılığı doğar (`undersoil_heating` / `retractable_roof` yoksa). |
| **Rüzgar (`Wind`: `Calm`, `Breezy`, `Gusty`, `Strong`, `Gale`)** | `W*ca`, `W*br`, `W*gu`, `W*st`, `W*ga` | **Havadan Uzun Top ve Orta Fiziği:** `Strong` ve `Gale` (Fırtına) rüzgarında havadan atılan uzun pasların (`passing`/`kicking`), kornerlerin (`corners`) ve ortaların (`crossing`) uçuş yörüngesi rüzgar vektörüyle sapar! Rüzgarlı havada `route_one` / `wing_play` isabeti düşerken yerden kısa pas (`short passing`) daha güvenlidir. |
| **Sıcaklık (`Temperature`: `Freezing <0°C` $\rightarrow$ `Very Hot >32°C`)** | `W*tp`, `W*t1..t8` | **1) Aşırı Sıcak (`Hot` / `Very Hot >30°C`):** Maç içinde su molası (`Cooling Break`) tetiklenir ve oyuncuların **`raw_condition` (`Pcon`) erime hızı `%20..%35` artar** (yüksek `gegenpress` ve `tempo` oynayan takımlar 70. dakikada çöker).<br>**2) Dondurucu Soğuk (`Freezing <0°C`):** Kas çekmesi (`hamstring`/`calf strain`) sakatlık olasılığını artırır ve zemini sertleştirir (`Hard/Frozen Pitch`). |

---

### 5.4. Ülke (`nation.xml` — 64 Kolon), Kıta (`continent.xml`), Bölge (`local region.xml`), Derbi (`derby.xml`) ve Anlaşmalar (`agreement.xml`)

| Tablo & Kolon Adı | FourCC | Tip / Aralık | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :---: | :---: | :--- |
| **`nation.youth_rating`**<br>*(Ülke Gençlik Derecesi)* | `NYRt` | `int16` (`1..200`) | **Ülkeden Çıkacak `Newgen` (`Wonderkid`) Tavanının Küresel Belirleyicisidir:** Brezilya (`163`), Fransa (`155`), Almanya/İspanya/İngiltere/Arjantin (`140..155`) gibi yüksek `NYRt` ülkelerinden her yıl çok sayıda yüksek `PA` (`160..200`) oyuncu çıkarken; düşük `NYRt` ülkelerinde kulübün tesisleri `20/20` olsa bile çıkan oyuncuların ortalama `PA` tavanı ülke çarpanıyla sınırlandırılır! *(FM22+ itibarıyla `Dynamic Youth Rating` sayesinde ülkenin FIFA sıralaması, lig itibarı ve mali gücü arttıkça `NYRt` zamanla yükselebilir).* |
| **`nation.game_importance`**<br>*(Futbolun Ülkedeki Önemi)* | `Ngim` | `enum` (`1..4`: `Very Important` $\rightarrow$ `Unimportant`) | **1) `Newgen` Kalitesi:** `NYRt` ile doğrudan çarpılır (`Very Important = 1.00x`, `Important = 0.85x`, `Less Important = 0.65x`, `Unimportant = 0.40x`)!<br>**2) Seyirci ve Sponsorluk:** Ülkedeki tüm kulüplerin bilet talebini ve yerel sponsorluk gelirlerini çarpar. |
| **`nation.economic_factor`** & **`state_of_development`** | `Necf`, `Nsod` | `1..20`, `enum` (`Developed`, `Developing`, `Third World`) | **1) Oyuncu Fiyatları ve Maaşlar (`[REF-EKO]`):** `Developed` ve `Necf = 18..20` olan ülkelerde oyuncu piyasa değerleri ve maaş talepleri yüksekken, `Developing` / düşük `Necf` ülkelerde aynı `CA`/`PA`'ya sahip genç yetenekler çok daha düşük bonservis ve maaşla (`10x` daha ucuza!) alınabilir.<br>**2) Uyum (`Adaptability`):** `Nsod` farkı göç eden oyuncunun uyum süresini belirler. |
| **`nation.years_to_gain_nationality`** | `Nygc`, `Ngnc` | `int` (`2..10` yıl) + `Cumulative/Continuous` | Yabancı bir oyuncunun o ülkede kaç gün/yıl oynadıktan sonra vatandaşlık (`second_nation_ids`) kazanıp yabancı kontenjanından düşeceğini belirler. |
| **`nation.tax_rules`** *(Vergi Kuralları)* | `Ntxr` | `list` (Gelir dilimi `%` vergi oranları) | Oyuncuya ödenen **Brüt Maaş (`Gross Wage`)** ile oyuncunun cebine giren **Net Maaş (`Net Wage`)** arasındaki farkı belirler! Vergi oranı yüksek ülkelerdeki (`%45..%50`) kulüpler, vergi oranı düşük ülkelerdeki (`%0..%20`) kulüplerin net maaş teklifiyle yarışabilmek için çok daha yüksek brüt maaş bütçesi (`wage_budget`) harcamak zorundadır. |
| **`agreement.xml`** *(Uluslararası Anlaşmalar: `EU`, `Cotonou`, `EFTA`, `Mercosur` vb.)* | `Agna`, `Agnt` | `8 kolon` (Üye ülke listesi) | **`Treated as Non-Foreign` (Yabancı Sayılmama Kuralı):** Lig kurallarında (`competition_rules`) *"Anlaşma ülkeleri yabancı sayılmaz"* seçildiğinde (örn. İspanya/Fransa'da `Cotonou` anlaşması sayesinde Afrika ülkelerinin yabancı sayılmaması veya AB içi serbest dolaşım) bu tablodaki `Agnt` ülke listesi kontrol edilir. |
| **`derby.xml`** *(Derbiler ve Ezeli Rekabetler — 16 Kolon)* | `Drep`, `Dcl1`, `Dcl2`, `Dtyp` | `1..200` itibar | Maçın bir **Derbi (`Local` / `National` / `Historic Derby`)** olduğunu işaretler: Maçta `important_matches` ve `temperament`/`aggression` özelliklerini tetikler, tribünleri `%100` doldurur (`maximum_attendance`), hakem baskısını (`Oprs`) artırır ve maç sonucunun hem `Board Confidence` hem de `Supporter Confidence` üzerindeki etkisini **`2.5x`** katlar! |


---

## Bölüm 6 — Sözleşmeler (`contracts`), Maddeler (`clauses` & `contract.xml`), Sakatlıklar (`injuries` & `injury-types`) ve Cezalar (`suspensions`) Tablolarının Tüm Kolonları

Kaynak modeller: [`Contract`](../fm26save/_core/models/contracts.py#L72-L120), [`Clause`](../fm26save/_core/models/contracts.py#L38-L48), [`ClauseKind`](../fm26save/_core/models/contracts.py#L12-L35), [`InjuryRecord`](../fm26save/_core/models/injuries.py#L22-L45), [`InjuryType`](../fm26save/_core/models/injuries.py#L12-L20), [`Suspension`](../fm26save/_core/models/suspensions.py#L12-L32) ve `editor.fmf` (`contract.xml` `66` alan, `injury.xml` `29` alan).

---

### 6.1. Sözleşme (`Contract` — 24 Kolon + `unknown` Sözleşme Ekonomisi) ve Sözleşme Maddeleri (`Clause` / `contract.xml`)

| Kolon Adı (`Contract`) | FourCC | Tip / Enum | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :---: | :--- | :--- |
| `player_id`, `club_uid`, `division_uid` | `Cply`, `Cclb` | `int32` | Sözleşmenin ait olduğu oyuncu, kulüp ve lig bağlantısı. |
| **`wage_per_week`**<br>*(Haftalık Brüt Maaş)* | `Cwag` | `int32` (£/€/\$) | **1) Bütçe Tüketimi:** Kulübün `FinanceMonth.current_wage_bill` kalemine doğrudan eklenir.<br>**2) Piyasa Değeri (`[REF-EKO]`):** Oyuncunun piyasa değerini `+0.3120 × ln(Wage + 1)` artırır (yüksek maaşlı oyuncunun piyasa değeri de yüksek görünür, ancak çok yaşlı/düşük `CA`'lı ise diğer kulüpler maaş yükünden korkup teklif yapmaz!).<br>**3) Vergi:** Ülkenin `Ntxr` vergi dilimine göre net maaşa çevrilir. |
| **`start_date` & `end_date`**<br>*(Başlangıç ve Bitiş Tarihi)* | `Csdt`, `Cedt` | `date` (`year`, `day_of_year`) | **1) Piyasa Değeri Erimesi (`[REF-EKO]`):** Kalan her tam yıl `ln(Value)` değerine `+0.1850` katar; son **12 aya** girildiğinde oyuncunun piyasa değeri hızla düşer.<br>**2) `Bosman` Kuralı:** `end_date` tarihine **6 ay (`180 gün`)** kaldığında yabancı ülke kulüpleri (İngiltere içi hariç, orada 1 ay) bonservis ödemeden doğrudan oyuncuyla ön sözleşme (`Approach to Sign`) imzalayabilir! |
| **`squad_status` & `promised_squad_status`**<br>*(Kadro Statüsü / Vaat Edilen Oynama Süresi)* | `Csqs` | `SquadStatus` (`Star Player` `1`, `Important Player` `2`, `Regular Starter` `3`, `Squad Player` `4`, `Impact Sub` `5`, `Fringe Player` `6`, `Emergency Backup` `7`, `Future Prospect` `8`, `Youth` `9`) | **1) `[REF-AI]` `TSF_AGREED_PLAYING_TIME (+45)`:** AI kadro seçiminde `Star Player` ve `Important Player` statüsündeki oyunculara `+45` öncelik verir.<br>**2) `Playing Time Happiness` & `[REF-TE]` `Player Buy-In`:** Motor her oyuncunun son 20 maçta ilk 11 başladığı dakika yüzdesini sözleşmesindeki `squad_status` beklentisiyle (`Star Player >= %80`, `Important >= %65`, `Regular >= %50`) karşılaştırır. Beklentinin altında kalınırsa oyuncu önce uyarır, sonra soyunma odası isyanı (`PromiseImpact` ve `0.20 × PlayingTimeHappiness` çöküşü) başlatır! |
| **`contract_type`** | `Ctyp` | `ContractType` (`FullTime`, `PartTime`, `Amateur`, `Youth`, `NonContract`) | **1) Antrenman Saatleri (`[REF-ANT]`):** `FullTime` oyuncular haftanın tüm antrenman seanslarına katılırken; `PartTime` (Yarı Zamanlı) oyuncular haftada yalnızca **2 gün (4 seans)** antrenman yapabilir (`CA` gelişimi çok yavaştır!).<br>**2) Bedelsiz Ayrılık:** `Amateur` ve `NonContract` (Maç başı ücretli) oyunculara herhangi bir kulüp her an `0£` bonservisle imza attırabilir. |
| **`transfer_status` & `loan_status`** | `Ctrs`, `Clns` | `TransferStatus` (`TransferListed`, `ListedByRequest` vb.) | Oyuncu `TransferListed` (Transfer Listesinde) ise `[REF-EKO]` piyasa değeri ve kulübün kabul edeceği bonservis (`Asking Price`) **`%30..%50` kırpılır**; temsilciler (`Apim`) oyuncuyu diğer kulüplere önermeye başlar. |
| **`asking_price`** | `Casp` | `int32` | Kulübün oyuncu için belirlediği etiket fiyatı. AI kulüpler bu fiyata eşit bir teklif yaptığında başkan/DoF (veya sözleşmede `Asking Price` vaadi varsa) teklifi otomatik kabul eder. |
| **`unknown.money_a` (`loyalty_bonus`)** | `Clbo` | `int32` | **Sadakat Primi (`Loyalty Bonus`):** Sözleşme süresi boyunca her ay taksitle ödenir. **Kritik Kural:** Kulüp oyuncuyu kendi isteğiyle satarsa (oyuncu `Transfer Request` vermemişse), sadakat priminin **kalan tüm taksitleri (`remaining money_a`) satış anında oyuncuya toplu olarak ödenir** ve transfer gelirinden düşülür! Oyuncu kendisi ayrılmak isterse (`Listed by Request`) kalan sadakat primini yakar. |
| **`unknown.money_b` (`agent_fee`)** | `Cagf` | `int32` | Sözleşme imzalanırken temsilciye (`Agent`) kulüp kasasından (`FinanceMonth.balance` ve `transfer_budget`) peşin ödenen komisyon. |
| **`clauses`** (`ClauseKind` — 14 Tür & `contract.xml` 66 FourCC) | `Ccls` | `Clause(kind, amount, info)` | **1) Serbest Kalma Maddeleri (`Minimum Fee Release Clause` — `Domestic` / `ForeignClubs` / `HigherDivision` / `Relegation` / `ChampionsLeague`):** Koşul sağlandığında ve `amount` kadar teklif geldiğinde kulübün teklifi **reddetme hakkı yoktur**; doğrudan sözleşme aşamasına geçilir!<br>**2) Maç ve Gol Bonusları (`Appearance Fee`, `Goal Bonus`, `Clean Sheet Bonus`, `Unused Substitute Fee`, `Team of the Year Bonus`):** Her maç/gol sonrasında kulüp kasasından otomatik düşülür; yüksek `ambition` oyuncuların maç içi motivasyonunu destekler.<br>**3) Maaş Artış Maddeleri (`Yearly Wage Rise %`, `Promotion Wage Rise %`, `Relegation Wage Drop %`, `Wage After X League Apps`):** Koşul tetiklendiği gün `wage_per_week` otomatik olarak güncellenir *(özellikle `Relegation Wage Drop %` küme düşen kulübün iflas etmesini önleyen en önemli maddedir!)*.<br>**4) Süre Uzatma Opsiyonları (`Optional Contract Extension by Club`, `One Year Extension After League Games Final Season`):** Kulübün tek taraflı kararıyla veya son sezonda belirli maç sayısına ulaşıldığında `end_date` tarihini `1–3 yıl` uzatır.<br>**5) Satış Payı (`Sell On Fee %` / `Sell On Fee Profit %`):** Oyuncu gelecekte satıldığında bonservisin `%X`'ini oyuncunun kendisine veya eski kulübüne aktarır. |

---

### 6.2. Sakatlık Kayıtları (`InjuryRecord` — 13 Kolon) ve Sakatlık Türleri (`InjuryType` / `server_db/table_6.dat` 48B Struct / `injury.xml` 29 Kolon)

Kaynak: [`InjuryRecord`](../fm26save/_core/models/injuries.py#L22-L45), [`InjuryType`](../fm26save/_core/models/injuries.py#L12-L20), [`docs/FM26_REVERSE_ENGINEERING_SAVE_AND_GAME_FILES.md`](./FM26_REVERSE_ENGINEERING_SAVE_AND_GAME_FILES.md#L110-L180) ve `editor.fmf/injury.xml`.

| Tablo & Kolon Adı | FourCC / Ofset | Tip / Aralık | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :---: | :---: | :--- |
| **`InjuryType.min_days` & `extra_days`** | `Imnd`, `Iexd` (`+8`, `+10`) | `int16` (Gün) | Sakatlığın baz iyileşme süresi (`Min Days` ile `Min Days + Extra Days` arasında; tedaviyi yapan kişi `Specialist` / `Club Physio` `physiotherapy` özelliğine göre süreyi alt sınıra çeker). |
| **`InjuryType.inactive_ratio`** | `Iina` (`+12`) | `float32` (`0.0..1.0`) | Sakatlık süresinin yüzde kaçında oyuncunun hiç antrenman yapamayacağını ve `raw_condition` / `raw_match_sharpness` değerlerinin sıfıra yaklaşacağını belirler. |
| **`InjuryType.occurrence_ratio`** | `Iocc` (`+16`) | `float32` | Genel sakatlık havuzunda bu sakatlığın çıkma ağırlığı (`Hamstring`, `Twisted Ankle`, `Groin Strain` yüksek; `Cruciate Ligament / ACL` düşük). |
| **`InjuryType.is_recurring`**<br>*(Kronik / Nükseden Sakatlık)* | `Irec` (`+29` bit) | `bool` | **`True` ise (Örn. `Hamstring`, `Groin`, `Knee Tendonitis`, `Back Strain`):** Oyuncu bu sakatlığı bir kez geçirdiğinde vücut geçmişine kaydedilir; gelecekte aynı bölgeden sakatlanma olasılığı kalıcı olarak yükselir ve gözlemci raporunda **"Kronik Sakatlık Sorunu (`Recurring Injury Problem`)"** uyarısı çıkar! |
| **`InjuryType.is_contagious`**<br>*(Bulaşıcı Hastalık)* | `Icon` (`+29` bit) | `bool` | **`True` ise (`Flu` Grip, `Virus`, `Food Poisoning`, `Chest Infection`):** Oyuncu **"Eve Gönder (`Send Home`)"** yerine **"Kulüp Doktorunda Tedavi Et (`Leave with Club Doctor`)"** seçeneğiyle tesiste tutulursa, hastalık soyunma odasındaki **diğer takım arkadaşlarına (`Social Groups` öncelikli) bulaşır!** |
| **`InjuryType.severity` & `cause` & `category`** | `Isev`, `Icau`, `Icat` | `enum` | **Kalıcı `CA` ve Fiziksel Özellik Kaybı:** `Severity == Serious / Career Threatening` olan ağır sakatlıklar (`Cruciate Ligament Damage`, `Broken Leg`, `Achilles Tendon Rupture`, `Damaged Spine`) iyileşme sürecinde oyuncunun **`acceleration`, `pace`, `agility`, `balance`, `natural_fitness` ve toplam `CA` değerinden kalıcı olarak `-1` ila `-4` puan (`-5..20` `CA`) siler** ve `injury_proneness` değerini artırır! |
| **`InjuryType.can_play_with_injections`** | `Iinj` | `bool` | Önemli bir maç öncesinde oyuncunun **Ağrı Kesici İğne (`Protective Equipment / Painkilling Injection`)** ile 1 maçlığına oynatılıp oynatılamayacağını belirler (iğneyle oynatılırsa maç sonunda sakatlık süresi **`1.5x..2.5x`** uzar ve oyuncuyla ilişki bozulabilir). |
| **`InjuryRecord`** (`player_id`, `injury_type_id`, `start_date`, `end_date`, `estimated_days_remaining`, `severity_level`) | — | `13 kolon` | Kayıt dosyasındaki aktif sakatlık kaydı. `end_date` yaklaştığında oyuncu `Light Training` (Turuncu `Inj` ikonu) fazına geçer ve maksimum `45–60 dakika` oynatılması önerilir. |

---

### 6.3. Cezalar (`Suspension` — 11 Kolon / `PlayerSuspension`)

Kaynak: [`Suspension`](../fm26save/_core/models/suspensions.py#L12-L32).

| Kolon Adı (`Suspension`) | Tip | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :---: | :--- |
| `player_id`, `competition_uid`, `ban_type`, `scope` | `int` / `enum` | Cezanın sadece **belirli bir turnuvada (`CompetitionSpecific` — örn. Şampiyonlar Ligi)** mı, **tüm yerel resmi maçlarda (`DomesticAll`)** mı yoksa **küresel (`Global` — örn. uzun süreli doping/disiplin cezası)** mı geçerli olduğunu belirler. |
| `matches_banned`, `matches_served`, `matches_remaining` | `uint8` | Kalan maç cezası sayısı (`matches_remaining > 0` ise oyuncu ilgili turnuvada maç kadrosuna `Ineligible / Suspended` olarak kilitlenir). |
| `start_date` & `end_date` | `date` | Tarih bazlı cezalarda (`Global Ban` / `Touchline Ban`) cezanın biteceği günü belirler. |

---

## Bölüm 7 — Taktik (`tactics`), Duran Top (`set-pieces`), Antrenman (`training`), Mentorluk (`mentoring`), İş İlanları, Turnuvalar ve İstatistik Tablolarının Tüm Kolonları + 81/75 `.dat` Konteyner Bölümleri

---

### 7.1. Taktik (`Tactic`, `TacticSlot`, `TacticSettingUnit`) ve Duran Top (`SetPieceRoutine`) Kolonları

Kaynak: [`Tactic`](../fm26save/_core/models/tactics.py#L48-L85), [`TacticSlot`](../fm26save/_core/models/tactics.py#L12-L35), [`SetPieceRoutine`](../fm26save/_core/models/tactics.py#L88-L110).

| Tablo & Kolon Adı | Tip / Aralık | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :---: | :--- |
| **`Tactic.mentality`**<br>*(Takım Zihniyeti: `Very Defensive` `1` $\rightarrow$ `Very Attacking` `7`)* | `uint8` (`1..7`) | **Tüm Takım Kaydırıcılarının Taban Ofsetidir:** Zihniyet yükseldikçe tüm oyuncuların bireysel risk alma (`tries_killer_balls`), ileri çıkış sıklığı, pas direktliği (`directness`), tempo (`tempo`) ve savunma çizgisi yüksekliği otomatik olarak yukarı kayar. Ayrıca FM27 `[REF-TE]` denkleminde `MentalityMod (-10..+5)` terimini üretir. |
| **`Tactic.in_possession_formation` & `out_of_possession_formation`** | `uint8` (`1..60`) | FM26/FM27 **Çift Dizilişli (`IP` vs `OOP`) Motor:** Takım topa sahipken `in_possession_formation` şeklini, topu kaybettiği anda ise `out_of_possession_formation` şeklini alır. İki diziliş arasındaki geçiş karmaşıklığı `[REF-TE]` içinde `C_FormationTransitions` (`0.25` ağırlık) terimini oluşturur. |
| **`TacticSlot`** (`slot_index` `0..10`, `player_id`, `ip_position`, `oop_position`, `ip_role`, `oop_role`, `duty`, `player_instructions_bitmask`) | `10 kolon` | Sahadaki 11 koltuğun her biri için `[REF-ROL]` denklemini (`0.60 × IP_Score + 0.40 × OOP_Score`) ve `OOP_PROXIMITY_MATRIX_24` geçiş mesafesini çalıştırır. `player_instructions_bitmask` ise oyuncuya özel talimatları (`Shoot Less Often`, `Dribble More`, `Tackle Harder`, `Mark Tighter`, `Stay Wider`, `Cut Inside` vb.) 3B maç motoruna iletir ve FM27 `C_PlayerInstructions` karmaşıklığını artırır. |
| **`TacticSettingUnit`** (`setting_id`, `value`) | `5 kolon` | Takım talimatlarını (`Tempo`, `Passing Directness`, `Width`, `Line of Engagement`, `Defensive Line`, `Trigger Press`, `Counter-Press`, `Counter`, `Work Ball Into Box`, `Play Out of Defence`, `Time Wasting` vb.) tutar. |
| **`SetPieceRoutine`** (`routine_type`, `delivery_target`, `swing_type`, `slot_assignments`, `taker_priority`) | `6 kolon` | `[REF-AI]` Duran Top Öncelik Kuyruklarını (`Aerial Threat`: `jumping_reach + heading + bravery + strength`; `Box Threat`: `anticipation + finishing + off_the_ball`; `Creator`: `corners/free_kick_taking + crossing + technique`; `Recovery Defender`: `pace + acceleration + positioning + decisions`) sahadaki 10 oyuncuya otomatik eşleştirir. |

---

### 7.2. Takım Antrenmanı (`TeamTraining`, `TrainingWeek`, `TrainingSchedule`) ve Mentorluk (`MentoringGroup`) Kolonları

Kaynak: [`TeamTraining`](../fm26save/_core/models/training.py#L35-L60), [`MentoringGroup`](../fm26save/_core/models/training.py#L63-L85).

| Tablo & Kolon Adı | Tip | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :---: | :--- |
| **`TrainingWeek.days`** (`7 gün × 3 slot = 21 seans ID`) | `tuple[int, ...]` | Haftanın 7 günündeki Sabah (`Slot 1`), Öğleden Sonra (`Slot 2`) ve Ekstra (`Slot 3`) seans ID'lerini (`FM26_TRAINING_SESSIONS` `44` seans / `FM27_TRAINING_SESSIONS` `59` seans) tutar. `[REF-ANT]` ve `[REF-TE]` denklemlerine doğrudan girdi verir. |
| **`MentoringGroup`** (`group_id`, `club_uid`, `member_player_ids`, `leader_player_id`, `estimated_influence_map`) | `8 kolon` | **Kişilik (`Personality`) ve `PPM` (`Trait`) Aktarım Motoru:**<br>- En az **3 oyuncudan** oluşmalıdır.<br>- Grup liderinin (`leader_player_id`: yaşı `>=24`, soyunma odası statüsü `Team Leader` veya `Highly Influential` olan kıdemli oyuncu) `determination` ve 8 gizli `Personality` özelliği (`professionalism`, `ambition`, `loyalty`, `pressure`, `temperament`, `sportsmanship`) ile oyun içi tercihleri (`Trait`/`PPM`), gruptaki genç oyunculara (`14..23` yaş, `estimated_influence: Light / Medium / Significant`) her hafta kademeli olarak aktarılır! *(Uyarı: Kıdemli oyuncunun `professionalism` veya `determination` değeri düşükse genç oyuncunun karakterini **bozar**!).* |

---

### 7.3. İş İlanları (`JobVacancy`), Turnuvalar (`Competition`, `Stage`, `LeagueTable`, `Fixture`, `CompetitionRules`, `TransferWindow`) Kolonları

Kaynak: [`JobVacancy`](../fm26save/_core/models/competitions.py#L12-L35), [`Competition`](../fm26save/_core/models/competitions.py#L38-L55), [`Stage`](../fm26save/_core/models/competitions.py#L58-L78), [`LeagueTable`](../fm26save/_core/models/competitions.py#L125-L150), [`LeagueTableRow`](../fm26save/_core/models/competitions.py#L81-L122), [`Fixture`](../fm26save/_core/models/competitions.py#L175-L235), [`CompetitionRules`](../fm26save/_core/models/competitions.py#L238-L275), [`TransferWindow`](../fm26save/_core/models/competitions.py#L278-L300) ve `editor.fmf/comp.xml` (`302` alan).

| Tablo & Kolon Adı | FourCC | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :---: | :--- |
| **`JobVacancy`** (`club_uid`, `job_role`, `status`, `applicant_person_ids`, `leading_candidate_id`) | — | Kulüpteki boş koltukları (`Manager`, `DoF`, `Coach`, `Scout`, `Physio`) ve başvuran adayları tutar; başkanın `NT27..NT40` eğilimlerine göre `leading_candidate_id` seçilir. |
| **`Competition`** (`id`, `unique_id`, `name`, `reputation`, `level`, `type`) | `Crep`, `Clvl` | **Lig İtibarı (`Competition.reputation` `1..200`):**<br>1) O ligde oynayan tüm kulüplerin ulaşabileceği maksimum `Club.reputation` ve sponsorluk/TV gelirini (`tv_revenue`) belirler.<br>2) Oyuncuların o lige transfer olma isteğini ve `Ballon d'Or` / Altın Ayakkabı (`Golden Boot` `1.0x / 1.5x / 2.0x` lig katsayısı) puanlarını çarpar. |
| **`LeagueTableRow`** (`club_uid`, `position`, `played`, `won`, `drawn`, `lost`, `goals_for`, `goals_against`, `goal_difference`, `points`, `points_deducted`, `form`, `qualification_flag`) | — (`20 kolon`) | Anlık lig puan durumu, averaj, finansal ceza/kayyum nedeniyle silinen puanlar (`points_deducted`) ve şampiyonluk/Avrupa kupası/küme düşme bayrakları (`qualification_flag`). |
| **`Fixture`** (`id`, `competition_uid`, `stage_index`, `date`, `home_club_uid`, `away_club_uid`, `stadium_id`, `attendance`, `referee_id`, `weather_code`, `home_goals`, `away_goals`, `is_played`, `tv_flag`) | — (`27 kolon`) | Maçın oynandığı stadyum (`stadium_id` $\rightarrow$ rakım/zemin), hakem (`referee_id`), seyirci (`attendance` $\rightarrow$ gişe geliri) ve TV yayını (`tv_flag == True` ise her iki kulübe ekstra **Canlı Yayın Ücreti (`TV Facility Fee`)** ödenir ve maç saati değiştirilir). |
| **`CompetitionRules`** (`competition_uid`, `sorting_rules`, `subs_allowed`, `subs_bench_size`, `max_foreign_players`, `min_home_grown_club`, `min_home_grown_nation`, `yellow_card_ban_thresholds`, `prize_money`, `var_enabled`) | — (`10 kolon`) | **Ligin Anayasasıdır:**<br>- `sorting_rules`: Puan eşitliğinde **İkili Averaj (`Head-to-Head`)** mı yoksa **Genel Averaj (`Goal Difference`)** mı bakılacağını belirler.<br>- `subs_allowed` / `subs_bench_size`: Maç içi değişiklik hakkı (`3` veya `5` değişiklik, `3` duraklama fırsatı).<br>- `max_foreign_players` & `min_home_grown_*`: Kadro kayıt (`Squad Registration`) ve maç kadrosu kuralları.<br>- `yellow_card_ban_thresholds`: Kaç sarı kartta (`4`, `5`, `10`) `1 maç` ceza (`Suspension`) tetikleneceğini belirler.<br>- `var_enabled`: Maçta `VAR` ve Yarı Otomatik Ofsayt / Gol Çizgisi Teknolojisi olup olmadığını belirler. |
| **`TransferWindow`** (`nation_id`, `start_date`, `end_date`, `window_type`, `loan_allowed`, `free_agent_allowed`) | — (`7 kolon`) | Ülkedeki Yaz (`Summer`) ve Kış (`Winter`) transfer pencerelerinin açılış ve kapanış (`Deadline Day`) tarihlerini belirler. Pencere kapalıyken yapılan transferler bir sonraki `start_date` tarihinde takıma katılır. |

---

### 7.4. Oyuncu İstatistik Tabloları (`PlayerSeasonStats` 66 Kolon, `PlayerSeasonHistory` 68 Kolon, `PlayerMatchStats` 20 Kolon)

Kaynak: [`PlayerSeasonStats`](../fm26save/_core/models/season_stats.py#L46), [`PlayerSeasonHistory`](../fm26save/_core/models/season_history.py#L12) (`pl_hist_dt.dat`), [`PlayerMatchStats`](../fm26save/_core/models/matches.py#L56).

| Tablo & Kolon Grupları | Kolon Sayısı | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :---: | :--- |
| **`PlayerSeasonStats`** (`appearances`, `subs_appearances`, `minutes_played`, `goals`, `assists`, `expected_goals` [`xG`], `non_penalty_xg` [`npxG`], `expected_assists` [`xA`], `shots_total`, `shots_on_target`, `passes_attempted`, `passes_completed`, `key_passes`, `open_play_key_passes`, `chances_created`, `dribbles_made`, `tackles_attempted`, `tackles_won`, `key_tackles`, `interceptions`, `blocks`, `clearances`, `headers_attempted`, `headers_won`, `key_headers`, `fouls_made`, `fouls_against`, `offsides`, `yellow_cards`, `red_cards`, `mistakes_leading_to_goal`, `conceded`, `clean_sheets`, `saves_held`, `saves_parried`, `saves_tipped`, `expected_goals_prevented` [`xGP`], `penalties_taken`, `penalties_scored`, `penalties_faced`, `penalties_saved`, `distance_covered_km`, `sprints`, `progressive_passes`, `pressures_attempted`, `pressures_completed`, `player_of_the_match`, `average_rating` + 90 dakika başına `_per_90` ve `_percent` türevleri) | **66 Ham + Türev Kolonlar** | **1) `Data Hub` (Veri Merkezi) ve Gözlemcilik Analitiği:** Oyuncunun sezonluk radar grafiklerini ve istatistiksel yüzdelik dilimlerini (`Percentile`) üretir.<br>**2) Yapay Zeka Transfer & Ödül Seçimi:** `average_rating`, `goals`, `assists`, `xG`, `xA`, `xGP` ve `player_of_the_match` sayıları; sezon sonu ödüllerini (`award.xml` — Yılın Oyuncusu, Gol Kralı, Yılın 11'i), oyuncunun `current_reputation` artışını ve veri odaklı (`Data-Driven Scouting`) AI kulüplerin transfer hedeflerini belirler.<br>**3) Sözleşme Bonusları:** `goals`, `appearances`, `clean_sheets` sayaçları doğrudan `Contract.clauses` primlerini tetikler. |
| **`PlayerSeasonHistory`** (`pl_hist_dt.dat`: `season_year`, `club_uid`, `competition_reference`, `apps`, `goals`, `average_rating` + tüm sezon istatistikleri) | **68 Kolon** | Oyuncunun geçmiş yıllardaki kariyer geçmişi (`Career Stats`), bir kulüpte geçirdiği toplam yıl (`Testimonial` jübile maçı ve `Favoured Personnel` uygunluğu) ile `Hall of Fame` puanlamasını tutar. |
| **`PlayerMatchStats`** (`fixture_id`, `player_id`, `rating`, `minutes`, `goals`, `assists`, `xg`, `xa`, `shots`, `passes`, `tackles`, `interceptions`, `distance`, `condition_end` vb.) | **20 Kolon** | Tek bir maçın (`Fixture`) bireysel performans kaydı; son 5 maçlık **Form (`TSF_FORM` / `TSF_MATCH_RATING`)** ortalamasını besler. |

---

### 7.5. Kayıt Dosyasındaki (`.fm` Save) 81 / 75 `.dat` Konteyner Bölümlerinin Tam Haritası

Kaynak: [`extra_sections.py`](../fm26save/extra_sections.py), [`docs/FM26_SAVE_DATABASE_SCHEMA_AND_81_SECTIONS.md`](./FM26_SAVE_DATABASE_SCHEMA_AND_81_SECTIONS.md).

| `.dat` Konteyner Bölümü | İçerdiği Veri Yapısı ve Oyun Motorundaki Görevi |
| :--- | :--- |
| `game.dat` (`server_db` + `client_db`) | Ana veritabanı konteyneri: `table_0.dat` .. `table_25.dat` içindeki tüm oyuncu, kulüp, personel, stadyum, sözleşme ve sakatlık ikili (binary) tablolarını barındırır. |
| `pl_hist_dt.dat` / `pl_hist_id.dat` | Tüm oyuncuların geçmiş sezon kariyer istatistikleri (`PlayerSeasonHistory`) ve indeks tablosu. |
| `non_pl_hist_dt.dat` / `non_pl_hist_id.dat` | Teknik direktör ve personelin geçmiş kulüp/başarı kariyer geçmişi. |
| `person_name_dt.dat` / `first_names.dat` / `surnames.dat` / `common_names.dat` | Kişi isimlerinin string havuzu ve yeni üretilecek `newgen` oyuncuların ülkeye/etnik kökene göre çekileceği ad-soyad frekans sözlüğü! |
| `board_takeover_manager.dat` | Aktif kulüp satışları, konsorsiyum/iş insanı/taraftar vakfı devir görüşmeleri (`Takeovers`), transfer ambargoları ve başkanlık seçimleri. |
| `agent_manager.dat` | Tüm oyuncu temsilcilerinin (`Agent`) müvekkil ağları, komisyon geçmişleri ve insan menajerle olan ilişki durumları. |
| `shortlist_man.dat` | İnsan ve AI teknik direktörlerin takip listeleri (`Shortlists`), gözlemci görevlendirmeleri (`Scouting Assignments`) ve transfer hedefleri. |
| `contract_man.dat` / `transfer_manager.dat` | Devam eden tüm aktif bonservis teklifleri, kiralama teklifleri, taksitli transfer ödemeleri (`Monthly Installments`) ve bekleyen sözleşme görüşmeleri. |
| `hall_of_fame.dat` | Ülke, kıta ve dünya bazında en çok kupa kazanan teknik direktörlerin (`Hall of Fame`) puanları ve sıralaması. |
| `news.dat` / `inbox.dat` | Gelen kutusu mesajları, medya haberleri, basın toplantısı kayıtları ve sosyal medya akışı. |
| `dynamic_reputation.dat` / `youth_intake_manager.dat` | Lig ve kulüp itibarlarının sezonluk dinamik değişim kuyruğu ile Mart/Nisan ayında kulüplere dağıtılacak `Youth Intake` (`Newgen`) aday ön-üretim listeleri. |


---

## Bölüm 8 — Ana Veritabanı (`editor.fmf`) Yardımcı Tabloları (`team`, `award`, `currency`, `team kit`, `region`, `stage name`, `description`)

Aşağıdaki tablo, `editor.fmf` içindeki 33 şemadan kalan yardımcı tabloların tüm kolonlarını ve oyun motorundaki görevlerini tamamlar:

| Şema / Tablo Adı (`editor.fmf`) | FourCC Alanları | Oyun Motorunda Dokunduğu Alanlar ve Tam Etkisi |
| :--- | :--- | :--- |
| **`team.xml` & `club b/c/d team.xml`**<br>*(Alt / Yedek / Genç Takım Konteyneri — 25 Kolon)* | `Ttyp` (`Team Type`: `Reserve`, `B Team`, `C Team`, `U23`, `U21`, `U19`, `U18`, `II Team`), `Tdiv` (Lig), `Tsta` (Stadyum), `Trep` (İtibar), `Tman` (Hoca) | Kulübün A takımı dışındaki B/C takımlarını (örn. İspanya'da `Real Madrid Castilla` / `Barça Atlètic`, Almanya'da `II` takımları) ve yaş altı (`U21`/`U19`) takımlarını tanımlar. **Kritik Fark:** `B Team` ayrı bir profesyonel alt ligde (`Tdiv`) mücadele ederken, `Reserve` / `U21` takımı genç/yedek liginde oynar; her ikisi de genç oyuncuların `18+` yaş sonrasında (antrenmandan ziyade **maç dakikası** belirleyici olduğu için) `CA` geliştirmesini sağlar. |
| **`award.xml`**<br>*(Ödüller — 126 Kolon)* | `Awty` (Tür: `Player of the Year`, `Top Goalscorer`, `Young Player`, `Goalkeeper`, `Manager of the Year`, `Team of the Year`, `Goal of the Month`), `Awre` (İtibar `1..200`), `Awvo` (Oylama Kriteri: `Match Ratings`, `Goals`, `Media`, `Managers`, `Players`), `Awel` (Uygunluk: `Age`, `Nationality`, `Division`) | **1) Oyuncu ve Hoca İtibarı:** Ödülü kazanan (veya ilk 3'e giren) kişinin `world_reputation` ve `current_reputation` değerine ödülün `Awre` itibarı oranında kalıcı sıçrama yaptırır.<br>**2) Sözleşme Maddeleri (`Contract.clauses`):** `Team of the Year Bonus`, `Top Goalscorer Bonus` ve `International / Award Bonus` ödemelerini tetikler.<br>**3) Kulüp İkonu & `Hall of Fame`:** Oyuncunun biyografisine (`Achievements`) işlenir ve piyasa değerini (`[REF-EKO]`) yükseltir. |
| **`currency.xml`**<br>*(Para Birimleri — 12 Kolon)* | `Cuna` (Ad), `Cusy` (Sembol), `Cuex` (`Exchange Rate` — `GBP £` bazlı döviz kuru), `Curu` (Yuvarlama kuralı) | Oyun içindeki tüm finansal tablolar (`FinanceMonth`, `Contract.wage_per_week`, `asking_price`, `Sponsorship`) arka planda **İngiliz Sterlini (`GBP £`)** cinsinden 64-bit/32-bit tam sayı olarak saklanır ve arayüzde/ülke kurallarında `Cuex` döviz kuruyla çarpılarak yerel para birimine (`€`, `\$`, `₺`, `¥` vb.) dönüştürülür. |
| **`team kit.xml`**<br>*(Formalar ve Renkler — 29 Kolon)* | `Ktyp` (`Home`, `Away`, `Third`, `GK`), `Kfgc` (Ön Plan Rengi `RGB`), `Kbgc` (Arka Plan Rengi `RGB`), `Kolc` (Çizgi/Yaka Rengi), `Ksty` (Desen `1..65`: Çubuklu, Parçalı, Düz, Çapraz vb.), `Knum` (Numara Rengi), `Kyr` (Yıl) | **1) 3B Maç Motoru Forma Çakışma Çözücüsü (`Kit Clash Resolver`):** Maç başlamadan önce ev sahibi takımın `Home` forması ile deplasman takımının `Home`/`Away`/`Third` formalarının `RGB` (`ΔE` renk mesafesi) kontrastını karşılaştırır; çakışma varsa deplasman takımına otomatik olarak `Away` veya `Third` (hatta şort/çorap kombinasyonu) giydirir.<br>**2) Arayüz Tema Renkleri:** Kulüp ekranının üst bar arka plan (`Kbgc`) ve yazı (`Kfgc`) renklerini belirler. |
| **`region.xml` & `local region.xml`**<br>*(Coğrafi Bölgeler — 14 Kolon)* | `Rgna` (Bölge Adı: `Eastern Europe`, `South America`, `Scandinavia`, `UK & Ireland` vb.), `Lrna` (Yerel Bölge), `Lrla` (Dil), `Lrcl` (İklim) | **1) Gözlemcilik Paketleri ve Görevlendirmeler (`Scouting Range / Assignments`):** Gözlemcileri tek bir ülke yerine tüm bir bölgeye (`Scout South America` / `Scout Central Europe`) göndermeyi sağlar.<br>**2) Altyapı (`Newgen`) Etnik ve Dil Dağılımı:** Aynı ülke içindeki farklı yerel bölgelerden (`local region.xml` — örn. İspanya'da Bask Bölgesi *Athletic Bilbao kuralı!*, Katalonya, Endülüs) çıkan oyuncuların yerel dilini (`Lrla`) ve bölgesel uygunluğunu belirler! |
| **`stage name.xml` & `description.xml`** | `Snna` (`Quarter Final`, `Playoff`, `Apertura`, `Clausura`), `Dsna` (`Wonderkid`, `Veteran`, `Tireless Midfielder`) | Fikstür/turnuva aşama adlarını ve oyuncunun profilinde görünen **`Media Description` (Medya Tanımı — örn. `PA >= 150` + `CA >= 115` + `Age <= 20` $\implies$ `"Wonderkid"` / Harika Çocuk)** etiket kurallarını barındırır. |


---

## Bölüm 9 — Kaynak Kod (`GameAssembly.dll` x86-64 Makine Kodu + `global-metadata.dat` IL2CPP v31 + `il2cpp.usym` + `tables.fmf` / `simatch.fmf`) Reverse Engineering Bulguları ve Kalıcı Decompiler Mimarisi (`binary_decompiler.py`)

Bu bölümdeki tüm veriler yalnızca dış dökümanlardan değil; doğrudan oyunun derlenmiş ikili (binary) motor dosyalarının **x86-64 makine kodu seviyesinde tersine mühendislik (reverse engineering / disassembly)** ile çözülmesiyle elde edilmiş ve her yeni oyun güncellemesinde tekrar tekrar manuel uğraşmaya gerek kalmaması için [`fm26save/binary_decompiler.py`](../fm26save/binary_decompiler.py) modülüne kalıcı olarak kodlanmıştır.

---

### 9.1. FM26 / FM27 İkili (Binary) Kaynak Kod Mimarisi Nasıl Çözüldü?

Oyun motoru dört ana derlenmiş ikili katmandan oluşur:

1. **`fm_Data/il2cpp_data/Metadata/global-metadata.dat` (`15.59 MB` FM26 / `15.68 MB` FM27 — Unity IL2CPP v31, `sanity = 0xFAB11BAF`):**
   - `64 × uint32` (`256` bayt) başlık tablosundan tüm C# derlemeleri (`127` adet `.dll` imajı), **`17,691` sınıf/struct/interface (`Il2CppTypeDefinition`, 88 bayt)**, **`752` FM/SI Enum tablosu**, **`78,075` saha (`Il2CppFieldDefinition`, 12 bayt)**, **`128,072` metot (`Il2CppMethodDefinition`, 36 bayt)**, **`26,210` özellik (`Il2CppPropertyDefinition`, 20 bayt)**, **`123,960` metot parametresi (`12` bayt)** ve **`29,841` string sabiti (`Il2CppStringLiteral`, 8 bayt)** doğrudan çıkarılmıştır.
2. **`GameAssembly.dll` (`53.64 MB` FM26 / `59.36 MB` FM27 — x86-64 PE64 Derlenmiş Makine Kodu):**
   - `g_CodeGenModules` (`const Il2CppCodeGenModule*[]`) dizisi $O(1)$ sürede (`~120 ms`) bulunarak `127` DLL'in tamamındaki `128,072` metodun tam sanal bellek adresleri (`VA`) ve zincirlenmiş `.pdata` (`RUNTIME_FUNCTION` + `UNWIND_INFO` `UNW_FLAG_CHAININFO = 0x4`) fonksiyon sınırları çözülmüştür.
   - `.data` bölümündeki başlatılmamış IL2CPP metadata kullanım jetonlarının (`(val >> 29) == 5 && (val & 1) == 1` $\implies$ `string_literals[(val & 0x1FFFFFFF) >> 1]`) şifresi kırılmıştır.
   - `SI.Bindable.Reference.Core.PropertyRegistration.Initialise` (`VA = 0x1803e4f30`, tek başına `921 KB` makine kodu!) ve `ContextRegistration.Initialise` (`VA = 0x180636fd0`) fonksiyonları tüm derlemelerde (`FM.UI.dll`, `SI.Bindable.dll`, `FM.GameConfig.dll`, `FM.Input.dll`, `FM.GamePlugin.dll`) disassemble edilerek C++ motorunun kullandığı **`8,138+` adet 4-baytlık FourCC Özellik Kodu (`PropertyKey`) $\rightarrow$ Tam C# Özellik Adı** ve **`220` adet FourCC Bağlam Kodu (`ContextKey`) $\rightarrow$ Tam C# Bağlam Adı** eşleşmesi %100 eksiksiz çıkarılmıştır.
3. **`il2cpp.usym` (`38.52 MB` — Unity Symbol Table v2, `magic = b"sym-"`):**
   - `24` baytlık başlık + **`1,593,548 × 24` baytlık sembol kaydı** + `38,245,176` ofsetindeki string tablosu çözülerek, Sports Interactive'in orijinal **TeamCity C# kaynak kodu dizin ağacı (`2,619` adet `.cs` dosyası: `C:/TeamCity/work/390f9e5df66ba53d/...`)** ve her makine kodu adresinin (`RVA`) hangi `.cs` dosyasının hangi satır numarasına (`line`) karşılık geldiği çıkarılmıştır.
4. **`game_plugin.dll` (`514.89 MB` FM26 / `433.98 MB` FM27) $\leftrightarrow$ `GameAssembly.dll` Köprüsü:**
   - `game_plugin.dll` C++ simülasyon çekirdeğini barındırır; `GameAssembly.dll` içindeki **`860` adet `*Reference` sınıfı (`FM.UI.*Reference`)** ve **`SI.Match` native struct'ları**, C++ çekirdeğindeki her bir veritabanı tablosunun hangi özellikleri (`GetPropertiesInternal`), hangi alt bağlamları (`GetContextsInternal`) ve hangi üst sınıfları (`DerivesFromInternal`) dışa açtığını birebir makine kodunda tutar.

---

### 9.2. C++ Motoru `0x444200XX` (`"DB\x00\xXX"`) Ana Veritabanı Tabloları ve `FM.UI.*Reference` Bağımlılık Grafiği

`GameAssembly.dll` içindeki tüm `*Reference` sınıflarının `get_ID` (`b8 <4B FourCC> c3`), `DerivesFromInternal` (`81 f9 <4B BaseFourCC>`), `GetPropertiesInternal` (`33 d2 b9 <4B PropFourCC> e8`), `GetContextsInternal` (`81 ff <4B PropFourCC>` + `ba <4B CtxFourCC>`) ve `GetPropertyTypeInternal` fonksiyonlarının x86-64 disassembly analizi sonucunda, C++ veritabanındaki **19 ana tablonun (`0x44420000` .. `0x44420039`)** ve kritik alt nesnelerin tam şeması:

| C++ Tablo ID (`get_ID`) | C# Bağlama Sınıfı (`FM.UI`) | Kalıtım (`DerivesFromInternal`) | Özellik Sayısı (`Props`) | Bağlam Sayısı (`Ctxs`) | C++ Motorundan Dışa Açılan Temel Alanlar ve Görevleri |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **`0x44420000`** (`DB #0`) | `AwardReference` | `AwardReference` | **13** | **1** (`Competition`) | `Name`, `Competition`, `Continent`, `Nation`, `AwardPeriodString`, `AwardUiType`, `AwardVote`, `PastWinnerDefault`, `PastWinners`, `SquadOfPlayers`, `TableStatType`, `HighlightFlags`. |
| **`0x44420001`** (`DB #1`) | **`PersonReference`** | `INonPlayerReference`, `IJournalistReference`, `IPlayerReference`, `IPersonBaseReference`, `IAgentReference`, `IOfficialReference` | **1,245** | **70** | Oyuncu, Teknik Direktör, Personel, Menajer (`Agent`), Hakem (`Official`) ve Gazeteciyi (`Journalist`) tek çatı altında toplayan devasa ana varlık! `548` özelliği parametrelidir (`team`, `club`, `PositionMask`, `RoleMask`, `InPossession`, `NegotiationStage`, `ComparisonPerson` vb. bağlamlarla sorgulanır). |
| **`0x44420002`** (`DB #2`) | `CityReference` | `CityReference` | **1** | **0** | `Name` (Şehir rakımı ve koordinatları maç motoruna `MatchStadiumLocationSetup` üzerinden doğrudan C++ tarafından aktarılır). |
| **`0x44420003`** (`DB #3`) | **`ClubReference`** | `ClubReference`, `ITeamContainerReference` | **492** | **31** | Kulübün tüm mali (`FfpData`, `ContinentalFfpData`, `NetDebt`, `ProjectionBalance`, `ProjectionTransferBudget`, `SponsorshipsData`, `DebtsAndLoansData`), yönetim (`ClubVisionNegotiationType`, `VisionObjectiveSetter`), tesis ve kadro verilerini barındırır (`111` parametreli özellik). |
| **`0x44420005`** (`DB #5`) | `ContinentReference` | `ContinentReference` | **50** | **7** | `ClubCoefficients`, `AfricanCaribbeanPacificGroup` (Cotonou anlaşması!), `DomesticDivisionsReferenceList`, `NumberOfTeams`, `CanViewManagers`. |
| **`0x44420007`** (`DB #7`) | `MediaSourceReference` | `MediaSourceReference` | **1** | **0** | `Name` (Medya kuruluşu / gazete / TV kanalı). |
| **`0x44420008`** (`DB #8`) | `LanguageReference` | `LanguageReference` | **1** | **0** | `Name` (`PersonReference` içinde `FirstLanguage` [`0x635a3367`], `SecondLanguage`, `ThirdLanguage`, `FourthLanguage`, `FifthLanguage`, `SixthLanguage` bağlamlarıyla kişiye bağlanır!). |
| **`0x44420009`** (`DB #9`) | `NationalTeamContainerReference` | `NationalTeamContainerReference`, `ITeamContainerReference` | **117** | **6** | `Nation`, `Legends`, `MajorClubs`, `TopPlayers`, `MostReputableLeague`, `AssociationFormedYear`, `DebugCallupExpectationInfo`, `DebugPlayersConsideredForSlot`. |
| **`0x4442000a`** (`DB #10`) | `NationReference` | `NationReference` | **52** | **9** | `Continent`, `DisplayRegion`, `DivisionList`, `AwardList`, `BestPlayerAward`, `NumberOfTeams`, `IsClickable`. |
| **`0x44420012`** (`DB #18`) | `DerbyReference` | `DerbyReference` | **0** | **0** | Ezeli rekabet / derbi kimlik referansı. |
| **`0x44420013`** (`DB #19`) | `RegionReference` | `RegionReference` | **1** | **0** | Coğrafi gözlemcilik bölgesi (`Name`). |
| **`0x44420015`** (`DB #21`) | **`StadiumReference`** | `StadiumReference` | **22** | **1** (`Competition`) | `City` ($\rightarrow$ `CityReference` `0x44420002`), `Nation` ($\rightarrow$ `NationReference` `0x4442000a`), `OwnedBy` ($\rightarrow$ `ClubOrNationReference` `0x72637678`), `Name`, `NameForComp` (`Competition` bağlamıyla UEFA/Sponsorluk stadyum adını döndürür!), `Condition`, `Capacity`, `TotalCapacity`, `FacilityRating`, `PitchCondition`, `PitchDimensions`, `PitchLength`, `PitchWidth`, `MaxPitchDimensions`, `Rent`, `Roof`, `Surface`, `UnderSoilHeating`, `YearBuilt`, `YearRebuilt`, `Environment`. |
| **`0x44420017`** (`DB #23`) | `StageNameReference` | `StageNameReference` | **0** | **0** | Turnuva aşama adı referansı. |
| **`0x44420018`** (`DB #24`) | **`TeamReference`** | `TeamReference` | **461** | **34** | A Takım, B Takımı, Rezerv ve U21/U19 takımlarının taktik, analiz (`PlayerAnalytics`, `LastMatchAnalysis`, `GeneralPerformanceVisual`), medya beklentisi (`MediaExpectedPosition`) ve kadro verilerini barındırır. |
| **`0x44420019`** (`DB #25`) | **`CompReference`** | `CompReference` | **296** | **24** | Lig/Kupa kuralları, aşamalar (`AllStages`), ödül oylamaları (`CanViewAwardVoting`), katsayılar (`CanViewCoefficients`), MLS Draft (`CanViewDraft`, `CanViewAllocationRanking`) ve istatistikleri barındırır. |
| **`0x4442001c`** (`DB #28`) | `RemovedRecordReference` | `RemovedRecordReference` | **1** | **0** | Silinmiş kayıt bayrağı (`HighlightFlags`). |
| **`0x4442002f`** (`DB #47`) | `LocalRegionReference` | `LocalRegionReference` | **1** | **0** | Yerel bölge (`Name`). |
| **`0x44420038`** (`DB #56`) | `AgreementReference` | `AgreementReference` | **3** | **0** | Uluslararası anlaşmalar (`Name`, `Nations`, `NationsCount` — örn. AB Serbest Dolaşım, Cotonou, Mercosur). |
| **`0x44420039`** (`DB #57`) | `FixtureNameReference` | `FixtureNameReference` | **1** | **1** | Özel maç/fikstür adı (`Name`). |
| **`0x636f6e74`** (`"cont"`) | **`ContractReference`** | `ContractReference` | **124** | **1** (`Number`) | Sözleşmedeki tüm maaş, oynama süresi yolu (`AgreedPlayingTime`, `AgreedPlayingTimeNextSeason`, `AgreedPlayingTimeTwoSeasonsTime`, `AgreedPlayingTimeThreeSeasonsTime`, `AgreedPlayingTimeFourSeasonsTime`, `ActualPlayingTime`), serbest kalma maddeleri (`ActivatedRelegationMinimumFeeReleaseClauseValue`, `ActivatedNonPromotionMinimumFeeReleaseClauseValue`, `AnyContinentalCompetitionMinimumFeeReleaseClauseValue`, `DomesticMinimumFeeReleaseClauseExpiryDate`) ve otomatik uzatma maddelerini (`Automatic1YearExtensionNumberLeagueGames`, `Automatic1YearExtensionNumberLeagueGamesAvoidRelegation`, `Automatic1YearExtentionNumberLeagueGamesPromotion`) barındırır. |
| **`0x77725342`** (`"BSrw"`) | **`TacticReference`** | `TacticReference` | **207** | **27** | Topa sahipken (`InPossession`) ve top rakipteyken (`OutOfPossession`) taktik motorunun tüm talimatlarını (`AttackingTransition`, `BuildUpStrategy`, `CreativeFreedom`, `CrossEngagement`, `CrossingStyle`, `PlayerContextRoleAbility`, `PlayerContextTacticAbility`, `SetPieceCreator` vb.) barındırır. |
| **`0x706c3465`** (`"e4lp"`) | **`PlayerTrainingReference`** | `PlayerTrainingReference` | **37** | **3** (`Judge`, `RoleMask`, `team`) | Bireysel antrenman gelişim hızlarını (`ImprovementAttackingTactical`, `ImprovementAttackingTechnical`, `ImprovementDefendingTactical`, `ImprovementDefendingTechnical`, `ImprovementFitness`, `ImprovementGoalkeeping`, `ImprovementPossessionTactical`, `ImprovementPossessionTechnical`, `ImprovementSetPieces`, `ImprovementOverall`), `OOPTraining`, `CanTrainWeakerFoot`, `TrainingRating` ve `Load` verilerini tutar. |
| **`0x6d617464`** (`"dtam"`) | **`MatchPlayerReference`** | `MatchPlayerReference`, `ITacticsTeamSelectionReference` | **39** | **2** (`Tactic`, `PlayerStatusSortType`) | Canlı maç içindeki oyuncunun anlık `Condition`, `Morale`, `BodyLanguage`, `Sharpness`, `MatchRating`, `MatchInjuryType`, `PositionAvailableRoles` ve `Stats` verilerini tutar. |

---

### 9.3. 3B Maç Motoru (`SI.Match.dll` & `SI.MatchTypes.dll`) Native C++ $\leftrightarrow$ C# Struct Yapıları

`global-metadata.dat` içindeki `SI.Match.dll` (`Image[9]`) ve `SI.MatchTypes.dll` (`Image[82]`) derlemelerinden decompile edilen, C++ simülasyon motorunun 3B maç motoruna maç başında gönderdiği gerçek veri yapıları (`ValueType` structs):

1. **`SI.Match.MatchStadiumLocationSetup` (`Type[13514]`):**
   - `m_longitude` (`float`): Stadyumun bulunduğu şehrin boylamı (`City.longitude` $\rightarrow$ güneşin doğuş/batış açısı).
   - `m_latitude` (`float`): Stadyumun bulunduğu şehrin enlemi (`City.latitude` $\rightarrow$ mevsimsel gün ışığı süresi ve gölge boyu).
   - `m_orientation` (`float`): Stadyumun pusula yönelimi (`m_altitude` ile birlikte güneşin hangi kalecinin gözünü alacağını ve rüzgarın hangi kaleye doğru eseceğini belirler).
   - **`m_altitude` (`float`):** Stadyumun/şehrin **deniz seviyesinden yüksekliği (Rakım - metre)**. Maç motoru bu değeri doğrudan hava yoğunluğu ($\rho_{\text{air}}$) ve oyuncu oksijen tüketimi (`Condition` düşüş çarpanı) hesaplamalarında kullanır!
   - `m_timeZone` (`int`): Saat dilimi.
2. **`SI.Match.PitchSetupInfo` (`Type[13507]`):**
   - `pitchLength` (`float`), `pitchWidth` (`float`): Saha uzunluğu ve genişliği (metre).
   - `wetnessStrength` (`float`): Zemindeki su/ıslaklık şiddeti (`0.0 .. 1.0` — topun sekme hızını ve kayarak müdahale mesafesini doğrudan değiştirir).
   - `pitchConditionRating` (`float`): Çim bozukluğu/kalitesi (`Stadium.Condition` $\rightarrow$ `First Touch` ve `Passing` hata payını artırır).
   - `precipitationType` (`PrecipitationType` enum: `None`, `Rain`, `Snow`, `Hail`), `pitchType` (`PitchType` enum: `Grass`, `Synthetic`, `Hybrid`, `Gravel`, `Clay`, `Sand`), `pitchPattern` (`int`), `hasUnderSoilHeating` (`bool`: alttan ısıtma varsa kar birikmesini ve donmayı engeller).
3. **`SI.Match.MatchLightingAndWeatherSetup` (`Type[13515]`):**
   - `m_weatherCondition`, `m_windSpeed`, `m_windDirection`, `m_temperature`, `m_lightingCondition`, `m_kickOffTimeOfDay`.

---

### 9.4. `tables.fmf` İçinden Decompile Edilen Boy (`Height`) $\rightarrow$ Zıplama (`jumping_reach.jsb`) ve Hava Hakimiyeti (`aerial_reach.jsb`) Tabloları

Oyuncunun `Person.height` (Boy - cm) kolonunun, `jumping_reach` (Zıplama) ve kaleci `aerial_reach` (Hava Hakimiyeti) özelliklerini nasıl doğrudan sınırladığı `shared/data/shared/tables.fmf` içindeki `tables/jumping_reach.jsb` (`3,253 B`) ve `tables/aerial_reach.jsb` (`3,721 B`) ikili dosyalarından birebir çözülmüştür:

#### A) Erkek Oyuncular İçin Boy (`cm`) $\rightarrow$ `jumping_reach` (`1–20`) Dönüşüm Tablosu (`tables/jumping_reach.jsb` $\rightarrow$ `male_data`)

| Maksimum Boy (`max_height` cm) | `poor` (Kötü Zıplayan) | `below_average` (Ort. Altı) | `average` (Ortalama) | `above_average` (Ort. Üstü) | `good` (Çok İyi Zıplayan) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **`<= 161 cm`** | `1` | `1` | `2` | `3` | `4` |
| **`162 – 163 cm`** | `1` | `2` | `3` | `4` | `5` |
| **`164 – 166 cm`** | `2` | `3` | `4` | `5` | `6` |
| **`167 – 168 cm`** | `3` | `4` | `5` | `6` | `7` |
| **`169 – 171 cm`** | `4` | `5` | `6` | `7` | `8` |
| **`172 – 173 cm`** | `5` | `6` | `7` | `8` | `9` |
| **`174 – 176 cm`** | `6` | `7` | `8` | `9` | `10` |
| **`177 – 179 cm`** | `7` | `8` | `9` | `10` | `11` |
| **`180 – 181 cm`** | `8` | `9` | `10` | `11` | `12` |
| **`182 – 184 cm`** | `9` | `10` | `11` | `12` | `13` |
| **`185 – 186 cm`** | `10` | `11` | `12` | `13` | `14` |
| **`187 – 189 cm`** | `12` | `13` | `14` | `15` | `16` |
| **`190 – 191 cm`** | `13` | `14` | `15` | `16` | `17` |
| **`192 – 194 cm`** | `14` | `15` | `16` | `17` | `18` |
| **`195 – 196 cm`** | `15` | `16` | `17` | `18` | `19` |
| **`197 – 199 cm`** | `16` | `17` | `18` | `19` | `20` |
| **`>= 200 cm`** | **`17`** | **`18`** | **`19`** | **`20`** | **`20`** |

> **Tablonun Kanıtladığı Kural:** `200 cm` boyundaki bir erkek oyuncunun zıplama yeteneği `poor` (en kötü) bile olsa `jumping_reach` değeri **en az `17`**, ortalama ise **`19`**, iyi ise **`20`** olur! Tersine, `171 cm` boyundaki bir oyuncunun zıplama yeteneği `good` (en iyi) bile olsa taban `jumping_reach` tavanı **`8`**'dir! (Kadın futbolcular için `female_data` tablosunda ise aynı eşikler yaklaşık `6–9 cm` daha erken başlar: örn. kadınlarda `>= 188 cm` $\implies$ `good = 20`, `>= 195 cm` $\implies$ `poor = 19, average = 20`).

#### B) Erkek Kaleciler İçin Boy (`cm`) $\rightarrow$ `aerial_reach` (`1–20`) Dönüşüm Tablosu (`tables/aerial_reach.jsb` $\rightarrow$ `male_data`)

- `<= 158 cm`: `poor=1, avg=1, good=1` | `171 cm`: `poor=2, avg=4, good=6` | `179 cm`: `poor=5, avg=7, good=9`
- `184 cm`: `poor=7, avg=9, good=11` | `188 cm`: `poor=9, avg=11, good=13` | `192 cm`: `poor=11, avg=13, good=15`
- `197 cm`: `poor=13, avg=15, good=17` | `200 cm`: `poor=14, avg=16, good=18` | `205 cm`: `poor=16, avg=18, good=20`
- `>= 209 cm`: `poor=18..19, below_average=19..20, average=20, above_average=20, good=20`.

---

### 9.5. `simatch.fmf` İçinden Decompile Edilen Maç Reytingi (`player_ratings_data.jsb`), QME İstatistik-Özellik (`qme_stat_relevant_attribute_data.jsb`) ve OOP Rol Puanlama (`oop_attributes_scoring.jsb`) Katsayıları

#### A) Maç Reytingi (`0.0 – 10.0`) Hesaplama Denklemi (`simatch/player_ratings_data.jsb` — `348,584 B`)

Maç motoru her oyuncunun `6.60` (`6600 / 1000`) taban puanına, oynadığı rolün (`32` farklı rol profili) katsayılarını (`1/1000` reyting puanı biriminde) ekler/çıkarır ve takımın maç beklentisine (`expected_score_data`) göre pozitif puanları çarpar:

- **Takım Beklenti Çarpanları (`expected_score_data`):**
  - Favori değilken farklı galibiyet / beraberlik (`Exceed Significant with Win / Draw`): Pozitif aksiyon puanları **`× 1.20`** (`1200 / 1000`) ile çarpılır!
  - Beklentiyi aşan galibiyet / beraberlik (`Exceed with Win / Draw`): Pozitif aksiyon puanları **`× 1.10`** (`1100 / 1000`) ile çarpılır!
- **Aksiyon Başına Kesin Reyting Katsayıları (`coefficients`, `100 = +0.10` Reyting Puanı):**
  - `90min Adjuster`: **`-600`** ($-0.60$ puan — 90 dakika sahada kalıp hiçbir olumlu istatistik üretmeyen oyuncunun puanı `6.60`'tan `6.00`'a iner!).
  - **Hücum & Gol:** `Goals`: **`+600`** ($+0.60$), `Good Goal Adder`: **`+100`** ($+0.10$), `Great Goal Adder`: **`+200`** ($+0.20$), `Decisive Goal` (Galibiyet/Beraberlik golü): **`+350`** ($+0.35$), `Decisive Late Goal` (Son dakika kritik golü): **`+400`** ($+0.40$), `Cumulative Goal Bonus` (2. ve 3. gol bonusu): **`+300`** ($+0.30$), `Goals minus xG times 100 (only if negative)`: **`4`** (Kaçırılan her `1.00 xG` için **`-400`** yani **$-0.40$ reyting cezası**!), `Penalties Scored`: **`+350`** ($+0.35$), `Penalties Missed`: **`-200`** ($-0.20$), `Shots`: **`+30`** ($+0.03$), `Shots On Target`: **`+20`** ($+0.02$).
  - **Oyun Kurma & Hücum Organizasyonu:** `Assists`: **`+300`** ($+0.30$), `Cumulative Assist Bonus`: **`+200`** ($+0.20$), `Key Passes`: **`+30`** ($+0.03$), `Passes Completed`: **`+7`** ($+0.007$), `Crosses Completed`: **`+40`** ($+0.04$), `Crosses Incompleted`: **`-8`** ($-0.008$), `Open Play xA`: **`+7`**, `Dribbles`: **`+20`** ($+0.02$), `Times Was Fouled`: **`+30`** ($+0.03$).
  - **Savunma & İkili Mücadele:** `Tackles Won`: **`+40`** ($+0.04$), `Tackles Lost`: **`-20`** ($-0.02$), `Interceptions`: **`+50`** ($+0.05$), `Blocks`: **`+50`** ($+0.05$), `Aerial Duels Won`: **`+20`** ($+0.02$), `Aerial Duels Lost`: **`-20`** ($-0.02$), `Fouls Committed`: **`-40`** ($-0.04$), **`Mistakes Leading to Goals`: `-300` ($-0.30$)**, **`Own Goal`: `-300` ($-0.30$)**.
  - **Kalecilik & Takım Skoru:** `Clean Sheet`: **`+500`** ($+0.50$), `Saves`: **`+100`** ($+0.10$), `Good Saves Adder`: **`+200`** ($+0.20$), `Great Saves Adder`: **`+400`** ($+0.40$), `Penalties Saved Adder`: **`+450`** ($+0.45$), `Keeper less than 5 shot boost`: **`+125`** ($+0.125$), `Team Goals For`: **`+50`** ($+0.05$), `Team Goals Conceded`: **`-100`** ($-0.10$).
  - **Kartlar & Seri Penaltılar:** `Yellow Card`: **`-50`** ($-0.05$), `Second Yellow Card`: **`-100`** ($-0.10$), `Red Card`: **`-300`** ($-0.30$); `Shootout Scored`: **`+200`**, `Shootout Missed`: **`-200`**, `Shootout Saved`: **`+300`**, `Shootout Saved Pen to Win`: **`+300`**.

#### B) Hızlı Maç Motoru (`QME`) İstatistik $\rightarrow$ Oyuncu Özelliği Doğrudan Eşleşmesi (`simatch/qme_stat_relevant_attribute_data.jsb`)

Arka planda simüle edilen maçlarda (`Quick Match Engine` / `Full Detail` olmayan lig maçları) her bir maç istatistiğinin hangi oyuncu özelliklerinden üretildiği:

| Maç İstatistiği (`stat_type`) | Doğrudan Besleyen Oyuncu Özellikleri (`relevant_attributes`) |
| :--- | :--- |
| `passes_attempted` (Denene Pas) | `passing` + `work_rate` |
| `pass_completion` (Pas İsabeti) | `passing` + `decisions` |
| `key_passes` & `progressive_passes` (Kilit / İlerletici Pas) | `passing` + `vision` |
| `crosses_attempted` (Denenen Orta) | `crossing` + `work_rate` |
| `cross_completion` (İsabetli Orta) | `crossing` + `vision` + `technique` |
| `tackles_attempted` & `key_tackles` (Top Çalma Girişimi / Kritik) | `tackling` + `positioning` + `work_rate` |
| `tackle_completion` (Başarılı Top Çalma) | `tackling` + `positioning` |
| `interceptions` (Pas Arası) | `anticipation` + `positioning` |
| `blocks` (Şut/Orta Bloklama) | `anticipation` + `positioning` + `bravery` |
| `clearances` (Uzaklaştırma) | `positioning` |
| `headers_attempted` & `key_headers` (Hava Topu Girişimi) | `positioning` + `jumping` (`jumping_reach`) |
| `header_completion` (Kazanılan Hava Topu) | `heading` + `strength` + `jumping` (`jumping_reach`) |
| `fouls_made` (Yapılan Faul) | `dirtiness` (Gizli) + `aggression` |
| `dribbles` (Başarılı Çalım) | `dribbling` + `flair` + `pace` + `acceleration` |
| `offsides` (Ofsayta Düşme — Ters Orantılı) | `movement` (`off_the_ball`) + `work_rate` + `acceleration` + `concentration` |
| `distance_run` (Koşu Mesafesi km) | `work_rate` + `stamina` + `pace` |
| `sprints` (Yüksek Yoğunluklu Sprint Sayısı) | `work_rate` + `stamina` |
| `pressures_attempted` (Baskı / Pres Girişimi) | `work_rate` + `anticipation` |
| `pressures_completion` (Başarılı Pres) | `work_rate` + `anticipation` + `acceleration` |

---

### 9.6. Kalıcı Reverse-Engineering & Decompiler Modülü (`fm26save/binary_decompiler.py`) Kullanımı

Herhangi bir FM26 veya FM27 kurulumunda (veya gelecekteki oyun güncellemelerinde) tüm ikili dosyaları (`GameAssembly.dll`, `global-metadata.dat`, `il2cpp.usym`, `tables.fmf`, `simatch.fmf`) tek komutla çözmek ve JSON + C# kaynak kod şemalarını üretmek için [`fm26save/binary_decompiler.py`](../fm26save/binary_decompiler.py) modülü kurulmuştur:

#### 1) Komut Satırı (CLI) ile Tek Seferde Tüm Kodları Çözme (`decompile-binaries`)

```bash
# Tüm binary'leri (GameAssembly.dll + global-metadata.dat + il2cpp.usym + .fmf tabloları) çözüp docs/decompiled_engine klasörüne JSON ve C# (.cs) olarak dök:
python -m fm26save.cli decompile-binaries --mode dump --out-dir docs/decompiled_engine

# Belirli bir C++ -> C# Reference varlığının (örn. PersonReference, ClubReference, StadiumReference, ContractReference) tüm özelliklerini ve bağlamlarını çöz:
python -m fm26save.cli decompile-binaries --mode bindings --entity PersonReference

# tables.fmf ve simatch.fmf içindeki boy->zıplama, QME ve maç reytingi tablolarını çöz:
python -m fm26save.cli decompile-binaries --mode tables
```

#### 2) Python API ile Programatik Kullanım

```python
from fm26save import (
    decompile_gameassembly_bindings,
    decompile_global_metadata,
    decompile_usym_symbols,
    dump_decompiled_codebase,
    extract_engine_lookup_tables,
)

# Tek çağrıda tüm oyun binary'lerini decompile edip diske kaydet:
summary = dump_decompiled_codebase(output_dir="docs/decompiled_engine")

# Veya doğrudan bellek içinde C++ <-> C# FourCC özellik ve varlık grafiğini al:
bindings = decompile_gameassembly_bindings()
person_schema = bindings["reference_classes"]["PersonReference"]
print(person_schema["property_count"], person_schema["contexts"])
```

