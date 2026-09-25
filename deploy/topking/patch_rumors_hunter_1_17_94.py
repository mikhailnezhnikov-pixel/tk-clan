from pathlib import Path
import sys

target=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=target.read_text(encoding="utf-8")

def need(old,label,count=1):
    actual=s.count(old)
    if actual!=count:
        raise SystemExit(f"{label}: expected {count}, got {actual}")

def rep(old,new,label,count=1):
    global s
    need(old,label,count)
    s=s.replace(old,new,count)

rep(
    "// @version      1.17.93",
    "// @version      1.17.94\n"
    "// @release-note Слухи: добавлен отдельный экран «Охота за слухами» по канону Kokkaras, а на главной «Сегодня» — автоматический блок «Слухи сегодня». Маршрут берётся с HK backend, который синхронизирует публичный rumors.php Kokkaras; прямые gamearea_id используются без повторного перебора карт.",
    "metadata version"
)
rep("const BUILD_VERSION = '1.17.93';","const BUILD_VERSION = '1.17.94';","build version")

marker="  const RUMOR_API_BASE = 'https://hk-license.89.125.1.71.sslip.io/api/v1/rumors';"
rep(
    marker,
    marker+"\n  const HK_RUMORS_HUNTER_CANON_REV='rumors-hunter-kokkaras-public-feed-20260925-r1';",
    "rumors canon marker"
)

rep(
    "  let dailyRumorRoute = [];\n  let dailyAccountAreaIndex = [];",
    "  let dailyRumorRoute = [];\n  let dailyRumorMeta = {source:'',date:'',publishedAt:0,sourceUpdatedAt:''};\n  let dailyAccountAreaIndex = [];",
    "rumor state"
)

old_load='''  async function loadRumorRoute() {
    try {
      const result = await rumorServerJson('/today');
      dailyRumorRoute = Array.isArray(result.routes) ? result.routes : [];
      dailyAccountAreaIndex = [];
      if (dailyRumorRoute.length) {
        const points = dailyRumorRoute.reduce((sum,row)=>sum+(Array.isArray(row?.points)?row.points.length:0),0);
        log(either('Маршрут слухов загружен: ','Rumor route loaded: ') + dailyRumorRoute.length + either(' городов · ',' cities · ') + points + either(' точек',' points'),'ok');
      }
      return dailyRumorRoute;
    } catch (error) {
      dailyRumorRoute = [];
      dailyAccountAreaIndex = [];
      log(either('Ошибка маршрута слухов','Rumor route error') + ': ' + (error?.message || error),'warn');
      return dailyRumorRoute;
    }
  }'''
new_load='''  async function loadRumorRoute() {
    try {
      const result = await rumorServerJson('/today');
      dailyRumorRoute = Array.isArray(result.routes) ? result.routes : [];
      dailyRumorMeta = {
        source:String(result?.source||''),
        date:String(result?.date||''),
        publishedAt:Number(result?.published_at||0),
        sourceUpdatedAt:String(result?.source_updated_at||'')
      };
      dailyAccountAreaIndex = [];
      if (dailyRumorRoute.length) {
        const points = dailyRumorRoute.reduce((sum,row)=>sum+(Array.isArray(row?.points)?row.points.length:0),0);
        log(either('Маршрут слухов загружен: ','Rumor route loaded: ') + dailyRumorRoute.length + either(' городов · ',' cities · ') + points + either(' точек',' points') + ' · ' + rumorRouteSourceLabel(),'ok');
      }
      renderRumorsTodaySummary();
      renderRumorsPage();
      return dailyRumorRoute;
    } catch (error) {
      dailyRumorRoute = [];
      dailyRumorMeta = {source:'',date:'',publishedAt:0,sourceUpdatedAt:''};
      dailyAccountAreaIndex = [];
      renderRumorsTodaySummary();
      renderRumorsPage();
      log(either('Ошибка маршрута слухов','Rumor route error') + ': ' + (error?.message || error),'warn');
      return dailyRumorRoute;
    }
  }'''
rep(old_load,new_load,"loadRumorRoute")

