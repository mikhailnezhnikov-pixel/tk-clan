from pathlib import Path

TARGET=Path('/tmp/HamsterKingMobile.user.js')
s=TARGET.read_text(encoding='utf-8')
REV='stage2i-buildings-explore-20260919-r1'

def require(needle,message):
    if needle not in s:
        raise SystemExit(message)

if '// @version      1.16.7' not in s and '// @version      1.16.8' not in s:
    raise SystemExit('Stage 2I requires Stage 2H 1.16.7 or existing 1.16.8')
require("HK_STAGE2H_WARS_REV = 'stage2h-wars-20260919-r1'",'Stage 2H missing')
require('async function acceptBuildingStudy(', 'preserved building-study handler missing')
require('function buildingRooms(', 'building room reader missing')
require('async function submitOwnedMapAreas(', 'preserved Explore/map scan missing')
require("apiJson(\`/game_area/${areaId}\`, 'GET')", 'game area reader missing')
require("apiJson(\`/game_area/${areaId}/buildings\`, 'GET')", 'game area building reader missing')

if f"HK_STAGE2I_BUILDINGS_REV = '{REV}'" not in s:
    s=s.replace('// @version      1.16.7','// @version      1.16.8',1)
    s=s.replace(": '1.16.7';",": '1.16.8';",1)
    marker="  const HK_STAGE2H_WARS_REV = 'stage2h-wars-20260919-r1';"
    require(marker,'Stage 2H marker anchor missing')
    s=s.replace(marker,marker+f"\n  const HK_STAGE2I_BUILDINGS_REV = '{REV}';",1)
    runtime='  runtime.warsStage = HK_STAGE2H_WARS_REV;'
    require(runtime,'Stage 2H runtime anchor missing')
    s=s.replace(runtime,runtime+"\n  runtime.buildingsExploreStage = HK_STAGE2I_BUILDINGS_REV;",1)

# /player/building is the historical read/study endpoint. Keep it outside the
# mutation gate just like /player/me and lvlUp/view.
if "'/player/building'," not in s:
    anchor="    '/player/hamster/lvlUp/view',"
    require(anchor,'read-only POST list anchor missing')
    s=s.replace(anchor,anchor+"\n    '/player/building',",1)

if 'const buildingStudyCache = new Map();' not in s:
    anchor='  function buildingRooms(documentValue) {'
    require(anchor,'buildingRooms anchor missing')
    s=s.replace(anchor,"  const buildingStudyCache = new Map();\n\n"+anchor,1)

