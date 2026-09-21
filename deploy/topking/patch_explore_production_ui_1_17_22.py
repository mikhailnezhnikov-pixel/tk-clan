from pathlib import Path

PATH=Path("/tmp/HamsterKingMobile.user.js")
s=PATH.read_text(encoding="utf-8")

required=[
    "// @version      1.17.21",
    "const BUILD_VERSION = '1.17.21';",
    "const HK_CORE_REVISION = 'core-20260921-r23-explore-e4-queue';",
    "const HK_EXPLORE_E4_REV='explore-e4-queue-20260921-r1';",
    "async function runExploreE4Queue()",
    "id=\"hk-ex-run-limit\"",
    "id=\"hk-ex-run-one\"",
    "id=\"hk-ex-run-queue\"",
]
for marker in required:
    if marker not in s:
        raise SystemExit(f"missing expected marker: {marker}")

s=s.replace("// @version      1.17.21","// @version      1.17.22",1)
s=s.replace(
    "// @release-note Добавлена безопасная очередь исследования E4 с лимитом 1 / 5 / 10 / 15 / 20 / все выбранные.",
    "// @release-note Упрощён экран исследования: убраны тестовая кнопка и дублирующий лимит; очередь использует «Максимум зданий».\n"
    "// @release-note Добавлена безопасная очередь исследования нескольких зданий.",
    1,
)
s=s.replace("const BUILD_VERSION = '1.17.21';","const BUILD_VERSION = '1.17.22';",1)
s=s.replace(
    "const HK_CORE_REVISION = 'core-20260921-r23-explore-e4-queue';",
    "const HK_CORE_REVISION = 'core-20260921-r24-explore-production-ui';",
    1,
)
s=s.replace(
    "const HK_EXPLORE_E4_REV='explore-e4-queue-20260921-r1';",
    "const HK_EXPLORE_E4_REV='explore-e4-queue-20260921-r1';\n"
    "  const HK_EXPLORE_UI_REV='explore-production-ui-20260921-r1';",
    1,
)

# Remove the redundant runLimit field from returned settings.
old="""      speedProfileRev:HK_EXPLORE_SPEED_REV,
      runLimit:[1,5,10,15,20].includes(Number(x.runLimit))||Number(x.runLimit)===0?Number(x.runLimit):1,
      exploreTargetTier:targetActionsAllowed,exploreTargetBattles:targetActionsAllowed&&x.exploreTargetBattles===true
"""
new="""      speedProfileRev:HK_EXPLORE_SPEED_REV,
      exploreTargetTier:targetActionsAllowed,exploreTargetBattles:targetActionsAllowed&&x.exploreTargetBattles===true
"""
if old not in s: raise SystemExit("settings runLimit block missing")
s=s.replace(old,new,1)

old="""    x.speedProfileRev=HK_EXPLORE_SPEED_REV;
    x.runLimit=[1,5,10,15,20].includes(Number(x.runLimit))||Number(x.runLimit)===0?Number(x.runLimit):1;
    x.exploreTargetTier=targetActionsAllowed;if(!x.exploreTargetTier)x.exploreTargetBattles=false;
"""
new="""    x.speedProfileRev=HK_EXPLORE_SPEED_REV;
    x.exploreTargetTier=targetActionsAllowed;if(!x.exploreTargetTier)x.exploreTargetBattles=false;
"""
if old not in s: raise SystemExit("save runLimit block missing")
s=s.replace(old,new,1)

old="""      buyMissingMaterials:!!b.querySelector('#hk-ex-buy')?.checked,
      runLimit:String(b.querySelector('#hk-ex-run-limit')?.value||'1')==='all'?0:Number(b.querySelector('#hk-ex-run-limit')?.value||1),
      exploreTargetTier:!!b.querySelector('#hk-ex-target-tier')?.checked,
"""
new="""      buyMissingMaterials:!!b.querySelector('#hk-ex-buy')?.checked,
      exploreTargetTier:!!b.querySelector('#hk-ex-target-tier')?.checked,
"""
if old not in s: raise SystemExit("read runLimit block missing")
s=s.replace(old,new,1)

# E4 queue now uses the already-existing selected list, which is capped by maxBuildings.
old="""      const limit=Number(settings.runLimit);
      const queue=limit===0?source:source.slice(0,Math.max(1,limit||1));
      const ok=confirm(either(
        'E4: обработать '+queue.length+' из '+source.length+' выбранных зданий последовательно?',
        'E4: process '+queue.length+' of '+source.length+' selected buildings sequentially?'
      ));
"""
new="""      const queue=source;
      const ok=confirm(either(
        'Обработать '+queue.length+' выбранных зданий последовательно?',
        'Process '+queue.length+' selected buildings sequentially?'
      ));
"""
if old not in s: raise SystemExit("queue limit block missing")
s=s.replace(old,new,1)

