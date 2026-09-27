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

rep("// @version      1.18.34",
    "// @version      1.18.35\n// @release-note Лампочки/Автокарта: после подтверждённого получения центральной награды комната считается завершённой и больше не запускает Автолампы повторно. Автокарта получает строгий handoff «основная награда забрана → кнопка возврата из мини-игры → Карта Сокровищ → продолжить активные клетки». Для выхода добавлен отдельный поиск текстового или иконочного Back/Exit-контрола с проверкой фактического возврата на карту.",
    "version")
rep("const BUILD_VERSION = '1.18.34';",
    "const BUILD_VERSION = '1.18.35';",
    "build")
rep("  const HK_LIGHTS_REWARD_CLAIM_REV = 'lights-reward-bottom-action-20260927-r1';",
    "  const HK_LIGHTS_REWARD_CLAIM_REV = 'lights-reward-bottom-action-20260927-r1';\n  const HK_LIGHTS_MAP_RETURN_REV = 'lights-map-return-after-main-reward-20260927-r1';",
    "revision")

rep("""    let lightsAutoRunning = false;
    let lightsAutoRunId = 0;
    let lightsAutoToggle = null;
""",
"""    let lightsAutoRunning = false;
    let lightsAutoRunId = 0;
    let lightsAutoToggle = null;
    let lightsFinalRewardClaimed = false;
    let lightsFinalRewardClaimedAt = 0;
""",
"lights claimed state")

old_should="""    function lightsShouldAuto() {
      return lightsNeedsAuto() || !!lightsRewardElement();
    }
"""
new_should="""    function lightsShouldAuto() {
      if (lightsFinalRewardClaimed) return false;
      return lightsNeedsAuto() || !!lightsRewardElement();
    }
"""
rep(old_should,new_should,"lightsShouldAuto claimed guard")

old_complete="""      recordDiagnostic('lights-final-reward-complete',{
        revision:HK_LIGHTS_REWARD_CLAIM_REV,
        steps,
        acknowledgement:acknowledged,
        result:result.reason
      });
      return {ok:true,claimed:true,reason:'reward-claimed'};
"""
new_complete="""      lightsFinalRewardClaimed=true;
      lightsFinalRewardClaimedAt=Date.now();
      recordDiagnostic('lights-final-reward-complete',{
        revision:HK_LIGHTS_REWARD_CLAIM_REV,
        steps,
        acknowledgement:acknowledged,
        result:result.reason,
        mapHandoffRevision:HK_LIGHTS_MAP_RETURN_REV
      });
      return {ok:true,claimed:true,reason:'reward-claimed'};
"""
rep(old_complete,new_complete,"mark final reward claimed")

# Reset a stale claimed flag if a fresh unsolved 3x3 board appears.
old_runlights="""    function runLights() {
      const board = getLightsBoard();
      if (board.filter(cell => cell !== null).length !== 9) return false;
      clearNumbers();
      const solution = solveLights(board);
"""
new_runlights="""    function runLights() {
      const board = getLightsBoard();
      if (board.filter(cell => cell !== null).length !== 9) return false;
      const liveState=lightsState(board);
      if (liveState && !allLightsOn(liveState) && lightsFinalRewardClaimed) {
        lightsFinalRewardClaimed=false;
        lightsFinalRewardClaimedAt=0;
        recordDiagnostic('lights-final-reward-reset',{
          revision:HK_LIGHTS_MAP_RETURN_REV,
          reason:'fresh-unsolved-board'
        });
      }
      clearNumbers();
      const solution = solveLights(board);
"""
rep(old_runlights,new_runlights,"reset on fresh lights board")

