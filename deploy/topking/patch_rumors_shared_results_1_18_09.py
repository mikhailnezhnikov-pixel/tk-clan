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
    "// @version      1.18.08",
    "// @version      1.18.09\n"
    "// @release-note Слухи: «Слухи сегодня» теперь автоматически обновляются каждые 30 секунд из публичного Kokkaras feed и общих результатов HK, показывают координаты прямо на главном экране; подтверждённые джекпоты, собранные через HK, публикуются в общую базу.",
    "metadata version"
)
rep("const BUILD_VERSION = '1.18.08';","const BUILD_VERSION = '1.18.09';","build version")

marker="  const HK_RUMORS_HUNTER_CANON_REV='rumors-hunter-kokkaras-public-feed-20260925-r1';"
rep(marker,marker+"\n  const HK_RUMORS_SHARED_RESULTS_REV='rumors-shared-results-20260926-r2';\n  const RUMOR_AUTO_REFRESH_MS=30*1000;","rumors shared marker")

rep(
    "  let dailyRumorRoute = [];\n  let dailyRumorMeta = {source:'',date:'',publishedAt:0,sourceUpdatedAt:''};\n  let dailyAccountAreaIndex = [];",
    "  let dailyRumorRoute = [];\n  let dailyRumorMeta = {source:'',date:'',publishedAt:0,sourceUpdatedAt:''};\n  let dailyAccountAreaIndex = [];\n  let rumorAutoRefreshTimer = null;\n  let rumorRouteFingerprint = '';",
    "rumor auto-refresh state"
)

source_fn='''  function rumorRouteSourceLabel() {
    if(dailyRumorMeta.source==='kokkaras')return 'Kokkaras · live';
    if(dailyRumorMeta.source==='kokkaras-cache')return 'Kokkaras · cache';
    if(dailyRumorMeta.source==='local')return either('HK · локальный резерв','HK · local fallback');
    return either('источник не опубликован','source unavailable');
  }
'''
source_new='''  function rumorRouteSourceLabel() {
    if(dailyRumorMeta.source==='kokkaras')return 'Kokkaras · live';
    if(dailyRumorMeta.source==='kokkaras+hk')return 'Kokkaras + HK · live';
    if(dailyRumorMeta.source==='kokkaras-cache')return 'Kokkaras · cache';
    if(dailyRumorMeta.source==='kokkaras-cache+hk')return 'Kokkaras + HK · cache';
    if(dailyRumorMeta.source==='hk')return either('HK · общая база','HK · shared results');
    if(dailyRumorMeta.source==='local')return either('HK · локальный резерв','HK · local fallback');
    if(dailyRumorMeta.source==='local+hk')return either('HK · резерв + общая база','HK · fallback + shared');
    return either('источник не опубликован','source unavailable');
  }
'''
rep(source_fn,source_new,"rumor source labels")

