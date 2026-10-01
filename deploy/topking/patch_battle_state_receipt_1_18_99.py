from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")
def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f"{label}: expected {count} anchors, got {n}")
    s=s.replace(old,new,count)
def between(start,end,new,label):
    global s
    a=s.find(start)
    if a<0: raise SystemExit(label+": start missing")
    b=s.find(end,a+len(start))
    if b<0: raise SystemExit(label+": end missing")
    s=s[:a]+new+s[b:]

rep("// @version      1.18.98",
    "// @version      1.18.99\n// @release-note Сражение: доступный боец и незакрытая карточка блокируют выход за 10 ягод даже при старом флаге награды. Атака подтверждается только реальным изменением мечей/лотов или появлением награды, а не перерисовкой модалки. Перед каждым выходом проверяется актуальное поле.",
    "version")
rep("const BUILD_VERSION = '1.18.98';","const BUILD_VERSION = '1.18.99';","build")
revision="  const HK_TREASURY_BATTLE_HANDOFF_REV='treasury-battle-foreground-handoff-20261001-r1';"
rep(revision,revision+"\n  const HK_BATTLE_NO_PREMATURE_EXIT_REV='battle-no-premature-exit-20261001-r1';\n  const HK_BATTLE_ATTACK_RECEIPT_REV='battle-attack-state-receipt-20261001-r1';","revisions")

# The final chest can be visually Activated in an old mounted node; it is
# weaker evidence than the live attackable fair board / open enemy dialog.
old=r'''    function battleRecoverFinalRewardClaimed(source='visual-activated') {
      if (!battleFinalRewardSettled()) return false;
      if (!battleFinalRewardClaimed) {
        battleFinalRewardClaimed=true;
        battleFinalRewardClaimedAt=Date.now();
        recordDiagnostic('battle-final-reward-recovered',{
          revision:HK_BATTLE_ACTIVATED_EXIT_REV,
          source
        });
      }
      return true;
    }
'''
new=r'''    function battleRecoverFinalRewardClaimed(source='visual-activated') {
      const enemyModalPending=!!battleEnemyModalRoot();
      const swords=getBattleAttack();
      const board=getBattleBoard().filter(enemy=>enemy!==null);
      const attackable=Number.isFinite(swords)
        ? board.filter(enemy=>Number(enemy.hp)>0 && Number(enemy.hp)<=swords)
        : [];
      if (enemyModalPending || (battleScreenVisiblyCurrent() && attackable.length>0)) {
        if (battleFinalRewardClaimed) {
          battleFinalRewardClaimed=false;
          battleFinalRewardClaimedAt=0;
          recordDiagnostic('battle-stale-reward-invalidated',{
            revision:HK_BATTLE_NO_PREMATURE_EXIT_REV,
            source,swords,
            attackable:attackable.map(enemy=>enemy.slot),
            enemyModalPending
          });
        }
        return false;
      }
      if (!battleFinalRewardSettled()) return false;
      if (!battleFinalRewardClaimed) {
        battleFinalRewardClaimed=true;
        battleFinalRewardClaimedAt=Date.now();
        recordDiagnostic('battle-final-reward-recovered',{
          revision:HK_BATTLE_ACTIVATED_EXIT_REV,
          source
        });
      }
      return true;
    }
'''
rep(old,new,"stale reward receipt")

