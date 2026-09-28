from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count:
        raise SystemExit(f"{label}: expected {count} got {n}")
    s=s.replace(old,new,count)

rep(
    "// @version      1.18.74",
    "// @version      1.18.75\n"
    "// @release-note Рыбалка: исправлен преждевременный выход из локации при открытом окне покупки. Во время модалки счётчик забросов может исчезать из видимого DOM; это больше не трактуется как 0. Если слот был доступен до открытия окна, подтверждение покупки завершается, и только после закрытия окна/награды разрешён выход.",
    "version"
)
rep("const BUILD_VERSION = '1.18.74';","const BUILD_VERSION = '1.18.75';","build")

anchor="  const HK_TREASURE_RECORDER_UI_REMOVED_REV='treasure-recorder-ui-removed-20260928-r1';"
rep(
    anchor,
    anchor+"\n  const HK_FISHING_MODAL_BUDGET_REV='fishing-modal-budget-ownership-20260928-r1';",
    "fishing modal budget revision"
)

# Add modal-aware helpers next to fishing budget helpers.
anchor2="""    function fishingClosePurchaseModal(reason='no-casts') {
"""
helper="""    function fishingPurchaseModalOpen() {
      return !!treasureModalRoot(null);
    }

    function fishingAffordableInsideOpenModal(cost) {
      const quantity=Math.max(0,Number(cost?.quantity||0));
      if (!(quantity>0)) return false;
      const casts=fishingVisibleCasts();

      // The game hides the cast counter behind the purchase modal on some
      // layouts/devices. A null value here is UNKNOWN, not zero. The target was
      // already checked as affordable before the modal was opened.
      if (casts===null && fishingPurchaseModalOpen()) return true;
      return casts!==null && casts>=quantity;
    }

"""
if s.count(anchor2)!=1:
    raise SystemExit("fishingClosePurchaseModal anchor missing")
s=s.replace(anchor2,helper+anchor2,1)

# Never schedule room exit while a purchase/reward modal is still visible.
old_schedule="""    function fishingScheduleExit(reason='no-casts') {
      fishingRetryNotBefore=0;
      fishingFailureStreak=0;
      lastSignature='';
      recordDiagnostic('fishing-auto-exit-ready',{
        revision:HK_FISHING_ZERO_CAST_EXIT_REV,
        reason,
        casts:fishingVisibleCasts()
      });
      if (autoMapEnabled()) {
        setTimeout(()=>void runAutoMapTick('fishing-'+reason),minigameRandomMs(450,750));
      } else {
        setTimeout(checkPuzzle,minigameRandomMs(450,750));
      }
    }
"""
new_schedule="""    function fishingScheduleExit(reason='no-casts') {
      if (fishingPurchaseModalOpen()) {
        lastSignature='';
        recordDiagnostic('fishing-auto-exit-blocked-modal',{
          revision:HK_FISHING_MODAL_BUDGET_REV,
          reason,
          casts:fishingVisibleCasts()
        });
        setTimeout(checkPuzzle,120);
        return false;
      }

      fishingRetryNotBefore=0;
      fishingFailureStreak=0;
      lastSignature='';
      recordDiagnostic('fishing-auto-exit-ready',{
        revision:HK_FISHING_ZERO_CAST_EXIT_REV,
        reason,
        casts:fishingVisibleCasts()
      });
      if (autoMapEnabled()) {
        setTimeout(()=>void runAutoMapTick('fishing-'+reason),minigameRandomMs(450,750));
      } else {
        setTimeout(checkPuzzle,minigameRandomMs(450,750));
      }
      return true;
    }
"""
rep(old_schedule,new_schedule,"modal exit gate")

# If the target disappears only because its modal is covering the board, do not
# close that modal and do not treat the hidden cast counter as exhausted.
old_no_target="""        if (casts===null || casts<=0) {
          fishingClosePurchaseModal('budget-empty');
          fishingScheduleExit(casts===0?'zero-casts':'counter-gone');
        } else {
          lastSignature='';
          setTimeout(checkPuzzle,120);
        }
"""
new_no_target="""        if (casts===null && fishingPurchaseModalOpen()) {
          recordDiagnostic('fishing-auto-modal-owns-flow',{
            revision:HK_FISHING_MODAL_BUDGET_REV,
            phase:'budget-empty',
            casts
          });
          lastSignature='';
          setTimeout(checkPuzzle,120);
        } else if (casts===null || casts<=0) {
          fishingClosePurchaseModal('budget-empty');
          fishingScheduleExit(casts===0?'zero-casts':'counter-gone');
        } else {
          lastSignature='';
          setTimeout(checkPuzzle,120);
        }
"""
rep(old_no_target,new_no_target,"initial no-target modal ownership")

