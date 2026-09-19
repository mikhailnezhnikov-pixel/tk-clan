from pathlib import Path

p = Path('/tmp/HamsterKingMobile.user.js')
s = p.read_text(encoding='utf-8')

def require(needle, message):
    if needle not in s:
        raise SystemExit(message)

# Stage 1 must only ever be built from the verified 1.14.4 live base.
require('// @version      1.14.4', 'expected live base 1.14.4')
require("GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'", 'hamster budget must be cur_cap before Stage 1')
require("GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'", 'general budget must be item_pit_token before Stage 1')
require('growthCostOnlyUses(cost,[GROWTH_HAMSTER_BUDGET_ID])', 'strict hamster Caps cost guard missing')
require('growthCostOnlyUses(cost,[GROWTH_GENERAL_BUDGET_ID])', 'strict general Pit Token cost guard missing')
require('HKNetworkTimeout', 'network timeout protection missing')
require('GROWTH_NO_PROGRESS_LIMIT', 'Growth no-progress protection missing')

s = s.replace('// @version      1.14.4', '// @version      1.15.0', 1)
s = s.replace(": '1.14.4';", ": '1.15.0';", 1)

old = "  async function apiJson(path, method = 'GET', body = null, retryAuthorization = true, retryNetwork = 3) {"
if old not in s:
    raise SystemExit('apiJson signature not found')
s = s.replace(old, "  async function apiJsonCore(path, method = 'GET', body = null, retryAuthorization = true, retryNetwork = 3) {", 1)

# IMPORTANT: apiJson has internal retry/recovery calls. Once the outer function is
# placed behind the global mutation queue, those retries must stay inside the same
# queue turn. Calling the public apiJson wrapper from apiJsonCore would enqueue the
# retry behind itself and deadlock forever.
marker = "\n  function deepObjects(value, depth = 0, output = []) {"
if marker not in s:
    raise SystemExit('deepObjects marker not found')
core_start = s.index("  async function apiJsonCore(")
core_end = s.index(marker, core_start)
core = s[core_start:core_end]
core = core.replace('apiJson(', 'apiJsonCore(')
if 'apiJson(' in core:
    raise SystemExit('apiJsonCore still contains public apiJson retry calls')
s = s[:core_start] + core + s[core_end:]

gate = r'''
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
      recordDiagnostic('mutation-start', { id, path: normalizedPath, pending: state.pending });

      try {
        // Pause only before starting a new mutation. Internal apiJsonCore retries
        // never re-enter this gate and therefore cannot deadlock behind themselves.
        if (hkRunner.running) await hkRunner.waitIfPaused();
        const value = await task();
        state.completed += 1;
        recordDiagnostic('mutation-finish', {
          id,
          path: normalizedPath,
          durationMs: Date.now() - active.startedAt
        });
        return value;
      } catch (error) {
        state.failed += 1;
        recordDiagnostic('mutation-error', {
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

s = s.replace(marker, "\n" + gate + marker, 1)

runtime_marker = "  runtime.runner = hkRunner;"
if runtime_marker not in s:
    raise SystemExit('runtime runner marker not found')
s = s.replace(runtime_marker, runtime_marker + "\n  runtime.mutationGate = hkMutationGate;", 1)

# Final invariants: currency routing and anti-hang protections must survive patching.
checks = [
    ("// @version      1.15.0", 'version 1.15.0 missing'),
    ("GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'", 'hamster budget changed away from Caps'),
    ("GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'", 'general budget changed away from Pit Tokens'),
    ('growthCostOnlyUses(cost,[GROWTH_HAMSTER_BUDGET_ID])', 'hamster strict cost guard lost'),
    ('growthCostOnlyUses(cost,[GROWTH_GENERAL_BUDGET_ID])', 'general strict cost guard lost'),
    ('const hkMutationGate', 'mutation gate missing'),
    ('return hkMutationGate.run', 'mutation routing missing'),
    ('runtime.mutationGate = hkMutationGate', 'runtime gate diagnostics missing'),
    ('HKNetworkTimeout', 'network timeout protection lost'),
    ('GROWTH_NO_PROGRESS_LIMIT', 'Growth no-progress protection lost'),
]
for needle, message in checks:
    if needle not in s:
        raise SystemExit(message)

p.write_text(s, encoding='utf-8')