start="    function battleExitState() {"
end="    function battleLeaveBackButton("
gate=r'''    function battleExitState() {
      const signature=String(getSignature()||'');
      const board=getBattleBoard();
      // No visual filter here: the leave confirmation hides the entire grid.
      // Raw fair slots must remain authoritative until the game updates them.
      const enemies=board.filter(enemy=>enemy!==null);
      const swords=getBattleAttack();
      const eggOffer=battleEggOfferTarget();
      const enemyModalPending=!!battleEnemyModalRoot();
      const rewardConfirmPending=battleRewardConfirmOnlyPending();
      const rewardPending=!!battleVictoryElement() || !!battleVictoryModalRoot() || rewardConfirmPending;
      const inBattle=
        battleScreenVisiblyCurrent() ||
        signature.startsWith('BATTLE') ||
        enemies.length>0 ||
        enemyModalPending ||
        rewardPending;
      if (!inBattle) {
        return {inBattle:false,allowed:true,reason:'not-battle',swords,enemies:0,attackable:0};
      }

      // A visible enemy modal is an unfinished attack, never a leave request.
      // This must outrank any cached "chest claimed" flag.
      if (enemyModalPending) {
        return {
          inBattle:true,allowed:false,reason:'enemy-modal-pending',
          swords,enemies:enemies.length,attackable:0
        };
      }

      // A transient missing sword balance is not proof that no attacks remain.
      if (!Number.isFinite(swords)) {
        return {
          inBattle:true,allowed:false,reason:'swords-unknown',
          swords:null,enemies:enemies.length,attackable:0
        };
      }

      const attackable=enemies.filter(enemy=>Number(enemy.hp)>0 && Number(enemy.hp)<=swords);
      if (attackable.length>0) {
        if (battleFinalRewardClaimed) {
          battleFinalRewardClaimed=false;
          battleFinalRewardClaimedAt=0;
          recordDiagnostic('battle-stale-claimed-exit-blocked',{
            revision:HK_BATTLE_NO_PREMATURE_EXIT_REV,
            swords,slots:attackable.map(enemy=>enemy.slot)
          });
        }
        return {
          inBattle:true,allowed:false,reason:'attack-available',
          swords,enemies:enemies.length,attackable:attackable.length,
          slots:attackable.map(enemy=>enemy.slot).slice(0,12)
        };
      }

      if (eggOffer) {
        return {
          inBattle:true,allowed:false,reason:'one-berry-egg-pending',
          swords,enemies:enemies.length,attackable:0,
          eggLotId:eggOffer.lotId,eggSlot:eggOffer.slot
        };
      }
      if (rewardPending) {
        return {
          inBattle:true,allowed:false,reason:'final-reward-pending',
          swords,enemies:enemies.length,attackable:0,rewardConfirmPending
        };
      }

      const activatedSettled=battleRecoverFinalRewardClaimed('exit-state');
      if (activatedSettled) {
        return {
          inBattle:true,allowed:true,reason:'final-reward-activated',
          swords,enemies:enemies.length,attackable:0,
          claimedAt:battleFinalRewardClaimedAt
        };
      }
      if (battleFinalRewardClaimed) {
        return {
          inBattle:true,allowed:true,reason:'final-reward-claimed',
          swords,enemies:enemies.length,attackable:0,
          claimedAt:battleFinalRewardClaimedAt
        };
      }
      if (!enemies.length) {
        return {
          inBattle:true,allowed:false,reason:'waiting-final-reward',
          swords,enemies:0,attackable:0
        };
      }
      return {
        inBattle:true,allowed:true,reason:'no-attack-available',
        swords,enemies:enemies.length,attackable:0
      };
    }

'''
between(start,end,gate,"priority exit gate")

# The release-1.18.98 signature put any Activated chest ahead of the live
# fighter board. An enemy modal or affordable fighter must win that ordering.
old="""      if (autoMapTreasuryForeground()) return 'NONE';
      const lightsReward=lightsRewardElement();"""
new="""      if (autoMapTreasuryForeground()) return 'NONE';
      const liveBattleModal=battleEnemyModalRoot();
      const liveBattleSwords=getBattleAttack();
      const liveBattleEnemies=getBattleBoard().filter(enemy=>enemy!==null);
      if (
        (liveBattleModal || battleScreenVisiblyCurrent()) &&
        Number.isFinite(liveBattleSwords) &&
        liveBattleEnemies.length>0 &&
        (
          !!liveBattleModal ||
          liveBattleEnemies.some(enemy=>Number(enemy.hp)>0 && Number(enemy.hp)<=liveBattleSwords)
        )
      ) {
        const battleIds='|SWORDS='+String(liveBattleSwords)+'|' +
          liveBattleEnemies.map(enemy=>enemy.lotId || (enemy.type+':'+enemy.hp+':sl'+enemy.slot)).join('|');
        return 'BATTLE' + battleIds;
      }
      const lightsReward=lightsRewardElement();"""
rep(old,new,"live board before old reward")

