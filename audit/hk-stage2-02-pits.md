# HK Stage 2.02 — Pits / Ямы

status: REWARD_EXECUTION_R13_LIVE_CANDIDATE_PENDING_USER_CHECK

## Required Stage 2 chain

UI → live read → calculation/plan → action → state update → rerun

## Scope

- Normal Pit
- Boss Pit
- Gang Pit
- free/paid move logic
- token usage limits
- collect-only mode
- battle/start/finish/respawn paths
- reread after mutation
- pause/stop safety

## Next action

Run SOURCE PREFLIGHT against pinned Kokkaras donor and compare donor Pit behavior with current/live 1.17.4.

Do not change gameplay logic before concrete mismatch is identified.


## SOURCE PREFLIGHT result

status: **BLOCKED_DONOR_SOURCE_NOT_FOUND**

Expected pinned donor from `reference/topking/REFERENCE.json`:
- title: `Вставленный текст.txt`
- donor: Kokkaras HK Control Panel
- version: `5.3.22-ui-icons-pit-dim`
- pinned SHA256: `28c3104020ecb7f54d0d51a72d067404d0176bc069d59fcca417d66817d1fcf1`
- expected source: `https://kokkaras.com/hk_maps/panel.js`

File Library searches performed for:
- exact version;
- exact donor name;
- exact SHA256;
- source URL;
- `showPitsMenu` / `runPits` and related Pit anchors.

Result:
- the exact pinned donor was not returned;
- unrelated/current HK files were returned instead;
- no substitute donor was used.

Protocol decision:
- do not compare/modify Pits from memory or a different script;
- do not start implementation until the exact pinned donor source is available again.

Current/live Pits code was **not changed** in this block.


## Donor restored

Exact donor re-uploaded and verified:
- raw upload: CRLF, 1,860,858 bytes, SHA256 `8a5aece8b10dfbaf0b3dd2890de600a9505aa523783cbe0c97ea81331d7e0c7d`
- normalized CRLF → LF: 1,836,359 bytes
- normalized SHA256: `28c3104020ecb7f54d0d51a72d067404d0176bc069d59fcca417d66817d1fcf1`
- version: `5.3.22-ui-icons-pit-dim`

The previous donor-source block is resolved.

Stage 2.02 source preflight resumes from this exact pinned donor.


## Confirmed live regression

Bug ticket:
`audit/hk-stage2-bug-pits-canonical-transfer-gap.md`

Direct live verification:
- workflow run: `35490479912`
- live SHA256: `303f6813d6e001751b53b32d83c6098f307aeedcee6a3cf320887bc93a07a117`
- legacy `pitLoop` active: YES
- canonical `runPits(configs)`: ABSENT
- canonical `pitBuildMenuState`: ABSENT
- canonical `pitReadRunConfigs`: ABSENT
- direct API `executeDailyPit`: orphaned declaration, no active call site

Result:
**BUG_CONFIRMED_FIX_PENDING**

Next block:
port/wire Kokkaras canonical three-Pit behavior into current HK visual/runner architecture.


## Canonical core r1 deployed

Marker:
`HK_PITS_CANON_REV = 'pits-canon-core-20260920-r1'`

Workflow:
`Deploy TopKing Pits Canon Core R1`

Successful run:
`35491426778`

Technical result:
- patch payload SHA verification: PASS
- Python compile: PASS
- exact pre-deploy live SHA verification: PASS
- JS syntax after patch: PASS
- backup/deploy: PASS
- service active: PASS
- public round-trip: PASS
- live/public byte equality: PASS
- version remains: `1.17.4`
- live/public SHA256: `0d6de4888121d5e09d2cd5fa5140ec5941734dd30c23dc70fbbd95a951dcb825`

Core behavior now wired into the visible Pits tab:
- three independent Pit cards: normal / boss / gang;
- live free-pass counts;
- donor Exact / Rounded / Direct / Pit Pass planning;
- target level selector;
- per-Pit maximum Restoration Paws;
- per-Pit Auto-finish plus global Auto-finish all;
- continuation of an already active Pit;
- direct API start/pass/battle/respawn/finish;
- current HK mutation gate and runner pause/stop;
- authoritative player reread before/after mutations;
- cost/balance revalidation before paid mutations;
- legacy single-Pit DOM UI/button bindings removed from active page.

Not yet in this core block:
- sniper mode/payment;
- tournament reward target planning / daily base runs / reward strategy;
- interactive restoration-decision modal.

