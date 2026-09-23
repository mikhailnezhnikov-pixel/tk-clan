# Hamster King Mobile 1.17.75 — runtime smoke execution checklist

Baseline:
- version: 1.17.75
- observability: runtime-smoke-observability-20260923-r1
- session persistence: runtime-smoke-session-20260923-r1
- game-request delta from diagnostics: NONE
- smoke events survive reload of the current tab via sessionStorage

## 1. Rat Hunt

Use the smallest safe available plan, preferably FREE.

Expected event family:
- runtime-smoke-rat-hunt-state
  - rat-hunt:start or rat-hunt:change-preset when applicable
  - rat-hunt:battle
  - rat-hunt:respawn only if needed
  - rat-hunt:finish when auto-finish is enabled
- runtime-smoke-rat-hunt-complete

Failure event:
- runtime-smoke-rat-hunt-error

PASS conditions:
- confirmation matches the selected preset/rounds/resources
- authoritative preflight succeeds
- first mutation returns a usable pit_generals state
- level/health updates after battle
- no duplicate start/battle mutation
- final authoritative refresh agrees with the visible game state

## 2. War

Use one FREE attack if available. Do not select a premium refill for the first smoke.

Expected event family:
- runtime-smoke-war-state
  - war-combat:fight
  - war-combat:buy-pass only when explicitly testing premium refill later
- runtime-smoke-war-complete

Failure event:
- runtime-smoke-war-error

PASS conditions:
- active war remains the same after preflight
- free-pass parity check succeeds
- opponent list returns exactly the expected live set
- weakest opponent is recalculated before attack
- fight response contains/applyies alliance_attack_war or compatible merged state
- defense HP/state changes are visible once, without duplicate attack

## 3. Neighborhood Battles

Select one unfinished Neighborhood for the first smoke.

Expected event family:
- runtime-smoke-neighborhood-state
  - neighborhood:view
  - neighborhood:run-preflight
  - neighborhood:/idler/claim, /idler/update, /idler/level, /idler/tap as applicable
- runtime-smoke-neighborhood-complete

Important anomaly:
- runtime-smoke-neighborhood-shape-miss

Failure event:
- runtime-smoke-neighborhood-error

PASS conditions:
- first /idler/view returns enemies and live idler state
- second /idler/view immediately before runner start succeeds
- tap power is non-zero
- claim/update/level/tap responses contain a usable idler shape
- 409 recovery does not loop
- 429/5xx handling does not duplicate mutation
- level/health progression matches the visible game

## Report collection

After running the three smoke tests, use the existing Diagnostics button in the HK panel and export one JSON report.

The report includes:
- runtimeSmoke revision/session metadata
- persisted runtime-smoke-* events from this tab
- runner state
- state-store summary
- bridge summary
- health/auth metadata with bearer/JWT redaction

Do not classify a module as runtime PASS until its real-game event sequence is present in the report.
