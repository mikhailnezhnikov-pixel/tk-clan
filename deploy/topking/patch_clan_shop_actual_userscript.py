# Deploy trigger: actual Clan Shop telemetry v1
# TopKing 1.17.2 deploy retry after service diagnostics hardening
from pathlib import Path
import re
import runpy
from patch_today_live_1170 import apply_today_hotfix
from patch_native_login_gate_1170 import apply_login_gate
from patch_bureau_resources_live_1171 import apply_hotfix as apply_bureau_resources_hotfix
from patch_bosses_readonly_1172 import apply_hotfix as apply_bosses_hotfix
from patch_regular_fair_1173 import apply_hotfix as apply_regular_fair_hotfix
from patch_auto_routines_1174 import apply_hotfix as apply_auto_routines_hotfix

p=Path("/tmp/HamsterKingMobile.user.js")
s=p.read_text()
MARKER="HK_CLAN_SHOP_ACTUAL_FACTS_V1"

def apply_alliance_v2_file_patch():
    runpy.run_path(str(Path(__file__).with_name("patch_alliance_ratings_v2_userscript.py")), run_name="__main__")


def apply_public_war_alliance_v3_file_patch():
    runpy.run_path(str(Path(__file__).with_name("patch_public_war_alliance_v3_userscript.py")), run_name="__main__")


