# FM27 Obje Modeli (otomatik üretilmiş yapı özeti)

> Bu dosya `fm-toolkit decompile-binaries --mode report` ile, yerelde üretilmiş (git'e girmeyen) `decompile-binaries --mode dump` çıktısından **otomatik** üretilir. Elle düzenlemeyin; yeniden üretin.
> Yalnızca **yapı bilgisi** içerir (sınıf/varlık adları, FourCC kimlikleri, kalıtım, sayılar, ilişkiler). Metod imzaları, alan listeleri ve kod yer almaz. Ayrıntı için: [DECOMPILED_ENGINE_REHBERI_TR.md](../DECOMPILED_ENGINE_REHBERI_TR.md).

## 1. Kaynak

| | |
|---|---|
| Oyun | **FM27** |
| Üretim zamanı | 2026-11-07T11:37:09 |
| `GameAssembly.dll` | 59,361,792 bayt, 2026-11-02T21:53:42, SHA1 `9f6b0560688d8428b55465c20f55b20789f33275` |
| `global-metadata.dat` | 15,680,796 bayt, SHA1 `c691a95bf7d45da3696773766f3f46f2c47ba8ce` |

## 2. Genel sayılar

| Öğe | Adet |
|---|---:|
| Assembly (image) | 143 |
| Tip (TypeDefinition) | 20,004 |
| Enum | 2,059 |
| Alan | 91,115 |
| Metod | 142,649 |
| C# property | 28,961 |
| Parametre | 136,675 |
| String literal | 32,034 |
| Kayıtlı binding property (FourCC) | 9,126 |
| Kayıtlı binding context (FourCC) | 233 |
| `*Reference` varlık sınıfı | 992 |
| Çekirdek DB tablosu varlığı (`0x4442xxxx`) | 19 |
| `il2cpp.usym` sembol kaydı | 3,600,816 |
| `il2cpp.usym` RVA-eşlenmiş C# metodu | 121,695 |
| `il2cpp.usym` kaynak dosya yolu | 6,186 |
| `game_plugin.dll` native export | 282 |
| `game_plugin.dll` `.pdata` C++ fonksiyonu | 139,131 (74,518,907 bayt) |
| `game_plugin.dll` `ActionContributor` vtable sınıfı | 224 |
| `game_plugin.dll` `SearchFilter` vtable sınıfı | 58 |
| `non_pl_hist_dt.dat` personel kariyer geçmişi satırı (24B) | 3,527,045 |
| `summary.dat` kulüp özet kaydı (25B) | 96,171 |
| UI `TableFactory` sınıfı (`ui-tablefactories`) | 220 |
| UI `TableFactory` sütun `binding.*` yolu | 2,102 |
| UI `TableView` / `TableSettings` şablonu (`ui-tableviews`) | 592 |
| Kurulumdaki toplam dosya sayısı (`100%` kapsama) | 1,283 (9,225,428,268 bayt) |
| Tüm UnityFS `.bundle` arşivleri (24 kategori) | 534 (764 CAB düğümü) |
| `sianim/*.cat` 3B maç animasyon klibi (`CAT\x00`) | 5,932 (557,440 iz) |
| `sianim/*.amd` Motion Matching segmenti | 5,500 (165,699 kare) |
| `fm_Data/manifest.dat` doğrulama kaydı (MD5) | 1,239 |
| Unity `SerializedFile v22` nesnesi (`fm_Data/*`) | 8,498 |
| Native PE64 ikili dosyası (`EXE`/`DLL`) | 17 (533,123 `.pdata` fonksiyonu) |

## 3. FM / SI assembly'leri

| Assembly | Tip | class | struct | enum | Alan | Metod | Property |
|---|---:|---:|---:|---:|---:|---:|---:|
| `FM.UI.dll` | 2,697 | 2,465 | 85 | 147 | 11,071 | 25,542 | 4,767 |
| `SI.Bindable.dll` | 1,137 | 964 | 99 | 74 | 7,059 | 11,000 | 3,451 |
| `FM.Graphics.dll` | 522 | 392 | 66 | 64 | 3,591 | 3,497 | 1,042 |
| `FM.Match.dll` | 473 | 409 | 32 | 32 | 2,404 | 3,177 | 648 |
| `SI.Core.dll` | 449 | 330 | 83 | 36 | 1,132 | 2,400 | 400 |
| `SI.UI.dll` | 445 | 327 | 71 | 47 | 1,681 | 3,129 | 665 |
| `SI.VisualScripting.dll` | 234 | 224 | 5 | 5 | 1,260 | 2,399 | 1,180 |
| `SI.CityGen.dll` | 146 | 107 | 36 | 3 | 599 | 834 | 308 |
| `FM.GamePlugin.dll` | 138 | 124 | 9 | 5 | 1,350 | 814 | 24 |
| `SI.Match.dll` | 71 | 5 | 32 | 34 | 782 | 84 | 0 |
| `FMGame.dll` | 70 | 59 | 8 | 3 | 263 | 255 | 22 |
| `SI.Anim.dll` | 39 | 29 | 4 | 6 | 143 | 224 | 31 |
| `SI.Audio.dll` | 31 | 21 | 8 | 2 | 93 | 173 | 44 |
| `FM.Graphics.Tools.dll` | 28 | 28 | 0 | 0 | 122 | 87 | 14 |
| `FM.Input.dll` | 24 | 24 | 0 | 0 | 95 | 154 | 13 |
| `SI.Bindable.Reference.Core.dll` | 22 | 16 | 4 | 2 | 35 | 119 | 22 |
| `FM.Lattice.dll` | 21 | 19 | 2 | 0 | 45 | 110 | 20 |
| `FM.GameSimulation.dll` | 21 | 17 | 1 | 3 | 89 | 155 | 50 |
| `SI.UnityBuildVerification.dll` | 20 | 18 | 0 | 2 | 97 | 75 | 14 |
| `SI.Marshalling.dll` | 19 | 12 | 6 | 1 | 35 | 57 | 9 |
| `SI.Input.dll` | 17 | 9 | 4 | 4 | 129 | 170 | 25 |
| `SI.Services.dll` | 14 | 12 | 2 | 0 | 24 | 43 | 12 |
| `SI.Lattice.dll` | 13 | 12 | 1 | 0 | 12 | 61 | 3 |
| `SI.Addressables.dll` | 13 | 11 | 2 | 0 | 21 | 38 | 4 |
| `SI.Interop.dll` | 9 | 8 | 1 | 0 | 9 | 46 | 5 |
| `SI.Playerloop.dll` | 8 | 8 | 0 | 0 | 8 | 9 | 0 |
| `Assembly-CSharp.dll` | 8 | 8 | 0 | 0 | 8 | 13 | 0 |
| `SI.Debug.dll` | 8 | 3 | 5 | 0 | 20 | 0 | 0 |
| `SI.Data.dll` | 7 | 5 | 2 | 0 | 23 | 48 | 10 |
| `FM.Performance.dll` | 6 | 5 | 1 | 0 | 6 | 4 | 0 |
| `SceneLoadTest.dll` | 5 | 5 | 0 | 0 | 3 | 4 | 0 |
| `FM.GameConfig.dll` | 4 | 4 | 0 | 0 | 3 | 3 | 0 |
| `SI.MatchDevUI.dll` | 3 | 3 | 0 | 0 | 0 | 0 | 0 |
| `SI.MatchTypes.dll` | 2 | 1 | 0 | 1 | 1,238 | 0 | 0 |
| `SI.VisualScripting.Core.dll` | 2 | 2 | 0 | 0 | 2 | 3 | 2 |

## 4. Çekirdek veritabanı tablosu varlıkları (`0x4442xxxx` = `"DB\0\xNN"`)

Oyun veritabanının ana tabloları UI/binding katmanında bu `*Reference` sınıflarıyla temsil edilir. `Çocuk varlıklar`: bu varlığın property'lerinin döndürdüğü diğer varlık tipleri.

| # | Sınıf | Kimlik | Türediği | Property | Parametreli | Context | Çocuk varlıklar |
|---:|---|---|---|---:|---:|---:|---|
| 0 | `AwardReference` | `0x44420000` | – | 14 | 0 | 1 | `AwardVoteReference`, `AwardHistoryItemReference` |
| 1 | `PersonReference` | `0x44420001` | `INonPlayerReference`, `IJournalistReference`, `IPlayerReference`, `IPersonBaseReference`, `IAgentReference`, `IOfficialReference` | 1,287 | 551 | 74 | `ValueCountReference`, `DisplayValuePairReference`, `HireIntermediaryReference`, `PlayerReportReference`, `NewsItemReference`, `LastFiveMatchesFormReference`, `PlayerFormReference`, `MatchFormReference`, `SpeakToReference`, `SupportersFeedbackReference`, `TransferWindowReference`, `FixtureReference` … (+91) |
| 2 | `CityReference` | `0x44420002` | – | 1 | 0 | 0 | – |
| 3 | `ClubReference` | `0x44420003` | `ITeamContainerReference`, `IClubFinanceOverviewReference` | 516 | 122 | 30 | `TeamContainerHonoursReference`, `CompletedTransferReference`, `ValueCountReference`, `StaffMeetingReference`, `DisplayValuePairReference`, `RankedYouthCandidatesReference`, `NewsActionDataReference`, `TeamSettingsEditSessionReference`, `ReputationInfoReference`, `VisionFfpObjectivesDataReference`, `DebugManagerBackingReference`, `FacilityRatingReference` … (+43) |
| 5 | `ContinentReference` | `0x44420005` | – | 61 | 24 | 8 | `AwardReference`, `PersonReference`, `LazyMenuReference` |
| 7 | `MediaSourceReference` | `0x44420007` | – | 1 | 0 | 0 | – |
| 8 | `LanguageReference` | `0x44420008` | – | 1 | 0 | 0 | – |
| 9 | `NationalTeamContainerReference` | `0x44420009` | `ITeamContainerReference` | 134 | 30 | 9 | `TeamReference` |
| 10 | `NationReference` | `0x4442000a` | – | 60 | 17 | 10 | `LazyMenuReference`, `TransferListDateSelectorItemReference`, `DisplayValuePairReference`, `TransferInOutReference`, `AwardReference`, `CompReference`, `ClubReference` |
| 18 | `DerbyReference` | `0x44420012` | – | 0 | 0 | 0 | – |
| 19 | `RegionReference` | `0x44420013` | – | 1 | 0 | 0 | – |
| 21 | `StadiumReference` | `0x44420015` | – | 22 | 0 | 1 | – |
| 23 | `StageNameReference` | `0x44420017` | – | 0 | 0 | 0 | – |
| 24 | `TeamReference` | `0x44420018` | – | 478 | 150 | 39 | `PlayerStatValuePairReference`, `TeamReportAssistDataReference`, `TeamFixtureReference`, `SpeakToReference`, `NationalSquadSelectionEditSessionReference`, `FactTypeDataReference`, `LastMatchAnalysisVisualsReference`, `TacticalEffectivenessTopPositionRowReference`, `StarRangeReference`, `CompReference`, `DisplayValuePairReference`, `ScoutPlayerPrioritiesReference` … (+56) |
| 25 | `CompReference` | `0x44420019` | – | 308 | 96 | 24 | `AwardReference` |
| 28 | `RemovedRecordReference` | `0x4442001c` | – | 1 | 0 | 0 | – |
| 47 | `LocalRegionReference` | `0x4442002f` | – | 1 | 0 | 0 | – |
| 56 | `AgreementReference` | `0x44420038` | – | 3 | 0 | 0 | `NationReference` |
| 57 | `FixtureNameReference` | `0x44420039` | – | 1 | 0 | 1 | – |

## 5. `*Reference` varlık sınıfı dizini

Her satır, UI'nin bağlanabildiği (binding) bir varlık tipidir. `Kimlik` = `get_ID` döndürdüğü 32-bit FourCC. Assembly dağılımı: `FM.UI.dll` 972, `SI.Bindable.dll` 18, `FM.Input.dll` 1, `FM.Lattice.dll` 1.

| Sınıf | Kimlik | Türediği | Property | Çocuk varlık |
|---|---|---|---:|---:|
| `ActionButtonReference` | `0x77363052` (`w60R`) | – | 14 | 1 |
| `ActionPotentialUnhappinessWarningReference` | `0x5238494d` (`R8IM`) | – | 7 | 1 |
| `ActionReference` | `0x61637469` (`acti`) | – | 1 | 0 |
| `ActionZonesMapChartPointDataReference` | `0x596d3420` (`Ym4 `) | – | 1 | 0 |
| `ActionZonesVisualisationReference` | `0x4c387342` (`L8sB`) | – | 4 | 1 |
| `ActionZonesVisualisationTeamDataReference` | `0x6b477170` (`kGqp`) | – | 4 | 0 |
| `ActiveBanReference` | `0x536c6c46` (`SllF`) | – | 11 | 0 |
| `ActiveTradeInfoReference` | `0x69584c33` (`iXL3`) | – | 3 | 1 |
| `AddOnReference` | `0x6f6f6f59` (`oooY`) | `SaveGameReference` | 4 | 0 |
| `AddUserEditSessionReference` | `0x6164646d` (`addm`) | – | 38 | 0 |
| `AdjustSeasonExpectationsReference` | `0x2064384b` (` d8K`) | – | 5 | 0 |
| `AdvancedContinentSelectionReference` | `0x6a79724d` (`jyrM`) | – | 3 | 0 |
| `AffiliateEditSessionReference` | `0x744f7052` (`tOpR`) | – | 4 | 0 |
| `AgentFeedbackReference` | `0x41674652` (`AgFR`) | – | 6 | 0 |
| `AgentPlayerDemandsReference` | `0x6f356967` (`o5ig`) | – | 6 | 1 |
| `AgentPlayerDemandsStringDataReference` | `0x70503273` (`pP2s`) | – | 5 | 0 |
| `AgreementReference` | `0x44420038` | – | 3 | 1 |
| `AllStarInjuryReplacementNewsReference` | `0x76725143` (`vrQC`) | – | 3 | 2 |
| `AllStarMatchSquadNewsReference` | `0x57674e32` (`WgN2`) | – | 3 | 2 |
| `AllTimeBestXIReference` | `0x30385242` (`08RB`) | – | 5 | 0 |
| `AnsweredPivotalMomentReference` | `0x30346320` (`04c `) | – | 13 | 1 |
| `ApplicationReference` | `0x61707020` (`app `) | – | 73 | 0 |
| `ArrangeFriendlyReference` | `0x30714752` (`0qGR`) | – | 18 | 1 |
| `ArrangePreTournamentFriendlyNewsReference` | `0x355a596c` (`5ZYl`) | – | 4 | 0 |
| `AssistLocationPitchReference` | `0x77574356` (`wWCV`) | – | 5 | 0 |
| `AttributeChangeReference` | `0x4f754256` (`OuBV`) | – | 3 | 0 |
| `AttributeNameAndValueReference` | `0x7379426a` (`syBj`) | – | 2 | 0 |
| `AttributeValueReference` | `0x41544a53` (`ATJS`) | – | 5 | 0 |
| `AveragePointsTableInformationReference` | `0x4b4d706f` (`KMpo`) | – | 4 | 1 |
| `AveragePointsTableRowReference` | `0x35474667` (`5GFg`) | – | 16 | 1 |
| `AveragePositionMapReference` | `0x6558344f` (`eX4O`) | – | 5 | 2 |
| `AveragePositionPlayerDataReference` | `0x47464145` (`GFAE`) | – | 5 | 0 |
| `AwardHistoryItemReference` | `0x7a533174` (`zS1t`) | – | 5 | 0 |
| `AwardReference` | `0x44420000` | – | 14 | 2 |
| `AwardVoteReference` | `0x64535042` (`dSPB`) | – | 3 | 0 |
| `BackroomChatDataReference` | `0x42343963` (`B49c`) | – | 3 | 2 |
| `BanCoverageReference` | `0x536c6c49` (`SllI`) | – | 6 | 0 |
| `BestGoalAwardHistoryReference` | `0x35744b70` (`5tKp`) | – | 5 | 0 |
| `BestTeamAwardWinnerReference` | `0x566f3147` (`Vo1G`) | – | 7 | 0 |
| `BestXIOverviewReference` | `0x4a793762` (`Jy7b`) | – | 5 | 1 |
| `BestXIPositionReference` | `0x41344738` (`A4G8`) | – | 5 | 1 |
| `BestXISquadPositionReference` | `0x316a4d78` (`1jMx`) | – | 2 | 0 |
| `BoardRequestReference` | `0x204c7043` (` LpC`) | – | 5 | 0 |
| `BoardTacticsFeedbackReference` | `0x456b317a` (`Ek1z`) | – | 2 | 0 |
| `BuyOrSellImmediatelyReference` | `0x36736138` (`6sa8`) | – | 5 | 0 |
| `CalendarDayReference` | `0x7666494b` (`vfIK`) | – | 10 | 0 |
| `CalendarEventReference` | `0x4f727356` (`OrsV`) | – | 33 | 0 |
| `CalendarReference` | `0x5041486c` (`PAHl`) | `ITrainingSelectorReference` | 41 | 2 |
| `CalendarWeekReference` | `0x32727532` (`2ru2`) | – | 20 | 1 |
| `CaptainStandInCandidateReference` | `0x4e443068` (`ND0h`) | – | 3 | 1 |
| `CareerMilestoneClubReference` | `0x636d6c5f` (`cml_`) | – | 6 | 1 |
| `CareerMilestoneReference` | `0x636d6c73` (`cmls`) | – | 8 | 0 |
| `CareerMilestoneSummaryReference` | `0x636d6c60` (`cml``) | – | 12 | 1 |
| `CareerMilestoneTypeCountSummaryReference` | `0x66374544` (`f7ED`) | – | 2 | 0 |
| `CareerMilestoneYearReference` | `0x636d6c59` (`cmlY`) | – | 2 | 0 |
| `CareerMilestonesReference` | `0x3256562d` (`2VV-`) | – | 3 | 0 |
| `CareerStatsFullReference` | `0x4742706e` (`GBpn`) | – | 5 | 0 |
| `CareerStatsReference` | `0x5a554f45` (`ZUOE`) | – | 21 | 1 |
| `CashSelectionReference` | `0x35324543` (`52EC`) | – | 4 | 1 |
| `ChangedPlayingTimeReference` | `0x4767324b` (`Gg2K`) | – | 4 | 0 |
| `CharacterSettingsReference` | `0x4279734c` (`BysL`) | `V0fC` | 169 | 0 |
| `CheckBoxFilterRuleReference` | `0x43684672` (`ChFr`) | – | 2 | 0 |
| `CityReference` | `0x44420002` | – | 1 | 0 |
| `ClubBudgetAdjustmentReference` | `0x4f515354` (`OQST`) | – | 13 | 1 |
| `ClubCoefficientReference` | `0x63636f72` (`ccor`) | – | 13 | 0 |
| `ClubCollectiveWinBonusAmountReference` | `0x35414d51` (`5AMQ`) | – | 5 | 0 |
| `ClubCollectiveWinBonusReference` | `0x4a6e4c70` (`JnLp`) | – | 8 | 0 |
| `ClubContractCompetitionBonusActivatedReference` | `0x4f577042` (`OWpB`) | – | 4 | 0 |
| `ClubDraftAllocationsReference` | `0x314b6459` (`1KdY`) | – | 4 | 0 |
| `ClubEligibilityReference` | `0x6e636574` (`ncet`) | – | 6 | 1 |
| `ClubFavouredPersonReference` | `0x34445259` (`4DRY`) | – | 2 | 1 |
| `ClubNationKnowledgeReference` | `0x4163584e` (`AcXN`) | – | 6 | 0 |
| `ClubPlayingTimesForUpcomingSeasonReference` | `0x72743566` (`rt5f`) | – | 2 | 0 |
| `ClubRatedDebugStringReference` | `0x44653863` (`De8c`) | – | 3 | 2 |
| `ClubReference` | `0x44420003` | `ITeamContainerReference`, `IClubFinanceOverviewReference` | 516 | 55 |
| `ClubRegionKnowledgeReference` | `0x66386a78` (`f8jx`) | – | 3 | 0 |
| `ClubSeasonExpectationsCompetitionPossibleOptionReference` | `0x37797730` (`7yw0`) | – | 2 | 1 |
| `ClubSeasonExpectationsCompetitionReference` | `0x576e4b49` (`WnKI`) | – | 8 | 1 |
| `ClubSeasonSummaryCompRowReference` | `0x5a417a67` (`ZAzg`) | – | 5 | 1 |
| `ClubSeasonSummaryPlayerRowReference` | `0x62456f48` (`bEoH`) | – | 3 | 1 |
| `ClubSingleDraftAllocationsReference` | `0x4d37586e` (`M7Xn`) | – | 2 | 0 |
| `ClubSponsorshipIncomeReference` | `0x304f7065` (`0Ope`) | – | 3 | 1 |
| `ClubTransferClausesItemReference` | `0x54385775` (`T8Wu`) | – | 19 | 0 |
| `ClubTransferClausesPersonReference` | `0x42456a7a` (`BEjz`) | – | 5 | 1 |
| `ClubTransferClausesReference` | `0x35547455` (`5TtU`) | – | 12 | 1 |
| `ClubVisionMeetingCurrentObjectiveReference` | `0x6d654278` (`meBx`) | – | 8 | 0 |
| `ClubVisionMeetingEditSessionReference` | `0x6d327254` (`m2rT`) | – | 14 | 1 |
| `ClubVisionMeetingSeasonExpectationsReference` | `0x54484964` (`THId`) | – | 6 | 1 |
| `ClubVisionObjectiveDebugReference` | `0x41733331` (`As31`) | – | 14 | 0 |
| `ClubVisionObjectiveReference` | `0x63766f72` (`cvor`) | – | 12 | 1 |
| `CoachAssignmentReference` | `0x5966414c` (`YfAL`) | – | 10 | 0 |
| `CoachAssignmentsReference` | `0x4a663853` (`Jf8S`) | – | 11 | 0 |
| `CoachCategoryAssignmentReference` | `0x6c58384e` (`lX8N`) | – | 4 | 1 |
| `CoachingStyleOptionReference` | `0x68728002` | – | 3 | 0 |
| `CodeOfConductFineListReference` | `0x39434d6a` (`9CMj`) | – | 5 | 1 |
| `CodeOfConductFineReference` | `0x4e513767` (`NQ7g`) | – | 7 | 0 |
| `CodeOfConductReference` | `0x564b7a6b` (`VKzk`) | – | 6 | 0 |
| `ColourSwatchReference` | `0x6c513036` (`lQ06`) | – | 5 | 0 |
| `CommercialMerchandiseDataReference` | `0x53395547` (`S9UG`) | – | 4 | 1 |
| `CompAndFixturesReference` | `0x39454967` (`9EIg`) | – | 2 | 1 |
| `CompBestPlayerReference` | `0x446a3976` (`Dj9v`) | – | 8 | 0 |
| `CompDebugAverageSquadMakeUpReference` | `0x664a3047` (`fJ0G`) | – | 14 | 0 |
| `CompDebugCompetitionTransfersReference` | `0x63656662` (`cefb`) | – | 2 | 0 |
| `CompDebugContractClauseFrequencyReference` | `0x314a3778` (`1J7x`) | – | 3 | 0 |
| `CompDebugContractIncludingClauseReference` | `0x75494d77` (`uIMw`) | – | 6 | 0 |
| `CompDebugFinanceBudgetReference` | `0x6d4e4b66` (`mNKf`) | – | 8 | 1 |
| `CompDebugFinanceExpenditureReference` | `0x356b4f69` (`5kOi`) | – | 22 | 1 |
| `CompDebugFinanceIncomeReference` | `0x796d4a79` (`ymJy`) | – | 18 | 1 |
| `CompDebugFinanceStaffWageRangeReference` | `0x75482045` (`uH E`) | – | 5 | 1 |
| `CompDebugFinanceTicketDataReference` | `0x7a395242` (`z9RB`) | – | 9 | 1 |
| `CompDebugFinanceTotalsReference` | `0x704c4772` (`pLGr`) | – | 10 | 1 |
| `CompDebugIndividualSquadMakeUpReference` | `0x71724145` (`qrAE`) | – | 14 | 1 |
| `CompDebugInjuryReference` | `0x636a495a` (`cjIZ`) | – | 11 | 0 |
| `CompDebugManagersReference` | `0x414c5442` (`ALTB`) | – | 1 | 0 |
| `CompDebugNewSigningOffShortlistReference` | `0x46767377` (`Fvsw`) | – | 5 | 0 |
| `CompDebugNextMatchOddsReference` | `0x4d473742` (`MG7B`) | – | 14 | 1 |
| `CompDebugPitchConditionsReference` | `0x556d7378` (`Umsx`) | – | 5 | 1 |
| `CompDebugReleaseClausesReference` | `0x4b4b6a66` (`KKjf`) | – | 5 | 0 |
| `CompDebugSupportersProfileInfoReference` | `0x43645370` (`CdSp`) | – | 4 | 1 |
| `CompDebugTeamTransfersReference` | `0x4e6d7047` (`NmpG`) | – | 4 | 0 |
| `CompDebugTransferReference` | `0x6e6d6475` (`nmdu`) | – | 14 | 0 |
| `CompDebugTransferTotalsReference` | `0x72764176` (`rvAv`) | – | 22 | 1 |
| `CompLeaguePositionRulesReference` | `0x636c7072` (`clpr`) | – | 8 | 0 |
| `CompMenuReference` | `0x33573042` (`3W0B`) | – | 2 | 1 |
| `CompObjectLookupDataReference` | `0x4c6e4635` (`LnF5`) | – | 4 | 0 |
| `CompPlayerInjuryReference` | `0x66736e32` (`fsn2`) | – | 4 | 1 |
| `CompReference` | `0x44420019` | – | 308 | 1 |
| `CompSquadRewardsListEntryReference` | `0x78577247` (`xWrG`) | – | 5 | 1 |
| `CompSquadRewardsReference` | `0x5a565879` (`ZVXy`) | – | 3 | 0 |
| `CompStadiumCapacityReference` | `0x74446e71` (`tDnq`) | – | 3 | 1 |
| `CompStadiumReference` | `0x4755624d` (`GUbM`) | – | 4 | 0 |
| `CompStageMenuReference` | `0x63736d72` (`csmr`) | – | 2 | 1 |
| `CompTeamInjuriesListCountDataReference` | `0x37744436` (`7tD6`) | – | 3 | 0 |
| `CompTeamInjuriesReference` | `0x5254774c` (`RTwL`) | – | 3 | 1 |
| `CompTeamToDrawReference` | `0x65677933` (`egy3`) | – | 9 | 1 |
| `CompTreeCupTieReference` | `0x63746374` (`ctct`) | – | 17 | 0 |
| `CompTreeReference` | `0x43745374` (`CtSt`) | – | 2 | 0 |
| `CompTreeRoundReference` | `0x43747252` (`CtrR`) | – | 1 | 0 |
| `CompTreeRowReference` | `0x43745272` (`CtRr`) | – | 1 | 1 |
| `CompWithTotalPlacesReference` | `0x32644872` (`2dHr`) | – | 2 | 1 |
| `CompXGStatsListEntryReference` | `0x704e4653` (`pNFS`) | – | 7 | 0 |
| `CompXgStatReference` | `0x4c753239` (`Lu29`) | – | 3 | 0 |
| `CompetitionDetailLevelReference` | `0x43444c72` (`CDLr`) | – | 3 | 1 |
| `CompetitionHistoryReference` | `0x36416938` (`6Ai8`) | – | 10 | 1 |
| `CompetitionHonoursHistoryReference` | `0x57424f4c` (`WBOL`) | – | 2 | 1 |
| `CompetitionManagerRepReference` | `0x716f7163` (`qoqc`) | – | 3 | 2 |
| `CompetitionRecordsOverviewInfoReference` | `0x61735476` (`asTv`) | – | 4 | 0 |
| `CompetitionRecordsOverviewStatReference` | `0x36744961` (`6tIa`) | – | 3 | 0 |
| `CompetitionRecordsStatReference` | `0x59564470` (`YVDp`) | – | 2 | 0 |
| `CompetitionStageReference` | `0x636f5354` (`coST`) | – | 38 | 1 |
| `CompetitionStageWithStatsReference` | `0x544a5444` (`TJTD`) | – | 2 | 0 |
| `CompetitionStatsPlayerStatsListReference` | `0x6370736c` (`cpsl`) | – | 5 | 0 |
| `CompetitionStatsPlayerStatsReference` | `0x346e377a` (`4n7z`) | – | 10 | 0 |
| `CompetitionStatsTeamStatsListReference` | `0x4353544c` (`CSTL`) | – | 5 | 0 |
| `CompetitionStatsTeamStatsReference` | `0x6b6e506f` (`knPo`) | – | 9 | 0 |
| `CompetitionStatsTopPlayerReference` | `0x57486138` (`WHa8`) | – | 8 | 0 |
| `CompetitionStatsTopTeamReference` | `0x5078396e` (`Px9n`) | – | 7 | 0 |
| `CompetitionTacticReference` | `0x77725345` (`wrSE`) | – | 0 | 0 |
| `CompetitionTeamInjuryTableReference` | `0x5530336d` (`U03m`) | – | 4 | 1 |
| `CompetitionWinnerReference` | `0x4179494b` (`AyIK`) | – | 2 | 0 |
| `CompetititionFixtureGroupReference` | `0x63666772` (`cfgr`) | – | 4 | 0 |
| `CompletedTransferReference` | `0x66552044` (`fU D`) | – | 5 | 0 |
| `ConfigReference` | `0x000493e2` | – | 173 | 0 |
| `ConstReference` | `0x00000003` | – | 42 | 0 |
| `ContinentReference` | `0x44420005` | – | 61 | 3 |
| `ContinueReference` | `0x6b683673` (`kh6s`) | – | 10 | 0 |
| `ContractAddOnActivatedNewsReference` | `0x44744e4f` (`DtNO`) | – | 2 | 2 |
| `ContractAddOnListReference` | `0x485a3061` (`HZ0a`) | – | 2 | 0 |
| `ContractAddOnReference` | `0x65206243` (`e bC`) | – | 4 | 0 |
| `ContractClauseDataReference` | `0x5a72346b` (`Zr4k`) | – | 2 | 1 |
| `ContractCompetitionBonusesActivatedReference` | `0x79626947` (`ybiG`) | – | 2 | 0 |
| `ContractEditSessionAddOnComponentReference` | `0x6e4e4635` (`nNF5`) | – | 13 | 0 |
| `ContractEditSessionBaseComponentReference` | `0x3865534e` (`8eSN`) | – | 6 | 0 |
| `ContractEditSessionCashComponentReference` | `0x75494d46` (`uIMF`) | – | 4 | 0 |
| `ContractEditSessionCoreComponentReference` | `0x20705046` (` pPF`) | – | 3 | 1 |
| `ContractEditSessionReference` | `0x72e50527` | – | 112 | 1 |
| `ContractExpiresSoonReference` | `0x35585645` (`5XVE`) | – | 6 | 0 |
| `ContractNegotiationPatienceReference` | `0x37735449` (`7sTI`) | – | 2 | 0 |
| `ContractOfferScreenValidationReference` | `0x58644a6e` (`XdJn`) | – | 2 | 1 |
| `ContractReference` | `0x636f6e74` (`cont`) | – | 128 | 1 |
| `ContractTalksInterestedClubReference` | `0x6f764a74` (`ovJt`) | – | 2 | 1 |
| `ContractTalksNewsItemInfoReference` | `0x6c764864` (`lvHd`) | – | 13 | 0 |
| `ConversationDynamicCardDataPersonReference` | `0x61533433` (`aS43`) | – | 6 | 0 |
| `ConversationEditSessionReference` | `0x57493573` (`WI5s`) | – | 24 | 3 |
| `ConversationEditSessionSelectionDialogReference` | `0x78515762` (`xQWb`) | – | 5 | 0 |
| `ConversationSummaryPromiseReference` | `0x37303357` (`703W`) | – | 4 | 0 |
| `ConversationSummaryTargetReference` | `0x206f3732` (` o72`) | – | 4 | 1 |
| `CreatedClubReference` | `0x72427438` (`rBt8`) | – | 1 | 0 |
| `CupDrawGroupReference` | `0x4775e261` | – | 3 | 2 |
| `CupDrawTieReference` | `0x43523509` | – | 5 | 1 |
| `CupTieReference` | `0x43705469` (`CpTi`) | – | 16 | 0 |
| `CupTieTeamReference` | `0x63707474` (`cptt`) | – | 3 | 2 |
| `CurrentSuspensionsListEntryReference` | `0x5359714c` (`SYqL`) | – | 7 | 0 |
| `CurrentSuspensionsReference` | `0x50715053` (`PqPS`) | – | 3 | 0 |
| `CustomTrainingScheduleReference` | `0x766f7045` (`vopE`) | `ITrainingSelectorReference` | 25 | 4 |
| `DailyScheduleReference` | `0x64617363` (`dasc`) | – | 0 | 0 |
| `DataAnalysisPolygonTeamPlayerDataReference` | `0x7674504c` (`vtPL`) | – | 6 | 0 |
| `DataAnalysisSegmentReference` | `0x64456a4f` (`dEjO`) | – | 7 | 0 |
| `DataAnalystInfoReference` | `0x6e447545` (`nDuE`) | – | 4 | 1 |
| `DataHubVisualisationsReference` | `0x71377048` (`q7pH`) | – | 7 | 1 |
| `DataHubXgTableReference` | `0x4b46736b` (`KFsk`) | – | 2 | 2 |
| `DatabaseSelectionReference` | `0x73617552` (`sauR`) | – | 2 | 0 |
| `DatabaseVersionReference` | `0x64627672` (`dbvr`) | – | 3 | 0 |
| `DateSelectionReference` | `0x6d6c7166` (`mlqf`) | – | 7 | 0 |
| `DbSummaryCityReference` | `0x64636974` (`dcit`) | – | 2 | 0 |
| `DbSummaryClubReference` | `0x6473636c` (`dscl`) | – | 16 | 2 |
| `DbSummaryCompetitionReference` | `0x6473636d` (`dscm`) | – | 14 | 1 |
| `DbSummaryContinentReference` | `0x6473636e` (`dscn`) | – | 19 | 3 |
| `DbSummaryLanguageReference` | `0x646c616e` (`dlan`) | – | 1 | 0 |
| `DbSummaryNationReference` | `0x64736e74` (`dsnt`) | – | 36 | 2 |
| `DbSummaryPersonReference` | `0x64737072` (`dspr`) | – | 3 | 1 |
| `DbSummaryStadiumReference` | `0x64627374` (`dbst`) | – | 2 | 0 |
| `DebugBoardRequestReference` | `0x55766e73` (`Uvns`) | – | 11 | 0 |
| `DebugClubFinancesAnalysisItemReference` | `0x716c3935` (`ql95`) | – | 9 | 1 |
| `DebugClubFinancesAnalysisOverviewReference` | `0x70796e63` (`pync`) | – | 2 | 0 |
| `DebugClubPlayTimeChoiceReference` | `0x524f6520` (`ROe `) | – | 11 | 1 |
| `DebugClubPotentialAffiliateReference` | `0x644d7353` (`dMsS`) | – | 7 | 0 |
| `DebugClubPotentialAffiliatesPanelReference` | `0x5748776d` (`WHwm`) | – | 2 | 1 |
| `DebugCompAnalysisClubFinancesReference` | `0x5563566e` (`UcVn`) | – | 9 | 0 |
| `DebugCompetitionClubVisionObjectivesReference` | `0x46764276` (`FvBv`) | – | 11 | 1 |
| `DebugContractExpiryAnalysisItemReference` | `0x44436572` (`DCer`) | – | 14 | 1 |
| `DebugContractExpiryAnalysisOverviewReference` | `0x556c3262` (`Ul2b`) | – | 2 | 0 |
| `DebugContractOfferComponentEvaluationReference` | `0x76374371` (`v7Cq`) | – | 4 | 1 |
| `DebugContractOfferEvaluationReference` | `0x70586f38` (`pXo8`) | – | 9 | 0 |
| `DebugDisplayReference` | `0x636d6c74` (`cmlt`) | – | 20 | 0 |
| `DebugFinanceExpenditureReference` | `0x4e447032` (`NDp2`) | – | 23 | 0 |
| `DebugFinanceIncomeReference` | `0x65316845` (`e1hE`) | – | 19 | 0 |
| `DebugFinanceTotalsReference` | `0x524c6365` (`RLce`) | – | 14 | 0 |
| `DebugInteractionStringsReference` | `0x39694e30` (`9iN0`) | – | 5 | 0 |
| `DebugManagerBackingReference` | `0x65683763` (`eh7c`) | – | 10 | 0 |
| `DebugMentoringGroupsReference` | `0x306f4d38` (`0oM8`) | – | 5 | 1 |
| `DebugNationInterestReference` | `0x386d6f61` (`8moa`) | – | 3 | 1 |
| `DebugNationYouthRatingTableReference` | `0x336e694f` (`3niO`) | – | 21 | 1 |
| `DebugNationalPlayerConsideredForSlotReference` | `0x4f495a71` (`OIZq`) | – | 5 | 1 |
| `DebugNationalTeamPlayerToBeSelectedReference` | `0x41474b59` (`AGKY`) | – | 3 | 1 |
| `DebugPersonCoachingCourseReference` | `0x38335642` (`83VB`) | – | 3 | 1 |
| `DebugPlayerPartnershipsReference` | `0x4e447033` (`NDp3`) | – | 9 | 0 |
| `DebugPlayerTargetsReference` | `0x6a665370` (`jfSp`) | – | 6 | 0 |
| `DebugPlayerTargetsValidityReference` | `0x45375957` (`E7YW`) | – | 4 | 0 |
| `DebugSquadDepthReference` | `0x32736332` (`2sc2`) | – | 5 | 1 |
| `DebugSquadMakeUpAnalysisItemReference` | `0x6565574b` (`eeWK`) | – | 14 | 1 |
| `DebugSquadMakeUpAnalysisOverviewReference` | `0x546e3352` (`Tn3R`) | – | 2 | 0 |
| `DebugTableReference` | `0x674a626a` (`gJbj`) | – | 3 | 1 |
| `DebugTeamAnalysisAcclimatiseTableReference` | `0x78426e57` (`xBnW`) | – | 5 | 0 |
| `DebugTeamAnalysisAttributeGapsReference` | `0x69737074` (`ispt`) | – | 4 | 1 |
| `DebugTeamAnalysisBuyBackTableReference` | `0x6b4e5471` (`kNTq`) | – | 6 | 0 |
| `DebugTeamAnalysisContractRebelsReference` | `0x347a726b` (`4zrk`) | – | 9 | 0 |
| `DebugTeamAnalysisDevelopmentalLoanReference` | `0x4336204c` (`C6 L`) | – | 7 | 0 |
| `DebugTeamAnalysisEarlyLoanRecallReference` | `0x4b315a55` (`K1ZU`) | – | 7 | 0 |
| `DebugTeamAnalysisEscTableReference` | `0x5a494d4a` (`ZIMJ`) | – | 4 | 0 |
| `DebugTeamAnalysisHighProfilePlayersTablesReference` | `0x44544850` (`DTHP`) | – | 2 | 2 |
| `DebugTeamAnalysisMutualTerminationCandidatesReference` | `0x446d7452` (`DmtR`) | – | 6 | 0 |
| `DebugTeamAnalysisPlayerRequiredScoreReference` | `0x36655a6e` (`6eZn`) | – | 5 | 1 |
| `DebugTeamAnalysisSellingTeamWageContributionReference` | `0x47355a74` (`G5Zt`) | – | 4 | 0 |
| `DebugTeamAnalysisTopEarnersReference` | `0x65783733` (`ex73`) | – | 3 | 2 |
| `DebugTeamAnalysisWorkExperienceLoanReference` | `0x33774434` (`3wD4`) | – | 3 | 2 |
| `DebugTransferValueReference` | `0x34636669` (`4cfi`) | – | 4 | 0 |
| `DebugTransferValueRowReference` | `0x446d4d30` (`DmM0`) | – | 2 | 0 |
| `DepartmentVacancyInfoReference` | `0x656f6e41` (`eonA`) | – | 3 | 0 |
| `DerbyInfoReference` | `0x4a464920` (`JFI `) | – | 2 | 1 |
| `DerbyReference` | `0x44420012` | – | 0 | 0 |
| `DevelopmentCentreAdviceReference` | `0x31496432` (`1Id2`) | – | 4 | 0 |
| `DevelopmentPlayersFirstTeamCandidatesReference` | `0x4b59536d` (`KYSm`) | – | 2 | 0 |
| `DialogReference` | `0x57704e53` (`WpNS`) | – | 21 | 0 |
| `DialogStringsReference` | `0x716c5471` (`qlTq`) | – | 8 | 0 |
| `DisciplineOverviewDataReference` | `0x536c6c48` (`SllH`) | – | 6 | 0 |
| `DisplayValuePairReference` | `0x5a336843` (`Z3hC`) | – | 2 | 0 |
| `DisplayValuePairWithDescriptionReference` | `0x4b615164` (`KaQd`) | – | 3 | 0 |
| `DisplayValuePairWithPositionReference` | `0x34653644` (`4e6D`) | – | 3 | 0 |
| `DisplayValueTweakedInstructionReference` | `0x5a33675a` (`Z3gZ`) | – | 4 | 0 |
| `DisplayValueWithSortReference` | `0x4f57726b` (`OWrk`) | – | 2 | 0 |
| `DivisionContCupReservedSlotsChangeNewsReference` | `0x50367965` (`P6ye`) | – | 3 | 2 |
| `DofTargetReference` | `0x20476c52` (` GlR`) | – | 32 | 0 |
| `DofTransferTargetsReference` | `0x3872474c` (`8rGL`) | – | 8 | 1 |
| `DraftCurrentPickReference` | `0x7934507a` (`y4Pz`) | – | 3 | 0 |
| `DraftIdentifierReference` | `0x6f30316e` (`o01n`) | – | 3 | 0 |
| `DraftInformationReference` | `0x57376350` (`W7cP`) | – | 6 | 0 |
| `DraftPickOrderReference` | `0x4952776e` (`IRwn`) | – | 2 | 1 |
| `DraftReference` | `0x58585444` (`XXTD`) | `IDraftBaseReference` | 11 | 0 |
| `DragAndDropReference` | `0x00000004` | – | 3 | 0 |
| `DrawTeamSlotReference` | `0x44555572` (`DUUr`) | – | 5 | 1 |
| `DropdownWithStepComponentReference` | `0x6b583358` (`kX3X`) | – | 3 | 1 |
| `DugoutSubstitutionReference` | `0x42674661` (`BgFa`) | – | 7 | 1 |
| `DugoutXgReference` | `0x4a784f6c` (`JxOl`) | – | 3 | 0 |
| `DynamicReference` | `0x00000001` | – | 0 | 0 |
| `DynamicsFeedbackDataReference` | `0x68727073` (`hrps`) | – | 12 | 0 |
| `EditSessionUndoBufferReference` | `0x30734d70` (`0sMp`) | – | 4 | 0 |
| `EditorFieldReference` | `0x65646975` (`ediu`) | – | 35 | 2 |
| `EditorFileReference` | `0x735ce172` | – | 9 | 0 |
| `EditorReference` | `0x65646974` (`edit`) | – | 10 | 1 |
| `ElementWithIndexReference` | `0x456a6b75` (`Ejku`) | – | 2 | 0 |
| `EndOfSeasonProjectionReference` | `0x7249706d` (`rIpm`) | – | 4 | 0 |
| `EstimatedAndActualReference` | `0x38753078` (`8u0x`) | – | 2 | 0 |
| `ExpectedFormationReference` | `0x46307a62` (`F0zb`) | – | 2 | 1 |
| `ExpectedTacticReference` | `0x6f507738` (`oPw8`) | – | 4 | 0 |
| `ExpectedTacticalStyleReference` | `0x594a4e57` (`YJNW`) | – | 5 | 0 |
| `ExperienceMatrixReference` | `0x364c7120` (`6Lq `) | – | 4 | 0 |
| `ExpiringContractDropdownRowReference` | `0x4c506f74` (`LPot`) | – | 3 | 1 |
| `ExternalNewsLinksReference` | `0x7a774178` (`zwAx`) | – | 4 | 1 |
| `ExtraSquadRuleReference` | `0x78436d34` (`xCm4`) | – | 3 | 0 |
| `FFPDetailsReference` | `0x4e737864` (`Nsxd`) | – | 31 | 1 |
| `FMConstantsReference` | `0x766c6573` (`vles`) | – | 10 | 0 |
| `FMFCReference` | `0x4c70576a` (`LpWj`) | – | 2 | 0 |
| `FMpediaDataReference` | `0x72424152` (`rBAR`) | – | 7 | 0 |
| `FacilityRatingReference` | `0x72637678` (`rcvx`) | – | 4 | 1 |
| `FactTypeDataReference` | `0x596d6620` (`Ymf `) | – | 2 | 1 |
| `FactsDataReference` | `0x79324e57` (`y2NW`) | – | 4 | 0 |
| `FakeClubReference` | `0x000c3500` | – | 5 | 1 |
| `FakeLeagueReference` | `0x000c3501` | – | 2 | 0 |
| `FantasyDraftAIManagerReference` | `0x5a66756b` (`Zfuk`) | – | 7 | 1 |
| `FantasyDraftGameReference` | `0x58585447` (`XXTG`) | – | 23 | 0 |
| `FantasyDraftReference` | `0x58585445` (`XXTE`) | `IDraftBaseReference` | 25 | 1 |
| `FavouredClubReference` | `0x41674654` (`AgFT`) | – | 2 | 1 |
| `FavouredClubsReasonReference` | `0x41674655` (`AgFU`) | – | 3 | 0 |
| `FavouredClubsReference` | `0x41674653` (`AgFS`) | – | 9 | 1 |
| `FavouredPeopleReasonReference` | `0x48636759` (`HcgY`) | – | 4 | 0 |
| `FavouredPeopleReference` | `0x324a4b61` (`2JKa`) | – | 7 | 1 |
| `FavouredPersonReference` | `0x52305a46` (`R0ZF`) | – | 2 | 1 |
| `FeederClubNewsItemReference` | `0x65677a36` (`egz6`) | – | 2 | 1 |
| `FifaRankingHistoryReference` | `0x336b3644` (`3k6D`) | – | 7 | 0 |
| `FileBrowserEntryReference` | `0x7a723754` (`zr7T`) | – | 5 | 0 |
| `FileBrowserReference` | `0x426e3852` (`Bn8R`) | – | 11 | 0 |
| `FilterActiveCountReference` | `0x6e614775` (`naGu`) | – | 2 | 0 |
| `FilterAttributeAndConditionReference` | `0x67476261` (`gGba`) | – | 5 | 0 |
| `FilterAttributeReference` | `0x79596143` (`yYaC`) | – | 3 | 0 |
| `FilterCompareRuleReference` | `0x6663726c` (`fcrl`) | `FilterRuleReference` | 38 | 0 |
| `FilterConditionCategoryDataAndActiveCountReference` | `0x54326845` (`T2hE`) | – | 2 | 2 |
| `FilterReference` | `0x66696c74` (`filt`) | – | 12 | 1 |
| `FilterRuleItemReference` | `0x72637679` (`rcvy`) | – | 2 | 0 |
| `FilterRuleMenuItemReference` | `0x35526343` (`5RcC`) | – | 3 | 0 |
| `FilterRuleReference` | `0x666c7472` (`fltr`) | – | 3 | 0 |
| `FinanceBreakdownRowReference` | `0x46544c47` (`FTLG`) | – | 6 | 0 |
| `FinanceDebtsLoansRowReference` | `0x69566575` (`iVeu`) | – | 11 | 0 |
| `FinanceNotableBreakdownRowReference` | `0x37587061` (`7Xpa`) | – | 4 | 0 |
| `FinancePlayerTypeWageRowReference` | `0x7a676234` (`zgb4`) | – | 10 | 0 |
| `FinanceProjectionsDataReference` | `0x43755a79` (`CuZy`) | – | 5 | 1 |
| `FinanceSponsorshipRowReference` | `0x685a6a51` (`hZjQ`) | – | 7 | 0 |
| `FinanceWagesDataReference` | `0x6e376e70` (`n7np`) | – | 26 | 0 |
| `FirstContactZoneMapReference` | `0x4948466c` (`IHFl`) | – | 6 | 1 |
| `FixtureDropdownDataReference` | `0x39384558` (`98EX`) | – | 2 | 1 |
| `FixtureEventInfoReference` | `0x45464775` (`EFGu`) | – | 5 | 1 |
| `FixtureIDReference` | `0x6b624a65` (`kbJe`) | – | 2 | 1 |
| `FixtureIncidentReference` | `0x66696e63` (`finc`) | – | 6 | 1 |
| `FixtureLineupReference` | `0x36324276` (`62Bv`) | – | 3 | 1 |
| `FixtureListElementReference` | `0x766a536f` (`vjSo`) | – | 3 | 1 |
| `FixtureNameReference` | `0x44420039` | – | 1 | 0 |
| `FixtureOddsReference` | `0x58634235` (`XcB5`) | – | 4 | 0 |
| `FixtureRearrangedFixtureReference` | `0x4d6e4c67` (`MnLg`) | – | 5 | 0 |
| `FixtureRearrangedNewsReference` | `0x5749716e` (`WIqn`) | – | 2 | 2 |
| `FixtureReference` | `0x66697874` (`fixt`) | – | 119 | 1 |
| `FixtureToWatchReference` | `0x4b397a52` (`K9zR`) | – | 3 | 1 |
| `FixtureWeatherReference` | `0x30522067` (`0R g`) | – | 9 | 0 |
| `FixturesInternationalManagerShouldWatchNewsReference` | `0x4d39416a` (`M9Aj`) | – | 1 | 0 |
| `FootednessReference` | `0x73383878` (`s88x`) | – | 11 | 0 |
| `ForcedResultDataReference` | `0x4b395168` (`K9Qh`) | – | 7 | 0 |
| `ForcedResultsReference` | `0x6548664b` (`eHfK`) | – | 9 | 2 |
| `FormationAnalysisReference` | `0x65554952` (`eUIR`) | – | 2 | 0 |
| `FormationChancesReference` | `0x78714c36` (`xqL6`) | – | 9 | 0 |
| `FormationLayoutReference` | `0x79474233` (`yGB3`) | – | 3 | 1 |
| `FormationPositionDataReference` | `0x4630444a` (`F0DJ`) | – | 1 | 0 |
| `FutureDraftReference` | `0x724f3870` (`rO8p`) | – | 3 | 0 |
| `GameBackgroundReference` | `0x35523636` (`5R66`) | – | 5 | 0 |
| `GameCreationClubHistoryReference` | `0x704e6752` (`pNgR`) | – | 3 | 1 |
| `GameCreationClubRivalReference` | `0x704e6949` (`pNiI`) | – | 2 | 1 |
| `GameCreationLeagueHistoryReference` | `0x6f466803` | – | 3 | 1 |
| `GameCreationLeagueRivalryReference` | `0x704e66e9` | – | 2 | 0 |
| `GameCreationPersonLookupDataReference` | `0x704e694a` (`pNiJ`) | – | 1 | 0 |
| `GameCreationTopClubReference` | `0x6f466847` (`oFhG`) | – | 3 | 2 |
| `GameCreationTopPlayerReference` | `0x704e694b` (`pNiK`) | – | 2 | 2 |
| `GameReference` | `0x67616d65` (`game`) | – | 131 | 3 |
| `GameWorldTabsAndBookmarksReference` | `0x67383530` (`g850`) | – | 35 | 0 |
| `GoOnHolidayReference` | `0x474f4872` (`GOHr`) | – | 20 | 1 |
| `GoalDataListReference` | `0x6d67465a` (`mgFZ`) | – | 3 | 1 |
| `GoalTimesReference` | `0x5634794e` (`V4yN`) | – | 7 | 1 |
| `GraphCoordinateReference` | `0x6f434545` (`oCEE`) | – | 2 | 0 |
| `GraphPointReference` | `0x4148766b` (`AHvk`) | – | 2 | 0 |
| `GroupStageNewRulesUEFAClubCompFixturesReference` | `0x74627854` (`tbxT`) | – | 5 | 1 |
| `GroupStageNewRulesUEFAClubCompNewsReference` | `0x677a4b56` (`gzKV`) | – | 5 | 0 |
| `HallOfFameEntryCompetitionReference` | `0x68666563` (`hfec`) | – | 4 | 1 |
| `HallOfFameEntryReference` | `0x686f6665` (`hofe`) | – | 6 | 0 |
| `HallOfFameRowReference` | `0x686f6673` (`hofs`) | – | 11 | 0 |
| `HappinessCategoryReference` | `0x79354d69` (`y5Mi`) | – | 6 | 0 |
| `HappinessIssuesRowReference` | `0x76204c41` (`v LA`) | – | 12 | 1 |
| `HeatMapPlayerDataReference` | `0x3771686f` (`7qho`) | – | 4 | 1 |
| `HeatMapReference` | `0x68493239` (`hI29`) | – | 6 | 0 |
| `HierarchyChangeDataReference` | `0x554a5a50` (`UJZP`) | – | 8 | 0 |
| `HighlightedStarPlayerRowReference` | `0x56454b75` (`VEKu`) | – | 2 | 0 |
| `HireIntermediaryReference` | `0x454f514a` (`EOQJ`) | – | 8 | 0 |
| `HistorySummaryReference` | `0x38365355` (`86SU`) | – | 8 | 1 |
| `HomeGrownNewsReference` | `0x31526837` (`1Rh7`) | – | 3 | 0 |
| `HomegrownCurrentRuleReference` | `0x53784d64` (`SxMd`) | – | 11 | 0 |
| `HumanActionControlPanelItemReference` | `0x6c4a5837` (`lJX7`) | – | 2 | 0 |
| `HumanContractOfferAgreementsReference` | `0x78323167` (`x21g`) | – | 9 | 0 |
| `HumanOrConnectionReference` | `0x686f7263` (`horc`) | – | 4 | 0 |
| `IAgentReference` | `0x61676e74` (`agnt`) | `IPersonBaseReference` | 323 | 4 |
| `IAnalysisVisualisationBaseDataReference` | `0x65735652` (`esVR`) | – | 2 | 0 |
| `IClubFinanceOverviewReference` | `0x54205176` (`T Qv`) | – | 9 | 2 |
| `IDraftBaseReference` | `0x58585446` (`XXTF`) | – | 8 | 0 |
| `IGEMovePersonReference` | `0x61645a4b` (`adZK`) | – | 48 | 0 |
| `IGEReference` | `0x74567a57` (`tVzW`) | – | 4 | 0 |
| `IJournalistReference` | `0x65717134` (`eqq4`) | `IPersonBaseReference` | 313 | 3 |
| `INonPlayerReference` | `0x4e706c79` (`Nply`) | `IPersonBaseReference` | 577 | 56 |
| `IOfficialReference` | `0x34775370` (`4wSp`) | `IPersonBaseReference` | 317 | 3 |
| `IPersonBaseReference` | `0x75303456` (`u04V`) | – | 310 | 3 |
| `IPlayerReference` | `0x706c7972` (`plyr`) | `IPersonBaseReference` | 997 | 84 |
| `ITacticsTeamSelectionReference` | `0x6d347248` (`m4rH`) | – | 4 | 0 |
| `ITeamContainerReference` | `0x524f664c` (`ROfL`) | – | 95 | 1 |
| `ITrainingSelectorReference` | `0x564e5334` (`VNS4`) | – | 9 | 2 |
| `IconTextItemReference` | `0x78b401f4` | – | 2 | 0 |
| `ImpossibleSignUpReference` | `0x69737572` (`isur`) | – | 5 | 0 |
| `IndividualTrainingOverviewReference` | `0x624c4d41` (`bLMA`) | – | 3 | 0 |
| `IndividualTrainingTypeReference` | `0x66564356` (`fVCV`) | – | 5 | 0 |
| `InductionReference` | `0x37584f43` (`7XOC`) | – | 1 | 1 |
| `InjuryListItemReference` | `0x7a533173` (`zS1s`) | – | 3 | 1 |
| `InputReference` | `0x61722037` (`ar 7`) | – | 7 | 0 |
| `InstalmentImpactPerSeasonReference` | `0x51753854` (`Qu8T`) | – | 3 | 0 |
| `InteractionBodyLanguageReference` | `0x66535a76` (`fSZv`) | – | 4 | 0 |
| `InteractionPersonAndBodyLanguageReference` | `0x20435936` (` CY6`) | – | 2 | 2 |
| `IntermediaryOffersReference` | `0x20764358` (` vCX`) | – | 6 | 1 |
| `InternationalCallupReference` | `0x6c39634d` (`l9cM`) | – | 2 | 1 |
| `InternationalCompConfidenceReference` | `0x706b7477` (`pktw`) | – | 3 | 1 |
| `IntroSceneReference` | `0x4a4a3775` (`JJ7u`) | – | 7 | 0 |
| `JobAdvertReference` | `0x58474765` (`XGGe`) | – | 6 | 0 |
| `JobHistoryReference` | `0x733fe392` | – | 7 | 0 |
| `JobReference` | `0x7636476b` (`v6Gk`) | – | 3 | 1 |
| `JobStatusReference` | `0x4347455a` (`CGEZ`) | – | 4 | 0 |
| `JobVacancyInfoReference` | `0x617a474e` (`azGN`) | – | 2 | 0 |
| `KeyFindingsVisualReference` | `0x48704536` (`HpE6`) | – | 5 | 1 |
| `KitReference` | `0x6057044b` | – | 23 | 0 |
| `LanguageReference` | `0x44420008` | – | 1 | 0 |
| `LastFiveMatchesFormReference` | `0x5a373367` (`Z73g`) | – | 8 | 0 |
| `LastMatchAnalysisVisualsReference` | `0x615a3067` (`aZ0g`) | – | 10 | 0 |
| `LastMatchSquadReference` | `0x6b543957` (`kT9W`) | – | 2 | 0 |
| `LatticeReference` | `0x4c745266` (`LtRf`) | – | 3 | 1 |
| `LazyMenuReference` | `0x3073554e` (`0sUN`) | – | 6 | 0 |
| `LeagueCombinedTableRowReference` | `0x636d6c76` (`cmlv`) | – | 21 | 0 |
| `LeagueFateReference` | `0x4946484b` (`IFHK`) | – | 3 | 1 |
| `LeaguePositionHistoryReference` | `0x6a455474` (`jETt`) | – | 10 | 1 |
| `LeagueSeasonClimaxReference` | `0x35624d65` (`5bMe`) | – | 2 | 2 |
| `LeagueSpecificDataReference` | `0x71415670` (`qAVp`) | – | 33 | 1 |
| `LeagueTableColorGroupReference` | `0x4b425844` (`KBXD`) | – | 2 | 0 |
| `LeagueTableRowReference` | `0x636d6c75` (`cmlu`) | – | 22 | 0 |
| `LineChartDataPointReference` | `0x31202021` (`1  !`) | – | 4 | 0 |
| `ListItemReference` | `0x43495652` (`CIVR`) | – | 1 | 0 |
| `ListReference` | `0x59206c6a` (`Y lj`) | – | 2 | 0 |
| `LoanReportReference` | `0x45306143` (`E0aC`) | – | 17 | 0 |
| `LoansPlayersMessageReference` | `0x4950556c` (`IPUl`) | – | 3 | 2 |
| `LocalRegionReference` | `0x4442002f` | – | 1 | 0 |
| `MLSCombinePlayerReference` | `0x366e6c49` (`6nlI`) | – | 2 | 1 |
| `ManagerHistoryCareerMilestoneReference` | `0x55784a35` (`UxJ5`) | – | 3 | 1 |
| `ManagerHistoryRecordReference` | `0x67643672` (`gd6r`) | – | 19 | 1 |
| `ManagerHistoryReference` | `0x46447169` (`FDqi`) | – | 10 | 0 |
| `ManagerKnownForReference` | `0x4c585754` (`LXWT`) | – | 2 | 0 |
| `ManagerMovementReference` | `0x73383879` (`s88y`) | – | 8 | 0 |
| `ManagerPersonaReference` | `0x35667870` (`5fxp`) | – | 43 | 0 |
| `ManagerPersonaUIReference` | `0x644b5855` (`dKXU`) | – | 7 | 0 |
| `ManagerSupportReference` | `0x644b5a49` (`dKZI`) | – | 4 | 0 |
| `ManagerTaskReference` | `0x6d74736b` (`mtsk`) | – | 0 | 0 |
| `MatchAnalysisFeedbackReference` | `0x5578324b` (`Ux2K`) | – | 16 | 0 |
| `MatchAnalysisPointKeyFindingsPairReference` | `0x4b534957` (`KSIW`) | – | 2 | 0 |
| `MatchClientInfoReference` | `0x686f7264` (`hord`) | – | 4 | 0 |
| `MatchConfidenceReference` | `0x3651526b` (`6QRk`) | – | 11 | 0 |
| `MatchDugoutEventInstanceReference` | `0x744e425a` (`tNBZ`) | – | 4 | 1 |
| `MatchDugoutEventScoreUpdateReference` | `0x64474336` (`dGC6`) | – | 4 | 1 |
| `MatchDugoutReference` | `0x45567662` (`EVvb`) | – | 2 | 0 |
| `MatchDugoutSelectedEventReference` | `0x6369466d` (`ciFm`) | – | 5 | 0 |
| `MatchDugoutTimelineEventReference` | `0x45503634` (`EP64`) | – | 3 | 0 |
| `MatchFocusPreparationReference` | `0x5a20674c` (`Z gL`) | – | 4 | 1 |
| `MatchFocusReference` | `0x6d61666f` (`mafo`) | – | 10 | 1 |
| `MatchFocusSessionReference` | `0x45596b6c` (`EYkl`) | – | 6 | 0 |
| `MatchFormReference` | `0x42376f70` (`B7op`) | – | 18 | 0 |
| `MatchMomentumObservationReference` | `0x4f426e66` (`OBnf`) | – | 10 | 1 |
| `MatchMomentumSegmentReference` | `0x58696330` (`Xic0`) | – | 5 | 1 |
| `MatchOfTheDayNewsReference` | `0x30495336` (`0IS6`) | – | 3 | 3 |
| `MatchPenaltyShootoutReference` | `0x72566f79` (`rVoy`) | – | 7 | 0 |
| `MatchPlayerReference` | `0x6d617464` (`matd`) | `ITacticsTeamSelectionReference` | 43 | 1 |
| `MatchPreparationDropdownRowReference` | `0x4c4a516e` (`LJQn`) | – | 7 | 0 |
| `MatchPreparationReference` | `0x6265206f` (`be o`) | – | 2 | 1 |
| `MatchPreparationTrainingSlotReference` | `0x65764343` (`evCC`) | – | 8 | 1 |
| `MatchRatingsReference` | `0x6d746372` (`mtcr`) | – | 9 | 0 |
| `MatchReference` | `0x6d617463` (`matc`) | – | 123 | 2 |
| `MatchReportDataReference` | `0x4ea74e72` | – | 12 | 2 |
| `MatchReportNewsReference` | `0x6834d598` | – | 2 | 2 |
| `MatchRulesDataReference` | `0x61594731` (`aYG1`) | – | 4 | 0 |
| `MatchRulesReference` | `0x7670374e` (`vp7N`) | – | 4 | 0 |
| `MatchStatsReference` | `0x37545638` (`7TV8`) | – | 39 | 0 |
| `MatchTacticReference` | `0x77725344` (`wrSD`) | – | 35 | 1 |
| `MediaDreamTeamInfoReference` | `0x20346254` (` 4bT`) | – | 2 | 0 |
| `MediaNewsAwardReference` | `0x4d4f6461` (`MOda`) | – | 13 | 2 |
| `MediaNewsBackgroundReference` | `0x69774a69` (`iwJi`) | – | 5 | 0 |
| `MediaNewsCommercialSummaryReference` | `0x6e345439` (`n4T9`) | – | 8 | 1 |
| `MediaNewsCompetitionReference` | `0x43314d20` (`C1M `) | – | 5 | 0 |
| `MediaNewsContractReference` | `0x7a664262` (`zfBb`) | – | 6 | 0 |
| `MediaNewsGenericReference` | `0x6d457273` (`mErs`) | – | 12 | 0 |
| `MediaNewsMatchReference` | `0x38417954` (`8AyT`) | – | 4 | 0 |
| `MediaNewsMatchResultReference` | `0x66784b50` (`fxKP`) | `MediaNewsMatchReference` | 7 | 0 |
| `MediaNewsTransfersReference` | `0x78624a79` (`xbJy`) | – | 7 | 0 |
| `MediaSourceReference` | `0x44420007` | – | 1 | 0 |
| `MentoringGroupReference` | `0x34434374` (`4CCt`) | – | 17 | 1 |
| `MentoringGroupsReference` | `0x32565641` (`2VVA`) | – | 2 | 0 |
| `MenuItemLabelReference` | `0x47673153` (`Gg1S`) | – | 2 | 0 |
| `MenuItemReference` | `0x35517667` (`5Qvg`) | – | 2 | 0 |
| `MinFeeReleaseClauseRoundupReference` | `0x4d7a7331` (`Mzs1`) | – | 1 | 0 |
| `MonthlyFinancialUpdateNewsReference` | `0x4cf60a9a` | `IClubFinanceOverviewReference` | 9 | 2 |
| `MultiplayerReference` | `0x59206c66` (`Y lf`) | – | 14 | 0 |
| `NPCWithActionsReference` | `0x4d545633` (`MTV3`) | – | 6 | 0 |
| `NationCoefficientEntryReference` | `0x37323557` (`725W`) | – | 14 | 1 |
| `NationCoefficientsReference` | `0x6e636f72` (`ncor`) | – | 13 | 0 |
| `NationCompetitionTierReference` | `0x486d4856` (`HmHV`) | – | 3 | 0 |
| `NationEligibilityReference` | `0x6e636572` (`ncer`) | – | 7 | 1 |
| `NationPlayersReleasedNewsReference` | `0x48666e6d` (`Hfnm`) | – | 2 | 1 |
| `NationQualificationReference` | `0x4e615175` (`NaQu`) | – | 13 | 1 |
| `NationReference` | `0x4442000a` | – | 60 | 7 |
| `NationalSquadSelectionEditSessionReference` | `0x53704f76` (`SpOv`) | – | 22 | 1 |
| `NationalSquadSelectionReference` | `0x636c4434` (`clD4`) | – | 8 | 1 |
| `NationalTeamContainerReference` | `0x44420009` | `ITeamContainerReference` | 134 | 1 |
| `NegotiateAskForPayOffReference` | `0x4b503036` (`KP06`) | – | 12 | 0 |
| `NegotiationCommentsReference` | `0x746a6330` (`tjc0`) | – | 5 | 0 |
| `NegotiationLockReference` | `0x72367269` (`r6ri`) | – | 3 | 0 |
| `NetworkConnectionReference` | `0x4e74436e` (`NtCn`) | – | 14 | 0 |
| `NewgenAppearanceDescriptionReference` | `0x50755141` (`PuQA`) | – | 14 | 0 |
| `NewsActionDataReference` | `0x45626b33` (`Ebk3`) | – | 4 | 0 |
| `NewsActionDataWithDisplayValueReference` | `0x67347876` (`g4xv`) | – | 2 | 1 |
| `NewsItemReference` | `0x6e69746d` (`nitm`) | – | 50 | 2 |
| `NewsSiteDropdownReference` | `0x73424833` (`sBH3`) | – | 7 | 0 |
| `NonPlayerAttributeReference` | `0x7951694f` (`yQiO`) | – | 5 | 0 |
| `NonPlayerNationKnowledgeReference` | `0x45464265` (`EFBe`) | – | 4 | 1 |
| `NonPlayerStaffRolesReference` | `0x71467546` (`qFuF`) | – | 4 | 0 |
| `NonPlayerTendanciesReference` | `0x62624746` (`bbGF`) | – | 2 | 0 |
| `NotableShortlistReference` | `0x56383954` (`V89T`) | – | 3 | 0 |
| `NotificationReference` | `0x50476c77` (`PGlw`) | – | 2 | 0 |
| `NullReference` | `0x00000002` | `ListItemReference` | 0 | 0 |
| `OOPTrainingReference` | `0x72456375` (`rEcu`) | – | 8 | 0 |
| `OddsLeagueTableRowReference` | `0x33356f47` (`35oG`) | – | 6 | 0 |
| `OnlineLobbyReference` | `0x6e746c62` (`ntlb`) | – | 31 | 0 |
| `OppositionInstructionSuggestionReference` | `0x535a5565` (`SZUe`) | – | 4 | 1 |
| `OppositionReportVisualsReference` | `0x53446e6e` (`SDnn`) | – | 2 | 1 |
| `OwnPlayerTappingUpAnotherPlayerNewsItemReference` | `0x574e314e` (`WN1N`) | – | 3 | 0 |
| `PanelHistoryReference` | `0x447a4459` (`DzDY`) | – | 9 | 1 |
| `PassCombinationReference` | `0x48446771` (`HDgq`) | – | 3 | 1 |
| `PassCompletionReference` | `0x534b4e41` (`SKNA`) | – | 4 | 0 |
| `PassMapPlayerDataReference` | `0x5a73326b` (`Zs2k`) | – | 5 | 1 |
| `PassMapPlayerIconDataReference` | `0x72575474` (`rWTt`) | – | 8 | 1 |
| `PassMapReference` | `0x4b68626b` (`Khbk`) | – | 5 | 0 |
| `PastDraftRoundReference` | `0x444f3933` (`DO93`) | – | 2 | 0 |
| `PastDraftSelectionReference` | `0x54696667` (`Tifg`) | – | 6 | 0 |
| `PastMatchTacticPlayerReference` | `0x66594c34` (`fYL4`) | – | 14 | 1 |
| `PastTransferReference` | `0x70737472` (`pstr`) | – | 6 | 0 |
| `PenaltyShootoutResultReference` | `0x63754d4d` (`cuMM`) | – | 3 | 0 |
| `PersonAwardHistoryItemReference` | `0x644d5134` (`dMQ4`) | – | 4 | 1 |
| `PersonAwardWinnerReference` | `0x7a533176` (`zS1v`) | – | 14 | 0 |
| `PersonContractCompetitionBonusActivatedReference` | `0x584a3750` (`XJ7P`) | – | 3 | 3 |
| `PersonExpiringContractReference` | `0x72307762` (`r0wb`) | – | 9 | 1 |
| `PersonFilterReference` | `0x4166756b` (`Afuk`) | – | 20 | 2 |
| `PersonInterestedClubReference` | `0x6b785048` (`kxPH`) | – | 3 | 1 |
| `PersonReference` | `0x44420001` | `INonPlayerReference`, `IJournalistReference`, `IPlayerReference`, `IPersonBaseReference`, `IAgentReference`, `IOfficialReference` | 1,287 | 103 |
| `PersonSearchReference` | `0x70727372` (`prsr`) | – | 74 | 1 |
| `PersonStringReference` | `0x744d5768` (`tMWh`) | – | 2 | 1 |
| `PersonTransferOfferReference` | `0x37717550` (`7quP`) | – | 5 | 1 |
| `PhysioTeamReportNewsReference` | `0x6e4a4a37` (`nJJ7`) | – | 2 | 1 |
| `PieChartValuePairReference` | `0x4d556354` (`MUcT`) | – | 2 | 0 |
| `PivotalMomentAnswerReference` | `0x3664646d` (`6ddm`) | – | 3 | 0 |
| `PivotalMomentReference` | `0x78593839` (`xY89`) | – | 7 | 1 |
| `PlannedStadiumWorkReference` | `0x394f384c` (`9O8L`) | – | 2 | 0 |
| `PlayerAbilityComparisonReference` | `0x6e4b3531` (`nK51`) | – | 2 | 0 |
| `PlayerAbilityComparisonRowReference` | `0x4b525778` (`KRWx`) | – | 6 | 0 |
| `PlayerAnalysisVisualsReference` | `0x56637320` (`Vcs `) | – | 3 | 2 |
| `PlayerAndRankingReference` | `0x596c7761` (`Ylwa`) | – | 2 | 1 |
| `PlayerAttributeComparisonCategoryReference` | `0x7a535248` (`zSRH`) | – | 2 | 1 |
| `PlayerAttributeComparisonReference` | `0x79466854` (`yFhT`) | – | 4 | 0 |
| `PlayerAttributeReference` | `0x5752694b` (`WRiK`) | – | 2 | 2 |
| `PlayerAttributeTypeReference` | `0x4a417347` (`JAsG`) | – | 5 | 0 |
| `PlayerAttributesGraphReference` | `0x5549454c` (`UIEL`) | – | 6 | 0 |
| `PlayerBansOverviewReference` | `0x3176734f` (`1vsO`) | – | 14 | 1 |
| `PlayerBuyinEventReference` | `0x43765432` (`CvT2`) | – | 4 | 0 |
| `PlayerComparisonStatisticsReference` | `0x5a554f46` (`ZUOF`) | – | 2 | 0 |
| `PlayerComparisonStatisticsRowReference` | `0x5a554f47` (`ZUOG`) | – | 4 | 0 |
| `PlayerFormFixtureDetailsReference` | `0x79656938` (`yei8`) | – | 15 | 1 |
| `PlayerFormMatchRatingsStatsReference` | `0x484f4948` (`HOIH`) | – | 9 | 0 |
| `PlayerFormMatchRowReference` | `0x73674767` (`sgGg`) | – | 37 | 0 |
| `PlayerFormReference` | `0x51576633` (`QWf3`) | – | 8 | 3 |
| `PlayerHappinessReference` | `0x71396a62` (`q9jb`) | – | 2 | 0 |
| `PlayerHistoryReference` | `0x4d654837` (`MeH7`) | – | 1 | 0 |
| `PlayerInjuryReference` | `0x376e4c79` (`7nLy`) | – | 24 | 1 |
| `PlayerInterestLevelReference` | `0x6a314869` (`j1Hi`) | – | 3 | 0 |
| `PlayerInvolvedInMatchReference` | `0x776d4764` (`wmGd`) | – | 12 | 0 |
| `PlayerLoanMostUsedPositionRoleReference` | `0x6d68337a` (`mh3z`) | – | 2 | 0 |
| `PlayerLoanSuggestionReference` | `0x745a4372` (`tZCr`) | – | 2 | 1 |
| `PlayerMatchStatsReference` | `0x566e7035` (`Vnp5`) | – | 82 | 1 |
| `PlayerMedalsNewsReference` | `0x55524f63` (`UROc`) | – | 3 | 1 |
| `PlayerNumberReference` | `0x496c716c` (`Ilql`) | – | 2 | 1 |
| `PlayerPastMatchReference` | `0x66747267` (`ftrg`) | – | 5 | 1 |
| `PlayerProjectedPositionReference` | `0x48515554` (`HQUT`) | – | 6 | 1 |
| `PlayerReportBasicInfoReference` | `0x6a6b4443` (`jkDC`) | – | 2 | 1 |
| `PlayerReportReference` | `0x4e644e54` (`NdNT`) | – | 40 | 1 |
| `PlayerReportScoutedAbilityReference` | `0x4d4d4f53` (`MMOS`) | – | 3 | 1 |
| `PlayerReportScoutedTransferInfoReference` | `0x4e435241` (`NCRA`) | – | 4 | 1 |
| `PlayerReportWatchedMatchesReference` | `0x70453745` (`pE7E`) | – | 3 | 0 |
| `PlayerSalaryCapAdjustmentReference` | `0x4251594e` (`BQYN`) | – | 8 | 1 |
| `PlayerSearchFilterSuggestionReference` | `0x4e594942` (`NYIB`) | – | 4 | 1 |
| `PlayerShirtSalesReference` | `0x6938754f` (`i8uO`) | – | 3 | 1 |
| `PlayerSignsLeavesAgentNewsReference` | `0x6e347456` (`n4tV`) | – | 2 | 1 |
| `PlayerStatValuePairReference` | `0x35496750` (`5IgP`) | – | 2 | 1 |
| `PlayerStatusFlagReference` | `0x63555a32` (`cUZ2`) | – | 6 | 0 |
| `PlayerTargetReference` | `0x73506835` (`sPh5`) | – | 26 | 0 |
| `PlayerTargetRowReference` | `0x494b686c` (`IKhl`) | – | 5 | 0 |
| `PlayerTrainingReference` | `0x706c3465` (`pl4e`) | – | 36 | 1 |
| `PlayerTraitReference` | `0x65466d62` (`eFmb`) | – | 4 | 0 |
| `PlayerTraitsReference` | `0x72514564` (`rQEd`) | – | 13 | 1 |
| `PlayerTransferOfferReference` | `0x56354578` (`V5Ex`) | – | 10 | 0 |
| `PlayerTransferStatusReference` | `0x6d323138` (`m218`) | – | 2 | 1 |
| `PlayerWithTacticalEffectivenessReference` | `0x4470556d` (`DpUm`) | – | 2 | 0 |
| `PlayersChangeRegistrationStatusReference` | `0x46343349` (`F43I`) | – | 3 | 2 |
| `PlayersInvolvedInMatchesNewsReference` | `0x42747736` (`Btw6`) | – | 3 | 1 |
| `PlayersInvolvedInMatchesReference` | `0x44335575` (`D3Uu`) | – | 3 | 1 |
| `PlayingTimePathwayEntryReference` | `0x75526d57` (`uRmW`) | – | 2 | 1 |
| `PolygonObservationReference` | `0x4139344c` (`A94L`) | – | 8 | 1 |
| `PolygonSegmentReference` | `0x69457235` (`iEr5`) | – | 4 | 0 |
| `PositionSelectedDataReference` | `0x53624b69` (`SbKi`) | – | 5 | 0 |
| `PositionalAbilitiesInfoReference` | `0x34534634` (`4SF4`) | – | 4 | 0 |
| `PositionalStatsRowReference` | `0x5753324c` (`WS2L`) | – | 6 | 0 |
| `PossiblePlayingTimeReference` | `0x506a3448` (`Pj4H`) | – | 3 | 0 |
| `PossibleTrainingPositionReference` | `0x37705536` (`7pU6`) | – | 9 | 1 |
| `PossibleTrainingPositionsReference` | `0x31204b44` (`1 KD`) | – | 2 | 1 |
| `PotentialBanReference` | `0x536c6c47` (`SllG`) | – | 7 | 0 |
| `PotentialConversationReference` | `0x51765a69` (`QvZi`) | – | 6 | 0 |
| `PreContractPromisesEditSessionBaseComponentReference` | `0x78587a34` (`xXz4`) | – | 3 | 0 |
| `PreContractPromisesEditSessionCoreComponentReference` | `0x56685146` (`VhQF`) | – | 2 | 1 |
| `PreContractPromisesEditSessionFuturePlayingTimeReference` | `0x78434130` (`xCA0`) | – | 13 | 1 |
| `PreContractPromisesEditSessionPromiseCategoryReference` | `0x13c6d6e4` | – | 2 | 1 |
| `PreContractPromisesEditSessionPromiseReference` | `0x4b6b557a` (`KkUz`) | – | 8 | 1 |
| `PreContractPromisesEditSessionReference` | `0x6d506c58` (`mPlX`) | – | 28 | 2 |
| `PreMatchLineupReference` | `0x63776d74` (`cwmt`) | – | 3 | 0 |
| `PreSeasonTrainingPrepNewsReference` | `0x65776a51` (`ewjQ`) | – | 4 | 1 |
| `PressConferenceEditSessionReference` | `0x476b6842` (`GkhB`) | – | 10 | 1 |
| `PreviousMeetingsReference` | `0x33657430` (`3et0`) | – | 7 | 0 |
| `PreviousPlayerBanReference` | `0x644c6147` (`dLaG`) | – | 4 | 0 |
| `PreviousStageTeamLinkReference` | `0x7073746c` (`pstl`) | – | 1 | 0 |
| `PrioritiseFutureTransferItemReference` | `0x49764e70` (`IvNp`) | – | 3 | 2 |
| `PrioritiseFutureTransfersReference` | `0x516c2053` (`Ql S`) | – | 3 | 1 |
| `PrivacyPolicyReference` | `0x79504149` (`yPAI`) | – | 17 | 0 |
| `ProConReference` | `0x20315948` (` 1YH`) | – | 5 | 0 |
| `PromiseReference` | `0x706d7266` (`pmrf`) | – | 18 | 1 |
| `PromoBannerReference` | `0x5a374c77` (`Z7Lw`) | – | 1 | 0 |
| `ProsConListsReference` | `0x62305a44` (`b0ZD`) | – | 4 | 0 |
| `QualificationPlacesInfoReference` | `0x62416648` (`bAfH`) | – | 9 | 0 |
| `QualificationPlacesListEntryReference` | `0x61476977` (`aGiw`) | – | 10 | 0 |
| `QualificationPlacesReference` | `0x766c4d58` (`vlMX`) | – | 3 | 1 |
| `QualificationStageNamesListEntryReference` | `0x704b666d` (`pKfm`) | – | 9 | 0 |
| `QuickStartReference` | `0x4857466c` (`HWFl`) | – | 3 | 0 |
| `RankedYouthCandidatesReference` | `0x63204a34` (`c J4`) | – | 15 | 0 |
| `RatedDebugStringReference` | `0x7635616a` (`v5aj`) | – | 3 | 0 |
| `RecentTacticsDebugInfoReference` | `0x356b7941` (`5kyA`) | – | 10 | 0 |
| `RecordReference` | `0x6f564661` (`oVFa`) | – | 4 | 0 |
| `RecruitmentFocusBasicSuggestionReference` | `0x346a6a72` (`4jjr`) | – | 2 | 0 |
| `RecruitmentFocusItemPositionReference` | `0x4b713767` (`Kq7g`) | – | 5 | 0 |
| `RecruitmentFocusItemReference` | `0x3669204c` (`6i L`) | – | 101 | 2 |
| `RecruitmentFocusPlayersStatsReference` | `0x42714647` (`BqFG`) | – | 3 | 0 |
| `RecruitmentFocusesReference` | `0x52466353` (`RFcS`) | – | 9 | 0 |
| `RegionReference` | `0x44420013` | – | 1 | 0 |
| `RelationshipWithHumanRanksReference` | `0x7465366f` (`te6o`) | – | 6 | 0 |
| `RelationshipWithHumanReference` | `0x4f754260` (`OuB``) | – | 4 | 0 |
| `RemovedRecordReference` | `0x4442001c` | – | 1 | 0 |
| `ReputationInfoReference` | `0x6859434c` (`hYCL`) | – | 2 | 0 |
| `ReserveTeamPlayerWarningNewsReference` | `0x56704e63` (`VpNc`) | – | 5 | 0 |
| `ResolutionReference` | `0x41474973` (`AGIs`) | – | 3 | 0 |
| `ResponsibilitiesRoundupReference` | `0x4f526258` (`ORbX`) | – | 4 | 0 |
| `ResponsibilityRoundupItemReference` | `0x67584853` (`gXHS`) | – | 4 | 0 |
| `RetainPlayerFilterPresetReference` | `0x34704e52` (`4pNR`) | – | 4 | 0 |
| `RetainPlayerFilterReference` | `0x4f654f73` (`OeOs`) | – | 19 | 3 |
| `RetainPlayerFilterRuleBoxItemReference` | `0x63435449` (`cCTI`) | – | 2 | 1 |
| `RetainPlayerFilterRuleBoxReference` | `0x4f654f74` (`OeOt`) | – | 3 | 0 |
| `RiskAssessmentReference` | `0x5553746a` (`UStj`) | – | 5 | 0 |
| `RivalTeamContainerReference` | `0x46357444` (`F5tD`) | – | 3 | 1 |
| `RoleAbilityRowReference` | `0x4e446a6b` (`NDjk`) | – | 7 | 1 |
| `RosterSalaryCapReference` | `0x67697474` (`gitt`) | – | 3 | 1 |
| `RotationsReference` | `0x4f727979` (`Oryy`) | – | 7 | 1 |
| `RuleGroupReference` | `0x726c6772` (`rlgr`) | – | 28 | 0 |
| `RunToDateReference` | `0x596e5159` (`YnQY`) | – | 2 | 0 |
| `RunToDateSelectorReference` | `0x556c4867` (`UlHg`) | – | 4 | 0 |
| `SaveGameReference` | `0x48396c43` (`H9lC`) | – | 6 | 0 |
| `SaveGameSummaryReference` | `0x73677375` (`sgsu`) | – | 31 | 0 |
| `ScatterChartDataPointReference` | `0x31202022` (`1  "`) | – | 2 | 0 |
| `ScatterChartPlayerTeamDataPointReference` | `0x79537638` (`ySv8`) | – | 3 | 3 |
| `ScattergraphAxisReference` | `0x4e575649` (`NWVI`) | – | 5 | 0 |
| `ScattergraphQuadrantReference` | `0x78646a4e` (`xdjN`) | – | 4 | 0 |
| `ScattergraphReference` | `0x57704e50` (`WpNP`) | – | 9 | 0 |
| `ScattergraphSubjectInfoReference` | `0x49696c61` (`Iila`) | – | 3 | 0 |
| `ScoutAssignmentsReference` | `0x6a6b7939` (`jky9`) | – | 3 | 1 |
| `ScoutNewsRecruitmentFocusSuggestionReference` | `0x46455649` (`FEVI`) | – | 3 | 1 |
| `ScoutNewsSingleMatchScoutReportReference` | `0x3071757a` (`0quz`) | – | 17 | 0 |
| `ScoutPlayerPrioritiesReference` | `0x41347977` (`A4yw`) | – | 9 | 3 |
| `ScoutTeamPrioritiesReference` | `0x69776244` (`iwbD`) | – | 3 | 0 |
| `ScoutedMatchReference` | `0x6c357432` (`l5t2`) | – | 6 | 0 |
| `ScoutedSquadComparisonReference` | `0x715a504c` (`qZPL`) | – | 5 | 0 |
| `ScoutedTransferInfoEntryReference` | `0x67565136` (`gVQ6`) | – | 3 | 0 |
| `ScoutingAreaReference` | `0x41727257` (`ArrW`) | – | 5 | 0 |
| `ScoutingCentreActionsReference` | `0x6f646d34` (`odm4`) | – | 41 | 2 |
| `ScoutingCentreDeliveryOptionReference` | `0x66624977` (`fbIw`) | – | 6 | 0 |
| `ScoutingCentreEntriesInfoReference` | `0x7156644a` (`qVdJ`) | – | 10 | 0 |
| `ScoutingCentreEntryItemReference` | `0x3579536e` (`5ySn`) | – | 7 | 0 |
| `ScoutingCentreEntryNewsReference` | `0x75516535` (`uQe5`) | – | 3 | 0 |
| `ScoutingInfoReference` | `0x4d466155` (`MFaU`) | – | 16 | 1 |
| `ScoutingKnowledgeLevelReference` | `0x654e454d` (`eNEM`) | – | 3 | 0 |
| `ScoutingRangeEntryReference` | `0x71536553` (`qSeS`) | – | 6 | 0 |
| `SearchReference` | `0x73656172` (`sear`) | – | 18 | 2 |
| `SearchResultReference` | `0x50487249` (`PHrI`) | – | 9 | 1 |
| `SeasonStatsReference` | `0x3535484d` (`55HM`) | – | 2 | 2 |
| `SeasonStatsRowReference` | `0x79625379` (`ybSy`) | – | 36 | 1 |
| `SeasonStatsSelectedCompetitionsReference` | `0x7a484e6c` (`zHNl`) | – | 59 | 0 |
| `SeasonSummaryCompetitionReference` | `0x4835535a` (`H5SZ`) | – | 32 | 0 |
| `SeasonSummaryContinentalFatesReference` | `0x684d4333` (`hMC3`) | – | 2 | 1 |
| `SeasonSummaryContinentalQualificationReference` | `0x6c20534e` (`l SN`) | – | 2 | 0 |
| `SeasonSummaryOverviewReference` | `0x4a636d55` (`JcmU`) | – | 4 | 0 |
| `SeasonTeamPreviewNewsReference` | `0x4679696f` (`Fyio`) | – | 2 | 0 |
| `SeasonTicketsSoldReference` | `0x6d506470` (`mPdp`) | – | 5 | 1 |
| `SeasonTransferInfoReference` | `0x46374b64` (`F7Kd`) | – | 13 | 0 |
| `SetPieceCreatorAnswerReference` | `0x58444242` (`XDBB`) | – | 5 | 0 |
| `SetPieceCreatorReference` | `0x42587036` (`BXp6`) | – | 15 | 0 |
| `SetPieceDataInsightsReference` | `0x33724947` (`3rIG`) | – | 2 | 0 |
| `SetPiecePenaltyTakerCandidateReference` | `0x66354748` (`f5GH`) | – | 2 | 1 |
| `SetPiecePitchPositionReference` | `0x6c7a566f` (`lzVo`) | – | 10 | 0 |
| `SetPieceReference` | `0x33685659` (`3hVY`) | – | 42 | 4 |
| `SetPieceResponsibilitiesReference` | `0x68647844` (`hdxD`) | – | 7 | 0 |
| `SetPieceRoutineCategoryInstructionReference` | `0x474f4d47` (`GOMG`) | – | 10 | 0 |
| `SetPieceRoutineCategoryPriorityReference` | `0x6d307a69` (`m0zi`) | – | 7 | 0 |
| `SetPieceRoutineCategoryReference` | `0x67366f46` (`g6oF`) | – | 5 | 0 |
| `SetPieceRoutineFrequencyReference` | `0x79697a58` (`yizX`) | – | 7 | 0 |
| `SetPieceRoutinePitchDataReference` | `0x63745a66` (`ctZf`) | – | 9 | 1 |
| `SetPieceRoutinePlayerReference` | `0x386f496c` (`8oIl`) | – | 4 | 1 |
| `SetPieceRoutineReference` | `0x30755872` (`0uXr`) | – | 34 | 0 |
| `SetPieceRoutineTakerReference` | `0x36546859` (`6ThY`) | – | 8 | 0 |
| `SetTransferStatusReference` | `0x354c4541` (`5LEA`) | – | 24 | 0 |
| `SettingsReference` | `0x00030d40` | – | 140 | 0 |
| `SetupGameAdvancedSettingsReference` | `0x50643175` (`Pd1u`) | – | 3 | 0 |
| `SetupGameReference` | `0x73746761` (`stga`) | – | 124 | 0 |
| `ShortcutDataReference` | `0x4779384f` (`Gy8O`) | – | 3 | 0 |
| `ShortlistSummaryReference` | `0x6b754a4e` (`kuJN`) | – | 5 | 0 |
| `ShotLocationDataPointReference` | `0x7041696d` (`pAim`) | – | 3 | 0 |
| `ShotLocationPitchReference` | `0x20624449` (` bDI`) | – | 13 | 1 |
| `ShotMapReference` | `0x79674742` (`ygGB`) | – | 15 | 0 |
| `ShotMapShotTypeReference` | `0x58384642` (`X8FB`) | – | 2 | 0 |
| `ShotMapZoneReference` | `0x62554755` (`bUGU`) | – | 3 | 0 |
| `ShuffleDraftLivePickReference` | `0x58585448` (`XXTH`) | – | 3 | 0 |
| `ShuffleDraftPickedPlayersInfoReference` | `0x51472058` (`QG X`) | – | 12 | 1 |
| `SigningOfTheSeasonReference` | `0x51525342` (`QRSB`) | – | 10 | 0 |
| `SigningsOfTheSeasonNewsReference` | `0x5a4c6137` (`ZLa7`) | – | 3 | 2 |
| `SliderInitialisationPropertiesReference` | `0x32496c6b` (`2Ilk`) | – | 3 | 0 |
| `SocialGroupDetailsReference` | `0x78567251` (`xVrQ`) | – | 6 | 0 |
| `SocialGroupReference` | `0x554c3142` (`UL1B`) | – | 8 | 0 |
| `SocialReactionReference` | `0x48635355` (`HcSU`) | – | 8 | 1 |
| `SortFieldReference` | `0x4f463953` (`OF9S`) | – | 2 | 0 |
| `SpeakToActionReference` | `0x72656164` (`read`) | – | 31 | 1 |
| `SpeakToActionsListReference` | `0x72656165` (`reae`) | – | 7 | 0 |
| `SpeakToActionsReference` | `0x51514a43` (`QQJC`) | – | 9 | 1 |
| `SpeakToQuickActionReference` | `0x4f53466a` (`OSFj`) | – | 2 | 0 |
| `SpeakToReference` | `0x6646634b` (`fFcK`) | – | 13 | 1 |
| `SpeakToSpeechBubbleReference` | `0x534e5063` (`SNPc`) | – | 3 | 0 |
| `SpecificallyScoutedPersonReference` | `0x7443314a` (`tC1J`) | – | 6 | 1 |
| `SpecificallyScoutedTeamReference` | `0x53434c4b` (`SCLK`) | – | 3 | 2 |
| `SpiderChartDataReference` | `0x73445777` (`sDWw`) | – | 2 | 0 |
| `SpiderChartLabelDataReference` | `0x566e3733` (`Vn73`) | – | 5 | 0 |
| `SpiderChartPlayerAttributesReference` | `0x54574147` (`TWAG`) | – | 13 | 1 |
| `SportsScientistTeamReportNewsReference` | `0x6e347455` (`n4tU`) | – | 4 | 0 |
| `SquadDynamicsProConsReference` | `0x2031594a` (` 1YJ`) | – | 2 | 0 |
| `SquadFilterRuleReference` | `0x73716672` (`sqfr`) | – | 1 | 0 |
| `SquadInternationalEventNewsReference` | `0x4e327855` (`N2xU`) | – | 2 | 0 |
| `SquadInternationalEventReference` | `0x49765954` (`IvYT`) | – | 4 | 1 |
| `SquadNumberReference` | `0x7341774d` (`sAwM`) | – | 4 | 1 |
| `SquadNumbersEditSessionReference` | `0x43436277` (`CCbw`) | – | 19 | 3 |
| `SquadOverviewPlayerDropdownRowReference` | `0x596d5976` (`YmYv`) | – | 3 | 0 |
| `SquadOverviewPlayerReference` | `0x43305066` (`C0Pf`) | – | 13 | 1 |
| `SquadPlanAnalysisReference` | `0x31683378` (`1h3x`) | – | 4 | 0 |
| `SquadPlannerCurrentPlanReference` | `0x5a664453` (`ZfDS`) | – | 4 | 1 |
| `SquadPlannerFullSquadPositionReference` | `0x466b3067` (`Fk0g`) | – | 5 | 0 |
| `SquadPlannerOverviewIssueReference` | `0x4a394937` (`J9I7`) | – | 3 | 0 |
| `SquadPlannerOverviewPositionReference` | `0x52697732` (`Riw2`) | – | 2 | 0 |
| `SquadPlannerPositionAnalysisReference` | `0x7a425745` (`zBWE`) | – | 9 | 1 |
| `SquadPlannerReference` | `0x58643954` (`Xd9T`) | – | 24 | 0 |
| `SquadPositionDepthAndQualityOverviewReference` | `0x53464b55` (`SFKU`) | – | 8 | 0 |
| `SquadPositionDepthReference` | `0x726f6158` (`roaX`) | – | 4 | 0 |
| `SquadRegistrationPlayersReference` | `0x71447752` (`qDwR`) | – | 2 | 1 |
| `SquadRegistrationRuleComplianceReference` | `0x41536e47` (`ASnG`) | – | 4 | 0 |
| `SquadRuleReference` | `0x30633956` (`0c9V`) | – | 7 | 0 |
| `SquadSelectionRulesAllCompsCompReference` | `0x66485948` (`fHYH`) | – | 3 | 1 |
| `SquadSelectionRulesAllCompsCompRulesReference` | `0x5a773548` (`Zw5H`) | – | 5 | 0 |
| `SquadSelectionWarningNewsReference` | `0x41424e58` (`ABNX`) | – | 8 | 0 |
| `StadiumReference` | `0x44420015` | – | 22 | 0 |
| `StaffCoachingQualificationReference` | `0x55344343` (`U4CC`) | – | 8 | 0 |
| `StaffHistoryReference` | `0x4f654279` (`OeBy`) | – | 6 | 0 |
| `StaffMeetingAdviceNewsReference` | `0x20576268` (` Wbh`) | – | 4 | 0 |
| `StaffMeetingAllCategoriesReference` | `0x77446c78` (`wDlx`) | – | 5 | 1 |
| `StaffMeetingCategoryReference` | `0x66637170` (`fcqp`) | – | 4 | 0 |
| `StaffMeetingReference` | `0x7048644f` (`pHdO`) | – | 9 | 1 |
| `StaffMeetingSuggestionReference` | `0x6c506c65` (`lPle`) | – | 12 | 0 |
| `StaffMeetingSuggestionSubjectReference` | `0x6d6f4879` (`moHy`) | – | 2 | 0 |
| `StaffMeetingTopicReference` | `0x38717548` (`8quH`) | – | 4 | 0 |
| `StaffNumberChangedDataReference` | `0x69746c4c` (`itlL`) | – | 7 | 0 |
| `StaffNumberChangedNewsReference` | `0x594a2041` (`YJ A`) | – | 2 | 2 |
| `StaffNumbersInfoReference` | `0x4a515749` (`JQWI`) | – | 3 | 0 |
| `StaffRoleReference` | `0x756e6934` (`uni4`) | – | 3 | 0 |
| `StaffSubGroupComparisonReference` | `0x304f536e` (`0OSn`) | – | 6 | 1 |
| `StaffSubGroupReference` | `0x53747347` (`StsG`) | – | 11 | 1 |
| `StageNameReference` | `0x44420017` | – | 0 | 0 |
| `StageRuleReference` | `0x686b666a` (`hkfj`) | – | 2 | 0 |
| `StarPlayerContractDebugReference` | `0x7662516c` (`vbQl`) | – | 4 | 1 |
| `StarRangeReference` | `0x53545247` (`STRG`) | – | 3 | 0 |
| `StartDateReference` | `0x73746474` (`stdt`) | – | 3 | 1 |
| `StaticDataReference` | `0x47373046` (`G70F`) | – | 50 | 0 |
| `StaticStringReference` | `0x71525155` (`qRQU`) | – | 11 | 0 |
| `StepComponentReference` | `0x42415646` (`BAVF`) | – | 3 | 0 |
| `StoreItemApplyRestrictionReference` | `0x34506257` (`4PbW`) | – | 2 | 0 |
| `StoreItemReference` | `0x7967796d` (`ygym`) | – | 17 | 0 |
| `StoreReference` | `0x6e7a6e6b` (`nznk`) | – | 16 | 2 |
| `StringListWithSeverityReference` | `0x44416820` (`DAh `) | – | 2 | 0 |
| `SuggestedNationalSquadNewsReference` | `0x4a733971` (`Js9q`) | – | 2 | 1 |
| `SuggestedNationalSquadPlayerReference` | `0x64555349` (`dUSI`) | – | 2 | 1 |
| `SummaryAmountReference` | `0x35564539` (`5VE9`) | – | 5 | 0 |
| `SupporterProfileReference` | `0x63764542` (`cvEB`) | – | 15 | 0 |
| `SupportersFeedbackReference` | `0x5a4d4d61` (`ZMMa`) | – | 3 | 0 |
| `SwapTableReference` | `0x38705856` (`8pXV`) | – | 2 | 0 |
| `TacticActiveTweakAbsoluteOverrideReference` | `0x61547741` (`aTwA`) | – | 1 | 0 |
| `TacticActiveTweakReference` | `0x61547752` (`aTwR`) | – | 8 | 2 |
| `TacticActiveTweakShiftOverrideReference` | `0x61547753` (`aTwS`) | – | 2 | 0 |
| `TacticNameDisplayAndPropertyValueReference` | `0x4d526953` (`MRiS`) | – | 4 | 1 |
| `TacticReference` | `0x77725342` (`wrSB`) | – | 238 | 3 |
| `TacticSelectedPlayersFitnessReference` | `0x69753170` (`iu1p`) | – | 5 | 0 |
| `TacticalEffectivenessAdviceReference` | `0x76494242` (`vIBB`) | – | 4 | 0 |
| `TacticalEffectivenessKeyFactorReference` | `0x41486570` (`AHep`) | – | 4 | 2 |
| `TacticalEffectivenessNextMatchInformationReference` | `0x5a763074` (`Zv0t`) | – | 5 | 1 |
| `TacticalEffectivenessPlayerAbilityReference` | `0x75436632` (`uCf2`) | – | 7 | 1 |
| `TacticalEffectivenessPlayerBuyInReference` | `0x69697657` (`iivW`) | – | 9 | 1 |
| `TacticalEffectivenessReference` | `0x32386475` (`28du`) | – | 7 | 1 |
| `TacticalEffectivenessScoreReference` | `0x36423258` (`6B2X`) | – | 3 | 0 |
| `TacticalEffectivenessStatusFlagsReference` | `0x2063494f` (` cIO`) | – | 9 | 0 |
| `TacticalEffectivenessTacticalComplexityReference` | `0x54623156` (`Tb1V`) | – | 5 | 0 |
| `TacticalEffectivenessTacticalComprehensionReference` | `0x30724a72` (`0rJr`) | – | 4 | 0 |
| `TacticalEffectivenessTacticalTypeScoresReference` | `0x496f5130` (`IoQ0`) | – | 4 | 0 |
| `TacticalEffectivenessTacticalUnderstandingReference` | `0x77574d48` (`wWMH`) | – | 16 | 1 |
| `TacticalEffectivenessTopPositionRowReference` | `0x62524f52` (`bROR`) | – | 3 | 2 |
| `TacticalPositionSimplifiedDataReference` | `0x4c796a20` (`Lyj `) | – | 4 | 1 |
| `TacticalStyleDeviationSuggestionReference` | `0x6b593420` (`kY4 `) | – | 4 | 0 |
| `TacticsGridSquareDetailedReference` | `0x5663674d` (`VcgM`) | – | 13 | 0 |
| `TacticsGridSquareItemReference` | `0x45557862` (`EUxb`) | – | 4 | 1 |
| `TacticsGridSquareReference` | `0x65573250` (`eW2P`) | – | 7 | 0 |
| `TacticsOppositionPlayerInstructionsReference` | `0x6170326f` (`ap2o`) | – | 4 | 0 |
| `TacticsOppositionSpecificInstructionsReference` | `0x5053704e` (`PSpN`) | – | 17 | 1 |
| `TacticsPlayerInstructionOptionReference` | `0x58c1e541` | – | 4 | 0 |
| `TacticsPlayerSelectionReference` | `0x6b68437a` (`khCz`) | – | 5 | 1 |
| `TacticsPositionAwardInformationReference` | `0x316f4568` (`1oEh`) | – | 3 | 0 |
| `TacticsPositionCombinedReference` | `0x3356344c` (`3V4L`) | `ITacticsTeamSelectionReference` | 14 | 0 |
| `TacticsPositionMatchInformationReference` | `0x38526832` (`8Rh2`) | – | 6 | 1 |
| `TacticsPositionReference` | `0x3645526b` (`6ERk`) | `ITacticsTeamSelectionReference` | 12 | 0 |
| `TacticsRoleReference` | `0x584f7461` (`XOta`) | – | 4 | 0 |
| `TacticsTeamSelectionIndexReference` | `0x37414445` (`7ADE`) | – | 4 | 1 |
| `TacticsTeamSelectionReference` | `0x524b6975` (`RKiu`) | `ITacticsTeamSelectionReference` | 6 | 0 |
| `TacticsTeamSelectionTableReference` | `0x61625779` (`abWy`) | – | 7 | 0 |
| `TargetsListsReference` | `0x384a6d36` (`8Jm6`) | – | 3 | 0 |
| `TddAgentOfferedPlayerReference` | `0x4f784f71` (`OxOq`) | – | 4 | 1 |
| `TddAgentOfferedPlayersNewsReference` | `0x326c4e68` (`2lNh`) | – | 3 | 3 |
| `TddAgentOfferedPlayersReference` | `0x4d657650` (`MevP`) | – | 2 | 1 |
| `TddAgentsOfferedPlayersPerTimeSliceReference` | `0x6b677956` (`kgyV`) | – | 2 | 0 |
| `TddAgentsOfferedPlayersReference` | `0x6e504f37` (`nPO7`) | – | 3 | 0 |
| `TeamAndPlayersReference` | `0x4b6f6d6e` (`Komn`) | – | 2 | 1 |
| `TeamConfidenceReference` | `0x65204f76` (`e Ov`) | – | 69 | 1 |
| `TeamContainerAwardWinnerReference` | `0x68694f68` (`hiOh`) | – | 4 | 1 |
| `TeamContainerHonoursListReference` | `0x6e4a6474` (`nJdt`) | – | 4 | 0 |
| `TeamContainerHonoursReference` | `0x59394f69` (`Y9Oi`) | – | 5 | 0 |
| `TeamContainerHonoursYearsReference` | `0x33204477` (`3 Dw`) | – | 2 | 0 |
| `TeamContainerLandmarksReference` | `0x53453546` (`SE5F`) | – | 2 | 0 |
| `TeamCurrentInjuryDataReference` | `0x376e4c78` (`7nLx`) | – | 16 | 0 |
| `TeamFixtureReference` | `0x36376a79` (`67jy`) | – | 2 | 0 |
| `TeamGeneralPerformanceDataPointReference` | `0x31202020` (`1   `) | – | 3 | 0 |
| `TeamMatchVisualisationDataReference` | `0x6c486241` (`lHbA`) | – | 9 | 0 |
| `TeamNewsRecordReference` | `0x35344269` (`54Bi`) | – | 3 | 0 |
| `TeamPlayerConfidenceReference` | `0x4a77616e` (`Jwan`) | – | 5 | 1 |
| `TeamReference` | `0x44420018` | – | 478 | 68 |
| `TeamReportAssistDataReference` | `0x44494576` (`DIEv`) | – | 3 | 1 |
| `TeamReportGoalDataReference` | `0x45506e72` (`EPnr`) | – | 4 | 0 |
| `TeamReportGoalPositionsListReference` | `0x4c545566` (`LTUf`) | – | 14 | 0 |
| `TeamReportStatReference` | `0x466c4b6a` (`FlKj`) | – | 3 | 0 |
| `TeamReportStatsReference` | `0x5a446831` (`ZDh1`) | – | 14 | 1 |
| `TeamSelectionAdviceEntryReference` | `0x7933394b` (`y39K`) | – | 5 | 1 |
| `TeamSettingsEditSessionAdviceAndReportsReference` | `0x43717165` (`Cqqe`) | – | 15 | 2 |
| `TeamSettingsEditSessionAdviceGiverRowReference` | `0x68503755` (`hP7U`) | – | 4 | 1 |
| `TeamSettingsEditSessionAdviceToggleRowReference` | `0x716d5370` (`qmSp`) | – | 2 | 0 |
| `TeamSettingsEditSessionCustomiseAdviceReference` | `0x4c724363` (`LrCc`) | – | 3 | 1 |
| `TeamSettingsEditSessionIndividualResponsibilityReference` | `0x4f4a6349` (`OJcI`) | – | 9 | 1 |
| `TeamSettingsEditSessionOfferToClubsReference` | `0x454c704a` (`ELpJ`) | – | 34 | 1 |
| `TeamSettingsEditSessionReference` | `0x6f62476b` (`obGk`) | – | 16 | 1 |
| `TeamSettingsEditSessionResponsibilityGroupReference` | `0x73206c61` (`s la`) | – | 12 | 2 |
| `TeamSettingsEditSessionResponsibilityHumanPreferencesReference` | `0x4b74624b` (`KtbK`) | – | 16 | 1 |
| `TeamSettingsEditSessionResponsibilityTabReference` | `0x5930566c` (`Y0Vl`) | – | 4 | 1 |
| `TeamSettingsStaffMemberResponsibilitiesReference` | `0x664b6b68` (`fKkh`) | – | 3 | 1 |
| `TeamSquadReference` | `0x63725858` (`crXX`) | – | 4 | 0 |
| `TeamTacticReference` | `0x77725343` (`wrSC`) | – | 0 | 0 |
| `TeamTalkPlayerReactionReference` | `0x66555567` (`fUUg`) | – | 9 | 0 |
| `TeamTalkReference` | `0x5a47636e` (`ZGcn`) | – | 10 | 1 |
| `TeamTouchlineShoutReference` | `0x38686638` (`8hf8`) | – | 7 | 0 |
| `TeamTrainingReference` | `0x36796c31` (`6yl1`) | – | 51 | 4 |
| `TeamWithIndexReference` | `0x6d6b614c` (`mkaL`) | – | 2 | 1 |
| `TextWithHintReference` | `0x35344268` (`54Bh`) | – | 2 | 0 |
| `TopPerformerReference` | `0x676d4a7a` (`gmJz`) | – | 4 | 1 |
| `TopPlayersInTheWorldNewsReference` | `0x61714564` (`aqEd`) | – | 2 | 1 |
| `TotalToRatioReference` | `0x6c665437` (`lfT7`) | – | 2 | 0 |
| `TradeAssetsReference` | `0x44586941` (`DXiA`) | – | 2 | 0 |
| `TradeOfferAssetReference` | `0x5a6b7947` (`ZkyG`) | – | 12 | 0 |
| `TradeOfferEditSessionReference` | `0x45416f48` (`EAoH`) | – | 32 | 0 |
| `TradeOfferReference` | `0x596a5847` (`YjXG`) | – | 2 | 1 |
| `TradeOfferTransferOfferReference` | `0x67504b75` (`gPKu`) | – | 2 | 1 |
| `TrainingAdditionalFocusReference` | `0x36373436` (`6746`) | – | 8 | 0 |
| `TrainingCategoryCoachRatingsReference` | `0x4d426744` (`MBgD`) | – | 9 | 1 |
| `TrainingCategoryWorkloadsReference` | `0x3975444d` (`9uDM`) | – | 9 | 0 |
| `TrainingDayScheduleReference` | `0x74727363` (`trsc`) | – | 6 | 1 |
| `TrainingEditSelectionReference` | `0x374e4452` (`7NDR`) | – | 2 | 0 |
| `TrainingIntensityConditionReference` | `0x657a6331` (`ezc1`) | – | 3 | 1 |
| `TrainingIntensityConditionSelectionReference` | `0x4374486e` (`CtHn`) | – | 3 | 0 |
| `TrainingIntensityDropdownRowReference` | `0x4f57726c` (`OWrl`) | – | 5 | 0 |
| `TrainingIntensityOrRestReference` | `0x74697272` (`tirr`) | – | 13 | 1 |
| `TrainingPlayerRatingReference` | `0x4f686964` (`Ohid`) | – | 2 | 2 |
| `TrainingPositionReference` | `0x6a584459` (`jXDY`) | – | 15 | 2 |
| `TrainingProgressReportReference` | `0x4e663365` (`Nf3e`) | – | 26 | 2 |
| `TrainingRatingAndColourReference` | `0x78356676` (`x5fv`) | – | 2 | 0 |
| `TrainingScheduleImpactReference` | `0x79524536` (`yRE6`) | – | 5 | 0 |
| `TrainingSessionDetailsReference` | `0x336c6466` (`3ldf`) | – | 10 | 2 |
| `TrainingSessionReference` | `0x4e7a4c42` (`NzLB`) | – | 3 | 1 |
| `TrainingUnitReference` | `0x63346768` (`c4gh`) | – | 6 | 0 |
| `TrainingWeekScheduleReference` | `0x4e575935` (`NWY5`) | – | 9 | 1 |
| `TransferActivityPersonReference` | `0x6c594c37` (`lYL7`) | – | 27 | 2 |
| `TransferActivityReference` | `0x63716c71` (`cqlq`) | – | 54 | 0 |
| `TransferActivityTeamActivityReference` | `0x69737573` (`isus`) | – | 14 | 1 |
| `TransferActivityTradeOfferReference` | `0x32594274` (`2YBt`) | – | 13 | 0 |
| `TransferActivityTransferOfferReference` | `0x51324443` (`Q2DC`) | – | 37 | 0 |
| `TransferBlockedDueToStaffLimitsPersonToReplaceReference` | `0x6856657a` (`hVez`) | – | 4 | 1 |
| `TransferBlockedDueToStaffLimitsReference` | `0x4b58636e` (`KXcn`) | – | 8 | 1 |
| `TransferConfidenceFeedbackReference` | `0x64527741` (`dRwA`) | – | 2 | 0 |
| `TransferConfidenceReference` | `0x336e5549` (`3nUI`) | – | 13 | 0 |
| `TransferInOutOverviewReference` | `0x50683963` (`Ph9c`) | – | 3 | 0 |
| `TransferInOutOverviewTypeReference` | `0x51783565` (`Qx5e`) | – | 3 | 0 |
| `TransferInOutReference` | `0x53675335` (`SgS5`) | – | 10 | 0 |
| `TransferListDateSelectorItemReference` | `0x4c6e3446` (`Ln4F`) | – | 3 | 0 |
| `TransferListOverviewReference` | `0x546d4238` (`TmB8`) | – | 2 | 0 |
| `TransferOfferActionButtonPropsReference` | `0x54416250` (`TAbP`) | – | 4 | 0 |
| `TransferOfferClauseReference` | `0x544f436c` (`TOCl`) | – | 17 | 0 |
| `TransferOfferClientContextReference` | `0x54636352` (`TccR`) | – | 3 | 0 |
| `TransferOfferCommentReference` | `0x544f6352` (`TOcR`) | – | 3 | 0 |
| `TransferOfferCompetitionBonusReference` | `0x354c6b4d` (`5LkM`) | – | 3 | 1 |
| `TransferOfferEditSessionReference` | `0x546e6752` (`TngR`) | – | 137 | 2 |
| `TransferOfferExchangedPersonReference` | `0x54657052` (`TepR`) | – | 6 | 1 |
| `TransferOfferPotentialExchangePersonReference` | `0x4e663965` (`Nf9e`) | – | 6 | 1 |
| `TransferRoomAdvertPositionSelectorReference` | `0x79436e31` (`yCn1`) | – | 4 | 0 |
| `TransferRoomAdvertReference` | `0x54526164` (`TRad`) | – | 38 | 1 |
| `TransferRoomAdvertResponseReference` | `0x595a4432` (`YZD2`) | – | 2 | 1 |
| `TransferRoomPitchActivityReference` | `0x446a3957` (`Dj9W`) | – | 10 | 1 |
| `TransferRoomReference` | `0x47486237` (`GHb7`) | – | 35 | 1 |
| `TransferRumourReference` | `0x37717551` (`7quQ`) | – | 9 | 0 |
| `TransferValueRangeReference` | `0x6d485049` (`mHPI`) | – | 15 | 1 |
| `TransferWindowAverageFeeReference` | `0x49454849` (`IEHI`) | – | 3 | 1 |
| `TransferWindowBigDealReference` | `0x3976506a` (`9vPj`) | – | 4 | 0 |
| `TransferWindowForeignImportReference` | `0x42685664` (`BhVd`) | – | 3 | 1 |
| `TransferWindowHeadlineStoryReference` | `0x334e4530` (`3NE0`) | – | 7 | 0 |
| `TransferWindowHistoryReference` | `0x4a733630` (`Js60`) | – | 10 | 1 |
| `TransferWindowNetSpendReference` | `0x74416c30` (`tAl0`) | – | 4 | 1 |
| `TransferWindowPlayerReference` | `0x726f6d63` (`romc`) | – | 2 | 1 |
| `TransferWindowReference` | `0x74667773` (`tfws`) | – | 20 | 1 |
| `TransferWindowTotalSpendReference` | `0x6b785842` (`kxXB`) | – | 3 | 1 |
| `TransferWindowTotalTransfersReference` | `0x4120564e` (`A VN`) | – | 7 | 1 |
| `TutorialManagerReference` | `0x4c507a59` (`LPzY`) | – | 1 | 1 |
| `TutorialReference` | `0x78586849` (`xXhI`) | – | 9 | 1 |
| `TutorialStepReference` | `0x5a456759` (`ZEgY`) | – | 5 | 0 |
| `UEFAClubCoefficientEntryReference` | `0x75636365` (`ucce`) | – | 18 | 1 |
| `UpcomingCompetitionsToScoutReference` | `0x724c6e4f` (`rLnO`) | – | 3 | 2 |
| `UpcomingMatchOpinionReference` | `0x445a6d5a` (`DZmZ`) | – | 4 | 0 |
| `UserRequiredTaskReference` | `0x434c4742` (`CLGB`) | – | 14 | 0 |
| `ValueCountReference` | `0x61767267` (`avrg`) | – | 2 | 0 |
| `ValueCountSortReference` | `0x47424a50` (`GBJP`) | – | 3 | 0 |
| `VersusModeFormatReference` | `0x766d666f` (`vmfo`) | – | 4 | 0 |
| `VisionFfpObjectivesDataReference` | `0x626d7a6c` (`bmzl`) | – | 3 | 1 |
| `VisualisationDropdownReference` | `0x6a41544f` (`jATO`) | – | 2 | 0 |
| `WorkPermitReference` | `0x6e636575` (`nceu`) | – | 23 | 0 |
| `XgStoryPointsReference` | `0x70756259` (`pubY`) | – | 8 | 0 |
| `XgStoryReference` | `0x76442070` (`vD p`) | – | 14 | 1 |
| `XgTableDataAnalysisReference` | `0x56674e43` (`VgNC`) | – | 4 | 1 |
| `XgTableListReference` | `0x57783368` (`Wx3h`) | – | 3 | 1 |
| `XgTableReference` | `0x6851674f` (`hQgO`) | – | 4 | 1 |
| `YearDataReference` | `0x79737461` (`ysta`) | – | 2 | 0 |
| `YouthCandidatesPositionPreviewReference` | `0x70455453` (`pETS`) | – | 7 | 0 |
| `YouthCandidatesPreviewReference` | `0x5636736d` (`V6sm`) | – | 6 | 1 |
| `YouthCandidatesSuggestedNewsReference` | `0x62367649` (`b6vI`) | – | 3 | 0 |
| `YouthPromotedReference` | `0x516d6354` (`QmcT`) | – | 2 | 2 |
| `ZoneMapReference` | `0x7a693252` (`zi2R`) | – | 8 | 1 |
| `ZoneMapZoneReference` | `0x37655137` (`7eQ7`) | – | 2 | 0 |

### 5.1 En çok property'ye sahip 25 varlık

| Sınıf | Property | Çocuk varlık |
|---|---:|---:|
| `PersonReference` | 1,287 | 103 |
| `IPlayerReference` | 997 | 84 |
| `INonPlayerReference` | 577 | 56 |
| `ClubReference` | 516 | 55 |
| `TeamReference` | 478 | 68 |
| `IAgentReference` | 323 | 4 |
| `IOfficialReference` | 317 | 3 |
| `IJournalistReference` | 313 | 3 |
| `IPersonBaseReference` | 310 | 3 |
| `CompReference` | 308 | 1 |
| `TacticReference` | 238 | 3 |
| `ConfigReference` | 173 | 0 |
| `CharacterSettingsReference` | 169 | 0 |
| `SettingsReference` | 140 | 0 |
| `TransferOfferEditSessionReference` | 137 | 2 |
| `NationalTeamContainerReference` | 134 | 1 |
| `GameReference` | 131 | 3 |
| `ContractReference` | 128 | 1 |
| `SetupGameReference` | 124 | 0 |
| `MatchReference` | 123 | 2 |
| `FixtureReference` | 119 | 1 |
| `ContractEditSessionReference` | 112 | 1 |
| `RecruitmentFocusItemReference` | 101 | 2 |
| `ITeamContainerReference` | 95 | 1 |
| `PlayerMatchStatsReference` | 82 | 1 |

## 6. Kayıtlı binding context'leri

Context'ler, parametreli property'lere (ör. bir takım veya tarih bağlamında hesaplanan değerler) verilen anahtarlardır.

| Context | FourCC |
|---|---|
| `ActionsSection` | `0x57625654` |
| `activenations` | `0x61636e74` |
| `ActivityTransferType` | `0x6d46666b` |
| `AddAnyDropdownOption` | `0x30765a49` |
| `AddOnType` | `0x41676d32` |
| `AdjustPlayerSearchSuggestionsForCurrentFilter` | `0x56534674` |
| `AdvertTransferType` | `0x6c355447` |
| `AdviceDeliveryType` | `0x50704276` |
| `AgentType` | `0x62764278` |
| `AllowSpecialPlayers` | `0x35586a4c` |
| `Award` | `0x6c36666b` |
| `Binding` | `0x6f49754a` |
| `Boolean` | `0x4d695538` |
| `BuyinDebugLevelUpdated` | `0x4e496678` |
| `BuyingClub` | `0x43627963` |
| `BuyingTeam` | `0x51684134` |
| `CalendarEvent` | `0x78426f66` |
| `Category` | `0x4f756854` |
| `club` | `0x636c7562` |
| `ClubsToInclude` | `0x65705239` |
| `ClubVisionNegotiationType` | `0x43396e4f` |
| `ComparisonClub` | `0x4a6b4467` |
| `ComparisonPerson` | `0x584f6352` |
| `Competition` | `0x63306d70` |
| `CompetitionList` | `0x56305157` |
| `ConditionRange` | `0x4e687831` |
| `Context` | `0x70516378` |
| `Continent` | `0x6e6a544d` |
| `ContinueFlowMode` | `0x35336478` |
| `ContractDemandType` | `0x4146206d` |
| `DatabaseTableType` | `0x31334335` |
| `Date` | `0x6e4d7a54` |
| `DateFormat` | `0x686b4c68` |
| `DateOfBirth` | `0x79414239` |
| `Day` | `0x73575733` |
| `DaysAfterWindowCloses` | `0x47415a33` |
| `DBSummaryCompetition` | `0x50414479` |
| `DBSummaryNation` | `0x50414474` |
| `DBSummarySecondNation` | `0x50414475` |
| `DBSummaryThirdNation` | `0x50414476` |
| `DebugSearchID` | `0x6f323550` |
| `DraftIdentifier` | `0x4751726d` |
| `DraggedContext` | `0x456d6c37` |
| `EditingLanguage` | `0x65303546` |
| `ExchangePlayerListFilter` | `0x6c395766` |
| `FifthLanguage` | `0x31556444` |
| `FileType` | `0x666c7479` |
| `FilterListID` | `0x4751726e` |
| `FirstChoiceAnalysis` | `0x6c365649` |
| `FirstLanguage` | `0x635a4967` |
| `FirstName` | `0x42454d48` |
| `FiveYearViewMode` | `0x4751726c` |
| `FixtureHasResult` | `0x446a484b` |
| `FixturePadding` | `0x4a423370` |
| `FixturesDropdown` | `0x62454176` |
| `Folder` | `0x666f6c64` |
| `format` | `0x3720202a` |
| `Formation` | `0x734d6d79` |
| `FourthLanguage` | `0x31594975` |
| `FutureAmount` | `0x62497974` |
| `FutureTransferMode` | `0x796f784a` |
| `Gender` | `0x67656e64` |
| `HideUnselectedPlayers` | `0x74783641` |
| `HighlightHumanPlayers` | `0x686c686d` |
| `HighlightSquadStatusFlags` | `0x686c7373` |
| `human` | `0x50625059` |
| `HumanTeam` | `0x5242464a` |
| `ID` | `0x69642020` |
| `Index` | `0x696e6478` |
| `InPossession` | `0x6b796454` |
| `InteractionTopic` | `0x6e366d32` |
| `InteractionType` | `0x6d544e43` |
| `IPPosition` | `0x6f653063` |
| `IPRole` | `0x46324646` |
| `IPTacticSlot` | `0x77326471` |
| `IsForcedScreen` | `0x42455232` |
| `IsGoalkeeper` | `0x4465545a` |
| `isHomeTeam` | `0x43696874` |
| `IsPlayerRecruitment` | `0x316c3263` |
| `IsQuick` | `0x446a484c` |
| `IsTeamVisuals` | `0x31483770` |
| `Items` | `0x5420676e` |
| `Job` | `0x7767344f` |
| `JobType` | `0x514b7773` |
| `Judge` | `0x51515478` |
| `KitType` | `0x4659306a` |
| `LeagueTableType` | `0x6c677479` |
| `LocalTeam` | `0x4c745a4d` |
| `LogChannelFlagsValue` | `0x38423954` |
| `LongStringID` | `0x51656966` |
| `MainStageIndex` | `0x6d736769` |
| `ManagerPrinciples` | `0x484d6e50` |
| `MaxFailedChecks` | `0x56326d6a` |
| `MentoringGroupPlayerOneID` | `0x594a6944` |
| `MentoringGroupPlayerTwoID` | `0x77526956` |
| `MilestoneClubList` | `0x57516447` |
| `MilestoneID` | `0x57516446` |
| `MindsetID` | `0x57516434` |
| `Mode` | `0x74483035` |
| `Month` | `0x3336466f` |
| `MonthIndex` | `0x6d506451` |
| `Name` | `0x35202020` |
| `Nation` | `0x77324b58` |
| `NegotiationStage` | `0x7265564c` |
| `NewsContextTeam` | `0x62316554` |
| `NewsItemUniqueId` | `0x6a774e4b` |
| `NextSeason` | `0x6e787365` |
| `Number` | `0x42647670` |
| `NumberOfRecruitmentFocusBasicSuggestions` | `0x52666273` |
| `NumberToReturn` | `0x4b737347` |
| `NumPositionRoleSuggestions` | `0x54715044` |
| `NumSimilarToSuggestions` | `0x30306470` |
| `onepergender` | `0x4f6e7067` |
| `OnlyShowPreseasonFixtures` | `0x56574874` |
| `OpportunitiesTransferType` | `0x6b354966` |
| `OppoTeam` | `0x30416e74` |
| `OtherClub` | `0x4a325a52` |
| `Panel` | `0x336f454a` |
| `Person` | `0x586b6961` |
| `PitchLength` | `0x794b345a` |
| `PitchPositionX` | `0x616c364d` |
| `PitchPositionY` | `0x76325545` |
| `PitchWidth` | `0x674b684e` |
| `PlayerImportance` | `0x44447a48` |
| `PlayerIndex` | `0x494c6959` |
| `PlayerInstructionGroupID` | `0x5455594c` |
| `PlayerInstructionOptionID` | `0x32355034` |
| `PlayerSelectionPosition` | `0x4d7a4d4d` |
| `PlayerSelectionRole` | `0x35584d4f` |
| `PlayerSquadSelectionValue` | `0x7a514350` |
| `PlayerStatsScope` | `0x6b615877` |
| `PortalMessagesTab` | `0x354b3667` |
| `PositionIndex` | `0x41767443` |
| `PositionMask` | `0x666e7152` |
| `PositionMask2` | `0x4c616a61` |
| `PossessionMode` | `0x4e395650` |
| `PotentialConversation` | `0x6d554239` |
| `PressConferenceId` | `0x4f765173` |
| `PreviousAmount` | `0x74427858` |
| `PrimaryJob` | `0x61557768` |
| `PrimaryTeamType` | `0x4467594c` |
| `ProposedAffiliateViewpoint` | `0x78366a74` |
| `RecentPlayerList` | `0x784c4339` |
| `Record` | `0x7265636f` |
| `Records` | `0x52207072` |
| `RecruitmentFocusID` | `0x20654373` |
| `RecruitmentFocusIDList` | `0x704c7349` |
| `ResultsToShow` | `0x346f7a4c` |
| `Role` | `0x726f6c65` |
| `RoleMask` | `0x47726d66` |
| `Scout` | `0x78653545` |
| `SearchValue` | `0x574d3432` |
| `SecondaryJob` | `0x446c4c32` |
| `SecondaryTeamType` | `0x644b6d44` |
| `SecondLanguage` | `0x59774944` |
| `SecondName` | `0x78567579` |
| `SelectedBan` | `0x3178327a` |
| `SelectedLoadScope` | `0x6e6f4235` |
| `SelectedObject` | `0x5a766474` |
| `SelectedObjectList` | `0x4d70504c` |
| `SelectedPlayersMindsetTally` | `0x7642564f` |
| `SelectedSave` | `0x666c6e6d` |
| `SelectedSaveMethod` | `0x50316e6c` |
| `SelectedTab` | `0x77485744` |
| `SelectedTabIndex` | `0x76726a64` |
| `SellingClub` | `0x43736c63` |
| `SellingTeam` | `0x4a506d52` |
| `ServerEndPeriod` | `0x6b796457` |
| `ServerGameMode` | `0x6b796459` |
| `ServerHideLocked` | `0x6b79645a` |
| `ServerHost` | `0x6b796458` |
| `ServerMaxConnections` | `0x6b796455` |
| `ServerStartPeriod` | `0x6b796456` |
| `SetPieceInstructionCategory` | `0x4e68206b` |
| `SetPiecePitchSide` | `0x6671424a` |
| `SetPieceRoutineIndex` | `0x42725665` |
| `SetPieceScenario` | `0x6b65444a` |
| `SetPieceType` | `0x33775532` |
| `ShortStringID` | `0x5a4c4f46` |
| `ShowAllEventTypes` | `0x666a5830` |
| `ShowAllPositions` | `0x59464164` |
| `ShowCurrentTeamInstructions` | `0x4e77466d` |
| `ShowingSubs` | `0x73735459` |
| `ShowReducedOptions` | `0x71746d58` |
| `SixthLanguage` | `0x76494f34` |
| `SortBySelectedPhase` | `0x54556177` |
| `SpecificDatabaseObjectUID` | `0x4c674569` |
| `SquadDepthMaximumPlayerCount` | `0x5c8e95c2` |
| `SquadNumbersFilter` | `0x7a307341` |
| `SquadPlanType` | `0x3850574a` |
| `SquadSelectionRule` | `0x76764741` |
| `Stage` | `0x73746167` |
| `StageRulesType` | `0x73727463` |
| `StatCategory` | `0x584d716f` |
| `StatValue` | `0x4b695548` |
| `StringID` | `0x63675759` |
| `StringType` | `0x56434651` |
| `SubStageIndex` | `0x73736769` |
| `SubSubStageIndex` | `0x73737369` |
| `Tactic` | `0x46495847` |
| `TacticalStyle` | `0x5a576552` |
| `TacticData` | `0x4c4c6a67` |
| `TacticIndex` | `0x71534546` |
| `TacticsFeedbackCategory` | `0x44424759` |
| `TargetClub` | `0x4733636a` |
| `TargetsDebugShortlistSlot` | `0x2051465a` |
| `TargetType` | `0x61434f36` |
| `team` | `0x6979725a` |
| `TeamInstructionID` | `0x59314d52` |
| `TeamInstructionOptionID` | `0x56487642` |
| `TeamRequestingReport` | `0x6d434c76` |
| `TeamSelectionIndex` | `0x72487470` |
| `TeamToDrawPotFilter` | `0x43413962` |
| `ThirdLanguage` | `0x59704838` |
| `ThisPhase` | `0x61426476` |
| `TrainingDayIndex` | `0x6730456a` |
| `TrainingFocus` | `0x77565030` |
| `TrainingScheduleCategory` | `0x6c793152` |
| `TrainingScheduleIndex` | `0x35416a75` |
| `TrainingSessionCategory` | `0x6f6b4573` |
| `TrainingSessionDayIndex` | `0x39735275` |
| `TrainingSessionType` | `0x4f426570` |
| `TransferType` | `0x436b6f47` |
| `Type` | `0x74797065` |
| `UnpickedPositionsOnly` | `0x74653920` |
| `ViewID` | `0x36202020` |
| `VisionIsUsingPerformanceData` | `0x43567064` |
| `VisionObjectiveSetter` | `0x436f7473` |
| `VisionObjectiveType` | `0x436f7474` |
| `VisionObjectiveYear` | `0x436f7479` |
| `Year` | `0x3336466e` |
| `YearForFixtures` | `0x59724678` |
| `YearIndex` | `0x34427470` |

## 7. Binding property kayıt defteri

Toplam **9,126** FourCC ↔ property adı eşlemesi (`PropertyRegistration.Initialise`). Tam liste yerel `properties_and_contexts.json` dosyasındadır. Assembly dağılımı:

| Assembly | Property |
|---|---:|
| `FM.UI.dll` | 8,616 |
| `SI.Bindable.dll` | 317 |
| `FM.GameConfig.dll` | 191 |
| `FM.Lattice.dll` | 2 |

## 8. Enum dağılımı

| Assembly | Enum |
|---|---:|
| `UnityEngine.CoreModule.dll` | 232 |
| `mscorlib.dll` | 188 |
| `UnityEngine.UIElementsModule.dll` | 166 |
| `FM.UI.dll` | 142 |
| `System.dll` | 107 |
| `Unity.RenderPipelines.Universal.Runtime.dll` | 99 |
| `System.Xml.dll` | 86 |
| `SI.Bindable.dll` | 70 |
| `FM.Graphics.dll` | 64 |
| `ExCSS.Unity.dll` | 62 |
| `Unity.RenderPipelines.Core.Runtime.dll` | 61 |
| `Unity.InputSystem.dll` | 47 |
| `SI.UI.dll` | 47 |
| `Newtonsoft.Json.dll` | 36 |
| `SI.Core.dll` | 36 |
| `SI.Match.dll` | 34 |
| `UnityEngine.UI.dll` | 33 |
| `FM.Match.dll` | 32 |
| `System.Data.dll` | 29 |
| `MagicaClothV2.dll` | 27 |

## 9. Unity UI bundle envanteri

69 bundle, 164 asset yolu, 9,250 benzersiz UI binding yolu.
Ayrıca `ui-tablefactories_assets_all.bundle` içinde **220** `TableFactory` ve **2,102** `binding.*` sütun bağlaması; `ui-tableviews_assets_all.bundle` içinde **592** `TableView`/`TableSettings` şablonu yer alır.

| Bundle | Sıkıştırılmış | Açılmış | Asset yolu | Binding yolu |
|---|---:|---:|---:|---:|
| `shortcutdata_assets_all.bundle` | 14,995 | 39,024 | 0 | 0 |
| `sibindable_assets_all.bundle` | 2,422 | 5,684 | 0 | 1 |
| `ui-backgrounds_assets_.bundle` | 34,063,148 | 130,935,848 | 0 | 0 |
| `ui-backgrounds_assets_1x.bundle` | 315,615 | 3,084,368 | 0 | 0 |
| `ui-backgrounds_assets_2x.bundle` | 499,870 | 8,167,228 | 0 | 0 |
| `ui-backgrounds_assets_3x.bundle` | 921,959 | 18,367,232 | 0 | 0 |
| `ui-backgrounds_assets_4x.bundle` | 1,348,264 | 32,647,228 | 0 | 0 |
| `ui-backgrounds_assets_common.bundle` | 64,725,925 | 180,367,328 | 0 | 0 |
| `ui-bounds_assets_all.bundle` | 1,469 | 3,332 | 0 | 0 |
| `ui-calendar_assets_all.bundle` | 13,546 | 39,164 | 0 | 16 |
| `ui-credits_assets_all.bundle` | 129,400 | 627,772 | 0 | 0 |
| `ui-datacollections_assets_all.bundle` | 145,481 | 561,652 | 0 | 0 |
| `ui-dynamiccardcollections_assets_all.bundle` | 67,256 | 637,000 | 0 | 11 |
| `ui-factoryxml_assets_all.bundle` | 2,476 | 5,652 | 0 | 0 |
| `ui-fonts_assets_assets_uiassets_fonts_licenced_fifa_worldcup.bundle` | 5,760,019 | 34,166,552 | 0 | 0 |
| `ui-fonts_assets_bundesliga.bundle` | 135,112 | 1,226,860 | 0 | 0 |
| `ui-fonts_assets_efl.bundle` | 729,644 | 5,382,402 | 0 | 0 |
| `ui-fonts_assets_fmuniverse.bundle` | 301,413 | 1,536,924 | 0 | 0 |
| `ui-fonts_assets_premierleague.bundle` | 419,317 | 2,425,972 | 0 | 0 |
| `ui-fonts_assets_production.bundle` | 21,975,156 | 54,889,184 | 0 | 0 |
| `ui-fonts_assets_uefa_championsleague.bundle` | 214,717 | 1,249,372 | 0 | 0 |
| `ui-fonts_assets_uefa_europa.bundle` | 201,957 | 1,379,202 | 0 | 0 |
| `ui-fonts_assets_uefa_supercup.bundle` | 102,003 | 1,142,152 | 0 | 0 |
| `ui-fonts_assets_uefa_uwcl.bundle` | 134,349 | 226,948 | 0 | 0 |
| `ui-globalnavigation_assets_all.bundle` | 23,638 | 131,444 | 0 | 80 |
| `ui-icons_assets_.bundle` | 12,799 | 41,836 | 0 | 0 |
| `ui-icons_assets_1x.bundle` | 344,366 | 1,382,304 | 0 | 0 |
| `ui-icons_assets_2x.bundle` | 622,385 | 7,877,932 | 0 | 0 |
| `ui-icons_assets_3x.bundle` | 753,398 | 12,621,944 | 0 | 0 |
| `ui-icons_assets_4x.bundle` | 934,639 | 21,637,636 | 0 | 0 |
| `ui-icons_assets_common.bundle` | 1,223,785 | 6,970,652 | 0 | 0 |
| `ui-iconspriteatlases_assets_1x.bundle` | 1,211,882 | 1,584,616 | 0 | 0 |
| `ui-iconspriteatlases_assets_2x.bundle` | 2,431,654 | 3,109,084 | 0 | 0 |
| `ui-iconspriteatlases_assets_3x.bundle` | 3,637,664 | 4,793,324 | 0 | 0 |
| `ui-iconspriteatlases_assets_4x.bundle` | 4,594,485 | 6,153,000 | 0 | 0 |
| `ui-mainmenu-assets_assets_all.bundle` | 3,985,998 | 12,392,608 | 0 | 0 |
| `ui-managercreation_assets_all.bundle` | 151,996 | 499,796 | 0 | 0 |
| `ui-managercreationimages_assets_all.bundle` | 15,155,321 | 40,411,192 | 0 | 0 |
| `ui-match_assets_all.bundle` | 10,754 | 28,496 | 0 | 0 |
| `ui-panelids_assets_all.bundle` | 88,147 | 243,676 | 0 | 0 |
| `ui-prematch-backgrounds_assets_1x.bundle` | 3,483 | 9,476 | 0 | 0 |
| `ui-prematch-backgrounds_assets_2x.bundle` | 4,042 | 10,628 | 0 | 0 |
| `ui-prematch-backgrounds_assets_3x.bundle` | 4,367 | 11,288 | 0 | 0 |
| `ui-prematch-backgrounds_assets_4x.bundle` | 5,174 | 12,972 | 0 | 0 |
| `ui-prematch-backgrounds_assets_common.bundle` | 734,436 | 24,905,224 | 0 | 0 |
| `ui-settings_assets_all.bundle` | 9,360 | 31,988 | 0 | 2 |
| `ui-staticdataentries_assets_all.bundle` | 38,748 | 114,208 | 0 | 1 |
| `ui-styles_assets_.bundle` | 1,908 | 4,588 | 0 | 2 |
| `ui-styles_assets_1x.bundle` | 141,844 | 539,700 | 0 | 0 |
| `ui-styles_assets_2x.bundle` | 179,298 | 1,079,712 | 0 | 0 |
| `ui-styles_assets_3x.bundle` | 297,468 | 3,239,636 | 0 | 0 |
| `ui-styles_assets_4x.bundle` | 446,886 | 6,839,648 | 0 | 0 |
| `ui-styles_assets_common.bundle` | 336,264 | 1,023,124 | 0 | 2 |
| `ui-styles_assets_default.bundle` | 1,129,847 | 3,960,524 | 0 | 2 |
| `ui-styles_assets_match.bundle` | 14,012 | 43,448 | 0 | 0 |
| `ui-tablefactories_assets_all.bundle` | 184,783 | 866,568 | 0 | 2,185 |
| `ui-tableviews_assets_all.bundle` | 351,629 | 1,809,712 | 0 | 20 |
| `ui-tacticalanimations_assets_all.bundle` | 477,467 | 3,784,016 | 0 | 1 |
| `ui-tactics_assets_all.bundle` | 41,157 | 178,964 | 0 | 2 |
| `ui-textures_assets_all.bundle` | 10,851,086 | 80,141,872 | 0 | 0 |
| `ui-tifo-icons-controller-keyboard_assets_all.bundle` | 2,146 | 4,924 | 0 | 0 |
| `ui-tileslayouts_assets_all.bundle` | 933,147 | 2,960,532 | 0 | 120 |
| `ui-visualfunctions_assets_all.bundle` | 677,716 | 2,699,836 | 0 | 1 |
| `ui-visualtreeassets_assets_fantasydraftvisualtreeassetpreload.bundle` | 173,293 | 1,215,908 | 20 | 242 |
| `ui-visualtreeassets_assets_gameworldvisualtreeassetpreload.bundle` | 9,332,777 | 69,707,004 | 53 | 5,318 |
| `ui-visualtreeassets_assets_globalvisualtreeassetpreload.bundle` | 3,732,225 | 28,595,092 | 37 | 2,009 |
| `ui-visualtreeassets_assets_initvisualtreeassetpreload.bundle` | 19,610 | 122,948 | 1 | 0 |
| `ui-visualtreeassets_assets_introvisualtreeassetpreload.bundle` | 144,347 | 1,057,940 | 18 | 90 |
| `ui-visualtreeassets_assets_matchvisualtreeassetpreload.bundle` | 529,927 | 3,949,740 | 35 | 362 |

### 9.1 `TableFactory` sınıfları (`ui-tablefactories_assets_all.bundle`)

`AboutPastWinnersCompactTableFactory`, `AboutPastWinnersTableFactory`, `AboutRankingsTableFactory`, `AddRemoveLeaguesTableFactory`, `AgentOfferedPlayerTableFactory`, `AgentTableFactory`, `AgreedPlayingTimeTableFactory`, `AllTimeBestXITableFactory`, `AttributeHolderTableFactory`, `AttributesComparsionTableFactory`, `BlockedJobRolePotentialStaffToReplaceTableFactory`, `BudgetAdjustmentDialogPlayersTableFactory`, `CareerStatsSeasonStatsTableFactory`, `CareerStatsTableFactory`, `ChooseFolderBrowseCardTableFactory`, `ChoosePictureBrowseCardTableFactory`, `ClubBalanceTableFactory`, `ClubBoardMembersTableFactory`, `ClubBoardRequestsTableFactory`, `ClubBoardTableFactory`, `ClubCodeOfConductTableFactory`, `ClubCoefficientTableFactory`, `ClubHistoryRecordsInGameTableFactory`, `ClubHistoryRecordsLeagueAllTimeRecordsTableFactory`, `ClubInfoPreviousFinishesTableFactory`, `ClubSeasonAwardsSeasonResultsTableFactory`, `ClubSelectionTableFactory`, `ClubSupportersExpectationsTableFactory`, `ClubsListTableFactory`, `CoachingAttributesDataTableFactory`, `CompetitionAboutAveragePointsTableFactory`, `CompetitionAboutAwardWinnersBestPlayersTableFactory`, `CompetitionAboutAwardWinnersBestSquadTableFactory`, `CompetitionAboutAwardWinnersBestTeamsTableFactory`, `CompetitionClubsStadiumsCardTableFactory`, `CompetitionLeagueCombinedTableFactory`, `CompetitionLeagueTableFactory`, `CompetitionSiteAboutDraftHistoryCardTableFactory`, `CompetitionSiteAboutDraftSelectionTableFactory`, `CompetitionSiteInsAndOutsTransfersTableFactory`, `CompetitionSitePastTransfersTableFactory`, `CompetitionSitePlayerStatsTableFactory`, `CompetitionSiteSeasonTicketsCardTableFactory`, `CompetitionSiteSquadRewardsTableFactory`, `CompetitionSiteTeamStatsTableFactory`, `CompetitionStatsInjuryTableFactory`, `CompetitionTableFactory`, `CompetitionTeamInjuryTableFactory`, `CompetitionTransferWindowReportTransferActivityTableFactory`, `CompetitionWaiverListPickOrderTableFactory`, `CompetitionXGStagesTableFactory`, `CompetitionsClubsSponsorshipIncomeTableFactory`, `CompetitionsNationsListTableFactory`, `ContractAddOnActivatedNewsTableFactory`, `ContractCompetitionBonusActivatedClubTableFactory`, `ContractCompetitionBonusActivatedPlayerTableFactory`, `ContractExpiresTableFactory`, `ConversationSummaryPlayerTargetTableFactory`, `ConversationSummaryPromisesTableFactory`, `DerbyTableFactory`, `DynamicsBuyinEventTableFactory`, `DynamicsPlayerIssuesTableFactory`, `DynamicsPlayerMindsetTableFactory`, `DynamicsSquadPlayerBuyinTableFactory`, `EstimatedTradeValueTableFactory`, `ExpectedFormationTableFactory`, `FavouredPersonnelTableFactory`, `FfpPlayersTableFactory`, `FileSummaryDetailsManagersCardTableFactory`, `FileSummaryDetailsNationsCardTableFactory`, `FinancesWagesTableFactory`, `FixtureListElementTableFactory`, `ForcedResultsTableFactory`, `GlobalSearchResultsAwardTabTableFactory`, `GlobalSearchResultsClubsTabTableFactory`, `GlobalSearchResultsCompTabTableFactory`, `GlobalSearchResultsMessageTabTableFactory`, `GlobalSearchResultsNationalTeamContainerTabTableFactory`, `GlobalSearchResultsNationsTabTableFactory`, `GlobalSearchResultsPeopleTabTableFactory`, `HallOfFameContentDetailsTableFactory`, `HallOfFameContentRankTableFactory`, `HeatMapsTableFactory`, `IGESearchResultsClubsTabTableFactory`, `IGESearchResultsCompTabTableFactory`, `IGESearchResultsLanguageTabTableFactory`, `IGESearchResultsNameTabTableFactory`, `IGESearchResultsNationsTabTableFactory`, `IGESearchResultsPeopleTabTableFactory`, `InterestedClubsTableFactory`, `IntermediariesTableFactory`, `JobBoardTableFactory`, `JobCentreTableFactory`, `JobHistoryTableFactory`, `JobMarketTableFactory`, `LastMatchTableFactory`, `LatestScoresCompetitionTableFactory`, `LeaguePositionRulesTableFactory`, `LeagueSeasonClimaxFixturesTableFactory`, `LeagueTableTooltipTableFactory`, `LeaguesSummaryTableFactory`, `LoadGameBrowseCardTableFactory`, `LoadGameLocalCardTableFactory`, `MLSCombinePerformanceResultsTableFactory`, `ManagerMilestoneInfoTableFactory`, `ManagerMovementTableFactory`, `MatchClientsTooltipTableFactory`, `MatchStatsTableFactory`, `MentalAttributesDataTableFactory`, `MyRelationshipsTableFactory`, `NationAgreementTableFactory`, `NationClubCoefficientTableFactory`, `NationCompetitionTableFactory`, `NationEligibilityTableFactory`, `NationKnowledgeTableFactory`, `NationLeagueStructureTableFactory`, `NationSelectionTableFactory`, `NationSiteRankingsTableFactory`, `NewsCompPlayersAwardTableFactory`, `NonPlayerReportOverviewHistoryTileTableFactory`, `NonPlayerTableFactory`, `NonPlayerViewableAttributesDataTableFactory`, `NotInterestedPlayersTableFactory`, `OddsTableFactory`, `OnThePitchComparisonReportTableFactory`, `OnlineLobbyLeagueTableFactory`, `OnlineLobbyTableFactory`, `OnlineManagerOptionsTableFactory`, `PassMapsTableFactory`, `PastManagersTableFactory`, `PastWinnersTableFactory`, `PersonInterestedClubTableFactory`, `PersonTransferOfferTableFactory`, `PlayerActiveTransferInfoTableFactory`, `PlayerBansOverviewTableFactory`, `PlayerBuyinTableFactory`, `PlayerFormTableFactory`, `PlayerIndividualTrainingTableFactory`, `PlayerInjuryHeroTableFactory`, `PlayerInjuryTableFactory`, `PlayerInvolvedInMatchesTableFactory`, `PlayerLast5MatchesFormTableFactory`, `PlayerMLSRightsTableFactory`, `PlayerMentoringGroupTableFactory`, `PlayerPositionalRolesTableFactory`, `PlayerReportBansAndDisciplineTableFactory`, `PlayerReportDevelopmentProgressReportTableFactory`, `PlayerReportScoutedSquadComparisonPlayersTableFactory`, `PlayerSearchSmallTableFactory`, `PlayerSeasonStatsTableFactory`, `PlayerShoutsTableFactory`, `PlayerTableFactory`, `PlayerTargetsTableFactory`, `PlayingTimeExpectationsTableFactory`, `PressConferenceInviteTableFactory`, `PreviousMeetingHeadToHeadLeagueTableTableFactory`, `PrioritiseFutureTransferItemTableFactory`, `QualificationPlacesTableFactory`, `RecruitmentDofTargetsTableFactory`, `RecruitmentFeedbackTableFactory`, `RecruitmentFocusStaffTableFactory`, `RivalryTableFactory`, `RoleAbilityTableFactory`, `RumouredClubsTableFactory`, `SaveGameBrowseCardTableFactory`, `SaveGameLocalCardTableFactory`, `ScoutAssignmentTableFactory`, `ScoutReportTacticalEffectivenessTableFactory`, `ScoutingCompetitionTableFactory`, `ScoutingFocusTableFactory`, `SetPieceFrequencyTableFactory`, `SetPieceInstructionsTableFactory`, `SetPiecePenaltyCandidatesTableFactory`, `SetPiecePriorityListTableFactory`, `SetPieceTakerListTableFactory`, `SetPiecesPlayerTableFactory`, `ShortcutsPreferencesCardTableFactory`, `SigningsOfTheSeasonNewsTableFactory`, `SpecificallyScoutedTeamTableFactory`, `SquadActiveBansTableFactory`, `SquadCaptainsStandInTableFactory`, `SquadDevelopmentTableFactory`, `SquadDisciplineTableFactory`, `SquadFeedbackConfidenceTableFactory`, `SquadPotentialBansTableFactory`, `SquadPromisesTableFactory`, `StaffAssignmentsTableFactory`, `StaffContractDecisionsTableFactory`, `StaffMeetingSuggestionTableFactory`, `StaffNumbersChangedTableFactory`, `StaffTransferActivityTableFactory`, `StatsInjuryListTableFactory`, `StatsSuspensionTableFactory`, `SteamDownloadTableFactory`, `SubstitutesTableFactory`, `SuggestedInternationalSquadTableFactory`, `TacticAnalysisTableFactory`, `TacticOppositionInstructionTableFactory`, `TacticTeamSelectionTableFactory`, `TacticalEffectivenessTableFactory`, `TeamHierarchyTableFactory`, `TeamReportPrioritiesTableFactory`, `TeamTalkPlayerReactionTableFactory`, `TendencyDataTableFactory`, `TopContinentClubsTableFactory`, `TransferActivityPersonTableFactory`, `TransferActivityTradeInfoTableFactory`, `TransferBreakdownInterestedClubsTableFactory`, `TransferConfidenceTableFactory`, `TransferOfferPotentialExchangePlayersTableFactory`, `TransferRoomAdvertResponsesTableFactory`, `TransferRoomAdvertsTableFactory`, `TransferRoomPitchActivityTableFactory`, `TransferRumoursTableFactory`, `TransferWindowTableFactory`, `WelcomePackPlayersTableFactory`, `WorkPermitStatusTableFactory`, `WorldKnowledgeNationTableFactory`, `WorldKnowledgeRegionTableFactory`, `YouthCandidatesPreviewTableFactory`

## 10. `il2cpp.usym` kaynak ağacı (klasör bazında dosya sayısı)

| Klasör | Dosya |
|---|---:|
| `…/apps/game/FM Unity` | 2,567 |
| `C:/build` | 1,061 |
| `…/shared/packages/com.si.lattice` | 374 |
| `SI.VisualScripting.Generator/SI.VisualScripting.Generator.NodeGenerator` | 353 |
| `…/shared/packages/com.si.bindable` | 298 |
| `Library/PackageCache/com.unity.render-pipelines.core@43eeb73e554f` | 203 |
| `Packages/com.unity.inputsystem/InputSystem` | 172 |
| `…/shared/packages/com.si.core` | 144 |
| `…/shared/packages/com.si.ui` | 142 |
| `C:/Users` | 116 |
| `Unity.UIToolkit.SourceGenerator/Unity.UIToolkit.SourceGenerator.UxmlSerializedDataGenerator` | 102 |
| `Library/PackageCache/io.backtrace.unity@c3dc42f2505a` | 76 |
| `Library/PackageCache/com.unity.ugui@2e4da8434a5c` | 73 |
| `…/shared/packages/com.si.citygen` | 68 |
| `Library/PackageCache/com.unity.timeline@bfd27f8016ff` | 47 |
| `Library/PackageCache/com.unity.cinemachine@285f38545487` | 46 |
| `Library/PackageCache/com.unity.collections@12999e356c23` | 40 |
| `…/shared/packages/com.si.visualscripting` | 39 |
| `Library/PackageCache/com.unity.mathematics@19a9377c4ffa` | 31 |
| `SI.Bindable.Reference.Generator/SI.Bindable.Reference.Generator.ReferenceGenerator` | 28 |
| `…/shared/packages/com.pragma.firstlook.core` | 22 |
| `…/shared/packages/com.tayx.graphy` | 21 |
| `Library/PackageCache/com.unity.splines@56b2023b4b9f` | 17 |
| `Users/grant.smith` | 15 |
| `…/shared/packages/com.si.audio` | 15 |
| `…/apps/game/packages` | 14 |
| `…/shared/packages/com.cysharp.zstring` | 14 |
| `…/shared/packages/com.si.anim` | 14 |
| `…/shared/packages/com.nosuchstudio.rtltmpro` | 10 |
| `…/shared/packages/com.si.marshalling` | 8 |

## 11. C++ Native Motor (`game_plugin.dll`) ve Veritabanı / FMF Tabloları

- **`game_plugin.dll`**: `404,308,480` bayt, `282` adlandırılmış export, `.pdata` istisna dizininde **`139,131`** C++ fonksiyonu (`74,518,907` bayt makine kodu).
- **`ActionContributor` vtable sınıfları (224 adet)**: `rPNN`, `yMKr`, `9pYX`, `4tL6`, `tNfl`, `nfE8`, `lLC5`, `gaS9`, `m Xp`, `l1d1`, `tauq`, `EkSD`, `D3uF`, `Ojlv`, `5Lbk`, `pdVZ`, `Jye1`, `z5DD`, `hb8D`, `PcdS`, `dC3h`, `IJRw`, `Pnbw`, `YIEn`, `5i7a`, `LG7g`, `FdnA`, `YHl3`, `NOpa`, `nyw9`, `o8HG`, `NZbJ`, `WmR5`, `m4Vg`, `ibpz`, `uDxN`, `6vNa`, `QhWI`, `hJEG`, `cbqL` … (+184).
- **`SearchFilter` native vtable sınıfları (58 adet)**: `phfr`, `pwei`, `pftr`, `pdpr`, `pllr`, `pmqr`, `pffr`, `pnat`, `ptrl`, `pcfr`, `phap`, `pfST`, `pf20`, `p100`, `p200`, `p2pa`, `p500`, `pfrd`, `pfpc`, `pfij`, `pftx`, `pfpu`, `pfdt`, `bpnt`, `pofr`, `pftr`, `pRoI`, `pRoO`, `psct`, `pjob`, `pemp`, `prep`, `pval`, `pbas`, `phei`, `pntf`, `plng`, `pwag`, `pPpM`, `pinj`, `pnam`, `pcbd`, `pdat`, `papp`, `bsnr`, `bsdv`, `pfav`, `pEfe`, `pEwg`, `pask`, `pcit`, `pcar`, `ppar`, `Nsta`, `pmfr`, `SEfr`, `agfr`, `ppir`.
- **`non_pl_hist_{index,id,dt}.dat`** (`shared/data/database/db/2700/2700_fm`): `746,641` personel indeksi, `739,120` bağlı liste düğümü (`8` bayt), **`3,527,045`** kariyer geçmişi satırı (`24` bayt `<IHHHHHHBBBBi`).
- **`summary.dat`** (`shared/data/database/db/2700/2700_fm/summary.dat`): `6` kıta, `251` ülke, **`96,171`** kulüp özet kaydı (`25` bayt `\xff\xff\xff\xff\x09`).
- **`lang_db_general.dat`**: `401` Zstd çerçevesi (`25` dil × `16` tablo: `82` turnuva, `394` kulüp, `2` ödül, `144` stadyum jenerik ad tablosu).
- **`constants.fmf`**: `constants/generated_colour_pair_constants.jsb`, `constants/generated_match_crowd_constants.jsb`, `constants/generated_shuffle_draft_constants.jsb`, `constants/generated_training_constants.jsb`.
- **`engine_lookup_tables.json`**: `jumping_reach_table`, `aerial_reach_table`, `qme_stat_relevant_attributes`, `oop_attributes_scoring`, `player_ratings_data`, `team_picking_weights_master`, `training_tables`, `simatch_extra_tables`, `simatchshared_tables`.
- **`all_fmf_configs_and_filters.json`**: 14 `.fmf` arşivi envanteri, 445 oyuncu arama filtresi ve ayar/mağaza/versus XML'leri.

## 12. Tüm Kurulum Envanteri, Addressable Katalogları, `sianim` 3B Animasyon Motoru ve Unity Runtime Konteynerleri

### 12.1 Tüm UnityFS `.bundle` Kategorileri (`BlocksInfo` CAB Dizin Özeti)

Toplam **534** `.bundle` dosyası, **4,264,347,140** bayt sıkıştırılmış, **8,244,629,304** bayt açılmış, **764** CAB düğümü.

| Kategori | Bundle | Sıkıştırılmış (Bayt) | Açılmış (Bayt) | CAB Düğümü |
|---|---:|---:|---:|---:|
| `art` | 355 | 3,515,313,430 | 6,232,702,167 | 520 |
| `ui` | 67 | 198,189,454 | 837,870,132 | 95 |
| `match` | 4 | 202,767,780 | 539,104,284 | 7 |
| `scenes` | 12 | 120,727,416 | 325,961,892 | 30 |
| `videos` | 3 | 99,600,802 | 103,396,155 | 6 |
| `shaders` | 62 | 37,193,757 | 54,791,256 | 63 |
| `stadiums` | 7 | 27,166,602 | 49,902,119 | 14 |
| `audio` | 1 | 45,581,448 | 48,620,876 | 2 |
| `changingroom` | 1 | 8,016,711 | 35,703,888 | 2 |
| `promobanner` | 1 | 7,290,331 | 8,779,264 | 2 |
| `vfx` | 1 | 1,827,834 | 5,025,416 | 2 |
| `f87a5c426c04c02c5c32c1ef21ae2ad6` | 2 | 283,980 | 1,186,428 | 3 |
| `globalobjects` | 1 | 144,957 | 608,248 | 1 |
| `gamemodules` | 7 | 101,247 | 455,243 | 7 |
| `characterbuilder` | 1 | 50,075 | 207,644 | 1 |
| `fantasydraft` | 1 | 26,049 | 104,548 | 1 |
| `settings` | 1 | 12,058 | 67,988 | 1 |
| `shortcutdata` | 1 | 14,995 | 39,024 | 1 |
| `initscene` | 1 | 11,556 | 37,260 | 1 |
| `stadiumbuilder` | 1 | 13,231 | 27,636 | 1 |
| `graphics` | 1 | 6,768 | 20,296 | 1 |
| `projectconfigurationassets` | 1 | 2,826 | 8,700 | 1 |
| `sibindable` | 1 | 2,422 | 5,684 | 1 |
| `performance` | 1 | 1,411 | 3,156 | 1 |

### 12.2 Unity Addressables İkili Katalogları (`0x0DE38942` v2) ve `manifest.dat`

- **`fm_Data/StreamingAssets/aa/catalog.bin`**: `3,269,712` bayt, sihirli sayı `0x0de38942` (v2), Locator ID `AddressablesMainContentCatalog`, Build Hash `7eb98230c27092580c839722562a28fa`, **`29,020`** anahtar-konum çifti, `1,302` benzersiz `.bundle` referansı.
- **`fm_Data/StreamingAssets/AddrData/catalog_info.bin`**: `5,497,964` bayt, sihirli sayı `0x0de38942` (v2), Locator ID `AddressablesMainContentCatalog`, Build Hash `6658876dbc881cca10bbd77f47c4be19`, **`37,582`** anahtar-konum çifti, `539` benzersiz `.bundle` referansı.
- **`aa/AddressablesLink/link.xml`**: `162,851` bayt, `50` assembly, `1,618` korunan tip.
- **`fm_Data/manifest.dat`**: `30,975` bayt, format `FM27_25B_binary_md5 (uint32 path_hash + int32 len=16 + 16B md5 + '\n')`, **`1,239`** dosya doğrulama kaydı (`1,235` aktif hash).

### 12.3 `sianim` 3B Maç Animasyon Motoru (`*.cat`, `*.amd`, Şemalar ve İskeletler)

| `.cat` Arşivi | Boyut (Bayt) | Sürüm | `CAT\x00` Klip | Kemik Bölümü | Animasyon İzi | `STAB` Dizesi |
|---|---:|---:|---:|---:|---:|---:|
| `locomotion_female.cat` | 29,717,081 | v38 | 49 | 4,508 | 3,773 | 0 |
| `locomotion_male.cat` | 35,442,004 | v38 | 52 | 4,784 | 3,996 | 0 |
| `locomotion_official.cat` | 3,026,725 | v38 | 12 | 1,104 | 956 | 0 |
| `pack.cat` | 29,800,182 | v38 | 5,819 | 535,348 | 548,715 | 5,819 |

| `.amd` Motion Matching DB | Boyut (Bayt) | Sürüm | Segment Sayısı (11B) | Toplam Kare Aralığı | Kare Başına Bayt |
|---|---:|---:|---:|---:|---:|
| `locomotion.amd` | 5 | v4 | 0 | 0 | 0 |
| `locomotion_female.amd` | 7,076,130 | v4 | 1,503 | 45,100 | 156.53 |
| `locomotion_male.amd` | 8,259,025 | v4 | 1,447 | 51,824 | 159.06 |
| `locomotion_official.amd` | 648,569 | v4 | 2,550 | 68,775 | 9.02 |

- **Maç Aksiyon Şemaları (`shared/data/sianim/schemas/*.json`)**: `44` şema dosyası.
- **İskelet Rig ve Dev UI Dosyaları (`shared/data/sianim/skeletons*`)**: `19` dosya.

### 12.4 Unity `SerializedFile v22` Konteynerleri (`fm_Data/`)

| Konteyner | Boyut (Bayt) | `.resS` Boyutu | Unity Sürümü | Tip | Nesne | Script Tipi | Dış Referans |
|---|---:|---:|---|---:|---:|---:|---:|
| `globalgamemanagers` | 388,132 | 0 | `6000.3.18f1-custom` | 19 | 19 | 0 | 5 |
| `globalgamemanagers.assets` | 1,860,728 | 4,173,536 | `6000.3.18f1-custom` | 50 | 5,964 | 42 | 2 |
| `resources.assets` | 1,249,176 | 1,595,600 | `6000.3.18f1-custom` | 62 | 2,019 | 50 | 2 |
| `sharedassets0.assets` | 362,700 | 416 | `6000.3.18f1-custom` | 7 | 20 | 1 | 2 |
| `level0` | 40,524 | 0 | `6000.3.18f1-custom` | 34 | 328 | 24 | 3 |
| `unity default resources` | 5,923,140 | 0 | `6000.3.11f1` | 8 | 99 | 1 | 0 |
| `unity_builtin_extra` | 491,796 | 0 | `6000.3.18f1-custom` | 1 | 49 | 0 | 0 |

### 12.5 Tüm Native PE64 İkili Dosyaları (`EXE` / `DLL`)

| Dosya | Boyut (Bayt) | Bölüm | Export | `.pdata` Fonksiyonu |
|---|---:|---:|---:|---:|
| `fm.exe` | 667,648 | 6 | 4 | 315 |
| `UnityPlayer.dll` | 36,528,040 | 8 | 2 | 111,094 |
| `GameAssembly.dll` | 59,361,792 | 8 | 373 | 175,972 |
| `BacktraceCrashpadWindows.dll` | 178,688 | 7 | 3 | 550 |
| `crashpad_handler.dll` | 630,784 | 7 | 0 | 1,800 |
| `EOSSDK-Win64-Shipping.dll` | 19,531,704 | 7 | 680 | 65,926 |
| `game_plugin.dll` | 404,308,480 | 13 | 282 | 145,090 |
| `icudt65.dll` | 3,072 | 2 | 1 | 0 |
| `icuin65.dll` | 2,632,704 | 6 | 5,766 | 7,287 |
| `icuuc65.dll` | 1,890,304 | 6 | 3,002 | 4,782 |
| `lib_burst_generated.dll` | 1,013,248 | 5 | 1,116 | 1,822 |
| `msvcp140.dll` | 642,720 | 6 | 1,515 | 1,365 |
| `PartyWin.dll` | 4,038,728 | 6 | 157 | 10,526 |
| `PlayFabMultiplayerWin.dll` | 1,882,656 | 6 | 79 | 5,294 |
| `steam_api64.dll` | 317,080 | 6 | 1,054 | 810 |
| `vcruntime140.dll` | 178,848 | 8 | 71 | 383 |
| `vcruntime140_1.dll` | 50,256 | 6 | 3 | 107 |

### 12.6 Veritabanı Sürümleri (`2300`..`2700`) ve `lang_db.dat` Yerelleştirme Veritabanı

- **`shared/data/database/db/2700/2700_fm/lang_db.dat`**: `90,962,133` bayt, **`401`** Zstd çerçevesi (`25` dil × `16` tablo; dil başına **`229,555`** yerelleştirilmiş satır: `251` ülke, `8,084` turnuva, `100,432` kulüp, `58,475` şehir, `3,902` ödül, `52,406` stadyum, `1,681` sakatlık).
- **Tarihsel Veritabanı Sürümleri**: `2300` (25 dosya, 169,100,689 B), `2330` (25 dosya, 100,965,023 B), `2340` (25 dosya, 97,979,550 B), `2400` (34 dosya, 264,696,849 B), `2430` (34 dosya, 198,067,149 B), `2600` (54 dosya, 306,565,435 B), `2620` (54 dosya, 362,201,325 B), `2700` (52 dosya, 389,580,039 B).

