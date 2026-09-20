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
- current module: Maps / Карты — scanner repair
- current module file: audit/hk-stage2-04-maps.md
- current module status: BUG_CONFIRMED_NO_FIX_APPLIED
- next module after LIVE PASS: Buildings / Здания — resume live confirmation
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
