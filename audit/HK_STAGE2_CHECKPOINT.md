# HK Stage 2 — Checkpoint

## Execution mode

Stage 2 is executed one migrated module at a time.

Each module:
1. SOURCE PREFLIGHT against pinned Kokkaras donor;
2. verify exact current live/public script and module code path;
3. verify UI/read/calculation/action/state-refresh/rerun as far as can be done non-destructively;
4. user performs any authenticated/state-changing browser check that cannot be safely executed from CI;
5. save module audit;
6. update this checkpoint;
7. stop.

## Current state

- stage: 2
- status: IN_PROGRESS
- current module: Bosses / Боссы
- current module file: audit/hk-stage2-03-bosses.md
- current module status: SOURCE_PREFLIGHT_PENDING
- next module after LIVE PASS: Maps / Карты
- Today / Сегодня: LIVE PASS

## Module order

1. Today / Сегодня
2. Pits / Ямы
3. Bosses / Боссы
4. Maps / Карты
5. Resources / Ресурсы
6. Buildings / Здания
7. Explore / Исследование
8. Businesses / Бизнесы
9. Recipes / Рецепты
10. Auto Routines / Авто-рутины
11. Growth / Развитие
12. Hamsters / Хомяки
13. Generals / Генералы
14. Fair / Ярмарка
15. Regular Fair / Обычная ярмарка
16. Shop / Магазин
17. Clan Skills / Навыки клана
18. Wars / Войны


## Today candidate

- marker: `today-kokkaras-order-20260920-r1`
- version: `1.17.4`
- live SHA256: `303f6813d6e001751b53b32d83c6098f307aeedcee6a3cf320887bc93a07a117`
- technical deploy/public verification: PASS
- user UI confirmation: PENDING

- r2 marker: `today-kokkaras-filter-20260920-r2`
- donor-exact Event Regular filter: PASS
- reward rows use explicit "Собрать" wording

- r3 marker: `today-toolbar-clean-20260920-r3`
- removed redundant Today toolbar buttons
- auto-refresh on module open retained
- technical verification: PASS


## Completed modules

- 2.01 Today / Сегодня — LIVE PASS
  - final SHA256: `303f6813d6e001751b53b32d83c6098f307aeedcee6a3cf320887bc93a07a117`
- 2.02 Pits / Ямы — LIVE PASS
  - final marker: `pits-reward-picker-20260920-r20`
  - final SHA256: `c733c62a49c38ae6c497c03c89ee9ec018363bc8f75c2ec64e7e8f3990dfafdb`
  - baseline sync: `35498145691` — PASS


## Pits donor source block

- expected donor: Kokkaras HK Control Panel `5.3.22-ui-icons-pit-dim`
- expected SHA256: `28c3104020ecb7f54d0d51a72d067404d0176bc069d59fcca417d66817d1fcf1`
- File Library lookup: NOT FOUND
- current module: BLOCKED_DONOR_SOURCE_NOT_FOUND
- no Pits gameplay code changed
- resume action: restore/re-upload the exact pinned donor, then rerun SOURCE PREFLIGHT and continue 2.02


## Pits donor source restored

- exact pinned donor re-uploaded
- CRLF → LF canonical SHA256 verified: `28c3104020ecb7f54d0d51a72d067404d0176bc069d59fcca417d66817d1fcf1`
- previous BLOCKED status resolved
- Stage 2.02 Pits preflight resumed


## Pits canonical transfer bug

- bug: `audit/hk-stage2-bug-pits-canonical-transfer-gap.md`
- live verification run: `35490479912`
- status: CONFIRMED
- active live path: legacy single-Pit `pitLoop()`
- donor canonical three-Pit `runPits(configs)`: missing
- next action: fix Pits only; do not advance to Bosses


## Pits canonical core r1

