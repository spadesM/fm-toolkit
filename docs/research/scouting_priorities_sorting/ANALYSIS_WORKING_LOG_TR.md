# FM26/FM27 Gözlemcilik Öncelikleri (Scout Priorities) Sıralama Analiz Raporu

> [!IMPORTANT]
> **Kalıcı sürüm repoda:** [docs/FM27_SCOUTING_PRIORITIES_SORTING_FIX_TR.md](../../FM27_SCOUTING_PRIORITIES_SORTING_FIX_TR.md). Yama aracı: [fm26save/ui_patches.py](../../../fm26save/ui_patches.py). Araştırma arşivi: [docs/research/scouting_priorities_sorting/](./README.md). Bu dosya çalışma günlüğüdür.

> [!WARNING]
> **Önemli düzeltme (5.11.2026):** Bölüm 1–4'teki analizlerin tamamı yanlışlıkla **FM26** kurulumu (`Football Manager 26\`) üzerinde yapıldı; çünkü `resolve_fm_install_dir()` önce FM26 yolunu seçiyordu. Kullanıcının oyunu **FM27**'dir: `C:\Program Files (x86)\Steam\steamapps\common\Football Manager 27\` (GameAssembly.dll 59.361.792 bayt, 2.11.2026). FM27'de bundle yapısı farklıdır (`ui-recruitment_assets_all.bundle` yoktur). Bundan sonraki analizler [use_fm27.py](file:///C:/Users/mcaka/.gemini/antigravity/brain/f3fe4be7-d8a5-4ec7-895a-ec06f09f2529/scratch/use_fm27.py) ile FM27'ye yönlendirilir. FM26'dan elde edilen genel mekanizma bilgisi (SI.Bindable sıralama zinciri) FM27 için de büyük olasılıkla geçerlidir ama RVA'lar farklıdır.

## ✅ SONUÇ (FM27): Kök Neden ve Uygulanan Düzeltme

**Kök neden:** FM27'de Gözlemcilik Öncelikleri tablosunun UXML'i (`ScoutPrioritiesBlock`, PathID `2056832882284531458`) tablo seviyesinde **`DisableSorting = 1`** ile kaydedilmiş. Bu bayrak `StreamedTable.MakeColumnHeader` içinde okunuyor; `1` olunca sütun başlıklarına tıklama işleyicisi hiç bağlanmıyor, yani başlığa tıklamak hiçbir şey yapmıyor. Oyuncu Veritabanı tablosunda bu bayrak `0`.

| Öğe | Değer |
|---|---|
| Bundle | [ui-visualtreeassets_assets_globalvisualtreeassetpreload.bundle](file:///C:/Program%20Files%20(x86)/Steam/steamapps/common/Football%20Manager%2027/fm_Data/StreamingAssets/aa/StandaloneWindows64/ui-visualtreeassets_assets_globalvisualtreeassetpreload.bundle) (UnityFS v8, LZ4HC, 219 blok) |
| Obje | `ScoutPrioritiesBlock` (Obj 2477) → `StreamedTable/UxmlSerializedData` |
| Alan | `DisableSorting` @ sıkıştırılmamış ofset `0x1194584` (blok 140, göreli `0x14584`) |
| Komşu alan | `MovedItemBinding = Team.ScoutPriorities.SpecificallyScoutedPlayerMove` (sürükle-bırak ile öncelik sırası) |
| Fabrika | `PlayerTableFactory` (`49c25af4…`); görünüm `ScoutPrioritiesTableSettings`: tüm sütunlarda `m_sortingDisabled = 0` |
| Sütun sıralama yolları | `name → binding.surname`, `age → binding.DateOfBirth`, `club → binding.club.name`, `nation → binding.nation.name`, `inf → binding.PlayerStatusSortOrder`, `transfer-value → binding.transfervaluerange.SortValue`, `scouted-best-position-and-role → binding.positioncombined`, `recommendation-grade-only → binding.PlayerReportForContextTeam.OverallReportGradeInfo.Grade`; `assigned-staff`, `progress-remaining`, `assigment-length`, `drag-column`, `index` için sıralama yolu **boş** (bu sütunlar sıralanamaz) |

**Düzeltme:** Bayrak `1 → 0` yapıldı. Değişen 131.072 baytlık LZ4 bloğu yeniden sıkıştırıldı (19110 → 19109 bayt); blocksInfo ve başlık güncellendi. Doğrulama: yamalı bundle açıldığında orijinalden **yalnızca `0x1194584`'teki 1 bayt** farklı.

- Yedek: `…\ui-visualtreeassets_assets_globalvisualtreeassetpreload.bundle.bak` (orijinal SHA1 `f90e1712551338b4edfbaa9ae425e88a4bb8b126`)
- Yama/geri alma betiği: [patch_fm27_scout_priorities_sorting.py](file:///C:/Users/mcaka/.gemini/antigravity/brain/f3fe4be7-d8a5-4ec7-895a-ec06f09f2529/scratch/patch_fm27_scout_priorities_sorting.py) (`--apply`, `--restore`, parametresiz = kuru çalıştırma). Oyun güncellenince yama gider; betik içeriği doğrulayıp yeniden uygular, içerik değişmişse iptal eder.

**Yardımcı betikler (FM27):** [use_fm27.py](file:///C:/Users/mcaka/.gemini/antigravity/brain/f3fe4be7-d8a5-4ec7-895a-ec06f09f2529/scratch/use_fm27.py), [fm27_scout_priorities_uxml.py](file:///C:/Users/mcaka/.gemini/antigravity/brain/f3fe4be7-d8a5-4ec7-895a-ec06f09f2529/scratch/fm27_scout_priorities_uxml.py), [fm27_find_factory.py](file:///C:/Users/mcaka/.gemini/antigravity/brain/f3fe4be7-d8a5-4ec7-895a-ec06f09f2529/scratch/fm27_find_factory.py), [fm27_tableviews_factories.py](file:///C:/Users/mcaka/.gemini/antigravity/brain/f3fe4be7-d8a5-4ec7-895a-ec06f09f2529/scratch/fm27_tableviews_factories.py), [bundle_locate_byte.py](file:///C:/Users/mcaka/.gemini/antigravity/brain/f3fe4be7-d8a5-4ec7-895a-ec06f09f2529/scratch/bundle_locate_byte.py) (bir baytın hangi LZ4 bloğu/eşleşmesinden geldiğini bulur), [cs_disasm.py](file:///C:/Users/mcaka/.gemini/antigravity/brain/f3fe4be7-d8a5-4ec7-895a-ec06f09f2529/scratch/cs_disasm.py) (capstone tabanlı, metod adlı disassembler), [meta_usage.py](file:///C:/Users/mcaka/.gemini/antigravity/brain/f3fe4be7-d8a5-4ec7-895a-ec06f09f2529/scratch/meta_usage.py) (IL2CPP metadata usage → tip/string çözücü).

> [!WARNING]
> SI bu listede sıralamayı muhtemelen bilerek kapattı; çünkü satır sırası = gözlem önceliği ve sürükle-bırak ile değiştiriliyor. Liste sıralıyken sürükle-bırak yapmayın; yeni öncelik yanlış konuma yazılabilir. Ayrıca Addressables bundle bütünlüğünü (CRC) kontrol ederse ekran yüklenmeyebilir; o durumda `--restore` ile geri alın.

## 0. FM26 Üzerinde Doğrulanan Sıralama Kapısı (Gating) Zinciri

`StreamedTable.MakeColumnHeader` (FM26 `0x015eac30`) bir sütun başlığına tıklama işleyicisi bağlamadan önce şunları kontrol eder:
1. `StreamedTable.DisableSorting` (`this+0x9b8`, UXML `DisableSorting`) → ScoutPrioritiesBlock'ta `0`.
2. Etkin `StreamedTableView` içindeki sütun konfigürasyonu: `ColumnConfiguration.m_columnMetadata.m_sortingDisabled` (`config+0x18 → +0x11`) → ScoutPrioritiesTable (Obj 766) ve -Small (Obj 791) içindeki **tüm sütunlarda `0`**.
3. Sonra `OnHeaderClicked` (`0x015ec910`) → fabrika (`this+0x988`) sözlüğünden sütun girdisi → `SetSorting` (`0x015efce0`) → `"binding"` önekini atıp `StreamedListView.SetSortingBinding` → `ApplySorting` → `ProcessSortingDataChanged` (ara derinlikte `SI.Bindable.NullReference` gelirse değer nihai kabul edilir) → `SortComparer.Compare` (`string` için `EmbeddedDataUtilities.CompareText`, diğerleri için `IComparable`).
4. `Reorderable` (`VirtualisedList+0x5c1`) yalnızca sürükle-bırak (`OnStartItemDrag/OnItemDrag/OnEndItemDrag`) metodlarında okunur; sıralamayı doğrudan engellemez.

Sonuç: FM26 verilerinde sıralamayı statik olarak engelleyen bir bayrak bulunamadı → FM27 verileri ayrıca incelenmelidir.

## 1. İncelenen Oyun Dosyaları ve Varlıklar (Assets)

Oyun kurulum dizini: `C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26\`

### 1.1. Lokalizasyon Eşleşmesi
- [languages.fmf](file:///C:/Program%20Files%20(x86)/Steam/steamapps/common/Football%20Manager%2026/data/game_simulation/languages.fmf) (`turkish.ltc`):
  - `"Gözlemcilik"` = `Scouting` (`@399851`)
  - `"Gözlemci Öncelikleri"` = `Scout Priorities` (`@99226`)

### 1.2. Unity Addressables Bundle Dosyaları
Dizin: `C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26\fm_Data\StreamingAssets\aa\StandaloneWindows64\`

| Bundle Dosyası | İncelenen Obje | PathID / GUID | Rolü |
|---|---|---|---|
| [ui-tileslayouts_assets_all.bundle](file:///C:/Program%20Files%20(x86)/Steam/steamapps/common/Football%20Manager%2026/fm_Data/StreamingAssets/aa/StandaloneWindows64/ui-tileslayouts_assets_all.bundle) | `RecruitmentScoutPrioritiesBlockDescription` (`Obj 631`) | PathID `-6602144080943892039` | `16x7` boyutta `ScoutPrioritiesBlock`, `12x7` boyutta `ScoutPrioritiesBlock-Small` şablonunu yükler |
| [ui-recruitment_assets_all.bundle](file:///C:/Program%20Files%20(x86)/Steam/steamapps/common/Football%20Manager%2026/fm_Data/StreamingAssets/aa/StandaloneWindows64/ui-recruitment_assets_all.bundle) | `RecruitmentScoutPrioritiesCard` (`Obj 177`) | PathID `35620230135737672` | Kart görünümü (salt okunur özet tablo) |
| [ui-recruitment_assets_all.bundle](file:///C:/Program%20Files%20(x86)/Steam/steamapps/common/Football%20Manager%2026/fm_Data/StreamingAssets/aa/StandaloneWindows64/ui-recruitment_assets_all.bundle) | `ScoutPrioritiesBlock` (`Obj 229`) | PathID `2056832882284531458`, GUID `cf0dd6dadc040da40bdc6ebb7938a1fe` | **Gözlemci Öncelikleri ana oyuncu listesi (16x7)** |
| [ui-recruitment_assets_all.bundle](file:///C:/Program%20Files%20(x86)/Steam/steamapps/common/Football%20Manager%2026/fm_Data/StreamingAssets/aa/StandaloneWindows64/ui-recruitment_assets_all.bundle) | `ScoutPrioritiesBlock-Small` (`Obj 263`) | PathID `3674608651584989843`, GUID `76c0db9d2a0cbb14c89cabd9751b52a0` | **Gözlemci Öncelikleri dar oyuncu listesi (12x7)** |
| [ui-recruitment_assets_all.bundle](file:///C:/Program%20Files%20(x86)/Steam/steamapps/common/Football%20Manager%2026/fm_Data/StreamingAssets/aa/StandaloneWindows64/ui-recruitment_assets_all.bundle) | `RecruitmentTeamReportPrioritiesTableBlock` (`Obj 360`) | PathID `8842523188605194199` | Takım raporu öncelikleri tablosu |
| [ui-tablefactories_assets_all.bundle](file:///C:/Program%20Files%20(x86)/Steam/steamapps/common/Football%20Manager%2026/fm_Data/StreamingAssets/aa/StandaloneWindows64/ui-tablefactories_assets_all.bundle) | `SpecificallyScoutedPersonTableFactory` (`Obj 92`) | PathID `-2280246386909779364`, GUID `399c0aa9357f67847b91ba2fe4756083` | Gözlemci Öncelikleri tablosunun sütun tanımları ve `m_sortBinding` yolları |
| [ui-tablefactories_assets_all.bundle](file:///C:/Program%20Files%20(x86)/Steam/steamapps/common/Football%20Manager%2026/fm_Data/StreamingAssets/aa/StandaloneWindows64/ui-tablefactories_assets_all.bundle) | `PlayerTableFactory` (`Obj 31`) | PathID `-6813643292728705340`, GUID `49c25af415c53814d8d3ed658d867204` | Oyuncu Veritabanı / Takip Listesi sütun fabrikası |
| [ui-tableviews_assets_all.bundle](file:///C:/Program%20Files%20(x86)/Steam/steamapps/common/Football%20Manager%2026/fm_Data/StreamingAssets/aa/StandaloneWindows64/ui-tableviews_assets_all.bundle) | `ScoutPrioritiesTableViewCollection` (`Obj 236`) & `ScoutPrioritiesTable` (`Obj 766`) | GUID `13a1f18bd93e860488c2cb84abb1168c` / PathID `6820118260298404215` | Geniş tablo görünümü sütun listesi |
| [ui-tableviews_assets_all.bundle](file:///C:/Program%20Files%20(x86)/Steam/steamapps/common/Football%20Manager%2026/fm_Data/StreamingAssets/aa/StandaloneWindows64/ui-tableviews_assets_all.bundle) | `ScoutPrioritiesTableViewCollection-Small` (`Obj 400`) & `ScoutPrioritiesTable-Small` (`Obj 791`) | GUID `c1a44f7eaa1698a43ab7664b7ce350da` / PathID `7446456543218343850` | Dar tablo görünümü sütun listesi |

---

## 2. Çözümlenen UXML ve Tablo Yapıları

### 2.1. `ScoutPrioritiesBlock` (`Obj 229`) `StreamedTable/UxmlSerializedData` Yapısı
- **`uxmlAssetId`**: `1922429255` (Veri ofseti: `+0x1328`)
- **`FixedElementSize`**: `47.0`
- **`Reorderable`**: `1` (`true`)
- **`SelectionMode`**: `3` (`Obj 263` içinde `1`)
- **`Binding`**: `Team.ScoutPriorities.SpecificallyScoutedPlayers`
- **`SelectedItemsBinding`**: `team.scoutpriorities.selectedplayers`
- **`DragEvents`**: `Team.ScoutPriorities.itemmoved`
- **`DragCellID`**: `drag-column`
- **`HeaderCellAsset`**: `f45d19f7c2614ae4782f06ccd001fbb1`
- **`FactoryAsset`**: `399c0aa9357f67847b91ba2fe4756083` (`SpecificallyScoutedPersonTableFactory`)
- **`InitFunction`**: `StreamedTable_CreateColumnsFromTableViewCollection` (`f93b92def36a8474fa5798233a6a3fb8`), argümanlar: `13a1f18bd93e860488c2cb84abb1168c` (`ScoutPrioritiesTableViewCollection`) ve `selectedView`.

### 2.2. `SpecificallyScoutedPersonTableFactory` (`Obj 92`) Sütun ve Sıralama Bağlantıları (`m_sortBinding`)
Bu fabrikada toplam **10 sütun** tanımlıdır ve sıralanabilir 9 sütunun tamamı `SpecificallyScoutedPerson` nesnesi altındaki alt nesnelere (`player.*` veya `Scout.*`) işaret eden **çok katmanlı (multi-depth >= 2)** yollardır:

| Sütun ID (`m_columnID`) | `m_sortBinding` | Derinlik (`Depth`) | `m_sortingDisabled` |
|---|---|---|---|
| `player-nationality` | `binding.player.name` | 2 | `0` |
| `club-division` | `binding.player.division.name` | 3 | `0` |
| `position` | `binding.player.positioncombined` | 2 | `0` |
| `recommendation` | `binding.player.ClubRecruitmentReport.OverallReportGradeInfo.Grade` | 4 | `0` |
| `staff` | `binding.Scout.Name` | 2 | `0` |
| `assignment-type` | `binding.player.name` | 2 | `0` |
| `value` | `binding.player.transfervaluerange.SortValue` | 3 | `0` |
| `age` | `binding.player.age` | 2 | `0` |
| `inf` | `binding.player.playerstatus` | 2 | `0` |
| `drag-column` | *(boş)* | 0 | `0` |

### 2.3. Oyuncu Veritabanı (`PlayerSearchTable` / `Shortlist`) ile Temel Farkı
- **Oyuncu Veritabanı ve Takip Listesi (Shortlist):**
  - Sunucu/C++ tarafında çalışan `QueryableDataCollection` (`personsearch.FilteredRowIndexTable` + `personsearch.ApplySortRuleData`) kullanır; `ServerSortBinding` ve `AsynchronousScrolling: 1` aktiftir.
- **Gözlemci Öncelikleri (`ScoutPrioritiesBlock`):**
  - `ServerSortBinding` yoktur; doğrudan `Team.ScoutPriorities.SpecificallyScoutedPlayers` listesine bağlıdır ve **istemci taraflı (client-side) `StreamedListView` sıralama mekanizmasını** kullanır.

---

## 3. `GameAssembly.dll` (IL2CPP) İçinde Çözümlenen Sınıflar ve Fonksiyon RVA Haritası

Hedef ikili dosya: [GameAssembly.dll](file:///C:/Program%20Files%20(x86)/Steam/steamapps/common/Football%20Manager%2026/GameAssembly.dll) ve [global-metadata.dat](file:///C:/Program%20Files%20(x86)/Steam/steamapps/common/Football%20Manager%2026/fm_Data/il2cpp_data/Metadata/global-metadata.dat).

### 3.1. `SI.Bindable.StreamedTable` ve `Header` Metodları
- `StreamedTable.CreateHeader`: `0x015e8f00`
- `StreamedTable.MakeColumnHeader`: `0x015eac30` (`<>c__DisplayClass214_0.<MakeColumnHeader>b__0`: `0x0160bb80`)
- `StreamedTable.BindHeader`: `0x015e6230`
- `StreamedTable.BindToDataInternal`: `0x015e6d70`
- `StreamedTable.RebuildInternal`: `0x015ee9c0`
- `StreamedTable.OnBindItem`: `0x015eb760` (`<OnBindItem>g__SetBindings|221_0`: `0x015f0580`)
- `StreamedTable.OnRebindItem`: `0x015ed7d0`
- `StreamedTable.OnHeaderClicked`: `0x015ec910`
- `StreamedTable.SetSorting(string, bool, bool)`: `0x015efc40`
- `StreamedTable.SetSorting(List<ColumnSortData>, bool)`: `0x015efce0`
- `StreamedTable.TrySetColumnsAndSort`: `0x015f0040`
- `StreamedTable.UpdateSortColum`: `0x015f1380`
- `StreamedTable.get_DisableSorting` / `set_DisableSorting`: `0x015f2190` / `0x015f2420` (Alan ofseti: `this + 0x9b8`)
- `StreamedTable.UxmlSerializedData.Deserialize`: `0x015f36b0`
- `Header..ctor`: `0x015dfab0` (`<>c__DisplayClass36_0.<.ctor>b__0`: `0x015f2ea0`)
- `Header.Bind`: `0x015df4f0`
- `Header.OnBindingChanged`: `0x015df600`
- `Header.SetupClickHandler`: `0x015df7e0`
- `Header.UpdateSortingIcons` / `ResetSortingIcons`: `0x015df970` / `0x015df720`

### 3.2. `SI.Bindable.StreamedListView` ve Sıralama (`SortData` / `SortComparer`) Metodları
- `StreamedListView.SetSortingBinding(BindingPath, SortOrder)`: `0x015a9a80`
- `StreamedListView.SetSortingBinding(List<ColumnSortData>)`: `0x015a9ae0`
- `StreamedListView.ApplySorting`: `0x015a4260`
- `StreamedListView.<ApplySorting>g__SetupRow|246_0`: `0x015aa320`
- `StreamedListView.BindSortPathNextDepth`: `0x015a4850`
- `StreamedListView.ProcessSortingDataChanged`: `0x015a8cb0`
- `StreamedListView.OnSortingDataChanged`: `0x015a7ff0`
- `StreamedListView.PostSortingDataChanged`: `0x015a8610`
- `StreamedListView.RefreshInternal`: `0x015a9060`
- `StreamedListView.GetItemFromView`: `0x015a5a10`
- `StreamedListView.UxmlSerializedData.Deserialize`: `0x015b0b50` (`m_reorderable` ofseti: `this + 0x68c`)
- `SortData.Clear`: `0x015a3f90`
- `SortData.HasReceived`: `0x015a4040`
- `SortComparer.Compare(int, int)`: `0x015a3c60`
- `SortComparer.Compare(Data, Data)`: `0x015a3d30`

### 3.3. `SI.Bindable.Bindings` ve `Node` Metodları
- `Bindings.Bind(Key, Key, ...)`: `0x014bee30` / `0x014beef0`
- `Bindings.Create`: `0x014bf980`
- `Bindings.GetNthProperty`: `0x014c1450`
- `Bindings.MarkChildrenDirtyRecursive`: `0x014c22e0`
- `Bindings.MarkNodeDirty`: `0x014c2350`
- `Bindings.SetAlias`: `0x014c3050`
- `Bindings.SetInternal`: `0x014c3770`
- `Bindings.SetTargetData`: `0x014c5350`
- `Bindings.Unbind`: `0x014c63d0`
- `Bindings.UpdateNodeDataTarget`: `0x014c6590`
- `Node.AddCallback`: `0x014d0b50`
- `Node.NotifyDataChanged`: `0x014d0ca0`

### 3.4. ViewModel Referans Sınıfları (`FM.UI`)
- `FM.UI.ScoutPlayerPrioritiesReference` (`Type #860`): `0x0067d270` (`AcceptsPropertyInternal`), `0x0067d310` (`GetInstance`), `0x0067d360` (`GetPropertiesInternal`), `0x0067d500` (`GetPropertyTypeInternal`)
- `FM.UI.ScoutTeamPrioritiesReference` (`Type #861`): `0x0067d660` .. `0x0067dc00`
- `FM.UI.SpecificallyScoutedPersonReference` (`Type #909`): `0x00696ef0` (`AcceptsPropertyInternal`), `0x00696f80` (`GetPropertiesInternal`), `0x00697200` (`GetPropertyTypeInternal`)
- `FM.UI.SpecificallyScoutedTeamReference` (`Type #910`): `0x00697380` .. `0x00697770`

