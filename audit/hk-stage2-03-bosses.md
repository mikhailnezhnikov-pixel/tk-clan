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
