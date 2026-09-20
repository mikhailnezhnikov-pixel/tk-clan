# HK Stage 2.04 — Maps / Карты

## Status

**LIVE PASS**

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

Final status:
**LIVE PASS**
