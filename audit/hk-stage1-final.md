# HK Stage 1 — Final migration audit

status: STAGE1_PASS

## Purpose

Final consolidation of Stage 1:
- old saved HK versions vs current implementation;
- pinned Kokkaras donor used as current external reference;
- no new gameplay development.

## Source set

### Pinned external reference
- Kokkaras HK Control Panel
- version: `5.3.22-ui-icons-pit-dim`
- pinned SHA256: `28c3104020ecb7f54d0d51a72d067404d0176bc069d59fcca417d66817d1fcf1`

### Historical migration evidence
- `audit/hk-migration-completeness.json`
- `audit/hk-migration-final-baseline.txt`
- `audit/hk-transfer-complete-status.txt`

### Current implementation evidence
- `baseline/topking/HamsterKingMobile.current.user.js`
- `baseline/topking/BASELINE.json`
- Stage 1 blocks 1A–1D

## Final migration numbers

- historical donor union functions: **515**
- historical live functions at migration baseline: **525**
- parser-reported missing functions: **11**
- genuinely missing historical functions: **0**
- parser-reported missing endpoints: **1**
- genuinely missing historical endpoints: **0**
- missing historical constants: **0**
- historical navigation entries retained: **20 / 20**
- current active navigation routes with real path: **18 / 18**
- intentional planned routes: **2**
  - Neighborhoods → Stage 5
  - Rat Hunt → Stage 6

## Final table

| Function / mechanic | Old script | Current | Live path | Status |
|---|---|---|---|---|
| Today / Daily | implemented | implemented | `daily` → render/read/actions | PASS |
| Pits | implemented | implemented | `pit` → read/plan/actions | PASS |
| Maps | implemented | implemented | `maps` → map index/detail/live | PASS |
| Resources | implemented | implemented | `resources` → live resource path | PASS |
| Buildings | implemented | implemented | `buildings` → render/live | PASS |
| Explore | implemented | implemented | `explore` → render/live | PASS |
| Businesses | implemented | implemented | `business` → lists/optimizer/actions | PASS |
| Recipes | implemented | implemented | `recipes` → render/run | PASS |
| Growth / Hamsters | implemented | implemented | `growth-hamsters` → Growth core | PASS |
| Growth / Generals | implemented | implemented | `growth-generals` → Growth core | PASS |
| Fair | implemented | implemented | `fair` → render/run | PASS |
| Shop | implemented | implemented | `shop` → render/buy | PASS |
| Clan skills | implemented | implemented | `clan` → render/scan/live | PASS |
| Wars | implemented | implemented | `wars` → render/read | PASS |
| Rumors | implemented | implemented | Daily rumor live/action path | PASS |
| Shared runner | implemented | implemented | pause/resume/stop/abort | PASS |
| Shared state | implemented | implemented | authoritative read/merge/refresh | PASS |
| Mutation serialization | historical/current migration layer | implemented | `hkMutationGate` | PASS |
| Budget/expense guards | implemented/superseded | implemented | budget decision + journal | PASS |
| Bosses | historically planned, later added | read-only implemented | `bosses` | PASS / later addition |
| Regular Fair | historically planned, later added | implemented | `fair-regular -> fair` | PASS / later addition |
| Generic Auto Routines | historically planned, later added | implemented | `routines` | PASS / later addition |
| Neighborhoods | planned / not transferable historical module | still planned | none by design | DEFERRED → Stage 5 |
| Rat Hunt | planned / not transferable historical module | still planned | none by design | DEFERRED → Stage 6 |

## Parser-reported function differences

| Historical function | Current equivalent / decision | Final status |
|---|---|---|
| `growthBestHamsterLevel` | current Growth candidate/level logic | COVERED |
| `growthBuyGeneralContracts` | `growthBuyAllGeneralContractsCore` | COVERED |
| `growthInventoryQuantity` | `growthInventoryMap` / `growthResource` | COVERED |
| `growthItemsCatalog` | current static/live item documents | COVERED |
| `growthRefresh` | `growthLoadLive` / current refresh flow | COVERED |
| `growthRunGenerals` | `growthRunGeneralsCore` | COVERED |
| `growthRunHamsters` | `growthRunHamstersCore` | COVERED |
| `growthRunLootboxes` | `growthOpenLootboxFamilyCore` | COVERED |
| `growthSetArray` | `growthArray` / current helpers | COVERED |
| `nutBuildingData` | `exactResourceBuildingData` | COVERED |
| `growthNutCost` | intentionally excluded; conflicts with approved currency invariant | INTENTIONAL EXCLUSION |

## Endpoint / constant result

Historical parser reported one endpoint as missing:

`/city/{…}/game_area`

Current implementation contains the real dynamic route:

`'/city/' + encodeURIComponent(cityId) + '/game_area'`

Final classification: **PARSER FALSE POSITIVE / PRESENT**.

Missing historical constants: **0**.

Kokkaras-only gateway, websocket, localStorage keys and Athens-specific scheduling constants are donor infrastructure and are not required to match our architecture.

## Automation decision

Kokkaras Business Auto Routines 1/2/3 were compared with current generic Auto Routines.

Decision:
- keep current generic Auto Routines;
- do not replace it with the Kokkaras business-only routines;
- retain Kokkaras routines only as an optional Stage 7 reference.

Reason:
- current system is broader;
- it preserves module-specific confirmations/budgets/guards;
- scheduled donor business mutations would increase mutation complexity.

This is a design decision, not a missing historical migration item.

## Navigation result

Historical entries retained: **20 / 20**.

Current:
- **18 active routes** → all have real content/execution paths;
- **2 planned routes**:
  - Neighborhoods;
  - Rat Hunt.

No dead active route found.

## Stage 0 / r9 note

Stage 0 canonical baseline manifest still records:
- version: `1.17.4`
- SHA256: `f7415cc08dc60f651bf95f7579407779ba16cbf2de876aeffb4f51463377d91e`

A later startup-only r9 candidate is recorded separately:
- `startup-error-scope-20260920-r9`
- SHA256: `5634b610d3686f4da3c79ec2078b2cd098653ca8fc5dcbce857069ffa6c80674`

r9 changes startup error trapping only and does not change gameplay migration coverage. Stage 1 result is therefore unaffected.

## DONE condition

Roadmap condition:

`Количество реально неперенесённых функций старого скрипта = 0`

Result:

**0**

## Final result

- functions: PASS
- endpoints: PASS
- constants: PASS
- automations/helpers: PASS
- navigation: PASS
- mutation-path presence: PASS
- genuinely untransferred historical functionality: **0**
- gameplay code changed during Stage 1 audit: **0**

# STAGE1_PASS

Next roadmap stage: **Stage 2 — LIVE verification of migrated modules**.

Stage 2 is not started by this audit.
