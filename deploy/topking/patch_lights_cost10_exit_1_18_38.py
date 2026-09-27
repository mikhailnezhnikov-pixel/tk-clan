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

rep("// @version      1.18.37",
    "// @version      1.18.38\n// @release-note Автокарта/Лабиринт: после основной награды выход выполняется через широкую нижнюю кнопку стоимости 10, а не через маленькую квадратную кнопку слева — она открывает инструкцию. Кнопка 10 теперь ищется по точной геометрии нижнего футера и подтверждается как обычная покупка выхода; инструкция больше не используется как fallback.",
    "version")
rep("const BUILD_VERSION = '1.18.37';",
    "const BUILD_VERSION = '1.18.38';",
    "build")
rep("  const HK_LIGHTS_MODAL_STEP_REV = 'lights-close-modal-between-steps-20260927-r1';",
    "  const HK_LIGHTS_MODAL_STEP_REV = 'lights-close-modal-between-steps-20260927-r1';\n  const HK_LIGHTS_COST_EXIT_REV = 'lights-cost10-exit-20260927-r1';",
    "revision")

old_bottom="""    function autoMapBottomContinueButton() {
      const candidates=[...document.querySelectorAll('button,[role="button"],a,div')]
        .filter(element=>
          element &&
          element!==autoMapToggle &&
          !element.disabled &&
          visible(element)
        )
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const rect=element.getBoundingClientRect?.() || {width:0,height:0,left:0,top:0};
          const actionable=element.matches?.('button,[role="button"],a') || !!element.onclick || getComputedStyle(element).cursor==='pointer';
          let score=0;
          if (/^10$/.test(text)) score+=120;
          if (rect.top>=window.innerHeight*0.62) score+=80;
          if (rect.width>=window.innerWidth*0.45) score+=80;
          if (rect.height>=38 && rect.height<=150) score+=40;
          if (actionable) score+=50;
          return {element,text,rect,score,area:rect.width*rect.height};
        })
        .filter(row=>row.score>=240)
        .sort((a,b)=>b.score-a.score || b.area-a.area);
      return candidates[0]?.element || null;
    }
"""
new_bottom="""    function autoMapBottomContinueButton(cost=10) {
      const wanted=String(Number(cost)||10);
      const vw=Math.max(1,window.innerWidth);
      const vh=Math.max(1,window.innerHeight);
      const centerX=vw/2;

      const candidates=[...document.querySelectorAll('button,[role="button"],a,[onclick],div,span')]
        .filter(element=>
          element &&
          element!==autoMapToggle &&
          element!==battleAutoToggle &&
          element!==chestAutoToggle &&
          element!==lightsAutoToggle &&
          element!==fishingAutoToggle &&
          element!==traderAutoToggle &&
          !element.disabled &&
          element.getAttribute?.('aria-disabled')!=='true' &&
          visible(element)
        )
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const rect=element.getBoundingClientRect?.() || {width:0,height:0,left:0,top:0};
          const style=getComputedStyle(element);
          const actionable=
            element.matches?.('button,[role="button"],a,[onclick]') ||
            !!element.onclick ||
            style.cursor==='pointer';
          const cx=rect.left+rect.width/2;
          const cy=rect.top+rect.height/2;

          let score=0;
          if (text===wanted) score+=500;
          else if (new RegExp('(?:^|\\\\s)'+wanted+'(?:\\\\s|$)').test(text) && text.length<=12) score+=300;

          if (cy>=vh*0.84) score+=260;
          if (Math.abs(cx-centerX)<=vw*0.22) score+=220;
          if (rect.width>=vw*0.12 && rect.width<=vw*0.48) score+=220;
          if (rect.height>=30 && rect.height<=110) score+=100;
          if (actionable) score+=120;

          if (rect.width<vw*0.08) score-=700;
          if (rect.width>vw*0.60) score-=500;
          if (cx<=vw*0.28 || cx>=vw*0.78) score-=320;
          if (/правила|инструкц|help|rules|info/i.test(text+' '+String(element.getAttribute?.('aria-label')||''))) score-=900;
          if (/^hk$/i.test(text)) score-=900;

          return {element,text,rect,score,area:rect.width*rect.height};
        })
        .filter(row=>row.score>=850)
        .sort((a,b)=>b.score-a.score || b.area-a.area);

      return candidates[0]?.element || null;
    }
"""
rep(old_bottom,new_bottom,"precise bottom cost button")

start=s.find("    async function autoMapReturnFromCompletedLights() {")
end=s.find("\n    function autoMapBottomContinueButton",start)
if start<0 or end<0:
    raise SystemExit("autoMapReturnFromCompletedLights block not found")

