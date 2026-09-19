from pathlib import Path

p=Path("/tmp/HamsterKingMobile.user.js")
s=p.read_text()
MARKER="HK_ALLIANCE_RATINGS_V2"

if MARKER in s:
    print("HK_ALLIANCE_RATINGS_V2_ALREADY_PRESENT")
    raise SystemExit(0)

read_start=s.find("  async function readPublicRatings() {")
collect_start=s.find("\n\n  async function collectPublicSnapshot", read_start)
if read_start < 0 or collect_start < 0:
    raise SystemExit("readPublicRatings anchor missing")

helpers=r'''  // HK_ALLIANCE_RATINGS_V2
  // Alliance totals are built from the clans that belong to each alliance.
  // Defense/defence ("Оборона" in the game) comes from the alliance/clan list;
  // clan power and influence are joined by clan name from the game's clan leaderboards.
  let discoveredClanPowerLeaderboardType = '';

  function allianceNameKey(value) {
    return String(value || '').normalize('NFKC').trim().replace(/\s+/g,' ').toLowerCase();
  }

  function allianceObjectName(value) {
    if(!value||typeof value!=='object')return '';
    const node=value.alliance||value.alliance_info||value.allianceInfo||value;
    return firstText(
      node?.name,node?.title,node?.alliance_name,node?.allianceName,
      value.alliance_name,value.allianceName,value.name,value.title
    );
  }

  function clanObjectName(value) {
    if(!value||typeof value!=='object')return '';
    const node=value.clan||value.clan_info||value.clanInfo||value;
    return firstText(
      node?.name,node?.title,node?.clan_name,node?.clanName,
      value.clan_name,value.clanName,value.name,value.title
    );
  }

  function clanObjectId(value) {
    if(!value||typeof value!=='object')return '';
    const node=value.clan||value.clan_info||value.clanInfo||value;
    return firstText(
      node?.clan_id,node?.clanId,node?.id,node?.uuid,
      value.clan_id,value.clanId,value.id,value.uuid
    );
  }

  function clanMemberCount(value) {
    if(!value||typeof value!=='object')return null;
    const node=value.clan||value.clan_info||value.clanInfo||value;
    return metricFromObject(node,[
      'members_count','membersCount','member_count','memberCount',
      'players_count','playersCount','participants_count','participantsCount',
      'members','participants'
    ]) ?? metricFromObject(value,[
      'members_count','membersCount','member_count','memberCount',
      'players_count','playersCount','participants_count','participantsCount'
    ]);
  }

  function directClanMetric(value,kind) {
    if(!value||typeof value!=='object')return null;
    const node=value.clan||value.clan_info||value.clanInfo||value;
    const keys=ALLIANCE_RATING_METRICS[kind]||[];
    return metricFromObject(node,keys) ?? metricFromObject(value,keys);
  }

  function likelyClanArray(list) {
    if(!Array.isArray(list)||!list.length||list.length>20)return false;
    let named=0,clanish=0;
    for(const item of list.slice(0,8)){
      if(!item||typeof item!=='object')continue;
      if(clanObjectName(item))named+=1;
      const keys=new Set([
        ...Object.keys(item),
        ...Object.keys(item.clan||item.clan_info||item.clanInfo||{})
      ].map(String));
      if(
        item.clan||item.clan_info||item.clanInfo||
        keys.has('clan_id')||keys.has('clanId')||
        keys.has('defense')||keys.has('defence')||
        keys.has('defense_points')||keys.has('defence_points')||
        keys.has('player_level')||keys.has('hamsters_power')||
        keys.has('members_count')||keys.has('membersCount')
      )clanish+=1;
    }
    return named>0 && (clanish>0 || named===list.length);
  }

  function allianceClanRows(value) {
    if(!value||typeof value!=='object')return [];
    const sources=[value.alliance||null,value.alliance_info||null,value.allianceInfo||null,value].filter(Boolean);
    const preferred=[
      'clans','alliance_clans','allianceClans','clan_list','clanList',
      'member_clans','memberClans','participants'
    ];
    for(const source of sources){
      for(const key of preferred){
        const list=source?.[key];
        if(likelyClanArray(list))return list;
      }
    }
    for(const source of sources){
      for(const child of Object.values(source||{})){
        if(likelyClanArray(child))return child;
      }
    }
    const singles=[];
    for(const source of sources){
      for(const key of ['core_clan','coreClan','leader_clan','leaderClan','clan']){
        const row=source?.[key];
        if(row&&typeof row==='object'&&clanObjectName(row))singles.push(row);
      }
    }
    return singles;
  }

  function allianceRecords(documentValue) {
    const output=[],seen=new Set();
    for(const value of deepObjects(documentValue)){
      if(!value||typeof value!=='object')continue;
      const name=allianceObjectName(value);
      const clans=allianceClanRows(value);
      if(!name||!clans.length)continue;
      const parsedClans=[];
      const clanSeen=new Set();
      for(const raw of clans){
        const clanName=clanObjectName(raw);
        if(!clanName)continue;
        const clanKey=allianceNameKey(clanName);
        if(!clanKey||clanSeen.has(clanKey))continue;
        clanSeen.add(clanKey);
        parsedClans.push({
          name:clanName,
          key:clanKey,
          id:clanObjectId(raw),
          members:clanMemberCount(raw),
          power:directClanMetric(raw,'alliance_power'),
          influence:directClanMetric(raw,'alliance_influence'),
          defense:directClanMetric(raw,'alliance_defense')
        });
      }
      if(!parsedClans.length)continue;
      const key=allianceNameKey(name);
      if(!key||seen.has(key))continue;
      seen.add(key);
      output.push({
        name,key,clans:parsedClans,
        power:metricFromObject(value.alliance||value,ALLIANCE_RATING_METRICS.alliance_power),
        influence:metricFromObject(value.alliance||value,ALLIANCE_RATING_METRICS.alliance_influence),
        defense:metricFromObject(value.alliance||value,ALLIANCE_RATING_METRICS.alliance_defense)
      });
    }
    return output;
  }

  function clanMetricRows(documentValue,kind) {
    const arrays=leaderboardArrays(documentValue);
    for(const list of arrays){
      const rows=list.map((row,index)=>{
        if(!row||typeof row!=='object')return null;
        const entity=row.clan||row.clan_info||row.clanInfo||row;
        const name=clanObjectName(row);
        if(!name)return null;
        const rank=Math.trunc(firstFinite(row.rank,row.place,row.position,entity.rank)||index+1);
        let value=null;
        if(kind==='power'){
          value=metricFromObject(entity,ALLIANCE_RATING_METRICS.alliance_power)
            ?? metricFromObject(row,ALLIANCE_RATING_METRICS.alliance_power)
            ?? finiteMetric(row.value) ?? finiteMetric(row.score);
        }else{
          value=metricFromObject(entity,ALLIANCE_RATING_METRICS.alliance_influence)
            ?? metricFromObject(row,ALLIANCE_RATING_METRICS.alliance_influence)
            ?? finiteMetric(row.value) ?? finiteMetric(row.score);
        }
        return rank>=1&&value!==null?{rank,name,value}:null;
      }).filter(Boolean);
      if(rows.length)return rows.slice(0,200);
    }
    return [];
  }

  function clanRowsMap(rows) {
    return new Map((Array.isArray(rows)?rows:[])
      .filter(row=>row&&row.name&&Number.isFinite(Number(row.value)))
      .map(row=>[allianceNameKey(row.name),Number(row.value)]));
  }

  async function readClanPowerRows() {
    const candidates=discoveredClanPowerLeaderboardType
      ? [discoveredClanPowerLeaderboardType]
      : ['clan_hamsters_power_lb','clan_hamster_power_lb','clan_power_lb','clans_hamsters_power_lb'];
    for(const leaderboard_type of candidates){
      try{
        const value=await apiJson('/leaderboard','POST',{leaderboard_type},true,1);
        const rows=clanMetricRows(value,'power');
        if(rows.length){
          discoveredClanPowerLeaderboardType=leaderboard_type;
          return rows;
        }
      }catch(_){}
    }
    return [];
  }

  function completeAllianceSum(alliance,metric,map) {
    const direct=finiteMetric(alliance?.[metric]);
    if(direct!==null&&direct>0)return direct;
    let total=0,covered=0;
    for(const clan of alliance.clans||[]){
      let value=finiteMetric(clan?.[metric]);
      if((value===null||value<=0)&&map)value=finiteMetric(map.get(clan.key));
      if(value===null||value<0)continue;
      total+=value;covered+=1;
    }
    // Never publish a partial total. A missing clan must not silently reduce
    // an alliance's power/influence/defense.
    return covered===(alliance.clans||[]).length&&covered>0?total:null;
  }

  function buildAllianceRatings(allianceDocument,clanInfluenceRows,clanPowerRows) {
    const alliances=allianceRecords(allianceDocument);
    const influenceMap=clanRowsMap(clanInfluenceRows);
    const powerMap=clanRowsMap(clanPowerRows);
    const totals=alliances.map(alliance=>({
      name:alliance.name,
      clans:alliance.clans.length,
      members:alliance.clans.reduce((sum,row)=>sum+(Number(row.members)||0),0),
      alliance_power:completeAllianceSum(alliance,'power',powerMap),
      alliance_influence:completeAllianceSum(alliance,'influence',influenceMap),
      alliance_defense:completeAllianceSum(alliance,'defense',null)
    }));
    const result={};
    for(const kind of ['alliance_power','alliance_influence','alliance_defense']){
      const rows=totals
        .filter(row=>Number.isFinite(row[kind])&&row[kind]>0)
        .sort((a,b)=>b[kind]-a[kind]||a.name.localeCompare(b.name))
        .slice(0,100)
        .map((row,index)=>({rank:index+1,name:row.name,value:row[kind]}));
      if(rows.length)result[kind]=rows;
    }
    try{
      recordDiagnostic('alliance-rating-v2',{
        alliances:alliances.length,
        power:result.alliance_power?.length||0,
        influence:result.alliance_influence?.length||0,
        defense:result.alliance_defense?.length||0,
        powerLeaderboard:discoveredClanPowerLeaderboardType||''
      });
    }catch(_){}
    return result;
  }

'''

