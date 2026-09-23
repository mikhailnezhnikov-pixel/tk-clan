# Hamster King Mobile 1.17.72 — runtime smoke readiness

Status: READY_FOR_RUNTIME_SMOKE (not runtime PASS)

Baseline:
- userscript version: 1.17.72
- deployed userscript commit: 37b247377947a777b779fe677d9547f27af3f326
- main inspected at: 043aa8c7a62e1460d3ebb4d98ca78b86a7fb8045
- Stage 7 marker: stage7-combat-confirm-20260923-r1
- post-deploy Treasure inspection commits do not modify the userscript combat flows

Rat Hunt:
- explicit confirmation before irreversible combat
- authoritative /player/me preflight
- live preset switch-cost verification
- live FREE / ITEM / PREM resource checks
- per-step start/pass validation
- respawn budget guard
- fresh authoritative read after completion/error
- runtime result: PENDING

War:
- explicit confirmation before irreversible combat
- authoritative /player/me preflight
- exact pass-balance parity check
- active war re-fetch before attacks
- attack-cost re-fetch before premium refill
- opponent list re-fetch before every attack
- weakest opponent recalculated before every attack
- fresh authoritative read after completion/error
- runtime result: PENDING

Neighborhood Battles:
- fresh /idler/view before plan formation
- explicit confirmation before irreversible combat
- second fresh /idler/view immediately before runner start
- claim/update/level/tap paths apply returned idler state
- 409/429/5xx handling is state-aware
- live tap power is read from refreshed idler state
- runtime result: PENDING

Required real-game smoke order:
1. Rat Hunt
2. War
3. Neighborhood Battles

PASS criteria for each module:
- module loads without UI/runtime exception
- read API returns expected shape
- confirmation matches the selected plan
- first safe mutation succeeds
- returned state is applied without stale UI
- stop/pause/error path does not duplicate mutation
- final refresh matches the game state
- no unexpected 429 burst or duplicate request loop

No functional code changes were made in this checkpoint because there is no reproducible runtime failure yet.
