# TopKing Stage 2 — W3 Website → shared userscript knowledge pilot

Date: 2026-09-20  
Stage: W3 — Website → shared userscript knowledge, one-map pilot  
Result: **PASS**

## Goal

Use exactly one W2-linked website map and prove that authorized website/HK Maps crystal knowledge can be written into the canonical shared `map_buildings` knowledge layer and read back through the existing Maps detail path, without duplicating geometry or districts and without bulk migration.

Pilot:

- `map_key = hk_moscow1226`
- canonical area: `9ea6ff78-b881-45b3-b92d-a8f1da8eca05`
- website grid: Moscow `12:26` in historical `Y:X`
- canonical coordinates: `x=26, y=12`

## Source validation

The authorized HK Maps index for the pilot records:

- 117 buildings;
- 85 buildings with 0 crystals;
- 17 with 1 crystal;
- 12 with 2 crystals;
- 3 with 3 crystals;
- 32 positive/event buildings;
- 3 investment buildings.

The private compact website payload contains `point_count=32` and 96 flat values.

The existing website decoder was verified:

```text
delta longitude
delta latitude
flag
```

where:

- `flag >= 7` means investment;
- investment crystal count = `flag - 8`;
- otherwise crystal count = `flag`.

Decoded pilot histogram:

- 1 crystal: 17;
- 2 crystals: 12;
- 3 crystals: 3;
- investment positive points: 3.

This exactly matches the HK Maps index summary.

## Building-ID recovery audit

The compact website payload intentionally does not contain `building_id`.

For the pilot only, the 32 decoded geographic points were tested against OSM geometry for the 117 canonical building IDs already present in `map_buildings`.

Evidence: `audit/hk-stage2-maps-shared-kb-w3-osm-recovery.txt`

Results:

- exact point-in-polygon matches: **29/32**;
- ambiguous matches: **0**;
- unmatched: **3**;
- among the 29 exact matches:
  - current canonical `room_count=0`: 26;
  - current canonical `room_count=NULL`: 3.

The three exact matches whose canonical knowledge was still unknown were:

1. `way29242551 → room_count=2` — investment;
2. `way29242552 → room_count=2` — investment;
3. `way430609368 → room_count=2` — investment.

The three unmatched positive points were deliberately left untouched. Nearest-building tolerance was **not** accepted as authoritative W3 evidence.

The 26 exact positive source points whose canonical rows already had non-NULL `room_count=0` were also deliberately left untouched. W3 does not establish source precedence; that belongs to W5.

## W3 server implementation

Patch:

`deploy/topking/patch_server_maps_shared_kb_w3.py`

Marker:

`HK_MAP_ROOM_KNOWLEDGE_W3_V1`

Added:

`import_hk_map_room_knowledge(map_key, rows)`

and controlled CLI:

`server.py --import-hk-map-room-knowledge MAP_KEY FILE.json`

W3 safety behavior:

- map must already exist in `hk_map_area_links`;
- only existing canonical `map_buildings` rows may be updated;
- only rows with `room_count IS NULL` may be filled;
- existing non-NULL values are preserved;
- missing building IDs are reported, not inserted;
- geometry is never touched;
- no `map_areas` row is created;
- imported rows receive temporary source marker `source-hk-maps-import`;
- full normalized provenance/source-priority design remains W5 work.

## Build verification

Build run: `35510361084` — **PASS**

Build status:

`audit/hk-stage2-maps-shared-kb-w3-build-status.txt`

Candidate/live W3 server SHA256:

`26cf4729b90dd47da881760794b5bdcaef783c41b8fd4fba8e71b191f4d4f7e4`

Temporary DB regression proved:

- NULL-only fill: PASS;
- existing non-NULL preservation: PASS;
- `map_detail()` reads imported knowledge: PASS;
- rerun/idempotency: PASS;
- geometry unchanged: PASS;
- no duplicate district: PASS.

## Live pilot import

Deployment run: `35510477205`

Successful steps before the stale-client-SHA check:

- exact server candidate build: PASS;
- server-only backup/deploy: PASS;
- exactly three pilot room-count imports: PASS;
- idempotent rerun: PASS;
- live shared-knowledge verification: PASS.

Live result:

- `way29242551: NULL → 2`;
- `way29242552: NULL → 2`;
- `way430609368: NULL → 2`;
- non-NULL overwrite count: **0**;
- pilot room histogram after W3: `0:114, 2:3`;
- imported rows: **3**;
- source marker: `source-hk-maps-import`.

A second identical import filled **0** rows and preserved all 3, proving live idempotency.

## Existing shared Maps read path

After the import, the live server's existing canonical `map_detail(area_id)` returns the three pilot buildings with `room_count=2`.

This is the same canonical detail function used by the existing shared Maps detail API; no player rescan was performed to create these values.

Thus website-derived knowledge is present in the shared `map_buildings` layer and visible through the existing userscript read path.

## Geometry / district verification

After W3:

- `hk_map_points.point_count` for pilot: **32**;
- decoded source histogram remains `1:17, 2:12, 3:3`;
- geometry rewrite: **NO**;
- bridge rows: **1**;
- Moscow canonical district at `x=26,y=12`: exactly **1**;
- duplicate district created: **NO**;
- bulk map linking/migration: **NO**.

## Userscript SHA drift during W3

The first live verification workflow expected the old W2 userscript SHA:

`1932f3984a330edf234c02e80c0f27e1b845b299f3bb09875d166397dcded9d6`

That check failed **after** the W3 server/data checks had already passed.

The reason was independent parallel Explore E2 userscript deployment. W3 itself never copied, installed, or modified the userscript.

Final read-only verification run:

`35510595703` — **PASS**

Current public userscript SHA at final verification:

`76833b35de3620f7b946fac3c02fca021cd48d332e58c51ce74a40616c199c14`

Critical Maps invariants in that current userscript:

- scanner `maps-parallel-read-20260920-r5`: PASS;
- coordinates `maps-coordinates-column-row-20260920-r2`: PASS;
- `coord_revision:'column-row-v1'`: PASS.

Final verification evidence:

`audit/hk-stage2-maps-shared-kb-w3-final-verify.txt`

## Deferred intentionally

Not done in W3:

- no overwrite of the 26 canonical non-NULL zero rows;
- no inference/write for the 3 unmatched positive points;
- no source-priority policy;
- no full provenance schema;
- no bulk 26-map/235-map migration;
- no Personal Cabinet renderer change;
- no W4 reverse-direction rendering work.

These remain for later staged work, especially W5/W6.

## W3 gate

Required:

1. website/import knowledge becomes visible through canonical shared Maps detail without a new player scan — **PASS**;
2. no geometry duplication/change — **PASS**;
3. no district duplication — **PASS**.

**W3 = PASS.**

W4 is **NOT STARTED**. Stop here until explicit user instruction.
