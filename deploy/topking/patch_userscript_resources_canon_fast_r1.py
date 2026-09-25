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

# Version + release notes.
replace("// @version      1.17.83",
        "// @version      1.17.84\n"
        "// @release-note Ресурсы: Runner приведён к канону панели — выбранная Ореховая/Инструментовая/Жетоновая показывается в заголовке, а сырой placeholder «event name side» больше не попадает в интерфейс.\n"
        "// @release-note Ресурсы: убрано лишнее повторное чтение /player/me после обмена и разрешено переиспользовать совсем свежий player-state при обычном открытии/переключении вкладки; защита 429 и глобальный rate guard не ослаблены.",
        "metadata version")
replace("const BUILD_VERSION = '1.17.83';",
        "const BUILD_VERSION = '1.17.84';",
        "build version")

replace(
    "const HK_STAGE2D_RUNNER_REV = 'stage2d-resource-business-20260919-r1';",
    "const HK_STAGE2D_RUNNER_REV = 'stage2d-resource-business-20260919-r1';\n"
    "  const HK_RESOURCE_CANON_FAST_REV = 'resources-canon-fast-20260925-r1';\n"
    "  const RESOURCE_PLAYER_CACHE_MS = 12000;",
    "resource marker"
)

# Canonical display name: never surface raw localization placeholders.
tier_anchor = """  function resourceTierLabel(tier) {
    return ['1','2','3','4','4+','5','5+','MAX'][Math.max(0,Math.trunc(Number(tier)))] || `T${Math.max(0,Math.trunc(Number(tier))) + 1}`;
  }
"""
tier_new = tier_anchor + """
  function resourceDisplayName(row) {
    const raw=clean(row?.name);
    const placeholder=!raw || /^event[\\s_-]*name(?:[\\s_-]*side)?$/i.test(raw) || /^side[\\s_-]*event(?:[\\s_-]*name)?$/i.test(raw);
    if (!placeholder) return raw;
    const room=Number(row?.roomNumber);
    const base=either('Ресурсный обмен','Resource exchange');
    return Number.isFinite(room) && room > 0 ? `${base} · ${either('ячейка','slot')} ${room}` : base;
  }
"""
replace(tier_anchor, tier_new, "resource display helper")

replace(
    '<div><b>${escapeHtml(row.name)}</b><small>${escapeHtml(reason)}</small></div>',
    '<div><b>${escapeHtml(resourceDisplayName(row))}</b><small>${escapeHtml(reason)}</small></div>',
    "resource row label"
)

# Reuse a very fresh player snapshot for non-destructive UI refreshes.
replace(
    "async function loadResources(showLog = true) {\n    if (!requireLicense() || resourceBusy) return false;\n    resourceBusy = true; renderResources();\n    try {\n      playerDocument = await apiJson('/player/me', 'POST');",
    "async function loadResources(showLog = true, options = {}) {\n"
    "    if (!requireLicense() || resourceBusy) return false;\n"
    "    resourceBusy = true; renderResources();\n"
    "    try {\n"
    "      const refreshPlayer=options?.refreshPlayer !== false;\n"
    "      const maxAgeMs=Math.max(0,Number(options?.playerMaxAgeMs||0));\n"
    "      const freshSnapshot=maxAgeMs>0 && hkStateStore.snapshot && Date.now()-Number(hkStateStore.updatedAt||0)<=maxAgeMs;\n"
    "      if (refreshPlayer && !freshSnapshot) playerDocument = await apiJson('/player/me', 'POST');\n"
    "      else if (hkStateStore.snapshot) playerDocument = hkStateStore.snapshot;\n"
    "      else if (!playerDocument) playerDocument = await apiJson('/player/me', 'POST');",
    "loadResources player refresh"
)

replace(
    "return loadResources(false);\n  }\n\n  async function loadResources(showLog = true, options = {})",
    "return loadResources(false,{playerMaxAgeMs:RESOURCE_PLAYER_CACHE_MS});\n  }\n\n  async function loadResources(showLog = true, options = {})",
    "resource kind cached refresh"
)