anchor="  async function loadDailyAccountAreas() {"
module=r'''  function rumorRouteCityLabel(route) {
    const key=String(route?.city_key||'').trim();
    if(key){
      const translated=gameText(key);
      if(translated&&translated!==key)return String(translated);
    }
    return String(route?.city||key||either('Город','City'));
  }

  function rumorRoutePointIds(point) {
    const values=[];
    for(const id of (Array.isArray(point?.area_ids)?point.area_ids:[])){
      const value=String(id||'').trim();
      if(value&&!values.includes(value))values.push(value);
    }
    const direct=String(point?.gamearea_id||'').trim();
    if(direct&&!values.includes(direct))values.push(direct);
    return values;
  }

  function rumorRouteSourceLabel() {
    if(dailyRumorMeta.source==='kokkaras')return 'Kokkaras · live';
    if(dailyRumorMeta.source==='kokkaras-cache')return 'Kokkaras · cache';
    if(dailyRumorMeta.source==='local')return either('HK · локальный резерв','HK · local fallback');
    return either('источник не опубликован','source unavailable');
  }

  function rumorRouteUpdatedLabel() {
    const raw=dailyRumorMeta.sourceUpdatedAt;
    if(raw){
      const date=new Date(raw);
      if(!Number.isNaN(date.getTime()))return date.toLocaleString(locale(),{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'});
    }
    if(dailyRumorMeta.publishedAt){
      return new Date(dailyRumorMeta.publishedAt*1000).toLocaleString(locale(),{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'});
    }
    return '—';
  }

  function rumorRouteProgress(route) {
    const cityId=String(route?.city_id||'');
    const rumorState=playerDocument?.rumors||{};
    const cityRows=Array.isArray(rumorState?.city_rumors)?rumorState.city_rumors:[];
    const city=cityRows.find(row=>String(row?.city_id||'')===cityId);
    const cityCount=Math.max(0,Number(city?.jackpots_found||0));
    const researched=new Set((Array.isArray(rumorState?.researched_cells)?rumorState.researched_cells:[]).map(row=>String(row?.gamearea_id||'')));
    const pointCount=(route?.points||[]).filter(point=>rumorRoutePointIds(point).some(id=>researched.has(id))).length;
    const stored=load().today?.rumors?.[dailyCityKey(route?.city||route?.city_key||'')];
    const storedCount=stored?.periodStart===gamePeriodBounds().dayStart?Math.max(0,Number(stored?.completed||0)):0;
    return Math.min(3,Math.max(cityCount,pointCount,storedCount));
  }

  function rumorRoutesCopyText() {
    const date=dailyRumorMeta.date||new Date().toLocaleDateString('en-CA');
    const rows=[date,'■■■ RUMORS / СЛУХИ ■■■',''];
    for(const route of dailyRumorRoute){
      const coords=(route.points||[]).slice(0,3).map(point=>String(Number(point?.x)) + ':' + String(Number(point?.y)).padStart(2,'0')).join(' ');
      rows.push(rumorRouteCityLabel(route)+': '+coords);
    }
    rows.push('', '#rumors #слухи');
    return rows.join('\n');
  }

  async function copyRumorsToday() {
    const text=rumorRoutesCopyText();
    try{
      await navigator.clipboard.writeText(text);
      log(either('Слухи сегодня скопированы.','Today rumors copied.'),'ok');
    }catch(_){
      const area=document.createElement('textarea');
      area.value=text;area.style.position='fixed';area.style.opacity='0';
      document.body.appendChild(area);area.select();document.execCommand('copy');area.remove();
      log(either('Слухи сегодня скопированы.','Today rumors copied.'),'ok');
    }
  }

  function renderRumorsTodaySummary() {
    const host=root?.querySelector?.('#hk-rumors-today-summary');
    if(!host)return;
    const complete=dailyRumorRoute.filter(route=>rumorRouteProgress(route)>=3).length;
    const total=dailyRumorRoute.length;
    const points=dailyRumorRoute.reduce((sum,row)=>sum+(row?.points?.length||0),0);
    host.innerHTML=`
      <div class="hk-rumor-summary-head"><div><h3>${either('Слухи сегодня','Rumors today')}</h3><small>${escapeHtml(rumorRouteSourceLabel())} · ${escapeHtml(rumorRouteUpdatedLabel())}</small></div><b>${complete}/${total||17}</b></div>
      <div class="hk-rumor-summary-meta"><span>${either('Городов','Cities')}: <b>${total||'—'}</b></span><span>${either('Точек','Points')}: <b>${points||'—'}</b></span></div>
      <div class="hk-rumor-summary-actions"><button type="button" id="hk-rumors-summary-open" class="hk-primary">${either('Открыть охоту','Open hunter')}</button><button type="button" id="hk-rumors-summary-refresh" class="hk-secondary">${either('Обновить','Refresh')}</button></div>`;
    host.querySelector('#hk-rumors-summary-open')?.addEventListener('click',()=>runtime.navigate?.('rumors'));
    host.querySelector('#hk-rumors-summary-refresh')?.addEventListener('click',()=>void refreshRumorsPage());
  }

  function renderRumorsPage() {
    if(!rumorBox)return;
    const complete=dailyRumorRoute.filter(route=>rumorRouteProgress(route)>=3).length;
    const total=dailyRumorRoute.length;
    const cards=total?dailyRumorRoute.map(route=>{
      const progress=rumorRouteProgress(route);
      const points=(route.points||[]).map((point,index)=>{
        const coord=String(Number(point?.x))+':'+String(Number(point?.y)).padStart(2,'0');
        const direct=rumorRoutePointIds(point).length?either('готовый ID','direct ID'):either('по карте','via map');
        return `<span class="hk-rumor-point ${index<progress?'done':''}"><b>${escapeHtml(coord)}</b><small>${escapeHtml(direct)}</small></span>`;
      }).join('');
      return `<article class="hk-rumor-city ${progress>=3?'done':''}"><div><b>${escapeHtml(rumorRouteCityLabel(route))}</b><span>${progress}/3</span></div><div class="hk-rumor-points">${points}</div></article>`;
    }).join(''):`<p class="hk-muted">${either('Маршрут слухов пока не загружен.','Rumor route is not loaded yet.')}</p>`;

    rumorBox.innerHTML=`
      <div class="hk-rumor-hero"><div><h3>${either('Охота за слухами','Rumors Hunter')}</h3><p>${either('Канонический маршрут Kokkaras подгружается автоматически. Если Kokkaras уже нашёл слухи, HK использует готовые gamearea ID и не ищет эти координаты вслепую.','The canonical Kokkaras route loads automatically. When Kokkaras already has results, HK uses the direct gamearea IDs instead of rediscovering coordinates blindly.')}</p></div><div class="hk-rumor-source"><b>${escapeHtml(rumorRouteSourceLabel())}</b><small>${escapeHtml(rumorRouteUpdatedLabel())}</small></div></div>
      <div class="hk-rumor-stats"><span>${either('Готово','Done')} <b>${complete}/${total||17}</b></span><span>${either('Маршрут','Route')} <b>${total||0}</b></span></div>
      <div class="hk-rumor-actions"><button type="button" id="hk-rumors-start" class="hk-primary" ${total?'':'disabled'}>${either('Начать охоту','Start hunting')}</button><button type="button" id="hk-rumors-refresh" class="hk-secondary">${either('Обновить','Refresh')}</button><button type="button" id="hk-rumors-copy">${either('Копировать слухи','Copy rumors')}</button></div>
      <div class="hk-rumor-grid">${cards}</div>`;
    rumorBox.querySelector('#hk-rumors-start')?.addEventListener('click',()=>void runDailyRumors(false));
    rumorBox.querySelector('#hk-rumors-refresh')?.addEventListener('click',()=>void refreshRumorsPage());
    rumorBox.querySelector('#hk-rumors-copy')?.addEventListener('click',()=>void copyRumorsToday());
  }

  async function refreshRumorsPage() {
    if(rumorBox)rumorBox.innerHTML=`<p class="hk-muted">${either('Обновляю слухи…','Refreshing rumors…')}</p>`;
    await loadRumorRoute();
    renderRumorsTodaySummary();
    renderRumorsPage();
  }

'''
s=s.replace(anchor,module+anchor,1)

