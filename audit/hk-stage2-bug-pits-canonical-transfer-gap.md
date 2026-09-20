# HK Stage 2 bug — Pits canonical transfer gap

status: CONFIRMED_LIVE_BUG

## Module

Stage 2.02 — Pits / Ямы

## Source of truth

Pinned Kokkaras donor:
- version: `5.3.22-ui-icons-pit-dim`
- normalized SHA256: `28c3104020ecb7f54d0d51a72d067404d0176bc069d59fcca417d66817d1fcf1`

## Expected donor behavior

Kokkaras Pits is a unified live module for all three Pits:

- Pit 1 / Cartel: `pit`, `cur_pit_pass`
- Pit 2 / Boss: `boss_pit`, `cur_pit_2_pass`
- Pit 3 / Mobster: `pit_pve`, `cur_pit_3_pass`

Per-Pit state/config includes:
- independent enable toggle;
- live available passes;
- pass plan / batch plan;
- target level;
- maximum Restoration Paws per round;
- auto-finish;
- continuation of an already active Pit;
- optional sniper mode/payment;
- tournament reward target / daily base runs / reward strategy;
- live crystal and Pit Pass budgets.

Canonical execution:
`showPitsMenu → pitBuildMenuState → pitReadRunConfigs → runPits(configs)`

Runner uses direct game API mutation paths for each Pit and rereads/recalculates live state.

## Actual live 1.17.4

Verified directly from:
`/opt/hamsterking-license/HamsterKingMobile.user.js`

Workflow:
`HK Stage 2 Pits Live Structure Verify`

Run:
`35490479912`

Live SHA256:
`303f6813d6e001751b53b32d83c6098f307aeedcee6a3cf320887bc93a07a117`

Observed:

- `async function pitLoop()`: 1
- `await pitLoop()`: 1
- `async function executeDailyPit`: 1
- total `executeDailyPit(` occurrences: 1 — declaration only, therefore no current call site
- `function pitReadRunConfigs`: 0
- `async function runPits(configs)`: 0
- `function pitBuildMenuState`: 0
- canonical three-Pit definitions: 0

Current active Pits UI is the legacy single-Pit DOM runner with:
- Target round;
- Delay;
- Activation token limit;
- Restoration token limit;
- Allow tokens;
- Collect only;
- Start / Stop.

The runner inspects and clicks the currently open native Pit screen rather than building an authoritative three-Pit live plan.

## Regression consequence

After Stage 2.01 Today was corrected to remove Pits from Today, the old direct API helper `executeDailyPit()` became orphaned. The visible Pits tab still launches `pitLoop()`.

Therefore:
- the direct three-Pit canonical execution path is not reachable;
- settings are not independent per Pit;
- canonical pass-plan/target/restoration/autofinish behavior is absent from the active Pits UI;
- reward-target/sniper/live-budget logic is absent;
- module cannot be marked LIVE PASS.

## Classification

**CONFIRMED TRANSFER REGRESSION / CANONICAL MODULE NOT WIRED**

This is not a cosmetic difference.

## Fix rule

Preserve current HK visual language, but replace the legacy single-Pit control model with Kokkaras canonical Pits behavior:
- three Pit cards;
- donor ordering/calculations/guards;
- current HK shared state/mutation gate/runner;
- no blind mutation retries;
- live reread/recalculation after actions.

Do not advance to Bosses until this bug is fixed and Pits reaches LIVE PASS.
