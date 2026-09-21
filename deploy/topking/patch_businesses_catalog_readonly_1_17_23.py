from pathlib import Path
import re

PATH=Path("/tmp/HamsterKingMobile.user.js")
s=PATH.read_text(encoding="utf-8")

for marker in [
    "// @version      1.17.22",
    "const BUILD_VERSION = '1.17.22';",
    "const HK_CORE_REVISION = 'core-20260921-r24-explore-production-ui';",
    "let businessBusy = false;",
    "function refreshBusinessData()",
    "function businessCardDetails(businessId)",
    "function businessActiveLimit(businessId)",
    "async function ensureRecipeMetadata()",
]:
    if marker not in s:
        raise SystemExit("missing expected marker: "+marker)

s=s.replace("// @version      1.17.22","// @version      1.17.23",1)
s=s.replace("const BUILD_VERSION = '1.17.22';","const BUILD_VERSION = '1.17.23';",1)
s=s.replace("const HK_CORE_REVISION = 'core-20260921-r24-explore-production-ui';",
            "const HK_CORE_REVISION = 'core-20260921-r25-businesses-catalog';",1)
s=s.replace("const HK_EXPLORE_UI_REV='explore-production-ui-20260921-r1';",
            "const HK_EXPLORE_UI_REV='explore-production-ui-20260921-r1';\n  const HK_BUSINESSES_CANON_REV='businesses-catalog-readonly-20260921-r1';",1)

release="// @release-note Упрощён экран исследования: убраны тестовая кнопка и дублирующий лимит; очередь использует «Максимум зданий»."
if release in s:
    s=s.replace(release,
        "// @release-note В «Бизнесы» добавлен read-only каталог: поиск, фильтры бонусов, лимиты, наличие и известные рецепты.\n"+release,1)

s=s.replace("  let businessBusy = false;",
"""  let businessBusy = false;
  let businessCatalogSearch = '';
  let businessCatalogBonus = '';
  let businessCatalogExactBonusOnly = false;
  let businessCatalogTargetId = '';
  let businessCatalogTargetQuantity = 1;
  let businessCatalogLoading = false;
  let businessCatalogRoutesLoaded = false;""",1)

# Translation labels.
s=s.replace("businessRegular:'Обычная перестановка', businessOptimizer:'Оптимизатор',",
            "businessRegular:'Обычная перестановка', businessOptimizer:'Оптимизатор', businessCatalog:'Каталог',",1)
s=s.replace("businessRegular:'Manual rearrangement', businessOptimizer:'Optimizer',",
            "businessRegular:'Manual rearrangement', businessOptimizer:'Optimizer', businessCatalog:'Catalog',",1)

anchor="  function businessSelectionCount() {"
if anchor not in s:
    raise SystemExit("catalog insertion anchor missing")