# Do not reuse the claimed bit from a previous fight with fresh legal targets.
rep("""      if (battleFinalRewardClaimed) {
        recordDiagnostic('battle-stale-dom-after-reward',{""",
    """      if (battleFinalRewardClaimed && enemies.some(enemy=>
        Number(enemy.hp)>0 && Number(enemy.hp)<=maxAttack
      )) {
        battleFinalRewardClaimed=false;
        battleFinalRewardClaimedAt=0;
        recordDiagnostic('battle-stale-reward-cleared-before-attack',{
          revision:HK_BATTLE_NO_PREMATURE_EXIT_REV,
          swords:maxAttack
        });
      }
      if (battleFinalRewardClaimed) {
        recordDiagnostic('battle-stale-dom-after-reward',{""",
    "resume attacks after old claim")

# Opening the leave dialog is a separate (potentially stale) transaction.
# The check before actually purchasing the 10-berry exit is mandatory.
rep("""        const button=autoMapLeaveConfirmButton(modal,10);
        if (!button) {""",
    """        const preConfirmGate=battleExitState();
        if (preConfirmGate.inBattle && !preConfirmGate.allowed) {
          recordDiagnostic('battle-exit-cancel-before-10',{
            revision:HK_BATTLE_NO_PREMATURE_EXIT_REV,source,attempt,
            reason:preConfirmGate.reason,swords:preConfirmGate.swords,
            attackable:preConfirmGate.attackable
          });
          await autoMapRecoverOpenLeaveModal('battle-exit-guard-before-10');
          lastSignature='';
          setTimeout(checkPuzzle,120);
          return false;
        }

        const button=autoMapLeaveConfirmButton(modal,10);
        if (!button) {""",
    "completed exit confirmation gate")
rep("""      for (let attempt=1;attempt<=attempts;attempt++) {
        if (!autoMapEnabled()) return false;
        if (handoff()) return true;
        if (roomGone()) {""",
    """      for (let attempt=1;attempt<=attempts;attempt++) {
        if (!autoMapEnabled()) return false;
        if (handoff()) return true;
        const attemptGate=battleExitState();
        if (attemptGate.inBattle && !attemptGate.allowed) {
          recordDiagnostic('battle-complete-exit-blocked',{
            revision:HK_BATTLE_NO_PREMATURE_EXIT_REV,source,attempt,
            reason:attemptGate.reason,swords:attemptGate.swords,
            attackable:attemptGate.attackable
          });
          if (autoMapLeaveModalRoot()) {
            await autoMapRecoverOpenLeaveModal('battle-complete-exit-blocked');
          }
          lastSignature='';
          setTimeout(checkPuzzle,130);
          return false;
        }
        if (roomGone()) {""",
    "per attempt guard")

rep("""      if (!battleRecoverFinalRewardClaimed(source) && !battleFinalRewardClaimed) return false;

      const roomGone=""",
    """      if (!battleRecoverFinalRewardClaimed(source) && !battleFinalRewardClaimed) return false;
      const initialGate=battleExitState();
      if (initialGate.inBattle && !initialGate.allowed) {
        lastSignature='';
        setTimeout(checkPuzzle,110);
        recordDiagnostic('battle-complete-exit-blocked',{
          revision:HK_BATTLE_NO_PREMATURE_EXIT_REV,
          source,reason:initialGate.reason,
          swords:initialGate.swords,attackable:initialGate.attackable
        });
        return false;
      }

      const roomGone=""",
    "completed exit entry guard")

# The generic leave path pauses between checking and tapping. Re-check after
# the pause and again just before the paid confirmation.
rep("""      if (runId!==autoMapRunId || !autoMapEnabled()) return false;
      autoMapLastActionAt=Date.now();

      let firstTap=false;""",
    """      if (runId!==autoMapRunId || !autoMapEnabled()) return false;
      if (/(?:leave|exit)/i.test(String(label||''))) {
        const beforeTapGate=battleExitState();
        if (beforeTapGate.inBattle && !beforeTapGate.allowed) {
          recordDiagnostic('battle-exit-cancel-before-tap',{
            revision:HK_BATTLE_NO_PREMATURE_EXIT_REV,
            label,reason:beforeTapGate.reason,
            swords:beforeTapGate.swords,attackable:beforeTapGate.attackable
          });
          lastSignature='';
          setTimeout(checkPuzzle,100);
          return false;
        }
      }
      autoMapLastActionAt=Date.now();

      let firstTap=false;""",
    "guard after pause")
