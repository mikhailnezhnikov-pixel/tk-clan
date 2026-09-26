# build-trigger: 1.18.16 treasure auto map r1
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
    "// @version      1.18.15",
    "// @version      1.18.16\n"
    "// @release-note Карта Сокровищ: добавлен единый режим «Автокарта». Он проходит активные клетки по одной, подтверждает стоимость, забирает обычные награды, передаёт бой/рыбалку/торговца/лампочки/сундуки существующим авто-модулям, проходит treasury room и переходы лабиринта, после каждой комнаты возвращается к карте и пересчитывает доступные клетки. 409 обрабатывается пересканированием, 429/5xx — паузой без слепых повторных кликов.",
    "version"
)
rep("const BUILD_VERSION = '1.18.15';","const BUILD_VERSION = '1.18.16';","build")

# Keep all prior revisions and add the orchestrator marker next to the treasure recorder.
rep(
    "  const HK_TREASURE_RUN_RECORDER_STABILITY_REV='treasure-run-recorder-stability-blockers-20260926-r2';",
    "  const HK_TREASURE_RUN_RECORDER_STABILITY_REV='treasure-run-recorder-stability-blockers-20260926-r2';\n"
    "  const HK_TREASURE_AUTO_MAP_REV='treasure-auto-map-orchestrator-20260926-r1';",
    "auto map revision"
)

# Teach the shared game-response observer about 429 as a transient minigame/map error.
rep(
    "(response.status===409 || response.status>=500)",
    "(response.status===409 || response.status===429 || response.status>=500)",
    "fetch 429 observer"
)
rep(
    "(this.status===409 || this.status>=500)",
    "(this.status===409 || this.status===429 || this.status>=500)",
    "xhr 429 observer"
)

