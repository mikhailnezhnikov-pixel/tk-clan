from pathlib import Path

PATH = Path("/tmp/HamsterKingMobile.user.js")
s = PATH.read_text(encoding="utf-8")

def require(marker, label=None):
    if marker not in s:
        raise SystemExit("missing expected marker: " + (label or marker[:160]))

def replace_once(old, new, label):
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 match, got {count}")
    s = s.replace(old, new, 1)

for marker in [
    "// @version      1.17.23",
    "const BUILD_VERSION = '1.17.23';",
    "const HK_CORE_REVISION = 'core-20260921-r25-businesses-catalog';",
    "const HK_BUSINESSES_CANON_REV='businesses-catalog-readonly-20260921-r1';",
    "function refreshBusinessData()",
    "function renderBusinessLists()",
    "function makePlan()",
    "function prepareOriginalBusinessRestore()",
    "function businessOptimizerPreferences()",
    "function renderBusinessOptimizerFilters()",
    "function calculateBusinessOptimizer()",
    "function fillTierFilters()",
    'id="hk-remove-tier"',
    'id="hk-insert-tier"',
    "#hk-business-lists{display:grid;grid-template-columns:1fr;gap:12px}",
]:
    require(marker)

replace_once("// @version      1.17.23", "// @version      1.17.24", "userscript version")
replace_once("const BUILD_VERSION = '1.17.23';", "const BUILD_VERSION = '1.17.24';", "build version")
replace_once(
    "const HK_CORE_REVISION = 'core-20260921-r25-businesses-catalog';",
    "const HK_CORE_REVISION = 'core-20260921-r26-businesses-rearrange-guard';",
    "core revision"
)

release = "// @release-note В «Бизнесы» добавлен read-only каталог: поиск, фильтры бонусов, лимиты, наличие и известные рецепты."
replace_once(
    release,
    "// @release-note Перестановка бизнесов: на desktop «достать» слева, «вставить» справа; T4–T6 полностью защищены от снятия.\n" + release,
    "release note"
)

replace_once(
    "const HK_BUSINESSES_CANON_REV='businesses-catalog-readonly-20260921-r1';",
    "const HK_BUSINESSES_CANON_REV='businesses-catalog-readonly-20260921-r1';\n  const HK_BUSINESSES_REARRANGE_REV='businesses-rearrange-desktop-safe-t123-20260921-r1';",
    "businesses rearrange revision"
)

# The visible 'all' option now means every tier that is actually removable.
replace_once("removeAll:'Достать: все тиры'", "removeAll:'Достать: T1–T3'", "RU remove-all label")
replace_once("removeAll:'Remove: all tiers'", "removeAll:'Remove: T1–T3'", "EN remove-all label")

# Hard safety primitive. Any occupied card whose tier is not T1-T3 is protected.
anchor = "  function refreshBusinessData() {"
guard = """  function businessRemovalAllowed(businessId) {
    if (!businessId) return true;
    const value = Number(tier(businessId) || 0);
    return value >= 1 && value <= 3;
  }

  function assertBusinessRemovalPlanAllowed(plan) {
    const blocked = (Array.isArray(plan) ? plan : []).filter(([row]) =>
      row?.businessId && !businessRemovalAllowed(row.businessId));
    if (blocked.length) throw new Error(either(
      'T4, T5 и T6 защищены от снятия.',
      'T4, T5 and T6 are protected from removal.'));
    return plan;
  }

"""
replace_once(anchor, guard + anchor, "business removal guard insertion")

replace_once(
    "    selectedSlots = new Set([...selectedSlots].filter(key => layout.some(row => row.key === key)));",
    """    selectedSlots = new Set([...selectedSlots].filter(key => {
      const row = layout.find(item => item.key === key);
      return row && (!row.businessId || businessRemovalAllowed(row.businessId));
    }));""",
    "selected slot sanitizer"
)

replace_once(
    """    const outgoing = layout.filter(row => removeFilter === -1 ? !row.businessId :
      !!row.businessId && (!removeFilter || tier(row.businessId) === removeFilter));""",
    """    const outgoing = layout.filter(row => removeFilter === -1 ? !row.businessId :
      !!row.businessId && businessRemovalAllowed(row.businessId) && (!removeFilter || tier(row.businessId) === removeFilter));""",
    "manual outgoing protection"
)

