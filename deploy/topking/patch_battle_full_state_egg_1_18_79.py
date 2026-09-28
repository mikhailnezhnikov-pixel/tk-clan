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

rep(
    "// @version      1.18.78",
    "// @version      1.18.79\n"
    "// @release-note Сражение: яйцо mf_fight_egg_* за 1 ягоду теперь выкупается до атак. Поле боя рассчитывается по полному состоянию fair_mini_game_fight, а не только по видимым карточкам мобильного экрана; поэтому порядок ударов строится сразу по всей сетке 4×3. Для цели, которая ещё не смонтирована в DOM, скрипт сам доводит её до viewport только в момент клика.",
    "version"
)
rep("const BUILD_VERSION = '1.18.78';","const BUILD_VERSION = '1.18.79';","build")

anchor="  const HK_CHEST_VISIBLE_CLAIM_REV='chest-visible-claim-priority-20260928-r1';"
rep(
    anchor,
    anchor+"\n  const HK_BATTLE_FULL_STATE_REV='battle-full-fair-state-20260928-r1';\n  const HK_BATTLE_EGG_BERRY_REV='battle-egg-one-berry-buy-20260928-r1';",
    "battle full-state revisions"
)

old_attack_board=r'''    function getBattleAttack() {
      const sword = document.querySelector('[data-lot-id^="mf_treasurelot_sword_"]');
      if (!sword) return null;
      const id = sword.getAttribute('data-lot-id') || '';
      const match = id.match(/mf_treasurelot_sword_\d+_(\d+)/);
      return match ? Number(match[1]) : null;
    }

    function getBattleBoard() {
      const board = new Array(BATTLE_SIZE).fill(null);
      const enemies = [...document.querySelectorAll('[data-lot-id*="mf_treasurelot_enemy_type_"]')];
      enemies.forEach(element => {
        const id = element.getAttribute('data-lot-id') || '';
        const match = id.match(/enemy_type_(01|02|03|04)_(\d+)_sl(\d+)/);
        if (!match) return;
        const type = match[1];
        const hp = Number(match[2]);
        const slot = Number(match[3]);
        const position = slot - BATTLE_FIRST_SLOT;
        if (position < 0 || position >= BATTLE_SIZE) return;
        board[position] = {type,hp,alive:true,element,slot};
      });
      return board;
    }
'''

