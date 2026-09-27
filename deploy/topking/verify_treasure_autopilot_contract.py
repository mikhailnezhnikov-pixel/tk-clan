from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

def require(marker,label=None):
    if marker not in s:
        raise SystemExit(f"missing contract marker: {label or marker}")

def section(start,end):
    a=s.find(start)
    if a<0:
        raise SystemExit(f"missing section start: {start}")
    b=s.find(end,a+len(start))
    if b<0:
        raise SystemExit(f"missing section end: {end}")
    return s[a:b]

# These are not just historical revision tags. They define the behaviours that
# future Treasure Map releases are not allowed to silently remove.
required_markers=[
    "treasure-auto-map-orchestrator-20260926-r1",
    "treasure-auto-map-stability-20260926-r2",
    "treasure-auto-map-session-20260926-r3",
    "treasure-auto-map-start-lock-20260926-r4",
    "treasure-auto-map-active-priority-20260926-r5",
    "treasure-auto-map-foreground-handoff-20260926-r6",
    "treasure-auto-map-foreground-truth-20260926-r7",
    "treasure-chest-element-state-20260927-r1",
    "treasure-auto-map-stale-runner-20260927-r2",
    "treasure-chest-map-foreground-guard-20260927-r1",
    "treasure-location-modal-root-20260927-r1",
    "treasury-left-path-exit-recovery-20260927-r1",
    "lights-map-return-after-main-reward-20260927-r1",
    "lights-completed-dom-return-20260927-r2",
    "lights-modal-confirm-20260926-r2",
]
for marker in required_markers:
    require(marker)

# Chest false-positive protection: map cards win over chest-like DOM.
chest_elements=section("function treasureChestElements()","function treasureChestSignature()")
require("closest?.('[data-lot-id^=\"mf_treasurelot_active_sl\"]')","map-card chest descendant exclusion")
signature=section("function getSignature()","function checkPuzzle()")
if "if (treasureChestBlockedByForegroundMap(chestRows)) return 'NONE';" not in signature:
    raise SystemExit("contract broken: foreground map must suppress CHESTS signature")

# Location entry modal: the actual centered action dialog must be preferred.
modal_root=section("function treasureCenteredModalRoot()","function treasureActionButton")
for marker in [
    "document.elementFromPoint?.(vw/2,vh/2)",
    "if (!cost)",
    "if (centered) return centered;",
]:
    if marker not in modal_root:
        raise SystemExit(f"contract broken: location modal root lost {marker}")
tap_confirm=section("async function autoMapTapAndConfirm","async function autoMapDismissReward")
if "treasure-location-modal-action-recovered" not in tap_confirm:
    raise SystemExit("contract broken: location modal action recovery missing")

# Stale child runners must be cancellable when the real map is foreground.
stale=section("function autoMapCancelStaleRunners","function autoMapCaptureModes")
for marker in [
    "battleAutoRunId+=1",
    "chestAutoRunId+=1",
    "lightsAutoRunId+=1",
    "fishingAutoRunId+=1",
    "traderAutoRunId+=1",
]:
    if marker not in stale:
        raise SystemExit(f"contract broken: stale runner cancellation missing {marker}")

# A leave-confirm modal always outranks route selection.
tick=section("async function runAutoMapTick","function setAutoMapEnabled")
if "autoMapRecoverOpenLeaveModal('tick-preflight')" not in tick:
    raise SystemExit("contract broken: leave-modal preflight recovery missing")

# Active map cells must be handled before the persistent New Journey button.
active_pos=tick.find("const activeCount=autoMapActiveCellCount();")
journey_pos=tick.find("autoMapJourneyButton())")
if active_pos<0 or journey_pos<0 or active_pos>=journey_pos:
    raise SystemExit("contract broken: active route cells must outrank New Journey")

# Lights completed-room handoff must remain explicit.
for marker in [
    "autoMapReturnFromCompletedLights()",
    "lightsRoomCompleted()",
    "lights-map-return-complete",
]:
    if marker not in s:
        raise SystemExit(f"contract broken: lights completion handoff missing {marker}")

# From 1.18.47 onward AutoMap owns its child module toggles while inside a room.
if "treasure-automap-module-ownership-20260927-r1" in s:
    ownership=section("function autoMapEnsureOwnedModule","function autoMapCaptureModes")
    for marker in [
        "setLightsAutoEnabled(true)",
        "setChestAutoEnabled(true)",
        "setFishingAutoEnabled(true)",
        "setTraderAutoEnabled(true)",
    ]:
        if marker not in ownership:
            raise SystemExit(f"contract broken: AutoMap module ownership missing {marker}")

    fail_lights=section("function failLightsAuto","async function runLightsAuto")
    fatal=fail_lights[fail_lights.find("const fatalReasons"):fail_lights.find("if (autoMapOwnsLights")]
    if "stale-modal-blocking" in fatal or "modal-not-closed-after-change" in fatal:
        raise SystemExit("contract broken: recoverable lights UI failures became fatal again")


if "treasure-key-battle-handoff-20260928-r1" in s:
    key_helpers=section("function autoMapTreasureKeyModalRoot","async function autoMapWaitModal")
    for marker in [
        "Необычный ключ сокровищ",
        "Unusual treasure key",
        "quantity:10",
        "treasure-unusual-key-buy-10",
        "autoMapTreasureKeyModalRoot()",
        "autoMapTreasureKeyPurchaseButton(root)",
    ]:
        if marker not in key_helpers:
            raise SystemExit(f"treasure key purchase contract broken: {marker}")

    tick=section("async function runAutoMapTick","function setAutoMapEnabled")
    key_pos=tick.find("const keyModal=autoMapTreasureKeyModalRoot();")
    owner_pos=tick.find("const ownedSignature=getSignature();")
    if key_pos<0 or owner_pos<0 or key_pos>=owner_pos:
        raise SystemExit("treasure key modal must outrank child-module ownership")
    for marker in [
        "autoMapBuyTreasureKeyIfPresent()",
        "autoMapStatus('выкупаю ключ'",
        "cost:10",
    ]:
        if marker not in tick and marker not in key_helpers:
            raise SystemExit(f"treasure key AutoMap handoff broken: {marker}")

    check=section("function checkPuzzle()","function start()")
    if "autoMapTreasureKeyModalRoot()" not in check:
        raise SystemExit("treasure key overlay is not dispatched from puzzle loop")

print("TREASURE_AUTOPILOT_CONTRACT=PASS")
