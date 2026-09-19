from pathlib import Path

TARGET=Path('/tmp/HamsterKingMobile.user.js')
s=TARGET.read_text(encoding='utf-8')
REV='stage2h-wars-20260919-r1'

def require(needle,message):
    if needle not in s:
        raise SystemExit(message)

if '// @version      1.16.6' not in s and '// @version      1.16.7' not in s:
    raise SystemExit('Stage 2H requires live 1.16.6 or existing 1.16.7')
require("HK_STAGE2G_RUMORS_REV = 'stage2g-rumors-20260919-r1'",'Stage 2G missing')
require('function normalizePublicWar(', 'preserved war normalizer missing')
require('async function readPublicWar()', 'preserved war reader missing')

if f"HK_STAGE2H_WARS_REV = '{REV}'" not in s:
    s=s.replace('// @version      1.16.6','// @version      1.16.7',1)
    s=s.replace(": '1.16.6';",": '1.16.7';",1)
    marker="  const HK_STAGE2G_RUMORS_REV = 'stage2g-rumors-20260919-r1';"
    require(marker,'Stage 2G marker anchor missing')
    s=s.replace(marker,marker+f"\n  const HK_STAGE2H_WARS_REV = '{REV}';",1)
    runtime='  runtime.rumorsStage = HK_STAGE2G_RUMORS_REV;'
    require(runtime,'Stage 2G runtime anchor missing')
    s=s.replace(runtime,runtime+"\n  runtime.warsStage = HK_STAGE2H_WARS_REV;",1)

if 'let warSnapshot = null;' not in s:
    anchor='  async function readPublicWar() {'
    require(anchor,'readPublicWar anchor missing')
    state=r'''  let warSnapshot = null;
  let warLastReadAt = 0;

  function warTimestamp(value) {
    const number=Number(value||0);
    if(!Number.isFinite(number)||number<=0)return '';
    const ms=number<1e12?number*1000:number;
    try{return new Date(ms).toLocaleString(locale(),{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'});}catch(_){return '';}
  }

'''
    s=s.replace(anchor,state+anchor,1)

if 'function renderWars() {' not in s:
    anchor='  async function readPublicRatings() {'
    require(anchor,'readPublicRatings anchor missing')
    module=r'''  function renderWars() {
    const box=root?.querySelector('#hk-war-content');
    if(!box)return;
    const war=warSnapshot;
    if(!war){
      box.innerHTML='<div class="hk-clan-head"><div><h3>'+either('Войны','Wars')+'</h3><small>'+either('Данные читаются из активных войн клана','Data is read from active clan wars')+'</small></div><button id="hk-war-refresh" class="hk-secondary">'+either('Обновить','Refresh')+'</button></div><p class="hk-muted">'+either('Активная война не найдена.','No active war found.')+'</p>';
    }else{
      const ourScore=war.our_score==null?'—':Number(war.our_score).toLocaleString(locale());
      const enemyScore=war.opponent_score==null?'—':Number(war.opponent_score).toLocaleString(locale());
      const started=warTimestamp(war.started_at),ends=warTimestamp(war.ends_at);
      box.innerHTML='<div class="hk-clan-head"><div><h3>'+either('Войны','Wars')+'</h3><small>'+escapeHtml(String(war.status||either('активна','active')))+'</small></div><button id="hk-war-refresh" class="hk-secondary">'+either('Обновить','Refresh')+'</button></div>'+
        '<div class="hk-war-score"><div><small>'+either('Наш клан','Our clan')+'</small><b>'+escapeHtml(war.our_clan||'—')+'</b><strong>'+ourScore+'</strong></div><span>VS</span><div><small>'+either('Соперник','Opponent')+'</small><b>'+escapeHtml(war.opponent||'—')+'</b><strong>'+enemyScore+'</strong></div></div>'+
        '<p class="hk-muted">'+[started?either('Начало','Started')+': '+started:'',ends?either('Окончание','Ends')+': '+ends:'',warLastReadAt?either('Обновлено','Updated')+': '+new Date(warLastReadAt).toLocaleTimeString(locale(),{hour:'2-digit',minute:'2-digit'}):''].filter(Boolean).join(' · ')+'</p>';
    }
    box.querySelector('#hk-war-refresh')?.addEventListener('click',()=>void refreshWars(true));
  }

  async function refreshWars(force=false) {
    if(!requireLicense())return null;
    try{
      const result=await readPublicWar();
      warSnapshot=result?.war||null;
      warLastReadAt=Date.now();
      renderWars();
      if(force)log(warSnapshot?either('Данные войны обновлены','War data refreshed'):either('Активная война не найдена','No active war found'),warSnapshot?'ok':'warn');
      return warSnapshot;
    }catch(error){
      log(either('Ошибка чтения войны','War read error')+': '+(error?.message||error),'warn');
      renderWars();
      return null;
    }
  }

'''
    s=s.replace(anchor,module+anchor,1)

old_nav="{page:'clan',ru:'Навыки',en:'Skills'},{planned:true,ru:'Войны',en:'Wars'},{planned:true,ru:'Охота на крыс',en:'Rat Hunt'}"
new_nav="{page:'clan',ru:'Навыки',en:'Skills'},{page:'wars',ru:'Войны',en:'Wars'},{planned:true,ru:'Охота на крыс',en:'Rat Hunt'}"
if old_nav in s:
    s=s.replace(old_nav,new_nav,1)
elif new_nav not in s:
    raise SystemExit('Wars nav anchor missing')

war_page='''      <div class="hk-page" data-content="wars">
        <div id="hk-war-content" class="hk-cardbox"><h3>${either('Войны','Wars')}</h3><p class="hk-muted">${either('Откройте вкладку, чтобы считать текущую войну.','Open this tab to read the current war.')}</p></div>
      </div>
'''
if 'data-content="wars"' not in s:
    anchor='      <div class="hk-page" data-content="maps">'
    require(anchor,'Maps page anchor missing')
    s=s.replace(anchor,war_page+anchor,1)

if "if (key === 'wars')" not in s:
    anchor="        if (key === 'clan') {"
    require(anchor,'refreshModuleLive clan anchor missing')
    block="        if (key === 'wars') {const value=await refreshWars(false);liveReadOk=true;return value;}\n"
    s=s.replace(anchor,block+anchor,1)

if "if (finalPage === 'wars') renderWars();" not in s:
    anchor="      if (finalPage === 'clan') renderClanSkills();"
    require(anchor,'activateModule clan anchor missing')
    s=s.replace(anchor,anchor+"\n      if (finalPage === 'wars') renderWars();",1)

# Visual polish is intentionally non-blocking during mass migration.
checks=[
    ('// @version      1.16.7','Stage 2H version missing'),
    (f"HK_STAGE2H_WARS_REV = '{REV}'",'Stage 2H marker missing'),
    ("{page:'wars',ru:'Войны',en:'Wars'}",'Wars nav not enabled'),
    ('data-content="wars"','Wars page missing'),
    ('function renderWars()','Wars renderer missing'),
    ('async function refreshWars(','Wars refresh missing'),
    ("'/clan/active_battles'","active battles endpoint lost"),
    ("'/clan/active_defense_wars'","defense wars endpoint lost"),
    ("GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'",'Hamster Caps invariant lost'),
    ("GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'",'General Pit Token invariant lost'),
]
for needle,message in checks:
    require(needle,message)

TARGET.write_text(s,encoding='utf-8')
