from pathlib import Path
import sys

target = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/HamsterKingMobile.user.js")
s = target.read_text(encoding="utf-8")

def need(old, label, count=1):
    actual = s.count(old)
    if actual != count:
        raise SystemExit(f"{label}: expected {count}, got {actual}")

def replace(old, new, label, count=1):
    global s
    need(old, label, count)
    s = s.replace(old, new, count)

replace(
    "// @version      1.17.88",
    "// @version      1.17.89\n"
    "// @release-note Ярмарка: прокрутка больше не падает сразу при сетевом тайм-ауте. Для /fair/reroll увеличено окно ожидания, а неоднозначный тайм-аут сверяется с live-состоянием Ярмарки и балансом; если прокрутка уже прошла — работа продолжается без повторной траты, если нет — повтор выполняется только после подтверждения неизменившегося состояния.",
    "metadata version",
)
replace(
    "const BUILD_VERSION = '1.17.88';",
    "const BUILD_VERSION = '1.17.89';",
    "build version",
)

marker = "const HK_FAIR_RUNNER_CANON_REV = 'fair-runner-canon-20260925-r1';"
replace(
    marker,
    marker + "\n  const HK_FAIR_REROLL_TIMEOUT_REV = 'fair-reroll-timeout-reconcile-20260925-r1';",
    "Fair reroll timeout marker",
)

api_sig = "  async function apiJsonCore(path, method = 'GET', body = null, retryAuthorization = true, retryNetwork = 3, timeoutMs = 18000) {"
replace(
    api_sig,
    api_sig + "\n    if (hkNormalizedApiPath(path) === '/fair/reroll' && timeoutMs === 18000) timeoutMs = 35000;",
    "Fair reroll timeout window",
)

helper_anchor = "  function fairRunnerNote(message,type='') { hkRunner.note(message,type); }\n\n  async function runFair() {"
helpers = r"""  function fairRunnerNote(message,type='') { hkRunner.note(message,type); }

  function fairRerollStateSignature(state) {
    return JSON.stringify((state?.fair_slots || []).map((slot,index) => [
      index,
      String(slot?.id ?? ''),
      String(slot?.shop_lot_id ?? ''),
      slot?.is_bought === true ? 1 : 0
    ]));
  }

  function fairRerollTimeoutError(error) {
    const message=String(error?.message || error || '');
    return /\/fair\/reroll/i.test(message) && /(тайм-аут|timeout|timed out|время ожидания)/i.test(message);
  }

  async function reconcileFairRerollTimeout(beforeSignature,beforeBalances,rerollCost) {
    let lastDocument=playerDocument;
    for (const delay of [1200,2500,5000]) {
      await gameRetryDelay(delay);
      try {
        const documentValue=await hkAuthoritativePlayerRead('fair-reroll-timeout-reconcile');
        lastDocument=documentValue || lastDocument;
        fairDocument=lastDocument;
        const currentState=fairState(selectedFairId,lastDocument);
        if (!currentState) continue;
        const stateChanged=fairRerollStateSignature(currentState)!==beforeSignature;
        const charged=costParts(rerollCost).some(part => {
          const before=beforeBalances.get(part.id);
          const after=walletAmount(part.id,lastDocument);
          return before!==null && before!==undefined && after!==null && after!==undefined &&
            Number(after) <= Number(before) - Math.max(0,Number(part.quantity || 0));
        });
        if (stateChanged || charged) return {applied:true,documentValue:lastDocument,state:currentState};
      } catch (probeError) {
        recordDiagnostic('fair-reroll-timeout-probe-error',{error:probeError?.message || String(probeError)});
      }
    }
    return {applied:false,documentValue:lastDocument,state:fairState(selectedFairId,lastDocument)};
  }

  async function runFair() {"""
replace(helper_anchor, helpers, "Fair reroll timeout helpers")