# Add dedicated completed-lights room return helpers after generic exit button.
anchor="""    function autoMapExitButton() {
      return autoMapFindTextButton(/^(?:Покинуть локацию|Покинуть локацию\\s*›?|Leave location|Exit location)$/i);
    }

"""
insert="""    function autoMapCompletedLightsBackButton() {
      if (!lightsFinalRewardClaimed) return null;

      const viewportW=Math.max(1,window.innerWidth);
      const viewportH=Math.max(1,window.innerHeight);
      const candidates=[...document.querySelectorAll('button,[role="button"],a,[onclick],div')]
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
          const aria=clean(
            element.getAttribute?.('aria-label') ||
            element.getAttribute?.('title') ||
            element.getAttribute?.('data-tooltip') ||
            ''
          ).trim();
          const rect=element.getBoundingClientRect?.() || {left:0,top:0,width:0,height:0};
          const style=getComputedStyle(element);
          const actionable=
            element.matches?.('button,[role="button"],a,[onclick]') ||
            !!element.onclick ||
            style.cursor==='pointer';
          const squareish=
            rect.width>=28 && rect.width<=105 &&
            rect.height>=28 && rect.height<=105 &&
            rect.width/Math.max(1,rect.height)>=0.55 &&
            rect.width/Math.max(1,rect.height)<=1.85;
          const nearRight=rect.left>=viewportW*0.84;
          const nearLeft=rect.left+rect.width<=viewportW*0.20;
          const low=rect.top>=viewportH*0.62;
          const veryLow=rect.top>=viewportH*0.78;
          const hasIcon=!!element.querySelector?.('svg,img,use,path') || /[←↩⟵‹«]/.test(text);
          const explicitBack=/назад|back|return|вернуться|покинуть|leave|exit/i.test(text+' '+aria);

          let score=0;
          if (actionable) score+=100;
          if (explicitBack) score+=340;
          if (squareish) score+=130;
          if (low) score+=80;
          if (veryLow) score+=55;
          if (nearRight) score+=150;
          if (nearLeft) score+=70;
          if (hasIcon) score+=70;
          if (!text || /^[←↩⟵‹«]$/.test(text)) score+=45;

          // Never mistake the wide yellow "10" continuation/cost bar or HK
          // floating controls for the room-return control.
          if (rect.width>130 || rect.height>120) score-=500;
          if (/^\\d+$/.test(text)) score-=500;
          if (/^hk$/i.test(text)) score-=500;
          if (/автокарта|автолампы|auto\\s*map|auto\\s*lights/i.test(text)) score-=700;

          return {element,score,rect,text,aria};
        })
        .filter(row=>row.score>=300)
        .sort((a,b)=>b.score-a.score || a.rect.width*a.rect.height-b.rect.width*b.rect.height);

      return candidates[0]?.element || null;
    }

    async function autoMapWaitReturnedFromLights(timeoutMs=6500) {
      const started=Date.now();
      while (Date.now()-started<timeoutMs) {
        if (!autoMapEnabled()) return false;
        const signature=getSignature();
        const mapVisible=treasureGuideScreenVisible();
        const lightsForeground=signature.startsWith('LIGHTS|') && autoMapMiniGameForeground();
        if (mapVisible && !lightsForeground) return true;
        await new Promise(resolve=>setTimeout(resolve,100));
      }
      return false;
    }

    async function autoMapReturnFromCompletedLights() {
      if (!autoMapEnabled() || !lightsFinalRewardClaimed) return false;

      autoMapStatus('возврат на карту',{
        revision:HK_LIGHTS_MAP_RETURN_REV,
        claimedAgoMs:lightsFinalRewardClaimedAt ? Date.now()-lightsFinalRewardClaimedAt : null
      });

      await autoMapWaitActionGap();
      if (!autoMapEnabled() || !lightsFinalRewardClaimed) return false;

      // Prefer an explicit Leave/Exit button if the room exposes one.
      const explicit=autoMapExitButton();
      if (explicit) {
        const ok=await autoMapTapAndConfirm(explicit,'lights-return-map-explicit',10);
        if (ok && await autoMapWaitReturnedFromLights()) {
          lightsFinalRewardClaimed=false;
          lightsFinalRewardClaimedAt=0;
          autoMapReturnNotBefore=Date.now()+350;
          lastSignature='';
          recordDiagnostic('lights-map-return-complete',{
            revision:HK_LIGHTS_MAP_RETURN_REV,
            method:'explicit-exit'
          });
          setTimeout(()=>void runAutoMapTick('lights-returned-map'),420);
          return true;
        }
      }

      const back=autoMapCompletedLightsBackButton();
      if (!back) {
        autoMapStatus('жду выход из ламп',{
          revision:HK_LIGHTS_MAP_RETURN_REV
        });
        return false;
      }

      autoMapActionCount+=1;
      autoMapLastActionAt=Date.now();
      if (!dispatchBattleTap(back,'lights-return-map-back')) {
        return false;
      }

      // Some layouts return immediately; others put a confirm modal over the
      // room. Confirm that modal once, then require the actual Treasure Map.
      let returned=await autoMapWaitReturnedFromLights(2600);
      if (!returned) {
        const modal=treasureModalRoot(null);
        if (modal) {
          const action=autoMapModalPrimaryButton(modal,10);
          if (action) {
            await minigameHumanPause('confirm',{module:'auto-map',label:'lights-return-map'});
            if (autoMapEnabled() && lightsFinalRewardClaimed) {
              dispatchAutoMapTap(action,'auto-map-confirm-lights-return-map');
              autoMapLastActionAt=Date.now();
              returned=await autoMapWaitReturnedFromLights(5200);
            }
          }
        }
      }

      if (!returned) {
        autoMapRetryNotBefore=Date.now()+1400;
        autoMapStatus('жду карту после ламп',{
          revision:HK_LIGHTS_MAP_RETURN_REV
        });
        return false;
      }

      lightsFinalRewardClaimed=false;
      lightsFinalRewardClaimedAt=0;
      autoMapReturnNotBefore=Date.now()+350;
      autoMapCurrentLot='';
      lastSignature='';
      recordDiagnostic('lights-map-return-complete',{
        revision:HK_LIGHTS_MAP_RETURN_REV,
        method:'back-control',
        activeCells:autoMapActiveCellCount()
      });
      setTimeout(()=>{
        checkPuzzle();
        void runAutoMapTick('lights-returned-map');
      },420);
      return true;
    }

"""
if s.count(anchor)!=1:
    raise SystemExit("autoMapExitButton anchor missing")
