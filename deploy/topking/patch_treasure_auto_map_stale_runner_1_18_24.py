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

rep("// @version      1.18.23",
    "// @version      1.18.24\n// @release-note Автокарта: после возврата на реальную карту зависшие running-флаги старой мини-игры больше не блокируют следующую клетку. Если активная клетка карты действительно находится сверху, а мини-игра уже нет, старый runner отменяется по runId и Автокарта продолжает маршрут сама.",
    "version")
rep("const BUILD_VERSION = '1.18.23';",
    "const BUILD_VERSION = '1.18.24';",
    "build")
rep("  const HK_TREASURE_CHEST_ELEMENT_STATE_REV='treasure-chest-element-state-20260927-r1';",
    "  const HK_TREASURE_CHEST_ELEMENT_STATE_REV='treasure-chest-element-state-20260927-r1';\n  const HK_TREASURE_AUTO_MAP_STALE_RUNNER_REV='treasure-auto-map-stale-runner-20260927-r2';",
    "revision")

anchor="""    function autoMapModulesRunning() {
      return !!(battleAutoRunning || chestAutoRunning || lightsAutoRunning || fishingAutoRunning || traderAutoRunning);
    }
"""
if s.count(anchor)!=1:
    raise SystemExit("modules running anchor missing")
helpers=anchor+"""
    function autoMapMapIsForeground() {
      const rows=autoMapMapCards();
      return rows.some(row=>autoMapElementIsForeground(row.element));
    }

    function autoMapCancelStaleRunners(reason='map-foreground') {
      const cancelled=[];
      if (battleAutoRunning) {
        battleAutoRunId+=1;
        battleAutoRunning=false;
        cancelled.push('battle');
      }
      if (chestAutoRunning) {
        chestAutoRunId+=1;
        chestAutoRunning=false;
        cancelled.push('chests');
      }
      if (lightsAutoRunning) {
        lightsAutoRunId+=1;
        lightsAutoRunning=false;
        cancelled.push('lights');
      }
      if (fishingAutoRunning) {
        fishingAutoRunId+=1;
        fishingAutoRunning=false;
        cancelled.push('fishing');
      }
      if (traderAutoRunning) {
        traderAutoRunId+=1;
        traderAutoRunning=false;
        cancelled.push('trader');
      }
      if (cancelled.length) {
        lastSignature='';
        recordDiagnostic('treasure-auto-map-stale-runner-cancel',{
          revision:HK_TREASURE_AUTO_MAP_STALE_RUNNER_REV,
          reason,
          cancelled,
          activeCells:autoMapActiveCellCount()
        });
      }
      return cancelled;
    }
"""
s=s.replace(anchor,helpers,1)

old="""      if (autoMapModulesRunning()) {
        autoMapReturnNotBefore=Date.now()+AUTO_MAP_RETURN_SETTLE_MS;
        autoMapStatus('мини-игра');
        return false;
      }
"""
new="""      if (autoMapModulesRunning()) {
        const minigameForeground=autoMapMiniGameForeground();
        const mapForeground=autoMapMapIsForeground();
        if (mapForeground && !minigameForeground) {
          autoMapCancelStaleRunners('real-map-foreground');
          autoMapReturnNotBefore=Date.now()+350;
          autoMapStatus('возврат на карту');
          return false;
        }

        autoMapReturnNotBefore=Date.now()+AUTO_MAP_RETURN_SETTLE_MS;
        autoMapStatus('мини-игра');
        return false;
      }
"""
rep(old,new,"running gate")

rep("      treasureChestElementStateRevision:HK_TREASURE_CHEST_ELEMENT_STATE_REV,\n      start,",
    "      treasureChestElementStateRevision:HK_TREASURE_CHEST_ELEMENT_STATE_REV,\n      treasureAutoMapStaleRunnerRevision:HK_TREASURE_AUTO_MAP_STALE_RUNNER_REV,\n      start,",
    "export revision")

for marker in [
    "// @version      1.18.24",
    "const BUILD_VERSION = '1.18.24';",
    "treasure-auto-map-stale-runner-20260927-r2",
    "function autoMapMapIsForeground()",
    "function autoMapCancelStaleRunners",
    "battleAutoRunId+=1",
    "chestAutoRunId+=1",
    "lightsAutoRunId+=1",
    "fishingAutoRunId+=1",
    "traderAutoRunId+=1",
    "treasure-auto-map-stale-runner-cancel",
    "treasure-chest-element-state-20260927-r1"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("TREASURE_AUTO_MAP_STALE_RUNNER_1_18_24=PASS")