if 'function accountBuildingRows() {' not in s:
    anchor='  async function acceptBuildingStudy('
    require(anchor,'acceptBuildingStudy anchor missing')
    helpers=r'''  function accountBuildingRows() {
    const state=hkStateStore.snapshot||playerDocument||{};
    const rows=Array.isArray(state?.buildings)?state.buildings:(Array.isArray(state?.player?.buildings)?state.player.buildings:[]);
    return rows.filter(row=>row&&String(row?.id||row?.building_id||'')).map(row=>{
      const id=String(row?.id||row?.building_id||'');
      const cached=buildingStudyCache.get(id);
      const documentValue=cached||row;
      const rooms=buildingRooms(documentValue);
      const crystals=crystalRoomCount(documentValue);
      return {
        id,
        tier:Number(row?.chosen_tier??row?.tier??cached?.building?.chosen_tier??cached?.building?.tier??0),
        level:Number(row?.level??cached?.building?.level??0),
        hasEvents:row?.has_events??cached?.building?.has_events??rooms.length>0,
        roomCount:rooms.length,
        crystalRooms:crystals,
        raw:row
      };
    }).sort((a,b)=>b.tier-a.tier||b.level-a.level||a.id.localeCompare(b.id));
  }

  function renderBuildings() {
    const box=root?.querySelector('#hk-buildings-content');
    if(!box)return;
    const rows=accountBuildingRows();
    const content=rows.length?rows.map(row=>{
      const crystal=row.crystalRooms==null?'?':Number(row.crystalRooms).toLocaleString(locale());
      return '<div class="hk-card"><div class="hk-business-info"><b class="hk-business-name">'+escapeHtml(row.id)+'</b><small>'+
        either('Тир','Tier')+' '+Number(row.tier)+' · '+either('уровень','level')+' '+Number(row.level)+' · '+either('комнат','rooms')+' '+Number(row.roomCount)+' · 💎 '+crystal+
        '</small></div><button class="hk-secondary" data-building-read="'+escapeHtml(row.id)+'">'+either('Считать','Read')+'</button></div>';
    }).join(''):'<p class="hk-muted">'+either('Здания аккаунта пока не считаны.','Account buildings have not been read yet.')+'</p>';
    box.innerHTML='<div class="hk-clan-head"><div><h3>'+either('Здания','Buildings')+'</h3><small>'+either('Используется игровой /player/building из старого скрипта','Uses the historical in-game /player/building reader')+'</small></div><button id="hk-buildings-refresh" class="hk-secondary">'+either('Обновить','Refresh')+'</button></div><div class="hk-cards">'+content+'</div>';
    box.querySelector('#hk-buildings-refresh')?.addEventListener('click',()=>void refreshBuildings(true));
    box.querySelectorAll('[data-building-read]').forEach(button=>button.addEventListener('click',()=>void readBuildingStudy(button.dataset.buildingRead)));
  }

  async function refreshBuildings(force=false) {
    if(!requireLicense())return null;
    try{
      playerDocument=await apiJson('/player/me','POST');
      if(!eventCatalogDocument)eventCatalogDocument=normalizeEventCatalog(await apiJson('/events','GET'));
      renderBuildings();
      if(force)log(either('Список зданий обновлён','Building list refreshed'),'ok');
      return playerDocument;
    }catch(error){
      log(either('Ошибка чтения зданий','Building read error')+': '+(error?.message||error),'warn');
      renderBuildings();
      return null;
    }
  }

  async function readBuildingStudy(buildingId) {
    const id=String(buildingId||'');
    if(!id||!requireLicense())return null;
    if(hkRunner.running){alert(either('Сначала завершите текущую задачу','Finish the current task first'));return null;}
    hkRunner.start({title:either('Здание','Building'),total:1,step:id,pausable:false,stoppable:true});
    try{
      const path='/player/building?building_id='+encodeURIComponent(id);
      const value=await apiJson(path,'POST');
      buildingStudyCache.set(id,value);
      await acceptBuildingStudy((apiBase||GAME_API_FALLBACK)+path,apiHeaders,value);
      hkRunner.finish(either('Здание считано','Building read'));
      renderBuildings();
      return value;
    }catch(error){
      if(error?.name==='AbortError'){hkRunner.reset();log(either('Чтение здания остановлено','Building read stopped'),'warn');}
      else{hkRunner.fail(error);log(either('Ошибка здания','Building error')+': '+(error?.message||error),'bad');}
      return null;
    }
  }

  function exploreOwnedAreas() {
    const state=hkStateStore.snapshot||playerDocument||{};
    return Array.isArray(state?.areas?.areas)?state.areas.areas.filter(row=>row?.gamearea_id||row?.area_id):[];
  }

  function exploreMappedIds() {
    const ids=new Set();
    for(const row of mapRows||[]){
      if(row?.area_id)ids.add(String(row.area_id));
      for(const alias of (Array.isArray(row?.aliases)?row.aliases:[]))ids.add(String(alias));
    }
    return ids;
  }

  function renderExplore() {
    const box=root?.querySelector('#hk-explore-content');
    if(!box)return;
    const owned=exploreOwnedAreas(),mapped=exploreMappedIds();
    const known=owned.filter(row=>mapped.has(String(row?.gamearea_id||row?.area_id||''))).length;
    const rows=owned.slice(0,80).map(row=>{
      const id=String(row?.gamearea_id||row?.area_id||'');
      const city=String(row?.city_id||'');
      return '<div class="hk-card"><div class="hk-business-info"><b>'+escapeHtml(id)+'</b><small>'+escapeHtml(city||either('район','district'))+'</small></div><strong>'+(mapped.has(id)?'✓':'—')+'</strong></div>';
    }).join('');
    box.innerHTML='<div class="hk-clan-head"><div><h3>'+either('Исследование','Explore')+'</h3><small>'+either('Районов аккаунта','Account districts')+': '+owned.length+' · '+either('есть в общей карте','in map index')+': '+known+'</small></div></div>'+
      '<p class="hk-muted">'+either('Используется существующее исследование районов: /cities → /game_area/* → /game_area/*/buildings.','Uses the existing district research flow: /cities → /game_area/* → /game_area/*/buildings.')+'</p>'+
      '<div class="hk-toolbar"><button id="hk-explore-scan" class="hk-primary">'+either('Исследовать все районы','Research all districts')+'</button><button id="hk-explore-refresh" class="hk-secondary">'+either('Обновить','Refresh')+'</button><button id="hk-explore-maps" class="hk-secondary">'+either('Открыть карты','Open maps')+'</button></div>'+
      '<div class="hk-cards">'+(rows||'<p class="hk-muted">'+either('Районы не найдены','No districts found')+'</p>')+'</div>';
    box.querySelector('#hk-explore-scan')?.addEventListener('click',async()=>{await submitOwnedMapAreas(true);renderExplore();});
    box.querySelector('#hk-explore-refresh')?.addEventListener('click',()=>void refreshExplore(true));
    box.querySelector('#hk-explore-maps')?.addEventListener('click',()=>runtime.navigate?.('maps'));
  }

  async function refreshExplore(force=false) {
    if(!requireLicense())return null;
    try{
      playerDocument=await apiJson('/player/me','POST');
      await loadMapIndex(false);
      renderExplore();
      if(force)log(either('Исследование районов обновлено','District research refreshed'),'ok');
      return playerDocument;
    }catch(error){
      log(either('Ошибка исследования районов','District research error')+': '+(error?.message||error),'warn');
      renderExplore();
      return null;
    }
  }

'''
    s=s.replace(anchor,helpers+anchor,1)