anchor="  function rumorRouteUpdatedLabel() {"
module=r'''  function rumorRouteSignature(value=dailyRumorRoute,meta=dailyRumorMeta) {
    try{
      return JSON.stringify({
        source:String(meta?.source||''),
        date:String(meta?.date||''),
        updated:String(meta?.sourceUpdatedAt||meta?.publishedAt||''),
        routes:(value||[]).map(route=>({
          city_id:String(route?.city_id||''),
          points:(route?.points||[]).map(point=>[Number(point?.x),Number(point?.y),String(point?.gamearea_id||'')])
        }))
      });
    }catch(_){return '';}
  }

  function rumorApplyRoutePayload(result,{quiet=false}={}) {
    const routes=Array.isArray(result?.routes)?result.routes:[];
    const meta={
      source:String(result?.source||''),
      date:String(result?.date||''),
      publishedAt:Number(result?.published_at||0),
      sourceUpdatedAt:String(result?.source_updated_at||'')
    };
    const nextFingerprint=rumorRouteSignature(routes,meta);
    const changed=nextFingerprint!==rumorRouteFingerprint;
    dailyRumorRoute=routes;
    dailyRumorMeta=meta;
    rumorRouteFingerprint=nextFingerprint;
    dailyAccountAreaIndex=[];
    renderRumorsTodaySummary();
    renderRumorsPage();
    if(changed&&!quiet&&dailyRumorRoute.length){
      const points=dailyRumorRoute.reduce((sum,row)=>sum+(Array.isArray(row?.points)?row.points.length:0),0);
      log(either('Маршрут слухов загружен: ','Rumor route loaded: ')+dailyRumorRoute.length+either(' городов · ',' cities · ')+points+either(' точек',' points')+' · '+rumorRouteSourceLabel(),'ok');
    }
    return changed;
  }

  async function refreshRumorRouteQuietly() {
    try{
      const result=await rumorServerJson('/today');
      rumorApplyRoutePayload(result,{quiet:true});
      return true;
    }catch(error){
      recordDiagnostic('rumors-auto-refresh-error',{message:String(error?.message||error||'').slice(0,500)});
      return false;
    }
  }

  function scheduleRumorAutoRefresh() {
    if(rumorAutoRefreshTimer)return;
    rumorAutoRefreshTimer=setTimeout(async()=>{
      rumorAutoRefreshTimer=null;
      try{
        const active=hkPanelOpen()&&['daily','rumors'].includes(hkActiveModule());
        if(active)await refreshRumorRouteQuietly();
      }finally{
        scheduleRumorAutoRefresh();
      }
    },RUMOR_AUTO_REFRESH_MS);
  }

  function rumorJackpotIdFromResponse(response,gameareaId) {
    const rows=Array.isArray(response?.rumors?.researched_cells)?response.rumors.researched_cells:[];
    for(let i=rows.length-1;i>=0;i--){
      const row=rows[i];
      if(String(row?.gamearea_id||'')!==String(gameareaId||''))continue;
      const rumorId=String(row?.rumor_id||'');
      return /jackpot/i.test(rumorId)?rumorId:'';
    }
    const direct=String(response?.rumor_id||'');
    return /jackpot/i.test(direct)?direct:'';
  }

  async function reportRumorJackpot(route,point,gameareaId,response) {
    const rumorId=rumorJackpotIdFromResponse(response,gameareaId);
    if(!rumorId)return false;
    try{
      await rumorServerJson('/report',{
        city_id:String(route?.city_id||''),
        city_key:String(route?.city_key||''),
        city_name:rumorRouteCityLabel(route),
        x:Number(point?.x),
        y:Number(point?.y),
        gamearea_id:String(gameareaId||''),
        rumor_id:rumorId
      },false);
      return true;
    }catch(error){
      recordDiagnostic('rumors-report-error',{city_id:String(route?.city_id||''),gamearea_id:String(gameareaId||''),message:String(error?.message||error||'').slice(0,500)});
      return false;
    }
  }

'''
s=s.replace(anchor,module+anchor,1)

# Reuse centralized payload application.
old_load_success='''      dailyRumorRoute = Array.isArray(result.routes) ? result.routes : [];
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
      return dailyRumorRoute;'''
new_load_success='''      rumorApplyRoutePayload(result,{quiet:false});
      scheduleRumorAutoRefresh();
      return dailyRumorRoute;'''
rep(old_load_success,new_load_success,"load route shared apply")

# Summary now exposes today's coordinates directly.
old_summary='''    host.innerHTML=`
      <div class="hk-rumor-summary-head"><div><h3>${either('Слухи сегодня','Rumors today')}</h3><small>${escapeHtml(rumorRouteSourceLabel())} · ${escapeHtml(rumorRouteUpdatedLabel())}</small></div><b>${complete}/${total||17}</b></div>
      <div class="hk-rumor-summary-meta"><span>${either('Городов','Cities')}: <b>${total||'—'}</b></span><span>${either('Точек','Points')}: <b>${points||'—'}</b></span></div>
      <div class="hk-rumor-summary-actions"><button type="button" id="hk-rumors-summary-open" class="hk-primary">${either('Открыть охоту','Open hunter')}</button><button type="button" id="hk-rumors-summary-refresh" class="hk-secondary">${either('Обновить','Refresh')}</button></div>`;'''