new_read=r'''  async function readPublicRatings() {
    const ratings={};
    let clanInfluenceRows=[];

    try{
      const value=await apiJson('/leaderboard','POST',{leaderboard_type:'player_level_lb'},true,1);
      const rows=normalizePublicRanking(value,'influence');
      if(rows.length)ratings.influence=rows;
    }catch(_){}

    try{
      const value=await apiJson('/leaderboard','POST',{leaderboard_type:'hamsters_power_lb'},true,1);
      const rows=normalizePublicRanking(value,'power');
      if(rows.length)ratings.power=rows;
    }catch(_){}

    try{
      const value=await apiJson('/leaderboard','POST',{leaderboard_type:'clan_player_level_lb'},true,1);
      clanInfluenceRows=clanMetricRows(value,'influence');
      const publicRows=normalizePublicRanking(value,'clans');
      if(publicRows.length)ratings.clans=publicRows;
    }catch(_){}

    try{
      const [allianceDocument,clanPowerRows]=await Promise.all([
        apiJson('/alliance/list','GET',null,true,1),
        readClanPowerRows()
      ]);
      Object.assign(ratings,buildAllianceRatings(allianceDocument,clanInfluenceRows,clanPowerRows));
    }catch(error){
      try{recordDiagnostic('alliance-rating-v2-error',{message:error?.message||String(error)});}catch(_){}
    }
    return ratings;
  }'''

s=s[:read_start]+helpers+new_read+s[collect_start:]
p.write_text(s)
print("HK_ALLIANCE_RATINGS_V2_PATCH_OK")
