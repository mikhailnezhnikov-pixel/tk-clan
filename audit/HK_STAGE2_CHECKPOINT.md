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
- userscript: 1.17.40
- current module: Hamsters / Хомяки — Stage 2.12 verification
- current module file: audit/hk-stage2-12-hamsters.md
- current module status: SOURCE_PREFLIGHT_PASS · DONOR_COST_PARITY_BUG_CONFIRMED · TECHNICAL_LIVE_PASS · USER_BROWSER_CHECK_PENDING
- Maps / Карты: W1–W8 shared knowledge COMPLETE; Unified Maps Runtime U1 PASS
- Buildings / Здания: LIVE PASS
- Explore E4 multi-building: LIVE PASS
- Explore / Исследование: LIVE PASS
- parallel FULL235: separate track; do not mix into Stage 2 module gate

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
- 2.03 Bosses / Боссы — LIVE PASS
  - final marker: `bosses-area-target-20260920-r2`
  - final SHA256: `0e168e81ff6e4ee42400f99aaad8a4fb9359bcfbdc051d56c981d0adcbf247e7`
  - Area Boss Calculator intentionally remains website-only
- 2.04 Maps / Карты — REOPENED: SCANNER_R2_LIVE_CANDIDATE
  - marker: `stage2e-maps-20260919-r1`
  - no new patch required
- 2.05 Resources / Ресурсы — LIVE PASS
  - revision: `bureau-resources-live-20260920-r1`
  - no new patch required
- 2.06 Buildings / Здания — LIVE PASS
- 2.07 Explore / Исследование — LIVE PASS
- 2.08 Businesses / Бизнесы — FUNCTIONAL CHECKPOINT 1.17.30
  - Kokkaras rearrangement canon restored;
  - 429 Game API guard PASS;
  - collector activity lease PASS;
  - vertical Businesses Runner PASS;
  - catalog remains read-only;
- 2.09 Recipes / Рецепты — LIVE PASS
  - custom HK implementation confirmed working by user;
  - technical live verifier PASS;
  - global 429 cooldown regression fixed in 1.17.31;
- 2.10 Auto Routines / Авто-рутины — LIVE PASS
  - fail-closed chain PASS;
  - continuous collector lease PASS;
  - embedded into Today in 1.17.35;


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


## Bosses canonical transfer gap

- pinned donor source preflight: PASS;
- current baseline marker: `bosses-readonly-20260920-r1`;
- donor full Area/Regional Bosses mechanics are absent from current read-only module;
- bug: `audit/hk-stage2-bug-bosses-readonly-transfer-gap.md`;
- Stage 2.03 status: **CANONICAL_TRANSFER_GAP_CONFIRMED**;
- next action: transfer Bosses canonical core only, then live-test it before advancing to Maps.


## Bosses canonical core r1

- donor-first canonical Area + Regional core transferred;
- marker: `bosses-canon-core-20260920-r1`;
- technical predeploy: PASS;
- deploy/service/public byte equality: PASS;
- live/public SHA256: `571d97f7aa2adf5d747f94275350abf0872f04a63bdaf795c9ec53aed2b393a9`;
- baseline sync commit: `bac973abc67096f5642fce84ab1df8ba1a16883e` — PASS;
- current module status: **AREA_TARGET_R2_LIVE_CANDIDATE**.

Remaining static donor parity before final Bosses live checks:
- Area Boss tournament target/reward planning;
- reward-only continuation;
- Area Boss Calculator / rewards view.

Do not advance to Maps.


## Bosses area target r2

- canonical core r1 remains live and is extended by r2;
- r2 markers: `bosses-area-target-20260920-r2`;
- Area Boss target planning + reward-only continuation transferred;
- technical live verification: syntax PASS, public byte equality PASS, target/reward markers PASS;
- live/public SHA256: `0e168e81ff6e4ee42400f99aaad8a4fb9359bcfbdc051d56c981d0adcbf247e7`;
- current module status: **AREA_TARGET_R2_LIVE_CANDIDATE**.

Remaining before Bosses LIVE PASS:
- live user-path confirmation for Area + Regional action/state/rerun;
- live user-path confirmation for Area target/reward continuation;
- Area Boss Calculator / rewards view transfer.

Do not advance to Maps.


## Bosses final live confirmation

User confirmed Bosses r2 works correctly in live use.
- Area + Regional action paths: PASS;
- state refresh and rerun: PASS;
- Area target/reward continuation: PASS;
- Area Boss Calculator is explicitly out of userscript scope because it already exists on the website.

Stage 2.03 Bosses / Боссы: **LIVE PASS**.
Final live/public SHA remains `0e168e81ff6e4ee42400f99aaad8a4fb9359bcfbdc051d56c981d0adcbf247e7`.

Stage 2 continues with 2.04 Maps / Карты.


## Bosses website-only calculator scope lock

- user explicitly confirmed Area Boss Calculator remains on the website and must not be added to the userscript;
- attempted Bosses calculator r3 deploy did **not** reach live;
- diagnostic confirmed live remained r2 at SHA256 `0e168e81ff6e4ee42400f99aaad8a4fb9359bcfbdc051d56c981d0adcbf247e7` with no r3 calculator marker;
- r3 deploy/sync/diagnostic workflow and payload/trigger artifacts were removed;
- Stage 2.03 Bosses remains **LIVE PASS** at r2.

Stage 2.04 Maps resumes from **SOURCE_PREFLIGHT_PENDING** until a Maps-specific audit/candidate is actually recorded.


## Maps Stage 2.04 final

- current Maps implementation revalidated against the transferred Stage 2E patch and existing live verification;
- UI/read/calculation/action/state-reread/runner path present;
- no confirmed regression found;
- no redeploy required.

Stage 2.04 Maps / Карты: **LIVE PASS**.
Stage 2 continues with 2.05 Resources / Ресурсы.


## Resources Stage 2.05 final

- current Resources module revalidated against the deployed 1.17.1 Bureau/Resources fix;
- live read, budget calculation, guarded mutation, state refresh and rerun path are present;
- no confirmed regression found;
- no new deploy required.

Stage 2.05 Resources / Ресурсы: **LIVE PASS**.
Stage 2 continues with 2.06 Buildings / Здания.


## Buildings / Explore semantic transfer gap

Donor-first revalidation found that the historical Stage 2I implementation is not functionally equivalent to pinned Kokkaras:
- Buildings currently provides read/list only, while donor has filtered automatic opening + favorites;
- Explore currently duplicates district/map research, while donor Explore Buildings is a full building event/battle/upgrade automation.

Tickets:
- `audit/hk-stage2-bug-buildings-canonical-transfer-gap.md`;
- `audit/hk-stage2-bug-explore-canonical-transfer-gap.md`.

Current Stage 2.06 status: **CANONICAL_TRANSFER_GAP_CONFIRMED**.
Transfer Buildings first; Explore follows only after Buildings live candidate.


## Buildings canonical core r1

- donor Buildings automation transferred without Kokkaras runtime dependency;
- marker: `buildings-canon-core-20260920-r1`;
- exact input Bosses r2 SHA verified before patch;
- syntax/deploy/service/public byte equality: PASS;
- live/public SHA256: `0931ee3eb65a16f9dd768fe51b9a84b897620e011c51ee9e0226d92f37b9e686`;
- baseline sync: PASS;
- current module status: **CANON_CORE_R1_LIVE_CANDIDATE**.

Pending: one live open/favorite/state-rerun confirmation. Explore transfer gap remains queued for Stage 2.07 and is not part of this Buildings patch.


## Maps scanner r2 repair

User live screenshot exposed a real building-study attribution/backfill bug in Maps. The earlier Maps LIVE PASS is reopened.

Fix:
- `maps-building-scan-20260920-r2`;
- persistent `building_id -> area_id` relation;
- lazy owned-area lookup when relation is missing;
- safe full-study reread for already-active buildings during account scan;
- exact crystal-room submission back to the matching district/building;
- no closed building is opened by scanner backfill.

