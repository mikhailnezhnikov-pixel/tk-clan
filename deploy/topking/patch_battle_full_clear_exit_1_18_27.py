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

rep("// @version      1.18.26",
    "// @version      1.18.27\n// @release-note Сражение: если оставшегося запаса мечей недостаточно для полной зачистки всех мобов, автобой больше не тратит мечи частично. Перед следующим ударом HK сравнивает суммарный HP с остатком мечей и дополнительно проверяет полный план решателем; при невозможности зачистки автоматически нажимает «Покинуть локацию».",
    "version")
rep("const BUILD_VERSION = '1.18.26';",
    "const BUILD_VERSION = '1.18.27';",
    "build")
rep("  const HK_MINIGAME_HUMAN_PACING_REV='minigame-human-pacing-20260927-r1';",
    "  const HK_MINIGAME_HUMAN_PACING_REV='minigame-human-pacing-20260927-r1';\n  const HK_BATTLE_FULL_CLEAR_EXIT_REV='battle-full-clear-exit-20260927-r1';",
    "revision")

rep("    let battleAutoToggle = null;",
    "    let battleAutoToggle = null;\n    let battleInsufficientExitNotBefore = 0;",
    "battle exit retry state")

anchor="""    function addNumber(element, number) {
"""
if s.count(anchor)!=1:
    raise SystemExit("battle helper anchor missing")

helper="""    async function runBattleInsufficientExit(info={}) {
      if (!battleAutoEnabled() || battleAutoRunning || Date.now()<battleInsufficientExitNotBefore) return false;
      const exit=autoMapExitButton();
      if (!exit) {
        battleInsufficientExitNotBefore=Date.now()+1800;
        recordDiagnostic('battle-full-clear-exit-wait',{
          revision:HK_BATTLE_FULL_CLEAR_EXIT_REV,
          reason:'leave-location-button-missing',
          swords:Number(info.swords||0),
          totalHp:Number(info.totalHp||0),
          enemies:Number(info.enemies||0)
        });
        return false;
      }

      battleAutoRunning=true;
      const runId=++battleAutoRunId;
      let success=false;
      recordDiagnostic('battle-full-clear-exit-start',{
        revision:HK_BATTLE_FULL_CLEAR_EXIT_REV,
        swords:Number(info.swords||0),
        totalHp:Number(info.totalHp||0),
        enemies:Number(info.enemies||0),
        solverKilled:Number(info.solverKilled||0),
        reason:String(info.reason||'insufficient')
      });

      try {
        await minigameHumanPause('scan',{
          module:'battle-insufficient-exit',
          swords:Number(info.swords||0),
          totalHp:Number(info.totalHp||0)
        });
        if (runId!==battleAutoRunId || !battleAutoEnabled()) return false;

        if (autoMapEnabled()) {
          autoMapStatus('не хватает мечей',{
            swords:Number(info.swords||0),
            totalHp:Number(info.totalHp||0),
            enemies:Number(info.enemies||0)
          });
          success=await autoMapTapAndConfirm(exit,'battle-insufficient-swords-exit',null);
        } else {
          const before=getSignature();
          if (!dispatchBattleTap(exit,'battle-insufficient-swords-exit')) return false;

          let modal=null;
          const modalDeadline=Date.now()+2600;
          while (Date.now()<modalDeadline) {
            if (runId!==battleAutoRunId || !battleAutoEnabled()) return false;
            if (getSignature()!==before) {
              success=true;
              break;
            }
            modal=treasureModalRoot(null);
            if (modal) break;
            await new Promise(resolve=>setTimeout(resolve,90));
          }

          if (!success && modal) {
            let action=null;
            const actionDeadline=Date.now()+1800;
            while (Date.now()<actionDeadline) {
              if (runId!==battleAutoRunId || !battleAutoEnabled()) return false;
              action=autoMapModalPrimaryButton(modal,null);
              if (action) break;
              await new Promise(resolve=>setTimeout(resolve,90));
            }
            if (action) {
              await minigameHumanPause('confirm',{module:'battle-insufficient-exit'});
              if (runId!==battleAutoRunId || !battleAutoEnabled()) return false;
              if (dispatchBattleTap(action,'battle-insufficient-swords-confirm')) {
                const changed=await waitBattleSignatureChange(before,runId);
                success=changed || !getSignature().startsWith('BATTLE');
              }
            }
          }
        }

        battleInsufficientExitNotBefore=success ? 0 : Date.now()+2600;
        recordDiagnostic('battle-full-clear-exit-complete',{
          revision:HK_BATTLE_FULL_CLEAR_EXIT_REV,
          success,
          swords:Number(info.swords||0),
          totalHp:Number(info.totalHp||0),
          enemies:Number(info.enemies||0)
        });
        return success;
      } finally {
        if (runId===battleAutoRunId) battleAutoRunning=false;
        lastSignature='';
        setTimeout(checkPuzzle,success?1200:1500);
      }
    }

"""
s=s.replace(anchor,helper+anchor,1)