rep("""      await minigameHumanPause('confirm',{module:'auto-map',label});
      if (runId!==autoMapRunId || !autoMapEnabled()) return false;
      autoMapLastActionAt=Date.now();

      let confirmationSent=false;""",
    """      await minigameHumanPause('confirm',{module:'auto-map',label});
      if (runId!==autoMapRunId || !autoMapEnabled()) return false;
      if (/(?:leave|exit)/i.test(String(label||''))) {
        const beforePayGate=battleExitState();
        if (beforePayGate.inBattle && !beforePayGate.allowed) {
          recordDiagnostic('battle-exit-cancel-before-10',{
            revision:HK_BATTLE_NO_PREMATURE_EXIT_REV,
            label,reason:beforePayGate.reason,
            swords:beforePayGate.swords,attackable:beforePayGate.attackable
          });
          if (autoMapLeaveModalRoot()) {
            await autoMapRecoverOpenLeaveModal('generic-exit-before-10');
          }
          lastSignature='';
          setTimeout(checkPuzzle,100);
          return false;
        }
      }
      autoMapLastActionAt=Date.now();

      let confirmationSent=false;""",
    "generic paid exit guard")

# Before a 10-berry exit opened in a prior tick, the modal recovery guard
# already runs; add immediate re-check after its device-neutral pause.
rep("""      autoMapLastActionAt=Date.now();
      const leaveAccepted=()=> {
        const current=autoMapLeaveModalRoot();""",
    """      const paidExitGate=battleExitState();
      if (paidExitGate.inBattle && !paidExitGate.allowed) {
        const back=battleLeaveBackButton(modal) || autoMapModalCloseButton(modal);
        recordDiagnostic('battle-exit-cancel-before-10',{
          revision:HK_BATTLE_NO_PREMATURE_EXIT_REV,source,
          reason:paidExitGate.reason,attackable:paidExitGate.attackable
        });
        if (back) dispatchAutoMapTap(back,'battle-exit-cancel-back');
        lastSignature='';
        setTimeout(checkPuzzle,100);
        return false;
      }
      autoMapLastActionAt=Date.now();
      const leaveAccepted=()=> {
        const current=autoMapLeaveModalRoot();""",
    "modal paid exit guard")

