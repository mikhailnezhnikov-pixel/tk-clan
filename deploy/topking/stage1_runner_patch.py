from pathlib import Path
import re
import subprocess

test_path = Path(__file__).with_name('test_stage1_mutation_gate.js')
if not test_path.exists():
    raise SystemExit('Stage 1 mutation gate regression test missing')
subprocess.run(['node', str(test_path)], check=True)

p = Path('/tmp/HamsterKingMobile.user.js')
s = p.read_text(encoding='utf-8')

def require(needle, message):
    if needle not in s:
        raise SystemExit(message)

is_1144 = '// @version      1.14.4' in s
is_1150 = '// @version      1.15.0' in s
if not (is_1144 or is_1150):
    raise SystemExit('expected live base 1.14.4 or existing Stage 1 1.15.0')

# Currency/data-source invariants from the verified 1.14.4 baseline.
require("GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'", 'hamster budget must be cur_cap')
require("GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'", 'general budget must be item_pit_token')
require('HKNetworkTimeout', 'network timeout protection missing')
require('GROWTH_NO_PROGRESS_LIMIT', 'Growth no-progress protection missing')
require('growthRunGeneralsCore', 'general runner missing')
require('growthRunPriorityCopiesCore', 'priority copy runner missing')
require('growthRunLevelsCore', 'hamster level runner missing')
require('async function refreshModuleLive', 'live reread helper missing')
require('const hkGameBridge', 'game UI refresh bridge missing')

if 'hk-growth-nuts-percent' in s:
    raise SystemExit('obsolete Nuts hamster budget control found')
if 'growthNutCost' in s:
    raise SystemExit('obsolete Nuts hamster cost path found')

# Harden Growth currency enforcement on the verified 1.14.4 source.
# Hamsters may spend only Caps (cur_cap); Generals may spend only Pit Tokens.
strict_hamster = "growthCostOnlyUses(cost,[GROWTH_HAMSTER_BUDGET_ID])"
strict_general = "growthCostOnlyUses(cost,[GROWTH_GENERAL_BUDGET_ID])"
if strict_hamster not in s or strict_general not in s:
    old_cost_guards = (
        "  function growthSafeCost(cost){ return costParts(cost).every(row=>row.id&&row.quantity>0&&!['cur_prem','cur_hard'].includes(row.id)); }\n"
        "  function growthHamsterCostSafe(cost){ return growthSafeCost(cost)&&growthPitCost(cost)===0; }\n"
        "  function growthHamsterLevelCostSafe(cost){ return growthHamsterCostSafe(cost)&&growthCapCost(cost)>0; }"
    )
    new_cost_guards = (
        "  function growthSafeCost(cost){ return costParts(cost).every(row=>row.id&&row.quantity>0&&!['cur_prem','cur_hard'].includes(row.id)); }\n"
        "  function growthCostOnlyUses(cost,allowed){const ids=new Set((allowed||[]).map(String)),parts=costParts(cost).filter(row=>row.id&&row.quantity>0);return parts.length>0&&parts.every(row=>ids.has(String(row.id)));}\n"
        "  function growthHamsterCostSafe(cost){ return growthSafeCost(cost)&&growthCostOnlyUses(cost,[GROWTH_HAMSTER_BUDGET_ID]); }\n"
        "  function growthHamsterLevelCostSafe(cost){ return growthHamsterCostSafe(cost)&&growthCapCost(cost)>0; }\n"
        "  function growthGeneralCostSafe(cost){ return growthSafeCost(cost)&&growthCostOnlyUses(cost,[GROWTH_GENERAL_BUDGET_ID])&&growthPitCost(cost)>0; }"
    )
    if old_cost_guards not in s:
        raise SystemExit('verified 1.14.4 Growth cost guard block not found')
    s = s.replace(old_cost_guards, new_cost_guards, 1)

