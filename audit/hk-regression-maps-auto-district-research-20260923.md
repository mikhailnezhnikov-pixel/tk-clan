# HK regression — automatic district research

## User report

Opening/using HK can unexpectedly start **District research** with progress such as `1/48`, blocking normal play until the Runner finishes.

Expected behavior:
- opening Maps must be read-only;
- district/account map research starts only after an explicit user action.

## Root cause

Two automatic paths existed in userscript 1.17.37:

1. `refreshModuleLive('maps')`
   - after `/player/me`, checked `mapContributionByPlayer`;
   - if more than 24 hours had passed, it called `submitOwnedMapAreas(true)`;
   - this also ran when a remembered Maps tab was restored on startup.

2. `loadMapIndex(contribute=true)`
   - contained a second 24-hour auto-contribution path calling `submitOwnedMapAreas(true)`.

`submitOwnedMapAreas(true)` starts HK Runner **District research** and iterates all owned districts, which explains `1/48, 2/48...` and the temporary interaction lock.

## 1.17.38 fix

Marker:
`maps-manual-scan-only-20260923-r1`

Changes:
- removed the 24-hour auto-contribute branch from `loadMapIndex`;
- Maps live refresh now only:
  - refreshes `/player/me`;
  - reads the saved/public map index;
- full district/account scanning remains available only via:
  - `#hk-map-scan → submitOwnedMapAreas(true)`.

Static invariant:
- exactly one active `submitOwnedMapAreas(true)` call remains;
- that call is the explicit scan button handler.

No map mutation/research is executed by CI.
