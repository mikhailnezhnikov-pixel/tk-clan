# build-trigger: 1.18.07 minigame flow fixes
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
    "// @version      1.18.06",
    "// @version      1.18.07\n"
    "// @release-note Мини-игры: лампочки теперь забирают итоговое хранилище; сундуки сначала полностью раскапывают доступные клетки; автобой не атакует скрытое поле до входа в сражение; рыбалка получила авторежим с приоритетом редких/выгодных типов воды и пересчётом после каждого улова.",
    "version"
)
rep("const BUILD_VERSION = '1.18.06';","const BUILD_VERSION = '1.18.07';","build")

rep(
    "  const HK_LIGHTS_AUTO_REV = 'lights-modal-confirm-20260926-r2';",
    "  const HK_LIGHTS_AUTO_REV = 'lights-modal-confirm-20260926-r2';\n"
    "  const HK_LIGHTS_FINAL_REWARD_REV = 'lights-final-reward-20260926-r1';\n"
    "  const HK_CHEST_FULL_DIG_REV = 'chest-full-dig-first-20260926-r1';\n"
    "  const HK_BATTLE_ENTRY_GUARD_REV = 'battle-entry-before-auto-20260926-r1';\n"
    "  const HK_FISHING_AUTO_REV = 'fishing-value-priority-auto-20260926-r1';",
    "minigame markers"
)

rep(
    """    let lightsAutoRunning = false;
    let lightsAutoRunId = 0;
    let lightsAutoToggle = null;
""",
    """    let lightsAutoRunning = false;
    let lightsAutoRunId = 0;
    let lightsAutoToggle = null;
    const FISHING_AUTO_STORAGE_KEY = 'hk:fishing:auto-click:v1';
    const FISHING_ACTION_TIMEOUT_MS = 4200;
    let fishingAutoRunning = false;
    let fishingAutoRunId = 0;
    let fishingAutoToggle = null;
""",
    "fishing state"
)

