from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count:
        raise SystemExit(f"{label}: expected {count}, got {n}")
    s=s.replace(old,new,count)

def replace_between(start,end,new,label):
    global s
    a=s.find(start)
    if a<0:
        raise SystemExit(f"{label}: start anchor missing")
    b=s.find(end,a+len(start))
    if b<0:
        raise SystemExit(f"{label}: end anchor missing")
    s=s[:a]+new+s[b:]

rep("// @version      1.18.95",
    "// @version      1.18.96\n// @release-note Сражение: открытая карточка бойца «МОЖНО ОТЫСКАТЬ» теперь является жёстким приоритетом — Автобой восстанавливает нижнюю кнопку стоимости прямо из модалки до пересчёта поля и запрещает выход/пропуск, пока карточка не подтверждена. Тайный торговец: Карта сокровищ добавлена в подтверждаемый whitelist модалок, поэтому выбранная карта действительно покупается.",
    "version")
rep("const BUILD_VERSION = '1.18.95';",
    "const BUILD_VERSION = '1.18.96';",
    "build")

trader_rev="  const HK_TRADER_GOLD_EXACT_MODAL_REV='trader-gold-exact-purchase-modal-20260929-r1';"
rep(trader_rev,
    trader_rev+"\n  const HK_TRADER_MAP_MODAL_REV='trader-map-modal-approval-20260930-r1';",
    "trader map revision")

battle_rev="  const HK_BATTLE_COMPLETE_EXIT_LOOP_REV='battle-complete-exit-loop-20260930-r1';"
rep(battle_rev,
    battle_rev+"\n  const HK_BATTLE_OPEN_MODAL_PRIORITY_REV='battle-open-modal-priority-20260930-r1';",
    "battle open modal priority revision")

old_trader=r'''      return /вкусняшк.*питом|лакомств.*питом|pet\s*(?:treat|snack)/i.test(text) ||
        /(?:необычн|обычн|редк|эпическ|легендарн).*ключ\s+сокровищ|treasure\s+key/i.test(text) ||
        /походн.*припас|провизия\s+для\s+путешеств|travel\s+provision|hiking\s+suppl/i.test(text) ||
        /смена\s+навыка\s+питомца|замена\s+навыка\s+питомца|pet\s+skill\s+(?:change|replace)/i.test(text);'''
new_trader=r'''      return /вкусняшк.*питом|лакомств.*питом|pet\s*(?:treat|snack)/i.test(text) ||
        /(?:необычн|обычн|редк|эпическ|легендарн).*ключ\s+сокровищ|treasure\s+key/i.test(text) ||
        /походн.*припас|провизия\s+для\s+путешеств|travel\s+provision|hiking\s+suppl/i.test(text) ||
        /карта\s+сокровищ|treasure\s+map/i.test(text) ||
        /смена\s+навыка\s+питомца|замена\s+навыка\s+питомца|pet\s+skill\s+(?:change|replace)/i.test(text);'''
rep(old_trader,new_trader,"trader map modal whitelist")

