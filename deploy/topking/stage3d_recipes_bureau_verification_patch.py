from pathlib import Path

TARGET=Path('/tmp/HamsterKingMobile.user.js')
s=TARGET.read_text(encoding='utf-8')
REV='stage3d-recipes-bureau-verify-20260920-r1'

def require(needle,message):
    if needle not in s:
        raise SystemExit(message)

if '// @version      1.16.11' not in s and '// @version      1.16.12' not in s:
    raise SystemExit('Stage 3D requires Stage 3C 1.16.11 or existing 1.16.12')
require("HK_STAGE3C_FAIR_SHOP_REV = 'stage3c-fair-shop-verify-20260920-r1'",'Stage 3C marker missing')

if f"HK_STAGE3D_RECIPES_BUREAU_REV = '{REV}'" not in s:
    s=s.replace('// @version      1.16.11','// @version      1.16.12',1)
    s=s.replace(": '1.16.11';",": '1.16.12';",1)
    marker="  const HK_STAGE3C_FAIR_SHOP_REV = 'stage3c-fair-shop-verify-20260920-r1';"
    require(marker,'Stage 3C marker anchor missing')
    s=s.replace(marker,marker+f"\n  const HK_STAGE3D_RECIPES_BUREAU_REV = '{REV}';",1)
    runtime='  runtime.fairShopVerificationStage = HK_STAGE3C_FAIR_SHOP_REV;'
    require(runtime,'Stage 3C runtime anchor missing')
    s=s.replace(runtime,runtime+"\n  runtime.recipesBureauVerificationStage = HK_STAGE3D_RECIPES_BUREAU_REV;",1)

# Recipes: refresh live state before confirmation.
old="""    const attempts = Math.max(1, Math.min(100, Math.trunc(Number(root.querySelector('#hk-recipe-attempts').value || 1))));
    let state = recipeState();
    if (!safeReroll(state.fair_reroll_cost, false))"""
new="""    const attempts = Math.max(1, Math.min(100, Math.trunc(Number(root.querySelector('#hk-recipe-attempts').value || 1))));
    let state;
    try {
      playerDocument = await apiJson('/player/me', 'POST');
      fairDocument = playerDocument;
      state = recipeState();
    } catch (error) {
      log(either('Не удалось обновить каталог перед прокруткой','Could not refresh the catalog before rerolling') + ': ' + (error?.message || error),'bad');
      return;
    }
    if (!state) { log(either('Каталог бизнес-планов недоступен','Business-plan catalog is unavailable'),'warn'); return; }
    if (!safeReroll(state.fair_reroll_cost, false))"""
if old in s:
    s=s.replace(old,new,1)
elif "Could not refresh the catalog before rerolling" not in s:
    raise SystemExit('Recipes preflight refresh anchor missing')

# Recipes: re-check current reroll cost before every irreversible reroll and journal it.
old="""        log(either(`Прокрутка каталога ${index + 1}/${attempts}…`, `Catalog reroll ${index + 1}/${attempts}…`));
        fairDocument = await apiJson('/fair/reroll', 'POST', {fair_id:recipeFairId});
        state = recipeState(fairDocument);"""
new="""        log(either(`Прокрутка каталога ${index + 1}/${attempts}…`, `Catalog reroll ${index + 1}/${attempts}…`));
        state = recipeState(fairDocument || playerDocument);
        if (!state) throw new Error(either('Каталог бизнес-планов больше недоступен','Business-plan catalog is no longer available'));
        if (!safeReroll(state.fair_reroll_cost, false)) throw new Error(either('Цена прокрутки изменилась и стала небезопасной','Reroll cost changed and became unsafe'));
        const recipeDecision = budgetDecision(state.fair_reroll_cost, 'recipes', 1, playerDocument);
        if (!recipeDecision.allowed) throw new Error(recipeDecision.problems.join('; '));
        const recipeCost = state.fair_reroll_cost;
        const recipeBefore = new Map(costParts(recipeCost).map(part => [part.id, walletAmount(part.id, playerDocument)]));
        fairDocument = await apiJson('/fair/reroll', 'POST', {fair_id:recipeFairId});
        updateWalletFromResponse(fairDocument, recipeCost);
        for (const part of costParts(recipeCost)) appendExpense({section:'recipes', lotId:`recipe-reroll:${recipeFairId}`, name:either('Прокрутка каталога рецептов','Recipe catalog reroll'), currencyId:part.id, amount:part.quantity, balanceBefore:recipeBefore.get(part.id), balanceAfter:walletAmount(part.id, playerDocument), status:'ok', result:'rerolled'});
        state = recipeState(fairDocument);"""
if old in s:
    s=s.replace(old,new,1)
elif "const recipeDecision = budgetDecision" not in s:
    raise SystemExit('Recipes per-reroll safety anchor missing')

# Project Bureau read must always use a fresh inventory.
old="      if (!playerDocument) playerDocument = await apiJson('/player/me', 'POST');"
new="      playerDocument = await apiJson('/player/me', 'POST');"
if old in s:
    s=s.replace(old,new,1)
elif new not in s:
    raise SystemExit('Bureau fresh inventory anchor missing')

