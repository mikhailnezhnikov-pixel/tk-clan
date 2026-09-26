from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count:
        raise SystemExit(f"{label}: expected {count} got {n}")
    s=s.replace(old,new,count)

rep("// @version      1.18.24",
    "// @version      1.18.25\n// @release-note Торговец: жёсткий whitelist — покупать только монеты сокровищ (random4coins), ягоды (food_*) и карты сокровищ (map). Ключи, яйца, HK-монеты и прочие лоты игнорируются. Рыбалка: каждая цель проходит живую проверку остатка валюты перед выбором и перед подтверждением; недоступные по балансу клетки не нажимаются, после исчерпания очков Автокарта штатно выходит.",
    "version")
rep("const BUILD_VERSION = '1.18.24';",
    "const BUILD_VERSION = '1.18.25';",
    "build")
rep("  const HK_TREASURE_AUTO_MAP_STALE_RUNNER_REV='treasure-auto-map-stale-runner-20260927-r2';",
    "  const HK_TREASURE_AUTO_MAP_STALE_RUNNER_REV='treasure-auto-map-stale-runner-20260927-r2';\n  const HK_TRADER_WHITELIST_REV='trader-approved-lots-20260927-r1';\n  const HK_FISHING_BUDGET_REV='fishing-live-budget-20260927-r1';",
    "revisions")

# Fishing: infer the actual game currency from live catalog, then require a known
# live balance before a tile can become a target.
old_tile="""    function fishingTileCost(row) {
      const catalogRow=fairCatalog.find(item=>String(item?.lotId||'')===row.lotId);
      const parts=costParts(catalogRow?.cost).filter(part=>part.quantity>0);
      if (parts.length===1) return {id:parts[0].id,quantity:parts[0].quantity};

      const text=clean(row.element?.innerText||row.element?.textContent||'');
      const nums=[...text.matchAll(/(?:^|\s)(\d{1,2})(?=\s|$)/g)]
        .map(match=>Number(match[1]))
        .filter(value=>value>=1 && value<=9);
      const quantity=nums.length ? nums[nums.length-1] : fishingCanonicalCost(row.lotId);
      return {id:'',quantity};
    }
"""
new_tile="""    function fishingCurrencyId() {
      for (const item of fairCatalog) {
        if (!String(item?.lotId||'').includes('mf_treasurelot_is_fishing_')) continue;
        const parts=costParts(item?.cost).filter(part=>part.quantity>0);
        if (parts.length===1 && parts[0].id) return String(parts[0].id);
      }
      return '';
    }

    function fishingTileCost(row) {
      const catalogRow=fairCatalog.find(item=>String(item?.lotId||'')===row.lotId);
      const parts=costParts(catalogRow?.cost).filter(part=>part.quantity>0);
      if (parts.length===1) return {id:parts[0].id,quantity:parts[0].quantity};

      const text=clean(row.element?.innerText||row.element?.textContent||'');
      const nums=[...text.matchAll(/(?:^|\s)(\d{1,2})(?=\s|$)/g)]
        .map(match=>Number(match[1]))
        .filter(value=>value>=1 && value<=9);
      const quantity=nums.length ? nums[nums.length-1] : fishingCanonicalCost(row.lotId);
      return {id:fishingCurrencyId(),quantity};
    }

    function fishingAffordable(cost) {
      const quantity=Math.max(0,Number(cost?.quantity||0));
      const id=String(cost?.id||'');
      if (!(quantity>0) || !id) return false;
      const amount=walletAmount(id);
      return amount!==null && Number(amount)>=quantity;
    }

    function fishingBudgetSnapshot(cost) {
      const id=String(cost?.id||'');
      const amount=id ? walletAmount(id) : null;
      return {
        id,
        balance:amount===null ? null : Number(amount),
        cost:Math.max(0,Number(cost?.quantity||0))
      };
    }
"""
rep(old_tile,new_tile,"fishing cost and budget")

old_target="""      const rows=source.filter(row=>!row.activated).map(row=>{
        const cost=fishingTileCost(row);
        const tier=fishingValueTier(row.lotId,hasCurseTrigger);
        const roi=tier/Math.max(1,cost.quantity||1);
        return {...row,cost,tier,roi};
      }).filter(row=>row.tier>0);
"""
new_target="""      const rows=source.filter(row=>!row.activated).map(row=>{
        const cost=fishingTileCost(row);
        const tier=fishingValueTier(row.lotId,hasCurseTrigger);
        const roi=tier/Math.max(1,cost.quantity||1);
        return {...row,cost,tier,roi};
      }).filter(row=>row.tier>0 && fishingAffordable(row.cost));
"""
rep(old_target,new_target,"fishing target affordability")

rep("""      const target=fishingTarget();
      if (!target) return false;

      await waitMutationGap(fishingLastMutationAt,FISHING_MIN_NEXT_ACTION_GAP_MS);
      if (!fishingAutoEnabled()) return false;
""",
"""      const target=fishingTarget();
      if (!target) {
        recordDiagnostic('fishing-auto-budget-empty',{
          revision:HK_FISHING_BUDGET_REV,
          candidates:fishingElements().filter(row=>!row.activated).length
        });
        return false;
      }

      await waitMutationGap(fishingLastMutationAt,FISHING_MIN_NEXT_ACTION_GAP_MS);
      if (!fishingAutoEnabled()) return false;
      if (!fishingAffordable(target.cost)) {
        recordDiagnostic('fishing-auto-budget-changed',{
          revision:HK_FISHING_BUDGET_REV,
          lotId:target.lotId,
          ...fishingBudgetSnapshot(target.cost)
        });
        lastSignature='';
        setTimeout(checkPuzzle,80);
        return false;
      }
""",
"fishing pre-action budget recheck")

