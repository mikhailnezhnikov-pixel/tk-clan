from pathlib import Path

p=Path("/tmp/HamsterKingMobile.user.js")
s=p.read_text()
MARKER="HK_PUBLIC_WAR_ALLIANCE_V3"

if MARKER in s:
    print("HK_PUBLIC_WAR_ALLIANCE_V3_ALREADY_PRESENT")
    raise SystemExit(0)

# ---- exact clan-war schema from Hamster King client 1.77.2.2017 ----
war_start=s.find("  function normalizePublicWar(documentValue) {")
war_end=s.find("\n\n  function leaderboardArrays",war_start)
if war_start < 0 or war_end < 0:
    raise SystemExit("normalizePublicWar anchor missing")

war_code=r'''  // HK_PUBLIC_WAR_ALLIANCE_V3
  function publicWarUnixFromTimer(value) {
    const timer=Number(value);
    if(!Number.isFinite(timer)||timer<=0)return 0;
    // Game client treats end_timer/attack_timer as milliseconds from now.
    return Math.floor((Date.now()+timer)/1000);
  }

  function normalizePublicWar(documentValue) {
    if(!documentValue||typeof documentValue!=='object')return null;
    const ownClan=firstText(
      playerDocument?.player?.clan?.name,
      playerDocument?.clan?.name,
      playerDocument?.player?.clan_name,
      'Top King'
    );

    const attack=documentValue.alliance_attack_war;
    if(attack&&typeof attack==='object'){
      const current=Number(attack.health);
      const maximum=Number(attack.initial_health);
      const result={
        our_clan:ownClan,
        opponent:firstText(attack.name,attack.defender_clan_name,'—'),
        our_score:0,
        opponent_score:0,
        status:'active',
        started_at:0,
        ends_at:publicWarUnixFromTimer(attack.end_timer),
        war_id:String(attack.id||''),
        war_type:'attack'
      };
      if(Number.isFinite(current)&&current>=0)result.opponent_hp=Math.round(current);
      if(Number.isFinite(maximum)&&maximum>0)result.opponent_hp_max=Math.round(maximum);
      return result;
    }

    const defenses=Array.isArray(documentValue.clan_defense_wars)
      ? documentValue.clan_defense_wars.filter(row=>row&&typeof row==='object')
      : [];
    if(defenses.length){
      defenses.sort((a,b)=>Number(a.end_timer||0)-Number(b.end_timer||0));
      const defense=defenses[0];
      const current=Number(defense.health);
      const maximum=Number(defense.initial_health);
      const result={
        our_clan:ownClan,
        opponent:firstText(defense.name,defense.attacker_alliance_name,'—'),
        our_score:0,
        opponent_score:0,
        status:'active',
        started_at:0,
        ends_at:publicWarUnixFromTimer(defense.end_timer),
        war_id:String(defense.id||''),
        war_type:'defense'
      };
      if(Number.isFinite(current)&&current>=0)result.our_hp=Math.round(current);
      if(Number.isFinite(maximum)&&maximum>0)result.our_hp_max=Math.round(maximum);
      return result;
    }
    return null;
  }
'''
s=s[:war_start]+war_code+s[war_end:]

# Replace readPublicWar: /clan/active_battles is the authoritative list.
read_war_start=s.find("  async function readPublicWar() {")
read_war_end=s.find("\n\n  function renderWars()",read_war_start)
if read_war_start < 0 or read_war_end < 0:
    raise SystemExit("readPublicWar anchor missing")
read_war=r'''  async function readPublicWar() {
    try{
      const value=await apiJson('/clan/active_battles','GET',null,true,1);
      return {read:true,war:normalizePublicWar(value)};
    }catch(_){
      return {read:false,war:null};
    }
  }'''
s=s[:read_war_start]+read_war+s[read_war_end:]

# ---- alliance V3: list -> /alliance/members for every alliance ----
read_rating_start=s.find("  async function readPublicRatings() {")
collect_start=s.find("\n\n  async function collectPublicSnapshot",read_rating_start)
if read_rating_start < 0 or collect_start < 0:
    raise SystemExit("readPublicRatings anchor missing")

