# FM27 & FM26 Kalan Tüm Oyun Dosyalarının (Kategori 2) Tam Decompile ve İkili Şema Raporu (`%100` Kapsama)

Bu döküman, **Kategori 1 (Kısmen Decompile Edilmiş 5 Sistem)** tamamlandıktan sonra (`bkz.` [FM27_PARTIAL_FILES_FULL_DECOMPILATION_TR.md](FM27_PARTIAL_FILES_FULL_DECOMPILATION_TR.md)), oyun kurulum dizininde (`Football Manager 27` ve `Football Manager 26`) geriye kalan **tüm dokunulmamış ikili (binary), arşiv, animasyon, katalog, Unity çalışma zamanı ve veritabanı dosyalarının (`Kategori 2`)** bayt düzeyinde tersine mühendislik ve tam decompile sonuçlarını içerir.

Bu aşamayla birlikte kurulum dizinindeki **1.283 dosyanın tamamı (`8,31 GB` — `%100`)** ayrıştırılmış, ikili şemaları çıkarılmış ve [`fm26save/binary_decompiler.py`](../fm26save/binary_decompiler.py) içindeki `decompile_all_remaining_game_files()` fonksiyonuna kalıcı olarak entegre edilmiştir.

---

## 1. Yönetici Özeti: Kategori 2 Sistemleri (`FM27` vs `FM26`)

| # | Sistem / Dosya Grubu | Konum | İkili Format / Sihirli Sayı | FM27 Tam Decompile Sonucu | FM26 Tam Decompile Sonucu |
|---:|---|---|---|---|---|
| **1** | **Tüm Kurulum Dosya Envanteri** | `<FM_ROOT>/**/*` | Tüm uzantılar (`.bundle`, `.dll`, `.fmf`, `.dat`, `.cat`, `.amd`, `.bin`, `.dbc`, `.xml`, `.json`) | **1.283** dosya (`8.926.153.524` B / `8,31 GB`) — **0** bilinmeyen dosya | **1.037** dosya — **0** bilinmeyen dosya |
| **2** | **Tüm UnityFS `.bundle` Arşivleri** | `fm_Data/StreamingAssets/aa/StandaloneWindows64/*.bundle` + `fm_Data/Resources/*.bundle` | `UnityFS\x00` v8 (LZ4/LZ4HC `BlocksInfo` + CAB dizin tablosu) | **534** `.bundle` (`24` kategori), `4,26 GB` sıkıştırılmış → **`8,24 GB`** açılmış, **764** CAB düğümü | **293** `.bundle`, **436** CAB düğümü |
| **3** | **Unity Addressables İkili Katalogları & `manifest.dat`** | `aa/catalog.bin`, `AddrData/catalog_info.bin`, `aa/AddressablesLink/link.xml`, `fm_Data/manifest.dat` | `0x0DE38942` v2 `BinaryStorageBuffer` + `25B`/`37B` MD5 manifest kayıtları | `catalog.bin`: **29.020** anahtar (`1.302` bundle ref); `catalog_info.bin`: **37.582** anahtar (`539` bundle ref); `manifest.dat`: **1.239** × `25B` ikili MD5 kaydı | `catalog.bin`: **28.057** anahtar; `catalog_info.bin`: **36.697** anahtar; `manifest.dat`: **1.000** × `37B` ASCII MD5 kaydı |
| **4** | **`sianim` 3B Maç Animasyon Motoru** | `shared/data/sianim/{animations,schemas,skeletons}` | `CAT\x00` (`v38`/`v37`) + `STAB` dize tablosu + `.amd` (`v4` `11B` segment tablosu) | **4** `.cat` arşivinde **5.932** `CAT\x00` klip, **545.744** kemik bölümü, **557.440** animasyon izi, **5.819** `STAB` klip yolu; **4** `.amd` içinde **5.500** Motion Matching segmenti (**165.699** kare); **44** JSON aksiyon şeması; **19** iskelet rig dosyası | **4** `.cat` arşivinde **5.833** `CAT\x00` klip (`v37`); **4** `.amd` içinde **5.611** segment; **41** şema; **19** iskelet dosyası |
| **5** | **Unity `SerializedFile v22` Konteynerleri & Çalışma Zamanı** | `fm_Data/{globalgamemanagers*,resources.assets,sharedassets0.assets,level0,Resources/*}` | Unity `SerializedFile` v22 (`6000.3.18f1-custom`, `platform=19`) | **7** çekirdek konteynerde **181** serileştirilmiş tip, **8.498** Unity nesnesi, **118** script tipi, **14** dış dosya referansı + `.resS` (`5,77 MB`) | **7** çekirdek konteynerde **8.390+** Unity nesnesi |
| **6** | **Tüm Native PE64 İkilileri & `lang_db.dat` / Tarihsel DB'ler** | `fm.exe`, `UnityPlayer.dll`, `GameAssembly.dll`, `Plugins/x86_64/*.dll`, `shared/data/database/db/2300..2700` | `MZ`/`PE\x00\x00` (`0x8664`) + `\x03\x01tad.` Zstd çerçeveleri | **17** PE64 ikilisinde **14.106** export ve **532.123** `.pdata` fonksiyonu; `lang_db.dat` içinde **401** Zstd çerçevesi (`25` dil × `16` tablo = dil başına **229.555** yerelleştirilmiş satır); **8** tarihsel DB sürümü (`2300`..`2700`, `303` dosya) | **17** PE64 ikilisi; `lang_db.dat` içinde **401** Zstd çerçevesi; **8** tarihsel DB sürümü (`2300`..`2630`) |

