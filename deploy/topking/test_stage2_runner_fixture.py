from pathlib import Path
import subprocess
import sys
import re

ROOT = Path(__file__).resolve().parents[2]
PATCH = Path(__file__).with_name('stage2_runner_patch.py')
TARGET = Path('/tmp/HamsterKingMobile.user.js')

FIXTURE = r"""// ==UserScript==
// @version      1.15.0
(() => {
  'use strict';
  const VERSION = true ? 'fixture' : '1.15.0';
  const GROWTH_HAMSTER_BUDGET_ID = 'cur_cap';
  const GROWTH_GENERAL_BUDGET_ID = 'item_pit_token';
  const hkRunner = (() => {
    const state = {status:'idle'};
    let abortController = null;
    return {
      state,
      get signal(){ return abortController?.signal || null; },
      get running(){ return state.status === 'running'; },
      start(){ abortController = new AbortController(); state.status='running'; },
      async waitIfPaused(){ if(abortController?.signal.aborted) throw new DOMException('Aborted','AbortError'); },
      stop(reason='user'){ abortController?.abort(reason); state.status='stopping'; return true; },
      setStep(){},
      finish(){ state.status='done'; },
      fail(){ state.status='error'; },
      reset(){ state.status='idle'; abortController=null; }
    };
  })();
  const runtime = {};
  const HK_MUTATION_GATE_REV = 'stage1-20260919-r4';
  runtime.runner = hkRunner;
  runtime.mutationGate = {};

  async function gameRetryDelay(ms) { return ms; }
  async function apiJson() { return {}; }
  const root = {querySelector(){ return {value:'1',checked:false}; }};
  const either = (a,b) => a;
  const requireLicense = () => true;
  const alert = () => {};
  const confirm = () => true;
  const log = () => {};
  const save = () => {};
  const updatePitButtons = () => {};
  const pitState = () => ({round:1});
  const pitPowerValue = () => 1;
  const rememberPower = () => {};
  const clickRestoreToken = () => false;
  const clickText = () => false;
  const visible = () => false;
  const document = {querySelectorAll(){return []},body:{innerText:''}};
  let settings = {target:2,interval:1,activationLimit:1,restoreLimit:1,allowTokens:true,collectOnly:false};
  let activationSpent=0,restoreSpent=0,pitRunStart=null,pitRunning=false;
  let fairRunning=false,fairStop=false,selectedFairLots=new Set(['x']),selectedFairId='fair';
  const selectedFairSlotRules=new Map([['x',{regular:true,vip:true}]]);
  const fairCatalog=[];
  const locale=()=> 'ru-RU';
  const fairComboSettings=()=>({exactLots:0});
  const fairState=()=>({fair_reroll_cost:{}});
  const safeReroll=()=>true;
  const costParts=()=>[];
  const fairSlotOptions=()=>[];
  const updateFairControls=()=>{};
  const budgetDecision=()=>({allowed:true,problems:[]});
  const isEventFairState=()=>false;
  const appendExpense=()=>{};
  const walletAmount=()=>0;
  const updateWalletFromResponse=()=>{};
  let playerDocument={},fairDocument={};
  function updatePitStatus(){}

  async function pitLoop() {
    while (pitRunning) {
      const state = pitState();
      rememberPower(state);
      updatePitStatus(state);
      if (state.round !== null && state.round >= settings.target) {
        pitRunning = false; log(`Цель достигнута: раунд ${state.round}`, 'ok'); break;
      }
      if (settings.collectOnly) {
        await sleep(Math.max(700, settings.interval * 1000));
        continue;
      }
      let acted = false;
      await sleep(Math.max(700, settings.interval * 1000));
      if (!acted) await sleep(500);
    }
    updatePitButtons();
  }

  function updatePitStatus(){}

  async function runFair() {
    if (!requireLicense() || fairRunning || !selectedFairLots.size) return;
    if ([...selectedFairLots].some(lotId => {
      const rule = selectedFairSlotRules.get(lotId); return !(rule?.regular || rule?.vip);
    })) {
      alert('no cells'); return;
    }
    const buyLimit = Math.max(1, Number(root.querySelector('#hk-fair-buy-limit').value || 1));
    const rerollLimit = Math.max(0, Number(root.querySelector('#hk-fair-reroll-limit').value || 0));
    const allowPremium = root.querySelector('#hk-fair-premium-reroll').checked;
    const combo = fairComboSettings();
    let state = fairState(selectedFairId);
    if (!safeReroll(state?.fair_reroll_cost, allowPremium)) { alert('blocked'); return; }
    const cost = costParts(state?.fair_reroll_cost)[0];
    const worst = cost ? `${cost.quantity * rerollLimit} ${cost.id}` : '0';
    const maximumCrystalLotCost = 0;
    const crystalNotice = '';
    if (!confirm('go')) return;
    fairRunning = true; fairStop = false; updateFairControls();
    let bought = 0, bonusBought = 0, rerolls = 0, authRetries = 0;
    try {
      playerDocument = await apiJson('/player/me', 'POST');
      fairDocument = playerDocument;
      while (!fairStop && bought < buyLimit) {
        state = fairState(selectedFairId);
        if (!state) throw new Error('missing');
        const purchased = false;
        if (!purchased) {
          if (rerolls >= rerollLimit) break;
          fairDocument = await apiJson('/fair/reroll', 'POST', {fair_id:selectedFairId});
          rerolls++;
        }
        await sleep(550);
      }
      log(`Ярмарка завершена: выбранных покупок ${bought}, бонусных ${bonusBought}, прокруток ${rerolls}`, 'ok');
    } catch (error) { log(`Аварийная остановка ярмарки: ${error.message}`, 'bad'); }
    finally { fairRunning = false; fairStop = false; renderFair(); }
  }

  function ordinaryShopGroup(){}

  const renderFair=()=>{};
  const sleep = ms => Promise.resolve(ms);

  function wire() {
    root.querySelector('#hk-pit-start').onclick = () => {
      if (!requireLicense()) return;
      settings = {
        target: Math.max(1, Number(root.querySelector('#hk-target').value || 1)),
        interval: Math.max(.7, Number(root.querySelector('#hk-interval').value || 1.2)),
        activationLimit: Math.max(0, Number(root.querySelector('#hk-activation-limit').value || 0)),
        restoreLimit: Math.max(0, Number(root.querySelector('#hk-restore-limit').value || 0)),
        allowTokens: root.querySelector('#hk-allow-tokens').checked,
        collectOnly: root.querySelector('#hk-pit-collect-only').checked
      };
      save({settings}); activationSpent = 0; restoreSpent = 0; pitRunStart = (() => { const state=pitState(); return {round:state.round,power:pitPowerValue(state)}; })(); pitRunning = true; updatePitButtons(); log(settings.collectOnly ? either('Запущен безопасный сбор данных Ямы без боя','Started safe Pit data collection without battle') : `Автобой запущен до раунда ${settings.target}`); pitLoop();
    };
    root.querySelector('#hk-pit-stop').onclick = () => { pitRunning = false; updatePitButtons(); log('Автобой остановлен'); };
    root.querySelector('#hk-fair-start').onclick = runFair;
    root.querySelector('#hk-fair-stop').onclick = () => { fairStop = true; log('Останавливаю ярмарку после текущего запроса…', 'warn'); };
  }
})();
"""

