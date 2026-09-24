// ==UserScript==
// @name         HK Puzzle Solver — Top King
// @namespace    hk-puzzle
// @version      3.1.0
// @description  Подсказчик порядка ходов + локальный журнал действий Рыбалки/Сокровищницы для Hamster King
// @match        https://*.hamsterking.games/*
// @match        https://hamsterking.games/*
// @homepageURL  https://tk-clan.ru/information/
// @downloadURL  https://raw.githubusercontent.com/mikhailnezhnikov-pixel/tk-clan/main/scripts/hk-puzzle-solver.user.js
// @updateURL    https://raw.githubusercontent.com/mikhailnezhnikov-pixel/tk-clan/main/scripts/hk-puzzle-solver.user.js
// @run-at       document-idle
// @grant        none
// ==/UserScript==

(function () {
    'use strict';

    const BATTLE_FIRST_SLOT = 7;
    const BATTLE_SIZE = 12;
    const BATTLE_COLS = 3;
    const BATTLE_ROWS = 4;

    const RED = '01';
    const BLUE = '02';
    const GREEN = '03';

    let lastSignature = '';

    const HISTORY_KEY = 'hkPuzzleSolverHistoryV1';
    const HISTORY_LIMIT = 250;

    function readHistory() {
        try {
            const raw = localStorage.getItem(HISTORY_KEY);
            const parsed = raw ? JSON.parse(raw) : [];
            return Array.isArray(parsed) ? parsed : [];
        } catch (_) {
            return [];
        }
    }

    function writeHistory(rows) {
        try {
            localStorage.setItem(HISTORY_KEY, JSON.stringify(rows.slice(-HISTORY_LIMIT)));
        } catch (_) {}
    }

    function recordHistory(type, payload) {
        const rows = readHistory();
        rows.push({
            ts: new Date().toISOString(),
            type: type,
            path: location.pathname,
            payload: payload || {}
        });
        writeHistory(rows);
    }

    function findLotElement(target) {
        if (!target || typeof target.closest !== 'function') return null;
        return target.closest('[data-lot-id]');
    }

    function classifyLotId(id) {
        id = String(id || '');
        if (/fish/i.test(id)) return 'fishing_click';
        if (/treasury|treasure.*way|way_[123]/i.test(id)) return 'treasury_click';
        if (/lights_out/i.test(id)) return 'labyrinth_click';
        if (/enemy_type_|treasurelot_sword/i.test(id)) return 'battle_click';
        return '';
    }

    function installHistoryCapture() {
        if (window.__HK_PUZZLE_HISTORY_CAPTURE__) return;
        window.__HK_PUZZLE_HISTORY_CAPTURE__ = true;

        document.addEventListener('click', function (event) {
            const el = findLotElement(event.target);
            if (!el) return;

            const id = el.getAttribute('data-lot-id') || '';
            const type = classifyLotId(id);
            if (!type) return;

            recordHistory(type, {
                lotId: id,
                text: String(el.textContent || '').trim().slice(0, 160)
            });
        }, true);
    }

    function clearNumbers() {
        const numbers = [...document.querySelectorAll('.hkSolverNumber')];
        numbers.forEach(function (el) { el.remove(); });
    }

    function addNumber(element, number) {
        if (!element) return;

        const style = window.getComputedStyle(element);
        if (style.position === 'static') {
            element.style.position = 'relative';
        }

        const badge = document.createElement('div');
        badge.className = 'hkSolverNumber';
        badge.textContent = String(number);

        Object.assign(badge.style, {
            position: 'absolute',
            top: '6px',
            right: '6px',
            width: '38px',
            height: '38px',
            borderRadius: '50%',
            background: number === 1 ? '#62ff75' : '#ffd740',
            color: '#000',
            border: '3px solid #fff',
            boxSizing: 'border-box',
            fontSize: '22px',
            fontWeight: '900',
            lineHeight: '32px',
            textAlign: 'center',
            zIndex: '9999999',
            boxShadow: '0 2px 8px rgba(0,0,0,.9)',
            pointerEvents: 'none',
            userSelect: 'none'
        });

        element.appendChild(badge);
    }

    // =========================
    // LIGHTS OUT 3x3
    // =========================

    function getLightsBoard() {
        const board = new Array(9).fill(null);
        const elements = [
            ...document.querySelectorAll(
                '[data-lot-id^="mf_fairlot_lights_out_sl"]'
            )
        ];

        elements.forEach(function (el) {
            const id = el.getAttribute('data-lot-id') || '';
            const match = id.match(
                /mf_fairlot_lights_out_sl(\d+)_(true|false)/
            );

            if (!match) return;

            const slot = Number(match[1]);
            const isOn = match[2] === 'true';

            if (slot < 1 || slot > 9) return;

            board[slot - 1] = {
                slot: slot,
                on: isOn,
                element: el
            };
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
        const affected = lightNeighbours(position);

        affected.forEach(function (pos) {
            next[pos] = !next[pos];
        });

        return next;
    }

    function allLightsOn(state) {
        for (let i = 0; i < state.length; i++) {
            if (!state[i]) return false;
        }
        return true;
    }

    function solveLights(board) {
        const initial = board.map(function (cell) {
            return cell.on;
        });

        if (allLightsOn(initial)) return [];

        let best = null;

        for (let mask = 1; mask < 512; mask++) {
            let state = initial.slice();
            const presses = [];

            for (let pos = 0; pos < 9; pos++) {
                if (mask & (1 << pos)) {
                    presses.push(pos);
                    state = applyLightPress(state, pos);
                }
            }

            if (!allLightsOn(state)) continue;

            if (best === null || presses.length < best.length) {
                best = presses;
            }
        }

        return best;
    }

    function runLights() {
        const board = getLightsBoard();
        const valid = board.filter(function (cell) {
            return cell !== null;
        });

        if (valid.length !== 9) return false;

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

        solution.forEach(function (position, index) {
            addNumber(board[position].element, index + 1);
        });

        console.log(
            'HK LIGHTS: нажать лампы:',
            solution.map(function (pos) { return pos + 1; })
        );

        return true;
    }

    // =========================
    // BATTLE
    // =========================

    function getBattleAttack() {
        const sword = document.querySelector(
            '[data-lot-id^="mf_treasurelot_sword_"]'
        );

        if (!sword) return null;

        const id = sword.getAttribute('data-lot-id') || '';
        const match = id.match(/mf_treasurelot_sword_\d+_(\d+)/);

        if (!match) return null;
        return Number(match[1]);
    }

    function getBattleBoard() {
        const board = new Array(BATTLE_SIZE).fill(null);

        const enemies = [
            ...document.querySelectorAll(
                '[data-lot-id*="mf_treasurelot_enemy_type_"]'
            )
        ];

        enemies.forEach(function (el) {
            const id = el.getAttribute('data-lot-id') || '';
            const match = id.match(
                /enemy_type_(01|02|03)_(\d+)_sl(\d+)/
            );

            if (!match) return;

            const type = match[1];
            const hp = Number(match[2]);
            const slot = Number(match[3]);
            const position = slot - BATTLE_FIRST_SLOT;

            if (position < 0 || position >= BATTLE_SIZE) return;

            board[position] = {
                type: type,
                hp: hp,
                alive: true,
                element: el,
                slot: slot
            };
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
        return state.map(function (enemy) {
            if (!enemy) return null;

            return {
                type: enemy.type,
                hp: enemy.hp,
                alive: enemy.alive
            };
        });
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
                around.forEach(function (pos) {
                    const target = state[pos];

                    if (!target || !target.alive) return;

                    target.hp -= 2;

                    if (target.hp <= 0) {
                        queue.push(pos);
                    }
                });
            }

            if (enemy.type === GREEN) {
                around.forEach(function (pos) {
                    const target = state[pos];

                    if (!target || !target.alive) return;

                    target.hp += 3;
                });
            }
        }
    }

    function battleAttack(state, position) {
        const enemy = state[position];

        if (!enemy || !enemy.alive || enemy.hp <= 0) {
            return null;
        }

        const next = copyBattleState(state);
        const cost = next[position].hp;

        next[position].hp = 0;
        resolveBattleDeaths(next, position);

        return {
            state: next,
            cost: cost
        };
    }

    function countBattleAlive(state) {
        let count = 0;

        state.forEach(function (enemy) {
            if (enemy && enemy.alive) count++;
        });

        return count;
    }

    function battleStateKey(state) {
        return state.map(function (enemy) {
            if (!enemy) return '-';
            if (!enemy.alive) return 'X';

            return enemy.type + ':' + enemy.hp;
        }).join('|');
    }

    function betterBattleSolution(candidate, current) {
        if (!current) return true;

        if (candidate.killed > current.killed) return true;
        if (candidate.killed < current.killed) return false;

        if (candidate.cost < current.cost) return true;
        if (candidate.cost > current.cost) return false;

        if (candidate.order.length < current.order.length) return true;

        return false;
    }

    function solveBattle(initialState, maxAttack) {
        const memo = new Map();

        function dfs(state, remaining) {
            const key = battleStateKey(state) + '#' + remaining;

            if (memo.has(key)) {
                return memo.get(key);
            }

            const aliveBefore = countBattleAlive(state);

            let best = {
                killed: 0,
                cost: 0,
                order: []
            };

            if (aliveBefore === 0) {
                memo.set(key, best);
                return best;
            }

            for (let position = 0; position < BATTLE_SIZE; position++) {
                const enemy = state[position];

                if (!enemy || !enemy.alive || enemy.hp <= 0) continue;
                if (enemy.hp > remaining) continue;

                const result = battleAttack(state, position);
                if (!result) continue;

                const aliveAfter = countBattleAlive(result.state);
                const killedNow = aliveBefore - aliveAfter;

                const rest = dfs(
                    result.state,
                    remaining - result.cost
                );

                const candidate = {
                    killed: killedNow + rest.killed,
                    cost: result.cost + rest.cost,
                    order: [position].concat(rest.order)
                };

                if (betterBattleSolution(candidate, best)) {
                    best = candidate;
                }
            }

            memo.set(key, best);
            return best;
        }

        return dfs(initialState, maxAttack);
    }

    function runBattle() {
        const maxAttack = getBattleAttack();

        if (maxAttack === null) return false;

        const board = getBattleBoard();

        const enemies = board.filter(function (enemy) {
            return enemy !== null;
        });

        if (enemies.length === 0) return false;

        clearNumbers();

        const state = board.map(function (enemy) {
            if (!enemy) return null;

            return {
                type: enemy.type,
                hp: enemy.hp,
                alive: true
            };
        });

        const solution = solveBattle(state, maxAttack);

        if (!solution || solution.order.length === 0) {
            return true;
        }

        solution.order.forEach(function (position, index) {
            const enemy = board[position];

            if (enemy && enemy.element) {
                addNumber(enemy.element, index + 1);
            }
        });

        console.log('HK BATTLE ATK:', maxAttack);
        console.log('HK BATTLE потрачено:', solution.cost);
        console.log(
            'HK BATTLE уничтожено:',
            solution.killed,
            'из',
            enemies.length
        );

        console.log(
            'HK BATTLE нажать слоты:',
            solution.order.map(function (pos) {
                return pos + BATTLE_FIRST_SLOT;
            })
        );

        return true;
    }

    // =========================
    // AUTO DETECT
    // =========================

    function getSignature() {
        const lights = [
            ...document.querySelectorAll(
                '[data-lot-id^="mf_fairlot_lights_out_sl"]'
            )
        ];

        if (lights.length === 9) {
            return (
                'LIGHTS|' +
                lights.map(function (el) {
                    return el.getAttribute('data-lot-id');
                }).join('|')
            );
        }

        const sword = document.querySelector(
            '[data-lot-id^="mf_treasurelot_sword_"]'
        );

        const enemies = [
            ...document.querySelectorAll(
                '[data-lot-id*="mf_treasurelot_enemy_type_"]'
            )
        ];

        if (sword && enemies.length > 0) {
            return (
                'BATTLE|' +
                sword.getAttribute('data-lot-id') +
                '|' +
                enemies.map(function (el) {
                    return el.getAttribute('data-lot-id');
                }).join('|')
            );
        }

        return 'NONE';
    }

    function checkPuzzle() {
        const signature = getSignature();

        if (signature === lastSignature) return;

        lastSignature = signature;
        clearNumbers();

        if (signature !== 'NONE') {
            recordHistory('board_state', { signature: signature });
        }

        if (signature.indexOf('LIGHTS|') === 0) {
            runLights();
            return;
        }

        if (signature.indexOf('BATTLE|') === 0) {
            runBattle();
            return;
        }
    }

    installHistoryCapture();

    window.__HK_PUZZLE_SOLVER__ = {
        version: '3.1.0',
        check: checkPuzzle,
        getHistory: function () {
            return readHistory();
        },
        clearHistory: function () {
            writeHistory([]);
            return true;
        },
        exportHistory: function () {
            return JSON.stringify(readHistory(), null, 2);
        }
    };

    setInterval(checkPuzzle, 500);
    setTimeout(checkPuzzle, 300);

})();