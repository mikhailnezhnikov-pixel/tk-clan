# TopKing Stage 2 — Unified Maps Runtime U1

Date: 2026-09-21  
Stage: Unified Maps Runtime U1  
Result: **PASS**

## User goal

Make Personal Cabinet → Maps a single working map list and make the userscript consume the shared map knowledge before researching buildings directly.

The shared knowledge must include:

- website/HK Maps data;
- maps gathered by players through the userscript;
- safe deduplication of the same district;
- building-level merge with W5 provenance priority;
- no unsafe bulk matching of unresolved historical maps.

## Unified Personal Cabinet

The backend `cabinet_maps()` now returns one unified list.

Each row has one source state:

- `website` — historical website map not yet safely linked to canonical knowledge;
- `script` — canonical/script district without separate website visualization;
- `combined` — website visualization and canonical/script knowledge safely linked to one district.

Current production result:

- combined: **25**
- script-only: **285**
- website-only: **210**
- unified rows: **520**

The 25 linked maps are displayed once, not twice.

If several website visualizations ever point to one canonical district, one unified row is returned and the richest available website visualization is chosen as primary while canonical building knowledge remains the source of truth.

Frontend:

`cabinet/index.html`

shows the source label:

- `Сайт`
- `Скрипт`
- `Сайт + Скрипт`

Script-only rows do not expose website publication controls.

## Why 210 historical maps are not force-merged

W6 proved that only 25 of the historical website maps could currently be linked to canonical districts without guessing.

U1 deliberately does **not** merge the remaining 210 by a fuzzy city/name/coordinate heuristic.

Instead, a historical map becomes linked when a real player area scan provides:

- canonical city;
- versioned canonical X:Y;
- current game building IDs;
- current game building geometry.

The server then applies the proven historical website grid rule:

`website Y:X → canonical X:Y`

Only exactly one city+grid candidate is accepted.

If the match is zero or ambiguous, no historical map write occurs.

## Automatic legacy website hydration

New server marker:

`HK_MAP_UNIFIED_RUNTIME_U1_V1`

Patch:

`deploy/topking/patch_server_unified_maps_runtime_u1.py`

During a normal `game_live` area submission, when shared maps are enabled, the userscript also supplies the current game's building geometry.

The server:

1. stores/updates the canonical game area normally;
2. searches the unresolved website catalog for exactly one safe historical city+Y:X match;
3. links that website map to the canonical area;
4. matches website points to existing canonical building IDs by strict point-in-polygon against the current game geometry;
5. writes exact `hk_map_point_links`;
6. imports historical room knowledge using the existing W5-safe `hk_maps_import` path.

No nearest-building guessing is used.

A hydration failure is isolated from the main game map submit: it cannot prevent the player's normal canonical map update.

## Shared knowledge in the userscript

Userscript patch:

`deploy/topking/patch_userscript_unified_maps_runtime_u1.py`

Current scanner marker:

`maps-shared-runtime-20260921-r7-safe5`

Shared runtime marker:

`maps-shared-knowledge-20260921-r1`

A new setting appears in Maps:

**Использовать общую базу карт**

Default: **ON**.

When enabled, before direct game building reads the userscript:

1. obtains the current shared canonical map index;
2. loads shared details only for the player's selected/owned areas;
3. collects building IDs with known non-NULL `room_count`;
4. intersects this knowledge with the existing active-player building set;
5. removes already-known active buildings from the direct game-read queue;
6. reads only the remaining unknown active buildings.

This means a more researched website/imported map can immediately save repeated building research.

## Scanner safety retained

The existing active-building safety gate remains unchanged.

A building can enter direct research only when:

1. it is currently active for the current player;
2. it has a known game-area mapping;
3. if selected-area filtering is active, it belongs to the selected district;
4. it is still unknown in shared knowledge.

Read-only game concurrency remains:

**5 workers maximum**

No shared database row can cause the script to probe an inactive building.

## Source priority

