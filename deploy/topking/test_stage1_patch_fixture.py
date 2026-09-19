from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PATCH = Path(__file__).with_name('stage1_runner_patch.py')
TARGET = Path('/tmp/HamsterKingMobile.user.js')

FIXTURE = r"""// ==UserScript==
// @version      1.14.4
(() => {
  'use strict';
  const SOME_RUNTIME_VERSION = true ? 'fixture' : '1.14.4';
  const GROWTH_HAMSTER_BUDGET_ID = 'cur_cap';
  const GROWTH_GENERAL_BUDGET_ID = 'item_pit_token';
  class HKNetworkTimeout extends Error {}
  function costParts(cost) { return Array.isArray(cost?.parts) ? cost.parts : []; }
  function growthCapCost(cost){ return costParts(cost).filter(row=>row.kind==='currencies'&&row.id===GROWTH_HAMSTER_BUDGET_ID).reduce((sum,row)=>sum+Math.max(0,row.quantity),0); }
  function growthPitCost(cost){ return costParts(cost).filter(row=>row.kind==='items'&&row.id===GROWTH_GENERAL_BUDGET_ID).reduce((sum,row)=>sum+Math.max(0,row.quantity),0); }
  function growthSafeCost(cost){ return costParts(cost).every(row=>row.id&&row.quantity>0&&!['cur_prem','cur_hard'].includes(row.id)); }
  function growthHamsterCostSafe(cost){ return growthSafeCost(cost)&&growthPitCost(cost)===0; }
  function growthHamsterLevelCostSafe(cost){ return growthHamsterCostSafe(cost)&&growthCapCost(cost)>0; }
  function growthCanAfford(cost,state){ return true; }
  function growthBestGeneral(state,blocked,budget,mode='x1',weightValue=1){
    for(const general of [{nextLevelUp:{costs:{parts:[{kind:'items',id:GROWTH_GENERAL_BUDGET_ID,quantity:1}]}},nearest10LevelUp:{costs:{parts:[{kind:'items',id:GROWTH_GENERAL_BUDGET_ID,quantity:10}]}}}]){
      let actionType=null,preview=general.nextLevelUp,costs=preview.costs||{};
      if(mode==='fast10'&&general?.nearest10LevelUp){const fast=general.nearest10LevelUp.costs||{};if(growthCanAfford(fast,state)&&budget.spent+growthPitCost(fast)<=budget.limit){actionType='fast10';preview=general.nearest10LevelUp;costs=fast;}}
      const pit=growthPitCost(costs);if(pit<=0||!growthCanAfford(costs,state)||budget.spent+pit>budget.limit)continue;
      return {actionType,pit,costs};
    }
    return null;
  }
  function growthRunGeneralsCore() {}
  function growthRunPriorityCopiesCore() {}
  function growthRunLevelsCore() {}
  async function refreshModuleLive() {}
  const hkGameBridge = {};
  function recordDiagnostic() {}

  async function apiJson(path, method = 'GET', body = null, retryAuthorization = true, retryNetwork = 3) {
    if (retryAuthorization === 'again') {
      return apiJson(path, method, body, false, retryNetwork);
    }
    if (retryNetwork > 0 && path === '/fixture/retry') {
      return apiJson(path, method, body, retryAuthorization, retryNetwork - 1);
    }
    return {ok:true};
  }

  function deepObjects(value, depth = 0, output = []) { return output; }

  const hkRunner = {};
  const runtime = {};
  runtime.runner = hkRunner;
})();
"""

def run_patch():
    completed = subprocess.run(
        [sys.executable, str(PATCH)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise AssertionError('patcher failed:\n' + completed.stdout + completed.stderr)
    if 'STAGE1_MUTATION_GATE_TEST_OK' not in completed.stdout:
        raise AssertionError('mutation gate regression test did not run inside patcher')

def validate(text: str):
    if '// @version      1.15.0' not in text:
        raise AssertionError('fixture was not upgraded to 1.15.0')
    if text.count("const HK_MUTATION_GATE_REV = 'stage1-20260919-r4';") != 1:
        raise AssertionError('Stage 1 revision block must exist exactly once')
    if text.count('const hkMutationGate = (() => {') != 1:
        raise AssertionError('mutation gate must exist exactly once')
    if text.count('async function apiJson(path, method =') != 1:
        raise AssertionError('public apiJson wrapper must exist exactly once')
    if text.count('async function apiJsonCore(path, method =') != 1:
        raise AssertionError('apiJsonCore must exist exactly once')
    if "GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'" not in text:
        raise AssertionError('Hamster Caps invariant lost')
    if "GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'" not in text:
        raise AssertionError('General Pit Token invariant lost')
    if "growthCostOnlyUses(cost,[GROWTH_HAMSTER_BUDGET_ID])" not in text:
        raise AssertionError('fixture did not migrate Hamsters to strict Caps-only costs')
    if "growthCostOnlyUses(cost,[GROWTH_GENERAL_BUDGET_ID])" not in text:
        raise AssertionError('fixture did not migrate Generals to strict Pit-Token-only costs')
    if text.count('GROWTH_NO_PROGRESS_LIMIT') < 1:
        raise AssertionError('fixture did not add no-progress protection')
    core_start = text.index('async function apiJsonCore(')
    gate_start = text.index("const HK_MUTATION_GATE_REV = 'stage1-20260919-r4';", core_start)
    core = text[core_start:gate_start]
    import re
    if re.search(r'\bapiJson\s*\(', core):
        raise AssertionError('apiJsonCore still re-enters public apiJson')

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
            import difflib
            diff = ''.join(difflib.unified_diff(first.splitlines(True), second.splitlines(True), fromfile='first', tofile='second'))
            raise AssertionError('Stage 1 patch is not idempotent on existing 1.15.0\n' + diff[:12000])

        print('STAGE1_PATCH_FIXTURE_TEST_OK')
    finally:
        if original is None:
            TARGET.unlink(missing_ok=True)
        else:
            TARGET.write_bytes(original)

if __name__ == '__main__':
    main()
