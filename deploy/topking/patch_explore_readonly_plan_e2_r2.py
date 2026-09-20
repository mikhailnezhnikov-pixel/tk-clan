from pathlib import Path

p = Path("/tmp/HamsterKingMobile.user.js")
s = p.read_text()
a = s.index("  const HK_EXPLORE_CANON_REV='explore-readonly-plan-20260920-r1';")
b = s.index("  async function acceptBuildingStudy(", a)
block = s[a:b]

def rep(old, new):
    global block
    count = block.count(old)
    assert count == 1, (count, old[:140])
    block = block.replace(old, new, 1)

rep(
    "const HK_EXPLORE_CANON_REV='explore-readonly-plan-20260920-r1';",
    "const HK_EXPLORE_CANON_REV='explore-readonly-plan-20260920-r2';",
)

rep(
"""    const target=clamp(x.targetTier,0,8,3);
    return {
      maxBuildings:clamp(x.maxBuildings,1,5000,500),startTiers:st.length?st:[0,1,2],targetTier:target,""",
"""    const target=clamp(x.targetTier,1,8,3),targetActionsAllowed=target>=1&&target<=6&&x.exploreTargetTier===true;
    const maxStart=targetActionsAllowed?target:Math.min(target,7)-1,selectedStart=st.filter(v=>v<=maxStart);
    return {
      maxBuildings:clamp(x.maxBuildings,1,5000,500),startTiers:selectedStart.length?selectedStart:[0],targetTier:target,""",
)

rep(
"""      exploreTargetTier:target<=6&&x.exploreTargetTier===true,exploreTargetBattles:target<=6&&x.exploreTargetTier===true&&x.exploreTargetBattles===true""",
"""      exploreTargetTier:targetActionsAllowed,exploreTargetBattles:targetActionsAllowed&&x.exploreTargetBattles===true""",
)

rep(
"""  function exploreSaveSettings(x){
    x={...x,startTiers:[...new Set((x.startTiers||[]).map(Number).filter(v=>Number.isInteger(v)&&v>=0&&v<=7))],
      maxBuildings:Math.min(5000,Math.max(1,Math.trunc(Number(x.maxBuildings)||500))),targetTier:Math.min(8,Math.max(0,Math.trunc(Number(x.targetTier)||0)))};
    if(x.actionDelayMaxMs<x.actionDelayMinMs)x.actionDelayMaxMs=x.actionDelayMinMs;
    if(x.betweenBuildingsDelayMaxMs<x.betweenBuildingsDelayMinMs)x.betweenBuildingsDelayMaxMs=x.betweenBuildingsDelayMinMs;
    if(x.targetTier>6){x.exploreTargetTier=false;x.exploreTargetBattles=false;} if(!x.exploreTargetTier)x.exploreTargetBattles=false;
    save({exploreCanonSettings:x});return x;
  }""",
"""  function exploreSaveSettings(x){
    const target=Math.min(8,Math.max(1,Math.trunc(Number(x.targetTier)||3))),targetActionsAllowed=target>=1&&target<=6&&x.exploreTargetTier===true;
    const maxStart=targetActionsAllowed?target:Math.min(target,7)-1;
    x={...x,targetTier:target,startTiers:[...new Set((x.startTiers||[]).map(Number).filter(v=>Number.isInteger(v)&&v>=0&&v<=7&&v<=maxStart))],
      maxBuildings:Math.min(5000,Math.max(1,Math.trunc(Number(x.maxBuildings)||500)))};
    if(!x.startTiers.length)x.startTiers=[0];
    if(x.actionDelayMaxMs<x.actionDelayMinMs)x.actionDelayMaxMs=x.actionDelayMinMs;
    if(x.betweenBuildingsDelayMaxMs<x.betweenBuildingsDelayMinMs)x.betweenBuildingsDelayMaxMs=x.betweenBuildingsDelayMinMs;
    x.exploreTargetTier=targetActionsAllowed;if(!x.exploreTargetTier)x.exploreTargetBattles=false;
    save({exploreCanonSettings:x});return x;
  }""",
)

