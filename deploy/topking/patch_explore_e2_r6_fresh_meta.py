from pathlib import Path

p=Path("/tmp/HamsterKingMobile.user.js")
s=p.read_text()

old_marker="const HK_EXPLORE_CANON_REV='explore-readonly-plan-20260920-r5-filters';"
new_marker="const HK_EXPLORE_CANON_REV='explore-readonly-plan-20260920-r6-fresh-meta';"
assert s.count(old_marker)==1, s.count(old_marker)
s=s.replace(old_marker,new_marker,1)

old="""  let explorePlan=null,exploreBusy=false,exploreMeta=null;

  function exploreTierLabel(v){v=Number(v);return v===8?either('Мгновенно MAX','Instant MAX'):(EXPLORE_TIERS.find(r=>r.value===v)?.label||('Tier '+(v+1)));}"""
new="""  let explorePlan=null,exploreBusy=false,exploreMeta=null,explorePlayerState=null;

  function exploreState(){return explorePlayerState&&typeof explorePlayerState==='object'?explorePlayerState:{};}
  async function exploreReadFreshPlayer(reason='explore'){
    const value=await apiJson('/player/me','POST');
    const hasBuildings=Array.isArray(value?.buildings)||Array.isArray(value?.player?.buildings);
    if(!value?.player||!hasBuildings)throw new Error(either('Игра не вернула полное состояние аккаунта','Game did not return a complete account state'));
    explorePlayerState=value;
    playerDocument=value;
    recordDiagnostic('explore-fresh-player',{reason,buildings:buildingCanonActiveRows(value).length,playerLevel:Number(value?.player?.level||0)});
    return value;
  }

  function exploreTierLabel(v){v=Number(v);return v===8?either('Мгновенно MAX','Instant MAX'):(EXPLORE_TIERS.find(r=>r.value===v)?.label||('Tier '+(v+1)));}"""
assert s.count(old)==1, s.count(old)
s=s.replace(old,new,1)

s=s.replace(
"function exploreConsigliere(st=hkStateStore.snapshot||playerDocument||{}){",
"function exploreConsigliere(st=exploreState()){",
1
)
s=s.replace(
"function exploreActive(st=hkStateStore.snapshot||playerDocument||{}){",
"function exploreActive(st=exploreState()){",
1
)

old="""  async function exploreLoadMeta(force=false){
    const st=hkStateStore.snapshot||playerDocument||{},pk=String(playerIdentity(st?.player||{})||'');"""
new="""  function exploreBuildingType(...src){
    for(const x of src){if(!x||typeof x!=='object')continue;
      for(const raw of [x?.building_type,x?.buildingType,x?.meta?.building_type,x?.meta?.buildingType]){
        const value=String(raw||'').trim().toLowerCase();
        if(value==='normal'||value==='investment')return value;
      }
    }
    const total=exploreTotalEvents(...src);
    return total===null||total===undefined?'':(Number(total)>20?'normal':'investment');
  }
  async function exploreLoadMeta(force=false,sourceState=exploreState()){
    const st=sourceState||{},pk=String(playerIdentity(st?.player||{})||'');"""
assert s.count(old)==1, s.count(old)
s=s.replace(old,new,1)

old="""      const list=full?.info?.invest_building_list,known=Array.isArray(list),invest=new Set((known?list:[]).map(String)),dm=new Map(defs.map(r=>[String(r?.building_id||''),r]));
      for(const row of active){if(String(mapBuildingAreas.get(row.id)||'')!==areaId)continue;const d=dm.get(row.id)||null;let isInvest=null;
        if(known)isInvest=invest.has(row.id);else if(typeof row?.is_investment==='boolean')isInvest=!!row.is_investment;else if(typeof row?.is_invest==='boolean')isInvest=!!row.is_invest;
        buildingMeta[row.id]={areaId,isInvest,totalEvents:exploreTotalEvents(buildingStudyCache.get(row.id),row,d)};if(d)mapRememberBuildingArea(row.id,areaId);}
    }};
    await Promise.all(Array.from({length:Math.min(4,Math.max(1,areaIds.length))},()=>worker()));
    for(const r of active)if(!buildingMeta[r.id]){let isInvest=null;if(typeof r?.is_investment==='boolean')isInvest=!!r.is_investment;else if(typeof r?.is_invest==='boolean')isInvest=!!r.is_invest;
      buildingMeta[r.id]={areaId:String(mapBuildingAreas.get(r.id)||''),isInvest,totalEvents:exploreTotalEvents(buildingStudyCache.get(r.id),r)};}
    districts.sort((a,b)=>a.label.localeCompare(b.label));
    exploreMeta={playerKey:pk,loadedAt:Date.now(),districts,buildingMeta,errors,unmapped:active.filter(r=>!buildingMeta[r.id]?.areaId).length,unknownType:active.filter(r=>buildingMeta[r.id]?.isInvest===null).length};return exploreMeta;
  }"""