- marker: `pits-canon-core-20260920-r1`
- deploy run: `35491426778`
- technical verification: PASS
- live/public SHA256: `0d6de4888121d5e09d2cd5fa5140ec5941734dd30c23dc70fbbd95a951dcb825`
- core UI/live-read user confirmation: PENDING
- advanced donor Pits (sniper + tournament reward planning + restoration decision): PENDING next Pits block
- do not advance to Bosses


## Pits UI r2 + Pass-plan / Sniper r3

- UI r2 marker: `pits-ui-align-20260920-r2`
- UI r2 deploy run: `35492472689`
- r2 live SHA256: `a3df20e0996ced42e4efa39baa5f25b9e41af979657854079c8e645e57b16708`

- r3 marker: `pits-passplan-sniper-20260920-r3`
- r3 deploy run: `35493218772`
- technical deploy/public verification: PASS
- r3 live/public SHA256: `42d39c573c5bb8bf445f8166a72a6b0a16fde14295365a0ebea0ee43e71b6f64`
- baseline sync run: `35493258548` — SUCCESS

r3 fixes:
- canonical active-state now follows donor `state.is_finish === false`;
- false active-state no longer blocks Pass plan on finished Pit snapshots;
- donor Sniper mode added per Pit;
- Sniper ×1 payment selector: FREE / PREM / ITEM;
- donor recommended Sniper target and higher target selection added;
- normal Pass plan state is preserved separately from Sniper settings.

Pinned donor:
- exact upload `скрипт Kokkaras,.txt`;
- canonical SHA256: `28c3104020ecb7f54d0d51a72d067404d0176bc069d59fcca417d66817d1fcf1`;
- donor is not stored in repo by user choice; re-upload exact file if a future chat needs donor code.

Current module status:
**PASSPLAN_SNIPER_LIVE_CANDIDATE_PENDING_USER_UI_CHECK**

Next action:
user reloads game → HK → Ямы and visually checks Pass plan + Sniper only.
Do not press Start yet.
Do not begin tournament reward planning / restoration decision / Bosses before this check.


## Pits toolbar r4 + UI/live-read PASS

- user confirmed current Pits UI/pass-plan/sniper configuration is OK;
- requested cleanup: removed `Обновить данные` button only;
- automatic refresh on opening Pits remains;
- r4 marker: `pits-toolbar-clean-20260920-r4`;
- deploy run: `35493415188` — PASS;
- live/public SHA256: `003c3a2a47bc2dc97e1e073b14744a57463d936e1fdc20b02e6041b124842223`;
- baseline sync run: `35493446456` — SUCCESS.

Current module status:
**UI_LIVE_READ_PASS_ACTION_PENDING**

Next required chain:
action → authoritative state update → rerun.
Do not advance to Bosses until Pits reaches LIVE PASS.


## Pits start action r5

- bug: run config was captured after async reread/re-render;
- fix: capture selected Pits/config before any await, start runner immediately, then live reread/revalidate;
- donor execution order restored for this boundary;
- marker: `pits-start-config-snapshot-20260920-r5`;
- deploy run: `35493622785` — PASS;
- live/public SHA256: `c373370ba5c3cf9a24f19d7e3ae82e871c124357e2d940f954fe834520a44629`;
- baseline sync: `35493651043` — PASS.

Current module status:
**ACTION_RETEST_PENDING**

Do not advance to Bosses until action → state update → rerun is confirmed.

## Pits respawn r6

User action reached battle/restoration and exposed a missing helper:
`pitCanonRespawnCost is not defined`.

- Start button/action entry is therefore confirmed working.
- r6 transfers donor-compatible respawn-cost calculation.
- marker: `pits-respawn-cost-20260920-r6`;
- deploy run: `35493832589` — PASS;
- live/public SHA256: `f8644b37332e2b8d9d763ef80ff00768f932fae31e88963bac51f8791946d895`.
- static Pit action-path function audit: no other undefined canonical helper calls found.

Current module status:
**RESPAWN_RETEST_PENDING**