W5 remains unchanged:

`game_live > hk_maps_import`

Historical website knowledge fills unknown room knowledge.

If current game knowledge is already non-NULL, website/import knowledge cannot overwrite it.

If the game later observes a new value, `game_live` replaces the imported value.

## Build verification

Build run:

`35521561010`

Job:

`106106419454`

Result: **PASS**

Evidence:

`audit/hk-stage2-unified-maps-u1-build-status.txt`

Verified:

- unified Personal Cabinet dedupe: PASS;
- legacy website auto-hydration: PASS;
- website point → canonical building relation: PASS;
- shared room import: PASS;
- shared preload filter: PASS;
- safe active intersection unchanged: PASS;
- direct game read concurrency = 5;
- `game_live` priority: PASS.

Candidate SHAs:

- server: `f8b10a30a42d7dbb19ea11ee746eaccd89704a70ddb577631bf72c6ecca26df3`
- userscript: `46c6b95688a589e7d4b02a10403c9bd32c5012a8e92b6e0e768364aad54d55b5`

## Live deployment

Initial deploy run:

`35521677077`

The verified server and userscript were successfully installed and the service restarted.

That run then failed only in its shell SHA check because nested quoting expanded `$1` under `set -u`. The deployment itself had already completed.

No second deployment was performed.

A separate post-deploy verifier read the actual deployed files and confirmed the exact candidate SHAs.

Final live verification:

- run: `35521752892`
- rerun job: `106107338994`
- result: **PASS**

Live status:

`audit/hk-stage2-unified-maps-u1-live-status.txt`

Current live SHAs:

- server: `f8b10a30a42d7dbb19ea11ee746eaccd89704a70ddb577631bf72c6ecca26df3`
- userscript: `46c6b95688a589e7d4b02a10403c9bd32c5012a8e92b6e0e768364aad54d55b5`

## Production verification

No fake/test rows were written to production.

Current production state at final verification:

- `hk_maps_catalog = 235`
- `hk_map_points = 235`
- `hk_map_area_links = 25`
- `hk_map_point_links = 2007`
- `map_areas = 310`
- `map_buildings = 167690`

Unified Personal Cabinet production view:

- `combined = 25`
- `script = 285`
- `website = 210`
- unified rows = **520**

The fact that the bridge counts remain 25/2007 immediately after deployment proves U1 did not bulk-force-link the 210 unresolved maps.

## Personal Cabinet live UI

GitHub Pages initially lagged behind the repository change, so the first post-deploy HTTP check failed while backend/userscript tests were already passing.

The later Pages deployment completed successfully.

The post-deploy verification was rerun and confirmed the live Personal Cabinet contains the unified source UI.

Result: **PASS**

## Runtime behavior going forward

For a player opening/scanning Maps with shared knowledge enabled:

1. the script submits the actual owned/current area;
2. a matching old website map, if uniquely proven, is automatically attached to the same canonical district;
3. its safely matched building knowledge is imported;
4. the shared canonical details are loaded;
5. active buildings already known from website/other players are skipped;
6. only still-unknown active buildings are queried from the game;
7. new live results return to the canonical shared database.

Thus website maps and player scans progressively converge into one building-level knowledge base.

## U1 gate

- one Personal Cabinet map list — **PASS**
- safely linked duplicate district shown once — **PASS**
- website-only maps retained until proven — **PASS**
- script-only districts included — **PASS**
- shared knowledge setting in userscript — **PASS**
- shared knowledge enabled by default — **PASS**
- legacy website map automatically hydrates on real area scan — **PASS**
- known shared active buildings skipped before direct reads — **PASS**
- inactive buildings never added to direct reads — **PASS**
- max direct read concurrency remains 5 — **PASS**
- `game_live` priority preserved — **PASS**
- no bulk force-link of 210 unresolved maps — **PASS**
- live Personal Cabinet UI — **PASS**

**Unified Maps Runtime U1 = PASS.**
