from pathlib import Path
import re

TARGET = Path("/tmp/HamsterKingMobile.user.js")
REV = "bureau-resources-live-20260920-r1"
MARKER = f"// HK_BUREAU_RESOURCES_LIVE_V1 {REV}"

def require(text, needle, label):
    if needle not in text:
        raise SystemExit(f"1.17.1 hotfix check failed: {label}")

def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"1.17.1 hotfix anchor missing: {label}")
    return text.replace(old, new, 1)

def sync_version(text):
    if MARKER in text and "// @version      1.17.1" in text:
        return text
    require(text, "// @version      1.17.0", "live version 1.17.0")
    text = text.replace("// @version      1.17.0", "// @version      1.17.1", 1)
    old_fallback = """  const BUILD_VERSION = typeof GM_info !== 'undefined' && GM_info?.script?.version
    ? String(GM_info.script.version)
    : '1.17.0';"""
    new_fallback = """  const BUILD_VERSION = typeof GM_info !== 'undefined' && GM_info?.script?.version
    ? String(GM_info.script.version)
    : '1.17.1';"""
    if old_fallback not in text:
        raise SystemExit("BUILD_VERSION 1.17.0 fallback missing")
    text = text.replace(old_fallback, new_fallback, 1)
    return text

def apply_hotfix(text):
    require(text, "GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'", "Hamsters must use Caps")
    require(text, "GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'", "Generals must use Pit Tokens")
    require(text, "HK_STAGE2B_RUNNER_REV = 'stage2b-20260919-r1'", "Recipes/Bureau Runner migration")
    require(text, "HK_STAGE2I_BUILDINGS_REV = 'stage2i-buildings-explore-20260919-r1'", "Buildings/Explore migration")
    require(text, "hkAuthoritativePlayerRead('bureau-complete')", "Bureau authoritative reconciliation")
    require(text, "hkAuthoritativePlayerRead('resources-complete')", "Resource authoritative reconciliation")

    text = sync_version(text)

    if MARKER not in text:
        anchor = "  const HK_STAGE2I_BUILDINGS_REV = 'stage2i-buildings-explore-20260919-r1';"
        require(text, anchor, "revision marker anchor")
        text = text.replace(anchor, anchor + f"\n  {MARKER}", 1)

    # Project Bureau must always start from fresh inventory and live recipe costs.
    text = replace_once(
        text,
        "      if (!playerDocument) playerDocument = await apiJson('/player/me', 'POST');",
        "      playerDocument = await apiJson('/player/me', 'POST');",
        "Bureau fresh inventory read",
    )
    text = replace_once(
        text,
        "        bureauCosts = [{itemsCount:2,cost:{}},{itemsCount:3,cost:{}}];",
        "        bureauCosts = [];",
        "Bureau unknown-cost fail closed",
    )
    text = replace_once(
        text,
        "    const run = root?.querySelector('#hk-bureau-run'); if (run) run.disabled = bureauRunning || selectedCount !== bureauSize;",
        "    const run = root?.querySelector('#hk-bureau-run'); if (run) run.disabled = bureauRunning || selectedCount !== bureauSize || !costParts(bureauCost()).length;",
        "Bureau disabled without cost",
    )

    old = """    const attempts = Math.max(1, Math.min(100, Math.trunc(Number(root.querySelector('#hk-bureau-attempts').value || 1))));
    const available = new Map(bureauInventory.map(row => [row.businessId,row.quantity]));"""
    new = """    const attempts = Math.max(1, Math.min(100, Math.trunc(Number(root.querySelector('#hk-bureau-attempts').value || 1))));
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
    const projectedBureau = budgetDecision(liveBureauCost, 'bureau', attempts, playerDocument);
    if (!projectedBureau.allowed) {
      alert(projectedBureau.problems.join('\\n'));
      renderProjectBureau();
      return;
    }
    const available = new Map(bureauInventory.map(row => [row.businessId,row.quantity]));"""
    text = replace_once(text, old, new, "Bureau preflight refresh and budget")

    text = text.replace(
        "${scaledCostVisual(bureauCost(),attempts).replace(/<[^>]+>/g,' ')}",
        "${scaledCostVisual(liveBureauCost,attempts).replace(/<[^>]+>/g,' ')}",
    )

    old = """        log(either(`Создаю бизнес-план ${index + 1}/${attempts}…`, `Creating business plan ${index + 1}/${attempts}…`));
        playerDocument = await apiJson('/player/business/recipe/craft', 'POST', {businesses:inputs});
        completed++;"""
    new = """        log(either(`Создаю бизнес-план ${index + 1}/${attempts}…`, `Creating business plan ${index + 1}/${attempts}…`));
        const bureauDecision = budgetDecision(liveBureauCost, 'bureau', 1, playerDocument);
        if (!bureauDecision.allowed) throw new Error(bureauDecision.problems.join('; '));
        const bureauBefore = new Map(costParts(liveBureauCost).map(part => [part.id, walletAmount(part.id, playerDocument)]));
        playerDocument = await apiJson('/player/business/recipe/craft', 'POST', {businesses:inputs}, true, 0);
        for (const part of costParts(liveBureauCost)) appendExpense({section:'bureau', lotId:'project-bureau', name:either('Проектное бюро','Project Bureau'), currencyId:part.id, amount:part.quantity, balanceBefore:bureauBefore.get(part.id), balanceAfter:walletAmount(part.id, playerDocument), status:'ok', result:'crafted'});
        completed++;"""
    text = replace_once(text, old, new, "Bureau irreversible craft guard")

    # Resource rows and affordability must be rebuilt from live state before confirmation.
    old = """  async function runResourceEvents(rows) {
    const totalCompletions = 1000 * resourceRepeatCount;
    const maximumMode = resourceMaximumMode;
    const ready = (rows || []).filter(row => row?.atMax && row?.affordable > 0 && !resourceEventIsExcluded(row)).map(row => {
      const maximum = Math.max(0, Math.trunc(row.affordable));
      return {...row,plannedCompletions:maximumMode ? maximum : Math.min(totalCompletions,maximum)};
    });
    if (!requireLicense() || resourceBusy || !ready.length) return;"""
    new = """  async function runResourceEvents(rows) {
    if (!requireLicense() || resourceBusy) return;
    const wanted = (rows || []).map(row => ({buildingId:String(row?.buildingId || ''), roomId:String(row?.roomId || ''), sideEventId:String(row?.sideEventId || ''), eventId:String(row?.eventId || '')}));
    if (!wanted.length) return;
    const refreshed = await loadResources(false);
    if (!refreshed) return;
    const freshEvents = allResourceEvents();
    const sourceRows = wanted.map(key => freshEvents.find(row => String(row?.buildingId || '') === key.buildingId && String(row?.roomId || '') === key.roomId && String(row?.sideEventId || '') === key.sideEventId && String(row?.eventId || '') === key.eventId)).filter(Boolean);
    const totalCompletions = 1000 * resourceRepeatCount;
    const maximumMode = resourceMaximumMode;
    const ready = sourceRows.filter(row => row?.atMax && row?.affordable > 0 && !resourceEventIsExcluded(row)).map(row => {
      const maximum = Math.max(0, Math.trunc(row.affordable));
      return {...row,plannedCompletions:maximumMode ? maximum : Math.min(totalCompletions,maximum)};
    });
    if (!ready.length) return;"""
    text = replace_once(text, old, new, "Resources fresh-row preflight")

    old = "    const lines = ready.map((row,index) => `${index + 1}. ${row.buildingName} — ${row.name} ×${row.plannedCompletions}`);"
    new = """    const projectedProblems = ready.flatMap(row => budgetDecision(row.cost, 'resources', row.plannedCompletions, playerDocument).problems);
    if (projectedProblems.length) {
      alert(`${either('Ресурсный обмен заблокирован единым бюджетом','Resource exchange blocked by unified budget')}:\\n\\n${[...new Set(projectedProblems)].join('\\n')}`);
      return;
    }
    const lines = ready.map((row,index) => `${index + 1}. ${row.buildingName} — ${row.name} ×${row.plannedCompletions}`);"""
    text = replace_once(text, old, new, "Resources projected budget")

    old = """        const request = numberOfCompletions => apiJson('/player/event','POST',{
          event_building_id:row.roomId,
          tier:row.tier,
          side_event_id:row.sideEventId || undefined,
          number_of_completions:numberOfCompletions
        });"""
    new = """        const request = async numberOfCompletions => {
          const quantity = Math.max(1, Math.trunc(Number(numberOfCompletions || 0)));
          const decision = budgetDecision(row.cost, 'resources', quantity, playerDocument);
          if (!decision.allowed) throw new Error(decision.problems.join('; '));
          const before = new Map(costParts(row.cost).map(part => [part.id, walletAmount(part.id, playerDocument)]));
          const value = await apiJson('/player/event','POST',{
            event_building_id:row.roomId,
            tier:row.tier,
            side_event_id:row.sideEventId || undefined,
            number_of_completions:quantity
          },true,0);
          for (const part of costParts(row.cost)) appendExpense({section:'resources', lotId:`resource:${row.buildingId}:${row.roomId}:${row.sideEventId || row.eventId}`, name:row.name || either('Ресурсный обмен','Resource exchange'), currencyId:part.id, amount:part.quantity * quantity, balanceBefore:before.get(part.id), balanceAfter:null, status:'ok', result:`completed ${quantity}`});
          return value;
        };"""
    text = replace_once(text, old, new, "Resources non-retry budgeted mutation")

    checks = [
        "// @version      1.17.1",
        MARKER,
        "const liveBureauCost = bureauCost();",
        "budgetDecision(liveBureauCost, 'bureau', attempts",
        "budgetDecision(liveBureauCost, 'bureau', 1",
        "appendExpense({section:'bureau'",
        "const freshEvents = allResourceEvents();",
        "budgetDecision(row.cost, 'resources', row.plannedCompletions",
        "apiJson('/player/event','POST'",
        "},true,0);",
        "appendExpense({section:'resources'",
        "hkAuthoritativePlayerRead('bureau-complete')",
        "hkAuthoritativePlayerRead('resources-complete')",
        "GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'",
        "GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'",
    ]
    for needle in checks:
        require(text, needle, needle)

    # Resource exchanges are mutations, while building study is a read.
    ro_start = text.find("  const HK_READ_ONLY_POST_PATHS = new Set([")
    ro_end = text.find("\n  ]);", ro_start)
    if ro_start < 0 or ro_end < 0:
        raise SystemExit("read-only POST path block missing")
    ro = text[ro_start:ro_end]
    if "'/player/event'" in ro:
        raise SystemExit("/player/event incorrectly classified read-only")
    if "'/player/building'" not in ro:
        raise SystemExit("/player/building lost read-only classification")

    return text

if __name__ == "__main__":
    source = TARGET.read_text(encoding="utf-8")
    TARGET.write_text(apply_hotfix(source), encoding="utf-8")
    print("BUREAU_RESOURCES_LIVE_1171_OK")