Next:
resume/re-run the selected active Pit and verify restoration → state update → completion/rerun.
Do not advance to Bosses yet.


## Pits saved power table r7

- `Сохранённая сила уровней` now starts collapsed;
- manual expansion remains available;
- no data/forecast/action logic changed;
- marker: `pits-power-table-collapsed-20260920-r7`;
- deploy run: `35494081452` — PASS;
- live/public SHA256: `06422b7f259c15c47259e2156ea4446b2286bba6e9f8db3769d16faf7763bc6a`;
- baseline sync: `35494109901` — PASS.


## Pits runner history r9

- active Pits runner is now visually highlighted;
- runner shows the last 10 Pits execution messages for the current run;
- history resets on each new run;
- existing bottom journal remains unchanged;
- marker: `pits-runner-history-20260920-r9`;
- deploy run: `35494398235` — PASS;
- live/public SHA256: `bbc766dc775c7ce637302f1ecf1edfae28b835afeab8408c214abe47b4950fdd`;
- baseline sync: `35494440507` — PASS.


## Pits fast cycle r10

- user requested slightly faster battle/respawn cadence;
- removed mandatory full `/player/me` reread after every battle and respawn when the mutation response already provides Pit state;
- preserved fallback authoritative reread if state is absent;
- preserved short anti-lock pacing (80–180 ms depending on Pit/sniper mode);
- pre-start validation and post-finish rereads remain;
- marker: `pits-fast-cycle-20260920-r10`;
- deploy run: `35494689254` — PASS;
- live/public SHA256: `973e1b1788b86caaefac7a26b66f0eb42bc497ed49a618c277ebf36df63e6e25`;
- baseline sync: `35494718699` — PASS.

Current module status remains:
**RESPAWN_RETEST_PENDING**


## Pits r10 confirmed + restoration decision r11

User confirmed current Pits runner/action cadence after r10 is good.
Tested action path is no longer treated as the active regression.

r11:
- donor-compatible Restoration Paws decision flow added;
- current level / target / required / available / remaining are shown;
- choices: spend+continue / finish current round+continue / leave manual+continue / stop;
- remember choice + additional Paws budget applies only to the current Pits run;
- marker: `pits-restoration-decision-20260920-r11`;
- deploy run: `35495418034` — PASS;
- live/public SHA256: `d2667d1fec05456cdb7e7bba0f0da2854d3fccf6275cf5df991b44942d05e52c`;
- baseline sync: `35495453299` — PASS.

Current module status:
**RESTORATION_DECISION_LIVE_CANDIDATE_PENDING_USER_CHECK**

Next:
user verifies the decision modal at a low Paws limit.
After confirmation, continue Pits with tournament reward target planning / daily base runs / reward strategy.
Do not advance to Bosses.


## Pits tournament reward planner core r12

User asked to continue to the next Pits block before r11 user-path confirmation.

r12 adds donor-based live/read-only reward planning:
- per-Pit live tournament leaderboard/view reads;
- Reward target from live reward tiers;
- Daily base runs for future resets;
- strategies: Upfront / Gradual / Last day;
- exact-target tournament points forecast;
- future reset forecast;
- extra x1 / Pit Pass requirement;
- Tribute Box return forecast at 100 boxes -> 2 Pit Passes;
- projected tournament score.

Safety:
- no automatic extra Pit Pass spending in r12;
- reward continuation steps are not yet injected into the action plan.

Marker:
`pits-reward-planner-core-20260920-r12`

Deploy run:
`35495840079` — PASS

Live/public SHA256:
`56d5b9663b78767a6a290c71109878870b97113c975b21299869fce5fbca49a8`

Baseline sync:
`35495872850` — PASS

Current module status:
**REWARD_PLANNER_CORE_LIVE_CANDIDATE_PENDING_USER_UI_CHECK**

Still pending:
- r11 restoration modal user-path check;
- r12 live tournament UI/calculation check;
- then reward execution + after-run recalculation.
Do not advance to Bosses yet.


