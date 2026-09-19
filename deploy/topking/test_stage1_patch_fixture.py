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
  const GROWTH_NO_PROGRESS_LIMIT = 2;
  class HKNetworkTimeout extends Error {}
  function growthCostOnlyUses(cost, allowed) { return true; }
  function growthHamsterCostSafe(cost) { return growthCostOnlyUses(cost,[GROWTH_HAMSTER_BUDGET_ID]); }
  function growthGeneralCostSafe(cost) { return growthCostOnlyUses(cost,[GROWTH_GENERAL_BUDGET_ID]); }
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
        check=True,
        capture_output=True,
        text=True,
    )
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

        run_patch()
        second = TARGET.read_text(encoding='utf-8')
        validate(second)

        if first != second:
            raise AssertionError('Stage 1 patch is not idempotent on existing 1.15.0')

        print('STAGE1_PATCH_FIXTURE_TEST_OK')
    finally:
        if original is None:
            TARGET.unlink(missing_ok=True)
        else:
            TARGET.write_bytes(original)

if __name__ == '__main__':
    main()