# Blind success on a reconstructed modal root is a false attack receipt.
start="    async function battleConfirmAlreadyOpenEnemyModal(expectedCost,runId,beforeSignature=null) {"
end="    async function runBattleOpenEnemyModalRecovery("
confirm=r'''    async function battleConfirmAlreadyOpenEnemyModal(expectedCost,runId,beforeSignature=null) {
      const root=battleEnemyModalRoot();
      if (!root) return {handled:false,success:false,reason:'no-modal'};
      const numericExpected=Number(expectedCost);
      const hasExpected=Number.isFinite(numericExpected) && numericExpected>0;
      const before=beforeSignature===null ? getSignature() : beforeSignature;
      const beforeSwords=getBattleAttack();
      const beforeBoard=getBattleBoard().filter(Boolean)
        .map(enemy=>String(enemy.lotId||enemy.slot+':'+enemy.hp)).sort().join('|');
      let action=null,elapsed=Date.now();
      while (Date.now()-elapsed<2200) {
        if (runId!==battleAutoRunId || !battleAutoEnabled()) {
          return {handled:true,success:false,reason:'cancelled'};
        }
        if (!battleEnemyModalRoot()) {
          return {handled:true,success:false,reason:'modal-closed-without-receipt'};
        }
        action=battleEnemyModalActionButton(hasExpected?numericExpected:null);
        if (action) {
          let blocked=!!action.disabled || action.getAttribute?.('aria-disabled')==='true';
          try { blocked=blocked || getComputedStyle(action).pointerEvents==='none'; } catch (_) {}
          if (!blocked) break;
        }
        action=null;
        await new Promise(resolve=>setTimeout(resolve,90));
      }
      const resolvedCost=hasExpected?numericExpected:battleEnemyModalActionCost(action);
      if (!action) {
        recordDiagnostic('battle-open-modal-confirm-wait',{
          revision:HK_BATTLE_ATTACK_RECEIPT_REV,
          expectedCost:hasExpected?numericExpected:null,
          reason:'price-loading-or-disabled'
        });
        return {handled:true,success:false,reason:'price-loading-or-disabled'};
      }
      const ready=await battleScrollTargetIntoViewportAsync(
        action,'battle-open-modal-confirm-'+String(resolvedCost??'auto'),runId
      );
      if (!ready) {
        return {handled:true,success:false,reason:'action-not-clickable'};
      }
      if (!dispatchBattleOverlaySafeTap(action,'battle-open-modal-confirm')) {
        return {handled:true,success:false,reason:'tap-failed'};
      }

      const started=Date.now();
      while (Date.now()-started<5000) {
        if (runId!==battleAutoRunId || !battleAutoEnabled()) {
          return {handled:true,success:false,reason:'cancelled'};
        }
        const afterSwords=getBattleAttack();
        const afterBoard=getBattleBoard().filter(Boolean)
          .map(enemy=>String(enemy.lotId||enemy.slot+':'+enemy.hp)).sort().join('|');
        const swordSpent=Number.isFinite(beforeSwords) &&
          Number.isFinite(afterSwords) && afterSwords<beforeSwords;
        const enemyStateChanged=afterBoard!==beforeBoard;
        const rewardArrived=!!battleVictoryElement() || !!battleVictoryModalRoot();
        if (swordSpent || enemyStateChanged || (rewardArrived && !battleEnemyModalRoot())) {
          recordDiagnostic('battle-attack-receipt-verified',{
            revision:HK_BATTLE_ATTACK_RECEIPT_REV,
            expectedCost:hasExpected?numericExpected:null,
            resolvedCost,swordSpent,enemyStateChanged,rewardArrived,
            beforeSignature:String(before).slice(0,120),
            swordsBefore:beforeSwords,swordsAfter:afterSwords
          });
          return {handled:true,success:true,reason:'server-state-changed',resolvedCost};
        }
        await new Promise(resolve=>setTimeout(resolve,90));
      }
      recordDiagnostic('battle-attack-receipt-pending',{
        revision:HK_BATTLE_ATTACK_RECEIPT_REV,
        expectedCost:hasExpected?numericExpected:null,
        resolvedCost,reason:'no-server-state-change'
      });
      return {handled:true,success:false,reason:'no-server-state-change'};
    }

'''
between(start,end,confirm,"verify real attack receipt")

