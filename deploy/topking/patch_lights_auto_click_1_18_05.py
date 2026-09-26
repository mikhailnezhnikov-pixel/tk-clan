# build-trigger: 1.18.05 lights auto-click
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
    "// @version      1.18.04",
    "// @version      1.18.05\n"
    "// @release-note Лампочки: в общем HK-скрипте добавлен отдельный безопасный автоклик. После каждого нажатия скрипт ждёт фактического изменения 3×3 поля, заново считывает состояние, пересчитывает решение и только затем нажимает следующую лампу. При отсутствии изменения, потере цели, невалидном поле или цикле автоматизация отключается вместо повторных кликов. Цифры подсказки сохраняются.",
    "version"
)
rep("const BUILD_VERSION = '1.18.04';","const BUILD_VERSION = '1.18.05';","build")

rep(
    "  const HK_BATTLE_VICTORY_TAP_REV = 'battle-victory-tap-fallback-20260926-r1';\n"
    "  const HK_CHEST_AUTO_REV = 'chest-auto-dig-open-20260926-r1';",
    "  const HK_BATTLE_VICTORY_TAP_REV = 'battle-victory-tap-fallback-20260926-r1';\n"
    "  const HK_CHEST_AUTO_REV = 'chest-auto-dig-open-20260926-r1';\n"
    "  const HK_LIGHTS_AUTO_REV = 'lights-auto-recalc-20260926-r1';",
    "lights auto marker"
)

old_state="""    const BATTLE_AUTO_STORAGE_KEY = 'hk:battle:auto-click:v1';
    const CHEST_AUTO_STORAGE_KEY = 'hk:chests:auto-open:v1';
    const BATTLE_AUTO_SETTLE_MS = 260;
    const BATTLE_AUTO_CHANGE_TIMEOUT_MS = 4500;
    const CHEST_ACTION_TIMEOUT_MS = 3600;

    let lastSignature = '';
    let intervalId = null;
    let initialTimerId = null;
    let battleAutoRunning = false;
    let battleAutoRunId = 0;
    let battleAutoToggle = null;
    let chestAutoRunning = false;
    let chestAutoRunId = 0;
    let chestAutoToggle = null;
"""
new_state="""    const BATTLE_AUTO_STORAGE_KEY = 'hk:battle:auto-click:v1';
    const CHEST_AUTO_STORAGE_KEY = 'hk:chests:auto-open:v1';
    const LIGHTS_AUTO_STORAGE_KEY = 'hk:lights:auto-click:v1';
    const BATTLE_AUTO_SETTLE_MS = 260;
    const BATTLE_AUTO_CHANGE_TIMEOUT_MS = 4500;
    const CHEST_ACTION_TIMEOUT_MS = 3600;
    const LIGHTS_AUTO_SETTLE_MS = 240;
    const LIGHTS_AUTO_CHANGE_TIMEOUT_MS = 4200;
    const LIGHTS_AUTO_MAX_STEPS = 24;

    let lastSignature = '';
    let intervalId = null;
    let initialTimerId = null;
    let battleAutoRunning = false;
    let battleAutoRunId = 0;
    let battleAutoToggle = null;
    let chestAutoRunning = false;
    let chestAutoRunId = 0;
    let chestAutoToggle = null;
    let lightsAutoRunning = false;
    let lightsAutoRunId = 0;
    let lightsAutoToggle = null;
"""
rep(old_state,new_state,"lights state")