anchor="""    function getSignature() {
"""
helpers=r'''    // ----- Full Treasure Map orchestrator -----
    const AUTO_MAP_STORAGE_KEY='hk:treasure:auto-map:v1';
    const AUTO_MAP_LOOP_MS=420;
    const AUTO_MAP_ACTION_GAP_MS=850;
    const AUTO_MAP_MODAL_TIMEOUT_MS=2600;
    const AUTO_MAP_SETTLE_TIMEOUT_MS=5200;
    const AUTO_MAP_MAX_ACTIONS=240;
    let autoMapRunning=false;
    let autoMapRunId=0;
    let autoMapToggle=null;
    let autoMapIntervalId=null;
    let autoMapLastActionAt=0;
    let autoMapRetryNotBefore=0;
    let autoMapActionCount=0;
    let autoMapCurrentLot='';
    let autoMapPreviousModes=null;
    let autoMapLastStatus='';

    function autoMapEnabled() {
      try{return localStorage.getItem(AUTO_MAP_STORAGE_KEY)==='1';}
      catch(_){return false;}
    }

    function autoMapModulesRunning() {
      return !!(battleAutoRunning || chestAutoRunning || lightsAutoRunning || fishingAutoRunning || traderAutoRunning);
    }

    function autoMapCaptureModes() {
      if (autoMapPreviousModes) return;
      autoMapPreviousModes={
        battle:battleAutoEnabled(),
        chests:chestAutoEnabled(),
        lights:lightsAutoEnabled(),
        fishing:fishingAutoEnabled(),
        trader:traderAutoEnabled()
      };
    }

    function autoMapEnableModules() {
      autoMapCaptureModes();
      if (!battleAutoEnabled()) setBattleAutoEnabled(true);
      if (!chestAutoEnabled()) setChestAutoEnabled(true);
      if (!lightsAutoEnabled()) setLightsAutoEnabled(true);
      if (!fishingAutoEnabled()) setFishingAutoEnabled(true);
      if (!traderAutoEnabled()) setTraderAutoEnabled(true);
    }

    function autoMapRestoreModes() {
      const modes=autoMapPreviousModes;
      autoMapPreviousModes=null;
      if (!modes) return;
      if (battleAutoEnabled()!==modes.battle) setBattleAutoEnabled(modes.battle);
      if (chestAutoEnabled()!==modes.chests) setChestAutoEnabled(modes.chests);
      if (lightsAutoEnabled()!==modes.lights) setLightsAutoEnabled(modes.lights);
      if (fishingAutoEnabled()!==modes.fishing) setFishingAutoEnabled(modes.fishing);
      if (traderAutoEnabled()!==modes.trader) setTraderAutoEnabled(modes.trader);
    }

    function autoMapStatus(status,data={}) {
      const value=String(status||'');
      if (value!==autoMapLastStatus) {
        autoMapLastStatus=value;
        recordDiagnostic('treasure-auto-map-status',{
          revision:HK_TREASURE_AUTO_MAP_REV,
          status:value,
          actions:autoMapActionCount,
          ...data
        });
      }
      updateAutoMapToggle();
    }

    function updateAutoMapToggle(showOverride=null) {
      if (!autoMapToggle) return;
      const enabled=autoMapEnabled();
      const show=showOverride===null
        ? (enabled || treasureGuideScreenVisible())
        : !!showOverride;
      autoMapToggle.style.display=show?'block':'none';
      autoMapToggle.textContent=enabled
        ? 'Автокарта: ВКЛ'+(autoMapLastStatus?' · '+autoMapLastStatus:'')
        : 'Автокарта: ВЫКЛ';
      autoMapToggle.style.background=enabled?'#38c85a':'#292929';
      autoMapToggle.style.color=enabled?'#071b0a':'#fff';
      autoMapToggle.style.borderColor=enabled?'#d8ffe0':'rgba(255,255,255,.8)';
    }

    function ensureAutoMapToggle() {
      if (autoMapToggle) {
        updateAutoMapToggle();
        return;
      }
      if (!document.body) return;
      autoMapToggle=document.createElement('button');
      autoMapToggle.id='hkTreasureAutoMapToggle';
      autoMapToggle.type='button';
      Object.assign(autoMapToggle.style,{
        position:'fixed',
        right:'14px',
        bottom:'202px',
        zIndex:'2147483646',
        border:'2px solid rgba(255,255,255,.8)',
        borderRadius:'18px',
        padding:'8px 11px',
        fontSize:'12px',
        fontWeight:'900',
        lineHeight:'1',
        boxShadow:'0 4px 14px rgba(0,0,0,.55)',
        WebkitTapHighlightColor:'transparent',
        touchAction:'manipulation'
      });
      autoMapToggle.addEventListener('click',event=>{
        event.preventDefault();
        event.stopPropagation();
        setAutoMapEnabled(!autoMapEnabled());
      },true);
      document.body.appendChild(autoMapToggle);
      updateAutoMapToggle();
    }

    function autoMapFindTextButton(pattern,root=document) {
      const candidates=[...root.querySelectorAll('button,[role="button"],a,div,span')]
        .filter(element=>
          element &&
          element!==autoMapToggle &&
          element!==battleAutoToggle &&
          element!==chestAutoToggle &&
          element!==lightsAutoToggle &&
          element!==fishingAutoToggle &&
          element!==traderAutoToggle &&
          !element.disabled &&
          visible(element)
        )
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const rect=element.getBoundingClientRect?.() || {width:0,height:0,left:0,top:0};
          return {element,text,rect,area:rect.width*rect.height};
        })
        .filter(row=>pattern.test(row.text))
        .sort((a,b)=>a.area-b.area);
      return candidates[0]?.element || null;
    }

    function autoMapJourneyButton() {
      return autoMapFindTextButton(/^(?:Начать новое путешествие|Start new journey|New journey)$/i);
    }

    function autoMapExitButton() {
      return autoMapFindTextButton(/^(?:Покинуть локацию|Покинуть локацию\s*›?|Leave location|Exit location)$/i);
    }

    function autoMapBottomContinueButton() {
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

    function autoMapMapCards() {
      return [...document.querySelectorAll('[data-lot-id^="mf_treasurelot_active_sl"]')]
        .filter(visible)
        .map(element=>{
          const lotId=String(element.getAttribute('data-lot-id')||'');
          const text=clean(element.innerText||element.textContent||'').trim();
          const slotMatch=lotId.match(/_sl(\d+)/);
          const costMatch=text.match(/(?:^|\s)(\d{1,4})(?:\s|$)/);
          const style=getComputedStyle(element);
          const disabled=!!element.disabled ||
            element.getAttribute('aria-disabled')==='true' ||
            style.pointerEvents==='none' ||
            /disabled|locked|blocked/i.test(String(element.className||''));
          return {
            element,
            lotId,
            slot:slotMatch?Number(slotMatch[1]):999,
            cost:costMatch?Number(costMatch[1]):null,
            text,
            disabled
          };
        })
        .filter(row=>row.lotId && !row.disabled)
        .sort((a,b)=>a.slot-b.slot || (a.cost??9999)-(b.cost??9999));
    }

    function autoMapTreasuryChoice() {
      return [...document.querySelectorAll('[data-lot-id^="mf_fair_treasury_room_choose_way_"]')]
        .filter(visible)
        .map(element=>{
          const lotId=String(element.getAttribute('data-lot-id')||'');
          const m=lotId.match(/choose_way_(\d+)/);
          const text=clean(element.innerText||element.textContent||'').trim();
          const costMatch=text.match(/(?:^|\s)(\d{1,4})(?:\s|$)/);
          return {element,lotId,index:m?Number(m[1]):999,cost:costMatch?Number(costMatch[1]):null};
        })
        .sort((a,b)=>a.index-b.index)[0] || null;
    }

    function autoMapTreasuryChest() {
      return [...document.querySelectorAll('[data-lot-id*="mf_fairlot_minigame_treasury_room_big_chest"]')]
        .filter(visible)[0] || null;
    }

    function autoMapStateFingerprint() {
      const active=autoMapMapCards().map(row=>row.lotId).join(',');
      const treasury=[
        ...document.querySelectorAll('[data-lot-id^="mf_fair_treasury_room_choose_way_"],[data-lot-id*="mf_fairlot_minigame_treasury_room_big_chest"]')
      ].filter(visible).map(el=>el.getAttribute('data-lot-id')).join(',');
      const reward=treasureRewardButton();
      const exit=autoMapExitButton();
      const journey=autoMapJourneyButton();
      return [
        treasureGuideScreenVisible()?'MAP':'NOT_MAP',
        getSignature(),
        active,
        treasury,
        reward?clean(reward.innerText||reward.textContent||''):'',
        exit?'EXIT':'',
        journey?'DONE':''
      ].join('|');
    }

    function autoMapModalPrimaryButton(root,costHint=null) {
      if (!root) return null;
      if (Number.isFinite(costHint) && costHint>0) {
        const byCost=treasureActionButton(root,{id:'',quantity:Number(costHint)});
        if (byCost) return byCost;
      }
      const rr=root.getBoundingClientRect?.();
      if (!rr) return null;
      const centerX=rr.left+rr.width/2;
      const candidates=[...root.querySelectorAll('button,[role="button"],a,div,span')]
        .filter(element=>
          element &&
          element!==autoMapToggle &&
          !element.disabled &&
          visible(element)
        )
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const rect=element.getBoundingClientRect?.() || {width:0,height:0,left:0,top:0};
          const cx=rect.left+rect.width/2;
          let score=0;
          if (/^(?:\d{1,4}|▷|▶|►|play|start|open|открыть|получить|забрать|claim|collect)$/i.test(text)) score+=120;
          if (/▷|▶|►/.test(text)) score+=80;
          if (rect.top>=rr.top+rr.height*0.50) score+=60;
          if (rect.width>=rr.width*0.25 && rect.width<=rr.width*0.92) score+=45;
          if (rect.height>=36 && rect.height<=160) score+=35;
          if (Math.abs(cx-centerX)<=rr.width*0.30) score+=35;
          if (/закрыть|close|×|✕|назад|back|понятно|ok|okay/i.test(text)) score-=320;
          return {element,score,area:rect.width*rect.height};
        })
        .filter(row=>row.score>=120)
        .sort((a,b)=>b.score-a.score || a.area-b.area);
      return candidates[0]?.element || null;
    }

    async function autoMapWaitModal(runId,timeoutMs=AUTO_MAP_MODAL_TIMEOUT_MS) {
      const started=Date.now();
      while (Date.now()-started<timeoutMs) {
        if (runId!==autoMapRunId || !autoMapEnabled()) return null;
        const root=treasureModalRoot(null);
        if (root) return root;
        await new Promise(resolve=>setTimeout(resolve,80));
      }
      return null;
    }

    async function autoMapWaitActionGap() {
      const delay=Math.max(0,autoMapLastActionAt+AUTO_MAP_ACTION_GAP_MS-Date.now());
      if (delay>0) await new Promise(resolve=>setTimeout(resolve,delay));
    }

    function autoMapTransientError(since=0) {
      const error=minigameRecentHttpError(since,9000);
      if (!error) return null;
      const status=Number(error.status||0);
      if (![409,429].includes(status) && status<500) return null;
      return error;
    }

    function autoMapBackoff(error,reason='transient') {
      const status=Number(error?.status||0);
      const wait=status===409 ? 1200 :
        status===429 ? 3200 :
        status>=500 ? 5200 : 1800;
      autoMapRetryNotBefore=Date.now()+wait;
      autoMapStatus('пауза',{
        reason,
        httpStatus:status||null,
        waitMs:wait
      });
      return wait;
    }

    async function autoMapTapAndConfirm(element,label,costHint=null) {
      if (!element || !visible(element) || !autoMapEnabled()) return false;
      await autoMapWaitActionGap();
      if (!autoMapEnabled()) return false;
      if (autoMapActionCount>=AUTO_MAP_MAX_ACTIONS) {
        autoMapStatus('лимит');
        setAutoMapEnabled(false,{reason:'action-limit'});
        return false;
      }

      const runId=autoMapRunId;
      const before=autoMapStateFingerprint();
      const startedAt=Date.now();
      clearMinigameHttpError();
      autoMapActionCount+=1;
      autoMapLastActionAt=Date.now();

      if (!dispatchBattleTap(element,'auto-map-'+label)) {
        autoMapStatus('клик не прошёл',{label});
        return false;
      }

      // Map/minigame cards usually open a purchase modal. If state already changed,
      // treat it as a direct action and never click a second time blindly.
      let modal=null;
      const modalDeadline=Date.now()+AUTO_MAP_MODAL_TIMEOUT_MS;
      while (Date.now()<modalDeadline) {
        if (runId!==autoMapRunId || !autoMapEnabled()) return false;
        const error=autoMapTransientError(startedAt);
        if (error) {
          autoMapBackoff(error,'tap-http-error');
          return false;
        }
        modal=treasureModalRoot(null);
        if (modal) break;
        if (autoMapStateFingerprint()!==before) return true;
        await new Promise(resolve=>setTimeout(resolve,80));
      }

      if (!modal) {
        // No modal + no observed change: do not retry the same element immediately.
        autoMapRetryNotBefore=Date.now()+1400;
        autoMapStatus('пересканирую',{label,reason:'modal-missing'});
        return false;
      }

      let action=null;
      const actionDeadline=Date.now()+1800;
      while (Date.now()<actionDeadline) {
        if (runId!==autoMapRunId || !autoMapEnabled()) return false;
        action=autoMapModalPrimaryButton(modal,costHint);
        if (action) break;
        await new Promise(resolve=>setTimeout(resolve,80));
      }
      if (!action) {
        autoMapRetryNotBefore=Date.now()+1500;
        autoMapStatus('жду подтверждение',{label});
        return false;
      }

      autoMapLastActionAt=Date.now();
      if (!dispatchBattleTap(action,'auto-map-confirm-'+label)) {
        autoMapRetryNotBefore=Date.now()+1400;
        return false;
      }

      const settleStarted=Date.now();
      while (Date.now()-settleStarted<AUTO_MAP_SETTLE_TIMEOUT_MS) {
        if (runId!==autoMapRunId || !autoMapEnabled()) return false;
        const error=autoMapTransientError(startedAt);
        if (error) {
          autoMapBackoff(error,'confirm-http-error');
          return false;
        }
        if (autoMapStateFingerprint()!==before || !treasureModalRoot(null)) {
          await new Promise(resolve=>setTimeout(resolve,180));
          return true;
        }
        await new Promise(resolve=>setTimeout(resolve,100));
      }

      autoMapRetryNotBefore=Date.now()+1800;
      autoMapStatus('пересканирую',{label,reason:'no-state-change'});
      return false;
    }

    async function autoMapDismissReward() {
      const button=treasureRewardButton();
      if (!button || autoMapModulesRunning()) return false;
      await autoMapWaitActionGap();
      if (!autoMapEnabled()) return false;
      autoMapActionCount+=1;
      autoMapLastActionAt=Date.now();
      const text=clean(button.innerText||button.textContent||'');
      const ok=dispatchBattleTap(button,'auto-map-reward-'+text.slice(0,30));
      if (ok) {
        autoMapStatus('награда');
        await new Promise(resolve=>setTimeout(resolve,340));
      }
      return ok;
    }

    function autoMapCurrentModuleComplete() {
      const signature=getSignature();
      if (signature.startsWith('LIGHTS|')) return !lightsShouldAuto();
      if (signature.startsWith('FISHING|')) return !fishingTarget();
      if (signature.startsWith('TRADER|')) return !traderTarget();
      if (signature.startsWith('CHESTS|')) return !treasureChestTarget();
      if (signature.startsWith('BATTLE')) return !!autoMapExitButton();
      if (signature==='NONE' && !treasureGuideScreenVisible()) return true;
      return false;
    }

    async function autoMapHandleExitOrContinue() {
      if (autoMapModulesRunning()) return false;
      const exit=autoMapExitButton();
      if (exit) {
        autoMapStatus('выход');
        return autoMapTapAndConfirm(exit,'leave-location',10);
      }
      if (!treasureGuideScreenVisible() && autoMapCurrentModuleComplete()) {
        const next=autoMapBottomContinueButton();
        if (next) {
          autoMapStatus('следующая комната');
          return autoMapTapAndConfirm(next,'room-continue',10);
        }
      }
      return false;
    }

    async function runAutoMapTick(source='loop') {
      if (!autoMapEnabled() || autoMapRunning) {
        ensureAutoMapToggle();
        return false;
      }
      ensureAutoMapToggle();

      if (Date.now()<autoMapRetryNotBefore) {
        autoMapStatus('пауза');
        return false;
      }

      if (autoMapModulesRunning()) {
        autoMapStatus('мини-игра');
        return false;
      }

      autoMapRunning=true;
      const runId=autoMapRunId;
      try {
        // Never let an instruction/reward overlay block an existing module.
        if (treasureRewardButton()) {
          await autoMapDismissReward();
          lastSignature='';
          setTimeout(checkPuzzle,80);
          return true;
        }

        // A completed Treasure Map is the terminal state: do not start a new map.
        if (treasureGuideScreenVisible() && autoMapJourneyButton()) {
          autoMapStatus('ГОТОВО');
          recordDiagnostic('treasure-auto-map-complete',{
            revision:HK_TREASURE_AUTO_MAP_REV,
            actions:autoMapActionCount,
            source
          });
          setAutoMapEnabled(false,{reason:'map-complete',preserveStatus:'ГОТОВО'});
          return true;
        }

        // Normal map traversal: lowest currently active slot first, then rescan.
        if (treasureGuideScreenVisible()) {
          const target=autoMapMapCards()[0];
          if (target) {
            autoMapCurrentLot=target.lotId;
            autoMapStatus('ячейка '+String(target.slot),{
              lotId:target.lotId,
              cost:target.cost
            });
            const ok=await autoMapTapAndConfirm(target.element,'map-'+target.lotId,target.cost);
            if (ok) {
              autoMapCurrentLot='';
              lastSignature='';
              setTimeout(checkPuzzle,100);
            }
            return ok;
          }
          autoMapStatus('жду карту');
          return false;
        }

        // Treasury room after the boss: first choose route 1 (recorded canonical run),
        // then open the big chest, collect reward and leave normally.
        const choice=autoMapTreasuryChoice();
        if (choice) {
          autoMapStatus('treasury путь');
          return autoMapTapAndConfirm(choice.element,'treasury-'+choice.lotId,choice.cost);
        }
        const treasuryChest=autoMapTreasuryChest();
        if (treasuryChest) {
          autoMapStatus('treasury сундук');
          return autoMapTapAndConfirm(treasuryChest,'treasury-big-chest',null);
        }

        // Existing puzzle modules own all clicks while their room is active.
        const signature=getSignature();
        if (signature.startsWith('LIGHTS|')) {
          autoMapStatus('лампочки');
          if (lightsAutoEnabled() && !lightsAutoRunning && lightsShouldAuto()) {
            lastSignature='';
            setTimeout(checkPuzzle,20);
          } else {
            await autoMapHandleExitOrContinue();
          }
          return true;
        }
        if (signature.startsWith('BATTLE')) {
          autoMapStatus('сражение');
          if (signature.startsWith('BATTLE_REWARD') && battleAutoEnabled()) {
            lastSignature='';
            setTimeout(checkPuzzle,20);
          } else if (autoMapExitButton()) {
            await autoMapHandleExitOrContinue();
          } else {
            lastSignature='';
            setTimeout(checkPuzzle,20);
          }
          return true;
        }
        if (signature.startsWith('FISHING|')) {
          autoMapStatus('рыбалка');
          if (fishingTarget()) {
            lastSignature='';
            setTimeout(checkPuzzle,20);
          } else {
            await autoMapHandleExitOrContinue();
          }
          return true;
        }
        if (signature.startsWith('TRADER|')) {
          autoMapStatus('торговец');
          if (traderTarget()) {
            lastSignature='';
            setTimeout(checkPuzzle,20);
          } else {
            await autoMapHandleExitOrContinue();
          }
          return true;
        }
        if (signature.startsWith('CHESTS|')) {
          autoMapStatus('сундуки');
          if (treasureChestTarget()) {
            lastSignature='';
            setTimeout(checkPuzzle,20);
          } else {
            await autoMapHandleExitOrContinue();
          }
          return true;
        }

        // Between rooms the only safe autonomous operation is a recorded exit/
        // continue control. Unknown screens are never blindly clicked.
        if (await autoMapHandleExitOrContinue()) return true;

        autoMapStatus('жду экран');
        return false;
      } finally {
        if (runId===autoMapRunId) autoMapRunning=false;
      }
    }

    function setAutoMapEnabled(enabled,meta={}) {
      const value=!!enabled;
      try{localStorage.setItem(AUTO_MAP_STORAGE_KEY,value?'1':'0');}catch(_){}
      autoMapRunId+=1;
      autoMapRunning=false;
      autoMapRetryNotBefore=0;
      autoMapCurrentLot='';

      if (value) {
        autoMapActionCount=0;
        autoMapLastStatus='';
        autoMapEnableModules();
        autoMapStatus('старт');
        setTimeout(()=>void runAutoMapTick('enable'),50);
      } else {
        const finalStatus=String(meta?.preserveStatus||'');
        autoMapRestoreModes();
        if (finalStatus) autoMapLastStatus=finalStatus;
        else if (meta?.reason && meta.reason!=='map-complete') autoMapLastStatus='стоп';
        recordDiagnostic('treasure-auto-map-toggle',{
          revision:HK_TREASURE_AUTO_MAP_REV,
          enabled:false,
          reason:String(meta?.reason||'manual'),
          actions:autoMapActionCount
        });
        updateAutoMapToggle();
      }

      recordDiagnostic('treasure-auto-map-toggle',{
        revision:HK_TREASURE_AUTO_MAP_REV,
        enabled:value,
        actions:autoMapActionCount
      });
      updateAutoMapToggle();
      return value;
    }

'''
need(anchor,"getSignature anchor")
s=s.replace(anchor,helpers+anchor,1)