These stay for the next Pits block after the core UI/live-read is visually confirmed.

Current status:
**CORE_LIVE_CANDIDATE_PENDING_USER_UI_CHECK**


## UI alignment r2

Marker:
`HK_PITS_UI_REV = 'pits-ui-align-20260920-r2'`

Workflow:
`Deploy TopKing Pits UI Align R2`

Successful run:
`35492472689`

Result:
- card controls aligned into a bounded grid;
- Restoration Paws checkbox/input alignment corrected;
- Core r1 gameplay/API logic unchanged;
- live/public SHA256 after r2: `a3df20e0996ced42e4efa39baa5f25b9e41af979657854079c8e645e57b16708`.

## Pass-plan + Sniper r3 deployed

Pinned donor used:
- uploaded `скрипт Kokkaras,.txt`;
- version: `5.3.22-ui-icons-pit-dim`;
- canonical CRLF→LF SHA256: `28c3104020ecb7f54d0d51a72d067404d0176bc069d59fcca417d66817d1fcf1`.
- donor file is not committed to the repository by user choice; future chat must use the same exact upload/SHA if donor code is needed again.

Confirmed donor behavior transferred in this block:
- Pit is active only when its state has `is_finish === false`;
- finished Pit snapshots no longer lock the Pass plan merely because an old `mass_multiplier` remains;
- normal Pass plan remains donor-compatible: Exact / Rounded / Direct / Pit Pass;
- Sniper mode is independent per Pit;
- standalone Sniper uses multiplier ×1;
- Sniper payment is selectable as FREE / PREM / ITEM when that payment is live-available;
- Sniper recommended target = `floor(currentLevel / 5) * 5 + 15`;
- Sniper target choices start at the recommended target and higher available target levels;
- active ×1 Pit can preserve Sniper flag, while active non-×1 Pit cannot enable Sniper;
- saved normal Pass plan/target remain separate from Sniper target/payment.

Marker:
`HK_PITS_SNIPER_REV = 'pits-passplan-sniper-20260920-r3'`

Workflow:
`Deploy TopKing Pits PassPlan Sniper R3`

Successful run:
`35493218772`

Technical result:
- exact pre-deploy r2 SHA verification: PASS;
- Python patch compile: PASS;
- donor-transfer anchors: PASS;
- JS syntax: PASS;
- backup/deploy: PASS;
- service active: PASS;
- public round-trip: PASS;
- live/public byte equality: PASS;
- live/public SHA256: `42d39c573c5bb8bf445f8166a72a6b0a16fde14295365a0ebea0ee43e71b6f64`.

Baseline sync:
- workflow: `Sync TopKing Current From Live`;
- run: `35493258548`;
- result: SUCCESS;
- `baseline/topking/HamsterKingMobile.current.user.js` contains the r3 marker.

Current status:
**PASSPLAN_SNIPER_LIVE_CANDIDATE_PENDING_USER_UI_CHECK**

Required user check:
1. reload the game;
2. open HK → Ямы;
3. do NOT start the Pits yet;
4. verify that completed/non-active Pits have a selectable Pass plan;
5. verify Sniper mode appears on each Pit;
6. enable Sniper on one non-active Pit and verify:
   - Pass plan becomes ×1;
   - Pass payment selector appears;
   - target list starts at the recommended Sniper level and allows higher targets.

Do not advance to tournament reward planning, restoration decision logic, or Bosses until this UI/live-read check is confirmed.


## Toolbar clean r4 + user UI confirmation

User confirmation:
- Pass plan: visually OK;
- Sniper mode/payment/target UI: visually OK;
- remaining requested UI change: remove redundant `Обновить данные` button.

r4 change:
- removed only the manual `Обновить данные` / `Refresh live data` button from Pits;
- removed its click handler;
- automatic live refresh on module open remains unchanged;
- no Pits calculation/action logic changed.

Marker:
`HK_PITS_TOOLBAR_REV = 'pits-toolbar-clean-20260920-r4'`

Workflow:
`Deploy TopKing Pits Toolbar Clean R4`

Successful run:
`35493415188`

Technical result:
- exact pre-deploy r3 SHA verification: PASS;
- Python patch compile: PASS;
- JS syntax: PASS;
- backup/deploy: PASS;
- service active: PASS;
- public round-trip: PASS;
- live/public byte equality: PASS;
- live/public SHA256: `003c3a2a47bc2dc97e1e073b14744a57463d936e1fdc20b02e6041b124842223`.