new_attack_board=r'''    function battleFairState() {
      return fairState('fair_mini_game_fight',playerDocument)
        || fairState('fair_mini_game_fight',fairDocument)
        || null;
    }

    function battleFairSlots() {
      const state=battleFairState();
      const rows=state?.fair_slots || state?.slots || [];
      return Array.isArray(rows) ? rows : [];
    }

    function battleFindLotElement(lotId) {
      const wanted=String(lotId||'');
      if (!wanted) return null;
      return [...document.querySelectorAll('[data-lot-id]')]
        .find(element=>element?.isConnected && String(element.getAttribute('data-lot-id')||'')===wanted) || null;
    }

    function battleRawContextPresent() {
      return !!document.querySelector(
        '[data-lot-id^="mf_treasurelot_sword_"],[data-lot-id*="mf_treasurelot_enemy_type_"],[data-lot-id^="mf_fight_egg_"]'
      );
    }

    function getBattleAttack() {
      for (const slot of battleFairSlots()) {
        if (slot?.is_bought===true) continue;
        const id=String(slot?.shop_lot_id||'');
        const match=id.match(/mf_treasurelot_sword_\d+_(\d+)/);
        if (match) return Number(match[1]);
      }

      const sword = document.querySelector('[data-lot-id^="mf_treasurelot_sword_"]');
      if (!sword) return null;
      const id = sword.getAttribute('data-lot-id') || '';
      const match = id.match(/mf_treasurelot_sword_\d+_(\d+)/);
      return match ? Number(match[1]) : null;
    }

    function getBattleBoard() {
      const board = new Array(BATTLE_SIZE).fill(null);
      let fairEnemies=0;

      // Canonical source: full fight fair state. Mobile Safari may only mount a
      // viewport-sized subset of the 4x3 field, but fair_mini_game_fight always
      // carries every slot and therefore must drive the solver.
      for (const row of battleFairSlots()) {
        if (row?.is_bought===true) continue;
        const id=String(row?.shop_lot_id||'');
        const match=id.match(/enemy_type_(01|02|03|04)_(\d+)_sl(\d+)/);
        if (!match) continue;
        const type=match[1];
        const hp=Number(match[2]);
        const slot=Number(match[3]);
        const position=slot-BATTLE_FIRST_SLOT;
        if (position<0 || position>=BATTLE_SIZE) continue;
        board[position]={
          type,
          hp,
          alive:true,
          element:battleFindLotElement(id),
          slot,
          lotId:id,
          source:'fair'
        };
        fairEnemies+=1;
      }

      if (fairEnemies>0) {
        recordDiagnostic('battle-full-board-state',{
          revision:HK_BATTLE_FULL_STATE_REV,
          source:'fair_mini_game_fight',
          enemies:fairEnemies,
          slots:board.map(enemy=>enemy?.slot||null)
        });
        return board;
      }

      // DOM fallback for the short interval before the current fair state is
      // captured. Do not filter by viewport visibility.
      const enemies = [...document.querySelectorAll('[data-lot-id*="mf_treasurelot_enemy_type_"]')];
      enemies.forEach(element => {
        const id = element.getAttribute('data-lot-id') || '';
        const match = id.match(/enemy_type_(01|02|03|04)_(\d+)_sl(\d+)/);
        if (!match) return;
        const type = match[1];
        const hp = Number(match[2]);
        const slot = Number(match[3]);
        const position = slot - BATTLE_FIRST_SLOT;
        if (position < 0 || position >= BATTLE_SIZE) return;
        board[position] = {type,hp,alive:true,element,slot,lotId:id,source:'dom'};
      });
      return board;
    }

    function battleEggOfferCost(lotId,element=null) {
      const id=String(lotId||'');
      if (!/^mf_fight_egg_/i.test(id)) return null;

      const catalog=fairCatalog.find(row=>String(row?.lotId||'')===id) || null;
      const parts=costParts(catalog?.cost).filter(part=>part.quantity>0);
      if (parts.length===1 &&
          String(parts[0].id)==='item_treasurehunt_energy' &&
          Number(parts[0].quantity)===1) {
        return {id:'item_treasurehunt_energy',quantity:1};
      }

      // Known fight-egg cards are the one-berry bonus. When shop/view metadata
      // is not loaded, verify the live card where possible and use the canonical
      // one-berry cost for this exact lot family.
      if (element) {
        const text=clean(element.innerText||element.textContent||'');
        const assets=[...element.querySelectorAll?.('img')||[]]
          .map(img=>String(img.alt||'')+' '+String(img.src||'')).join(' ').toLowerCase();
        const hasOne=/(?:^|\s)1(?:\s|$)/.test(text);
        const hasBerry=/treasurehunt_energy|berry|ягод/i.test(assets+' '+text);
        if (hasOne && hasBerry) return {id:'item_treasurehunt_energy',quantity:1};
      }

      return {id:'item_treasurehunt_energy',quantity:1};
    }

    function battleEggOfferTarget() {
      for (const row of battleFairSlots()) {
        if (row?.is_bought===true) continue;
        const lotId=String(row?.shop_lot_id||'');
        if (!/^mf_fight_egg_/i.test(lotId)) continue;
        const slot=Number(row?.id ?? lotId.match(/_sl(\d+)$/)?.[1]);
        const element=battleFindLotElement(lotId);
        const cost=battleEggOfferCost(lotId,element);
        if (!cost) continue;
        const balance=walletAmount(cost.id);
        if (balance!==null && balance<cost.quantity) continue;
        return {lotId,slot,element,cost};
      }

      // DOM fallback if the fair response has not reached the shared store yet.
      const element=[...document.querySelectorAll('[data-lot-id^="mf_fight_egg_"]')]
        .find(node=>node?.isConnected) || null;
      if (!element) return null;
      const lotId=String(element.getAttribute('data-lot-id')||'');
      const cost=battleEggOfferCost(lotId,element);
      const balance=walletAmount(cost?.id);
      if (!cost || (balance!==null && balance<cost.quantity)) return null;
      const slot=Number(lotId.match(/_sl(\d+)$/)?.[1]||0);
      return {lotId,slot,element,cost};
    }
'''
rep(old_attack_board,new_attack_board,"full battle fair-state board")

