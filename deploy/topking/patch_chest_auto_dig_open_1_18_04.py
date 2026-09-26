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
    "// @version      1.18.03",
    "// @version      1.18.04\n"
    "// @release-note Сундуки: в общем HK-скрипте добавлена автоцепочка «раскопать → открыть найденный сундук → забрать награду». Перед каждым действием проверяется живой баланс: раскоп/обычный найденный сундук — 5 энергии, зелёный — 1 обычный ключ, золотой — 1 необычный ключ, красный — 1 эпический ключ. Недоступные сундуки пропускаются.",
    "version"
)
rep("const BUILD_VERSION = '1.18.03';","const BUILD_VERSION = '1.18.04';","build")

rep(
    "  const HK_BATTLE_VICTORY_TAP_REV = 'battle-victory-tap-fallback-20260926-r1';",
    "  const HK_BATTLE_VICTORY_TAP_REV = 'battle-victory-tap-fallback-20260926-r1';\n"
    "  const HK_CHEST_AUTO_REV = 'chest-auto-dig-open-20260926-r1';",
    "chest auto marker"
)

old_state="""    const BATTLE_AUTO_STORAGE_KEY = 'hk:battle:auto-click:v1';
    const BATTLE_AUTO_SETTLE_MS = 260;
    const BATTLE_AUTO_CHANGE_TIMEOUT_MS = 4500;

    let lastSignature = '';
    let intervalId = null;
    let initialTimerId = null;
    let battleAutoRunning = false;
    let battleAutoRunId = 0;
    let battleAutoToggle = null;
"""
new_state="""    const BATTLE_AUTO_STORAGE_KEY = 'hk:battle:auto-click:v1';
    const CHEST_AUTO_STORAGE_KEY = 'hk:chests:auto-open:v1';
    const BATTLE_AUTO_SETTLE_MS = 260;
    const BATTLE_AUTO_CHANGE_TIMEOUT_MS = 4500;
    const CHEST_ACTION_TIMEOUT_MS = 3600;

    let lastSignature = '';
    let intervalId = null;
    let initialTimerId = null;
    let battleAutoRunning = false;
    let battleAutoRunId = 0;
    let battleAutoToggle = null;
    let chestAutoRunning = false;
    let chestAutoRunId = 0;
    let chestAutoToggle = null;
"""
rep(old_state,new_state,"chest state")

anchor="""    function ensureBattleAutoToggle(isBattle) {
      if (!battleAutoToggle) {
        battleAutoToggle=document.createElement('button');
        battleAutoToggle.id='hkBattleAutoToggle';
        battleAutoToggle.type='button';
        Object.assign(battleAutoToggle.style,{
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
        battleAutoToggle.addEventListener('click',event=>{
          event.preventDefault();
          event.stopPropagation();
          setBattleAutoEnabled(!battleAutoEnabled());
        },true);
        (document.body || document.documentElement)?.appendChild(battleAutoToggle);
      }
      updateBattleAutoToggle(!!isBattle);
    }

"""
insert="""    function chestAutoEnabled() {
      try {
        const saved=localStorage.getItem(CHEST_AUTO_STORAGE_KEY);
        return saved===null ? battleAutoEnabled() : saved==='1';
      } catch (_) { return false; }
    }

    function updateChestAutoToggle(isChest = null) {
      if (!chestAutoToggle) return;
      const enabled=chestAutoEnabled();
      chestAutoToggle.textContent=enabled ? either('Автосундуки: ВКЛ','Auto chests: ON') : either('Автосундуки: ВЫКЛ','Auto chests: OFF');
      chestAutoToggle.style.background=enabled ? '#40c85a' : '#2b2b2b';
      chestAutoToggle.style.color=enabled ? '#071b0a' : '#fff';
      if (isChest !== null) chestAutoToggle.style.display=isChest ? 'block' : 'none';
    }

    function setChestAutoEnabled(enabled) {
      const value=!!enabled;
      try { localStorage.setItem(CHEST_AUTO_STORAGE_KEY,value?'1':'0'); } catch (_) {}
      if (!value) {
        chestAutoRunId += 1;
        chestAutoRunning = false;
      }
      updateChestAutoToggle();
      recordDiagnostic('chest-auto-toggle',{revision:HK_CHEST_AUTO_REV,enabled:value});
      if (value) {
        lastSignature='';
        setTimeout(checkPuzzle,0);
      }
      return value;
    }

    function ensureChestAutoToggle(isChest) {
      if (!chestAutoToggle) {
        chestAutoToggle=document.createElement('button');
        chestAutoToggle.id='hkChestAutoToggle';
        chestAutoToggle.type='button';
        Object.assign(chestAutoToggle.style,{
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
        chestAutoToggle.addEventListener('click',event=>{
          event.preventDefault();
          event.stopPropagation();
          setChestAutoEnabled(!chestAutoEnabled());
        },true);
        (document.body || document.documentElement)?.appendChild(chestAutoToggle);
      }
      updateChestAutoToggle(!!isChest);
    }

"""
need(anchor,"battle toggle anchor")
s=s.replace(anchor,anchor+insert,1)

