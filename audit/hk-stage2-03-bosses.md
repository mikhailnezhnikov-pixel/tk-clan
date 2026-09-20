# HK Stage 2.03 — Bosses / Боссы

## Status

**CANONICAL_TRANSFER_GAP_CONFIRMED**

## Baseline

Stage 2.02 Pits: LIVE PASS.

Current Bosses baseline marker:
`HK_STAGE2J_BOSSES_REV = 'bosses-readonly-20260920-r1'`

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
