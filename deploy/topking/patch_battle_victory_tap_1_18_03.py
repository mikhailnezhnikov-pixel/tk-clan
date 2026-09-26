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
    "// @version      1.18.02",
    "// @version      1.18.03\n"
    "// @release-note Сражение: финальный «Сундук победителя» теперь нажимается мобильным tap-событием, а кнопка выдачи награды ищется по геометрии модального окна с безопасным fallback-тапом по нижней центральной кнопке.",
    "version"
)
rep("const BUILD_VERSION = '1.18.02';","const BUILD_VERSION = '1.18.03';","build")

rep(
    "  const HK_BATTLE_VICTORY_CLAIM_REV = 'battle-victory-claim-20260926-r1';",
    "  const HK_BATTLE_VICTORY_CLAIM_REV = 'battle-victory-claim-20260926-r1';\n"
    "  const HK_BATTLE_VICTORY_TAP_REV = 'battle-victory-tap-fallback-20260926-r1';",
    "victory tap marker"
)

old="""    function battleVictoryElement() {
      return document.querySelector('[data-lot-id*="mf_treasurelot_enemy_defeated"]');
    }

    function battleVictoryModalRoot() {
      const candidates=[...document.querySelectorAll('[role="dialog"],[class*="modal"],[class*="popup"],div')]
        .filter(element=>visible(element))
        .filter(element=>/Сундук победителя|Victory chest|Winner chest/i.test(clean(element.innerText||element.textContent||'')));
      if (!candidates.length) return null;
      return candidates
        .map(element=>({element,area:(element.getBoundingClientRect?.().width||0)*(element.getBoundingClientRect?.().height||0)}))
        .sort((a,b)=>b.area-a.area)[0]?.element || candidates[0];
    }

    function battleVictoryClaimButton(root=battleVictoryModalRoot()) {
      if (!root) return null;
      const rootRect=root.getBoundingClientRect?.() || {top:0,height:window.innerHeight};
      const candidates=[...root.querySelectorAll('button,[role="button"],a,div')]
        .filter(element=>element && element!==battleAutoToggle && element.id!=='hkBattleAutoToggle')
        .filter(element=>!element.disabled && visible(element))
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'');
          const images=[...element.querySelectorAll?.('img')||[]]
            .map(img=>String(img.alt||'')+' '+String(img.src||'')).join(' ');
          const rect=element.getBoundingClientRect?.() || {width:0,height:0,top:0};
          const actionable=element.matches?.('button,[role="button"],a') || !!element.onclick || getComputedStyle(element).cursor==='pointer';
          let score=actionable?15:0;
          if (/получить|забрать|claim|collect|take/i.test(text)) score+=120;
          if (/play|claim|collect|reward|arrow|continue|triangle|сундук|chest/i.test(images+' '+text)) score+=70;
          if (rect.width>=180 && rect.height>=45) score+=45;
          if (rect.top>=rootRect.top+rootRect.height*0.55) score+=30;
          if (/закрыть|close|×|✕|назад|back|понятно|ok|okay/i.test(text)) score-=220;
          return {element,score,actionable};
        })
        .filter(row=>row.actionable && row.score>20)
        .sort((a,b)=>b.score-a.score);
      return candidates[0]?.element || null;
    }

    function waitBattleVictoryClaimButton(runId,timeoutMs=3000) {
      return new Promise(resolve=>{
        const started=Date.now();
        const poll=()=>{
          if (runId!==battleAutoRunId || !battleAutoEnabled()) { resolve(null); return; }
          const button=battleVictoryClaimButton();
          if (button) { resolve(button); return; }
          if (Date.now()-started>=timeoutMs) { resolve(null); return; }
          setTimeout(poll,90);
        };
        setTimeout(poll,90);
      });
    }

    async function runBattleVictoryClaim() {
      if (!battleAutoEnabled() || battleAutoRunning) return false;
      const victory=battleVictoryElement();
      const modal=battleVictoryModalRoot();
      if (!victory && !modal) return false;

      battleAutoRunning=true;
      const runId=++battleAutoRunId;
      recordDiagnostic('battle-victory-claim-start',{
        revision:HK_BATTLE_VICTORY_CLAIM_REV,
        hasVictoryLot:!!victory,
        hasModal:!!modal
      });
      try {
        if (!modal && victory) {
          victory.click();
          recordDiagnostic('battle-victory-open',{revision:HK_BATTLE_VICTORY_CLAIM_REV});
        }

        const claimButton=await waitBattleVictoryClaimButton(runId);
        if (!claimButton) {
          recordDiagnostic('battle-victory-claim-stop',{revision:HK_BATTLE_VICTORY_CLAIM_REV,reason:'claim-button-missing'});
          return false;
        }

        const before=getSignature();
        claimButton.click();
        recordDiagnostic('battle-victory-claim-click',{revision:HK_BATTLE_VICTORY_CLAIM_REV});

        await waitBattleSignatureChange(before,runId);
        await new Promise(resolve=>setTimeout(resolve,260));
        await dismissBattleRewardIfPresent(runId);
        recordDiagnostic('battle-victory-claim-complete',{revision:HK_BATTLE_VICTORY_CLAIM_REV});
        return true;
      } finally {
        if (runId===battleAutoRunId) battleAutoRunning=false;
        lastSignature='';
        setTimeout(checkPuzzle,350);
      }
    }
"""

