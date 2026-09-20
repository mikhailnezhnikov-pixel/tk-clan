from pathlib import Path

p=Path('/tmp/HamsterKingMobile.user.js')
s=p.read_text(encoding='utf-8')
marker="const HK_TODAY_TOOLBAR_REV = 'today-toolbar-clean-20260920-r3';"
if marker in s: raise SystemExit('already applied')
anchor="  const HK_TODAY_CANON_FILTER_REV = 'today-kokkaras-filter-20260920-r2';\n"
if anchor not in s: raise SystemExit('r2 marker missing')
s=s.replace(anchor,anchor+'  '+marker+'\n',1)

old='''        <div class="hk-cardbox"><h3 data-i18n="dailyTasks">${tr('dailyTasks')}</h3><div class="hk-toolbar"><button id="hk-daily-refresh" class="hk-secondary" data-i18n="dailyRefresh">${tr('dailyRefresh')}</button><button id="hk-daily-clear" data-i18n="dailyClear">${tr('dailyClear')}</button></div><div id="hk-daily-tasks"></div><button id="hk-daily-run" class="hk-primary" data-i18n="dailyRun" disabled>${tr('dailyRun')}</button></div>'''
new='''        <div class="hk-cardbox"><h3 data-i18n="dailyTasks">${tr('dailyTasks')}</h3><div id="hk-daily-tasks"></div><button id="hk-daily-run" class="hk-primary" data-i18n="dailyRun" disabled>${tr('dailyRun')}</button></div>'''
if old not in s: raise SystemExit('Today toolbar HTML anchor missing')
s=s.replace(old,new,1)

for oldline in [
    "    root.querySelector('#hk-daily-refresh').onclick = () => refreshModuleLive('daily',{force:true});\n",
    "    root.querySelector('#hk-daily-clear').onclick = () => { if (logBox) logBox.innerHTML = ''; if (statusLine) statusLine.textContent = tr('dailyReady'); };\n"
]:
    if oldline not in s: raise SystemExit('listener anchor missing: '+oldline.strip())
    s=s.replace(oldline,'',1)

if "refreshModuleLive(finalPage)" not in s: raise SystemExit('auto refresh path missing')
if "if (finalPage === 'daily') renderDailyTasks();" not in s: raise SystemExit('daily open path missing')
for forbidden in ['id="hk-daily-refresh"','id="hk-daily-clear"',"querySelector('#hk-daily-refresh')","querySelector('#hk-daily-clear')"]:
    if forbidden in s: raise SystemExit('toolbar residue: '+forbidden)

p.write_text(s,encoding='utf-8')
print('TODAY_TOOLBAR_R3_OK')