old_element=r'''    function battleElementForSlot(slot) {
      const elements=[...document.querySelectorAll('[data-lot-id*="mf_treasurelot_enemy_type_"]')];
      return elements.find(element=>{
        const id=element.getAttribute('data-lot-id')||'';
        const match=id.match(/enemy_type_(01|02|03|04)_(\d+)_sl(\d+)/);
        return !!match && Number(match[3])===Number(slot);
      }) || null;
    }
'''
new_element=r'''    function battleElementForSlot(slot) {
      const wanted=Number(slot);
      const boardRow=getBattleBoard()[wanted-BATTLE_FIRST_SLOT];
      if (boardRow?.element?.isConnected) return boardRow.element;

      const elements=[...document.querySelectorAll('[data-lot-id*="mf_treasurelot_enemy_type_"]')];
      return elements.find(element=>{
        const id=element.getAttribute('data-lot-id')||'';
        const match=id.match(/enemy_type_(01|02|03|04)_(\d+)_sl(\d+)/);
        return !!match && Number(match[3])===wanted;
      }) || null;
    }

    function battleScrollHost() {
      const seed=document.querySelector(
        '[data-lot-id^="mf_treasurelot_sword_"],[data-lot-id*="mf_treasurelot_enemy_type_"],[data-lot-id^="mf_fight_egg_"]'
      );
      let node=seed?.parentElement || null;
      for (let depth=0;node && depth<10;depth++,node=node.parentElement) {
        try {
          const style=getComputedStyle(node);
          if (/(auto|scroll)/.test(style.overflowY||'') && node.scrollHeight>node.clientHeight+80) return node;
        } catch (_) {}
      }
      return document.scrollingElement || document.documentElement;
    }

    async function battleEnsureLotElement(lotId,slot,runId) {
      let element=battleFindLotElement(lotId);
      if (element) return element;

      const host=battleScrollHost();
      if (!host) return null;
      const isWindowHost=host===document.scrollingElement || host===document.documentElement || host===document.body;
      const max=Math.max(0,(isWindowHost?document.documentElement.scrollHeight:host.scrollHeight)-
        (isWindowHost?window.innerHeight:host.clientHeight));
      const original=isWindowHost ? window.scrollY : host.scrollTop;
      const row=Math.max(0,Math.min(BATTLE_ROWS-1,Math.floor((Number(slot)-BATTLE_FIRST_SLOT)/BATTLE_COLS)));
      const preferred=max*(row/Math.max(1,BATTLE_ROWS-1));
      const positions=[preferred,0,max*0.34,max*0.67,max];

      for (const position of positions) {
        if (runId!==battleAutoRunId || !battleAutoEnabled()) return null;
        try {
          if (isWindowHost) window.scrollTo(0,Math.max(0,position));
          else host.scrollTop=Math.max(0,position);
        } catch (_) {}
        await new Promise(resolve=>setTimeout(resolve,90));
        element=battleFindLotElement(lotId);
        if (element) {
          recordDiagnostic('battle-target-auto-mounted',{
            revision:HK_BATTLE_FULL_STATE_REV,
            lotId,
            slot:Number(slot)||0,
            scrollPosition:Math.round(position)
          });
          return element;
        }
      }

      try {
        if (isWindowHost) window.scrollTo(0,original);
        else host.scrollTop=original;
      } catch (_) {}
      return null;
    }

    async function battleEnsureElementForSlot(slot,runId) {
      const row=getBattleBoard()[Number(slot)-BATTLE_FIRST_SLOT];
      const lotId=String(row?.lotId||'');
      let element=battleElementForSlot(slot);
      if (element) return element;
      if (!lotId) return null;
      return await battleEnsureLotElement(lotId,slot,runId);
    }
'''
rep(old_element,new_element,"battle target auto-mount")

