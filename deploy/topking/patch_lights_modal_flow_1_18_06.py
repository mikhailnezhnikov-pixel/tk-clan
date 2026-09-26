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
    "// @version      1.18.05",
    "// @version      1.18.06\n"
    "// @release-note Лампочки: автоклик теперь учитывает реальный мобильный сценарий игры — после выбора лампы ждёт карточку, подтверждает стоимость 1 ягода, закрывает экран «Понятно», затем ждёт фактического изменения поля 3×3 и только после этого заново пересчитывает следующий ход. Если любой этап модального сценария не найден, автолампы безопасно отключаются.",
    "version"
)
rep("const BUILD_VERSION = '1.18.05';","const BUILD_VERSION = '1.18.06';","build")
rep(
    "  const HK_LIGHTS_AUTO_REV = 'lights-auto-recalc-20260926-r1';",
    "  const HK_LIGHTS_AUTO_REV = 'lights-modal-confirm-20260926-r2';",
    "lights revision"
)

anchor="""    async function waitLightsBoardChange(before,runId) {
      const started=Date.now();
      while (Date.now()-started<LIGHTS_AUTO_CHANGE_TIMEOUT_MS) {
        if (runId!==lightsAutoRunId || !lightsAutoEnabled()) return false;
        const current=lightsBoardSignature();
        if (current!==before) return true;
        await new Promise(resolve=>setTimeout(resolve,90));
      }
      return false;
    }

"""
insert="""    function lightsModalText(element) {
      return clean(element?.innerText || element?.textContent || '').toLowerCase();
    }

    function lightsModalRoot() {
      const rows=[];
      const add=(element,bonus=0)=>{
        if (!element || !visible(element)) return;
        const rect=element.getBoundingClientRect?.();
        if (!rect || rect.width<Math.min(260,window.innerWidth*0.42) || rect.height<160) return;
        if (rect.width>window.innerWidth*0.99 || rect.height>window.innerHeight*0.98) return;
        const text=lightsModalText(element);
        let score=bonus;
        if (/лампоч|light\\s*bulb|bulb|lights?\\s*out/.test(text)) score+=180;
        if (/понятно|got\\s*it|understood|okay|\\bok\\b/.test(text)) score+=80;
        const style=getComputedStyle(element);
        const z=parseInt(style.zIndex,10);
        if (style.position==='fixed') score+=90;
        else if (style.position==='absolute') score+=45;
        if (Number.isFinite(z) && z>=100) score+=Math.min(100,Math.log10(z+1)*20);
        const cx=rect.left+rect.width/2;
        const cy=rect.top+rect.height/2;
        const dist=Math.hypot(cx-window.innerWidth/2,cy-window.innerHeight/2);
        score+=Math.max(0,80-dist/8);
        rows.push({element,score,area:rect.width*rect.height});
      };

      [...document.querySelectorAll('[role="dialog"],[aria-modal="true"],[class*="modal"],[class*="popup"],[class*="dialog"]')]
        .forEach(element=>add(element,90));

      const buttons=[...document.querySelectorAll('button,[role="button"],a')].filter(visible);
      for (const button of buttons) {
        const text=clean(button.innerText||button.textContent||'').trim();
        if (!(text==='1' || /^(?:понятно|got it|understood|ok|okay)$/i.test(text))) continue;
        let node=button.parentElement;
        for (let depth=0;node && depth<9;depth++,node=node.parentElement) add(node,50-depth*3);
      }

      rows.sort((a,b)=>b.score-a.score || a.area-b.area);
      return rows[0]?.score>=100 ? rows[0].element : null;
    }

    async function waitLightsModal(runId,timeoutMs=2600) {
      const started=Date.now();
      while (Date.now()-started<timeoutMs) {
        if (runId!==lightsAutoRunId || !lightsAutoEnabled()) return null;
        const root=lightsModalRoot();
        if (root) return root;
        await new Promise(resolve=>setTimeout(resolve,80));
      }
      return null;
    }

    function lightsPurchaseButton(root) {
      if (!root) return null;
      const rr=root.getBoundingClientRect?.();
      if (!rr) return null;
      const candidates=[...root.querySelectorAll('button,[role="button"],a')]
        .filter(element=>element && element!==lightsAutoToggle && !element.disabled && visible(element))
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const rect=element.getBoundingClientRect?.() || {left:0,top:0,width:0,height:0};
          let score=0;
          if (text==='1') score+=220;
          if (/^(?:понятно|got it|understood|ok|okay)$/i.test(text)) score-=300;
          if (/закрыть|close|×|✕|назад|back/i.test(text)) score-=300;
          if (rect.width>=rr.width*0.28) score+=35;
          if (rect.height>=38) score+=25;
          if (rect.top>=rr.top+rr.height*0.55) score+=35;
          return {element,score};
        })
        .filter(row=>row.score>=180)
        .sort((a,b)=>b.score-a.score);
      return candidates[0]?.element || null;
    }

    function lightsAcknowledgeButton(root = null) {
      const scope=root || document;
      const exact=/^(?:понятно|got it|understood|ok|okay)$/i;
      const candidates=[...scope.querySelectorAll('button,[role="button"],a')]
        .filter(element=>element && element!==lightsAutoToggle && !element.disabled && visible(element))
        .map(element=>({element,text:clean(element.innerText||element.textContent||'').trim()}))
        .filter(row=>exact.test(row.text));
      return candidates[0]?.element || null;
    }

    async function waitLightsAcknowledge(runId,before,timeoutMs=3000) {
      const started=Date.now();
      while (Date.now()-started<timeoutMs) {
        if (runId!==lightsAutoRunId || !lightsAutoEnabled()) return {button:null,changed:false};
        const changed=lightsBoardSignature()!==before;
        const root=lightsModalRoot();
        const button=lightsAcknowledgeButton(root);
        if (button) return {button,changed};
        if (changed && !root) return {button:null,changed:true};
        await new Promise(resolve=>setTimeout(resolve,90));
      }
      return {button:null,changed:lightsBoardSignature()!==before};
    }

    async function runLightsModalStep(before,target,slot,runId) {
      if (!target || !target.isConnected) return {ok:false,reason:'target-missing'};

      const opened=dispatchBattleTap(target,'lights-open-'+slot);
      if (!opened) return {ok:false,reason:'target-tap-failed'};

      const purchaseModal=await waitLightsModal(runId);
      if (!purchaseModal) return {ok:false,reason:'purchase-modal-missing'};

      const purchaseButton=lightsPurchaseButton(purchaseModal);
      if (!purchaseButton) return {ok:false,reason:'purchase-button-missing'};

      if (!dispatchBattleTap(purchaseButton,'lights-confirm-cost-'+slot)) {
        return {ok:false,reason:'purchase-tap-failed'};
      }

      const acknowledgement=await waitLightsAcknowledge(runId,before);
      if (acknowledgement.button) {
        if (!dispatchBattleTap(acknowledgement.button,'lights-understood-'+slot)) {
          return {ok:false,reason:'ack-tap-failed'};
        }
        await new Promise(resolve=>setTimeout(resolve,180));
      }

      if (acknowledgement.changed) return {ok:true,reason:'changed-before-ack'};

      const changed=await waitLightsBoardChange(before,runId);
      return changed ? {ok:true,reason:'field-changed'} : {ok:false,reason:'field-no-change'};
    }

"""
need(anchor,"waitLightsBoardChange anchor")
s=s.replace(anchor,anchor+insert,1)

