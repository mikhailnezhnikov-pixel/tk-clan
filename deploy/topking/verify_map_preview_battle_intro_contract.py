from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

required=[
  "// @version      1.18.85",
  "trader-gold-exact-purchase-modal-20260929-r1",
  "battle-intro-hard-gate-20260929-r1",
  "function traderForbiddenGoldModalRootLegacy()",
  "function traderForbiddenGoldModalRoot()",
  "row.exactTitle && row.purchaseText",
  "function battleIntroModalRootLegacy()",
  "function battleIntroModalRoot()",
  "function battleIntroTransitionLocked()",
  "battleIntroGateUntil=Date.now()+2600",
  "battle-intro-transition",
  "сражение → загружаю поле",
  "traderGoldExactModalRevision:HK_TRADER_GOLD_EXACT_MODAL_REV",
  "battleIntroHardGateRevision:HK_BATTLE_INTRO_HARD_GATE_REV",
]
for marker in required:
    if marker not in s:
        raise SystemExit("map-preview/battle-intro contract broken: "+marker)

# Strict gold modal detection must not use reward icon metadata or cur_gold.
start=s.find("function traderForbiddenGoldModalRoot()")
end=s.find("function traderForbiddenGoldCloseButton",start)
block=s[start:end]
if "querySelectorAll?.('img')" in block:
    raise SystemExit("gold modal detector still scans reward icons")
if "cur_gold" in block:
    raise SystemExit("gold modal detector still keys off cur_gold assets")
if "row.exactTitle && row.purchaseText" not in block:
    raise SystemExit("gold modal detector is not exact purchase-modal only")

# Hard intro gate must be evaluated before leave-modal recovery.
start=s.find("async function runAutoMapTick(source='loop')")
end=s.find("function setAutoMapEnabled",start)
block=s[start:end]
intro=block.find("const introHardGate=battleIntroModalRoot();")
leave=block.find("if (autoMapLeaveModalRoot())")
if intro<0 or leave<0 or intro>leave:
    raise SystemExit("battle intro gate does not outrank leave-modal recovery")

for marker in [
  "trader-gold-stale-modal-reset-20260929-r1",
  "trader-gold-currency-skip-20260928-r1",
  "battle-visible-point-truth-20260929-r1",
  "battle-full-fair-state-20260928-r1",
  "battle-egg-one-berry-buy-20260928-r1",
  "battle-strict-exit-gate-20260927-r1",
  "battle-reward-state-machine-20260928-r1",
  "clan-crest-transparent-mask-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("preserved behavior missing: "+marker)

print("MAP_PREVIEW_BATTLE_INTRO_CONTRACT=PASS")

# trigger build 1.18.85

# trigger after battle-state anchor fix