new_return="""    async function autoMapReturnFromCompletedLights() {
      if (!autoMapEnabled() || !lightsRoomCompleted()) return false;

      if (!lightsFinalRewardClaimed && lightsRewardActivated()) {
        lightsFinalRewardClaimed=true;
        lightsFinalRewardClaimedAt=Date.now();
        recordDiagnostic('lights-final-reward-recovered',{
          revision:HK_LIGHTS_COMPLETED_RETURN_REV,
          source:'activated-reward-dom'
        });
      }

      autoMapStatus('выход за 10',{
        revision:HK_LIGHTS_COST_EXIT_REV,
        claimedAgoMs:lightsFinalRewardClaimedAt ? Date.now()-lightsFinalRewardClaimedAt : null
      });

      await autoMapWaitActionGap();
      if (!autoMapEnabled() || !lightsRoomCompleted()) return false;

      const explicit=autoMapExitButton();
      if (explicit) {
        const ok=await autoMapTapAndConfirm(explicit,'lights-return-map-explicit',10);
        if (ok && await autoMapWaitReturnedFromLights()) {
          lightsFinalRewardClaimed=false;
          lightsFinalRewardClaimedAt=0;
          autoMapReturnNotBefore=Date.now()+350;
          autoMapCurrentLot='';
          lastSignature='';
          recordDiagnostic('lights-map-return-complete',{
            revision:HK_LIGHTS_COST_EXIT_REV,
            method:'explicit-exit'
          });
          setTimeout(()=>void runAutoMapTick('lights-returned-map'),420);
          return true;
        }
      }

      const costExit=autoMapBottomContinueButton(10);
      if (!costExit) {
        autoMapRetryNotBefore=Date.now()+900;
        autoMapStatus('жду кнопку выхода 10',{
          revision:HK_LIGHTS_COST_EXIT_REV
        });
        recordDiagnostic('lights-cost-exit-missing',{
          revision:HK_LIGHTS_COST_EXIT_REV
        });
        return false;
      }

      const rect=costExit.getBoundingClientRect?.();
      recordDiagnostic('lights-cost-exit-target',{
        revision:HK_LIGHTS_COST_EXIT_REV,
        text:clean(costExit.innerText||costExit.textContent||'').trim(),
        left:Math.round(rect?.left||0),
        top:Math.round(rect?.top||0),
        width:Math.round(rect?.width||0),
        height:Math.round(rect?.height||0)
      });

      const ok=await autoMapTapAndConfirm(costExit,'lights-return-map-cost10',10);
      if (!ok) {
        autoMapRetryNotBefore=Date.now()+1200;
        return false;
      }

      const returned=await autoMapWaitReturnedFromLights(6500);
      if (!returned) {
        autoMapRetryNotBefore=Date.now()+1400;
        autoMapStatus('жду карту после выхода 10',{
          revision:HK_LIGHTS_COST_EXIT_REV
        });
        return false;
      }

      lightsFinalRewardClaimed=false;
      lightsFinalRewardClaimedAt=0;
      autoMapReturnNotBefore=Date.now()+350;
      autoMapCurrentLot='';
      lastSignature='';
      recordDiagnostic('lights-map-return-complete',{
        revision:HK_LIGHTS_COST_EXIT_REV,
        method:'cost10-footer',
        activeCells:autoMapActiveCellCount()
      });
      setTimeout(()=>{
        checkPuzzle();
        void runAutoMapTick('lights-returned-map');
      },420);
      return true;
    }
"""
s=s[:start]+new_return+s[end:]

rep("      lightsModalStepRevision:HK_LIGHTS_MODAL_STEP_REV,\n      start,",
    "      lightsModalStepRevision:HK_LIGHTS_MODAL_STEP_REV,\n      lightsCostExitRevision:HK_LIGHTS_COST_EXIT_REV,\n      start,",
    "export cost exit revision")

for marker in [
    "// @version      1.18.38",
    "const BUILD_VERSION = '1.18.38';",
    "lights-cost10-exit-20260927-r1",
    "function autoMapBottomContinueButton(cost=10)",
    "method:'cost10-footer'",
    "жду кнопку выхода 10",
    "lights-cost-exit-target",
    "lights-return-map-cost10",
    "lights-close-modal-between-steps-20260927-r1",
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

completed=s[s.find("    async function autoMapReturnFromCompletedLights() {"):s.find("\n    function autoMapBottomContinueButton",s.find("    async function autoMapReturnFromCompletedLights() {"))]
if "autoMapCompletedLightsBackButton()" in completed:
    raise SystemExit("instruction/back fallback still used by completed lights")

p.write_text(s,encoding="utf-8")
print("LIGHTS_COST10_EXIT_1_18_38=PASS")
