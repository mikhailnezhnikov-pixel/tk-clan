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

rep("// @version      1.18.51",
    "// @version      1.18.52\n// @release-note Сражения: введено строгое правило выхода. Покинуть боевую локацию можно только после получения финального сундука либо когда среди оставшихся врагов нет ни одного, кого можно атаковать текущим запасом мечей. Невозможность полной зачистки больше не является причиной выхода. Если окно выхода открылось преждевременно, Автокарта сама нажимает «Назад» и продолжает бой.",
    "version")
rep("const BUILD_VERSION = '1.18.51';",
    "const BUILD_VERSION = '1.18.52';",
    "build")
rep("  const HK_BATTLE_AUTOMAP_FULL_CLEAR_REV='battle-automap-full-clear-20260927-r1';",
    "  const HK_BATTLE_AUTOMAP_FULL_CLEAR_REV='battle-automap-full-clear-20260927-r1';\n  const HK_BATTLE_STRICT_EXIT_REV='battle-strict-exit-gate-20260927-r1';",
    "revision")

rep("    let battleInsufficientExitNotBefore = 0;\n    let chestAutoRunning = false;",
    "    let battleInsufficientExitNotBefore = 0;\n    let battleFinalRewardClaimed = false;\n    let battleFinalRewardClaimedAt = 0;\n    let chestAutoRunning = false;",
    "battle final reward state")

anchor="""    function runBattle() {
"""
helper="""    function battleExitState() {
      const signature=String(getSignature()||'');
      const board=getBattleBoard();
      const enemies=board.filter(enemy=>enemy && visible(enemy.element));
      const swords=getBattleAttack();
      const rewardPending=!!battleVictoryElement() || !!battleVictoryModalRoot();
      const inBattle=
        signature.startsWith('BATTLE') ||
        enemies.length>0 ||
        rewardPending;

      if (enemies.length>0 && battleFinalRewardClaimed) {
        battleFinalRewardClaimed=false;
        battleFinalRewardClaimedAt=0;
      }

      if (!inBattle) {
        return {inBattle:false,allowed:true,reason:'not-battle',swords,enemies:0,attackable:0};
      }

      if (rewardPending) {
        return {
          inBattle:true,
          allowed:false,
          reason:'final-reward-pending',
          swords,
          enemies:enemies.length,
          attackable:0
        };
      }

      if (battleFinalRewardClaimed) {
        return {
          inBattle:true,
          allowed:true,
          reason:'final-reward-claimed',
          swords,
          enemies:enemies.length,
          attackable:0,
          claimedAt:battleFinalRewardClaimedAt
        };
      }

      if (!enemies.length) {
        return {
          inBattle:true,
          allowed:false,
          reason:'waiting-final-reward',
          swords,
          enemies:0,
          attackable:0
        };
      }

      if (!Number.isFinite(swords)) {
        return {
          inBattle:true,
          allowed:false,
          reason:'swords-unknown',
          swords:null,
          enemies:enemies.length,
          attackable:0
        };
      }

      const attackable=enemies.filter(enemy=>Number(enemy.hp)>0 && Number(enemy.hp)<=swords);
      if (attackable.length>0) {
        return {
          inBattle:true,
          allowed:false,
          reason:'attack-available',
          swords,
          enemies:enemies.length,
          attackable:attackable.length,
          slots:attackable.map(enemy=>enemy.slot).slice(0,12)
        };
      }

      return {
        inBattle:true,
        allowed:true,
        reason:'no-attack-available',
        swords,
        enemies:enemies.length,
        attackable:0
      };
    }

    function battleLeaveBackButton(root=autoMapLeaveModalRoot()) {
      if (!root) return null;
      const rows=[...root.querySelectorAll('button,[role="button"],a,[onclick],div,span')]
        .filter(element=>element && !element.disabled && visible(element))
        .map(element=>({
          element,
          text:clean(element.innerText||element.textContent||'').trim(),
          rect:element.getBoundingClientRect?.() || {width:0,height:0}
        }))
        .filter(row=>/^(?:Назад|Back|Отмена|Cancel)$/i.test(row.text))
        .sort((a,b)=>a.rect.width*a.rect.height-b.rect.width*b.rect.height);
      return rows[0]?.element || null;
    }

"""
if s.count(anchor)!=1:
    raise SystemExit("runBattle anchor missing")
