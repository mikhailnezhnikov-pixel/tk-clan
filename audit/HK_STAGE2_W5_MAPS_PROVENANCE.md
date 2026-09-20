# TopKing Stage 2 — W5 Source provenance and conflict rules

Date: 2026-09-20  
Stage: W5 — Source provenance and conflict rules  
Result: **PASS**

## Goal

Normalize the source of every canonical `map_buildings.room_count` value and enforce the conflict rule:

`game_live` has priority over imported/historical knowledge.

A later old import must not overwrite a newer authoritative live game observation.

W5 does not migrate the 235 website maps.

## Schema

Two columns were added to `map_buildings`:

- `knowledge_source` — normalized source of the current room knowledge;
- `knowledge_observed_at` — timestamp of the observation that owns the current room value.

Supported normalized sources:

- `game_live`;
- `hk_maps_import`;
- `legacy`.

Server marker:

`HK_MAP_PROVENANCE_W5_V1`

Patch:

`deploy/topking/patch_server_maps_shared_kb_w5.py`

## Backfill rules

Existing rows are normalized once during `init_db()`:

- `last_player_id = source-hk-maps-import` → `hk_maps_import`;
- `last_player_id LIKE anon-%` → `game_live`;
- all other historical/source identifiers → `legacy`.

For backfilled rows:

`knowledge_observed_at = last_seen`.

Live result after migration:

- total `map_buildings`: **162170**;
- `game_live`: **162167**;
- `hk_maps_import`: **3**;
- `legacy`: **0**;
- invalid/zero provenance timestamps: **0**.

The schema supports `legacy`, but no existing live row required that category at the time of W5 migration.

## New write classification

New canonical submissions are classified before contributor anonymization:

- normal player/userscript submission → `game_live`;
- `source-hk-maps-import` → `hk_maps_import`;
- `kokkaras-import`, `historical-har`, and other `source-*` historical paths → `legacy`.

## Conflict policy

### game_live

A current game observation with a non-null room count is authoritative.

It may replace an existing imported/historical/non-null room count and updates:

- `room_count`;
- `has_events`;
- `last_player_id`;
- `knowledge_source=game_live`;
- `knowledge_observed_at`.

Previously, a fully known district returned `ignored_complete` before processing buildings. W5 changes that boundary:

- complete districts may still short-circuit historical/import paths;
- `game_live` is **not** short-circuited and can refresh room knowledge on a fully known district.

### hk_maps_import

The website/HK Maps import remains conservative:

- it fills only `room_count IS NULL`;
- it sets `knowledge_source=hk_maps_import`;
- it records `knowledge_observed_at`;
- it never overwrites an existing non-null value, including `game_live`.

### legacy

Historical/legacy submissions do not replace already complete canonical room knowledge.

### duplicate-area merge

The duplicate-area merge path was also updated to preserve provenance. If a merged row competes with existing knowledge:

- a non-null value can fill an unknown;
- a newer `game_live` value may replace non-game or older game-live knowledge;
- otherwise existing canonical knowledge is retained.

This prevents a future manual merge from silently resetting provenance to `legacy`.

## Explicit regression

Build/regression run:

`35512193549` — **PASS**

Candidate/live W5 server SHA256:

`8e3664d5a437ea7e924e91f4b6de3944e75b80e0bafbed5fc10769e37f71b22d`

The temporary-DB regression explicitly proved:

- W5 backfill classification: PASS;
- `game_live` updates a fully complete district: PASS;
- a later `hk_maps_import` cannot overwrite that `game_live` value: PASS;
- a later legacy/Kokkaras submission cannot overwrite the complete canonical value: PASS;
- `map_detail()` exposes `knowledge_source` and `knowledge_observed_at`: PASS.

The regression sequence was:

1. start with imported room count `2`;
2. backfill it as `hk_maps_import`;
3. submit fresh live-game room count `0` to a complete district;
4. verify canonical value becomes `0 / game_live`;
5. run a later website import trying to write `3`;
6. verify canonical value stays `0 / game_live`;
7. run a later legacy import trying to write `5`;
8. verify it is ignored for the complete district.

This is the explicit W5 conflict regression required by the checkpoint.

## Live deployment

Live run:

`35512251926` — **PASS**

Live server SHA256:

`8e3664d5a437ea7e924e91f4b6de3944e75b80e0bafbed5fc10769e37f71b22d`

The live migration changed provenance metadata only. Verification confirmed that room knowledge totals did not change during backfill.

Pilot `hk_moscow1226` after W5:

- canonical area: `9ea6ff78-b881-45b3-b92d-a8f1da8eca05`;
- canonical room histogram: `0:114, 2:3`;
- normalized source histogram:
  - `game_live: 114`;
  - `hk_maps_import: 3`;
- W3 imported buildings remain `hk_maps_import`;
- all provenance timestamps are positive/inspectable.

## W4 compatibility

The W4 Website ← canonical overlay remained unchanged.

Pilot website response after W5:

- `0:26`;
- `1:1`;
- `2:3`;
- `3:2`.

Stored geometry remains unchanged:

`58ead2cc505d010b676ff5aac55b230c9609809600b69681c99f793d593c6cd6`

W5 did not alter `hk_map_points`, point links, or district links.

## Userscript invariants

W5 is server-only.

Current public userscript SHA256:

`df677e603e0a180e0e2e2b5ce27af268ab788ced12e4e6b2036d4c9b23c78115`

Verified:

- Maps scanner: `maps-parallel-read-20260920-r6-safe5`;
- read concurrency: **5**;
- coordinate marker: `maps-coordinates-column-row-20260920-r2`;
- coordinate revision: `column-row-v1`;
- W5 changed userscript: **NO**.

## W5 gate

Required:

1. imported data cannot overwrite newer `game_live` knowledge — **PASS**;
2. source is inspectable — **PASS**;
3. source timestamp is inspectable — **PASS**.

**W5 = PASS.**

W6 is **NOT STARTED**. Stop here until explicit user instruction.
