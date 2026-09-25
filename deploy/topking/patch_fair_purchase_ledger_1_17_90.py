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
    "// @version      1.17.89",
    "// @version      1.17.90\n"
    "// @release-note Ярмарка: добавлен live-счётчик покупок с названием и количеством купленного лота; по завершении журнал показывает полный состав покупок и расход ресурсов отдельно на покупки, прокрутки и общий итог.",
    "metadata version",
)
replace(
    "const BUILD_VERSION = '1.17.89';",
    "const BUILD_VERSION = '1.17.90';",
    "build version",
)

marker = "const HK_FAIR_REROLL_TIMEOUT_REV = 'fair-reroll-timeout-reconcile-20260925-r1';"
replace(
    marker,
    marker + "\n  const HK_FAIR_PURCHASE_LEDGER_REV = 'fair-purchase-ledger-20260925-r1';",
    "Fair purchase ledger marker",
)

anchor = "  async function executeFairPurchase(row, slot, allowPremium = false) {"
helpers = r"""  let fairRunLedger = null;

  function fairCreateRunLedger() {
    return {purchases:new Map(), purchaseCount:0, rewardUnits:0, purchaseSpend:new Map(), rerollSpend:new Map()};
  }

  function fairLedgerName(row) {
    const name=gameText(row?.name) || row?.name || row?.rewardName || row?.rewardId || row?.lotId || either('Лот','Lot');
    return String(name || either('Лот','Lot'));
  }

  function fairLedgerRewardQty(row) {
    const value=Math.trunc(Number(row?.rewardQuantity ?? row?.quantity ?? 1));
    return Number.isFinite(value) && value>0 ? value : 1;
  }

  function fairLedgerAddCost(target,cost) {
    if(!target)return;
    for(const part of costParts(cost)) {
      const amount=Math.max(0,Number(part.quantity || 0));
      if(!amount || !part.id)continue;
      target.set(part.id,(target.get(part.id)||0)+amount);
    }
  }

  function fairLedgerAddPurchase(row,slot) {
    if(!fairRunLedger)return;
    const name=fairLedgerName(row), quantity=fairLedgerRewardQty(row);
    const key=String(row?.rewardId || row?.lotId || name);
    const current=fairRunLedger.purchases.get(key) || {name,quantity:0,purchases:0};
    current.name=name;
    current.quantity+=quantity;
    current.purchases+=1;
    fairRunLedger.purchases.set(key,current);
    fairRunLedger.purchaseCount+=1;
    fairRunLedger.rewardUnits+=quantity;
    fairLedgerAddCost(fairRunLedger.purchaseSpend,row?.cost);
    fairRunnerNote(either(
      `✓ Куплено: ${name} ×${quantity.toLocaleString(locale())} · всего этого товара ×${current.quantity.toLocaleString(locale())} (${current.purchases} покупок)`,
      `✓ Purchased: ${name} ×${quantity.toLocaleString(locale())} · total ×${current.quantity.toLocaleString(locale())} (${current.purchases} purchases)`
   "),'ok');
  }

  function fairLedgerAddReroll(cost) {
    if(!fairRunLedger)return;
    fairLedgerAddCost(fairRunLedger.rerollSpend,cost);
  }

  function fairLedgerCostText(map) {
    const rows=[...(map||new Map()).entries()].filter(([,amount])=>Number(amount)>0);
    if(!rows.length)return '0';
    return rows.map(([id,amount])=>`${paymentLabel(id)} ${Number(amount).toLocaleString(locale())}`).join(' + ');
  }

  function fairLedgerTotalSpendText() {
    const total=new Map();
    if(fairRunLedger) for(const source of [fairRunLedger.purchaseSpend,fairRunLedger.rerollSpend]) {
      for(const [id,amount] of source.entries()) total.set(id,(total.get(id)||0)+Number(amount||0));
    }
    return fairLedgerCostText(total);
  }

  function fairRunSummaryText() {
    if(!fairRunLedger)return either('Покупок не зафиксировано.','No purchases recorded.');
    const products=[...fairRunLedger.purchases.values()];
    const productText=products.length
      ? products.map(item=>`${item.name} ×${item.quantity.toLocaleString(locale())} (${item.purchases} покупок)`).join('; ')
      : either('ничего','nothing');
    return either(
      `Куплено: ${productText}. Всего лотов: ${fairRunLedger.purchaseCount}, единиц товара: ${fairRunLedger.rewardUnits.toLocaleString(locale())}. Расход: покупки — ${fairLedgerCostText(fairRunLedger.purchaseSpend)}; прокрутки — ${fairLedgerCostText(fairRunLedger.rerollSpend)}; всего — ${fairLedgerTotalSpendText()}.`,
      `Purchased: ${productText}. Total lots: ${fairRunLedger.purchaseCount}, reward units: ${fairRunLedger.rewardUnits.toLocaleString(locale())}. Spend: purchases — ${fairLedgerCostText(fairRunLedger.purchaseSpend)}; rerolls — ${fairLedgerCostText(fairRunLedger.rerollSpend)}; total — ${fairLedgerTotalSpendText()}.`
    );
  }

  async function executeFairPurchase(row, slot, allowPremium = false) {"""
