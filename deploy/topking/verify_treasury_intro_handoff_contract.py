from pathlib import Path
import sys

s=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js").read_text(encoding="utf-8")

def section(start,end):
    a=s.find(start)
    if a<0: raise SystemExit("missing: "+start)
    b=s.find(end,a+len(start))
    if b<0: raise SystemExit("missing end: "+end)
    return s[a:b]

for marker in [
    "// @version      1.18.98",
    "const BUILD_VERSION = '1.18.98';",
    "treasury-intro-mobile-ack-20261001-r1",
    "treasury-battle-foreground-handoff-20261001-r1",
    "battle-open-modal-priority-20260930-r1",
    "trader-map-modal-approval-20260930-r1",
    "leave-modal-foreground-truth-20261001-r1",
    "exit-map-proof-20261001-r1"
]:
    if marker not in s: raise SystemExit("1.18.98 missing "+marker)

treasury=section("function autoMapTreasuryForeground()","function autoMapTreasuryCorridorModalRoot()")
for marker in [
    "function autoMapTreasuryForeground()",
    "if (battleScreenVisiblyCurrent()) return false;",
    "autoMapElementIsForeground",
    "function autoMapTreasuryIntroModalRoot()",
    "function autoMapTreasuryIntroAction(root)",
    "rect.top<rr.top+rr.height*0.55",
    "style.cursor==='pointer'",
    "getAttribute?.('aria-disabled')!=='true'",
    "function autoMapAcknowledgeTreasuryIntro(source='treasury-intro')",
    "await deviceNeutralActivate(",
    "const accepted=()=>!autoMapTreasuryIntroModalRoot();",
    "if (battlePointBelongsToElement(action,top))",
    "treasury-intro-action-missing",
    "treasury-intro-acknowledged"
]:
    if marker not in treasury: raise SystemExit("Treasury intro missing "+marker)

tick=section("async function runAutoMapTick(","function setAutoMapEnabled")
intro=tick.find("const treasuryForeground=autoMapTreasuryForeground();")
corridor=tick.find("const treasuryCorridorModal=autoMapTreasuryCorridorModalRoot();")
battle=tick.find("if (battleRecoverFinalRewardClaimed('automap-preflight'))")
if not (0<=intro<corridor<battle):
    raise SystemExit("Treasury intro must run before battle reward/exit preflight")
for marker in [
    "autoMapCancelStaleRunners('treasury-foreground-handoff')",
    "battleFinalRewardClaimed=false",
    "battleFinalRewardClaimedAt=0",
    "battleIntroGateUntil=0",
    "autoMapAcknowledgeTreasuryIntro('tick-preflight')"
]:
    if marker not in tick: raise SystemExit("Treasury handoff missing "+marker)

signature=section("function getSignature()","function checkPuzzle()")
treasury_pos=signature.find("if (autoMapTreasuryForeground()) return 'NONE';")
battle_pos=signature.find("battleRecoverFinalRewardClaimed('signature')")
if not (0<=treasury_pos<battle_pos):
    raise SystemExit("Stale battle chest can still outrank foreground Treasury")

battle_exit=section("async function autoMapRecoverCompletedBattleExit","function autoMapModalPrimaryButton")
for marker in [
    "const treasuryHandoff=()=>autoMapTreasuryForeground();",
    "battle-exit-treasury-handoff",
    "if (handoff()) return true;",
    "battle-complete-exit-retry"
]:
    if marker not in battle_exit: raise SystemExit("Battle exit handoff missing "+marker)

hud=section("function updateAutoMapToggle(","function ensureAutoMapToggle")
for marker in [
    "const treasuryIntro=autoMapTreasuryIntroModalRoot();",
    "const hudBottom=treasuryIntro?'auto':'202px';",
    "const hudTop=treasuryIntro?'85px':'auto';"
]:
    if marker not in hud: raise SystemExit("Treasury popup HUD obstruction regression")

mapproof=section("function autoMapReturnMapConfirmed()","function autoMapLeaveModalRoot")
if "if (autoMapTreasuryForeground()) return false;" not in mapproof:
    raise SystemExit("Treasury incorrectly accepted as returned Map")

check=section("function checkPuzzle()","function resumePuzzleAutomation")
if "runAutoMapTick('treasury-intro-overlay')" not in check:
    raise SystemExit("Treasury intro not polled on browser resume")

print("TREASURY_INTRO_HANDOFF_CONTRACT=PASS")