Technical live verification: PASS.
Live/public SHA256: `a250839d884d23ff12fb2808364338d62b5555554fad2edc4d7b4a1e0cec177e`.

Current status: **SCANNER_R2_LIVE_CANDIDATE**.
Buildings r1 remains deployed but its live confirmation is paused until Maps scanner r2 is confirmed. Explore remains blocked.


## Maps canonical coordinate fix r1

- reversed district coordinate labels confirmed;
- canonical map submission now converts raw game row/column to user-facing X:Y = column:row;
- marker: `maps-coordinates-column-row-20260920-r1`;
- technical live verification: PASS;
- live/public SHA256: `f52ed4a3c61a3833941f8bf0c5e8016be8a59eac2ca4f6f352dd28ee16c3b290`.

Maps remains **SCANNER_R2_LIVE_CANDIDATE** pending user confirmation after a fresh account-map scan.


## Rollback — both Maps fixes removed

User requested that neither experimental Maps fix remain applied.

Removed from live:
- scanner/backfill r2;
- coordinate swap r1.

Verified restored live:
- SHA256: `0931ee3eb65a16f9dd768fe51b9a84b897620e011c51ee9e0226d92f37b9e686`;
- public byte equality: PASS;
- syntax: PASS;
- `maps-building-scan-20260920-r2`: ABSENT;
- `maps-coordinates-column-row-20260920-r1`: ABSENT;
- `buildings-canon-core-20260920-r1`: PRESENT.

Deployment/check artifacts for both reverted fixes were removed to prevent accidental reapplication.

Current Maps status: **BUG_CONFIRMED_NO_FIX_APPLIED**.
Buildings r1 remains deployed; Explore remains blocked until Maps data semantics are redesigned and confirmed.


## Maps two-fix rollback incident and reapply

- an ambiguous user typo was interpreted as a request to remove both Maps fixes;
- rollback workflow restored pre-fix live SHA256 `0931ee3eb65a16f9dd768fe51b9a84b897620e011c51ee9e0226d92f37b9e686`, which explains why neither change was visible in the subsequent check;
- user immediately clarified that neither fix had applied and did **not** intend a rollback;
- exact previously verified two-fix candidate was reapplied;
- scanner marker: `maps-building-scan-20260920-r2`;
- coordinate marker: `maps-coordinates-column-row-20260920-r1`;
- live/public SHA256: `f52ed4a3c61a3833941f8bf0c5e8016be8a59eac2ca4f6f352dd28ee16c3b290`;
- syntax: PASS;
- public byte equality: PASS;
- accidental rollback workflow and trigger removed.

Maps remains **SCANNER_R2_LIVE_CANDIDATE** pending fresh user scan confirmation.


## Maps safe active-building scanner r3

- source rule now strictly intersects `/player/me.buildings` with `/game_area/{area}/buildings` before any detailed building read;
- active ID normalization supports `id` and `building_id`;
- event catalog is ensured for room matching;
- unavailable `/events` can no longer silently create false zero-crystal observations;
- unopened buildings are never read by scanner backfill;
- marker: `maps-active-intersection-20260920-r3`;
- coordinates marker retained: `maps-coordinates-column-row-20260920-r1`;
- live/public SHA256: `f8a34bff26fd449f315f07a2ef8e6a8a6e8169ea62f463e7efe527766d698101`;
- technical live verification: PASS.

Current Maps status: **SCANNER_R3_LIVE_CANDIDATE** pending user scan confirmation.


## Maps parallel reader r4

- safe scanner logic from r3 retained;
- 6 concurrent read-only `/player/building` workers;
- batched map submission up to 100 building observations per request;
- existing 429/transient/player-lock retry/backoff retained;
- unopened buildings remain excluded;
- marker: `maps-parallel-read-20260920-r4`;
- live/public SHA256: `f4f5a74ed8a4cc25b63ef11adf714d358ada0399f95a765bfedb21728a6162ca`;
- technical live verification: PASS.

Current Maps status: **SCANNER_R4_LIVE_CANDIDATE** pending user timing and map-result confirmation.


## Maps parallel reader r5

- 10 concurrent read-only `/player/building` workers;
- submit batches up to 200 building observations;
- r3 safety intersection and event guards retained;
- retry/backoff retained;
- marker: `maps-parallel-read-20260920-r5`;
- live/public SHA256: `d4c84856ffcad0617ce783451c054205491f7d0d956bf7e7ec1ae5315480680a`;
- technical live verification: PASS.

Current Maps status: **SCANNER_R5_LIVE_CANDIDATE** pending user timing/result confirmation.


## Maps coordinate backend r2

Root cause confirmed in live backend: existing non-null `map_areas.x/y` could not be replaced, and completed maps returned before coordinate updates.

Deployed fix:
- versioned coordinate payload `column-row-v1`;
- trusted coordinate update before `ignored_complete` return;
- old/unversioned submissions cannot overwrite corrected values;
- complete-map 32:23 -> 23:32 regression test PASS.

Client SHA256: `1932f3984a330edf234c02e80c0f27e1b845b299f3bb09875d166397dcded9d6`.
Server SHA256: `1fb8007651c6772400a1e6bc8b7f3152d0f907942a7fa0140e854e17d7f2a2e1`.
Maps remains live-candidate pending fresh user rescan confirmation.


## Maps ↔ Website shared knowledge base — staged implementation plan

### Goal

Create one shared canonical knowledge base for district/building knowledge so that:

- data collected by players through the userscript appears automatically in Website → Personal Cabinet → Maps;
- maps/imports added on the website feed the same shared building knowledge used by the userscript;
- geometry and knowledge stay separate:
  - `hk_maps_catalog` / `hk_map_points` = website map geometry / visualization layer;
  - `map_areas` / `map_buildings` / `map_area_aliases` = canonical district/building knowledge layer;
- do **not** create two periodically synchronized independent databases.

### Current live state before this work

- Maps scanner marker: `maps-parallel-read-20260920-r5`
- parallel read-only `/player/building` workers: 10
- map submit batch: 200
- coordinate marker: `maps-coordinates-column-row-20260920-r2`
- canonical coordinate backend revision: `column-row-v1`
- current userscript live/public SHA256:
  `1932f3984a330edf234c02e80c0f27e1b845b299f3bb09875d166397dcded9d6`
- current map backend SHA256:
  `1fb8007651c6772400a1e6bc8b7f3152d0f907942a7fa0140e854e17d7f2a2e1`
- coordinate complete-map regression: PASS
- Maps is still a live candidate pending user rescan confirmation.
- Do not modify Explore while this work is in progress.
- Do not alter scanner safety rule: only read `/player/building` for IDs in the safe active-building intersection.

### Stage W1 — Audit only, no live changes

Inspect the current live/backend implementation of:

- `map_areas`
- `map_buildings`
- `map_area_aliases`
- `hk_maps_catalog`
- `hk_map_points`
- `/maps/list`
- `/maps/detail`
- `/maps/submit`
- HK Maps / Kokkaras import path
- Personal Cabinet → Maps read path
- current 235 website maps

Required output before any schema/write change:

1. exact current data flow;
2. how many of the 235 maps can be linked automatically to a canonical `area_id`;
3. exact proposed relation between `map_key` and `canonical_area_id`;
4. unresolved/ambiguous maps list;
5. no live mutation.

PASS gate: audit written and reviewed.

#### W1 result — PASS (2026-09-20)