---

## 2. Tüm `534` UnityFS `.bundle` Arşivi (`BlocksInfo` ve CAB Dizin Tablosu)

Kategori 1'de `ui-*` ve `sibindable_*` önekli **69** UI bundle dosyası decompile edilmişti. Kategori 2'de `fm_Data/StreamingAssets/aa/StandaloneWindows64/` altındaki **533** `.bundle` ve `fm_Data/Resources/` altındaki **1** `.bundle` olmak üzere **toplam 534 `.bundle` dosyasının tamamı** `BlocksInfo` + CAB iç düğüm (node) tablolarıyla ayrıştırılmıştır:

- **Toplam Sıkıştırılmış Boyut (LZ4/LZ4HC):** `4.264.347.140` bayt (`3,97 GB`)
- **Toplam Açılmış Boyut (Uncompressed):** `8.244.629.304` bayt (`7,68 GB`)
- **Toplam İç CAB Düğümü (`CAB-*` / `.resS` / `.resource`):** `764` adet

| Kategori Öneki | Bundle Sayısı | Sıkıştırılmış (Bayt) | Açılmış (Bayt) | CAB Düğümü | İçerik Açıklaması |
|---|---:|---:|---:|---:|---|
| `art` | 355 | 3.515.313.430 | 6.232.702.167 | 520 | 3B oyuncu/menajer karakter modelleri, saç/sakal, formalar, stadyum çevresi, kupalar, toplar, animasyon rig'leri |
| `ui` | 67 | 198.189.454 | 837.870.132 | 95 | UXML (`VisualTreeAsset`), USS (`StyleSheet`), `TableFactory`, `TableView`, ikonlar, fontlar, UI dokuları |
| `match` | 4 | 202.767.780 | 539.104.284 | 7 | 3B maç motoru saha, kamera, tribün, ışıklandırma ve maç günü varlıkları |
| `scenes` | 12 | 120.727.416 | 325.961.892 | 30 | Maç önü/sonu ara sahneleri (cutscene), soyunma odası, basın toplantısı ve ödül töreni sahneleri |
| `videos` | 3 | 99.600.802 | 103.396.155 | 6 | Turnuva açılış, kupa töreni ve arayüz arka plan video klipleri |
| `shaders` | 62 | 37.193.757 | 54.791.256 | 63 | URP / özel SI karakter, çim (pitch), forma (kit), kalabalık (crowd) ve UI shader paketleri |
| `stadiums` | 7 | 27.166.602 | 49.902.119 | 14 | Stadyum tribün şablonları, çatılar, köşe parçaları ve saha kenarı yapıları |
| `audio` | 1 | 45.581.448 | 48.620.876 | 2 | Maç atmosferi, tribün tezahüratları, düdük/top vuruş ses bankaları |
| `changingroom` | 1 | 8.016.711 | 35.703.888 | 2 | Soyunma odası 3B sahne ve iç mekan materyalleri |
| `promobanner` | 1 | 7.290.331 | 8.779.264 | 2 | Ana menü tanıtım görselleri |
| `vfx` | 1 | 1.827.834 | 5.025.416 | 2 | Yağmur, kar, konfeti, meşale ve saha parçacık efektleri |
| `f87a5c426c04c02c5c32c1ef21ae2ad6` | 2 | 283.980 | 1.186.428 | 3 | Paylaşılan Unity yerleşik (built-in) materyal/mesh bağımlılık paketi |
| `globalobjects` | 1 | 144.957 | 608.248 | 1 | Global çalışma zamanı prefab ve yönetici nesneleri |
| `gamemodules` | 7 | 101.247 | 455.243 | 7 | Alt modül yapılandırma varlıkları |
| `characterbuilder` | 1 | 50.075 | 207.644 | 1 | Menajer / oyuncu yüz ve vücut oluşturucu (Character Builder) verileri |
| `fantasydraft` | 1 | 26.049 | 104.548 | 1 | Fantasy Draft modu arayüz ve kural varlıkları |
| `settings` | 1 | 12.058 | 67.988 | 1 | Grafik ve kalite önayar (preset) tanımları |
| `shortcutdata` | 1 | 14.995 | 39.024 | 1 | Klavye kısayol haritaları |
| `initscene` | 1 | 11.556 | 37.260 | 1 | Başlangıç (bootstrap) sahnesi |
| `stadiumbuilder` | 1 | 13.231 | 27.636 | 1 | Prosedürel stadyum oluşturucu kuralları |
| `graphics` | 1 | 6.768 | 20.296 | 1 | Render pipeline (URP) profil varlıkları |
| `projectconfigurationassets` | 1 | 2.826 | 8.700 | 1 | Addressables / proje yapılandırma sabitleri |
| `sibindable` | 1 | 2.422 | 5.684 | 1 | `SI.Bindable` temel bağlama şeması |
| `performance` | 1 | 1.411 | 3.156 | 1 | Cihaz performans derecelendirme eşikleri |

