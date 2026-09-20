from pathlib import Path
import re
p=Path('/tmp/HamsterKingMobile.user.js')
s=p.read_text('utf-8')
M="const HK_TODAY_CANON_REV = 'today-kokkaras-order-20260920-r1';"
if M in s: raise SystemExit('already applied')
for x in ["// @version      1.17.4","HK_STARTUP_ERROR_SCOPE_REV = 'startup-error-scope-20260920-r9'","function dailyActionRows()","function renderDailyTasks()"]:
    if x not in s: raise SystemExit('missing '+x)
s=s.replace("  // HK_TODAY_LIVE_VERIFY_V1 stage3a-today-live-20260920-r2\n","  "+M+"\n  // HK_TODAY_LIVE_VERIFY_V1 stage3a-today-live-20260920-r2\n",1)
s=s.replace("  let dailyShopRows = [];\n  let dailyRunning = false;","  let dailyShopRows = [];\n  let dailyClientConfigDocument = null;\n  let dailyRunning = false;",1)
s=s.replace("  let dailySelection = {...{advertisement:true, rumors:true, recruits:false, cartels:false, investments:false}, ...(load().today?.selection || {})};","  let dailySelection = {...{advertisement:true,rumors:true,dailyQuests:true,claimLeaderboardRewards:true,claimAreaBossBattlePass:true}, ...(load().today?.selection || {})};",1)