# Puzzle solver must let AutoMap remove blocking "Понятно" overlays before a
# minigame module tries to tap through them.
rep(
    """    function checkPuzzle() {
      const signature = getSignature();
""",
    """    function checkPuzzle() {
      ensureAutoMapToggle();
      if (autoMapEnabled() && !autoMapModulesRunning() && treasureRewardButton()) {
        void runAutoMapTick('puzzle-overlay');
        return;
      }
      const signature = getSignature();
""",
    "checkPuzzle overlay guard"
)

# Start/stop the orchestrator loop together with the existing puzzle solver.
rep(
    """    function start() {
      if (intervalId !== null) return;
      initialTimerId = setTimeout(checkPuzzle,300);
      intervalId = setInterval(checkPuzzle,500);
      recordDiagnostic('puzzle-solver-start',{revision:HK_PUZZLE_SOLVER_REV});
    }
""",
    """    function start() {
      if (intervalId !== null) return;
      initialTimerId = setTimeout(checkPuzzle,300);
      intervalId = setInterval(checkPuzzle,500);
      if (autoMapIntervalId!==null) clearInterval(autoMapIntervalId);
      autoMapIntervalId=setInterval(()=>void runAutoMapTick('interval'),AUTO_MAP_LOOP_MS);
      ensureAutoMapToggle();
      if (autoMapEnabled()) {
        autoMapEnableModules();
        setTimeout(()=>void runAutoMapTick('resume'),120);
      }
      recordDiagnostic('puzzle-solver-start',{revision:HK_PUZZLE_SOLVER_REV});
    }
""",
    "start auto map loop"
)