- audit evidence: `audit/HK_STAGE2_W1_MAPS_SHARED_KB_AUDIT.md`
- read-only live snapshot: `map_areas=301`, `map_buildings=162170`, `map_area_aliases=301`, `hk_maps_catalog=235`, `hk_map_points=235`;
- all 301 current alias rows are self-aliases; no non-self alias existed in the W1 snapshot;
- historical HK Maps coordinate convention is `grid Y:X`; canonical discovery must use `x=grid.X`, `y=grid.Y`;
- direct unswapped interpretation produced 0 matches and is rejected;
- safe automatic links: **26/235**;
- ambiguous: **0**;
- unresolved/not found: **209**;
- no duplicate canonical target among the 26 safe candidates;
- exact 26 `map_key → canonical_area_id` candidates and all 209 unresolved maps are recorded in the W1 audit;
- current Personal Cabinet maps still read `hk_maps_catalog/hk_map_points` only; userscript `/maps/list|detail|submit` still use `map_areas/map_buildings/map_area_aliases`;
- W2 recommended durable bridge: `hk_map_area_links(map_key PK/FK → hk_maps_catalog, canonical_area_id FK → map_areas, match_method, linked_at)`;
- **no live/schema/write/deploy mutation was performed during W1**;
- W2 is **NOT STARTED** and requires an explicit next instruction.


### Stage W2 — Link website map ↔ canonical game district

Add a durable relation:

`map_key → canonical_area_id`

Prefer exact `area_id` when available.
For historical maps without an exact game area ID, use:

`city + canonical X:Y`

only to discover the match, then persist the resolved canonical relation.

Do not migrate all building data yet.

PASS gate:
- one test website map is linked to exactly one canonical district;
- no duplicate district is created;
- aliases still resolve correctly.

#### W2 result — PASS (2026-09-20)

- audit evidence: `audit/HK_STAGE2_W2_MAPS_SHARED_KB_LINK.md`;
- durable bridge added: `hk_map_area_links(map_key PK/FK, canonical_area_id FK, match_method, linked_at)`;
- supported match methods: `exact_area_id`, `city_grid_yx`;
- historical coordinate rule retained: HK Maps `Y:X` → canonical `x=X,y=Y`;
- pilot: `hk_moscow1226` → `9ea6ff78-b881-45b3-b92d-a8f1da8eca05`;
- pilot canonical coordinates: Moscow `x=26,y=12`;
- live bridge rows: **1**;
- duplicate district created: **NO**;
- alias resolution: **PASS**;
- `hk_maps_catalog=235`, `hk_map_points=235`;
- building migration: **NO**;
- userscript/public SHA unchanged: `1932f3984a330edf234c02e80c0f27e1b845b299f3bb09875d166397dcded9d6`;
- live server SHA: `1fe9fc44953713032bad755bc658233e881cba1941d7fae53747e6d27e7a7e3e`;
- build run `35508970854`: PASS;
- successful live run `35509058115`: PASS;
- first live attempt `35509018962` failed in read-only CI quoting before any live change;
- Explore/scanner behavior untouched;
- **W3 NOT STARTED**; stop here until explicit user instruction.


### Stage W3 — Website → shared userscript knowledge, one-map pilot

Use exactly one linked map first.

For that map:

- geometry remains in `hk_map_points`;
- known `building_id + crystals` from the authorized HK Maps import is written into canonical `map_buildings.room_count`;
- the userscript reads that knowledge through the existing shared map API;
- no bulk 235-map migration yet.

PASS gate:
- userscript can see the imported room counts for the pilot map without the current player scanning those buildings;
- no geometry duplication;
- no district duplication.

#### W3 result — PASS (2026-09-20)

- audit evidence: `audit/HK_STAGE2_W3_MAPS_SHARED_KB_PILOT.md`;
- final live verification: `audit/hk-stage2-maps-shared-kb-w3-final-verify.txt`;
- pilot remains `hk_moscow1226 → 9ea6ff78-b881-45b3-b92d-a8f1da8eca05`;
- authorized compact HK Maps source decodes to **32** positive points with histogram `1:17, 2:12, 3:3`, matching the saved HK Maps index;
- exact OSM/canonical building-ID recovery: **29/32**, ambiguous **0**, unmatched **3**;
- W3 deliberately imported only the 3 exact matches whose canonical `room_count` was still `NULL`:
  - `way29242551 → 2`;
  - `way29242552 → 2`;
  - `way430609368 → 2`;
- all three are investment points in the website source; W3 does not yet normalize/overwrite investment provenance;
- existing non-NULL canonical values overwritten: **0**;
- pilot canonical histogram after import: `0:114, 2:3`;
- source marker on the three imported rows: `source-hk-maps-import`;
- live rerun: **0 fills / 3 preserved** — idempotency PASS;
- existing canonical `map_detail()` read path returns the three imported `room_count=2` values without a new player scan;
- geometry remains in `hk_map_points`; point count stays **32**; geometry rewrite/duplication: **NO**;
- bridge rows: **1**; duplicate district: **NO**;
- W3 live server SHA: `26cf4729b90dd47da881760794b5bdcaef783c41b8fd4fba8e71b191f4d4f7e4`;
- build run `35510361084`: PASS;
- live import/data verification steps in run `35510477205`: PASS; its later client-SHA assertion used the stale W2 SHA and failed only because Explore E2 was being deployed independently in parallel;
- final read-only W3 run `35510595703`: PASS;
- current userscript SHA at final verification: `76833b35de3620f7b946fac3c02fca021cd48d332e58c51ce74a40616c199c14`;
- W3 changed userscript: **NO**;
- current userscript still contains Maps scanner r5, coords r2 and `column-row-v1`: PASS;
- the 26 exact positive source points conflicting with existing canonical zero values and the 3 unmatched points remain untouched pending provenance/conflict work;
- bulk map migration: **NO**;
- **W4 NOT STARTED**; stop here until explicit user instruction.


### Stage W4 — Shared knowledge → Website, one-map pilot

Make Personal Cabinet → Maps render the same pilot map from:

- geometry: `hk_map_points`;
- current canonical building knowledge: `map_buildings`.

PASS gate:
- player scan updates `map_buildings`;
- reopening the website map shows the same updated room counts automatically;
- no manual export/import is needed.

#### W4 result — PASS (2026-09-20)

- audit evidence: `audit/HK_STAGE2_W4_MAPS_SHARED_KB_WEBSITE.md`;
- live status: `audit/hk-stage2-maps-shared-kb-w4-live-status.txt`;
- live server SHA: `c1c583230f632ed38c654a00541809b1a7cb2f2bf0296708f4c44b2456ad46ce`;
- new pilot relation: `hk_map_point_links(map_key,point_index,building_id,match_method,linked_at)`;
- pilot: `hk_moscow1226 → 9ea6ff78-b881-45b3-b92d-a8f1da8eca05`;
- safe point→building links: **29/32**; unique canonical buildings: **29**; match method `osm_point_in_polygon`;
- 3 W3-unmatched points remain source fallback;
- `hk_map_data()` point mode now keeps delta geometry from `hk_map_points` and overlays current `map_buildings.room_count` at response time;
- stored pilot geometry remains point_count **32**, SHA256 `58ead2cc505d010b676ff5aac55b230c9609809600b69681c99f793d593c6cd6`;
- geometry rewrite/duplication: **NO**;
- W4 writes to `map_buildings`: **0**;
- live website render histogram from shared canonical knowledge: `0:26, 1:1, 2:3, 3:2`;
- investment bit preserved: **3** investment points;
- dynamic regression: changing canonical `room_count` changes the next `hk_map_data()` response while stored `hk_map_points` stays unchanged — PASS;
- no manual export/import is required after canonical knowledge changes;
- duplicate pilot district: **NO**;
- bulk migration: **NO**;
- build/regression run `35511398010`: W4 code/tests PASS; audit push later lost a branch race only;
- live run `35511455366`: build/precheck/deploy/link/website canonical-response verification PASS; final client assertion failed only because it expected obsolete scanner r5;
- current Maps scanner is now `maps-parallel-read-20260920-r6-safe5` with **5** read-only workers, per the user's requested throttle;
- current coordinate marker remains `maps-coordinates-column-row-20260920-r2`;
- current public userscript after parallel Explore r5: `df677e603e0a180e0e2e2b5ce27af268ab788ced12e4e6b2036d4c9b23c78115`;
- parallel Explore r5 explicitly verified `map_concurrency_5_preserved=PASS`;
- W4 changed userscript: **NO**;
- pilot is point-mode; full-contour generalized overlay is not claimed in W4;
- **W5 NOT STARTED**; stop here until explicit user instruction.


