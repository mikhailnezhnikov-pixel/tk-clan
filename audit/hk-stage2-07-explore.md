# HK Stage 2.07 — Explore / Исследование

## E1 — canonical donor audit

Status: **AUDIT PASS / NO LIVE CHANGES**

This file is the Explore-local checkpoint while Maps ↔ Website work is running in parallel.
Do not treat the current district/map research UI as Explore parity.

## Source preflight

Pinned donor:
- title: `скрипт Kokkaras,.txt`
- version: `5.3.22-ui-icons-pit-dim`
- raw upload SHA256: `8a5aece8b10dfbaf0b3dd2890de600a9505aa523783cbe0c97ea81331d7e0c7d`
- CRLF→LF canonical SHA256: `28c3104020ecb7f54d0d51a72d067404d0176bc069d59fcca417d66817d1fcf1`
- canonical size: 1,836,359 bytes
- identity anchors verified: `showExploreBuildingsMenu`, `runExploreBuildings`

Current bug ticket:
`audit/hk-stage2-bug-explore-canonical-transfer-gap.md`

## Current baseline behavior

Current `Explore / Исследование` is not donor Explore Buildings.

Current functions:
- `exploreOwnedAreas()`
- `exploreMappedIds()`
- `renderExplore()`
- `refreshExplore()`

Current action:
`submitOwnedMapAreas(true)`

Current semantics:
`/cities → /game_area/* → /game_area/*/buildings → shared Maps database`

That belongs to Maps/district research and must not be considered Explore parity.

## Donor Explore semantics

Donor module:
- `showExploreBuildingsMenu()`
- `runExploreBuildings(settings, preparedState)`

Purpose:
process already-owned/open player buildings through building event completion, battles and tier/remort progression.

### Donor defaults

```
maxBuildings: 500
startTiers: [0,1,2]
targetTier: 3
districtId: all
buildingType: all
battleLevel: min
level: min
nextTierLevel: max
totalEvents: any
actionDelay: 1000–3000 ms
battleDelay: 1000 ms
betweenBuildingsDelay: 2000–7000 ms
buyMissingMaterials: false
exploreTargetTier: false
exploreTargetBattles: false
```

Allowed maximum buildings: 1..5000.

Tier mapping:
- 0 = Tier 1
- 1 = Tier 2
- 2 = Tier 3
- 3 = Tier 4
- 4 = Tier 4+
- 5 = Tier 5
- 6 = Tier 5+
- 7 = MAX
- target value 8 = Instant MAX path

### Filters

Donor filters by:
- district
- building type: all / normal / investment
- selected starting tiers
- target tier
- target-tier exploration toggle
- target-tier battles toggle

District/building-type metadata is obtained from donor `buildings_api.php` with:
`{mode:'explore_metadata'}`.

For our implementation this donor server is not to be copied as a dependency.
Equivalent metadata should come from our existing owned-area/building mapping/shared map knowledge where exact.

### Priority order

Base candidate sorting is stable and uses:
1. next-tier level
2. building level
3. battle level

When `totalEvents != any`, donor enriches with total event count and sorts:
1. next-tier level
2. building level
3. total events
4. battle level

Each priority supports:
- min
- max
- any

### Target-tier scan optimization

When `exploreTargetTier` is enabled, donor does not blindly reprocess every building already at target tier.

It:
- keeps a per-player Explore progress cache;
- reads target-tier building details only when necessary;
- calculates total/completed/remaining events;
- skips already-finished target-tier buildings unless target-tier battles are still required;
- uses a 100 ms scan pacing delay.

This behavior is part of canonical parity and should not be removed.

## Capability rules

### Fast completion by player level

Donor level rules:

| Player level | Tier | Mode |
|---:|---:|---|
| 5,000 | 0 | auto |
| 30,000 | 1 | auto |
| 100,000 | 0 | fast |
| 100,000 | 2 | auto |
| 250,000 | 1 | fast |
| 250,000 | 3 | auto |
| 400,000 | 2 | fast |
| 400,000 | 4 | auto |
| 750,000 | 3 | fast |
| 750,000 | 5 | auto |
| 1,000,000 | 4 | fast |
| 1,000,000 | 6 | auto |
| 1,500,000 | 5 | fast |
| 2,000,000 | 6 | fast |

`fast` is required for event fast-completion on an unfinished building tier.

### Automatic battles from Remort Consigliere

Donor detects:
- `hamsteress_remort`
- preferably line `hamsteress_remort_line_01`
- status must be `ACTIVE`

Automatic battle maximum tier:
- level 0 → T1
- level 1–9 → T2
- level 10–19 → T3
- level 20–29 → T4
- level 30–39 → T4+
- level 40–49 → T5
- level 50+ → T5+

If automatic battle is unavailable/fails, donor can fall back to manual battles.