replace_once(
    """    const prepared = resolvedPreparedBusinessPlan();
    if (prepared) return prepared;
    const remaining = layout.filter(row => selectedSlots.has(row.key));""",
    """    const prepared = resolvedPreparedBusinessPlan();
    if (prepared) return assertBusinessRemovalPlanAllowed(prepared);
    const remaining = layout.filter(row => selectedSlots.has(row.key));
    assertBusinessRemovalPlanAllowed(remaining.map(row => [row, '']));""",
    "plan removal protection"
)

# Saved original layouts may contain high-tier cards. Restore may insert them,
# but it must never remove a currently installed T4-T6 card.
replace_once(
    """    if (!pairs.length) { alert(either('Исходная схема уже установлена.', 'The original setup is already active.')); return; }
    preparedBusinessPlan = pairs.map(([row,id]) => [{key:row.key,businessId:row.businessId || ''},id]);""",
    """    if (!pairs.length) { alert(either('Исходная схема уже установлена.', 'The original setup is already active.')); return; }
    const protectedPairs = pairs.filter(([row]) => row.businessId && !businessRemovalAllowed(row.businessId));
    if (protectedPairs.length) {
      alert(either(
        'Восстановление остановлено: T4, T5 и T6 нельзя снимать.',
        'Restore stopped: T4, T5 and T6 cannot be removed.'));
      return;
    }
    preparedBusinessPlan = pairs.map(([row,id]) => [{key:row.key,businessId:row.businessId || ''},id]);""",
    "restore protection"
)

# Optimizer: migration-safe read, storage-safe write, and explicit execution guard.
replace_once(
    "    const removeTiers = normalizeTiers(Array.isArray(stored.removeTiers) ? stored.removeTiers : legacyTiers);",
    "    const removeTiers = normalizeTiers(Array.isArray(stored.removeTiers) ? stored.removeTiers : legacyTiers).filter(value => value <= 3);",
    "optimizer remove tier migration"
)
replace_once(
    "      removeTiers:[...removeTiers].sort((a,b)=>a-b), insertTiers:[...insertTiers].sort((a,b)=>a-b),",
    "      removeTiers:[...removeTiers].filter(value => value >= 1 && value <= 3).sort((a,b)=>a-b), insertTiers:[...insertTiers].sort((a,b)=>a-b),",
    "optimizer remove tier persistence"
)
replace_once(
    """    const tierChoices = (kind, selected) => [1,2,3,4,5,6].map(value => `<label class="hk-tier-choice"><input type="checkbox" data-optimizer-${kind}-tier="${value}" ${selected.has(value)?'checked':''}><b>T${value}</b></label>`).join('');
    removeTierBox.innerHTML = tierChoices('remove',preferences.removeTiers);
    insertTierBox.innerHTML = tierChoices('insert',preferences.insertTiers);""",
    """    const tierChoices = (kind, selected, values) => values.map(value => `<label class="hk-tier-choice"><input type="checkbox" data-optimizer-${kind}-tier="${value}" ${selected.has(value)?'checked':''}><b>T${value}</b></label>`).join('');
    removeTierBox.innerHTML = tierChoices('remove',preferences.removeTiers,[1,2,3]);
    insertTierBox.innerHTML = tierChoices('insert',preferences.insertTiers,[1,2,3,4,5,6]);""",
    "optimizer tier controls"
)
replace_once(
    """    const canRemove = row => !row.businessId || (!protectedByGoal(row) && preferences.removeTiers.has(Number(tier(row.businessId) || 0)) && !preferences.lockedBusinessIds.has(row.businessId));""",
    """    const canRemove = row => !row.businessId || (businessRemovalAllowed(row.businessId) && !protectedByGoal(row) && preferences.removeTiers.has(Number(tier(row.businessId) || 0)) && !preferences.lockedBusinessIds.has(row.businessId));""",
    "optimizer execution protection"
)