---

## 3. Unity Addressables İkili Katalogları (`0x0DE38942` v2) ve `fm_Data/manifest.dat`

### 3.1 `aa/catalog.bin` ve `AddrData/catalog_info.bin` İkili Şeması
Her iki dosya da Unity `ContentCatalogData` **Binary Storage v2** (`BinaryStorageBuffer`) formatını kullanır. Dosya başındaki 32 baytlık (`8 × uint32`) başlık yapısı:

```text
Offset  Tip     Alan Adı                   aa/catalog.bin (3.269.712 B)   AddrData/catalog_info.bin (5.497.964 B)
------  ------  -------------------------  -----------------------------  ---------------------------------------
0x00    uint32  magic                      0x0DE38942                     0x0DE38942
0x04    uint32  version                    2                              2
0x08    uint32  keysOffset                 0x000024 (36)                  0x000024 (36)
0x0C    uint32  idOffset                   0x038B08 (232.200)             0x049698 (300.696)
0x10    uint32  instanceProviderOffset     0x038C4F (232.527)             0x0497DF (301.023)
0x14    uint32  sceneProviderOffset        0x038CBE (232.638)             0x04984E (301.134)
0x18    uint32  initObjectsArrayOffset     0x038E41 (233.025)             0x0499D1 (301.521)
0x1C    uint32  buildResultHashOffset      0x038E55 (233.045)             0x0499E5 (301.541)
```

- **`BinaryStorageBuffer` Kuralı:** Herhangi bir dizi veya dize ofseti `off` için, tam `4` bayt öncesindeki `uint32 [off - 4]` alanı o nesnenin bayt uzunluğunu (`byteSize`) tutar:
  - `keysOffset = 0x24` için `[0x20]` adresindeki `uint32 keysByteSize`:
    - `aa/catalog.bin`: `0x038AE0` (`232.160` bayt) $\rightarrow$ `232.160 / 8 =` **29.020** adet `(uint32 keyOffset, uint32 locationListOffset)` anahtar-konum çifti (`0x24 + 0x38AE0 = 0x38B04 == idOffset - 4`).
    - `AddrData/catalog_info.bin`: `0x049670` (`300.656` bayt) $\rightarrow$ `300.656 / 8 =` **37.582** adet `(uint32 keyOffset, uint32 locationListOffset)` çifti (`0x24 + 0x49670 = 0x49694 == idOffset - 4`).
  - `idOffset`: `"AddressablesMainContentCatalog"`.
  - `buildResultHashOffset`:
    - `aa/catalog.bin`: `"7eb98230c27092580c839722562a28fa"` (**1.302** benzersiz `.bundle` referansı).
    - `AddrData/catalog_info.bin`: `"6658876dbc881cca10bbd77f47c4be19"` (**539** benzersiz `.bundle` referansı; `SI.Addressables.CatalogInfoData` ve `MultiAddressIndex` tarafından forma/logo/oyuncu/top varlık çözümlemesinde kullanılır).