rep(
"""  function exploreCache(){const pk=String(playerIdentity((hkStateStore.snapshot||playerDocument)?.player||{})||''),rootCache=load().exploreCanonProgressByPlayer;""",
"""  function exploreFingerprint(r){return [Number(r?.tier||0),Number(r?.level||0),Number(r?.next_tier_level||0),Number(r?.max_battle_level||0),r?.has_events===undefined?'':(r.has_events?1:0)].join('|');}
  function exploreCache(){const pk=String(playerIdentity((hkStateStore.snapshot||playerDocument)?.player||{})||''),rootCache=load().exploreCanonProgressByPlayer;""",
)

rep(
"""    if(!settings.exploreTargetTier||settings.targetTier>6)return {rows,checked:0,skipped:0,errors:0};const target=Number(settings.targetTier),cc=exploreCache(),out=[];let checked=0,skipped=0,errors=0;
    const total=rows.filter(r=>Number(r.tier)===target).length;
    for(const r of rows){if(Number(r.tier)!==target){out.push(r);continue;}const cached=cc.cache[r.id],needBattle=settings.exploreTargetBattles&&Number(r.battle_level||0)<Number(r.max_battle_level||0);
      if(cached&&Number(cached.tier)===target&&cached.finished===true&&!needBattle){skipped++;continue;}""",
"""    if(!settings.exploreTargetTier||settings.targetTier>6)return {rows,checked:0,skipped:0,errors:0};const target=Number(settings.targetTier),cc=exploreCache(),out=[];let checked=0,skipped=0,errors=0;
    let queue=rows;if(settings.level==='max')queue=rows.map((row,index)=>({row,index})).sort((a,b)=>{const at=Number(a.row?.tier)===target,bt=Number(b.row?.tier)===target;if(at!==bt)return at?-1:1;if(at&&bt){const ac=cc.cache[a.row.id],bc=cc.cache[b.row.id],ak=!!ac&&ac.fingerprint===exploreFingerprint(a.row),bk=!!bc&&bc.fingerprint===exploreFingerprint(b.row);if(ak!==bk)return ak?-1:1;if(ak&&bk){const d=Number(ac.remaining||0)-Number(bc.remaining||0);if(d)return d;}}return a.index-b.index;}).map(x=>x.row);queue=exploreStable(queue,r=>r.battle_level,settings.battleLevel);
    const total=queue.filter(r=>Number(r.tier)===target).length;
    for(const r of queue){if(Number(r.tier)!==target){out.push(r);continue;}const cached=cc.cache[r.id],cacheValid=!!cached&&Number(cached.tier)===target&&cached.fingerprint===exploreFingerprint(r),needBattle=settings.exploreTargetBattles&&Number(r.battle_level||0)<Number(r.max_battle_level||0);
      if(cacheValid&&cached.finished===true&&!needBattle){skipped++;continue;}""",
)

rep(
"""        cc.cache[r.id]={tier:target,total:p.total,completed:p.completed,remaining:p.remaining,finished:p.finished,checkedAt:Date.now()};""",
"""        cc.cache[r.id]={tier:target,fingerprint:exploreFingerprint({...r,...b}),total:p.total,completed:p.completed,remaining:p.remaining,finished:p.finished,checkedAt:Date.now()};""",
)