### Manual battle faction counters

Valid factions:
`blue, green, orange, violet, khaki, turquoise, red, brown`

Donor chooses the strongest owned faction among counters for the enemy faction.

Manual battle loop:
- repeats until `battle_level >= max_battle_level`;
- records win only when level actually advances;
- stops a building after 5 consecutive non-advancing battle responses.

## Exact donor endpoints

Read/detail:
- `POST /player/building?building_id=...`

Fast completion:
- `POST /player/building/fast_completion/cost` body `{building_id}`
- `POST /player/building/fast_completion` body `{building_id}`

Battles:
- `POST /player/battle/fast` body `{building_id}`
- `POST /player/battle?building_id=...&faction_id=...`

Tier/remort:
- `POST /player/building/remort?building_id=...`
- `POST /player/building/fast_remort/cost` body `{building_id}`
- `POST /player/building/fast_remort` body `{building_id}`

Optional renovation-material purchase:
- `GET /shop/view`
- `POST /shop/buy`

Static data needed:
- items
- currencies
- tiers
- localization

## Per-building canonical execution

For normal target tiers (1..7):

1. load full building if needed;
2. if already past target, or at target and target-tier exploration is disabled → complete;
3. if current events are unfinished:
   - verify player-level `fast` capability;
   - read fast-completion cost;
   - reject if required constructions are present;
   - verify currencies/items;
   - call fast completion;
   - update local resource state;
4. if at target and target-tier battles disabled → complete;
5. if battles remain:
   - use auto battle when Consigliere tier permits;
   - otherwise/fallback use manual battle with faction counter;
6. when events and battles are complete:
   - if at target → complete;
   - otherwise prepare remort costs/materials;
   - optionally buy missing beams/nails;
   - call remort;
   - verify tier increased;
7. repeat until target reached.

Safety guard in donor:
maximum 100 internal iterations for one building.

### Instant MAX target (targetTier = 8)

Separate path:
1. if already tier 7/MAX → complete;
2. read `fast_remort/cost`;
3. reject if required constructions exist;
4. optionally buy missing renovation materials;
5. verify complete cost affordability;
6. call `fast_remort`;
7. verify resulting tier >= 7.

## Renovation materials

Donor only auto-buys:
`item_beams_t1..t5`
`item_nails_t1..t5`

Tier material mapping:
`0→1, 1→2, 2→3, 3→4, 4→4, 5→5, 6→5`

Material shop logic:
- load `/shop/view` once per run;
- find lots whose single reward is required beam/nail;
- sort lots by reward quantity ascending;
- use the smallest matching lot repeatedly until required quantity is reached;
- verify lot affordability before every purchase;
- stop with resource-exhausted status when purchase cost cannot be afforded.

## Resource/state behavior

Donor initializes run-local owned maps from `/player/me`:
- currencies
- items
- player factions

Every action response updates those run-local balances from:
- known costs
- rewards
- returned currencies/items

A resource shortage stops further building processing rather than blindly continuing.

After a building action result, donor patches the in-memory player building summary fields:
- tier
- level
- next_tier_level
- battle_level
- max_battle_level
- has_events
- is_favorite

## Run-level behavior

Before run:
- fresh auth/player read;
- load static items/currencies/tiers;
- load localization;
- calculate Remort Consigliere capability;
- calculate player factions/resources;
- obtain exact district/building metadata if not already prepared;
- build candidate queue.

During run:
- pause checkpoints before each building/action loop;
- configured delays;
- process buildings sequentially;
- stop further buildings on resource exhaustion;
- continue past ordinary skipped/failed individual buildings.

Final counters:
- completed
- skipped
- failed
- fast completions
- instant maxes
- automatic battles
- manual battles
- remorts

## Integration requirements for our HK

Do not reuse the current `renderExplore()` district-scanner semantics.

Preserve existing shared infrastructure where it already provides equivalent behavior:
- `hkStateStore`
- `hkRunner`
- `apiJson`
- mutation gate
- AbortController/runner stop
- game retry/backoff
- current resource/static catalogs
- current building/map area mapping

Important mutation safety:
- `/player/building` detail reads must remain safe only for buildings already present in the player's owned/open building state;
- all actual Explore action endpoints must be treated as mutations;
- no blind automatic retry of an uncertain mutation result;
- authoritative state reread/reconciliation is required at safe boundaries.

## Short implementation blocks

### E1 — Audit / canonicalization
Status: **PASS**
- donor verified;
- current mismatch verified;
- endpoints/defaults/order/capabilities documented;
- no live changes.

### E2 — Explore UI + read-only plan
Implement only:
- donor-equivalent settings UI;
- fresh player state;
- district/type/tier filtering;
- capability display;
- candidate calculation/preview;
- target-tier read-only scan/cache;
- no event completion, battles, remort, fast remort or purchases.

