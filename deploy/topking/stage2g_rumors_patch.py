from pathlib import Path

TARGET = Path('/tmp/HamsterKingMobile.user.js')
s = TARGET.read_text(encoding='utf-8')

REV = 'stage2g-rumors-20260919-r1'

def require(needle, message):
    if needle not in s:
        raise SystemExit(message)

if '// @version      1.16.5' not in s and '// @version      1.16.6' not in s:
    raise SystemExit('Stage 2G requires live 1.16.5 or existing Stage 2G 1.16.6')
require("HK_STAGE2F_RUNNER_REV = 'stage2f-clan-20260919-r1'", 'Stage 2F missing')
require('async function licensedServerJson(', 'licensed server helper missing')
require('async function runDailySelected()', 'Today runner missing')

if f"HK_STAGE2G_RUMORS_REV = '{REV}'" not in s:
    s = s.replace('// @version      1.16.5', '// @version      1.16.6', 1)
    s = s.replace(": '1.16.5';", ": '1.16.6';", 1)

    marker = "  const HK_STAGE2F_RUNNER_REV = 'stage2f-clan-20260919-r1';"
    require(marker, 'Stage 2F marker missing')
    s = s.replace(marker, marker + f"\n  const HK_STAGE2G_RUMORS_REV = '{REV}';", 1)

    runtime_marker = '  runtime.clanRunnerStage = HK_STAGE2F_RUNNER_REV;'
    require(runtime_marker, 'Stage 2F runtime marker missing')
    s = s.replace(runtime_marker, runtime_marker + "\n  runtime.rumorsStage = HK_STAGE2G_RUMORS_REV;", 1)

if "const RUMOR_API_BASE = 'https://hk-license.89.125.1.71.sslip.io/api/v1/rumors';" not in s:
    anchor = "  const PUBLIC_SNAPSHOT_API = 'https://hk-license.89.125.1.71.sslip.io/api/v1/public-snapshot';"
    require(anchor, 'public snapshot constant anchor missing')
    s = s.replace(anchor, anchor + "\n  const RUMOR_API_BASE = 'https://hk-license.89.125.1.71.sslip.io/api/v1/rumors';", 1)

if 'let dailyRumorRoute = [];' not in s:
    anchor = '  let mapScanning = false;'
    require(anchor, 'map state anchor missing')
    s = s.replace(anchor, anchor + "\n  let dailyRumorRoute = [];\n  let dailyAccountAreaIndex = [];", 1)

old_selection = "  let dailySelection = {...{advertisement:true, recruits:false, cartels:false, investments:false}, ...(load().today?.selection || {})};"
new_selection = "  let dailySelection = {...{advertisement:true, rumors:true, recruits:false, cartels:false, investments:false}, ...(load().today?.selection || {})};"
if old_selection in s:
    s = s.replace(old_selection, new_selection, 1)
elif new_selection not in s:
    raise SystemExit('Today selection anchor missing')
s = s.replace('  delete dailySelection.rumors;\n', '', 1)

