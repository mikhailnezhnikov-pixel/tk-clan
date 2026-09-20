# HK Stage 1A — Functions audit

status: PASS

## Scope rule

Stage 1 in `docs/HK_MASTER_ROADMAP.md` is the final audit of the **historical migration source**: saved old HK versions compared with current/live.

The pinned Kokkaras donor `5.3.22-ui-icons-pit-dim` is still read first under SOURCE PREFLIGHT, but donor-only implementations that the roadmap explicitly assigns to later stages are **reference-only**, not Stage 1 migration defects.

This distinction is required because the roadmap separately defines:
- Stage 5 — Neighborhoods / Districts / Discovery;
- Stage 6 — Rat Hunt;
while Stage 1 explicitly audits the old saved script transfer and forbids new module development.

## Sources checked

- pinned donor: `reference/topking/REFERENCE.json`
  - file: `Вставленный текст.txt`
  - file id: `file_0000000006d08243a84499c0fe6f08c7`
  - version: `5.3.22-ui-icons-pit-dim`
  - sha256: `28c3104020ecb7f54d0d51a72d067404d0176bc069d59fcca417d66817d1fcf1`
- historical migration audit:
  - `audit/hk-migration-completeness.json`
  - `audit/hk-migration-final-baseline.txt`
  - `audit/hk-transfer-complete-status.txt`
- current implementation:
  - `baseline/topking/HamsterKingMobile.current.user.js`
- current non-feature startup hotfix r9 changes only startup error trapping; it does not alter gameplay function coverage.

## Historical migration function result

The historical donor-union audit recorded:
- donor union functions: **515**
- live functions at final migration baseline: **525**
- parser-reported missing donor functions: **11**
- genuinely missing real features: **0**

### Parser-reported names resolved as superseded/equivalent

| Historical function | Current equivalent | Status |
|---|---|---|
| `growthBestHamsterLevel` | current Growth level/candidate logic | SUPERSEDED / COVERED |
| `growthBuyGeneralContracts` | `growthBuyAllGeneralContractsCore` | SUPERSEDED / COVERED |
| `growthInventoryQuantity` | `growthInventoryMap` / `growthResource` | SUPERSEDED / COVERED |
| `growthItemsCatalog` | current static/live item documents | SUPERSEDED / COVERED |
| `growthRefresh` | `growthLoadLive` / current refresh flow | SUPERSEDED / COVERED |
| `growthRunGenerals` | `growthRunGeneralsCore` | SUPERSEDED / COVERED |
| `growthRunHamsters` | `growthRunHamstersCore` | SUPERSEDED / COVERED |
| `growthRunLootboxes` | `growthOpenLootboxFamilyCore` | SUPERSEDED / COVERED |
| `growthSetArray` | `growthArray` / current helpers | SUPERSEDED / COVERED |
| `nutBuildingData` | `exactResourceBuildingData` | SUPERSEDED / COVERED |
| `growthNutCost` | intentionally not restored; obsolete against approved currency invariant | INTENTIONAL EXCLUSION |

Therefore:

**historical genuinely untransferred functions = 0**

## Current function-family evidence

Current 1.17.4 contains active function families for the migrated modules:

| Function family | Representative current functions | Status |
|---|---|---|
| Today / daily | `renderDailyTasks`, `refreshDailyTasks`, `runDailySelected`, `runDailyAd`, `runDailyRumors`, `runDailyClanPurchases` | PRESENT |
| Pits | `pitLoop`, `pitMovePlan`, `renderPitForecast`, `finishDailyPitRace` | PRESENT |
| Businesses | `refreshBusinessData`, `renderBusinessLists`, `executeBusinessPlan`, optimizer helpers | PRESENT |
| Buildings | `refreshBuildings`, `renderBuildings`, `findBuildings` | PRESENT |
| Explore | `refreshExplore`, `renderExplore`, `exploreOwnedAreas`, `exploreMappedIds` | PRESENT |
| Growth / Hamsters / Generals | `growthRunHamstersCore`, `growthRunGeneralsCore`, `growthRunPlan`, `growthLoadLive` | PRESENT |
| Fair | `loadFair`, `renderFair`, `runFair`, purchase/preset helpers | PRESENT |
| Shop | `loadShop`, `renderShop`, `buyRegularShop` | PRESENT |
| Clan | `renderClanSkills`, `scanClanSkills`, `refreshSharedClanSkills` | PRESENT |
| Wars | `readPublicWar`, `refreshWars`, `renderWars` | PRESENT |
| Rumors | `loadRumorRoute`, `runDailyRumors`, `rumorServerJson` | PRESENT |
| Bosses | `refreshBosses`, `renderBosses`, boss row/state helpers | PRESENT / READ-ONLY |
| Auto routines | `renderAutoRoutines`, `runAutoRoutine`, `stopAutoRoutine` | PRESENT |
| Regular Fair | dedicated current UI marker `regular-fair-ui-20260920-r1` | PRESENT |
| Maps | map index/detail/read helpers | PRESENT |

Current markers also confirm:
- `bosses-readonly-20260920-r1`
- `regular-fair-ui-20260920-r1`
- `auto-routines-20260920-r1`

## Pinned Kokkaras donor — additional function reference

The pinned donor exposes/uses concrete entrypoints including:
- `showDailyTasksMenu` / `runDailyTasks`;
- `showNeighborhoodBattlesMenu` / `runNeighborhoodBattles`;
- `showHamstersGeneralsMenu` / `runHamstersGenerals`;
- `showBuildingsMenu` / `runBuildings`;
- `showExploreBuildingsMenu` / `runExploreBuildings`;
- `showBuildingsEventMenu`;
- `showBusinessesMenu` / `runBusinessRearrange` / `runBusinessAutoRoutine1/2/3`;
- `showPitsMenu` / `runPits`;
- Clan Wars / Rat Hunt helpers;
- Fair / Default Fair helpers and menus.

These names are **not required to exist verbatim** in current because current HK has a different architecture. The audit checks transferred behavior/function families, not identifier-name equality.

### Reference-only donor functions for later roadmap stages

| Donor family | Current state | Stage 1 classification |
|---|---|---|
| Neighborhood Battles / Neighborhoods | current navigation still marks Neighborhoods as planned | REFERENCE ONLY — Stage 5 scope |
| Rat Hunt | current navigation marks Rat Hunt as planned | REFERENCE ONLY — Stage 6 scope |
| richer donor Clan Wars mutations | current Wars read path exists; deeper correctness/actions belong later roadmap checks | NOT A STAGE 1 MIGRATION DEFECT |
| dedicated donor Buildings Event UI | historical migration audit records building events as covered by resources/player-event | COVERED / ARCHITECTURE DIFFERENCE |

## Stage 1A conclusion

- historical transferable function coverage: **PASS**
- genuinely missing historical functions: **0**
- donor/current identifier parity: **not required**
- donor-only later-stage modules: **tracked separately, not implemented in 1A**
- new gameplay code added in this block: **0**

Next block: **1B — endpoints and constants audit**.