new="""      const dm=new Map(defs.map(r=>[String(r?.building_id||''),r]));
      for(const row of active){if(String(mapBuildingAreas.get(row.id)||'')!==areaId)continue;const d=dm.get(row.id)||null,study=buildingStudyCache.get(row.id)||null;
        const totalEvents=exploreTotalEvents(study,row,d),buildingType=exploreBuildingType(d,row,study);
        buildingMeta[row.id]={areaId,buildingType,isInvest:buildingType==='investment'?true:buildingType==='normal'?false:null,totalEvents};if(d)mapRememberBuildingArea(row.id,areaId);}
    }};
    await Promise.all(Array.from({length:Math.min(4,Math.max(1,areaIds.length))},()=>worker()));
    for(const r of active)if(!buildingMeta[r.id]){const study=buildingStudyCache.get(r.id)||null,totalEvents=exploreTotalEvents(study,r),buildingType=exploreBuildingType(r,study);
      buildingMeta[r.id]={areaId:String(mapBuildingAreas.get(r.id)||''),buildingType,isInvest:buildingType==='investment'?true:buildingType==='normal'?false:null,totalEvents};}
    districts.sort((a,b)=>a.label.localeCompare(b.label));
    exploreMeta={playerKey:pk,loadedAt:Date.now(),districts,buildingMeta,errors,unmapped:active.filter(r=>!buildingMeta[r.id]?.areaId).length,unknownType:active.filter(r=>!buildingMeta[r.id]?.buildingType).length};return exploreMeta;
  }"""
assert s.count(old)==1, s.count(old)
s=s.replace(old,new,1)

old="""  function exploreFiltered(settings,st,meta){return exploreActive(st).filter(r=>{const m=meta?.buildingMeta?.[r.id]||{};if(settings.districtId!=='all'&&String(m.areaId||'')!==settings.districtId)return false;
    if(settings.buildingType==='investment'&&m.isInvest!==true)return false;if(settings.buildingType==='normal'&&m.isInvest!==false)return false;return true;});}"""
new="""  function exploreFiltered(settings,st,meta){return exploreActive(st).filter(r=>{const m=meta?.buildingMeta?.[r.id]||{};if(settings.districtId!=='all'&&String(m.areaId||'')!==settings.districtId)return false;
    if(settings.buildingType!=='all'&&String(m.buildingType||'')!==settings.buildingType)return false;return true;});}"""
assert s.count(old)==1, s.count(old)
s=s.replace(old,new,1)

old="""      .map(r=>{const m=meta?.buildingMeta?.[r.id]||{};return {...r,areaId:String(m.areaId||''),isInvest:m.isInvest,totalEvents:m.totalEvents};});"""
new="""      .map(r=>{const m=meta?.buildingMeta?.[r.id]||{};return {...r,areaId:String(m.areaId||''),buildingType:String(m.buildingType||''),isInvest:m.isInvest,totalEvents:m.totalEvents};});"""
assert s.count(old)==1, s.count(old)
s=s.replace(old,new,1)

old="""  async function exploreBuildPlan(){
    playerDocument=await hkAuthoritativePlayerRead('explore:plan');const settings=exploreSettings(),meta=await exploreLoadMeta(false),basic=exploreBasic(settings,playerDocument,meta),scan=await exploreScanTarget(basic.rows,settings);
    let candidates=scan.rows;if(!settings.exploreTargetTier)candidates=candidates.slice(0,settings.maxBuildings);
    if(settings.totalEvents!=='any'&&basic.totalEventsKnown){candidates=exploreStable(candidates,r=>r.next_tier_level,settings.nextTierLevel);candidates=exploreStable(candidates,r=>r.level,settings.level);
      candidates=exploreStable(candidates,r=>r.totalEvents,settings.totalEvents);candidates=exploreStable(candidates,r=>r.battle_level,settings.battleLevel);}
    const filtered=exploreFiltered(settings,playerDocument,meta),c=exploreConsigliere(playerDocument),level=Number(playerDocument?.player?.level||0);
    return {settings,meta,candidates,selected:settings.exploreTargetTier?candidates.slice(0,settings.maxBuildings):candidates,filteredCount:filtered.length,tierCounts:exploreCounts(filtered),consigliere:c,autoMaxTier:exploreAutoTier(c),playerLevel:level,tierModes:exploreTierModes(level),targetScan:scan,totalEventsKnown:basic.totalEventsKnown};
  }"""