### Stage W5 — Source provenance and conflict rules

Add/normalize provenance for building knowledge.

At minimum distinguish:

- `game_live`
- `hk_maps_import`
- `legacy` if required by existing data

Conflict rule:

`game_live` has priority over imported/historical knowledge.

A later old import must not overwrite a newer authoritative live game observation.

PASS gate:
- explicit regression test proves imported data cannot overwrite newer `game_live` knowledge;
- source and timestamp are inspectable.

#### W5 result — PASS (2026-09-20)

- audit evidence: `audit/HK_STAGE2_W5_MAPS_PROVENANCE.md`;
- live status: `audit/hk-stage2-maps-shared-kb-w5-live-status.txt`;
- schema added to `map_buildings`:
  - `knowledge_source`;
  - `knowledge_observed_at`;
- normalized sources: `game_live`, `hk_maps_import`, `legacy`;
- live backfill: **162170** rows total:
  - `game_live=162167`;
  - `hk_maps_import=3`;
  - `legacy=0`;
- invalid/zero provenance timestamps after migration: **0**;
- current live-game submissions are authoritative and can refresh room knowledge even on a fully complete district;
- `hk_maps_import` remains NULL-only and cannot overwrite an existing non-null value;
- legacy/Kokkaras imports cannot overwrite complete canonical room knowledge;
- duplicate-area merge path now preserves provenance and prefers newer `game_live` knowledge over non-game/older live knowledge;
- explicit temp-DB conflict regression run `35512193549`: PASS:
  - `game_live` overwrites prior import on complete district;
  - later HK Maps import cannot overwrite that `game_live`;
  - later legacy import cannot overwrite it;
  - source + timestamp visible through `map_detail()`;
- live deploy/verification run `35512251926`: PASS;
- live server SHA: `8e3664d5a437ea7e924e91f4b6de3944e75b80e0bafbed5fc10769e37f71b22d`;
- pilot `hk_moscow1226` provenance after W5:
  - `game_live:114`;
  - `hk_maps_import:3`;
  - room histogram remains `0:114,2:3`;
- W4 website render remains `0:26,1:1,2:3,3:2`;
- geometry SHA unchanged: `58ead2cc505d010b676ff5aac55b230c9609809600b69681c99f793d593c6cd6`;
- current public userscript SHA unchanged by W5: `df677e603e0a180e0e2e2b5ce27af268ab788ced12e4e6b2036d4c9b23c78115`;
- Maps scanner remains `maps-parallel-read-20260920-r6-safe5` with **5** read-only workers;
- coordinate marker remains `maps-coordinates-column-row-20260920-r2`;
- bulk 235-map migration: **NO**;
- **W6 NOT STARTED**; stop here until explicit user instruction.


### Stage W6 — Dry-run and migration of all 235 website maps

Before any bulk write, produce a dry-run report:

- total maps: 235;
- exact area_id matches;
- city+X:Y matches;
- unresolved maps;
- ambiguous maps;
- maps that would create duplicates;
- building rows to add;
- building rows already known;
- room_count conflicts by source.

Only after reviewing the dry-run, migrate automatically resolvable maps.

PASS gate:
- resolved maps linked;
- no duplicate canonical districts;
- unresolved/ambiguous maps remain untouched and are reported;
- migration is rerunnable/idempotent.

#### W6 result — PASS (2026-09-21)

- audit: `audit/HK_STAGE2_W6_MAPS_SHARED_KB_MIGRATION.md`;
- final dry-run: `audit/hk-stage2-w6-final-dryrun.json`;
- final live status: `audit/hk-stage2-maps-shared-kb-w6-live-status.txt`;
- website maps reviewed: **235**;
- safe canonical matches migrated: **25**;
- unresolved and untouched: **210**;
- ambiguous maps: **0**;
- duplicate canonical target groups: **0**;
- safe point → canonical building matches: **2003**;
- unmatched points left untouched: **136**;
- ambiguous points left untouched: **4**;
- new canonical building rows created by W6: **0**;
- dry-run room conflicts: **266**, all against `game_live`; all preserved;
- final area links: **25**;
- final point links: **2007**;
- migration rerun/idempotency: **PASS**;
- final control run: `35519077891`, job `106099902200`: PASS;
- current server SHA: `8fe91e74f49ecec9ea662e5ec85c32f07854a6dd5ed03864f70a3261a43dc245`;
- current userscript SHA: `bddc55fc46bd4fe8da70c37799a35b74f3924015b071a3e692c532f0f7e6d766`;
- scanner remains `maps-parallel-read-20260920-r6-safe5`, concurrency **5**;
- coordinate marker remains `maps-coordinates-column-row-20260920-r2`;
- HK Maps point metadata was confirmed as bitmask:
  - `crystals = meta & 0x07`;
  - `investment = bool(meta & 0x08)`;
- W6 corrected the W4 overlay bitmask edge case; hotfix run `35518945365`: PASS;
- `hk_dubai5335` was deliberately moved to unresolved because current canonical coordinates do not satisfy the proven historical Y:X mapping; no force-link was made;
- **W7 NOT STARTED**; stop here until explicit user instruction.


### Stage W7 — New website uploads write directly to shared knowledge

Change the website import path so every new authorized map upload:

1. stores/updates geometry in `hk_maps_catalog` / `hk_map_points`;
2. resolves or creates the canonical district relation;
3. writes imported building knowledge into canonical `map_buildings` using source/provenance rules.

PASS gate:
- a new website map becomes visible to userscript knowledge automatically;
- no separate synchronization job is required.

#### W7 result — PASS (2026-09-21)

- audit: `audit/HK_STAGE2_W7_DIRECT_AUTHORIZED_UPLOAD.md`;
- build status: `audit/hk-stage2-maps-shared-kb-w7-build-status.txt`;
- live status: `audit/hk-stage2-maps-shared-kb-w7-live-status.txt`;
- new server path: `import_hk_authorized_map_upload()`;
- new CLI: `server.py --import-hk-authorized-map FILE.json[.gz]`;
- authorized upload contract now preserves exact `building_id` from full/raw map GeoJSON instead of reconstructing IDs later through OSM;
- upload requires explicit `coord_revision` and canonical X/Y metadata; silent coordinate-orientation guessing is rejected;
- one import now performs:
  - website catalog write;
  - compact geometry write;
  - canonical resolve/create;
  - canonical room knowledge write with `hk_maps_import` provenance;
  - area link write;
  - exact point link write;
- build run `35520020636`: PASS:
  - create canonical: PASS;
  - resolve existing canonical: PASS;
  - direct shared visibility through `map_detail()`: PASS;
  - `game_live` priority: PASS;
  - idempotent re-upload: PASS;
  - no separate sync: PASS;
- future authorized import workflow: `.github/workflows/import-authorized-hk-map.yml`;
- upload path: `deploy/maps/authorized/*.json.gz`;
- schema/contract: `deploy/maps/authorized/README.md`;
- live deploy run `35520130288`: PASS;
- live server SHA: `b5189981acade420e1aaa533dec8b745c0e16969bf1def0c5008aa297f2a2812`;
- deployed integration test used a temporary SQLite DB only; production test rows: **0**;
- production W6 state remains:
  - `hk_maps_catalog=235`;
  - `hk_map_points=235`;
  - `hk_map_area_links=25`;
  - `hk_map_point_links=2007`;
