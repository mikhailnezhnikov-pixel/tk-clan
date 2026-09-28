// Canonical hint-only Lights Out solver extracted verbatim from HamsterKingMobile 1.18.04.
// Purpose: immutable reference for the labyrinth lamp puzzle.
// Automation must preserve this solver's board model and solution set; it may only add
// deterministic UI execution around the frozen hinted slots.
//
// Source candidate blob: d7bc8d2669317778d5d76c4f0a6eb90e4e853580
// Captured: 2026-09-28
//
// The solver target is ALL NINE LAMPS ON. A solution is a set of distinct slots;
// each planned slot is clicked at most once. Click order does not change the result.

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
        const match = id.match(/mf_fairlot_lights_out_sl(\d+)_(true|false)/);
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