# Add chest automation helpers after the shared mobile-tap helpers, so we reuse
# the exact same touch/mouse synthesis that already works for battle modals.
tap_anchor="""    function battleVictoryElement() {
"""
chest_code="""    function treasureChestCost(lotId) {
      const id=String(lotId||'');
      const catalogRow=fairCatalog.find(row=>String(row?.lotId||'')===id);
      const liveParts=costParts(catalogRow?.cost).filter(part=>part.quantity>0);
      if (liveParts.length===1) return {id:liveParts[0].id,quantity:liveParts[0].quantity};

      if (/^mf_treasurelot_chest_digging_spot_sl\d+$/.test(id)) return {id:'item_treasurehunt_energy',quantity:5};
      if (id==='mf_treasurelot_chest_type_01') return {id:'item_treasurehunt_energy',quantity:5};
      if (id==='mf_treasurelot_chest_type_015') return {id:'item_treasurehunt_key_common',quantity:1};
      if (id==='mf_treasurelot_chest_type_02') return {id:'item_treasurehunt_key_uncommon',quantity:1};
      if (id==='mf_treasurelot_chest_type_03') return {id:'item_treasurehunt_key_epic',quantity:1};
      return null;
    }

    function treasureChestFairState() {
      return fairState('fair_mini_game_chests',fairDocument || playerDocument)
        || fairState('fair_mini_game_chests',playerDocument);
    }

    function treasureChestUnboughtCount(lotId) {
      const state=treasureChestFairState();
      if (!state) return null;
      const rows=(state.fair_slots||[]).filter(row=>String(row?.shop_lot_id||'')===String(lotId||''));
      if (!rows.length) return null;
      return rows.filter(row=>row?.is_bought!==true).length;
    }

    function treasureChestAffordable(cost) {
      if (!cost?.id || !(cost.quantity>0)) return false;
      const balance=walletAmount(cost.id);
      return balance!==null && balance>=cost.quantity;
    }

    function treasureChestElements() {
      const selector='[data-lot-id*="mf_treasurelot_chest_"]';
      return [...document.querySelectorAll(selector)]
        .filter(visible)
        .map(element=>({element,lotId:String(element.getAttribute('data-lot-id')||'')}))
        .filter(row=>row.lotId && !row.lotId.includes('_empty_spot') && !row.lotId.includes('_bought_'));
    }

    function treasureChestSignature() {
      const rows=treasureChestElements()
        .map(row=>{
          const rect=row.element.getBoundingClientRect?.() || {left:0,top:0,width:0,height:0};
          return row.lotId+'@'+Math.round(rect.left)+','+Math.round(rect.top)+'#'+clean(row.element.className||'');
        })
        .sort();
      const balances=[
        'item_treasurehunt_energy',
        'item_treasurehunt_key_common',
        'item_treasurehunt_key_uncommon',
        'item_treasurehunt_key_epic'
      ].map(id=>id+'='+String(walletAmount(id))).join(',');
      return 'CHESTS|'+rows.join('|')+'|'+balances;
    }

    function treasureChestTarget() {
      const rows=treasureChestElements();
      const candidates=[];
      rows.forEach((row,index)=>{
        const lotId=row.lotId;
        const cost=treasureChestCost(lotId);
        if (!cost || !treasureChestAffordable(cost)) return;
        const unbought=treasureChestUnboughtCount(lotId);
        if (unbought===0) return;
        const digging=/^mf_treasurelot_chest_digging_spot_sl\d+$/.test(lotId);
        const chest=/^mf_treasurelot_chest_type_(?:01|015|02|03)$/.test(lotId);
        if (!digging && !chest) return;
        let priority=digging ? 100 : 300;
        if (lotId==='mf_treasurelot_chest_type_03') priority+=40;
        else if (lotId==='mf_treasurelot_chest_type_02') priority+=30;
        else if (lotId==='mf_treasurelot_chest_type_015') priority+=20;
        else if (lotId==='mf_treasurelot_chest_type_01') priority+=10;
        candidates.push({...row,cost,digging,chest,priority,index});
      });
      candidates.sort((a,b)=>b.priority-a.priority || a.index-b.index);
      return candidates[0] || null;
    }

    function treasureModalRoot(cost) {
      const needle=String(cost?.id||'');
      const imgs=[...document.querySelectorAll('img')].filter(img=>visible(img) && (!needle || String(img.src||'').includes(needle)));
      const rows=[];
      for (const img of imgs) {
        let node=img;
        for (let depth=0;node && depth<10;depth++,node=node.parentElement) {
          const rect=node.getBoundingClientRect?.();
          if (!rect) continue;
          if (rect.width<Math.min(260,window.innerWidth*0.42) || rect.height<180) continue;
          if (rect.width>window.innerWidth*0.99 || rect.height>window.innerHeight*0.97) continue;
          rows.push({element:node,area:rect.width*rect.height});
        }
      }
      if (rows.length) return rows.sort((a,b)=>a.area-b.area)[0].element;

      const generic=[...document.querySelectorAll('[role="dialog"],[class*="modal"],[class*="popup"]')]
        .filter(visible)
        .map(element=>({element,rect:element.getBoundingClientRect?.()}))
        .filter(row=>row.rect && row.rect.width>=Math.min(260,window.innerWidth*0.42) && row.rect.height>=180)
        .sort((a,b)=>a.rect.width*a.rect.height-b.rect.width*b.rect.height);
      return generic[0]?.element || null;
    }

    function treasureActionButton(root,cost) {
      if (!root || !cost) return null;
      const rr=root.getBoundingClientRect?.();
      if (!rr) return null;
      const costText=String(cost.quantity);
      const itemId=String(cost.id||'');
      const centerX=rr.left+rr.width/2;
      const candidates=[...root.querySelectorAll('button,[role="button"],a,div,span')]
        .filter(element=>element && element!==chestAutoToggle && element!==battleAutoToggle && !element.disabled && visible(element))
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'');
          const images=[...element.querySelectorAll?.('img')||[]]
            .map(img=>String(img.alt||'')+' '+String(img.src||'')).join(' ');
          const rect=element.getBoundingClientRect?.() || {width:0,height:0,left:0,top:0};
          const cx=rect.left+rect.width/2;
          let score=0;
          if (itemId && images.includes(itemId)) score+=150;
          if (text===costText) score+=90;
          else if (new RegExp('(?:^|\\s)'+costText+'(?:\\s|$)').test(text)) score+=35;
          if (rect.width>=rr.width*0.28 && rect.width<=rr.width*0.90) score+=45;
          if (rect.height>=38 && rect.height<=150) score+=35;
          if (rect.top>=rr.top+rr.height*0.52) score+=45;
          if (Math.abs(cx-centerX)<=rr.width*0.28) score+=35;
          if (/закрыть|close|×|✕|назад|back|понятно|ok|okay/i.test(text)) score-=260;
          return {element,score,rect};
        })
        .filter(row=>row.score>=100)
        .sort((a,b)=>b.score-a.score || a.rect.width*a.rect.height-b.rect.width*b.rect.height);
      return candidates[0]?.element || null;
    }

    async function waitTreasureModal(cost,runId,timeoutMs=2400) {
      const started=Date.now();
      while (Date.now()-started<timeoutMs) {
        if (runId!==chestAutoRunId || !chestAutoEnabled()) return null;
        const root=treasureModalRoot(cost);
        if (root) return root;
        await new Promise(resolve=>setTimeout(resolve,80));
      }
      return null;
    }

    async function waitTreasureActionButton(root,cost,runId,timeoutMs=2200) {
      const started=Date.now();
      while (Date.now()-started<timeoutMs) {
        if (runId!==chestAutoRunId || !chestAutoEnabled()) return null;
        const button=treasureActionButton(root,cost);
        if (button) return button;
        await new Promise(resolve=>setTimeout(resolve,80));
      }
      return null;
    }

    function treasureRewardButton() {
      const exact=/^(?:понятно|ok|okay|got it|understood|забрать|получить|claim|collect|take|далее|continue)$/i;
      const candidates=[...document.querySelectorAll('button,[role="button"],a')]
        .filter(element=>element && element!==battleAutoToggle && element!==chestAutoToggle && !element.disabled && visible(element))
        .map(element=>({element,text:clean(element.innerText||element.textContent||'')}))
        .filter(row=>exact.test(row.text));
      return candidates[0]?.element || null;
    }

    async function dismissTreasureRewards(runId) {
      let clicked=0;
      for (let i=0;i<5;i++) {
        if (runId!==chestAutoRunId || !chestAutoEnabled()) break;
        const button=treasureRewardButton();
        if (!button) {
          await new Promise(resolve=>setTimeout(resolve,180));
          if (!treasureRewardButton()) break;
          continue;
        }
        dispatchBattleTap(button,'chest-reward-'+(i+1));
        clicked+=1;
        await new Promise(resolve=>setTimeout(resolve,280));
      }
      return clicked;
    }

    async function tapTreasureActionFallback(root,runId) {
      if (!root || runId!==chestAutoRunId || !chestAutoEnabled()) return false;
      const rr=root.getBoundingClientRect?.();
      if (!rr) return false;
      const x=rr.left+rr.width/2;
      for (const fraction of [0.88,0.83,0.92]) {
        if (runId!==chestAutoRunId || !chestAutoEnabled()) return false;
        if (dispatchBattleTapAt(x,rr.top+rr.height*fraction,'chest-action-fallback-'+fraction)) {
          await new Promise(resolve=>setTimeout(resolve,360));
          if (!treasureModalRoot(null)) return true;
        }
      }
      return false;
    }

    async function runTreasureChestAuto() {
      if (!chestAutoEnabled() || chestAutoRunning || battleAutoRunning) return false;
      const target=treasureChestTarget();
      if (!target) return false;

      chestAutoRunning=true;
      const runId=++chestAutoRunId;
      const beforeSignature=treasureChestSignature();
      const beforeBalance=walletAmount(target.cost.id);
      recordDiagnostic('chest-auto-start',{
        revision:HK_CHEST_AUTO_REV,
        lotId:target.lotId,
        cost:target.cost,
        balance:beforeBalance,
        digging:target.digging
      });
      try {
        if (runId!==chestAutoRunId || !chestAutoEnabled()) return false;
        dispatchBattleTap(target.element,target.digging?'chest-dig-spot':'chest-open-card');

        const modal=await waitTreasureModal(target.cost,runId);
        if (!modal) {
          recordDiagnostic('chest-auto-stop',{revision:HK_CHEST_AUTO_REV,reason:'modal-missing',lotId:target.lotId});
          return false;
        }

        let action=await waitTreasureActionButton(modal,target.cost,runId);
        let tapped=false;
        if (action) tapped=dispatchBattleTap(action,target.digging?'chest-dig-confirm':'chest-open-confirm');
        if (!tapped) tapped=await tapTreasureActionFallback(modal,runId);
        if (!tapped) {
          recordDiagnostic('chest-auto-stop',{revision:HK_CHEST_AUTO_REV,reason:'action-missing',lotId:target.lotId});
          return false;
        }

        const started=Date.now();
        while (Date.now()-started<CHEST_ACTION_TIMEOUT_MS) {
          if (runId!==chestAutoRunId || !chestAutoEnabled()) return false;
          const changed=treasureChestSignature()!==beforeSignature;
          const reward=treasureRewardButton();
          if (changed || reward || !treasureModalRoot(target.cost)) break;
          await new Promise(resolve=>setTimeout(resolve,100));
        }

        await new Promise(resolve=>setTimeout(resolve,220));
        const rewards=await dismissTreasureRewards(runId);
        recordDiagnostic('chest-auto-complete',{
          revision:HK_CHEST_AUTO_REV,
          lotId:target.lotId,
          digging:target.digging,
          rewardsDismissed:rewards,
          beforeBalance,
          afterBalance:walletAmount(target.cost.id)
        });
        return true;
      } finally {
        if (runId===chestAutoRunId) chestAutoRunning=false;
        lastSignature='';
        setTimeout(checkPuzzle,320);
      }
    }

"""
need(tap_anchor,"tap helper insertion anchor")
s=s.replace(tap_anchor,chest_code+tap_anchor,1)