# Prefer direct Kokkaras gamearea ids and skip city-grid discovery when every point already has one.
old_maps="      const maps = await loadDailyAccountAreas();"
new_maps="""      const hasDirectRoute=dailyRumorRoute.every(route=>(route?.points||[]).every(point=>rumorRoutePointIds(point).length));
      const maps = hasDirectRoute ? [] : await loadDailyAccountAreas();"""
rep(old_maps,new_maps,"direct rumor route")

old_area="""          const area = dailyMapArea(maps,route.city,point);
          const ids = area?.area_id ? [String(area.area_id)] : [];"""
new_area="""          const directIds=rumorRoutePointIds(point);
          const area = directIds.length ? null : dailyMapArea(maps,route.city,point);
          const ids = directIds.length ? directIds : (area?.area_id ? [String(area.area_id)] : []);"""
rep(old_area,new_area,"direct gamearea ids")

# Use localized city labels in rumor logs.
s=s.replace("route.city + ' [' + point.x + ':' + point.y + ']'", "rumorRouteCityLabel(route) + ' [' + point.x + ':' + point.y + ']'")
s=s.replace("'↷ ' + route.city + ' — '", "'↷ ' + rumorRouteCityLabel(route) + ' — '")

# Main Today navigation gets a separate Rumors module.
old_nav="{id:'today',label:'navToday',hint:'navTodayHint',image:'today.png',modules:[{page:'daily',ru:'Сегодня',en:'Today'}]},"
new_nav="{id:'today',label:'navToday',hint:'navTodayHint',image:'today.png',modules:[{page:'daily',ru:'Сегодня',en:'Today'},{page:'rumors',ru:'Слухи',en:'Rumors'}]},"
rep(old_nav,new_nav,"today rumor nav")