catalog=r'''  function businessCatalogOwnedCount(businessId, documentValue = playerDocument) {
    const id=String(businessId||''); if(!id)return 0;
    let count=0;
    for(const item of documentValue?.items||[]){
      if(String(item?.item_id||'')===id)count+=Math.max(0,Number(item?.quantity||0));
    }
    for(const building of findBuildings(documentValue)||[]){
      for(const slot of building?.active_business||[]){
        const qty=Math.max(1,Number(slot?.count||1));
        const status=String(slot?.status||'').toUpperCase();
        if(status==='TRANSFIGURING'){
          const nextId=String(slot?.transfiguration?.new_business_id||'');
          if(nextId===id)count+=qty;
          continue;
        }
        if(String(slot?.business_id||'')===id)count+=qty;
      }
    }
    return count;
  }

  function businessCatalogCapacity(documentValue = playerDocument) {
    const player=documentValue?.player||documentValue||{};
    const standardMax=Math.max(0,Number(player?.business_worker_max||0));
    const standardBusy=Math.max(0,Number(player?.business_worker_busy||0));
    let rebrandMax=0,rebrandBusy=0;
    for(const building of findBuildings(documentValue)||[]){
      if(!String(building?.id||'').startsWith('special_building_business_group_'))continue;
      rebrandMax+=Math.max(0,Number(building?.num_slots||0));
      rebrandBusy+=(building?.active_business||[]).filter(slot=>String(slot?.status||'').toUpperCase()==='TRANSFIGURING').length;
    }
    return {
      standardMax,standardBusy,standardFree:Math.max(0,standardMax-standardBusy),
      rebrandMax,rebrandBusy,rebrandFree:Math.max(0,rebrandMax-rebrandBusy),
      ideal:Math.max(1,standardMax+rebrandMax),
      freeNow:Math.max(0,standardMax-standardBusy)+Math.max(0,rebrandMax-rebrandBusy)
    };
  }

  function businessCatalogRecords() {
    const ids=new Set();
    for(const row of businessCatalogDocument||[])if(row?.id)ids.add(String(row.id));
    for(const row of itemCatalogDocument||[]){
      const id=String(row?.id||'');
      if(id.startsWith('item_bsn_')&&!id.endsWith('_dummy'))ids.add(id);
    }
    const active=businessCounts(normalizeLayout(playerDocument)
      .filter(row=>String(row.status||'').toUpperCase()==='ACTIVE'&&Number(row.timer||0)<=0)
      .map(row=>row.businessId));
    return [...ids].map(id=>{
      const meta=recipeMetadata(id),effects=businessEffects(id),details=businessCardDetails(id);
      const owned=businessCatalogOwnedCount(id),limit=businessActiveLimit(id),activeCount=Number(active.get(id)||0);
      return {id,meta,effects,details,owned,limit,activeCount,
        search:[id,meta.name,meta.description,details.properties,...effects.map(e=>e.label)].join(' ').toLocaleLowerCase(locale())};
    }).sort((a,b)=>Number(a.meta.tier||99)-Number(b.meta.tier||99)||String(a.meta.name||a.id).localeCompare(String(b.meta.name||b.id),locale()));
  }

  function businessCatalogBonusOptions(records) {
    const map=new Map();
    for(const row of records)for(const effect of row.effects||[]){
      const key=String(effect.key||effect.label||''); if(!key)continue;
      const current=map.get(key)||{key,label:effect.label||key,count:0};
      current.count++;map.set(key,current);
    }
    return [...map.values()].sort((a,b)=>a.label.localeCompare(b.label,locale()));
  }

  function businessCatalogKnownRoutes(targetId) {
    const id=String(targetId||''); if(!id)return [];
    return (communityRecipes||[]).filter(row=>String(row?.item_id||'')===id)
      .map(row=>({planId:String(row?.plan_id||''),components:Array.isArray(row?.components)?row.components:[]}))
      .sort((a,b)=>a.planId.localeCompare(b.planId));
  }

  function businessCatalogCardHtml(row) {
    const selected=row.id===businessCatalogTargetId;
    const limit=Number.isFinite(row.limit)?String(row.limit):'∞';
    const bonuses=(row.effects||[]).map(effect=>'<span>'+escapeHtml(effect.label||effect.key)+'</span>').join('');
    return '<button type="button" class="hk-business-catalog-card '+(selected?'selected':'')+'" data-business-catalog-id="'+escapeHtml(row.id)+'">'+
      iconHtml(row.id)+'<span class="hk-business-catalog-copy"><b>'+escapeHtml(row.meta.name||row.id)+'</b>'+
      '<small>T'+escapeHtml(row.meta.tier??'—')+' · '+either('есть ','owned ')+Number(row.owned||0)+' · '+either('активно ','active ')+Number(row.activeCount||0)+'/'+escapeHtml(limit)+'</small>'+
      '<small class="hk-business-properties">'+escapeHtml(row.details.properties)+'</small>'+
      (bonuses?'<span class="hk-business-catalog-bonuses">'+bonuses+'</span>':'')+'</span></button>';
  }

  function businessCatalogPlannerHtml(records) {
    const target=records.find(row=>row.id===businessCatalogTargetId);
    if(!target)return '<div class="hk-cardbox hk-business-catalog-planner"><b>'+either('Планировщик','Planner')+'</b><p class="hk-muted">'+either('Выберите бизнес-карту из каталога.','Select a business card from the catalog.')+'</p></div>';
    const qty=Math.max(1,Math.trunc(Number(businessCatalogTargetQuantity||1)));
    const missing=Math.max(0,qty-Number(target.owned||0));
    const routes=businessCatalogKnownRoutes(target.id),cap=businessCatalogCapacity();
    let routeHtml='';
    if(routes.length){
      routeHtml=routes.map((route,index)=>{
        const parts=route.components.map(component=>{
          const id=String(component?.item_id||''),meta=recipeMetadata(id);
          return '<span class="hk-business-route-part">'+iconHtml(id)+'<small>'+escapeHtml(meta.name||id)+'</small></span>';
        }).join('<b>+</b>');
        return '<div class="hk-business-route"><strong>'+either('Рецепт ','Recipe ')+(index+1)+'</strong><div>'+parts+(parts?'<b>→</b>':'')+'<span class="hk-business-route-part">'+iconHtml(target.id)+'<small>'+escapeHtml(target.meta.name||target.id)+'</small></span></div></div>';
      }).join('');
    }else routeHtml='<p class="hk-muted">'+either('Известный рецепт пока не найден в общей базе.','No known recipe is currently available in the shared database.')+'</p>';
    return '<div class="hk-cardbox hk-business-catalog-planner"><div class="hk-business-catalog-plan-head"><b>'+either('Планировщик','Planner')+'</b><span>'+escapeHtml(target.meta.name||target.id)+'</span></div>'+
      '<div class="hk-business-catalog-plan-stats"><label><span>'+either('Нужное количество','Target quantity')+'</span><input id="hk-business-catalog-qty" type="number" min="1" max="999" value="'+qty+'"></label>'+
      '<div><span>'+either('Есть сейчас','Owned now')+'</span><b>'+Number(target.owned||0)+'</b></div>'+
      '<div><span>'+either('Не хватает','Missing')+'</span><b>'+missing+'</b></div>'+
      '<div><span>'+either('Параллельные улучшения','Upgrade capacity')+'</span><b>'+cap.freeNow+'/'+cap.ideal+'</b></div></div>'+
      '<div class="hk-business-routes">'+routeHtml+'</div></div>';
  }

  function renderBusinessCatalog() {
    const box=root?.querySelector('#hk-business-catalog'); if(!box)return;
    if(businessCatalogLoading){box.innerHTML='<p class="hk-muted">'+either('Загрузка каталога…','Loading catalog…')+'</p>';return;}
    if(!businessCatalogDocument||!itemCatalogDocument){
      box.innerHTML='<button id="hk-business-catalog-load" class="hk-primary">'+either('Загрузить каталог','Load catalog')+'</button>';
      box.querySelector('#hk-business-catalog-load')?.addEventListener('click',()=>void refreshBusinessCatalog(true));
      return;
    }
    const records=businessCatalogRecords(),bonuses=businessCatalogBonusOptions(records);
    const q=String(businessCatalogSearch||'').trim().toLocaleLowerCase(locale());
    const filtered=records.filter(row=>{
      if(q&&!row.search.includes(q))return false;
      if(!businessCatalogBonus)return true;
      const matches=(row.effects||[]).filter(effect=>String(effect.key||effect.label||'')===businessCatalogBonus);
      return !!matches.length&&(!businessCatalogExactBonusOnly||(row.effects||[]).length===1);
    });
    let options='<option value="">'+either('Все бонусы','All bonuses')+'</option>';
    options+=bonuses.map(row=>'<option value="'+escapeHtml(row.key)+'" '+(row.key===businessCatalogBonus?'selected':'')+'>'+escapeHtml(row.label)+' ('+row.count+')</option>').join('');
    box.innerHTML='<div class="hk-business-catalog-toolbar">'+
      '<input id="hk-business-catalog-search" value="'+escapeHtml(businessCatalogSearch)+'" placeholder="'+either('Поиск бизнесов…','Search businesses…')+'">'+
      '<select id="hk-business-catalog-bonus">'+options+'</select>'+
      '<label><input id="hk-business-catalog-exact" type="checkbox" '+(businessCatalogExactBonusOnly?'checked':'')+'><span>'+either('Только карты с этим бонусом','Only cards with this bonus')+'</span></label>'+
      '<button id="hk-business-catalog-refresh" class="hk-secondary">'+either('Обновить','Refresh')+'</button></div>'+
      '<div class="hk-business-catalog-summary"><b>'+either('Бизнесов: ','Businesses: ')+filtered.length+'</b><span>'+either('Всего карт: ','Total cards: ')+records.length+'</span></div>'+
      businessCatalogPlannerHtml(records)+
      '<div class="hk-business-catalog-grid">'+(filtered.length?filtered.map(businessCatalogCardHtml).join(''):'<p class="hk-muted">'+either('По вашему фильтру ничего не найдено.','No businesses matched the filter.')+'</p>')+'</div>';
    installIconFallbacks(box);
    box.querySelector('#hk-business-catalog-search')?.addEventListener('input',event=>{businessCatalogSearch=event.target.value;renderBusinessCatalog();});
    box.querySelector('#hk-business-catalog-bonus')?.addEventListener('change',event=>{businessCatalogBonus=event.target.value;renderBusinessCatalog();});
    box.querySelector('#hk-business-catalog-exact')?.addEventListener('change',event=>{businessCatalogExactBonusOnly=!!event.target.checked;renderBusinessCatalog();});
    box.querySelector('#hk-business-catalog-refresh')?.addEventListener('click',()=>void refreshBusinessCatalog(true));
    box.querySelector('#hk-business-catalog-qty')?.addEventListener('change',event=>{businessCatalogTargetQuantity=Math.max(1,Math.min(999,Math.trunc(Number(event.target.value)||1)));renderBusinessCatalog();});
    box.querySelectorAll('[data-business-catalog-id]').forEach(button=>button.addEventListener('click',()=>{businessCatalogTargetId=String(button.dataset.businessCatalogId||'');renderBusinessCatalog();}));
  }

  async function refreshBusinessCatalog(forceRoutes=false) {
    if(businessCatalogLoading)return;
    businessCatalogLoading=true;renderBusinessCatalog();
    try{
      playerDocument=await hkAuthoritativePlayerRead('business-catalog');
      await ensureRecipeMetadata();
      refreshBusinessData();
      if(forceRoutes||!businessCatalogRoutesLoaded){
        try{
          const result=await recipeServerJson('/list');
          communityRecipes=Array.isArray(result?.recipes)?result.recipes:[];
          businessCatalogRoutesLoaded=true;
        }catch(_){businessCatalogRoutesLoaded=false;}
      }
    }catch(error){log(either('Ошибка каталога бизнесов: ','Business catalog error: ')+(error?.message||error),'warn');}
    finally{businessCatalogLoading=false;renderBusinessCatalog();}
  }

'''
s=s.replace(anchor,catalog+anchor,1)