old_sig="""    function getSignature() {
      const lights = [...document.querySelectorAll('[data-lot-id^="mf_fairlot_lights_out_sl"]')];
      if (lights.length === 9) return 'LIGHTS|' + lights.map(element => element.getAttribute('data-lot-id')).join('|');

      const sword = document.querySelector('[data-lot-id^="mf_treasurelot_sword_"]');
      const enemies = [...document.querySelectorAll('[data-lot-id*="mf_treasurelot_enemy_type_"]')];
      if (sword && enemies.length > 0) {
        return 'BATTLE|' + sword.getAttribute('data-lot-id') + '|' +
          enemies.map(element => element.getAttribute('data-lot-id')).join('|');
      }

      const victory=battleVictoryElement();
      if (battleVictoryModalRoot()) return 'BATTLE_REWARD_MODAL|mf_treasurelot_enemy_defeated';
      if (victory) return 'BATTLE_REWARD|' + (victory.getAttribute('data-lot-id') || 'mf_treasurelot_enemy_defeated');
      return 'NONE';
    }

    function checkPuzzle() {
      const signature = getSignature();
      const isBattle=signature.startsWith('BATTLE|');
      const isBattleReward=signature.startsWith('BATTLE_REWARD');
      const battleContext=isBattle || isBattleReward || !!document.querySelector('[data-lot-id^="mf_treasurelot_sword_"]');
      ensureBattleAutoToggle(battleContext);
      if (battleAutoRunning) return;
      if (signature === lastSignature) return;
      lastSignature = signature;
      clearNumbers();
      if (signature.startsWith('LIGHTS|')) { runLights(); return; }
      if (isBattle) { runBattle(); return; }
      if (isBattleReward && battleAutoEnabled()) void runBattleVictoryClaim();
    }"""