alliance_code=r'''  function allianceV3ListRows(documentValue) {
    const list=Array.isArray(documentValue?.result)
      ? documentValue.result
      : Array.isArray(documentValue?.data?.result)
        ? documentValue.data.result
        : [];
    return list.map(row=>({
      id:String(row?.id||''),
      name:firstText(row?.name,row?.title),
      members:Number(row?.members_count||0),
      defense:Number(row?.defense_point||0)
    })).filter(row=>row.id&&row.name);
  }

  function allianceV3MemberClans(documentValue) {
    if(!documentValue||typeof documentValue!=='object')return [];
    const raw=[
      documentValue.core_clan,
      ...(Array.isArray(documentValue.satellite_clans)?documentValue.satellite_clans:[])
    ].filter(row=>row&&typeof row==='object');
    const seen=new Set();
    return raw.map(row=>{
      const name=firstText(row.name,row.clan_name,row.title);
      const key=allianceNameKey(name);
      return {
        id:String(row.id||row.clan_id||''),
        name,key?name:'',
        key,
        members:Number(row.number_of_members||row.members_count||0),
        defense:Number(row.defense_point||0)
      };
    }).filter(row=>row.id&&row.name&&!seen.has(row.key)&&(seen.add(row.key)||true));
  }

  async function allianceV3ReadMembers(alliances) {
    const results=new Map();
    let cursor=0;
    const workers=Array.from({length:Math.min(3,Math.max(1,alliances.length))},async()=>{
      while(cursor<alliances.length){
        const index=cursor++;
        const alliance=alliances[index];
        try{
          const value=await apiJson('/alliance/members?alliance_id='+encodeURIComponent(alliance.id),'GET',null,true,1);
          results.set(alliance.id,allianceV3MemberClans(value));
        }catch(_){}
      }
    });
    await Promise.all(workers);
    return results;
  }

  function allianceV3Rows(kind,alliances,membersByAlliance,metricMap) {
    const rows=[];
    for(const alliance of alliances){
      if(kind==='alliance_defense'){
        const value=Number(alliance.defense);
        if(Number.isFinite(value)&&value>0)rows.push({name:alliance.name,value});
        continue;
      }
      const clans=membersByAlliance.get(alliance.id)||[];
      if(!clans.length)continue;
      let total=0,covered=0;
      for(const clan of clans){
        const value=Number(metricMap.get(clan.key));
        if(!Number.isFinite(value)||value<0)continue;
        total+=value;covered+=1;
      }
      // Never understate an alliance with a partial clan set.
      if(covered===clans.length&&covered>0&&total>0)rows.push({name:alliance.name,value:total});
    }
    return rows.sort((a,b)=>b.value-a.value||a.name.localeCompare(b.name))
      .slice(0,100)
      .map((row,index)=>({rank:index+1,name:row.name,value:row.value}));
  }

  async function readPublicRatings() {
    const ratings={};
    let clanInfluenceRows=[];
    let clanPowerRows=[];

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

    try{clanPowerRows=await readClanPowerRows();}catch(_){}

    try{
      const allianceDocument=await apiJson('/alliance/list','GET',null,true,1);
      const alliances=allianceV3ListRows(allianceDocument);
      const membersByAlliance=await allianceV3ReadMembers(alliances);
      const influenceMap=clanRowsMap(clanInfluenceRows);
      const powerMap=clanRowsMap(clanPowerRows);

      const defenseRows=allianceV3Rows('alliance_defense',alliances,membersByAlliance,new Map());
      const influenceRows=allianceV3Rows('alliance_influence',alliances,membersByAlliance,influenceMap);
      const powerRows=allianceV3Rows('alliance_power',alliances,membersByAlliance,powerMap);

      if(defenseRows.length)ratings.alliance_defense=defenseRows;
      if(influenceRows.length)ratings.alliance_influence=influenceRows;
      if(powerRows.length)ratings.alliance_power=powerRows;

      try{
        recordDiagnostic('alliance-rating-v3',{
          alliances:alliances.length,
          detailed:[...membersByAlliance.values()].filter(rows=>rows.length).length,
          defense:defenseRows.length,
          influence:influenceRows.length,
          power:powerRows.length,
          powerLeaderboard:discoveredClanPowerLeaderboardType||''
        });
      }catch(_){}
    }catch(error){
      try{recordDiagnostic('alliance-rating-v3-error',{message:error?.message||String(error)});}catch(_){}
    }

    return ratings;
  }'''
s=s[:read_rating_start]+alliance_code+s[collect_start:]

p.write_text(s)
print("HK_PUBLIC_WAR_ALLIANCE_V3_PATCH_OK")