# A mobile purchase button can remain a spinner after an unacknowledged
# request. Wait for the backend first; after 15 s of identical board/swords,
# close only the actual enemy popup (never a paid exit modal) and rescan.
# Bound recovery to two closures per unchanged server state.
stall=r'''    const battleOpenModalStall={
      key:'',since:0,retries:0,nextAllowed:0
    };

    async function battleRecoverStalledEnemyModal(source='attack-not-accepted') {
      const root=battleEnemyModalRoot();
      if (!root || !battleAutoEnabled()) return false;
      const key=String(getBattleAttack())+'|'+
        getBattleBoard().filter(Boolean)
          .map(enemy=>String(enemy.lotId||enemy.slot+':'+enemy.hp))
          .sort().join('|');
      const now=Date.now();
      if (key!==battleOpenModalStall.key) {
        battleOpenModalStall.key=key;
        battleOpenModalStall.since=now;
        battleOpenModalStall.retries=0;
        battleOpenModalStall.nextAllowed=0;
      }
      if (now<battleOpenModalStall.nextAllowed ||
          now-battleOpenModalStall.since<15000) {
        autoMapStatus('сражение → жду ответ',{
          revision:HK_BATTLE_ATTACK_RECEIPT_REV,source
        });
        return false;
      }
      if (minigameRecentHttpError(0,5000)) {
        battleOpenModalStall.nextAllowed=now+3500;
        return false;
      }
      if (battleOpenModalStall.retries>=2) {
        autoMapStatus('сражение → требуется проверка',{
          revision:HK_BATTLE_ATTACK_RECEIPT_REV,source
        });
        recordDiagnostic('battle-modal-stall-recovery-exhausted',{
          revision:HK_BATTLE_ATTACK_RECEIPT_REV,source,key
        });
        return false;
      }
      const rr=root.getBoundingClientRect?.();
      if (!rr) return false;
      const close=[...root.querySelectorAll(
        'button,[role="button"],a,[onclick],div,span'
      )]
        .filter(element=>element && !element.disabled && visible(element))
        .map(element=>{
          const rect=element.getBoundingClientRect?.();
          const text=clean(element.innerText||element.textContent||'').trim();
          return {element,rect,text};
        })
        .filter(row=>
          row.rect &&
          /^(?:×|✕|Закрыть|Close)$/i.test(row.text) &&
          row.rect.width>0 && row.rect.width<=70 &&
          row.rect.height>0 && row.rect.height<=70 &&
          row.rect.top<rr.top+rr.height*0.42 &&
          row.rect.left>rr.left+rr.width*0.65
        )
        .sort((a,b)=>a.rect.width*a.rect.height-b.rect.width*b.rect.height)[0]?.element;
      if (!close) return false;
      const sent=dispatchBattleOverlaySafeTap(close,'battle-stalled-modal-close');
      if (!sent) return false;
      battleOpenModalStall.retries+=1;
      battleOpenModalStall.since=Date.now();
      battleOpenModalStall.nextAllowed=Date.now()+1500;
      battleInsufficientExitNotBefore=Date.now()+2500;
      lastSignature='';
      recordDiagnostic('battle-modal-stall-recover',{
        revision:HK_BATTLE_ATTACK_RECEIPT_REV,source,
        retries:battleOpenModalStall.retries
      });
      setTimeout(checkPuzzle,1600);
      return true;
    }

'''
rep("    async function runBattleOpenEnemyModalRecovery(source='battle-hard-gate') {",
    stall+"    async function runBattleOpenEnemyModalRecovery(source='battle-hard-gate') {",
    "bounded enemy modal stale recovery")
rep("""        if (!result.success) {
          recordDiagnostic('battle-open-modal-priority-stop',{""",
    """        if (!result.success) {
          await battleRecoverStalledEnemyModal(result.reason);
          recordDiagnostic('battle-open-modal-priority-stop',{""",
    "stalled enemy modal hook")
rep("""        await new Promise(resolve=>setTimeout(resolve,BATTLE_AUTO_SETTLE_MS));
        await dismissBattleRewardIfPresent(runId);
        battleInsufficientExitNotBefore=Date.now()+900;
        recordDiagnostic('battle-open-modal-priority-complete',{""",
    """        battleOpenModalStall.key='';
        battleOpenModalStall.since=0;
        await new Promise(resolve=>setTimeout(resolve,BATTLE_AUTO_SETTLE_MS));
        await dismissBattleRewardIfPresent(runId);
        battleInsufficientExitNotBefore=Date.now()+900;
        recordDiagnostic('battle-open-modal-priority-complete',{""",
    "reset stall after verified attack")

# Only strengthen this selector in the enemy modal, not unrelated earlier selectors.
selector_start=s.find("    function battleEnemyModalActionButton(")
selector_end=s.find("    function battleEnemyModalActionCost(",selector_start)
if selector_start<0 or selector_end<0:
    raise SystemExit("enemy modal action selector missing")
selector=s[selector_start:selector_end]
target=".filter(element=>element && !element.disabled && visible(element))"
updated=""".filter(element=>
          element && !element.disabled &&
          element.getAttribute?.('aria-disabled')!=='true' && visible(element)
        )"""
if selector.count(target)!=1:
    raise SystemExit("enemy modal action filter does not match")
s=s[:selector_start]+selector.replace(target,updated,1)+s[selector_end:]


revexport="      treasuryBattleHandoffRevision:HK_TREASURY_BATTLE_HANDOFF_REV,"
rep(revexport,revexport+"\n      battleNoPrematureExitRevision:HK_BATTLE_NO_PREMATURE_EXIT_REV,\n      battleAttackReceiptRevision:HK_BATTLE_ATTACK_RECEIPT_REV,","revision export")

p.write_text(s,encoding="utf-8")
print("PATCH_BATTLE_STATE_RECEIPT_1_18_99=PASS")