### 3.2 `fm_Data/manifest.dat` (`SI.UnityBuildVerification.BuildVerifierUtilities.ReadManifest`)
`GameAssembly.dll` içindeki `BuildVerifierUtilities.ReadManifest` (`RVA 0x01981710..0x019818F6`, `BuildVerifierUtilities.cs:39..65`) ve `BuildVerifierPaths.CalculateHash` (`RVA 0x01981378..0x01981419`, `BuildVerifierPaths.cs:129..131`) fonksiyonlarının x86-64 disassembly analiziyle dosyanın ikili şeması tamamen çözülmüştür:

- **FM27 `manifest.dat` (`30.975` bayt = `1.239` × `25` baytlık kayıt):**
  - `0..4` (`uint32`): `path_hash` (dosya göreli yolunun UTF-8 baytları üzerinden hesaplanan 32-bit hash; `1.235` aktif hash + `4` kök `0x00000000` kaydı).
  - `4..8` (`int32`): `hash_byte_len = 16` (`0x00000010`).
  - `8..24` (`16` bayt): Ham ikili (raw binary) **MD5** özeti (`128-bit`).
  - `24` (`uint8`): `0x0A` (`\n` satır sonu ayırıcısı).
- **FM26 `manifest.dat` (`37.000` bayt = `1.000` × `37` baytlık kayıt):**
  - `0..4` (`uint32`): `path_hash`.
  - `4..36` (`32` bayt): ASCII onaltılık (hex) **MD5** dizgesi.
  - `36` (`uint8`): `0x0A` (`\n`).

---

## 4. `shared/data/sianim/` 3B Maç Animasyon Motoru (`CAT\x00` ve `.amd`)

### 4.1 `animations/*.cat` (`CAT\x00` v38/v37) İkili Formatı ve `STAB` Dize Tablosu
`game_plugin.dll` içindeki `RVA 0x007F6C50..0x007F6F90` fonksiyonunun x86-64 disassembly analiziyle `.cat` dosyalarının yapısı baytına kadar çözülmüştür:

1. **Tekil `CAT\x00` Klip Paketi Yapısı (`r15` = klip başlangıcı, `rax` = `clip_size >= 13`):**
   - `0..4`: Sihirli sayı `b"CAT\x00"` (`0x00544143`).
   - `4..8`: `uint32 version` (**FM27'de `38` (`0x26`)**, **FM26'da `37` (`0x25`)**).
   - `8 .. clip_size - 5 - 9 * section_count`: Sıkıştırılmış kuaterniyon/transform anahtar kare (keyframe) iz verileri.
   - `clip_size - 5 - 9 * section_count .. clip_size - 5`: `section_count` × **9 baytlık** kemik bölümü (bone section) tanımlayıcı tablosu:
     - `+0..4` (`uint32`): `section_header_param`
     - `+4..8` (`uint32`): `section_data_offset` (`8 <= offset < trailer_start`, monoton artan)
     - `+8` (`uint8`): `track_count` (bu kemik bölümündeki animasyon izi sayısı)
   - `clip_size - 5` (`uint8`): `section_count` (her standart klipte `92` kemik bölümü).
   - `clip_size - 4 .. clip_size` (`uint32`): `clip_size` (klibin kendi toplam bayt boyutu; `cmp rax, rcx` @ `0x007F6CDB`).
2. **Arşiv Düzeyinde Geriye Doğru Yürüme (EOF $\rightarrow$ `0`) ve `STAB` Tablosu:**
   - Bir `.cat` dosyası ardışık `CAT\x00` klip paketlerinin birleşimidir. Dosya sonundaki (`EOF - 4`) `uint32` değerinden başlanarak her klibin kendi `clip_size` değeriyle geriye doğru yüründüğünde **tüm `.cat` dosyalarında tam `offset = 0` noktasına (`0` artık bayt ile) ulaşılmaktadır!**
   - `pack.cat` dosyasının sonunda ayrıca `EOF - last_u32` (`29.380.494`) adresinde **`STAB`** (`0x42415453`) sihirli sayısıyla başlayan bir dize tablosu yer alır ve `pack.cat` içindeki **5.819** `CAT\x00` klibin tam dosya yollarını (`1:1` eşleşmeyle **5.819** null-sonlandırmalı UTF-8 dize) barındırır:

