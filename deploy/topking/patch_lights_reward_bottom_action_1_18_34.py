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

rep("// @version      1.18.33",
    "// @version      1.18.34\n// @release-note Лабиринт: финальное «Активированное хранилище» теперь подтверждается только нижней центральной кнопкой действия. Иконки ресурсов внутри окна явно исключены из кандидатов, а глобальная кнопка «Понятно» под модалкой больше не может быть нажата как подтверждение награды. После клика скрипт ждёт фактического закрытия/смены модалки перед передачей управления Автокарте.",
    "version")
rep("const BUILD_VERSION = '1.18.33';",
    "const BUILD_VERSION = '1.18.34';",
    "build")
rep("  const HK_LIGHTS_FINAL_REWARD_REV = 'lights-final-reward-20260926-r1';",
    "  const HK_LIGHTS_FINAL_REWARD_REV = 'lights-final-reward-20260926-r1';\n  const HK_LIGHTS_REWARD_CLAIM_REV = 'lights-reward-bottom-action-20260927-r1';",
    "revision")

old_btn="""    function lightsRewardClaimButton(root) {
      if (!root) return null;
      const rr=root.getBoundingClientRect?.();
      if (!rr) return null;
      const candidates=[...root.querySelectorAll('button,[role="button"],a,div')]
        .filter(element=>element && element!==lightsAutoToggle && !element.disabled && visible(element))
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const rect=element.getBoundingClientRect?.() || {width:0,height:0,top:0,left:0};
          const style=getComputedStyle(element);
          const actionable=element.matches?.('button,[role="button"],a') || !!element.onclick || style.cursor==='pointer';
          const hasIcon=!!element.querySelector?.('svg,img');
          let score=actionable?40:0;
          if (/^(?:понятно|got it|understood|ok|okay)$/i.test(text)) score-=400;
          if (/закрыть|close|×|✕|назад|back/i.test(text)) score-=400;
          if (/забрать|получить|claim|collect|open|открыть/i.test(text)) score+=180;
          if (hasIcon) score+=70;
          if (rect.width>=rr.width*0.32 && rect.height>=42) score+=80;
          if (rect.top>=rr.top+rr.height*0.58) score+=70;
          return {element,score,rect};
        })
        .filter(row=>row.score>=120)
        .sort((a,b)=>b.score-a.score || b.rect.width*b.rect.height-a.rect.width*a.rect.height);
      return candidates[0]?.element || null;
    }
"""
new_btn="""    function lightsRewardClaimButton(root) {
      if (!root) return null;
      const rr=root.getBoundingClientRect?.();
      if (!rr) return null;
      const centerX=rr.left+rr.width/2;
      const candidates=[...root.querySelectorAll('button,[role="button"],a,[onclick],div,span')]
        .filter(element=>element && element!==lightsAutoToggle && !element.disabled && visible(element))
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const rect=element.getBoundingClientRect?.() || {width:0,height:0,top:0,left:0};
          const style=getComputedStyle(element);
          const actionable=
            element.matches?.('button,[role="button"],a,[onclick]') ||
            !!element.onclick ||
            style.cursor==='pointer';
          const cx=rect.left+rect.width/2;
          const centered=Math.abs(cx-centerX)<=rr.width*0.18;
          const bottom=rect.top>=rr.top+rr.height*0.68;
          const buttonWidth=rect.width>=rr.width*0.22 && rect.width<=rr.width*0.72;
          const buttonHeight=rect.height>=28 && rect.height<=100;
          const iconCount=element.querySelectorAll?.('img,svg')?.length || 0;
          const resourceLike=
            /(?:^|\\s)x\\s*\\d+/i.test(text) ||
            /доступно\\s*:/i.test(text) ||
            !!element.closest?.('[data-lot-id]') ||
            rect.top<rr.top+rr.height*0.60;

          let score=0;
          if (actionable) score+=120;
          if (bottom) score+=220;
          if (centered) score+=180;
          if (buttonWidth) score+=120;
          if (buttonHeight) score+=90;
          if (iconCount>0 && iconCount<=2) score+=35;
          if (/забрать|получить|claim|collect|open|открыть|▶|▷|►/i.test(text)) score+=120;
          if (/^(?:понятно|got it|understood|ok|okay)$/i.test(text)) score-=500;
          if (/закрыть|close|×|✕|назад|back/i.test(text)) score-=500;
          if (resourceLike) score-=700;

          return {element,score,rect,actionable,bottom,centered};
        })
        .filter(row=>
          row.actionable &&
          row.bottom &&
          row.centered &&
          row.rect.width>0 &&
          row.rect.height>0 &&
          row.score>=400
        )
        .sort((a,b)=>b.score-a.score || b.rect.width*b.rect.height-a.rect.width*a.rect.height);
      return candidates[0]?.element || null;
    }

    function lightsRewardAckButton() {
      const roots=[...document.querySelectorAll('[role="dialog"],[aria-modal="true"],[class*="modal"],[class*="popup"],[class*="dialog"]')]
        .filter(element=>visible(element))
        .filter(element=>{
          const rect=element.getBoundingClientRect?.();
          return rect && rect.width>=220 && rect.height>=120 &&
            rect.width<window.innerWidth*0.98 &&
            rect.height<window.innerHeight*0.95;
        });

      const exact=/^(?:понятно|got it|understood|ok|okay)$/i;
      for (const root of roots) {
        const button=[...root.querySelectorAll('button,[role="button"],a')]
          .filter(element=>element && !element.disabled && visible(element))
          .find(element=>exact.test(clean(element.innerText||element.textContent||'').trim()));
        if (button) return button;
      }
      return null;
    }

    async function waitLightsRewardResult(runId,originalModal,timeoutMs=6500) {
      const started=Date.now();
      while (Date.now()-started<timeoutMs) {
        if (runId!==lightsAutoRunId || !lightsAutoEnabled()) {
          return {ok:false,reason:'cancelled',ack:null};
        }

        const ack=lightsRewardAckButton();
        if (ack) return {ok:true,reason:'ack-visible',ack};

        const current=lightsRewardModalRoot();
        if (!current) return {ok:true,reason:'modal-closed',ack:null};
        if (current!==originalModal) return {ok:true,reason:'modal-changed',ack:null};

        await new Promise(resolve=>setTimeout(resolve,100));
      }
      return {ok:false,reason:'claim-no-ui-change',ack:null};
    }
"""
rep(old_btn,new_btn,"reward claim button")