s=s.replace(anchor,helper+anchor,1)

old_run="""    function runBattle() {
      // AutoMap owns orchestration, but it must not suppress the battle solver.
      // Fight whenever a complete clear is possible. The existing
      // runBattleInsufficientExit() remains the only route that leaves without
      // fighting, and only after the solver proves that a full clear is not
      // possible with the current sword budget.
      if (autoMapEnabled()) {
        autoMapStatus('сражение',{
          revision:HK_BATTLE_AUTOMAP_FULL_CLEAR_REV
        });
      }

      const maxAttack = getBattleAttack();
      if (maxAttack === null) return false;
      const board = getBattleBoard();
      const enemies = board.filter(enemy => enemy !== null);
      if (enemies.length === 0) return false;
      clearNumbers();
      const state = board.map(enemy => enemy ? {type:enemy.type,hp:enemy.hp,alive:true} : null);
      const totalHp=state.reduce((sum,enemy)=>sum+(enemy&&enemy.alive?Math.max(0,Number(enemy.hp)||0):0),0);
      const solution = solveBattle(state,maxAttack);
      const solverKilled=Number(solution?.killed||0);
      const insufficientByHp=totalHp>maxAttack;
      const insufficientBySolver=solverKilled<enemies.length;

      if (insufficientByHp || insufficientBySolver) {
        console.log('HK BATTLE: полная зачистка невозможна — выходим');
        console.log('HK BATTLE мечей:',maxAttack,'HP:',totalHp,'решатель:',solverKilled,'из',enemies.length);
        recordDiagnostic('battle-full-clear-insufficient',{
          revision:HK_BATTLE_FULL_CLEAR_EXIT_REV,
          swords:maxAttack,
          totalHp,
          enemies:enemies.length,
          solverKilled,
          solutionCost:Number(solution?.cost||0),
          insufficientByHp,
          insufficientBySolver
        });
        if (battleAutoEnabled() && !battleAutoRunning) {
          void runBattleInsufficientExit({
            swords:maxAttack,
            totalHp,
            enemies:enemies.length,
            solverKilled,
            reason:insufficientByHp?'hp-over-swords':'solver-no-full-clear'
          });
        }
        return true;
      }

      if (!solution || solution.order.length === 0) return true;
"""
new_run="""    function runBattle() {
      // AutoMap owns orchestration, but battle always keeps attacking while at
      // least one legal target exists. It is NOT necessary to prove that the
      // whole room can be cleared before starting/continuing the fight.
      if (autoMapEnabled()) {
        autoMapStatus('сражение',{
          revision:HK_BATTLE_STRICT_EXIT_REV
        });
      }

      const maxAttack = getBattleAttack();
      if (maxAttack === null) return false;
      const board = getBattleBoard();
      const enemies = board.filter(enemy => enemy !== null);
      if (enemies.length === 0) return false;

      battleFinalRewardClaimed=false;
      battleFinalRewardClaimedAt=0;

      clearNumbers();
      const state = board.map(enemy => enemy ? {type:enemy.type,hp:enemy.hp,alive:true} : null);
      const totalHp=state.reduce((sum,enemy)=>sum+(enemy&&enemy.alive?Math.max(0,Number(enemy.hp)||0):0),0);
      const solution = solveBattle(state,maxAttack);
      const solverKilled=Number(solution?.killed||0);

      if (!solution || solution.order.length===0) {
        console.log('HK BATTLE: доступных атак больше нет — разрешён выход');
        recordDiagnostic('battle-no-legal-attack',{
          revision:HK_BATTLE_STRICT_EXIT_REV,
          swords:maxAttack,
          totalHp,
          enemies:enemies.length,
          solverKilled
        });
        if (battleAutoEnabled() && !battleAutoRunning) {
          void runBattleInsufficientExit({
            swords:maxAttack,
            totalHp,
            enemies:enemies.length,
            solverKilled,
            reason:'no-legal-attack'
          });
        }
        return true;
      }
"""
rep(old_run,new_run,"strict runBattle rule")

