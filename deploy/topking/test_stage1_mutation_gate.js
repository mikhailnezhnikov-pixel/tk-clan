'use strict';

const assert = require('node:assert/strict');

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

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

function createMutationGate(recordDiagnostic) {
  let tail = Promise.resolve();
  let sequence = 0;
  const safeDiagnostic = (kind, payload) => {
    try { recordDiagnostic(kind, payload); } catch (_) {}
  };
  return {
    async run(path, task) {
      const id = ++sequence;
      let release;
      const turn = new Promise(resolve => { release = resolve; });
      const previous = tail;
      tail = turn;
      await previous.catch(() => {});
      safeDiagnostic('mutation-start', {id, path});
      try {
        const value = await task();
        safeDiagnostic('mutation-finish', {id, path});
        return value;
      } catch (error) {
        safeDiagnostic('mutation-error', {id, path, error:error?.message || String(error)});
        throw error;
      } finally {
        release();
      }
    }
  };
}

async function main() {
  assert.equal(hkIsMutationRequest('/player/hamster/lvlUp/view', 'POST'), false);
  assert.equal(hkIsMutationRequest('/player/hamster/lvlUp', 'POST'), true);
  assert.equal(hkIsMutationRequest('/shop/buy', 'POST'), true);
  assert.equal(hkIsMutationRequest('/player/me?fresh=1', 'POST'), false);
  assert.equal(hkIsMutationRequest('/player/me', 'GET'), false);

  const events = [];
  let throwDiagnostic = true;
  const gate = createMutationGate((kind, payload) => {
    events.push('diag:' + kind + ':' + payload.path);
    if (throwDiagnostic) {
      throwDiagnostic = false;
      throw new Error('simulated diagnostic failure');
    }
  });

  let retryCount = 0;
  async function apiJsonCore(path, method = 'GET') {
    if (path === '/mutation/retry') {
      events.push('core:retry:' + retryCount);
      if (retryCount++ === 0) {
        await sleep(5);
        // Critical invariant: internal recovery stays inside the current gate turn.
        return apiJsonCore(path, method);
      }
      return {ok:true};
    }
    if (path === '/mutation/slow') {
      events.push('core:slow:start');
      await sleep(20);
      events.push('core:slow:end');
      return {ok:true};
    }
    events.push('core:' + path);
    return {ok:true};
  }

  async function apiJson(path, method = 'GET') {
    if (!hkIsMutationRequest(path, method)) return apiJsonCore(path, method);
    return gate.run(path, () => apiJsonCore(path, method));
  }

  const run = Promise.all([
    apiJson('/mutation/retry', 'POST'),
    apiJson('/mutation/slow', 'POST'),
    apiJson('/player/me', 'POST')
  ]);

  await Promise.race([
    run,
    new Promise((_, reject) => setTimeout(() => reject(new Error('mutation gate deadlocked')), 1000))
  ]);

  assert.equal(retryCount, 2, 'internal retry must execute exactly once');
  const retryFinish = events.indexOf('diag:mutation-finish:/mutation/retry');
  const slowStart = events.indexOf('core:slow:start');
  assert.ok(retryFinish >= 0 && slowStart > retryFinish, 'mutations must be FIFO');

  // A diagnostic exception on the first task must not strand the queue.
  const after = await Promise.race([
    apiJson('/mutation/after-diagnostic-error', 'POST'),
    new Promise((_, reject) => setTimeout(() => reject(new Error('queue stranded after diagnostic error')), 1000))
  ]);
  assert.equal(after.ok, true);

  process.stdout.write('STAGE1_MUTATION_GATE_TEST_OK\n');
}

main().catch(error => {
  console.error(error);
  process.exit(1);
});