refresh_tail="""    renderBusinessLists();
    renderBusinessOptimizerFilters();
  }
"""
if refresh_tail not in s: raise SystemExit("refreshBusinessData tail missing")
s=s.replace(refresh_tail,"""    renderBusinessLists();
    renderBusinessOptimizerFilters();
    renderBusinessCatalog();
  }
""",1)

# Add Catalog tab directly after Optimizer.
pattern=r'(<button class="hk-business-tab" data-business-tab="optimizer"[^>]*>.*?</button>)'
s,count=re.subn(pattern,r'\1<button class="hk-business-tab" data-business-tab="catalog" data-i18n="businessCatalog">Каталог</button>',s,count=1)
if count!=1: raise SystemExit("business catalog tab insertion failed")

# Add catalog pane before the business page closes.
page_close='''        <section class="hk-bonus-analyzer"><h3 data-i18n="bonusAnalyzer">${tr('bonusAnalyzer')}</h3><div id="hk-bonus-analyzer-result"><p class="hk-muted">${tr('optimizerNoPlan')}</p></div></section></div></div>
      </div>
      <div class="hk-page" data-content="clan">'''
if page_close not in s: raise SystemExit("business page close missing")
catalog_pane='''        <section class="hk-bonus-analyzer"><h3 data-i18n="bonusAnalyzer">${tr('bonusAnalyzer')}</h3><div id="hk-bonus-analyzer-result"><p class="hk-muted">${tr('optimizerNoPlan')}</p></div></section></div>
        <div class="hk-business-pane" data-business-pane="catalog"><div id="hk-business-catalog"><p class="hk-muted">Каталог</p></div></div></div>
      </div>
      <div class="hk-page" data-content="clan">'''