# The General selector must reject a mixed or foreign-currency cost before any
# level-up request is sent. This is separate from the budget arithmetic.
if 'function growthBestGeneral' in s:
    old_fast = "if(mode==='fast10'&&general?.nearest10LevelUp){const fast=general.nearest10LevelUp.costs||{};if(growthCanAfford(fast,state)&&budget.spent+growthPitCost(fast)<=budget.limit)"
    new_fast = "if(mode==='fast10'&&general?.nearest10LevelUp){const fast=general.nearest10LevelUp.costs||{};if(growthGeneralCostSafe(fast)&&growthCanAfford(fast,state)&&budget.spent+growthPitCost(fast)<=budget.limit)"
    if old_fast in s:
        s = s.replace(old_fast, new_fast, 1)
    elif new_fast not in s:
        raise SystemExit('General fast10 selector guard not found')

    old_regular = "const pit=growthPitCost(costs);if(pit<=0||!growthCanAfford(costs,state)||budget.spent+pit>budget.limit)continue;"
    new_regular = "const pit=growthPitCost(costs);if(!growthGeneralCostSafe(costs)||pit<=0||!growthCanAfford(costs,state)||budget.spent+pit>budget.limit)continue;"
    if old_regular in s:
        s = s.replace(old_regular, new_regular, 1)
    elif new_regular not in s:
        raise SystemExit('General regular selector guard not found')

require(strict_hamster, 'strict hamster Caps cost guard missing')
require(strict_general, 'strict general Pit Token cost guard missing')

# Two consecutive successful responses without an actual level change stop the
# optimizer instead of letting a stale/partial response spin a long safety loop.
if 'GROWTH_NO_PROGRESS_LIMIT' not in s:
    no_progress_anchor = "  function growthBestGeneral(state,blocked,budget,mode='x1',weightValue=1){"
    if no_progress_anchor not in s:
        raise SystemExit('Growth General selector anchor missing')
    s = s.replace(no_progress_anchor, "  const GROWTH_NO_PROGRESS_LIMIT = 2;\n\n" + no_progress_anchor, 1)

if 'async function growthRunGeneralsCore' in s:
    old_general_state = "budget={limit,spent:0},blocked=new Set();let safety=0;"
    new_general_state = "budget={limit,spent:0},blocked=new Set();let safety=0,noProgress=0;"
    if old_general_state in s:
        s = s.replace(old_general_state, new_general_state, 1)
    elif new_general_state not in s:
        raise SystemExit('General no-progress state anchor missing')

    old_general_after = "const after=Number(live?.level??before),weighted="
    new_general_after = (
        "const after=Number(live?.level??before);"
        "if(after<=before){noProgress+=1;recordDiagnostic('growth-general-no-progress',{id:best.id,before,after,count:noProgress});"
        "if(noProgress>=GROWTH_NO_PROGRESS_LIMIT){blocked.add(best.id);break;}}else noProgress=0;"
        "const weighted="
    )
    if old_general_after in s:
        s = s.replace(old_general_after, new_general_after, 1)
    elif "growth-general-no-progress" not in s:
        raise SystemExit('General no-progress result anchor missing')

if 'async function growthRunLevelsCore' in s:
    old_hamster_state = "async function growthRunLevelsCore(state,budget,weightValue=1){\n    const blocked=new Set();let safety=0;"
    new_hamster_state = "async function growthRunLevelsCore(state,budget,weightValue=1){\n    const blocked=new Set();let safety=0,noProgress=0;"
    if old_hamster_state in s:
        s = s.replace(old_hamster_state, new_hamster_state, 1)
    elif new_hamster_state not in s:
        raise SystemExit('Hamster no-progress state anchor missing')

    old_hamster_after = "const after=Number(live?.level??current),actualGain="
    new_hamster_after = (
        "const after=Number(live?.level??current);"
        "if(after<=current){noProgress+=1;recordDiagnostic('growth-hamster-no-progress',{id:best.id,before:current,after,count:noProgress});"
        "if(noProgress>=GROWTH_NO_PROGRESS_LIMIT){blocked.add(best.id);break;}}else noProgress=0;"
        "const actualGain="
    )
    if old_hamster_after in s:
        s = s.replace(old_hamster_after, new_hamster_after, 1)
    elif "growth-hamster-no-progress" not in s:
        raise SystemExit('Hamster no-progress result anchor missing')

