# HK Stage 2 Bug — Explore canonical transfer gap

## Status

**CONFIRMED**

## Scope

Stage 2.07 — Explore / Исследование.

## Pinned donor

Exact uploaded `скрипт Kokkaras,.txt`, canonical SHA256:
`28c3104020ecb7f54d0d51a72d067404d0176bc069d59fcca417d66817d1fcf1`.

## Current baseline

Current Explore page is district/map research:
`/cities -> /game_area/* -> /game_area/*/buildings`
and routes to `submitOwnedMapAreas(true)`.

That is Maps functionality, not donor `Explore Buildings`.

## Confirmed donor behavior missing

Donor exports `showExploreBuildingsMenu` and `runExploreBuildings` and supports:
- district/building-type filters;
- starting tiers and target tier;
- target-tier exploration/battles;
- full per-building event completion;
- fast/manual battles;
- tier upgrades;
- optional purchase of missing renovation materials;
- remort / fast remort paths;
- configured action/battle/between-building delays;
- per-building state/progress tracking.

## Required fix

Transfer donor Explore Buildings after Stage 2.06 Buildings has a live candidate.
Do not treat district map research as Explore parity.
