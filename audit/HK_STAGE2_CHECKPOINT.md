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
- current module status: SOURCE_PREFLIGHT_PASS_IN_PROGRESS
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
