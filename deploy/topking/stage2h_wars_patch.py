from pathlib import Path

TARGET = Path('/tmp/HamsterKingMobile.user.js')
s = TARGET.read_text(encoding='utf-8')

REV = 'stage2h-wars-20260919-r1'

def require(needle, message):
    if needle not in s:
        raise SystemExit(message)

if '// @version      1.16.6' not in s and '// @version      1.16.7' not in s:
    raise SystemExit('Stage 2H requires live 1.16.6 or existing Stage 2H 1.16.7')
require("HK_STAGE2G_RUMORS_REV = 'stage2g-rumors-20260919-r1'", 'Stage 2G missing')
require('async function readPublicWar()', 'existing war collector missing')
require('async function refreshModuleLive(', 'module live refresh missing')

if f"HK_STAGE2H_WARS_REV = '{REV}'" not in s:
    s = s.replace('// @version      1.16.6', '// @version      1.16.7', 1)
    s = s.replace(": '1.16.6';", ": '1.16.7';", 1)

    marker = "  const HK_STAGE2G_RUMORS_REV = 'stage2g-rumors-20260919-r1';"
    require(marker, 'Stage 2G marker missing')
    s = s.replace(marker, marker + f"\n  const HK_STAGE2H_WARS_REV = '{REV}';", 1)

    runtime_marker = '  runtime.rumorsStage = HK_STAGE2G_RUMORS_REV;'
    require(runtime_marker, 'Stage 2G runtime marker missing')
    s = s.replace(runtime_marker, runtime_marker + "\n  runtime.warsStage = HK_STAGE2H_WARS_REV;", 1)

if 'let warSnapshot = null;' not in s:
    anchor = '  let publicSnapshotPromise = null;'
    require(anchor, 'public snapshot state anchor missing')
    s = s.replace(anchor, anchor + "\n  let warSnapshot = null;\n  let warLoading = false;", 1)

if '  function renderWars() {' not in s:
    anchor = '  async function loadFair() {'
    require(anchor, 'Fair loader anchor missing')
    module = r'''  function warTimeText(value) {
    const number = Number(value || 0);
    if (!number) return '—';
    const ms = number > 1e12 ? number : number * 1000;
    try { return new Date(ms).toLocaleString(locale()); } catch (_) { return '—'; }
  }

  function renderWars() {
    if (!warBox) return;
    if (warLoading) {
      warBox.innerHTML = '<h3>' + either('Войны клана','Clan Wars') + '</h3><p class="hk-muted">' + either('Считываю текущую войну…','Reading current war…') + '</p>';
      return;
    }
    if (!warSnapshot) {
      warBox.innerHTML = '<h3>' + either('Войны клана','Clan Wars') + '</h3><p class="hk-muted">' + either('Откройте вкладку или нажмите «Обновить».','Open the tab or press Refresh.') + '</p><button id="hk-war-refresh" class="hk-secondary">' + either('Обновить','Refresh') + '</button>';
      warBox.querySelector('#hk-war-refresh').onclick = () => refreshModuleLive('wars',{force:true});
      return;
    }
    if (!warSnapshot.read) {
      warBox.innerHTML = '<h3>' + either('Войны клана','Clan Wars') + '</h3><p class="hk-muted">' + either('Игра не вернула данные войны.','The game did not return war data.') + '</p><button id="hk-war-refresh" class="hk-secondary">' + either('Повторить','Retry') + '</button>';
      warBox.querySelector('#hk-war-refresh').onclick = () => refreshModuleLive('wars',{force:true});
      return;
    }
    const war = warSnapshot.war;
    if (!war) {
      warBox.innerHTML = '<h3>' + either('Войны клана','Clan Wars') + '</h3><p class="hk-muted">' + either('Сейчас активной войны нет.','There is no active war right now.') + '</p><button id="hk-war-refresh" class="hk-secondary">' + either('Обновить','Refresh') + '</button>';
      warBox.querySelector('#hk-war-refresh').onclick = () => refreshModuleLive('wars',{force:true});
      return;
    }
    const opponent = clean(
      war.opponent_name || war.enemy_name || war.opponent_clan_name || war.enemy_clan_name ||
      war.opponent?.name || war.enemy?.name || either('Соперник','Opponent')
    );
    const ourScore = Math.max(0, Number(war.our_score ?? war.player_score ?? war.attacker_score ?? 0));
    const enemyScore = Math.max(0, Number(war.opponent_score ?? war.enemy_score ?? war.defender_score ?? 0));
    const status = clean(war.status || war.state || either('активна','active'));
    const direction = clean(war.direction || war.side || war.type || '');
    warBox.innerHTML =
      '<div class="hk-war-head"><div><h3>' + either('Войны клана','Clan Wars') + '</h3><small>' + escapeHtml(status) + '</small></div>' +
      '<button id="hk-war-refresh" class="hk-secondary">' + either('Обновить','Refresh') + '</button></div>' +
      '<div class="hk-war-score"><span><small>' + either('Наш счёт','Our score') + '</small><b>' + ourScore.toLocaleString(locale()) + '</b></span>' +
      '<strong>:</strong><span><small>' + escapeHtml(opponent) + '</small><b>' + enemyScore.toLocaleString(locale()) + '</b></span></div>' +
      '<div class="hk-war-meta">' +
      (direction ? '<span>' + either('Тип','Type') + '<b>' + escapeHtml(direction) + '</b></span>' : '') +
      '<span>' + either('Начало','Started') + '<b>' + escapeHtml(warTimeText(war.started_at)) + '</b></span>' +
      '<span>' + either('Окончание','Ends') + '<b>' + escapeHtml(warTimeText(war.ends_at)) + '</b></span>' +
      '</div><p class="hk-muted">' + either('Данные считываются существующим безопасным сборщиком войны; боевые действия не выполняются.','Data is read by the existing safe war collector; no battle actions are performed.') + '</p>';
    warBox.querySelector('#hk-war-refresh').onclick = () => refreshModuleLive('wars',{force:true});
  }

  async function loadWars() {
    if (!requireLicense() || warLoading) return warSnapshot;
    warLoading = true;
    renderWars();
    try {
      warSnapshot = await readPublicWar();
      renderWars();
      return warSnapshot;
    } catch (error) {
      log(either('Ошибка чтения войны','War read error') + ': ' + (error?.message || error),'warn');
      warSnapshot = {read:false,war:null};
      renderWars();
      return warSnapshot;
    } finally {
      warLoading = false;
      renderWars();
    }
  }

'''
    s = s.replace(anchor, module + anchor, 1)

