from pathlib import Path
import re
import sys

p = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/HamsterKingMobile.user.js")
s = p.read_text(encoding="utf-8")

def rep(old, new, label, count=1):
    global s
    n = s.count(old)
    if n != count:
        raise SystemExit(f"{label}: expected {count}, got {n}")
    s = s.replace(old, new, count)

def sub(pattern, repl, label, count=1, flags=0):
    global s
    s2, n = re.subn(pattern, repl, s, count=count, flags=flags)
    if n != count:
        raise SystemExit(f"{label}: expected {count}, got {n}")
    s = s2

rep(
    "// @version      1.18.55",
    "// @version      1.18.56\n"
    "// @release-note Устройства и темп: компьютер, планшет и телефон теперь используют один и тот же сценарий действий и детерминированные паузы без случайного ускорения/замедления. Лабиринт дополнительно проверяет, что нажатие кнопки 1 действительно принято интерфейсом; если обычный DOM-click не сработал, включается единый fallback и только после подтверждённого изменения состояния выполняется следующий шаг.",
    "version",
)
rep("const BUILD_VERSION = '1.18.55';", "const BUILD_VERSION = '1.18.56';", "build")

rep(
    "  const HK_TREASURY_LOOP_REV = 'treasury-left-once-continuous-map-20260927-r1';",
    "  const HK_TREASURY_LOOP_REV = 'treasury-left-once-continuous-map-20260927-r1';\n"
    "  const HK_DEVICE_NEUTRAL_MINIGAME_REV = 'device-neutral-minigame-20260928-r1';",
    "revision",
)

anchor = "    function minigameRecentHttpError(since=0,windowMs=8000) {\n"
if s.count(anchor) != 1:
    raise SystemExit("minigameRecentHttpError anchor missing")

helper = """    async function minigameDevicePause(stage='scan',data={}) {
      // One deterministic pacing table for desktop/tablet/mobile. Do not use
      // viewport, user-agent, touch support or random jitter for normal actions.
      const waits={
        scan:350,
        aim:250,
        confirm:450,
        settle:700,
        reward:350,
        map:450
      };
      const waitMs=Number(waits[stage] ?? waits.scan);
      recordDiagnostic('minigame-device-neutral-pause',{
        revision:HK_DEVICE_NEUTRAL_MINIGAME_REV,
        stage,
        waitMs,
        ...data
      });
      await new Promise(resolve=>setTimeout(resolve,waitMs));
      return waitMs;
    }

    async function waitDeviceNeutralCondition(predicate,timeoutMs=900,pollMs=60) {
      const started=Date.now();
      while (Date.now()-started<timeoutMs) {
        try {
          if (predicate()) return true;
        } catch (_) {}
        await new Promise(resolve=>setTimeout(resolve,pollMs));
      }
      try { return !!predicate(); } catch (_) { return false; }
    }

    async function deviceNeutralActivate(element,label,accepted,timeoutMs=900) {
      if (!element || !element.isConnected) return false;

      // Native DOM activation is deliberately first on every device. It gives
      // desktop/mobile/tablet the same primary path instead of branching by UA.
      let nativeSent=false;
      try {
        if (typeof element.click==='function') {
          element.click();
          nativeSent=true;
          recordDiagnostic('device-neutral-activate',{
            revision:HK_DEVICE_NEUTRAL_MINIGAME_REV,
            label,
            mode:'native-click'
          });
        }
      } catch (_) {}

      if (nativeSent && await waitDeviceNeutralCondition(accepted,timeoutMs,60)) {
        return true;
      }

      // Only if the UI demonstrably did not accept the native activation, use
      // the existing robust pointer/touch dispatcher as the common fallback.
      if (!element.isConnected) {
        try { return !!accepted(); } catch (_) { return false; }
      }

      const fallbackSent=dispatchAutoMapTap(element,label+'-fallback');
      if (!fallbackSent) return false;

      recordDiagnostic('device-neutral-activate',{
        revision:HK_DEVICE_NEUTRAL_MINIGAME_REV,
        label,
        mode:'pointer-fallback'
      });
      return await waitDeviceNeutralCondition(accepted,timeoutMs,60);
    }

"""
s = s.replace(anchor, helper + anchor, 1)

# Preserve historical helper names/markers for regression contracts, but route
# their execution through the same deterministic pacing table on every device.
for signature,label in (
    ("    async function minigameHumanPause(stage='scan',data={}) {", "general"),
    ("    async function fishingHumanPause(stage='scan',data={}) {", "fishing"),
    ("    async function traderHumanPause(stage='scan',data={}) {", "trader"),
    ("    async function chestHumanPause(stage='scan',data={}) {", "chests"),
):
    if s.count(signature) != 1:
        raise SystemExit(f"{label} pacing helper missing")
    s = s.replace(
        signature,
        signature + "\n      return minigameDevicePause(stage,{...data,deviceNeutralModule:'" + label + "'});",
        1,
    )