new="""    function dispatchBattleTap(element,label='tap') {
      if (!element || !visible(element)) return false;
      const rect=element.getBoundingClientRect?.();
      if (!rect || rect.width<=0 || rect.height<=0) return false;
      const x=Math.max(1,Math.min(window.innerWidth-1,rect.left+rect.width/2));
      const y=Math.max(1,Math.min(window.innerHeight-1,rect.top+rect.height/2));
      const leaf=document.elementFromPoint(x,y) || element;
      const options={bubbles:true,cancelable:true,clientX:x,clientY:y,screenX:x,screenY:y,button:0,buttons:1,pointerId:1,pointerType:'touch',isPrimary:true};
      try { leaf.dispatchEvent(new PointerEvent('pointerdown',options)); } catch (_) {}
      try { leaf.dispatchEvent(new MouseEvent('mousedown',{...options,buttons:1})); } catch (_) {}
      try { leaf.dispatchEvent(new PointerEvent('pointerup',{...options,buttons:0})); } catch (_) {}
      try { leaf.dispatchEvent(new MouseEvent('mouseup',{...options,buttons:0})); } catch (_) {}
      try { leaf.dispatchEvent(new MouseEvent('click',{...options,buttons:0})); } catch (_) {}
      try { leaf.click?.(); } catch (_) {}
      recordDiagnostic('battle-mobile-tap',{revision:HK_BATTLE_VICTORY_TAP_REV,label,x:Math.round(x),y:Math.round(y),tag:leaf.tagName||''});
      return true;
    }

    function dispatchBattleTapAt(x,y,label='tap-at') {
      const px=Math.max(1,Math.min(window.innerWidth-1,Number(x)||1));
      const py=Math.max(1,Math.min(window.innerHeight-1,Number(y)||1));
      const leaf=document.elementFromPoint(px,py);
      if (!leaf) return false;
      const options={bubbles:true,cancelable:true,clientX:px,clientY:py,screenX:px,screenY:py,button:0,buttons:1,pointerId:1,pointerType:'touch',isPrimary:true};
      try { leaf.dispatchEvent(new PointerEvent('pointerdown',options)); } catch (_) {}
      try { leaf.dispatchEvent(new MouseEvent('mousedown',{...options,buttons:1})); } catch (_) {}
      try { leaf.dispatchEvent(new PointerEvent('pointerup',{...options,buttons:0})); } catch (_) {}
      try { leaf.dispatchEvent(new MouseEvent('mouseup',{...options,buttons:0})); } catch (_) {}
      try { leaf.dispatchEvent(new MouseEvent('click',{...options,buttons:0})); } catch (_) {}
      try { leaf.click?.(); } catch (_) {}
      recordDiagnostic('battle-mobile-tap',{revision:HK_BATTLE_VICTORY_TAP_REV,label,x:Math.round(px),y:Math.round(py),tag:leaf.tagName||''});
      return true;
    }

    function battleVictoryElement() {
      const elements=[...document.querySelectorAll('[data-lot-id*="mf_treasurelot_enemy_defeated"]')].filter(visible);
      return elements
        .map(element=>({element,area:(element.getBoundingClientRect?.().width||0)*(element.getBoundingClientRect?.().height||0)}))
        .sort((a,b)=>b.area-a.area)[0]?.element || null;
    }

    function battleVictoryModalRoot() {
      const all=[...document.querySelectorAll('[role="dialog"],[class*="modal"],[class*="popup"],div')];
      const candidates=all
        .filter(element=>visible(element))
        .filter(element=>/Сундук победителя|Victory chest|Winner chest/i.test(clean(element.innerText||element.textContent||'')))
        .map(element=>{
          const rect=element.getBoundingClientRect?.() || {width:0,height:0};
          return {element,rect,area:rect.width*rect.height};
        })
        .filter(row=>row.rect.width>=Math.min(280,window.innerWidth*0.45) && row.rect.height>=220)
        .filter(row=>row.rect.width<=window.innerWidth*0.99 && row.rect.height<=window.innerHeight*0.96)
        .sort((a,b)=>a.area-b.area);
      return candidates[0]?.element || null;
    }

    function battleVictoryClaimButton(root=battleVictoryModalRoot()) {
      if (!root) return null;
      const rr=root.getBoundingClientRect?.();
      if (!rr) return null;
      const centerX=rr.left+rr.width/2;
      const candidates=[...root.querySelectorAll('button,[role="button"],a,div,span')]
        .filter(element=>element && element!==battleAutoToggle && element.id!=='hkBattleAutoToggle')
        .filter(element=>!element.disabled && visible(element))
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'');
          const images=[...element.querySelectorAll?.('img')||[]]
            .map(img=>String(img.alt||'')+' '+String(img.src||'')).join(' ');
          const rect=element.getBoundingClientRect?.() || {width:0,height:0,left:0,top:0};
          const cx=rect.left+rect.width/2;
          const inBottom=rect.top>=rr.top+rr.height*0.62;
          const centered=Math.abs(cx-centerX)<=rr.width*0.22;
          let score=0;
          if (/получить|забрать|claim|collect|take/i.test(text)) score+=160;
          if (/play|claim|collect|reward|arrow|continue|triangle|сундук|chest/i.test(images+' '+text)) score+=100;
          if (rect.width>=rr.width*0.28 && rect.width<=rr.width*0.78) score+=60;
          if (rect.height>=42 && rect.height<=140) score+=45;
          if (inBottom) score+=70;
          if (centered) score+=55;
          if (/закрыть|close|×|✕|назад|back|понятно|ok|okay/i.test(text)) score-=300;
          return {element,score,rect};
        })
        .filter(row=>row.score>=120)
        .sort((a,b)=>b.score-a.score || a.rect.width*a.rect.height-b.rect.width*b.rect.height);
      return candidates[0]?.element || null;
    }

    function waitBattleVictoryClaimButton(runId,timeoutMs=2600) {
      return new Promise(resolve=>{
        const started=Date.now();
        const poll=()=>{
          if (runId!==battleAutoRunId || !battleAutoEnabled()) { resolve(null); return; }
          const button=battleVictoryClaimButton();
          if (button) { resolve(button); return; }
          if (Date.now()-started>=timeoutMs) { resolve(null); return; }
          setTimeout(poll,90);
        };
        setTimeout(poll,90);
      });
    }

    async function tapVictoryFallback(root,runId) {
      if (!root || runId!==battleAutoRunId || !battleAutoEnabled()) return false;
      const rr=root.getBoundingClientRect?.();
      if (!rr) return false;
      const x=rr.left+rr.width/2;
      for (const fraction of [0.90,0.86,0.93]) {
        if (runId!==battleAutoRunId || !battleAutoEnabled()) return false;
        const before=getSignature();
        dispatchBattleTapAt(x,rr.top+rr.height*fraction,'victory-fallback-'+fraction);
        await new Promise(resolve=>setTimeout(resolve,520));
        if (getSignature()!==before || !battleVictoryModalRoot()) return true;
      }
      return false;
    }

    async function runBattleVictoryClaim() {
      if (!battleAutoEnabled() || battleAutoRunning) return false;
      let victory=battleVictoryElement();
      let modal=battleVictoryModalRoot();
      if (!victory && !modal) return false;

      battleAutoRunning=true;
      const runId=++battleAutoRunId;
      recordDiagnostic('battle-victory-claim-start',{
        revision:HK_BATTLE_VICTORY_TAP_REV,
        hasVictoryLot:!!victory,
        hasModal:!!modal
      });
      try {
        if (!modal && victory) {
          dispatchBattleTap(victory,'victory-tile');
          recordDiagnostic('battle-victory-open',{revision:HK_BATTLE_VICTORY_TAP_REV});
          const started=Date.now();
          while (Date.now()-started<2600 && runId===battleAutoRunId && battleAutoEnabled()) {
            modal=battleVictoryModalRoot();
            if (modal) break;
            await new Promise(resolve=>setTimeout(resolve,90));
          }
        }

        modal=battleVictoryModalRoot();
        if (!modal) {
          recordDiagnostic('battle-victory-claim-stop',{revision:HK_BATTLE_VICTORY_TAP_REV,reason:'victory-modal-missing'});
          return false;
        }

        const before=getSignature();
        const claimButton=await waitBattleVictoryClaimButton(runId);
        let tapped=false;
        if (claimButton) {
          tapped=dispatchBattleTap(claimButton,'victory-claim-button');
          recordDiagnostic('battle-victory-claim-click',{revision:HK_BATTLE_VICTORY_TAP_REV,mode:'element'});
        }
        if (!tapped || getSignature()===before) {
          await new Promise(resolve=>setTimeout(resolve,180));
          if (battleVictoryModalRoot()) {
            tapped=await tapVictoryFallback(battleVictoryModalRoot(),runId) || tapped;
            recordDiagnostic('battle-victory-claim-click',{revision:HK_BATTLE_VICTORY_TAP_REV,mode:'fallback',tapped});
          }
        }

        await waitBattleSignatureChange(before,runId);
        await new Promise(resolve=>setTimeout(resolve,300));
        await dismissBattleRewardIfPresent(runId);
        const success=!battleVictoryModalRoot();
        recordDiagnostic('battle-victory-claim-complete',{revision:HK_BATTLE_VICTORY_TAP_REV,success});
        return success;
      } finally {
        if (runId===battleAutoRunId) battleAutoRunning=false;
        lastSignature='';
        setTimeout(checkPuzzle,350);
      }
    }
"""
rep(old,new,"victory mobile tap implementation")

for marker in [
    "// @version      1.18.03",
    "const BUILD_VERSION = '1.18.03';",
    "battle-victory-tap-fallback-20260926-r1",
    "dispatchBattleTapAt",
    "victory-fallback-",
    "victory-claim-button",
    "mf_treasurelot_enemy_defeated",
    "battle-victory-claim-20260926-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

target.write_text(s,encoding="utf-8")
print("BATTLE_VICTORY_TAP_1_18_03=PASS")