# Production-facing labels no longer expose development-stage E3/E4 terms.
s=s.replace(
    "hkRunner.start({title:either('Исследование · E4','Explore · E4'),total:queue.length,step:either('Подготовка очереди','Preparing queue'),pausable:true,stoppable:true});",
    "hkRunner.start({title:either('Исследование','Explore'),total:queue.length,step:either('Подготовка очереди','Preparing queue'),pausable:true,stoppable:true});",
    1,
)
s=s.replace("either('E4: здание пропущено: ','E4: building skipped: ')","either('Здание пропущено: ','Building skipped: ')",1)
s=s.replace("either('E4 остановлен: ','E4 stopped: ')","either('Исследование остановлено: ','Explore stopped: ')",1)
s=s.replace("either('E4 завершён','E4 completed')","either('Исследование завершено','Explore completed')",1)
s=s.replace("either('E4: очередь завершена','E4: queue completed')","either('Очередь исследования завершена','Explore queue completed')",1)
s=s.replace("either('E4 остановлен пользователем','E4 stopped by user')","either('Исследование остановлено пользователем','Explore stopped by user')",1)
s=s.replace("either('Ошибка E4: ','E4 error: ')","either('Ошибка исследования: ','Explore error: ')",1)

# Render: maxBuildings is the only queue cap.
old="""    const queueCount=p?Math.min(p.selected.length,s.runLimit===0?Number.MAX_SAFE_INTEGER:s.runLimit):0;
"""
new="""    const queueCount=p?Number(p.selected.length||0):0;
"""
if old not in s: raise SystemExit("queueCount block missing")
s=s.replace(old,new,1)

old_grid="'#hk-explore-content .hk-ex-filter-grid{display:grid;grid-template-columns:repeat(5,minmax(140px,1fr));gap:10px;margin-top:10px}'+"
new_grid="'#hk-explore-content .hk-ex-filter-grid{display:grid;grid-template-columns:repeat(4,minmax(150px,1fr));gap:10px;margin-top:10px}'+"
if old_grid not in s: raise SystemExit("5-column grid missing")
s=s.replace(old_grid,new_grid,1)

old="""            '<label class="hk-ex-field"><span>'+either('Максимум зданий','Maximum buildings')+'</span><input id="hk-ex-max" type="number" min="1" max="5000" value="'+s.maxBuildings+'"></label>'+
            '<label class="hk-ex-field"><span>'+either('Лимит запуска E4','E4 run limit')+'</span><select id="hk-ex-run-limit"><option value="1" '+(s.runLimit===1?'selected':'')+'>1</option><option value="5" '+(s.runLimit===5?'selected':'')+'>5</option><option value="10" '+(s.runLimit===10?'selected':'')+'>10</option><option value="15" '+(s.runLimit===15?'selected':'')+'>15</option><option value="20" '+(s.runLimit===20?'selected':'')+'>20</option><option value="all" '+(s.runLimit===0?'selected':'')+'>'+either('Все выбранные','All selected')+'</option></select></label>'+
"""
new="""            '<label class="hk-ex-field"><span>'+either('Максимум зданий','Maximum buildings')+'</span><input id="hk-ex-max" type="number" min="1" max="5000" value="'+s.maxBuildings+'"></label>'+
"""
if old not in s: raise SystemExit("run-limit field missing")
s=s.replace(old,new,1)

old="""    const planHtml=p?'<div class="hk-cardbox"><b>'+either('План','Plan')+'</b><p><strong>'+either('Выбрано планом: ','Selected by plan: ')+p.selected.length+' · '+either('К запуску E4: ','E4 queue: ')+queueCount+'</strong></p><p class="hk-muted">'+either('После фильтров','After filters')+': '+p.filteredCount+' · '+either('кандидатов','candidates')+': '+p.candidates.length+'</p>'+
"""
new="""    const planHtml=p?'<div class="hk-cardbox"><b>'+either('План','Plan')+'</b><p><strong>'+either('Будет обработано зданий: ','Buildings to process: ')+queueCount+'</strong></p><p class="hk-muted">'+either('После фильтров','After filters')+': '+p.filteredCount+' · '+either('кандидатов','candidates')+': '+p.candidates.length+'</p>'+
"""
if old not in s: raise SystemExit("plan E4 label missing")
s=s.replace(old,new,1)