| `.cat` Dosyası (FM27) | Boyut (Bayt) | Sürüm | `walked_to` | `CAT\x00` Klip Sayısı | Toplam Kemik Bölümü (`9B`) | Toplam Animasyon İzi | `STAB` Klip Adı Sayısı |
|---|---:|---:|---:|---:|---:|---:|---:|
| `locomotion_female.cat` | 29.717.081 | v38 | `0` (`%100`) | **49** | 4.508 | 3.773 | 0 |
| `locomotion_male.cat` | 35.442.004 | v38 | `0` (`%100`) | **52** | 4.784 | 3.996 | 0 |
| `locomotion_official.cat` | 3.026.725 | v38 | `0` (`%100`) | **12** | 1.104 | 956 | 0 |
| `pack.cat` | 29.800.182 | v38 | `0` (`%100`) | **5.819** | 535.348 | 548.715 | **5.819** (`male`: 4.651, `cutscene`: 854, `female`: 314) |
| **TOPLAM** | **97.985.992** | **v38** | **`0` (`%100`)** | **5.932** | **545.744** | **557.440** | **5.819** |

### 4.2 `animations/*.amd` (v4 Animation Motion Matching Veritabanları)
Motion Matching motorunun (`locomotion_*.cat` klipleri içindeki kare aralıklarını hız, yön ve poz vektörleriyle eşleştiren indeks) ikili şeması:
- `0` (`uint8`): `version = 4`.
- `1..3` (`uint16`): `segment_count` (`N`).
- `3 .. 3 + N * 11`: `N` adet **11 baytlık** (`<IIHB`) Motion Matching segment kaydı:
  - `start_frame` (`uint32`), `end_frame` (`uint32`), `clip_state_id` (`uint16`), `flags` (`uint8`).
- `3 + N * 11 .. 3 + N * 11 + 2` (`uint16`): İkinci tablo başlığı (`== N`), ardından her kare için `float32` hareket/yörünge öznitelik (feature) vektörleri:

| `.amd` Dosyası (FM27) | Boyut (Bayt) | Sürüm | Segment Sayısı (`11B`) | Toplam Kare Aralığı (`end - start`) | Özellik Yükü (Bayt) | Kare Başına Ortalama Bayt |
|---|---:|---:|---:|---:|---:|---:|
| `locomotion.amd` | 5 | v4 | 0 (`04 00 0c 40 71`) | 0 | 0 | 0 |
| `locomotion_female.amd` | 7.076.130 | v4 | **1.503** | **45.100** | 7.059.592 | `156,53` B (~39 `float32`) |
| `locomotion_male.amd` | 8.259.025 | v4 | **1.447** | **51.824** | 8.243.103 | `159,06` B (~39 `float32`) |
| `locomotion_official.amd` | 648.569 | v4 | **2.550** | **68.775** | 620.514 | `9,02` B |

