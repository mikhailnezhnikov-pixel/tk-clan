# HK Stage 2 Bug — Maps building study link loss

## Status

**CONFIRMED**

## Symptom

A district can contain hundreds of buildings that the player has already opened, while the map still renders most of them as `не исследовано` / unknown crystal-room count.

## Root causes

1. `mapAreaPayload()` builds `building_id -> area_id` only in the in-memory `mapBuildingAreas` map.
2. That association disappears after a page reload.
3. `acceptBuildingStudy()` previously returned immediately when `mapBuildingAreas.get(buildingId)` was empty, so a valid `/player/building` response could be discarded instead of being attached to its district.
4. Map account scan used the compact `/player/me.buildings` rows to calculate `room_count`. Those rows normally do not contain the full room/event structure, so active buildings were submitted with unknown room count.
5. The scanner did not perform a safe read-only `/player/building?building_id=...` backfill for already-active buildings.

## Required behavior

- persist owned `building_id -> area_id` relations by player;
- rebuild the relation from owned `/game_area/{id}/buildings` when a building study arrives without a known area;
- on map scan, first build district/building relations, then safely reread only buildings already present in `/player/me.buildings`;
- never call `/player/building` for a closed/unopened building during scanner backfill;
- calculate crystal rooms from the full building study response and submit them back to the exact district/building;
- keep the scanner pausable/stoppable and rate-limited.

## Candidate

`HK_MAP_SCANNER_REV = 'maps-building-scan-20260920-r2'`

Build-only verification:
- source live SHA256: `0931ee3eb65a16f9dd768fe51b9a84b897620e011c51ee9e0226d92f37b9e686`;
- candidate SHA256: `a250839d884d23ff12fb2808364338d62b5555554fad2edc4d7b4a1e0cec177e`;
- Python compile: PASS;
- JS syntax: PASS;
- deployed: no (build-only stage).