rep(
    """      if (intervalId !== null) clearInterval(intervalId);
      initialTimerId = null;
      intervalId = null;
      lastSignature = '';
""",
    """      if (intervalId !== null) clearInterval(intervalId);
      if (autoMapIntervalId !== null) clearInterval(autoMapIntervalId);
      initialTimerId = null;
      intervalId = null;
      autoMapIntervalId = null;
      lastSignature = '';
""",
    "stop auto map interval"
)

rep(
    """      try { traderAutoToggle?.remove(); } catch (_) {}
      battleAutoToggle = null;
""",
    """      try { traderAutoToggle?.remove(); } catch (_) {}
      try { autoMapToggle?.remove(); } catch (_) {}
      battleAutoToggle = null;
""",
    "remove auto map toggle"
)

rep(
    """      traderAutoToggle = null;
      recordDiagnostic('puzzle-solver-stop',{revision:HK_PUZZLE_SOLVER_REV});
""",
    """      traderAutoToggle = null;
      autoMapToggle = null;
      recordDiagnostic('puzzle-solver-stop',{revision:HK_PUZZLE_SOLVER_REV});
""",
    "clear auto map toggle"
)

# Export the orchestrator for diagnostics/manual control.
rep(
    """      battleVisibleBoardRevision:HK_BATTLE_VISIBLE_BOARD_REV,
      start,
""",
    """      battleVisibleBoardRevision:HK_BATTLE_VISIBLE_BOARD_REV,
      treasureAutoMapRevision:HK_TREASURE_AUTO_MAP_REV,
      start,
""",
    "export auto map revision"
)