Baseline sync:
- run: `35493446456`;
- result: SUCCESS.

Current Stage 2.02 status:
**UI_LIVE_READ_PASS_ACTION_PENDING**

Passed:
- UI;
- live read;
- normal Pass plan selection;
- Sniper mode/payment/target configuration;
- r4 toolbar cleanup.

Still required before Pits LIVE PASS:
- action execution;
- authoritative state update after action;
- rerun from the resulting state;
- remaining planned donor Pits functionality if still in Stage 2.02 scope.

Do not advance to Bosses yet.


## Start action r5

User report:
- main Pits start action did not visibly start.

Root cause fixed:
- current implementation performed an authoritative /player/me reread and re-render before freezing the selected Pits configuration;
- pinned donor freezes run configs first, then starts execution and performs live validation;
- r5 now snapshots selected Pits/config synchronously on click, starts the runner immediately in Preparing state, then performs authoritative reread;
- existing per-step live cost/resource/state revalidation remains unchanged.

Marker:
`HK_PITS_START_REV = 'pits-start-config-snapshot-20260920-r5'`

Deploy:
- workflow: `Deploy TopKing Pits Start R5`;
- run: `35493622785` — SUCCESS;
- live/public SHA256: `c373370ba5c3cf9a24f19d7e3ae82e871c124357e2d940f954fe834520a44629`;
- public round-trip byte equality: PASS.

Baseline sync:
- run: `35493651043` — SUCCESS.

Current status:
**ACTION_RETEST_PENDING**

Next user check:
- reload game → HK → Ямы;
- select only the Pit/plan the user is willing to spend;
- press `Запустить выбранные Ямы`;
- expected immediate UI response: runner enters `Подготовка`;
- report the first visible runner/log result.

## Respawn cost r6

User retest result:
- Start button works;
- runner entered the Pits action path;
- battle execution reached the HP restoration branch;
- runtime stopped with: `pitCanonRespawnCost is not defined`.

Cause:
- r1/r5 action code referenced `pitCanonRespawnCost()`, but the helper itself had not been transferred.

Pinned donor behavior:
- read `state.respawn_costs`;
- choose the first non-premium option (`is_prem === false`);
- read `item_pit_health_ticket` quantity from that cost;
- if cost is absent/zero, fall back to the current Pit batch size.

r6:
- adds only `pitCanonRespawnCost(state,chunk)`;
- no UI, pass-plan, sniper, battle endpoint or spending logic changed.

Marker:
`HK_PITS_RESPAWN_REV = 'pits-respawn-cost-20260920-r6'`

Deploy:
- workflow: `Deploy TopKing Pits Respawn R6`;
- run: `35493832589` — SUCCESS;
- JS syntax: PASS;
- service active: PASS;
- public round-trip byte equality: PASS;
- live/public SHA256: `f8644b37332e2b8d9d763ef80ff00768f932fae31e88963bac51f8791946d895`.

Static action-path audit after r6:
- all Pit canonical helper/function calls in `pitCanonRunOne()` are defined;
- the only missing runtime helper found in r5 was `pitCanonRespawnCost`, now supplied by r6.

Current status:
**RESPAWN_RETEST_PENDING**

This user run already confirms:
- main Start button ACTION entry: PASS;
- configuration snapshot before async reread: PASS in live usage;
- battle path reached: PASS.

Still required:
- restoration branch completes;
- authoritative state update;
- action completion;
- rerun from resulting state.


## Saved power table r7

User request:
- keep `Сохранённая сила уровней` collapsed by default;
- allow manual expansion when needed.

Change:
- `pitPowerTableOpen` default changed from `true` to `false`;
- existing `<details>` expand/collapse behavior retained;
- power observations, forecasts, table contents and calculations unchanged.

Marker:
`HK_PITS_POWER_TABLE_REV = 'pits-power-table-collapsed-20260920-r7'`

Deploy:
- workflow: `Deploy TopKing Pits Power Table R7`;
- run: `35494081452` — SUCCESS;
- live/public SHA256: `06422b7f259c15c47259e2156ea4446b2286bba6e9f8db3769d16faf7763bc6a`;
- public round-trip byte equality: PASS.

Baseline sync:
- run: `35494109901` — SUCCESS.

No Pits action logic changed in r7.