def run_patch():
    subprocess.run([sys.executable, str(PATCH)], cwd=ROOT, check=True)

def validate(text: str):
    required = [
        '// @version      1.16.0',
        "HK_STAGE2_RUNNER_REV = 'stage2a-20260919-r1'",
        "GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'",
        "GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'",
        "hkRunner.stop('pit')",
        "hkRunner.stop('fair')",
        "title:either('Яма','Pit')",
        "title:either('Ярмарка','Fair')",
        "await gameRetryDelay(Math.max(700, settings.interval * 1000));",
        "await gameRetryDelay(550);",
    ]
    for needle in required:
        if needle not in text:
            raise AssertionError(f'missing: {needle}')
    if text.count("HK_STAGE2_RUNNER_REV = 'stage2a-20260919-r1'") != 1:
        raise AssertionError('Stage 2 revision duplicated')
    if text.count("hkRunner.stop('pit')") != 1:
        raise AssertionError('Pit Stop duplicated')
    if text.count("hkRunner.stop('fair')") != 1:
        raise AssertionError('Fair Stop duplicated')
    pit_start = text.index('async function pitLoop()')
    pit_end = text.index('function updatePitStatus(', pit_start)
    pit = text[pit_start:pit_end]
    if 'await sleep(Math.max(700, settings.interval * 1000));' in pit or 'await sleep(500);' in pit:
        raise AssertionError('Pit still contains non-abortable delay')
    fair_start = text.index('async function runFair()')
    fair_end = text.index('function ordinaryShopGroup(', fair_start)
    fair = text[fair_start:fair_end]
    if 'await sleep(550);' in fair:
        raise AssertionError('Fair still contains non-abortable delay')
    if 'hk-growth-nuts-percent' in text or 'growthNutCost' in text:
        raise AssertionError('obsolete Hamster budget path found')

def main():
    original = TARGET.read_bytes() if TARGET.exists() else None
    try:
        TARGET.write_text(FIXTURE, encoding='utf-8')
        run_patch()
        first = TARGET.read_text(encoding='utf-8')
        validate(first)
        subprocess.run(['node', '--check', str(TARGET)], check=True)

        run_patch()
        second = TARGET.read_text(encoding='utf-8')
        validate(second)
        subprocess.run(['node', '--check', str(TARGET)], check=True)
        if first != second:
            raise AssertionError('Stage 2A patch is not byte-idempotent')
        print('STAGE2A_RUNNER_FIXTURE_TEST_OK')
    finally:
        if original is None:
            TARGET.unlink(missing_ok=True)
        else:
            TARGET.write_bytes(original)

if __name__ == '__main__':
    main()
