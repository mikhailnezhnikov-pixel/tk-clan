from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")
marker="lights-hint-canon-fixed-plan-map6-20260928-r1"

if marker not in s:
    print("TREASURE_LIGHTS_MAP6_CONTRACT=PASS legacy-source")
    raise SystemExit(0)

def section(start,end):
    a=s.find(start)
    if a<0:
        raise SystemExit(f"missing section start: {start}")
    b=s.find(end,a+len(start))
    if b<0:
        raise SystemExit(f"missing section end: {end}")
    return s[a:b]

modal=section("function lightsModalRoot()","async function waitLightsModal")
for token in [
    "titlePattern",
    'mf_fairlot_lights_out_sl',
    "Map #6 regression guard",
    "lights-strict-modal-root",
]:
    if token not in modal:
        raise SystemExit(f"map6 strict modal contract missing: {token}")
if "node.querySelector?.('[data-lot-id^=\"mf_fairlot_lights_out_sl\"]')" not in modal:
    raise SystemExit("map6 modal contract no longer excludes board ancestors")

cleanup=section("async function closeLightsModalAfterStateChange","async function runLightsModalStep")
if "dispatchBattleTapAt(" in cleanup:
    raise SystemExit("map6 regression: blind coordinate fallback returned to lamp cleanup")
for token in [
    "strict-dialog-has-no-safe-dismiss",
    "lights-close-after-change-",
]:
    if token not in cleanup:
        raise SystemExit(f"map6 safe cleanup missing: {token}")

runner=section("async function runLightsAuto()","function battleElementForSlot")
for token in [
    "reference/topking/lights-hint-only-canon-1.18.04.js",
    "const executedSlots=new Set()",
    "repeated-planned-slot",
    "canonical-plan-has-duplicates",
    "lightsTargetForSlot(slot)",
    "target-slot-mismatch",
    "executedSlots.add(slot)",
    "initial-modal-cannot-close",
]:
    if token not in runner:
        raise SystemExit(f"map6 canonical runner missing: {token}")
if "const target=board[position]?.element" in runner:
    raise SystemExit("map6 regression: runner reused mutable board DOM node")

if "source:'check-puzzle-activated-dom'" in s:
    raise SystemExit("reward regression: Activated is still treated as claimed")
if "reward-ack-still-visible" not in s:
    raise SystemExit("reward regression: acknowledgement is not verified before exit")
if "return lightsFinalRewardClaimed===true;" not in s:
    raise SystemExit("reward regression: lightsRoomCompleted is not strict")

# Canonical fixture from recorded map #6.
initial=[True,False,True,True,True,False,False,False,True]
def neighbours(p):
    row,col=divmod(p,3)
    out=[p]
    if row>0: out.append(p-3)
    if row<2: out.append(p+3)
    if col>0: out.append(p-1)
    if col<2: out.append(p+1)
    return out
def press(state,p):
    nxt=list(state)
    for q in neighbours(p):
        nxt[q]=not nxt[q]
    return nxt

best=None
for mask in range(1,512):
    state=list(initial)
    plan=[]
    for p0 in range(9):
        if mask & (1<<p0):
            plan.append(p0+1)
            state=press(state,p0)
    if all(state) and (best is None or len(plan)<len(best)):
        best=plan

if best != [1,3,4,5,6,7,8]:
    raise SystemExit(f"map6 canonical fixture changed: {best}")

print("TREASURE_LIGHTS_MAP6_CONTRACT=PASS")