# Successful final chest claim is the first explicit allowed-exit condition.
rep("""        const success=!battleVictoryModalRoot();
        recordDiagnostic('battle-victory-claim-complete',{""",
    """        const success=!battleVictoryModalRoot();
        if (success) {
          battleFinalRewardClaimed=true;
          battleFinalRewardClaimedAt=Date.now();
        }
        recordDiagnostic('battle-victory-claim-complete',{""",
    "mark final battle reward claimed")

# Guard the insufficient-swords exit itself so no stale caller can bypass rule.
old_insufficient_start="""    async function runBattleInsufficientExit(info={}) {
      if (!battleAutoEnabled() || battleAutoRunning || Date.now()<battleInsufficientExitNotBefore) return false;
      const exit=autoMapExitButton();
"""
new_insufficient_start="""    async function runBattleInsufficientExit(info={}) {
      if (!battleAutoEnabled() || battleAutoRunning || Date.now()<battleInsufficientExitNotBefore) return false;

      let gate=battleExitState();
      if (!gate.allowed) {
        recordDiagnostic('battle-insufficient-exit-blocked',{
          revision:HK_BATTLE_STRICT_EXIT_REV,
          reason:gate.reason,
          swords:gate.swords,
          enemies:gate.enemies,
          attackable:gate.attackable
        });
        battleInsufficientExitNotBefore=Date.now()+900;
        lastSignature='';
        setTimeout(checkPuzzle,120);
        return false;
      }

      const exit=autoMapExitButton();
"""
rep(old_insufficient_start,new_insufficient_start,"guard insufficient exit")

rep("""        if (runId!==battleAutoRunId || !battleAutoEnabled()) return false;

        if (autoMapEnabled()) {""",
    """        if (runId!==battleAutoRunId || !battleAutoEnabled()) return false;

        gate=battleExitState();
        if (!gate.allowed) {
          recordDiagnostic('battle-insufficient-exit-blocked',{
            revision:HK_BATTLE_STRICT_EXIT_REV,
            reason:gate.reason,
            swords:gate.swords,
            enemies:gate.enemies,
            attackable:gate.attackable,
            phase:'post-pause'
          });
          return false;
        }

        if (autoMapEnabled()) {""",
    "recheck insufficient exit",1)

# Generic leave action gate prevents any old or future battle exit path.
old_tap_start="""    async function autoMapTapAndConfirm(element,label,costHint=null) {
      if (!element || !visible(element) || !autoMapEnabled()) return false;
      await autoMapWaitActionGap();
"""
new_tap_start="""    async function autoMapTapAndConfirm(element,label,costHint=null) {
      if (!element || !visible(element) || !autoMapEnabled()) return false;

      if (/(?:leave|exit)/i.test(String(label||''))) {
        const battleGate=battleExitState();
        if (battleGate.inBattle && !battleGate.allowed) {
          recordDiagnostic('battle-exit-guard',{
            revision:HK_BATTLE_STRICT_EXIT_REV,
            label:String(label||''),
            reason:battleGate.reason,
            swords:battleGate.swords,
            enemies:battleGate.enemies,
            attackable:battleGate.attackable
          });
          autoMapStatus('бой продолжается',{
            reason:battleGate.reason,
            swords:battleGate.swords,
            attackable:battleGate.attackable
          });
          return false;
        }
      }

      await autoMapWaitActionGap();
"""
rep(old_tap_start,new_tap_start,"generic battle exit guard")