old_run="""    function runBattle() {
      const maxAttack = getBattleAttack();
      if (maxAttack === null) return false;
      const board = getBattleBoard();
      const enemies = board.filter(enemy => enemy !== null);
      if (enemies.length === 0) return false;
      clearNumbers();
      const state = board.map(enemy => enemy ? {type:enemy.type,hp:enemy.hp,alive:true} : null);
      const solution = solveBattle(state,maxAttack);
      if (!solution || solution.order.length === 0) return true;
      solution.order.forEach((position,index) => {
        const enemy = board[position];
        if (enemy?.element) addNumber(enemy.element,index + 1);
      });
      console.log('HK BATTLE ATK:',maxAttack);
      console.log('HK BATTLE потрачено:',solution.cost);
      console.log('HK BATTLE уничтожено:',solution.killed,'из',enemies.length);
      console.log('HK BATTLE нажать слоты:',solution.order.map(pos => pos + BATTLE_FIRST_SLOT));
      if (battleAutoEnabled() && !battleAutoRunning) void runBattleAuto(solution);
      return true;
    }"""

new_run="""    function runBattle() {
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
      solution.order.forEach((position,index) => {
        const enemy = board[position];
        if (enemy?.element) addNumber(enemy.element,index + 1);
      });
      console.log('HK BATTLE ATK:',maxAttack);
      console.log('HK BATTLE HP:',totalHp);
      console.log('HK BATTLE потрачено:',solution.cost);
      console.log('HK BATTLE уничтожено:',solution.killed,'из',enemies.length);
      console.log('HK BATTLE нажать слоты:',solution.order.map(pos => pos + BATTLE_FIRST_SLOT));
      if (battleAutoEnabled() && !battleAutoRunning) void runBattleAuto(solution);
      return true;
    }"""
rep(old_run,new_run,"battle full-clear guard")

rep("""          // Battle module owns the whole battle until victory/reward state is gone.
          // Never press the persistent "Покинуть локацию" while enemies remain.""",
    """          // Battle module owns the room. It may leave the location itself when
          // the full-clear guard proves that the remaining swords cannot clear all mobs.
          // AutoMap must not press the persistent exit button independently.""",
    "automap battle comment")

rep("      minigameHumanPacingRevision:HK_MINIGAME_HUMAN_PACING_REV,\n      start,",
    "      minigameHumanPacingRevision:HK_MINIGAME_HUMAN_PACING_REV,\n      battleFullClearExitRevision:HK_BATTLE_FULL_CLEAR_EXIT_REV,\n      start,",
    "export revision")

for marker in [
    "// @version      1.18.27",
    "const BUILD_VERSION = '1.18.27';",
    "battle-full-clear-exit-20260927-r1",
    "async function runBattleInsufficientExit",
    "const totalHp=state.reduce",
    "const insufficientByHp=totalHp>maxAttack;",
    "const insufficientBySolver=solverKilled<enemies.length;",
    "battle-insufficient-swords-exit",
    "battleFullClearExitRevision:HK_BATTLE_FULL_CLEAR_EXIT_REV",
    "minigame-human-pacing-20260927-r1",
    "trader-approved-lots-20260927-r1",
    "fishing-live-budget-20260927-r1"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("BATTLE_FULL_CLEAR_EXIT_1_18_27=PASS")