rep(
    """      get autoTraderEnabled(){return traderAutoEnabled();},
      setAutoTraderEnabled:setTraderAutoEnabled,
      get running(){return intervalId !== null;}
""",
    """      get autoTraderEnabled(){return traderAutoEnabled();},
      setAutoTraderEnabled:setTraderAutoEnabled,
      get autoMapEnabled(){return autoMapEnabled();},
      setAutoMapEnabled:setAutoMapEnabled,
      runAutoMapTick,
      get running(){return intervalId !== null;}
""",
    "export auto map controls"
)

for marker in [
    "// @version      1.18.16",
    "const BUILD_VERSION = '1.18.16';",
    "treasure-auto-map-orchestrator-20260926-r1",
    "Автокарта: ВКЛ",
    "Автокарта: ВЫКЛ",
    "mf_treasurelot_active_sl",
    "mf_fair_treasury_room_choose_way_",
    "mf_fairlot_minigame_treasury_room_big_chest",
    "treasure-auto-map-complete",
    "http-429-rate-limit",
    "response.status===409 || response.status===429 || response.status>=500",
    "this.status===409 || this.status===429 || this.status>=500",
    "rumors-hunter-coordinator-kokkaras-v40-20260926-r4",
    "treasure-run-recorder-stability-blockers-20260926-r2",
    "battle-visible-board-active-20260926-r1",
    "trader-fishing-stability-20260926-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

target.write_text(s,encoding="utf-8")
print("TREASURE_AUTO_MAP_1_18_16=PASS")
