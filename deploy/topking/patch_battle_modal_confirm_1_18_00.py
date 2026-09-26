from pathlib import Path
import sys

target=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=target.read_text(encoding="utf-8")

def need(old,label,count=1):
    actual=s.count(old)
    if actual!=count:
        raise SystemExit(f"{label}: expected {count}, got {actual}")

def rep(old,new,label,count=1):
    global s
    need(old,label,count)
    s=s.replace(old,new,count)

rep(
    "// @version      1.17.99",
    "// @version      1.18.00\n"
    "// @release-note Сражение: исправлен автобой на мобильном интерфейсе. Первый клик открывает карточку врага, затем HK нажимает кнопку фактической атаки в модальном окне, ждёт изменение поля и заново пересчитывает весь порядок перед следующим ударом.",
    "version"
)
rep("const BUILD_VERSION = '1.17.99';","const BUILD_VERSION = '1.18.00';","build")

rep(
    "  const HK_BATTLE_AUTO_CLICK_REV = 'battle-auto-click-toggle-20260926-r1';",
    "  const HK_BATTLE_AUTO_CLICK_REV = 'battle-auto-click-toggle-20260926-r1';\n"
    "  const HK_BATTLE_MODAL_CONFIRM_REV = 'battle-modal-confirm-20260926-r1';",
    "modal confirm marker"
)

old="""    function waitBattleSignatureChange(before,runId) {
      return new Promise(resolve=>{
        const started=Date.now();
        const poll=()=>{
          if (runId!==battleAutoRunId || !battleAutoEnabled()) { resolve(false); return; }
          const current=getSignature();
          if (current!==before) { resolve(true); return; }
          if (Date.now()-started>=BATTLE_AUTO_CHANGE_TIMEOUT_MS) { resolve(false); return; }
          setTimeout(poll,90);
        };
        setTimeout(poll,90);
      });
    }

    async function runBattleAuto(solution) {
      if (!battleAutoEnabled() || battleAutoRunning || !solution?.order?.length) return false;
      battleAutoRunning=true;
      const runId=++battleAutoRunId;
      recordDiagnostic('battle-auto-start',{
        revision:HK_BATTLE_AUTO_CLICK_REV,
        steps:solution.order.length,
        order:solution.order.map(position=>position+BATTLE_FIRST_SLOT)
      });
      try {
        for (let index=0;index<solution.order.length;index++) {
          if (runId!==battleAutoRunId || !battleAutoEnabled()) return false;
          const slot=solution.order[index]+BATTLE_FIRST_SLOT;
          const element=battleElementForSlot(slot);
          if (!element) {
            recordDiagnostic('battle-auto-stop',{revision:HK_BATTLE_AUTO_CLICK_REV,reason:'target-missing',slot,index});
            return false;
          }
          const before=getSignature();
          element.click();
          recordDiagnostic('battle-auto-click',{revision:HK_BATTLE_AUTO_CLICK_REV,slot,index:index+1});
          const changed=await waitBattleSignatureChange(before,runId);
          if (!changed) {
            recordDiagnostic('battle-auto-stop',{revision:HK_BATTLE_AUTO_CLICK_REV,reason:'field-no-change',slot,index});
            return false;
          }
          await new Promise(resolve=>setTimeout(resolve,BATTLE_AUTO_SETTLE_MS));
        }
        recordDiagnostic('battle-auto-complete',{revision:HK_BATTLE_AUTO_CLICK_REV,steps:solution.order.length});
        return true;
      } finally {
        if (runId===battleAutoRunId) battleAutoRunning=false;
        lastSignature='';
        setTimeout(checkPuzzle,300);
      }
    }
"""