action_start="    function battleEnemyModalActionButton(expectedCost) {"
action_end="    function battleEnemyModalRoot() {"
action_block=r'''    function battleEnemyModalActionButton(expectedCost=null) {
      const numericExpected=Number(expectedCost);
      const hasExpected=Number.isFinite(numericExpected) && numericExpected>0;
      const costText=hasExpected ? String(numericExpected) : '';
      const exactCost=hasExpected ? new RegExp('(?:^|\\s)'+costText+'(?:\\s|$)') : null;

      const roots=[...document.querySelectorAll(
        '[role="dialog"],[aria-modal="true"],[class*="modal"],[class*="popup"],[class*="dialog"],div'
      )]
        .filter(visible)
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const rect=element.getBoundingClientRect?.() || {left:0,top:0,width:0,height:0};
          return {element,text,rect,area:rect.width*rect.height};
        })
        .filter(row=>/МОЖНО\s+ОТЫСКАТЬ|CAN\s+BE\s+FOUND/i.test(row.text))
        .filter(row=>row.rect.width>=Math.min(260,window.innerWidth*0.40) && row.rect.height>=220)
        .filter(row=>row.rect.width<=window.innerWidth*0.99 && row.rect.height<=window.innerHeight*0.98)
        .sort((a,b)=>a.area-b.area);

      const root=roots[0]?.element || null;
      if (!root) return null;
      const rr=root.getBoundingClientRect?.();
      if (!rr) return null;
      const centerX=rr.left+rr.width/2;

      const rows=[...root.querySelectorAll('button,[role="button"],a,[onclick],div,span')]
        .filter(element=>element && !element.disabled && visible(element))
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const rect=element.getBoundingClientRect?.() || {left:0,top:0,width:0,height:0};
          let actionable=false;
          try {
            actionable=
              element.matches?.('button,[role="button"],a,[onclick]') ||
              !!element.onclick ||
              getComputedStyle(element).cursor==='pointer';
          } catch (_) {}
          const cx=rect.left+rect.width/2;
          const numericMatch=text.match(/(?:^|\\s)(\\d{1,4})(?:\\s|$)/);
          const inferredCost=numericMatch ? Number(numericMatch[1]) : null;
          let score=0;

          if (hasExpected) {
            if (text===costText) score+=520;
            else if (exactCost.test(text) && text.length<=16) score+=260;
          } else if (Number.isFinite(inferredCost) && inferredCost>0) {
            score+=330;
          }

          if (rect.top>=rr.top+rr.height*0.60) score+=220;
          if (Math.abs(cx-centerX)<=rr.width*0.32) score+=150;
          if (rect.width>=rr.width*0.28 && rect.width<=rr.width*0.90) score+=110;
          if (rect.height>=34 && rect.height<=150) score+=90;
          if (actionable) score+=120;

          // Without a known board cost, only the wide lower-centre numeric
          // control can own the attack. This excludes x1/x6 reward counters.
          if (!hasExpected) {
            if (!Number.isFinite(inferredCost) || inferredCost<=0) score-=1200;
            if (rect.top<rr.top+rr.height*0.66) score-=900;
            if (Math.abs(cx-centerX)>rr.width*0.28) score-=900;
            if (rect.width<rr.width*0.34) score-=900;
          }

          if (/закрыть|close|×|✕|назад|back|понятно|got it|understood/i.test(text)) score-=900;
          return {element,score,rect,text,inferredCost};
        })
        .filter(row=>row.score>=650)
        .sort((a,b)=>b.score-a.score || b.rect.width*b.rect.height-a.rect.width*a.rect.height);

      const best=rows[0] || null;
      if (best) {
        recordDiagnostic('battle-modal-action-recovered',{
          revision:hasExpected ? HK_BATTLE_MODAL_ACTION_RECOVERY_REV : HK_BATTLE_OPEN_MODAL_PRIORITY_REV,
          expectedCost:hasExpected ? numericExpected : null,
          inferredCost:Number.isFinite(best.inferredCost)?best.inferredCost:null,
          text:best.text.slice(0,80)
        });
      }
      return best?.element || null;
    }

    function battleEnemyModalActionCost(element) {
      if (!element) return null;
      const text=clean(element.innerText||element.textContent||'').trim();
      const values=[...text.matchAll(/(?:^|\\s)(\\d{1,4})(?=\\s|$)/g)]
        .map(match=>Number(match[1]))
        .filter(value=>Number.isFinite(value) && value>0);
      return values.length ? values[values.length-1] : null;
    }

'''
replace_between(action_start,action_end,action_block,"battle modal action inference")