PASS gate:
user can open Explore and confirm candidate selection/settings without spending anything.

### E3 — Single-building canonical action core
Implement donor action mechanics for exactly one selected/candidate building:
- fast completion;
- auto/manual battle;
- remort;
- Instant MAX;
- resource guards;
- optional material purchase;
- authoritative post-action reconciliation.

PASS gate:
one building reaches requested target correctly with pause/stop/error handling.

### E4 — Multi-building runner
Add:
- maxBuildings;
- canonical priority sorting;
- target-tier cache optimization;
- configured delays;
- run-local resource tracking;
- sequential multi-building loop;
- final counters.

PASS gate:
small 2–3 building run behaves correctly and rerun excludes/completes appropriately.

### E5 — Live PASS
Verify:
`UI → live read → calculation → action → state update → rerun`

Only after user confirmation mark Stage 2.07 Explore LIVE PASS.

## Parallel-work guard

Maps ↔ Website shared-knowledge work is running in another chat.

During Explore implementation:
- do not modify map backend/schema;
- do not change Maps scanner or map coordinate logic;
- do not refactor shared map APIs;
- rebase/re-read current baseline before every Explore deploy;
- patch Explore-specific code only.


## E2 — donor-equivalent UI + read-only plan

Status: **LIVE CANDIDATE / USER UI CHECK PENDING**

Marker:
`HK_EXPLORE_CANON_REV = 'explore-readonly-plan-20260920-r1'`

### Implemented

- replaced the incorrect district-map Explore UI with Explore Buildings planning;
- fresh authoritative player read for plan calculation;
- settings persistence;
- district filter;
- building type filter: all / normal / investment;
- starting tiers T1..MAX;
- target tiers T1..MAX + Instant MAX;
- target-tier exploration toggle;
- target-tier battle-completion toggle;
- max buildings 1..5000;
- donor priority controls:
  - battle level;
  - building level;
  - next-tier level;
  - total events;
- donor delay settings are visible/stored for E3/E4 but not executed;
- future missing beams/nails purchase toggle is visible/stored but inactive in E2;
- account capability display:
  - player level;
  - Remort Consigliere;
  - max automatic-battle tier;
  - per-tier manual/auto/fast capability;
- exact donor candidate eligibility rules;
- stable donor priority ordering;
- target-tier progress cache;
- target-tier read-only scan of already active buildings only;
- plan preview with first 20 selected candidates and total count;
- warnings for unmapped buildings, unknown investment type, and unavailable exact total-events values.

### Metadata source

Donor uses its own `buildings_api.php?mode=explore_metadata`.

Our E2 does not depend on donor infrastructure. Equivalent metadata is built read-only from:

- authoritative player state;
- persisted/current `building_id → area_id` mapping;
- `GET /cities`;
- `GET /game_area/{areaId}`;
- `GET /game_area/{areaId}/buildings`;
- `invest_building_list`;
- exact cached/full event data when available.

If exact `total_events` is unavailable for any candidate, E2 does not invent a value and does not apply the total-events priority.

### Safety

E2 Explore block contains **zero** mutation/action endpoints.

Explicitly absent from the new Explore block:

- `/player/building/fast_completion`;
- `/player/battle/fast`;
- `/player/building/remort`;
- `/player/building/fast_remort`;
- `/shop/buy`.

The only detailed building request in E2 is:

`POST /player/building?building_id=...`

and it is called only for rows that already come from the player's active/owned `buildings` state during the target-tier read-only scan.

The action button is deliberately disabled and states that Run becomes available in E3.

### Build verification

- source live SHA256: `1932f3984a330edf234c02e80c0f27e1b845b299f3bb09875d166397dcded9d6`;
- build candidate SHA256: `c32fc068e4bcf89748419ecaa207c6fe165660097c3c4b922abcf2a0b1d9bf9f`;
- JS syntax: PASS;
- Explore mutation endpoint scan: PASS (0);
- build evidence: `audit/hk-stage2-explore-e2-build-status.txt`.

### Live verification

- deploy: PASS;
- service: PASS;
- public byte equality: PASS;
- live/public SHA256:
  `c32fc068e4bcf89748419ecaa207c6fe165660097c3c4b922abcf2a0b1d9bf9f`;
- baseline sync: PASS;
- live evidence: `audit/hk-stage2-explore-e2-live-status.txt`.

### User check required

Reload game → HK → Исследование.

Check only:

1. district/type filters;
2. starting tiers;
3. target tier / Instant MAX;
4. target-tier toggles;
5. account capability summary;
6. priorities and limits;
7. click **Рассчитать план**;
8. inspect candidate list/count.

Do not expect or attempt building actions in E2.

### Next

After user UI/read-only confirmation:
**E3 — single-building canonical action core**.

Do not implement E3 automatically before E2 user confirmation.

