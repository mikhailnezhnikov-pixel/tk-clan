# HK Stage 2.12 — Hamsters / Хомяки

## Status

**SOURCE_PREFLIGHT_PASS · DONOR_COST_PARITY_BUG_CONFIRMED · TECHNICAL_LIVE_PASS · STATIC_CI_PASS · USER_BROWSER_CHECK_PENDING**

## Pinned donor

Kokkaras HK Control Panel `5.3.22-ui-icons-pit-dim`, pinned in `reference/topking/REFERENCE.json`.

Verified donor Hamsters behavior:
- Hamster budget wallet: `cur_nut`;
- saved budget: `nutsPercent`;
- execution order: Copy Priority → Rarity → Levels;
- copy purchases use donor family/rarity lot mapping and the exact priority list;
- current-event Hamsters may be excluded by exact event discovery;
- level choice optimizes Power / Nut with optional Mobster Pit weight;
- effective max level is 150 + `add_bonus_max_level`;
- fast `max` / `fast10` is used only when the live preview fits effective max level and budget.

## Confirmed parity bug in live 1.17.39

The Nuts wallet fix is preserved, but the HK safety helper is stricter than the pinned donor:

`growthHamsterCostSafe` requires every positive Hamster cost component to be exactly `cur_nut`.

The donor instead:
- budgets by the Nut component;
- checks affordability of the complete cost;
- blocks unsafe premium/hard purchases where applicable;
- does not reject a valid action solely because a safe extra item/currency component exists.

Impact:
- valid copy / rarity / level actions with an additional safe component may be silently skipped;
- candidate ordering can therefore diverge from donor behavior.

## Candidate 1.17.40

Marker: `hamsters-kokkaras-cost-parity-20260923-r1`

Change is intentionally minimal:
- `growthHamsterCostSafe` now accepts any non-empty `growthSafeCost`;
- `cur_prem` and `cur_hard` remain blocked by `growthSafeCost`;
- Hamster budget accounting still counts only `cur_nut`;
- Hamster level optimization still requires a positive Nut component;
- Copy Priority → Rarity → Levels order is unchanged.

Candidate:
`deploy/topking/HamsterKingMobile.1.17.40.hamsters-cost-parity.candidate.user.js`

Built from exact live-synced baseline 1.17.39 and preserves:
- Treasure Map passive capture 1.17.39;
- Maps manual-only scan;
- Growth Nuts canon;
- Clan Shop numeric player_id;
- Auto Routines in Today;
- adaptive 429 guard;
- collector activity lease;
- Kokkaras Businesses canon.

## Safety / deployment state

- destructive game mutations from CI: **NONE**;
- gameplay requests from validation CI: **NONE**;
- production deploy: **PASS**;
- baseline must remain 1.17.39 until a race-safe 1.17.40 deploy succeeds;
- user browser/live gate: **PENDING**.

## Browser/live gate after deploy

1. Open **Хомяки**.
2. Verify Hamster budget is **Орехи / Nuts** and saved percentage is correct.
3. Verify Copy Priority and current-event exclusion UI.
4. Inspect the execution plan before starting.
5. Observe the first real run for candidate ordering, Nut budget accounting and state refresh.
6. Stop immediately if a premium/hard cost is ever proposed.


## Static CI

- workflow: `Check Userscript 1.17.40 Hamsters Cost Parity`;
- run: `35812191033`;
- result: **SUCCESS**;
- `node --check`: PASS;
- version/build marker: PASS;
- donor cost-parity marker: PASS;
- Treasure / Maps / Growth / Clan Shop / Auto Routines / 429 / collector lease / Businesses preserved markers: PASS;
- Maps manual-only invariant: PASS;
- gameplay/network mutation from CI: NONE.