helpers='''
  const DAILY_CANON_CLAN_IDS=new Set(['mf_clan_shoplot_recruits_lvl_5','mf_clan_shoplot_hballs_lvl_5','mf_clan_shoplot_recruits_lvl_10','mf_clan_shoplot_hballs_lvl_10','mf_clan_shoplot_recruits_lvl_15','mf_clan_shoplot_hballs_lvl_15','mf_clan_shoplot_recruits_lvl_20','mf_clan_shoplot_hballs_lvl_20']);
  const DAILY_CANON_INVEST_IDS=new Set(['mf_shoplot_building_helpers_offer_01','mf_shoplot_building_helpers_offer_02']);
  const DAILY_CANON_EVENT_RE=/(?:_hballs|_hs_tokens|_crypto_hgen_fragments_5_4cur)$/i;
  const DAILY_CANON_LB_RE=/^(?:(?:clan_)?pit(?:_2|_3)?_daily_lb|(?:clan_)?area_boss_daily_lb|beast_boss_(?:cat|dog|pigeon)_monthly_lb|(?:clan_)?pit_gen_lb)$/;
  function dailyCanonInit(a){if(!a||Object.prototype.hasOwnProperty.call(dailySelection,a.id))return;let v=['advertisement','rumors','dailyQuests','claimLeaderboardRewards','claimAreaBossBattlePass'].includes(a.kind),id=String(a.row?.lotId||'');if(a.uiGroup==='clan')v=DAILY_CANON_CLAN_IDS.has(id);else if(a.uiGroup==='invest')v=DAILY_CANON_INVEST_IDS.has(id);else if(a.uiGroup==='event')v=DAILY_CANON_EVENT_RE.test(id);dailySelection[a.id]=v;}
  function dailyQuestRows(v,out=[],d=0){if(d>8||v==null)return out;if(Array.isArray(v)){for(const x of v)dailyQuestRows(x,out,d+1);return out}if(typeof v!=='object')return out;if(v.id)out.push(v);for(const x of Object.values(v))dailyQuestRows(x,out,d+1);return out}
  async function dailyClaimCompletedQuestsCurrent(){let n=0,b=new Set();for(let g=0;g<100;g++){await hkRunner.waitIfPaused();if(hkRunner.signal?.aborted)throw new DOMException('Aborted','AbortError');const q=dailyQuestRows(playerDocument?.quests||{}).find(x=>{const id=String(x?.id||'');return id.startsWith('qst_clan_daily_')&&!b.has(id)&&x?.completed!==true&&Number(x?.goal||0)>0&&Number(x?.progress||0)>=Number(x?.goal||0)});if(!q)break;try{const r=await apiJson('/quest/claim','POST',{quest_id:String(q.id)});playerDocument=hkStateStore.snapshot||r||playerDocument;n++;log(either('Получена награда ежедневного задания','Daily quest reward claimed')+': '+q.id,'ok')}catch(e){b.add(String(q.id));if(!/HTTP 409/.test(String(e?.message||e)))log(String(q.id)+' — '+(e?.message||e),'warn')}}return n}
  function dailyLbSort(x){const id=String(x?.id||'');if(/^(?:clan_)?pit_daily_lb$/.test(id))return id.startsWith('clan_')?1:0;if(/^(?:clan_)?pit_2_daily_lb$/.test(id))return 10+(id.startsWith('clan_')?1:0);if(/^(?:clan_)?pit_3_daily_lb$/.test(id))return 20+(id.startsWith('clan_')?1:0);if(/^(?:clan_)?area_boss_daily_lb$/.test(id))return 30+(id.startsWith('clan_')?1:0);if(id==='beast_boss_cat_monthly_lb')return 40;if(id==='beast_boss_dog_monthly_lb')return 41;if(id==='beast_boss_pigeon_monthly_lb')return 42;return 50}
  async function dailyClaimLeaderboardRewardsCurrent(){let n=0,v;try{v=await apiJson('/leaderboards/view','GET')}catch(e){log(e?.message||e,'warn');return 0}const a=Array.isArray(v)?v:(v?.leaderboards||v?.items||[]);for(const row of a.filter(x=>x&&DAILY_CANON_LB_RE.test(String(x.id||''))).sort((x,y)=>dailyLbSort(x)-dailyLbSort(y))){await hkRunner.waitIfPaused();let lb;try{lb=await apiJson('/leaderboard','POST',{leaderboard_type:String(row.id),leaderboard_status:'RELOAD'})}catch(e){continue}const slot=lb?.your_lb_slot;if(String(lb?.status||'').toUpperCase()!=='RELOAD'||!slot||slot.is_claimed!==false||!slot.reward_view)continue;try{const r=await apiJson('/leaderboard/reward','POST',{leaderboard_id:String(lb.id)});playerDocument=hkStateStore.snapshot||r||playerDocument;n++;log(either('Получена рейтинговая награда','Leaderboard reward claimed')+': '+row.id,'ok')}catch(e){if(!/HTTP 409/.test(String(e?.message||e)))log(e?.message||e,'warn')}}return n}
  function dailyBpNum(id){if(id==='bp_personal_area_boss')return 0;const m=String(id||'').match(/_([0-9]+)$/);return m?Number(m[1]):-1}
  function dailyBpIds(c){return [...new Set((((c?.points||{}).battle_pass_score)||[]).map(x=>x?.id).filter(id=>typeof id==='string'&&id.startsWith('bp_personal_area_boss')))].sort((a,b)=>dailyBpNum(b)-dailyBpNum(a))}
  async function dailyBpState(id,status){try{return await apiJson('/battlepass?battle_pass_type='+encodeURIComponent(id)+'&status='+encodeURIComponent(status),'GET')}catch(e){if(/HTTP (404|409)/.test(String(e?.message||e)))return null;throw e}}
  async function dailyClaimAreaBossBattlePassCurrent(){let n=0;try{const c=dailyClientConfigDocument||await apiJson('/client_config','GET');dailyClientConfigDocument=c;const ids=dailyBpIds(c);let cur=null;for(const id of ids){const d=await dailyBpState(id,'ACTUAL');const bp=d?.player_battle_pass;if(bp&&Number(bp.start_timer??1)<=0&&Number(bp.end_exp_timer??-1)>0){cur=bp;break}}if(!cur)return 0;const targets=[],i=ids.indexOf(String(cur.id));if(i>=0&&i+1<ids.length){const prev=(await dailyBpState(ids[i+1],'RELOAD'))?.player_battle_pass;if(prev&&Number(prev.end_reward_timer||0)>0)targets.push(prev)}targets.push(cur);for(const bp of targets){const count=Math.max(0,Number(bp?.rewards_may_claim||0));if(!bp?.id||Number(bp?.end_reward_timer||0)<=0||count<=0)continue;try{const r=await apiJson('/battlepass/claim','POST',{battle_pass_instance_id:String(bp.id)});playerDocument=hkStateStore.snapshot||r||playerDocument;n++;log(either('Получена награда Battle Pass боссов','Area Boss Battle Pass reward claimed')+': '+bp.id,'ok')}catch(e){if(!/HTTP 409/.test(String(e?.message||e)))log(e?.message||e,'warn')}}}catch(e){log(e?.message||e,'warn')}return n}
'''
pos=s.find('  function dailyActionRows() {')
s=s[:pos]+helpers+s[pos:]