anchor="""    function ensureChestAutoToggle(isChest) {
      if (!chestAutoToggle) {
        chestAutoToggle=document.createElement('button');
        chestAutoToggle.id='hkChestAutoToggle';
        chestAutoToggle.type='button';
        Object.assign(chestAutoToggle.style,{
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
        chestAutoToggle.addEventListener('click',event=>{
          event.preventDefault();
          event.stopPropagation();
          setChestAutoEnabled(!chestAutoEnabled());
        },true);
        (document.body || document.documentElement)?.appendChild(chestAutoToggle);
      }
      updateChestAutoToggle(!!isChest);
    }

"""
insert="""    function lightsAutoEnabled() {
      try { return localStorage.getItem(LIGHTS_AUTO_STORAGE_KEY) === '1'; }
      catch (_) { return false; }
    }

    function updateLightsAutoToggle(isLights = null) {
      if (!lightsAutoToggle) return;
      const enabled=lightsAutoEnabled();
      lightsAutoToggle.textContent=enabled ? either('Автолампы: ВКЛ','Auto lights: ON') : either('Автолампы: ВЫКЛ','Auto lights: OFF');
      lightsAutoToggle.style.background=enabled ? '#40c85a' : '#2b2b2b';
      lightsAutoToggle.style.color=enabled ? '#071b0a' : '#fff';
      if (isLights !== null) lightsAutoToggle.style.display=isLights ? 'block' : 'none';
    }

    function setLightsAutoEnabled(enabled) {
      const value=!!enabled;
      try { localStorage.setItem(LIGHTS_AUTO_STORAGE_KEY,value?'1':'0'); } catch (_) {}
      if (!value) {
        lightsAutoRunId += 1;
        lightsAutoRunning = false;
      }
      updateLightsAutoToggle();
      recordDiagnostic('lights-auto-toggle',{revision:HK_LIGHTS_AUTO_REV,enabled:value});
      if (value) {
        lastSignature='';
        setTimeout(checkPuzzle,0);
      }
      return value;
    }

    function ensureLightsAutoToggle(isLights) {
      if (!lightsAutoToggle) {
        lightsAutoToggle=document.createElement('button');
        lightsAutoToggle.id='hkLightsAutoToggle';
        lightsAutoToggle.type='button';
        Object.assign(lightsAutoToggle.style,{
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
        lightsAutoToggle.addEventListener('click',event=>{
          event.preventDefault();
          event.stopPropagation();
          setLightsAutoEnabled(!lightsAutoEnabled());
        },true);
        (document.body || document.documentElement)?.appendChild(lightsAutoToggle);
      }
      updateLightsAutoToggle(!!isLights);
    }

    function lightsBoardSignature(board = null) {
      const source=board || getLightsBoard();
      if (!Array.isArray(source) || source.length!==9 || source.some(cell=>!cell)) return 'LIGHTS_INVALID';
      return 'LIGHTS_STATE|'+source.map(cell=>String(cell.slot)+':'+(cell.on?'1':'0')).join('|');
    }

    function drawLightsSolution(board,solution) {
      clearNumbers();
      if (!Array.isArray(solution)) return;
      solution.forEach((position,index)=>{
        const cell=board?.[position];
        if (cell?.element) addNumber(cell.element,index+1);
      });
    }

    async function waitLightsBoardChange(before,runId) {
      const started=Date.now();
      while (Date.now()-started<LIGHTS_AUTO_CHANGE_TIMEOUT_MS) {
        if (runId!==lightsAutoRunId || !lightsAutoEnabled()) return false;
        const current=lightsBoardSignature();
        if (current!==before) return true;
        await new Promise(resolve=>setTimeout(resolve,90));
      }
      return false;
    }

    function failLightsAuto(reason,data={}) {
      try { localStorage.setItem(LIGHTS_AUTO_STORAGE_KEY,'0'); } catch (_) {}
      lightsAutoRunId += 1;
      lightsAutoRunning=false;
      updateLightsAutoToggle();
      recordDiagnostic('lights-auto-stop',{revision:HK_LIGHTS_AUTO_REV,reason,...data});
      return false;
    }

    async function runLightsAuto() {
      if (!lightsAutoEnabled() || lightsAutoRunning || battleAutoRunning || chestAutoRunning) return false;
      lightsAutoRunning=true;
      const runId=++lightsAutoRunId;
      const seen=new Set();
      let steps=0;
      recordDiagnostic('lights-auto-start',{revision:HK_LIGHTS_AUTO_REV});

      try {
        while (runId===lightsAutoRunId && lightsAutoEnabled()) {
          if (steps>=LIGHTS_AUTO_MAX_STEPS) {
            return failLightsAuto('step-limit',{steps});
          }

          const board=getLightsBoard();
          const valid=board.filter(cell=>cell!==null);
          if (valid.length!==9) {
            if (!getSignature().startsWith('LIGHTS|')) {
              clearNumbers();
              recordDiagnostic('lights-auto-complete',{revision:HK_LIGHTS_AUTO_REV,steps,reason:'board-closed'});
              return true;
            }
            return failLightsAuto('board-invalid',{valid:valid.length,steps});
          }

          const before=lightsBoardSignature(board);
          if (seen.has(before)) {
            return failLightsAuto('state-cycle',{state:before,steps});
          }
          seen.add(before);

          const solution=solveLights(board);
          drawLightsSolution(board,solution);

          if (solution===null) {
            return failLightsAuto('solution-missing',{state:before,steps});
          }

          if (solution.length===0) {
            recordDiagnostic('lights-auto-complete',{revision:HK_LIGHTS_AUTO_REV,steps,reason:'solved'});
            return true;
          }

          const position=solution[0];
          const target=board[position]?.element;
          if (!target || !target.isConnected) {
            return failLightsAuto('target-missing',{position,steps});
          }

          try {
            target.click();
          } catch (error) {
            return failLightsAuto('click-error',{position,steps,error:String(error?.message||error||'unknown')});
          }

          steps+=1;
          recordDiagnostic('lights-auto-click',{
            revision:HK_LIGHTS_AUTO_REV,
            step:steps,
            slot:position+1,
            remainingPlan:solution.map(pos=>pos+1)
          });

          const changed=await waitLightsBoardChange(before,runId);
          if (!changed) {
            if (runId!==lightsAutoRunId || !lightsAutoEnabled()) return false;
            return failLightsAuto('field-no-change',{position,slot:position+1,steps,state:before});
          }

          await new Promise(resolve=>setTimeout(resolve,LIGHTS_AUTO_SETTLE_MS));
        }
        return false;
      } finally {
        if (runId===lightsAutoRunId) lightsAutoRunning=false;
        lastSignature='';
        setTimeout(checkPuzzle,300);
      }
    }

"""
need(anchor,"chest toggle anchor")
s=s.replace(anchor,anchor+insert,1)