new_sig="""    function getSignature() {
      const lights = [...document.querySelectorAll('[data-lot-id^="mf_fairlot_lights_out_sl"]')];
      if (lights.length === 9) return 'LIGHTS|' + lights.map(element => element.getAttribute('data-lot-id')).join('|');

      const sword = document.querySelector('[data-lot-id^="mf_treasurelot_sword_"]');
      const enemies = [...document.querySelectorAll('[data-lot-id*="mf_treasurelot_enemy_type_"]')];
      if (sword && enemies.length > 0) {
        return 'BATTLE|' + sword.getAttribute('data-lot-id') + '|' +
          enemies.map(element => element.getAttribute('data-lot-id')).join('|');
      }

      const victory=battleVictoryElement();
      if (battleVictoryModalRoot()) return 'BATTLE_REWARD_MODAL|mf_treasurelot_enemy_defeated';
      if (victory) return 'BATTLE_REWARD|' + (victory.getAttribute('data-lot-id') || 'mf_treasurelot_enemy_defeated');

      const chestRows=treasureChestElements();
      if (chestRows.length>=3) return treasureChestSignature();
      return 'NONE';
    }

    function checkPuzzle() {
      const signature = getSignature();
      const isBattle=signature.startsWith('BATTLE|');
      const isBattleReward=signature.startsWith('BATTLE_REWARD');
      const isChests=signature.startsWith('CHESTS|');
      const battleContext=isBattle || isBattleReward || !!document.querySelector('[data-lot-id^="mf_treasurelot_sword_"]');
      ensureBattleAutoToggle(battleContext);
      ensureChestAutoToggle(isChests);
      if (battleAutoRunning || chestAutoRunning) return;
      if (signature === lastSignature) return;
      lastSignature = signature;
      clearNumbers();
      if (signature.startsWith('LIGHTS|')) { runLights(); return; }
      if (isBattle) { runBattle(); return; }
      if (isBattleReward && battleAutoEnabled()) { void runBattleVictoryClaim(); return; }
      if (isChests && chestAutoEnabled()) void runTreasureChestAuto();
    }"""