# ---------- Lights final reward ----------
anchor="""    async function runLightsModalStep(before,target,slot,runId) {
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
insert="""    function lightsRewardElement() {
      return [...document.querySelectorAll('[data-lot-id*="mf_fairlot_lights_out_reward_slot"]')]
        .find(element=>visible(element)) || null;
    }

    function lightsRewardModalRoot() {
      const candidates=[...document.querySelectorAll('[role="dialog"],[aria-modal="true"],[class*="modal"],[class*="popup"],[class*="dialog"],div')]
        .filter(element=>visible(element))
        .filter(element=>/активированное\\s+хранилище|activated\\s+storage/i.test(clean(element.innerText||element.textContent||'')))
        .map(element=>{
          const rect=element.getBoundingClientRect?.() || {width:0,height:0};
          return {element,area:rect.width*rect.height};
        })
        .filter(row=>row.area>40000 && row.area<window.innerWidth*window.innerHeight*0.98)
        .sort((a,b)=>a.area-b.area);
      return candidates[0]?.element || null;
    }

    function lightsRewardClaimButton(root) {
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

    async function waitLightsRewardModal(runId,timeoutMs=2800) {
      const started=Date.now();
      while (Date.now()-started<timeoutMs) {
        if (runId!==lightsAutoRunId || !lightsAutoEnabled()) return null;
        const root=lightsRewardModalRoot();
        if (root) return root;
        await new Promise(resolve=>setTimeout(resolve,80));
      }
      return null;
    }

    async function waitLightsRewardAck(runId,timeoutMs=3200) {
      const started=Date.now();
      while (Date.now()-started<timeoutMs) {
        if (runId!==lightsAutoRunId || !lightsAutoEnabled()) return null;
        const button=lightsAcknowledgeButton(lightsRewardModalRoot());
        if (button) return button;
        await new Promise(resolve=>setTimeout(resolve,90));
      }
      return null;
    }

    async function runLightsFinalReward(runId,steps) {
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

    function lightsShouldAuto() {
      return lightsNeedsAuto() || !!lightsRewardElement();
    }

"""
need(anchor,"lights modal step anchor")
s=s.replace(anchor,anchor+insert,1)

rep(
    """          if (solution.length===0) {
            recordDiagnostic('lights-auto-complete',{revision:HK_LIGHTS_AUTO_REV,steps,reason:'solved'});
            return true;
          }
""",
    """          if (solution.length===0) {
            const rewardResult=await runLightsFinalReward(runId,steps);
            if (!rewardResult.ok) {
              if (runId!==lightsAutoRunId || !lightsAutoEnabled()) return false;
              return failLightsAuto(rewardResult.reason,{steps});
            }
            recordDiagnostic('lights-auto-complete',{
              revision:HK_LIGHTS_AUTO_REV,
              steps,
              reason:rewardResult.claimed?'solved-and-reward-claimed':'solved'
            });
            return true;
          }
""",
    "lights final reward after solve"
)

# ---------- Chest full dig first ----------
rep(
    """        let priority=digging ? 100 : 300;
        if (lotId==='mf_treasurelot_chest_type_03') priority+=40;
        else if (lotId==='mf_treasurelot_chest_type_02') priority+=30;
        else if (lotId==='mf_treasurelot_chest_type_015') priority+=20;
        else if (lotId==='mf_treasurelot_chest_type_01') priority+=10;
""",
    """        // Canon: completely excavate every currently affordable digging spot
        // before spending time/resources on already uncovered chests.
        // Key chests remain available as a recovery path when energy is below 5;
        // if they return energy, digging immediately becomes the top priority again.
        let priority=digging ? 1000 : 300;
        if (lotId==='mf_treasurelot_chest_type_03') priority+=40;
        else if (lotId==='mf_treasurelot_chest_type_02') priority+=30;
        else if (lotId==='mf_treasurelot_chest_type_015') priority+=20;
        else if (lotId==='mf_treasurelot_chest_type_01') priority=180;
""",
    "chest full dig priority"
)

# ---------- Battle entry guard ----------
battle_anchor="""    function battleElementForSlot(slot) {
      const elements=[...document.querySelectorAll('[data-lot-id*="mf_treasurelot_enemy_type_"]')];
      return elements.find(element=>{
        const id=element.getAttribute('data-lot-id')||'';
        const match=id.match(/enemy_type_(01|02|03|04)_(\d+)_sl(\d+)/);
        return !!match && Number(match[3])===Number(slot);
      }) || null;
    }

"""
battle_insert="""    function battleSwordElement() {
      return [...document.querySelectorAll('[data-lot-id^="mf_treasurelot_sword_"]')]
        .find(element=>visible(element)) || null;
    }

    function battleEntryButton() {
      const sword=battleSwordElement();
      if (!sword) return null;
      const sr=sword.getBoundingClientRect?.();
      if (!sr) return null;
      const candidates=[...sword.querySelectorAll('button,[role="button"],a,div')]
        .filter(element=>element!==sword && visible(element) && !element.disabled)
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const rect=element.getBoundingClientRect?.() || {width:0,height:0,top:0};
          const style=getComputedStyle(element);
          const actionable=element.matches?.('button,[role="button"],a') || !!element.onclick || style.cursor==='pointer';
          const hasPlay=!!element.querySelector?.('svg,img') || /▶|►|play|start|начать|в\\s*бой/i.test(text);
          let score=actionable?40:0;
          if (hasPlay) score+=100;
          if (rect.width>=sr.width*0.45 && rect.height>=30) score+=70;
          if (rect.top>=sr.top+sr.height*0.55) score+=70;
          if (/\\d+/.test(text) && !/start|начать|бой/i.test(text)) score-=100;
          return {element,score,rect};
        })
        .filter(row=>row.score>=150)
        .sort((a,b)=>b.score-a.score);
      return candidates[0]?.element || null;
    }

    function battleCoveredVisualCount() {
      const enemies=[...document.querySelectorAll('[data-lot-id*="mf_treasurelot_enemy_type_"]')].filter(visible);
      let hidden=0;
      for (const enemy of enemies) {
        const assets=[
          ...[...enemy.querySelectorAll?.('img')||[]].map(img=>String(img.src||'')+' '+String(img.alt||'')),
          String(getComputedStyle(enemy).backgroundImage||'')
        ].join(' ').toLowerCase();
        if (/hidden|back|unknown|bones|bone|skull|closed/.test(assets)) hidden+=1;
      }
      return {total:enemies.length,hidden};
    }

    function battleNeedsEntry() {
      if (battleEntryButton()) return true;
      const covered=battleCoveredVisualCount();
      return covered.total>=4 && covered.hidden>=Math.ceil(covered.total*0.6);
    }

    async function waitBattleEntered(runId,timeoutMs=3600) {
      const started=Date.now();
      while (Date.now()-started<timeoutMs) {
        if (runId!==battleAutoRunId || !battleAutoEnabled()) return false;
        if (!battleNeedsEntry()) return true;
        await new Promise(resolve=>setTimeout(resolve,100));
      }
      return false;
    }

    async function runBattleEntry() {
      if (!battleAutoEnabled() || battleAutoRunning) return false;
      const button=battleEntryButton();
      if (!button) {
        recordDiagnostic('battle-entry-wait',{
          revision:HK_BATTLE_ENTRY_GUARD_REV,
          reason:'covered-board-entry-button-not-found'
        });
        return false;
      }

      battleAutoRunning=true;
      const runId=++battleAutoRunId;
      try {
        if (!dispatchBattleTap(button,'battle-enter-minigame')) {
          recordDiagnostic('battle-entry-stop',{revision:HK_BATTLE_ENTRY_GUARD_REV,reason:'entry-tap-failed'});
          return false;
        }
        const entered=await waitBattleEntered(runId);
        recordDiagnostic('battle-entry-result',{
          revision:HK_BATTLE_ENTRY_GUARD_REV,
          entered
        });
        return entered;
      } finally {
        if (runId===battleAutoRunId) battleAutoRunning=false;
        lastSignature='';
        setTimeout(checkPuzzle,300);
      }
    }