## E2 r2 — donor alignment checkpoint

Status: **TECHNICAL PASS / LIVE CANDIDATE / USER UI CHECK PENDING**

Marker:
`HK_EXPLORE_CANON_REV = 'explore-readonly-plan-20260920-r2'`

Live/baseline sync commit:
`1842d260c9d061331a8702bd603d881dd45e8f45`

### Donor re-check

The pinned donor Explore was re-read before the r2 deploy. E2 was aligned to the donor-specific read-only selection behavior:

- target tier starts at donor value `1` (Tier 2); Tier 1 is not a target option;
- target values remain Tier 2..MAX plus Instant MAX (`1..8`);
- starting-tier controls are limited by the selected target;
- target-tier exploration/battle toggles are available only for target values `1..6`;
- target-tier cache now uses a building-state fingerprint:
  `tier | level | next_tier_level | max_battle_level | has_events`;
- stale cached completion data is ignored when the building summary changes;
- target-tier queue keeps the donor cache-aware ordering for `level=max`;
- in the ordinary non-target-tier path, `maxBuildings` is applied before optional total-events reordering, matching donor `runExploreBuildings`.

### Safety / scope

E2 remains read-only.

Explore r2 contains no calls to:

- `/player/building/fast_completion`;
- `/player/battle/fast`;
- `/player/building/remort`;
- `/player/building/fast_remort`;
- `/shop/buy`.

Detailed target-tier inspection remains limited to:
`POST /player/building?building_id=...`

The action button remains disabled. E3 action mechanics were not implemented.

No Maps backend/schema/scanner changes were made by the E2 r2 deploy.

### Race-safe live verification

Before install the deploy fetched the then-current live script and patched only the Explore block.
The live SHA was checked again immediately before installation, so a concurrent live change would have aborted the deploy.

Result:

- source live SHA256: `c32fc068e4bcf89748419ecaa207c6fe165660097c3c4b922abcf2a0b1d9bf9f`;
- deployed/public SHA256: `6a40137d505248ff5525bed0136b185b0b1c7273147fa0d283cb65397039563a`;
- service restart: PASS;
- JS syntax: PASS;
- public byte equality: PASS;
- Explore mutation endpoint scan: 0;
- target tier minimum: donor-compatible value `1`;
- target cache fingerprint: PASS;
- donor max-buildings queue order: PASS;
- run action: disabled.

Evidence:
`audit/hk-stage2-explore-e2-r2-live-status.txt`

The first r2 workflow registration attempt failed at workflow/YAML validation and therefore made no live change. The corrected workflow then completed successfully.

### E2 stop gate

Do not start E3 from this checkpoint.

User UI/read-only confirmation still required:

1. reload game → HK → Исследование;
2. confirm district and building-type filters;
3. confirm starting tiers disable correctly as target changes;
4. confirm target list begins at Tier 2 and includes MAX / Instant MAX;
5. confirm target-tier toggles;
6. confirm account capability summary and priorities;
7. click **Рассчитать план**;
8. inspect candidate count/order.

Only after that confirmation may E2 be promoted from technical/live-candidate status to final E2 PASS and E3 be considered.

## E2 r3 — compact UI checkpoint

Status: **LIVE CANDIDATE / USER VISUAL CHECK PENDING**

Marker:
`HK_EXPLORE_CANON_REV = 'explore-readonly-plan-20260920-r3-ui'`

Live/baseline sync commit:
`fe6a03a7c56c25a9a68c82ee2007ddb27656a828`

Reason:
user UI review of r2 found the Explore screen visually disorganized on desktop: controls were stretched across the full panel, large empty gaps appeared between labels and fields, starting tiers were split across distant columns, and target toggles collapsed into one dense line.

### UI-only changes

- account capabilities are shown as compact tier chips;
- building filters use a bounded 3-column field grid on desktop;
- starting tiers use a compact 4-column grid;
- target tier and target options are grouped together;
- target-tier toggles are separated into readable toggle cards;
- Priority and Future delays are side-by-side desktop cards;
- form controls fill their local cell instead of being pushed to the far right edge;
- responsive breakpoints collapse to one-column/mobile layouts;
- candidate/read-only summary remains full width.

All existing Explore element IDs and handlers were preserved.

### Scope guard

- Explore mechanics changed: **NO**;
- candidate calculation changed: **NO**;
- donor rules changed: **NO**;
- mutation endpoints added: **0**;
- Maps/backend/schema changed: **NO**;
- E3 started: **NO**.

### Live verification

- source live SHA256: `6a40137d505248ff5525bed0136b185b0b1c7273147fa0d283cb65397039563a`;
- deployed/public SHA256: `76833b35de3620f7b946fac3c02fca021cd48d332e58c51ce74a40616c199c14`;
- syntax: PASS;
- service/deploy: PASS;
- public byte equality: PASS;
- Explore mutation endpoint scan: 0.

