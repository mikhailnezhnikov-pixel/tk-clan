# HK Stage 1D — Navigation and real live paths audit

status: PASS

## Scope

Audit:
- historical navigation entries;
- current navigation entries;
- current page targets;
- render/live-refresh execution paths;
- intentional planned modules;
- no new navigation development.

## SOURCE PREFLIGHT

Pinned donor:
- Kokkaras HK Control Panel
- version: `5.3.22-ui-icons-pit-dim`
- sha256: `28c3104020ecb7f54d0d51a72d067404d0176bc069d59fcca417d66817d1fcf1`

The donor contains dedicated menu/entry functions for multiple modules, including Neighborhood Battles, Explore Buildings, Pits, Clan Wars, Fair and Rat Hunt related behavior. Identifier-name parity with current HK is not required; this block checks whether current navigation reaches real current execution paths.

## Historical navigation baseline

The historical migration audit recorded **20 navigation entries**:

1. Today
2. Pits
3. Bosses — planned at historical audit time
4. Neighborhoods — planned
5. Maps
6. Resources
7. Buildings
8. Explore
9. Businesses
10. Recipes
11. Auto routines — planned at historical audit time
12. Growth Overview
13. Hamsters
14. Generals
15. Fair
16. Shop
17. Regular Fair — planned at historical audit time
18. Clan Skills
19. Wars
20. Rat Hunt — planned

## Current navigation

Current `NAV_GROUPS` still contains **20 navigation entries**.

Current status:
- active modules: **18**
- planned modules: **2**
  - Neighborhoods
  - Rat Hunt

Modules that were previously planned but are now active:
- Bosses;
- Auto Routines;
- Regular Fair.

Therefore the navigation did not lose historical entries; it gained live implementations for three formerly planned entries.

## Active route verification

| Current navigation | Page/content path | Execution path | Status |
|---|---|---|---|
| Today | `daily` | `renderDailyTasks` + `refreshModuleLive('daily')` | PASS |
| Pits | `pit` | page exists; generic `refreshModuleLive('pit')` path | PASS |
| Bosses | `bosses` | `renderBosses` + live refresh | PASS |
| Maps | `maps` | `renderMapIndex` + maps live path | PASS |
| Resources | `resources` | `renderResources` + live refresh | PASS |
| Buildings | `buildings` | `renderBuildings` + live refresh | PASS |
| Explore | `explore` | `renderExplore` + live refresh | PASS |
| Businesses | `business` | `renderBusinessLists` / optimizer + live refresh | PASS |
| Recipes | `recipes` | `renderRecipes` + live refresh | PASS |
| Auto Routines | `routines` | `renderAutoRoutines` | PASS |
| Growth Overview | `growth` | `renderGrowth` + `growthAutoOpen` | PASS |
| Hamsters | `growth-hamsters` | `renderGrowth` + `growthAutoOpen` | PASS |
| Generals | `growth-generals` | `renderGrowth` + `growthAutoOpen` | PASS |
| Fair | `fair` | `renderFair` + live refresh | PASS |
| Shop | `shop` | `renderShop` + live refresh | PASS |
| Regular Fair | alias `fair-regular -> fair` | forces `fair_default`, clears selection state, then `renderFair` | PASS |
| Clan Skills | `clan` | `renderClanSkills` + live refresh | PASS |
| Wars | `wars` | `renderWars` + live refresh | PASS |

All 18 active navigation entries have an existing content target and a current render/execution path.

## Navigation persistence / fallback

Current navigation also has:
- persisted `navGroup` / `navModule`;
- remembered-module restoration;
- invalid remembered page fallback to `daily`;
- group-to-module routing;
- disabled planned buttons without fake page targets;
- `fair-regular` explicit alias rather than a duplicate content tree.

Classification: **PRESENT / CLEANER THAN DUPLICATED ROUTES**.

## Intentional planned entries

### Neighborhoods

Current:
- visible as planned/disabled;
- no fake content target;
- no accidental fallback presented as a working Neighborhoods module.

Classification:
- **INTENTIONAL PLANNED**
- roadmap owner: **Stage 5 — Districts / Discovery**
- not a Stage 1 historical migration defect.

### Rat Hunt

Current:
- visible as planned/disabled;
- no fake live path.

Classification:
- **INTENTIONAL PLANNED**
- roadmap owner: **Stage 6 — Rat Hunt**
- not a Stage 1 historical migration defect.

## Auto Routines decision carried from 1C

The current generic `routines` navigation remains unchanged.

Kokkaras Business Auto Routines 1/2/3 are **not** inserted into navigation during Stage 1. They remain an optional Stage 7 reference because adding scheduled business mutations here would violate the Stage 1 rule against new development.

## Stage 1D conclusion

- historical nav entries retained: **20 / 20**
- current active routes with real content/execution path: **18 / 18**
- intentional planned routes: **2**
- accidental dead active routes found: **0**
- hidden/fallback route masquerading as a working module: **0**
- new gameplay/navigation code added: **0**

**Stage 1D: PASS**

Next block: **Stage 1 FINAL — consolidated migration table and final zero-missing decision**.