## Highlighted runner history r9

User feedback:
- Pits runner was technically visible but easy to miss;
- user requested stronger visual emphasis and about 10 recent execution lines;
- persistent bottom journal must remain unchanged.

r9 behavior:
- Pits runner gets a dedicated amber accent while a Pit task is active;
- runner includes a compact per-run history area;
- stores and shows the last 10 Pits execution messages;
- history is cleared at the beginning of every new runner task;
- Pits messages are mirrored into runner history while still continuing to the existing persistent journal unchanged;
- other modules do not populate this Pits-specific history unless they explicitly use runner notes.

Marker:
`HK_PITS_RUNNER_HISTORY_REV = 'pits-runner-history-20260920-r9'`

Deploy:
- workflow: `Deploy TopKing Pits Runner History R9`;
- run: `35494398235` — SUCCESS;
- live/public SHA256: `bbc766dc775c7ce637302f1ecf1edfae28b835afeab8408c214abe47b4950fdd`;
- public round-trip byte equality: PASS.

Baseline sync:
- run: `35494440507` — SUCCESS.

No Pit calculation/API endpoint/spending logic changed in r9.


## Faster battle/respawn cycle r10

User feedback:
- Pit action works, but battle/respawn cadence feels slower than necessary.

Donor reference:
- Kokkaras uses explicit battle pacing: normal/boss 1000 ms, gang 2000 ms; sniper 200/400 ms.
- Current HK was slower in practice because it additionally forced a full authoritative `/player/me` reread after every battle and respawn.

r10 change:
- mutation responses remain merged into the shared authoritative state store;
- after battle/respawn HK first uses the state already returned/merged by that mutation;
- full `/player/me` is now fallback only when the mutation response does not expose Pit state;
- short anti-lock pacing remains:
  - normal/boss: 120 ms;
  - gang: 180 ms;
  - sniper normal/boss: 80 ms;
  - sniper gang: 120 ms;
- pre-start resource validation and post-finish authoritative rereads remain unchanged;
- player-state-lock retries in the mutation layer remain unchanged.

Marker:
`HK_PITS_SPEED_REV = 'pits-fast-cycle-20260920-r10'`

Deploy:
- workflow: `Deploy TopKing Pits Fast Cycle R10`;
- run: `35494689254` — SUCCESS;
- live/public SHA256: `973e1b1788b86caaefac7a26b66f0eb42bc497ed49a618c277ebf36df63e6e25`;
- public round-trip byte equality: PASS.

Baseline sync:
- run: `35494718699` — SUCCESS.

Current status remains:
**RESPAWN_RETEST_PENDING**

Next user check:
- compare battle → result → respawn cadence;
- confirm no `player state is locked` errors;
- continue action → state update → rerun verification.


## Action flow confirmation + restoration decision r11

User confirmation after r10:
- battle/respawn speed: OK;
- highlighted runner/history: OK;
- Pits execution continues normally;
- no new player-state-lock issue reported.

Therefore the previously pending action-path regression is considered resolved for the tested path:
- Start button/action entry: PASS;
- battle loop: PASS;
- respawn path: PASS;
- visible progress: PASS;
- fast mutation/state path: PASS in user test.

Remaining Stage 2.02 donor functionality is now handled as separate advanced blocks, starting with the restoration decision flow.

r11 donor behavior transferred:
- when the configured Restoration Paws limit is exhausted before target completion, do not silently stop;
- show current level, selected target, required Paws, available Paws and post-spend balance;
- actions:
  - spend Paws and continue;
  - finish current round and continue;
  - leave current Pit for manual collection and continue;
  - stop the whole Pits runner;
- optional remember-choice behavior for the current run;
- optional additional Paws budget from the decision point;
- remembered budget is consumed only by subsequent restoration decisions in the same run;
- Stop integrates with the existing HK runner abort path.

Pinned donor reference:
- exact uploaded Kokkaras source;
- restoration decision semantics verified against `askPitRestorationDecision()` + shared battle decision flow.

Marker:
`HK_PITS_DECISION_REV = 'pits-restoration-decision-20260920-r11'`

Deploy:
- workflow: `Deploy TopKing Pits Restoration Decision R11`;
- successful run: `35495418034`;
- Python patch compile: PASS;
- JS syntax: PASS;
- backup/deploy: PASS;
- service active: PASS;
- public round-trip byte equality: PASS;
- live/public SHA256: `d2667d1fec05456cdb7e7bba0f0da2854d3fccf6275cf5df991b44942d05e52c`.