old="""          try {
            target.click();
          } catch (error) {
            return failLightsAuto('click-error',{position,steps,error:String(error?.message||error||'unknown')});
          }

          steps+=1;
          recordDiagnostic('lights-auto-click',{
            revision:HK_LIGHTS_AUTO_REV,
            step:steps,
            slot:position+1,
            remainingPlan:solution.map(pos=>pos+1)
          });

          const changed=await waitLightsBoardChange(before,runId);
          if (!changed) {
            if (runId!==lightsAutoRunId || !lightsAutoEnabled()) return false;
            return failLightsAuto('field-no-change',{position,slot:position+1,steps,state:before});
          }

          await new Promise(resolve=>setTimeout(resolve,LIGHTS_AUTO_SETTLE_MS));
"""
new="""          steps+=1;
          recordDiagnostic('lights-auto-click',{
            revision:HK_LIGHTS_AUTO_REV,
            step:steps,
            slot:position+1,
            remainingPlan:solution.map(pos=>pos+1),
            flow:'tile>cost1>ack>field-change'
          });

          const result=await runLightsModalStep(before,target,position+1,runId);
          if (!result.ok) {
            if (runId!==lightsAutoRunId || !lightsAutoEnabled()) return false;
            return failLightsAuto(result.reason,{position,slot:position+1,steps,state:before});
          }

          recordDiagnostic('lights-auto-step-complete',{
            revision:HK_LIGHTS_AUTO_REV,
            step:steps,
            slot:position+1,
            result:result.reason
          });
          await new Promise(resolve=>setTimeout(resolve,LIGHTS_AUTO_SETTLE_MS));
"""
rep(old,new,"lights modal flow")

for marker in [
    "// @version      1.18.06",
    "const BUILD_VERSION = '1.18.06';",
    "lights-modal-confirm-20260926-r2",
    "runLightsModalStep",
    "lightsPurchaseButton",
    "lightsAcknowledgeButton",
    "lights-confirm-cost-",
    "lights-understood-",
    "tile>cost1>ack>field-change",
    "chest-auto-dig-open-20260926-r1",
    "battle-auto-click-toggle-20260926-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

target.write_text(s,encoding="utf-8")
print("LIGHTS_MODAL_FLOW_1_18_06=PASS")
