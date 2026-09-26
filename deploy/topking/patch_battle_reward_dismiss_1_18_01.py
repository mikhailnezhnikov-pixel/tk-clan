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
    "// @version      1.18.00",
    "// @version      1.18.01\n"
    "// @release-note Сражение: автобой теперь закрывает промежуточное окно награды «Понятно» после убийства врага и только затем пересчитывает поле и продолжает следующий удар.",
    "version"
)
rep("const BUILD_VERSION = '1.18.00';","const BUILD_VERSION = '1.18.01';","build")

rep(
    "  const HK_BATTLE_MODAL_CONFIRM_REV = 'battle-modal-confirm-20260926-r1';",
    "  const HK_BATTLE_MODAL_CONFIRM_REV = 'battle-modal-confirm-20260926-r1';\n"
    "  const HK_BATTLE_REWARD_DISMISS_REV = 'battle-reward-dismiss-20260926-r1';",
    "reward dismiss marker"
)

anchor="""    function waitBattleActionButton(expectedCost,runId,timeoutMs=2500) {
      return new Promise(resolve=>{
        const started=Date.now();
        const poll=()=>{
          if (runId!==battleAutoRunId || !battleAutoEnabled()) { resolve(null); return; }
          const button=battleActionButton(expectedCost);
          if (button) { resolve(button); return; }
          if (Date.now()-started>=timeoutMs) { resolve(null); return; }
          setTimeout(poll,80);
        };
        setTimeout(poll,80);
      });
    }

"""
insert="""    function battleRewardDismissButton() {
      const exact=/^(?:понятно|ok|okay|got it|understood)$/i;
      const candidates=[...document.querySelectorAll('button,[role="button"],a')]
        .filter(element=>element && element!==battleAutoToggle && !element.disabled && visible(element))
        .map(element=>({element,text:clean(element.innerText||element.textContent||'')}))
        .filter(row=>exact.test(row.text));
      return candidates[0]?.element || null;
    }

    function waitBattleRewardDismissButton(runId,timeoutMs=2200) {
      return new Promise(resolve=>{
        const started=Date.now();
        const poll=()=>{
          if (runId!==battleAutoRunId || !battleAutoEnabled()) { resolve(null); return; }
          const button=battleRewardDismissButton();
          if (button) { resolve(button); return; }
          if (Date.now()-started>=timeoutMs) { resolve(null); return; }
          setTimeout(poll,90);
        };
        setTimeout(poll,90);
      });
    }

    async function dismissBattleRewardIfPresent(runId) {
      const button=await waitBattleRewardDismissButton(runId);
      if (!button) return false;
      button.click();
      recordDiagnostic('battle-auto-dismiss-reward',{revision:HK_BATTLE_REWARD_DISMISS_REV});
      await new Promise(resolve=>setTimeout(resolve,220));
      return true;
    }

"""
need(anchor,"reward helper anchor")
s=s.replace(anchor,anchor+insert,1)

old="""        const changed=await waitBattleSignatureChange(before,runId);
        if (!changed) {
          recordDiagnostic('battle-auto-stop',{revision:HK_BATTLE_MODAL_CONFIRM_REV,reason:'field-no-change-after-confirm',slot,expectedCost});
          return false;
        }

        await new Promise(resolve=>setTimeout(resolve,BATTLE_AUTO_SETTLE_MS));
        recordDiagnostic('battle-auto-step-complete',{revision:HK_BATTLE_MODAL_CONFIRM_REV,slot,expectedCost});

        // Deliberately execute one hit only. The board is recalculated from the
"""
new="""        const changed=await waitBattleSignatureChange(before,runId);
        if (!changed) {
          recordDiagnostic('battle-auto-stop',{revision:HK_BATTLE_MODAL_CONFIRM_REV,reason:'field-no-change-after-confirm',slot,expectedCost});
          return false;
        }

        await new Promise(resolve=>setTimeout(resolve,BATTLE_AUTO_SETTLE_MS));
        await dismissBattleRewardIfPresent(runId);
        recordDiagnostic('battle-auto-step-complete',{revision:HK_BATTLE_REWARD_DISMISS_REV,slot,expectedCost});

        // Deliberately execute one hit only. The board is recalculated from the
"""
rep(old,new,"dismiss reward after real hit")

for marker in [
    "// @version      1.18.01",
    "const BUILD_VERSION = '1.18.01';",
    "battle-reward-dismiss-20260926-r1",
    "battle-auto-dismiss-reward",
    "dismissBattleRewardIfPresent",
    "Понятно",
    "battle-modal-confirm-20260926-r1",
    "battle-auto-click-toggle-20260926-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

target.write_text(s,encoding="utf-8")
print("BATTLE_REWARD_DISMISS_1_18_01=PASS")
