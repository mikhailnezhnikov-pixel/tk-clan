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

rep("// @version      1.18.29",
    "// @version      1.18.30\n// @release-note Рыбалка: при 0 забросов больше не открывает следующий слот. Обычный wallet полностью исключён из расчёта бюджета рыбалки — источник только реальный счётчик забросов. Если счётчик исчез после последней покупки или модалка уже открыта с недоступной кнопкой, окно закрывается и Автокарта штатно выходит из комнаты.",
    "version")
rep("const BUILD_VERSION = '1.18.29';",
    "const BUILD_VERSION = '1.18.30';",
    "build")
rep("  const HK_FISHING_HUMAN_FAST_REV='fishing-human-fast-20260927-r1';",
    "  const HK_FISHING_HUMAN_FAST_REV='fishing-human-fast-20260927-r1';\n  const HK_FISHING_ZERO_CAST_EXIT_REV='fishing-zero-cast-exit-20260927-r1';",
    "revision")

old_aff="""    function fishingAffordable(cost) {
      const quantity=Math.max(0,Number(cost?.quantity||0));
      if (!(quantity>0)) return false;

      const casts=fishingVisibleCasts();
      if (casts!==null) return casts>=quantity;

      const id=String(cost?.id||'');
      if (!id) return false;
      const amount=walletAmount(id);
      return amount!==null && Number(amount)>=quantity;
    }
"""
new_aff="""    function fishingAffordable(cost) {
      const quantity=Math.max(0,Number(cost?.quantity||0));
      if (!(quantity>0)) return false;

      // Fishing casts are NOT a normal wallet currency. When the last cast is
      // consumed the rod counter may disappear for a short time; treating that
      // as wallet fallback incorrectly re-opens another slot.
      const casts=fishingVisibleCasts();
      return casts!==null && casts>=quantity;
    }
"""
rep(old_aff,new_aff,"remove wallet fallback")

old_snap="""    function fishingBudgetSnapshot(cost) {
      const id=String(cost?.id||'');
      const amount=id ? walletAmount(id) : null;
      const casts=fishingVisibleCasts();
      return {
        id,
        balance:casts!==null ? casts : (amount===null ? null : Number(amount)),
        casts,
        source:casts!==null ? 'visible-rod' : (amount===null ? 'unknown' : 'wallet'),
        cost:Math.max(0,Number(cost?.quantity||0))
      };
    }
"""
new_snap="""    function fishingBudgetSnapshot(cost) {
      const id=String(cost?.id||'');
      const casts=fishingVisibleCasts();
      return {
        id,
        balance:casts,
        casts,
        source:casts!==null ? 'visible-rod' : 'no-cast-counter',
        cost:Math.max(0,Number(cost?.quantity||0))
      };
    }

    function fishingClosePurchaseModal(reason='no-casts') {
      const modal=treasureModalRoot(null);
      if (!modal) return false;
      const close=[...modal.querySelectorAll('button,[role="button"],a,div,span')]
        .filter(el=>el && !el.disabled && visible(el))
        .map(el=>({
          el,
          text:clean(el.innerText||el.textContent||'').trim(),
          aria:clean(el.getAttribute?.('aria-label')||'').trim(),
          rect:el.getBoundingClientRect?.() || {width:0,height:0,top:0,left:0}
        }))
        .filter(row=>
          /^(?:×|✕|Назад|Back|Закрыть|Close)$/i.test(row.text) ||
          /close|закрыть|back|назад/i.test(row.aria)
        )
        .sort((a,b)=>(a.rect.width*a.rect.height)-(b.rect.width*b.rect.height))[0]?.el || null;
      if (!close) return false;
      const ok=dispatchAutoMapTap(close,'fishing-'+reason+'-close');
      if (ok) {
        recordDiagnostic('fishing-auto-modal-close',{
          revision:HK_FISHING_ZERO_CAST_EXIT_REV,
          reason,
          casts:fishingVisibleCasts()
        });
      }
      return ok;
    }

    function fishingScheduleExit(reason='no-casts') {
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
rep(old_snap,new_snap,"budget snapshot and exit helpers")

old_no_target="""      let target=fishingTarget();
      if (!target) {
        recordDiagnostic('fishing-auto-budget-empty',{
          revision:HK_FISHING_BUDGET_REV,
          candidates:fishingElements().filter(row=>!row.activated).length
        });
        return false;
      }
"""
new_no_target="""      let target=fishingTarget();
      if (!target) {
        let casts=fishingVisibleCasts();

        // The counter may be between DOM updates for a few hundred ms.
        if (casts===null) {
          await new Promise(resolve=>setTimeout(resolve,420));
          casts=fishingVisibleCasts();
        }

        recordDiagnostic('fishing-auto-budget-empty',{
          revision:HK_FISHING_ZERO_CAST_EXIT_REV,
          candidates:fishingElements().filter(row=>!row.activated).length,
          casts
        });

        if (casts===null || casts<=0) {
          fishingClosePurchaseModal('budget-empty');
          fishingScheduleExit(casts===0?'zero-casts':'counter-gone');
        } else {
          lastSignature='';
          setTimeout(checkPuzzle,120);
        }
        return false;
      }
"""
rep(old_no_target,new_no_target,"no-target exit")

old_second_target="""      target=fishingTarget();
      if (!target) return false;
"""
new_second_target="""      target=fishingTarget();
      if (!target) {
        const casts=fishingVisibleCasts();
        if (casts===null || casts<=0) {
          fishingClosePurchaseModal('post-scan-empty');
          fishingScheduleExit(casts===0?'zero-casts-post-scan':'counter-gone-post-scan');
        }
        return false;
      }
"""
rep(old_second_target,new_second_target,"post-scan no target")

old_insufficient="""        if (!fishingAffordable(target.cost)) {
          const close=[...modal.querySelectorAll('button,[role="button"],a,div,span')]
            .filter(el=>el && !el.disabled && visible(el))
            .find(el=>/^(?:×|✕|Назад|Back|Закрыть|Close)$/i.test(clean(el.innerText||el.textContent||'').trim()));
          if (close) dispatchAutoMapTap(close,'fishing-insufficient-close');
          recordDiagnostic('fishing-auto-insufficient-before-confirm',{
            revision:HK_FISHING_BUDGET_REV,
            lotId:target.lotId,
            ...fishingBudgetSnapshot(target.cost)
          });
          return false;
        }
"""
new_insufficient="""        if (!fishingAffordable(target.cost)) {
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
rep(old_insufficient,new_insufficient,"modal insufficient exit")

rep("      fishingHumanFastRevision:HK_FISHING_HUMAN_FAST_REV,\n      start,",
    "      fishingHumanFastRevision:HK_FISHING_HUMAN_FAST_REV,\n      fishingZeroCastExitRevision:HK_FISHING_ZERO_CAST_EXIT_REV,\n      start,",
    "export revision")

for marker in [
    "// @version      1.18.30",
    "const BUILD_VERSION = '1.18.30';",
    "fishing-zero-cast-exit-20260927-r1",
    "return casts!==null && casts>=quantity;",
    "source:casts!==null ? 'visible-rod' : 'no-cast-counter'",
    "function fishingClosePurchaseModal",
    "function fishingScheduleExit",
    "fishing-auto-exit-ready",
    "fishing-human-fast-20260927-r1",
    "fishing-visible-casts-20260927-r1",
    "minigame-single-tap-20260927-r1"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("FISHING_ZERO_CAST_EXIT_1_18_30=PASS")
