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
    "// @version      1.18.11",
    "// @version      1.18.12\n"
    "// @release-note Сражение: реальный бой теперь определяется сразу по видимому мечу и видимой сетке врагов. Закрытые костями карточки больше не считаются признаком превью, поэтому подсказка и автобой запускаются с первого хода после входа в бой.",
    "version"
)
rep("const BUILD_VERSION = '1.18.11';","const BUILD_VERSION = '1.18.12';","build")

rep(
    "  const HK_MINIGAME_ENTRY_GATE_REV = 'minigame-entry-only-auto-20260926-r1';",
    "  const HK_MINIGAME_ENTRY_GATE_REV = 'minigame-entry-only-auto-20260926-r1';\n"
    "  const HK_BATTLE_VISIBLE_BOARD_REV = 'battle-visible-board-active-20260926-r1';",
    "battle visible marker"
)

old="""      const sword = battleSwordElement();
      const enemies = [...document.querySelectorAll('[data-lot-id*="mf_treasurelot_enemy_type_"]')].filter(visible);
      if (sword && enemies.length > 0) {
        const battleIds='|' + sword.getAttribute('data-lot-id') + '|' +
          enemies.map(element => element.getAttribute('data-lot-id')).join('|');
        if (battleNeedsEntry()) return 'BATTLE_PREVIEW' + battleIds;
        return 'BATTLE' + battleIds;
      }
"""
new="""      const sword = battleSwordElement();
      const enemies = [...document.querySelectorAll('[data-lot-id*="mf_treasurelot_enemy_type_"]')].filter(visible);
      if (sword && enemies.length > 0) {
        const battleIds='|' + sword.getAttribute('data-lot-id') + '|' +
          enemies.map(element => element.getAttribute('data-lot-id')).join('|');
        // Once the user has entered the battle, unopened/covered enemy cards are
        // still part of the real board. Their visual "bones" state must never
        // downgrade the screen back to preview.
        return 'BATTLE' + battleIds;
      }

      // Preview/entry card may exist in DOM before the real enemy grid is visible.
      // Keep automation idle there, while preserving the user's ON setting.
      const previewSword=[...document.querySelectorAll('[data-lot-id^="mf_treasurelot_sword_"]')].find(visible);
      if (previewSword) {
        return 'BATTLE_PREVIEW|' + (previewSword.getAttribute('data-lot-id') || 'sword');
      }
"""
rep(old,new,"battle visible board signature")

# Update preview diagnostic so it is clear why automation is waiting.
rep(
    """        recordDiagnostic('battle-auto-wait-entry',{
          revision:HK_MINIGAME_ENTRY_GATE_REV,
          autoEnabled:battleAutoEnabled()
        });""",
    """        recordDiagnostic('battle-auto-wait-entry',{
          revision:HK_BATTLE_VISIBLE_BOARD_REV,
          reason:'visible-enemy-grid-not-found',
          autoEnabled:battleAutoEnabled()
        });""",
    "battle preview diagnostic"
)

rep(
    """      minigameEntryGateRevision:HK_MINIGAME_ENTRY_GATE_REV,
      start,""",
    """      minigameEntryGateRevision:HK_MINIGAME_ENTRY_GATE_REV,
      battleVisibleBoardRevision:HK_BATTLE_VISIBLE_BOARD_REV,
      start,""",
    "export battle visible revision"
)

for marker in [
    "// @version      1.18.12",
    "const BUILD_VERSION = '1.18.12';",
    "battle-visible-board-active-20260926-r1",
    "return 'BATTLE' + battleIds;",
    "visible-enemy-grid-not-found",
    "minigame-entry-only-auto-20260926-r1",
    "trader-fishing-stability-20260926-r1",
    "rumors-shared-results-20260926-r2",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

target.write_text(s,encoding="utf-8")
print("BATTLE_VISIBLE_BOARD_GATE_1_18_12=PASS")
