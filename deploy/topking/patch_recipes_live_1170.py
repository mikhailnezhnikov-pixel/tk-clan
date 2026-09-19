from pathlib import Path
TARGET=Path("/tmp/HamsterKingMobile.user.js")
MARKER="// HK_RECIPES_LIVE_VERIFY_V1 recipes-live-20260920-r1"

def req(s,n,m):
    if n not in s: raise SystemExit(m)

def rep(s,old,new,label):
    if old in s: return s.replace(old,new,1)
    if new in s: return s
    raise SystemExit("Recipes anchor missing: "+label)

def apply_recipes_live_hotfix(s):
    req(s,"// @version      1.17.0","Recipes requires live 1.17.0")
    req(s,"HK_FAIR_SHOP_LIVE_VERIFY_V1 fair-shop-live-verify-20260920-r1","Fair/Shop marker missing")
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
    s=rep(s,old,new,"fresh preflight")
    old="""        fairDocument = await apiJson('/fair/reroll', 'POST', {fair_id:recipeFairId});
        state = recipeState(fairDocument);"""
    new="""        state = recipeState(fairDocument || playerDocument);
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
    s=rep(s,old,new,"per-reroll safety")
    anchor="  // HK_FAIR_SHOP_LIVE_VERIFY_V1 fair-shop-live-verify-20260920-r1"
    req(s,anchor,"Recipes marker anchor missing")
    if MARKER not in s: s=s.replace(anchor,anchor+"\n  "+MARKER,1)
    for n in [MARKER,"const recipeDecision = budgetDecision(state.fair_reroll_cost, 'recipes'","appendExpense({section:'recipes'","() => apiJsonCore(path, method, body, retryAuthorization, 0)"]:
        req(s,n,"Recipes verification failed: "+n)
    return s

if __name__=="__main__":
    s=TARGET.read_text(encoding="utf-8")
    TARGET.write_text(apply_recipes_live_hotfix(s),encoding="utf-8")
    print("RECIPES_LIVE_1170_VERIFY_OK")
