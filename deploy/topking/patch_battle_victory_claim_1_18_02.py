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
    "// @version      1.18.01",
    "// @version      1.18.02\n"
    "// @release-note Сражение: после полной зачистки автобой теперь сам открывает mf_treasurelot_enemy_defeated («Сундук победителя»), нажимает кнопку получения награды и закрывает возможное итоговое окно.",
    "version"
)
rep("const BUILD_VERSION = '1.18.01';","const BUILD_VERSION = '1.18.02';","build")

rep(
    "  const HK_BATTLE_REWARD_DISMISS_REV = 'battle-reward-dismiss-20260926-r1';",
    "  const HK_BATTLE_REWARD_DISMISS_REV = 'battle-reward-dismiss-20260926-r1';\n"
    "  const HK_BATTLE_VICTORY_CLAIM_REV = 'battle-victory-claim-20260926-r1';",
    "victory claim marker"
)

anchor="""    async function dismissBattleRewardIfPresent(runId) {
      const button=await waitBattleRewardDismissButton(runId);
      if (!button) return false;
      button.click();
      recordDiagnostic('battle-auto-dismiss-reward',{revision:HK_BATTLE_REWARD_DISMISS_REV});
      await new Promise(resolve=>setTimeout(resolve,220));
      return true;
    }

"""
insert="""    function battleVictoryElement() {
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
need(anchor,"victory helper anchor")
s=s.replace(anchor,anchor+insert,1)

old_sig="""    function getSignature() {
      const lights = [...document.querySelectorAll('[data-lot-id^="mf_fairlot_lights_out_sl"]')];
      if (lights.length === 9) return 'LIGHTS|' + lights.map(element => element.getAttribute('data-lot-id')).join('|');

      const sword = document.querySelector('[data-lot-id^="mf_treasurelot_sword_"]');
      const enemies = [...document.querySelectorAll('[data-lot-id*="mf_treasurelot_enemy_type_"]')];
      if (sword && enemies.length > 0) {
        return 'BATTLE|' + sword.getAttribute('data-lot-id') + '|' +
          enemies.map(element => element.getAttribute('data-lot-id')).join('|');
      }
      return 'NONE';
    }

    function checkPuzzle() {
      const signature = getSignature();
      const isBattle=signature.startsWith('BATTLE|');
      ensureBattleAutoToggle(isBattle);
      if (battleAutoRunning) return;
      if (signature === lastSignature) return;
      lastSignature = signature;
      clearNumbers();
      if (signature.startsWith('LIGHTS|')) { runLights(); return; }
      if (isBattle) runBattle();
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
rep(old_sig,new_sig,"reward signature and check")

for marker in [
    "// @version      1.18.02",
    "const BUILD_VERSION = '1.18.02';",
    "battle-victory-claim-20260926-r1",
    "mf_treasurelot_enemy_defeated",
    "battle-victory-open",
    "battle-victory-claim-click",
    "runBattleVictoryClaim",
    "BATTLE_REWARD_MODAL",
    "battle-reward-dismiss-20260926-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

target.write_text(s,encoding="utf-8")
print("BATTLE_VICTORY_CLAIM_1_18_02=PASS")