new="""  async function exploreBuildPlan(){
    const state=await exploreReadFreshPlayer('explore:plan'),settings=exploreSettings(),meta=await exploreLoadMeta(false,state),basic=exploreBasic(settings,state,meta),scan=await exploreScanTarget(basic.rows,settings);
    let candidates=scan.rows;if(!settings.exploreTargetTier)candidates=candidates.slice(0,settings.maxBuildings);
    if(settings.totalEvents!=='any'&&basic.totalEventsKnown){candidates=exploreStable(candidates,r=>r.next_tier_level,settings.nextTierLevel);candidates=exploreStable(candidates,r=>r.level,settings.level);
      candidates=exploreStable(candidates,r=>r.totalEvents,settings.totalEvents);candidates=exploreStable(candidates,r=>r.battle_level,settings.battleLevel);}
    const filtered=exploreFiltered(settings,state,meta),c=exploreConsigliere(state),level=Number(state?.player?.level||0);
    return {settings,meta,candidates,selected:settings.exploreTargetTier?candidates.slice(0,settings.maxBuildings):candidates,filteredCount:filtered.length,tierCounts:exploreCounts(filtered),consigliere:c,autoMaxTier:exploreAutoTier(c),playerLevel:level,tierModes:exploreTierModes(level),targetScan:scan,totalEventsKnown:basic.totalEventsKnown};
  }"""
assert s.count(old)==1, s.count(old)
s=s.replace(old,new,1)

s=s.replace(
"const box=root?.querySelector('#hk-explore-content');if(!box)return;const s=exploreSettings(),p=explorePlan,st=hkStateStore.snapshot||playerDocument||{},active=exploreActive(st),c=p?.consigliere||exploreConsigliere(st);",
"const box=root?.querySelector('#hk-explore-content');if(!box)return;const s=exploreSettings(),p=explorePlan,st=exploreState(),ready=!!st?.player&&(Array.isArray(st?.buildings)||Array.isArray(st?.player?.buildings)),active=ready?exploreActive(st):[],c=p?.consigliere||(ready?exploreConsigliere(st):null);",
1
)
s=s.replace(
"const auto=p?.autoMaxTier??exploreAutoTier(c),level=p?.playerLevel??Number(st?.player?.level||0),modes=p?.tierModes||exploreTierModes(level),counts=p?.tierCounts||exploreCounts(active),targetOk=s.targetTier>=1&&s.targetTier<=6;",
"const auto=p?.autoMaxTier??(ready?exploreAutoTier(c):-1),level=p?.playerLevel??(ready?Number(st?.player?.level||0):null),modes=p?.tierModes||(ready?exploreTierModes(level):{}),counts=p?.tierCounts||exploreCounts(active),targetOk=s.targetTier>=1&&s.targetTier<=6;",
1
)
s=s.replace(
"const modeLine=EXPLORE_TIERS.map(t=>'<span><b>'+t.label+'</b> '+(modes[t.value]==='fast'?either('быстро','fast'):modes[t.value]==='auto'?either('авто','auto'):either('вручную','manual'))+'</span>').join('');",
"const modeLine=EXPLORE_TIERS.map(t=>'<span><b>'+t.label+'</b> '+(!ready?'—':modes[t.value]==='fast'?either('быстро','fast'):modes[t.value]==='auto'?either('авто','auto'):either('вручную','manual'))+'</span>').join('');",
1
)
s=s.replace(
"either('Уровень','Level')+': '+Number(level).toLocaleString(locale())+' · Remort Consigliere: '+(c?(Number(c.level||0)+' · '+(c.status==='ACTIVE'?either('активен','active'):either('заблокирован','locked'))):either('не найден','not found'))+' · '+either('Автобои','Auto battles')+': '+(auto>=0?either('до ','up to ')+exploreTierLabel(auto):either('нет','none'))",
"either('Уровень','Level')+': '+(ready?Number(level).toLocaleString(locale()):'—')+' · Remort Consigliere: '+(!ready?'—':c?(Number(c.level||0)+' · '+(c.status==='ACTIVE'?either('активен','active'):either('заблокирован','locked'))):either('не найден','not found'))+' · '+either('Автобои','Auto battles')+': '+(!ready?'—':auto>=0?either('до ','up to ')+exploreTierLabel(auto):either('нет','none'))",
1
)
s=s.replace(
"<option value="normal" '+(s.buildingType==='normal'?'selected':'')+'>'+either('Обычные','Normal')+'</option><option value="investment" '+(s.buildingType==='investment'?'selected':'')+'>'+either('Инвестиционные','Investment')+'</option>",
"<option value="normal" '+(s.buildingType==='normal'?'selected':'')+'>'+either('Обычные (>20 событий)','Normal (>20 events)')+'</option><option value="investment" '+(s.buildingType==='investment'?'selected':'')+'>'+either('Инвестиционные (до 20 событий)','Investment (up to 20 events)')+'</option>",
1
)
s=s.replace(
"const state=hkStateStore.snapshot||playerDocument||{},summary=box.querySelector('#hk-ex-filter-summary'),ready=!!state?.player&&Array.isArray(state?.buildings),metaReady=!!exploreMeta;",
"const state=exploreState(),summary=box.querySelector('#hk-ex-filter-summary'),ready=!!state?.player&&(Array.isArray(state?.buildings)||Array.isArray(state?.player?.buildings)),metaReady=!!exploreMeta&&exploreMeta.playerKey===String(playerIdentity(state?.player||{})||'');",
1
)