if is_1144:
    s = s.replace('// @version      1.14.4', '// @version      1.15.0', 1)
    s = s.replace(": '1.14.4';", ": '1.15.0';", 1)

    old = "  async function apiJson(path, method = 'GET', body = null, retryAuthorization = true, retryNetwork = 3) {"
    if old not in s:
        raise SystemExit('apiJson signature not found on 1.14.4 base')
    s = s.replace(
        old,
        "  async function apiJsonCore(path, method = 'GET', body = null, retryAuthorization = true, retryNetwork = 3) {",
        1
    )
else:
    require(
        "  async function apiJsonCore(path, method = 'GET', body = null, retryAuthorization = true, retryNetwork = 3) {",
        'existing 1.15.0 is not a recognized Stage 1 build'
    )

# apiJson owns auth/network/player-lock recovery. Internal recovery MUST stay inside
# the same gate turn. Re-entering public apiJson from apiJsonCore self-deadlocks.
marker = "\n  function deepObjects(value, depth = 0, output = []) {"
if marker not in s:
    raise SystemExit('deepObjects marker not found')
core_start = s.index("  async function apiJsonCore(")
core_end = s.index(marker, core_start)
core = s[core_start:core_end]
core = re.sub(r'\bapiJson\s*\(', 'apiJsonCore(', core)
if re.search(r'\bapiJson\s*\(', core):
    raise SystemExit('apiJsonCore still contains public apiJson retry calls')
s = s[:core_start] + core + s[core_end:]

gate = r'''
  const HK_MUTATION_GATE_REV = 'stage1-20260919-r4';

  const HK_READ_ONLY_POST_PATHS = new Set([
    '/player/me',
    '/player/hamster/lvlUp/view',
    '/shop/view',
    '/business/values',
    '/business_items',
    '/cities',
    '/client_config',
    '/events',
    '/items',
    '/leaderboard',
    '/premium',
    '/bonuses/view',
    '/alliance/list',
    '/clan/skill_lines/stats',
    '/player/event'
  ]);

  function hkNormalizedApiPath(path) {
    const value = String(path || '');
    const q = value.indexOf('?');
    return q >= 0 ? value.slice(0, q) : value;
  }

  function hkIsMutationRequest(path, method = 'GET') {
    const verb = String(method || 'GET').toUpperCase();
    if (verb === 'GET' || verb === 'HEAD' || verb === 'OPTIONS') return false;
    return !HK_READ_ONLY_POST_PATHS.has(hkNormalizedApiPath(path));
  }

  const hkMutationGate = (() => {
    let tail = Promise.resolve();
    let sequence = 0;
    let active = null;
    const state = {
      pending: 0,
      completed: 0,
      failed: 0,
      lastPath: '',
      activePath: ''
    };

    const safeDiagnostic = (kind, payload) => {
      try { recordDiagnostic(kind, payload); } catch (_) {}
    };

    const run = async (path, task) => {
      const id = ++sequence;
      const normalizedPath = hkNormalizedApiPath(path);
      state.pending += 1;

      let release;
      const turn = new Promise(resolve => { release = resolve; });
      const previous = tail;
      tail = turn;

      await previous.catch(() => {});
      state.pending = Math.max(0, state.pending - 1);
      state.activePath = normalizedPath;
      state.lastPath = normalizedPath;
      active = { id, path: normalizedPath, startedAt: Date.now() };
      safeDiagnostic('mutation-start', { id, path: normalizedPath, pending: state.pending });

      try {
        // Serialization is neutral: module-specific Pause/Stop stays in the
        // calling runner. A paused Growth task must not freeze unrelated modules.
        // Internal apiJsonCore retries remain inside this same queue turn.
        const value = await task();
        state.completed += 1;
        safeDiagnostic('mutation-finish', {
          id,
          path: normalizedPath,
          durationMs: Date.now() - active.startedAt
        });
        return value;
      } catch (error) {
        state.failed += 1;
        safeDiagnostic('mutation-error', {
          id,
          path: normalizedPath,
          error: error?.message || String(error)
        });
        throw error;
      } finally {
        active = null;
        state.activePath = '';
        release();
      }
    };

    return {
      revision: HK_MUTATION_GATE_REV,
      state,
      run,
      get active() { return active; }
    };
  })();

  async function apiJson(path, method = 'GET', body = null, retryAuthorization = true, retryNetwork = 3) {
    if (!hkIsMutationRequest(path, method)) {
      return apiJsonCore(path, method, body, retryAuthorization, retryNetwork);
    }
    return hkMutationGate.run(
      path,
      () => apiJsonCore(path, method, body, retryAuthorization, retryNetwork)
    );
  }
'''
gate = gate.strip('\n')
gate_block = "\n" + gate + "\n"