old="""        '<div class="hk-ex-actions"><button id="hk-ex-plan" class="hk-primary" '+(exploreBusy?'disabled':'')+'>'+(exploreBusy?either('Считаю…','Calculating…'):either('Рассчитать план','Calculate plan'))+'</button><button id="hk-ex-run-one" class="hk-secondary" '+(exploreBusy||!p?.selected?.length?'disabled':'')+'>'+either('Тест E3 · 1 здание','E3 test · 1 building')+'</button><button id="hk-ex-run-queue" class="hk-primary" '+(exploreBusy||!p?.selected?.length?'disabled':'')+'>'+(s.runLimit===0?either('Запустить E4 · все выбранные','Run E4 · all selected'):either('Запустить E4 · до '+s.runLimit,'Run E4 · up to '+s.runLimit))+'</button><span id="hk-ex-dirty" class="hk-muted hk-ex-dirty"></span></div>'+
"""
new="""        '<div class="hk-ex-actions"><button id="hk-ex-plan" class="hk-primary" '+(exploreBusy?'disabled':'')+'>'+(exploreBusy?either('Считаю…','Calculating…'):either('Рассчитать план','Calculate plan'))+'</button><button id="hk-ex-run-queue" class="hk-primary" '+(exploreBusy||!p?.selected?.length?'disabled':'')+'>'+either('Запустить','Run')+'</button><span id="hk-ex-dirty" class="hk-muted hk-ex-dirty"></span></div>'+
"""
if old not in s: raise SystemExit("test/run action block missing")
s=s.replace(old,new,1)

old="""    box.querySelector('#hk-ex-run-one')?.addEventListener('click',()=>void runExploreE3Single());
    box.querySelector('#hk-ex-run-queue')?.addEventListener('click',()=>void runExploreE4Queue());
"""
new="""    box.querySelector('#hk-ex-run-queue')?.addEventListener('click',()=>void runExploreE4Queue());
"""
if old not in s: raise SystemExit("run-one listener missing")
s=s.replace(old,new,1)

# Runner recognizes production Explore title while keeping E3 compatibility internally.
old="""    const visibleState=state.status!=='idle',title=String(state.title||''),exploreRun=visibleState&&[either('Исследование · E3','Explore · E3'),either('Исследование · E4','Explore · E4')].includes(title),buildingsRun=visibleState&&title===either('Здания','Buildings'); box.classList.toggle('show',visibleState);
"""
new="""    const visibleState=state.status!=='idle',title=String(state.title||''),exploreRun=visibleState&&[either('Исследование · E3','Explore · E3'),either('Исследование','Explore')].includes(title),buildingsRun=visibleState&&title===either('Здания','Buildings'); box.classList.toggle('show',visibleState);
"""
if old not in s: raise SystemExit("runner Explore title block missing")
s=s.replace(old,new,1)

old="""const exploreTitle=[either('Исследование · E3','Explore · E3'),either('Исследование · E4','Explore · E4')].includes(String(state.title||''));"""
new="""const exploreTitle=[either('Исследование · E3','Explore · E3'),either('Исследование','Explore')].includes(String(state.title||''));"""
if old not in s: raise SystemExit("finish exploreTitle block missing")
s=s.replace(old,new,1)

for marker in [
    "// @version      1.17.22",
    "const BUILD_VERSION = '1.17.22';",
    "core-20260921-r24-explore-production-ui",
    "explore-production-ui-20260921-r1",
    "const queue=source;",
    "Будет обработано зданий:",
    "id=\"hk-ex-run-queue\"",
    "either('Запустить','Run')",
    "buildings-native-sync-20260921-r1",
    "maps-shared-runtime-20260921-r7-safe5",
    "AUTH_PASSIVE_SAFETY_R1",
]:
    if marker not in s:
        raise SystemExit(f"post-patch marker missing: {marker}")

for forbidden in [
    'id="hk-ex-run-limit"',
    'id="hk-ex-run-one"',
    "Лимит запуска E4",
    "Тест E3 · 1 здание",
    "Запустить E4",
    "s.runLimit",
    "settings.runLimit",
]:
    if forbidden in s:
        raise SystemExit(f"forbidden UI/redundant marker remains: {forbidden}")

PATH.write_text(s,encoding="utf-8")
print("EXPLORE_PRODUCTION_UI_R1_PATCH=PASS")