def apply_alliance_ratings_patch(text):
    marker="HK_ALLIANCE_RATINGS_V1"
    interval="    setInterval(() => collectPublicSnapshot(), PUBLIC_SNAPSHOT_INTERVAL_MS);"
    immediate="    setTimeout(() => collectPublicSnapshot(true), 5000);\n" + interval
    if marker in text:
        if "setTimeout(() => collectPublicSnapshot(true), 5000);" not in text and interval in text:
            text=text.replace(interval,immediate,1)
        return text
    anchor="""  async function publicSnapshotServerJson(documentValue, retry = true) {
"""
    if anchor not in text:
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
    const result=[],seen=new Set();
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
      const normalized=[],names=new Set();
      for(const row of candidate.list){
        if(!row||typeof row!=='object')continue;
        const entity=row.alliance||row;
        const name=firstText(entity?.name,entity?.title,entity?.alliance_name,entity?.allianceName,row.alliance_name,row.allianceName,row.name,row.title);
        if(!name||names.has(name))continue;
        const metrics={
          alliance_power:allianceMetric(row,entity,'alliance_power'),
          alliance_influence:allianceMetric(row,entity,'alliance_influence'),
          alliance_defense:allianceMetric(row,entity,'alliance_defense')
        };
        if(Object.values(metrics).every(value=>value===null))continue;
        names.add(name);normalized.push({name,...metrics});
      }
      if(normalized.length){
        const result={};
        for(const kind of Object.keys(ALLIANCE_RATING_METRICS)){
          const rows=normalized.filter(row=>Number.isFinite(row[kind])&&row[kind]>0)
            .sort((a,b)=>b[kind]-a[kind]||a.name.localeCompare(b.name)).slice(0,100)
            .map((row,index)=>({rank:index+1,name:row.name,value:row[kind]}));
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
    text=text.replace(anchor,helpers+anchor,1)
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
    if old not in text:
        raise SystemExit("readPublicRatings block missing")
    text=text.replace(old,new,1)
    if "setTimeout(() => collectPublicSnapshot(true), 5000);" not in text and interval in text:
        text=text.replace(interval,immediate,1)
    return text


def apply_clan_war_hp_patch(text):
    marker="HK_CLAN_WAR_HP_V1"
    if marker in text:
        return text
    old=r'''  function normalizePublicWar(documentValue) {
    for (const row of deepObjects(documentValue)) {
      const ourNode = row.our_clan || row.player_clan || row.my_clan || row.attacker_clan || row.clan;
      const enemyNode = row.opponent_clan || row.enemy_clan || row.rival_clan || row.defender_clan || row.opponent || row.enemy;
      const ourClan = firstText(ourNode?.name, ourNode?.title, row.our_clan_name, row.player_clan_name, row.attacker_name);
      const opponent = firstText(enemyNode?.name, enemyNode?.title, row.opponent_name, row.enemy_name, row.defender_name);
      if (!ourClan || !opponent) continue;
      return {
        our_clan:ourClan, opponent,
        our_score:firstFinite(row.our_score, row.player_score, row.attacker_score, ourNode?.score, ourNode?.points),
        opponent_score:firstFinite(row.opponent_score, row.enemy_score, row.defender_score, enemyNode?.score, enemyNode?.points),
        status:firstText(row.status, row.state) || 'active',
        started_at:firstFinite(row.started_at, row.start_at, row.start_time, row.started),
        ends_at:firstFinite(row.ends_at, row.end_at, row.finish_time, row.finished_at),
      };
    }
    return null;
  }
'''
    new=r'''  // HK_CLAN_WAR_HP_V1
  function publicWarNumber(...values) {
    for (const value of values) {
      if (value === null || value === undefined || value === '') continue;
      const parsed=Number(value);
      if (Number.isFinite(parsed) && parsed >= 0) return parsed;
    }
    return null;
  }

  function publicWarHp(node, row, side) {
    const currentKeys=['hp','current_hp','currentHp','health','current_health','currentHealth','remaining_hp','remainingHp','remaining_health','remainingHealth','hit_points','hitPoints','current_hit_points','currentHitPoints'];
    const maxKeys=['max_hp','maxHp','total_hp','totalHp','hp_max','hpMax','max_health','maxHealth','total_health','totalHealth','health_max','healthMax','max_hit_points','maxHitPoints','total_hit_points','totalHitPoints'];
    const direct=(keys,source)=>{
      if(!source||typeof source!=='object')return null;
      for(const key of keys){
        if(!Object.prototype.hasOwnProperty.call(source,key))continue;
        const value=publicWarNumber(source[key]);
        if(value!==null)return value;
      }
      return null;
    };
    const prefixes=side==='our'
      ? ['our','player','attacker','my','clan']
      : ['opponent','enemy','defender','rival','target'];
    const directional=(suffixes)=>{
      for(const prefix of prefixes){
        for(const suffix of suffixes){
          const key=prefix+'_'+suffix;
          if(Object.prototype.hasOwnProperty.call(row,key)){
            const value=publicWarNumber(row[key]);
            if(value!==null)return value;
          }
          const camel=prefix+suffix.split('_').map(part=>part ? part[0].toUpperCase()+part.slice(1) : '').join('');
          if(Object.prototype.hasOwnProperty.call(row,camel)){
            const value=publicWarNumber(row[camel]);
            if(value!==null)return value;
          }
        }
      }
      return null;
    };
    return {
      current:direct(currentKeys,node) ?? directional(['hp','current_hp','health','current_health','remaining_hp','remaining_health','hit_points','current_hit_points']),
      max:direct(maxKeys,node) ?? directional(['max_hp','total_hp','hp_max','max_health','total_health','health_max','max_hit_points','total_hit_points'])
    };
  }

  function normalizePublicWar(documentValue) {
    for (const row of deepObjects(documentValue)) {
      const ourNode = row.our_clan || row.player_clan || row.my_clan || row.attacker_clan || row.clan;
      const enemyNode = row.opponent_clan || row.enemy_clan || row.rival_clan || row.defender_clan || row.opponent || row.enemy;
      const ourClan = firstText(ourNode?.name, ourNode?.title, row.our_clan_name, row.player_clan_name, row.attacker_name);
      const opponent = firstText(enemyNode?.name, enemyNode?.title, row.opponent_name, row.enemy_name, row.defender_name);
      if (!ourClan || !opponent) continue;
      const ourHp=publicWarHp(ourNode,row,'our');
      const opponentHp=publicWarHp(enemyNode,row,'opponent');
      const result={
        our_clan:ourClan, opponent,
        our_score:firstFinite(row.our_score, row.player_score, row.attacker_score, ourNode?.score, ourNode?.points),
        opponent_score:firstFinite(row.opponent_score, row.enemy_score, row.defender_score, enemyNode?.score, enemyNode?.points),
        status:firstText(row.status, row.state) || 'active',
        started_at:firstFinite(row.started_at, row.start_at, row.start_time, row.started),
        ends_at:firstFinite(row.ends_at, row.end_at, row.finish_time, row.finished_at),
      };
      if(ourHp.current!==null)result.our_hp=Math.round(ourHp.current);
      if(ourHp.max!==null)result.our_hp_max=Math.round(ourHp.max);
      if(opponentHp.current!==null)result.opponent_hp=Math.round(opponentHp.current);
      if(opponentHp.max!==null)result.opponent_hp_max=Math.round(opponentHp.max);
      if(!result.our_hp_max && !result.opponent_hp_max){
        try{
          const keys=[...new Set([row,ourNode,enemyNode].filter(Boolean).flatMap(value=>Object.keys(value||{})))].filter(key=>/hp|health|life|durab/i.test(key)).slice(0,60);
          if(keys.length)recordDiagnostic('clan-war-hp-schema',{keys});
        }catch(_){}
      }
      return result;
    }
    return null;
  }
'''
    if old not in text:
        raise SystemExit("normalizePublicWar block missing")
    return text.replace(old,new,1)

def sync_version(text):
    text, n_meta = re.subn(r"^// @version\s+\S+.*$", "// @version      1.17.0", text, count=1, flags=re.M)
    if n_meta != 1:
        raise SystemExit("userscript version metadata missing")
    text, n_fallback = re.subn(
        r"(const BUILD_VERSION = typeof GM_info.*?\n\s*: )'[^']+';",
        r"\1'1.17.0';",
        text,
        count=1,
        flags=re.S,
    )
    if n_fallback != 1:
        raise SystemExit("BUILD_VERSION fallback missing")
    return text

s = sync_version(s)
if MARKER in s:
    s = apply_alliance_ratings_patch(s)
    s = apply_clan_war_hp_patch(s)
    s = apply_today_hotfix(s)
    if 'HK_NATIVE_LOGIN_GATE_V1 login-gate-20260920-r1' not in s:
        s = apply_login_gate(s)
    s = apply_bureau_resources_hotfix(s)
    s = apply_bosses_hotfix(s)
    s = apply_regular_fair_hotfix(s)
    s = apply_auto_routines_hotfix(s)
    p.write_text(s)
    apply_alliance_v2_file_patch()
    apply_public_war_alliance_v3_file_patch()
    print("CLAN_SHOP_USERSCRIPT_VERSION_SYNCED_TODAY_LOGIN_AND_1171")
    raise SystemExit(0)

anchor="  const CLAN_SKILLS_API_BASE = 'https://hk-license.89.125.1.71.sslip.io/api/v1/clan-skills';\n"
if anchor not in s:
    raise SystemExit("CLAN_SKILLS_API_BASE anchor missing")
s=s.replace(anchor,anchor+"  const CLAN_SHOP_FACT_API_BASE = 'https://hk-license.89.125.1.71.sslip.io/api/v1';\n",1)

old="""        bought, maximum:bought + remaining, remaining, unlimited, section, clanGroup,
        icon:mediaUrl(view.icon_card || view.icon || content.icon_card || content.icon, rewardId)}];"""
new="""        bought, maximum:bought + remaining, remaining, unlimited, section, clanGroup,
        sharedPurchased:sharedLimit ? Math.max(0, Number(sharedLimit.value || 0)) : 0,
        sharedMaximum:sharedLimit ? Math.max(0, Number(sharedLimit.limit || 0) + Number(sharedLimit.bonus || 0)) : 0,
        icon:mediaUrl(view.icon_card || view.icon || content.icon_card || content.icon, rewardId)}];"""
if old not in s:
    raise SystemExit("normalize row anchor missing")
s=s.replace(old,new,1)

anchor="  async function loadShop() {\n"
helper=r"""  // HK_CLAN_SHOP_ACTUAL_FACTS_V1
  function clanShopActualFactType(row) {
    if (row?.section !== 'clan' || row?.clanGroup !== 'shared') return '';
    const label = clean(String(gameText(row?.name || '') || '') + ' ' + String(row?.name || '') + ' ' + String(row?.rewardId || '') + ' ' + String(row?.lotId || '')).toLowerCase();
    if (/шар.{0,24}идол|идол.{0,24}шар|idol.{0,24}ball|ball.{0,24}idol|guru.{0,24}ball|ball.{0,24}guru/.test(label)) return 'idol_orbs';
    if (/s\s*\+.{0,24}бизнес|бизнес.{0,24}s\s*\+|s\s*\+.{0,24}business|business.{0,24}s\s*\+|splus.{0,24}business|business.{0,24}splus/.test(label)) return 'splus_businesses';
    return '';
  }

  async function reportClanShopActualFacts() {
    const rows = shopRows.flatMap(row => {
      const itemType = clanShopActualFactType(row);
      if (!itemType) return [];
      return [{
        lot_id:String(row.lotId || ''),
        item_type:itemType,
        lot_name:gameText(row.name || '') || String(row.name || ''),
        reward_id:String(row.rewardId || ''),
        shared_purchased:Math.max(0, Number(row.sharedPurchased || 0)),
        shared_maximum:Math.max(0, Number(row.sharedMaximum || 0)),
        player_purchased:Math.max(0, Number(row.bought || 0))
      }];
    });
    if (!rows.length || !licenseState.allowed) return;
    try {
      await licensedServerJson(CLAN_SHOP_FACT_API_BASE, '/clan-shop-facts/submit', {rows}, false, 'clan-shop-facts');
    } catch (error) {
      console.warn('[HK] Clan Shop actual facts sync failed', error);
    }
  }

"""
if anchor not in s:
    raise SystemExit("loadShop anchor missing")
s=s.replace(anchor,helper+anchor,1)

old="""      shopRows = normalizeRegularShop();
      selectedShopLots = new Set([...selectedShopLots].filter(id => shopRows.some(row => row.lotId === id && row.safe && row.remaining > 0)));"""
new="""      shopRows = normalizeRegularShop();
      void reportClanShopActualFacts();
      selectedShopLots = new Set([...selectedShopLots].filter(id => shopRows.some(row => row.lotId === id && row.safe && row.remaining > 0)));"""
if old not in s:
    raise SystemExit("loadShop normalize anchor missing")
s=s.replace(old,new,1)

old="""      await hkAuthoritativePlayerRead('shop-complete');
      shopRows = normalizeRegularShop();
      hkRunner.finish(either('Покупки завершены','Purchases completed'));"""
new="""      await hkAuthoritativePlayerRead('shop-complete');
      try { shopViewDocument = await apiJson('/shop/view', 'GET'); } catch (_) {}
      shopRows = normalizeRegularShop();
      void reportClanShopActualFacts();
      hkRunner.finish(either('Покупки завершены','Purchases completed'));"""
if old not in s:
    raise SystemExit("buy completion anchor missing")
s=s.replace(old,new,1)

s = apply_alliance_ratings_patch(s)
s = apply_clan_war_hp_patch(s)
s = apply_today_hotfix(s)
if 'HK_NATIVE_LOGIN_GATE_V1 login-gate-20260920-r1' not in s:
    s = apply_login_gate(s)
s = apply_bureau_resources_hotfix(s)
s = apply_bosses_hotfix(s)
s = apply_regular_fair_hotfix(s)
s = apply_auto_routines_hotfix(s)
p.write_text(s)
apply_alliance_v2_file_patch()
apply_public_war_alliance_v3_file_patch()
print("CLAN_SHOP_USERSCRIPT_PATCH_OK_WITH_LOGIN_GATE_AND_1171")
