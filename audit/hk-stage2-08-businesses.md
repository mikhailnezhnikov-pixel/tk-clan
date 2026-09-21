# HK Stage 2.08 — Businesses / Бизнесы

## Status

**CATALOG_R1_LIVE_CANDIDATE_USER_UI_CHECK_PENDING · REARRANGE_UI_GUARD_R1_LIVE_CANDIDATE_USER_VISUAL_CHECK_PENDING**

## Current production baseline

- userscript: `1.17.23`
- core: `core-20260921-r25-businesses-catalog`
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

## Businesses canonical catalog r1 — userscript 1.17.23 (2026-09-21)

The first donor-based transfer slice is now live and remains strictly read-only.

Delivered:
- marker: `businesses-catalog-readonly-20260921-r1`;
- third Businesses subtab: **Каталог / Catalog**;
- all known business cards from current static metadata;
- text search;
- bonus filter;
- exact-bonus-only filter;
- visible tier, owned count, active count and active-copy limit;
- read-only target quantity;
- owned-now / missing calculation;
- worker/upgrading capacity summary;
- known Project Bureau recipe routes from the shared recipe database.

Explicitly not included in r1:
- no catalog-driven purchases;
- no Project Bureau craft action;
- no Fair reroll/buy action;
- no automatic rearrangement from the catalog.

Existing production functionality remains intact:
- manual rearrangement;
- optimizer;
- bonus analyzer;
- rollback;
- manager handling;
- authoritative postconditions.

Verification:
- Stage 2.08 source preflight `35580260242`: PASS;
- catalog predeploy `35580823075`: PASS;
- deploy/public round-trip `35580937013`: PASS;
- loader core-r25 `35581115286`: PASS;
- live Businesses verifier `35581126441`: PASS;
- `business_catalog_read_only=PASS`;
- `business_catalog_search_filters=PASS`;
- `business_catalog_owned_missing_capacity=PASS`;
- `business_catalog_recipe_routes=PASS`;
- `business_existing_rearrangement_preserved=PASS`;
- public E2E `35581138549`: PASS.

Current status:
**CATALOG_R1_LIVE_CANDIDATE_USER_UI_CHECK_PENDING**

User live gate:
1. reload game/HK;
2. open **Бизнес → Бизнесы → Каталог**;
3. confirm the catalog layout is readable;
4. test search and bonus filter;
5. select one business card;
6. verify target quantity, owned/missing, capacity and known recipe route display;
7. no state-changing catalog action should be present.



## Businesses rearrangement desktop + T1–T3 guard r1 — userscript 1.17.24 (2026-09-21)

User live feedback on the existing rearrangement screen required two focused corrections without replacing the current working module or inventing a new flow:

1. desktop must show the existing **remove / Достать** side on the left and **insert / Вставить** side on the right;
2. currently installed **T4, T5 and T6 must never be user-removable**.

The pinned Kokkaras donor remains the source of truth. This is a focused compatibility/safety patch on the current rearrangement layer; the donor catalog/planner r1 stays read-only.

Delivered:
- marker: `businesses-rearrange-desktop-safe-t123-20260921-r1`;
- userscript: `1.17.24`;
- core: `core-20260921-r26-businesses-rearrange-guard`;
- desktop remove controls/list = left column;
- desktop insert controls/list = right column;
- mobile remains stacked;
- manual remove selector exposes only T1–T3 plus empty slots;
- optimizer removal tiers expose only T1–T3;
- stale presets selecting T4–T6 are sanitized;
- original-layout restore is blocked if it would remove a currently installed T4–T6;
- final plan has a runtime guard, so stale/in-memory plans cannot remove T4–T6;
- transaction rollback remains available only as a safety path for reverting a business inserted by the same failed rearrangement run.

Preserved:
- catalog r1 read-only contract;
- manual rearrangement semantics apart from the explicit T4–T6 protection;
- optimizer insertion tiers;
- bonus analyzer;
- manager/free-speed-up handling;
- authoritative postconditions;
- rollback safety;
- Buildings 2.06 LIVE PASS;
- Explore 2.07 LIVE PASS;
- Maps safe5.

Verification:
- deploy/public round-trip run `35590711750`: PASS;
- live Businesses verifier run `35590863403`: PASS;
- loader core-r26 retry run `35590914106`: PASS;
- public E2E run `35590987942`: PASS;
- `desktop_remove_left_insert_right=PASS`;
- `manual_remove_t4_t6=BLOCKED`;
- `optimizer_remove_t4_t6=BLOCKED`;
- `preset_stale_remove_t4_t6=SANITIZED`;
- `restore_remove_t4_t6=BLOCKED`;
- `plan_runtime_guard=PASS`.

Current Stage 2.08 gate:
**CATALOG_R1_LIVE_CANDIDATE_USER_UI_CHECK_PENDING · REARRANGE_UI_GUARD_R1_LIVE_CANDIDATE_USER_VISUAL_CHECK_PENDING**

Do not enable catalog-driven mutations until the read-only catalog/planner live UI is confirmed.


## Businesses runner visual canon r1 — hotfix (2026-09-21)

User screenshot showed the shared Runner falling back to the generic full-width action layout during **Перестановка бизнесов**.

Hotfix on userscript `1.17.24`:
- core: `core-20260921-r27-businesses-runner-canon`;
- marker: `businesses-runner-canon-20260921-r1`;
- Businesses rearrangement Runner now uses the same established compact visual canon as Buildings;
- title/status/progress keep the shared Runner semantics;
- desktop Pause/Stop actions are compact and right-aligned instead of stretching across the panel;
- mobile keeps the canonical two-action responsive layout;
- business logic, T4–T6 protection, catalog and optimizer are unchanged.

Verification:
- deploy/public round-trip `35596167960`: PASS;
- loader core-r27 `35596327521`: PASS;
- Businesses current-live `35596331997`: PASS;
- public E2E `35596336047`: PASS.

Stage 2.08 remains open for the user's next UI comments.
