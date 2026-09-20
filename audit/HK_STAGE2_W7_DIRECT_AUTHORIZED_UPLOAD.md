# TopKing Stage 2 — W7 Direct authorized website upload → shared knowledge

Date: 2026-09-21  
Stage: W7 — New website uploads write directly to shared knowledge  
Result: **PASS**

## Goal

Every new authorized HK Maps upload must perform one direct import path:

1. store/update website geometry in `hk_maps_catalog` / `hk_map_points`;
2. resolve or create the canonical district relation;
3. write imported building knowledge directly into canonical `map_buildings`;
4. preserve W5 source/provenance priority;
5. require **no later synchronization job**.

## W7 preflight

Evidence:

- `audit/hk-stage2-w7-import-preflight.txt`
- `audit/hk-stage2-w7-full-feature-sample.json`

The old website import path was split:

- `import_hk_maps_index()` wrote only `hk_maps_catalog`;
- `import_hk_map_points()` wrote only `hk_map_points`;
- neither called `link_hk_map_area()`;
- neither called `link_hk_map_points()`;
- neither wrote canonical room knowledge.

The compact private HK payload intentionally contains coordinates + bitmask only; it does **not** preserve building IDs.

The authorized full/raw map source does preserve exact game building identity. Live sample from `hk_newyork2332` proves game features include:

- feature `id`;
- `properties.building_id`;
- `properties.osm_id`;
- `properties.crystals`;
- `properties.is_investment`;
- `properties.faction`;
- `properties.building_generator`.

Sample IDs are exact canonical-style OSM IDs such as `way248169359`.

Therefore W7 does not reconstruct new uploads through external OSM/Overpass. It preserves exact IDs from the authorized source.

## New direct import path

Server patch:

`deploy/topking/patch_server_maps_shared_kb_w7.py`

Marker:

`HK_MAP_AUTHORIZED_UPLOAD_W7_V1`

New function:

`import_hk_authorized_map_upload(value)`

New CLI:

`server.py --import-hk-authorized-map FILE.json[.gz]`

Required authorized upload content:

- `catalog` — website catalog row;
- `points` — compact delta point array;
- `meta` — explicit canonical district metadata;
- `buildingsGeoJSON` — authorized full source preserving `building_id`;
- optional exact `point_links`.

No login/session/cookie data is stored.

## Coordinate safety

W7 never silently guesses coordinate orientation.

`meta.coord_revision` is mandatory and supports:

- `column-row-v1`;
- `canonical-xy`;
- explicit legacy `historical-yx`.

Any upload without an explicit supported coordinate revision is rejected.

This prevents a repeat of the Dubai historical X/Y ambiguity found in W6.

## Direct write sequence

For a validated upload the server:

1. parses full game features and exact `building_id` values;
2. decodes compact point metadata by bitmask:
   - `crystals = flag & 0x07`;
   - `investment = bool(flag & 0x08)`;
3. derives exact point → building links from supplied IDs / supplied full geometry;
4. calls `submit_map_area("source-hk-maps-import", area)`;
5. canonical resolution reuses an existing district when city + canonical X:Y matches;
6. otherwise a new canonical district is created from explicit upload metadata;
7. stores/updates `hk_maps_catalog`;
8. stores/updates `hk_map_points`;
9. persists `hk_map_area_links`;
10. persists exact `hk_map_point_links`;
11. writes room knowledge through the existing W5-safe import path.

The result explicitly returns:

- `direct_shared=true`;
- `sync_required=false`.

All operations are idempotent and safe to retry.

## Provenance / conflict behavior

Canonical imported knowledge uses:

`knowledge_source = hk_maps_import`

W5 remains authoritative:

- an imported value may fill unknown canonical knowledge;
- an existing non-null `game_live` value is never overwritten;
- a repeated upload does not create duplicate areas, area links, point links, or canonical buildings.

## Build regression

Build run:

`35520020636` — **PASS**

Build status:

`audit/hk-stage2-maps-shared-kb-w7-build-status.txt`

Candidate server SHA256:

`b5189981acade420e1aaa533dec8b745c0e16969bf1def0c5008aa297f2a2812`

Temporary DB regression proved:

- create new canonical district: PASS;
- resolve upload to existing canonical district: PASS;
- website geometry stored: PASS;
- point links created directly: PASS;
- userscript/shared `map_detail()` sees imported room knowledge immediately: PASS;
- no separate synchronization: PASS;
- later/repeated import cannot overwrite newer `game_live`: PASS;
- repeated import is idempotent: PASS;
- no duplicate district: PASS.

## Future authorized upload workflow

Workflow:

`.github/workflows/import-authorized-hk-map.yml`

Upload location:

`deploy/maps/authorized/*.json.gz`

Contract documentation:

`deploy/maps/authorized/README.md`

A new authorized upload now invokes exactly:

`server.py --import-hk-authorized-map FILE.json.gz`

The workflow validates that the returned result has:

- `ok=true`;
- `direct_shared=true`;
- `sync_required=false`;
- a canonical area ID.

No separate W3/W4/W6 synchronization command is required.

## Website point-mode bitmask correction

W6 discovered the real private payload bit layout. W7 also corrected the static website point renderer:

`maps/view/index.html`

Old point-mode logic incorrectly used `flag >= 7`.

Current logic:

- `investment = Boolean(flag & 0x08)`;
- `crystals = flag & 0x07`.

Point filters now include room values 6 and 7 as well.

This change affects website rendering only; the userscript was not changed.

## Live deployment

Live deployment run:

`35520130288` — **PASS**

All steps passed:

1. exact live server reread;
2. exact W7 candidate build;
3. server backup/deploy;
4. deployed W7 direct-upload integration test on a temporary SQLite DB;
5. live production DB read-only verification;
6. current Maps userscript invariant verification;
7. audit status write.

Live server SHA256:

`b5189981acade420e1aaa533dec8b745c0e16969bf1def0c5008aa297f2a2812`

Live status:

`audit/hk-stage2-maps-shared-kb-w7-live-status.txt`

The deployed integration test used only a temporary DB and left **0** production test rows.

Production W6 state after W7 deploy remains:

- `hk_maps_catalog = 235`;
- `hk_map_points = 235`;
- `hk_map_area_links = 25`;
- `hk_map_point_links = 2007`.

## Userscript invariants

W7 did not modify the public userscript.

Current userscript SHA256:

`bddc55fc46bd4fe8da70c37799a35b74f3924015b071a3e692c532f0f7e6d766`

Verified:

- scanner: `maps-parallel-read-20260920-r6-safe5`;
- coordinate marker: `maps-coordinates-column-row-20260920-r2`;
- coordinate revision remains `column-row-v1`.

## W7 gate

Required:

1. a new authorized website map becomes visible to shared/userscript knowledge automatically — **PASS**;
2. canonical relation is resolved or created in the same import path — **PASS**;
3. imported knowledge obeys W5 provenance rules — **PASS**;
4. no separate synchronization job is required — **PASS**.

**W7 = PASS.**

**W8 NOT STARTED.** Stop here until explicit user instruction.
