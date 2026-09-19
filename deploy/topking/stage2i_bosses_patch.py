from pathlib import Path
p=Path('/tmp/HamsterKingMobile.user.js')
s=p.read_text(encoding='utf-8')
REV='stage2j-bosses-20260920-r1'
def req(x,m):
    if x not in s: raise SystemExit(m)
if '// @version      1.16.9' not in s and '// @version      1.16.9' not in s: raise SystemExit('Stage 2J requires 1.16.8 or 1.16.9')
req("HK_STAGE2I_BUILDINGS_REV = 'stage2i-buildings-explore-20260919-r1'",'Stage 2I Buildings missing')
if f"HK_STAGE2J_BOSSES_REV = '{REV}'" not in s:
    s=s.replace('// @version      1.16.9','// @version      1.16.9',1)
    s=s.replace(": '1.16.8';",": '1.16.9';",1)
    a="  const HK_STAGE2I_BUILDINGS_REV = 'stage2i-buildings-explore-20260919-r1';"; req(a,'marker')
    s=s.replace(a,a+f"\n  const HK_STAGE2J_BOSSES_REV = '{REV}';",1)
    a='  runtime.buildingsExploreStage = HK_STAGE2I_BUILDINGS_REV;'; req(a,'runtime')
    s=s.replace(a,a+"\n  runtime.bossesStage = HK_STAGE2J_BOSSES_REV;",1)
if 'let bossSnapshot = null;' not in s:
    a='  let warSnapshot = null;'; req(a,'war state')
    s=s.replace(a,"  let bossSnapshot = null;\n  let bossLastReadAt = 0;\n"+a,1)
if 'function bossStateRows(' not in s:
    a='  function renderWars() {'; req(a,'war renderer')
    mod=r'''  function bossStateRows(documentValue = bossSnapshot || hkStateStore.snapshot || playerDocument) {
    const rows=[]; const add=(kind,value)=>{if(value==null)return;if(Array.isArray(value))value.forEach((row,index)=>rows.push({kind,index,row}));else if(typeof value==='object')rows.push({kind,index:0,row:value});};
    add('player_bosses',documentValue?.player_bosses); add('player_regional_bosses',documentValue?.player_regional_bosses); add('boss_battle',documentValue?.boss_battle); return rows;
  }
  function bossRowLabel(v,i=0){return gameText(v?.name||v?.title||v?.boss?.name||v?.boss_name||v?.regional_boss_id||v?.boss_id||v?.id||(either('Босс ','Boss ')+(i+1)));}
  function bossRowSummary(v){const f=[[either('Уровень','Level'),v?.level??v?.boss_level??v?.tier],[either('Здоровье','Health'),v?.health??v?.hp??v?.current_health],[either('Макс. здоровье','Max health'),v?.max_health??v?.max_hp],[either('Урон','Damage'),v?.damage??v?.player_damage??v?.total_damage],[either('Попытки','Attempts'),v?.attempts??v?.tries??v?.battle_count],[either('Статус','Status'),v?.status??v?.state]].filter(([,x])=>x!==undefined&&x!==null&&String(x)!=='');return f.map(([k,x])=>'<span><small>'+escapeHtml(k)+'</small><b>'+escapeHtml(typeof x==='number'?Number(x).toLocaleString(locale()):String(x))+'</b></span>').join('');}
  function renderBosses(){
    const box=root?.querySelector('#hk-boss-content'); if(!box)return; const rows=bossStateRows(),profile=pitForecastProfile('boss');
    const body=rows.length?rows.map(({kind,index,row})=>'<article class="hk-boss-row"><div><b>'+escapeHtml(bossRowLabel(row,index))+'</b><small>'+escapeHtml(kind)+'</small></div><div class="hk-boss-stats">'+bossRowSummary(row)+'</div></article>').join(''):'<p class="hk-muted">'+either('Сейчас нет активных данных регионального босса.','There is no active regional boss data right now.')+'</p>';
    box.innerHTML='<div class="hk-clan-head"><div><h3>'+either('Боссы','Bosses')+'</h3><small>'+either('Игровое состояние боссов и Ямы боссов','Game boss state and Boss Pit data')+'</small></div><button id="hk-boss-refresh" class="hk-secondary">'+either('Обновить','Refresh')+'</button></div><div class="hk-boss-pit"><span><small>'+either('Яма боссов — уровень','Boss Pit level')+'</small><b>'+(Number(profile?.localLevel||0)||'—')+'</b></span><span><small>'+either('Сила','Power')+'</small><b>'+(Number(profile?.playerPower||0)?Number(profile.playerPower).toLocaleString(locale()):'—')+'</b></span></div>'+body+'<p class="hk-muted">'+(bossLastReadAt?either('Обновлено','Updated')+': '+new Date(bossLastReadAt).toLocaleTimeString(locale(),{hour:'2-digit',minute:'2-digit'}):either('Нажмите «Обновить».','Press Refresh.'))+'</p>';
    box.querySelector('#hk-boss-refresh')?.addEventListener('click',()=>void refreshBosses(true));
  }
  async function refreshBosses(force=false){
    if(!requireLicense())return null;
    try{playerDocument=await apiJson('/player/me','POST');bossSnapshot=hkStateStore.snapshot||playerDocument;bossLastReadAt=Date.now();renderBosses();if(force)log(either('Данные боссов обновлены','Boss data refreshed'),'ok');return bossSnapshot;}
    catch(error){log(either('Ошибка чтения боссов','Boss read error')+': '+(error?.message||error),'warn');renderBosses();return null;}
  }

'''
    s=s.replace(a,mod+a,1)
old="{page:'pit',ru:'Ямы',en:'Pits'},{planned:true,ru:'Боссы',en:'Bosses'},{planned:true,ru:'Районы',en:'Neighborhoods'}"
new="{page:'pit',ru:'Ямы',en:'Pits'},{page:'bosses',ru:'Боссы',en:'Bosses'},{planned:true,ru:'Районы',en:'Neighborhoods'}"
if old in s:s=s.replace(old,new,1)
elif new not in s:raise SystemExit('nav')
if 'data-content="bosses"' not in s:
    a='      <div class="hk-page" data-content="pit">';req(a,'pit page')
    page='''      <div class="hk-page" data-content="bosses"><div id="hk-boss-content" class="hk-cardbox"><h3>${either('Боссы','Bosses')}</h3><p class="hk-muted">${either('Откройте вкладку, чтобы считать состояние босса.','Open this tab to read boss state.')}</p></div></div>
'''
    s=s.replace(a,page+a,1)
if "if (key === 'bosses')" not in s:
    a="        if (key === 'wars') {";req(a,'wars live')
    s=s.replace(a,"        if (key === 'bosses') {const value=await refreshBosses(false);liveReadOk=true;return value;}\n"+a,1)
if "if (finalPage === 'bosses') renderBosses();" not in s:
    a="      if (finalPage === 'wars') renderWars();";req(a,'wars activate')
    s=s.replace(a,a+"\n      if (finalPage === 'bosses') renderBosses();",1)
for x in ['// @version      1.16.9',f"HK_STAGE2J_BOSSES_REV = '{REV}'","{page:'bosses',ru:'Боссы',en:'Bosses'}",'data-content="bosses"','function bossStateRows(','async function refreshBosses(',"documentValue?.player_bosses","documentValue?.player_regional_bosses","documentValue?.boss_battle","GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'","GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'"]:req(x,'Stage 2I missing '+x)
p.write_text(s,encoding='utf-8')
