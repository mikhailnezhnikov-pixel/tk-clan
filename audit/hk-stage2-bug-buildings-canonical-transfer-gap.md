# HK Stage 2 Bug — Buildings canonical transfer gap

## Status

**CONFIRMED**

## Scope

Stage 2.06 — Buildings / Здания.

## Pinned donor

Exact uploaded `скрипт Kokkaras,.txt`, canonical SHA256:
`28c3104020ecb7f54d0d51a72d067404d0176bc069d59fcca417d66817d1fcf1`.

## Current baseline

Current `stage2i-buildings-explore-20260919-r1` Buildings page only:
- lists active account buildings;
- refreshes `/player/me`;
- manually reads one `/player/building?building_id=...`.

It does not contain donor `runBuildings(filters)`.

## Confirmed donor behavior missing

- protected buildings candidate plan;
- filters: minimum crystals, building type, favorite threshold;
- calculation of free active-building slots;
- selection of best eligible unopened candidates;
- opening candidates through `/player/building?building_id=...`;
- handling max-active-building 409 safely;
- adding opened buildings to favorites when threshold is met and slots remain;
- Runner progress, pause/stop, per-building delay;
- final authoritative state refresh / rerun.

## Required fix

Transfer Buildings automation into the current HK runtime using current auth, mutation gate, runner and state store.
Do not replace donor source with historical reconstruction.
Do not modify Explore in the Buildings patch.