confirm_start="    async function battleConfirmAlreadyOpenEnemyModal(expectedCost,runId,beforeSignature=null) {"
confirm_end="    function battleActionButton(expectedCost) {"
confirm_block=r'''    async function battleConfirmAlreadyOpenEnemyModal(expectedCost,runId,beforeSignature=null) {
      const root=battleEnemyModalRoot();
      if (!root) return {handled:false,success:false,reason:'no-modal'};

      const numericExpected=Number(expectedCost);
      const hasExpected=Number.isFinite(numericExpected) && numericExpected>0;
      const action=battleEnemyModalActionButton(hasExpected?numericExpected:null);
      const resolvedCost=hasExpected ? numericExpected : battleEnemyModalActionCost(action);
      if (!action) {
        recordDiagnostic('battle-open-modal-confirm-wait',{
          revision:HK_BATTLE_OPEN_MODAL_PRIORITY_REV,
          expectedCost:hasExpected?numericExpected:null,
          reason:'action-missing'
        });
        return {handled:true,success:false,reason:'action-missing'};
      }

      const before=beforeSignature===null ? getSignature() : beforeSignature;
      const beforeSwords=Number(getBattleAttack());
      const ready=await battleScrollTargetIntoViewportAsync(
        action,
        'battle-open-modal-confirm-'+String(resolvedCost??'auto'),
        runId
      );
      if (!ready) {
        recordDiagnostic('battle-open-modal-confirm-stop',{
          revision:HK_BATTLE_OPEN_MODAL_PRIORITY_REV,
          expectedCost:hasExpected?numericExpected:null,
          resolvedCost,
          reason:'action-not-clickable'
        });
        return {handled:true,success:false,reason:'action-not-clickable'};
      }

      let sent=dispatchBattleOverlaySafeTap(action,'battle-open-modal-confirm');
      if (!sent && root.isConnected) {
        const rr=root.getBoundingClientRect?.();
        if (rr && rr.width>0 && rr.height>0) {
          for (const fraction of [0.91,0.87,0.94]) {
            if (runId!==battleAutoRunId || !battleAutoEnabled()) {
              return {handled:true,success:false,reason:'cancelled'};
            }
            sent=dispatchBattleOverlaySafeTapAt(
              rr.left+rr.width/2,
              rr.top+rr.height*fraction,
              'battle-open-modal-confirm-fallback-'+String(fraction)
            );
            if (sent) break;
          }
        }
      }
      if (!sent) {
        return {handled:true,success:false,reason:'tap-failed'};
      }

      const started=Date.now();
      while (Date.now()-started<4400) {
        if (runId!==battleAutoRunId || !battleAutoEnabled()) {
          return {handled:true,success:false,reason:'cancelled'};
        }
        const currentRoot=battleEnemyModalRoot();
        const currentSwords=Number(getBattleAttack());
        const currentSignature=getSignature();
        if (!currentRoot || currentRoot!==root || currentSignature!==before ||
            (Number.isFinite(beforeSwords) && Number.isFinite(currentSwords) && currentSwords!==beforeSwords)) {
          recordDiagnostic('battle-open-modal-confirm-complete',{
            revision:HK_BATTLE_OPEN_MODAL_PRIORITY_REV,
            expectedCost:hasExpected?numericExpected:null,
            resolvedCost,
            modalClosed:!currentRoot || currentRoot!==root,
            signatureChanged:currentSignature!==before,
            swordsBefore:beforeSwords,
            swordsAfter:currentSwords
          });
          return {handled:true,success:true,reason:'accepted',resolvedCost};
        }
        await new Promise(resolve=>setTimeout(resolve,90));
      }

      recordDiagnostic('battle-open-modal-confirm-stop',{
        revision:HK_BATTLE_OPEN_MODAL_PRIORITY_REV,
        expectedCost:hasExpected?numericExpected:null,
        resolvedCost,
        reason:'no-state-change'
      });
      return {handled:true,success:false,reason:'no-state-change'};
    }

    async function runBattleOpenEnemyModalRecovery(source='battle-hard-gate') {
      if (!battleAutoEnabled() || battleAutoRunning) return false;
      const root=battleEnemyModalRoot();
      if (!root) return false;

      battleAutoRunning=true;
      const runId=++battleAutoRunId;
      try {
        const action=battleEnemyModalActionButton(null);
        const inferredCost=battleEnemyModalActionCost(action);
        recordDiagnostic('battle-open-modal-priority-start',{
          revision:HK_BATTLE_OPEN_MODAL_PRIORITY_REV,
          source,
          inferredCost
        });

        const result=await battleConfirmAlreadyOpenEnemyModal(inferredCost,runId);
        if (!result.success) {
          recordDiagnostic('battle-open-modal-priority-stop',{
            revision:HK_BATTLE_OPEN_MODAL_PRIORITY_REV,
            source,
            reason:result.reason,
            inferredCost
          });
          return false;
        }

        await new Promise(resolve=>setTimeout(resolve,BATTLE_AUTO_SETTLE_MS));
        await dismissBattleRewardIfPresent(runId);
        battleInsufficientExitNotBefore=Date.now()+900;
        recordDiagnostic('battle-open-modal-priority-complete',{
          revision:HK_BATTLE_OPEN_MODAL_PRIORITY_REV,
          source,
          resolvedCost:result.resolvedCost??inferredCost
        });
        return true;
      } finally {
        if (runId===battleAutoRunId) battleAutoRunning=false;
        lastSignature='';
        setTimeout(checkPuzzle,180);
      }
    }

'''
replace_between(confirm_start,confirm_end,confirm_block,"battle open modal priority recovery")