- W7 changed userscript: **NO**;
- current userscript SHA: `bddc55fc46bd4fe8da70c37799a35b74f3924015b071a3e692c532f0f7e6d766`;
- Maps scanner remains `maps-parallel-read-20260920-r6-safe5`;
- coordinate marker remains `maps-coordinates-column-row-20260920-r2`;
- website point renderer was corrected to the real HK Maps bitmask and now handles values 6/7 correctly;
- **W8 NOT STARTED**; stop here until explicit user instruction.


### Stage W8 — End-to-end verification and checkpoint

Test both directions on multiple districts:

A. userscript → shared DB → website
B. website/import → shared DB → userscript

Verify:

- coordinates;
- aliases;
- room_count;
- investment flag behavior;
- unknown/null buildings;
- source priority;
- rerun/idempotency;
- Personal Cabinet display;
- scanner still uses 5 read-only workers (`maps-parallel-read-20260920-r6-safe5`) and safe active-building intersection.

Only after user confirmation:
- mark Website ↔ Maps shared knowledge link PASS;
- resume the normal Stage 2 sequence.

#### W8 result — PASS (2026-09-21)

- user explicitly authorized continuing after W7, satisfying the W8 confirmation gate;
- audit: `audit/HK_STAGE2_W8_MAPS_SHARED_KB_E2E.md`;
- status: `audit/hk-stage2-maps-shared-kb-w8-status.txt`;
- temporary end-to-end summary: `audit/hk-stage2-w8-temp-e2e-summary.json`;
- production read-only samples: `audit/hk-stage2-w8-live-samples.json`;
- verification run `35520602358`, job `106103898484`: PASS;
- direction A, userscript/game_live → shared DB → website: **PASS on 2 districts**;
- direction B, authorized website import → shared DB → userscript: **PASS on 2 districts**;
- coordinates:
  - `column-row-v1`: PASS;
  - explicit `historical-yx`: PASS;
- aliases: PASS;
- room_count propagation in both directions: PASS;
- investment bit/is_invest behavior: PASS;
- unknown/NULL behavior: PASS;
- source priority `game_live > hk_maps_import`: PASS;
- rerun/idempotency: PASS;
- Personal Cabinet backend: PASS;
- live Personal Cabinet Maps UI path: PASS;
- live website point bitmask renderer: PASS;
- current server SHA: `b5189981acade420e1aaa533dec8b745c0e16969bf1def0c5008aa297f2a2812`;
- current userscript SHA: `bddc55fc46bd4fe8da70c37799a35b74f3924015b071a3e692c532f0f7e6d766`;
- scanner remains `maps-parallel-read-20260920-r6-safe5`;
- read-only scanner concurrency remains **5**;
- safe active-building intersection: PASS;
- coordinate marker remains `maps-coordinates-column-row-20260920-r2`;
- production bridge state:
  - `hk_maps_catalog=235`;
  - `hk_map_points=235`;
  - `hk_map_area_links=25`;
  - `hk_map_point_links=2007`;
  - duplicate canonical targets=0;
- real production read-only samples verified across New York, Moscow, and Saint Petersburg;
- W8 production writes: **NO**;
- **Website ↔ Maps shared knowledge link = PASS**;
- **W1–W8 shared-knowledge subproject = COMPLETE**;
- normal Stage 2 may resume on the **next explicit user instruction**; stop here.


### Unified Maps Runtime U1 — PASS (2026-09-21)

User-requested continuation after W8: one Personal Cabinet map list plus shared map knowledge consumed by the userscript before direct building research.

Evidence:
- audit: `audit/HK_STAGE2_UNIFIED_MAPS_RUNTIME_U1.md`;
- build status: `audit/hk-stage2-unified-maps-u1-build-status.txt`;
- live status: `audit/hk-stage2-unified-maps-u1-live-status.txt`;
- backend preflight: `audit/hk-stage2-unified-maps-preflight.txt`.

Implemented:
- Personal Cabinet `cabinet_maps()` now returns one unified list with source states:
  - `website`;
  - `script`;
  - `combined`;
- safely linked website+canonical districts appear once;
- script-only canonical districts are included;
- unresolved historical website maps remain visible as website-only rows until proven by a real game scan;
- current production unified list:
  - `combined=25`;
  - `script=285`;
  - `website=210`;
  - total unified rows: **520**;
- no bulk force-link of the 210 unresolved maps;
- normal player area scan now carries current game building geometry when shared knowledge is enabled;
- server accepts a historical website match only for exactly one normalized city + proven historical Y:X → canonical X:Y candidate;
- website point → canonical `building_id` matching uses strict point-in-polygon against the current game geometry;
- safely matched historical room knowledge is imported as `hk_maps_import`;
- W5 priority remains `game_live > hk_maps_import`;
- a failed/ambiguous historical hydration cannot fail the primary game map submission.

Userscript:
- new scanner marker: `maps-shared-runtime-20260921-r7-safe5`;
- shared runtime marker: `maps-shared-knowledge-20260921-r1`;
- new setting: **Использовать общую базу карт**;
- default: **ON**;
- before direct game reads the script loads shared canonical knowledge for owned/selected areas;
- active buildings with already-known non-NULL room counts are removed from the direct read queue;
- only still-unknown active buildings are queried from the game;
- original safe active-building intersection remains intact;
- max direct read concurrency remains **5**.

Build verification:
- run `35521561010`, job `106106419454`: PASS;
- unified cabinet dedupe: PASS;
- legacy website auto-hydration: PASS;
- shared preload filter: PASS;
- safe active intersection: PASS;
- game-live priority: PASS.

Live deployment:
- initial run `35521677077` installed both verified candidates and restarted the service;
- that run then failed only in its nested shell SHA assertion because `$1` was expanded under `set -u`;
- no second deployment was performed;
- post-deploy verification run `35521752892`, rerun job `106107338994`: **PASS**.

Current live SHAs:
- server: `f8b10a30a42d7dbb19ea11ee746eaccd89704a70ddb577631bf72c6ecca26df3`;
- userscript: `46c6b95688a589e7d4b02a10403c9bd32c5012a8e92b6e0e768364aad54d55b5`.

Production verification immediately after deployment:
- `hk_maps_catalog=235`;
- `hk_map_points=235`;
- `hk_map_area_links=25`;
- `hk_map_point_links=2007`;
- `map_areas=310`;
- `map_buildings=167690`;
- production test rows: **0**.

Live Personal Cabinet unified UI: PASS after GitHub Pages deployment completed.

**Unified Maps Runtime U1 = PASS.**

Stop here until the next explicit user instruction.


### Full235 archive import V2 — resolver ready (2026-09-21)

Purpose: replace the conservative 25/210 bridge with a complete, building-ID-driven import of the original 235-map HK Maps archive.

Verified source archive characteristics:
- format: `HK Maps Full Export`, version 3;
- maps: **235/235**;
- export errors: **0**;
- full game buildings: **152,593**;
- building IDs are unique across archive maps;
- source contains exact building IDs and room/investment knowledge.

Building-ID fingerprint dry-run:
- evidence: `audit/hk-stage2-full235-fingerprint-dryrun.json`;
- summary: `audit/hk-stage2-full235-fingerprint-summary.txt`;
- **160** maps match one existing canonical area by exact building IDs;
- **75** maps have zero overlap with current canonical buildings;
- existing website links that were present all agreed with the building-ID resolver.

Safe 160 live linking:
- run `35550161783`: PASS;
- evidence: `audit/hk-stage2-full235-link160-live-status.txt`;
- safe maps linked: **160**;
- new links from that operation: **134**;
- map areas/buildings unchanged;
- idempotent rerun: PASS.