nav_old = "{id:'clan',label:'navClan',hint:'navClanHint',image:'clan.png',modules:[{page:'clan',ru:'Навыки',en:'Skills'},{planned:true,ru:'Войны',en:'Wars'},{planned:true,ru:'Охота на крыс',en:'Rat Hunt'}]}"
nav_new = "{id:'clan',label:'navClan',hint:'navClanHint',image:'clan.png',modules:[{page:'clan',ru:'Навыки',en:'Skills'},{page:'wars',ru:'Войны',en:'Wars'},{planned:true,ru:'Охота на крыс',en:'Rat Hunt'}]}"
if nav_old in s:
    s = s.replace(nav_old, nav_new, 1)
elif nav_new not in s:
    raise SystemExit('Wars navigation anchor missing')

if 'data-content="wars"' not in s:
    anchor = '      <div class="hk-page" data-content="maps">'
    require(anchor, 'Maps page anchor missing')
    page = '''      <div class="hk-page" data-content="wars">
        <div id="hk-war-content" class="hk-cardbox"></div>
      </div>
'''
    s = s.replace(anchor, page + anchor, 1)

root_vars_old = 'mapIndexBox, mapDetailBox, dailyBox, clanBox, resourceBox;'
root_vars_new = 'mapIndexBox, mapDetailBox, dailyBox, clanBox, warBox, resourceBox;'
if root_vars_old in s:
    s = s.replace(root_vars_old, root_vars_new, 1)
elif root_vars_new not in s:
    raise SystemExit('Root variable list anchor missing')

assign_old = "dailyBox = root.querySelector('#hk-daily-tasks'); clanBox = root.querySelector('#hk-clan-content'); resourceBox = root.querySelector('#hk-resource-content');"
assign_new = "dailyBox = root.querySelector('#hk-daily-tasks'); clanBox = root.querySelector('#hk-clan-content'); warBox = root.querySelector('#hk-war-content'); resourceBox = root.querySelector('#hk-resource-content');"
if assign_old in s:
    s = s.replace(assign_old, assign_new, 1)
elif assign_new not in s:
    raise SystemExit('Root assignment anchor missing')

refresh_anchor = "        if (key === 'clan') {"
if "if (key === 'wars')" not in s:
    require(refresh_anchor, 'Clan live refresh anchor missing')
    wars_refresh = "        if (key === 'wars') {const value=await loadWars();liveReadOk=!!value;return value;}\n"
    s = s.replace(refresh_anchor, wars_refresh + refresh_anchor, 1)

activate_anchor = "      if (finalPage === 'clan') renderClanSkills();"
if "if (finalPage === 'wars') renderWars();" not in s:
    require(activate_anchor, 'Clan module activation anchor missing')
    s = s.replace(activate_anchor, activate_anchor + "\n      if (finalPage === 'wars') renderWars();", 1)

if '.hk-war-score{' not in s:
    style_anchor = '      .hk-business-tabs{'
    require(style_anchor, 'CSS anchor missing')
    css = "      .hk-war-head{display:flex;align-items:center;justify-content:space-between;gap:10px}.hk-war-head h3{margin:0}.hk-war-head small{color:#94a3b8}.hk-war-head button{width:auto;margin:0}.hk-war-score{display:grid;grid-template-columns:1fr auto 1fr;gap:12px;align-items:center;margin:14px 0;padding:14px;border:1px solid #35445a;border-radius:14px;background:#101927;text-align:center}.hk-war-score span{display:grid;gap:5px}.hk-war-score small{color:#95a3b7;font-size:10px}.hk-war-score b{font-size:24px;color:#ffe083}.hk-war-score strong{font-size:22px;color:#67768b}.hk-war-meta{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:7px}.hk-war-meta span{display:grid;gap:3px;padding:9px;border-radius:10px;background:#0d1520;color:#91a0b5;font-size:10px}.hk-war-meta b{color:#e4ebf5;font-size:11px}\n"
    s = s.replace(style_anchor, css + style_anchor, 1)

checks = [
    ('// @version      1.16.7','Stage 2H version missing'),
    (f"HK_STAGE2H_WARS_REV = '{REV}'",'Stage 2H marker missing'),
    ("{page:'wars',ru:'Войны',en:'Wars'}",'Wars navigation missing'),
    ('data-content="wars"','Wars page missing'),
    ('async function loadWars()','Wars loader missing'),
    ('warSnapshot = await readPublicWar();','Existing war collector is not reused'),
    ("if (key === 'wars')",'Wars live refresh missing'),
    ("if (finalPage === 'wars') renderWars();",'Wars render activation missing'),
    ("GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'",'Hamster Caps invariant lost'),
    ("GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'",'General Pit Token invariant lost'),
]
for needle,message in checks:
    require(needle,message)

TARGET.write_text(s,encoding='utf-8')