old_wait="""    async function waitLightsRewardAck(runId,timeoutMs=3200) {
      const started=Date.now();
      while (Date.now()-started<timeoutMs) {
        if (runId!==lightsAutoRunId || !lightsAutoEnabled()) return null;
        const button=lightsAcknowledgeButton(lightsRewardModalRoot());
        if (button) return button;
        await new Promise(resolve=>setTimeout(resolve,90));
      }
      return null;
    }

"""
rep(old_wait,"","remove unsafe reward ack")

old_run="""    async function runLightsFinalReward(runId,steps) {
      const reward=lightsRewardElement();
      if (!reward) {
        recordDiagnostic('lights-final-reward-skip',{revision:HK_LIGHTS_FINAL_REWARD_REV,reason:'reward-not-visible',steps});
        return {ok:true,claimed:false,reason:'reward-not-visible'};
      }

      if (!dispatchBattleTap(reward,'lights-final-reward-open')) {
        return {ok:false,claimed:false,reason:'reward-open-tap-failed'};
      }

      const modal=await waitLightsRewardModal(runId);
      if (!modal) return {ok:false,claimed:false,reason:'reward-modal-missing'};

      let claim=lightsRewardClaimButton(modal);
      let clicked=false;
      if (claim) clicked=dispatchBattleTap(claim,'lights-final-reward-claim');

      if (!clicked) {
        const rr=modal.getBoundingClientRect?.();
        if (rr) clicked=dispatchBattleTapAt(
          rr.left+rr.width/2,
          rr.top+rr.height*0.86,
          'lights-final-reward-claim-fallback'
        );
      }
      if (!clicked) return {ok:false,claimed:false,reason:'reward-claim-button-missing'};

      const ack=await waitLightsRewardAck(runId);
      if (ack) {
        if (!dispatchBattleTap(ack,'lights-final-reward-understood')) {
          return {ok:false,claimed:true,reason:'reward-ack-tap-failed'};
        }
        await new Promise(resolve=>setTimeout(resolve,220));
      }

      recordDiagnostic('lights-final-reward-complete',{
        revision:HK_LIGHTS_FINAL_REWARD_REV,
        steps,
        acknowledgement:!!ack
      });
      return {ok:true,claimed:true,reason:'reward-claimed'};
    }
"""
new_run="""    async function runLightsFinalReward(runId,steps) {
      const reward=lightsRewardElement();
      let modal=lightsRewardModalRoot();

      if (!modal) {
        if (!reward) {
          recordDiagnostic('lights-final-reward-skip',{revision:HK_LIGHTS_REWARD_CLAIM_REV,reason:'reward-not-visible',steps});
          return {ok:true,claimed:false,reason:'reward-not-visible'};
        }

        if (!dispatchBattleTap(reward,'lights-final-reward-open')) {
          return {ok:false,claimed:false,reason:'reward-open-tap-failed'};
        }

        modal=await waitLightsRewardModal(runId);
      }

      if (!modal) return {ok:false,claimed:false,reason:'reward-modal-missing'};

      const claim=lightsRewardClaimButton(modal);
      if (!claim) {
        recordDiagnostic('lights-final-reward-claim-missing',{
          revision:HK_LIGHTS_REWARD_CLAIM_REV,
          steps
        });
        return {ok:false,claimed:false,reason:'reward-claim-button-missing'};
      }

      const rect=claim.getBoundingClientRect?.();
      recordDiagnostic('lights-final-reward-claim-target',{
        revision:HK_LIGHTS_REWARD_CLAIM_REV,
        steps,
        left:Math.round(rect?.left||0),
        top:Math.round(rect?.top||0),
        width:Math.round(rect?.width||0),
        height:Math.round(rect?.height||0),
        text:clean(claim.innerText||claim.textContent||'').trim().slice(0,80)
      });

      if (!dispatchBattleTap(claim,'lights-final-reward-claim-bottom-action')) {
        return {ok:false,claimed:false,reason:'reward-claim-tap-failed'};
      }

      const result=await waitLightsRewardResult(runId,modal);
      if (!result.ok) {
        return {ok:false,claimed:false,reason:result.reason};
      }

      let acknowledged=false;
      if (result.ack) {
        if (!dispatchBattleTap(result.ack,'lights-final-reward-understood')) {
          return {ok:false,claimed:true,reason:'reward-ack-tap-failed'};
        }
        acknowledged=true;
        await new Promise(resolve=>setTimeout(resolve,260));
      }

      recordDiagnostic('lights-final-reward-complete',{
        revision:HK_LIGHTS_REWARD_CLAIM_REV,
        steps,
        acknowledgement:acknowledged,
        result:result.reason
      });
      return {ok:true,claimed:true,reason:'reward-claimed'};
    }
"""
rep(old_run,new_run,"reward final flow")

rep("      lightsStablePlanRevision:HK_LIGHTS_STABLE_PLAN_REV,\n      start,",
    "      lightsStablePlanRevision:HK_LIGHTS_STABLE_PLAN_REV,\n      lightsRewardClaimRevision:HK_LIGHTS_REWARD_CLAIM_REV,\n      start,",
    "export revision")

for marker in [
    "// @version      1.18.34",
    "const BUILD_VERSION = '1.18.34';",
    "lights-reward-bottom-action-20260927-r1",
    "function lightsRewardAckButton()",
    "async function waitLightsRewardResult",
    "reward-claim-button-missing",
    "lights-final-reward-claim-bottom-action",
    "claim-no-ui-change",
    "lights-stable-plan-20260927-r1",
    "fishing-zero-cast-exit-20260927-r1",
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

if "waitLightsRewardAck(" in s:
    raise SystemExit("unsafe waitLightsRewardAck still present")

p.write_text(s,encoding="utf-8")
print("LIGHTS_REWARD_BOTTOM_ACTION_1_18_34=PASS")