A=s.find('  function dailyActionRows() {');B=s.find('  function saveDailySelection()',A)
new='''  function dailyActionRows() {
    const actions=[],ad=dailyAdvertisement();
    if(ad.available)actions.push({id:'advertisement',label:tr('dailyAds'),kind:'advertisement',uiGroup:'activities',free:true,available:true});
    if(dailyRumorRoute.length)actions.push({id:'rumors',label:either('Слухи','Rumors'),kind:'rumors',uiGroup:'activities',free:true,available:true});
    actions.push({id:'dailyQuests',label:either('Ежедневные задания (Ω)','Daily quests (Ω)'),kind:'dailyQuests',uiGroup:'activities',free:true,available:true});
    const rows=dailyShopRows.filter(x=>x?.safe),push=(row,ui)=>{const id='lot:'+row.lotId,a={id,label:(ui==='clan'?tr('clanShop'):ui==='invest'?tr('investShop'):either('Обычное предложение события','Event regular deal'))+': '+(gameText(row.name)||row.rewardId||row.lotId),kind:'purchase',uiGroup:ui,section:ui==='clan'?'clan':'shop',free:false,mandatory:false,available:row.remaining>0&&row.affordable,boughtOut:row.remaining<=0,row,count:0,cost:row.cost,signature:costSignature(row.cost)};dailyCanonInit(a);const saved=Math.max(0,Math.floor(Number(dailyPurchaseCounts[id]||0)));a.count=Math.min(Math.max(0,Number(row.remaining||0)),saved||(dailySelection[id]?1:0));actions.push(a)};
    rows.filter(x=>x.section==='clan'&&x.clanGroup==='personal'&&!excludedDailyClanLot(x)&&String(x.lotId||'')!=='mf_clan_shoplot_refill_lvl_15').forEach(x=>push(x,'clan'));
    rows.filter(x=>DAILY_CANON_INVEST_IDS.has(String(x.lotId||''))).forEach(x=>push(x,'invest'));
    rows.filter(x=>x.section==='regular').forEach(x=>push(x,'event'));
    actions.push({id:'claimLeaderboardRewards',label:either('Награды рейтинга: Ямы / Боссы / Крысы','Leaderboard rewards: Pits / Bosses / Rats'),kind:'claimLeaderboardRewards',uiGroup:'rewards',free:true,available:true});
    actions.push({id:'claimAreaBossBattlePass',label:either('Battle Pass боссов — получить награды','Area Boss Battle Pass — claim rewards'),kind:'claimAreaBossBattlePass',uiGroup:'rewards',free:true,available:true});
    actions.forEach(dailyCanonInit);return actions;
  }
  function selectedDailyActions(){return dailyActionRows().filter(a=>a.available&&dailySelection[a.id]===true&&(a.kind!=='purchase'||a.count>0));}

'''
s=s[:A]+new+s[B:]