replace(anchor, helpers, "Fair purchase ledger helpers")

purchase_tail = """    for (const part of costParts(row.cost)) appendExpense({section:'fair', lotId:row.lotId, name:gameText(row.name) || row.name,
      currencyId:part.id, amount:part.quantity, balanceBefore:before.get(part.id), balanceAfter:walletAmount(part.id, playerDocument), status:'ok', result:'purchased'});
  }"""
purchase_tail_new = """    for (const part of costParts(row.cost)) appendExpense({section:'fair', lotId:row.lotId, name:gameText(row.name) || row.name,
      currencyId:part.id, amount:part.quantity, balanceBefore:before.get(part.id), balanceAfter:walletAmount(part.id, playerDocument), status:'ok', result:'purchased'});
    fairLedgerAddPurchase(row,slot);
  }"""
replace(purchase_tail, purchase_tail_new, "Fair purchase receipt hook")

replace(
    "    hkRunner.start({title:either('Ярмарка','Fair'),total:buyLimit,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});",
    "    fairRunLedger=fairCreateRunLedger();\n    hkRunner.start({title:either('Ярмарка','Fair'),total:buyLimit,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});",
    "Fair ledger initialization",
)

old_generic = "              fairRunnerNote(`Лоты ${purchaseTargets.length}: покупка…`);"
new_generic = """              fairRunnerNote(either(
                `Покупка: ${fairLedgerName(row)} ×${fairLedgerRewardQty(row).toLocaleString(locale())}…`,
                `Buying: ${fairLedgerName(row)} ×${fairLedgerRewardQty(row).toLocaleString(locale())}…`
              ));"""
if old_generic in s:
    s=s.replace(old_generic,new_generic,1)
elif "Покупка: ${fairLedgerName(row)}" not in s:
    raise SystemExit("Fair purchase pre-note anchor missing")

normal_reroll = "          rerolls++; authRetries = 0;"
normal_reroll_new = "          fairLedgerAddReroll(rerollCost);\n          rerolls++; authRetries = 0;"
if s.count(normal_reroll) < 1:
    raise SystemExit("Fair normal reroll counter anchor missing")
s=s.replace(normal_reroll,normal_reroll_new,1)

timeout_receipt = "              rerolls++; authRetries = 0;\n              fairRunnerNote(either('Прокрутка подтверждена по live-состоянию. Продолжаю.','Reroll confirmed from live state. Continuing.'),'ok');"
timeout_receipt_new = "              fairLedgerAddReroll(rerollCost);\n              rerolls++; authRetries = 0;\n              fairRunnerNote(either('Прокрутка подтверждена по live-состоянию. Продолжаю.','Reroll confirmed from live state. Continuing.'),'ok');"
if timeout_receipt in s:
    s=s.replace(timeout_receipt,timeout_receipt_new,1)
elif "rerolled-timeout-reconciled" in s and s.count("fairLedgerAddReroll(rerollCost);") < 2:
    raise SystemExit("Fair timeout reroll ledger anchor missing")

ru_old = "прокруток ${rerolls}`"
ru_new = "прокруток ${rerolls}. ${fairRunSummaryText()}`"
en_old = "rerolls ${rerolls}`"
en_new = "rerolls ${rerolls}. ${fairRunSummaryText()}`"
ru_count=s.count(ru_old)
en_count=s.count(en_old)
if ru_count < 4 or en_count < 4:
    raise SystemExit(f"Fair final summary anchors missing: ru={ru_count}, en={en_count}")
s=s.replace(ru_old,ru_new)
s=s.replace(en_old,en_new)

replace(
    "    } finally { fairRunning = false; fairStop = false; renderFair(); }",
    "    } finally { fairRunning = false; fairStop = false; renderFair(); fairRunLedger = null; }",
    "Fair ledger cleanup",
)

for marker in [
    "// @version      1.17.90",
    "const BUILD_VERSION = '1.17.90';",
    "fair-purchase-ledger-20260925-r1",
    "function fairLedgerAddPurchase(row,slot)",
    "✓ Куплено:",
    "Покупка: ${fairLedgerName(row)}",
    "Расход: покупки —",
    "fairLedgerAddReroll(rerollCost);",
    "${fairRunSummaryText()}",
]:
    if marker not in s:
        raise SystemExit("missing marker: " + marker)

target.write_text(s, encoding="utf-8")
print("FAIR_PURCHASE_LEDGER_1_17_90=PASS")
print("version=1.17.90")
