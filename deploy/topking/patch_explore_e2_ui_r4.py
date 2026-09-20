from pathlib import Path

p=Path("/tmp/HamsterKingMobile.user.js")
s=p.read_text()
old_marker="const HK_EXPLORE_CANON_REV='explore-readonly-plan-20260920-r3-ui';"
new_marker="const HK_EXPLORE_CANON_REV='explore-readonly-plan-20260920-r4-ui';"
assert s.count(old_marker)==1, s.count(old_marker)
s=s.replace(old_marker,new_marker,1)

a=s.index("  function renderExplore(){")
b=s.index("  async function refreshExplore",a)

new_fn=r'''  function renderExplore(){
    const box=root?.querySelector('#hk-explore-content');if(!box)return;const s=exploreSettings(),p=explorePlan,st=hkStateStore.snapshot||playerDocument||{},active=exploreActive(st),c=p?.consigliere||exploreConsigliere(st);
    const auto=p?.autoMaxTier??exploreAutoTier(c),level=p?.playerLevel??Number(st?.player?.level||0),modes=p?.tierModes||exploreTierModes(level),counts=p?.tierCounts||exploreCounts(active),targetOk=s.targetTier>=1&&s.targetTier<=6;
    const maxStart=targetOk&&s.exploreTargetTier?s.targetTier:Math.min(s.targetTier,7)-1;
    const tiers=EXPLORE_TIERS.map(t=>'<label class="hk-ex-check"><input type="checkbox" data-ex-tier="'+t.value+'" '+(s.startTiers.includes(t.value)?'checked':'')+' '+(t.value>maxStart?'disabled':'')+'><span>'+t.label+'</span><small class="hk-muted">'+(counts[t.value]?.all||0)+' / '+(counts[t.value]?.battles||0)+'</small></label>').join('');
    const targets=EXPLORE_TIERS.filter(t=>t.value>=1).map(t=>'<option value="'+t.value+'" '+(s.targetTier===t.value?'selected':'')+'>'+t.label+'</option>').join('')+'<option value="8" '+(s.targetTier===8?'selected':'')+'>'+either('Мгновенно MAX','Instant MAX')+'</option>';
    const modeLine=EXPLORE_TIERS.map(t=>'<span><b>'+t.label+'</b> '+(modes[t.value]==='fast'?either('быстро','fast'):modes[t.value]==='auto'?either('авто','auto'):either('вручную','manual'))+'</span>').join('');
    const rows=(p?.selected||[]).slice(0,20).map((r,i)=>'<div class="hk-card"><div class="hk-business-info"><b>'+(i+1)+'. '+escapeHtml(r.id)+'</b><small>'+escapeHtml(r.areaId||either('район неизвестен','district unknown'))+' · '+exploreTierLabel(r.tier)+' · '+either('ур.','Lv')+' '+Number(r.level||0)+' · '+either('бой','battle')+' '+Number(r.battle_level||0)+'/'+Number(r.max_battle_level||0)+' · '+either('события','events')+' '+(r.targetRemaining!=null?(r.targetRemaining+'/'+r.targetTotal):(r.totalEvents==null?'?':r.totalEvents))+(r.isInvest===true?' · ◆ '+either('инвест','investment'):r.isInvest===false?' · '+either('обычное','normal'):'')+'</small></div><strong>→ '+exploreTierLabel(s.targetTier)+'</strong></div>').join('');
    const planHtml=p?'<div class="hk-cardbox"><b>'+either('Read-only план','Read-only plan')+'</b><p class="hk-muted">'+either('После фильтров','After filters')+': '+p.filteredCount+' · '+either('кандидатов','candidates')+': '+p.candidates.length+' · '+either('к обработке','to process')+': '+p.selected.length+'</p>'+
      (p.targetScan.checked?'<p class="hk-muted">'+either('Проверено на целевом тире','Checked at target tier')+': '+p.targetScan.checked+' · '+either('готовых пропущено','finished skipped')+': '+p.targetScan.skipped+(p.targetScan.errors?' · '+either('ошибок','errors')+': '+p.targetScan.errors:'')+'</p>':'')+
      (s.totalEvents!=='any'&&!p.totalEventsKnown?'<p class="hk-muted">⚠ '+either('Приоритет «Всего событий» не применён: точные данные есть не у всех кандидатов.','Total-events priority was not applied: exact data is unavailable for some candidates.')+'</p>':'')+
      (p.meta?.unmapped?'<p class="hk-muted">⚠ '+either('Без района','Without district')+': '+p.meta.unmapped+'</p>':'')+(p.meta?.unknownType?'<p class="hk-muted">⚠ '+either('Тип неизвестен','Unknown type')+': '+p.meta.unknownType+'</p>':'')+
      '<div class="hk-cards">'+(rows||'<p class="hk-muted">'+either('Подходящих зданий нет.','No eligible buildings.')+'</p>')+'</div>'+(p.selected.length>20?'<p class="hk-muted">… +'+(p.selected.length-20)+'</p>':'')+'</div>':
      '<div class="hk-cardbox hk-ex-hint">'+either('Выберите фильтры и нажмите «Рассчитать план». Здесь ничего не тратится.','Choose filters and press “Calculate plan”. Nothing is spent here.')+'</div>';

    box.innerHTML='<style>'+
      '#hk-explore-content .hk-ex-main{display:grid;gap:12px}'+
      '#hk-explore-content .hk-ex-filter-grid{display:grid;grid-template-columns:repeat(4,minmax(150px,1fr));gap:10px;margin-top:10px}'+
      '#hk-explore-content .hk-ex-field{display:grid;gap:5px;min-width:0}'+
      '#hk-explore-content .hk-ex-field>span{font-size:12px;font-weight:700}'+
      '#hk-explore-content .hk-ex-field select,#hk-explore-content .hk-ex-field input{width:100%;box-sizing:border-box;min-width:0}'+
      '#hk-explore-content .hk-ex-tier-list{display:flex;flex-wrap:wrap;gap:7px;margin-top:7px}'+
      '#hk-explore-content .hk-ex-check{display:flex;align-items:center;gap:6px;padding:7px 9px;border:1px solid rgba(255,255,255,.09);border-radius:8px;background:rgba(255,255,255,.02);cursor:pointer}'+
      '#hk-explore-content .hk-ex-check:has(input:disabled){opacity:.45;cursor:default}'+
      '#hk-explore-content .hk-ex-check small{margin-left:2px;white-space:nowrap}'+
      '#hk-explore-content .hk-ex-options{display:flex;flex-wrap:wrap;gap:14px;margin-top:10px}'+
      '#hk-explore-content .hk-ex-options label{display:flex;align-items:center;gap:6px;font-size:12px}'+
      '#hk-explore-content .hk-ex-two{display:grid;grid-template-columns:1fr 1fr;gap:12px}'+
      '#hk-explore-content .hk-ex-rows{display:grid;gap:8px;margin-top:9px}'+
      '#hk-explore-content .hk-ex-row{display:grid;grid-template-columns:minmax(120px,1fr) minmax(150px,190px);gap:10px;align-items:center}'+
      '#hk-explore-content .hk-ex-row>span{font-size:12px}'+
      '#hk-explore-content .hk-ex-row select,#hk-explore-content .hk-ex-row input{width:100%;box-sizing:border-box}'+
      '#hk-explore-content .hk-ex-modes{display:flex;flex-wrap:wrap;gap:7px 14px;margin-top:8px;font-size:12px}'+
      '#hk-explore-content .hk-ex-actions{display:flex;gap:8px;flex-wrap:wrap}'+
      '#hk-explore-content .hk-ex-hint{padding:11px 13px}'+
      '#hk-explore-content .hk-ex-dirty{font-size:12px;margin-left:8px}'+
      '@media(max-width:950px){#hk-explore-content .hk-ex-filter-grid{grid-template-columns:repeat(2,minmax(0,1fr))}#hk-explore-content .hk-ex-two{grid-template-columns:1fr}}'+
      '@media(max-width:560px){#hk-explore-content .hk-ex-filter-grid{grid-template-columns:1fr}#hk-explore-content .hk-ex-row{grid-template-columns:1fr}#hk-explore-content .hk-ex-options{display:grid;gap:8px}}'+
      '</style>'+
      '<div class="hk-clan-head"><div><h3>'+either('Исследование зданий','Explore Buildings')+'</h3><small>'+either('E2 · только чтение и расчёт','E2 · read-only planning')+'</small></div><button id="hk-ex-refresh" class="hk-secondary" '+(exploreBusy?'disabled':'')+'>'+either('Обновить','Refresh')+'</button></div>'+
      '<div class="hk-ex-main">'+
        '<div class="hk-cardbox"><b>'+either('Возможности аккаунта','Account capabilities')+'</b><p class="hk-muted" style="margin:6px 0 0">'+either('Уровень','Level')+': '+Number(level).toLocaleString(locale())+' · Remort Consigliere: '+(c?(Number(c.level||0)+' · '+(c.status==='ACTIVE'?either('активен','active'):either('заблокирован','locked'))):either('не найден','not found'))+' · '+either('Автобои','Auto battles')+': '+(auto>=0?either('до ','up to ')+exploreTierLabel(auto):either('нет','none'))+'</p><div class="hk-ex-modes">'+modeLine+'</div></div>'+
        '<div class="hk-cardbox"><b>'+either('Фильтры зданий','Building filters')+'</b>'+
          '<div class="hk-ex-filter-grid">'+
            '<label class="hk-ex-field"><span>'+either('Район','District')+'</span><select id="hk-ex-district">'+exploreDistrictOptions(s.districtId)+'</select></label>'+
            '<label class="hk-ex-field"><span>'+either('Тип здания','Building type')+'</span><select id="hk-ex-type"><option value="all" '+(s.buildingType==='all'?'selected':'')+'>'+either('Все','All')+'</option><option value="normal" '+(s.buildingType==='normal'?'selected':'')+'>'+either('Обычные','Normal')+'</option><option value="investment" '+(s.buildingType==='investment'?'selected':'')+'>'+either('Инвестиционные','Investment')+'</option></select></label>'+
            '<label class="hk-ex-field"><span>'+either('Целевой тир','Target tier')+'</span><select id="hk-ex-target">'+targets+'</select></label>'+
            '<label class="hk-ex-field"><span>'+either('Максимум зданий','Maximum buildings')+'</span><input id="hk-ex-max" type="number" min="1" max="5000" value="'+s.maxBuildings+'"></label>'+
          '</div>'+
          '<p class="hk-muted" style="margin:11px 0 0">'+either('Стартовые тиры · всего / бои завершены','Starting tiers · total / battles done')+'</p>'+
          '<div class="hk-ex-tier-list">'+tiers+'</div>'+
          '<div class="hk-ex-options">'+
            '<label><input id="hk-ex-target-tier" type="checkbox" '+(s.exploreTargetTier?'checked':'')+' '+(targetOk?'':'disabled')+'><span>'+either('Исследовать целевой тир','Explore target tier')+'</span></label>'+
            '<label><input id="hk-ex-target-battles" type="checkbox" '+(s.exploreTargetBattles?'checked':'')+' '+(targetOk&&s.exploreTargetTier?'':'disabled')+'><span>'+either('Завершить бои на целевом тире','Complete target-tier battles')+'</span></label>'+
            '<label><input id="hk-ex-buy" type="checkbox" '+(s.buyMissingMaterials?'checked':'')+'><span>'+either('Автопокупка балок/гвоздей · с E3','Auto-buy beams/nails · from E3')+'</span></label>'+
          '</div>'+
        '</div>'+
        '<div class="hk-ex-two">'+
          '<div class="hk-cardbox"><b>'+either('Приоритет','Priority')+'</b><div class="hk-ex-rows">'+
            '<label class="hk-ex-row"><span>'+either('Бой','Battle')+'</span><select id="hk-ex-pr-battle">'+explorePrOptions(s.battleLevel)+'</select></label>'+
            '<label class="hk-ex-row"><span>'+either('Уровень здания','Building level')+'</span><select id="hk-ex-pr-level">'+explorePrOptions(s.level)+'</select></label>'+
            '<label class="hk-ex-row"><span>'+either('До следующего тира','Next-tier level')+'</span><select id="hk-ex-pr-next">'+explorePrOptions(s.nextTierLevel)+'</select></label>'+
            '<label class="hk-ex-row"><span>'+either('Всего событий','Total events')+'</span><select id="hk-ex-pr-events">'+explorePrOptions(s.totalEvents)+'</select></label>'+
          '</div></div>'+
          '<div class="hk-cardbox"><b>'+either('Задержки будущего запуска','Future run delays')+'</b><div class="hk-ex-rows">'+
            '<label class="hk-ex-row"><span>'+either('Действие, мин. сек','Action min, sec')+'</span><input id="hk-ex-action-min" type="number" min="0" step="0.1" value="'+s.actionDelayMinMs/1000+'"></label>'+
            '<label class="hk-ex-row"><span>'+either('Действие, макс. сек','Action max, sec')+'</span><input id="hk-ex-action-max" type="number" min="0" step="0.1" value="'+s.actionDelayMaxMs/1000+'"></label>'+
            '<label class="hk-ex-row"><span>'+either('Бой, сек','Battle, sec')+'</span><input id="hk-ex-battle" type="number" min="0" step="0.1" value="'+s.battleDelayMs/1000+'"></label>'+
            '<label class="hk-ex-row"><span>'+either('Между зданиями, мин. сек','Between buildings min, sec')+'</span><input id="hk-ex-between-min" type="number" min="0" step="0.1" value="'+s.betweenBuildingsDelayMinMs/1000+'"></label>'+
            '<label class="hk-ex-row"><span>'+either('Между зданиями, макс. сек','Between buildings max, sec')+'</span><input id="hk-ex-between-max" type="number" min="0" step="0.1" value="'+s.betweenBuildingsDelayMaxMs/1000+'"></label>'+
          '</div></div>'+
        '</div>'+
        '<div class="hk-ex-actions"><button id="hk-ex-plan" class="hk-primary" '+(exploreBusy?'disabled':'')+'>'+(exploreBusy?either('Считаю…','Calculating…'):either('Рассчитать план','Calculate plan'))+'</button><button class="hk-secondary" disabled>'+either('Запуск появится на E3','Run becomes available in E3')+'</button><span id="hk-ex-dirty" class="hk-muted hk-ex-dirty"></span></div>'+
        '<div id="hk-ex-plan-result">'+planHtml+'</div>'+
      '</div>';

    const dirty=()=>{const n=box.querySelector('#hk-ex-dirty');if(n)n.textContent=either('Настройки изменены — пересчитайте план','Settings changed — recalculate plan');const r=box.querySelector('#hk-ex-plan-result');if(r)r.innerHTML='<div class="hk-cardbox hk-ex-hint">'+either('Настройки изменены. Нажмите «Рассчитать план».','Settings changed. Press “Calculate plan”.')+'</div>';};
    const persist=()=>{exploreReadSettings();explorePlan=null;dirty();};
    const syncDependencies=()=>{
      const target=Number(box.querySelector('#hk-ex-target')?.value||3),targetTier=box.querySelector('#hk-ex-target-tier'),targetBattles=box.querySelector('#hk-ex-target-battles'),ok=target>=1&&target<=6;
      if(targetTier){targetTier.disabled=!ok;if(!ok)targetTier.checked=false;}
      if(targetBattles){targetBattles.disabled=!ok||!targetTier?.checked;if(targetBattles.disabled)targetBattles.checked=false;}
      const maxAllowed=ok&&targetTier?.checked?target:Math.min(target,7)-1;
      const tierInputs=[...box.querySelectorAll('[data-ex-tier]')];
      for(const n of tierInputs){const disabled=Number(n.dataset.exTier)>maxAllowed;n.disabled=disabled;if(disabled)n.checked=false;}
      if(!tierInputs.some(n=>!n.disabled&&n.checked)){const first=tierInputs.find(n=>!n.disabled);if(first)first.checked=true;}
      persist();
    };

    box.querySelector('#hk-ex-refresh')?.addEventListener('click',()=>void refreshExplore(true));
    box.querySelector('#hk-ex-plan')?.addEventListener('click',()=>{exploreReadSettings();explorePlan=null;void explorePreparePlan();});
    box.querySelector('#hk-ex-target')?.addEventListener('change',syncDependencies);
    box.querySelector('#hk-ex-target-tier')?.addEventListener('change',syncDependencies);
    box.querySelectorAll('select,input').forEach(n=>{
      if(n.id==='hk-ex-target'||n.id==='hk-ex-target-tier')return;
      n.addEventListener('change',persist);
    });
  }
'''
s=s[:a]+new_fn+s[b:]

# Scope/safety: only marker + render function changes.
assert "explore-readonly-plan-20260920-r4-ui" in s
assert "const changed=()=>{exploreReadSettings();explorePlan=null;renderExplore();};" not in s[a:a+len(new_fn)+100]
assert "syncDependencies" in s[a:a+len(new_fn)+100]
p.write_text(s)
