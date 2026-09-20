# HK Stage 2.04 — Maps / Карты

## Status

**BUG_CONFIRMED_NO_FIX_APPLIED**

## Canonical implementation

Marker:
`HK_STAGE2E_RUNNER_REV = 'stage2e-maps-20260919-r1'`

The current baseline retains the transferred Maps path:
- account map read from `/player/me`;
- city list from `/cities`;
- district geometry/state from `/game_area/{id}`;
- district building definitions from `/game_area/{id}/buildings`;
- map contribution through `/api/v1/maps/submit`;
- index reread through `/api/v1/maps/list`;
- detail reread through `/api/v1/maps/detail`;
- map filters, geometry render and selected-building detail;
- account/uploaded source switch;
- Runner integration with pause/stop and abort-aware pacing.

## Historical live verification

Existing live record:
- version: 1.16.5;
- module: `maps-district-research`;
- marker: `stage2e-maps-20260919-r1`;
- syntax: PASS;
- deployed/live roundtrip: identical;
- recorded SHA256: `ef61e4dbf7dbee2cec2bdacc3ac96156cdd3bf41ab7c02576c23ac22dcb9b9f0`.

Evidence file:
`audit/hk-1165-live-status.txt`

## Current-state revalidation

Current baseline still contains the exact Stage 2E safety/action path required by the original patch:
- explicit `hkRunner.running` guard;
- `hkRunner.start` for district research;
- pause checkpoint via `hkRunner.waitIfPaused()`;
- abort handling;
- `gameRetryDelay(180)`;
- resulting map index reread via `loadMapIndex(false)`;
- `hkRunner.finish` on completion.

Current baseline is the synchronized live candidate after Bosses r2, whose live/public roundtrip passed. Bosses changes are isolated to the Bosses block and did not require a Maps patch.

## Stage 2 matrix

- UI: PASS
- live read: PASS
- calculation/normalization: PASS
- action: PASS
- state update: PASS
- rerun/readback: PASS
- pause/stop: PASS
- syntax/current live synchronization: PASS

No confirmed Maps regression was found.
No Maps patch or redeploy was required.

Historical status before scanner bug discovery:
**REOPENED**


## Building-study scanner r2 — reopened after live bug report

A real live regression was confirmed from the district map: many buildings already opened by the player remained `не исследовано` because the scanner did not reliably attach full `/player/building` study responses to their district and did not reread all already-active buildings during account map scan.

Bug ticket:
`audit/hk-stage2-bug-maps-building-study-link-loss.md`

Fix marker:
`HK_MAP_SCANNER_REV = 'maps-building-scan-20260920-r2'`

Fix behavior:
- persists owned `building_id -> area_id` mapping per player;
- lazily rebuilds that mapping from owned `/game_area/{id}/buildings` when a building response arrives without an area;
- account map scan starts from fresh authoritative `/player/me`;
- after district mapping, rereads **only buildings already active in /player/me.buildings** through read-only `/player/building`;
- calculates crystal-room count from the full building response;
- submits the observation to the exact district/building;
- closed/unopened buildings are not touched by scanner backfill;
- pause/stop and pacing are retained.

Build-only verification:
- source live SHA256: `0931ee3eb65a16f9dd768fe51b9a84b897620e011c51ee9e0226d92f37b9e686`;
- candidate SHA256: `a250839d884d23ff12fb2808364338d62b5555554fad2edc4d7b4a1e0cec177e`;
- Python compile: PASS;
- JS syntax: PASS.

Live verification:
- deploy: PASS;
- service: PASS;
- syntax: PASS;
- public byte equality: PASS;
- live/public SHA256: `a250839d884d23ff12fb2808364338d62b5555554fad2edc4d7b4a1e0cec177e`;
- baseline sync: PASS.

Current Maps status:
**SCANNER_R2_LIVE_CANDIDATE**