Evidence:
`audit/hk-stage2-explore-e2-ui-r3-live-status.txt`

### Stop gate

E2 remains pending user visual/read-only confirmation.
Do not start E3 automatically.

## E2 r4 — functional native controls + layout fix

Status: **LIVE CANDIDATE / USER UI FUNCTION CHECK PENDING**

Marker:
`HK_EXPLORE_CANON_REV = 'explore-readonly-plan-20260920-r4-ui'`

Live/baseline sync commit:
`c2282e7ce8a9b13b11e3c0589d47f14e3184aa9d`

### Root cause fixed

The r3 UI rebound every `select` and `input` to a handler that saved settings and immediately called `renderExplore()`.
That destroyed and recreated the native control on every change. Depending on browser/input behavior this could appear as a selector or checkbox refusing to switch or reverting immediately.

r4 removes full Explore rerender from ordinary filter changes.

### r4 behavior

- district/type/priority/delay/max-building controls are plain native inputs;
- ordinary changes save in-place without recreating the DOM;
- target-tier and target-tier-explore controls update only their dependent disabled states;
- start-tier checkboxes are enabled/disabled in-place according to donor target rules;
- at least one allowed starting tier is kept selected;
- changing settings invalidates the current preview and shows a recalculation hint;
- full render happens only on explicit refresh / plan calculation / normal module refresh;
- visual layout is simplified into:
  - account capability summary;
  - one ordinary Building filters card;
  - Priority + Future delays as two balanced cards;
  - action row;
  - plan result.

### Scope guard

- Explore candidate/action mechanics changed: **NO**;
- donor calculation functions before `renderExplore()`: byte-equivalent apart from revision marker;
- mutation endpoints added: **0**;
- Maps/backend/schema changed: **NO**;
- E3 started: **NO**.

### Live verification

- source live SHA256: `76833b35de3620f7b946fac3c02fca021cd48d332e58c51ce74a40616c199c14`;
- deployed/public SHA256: `78f120fb0a3f83f66378a60dd950673de143d1d1f8dc4067bcdb8572483aa5f6`;
- syntax: PASS;
- service/deploy: PASS;
- public byte equality: PASS;
- Explore mutation endpoint scan: 0;
- full rerender on filter change: REMOVED.

Evidence:
`audit/hk-stage2-explore-e2-ui-r4-live-status.txt`

### Stop gate

User should now verify that normal selects and checkboxes actually switch and remain selected, then run **Рассчитать план**.
Do not start E3 automatically.

## E2 r5 — dynamic filter state

Status: **LIVE CANDIDATE / USER FILTER CHECK PENDING**

Marker:
`HK_EXPLORE_CANON_REV = 'explore-readonly-plan-20260920-r5-filters'`

Live/baseline sync commit:
`3842c8a7f9055dd92ae6f83c1f71c2aad441963d`

### User-reported issue

After r4, native controls switched correctly, but changing District / Building type did not update the visible tier counts or candidate expectation until an explicit Calculate Plan action. This made the filters appear non-functional.

### Donor parity re-check

Pinned donor behavior was re-checked:
- `renderExploreDynamicState()` recalculates filtered buildings immediately when district/building-type changes;
- visible tier building counts and completed-battle counts are updated from that filtered set;
- `filterExploreBuildings()` applies exact metadata fields `gamearea_id` and `building_type`.

### r5 behavior

- changing district/type/start tiers/target/priorities saves settings in-place;
- no full Explore rerender on native control change;
- tier `total / battles complete` counters update immediately from already-loaded state;
- a local preliminary candidate count updates immediately without extra target-tier detail requests;
- the exact read-only plan remains behind **Calculate plan**;
- if account state is not loaded, tier counters show `—` instead of pretending that `0/0` is authoritative;
- failed automatic Explore refresh is no longer cached as a successful module refresh.

### Safety / scope

- no E3 actions;
- Explore mutation endpoints: 0;
- Map scanner r6 safe5 preserved;
- map concurrency remains 5;
- Maps backend/schema unchanged.

### Live verification

- source live SHA256: `416e214c462285389e3e905de53c2011e6bfb217ffd6286cebefe8206d3ae318`;
- deployed/public SHA256: `df677e603e0a180e0e2e2b5ce27af268ab788ced12e4e6b2036d4c9b23c78115`;
- syntax: PASS;
- public byte equality: PASS;
- dynamic filter counts: PASS;
- failed auto-refresh cached as success: NO;
- map concurrency 5 preserved: PASS.

Evidence:
`audit/hk-stage2-explore-e2-filters-r5-live-status.txt`

## E2 r6 — fresh player state + exact donor type filters

Status: **LIVE CANDIDATE / USER CHECK PENDING**