old_nav="{page:'maps',ru:'Карты',en:'Maps'},{page:'resources',ru:'Ресурсы',en:'Resources'},{planned:true,ru:'Здания',en:'Buildings'},{planned:true,ru:'Исследование',en:'Explore'}"
new_nav="{page:'maps',ru:'Карты',en:'Maps'},{page:'resources',ru:'Ресурсы',en:'Resources'},{page:'buildings',ru:'Здания',en:'Buildings'},{page:'explore',ru:'Исследование',en:'Explore'}"
if old_nav in s:
    s=s.replace(old_nav,new_nav,1)
elif new_nav not in s:
    raise SystemExit('Buildings/Explore nav anchor missing')

pages='''      <div class="hk-page" data-content="buildings">
        <div id="hk-buildings-content" class="hk-cardbox"><h3>${either('Здания','Buildings')}</h3></div>
      </div>
      <div class="hk-page" data-content="explore">
        <div id="hk-explore-content" class="hk-cardbox"><h3>${either('Исследование','Explore')}</h3></div>
      </div>
'''
if 'data-content="buildings"' not in s:
    anchor='      <div class="hk-page" data-content="maps">'
    require(anchor,'Maps page anchor missing')
    s=s.replace(anchor,pages+anchor,1)

if "if (key === 'buildings')" not in s:
    anchor="        if (key === 'maps') {"
    require(anchor,'refresh maps anchor missing')
    block="        if (key === 'buildings') {const value=await refreshBuildings(false);liveReadOk=true;return value;}\n        if (key === 'explore') {const value=await refreshExplore(false);liveReadOk=true;return value;}\n"
    s=s.replace(anchor,block+anchor,1)

if "if (finalPage === 'buildings') renderBuildings();" not in s:
    anchor="      if (finalPage === 'resources') renderResources();"
    require(anchor,'activate resources anchor missing')
    s=s.replace(anchor,anchor+"\n      if (finalPage === 'buildings') renderBuildings();\n      if (finalPage === 'explore') renderExplore();",1)

checks=[
    ('// @version      1.16.8','Stage 2I version missing'),
    (f"HK_STAGE2I_BUILDINGS_REV = '{REV}'",'Stage 2I marker missing'),
    ("'/player/building',",'building reader not classified read-only'),
    ("{page:'buildings',ru:'Здания',en:'Buildings'}",'Buildings nav missing'),
    ("{page:'explore',ru:'Исследование',en:'Explore'}",'Explore nav missing'),
    ('data-content="buildings"','Buildings page missing'),
    ('data-content="explore"','Explore page missing'),
    ('async function readBuildingStudy(','generic building read missing'),
    ("const path='/player/building?building_id='",'player/building endpoint missing'),
    ('async function refreshExplore(','Explore refresh missing'),
    ('await submitOwnedMapAreas(true);','existing map research not wired'),
    ("GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'",'Hamster Caps invariant lost'),
    ("GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'",'General Pit Token invariant lost'),
]
for needle,message in checks:
    require(needle,message)

TARGET.write_text(s,encoding='utf-8')