replace(
    "if (resourceMaximumMode) await loadResources(false);\n      else renderResources();",
    "if (resourceMaximumMode) await loadResources(false,{playerMaxAgeMs:RESOURCE_PLAYER_CACHE_MS});\n      else renderResources();",
    "resource maximum cached refresh"
)

# Confirmation and Runner: selected resource is the title, stable canonical task text is the step.
replace(
    "const lines = ready.map((row,index) => `${index + 1}. ${row.buildingName} — ${row.name} ×${row.plannedCompletions}`);",
    "const lines = ready.map((row,index) => `${index + 1}. ${row.buildingName} — ${resourceDisplayName(row)} ×${row.plannedCompletions}`);",
    "resource confirm lines"
)
replace(
    "hkRunner.start({title:either('Ресурсные здания','Resource buildings'),total:ready.length,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});",
    "hkRunner.start({title:resourceTypeName(resourceSelectedKind),total:ready.length,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});",
    "resource runner title"
)
replace(
    "hkRunner.setStep(row.name || either('Ресурсное задание','Resource task'), completed, ready.length);\n        log(either(`Выполняю: ${row.name} ×${row.plannedCompletions}…`,`Running: ${row.name} ×${row.plannedCompletions}…`));",
    "const displayName=resourceDisplayName(row);\n"
    "        hkRunner.setStep(`${resourceTierLabel(row.tier)} · ${displayName} · ×${row.plannedCompletions}`, completed, ready.length);\n"
    "        log(either(`Выполняю: ${displayName} ×${row.plannedCompletions}…`,`Running: ${displayName} ×${row.plannedCompletions}…`));",
    "resource runner step"
)
replace(
    "name:row.name || either('Ресурсный обмен','Resource exchange')",
    "name:displayName || either('Ресурсный обмен','Resource exchange')",
    "resource expense label"
)
replace(
    "Для задания «${row.name}» потребуется ${requestCount.toLocaleString(locale())} отдельных запросов.",
    "Для задания «${displayName}» потребуется ${requestCount.toLocaleString(locale())} отдельных запросов.",
    "resource large request prompt ru"
)
replace(
    "Task “${row.name}” requires ${requestCount.toLocaleString(locale())} separate requests.",
    "Task “${displayName}” requires ${requestCount.toLocaleString(locale())} separate requests.",
    "resource large request prompt en"
)
replace(
    "Обмен «${row.name}»: запросов ${processedRequests.toLocaleString(locale())}/${requestCount.toLocaleString(locale())}",
    "Обмен «${displayName}»: запросов ${processedRequests.toLocaleString(locale())}/${requestCount.toLocaleString(locale())}",
    "resource progress log ru"
)
replace(
    "Exchange “${row.name}”: requests ${processedRequests.toLocaleString(locale())}/${requestCount.toLocaleString(locale())}",
    "Exchange “${displayName}”: requests ${processedRequests.toLocaleString(locale())}/${requestCount.toLocaleString(locale())}",
    "resource progress log en"
)

# Post-run had player/me twice: loadResources() already read it and then authoritative read repeated it.
replace(
    "resourceBusy = false;\n      await loadResources(false);\n      await hkAuthoritativePlayerRead('resources-complete');\n      hkRunner.finish(either('Ресурсные задания завершены','Resource tasks completed'));",
    "resourceBusy = false;\n"
    "      await hkAuthoritativePlayerRead('resources-complete');\n"
    "      await loadResources(false,{refreshPlayer:false});\n"
    "      const resourceLive=moduleLiveState.get('resources')||{};\n"
    "      moduleLiveState.set('resources',{...resourceLive,at:Date.now(),blockedUntil:0});\n"
    "      hkRunner.finish(either('Ресурсные задания завершены','Resource tasks completed'));",
    "resource post-run duplicate read"
)

