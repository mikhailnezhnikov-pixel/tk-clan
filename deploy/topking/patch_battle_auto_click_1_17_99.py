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
    "// @version      1.17.98",
    "// @version      1.17.99\n"
    "// @release-note Сражение: в общем HK-скрипте добавлен отдельный переключатель «Автобой». По умолчанию выключен. При включении скрипт кликает врагов по рассчитанным цифрам по одному, ждёт обновления поля после каждого удара и останавливается при рассинхронизации. Публичный скрипт Сокровищ не изменён.",
    "version"
)
rep("const BUILD_VERSION = '1.17.98';","const BUILD_VERSION = '1.17.99';","build")

rep(
    "  // HK Puzzle Solver v3 embedded from the user's standalone userscript.\n"
    "  // It is intentionally DOM-only: no Game API calls and no automatic clicks.\n"
    "  // The background loop preserves the standalone cadence (300 ms initial scan,\n"
    "  // then every 500 ms) and only draws numbered, pointer-events:none overlays.\n"
    "  const HK_PUZZLE_SOLVER_REV = 'puzzle-solver-v3-embedded-20260921-r1';\n"
    "  const HK_BATTLE_ENEMY_TYPE04_REV = 'battle-enemy-type04-20260926-r1';",
    "  // HK Puzzle Solver v3 embedded only in the common HK userscript.\n"
    "  // It remains DOM-only. Number hints are always passive; optional battle\n"
    "  // auto-click is local, default-off, and is NOT published to the standalone\n"
    "  // public Treasure script/site.\n"
    "  const HK_PUZZLE_SOLVER_REV = 'puzzle-solver-v3-embedded-20260921-r1';\n"
    "  const HK_BATTLE_ENEMY_TYPE04_REV = 'battle-enemy-type04-20260926-r1';\n"
    "  const HK_BATTLE_AUTO_CLICK_REV = 'battle-auto-click-toggle-20260926-r1';",
    "solver header"
)

rep(
    "    const GREEN = '03';\n\n"
    "    let lastSignature = '';\n"
    "    let intervalId = null;\n"
    "    let initialTimerId = null;",
    "    const GREEN = '03';\n"
    "    const BATTLE_AUTO_STORAGE_KEY = 'hk:battle:auto-click:v1';\n"
    "    const BATTLE_AUTO_SETTLE_MS = 260;\n"
    "    const BATTLE_AUTO_CHANGE_TIMEOUT_MS = 4500;\n\n"
    "    let lastSignature = '';\n"
    "    let intervalId = null;\n"
    "    let initialTimerId = null;\n"
    "    let battleAutoRunning = false;\n"
    "    let battleAutoRunId = 0;\n"
    "    let battleAutoToggle = null;",
    "auto state"
)

anchor="""    function clearNumbers() {
      [...document.querySelectorAll('.hkSolverNumber')].forEach(element => element.remove());
    }

"""
insert="""    function battleAutoEnabled() {
      try { return localStorage.getItem(BATTLE_AUTO_STORAGE_KEY) === '1'; }
      catch (_) { return false; }
    }

    function setBattleAutoEnabled(enabled) {
      const value=!!enabled;
      try { localStorage.setItem(BATTLE_AUTO_STORAGE_KEY,value?'1':'0'); } catch (_) {}
      if (!value) {
        battleAutoRunId += 1;
        battleAutoRunning = false;
      }
      updateBattleAutoToggle();
      recordDiagnostic('battle-auto-toggle',{revision:HK_BATTLE_AUTO_CLICK_REV,enabled:value});
      if (value) {
        lastSignature='';
        setTimeout(checkPuzzle,0);
      }
      return value;
    }

    function updateBattleAutoToggle(isBattle = null) {
      if (!battleAutoToggle) return;
      const enabled=battleAutoEnabled();
      battleAutoToggle.textContent=enabled ? either('Автобой: ВКЛ','Auto battle: ON') : either('Автобой: ВЫКЛ','Auto battle: OFF');
      battleAutoToggle.style.background=enabled ? '#40c85a' : '#2b2b2b';
      battleAutoToggle.style.color=enabled ? '#071b0a' : '#fff';
      if (isBattle !== null) battleAutoToggle.style.display=isBattle ? 'block' : 'none';
    }

    function ensureBattleAutoToggle(isBattle) {
      if (!battleAutoToggle) {
        battleAutoToggle=document.createElement('button');
        battleAutoToggle.id='hkBattleAutoToggle';
        battleAutoToggle.type='button';
        Object.assign(battleAutoToggle.style,{
          position:'fixed',
          right:'14px',
          bottom:'154px',
          zIndex:'2147483646',
          border:'2px solid rgba(255,255,255,.75)',
          borderRadius:'18px',
          padding:'8px 11px',
          fontSize:'12px',
          fontWeight:'900',
          lineHeight:'1',
          boxShadow:'0 4px 14px rgba(0,0,0,.55)',
          WebkitTapHighlightColor:'transparent',
          touchAction:'manipulation'
        });
        battleAutoToggle.addEventListener('click',event=>{
          event.preventDefault();
          event.stopPropagation();
          setBattleAutoEnabled(!battleAutoEnabled());
        },true);
        (document.body || document.documentElement)?.appendChild(battleAutoToggle);
      }
      updateBattleAutoToggle(!!isBattle);
    }

    function battleElementForSlot(slot) {
      const elements=[...document.querySelectorAll('[data-lot-id*="mf_treasurelot_enemy_type_"]')];
      return elements.find(element=>{
        const id=element.getAttribute('data-lot-id')||'';
        const match=id.match(/enemy_type_(01|02|03|04)_(\d+)_sl(\d+)/);
        return !!match && Number(match[3])===Number(slot);
      }) || null;
    }

    function waitBattleSignatureChange(before,runId) {
      return new Promise(resolve=>{
        const started=Date.now();
        const poll=()=>{
          if (runId!==battleAutoRunId || !battleAutoEnabled()) { resolve(false); return; }
          const current=getSignature();
          if (current!==before) { resolve(true); return; }
          if (Date.now()-started>=BATTLE_AUTO_CHANGE_TIMEOUT_MS) { resolve(false); return; }
          setTimeout(poll,90);
        };
        setTimeout(poll,90);
      });
    }

    async function runBattleAuto(solution) {
      if (!battleAutoEnabled() || battleAutoRunning || !solution?.order?.length) return false;
      battleAutoRunning=true;
      const runId=++battleAutoRunId;
      recordDiagnostic('battle-auto-start',{
        revision:HK_BATTLE_AUTO_CLICK_REV,
        steps:solution.order.length,
        order:solution.order.map(position=>position+BATTLE_FIRST_SLOT)
      });
      try {
        for (let index=0;index<solution.order.length;index++) {
          if (runId!==battleAutoRunId || !battleAutoEnabled()) return false;
          const slot=solution.order[index]+BATTLE_FIRST_SLOT;
          const element=battleElementForSlot(slot);
          if (!element) {
            recordDiagnostic('battle-auto-stop',{revision:HK_BATTLE_AUTO_CLICK_REV,reason:'target-missing',slot,index});
            return false;
          }
          const before=getSignature();
          element.click();
          recordDiagnostic('battle-auto-click',{revision:HK_BATTLE_AUTO_CLICK_REV,slot,index:index+1});
          const changed=await waitBattleSignatureChange(before,runId);
          if (!changed) {
            recordDiagnostic('battle-auto-stop',{revision:HK_BATTLE_AUTO_CLICK_REV,reason:'field-no-change',slot,index});
            return false;
          }
          await new Promise(resolve=>setTimeout(resolve,BATTLE_AUTO_SETTLE_MS));
        }
        recordDiagnostic('battle-auto-complete',{revision:HK_BATTLE_AUTO_CLICK_REV,steps:solution.order.length});
        return true;
      } finally {
        if (runId===battleAutoRunId) battleAutoRunning=false;
        lastSignature='';
        setTimeout(checkPuzzle,300);
      }
    }

"""
need(anchor,"clearNumbers anchor")
s=s.replace(anchor,anchor+insert,1)