if '  function dailyCityKey(value) {' not in s:
    anchor = '  function playRewardedAdInPageWorld() {'
    require(anchor, 'rewarded ad anchor missing')
    module = r'''  function dailyCityKey(value) {
    const key = clean(value).toLowerCase().replace(/ё/g, 'е').replace(/[^a-zа-я0-9]+/g, ' ').trim();
    const aliases = {
      'moscow':'moscow','москва':'moscow','spb':'spb','saint petersburg':'spb','st petersburg':'spb','санкт петербург':'spb',
      'minsk':'minsk','минск':'minsk','berlin':'berlin','берлин':'berlin','london':'london','лондон':'london',
      'paris':'paris','париж':'paris','dubai':'dubai','дубай':'dubai','tokyo':'tokyo','токио':'tokyo',
      'singapore':'singapore','сингапур':'singapore','new york':'new york','нью йорк':'new york',
      'los angeles':'los angeles','лос анджелес':'los angeles','boston':'boston','бостон':'boston',
      'washington':'washington','вашингтон':'washington','rio':'rio','rio de janeiro':'rio','рио':'rio','рио де жанейро':'rio',
      'lagos':'lagos','лагос':'lagos','sydney':'sydney','сидней':'sydney','auckland':'auckland','окленд':'auckland'
    };
    return aliases[key] || key.replace(/^(?:city|город)\s+/, '');
  }

  function dailyMapArea(rows, city, point) {
    const wantedCity = dailyCityKey(city);
    const wantedX = Number(point?.x), wantedY = Number(point?.y);
    return rows.find(row => Number(row?.x) === wantedY && Number(row?.y) === wantedX &&
      [row?.city_name, row?.city_id].some(value => {
        const cityKey = dailyCityKey(value);
        return cityKey && wantedCity && (cityKey.includes(wantedCity) || wantedCity.includes(cityKey));
      }));
  }

  async function rumorServerJson(path, body = {}, retry = true) {
    return licensedServerJson(RUMOR_API_BASE, path, body, retry, 'rumors');
  }

  async function loadRumorRoute() {
    try {
      const result = await rumorServerJson('/today');
      dailyRumorRoute = Array.isArray(result.routes) ? result.routes : [];
      dailyAccountAreaIndex = [];
      if (dailyRumorRoute.length) {
        const points = dailyRumorRoute.reduce((sum,row)=>sum+(Array.isArray(row?.points)?row.points.length:0),0);
        log(either('Маршрут слухов загружен: ','Rumor route loaded: ') + dailyRumorRoute.length + either(' городов · ',' cities · ') + points + either(' точек',' points'),'ok');
      }
      return dailyRumorRoute;
    } catch (error) {
      dailyRumorRoute = [];
      dailyAccountAreaIndex = [];
      log(either('Ошибка маршрута слухов','Rumor route error') + ': ' + (error?.message || error),'warn');
      return dailyRumorRoute;
    }
  }

  async function loadDailyAccountAreas() {
    if (dailyAccountAreaIndex.length) return dailyAccountAreaIndex;
    playerDocument = await apiJson('/player/me','POST');
    await ensureRecipeMetadata();
    const citiesValue = await apiJson('/cities','GET');
    const cities = Array.isArray(citiesValue) ? citiesValue : (Array.isArray(citiesValue?.cities) ? citiesValue.cities : []);
    const routeCities = new Set(dailyRumorRoute.map(row => dailyCityKey(row?.city)).filter(Boolean));
    const wantedCities = cities.filter(city => {
      const key = dailyCityKey(cityLabel(city));
      return routeCities.has(key) || [...routeCities].some(routeKey => key.includes(routeKey) || routeKey.includes(key));
    });
    const rows = [];
    let cursor = 0;
    const worker = async () => {
      while (cursor < wantedCities.length) {
        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');
        await hkRunner.waitIfPaused();
        const city = wantedCities[cursor++];
        const cityId = String(city?.id || '');
        try {
          const value = await apiJson('/city/' + encodeURIComponent(cityId) + '/game_area','GET');
          const areas = Array.isArray(value) ? value : (Array.isArray(value?.areas) ? value.areas : []);
          for (const area of areas) {
            const info = area?.info || {};
            const areaId = String(area?.id || area?.gamearea_id || '');
            const x = info?.x ?? area?.x ?? area?.meta?.gamearea_coords?.x;
            const y = info?.y ?? area?.y ?? area?.meta?.gamearea_coords?.y;
            if (areaId && x != null && y != null) rows.push({area_id:areaId,city_id:cityId,city_name:cityLabel(city),x:Number(x),y:Number(y)});
          }
        } catch (error) {
          if (error?.name === 'AbortError') throw error;
          log(either('Не удалось считать сетку города','Could not read city grid') + ' ' + cityLabel(city) + ': ' + (error?.message || error),'warn');
        }
      }
    };
    await Promise.all(Array.from({length:Math.min(4,Math.max(1,wantedCities.length))},worker));
    dailyAccountAreaIndex = rows;
    return rows;
  }

  async function runDailyRumors(internal = false) {
    if (!requireLicense() || (dailyRunning && !internal)) return;
    if (!dailyRumorRoute.length) await loadRumorRoute();
    if (!dailyRumorRoute.length) { log(either('Маршрут слухов не опубликован.','The rumor route is not published.'),'warn'); return; }
    if (!internal) {
      if (hkRunner.running) { alert(either('Сначала завершите текущую задачу','Finish the current task first')); return; }
      hkRunner.start({title:either('Слухи','Rumors'),total:dailyRumorRoute.length,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});
      dailyRunning = true;
      renderDailyTasks();
    }
    let collected = 0, completed = 0, checked = 0, completedCities = 0, skippedCities = 0, routeIndex = 0;
    try {
      const maps = await loadDailyAccountAreas();
      for (const route of dailyRumorRoute) {
        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');
        await hkRunner.waitIfPaused();
        if (!internal) hkRunner.setStep(route.city || either('Город','City'),routeIndex,dailyRumorRoute.length);
        routeIndex++;
        let cityCollected = 0, cityCompleted = 0, cityUnavailable = false;
        for (const point of route.points || []) {
          if (cityCompleted >= 3) break;
          if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');
          await hkRunner.waitIfPaused();
          const area = dailyMapArea(maps,route.city,point);
          const ids = area?.area_id ? [String(area.area_id)] : [];
          if (!ids.length) {
            log(String(route.city || '') + ' ' + Number(point?.x) + ':' + Number(point?.y) + ' — ' + either('район не найден','district not found'),'warn');
            continue;
          }
          let searched = false;
          for (const gameareaId of ids) {
            try {
              playerDocument = await apiJson('/rumors/search','POST',{gamearea_id:gameareaId});
              collected++; completed++; cityCollected++; cityCompleted++; checked++; searched = true;
              log(either('★ СЛУХ СОБРАН → ','★ RUMOR COLLECTED → ') + route.city + ' [' + point.x + ':' + point.y + '] (' + cityCompleted + '/3)','ok');
              break;
            } catch (error) {
              if (error?.name === 'AbortError') throw error;
              const message = String(error?.message || error);
              if (/player.{0,40}does.{0,20}not.{0,20}have.{0,20}city|does.{0,20}not.{0,20}have.{0,20}city.{0,40}(?:rumor|search)|нет.{0,30}город/i.test(message)) {
                cityUnavailable = true; searched = true;
                log('↷ ' + route.city + ' — ' + either('города нет на аккаунте, пропускаю','city is not available on this account, skipping'),'warn');
                break;
              }
              if (/already.{0,50}(?:searched.{0,20}rumor|research|explor)|(?:searched.{0,20}rumor|research|explor).{0,50}already|уже.{0,30}исследован/i.test(message)) {
                completed++; cityCompleted++; checked++; searched = true;
                log(either('✓ СЛУХ УЖЕ НАЙДЕН → ','✓ RUMOR ALREADY FOUND → ') + route.city + ' [' + point.x + ':' + point.y + '] (' + cityCompleted + '/3)','warn');
                break;
              }
              if (/no.{0,20}rumor.{0,20}(?:for|in).{0,20}gamearea|object.{0,20}not.{0,20}found/i.test(message)) {
                checked++; searched = true;
                log(either('— СЛУХ НЕ НАЙДЕН → ','— NO RUMOR FOUND → ') + route.city + ' [' + point.x + ':' + point.y + ']','warn');
                break;
              }
              throw error;
            }
          }
          if (cityUnavailable) break;
          if (!searched) checked++;
          await gameRetryDelay(300);
        }
        if (cityUnavailable) { skippedCities++; continue; }
        if (cityCompleted >= 3) completedCities++;
        const today = load().today || {};
        const rumors = {...(today.rumors || {}),[dailyCityKey(route.city)]:{city:route.city,completed:cityCompleted,collected:cityCollected,updatedAt:Date.now(),periodStart:gamePeriodBounds().dayStart}};
        save({today:{...today,rumors}});
      }
      const availableCities = Math.max(0,dailyRumorRoute.length-skippedCities);
      log(either('Сбор слухов завершён: ','Rumor collection completed: ') + completedCities + '/' + availableCities + either(' городов · новых ',' cities · new ') + collected + either(' · проверено ',' · checked ') + checked, completedCities ? 'ok' : 'warn');
      if (!internal) hkRunner.finish(either('Слухи собраны','Rumors completed'));
    } catch (error) {
      if (!internal && error?.name === 'AbortError') {
        hkRunner.reset();
        log(either('Сбор слухов остановлен','Rumor collection stopped'),'warn');
      } else {
        if (!internal) hkRunner.fail(error);
        log(either('Сбор слухов остановлен','Rumor collection stopped') + ': ' + (error?.message || error),'bad');
        if (internal) throw error;
      }
    } finally {
      if (!internal) { dailyRunning = false; renderDailyTasks(); }
    }
  }

'''
    s = s.replace(anchor, module + anchor, 1)