# Render: drop route/ad/pit summary, switch store tabs to fixed canonical sections.
R=s.find('  function renderDailyTasks() {');E=s.find('  // HK_TODAY_LIVE_VERIFY_V1',R)
r=s[R:E]
r=re.sub(r"\n    const rumorsStored = .*?\n    const pit = pitState\(\);",'',r,flags=re.S)
r=re.sub(r"\n    const freeRows = .*?\n    const actionHtml = `\$\{freeHtml\}\$\{storeTabs\}\$\{paidHtml\}`;",'''\n    const canonicalGroups=[['activities',either('1. Действия','1. Activities')],['clan',either('2. Магазин клана','2. Clan shop')],['invest',either('3. Инвестиционные предложения','3. Invest deals')],['event',either('4. Обычные предложения события','4. Event regular deals')],['rewards',either('5. Получение наград','5. Claim rewards')]];\n    const actionHtml=canonicalGroups.map(([key,title])=>{const rows=actions.filter(a=>a.uiGroup===key);return rows.length?'<details class="hk-today-action-group" open><summary><b>'+escapeHtml(title)+'</b><span>'+rows.length+'</span></summary><div>'+rows.map(actionRowHtml).join('')+'</div></details>':''}).join('');''',r,flags=re.S)
r=re.sub(r"\n      <section class=\"hk-today-section\"><h4>\$\{either\('Слухи'.*?</section>\n      <div class=\"hk-today-grid\">.*?</div>\n      <section class=\"hk-today-section\"><h4>\$\{tr\('dailyStores'\)\}</h4><div class=\"hk-today-action-groups\">\$\{actionHtml\}</div></section>","\n      <section class=\"hk-today-section\"><h4>${either('Порядок действий','Action order')}</h4><div class=\"hk-today-action-groups\">${actionHtml}</div></section>",r,flags=re.S)
r=re.sub(r"\n    dailyBox.querySelectorAll\('\[data-pit-moves\]'\).*?\n    dailyBox.querySelectorAll\('\[data-daily-action\]'\)","\n    dailyBox.querySelectorAll('[data-daily-action]')",r,flags=re.S)
r=re.sub(r"\n    dailyBox.querySelectorAll\('\[data-daily-store-tab\]'\).*?\n    dailyBox.querySelectorAll\('\[data-budget-row\]'\)","\n    dailyBox.querySelectorAll('[data-budget-row]')",r,flags=re.S)
s=s[:R]+r+s[E:]

old="""      playerDocument = await apiJson('/player/me', 'POST');
      shopViewDocument = await apiJson('/shop/view', 'GET');
      dailyShopRows = shopViewDocument ? normalizeRegularShop() : [];
"""
new="""      playerDocument = await apiJson('/player/me', 'POST');
      shopViewDocument = await apiJson('/shop/view', 'GET');
      dailyClientConfigDocument = await apiJson('/client_config', 'GET').catch(()=>dailyClientConfigDocument);
      dailyShopRows = shopViewDocument ? normalizeRegularShop() : [];
"""
if old not in s:raise SystemExit('refresh anchor')
s=s.replace(old,new,1)
old="""          if (action.kind === 'rumors') await runDailyRumors(true);
          else if (action.kind === 'advertisement') await runDailyAd(true);
          else if (action.kind === 'pit') await executeDailyPit(action);
          else if (action.kind === 'purchase') await executeDailyPurchase(action);
"""
new="""          if (action.kind === 'advertisement') await runDailyAd(true);
          else if (action.kind === 'rumors') await runDailyRumors(true);
          else if (action.kind === 'dailyQuests') await dailyClaimCompletedQuestsCurrent();
          else if (action.kind === 'purchase') await executeDailyPurchase(action);
          else if (action.kind === 'claimLeaderboardRewards') await dailyClaimLeaderboardRewardsCurrent();
          else if (action.kind === 'claimAreaBossBattlePass') await dailyClaimAreaBossBattlePassCurrent();
"""
if old not in s:raise SystemExit('dispatch anchor')
s=s.replace(old,new,1)
for x in [M,'1. Действия','2. Магазин клана','3. Инвестиционные предложения','4. Обычные предложения события','5. Получение наград','dailyClaimCompletedQuestsCurrent','dailyClaimLeaderboardRewardsCurrent','dailyClaimAreaBossBattlePassCurrent']:
    if x not in s:raise SystemExit('missing '+x)
r=s[s.find('  function renderDailyTasks() {'):s.find('  // HK_TODAY_LIVE_VERIFY_V1')]
for x in ['routeHtml','pitLimitsHtml()','data-pit-moves','data-daily-store-tab']:
    if x in r:raise SystemExit('old UI '+x)
p.write_text(s,'utf-8')
print('TODAY_CANON_R1_PATCH_OK')