## Pits reward execution r13

User accepted r12 planner and asked to continue.

r13 activates donor-style reward continuation:
- only r12-valid reward plans can generate ITEM reward steps;
- Tribute Boxes open in full x100 batches;
- every reward ITEM round revalidates live balance/cost;
- live tournament score rereads after each completed Pit round;
- remaining reward steps recalculate dynamically from actual score;
- Upfront / Gradual / Last day requested-now semantics match donor;
- unnecessary future reward steps are removed when target/future schedule already covers the goal;
- insufficient actual Pit Pass balance safely cancels remaining reward continuation instead of overspending.

Marker:
`pits-reward-execution-20260920-r13`

Deploy:
`35496430554` — PASS

Live/public SHA256:
`c51b1549bd631bcc4ea87df8b37a4be990db2300470f6c446a81319532c3ef6b`

Baseline sync:
`35496474389` — PASS

Current module status:
**REWARD_EXECUTION_R13_LIVE_CANDIDATE_PENDING_USER_CHECK**

Pending before Pits LIVE PASS:
- r11 restoration decision user-path check;
- r13 reward execution/recalculation user-path check.
Do not advance to Bosses yet.


## Pits plan/totals r14

- donor execution-plan summary added before start;
- actual per-Pit and overall totals added after execution;
- actual counters: rounds / passes / crystals / Pit Passes / Restoration Paws;
- marker: `pits-plan-totals-20260920-r14`;
- deploy `35496803315` — PASS;
- live/public SHA256: `0079d453a830fc452b7d1d953cc3c2991ac023daea7543112377ccd90c1cade9`;
- baseline sync `35496845598` — PASS.

Pending Pits live checks remain r11 restoration decision and r13 reward execution.
Do not advance to Bosses yet.


## Pits shared tournament forecast r15

- donor shared Pit Pass/Tribute Box/passive-income forecast transferred;
- maximum reachable reward tier shown;
- no spending logic changed;
- marker: `pits-shared-reward-forecast-20260920-r15`;
- deploy `35496976601` — PASS;
- live/public SHA256: `c5806b911ddc4c89aec36ad5dc99a672e18ba8a1870adfc03c31ecd4632bce9c`;
- baseline sync `35497018252` — PASS.


## Pits reward-only plan r16

- donor `reward-0` mode transferred;
- reward target only / zero base runs;
- only computed tournament reward ITEM continuation executes;
- marker: `pits-reward-only-plan-20260920-r16`;
- deploy `35497301664` — PASS;
- live/public SHA256: `7a94ab3ce598fca1c12bc3daab4e41f46bc0bdccd517869f9662bf723dd3afdf`;
- baseline sync `35497344758` — PASS.

Still pending before Pits LIVE PASS:
- r11 restoration decision user-path check;
- r13 reward execution/recalculation user-path check.


## Pits r17–r19 final donor mechanics

### r17 — runtime preview
- exact game preview / winrate transferred;
- normal `pit/preview`, boss `pit_2/preview`, gang `pit_pve/preview`;
- exact `шанс игры` preferred; stored-power forecast is fallback;
- deploy `35497432303` — PASS;
- SHA256 `8a461d0627209a55eff885c039ecb92356feb51519e2e1e4e3c3660d0266afd1`;
- sync `35497472469` — PASS.

### r18 — adaptive reward batch fit
- reward ITEM step can shrink to the largest supported affordable batch and decompose the remainder;
- total reward multiplier is preserved;
- deploy `35497591634` — PASS;
- SHA256 `8f76e1d6ef11e15765c499807552d2e1b6c8bea7ee5f76d6e0d9eb06d0dabd6b`;
- sync `35497639381` — PASS.