replace(
    "if (key === 'resources') {const value=await loadResources(false);liveReadOk=true;return value;}",
    "if (key === 'resources') {const value=await loadResources(false,{playerMaxAgeMs:RESOURCE_PLAYER_CACHE_MS});liveReadOk=true;return value;}",
    "resource module live cache"
)

# Give Resources the same compact runner card canon as Buildings.
old_decl = "const visibleState=state.status!=='idle',title=String(state.title||''),exploreRun=visibleState&&[either('Исследование · E3','Explore · E3'),either('Исследование','Explore')].includes(title),buildingsRun=visibleState&&title===either('Здания','Buildings'),businessesRun=visibleState&&title===either('Перестановка бизнесов','Business rearrangement'),hamstersRun=visibleState&&title===either('Хомяки','Hamsters'),generalsRun=visibleState&&title===either('Генералы','Generals'); box.classList.toggle('show',visibleState);"
new_decl = "const visibleState=state.status!=='idle',title=String(state.title||''),exploreRun=visibleState&&[either('Исследование · E3','Explore · E3'),either('Исследование','Explore')].includes(title),buildingsRun=visibleState&&title===either('Здания','Buildings'),resourcesRun=visibleState&&Object.keys(RESOURCE_BUILDING_TYPES).some(kind=>title===resourceTypeName(kind)),businessesRun=visibleState&&title===either('Перестановка бизнесов','Business rearrangement'),hamstersRun=visibleState&&title===either('Хомяки','Hamsters'),generalsRun=visibleState&&title===either('Генералы','Generals'); box.classList.toggle('show',visibleState);"
replace(old_decl,new_decl,"runner resources detection")
replace(
    "box.classList.toggle('buildings-run',buildingsRun);",
    "box.classList.toggle('buildings-run',buildingsRun);\n    box.classList.toggle('resources-run',resourcesRun);",
    "runner resources class"
)
replace(
    "(buildingsRun||exploreRun||businessesRun||hamstersRun||generalsRun)&&state.total",
    "(buildingsRun||resourcesRun||exploreRun||businessesRun||hamstersRun||generalsRun)&&state.total",
    "runner resources count"
)

css_anchor = ".hk-runner.buildings-run .hk-runner-history{border-color:#304057;background:#0c131d}"
css_add = css_anchor + ".hk-runner.resources-run{margin:0 0 14px;padding:14px 16px;border:1px solid #304057;border-radius:16px;background:#111925;box-shadow:none}.hk-runner.resources-run .hk-runner-head b{font-size:15px;color:#f2f5fa}.hk-runner.resources-run .hk-runner-state{padding:4px 8px;border-radius:999px;background:#1d2a3c;color:#cbd7e6;font-size:9px;font-weight:800}.hk-runner.resources-run .hk-runner-step{margin-top:7px;color:#9fb0c6;font-size:11px}.hk-runner.resources-run .hk-runner-track{height:7px;margin:10px 0 9px;background:#26364b}.hk-runner.resources-run .hk-runner-actions{justify-content:flex-end}.hk-runner.resources-run .hk-runner-actions button{flex:0 0 auto;width:auto;min-width:132px;min-height:36px;padding:9px 16px}.hk-runner.resources-run .hk-runner-history{border-color:#304057;background:#0c131d}"
replace(css_anchor,css_add,"resource runner css")

for marker in [
    "// @version      1.17.84",
    "const BUILD_VERSION = '1.17.84';",
    "resources-canon-fast-20260925-r1",
    "function resourceDisplayName(row)",
    "playerMaxAgeMs:RESOURCE_PLAYER_CACHE_MS",
    "box.classList.toggle('resources-run',resourcesRun)",
    ".hk-runner.resources-run"
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

if "event name side" in s.lower():
    # The phrase is allowed only in the release note documenting the fix.
    occurrences=s.lower().count("event name side")
    if occurrences != 1:
        raise SystemExit(f"unexpected raw event placeholder occurrences: {occurrences}")

target.write_text(s, encoding="utf-8")
print("RESOURCE_CANON_FAST_R1=PASS")
print("version=1.17.84")
