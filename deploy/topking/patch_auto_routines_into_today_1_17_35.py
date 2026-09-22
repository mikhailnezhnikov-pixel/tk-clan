from pathlib import Path

PATH=Path("/tmp/HamsterKingMobile.user.js")
s=PATH.read_text(encoding="utf-8")
MARKER="auto-routines-in-today-20260922-r3"

if MARKER in s:
    print("AUTO_ROUTINES_IN_TODAY_ALREADY_PRESENT")
    raise SystemExit(0)

for required in [
    "// @version      1.17.34",
    "const BUILD_VERSION = '1.17.34';",
    "auto-routines-safe-orchestrator-20260922-r2",
    "clan-shop-dom-history-capture-20260922-r3",
    "game-api-rate-guard-20260922-r1",
    "public-collector-activity-lease-20260922-r1",
    "{page:'routines',ru:'Авто-рутины',en:'Auto routines'}",
    'data-content="routines"',
    'id="hk-routines-content"',
]:
    if required not in s:
        raise SystemExit("missing marker: "+required)

s=s.replace("// @version      1.17.34","// @version      1.17.35",1)
s=s.replace("const BUILD_VERSION = '1.17.34';","const BUILD_VERSION = '1.17.35';",1)

release_anchor="// @release-note Auto Routines теперь fail-closed: следующий этап запускается только после реального Runner=done; error/stop/cancel/no-op останавливают цепочку. Collector lease удерживается непрерывно на всю рутину."
release_new="// @release-note Авто-рутины перенесены внутрь «Сегодня»: отдельная вкладка убрана, сохранённый выбор и fail-closed логика сохранены; старый navModule=routines автоматически мигрирует на daily."
if release_anchor not in s:
    raise SystemExit("release anchor missing")
s=s.replace(release_anchor,release_new+"\n"+release_anchor,1)

rev_anchor="  const HK_AUTO_ROUTINES_SAFE_REV = 'auto-routines-safe-orchestrator-20260922-r2';"
if rev_anchor not in s:
    raise SystemExit("auto routine safe revision anchor missing")
s=s.replace(rev_anchor,rev_anchor+"\n  const HK_AUTO_ROUTINES_TODAY_REV = 'auto-routines-in-today-20260922-r3';",1)

nav_old="{id:'business',label:'navBusiness',hint:'navBusinessHint',image:'businesses.png',modules:[{page:'business',ru:'Бизнесы',en:'Businesses'},{page:'recipes',ru:'Рецепты',en:'Recipes'},{page:'routines',ru:'Авто-рутины',en:'Auto routines'}]}"
nav_new="{id:'business',label:'navBusiness',hint:'navBusinessHint',image:'businesses.png',modules:[{page:'business',ru:'Бизнесы',en:'Businesses'},{page:'recipes',ru:'Рецепты',en:'Recipes'}]}"
if nav_old not in s:
    raise SystemExit("business nav routines anchor missing")
s=s.replace(nav_old,nav_new,1)

daily_old='''      <div class="hk-page active" data-content="daily">
        <div class="hk-cardbox"><h3 data-i18n="dailyTasks">\${tr('dailyTasks')}</h3><div id="hk-daily-tasks"></div><button id="hk-daily-run" class="hk-primary" data-i18n="dailyRun" disabled>\${tr('dailyRun')}</button></div>
      </div>
'''
daily_new='''      <div class="hk-page active" data-content="daily">
        <div class="hk-cardbox"><h3 data-i18n="dailyTasks">\${tr('dailyTasks')}</h3><div id="hk-daily-tasks"></div><button id="hk-daily-run" class="hk-primary" data-i18n="dailyRun" disabled>\${tr('dailyRun')}</button></div>
        <div id="hk-routines-content" class="hk-cardbox" style="margin-top:12px"></div>
      </div>
'''
if daily_old not in s:
    raise SystemExit("daily page anchor missing")
s=s.replace(daily_old,daily_new,1)

routines_page='''      <div class="hk-page" data-content="routines">
        <div id="hk-routines-content" class="hk-cardbox"></div>
      </div>
'''
if routines_page not in s:
    raise SystemExit("standalone routines page missing")
s=s.replace(routines_page,"",1)

activate_old="      if (finalPage === 'daily') renderDailyTasks();"
activate_new="      if (finalPage === 'daily') { renderDailyTasks(); renderAutoRoutines(); }"
if activate_old not in s:
    raise SystemExit("daily activation anchor missing")
s=s.replace(activate_old,activate_new,1)

if "      if (finalPage === 'routines') renderAutoRoutines();\n" not in s:
    raise SystemExit("standalone routines render anchor missing")
s=s.replace("      if (finalPage === 'routines') renderAutoRoutines();\n","",1)

old_refresh="""      if (finalPage.startsWith('growth')) { renderGrowth(); growthAutoOpen(finalPage); }
      else if (finalPage !== 'routines') void refreshModuleLive(finalPage);"""
new_refresh="""      if (finalPage.startsWith('growth')) { renderGrowth(); growthAutoOpen(finalPage); }
      else void refreshModuleLive(finalPage);"""
if old_refresh not in s:
    raise SystemExit("routines refresh exception anchor missing")
s=s.replace(old_refresh,new_refresh,1)

remember_old='''    const remembered=clean(load().navModule||'daily');
    activateModule(remembered === 'fair-regular' || root.querySelector(\`[data-content="\${remembered}"]\`) ? remembered : 'daily',false);'''
remember_new='''    const rememberedRaw=clean(load().navModule||'daily');
    const remembered=rememberedRaw==='routines'?'daily':rememberedRaw;
    if(rememberedRaw==='routines')save({navGroup:'today',navModule:'daily'});
    activateModule(remembered === 'fair-regular' || root.querySelector(\`[data-content="\${remembered}"]\`) ? remembered : 'daily',false);'''
if remember_old not in s:
    raise SystemExit("remembered navigation anchor missing")
s=s.replace(remember_old,remember_new,1)

for marker in [
    "// @version      1.17.35",
    "const BUILD_VERSION = '1.17.35';",
    "HK_AUTO_ROUTINES_TODAY_REV = 'auto-routines-in-today-20260922-r3'",
    "{page:'business',ru:'Бизнесы',en:'Businesses'},{page:'recipes',ru:'Рецепты',en:'Recipes'}",
    '<div id="hk-routines-content" class="hk-cardbox" style="margin-top:12px"></div>',
    "if (finalPage === 'daily') { renderDailyTasks(); renderAutoRoutines(); }",
    "rememberedRaw==='routines'?'daily':rememberedRaw",
    "auto-routines-safe-orchestrator-20260922-r2",
    "clan-shop-dom-history-capture-20260922-r3",
]:
    if marker not in s:
        raise SystemExit("post-patch marker missing: "+marker)

if "{page:'routines',ru:'Авто-рутины',en:'Auto routines'}" in s:
    raise SystemExit("routines nav still present")
if 'data-content="routines"' in s:
    raise SystemExit("standalone routines page still present")
if s.count('id="hk-routines-content"') != 1:
    raise SystemExit("unexpected routines content count")

PATH.write_text(s,encoding="utf-8")
print("AUTO_ROUTINES_IN_TODAY_R3=PASS")
