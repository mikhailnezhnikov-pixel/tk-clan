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

rep("// @version      1.18.50",
    "// @version      1.18.51\n// @release-note Сражения на Автокарте снова проходят автоматически. Полный пропуск боя удалён: если текущего запаса мечей хватает на полную зачистку по решателю, Автосражение атакует врагов до победы и забирает награду. Выход из локации остаётся только запасным сценарием, когда полной зачистки действительно не хватает по мечам/решению.",
    "version")
rep("const BUILD_VERSION = '1.18.50';",
    "const BUILD_VERSION = '1.18.51';",
    "build")
rep("  const HK_TREASURE_CHEST_FAST_PACING_REV='treasure-chest-fast-pacing-20260927-r1';",
    "  const HK_TREASURE_CHEST_FAST_PACING_REV='treasure-chest-fast-pacing-20260927-r1';\n  const HK_BATTLE_AUTOMAP_FULL_CLEAR_REV='battle-automap-full-clear-20260927-r1';",
    "revision")

old_run="""    function runBattle() {
      if (autoMapEnabled()) {
        recordDiagnostic('battle-auto-skip-owned-by-map',{
          revision:HK_BATTLE_SKIP_CANON_REV
        });
        setTimeout(()=>void runAutoMapTick('battle-skip-owned-by-map'),20);
        return true;
      }

      const maxAttack = getBattleAttack();
"""
new_run="""    function runBattle() {
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
"""
rep(old_run,new_run,"restore runBattle under AutoMap")

old_owner="""      if (sig.startsWith('LIGHTS|')) {
        name='lights';
        enabled=lightsAutoEnabled;
        enable=()=>setLightsAutoEnabled(true);
      } else if (sig.startsWith('CHESTS|')) {
"""
new_owner="""      if (sig.startsWith('BATTLE|') || sig.startsWith('BATTLE_REWARD')) {
        name='battle';
        enabled=battleAutoEnabled;
        enable=()=>setBattleAutoEnabled(true);
      } else if (sig.startsWith('LIGHTS|')) {
        name='lights';
        enabled=lightsAutoEnabled;
        enable=()=>setLightsAutoEnabled(true);
      } else if (sig.startsWith('CHESTS|')) {
"""
rep(old_owner,new_owner,"AutoMap owns battle toggle")

old_tick="""        if (signature.startsWith('BATTLE')) {
          // Canon from recording #9: do not perform any fight while AutoMap owns
          // the room. Acknowledge the intro, leave the location, pay 10, resume map.
          if (battleAutoRunning) {
            battleAutoRunId+=1;
            battleAutoRunning=false;
            recordDiagnostic('battle-auto-cancel-for-skip',{
              revision:HK_BATTLE_SKIP_CANON_REV
            });
          }
          return await autoMapSkipBattleWithoutFight();
        }
"""
new_tick="""        if (signature.startsWith('BATTLE')) {
          // Battle is a normal child module of AutoMap. Let the solver perform a
          // complete clear whenever possible; only runBattleInsufficientExit()
          // may leave the room without fighting.
          autoMapStatus('сражение',{
            revision:HK_BATTLE_AUTOMAP_FULL_CLEAR_REV
          });
          if (!battleAutoEnabled()) {
            setBattleAutoEnabled(true);
            lastSignature='';
          }
          if (!battleAutoRunning) {
            lastSignature='';
            setTimeout(checkPuzzle,20);
          }
          return true;
        }
"""
rep(old_tick,new_tick,"AutoMap battle branch")

old_check="""      if (isBattle) {
        if (autoMapEnabled()) {
          recordDiagnostic('battle-skip-dispatch',{
            revision:HK_BATTLE_SKIP_CANON_REV
          });
          setTimeout(()=>void runAutoMapTick('battle-skip-check-puzzle'),20);
          return;
        }
        runBattle();
        return;
      }
"""
new_check="""      if (isBattle) {
        runBattle();
        return;
      }
"""
rep(old_check,new_check,"checkPuzzle battle dispatch")

rep("      treasureChestFastPacingRevision:HK_TREASURE_CHEST_FAST_PACING_REV,\n      traderWhitelistRevision:HK_TRADER_WHITELIST_REV,",
    "      treasureChestFastPacingRevision:HK_TREASURE_CHEST_FAST_PACING_REV,\n      battleAutoMapFullClearRevision:HK_BATTLE_AUTOMAP_FULL_CLEAR_REV,\n      traderWhitelistRevision:HK_TRADER_WHITELIST_REV,",
    "export battle revision")

for marker in [
    "// @version      1.18.51",
    "const BUILD_VERSION = '1.18.51';",
    "battle-automap-full-clear-20260927-r1",
    "autoMapStatus('сражение'",
    "const solution = solveBattle(state,maxAttack);",
    "void runBattleInsufficientExit({",
    "void runBattleAuto(solution);",
    "sig.startsWith('BATTLE|') || sig.startsWith('BATTLE_REWARD')",
    "enabled=battleAutoEnabled",
    "setBattleAutoEnabled(true)",
    "treasure-chest-fast-pacing-20260927-r1",
    "treasure-lights-outer-modal-20260927-r1"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("TREASURE_BATTLE_FULL_CLEAR_1_18_51=PASS")