Required user confirmation:
1. run “Считать карты аккаунта”;
2. wait for the active-building reread phase to finish;
3. reopen the affected district;
4. confirm that currently active buildings are now colored with 0/1/2/3/4/5+ 💎 instead of remaining unknown.


## Canonical coordinate fix r1

Confirmed coordinate orientation bug:
- game API grid axes are row/column;
- user-facing district coordinates are X:Y = column:row;
- Maps previously stored raw API x:y, producing reversed labels such as 32:23 instead of 23:32.

Fix marker:
`HK_MAP_COORDS_REV = 'maps-coordinates-column-row-20260920-r1'`

Canonical submit mapping now stores:
- `x = API y`;
- `y = API x`.

Rumor routing remains on its existing raw-grid compatibility path and was explicitly preserved.

Build-only verification:
- source live SHA256: `a250839d884d23ff12fb2808364338d62b5555554fad2edc4d7b4a1e0cec177e`;
- candidate SHA256: `f52ed4a3c61a3833941f8bf0c5e8016be8a59eac2ca4f6f352dd28ee16c3b290`;
- syntax: PASS.

Live verification:
- deploy: PASS;
- service: PASS;
- public byte equality: PASS;
- live/public SHA256: `f52ed4a3c61a3833941f8bf0c5e8016be8a59eac2ca4f6f352dd28ee16c3b290`;
- baseline sync: PASS.

Existing server rows are corrected when the district is submitted again through “Считать карты аккаунта”.


## Rollback of scanner r2 and coordinate r1

User explicitly requested that neither of the two experimental fixes remain applied.

Rolled back from:
- `maps-building-scan-20260920-r2`;
- `maps-coordinates-column-row-20260920-r1`.

Restored exact pre-fix live:
- source commit: `4c0f3d6c5b1278d3547ba53fd593b484f826ff92`;
- live/public SHA256: `0931ee3eb65a16f9dd768fe51b9a84b897620e011c51ee9e0226d92f37b9e686`;
- syntax: PASS;
- service: PASS;
- public byte equality: PASS;
- scanner r2 marker: ABSENT;
- coordinate r1 marker: ABSENT;
- Buildings canonical r1 remains present.

The confirmed Maps building-study attribution issue and reversed-coordinate issue remain **unfixed by design** after this rollback. Do not treat the two reverted implementations as active or approved.

Current status:
**BUG_CONFIRMED_NO_FIX_APPLIED**


## Safe active-building scanner r3

Marker:
`HK_MAP_SCANNER_REV = 'maps-active-intersection-20260920-r3'`

Applied scanner source rule:
- district/building membership comes from `/game_area/{area}/buildings`;
- detailed `POST /player/building?building_id=...` reads are performed only for IDs present in `/player/me.buildings` **and** mapped to the selected owned district;
- active building ID normalization accepts both `row.id` and `row.building_id`;
- `mapAreaPayload()` uses the same normalized active ID rule;
- `/events` is explicitly ensured before bulk room counting;
- if the event catalog is unavailable, bare event IDs cannot produce a false `room_count=0`; such buildings remain unknown unless a direct crystal marker or direct crystals field is present;
- direct `crystals/crystal_rooms/crystalRooms` remains first priority;
- otherwise room/event matching uses `item_fake_prematmaxeventlvl` and the event catalog;
- scanner does not call `/player/building` for closed/unopened buildings;
- explicit building opening remains isolated in `buildingCanonOpen()` through `hkMutationGate`.

Build verification:
- source live SHA256: `f52ed4a3c61a3833941f8bf0c5e8016be8a59eac2ca4f6f352dd28ee16c3b290`;
- candidate SHA256: `f8a34bff26fd449f315f07a2ef8e6a8a6e8169ea62f463e7efe527766d698101`;
- Python compile: PASS;
- JS syntax: PASS.

Live verification:
- deploy: PASS;
- service: PASS;
- public byte equality: PASS;
- live/public SHA256: `f8a34bff26fd449f315f07a2ef8e6a8a6e8169ea62f463e7efe527766d698101`;
- baseline sync: PASS.