Original UUID recovery for the 75 no-overlap maps:
- mapping: `deploy/maps/full235-nooverlap-area-ids.json`;
- all **75** original area UUIDs recovered;
- read-only validation run `35550447698`: PASS;
- at latest V2 safety check:
  - existing areas among these UUIDs: **0**;
  - aliases: **0**;
  - links: **0**;
  - conflicts: **0**.

Full235 importer V1:
- manager-only importer is live in Personal Cabinet;
- server supports staged dry-run and apply;
- archive is decompressed in the browser;
- only compact building knowledge is sent to the server;
- apply requires explicit `IMPORT_235` confirmation;
- DB backup occurs before apply;
- `game_live > hk_maps_import`;
- staged private building rows are purged after successful apply;
- archive has **not** been applied yet.

V2 improvement:
- marker: `HK_FULL235_ORIGINAL75_V2`;
- patch: `deploy/topking/patch_server_full235_original75_v2.py`;
- the 75 no-overlap maps now resolve to their **real original UUIDs**, not synthetic `hkfull…` IDs;
- V2 blocks apply if an original UUID appears with conflicting non-overlapping canonical buildings;
- safe statuses include `new_original` and `matched_original_id_empty`.

V2 regression:
- run `35551797290`, job `106187778861`: PASS;
- matched existing 160: PASS;
- create 75 using original UUIDs: PASS;
- re-import creates 0 new areas: PASS;
- production writes during regression: **NO**.

V2 live deploy:
- run `35551905146`, job `106188066312`: PASS;
- current V2 server SHA: `19839098c3db0246d87b72931381320378e46d0ed6d09b6cf2db2110530448db`;
- live status: `audit/hk-stage2-full235-original75-v2-live-status.txt`;
- archive applied: **NO**;
- production data changed by V2 deploy: **NO**;
- live state at deploy:
  - `hk_maps_catalog=235`;
  - `hk_map_points=235`;
  - `hk_map_area_links=160`;
  - `hk_map_point_links=2016`;
  - `map_areas=310`;
  - `map_buildings=167690`;
- 75 original UUIDs remain free/conflict-free.

Next gate:
1. In Personal Cabinet → Maps, select local `hk_maps_235_full.json.gz`.
2. Run **Проверить 235 карт** only.
3. Expected safe dry-run target:
   - 235 maps received;
   - 152,593 unique source buildings;
   - existing/linked ≈160;
   - `new_original=75`;
   - no ambiguous/conflict statuses;
   - original UUIDs 75/75;
   - `ready_to_apply=true`.
4. Do **not** press Apply until the dry-run result is reviewed.
5. If dry-run PASS, apply once, verify all 235 are combined, source priority, DB counts and idempotency.

**Current state: resolver V2 PASS; waiting only for local archive dry-run.**


### Execution rule for W1–W8

Work in short sessions.
After each stage:

1. write audit evidence;
2. update this checkpoint;
3. stop and report PASS/FAIL;
4. do not continue to the next stage automatically unless explicitly requested.

No bulk migration, schema mutation, or live deploy is allowed during W1.

### HK loader core-alignment hotfix — PASS (2026-09-21)

User live test before Buildings action exposed a launcher blocker:
- public `hk/loader.js` still expected `core-20260920-r6`;
- production userscript `1.17.12` uses `core-20260921-r14-auth-bridge-xhr`;
- the loader therefore rejected the current core after loading it.

Fix:
- loader revision: `loader-20260921-r10`;
- expected core aligned to `core-20260921-r14-auth-bridge-xhr`;
- stale hardcoded `r6` success label removed;
- userscript/game modules unchanged.

Verification:
- GitHub Pages deploy run `35564240938`: PASS;
- public loader verification run `35564300896`: PASS;
- old expected core r6 absent from public loader: PASS.

Stage 2 remains at:
**Buildings 2.06 — TECHNICAL_REVALIDATION_PASS_USER_ACTION_PENDING**.

### Late native login handoff — PASS (2026-09-21)

Live screenshot exposed a second launcher/startup blocker after the loader-core mismatch was fixed:
- current core loaded successfully but remained at `stage=BOOT`;
- root cause: bookmarklet/loader can start after the native game already completed its first authenticated `/player/me`;
- passive observer therefore missed that already-completed request and the UI gate could wait forever.

Fix in userscript `1.17.13`:
- core `core-20260921-r15-late-login-handoff`;
- normal passive path is unchanged;
- when HK starts late, it first requires evidence that native game auth already exists;
- then it may perform one read-only `/player/me` to recover missed player state;
- userscript still never owns or calls `/auth/create`;
- startup stage now reports `WAIT_NATIVE_LOGIN` / `LATE_HANDOFF` instead of remaining misleadingly at `BOOT`.

Verification:
- userscript deploy run `35564549471`: PASS;
- public loader core-r15 verification run `35564622707`: PASS;
- Buildings revalidation run `35564647224`: PASS;
- public E2E run `35564651904`: PASS;
- Maps/Explore protected invariants: PASS;
- passive auth-create safety: PASS.

Stage 2 remains at:
**Buildings 2.06 — TECHNICAL_REVALIDATION_PASS_USER_ACTION_PENDING**.

### Buildings UI r2 — live candidate (2026-09-21)

User screenshot confirmed the Buildings page was functionally present but visually broken:
- per-row Read button expanded to full width;
- UUID text collapsed into a one-character-wide column;
- active-building list became excessively tall.

Delivered in userscript `1.17.14`:
- compact Buildings-only layout;
- stable one-line UUID display;
- compact per-row Read button;
- structured settings / plan / active-building sections;
- responsive mobile layout;
- action logic unchanged.

Verification:
- predeploy `35565025652`: PASS;
- live deploy `35565072034`: PASS;
- Buildings verification `35565201926`: PASS;
- public E2E `35565212100`: PASS;
- Maps/Explore/auth protected invariants: PASS.

Current Stage 2 gate:
**Buildings 2.06 — UI_R2_LIVE_CANDIDATE_USER_VISUAL_AND_ACTION_CHECK_PENDING**.

### Buildings UI r3 — active list removed (2026-09-21)

User requested a simpler Buildings page with no full list of already-active buildings.

Delivered:
- userscript `1.17.15`;
- core `core-20260921-r17-buildings-ui-compact`;
- full Active buildings list removed;
- per-active-building Read buttons removed from this page;
- active slot count retained in Opening plan;
- candidate list retained;
- Buildings action logic unchanged.

Verification:
- predeploy `35565570357`: PASS;
- deploy `35565665494`: PASS;
- loader verification `35565756294`: PASS;
- Buildings verification `35565811595`: PASS;
- public E2E `35565773961`: PASS;
- Maps/Explore/auth protected invariants: PASS.

Current Stage 2 gate:
**Buildings 2.06 — UI_R3_LIVE_CANDIDATE_USER_VISUAL_AND_ACTION_CHECK_PENDING**.

### Buildings active-slot semantics r1 — PASS technical / user action pending (2026-09-21)

User live check exposed contradictory Buildings behavior:
- plan: 92 candidates;
- displayed active count: 2175/698;
- run: “no eligible unopened buildings”.

Read-only live schema diagnostics established the cause:
- `buildings` includes **2175 known records**;
- game reports **467 active buildings**;
- max active buildings: **698**;
- exactly **467** rows carry the current active-row signal `next_tier_level`;
- old code incorrectly counted all known records as active and calculated zero free slots.

Delivered in userscript `1.17.16`:
- core `core-20260921-r18-buildings-active-fix`;
- marker `buildings-active-semantics-20260921-r1`;
- active count now uses `player_active_building`;
- active ID filtering is cross-checked against the authoritative count;
- free capacity now derives from real active/max values;
- “no candidates” and “no free active slots” are distinct outcomes.