s=s.replace(page_close,catalog_pane,1)

s=s.replace("const pane = paneName === 'optimizer' ? 'optimizer' : 'regular';",
            "const pane = ['optimizer','catalog'].includes(paneName) ? paneName : 'regular';",1)

branch="""      if (pane === 'optimizer') {
        renderBusinessOptimizerFilters();
        renderBonusAnalyzer();
      } else {
        renderBusinessLists();
      }
"""
if branch not in s: raise SystemExit("business pane branch missing")
s=s.replace(branch,"""      if (pane === 'optimizer') {
        renderBusinessOptimizerFilters();
        renderBonusAnalyzer();
      } else if (pane === 'catalog') {
        renderBusinessCatalog();
        if(!businessCatalogDocument||!itemCatalogDocument)void refreshBusinessCatalog(false);
      } else {
        renderBusinessLists();
      }
""",1)

s=s.replace("if (finalPage === 'business') { renderBusinessLists(); renderBusinessOptimizerFilters(); }",
            "if (finalPage === 'business') { renderBusinessLists(); renderBusinessOptimizerFilters(); renderBusinessCatalog(); }",1)

s=s.replace(".hk-business-tabs{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin:10px 0}",
            ".hk-business-tabs{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin:10px 0}",1)

css_anchor=".hk-bonus-analyzer{margin:10px 0;padding:11px;border:1px solid #34445b;border-radius:14px;background:#0d1520}"
if css_anchor not in s: raise SystemExit("business css anchor missing")
css=""".hk-business-catalog-toolbar{display:grid;grid-template-columns:minmax(180px,1fr) minmax(180px,.7fr) auto auto;gap:8px;align-items:center;margin:10px 0}.hk-business-catalog-toolbar input,.hk-business-catalog-toolbar select,.hk-business-catalog-plan-stats input{min-width:0;background:#0b111b;color:#fff;border:1px solid #43536d;border-radius:9px;padding:9px}.hk-business-catalog-toolbar label{display:flex;gap:6px;align-items:center;color:#aebbd0;font-size:11px}.hk-business-catalog-summary{display:flex;justify-content:space-between;gap:10px;color:#aebbd0;margin:8px 0}.hk-business-catalog-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:8px}.hk-business-catalog-card{display:grid;grid-template-columns:46px minmax(0,1fr);gap:9px;text-align:left;align-items:center;border:1px solid #2a374a;border-radius:12px;padding:9px;background:#111925;color:#fff}.hk-business-catalog-card.selected{border-color:#ffad1f;background:#2a2418}.hk-business-catalog-copy{display:grid;gap:3px;min-width:0}.hk-business-catalog-copy>b,.hk-business-catalog-copy>small{overflow:hidden;text-overflow:ellipsis}.hk-business-catalog-bonuses{display:flex;gap:4px;flex-wrap:wrap}.hk-business-catalog-bonuses span{font-size:9px;padding:2px 6px;border-radius:999px;background:#202c3d;color:#b9c8dc}.hk-business-catalog-planner{margin:10px 0}.hk-business-catalog-plan-head{display:flex;justify-content:space-between;gap:8px}.hk-business-catalog-plan-head span{color:#ffd166}.hk-business-catalog-plan-stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px;margin:9px 0}.hk-business-catalog-plan-stats>div,.hk-business-catalog-plan-stats>label{display:grid;gap:4px;padding:8px;border:1px solid #2c3a4d;border-radius:9px;background:#101824}.hk-business-catalog-plan-stats span{font-size:10px;color:#91a2b9}.hk-business-routes{display:grid;gap:7px}.hk-business-route{padding:8px;border:1px solid #2b3a4e;border-radius:10px;background:#0e1722}.hk-business-route>div{display:flex;align-items:center;gap:5px;overflow-x:auto;margin-top:6px}.hk-business-route-part{display:grid;justify-items:center;gap:2px;min-width:70px}.hk-business-route-part .hk-icon{width:34px;height:34px;flex-basis:34px}.hk-business-route-part small{max-width:80px;text-align:center;font-size:9px;color:#9fb0c7}@media(max-width:760px){.hk-business-catalog-toolbar{grid-template-columns:1fr}.hk-business-catalog-plan-stats{grid-template-columns:1fr 1fr}.hk-business-tabs{grid-template-columns:1fr}.hk-business-catalog-grid{grid-template-columns:1fr}}"""
s=s.replace(css_anchor,css+css_anchor,1)

for marker in [
    "// @version      1.17.23",
    "const BUILD_VERSION = '1.17.23';",
    "core-20260921-r25-businesses-catalog",
    "businesses-catalog-readonly-20260921-r1",
    "function businessCatalogOwnedCount(",
    "function businessCatalogCapacity(",
    "function businessCatalogRecords()",
    "function renderBusinessCatalog()",
    "async function refreshBusinessCatalog(",
    'data-business-tab="catalog"',
    'id="hk-business-catalog"',
    "explore-production-ui-20260921-r1",
    "buildings-native-sync-20260921-r1",
    "maps-shared-runtime-20260921-r7-safe5",
    "AUTH_PASSIVE_SAFETY_R1",
]:
    if marker not in s:
        raise SystemExit("post-patch marker missing: "+marker)

catalog_slice=s[s.index("function businessCatalogOwnedCount("):s.index("function businessSelectionCount()")]
for forbidden in ["/player/business/insert","/shop/buy","/player/business/recipe/craft","/fair/reroll"]:
    if forbidden in catalog_slice:
        raise SystemExit("read-only catalog contains mutation path: "+forbidden)

PATH.write_text(s,encoding="utf-8")
print("BUSINESSES_CATALOG_READONLY_R1_PATCH=PASS")