new="""    function waitBattleSignatureChange(before,runId) {
      return new Promise(resolve=>{
        const started=Date.now();
        const poll=()=>{
          if (runId!==battleAutoRunId || !battleAutoEnabled()) { resolve(false); return; }
          const current=getSignature();
          if (current!==before) { resolve(true); return; }
          if (Date.now()-started>=BATTLE_AUTO_CHANGE_TIMEOUT_MS) { resolve(false); return; }
          setTimeout(poll,90);
        };
        setTimeout(poll,90);
      });
    }

    function battleCostForElement(element) {
      const id=element?.getAttribute?.('data-lot-id')||'';
      const match=id.match(/enemy_type_(?:01|02|03|04)_(\d+)_sl\d+/);
      return match ? Number(match[1]) : null;
    }

    function battleActionButton(expectedCost) {
      const costText=String(expectedCost ?? '');
      const candidates=[...document.querySelectorAll('button,[role="button"],a')]
        .filter(element=>element && element!==battleAutoToggle && element.id!=='hkBattleAutoToggle')
        .filter(element=>!element.disabled && visible(element))
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'');
          const images=[...element.querySelectorAll?.('img')||[]]
            .map(img=>String(img.alt||'')+' '+String(img.src||'')).join(' ');
          const rect=element.getBoundingClientRect?.() || {width:0,height:0,top:0};
          let score=0;
          if (text===costText) score+=100;
          else if (costText && new RegExp('(?:^|\\s)'+costText+'(?:\\s|$)').test(text)) score+=35;
          if (/sword|attack|fight|weapon|blade|меч|атак/i.test(images+' '+text)) score+=50;
          if (rect.width>=120 && rect.height>=36) score+=10;
          if (rect.top>window.innerHeight*0.45) score+=5;
          if (/закрыть|close|×|✕|назад|back/i.test(text)) score-=200;
          return {element,text,score};
        })
        .filter(row=>row.score>0)
        .sort((a,b)=>b.score-a.score);
      return candidates[0]?.element || null;
    }

    function waitBattleActionButton(expectedCost,runId,timeoutMs=2500) {
      return new Promise(resolve=>{
        const started=Date.now();
        const poll=()=>{
          if (runId!==battleAutoRunId || !battleAutoEnabled()) { resolve(null); return; }
          const button=battleActionButton(expectedCost);
          if (button) { resolve(button); return; }
          if (Date.now()-started>=timeoutMs) { resolve(null); return; }
          setTimeout(poll,80);
        };
        setTimeout(poll,80);
      });
    }

    async function runBattleAuto(solution) {
      if (!battleAutoEnabled() || battleAutoRunning || !solution?.order?.length) return false;
      battleAutoRunning=true;
      const runId=++battleAutoRunId;
      const position=solution.order[0];
      const slot=position+BATTLE_FIRST_SLOT;
      recordDiagnostic('battle-auto-start',{
        revision:HK_BATTLE_MODAL_CONFIRM_REV,
        plannedSteps:solution.order.length,
        nextSlot:slot,
        fullOrder:solution.order.map(value=>value+BATTLE_FIRST_SLOT)
      });
      try {
        if (runId!==battleAutoRunId || !battleAutoEnabled()) return false;
        const element=battleElementForSlot(slot);
        if (!element) {
          recordDiagnostic('battle-auto-stop',{revision:HK_BATTLE_MODAL_CONFIRM_REV,reason:'target-missing',slot});
          return false;
        }
        const expectedCost=battleCostForElement(element);
        const before=getSignature();

        // First tap only opens the enemy card in the mobile UI.
        element.click();
        recordDiagnostic('battle-auto-open-card',{revision:HK_BATTLE_MODAL_CONFIRM_REV,slot,expectedCost});

        // The actual attack is a second tap on the cost/action button in the modal.
        const actionButton=await waitBattleActionButton(expectedCost,runId);
        if (!actionButton) {
          recordDiagnostic('battle-auto-stop',{revision:HK_BATTLE_MODAL_CONFIRM_REV,reason:'attack-button-missing',slot,expectedCost});
          return false;
        }
        actionButton.click();
        recordDiagnostic('battle-auto-confirm-attack',{revision:HK_BATTLE_MODAL_CONFIRM_REV,slot,expectedCost});

        const changed=await waitBattleSignatureChange(before,runId);
        if (!changed) {
          recordDiagnostic('battle-auto-stop',{revision:HK_BATTLE_MODAL_CONFIRM_REV,reason:'field-no-change-after-confirm',slot,expectedCost});
          return false;
        }

        await new Promise(resolve=>setTimeout(resolve,BATTLE_AUTO_SETTLE_MS));
        recordDiagnostic('battle-auto-step-complete',{revision:HK_BATTLE_MODAL_CONFIRM_REV,slot,expectedCost});

        // Deliberately execute one hit only. The board is recalculated from the
        // real post-hit DOM before choosing the next target. This protects
        // against chain explosions/heals and any game-side state differences.
        return true;
      } finally {
        if (runId===battleAutoRunId) battleAutoRunning=false;
        lastSignature='';
        setTimeout(checkPuzzle,300);
      }
    }
"""
rep(old,new,"modal two-stage auto battle")

for marker in [
    "// @version      1.18.00",
    "const BUILD_VERSION = '1.18.00';",
    "battle-modal-confirm-20260926-r1",
    "battle-auto-open-card",
    "battle-auto-confirm-attack",
    "battleActionButton",
    "waitBattleActionButton",
    "const position=solution.order[0];",
    "field-no-change-after-confirm",
    "enemy_type_(01|02|03|04)",
    "battle-auto-click-toggle-20260926-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

target.write_text(s,encoding="utf-8")
print("BATTLE_MODAL_CONFIRM_1_18_00=PASS")