rep("""        const action=await (async()=>{
          const started=Date.now();
          while (Date.now()-started<1800) {
            if (runId!==fishingAutoRunId || !fishingAutoEnabled()) return null;
            const button=treasureActionButton(modal,target.cost);
            if (button) return button;
            await new Promise(resolve=>setTimeout(resolve,80));
          }
          return null;
        })();

        if (!action || !dispatchAutoMapTap(action,'fishing-confirm-'+target.lotId)) {
""",
"""        const action=await (async()=>{
          const started=Date.now();
          while (Date.now()-started<1800) {
            if (runId!==fishingAutoRunId || !fishingAutoEnabled()) return null;
            if (!fishingAffordable(target.cost)) return null;
            const button=treasureActionButton(modal,target.cost);
            if (button) return button;
            await new Promise(resolve=>setTimeout(resolve,80));
          }
          return null;
        })();

        if (!fishingAffordable(target.cost)) {
          const close=[...modal.querySelectorAll('button,[role="button"],a,div,span')]
            .filter(el=>el && !el.disabled && visible(el))
            .find(el=>/^(?:×|✕|Назад|Back|Закрыть|Close)$/i.test(clean(el.innerText||el.textContent||'').trim()));
          if (close) dispatchAutoMapTap(close,'fishing-insufficient-close');
          recordDiagnostic('fishing-auto-insufficient-before-confirm',{
            revision:HK_FISHING_BUDGET_REV,
            lotId:target.lotId,
            ...fishingBudgetSnapshot(target.cost)
          });
          return false;
        }

        if (!action || !dispatchAutoMapTap(action,'fishing-confirm-'+target.lotId)) {
""",
"fishing confirm budget recheck")

# Trader: explicit allow-list based on the actual lot-id families observed in the
# game. Do not use generic "coins" matching because key_uncommon4coins is a KEY.
anchor="""    function traderValueTier(lotId) {
"""
if s.count(anchor)!=1:
    raise SystemExit("trader tier anchor missing")
helper="""    function traderApprovedLot(lotId) {
      const id=String(lotId||'').toLowerCase();
      if (!id) return false;

      // Treasure coins. "4coins" alone is NOT enough: key_uncommon4coins is a key.
      if (/random4coins/.test(id) || /treasure[_-]?coins/.test(id)) return true;

      // Berries/food lots.
      if (/(?:^|_)food(?:_|$)/.test(id) || /berr(?:y|ies)/.test(id)) return true;

      // Treasure maps.
      if (/(?:^|_)map(?:_|$)/.test(id) || /treasure[_-]?map/.test(id)) return true;

      return false;
    }

"""
s=s.replace(anchor,helper+anchor,1)

rep("""      const rows=traderElements()
        .filter(row=>!row.activated)
        .map(row=>{
""",
"""      const rows=traderElements()
        .filter(row=>!row.activated)
        .filter(row=>traderApprovedLot(row.lotId))
        .map(row=>{
""",
"trader whitelist")

rep("""      if (!target) {
        recordDiagnostic('trader-auto-complete',{
          revision:HK_TRADER_AUTO_REV,
          purchases:traderSessionPurchases,
          reason:'no-affordable-lots'
        });
        return false;
      }
""",
"""      if (!target) {
        const visible=traderElements().filter(row=>!row.activated);
        recordDiagnostic('trader-auto-complete',{
          revision:HK_TRADER_WHITELIST_REV,
          purchases:traderSessionPurchases,
          reason:'no-approved-affordable-lots',
          skipped:visible.filter(row=>!traderApprovedLot(row.lotId)).map(row=>row.lotId).slice(0,24)
        });
        return false;
      }
""",
"trader no target diagnostic")

rep("      treasureAutoMapStaleRunnerRevision:HK_TREASURE_AUTO_MAP_STALE_RUNNER_REV,\n      start,",
    "      treasureAutoMapStaleRunnerRevision:HK_TREASURE_AUTO_MAP_STALE_RUNNER_REV,\n      traderWhitelistRevision:HK_TRADER_WHITELIST_REV,\n      fishingBudgetRevision:HK_FISHING_BUDGET_REV,\n      start,",
    "export revisions")

for marker in [
    "// @version      1.18.25",
    "const BUILD_VERSION = '1.18.25';",
    "trader-approved-lots-20260927-r1",
    "fishing-live-budget-20260927-r1",
    "function traderApprovedLot(lotId)",
    "random4coins",
    ".filter(row=>traderApprovedLot(row.lotId))",
    "function fishingAffordable(cost)",
    ".filter(row=>row.tier>0 && fishingAffordable(row.cost))",
    "fishing-auto-insufficient-before-confirm",
    "treasure-auto-map-stale-runner-20260927-r2"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("TRADER_WHITELIST_FISHING_BUDGET_1_18_25=PASS")