# Manual tier selector exposes only legal removal tiers. Insert side keeps T1-T6.
replace_once(
    """      remove.innerHTML = `<option value="0">${tr('removeAll')}</option><option value="-1">${tr('emptySlots')}</option>` +
        Array.from({length:6}, (_,i) => `<option value="${i+1}">${tr('removeTier',{n:i+1})}</option>`).join('');""",
    """      remove.innerHTML = `<option value="0">${tr('removeAll')}</option><option value="-1">${tr('emptySlots')}</option>` +
        Array.from({length:3}, (_,i) => `<option value="${i+1}">${tr('removeTier',{n:i+1})}</option>`).join('');""",
    "manual tier selector"
)

replace_once(
    """      layout.filter(row => filter === 0 ? true : filter === -1 ? !row.businessId : !!row.businessId && tier(row.businessId) === filter)
        .forEach(row => selectedSlots.add(row.key));""",
    """      layout.filter(row => filter === 0 ? (!row.businessId || businessRemovalAllowed(row.businessId)) :
        filter === -1 ? !row.businessId : !!row.businessId && businessRemovalAllowed(row.businessId) && tier(row.businessId) === filter)
        .forEach(row => selectedSlots.add(row.key));""",
    "select-all removal protection"
)

# Desktop: existing canon semantics are retained. We only place the current
# remove control/list on the left and insert control/list on the right.
replace_once(
    """        <div class="hk-toolbar"><select id="hk-remove-tier"></select><button id="hk-select-remove" data-i18n="selectAll">${tr('selectAll')}</button></div>
        <div class="hk-toolbar"><select id="hk-insert-tier"></select></div>
        <div id="hk-business-lists"></div>""",
    """        <div class="hk-business-rearrange-controls"><div class="hk-toolbar"><select id="hk-remove-tier"></select><button id="hk-select-remove" data-i18n="selectAll">${tr('selectAll')}</button></div>
        <div class="hk-toolbar"><select id="hk-insert-tier"></select></div></div>
        <div id="hk-business-lists"></div>""",
    "desktop rearrange controls layout"
)

replace_once(
    "#hk-business-lists{display:grid;grid-template-columns:1fr;gap:12px}",
    ".hk-business-rearrange-controls{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:12px;align-items:start}#hk-business-lists{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:12px;align-items:start}#hk-business-lists>section{min-width:0}@media(max-width:760px){.hk-business-rearrange-controls,#hk-business-lists{grid-template-columns:1fr}}",
    "desktop rearrange CSS"
)

# Post-patch structural checks.
for marker in [
    "// @version      1.17.24",
    "const BUILD_VERSION = '1.17.24';",
    "core-20260921-r26-businesses-rearrange-guard",
    "businesses-catalog-readonly-20260921-r1",
    "businesses-rearrange-desktop-safe-t123-20260921-r1",
    "function businessRemovalAllowed(",
    "function assertBusinessRemovalPlanAllowed(",
    "removeAll:'Достать: T1–T3'",
    "removeAll:'Remove: T1–T3'",
    "Array.from({length:3}",
    "removeTierBox.innerHTML = tierChoices('remove',preferences.removeTiers,[1,2,3]);",
    "businessRemovalAllowed(row.businessId)",
    "hk-business-rearrange-controls",
    "grid-template-columns:minmax(0,1fr) minmax(0,1fr)",
    'data-business-tab="catalog"',
    "businesses-catalog-readonly-20260921-r1",
    "explore-production-ui-20260921-r1",
    "buildings-native-sync-20260921-r1",
    "maps-shared-runtime-20260921-r7-safe5",
]:
    require(marker, "post-patch " + marker)

# These forbidden selectors must no longer be produced by the manual/optimizer
# removal controls.
if "Array.from({length:6}, (_,i) => `<option value=\"${i+1}\">${tr('removeTier'" in s:
    raise SystemExit("legacy T1-T6 manual removal selector still present")
if "removeTierBox.innerHTML = tierChoices('remove',preferences.removeTiers);" in s:
    raise SystemExit("legacy T1-T6 optimizer removal selector still present")

PATH.write_text(s, encoding="utf-8")
print("BUSINESSES_REARRANGE_DESKTOP_SAFE_T123_R1_PATCH=PASS")
