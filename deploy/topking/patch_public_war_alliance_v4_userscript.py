from pathlib import Path
import re

p=Path("/tmp/HamsterKingMobile.user.js")
s=p.read_text()
MARKER="HK_PUBLIC_WAR_ALLIANCE_V4"

if MARKER in s:
    print("HK_PUBLIC_WAR_ALLIANCE_V4_ALREADY_PRESENT")
    raise SystemExit(0)

collect=s.find("  async function collectPublicSnapshot")
if collect < 0:
    raise SystemExit("collectPublicSnapshot anchor missing")

helpers=r'''  // HK_PUBLIC_WAR_ALLIANCE_V4
  // Exact schema verified against Hamster King client v1.77.2.2017.
  function hkV4Key(value){
    return String(value||'').normalize('NFKC').trim().replace(/\s+/g,' ').toLowerCase();
  }

  function hkV4Number(...values){
    for(const raw of values){
      if(raw===null||raw===undefined||raw==='')continue;
      const value=Number(raw);
      if(Number.isFinite(value)&&value>=0)return value;
    }
    return null;
  }

  function hkV4EndTimer(value){
    const timer=Number(value);
    return Number.isFinite(timer)&&timer>0 ? Math.floor((Date.now()+timer)/1000) : 0;
  }

  async function readPublicWarV4(){
    try{
      const value=await apiJson('/clan/active_battles','GET',null,true,1);
      const ownClan=firstText(
        playerDocument?.player?.clan?.name,
        playerDocument?.clan?.name,
        playerDocument?.player?.clan_name,
        'Top King'
      );
      const attack=value?.alliance_attack_war;
      if(attack&&typeof attack==='object'){
        const current=hkV4Number(attack.health);
        const maximum=hkV4Number(attack.initial_health);
        const war={
          our_clan:ownClan,
          opponent:firstText(attack.name,attack.defender_clan_name,'—'),
          our_score:0,opponent_score:0,status:'active',
          started_at:0,ends_at:hkV4EndTimer(attack.end_timer),
          war_id:String(attack.id||''),war_type:'attack'
        };
        if(current!==null)war.opponent_hp=Math.round(current);
        if(maximum!==null&&maximum>0)war.opponent_hp_max=Math.round(maximum);
        return {read:true,war};
      }
      const defenses=Array.isArray(value?.clan_defense_wars)
        ? value.clan_defense_wars.filter(row=>row&&typeof row==='object')
        : [];
      if(defenses.length){
        defenses.sort((a,b)=>Number(a.end_timer||0)-Number(b.end_timer||0));
        const defense=defenses[0];
        const current=hkV4Number(defense.health);
        const maximum=hkV4Number(defense.initial_health);
        const war={
          our_clan:ownClan,
          opponent:firstText(defense.name,defense.attacker_alliance_name,'—'),
          our_score:0,opponent_score:0,status:'active',
          started_at:0,ends_at:hkV4EndTimer(defense.end_timer),
          war_id:String(defense.id||''),war_type:'defense'
        };
        if(current!==null)war.our_hp=Math.round(current);
        if(maximum!==null&&maximum>0)war.our_hp_max=Math.round(maximum);
        return {read:true,war};
      }
      return {read:true,war:null};
    }catch(error){
      try{recordDiagnostic('public-war-v4-error',{message:error?.message||String(error)});}catch(_){}
      return {read:false,war:null};
    }
  }

  function hkV4AllianceList(value){
    const list=Array.isArray(value?.result)
      ? value.result
      : Array.isArray(value?.data?.result) ? value.data.result : [];
    return list.map(row=>({
      id:String(row?.id||''),
      name:firstText(row?.name,row?.title),
      defense:hkV4Number(row?.defense_point)??0,
      members:hkV4Number(row?.members_count)??0
    })).filter(row=>row.id&&row.name);
  }

  function hkV4AllianceClans(value){
    const raw=[
      value?.core_clan,
      ...(Array.isArray(value?.satellite_clans)?value.satellite_clans:[])
    ].filter(row=>row&&typeof row==='object');
    const result=[],seen=new Set();
    for(const row of raw){
      const name=firstText(row.name,row.clan_name,row.title);
      const key=hkV4Key(name);
      const id=String(row.id||row.clan_id||'');
      if(!name||!id||!key||seen.has(key))continue;
      seen.add(key);
      result.push({
        id,name,key,
        defense:hkV4Number(row.defense_point)??0,
        members:hkV4Number(row.number_of_members,row.members_count)??0
      });
    }
    return result;
  }

  async function hkV4AllianceMembers(alliances){
    const map=new Map();
    let cursor=0;
    const count=Math.min(2,Math.max(1,alliances.length));
    const workers=Array.from({length:count},async()=>{
      while(cursor<alliances.length){
        const alliance=alliances[cursor++];
        try{
          const value=await apiJson(
            '/alliance/members?alliance_id='+encodeURIComponent(alliance.id),
            'GET',null,true,1
          );
          const clans=hkV4AllianceClans(value);
          if(clans.length)map.set(alliance.id,clans);
        }catch(_){}
        await new Promise(resolve=>setTimeout(resolve,120));
      }
    });
    await Promise.all(workers);
    return map;
  }

  function hkV4MapRows(rows){
    return new Map((Array.isArray(rows)?rows:[])
      .filter(row=>row&&row.name&&Number.isFinite(Number(row.value)))
      .map(row=>[hkV4Key(row.name),Number(row.value)]));
  }

  async function hkV4ClanPowerRows(){
    for(const leaderboard_type of [
      'clan_hamsters_power_lb',
      'clan_hamster_power_lb',
      'clan_power_lb',
      'clans_hamsters_power_lb'
    ]){
      try{
        const value=await apiJson('/leaderboard','POST',{leaderboard_type},true,1);
        const rows=normalizePublicRanking(value,'clans');
        if(rows.length){
          try{recordDiagnostic('alliance-power-leaderboard-v4',{leaderboard_type,rows:rows.length});}catch(_){}
          return rows;
        }
      }catch(_){}
    }
    return [];
  }

  async function hkV4ClanPowerFromMembers(clan,cache){
    if(cache.has(clan.id))return cache.get(clan.id);
    let result=null;
    try{
      const value=await apiJson('/clan/members?clan_id='+encodeURIComponent(clan.id),'GET',null,true,1);
      const members=Array.isArray(value?.clan_members)
        ? value.clan_members
        : Array.isArray(value?.members) ? value.members : [];
      if(members.length){
        let sum=0,covered=0;
        for(const member of members){
          const power=hkV4Number(
            member?.hamsters_power,member?.power,
            member?.player?.hamsters_power,member?.player?.power
          );
          if(power===null)continue;
          sum+=power;covered+=1;
        }
        if(covered===members.length&&covered>0)result=sum;
      }
    }catch(_){}
    cache.set(clan.id,result);
    return result;
  }

  async function hkV4AllianceTotals(alliances,membersByAlliance,influenceMap,powerMap){
    const rows=[];
    const powerCache=new Map();
    for(const alliance of alliances){
      const clans=membersByAlliance.get(alliance.id)||[];
      if(!clans.length){
        if(alliance.defense>0)rows.push({
          name:alliance.name,defense:alliance.defense,influence:null,power:null
        });
        continue;
      }

      let influence=0,influenceCovered=0;
      let power=0,powerCovered=0;
      for(const clan of clans){
        const iv=hkV4Number(influenceMap.get(clan.key));
        if(iv!==null){influence+=iv;influenceCovered+=1}

        let pv=hkV4Number(powerMap.get(clan.key));
        if(pv===null)pv=await hkV4ClanPowerFromMembers(clan,powerCache);
        if(pv!==null){power+=pv;powerCovered+=1}
      }

      rows.push({
        name:alliance.name,
        defense:alliance.defense>0?alliance.defense:clans.reduce((sum,row)=>sum+Number(row.defense||0),0),
        influence:influenceCovered===clans.length&&clans.length?influence:null,
        power:powerCovered===clans.length&&clans.length?power:null
      });
      await new Promise(resolve=>setTimeout(resolve,80));
    }
    return rows;
  }

  function hkV4Rank(totals,key){
    return totals
      .filter(row=>Number.isFinite(row[key])&&row[key]>0)
      .sort((a,b)=>b[key]-a[key]||a.name.localeCompare(b.name))
      .slice(0,100)
      .map((row,index)=>({rank:index+1,name:row.name,value:row[key]}));
  }

  async function readPublicRatingsV4(){
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
      clanInfluenceRows=normalizePublicRanking(value,'clans');
      if(clanInfluenceRows.length)ratings.clans=clanInfluenceRows;
    }catch(_){}

    try{
      const allianceDocument=await apiJson('/alliance/list','GET',null,true,1);
      const alliances=hkV4AllianceList(allianceDocument);
      const [membersByAlliance,clanPowerRows]=await Promise.all([
        hkV4AllianceMembers(alliances),
        hkV4ClanPowerRows()
      ]);
      const totals=await hkV4AllianceTotals(
        alliances,
        membersByAlliance,
        hkV4MapRows(clanInfluenceRows),
        hkV4MapRows(clanPowerRows)
      );
      const defense=hkV4Rank(totals,'defense');
      const influence=hkV4Rank(totals,'influence');
      const power=hkV4Rank(totals,'power');
      if(defense.length)ratings.alliance_defense=defense;
      if(influence.length)ratings.alliance_influence=influence;
      if(power.length)ratings.alliance_power=power;
      try{
        recordDiagnostic('public-alliance-v4',{
          alliances:alliances.length,
          detailed:[...membersByAlliance.values()].filter(rows=>rows.length).length,
          defense:defense.length,influence:influence.length,power:power.length
        });
      }catch(_){}
    }catch(error){
      try{recordDiagnostic('public-alliance-v4-error',{message:error?.message||String(error)});}catch(_){}
    }
    return ratings;
  }

'''

s=s[:collect]+helpers+s[collect:]

old="const [warResult, ratings] = await Promise.all([readPublicWar(), readPublicRatings()]);"
if old not in s:
    match=re.search(r"const\s*\[\s*warResult\s*,\s*ratings\s*\]\s*=\s*await\s*Promise\.all\(\[\s*readPublicWar\(\)\s*,\s*readPublicRatings\(\)\s*\]\);",s)
    if not match:
        raise SystemExit("public snapshot Promise.all anchor missing")
    s=s[:match.start()]+"const [warResult, ratings] = await Promise.all([readPublicWarV4(), readPublicRatingsV4()]);"+s[match.end():]
else:
    s=s.replace(old,"const [warResult, ratings] = await Promise.all([readPublicWarV4(), readPublicRatingsV4()]);",1)

p.write_text(s)
print("HK_PUBLIC_WAR_ALLIANCE_V4_PATCH_OK")
