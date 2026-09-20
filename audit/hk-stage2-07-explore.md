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
