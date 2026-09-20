from pathlib import Path

p = Path("/tmp/HamsterKingMobile.user.js")
s = p.read_text()

old_marker = "const HK_EXPLORE_CANON_REV='explore-readonly-plan-20260920-r2';"
new_marker = "const HK_EXPLORE_CANON_REV='explore-readonly-plan-20260920-r3-ui';"
assert s.count(old_marker) == 1, s.count(old_marker)
s = s.replace(old_marker, new_marker, 1)

a = s.index("  function renderExplore(){")
b = s.index("  async function refreshExplore", a)

new_fn = r'''  function renderExplore(){
    const box=root?.querySelector('#hk-explore-content');if(!box)return;const s=exploreSettings(),p=explorePlan,st=hkStateStore.snapshot||playerDocument||{},active=exploreActive(st),c=p?.consigliere||exploreConsigliere(st);
    const auto=p?.autoMaxTier??exploreAutoTier(c),level=p?.playerLevel??Number(st?.player?.level||0),modes=p?.tierModes||exploreTierModes(level),counts=p?.tierCounts||exploreCounts(active),targetOk=s.targetTier>=1&&s.targetTier<=6;
    const maxStart=targetOk&&s.exploreTargetTier?s.targetTier:Math.min(s.targetTier,7)-1;
    const tiers=EXPLORE_TIERS.map(t=>'<label class="hk-ex-tier"><span><input type="checkbox" data-ex-tier="'+t.value+'" '+(s.startTiers.includes(t.value)?'checked':'')+' '+(t.value>maxStart?'disabled':'')+'> <b>'+t.label+'</b></span><small class="hk-muted">'+(counts[t.value]?.all||0)+' / '+(counts[t.value]?.battles||0)+'</small></label>').join('');
    const targets=EXPLORE_TIERS.filter(t=>t.value>=1).map(t=>'<option value="'+t.value+'" '+(s.targetTier===t.value?'selected':'')+'>'+t.label+'</option>').join('')+'<option value="8" '+(s.targetTier===8?'selected':'')+'>'+either('Мгновенно MAX','Instant MAX')+'</option>';
    const modeChips=EXPLORE_TIERS.map(t=>'<span class="hk-ex-chip"><b>'+t.label+'</b><small>'+(modes[t.value]==='fast'?either('быстро','fast'):modes[t.value]==='auto'?either('авто','auto'):either('вручную','manual'))+'</small></span>').join('');
    const rows=(p?.selected||[]).slice(0,20).map((r,i)=>'<div class="hk-card"><div class="hk-business-info"><b>'+(i+1)+'. '+escapeHtml(r.id)+'</b><small>'+escapeHtml(r.areaId||either('район неизвестен','district unknown'))+' · '+exploreTierLabel(r.tier)+' · '+either('ур.','Lv')+' '+Number(r.level||0)+' · '+either('бой','battle')+' '+Number(r.battle_level||0)+'/'+Number(r.max_battle_level||0)+' · '+either('события','events')+' '+(r.targetRemaining!=null?(r.targetRemaining+'/'+r.targetTotal):(r.totalEvents==null?'?':r.totalEvents))+(r.isInvest===true?' · ◆ '+either('инвест','investment'):r.isInvest===false?' · '+either('обычное','normal'):'')+'</small></div><strong>→ '+exploreTierLabel(s.targetTier)+'</strong></div>').join('');
    const summary=p?'<div class="hk-cardbox hk-ex-wide"><b>'+either('Read-only план','Read-only plan')+'</b><p class="hk-muted">'+either('После фильтров','After filters')+': '+p.filteredCount+' · '+either('кандидатов','candidates')+': '+p.candidates.length+' · '+either('к обработке','to process')+': '+p.selected.length+'</p>'+
      (p.targetScan.checked?'<p class="hk-muted">'+either('Проверено на целевом тире','Checked at target tier')+': '+p.targetScan.checked+' · '+either('готовых пропущено','finished skipped')+': '+p.targetScan.skipped+(p.targetScan.errors?' · '+either('ошибок','errors')+': '+p.targetScan.errors:'')+'</p>':'')+
      (s.totalEvents!=='any'&&!p.totalEventsKnown?'<p class="hk-muted">⚠ '+either('Приоритет «Всего событий» не применён: точные данные есть не у всех кандидатов.','Total-events priority was not applied: exact data is unavailable for some candidates.')+'</p>':'')+
      (p.meta?.unmapped?'<p class="hk-muted">⚠ '+either('Без района','Without district')+': '+p.meta.unmapped+'</p>':'')+(p.meta?.unknownType?'<p class="hk-muted">⚠ '+either('Тип неизвестен','Unknown type')+': '+p.meta.unknownType+'</p>':'')+
      '<div class="hk-cards">'+(rows||'<p class="hk-muted">'+either('Подходящих зданий нет.','No eligible buildings.')+'</p>')+'</div>'+(p.selected.length>20?'<p class="hk-muted">… +'+(p.selected.length-20)+'</p>':'')+'</div>':
      '<div class="hk-cardbox hk-ex-wide hk-ex-empty"><span>'+either('Настройте фильтры и нажмите «Рассчитать план». E2 только читает данные — ничего не тратит.','Configure filters and press “Calculate plan”. E2 only reads data and spends nothing.')+'</span></div>';

    box.innerHTML='<style>'+
      '#hk-explore-content .hk-ex-layout{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(300px,.9fr);gap:12px;align-items:start}'+
      '#hk-explore-content .hk-ex-wide{grid-column:1/-1}'+
      '#hk-explore-content .hk-ex-fields{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:10px}'+
      '#hk-explore-content .hk-ex-field{display:flex;flex-direction:column;gap:5px;min-width:0}'+
      '#hk-explore-content .hk-ex-field>span{font-size:12px;font-weight:700}'+
      '#hk-explore-content .hk-ex-field select,#hk-explore-content .hk-ex-field input{width:100%;min-width:0;box-sizing:border-box}'+
      '#hk-explore-content .hk-ex-tiers{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px;margin-top:7px}'+
      '#hk-explore-content .hk-ex-tier{display:flex;align-items:center;justify-content:space-between;gap:8px;min-width:0;padding:8px 9px;border:1px solid rgba(255,255,255,.09);border-radius:9px;background:rgba(255,255,255,.025)}'+
      '#hk-explore-content .hk-ex-tier span{display:flex;align-items:center;gap:4px;white-space:nowrap}'+
      '#hk-explore-content .hk-ex-tier small{white-space:nowrap}'+
      '#hk-explore-content .hk-ex-target-row{display:grid;grid-template-columns:minmax(180px,.65fr) minmax(0,1.35fr);gap:10px;margin-top:10px;align-items:start}'+
      '#hk-explore-content .hk-ex-toggles{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px}'+
      '#hk-explore-content .hk-ex-toggle{display:flex;align-items:flex-start;gap:7px;padding:8px 9px;border:1px solid rgba(255,255,255,.09);border-radius:9px;background:rgba(255,255,255,.025);font-size:12px;line-height:1.25}'+
      '#hk-explore-content .hk-ex-toggle input{margin-top:2px;flex:0 0 auto}'+
      '#hk-explore-content .hk-ex-priority{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;margin-top:10px}'+
      '#hk-explore-content .hk-ex-delays{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;margin-top:10px}'+
      '#hk-explore-content .hk-ex-chips{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px;margin-top:8px}'+
      '#hk-explore-content .hk-ex-chip{display:flex;flex-direction:column;gap:2px;padding:7px 8px;border:1px solid rgba(255,255,255,.07);border-radius:8px;background:rgba(255,255,255,.02)}'+
      '#hk-explore-content .hk-ex-chip small{font-size:11px}'+
      '#hk-explore-content .hk-ex-section-title{display:flex;justify-content:space-between;align-items:center;gap:8px}'+
      '#hk-explore-content .hk-ex-section-title small{font-weight:400}'+
      '#hk-explore-content .hk-ex-empty{padding:11px 13px}'+
      '#hk-explore-content .hk-ex-actions{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}'+
      '@media(max-width:900px){#hk-explore-content .hk-ex-layout{grid-template-columns:1fr}#hk-explore-content .hk-ex-wide{grid-column:auto}#hk-explore-content .hk-ex-fields{grid-template-columns:repeat(2,minmax(0,1fr))}#hk-explore-content .hk-ex-tiers{grid-template-columns:repeat(2,minmax(0,1fr))}#hk-explore-content .hk-ex-target-row{grid-template-columns:1fr}#hk-explore-content .hk-ex-toggles{grid-template-columns:1fr}#hk-explore-content .hk-ex-chips{grid-template-columns:repeat(2,minmax(0,1fr))}}'+
      '@media(max-width:520px){#hk-explore-content .hk-ex-fields,#hk-explore-content .hk-ex-priority,#hk-explore-content .hk-ex-delays{grid-template-columns:1fr}}'+
      '</style>'+
      '<div class="hk-clan-head"><div><h3>'+either('Исследование зданий','Explore Buildings')+'</h3><small>'+either('E2 · read-only планирование','E2 · read-only planning')+'</small></div><button id="hk-ex-refresh" class="hk-secondary" '+(exploreBusy?'disabled':'')+'>'+either('Обновить','Refresh')+'</button></div>'+
      '<div class="hk-ex-layout">'+
        '<div class="hk-cardbox hk-ex-wide"><div class="hk-ex-section-title"><b>'+either('Возможности аккаунта','Account capabilities')+'</b><small class="hk-muted">'+either('Уровень','Level')+' '+Number(level).toLocaleString(locale())+' · Remort '+(c?(Number(c.level||0)+' · '+(c.status==='ACTIVE'?either('активен','active'):either('заблокирован','locked'))):either('не найден','not found'))+' · '+either('автобои','auto battles')+' '+(auto>=0?either('до ','up to ')+exploreTierLabel(auto):either('нет','none'))+'</small></div><div class="hk-ex-chips">'+modeChips+'</div></div>'+
        '<div class="hk-cardbox hk-ex-wide"><div class="hk-ex-section-title"><b>'+either('Здания для обработки','Buildings to include')+'</b><small class="hk-muted">'+either('всего / бои завершены','total / battles done')+'</small></div>'+
          '<div class="hk-ex-fields">'+
            '<label class="hk-ex-field"><span>'+either('Район','District')+'</span><select id="hk-ex-district">'+exploreDistrictOptions(s.districtId)+'</select></label>'+
            '<label class="hk-ex-field"><span>'+either('Тип','Type')+'</span><select id="hk-ex-type"><option value="all" '+(s.buildingType==='all'?'selected':'')+'>'+either('Все','All')+'</option><option value="normal" '+(s.buildingType==='normal'?'selected':'')+'>'+either('Обычные','Normal')+'</option><option value="investment" '+(s.buildingType==='investment'?'selected':'')+'>'+either('Инвестиционные','Investment')+'</option></select></label>'+
            '<label class="hk-ex-field"><span>'+either('Максимум зданий','Maximum buildings')+'</span><input id="hk-ex-max" type="number" min="1" max="5000" value="'+s.maxBuildings+'"></label>'+
          '</div>'+
          '<p class="hk-muted" style="margin:10px 0 0">'+either('Стартовые тиры','Starting tiers')+'</p><div class="hk-ex-tiers">'+tiers+'</div>'+
          '<div class="hk-ex-target-row">'+
            '<label class="hk-ex-field"><span>'+either('Целевой тир','Target tier')+'</span><select id="hk-ex-target">'+targets+'</select></label>'+
            '<div class="hk-ex-toggles">'+
              '<label class="hk-ex-toggle"><input id="hk-ex-target-tier" type="checkbox" '+(s.exploreTargetTier?'checked':'')+' '+(targetOk?'':'disabled')+'><span>'+either('Исследовать целевой тир','Explore target tier')+'</span></label>'+
              '<label class="hk-ex-toggle"><input id="hk-ex-target-battles" type="checkbox" '+(s.exploreTargetBattles?'checked':'')+' '+(targetOk&&s.exploreTargetTier?'':'disabled')+'><span>'+either('Завершить бои на целевом тире','Complete target-tier battles')+'</span></label>'+
              '<label class="hk-ex-toggle"><input id="hk-ex-buy" type="checkbox" '+(s.buyMissingMaterials?'checked':'')+'><span>'+either('Автопокупка балок/гвоздей · с E3','Auto-buy beams/nails · from E3')+'</span></label>'+
            '</div>'+
          '</div>'+
        '</div>'+
        '<div class="hk-cardbox"><b>'+either('Приоритет','Priority')+'</b><div class="hk-ex-priority">'+
          '<label class="hk-ex-field"><span>'+either('Бой','Battle')+'</span><select id="hk-ex-pr-battle">'+explorePrOptions(s.battleLevel)+'</select></label>'+
          '<label class="hk-ex-field"><span>'+either('Уровень здания','Building level')+'</span><select id="hk-ex-pr-level">'+explorePrOptions(s.level)+'</select></label>'+
          '<label class="hk-ex-field"><span>'+either('До следующего тира','Next-tier level')+'</span><select id="hk-ex-pr-next">'+explorePrOptions(s.nextTierLevel)+'</select></label>'+
          '<label class="hk-ex-field"><span>'+either('Всего событий','Total events')+'</span><select id="hk-ex-pr-events">'+explorePrOptions(s.totalEvents)+'</select></label>'+
        '</div></div>'+
        '<div class="hk-cardbox"><b>'+either('Задержки будущего запуска','Future run delays')+'</b><div class="hk-ex-delays">'+
          '<label class="hk-ex-field"><span>'+either('Действие мин., сек','Action min, sec')+'</span><input id="hk-ex-action-min" type="number" min="0" step="0.1" value="'+s.actionDelayMinMs/1000+'"></label>'+
          '<label class="hk-ex-field"><span>'+either('Действие макс., сек','Action max, sec')+'</span><input id="hk-ex-action-max" type="number" min="0" step="0.1" value="'+s.actionDelayMaxMs/1000+'"></label>'+
          '<label class="hk-ex-field"><span>'+either('Бой, сек','Battle, sec')+'</span><input id="hk-ex-battle" type="number" min="0" step="0.1" value="'+s.battleDelayMs/1000+'"></label>'+
          '<label class="hk-ex-field"><span>'+either('Между зданиями мин., сек','Between min, sec')+'</span><input id="hk-ex-between-min" type="number" min="0" step="0.1" value="'+s.betweenBuildingsDelayMinMs/1000+'"></label>'+
          '<label class="hk-ex-field"><span>'+either('Между зданиями макс., сек','Between max, sec')+'</span><input id="hk-ex-between-max" type="number" min="0" step="0.1" value="'+s.betweenBuildingsDelayMaxMs/1000+'"></label>'+
        '</div></div>'+
        '<div class="hk-ex-actions hk-ex-wide"><button id="hk-ex-plan" class="hk-primary" '+(exploreBusy?'disabled':'')+'>'+(exploreBusy?either('Считаю…','Calculating…'):either('Рассчитать план','Calculate plan'))+'</button><button class="hk-secondary" disabled>'+either('Запуск появится на E3','Run becomes available in E3')+'</button></div>'+
        summary+
      '</div>';
    const changed=()=>{exploreReadSettings();explorePlan=null;renderExplore();};
    box.querySelector('#hk-ex-refresh')?.addEventListener('click',()=>void refreshExplore(true));
    box.querySelector('#hk-ex-plan')?.addEventListener('click',()=>{exploreReadSettings();explorePlan=null;void explorePreparePlan();});
    box.querySelectorAll('select,input').forEach(n=>n.addEventListener('change',changed));
  }
'''

s = s[:a] + new_fn + s[b:]

# E2 UI-only safety checks.
assert "explore-readonly-plan-20260920-r3-ui" in s
assert "function exploreBuildPlan()" in s
assert "hk-ex-layout" in s
assert "hk-ex-target-tier" in s and "hk-ex-pr-battle" in s and "hk-ex-action-min" in s

p.write_text(s)
