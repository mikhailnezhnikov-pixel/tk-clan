# HK Stage 2.10 — Auto Routines / Авто-рутины

## Status

**LIVE PASS**

## Source decision

Auto Routines is a custom generic HK orchestrator.

Stage 1 already decided:
- keep the current generic Auto Routines implementation;
- Kokkaras Business Auto Routines 1/2/3 are a different specialized reset/business automation;
- donor Auto Routines remain Stage 7 reference only.

Therefore Stage 2.10 verifies and hardens the current HK orchestrator rather than replacing it with Kokkaras.

## Baseline checked

- current live/baseline userscript: 1.17.33;
- Clan Shop DOM history capture 1.17.33: preserved;
- adaptive Game API cooldown: preserved;
- collector activity lease: preserved;
- Kokkaras Businesses canon: preserved.

## Confirmed orchestration bug

Legacy `runAutoRoutine()` did:

1. `await action.run()`;
2. wait while `hkRunner.running`;
3. increment `completed += 1`;
4. continue to the next module.

Several module runners catch their own failures internally and return after calling `hkRunner.fail(error)`.

Therefore the legacy routine could:
- count a failed stage as completed;
- continue after `Runner=error`;
- count cancelled confirmation as success;
- count a selected stage with no configured work as success;
- lose the distinction between done/error/reset/not-started.

**STATIC BUG: CONFIRMED**

## Collector lease gap

The collector lease follows hkRunner status.

Between Auto Routine stages:
- module finishes and Runner becomes done;
- activity bridge may release the collector lease;
- the next stage starts later.

This creates a short interval where the server collector can use the same game token during a multi-stage automation.

**STATIC BUG: CONFIRMED**

## 1.17.34 patch

Revision:
- `auto-routines-safe-orchestrator-20260922-r2`

### Fail-closed stage contract

A selected stage is successful only if:
- it starts a new Runner instance, identified by a changed `startedAt`;
- its final Runner status is exactly `done`.

The chain stops if:
- Runner ends in `error`;
- Runner was reset/stopped;
- user presses Stop;
- module confirmation is cancelled;
- selected module does not start because no work is configured;
- module preconditions block startup;
- Game API is still in cooldown.

### Collector lease continuity

Auto Routine takes an explicit collector lease hold for the whole sequence.

While the routine is active:
- `Runner=done` between stages does not release collector lease;
- 20-second lease heartbeat continues between stages;
- Stop/error retains lease until current stage unwinds;
- final cleanup releases lease once.

If collector lease is required but cannot be acquired, the routine does not begin game mutations.

### Scope

No gameplay logic is changed in:
- Today;
- Growth;
- Businesses;
- Fair;
- Shop;
- Recipes;
- Project Bureau.

Only the generic orchestrator and collector-lease ownership are changed.

## Required live invariants

- userscript 1.17.34;
- exact public/live/baseline match;
- `node --check`;
- `HK_AUTO_ROUTINES_SAFE_REV`;
- changed `startedAt` gate;
- `result.status !== 'done'` fail-closed gate;
- old blind completion rule removed;
- Auto Routine collector lease hold participates in activity state + heartbeat;
- Clan Shop DOM history capture 1.17.33 preserved;
- adaptive 429 guard preserved;
- no CI game mutation.

## Browser gate

After technical live PASS:

1. reload to 1.17.34;
2. open **Авто-рутины**;
3. select one configured stage and cancel its module confirmation:
   - expected: routine stops; stage is not counted complete;
4. run one configured stage to successful completion:
   - expected: stage is confirmed only after Runner=done;
5. press Stop during an active stage:
   - expected: current Runner stops and next stage never starts.

A destructive multi-stage browser run is not required for Stage 2.10.

## UI consolidation 1.17.35

- User feedback: standalone Auto Routines overlaps Today and appears as a list of empty checkboxes.
- Standalone navigation/page removed.
- Existing Auto Routines block moved under Today.
- Saved routine selections and fail-closed orchestration are preserved.
- Legacy saved navModule=routines migrates to daily.
- Technical live deployment: PASS; browser check remains pending.

## User live confirmation

- User confirmed the 1.17.35 Auto Routines placement inside Today is correct.
- Standalone Auto Routines navigation is no longer needed.
- Stage 2.10: **LIVE PASS**.