# Separate summary card on Today and a dedicated Rumors page.
old_daily='''      <div class="hk-page active" data-content="daily">
        <div class="hk-cardbox"><h3 data-i18n="dailyTasks">${tr('dailyTasks')}</h3><div id="hk-daily-tasks"></div><button id="hk-daily-run" class="hk-primary" data-i18n="dailyRun" disabled>${tr('dailyRun')}</button></div>
        <div id="hk-routines-content" class="hk-cardbox" style="margin-top:12px"></div>
      </div>'''
new_daily='''      <div class="hk-page active" data-content="daily">
        <div id="hk-rumors-today-summary" class="hk-cardbox hk-rumor-summary"></div>
        <div class="hk-cardbox" style="margin-top:12px"><h3 data-i18n="dailyTasks">${tr('dailyTasks')}</h3><div id="hk-daily-tasks"></div><button id="hk-daily-run" class="hk-primary" data-i18n="dailyRun" disabled>${tr('dailyRun')}</button></div>
        <div id="hk-routines-content" class="hk-cardbox" style="margin-top:12px"></div>
      </div>
      <div class="hk-page" data-content="rumors">
        <div id="hk-rumors-content" class="hk-cardbox"></div>
      </div>'''
rep(old_daily,new_daily,"rumors page markup")

# UI state reference.
old_vars="let root, panel, statusLine, logBox, businessLists, planBox, presetSelect, fairTypes, fairLots, fairSlotRules, fairPresetSelect, shopCards, shopSummary, recipeCards, recipeSummary, recipeDatabaseBox, bureauCards, bureauSummary, mapIndexBox, mapDetailBox, dailyBox, clanBox, resourceBox;"
new_vars="let root, panel, statusLine, logBox, businessLists, planBox, presetSelect, fairTypes, fairLots, fairSlotRules, fairPresetSelect, shopCards, shopSummary, recipeCards, recipeSummary, recipeDatabaseBox, bureauCards, bureauSummary, mapIndexBox, mapDetailBox, dailyBox, rumorBox, clanBox, resourceBox;"
rep(old_vars,new_vars,"rumorBox variable")

old_assign="dailyBox = root.querySelector('#hk-daily-tasks'); clanBox = root.querySelector('#hk-clan-content'); resourceBox = root.querySelector('#hk-resource-content');"
new_assign="dailyBox = root.querySelector('#hk-daily-tasks'); rumorBox = root.querySelector('#hk-rumors-content'); clanBox = root.querySelector('#hk-clan-content'); resourceBox = root.querySelector('#hk-resource-content');"
rep(old_assign,new_assign,"rumorBox assignment")