Verification:
- schema diagnostic `35567254035`: PASS;
- refined active-row diagnostic `35567342973`: PASS;
- predeploy fixture `35567569494`: PASS — 2175 known / 467 active / 698 max / 231 free;
- deploy `35567837973`: PASS;
- loader core-r18 `35567970830`: PASS;
- Buildings verifier `35567975463`: PASS;
- final public E2E retry `35568104811`: PASS;
- Maps/Explore/auth protected invariants: PASS.

Current Stage 2 gate:
**Buildings 2.06 — ACTIVE_SEMANTICS_R1_LIVE_CANDIDATE_USER_ACTION_CHECK_PENDING**.

Next user check:
1. reload game/HK;
2. calculate Buildings candidates;
3. verify the active/max count is no longer the all-known-record count;
4. run Open eligible;
5. perform one controlled open and recalculate;
6. confirm the opened building is no longer offered.

Do not advance Explore E4 before Buildings live action PASS and Explore E3 single-building PASS.

### Buildings open-limit + canonical runner — PASS technical / user action pending (2026-09-21)

User requested:
- apply the current visual canon to the Buildings runner panel;
- add an explicit number-of-buildings limit before mass opening.

Delivered in userscript `1.17.17`:
- Open limit: **1 / 10 / 15 / 20 / All available**;
- safe default: **1**;
- plan separates total candidates from **К запуску**;
- run confirmation displays the exact number selected;
- Buildings runner uses compact canonical styling and progress count;
- active-slot fix from 1.17.16 remains intact.

Verification:
- predeploy `35569077513`: PASS;
- deploy `35569168241`: PASS;
- loader core-r19 `35569276675`: PASS;
- Buildings verifier `35569279946`: PASS;
- public E2E `35569283445`: PASS;
- Maps/Explore/auth protected invariants: PASS.

Current Stage 2 gate:
**Buildings 2.06 — LIMIT_RUNNER_R1_LIVE_CANDIDATE_USER_ACTION_CHECK_PENDING**.

Next user check:
1. reload game/HK;
2. confirm limit selector and canonical runner;
3. keep limit at 1;
4. calculate candidates;
5. open exactly one building;
6. recalculate and confirm it disappears from candidates.

### Buildings owned/postcondition r1 — PASS technical / user action pending (2026-09-21)

User live action showed that the runner could say a building was opened while the account did not actually gain a new building, and favorite state was not being verified.

Root cause:
- the plan excluded only currently-active buildings;
- already-owned but inactive/max-tier buildings could be offered again;
- a successful HTTP response was treated as successful state mutation without checking `/player/me`.

Delivered in userscript `1.17.18`:
- candidates exclude all already-owned buildings;
- claim success requires authoritative postcondition confirmation;
- favorite success requires authoritative postcondition confirmation;
- false positive “opened” / “added to favorite” messages are no longer accepted;
- Favorites usage/max is visible in the plan;
- limit 1/10/15/20/all and canonical runner remain unchanged.

Verification:
- predeploy `35571939466`: PASS;
- deploy `35572226472`: PASS;
- loader core-r20 `35572447994`: PASS;
- Buildings verifier `35572452357`: PASS;
- public E2E `35572333927`: PASS;
- Maps/Explore/auth protected invariants: PASS.

Current Stage 2 gate:
**Buildings 2.06 — OWNED_POSTCONDITION_R1_LIVE_USER_ACTION_CHECK_PENDING**.

Next user check:
1. reload game/HK;
2. calculate candidates;
3. leave limit at 1;
4. open one candidate;
5. verify server-confirmed opening and, where eligible, confirmed favorite;
6. recalculate and verify the opened building is no longer offered.

### Buildings native-store sync r1 — PASS technical / user check pending (2026-09-21)

User live evidence showed server state had already changed correctly (active 468, favorite added), while the game map still showed the old ownership prompt. This isolated the remaining issue to native client-state synchronization rather than claim/favorite API logic.

Delivered in userscript `1.17.19`:
- Buildings waits for native game-state sync before runner completion;
- native player store is checked for newly-owned and newly-favorited buildings;
- if native sync cannot be proven, one automatic page reload is used as a safe fallback;
- no duplicate claim is sent during fallback.

Verification:
- read-only post-action diagnostic `35574950160`: PASS;
- predeploy `35575240613`: PASS;
- deploy `35575353091`: PASS;
- loader core-r21 `35575475749`: PASS;
- Buildings verifier `35575485583`: PASS;
- public E2E `35575493955`: PASS;
- Maps/Explore/auth protected invariants: PASS.

Current Stage 2 gate:
**Buildings 2.06 — NATIVE_SYNC_R1_LIVE_USER_CHECK_PENDING**.

Next:
1. reload game/HK;
2. limit 1;
3. open one candidate;
4. let native sync/fallback complete;
5. tap that building and confirm the stale “Исследовать это здание?” ownership prompt is gone.

### Buildings 2.06 — LIVE PASS / Explore E3 resumed (2026-09-21)

User confirmed the final Buildings native-sync check after userscript `1.17.19`:
- server state persisted;
- the game map recognized the claimed building after refresh;
- the stale ownership prompt was gone.

Therefore:
**Buildings / Здания 2.06 = LIVE PASS**

Stage 2 now resumes at:
**Explore / Исследование — E3 r9 single-building live validation**

E4 multi-building remains blocked until the E3 single-building path receives user PASS.

### Explore E3 r9 — current-production revalidation PASS (2026-09-21)

With Buildings 2.06 closed as LIVE PASS, the existing Explore E3 one-building runner was revalidated against userscript `1.17.19`.

Run `35576298312`: **PASS**
- one-building scope: PASS;
- shared mutation gate/no blind retry: PASS;
- authoritative reconciliation: PASS;
- fast completion/battles/remort/Instant MAX paths: PASS;
- staged runner UI: PASS;
- 15-second completion visibility: PASS;
- E4 absent: PASS;
- Buildings/Maps/auth protections preserved: PASS.

Current Stage 2 gate:
**Explore 2.07 — E3_R9_SINGLE_BUILDING_LIVE_TEST_PENDING**.

### Explore E3 — LIVE PASS + speed r1 deployed (2026-09-21)

User confirmed the E3 single-building action and staged runner work correctly.

Functional gate:
**Explore E3 = LIVE PASS**

Timing refinement in userscript `1.17.20`:
- action delay: 0.7–2.0 s;
- battle delay: 0.7 s;
- old standard 1/3/1 profile migrates automatically;
- safety/reconciliation/action mechanics unchanged;
- E4 still not enabled.

Verification:
- predeploy `35576826016`: PASS;
- deploy `35576921480`: PASS;
- Explore current verifier `35577054251`: PASS;
- loader core-r22 `35577128071`: PASS;
- public E2E `35577067567`: PASS.

Current Stage 2 gate:
**Explore 2.07 — E3_SPEED_R1_LIVE_USER_FEEL_CHECK_PENDING**.

Once the user confirms the new pace feels right, E3 can be closed and the next checkpoint can move to E4.

### Explore E4 queue r1 — technical PASS / user multi-building check pending (2026-09-21)

User asked to continue after the E3 speed refinement, so E3 remains LIVE PASS and Stage 2 advanced to E4.

Delivered in userscript `1.17.21`:
- E4 queue limit: **1 / 5 / 10 / 15 / 20 / All selected**;
- safe default: **1**;
- sequential processing only;
- each queue item reuses the validated E3 building core;
- authoritative reconciliation after every building;
- resource exhaustion/error stops the queue;
- skipped building may be recorded and queue may continue;
- overall progress `N/M`;
- same staged runner UI, Pause and Stop.

Verification:
- predeploy `35577683410`: PASS;
- deploy `35577789532`: PASS;
- loader core-r23 `35577988627`: PASS;
- Explore current verifier `35577999810`: PASS;
- public E2E `35578012994`: PASS;
- Buildings/Maps/auth protected invariants: PASS.

Current Stage 2 gate:
**Explore 2.07 — E4_QUEUE_R1_TECHNICAL_PASS_USER_MULTI_BUILDING_CHECK_PENDING**.

