# HK Stage 1C — Automation / mutation / hidden helpers audit

status: PASS_WITH_STAGE7_REFERENCE

## Scope

This block audits:
- automation entrypoints;
- mutation serialization;
- pause/stop/abort helpers;
- stale-state/live-refresh helpers;
- budget/expense guards;
- hidden helper coverage.

It does **not** perform the full mutation-safety proof. That belongs to Stage 7 by roadmap.

## SOURCE PREFLIGHT

Pinned donor:
- Kokkaras HK Control Panel
- version: `5.3.22-ui-icons-pit-dim`
- sha256: `28c3104020ecb7f54d0d51a72d067404d0176bc069d59fcca417d66817d1fcf1`

Relevant donor behavior confirmed:
- unified run state with `prepareRun`, `beginRun`, `pauseRun`, `continueRun`, hard stop and active `AbortController`;
- busy/double-run protection;
- business auto routines 1/2/3;
- scheduled Business Routine 3 around Athens reset;
- stored auto-routine options;
- explicit close/reopen routing to the currently running settings page.

## Historical migration audit

The historical migration audit still reports:
- genuinely missing real historical features: **0**;
- parser-only missing functions: 11, all already classified as superseded/equivalent except the intentionally excluded obsolete `growthNutCost`;
- no missing historical constants.

The Stage 1 mutation patch also explicitly introduced/preserved:
- `HK_MUTATION_GATE_REV = stage1-20260919-r4`;
- mutation serialization;
- safe non-fatal diagnostics;
- no recursive public `apiJson` retry inside `apiJsonCore`;
- strict Growth currency guards;
- no-progress protection;
- live reread helper;
- game UI refresh bridge.

## Current mutation layer

Current implementation contains:

### 1. Mutation classifier

`hkIsMutationRequest(path, method)`
- GET / HEAD / OPTIONS are never classified as mutations;
- known read-only POST routes are excluded through `HK_READ_ONLY_POST_PATHS`;
- remaining state-changing requests are routed through the mutation gate.

### 2. Serialized mutation gate

`hkMutationGate`
- one queued mutation turn at a time;
- tracks pending / completed / failed / active path;
- records mutation start / finish / error diagnostics;
- always releases the queue in `finally`;
- runtime exposure is registered only after initialization:
  `HK_MUTATION_GATE_ORDER_REV = mutation-gate-order-20260920-r1`.

### 3. Retry separation

Public `apiJson` sends mutations through:

`hkMutationGate.run(path, () => apiJsonCore(..., retryNetwork = 0))`

This is important: generic network retry is disabled for the mutation turn. Read-only requests may retain network retry behavior.

Full per-operation retry correctness is deferred to Stage 7.

### 4. Shared live state / refresh helpers

Present:
- `hkAuthoritativePlayerRead`;
- `refreshModuleLive`;
- `moduleMutationBusy`;
- shared state store;
- `hkGameBridge.noteMutation`;
- bridge flush after runner completion;
- deferred live reads while mutation modules are busy.

### 5. Runner controls

Current has:
- pause;
- resume;
- stop;
- runner signal / abort checks;
- `growthAbortCheck`;
- `growthCheckpoint`;
- module busy flags;
- no-progress guard for Growth.

### 6. Budget / spending guards

Present:
- `budgetDecision`;
- reserve checks;
- day/week limits;
- per-section allow/deny;
- premium-currency protection;
- current-balance affordability;
- `appendExpense` journal;
- strict Growth currency enforcement:
  - Hamsters: Cola Caps only;
  - Generals: Pit Tokens only.

## Auto routines — important donor/current difference

Pinned Kokkaras donor has **three dedicated Business Auto Routines**:
- `runBusinessAutoRoutine1`;
- `runBusinessAutoRoutine2`;
- `runBusinessAutoRoutine3`.

It also has:
- `BUSINESS_AUTO_ROUTINES`;
- scheduled Routine 3;
- reset countdown / reset safety;
- persisted routine settings;
- automatic launch around the configured reset window.

Current HK does **not** contain those donor identifiers:
- `runBusinessAutoRoutine1`: 0 occurrences;
- `runBusinessAutoRoutine2`: 0 occurrences;
- `runBusinessAutoRoutine3`: 0 occurrences;
- `BUSINESS_AUTO_ROUTINES`: 0 occurrences;
- `businessAutoRoutineArmed`: 0 occurrences.

Current HK instead contains the separate module-chain implementation:
- `renderAutoRoutines`;
- `runAutoRoutine`;
- `stopAutoRoutine`;
- marker `auto-routines-20260920-r1`.

That current module sequentially runs already-configured modules and deliberately preserves each module's own confirmations and budget guards.

### Classification

The two implementations are **not equivalent feature-for-feature**.

This is **not silently marked as transferred**.

Classification:
- current generic Auto Routines: PRESENT;
- Kokkaras Business Auto Routines 1/2/3: DONOR REFERENCE / NOT PRESENT VERBATIM;
- full decision whether to reproduce/merge donor Business Auto Routines belongs to **Stage 7 — Automations and mutation safety**, because Stage 7 explicitly owns Auto Routines, Businesses, mutation paths, confirm/pause/stop/retry/double-run protection and state refresh.

Stage 1C therefore records this as a **deferred donor-reference difference**, not as a historical migration regression.

## Hidden-helper result

No new missing historical helper was found beyond the already resolved parser list.

Current equivalents cover the important helper classes:
- mutation classification;
- serialized execution;
- state merge / authoritative reread;
- live module refresh;
- diagnostics;
- runner pause/stop;
- abort checks;
- budget decisions;
- expense tracking;
- game UI refresh bridge.

## Stage 1C conclusion

- historical migration helper coverage: **PASS**
- current mutation serialization: **PRESENT**
- current pause/stop/abort helpers: **PRESENT**
- current budget/live-refresh helpers: **PRESENT**
- genuinely missing historical helpers found in this block: **0**
- donor Business Auto Routines 1/2/3: **NOT EQUIVALENT TO CURRENT GENERIC AUTO ROUTINES; DEFERRED TO STAGE 7**
- gameplay code changed in this block: **0**

**Stage 1C: PASS_WITH_STAGE7_REFERENCE**

Next block: **1D — navigation and real live paths audit**.