### r19 — aggregate preflight
- checks total crystals, configured Paws ceiling and shared Pit Pass/Tribute Box economy before first mutation;
- failure stops before spending;
- marker `pits-aggregate-preflight-20260920-r19`;
- deploy `35497775963` — PASS;
- live/public SHA256 `0c13faad6e3a85b6105e62d8b9e764077724063947c047e13a377b1d8c0fe71a`;
- sync `35497815376` — PASS.

Current module status:
**FINAL_LIVE_CHECKS_PENDING**

No Bosses yet.

Required final Pits checks:
- r11 restoration-decision live path;
- reward target execution/recalculation + final state/rerun;
- runtime exact winrate visibility when preview supplies data.


## Pits final static parity audit

After r19:
- all Pits revision markers r1–r19 present in current baseline;
- required canonical helpers/action paths present;
- active canonical runner is `runPitsCanonical()`;
- legacy `pitLoop()` has no active call site;
- donor reward-card picker remains a visual difference only; current inline reward UI was already user-approved and retains the functional planning/execution semantics.

Static donor parity:
**DONOR_FUNCTIONAL_PARITY_PASS**

Current module status:
**FINAL_LIVE_CHECKS_PENDING**

No more speculative Pits patches.

Live confirmations still required:
1. restoration decision modal (r11);
2. reward execution/recalculation/adaptive batch path (r13/r18/r19);
3. exact game winrate visibility from runtime preview (r17);
4. resulting state + rerun confirmation.

Only after these: mark Stage 2.02 Pits LIVE PASS and proceed to Bosses.


## Pits reward picker r20

- donor reward-card picker UI added;
- live reward contents shown on selectable cards;
- forecast and validity shown per reward tier;
- picker and inline reward target remain synchronized;
- marker: `pits-reward-picker-20260920-r20`;
- deploy `35497956677` — PASS;
- live/public SHA256: `c733c62a49c38ae6c497c03c89ee9ec018363bc8f75c2ec64e7e8f3990dfafdb`;
- baseline sync `35498145691` — PASS.

Pits now have static donor UI + functional parity.

Current module status:
**FINAL_LIVE_CHECKS_PENDING**

No more speculative Pits patches.
Required user live checks:
- r11 restoration decision;
- reward execution/recalculation/adaptive fit + rerun;
- r17 runtime exact winrate.
Only after these: mark Pits LIVE PASS and proceed to Bosses.


## Pits handoff revalidation after r20

- pinned donor revalidated from the current uploaded `скрипт Kokkaras,.txt`;
- raw upload SHA256: `8a5aece8b10dfbaf0b3dd2890de600a9505aa523783cbe0c97ea81331d7e0c7d`;
- CRLF -> LF canonical SHA256: `28c3104020ecb7f54d0d51a72d067404d0176bc069d59fcca417d66817d1fcf1` — exact REFERENCE match;
- current baseline re-read: Pits markers r1-r20 present;
- active canonical runner: `runPitsCanonical()`;
- legacy `pitLoop()` remains defined but is not the active Pits start path;
- no Pits code change made during this revalidation;
- module status remains **FINAL_LIVE_CHECKS_PENDING**.

Remaining live-only checks:
1. r11 Restoration decision: exceed configured Paws limit, choose spend+continue, verify state change;
2. reward execution/recalculation: r13 + r18 + r19 controlled run and resulting state;
3. r17 exact runtime winrate from game preview;
4. rerun and confirm the resulting state is read correctly.


## Pits final live confirmation

User confirmed all remaining r20 final live checks are working:
- r11 Restoration decision: PASS;
- r13/r18/r19 reward execution, recalculation, adaptive fit and aggregate preflight: PASS;
- r17 exact runtime preview winrate: PASS;
- resulting state and rerun read: PASS.

Stage 2.02 Pits / Ямы: **LIVE PASS**.
No post-r20 code patch was required; final live/public SHA remains `c733c62a49c38ae6c497c03c89ee9ec018363bc8f75c2ec64e7e8f3990dfafdb` and baseline sync `35498145691` remains current.

Stage 2 continues with 2.03 Bosses / Боссы.