Baseline sync:
- run: `35495453299` — SUCCESS.

Current status:
**RESTORATION_DECISION_LIVE_CANDIDATE_PENDING_USER_CHECK**

User check:
- set a deliberately low Restoration Paws limit for one Pit;
- let the Pit reach the next required restoration;
- expected: the decision modal appears instead of silent stop;
- verify one safe branch first (recommended: `Потратить Лапы и продолжить` with a small known amount).

Do not advance to tournament reward planning until this r11 decision path is visually/action confirmed.


## Tournament reward planner core r12

User requested to proceed to the next Pits block before separately confirming the r11 restoration modal.
Therefore r11 remains technically deployed but still has an outstanding user-path check.

Pinned donor basis:
- live reward data is loaded from each Pit view plus its leaderboard;
- reward tiers use leaderboard score rewards with min_score >= 500000;
- tournament activity is status ACTUAL;
- current score is read from your_lb_slot.score;
- Pit score per x1 is calculated from the selected exact Target level and the Pit score reward item;
- future daily reset count uses the donor 12:00 UTC reset boundary;
- Daily base runs applies only to future resets; today's selected Pass plan remains the base;
- strategies are donor terms/semantics: upfront / gradual / last_day;
- every full 100 Tribute Boxes is forecast as 2 Pit Passes.

r12 includes:
- per-Pit live tournament section;
- active/inactive tournament indicator and remaining time;
- current tournament points and current Tribute Boxes;
- Reward target selector from live reward tiers;
- Daily base runs input;
- Extra Pit Pass strategy selector: Upfront / Gradual / Last day;
- read-only forecast:
  - points per x1;
  - future daily resets;
  - points still required after base plan;
  - total extra x1 runs;
  - runs scheduled now by strategy;
  - extra Pit Pass requirement;
  - expected Pit Pass return from Tribute Boxes;
  - projected tournament score;
- Auto-finish and exact Target-level readiness are surfaced in plan status.

Safety boundary:
- r12 DOES NOT automatically spend extra Pit Passes;
- it does not append reward-generated x1 runs to the execution plan yet;
- execution/recalculation after completed runs remains the next patch after UI/live calculation confirmation.

Marker:
`HK_PITS_REWARD_REV = 'pits-reward-planner-core-20260920-r12'`

Deploy:
- workflow: `Deploy TopKing Pits Reward Planner R12`;
- successful run: `35495840079`;
- Python patch compile: PASS;
- JS syntax: PASS;
- backup/deploy: PASS;
- service active: PASS;
- public round-trip byte equality: PASS;
- live/public SHA256: `56d5b9663b78767a6a290c71109878870b97113c975b21299869fce5fbca49a8`.

Baseline sync:
- run: `35495872850` — SUCCESS.

Current status:
**REWARD_PLANNER_CORE_LIVE_CANDIDATE_PENDING_USER_UI_CHECK**

Outstanding checks before reward execution:
1. r11 restoration decision modal still needs user-path confirmation when a Paws limit is hit;
2. r12 tournament section must be checked against live tournament values;
3. only after r12 UI/live-read/calculation is confirmed should automatic extra Pit Pass execution and after-run recalculation be enabled.


## Tournament reward execution r13

User accepted the r12 planner UI and asked to continue.

Pinned donor execution behavior used:
- reward-enabled Pits may open available Tribute Boxes before reward continuation;
- reward continuation uses ITEM-paid Pit rounds;
- after every completed round the live leaderboard score is reread;
- remaining reward steps are recalculated from live score, future base steps and future daily points;
- if the target is already reached or future scheduled work is enough, remaining reward steps are removed;
- gradual/upfront/last-day scheduling follows the donor requested-now formula;
- actual Pit Pass balance and direct ITEM cost are revalidated immediately before every reward round.

r13 includes:
- reward steps are appended to the selected Pit execution config only when r12 marks the reward plan valid;
- base steps are tagged separately from reward-generated ITEM steps;
- Tribute Boxes are opened only in full x100 batches;
- box opening is reread authoritatively before reward spending continues;
- live leaderboard score is refreshed after every completed round;
- reward continuation is recalculated dynamically and the runner total is adjusted;
- reaching the reward target removes unnecessary remaining reward x1;
- if actual Pit Pass balance is insufficient even after available x100 boxes are opened, remaining reward steps are removed and the reward branch stops safely instead of overspending;
- every ITEM reward start still passes through the existing live cost and balance checks.