---

## 4. Saklanan Çözümleme Betikleri (Scratch Dizini)

Tüm analiz ve tersine mühendislik betikleri `C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch\` dizininde saklanmaktadır:
- [check_deep_sorting.py](file:///C:/Users/mcaka/.gemini/antigravity/brain/f3fe4be7-d8a5-4ec7-895a-ec06f09f2529/scratch/check_deep_sorting.py): PE/IL2CPP metadata okuyucu, modül-metod RVA haritalayıcı (`rva_to_method_name`) ve çağrı hedeflerini otomatik etiketleyen disassembler (`dump_func_details`).
- [dump_table_bind_and_header.py](file:///C:/Users/mcaka/.gemini/antigravity/brain/f3fe4be7-d8a5-4ec7-895a-ec06f09f2529/scratch/dump_table_bind_and_header.py): `StreamedTable.BindHeader`, `BindToDataInternal`, `RebuildInternal` ve `Header` metodlarını çözümleyen betik.
- [dump_onbinditem_and_types.py](file:///C:/Users/mcaka/.gemini/antigravity/brain/f3fe4be7-d8a5-4ec7-895a-ec06f09f2529/scratch/dump_onbinditem_and_types.py): `StreamedTable.OnBindItem`, `<OnBindItem>g__SetBindings|221_0` ve `OnRebindItem` çözümleyici.
- [dump_bindings_and_deserialize.py](file:///C:/Users/mcaka/.gemini/antigravity/brain/f3fe4be7-d8a5-4ec7-895a-ec06f09f2529/scratch/dump_bindings_and_deserialize.py) & [dump_streamedtable_deserialize.py](file:///C:/Users/mcaka/.gemini/antigravity/brain/f3fe4be7-d8a5-4ec7-895a-ec06f09f2529/scratch/dump_streamedtable_deserialize.py): `Bindings.SetTargetData`, `MarkNodeDirty`, `MarkChildrenDirtyRecursive` ve `StreamedTable`/`StreamedListView` UXML `Deserialize` metodlarını çözümleyen betikler.
- [find_scout_priorities_vm.py](file:///C:/Users/mcaka/.gemini/antigravity/brain/f3fe4be7-d8a5-4ec7-895a-ec06f09f2529/scratch/find_scout_priorities_vm.py) & [dump_specifically_scouted_ref.py](file:///C:/Users/mcaka/.gemini/antigravity/brain/f3fe4be7-d8a5-4ec7-895a-ec06f09f2529/scratch/dump_specifically_scouted_ref.py): `ScoutPlayerPrioritiesReference` ve `SpecificallyScoutedPersonReference` sınıflarını çözümleyen betikler.
