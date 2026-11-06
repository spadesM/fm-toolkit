# Araştırma Arşivi — FM27 Gözlemci Öncelikleri Sıralama Sorunu

Bu klasörde [FM27_SCOUTING_PRIORITIES_SORTING_FIX_TR.md](../../FM27_SCOUTING_PRIORITIES_SORTING_FIX_TR.md) raporunun dayandığı **ham araştırma materyali** saklanıyor. Rapor sonuçları özetliyor; burada ise sonuca nasıl varıldığını gösteren betikler ve çıktılar var.

| Yol | İçerik |
|---|---|
| [`ANALYSIS_WORKING_LOG_TR.md`](./ANALYSIS_WORKING_LOG_TR.md) | Çalışma sırasında tutulan ayrıntılı not dosyası: FM26 bundle/obje/PathID tabloları, RVA haritaları, betik listesi, FM27 düzeltmesi |
| [`scripts/`](./scripts) | Bu araştırmada yazılan **tüm** Python betikleri (634 dosya, yaklaşık 1 MB) |
| [`outputs/`](./outputs) | Seçilmiş betik çıktıları (120 KB altındaki metin dökümleri, disassembly'ler, UXML alan dökümleri) |

## Önemli betikler

| Betik | Ne yapar |
|---|---|
| `use_fm27.py` | **Diğer betiklerden önce import edilir.** `fm26save.binary_decompiler.DEFAULT_FM_PATHS` değerini FM27 kurulumuna yönlendirir |
| `check_deep_sorting.py` | PE64 bölümleri, `.pdata` fonksiyon sınırları, `g_CodeGenModules` → `rva_to_method_name` haritası, `dump_func_details` (FM26 için; `use_fm27` ile FM27'ye çevrilebilir) |
| `cs_disasm.py` | capstone tabanlı disassembler; çağrı hedeflerine metod adlarını yazar (`disasm(rva)`, `find_rva(name)`) |
| `meta_usage.py` | IL2CPP v31 `Il2CppMetadataRegistration` bulur; RIP-relative slotları tip (`TypeInfo`/`Il2CppType`) veya string literal olarak çözer |
| `decode_all_props_and_table.py` | `PropertyRegistration.Initialise` → 8.225 FourCC ↔ özellik adı; `*Reference` sınıflarının ID, türetme, özellik ve alt-tip tabloları |
| `cs_dump_sorting_chain.py`, `cs_dump_header_chain.py` | `StreamedTable`/`StreamedListView` sıralama ve başlık zincirinin tam disassembly'si (→ `outputs/cs_*.txt`) |
| `compare_full_st_serialized_data.py`, `check_refs_and_grid.py` | Bundle içindeki `MonoBehaviour`/`UxmlSerializedData` ağaçlarını (`ref_types` dahil) TypeTree ile yürütür |
| `print_st_all_fields.py`, `diff_streamed_tables.py` | FM26 `StreamedTable` UXML alanlarını döker ve karşılaştırır |
| `tableview_sorting_disabled.py` | Tüm table view'larda `m_sortingDisabled` envanteri |
| `fm27_find_bundles.py` | FM27 bundle'larında anahtar dizge araması |
| `fm27_scout_priorities_uxml.py` | FM27 `ScoutPrioritiesBlock` UXML alanları (**kök neden burada görüldü:** `DisableSorting: 1`) |
| `fm27_find_factory.py`, `fm27_tableviews_factories.py` | FM27 `PlayerTableFactory` sütun sıralama yolları ve `ScoutPrioritiesTableSettings` |
| `bundle_locate_byte.py` | Sıkıştırılmamış bir ofsetin hangi LZ4 bloğunda olduğunu ve literal mi eşleşme mi olduğunu gösterir |
| `patch_fm27_scout_priorities_sorting.py` | İlk yama betiği. Kalıcı sürümü: `python -m fm26save.ui_patches` |

## Notlar

- Betiklerin çoğunda yollar sabit yazılmış (`C:\Users\mcaka\.gemini\…\scratch`, `c:\Repos\fm26save`). Başka bir makinede çalıştırmak için `sys.path.insert` satırlarını bu klasörü gösterecek şekilde değiştirin.
- Adı `fm27_` ile başlamayan betikler **FM26** kurulumu üzerinde çalıştırıldı (bkz. raporun "Araştırma süreci" bölümü). RVA'lar FM26 `GameAssembly.dll` (53.639.168 bayt) içindir.
- Gerekli paketler: `capstone` (disassembly), `lz4` (yama yazımı). İkisi de `pip install` ile kurulabilir.
- Oyun dosyaları (bundle, DLL, metadata) telif nedeniyle repoya **eklenmedi**. Yalnızca türetilmiş metin dökümleri var.