Marker:
`HK_EXPLORE_CANON_REV = 'explore-readonly-plan-20260920-r6-fresh-meta'`

Live/baseline sync commit:
`e0dcdc547dcd50929a7882cb238d0da57f494f4f`

### Fixed from user report

1. Explore now owns a dedicated fresh account snapshot.
   - opening/refreshing Explore performs a fresh full `POST /player/me`;
   - plan calculation performs another fresh full `POST /player/me`;
   - Explore UI/filtering no longer trusts an arbitrary shared snapshot before this read completes;
   - before fresh state is available, capability values show `—` instead of false `0 / not found` data.

2. Building type filtering now follows donor metadata semantics.
   - exact explicit `building_type=normal|investment` is accepted when present;
   - otherwise exact total-event metadata is used:
     - `normal` = more than 20 events;
     - `investment` = up to 20 events;
   - the previous `invest_building_list` inference was removed from Explore;
   - unknown type stays unknown instead of being guessed;
   - `All` includes all buildings, while Normal/Investment require the exact resolved type.

3. UI type labels now expose the same donor meaning:
   - Ordinary (>20 events)
   - Investment (up to 20 events)

### Safety / scope

- E3 actions added: **NO**;
- Explore mutation endpoints: **0**;
- map scanner concurrency remains **5**;
- Maps backend/schema changed: **NO**;
- code outside the Explore block was byte-identical during the patch.

### Live verification

- source live SHA256: `df677e603e0a180e0e2e2b5ce27af268ab788ced12e4e6b2036d4c9b23c78115`;
- deployed/public SHA256: `2855b2bf6a4ad714838e8b89b7460ad22e99afcf39430b34edd37b527d52a5af`;
- syntax: PASS;
- service/deploy: PASS;
- public byte equality: PASS;
- fresh player state: PASS;
- donor type threshold filter: PASS;
- map concurrency 5 preserved: PASS.

Evidence:
`audit/hk-stage2-explore-e2-r6-fresh-meta-live-status.txt`

The first r6 workflow attempt failed before deployment because of a Python patch-file quoting error. No live change occurred in that failed attempt. The corrected retry completed successfully.

### Stop gate

User should reload Explore and verify:
- account level / Remort Consigliere / auto-battle capability are populated;
- All / Ordinary / Investment show different immediate counts where the account contains both types;
- Calculate Plan follows the selected type.

Do not start E3 automatically.

## E2 r7 — active-building area/type mapping fix

Status: **LIVE CANDIDATE / USER FILTER CHECK PENDING**

Marker:
`HK_EXPLORE_CANON_REV = 'explore-readonly-plan-20260920-r7-area-types'`

Live/baseline sync commit:
`e152c741852e57282d96111b7133bc6f6373a6d0`

### User report

With r6:
- All buildings returned the expected active-building population;
- Ordinary and Investment both returned zero.

This proved that the selector itself worked, but active buildings had no resolved type metadata.

### Root cause

Explore r6 read the fresh player state correctly, but its building→area lookup still depended on shared map helpers whose cache key can prefer the global state store. That prevented the Explore metadata loader from resolving areas for the fresh Explore snapshot.

Without area IDs, the district metadata could not provide exact investment membership, so type-specific filters saw every active building as unknown.

The r6 event-count fallback was also removed. Donor filtering uses explicit metadata `building_type`; event count is not a valid substitute for building type.

### r7 fix

- Explore now builds its own read-only building→area index using the saved `mapBuildingAreasByPlayer` entry for the **current Explore player ID**;
- direct area fields and already-known in-memory map mappings remain safe fallbacks;
- for each resolved district, Explore reads the exact district metadata already used by Maps;
- building type priority is now:
  1. explicit `building_type = normal|investment`;
  2. explicit boolean investment field;
  3. exact membership in district `invest_building_list`;
- no event-count heuristic remains;
- UI labels are again simply Ordinary / Investment.

This matches the donor contract: the donor filters by exact per-building `building_type`, not by candidate event count. fileciteturn183file0

### Safety / scope

- E3 actions added: **NO**;
- Explore mutation endpoints: **0**;
- Maps backend/schema changed: **NO**;
- map scanner concurrency remains **5**;
- patch outside the Explore block: byte-identical.

### Live verification

- source live SHA256: `2855b2bf6a4ad714838e8b89b7460ad22e99afcf39430b34edd37b527d52a5af`;
- deployed/public SHA256: `4b58e9866bdf77fc3a298b47743da6c7e80f5eb618fb5f25f07c1e648e2e7584`;
- syntax: PASS;
- service/deploy: PASS;
- public byte equality: PASS;
- exact/current-player area index: PASS;
- explicit/invest-list building type: PASS;
- event-count type heuristic: REMOVED;
- map concurrency 5 preserved: PASS.