"""
need(battle_anchor,"battle element anchor")
s=s.replace(battle_anchor,battle_anchor+battle_insert,1)

# ---------- Fishing ----------
fishing_anchor="""    function lightsBoardSignature(board = null) {
"""
fishing_code="""    function fishingAutoEnabled() {
      try {
        const saved=localStorage.getItem(FISHING_AUTO_STORAGE_KEY);
        return saved===null ? battleAutoEnabled() : saved==='1';
      } catch (_) { return false; }
    }

    function updateFishingAutoToggle(isFishing = null) {
      if (!fishingAutoToggle) return;
      const enabled=fishingAutoEnabled();
      fishingAutoToggle.textContent=enabled ? either('Авторыбалка: ВКЛ','Auto fishing: ON') : either('Авторыбалка: ВЫКЛ','Auto fishing: OFF');
      fishingAutoToggle.style.background=enabled ? '#40c85a' : '#2b2b2b';
      fishingAutoToggle.style.color=enabled ? '#071b0a' : '#fff';
      if (isFishing!==null) fishingAutoToggle.style.display=isFishing?'block':'none';
    }

    function setFishingAutoEnabled(enabled) {
      const value=!!enabled;
      try { localStorage.setItem(FISHING_AUTO_STORAGE_KEY,value?'1':'0'); } catch (_) {}
      if (!value) {
        fishingAutoRunId+=1;
        fishingAutoRunning=false;
      }
      updateFishingAutoToggle();
      recordDiagnostic('fishing-auto-toggle',{revision:HK_FISHING_AUTO_REV,enabled:value});
      if (value) {
        lastSignature='';
        setTimeout(checkPuzzle,0);
      }
      return value;
    }

    function ensureFishingAutoToggle(isFishing) {
      if (!fishingAutoToggle) {
        fishingAutoToggle=document.createElement('button');
        fishingAutoToggle.id='hkFishingAutoToggle';
        fishingAutoToggle.type='button';
        Object.assign(fishingAutoToggle.style,{
          position:'fixed',
          right:'14px',
          bottom:'154px',
          zIndex:'2147483646',
          border:'2px solid rgba(255,255,255,.75)',
          borderRadius:'18px',
          padding:'8px 11px',
          fontSize:'12px',
          fontWeight:'900',
          lineHeight:'1',
          boxShadow:'0 4px 14px rgba(0,0,0,.55)',
          WebkitTapHighlightColor:'transparent',
          touchAction:'manipulation'
        });
        fishingAutoToggle.addEventListener('click',event=>{
          event.preventDefault();
          event.stopPropagation();
          setFishingAutoEnabled(!fishingAutoEnabled());
        },true);
        (document.body || document.documentElement)?.appendChild(fishingAutoToggle);
      }
      updateFishingAutoToggle(!!isFishing);
    }

    function fishingElements() {
      return [...document.querySelectorAll('[data-lot-id*="mf_treasurelot_is_fishing_"]')]
        .filter(visible)
        .map((element,index)=>({
          element,
          index,
          lotId:String(element.getAttribute('data-lot-id')||'')
        }))
        .filter(row=>row.lotId);
    }

    function fishingTileCost(row) {
      const catalogRow=fairCatalog.find(item=>String(item?.lotId||'')===row.lotId);
      const parts=costParts(catalogRow?.cost).filter(part=>part.quantity>0);
      if (parts.length===1) return {id:parts[0].id,quantity:parts[0].quantity};

      const text=clean(row.element?.innerText||row.element?.textContent||'');
      const nums=[...text.matchAll(/(?:^|\\s)(\\d{1,2})(?=\\s|$)/g)]
        .map(match=>Number(match[1]))
        .filter(value=>value>=1 && value<=9);
      const quantity=nums.length ? nums[nums.length-1] : (/calm_water/.test(row.lotId)?1:2);
      return {id:'',quantity};
    }

    function fishingValueTier(lotId) {
      const id=String(lotId||'');
      if (/lamp_fish_water/.test(id)) return 600;
      if (/fishing_water/.test(id)) return 500;
      if (/creatures_water/.test(id)) return 440;
      if (/tornado_water/.test(id)) return 260;
      if (/calm_water/.test(id)) return 120;
      return 0;
    }

    function fishingTarget() {
      const rows=fishingElements().map(row=>{
        const cost=fishingTileCost(row);
        const tier=fishingValueTier(row.lotId);
        const roi=tier/Math.max(1,cost.quantity||1);
        return {...row,cost,tier,roi};
      }).filter(row=>row.tier>0);

      rows.sort((a,b)=>
        b.tier-a.tier ||
        b.roi-a.roi ||
        (a.cost.quantity||99)-(b.cost.quantity||99) ||
        a.index-b.index
      );
      return rows[0] || null;
    }

    function fishingSignature() {
      return 'FISHING|'+fishingElements()
        .map(row=>row.lotId+'#'+clean(row.element.className||''))
        .join('|');
    }

    async function waitFishingChange(before,runId,timeoutMs=FISHING_ACTION_TIMEOUT_MS) {
      const started=Date.now();
      while (Date.now()-started<timeoutMs) {
        if (runId!==fishingAutoRunId || !fishingAutoEnabled()) return false;
        if (fishingSignature()!==before) return true;
        await new Promise(resolve=>setTimeout(resolve,100));
      }
      return false;
    }

    function failFishingAuto(reason,data={}) {
      try { localStorage.setItem(FISHING_AUTO_STORAGE_KEY,'0'); } catch (_) {}
      fishingAutoRunId+=1;
      fishingAutoRunning=false;
      updateFishingAutoToggle();
      recordDiagnostic('fishing-auto-stop',{revision:HK_FISHING_AUTO_REV,reason,...data});
      return false;
    }

    async function runFishingAuto() {
      if (!fishingAutoEnabled() || fishingAutoRunning || battleAutoRunning || chestAutoRunning || lightsAutoRunning) return false;
      const target=fishingTarget();
      if (!target) return false;

      fishingAutoRunning=true;
      const runId=++fishingAutoRunId;
      const before=fishingSignature();
      recordDiagnostic('fishing-auto-start',{
        revision:HK_FISHING_AUTO_REV,
        lotId:target.lotId,
        tier:target.tier,
        roi:target.roi,
        cost:target.cost
      });

      try {
        if (!dispatchBattleTap(target.element,'fishing-open-'+target.lotId)) {
          return failFishingAuto('target-tap-failed',{lotId:target.lotId});
        }

        // Some water cards execute directly; others open the standard purchase modal.
        const directStarted=Date.now();
        while (Date.now()-directStarted<700) {
          if (runId!==fishingAutoRunId || !fishingAutoEnabled()) return false;
          if (fishingSignature()!==before) {
            recordDiagnostic('fishing-auto-complete',{revision:HK_FISHING_AUTO_REV,lotId:target.lotId,mode:'direct'});
            return true;
          }
          await new Promise(resolve=>setTimeout(resolve,80));
        }

        const modal=await (async()=>{
          const started=Date.now();
          while (Date.now()-started<2200) {
            if (runId!==fishingAutoRunId || !fishingAutoEnabled()) return null;
            const root=treasureModalRoot(target.cost);
            if (root) return root;
            await new Promise(resolve=>setTimeout(resolve,80));
          }
          return null;
        })();

        if (!modal) return failFishingAuto('modal-missing',{lotId:target.lotId});

        const action=await (async()=>{
          const started=Date.now();
          while (Date.now()-started<1800) {
            if (runId!==fishingAutoRunId || !fishingAutoEnabled()) return null;
            const button=treasureActionButton(modal,target.cost);
            if (button) return button;
            await new Promise(resolve=>setTimeout(resolve,80));
          }
          return null;
        })();

        if (!action || !dispatchBattleTap(action,'fishing-confirm-'+target.lotId)) {
          return failFishingAuto('action-missing',{lotId:target.lotId,cost:target.cost});
        }

        const changed=await waitFishingChange(before,runId);
        await new Promise(resolve=>setTimeout(resolve,220));
        const rewards=await dismissTreasureRewards(runId);
        if (!changed && rewards===0) {
          return failFishingAuto('field-no-change',{lotId:target.lotId});
        }

        recordDiagnostic('fishing-auto-complete',{
          revision:HK_FISHING_AUTO_REV,
          lotId:target.lotId,
          tier:target.tier,
          cost:target.cost,
          rewardsDismissed:rewards
        });
        return true;
      } finally {
        if (runId===fishingAutoRunId) fishingAutoRunning=false;
        lastSignature='';
        setTimeout(checkPuzzle,300);
      }
    }

"""
need(fishing_anchor,"fishing insertion anchor")
s=s.replace(fishing_anchor,fishing_code+fishing_anchor,1)

# getSignature: add fishing detection before chest detection.
rep(
    """      const chestRows=treasureChestElements();
      if (chestRows.length>=3) return treasureChestSignature();
      return 'NONE';
""",
    """      const fishingRows=fishingElements();
      if (fishingRows.length>=3) return fishingSignature();

      const chestRows=treasureChestElements();
      if (chestRows.length>=3) return treasureChestSignature();
      return 'NONE';
""",
    "fishing signature"
)

# checkPuzzle: contexts + guarded battle entry + fishing auto + final lights reward.
rep(
    """      const isLights=signature.startsWith('LIGHTS|');
      const isBattle=signature.startsWith('BATTLE|');
      const isBattleReward=signature.startsWith('BATTLE_REWARD');
      const isChests=signature.startsWith('CHESTS|');
      const battleContext=isBattle || isBattleReward || !!document.querySelector('[data-lot-id^="mf_treasurelot_sword_"]');
      ensureBattleAutoToggle(battleContext);
      ensureChestAutoToggle(isChests);
      ensureLightsAutoToggle(isLights);
      if (battleAutoRunning || chestAutoRunning || lightsAutoRunning) return;
""",
    """      const isLights=signature.startsWith('LIGHTS|');
      const isBattle=signature.startsWith('BATTLE|');
      const isBattleReward=signature.startsWith('BATTLE_REWARD');
      const isFishing=signature.startsWith('FISHING|');
      const isChests=signature.startsWith('CHESTS|');
      const battleContext=isBattle || isBattleReward || !!document.querySelector('[data-lot-id^="mf_treasurelot_sword_"]');
      ensureBattleAutoToggle(battleContext);
      ensureChestAutoToggle(isChests);
      ensureLightsAutoToggle(isLights);
      ensureFishingAutoToggle(isFishing);
      if (battleAutoRunning || chestAutoRunning || lightsAutoRunning || fishingAutoRunning) return;
""",
    "check contexts"
)

rep(
    """      if (isLights) {
        runLights();
        if (lightsAutoEnabled() && !lightsAutoRunning && lightsNeedsAuto()) void runLightsAuto();
        return;
      }
      if (isBattle) { runBattle(); return; }
      if (isBattleReward && battleAutoEnabled()) { void runBattleVictoryClaim(); return; }
      if (isChests && chestAutoEnabled()) void runTreasureChestAuto();
""",
    """      if (isLights) {
        runLights();
        if (lightsAutoEnabled() && !lightsAutoRunning && lightsShouldAuto()) void runLightsAuto();
        return;
      }
      if (isBattle) {
        if (battleAutoEnabled() && battleNeedsEntry()) { void runBattleEntry(); return; }
        runBattle();
        return;
      }
      if (isBattleReward && battleAutoEnabled()) { void runBattleVictoryClaim(); return; }
      if (isFishing && fishingAutoEnabled()) { void runFishingAuto(); return; }
      if (isChests && chestAutoEnabled()) void runTreasureChestAuto();
""",
    "check flow"
)

# stop/export fishing state.
rep(
    """      lightsAutoRunId += 1;
      lightsAutoRunning = false;
      clearNumbers();
      try { battleAutoToggle?.remove(); } catch (_) {}
      try { chestAutoToggle?.remove(); } catch (_) {}
      try { lightsAutoToggle?.remove(); } catch (_) {}
      battleAutoToggle = null;
      chestAutoToggle = null;
      lightsAutoToggle = null;
""",
    """      lightsAutoRunId += 1;
      lightsAutoRunning = false;
      fishingAutoRunId += 1;
      fishingAutoRunning = false;
      clearNumbers();
      try { battleAutoToggle?.remove(); } catch (_) {}
      try { chestAutoToggle?.remove(); } catch (_) {}
      try { lightsAutoToggle?.remove(); } catch (_) {}
      try { fishingAutoToggle?.remove(); } catch (_) {}
      battleAutoToggle = null;
      chestAutoToggle = null;
      lightsAutoToggle = null;
      fishingAutoToggle = null;
""",
    "stop fishing state"
)

rep(
    """      lightsAutoRevision:HK_LIGHTS_AUTO_REV,
      start,
""",
    """      lightsAutoRevision:HK_LIGHTS_AUTO_REV,
      lightsFinalRewardRevision:HK_LIGHTS_FINAL_REWARD_REV,
      fishingAutoRevision:HK_FISHING_AUTO_REV,
      start,
""",
    "export revisions"
)

rep(
    """      get autoLightsEnabled(){return lightsAutoEnabled();},
      setAutoLightsEnabled:setLightsAutoEnabled,
      get running(){return intervalId !== null;}
""",
    """      get autoLightsEnabled(){return lightsAutoEnabled();},
      setAutoLightsEnabled:setLightsAutoEnabled,
      get autoFishingEnabled(){return fishingAutoEnabled();},
      setAutoFishingEnabled:setFishingAutoEnabled,
      get running(){return intervalId !== null;}
""",
    "export fishing"
)

for marker in [
    "// @version      1.18.07",
    "const BUILD_VERSION = '1.18.07';",
    "lights-final-reward-20260926-r1",
    "mf_fairlot_lights_out_reward_slot",
    "lights-final-reward-claim",
    "chest-full-dig-first-20260926-r1",
    "let priority=digging ? 1000 : 300;",
    "battle-entry-before-auto-20260926-r1",
    "battle-enter-minigame",
    "battleNeedsEntry",
    "fishing-value-priority-auto-20260926-r1",
    "Авторыбалка: ВКЛ",
    "mf_treasurelot_is_fishing_",
    "lamp_fish_water",
    "fishing_water",
    "creatures_water",
    "tornado_water",
    "calm_water",
    "runFishingAuto",
    "lights-modal-confirm-20260926-r2",
    "chest-auto-dig-open-20260926-r1",
    "battle-auto-click-toggle-20260926-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

target.write_text(s,encoding="utf-8")
print("MINIGAME_FLOW_FIXES_1_18_07=PASS")