rep(
    "      console.log('HK BATTLE нажать слоты:',solution.order.map(pos => pos + BATTLE_FIRST_SLOT));\n"
    "      return true;",
    "      console.log('HK BATTLE нажать слоты:',solution.order.map(pos => pos + BATTLE_FIRST_SLOT));\n"
    "      if (battleAutoEnabled() && !battleAutoRunning) void runBattleAuto(solution);\n"
    "      return true;",
    "runBattle auto start"
)

rep(
    """    function checkPuzzle() {
      const signature = getSignature();
      if (signature === lastSignature) return;
      lastSignature = signature;
      clearNumbers();
      if (signature.startsWith('LIGHTS|')) { runLights(); return; }
      if (signature.startsWith('BATTLE|')) runBattle();
    }""",
    """    function checkPuzzle() {
      const signature = getSignature();
      const isBattle=signature.startsWith('BATTLE|');
      ensureBattleAutoToggle(isBattle);
      if (battleAutoRunning) return;
      if (signature === lastSignature) return;
      lastSignature = signature;
      clearNumbers();
      if (signature.startsWith('LIGHTS|')) { runLights(); return; }
      if (isBattle) runBattle();
    }""",
    "checkPuzzle toggle"
)

rep(
    """    function stop() {
      if (initialTimerId !== null) clearTimeout(initialTimerId);
      if (intervalId !== null) clearInterval(intervalId);
      initialTimerId = null;
      intervalId = null;
      lastSignature = '';
      clearNumbers();
      recordDiagnostic('puzzle-solver-stop',{revision:HK_PUZZLE_SOLVER_REV});
    }

    return {revision:HK_PUZZLE_SOLVER_REV,start,stop,check:checkPuzzle,get running(){return intervalId !== null;}};
""",
    """    function stop() {
      if (initialTimerId !== null) clearTimeout(initialTimerId);
      if (intervalId !== null) clearInterval(intervalId);
      initialTimerId = null;
      intervalId = null;
      lastSignature = '';
      battleAutoRunId += 1;
      battleAutoRunning = false;
      clearNumbers();
      try { battleAutoToggle?.remove(); } catch (_) {}
      battleAutoToggle = null;
      recordDiagnostic('puzzle-solver-stop',{revision:HK_PUZZLE_SOLVER_REV});
    }

    return {
      revision:HK_PUZZLE_SOLVER_REV,
      battleAutoRevision:HK_BATTLE_AUTO_CLICK_REV,
      start,
      stop,
      check:checkPuzzle,
      get autoBattleEnabled(){return battleAutoEnabled();},
      setAutoBattleEnabled:setBattleAutoEnabled,
      get running(){return intervalId !== null;}
    };
""",
    "solver return"
)

for marker in [
    "// @version      1.17.99",
    "const BUILD_VERSION = '1.17.99';",
    "battle-auto-click-toggle-20260926-r1",
    "Автобой: ВКЛ",
    "BATTLE_AUTO_STORAGE_KEY",
    "waitBattleSignatureChange",
    "element.click();",
    "if (battleAutoEnabled() && !battleAutoRunning) void runBattleAuto(solution);",
    "enemy_type_(01|02|03|04)",
    "late-login-recovery-20260926-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

target.write_text(s,encoding="utf-8")
print("BATTLE_AUTO_CLICK_1_17_99=PASS")