old_actions = """    const actions = [
      {id:'advertisement', label:tr('dailyAds'), kind:'advertisement', uiGroup:'free', free:true, available:ad.available}
    ];"""
new_actions = """    const actions = [
      {id:'rumors', label:either('Слухи','Rumors'), kind:'rumors', uiGroup:'free', free:true, available:dailyRumorRoute.length > 0},
      {id:'advertisement', label:tr('dailyAds'), kind:'advertisement', uiGroup:'free', free:true, available:ad.available}
    ];"""
if old_actions in s:
    s = s.replace(old_actions,new_actions,1)
elif new_actions not in s:
    raise SystemExit('Today free action block missing')

if 'const rumorsStored = load().today?.rumors || {};' not in s:
    anchor = "    const currencies = discoveredCurrencyIds();\n    const ad = dailyAdvertisement();"
    require(anchor, 'Today render variable anchor missing')
    addition = """    const currencies = discoveredCurrencyIds();
    const rumorsStored = load().today?.rumors || {};
    const rumorPeriodStart = gamePeriodBounds().dayStart;
    const routeHtml = dailyRumorRoute.length ? '<ul>' + dailyRumorRoute.map(row => {
      const progress = rumorsStored[dailyCityKey(row.city)];
      const count = progress?.periodStart === rumorPeriodStart ? Math.min(3,Number(progress.completed || 0)) : 0;
      const points = (row.points || []).map(point => Number(point.x) + ':' + String(Number(point.y)).padStart(2,'0')).join(' · ');
      return '<li><b>' + escapeHtml(row.city) + '</b><span>' + count + '/3 · ' + escapeHtml(points) + '</span></li>';
    }).join('') + '</ul>' : '<span>' + either('Маршрут слухов не опубликован','Rumor route is not published') + '</span>';
    const ad = dailyAdvertisement();"""
    s = s.replace(anchor,addition,1)

