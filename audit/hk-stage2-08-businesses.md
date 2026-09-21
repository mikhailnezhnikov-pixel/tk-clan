# HK Stage 2.08 — Businesses / Бизнесы

## Status

**CANONICAL_TRANSFER_GAP_CONFIRMED**

## Current production baseline

- userscript: `1.17.22`
- core: `core-20260921-r24-explore-production-ui`
- existing Businesses functionality is already substantial and must be preserved:
  - manual rearrangement;
  - smart optimizer;
  - bonus analysis;
  - presets/original-layout restore;
  - manager-capacity handling;
  - free-only speed-up policy;
  - authoritative slot rereads;
  - rollback path;
  - shared Runner Pause/Stop integration.

## Pinned donor preflight

Pinned source: `скрипт Kokkaras,.txt`.

Donor Businesses includes a separate canonical catalog/planner layer that current production does not have:
- all business cards browser;
- business search;
- bonus filter;
- exact-bonus-only filter;
- active-copy limit display;
- source/family/card metadata;
- target quantity;
- owned-now / missing calculation;
- upgrade/craft route planner;
- Project Bureau recipe routes;
- Event Fair acquisition route when contextually valid;
- worker/upgrading capacity calculation.

Representative donor symbols:
- `businessesBetaState`
- `businessesPlannerCapacity()`
- `businessesPlannerRouteOptions()`
- `businessesPlannerOwnedCount()`
- `businessesPlannerOwnedBusinessInventory()`

These symbols are absent from current production.

## Transfer decision

Do **not** replace or rewrite the current rearrangement/optimizer.

Stage 2.08 will add the missing donor catalog/planner as an additional Businesses layer, reusing current shared:
- player snapshot;
- static `/business_items` capture;
- recipe metadata/localization;
- existing UI visual system;
- mutation gate for any future action-enabled planner step.

First transfer slice must be **read-only**:
1. catalog;
2. search;
3. bonus filters;
4. card details;
5. active-copy limit;
6. planner target + route calculation;
7. owned/missing + worker capacity.

No crafting, fair buying, rearrangement, or other mutation is to be added in the first slice.

## Protected invariants

The transfer must preserve:
- current manual rearrangement and optimizer;
- Buildings 2.06 LIVE PASS;
- Explore 2.07 LIVE PASS;
- Maps safe5 / concurrency 5;
- passive auth safety;
- Wars parallel work;
- FULL235 separate track.

## Next

Build **Businesses canonical read-only catalog/planner r1**, then run static/live read-only verification before exposing any planner mutations.