# The fight signature must no longer be viewport-driven.
old_sig=r'''      const sword = battleSwordElement();
      const enemies = [...document.querySelectorAll('[data-lot-id*="mf_treasurelot_enemy_type_"]')].filter(visible);
      if (sword && enemies.length > 0) {
        const battleIds='|' + sword.getAttribute('data-lot-id') + '|' +
          enemies.map(element => element.getAttribute('data-lot-id')).join('|');
        // Once the user has entered the battle, unopened/covered enemy cards are
        // still part of the real board. Their visual "bones" state must never
        // downgrade the screen back to preview.
        return 'BATTLE' + battleIds;
      }
'''
new_sig=r'''      const sword = battleSwordElement();
      const rawBattleContext=battleRawContextPresent();
      const battleBoard=getBattleBoard();
      const fullEnemies=battleBoard.filter(enemy=>enemy!==null);
      const swords=getBattleAttack();
      if (rawBattleContext && Number.isFinite(swords) && fullEnemies.length > 0) {
        const battleIds='|SWORDS='+String(swords)+'|' +
          fullEnemies.map(enemy=>enemy.lotId || (enemy.type+':'+enemy.hp+':sl'+enemy.slot)).join('|');
        const egg=battleEggOfferTarget();
        return 'BATTLE' + battleIds + (egg ? '|EGG='+egg.lotId : '');
      }
'''
rep(old_sig,new_sig,"battle full-state signature")

# Egg purchase owns the battle before any attack plan is calculated.
run_anchor=r'''    function runBattle() {
      // AutoMap owns orchestration, but battle always keeps attacking while at
'''
if s.count(run_anchor)!=1:
    raise SystemExit("runBattle anchor missing")

egg_runner=r'''    async function runBattleEggOffer(target) {
      if (!target || !battleAutoEnabled() || battleAutoRunning) return false;
      battleAutoRunning=true;
      const runId=++battleAutoRunId;
      const beforeSignature=getSignature();

      try {
        let element=target.element;
        if (!element?.isConnected) {
          element=await battleEnsureLotElement(target.lotId,target.slot,runId);
        }
        if (!element) {
          recordDiagnostic('battle-egg-buy-stop',{
            revision:HK_BATTLE_EGG_BERRY_REV,
            reason:'egg-card-not-mounted',
            lotId:target.lotId,
            slot:target.slot
          });
          return false;
        }

        if (!dispatchBattleOverlaySafeTap(element,'battle-egg-one-berry-card')) return false;

        let modal=null;
        const openedAt=Date.now();
        while (Date.now()-openedAt<2200 && runId===battleAutoRunId && battleAutoEnabled()) {
          modal=treasureModalRoot(target.cost);
          if (modal) break;
          const current=battleEggOfferTarget();
          if (!current || current.lotId!==target.lotId) break;
          await new Promise(resolve=>setTimeout(resolve,70));
        }

        if (modal) {
          let action=null;
          const actionAt=Date.now();
          while (Date.now()-actionAt<1800 && runId===battleAutoRunId && battleAutoEnabled()) {
            action=treasureActionButton(modal,target.cost);
            if (action) break;
            await new Promise(resolve=>setTimeout(resolve,70));
          }
          if (!action) {
            recordDiagnostic('battle-egg-buy-stop',{
              revision:HK_BATTLE_EGG_BERRY_REV,
              reason:'purchase-button-missing',
              lotId:target.lotId
            });
            return false;
          }
          await new Promise(resolve=>setTimeout(resolve,minigameRandomMs(100,180)));
          if (!dispatchBattleOverlaySafeTap(action,'battle-egg-one-berry-confirm')) return false;
        }

        const settledAt=Date.now();
        let bought=false;
        while (Date.now()-settledAt<3600 && runId===battleAutoRunId && battleAutoEnabled()) {
          const current=battleEggOfferTarget();
          if (!current || current.lotId!==target.lotId) { bought=true; break; }
          const reward=battleRewardDismissButton();
          if (reward) break;
          if (getSignature()!==beforeSignature && !battleFindLotElement(target.lotId)) { bought=true; break; }
          await new Promise(resolve=>setTimeout(resolve,90));
        }

        const reward=await waitBattleRewardDismissButton(runId,900);
        if (reward) {
          dispatchBattleOverlaySafeTap(reward,'battle-egg-one-berry-reward');
          await new Promise(resolve=>setTimeout(resolve,180));
          bought=true;
        }

        recordDiagnostic('battle-egg-buy-complete',{
          revision:HK_BATTLE_EGG_BERRY_REV,
          lotId:target.lotId,
          slot:target.slot,
          cost:target.cost,
          success:!!bought
        });
        return !!bought;
      } finally {
        if (runId===battleAutoRunId) battleAutoRunning=false;
        lastSignature='';
        setTimeout(checkPuzzle,120);
      }
    }

'''
s=s.replace(run_anchor,egg_runner+run_anchor,1)