Evidence:
`audit/hk-stage2-explore-e2-r7-area-types-live-status.txt`

### Stop gate

Reload Explore and verify that:
- All still shows the full active population;
- Ordinary and Investment now split that population into non-zero groups where both types are owned;
- tier counters update immediately when switching type;
- Calculate Plan respects the selected type.

Do not start E3 automatically.

## E2 — USER PASS / E3 r8 single-building live candidate

E2 status: **PASS**

User confirmed the read-only Explore flow far enough to proceed:
- fresh account capability state is populated;
- district/type filters produce a valid candidate set;
- plan calculation returns candidates;
- user requested an actual Run action.

The detailed per-building ID cards were explicitly rejected as unnecessary. The plan UI now shows only aggregate counts:
- buildings after filters;
- candidates;
- **buildings to process**.

No individual building IDs are displayed in the normal plan summary.

## E3 r8 — single-building canonical action core

Status: **LIVE CANDIDATE / USER SINGLE-BUILDING TEST PENDING**

Marker:
`HK_EXPLORE_CANON_REV = 'explore-e3-single-20260920-r8'`

Live/baseline sync commit:
`ffa72351299a076d7cabf5f1bdd88f823cb09611`

### UI

After **Рассчитать план** and when at least one candidate exists, Explore now enables:

`Запустить тест E3 · 1 здание`

This is deliberately limited to the first candidate only. E4 multi-building processing is not enabled yet.

Before mutation, the UI asks for explicit confirmation that exactly one test building will be processed.

### Canonical E3 mechanics

The one-building runner implements the donor action sequence:

- full building detail read;
- fast-completion cost check;
- fast completion when allowed by player level;
- target-tier behavior;
- automatic battles from active Remort Consigliere capability;
- manual-battle fallback with donor faction-counter selection;
- stop after 5 consecutive non-advancing manual battle responses;
- remort cost/resource guard;
- remort with tier-increase verification;
- Instant MAX via fast-remort cost/action;
- optional missing beams/nails purchase when the user enabled that toggle;
- maximum 100 internal building iterations.

Donor references:
- per-building/Instant MAX runner: fileciteturn211file0
- normal fast-completion flow: fileciteturn209file0
- remort flow: fileciteturn212file0
- manual-battle counter behavior: fileciteturn217file0

### Mutation safety

The two cost endpoints are explicitly classified as read-only POST requests:

- `/player/building/fast_completion/cost`
- `/player/building/fast_remort/cost`

Actual actions remain mutations behind the existing serialized mutation gate:

- `/player/building/fast_completion`
- `/player/battle/fast`
- `/player/battle?...faction_id=...`
- `/player/building/remort?...building_id=...`
- `/player/building/fast_remort`
- optional `/shop/buy`

Mutation requests use no blind network retry.

After every mutation attempt, E3 rereads authoritative player state and the exact building detail before deciding whether the action applied. An uncertain transport response therefore is not blindly repeated.

### Scope guard

- E4 multi-building queue: **NOT ENABLED**;
- E3 scope: **exactly one building**;
- map scanner concurrency: **5 preserved**;
- Maps backend/schema: **unchanged**.

### Live verification

- source live SHA256:
  `4b58e9866bdf77fc3a298b47743da6c7e80f5eb618fb5f25f07c1e648e2e7584`;
- deployed/public SHA256:
  `cd210c35e6579fb594439b81fd0a08dd8089a35b3598b9e245478b959f4f6a3a`;
- syntax: PASS;
- service/deploy: PASS;
- public byte equality: PASS;
- plan detail cards removed: PASS;
- Run button enabled after a non-empty plan: PASS;
- fast completion / battles / remort / Instant MAX core present: PASS;
- no-blind-retry mutation behavior: PASS;
- post-action authoritative reconciliation: PASS.

Evidence:
`audit/hk-stage2-explore-e3-r8-live-status.txt`

Several preliminary r8 workflow attempts failed during local patch/predeploy validation and therefore did not change live. The final race-safe deploy completed successfully.

### E3 stop gate

User test:

1. reload the game / HK panel;
2. open **Исследование**;
3. choose the intended filters/target;
4. click **Рассчитать план**;
5. verify only the aggregate building count is shown;
6. click **Запустить тест E3 · 1 здание**;
7. confirm the one-building prompt;
8. report the resulting runner/log and resulting building state.

Do not enable E4 multi-building processing until this one-building test passes.

## E3 r9 — staged Explore runner UI

Status: **LIVE CANDIDATE / USER VISUAL CHECK PENDING**

Marker:
`HK_EXPLORE_CANON_REV = 'explore-e3-single-20260920-r9-runner'`

Live/baseline sync commit:
`8b6149836104e1d6e07587f9ddde02e1d8d91235`

### User request