old="""  async function refreshExplore(force=false){
    if(!requireLicense())return null;if(exploreBusy)return playerDocument;exploreBusy=true;renderExplore();
    try{playerDocument=await hkAuthoritativePlayerRead('explore:view');exploreMeta=await exploreLoadMeta(force);explorePlan=null;if(force)log(either('Исследование обновлено','Explore refreshed'),'ok');return playerDocument;}
    catch(e){log(either('Ошибка чтения исследования','Explore read error')+': '+(e?.message||e),'warn');return null;}finally{exploreBusy=false;renderExplore();}
  }"""
new="""  async function refreshExplore(force=false){
    if(!requireLicense())return null;if(exploreBusy)return explorePlayerState;exploreBusy=true;renderExplore();
    try{const state=await exploreReadFreshPlayer('explore:view');exploreMeta=await exploreLoadMeta(force,state);explorePlan=null;if(force)log(either('Исследование обновлено','Explore refreshed'),'ok');return state;}
    catch(e){explorePlayerState=null;exploreMeta=null;log(either('Ошибка чтения исследования','Explore read error')+': '+(e?.message||e),'warn');return null;}finally{exploreBusy=false;renderExplore();}
  }"""
assert s.count(old)==1, s.count(old)
s=s.replace(old,new,1)

# Cache player key should follow the exact Explore snapshot.
s=s.replace(
"function exploreCache(){const pk=String(playerIdentity((hkStateStore.snapshot||playerDocument)?.player||{})||''),rootCache=load().exploreCanonProgressByPlayer;",
"function exploreCache(){const pk=String(playerIdentity(exploreState()?.player||{})||''),rootCache=load().exploreCanonProgressByPlayer;",
1
)

# Safety and scope assertions.
assert "explore-readonly-plan-20260920-r6-fresh-meta" in s
assert "function exploreBuildingType(...src)" in s
assert "Number(total)>20?'normal':'investment'" in s
assert "invest_building_list" not in s[s.index("  const HK_EXPLORE_CANON_REV="):s.index("  async function acceptBuildingStudy(",s.index("  const HK_EXPLORE_CANON_REV="))]
forbidden=["/player/building/fast_completion","/player/battle/fast","/player/building/remort?","/player/building/fast_remort","/shop/buy"]
block=s[s.index("  const HK_EXPLORE_CANON_REV="):s.index("  async function acceptBuildingStudy(",s.index("  const HK_EXPLORE_CANON_REV="))]
assert not [x for x in forbidden if x in block]
assert "const HK_MAP_READ_CONCURRENCY = 5;" in s
p.write_text(s)
