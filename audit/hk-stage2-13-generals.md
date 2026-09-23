# HK Stage 2.13 — Generals / Генералы

## Status

**SOURCE_PREFLIGHT_PASS · DONOR_COST_PARITY_BUG_CONFIRMED · CANDIDATE_1_17_44_READY · STATIC_CI_PENDING · LIVE_DEPLOY_PENDING**

## Pinned donor

Kokkaras HK Control Panel `5.3.22-ui-icons-pit-dim`.

Verified donor Generals behavior:
- budget wallet: `item_pit_token`;
- budget percent applies to Pit Tokens only;
- full action affordability is checked against all cost components;
- a valid General level-up requires both positive Nuts and positive Pit Tokens in the live cost;
- `x1` and `fast10` are supported;
- `fast10` is used only when affordable and inside Pit budget;
- efficiency: Power / Pit Tokens;
- Mobster Pit weighting applies to Idol/Crypto/Pit-general targets;
- state is refreshed after level-up when the mutation response is incomplete.

## Confirmed parity bug in live 1.17.43

HK currently uses:

`growthGeneralCostSafe = safe && only item_pit_token && pit > 0`

That rejects valid Kokkaras General upgrades whose full live cost contains **Nuts + Pit Tokens**.

The donor instead:
- budgets by Pit Tokens;
- requires a positive Nut component;
- requires a positive Pit Token component;
- checks affordability of the complete cost.

Impact:
- valid General candidates can be silently skipped;
- a Generals run can finish with no upgrades even when affordable donor-valid upgrades exist.

## Candidate 1.17.44

Marker: `generals-kokkaras-cost-parity-20260923-r1`

Change:
- safe full cost is allowed;
- premium/hard remains blocked by the shared safety layer;
- positive Nuts are required;
- positive Pit Tokens are required;
- Pit budget remains Pit-only;
- x1/fast10 and efficiency ordering are unchanged;
- Generals Runner uses the approved vertical layout;
- Runner exposes General count / level-data count / Pit Tokens / budget.

No gameplay mutation is executed by CI.

## Preserved

- Hamsters LIVE PASS 1.17.43;
- Hamsters auth-state r3;
- Treasure selective capture r2;
- Maps manual-only scan;
- Growth Nuts canon;
- Clan Shop numeric player_id;
- Auto Routines in Today;
- adaptive 429 guard;
- collector activity lease;
- Businesses Kokkaras canon and vertical Runner.

## User live gate after deploy

1. Open **Генералы**.
2. Verify Runner is vertical.
3. Verify diagnostic line shows Generals and Pit Tokens.
4. Run Generals.
5. Confirm actual level increases and Pit Token spending.
6. Confirm no premium/hard cost is proposed.
