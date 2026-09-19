from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text()
MARKER="HK_ALLIANCE_RATINGS_V1"
if MARKER in s:
    print("HK_ALLIANCE_RATINGS_V1_ALREADY_PRESENT")
    raise SystemExit(0)

anchor="""  async function publicSnapshotServerJson(documentValue, retry = true) {
"""
if anchor not in s:
    raise SystemExit("public snapshot anchor missing")

helpers=r'''  // HK_ALLIANCE_RATINGS_V1
  const ALLIANCE_RATING_METRICS = {
    alliance_power:[
      'total_power','totalPower','overall_power','overallPower','alliance_power','alliancePower',
      'hamsters_power','hamstersPower','hamster_power','hamsterPower','members_power','membersPower',
      'players_power','playersPower','clans_power','clansPower','power'
    ],
    alliance_influence:[
      'total_influence','totalInfluence','alliance_influence','allianceInfluence',
      'members_influence','membersInfluence','players_influence','playersInfluence',
      'clans_influence','clansInfluence','influence','total_player_level','totalPlayerLevel',
      'player_level_sum','playerLevelSum','players_level','playersLevel','player_level','playerLevel'
    ],
    alliance_defense:[
      'total_defense','totalDefense','total_defence','totalDefence','alliance_defense','allianceDefense',
      'alliance_defence','allianceDefence','defense_points','defensePoints','defence_points','defencePoints',
      'total_defense_points','totalDefensePoints','total_defence_points','totalDefencePoints',
      'war_defense','warDefense','war_defence','warDefence','protection_points','protectionPoints',
      'total_protection','totalProtection','defense','defence','protection'
    ]
  };

  function finiteMetric(value) {
    const parsed=Number(value);
    return Number.isFinite(parsed)&&parsed>=0?parsed:null;
  }

  function metricFromObject(value, keys) {
    if(!value||typeof value!=='object')return null;
    for(const key of keys){
      if(!Object.prototype.hasOwnProperty.call(value,key))continue;
      const parsed=finiteMetric(value[key]);
      if(parsed!==null)return parsed;
    }
    return null;
  }

  function allianceChildren(row, entity) {
    const result=[];
    const seen=new Set();
    for(const source of [entity,row]){
      if(!source||typeof source!=='object')continue;
      for(const key of ['clans','alliance_clans','allianceClans','members','items','list','participants']){
        const list=source[key];
        if(!Array.isArray(list))continue;
        for(const child of list){
          if(!child||typeof child!=='object'||seen.has(child))continue;
          seen.add(child);result.push(child);
        }
      }
    }
    return result;
  }

  function allianceMetric(row, entity, kind) {
    const keys=ALLIANCE_RATING_METRICS[kind]||[];
    const direct=metricFromObject(entity,keys) ?? metricFromObject(row,keys);
    if(direct!==null)return direct;

    // Some game responses keep aggregate values on Clan objects inside the
    // Alliance. Sum only one child layer so a nested response is never counted twice.
    const children=allianceChildren(row,entity);
    if(!children.length)return null;
    let total=0,found=0;
    for(const child of children){
      const node=child.clan||child.member||child;
      const value=metricFromObject(node,keys) ?? metricFromObject(child,keys);
      if(value===null)continue;
      total+=value;found+=1;
    }
    return found?total:null;
  }

  function allianceCandidateScore(list) {
    if(!Array.isArray(list)||!list.length)return -1;
    let score=0;
    for(const row of list.slice(0,12)){
      if(!row||typeof row!=='object')continue;
      const entity=row.alliance||row;
      const keys=new Set([...Object.keys(row),...Object.keys(entity||{})].map(String));
      if(row.alliance||keys.has('alliance_id')||keys.has('allianceId')||keys.has('alliance_name')||keys.has('allianceName'))score+=5;
      if(keys.has('clans')||keys.has('alliance_clans')||keys.has('allianceClans')||keys.has('core_clan')||keys.has('coreClan'))score+=4;
      for(const metricKeys of Object.values(ALLIANCE_RATING_METRICS)){
        if(metricKeys.some(key=>keys.has(key))){score+=3;break;}
      }
      if(firstText(entity?.name,entity?.title,row.name,row.alliance_name,row.allianceName))score+=1;
    }
    return score;
  }

  function normalizeAllianceRatings(documentValue) {
    const arrays=leaderboardArrays(documentValue)
      .map(list=>({list,score:allianceCandidateScore(list)}))
      .filter(item=>item.score>0)
      .sort((a,b)=>b.score-a.score||b.list.length-a.list.length);

    for(const candidate of arrays){
      const normalized=[];
      const names=new Set();
      for(const row of candidate.list){
        if(!row||typeof row!=='object')continue;
        const entity=row.alliance||row;
        const name=firstText(
          entity?.name,entity?.title,entity?.alliance_name,entity?.allianceName,
          row.alliance_name,row.allianceName,row.name,row.title
        );
        if(!name||names.has(name))continue;
        const metrics={
          alliance_power:allianceMetric(row,entity,'alliance_power'),
          alliance_influence:allianceMetric(row,entity,'alliance_influence'),
          alliance_defense:allianceMetric(row,entity,'alliance_defense')
        };
        if(Object.values(metrics).every(value=>value===null))continue;
        names.add(name);
        normalized.push({name,...metrics});
      }
      if(normalized.length){
        const result={};
        for(const kind of Object.keys(ALLIANCE_RATING_METRICS)){
          const rows=normalized
            .filter(row=>Number.isFinite(row[kind])&&row[kind]>0)
            .sort((a,b)=>b[kind]-a[kind]||a.name.localeCompare(b.name))
            .slice(0,100)
            .map((row,index)=>({rank:index+1,name:row.name,value:row[kind]}));
          // Never publish a zero-only/unknown metric. This prevents a malformed
          // /alliance/list response from overwriting the last valid snapshot.
          if(rows.length)result[kind]=rows;
        }
        if(Object.keys(result).length)return result;
      }
    }

    try{
      const objects=deepObjects(documentValue).slice(0,40);
      const keys=[...new Set(objects.flatMap(value=>Object.keys(value||{})))].filter(key=>/alliance|power|influence|defen|protect|level/i.test(key)).slice(0,80);
      recordDiagnostic('alliance-rating-schema',{keys});
    }catch(_){}
    return {};
  }

'''
s=s.replace(anchor,helpers+anchor,1)