rep(old_sig,new_sig,"chest signature and runner")

old_stop="""      battleAutoRunId += 1;
      battleAutoRunning = false;
      clearNumbers();
      try { battleAutoToggle?.remove(); } catch (_) {}
      battleAutoToggle = null;
      recordDiagnostic('puzzle-solver-stop',{revision:HK_PUZZLE_SOLVER_REV});
    }

    return {
      revision:HK_PUZZLE_SOLVER_REV,
      battleAutoRevision:HK_BATTLE_AUTO_CLICK_REV,
      start,
      stop,
      check:checkPuzzle,
      get autoBattleEnabled(){return battleAutoEnabled();},
      setAutoBattleEnabled:setBattleAutoEnabled,
      get running(){return intervalId !== null;}
    };
"""
new_stop="""      battleAutoRunId += 1;
      battleAutoRunning = false;
      chestAutoRunId += 1;
      chestAutoRunning = false;
      clearNumbers();
      try { battleAutoToggle?.remove(); } catch (_) {}
      try { chestAutoToggle?.remove(); } catch (_) {}
      battleAutoToggle = null;
      chestAutoToggle = null;
      recordDiagnostic('puzzle-solver-stop',{revision:HK_PUZZLE_SOLVER_REV});
    }

    return {
      revision:HK_PUZZLE_SOLVER_REV,
      battleAutoRevision:HK_BATTLE_AUTO_CLICK_REV,
      chestAutoRevision:HK_CHEST_AUTO_REV,
      start,
      stop,
      check:checkPuzzle,
      get autoBattleEnabled(){return battleAutoEnabled();},
      setAutoBattleEnabled:setBattleAutoEnabled,
      get autoChestsEnabled(){return chestAutoEnabled();},
      setAutoChestsEnabled:setChestAutoEnabled,
      get running(){return intervalId !== null;}
    };
"""
rep(old_stop,new_stop,"solver stop and export")

for marker in [
    "// @version      1.18.04",
    "const BUILD_VERSION = '1.18.04';",
    "chest-auto-dig-open-20260926-r1",
    "Автосундуки: ВКЛ",
    "item_treasurehunt_energy",
    "item_treasurehunt_key_common",
    "item_treasurehunt_key_uncommon",
    "item_treasurehunt_key_epic",
    "runTreasureChestAuto",
    "CHESTS|",
    "mf_treasurelot_chest_type_015",
    "mf_treasurelot_chest_type_01",
    "mf_treasurelot_chest_type_02",
    "mf_treasurelot_chest_type_03",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

target.write_text(s,encoding="utf-8")
print("CHEST_AUTO_DIG_OPEN_1_18_04=PASS")