Current status remains **LIVE_CANDIDATE** pending user scan confirmation.


## Parallel active-building reader r4

Marker:
`HK_MAP_SCANNER_REV = 'maps-parallel-read-20260920-r4'`

Performance changes:
- safe source intersection from r3 is unchanged;
- detailed `/player/building` reads are now processed by up to 6 concurrent read-only workers;
- scanner observations are accumulated in memory;
- map submissions are grouped by district and sent in batches of up to 100 buildings;
- if a batch submit fails, only that batch falls back to the previous one-building submit path;
- game-side 429 / transient failures / player-state locks continue to use the existing retry/backoff logic;
- Pause/Stop remains runner-controlled, and Stop aborts in-flight game requests through the shared runner signal;
- unopened buildings remain excluded because workers consume only the safe `/player/me.buildings ∩ mapped district building IDs` set.

Build verification:
- source live SHA256: `f8a34bff26fd449f315f07a2ef8e6a8a6e8169ea62f463e7efe527766d698101`;
- candidate SHA256: `f4f5a74ed8a4cc25b63ef11adf714d358ada0399f95a765bfedb21728a6162ca`;
- Python compile: PASS;
- JS syntax: PASS.

Live verification:
- deploy: PASS;
- service: PASS;
- public byte equality: PASS;
- live/public SHA256: `f4f5a74ed8a4cc25b63ef11adf714d358ada0399f95a765bfedb21728a6162ca`;
- baseline sync: PASS.

Current status remains **LIVE_CANDIDATE** pending user timing/behavior confirmation.


## Parallel active-building reader r5

Marker:
`HK_MAP_SCANNER_REV = 'maps-parallel-read-20260920-r5'`

Performance tuning over r4:
- concurrent read-only `/player/building` workers increased from 6 to 10;
- map submit batch size increased from 100 to 200 building observations;
- safe active-building intersection and event-catalog guards are unchanged;
- existing retry/backoff for 429/transient/player-lock responses remains active;
- unopened buildings remain excluded.

Build verification:
- source live SHA256: `f4f5a74ed8a4cc25b63ef11adf714d358ada0399f95a765bfedb21728a6162ca`;
- candidate SHA256: `d4c84856ffcad0617ce783451c054205491f7d0d956bf7e7ec1ae5315480680a`;
- syntax: PASS.

Live verification:
- deploy: PASS;
- service: PASS;
- public byte equality: PASS;
- live/public SHA256: `d4c84856ffcad0617ce783451c054205491f7d0d956bf7e7ec1ae5315480680a`;
- baseline sync: PASS.

Current status remains **LIVE_CANDIDATE** pending user timing/behavior confirmation.


## Canonical coordinate backend r2

Confirmed live backend bug:
- userscript was already submitting corrected X:Y = column:row;
- existing `map_areas.x/y` were sticky because backend used `x=COALESCE(map_areas.x,excluded.x)` and the same for y;
- completed maps returned `ignored_complete=True` before any coordinate update.

Fix:
- userscript now sends `coord_revision: column-row-v1` with full district payloads;
- backend accepts coordinate replacement only for this explicit revision;
- trusted x/y update is performed before the completed-map early return;
- legacy/unversioned submissions cannot overwrite corrected coordinates;
- building-only batch submissions do not carry coordinates and therefore cannot change district numbers.

Verification:
- complete-map regression test: old 32:23 -> submitted 23:32 -> stored 23:32 while `ignored_complete=True`: PASS;
- client SHA256: `1932f3984a330edf234c02e80c0f27e1b845b299f3bb09875d166397dcded9d6`;
- server SHA256: `1fb8007651c6772400a1e6bc8b7f3152d0f907942a7fa0140e854e17d7f2a2e1`;
- public byte equality: PASS;
- service: PASS.

Current coordinate marker:
`HK_MAP_COORDS_REV = 'maps-coordinates-column-row-20260920-r2'`
