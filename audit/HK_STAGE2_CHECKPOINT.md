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
- current module: Pits / Ямы
- current module file: audit/hk-stage2-02-pits.md
- current module status: RESPAWN_RETEST_PENDING
- next module after LIVE PASS: Bosses / Боссы
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
