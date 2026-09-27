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

rep("// @version      1.18.52",
    "// @version      1.18.53\n// @release-note Сражения: строгий запрет выхода теперь работает даже когда окно «Покинуть локацию» перекрывает поле. Проверка боя использует сырой DOM врагов, а не только визуально видимые карточки. Пока есть хотя бы один враг с HP не больше остатка мечей, выход блокируется и окно закрывается через «Назад». Атака на мобильном выполняется полноценным pointer/touch tap вместо обычного element.click().",
    "version")
rep("const BUILD_VERSION = '1.18.52';",
    "const BUILD_VERSION = '1.18.53';",
    "build")
rep("  const HK_BATTLE_STRICT_EXIT_REV='battle-strict-exit-gate-20260927-r1';",
    "  const HK_BATTLE_STRICT_EXIT_REV='battle-strict-exit-gate-20260927-r1';\n  const HK_BATTLE_RAW_CONTEXT_REV='battle-raw-context-mobile-tap-20260927-r1';",
    "revision")

rep("      const enemies=board.filter(enemy=>enemy && visible(enemy.element));",
    "      // Do not use visual visibility here. A leave-confirm modal covers the\n      // battle grid, so visible(enemy.element) becomes false exactly when the\n      // exit guard is most important. Raw enemy DOM is the authoritative room\n      // state until the battle actually mutates/removes those lots.\n      const enemies=board.filter(enemy=>enemy!==null);",
    "battle exit raw enemy context")

rep("""        const back=battleLeaveBackButton(modal);
        recordDiagnostic('battle-leave-modal-blocked',{""",
    """        const back=battleLeaveBackButton(modal) || autoMapModalCloseButton(modal);
        recordDiagnostic('battle-leave-modal-blocked',{""",
    "battle leave modal close fallback")

rep("""        // First tap only opens the enemy card in the mobile UI.
        element.click();
        recordDiagnostic('battle-auto-open-card',{revision:HK_BATTLE_MODAL_CONFIRM_REV,slot,expectedCost});

        // The actual attack is a second tap on the cost/action button in the modal.
        const actionButton=await waitBattleActionButton(expectedCost,runId);
        if (!actionButton) {
          recordDiagnostic('battle-auto-stop',{revision:HK_BATTLE_MODAL_CONFIRM_REV,reason:'attack-button-missing',slot,expectedCost});
          return false;
        }
        actionButton.click();
        recordDiagnostic('battle-auto-confirm-attack',{revision:HK_BATTLE_MODAL_CONFIRM_REV,slot,expectedCost});
""",
    """        // Mobile Safari/game handlers are not guaranteed to react to a raw
        // HTMLElement.click(). Use the same complete pointer/touch sequence that
        // already works for other Treasure Map actions.
        if (!dispatchBattleTap(element,'battle-open-card')) {
          recordDiagnostic('battle-auto-stop',{
            revision:HK_BATTLE_RAW_CONTEXT_REV,
            reason:'target-tap-failed',
            slot,
            expectedCost
          });
          return false;
        }
        recordDiagnostic('battle-auto-open-card',{
          revision:HK_BATTLE_RAW_CONTEXT_REV,
          slot,
          expectedCost
        });

        // The actual attack is a second mobile tap on the cost/action button.
        const actionButton=await waitBattleActionButton(expectedCost,runId);
        if (!actionButton) {
          recordDiagnostic('battle-auto-stop',{
            revision:HK_BATTLE_RAW_CONTEXT_REV,
            reason:'attack-button-missing',
            slot,
            expectedCost
          });
          return false;
        }
        if (!dispatchBattleTap(actionButton,'battle-confirm-attack')) {
          recordDiagnostic('battle-auto-stop',{
            revision:HK_BATTLE_RAW_CONTEXT_REV,
            reason:'attack-confirm-tap-failed',
            slot,
            expectedCost
          });
          return false;
        }
        recordDiagnostic('battle-auto-confirm-attack',{
          revision:HK_BATTLE_RAW_CONTEXT_REV,
          slot,
          expectedCost
        });
""",
    "mobile battle tap sequence")

rep("      battleStrictExitRevision:HK_BATTLE_STRICT_EXIT_REV,\n      traderWhitelistRevision:HK_TRADER_WHITELIST_REV,",
    "      battleStrictExitRevision:HK_BATTLE_STRICT_EXIT_REV,\n      battleRawContextRevision:HK_BATTLE_RAW_CONTEXT_REV,\n      traderWhitelistRevision:HK_TRADER_WHITELIST_REV,",
    "export raw battle context revision")

for marker in [
    "// @version      1.18.53",
    "const BUILD_VERSION = '1.18.53';",
    "battle-raw-context-mobile-tap-20260927-r1",
    "const enemies=board.filter(enemy=>enemy!==null);",
    "battleLeaveBackButton(modal) || autoMapModalCloseButton(modal)",
    "dispatchBattleTap(element,'battle-open-card')",
    "dispatchBattleTap(actionButton,'battle-confirm-attack')",
    "battle-strict-exit-gate-20260927-r1",
    "treasure-chest-fast-pacing-20260927-r1"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("TREASURE_BATTLE_RAW_CONTEXT_MOBILE_TAP_1_18_53=PASS")