old="""  async function readPublicRatings() {
    const ratings = {}, definitions = {influence:'player_level_lb',power:'hamsters_power_lb',clans:'clan_player_level_lb'};
    for (const [kind, leaderboard_type] of Object.entries(definitions)) {
      try { const value = await apiJson('/leaderboard', 'POST', {leaderboard_type}, true, 1); const rows = normalizePublicRanking(value, kind); if (rows.length) ratings[kind] = rows; }
      catch (_) {}
    }
    try { const value = await apiJson('/alliance/list', 'GET', null, true, 1); const rows = normalizePublicRanking(value, 'alliances'); if (rows.length) ratings.alliances = rows; }
    catch (_) {}
    return ratings;
  }
"""
new="""  async function readPublicRatings() {
    const ratings = {}, definitions = {influence:'player_level_lb',power:'hamsters_power_lb',clans:'clan_player_level_lb'};
    for (const [kind, leaderboard_type] of Object.entries(definitions)) {
      try { const value = await apiJson('/leaderboard', 'POST', {leaderboard_type}, true, 1); const rows = normalizePublicRanking(value, kind); if (rows.length) ratings[kind] = rows; }
      catch (_) {}
    }
    try {
      const value = await apiJson('/alliance/list', 'GET', null, true, 1);
      Object.assign(ratings, normalizeAllianceRatings(value));
    } catch (_) {}
    return ratings;
  }
"""
if old not in s:
    raise SystemExit("readPublicRatings block missing")
s=s.replace(old,new,1)
path.write_text(s)
print("HK_ALLIANCE_RATINGS_V1_PATCH_OK")