# Render summary whenever Today is rendered.
rep("  function renderDailyTasks() {\n    if (!dailyBox) return;",
    "  function renderDailyTasks() {\n    renderRumorsTodaySummary();\n    if (!dailyBox) return;",
    "today rumors summary render")

# Page activation.
rep("      if (finalPage === 'daily') { renderDailyTasks(); renderAutoRoutines(); }",
    "      if (finalPage === 'daily') { renderDailyTasks(); renderAutoRoutines(); if(!dailyRumorRoute.length)void loadRumorRoute(); }\n      if (finalPage === 'rumors') { renderRumorsPage(); if(!dailyRumorRoute.length)void refreshRumorsPage(); }",
    "rumors page activation")

# CSS.
css_anchor="      @media(max-width:620px){.hk-map-row{grid-template-columns:1fr 45px 54px}"
require_css=css_anchor in s
if not require_css:
    raise SystemExit("CSS anchor missing")
rumor_css="""
      .hk-rumor-summary{margin-bottom:12px}.hk-rumor-summary-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}.hk-rumor-summary-head h3{margin:0 0 4px}.hk-rumor-summary-head small{color:#8fa1b8}.hk-rumor-summary-head>b{font-size:20px;color:#ffd166}.hk-rumor-summary-meta{display:flex;gap:8px;margin:10px 0}.hk-rumor-summary-meta span,.hk-rumor-stats span{padding:7px 9px;border:1px solid #304057;border-radius:10px;background:#101927;color:#9fb0c6}.hk-rumor-summary-actions,.hk-rumor-actions{display:flex;gap:7px;flex-wrap:wrap}.hk-rumor-summary-actions button,.hk-rumor-actions button{flex:1;min-width:120px}.hk-rumor-hero{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.hk-rumor-hero h3{margin:0}.hk-rumor-hero p{margin:5px 0 0;color:#93a3b8;line-height:1.4;max-width:760px}.hk-rumor-source{flex:0 0 auto;text-align:right;padding:8px 10px;border:1px solid #30506b;border-radius:11px;background:#0d1722}.hk-rumor-source b,.hk-rumor-source small{display:block}.hk-rumor-source b{color:#7fe0ad}.hk-rumor-source small{margin-top:3px;color:#8192a8}.hk-rumor-stats{display:flex;gap:8px;margin:12px 0}.hk-rumor-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-top:12px}.hk-rumor-city{padding:10px;border:1px solid #304057;border-radius:12px;background:#101927}.hk-rumor-city.done{border-color:#2c7457;background:#10211c}.hk-rumor-city>div:first-child{display:flex;justify-content:space-between;gap:8px}.hk-rumor-city>div:first-child span{color:#ffd166;font-weight:900}.hk-rumor-points{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}.hk-rumor-point{display:grid;padding:6px 8px;border:1px solid #293a50;border-radius:9px;background:#0c1420;min-width:64px}.hk-rumor-point b{font:800 11px ui-monospace,monospace}.hk-rumor-point small{margin-top:2px;color:#74869c;font-size:8px}.hk-rumor-point.done{border-color:#2e7058;background:#10231d}.hk-rumor-point.done b{color:#7fe0ad}@media(max-width:720px){.hk-rumor-grid{grid-template-columns:1fr}.hk-rumor-hero{display:block}.hk-rumor-source{margin-top:9px;text-align:left}}
"""
s=s.replace(css_anchor,rumor_css+css_anchor,1)

for marker in [
    "// @version      1.17.94",
    "const BUILD_VERSION = '1.17.94';",
    "rumors-hunter-kokkaras-public-feed-20260925-r1",
    "function renderRumorsPage()",
    "function renderRumorsTodaySummary()",
    "data-content=\"rumors\"",
    "page:'rumors',ru:'Слухи'",
    "rumorRoutePointIds(point)",
    "Kokkaras · live",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

target.write_text(s,encoding="utf-8")
print("RUMORS_HUNTER_1_17_94=PASS")