old_run="""    function runLights() {
      const board = getLightsBoard();
      if (board.filter(cell => cell !== null).length !== 9) return false;
      clearNumbers();
      const solution = solveLights(board);
      if (solution === null) { console.log('HK LIGHTS: решения не найдено'); return true; }
      if (solution.length === 0) { console.log('HK LIGHTS: все лампы уже включены'); return true; }
      solution.forEach((position,index) => addNumber(board[position].element,index+1));
      console.log('HK LIGHTS: нажать лампы:',solution.map(pos => pos+1));
      return true;
    }
"""
new_run="""    function runLights() {
      const board = getLightsBoard();
      if (board.filter(cell => cell !== null).length !== 9) return false;
      clearNumbers();
      const solution = solveLights(board);
      if (solution === null) { console.log('HK LIGHTS: решения не найдено'); return true; }
      if (solution.length === 0) { console.log('HK LIGHTS: все лампы уже включены'); return true; }
      solution.forEach((position,index) => addNumber(board[position].element,index+1));
      console.log('HK LIGHTS: нажать лампы:',solution.map(pos => pos+1));
      if (lightsAutoEnabled() && !lightsAutoRunning) void runLightsAuto();
      return true;
    }
"""
rep(old_run,new_run,"runLights auto start")

old_sig="""    function checkPuzzle() {
      const signature = getSignature();
      const isBattle=signature.startsWith('BATTLE|');
      const isBattleReward=signature.startsWith('BATTLE_REWARD');
      const isChests=signature.startsWith('CHESTS|');
      const battleContext=isBattle || isBattleReward || !!document.querySelector('[data-lot-id^="mf_treasurelot_sword_"]');
      ensureBattleAutoToggle(battleContext);
      ensureChestAutoToggle(isChests);
      if (battleAutoRunning || chestAutoRunning) return;
      if (signature === lastSignature) return;
      lastSignature = signature;
      clearNumbers();
      if (signature.startsWith('LIGHTS|')) { runLights(); return; }
      if (isBattle) { runBattle(); return; }
      if (isBattleReward && battleAutoEnabled()) { void runBattleVictoryClaim(); return; }
      if (isChests && chestAutoEnabled()) void runTreasureChestAuto();
    }"""