rep(
"""  async function exploreBuildPlan(){
    playerDocument=await hkAuthoritativePlayerRead('explore:plan');const settings=exploreSettings(),meta=await exploreLoadMeta(false),basic=exploreBasic(settings,playerDocument,meta),scan=await exploreScanTarget(basic.rows,settings);
    let candidates=scan.rows;if(settings.totalEvents!=='any'&&basic.totalEventsKnown){candidates=exploreStable(candidates,r=>r.next_tier_level,settings.nextTierLevel);candidates=exploreStable(candidates,r=>r.level,settings.level);
      candidates=exploreStable(candidates,r=>r.totalEvents,settings.totalEvents);candidates=exploreStable(candidates,r=>r.battle_level,settings.battleLevel);}
    const filtered=exploreFiltered(settings,playerDocument,meta),c=exploreConsigliere(playerDocument),level=Number(playerDocument?.player?.level||0);
    return {settings,meta,candidates,selected:candidates.slice(0,settings.maxBuildings),filteredCount:filtered.length,tierCounts:exploreCounts(filtered),consigliere:c,autoMaxTier:exploreAutoTier(c),playerLevel:level,tierModes:exploreTierModes(level),targetScan:scan,totalEventsKnown:basic.totalEventsKnown};
  }""",
"""  async function exploreBuildPlan(){
    playerDocument=await hkAuthoritativePlayerRead('explore:plan');const settings=exploreSettings(),meta=await exploreLoadMeta(false),basic=exploreBasic(settings,playerDocument,meta),scan=await exploreScanTarget(basic.rows,settings);
    let candidates=scan.rows;if(!settings.exploreTargetTier)candidates=candidates.slice(0,settings.maxBuildings);
    if(settings.totalEvents!=='any'&&basic.totalEventsKnown){candidates=exploreStable(candidates,r=>r.next_tier_level,settings.nextTierLevel);candidates=exploreStable(candidates,r=>r.level,settings.level);
      candidates=exploreStable(candidates,r=>r.totalEvents,settings.totalEvents);candidates=exploreStable(candidates,r=>r.battle_level,settings.battleLevel);}
    const filtered=exploreFiltered(settings,playerDocument,meta),c=exploreConsigliere(playerDocument),level=Number(playerDocument?.player?.level||0);
    return {settings,meta,candidates,selected:settings.exploreTargetTier?candidates.slice(0,settings.maxBuildings):candidates,filteredCount:filtered.length,tierCounts:exploreCounts(filtered),consigliere:c,autoMaxTier:exploreAutoTier(c),playerLevel:level,tierModes:exploreTierModes(level),targetScan:scan,totalEventsKnown:basic.totalEventsKnown};
  }""",
)

rep(
"""    const auto=p?.autoMaxTier??exploreAutoTier(c),level=p?.playerLevel??Number(st?.player?.level||0),modes=p?.tierModes||exploreTierModes(level),counts=p?.tierCounts||exploreCounts(active),targetOk=s.targetTier<=6;
    const tiers=EXPLORE_TIERS.map(t=>'<label><input type="checkbox" data-ex-tier="'+t.value+'" '+(s.startTiers.includes(t.value)?'checked':'')+'> '+t.label+' <small class="hk-muted">'+(counts[t.value]?.all||0)+' / '+(counts[t.value]?.battles||0)+'</small></label>').join('');
    const targets=EXPLORE_TIERS.map(t=>'<option value="'+t.value+'" '+(s.targetTier===t.value?'selected':'')+'>'+t.label+'</option>').join('')+'<option value="8" '+(s.targetTier===8?'selected':'')+'>'+either('Мгновенно MAX','Instant MAX')+'</option>';""",
"""    const auto=p?.autoMaxTier??exploreAutoTier(c),level=p?.playerLevel??Number(st?.player?.level||0),modes=p?.tierModes||exploreTierModes(level),counts=p?.tierCounts||exploreCounts(active),targetOk=s.targetTier>=1&&s.targetTier<=6;
    const maxStart=targetOk&&s.exploreTargetTier?s.targetTier:Math.min(s.targetTier,7)-1;
    const tiers=EXPLORE_TIERS.map(t=>'<label><input type="checkbox" data-ex-tier="'+t.value+'" '+(s.startTiers.includes(t.value)?'checked':'')+' '+(t.value>maxStart?'disabled':'')+'> '+t.label+' <small class="hk-muted">'+(counts[t.value]?.all||0)+' / '+(counts[t.value]?.battles||0)+'</small></label>').join('');
    const targets=EXPLORE_TIERS.filter(t=>t.value>=1).map(t=>'<option value="'+t.value+'" '+(s.targetTier===t.value?'selected':'')+'>'+t.label+'</option>').join('')+'<option value="8" '+(s.targetTier===8?'selected':'')+'>'+either('Мгновенно MAX','Instant MAX')+'</option>';""",
)

forbidden = [
    "/player/building/fast_completion",
    "/player/battle/fast",
    "/player/building/remort?",
    "/player/building/fast_remort",
    "/shop/buy",
]
assert not [x for x in forbidden if x in block]
assert "explore-readonly-plan-20260920-r2" in block
assert "EXPLORE_TIERS.filter(t=>t.value>=1)" in block
assert "fingerprint:exploreFingerprint" in block

p.write_text(s[:a] + block + s[b:])