old_second="""      target=fishingTarget();
      if (!target) {
        const casts=fishingVisibleCasts();
        if (casts===null || casts<=0) {
          fishingClosePurchaseModal('post-scan-empty');
          fishingScheduleExit(casts===0?'zero-casts-post-scan':'counter-gone-post-scan');
        }
        return false;
      }
"""
new_second="""      target=fishingTarget();
      if (!target) {
        const casts=fishingVisibleCasts();
        if (casts===null && fishingPurchaseModalOpen()) {
          recordDiagnostic('fishing-auto-modal-owns-flow',{
            revision:HK_FISHING_MODAL_BUDGET_REV,
            phase:'post-scan',
            casts
          });
          lastSignature='';
          setTimeout(checkPuzzle,120);
        } else if (casts===null || casts<=0) {
          fishingClosePurchaseModal('post-scan-empty');
          fishingScheduleExit(casts===0?'zero-casts-post-scan':'counter-gone-post-scan');
        }
        return false;
      }
"""
rep(old_second,new_second,"post-scan modal ownership")

# Once the purchase modal is open, do not abort just because the underlying cast
# counter is hidden. Use the already-validated pre-open affordability.
rep(
    "            if (!fishingAffordable(target.cost)) return null;",
    "            if (!fishingAffordableInsideOpenModal(target.cost)) return null;",
    "modal action affordability"
)

old_insufficient="""        if (!fishingAffordable(target.cost)) {
          fishingClosePurchaseModal('insufficient-before-confirm');
          recordDiagnostic('fishing-auto-insufficient-before-confirm',{
            revision:HK_FISHING_ZERO_CAST_EXIT_REV,
            lotId:target.lotId,
            ...fishingBudgetSnapshot(target.cost)
          });
          const casts=fishingVisibleCasts();
          if (casts===null || casts<=0) {
            fishingScheduleExit(casts===0?'zero-casts-modal':'counter-gone-modal');
          }
          return false;
        }
"""
new_insufficient="""        if (!fishingAffordableInsideOpenModal(target.cost)) {
          fishingClosePurchaseModal('insufficient-before-confirm');
          recordDiagnostic('fishing-auto-insufficient-before-confirm',{
            revision:HK_FISHING_MODAL_BUDGET_REV,
            lotId:target.lotId,
            ...fishingBudgetSnapshot(target.cost)
          });
          const casts=fishingVisibleCasts();
          if (casts!==null && casts<=0) {
            fishingScheduleExit('zero-casts-modal');
          }
          return false;
        }
"""
rep(old_insufficient,new_insufficient,"modal confirm affordability")

# Export revision for diagnostics.
export_anchor="      treasureRecorderUiRemovedRevision:HK_TREASURE_RECORDER_UI_REMOVED_REV,"
if s.count(export_anchor)!=1:
    raise SystemExit("recorder export anchor missing")
s=s.replace(
    export_anchor,
    export_anchor+"\n      fishingModalBudgetRevision:HK_FISHING_MODAL_BUDGET_REV,",
    1
)

for marker in [
    "// @version      1.18.75",
    "const BUILD_VERSION = '1.18.75';",
    "fishing-modal-budget-ownership-20260928-r1",
    "function fishingPurchaseModalOpen()",
    "function fishingAffordableInsideOpenModal(cost)",
    "casts===null && fishingPurchaseModalOpen()",
    "fishing-auto-exit-blocked-modal",
    "fishing-auto-modal-owns-flow",
    "fishingAffordableInsideOpenModal(target.cost)",
    "fishingModalBudgetRevision:HK_FISHING_MODAL_BUDGET_REV",
    "purchase-confirm-fast-global-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

# Make sure the old false-negative modal checks are gone.
if "if (!fishingAffordable(target.cost)) return null;" in s:
    raise SystemExit("old modal affordability loop still present")

p.write_text(s,encoding="utf-8")
print("FISHING_MODAL_BUDGET_1_18_75=PASS")