### 4.3 `schemas/*.json` (`44` Aksiyon Şeması) ve `skeletons*` (`19` İskelet Dosyası)
- `shared/data/sianim/schemas/*.json`: Maç motorundaki şut, pas, kafa vuruşu, kayarak müdahale, kaleci kurtarışı, taç atışı ve gol sevinci aksiyonlarının (`celebrate_moving_big.json` .. `throw_in.json`) animasyon seçim parametrelerini tanımlayan **44** JSON şeması (FM26'da **41**).
- `shared/data/sianim/skeletons/config.xml` + `skeletons/{female,male}/*.json` (**10** dosya) + `skeletons_dev_ui_data/{female,male}/*.json` (**8** dosya): Kadın ve erkek oyuncu/hakem 3B iskelet kemik hiyerarşileri ve eklem kısıtlamaları.

---

## 5. Unity `SerializedFile v22` Konteynerleri ve Çalışma Zamanı Yapılandırmaları (`fm_Data/`)

`fm_Data/` dizinindeki tüm Unity `SerializedFile v22` (`header version = 22`, `unity_version = "6000.3.18f1-custom"`, `target_platform = 19` / `StandaloneWindows64`) konteynerlerinin tip tabloları (`23B` standart tip / `39B` `MonoBehaviour` tipi), nesne tabloları (`24B` `ObjectInfo`), script referansları (`12B`) ve dış dosya bağımlılıkları (`FileIdentifier`) tamamen ayrıştırılmıştır:

| Konteyner Dosyası | Boyut (Bayt) | Eşlik Eden `.resS` | Unity Sürümü | Tip Sayısı | Nesne Sayısı | Script Tipi | Dış Referanslar |
|---|---:|---:|---|---:|---:|---:|---|
| `globalgamemanagers` | 388.132 | — | `6000.3.18f1-custom` | 19 | **19** | 0 | `globalgamemanagers.assets`, `unity default resources`, `unity_builtin_extra`, `resources.assets`, `sharedassets0.assets` |
| `globalgamemanagers.assets` | 1.860.728 | 4.173.536 | `6000.3.18f1-custom` | 50 | **5.964** | 42 | `unity default resources`, `unity_builtin_extra` |
| `resources.assets` | 1.249.176 | 1.595.600 | `6000.3.18f1-custom` | 62 | **2.019** | 50 | `globalgamemanagers.assets`, `unity default resources` |
| `sharedassets0.assets` | 362.700 | 416 | `6000.3.18f1-custom` | 7 | **20** | 1 | `globalgamemanagers.assets`, `unity default resources` |
| `level0` | 40.524 | — | `6000.3.18f1-custom` | 34 | **328** | 24 | `globalgamemanagers.assets`, `unity default resources`, `sharedassets0.assets` |
| `Resources/unity default resources` | 5.923.140 | — | `6000.3.11f1` | 8 | **99** | 1 | — |
| `Resources/unity_builtin_extra` | 491.796 | — | `6000.3.18f1-custom` | 1 | **49** | 0 | — |

Ayrıca çalışma zamanı yapılandırma dosyaları:
- `fm_Data/RuntimeInitializeOnLoads.json` (`16.004` B): Oyun başlangıcında `[RuntimeInitializeOnLoadMethod]` ile tetiklenen tüm C# metod kayıtları.
- `fm_Data/ScriptingAssemblies.json` (`6.917` B): IL2CPP çalışma zamanına yüklenen **249** C# assembly adı ve tür bayrakları.
- `fm_Data/boot.config` (`216` B): Unity motoru önyükleme parametreleri (`gfx-enable-gfx-jobs=1`, `wait-for-native-debugger=0`, `hdr-display-enabled=0`, `gc-max-time-slice=3`).
- `fm_Data/app.info` (`38` B): `Sports Interactive` / `Football Manager 26`.

---

## 6. Tüm `17` Native PE64 İkili Dosyası, `lang_db.dat` ve Tarihsel Veritabanları

### 6.1 Kurulumdaki Tüm `17` Native PE64 (`x86-64`) İkili Dosyası
Kurulumdaki tüm `.exe` ve `.dll` dosyalarının PE64 başlıkları, bölüm (section) tabloları, Export Directory girişleri ve `.pdata` (`RUNTIME_FUNCTION`) istisna tabloları çıkarılmıştır (**toplam `14.106` export ve `532.123` `.pdata` fonksiyon girişi**):

| İkili Dosya | Boyut (Bayt) | Bölüm | Export Sayısı | `.pdata` Fonksiyonu | Rolü / Alt Sistemi |
|---|---:|---:|---:|---:|---|
| `fm.exe` | 667.648 | 6 | 4 | 315 | Ana Windows başlatıcısı (`UnityMain` yükleyicisi) |
| `UnityPlayer.dll` | 36.528.040 | 8 | 2 | 111.094 | Unity `6000.3.18f1-custom` C++ çekirdek çalışma zamanı motoru |
| `GameAssembly.dll` | 59.361.792 | 8 | 373 | 175.972 | IL2CPP tarafından C#'tan derlenmiş `249` assembly makine kodu |
| `game_plugin.dll` | 404.308.480 | 13 | 282 | 145.090 | Sports Interactive C++ maç, veritabanı, transfer, gözlemcilik ve kayıt motoru |
| `lib_burst_generated.dll` | 1.013.248 | 5 | 1.116 | 1.822 | Unity Burst SIMD/AVX2 derlenmiş maç/fizik/animasyon rutinleri |
| `EOSSDK-Win64-Shipping.dll` | 19.531.704 | 7 | 680 | 65.926 | Epic Online Services çok oyunculu / çapraz ağ SDK'sı |
| `PartyWin.dll` | 4.038.728 | 6 | 157 | 10.526 | Azure PlayFab Party ağ iletişimi kütüphanesi |
| `PlayFabMultiplayerWin.dll` | 1.882.656 | 6 | 79 | 5.294 | PlayFab lobi ve eşleştirme (matchmaking) kütüphanesi |
| `icuin65.dll` | 2.632.704 | 6 | 5.766 | 7.287 | ICU 65 uluslararasılaştırma (collation/sıralama/takvim) kütüphanesi |
| `icuuc65.dll` | 1.890.304 | 6 | 3.002 | 4.782 | ICU 65 Unicode temel karakter/dize işleme kütüphanesi |
| `icudt65.dll` (+ `icudt65l.dat`) | 3.072 (+ `27,9 MB`) | 2 | 1 | 0 | ICU 65 yerel ayar (locale) ve Türkçe/diğer dil sıralama veri tablosu |
| `steam_api64.dll` | 317.080 | 6 | 1.054 | 810 | Steamworks API entegrasyonu |
| `crashpad_handler.dll` | 630.784 | 7 | 0 | 1.800 | Crashpad hata dökümü yakalayıcısı |
| `BacktraceCrashpadWindows.dll` | 178.688 | 7 | 3 | 550 | Backtrace kilitlenme raporlama köprüsü |
| `msvcp140.dll` | 642.720 | 6 | 1.515 | 1.365 | MSVC C++ standart kütüphane çalışma zamanı |
| `vcruntime140.dll` | 178.848 | 8 | 71 | 383 | MSVC C çalışma zamanı |
| `vcruntime140_1.dll` | 50.256 | 6 | 3 | 107 | MSVC C++ CxxFrameHandler4 istisna işleyicisi |

### 6.2 `lang_db.dat` (`90,96 MB` — `401` Zstd Çerçevesi) ve Tarihsel Veritabanı Sürümleri (`2300`..`2700`)
- **`shared/data/database/db/2700/2700_fm/lang_db.dat` (`90.962.133` bayt):**
  - `\x03\x01tad.` başlığı altında **401** bağımsız Zstd çerçevesi (`1` temel ülke tablosu + **`25` dil × `16` yerelleştirilmiş isim tablosu**) barındırır.
  - Her dil bloğundaki `16` tablonun satır sayıları (dil başına toplam **229.555** yerelleştirilmiş satır):
    - Turnuvalar (`competitions`): **8.084**
    - Kulüpler (`clubs`): **100.432**
    - Şehirler (`cities`): **58.475**
    - Stadyumlar (`stadiums`): **52.406**
    - Ödüller (`awards`): **3.902**
    - Açıklamalar (`descriptions`): **2.532**
    - Sakatlıklar (`injuries`): **1.681**
    - Para birimleri/diğer (`currencies/misc`): **924** + **502** + **288** + **180** + **136** + **7** + **6** (ve `frame[0]` içinde **251** ülke).
- **Tarihsel Veritabanı Sürümleri (`shared/data/database/db/`):**
  - `2300` (`25` dosya, `169,1 MB`), `2330` (`25` dosya, `101,0 MB`), `2340` (`25` dosya, `98,0 MB`), `2400` (`34` dosya, `264,7 MB`), `2430` (`34` dosya, `198,1 MB`), `2600` (`54` dosya, `306,6 MB`), `2620` (`54` dosya, `362,2 MB`), `2700` (`52` dosya, `389,6 MB`).

---

## 7. CLI ve Python API ile Yeniden Üretim Komutları

```powershell
# 1. Kategori 2 (kalan tüm dosyalar) decompile çıktısını tek başına JSON olarak üretmek için:
python -m fm26save.cli decompile-binaries --mode remaining --fm-dir "C:\Program Files (x86)\Steam\steamapps\common\Football Manager 27"

# 2. Tüm decompile çıktısını (Kategori 1 + Kategori 2 dahil) docs/decompiled_engine/FM27 altına üretmek için:
python -m fm26save.cli decompile-binaries --mode dump --fm-dir "C:\Program Files (x86)\Steam\steamapps\common\Football Manager 27" --out-dir docs/decompiled_engine/FM27

# 3. Repo içinde saklanan nesne modeli raporunu (docs/object_model/FM27_OBJECT_MODEL.md) güncellemek için:
python -m fm26save.cli decompile-binaries --mode report --out-dir docs/decompiled_engine/FM27
```