The E3 runner needed the same visual clarity as the Pit runner:
- visually highlighted execution panel;
- several persistent stage rows;
- obvious current step;
- obvious completed / pending / skipped / failed state;
- enough time after completion to inspect the result.

### r9 behavior

Explore E3 now renders a highlighted runner with five stage rows:

1. Building state read
2. Explore events
3. Battles
4. Tier progression / Instant MAX
5. Final verification

Stage statuses:
- `○` pending;
- `▶` running;
- `✓` completed;
- `—` skipped;
- `×` error.

The current row receives the active highlight, completed rows are green, skipped rows are muted/warn-colored, and failed rows are red.

The runner keeps the existing Pause / Stop controls.

For Explore E3 only, a successful completed runner remains visible for 15 seconds instead of the generic 1.8-second completion timeout, so the user can visually inspect what finished.

### Scope

- E3 action mechanics: unchanged;
- E4: not started;
- Maps scanner concurrency: 5 preserved;
- Maps backend/schema: unchanged.

### Live verification

- source live SHA256: `cd210c35e6579fb594439b81fd0a08dd8089a35b3598b9e245478b959f4f6a3a`;
- deployed/public SHA256: `d41ca53e345efb346be393283bee982ff3112234fea2394e4c4efe8e70cd741f`;
- syntax: PASS;
- service/deploy: PASS;
- public byte equality: PASS;
- Explore runner highlight: PASS;
- Explore staged rows: PASS;
- completed runner linger: 15s;
- map concurrency 5 preserved: PASS.

Evidence:
`audit/hk-stage2-explore-e3-runner-r9-live-status.txt`

### Next

Continue E3 single-building validation.
Do not enable E4 until the single-building action path passes user verification.

## E3 r9 — current userscript 1.17.19 revalidation (2026-09-21)

After Stage 2.06 Buildings reached LIVE PASS, Explore E3 was revalidated against the current production userscript.

Current production:
- userscript: `1.17.19`;
- core: `core-20260921-r21-buildings-native-sync`;
- Explore marker remains `explore-e3-single-20260920-r9-runner`.

Read-only verification run `35576298312`: **PASS**.

Verified:
- live = public = baseline;
- E3 scope remains exactly one building;
- mutations still route through the shared serialized mutation gate;
- mutation network retry remains disabled by the shared mutation path;
- authoritative player/building reconciliation remains after every mutation attempt;
- fast completion path present;
- auto/manual battle paths present;
- remort path present;
- Instant MAX path present;
- five staged runner rows present;
- completed E3 runner remains visible for 15 seconds;
- E4 remains absent/not enabled;
- Buildings native-sync, Maps safe5 and passive auth protections remain present.

Current status:
**E3_R9_SINGLE_BUILDING_LIVE_TEST_PENDING**

Next gate is the real one-building action test. Do not enable E4 before user PASS.

## E3 r9 — USER LIVE PASS / speed refinement requested (2026-09-21)

User confirmed the one-building E3 action path works correctly and the staged runner tracks execution as expected.

Therefore the functional E3 single-building gate is:
**LIVE PASS**

User requested only a modest speed increase. This is treated as a timing refinement, not a functional E3 rework.

Constraints for the refinement:
- do not remove authoritative rereads;
- do not change mutation serialization;
- do not enable network retry for mutations;
- do not change battle/remort/Instant MAX logic;
- do not enable E4 in the same change.

## E3 speed r1 — userscript 1.17.20 (2026-09-21)

User confirmed the E3 one-building flow and staged runner are functionally correct, then requested a modest speed increase.

Delivered:
- userscript `1.17.20`;
- core `core-20260921-r22-explore-speed-tune`;
- marker `explore-e3-speed-20260921-r1`;
- default action delay changed from **1.0–3.0 s** to **0.7–2.0 s**;
- default battle delay changed from **1.0 s** to **0.7 s**;
- between-building delay remains **2–7 s** and is irrelevant to the one-building E3 gate;
- legacy standard `1/3/1` settings migrate once to the new `0.7/2.0/0.7` profile;
- custom user delay values are preserved;
- UI label changed from “Future run delays” to “Execution delays”.

Safety unchanged:
- authoritative rereads remain;
- shared mutation gate remains;
- mutation network retry remains disabled;
- fast completion / battles / remort / Instant MAX logic unchanged;
- E4 remains absent;
- Buildings native sync, Maps safe5 and passive auth protections preserved.

Verification:
- predeploy `35576826016`: PASS;
- deploy/public round-trip `35576921480`: PASS;
- current E3 verification `35577054251`: PASS;
- loader core-r22 recheck `35577128071`: PASS;
- public E2E `35577067567`: PASS.

Functional E3 status remains:
**LIVE PASS**

Current refinement status:
**SPEED_R1_LIVE_USER_FEEL_CHECK_PENDING**