# An already-open premature exit modal must be cancelled, not confirmed.
old_recover="""    async function autoMapRecoverOpenLeaveModal(source='leave-modal-recovery') {
      if (!autoMapEnabled()) return false;
      const modal=autoMapLeaveModalRoot();
      if (!modal) return false;

      const button=autoMapLeaveConfirmButton(modal,10);
"""
new_recover="""    async function autoMapRecoverOpenLeaveModal(source='leave-modal-recovery') {
      if (!autoMapEnabled()) return false;
      const modal=autoMapLeaveModalRoot();
      if (!modal) return false;

      const battleGate=battleExitState();
      if (battleGate.inBattle && !battleGate.allowed) {
        const back=battleLeaveBackButton(modal);
        recordDiagnostic('battle-leave-modal-blocked',{
          revision:HK_BATTLE_STRICT_EXIT_REV,
          source,
          reason:battleGate.reason,
          swords:battleGate.swords,
          enemies:battleGate.enemies,
          attackable:battleGate.attackable,
          hasBack:!!back
        });
        autoMapStatus('бой продолжается',{
          reason:battleGate.reason,
          swords:battleGate.swords,
          attackable:battleGate.attackable
        });
        if (back && dispatchAutoMapTap(back,'battle-exit-blocked-back')) {
          autoMapLastActionAt=Date.now();
          await new Promise(resolve=>setTimeout(resolve,280));
          lastSignature='';
          setTimeout(checkPuzzle,80);
          return true;
        }
        return false;
      }

      const button=autoMapLeaveConfirmButton(modal,10);
"""
rep(old_recover,new_recover,"cancel premature battle leave modal")

# Legacy skip helper is kept only for compatibility but obeys the same gate.
rep("""    async function autoMapSkipBattleWithoutFight() {
      if (!autoMapEnabled()) return false;
      const signature=getSignature();
      if (!signature.startsWith('BATTLE')) return false;
""",
    """    async function autoMapSkipBattleWithoutFight() {
      if (!autoMapEnabled()) return false;
      const signature=getSignature();
      if (!signature.startsWith('BATTLE')) return false;
      const strictGate=battleExitState();
      if (!strictGate.allowed) {
        recordDiagnostic('battle-legacy-skip-blocked',{
          revision:HK_BATTLE_STRICT_EXIT_REV,
          reason:strictGate.reason,
          swords:strictGate.swords,
          enemies:strictGate.enemies,
          attackable:strictGate.attackable
        });
        return false;
      }
""",
    "guard legacy battle skip")

rep("      battleAutoMapFullClearRevision:HK_BATTLE_AUTOMAP_FULL_CLEAR_REV,\n      traderWhitelistRevision:HK_TRADER_WHITELIST_REV,",
    "      battleAutoMapFullClearRevision:HK_BATTLE_AUTOMAP_FULL_CLEAR_REV,\n      battleStrictExitRevision:HK_BATTLE_STRICT_EXIT_REV,\n      traderWhitelistRevision:HK_TRADER_WHITELIST_REV,",
    "export strict battle exit revision")

for marker in [
    "// @version      1.18.52",
    "const BUILD_VERSION = '1.18.52';",
    "battle-strict-exit-gate-20260927-r1",
    "function battleExitState()",
    "function battleLeaveBackButton",
    "reason:'attack-available'",
    "reason:'no-attack-available'",
    "if (!solution || solution.order.length===0)",
    "reason:'no-legal-attack'",
    "battle-insufficient-exit-blocked",
    "battle-exit-guard",
    "battle-leave-modal-blocked",
    "battle-exit-blocked-back",
    "battleFinalRewardClaimed=true",
    "treasure-chest-fast-pacing-20260927-r1",
    "treasure-lights-outer-modal-20260927-r1"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("TREASURE_BATTLE_STRICT_EXIT_1_18_52=PASS")
