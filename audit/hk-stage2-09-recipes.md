# HK Stage 2.09 — Recipes / Рецепты

## Status

**SOURCE_PREFLIGHT_PASS · STATIC_CURRENT_PASS · TECHNICAL_LIVE_PASS · USER_BROWSER_CHECK_PENDING**

## Current production baseline

- userscript: `1.17.30`
- current implementation: `baseline/topking/HamsterKingMobile.current.user.js`
- inherited safety:
  - `game-api-rate-guard-20260922-r1`;
  - public collector activity lease;
  - serialized mutation gate;
  - Runner Pause/Stop/Abort;
  - unified budget guard / expense journal.

## Pinned donor preflight

Pinned donor confirmed from `reference/topking/REFERENCE.json` and ChatGPT File Library:

- Kokkaras HK Control Panel;
- file: `скрипт Kokkaras,.txt`;
- donor version: `5.3.22-ui-icons-pit-dim`;
- pinned SHA256: `28c3104020ecb7f54d0d51a72d067404d0176bc069d59fcca417d66817d1fcf1`.

Relevant donor recipe/business-planner behavior read before current implementation:

- Project Bureau recipes are real recipe graph edges, not inferred names;
- donor builds `recipesByResult` from canonical recipe rows;
- `/business/values` supplies `recipe_costs` keyed by `business_count`;
- recipe route selection prefers real recipe edges and preserves component order;
- Event Fair is only allowed as a component source in the correct recipe context;
- current account worker/capacity state is treated separately from the recipe graph.

The current HK Recipes module has a different UI architecture and remains the transferred implementation under verification; donor mechanics are used as the primary semantic reference, not copied by identifier name.

## Current Recipes module

### 1. Business-plan catalog / reroll

Current path:

1. fresh `POST /player/me`;
2. locate the Project Bureau catalog fair from real `fair_slots`;
3. accept only `mf_craftlot_*` business-plan lots;
4. derive current result + ordered components;
5. verify reroll cost through `safeReroll(..., false)`;
6. verify unified budget before every reroll;
7. mutation: `POST /fair/reroll`;
8. mutation is serialized by `hkMutationGate` and generic network retry is forced to zero;
9. expense is journaled;
10. observed recipe is submitted to the shared recipe DB;
11. one authoritative player reread is performed at completion.

Static result: **PASS**.

### 2. Shared recipe database

- game mutation: **NO**;
- current observed plans can be submitted to HK backend;
- duplicate observed plans are not counted as new;
- community recipe list is read from HK backend;
- result business and ordered components are rendered separately.

Static result: **PASS**.

### 3. Project Bureau craft

Current path:

1. recipe metadata is loaded;
2. fresh `POST /player/me` inventory before craft;
3. fresh `GET /business/values` recipe costs;
4. unknown recipe cost fails closed;
5. selected inputs must exactly match the 2- or 3-business recipe size;
6. stock is validated for `selected quantity × attempts`;
7. projected unified budget is checked before confirmation;
8. per-attempt budget is rechecked;
9. mutation: `POST /player/business/recipe/craft` with explicit `retryNetwork=0`;
10. expense is journaled;
11. Runner Pause/Stop/Abort remains active;
12. authoritative player state is reconciled after completion.

Static result: **PASS**.

## Mutation classification

Expected/current:

- `POST /player/me` = read-only;
- `POST /fair/reroll` = mutation;
- `POST /player/business/recipe/craft` = mutation.

Because all mutations pass through `apiJson → hkMutationGate → apiJsonCore(... retryNetwork=0)`, neither recipe rerolls nor Project Bureau crafts receive blind generic retries.

## 429 / collector isolation

Inherited from 1.17.30:

- all HK Game API calls use the global request-rate guard;
- HTTP 429 is not retried;
- active Runner places the server collector under activity lease;
- Recipes and Project Bureau therefore do not compete with the public collector for the same game token while running.

## Non-critical observation

Project Bureau completion currently performs:

1. direct `POST /player/me`;
2. immediately afterward `hkAuthoritativePlayerRead('bureau-complete')`, which is another `POST /player/me`.

This is one redundant read per completed Bureau batch. It is **not changed in this Stage 2.09 preflight** because the module is currently working and Stage 2 fixes only confirmed regressions. If the user live run confirms the Bureau path, this can be reduced in the later state/API or mutation-safety stage without changing gameplay behavior.

## Technical live gate

Verification must confirm from exact live/public 1.17.30:

- syntax;
- public/live exact match;
- recipe safety marker present;
- reroll fresh-state + budget guard;
- reroll expense journal;
- Project Bureau fresh inventory/cost;
- unknown-cost fail closed;
- craft stock × attempts guard;
- craft mutation no-retry;
- Runner Pause/Stop;
- final authoritative reconciliation;
- Game API 429 guard preserved;
- collector activity lease preserved.

## User browser gate

After technical live PASS:

1. reload to `1.17.30`;
2. open **Рецепты**;
3. **Каталог**: press read and confirm current recipe/result + component list is readable;
4. set rerolls to `1`; confirm shown cost is correct; do not start yet unless desired;
5. **База рецептов**: load and confirm recipes render/group correctly;
6. **Проектное бюро**: press read, confirm 2/3 input options, costs, stock names and tiers;
7. if making one real craft, use only a combination the user intentionally wants to consume; confirm one completion and fresh post-state;
8. confirm Pause/Stop controls appear while a mutable recipe task is running.

No automatic destructive CI action is permitted for this gate.
