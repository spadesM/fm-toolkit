# `docs/decompiled_engine` Yeniden Üretim ve Nesne Modeli Rehberi

Bu rehber, **`docs/decompiled_engine/`** dizinindeki tüm tersine mühendislik çıktılarını (C# tipleri, `SI.Bindable` `PropertyRegistration` / `ContextRegistration` FourCC tabloları, `*Reference` varlık grafiği, `.fmf` simülasyon tabloları, `game_plugin.dll` C++ export'ları ve UnityFS UI `.bundle` envanteri) mevcut araç setiyle **tek komutla nasıl yeniden üretebileceğinizi** ve depoda versiyonlanan **yapısal nesne modeli raporlarını** açıklar.

---

## 1. Neden `docs/decompiled_engine/` Git'e Eklenmez ve Nasıl Korunur?

`docs/decompiled_engine/` dizini, oyun ikililerinden (`GameAssembly.dll`, `global-metadata.dat`, `il2cpp.usym`, `.fmf`, `.bundle`) doğrudan üretilen ~75 MB boyutunda ham JSON dökümleri ve C# başlık dosyaları (`DecompiledAllGameAssemblies.cs`, `DecompiledReferences.cs`) içerir. Telif ve depo boyutu nedeniyle bu dizin `.gitignore` içindedir.

Buna karşılık:
1. **Tam Yeniden Üretilebilirlik:** `fm26save/binary_decompiler.py` hem **FM26** (Unity `6000.0.52f1`, IL2CPP `global-metadata.dat` **v31**) hem de **FM27** (Unity `6000.3.18f1`, IL2CPP `global-metadata.dat` **v39**) ikililerini %100 saf Python ile ayrıştırır. Herhangi bir üçüncü parti araca (Ghidra, IDA, Il2CppDumper vb.) ihtiyaç duymadan tüm `docs/decompiled_engine/` içeriği ~15–20 saniyede sıfırdan üretilebilir.
2. **Versiyonlanan Yapısal Nesne Modeli Raporları:** Ham C# kodlarını depoya koymadan, oyunun tüm nesne yapısını (`*Reference` sınıfları, Çekirdek DB Tablo FourCC kimlikleri, `Property`/`Context` sayıları, Assembly envanteri, UI `.bundle` ve `.fmf` özetleri) kayıt altına alan Markdown raporları doğrudan depoda saklanır:
   - [`docs/object_model/FM26_OBJECT_MODEL.md`](object_model/FM26_OBJECT_MODEL.md)
   - [`docs/object_model/FM27_OBJECT_MODEL.md`](object_model/FM27_OBJECT_MODEL.md)

---

## 2. Komut Satırından (CLI) Yeniden Üretim

### A. Tüm `docs/decompiled_engine/` Çıktılarını Üretmek (`--mode dump`)

**FM26 kurulumundan üretmek için:**
```powershell
python -m fm26save.cli decompile-binaries --mode dump `
  --fm-dir "C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26" `
  --out-dir docs/decompiled_engine
```

**FM27 kurulumundan üretmek için:**
```powershell
python -m fm26save.cli decompile-binaries --mode dump `
  --fm-dir "C:\Program Files (x86)\Steam\steamapps\common\Football Manager 27" `
  --out-dir docs/decompiled_engine_fm27
```

> **İpucu:** `--fm-dir` parametresi verilmezse araç sırasıyla `FM_INSTALL_DIR` / `FM26_INSTALL_DIR` ortam değişkenlerine, ardından varsayılan Steam (`Football Manager 26` / `Football Manager 27`) kurulum dizinlerine bakar.

### B. Yapısal Nesne Modeli Raporunu Üretmek (`--mode report`)

Mevcut bir `decompiled_engine` dökümünden (veya döküm yoksa otomatik olarak oyun dizininden) telifsiz, Git'e commit edilebilir Markdown nesne modeli raporu üretmek için:

```powershell
# FM26 Nesne Modeli Raporu
python -m fm26save.cli decompile-binaries --mode report `
  --out-dir docs/decompiled_engine `
  --report-path docs/object_model/FM26_OBJECT_MODEL.md

# FM27 Nesne Modeli Raporu
python -m fm26save.cli decompile-binaries --mode report `
  --out-dir docs/decompiled_engine_fm27 `
  --report-path docs/object_model/FM27_OBJECT_MODEL.md
```

### C. Alt Bileşenleri Tek Tek Sorgulamak

Tüm dökümü diske yazmadan belirli bir alt sistemi incelemek için:
- `--mode metadata --filter PersonSearch` -> `global-metadata.dat` içinden eşleşen C# tiplerini, enum'ları ve metot imzalarını döndürür.
- `--mode bindings --entity PersonReference` -> `GameAssembly.dll` içinden FourCC property/context kayıtlarını ve `*Reference` sınıflarını döndürür.
- `--mode usym --filter Scouting` -> `il2cpp.usym` sembol tablosundan SI'ın orijinal C#/C++ kaynak dosya yollarını, RVA adreslerini ve `mapped_csharp_method_count` sayısını döndürür.
- `--mode csharp-bodies --filter ScoutPrioritiesTableFactory` -> Seçilen C# sınıf veya metodunun `GameAssembly.dll` içindeki x86-64 makine kodunu `il2cpp.usym` `.cs:satır` numaraları (`[L...]`) ve çözümlenmiş `call` hedefleriyle söker.
- `--mode tables` -> `tables.fmf`, `simatch.fmf`, `training.fmf`, `simatchshared.fmf` içindeki ikili JSB tablolarını çözer.
- `--mode game-plugin` -> `game_plugin.dll` ve `lib_burst_generated.dll` PE64 C++ export tablosunu, `.pdata` (`139.131` C++ fonksiyonu) istatistiklerini, `224` `ActionContributor` ve `58` `SearchFilter` vtable sınıfını çıkarır.
- `--mode fmf-all` -> Tüm `.fmf` arşivlerinin dizinlerini, `filters.fmf` oyuncu arama filtrelerini, `constants.fmf` sabitlerini, `non_pl_hist_{index,id,dt}.dat` (`3,52` milyon personel kariyer satırı), `summary.dat` (`96.171` kulüp özeti) ve `lang_db_general.dat` (`401` Zstd çerçevesi) verilerini çıkarır.
- `--mode ui-bundles` -> Tüm 69 UnityFS v8 (LZ4) UI/Bindable `.bundle` dosyasını açarak `.uxml`/`.asset` yollarını, `174` `TableFactory` sınıfını, `2.102` `binding.*` sütun bağlamasını, `592` `TableView` şablonunu ve veri bağlama (`binding`) ifadelerini listeler.

> **Ayrıntılı Teknik Referans:** Kısmen çözümlenmiş 5 sistemin tam ikili şema referansı için bkz. [`FM27_PARTIAL_FILES_FULL_DECOMPILATION_TR.md`](FM27_PARTIAL_FILES_FULL_DECOMPILATION_TR.md).

---

## 3. Python API ile Kullanım

```python
from fm26save import (
    dump_decompiled_codebase,
    write_object_model_report,
    decompile_global_metadata,
    decompile_gameassembly_bindings,
)

# 1. Tüm 11 dosyayı docs/decompiled_engine altına üret
summary = dump_decompiled_codebase(
    fm_install_dir=r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 27",
    output_dir="docs/decompiled_engine_fm27",
)

# 2. Yapısal Markdown raporunu oluştur
write_object_model_report(
    dump_dir="docs/decompiled_engine_fm27",
    output_path="docs/object_model/FM27_OBJECT_MODEL.md",
)
```

---

## 4. `docs/decompiled_engine/` Dosya Şeması (11 Dosya)

`--mode dump` çalıştırıldığında hedef dizinde aşağıdaki **11 dosya** oluşturulur:

| # | Dosya Adı | İçerik ve Yapısal Şema |
|---|---|---|
| 1 | `manifest.json` | Üretim zamanı, kaynak oyun dizini (`FM26` / `FM27`), `GameAssembly.dll` ve `global-metadata.dat` boyut + SHA-1 özetleri ve üretilen dosyaların bayt boyutları. |
| 2 | `properties_and_contexts.json` | `PropertyRegistration.Initialise` ve `ContextRegistration.Initialise` metotlarının x86-64 makine kodundan çözülen **FourCC (`0xXXXXXXXX`) -> İsim + Assembly** eşlemeleri (`counts`, `properties`, `contexts`). |
| 3 | `entity_reference_graph.json` | Tüm `*Reference` sınıflarının (`PersonReference`, `ClubReference`, `ScoutPlayerPrioritiesReference`, `PersonSearchReference` vb.) tam nesne grafiği: `entity_id_hex`, `entity_fourcc`, `is_core_db_table`, `db_table_index`, `derives_from`, `properties`, `parameterized_properties`, `contexts`, `child_entity_references`. |
| 4 | `enums_and_structs.json` | `global-metadata.dat` içinden çözülen tüm enum sabitleri (`enums`: tam ad -> `{ad: sayısal_değer}`) ve `FM.*` / `SI.*` / `Assembly-CSharp` C# tiplerinin (`fm_si_types`) alan (`fields`), özellik (`properties`) ve metot (`methods`) tanımları. |
| 5 | `engine_lookup_tables.json` | `tables.fmf`, `simatch.fmf`, `training.fmf` ve `simatchshared.fmf` içindeki derlenmiş `.jsb` simülasyon tabloları (`jumping_reach_table`, `aerial_reach_table`, `qme_stat_relevant_attributes`, `oop_attributes_scoring`, `player_ratings_data`, `team_picking_weights_master`, `training_tables`). |
| 6 | `usym_source_tree.json` | `il2cpp.usym` sembol tablosundan çıkarılan SI iç kaynak kodu dosya ağacı (`source_files`) ve örnek RVA -> kaynak satır (`records_sample`) eşlemeleri. |
| 7 | `game_plugin_native_exports.json` | `fm_Data/Plugins/x86_64/game_plugin.dll` ve `lib_burst_generated.dll` içindeki tüm C/C++ P/Invoke export fonksiyonları, RVA/VA adresleri ve alt sistem dağılımı. |
| 8 | `all_fmf_configs_and_filters.json` | Oyun kurulumundaki tüm `.fmf` arşivlerinin dosya envanteri, `filters.fmf` içindeki `person_search_filters`, `achievements.xml`, `leaderboards.xml`, `settings_xmls`, `versus_comps_xmls`, `sianim_skeletons` ve `shared/data` altındaki `.dat`/`.dbc`/`.edt`/`.lnc` envanteri. |
| 9 | `unity_ui_bundles_decompiled.json` | LZ4 ile sıkıştırılmış UnityFS v8 UI `.bundle` dosyalarından çıkarılan `Assets/.../*.uxml` / `*.asset` yolları ve benzersiz UI veri bağlama (`player.*`, `person.*`, `club.*` vb.) yolları. |
| 10 | `DecompiledReferences.cs` | Tüm `*Reference` sınıflarını kalıtım zinciri, FourCC sabitleri ve `public object <Property> { get; }` bildirimleriyle sunan tek parça C# referans dosyası. |
| 11 | `DecompiledAllGameAssemblies.cs` | Tüm `FM.*` ve `SI.*` C# sınıflarını, struct'larını, enum sabitlerini, alanlarını ve metot imzalarını içeren kapsamlı C# bildirim dosyası. |

---

## 5. FM26 (IL2CPP v31) ve FM27 (IL2CPP v39) İkili Format Farkları

`fm26save/binary_decompiler.py` içindeki `_parse_metadata_header()` fonksiyonu `global-metadata.dat` başlığındaki `version` alanını okuyarak her iki oyun motoru sürümünü otomatik olarak destekler:

| Özellik | FM26 (`version = 31`, Unity `6000.0.52f1`) | FM27 (`version = 39`, Unity `6000.3.18f1`) |
|---|---|---|
| Başlık Tablo Girişleri | `(offset, size)` ikilileri (`2 x int32`) | `(offset, size, count)` üçlüleri (`3 x int32`) |
| `Il2CppStringLiteral` | `8` bayt (`<II`: `length, dataIndex`) | `4` bayt (`<I`: `dataIndex`, uzunluk ardışık farktan hesaplanır) |
| `Il2CppImageDefinition` | `40` bayt (`<10i`, `typeStart=u[2]`, `typeCount=u[3]`) | `36` bayt (`<iiHH...`, `typeStart` ve `typeCount` `uint16` olarak `+8` ofsetinde) |
| `Il2CppTypeDefinition` | `88` bayt (`<22i`) | `76` bayt (`<13i8Hii`) |
| `Il2CppMethodDefinition` | `36` bayt (`<7i4H`) | `30` bayt (`<iiiihIHHHH`) |
| `Il2CppFieldDefinition` | `12` bayt (`<iiI`) | `10` bayt (`<iiH`) |
| `Il2CppParameterDefinition` | `12` bayt | `10` bayt |
| `Il2CppFieldDefaultValue` | `12` bayt (`<iii`) | `10` bayt (`<iHi`) |
| UI UXML Bundle Yapısı | `ui-panelids-uxml_assets_all.bundle`, `ui-widgets_assets_all.bundle` vb. | `ui-visualtreeassets_assets_globalvisualtreeassetpreload.bundle` ve `*gameworld*` |