Marker:
`HK_PITS_REWARD_EXEC_REV = 'pits-reward-execution-20260920-r13'`

Deploy:
- workflow: `Deploy TopKing Pits Reward Execution R13`;
- run: `35496430554` — SUCCESS;
- Python patch compile: PASS;
- JS syntax: PASS;
- backup/deploy: PASS;
- service active: PASS;
- public round-trip byte equality: PASS;
- live/public SHA256: `c51b1549bd631bcc4ea87df8b37a4be990db2300470f6c446a81319532c3ef6b`.

Baseline sync:
- run: `35496474389` — SUCCESS.

Current status:
**REWARD_EXECUTION_R13_LIVE_CANDIDATE_PENDING_USER_CHECK**

Required user-path check:
1. choose one Pit with an active tournament and exact target level;
2. select a reachable reward target and strategy;
3. enable the Pit and start;
4. expected runner behavior:
   - full x100 Tribute Box openings appear first if available and reward planning needs them;
   - normal/base Pit round(s) execute;
   - live tournament score is reread;
   - runner logs `дополнительные x1 пересчитаны: before → after` when the continuation changes;
   - only then ITEM reward rounds execute;
   - if target is reached early, remaining reward rounds disappear;
   - if actual Pit Pass balance is insufficient, reward continuation stops safely without a paid request.

Outstanding:
- r11 restoration-decision modal still lacks a dedicated user-path confirmation;
- r13 reward execution/recalculation needs one live user test.
Do not advance to Bosses until these Stage 2.02 live checks are complete.


## Plan summary and execution totals r14

Transferred from pinned Kokkaras donor:
- execution-plan summary before start;
- selected Pits count and total planned rounds;
- maximum crystal / Pit Pass / Restoration Paws budgets;
- per-Pit start level and execution mode;
- actual per-Pit totals after execution;
- overall totals across all selected Pits.

Counters are based on actual successful actions:
- active/resumed Pit does not count already-spent passes;
- newly started round adds its real multiplier to passes used;
- crystals and Pit Pass items count actual live start costs;
- Restoration Paws count only successful respawns.

Marker:
`HK_PITS_SUMMARY_REV = 'pits-plan-totals-20260920-r14'`

Deploy:
- run `35496803315` — PASS;
- live/public SHA256: `0079d453a830fc452b7d1d953cc3c2991ac023daea7543112377ccd90c1cade9`;
- public byte equality: PASS.

Baseline sync:
- run `35496845598` — PASS.

No Pit API/action logic changed in r14.


## Shared tournament resource forecast r15

Transferred from pinned donor:
- existing shared Pit Passes;
- selected Pit-plan ITEM cost through the tournament deadline;
- current + projected Tribute Boxes;
- expected x100 box returns at 2 Pit Passes per full batch;
- passive Pit Pass income from `bonuses.passive_income_item` including building bonus and active VIP component;
- projected shared Pit Pass balance;
- future free Pit runs;
- maximum reachable reward tier.

Marker:
`HK_PITS_SHARED_FORECAST_REV = 'pits-shared-reward-forecast-20260920-r15'`

Deploy:
- run `35496976601` — PASS;
- live/public SHA256: `c5806b911ddc4c89aec36ad5dc99a672e18ba8a1870adfc03c31ecd4632bce9c`;
- public byte equality: PASS.

Baseline sync:
- run `35497018252` — PASS.

r15 is forecast/UI only; no action/spending path changed.


## Reward-only plan r16

Transferred from pinned donor:
- synthetic pass plan `reward-0`;
- label: `Только цель награды — 0 базовых запусков`;
- option is available only while a tournament reward target is selected;
- base steps are empty;
- execution consists only of reward-generated ITEM continuation steps;
- if the reward target is removed, the synthetic plan falls back to a normal pass plan;
- runnable validation requires the selected reward plan itself to be valid.

Marker:
`HK_PITS_REWARD_ONLY_REV = 'pits-reward-only-plan-20260920-r16'`

Deploy:
- successful run `35497301664`;
- live/public SHA256: `7a94ab3ce598fca1c12bc3daab4e41f46bc0bdccd517869f9662bf723dd3afdf`;
- public byte equality: PASS.

Baseline sync:
- run `35497344758` — PASS.
