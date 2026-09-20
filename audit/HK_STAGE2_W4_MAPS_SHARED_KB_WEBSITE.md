# TopKing Stage 2 — W4 Shared knowledge → Website pilot

Date: 2026-09-20  
Stage: W4 — Shared knowledge → Website, one-map pilot  
Result: **PASS**

## Pilot

- website map: `hk_moscow1226`;
- canonical area: `9ea6ff78-b881-45b3-b92d-a8f1da8eca05`;
- canonical coordinates: Moscow `x=26,y=12`;
- geometry source remains `hk_map_points`;
- canonical knowledge source remains `map_buildings`.

W4 does not migrate additional website maps.

## Gap confirmed before W4

Live `hk_map_data()` previously returned `hk_map_points.points_json` directly.

Therefore Personal Cabinet → Maps could render the historical website values, but a later userscript/player update to canonical `map_buildings.room_count` did not automatically affect the website map.

No reverse shared-knowledge read existed.

Preflight evidence:

`audit/hk-stage2-w4-functions.txt`

## Point → canonical building bridge

The compact website geometry contains 32 delta-coded positive points but does not contain `building_id`.

W3 had already proven 29 exact point-in-polygon matches against building IDs already present in the canonical pilot area, with 0 ambiguous matches.

W4 persists those exact matches in:

`hk_map_point_links`

Schema semantics:

- `map_key`;
- `point_index`;
- `building_id`;
- `match_method`;
- `linked_at`;
- primary key: `map_key + point_index`;
- unique per `map_key + building_id`.

Pilot rows: **29**.

Match method: `osm_point_in_polygon`.

The three W3-unmatched points are deliberately not linked and retain their source website values.

Pilot mapping source:

`deploy/topking/hk_moscow1226-point-links-w4.json`

## Dynamic website overlay

Server marker:

`HK_MAP_WEBSITE_OVERLAY_W4_V1`

Patch:

`deploy/topking/patch_server_maps_shared_kb_w4.py`

For point-mode website maps:

1. coordinates/deltas continue to come from stored `hk_map_points.points_json`;
2. for a linked point, server resolves `map_key → canonical_area_id → building_id`;
3. current `map_buildings.room_count` replaces only the point's crystal/room flag at response time;
4. original investment bit is preserved from website geometry;
5. source geometry is never rewritten;
6. a point without a safe link remains source fallback.

Current `hk_map_data()` returns overlay metadata:

- canonical enabled: true;
- linked points: 29;
- applied points: 29;
- fallback points: 3.

Final live server SHA256:

`c1c583230f632ed38c654a00541809b1a7cb2f2bf0296708f4c44b2456ad46ce`

Final server snapshot confirms the live `hk_map_data()` calls `hk_map_points_with_canonical()`.

## Dynamic-update regression

Build/regression run: `35511398010`.

The W4 code itself passed before the workflow's later Git push race:

- dynamic canonical read: PASS;
- investment bit preservation: PASS;
- geometry unchanged: PASS.

Temporary DB test:

1. website source point stored a historical room flag;
2. canonical `map_buildings.room_count` was changed;
3. a second `hk_map_data()` call immediately returned the new canonical value;
4. `hk_map_points.points_json` remained byte-for-byte unchanged;
5. no export/import/sync step was run.

This proves the intended player-scan path: once a scan changes canonical `map_buildings`, reopening/fetching the website map reads that current value automatically.

## Live pilot result

Live deployment run: `35511455366`.

The following steps passed:

- exact W3 server precondition;
- W4 candidate build;
- live pilot precheck;
- server-only deploy;
- creation/use of point-link relation;
- all 29 pilot point links;
- website response from canonical knowledge.

Stored source geometry before and after:

- point count: **32**;
- SHA256: `58ead2cc505d010b676ff5aac55b230c9609809600b69681c99f793d593c6cd6`;
- geometry changed: **NO**.

Historical source positive histogram was:

- 1: 17;
- 2: 12;
- 3: 3.

After W4, the website response is dynamically rendered from current canonical knowledge for the 29 safe links:

- 0: **26**;
- 1: **1**;
- 2: **3**;
- 3: **2**.

Interpretation:

- 26 safely mapped points now show the existing canonical game-scan value `0` instead of stale historical positive source values;
- the 3 W3-imported canonical rows show `2`;
- the 3 unmatched website points stay source fallback: two `3`, one `1`.

Investment points remain **3**.

This is direct evidence that website rendering is now using current shared canonical knowledge rather than merely replaying the stored historical flags.

W4 wrote **zero** `map_buildings` rows.

## No duplication

- pilot point links: 29;
- unique linked canonical buildings: 29;
- pilot district at Moscow `26:12`: exactly 1;
- duplicate district created: **NO**;
- `hk_map_points` geometry duplication: **NO**;
- bulk migration: **NO**.

## Client drift during W4

The deployment workflow's final client assertion expected scanner r5 and therefore failed after all W4 server/data verification steps had passed.

This is not a W4 regression.

In the parallel Maps work, scanner concurrency was intentionally reduced from 10 to 5:

- current marker: `maps-parallel-read-20260920-r6-safe5`;
- `HK_MAP_READ_CONCURRENCY = 5`;
- submit batch remains 200;
- safe active-building intersection remains;
- coordinate marker remains `maps-coordinates-column-row-20260920-r2`.

Then parallel Explore E2 r5 deployed on top and explicitly verified:

`map_concurrency_5_preserved=PASS`.

Current public userscript SHA256 after Explore r5:

`df677e603e0a180e0e2e2b5ce27af268ab788ced12e4e6b2036d4c9b23c78115`

W4 changed userscript: **NO**.

## Pilot limitation

The pilot has no full contour package, so W4 validates the existing point-mode website path.

Full-contour canonical overlay and generalized mapping for additional maps are not claimed by W4 and remain later staged work.

## W4 gate

Required:

1. a canonical/player update is automatically reflected by a subsequent website map-data read — **PASS** by dynamic regression and live canonical overlay;
2. website pilot renders current shared canonical room counts — **PASS**;
3. no manual export/import is needed after the canonical change — **PASS**;
4. no geometry duplication — **PASS**;
5. no district duplication — **PASS**.

**W4 = PASS.**

W5 is **NOT STARTED**. Stop here until explicit user instruction.