# If recipe costs cannot be read, keep browsing available but fail closed on Craft.
old="        bureauCosts = [{itemsCount:2,cost:{}},{itemsCount:3,cost:{}}];"
new="        bureauCosts = [];"
if old in s:
    s=s.replace(old,new,1)
elif new not in s:
    raise SystemExit('Bureau unknown-cost fallback anchor missing')

old="    const run = root?.querySelector('#hk-bureau-run'); if (run) run.disabled = bureauRunning || selectedCount !== bureauSize;"
new="    const run = root?.querySelector('#hk-bureau-run'); if (run) run.disabled = bureauRunning || selectedCount !== bureauSize || !costParts(bureauCost()).length;"
if old in s:
    s=s.replace(old,new,1)
elif new not in s:
    raise SystemExit('Bureau run fail-closed anchor missing')

# Bureau: refresh inventory and live cost before stock validation/confirmation.
old="""    const attempts = Math.max(1, Math.min(100, Math.trunc(Number(root.querySelector('#hk-bureau-attempts').value || 1))));
    const available = new Map(bureauInventory.map(row => [row.businessId,row.quantity]));"""
new="""    const attempts = Math.max(1, Math.min(100, Math.trunc(Number(root.querySelector('#hk-bureau-attempts').value || 1))));
    try {
      playerDocument = await apiJson('/player/me', 'POST');
      bureauInventory = normalizeInventory(playerDocument);
      const values = await apiJson('/business/values', 'GET');
      bureauCosts = (values?.recipe_costs || []).map(row => ({itemsCount:Math.max(0, Number(row?.business_count || 0)), cost:row?.cost || {}}))
        .filter(row => [2,3].includes(row.itemsCount)).sort((a,b) => a.itemsCount - b.itemsCount);
    } catch (error) {
      log(either('Не удалось обновить Проектное бюро перед созданием','Could not refresh Project Bureau before crafting') + ': ' + (error?.message || error),'bad');
      renderProjectBureau();
      return;
    }
    const liveBureauCost = bureauCost();
    if (!costParts(liveBureauCost).length) {
      alert(either('Стоимость создания не определена. Создание заблокировано.','Craft cost is unknown. Crafting is blocked.'));
      renderProjectBureau();
      return;
    }
    const available = new Map(bureauInventory.map(row => [row.businessId,row.quantity]));"""
if old in s:
    s=s.replace(old,new,1)
elif "const liveBureauCost = bureauCost();" not in s:
    raise SystemExit('Bureau preflight refresh anchor missing')

old="${scaledCostVisual(bureauCost(),attempts).replace(/<[^>]+>/g,' ')}"
new="${scaledCostVisual(liveBureauCost,attempts).replace(/<[^>]+>/g,' ')}"
if old in s:
    s=s.replace(old,new)

# Bureau: enforce budget and journal each irreversible craft.
old="""        log(either(`Создаю бизнес-план ${index + 1}/${attempts}…`, `Creating business plan ${index + 1}/${attempts}…`));
        playerDocument = await apiJson('/player/business/recipe/craft', 'POST', {businesses:inputs});
        completed++;"""
new="""        log(either(`Создаю бизнес-план ${index + 1}/${attempts}…`, `Creating business plan ${index + 1}/${attempts}…`));
        const bureauDecision = budgetDecision(liveBureauCost, 'bureau', 1, playerDocument);
        if (!bureauDecision.allowed) throw new Error(bureauDecision.problems.join('; '));
        const bureauBefore = new Map(costParts(liveBureauCost).map(part => [part.id, walletAmount(part.id, playerDocument)]));
        playerDocument = await apiJson('/player/business/recipe/craft', 'POST', {businesses:inputs});
        for (const part of costParts(liveBureauCost)) appendExpense({section:'bureau', lotId:'project-bureau', name:either('Проектное бюро','Project Bureau'), currencyId:part.id, amount:part.quantity, balanceBefore:bureauBefore.get(part.id), balanceAfter:walletAmount(part.id, playerDocument), status:'ok', result:'crafted'});
        completed++;"""
if old in s:
    s=s.replace(old,new,1)
elif "const bureauDecision = budgetDecision" not in s:
    raise SystemExit('Bureau budget anchor missing')

checks=[
    ('// @version      1.16.12','version missing'),
    (f"HK_STAGE3D_RECIPES_BUREAU_REV = '{REV}'",'marker missing'),
    ("const recipeDecision = budgetDecision(state.fair_reroll_cost, 'recipes'",'Recipes budget check missing'),
    ("appendExpense({section:'recipes'",'Recipes expense journal missing'),
    ("!costParts(bureauCost()).length",'Bureau fail-closed UI missing'),
    ("const liveBureauCost = bureauCost();",'Bureau fresh cost missing'),
    ("const bureauDecision = budgetDecision(liveBureauCost, 'bureau'",'Bureau budget check missing'),
    ("appendExpense({section:'bureau'",'Bureau expense journal missing'),
    ("GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'",'Hamster Caps invariant lost'),
    ("GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'",'General Pit Token invariant lost'),
]
for needle,message in checks:
    require(needle,message)

TARGET.write_text(s,encoding='utf-8')