s=s.replace(anchor,anchor+insert,1)

# Prioritize the strict post-reward return before any generic reward/room handling.
old_try="""      autoMapRunning=true;
      const runId=autoMapRunId;
      try {
        // Never let an instruction/reward overlay block an existing module.
        if (treasureRewardButton()) {
"""
new_try="""      autoMapRunning=true;
      const runId=autoMapRunId;
      try {
        // Lights room has a strict handoff: claim the central/main reward first,
        // then return to Treasure Map, then resume traversal. Do not treat the
        // persistent activated reward tile as unfinished work.
        if (lightsFinalRewardClaimed && getSignature().startsWith('LIGHTS|')) {
          return await autoMapReturnFromCompletedLights();
        }

        // Never let an instruction/reward overlay block an existing module.
        if (treasureRewardButton()) {
"""
rep(old_try,new_try,"strict lights map return priority")

# Reset claimed state only once the screen really leaves Lights.
old_check="""      const isLights=signature.startsWith('LIGHTS|');
      const isBattle=signature.startsWith('BATTLE|');
"""
new_check="""      const isLights=signature.startsWith('LIGHTS|');
      if (!isLights && lightsFinalRewardClaimed) {
        lightsFinalRewardClaimed=false;
        lightsFinalRewardClaimedAt=0;
        recordDiagnostic('lights-final-reward-reset',{
          revision:HK_LIGHTS_MAP_RETURN_REV,
          reason:'left-lights-screen'
        });
      }
      const isBattle=signature.startsWith('BATTLE|');
"""
rep(old_check,new_check,"reset claimed after leaving lights")

rep("      lightsRewardClaimRevision:HK_LIGHTS_REWARD_CLAIM_REV,\n      start,",
    "      lightsRewardClaimRevision:HK_LIGHTS_REWARD_CLAIM_REV,\n      lightsMapReturnRevision:HK_LIGHTS_MAP_RETURN_REV,\n      start,",
    "export map return revision")

for marker in [
    "// @version      1.18.35",
    "const BUILD_VERSION = '1.18.35';",
    "lights-map-return-after-main-reward-20260927-r1",
    "let lightsFinalRewardClaimed = false;",
    "function autoMapCompletedLightsBackButton()",
    "async function autoMapReturnFromCompletedLights()",
    "lights-return-map-back",
    "lights-map-return-complete",
    "if (lightsFinalRewardClaimed && getSignature().startsWith('LIGHTS|'))",
    "lights-reward-bottom-action-20260927-r1",
    "lights-stable-plan-20260927-r1",
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("LIGHTS_MAP_RETURN_1_18_35=PASS")