new_summary='''    const routePreview=total?dailyRumorRoute.map(route=>{
      const coords=(route?.points||[]).map(point=>String(Number(point?.x))+':'+String(Number(point?.y)).padStart(2,'0')).join(' · ');
      return `<div class="hk-rumor-summary-route"><b>${escapeHtml(rumorRouteCityLabel(route))}</b><span>${escapeHtml(coords||'—')}</span></div>`;
    }).join(''):`<span class="hk-muted">${either('Координаты ещё не опубликованы.','Coordinates are not published yet.')}</span>`;
    host.innerHTML=`
      <div class="hk-rumor-summary-head"><div><h3>${either('Слухи сегодня','Rumors today')}</h3><small>${escapeHtml(rumorRouteSourceLabel())} · ${escapeHtml(rumorRouteUpdatedLabel())} · ${either('автообновление 30 сек.','auto refresh 30 sec.')}</small></div><b>${complete}/${total||17}</b></div>
      <div class="hk-rumor-summary-meta"><span>${either('Городов','Cities')}: <b>${total||'—'}</b></span><span>${either('Точек','Points')}: <b>${points||'—'}</b></span></div>
      <details class="hk-rumor-summary-routes" open><summary>${either('Координаты сегодня','Today coordinates')}</summary><div>${routePreview}</div></details>
      <div class="hk-rumor-summary-actions"><button type="button" id="hk-rumors-summary-open" class="hk-primary">${either('Открыть охоту','Open hunter')}</button><button type="button" id="hk-rumors-summary-refresh" class="hk-secondary">${either('Обновить','Refresh')}</button></div>`;'''
rep(old_summary,new_summary,"rumor today coordinate summary")

# Ensure polling starts whenever either Rumors surface renders.
rep(
    "  function renderRumorsTodaySummary() {\n    const host=root?.querySelector?.('#hk-rumors-today-summary');",
    "  function renderRumorsTodaySummary() {\n    scheduleRumorAutoRefresh();\n    const host=root?.querySelector?.('#hk-rumors-today-summary');",
    "summary auto-refresh schedule"
)
rep(
    "  function renderRumorsPage() {\n    if(!rumorBox)return;",
    "  function renderRumorsPage() {\n    scheduleRumorAutoRefresh();\n    if(!rumorBox)return;",
    "page auto-refresh schedule"
)

# Publish confirmed HK jackpot results after game mutation.
old_search="              playerDocument = await apiJson('/rumors/search','POST',{gamearea_id:gameareaId});\n              collected++; completed++; cityCollected++; cityCompleted++; checked++; searched = true;"
new_search="              playerDocument = await apiJson('/rumors/search','POST',{gamearea_id:gameareaId});\n              void reportRumorJackpot(route,point,gameareaId,playerDocument);\n              collected++; completed++; cityCollected++; cityCompleted++; checked++; searched = true;"
rep(old_search,new_search,"report collected jackpot")

# CSS for Today coordinate list.
css_anchor=".hk-rumor-summary-actions,.hk-rumor-actions{display:flex;gap:7px;flex-wrap:wrap}"
need(css_anchor,"rumor CSS anchor")
s=s.replace(css_anchor,".hk-rumor-summary-routes{margin:10px 0;border:1px solid #2c3c50;border-radius:11px;background:#0d1621}.hk-rumor-summary-routes>summary{padding:9px 10px;cursor:pointer;font-weight:800}.hk-rumor-summary-routes>div{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:5px;padding:0 8px 8px}.hk-rumor-summary-route{display:flex;justify-content:space-between;gap:7px;padding:6px 7px;border:1px solid #26364a;border-radius:8px;background:#101927}.hk-rumor-summary-route b{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.hk-rumor-summary-route span{font:800 10px ui-monospace,monospace;color:#ffd166;white-space:nowrap}.hk-rumor-summary-actions,.hk-rumor-actions{display:flex;gap:7px;flex-wrap:wrap}",1)

mobile_anchor="@media(max-width:720px){.hk-rumor-grid{grid-template-columns:1fr}"
need(mobile_anchor,"rumor mobile CSS")
s=s.replace(mobile_anchor,"@media(max-width:720px){.hk-rumor-summary-routes>div{grid-template-columns:1fr}.hk-rumor-grid{grid-template-columns:1fr}",1)

for marker in [
    "// @version      1.18.09",
    "const BUILD_VERSION = '1.18.09';",
    "rumors-shared-results-20260926-r2",
    "const RUMOR_AUTO_REFRESH_MS=30*1000;",
    "async function refreshRumorRouteQuietly()",
    "async function reportRumorJackpot",
    "void reportRumorJackpot(route,point,gameareaId,playerDocument);",
    "Координаты сегодня",
    "автообновление 30 сек.",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

target.write_text(s,encoding="utf-8")
print("RUMORS_SHARED_RESULTS_1_18_09=PASS")
print("version=1.18.09")
