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
    "// @version      1.18.10",
    "// @version      1.18.11\n"
    "// @release-note Мини-игры: все авто-режимы теперь запускаются только после фактического входа внутрь мини-игры. На внешней карте/превью скрипт не кликает входные ячейки и не атакует скрытый DOM. Настройка ВКЛ сохраняется и автоматически начинает работу после появления реального игрового поля.",
    "version"
)
rep("const BUILD_VERSION = '1.18.10';","const BUILD_VERSION = '1.18.11';","build")

rep(
    "  const HK_TRADER_FISHING_STABILITY_REV = 'trader-fishing-stability-20260926-r1';",
    "  const HK_TRADER_FISHING_STABILITY_REV = 'trader-fishing-stability-20260926-r1';\n"
    "  const HK_MINIGAME_ENTRY_GATE_REV = 'minigame-entry-only-auto-20260926-r1';",
    "entry gate marker"
)

# Lights must only be detected from the actually visible board.
rep(
    """      const lights = [...document.querySelectorAll('[data-lot-id^="mf_fairlot_lights_out_sl"]')];
      if (lights.length === 9) return 'LIGHTS|' + lights.map(element => element.getAttribute('data-lot-id')).join('|');
""",
    """      const lights = [...document.querySelectorAll('[data-lot-id^="mf_fairlot_lights_out_sl"]')].filter(visible);
      if (lights.length === 9) return 'LIGHTS|' + lights.map(element => element.getAttribute('data-lot-id')).join('|');
""",
    "visible lights only"
)

# Battle DOM exists before the user enters. Classify that as preview, never as an active battle.
rep(
    """      const sword = document.querySelector('[data-lot-id^="mf_treasurelot_sword_"]');
      const enemies = [...document.querySelectorAll('[data-lot-id*="mf_treasurelot_enemy_type_"]')];
      if (sword && enemies.length > 0) {
        return 'BATTLE|' + sword.getAttribute('data-lot-id') + '|' +
          enemies.map(element => element.getAttribute('data-lot-id')).join('|');
      }
""",
    """      const sword = battleSwordElement();
      const enemies = [...document.querySelectorAll('[data-lot-id*="mf_treasurelot_enemy_type_"]')].filter(visible);
      if (sword && enemies.length > 0) {
        const battleIds='|' + sword.getAttribute('data-lot-id') + '|' +
          enemies.map(element => element.getAttribute('data-lot-id')).join('|');
        if (battleNeedsEntry()) return 'BATTLE_PREVIEW' + battleIds;
        return 'BATTLE' + battleIds;
      }
""",
    "battle preview signature"
)

# Never expose/run autobattle on preview. Existing ON setting remains stored for after entry.
rep(
    """      const isBattle=signature.startsWith('BATTLE|');
      const isBattleReward=signature.startsWith('BATTLE_REWARD');
      const isFishing=signature.startsWith('FISHING|');
      const isTrader=signature.startsWith('TRADER|');
      const isChests=signature.startsWith('CHESTS|');
      const battleContext=isBattle || isBattleReward || !!document.querySelector('[data-lot-id^="mf_treasurelot_sword_"]');
""",
    """      const isBattle=signature.startsWith('BATTLE|');
      const isBattlePreview=signature.startsWith('BATTLE_PREVIEW|');
      const isBattleReward=signature.startsWith('BATTLE_REWARD');
      const isFishing=signature.startsWith('FISHING|');
      const isTrader=signature.startsWith('TRADER|');
      const isChests=signature.startsWith('CHESTS|');
      const battleContext=isBattle || isBattleReward;
""",
    "battle context only after entry"
)

rep(
    """      if (isBattle) {
        if (battleAutoEnabled() && battleNeedsEntry()) { void runBattleEntry(); return; }
        runBattle();
        return;
      }
""",
    """      if (isBattlePreview) {
        recordDiagnostic('battle-auto-wait-entry',{
          revision:HK_MINIGAME_ENTRY_GATE_REV,
          autoEnabled:battleAutoEnabled()
        });
        return;
      }
      if (isBattle) {
        runBattle();
        return;
      }
""",
    "remove automatic battle entry"
)

# Export marker so live diagnostics can prove this behavior is active.
rep(
    """      traderAutoRevision:HK_TRADER_AUTO_REV,
      start,
""",
    """      traderAutoRevision:HK_TRADER_AUTO_REV,
      minigameEntryGateRevision:HK_MINIGAME_ENTRY_GATE_REV,
      start,
""",
    "export entry gate revision"
)

for marker in [
    "// @version      1.18.11",
    "const BUILD_VERSION = '1.18.11';",
    "minigame-entry-only-auto-20260926-r1",
    "BATTLE_PREVIEW",
    "battle-auto-wait-entry",
    "const battleContext=isBattle || isBattleReward;",
    ".filter(visible)",
    "trader-fishing-stability-20260926-r1",
    "rumors-shared-results-20260926-r2",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

target.write_text(s,encoding="utf-8")
print("MINIGAME_ENTRY_GATE_1_18_11=PASS")
