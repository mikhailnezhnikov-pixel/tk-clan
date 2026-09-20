# TopKing Stage 2 — W8 End-to-end shared knowledge verification

Date: 2026-09-21  
Stage: W8 — End-to-end verification and checkpoint  
Result: **PASS**

## Goal

Verify the completed Maps ↔ Website shared knowledge link in both directions on multiple districts:

A. userscript/game scan → shared canonical DB → website  
B. authorized website import → shared canonical DB → userscript

W8 is verification only. It does not perform production data migration.

## Verification run

Workflow:

`.github/workflows/verify-w8-maps-shared-kb-e2e.yml`

Run:

`35520602358`

Job:

`106103898484`

Result: **PASS**

All workflow steps passed.

Evidence:

- `audit/hk-stage2-maps-shared-kb-w8-status.txt`
- `audit/hk-stage2-w8-temp-e2e-summary.json`
- `audit/hk-stage2-w8-live-samples.json`

## Direction A — userscript → shared DB → website

Two independent districts were tested on the deployed server code using a temporary SQLite database.

### District A1

The test started with:

- canonical district with two building IDs;
- both room counts unknown;
- website compact point geometry already linked to those canonical building IDs;
- first website point marked as investment.

Then a simulated userscript/game submission arrived through the normal canonical `submit_map_area()` path using a different source area ID at the same canonical city/X:Y.

Verified:

- alias resolved to the existing canonical district;
- canonical room count changed from NULL to `6`;
- source became `game_live`;
- unknown second building stayed NULL;
- website geometry bytes were not rewritten;
- subsequent `hk_map_data()` immediately rendered the new canonical value;
- original website investment bit was preserved.

Stored website flag:

`investment + room 1 = 9`

Dynamic canonical result:

`investment + room 6 = 14`

Therefore only the room bits changed; geometry and investment state did not.

### District A2

A complete imported canonical district began with room count `2`.

A later simulated current game observation changed it to `0`.

Verified:

- complete-map live refresh was accepted;
- source became `game_live`;
- website immediately rendered `0`;
- no export/sync/re-import was required.

Direction A result:

**PASS on 2 districts.**

## Direction B — website/import → shared DB → userscript

Two independent authorized uploads were tested through the deployed W7 import path.

### District B1 — canonical X:Y

Upload used:

`coord_revision = column-row-v1`

Verified:

- website catalog row stored;
- website compact points stored;
- canonical district created;
- exact building IDs persisted;
- point links persisted;
- room counts visible through shared `map_detail()`;
- investment building remained investment;
- a third game building with no room knowledge remained NULL;
- Personal Cabinet backend listed the uploaded map immediately;
- no separate sync step was required.

### District B2 — historical Y:X

Upload used:

`coord_revision = historical-yx`

Input metadata:

- x=55
- y=44

Verified canonical result:

- x=44
- y=55

The coordinate swap occurred exactly once.

This complete imported district initially had room count `7`.

A later `game_live` observation changed it to `0`.

The original website upload was then repeated.

Verified:

- repeated import did not create a second district;
- repeated import did not create duplicate area links;
- repeated import did not create duplicate point links;
- imported room `7` did not overwrite current `game_live=0`;
- userscript/shared `map_detail()` still returned `0 / game_live`;
- website dynamic overlay also returned `0`.

Direction B result:

**PASS on 2 districts.**

## Required W8 checks

### Coordinates

Verified:

- canonical `column-row-v1`: PASS;
- explicit historical `historical-yx`: PASS;
- no silent coordinate orientation guessing: retained from W7.

### Aliases

Verified:

- userscript submissions with alternate area IDs resolve to existing canonical districts;
- `map_detail(alias)` returns the canonical district;
- canonical alias lists expose alternate IDs.

Result: **PASS**

### room_count

Verified in both directions:

- userscript canonical updates appear on website reads;
- authorized website imports appear in userscript/shared map reads.

Result: **PASS**

### Investment behavior

Verified:

- canonical `is_invest` is preserved;
- website compact point high bit is preserved while canonical room bits are overlaid;
- live website point renderer decodes:
  - `crystals = flag & 0x07`;
  - `investment = Boolean(flag & 0x08)`.

Result: **PASS**

### Unknown / NULL buildings

Verified:

- unknown canonical buildings remain NULL;
- a linked point with no canonical room knowledge uses website source fallback;
- authorized full-map buildings with no crystal knowledge remain NULL in shared DB.

