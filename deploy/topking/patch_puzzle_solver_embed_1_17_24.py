from pathlib import Path

PATH = Path("/tmp/HamsterKingMobile.user.js")
s = PATH.read_text(encoding="utf-8")

def require(marker, label=None):
    if marker not in s:
        raise SystemExit("missing expected marker: " + (label or marker[:180]))

def replace_once(old, new, label):
    global s
    count=s.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 match, got {count}")
    s=s.replace(old,new,1)

for marker in [
    "// @version      1.17.24",
    "const BUILD_VERSION = '1.17.24';",
    "const HK_CORE_REVISION = 'core-20260921-r27-businesses-runner-canon';",
    "businesses-finalize-single-snapshot-20260921-r1",
    "runtime.destroy = () => {",
    "startNetworkCapture();",
    "startAfterNativeGameLogin();",
]:
    require(marker)

release = "// @release-note Перестановка бизнесов: на desktop «достать» слева, «вставить» справа; T4–T6 полностью защищены от снятия."
replace_once(
    release,
    "// @release-note Встроен фоновый HK Puzzle Solver v3: автоматически показывает порядок нажатий для Lights Out 3×3 и Battle.\n" + release,
    "release note"
)

anchor = """  runtime.destroy = () => {
    runtime.active = false;
    try { root?.remove(); } catch (_) {}
    try { bootstrapButton?.remove(); } catch (_) {}
    root = null;
    panel = null;
  };

  // PRELOGIN_ZERO_GAME_API_R1: install only passive interception before login."""

