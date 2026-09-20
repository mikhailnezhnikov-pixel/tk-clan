# HK Stage 2.03 — Bosses / Боссы

## Status

**CANON_CORE_R1_LIVE_CANDIDATE**

## Baseline

Stage 2.02 Pits: LIVE PASS.

Current Bosses baseline marker:
`HK_STAGE2J_BOSSES_REV = 'bosses-canon-core-20260920-r1'`

## Source preflight

Pinned Kokkaras donor revalidated:
- `скрипт Kokkaras,.txt`
- canonical SHA256: `28c3104020ecb7f54d0d51a72d067404d0176bc069d59fcca417d66817d1fcf1`

Donor Bosses mechanics exist and are not represented by the current read-only implementation.

Bug ticket:
`audit/hk-stage2-bug-bosses-readonly-transfer-gap.md`

## Current baseline behavior

Present:
- Bosses navigation/module;
- `/player/me` read;
- read-only boss state rows;
- Boss Pit level/power summary;
- Refresh.

Missing versus donor:
- canonical Area/Regional selection UI;
- pass plans and live cost validation;
- action runner;
- active/resume;
- FREE/PREM/ITEM execution;
- restoration and decision flow;
- battle result/winrate logs;
- mutation/state-refresh chain;
- Area Boss target/reward planning;
- Area Boss calculator.

## Next block

Transfer canonical Bosses core only.
Do not touch Maps or later modules.
Do not mark LIVE PASS until:
`UI -> live read -> calculation -> action -> state update -> rerun`
is confirmed.


## Canonical core r1

Transferred from pinned donor into the existing HK runtime:
- Area + Regional Boss selection;
- live pass-plan construction and revalidation;
- FREE / PREM / ITEM execution;
- active battle resume;
- Area Boss endpoints: `/bosses/battle`, `/bosses/pass`, `/bosses/respawn`;
- Regional endpoints: `/regional_boss/battle_state`, `/regional_boss/battle`, `/player/regional_boss/pass`;
- Restoration Paws decision flow with per-run remembered additional budget;
- battle result / Regional runtime winrate logging;
- authoritative state reread after mutations;
- explicit Start-only mutation path through the existing mutation gate.

Integration fix:
- `/regional_boss/battle_state` added to the read-only POST whitelist so state reads do not enter the mutation gate.

Marker:
- `HK_STAGE2J_BOSSES_REV = 'bosses-canon-core-20260920-r1'`;
- `HK_BOSSES_CANON_REV='bosses-canon-core-20260920-r1'`.

Predeploy:
- exact input SHA: `c733c62a49c38ae6c497c03c89ee9ec018363bc8f75c2ec64e7e8f3990dfafdb`;
- Python compile: PASS;
- patch + core SHA verification: PASS;
- JS syntax: PASS;
- candidate SHA: `571d97f7aa2adf5d747f94275350abf0872f04a63bdaf795c9ec53aed2b393a9`.

Deploy/live verification:
- backup/deploy: PASS;
- service active: PASS;
- live SHA256: `571d97f7aa2adf5d747f94275350abf0872f04a63bdaf795c9ec53aed2b393a9`;
- public SHA256: `571d97f7aa2adf5d747f94275350abf0872f04a63bdaf795c9ec53aed2b393a9`;
- public byte equality: PASS;
- syntax: PASS.

Baseline sync:
- commit: `bac973abc67096f5642fce84ab1df8ba1a16883e` — PASS.

Current status:
**CANON_CORE_R1_LIVE_CANDIDATE**

Still missing versus donor before static Bosses parity:
- Area Boss tournament target / reward planning;
- reward-only continuation;
- Area Boss Calculator / rewards view.

Do not mark Bosses LIVE PASS yet.


## Area target / reward continuation r2

Transferred and deployed after canonical core r1:
- Area Boss tournament target planning;
- selectable target levels from donor target set;
- reward-only plan (`reward-0`);
- live target score/forecast calculation;
- future free-attempt / passive invitation forecast;
- current-run strategy handling;
- Area Boss reward continuation using available invitations;
- safe stop when invitation balance is insufficient;
- rerun/live score reread during continuation.

Markers:
- `HK_STAGE2J_BOSSES_REV = 'bosses-area-target-20260920-r2'`;
- `HK_BOSSES_CANON_REV='bosses-area-target-20260920-r2'`;
- `HK_BOSSES_TARGET_REV='bosses-area-target-20260920-r2'`.

Technical live verification:
- syntax: PASS;
- outer marker: PASS;
- inner canonical marker: R2;
- target marker: PASS;
- target plan: PASS;
- reward-only plan: PASS;
- public byte equality: PASS;
- live/public SHA256: `0e168e81ff6e4ee42400f99aaad8a4fb9359bcfbdc051d56c981d0adcbf247e7`.

Baseline sync:
- live candidate synchronized after r2;
- current baseline contains r2 markers and target continuation functions.

Current status:
**AREA_TARGET_R2_LIVE_CANDIDATE**

Still pending before Bosses LIVE PASS:
1. user live UI/action/state/rerun confirmation for canonical Area + Regional runner;
2. user live confirmation of Area target/reward continuation;
3. donor Area Boss Calculator / rewards view is still not transferred.

Do not advance to Maps yet.


## Final live confirmation — Stage 2.03 PASS

User confirmed the current Bosses implementation works correctly in live use.

Confirmed live:
- canonical Area Boss runner: PASS;
- canonical Regional Boss runner: PASS;
- FREE / PREM / ITEM execution: PASS;
- active battle resume: PASS;
- Restoration Paws / decision flow: PASS;
- resulting state refresh: PASS;
- rerun reads resulting state correctly: PASS;
- Area Boss target / reward continuation r2: PASS.

Scope decision:
- Area Boss Calculator / rewards view is intentionally **not part of the userscript module**;
- the calculator already exists on the website and must not be duplicated into HK;
- this item is therefore removed from the Bosses parity blocker list by explicit user decision.

Final Bosses revision:
- `HK_STAGE2J_BOSSES_REV = 'bosses-area-target-20260920-r2'`;
- `HK_BOSSES_CANON_REV='bosses-area-target-20260920-r2'`;
- `HK_BOSSES_TARGET_REV='bosses-area-target-20260920-r2'`;
- live/public SHA256: `0e168e81ff6e4ee42400f99aaad8a4fb9359bcfbdc051d56c981d0adcbf247e7`;
- no additional Bosses patch required.

Final status:
**LIVE PASS**

Stage 2.03 Bosses is closed. Next module: Stage 2.04 Maps / Карты.