new_sig="""    function checkPuzzle() {
      const signature = getSignature();
      const isLights=signature.startsWith('LIGHTS|');
      const isBattle=signature.startsWith('BATTLE|');
      const isBattleReward=signature.startsWith('BATTLE_REWARD');
      const isChests=signature.startsWith('CHESTS|');
      const battleContext=isBattle || isBattleReward || !!document.querySelector('[data-lot-id^="mf_treasurelot_sword_"]');
      ensureBattleAutoToggle(battleContext);
      ensureChestAutoToggle(isChests);
      ensureLightsAutoToggle(isLights);
      if (battleAutoRunning || chestAutoRunning || lightsAutoRunning) return;
      if (signature === lastSignature) return;
      lastSignature = signature;
      clearNumbers();
      if (isLights) { runLights(); return; }
      if (isBattle) { runBattle(); return; }
      if (isBattleReward && battleAutoEnabled()) { void runBattleVictoryClaim(); return; }
      if (isChests && chestAutoEnabled()) void runTreasureChestAuto();
    }"""
rep(old_sig,new_sig,"lights signature and runner")

old_stop="""      battleAutoRunId += 1;
      battleAutoRunning = false;
      chestAutoRunId += 1;
      chestAutoRunning = false;
      clearNumbers();
      try { battleAutoToggle?.remove(); } catch (_) {}
      try { chestAutoToggle?.remove(); } catch (_) {}
      battleAutoToggle = null;
      chestAutoToggle = null;
      recordDiagnostic('puzzle-solver-stop',{revision:HK_PUZZLE_SOLVER_REV});
    }

    return {
      revision:HK_PUZZLE_SOLVER_REV,
      battleAutoRevision:HK_BATTLE_AUTO_CLICK_REV,
      chestAutoRevision:HK_CHEST_AUTO_REV,
      start,
      stop,
      check:checkPuzzle,
      get autoBattleEnabled(){return battleAutoEnabled();},
      setAutoBattleEnabled:setBattleAutoEnabled,
      get autoChestsEnabled(){return chestAutoEnabled();},
      setAutoChestsEnabled:setChestAutoEnabled,
      get running(){return intervalId !== null;}
    };
"""
new_stop="""      battleAutoRunId += 1;
      battleAutoRunning = false;
      chestAutoRunId += 1;
      chestAutoRunning = false;
      lightsAutoRunId += 1;
      lightsAutoRunning = false;
      clearNumbers();
      try { battleAutoToggle?.remove(); } catch (_) {}
      try { chestAutoToggle?.remove(); } catch (_) {}
      try { lightsAutoToggle?.remove(); } catch (_) {}
      battleAutoToggle = null;
      chestAutoToggle = null;
      lightsAutoToggle = null;
      recordDiagnostic('puzzle-solver-stop',{revision:HK_PUZZLE_SOLVER_REV});
    }

    return {
      revision:HK_PUZZLE_SOLVER_REV,
      battleAutoRevision:HK_BATTLE_AUTO_CLICK_REV,
      chestAutoRevision:HK_CHEST_AUTO_REV,
      lightsAutoRevision:HK_LIGHTS_AUTO_REV,
      start,
      stop,
      check:checkPuzzle,
      get autoBattleEnabled(){return battleAutoEnabled();},
      setAutoBattleEnabled:setBattleAutoEnabled,
      get autoChestsEnabled(){return chestAutoEnabled();},
      setAutoChestsEnabled:setChestAutoEnabled,
      get autoLightsEnabled(){return lightsAutoEnabled();},
      setAutoLightsEnabled:setLightsAutoEnabled,
      get running(){return intervalId !== null;}
    };
"""
rep(old_stop,new_stop,"solver stop and export")

for marker in [
    "// @version      1.18.05",
    "const BUILD_VERSION = '1.18.05';",
    "lights-auto-recalc-20260926-r1",
    "Автолампы: ВКЛ",
    "LIGHTS_AUTO_STORAGE_KEY",
    "waitLightsBoardChange",
    "state-cycle",
    "field-no-change",
    "if (lightsAutoEnabled() && !lightsAutoRunning) void runLightsAuto();",
    "chest-auto-dig-open-20260926-r1",
    "battle-auto-click-toggle-20260926-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

target.write_text(s,encoding="utf-8")
print("LIGHTS_AUTO_CLICK_1_18_05=PASS")
