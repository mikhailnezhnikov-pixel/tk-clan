from pathlib import Path

p=Path("/tmp/HamsterKingMobile.user.js")
s=p.read_text()

old_marker="const HK_EXPLORE_CANON_REV='explore-readonly-plan-20260920-r4-ui';"
new_marker="const HK_EXPLORE_CANON_REV='explore-readonly-plan-20260920-r5-filters';"
assert s.count(old_marker)==1, s.count(old_marker)
s=s.replace(old_marker,new_marker,1)

old_tiers="""    const tiers=EXPLORE_TIERS.map(t=>'<label class="hk-ex-check"><input type="checkbox" data-ex-tier="'+t.value+'" '+(s.startTiers.includes(t.value)?'checked':'')+' '+(t.value>maxStart?'disabled':'')+'><span>'+t.label+'</span><small class="hk-muted">'+(counts[t.value]?.all||0)+' / '+(counts[t.value]?.battles||0)+'</small></label>').join('');"""
new_tiers="""    const tiers=EXPLORE_TIERS.map(t=>'<label class="hk-ex-check"><input type="checkbox" data-ex-tier="'+t.value+'" '+(s.startTiers.includes(t.value)?'checked':'')+' '+(t.value>maxStart?'disabled':'')+'><span>'+t.label+'</span><small class="hk-muted"><span data-ex-count="'+t.value+'">'+(counts[t.value]?.all||0)+'</span> / <span data-ex-battles="'+t.value+'">'+(counts[t.value]?.battles||0)+'</span></small></label>').join('');"""
assert s.count(old_tiers)==1
s=s.replace(old_tiers,new_tiers,1)

old_options="""          '<div class="hk-ex-options">'+
            '<label><input id="hk-ex-target-tier" type="checkbox" '+(s.exploreTargetTier?'checked':'')+' '+(targetOk?'':'disabled')+'><span>'+either('Исследовать целевой тир','Explore target tier')+'</span></label>'+
            '<label><input id="hk-ex-target-battles" type="checkbox" '+(s.exploreTargetBattles?'checked':'')+' '+(targetOk&&s.exploreTargetTier?'':'disabled')+'><span>'+either('Завершить бои на целевом тире','Complete target-tier battles')+'</span></label>'+
            '<label><input id="hk-ex-buy" type="checkbox" '+(s.buyMissingMaterials?'checked':'')+'><span>'+either('Автопокупка балок/гвоздей · с E3','Auto-buy beams/nails · from E3')+'</span></label>'+
          '</div>'+"""
new_options="""          '<div class="hk-ex-options">'+
            '<label><input id="hk-ex-target-tier" type="checkbox" '+(s.exploreTargetTier?'checked':'')+' '+(targetOk?'':'disabled')+'><span>'+either('Исследовать целевой тир','Explore target tier')+'</span></label>'+
            '<label><input id="hk-ex-target-battles" type="checkbox" '+(s.exploreTargetBattles?'checked':'')+' '+(targetOk&&s.exploreTargetTier?'':'disabled')+'><span>'+either('Завершить бои на целевом тире','Complete target-tier battles')+'</span></label>'+
            '<label><input id="hk-ex-buy" type="checkbox" '+(s.buyMissingMaterials?'checked':'')+'><span>'+either('Автопокупка балок/гвоздей · с E3','Auto-buy beams/nails · from E3')+'</span></label>'+
          '</div>'+
          '<p id="hk-ex-filter-summary" class="hk-muted" style="margin:9px 0 0"></p>'+"""
assert s.count(old_options)==1
s=s.replace(old_options,new_options,1)

old_handlers="""    const dirty=()=>{const n=box.querySelector('#hk-ex-dirty');if(n)n.textContent=either('Настройки изменены — пересчитайте план','Settings changed — recalculate plan');const r=box.querySelector('#hk-ex-plan-result');if(r)r.innerHTML='<div class="hk-cardbox hk-ex-hint">'+either('Настройки изменены. Нажмите «Рассчитать план».','Settings changed. Press “Calculate plan”.')+'</div>';};
    const persist=()=>{exploreReadSettings();explorePlan=null;dirty();};
    const syncDependencies=()=>{"""
new_handlers="""    const dirty=()=>{const n=box.querySelector('#hk-ex-dirty');if(n)n.textContent=either('Настройки изменены — пересчитайте план','Settings changed — recalculate plan');const r=box.querySelector('#hk-ex-plan-result');if(r)r.innerHTML='<div class="hk-cardbox hk-ex-hint">'+either('Настройки изменены. Нажмите «Рассчитать план».','Settings changed. Press “Calculate plan”.')+'</div>';};
    const updateFilterPreview=(settings=exploreSettings())=>{
      const state=hkStateStore.snapshot||playerDocument||{},summary=box.querySelector('#hk-ex-filter-summary'),ready=!!state?.player&&Array.isArray(state?.buildings),metaReady=!!exploreMeta;
      if(!ready){
        for(const t of EXPLORE_TIERS){const cEl=box.querySelector('[data-ex-count="'+t.value+'"]'),bEl=box.querySelector('[data-ex-battles="'+t.value+'"]');if(cEl)cEl.textContent='—';if(bEl)bEl.textContent='—';}
        if(summary)summary.textContent=either('Данные аккаунта ещё загружаются. Нажмите «Обновить», если значения не появятся.','Account data is still loading. Press “Refresh” if values do not appear.');
        return;
      }
      const filtered=exploreFiltered(settings,state,exploreMeta),tierCounts=exploreCounts(filtered),basic=exploreBasic(settings,state,exploreMeta);
      for(const t of EXPLORE_TIERS){const row=tierCounts[t.value]||{all:0,battles:0},cEl=box.querySelector('[data-ex-count="'+t.value+'"]'),bEl=box.querySelector('[data-ex-battles="'+t.value+'"]');if(cEl)cEl.textContent=String(row.all||0);if(bEl)bEl.textContent=String(row.battles||0);}
      if(summary){
        const typeNeedsMeta=settings.buildingType!=='all'&&!metaReady;
        summary.textContent=typeNeedsMeta
          ? either('Данные типов зданий ещё загружаются.','Building-type metadata is still loading.')
          : either('По фильтру: ','Filtered: ')+filtered.length+' · '+either('предварительно кандидатов: ','preliminary candidates: ')+basic.rows.length;
      }
    };
    const persist=()=>{const settings=exploreReadSettings();explorePlan=null;dirty();updateFilterPreview(settings);};
    const syncDependencies=()=>{"""
assert s.count(old_handlers)==1
s=s.replace(old_handlers,new_handlers,1)

old_end="""    box.querySelectorAll('select,input').forEach(n=>{
      if(n.id==='hk-ex-target'||n.id==='hk-ex-target-tier')return;
      n.addEventListener('change',persist);
    });
  }"""
new_end="""    box.querySelectorAll('select,input').forEach(n=>{
      if(n.id==='hk-ex-target'||n.id==='hk-ex-target-tier')return;
      n.addEventListener('change',persist);
    });
    updateFilterPreview(s);
  }"""
assert s.count(old_end)==1
s=s.replace(old_end,new_end,1)

old_branch="        if (key === 'explore') {const value=await refreshExplore(false);liveReadOk=true;return value;}"
new_branch="        if (key === 'explore') {const value=await refreshExplore(false);liveReadOk=!!value;return value;}"
assert s.count(old_branch)==1
s=s.replace(old_branch,new_branch,1)

assert "HK_MAP_SCANNER_REV = 'maps-parallel-read-20260920-r6-safe5'" in s
assert "const HK_MAP_READ_CONCURRENCY = 5;" in s
p.write_text(s)