module = r"""  // HK Puzzle Solver v3 embedded from the user's standalone userscript.
  // It is intentionally DOM-only: no Game API calls and no automatic clicks.
  // The background loop preserves the standalone cadence (300 ms initial scan,
  // then every 500 ms) and only draws numbered, pointer-events:none overlays.
  const HK_PUZZLE_SOLVER_REV = 'puzzle-solver-v3-embedded-20260921-r1';
  const hkPuzzleSolver = (() => {
    const BATTLE_FIRST_SLOT = 7;
    const BATTLE_SIZE = 12;
    const BATTLE_COLS = 3;
    const BATTLE_ROWS = 4;
    const RED = '01';
    const BLUE = '02';
    const GREEN = '03';

    let lastSignature = '';
    let intervalId = null;
    let initialTimerId = null;

    function clearNumbers() {
      [...document.querySelectorAll('.hkSolverNumber')].forEach(element => element.remove());
    }

    function addNumber(element, number) {
      if (!element) return;
      const style = window.getComputedStyle(element);
      if (style.position === 'static') element.style.position = 'relative';

      const badge = document.createElement('div');
      badge.className = 'hkSolverNumber';
      badge.textContent = String(number);
      Object.assign(badge.style, {
        position:'absolute',
        top:'6px',
        right:'6px',
        width:'38px',
        height:'38px',
        borderRadius:'50%',
        background:number === 1 ? '#62ff75' : '#ffd740',
        color:'#000',
        border:'3px solid #fff',
        boxSizing:'border-box',
        fontSize:'22px',
        fontWeight:'900',
        lineHeight:'32px',
        textAlign:'center',
        zIndex:'9999999',
        boxShadow:'0 2px 8px rgba(0,0,0,.9)',
        pointerEvents:'none',
        userSelect:'none'
      });
      element.appendChild(badge);
    }

    function getLightsBoard() {
      const board = new Array(9).fill(null);
      const elements = [...document.querySelectorAll('[data-lot-id^="mf_fairlot_lights_out_sl"]')];
      elements.forEach(element => {
        const id = element.getAttribute('data-lot-id') || '';
        const match = id.match(/mf_fairlot_lights_out_sl(d+)_(true|false)/);
        if (!match) return;
        const slot = Number(match[1]);
        const isOn = match[2] === 'true';
        if (slot < 1 || slot > 9) return;
        board[slot - 1] = {slot,on:isOn,element};
      });
      return board;
    }

    function lightNeighbours(position) {
      const result = [position];
      const row = Math.floor(position / 3);
      const col = position % 3;
      if (row > 0) result.push(position - 3);
      if (row < 2) result.push(position + 3);
      if (col > 0) result.push(position - 1);
      if (col < 2) result.push(position + 1);
      return result;
    }

    function applyLightPress(state, position) {
      const next = state.slice();
      lightNeighbours(position).forEach(pos => { next[pos] = !next[pos]; });
      return next;
    }

    function allLightsOn(state) {
      for (let i=0;i<state.length;i++) if (!state[i]) return false;
      return true;
    }

    function solveLights(board) {
      const initial = board.map(cell => cell.on);
      if (allLightsOn(initial)) return [];
      let best = null;
      for (let mask=1;mask<512;mask++) {
        let state = initial.slice();
        const presses = [];
        for (let pos=0;pos<9;pos++) {
          if (mask & (1 << pos)) {
            presses.push(pos);
            state = applyLightPress(state,pos);
          }
        }
        if (!allLightsOn(state)) continue;
        if (best === null || presses.length < best.length) best = presses;
      }
      return best;
    }

    function runLights() {
      const board = getLightsBoard();
      if (board.filter(cell => cell !== null).length !== 9) return false;
      clearNumbers();
      const solution = solveLights(board);
      if (solution === null) {
        console.log('HK LIGHTS: решения не найдено');
        return true;
      }
      if (solution.length === 0) {
        console.log('HK LIGHTS: все лампы уже включены');
        return true;
      }
      solution.forEach((position,index) => addNumber(board[position].element,index + 1));
      console.log('HK LIGHTS: нажать лампы:',solution.map(pos => pos + 1));
      return true;
    }

    function getBattleAttack() {
      const sword = document.querySelector('[data-lot-id^="mf_treasurelot_sword_"]');
      if (!sword) return null;
      const id = sword.getAttribute('data-lot-id') || '';
      const match = id.match(/mf_treasurelot_sword_d+_(d+)/);
      return match ? Number(match[1]) : null;
    }

    function getBattleBoard() {
      const board = new Array(BATTLE_SIZE).fill(null);
      const enemies = [...document.querySelectorAll('[data-lot-id*="mf_treasurelot_enemy_type_"]')];
      enemies.forEach(element => {
        const id = element.getAttribute('data-lot-id') || '';
        const match = id.match(/enemy_type_(01|02|03)_(d+)_sl(d+)/);
        if (!match) return;
        const type = match[1];
        const hp = Number(match[2]);
        const slot = Number(match[3]);
        const position = slot - BATTLE_FIRST_SLOT;
        if (position < 0 || position >= BATTLE_SIZE) return;
        board[position] = {type,hp,alive:true,element,slot};
      });
      return board;
    }

    function battleNeighbours(position) {
      const result = [];
      const row = Math.floor(position / BATTLE_COLS);
      const col = position % BATTLE_COLS;
      if (col > 0) result.push(position - 1);
      if (col < BATTLE_COLS - 1) result.push(position + 1);
      if (row > 0) result.push(position - BATTLE_COLS);
      if (row < BATTLE_ROWS - 1) result.push(position + BATTLE_COLS);
      return result;
    }

    function copyBattleState(state) {
      return state.map(enemy => enemy ? {type:enemy.type,hp:enemy.hp,alive:enemy.alive} : null);
    }

    function resolveBattleDeaths(state, firstPosition) {
      const queue = [firstPosition];
      while (queue.length > 0) {
        const position = queue.shift();
        const enemy = state[position];
        if (!enemy || !enemy.alive || enemy.hp > 0) continue;
        enemy.alive = false;
        const around = battleNeighbours(position);
        if (enemy.type === BLUE) {
          around.forEach(pos => {
            const target = state[pos];
            if (!target || !target.alive) return;
            target.hp -= 2;
            if (target.hp <= 0) queue.push(pos);
          });
        }
        if (enemy.type === GREEN) {
          around.forEach(pos => {
            const target = state[pos];
            if (!target || !target.alive) return;
            target.hp += 3;
          });
        }
      }
    }

    function battleAttack(state, position) {
      const enemy = state[position];
      if (!enemy || !enemy.alive || enemy.hp <= 0) return null;
      const next = copyBattleState(state);
      const cost = next[position].hp;
      next[position].hp = 0;
      resolveBattleDeaths(next,position);
      return {state:next,cost};
    }

    function countBattleAlive(state) {
      let count = 0;
      state.forEach(enemy => { if (enemy && enemy.alive) count += 1; });
      return count;
    }

    function battleStateKey(state) {
      return state.map(enemy => !enemy ? '-' : !enemy.alive ? 'X' : enemy.type + ':' + enemy.hp).join('|');
    }

    function betterBattleSolution(candidate,current) {
      if (!current) return true;
      if (candidate.killed > current.killed) return true;
      if (candidate.killed < current.killed) return false;
      if (candidate.cost < current.cost) return true;
      if (candidate.cost > current.cost) return false;
      return candidate.order.length < current.order.length;
    }

    function solveBattle(initialState,maxAttack) {
      const memo = new Map();
      function dfs(state,remaining) {
        const key = battleStateKey(state) + '#' + remaining;
        if (memo.has(key)) return memo.get(key);
        const aliveBefore = countBattleAlive(state);
        let best = {killed:0,cost:0,order:[]};
        if (aliveBefore === 0) {
          memo.set(key,best);
          return best;
        }
        for (let position=0;position<BATTLE_SIZE;position++) {
          const enemy = state[position];
          if (!enemy || !enemy.alive || enemy.hp <= 0 || enemy.hp > remaining) continue;
          const result = battleAttack(state,position);
          if (!result) continue;
          const killedNow = aliveBefore - countBattleAlive(result.state);
          const rest = dfs(result.state,remaining - result.cost);
          const candidate = {killed:killedNow + rest.killed,cost:result.cost + rest.cost,order:[position].concat(rest.order)};
          if (betterBattleSolution(candidate,best)) best = candidate;
        }
        memo.set(key,best);
        return best;
      }
      return dfs(initialState,maxAttack);
    }

    function runBattle() {
      const maxAttack = getBattleAttack();
      if (maxAttack === null) return false;
      const board = getBattleBoard();
      const enemies = board.filter(enemy => enemy !== null);
      if (enemies.length === 0) return false;
      clearNumbers();
      const state = board.map(enemy => enemy ? {type:enemy.type,hp:enemy.hp,alive:true} : null);
      const solution = solveBattle(state,maxAttack);
      if (!solution || solution.order.length === 0) return true;
      solution.order.forEach((position,index) => {
        const enemy = board[position];
        if (enemy?.element) addNumber(enemy.element,index + 1);
      });
      console.log('HK BATTLE ATK:',maxAttack);
      console.log('HK BATTLE потрачено:',solution.cost);
      console.log('HK BATTLE уничтожено:',solution.killed,'из',enemies.length);
      console.log('HK BATTLE нажать слоты:',solution.order.map(pos => pos + BATTLE_FIRST_SLOT));
      return true;
    }

    function getSignature() {
      const lights = [...document.querySelectorAll('[data-lot-id^="mf_fairlot_lights_out_sl"]')];
      if (lights.length === 9) return 'LIGHTS|' + lights.map(element => element.getAttribute('data-lot-id')).join('|');

      const sword = document.querySelector('[data-lot-id^="mf_treasurelot_sword_"]');
      const enemies = [...document.querySelectorAll('[data-lot-id*="mf_treasurelot_enemy_type_"]')];
      if (sword && enemies.length > 0) {
        return 'BATTLE|' + sword.getAttribute('data-lot-id') + '|' +
          enemies.map(element => element.getAttribute('data-lot-id')).join('|');
      }
      return 'NONE';
    }

    function checkPuzzle() {
      const signature = getSignature();
      if (signature === lastSignature) return;
      lastSignature = signature;
      clearNumbers();
      if (signature.startsWith('LIGHTS|')) { runLights(); return; }
      if (signature.startsWith('BATTLE|')) runBattle();
    }

    function start() {
      if (intervalId !== null) return;
      initialTimerId = setTimeout(checkPuzzle,300);
      intervalId = setInterval(checkPuzzle,500);
      recordDiagnostic('puzzle-solver-start',{revision:HK_PUZZLE_SOLVER_REV});
    }

    function stop() {
      if (initialTimerId !== null) clearTimeout(initialTimerId);
      if (intervalId !== null) clearInterval(intervalId);
      initialTimerId = null;
      intervalId = null;
      lastSignature = '';
      clearNumbers();
      recordDiagnostic('puzzle-solver-stop',{revision:HK_PUZZLE_SOLVER_REV});
    }

    return {revision:HK_PUZZLE_SOLVER_REV,start,stop,check:checkPuzzle,get running(){return intervalId !== null;}};
  })();
  runtime.puzzleSolver = hkPuzzleSolver;

  runtime.destroy = () => {
    runtime.active = false;
    hkPuzzleSolver.stop();
    try { root?.remove(); } catch (_) {}
    try { bootstrapButton?.remove(); } catch (_) {}
    root = null;
    panel = null;
  };

  // PRELOGIN_ZERO_GAME_API_R1: install only passive interception before login."""

replace_once(anchor,module,"embed puzzle solver")

replace_once(
    """  startNetworkCapture();
  startAfterNativeGameLogin();""",
    """  hkPuzzleSolver.start();
  startNetworkCapture();
  startAfterNativeGameLogin();""",
    "start background puzzle solver"
)

for marker in [
    "HK_PUZZLE_SOLVER_REV = 'puzzle-solver-v3-embedded-20260921-r1'",
    "runtime.puzzleSolver = hkPuzzleSolver;",
    "hkPuzzleSolver.start();",
    "hkPuzzleSolver.stop();",
    "[data-lot-id^=\"mf_fairlot_lights_out_sl\"]",
    "[data-lot-id*=\"mf_treasurelot_enemy_type_\"]",
    "setInterval(checkPuzzle,500)",
    "setTimeout(checkPuzzle,300)",
    "businesses-finalize-single-snapshot-20260921-r1",
    "core-20260921-r27-businesses-runner-canon",
]:
    require(marker,"post-patch "+marker)

PATH.write_text(s,encoding="utf-8")
print("PUZZLE_SOLVER_EMBED_R1_PATCH=PASS")
