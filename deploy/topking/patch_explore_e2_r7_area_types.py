from pathlib import Path

p=Path("/tmp/HamsterKingMobile.user.js")
s=p.read_text()

old_marker="const HK_EXPLORE_CANON_REV='explore-readonly-plan-20260920-r6-fresh-meta';"
new_marker="const HK_EXPLORE_CANON_REV='explore-readonly-plan-20260920-r7-area-types';"
assert s.count(old_marker)==1, s.count(old_marker)
s=s.replace(old_marker,new_marker,1)

old="""  function exploreBuildingType(...src){
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
    const st=sourceState||{},pk=String(playerIdentity(st?.player||{})||'');
    if(!force&&exploreMeta?.playerKey===pk&&Date.now()-Number(exploreMeta.loadedAt||0)<600000)return exploreMeta;
    mapHydrateBuildingAreas();await mapEnsureOwnedBuildingAreaIndex(false);
    const active=exploreActive(st),owned=(st?.areas?.areas||[]).filter(r=>r?.gamearea_id||r?.area_id),ownedMap=new Map(owned.map(r=>[String(r?.gamearea_id||r?.area_id||''),r]));
    const areaIds=[...new Set(active.map(r=>String(mapBuildingAreas.get(r.id)||'')).filter(Boolean))];
"""
new="""  function exploreBuildingType(...src){
    for(const x of src){if(!x||typeof x!=='object')continue;
      for(const raw of [x?.building_type,x?.buildingType,x?.meta?.building_type,x?.meta?.buildingType]){
        const value=String(raw||'').trim().toLowerCase();
        if(value==='normal'||value==='investment')return value;
      }
      for(const raw of [x?.is_investment,x?.isInvestment,x?.is_invest,x?.isInvest]){
        if(typeof raw==='boolean')return raw?'investment':'normal';
      }
    }
    return '';
  }
  function exploreAreaIndex(st){
    const result=new Map(),pk=String(playerIdentity(st?.player||{})||'');
    const cachedRoot=load().mapBuildingAreasByPlayer,cached=cachedRoot&&typeof cachedRoot==='object'&&cachedRoot[pk]&&typeof cachedRoot[pk]==='object'?cachedRoot[pk]:{};
    for(const [buildingId,areaId] of Object.entries(cached)){if(buildingId&&areaId)result.set(String(buildingId),String(areaId));}
    for(const row of exploreActive(st)){
      const id=String(row?.id||''),direct=String(row?.gamearea_id||row?.area_id||row?.gameAreaId||'');
      if(id&&direct)result.set(id,direct);
      else if(id&&mapBuildingAreas.has(id))result.set(id,String(mapBuildingAreas.get(id)||''));
    }
    return result;
  }
  async function exploreLoadMeta(force=false,sourceState=exploreState()){
    const st=sourceState||{},pk=String(playerIdentity(st?.player||{})||'');
    if(!force&&exploreMeta?.playerKey===pk&&Date.now()-Number(exploreMeta.loadedAt||0)<600000)return exploreMeta;
    const active=exploreActive(st),areaIndex=exploreAreaIndex(st),owned=(st?.areas?.areas||[]).filter(r=>r?.gamearea_id||r?.area_id),ownedMap=new Map(owned.map(r=>[String(r?.gamearea_id||r?.area_id||''),r]));
    const areaIds=[...new Set(active.map(r=>String(areaIndex.get(r.id)||'')).filter(Boolean))];
"""
assert s.count(old)==1, s.count(old)
s=s.replace(old,new,1)

old="""      const dm=new Map(defs.map(r=>[String(r?.building_id||''),r]));
      for(const row of active){if(String(mapBuildingAreas.get(row.id)||'')!==areaId)continue;const d=dm.get(row.id)||null,study=buildingStudyCache.get(row.id)||null;
        const totalEvents=exploreTotalEvents(study,row,d),buildingType=exploreBuildingType(d,row,study);
        buildingMeta[row.id]={areaId,buildingType,isInvest:buildingType==='investment'?true:buildingType==='normal'?false:null,totalEvents};if(d)mapRememberBuildingArea(row.id,areaId);}
    }};
    await Promise.all(Array.from({length:Math.min(4,Math.max(1,areaIds.length))},()=>worker()));
    for(const r of active)if(!buildingMeta[r.id]){const study=buildingStudyCache.get(r.id)||null,totalEvents=exploreTotalEvents(study,r),buildingType=exploreBuildingType(r,study);
      buildingMeta[r.id]={areaId:String(mapBuildingAreas.get(r.id)||''),buildingType,isInvest:buildingType==='investment'?true:buildingType==='normal'?false:null,totalEvents};}
"""
new="""      const dm=new Map(defs.map(r=>[String(r?.building_id||''),r])),investList=full?.info?.invest_building_list,investKnown=Array.isArray(investList),investSet=new Set((investKnown?investList:[]).map(String));
      for(const row of active){if(String(areaIndex.get(row.id)||'')!==areaId)continue;const d=dm.get(row.id)||null,study=buildingStudyCache.get(row.id)||null;
        const totalEvents=exploreTotalEvents(study,row,d);let buildingType=exploreBuildingType(d,row,study);
        if(!buildingType&&investKnown)buildingType=investSet.has(row.id)?'investment':'normal';
        buildingMeta[row.id]={areaId,buildingType,isInvest:buildingType==='investment'?true:buildingType==='normal'?false:null,totalEvents};}
    }};
    await Promise.all(Array.from({length:Math.min(4,Math.max(1,areaIds.length))},()=>worker()));
    for(const r of active)if(!buildingMeta[r.id]){const study=buildingStudyCache.get(r.id)||null,totalEvents=exploreTotalEvents(study,r),buildingType=exploreBuildingType(r,study);
      buildingMeta[r.id]={areaId:String(areaIndex.get(r.id)||''),buildingType,isInvest:buildingType==='investment'?true:buildingType==='normal'?false:null,totalEvents};}
"""
assert s.count(old)==1, s.count(old)
s=s.replace(old,new,1)

# Restore honest labels.
old_label="""<option value="normal" '+(s.buildingType==='normal'?'selected':'')+'>'+either('Обычные (>20 событий)','Normal (>20 events)')+'</option><option value="investment" '+(s.buildingType==='investment'?'selected':'')+'>'+either('Инвестиционные (до 20 событий)','Investment (up to 20 events)')+'</option>"""
new_label="""<option value="normal" '+(s.buildingType==='normal'?'selected':'')+'>'+either('Обычные','Normal')+'</option><option value="investment" '+(s.buildingType==='investment'?'selected':'')+'>'+either('Инвестиционные','Investment')+'</option>"""
assert s.count(old_label)==1, s.count(old_label)
s=s.replace(old_label,new_label,1)

block=s[s.index("  const HK_EXPLORE_CANON_REV="):s.index("  async function acceptBuildingStudy(",s.index("  const HK_EXPLORE_CANON_REV="))]
assert "explore-readonly-plan-20260920-r7-area-types" in block
assert "function exploreAreaIndex(st)" in block
assert "invest_building_list" in block
assert "Number(total)>20" not in block
forbidden=["/player/building/fast_completion","/player/battle/fast","/player/building/remort?","/player/building/fast_remort","/shop/buy"]
assert not [x for x in forbidden if x in block]
assert "const HK_MAP_READ_CONCURRENCY = 5;" in s
p.write_text(s)
