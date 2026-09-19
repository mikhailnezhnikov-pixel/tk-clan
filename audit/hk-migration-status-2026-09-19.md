# TopKing migration status — 2026-09-19

## Live baseline

Current confirmed userscript: **1.16.6**.

Confirmed migrated layers:

- Stage 1 `stage1-20260919-r4` — mutation gate, retry/deadlock protection, Growth guards.
- Stage 2A `stage2a-20260919-r1` — Pit + Fair on shared Runner.
- Stage 2B `stage2b-20260919-r1` — Shop + Recipes + Project Bureau on shared Runner.
- Stage 2C `stage2c-state-20260919-r1` — shared State Store for mutation responses + authoritative rereads.
- Stage 2D `stage2d-resource-business-20260919-r1` — Resource tasks + Business rearrangement.
- Stage 2E `stage2e-maps-20260919-r1` — district/map research.
- Stage 2F `stage2f-clan-20260919-r1` — Clan Skills scan.
- Stage 2G `stage2g-rumors-20260919-r1` — historical Rumors restored to Today.
- Rumors backend `stage2g-rumors-server-20260919-r1` — route DB/API/admin publisher restored.

Growth invariant remains:

- Hamsters: `cur_cap` only.
- Generals: `item_pit_token` only.

## Migration matrix

| Area | Current state | Source | Next migration action |
|---|---|---|---|
| Today / daily | Live | current userscript | Rumors restored in 1.16.6; later test actions in game |
| Growth / Hamsters | Live | current userscript | post-migration gameplay test only |
| Growth / Generals | Live | current userscript | post-migration gameplay test only |
| Resource buildings | Live | current userscript | gameplay test later |
| Buildings Event / resource events | Live through Resource module | current `/player/event` logic | gameplay test later |
| Business rearrangement | Live | current userscript | gameplay test later |
| Pit | Live | current userscript | gameplay test later |
| Fair | Live | current userscript | gameplay test later |
| Shop | Live | current userscript | gameplay test later |
| Recipes | Live | current userscript | gameplay test later |
| Project Bureau | Live | current userscript | gameplay test later |
| Districts / Maps | Live | current userscript | gameplay test later |
| Clan Skills | Live | current userscript | gameplay test later |
| Rumors | Live 1.16.6 | historical userscript 1.9.8 + removed 1.9.9 backend | gameplay test later |
| Wars | Collector already exists; UI was planned | current `readPublicWar()` + preserved 1.9.6 | Stage 2H: expose working read-only Wars page |
| Regional Boss | State fields/data capture exist; no full preserved action module confirmed | 1.13.x/current State Store | keep for post-migration implementation unless exact donor is found |
| Open / Explore Buildings | building study/data capture exists; no preserved action loop confirmed | 1.7.95/current map study data | keep for post-migration implementation unless exact donor is found |
| Rat Hunt | planned only; no preserved implementation confirmed | none found | post-migration new feature |
| Reminders | no preserved implementation confirmed | none found | post-migration new feature |
| Realtime / WebSocket | no preserved implementation in saved versions | none found | post-migration new feature |

## Migration rule

During this phase:

1. Preserve existing game API behavior and algorithms.
2. Transfer existing/historical modules before designing new mechanics.
3. Use the shared Runner/State Store where the transferred module mutates game state or runs a long loop.
4. Only require syntax/build/invariant checks before migration deploy.
5. Defer detailed gameplay edge-case testing until the migration list is complete.

## Immediate queue

1. Stage 2H Wars — expose the existing safe war collector as a working module.
2. Re-check repository/backups for exact donor implementations of Regional Boss and Open/Explore Buildings.
3. If no exact donor exists, mark them as post-migration features instead of inventing behavior during transfer.
4. Then move to Rat Hunt / Reminders / Realtime only after all transferable modules are exhausted.