# Keep module-specific safety timeouts, but normal action cadence is fixed.
sub(r"const BATTLE_AUTO_SETTLE_MS = \d+;", "const BATTLE_AUTO_SETTLE_MS = 700;", "battle settle")
sub(r"const LIGHTS_AUTO_SETTLE_MS = \d+;", "const LIGHTS_AUTO_SETTLE_MS = 700;", "lights settle")
sub(r"const FISHING_MIN_NEXT_ACTION_GAP_MS = \d+;", "const FISHING_MIN_NEXT_ACTION_GAP_MS = 1200;", "fishing gap")
sub(r"const TRADER_MIN_NEXT_ACTION_GAP_MS = \d+;", "const TRADER_MIN_NEXT_ACTION_GAP_MS = 1200;", "trader gap")
sub(r"const AUTO_MAP_ACTION_GAP_MS=\d+;", "const AUTO_MAP_ACTION_GAP_MS=1200;", "auto map gap")

# Replace the complete lamp step. The important behavioral change is that a
# dispatched event is no longer considered success by itself: desktop/mobile
# both wait for a real UI/state transition before advancing.
start = s.find("    async function runLightsModalStep(before,target,slot,runId) {")
end = s.find("\n    function lightsRewardElement()", start)
if start < 0 or end < 0:
    raise SystemExit("runLightsModalStep block not found")

new_step = """    async function runLightsModalStep(before,target,slot,runId) {
      if (!target || !target.isConnected) return {ok:false,reason:'target-missing'};

      // Never inherit the previous lamp's dialog as a new purchase. Drain it,
      // then open the current target from a clean board state.
      if (lightsModalRoot()) {
        const cleared=await clearStaleLightsModalBeforeStep(runId,slot);
        if (!cleared) return {ok:false,reason:'stale-modal-blocking'};
      }

      if (runId!==lightsAutoRunId || !lightsAutoEnabled()) {
        return {ok:false,reason:'cancelled'};
      }

      const opened=await deviceNeutralActivate(
        target,
        'lights-open-'+slot,
        ()=>!!lightsModalRoot(),
        900
      );
      if (!opened) return {ok:false,reason:'target-tap-failed'};

      const purchaseModal=lightsModalRoot() || await waitLightsModal(runId);
      if (!purchaseModal) return {ok:false,reason:'purchase-modal-missing'};

      const purchaseButton=await waitLightsPurchaseButton(purchaseModal,runId);
      if (!purchaseButton) return {ok:false,reason:'purchase-button-missing'};

      const clickTarget=lightsPurchaseClickTarget(purchaseButton,purchaseModal) || purchaseButton;
      const accepted=()=> {
        if (lightsBoardSignature()!==before) return true;
        const current=lightsModalRoot();
        if (!current) return true;
        if (lightsAcknowledgeButton(current)) return true;
        const currentPurchase=lightsPurchaseButton(current);
        return !currentPurchase;
      };

      const confirmed=await deviceNeutralActivate(
        clickTarget,
        'lights-confirm-cost-'+slot,
        accepted,
        1100
      );
      if (!confirmed) return {ok:false,reason:'purchase-tap-failed'};

      recordDiagnostic('lights-purchase-confirmed-device-neutral',{
        revision:HK_DEVICE_NEUTRAL_MINIGAME_REV,
        slot,
        stateBefore:before
      });

      // Server/render speed may differ, but the algorithm does not. Advance
      // only after the board has actually changed.
      let changed=lightsBoardSignature()!==before;
      if (!changed) {
        changed=await waitLightsBoardChange(before,runId,3200);
      }
      if (!changed) return {ok:false,reason:'field-no-change'};

      if (lightsModalRoot()) {
        const drained=await closeLightsModalAfterStateChange(runId,before,slot,1800);
        if (!drained) return {ok:false,reason:'modal-not-closed-after-change'};
      }

      recordDiagnostic('lights-auto-step-ui-complete',{
        revision:HK_DEVICE_NEUTRAL_MINIGAME_REV,
        slot,
        state:lightsBoardSignature(),
        deviceNeutral:true
      });
      return {ok:true,reason:'field-changed-modal-closed-device-neutral'};
    }
"""
s = s[:start] + new_step + s[end:]

rep(
    "      treasuryLoopRevision:HK_TREASURY_LOOP_REV,\n      start,",
    "      treasuryLoopRevision:HK_TREASURY_LOOP_REV,\n"
    "      deviceNeutralMinigameRevision:HK_DEVICE_NEUTRAL_MINIGAME_REV,\n"
    "      start,",
    "export revision",
)

for marker in [
    "// @version      1.18.56",
    "const BUILD_VERSION = '1.18.56';",
    "device-neutral-minigame-20260928-r1",
    "async function minigameDevicePause",
    "async function deviceNeutralActivate",
    "lights-purchase-confirmed-device-neutral",
    "field-changed-modal-closed-device-neutral",
    "BATTLE_AUTO_SETTLE_MS = 700",
    "LIGHTS_AUTO_SETTLE_MS = 700",
    "FISHING_MIN_NEXT_ACTION_GAP_MS = 1200",
    "TRADER_MIN_NEXT_ACTION_GAP_MS = 1200",
    "AUTO_MAP_ACTION_GAP_MS=1200",
    "treasure-lights-outer-modal-20260927-r1",
    "treasure-lights-resume-open-modal-20260927-r1",
    "treasure-chest-fast-pacing-20260927-r1",
    "battle-raw-context-mobile-tap-20260927-r1",
    "treasury-left-once-continuous-map-20260927-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

p.write_text(s, encoding="utf-8")
print("DEVICE_NEUTRAL_MINIGAME_1_18_56=PASS")
