from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

required=[
  "battle-full-fair-state-20260928-r1",
  "battle-egg-one-berry-buy-20260928-r1",
  "function battleFairState()",
  "fairState('fair_mini_game_fight',playerDocument)",
  "function battleFairSlots()",
  "source:'fair_mini_game_fight'",
  "function battleRawContextPresent()",
  "function battleEggOfferTarget()",
  "/^mf_fight_egg_/i",
  "item_treasurehunt_energy',quantity:1",
  "async function runBattleEggOffer(target)",
  "battle-egg-one-berry-card",
  "battle-egg-one-berry-confirm",
  "сражение → яйцо за 1 ягоду",
  "reason:'one-berry-egg-pending'",
  "async function battleEnsureElementForSlot(slot,runId)",
  "await battleEnsureElementForSlot(slot,runId)",
  "battleFullStateRevision:HK_BATTLE_FULL_STATE_REV",
  "battleEggBerryRevision:HK_BATTLE_EGG_BERRY_REV",
]
for marker in required:
    if marker not in s:
        raise SystemExit("battle full-state/egg contract broken: "+marker)

# Full board reading must no longer depend on visible enemy cards in getSignature.
for forbidden in [
  "const enemies = [...document.querySelectorAll('[data-lot-id*=\"mf_treasurelot_enemy_type_\"]')].filter(visible);"
]:
    if forbidden in s:
        raise SystemExit("viewport-dependent battle signature still present")

for marker in [
  "battle-viewport-scroll-resume-20260928-r1",
  "battle-automap-full-clear-20260927-r1",
  "battle-strict-exit-gate-20260927-r1",
  "battle-achievement-priority-20260927-r1",
  "battle-reward-state-machine-20260928-r1",
  "battle-overlay-safe-targeting-20260928-r1",
  "chest-visible-claim-priority-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("preserved marker missing: "+marker)

print("BATTLE_FULL_STATE_EGG_CONTRACT=PASS")