run_insertion=r'''      const maxAttack = getBattleAttack();
      if (maxAttack === null) return false;
'''
run_new=r'''      const eggOffer=battleEggOfferTarget();
      if (eggOffer) {
        if (autoMapEnabled()) {
          autoMapStatus('сражение → яйцо за 1 ягоду',{
            revision:HK_BATTLE_EGG_BERRY_REV,
            lotId:eggOffer.lotId,
            slot:eggOffer.slot
          });
        }
        if (battleAutoEnabled() && !battleAutoRunning) void runBattleEggOffer(eggOffer);
        return true;
      }

      const maxAttack = getBattleAttack();
      if (maxAttack === null) return false;
'''
rep(run_insertion,run_new,"egg pre-attack priority")

# Exit is forbidden while the one-berry egg is still available.
exit_anchor=r'''      const enemies=board.filter(enemy=>enemy!==null);
      const swords=getBattleAttack();
      const activatedSettled=battleRecoverFinalRewardClaimed('exit-state');
'''
exit_new=r'''      const enemies=board.filter(enemy=>enemy!==null);
      const swords=getBattleAttack();
      const eggOffer=battleEggOfferTarget();
      const activatedSettled=battleRecoverFinalRewardClaimed('exit-state');
'''
rep(exit_anchor,exit_new,"exit egg state")

reward_pending_anchor=r'''      if (rewardPending) {
        return {
'''
egg_exit=r'''      if (eggOffer) {
        return {
          inBattle:true,
          allowed:false,
          reason:'one-berry-egg-pending',
          swords,
          enemies:enemies.length,
          attackable:0,
          eggLotId:eggOffer.lotId,
          eggSlot:eggOffer.slot
        };
      }

'''
if s.count(reward_pending_anchor)!=1:
    raise SystemExit("reward pending anchor missing")
s=s.replace(reward_pending_anchor,egg_exit+reward_pending_anchor,1)

# Attack click can now mount/scroll only the selected target after the full board
# has already been solved from fair state.
rep(
"""        const element=battleElementForSlot(slot);
        if (!element) {
          recordDiagnostic('battle-auto-stop',{revision:HK_BATTLE_MODAL_CONFIRM_REV,reason:'target-missing',slot});
          return false;
        }
""",
"""        const element=await battleEnsureElementForSlot(slot,runId);
        if (!element) {
          recordDiagnostic('battle-auto-stop',{revision:HK_BATTLE_FULL_STATE_REV,reason:'target-missing-after-auto-mount',slot});
          return false;
        }
""",
"battle auto ensure target"
)

export_anchor="      chestVisibleClaimRevision:HK_CHEST_VISIBLE_CLAIM_REV,"
if s.count(export_anchor)!=1:
    raise SystemExit("visible chest export anchor missing")
s=s.replace(
    export_anchor,
    export_anchor+"\n      battleFullStateRevision:HK_BATTLE_FULL_STATE_REV,\n      battleEggBerryRevision:HK_BATTLE_EGG_BERRY_REV,",
    1
)

for marker in [
    "// @version      1.18.79",
    "const BUILD_VERSION = '1.18.79';",
    "battle-full-fair-state-20260928-r1",
    "battle-egg-one-berry-buy-20260928-r1",
    "function battleFairState()",
    "function battleFairSlots()",
    "source:'fair_mini_game_fight'",
    "function battleEggOfferTarget()",
    "/^mf_fight_egg_/i",
    "item_treasurehunt_energy',quantity:1",
    "async function runBattleEggOffer(target)",
    "сражение → яйцо за 1 ягоду",
    "reason:'one-berry-egg-pending'",
    "await battleEnsureElementForSlot(slot,runId)",
    "battleFullStateRevision:HK_BATTLE_FULL_STATE_REV",
    "battleEggBerryRevision:HK_BATTLE_EGG_BERRY_REV",
    "chest-visible-claim-priority-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

p.write_text(s,encoding="utf-8")
print("BATTLE_FULL_STATE_EGG_1_18_79=PASS")