Result: **PASS**

### Source priority

Verified:

`game_live > hk_maps_import`

A repeated old website import cannot overwrite a current non-null `game_live` observation.

Result: **PASS**

### Rerun / idempotency

Repeated authorized upload preserved counts of:

- canonical areas;
- canonical buildings;
- website catalog maps;
- website point records;
- area links;
- point links.

Result: **PASS**

### Personal Cabinet

Backend test:

- manager access returned the newly imported map through `cabinet_maps()`;
- private map data returned canonical overlay immediately.

Live website check:

- Maps tab exists;
- `maps_access || maps_manage` controls visibility;
- Personal Cabinet loads `/maps`;
- `renderMapsIndex()` remains active.

Result: **PASS**

## Scanner safety

Current live userscript SHA256:

`bddc55fc46bd4fe8da70c37799a35b74f3924015b071a3e692c532f0f7e6d766`

Verified live source:

- scanner marker:
  `maps-parallel-read-20260920-r6-safe5`
- read concurrency:
  `HK_MAP_READ_CONCURRENCY = 5`
- coordinate marker:
  `maps-coordinates-column-row-20260920-r2`
- payload revision:
  `column-row-v1`

Safe active-building intersection was explicitly verified:

1. building ID must exist in current active player buildings;
2. building ID must also map to a district through the game-area building mapping;
3. if a selected-district set is present, the mapped district must be selected;
4. only that resulting intersection is read by the parallel workers.

Result:

**PASS**

## Production read-only verification

W8 performed no production writes.

Current shared website bridge:

- `hk_maps_catalog = 235`;
- `hk_map_points = 235`;
- `hk_map_area_links = 25`;
- `hk_map_point_links = 2007`;
- duplicate canonical targets = **0**.

Three real linked districts were sampled read-only:

### New York — hk_newyork4026

- canonical area: `6618d3a0-91c9-44ff-8029-eba045469962`;
- point links: **451**;
- canonical buildings: **1101**;
- NULL buildings: **649**;
- investment buildings: **8**;
- source histogram:
  - `game_live: 668`;
  - `hk_maps_import: 433`.

### Moscow — hk_moscow1226

- canonical area: `9ea6ff78-b881-45b3-b92d-a8f1da8eca05`;
- point links: **29**;
- canonical buildings: **117**;
- NULL buildings: **0**;
- investment buildings: **3**;
- source histogram:
  - `game_live: 114`;
  - `hk_maps_import: 3`.

### Saint Petersburg — hk_saintpetersburg0003

- canonical area: `fbd2e69c-09fd-44b8-b71f-182c01652d9c`;
- point links: **16**;
- canonical buildings: **315**;
- NULL buildings: **268**;
- investment buildings: **6**;
- source histogram:
  - `game_live: 309`;
  - `hk_maps_import: 6`.

This confirms mixed live/import provenance and unknown buildings coexist correctly in real production districts.

## Server state

Current live server SHA256:

`b5189981acade420e1aaa533dec8b745c0e16969bf1def0c5008aa297f2a2812`

W8 deployed no server change.

## Final W1–W8 result

The two directions now share one canonical knowledge layer:

`map_areas / map_buildings / map_area_aliases`

Website visualization stays separate:

`hk_maps_catalog / hk_map_points`

Durable bridges:

- `hk_map_area_links`;
- `hk_map_point_links`.

Behavior:

- userscript knowledge automatically appears on linked website maps;
- authorized website uploads automatically enter userscript/shared knowledge;
- no periodic two-database synchronization exists or is required;
- provenance protects current live observations;
- geometry is not duplicated into the canonical knowledge tables.

## W8 gate

- userscript → shared DB → website, multiple districts — **PASS**
- website/import → shared DB → userscript, multiple districts — **PASS**
- coordinates — **PASS**
- aliases — **PASS**
- room_count — **PASS**
- investment behavior — **PASS**
- unknown/null — **PASS**
- source priority — **PASS**
- rerun/idempotency — **PASS**
- Personal Cabinet — **PASS**
- scanner 5 read-only workers — **PASS**
- safe active-building intersection — **PASS**
- production writes by W8 — **NO**

**W8 = PASS.**

**Website ↔ Maps shared knowledge link = PASS.**

The W1–W8 shared-knowledge subproject is complete.

Normal Stage 2 work may resume only on the next explicit user instruction.