old_block = r"""        try {
          if (!isEventFairState(state)) {
            const rerollDecision = budgetDecision(state.fair_reroll_cost, 'fair', 1, playerDocument, {allowPremiumOverride:allowPremium});
            if (!rerollDecision.allowed) throw new Error(rerollDecision.problems.join('; '));
          }
          const before = new Map(costParts(state.fair_reroll_cost).map(part => [part.id, walletAmount(part.id, playerDocument)]));
          const rerollCost = state.fair_reroll_cost;
          fairDocument = await apiJson('/fair/reroll', 'POST', {fair_id:selectedFairId});
          updateWalletFromResponse(fairDocument, rerollCost);
          for (const part of costParts(state.fair_reroll_cost)) appendExpense({section:'fair', lotId:`reroll:${selectedFairId}`, name:either('Прокрутка ярмарки','Fair reroll'),
            currencyId:part.id, amount:part.quantity, balanceBefore:before.get(part.id), balanceAfter:walletAmount(part.id, playerDocument), status:'ok', result:'rerolled'});
          rerolls++; authRetries = 0;
        }
        catch (error) {
          if (/HTTP 401|unauthorized/i.test(error.message) && authRetries++ < 2) { playerDocument = await apiJson('/player/me', 'POST'); fairDocument = playerDocument; continue; }
          throw error;
        }"""
new_block = r"""        if (!isEventFairState(state)) {
          const rerollDecision = budgetDecision(state.fair_reroll_cost, 'fair', 1, playerDocument, {allowPremiumOverride:allowPremium});
          if (!rerollDecision.allowed) throw new Error(rerollDecision.problems.join('; '));
        }
        const rerollCost = state.fair_reroll_cost;
        const before = new Map(costParts(rerollCost).map(part => [part.id, walletAmount(part.id, playerDocument)]));
        const beforeSignature = fairRerollStateSignature(state);
        try {
          fairDocument = await apiJson('/fair/reroll', 'POST', {fair_id:selectedFairId});
          updateWalletFromResponse(fairDocument, rerollCost);
          for (const part of costParts(rerollCost)) appendExpense({section:'fair', lotId:`reroll:${selectedFairId}`, name:either('Прокрутка ярмарки','Fair reroll'),
            currencyId:part.id, amount:part.quantity, balanceBefore:before.get(part.id), balanceAfter:walletAmount(part.id, playerDocument), status:'ok', result:'rerolled'});
          rerolls++; authRetries = 0;
        }
        catch (error) {
          if (/HTTP 401|unauthorized/i.test(error.message) && authRetries++ < 2) { playerDocument = await apiJson('/player/me', 'POST'); fairDocument = playerDocument; continue; }
          if (fairRerollTimeoutError(error)) {
            fairRunnerNote(either('Прокрутка отвечает дольше обычного. Проверяю состояние без повторной траты…','Reroll is taking longer than usual. Verifying state without spending twice…'),'warn');
            const reconciled=await reconcileFairRerollTimeout(beforeSignature,before,rerollCost);
            playerDocument=reconciled.documentValue || playerDocument;
            fairDocument=playerDocument;
            if (reconciled.applied) {
              for (const part of costParts(rerollCost)) appendExpense({section:'fair', lotId:`reroll:${selectedFairId}`, name:either('Прокрутка ярмарки','Fair reroll'),
                currencyId:part.id, amount:part.quantity, balanceBefore:before.get(part.id), balanceAfter:walletAmount(part.id, playerDocument), status:'ok', result:'rerolled-timeout-reconciled'});
              rerolls++; authRetries = 0;
              fairRunnerNote(either('Прокрутка подтверждена по live-состоянию. Продолжаю.','Reroll confirmed from live state. Continuing.'),'ok');
            } else {
              authRetries = 0;
              fairRunnerNote(either('После тайм-аута Ярмарка и баланс не изменились. Повторяю прокрутку безопасно.','After the timeout the Fair and balance are unchanged. Retrying the reroll safely.'),'warn');
              continue;
            }
          } else {
            throw error;
          }
        }"""
replace(old_block, new_block, "Fair reroll timeout reconciliation block")

for marker in [
    "// @version      1.17.89",
    "const BUILD_VERSION = '1.17.89';",
    "fair-reroll-timeout-reconcile-20260925-r1",
    "timeoutMs = 35000",
    "function fairRerollStateSignature(state)",
    "function fairRerollTimeoutError(error)",
    "async function reconcileFairRerollTimeout",
    "rerolled-timeout-reconciled",
    "Повторяю прокрутку безопасно",
]:
    if marker not in s:
        raise SystemExit("missing marker: " + marker)

# Mutation safety stays intact: /fair/reroll itself is never blindly retried
# inside apiJsonCore; reconciliation happens only in the Fair runner.
if "() => apiJsonCore(path, method, body, retryAuthorization, 0)" not in s:
    raise SystemExit("mutation network-retry safety invariant missing")

target.write_text(s, encoding="utf-8")
print("FAIR_REROLL_TIMEOUT_1_17_89=PASS")
print("version=1.17.89")
