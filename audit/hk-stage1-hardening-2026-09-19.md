# HK Stage 1 hardening audit — 2026-09-19

Baseline: verified live 1.14.4 from Stage 0 audit.

## Currency and source invariants

### Hamsters
- Budget currency: `cur_cap` (Caps / Крышки).
- Hamster level/rarity code must reject any cost containing `item_pit_token`.
- The spend limit and displayed balance must come from the current live player state, not a cached tab value.
- After a level/rarity mutation, progress is accepted only after the live hamster entity actually advances.
- Priority-copy purchases are accepted only after the copy count actually advances; spend is measured from live Caps before/after.
- Current shop lot/cost is sourced from the current shop state; stale/premium/hard-currency lots are not accepted.

### Generals
- Budget currency: `item_pit_token` (Pit Tokens / Жетоны Ямы).
- General upgrades must reject costs in `cur_cap`.
- Level cost is read from the server level-view response.
- General progress is accepted only after the live general entity actually advances.
- x1 / nearest x10 execution uses the server-provided action mode.

## Verified anti-stale protections inherited from 1.14.4
- `hkStateStore` exists and merges entity rows.
- Full `/player/me` arrays replace authoritative arrays.
- Older responses are timestamp-guarded.
- Growth force-rereads state before mutation groups.
- `HKNetworkTimeout` exists.
- `GROWTH_NO_PROGRESS_LIMIT` exists.
- Growth recovers live entities after ambiguous/no-progress mutation results.
- `apiJson` owns transient authorization/network/lock retries.

## Root cause of broken 1.15.0 Stage 1 attempt
The first mutation-gate patch renamed the original `apiJson` implementation to `apiJsonCore` and wrapped public mutation calls in a FIFO gate. Internal retry/recovery calls inside the original function still called public `apiJson`.

For a mutation:
1. outer `apiJson` acquired the mutation gate;
2. `apiJsonCore` hit an auth/network/player-lock retry;
3. the retry called public `apiJson`;
4. the retry queued behind the still-active outer mutation;
5. the outer mutation waited for the retry.

That is a self-deadlock.

## Hardening applied
Key commits:
- `c04c143e105229d76854cf05fbb7918a12ef42a5` — keep internal retries inside `apiJsonCore`; add build-time currency/progress/timeout invariants.
- `9600a915a17ca56fc9ac497d17d34e3d34a2ebf2` — make diagnostics non-fatal and remove cross-module pause coupling from the serialization gate.
- `19168b9545a7b403c65818619b9d6afeb6164c5e` — serialize Stage 1 deployments with GitHub Actions concurrency.
- `7f8991e651ee2c0fa65956f9ee28d35dbe8e1286` — add mutation-gate deadlock/FIFO/diagnostic regression test.
- `fbad45fdcdad0a08146c9575f1fafc5d4cb9a5ea` + follow-up fixes — make the patch repair either verified 1.14.4 or an existing Stage 1 1.15.0.
- `ea3f23e5ba1affa12e09f8915d53c0a8fba9a6f8` — rebuild the deployment workflow cleanly after detecting a malformed intermediate edit.
- `cb4ece899cd0db0c9179d5a15e3e0cb441e6f6bf` — add synthetic 1.14.4→1.15→1.15 fixture/idempotency regression test.
- `830bf19fe349fac61b33eda883f81efa0efddc53` — normalize gate block boundaries for byte-stable idempotency.

Current Stage 1 revision marker: `stage1-20260919-r4`.

Current Stage 1 patch now:
- refuses to build unless its base is verified 1.14.4;
- refuses to build unless Hamsters use `cur_cap`;
- refuses to build unless Generals use `item_pit_token`;
- refuses to build if strict currency-only cost guards disappear;
- refuses to build if network timeout or Growth no-progress protection disappears;
- routes internal api retries to `apiJsonCore`, never back through the gate;
- serializes state-changing requests FIFO;
- does not let a paused Growth/Today runner freeze unrelated modules;
- does not let diagnostic logging failure strand the FIFO queue;
- leaves read-only API requests outside the mutation queue;
- can repair an already-installed older 1.15.0 gate in place;
- runs a deadlock/FIFO regression test before patching;
- the deployment workflow also runs a synthetic patch idempotency test;
- GitHub Actions deployment uses a single concurrency group with `cancel-in-progress: true` so an older Stage 1 run cannot intentionally remain active beside the latest run.

## Verification status
Repository-side hardening and regression coverage are in place. The connector used for this audit does not expose usable GitHub Actions run status for these commits, so do not claim the current live server is verified 1.15.0 until a live export / workflow result confirms revision `stage1-20260919-r4`. The verified pre-Stage-1 baseline remains live audit 1.14.4.

## Stage 1 is NOT complete yet
Do not mark the global runner migration complete until these are implemented and verified:
1. Per-task AbortController / queued-task cancellation for Stop.
2. Automatic successful-mutation merge into `hkStateStore` for legacy modules, not only Growth-aware paths.
3. Authoritative reread policy after mutation groups.
4. Migration of Pit local flags.
5. Migration of Fair local flags.
6. Migration of Shop local flags.
7. Migration of Recipes / Bureau local flags.
8. Migration of remaining mutation loops.
9. Regression test proving a retry during a queued mutation cannot deadlock.
10. Live-server verification after deployment: version, syntax, currency invariants, service health and a real read-only check.

Until those items are verified, 1.14.4 remains the known-good baseline.