# Replace an older Stage 1 gate in-place, or insert it into the verified 1.14.4 base.
gate_start_token = "\n  const HK_READ_ONLY_POST_PATHS = new Set(["
rev_start_token = "\n  const HK_MUTATION_GATE_REV = "
marker_pos = s.index(marker, core_start)
# Recompute from core_start after rewriting, because replacing apiJson(...) with
# apiJsonCore(...) changes offsets in an existing 1.15.0 file.
gate_start = s.find(rev_start_token, core_start, marker_pos)
if gate_start < 0:
    gate_start = s.find(gate_start_token, core_start, marker_pos)

if gate_start >= 0:
    s = s[:gate_start] + gate_block + s[marker_pos:]
else:
    s = s[:marker_pos] + gate_block + s[marker_pos:]

runtime_marker = "  runtime.runner = hkRunner;"
if runtime_marker not in s:
    raise SystemExit('runtime runner marker not found')
if "  runtime.mutationGate = hkMutationGate;" not in s:
    s = s.replace(runtime_marker, runtime_marker + "\n  runtime.mutationGate = hkMutationGate;", 1)

# Final invariants: build must fail before deployment on any regression.
checks = [
    ("// @version      1.15.0", 'version 1.15.0 missing'),
    ("HK_MUTATION_GATE_REV = 'stage1-20260919-r4'", 'Stage 1 revision marker missing'),
    ("GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'", 'hamster budget changed away from Caps'),
    ("GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'", 'general budget changed away from Pit Tokens'),
    ('growthCostOnlyUses(cost,[GROWTH_HAMSTER_BUDGET_ID])', 'hamster strict cost guard lost'),
    ('growthCostOnlyUses(cost,[GROWTH_GENERAL_BUDGET_ID])', 'general strict cost guard lost'),
    ('const hkMutationGate', 'mutation gate missing'),
    ('const safeDiagnostic', 'non-fatal mutation diagnostics missing'),
    ('return hkMutationGate.run', 'mutation routing missing'),
    ('runtime.mutationGate = hkMutationGate', 'runtime gate diagnostics missing'),
    ('HKNetworkTimeout', 'network timeout protection lost'),
    ('GROWTH_NO_PROGRESS_LIMIT', 'Growth no-progress protection lost'),
    ('async function refreshModuleLive', 'live reread helper lost'),
    ('const hkGameBridge', 'game bridge lost'),
]
for needle, message in checks:
    if needle not in s:
        raise SystemExit(message)

# Assert again on the FINAL apiJsonCore body only. The public apiJson wrapper
# intentionally exists after the core, inside the gate block.
final_core_start = s.index("  async function apiJsonCore(")
final_gate_start = s.index("\n  const HK_MUTATION_GATE_REV = ", final_core_start)
if re.search(r'\bapiJson\s*\(', s[final_core_start:final_gate_start]):
    raise SystemExit('final apiJsonCore re-enters public apiJson and can deadlock')

p.write_text(s, encoding='utf-8')