exit_anchor=r'''      const swords=getBattleAttack();
      const eggOffer=battleEggOfferTarget();
      const activatedSettled=battleRecoverFinalRewardClaimed('exit-state');'''
exit_new=r'''      const swords=getBattleAttack();
      const eggOffer=battleEggOfferTarget();
      const enemyModalPending=!!battleEnemyModalRoot();
      const activatedSettled=battleRecoverFinalRewardClaimed('exit-state');'''
rep(exit_anchor,exit_new,"battle exit modal pending state")

egg_anchor=r'''      if (eggOffer) {
        return {
          inBattle:true,
          allowed:false,
          reason:'one-berry-egg-pending','''
egg_new=r'''      if (enemyModalPending) {
        return {
          inBattle:true,
          allowed:false,
          reason:'enemy-modal-pending',
          swords,
          enemies:enemies.length,
          attackable:0
        };
      }

      if (eggOffer) {
        return {
          inBattle:true,
          allowed:false,
          reason:'one-berry-egg-pending','''
rep(egg_anchor,egg_new,"battle exit hard gate on enemy modal")

run_anchor=r'''      const eggOffer=battleEggOfferTarget();
      if (eggOffer) {'''
run_new=r'''      // A visible enemy card is an unfinished attack transaction. Recover it
      // before reading board state or deciding that no legal attack remains.
      // This is the exact intermittent mobile state where the old runner could
      // fall through to the insufficient-swords exit path and skip the fight.
      if (battleEnemyModalRoot()) {
        if (autoMapEnabled()) {
          autoMapStatus('сражение → подтверждаю бой',{
            revision:HK_BATTLE_OPEN_MODAL_PRIORITY_REV
          });
        }
        if (battleAutoEnabled() && !battleAutoRunning) {
          void runBattleOpenEnemyModalRecovery('run-battle-hard-gate');
        }
        return true;
      }

      const eggOffer=battleEggOfferTarget();
      if (eggOffer) {'''
rep(run_anchor,run_new,"run battle open modal hard gate")

trader_export="      traderGoldExactModalRevision:HK_TRADER_GOLD_EXACT_MODAL_REV,"
rep(trader_export,
    trader_export+"\n      traderMapModalRevision:HK_TRADER_MAP_MODAL_REV,",
    "trader revision export")

battle_export="      battleCompleteExitLoopRevision:HK_BATTLE_COMPLETE_EXIT_LOOP_REV,"
rep(battle_export,
    battle_export+"\n      battleOpenModalPriorityRevision:HK_BATTLE_OPEN_MODAL_PRIORITY_REV,",
    "battle revision export")

p.write_text(s,encoding="utf-8")
print("PATCH_BATTLE_MODAL_TRADER_MAP_1_18_96=PASS")