rumor_section = "      <section class=\"hk-today-section\"><h4>${either('Слухи','Rumors')}</h4>${routeHtml}</section>\n"
if rumor_section not in s:
    anchor = "      <section class=\"hk-today-section\"><h4>${tr('dailyBalances')}</h4><div class=\"hk-today-balances\">${balancesHtml}</div></section>\n"
    require(anchor, 'Today balances markup anchor missing')
    s = s.replace(anchor,anchor+rumor_section,1)

refresh_anchor = "      if (!shopViewDocument) log(tr('dailyNoShop'), 'warn');\n      fairDocument = playerDocument;"
if refresh_anchor in s:
    s = s.replace(refresh_anchor,"      if (!shopViewDocument) log(tr('dailyNoShop'), 'warn');\n      await loadRumorRoute();\n      fairDocument = playerDocument;",1)
elif 'await loadRumorRoute();' not in s[s.find('async function refreshDailyTasks()'):s.find('function resourceCost(',s.find('async function refreshDailyTasks()'))]:
    raise SystemExit('Today refresh anchor missing')

runner_anchor = "          if (action.kind === 'advertisement') await runDailyAd(true);"
if runner_anchor in s:
    s = s.replace(runner_anchor,"          if (action.kind === 'rumors') await runDailyRumors(true);\n          else if (action.kind === 'advertisement') await runDailyAd(true);",1)
elif "action.kind === 'rumors'" not in s:
    raise SystemExit('Today action dispatcher anchor missing')

checks = [
    ('// @version      1.16.6','Stage 2G version missing'),
    (f"HK_STAGE2G_RUMORS_REV = '{REV}'",'Stage 2G marker missing'),
    ("const RUMOR_API_BASE = 'https://hk-license.89.125.1.71.sslip.io/api/v1/rumors';",'Rumors API missing'),
    ('let dailyRumorRoute = [];','Rumor route state missing'),
    ("{id:'rumors'",'Today Rumors action missing'),
    ("apiJson('/rumors/search','POST'",'Rumors game mutation missing'),
    ("await loadRumorRoute();",'Rumor route refresh missing'),
    ("action.kind === 'rumors'",'Today Rumors dispatcher missing'),
    ("GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'",'Hamster Caps invariant lost'),
    ("GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'",'General Pit Token invariant lost'),
]
for needle,message in checks:
    require(needle,message)

TARGET.write_text(s,encoding='utf-8')