Next user live test:
1. reload game/HK;
2. calculate Explore plan;
3. set E4 limit to 5;
4. launch E4;
5. confirm sequential 1/5 → 5/5 processing and correct final plan refresh.

### Explore queue — LIVE PASS / production UI cleanup r1 (2026-09-21)

User confirmed the multi-building queue works correctly in live use.

Functional status:
**Explore E4 multi-building = LIVE PASS**

Production UI cleanup in userscript `1.17.22`:
- removed the E3 test button from normal UI;
- removed the duplicate E4 run-limit selector;
- **Maximum buildings** is now the only queue-size limit;
- normal actions reduced to **Calculate plan** and **Run**;
- queue mechanics and E3 core are unchanged.

Verification:
- predeploy `35579236728`: PASS;
- deploy `35579341358`: PASS;
- loader core-r24 `35579489161`: PASS;
- Explore verifier `35579499230`: PASS;
- public E2E `35579510611`: PASS.

Current Stage 2 gate:
**Explore 2.07 — PRODUCTION_UI_R1_TECHNICAL_PASS_USER_VISUAL_CHECK_PENDING**.

After the user confirms the cleaned UI, Explore can be closed and Stage 2 advances to **Businesses / Бизнесы**.

### Explore 2.07 — LIVE PASS / Businesses 2.08 started (2026-09-21)

User confirmed the cleaned Explore production UI is correct.

Therefore:
**Explore / Исследование 2.07 = LIVE PASS**

Stage 2 advances to:
**Businesses / Бизнесы 2.08**

Initial Businesses source preflight:
- current production rearrangement/optimizer code remains present and is not to be removed;
- pinned Kokkaras donor contains a separate Businesses catalog/planner layer that is absent from current production;
- canonical transfer gap is confirmed before any Businesses production mutation.

Current Businesses status:
**CANONICAL_TRANSFER_GAP_CONFIRMED**

### Businesses catalog r1 — live candidate (2026-09-21)

First Businesses donor-transfer slice is live in userscript `1.17.23`.

Scope:
- read-only catalog;
- search + bonus filters;
- owned/active/limit information;
- target quantity + missing calculation;
- upgrade-capacity summary;
- known recipe routes.

No catalog mutation actions are enabled yet.

Verification:
- source preflight `35580260242`: PASS;
- predeploy `35580823075`: PASS;
- deploy `35580937013`: PASS;
- loader core-r25 `35581115286`: PASS;
- Businesses current-live `35581126441`: PASS;
- public E2E `35581138549`: PASS.

Current Stage 2 gate:
**Businesses 2.08 — CATALOG_R1_LIVE_CANDIDATE_USER_UI_CHECK_PENDING**.



### Businesses rearrangement guard r1 — 1.17.24 live candidate (2026-09-21)

User feedback on the current Businesses rearrangement screen was applied as a focused Stage 2.08 correction, while the Kokkaras donor remains authoritative.

Delivered:
- desktop: existing remove side on the left, insert side on the right;
- mobile: stacked layout preserved;
- full user-driven removal protection for T4/T5/T6;
- manual remove selector limited to T1–T3;
- optimizer remove tiers limited to T1–T3;
- stale preset selections sanitized;
- original-layout restore blocked when it would remove T4–T6;
- runtime plan guard prevents stale plans from removing T4–T6;
- rollback transaction safety preserved.

Live:
- userscript `1.17.24`;
- core `core-20260921-r26-businesses-rearrange-guard`;
- deploy/public round-trip `35590711750`: PASS;
- Businesses current-live `35590863403`: PASS;
- loader core-r26 `35590914106`: PASS;
- public E2E `35590987942`: PASS.

Stage 2.08 remains at the live UI gate:
**CATALOG_R1_LIVE_CANDIDATE_USER_UI_CHECK_PENDING · REARRANGE_UI_GUARD_R1_LIVE_CANDIDATE_USER_VISUAL_CHECK_PENDING**

No catalog mutation actions are enabled yet.


### Businesses runner visual canon r1 — PASS (2026-09-21)

User screenshot identified that **Перестановка бизнесов** was still using the generic shared Runner appearance with full-width Pause/Stop buttons.

Applied as a same-version Stage 2.08 hotfix:
- userscript `1.17.24`;
- core `core-20260921-r27-businesses-runner-canon`;
- Businesses runner now uses the established compact Buildings runner visual canon;
- desktop actions are compact/right-aligned;
- mobile two-action layout preserved;
- no business logic changes.

Verification:
- deploy `35596167960`: PASS;
- loader `35596327521`: PASS;
- Businesses live `35596331997`: PASS;
- public E2E `35596336047`: PASS.

Stage 2.08 remains open for further user UI comments.


### Businesses completion hotfix r1 — live (2026-09-21)

User live evidence exposed a slow finalization tail after a large business rearrangement.

Cause:
- after all visible insert/activate actions, the script performed a separate `/player/me` final verification for every inserted slot;
- on large plans this left Runner near 100% in **Выполняется** for a long time.

Fixed in userscript `1.17.24`:
- core `core-20260921-r28-businesses-finalize`;
- one authoritative final snapshot validates all inserted businesses;
- targeted rereads only for unresolved slots;
- progress reaches the final step immediately after all mutation rows are processed;
- explicit **Проверяю результат** stage;
- confirmed success shows **Перестановка завершена**;
- done state remains visible for 6 seconds.

Verification:
- deploy/public round-trip `35596770570`: PASS;
- Businesses live verifier `35596934604`: PASS;
- public E2E `35596856911`: PASS.

Stage 2.08 remains open for user live recheck and further comments.


### Businesses completion loader compatibility final (2026-09-21)

The completion hotfix itself is unchanged, but its core identifier is pinned back to the already-public loader contract:
- userscript: `1.17.24`;
- core: `core-20260921-r27-businesses-runner-canon`;
- finalization marker: `businesses-finalize-single-snapshot-20260921-r1`.

Reason:
GitHub Pages publication of a new loader revision was queued. Keeping the hotfix on the already-public `loader-20260921-r24 → core r27` contract avoids any temporary launcher mismatch while preserving the new finalization behavior.

Final verification:
- loader compatibility deploy `35597317859`: PASS;
- public loader verification `35597375147`: PASS;
- Businesses current-live `35597379988`: PASS;
- public E2E `35597399052`: PASS.

Current behavior:
- no per-slot O(N) final reread tail;
- one authoritative final snapshot;
- targeted recovery only for unresolved slots;
- progress reaches 100% after mutation rows;
- successful Runner shows **Перестановка завершена** for 6 seconds.


## Maps regression hotfix

- Maps auto-research regression hotfix 1.17.38: TECHNICAL LIVE PASS; user check pending.
- Opening Maps is read-only; full district scan is manual-only via scan button.


## Treasure Map guide capture

- Treasure Map guide capture 1.17.39: TECHNICAL LIVE PASS; passive-only event/API/DOM/asset collector; guide population pending captured event data.


## Stage 2.12 Hamsters candidate

- current live userscript: **1.17.40**;
- candidate: **1.17.40**;
- marker: `hamsters-kokkaras-cost-parity-20260923-r1`;
- source preflight against pinned Kokkaras donor: PASS;
- donor order Copy Priority → Rarity → Levels: preserved;
- Nuts budget and `nutsPercent`: preserved;
- safe additional non-premium/non-hard cost components: restored to donor parity;
- premium/hard safety block: preserved;
- static CI run `35812191033`: PASS;
- destructive/gameplay CI mutations: NONE;
- production deploy: PASS;
- user browser/live check: PENDING.


## Hamsters Kokkaras live-state 1.17.41

- `hamsters-kokkaras-live-state-20260923-r2`: TECHNICAL LIVE PASS; user browser check pending.
- Hamsters Runner vertical layout restored.
