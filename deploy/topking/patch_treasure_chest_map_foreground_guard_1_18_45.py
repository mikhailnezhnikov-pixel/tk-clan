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

rep("// @version      1.18.44",
    "// @version      1.18.45\n// @release-note Карта сокровищ: клетки карты больше не принимаются за мини-игру «Сундуки». Пока реальная активная клетка карты находится на переднем плане, детектор сундуков блокируется, Автосундуки не стартуют и Автокарта продолжает маршрут. При входе в настоящую комнату сундуков защита автоматически снимается.",
    "version")
rep("const BUILD_VERSION = '1.18.44';",
    "const BUILD_VERSION = '1.18.45';",
    "build")
rep("  const HK_TREASURE_AUTO_MAP_STALE_RUNNER_REV='treasure-auto-map-stale-runner-20260927-r2';",
    "  const HK_TREASURE_AUTO_MAP_STALE_RUNNER_REV='treasure-auto-map-stale-runner-20260927-r2';\n  const HK_TREASURE_CHEST_MAP_GUARD_REV='treasure-chest-map-foreground-guard-20260927-r1';",
    "revision")

# Do not count chest-like descendants rendered inside an active route card as
# chest-room controls. These decorations share the game's chest lot-id prefix.
old_elements_tail="""        })
        .filter(row=>row.lotId && !row.lotId.includes('_empty_spot') && !row.lotId.includes('_bought_'));
    }
"""
new_elements_tail="""        })
        .filter(row=>
          row.lotId &&
          !row.lotId.includes('_empty_spot') &&
          !row.lotId.includes('_bought_') &&
          !row.element.closest?.('[data-lot-id^="mf_treasurelot_active_sl"]')
        );
    }
"""
rep(old_elements_tail,new_elements_tail,"exclude map-card chest descendants")

# Add a z-order based truth guard. "visible()" alone does not account for
# occlusion and was the root of the false CHESTS signature on the route board.
anchor="""    function autoMapMiniGameForeground() {
"""
helper="""    function treasureChestBlockedByForegroundMap(chestRows=treasureChestElements()) {
      if (!treasureGuideScreenVisible()) return false;

      const mapRows=[...document.querySelectorAll('[data-lot-id^="mf_treasurelot_active_sl"]')]
        .filter(visible)
        .filter(autoMapElementIsForeground);

      if (!mapRows.length) return false;

      const now=Date.now();
      const last=Number(treasureChestBlockedByForegroundMap.lastLoggedAt||0);
      if (now-last>=3000) {
        treasureChestBlockedByForegroundMap.lastLoggedAt=now;
        recordDiagnostic('treasure-chest-map-false-positive-blocked',{
          revision:HK_TREASURE_CHEST_MAP_GUARD_REV,
          activeMapLots:mapRows
            .map(element=>String(element.getAttribute('data-lot-id')||''))
            .filter(Boolean)
            .slice(0,16),
          chestLikeLots:(Array.isArray(chestRows)?chestRows:[])
            .map(row=>String(row?.lotId||''))
            .filter(Boolean)
            .slice(0,24)
        });
      }
      return true;
    }

"""
if s.count(anchor)!=1:
    raise SystemExit("mini-game foreground anchor missing")
s=s.replace(anchor,helper+anchor,1)

# A chest runner must never click while the route board itself is the real
# foreground. Re-check after the human scan pause as the UI may have changed.
old_chest_start="""    async function runTreasureChestAuto() {
      if (!chestAutoEnabled() || chestAutoRunning || battleAutoRunning) return false;
      let target=treasureChestTarget();
      if (!target) return false;
      await minigameHumanPause('scan',{module:'chests'});
      if (!chestAutoEnabled()) return false;
      target=treasureChestTarget();
      if (!target) return false;
"""
new_chest_start="""    async function runTreasureChestAuto() {
      if (!chestAutoEnabled() || chestAutoRunning || battleAutoRunning) return false;
      if (treasureChestBlockedByForegroundMap()) {
        lastSignature='';
        if (autoMapEnabled()) setTimeout(()=>void runAutoMapTick('chest-map-guard-pre'),20);
        return false;
      }
      let target=treasureChestTarget();
      if (!target) return false;
      await minigameHumanPause('scan',{module:'chests'});
      if (!chestAutoEnabled()) return false;
      if (treasureChestBlockedByForegroundMap()) {
        lastSignature='';
        if (autoMapEnabled()) setTimeout(()=>void runAutoMapTick('chest-map-guard-post'),20);
        return false;
      }
      target=treasureChestTarget();
      if (!target) return false;
"""
rep(old_chest_start,new_chest_start,"guard chest runner")

# Signature classification is the central fix: a foreground route board wins
# over stale/upcoming chest DOM. Once the room replaces/covers the map, the
# guard becomes false and the normal CHESTS signature is restored.
old_signature="""      const chestRows=treasureChestElements();
      if (chestRows.length>=3) return treasureChestSignature();
      return 'NONE';
"""
new_signature="""      const chestRows=treasureChestElements();
      if (chestRows.length>=3) {
        if (treasureChestBlockedByForegroundMap(chestRows)) return 'NONE';
        return treasureChestSignature();
      }
      return 'NONE';
"""
rep(old_signature,new_signature,"guard chest signature")

# Defensive branch: if the screen changes between signature collection and
# foreground ownership, never report the stale chest room as foreground.
old_foreground="""      } else if (signature.startsWith('CHESTS|')) {
        elements=treasureChestElements().map(row=>row.element);
      } else if (signature.startsWith('FISHING|')) {
"""
new_foreground="""      } else if (signature.startsWith('CHESTS|')) {
        const chestRows=treasureChestElements();
        if (treasureChestBlockedByForegroundMap(chestRows)) return false;
        elements=chestRows.map(row=>row.element);
      } else if (signature.startsWith('FISHING|')) {
"""
rep(old_foreground,new_foreground,"guard chest foreground")

rep("      treasureAutoMapStaleRunnerRevision:HK_TREASURE_AUTO_MAP_STALE_RUNNER_REV,\n      traderWhitelistRevision:HK_TRADER_WHITELIST_REV,",
    "      treasureAutoMapStaleRunnerRevision:HK_TREASURE_AUTO_MAP_STALE_RUNNER_REV,\n      treasureChestMapGuardRevision:HK_TREASURE_CHEST_MAP_GUARD_REV,\n      traderWhitelistRevision:HK_TRADER_WHITELIST_REV,",
    "export guard revision")

for marker in [
    "// @version      1.18.45",
    "const BUILD_VERSION = '1.18.45';",
    "treasure-chest-map-foreground-guard-20260927-r1",
    "function treasureChestBlockedByForegroundMap(",
    "treasure-chest-map-false-positive-blocked",
    "chest-map-guard-pre",
    "chest-map-guard-post",
    "!row.element.closest?.('[data-lot-id^=\"mf_treasurelot_active_sl\"]')",
    "if (treasureChestBlockedByForegroundMap(chestRows)) return 'NONE';",
    "treasury-left-path-exit-recovery-20260927-r1"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("TREASURE_CHEST_MAP_FOREGROUND_GUARD_1_18_45=PASS")
