// ==UserScript==
// @name         Hamster King Mobile
// @namespace    hamsterking.local
// @version      1.17.4
// @description  Mobile panel for Pit battles, businesses, fairs, shops and community recipes.
// @release-note Hotfix версии bookmarklet: metadata и runtime version синхронизированы; аудит валют и live-state сохранён.
// @match        https://app.hamsterking.games/*
// @run-at       document-start
// @grant        none
// ==/UserScript==

(() => {
  'use strict';
  const BUILD_VERSION = '1.17.4';
  const HK_RUNTIME_TAKEOVER_REV = 'runtime-takeover-20260920-r5';
  const HK_CORE_REVISION = 'core-20260920-r6';
  function hkRuntimeVersionTuple(value) {
    const match = String(value || '').match(/^\s*(\d+(?:\.\d+)*)/);
    return match ? match[1].split('.').map(Number) : [];
  }
  function hkRuntimeAtLeast(value, minimum) {
    const current = hkRuntimeVersionTuple(value);
    const required = hkRuntimeVersionTuple(minimum);
    if (!current.length || !required.length) return false;
    const width = Math.max(current.length, required.length);
    while (current.length < width) current.push(0);
    while (required.length < width) required.push(0);
    for (let index = 0; index < width; index++) {
      if (current[index] !== required[index]) return current[index] > required[index];
    }
    return true;
  }
  const previousRuntime = window.__HK_MOBILE_RUNTIME__;
  if (previousRuntime?.active && previousRuntime.revision === HK_CORE_REVISION) {
    try { previousRuntime.open?.(); } catch (_) {}
    return;
  }
  if (previousRuntime?.active) {
    try { previousRuntime.active = false; } catch (_) {}
    try { document.getElementById('hk-mobile-root')?.remove(); } catch (_) {}
    try { document.querySelectorAll('#hk-fab').forEach(node => node.remove()); } catch (_) {}
    try { window.__HK_MOBILE_RUNTIME__ = null; } catch (_) {}
    try { window.__HK_MOBILE_LOADED__ = false; } catch (_) {}
  }
  const runtime = {active:true, version:BUILD_VERSION, revision:HK_CORE_REVISION, open:null, ensure:null, destroy:null};
  window.__HK_MOBILE_RUNTIME__ = runtime;
  window.__HK_MOBILE_LOADED__ = true;
  window.__HK_MOBILE_VERSION__ = BUILD_VERSION;
  window.__HK_MOBILE_REVISION__ = HK_CORE_REVISION;

  // Always leave a visible diagnostic entry point until the real panel is
  // mounted.  This makes a failed start recoverable on Safari and desktop
  // userscript managers instead of looking like the script simply vanished.
  const HK_STARTUP_STAGE_REV = 'startup-stages-20260920-r7';
  const HK_STARTUP_ERROR_TRAP_REV = 'startup-error-trap-20260920-r8';
  let hkStartupStage = 'BOOT';
  let bootstrapProblem = '';
  let bootstrapButton = null;
  function showBootstrap(problem = '') {
    bootstrapProblem = String(problem || bootstrapProblem || ('HK '+HK_CORE_REVISION+' · '+hkStartupStage));
    if (!bootstrapButton) {
      bootstrapButton = document.createElement('button');
      bootstrapButton.id = 'hk-bootstrap-button';
      bootstrapButton.dataset.hkRevision = HK_CORE_REVISION;
      bootstrapButton.type = 'button';
      bootstrapButton.style.cssText = 'position:fixed;right:16px;bottom:90px;z-index:2147483647;border:0;border-radius:50%;width:58px;height:58px;background:#ff9f1c;color:#16110a;font:bold 20px Arial;box-shadow:0 8px 24px #0008';
      bootstrapButton.onclick = () => alert(bootstrapProblem+'\nrev='+HK_CORE_REVISION+'\nstage='+hkStartupStage);
    }
    bootstrapButton.textContent = problem ? 'HK!' : 'HK6';
    const host = document.documentElement || document.head;
    if (host && !bootstrapButton.isConnected) host.appendChild(bootstrapButton);
  }
  function hideBootstrap() { bootstrapButton?.remove(); }

  function hkStartupFailure(kind, value) {
    try {
      hkStartupStage = 'ERROR';
      const message = String(
        value?.stack ||
        value?.message ||
        value?.reason?.stack ||
        value?.reason?.message ||
        value ||
        'unknown startup error'
      ).slice(0, 1800);
      showBootstrap(kind + ': ' + message);
    } catch (_) {}
  }

  window.addEventListener('error', event => {
    hkStartupFailure('error', event?.error || event?.message || event);
  }, true);

  window.addEventListener('unhandledrejection', event => {
    hkStartupFailure('promise', event?.reason || event);
  }, true);

  showBootstrap();
  // HK UI is intentionally deferred until the native game login has completed.

  const VERSION = BUILD_VERSION;
  const HK_LAUNCHER_REV = 'launcher-hotfix-20260920-r1';
  const MENU_ICONS_BASE = 'https://tk-clan.ru/assets/menu';
  // Event offers are identified from the live /shop/view response. The game
  // keeps old event definitions in its catalog, but only current offers have
  // an active purchase limit (checked below before this classification).
  const STORE = 'hk_mobile_v1';
  const ASSET_BASE = 'https://cdn-prod-art.hwgame.cloud/items';
  const LICENSE_URL = 'https://hk-license.89.125.1.71.sslip.io/api/v1/check';
  const DONATION_URL = 'https://www.tbank.ru/cf/5Sta35vQwQM';
  const RECIPE_API_BASE = 'https://hk-license.89.125.1.71.sslip.io/api/v1/recipes';
  const MAP_API_BASE = 'https://hk-license.89.125.1.71.sslip.io/api/v1/maps';
  const PIT_API_BASE = 'https://hk-license.89.125.1.71.sslip.io/api/v1/pits';
  const SETTINGS_API_BASE = 'https://hk-license.89.125.1.71.sslip.io/api/v1/settings';
  const CLAN_SKILLS_API_BASE = 'https://hk-license.89.125.1.71.sslip.io/api/v1/clan-skills';
  const CLAN_SHOP_FACT_API_BASE = 'https://hk-license.89.125.1.71.sslip.io/api/v1';
  const PUBLIC_SNAPSHOT_API = 'https://hk-license.89.125.1.71.sslip.io/api/v1/public-snapshot';
  const RUMOR_API_BASE = 'https://hk-license.89.125.1.71.sslip.io/api/v1/rumors';
  const PUBLIC_SNAPSHOT_INTERVAL_MS = 15 * 60 * 1000;
  const LICENSE_RECHECK_MS = 60 * 60 * 1000;
  const GAME_API_FALLBACK = 'https://hk-game-api.hwgame.cloud';
  const GAME_AUTH_REFRESH_EARLY_MS = 60 * 1000;
  const GAME_REQUEST_RETRY_DELAYS_MS = [900, 2500, 6000];
  const SERVER_REQUEST_RETRY_DELAYS_MS = [1000, 3000, 7000];
  const DIAGNOSTIC_MAX_EVENTS = 180;
  const SHOP_UNLIMITED_RUN_MAX = 999;
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const clean = value => String(value || '').replace(/\s+/g, ' ').trim();
  const visible = element => !!(element && (element.offsetWidth || element.offsetHeight || element.getClientRects().length));
  const number = value => Number.isFinite(Number(value)) ? Number(value) : null;
  const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const diagnostic = {startedAt:new Date().toISOString(), events:[]};
  const healthState = {
    game:{ok:false, detail:'ожидание'}, auth:{ok:false, detail:'ожидание'},
    license:{ok:false, detail:'ожидание'}, server:{ok:false, detail:'ожидание'}
  };
  function diagnosticRedact(value, limit = 1800) {
    return String(value ?? '')
      .replace(/Bearer\s+[A-Za-z0-9._~-]+/gi, 'Bearer [REDACTED]')
      .replace(/eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/g, '[REDACTED_JWT]')
      .slice(0, limit);
  }
  function diagnosticFingerprint(value) {
    let hash = 2166136261;
    for (const char of String(value || '')) { hash ^= char.charCodeAt(0); hash = Math.imul(hash, 16777619); }
    return `hk-${(hash >>> 0).toString(16).padStart(8,'0')}`;
  }
  function recordDiagnostic(type, data = {}) {
    let safe = {};
    try { safe = JSON.parse(JSON.stringify(data, (_key, value) => typeof value === 'string' ? diagnosticRedact(value) : value)); }
    catch (_) { safe = {value:diagnosticRedact(data)}; }
    diagnostic.events.push({at:new Date().toISOString(), type:String(type || 'event'), data:safe});
    if (diagnostic.events.length > DIAGNOSTIC_MAX_EVENTS) diagnostic.events.splice(0, diagnostic.events.length - DIAGNOSTIC_MAX_EVENTS);
  }
  function setHealth(name, ok, detail = '') {
    if (!healthState[name]) return;
    healthState[name] = {ok:!!ok, detail:clean(detail || (ok ? 'OK' : 'ошибка'))};
    renderHealth();
  }
  function renderHealth() {
    if (!root) return;
    for (const name of ['game','auth','license','server']) {
      const item = root.querySelector(`[data-health="${name}"]`);
      if (!item) continue;
      const state = healthState[name];
      item.classList.toggle('ok', !!state.ok);
      item.classList.toggle('bad', !state.ok && state.detail !== 'ожидание');
      item.title = state.detail || '';
      const detail = item.querySelector('small');
      if (detail) detail.textContent = state.ok ? either('OK','OK') : state.detail === 'ожидание' ? either('ожидание','waiting') : either('проверить','check');
    }
  }
  function diagnosticEnvironment() {
    const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection || null;
    return {
      page:{origin:location.origin, pathname:location.pathname},
      browser:{userAgent:navigator.userAgent, language:navigator.language, onLine:navigator.onLine},
      viewport:{width:innerWidth, height:innerHeight, dpr:devicePixelRatio || 1},
      document:{visibilityState:document.visibilityState, readyState:document.readyState},
      timezone:Intl.DateTimeFormat().resolvedOptions().timeZone || '',
      connection:connection ? {effectiveType:connection.effectiveType || '', downlink:connection.downlink ?? null, rtt:connection.rtt ?? null, saveData:!!connection.saveData} : null
    };
  }
  function downloadDiagnosticReport() {
    const currentBearer = String(apiHeaders?.Authorization || '').replace(/^Bearer\s+/i,'');
    const report = {
      schema:'topking-hk-diagnostic-v1', version:VERSION, startedAt:diagnostic.startedAt, exportedAt:new Date().toISOString(),
      environment:diagnosticEnvironment(), health:healthState,
      gameAuth:{present:!!currentBearer, fingerprint:currentBearer ? diagnosticFingerprint(currentBearer) : '', expiresAt:jwtExpiration(currentBearer) || null},
      license:{checked:!!licenseState.checked, allowed:!!licenseState.allowed, playerId:clean(licenseState.playerId || ''), tokenPresent:!!licenseState.token},
      stateStore:hkStateStore?.exportSummary?.() || null,
      runner:{...hkRunner.state},
      gameBridge:hkGameBridge?.summary?.() || null,
      events:diagnostic.events
    };
    const blob = new Blob([JSON.stringify(report,null,2)], {type:'application/json;charset=utf-8'});
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url; link.download = `HK_diagnostic_${new Date().toISOString().replace(/[:.]/g,'-')}.json`;
    document.body.appendChild(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1200);
    recordDiagnostic('diagnostic-exported');
  }
  function showVisualNotice(title, details = '') {
    const host = root || document.body || document.documentElement;
    if (!host) return;
    let notice = host.querySelector?.('#hk-visual-notice');
    if (!notice) {
      notice = document.createElement('div');
      notice.id = 'hk-visual-notice';
      notice.style.cssText = 'position:fixed;left:50%;top:18px;transform:translateX(-50%);z-index:2147483647;width:min(440px,calc(100vw - 28px));box-sizing:border-box;padding:16px 48px 16px 18px;border:2px solid #42d69b;border-radius:16px;background:#10271f;color:#f5fff9;box-shadow:0 14px 40px #000b;font:15px/1.35 Arial,sans-serif';
      host.appendChild(notice);
    }
    clearTimeout(notice.__hkTimer);
    notice.innerHTML = `<button type="button" aria-label="Close" style="position:absolute;right:9px;top:8px;width:32px;height:32px;border:0;border-radius:9px;background:#ffffff1c;color:#fff;font-size:22px">×</button><b style="display:block;font-size:18px;color:#6ee7a8">✓ ${escapeHtml(title)}</b>${details ? `<span style="display:block;margin-top:5px;color:#d7e7df">${escapeHtml(details)}</span>` : ''}`;
    notice.querySelector('button').onclick = () => notice.remove();
    notice.__hkTimer = setTimeout(() => notice.remove(), 15000);
    try { navigator.vibrate?.([120, 60, 120]); } catch (_) {}
  }
  const load = () => {
    try { return JSON.parse(localStorage.getItem(STORE) || '{}'); } catch (_) { return {}; }
  };
  const save = patch => {
    const userKeys = Object.keys(patch || {}).filter(key => !['deviceId', 'watermarkCode', '_settingsUpdatedAt'].includes(key));
    const next = {...load(), ...patch, ...(userKeys.length ? {_settingsUpdatedAt:Date.now()} : {})};
    localStorage.setItem(STORE, JSON.stringify(next));
    try { if (userKeys.length) queueSettingsSync(next); } catch (_) {}
    return next;
  };

  let language = load().language === 'en' ? 'en' : 'ru';
  const TEXT = {
    ru: {
      daily:'Сегодня', pit:'Яма', businesses:'Бизнесы', clan:'Клан', fair:'Ярмарка', shop:'Магазин', recipes:'Рецепты', maps:'Карты', navToday:'Сегодня', navBattles:'Бои', navCity:'Город', navBusiness:'Бизнес', navGrowth:'Развитие', navTrade:'Торговля', navClan:'Клан', navTodayHint:'задачи и награды', navBattlesHint:'ямы и бои', navCityHint:'карты и здания', navBusinessHint:'карты и рецепты', navGrowthHint:'хомяки и генералы', navTradeHint:'ярмарка и магазин', navClanHint:'навыки и войны', checkingLicense:'Проверяю лицензию…',
      dailyTasks:'Сегодня', dailyRefresh:'Только проверить', dailyRun:'Выполнить выбранное', dailyAdRun:'Просмотреть доступную рекламу', dailyClear:'Очистить журнал', dailyOverall:'Общий прогресс', dailyCurrent:'Текущий этап', dailyAds:'Реклама', dailyClan:'Покупки клана', dailyInvest:'Инвестиционные предложения', dailyReady:'Готово к запуску', dailyNoShop:'Сначала откройте в игре магазин и нажмите «Только проверить».',
      dailyBalances:'Балансы', dailyStores:'Доступные покупки', dailyFreeActions:'Бесплатные действия', dailyRegularActions:'Регулярный магазин', dailyOrdinaryActions:'Обычный магазин', dailyClanActions:'Личные лоты клана', dailyInvestActions:'Инвест-сделки', dailyPit:'Состояние Ямы', pitNormal:'Обычная Яма', pitBoss:'Яма боссов', pitGang:'Яма банд', pitAvailableNow:'доступно сейчас', pitLimit:'лимит', pitDiamondTopUp:'догон за 💎', pitMultipleReady:'уже кратно 5', pitOpenOnce:'Откройте этот раздел Ямы один раз', pitRun:'Запускать', pitUseMoves:'Отходить', pitMovePlan:'Оптимально', pitNoMoves:'не выбрано', dailyConsigliere:'Консильери', dailyPlan:'План выполнения', dailyBudget:'Единый бюджет', dailyReserve:'Оставить минимум', dailyLimit:'Лимит в сутки', weeklyLimit:'Лимит в неделю', spentToday:'Сегодня потрачено', spentWeek:'За неделю', allowPremium:'Разрешить алмазы', exportSettings:'Экспорт настроек', importSettings:'Восстановить настройки', noLimit:'Без лимита', selectedActions:'Выбрано действий: {n}', exactPlan:'Проверьте точный план расходов перед запуском.',
      targetRound:'Дойти до раунда', delay:'Пауза, секунд', activationTokens:'Жетоны на активацию', pitCollectOnly:'Только собирать данные — не нажимать бой', pitForecast:'Прогноз до цели', pitObserved:'Сохранено уровней: {n}', pitPredictedPower:'Прогноз силы на раунде {round}: {power}', pitTokenBudget:'Максимальный разрешённый расход: {n} жетонов', pitComparison:'За запуск: раунд {before} → {after}, сила {powerBefore} → {powerAfter}', pitPowerTable:'Сохранённая сила уровней',
      restoreTokens:'Жетоны на восстановление', allowTokens:'Разрешить жетоны', round:'Раунд', startBattle:'Запустить автобой',
      stop:'Остановить', exportCsv:'Скачать силу уровней CSV', refreshGame:'Обновить игру', waiting:'Ожидание подключения…',
      savedSets:'Сохранённые наборы', saveNew:'Сохранить новый', delete:'Удалить', removeAll:'Достать: все тиры',
      emptySlots:'Пустые слоты', removeTier:'Достать: T{n}', selectAll:'Выбрать все', insertAll:'Вставить: все тиры',
      insertTier:'Вставить: T{n}', loadFair:'Обновить ярмарку', chooseFair:'Выберите ярмарку', readFirst:'Сначала считайте данные',
      searchLot:'Поиск лота', choosePurchases:'Выберите покупки', selectedLots:'Выбрано лотов: {n}', totalPurchases:'Всего покупок',
      maxRerolls:'Макс. прокруток', allowDiamonds:'Разрешить алмазы на прокрутки и покупки', findBuy:'Найти и выкупить',
      fairWarning:'Лоты за кристаллы отмечены 💎. Перед запуском показывается максимальный расход.', version:'Версия {v}',
      connectedSlots:'Подключено · слотов {n}', chooseBuildingSlots:'Выбрать слоты в зданиях', insertFromStock:'Вставить со склада',
      emptySlot:'Пустой слот', influence:'Влияние {n}', inStock:'На складе {n}', noBusinesses:'Нет бизнесов этого тира',
      buildingSlot:'Здание {building} · слот {slot}', selectedPlan:'Выбрано: слотов {remove} · вставить {insert}', execute:'Выполнить перестановку',
      businessRegular:'Обычная перестановка', businessOptimizer:'Оптимизатор', optimizer:'Умный оптимизатор', optimizerGoal:'Цель', optimizerPit:'Сила в Яме', optimizerIncome:'Пассивный доход', optimizerEnergy:'Энергия', optimizerBuildings:'Лимит зданий', optimizerRemoveTiers:'Какие тиры можно достать', optimizerInsertTiers:'Какие тиры можно вставить', optimizerReplaceable:'Какие установленные бизнесы можно заменять', optimizerReplaceHint:'Снятая галочка защищает все экземпляры этого бизнеса', optimizerStockAllowed:'Какие складские бизнесы можно вставить', optimizerStockHint:'Выбор доступен вручную для всех тиров', optimizerCalculate:'Рассчитать лучший состав', optimizerApply:'Перенести в план', optimizerRestore:'Вернуть сохранённую схему', optimizerNoPlan:'Сначала считайте бизнесы и рассчитайте состав.', optimizerChanges:'Замен: {n}', optimizerManagers:'Менеджеры: {busy}/{max}', optimizerSafe:'Проверка пройдена', optimizerBlocked:'Запуск заблокирован', optimizerBefore:'Было', optimizerAfter:'Станет', optimizerDifference:'Изменение бонусов',
      bonusAnalyzer:'Анализатор бонусов', bonusSources:'Источники бонусов', bonusDuplicates:'одинаковых источников: {n}', bonusActiveCopies:'активно: {active} / лимит: {limit}', bonusNoLimit:'лимит не указан', bonusBestNext:'Лучший следующий бизнес', bonusNoCandidate:'Подходящего бизнеса на складе нет', bonusLimited:'Лимит активных экземпляров уже достигнут', bonusZeroEffect:'Эффект не распознан',
      all:'Все', blocked:'заблокировано', noLots:'Лоты не найдены', noFairs:'Нет ярмарок с доступными лотами',
      allowedCells:'Разрешённые слоты', cell:'Ячейка {n}', selectCellsHint:'Выберите, из каких групп слотов разрешён выкуп',
      regularSlots:'Обычные', vipSlots:'VIP', yes:'ДА', no:'НЕТ', noCells:'Для выбранного товара отключены и обычные, и VIP-слоты', fairSavedSettings:'Сохранённые настройки',
      fairExactLots:'Искать комбинации до', fairBonusLots:'Выкупить бонусные лоты',
      saveSetting:'Сохранить настройку', updateSetting:'Обновить', settingName:'Название настройки:', settingSaved:'Настройка «{name}» сохранена',
      settingLoaded:'Настройка «{name}» загружена', deleteSetting:'Удалить настройку «{name}»?',
      regularShop:'Регулярный магазин', ordinaryShop:'Обычный магазин', clanShop:'Магазин клана', readShop:'Обновить магазин', selectAvailable:'Выбрать доступные', shopReadFirst:'Сначала считайте магазин',
      remaining:'Осталось {n}', unlimited:'Без лимита', boughtOut:'Выкуплено', selectedPurchases:'Выбрано покупок: {n}', maxCost:'Максимальная стоимость',
      balance:'Баланс', willSpend:'Расход', balanceAfter:'Останется',
      buySelected:'Выкупить выбранное', shopWarning:'Лоты за кристаллы доступны только в ярмарке и магазине клана и отмечены 💎. Внешняя оплата заблокирована.',
      resourcesShop:'Ресурсы', renovationShop:'Реновация', investShop:'Инвест-сделки', personalLots:'Личные лоты', sharedLots:'Общие лоты', quantity:'Количество',
      recipeSpin:'Каталог', recipeDatabase:'Общая база', projectBureau:'Проектное бюро', readRecipes:'Обновить каталог', recipeAttempts:'Количество прокруток',
      spinRecipes:'Прокрутить каталог', currentRecipePlans:'Сейчас в каталоге', recipeCost:'Цена одной прокрутки',
      loadRecipeDatabase:'Обновить общую базу', uniqueRecipes:'Уникальных бизнес-планов: {n}', uniqueRecipeResults:'Итоговых бизнесов: {results} · рецептов: {plans}', recipeWays:'Вариантов получения: {n}', recipeReadFirst:'Сначала считайте каталог',
      recipeDatabaseEmpty:'В общей базе пока нет бизнес-планов', recipeSharedHint:'Каждый увиденный бизнес-план добавляется в общую базу один раз. Повторные выпадения не засчитываются.',
      readBureau:'Считать бизнесы', bureauSize:'Бизнесов в проекте', bureauAttempts:'Количество созданий', bureauSelected:'Выбрано бизнесов: {n} / {max}',
      createBusinessPlan:'Создать бизнес-план', bureauHint:'Действия Проектного бюро не добавляются в общую базу и не сохраняются.',
      bureauTier:'Тир бизнеса', bureauAllTiers:'Все тиры', mapIndex:'Исследованные карты', readMapIndex:'Обновить индекс', scanMyMaps:'Исследовать мои районы',
      donation:'Пожертвование', mapSearch:'Город, район или координаты', mapOpen:'Открыть', mapProgress:'Прогресс', mapRating:'Рейтинг', mapBuildings:'Здания', mapUnexplored:'Не исследовано', mapRooms:'Алмазные комнаты',
      myMaps:'Мои карты', uploadedMaps:'Загруженные карты', scanAccountMaps:'Считать карты аккаунта', refreshUploadedMaps:'Обновить загруженные карты'
    },
    en: {
      daily:'Today', pit:'Pit', businesses:'Businesses', clan:'Clan', fair:'Fair', shop:'Shop', recipes:'Recipes', maps:'Maps', navToday:'Today', navBattles:'Battles', navCity:'City', navBusiness:'Business', navGrowth:'Growth', navTrade:'Trade', navClan:'Clan', navTodayHint:'tasks and rewards', navBattlesHint:'pits and battles', navCityHint:'maps and buildings', navBusinessHint:'cards and recipes', navGrowthHint:'hamsters and generals', navTradeHint:'fair and shop', navClanHint:'skills and wars', checkingLicense:'Checking license…',
      dailyTasks:'Today', dailyRefresh:'Check only', dailyRun:'Run selected', dailyAdRun:'Watch available ad', dailyClear:'Clear log', dailyOverall:'Overall progress', dailyCurrent:'Current stage', dailyAds:'Ads', dailyClan:'Clan purchases', dailyInvest:'Investment offers', dailyReady:'Ready to start', dailyNoShop:'Open the in-game shop first, then tap “Check only”.',
      dailyBalances:'Balances', dailyStores:'Available purchases', dailyFreeActions:'Free actions', dailyRegularActions:'Regular shop', dailyOrdinaryActions:'Standard shop', dailyClanActions:'Personal clan lots', dailyInvestActions:'Invest deals', dailyPit:'Pit status', pitNormal:'Normal Pit', pitBoss:'Boss Pit', pitGang:'Gang Pit', pitAvailableNow:'available now', pitLimit:'limit', pitDiamondTopUp:'diamond top-up', pitMultipleReady:'already divisible by 5', pitOpenOnce:'Open this Pit section once', pitRun:'Run', pitUseMoves:'Use moves', pitMovePlan:'Optimal', pitNoMoves:'not selected', dailyConsigliere:'Consigliere', dailyPlan:'Execution plan', dailyBudget:'Unified budget', dailyReserve:'Minimum balance', dailyLimit:'Daily limit', weeklyLimit:'Weekly limit', spentToday:'Spent today', spentWeek:'Spent this week', allowPremium:'Allow diamonds', exportSettings:'Export settings', importSettings:'Restore settings', noLimit:'No limit', selectedActions:'Selected actions: {n}', exactPlan:'Review the exact spending plan before running.',
      targetRound:'Reach round', delay:'Delay, seconds', activationTokens:'Activation tokens', pitCollectOnly:'Collect data only — never click battle', pitForecast:'Forecast to target', pitObserved:'Saved levels: {n}', pitPredictedPower:'Predicted power at round {round}: {power}', pitTokenBudget:'Maximum allowed spend: {n} tokens', pitComparison:'This run: round {before} → {after}, power {powerBefore} → {powerAfter}', pitPowerTable:'Saved level powers', restoreTokens:'Recovery tokens',
      allowTokens:'Allow tokens', round:'Round', startBattle:'Start auto battle', stop:'Stop', exportCsv:'Download level power CSV',
      refreshGame:'Refresh game', waiting:'Waiting for connection…', savedSets:'Saved sets', saveNew:'Save new', delete:'Delete',
      removeAll:'Remove: all tiers', emptySlots:'Empty slots', removeTier:'Remove: T{n}', selectAll:'Select all',
      insertAll:'Insert: all tiers', insertTier:'Insert: T{n}', loadFair:'Refresh fair', chooseFair:'Choose a fair',
      readFirst:'Read the data first', searchLot:'Search lots', choosePurchases:'Choose purchases', selectedLots:'Selected lots: {n}',
      totalPurchases:'Total purchases', maxRerolls:'Max rerolls', allowDiamonds:'Allow diamonds for rerolls and purchases',
      findBuy:'Find and buy', fairWarning:'Crystal lots are marked 💎. The maximum cost is shown before starting.',
      version:'Version {v}', connectedSlots:'Connected · slots {n}', chooseBuildingSlots:'Choose building slots', insertFromStock:'Insert from stock',
      emptySlot:'Empty slot', influence:'Influence {n}', inStock:'In stock {n}', noBusinesses:'No businesses of this tier',
      buildingSlot:'Building {building} · slot {slot}', selectedPlan:'Selected: slots {remove} · insert {insert}', execute:'Run rearrangement',
      businessRegular:'Manual rearrangement', businessOptimizer:'Optimizer', optimizer:'Smart optimizer', optimizerGoal:'Goal', optimizerPit:'Pit power', optimizerIncome:'Passive income', optimizerEnergy:'Energy', optimizerBuildings:'Building limit', optimizerRemoveTiers:'Tiers allowed to be removed', optimizerInsertTiers:'Tiers allowed to be inserted', optimizerReplaceable:'Installed businesses allowed to be replaced', optimizerReplaceHint:'Clear a checkbox to protect every copy of that business', optimizerStockAllowed:'Stock businesses allowed to be inserted', optimizerStockHint:'Every tier remains manually selectable', optimizerCalculate:'Calculate best setup', optimizerApply:'Move to plan', optimizerRestore:'Restore saved setup', optimizerNoPlan:'Read businesses and calculate a setup first.', optimizerChanges:'Replacements: {n}', optimizerManagers:'Managers: {busy}/{max}', optimizerSafe:'Safety check passed', optimizerBlocked:'Start is blocked', optimizerBefore:'Before', optimizerAfter:'After', optimizerDifference:'Bonus changes',
      bonusAnalyzer:'Bonus analyzer', bonusSources:'Bonus sources', bonusDuplicates:'matching sources: {n}', bonusActiveCopies:'active: {active} / limit: {limit}', bonusNoLimit:'limit not specified', bonusBestNext:'Best next business', bonusNoCandidate:'No suitable business in stock', bonusLimited:'Active-copy limit reached', bonusZeroEffect:'Effect was not recognized',
      all:'All', blocked:'blocked', noLots:'No lots found', noFairs:'No fairs with available lots',
      allowedCells:'Allowed slots', cell:'Cell {n}', selectCellsHint:'Choose which slot groups are allowed for purchases',
      regularSlots:'Regular', vipSlots:'VIP', yes:'YES', no:'NO', noCells:'Both regular and VIP slots are disabled for a selected item', fairSavedSettings:'Saved settings', saveSetting:'Save setting',
      fairExactLots:'Search combinations up to', fairBonusLots:'Buy bonus lots',
      updateSetting:'Update', settingName:'Setting name:', settingSaved:'Setting “{name}” saved', settingLoaded:'Setting “{name}” loaded',
      deleteSetting:'Delete setting “{name}”?', regularShop:'Regular shop', ordinaryShop:'Standard shop', clanShop:'Clan shop', readShop:'Refresh shop', selectAvailable:'Select available',
      shopReadFirst:'Read the shop first', remaining:'Remaining {n}', unlimited:'Unlimited', boughtOut:'Purchased', selectedPurchases:'Selected purchases: {n}',
      balance:'Balance', willSpend:'Spend', balanceAfter:'Remaining',
      maxCost:'Maximum cost', buySelected:'Buy selected', shopWarning:'Crystal lots are available only in the fair and clan shop and are marked 💎. External payments are blocked.',
      resourcesShop:'Resources', renovationShop:'Renovation', investShop:'Invest deals', personalLots:'Personal lots', sharedLots:'Shared lots', quantity:'Quantity',
      recipeSpin:'Catalog', recipeDatabase:'Shared database', projectBureau:'Project Bureau', readRecipes:'Refresh catalog', recipeAttempts:'Reroll count',
      spinRecipes:'Reroll catalog', currentRecipePlans:'Currently in catalog', recipeCost:'Cost per reroll',
      loadRecipeDatabase:'Refresh shared database', uniqueRecipes:'Unique business plans: {n}', uniqueRecipeResults:'Result businesses: {results} · recipes: {plans}', recipeWays:'Ways to obtain: {n}', recipeReadFirst:'Read the catalog first',
      recipeDatabaseEmpty:'No business plans in the shared database yet', recipeSharedHint:'Each observed business plan is added to the shared database once. Repeat drops are ignored.',
      readBureau:'Read businesses', bureauSize:'Businesses per project', bureauAttempts:'Creation count', bureauSelected:'Selected businesses: {n} / {max}',
      createBusinessPlan:'Create business plan', bureauHint:'Project Bureau actions are not added to the shared database and are not stored.',
      bureauTier:'Business tier', bureauAllTiers:'All tiers', mapIndex:'Researched maps', readMapIndex:'Refresh index', scanMyMaps:'Research my districts',
      donation:'Donation', mapSearch:'City, district or coordinates', mapOpen:'Open', mapProgress:'Progress', mapRating:'Rating', mapBuildings:'Buildings', mapUnexplored:'Unresearched', mapRooms:'Diamond rooms',
      myMaps:'My maps', uploadedMaps:'Uploaded maps', scanAccountMaps:'Read account maps', refreshUploadedMaps:'Refresh uploaded maps'
    }
  };
  const tr = (key, vars = {}) => {
    let value = TEXT[language]?.[key] ?? TEXT.ru[key] ?? key;
    for (const [name, replacement] of Object.entries(vars)) value = value.replaceAll(`{${name}}`, replacement);
    return value;
  };
  const locale = () => language === 'en' ? 'en-US' : 'ru-RU';
  const either = (ru, en) => language === 'en' ? en : ru;
  function localizeMessage(value) {
    if (language !== 'en') return String(value);
    let text = String(value);
    const replacements = [
      [/Проверяю лицензию…/g,'Checking license…'], [/Доступ разрешён/g,'Access granted'], [/Проверка лицензии…/g,'Checking license…'],
      [/ID не добавлен владельцем/g,'ID has not been added by the owner'], [/Лицензия заблокирована/g,'License is blocked'],
      [/Срок лицензии истёк/g,'License has expired'], [/Достигнут лимит устройств/g,'Device limit reached'],
      [/Домен игры не разрешён/g,'Game domain is not allowed'], [/Не удалось определить ID игрового аккаунта/g,'Could not identify the game account ID'],
      [/Не удалось определить аккаунт/g,'Could not identify the account'], [/Сервер лицензий недоступен/g,'License server is unavailable'],
      [/Добавьте этот ID в панели владельца/g,'Add this ID in the owner panel'], [/Проверка не пройдена/g,'License check failed'],
      [/Подключено/g,'Connected'], [/Ожидание подключения…/g,'Waiting for connection…'], [/Автобой запущен до раунда/g,'Auto battle started up to round'],
      [/Автобой остановлен/g,'Auto battle stopped'], [/Цель достигнута: раунд/g,'Target reached: round'], [/Ускорение боя включено/g,'Battle speed enabled'],
      [/Остановка: достигнут лимит жетонов восстановления/g,'Stopped: recovery token limit reached'],
      [/Остановка: достигнут лимит жетонов активации/g,'Stopped: activation token limit reached'],
      [/Требуется восстановление, но расход жетонов запрещён/g,'Recovery is required, but token spending is disabled'],
      [/Восстановление жетоном/g,'Recovery token'], [/Активация жетоном/g,'Activation token'],
      [/Считываю ярмарки…/g,'Reading fairs…'], [/Ярмарка считана:/g,'Fair loaded:'], [/Ошибка ярмарки:/g,'Fair error:'],
      [/Лот найден\. Покупка/g,'Lot found. Purchase'], [/Куплено/g,'Purchased'], [/Достигнут лимит прокруток:/g,'Reroll limit reached:'],
      [/Лота нет\. Прокрутка/g,'No lot. Reroll'], [/Ярмарка завершена: покупок/g,'Fair completed: purchases'],
      [/прокруток/g,'rerolls'], [/Аварийная остановка ярмарки:/g,'Emergency fair stop:'],
      [/Пустой слот:/g,'Empty slot:'], [/Снимаю/g,'Removing'], [/Вставляю/g,'Inserting'], [/Перестановка завершена/g,'Rearrangement completed'],
      [/Исходная схема восстановлена/g,'Original layout restored'], [/Ошибка:/g,'Error:'], [/Набор/g,'Set'], [/сохранён/g,'saved'], [/выбран/g,'selected']
    ];
    for (const [pattern, replacement] of replacements) text = text.replace(pattern, replacement);
    return text;
  }

  let settings = {
    target: 200,
    interval: 1.2,
    allowTokens: true,
    activationLimit: 1,
    restoreLimit: 5,
    collectOnly: false,
    ...load().settings
  };
  let pitRunning = false;
  let activationSpent = 0;
  let restoreSpent = 0;
  let pitRunStart = null;
  let playerDocument = null;
  let apiBase = '';
  let apiHeaders = {};
  let layout = [];
  let inventory = [];
  let selectedSlots = new Set();
  let selectedStock = new Map();
  let businessBusy = false;
  let optimizerResult = null;
  let preparedBusinessPlan = null;
  let preparedBusinessPlanSource = '';
  let networkCaptureInstalled = false;
  let nativeNetworkFetch = null;
  let authUpdatedAt = 0;
  let authCreatePromise = null;
  let licenseState = {checked:false, allowed:false, playerId:'', reason:'Проверка лицензии…', update:null};
  let licenseCheckPromise = null;
  let lastLicenseCheck = 0;
  let publicSnapshotPromise = null;
  let lastPublicSnapshot = 0;
  let settingsSyncReady = false;
  let settingsSyncTimer = null;
  let settingsSyncPromise = null;
  let fairDocument = null;
  let shopViewDocument = null;
  let itemCatalogDocument = null;
  let businessCatalogDocument = null;
  let bonusCatalogDocument = null;
  let eventCatalogDocument = null;
  let clientConfigDocument = null;
  let premiumDocument = null;
  let localizationDocument = null;
  let activeEventCode = clean(load().activeEventCode || '').toLowerCase();
  let fairCatalog = [];
  let selectedFairId = '';
  let selectedFairLots = new Set();
  let selectedFairSlotRules = new Map(); // lot id -> {regular:boolean, vip:boolean}
  let selectedFairCurrency = '';
  let selectedFairBonusLots = new Set([5, 10, 30]);
  let fairRunning = false;
  let fairStop = false;
  let shopRows = [];
  let selectedShopLots = new Set();
  let selectedShopCounts = new Map();
  let selectedShopSection = 'regular';
  let selectedShopGroup = 'resources';
  let shopRunning = false;
  let recipeFairId = load().recipeFairId || '';
  let currentRecipePlans = [];
  let recipeRunning = false;
  let recipeStop = false;
  let communityRecipes = [];
  let bureauCosts = [];
  let bureauInventory = [];
  let selectedBureauInputs = new Map();
  let bureauSize = 2;
  let bureauTier = 0;
  let bureauRunning = false;
  let mapRows = [];
  let mapSource = 'mine';
  let mapDetail = null;
  let mapGeometry = null;
  let mapZoom = 1;
  let mapPanX = 0;
  let mapPanY = 0;
  let mapPointerMoved = false;
  let mapBuildingAreas = new Map();
  let mapScanning = false;
  let dailyRumorRoute = [];
  let dailyAccountAreaIndex = [];
  let dailyShopRows = [];
  let dailyRunning = false;
  let dailyAdController = null;
  let dailySnapshot = load().today?.snapshot || null;
  let dailySelection = {...{advertisement:true, rumors:true, recruits:false, cartels:false, investments:false}, ...(load().today?.selection || {})};
  let dailyPurchaseCounts = {...(load().today?.purchaseCounts || {})};
  let dailyStoreTab = String(load().today?.storeTab || 'regular');
  let sharedPitRows = [];
  let pitCatalogLoaded = false;
  let pitSubmitQueue = [];
  let pitSubmitTimer = null;
  let pitPowerTableOpen = true;
  let lastNetworkPitContext = null;
  const pitSubmittedThisSession = new Set();
  const initialMapResearchAttempted = new Set();
  let root, panel, statusLine, logBox, businessLists, planBox, presetSelect, fairTypes, fairLots, fairSlotRules, fairPresetSelect, shopCards, shopSummary, recipeCards, recipeSummary, recipeDatabaseBox, bureauCards, bureauSummary, mapIndexBox, mapDetailBox, dailyBox, clanBox, resourceBox;

  // Shared live player state. Full /player/me responses replace complete fields;
  // action responses merge entity rows so a one-hamster response cannot erase
  // the rest of the account. Server timestamps prevent an older concurrent
  // response from overwriting newer state.
  const HK_STATE_MERGE_ROWS = {
    currencies:['currency_id','id'], items:['item_id','id'], buildings:['id','building_id'], business_building:['id'], constructions:['id'],
    playerFactions:['id','faction_id'], playerHamsters:['hamster_id','id'], player_hamster_generals:['hamster_id','id'],
    player_counters:['id','counter_id']
  };
  const HK_STATE_REPLACE_ARRAYS = new Set(['shop_lot_limits','fair','hamsteresses','player_hamsteresses_skill_line','hamsteresses_quest_slots','favorite_building_slots','player_bosses','player_battle_pass_rewards','auth_methods','offers','triggers']);
  const HK_STATE_REPLACE_VALUES = new Set(['advertisement','areas','bonuses','boss_battle','clan','daily_rewards','gameArea','gamearea_recommendation','idler','pit','pit2','pit_generals','pit_pve','player_regional_bosses','quests','referals','rumors']);
  function hkMergeRowsByFields(existing,incoming,fields){
    if(!Array.isArray(incoming)) return Array.isArray(existing)?existing:[];
    const result=(Array.isArray(existing)?existing:[]).map(row=>row&&typeof row==='object'?{...row}:row), positions=new Map();
    for(let i=0;i<result.length;i++) for(const field of fields){const value=result[i]?.[field];if(value!==undefined&&value!==null){positions.set(`${field}:${value}`,i);break;}}
    for(const row of incoming){if(!row||typeof row!=='object')continue;let key='';for(const field of fields){const value=row[field];if(value!==undefined&&value!==null){key=`${field}:${value}`;break;}}if(!key)continue;if(positions.has(key)){const i=positions.get(key);result[i]={...result[i],...row};}else{positions.set(key,result.length);result.push({...row});}}
    return result;
  }
  const hkStateStore = (() => {
    let snapshot = null, updatedAt = 0, revision = 0, fieldTimestamps = Object.create(null);
    const listeners = new Set();
    const clone = value => { if(value==null)return value; try{return structuredClone(value);}catch(_){try{return JSON.parse(JSON.stringify(value));}catch(_){return value;}} };
    const notify = (reason='update',changed=new Set()) => { revision+=1;const event={reason,revision,updatedAt,snapshot,changed};for(const listener of [...listeners]){try{listener(event);}catch(_){}} };
    const applyOne = (state,data,full=false,changed=new Set()) => {
      if(!state||!data||typeof data!=='object') return changed;
      const rawTs=Number(data.timestamp||0), incomingTs=Math.max(0,Number.isFinite(rawTs)?(rawTs>0&&rawTs<1e12?rawTs*1000:rawTs):0);
      const canApply=key=>!incomingTs||!fieldTimestamps[key]||fieldTimestamps[key]<=incomingTs;
      const stamp=key=>{if(incomingTs)fieldTimestamps[key]=incomingTs;changed.add(key);};
      const replaceArray=(key,value)=>{if(!canApply(key)||!Array.isArray(value))return;state[key]=value.map(row=>row&&typeof row==='object'?{...row}:row);stamp(key);};
      const mergeRows=(key,value,fields)=>{if(!canApply(key)||!Array.isArray(value))return;state[key]=hkMergeRowsByFields(state[key],value,fields);stamp(key);};
      if(data.player&&typeof data.player==='object'&&canApply('player')){state.player=state.player&&typeof state.player==='object'?{...state.player,...data.player}:{...data.player};stamp('player');}
      for(const [key,fields] of Object.entries(HK_STATE_MERGE_ROWS)) if(Array.isArray(data[key])) full?replaceArray(key,data[key]):mergeRows(key,data[key],fields);
      for(const key of HK_STATE_REPLACE_ARRAYS) if(Array.isArray(data[key])) replaceArray(key,data[key]);
      if(data.building&&typeof data.building==='object') mergeRows('buildings',[data.building],['id','building_id']);
      for(const key of HK_STATE_REPLACE_VALUES) if(Object.prototype.hasOwnProperty.call(data,key)&&canApply(key)){state[key]=data[key];stamp(key);}
      if(full){
        for(const [key,value] of Object.entries(data)){
          if(key==='player'||key==='building'||key==='timestamp'||changed.has(key)||HK_STATE_MERGE_ROWS[key]||HK_STATE_REPLACE_ARRAYS.has(key)||HK_STATE_REPLACE_VALUES.has(key)||!canApply(key))continue;
          state[key]=value;stamp(key);
        }
      }
      if(incomingTs) state.timestamp=Math.max(Number(state.timestamp||0),incomingTs);
      return changed;
    };
    const candidates = value => [
      value,
      value?.player,
      value?.result,
      value?.result?.player,
      value?.data,
      value?.data?.player
    ].filter((row,index,rows)=>row&&typeof row==='object'&&rows.indexOf(row)===index);
    return {
      get snapshot(){return snapshot;}, get updatedAt(){return updatedAt;}, get revision(){return revision;},
      replace(value,reason='player/me'){
        if(!value||typeof value!=='object')return snapshot;
        const currentId=snapshot?.player?.id,incomingId=value?.player?.id;
        if(!snapshot||(currentId!=null&&incomingId!=null&&String(currentId)!==String(incomingId))){snapshot={};fieldTimestamps=Object.create(null);}
        const changed=new Set();
        applyOne(snapshot,value,true,changed);
        // Some game responses keep inventories/hamsters under player/data.player.
        // Flatten only known live-state fields; never copy nested scalar player
        // properties onto the root snapshot.
        for(const nested of [value?.player,value?.result?.player,value?.data?.player]) if(nested&&typeof nested==='object') {
          for(const [key,fields] of Object.entries(HK_STATE_MERGE_ROWS)) if(Array.isArray(nested[key])) { snapshot[key]=nested[key].map(row=>row&&typeof row==='object'?{...row}:row); changed.add(key); }
          for(const key of HK_STATE_REPLACE_ARRAYS) if(Array.isArray(nested[key])) { snapshot[key]=nested[key].map(row=>row&&typeof row==='object'?{...row}:row); changed.add(key); }
          applyOne(snapshot,nested,false,changed);
        }
        if(changed.size){updatedAt=Date.now();notify(reason,changed);}return snapshot;
      },
      merge(value,reason='partial'){
        if(!value||typeof value!=='object')return snapshot;
        if(!snapshot)snapshot={};const changed=new Set();for(const source of candidates(value))applyOne(snapshot,source,false,changed);if(changed.size){updatedAt=Date.now();notify(reason,changed);}return snapshot;
      },
      syncFromPlayerDocument(reason='legacy-sync'){if(playerDocument)this.replace(playerDocument,reason);return snapshot;},
      subscribe(listener){if(typeof listener!=='function')return()=>{};listeners.add(listener);return()=>listeners.delete(listener);},
      exportSummary(){return{revision,updatedAt,hasSnapshot:!!snapshot,playerId:playerIdentity(snapshot?.player||{}),fields:Object.keys(snapshot||{}).length};},
      clone
    };
  })();

  const hkRunner = (() => {
    const state = {status:'idle', title:'', step:'', done:0, total:0, startedAt:0, error:'', pausable:true, stoppable:true};
    let abortController = null;
    let pauseResolvers = [];
    const emit = () => renderRunnerState();
    const settlePaused = () => { const rows=pauseResolvers.splice(0); rows.forEach(resolve=>resolve()); };
    return {
      state,
      get signal(){ return abortController?.signal || null; },
      get running(){ return state.status === 'running' || state.status === 'paused' || state.status === 'stopping'; },
      start({title='', total=0, step='', pausable=true, stoppable=true}={}) {
        if (this.running) throw new Error(either('Уже выполняется другая задача','Another task is already running'));
        abortController = new AbortController();
        Object.assign(state,{status:'running',title:String(title||either('Выполнение','Execution')),step:String(step||''),done:0,total:Math.max(0,Number(total)||0),startedAt:Date.now(),error:'',pausable:!!pausable,stoppable:!!stoppable});
        recordDiagnostic('runner-start',{title:state.title,total:state.total}); emit(); return state;
      },
      setStep(step, done=state.done, total=state.total) { state.step=String(step||''); state.done=Math.max(0,Number(done)||0); state.total=Math.max(0,Number(total)||0); emit(); return state; },
      advance(step='') { state.done=Math.min(state.total||state.done+1,state.done+1); if(step)state.step=String(step); emit(); return state; },
      pause() { if(state.status!=='running'||!state.pausable)return false; state.status='paused'; recordDiagnostic('runner-pause',{title:state.title}); emit(); return true; },
      resume() { if(state.status!=='paused')return false; state.status='running'; settlePaused(); recordDiagnostic('runner-resume',{title:state.title}); emit(); return true; },
      async waitIfPaused() { while(state.status==='paused') await new Promise(resolve=>pauseResolvers.push(resolve)); if(abortController?.signal.aborted) throw new DOMException('Aborted','AbortError'); },
      stop(reason='user') { if(!this.running||!state.stoppable)return false; state.status='stopping'; abortController?.abort(reason); settlePaused(); recordDiagnostic('runner-stop',{title:state.title,reason}); emit(); return true; },
      finish(step='') { if(step)state.step=String(step); state.status='done'; if(state.total)state.done=state.total; recordDiagnostic('runner-finish',{title:state.title}); emit(); setTimeout(()=>{if(state.status==='done'){state.status='idle';emit();}},1800); },
      fail(error) { state.status='error'; state.error=String(error?.message||error||either('Ошибка','Error')); recordDiagnostic('runner-error',{title:state.title,error:state.error}); emit(); },
      reset() { abortController=null; settlePaused(); Object.assign(state,{status:'idle',title:'',step:'',done:0,total:0,startedAt:0,error:'',pausable:true,stoppable:true}); emit(); }
    };
  })();

  // Optional bridge back into the game's own React state. HK never depends on
  // this bridge for API actions: when the game changes its internal React
  // structure the helper keeps working and only the instant native UI refresh
  // is skipped. Mutations are batched and one native player refresh is issued
  // at safe boundaries instead of trying to edit React stores manually.
  const hkGameBridge = (() => {
    let player = null;
    let refreshTask = null;
    let refreshThis = null;
    let generalViewStore = null;
    let dirty = false;
    let timer = null;
    let flushing = false;
    let lastDiscoveryAt = 0;
    let lastFlushAt = 0;
    let discoveries = 0;
    let flushes = 0;
    let failures = 0;

    const ready = () => !!(player && typeof refreshTask === 'function');
    const clearTimer = () => { if (timer) { clearTimeout(timer); timer = null; } };
    const roots = () => {
      const found = [];
      try {
        for (const element of document.querySelectorAll('*')) {
          let keys = [];
          try { keys = Object.getOwnPropertyNames(element); } catch (_) {}
          for (const key of keys) {
            if (!key.startsWith('__reactContainer$') && !key.startsWith('__reactFiber$')) continue;
            let fiber = element[key];
            if (fiber?.current) fiber = fiber.current;
            if (fiber) found.push(fiber);
          }
        }
      } catch (_) {}
      return found;
    };
    const setPlayer = candidate => {
      if (!candidate || typeof candidate.update !== 'function') return false;
      let taskOwner = candidate.vip || null;
      let task = taskOwner?._task;
      if (typeof task !== 'function' && !candidate.vip && typeof candidate._updatePlayerInfo === 'function' && typeof candidate.deleteVipStatus === 'function') {
        try {
          candidate._updatePlayerInfo({vipEndingTime:Date.now()+3600000});
          const temporary = candidate.vip;
          const VipClass = temporary?.constructor;
          try { temporary?.clear?.(); } catch (_) {}
          try { candidate.deleteVipStatus(); } catch (_) {}
          if (typeof VipClass === 'function') {
            const detached = new VipClass(Date.now()+3600000);
            try { detached.clear?.(); } catch (_) {}
            if (typeof detached._task === 'function') { taskOwner = detached; task = detached._task; }
          }
        } catch (_) {
          try { if (candidate.vip) candidate.deleteVipStatus(); } catch (_) {}
        }
      }
      if (typeof task !== 'function') return false;
      player = candidate; refreshTask = task; refreshThis = taskOwner;
      return true;
    };
    const discover = (force = false) => {
      if (ready() && !force) return true;
      if (!force && Date.now() - lastDiscoveryAt < 2500) return false;
      lastDiscoveryAt = Date.now(); discoveries += 1;
      const stack = roots();
      const seen = new Set();
      let scanned = 0;
      while (stack.length && scanned < 25000) {
        const fiber = stack.pop();
        if (!fiber || seen.has(fiber)) continue;
        seen.add(fiber); scanned += 1;
        for (const value of [fiber.memoizedProps?.value, fiber.pendingProps?.value]) {
          try {
            if (value?.generalViewStore && typeof value.generalViewStore === 'object') generalViewStore = value.generalViewStore;
            if (setPlayer(value?.appStore?.player)) {
              recordDiagnostic('game-bridge-discovered',{scanned,discoveries});
              return true;
            }
          } catch (_) {}
        }
        if (fiber.child) stack.push(fiber.child);
        if (fiber.sibling) stack.push(fiber.sibling);
        if (fiber.alternate) stack.push(fiber.alternate);
      }
      return ready();
    };
    const refreshHamsterCollection = (beforeUnits, afterUnits) => {
      if (!Number.isFinite(beforeUnits) || !Number.isFinite(afterUnits) || beforeUnits === afterUnits) return;
      const collection = generalViewStore?.hamsterCollection;
      if (!collection || typeof collection.mount !== 'function' || !/\/hamsters(?:[/?#]|$)/i.test(String(location.href || ''))) return;
      try { collection.mount(false); } catch (_) {}
    };
    const flush = async (force = false) => {
      if (flushing) { while (flushing) await sleep(50); return !dirty; }
      if (!force && !dirty) return true;
      flushing = true;
      clearTimer();
      try {
        for (let attempt = 0; attempt < 2; attempt++) {
          if (!discover(attempt > 0)) { failures += 1; return false; }
          const current = player, task = refreshTask, taskThis = refreshThis;
          const originalUpdate = current?.update, originalDelete = current?.deleteVipStatus;
          if (typeof originalUpdate !== 'function' || typeof task !== 'function') { player=null; refreshTask=null; refreshThis=null; failures += 1; continue; }
          const updated = await new Promise(resolve => {
            let settled = false, timeout = null, wrapped = null;
            const settle = ok => {
              if (settled) return; settled = true;
              if (timeout) clearTimeout(timeout);
              try { if (current.update === wrapped) current.update = originalUpdate; } catch (_) {}
              try { if (typeof originalDelete === 'function') current.deleteVipStatus = originalDelete; } catch (_) {}
              resolve(ok);
            };
            try {
              wrapped = function(...args) {
                const before = Number(current?.hamsterCollection?.unitsCount);
                try { return originalUpdate.apply(this,args); }
                finally {
                  const after = Number(current?.hamsterCollection?.unitsCount);
                  refreshHamsterCollection(before,after);
                  settle(true);
                }
              };
              current.update = wrapped;
              if (typeof originalDelete === 'function') current.deleteVipStatus = () => {};
              let returned;
              try { returned = task.call(taskThis); }
              finally { try { if (typeof originalDelete === 'function') current.deleteVipStatus = originalDelete; } catch (_) {} }
              if (returned?.catch) returned.catch(() => settle(false));
              if (!settled) timeout = setTimeout(() => settle(false), 8000);
            } catch (_) { settle(false); }
          });
          if (updated) {
            dirty = false; lastFlushAt = Date.now(); flushes += 1;
            recordDiagnostic('game-bridge-flush',{attempt:attempt+1,flushes});
            return true;
          }
          failures += 1;
          player=null; refreshTask=null; refreshThis=null;
          await sleep(attempt ? 1800 : 700);
        }
        return false;
      } finally { flushing = false; }
    };
    const schedule = (delay = 180) => {
      if (!dirty) return;
      clearTimer();
      timer = setTimeout(() => { timer=null; if (dirty && !hkRunner.running) void flush(false); }, Math.max(0,Number(delay)||0));
    };
    const noteMutation = (path, method = 'POST') => {
      const verb = String(method || 'GET').toUpperCase();
      const route = String(path || '').split('?')[0];
      if (['GET','HEAD','OPTIONS'].includes(verb) || route === '/player/me' || route === '/rumors/search' || route === '/regional_boss/battle_state') return;
      dirty = true;
      recordDiagnostic('game-bridge-dirty',{path:route,method:verb});
      if (!hkRunner.running) schedule(180);
    };
    const summary = () => ({ready:ready(),dirty,flushing,lastDiscoveryAt,lastFlushAt,discoveries,flushes,failures,hasGeneralViewStore:!!generalViewStore});
    return {discover,flush,schedule,noteMutation,summary,get ready(){return ready();},get dirty(){return dirty;}};
  })();

  // Runner completion is the safest place to refresh the game's visible React
  // state after a batch. Individual requests only mark the bridge dirty.
  const hkRunnerFinishBase = hkRunner.finish.bind(hkRunner);
  hkRunner.finish = step => { hkRunnerFinishBase(step); if (hkGameBridge.dirty) void hkGameBridge.flush(true); };
  const hkRunnerFailBase = hkRunner.fail.bind(hkRunner);
  hkRunner.fail = error => { hkRunnerFailBase(error); if (hkGameBridge.dirty) hkGameBridge.schedule(250); };

  runtime.stateStore = hkStateStore;
  const HK_STAGE2_RUNNER_REV = 'stage2a-20260919-r1';
  // HK_PIT_LIVE_VERIFY_V1 pit-live-verify-20260920-r1
  // HK_BUSINESS_LIVE_VERIFY_V1 business-live-verify-20260920-r1
  // HK_FAIR_SHOP_LIVE_VERIFY_V1 fair-shop-live-verify-20260920-r1
  // HK_RECIPES_LIVE_VERIFY_V1 recipes-live-20260920-r1
  // HK_MUTATION_RETRY_LIVE_V1 mutation-retry-live-20260920-r1
  const HK_STAGE2B_RUNNER_REV = 'stage2b-20260919-r1';
  const HK_STAGE2_STATE_REV = 'stage2c-state-20260919-r1';
  const HK_STAGE2D_RUNNER_REV = 'stage2d-resource-business-20260919-r1';
  const HK_STAGE2E_RUNNER_REV = 'stage2e-maps-20260919-r1';
  const HK_STAGE2F_RUNNER_REV = 'stage2f-clan-20260919-r1';
  const HK_STAGE2G_RUMORS_REV = 'stage2g-rumors-20260919-r1';
  const HK_STAGE2H_WARS_REV = 'stage2h-wars-20260919-r1';
  const HK_STAGE2I_BUILDINGS_REV = 'stage2i-buildings-explore-20260919-r1';
  const HK_STAGE2J_BOSSES_REV = 'bosses-readonly-20260920-r1';
  const HK_REGULAR_FAIR_REV = 'regular-fair-ui-20260920-r1';
  const HK_AUTO_ROUTINES_REV = 'auto-routines-20260920-r1';
  // HK_BUREAU_RESOURCES_LIVE_V1 bureau-resources-live-20260920-r1
  runtime.runner = hkRunner;
  runtime.legacyRunnerStage = HK_STAGE2_RUNNER_REV;
  runtime.legacyRunnerStageB = HK_STAGE2B_RUNNER_REV;
  runtime.stateMigrationStage = HK_STAGE2_STATE_REV;
  runtime.resourceBusinessRunnerStage = HK_STAGE2D_RUNNER_REV;
  runtime.mapRunnerStage = HK_STAGE2E_RUNNER_REV;
  runtime.clanRunnerStage = HK_STAGE2F_RUNNER_REV;
  runtime.rumorsStage = HK_STAGE2G_RUMORS_REV;
  runtime.warsStage = HK_STAGE2H_WARS_REV;
  runtime.buildingsExploreStage = HK_STAGE2I_BUILDINGS_REV;
  runtime.bossesStage = HK_STAGE2J_BOSSES_REV;
  runtime.gameBridge = hkGameBridge;
  let clanSkillScanning = false;
  let clanSkillRefreshing = false;
  let resourceBuildings = [];
  let resourceBusy = false;
  let resourceRepeatCount = Math.max(1, Math.min(10, Math.trunc(Number(load().resourceRepeatCount || 1))));
  let resourceMaximumMode = false;
  let resourceSelectedKind = String(load().resourceSelectedKind || 'nut');
  const RESOURCE_BUILDING_TYPES = {
    nut:{marker:'cur_nut', eventMarker:'mf_evts_main_nut', generatorMarker:'resources_1', nameRu:'Ореховая', nameEn:'Nut Station', buildingRu:'Станция снабжения', buildingEn:'Supply Station'},
    build:{marker:'cur_build', eventMarker:'mf_evts_main_build', generatorMarker:'resources_2', nameRu:'Инструментовая', nameEn:'Tool Workshop', buildingRu:'Индустриальный узел', buildingEn:'Industrial Hub'},
    pit:{marker:'cur_pit_pass', eventMarker:'mf_evts_main_pittoken', generatorMarker:'resources_3', nameRu:'Жетоновая', nameEn:'Token Workshop', buildingRu:'Павильон спорта', buildingEn:'Sports Pavilion'}
  };
  if (!RESOURCE_BUILDING_TYPES[resourceSelectedKind]) resourceSelectedKind = 'nut';
  const RESOURCE_PROTECTED_COST_IDS = new Set(['cur_fame','cur_power','cur_daily_combat_hamsters']);

  // Growth module (HK 1.13): live state is loaded automatically when a Growth
  // tab opens and is refreshed again before a run. Opening a tab never spends
  // resources; mutations start only from an explicit Run action.
  const GROWTH_STATIC_API = 'https://cdn-prod-static-api.hwgame.cloud';
  const GROWTH_ACTION_SAFETY = 5000;
  const GROWTH_LOOTBOX_BATCH = 1000;
  const GROWTH_GENERAL_BALL_PREFIX = 'item_hball_hgen_';
  const GROWTH_HAMSTER_BASE_MAX_LEVEL = 150;
  const GROWTH_HAMSTER_BUDGET_ID = 'cur_cap';
  const GROWTH_GENERAL_BUDGET_ID = 'item_pit_token';
  const GROWTH_COPY_PRIORITY_DEFAULT = [[19,20],[18,20],[4,5],[11,12],[1,2],[7,8],[3,5],[17,20],[10,12],[2,5],[9,12],[6,8]];
  let growthState = null;
  let growthBusy = false;
  let growthMenuLoading = false;
  let growthLoadPromise = null;
  let growthItemsDocument = null;
  let growthHamstersStaticDocument = null;
  let growthShopDocument = null;
  let growthClientConfigDocument = null;
  let growthLastLoadedAt = 0;

  function log(message, type = '') {
    message = localizeMessage(message);
    const time = new Date().toLocaleTimeString(locale(), {hour:'2-digit', minute:'2-digit', second:'2-digit'});
    if (logBox) {
      const row = document.createElement('div');
      row.className = type ? `hk-log-${type}` : '';
      row.textContent = `[${time}] ${message}`;
      logBox.prepend(row);
      while (logBox.children.length > 80) logBox.lastElementChild.remove();
    }
    if (statusLine) statusLine.textContent = message;
  }

  function headersToObject(headers) {
    const result = {};
    try { new Headers(headers || {}).forEach((value, key) => result[key] = value); } catch (_) {}
    return result;
  }

  function captureAuthorization(url, headers) {
    if (!url) return false;
    const resolvedUrl = new URL(url, location.href);
    // The shared catalog has its own bearer token. Never let that request
    // replace the captured Hamster King API address and game authorization.
    if (resolvedUrl.origin === new URL(LICENSE_URL).origin) return false;
    const auth = Object.entries(headers || {}).find(([key]) => key.toLowerCase() === 'authorization');
    if (!auth?.[1]) return false;
    apiBase = resolvedUrl.origin;
    apiHeaders = {Authorization: auth[1], Accept: 'application/json, text/plain, */*', 'Content-Type': 'application/json'};
    authUpdatedAt = Date.now();
    return true;
  }

  function jwtPayload(token) {
    try {
      const encoded = String(token || '').replace(/^Bearer\s+/i,'').split('.')[1];
      if (!encoded) return null;
      const padded = encoded.replace(/-/g,'+').replace(/_/g,'/').padEnd(Math.ceil(encoded.length/4)*4,'=');
      return JSON.parse(atob(padded));
    } catch (_) { return null; }
  }

  function jwtExpiration(token) {
    return Number(jwtPayload(token)?.exp || 0) * 1000;
  }

  function gameBearerPlayerId(token) {
    const payload = jwtPayload(token) || {};
    return clean(payload.id ?? payload.player_id ?? payload.playerId ?? payload.user_id ?? payload.sub ?? '');
  }

  function sameGameJwt(currentToken, candidateToken) {
    const current = jwtPayload(currentToken);
    const candidate = jwtPayload(candidateToken);
    if (!current || !candidate) return false;
    const currentId = gameBearerPlayerId(currentToken);
    const candidateId = gameBearerPlayerId(candidateToken);
    if (currentId && candidateId) return currentId === candidateId;
    const stableClaims = ['sub','iss','aud'];
    let compared = 0;
    for (const claim of stableClaims) {
      if (current[claim] == null || candidate[claim] == null) continue;
      compared += 1;
      if (JSON.stringify(current[claim]) !== JSON.stringify(candidate[claim])) return false;
    }
    return compared > 0;
  }

  function currentGameBearer() {
    return String(apiHeaders.Authorization || '').replace(/^Bearer\s+/i,'').trim();
  }

  function refreshStoredGameAuthorization() {
    let newest = '', newestExpiration = 0;
    const pattern = /eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/g;
    const currentAuthorization = apiHeaders.Authorization || '';
    for (const storage of [sessionStorage, localStorage]) {
      try {
        for (let index = 0; index < storage.length; index += 1) {
          const raw = String(storage.getItem(storage.key(index)) || '');
          if (!raw || raw.length > 1_000_000) continue;
          for (const token of raw.match(pattern) || []) {
            if (currentAuthorization && !sameGameJwt(currentAuthorization, token)) continue;
            const expiration = jwtExpiration(token);
            if (expiration > newestExpiration && expiration > Date.now() + 5000) {
              newest = token; newestExpiration = expiration;
            }
          }
        }
      } catch (_) {}
    }
    if (!newest) return false;
    const authorization = `Bearer ${newest}`;
    if (apiHeaders.Authorization === authorization) return false;
    apiHeaders = {...apiHeaders, Authorization:authorization, Accept:'application/json, text/plain, */*', 'Content-Type':'application/json'};
    authUpdatedAt = Date.now();
    setHealth('auth', true, 'токен восстановлен из браузера');
    recordDiagnostic('auth-restored',{fingerprint:diagnosticFingerprint(newest), expiresAt:newestExpiration});
    return true;
  }

  function readNativeGameAuthParams() {
    try {
      const webApp = window.Telegram?.WebApp;
      const initData = String(webApp?.initData || '');
      if (webApp && webApp.platform && webApp.platform !== 'unknown' && initData) {
        return {authType:'MiniApp', authData:initData.replaceAll('&','%26'), platform:'TG', source:'telegram'};
      }
    } catch (_) {}
    try {
      const stored = JSON.parse(localStorage.getItem('auth-data') || 'null');
      const authType = clean(stored?.params?.auth_type);
      const authData = clean(stored?.params?.auth_data);
      const remembered = clean(localStorage.getItem('remember-me'));
      if (!authType || !authData || remembered !== authType) return null;
      return {authType, authData, platform:'WEB', source:'browser'};
    } catch (_) { return null; }
  }

  async function refreshGoogleAuthData(params) {
    if (String(params?.authType || '') !== 'Google') return params;
    const expiration = jwtExpiration(params.authData);
    if (expiration > Date.now() + GAME_AUTH_REFRESH_EARLY_MS) return params;
    const previous = String(params.authData || '');
    const prompt = window.google?.accounts?.id?.prompt;
    if (typeof prompt !== 'function') return null;
    try { prompt.call(window.google.accounts.id); } catch (_) { return null; }
    const deadline = Date.now() + 6500;
    while (Date.now() < deadline) {
      await sleep(250);
      const next = readNativeGameAuthParams();
      if (next?.authType !== 'Google' || !next.authData || next.authData === previous) continue;
      if (jwtExpiration(next.authData) > Date.now() + 5000) return next;
    }
    return null;
  }

  async function checkGameBearer(token) {
    if (!token) return false;
    const request = nativeNetworkFetch || window.fetch.bind(window);
    const base = apiBase || GAME_API_FALLBACK;
    try {
      const {response}=await gameFetchText(request,`${base}/auth/check`,{method:'POST',cache:'no-store',headers:{Authorization:`Bearer ${token}`,Accept:'application/json, text/plain, */*'}},12000);
      recordDiagnostic('auth-check',{status:response.status, ok:response.ok, fingerprint:diagnosticFingerprint(token)});
      return response.ok;
    } catch (error) {
      recordDiagnostic('auth-check-network-error',{error:error?.message || error});
      return false;
    }
  }

  async function createFreshGameAuthorization(reason = 'refresh', expectedToken = '') {
    if (authCreatePromise) return authCreatePromise;
    authCreatePromise = (async () => {
      let params = readNativeGameAuthParams();
      if (!params) { recordDiagnostic('auth-create-unavailable',{reason}); return ''; }
      if (params.authType === 'Google') {
        params = await refreshGoogleAuthData(params);
        if (!params) { recordDiagnostic('auth-google-refresh-unavailable',{reason}); return ''; }
      }
      const base = apiBase || GAME_API_FALLBACK;
      const url = new URL(`${base}/auth/create`);
      url.searchParams.set('auth_type', params.authType);
      url.searchParams.set('auth_data', params.authData);
      url.searchParams.set('platform', params.platform);
      recordDiagnostic('auth-create-start',{reason, authType:params.authType, platform:params.platform, source:params.source});
      const request = nativeNetworkFetch || window.fetch.bind(window);
      try {
        const {response,text}=await gameFetchText(request,url,{method:'POST',cache:'no-store',headers:{Accept:'application/json, text/plain, */*'}},15000);
        let data=null;try{data=JSON.parse(text);}catch(_){}
        const token = clean(data?.token);
        if (!response.ok || !token) { recordDiagnostic('auth-create-failed',{reason,status:response.status}); return ''; }
        if (expectedToken && !sameGameJwt(expectedToken, token)) {
          recordDiagnostic('auth-identity-mismatch',{reason, expectedPlayerId:gameBearerPlayerId(expectedToken), receivedPlayerId:gameBearerPlayerId(token)});
          setHealth('auth', false, 'сменился игровой аккаунт');
          return '';
        }
        const knownPlayerId = playerIdentity(playerDocument?.player || {});
        const receivedPlayerId = gameBearerPlayerId(token);
        if (knownPlayerId && receivedPlayerId && knownPlayerId !== receivedPlayerId) {
          recordDiagnostic('auth-player-mismatch',{reason, expectedPlayerId:knownPlayerId, receivedPlayerId});
          setHealth('auth', false, 'аккаунт не совпадает');
          return '';
        }
        try { sessionStorage.setItem('token', token); } catch (_) {}
        apiBase = base;
        apiHeaders = {...apiHeaders, Authorization:`Bearer ${token}`, Accept:'application/json, text/plain, */*', 'Content-Type':'application/json'};
        authUpdatedAt = Date.now();
        setHealth('auth', true, 'токен обновлён');
        recordDiagnostic('auth-create-success',{reason, fingerprint:diagnosticFingerprint(token), playerId:gameBearerPlayerId(token), expiresAt:jwtExpiration(token)});
        return token;
      } catch (error) {
        recordDiagnostic('auth-create-network-error',{reason,error:error?.message || error});
        return '';
      }
    })();
    try { return await authCreatePromise; } finally { authCreatePromise = null; }
  }

  async function ensureGameAuthorization(force = false, reason = 'runtime') {
    restoreGameApiBaseFromPerformance();
    if (!apiBase) apiBase = GAME_API_FALLBACK;
    refreshStoredGameAuthorization();
    let token = currentGameBearer();
    const expiresAt = jwtExpiration(token);
    if (!force && token && expiresAt > Date.now() + GAME_AUTH_REFRESH_EARLY_MS) {
      setHealth('auth', true, 'токен активен');
      return true;
    }
    if (token && !force && expiresAt > Date.now() + 5000) {
      const valid = await checkGameBearer(token);
      if (valid) { setHealth('auth', true, 'токен проверен'); return true; }
    }
    const fresh = await createFreshGameAuthorization(reason, token);
    token = fresh || currentGameBearer();
    const ok = !!token && jwtExpiration(token) > Date.now() + 5000;
    setHealth('auth', ok, ok ? 'авторизация активна' : 'нужен повторный вход');
    return ok;
  }

  function restoreGameApiBaseFromPerformance() {
    if (apiBase) return true;
    try {
      const entries = performance.getEntriesByType('resource').slice().reverse();
      const useful = new Set(['/player/me','/shop/view','/items','/business_items','/events','/client_config']);
      for (const entry of entries) {
        const url = new URL(String(entry?.name || ''), location.href);
        if (url.origin === new URL(LICENSE_URL).origin) continue;
        if (!useful.has(url.pathname) && !url.pathname.startsWith('/localization/')) continue;
        apiBase = url.origin;
        return true;
      }
    } catch (_) {}
    return false;
  }

  async function bootstrapLateGameConnection() {
    if (playerDocument && apiBase && apiHeaders.Authorization) { setHealth('game', true, 'игра подключена'); return true; }
    const authorized = await ensureGameAuthorization(false, 'late-bootstrap');
    if (!apiBase || !authorized) { setHealth('game', false, 'нет подключения к игре'); return false; }
    try {
      const documentValue = await apiJson('/player/me', 'POST', null, true, 2);
      acceptPlayerState(`${apiBase}/player/me`, apiHeaders, documentValue, false);
      setHealth('game', true, 'игра отвечает');
      return true;
    } catch (error) {
      recordDiagnostic('late-bootstrap-failed',{error:error?.message || error});
      setHealth('game', false, 'игра не отвечает');
      console.warn('[HK] late connection bootstrap failed', error);
      return false;
    }
  }

  function acceptPlayerState(url, headers, documentValue, partial = false) {
    if (!documentValue || typeof documentValue !== 'object') return;
    if (!captureAuthorization(url, headers)) return;
    // /player/me with `arguments` returns only the requested sections. Keep
    // the rest of the last full response (advertisement, currencies, pits,
    // etc.) instead of replacing it with that partial document.
    setHealth('game', true, 'данные игрока получены');
    setHealth('auth', true, 'игровая сессия активна');
    playerDocument = partial && playerDocument ? {
      ...playerDocument,
      ...documentValue,
      ...(playerDocument.player || documentValue.player ? {player:{...(playerDocument.player || {}), ...(documentValue.player || {})}} : {}),
      ...(playerDocument.data || documentValue.data ? {data:{...(playerDocument.data || {}), ...(documentValue.data || {})}} : {})
    } : documentValue;
    if (partial) hkStateStore.merge(documentValue, 'player/me-partial');
    else hkStateStore.replace(playerDocument, 'player/me');
    playerDocument = hkStateStore.snapshot || playerDocument;
    refreshBusinessData();
    const player = playerDocument.player || {};
    log(`Подключено${player.nickname ? `: ${player.nickname}` : ''}`);
    // Checking access is required to unlock the panel. This does not scan
    // districts or submit any map data; those actions remain manual.
    checkLicense(player);
    // Never scan or upload map areas automatically. The player must explicitly
    // press "Считать карты аккаунта" in the Maps tab for that operation.
  }

  function getDeviceId() {
    const stored = load().deviceId;
    if (stored) return stored;
    const value = (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}_${Math.random()}_${Math.random()}`).replace(/[^A-Za-z0-9_-]/g, '');
    save({deviceId:value});
    return value;
  }

  function playerIdentity(player) {
    return clean(player?.id ?? player?.player_id ?? player?.uuid ?? player?.nickname ?? '');
  }

  function licenseReason(code) {
    return ({not_allowed:'ID не добавлен владельцем', blocked:'Лицензия заблокирована', expired:'Срок лицензии истёк',
      device_limit:'Достигнут лимит устройств', origin_not_allowed:'Домен игры не разрешён', invalid_identity:'Не удалось определить аккаунт',
      update_required:'Требуется обязательное обновление'}[code] || code || 'Проверка не пройдена');
  }

  function updateLicenseUI() {
    setHealth('license', !!licenseState.allowed, licenseState.allowed ? 'доступ разрешён' : (licenseState.checked ? licenseState.reason : 'ожидание'));
    if (!panel) return;
    const gate = root.querySelector('#hk-license-gate');
    const updateBox = root.querySelector('#hk-update-banner');
    const update = licenseState.update;
    if (updateBox && update?.available && update?.download_url) {
      const latest=escapeHtml(update.latest_version || '?');
      updateBox.style.display='block';
      updateBox.className=`hk-update${update.required ? ' required' : ''}`;
      updateBox.innerHTML=`<b>${either('Доступно обновление','Update available')} ${latest}</b>${update.notes ? `<small>${escapeHtml(update.notes).replace(/\n/g,'<br>')}</small>` : ''}${update.sha256 ? `<small>SHA-256: ${escapeHtml(String(update.sha256).slice(0,16))}…</small>` : ''}<button id="hk-install-update" class="hk-primary">${either('Установить обновление','Install update')}</button>`;
      updateBox.querySelector('#hk-install-update').onclick=()=>{
        const notes=clean(update.notes || '');
        const heading=either(`Изменения версии ${latest}:`,`Changes in version ${latest}:`);
        const instruction=either('После открытия файла нажмите значок расширений Safari возле адресной строки → Userscripts → Install/Update.',
          'After the file opens, tap the Safari extensions icon beside the address bar → Userscripts → Install/Update.');
        alert(`${heading}${notes ? `\n\n${notes}` : ''}\n\n${instruction}`);
        window.open(String(update.download_url),'_blank','noopener');
      };
    } else if (updateBox) {
      updateBox.style.display='none'; updateBox.innerHTML='';
    }
    if (licenseState.allowed) {
      panel.classList.remove('hk-locked');
      if (gate) { gate.className = 'hk-license ok'; gate.textContent = `${localizeMessage('Доступ разрешён')} · ID: ${licenseState.playerId}`; }
    } else {
      panel.classList.add('hk-locked');
      if (gate) { gate.className = `hk-license ${licenseState.checked ? 'bad' : ''}`; gate.innerHTML = `${escapeHtml(localizeMessage(licenseState.reason))}${licenseState.playerId ? `<br><b>ID: ${escapeHtml(licenseState.playerId)}</b><br><small>${escapeHtml(localizeMessage('Добавьте этот ID в панели владельца'))}</small>` : ''}`; }
      pitRunning = false; fairStop = true;
    }
    updateWatermark();
  }

  function watermarkCode() {
    const stored = clean(load().watermarkCode);
    if (/^[A-Z0-9]{6}$/.test(stored)) return stored;
    const alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    const bytes = new Uint8Array(6); crypto.getRandomValues(bytes);
    const code = [...bytes].map(value => alphabet[value % alphabet.length]).join('');
    save({watermarkCode:code});
    return code;
  }

  function updateWatermark() {
    const layer = root?.querySelector('#hk-watermark');
    if (!layer) return;
    const playerId = clean(licenseState.playerId || playerIdentity(playerDocument?.player || {})) || 'NO-ID';
    const stamp = new Date().toLocaleString(locale(), {day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'});
    const label = `HK · ID ${playerId} · ${stamp} · ${watermarkCode()}`;
    layer.innerHTML = Array.from({length:12}, () => `<span>${escapeHtml(label)}</span>`).join('');
    const phase = Math.floor(Date.now() / 30000) % 4;
    layer.style.transform = `translate(${phase * 7 - 10}px,${(phase % 3) * 9 - 8}px)`;
  }

  async function checkLicense(player, force = false) {
    const playerId = playerIdentity(player);
    if (!playerId) {
      licenseState = {checked:true, allowed:false, playerId:'', reason:'Не удалось определить ID игрового аккаунта'};
      setHealth('license', false, 'не найден ID');
      updateLicenseUI(); return false;
    }
    if (!force && licenseState.allowed && licenseState.playerId === playerId && Date.now() - lastLicenseCheck < LICENSE_RECHECK_MS) return true;
    if (licenseCheckPromise) return licenseCheckPromise;
    const backgroundCheck = licenseState.allowed && licenseState.playerId === playerId;
    if (!backgroundCheck) {
      licenseState = {checked:false, allowed:false, playerId, reason:'Проверяю лицензию…'};
      updateLicenseUI();
    }
    licenseCheckPromise = (async () => {
      let lastError = null;
      for (let attempt = 0; attempt <= SERVER_REQUEST_RETRY_DELAYS_MS.length; attempt += 1) {
        try {
          const response = await new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', LICENSE_URL, true);
            xhr.timeout = 12000;
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onload = () => {
              let body = {}; try { body = JSON.parse(xhr.responseText || '{}'); } catch (_) {}
              resolve({ok:xhr.status >= 200 && xhr.status < 300, status:xhr.status, body});
            };
            xhr.onerror = () => reject(new Error('network_error'));
            xhr.ontimeout = () => reject(new Error('timeout'));
            xhr.send(JSON.stringify({player_id:playerId, device_id:getDeviceId(), script_version:VERSION}));
          });
          recordDiagnostic('license-check',{status:response.status,attempt:attempt+1,allowed:!!response.body?.allowed,playerId});
          const transient = response.status === 408 || response.status === 425 || response.status === 429 || response.status >= 500;
          if (transient && attempt < SERVER_REQUEST_RETRY_DELAYS_MS.length) {
            await sleep(SERVER_REQUEST_RETRY_DELAYS_MS[attempt]); continue;
          }
          const body = response.body || {};
          licenseState = response.ok && body.allowed
            ? {checked:true, allowed:true, playerId, reason:'Доступ разрешён', token:String(body.token || ''), update:body.update || null}
            : {checked:true, allowed:false, playerId, reason:licenseReason(body.reason || `HTTP ${response.status}`), update:body.update || null};
          lastLicenseCheck = Date.now();
          setHealth('server', response.ok, response.ok ? 'сервер отвечает' : `HTTP ${response.status}`);
          setHealth('license', licenseState.allowed, licenseState.allowed ? 'доступ разрешён' : licenseState.reason);
          lastError = null;
          break;
        } catch (error) {
          lastError = error;
          recordDiagnostic('license-network-error',{attempt:attempt+1,error:error?.message || error});
          if (attempt < SERVER_REQUEST_RETRY_DELAYS_MS.length) { await sleep(SERVER_REQUEST_RETRY_DELAYS_MS[attempt]); continue; }
        }
      }
      if (lastError) {
        licenseState = {checked:true, allowed:false, playerId, reason:'Сервер лицензий недоступен'};
        setHealth('server', false, 'сервер недоступен');
        setHealth('license', false, 'не удалось проверить');
      }
      licenseCheckPromise = null; updateLicenseUI();
      if (licenseState.allowed) setTimeout(() => {
        synchronizeSettings(); flushPitObservations(); loadSharedPitPowers(); refreshSharedClanSkills(); maybeAutoScanClanSkills(); collectPublicSnapshot();
      }, 0);
      return licenseState.allowed;
    })();
    return licenseCheckPromise;
  }

  function requireLicense() {
    if (licenseState.allowed) return true;
    alert(`${localizeMessage(licenseState.reason)}${licenseState.playerId ? `\n\nID: ${licenseState.playerId}` : ''}`);
    return false;
  }

  function acceptShopView(url, headers, documentValue) {
    if (!documentValue || typeof documentValue !== 'object' || !Array.isArray(documentValue.shop_lots)) return;
    shopViewDocument = documentValue;
    captureAuthorization(url, headers);
  }

  function acceptStaticDocument(url, headers, documentValue) {
    if (!documentValue || typeof documentValue !== 'object') return;
    const path = new URL(url, location.href).pathname;
    captureAuthorization(url, headers);
    if (path === '/items' && Array.isArray(documentValue)) itemCatalogDocument = documentValue;
    else if (path === '/business_items' && Array.isArray(documentValue.businesses)) businessCatalogDocument = documentValue.businesses;
    else if (path === '/bonuses/view' && Array.isArray(documentValue)) bonusCatalogDocument = documentValue;
    else if (path === '/events') eventCatalogDocument = normalizeEventCatalog(documentValue);
    else if (path === '/client_config') clientConfigDocument = documentValue;
    else if (path === '/premium') premiumDocument = documentValue;
    else if (path.startsWith('/localization/')) localizationDocument = documentValue;
  }

  const CRYSTAL_ROOM_MARKER = 'item_fake_prematmaxeventlvl';

  function containsCrystalMarker(value, seen = new Set()) {
    if (typeof value === 'string') return value === CRYSTAL_ROOM_MARKER;
    if (!value || typeof value !== 'object' || seen.has(value)) return false;
    seen.add(value);
    if (Array.isArray(value)) return value.some(item=>containsCrystalMarker(item,seen));
    return Object.values(value).some(item=>containsCrystalMarker(item,seen));
  }

  function normalizeEventCatalog(value) {
    if (Array.isArray(value)) return value;
    for (const key of ['events','items','data','rows']) if (Array.isArray(value?.[key])) return value[key];
    return [];
  }

  function crystalEventIds() {
    return new Set(normalizeEventCatalog(eventCatalogDocument).filter(row=>containsCrystalMarker(row))
      .flatMap(row=>[row?.event?.id,row?.event_id,row?.eventId,row?.id,row?.config?.id])
      .filter(value=>value != null && value !== '').map(String));
  }

  function roomEventIds(room) {
    const result=[]; const add=value=>{ if (value != null && value !== '') result.push(String(value)); };
    add(room?.event_id); add(room?.eventId); add(room?.core_event_id); add(room?.coreEventId);
    const eventObjects=[room?.event,room?.core_event,room?.coreEvent,
      ...(room?.side_events || []),...(room?.sideEvents || [])].filter(Boolean);
    eventObjects.forEach(value=>{ add(value?.event_id); add(value?.eventId); add(value?.id); add(value?.event?.id); });
    return result;
  }

  function roomContainsCrystal(room, ids) {
    return containsCrystalMarker(room) || roomEventIds(room).some(id=>ids.has(id));
  }

  const buildingStudyCache = new Map();

  function buildingRooms(documentValue) {
    const building=documentValue?.building || documentValue?.data?.building || documentValue?.data || documentValue;
    for (const value of [building?.events,building?.rooms,building?.event_rooms,building?.building_events,
      documentValue?.events,documentValue?.rooms,documentValue?.event_rooms]) if (Array.isArray(value)) return value;
    return [];
  }

  function directCrystalRoomCount(documentValue) {
    const building=documentValue?.building || documentValue?.data?.building || documentValue?.data || documentValue;
    for (const value of [building?.crystals,building?.crystal_rooms,building?.crystalRooms,
      documentValue?.crystals,documentValue?.crystal_rooms,documentValue?.crystalRooms]) {
      if (value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value))) return Math.max(0,Math.trunc(Number(value)));
    }
    return null;
  }

  function crystalRoomCount(documentValue, ids = crystalEventIds()) {
    const direct=directCrystalRoomCount(documentValue);
    if (direct != null) return direct;
    const rooms=buildingRooms(documentValue);
    return rooms.length ? rooms.filter(room=>roomContainsCrystal(room,ids)).length : null;
  }

  function exactResourceBuildingData(documentValue, expectedKind = '', trustedCompleted = false) {
    const building=documentValue?.building || documentValue?.data?.building || documentValue?.data || documentValue;
    if (!building || typeof building !== 'object') return null;
    try {
      const serialized=JSON.stringify(building);
      const match=expectedKind
        ? [[expectedKind,RESOURCE_BUILDING_TYPES[expectedKind]]].find(([,definition])=>definition && serialized.includes(definition.eventMarker))
        : Object.entries(RESOURCE_BUILDING_TYPES).find(([,definition])=>serialized.includes(definition.eventMarker));
      if (match) return {kind:match[0],definition:match[1],building};
      const trustedDefinition=expectedKind && trustedCompleted ? RESOURCE_BUILDING_TYPES[expectedKind] : null;
      return trustedDefinition && serialized.includes(`"${trustedDefinition.marker}"`)
        ? {kind:expectedKind,definition:trustedDefinition,building,completedMainEvent:true}
        : null;
    } catch (_) { return null; }
  }

  function exactResourceBuildingDefinition(row, expectedKind) {
    const definition=RESOURCE_BUILDING_TYPES[expectedKind];
    const generator=String(row?.meta?.building_generator || row?.building_generator || '').toLowerCase();
    return !!(definition?.generatorMarker && generator.includes(definition.generatorMarker));
  }

  function savedResourceBuildingIds() {
    const stored=load().resourceBuildingIds;
    const result=stored && typeof stored === 'object' ? {...stored} : {};
    if (!result.nut && load().resourceNutBuildingId) result.nut=String(load().resourceNutBuildingId);
    return result;
  }

  function savedResourceBuildingProofs() {
    const stored=load().resourceBuildingProofs;
    return stored && typeof stored === 'object' ? {...stored} : {};
  }

  function savedResourceTiers() {
    const stored=load().resourceSelectedTiers;
    const result=stored && typeof stored === 'object' ? {...stored} : {};
    if (result.nut == null && Number.isSafeInteger(Number(load().resourceSelectedTier))) result.nut=Number(load().resourceSelectedTier);
    return result;
  }

  function resourceTypeName(kind, building = false) {
    const definition=RESOURCE_BUILDING_TYPES[kind] || RESOURCE_BUILDING_TYPES.nut;
    return either(building ? definition.buildingRu : definition.nameRu, building ? definition.buildingEn : definition.nameEn);
  }

  async function discoverResourceBuildingIds(showLog = false, wantedKind = resourceSelectedKind) {
    const ids=savedResourceBuildingIds();
    const proofs=savedResourceBuildingProofs();
    const kinds=RESOURCE_BUILDING_TYPES[wantedKind] ? [wantedKind] : Object.keys(RESOURCE_BUILDING_TYPES);
    const missing=()=>kinds.filter(kind=>!ids[kind]);
    if (!missing().length) return ids;
    const currentArea=String(playerDocument?.gameArea?.gamearea_id || playerDocument?.game_area?.gamearea_id || '');
    const areaIds=[currentArea, ...(playerDocument?.areas?.areas || []).map(row=>String(row?.gamearea_id || row?.area_id || ''))]
      .filter((value,index,rows)=>value && rows.indexOf(value)===index);
    for (let index=0; index<areaIds.length && missing().length; index++) {
      if (showLog && (index===0 || index%10===9)) log(either(`Ищу ресурсные здания: район ${index+1}/${areaIds.length}…`,`Searching resource buildings: district ${index+1}/${areaIds.length}…`));
      let definitions=[];
      try { definitions=await apiJson(`/game_area/${encodeURIComponent(areaIds[index])}/buildings`,'GET'); }
      catch (_) { continue; }
      const candidates=(Array.isArray(definitions) ? definitions : [])
        .filter(row=>missing().includes(String(row?.meta?.resource || '').toLowerCase()))
        .sort((left,right)=>Number(exactResourceBuildingDefinition(right,String(right?.meta?.resource || '').toLowerCase()))-Number(exactResourceBuildingDefinition(left,String(left?.meta?.resource || '').toLowerCase())));
      for (const row of candidates) {
        const kind=String(row?.meta?.resource || '').toLowerCase();
        // `row.id` is the catalog/template id on some game responses. Only
        // `building_id` identifies the building owned by this player.
        const buildingId=String(row?.building_id || '');
        if (!RESOURCE_BUILDING_TYPES[kind] || !buildingId || ids[kind]) continue;
        mapBuildingAreas.set(buildingId,areaIds[index]);
        // Several unrelated buildings may generate the same resource. Confirm
        // the building by its own main event or its exact resource generator.
        try {
          const documentValue=await apiJson(`/player/building?building_id=${encodeURIComponent(buildingId)}`, 'POST');
          const exactGenerator=exactResourceBuildingDefinition(row,kind);
          if (exactResourceBuildingData(documentValue,kind,exactGenerator)) {
            ids[kind]=buildingId;
            proofs[kind]=buildingId;
          }
        } catch (_) {}
      }
    }
    save({resourceBuildingIds:ids,resourceBuildingProofs:proofs, ...(ids.nut?{resourceNutBuildingId:ids.nut}:{})});
    return ids;
  }

  function accountBuildingRows() {
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

  async function acceptBuildingStudy(url, headers, documentValue) {
    captureAuthorization(url,headers); const building=documentValue?.building || documentValue?.data?.building || documentValue?.data || documentValue;
    const buildingId=String(building?.id || building?.building_id || new URL(url,location.href).searchParams.get('building_id') || '');
    const resourceBuilding=buildingId && exactResourceBuildingData(documentValue);
    if (resourceBuilding && licenseState.allowed) {
      const {kind,building:buildingData}=resourceBuilding;
      const ids=savedResourceBuildingIds();
      const storedId=String(ids[kind] || '');
      const proofs=savedResourceBuildingProofs();
      if (storedId !== buildingId || String(proofs[kind] || '') !== buildingId) {
        ids[kind]=buildingId;
        proofs[kind]=buildingId;
        save({resourceBuildingIds:ids,resourceBuildingProofs:proofs, ...(kind==='nut'?{resourceNutBuildingId:buildingId}:{})});
        if (storedId !== buildingId) log(either(`Здание «${resourceTypeName(kind,true)}» запомнено`,`${resourceTypeName(kind,true)} remembered`),'ok');
      }
      const selectedTier=Number(buildingData?.chosen_tier ?? buildingData?.tier ?? 0);
      const maximumTier=Math.max(selectedTier,Number(buildingData?.tier ?? selectedTier));
      const tiers=savedResourceTiers(); tiers[kind]=selectedTier;
      resourceSelectedKind=kind;
      resourceBuildings=[{id:buildingId,kind,areaId:'',tier:selectedTier,maxTier:maximumTier,name:resourceTypeName(kind),buildingName:resourceTypeName(kind,true),document:documentValue}];
      save({resourceSelectedKind:kind,resourceSelectedTiers:tiers, ...(kind==='nut'?{resourceSelectedTier:selectedTier}:{})});
      renderResources();
    }
    const areaId=mapBuildingAreas.get(buildingId); if (!areaId || !licenseState.allowed) return;
    if (!eventCatalogDocument) { try { eventCatalogDocument=normalizeEventCatalog(await apiJson('/events','GET')); } catch (_) { return; } }
    const rooms=buildingRooms(documentValue); const roomCount=crystalRoomCount(documentValue);
    if (roomCount == null) return;
    const area=(playerDocument?.areas?.areas || []).find(row=>String(row?.gamearea_id)===areaId); if(!area)return;
    const hasEvents=rooms.length>0 || roomCount>0;
    if (String(mapDetail?.area?.area_id || '') === areaId) {
      const localRow=(mapDetail.buildings || []).find(row=>String(row?.building_id)===buildingId);
      if (localRow) { localRow.opened=true; localRow.room_count=roomCount; localRow.has_events=hasEvents; renderMapDetail(); }
    }
    mapServerJson('/submit',{area:{area_id:areaId,city_id:String(area.city_id||''),expected_buildings:0,buildings:[{building_id:buildingId,opened:true,room_count:roomCount,has_events:hasEvents}]}}).catch(()=>{});
  }

  const PIT_API_PATH_TYPES = new Map([
    ['/pit/view','normal'], ['/player/pit/start','normal'], ['/player/pit/battle','normal'], ['/player/pit/finish','normal'], ['/player/pit/pass','normal'], ['/player/pit/respawn','normal'], ['/pit/preview','normal'],
    ['/boss_pit/view','boss'], ['/player/boss_pit/start','boss'], ['/player/boss_pit/battle','boss'], ['/player/boss_pit/finish','boss'], ['/player/boss_pit/pass','boss'], ['/player/boss_pit/respawn','boss'], ['/pit_2/preview','boss'],
    ['/pit_pve/view','gang'], ['/player/pit_pve/start','gang'], ['/player/pit_pve/battle','gang'], ['/player/pit_pve/finish','gang'], ['/player/pit_pve/pass','gang'], ['/player/pit_pve/respawn','gang'], ['/pit_pve/preview','gang'], ['/player/pit_pve_battle_info','gang']
  ]);
  // Pit rounds currently end at 200. Keeping this boundary in one place also
  // prevents an unrelated nested `level` field from being mistaken for a Pit
  // round while walking a large /player/me response.
  const PIT_MAX_LEVEL = 200;

  function pitApiType(path) { return PIT_API_PATH_TYPES.get(String(path || '')) || null; }

  function pitStoreDocument() {
    const stored = load();
    const next = {normal:{}, boss:{}, gang:{}, ...(stored.pitPowersV2 || {})};
    if (!Object.keys(next.normal || {}).length && stored.pitPowers && typeof stored.pitPowers === 'object') {
      next.normal = Object.fromEntries(Object.entries(stored.pitPowers).map(([level, enemyPower]) => [level, {enemyPower:Number(enemyPower), samples:1, lastSeen:0}]));
    }
    for (const pitType of ['normal','boss','gang']) {
      next[pitType] = Object.fromEntries(Object.entries(next[pitType] || {}).filter(([level,value]) => {
        const numericLevel = Number(level), enemyPower = Number(value?.enemyPower);
        return Number.isSafeInteger(numericLevel) && numericLevel >= 1 && numericLevel <= PIT_MAX_LEVEL && Number.isFinite(enemyPower) && enemyPower > 0;
      }));
    }
    return next;
  }

  function writePitStore(documentValue) {
    const stored = load();
    localStorage.setItem(STORE, JSON.stringify({...stored, pitPowersV2:documentValue}));
  }

  function normalizePitChance(value) {
    const result = number(value);
    if (result === null) return null;
    const normalized = result > 1 && result <= 100 ? result / 100 : result;
    return normalized >= 0 && normalized <= 1 ? normalized : null;
  }

  function pitAtLeastWins(chances, needed) {
    let distribution = [1];
    for (const chance of chances) {
      const next = Array(distribution.length + 1).fill(0);
      distribution.forEach((value, wins) => { next[wins] += value * (1 - chance); next[wins + 1] += value * chance; });
      distribution = next;
    }
    return distribution.slice(needed).reduce((sum,value)=>sum+value,0);
  }

  function rememberPitObservation(pitType, raw) {
    const level = Number(raw?.level), enemyPower = Math.round(Number(raw?.enemyPower || 0));
    if (!['normal','boss','gang'].includes(pitType) || !Number.isSafeInteger(level) || level < 1 || level > PIT_MAX_LEVEL || !Number.isSafeInteger(enemyPower) || enemyPower < 1) return;
    const playerPower = Math.max(0, Math.round(Number(raw?.playerPower || 0))) || null;
    const supportPower = Math.max(0, Math.round(Number(raw?.supportPower || 0))) || 0;
    const winrate = normalizePitChance(raw?.winrate);
    const roundEnemyPowers = Array.isArray(raw?.roundEnemyPowers) ? raw.roundEnemyPowers.map(Number).slice(0,8) : [];
    const roundChances = Array.isArray(raw?.roundChances) ? raw.roundChances.map(normalizePitChance).slice(0,8) : [];
    const documentValue = pitStoreDocument();
    const previous = documentValue[pitType]?.[level] || {};
    documentValue[pitType] = {...(documentValue[pitType] || {}), [level]:{
      enemyPower, playerPower:playerPower || previous.playerPower || null,
      winrate:winrate ?? previous.winrate ?? null, samples:Number(previous.samples || 0) + 1,
      lastSeen:Date.now(), source:raw?.source || previous.source || 'legacy'
    }};
    writePitStore(documentValue);
    // Boss Pit uses the sum of every combat cartel. Normal Pit only needs the
    // single strongest cartel and Gang Pit uses eight separate battles.
    const factionLimit = pitType === 'boss' ? 64 : pitType === 'gang' ? 8 : 1;
    const factionPowers = Array.isArray(raw?.factionPowers) ? raw.factionPowers.map(Number).filter(value=>value>0).slice(0,factionLimit) : [];
    if (playerPower || factionPowers.length) {
      const stored = load();
      const previousProfile = stored.pitPlayerProfiles?.[pitType] || {};
      localStorage.setItem(STORE, JSON.stringify({...stored, pitPlayerProfiles:{...(stored.pitPlayerProfiles || {}), [pitType]:{
        playerPower:playerPower || previousProfile.playerPower || null,
        supportPower:supportPower || previousProfile.supportPower || 0,
        factionPowers:factionPowers.length ? factionPowers : (previousProfile.factionPowers || []),
        roundEnemyPowers:roundEnemyPowers.length === 8 ? roundEnemyPowers : (previousProfile.roundEnemyPowers || []),
        roundChances:roundChances.length === 8 ? roundChances : (previousProfile.roundChances || []),
        referenceEnemyPower:pitType !== 'gang' || roundEnemyPowers.length === 8 ? enemyPower : (previousProfile.referenceEnemyPower || enemyPower),
        level, winrate, updatedAt:Date.now()
      }}}));
    }
    const observation = {pit_type:pitType, level, enemy_power:enemyPower, player_power:playerPower, winrate};
    const key = [pitType, level, enemyPower, playerPower || '', winrate ?? ''].join(':');
    if (!pitSubmittedThisSession.has(key)) {
      pitSubmittedThisSession.add(key); pitSubmitQueue.push(observation); schedulePitSubmission();
    }
    if (root) renderPitForecast();
  }

  function schedulePitSubmission() {
    clearTimeout(pitSubmitTimer);
    pitSubmitTimer = setTimeout(flushPitObservations, 900);
  }

  async function flushPitObservations() {
    if (!pitSubmitQueue.length || !licenseState.allowed || !licenseState.token) return;
    const observations = pitSubmitQueue.splice(0, 80);
    try { await pitServerJson('/submit', {observations}); }
    catch (error) { pitSubmitQueue.unshift(...observations); console.warn('[HK] pit observation upload failed', error); }
  }

  function pitDisplayedLevel(rawLevel) {
    const value = number(rawLevel);
    const displayed = value !== null ? Math.trunc(value) + 1 : null;
    return Number.isSafeInteger(displayed) && displayed >= 1 && displayed <= PIT_MAX_LEVEL ? displayed : null;
  }

  function pitFactionPowers(value, pitType = 'normal') {
    // The game keeps the combat factions in player_factions. The similarly
    // named player_subfactions object is the support cartel and must not be
    // used as the four/eight combat powers.
    const source = value?.player_factions ?? value?.playerFactions;
    const rows = Array.isArray(source) ? source : (source && typeof source === 'object' ? Object.values(source) : []);
    const limit = pitType === 'boss' ? Number.POSITIVE_INFINITY : pitType === 'gang' ? 8 : 4;
    return rows.map(row => number(typeof row === 'number' ? row : row?.overall_power ?? row?.overallPower ?? row?.power ?? row?.value ?? row?.total_power ?? row?.totalPower)).filter(row=>row>0).sort((a,b)=>b-a).slice(0,limit);
  }

  function pitSupportPower(value) {
    const direct = number(
      value?.support_power ?? value?.supportPower ?? value?.player_support_power ?? value?.playerSupportPower ??
      value?.player_subfactions?.overall_power ?? value?.playerSubfactions?.overallPower ?? value?.support?.overall_power ?? value?.support?.overallPower ?? value?.support?.power
    );
    if (direct > 0) return direct;
    const source = value?.player_subfactions ?? value?.playerSubfactions ?? value?.support?.factions ?? value?.support?.rows;
    const rows = Array.isArray(source) ? source : (source && typeof source === 'object' ? Object.values(source) : []);
    return rows.map(row=>number(typeof row === 'number' ? row : row?.overall_power ?? row?.overallPower ?? row?.power ?? row?.value ?? row?.total_power ?? row?.totalPower))
      .filter(power=>power>0).reduce((sum,power)=>sum+power,0);
  }

  function pitCombinedPlayerPower(value) {
    const direct = number(
      value?.power ?? value?.player_power ?? value?.playerPower ?? value?.overall_power ?? value?.overallPower ??
      value?.total_power ?? value?.totalPower ?? value?.player_total_power ?? value?.playerTotalPower ?? value?.player?.power
    );
    if (direct > 0) return direct;
    const source = value?.player_factions ?? value?.playerFactions;
    const rows = Array.isArray(source) ? source : (source && typeof source === 'object' ? Object.values(source) : []);
    const factionTotal = rows.map(row => number(typeof row === 'number' ? row : row?.overall_power ?? row?.overallPower ?? row?.power ?? row?.total_power ?? row?.totalPower)).filter(row=>row>0).reduce((sum,row)=>sum+row,0);
    const calculated = factionTotal + pitSupportPower(value);
    return calculated > 0 ? calculated : null;
  }

  function acceptPitDocument(url, documentValue) {
    if (!documentValue || typeof documentValue !== 'object') return;
    const path = new URL(url || location.href, location.href).pathname;
    const runtime = {...(load().pitRuntimeLevels || {})};
    const visit = (pitType, value, inheritedLevel = null) => {
      if (!value || typeof value !== 'object') return;
      if (Array.isArray(value)) { value.forEach(row => visit(pitType, row, inheritedLevel)); return; }
      const rawLevel = number(value.level ?? value.round ?? value.pit_level);
      const level = rawLevel !== null ? pitDisplayedLevel(rawLevel) : inheritedLevel || runtime[pitType] || null;
      if (level) runtime[pitType] = level;
      const rounds = Array.isArray(value.rounds) ? value.rounds.filter(row => number(row?.enemy_power) > 0) : [];
      if (rounds.length) {
        const directEnemyPower = number(value.enemy_power ?? value.enemyPower);
        const roundEnemyPowers = rounds.map(row=>Number(row.enemy_power));
        // Gang rounds may contain one enemy boosted by faction efficiency.
        // The shared level value is the unboosted base power, not the average.
        const enemyPower = Math.round(pitType === 'gang'
          ? Math.min(...roundEnemyPowers)
          : directEnemyPower || roundEnemyPowers.reduce((sum,power)=>sum+power,0)/roundEnemyPowers.length);
        const powered = rounds.filter(row=>number(row.power)>0);
        const playerPower = powered.length ? Math.round(powered.reduce((sum,row)=>sum+Number(row.power),0)/powered.length) : pitCombinedPlayerPower(value);
        // PVE preview stores the eight combat powers directly in rounds.
        // Keep their original order for the gang probability calculation.
        const roundFactionPowers = pitType === 'gang' && powered.length >= 8 ? powered.slice(0,8).map(row=>Number(row.power)) : [];
        const roundChances = rounds.map(row=>normalizePitChance(row.winrate));
        const validChances = roundChances.filter(row=>row!==null);
        const winrate = normalizePitChance(value.winrate) ?? (validChances.length === rounds.length ? pitAtLeastWins(validChances, 5) : null);
        rememberPitObservation(pitType, {level, enemyPower, playerPower, winrate, supportPower:pitSupportPower(value), factionPowers:roundFactionPowers.length ? roundFactionPowers : pitFactionPowers(value,pitType), roundEnemyPowers, roundChances, source:'network'});
        return;
      }
      const enemyPower = number(value.enemy_power ?? value.enemyPower);
      if (enemyPower && level) rememberPitObservation(pitType, {level, enemyPower, playerPower:pitCombinedPlayerPower(value), winrate:value.winrate, supportPower:pitSupportPower(value), factionPowers:pitFactionPowers(value,pitType), source:'network'});
      Object.values(value).forEach(child => visit(pitType, child, level));
    };
    if (path === '/player/me') {
      const roots = [documentValue, documentValue.player, documentValue.data].filter(Boolean);
      for (const base of roots) {
        const context = {player_factions:base?.player_factions, player_subfactions:base?.player_subfactions};
        const normal = base?.pit, boss = base?.pit2 ?? base?.boss_pit, gang = base?.pit_pve;
        const normalLevel = pitDisplayedLevel(normal?.level ?? normal?.round ?? normal?.pit_level);
        const bossLevel = pitDisplayedLevel(boss?.level ?? boss?.round ?? boss?.pit_level);
        const gangLevel = pitDisplayedLevel(gang?.level ?? gang?.round ?? gang?.pit_level);
        visit('normal', normal && {...context,...normal});
        visit('normal', base?.pit_preview && {...context,...base.pit_preview}, normalLevel);
        visit('boss', boss && {...context,...boss});
        visit('boss', base?.pit2_preview && {...context,...base.pit2_preview}, bossLevel);
        visit('gang', gang && {...context,...gang});
        visit('gang', base?.pit_pve_preview && {...context,...base.pit_pve_preview}, gangLevel);
      }
    } else {
      const pitType = pitApiType(path);
      if (pitType) {
        lastNetworkPitContext = {pitType, at:Date.now()};
        const roots = [documentValue, documentValue.player, documentValue.data].filter(Boolean);
        const explicit = [];
        for (const base of roots) {
          const state = pitType === 'normal' ? base?.pit : pitType === 'boss' ? (base?.pit2 ?? base?.boss_pit) : base?.pit_pve;
          const preview = pitType === 'normal' ? base?.pit_preview : pitType === 'boss' ? base?.pit2_preview : base?.pit_pve_preview;
          const inheritedLevel = pitDisplayedLevel(state?.level ?? state?.round ?? state?.pit_level) || runtime[pitType] || null;
          const context = {player_factions:base?.player_factions, player_subfactions:base?.player_subfactions};
          if (state) explicit.push({value:{...context,...state}, level:null});
          if (preview) explicit.push({value:{...context,...preview}, level:inheritedLevel});
        }
        if (explicit.length) explicit.forEach(row => visit(pitType,row.value,row.level));
        else visit(pitType, documentValue);
      }
    }
    localStorage.setItem(STORE, JSON.stringify({...load(), pitRuntimeLevels:runtime}));
  }

  function isGameApiRequest(url){
    try{const target=new URL(String(url||''),location.href),origins=new Set([new URL(GAME_API_FALLBACK).origin]);if(apiBase)origins.add(new URL(apiBase).origin);return origins.has(target.origin);}catch(_){return false;}
  }
  function acceptSharedGameResponse(url,documentValue){
    if(!documentValue||typeof documentValue!=='object'||!isGameApiRequest(url))return;
    let path='';try{path=new URL(String(url||''),location.href).pathname;}catch(_){}
    if(path==='/player/me')return;
    const before=hkStateStore.revision,merged=hkStateStore.merge(documentValue,`game-ui:${path||'response'}`);
    if(hkStateStore.revision!==before&&merged){playerDocument=merged;try{refreshBusinessData();}catch(_){}}
  }

  function installNetworkCapture() {
    if (networkCaptureInstalled) return;
    if (typeof window.fetch !== 'function' || !window.XMLHttpRequest) throw new Error('Игровая сеть ещё не готова');
    const nativeFetch = window.fetch.bind(window);
    nativeNetworkFetch = nativeFetch;
    window.fetch = async function(input, init) {
      const url = typeof input === 'string' ? input : input?.url;
      const requestHeaders = {...headersToObject(input?.headers), ...headersToObject(init?.headers)};
      captureAuthorization(url, requestHeaders);
      const response = await nativeFetch(input, init);
      const path = url ? new URL(url, location.href).pathname : '';
      if (response.ok && isGameApiRequest(url)) hkGameBridge.noteMutation(path, init?.method || input?.method || 'GET');
      if(response.ok && isGameApiRequest(url) && path!=='/player/me') response.clone().json().then(body=>acceptSharedGameResponse(url,body)).catch(()=>{});
      if (path === '/player/me' && response.ok) {
        let partial = false;
        try { partial = Array.isArray(JSON.parse(String(init?.body || '{}'))?.arguments); } catch (_) {}
        response.clone().json().then(body => { acceptPlayerState(url, requestHeaders, body, partial); acceptPitDocument(url, body); }).catch(() => {});
      } else if (path === '/shop/view' && response.ok) {
        response.clone().json().then(body => acceptShopView(url, requestHeaders, body)).catch(() => {});
      } else if (['/items','/business_items','/bonuses/view','/events','/client_config'].includes(path) || path.startsWith('/localization/')) {
        if (response.ok) response.clone().json().then(body => acceptStaticDocument(url, requestHeaders, body)).catch(() => {});
      } else if (path === '/player/building' && response.ok) {
        response.clone().json().then(body => acceptBuildingStudy(url,requestHeaders,body)).catch(()=>{});
      } else if (pitApiType(path) && response.ok) {
        response.clone().json().then(body => acceptPitDocument(url,body)).catch(()=>{});
      }
      return response;
    };

    const open = XMLHttpRequest.prototype.open;
    const setHeader = XMLHttpRequest.prototype.setRequestHeader;
    const send = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function(method, url, ...rest) {
      this.__hkUrl = url; this.__hkMethod = method; this.__hkHeaders = {};
      return open.call(this, method, url, ...rest);
    };
    XMLHttpRequest.prototype.setRequestHeader = function(name, value) {
      if (this.__hkHeaders) this.__hkHeaders[name] = value;
      return setHeader.call(this, name, value);
    };
    XMLHttpRequest.prototype.send = function(...args) {
      if (this.__hkUrl) captureAuthorization(this.__hkUrl, this.__hkHeaders);
      if (this.__hkUrl && isGameApiRequest(this.__hkUrl)) {
        this.addEventListener('load', () => {
          if (this.status >= 200 && this.status < 300) {
            try {
              const path = new URL(this.__hkUrl, location.href).pathname;
              const body = JSON.parse(this.responseText);
              hkGameBridge.noteMutation(path, this.__hkMethod || 'GET');
              if(path!=='/player/me')acceptSharedGameResponse(this.__hkUrl,body);
               if (path === '/player/me') {
                 let partial = false;
                 try { partial = Array.isArray(JSON.parse(String(args[0] || '{}'))?.arguments); } catch (_) {}
                 acceptPlayerState(this.__hkUrl, this.__hkHeaders, body, partial); acceptPitDocument(this.__hkUrl,body);
               }
              else if (path === '/shop/view') acceptShopView(this.__hkUrl, this.__hkHeaders, body);
              else if (path === '/player/building') acceptBuildingStudy(this.__hkUrl,this.__hkHeaders,body);
              else if (pitApiType(path)) acceptPitDocument(this.__hkUrl,body);
              else acceptStaticDocument(this.__hkUrl, this.__hkHeaders, body);
            } catch (_) {}
          }
        });
      }
      return send.apply(this, args);
    };
    networkCaptureInstalled = true;
  }

  function pitState() {
    const text = document.body?.innerText || '';
    const roundText = clean(document.querySelector('.pit-page__round-name')?.innerText || '');
    const parseRound = value => {
      const match = String(value || '').match(/(?:Раунд|Round)\s*([\d\s.,]+)/i);
      let digits = (match?.[1] || '').replace(/\D/g, '');
      if (!digits) return null;
      // The mobile game draws the same number in two text layers. Safari can
      // expose "Раунд 135135" instead of "Раунд 135".
      if (digits.length % 2 === 0) {
        const half = digits.length / 2;
        if (digits.slice(0, half) === digits.slice(half)) digits = digits.slice(0, half);
      }
      const parsed = Number(digits);
      return Number.isSafeInteger(parsed) && parsed > 0 && parsed < 10000 ? parsed : null;
    };
    const parsedRound = parseRound(roundText) ?? parseRound(text);
    const controls = [...document.querySelectorAll('button,[role="button"],a')].filter(visible).map(e => clean(e.innerText)).filter(Boolean);
    const state = {
      round: parsedRound,
      roundText,
      controls,
      restoreModal: /Восстановление жизней|Restore lives/i.test(text),
      fastToggle: !![...document.querySelectorAll('button.event-offer__auto')].find(visible),
      enemyText: clean(document.querySelector('.pit-page__enemy')?.innerText || '')
    };
    capturePitLimitFromPage();
    return state;
  }

  const PIT_LIMIT_TYPES = [
    {id:'normal', textKey:'pitNormal', currencyId:'cur_pit_pass', currencyType:'pit-ticket', heading:/^(?:Хомячья Яма|Hamster Pit)$/i},
    {id:'boss', textKey:'pitBoss', currencyId:'cur_pit_2_pass', currencyType:'boss-pit-ticket', heading:/^(?:Яма Боссов|Boss Pit)$/i},
    {id:'gang', textKey:'pitGang', currencyId:'cur_pit_3_pass', currencyType:'pve-pit-ticket', heading:/^(?:Яма Банд|Gang Pit)$/i}
  ];
  const PIT_DAILY_API = {
    normal:{stateKeys:['pit'], start:'/player/pit/start', battle:'/player/pit/battle', finish:'/player/pit/finish'},
    boss:{stateKeys:['pit2','boss_pit'], start:'/player/boss_pit/start', battle:'/player/boss_pit/battle', finish:'/player/boss_pit/finish'},
    gang:{stateKeys:['pit_pve'], start:'/player/pit_pve/start', battle:'/player/pit_pve/battle', finish:'/player/pit_pve/finish'}
  };

  function persistPitLimits(limits) {
    const previous = load();
    localStorage.setItem(STORE, JSON.stringify({...previous, pitLimits:limits}));
  }

  function capturePitLimitFromPage() {
    const heading = clean(document.querySelector('h1')?.innerText || '');
    const type = PIT_LIMIT_TYPES.find(value => value.heading.test(heading));
    if (!type) return null;
    const counter = [...document.querySelectorAll('.value-bar__value span')]
      .map(element => clean(element.innerText || '')).find(value => /^\d+\s*\/\s*\d+$/.test(value));
    const match = String(counter || '').match(/^(\d+)\s*\/\s*(\d+)$/);
    if (!match) return null;
    const current = Number(match[1]), limit = Number(match[2]);
    if (!Number.isSafeInteger(current) || !Number.isSafeInteger(limit) || limit <= 0) return null;
    const limits = {...(load().pitLimits || {}), [type.id]:{current, limit, capturedAt:Date.now()}};
    const previous = load().pitLimits?.[type.id];
    if (!previous || previous.current !== current || previous.limit !== limit) persistPitLimits(limits);
    return limits[type.id];
  }

  function pitLimitFromPlayer(type, documentValue = playerDocument) {
    const lists = [documentValue?.currencies, documentValue?.player?.currencies, documentValue?.inventory?.currencies];
    for (const list of lists) {
      if (!Array.isArray(list)) continue;
      const value = list.find(row => String(row?.currency_id || row?.id || '') === type.currencyId ||
        String(row?.type || row?.currency_type || row?.currencyType || '') === type.currencyType);
      if (!value) continue;
      const current = number(value.value ?? value.quantity ?? value.current ?? value.amount);
      const limit = number(value.max_value ?? value.maxValue ?? value.limit ?? value.maximum);
      if (limit !== null && limit > 0) return {current:Math.max(0, current || 0), limit};
    }
    return null;
  }

  function pitLimitSummaries() {
    capturePitLimitFromPage();
    const cached = load().pitLimits || {};
    return PIT_LIMIT_TYPES.map(type => {
      const live = pitLimitFromPlayer(type);
      const value = live || cached[type.id] || null;
      // `current` is the number of moves that can actually be spent now.
      // It may be higher than maxValue after bonuses, so never clamp it to
      // the nominal limit shown after the slash.
      const walletCurrent = Math.max(0, Number(value?.current ?? value?.used ?? 0));
      // A race multiplier describes a separate already-started batch. Its
      // tickets have already been removed from the wallet and must not be
      // added back to the value labelled "available now". Finished races can
      // also remain in /player/me briefly, which previously displayed 55 when
      // the real wallet contained 50.
      const race = pitRaceState(type.id, playerDocument);
      const reserved = Math.max(0, Math.trunc(Number(race?.mass_multiplier ?? race?.massMultiplier ?? race?.multiplier ?? 0)));
      const current = pitUnavailableThisPeriod(type.id) ? 0 : walletCurrent;
      const limit = Math.max(0, Number(value?.limit || 0));
      const topUp = limit ? (5 - limit % 5) % 5 : null;
      return {...type, current, walletCurrent, reserved, limit, topUp};
    });
  }

  function pitMovePlan(amount) {
    let remaining = Math.max(0, Math.floor(Number(amount || 0)));
    const result = [];
    for (const size of [50, 20, 10, 5, 1]) {
      const count = Math.floor(remaining / size);
      if (count > 0) result.push({size, count});
      remaining %= size;
    }
    return result;
  }

  function pitMovePlanText(amount) {
    const parts = pitMovePlan(amount);
    if (!parts.length) return tr('pitNoMoves');
    return parts.map(part => part.count > 1 ? `${part.count} × ${part.size}` : `×${part.size}`).join(' + ');
  }

  function selectedPitMoves(typeId, maximum) {
    const today = load().today || {};
    const periodStart = gamePeriodBounds().dayStart;
    // A saved zero from yesterday must not hide tickets that appeared after
    // the daily reset. On the first read of a new period select every live
    // ticket; an explicit choice made during this period is preserved.
    if (Number(today.pitMovesPeriodStart || 0) !== periodStart ||
        !Object.prototype.hasOwnProperty.call(today.pitMoves || {}, typeId)) {
      return Math.max(0, Math.floor(Number(maximum || 0)));
    }
    const stored = Number(today.pitMoves?.[typeId] || 0);
    return Math.min(Math.max(0, Math.floor(stored)), Math.max(0, Math.floor(Number(maximum || 0))));
  }

  function pitMoveOptions(maximum, selected) {
    const max = Math.max(0, Math.floor(Number(maximum || 0)));
    return Array.from({length:max + 1}, (_, value) => `<option value="${value}" ${value === selected ? 'selected' : ''}>${value.toLocaleString(locale())}</option>`).join('');
  }

  function savePitMoves(typeId, value) {
    const today = load().today || {};
    const periodStart = gamePeriodBounds().dayStart;
    const periodMoves = Number(today.pitMovesPeriodStart || 0) === periodStart ? (today.pitMoves || {}) : {};
    save({today:{...today, pitMovesPeriodStart:periodStart,
      pitMoves:{...periodMoves, [typeId]:Math.max(0, Math.floor(Number(value || 0)))}}});
  }

  function pitUnavailableThisPeriod(typeId) {
    return Number(load().today?.pitUnavailable?.[typeId] || 0) === gamePeriodBounds().dayStart;
  }

  function markPitUnavailable(typeId) {
    const today = load().today || {};
    const periodStart = gamePeriodBounds().dayStart;
    const periodMoves = Number(today.pitMovesPeriodStart || 0) === periodStart ? (today.pitMoves || {}) : {};
    save({today:{...today, pitMovesPeriodStart:periodStart,
      pitMoves:{...periodMoves, [typeId]:0},
      pitUnavailable:{...(today.pitUnavailable || {}), [typeId]:periodStart}}});
  }

  function pitLimitsHtml() {
    return `<div class="hk-pit-limits">${pitLimitSummaries().map(row => {
      if (!row.limit) return `<div><b>${tr(row.textKey)}</b><small>${tr('pitOpenOnce')}</small></div>`;
      const selected = selectedPitMoves(row.id, row.current);
      const enabled = dailySelection[`pit:${row.id}`] !== false;
      const topUp = row.topUp
        ? `${tr('pitDiamondTopUp')}: <b>+${row.topUp}</b> → ${(row.limit + row.topUp).toLocaleString(locale())}`
        : tr('pitMultipleReady');
      return `<div><label class="hk-pit-enable"><input type="checkbox" data-pit-enabled="${row.id}" ${enabled ? 'checked' : ''} ${row.current > 0 ? '' : 'disabled'}><b>${tr(row.textKey)}</b><span>${tr('pitRun')}</span></label><span>${tr('pitAvailableNow')}: <strong>${row.current.toLocaleString(locale())}</strong>/${row.limit.toLocaleString(locale())}</span><small>${tr('pitLimit')}: ${row.limit.toLocaleString(locale())} · ${topUp}</small><label class="hk-pit-move-choice"><span>${tr('pitUseMoves')}</span><select data-pit-moves="${row.id}" ${enabled && row.current > 0 ? '' : 'disabled'}>${pitMoveOptions(row.current, selected)}</select><em>${tr('pitMovePlan')}: <b>${pitMovePlanText(selected)}</b></em></label></div>`;
    }).join('')}</div>`;
  }

  function pitRaceSnapshot(typeId, documentValue) {
    const config = PIT_DAILY_API[typeId];
    if (!config || !documentValue || typeof documentValue !== 'object') return null;
    const roots = [documentValue, documentValue.player, documentValue.data, documentValue.data?.player]
      .filter(value => value && typeof value === 'object');
    for (const root of roots) for (const key of config.stateKeys) {
      const state = root?.[key];
      if (state && typeof state === 'object' && Number.isFinite(Number(state.level))) return state;
    }
    return null;
  }

  function pitRaceState(typeId, documentValue) {
    const state = pitRaceSnapshot(typeId, documentValue);
    if (!state) return null;
    // /player/me permanently keeps the Pit level and combat preview after a
    // round has been collected. Only a positive multiplier identifies a
    // batch that was actually started and still has to be fought/collected.
    const multiplier = Number(state.mass_multiplier ?? state.massMultiplier ?? state.multiplier ?? 0);
    return Number.isFinite(multiplier) && multiplier > 0 ? state : null;
  }

  function pitRaceFinished(state) {
    if (!state || typeof state !== 'object') return true;
    const explicit = state.is_finish ?? state.is_finished ?? state.isFinished ?? state.finished ?? state.completed;
    if (typeof explicit === 'boolean') return explicit;
    if (explicit === 0 || explicit === 1 || explicit === '0' || explicit === '1') return Number(explicit) === 1;
    const status = String(state.status ?? state.state ?? '').toLowerCase();
    return ['finish','finished','complete','completed','done'].includes(status);
  }

  function pitAlreadyFinishedError(error) {
    const message = String(error?.message || error || '');
    return /HTTP 409\b/i.test(message) && /player already finished pit(?:\s|[_.-]|$)/i.test(message);
  }

  async function finishDailyPitRace(typeId, documentValue) {
    const config = PIT_DAILY_API[typeId];
    let result = documentValue;
    let state = pitRaceState(typeId, result);
    if (!state) return result;
    let battles = 0;
    while (!pitRaceFinished(state)) {
      if (hkRunner.running) await hkRunner.waitIfPaused();
      if (++battles > 1000) throw new Error(either('превышен безопасный предел боёв Ямы','Pit battle safety limit exceeded'));
      try {
        result = await apiJson(config.battle, 'POST');
      } catch (error) {
        // /player/me can lag behind the Pit endpoints: it may still mark the
        // race as active after the server has already completed its last
        // battle. In that state another battle returns 409. Finalize the race
        // below instead of treating the whole selected Pit action as failed.
        if (pitAlreadyFinishedError(error)) break;
        throw error;
      }
      const battleSnapshot = pitRaceSnapshot(typeId, result);
      if (battleSnapshot && pitRaceFinished(battleSnapshot)) break;
      state = pitRaceState(typeId, result);
      // Some battle responses omit mass_multiplier or return only the reward
      // payload. Refresh /player/me before deciding whether another battle is
      // required; losing this state previously skipped reward collection.
      if (!state) {
        result = await apiJson('/player/me', 'POST');
        const refreshedSnapshot = pitRaceSnapshot(typeId, result);
        if (!pitRaceState(typeId, result) || pitRaceFinished(refreshedSnapshot)) break;
        state = pitRaceState(typeId, result);
      }
      await sleep(120);
    }
    for (let attempt = 0; attempt < 3; attempt++) {
      if (hkRunner.running) await hkRunner.waitIfPaused();
      try {
        await apiJson(config.finish, 'POST');
      } catch (error) {
        // 409 here means the server has already closed this race. Refreshing
        // the player document below is still required before the next start.
        if (!pitAlreadyFinishedError(error)) throw error;
      }
      result = await apiJson('/player/me', 'POST');
      if (!pitRaceState(typeId, result)) return result;
      await sleep(250 * (attempt + 1));
    }
    throw new Error(either('награда Ямы не была собрана после трёх попыток','Pit reward was not collected after three attempts'));
  }

  async function executeDailyPit(action) {
    const typeId = action.pitType;
    const config = PIT_DAILY_API[typeId];
    if (!config) throw new Error(either('неизвестный тип Ямы','unknown Pit type'));
    playerDocument = await apiJson('/player/me', 'POST');
    const existingRace = pitRaceState(typeId, playerDocument);
    const alreadyReserved = existingRace && !pitRaceFinished(existingRace)
      ? Math.max(0, Math.trunc(Number(existingRace?.mass_multiplier ?? existingRace?.massMultiplier ?? existingRace?.multiplier ?? 0)))
      : 0;
    // Complete a race that was left open in the game before starting the
    // selected batches; starting a new one while it is active is rejected.
    playerDocument = await finishDailyPitRace(typeId, playerDocument);
    // The selector represents only tickets currently present in the wallet.
    // A previously started batch is completed separately and does not replace
    // any of the newly selected moves.
    const requested = selectedPitMoves(typeId, pitLimitSummaries().find(row => row.id === typeId)?.current || 0);
    if (!requested) throw new Error(either('нет выбранных доступных ходов','no available moves selected'));
    let completedMoves = 0;
    const remainingRequested = requested;
    if (alreadyReserved) log(`${tr(action.textKey)}: ${either('завершена ранее начатая серия','previously started batch completed')} ×${alreadyReserved}`, 'ok');
    for (const part of pitMovePlan(remainingRequested)) for (let index = 0; index < part.count; index++) {
      if (hkRunner.running) await hkRunner.waitIfPaused();
      // Re-read the wallet before every batch. The nominal limit is not used:
      // only the live, currently available ticket count can authorize a run.
      playerDocument = await apiJson('/player/me', 'POST');
      const available = pitLimitSummaries().find(row => row.id === typeId)?.current || 0;
      if (available < part.size) throw new Error(either(
        `доступных ходов осталось ${available}, для серии ×${part.size} недостаточно`,
        `${available} moves remain, not enough for the ×${part.size} batch`
      ));
      try {
        playerDocument = await apiJson(config.start, 'POST', {mass_multiplier:part.size});
      } catch (error) {
        // Some server responses omit the finished race from /player/me. If
        // start still reports it, close it explicitly and retry once.
        if (!pitAlreadyFinishedError(error)) throw error;
        try { playerDocument = await apiJson(config.finish, 'POST'); }
        catch (finishError) {
          if (!pitAlreadyFinishedError(finishError)) throw finishError;
          playerDocument = await apiJson('/player/me', 'POST');
        }
        try {
          playerDocument = await apiJson(config.start, 'POST', {mass_multiplier:part.size});
        } catch (retryError) {
          if (pitAlreadyFinishedError(retryError)) {
            markPitUnavailable(typeId);
            throw new Error(either('Яма уже завершена в текущем периоде; доступных запусков: 0',
              'The Pit is already completed for the current period; available starts: 0'));
          }
          throw retryError;
        }
      }
      if (!pitRaceState(typeId, playerDocument)) {
        playerDocument = await apiJson('/player/me', 'POST');
        if (!pitRaceState(typeId, playerDocument)) throw new Error(either('Яма не запустилась','Pit did not start'));
      }
      playerDocument = await finishDailyPitRace(typeId, playerDocument);
      completedMoves += part.size;
      savePitMoves(typeId, Math.max(0, requested - completedMoves));
      log(`${tr(action.textKey)}: ${either('пройдена серия','batch completed')} ×${part.size}`, 'ok');
      await sleep(250);
    }
    savePitMoves(typeId, 0);
  }

  function clickText(pattern, forbidden = null) {
    const candidates = [...document.querySelectorAll('button,[role="button"],a')]
      .filter(visible)
      .filter(e => pattern.test(clean(e.innerText)) && !(forbidden && forbidden.test(clean(e.innerText))))
      .sort((a, b) => clean(a.innerText).length - clean(b.innerText).length);
    if (!candidates[0]) return false;
    candidates[0].click();
    return true;
  }

  async function clickEntranceToken() {
    const exactOne = [...document.querySelectorAll('button,[role="button"]')].filter(visible).filter(e => clean(e.innerText) === '1');
    for (const button of exactOne) {
      let ancestor = button.parentElement;
      for (let depth = 0; ancestor && depth < 12; depth++, ancestor = ancestor.parentElement) {
        const context = clean(ancestor.innerText);
        if (/алмаз|diamond/i.test(context)) break;
        if (/Оплатить вход|Pay (?:for )?entrance|Pay entry/i.test(context)) {
          button.click(); return true;
        }
      }
    }
    const roots = [...document.querySelectorAll('[role="dialog"],[class*="modal"],[class*="popup"],[class*="payment"]')].filter(visible);
    const describe = e => clean([e.innerText, e.getAttribute?.('aria-label'), e.getAttribute?.('title'), ...[...e.querySelectorAll?.('img') || []].map(img => img.alt)].filter(Boolean).join(' '));
    const safe = e => !/алмаз|diamond/i.test(describe(e));
    const actionable = e => e && !e.disabled && (e.matches('button,[role="button"],a') || e.onclick || getComputedStyle(e).cursor === 'pointer');
    const confirm = () => roots.flatMap(r => [...r.querySelectorAll('button,[role="button"],a,div')]).filter(visible).filter(actionable).filter(safe)
      .find(e => /использовать\s*(?:1\s*)?жетон|use\s*(?:1\s*)?token|подтвердить|confirm/i.test(describe(e)));
    let target = confirm();
    if (target) { target.click(); return true; }
    const marker = roots.flatMap(r => [...r.querySelectorAll('button,[role="button"],a,div')]).filter(visible).filter(safe)
      .find(e => /жетон|token/i.test(describe(e)));
    if (!marker) return false;
    target = marker;
    for (let depth = 0; target && depth < 8; depth++, target = target.parentElement) {
      if (!safe(target)) break;
      if (actionable(target)) {
        target.click(); await gameRetryDelay(450);
        if (hkRunner.running) await hkRunner.waitIfPaused();
        const next = confirm(); if (next) next.click();
        return true;
      }
    }
    return false;
  }

  function clickRestoreToken() {
    const candidates = [...document.querySelectorAll('button,[role="button"]')].filter(visible).filter(e => clean(e.innerText) === '1');
    for (const button of candidates) {
      let ancestor = button.parentElement;
      for (let depth = 0; ancestor && depth < 10; depth++, ancestor = ancestor.parentElement) {
        if (/Восстановление жизней|Restore lives/i.test(clean(ancestor.innerText)) && !/алмаз|diamond/i.test(clean(ancestor.innerText))) {
          button.click(); return true;
        }
      }
    }
    return false;
  }

  function rememberPower(state) {
    if (!state.round || !state.enemyText) return;
    // Do not use look-behind here: some Safari userscript engines reject it
    // while parsing the whole panel, which prevented the HK button from
    // appearing at all. The follow-up numeric filtering is sufficient.
    const values = [...state.enemyText.matchAll(/\d[\d\s.,]{4,}\d/g)].map(m => Number(m[0].replace(/\D/g, ''))).filter(Boolean);
    if (!values.length) return;
    const pitType = currentPitType();
    if (!pitType) return;
    rememberPitObservation(pitType, {level:state.round, enemyPower:Math.max(...values), source:'screen'});
    renderPitForecast(state);
  }

  function currentPitType() {
    const path = location.pathname.toLowerCase();
    const heading = [...document.querySelectorAll('h1,h2,.pit-page__title,.page-title')].map(element=>clean(element.innerText || '')).join(' · ');
    if (/boss[_-]?pit|pit[_-]?2/.test(path) || /Яма Боссов|Boss Pit/i.test(heading)) return 'boss';
    if (/pit[_-]?pve|pve[_-]?pit/.test(path) || /Яма Банд|Gang Pit/i.test(heading)) return 'gang';
    if (/(?:^| · )(?:Хомячья Яма|Hamster Pit)(?: · |$)/i.test(heading)) return 'normal';
    if (lastNetworkPitContext && Date.now()-lastNetworkPitContext.at < 120000) return lastNetworkPitContext.pitType;
    return null;
  }

  function pitPowerValue(state) {
    const values = [...String(state?.enemyText || '').matchAll(/\d[\d\s.,]{4,}\d/g)].map(match => Number(match[0].replace(/\D/g,''))).filter(Boolean);
    return values.length ? Math.max(...values) : null;
  }

  function combinedPitRows(pitType) {
    const local = pitStoreDocument()[pitType] || {};
    const grouped = new Map();
    for (const row of sharedPitRows.filter(value=>value?.pit_type===pitType)) {
      const level = Number(row.level), existing = grouped.get(level);
      if (!Number.isSafeInteger(level) || level < 1 || level > PIT_MAX_LEVEL || !Number.isFinite(Number(row.enemy_power))) continue;
      if (!existing || Number(row.players||0)>Number(existing.players||0) || (Number(row.players||0)===Number(existing.players||0) && Number(row.samples||0)>Number(existing.samples||0))) grouped.set(level,row);
    }
    for (const [level,value] of Object.entries(local)) {
      const numericLevel = Number(level), enemyPower = Number(value.enemyPower);
      if (!Number.isSafeInteger(numericLevel) || numericLevel < 1 || numericLevel > PIT_MAX_LEVEL || !(enemyPower > 0)) continue;
      const confirmedElsewhere = value.source !== 'network' && sharedPitRows.some(row =>
        row?.pit_type !== pitType && Number(row?.level) === numericLevel && Number(row?.enemy_power) === enemyPower
      );
      if (confirmedElsewhere) continue;
      grouped.set(numericLevel, {pit_type:pitType,level:numericLevel,enemy_power:enemyPower,players:Math.max(1,Number(grouped.get(numericLevel)?.players||0)),samples:Number(value.samples||1),observed_winrate:value.winrate});
    }
    return [...grouped.values()].sort((a,b)=>Number(a.level)-Number(b.level));
  }

  function predictedPitPower(round, pitType = 'normal') {
    const rows = combinedPitRows(pitType).map(row => [Number(row.level),Number(row.enemy_power)]).filter(([x,y]) => Number.isFinite(x)&&Number.isFinite(y));
    if (!rows.length) return null;
    if (rows.length === 1) return rows[0][1];
    const meanX = rows.reduce((sum,row)=>sum+row[0],0)/rows.length;
    const meanY = rows.reduce((sum,row)=>sum+row[1],0)/rows.length;
    const denominator = rows.reduce((sum,row)=>sum+(row[0]-meanX)**2,0);
    const slope = denominator ? rows.reduce((sum,row)=>sum+(row[0]-meanX)*(row[1]-meanY),0)/denominator : 0;
    return Math.max(0,Math.round(meanY+slope*(Number(round)-meanX)));
  }

  function pitDuelChance(playerPower, enemyPower, exponent = 5) {
    if (!(playerPower > 0) || !(enemyPower > 0)) return null;
    return Math.max(0,Math.min(1,2*Math.atan((playerPower/enemyPower)**exponent)/Math.PI));
  }

  function pitChanceExponentFromSample(playerPower, enemyPower, rawChance) {
    const chance = normalizePitChance(rawChance);
    const ratio = Number(playerPower || 0) / Number(enemyPower || 0);
    if (!(chance > 0 && chance < 1) || !(ratio > 0) || Math.abs(ratio - 1) < 0.001) return 5;
    const exponent = Math.log(Math.tan(chance*Math.PI/2)) / Math.log(ratio);
    return Number.isFinite(exponent) && exponent >= 1 && exponent <= 12 ? exponent : 5;
  }

  function pitLocalChanceExponent(pitType, playerPower) {
    const profile = load().pitPlayerProfiles?.[pitType] || {};
    const level = Number(profile.level || 0);
    const enemyPower = Number(pitStoreDocument()?.[pitType]?.[level]?.enemyPower || 0);
    return pitChanceExponentFromSample(playerPower,enemyPower,profile.winrate);
  }

  function pitForecastProfile(pitType) {
    const profiles = load().pitPlayerProfiles || {};
    const roots = [playerDocument, playerDocument?.player, playerDocument?.data].filter(value=>value && typeof value === 'object');
    const typePreviews = roots.map(value=>pitType === 'normal' ? value?.pit_preview
      : pitType === 'boss' ? value?.pit2_preview
        : value?.pit_pve_preview).filter(value=>value && typeof value === 'object');
    const liveFactionSets = roots.map(value=>pitFactionPowers(value,pitType)).filter(rows=>rows.length)
      .map(rows=>rows.map(Number).filter(power=>power>0).sort((a,b)=>b-a));
    const liveBest = liveFactionSets.sort((a,b)=>b.length-a.length)[0] || [];
    const saved = Array.isArray(profiles[pitType]?.factionPowers)
      ? profiles[pitType].factionPowers.map(Number).filter(power=>power>0)
      : [];
    if (pitType !== 'gang') saved.sort((a,b)=>b-a);
    // Profiles from different Pit types are not interchangeable: Boss Pit
    // must use only the cartel powers and support captured for Boss Pit.
    const best = pitType === 'gang' && saved.length ? saved : liveBest.length ? liveBest : saved;
    const factionPowers = pitType === 'boss' ? best : best.slice(0,pitType === 'gang' ? 8 : 1);
    const liveTypeSupport = typePreviews.map(pitSupportPower).find(power=>power>0) || 0;
    const genericLiveSupport = roots.map(pitSupportPower).find(power=>power>0) || 0;
    const supportPower = liveTypeSupport || Number(profiles[pitType]?.supportPower || 0) || genericLiveSupport;
    const liveTypePlayerPower = typePreviews.map(pitCombinedPlayerPower).find(power=>power>0) || 0;
    // Never borrow another mode's or another participant's power. The value
    // saved from this installation's preview is the authoritative local one.
    const playerPower = liveTypePlayerPower || Number(profiles[pitType]?.playerPower || 0) ||
      (pitType === 'boss' ? 0 : roots.map(pitCombinedPlayerPower).find(power=>power>0) || 0);
    const roundEnemyPowers = Array.isArray(profiles[pitType]?.roundEnemyPowers) ? profiles[pitType].roundEnemyPowers.map(Number).slice(0,8) : [];
    const roundChances = Array.isArray(profiles[pitType]?.roundChances) ? profiles[pitType].roundChances.map(normalizePitChance).slice(0,8) : [];
    const referenceEnemyPower = Number(profiles[pitType]?.referenceEnemyPower || 0);
    const localLevel = Number(profiles[pitType]?.level || 0);
    const localWinrate = normalizePitChance(profiles[pitType]?.winrate);
    return {factionPowers, supportPower, playerPower, roundEnemyPowers, roundChances, referenceEnemyPower, localLevel, localWinrate};
  }

  function pitForecastChance(pitType, level, enemyPower) {
    const profile = pitForecastProfile(pitType);
    const supportPower = Number(profile?.supportPower || 0);
    if (Number(level) === profile.localLevel && profile.localWinrate !== null && profile.referenceEnemyPower > 0 &&
        Math.abs(Number(enemyPower || 0)-profile.referenceEnemyPower) <= Math.max(1,profile.referenceEnemyPower*0.001)) {
      return profile.localWinrate;
    }
    if (pitType === 'normal' && (Number(profile?.playerPower || 0) > 0 || (Array.isArray(profile?.factionPowers) && profile.factionPowers.length))) {
      const strongest = Math.max(0,...(profile.factionPowers || []).map(Number).filter(power=>power>0));
      // Normal Pit preview already includes the selected cartel, generals,
      // the current efficiency bonus and every support cartel.
      const effectivePower = Number(profile?.playerPower || 0) || strongest*1.5+supportPower;
      return pitDuelChance(effectivePower,Number(enemyPower||0),pitLocalChanceExponent('normal',effectivePower));
    }
    if (pitType === 'boss' && (Number(profile?.playerPower || 0) > 0 || (Array.isArray(profile?.factionPowers) && profile.factionPowers.length))) {
      // The Boss Pit preview returns this participant's final power after all
      // cartel and support modifiers. Prefer it so every installation gets an
      // individual forecast; reconstruct the value only before preview data is available.
      const combinedPower = Number(profile?.playerPower || 0) ||
        profile.factionPowers.reduce((sum,power)=>sum+Number(power||0),0) + supportPower*5;
      return pitDuelChance(combinedPower,Number(enemyPower||0),pitLocalChanceExponent('boss',combinedPower));
    }
    if (pitType === 'gang' && Array.isArray(profile?.factionPowers) && profile.factionPowers.length >= 8) {
      const referenceBase = Number(profile.referenceEnemyPower || 0);
      const hasRoundProfile = referenceBase > 0 && profile.roundEnemyPowers?.length === 8 && profile.roundChances?.length === 8;
      if (!hasRoundProfile) return null;
      const chances = profile.factionPowers.slice(0,8).map((power,index)=>{
        const referenceEnemy = Number(profile.roundEnemyPowers[index] || referenceBase);
        const targetEnemy = Number(enemyPower || 0) * referenceEnemy / referenceBase;
        const exponent = pitChanceExponentFromSample(power,referenceEnemy,profile.roundChances[index]);
        return pitDuelChance(Number(power),targetEnemy,exponent);
      }).filter(value=>value!==null);
      return chances.length === 8 ? pitAtLeastWins(chances,5) : null;
    }
    const duel = pitDuelChance(Number(profile?.playerPower||0), Number(enemyPower||0));
    if (duel === null) return null;
    return pitType === 'gang' ? null : duel;
  }

  function pitPaws(pitType, chance) {
    if (!(chance > 0)) return chance === 0 ? Infinity : null;
    // The player starts with five free attempts. Every recovery token adds
    // another five, so only attempts beyond the first five consume tokens.
    const expectedAttempts = 1/chance;
    return Math.max(0, Math.ceil(expectedAttempts/5)-1);
  }

  function pitChanceLabel(chance) {
    if (chance === null) return '';
    if (chance > 0 && chance < 0.001) return '<0,1%';
    return `${(chance*100).toLocaleString(locale(),{maximumFractionDigits:1})}%`;
  }

  function pitRestoreLabel(tokens) {
    const amount = tokens === Infinity ? '∞' : tokens;
    return locale() === 'ru' ? `жет. восстановления: ${amount}` : `restore tokens: ${amount}`;
  }

  function pitCurrentLevel(pitType) {
    const stored = load();
    const runtime = Number(stored.pitRuntimeLevels?.[pitType] || 0);
    const observed = Number(stored.pitPlayerProfiles?.[pitType]?.level || 0);
    const value = Math.max(runtime, observed);
    return Number.isSafeInteger(value) && value > 0 ? value : null;
  }

  function pitEstimatedTokensToTarget(pitType, target, rowsByLevel) {
    const from = pitCurrentLevel(pitType);
    if (!from) return {from:null, tokens:null};
    if (target <= from) return {from, tokens:0};
    let tokens = 0;
    // Reaching level N requires completing the current level through N-1.
    for (let level = from; level < target; level++) {
      const exact = rowsByLevel.get(level);
      const enemyPower = Number(exact?.enemy_power) || predictedPitPower(level,pitType);
      const chance = pitForecastChance(pitType,level,enemyPower);
      const estimate = pitPaws(pitType,chance);
      if (estimate === null) return {from, tokens:null};
      if (estimate === Infinity) return {from, tokens:Infinity};
      tokens += estimate;
    }
    return {from, tokens};
  }

  function pitPowerCell(pitType, level, enemyPower) {
    if (!(enemyPower > 0)) return '<span class="hk-muted">—</span>';
    const chance = pitForecastChance(pitType,level,enemyPower);
    const paws = pitPaws(pitType,chance);
    const detail = chance === null ? '' : `<small>${pitChanceLabel(chance)} · ${pitRestoreLabel(paws)}</small>`;
    const power = Math.round(enemyPower).toLocaleString(locale());
    const shownPower = pitType === 'gang'
      ? `<b>${power}</b><small>${either('обычная','base')}: ${power} · +50%: ${Math.round(enemyPower*1.5).toLocaleString(locale())}</small>`
      : `<b>${power}</b>`;
    return `${shownPower}${detail}`;
  }

  function renderPitForecast(state = pitState()) {
    const box = root?.querySelector('#hk-pit-forecast'); if (!box) return;
    const currentDetails = box.querySelector('details');
    if (currentDetails) pitPowerTableOpen = currentDetails.open;
    const byType = Object.fromEntries(['normal','boss','gang'].map(type=>[type,combinedPitRows(type)]));
    const levels = [...new Set(Object.values(byType).flatMap(rows=>rows.map(row=>Number(row.level))))].filter(Number.isFinite).sort((a,b)=>a-b);
    const lookup = Object.fromEntries(Object.entries(byType).map(([type,rows])=>[type,new Map(rows.map(row=>[Number(row.level),row]))]));
    const target = Math.max(1,Number(root?.querySelector('#hk-target')?.value || settings.target || 1));
    const currentPower = pitPowerValue(state);
    const comparison = pitRunStart && state.round ? `<p>${tr('pitComparison',{before:pitRunStart.round||'—',after:state.round,powerBefore:Number(pitRunStart.power||0).toLocaleString(locale()),powerAfter:Number(currentPower||0).toLocaleString(locale())})}</p>` : '';
    const targets = ['normal','boss','gang'].map(type=>{
      const exact=lookup[type].get(target); const power=Number(exact?.enemy_power)||predictedPitPower(target,type); const chance=pitForecastChance(type,target,power); const paws=pitPaws(type,chance);
      const label=tr(type==='normal'?'pitNormal':type==='boss'?'pitBoss':'pitGang');
      const displayedPower = power ? (type === 'gang'
        ? `${Math.round(power).toLocaleString(locale())} / +50% ${Math.round(power*1.5).toLocaleString(locale())}`
        : Math.round(power).toLocaleString(locale())) : '—';
      const total = pitEstimatedTokensToTarget(type,target,lookup[type]);
      const totalText = total.tokens === null
        ? either('Откройте эту Яму, чтобы определить текущий уровень и силу','Open this Pit to detect the current level and power')
        : total.tokens === Infinity
          ? either(`Примерно до уровня ${target}: 🐾 ∞`,`Estimated to level ${target}: 🐾 ∞`)
          : either(`Примерно до уровня ${target}: 🐾 ${total.tokens} · с уровня ${total.from}`,`Estimated to level ${target}: 🐾 ${total.tokens} · from level ${total.from}`);
      const targetChance = chance === null ? '' : ` · ${either('шанс боя','battle chance')}: ${pitChanceLabel(chance)} · ${pitRestoreLabel(paws)}`;
      return `<div><b>${label}</b><small>${either(`Сила уровня ${target}`,`Level ${target} power`)}</small><strong>${displayedPower}</strong><small>${totalText}${targetChance}</small></div>`;
    }).join('');
    const table = levels.slice(-40).reverse().map(level=>`<tr><th>${level}</th>${['normal','boss','gang'].map(type=>{const row=lookup[type].get(level);return `<td>${pitPowerCell(type,level,Number(row?.enemy_power))}</td>`;}).join('')}</tr>`).join('');
    box.innerHTML = `<h4>${tr('pitForecast')}</h4><div class="hk-pit-targets">${targets}</div><p>${either('Расчёт: обычная Яма — итоговая сила лучшего картеля из предпросмотра боя, включая генералов, текущую эффективность и всю поддержку; Яма боссов — итоговая сила всех картелей из личного предпросмотра; Яма банд — восемь индивидуальных пар с их фактической силой, эффективностью и поддержкой, общий успех требует минимум 5 побед из 8. Проценты рассчитываются индивидуально. Один жетон восстановления даёт 5 дополнительных попыток.','Calculation: Normal Pit uses the best cartel final power from the local preview, including generals, current efficiency and all support; Boss Pit uses the local preview final power of all cartels; Gang Pit uses eight individual matchups with their actual power, efficiency and support, and requires at least 5 wins out of 8. Chances are calculated individually. One recovery token gives five extra attempts.')}</p><p>${tr('pitTokenBudget',{n:Number(settings.activationLimit||0)+Number(settings.restoreLimit||0)})}</p>${comparison}${table?`<details ${pitPowerTableOpen?'open':''}><summary>${tr('pitPowerTable')}</summary><div class="hk-pit-table-wrap"><table><thead><tr><th>${either('Уровень','Level')}</th><th>${tr('pitNormal')}</th><th>${tr('pitBoss')}</th><th>${tr('pitGang')}</th></tr></thead><tbody>${table}</tbody></table></div></details>`:''}`;
    const details = box.querySelector('details');
    if (details) details.addEventListener('toggle',()=>{ pitPowerTableOpen=details.open; });
  }

  async function pitLoop() {
    while (pitRunning) {
      if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');
      await hkRunner.waitIfPaused();
      const state = pitState();
      rememberPower(state);
      updatePitStatus(state);
      if (state.round !== null && state.round >= settings.target) {
        pitRunning = false; log(`Цель достигнута: раунд ${state.round}`, 'ok'); break;
      }
      if (settings.collectOnly) {
        await gameRetryDelay(Math.max(700, settings.interval * 1000));
        continue;
      }
      let acted = false;
      if (state.restoreModal) {
        if (!settings.allowTokens || restoreSpent >= settings.restoreLimit) {
          pitRunning = false; log('Остановка: достигнут лимит жетонов восстановления', 'warn'); break;
        }
        acted = clickRestoreToken();
        if (acted) { restoreSpent++; log(`Восстановление жетоном ${restoreSpent}/${settings.restoreLimit}`); }
      } else if (state.controls.some(text => /^(Восстановить|Restore)$/i.test(text))) {
        if (!settings.allowTokens || restoreSpent >= settings.restoreLimit) {
          pitRunning = false; log('Требуется восстановление, но расход жетонов запрещён', 'warn'); break;
        }
        acted = clickText(/^(Восстановить|Restore)$/i);
      } else if (state.controls.some(text => /Сражаться\s+До конца|Fight\s+to\s+end/i.test(text))) {
        acted = clickText(/Сражаться\s+До конца|Fight\s+to\s+end/i);
      } else if (state.controls.some(text => /Сражаться|Fight/i.test(text))) {
        const fast = [...document.querySelectorAll('button.event-offer__auto')].find(visible);
        if (fast) { fast.click(); acted = true; log('Ускорение боя включено'); }
        else acted = clickText(/Сражаться|Fight/i, /До конца|to end/i);
      } else if (state.controls.some(text => /Оплатить|Pay/i.test(text)) || /Оплатить вход|Pay entry/i.test(document.body?.innerText || '')) {
        if (!settings.allowTokens || activationSpent >= settings.activationLimit) {
          pitRunning = false; log('Остановка: достигнут лимит жетонов активации', 'warn'); break;
        }
        if (state.controls.some(text => /Оплатить|Pay/i.test(text))) clickText(/Оплатить|Pay/i);
        await gameRetryDelay(400);
        if (hkRunner.running) await hkRunner.waitIfPaused();
        acted = await clickEntranceToken();
        if (acted) { activationSpent++; log(`Активация жетоном ${activationSpent}/${settings.activationLimit}`); }
      } else if (/жетон|token/i.test(document.body?.innerText || '')) {
        if (settings.allowTokens && activationSpent < settings.activationLimit) {
          acted = await clickEntranceToken();
          if (acted) { activationSpent++; log(`Активация жетоном ${activationSpent}/${settings.activationLimit}`); }
        }
      }
      await gameRetryDelay(Math.max(700, settings.interval * 1000));
      if (!acted) await gameRetryDelay(500);
    }
    updatePitButtons();
  }

  function updatePitStatus(state = pitState()) {
    const element = document.querySelector('#hk-pit-live');
    if (element) element.textContent = language === 'en'
      ? `Round: ${state.round ?? '—'} · activations ${activationSpent}/${settings.activationLimit} · recoveries ${restoreSpent}/${settings.restoreLimit}`
      : `Раунд: ${state.round ?? '—'} · активации ${activationSpent}/${settings.activationLimit} · восстановления ${restoreSpent}/${settings.restoreLimit}`;
    renderPitForecast(state);
  }

  function updatePitButtons() {
    const start = document.querySelector('#hk-pit-start');
    const stop = document.querySelector('#hk-pit-stop');
    if (start) start.disabled = pitRunning;
    if (stop) stop.disabled = !pitRunning;
  }

  function findBuildings(value) {
    if (Array.isArray(value)) { for (const child of value) { const found = findBuildings(child); if (found) return found; } }
    else if (value && typeof value === 'object') {
      if (Array.isArray(value.business_building)) return value.business_building;
      for (const child of Object.values(value)) { const found = findBuildings(child); if (found) return found; }
    }
    return null;
  }

  function normalizeLayout(documentValue) {
    const result = [];
    for (const building of findBuildings(documentValue) || []) {
      const active = new Map((building.active_business || []).filter(item => number(item.slot) !== null).map(item => [Number(item.slot), item]));
      const slots = new Set(active.keys());
      const slotCount = Math.max(0, Number(building.num_slots || 0));
      const negative = [...slots].filter(slot => slot < 0);
      const firstSlot = negative.length ? Math.min(...negative) : 0;
      for (let slot = firstSlot; slot < firstSlot + slotCount; slot++) slots.add(slot);
      for (const slot of [...slots].sort((a,b) => a-b)) {
        const item = active.get(slot) || {};
        result.push({
          key: `${building.id}|${slot}`, buildingId: String(building.id), slot,
          buildingLevel: building.level, businessId: item.business_id || '', status: item.status || 'INACTIVE', timer: item.timer,
          freeSpeedUpTime: item.free_speed_up_time, influence: item.influence || 0
        });
      }
    }
    return result;
  }

  function normalizeInventory(documentValue) {
    const quantities = new Map();
    for (const item of documentValue.items || []) {
      const id = String(item?.item_id || '');
      const quantity = Math.max(0, Number(item?.quantity || 0));
      if (!id.startsWith('item_bsn_') || id.endsWith('_dummy') || !quantity) continue;
      quantities.set(id, (quantities.get(id) || 0) + quantity);
    }
    return [...quantities].map(([businessId, quantity]) => ({businessId, quantity})).sort((a,b) => a.businessId.localeCompare(b.businessId));
  }

  function visibleBusinessTier(value) {
    const technicalTier = Number(value);
    // Business quality codes are sparse in the game data. In particular,
    // yellow is t5/T5 and orange is t8/T6; simply adding one makes yellow
    // businesses appear as T6 and orange businesses as T9.
    return ({0:1, 1:2, 2:3, 3:4, 5:5, 8:6})[technicalTier] ?? null;
  }

  function tier(id) {
    const match = String(id || '').match(/_r\d+t(\d+)(?:_|$)/);
    return match ? visibleBusinessTier(match[1]) : null;
  }

  function iconUrls(id) {
    const urls = [];
    const match = String(id || '').match(/^item_bsn_r(\d+)t\d+_(.+)$/);
    if (match) {
      const [, rarity, rest] = match;
      if (rest.startsWith('event_') || rest.startsWith('tier2_')) urls.push(`${ASSET_BASE}/item_bsn_r${rarity}_${rest}_icon.png`);
      urls.push(`${ASSET_BASE}/item_bsn_${rest}_r${rarity}_icon.png`, `${ASSET_BASE}/item_bsn_r${rarity}_${rest}_icon.png`);
    }
    urls.push(`${ASSET_BASE}/${id}_icon.png`);
    return [...new Set(urls)];
  }

  function iconHtml(id) {
    const urls = iconUrls(id);
    return `<img class="hk-icon" src="${escapeHtml(urls[0] || '')}" data-fallbacks="${escapeHtml(JSON.stringify(urls.slice(1)))}" alt="">`;
  }

  function installIconFallbacks(scope) {
    scope.querySelectorAll('img[data-fallbacks]').forEach(img => img.addEventListener('error', () => {
      let items = []; try { items = JSON.parse(img.dataset.fallbacks || '[]'); } catch (_) {}
      const next = items.shift(); img.dataset.fallbacks = JSON.stringify(items);
      if (next) img.src = next; else img.style.visibility = 'hidden';
    }));
  }

  function fairStates(documentValue = fairDocument || playerDocument) {
    const values = documentValue?.fair ?? documentValue?.player?.fair ?? [];
    return values.filter(value => value && value.id);
  }

  function fairState(id, documentValue = fairDocument || playerDocument) {
    return fairStates(documentValue).find(value => String(value.id) === String(id));
  }

  function isEventFairState(state) {
    return !!state && String(state.id || '').toLowerCase() !== 'fair_default';
  }

  function costParts(cost) {
    return ['items', 'currencies'].flatMap(kind => (cost?.[kind] || []).map(value => ({
      kind, id: String(value?.id || ''), quantity: Math.trunc(Number(value?.quantity || 0))
    })));
  }

  // A shop limit only says that a lot may be bought today. It does not mean
  // that the account has its required clan currency. Check the live player
  // inventory first so daily purchases do not stop on a server-side 409.
  function walletAmount(id, documentValue = playerDocument) {
    const wanted = String(id || '');
    const lists = [documentValue?.items, documentValue?.player?.items, documentValue?.inventory?.items,
      documentValue?.currencies, documentValue?.player?.currencies, documentValue?.inventory?.currencies];
    for (const list of lists) {
      if (!Array.isArray(list)) continue;
      const matches = list.filter(item => String(item?.item_id || item?.currency_id || item?.id || '') === wanted);
      if (matches.length) return matches.reduce((sum, item) => sum + Math.max(0, Number(item?.quantity ?? item?.value ?? 0)), 0);
    }
    const direct = [documentValue?.[wanted], documentValue?.player?.[wanted], documentValue?.currencies?.[wanted], documentValue?.player?.currencies?.[wanted], documentValue?.wallet?.[wanted]];
    for (const value of direct) if (Number.isFinite(Number(value))) return Math.max(0, Number(value));
    return null;
  }

  function debitWallet(cost, multiplier = 1, documentValue = playerDocument) {
    if (!documentValue) return;
    for (const part of costParts(cost)) {
      const amount = Math.max(0, Number(part.quantity || 0) * Math.max(0, Number(multiplier || 0)));
      if (!amount) continue;
      const wanted = String(part.id || '');
      const lists = [documentValue?.items, documentValue?.player?.items, documentValue?.inventory?.items,
        documentValue?.currencies, documentValue?.player?.currencies, documentValue?.inventory?.currencies];
      let debited = false;
      for (const list of lists) {
        if (!Array.isArray(list)) continue;
        const item = list.find(value => String(value?.item_id || value?.currency_id || value?.id || '') === wanted);
        if (!item) continue;
        if (item.quantity !== undefined) item.quantity = Math.max(0, Number(item.quantity || 0) - amount);
        else if (item.value !== undefined) item.value = Math.max(0, Number(item.value || 0) - amount);
        debited = true;
        break;
      }
      if (debited) continue;
      const owners = [documentValue, documentValue?.player, documentValue?.currencies, documentValue?.player?.currencies, documentValue?.wallet];
      for (const owner of owners) {
        if (!owner || !Number.isFinite(Number(owner[wanted]))) continue;
        owner[wanted] = Math.max(0, Number(owner[wanted]) - amount);
        break;
      }
    }
  }

  function setWalletAmount(id, amount, documentValue = playerDocument) {
    if (!documentValue || !Number.isFinite(Number(amount))) return false;
    const wanted = String(id || '');
    const lists = [documentValue?.items, documentValue?.player?.items, documentValue?.inventory?.items,
      documentValue?.currencies, documentValue?.player?.currencies, documentValue?.inventory?.currencies];
    for (const list of lists) {
      if (!Array.isArray(list)) continue;
      const matches = list.filter(item => String(item?.item_id || item?.currency_id || item?.id || '') === wanted);
      if (!matches.length) continue;
      matches.forEach((item,index) => {
        const value = index ? 0 : Math.max(0, Number(amount));
        if (item.quantity !== undefined) item.quantity = value;
        else if (item.value !== undefined) item.value = value;
      });
      return true;
    }
    const owners = [documentValue, documentValue?.player, documentValue?.currencies, documentValue?.player?.currencies, documentValue?.wallet];
    for (const owner of owners) {
      if (!owner || !Object.prototype.hasOwnProperty.call(owner,wanted)) continue;
      owner[wanted] = Math.max(0, Number(amount));
      return true;
    }
    return false;
  }

  function updateWalletFromResponse(response, cost) {
    // Fair endpoints often return only the currency changed by that action.
    // Replacing /player/me with such a partial response drops every other
    // balance and makes the next discovered lot fail as "balance unknown".
    for (const part of costParts(cost)) {
      const serverBalance = walletAmount(part.id, response);
      if (serverBalance === null || !setWalletAmount(part.id,serverBalance,playerDocument)) {
        debitWallet(costDocumentFromParts([part]),1,playerDocument);
      }
    }
  }

  function canAffordCost(cost, documentValue = playerDocument) {
    return costParts(cost).every(part => {
      const amount = walletAmount(part.id, documentValue);
      return amount === null || amount >= part.quantity;
    });
  }

  function safeFairPurchase(cost) {
    const parts = costParts(cost);
    return !!parts.length && parts.every(part => part.quantity > 0 &&
      ((part.kind === 'items' && part.id.startsWith('item_')) ||
       (part.kind === 'currencies' && ['cur_gold', 'cur_cap', 'cur_prem'].includes(part.id))));
  }

  function premiumPurchase(cost) {
    return costParts(cost).some(part => part.kind === 'currencies' && part.id === 'cur_prem' && part.quantity > 0);
  }

  function premiumReroll(cost) {
    const parts = costParts(cost);
    return !!parts.length && parts.every(part => part.kind === 'currencies' && part.id === 'cur_prem' && part.quantity > 0);
  }

  function safeReroll(cost, allowPremium) {
    const parts = costParts(cost);
    return (!parts.length || parts.every(part => part.quantity >= 0 && part.kind === 'items' && part.id.startsWith('item_'))) ||
      (allowPremium && premiumReroll(cost));
  }

  function itemFamily(id) {
    let value = String(id || '');
    while (/_(?:pb|bp|\d+)$/i.test(value)) value = value.replace(/_(?:pb|bp|\d+)$/i, '');
    return value;
  }

  function fairRowsForState(state) {
    if (!state) return [];
    // The game returns the actual live slots for each fair. Always include
    // those first: newly added events and slots unlocked by progress do not
    // need a hard-coded currency or event identifier in the script.
    const liveSlotLotIds = new Set((state.fair_slots || []).map(slot => String(slot?.shop_lot_id || '')).filter(Boolean));
    if (state.id === 'fair_default') return fairCatalog.filter(row => {
      const parts = costParts(row.cost);
      return liveSlotLotIds.has(row.lotId) || (row.lotId.startsWith('mf_fairlot_') && !row.lotId.includes('_event_') &&
        (parts.some(part => part.kind === 'currencies') || parts.some(part => part.id === 'item_invest_cur')));
    });
    const families = new Set(costParts(state.fair_reroll_cost).filter(p => p.kind === 'items').map(p => itemFamily(p.id)));
    const overrides = {fair_event_hw:['item_event_hw_cur'], fair_event_nyear:['item_event_nyear_cur']};
    (overrides[state.id] || []).forEach(value => families.add(value));
    return fairCatalog.filter(row => liveSlotLotIds.has(row.lotId) ||
      costParts(row.cost).some(p => p.kind === 'items' && families.has(itemFamily(p.id))));
  }

  let fairViewMode = 'all';

  function userVisibleFair(state) {
    if (!state) return false;
    const id = String(state.id || '').toLowerCase();
    // fair_event_base is reused by the game for the currently running event.
    // New clients may instead expose a named state (for example an autumn
    // fair). Match that state through its live reroll currency/slots so future
    // event names do not require another hard-coded fair id.
    if (id === 'fair_default' || id === 'fair_event_base') return true;
    const code = captureActiveEventCode();
    if (!code) return false;
    const markers = [id,
      ...costParts(state.fair_reroll_cost).map(part => part.id),
      ...(state.fair_slots || []).map(slot => String(slot?.shop_lot_id || ''))
    ].map(value => String(value || '').toLowerCase());
    return markers.some(value => value.includes(`event_${code}`) || value.includes(`_${code}_`) || value.endsWith(`_${code}`));
  }

  function visibleFairStates(documentValue = fairDocument || playerDocument) {
    return fairStates(documentValue).filter(state => userVisibleFair(state) && fairRowsForState(state).length);
  }

  function fairStatesForView(documentValue = fairDocument || playerDocument) {
    const states = visibleFairStates(documentValue);
    if (fairViewMode === 'regular') return states.filter(state => String(state?.id || '') === 'fair_default');
    return states;
  }

  function mediaUrl(value, itemId = '') {
    const raw = String(value || '');
    if (/^https?:\/\//.test(raw)) return raw;
    if (raw) return `https://cdn-prod-art.hwgame.cloud/${raw.replace(/^\/+/, '')}`;
    return itemId ? `${ASSET_BASE}/${itemId}_icon.png` : '';
  }

  function paymentIcon(part) {
    if (!part?.id) return '';
    const folder = part.kind === 'currencies' ? 'currencies' : 'items';
    return `https://cdn-prod-art.hwgame.cloud/${folder}/${part.id}_icon.png`;
  }

  function paymentLabel(id) {
    const known = language === 'en'
      ? {cur_gold:'Gold', cur_cap:'Caps', cur_prem:'Diamonds', item_invest_cur:'Invest coins', item_event_hw_cur:'Halloween', item_event_nyear_cur:'New Year', item_event_autumn_cur:'Autumn Leaves', item_event_autumn_cur_pb:'Golden Leaves'}
      : {cur_gold:'Золото', cur_cap:'Крышки', cur_prem:'Алмазы', item_invest_cur:'Инвест-монеты', item_event_hw_cur:'Хэллоуин', item_event_nyear_cur:'Новый год', item_event_autumn_cur:'Осенние листья', item_event_autumn_cur_pb:'Золотые листья'};
    return known[id] || String(id || '').replace(/^item_/, '').replace(/^cur_/, '').replace(/_/g, ' ');
  }

  function fairIconHtml(url, className = 'hk-fair-icon') {
    return `<img class="${className}" src="${escapeHtml(url)}" alt="" onerror="this.style.visibility='hidden'">`;
  }

  function shopLotIconHtml(row) {
    if (!row) return '';
    const urls = [...new Set([row.icon, ...iconUrls(row.rewardId)].filter(Boolean))];
    const first = urls.shift() || '';
    const quantity = Math.max(0, Number(row.rewardQuantity || 0));
    return `<span class="hk-today-lot-visual"><img class="hk-today-lot-image" src="${escapeHtml(first)}" data-fallbacks="${escapeHtml(JSON.stringify(urls))}" alt=""><small>${quantity ? `×${quantity.toLocaleString(locale())}` : ''}</small></span>`;
  }

  function normalizeFairCatalog(documentValue) {
    return (documentValue?.shop_lots || []).flatMap(lot => {
      const view = lot?.lot_view || {};
      const content = (view.content_view || [])[0];
      const parts = costParts(lot?.cost);
      if (String(view.type || '').toLowerCase() !== 'fair' || lot.external_cost || !content || !parts.length || parts.some(p => p.quantity <= 0)) return [];
      const rewardId = String(content.id || '');
      return [{lotId:String(lot.id || ''), name:String(view.name || rewardId || lot.id), rewardId,
        rewardQuantity:Math.trunc(Number(content.quantity || 0)), cost:lot.cost || {}, safe:safeFairPurchase(lot.cost), premium:premiumPurchase(lot.cost),
        icon:mediaUrl(view.icon_card || view.icon || content.icon_card || content.icon, rewardId)}];
    });
  }

  async function gameRetryDelay(ms){
    const delay=Math.max(0,Number(ms)||0), signal=hkRunner.running?hkRunner.signal:null;
    if(!delay)return;
    if(!signal){await sleep(delay);return;}
    if(signal.aborted)throw new DOMException('Aborted','AbortError');
    await new Promise((resolve,reject)=>{let timer=null;const abort=()=>{if(timer)clearTimeout(timer);signal.removeEventListener('abort',abort);reject(new DOMException('Aborted','AbortError'));};timer=setTimeout(()=>{signal.removeEventListener('abort',abort);resolve();},delay);signal.addEventListener('abort',abort,{once:true});});
  }

  async function gameFetchText(request,url,init={},timeoutMs=18000){
    const controller=new AbortController(), runnerSignal=hkRunner.running?hkRunner.signal:null;
    let timedOut=false, timer=null, detach=null;
    if(runnerSignal){
      const abort=()=>controller.abort('runner');
      if(runnerSignal.aborted)abort();else{runnerSignal.addEventListener('abort',abort,{once:true});detach=()=>runnerSignal.removeEventListener('abort',abort);}
    }
    timer=setTimeout(()=>{timedOut=true;controller.abort('timeout');},Math.max(1000,Number(timeoutMs)||18000));
    try{
      const response=await request(url,{...init,signal:controller.signal});
      const text=await response.text();
      return{response,text};
    }catch(error){
      if(runnerSignal?.aborted)throw new DOMException('Aborted','AbortError');
      if(timedOut){const timeoutError=new Error(either('Тайм-аут запроса к игре','Game request timed out'));timeoutError.name='HKNetworkTimeout';throw timeoutError;}
      throw error;
    }finally{if(timer)clearTimeout(timer);try{detach?.();}catch(_){}}
  }

  async function apiJsonCore(path, method = 'GET', body = null, retryAuthorization = true, retryNetwork = 3) {
    const maxRetries = retryNetwork === true ? GAME_REQUEST_RETRY_DELAYS_MS.length : retryNetwork === false ? 0 : Math.max(0, Math.trunc(Number(retryNetwork) || 0));
    let authRetryLeft = retryAuthorization ? 1 : 0;
    let attempt = 0, lockAttempt = 0;
    while (true) {
      const authorized = await ensureGameAuthorization(false, `api:${path}`);
      if (!apiBase || !authorized || !apiHeaders.Authorization) throw new Error('Нет подключения к игре. Обновите страницу.');
      const request = nativeNetworkFetch || window.fetch.bind(window);
      const started = performance.now();
      let response,text;
      try {
        ({response,text}=await gameFetchText(request,`${apiBase}${path}`,{method,headers:{...apiHeaders},body:body == null ? undefined : JSON.stringify(body)},18000));
      } catch (error) {
        if(error?.name==='AbortError'||hkRunner.signal?.aborted)throw error;
        recordDiagnostic('game-request-network-error',{path,method,attempt:attempt+1,error:error?.message || error});
        if (attempt < maxRetries) {
          const delay = GAME_REQUEST_RETRY_DELAYS_MS[Math.min(attempt, GAME_REQUEST_RETRY_DELAYS_MS.length - 1)] || 6000;
          attempt += 1; await gameRetryDelay(delay); continue;
        }
        setHealth('game', false, error?.name==='HKNetworkTimeout'?'тайм-аут':'ошибка сети');
        throw new Error(`${path}: ${error?.message || error}`);
      }
      let value; try { value = JSON.parse(text); } catch (_) { value = null; }
      recordDiagnostic('game-request',{path,method,status:response.status,attempt:attempt+1,durationMs:Math.round(performance.now()-started)});
      if ((response.status === 401 || response.status === 403) && authRetryLeft > 0) {
        authRetryLeft -= 1;
        const refreshed = await ensureGameAuthorization(true, `http-${response.status}:${path}`);
        if (refreshed) { attempt = 0; continue; }
      }
      const lockedText=String(value?.description||value?.message||text||'').toLowerCase();
      const playerLocked=/player state is locked|state is locked by (?:other|another) request|player.*locked.*request/.test(lockedText);
      if(playerLocked&&lockAttempt<3){
        const delay=[650,1400,3000][lockAttempt++]||3000;
        recordDiagnostic('game-request-player-locked',{path,method,status:response.status,lockAttempt,delay});
        await gameRetryDelay(delay);continue;
      }
      const transient = response.status === 408 || response.status === 425 || response.status === 429 || response.status >= 500;
      if (transient && attempt < maxRetries) {
        const delay = GAME_REQUEST_RETRY_DELAYS_MS[Math.min(attempt, GAME_REQUEST_RETRY_DELAYS_MS.length - 1)] || 6000;
        attempt += 1; await gameRetryDelay(delay); continue;
      }
      if (!response.ok) {
        if (response.status === 401 || response.status === 403) setHealth('auth', false, 'сессия истекла');
        setHealth('game', false, `HTTP ${response.status}`);
        const error=new Error(value?.description || value?.message || `HTTP ${response.status}: ${text.slice(0,160)}`);
        error.name='HKGameApiError'; error.httpStatus=response.status; error.apiData=value; error.apiPath=path;
        throw error;
      }
      if (!value || typeof value !== 'object') throw new Error('Сервер вернул некорректный ответ');
      setHealth('game', true, 'игра отвечает');
      setHealth('auth', true, 'авторизация активна');
      if (path === '/player/me') {
        const partial = !!(body && Array.isArray(body.arguments));
        if (partial) hkStateStore.merge(value, 'api:player/me-partial'); else { hkStateStore.replace(value, 'api:player/me'); value = hkStateStore.snapshot || value; }
        playerDocument = hkStateStore.snapshot || value || playerDocument;
      } else if (hkIsMutationRequest(path, method)) {
        hkStateStore.merge(value, `api:${path}`);
        playerDocument = hkStateStore.snapshot || playerDocument;
      }
      hkGameBridge.noteMutation(path, method);
      return value;
    }
  }

  const HK_MUTATION_GATE_REV = 'stage1-20260919-r4';

  const HK_READ_ONLY_POST_PATHS = new Set([
    '/player/me',
    '/player/hamster/lvlUp/view',
    '/player/building',
    '/shop/view',
    '/business/values',
    '/business_items',
    '/cities',
    '/client_config',
    '/events',
    '/items',
    '/leaderboard',
    '/premium',
    '/bonuses/view',
    '/alliance/list',
    '/clan/skill_lines/stats',
  ]);

  function hkNormalizedApiPath(path) {
    const value = String(path || '');
    const q = value.indexOf('?');
    return q >= 0 ? value.slice(0, q) : value;
  }

  function hkIsMutationRequest(path, method = 'GET') {
    const verb = String(method || 'GET').toUpperCase();
    if (verb === 'GET' || verb === 'HEAD' || verb === 'OPTIONS') return false;
    return !HK_READ_ONLY_POST_PATHS.has(hkNormalizedApiPath(path));
  }

  const hkMutationGate = (() => {
    let tail = Promise.resolve();
    let sequence = 0;
    let active = null;
    const state = {
      pending: 0,
      completed: 0,
      failed: 0,
      lastPath: '',
      activePath: ''
    };

    const safeDiagnostic = (kind, payload) => {
      try { recordDiagnostic(kind, payload); } catch (_) {}
    };

    const run = async (path, task) => {
      const id = ++sequence;
      const normalizedPath = hkNormalizedApiPath(path);
      state.pending += 1;

      let release;
      const turn = new Promise(resolve => { release = resolve; });
      const previous = tail;
      tail = turn;

      await previous.catch(() => {});
      state.pending = Math.max(0, state.pending - 1);
      state.activePath = normalizedPath;
      state.lastPath = normalizedPath;
      active = { id, path: normalizedPath, startedAt: Date.now() };
      safeDiagnostic('mutation-start', { id, path: normalizedPath, pending: state.pending });

      try {
        // Serialization is neutral: module-specific Pause/Stop stays in the
        // calling runner. A paused Growth task must not freeze unrelated modules.
        // Internal apiJsonCore retries remain inside this same queue turn.
        const value = await task();
        state.completed += 1;
        safeDiagnostic('mutation-finish', {
          id,
          path: normalizedPath,
          durationMs: Date.now() - active.startedAt
        });
        return value;
      } catch (error) {
        state.failed += 1;
        safeDiagnostic('mutation-error', {
          id,
          path: normalizedPath,
          error: error?.message || String(error)
        });
        throw error;
      } finally {
        active = null;
        state.activePath = '';
        release();
      }
    };

    return {
      revision: HK_MUTATION_GATE_REV,
      state,
      run,
      get active() { return active; }
    };
  })();

  const HK_MUTATION_GATE_ORDER_REV = 'mutation-gate-order-20260920-r1';
  runtime.mutationGate = hkMutationGate;

  async function apiJson(path, method = 'GET', body = null, retryAuthorization = true, retryNetwork = 3) {
    if (!hkIsMutationRequest(path, method)) {
      return apiJsonCore(path, method, body, retryAuthorization, retryNetwork);
    }
    return hkMutationGate.run(
      path,
      () => apiJsonCore(path, method, body, retryAuthorization, 0)
    );
  }

  async function hkAuthoritativePlayerRead(reason='mutation-group') {
    const value = await apiJson('/player/me','POST');
    playerDocument = hkStateStore.snapshot || value || playerDocument;
    recordDiagnostic('authoritative-player-read',{reason,revision:hkStateStore.exportSummary().revision});
    return playerDocument;
  }

  function deepObjects(value, depth = 0, output = []) {
    if (depth > 6 || value == null) return output;
    if (Array.isArray(value)) { for (const item of value) deepObjects(item, depth + 1, output); return output; }
    if (typeof value !== 'object') return output;
    output.push(value);
    for (const child of Object.values(value)) if (child && typeof child === 'object') deepObjects(child, depth + 1, output);
    return output;
  }

  function firstText(...values) {
    for (const value of values) { const text = clean(value); if (text) return text.slice(0, 100); }
    return '';
  }

  function firstFinite(...values) {
    for (const value of values) { const parsed = Number(value); if (Number.isFinite(parsed) && parsed >= 0) return parsed; }
    return 0;
  }

  // HK_CLAN_WAR_HP_V1
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

  function leaderboardArrays(documentValue) {
    const arrays = [];
    function walk(value, depth = 0) {
      if (depth > 6 || value == null) return;
      if (Array.isArray(value)) { if (value.some(row => row && typeof row === 'object')) arrays.push(value); for (const row of value) walk(row, depth + 1); return; }
      if (typeof value === 'object') for (const child of Object.values(value)) walk(child, depth + 1);
    }
    walk(documentValue); return arrays.sort((a,b) => b.length - a.length);
  }

  function normalizePublicRanking(documentValue, kind) {
    const arrays = leaderboardArrays(documentValue);
    for (const list of arrays) {
      const rows = list.map((row,index) => {
        if (!row || typeof row !== 'object') return null;
        const entity = row.player || row.user || row.clan || row.alliance || row.member || row;
        const name = firstText(entity.nickname, entity.name, entity.title, row.nickname, row.name, row.clan_name, row.alliance_name);
        const rank = Math.trunc(firstFinite(row.rank, row.place, row.position, entity.rank) || index + 1);
        const preferred = kind === 'power' ? [row.power, entity.power, row.value, row.score]
          : kind === 'influence' ? [row.influence, entity.influence, row.level, entity.level, row.value, row.score]
          : [row.score, row.points, row.value, entity.score, entity.points, entity.power, entity.level];
        const value = firstFinite(...preferred);
        return name && rank >= 1 && rank <= 100 ? {rank,name,value} : null;
      }).filter(Boolean).slice(0,100);
      if (rows.length) return rows;
    }
    return [];
  }

  // HK_ALLIANCE_RATINGS_V1
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

  async function publicSnapshotServerJson(documentValue, retry = true) {
    return licensedServerJson(PUBLIC_SNAPSHOT_API, '', documentValue, retry, 'public-snapshot');
  }

  let bossSnapshot = null;
  let bossLastReadAt = 0;
  let warSnapshot = null;
  let warLastReadAt = 0;

  function warTimestamp(value) {
    const number=Number(value||0);
    if(!Number.isFinite(number)||number<=0)return '';
    const ms=number<1e12?number*1000:number;
    try{return new Date(ms).toLocaleString(locale(),{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'});}catch(_){return '';}
  }

  async function readPublicWar() {
    let endpointRead = false;
    for (const path of ['/clan/active_battles','/clan/active_defense_wars']) {
      try { const value = await apiJson(path, 'GET', null, true, 1); endpointRead = true; const war = normalizePublicWar(value); if (war) return {read:true,war}; }
      catch (_) {}
    }
    return {read:endpointRead,war:null};
  }

  function bossStateRows(documentValue = bossSnapshot || hkStateStore.snapshot || playerDocument) {
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
    
      function renderWars() {
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

  // HK_ALLIANCE_RATINGS_V2
  // Alliance totals are built from the clans that belong to each alliance.
  // Defense/defence ("Оборона" in the game) comes from the alliance/clan list;
  // clan power and influence are joined by clan name from the game's clan leaderboards.
  let discoveredClanPowerLeaderboardType = '';

  function allianceNameKey(value) {
    return String(value || '').normalize('NFKC').trim().replace(/\s+/g,' ').toLowerCase();
  }

  function allianceObjectName(value) {
    if(!value||typeof value!=='object')return '';
    const node=value.alliance||value.alliance_info||value.allianceInfo||value;
    return firstText(
      node?.name,node?.title,node?.alliance_name,node?.allianceName,
      value.alliance_name,value.allianceName,value.name,value.title
    );
  }

  function clanObjectName(value) {
    if(!value||typeof value!=='object')return '';
    const node=value.clan||value.clan_info||value.clanInfo||value;
    return firstText(
      node?.name,node?.title,node?.clan_name,node?.clanName,
      value.clan_name,value.clanName,value.name,value.title
    );
  }

  function clanObjectId(value) {
    if(!value||typeof value!=='object')return '';
    const node=value.clan||value.clan_info||value.clanInfo||value;
    return firstText(
      node?.clan_id,node?.clanId,node?.id,node?.uuid,
      value.clan_id,value.clanId,value.id,value.uuid
    );
  }

  function clanMemberCount(value) {
    if(!value||typeof value!=='object')return null;
    const node=value.clan||value.clan_info||value.clanInfo||value;
    return metricFromObject(node,[
      'members_count','membersCount','member_count','memberCount',
      'players_count','playersCount','participants_count','participantsCount',
      'members','participants'
    ]) ?? metricFromObject(value,[
      'members_count','membersCount','member_count','memberCount',
      'players_count','playersCount','participants_count','participantsCount'
    ]);
  }

  function directClanMetric(value,kind) {
    if(!value||typeof value!=='object')return null;
    const node=value.clan||value.clan_info||value.clanInfo||value;
    const keys=ALLIANCE_RATING_METRICS[kind]||[];
    return metricFromObject(node,keys) ?? metricFromObject(value,keys);
  }

  function likelyClanArray(list) {
    if(!Array.isArray(list)||!list.length||list.length>20)return false;
    let named=0,clanish=0;
    for(const item of list.slice(0,8)){
      if(!item||typeof item!=='object')continue;
      if(clanObjectName(item))named+=1;
      const keys=new Set([
        ...Object.keys(item),
        ...Object.keys(item.clan||item.clan_info||item.clanInfo||{})
      ].map(String));
      if(
        item.clan||item.clan_info||item.clanInfo||
        keys.has('clan_id')||keys.has('clanId')||
        keys.has('defense')||keys.has('defence')||
        keys.has('defense_points')||keys.has('defence_points')||
        keys.has('player_level')||keys.has('hamsters_power')||
        keys.has('members_count')||keys.has('membersCount')
      )clanish+=1;
    }
    return named>0 && (clanish>0 || named===list.length);
  }

  function allianceClanRows(value) {
    if(!value||typeof value!=='object')return [];
    const sources=[value.alliance||null,value.alliance_info||null,value.allianceInfo||null,value].filter(Boolean);
    const preferred=[
      'clans','alliance_clans','allianceClans','clan_list','clanList',
      'member_clans','memberClans','participants'
    ];
    for(const source of sources){
      for(const key of preferred){
        const list=source?.[key];
        if(likelyClanArray(list))return list;
      }
    }
    for(const source of sources){
      for(const child of Object.values(source||{})){
        if(likelyClanArray(child))return child;
      }
    }
    const singles=[];
    for(const source of sources){
      for(const key of ['core_clan','coreClan','leader_clan','leaderClan','clan']){
        const row=source?.[key];
        if(row&&typeof row==='object'&&clanObjectName(row))singles.push(row);
      }
    }
    return singles;
  }

  function allianceRecords(documentValue) {
    const output=[],seen=new Set();
    for(const value of deepObjects(documentValue)){
      if(!value||typeof value!=='object')continue;
      const name=allianceObjectName(value);
      const clans=allianceClanRows(value);
      if(!name||!clans.length)continue;
      const parsedClans=[];
      const clanSeen=new Set();
      for(const raw of clans){
        const clanName=clanObjectName(raw);
        if(!clanName)continue;
        const clanKey=allianceNameKey(clanName);
        if(!clanKey||clanSeen.has(clanKey))continue;
        clanSeen.add(clanKey);
        parsedClans.push({
          name:clanName,
          key:clanKey,
          id:clanObjectId(raw),
          members:clanMemberCount(raw),
          power:directClanMetric(raw,'alliance_power'),
          influence:directClanMetric(raw,'alliance_influence'),
          defense:directClanMetric(raw,'alliance_defense')
        });
      }
      if(!parsedClans.length)continue;
      const key=allianceNameKey(name);
      if(!key||seen.has(key))continue;
      seen.add(key);
      output.push({
        name,key,clans:parsedClans,
        power:metricFromObject(value.alliance||value,ALLIANCE_RATING_METRICS.alliance_power),
        influence:metricFromObject(value.alliance||value,ALLIANCE_RATING_METRICS.alliance_influence),
        defense:metricFromObject(value.alliance||value,ALLIANCE_RATING_METRICS.alliance_defense)
      });
    }
    return output;
  }

  function clanMetricRows(documentValue,kind) {
    const arrays=leaderboardArrays(documentValue);
    for(const list of arrays){
      const rows=list.map((row,index)=>{
        if(!row||typeof row!=='object')return null;
        const entity=row.clan||row.clan_info||row.clanInfo||row;
        const name=clanObjectName(row);
        if(!name)return null;
        const rank=Math.trunc(firstFinite(row.rank,row.place,row.position,entity.rank)||index+1);
        let value=null;
        if(kind==='power'){
          value=metricFromObject(entity,ALLIANCE_RATING_METRICS.alliance_power)
            ?? metricFromObject(row,ALLIANCE_RATING_METRICS.alliance_power)
            ?? finiteMetric(row.value) ?? finiteMetric(row.score);
        }else{
          value=metricFromObject(entity,ALLIANCE_RATING_METRICS.alliance_influence)
            ?? metricFromObject(row,ALLIANCE_RATING_METRICS.alliance_influence)
            ?? finiteMetric(row.value) ?? finiteMetric(row.score);
        }
        return rank>=1&&value!==null?{rank,name,value}:null;
      }).filter(Boolean);
      if(rows.length)return rows.slice(0,200);
    }
    return [];
  }

  function clanRowsMap(rows) {
    return new Map((Array.isArray(rows)?rows:[])
      .filter(row=>row&&row.name&&Number.isFinite(Number(row.value)))
      .map(row=>[allianceNameKey(row.name),Number(row.value)]));
  }

  async function readClanPowerRows() {
    const candidates=discoveredClanPowerLeaderboardType
      ? [discoveredClanPowerLeaderboardType]
      : ['clan_hamsters_power_lb','clan_hamster_power_lb','clan_power_lb','clans_hamsters_power_lb'];
    for(const leaderboard_type of candidates){
      try{
        const value=await apiJson('/leaderboard','POST',{leaderboard_type},true,1);
        const rows=clanMetricRows(value,'power');
        if(rows.length){
          discoveredClanPowerLeaderboardType=leaderboard_type;
          return rows;
        }
      }catch(_){}
    }
    return [];
  }

  function completeAllianceSum(alliance,metric,map) {
    const direct=finiteMetric(alliance?.[metric]);
    if(direct!==null&&direct>0)return direct;
    let total=0,covered=0;
    for(const clan of alliance.clans||[]){
      let value=finiteMetric(clan?.[metric]);
      if((value===null||value<=0)&&map)value=finiteMetric(map.get(clan.key));
      if(value===null||value<0)continue;
      total+=value;covered+=1;
    }
    // Never publish a partial total. A missing clan must not silently reduce
    // an alliance's power/influence/defense.
    return covered===(alliance.clans||[]).length&&covered>0?total:null;
  }

  function buildAllianceRatings(allianceDocument,clanInfluenceRows,clanPowerRows) {
    const alliances=allianceRecords(allianceDocument);
    const influenceMap=clanRowsMap(clanInfluenceRows);
    const powerMap=clanRowsMap(clanPowerRows);
    const totals=alliances.map(alliance=>({
      name:alliance.name,
      clans:alliance.clans.length,
      members:alliance.clans.reduce((sum,row)=>sum+(Number(row.members)||0),0),
      alliance_power:completeAllianceSum(alliance,'power',powerMap),
      alliance_influence:completeAllianceSum(alliance,'influence',influenceMap),
      alliance_defense:completeAllianceSum(alliance,'defense',null)
    }));
    const result={};
    for(const kind of ['alliance_power','alliance_influence','alliance_defense']){
      const rows=totals
        .filter(row=>Number.isFinite(row[kind])&&row[kind]>0)
        .sort((a,b)=>b[kind]-a[kind]||a.name.localeCompare(b.name))
        .slice(0,100)
        .map((row,index)=>({rank:index+1,name:row.name,value:row[kind]}));
      if(rows.length)result[kind]=rows;
    }
    try{
      recordDiagnostic('alliance-rating-v2',{
        alliances:alliances.length,
        power:result.alliance_power?.length||0,
        influence:result.alliance_influence?.length||0,
        defense:result.alliance_defense?.length||0,
        powerLeaderboard:discoveredClanPowerLeaderboardType||''
      });
    }catch(_){}
    return result;
  }

  async function readPublicRatings() {
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
      clanInfluenceRows=clanMetricRows(value,'influence');
      const publicRows=normalizePublicRanking(value,'clans');
      if(publicRows.length)ratings.clans=publicRows;
    }catch(_){}

    try{
      const [allianceDocument,clanPowerRows]=await Promise.all([
        apiJson('/alliance/list','GET',null,true,1),
        readClanPowerRows()
      ]);
      Object.assign(ratings,buildAllianceRatings(allianceDocument,clanInfluenceRows,clanPowerRows));
    }catch(error){
      try{recordDiagnostic('alliance-rating-v2-error',{message:error?.message||String(error)});}catch(_){}
    }
    return ratings;
  }

  // HK_PUBLIC_WAR_ALLIANCE_V4
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

  async function collectPublicSnapshot(force = false) {
    if (publicSnapshotPromise || !licenseState.allowed || !licenseState.token || !apiHeaders.Authorization) return publicSnapshotPromise;
    if (!force && Date.now() - lastPublicSnapshot < PUBLIC_SNAPSHOT_INTERVAL_MS) return null;
    publicSnapshotPromise = (async () => {
      try {
        const [warResult, ratings] = await Promise.all([readPublicWarV4(), readPublicRatingsV4()]);
        const payload = {ratings}; if (warResult.read) payload.war = warResult.war;
        if (!warResult.read && !Object.keys(ratings).length) return;
        await publicSnapshotServerJson(payload); lastPublicSnapshot = Date.now();
      } catch (error) { console.warn('[HK] public snapshot failed', error); }
      finally { publicSnapshotPromise = null; }
    })();
    return publicSnapshotPromise;
  }

  async function loadFair() {
    if (!requireLicense()) return;
    try {
      log('Считываю ярмарки…');
      playerDocument = await apiJson('/player/me', 'POST');
      fairDocument = playerDocument;
      shopViewDocument = await apiJson('/shop/view', 'GET');
      fairCatalog = normalizeFairCatalog(shopViewDocument);
      const visibleFairs = fairStatesForView();
      if (!visibleFairs.some(state => state.id === selectedFairId)) selectedFairId = visibleFairs[0]?.id || '';
      selectedFairLots.clear();
      selectedFairSlotRules.clear();
      renderFair();
      log(`Ярмарка считана: ${visibleFairs.length} разделов, ${fairCatalog.length} лотов`, 'ok');
    } catch (error) { log(`Ошибка ярмарки: ${error.message}`, 'bad'); }
  }

  function costVisual(cost, multiplier = 1) {
    const parts = costParts(cost);
    if (!parts.length) return '<span>0</span>';
    return parts.map(part => `${fairIconHtml(paymentIcon(part), 'hk-price-icon')}<b>${(part.quantity * multiplier).toLocaleString(locale())}</b>`).join('');
  }

  function addProjectedCost(target, part, multiplier = 1) {
    if (!part?.id) return;
    const key = `${part.kind}|${part.id}`;
    const current = target.get(key) || {...part, quantity:0};
    current.quantity += Math.max(0, Number(part.quantity || 0)) * Math.max(0, Number(multiplier || 0));
    target.set(key, current);
  }

  function walletForecastHtml(parts) {
    const values = [...parts.values()].filter(part => part?.id).sort((a, b) => a.id.localeCompare(b.id));
    if (!values.length) return '';
    return `<div class="hk-wallet-forecast">${values.map(part => {
      const balance = walletAmount(part.id);
      const spend = Math.max(0, Number(part.quantity || 0));
      const known = balance !== null;
      return `<div class="hk-wallet-row">
        <span class="hk-wallet-currency">${fairIconHtml(paymentIcon(part), 'hk-price-icon')}<b>${escapeHtml(paymentLabel(part.id))}</b></span>
        <span>${tr('balance')}: <b>${known ? balance.toLocaleString(locale()) : '—'}</b> · ${either('Макс. возможный расход','Maximum possible spend')}: <b>${spend.toLocaleString(locale())}</b></span>
      </div>`;
    }).join('')}</div>`;
  }

  function fairProjectedCosts() {
    const totals = new Map();
    const state = fairState(selectedFairId);
    const rows = fairRowsForState(state);
    const selectedRows = rows.filter(row => selectedFairLots.has(row.lotId));
    const buyLimit = Math.max(1, Number(root?.querySelector('#hk-fair-buy-limit')?.value || 1));
    const rerollLimit = Math.max(0, Number(root?.querySelector('#hk-fair-reroll-limit')?.value || 0));
    const relevantRows = selectedRows.length ? selectedRows : rows;
    const maximumLots = new Map();
    for (const row of relevantRows) for (const part of costParts(row.cost)) {
      const key = `${part.kind}|${part.id}`;
      const current = maximumLots.get(key);
      if (!current || part.quantity > current.quantity) maximumLots.set(key, {...part});
    }
    for (const part of maximumLots.values()) addProjectedCost(totals, part, selectedRows.length ? buyLimit : 0);
    for (const part of costParts(state?.fair_reroll_cost)) addProjectedCost(totals, part, rerollLimit);
    return totals;
  }

  function renderFair() {
    if (!fairTypes || !fairLots) return;
    if (!fairCatalog.length) {
      fairTypes.innerHTML = `<p class="hk-muted">${tr('readFirst')}</p>`;
      fairLots.innerHTML = '';
      const currencyBar = root?.querySelector('#hk-fair-currencies'); if (currencyBar) currencyBar.innerHTML = '';
      updateFairControls(); return;
    }
    const states = fairStatesForView();
    fairTypes.innerHTML = states.map(state => {
      const firstLot = fairRowsForState(state).find(row => (state.fair_slots || []).some(slot => slot.shop_lot_id === row.lotId)) || fairRowsForState(state)[0];
      return `<button class="hk-fair-type ${state.id === selectedFairId ? 'selected' : ''}" data-fair="${escapeHtml(state.id)}">
        ${fairIconHtml(firstLot?.icon || '')}<span>${costVisual(state.fair_reroll_cost)}</span></button>`;
    }).join('') || `<p class="hk-muted">${tr('noFairs')}</p>`;
    fairTypes.querySelectorAll('[data-fair]').forEach(button => button.onclick = () => {
      selectedFairId = button.dataset.fair; selectedFairLots.clear(); selectedFairSlotRules.clear(); selectedFairCurrency = ''; renderFair();
    });
    const query = clean(root?.querySelector('#hk-fair-search')?.value).toLowerCase();
    const allRows = fairRowsForState(fairState(selectedFairId));
    const currencyIds = [...new Set(allRows.flatMap(row => costParts(row.cost).map(part => part.id)).filter(Boolean))];
    if (selectedFairCurrency && !currencyIds.includes(selectedFairCurrency)) selectedFairCurrency = '';
    const currencyBar = root?.querySelector('#hk-fair-currencies');
    if (currencyBar) {
      currencyBar.innerHTML = `<button class="${selectedFairCurrency ? '' : 'selected'}" data-currency="">${tr('all')}</button>` + currencyIds.map(id => {
        const part = allRows.flatMap(row => costParts(row.cost)).find(value => value.id === id);
        return `<button class="${selectedFairCurrency === id ? 'selected' : ''}" data-currency="${escapeHtml(id)}">${fairIconHtml(paymentIcon(part), 'hk-price-icon')}<span>${escapeHtml(paymentLabel(id))}</span></button>`;
      }).join('');
      currencyBar.querySelectorAll('[data-currency]').forEach(button => button.onclick = () => { selectedFairCurrency = button.dataset.currency; renderFair(); });
    }
    const rows = allRows.filter(row => (!selectedFairCurrency || costParts(row.cost).some(part => part.id === selectedFairCurrency)) &&
      (!query || `${row.name} ${row.rewardId} ${row.lotId}`.toLowerCase().includes(query)));
    fairLots.innerHTML = rows.map(row => `<button class="hk-lot ${selectedFairLots.has(row.lotId) ? 'selected' : ''} ${row.premium ? 'premium' : ''} ${row.safe ? '' : 'locked'}" data-lot="${escapeHtml(row.lotId)}">
      ${row.premium ? '<i class="hk-premium-mark">💎</i>' : ''}${fairIconHtml(row.icon)}<b>×${row.rewardQuantity.toLocaleString(locale())}</b><span>${costVisual(row.cost)}</span>${row.safe ? '' : `<small>${tr('blocked')}</small>`}</button>`).join('') || `<p class="hk-muted">${tr('noLots')}</p>`;
    fairLots.querySelectorAll('[data-lot]').forEach(button => button.onclick = () => {
      const row = fairCatalog.find(value => value.lotId === button.dataset.lot);
      if (!row?.safe) { log(either('Этот лот заблокирован: неизвестная валюта', 'This lot is blocked: unknown currency'), 'warn'); return; }
      if (selectedFairLots.has(row.lotId)) {
        selectedFairLots.delete(row.lotId);
        selectedFairSlotRules.delete(row.lotId);
      } else {
        selectedFairLots.add(row.lotId);
        const options = fairSlotOptions();
        selectedFairSlotRules.set(row.lotId, {regular:options.some(value => !value.vip), vip:options.some(value => value.vip)});
      }
      renderFair();
    });
    renderFairSlotRules();
    updateFairControls();
  }

  function fairSlotOptions(state = fairState(selectedFairId)) {
    const fairConfigs = shopViewDocument?.fairs || shopViewDocument?.fair || [];
    const config = (Array.isArray(fairConfigs) ? fairConfigs : []).find(value => String(value?.id) === String(state?.id));
    const metaById = new Map((config?.fair_slots || []).map(slot => [String(slot?.id), slot]));
    return [...(state?.fair_slots || [])]
      .sort((a, b) => Number(a?.id ?? 0) - Number(b?.id ?? 0))
      .map((slot, index) => ({slot, index, key:String(index), vip:Boolean(slot?.is_vip || metaById.get(String(slot?.id))?.is_vip)}));
  }

  function renderFairSlotRules() {
    if (!fairSlotRules) return;
    const slots = fairSlotOptions();
    if (!selectedFairLots.size || !slots.length) {
      fairSlotRules.innerHTML = '';
      fairSlotRules.style.display = 'none';
      return;
    }
    fairSlotRules.style.display = '';
    const hasRegular = slots.some(value => !value.vip);
    const hasVip = slots.some(value => value.vip);
    for (const lotId of selectedFairLots) {
      if (!selectedFairSlotRules.has(lotId)) selectedFairSlotRules.set(lotId, {regular:hasRegular, vip:hasVip});
    }
    fairSlotRules.innerHTML = `<h3>${tr('allowedCells')}</h3><p class="hk-muted">${tr('selectCellsHint')}</p>` +
      [...selectedFairLots].map(lotId => {
        const row = fairCatalog.find(value => value.lotId === lotId);
        const allowed = selectedFairSlotRules.get(lotId) || {regular:hasRegular, vip:hasVip};
        return `<div class="hk-slot-rule"><div class="hk-slot-product">${fairIconHtml(row?.icon || '', 'hk-price-icon')}<b>×${Number(row?.rewardQuantity || 0).toLocaleString(locale())}</b></div>
          <div class="hk-slot-buttons"><button class="${allowed.regular ? 'selected' : ''}" data-rule-lot="${escapeHtml(lotId)}" data-rule-group="regular" ${hasRegular ? '' : 'disabled'}>${tr('regularSlots')}: ${tr(allowed.regular ? 'yes' : 'no')}</button>
          <button class="vip ${allowed.vip ? 'selected' : ''}" data-rule-lot="${escapeHtml(lotId)}" data-rule-group="vip" ${hasVip ? '' : 'disabled'}>♛ ${tr('vipSlots')}: ${tr(allowed.vip ? 'yes' : 'no')}</button></div></div>`;
      }).join('');
    fairSlotRules.querySelectorAll('[data-rule-lot]').forEach(button => button.onclick = () => {
      const allowed = selectedFairSlotRules.get(button.dataset.ruleLot) || {regular:hasRegular, vip:hasVip};
      allowed[button.dataset.ruleGroup] = !allowed[button.dataset.ruleGroup];
      selectedFairSlotRules.set(button.dataset.ruleLot, allowed);
      renderFairSlotRules(); updateFairControls();
    });
  }

  function updateFairControls() {
    const selected = root?.querySelector('#hk-fair-selected');
    if (selected) selected.innerHTML = `<b>${tr('selectedLots', {n:selectedFairLots.size})}</b>${walletForecastHtml(fairProjectedCosts())}`;
    const start = root?.querySelector('#hk-fair-start');
    const rulesValid = [...selectedFairLots].every(lotId => {
      const rule = selectedFairSlotRules.get(lotId); return Boolean(rule?.regular || rule?.vip);
    });
    if (start) start.disabled = fairRunning || !selectedFairId || !selectedFairLots.size || !rulesValid;
    const stop = root?.querySelector('#hk-fair-stop');
    if (stop) stop.disabled = !fairRunning;
  }

  function fairComboSettings() {
    return {
      exactLots:Math.max(0, Number(root?.querySelector('#hk-fair-exact-lots')?.value || 0))
    };
  }

  function availableFairBonusLots(exactLots = fairComboSettings().exactLots) {
    return exactLots >= 9 ? [5, 10, 30] : exactLots >= 6 ? [5, 10] : exactLots >= 3 ? [5] : [];
  }

  function renderFairBonusChoices() {
    const box = root?.querySelector('#hk-fair-bonus-lots'); if (!box) return;
    const available = new Set(availableFairBonusLots());
    box.innerHTML = `<span>${tr('fairBonusLots')}</span><div>${[5,10,30].map(quantity =>
      `<label class="hk-check ${available.has(quantity) ? 'available' : 'unavailable'}"><input type="checkbox" data-fair-bonus="${quantity}" ${selectedFairBonusLots.has(quantity) ? 'checked' : ''} ${available.has(quantity) ? '' : 'disabled'}><b>×${quantity}</b></label>`).join('')}</div>`;
    box.querySelectorAll('[data-fair-bonus]').forEach(input => input.onchange = () => {
      const quantity = Number(input.dataset.fairBonus);
      if (input.checked) selectedFairBonusLots.add(quantity); else selectedFairBonusLots.delete(quantity);
    });
  }

  function fairPresets() {
    const value = load().fairPresets;
    return value && typeof value === 'object' && !Array.isArray(value) ? value : {};
  }

  function refreshFairPresets(selectName = '') {
    if (!fairPresetSelect) return;
    const names = Object.keys(fairPresets()).sort((a, b) => a.localeCompare(b, locale()));
    fairPresetSelect.innerHTML = `<option value="">${tr('fairSavedSettings')}</option>` +
      names.map(name => `<option value="${escapeHtml(name)}" ${name === selectName ? 'selected' : ''}>${escapeHtml(name)}</option>`).join('');
  }

  function fairPresetSnapshot() {
    return {
      fairId:selectedFairId,
      lots:[...selectedFairLots],
      slotGroups:Object.fromEntries([...selectedFairSlotRules].map(([lotId, groups]) => [lotId, {regular:Boolean(groups.regular), vip:Boolean(groups.vip)}])),
      currency:selectedFairCurrency,
      exactLots:fairComboSettings().exactLots, bonusLots:[...selectedFairBonusLots],
      buyLimit:Math.max(1, Number(root?.querySelector('#hk-fair-buy-limit')?.value || 1)),
      rerollLimit:Math.max(0, Number(root?.querySelector('#hk-fair-reroll-limit')?.value || 0)),
      premiumReroll:Boolean(root?.querySelector('#hk-fair-premium-reroll')?.checked)
    };
  }

  function saveFairPreset(existingName = '') {
    if (!selectedFairId || !selectedFairLots.size) {
      alert(either('Сначала выберите ярмарку и хотя бы один товар', 'Choose a fair and at least one item first')); return;
    }
    const name = existingName || prompt(tr('settingName'));
    if (!name?.trim()) return;
    const normalized = name.trim();
    const all = fairPresets();
    all[normalized] = fairPresetSnapshot();
    save({fairPresets:all});
    refreshFairPresets(normalized);
    log(tr('settingSaved', {name:normalized}), 'ok');
  }

  function loadFairPreset(name) {
    const preset = fairPresets()[name];
    if (!preset) return;
    if (!fairCatalog.length) {
      alert(either('Сначала нажмите «Считать ярмарку»', 'Press “Read fair” first'));
      refreshFairPresets(); return;
    }
    if (fairStates().some(state => String(state.id) === String(preset.fairId))) selectedFairId = String(preset.fairId);
    const available = new Set(fairRowsForState(fairState(selectedFairId)).map(row => row.lotId));
    selectedFairLots = new Set((preset.lots || []).map(String).filter(id => available.has(id)));
    selectedFairSlotRules.clear();
    const options = fairSlotOptions();
    for (const lotId of selectedFairLots) {
      const groups = preset.slotGroups?.[lotId];
      if (groups && typeof groups === 'object') {
        selectedFairSlotRules.set(lotId, {regular:Boolean(groups.regular), vip:Boolean(groups.vip)});
      } else {
        const oldCells = new Set(Array.isArray(preset.slotRules?.[lotId]) ? preset.slotRules[lotId].map(String) : options.map(value => value.key));
        selectedFairSlotRules.set(lotId, {
          regular:options.some(value => !value.vip && oldCells.has(value.key)),
          vip:options.some(value => value.vip && oldCells.has(value.key))
        });
      }
    }
    selectedFairCurrency = String(preset.currency || '');
    const buy = root?.querySelector('#hk-fair-buy-limit'); if (buy) buy.value = Math.max(1, Number(preset.buyLimit || 1));
    const reroll = root?.querySelector('#hk-fair-reroll-limit'); if (reroll) reroll.value = Math.max(0, Number(preset.rerollLimit || 0));
    const premium = root?.querySelector('#hk-fair-premium-reroll'); if (premium) premium.checked = Boolean(preset.premiumReroll);
    selectedFairBonusLots = new Set(Array.isArray(preset.bonusLots) ? preset.bonusLots.map(Number).filter(value => [5,10,30].includes(value)) : [5,10,30]);
    renderFair();
    const exact=root?.querySelector('#hk-fair-exact-lots'); if(exact) exact.value=['0','3','6','9'].includes(String(preset.exactLots)) ? String(preset.exactLots) : '0';
    renderFairBonusChoices();
    refreshFairPresets(name);
    log(tr('settingLoaded', {name}), 'ok');
  }

  function deleteFairPreset() {
    const name = fairPresetSelect?.value;
    if (!name || !confirm(tr('deleteSetting', {name}))) return;
    const all = fairPresets(); delete all[name]; save({fairPresets:all}); refreshFairPresets();
  }

  function costDocumentFromParts(parts) {
    const result = {items:[], currencies:[]};
    for (const part of parts || []) if (part?.id && part.quantity > 0) result[part.kind === 'currencies' ? 'currencies' : 'items'].push({id:part.id, quantity:part.quantity});
    return result;
  }

  async function executeFairPurchase(row, slot, allowPremium = false) {
    // Event fairs have their own currency/amount controls in this tab. Do not
    // let the global daily budget reject the whole event run because one of
    // the selected variants costs diamonds. The normal fair remains covered
    // by the unified budget.
    if (!isEventFairState(fairState(selectedFairId))) {
      const decision = budgetDecision(row.cost, 'fair', 1, playerDocument, {allowPremiumOverride:allowPremium});
      if (!decision.allowed) throw new Error(decision.problems.join('; '));
    }
    const beforeDoc = playerDocument;
    const before = new Map(costParts(row.cost).map(part => [part.id, walletAmount(part.id, beforeDoc)]));
    fairDocument = await apiJson('/shop/buy', 'POST', {shop_lot_id:row.lotId, payment_type:'INTERNAL', fair_id:selectedFairId, slot_id:slot.id, lotName:row.name, lotDescription:''});
    updateWalletFromResponse(fairDocument, row.cost);
    for (const part of costParts(row.cost)) appendExpense({section:'fair', lotId:row.lotId, name:gameText(row.name) || row.name,
      currencyId:part.id, amount:part.quantity, balanceBefore:before.get(part.id), balanceAfter:walletAmount(part.id, playerDocument), status:'ok', result:'purchased'});
  }

  async function runFair() {
    if (!requireLicense() || fairRunning || !selectedFairLots.size) return;
    if ([...selectedFairLots].some(lotId => {
      const rule = selectedFairSlotRules.get(lotId); return !(rule?.regular || rule?.vip);
    })) {
      alert(tr('noCells')); return;
    }
    try {
      playerDocument = await apiJson('/player/me', 'POST');
      fairDocument = playerDocument;
      shopViewDocument = await apiJson('/shop/view', 'GET');
      fairCatalog = normalizeFairCatalog(shopViewDocument);
      const missingSelected = [...selectedFairLots].filter(lotId => !fairCatalog.some(row => row.lotId === lotId && row.safe));
      if (missingSelected.length) {
        renderFair();
        alert(either('Каталог ярмарки изменился. Проверьте выбранные лоты ещё раз.','The fair catalog changed. Review the selected lots again.'));
        return;
      }
    } catch (error) {
      log(either('Не удалось обновить ярмарку перед запуском','Could not refresh the fair before starting') + ': ' + (error?.message || error),'bad');
      return;
    }
    try {
      playerDocument = await apiJson('/player/me', 'POST');
      fairDocument = playerDocument;
      shopViewDocument = await apiJson('/shop/view', 'GET');
      fairCatalog = normalizeFairCatalog(shopViewDocument);
      const missingSelected = [...selectedFairLots].filter(lotId => !fairCatalog.some(row => row.lotId === lotId && row.safe));
      if (missingSelected.length) {
        renderFair();
        alert(either('Каталог ярмарки изменился. Проверьте выбранные лоты ещё раз.','The fair catalog changed. Review the selected lots again.'));
        return;
      }
    } catch (error) {
      log(either('Не удалось обновить ярмарку перед запуском','Could not refresh the fair before starting') + ': ' + (error?.message || error),'bad');
      return;
    }
    const buyLimit = Math.max(1, Number(root.querySelector('#hk-fair-buy-limit').value || 1));
    const rerollLimit = Math.max(0, Number(root.querySelector('#hk-fair-reroll-limit').value || 0));
    const allowPremium = root.querySelector('#hk-fair-premium-reroll').checked;
    const combo = fairComboSettings();
    let state = fairState(selectedFairId);
    if (!safeReroll(state?.fair_reroll_cost, allowPremium)) { alert(either('Прокрутка заблокирована: цена небезопасна.', 'Reroll is blocked: unsafe cost.')); return; }
    const cost = costParts(state?.fair_reroll_cost)[0];
    const worst = cost ? `${cost.quantity * rerollLimit} ${cost.id}` : '0';
    const maximumCrystalLotCost = fairCatalog.filter(row => selectedFairLots.has(row.lotId))
      .flatMap(row => costParts(row.cost)).filter(part => part.kind === 'currencies' && part.id === 'cur_prem')
      .reduce((maximum, part) => Math.max(maximum, part.quantity), 0) * buyLimit;
    const crystalNotice = maximumCrystalLotCost
      ? either(`\nМаксимум кристаллов на покупки: ${maximumCrystalLotCost.toLocaleString(locale())} 💎`, `\nMaximum crystals for purchases: ${maximumCrystalLotCost.toLocaleString(locale())} 💎`)
      : '';
    if (!confirm(language === 'en'
      ? `Start searching for selected lots?\n\nTotal purchases: ${buyLimit}\nMaximum rerolls: ${rerollLimit}\nMaximum reroll cost: ${worst}${crystalNotice}`
      : `Запустить поиск выбранных лотов?\n\nВсего покупок: ${buyLimit}\nМаксимум прокруток: ${rerollLimit}\nМаксимальная цена прокруток: ${worst}${crystalNotice}`)) return;
    if (hkRunner.running) { alert(either('Сначала завершите текущую задачу','Finish the current task first')); return; }
    hkRunner.start({title:either('Ярмарка','Fair'),total:buyLimit,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});
    fairRunning = true; fairStop = false; updateFairControls();
    let bought = 0, bonusBought = 0, rerolls = 0, authRetries = 0;
    try {
      playerDocument = await apiJson('/player/me', 'POST');
      fairDocument = playerDocument;
      while (!fairStop && bought < buyLimit) {
        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');
        await hkRunner.waitIfPaused();
        hkRunner.setStep(either('Поиск и покупка лотов','Searching and buying lots'), bought, buyLimit);
        if (combo.exactLots && buyLimit - bought < 3) {
          log(either(`Остаток лимита ${buyLimit - bought}: для комбинации требуется минимум 3 покупки.`, `Remaining limit ${buyLimit - bought}: a combination requires at least 3 purchases.`), 'warn');
          break;
        }
        state = fairState(selectedFairId);
        if (!state) throw new Error('Выбранная ярмарка больше недоступна');
        let purchased = false;
        const options = fairSlotOptions(state);
        const targets = options.filter(({slot, vip, index}) => {
          // A combination spans all nine main cells: six regular and three
          // VIP. Encrypted bonus cells start after them and never count toward
          // the 3/6/9 group itself.
          if (index >= 9 || slot.is_bought || !selectedFairLots.has(String(slot.shop_lot_id))) return false;
          const groups = selectedFairSlotRules.get(String(slot.shop_lot_id));
          return !groups || (vip ? groups.vip : groups.regular);
        });
        const maximumGroup = combo.exactLots
          ? Math.floor(Math.min(combo.exactLots, buyLimit - bought) / 3) * 3
          : 0;
        const matchedTargets = maximumGroup ? targets.slice(0, maximumGroup) : [];
        const groupSize = Math.floor(matchedTargets.length / 3) * 3;
        const purchaseTargets = matchedTargets.slice(0, groupSize);
        if (combo.exactLots && groupSize >= 3) {
          const totalCosts = new Map();
          for (const {slot} of purchaseTargets) {
            const row = fairCatalog.find(value => value.lotId === String(slot.shop_lot_id));
            for (const part of costParts(row?.cost)) totalCosts.set(part.id, (totalCosts.get(part.id) || 0) + part.quantity);
          }
          const insufficient = [...totalCosts].filter(([id, amount]) => {
            const balance = walletAmount(id, playerDocument);
            return balance === null || balance < amount;
          }).map(([id, amount]) => {
            const balance = walletAmount(id, playerDocument);
            return `${paymentLabel(id)}: ${balance === null ? either('остаток не определён','balance is unknown') : `${balance.toLocaleString(locale())} / ${amount.toLocaleString(locale())}`}`;
          });
          if (insufficient.length) {
            log(either(`Комбинация ${purchaseTargets.length} не выкуплена — не хватает средств: ${insufficient.join('; ')}`,
              `Combination ${purchaseTargets.length} was not purchased — insufficient funds: ${insufficient.join('; ')}`), 'warn');
          } else {
            for (const {slot} of purchaseTargets) {
              const row = fairCatalog.find(value => value.lotId === String(slot.shop_lot_id));
              if (!row?.safe) continue;
              log(`Лоты ${purchaseTargets.length}: покупка…`);
              await executeFairPurchase(row, slot, allowPremium);
              bought++; purchased = true; authRetries = 0;
            }
            // The last /shop/buy response may still contain the previous set
            // of encrypted cells. Refresh once after the completed group so
            // newly opened bonus slots are visible before we try to buy them.
            playerDocument = await apiJson('/player/me', 'POST');
            fairDocument = playerDocument;
            state = fairState(selectedFairId);
            const collars = fairSlotOptions(state).filter(({slot,index}) => {
              if (index < 9 || index >= 9 + groupSize / 3 || slot.is_bought) return false;
              const row = fairCatalog.find(value => value.lotId === String(slot.shop_lot_id));
              return selectedFairBonusLots.has(Number(row?.rewardQuantity || 0));
            });
            for (const {slot} of collars) {
              const row = fairCatalog.find(value => value.lotId === String(slot.shop_lot_id));
              if (!row?.safe) continue;
              log(`Открытый слот ${Number(slot.id) + 1}: покупка…`);
              await executeFairPurchase(row, slot, allowPremium);
              bonusBought++; purchased = true; authRetries = 0;
            }
          }
        }
        if (!combo.exactLots) for (const {slot, vip} of options) {
          if (fairStop || bought >= buyLimit || slot.is_bought || !selectedFairLots.has(String(slot.shop_lot_id))) continue;
          const allowedGroups = selectedFairSlotRules.get(String(slot.shop_lot_id));
          if (allowedGroups && !(vip ? allowedGroups.vip : allowedGroups.regular)) continue;
          const row = fairCatalog.find(value => value.lotId === String(slot.shop_lot_id));
          if (!row?.safe) continue;
          log(`Лот найден. Покупка ${bought + 1}/${buyLimit}…`);
          try {
            await executeFairPurchase(row, slot, allowPremium);
            bought++; purchased = true; authRetries = 0; log(`Куплено ${bought}/${buyLimit}`, 'ok');
          } catch (error) {
            if (/HTTP 401|unauthorized/i.test(error.message) && authRetries++ < 2) { playerDocument = await apiJson('/player/me', 'POST'); fairDocument = playerDocument; continue; }
            throw error;
          }
        }
        if (purchased) continue;
        if (rerolls >= rerollLimit) { log(`Достигнут лимит прокруток: ${rerollLimit}`, 'warn'); break; }
        if (!safeReroll(state.fair_reroll_cost, allowPremium)) throw new Error('Цена прокрутки изменилась и стала небезопасной');
        log(`Лота нет. Прокрутка ${rerolls + 1}/${rerollLimit}…`);
        try {
          if (!isEventFairState(state)) {
            const rerollDecision = budgetDecision(state.fair_reroll_cost, 'fair', 1, playerDocument, {allowPremiumOverride:allowPremium});
            if (!rerollDecision.allowed) throw new Error(rerollDecision.problems.join('; '));
          }
          const before = new Map(costParts(state.fair_reroll_cost).map(part => [part.id, walletAmount(part.id, playerDocument)]));
          const rerollCost = state.fair_reroll_cost;
          fairDocument = await apiJson('/fair/reroll', 'POST', {fair_id:selectedFairId});
          updateWalletFromResponse(fairDocument, rerollCost);
          for (const part of costParts(state.fair_reroll_cost)) appendExpense({section:'fair', lotId:`reroll:${selectedFairId}`, name:either('Прокрутка ярмарки','Fair reroll'),
            currencyId:part.id, amount:part.quantity, balanceBefore:before.get(part.id), balanceAfter:walletAmount(part.id, playerDocument), status:'ok', result:'rerolled'});
          rerolls++; authRetries = 0;
        }
        catch (error) {
          if (/HTTP 401|unauthorized/i.test(error.message) && authRetries++ < 2) { playerDocument = await apiJson('/player/me', 'POST'); fairDocument = playerDocument; continue; }
          throw error;
        }
        await gameRetryDelay(550);
      }
      playerDocument = await hkAuthoritativePlayerRead('fair-complete');
      fairDocument = playerDocument;
      hkRunner.finish(either('Ярмарка завершена','Fair completed'));
      log(`Ярмарка завершена: выбранных покупок ${bought}, бонусных ${bonusBought}, прокруток ${rerolls}`, 'ok');
    } catch (error) {
      if (error?.name === 'AbortError') { hkRunner.reset(); log(either('Ярмарка остановлена','Fair stopped'),'warn'); }
      else { hkRunner.fail(error); log(`Аварийная остановка ярмарки: ${error.message}`, 'bad'); }
    } finally { fairRunning = false; fairStop = false; renderFair(); }
  }

  function ordinaryShopGroup(lot) {
    const lotId = String(lot?.id || '').toLowerCase();
    // Each Resources card has one visible base lot plus three real hidden
    // package commands (_10, _50 and _100). They are separate shop_lot_id
    // values, not a quantity parameter on the base purchase.
    if (/^mf_shoplot_itempack_[1-5](?:_(?:10|50|100))?$/.test(lotId)) return 'resources';
    // Renovation contains the ten individual materials (two materials per tier).
    // The combined mf_shoplot_pit_remort_all pack is intentionally excluded.
    if (/^mf_shoplot_pit_remort_(?:beams|nails)_[1-5]$/.test(lotId)) return 'renovation';
    // Invest Deals contains the two daily building-helper offers only.
    if (/^mf_shoplot_building_helpers_offer_0[12]$/.test(lotId)) return 'invest';
    return '';
  }

  function quantitySelectOptions(maximum, selected) {
    const max = Math.max(0, Math.trunc(Number(maximum || 0)));
    const current = Math.min(max, Math.max(0, Math.trunc(Number(selected || 0))));
    const values = new Set([0, current, max]);
    for (let value = 1; value <= Math.min(max, 20); value++) values.add(value);
    for (const value of [25, 50, 100, 250, 500]) if (value <= max) values.add(value);
    return [...values].sort((a, b) => a - b).map(value => `<option value="${value}" ${value === current ? 'selected' : ''}>${value}</option>`).join('');
  }

  function captureActiveEventCode() {
    let code = '';
    const activeIcon = document.querySelector('.picture-counter.special-counter img[src*="/special_events/icons/timer_event_"]');
    const iconMatch = String(activeIcon?.getAttribute('src') || '').match(/timer_event_([^/?]+?)_icon(?:\.|\?)/i);
    if (iconMatch?.[1]) code = iconMatch[1].toLowerCase();
    // On a first installation the player may already be inside the current
    // event page. Use its visible cards only until the map icon has supplied
    // and persisted the authoritative current event code.
    if (!code && !activeEventCode) {
      const visibleCard = [...document.querySelectorAll('[data-lot-id^="mf_shoplot_"]')].find(element =>
        visible(element) && /^mf_shoplot_(?:daily_|finite_|infinite_)?event_[^_]+_/i.test(String(element.getAttribute('data-lot-id') || '')));
      const cardMatch = String(visibleCard?.getAttribute('data-lot-id') || '').match(/^mf_shoplot_(?:daily_|finite_|infinite_)?event_([^_]+)_/i);
      if (cardMatch?.[1]) code = cardMatch[1].toLowerCase();
    }
    if (code && code !== activeEventCode) {
      activeEventCode = code;
      save({activeEventCode:code});
      if (shopViewDocument) {
        shopRows = normalizeRegularShop();
        if (root && selectedShopSection === 'regular') renderShop();
      }
    }
    return activeEventCode;
  }

  function normalizeRegularShop(shopDocument = shopViewDocument, playerDoc = playerDocument) {
    const currentEventCode = captureActiveEventCode();
    const limits = new Map();
    const playerLimits = playerDoc?.shop_lot_limits || playerDoc?.player?.shop_lot_limits || [];
    for (const item of playerLimits) limits.set(String(item?.shop_lot_id || ''), Math.max(0, Number(item?.number_of_purchase || 0)));
    const shopLots = shopDocument?.shop_lots || [];
    const lotsById = new Map(shopLots.map(lot => [String(lot?.id || ''), lot]));
    return shopLots.flatMap(lot => {
      const rawView = lot?.lot_view || {};
      const lotId = String(lot.id || '');
      const currentEventLot = Boolean(currentEventCode) &&
        lotId.toLowerCase().includes(`_event_${currentEventCode}_`);
      const resourceMatch = lotId.match(/^(mf_shoplot_itempack_[1-5])(?:_(10|50|100))?$/i);
      const resourceBaseLot = resourceMatch ? lotsById.get(resourceMatch[1]) : null;
      const resourceBaseView = resourceBaseLot?.lot_view || {};
      const declaredMultiplier = Boolean(resourceMatch?.[2]) &&
        (resourceBaseView.multiplier_lots || []).map(String).includes(lotId);
      // Hidden multiplier lots contain only their resulting package quantity.
      // Reuse the visible parent card for its name/icon/content, while keeping
      // the child's own lot ID, cost and package quantity for the purchase.
      if (resourceMatch?.[2] && !declaredMultiplier) return [];
      const view = declaredMultiplier ? resourceBaseView : rawView;
      if (String(view.type || '').toLowerCase() === 'fair' || lot.external_cost) return [];
      const lotLimits = lot.limit || [];
      // The standard Resources and Renovation cards have no daily purchase
      // limit in the game. Keep only our explicitly allow-listed ordinary
      // lots when a server-side limit is absent.
      const unlimited = !lotLimits.length && (Boolean(ordinaryShopGroup(lot)) || currentEventLot);
      if (!lotLimits.length && !unlimited) return [];
      const playerLimit = lotLimits.find(value => String(value?.type || '').toUpperCase() === 'PLAYER');
      const sharedLimit = lotLimits.find(value => ['CLAN','GLOBAL'].includes(String(value?.type || '').toUpperCase()));
      const remainingValues = [];
      if (playerLimit) remainingValues.push(Math.max(0, Number(playerLimit.limit || 0) + Number(playerLimit.bonus || 0) - (limits.get(String(lot.id || '')) || 0)));
      if (sharedLimit) remainingValues.push(Math.max(0, Number(sharedLimit.limit || 0) + Number(sharedLimit.bonus || 0) - Number(sharedLimit.value || 0)));
      if (!remainingValues.length && !unlimited) return [];
      const bought = limits.get(lotId) || 0;
      const remaining = unlimited ? SHOP_UNLIMITED_RUN_MAX : Math.min(...remainingValues);
      const parts = costParts(lot.cost);
      const content = (view.content_view || [])[0] || {};
      const rewardId = String(content.id || '');
      const rewardQuantity = resourceMatch
        ? Math.max(0, Number(rawView.quantity || view.quantity || 0))
        : Math.max(0, Number(content.quantity || view.quantity || 0));
      const tab = String(view.tab || 'default').toLowerCase();
      // The shop catalog and the player's limit list both retain past events.
      // Include every internal lot of the active event: the updated game uses
      // daily_event, finite_event, event and infinite_event prefixes together.
      // If the current event cannot be identified, fail closed and show none.
      const section = ['clan','clan_2'].includes(tab) ? 'clan' : currentEventLot ? 'regular' : 'ordinary';
      const group = section === 'ordinary' ? ordinaryShopGroup(lot) : '';
      const clanGroup = section === 'clan' ? (sharedLimit ? 'shared' : 'personal') : '';
      if (section === 'ordinary' && !group) return [];
      const premium = premiumPurchase(lot.cost);
      const safe = parts.length > 0 && parts.every(part => part.quantity > 0 &&
        (part.kind === 'items' ? part.id.startsWith('item_') :
          ['cur_gold', 'cur_cap'].includes(part.id) || (section === 'clan' && part.id === 'cur_prem')));
      return [{lotId, name:String(view.name || rewardId || lotId), rewardId,
        rewardQuantity, resourceTier:resourceMatch ? Number(resourceMatch[1].slice(-1)) : 0,
        cost:lot.cost || {}, safe, affordable:canAffordCost(lot.cost || {}, playerDoc), premium, group,
        bought, maximum:bought + remaining, remaining, unlimited, section, clanGroup,
        sharedPurchased:sharedLimit ? Math.max(0, Number(sharedLimit.value || 0)) : 0,
        sharedMaximum:sharedLimit ? Math.max(0, Number(sharedLimit.limit || 0) + Number(sharedLimit.bonus || 0)) : 0,
        icon:mediaUrl(view.icon_card || view.icon || content.icon_card || content.icon, rewardId)}];
    }).sort((a, b) => Number(b.remaining > 0) - Number(a.remaining > 0) ||
      (a.group === 'resources' && b.group === 'resources'
        ? a.resourceTier - b.resourceTier || a.rewardQuantity - b.rewardQuantity
        : a.lotId.localeCompare(b.lotId)));
  }

  // HK_CLAN_SHOP_ACTUAL_FACTS_V1
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

  async function loadShop() {
    if (!requireLicense()) return;
    try {
      log(either('Считываю магазин…', 'Reading shop…'));
      playerDocument = await apiJson('/player/me', 'POST');
      shopViewDocument = await apiJson('/shop/view', 'GET');
      shopRows = normalizeRegularShop();
      void reportClanShopActualFacts();
      selectedShopLots = new Set([...selectedShopLots].filter(id => shopRows.some(row => row.lotId === id && row.safe && row.remaining > 0)));
      selectedShopCounts = new Map([...selectedShopCounts].flatMap(([id, count]) => {
        const row = shopRows.find(value => value.lotId === id && value.safe && value.remaining > 0);
        return row ? [[id, Math.min(row.remaining, Math.max(0, Number(count || 0)))]] : [];
      }));
      renderShop();
      log(either(`Магазин считан: ${shopRows.length} лотов`, `Shop loaded: ${shopRows.length} lots`), 'ok');
    } catch (error) { log(`${either('Ошибка магазина', 'Shop error')}: ${error.message}`, 'bad'); }
  }

  function defaultShopPurchaseCount(row) {
    if (!row) return 0;
    const remaining = Math.max(0, Number(row.remaining || 0));
    if (isRenovationBatch(row)) return remaining >= renovationBatchMultiplier(row) ? renovationBatchMultiplier(row) : 0;
    return Math.min(remaining, 1);
  }

  function isRenovationBatch(row) {
    return row?.section === 'ordinary' && row?.group === 'renovation';
  }

  function renovationBatchMultiplier(row) {
    return Math.ceil(500 / Math.max(1, Number(row?.rewardQuantity || 0)));
  }

  function renovationBatchCount(row, count) {
    return Math.floor(Math.max(0, Number(count || 0)) / renovationBatchMultiplier(row));
  }

  function renovationBatchMaximum(row) {
    return Math.floor(Math.min(SHOP_UNLIMITED_RUN_MAX, Math.max(0, Number(row?.remaining || 0))) / renovationBatchMultiplier(row));
  }

  function renderShop() {
    if (!shopCards || !shopSummary) return;
    if (!shopRows.length) {
      shopCards.innerHTML = `<p class="hk-muted">${tr('shopReadFirst')}</p>`;
      shopSummary.textContent = tr('selectedPurchases', {n:0});
      const buy = root?.querySelector('#hk-shop-buy'); if (buy) buy.disabled = true;
      return;
    }
    const groupBar = root?.querySelector('#hk-shop-groups');
    if (groupBar) {
      const groups = selectedShopSection === 'ordinary'
        ? [['resources','resourcesShop'],['renovation','renovationShop'],['invest','investShop']]
        : selectedShopSection === 'clan'
          ? [['personal','personalLots'],['shared','sharedLots']]
          : [];
      groupBar.style.display = groups.length ? '' : 'none';
      groupBar.innerHTML = groups.map(([id, label]) => `<button class="${selectedShopGroup === id ? 'active' : ''}" data-shop-group="${id}" data-i18n="${label}">${tr(label)}</button>`).join('');
      groupBar.querySelectorAll('[data-shop-group]').forEach(button => button.onclick = () => {
        selectedShopGroup = button.dataset.shopGroup; selectedShopLots.clear(); selectedShopCounts.clear(); renderShop();
      });
    }
    const visibleRows = shopRows.filter(row => row.section === selectedShopSection &&
      (selectedShopSection === 'ordinary' ? row.group === selectedShopGroup :
        selectedShopSection === 'clan' ? row.clanGroup === selectedShopGroup : true));
    shopCards.innerHTML = visibleRows.map(row => {
      const selectable = row.safe && row.remaining > 0 && (!isRenovationBatch(row) || renovationBatchMaximum(row) > 0);
      const count = selectable ? Math.min(row.remaining, Math.max(0, Number(selectedShopCounts.get(row.lotId) || 0))) : 0;
      const shownRewardQuantity = count && row.group === 'renovation' ? row.rewardQuantity * count : row.rewardQuantity;
      const selectedBatches = isRenovationBatch(row) ? renovationBatchCount(row, count) : 0;
      const maximumBatches = isRenovationBatch(row) ? renovationBatchMaximum(row) : 0;
      return `<div class="hk-shop-lot ${count ? 'selected' : ''} ${row.premium ? 'premium' : ''} ${selectable ? '' : 'locked'}">
        ${row.premium ? '<i class="hk-premium-mark">💎</i>' : ''}<label class="hk-shop-pick"><input type="checkbox" data-shop-lot="${escapeHtml(row.lotId)}" ${count ? 'checked' : ''} ${selectable ? '' : 'disabled'}>
        ${fairIconHtml(row.icon)}<b>×${shownRewardQuantity.toLocaleString(locale())}</b><span>${costVisual(row.cost, count && row.group === 'renovation' ? count : 1)}</span></label>
        <small>${row.unlimited ? tr('unlimited') : row.remaining > 0 ? tr('remaining',{n:row.remaining}) : tr('boughtOut')}</small>
        ${isRenovationBatch(row)
          ? `<label class="hk-shop-quantity"><span>${either('Пакетов ×500','×500 packages')}</span><select data-shop-batches="${escapeHtml(row.lotId)}" ${selectable ? '' : 'disabled'}>${Array.from({length:maximumBatches + 1}, (_, n) => `<option value="${n}" ${n === selectedBatches ? 'selected' : ''}>${n} × 500</option>`).join('')}</select></label>`
          : `<label class="hk-shop-quantity"><span>${tr('quantity')}</span><input data-shop-qty="${escapeHtml(row.lotId)}" type="number" inputmode="numeric" min="0" max="${row.remaining}" value="${count}" ${selectable ? '' : 'disabled'}><button type="button" data-shop-max="${escapeHtml(row.lotId)}" ${selectable ? '' : 'disabled'}>MAX</button></label>`}</div>`;
    }).join('') || `<p class="hk-muted">${tr('noLots')}</p>`;
    shopCards.querySelectorAll('[data-shop-lot]').forEach(input => input.onchange = () => {
      const id = input.dataset.shopLot;
      const row = visibleRows.find(value => value.lotId === id);
      const count = input.checked ? Math.max(defaultShopPurchaseCount(row), Number(selectedShopCounts.get(id) || 0)) : 0;
      if (count) { selectedShopLots.add(id); selectedShopCounts.set(id, Math.min(row?.remaining || 0, count)); }
      else { selectedShopLots.delete(id); selectedShopCounts.delete(id); }
      renderShop();
    });
    shopCards.querySelectorAll('[data-shop-qty]').forEach(input => input.onchange = () => {
      const id = input.dataset.shopQty;
      const row = visibleRows.find(value => value.lotId === id);
      const count = Math.min(row?.remaining || 0, Math.max(0, Math.trunc(Number(input.value || 0))));
      if (count) { selectedShopLots.add(id); selectedShopCounts.set(id, count); }
      else { selectedShopLots.delete(id); selectedShopCounts.delete(id); }
      renderShop();
    });
    shopCards.querySelectorAll('[data-shop-batches]').forEach(select => select.onchange = () => {
      const id = select.dataset.shopBatches;
      const row = visibleRows.find(value => value.lotId === id);
      const batches = Math.min(renovationBatchMaximum(row), Math.max(0, Math.trunc(Number(select.value || 0))));
      const count = batches * renovationBatchMultiplier(row);
      if (count) { selectedShopLots.add(id); selectedShopCounts.set(id, count); }
      else { selectedShopLots.delete(id); selectedShopCounts.delete(id); }
      renderShop();
    });
    shopCards.querySelectorAll('[data-shop-max]').forEach(button => button.onclick = () => {
      const id = button.dataset.shopMax;
      const row = visibleRows.find(value => value.lotId === id);
      const count = Math.min(SHOP_UNLIMITED_RUN_MAX, Math.max(0, Math.trunc(Number(row?.remaining || 0))));
      if (count) { selectedShopLots.add(id); selectedShopCounts.set(id, count); }
      else { selectedShopLots.delete(id); selectedShopCounts.delete(id); }
      renderShop();
    });
    const selected = visibleRows.filter(row => selectedShopLots.has(row.lotId) && row.safe && row.remaining > 0)
      .map(row => ({row, count:Math.min(row.remaining, Math.max(0, Number(selectedShopCounts.get(row.lotId) || 0)))})).filter(item => item.count > 0);
    const purchaseCount = selected.reduce((sum, item) => sum + (isRenovationBatch(item.row) ? renovationBatchCount(item.row, item.count) : item.count), 0);
    const totals = new Map();
    for (const row of visibleRows) for (const part of costParts(row.cost)) addProjectedCost(totals, part, 0);
    for (const {row, count} of selected) for (const part of costParts(row.cost)) addProjectedCost(totals, part, count);
    const spending = [...totals.values()].filter(part => part.quantity > 0);
    const totalVisual = spending.length ? spending.map(part => `${fairIconHtml(paymentIcon(part), 'hk-price-icon')}<b>${part.quantity.toLocaleString(locale())}</b>`).join(' ') : '0';
    shopSummary.innerHTML = `<b>${tr('selectedPurchases',{n:purchaseCount})}</b><br><small>${tr('maxCost')}: ${totalVisual}</small>${walletForecastHtml(totals)}`;
    const buy = root?.querySelector('#hk-shop-buy'); if (buy) buy.disabled = shopRunning || !purchaseCount;
  }

  async function buyRegularShop() {
    if (!requireLicense() || shopRunning) return;
    try {
      playerDocument = await apiJson('/player/me', 'POST');
      shopViewDocument = await apiJson('/shop/view', 'GET');
      shopRows = normalizeRegularShop();
    } catch (error) {
      log(either('Не удалось обновить магазин перед покупкой','Could not refresh the shop before purchase') + ': ' + (error?.message || error),'bad');
      return;
    }
    const plan = shopRows.filter(row => row.section === selectedShopSection &&
      (selectedShopSection !== 'ordinary' || row.group === selectedShopGroup) && selectedShopLots.has(row.lotId) && row.safe && row.remaining > 0)
      .map(row => ({row, count:Math.min(row.remaining, Math.max(0, Number(selectedShopCounts.get(row.lotId) || 0)))})).filter(item => item.count > 0);
    if (!plan.length) return;
    const count = plan.reduce((sum, item) => sum + (isRenovationBatch(item.row) ? renovationBatchCount(item.row, item.count) : item.count), 0);
    const budgetSection = selectedShopSection === 'clan' ? 'clan' : 'shop';
    const projectedProblems = plan.flatMap(item => budgetDecision(item.row.cost, budgetSection, item.count, playerDocument).problems);
    if (projectedProblems.length) {
      alert(`${either('Покупка заблокирована единым бюджетом','Purchase blocked by unified budget')}:\n\n${[...new Set(projectedProblems)].join('\n')}`);
      return;
    }
    const crystalCost = plan.reduce((sum, item) => sum + costParts(item.row.cost)
      .filter(part => part.kind === 'currencies' && part.id === 'cur_prem').reduce((value, part) => value + part.quantity * item.count, 0), 0);
    if (!confirm(language === 'en'
      ? `Buy ${count} selected items?${crystalCost ? `\n\nCrystal cost: ${crystalCost.toLocaleString(locale())} 💎` : ''}\n\nPurchases are irreversible. External payments are blocked.`
      : `Выкупить выбранные товары: ${count}?${crystalCost ? `\n\nСтоимость: ${crystalCost.toLocaleString(locale())} 💎` : ''}\n\nПокупки необратимы. Внешняя оплата заблокирована.`)) return;
    if (hkRunner.running) { alert(either('Сначала завершите текущую задачу','Finish the current task first')); return; }
    hkRunner.start({title:either('Магазин','Shop'),total:count,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});
    shopRunning = true; renderShop();
    let completed = 0;
    try {
      playerDocument = await apiJson('/player/me', 'POST');
      for (const {row, count:rowCount} of plan) {
        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');
        await hkRunner.waitIfPaused();
        hkRunner.setStep(either('Покупка товаров','Buying items'), completed, count);
        const requestCount = Math.min(rowCount, row.remaining, SHOP_UNLIMITED_RUN_MAX);
        const before = new Map(costParts(row.cost).map(part => [part.id, walletAmount(part.id, playerDocument)]));
        const requestBody = {shop_lot_id:row.lotId, payment_type:'INTERNAL', lotName:row.name, lotDescription:''};
        let purchasedRow = 0;
        try {
          if (isRenovationBatch(row)) {
            const decision = budgetDecision(row.cost, budgetSection, requestCount, playerDocument);
            if (!decision.allowed) throw new Error(decision.problems.join('; '));
            const batchMultiplier = renovationBatchMultiplier(row);
            const batchCount = renovationBatchCount(row, requestCount);
            for (let batch = 0; batch < batchCount; batch += 1) {
              log(either(`Пакетная покупка ×500: ${batch + 1}/${batchCount}…`, `Batch purchase ×500: ${batch + 1}/${batchCount}…`));
              if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');
              await hkRunner.waitIfPaused();
              hkRunner.setStep(either('Покупка товаров','Buying items'), completed, count);
              playerDocument = await apiJson('/shop/buy', 'POST', {
                ...requestBody,
                collection_entity_id:row.rewardId,
                collection_count:batchMultiplier
              }, true, 0);
              purchasedRow += batchMultiplier;
              completed += 1;
            }
          } else for (let index = 0; index < requestCount; index += 1) {
            const decision = budgetDecision(row.cost, budgetSection, 1, playerDocument);
            if (!decision.allowed) throw new Error(decision.problems.join('; '));
            if (index === 0 || (index + 1) % 25 === 0 || index + 1 === requestCount) {
              log(either(`Покупка по ×1: ${index + 1}/${requestCount}…`, `Buying ×1: ${index + 1}/${requestCount}…`));
            }
            // Start the next purchase immediately after the previous response.
            // Network retries are disabled because repeating an irreversible
            // request after a lost response could buy an extra copy.
            if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');
            await hkRunner.waitIfPaused();
            hkRunner.setStep(either('Покупка товаров','Buying items'), completed, count);
            playerDocument = await apiJson('/shop/buy', 'POST', requestBody, true, 0);
            purchasedRow += 1;
            completed += 1;
          }
        } finally {
          if (purchasedRow) for (const part of costParts(row.cost)) appendExpense({section:budgetSection, lotId:row.lotId, name:gameText(row.name) || row.name,
            currencyId:part.id, amount:part.quantity * purchasedRow, balanceBefore:before.get(part.id), balanceAfter:walletAmount(part.id, playerDocument), status:'ok', result:`purchased ${purchasedRow}/${requestCount}`});
        }
      }
      await hkAuthoritativePlayerRead('shop-complete');
      try { shopViewDocument = await apiJson('/shop/view', 'GET'); } catch (_) {}
      shopRows = normalizeRegularShop();
      void reportClanShopActualFacts();
      hkRunner.finish(either('Покупки завершены','Purchases completed'));
      selectedShopLots.clear();
      selectedShopCounts.clear();
      log(either(`Покупки завершены: ${completed}`, `Purchases completed: ${completed}`), 'ok');
    } catch (error) {
      if (error?.name === 'AbortError') { hkRunner.reset(); log(either('Магазин остановлен','Shop stopped'),'warn'); }
      else { hkRunner.fail(error); log(either('Остановка магазина','Shop stopped') + ': ' + (error?.message || error), 'bad'); }
    } finally {
      shopRunning = false;
      shopRows = normalizeRegularShop();
      renderShop();
    }
  }

  function dailyLabel(row) {
    return clean(`${gameText(row?.name || '')} ${row?.name || ''} ${row?.rewardId || ''}`).toLowerCase();
  }

  function dailyRecruitLot(row) {
    const label = dailyLabel(row);
    return /пополнени[ея]\s+рекрут|recruit\s+(?:replenishment|refill)|replenish(?:ment)?\s+recruit|нов(?:ые|ых)\s+рекрут|new\s+recruits?|салаг|rookies?/.test(label);
  }

  function dailyCartelLot(row) {
    const label = dailyLabel(row);
    return /пополнени[ея]\s+картел|cartel\s+(?:replenishment|refill)|replenish(?:ment)?\s+cartel/.test(label);
  }

  function excludedDailyClanLot(row) {
    if (row?.section !== 'clan' || row?.clanGroup !== 'personal') return false;
    const label = dailyLabel(row);
    const excludedByName = /хомячий\s+шар\s+идол|idol(?:s)?\s+hamster\s+ball|случайный\s+s\+?\s+бизнес|random\s+s\+?\s+business/.test(label);
    const excludedByCurrency = costParts(row.cost).some(part => {
      const currencyId = String(part.id || '').toLowerCase().replace(/[\s-]+/g, '_');
      return /pit_?rat_?tokens?/.test(currencyId);
    });
    return excludedByName || excludedByCurrency;
  }

  function mandatoryDailyClanLot(row) {
    // Recruit and cartel replenishment are obligatory personal clan lots.
    // Hamster balls and random S/S+ businesses remain excluded from Today.
    if (row?.section !== 'clan' || row?.clanGroup !== 'personal') return false;
    return dailyRecruitLot(row) || dailyCartelLot(row);
  }

  function clanSkillPointLot(row) {
    if (row?.section !== 'clan' || row?.clanGroup !== 'personal') return false;
    const label = clean(`${gameText(row?.name || '')} ${row?.name || ''}`).toLowerCase();
    return /очки\s+навыков(?:\s+клана)?|clan\s+skill\s+points?|skill\s+points?/.test(label);
  }

  function gamePeriodBounds(now = new Date()) {
    const dayStart = new Date(now);
    dayStart.setHours(21, 0, 0, 0);
    if (now < dayStart) dayStart.setDate(dayStart.getDate() - 1);
    const dayEnd = new Date(dayStart); dayEnd.setDate(dayEnd.getDate() + 1);
    const weekStart = new Date(dayStart);
    const daysSinceMonday = (weekStart.getDay() + 6) % 7;
    weekStart.setDate(weekStart.getDate() - daysSinceMonday);
    const weekEnd = new Date(weekStart); weekEnd.setDate(weekEnd.getDate() + 7);
    return {dayStart:dayStart.getTime(), dayEnd:dayEnd.getTime(), weekStart:weekStart.getTime(), weekEnd:weekEnd.getTime()};
  }

  function budgetDocument() {
    const stored = load().budget || {};
    const periods = gamePeriodBounds();
    return {currencies:{...(stored.currencies || {})}, periods, timezone:Intl.DateTimeFormat().resolvedOptions().timeZone || ''};
  }

  function currencyBudget(id) {
    const value = budgetDocument().currencies[String(id)] || {};
    const premium = String(id) === 'cur_prem';
    return {
      reserve:Math.max(0, Number(value.reserve || 0)),
      dailyLimit:Math.max(0, Number(value.dailyLimit || 0)),
      weeklyLimit:Math.max(0, Number(value.weeklyLimit || 0)),
      allow:{shop:value.allow?.shop !== false, fair:value.allow?.fair !== false, clan:value.allow?.clan !== false},
      allowPremium:premium && value.allowPremium === true
    };
  }

  function saveCurrencyBudget(id, patch) {
    const budget = budgetDocument();
    budget.currencies[String(id)] = {...currencyBudget(id), ...patch,
      allow:{...currencyBudget(id).allow, ...(patch.allow || {})}};
    save({budget});
  }

  function expenseJournal() {
    return Array.isArray(load().expenseJournal) ? load().expenseJournal : [];
  }

  function budgetUsage(id, now = Date.now()) {
    const periods = gamePeriodBounds(new Date(now));
    const rows = expenseJournal().filter(row => row?.status === 'ok' && String(row.currencyId) === String(id));
    return {
      day:rows.filter(row => Number(row.time || 0) >= periods.dayStart).reduce((sum, row) => sum + Math.max(0, Number(row.amount || 0)), 0),
      week:rows.filter(row => Number(row.time || 0) >= periods.weekStart).reduce((sum, row) => sum + Math.max(0, Number(row.amount || 0)), 0)
    };
  }

  function appendExpense(entry) {
    const rows = [...expenseJournal(), {time:Date.now(), ...entry}].slice(-300);
    save({expenseJournal:rows});
  }

  function costSignature(cost) {
    return costParts(cost).filter(part => part.id && part.quantity > 0)
      .sort((a,b) => `${a.kind}:${a.id}`.localeCompare(`${b.kind}:${b.id}`))
      .map(part => `${part.kind}:${part.id}:${part.quantity}`).join('|');
  }

  function budgetDecision(cost, section, multiplier = 1, documentValue = playerDocument, options = {}) {
    const problems = [];
    for (const part of costParts(cost)) {
      const amount = Math.max(0, Number(part.quantity || 0) * multiplier);
      const rules = currencyBudget(part.id);
      const usage = budgetUsage(part.id);
      const balance = walletAmount(part.id, documentValue);
      if (balance === null) problems.push(`${paymentLabel(part.id)}: ${either('баланс не определён','balance is unknown')}`);
      if (rules.allow?.[section] === false) problems.push(`${paymentLabel(part.id)}: ${either('раздел запрещён','section is disabled')}`);
      if (part.id === 'cur_prem' && !rules.allowPremium && !options.allowPremiumOverride) problems.push(`${paymentLabel(part.id)}: ${either('алмазы запрещены','diamonds are disabled')}`);
      if (balance !== null && balance - amount < rules.reserve) problems.push(`${paymentLabel(part.id)}: ${either('нарушается остаток','minimum balance would be breached')}`);
      if (rules.dailyLimit > 0 && usage.day + amount > rules.dailyLimit) problems.push(`${paymentLabel(part.id)}: ${either('превышен дневной лимит','daily limit exceeded')}`);
      if (rules.weeklyLimit > 0 && usage.week + amount > rules.weeklyLimit) problems.push(`${paymentLabel(part.id)}: ${either('превышен недельный лимит','weekly limit exceeded')}`);
      if (balance !== null && balance < amount) problems.push(`${paymentLabel(part.id)}: ${either('недостаточно средств','insufficient balance')}`);
    }
    return {allowed:!problems.length, problems};
  }

  function discoveredCurrencyIds() {
    // Only universal currencies and currencies of the event that is active
    // right now belong in Today. Feature tokens and archived event balances
    // remain in the player's inventory, but must not clutter this screen.
    const ids = new Set(['cur_prem','cur_gold','cur_cap','item_invest_cur','item_business_dust','item_clan_cur']);
    const currentShopRows = dailyShopRows.length ? dailyShopRows : shopRows;
    for (const row of currentShopRows.filter(value => value?.safe && value.remaining > 0 && value.section === 'regular')) {
      for (const part of costParts(row.cost)) if (part.id) ids.add(part.id);
    }
    for (const state of visibleFairStates(playerDocument).filter(value => String(value?.id) === 'fair_event_base')) {
      for (const part of costParts(state?.fair_reroll_cost)) if (part.id) ids.add(part.id);
      for (const slot of state.fair_slots || []) {
        if (slot?.is_bought) continue;
        const row = fairCatalog.find(value => value.lotId === String(slot?.shop_lot_id || ''));
        for (const part of costParts(row?.cost)) if (part.id) ids.add(part.id);
      }
    }
    return [...ids].sort((a,b) => Number(a !== 'cur_prem') - Number(b !== 'cur_prem') || paymentLabel(a).localeCompare(paymentLabel(b), locale()));
  }

  function timestampFrom(value) {
    if (value == null) return null;
    const numberValue = Number(value);
    if (Number.isFinite(numberValue) && numberValue > 0) return numberValue < 1e12 ? numberValue * 1000 : numberValue;
    const parsed = Date.parse(String(value));
    return Number.isFinite(parsed) ? parsed : null;
  }

  function firstTimer(value) {
    const candidates = [value?.timer?.timestamp, value?.timestamp, value?.end, value?.ends_at, value?.finish_at, value?.expires_at, value?.expired_at];
    for (const candidate of candidates) { const result = timestampFrom(candidate); if (result && result > Date.now()) return result; }
    return null;
  }

  function countdownLabel(timestamp) {
    if (!timestamp) return '—';
    const seconds = Math.max(0, Math.floor((timestamp - Date.now()) / 1000));
    const days = Math.floor(seconds / 86400), hours = Math.floor(seconds % 86400 / 3600), minutes = Math.floor(seconds % 3600 / 60);
    return days ? `${days}${either('д','d')} ${hours}${either('ч','h')}` : `${hours}${either('ч','h')} ${minutes}${either('м','m')}`;
  }

  function dailyAdvertisement(documentValue = playerDocument) {
    const candidates = [
      documentValue?.advertisement, documentValue?.player?.advertisement,
      documentValue?.data?.advertisement, documentValue?.data?.player?.advertisement
    ];
    const wrapper = candidates.find(value => value && typeof value === 'object') || {};
    const raw = wrapper.$ && typeof wrapper.$ === 'object' ? wrapper.$ : wrapper;
    const card = [...document.querySelectorAll('.ribbon-ad-card[data-lot-id],.simple-ad-card[data-lot-id]')].find(visible);
    const lotId = String(raw.shop_lot_id ?? raw.lot_id ?? raw.lotId ?? raw.shopLotId ?? card?.dataset?.lotId ?? '');
    const watchedAt = Math.max(Number(sessionStorage.getItem('timestamp-ad') || 0), Number(localStorage.getItem('timestamp-ad') || 0));
    const cooldownUntil = watchedAt > 0 ? watchedAt + 1000 : 0;
    const timer = cooldownUntil > Date.now() ? {timestamp:cooldownUntil} : null;
    return {raw, lotId, type:String(raw.type || (card ? 'external' : '')).toLowerCase(), timer, available:!!lotId && !timer};
  }

  function dailyActionRows() {
    const ad = dailyAdvertisement();
    const actions = [
      {id:'rumors', label:either('Слухи','Rumors'), kind:'rumors', uiGroup:'free', free:true, available:dailyRumorRoute.length > 0},
      {id:'advertisement', label:tr('dailyAds'), kind:'advertisement', uiGroup:'free', free:true, available:ad.available}
    ];
    for (const row of pitLimitSummaries()) {
      const count = selectedPitMoves(row.id, row.current);
      if (count > 0) actions.push({id:`pit:${row.id}`, label:tr(row.textKey), textKey:row.textKey, kind:'pit', uiGroup:'pit',
        free:true, available:true, pitType:row.id, count});
    }
    const rows = dailyShopRows.filter(row => row.safe && !excludedDailyClanLot(row) && (
      // Keep every lot of the current regular event visible, including lots
      // already bought today. Required recruit/cartel cards also remain visible
      // after purchase so the Today page shows their complete daily state.
      row.section === 'regular' || row.group === 'invest' || mandatoryDailyClanLot(row) || clanSkillPointLot(row) || (row.remaining > 0 && (
        (row.section === 'ordinary' && !row.unlimited) || (row.section === 'clan' && row.clanGroup === 'personal')
      ))
    ));
    for (const row of rows) {
      const label = row.section === 'regular' ? tr('regularShop') : row.section === 'clan' ? tr('clanShop') :
        row.group === 'invest' ? tr('investShop') : row.group === 'resources' ? tr('resourcesShop') : tr('renovationShop');
      const section = row.section === 'clan' ? 'clan' : 'shop';
      const actionId = `lot:${row.lotId}`;
      const mandatory = mandatoryDailyClanLot(row);
      const savedCount = Math.max(0, Math.floor(Number(dailyPurchaseCounts[actionId] || 0)));
      const count = mandatory ? Math.max(0, Number(row.remaining || 0)) :
        Math.min(Math.max(0, Number(row.remaining || 0)), savedCount || (dailySelection[actionId] ? 1 : 0));
      if (mandatory && row.remaining > 0) {
        dailySelection[actionId] = true;
        dailyPurchaseCounts[actionId] = count;
      }
      actions.push({id:actionId, label:`${label}: ${gameText(row.name) || row.rewardId || row.lotId}`, kind:'purchase',
        uiGroup:row.group === 'invest' ? 'invest' : row.section, category:row.group || row.section, section, free:false, mandatory,
        available:row.remaining > 0 && row.affordable, boughtOut:row.remaining <= 0,
        row, count, cost:row.cost, signature:costSignature(row.cost)});
    }
    return actions;
  }

  function selectedDailyActions() {
    return dailyActionRows().filter(action => action.available && (action.kind === 'pit' ? dailySelection[action.id] !== false : dailySelection[action.id] === true) &&
      (action.kind !== 'purchase' || action.count > 0));
  }

  function saveDailySelection() {
    const today = {...(load().today || {}), selection:{...dailySelection}, purchaseCounts:{...dailyPurchaseCounts}, storeTab:dailyStoreTab, snapshot:dailySnapshot};
    save({today});
  }

  function dailyPlanTotals(actions = selectedDailyActions()) {
    const totals = new Map();
    for (const action of actions.filter(row => row.kind === 'purchase')) for (const part of costParts(action.cost)) addProjectedCost(totals, part, action.count || 1);
    return totals;
  }

  function dailyTaskGroups(rows = dailyShopRows) {
    const clan = rows.filter(row => row.section === 'clan' && row.clanGroup === 'personal' && !excludedDailyClanLot(row));
    const recruits = clan.filter(dailyRecruitLot);
    const cartels = clan.filter(dailyCartelLot);
    const investments = rows.filter(row => row.section === 'ordinary' && row.group === 'invest');
    return {recruits, cartels, investments};
  }

  function dailyRowText(rows, title) {
    const available = rows.filter(row => row.safe && row.remaining > 0 && row.affordable).length;
    const short = rows.filter(row => row.safe && row.remaining > 0 && !row.affordable).length;
    const message = available ? `${either('доступно','available')}: ${available}` : short ? either('недостаточно валюты','not enough currency') : either('пока нет доступных','not available yet');
    return `<li class="${available ? 'ready' : ''}"><b>${escapeHtml(title)}</b><span>${message}</span></li>`;
  }

  function dailyCityKey(value) {
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

  function playRewardedAdInPageWorld() {
    return new Promise((resolve, reject) => {
      const bridgeId = `hk-ad-${Date.now()}-${Math.random().toString(36).slice(2)}`;
      const marker = document.createElement('span');
      marker.id = bridgeId;
      marker.hidden = true;
      (document.documentElement || document.body).appendChild(marker);
      let settled = false;
      const finish = (error = '') => {
        if (settled) return;
        settled = true;
        clearTimeout(timeout);
        marker.remove();
        if (error) reject(new Error(error)); else resolve();
      };
      marker.addEventListener('hk-ad-finished', () => finish(marker.dataset.error || ''));
      const timeout = setTimeout(() => finish(either('рекламный модуль не ответил','the ad module did not respond')), 180000);
      const script = document.createElement('script');
      script.textContent = `(()=>{const n=document.getElementById(${JSON.stringify(bridgeId)});(async()=>{try{if(!window.HamsterAds||typeof window.HamsterAds.init!=='function')throw new Error('HamsterAds SDK not found');const c=window.HamsterAds.init({partnerId:'King'});if(!c||typeof c.play!=='function')throw new Error('HamsterAds controller not available');await c.play({advType:'rewarded'});}catch(e){n.dataset.error=String(e&&e.message||e)}finally{n.dispatchEvent(new Event('hk-ad-finished'))}})()})()`;
      (document.documentElement || document.head).appendChild(script);
      script.remove();
    });
  }

  async function playOfficialRewardedAd() {
    if (window.HamsterAds?.init) {
      dailyAdController ||= window.HamsterAds.init({partnerId:'King'});
      if (!dailyAdController?.play) throw new Error(either('Рекламный контроллер игры недоступен','The game ad controller is unavailable'));
      return dailyAdController.play({advType:'rewarded'});
    }
    return playRewardedAdInPageWorld();
  }

  async function runDailyAd(internal = false) {
    if (!requireLicense() || (dailyRunning && !internal)) return;
    if (!internal) dailyRunning = true; renderDailyTasks();
    try {
      playerDocument = await apiJson('/player/me', 'POST');
      let ad = dailyAdvertisement(playerDocument);
      if (!ad.lotId) {
        try {
          const partial = await apiJson('/player/me', 'POST', {arguments:['advertisement']});
          ad = dailyAdvertisement(partial);
        } catch (_) {}
      }
      const lotId = ad.lotId;
      if (!lotId) throw new Error(either('Сейчас нет доступной рекламы', 'No ad is currently available'));
      if (ad.timer) throw new Error(either(`Следующая реклама через ${countdownLabel(ad.timer.timestamp)}`, `Next ad in ${countdownLabel(ad.timer.timestamp)}`));
      if (ad.type === 'external') {
        log(either('Запускаю официальный рекламный показ…', 'Starting the official ad…'));
        await playOfficialRewardedAd();
      }
      playerDocument = await apiJson('/shop/buy', 'POST', {shop_lot_id:lotId, payment_type:'AD', lotName:'advertisement', lotDescription:''});
      sessionStorage.setItem('timestamp-ad', String(Date.now()));
      log(either('Рекламная награда получена', 'Ad reward received'), 'ok');
    } catch (error) { log(`${either('Реклама не выполнена','Ad was not completed')}: ${error.message}`, 'warn'); if (internal) throw error; }
    finally { if (!internal) dailyRunning = false; renderDailyTasks(); }
  }

  function renderDailyTasks() {
    if (!dailyBox) return;
    const groups = dailyTaskGroups();
    const actions = dailyActionRows();
    const selected = selectedDailyActions();
    const totals = dailyPlanTotals(selected);
    const currencies = discoveredCurrencyIds();
    const rumorsStored = load().today?.rumors || {};
    const rumorPeriodStart = gamePeriodBounds().dayStart;
    const routeHtml = dailyRumorRoute.length ? '<ul>' + dailyRumorRoute.map(row => {
      const progress = rumorsStored[dailyCityKey(row.city)];
      const count = progress?.periodStart === rumorPeriodStart ? Math.min(3,Number(progress.completed || 0)) : 0;
      const points = (row.points || []).map(point => Number(point.x) + ':' + String(Number(point.y)).padStart(2,'0')).join(' · ');
      return '<li><b>' + escapeHtml(row.city) + '</b><span>' + count + '/3 · ' + escapeHtml(points) + '</span></li>';
    }).join('') + '</ul>' : '<span>' + either('Маршрут слухов не опубликован','Rumor route is not published') + '</span>';
    const ad = dailyAdvertisement();
    const adTimer = ad.timer?.timestamp || firstTimer(ad.raw);
    const pit = pitState();
    const balancesHtml = currencies.map(id => {
      const amount = walletAmount(id);
      return `<div class="hk-today-balance">${fairIconHtml(paymentIcon({id,kind:id.startsWith('cur_') ? 'currencies' : 'items'}),'hk-price-icon')}<span>${escapeHtml(paymentLabel(id))}</span><b>${amount === null ? '—' : amount.toLocaleString(locale())}</b></div>`;
    }).join('');
    const actionRowHtml = action => {
      const checked = action.available && dailySelection[action.id] === true;
      const decision = action.kind === 'purchase' ? budgetDecision(action.cost, action.section, action.count) : {allowed:true,problems:[]};
      const quantity = action.count > 1 ? `<b class="hk-action-count">×${action.count}</b>` : '';
      const lotVisual = action.kind === 'purchase' ? shopLotIconHtml(action.row) : '';
      const quantityControl = action.kind === 'purchase' && !action.boughtOut ? `<label class="hk-today-quantity"><span>${tr('quantity')}</span><select data-daily-quantity="${escapeHtml(action.id)}" ${action.available && !action.mandatory ? '' : 'disabled'}>${quantitySelectOptions(action.row.remaining, action.count)}</select></label>` : '';
      const availability = action.kind === 'purchase' && action.row && Object.prototype.hasOwnProperty.call(action.row, 'remaining') ?
        (action.boughtOut ? '' : ` · ${action.row.unlimited ? tr('unlimited') : tr('remaining',{n:action.row.remaining})}`) : '';
      const price = action.boughtOut ? `<span class="hk-bought-out">${tr('boughtOut')}</span>` :
        action.kind === 'purchase' ? `${costVisual(action.cost)}${quantity}` : `<span class="hk-free">${either('бесплатно','free')}</span>`;
      return `<div class="hk-today-action ${lotVisual ? 'has-lot-icon' : ''} ${action.mandatory ? 'mandatory' : ''} ${action.available ? (decision.allowed ? '' : 'budget-warning') : 'locked'}"><input type="checkbox" data-daily-action="${escapeHtml(action.id)}" ${checked ? 'checked' : ''} ${action.available && !action.mandatory ? '' : 'disabled'}>${lotVisual}<span><b>${escapeHtml(action.label)}</b><small>${price}${availability}${action.mandatory ? ` · ${either('обязательный ежедневный лот','required daily lot')}` : ''}${decision.problems.length ? ` · ${escapeHtml(decision.problems.join('; '))}` : ''}</small></span>${quantityControl}</div>`;
    };
    const freeRows = actions.filter(action => action.uiGroup === 'free');
    const paidGroups = [
      ['regular', tr('dailyRegularActions')], ['ordinary', tr('dailyOrdinaryActions')],
      ['clan', tr('dailyClanActions')], ['invest', tr('dailyInvestActions')]
    ].map(([key,title]) => ({key,title,rows:actions.filter(action => action.uiGroup === key)})).filter(group => group.rows.length);
    if (!paidGroups.some(group => group.key === dailyStoreTab)) dailyStoreTab = paidGroups[0]?.key || 'regular';
    const activePaid = paidGroups.find(group => group.key === dailyStoreTab);
    const freeHtml = freeRows.length ? `<details class="hk-today-action-group" open><summary><b>${escapeHtml(tr('dailyFreeActions'))}</b><span>${freeRows.length}</span></summary><div>${freeRows.map(actionRowHtml).join('')}</div></details>` : '';
    const storeTabs = paidGroups.length ? `<div class="hk-today-store-tabs">${paidGroups.map(group => `<button type="button" data-daily-store-tab="${group.key}" class="${group.key === dailyStoreTab ? 'active' : ''}">${escapeHtml(group.title)} <span>${group.rows.length}</span></button>`).join('')}</div>` : '';
    const paidHtml = activePaid ? `<div class="hk-today-action-group hk-today-store-page"><div>${activePaid.rows.map(actionRowHtml).join('')}</div></div>` : '';
    const actionHtml = `${freeHtml}${storeTabs}${paidHtml}`;
    const planRows = selected.map((action,index) => {
      const decision = action.kind === 'purchase' ? budgetDecision(action.cost, action.section, action.count) : {allowed:true,problems:[]};
      return `<li class="${decision.allowed ? '' : 'blocked'}"><b>${index + 1}. ${escapeHtml(action.label)}${action.count > 1 ? ` ×${action.count}` : ''}</b><span>${action.kind === 'purchase' ? costVisual(action.cost) : either('без расходов','no cost')}${decision.problems.length ? `<br>${escapeHtml(decision.problems.join('; '))}` : ''}</span></li>`;
    }).join('') || `<p class="hk-muted">${either('Отметьте действия выше','Select actions above')}</p>`;
    const budgetRows = currencies.map(id => {
      const rules = currencyBudget(id), usage = budgetUsage(id), premium = id === 'cur_prem';
      return `<div class="hk-budget-row" data-budget-row="${escapeHtml(id)}"><div class="hk-budget-title">${fairIconHtml(paymentIcon({id,kind:id.startsWith('cur_') ? 'currencies' : 'items'}),'hk-price-icon')}<b>${escapeHtml(paymentLabel(id))}</b></div>
        <label>${tr('dailyReserve')}<input data-budget-field="reserve" type="number" min="0" step="1" value="${rules.reserve}"></label>
        <label>${tr('dailyLimit')}<input data-budget-field="dailyLimit" type="number" min="0" step="1" value="${rules.dailyLimit}"></label>
        <label>${tr('weeklyLimit')}<input data-budget-field="weeklyLimit" type="number" min="0" step="1" value="${rules.weeklyLimit}"></label>
        <small>${tr('spentToday')}: <b>${usage.day.toLocaleString(locale())}</b> · ${tr('spentWeek')}: <b>${usage.week.toLocaleString(locale())}</b></small>
        <div class="hk-budget-flags"><label><input data-budget-allow="shop" type="checkbox" ${rules.allow.shop ? 'checked' : ''}>${tr('shop')}</label><label><input data-budget-allow="fair" type="checkbox" ${rules.allow.fair ? 'checked' : ''}>${tr('fair')}</label><label><input data-budget-allow="clan" type="checkbox" ${rules.allow.clan ? 'checked' : ''}>${tr('clanShop')}</label>${premium ? `<label class="premium"><input data-budget-premium type="checkbox" ${rules.allowPremium ? 'checked' : ''}>${tr('allowPremium')}</label>` : ''}</div></div>`;
    }).join('');
    const journalHtml = expenseJournal().slice(-12).reverse().map(row => `<li class="${row.status === 'ok' ? 'ok' : 'failed'}"><span>${new Date(row.time).toLocaleString(locale(),{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'})} · ${escapeHtml(row.name || row.lotId || '')}</span><b>${Number(row.amount || 0).toLocaleString(locale())} ${escapeHtml(paymentLabel(row.currencyId))}</b><small>${escapeHtml(row.result || row.status || '')}</small></li>`).join('') || `<li><span>${either('Операций пока нет','No operations yet')}</span></li>`;
    dailyBox.innerHTML = `<div class="hk-daily-progress"><div><b>${tr('dailyCurrent')}</b><span>${dailyRunning ? either('выполняется','running') : dailySnapshot ? `${either('проверено','checked')} ${new Date(dailySnapshot.checkedAt).toLocaleTimeString(locale(),{hour:'2-digit',minute:'2-digit'})}` : tr('dailyReady')}</span></div><i><em style="width:${dailyRunning ? 45 : dailySnapshot ? 100 : 0}%"></em></i></div>
      <section class="hk-today-section"><h4>${tr('dailyBalances')}</h4><div class="hk-today-balances">${balancesHtml}</div></section>
      <section class="hk-today-section"><h4>${either('Слухи','Rumors')}</h4>${routeHtml}</section>
      <div class="hk-today-grid"><section class="hk-today-section"><h4>${tr('dailyAds')}</h4><p>${ad.lotId ? (adTimer ? either('Ожидание','Cooldown') : either('Доступна','Available')) : either('Недоступна','Unavailable')}${adTimer ? ` · ${countdownLabel(adTimer)}` : ''}</p></section>
      <section class="hk-today-section"><h4>${tr('dailyPit')}</h4>${pitLimitsHtml()}${pit.round ? `<p>${tr('round')}: <b>${pit.round}</b>${pit.enemyText ? ` · ${escapeHtml(pit.enemyText)}` : ''}</p>` : ''}</section></div>
      <section class="hk-today-section"><h4>${tr('dailyStores')}</h4><div class="hk-today-action-groups">${actionHtml}</div></section>
      <section class="hk-today-section hk-today-plan"><h4>${tr('dailyPlan')}</h4><small>${tr('exactPlan')}</small><ol>${planRows}</ol>${walletForecastHtml(totals)}</section>
      <details class="hk-today-section hk-budget"><summary>${tr('dailyBudget')}</summary>${budgetRows}<h4>${either('Журнал расходов','Expense journal')}</h4><ul class="hk-expense-journal">${journalHtml}</ul><div class="hk-toolbar"><button id="hk-settings-export">${tr('exportSettings')}</button><button id="hk-settings-import">${tr('importSettings')}</button></div></details>`;
    installIconFallbacks(dailyBox);
    const run = root?.querySelector('#hk-daily-run');
    if (run) run.disabled = dailyRunning || !selected.length;
    dailyBox.querySelectorAll('[data-pit-moves]').forEach(select => select.onchange = () => {
      savePitMoves(select.dataset.pitMoves, select.value);
      renderDailyTasks();
    });
    dailyBox.querySelectorAll('[data-pit-enabled]').forEach(input => input.onchange = () => {
      dailySelection[`pit:${input.dataset.pitEnabled}`] = input.checked;
      saveDailySelection();
      renderDailyTasks();
    });
    dailyBox.querySelectorAll('[data-daily-action]').forEach(input => input.onchange = () => {
      dailySelection[input.dataset.dailyAction] = input.checked;
      if (input.dataset.dailyAction.startsWith('lot:')) {
        if (input.checked && !(Number(dailyPurchaseCounts[input.dataset.dailyAction]) > 0)) dailyPurchaseCounts[input.dataset.dailyAction] = 1;
        if (!input.checked) dailyPurchaseCounts[input.dataset.dailyAction] = 0;
      }
      saveDailySelection(); renderDailyTasks();
    });
    dailyBox.querySelectorAll('[data-daily-quantity]').forEach(select => select.onchange = () => {
      const id = select.dataset.dailyQuantity;
      const count = Math.max(0, Math.floor(Number(select.value || 0)));
      dailyPurchaseCounts[id] = count;
      dailySelection[id] = count > 0;
      saveDailySelection(); renderDailyTasks();
    });
    dailyBox.querySelectorAll('[data-daily-store-tab]').forEach(button => button.onclick = () => {
      dailyStoreTab = button.dataset.dailyStoreTab || 'regular';
      saveDailySelection(); renderDailyTasks();
    });
    dailyBox.querySelectorAll('[data-budget-row]').forEach(row => {
      const id = row.dataset.budgetRow;
      row.querySelectorAll('[data-budget-field]').forEach(input => input.onchange = () => saveCurrencyBudget(id, {[input.dataset.budgetField]:Math.max(0,Number(input.value || 0))}));
      row.querySelectorAll('[data-budget-allow]').forEach(input => input.onchange = () => saveCurrencyBudget(id, {allow:{[input.dataset.budgetAllow]:input.checked}}));
      const premium = row.querySelector('[data-budget-premium]'); if (premium) premium.onchange = () => saveCurrencyBudget(id, {allowPremium:premium.checked});
    });
    const exportButton = dailyBox.querySelector('#hk-settings-export'); if (exportButton) exportButton.onclick = exportMobileSettings;
    const importButton = dailyBox.querySelector('#hk-settings-import'); if (importButton) importButton.onclick = importMobileSettings;
  }

  // HK_TODAY_LIVE_VERIFY_V1 stage3a-today-live-20260920-r2
  // HK_TODAY_REFRESH_FRESH_V1 stage3a-today-live-20260920-r3
  async function refreshDailyTasks() {
    if (!requireLicense()) return;
    try {
      log(either('Проверяю доступные ежедневные задачи…', 'Checking available daily tasks…'));
      playerDocument = await apiJson('/player/me', 'POST');
      shopViewDocument = await apiJson('/shop/view', 'GET');
      dailyShopRows = shopViewDocument ? normalizeRegularShop() : [];
      if (!shopViewDocument) log(tr('dailyNoShop'), 'warn');
      await loadRumorRoute();
      fairDocument = playerDocument;
      if (shopViewDocument) fairCatalog = normalizeFairCatalog(shopViewDocument);
      dailySnapshot = {checkedAt:Date.now(), playerId:playerIdentity(playerDocument?.player || {}), periodStart:gamePeriodBounds().dayStart};
      save({today:{...(load().today || {}), selection:{...dailySelection}, snapshot:dailySnapshot}, budget:budgetDocument()});
      renderDailyTasks();
      const groups = dailyTaskGroups();
      log(either(`Задачи считаны: рекруты ${groups.recruits.length}, картели ${groups.cartels.length}`, `Tasks loaded: recruits ${groups.recruits.length}, cartels ${groups.cartels.length}`), 'ok');
    } catch (error) {
      log(`${either('Ошибка ежедневных задач', 'Daily tasks error')}: ${error.message}`, 'bad');
      renderDailyTasks();
    }
  }

  function resourceCost(rawCost) {
    const result = {items:[], currencies:[]};
    for (const kind of ['items','currencies']) {
      result[kind] = (rawCost?.[kind] || []).map(value => ({
        id:String(value?.id || value?.item_id || value?.currency_id || ''),
        quantity:Math.max(0, Math.trunc(Number(value?.quantity ?? value?.value ?? 0)))
      })).filter(value => value.id && value.quantity > 0);
    }
    return result;
  }

  function resourceEventName(eventId) {
    const wanted = String(eventId || '');
    const row = normalizeEventCatalog(eventCatalogDocument).find(value => String(value?.id || value?.event_id || value?.event?.id || '') === wanted) || {};
    return gameText(row?.name || row?.event?.name || row?.title || wanted || either('Ресурсное задание','Resource task'));
  }

  function resourceEvents(buildingRow) {
    const documentValue = buildingRow?.document || {};
    const building = documentValue?.building || documentValue?.data?.building || documentValue?.data || documentValue;
    const tier = Number(building?.chosen_tier ?? building?.tier ?? buildingRow?.tier ?? 0);
    const rows = Array.isArray(building?.events) ? building.events : [];
    return rows.flatMap(room => {
      const roomId = String(room?.id || '');
      const roomNumber = Number(room?.room_number || 0);
      const values = [{...room,isSide:false}, ...(room?.side_events || []).map(value => ({...value,isSide:true}))];
      return values.filter(value => value?.level != null && Number(value.level) >= 0 && roomId).map(value => {
        const cost = resourceCost(value?.costs);
        const parts = costParts(cost);
        const affordable = parts.length ? Math.max(0, Math.floor(Math.min(...parts.map(part => {
          const balance = walletAmount(part.id);
          return balance == null || part.quantity <= 0 ? 0 : balance / part.quantity;
        })))) : 0;
        const atMax = value?.max_level == null || Number(value.level) >= Number(value.max_level);
        return {buildingId:buildingRow.id, buildingName:buildingRow.name, resourceKind:buildingRow.kind, tier, roomId, roomNumber,
          sideEventId:value.isSide ? String(value?.id || '') : '', eventId:String(value?.event_id || ''),
          name:resourceEventName(value?.event_id), cost, affordable, atMax};
      });
    }).filter(row => !resourceEventIsExcluded(row) && clean(row.name).toLocaleLowerCase() !== clean(row.buildingName).toLocaleLowerCase());
  }

  function allResourceEvents() {
    return resourceBuildings.flatMap(resourceEvents);
  }

  function resourceUsesProtectedCost(row) {
    return costParts(row?.cost).some(part => RESOURCE_PROTECTED_COST_IDS.has(String(part?.id || '')));
  }

  function resourceEventIsExcluded(row) {
    const mainEventId = RESOURCE_BUILDING_TYPES[row?.resourceKind]?.eventMarker || '';
    return resourceUsesProtectedCost(row) || (mainEventId && String(row?.eventId || '') === mainEventId);
  }

  function resourceTierLabel(tier) {
    return ['1','2','3','4','4+','5','5+','MAX'][Math.max(0,Math.trunc(Number(tier)))] || `T${Math.max(0,Math.trunc(Number(tier))) + 1}`;
  }

  function resourceWalletCostVisual(cost, multiplier = 1000) {
    const parts = costParts(cost);
    if (!parts.length) return `<span class="hk-resource-balance ok">${either('Без затрат','No cost')}</span>`;
    return parts.map(part => {
      const required = Math.max(0, Number(part.quantity || 0) * multiplier);
      const balance = walletAmount(part.id);
      const enough = balance != null && balance >= required;
      const availableText = balance == null ? '?' : Number(balance).toLocaleString(locale());
      return `<span class="hk-resource-balance ${enough?'ok':'short'}">${fairIconHtml(paymentIcon(part),'hk-price-icon')}<i>${either('в наличии','available')} <b>${availableText}</b></i><em>/</em><i>${either('нужно','required')} <b>${required.toLocaleString(locale())}</b></i></span>`;
    }).join('');
  }

  function renderResources() {
    if (!resourceBox) return;
    const events = allResourceEvents();
    const totalCompletions = 1000 * resourceRepeatCount;
    const available = events.filter(row => row.atMax && row.affordable > 0 && !resourceEventIsExcluded(row));
    const activeBuilding = resourceBuildings[0] || null;
    const savedIds = savedResourceBuildingIds();
    const buildingButtons = Object.keys(RESOURCE_BUILDING_TYPES).map(kind => `<button data-resource-kind="${kind}" class="${kind===resourceSelectedKind?'active':''}" ${resourceBusy?'disabled':''}><b>${escapeHtml(resourceTypeName(kind,true))}</b><small>${escapeHtml(resourceTypeName(kind))}${savedIds[kind]?' ✓':''}</small></button>`).join('');
    const activeTier = Math.max(0, Math.trunc(Number(activeBuilding?.tier || 0)));
    const maximumTier = Math.max(activeTier, Math.trunc(Number(activeBuilding?.maxTier ?? activeTier)));
    const tierButtons = activeBuilding ? Array.from({length:maximumTier + 1},(_,tier)=>`<button data-resource-tier="${tier}" class="${tier===activeTier?'active':''}" ${resourceBusy?'disabled':''}>${resourceTierLabel(tier)}</button>`).join('') : '';
    const buildings = resourceBuildings.length ? resourceBuildings.map(building => {
      const rows = resourceEvents(building);
      const content = rows.length ? rows.map((row,index) => {
        const protectedCost = resourceUsesProtectedCost(row);
        const maximum = Math.max(0, Math.trunc(row.affordable));
        const planned = protectedCost ? 0 : resourceMaximumMode ? maximum : Math.min(totalCompletions, maximum);
        const ready = !protectedCost && row.atMax && planned > 0;
        const reason = protectedCost ? either('Слава защищена — расход отключён','Fame is protected — spending disabled') : !row.atMax ? either('Сначала доведите задание до max','First raise the task to max') : resourceMaximumMode ? either(`Максимально возможно ×${planned}`,`Maximum possible ×${planned}`) : planned < totalCompletions ? either(`Ресурсов меньше выбранного объёма — будет выполнено ×${planned}`,`Resources are below the selected amount — will run ×${planned}`) : either(`Будет выполнено ×${planned}`,`Will run ×${planned}`);
        return `<div class="hk-resource-task ${protectedCost?'protected':''}"><div><b>${escapeHtml(row.name)}</b><small>${escapeHtml(reason)}</small></div><span class="hk-resource-cost">${resourceWalletCostVisual(row.cost,protectedCost?1:(planned || totalCompletions))}</span><button data-resource-building="${escapeHtml(building.id)}" data-resource-event="${index}" ${resourceBusy || !ready?'disabled':''}>${protectedCost?either('Запрещено','Blocked'):`×${planned || 0}`}</button></div>`;
      }).join('') : `<p class="hk-muted">${either('Доступных ресурсных заданий нет','No resource tasks are available')}</p>`;
      return `<section class="hk-resource-building"><h4>${escapeHtml(building.buildingName || resourceTypeName(building.kind,true))} · ${escapeHtml(building.name || building.id)} <small>${resourceTierLabel(building.tier)}</small></h4>${content}</section>`;
    }).join('') : `<p class="hk-muted">${either(`Скрипт автоматически найдёт «${resourceTypeName(resourceSelectedKind,true)}» в ваших районах и загрузит задания.`,`The script will automatically find “${resourceTypeName(resourceSelectedKind,true)}” in your districts and load its tasks.`)}</p>`;
    const repeatOptions = Array.from({length:10},(_,index)=>index + 1).map(value=>`<option value="${value}" ${value===resourceRepeatCount?'selected':''}>${value}</option>`).join('');
    resourceBox.innerHTML = `<div class="hk-resource-type-tabs">${buildingButtons}</div><div class="hk-resource-head"><div><h3>${escapeHtml(resourceTypeName(resourceSelectedKind))}</h3><small>${resourceBuildings.length ? `${either('Заданий','Tasks')}: ${events.length} · ${either('можно выполнить','runnable')}: ${available.length}` : either('Множитель заданий: только ×1000','Task multiplier: ×1000 only')}</small></div><div class="hk-resource-tiers">${tierButtons}</div><button id="hk-resource-read" class="hk-secondary" ${resourceBusy?'disabled':''}>${resourceBusy?either('Считываю…','Reading…'):either(`Обновить ${resourceTypeName(resourceSelectedKind)}`,`Refresh ${resourceTypeName(resourceSelectedKind)}`)}</button></div><label class="hk-resource-repeat"><span>${either('Количество повторов ×1000','Number of ×1000 repeats')}</span><select id="hk-resource-repeat" ${resourceBusy || resourceMaximumMode?'disabled':''}>${repeatOptions}</select></label><button id="hk-resource-maximum" class="hk-secondary hk-resource-maximum" ${resourceBusy || !events.length?'disabled':''}>${resourceMaximumMode?either('Вернуться к выбранному количеству','Return to selected amount'):either('Рассчитать максимально возможный обмен','Calculate maximum possible exchange')}</button><div class="hk-resource-buildings">${buildings}</div><button id="hk-resource-run-all" class="hk-primary" ${resourceBusy || !available.length?'disabled':''}>${resourceMaximumMode?either('Выполнить рассчитанный максимум','Run calculated maximum'):either(`Выполнить доступные — до ×${totalCompletions}`,`Run available — up to ×${totalCompletions}`)}</button><p class="hk-muted">${either('Здания находятся автоматически. Выберите нужное — его задания загрузятся без предварительного открытия в игре. Переключатели 1–MAX меняют тир.','Buildings are found automatically. Select one to load its tasks without opening it in the game first. The 1–MAX controls change the tier.')}</p>`;
    installIconFallbacks(resourceBox);
    resourceBox.querySelector('#hk-resource-read').onclick = () => loadResources();
    resourceBox.querySelector('#hk-resource-run-all').onclick = () => runResourceEvents(available);
    resourceBox.querySelectorAll('[data-resource-kind]').forEach(button => button.onclick = () => selectResourceBuilding(button.dataset.resourceKind));
    resourceBox.querySelectorAll('[data-resource-tier]').forEach(button => button.onclick = () => loadResourceTier(Number(button.dataset.resourceTier)));
    resourceBox.querySelector('#hk-resource-maximum').onclick = async () => {
      resourceMaximumMode = !resourceMaximumMode;
      if (resourceMaximumMode) await loadResources(false);
      else renderResources();
    };
    resourceBox.querySelector('#hk-resource-repeat').onchange = event => {
      resourceRepeatCount = Math.max(1, Math.min(10, Math.trunc(Number(event.target.value || 1))));
      resourceMaximumMode = false;
      save({resourceRepeatCount});
      renderResources();
    };
    resourceBox.querySelectorAll('[data-resource-building]').forEach(button => button.onclick = () => {
      const building = resourceBuildings.find(value => value.id === button.dataset.resourceBuilding);
      const row = resourceEvents(building)[Number(button.dataset.resourceEvent)];
      if (row) runResourceEvents([row]);
    });
  }

  async function selectResourceBuilding(kind) {
    if (!RESOURCE_BUILDING_TYPES[kind] || resourceBusy) return false;
    resourceSelectedKind=kind;
    resourceMaximumMode=false;
    resourceBuildings=resourceBuildings.filter(row=>row.kind===kind);
    save({resourceSelectedKind:kind});
    renderResources();
    return loadResources(false);
  }

  async function loadResources(showLog = true) {
    if (!requireLicense() || resourceBusy) return false;
    resourceBusy = true; renderResources();
    try {
      playerDocument = await apiJson('/player/me', 'POST');
      if (!eventCatalogDocument) eventCatalogDocument = normalizeEventCatalog(await apiJson('/events','GET'));
      const discoveredIds=await discoverResourceBuildingIds(showLog,resourceSelectedKind);
      let buildingId=String((resourceBuildings[0]?.kind===resourceSelectedKind ? resourceBuildings[0]?.id : '') || discoveredIds[resourceSelectedKind] || '');
      if (!buildingId) {
        resourceBuildings=[];
        if (showLog) log(either(`Здание «${resourceTypeName(resourceSelectedKind,true)}» не найдено в принадлежащих вам районах.`,`“${resourceTypeName(resourceSelectedKind,true)}” was not found in your owned districts.`),'warn');
        return false;
      }
      const storedTier=Number(savedResourceTiers()[resourceSelectedKind]);
      const requestedTier=Number.isSafeInteger(Number(resourceBuildings[0]?.tier)) ? Number(resourceBuildings[0].tier) : Number.isSafeInteger(storedTier) ? storedTier : null;
      const tierQuery=requestedTier == null ? '' : `&tier=${encodeURIComponent(requestedTier)}`;
      let documentValue=await apiJson(`/player/building?building_id=${encodeURIComponent(buildingId)}${tierQuery}`, 'POST');
      let proofs=savedResourceBuildingProofs();
      let resourceBuilding=exactResourceBuildingData(documentValue,resourceSelectedKind,String(proofs[resourceSelectedKind] || '')===buildingId);
      if (!resourceBuilding || resourceBuilding.kind!==resourceSelectedKind) {
        const ids=savedResourceBuildingIds(); delete ids[resourceSelectedKind];
        delete proofs[resourceSelectedKind];
        save({resourceBuildingIds:ids,resourceBuildingProofs:proofs, ...(resourceSelectedKind==='nut'?{resourceNutBuildingId:''}:{})});
        resourceBuildings=[];
        const rediscoveredIds=await discoverResourceBuildingIds(showLog,resourceSelectedKind);
        const replacementId=String(rediscoveredIds[resourceSelectedKind] || '');
        if (!replacementId || replacementId===buildingId) {
          throw new Error(either(`Не удалось автоматически найти «${resourceTypeName(resourceSelectedKind,true)}» в принадлежащих вам районах.`,`Could not automatically find “${resourceTypeName(resourceSelectedKind,true)}” in your owned districts.`));
        }
        buildingId=replacementId;
        documentValue=await apiJson(`/player/building?building_id=${encodeURIComponent(buildingId)}${tierQuery}`, 'POST');
        proofs=savedResourceBuildingProofs();
        resourceBuilding=exactResourceBuildingData(documentValue,resourceSelectedKind,String(proofs[resourceSelectedKind] || '')===buildingId);
        if (!resourceBuilding || resourceBuilding.kind!==resourceSelectedKind) {
          const retryIds=savedResourceBuildingIds(); delete retryIds[resourceSelectedKind];
          delete proofs[resourceSelectedKind];
          save({resourceBuildingIds:retryIds,resourceBuildingProofs:proofs, ...(resourceSelectedKind==='nut'?{resourceNutBuildingId:''}:{})});
          throw new Error(either(`Автоматически найденное здание не является «${resourceTypeName(resourceSelectedKind,true)}».`,`The automatically found building is not “${resourceTypeName(resourceSelectedKind,true)}”.`));
        }
      }
      if (!resourceBuilding.completedMainEvent && String(proofs[resourceSelectedKind] || '') !== buildingId) {
        proofs[resourceSelectedKind]=buildingId;
        save({resourceBuildingProofs:proofs});
      }
      const building=resourceBuilding.building;
      const selectedTier=Number(building?.chosen_tier ?? requestedTier ?? building?.tier ?? 0);
      const maximumTier=Math.max(selectedTier,Number(building?.tier ?? selectedTier),Number(resourceBuildings[0]?.maxTier ?? selectedTier));
      resourceBuildings=[{id:buildingId,kind:resourceSelectedKind,areaId:'',tier:selectedTier,maxTier:maximumTier,name:resourceTypeName(resourceSelectedKind),buildingName:resourceTypeName(resourceSelectedKind,true),document:documentValue}];
      const tiers=savedResourceTiers(); tiers[resourceSelectedKind]=selectedTier;
      save({resourceSelectedTiers:tiers, ...(resourceSelectedKind==='nut'?{resourceSelectedTier:selectedTier}:{})});
      if (showLog) log(either(`${resourceTypeName(resourceSelectedKind)} считана, заданий: ${allResourceEvents().length}`,`${resourceTypeName(resourceSelectedKind)} read, tasks: ${allResourceEvents().length}`),'ok');
      return true;
    } catch (error) {
      log(`${either(`Ошибка чтения «${resourceTypeName(resourceSelectedKind)}»`,`${resourceTypeName(resourceSelectedKind)} read error`)}: ${error.message}`,'bad');
      return false;
    } finally {
      resourceBusy = false; renderResources();
    }
  }

  async function loadResourceTier(tier) {
    const row=resourceBuildings[0];
    const selectedTier=Math.max(0,Math.trunc(Number(tier)));
    if (!requireLicense() || resourceBusy || !row || !Number.isSafeInteger(selectedTier) || selectedTier > Number(row.maxTier ?? row.tier ?? 0)) return false;
    resourceBusy=true; renderResources();
    try {
      const documentValue=await apiJson(`/player/building?building_id=${encodeURIComponent(row.id)}&tier=${encodeURIComponent(selectedTier)}`,'POST');
      const proofs=savedResourceBuildingProofs();
      const resourceBuilding=exactResourceBuildingData(documentValue,row.kind,String(proofs[row.kind] || '')===String(row.id));
      if (!resourceBuilding || resourceBuilding.kind!==row.kind) throw new Error(either(`Не удалось прочитать выбранный тир «${resourceTypeName(row.kind)}».`,`Could not read the selected ${resourceTypeName(row.kind)} tier.`));
      const building=resourceBuilding.building;
      const actualTier=Number(building?.chosen_tier ?? selectedTier);
      if (actualTier !== selectedTier) throw new Error(either(`Игра вернула другой тир: ${resourceTierLabel(actualTier)}.`,`The game returned a different tier: ${resourceTierLabel(actualTier)}.`));
      const maximumTier=Math.max(actualTier,Number(building?.tier ?? actualTier),Number(row.maxTier ?? actualTier));
      resourceBuildings=[{...row,tier:actualTier,maxTier:maximumTier,document:documentValue}];
      const tiers=savedResourceTiers(); tiers[row.kind]=actualTier;
      save({resourceSelectedTiers:tiers, ...(row.kind==='nut'?{resourceSelectedTier:actualTier}:{})});
      log(either(`${resourceTypeName(row.kind)}: выбран тир ${resourceTierLabel(actualTier)}, заданий ${allResourceEvents().length}`,`${resourceTypeName(row.kind)}: tier ${resourceTierLabel(actualTier)} selected, tasks ${allResourceEvents().length}`),'ok');
      return true;
    } catch (error) {
      log(`${either('Ошибка переключения тира','Tier switch error')}: ${error.message}`,'bad');
      return false;
    } finally {
      resourceBusy=false; renderResources();
    }
  }

  async function runResourceEvents(rows) {
    if (!requireLicense() || resourceBusy) return;
    const wanted = (rows || []).map(row => ({buildingId:String(row?.buildingId || ''), roomId:String(row?.roomId || ''), sideEventId:String(row?.sideEventId || ''), eventId:String(row?.eventId || '')}));
    if (!wanted.length) return;
    const refreshed = await loadResources(false);
    if (!refreshed) return;
    const freshEvents = allResourceEvents();
    const sourceRows = wanted.map(key => freshEvents.find(row => String(row?.buildingId || '') === key.buildingId && String(row?.roomId || '') === key.roomId && String(row?.sideEventId || '') === key.sideEventId && String(row?.eventId || '') === key.eventId)).filter(Boolean);
    const totalCompletions = 1000 * resourceRepeatCount;
    const maximumMode = resourceMaximumMode;
    const ready = sourceRows.filter(row => row?.atMax && row?.affordable > 0 && !resourceEventIsExcluded(row)).map(row => {
      const maximum = Math.max(0, Math.trunc(row.affordable));
      return {...row,plannedCompletions:maximumMode ? maximum : Math.min(totalCompletions,maximum)};
    });
    if (!ready.length) return;
    const projectedProblems = ready.flatMap(row => budgetDecision(row.cost, 'resources', row.plannedCompletions, playerDocument).problems);
    if (projectedProblems.length) {
      alert(`${either('Ресурсный обмен заблокирован единым бюджетом','Resource exchange blocked by unified budget')}:\n\n${[...new Set(projectedProblems)].join('\n')}`);
      return;
    }
    const lines = ready.map((row,index) => `${index + 1}. ${row.buildingName} — ${row.name} ×${row.plannedCompletions}`);
    const heading = maximumMode ? either('Выполнить рассчитанный максимальный обмен?','Run the calculated maximum exchange?') : either(`Выполнить ресурсные задания? Выбранный предел: ×${totalCompletions}.`,`Run resource tasks? Selected limit: ×${totalCompletions}.`);
    if (!confirm(`${heading}\n\n${lines.join('\n')}`)) return;
    if (hkRunner.running) { alert(either('Сначала завершите текущую задачу','Finish the current task first')); return; }
    hkRunner.start({title:either('Ресурсные здания','Resource buildings'),total:ready.length,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});
    resourceBusy = true; renderResources();
    let completed = 0, completions = 0;
    try {
      for (const row of ready) {
        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');
        await hkRunner.waitIfPaused();
        hkRunner.setStep(row.name || either('Ресурсное задание','Resource task'), completed, ready.length);
        log(either(`Выполняю: ${row.name} ×${row.plannedCompletions}…`,`Running: ${row.name} ×${row.plannedCompletions}…`));
        const request = async numberOfCompletions => {
          const quantity = Math.max(1, Math.trunc(Number(numberOfCompletions || 0)));
          const decision = budgetDecision(row.cost, 'resources', quantity, playerDocument);
          if (!decision.allowed) throw new Error(decision.problems.join('; '));
          const before = new Map(costParts(row.cost).map(part => [part.id, walletAmount(part.id, playerDocument)]));
          const value = await apiJson('/player/event','POST',{
            event_building_id:row.roomId,
            tier:row.tier,
            side_event_id:row.sideEventId || undefined,
            number_of_completions:quantity
          },true,0);
          for (const part of costParts(row.cost)) appendExpense({section:'resources', lotId:`resource:${row.buildingId}:${row.roomId}:${row.sideEventId || row.eventId}`, name:row.name || either('Ресурсный обмен','Resource exchange'), currencyId:part.id, amount:part.quantity * quantity, balanceBefore:before.get(part.id), balanceAfter:null, status:'ok', result:`completed ${quantity}`});
          return value;
        };
        if (row.plannedCompletions <= 1000) {
          await request(row.plannedCompletions);
        } else {
          try {
            await request(row.plannedCompletions);
          } catch (error) {
            if (!/HTTP (400|422)|invalid|not allowed/i.test(String(error?.message || error))) throw error;
            const requestCount=Math.ceil(row.plannedCompletions / 1000);
            if (requestCount > 10 && !confirm(either(`Игра не приняла объединённый обмен ×${row.plannedCompletions}. Для задания «${row.name}» потребуется ${requestCount.toLocaleString(locale())} отдельных запросов. Продолжить?`,`The game rejected the combined ×${row.plannedCompletions} exchange. Task “${row.name}” requires ${requestCount.toLocaleString(locale())} separate requests. Continue?`))) throw new Error(either('Выполнение большого обмена отменено пользователем.','Large exchange cancelled by the user.'));
            log(either('Сервер не принял объединённый обмен — разбиваю его на части без паузы.','The server rejected the combined exchange — splitting it into chunks without delay.'),'warn');
            let remaining = row.plannedCompletions;
            let processedRequests = 0;
            while (remaining > 0) {
              if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');
              await hkRunner.waitIfPaused();
              const chunk = Math.min(1000, remaining);
              await request(chunk);
              remaining -= chunk;
              processedRequests += 1;
              if (requestCount > 10 && (processedRequests % 25 === 0 || remaining === 0)) log(either(`Обмен «${row.name}»: запросов ${processedRequests.toLocaleString(locale())}/${requestCount.toLocaleString(locale())}`,`Exchange “${row.name}”: requests ${processedRequests.toLocaleString(locale())}/${requestCount.toLocaleString(locale())}`));
            }
          }
        }
        completions += row.plannedCompletions;
        completed += 1;
      }
      log(either(`Ресурсные задания выполнены: ${completed}, всего выполнений: ${completions}`,`Resource tasks completed: ${completed}, total completions: ${completions}`),'ok');
      resourceBusy = false;
      await loadResources(false);
      await hkAuthoritativePlayerRead('resources-complete');
      hkRunner.finish(either('Ресурсные задания завершены','Resource tasks completed'));
    } catch (error) {
      if (error?.name === 'AbortError') { hkRunner.reset(); log(either('Ресурсные задания остановлены','Resource tasks stopped'),'warn'); }
      else { hkRunner.fail(error); log(either('Ошибка выполнения ресурсного задания','Resource task error') + ': ' + (error?.message || error),'bad'); }
    } finally {
      resourceBusy = false; renderResources();
    }
  }

  function exportMobileSettings() {
    const documentValue = {...load(), exportedAt:Date.now(), exportVersion:VERSION};
    delete documentValue.deviceId;
    delete documentValue.watermarkCode;
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([JSON.stringify(documentValue, null, 2)], {type:'application/json'}));
    link.download = `HamsterKingMobile_settings_${VERSION}.json`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  }

  function importMobileSettings() {
    const input = document.createElement('input'); input.type = 'file'; input.accept = 'application/json,.json';
    input.onchange = async () => {
      try {
        const file = input.files?.[0]; if (!file) return;
        const imported = JSON.parse(await file.text());
        if (!imported || typeof imported !== 'object' || Array.isArray(imported)) throw new Error(either('Некорректный файл','Invalid file'));
        if (!confirm(either('Восстановить настройки из файла? Текущие настройки будут объединены с импортированными.', 'Restore settings from this file? Current settings will be merged with imported settings.'))) return;
        const current = load();
        const merged = {...current, ...imported, deviceId:current.deviceId || getDeviceId(), watermarkCode:current.watermarkCode, _settingsUpdatedAt:Date.now()};
        delete merged.exportedAt; delete merged.exportVersion;
        localStorage.setItem(STORE, JSON.stringify(merged));
        queueSettingsSync(merged);
        location.reload();
      } catch (error) { alert(`${either('Не удалось восстановить настройки','Could not restore settings')}: ${error.message}`); }
    };
    input.click();
  }

  function dailyConfirmationText(actions) {
    const totals = dailyPlanTotals(actions);
    const lines = actions.map((action,index) => `${index + 1}. ${action.label}${action.count > 1 ? ` ×${action.count}` : ''}${action.kind === 'purchase' ? ` — ${costParts(action.cost).map(part => `${part.quantity * (action.count || 1)} ${paymentLabel(part.id)}`).join(' + ')}` : ` — ${either('без расходов','no cost')}`}`);
    const costs = [...totals.values()].filter(part => part.quantity > 0).map(part => `${part.quantity.toLocaleString(locale())} ${paymentLabel(part.id)}`);
    return `${either('Выполнить выбранные действия?','Run selected actions?')}\n\n${lines.join('\n')}\n\n${either('Максимальный расход','Maximum spend')}: ${costs.length ? costs.join(' + ') : '0'}`;
  }

  async function executeDailyPurchase(action) {
    playerDocument = await apiJson('/player/me', 'POST');
    if (action.section === 'fair') {
      let purchased = 0;
      const errors = [];
      for (const target of action.slots || []) {
        if (hkRunner.running) await hkRunner.waitIfPaused();
        try {
          fairDocument = playerDocument;
          const state = fairState(target.fairId, playerDocument);
          const slot = (state?.fair_slots || []).find(value => String(value?.id) === String(target.slotId));
          const live = fairCatalog.find(row => row.lotId === String(slot?.shop_lot_id || ''));
          if (!slot || slot.is_bought || !live) throw new Error(either('лот ярмарки больше недоступен','fair lot is no longer available'));
          if (live.lotId !== action.row.lotId || costSignature(live.cost) !== action.signature) throw new Error(either('лот или цена изменились — покупка пропущена','lot or price changed — purchase skipped'));
          const decision = budgetDecision(live.cost, 'fair', 1, playerDocument);
          if (!decision.allowed) throw new Error(decision.problems.join('; '));
          const before = new Map(costParts(live.cost).map(part => [part.id, walletAmount(part.id, playerDocument)]));
          const result = await apiJson('/shop/buy', 'POST', {shop_lot_id:live.lotId, payment_type:'INTERNAL', fair_id:target.fairId,
            slot_id:slot.id, lotName:live.name, lotDescription:''});
          playerDocument = result; fairDocument = result; purchased++;
          for (const part of costParts(live.cost)) appendExpense({section:'fair', lotId:live.lotId, name:gameText(live.name) || live.name,
            currencyId:part.id, amount:part.quantity, balanceBefore:before.get(part.id), balanceAfter:walletAmount(part.id, result), status:'ok', result:'purchased'});
        } catch (error) {
          if (error?.name === 'AbortError' || hkRunner.signal?.aborted) throw error;
          errors.push(error.message);
          log(`${action.label}: ${error.message}`, 'warn');
        }
      }
      if (!purchased && errors.length) throw new Error(errors[0]);
      return;
    }
    const requested = Math.max(1, Math.floor(Number(action.count || 1)));
    for (let index = 0; index < requested; index++) {
      if (hkRunner.running) await hkRunner.waitIfPaused();
      // Reload both the player balance and the live shop counters before every
      // purchase. A changed price, exhausted lot or budget limit skips the
      // remaining copies instead of spending by stale data.
      playerDocument = await apiJson('/player/me', 'POST');
      shopViewDocument = await apiJson('/shop/view', 'GET');
      dailyShopRows = normalizeRegularShop();
      const live = dailyShopRows.find(row => row.lotId === action.row.lotId);
      if (!live || live.remaining <= 0) throw new Error(either(`лот закончился после ${index} покупок`,`lot exhausted after ${index} purchases`));
      if (costSignature(live.cost) !== action.signature) throw new Error(either('цена изменилась — остальные покупки пропущены','price changed — remaining purchases skipped'));
      const decision = budgetDecision(live.cost, action.section, 1, playerDocument);
      if (!decision.allowed) throw new Error(decision.problems.join('; '));
      const before = new Map(costParts(live.cost).map(part => [part.id, walletAmount(part.id, playerDocument)]));
      const result = await apiJson('/shop/buy', 'POST', {shop_lot_id:live.lotId, payment_type:'INTERNAL', lotName:live.name, lotDescription:''});
      playerDocument = result;
      for (const part of costParts(live.cost)) appendExpense({section:action.section, lotId:live.lotId, name:gameText(live.name) || live.name,
        currencyId:part.id, amount:part.quantity, balanceBefore:before.get(part.id), balanceAfter:walletAmount(part.id, result), status:'ok', result:`purchased ${index + 1}/${requested}`});
      if (index + 1 < requested) await sleep(250);
    }
  }

  async function runDailySelected() {
    if (!requireLicense() || dailyRunning) return;
    const actions = selectedDailyActions();
    if (!actions.length) return;
    const blocked = actions.flatMap(action => action.kind === 'purchase'
      ? budgetDecision(action.cost, action.section, action.count).problems.map(problem => action.label + ': ' + problem)
      : []);
    if (blocked.length) {
      alert(either('План заблокирован настройками бюджета','Plan blocked by budget settings') + ':\n\n' + blocked.join('\n'));
      return;
    }
    if (!confirm(dailyConfirmationText(actions))) return;
    if (hkRunner.running) { alert(either('Сначала завершите текущую задачу','Finish the current task first')); return; }
    hkRunner.start({title:either('Сегодня','Today'),total:actions.length,step:either('Подготовка плана','Preparing plan')});
    dailyRunning = true; renderDailyTasks();
    let completed = 0, skipped = 0;
    try {
      for (const action of actions) {
        if (hkRunner.signal?.aborted) break;
        await hkRunner.waitIfPaused();
        hkRunner.setStep(action.label, completed + skipped, actions.length);
        try {
          log(`${either('Выполняю','Running')}: ${action.label}`);
          if (action.kind === 'rumors') await runDailyRumors(true);
          else if (action.kind === 'advertisement') await runDailyAd(true);
          else if (action.kind === 'pit') await executeDailyPit(action);
          else if (action.kind === 'purchase') await executeDailyPurchase(action);
          completed++;
        } catch (error) {
          if (error?.name === 'AbortError' || hkRunner.signal?.aborted) break;
          skipped++;
          if (action.kind === 'purchase') for (const part of costParts(action.cost)) appendExpense({section:action.section, lotId:action.row?.lotId,
            name:action.label, currencyId:part.id, amount:part.quantity * Math.max(1, Number(action.count || 1)), status:'failed', result:error.message});
          log(`${either('Пропущено','Skipped')} «${action.label}»: ${error.message}`, 'warn');
        }
        if (action.kind === 'purchase') {
          dailySelection[action.id] = false;
          dailyPurchaseCounts[action.id] = 0;
          saveDailySelection();
        }
        hkRunner.advance();
        await sleep(300);
      }
      const stopped=!!hkRunner.signal?.aborted;
      if (stopped) hkRunner.reset();
      playerDocument = await apiJson('/player/me', 'POST');
      shopViewDocument = await apiJson('/shop/view', 'GET');
      dailyShopRows = normalizeRegularShop();
      dailySnapshot = {checkedAt:Date.now(), playerId:playerIdentity(playerDocument?.player || {}), periodStart:gamePeriodBounds().dayStart};
      save({today:{...(load().today || {}), selection:{...dailySelection}, snapshot:dailySnapshot}, budget:budgetDocument()});
      log(stopped ? either(`Выполнение остановлено: завершено ${completed}, пропущено ${skipped}`,`Execution stopped: completed ${completed}, skipped ${skipped}`) : either(`Выбранные действия завершены: ${completed}, пропущено ${skipped}`, `Selected actions completed: ${completed}, skipped ${skipped}`), stopped || skipped ? 'warn' : 'ok');
      if (!stopped) hkRunner.finish(either('План выполнен','Plan completed'));
    } catch (error) {
      hkRunner.fail(error); throw error;
    } finally { dailyRunning = false; renderDailyTasks(); }
  }

  async function runDailyClanPurchases() {
    if (!requireLicense() || dailyRunning) return;
    if (!dailyShopRows.length) { await refreshDailyTasks(); if (!dailyShopRows.length) return; }
    const groups = dailyTaskGroups();
    const plan = [...groups.recruits, ...groups.cartels, ...groups.investments]
      .filter(row => row.safe && row.remaining > 0 && row.affordable);
    if (!plan.length) { log(either('Доступных ежедневных покупок нет.', 'No daily purchases are available.'), 'warn'); renderDailyTasks(); return; }
    if (!confirm(either(`Выполнить доступные ежедневные покупки: ${plan.length}? Покупки необратимы.`, `Complete ${plan.length} available daily purchases? Purchases are irreversible.`))) return;
    dailyRunning = true; renderDailyTasks();
    let completed = 0;
    try {
      for (const row of plan) {
        log(either(`Ежедневная покупка ${completed + 1}/${plan.length}…`, `Daily purchase ${completed + 1}/${plan.length}…`));
        playerDocument = await apiJson('/shop/buy', 'POST', {shop_lot_id:row.lotId, payment_type:'INTERNAL', lotName:row.name, lotDescription:''});
        completed++;
        await sleep(300);
      }
      dailyShopRows = normalizeRegularShop();
      log(either(`Ежедневные покупки завершены: ${completed}`, `Daily purchases completed: ${completed}`), 'ok');
    } catch (error) {
      dailyShopRows = normalizeRegularShop();
      log(`${either('Остановка ежедневных покупок', 'Daily purchases stopped')}: ${error.message}`, 'bad');
    } finally {
      dailyRunning = false; renderDailyTasks();
    }
  }

  async function licensedServerJson(base, path, body = {}, retry = true, label = 'server') {
    if (!licenseState.token) await checkLicense(playerDocument?.player || {}, true);
    if (!licenseState.token) throw new Error('Лицензия недоступна');
    const retries = retry ? SERVER_REQUEST_RETRY_DELAYS_MS.length : 0;
    let attempt = 0;
    let licenseRetryLeft = retry ? 1 : 0;
    while (true) {
      const request = nativeNetworkFetch || window.fetch.bind(window);
      const started = performance.now();
      let response,text;
      try {
        ({response,text}=await gameFetchText(request,`${base}${path}`,{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${licenseState.token || ''}`},body:JSON.stringify(body)},18000));
      } catch (error) {
        if(error?.name==='AbortError')throw error;
        recordDiagnostic('server-network-error',{label,path,attempt:attempt+1,error:error?.message || error});
        if (attempt < retries) { const delay=SERVER_REQUEST_RETRY_DELAYS_MS[Math.min(attempt,SERVER_REQUEST_RETRY_DELAYS_MS.length-1)]; attempt += 1; await gameRetryDelay(delay); continue; }
        setHealth('server', false, error?.name==='HKNetworkTimeout'?'тайм-аут':'ошибка сети');
        throw error;
      }
      let value; try { value = JSON.parse(text); } catch (_) { value = null; }
      recordDiagnostic('server-request',{label,path,status:response.status,attempt:attempt+1,durationMs:Math.round(performance.now()-started)});
      if (response.status === 401 && licenseRetryLeft > 0) {
        licenseRetryLeft -= 1;
        await checkLicense(playerDocument?.player || {}, true);
        if (licenseState.token) { attempt = 0; continue; }
      }
      const transient = response.status === 408 || response.status === 425 || response.status === 429 || response.status >= 500;
      if (transient && attempt < retries) {
        const delay=SERVER_REQUEST_RETRY_DELAYS_MS[Math.min(attempt,SERVER_REQUEST_RETRY_DELAYS_MS.length-1)]; attempt += 1; await gameRetryDelay(delay); continue;
      }
      if (!response.ok || !value) {
        setHealth('server', false, `HTTP ${response.status}`);
        throw new Error(`HTTP ${response.status}: ${text.slice(0, 120)}`);
      }
      setHealth('server', true, 'сервер отвечает');
      return value;
    }
  }

  async function recipeServerJson(path, body = {}, retry = true) { return licensedServerJson(RECIPE_API_BASE, path, body, retry, 'recipes'); }
  async function pitServerJson(path, body = {}, retry = true) { return licensedServerJson(PIT_API_BASE, path, body, retry, 'pits'); }

  async function loadSharedPitPowers(force = false) {
    if (pitCatalogLoaded && !force) return sharedPitRows;
    try {
      const result = await pitServerJson('/list');
      sharedPitRows = Array.isArray(result.rows) ? result.rows : [];
      pitCatalogLoaded = true;
      if (root) renderPitForecast();
    } catch (error) { console.warn('[HK] shared pit catalog failed', error); }
    return sharedPitRows;
  }

  function settingsForServer(documentValue = load()) {
    const result = {...(documentValue || {})};
    delete result.deviceId;
    delete result.watermarkCode;
    return result;
  }

  function hasUserSettings(documentValue) {
    return Object.keys(documentValue || {}).some(key => !['deviceId', 'watermarkCode', '_settingsUpdatedAt'].includes(key));
  }

  async function settingsServerJson(path, body = {}, retry = true) { return licensedServerJson(SETTINGS_API_BASE, path, body, retry, 'settings'); }
  async function clanSkillsServerJson(path, body = {}, retry = true) { return licensedServerJson(CLAN_SKILLS_API_BASE, path, body, retry, 'clan-skills'); }
  function queueSettingsSync(snapshot = load()) {
    if (!settingsSyncReady || !licenseState.allowed) return;
    clearTimeout(settingsSyncTimer);
    settingsSyncTimer = setTimeout(async () => {
      try { await settingsServerJson('/save', {settings:settingsForServer(snapshot)}); }
      catch (error) { console.warn('[HK] settings backup failed', error); }
    }, 1200);
  }

  async function synchronizeSettings() {
    if (settingsSyncPromise || !licenseState.allowed) return settingsSyncPromise;
    settingsSyncPromise = (async () => {
      try {
        const response = await settingsServerJson('/load');
        const remote = response.settings && typeof response.settings === 'object' ? response.settings : {};
        const local = load();
        const localTime = Number(local._settingsUpdatedAt || 0);
        const remoteTime = Number(response.updated_at || remote._settingsUpdatedAt || 0);
        if (hasUserSettings(remote) && (!hasUserSettings(local) || remoteTime > localTime)) {
          const restored = {...remote, deviceId:local.deviceId || getDeviceId(), watermarkCode:local.watermarkCode};
          localStorage.setItem(STORE, JSON.stringify(restored));
          settingsSyncReady = true;
          location.reload();
          return;
        }
        if (hasUserSettings(local)) {
          if (!localTime) {
            local._settingsUpdatedAt = Date.now();
            localStorage.setItem(STORE, JSON.stringify(local));
          }
          await settingsServerJson('/save', {settings:settingsForServer(local)});
        }
        settingsSyncReady = true;
      } catch (error) {
        settingsSyncReady = true;
        console.warn('[HK] settings synchronization failed', error);
      } finally {
        settingsSyncPromise = null;
      }
    })();
    return settingsSyncPromise;
  }

  async function mapServerJson(path, body = {}, retry = true) { return licensedServerJson(MAP_API_BASE, path, body, retry, 'maps'); }
  function cityLabel(row) {
    return gameText(row?.name || row?.city_name || row?.city_id || '');
  }

  async function mapAreaPayload(area, cities = []) {
    const areaId = String(area?.gamearea_id || area?.area_id || '');
    const cityId = String(area?.city_id || '');
    const [full, definitions] = await Promise.all([apiJson(`/game_area/${areaId}`, 'GET'), apiJson(`/game_area/${areaId}/buildings`, 'GET')]);
    const playerBuildings = new Map((playerDocument?.buildings || []).map(row => [String(row?.id || ''), row]));
    const invest = new Set(full?.info?.invest_building_list || []);
    const buildings = (Array.isArray(definitions) ? definitions : []).map(row => {
      const id = String(row?.building_id || ''); const state = playerBuildings.get(id); mapBuildingAreas.set(id, areaId);
      const detectedRooms=state ? crystalRoomCount(state) : null;
      return {building_id:id, opened:!!state, room_count:detectedRooms ?? (state && state.has_events === false ? 0 : null), has_events:!!state?.has_events,
        is_invest:invest.has(id), tier:state?.tier ?? null, faction:String(row?.faction || ''), building_type:String(row?.meta?.building_generator || row?.meta?.building_type || '')};
    });
    const city = cities.find(row => String(row?.id) === cityId) || {};
    return {area_id:areaId, city_id:cityId, city_name:cityLabel(city), x:full?.info?.x ?? full?.meta?.gamearea_coords?.x,
      y:full?.info?.y ?? full?.meta?.gamearea_coords?.y, invest_count:Number(full?.info?.invest_count || invest.size),
      expected_buildings:Math.max(buildings.length, Number(full?.meta?.buildings_total || 0)), buildings};
  }

  async function submitOwnedMapAreas(all = true) {
    if (!requireLicense() || mapScanning || !playerDocument) return;
    if (hkRunner.running) { alert(either('Сначала завершите текущую задачу','Finish the current task first')); return; }
    mapScanning = true;
    try {
      await ensureRecipeMetadata();
      const cities = await apiJson('/cities', 'GET');
      const owned = (playerDocument?.areas?.areas || []).filter(row => row?.gamearea_id);
      const currentId = String(playerDocument?.gameArea?.gamearea_id || '');
      const selected = all ? owned : owned.filter(row => String(row.gamearea_id) === currentId).slice(0,1);
      hkRunner.start({title:either('Исследование районов','District research'),total:selected.length,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});
      for (let index=0; index<selected.length; index++) {
        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');
        await hkRunner.waitIfPaused();
        hkRunner.setStep(either('Исследование района','Researching district'),index,selected.length);
        log(either(`Исследую район ${index+1}/${selected.length}…`,`Researching district ${index+1}/${selected.length}…`));
        const payload = await mapAreaPayload(selected[index], Array.isArray(cities) ? cities : []);
        await mapServerJson('/submit', {area:payload});
        await gameRetryDelay(180);
      }
      const completedAt = Date.now();
      if (all) {
        const playerId = playerIdentity(playerDocument?.player);
        if (playerId) save({mapContributionByPlayer:{...(load().mapContributionByPlayer || {}), [playerId]:completedAt}});
      }
      save({lastMapContribution:completedAt});
      log(either(`Карты отправлены: районов ${selected.length}`,`Maps submitted: ${selected.length} districts`),'ok');
      await loadMapIndex(false);
      hkRunner.finish(either('Исследование районов завершено','District research completed'));
    } catch (error) {
      if (error?.name === 'AbortError') { hkRunner.reset(); log(either('Исследование районов остановлено','District research stopped'),'warn'); }
      else { hkRunner.fail(error); log(either('Ошибка исследования карт','Map research error') + ': ' + (error?.message || error),'bad'); }
    }
    finally { mapScanning=false; }
  }

  async function loadMapIndex(contribute = false) {
    if (!requireLicense()) return;
    try {
      if (contribute && Date.now()-Number(load().lastMapContribution || 0)>86400000) await submitOwnedMapAreas(true);
      const result = await mapServerJson('/list'); mapRows = Array.isArray(result.maps) ? result.maps : []; mapDetail=null; renderMapIndex();
      log(either(`В индексе районов: ${mapRows.length}`,`Districts in index: ${mapRows.length}`),'ok');
    } catch (error) { log(`${either('Ошибка индекса карт','Map index error')}: ${error.message}`,'bad'); }
  }

  function ownedMapIds() {
    return new Set((playerDocument?.areas?.areas || []).map(row => String(row?.gamearea_id || row?.area_id || '')).filter(Boolean));
  }

  function setMapSource(source) {
    mapSource = source === 'uploaded' ? 'uploaded' : 'mine';
    mapDetail = null;
    renderMapIndex();
  }

  function renderMapIndex() {
    if (!mapIndexBox || !mapDetailBox) return;
    mapDetailBox.style.display='none'; mapIndexBox.style.display='block';
    const query=clean(root.querySelector('#hk-map-search')?.value).toLowerCase(); const sort=root.querySelector('#hk-map-sort')?.value || 'rating';
    const owned = ownedMapIds();
    root.querySelectorAll('[data-map-source]').forEach(button => {
      button.classList.toggle('active', button.dataset.mapSource === mapSource);
      const count = button.dataset.mapSource === 'mine' ? owned.size : mapRows.length;
      const label = button.dataset.mapSource === 'mine' ? tr('myMaps') : tr('uploadedMaps');
      button.textContent = `${label} · ${count}`;
    });
    const belongsToAccount = row => [String(row.area_id || ''), ...(Array.isArray(row.aliases) ? row.aliases.map(String) : [])].some(id => owned.has(id));
    const sourceRows = mapSource === 'mine' ? mapRows.filter(belongsToAccount) : mapRows;
    const rows=sourceRows.filter(row => `${row.city_name} ${row.x}:${row.y}`.toLowerCase().includes(query)).sort((a,b) => sort==='city' ? String(a.city_name).localeCompare(String(b.city_name)) : Number(b[sort]||0)-Number(a[sort]||0));
    const scanButton=root.querySelector('#hk-map-scan'), loadButton=root.querySelector('#hk-map-load');
    if (scanButton) scanButton.style.display = mapSource === 'mine' ? '' : 'none';
    if (loadButton) { loadButton.style.display = mapSource === 'uploaded' ? '' : 'none'; loadButton.textContent=tr('refreshUploadedMaps'); }
    const list=root.querySelector('#hk-map-list');
    const emptyMessage = mapSource === 'mine'
      ? either('Нажмите «Считать карты аккаунта», чтобы добавить все районы этого аккаунта.','Tap “Read account maps” to add every district from this account.')
      : either('Загруженные карты пока отсутствуют.','There are no uploaded maps yet.');
    list.innerHTML=rows.length ? rows.map(row => {
      const gameAreaId = mapSource === 'mine' ? [String(row.area_id || ''), ...(Array.isArray(row.aliases) ? row.aliases.map(String) : [])].find(id => owned.has(id)) : String(row.area_id || '');
      return `<button class="hk-map-row" data-area="${escapeHtml(row.area_id)}" data-game-area="${escapeHtml(gameAreaId || row.area_id)}"><b>${escapeHtml(row.city_name || row.city_id)}</b><span>${row.x ?? '?'}:${row.y ?? '?'}</span><span>${tr('mapBuildings')}: ${Number(row.opened||0).toLocaleString(locale())}</span><span>${tr('mapUnexplored')}: ${Number(row.unexplored||0).toLocaleString(locale())}</span><span>${tr('mapRooms')}: ${Number(row.total_rooms||0).toLocaleString(locale())}</span><span class="hk-progress">${row.progress}%</span><strong>${row.rating||0} ›</strong></button>`;
    }).join('') : `<p class="hk-muted">${emptyMessage}</p>`;
    list.querySelectorAll('[data-area]').forEach(button => button.onclick=()=>openMapDetail(button.dataset.area,button.dataset.gameArea));
  }

  async function openMapDetail(areaId, gameAreaId = areaId) {
    try {
      mapZoom=1; mapPanX=0; mapPanY=0;
      const result = await mapServerJson('/detail',{area_id:areaId});
      let full = null;
      try { full = await apiJson(`/game_area/${encodeURIComponent(gameAreaId || areaId)}`, 'GET'); }
      catch (_) { log(either('Данные карты загружены без игровой геометрии района','Map data loaded without the district game geometry'),'warn'); }
      mapDetail=result.detail;
      mapGeometry=full?.geo_json_buildings || null;
      (mapDetail?.buildings || []).forEach(row=>mapBuildingAreas.set(String(row.building_id||''),String(areaId)));
      renderMapDetail();
    }
    catch(error){log(`${either('Ошибка карты','Map error')}: ${error.message}`,'bad');}
  }

  function mapFeatureId(feature) {
    return String(feature?.id ?? feature?.properties?.id ?? feature?.properties?.building_id ?? feature?.properties?.buildingId ?? '');
  }

  function mapGeometryFeatures(value) {
    if (!value) return [];
    if (typeof value === 'string') { try { value=JSON.parse(value); } catch (_) { return []; } }
    if (Array.isArray(value)) return value;
    return Array.isArray(value.features) ? value.features : [];
  }

  function mapCoordinatePairs(value, result=[]) {
    if (!Array.isArray(value)) return result;
    if (value.length>=2 && Number.isFinite(Number(value[0])) && Number.isFinite(Number(value[1]))) result.push([Number(value[0]),Number(value[1])]);
    else value.forEach(item=>mapCoordinatePairs(item,result));
    return result;
  }

  function mapPolygonRings(geometry) {
    if (!geometry) return [];
    if (geometry.type==='Polygon') return geometry.coordinates || [];
    if (geometry.type==='MultiPolygon') return (geometry.coordinates || []).flat();
    return [];
  }

  function mapBuildingMatches(row, status, rooms, type, faction) {
    return (status==='all' || (status==='opened' && !!row.opened) || (status==='unknown' && row.room_count==null)) &&
      (rooms==='all' || (rooms==='5' ? Number(row.room_count)>=5 : String(row.room_count)===rooms)) &&
      (type==='all' || (type==='invest' && !!row.is_invest) || (type==='normal' && !row.is_invest)) &&
      (faction==='all' || row.faction===faction);
  }

  function mapBuildingColor(row) {
    if (row.room_count==null) return '#d7a93d';
    const rooms=Number(row.room_count||0);
    return ['#34435a','#35c77a','#21b8d7','#4285f4','#9b67ed','#78efff'][Math.min(rooms,5)];
  }

  function mapVisualMarkup(features, rows, filters) {
    const allPoints=features.flatMap(feature=>mapCoordinatePairs(feature?.geometry?.coordinates));
    if (!allPoints.length) return `<p class="hk-muted">${either('Геометрия района недоступна','District geometry is unavailable')}</p>`;
    const xs=allPoints.map(point=>point[0]), ys=allPoints.map(point=>point[1]);
    const minX=Math.min(...xs), maxX=Math.max(...xs), minY=Math.min(...ys), maxY=Math.max(...ys);
    const rawWidth=Math.max(maxX-minX,0.0000001), rawHeight=Math.max(maxY-minY,0.0000001);
    const scale=1000/Math.max(rawWidth,rawHeight), width=rawWidth*scale, height=rawHeight*scale, pad=20;
    const rowById=new Map(rows.map(row=>[String(row.building_id),row]));
    const paths=features.map((feature,index)=>{
      const id=mapFeatureId(feature); const row=rowById.get(id) || {building_id:id,opened:false,room_count:null,is_invest:false,faction:'',tier:null,building_type:''};
      const rings=mapPolygonRings(feature.geometry); if(!rings.length) return '';
      const d=rings.map(ring=>ring.map((point,i)=>{
        const x=(Number(point[0])-minX)*scale, y=(maxY-Number(point[1]))*scale;
        return `${i?'L':'M'}${x.toFixed(2)} ${y.toFixed(2)}`;
      }).join(' ')+' Z').join(' ');
      const matches=mapBuildingMatches(row,...filters); const fill=mapBuildingColor(row); const title=`${id || index} · ${row.room_count==null?'?':row.room_count} 💎${row.is_invest?' · ◆':''}`;
      return `<path class="hk-map-shape${matches?' match':' dim'}" data-map-building="${escapeHtml(id)}" d="${d}" fill="${fill}" opacity="${matches?0.94:0.16}" stroke="${row.is_invest?'#ffd761':'#172233'}" stroke-width="${row.is_invest?1.8:0.7}" vector-effect="non-scaling-stroke"><title>${escapeHtml(title)}</title></path>`;
    }).join('');
    return `<svg viewBox="${-pad} ${-pad} ${width+pad*2} ${height+pad*2}" preserveAspectRatio="xMidYMid meet" aria-label="${either('Карта района','District map')}">${paths}</svg>`;
  }

  function applyMapZoom() {
    const visual = root?.querySelector('#hk-map-visual');
    const svg = visual?.querySelector('svg');
    if (svg) svg.style.transform = `translate(${mapPanX}px,${mapPanY}px) scale(${mapZoom})`;
    const label = root?.querySelector('#hk-map-zoom-value');
    if (label) label.textContent = `${Math.round(mapZoom * 100)}%`;
    root?.querySelector('#hk-map-zoom-out')?.toggleAttribute('disabled', mapZoom <= 1);
    root?.querySelector('#hk-map-zoom-in')?.toggleAttribute('disabled', mapZoom >= 8);
  }

  function changeMapZoom(nextZoom, centerX = null, centerY = null) {
    const visual = root?.querySelector('#hk-map-visual');
    const previous = mapZoom;
    mapZoom = Math.min(8, Math.max(1, Number(nextZoom) || 1));
    if (mapZoom === 1) { mapPanX = 0; mapPanY = 0; }
    else if (visual && centerX != null && centerY != null && previous > 0) {
      const rect = visual.getBoundingClientRect();
      const x = centerX - rect.left - rect.width / 2, y = centerY - rect.top - rect.height / 2;
      const factor = mapZoom / previous;
      mapPanX = x - (x - mapPanX) * factor;
      mapPanY = y - (y - mapPanY) * factor;
    }
    applyMapZoom();
  }

  function resetMapZoom() {
    mapZoom = 1; mapPanX = 0; mapPanY = 0; applyMapZoom();
  }

  function installMapZoom(visual) {
    const pointers = new Map();
    let drag = null, pinch = null;
    visual.onwheel = event => {
      event.preventDefault();
      changeMapZoom(mapZoom * (event.deltaY < 0 ? 1.25 : .8), event.clientX, event.clientY);
    };
    visual.onpointerdown = event => {
      pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});
      visual.setPointerCapture?.(event.pointerId);
      mapPointerMoved = false;
      if (pointers.size === 1) drag={x:event.clientX,y:event.clientY,panX:mapPanX,panY:mapPanY};
      if (pointers.size === 2) {
        const [a,b]=[...pointers.values()];
        pinch={distance:Math.hypot(a.x-b.x,a.y-b.y),zoom:mapZoom};
      }
    };
    visual.onpointermove = event => {
      if (!pointers.has(event.pointerId)) return;
      pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});
      if (pointers.size >= 2 && pinch) {
        const [a,b]=[...pointers.values()];
        const distance=Math.hypot(a.x-b.x,a.y-b.y);
        if (Math.abs(distance-pinch.distance)>3) mapPointerMoved=true;
        changeMapZoom(pinch.zoom * distance / Math.max(1,pinch.distance),(a.x+b.x)/2,(a.y+b.y)/2);
      } else if (drag && mapZoom > 1) {
        const dx=event.clientX-drag.x, dy=event.clientY-drag.y;
        if (Math.abs(dx)+Math.abs(dy)>4) mapPointerMoved=true;
        mapPanX=drag.panX+dx; mapPanY=drag.panY+dy; applyMapZoom();
      }
    };
    const release = event => {
      pointers.delete(event.pointerId);
      if (pointers.size < 2) pinch=null;
      if (pointers.size === 1) { const value=[...pointers.values()][0]; drag={x:value.x,y:value.y,panX:mapPanX,panY:mapPanY}; }
      else if (!pointers.size) drag=null;
      setTimeout(()=>{ if (!pointers.size) mapPointerMoved=false; },80);
    };
    visual.onpointerup=release; visual.onpointercancel=release;
    applyMapZoom();
  }

  function renderMapDetail() {
    if (!mapDetail) return;
    mapIndexBox.style.display='none'; mapDetailBox.style.display='block'; const area=mapDetail.area||{};
    root.querySelector('#hk-map-detail-title').textContent=`${area.city_name || area.city_id} · ${area.x ?? '?'}:${area.y ?? '?'}`;
    const status=root.querySelector('#hk-map-status-filter')?.value || 'all', rooms=root.querySelector('#hk-map-room-filter')?.value || 'all', type=root.querySelector('#hk-map-type-filter')?.value || 'all', faction=root.querySelector('#hk-map-faction-filter')?.value || 'all';
    const allRows=mapDetail.buildings || [];
    const factions=[...new Set(allRows.map(row=>row.faction).filter(Boolean))].sort(); const fs=root.querySelector('#hk-map-faction-filter');
    if(fs && fs.options.length<=1) { const selected=fs.value; fs.innerHTML=`<option value="all">${tr('all')}</option>`+factions.map(x=>`<option value="${escapeHtml(x)}">${escapeHtml(x)}</option>`).join(''); fs.value=selected; }
    const features=mapGeometryFeatures(mapGeometry); const visual=root.querySelector('#hk-map-visual');
    visual.innerHTML=mapVisualMarkup(features,allRows,[status,rooms,type,faction]);
    installMapZoom(visual);
    const matched=allRows.filter(row=>mapBuildingMatches(row,status,rooms,type,faction)).length;
    root.querySelector('#hk-map-match-count').textContent=either(`Подходит зданий: ${matched} из ${Math.max(features.length,allRows.length)}`,`Matching buildings: ${matched} of ${Math.max(features.length,allRows.length)}`);
    visual.querySelectorAll('[data-map-building]').forEach(shape=>shape.onclick=()=>{
      if (mapPointerMoved) return;
      const row=allRows.find(item=>String(item.building_id)===shape.dataset.mapBuilding) || {building_id:shape.dataset.mapBuilding,room_count:null};
      root.querySelector('#hk-map-selected').innerHTML=`<b>${escapeHtml(row.building_id||'—')}</b><span>${row.is_invest?'◆ ':''}${escapeHtml(row.faction||either('фракция неизвестна','faction unknown'))} · T${row.tier ?? '?'}</span><strong>${row.room_count==null?'?':row.room_count} 💎</strong><small>${escapeHtml(row.building_type||either('Данные здания ещё не исследованы','Building data has not been researched yet'))}</small>`;
      visual.querySelectorAll('.selected').forEach(item=>item.classList.remove('selected')); shape.classList.add('selected');
    });
  }

  function scaledCostVisual(cost, multiplier) {
    const parts = costParts(cost);
    return parts.length ? parts.map(part => `${fairIconHtml(paymentIcon(part), 'hk-price-icon')}<b>${(part.quantity * multiplier).toLocaleString(locale())}</b>`).join('') : '—';
  }

  function gameText(key) {
    const value = localizationDocument?.[String(key || '')];
    return typeof value === 'string' ? value : String(key || '').replace(/^item_bsn_/, '').replace(/_(?:name|desc)$/, '').replace(/_/g, ' ');
  }

  function recipeRank(value) {
    return ['B','A','S','S+','S++'][Number(value)] || `R${value ?? '?'}`;
  }

  function recipeQuality(value) {
    const quality = Number(value);
    const row = (clientConfigDocument?.qualities || []).find(item => Number(item?.quality) === quality) || {};
    const colors = {white:'#cbd5e1',green:'#49cf74',blue:'#4fa5ff',purple:'#b56cff',yellow:'#ffd34f',orange:'#ff962e',red:'#ff5967',diamond:'#58e2ff',event:'#ff70c9'};
    return {quality, found:!!Object.keys(row).length, colorName:String(row.color || 'white'), color:colors[row.color] || '#cbd5e1', pluses:Number(row.pluses_count || 0),
      buildingTier:Number.isFinite(Number(row.building_tier)) ? Number(row.building_tier) : null};
  }

  function recipeTierFromQuality(quality) {
    if (!quality?.found) return null;
    const tiers = {white:1, green:2, blue:3, purple:4, yellow:5, orange:6};
    return tiers[String(quality.colorName || '').toLowerCase()] ?? quality.buildingTier ?? null;
  }

  function recipeLotColor(item) {
    let colors = item?.meta?.recipe_lot_colors;
    if (typeof colors === 'string') {
      const linked = (shopViewDocument?.shop_lots || []).find(lot => String(lot?.id || '') === colors);
      colors = linked?.lot_view || null;
    }
    if (!colors || typeof colors !== 'object') return '';
    return String(colors.main_border_color || colors.main_light_color || colors.secondary_color || '');
  }

  function recipeMetadata(itemId) {
    const item = (itemCatalogDocument || []).find(row => String(row?.id) === itemId) || {};
    const business = (businessCatalogDocument || []).find(row => String(row?.id) === itemId) || {};
    const bonusById = new Map((bonusCatalogDocument || []).map(row => [String(row?.id || ''), row]));
    const bonuses = (business?.reward_view?.bonuses || []).flatMap(value => {
      const source = bonusById.get(String(value?.bonus_id || '')) || {};
      const view = source.view || {};
      if (!source.id && !value?.bonus_id) return [];
      return [{id:String(source.id || value.bonus_id), caption:gameText(view.caption || source.id || value.bonus_id), value:String(view.value || ''), icon:mediaUrl(view.icon || '')}];
    });
    const quality = recipeQuality(item.rarity_level);
    const idTier = String(itemId || '').match(/^item_bsn_r\d+t(\d+)(?:_|$)/);
    return {
      name:gameText(item.name || itemId), description:gameText(item.desc || ''), icon:mediaUrl(item.icon || '', itemId),
      rarity:Number.isFinite(Number(business.rarity)) ? Number(business.rarity) : null,
      quality:quality.quality, color:recipeLotColor(item) || quality.color, color_name:quality.colorName, pluses:quality.pluses,
      // Recipe quality is authoritative: yellow is T5 and orange is T6.
      // The technical tN fragment is only a fallback for items without
      // quality metadata and must not override the visible game color.
      tier:recipeTierFromQuality(quality) ?? (idTier ? visibleBusinessTier(idTier[1]) : null), bonuses
    };
  }

  function currentRecipeDisplay(row) {
    const meta = recipeMetadata(String(row?.item_id || ''));
    return {...row,
      rarity:meta.rarity ?? row?.rarity,
      tier:meta.tier ?? row?.tier,
      quality:meta.quality ?? row?.quality,
      color:meta.color || row?.color || recipeQuality(row?.quality).color,
      color_name:meta.color_name || row?.color_name,
      pluses:meta.pluses ?? row?.pluses,
      name:meta.name || row?.name,
      description:meta.description || row?.description,
      icon:meta.icon || row?.icon,
      bonuses:meta.bonuses?.length ? meta.bonuses : (row?.bonuses || [])};
  }

  async function ensureRecipeMetadata() {
    const requests = [];
    if (!itemCatalogDocument) requests.push(apiJson('/items', 'GET').then(value => itemCatalogDocument = Array.isArray(value) ? value : []));
    if (!businessCatalogDocument) requests.push(apiJson('/business_items', 'GET').then(value => businessCatalogDocument = value?.businesses || []));
    if (!bonusCatalogDocument) requests.push(apiJson('/bonuses/view', 'GET').then(value => bonusCatalogDocument = Array.isArray(value) ? value : []));
    if (!eventCatalogDocument) requests.push(apiJson('/events', 'GET').then(value => eventCatalogDocument = Array.isArray(value) ? value : []));
    if (!clientConfigDocument) requests.push(apiJson('/client_config', 'GET').then(value => clientConfigDocument = value));
    if (!premiumDocument) requests.push(apiJson('/premium', 'GET').then(value => premiumDocument = value || {}));
    if (!localizationDocument) requests.push(apiJson(`/localization/${language}`, 'GET').then(value => localizationDocument = value));
    await Promise.allSettled(requests);
  }

  function businessPlanFromLot(planId, slotOrder = 0) {
    const id = String(planId || '');
    if (!id.startsWith('mf_craftlot_')) return null;
    const itemId = id.slice('mf_craftlot_'.length);
    const match = itemId.match(/^item_bsn_r(\d+)t(\d+)(?:_|$)/);
    const meta = recipeMetadata(itemId);
    return {plan_id:id, item_id:itemId, rarity:meta.rarity ?? (match ? Number(match[1]) : null), tier:meta.tier ?? (match ? visibleBusinessTier(match[2]) : null),
      quality:meta.quality, color:meta.color, color_name:meta.color_name, pluses:meta.pluses, name:meta.name,
      description:meta.description, icon:meta.icon, bonuses:meta.bonuses, components:[], slot_order:Number(slotOrder || 0)};
  }

  function recipeState(documentValue = fairDocument || playerDocument) {
    let states = fairStates(documentValue);
    let state = recipeFairId ? states.find(value => String(value.id) === String(recipeFairId)) : null;
    state ||= states.find(value => (value.fair_slots || []).some(slot => String(slot?.shop_lot_id || '').startsWith('mf_craftlot_')));
    if (!state && documentValue !== playerDocument) {
      states = fairStates(playerDocument);
      state = recipeFairId ? states.find(value => String(value.id) === String(recipeFairId)) : null;
      state ||= states.find(value => (value.fair_slots || []).some(slot => String(slot?.shop_lot_id || '').startsWith('mf_craftlot_')));
    }
    if (state && String(state.id) !== recipeFairId) {
      recipeFairId = String(state.id); save({recipeFairId});
    }
    return state;
  }

  function plansFromRecipeState(state) {
    const sequence = [];
    for (const [index, slot] of (state?.fair_slots || []).entries()) {
      const plan = businessPlanFromLot(slot?.shop_lot_id, index);
      if (plan) sequence.push(plan);
    }
    if (!sequence.length) return [];
    const primary = sequence[0];
    const components = sequence.slice(1).map((row, index) => ({...row, component_order:index + 1}));
    const signature = [primary.item_id, ...components.map(row => row.item_id)].join('|');
    let hash = 2166136261;
    for (let index = 0; index < signature.length; index++) {
      hash ^= signature.charCodeAt(index); hash = Math.imul(hash, 16777619);
    }
    return [{...primary, plan_id:`recipe_${(hash >>> 0).toString(16).padStart(8,'0')}`, components, slot_order:0}];
  }

  async function submitRecipePlans(plans) {
    if (!plans.length) return {added:0,total:communityRecipes.length};
    const result = await recipeServerJson('/submit', {plans});
    log(result.added
      ? either(`В общую базу добавлено новых планов: ${result.added}`, `New plans added to the shared database: ${result.added}`)
      : either('Все выпавшие планы уже есть в базе — дубли не засчитаны', 'All observed plans already exist — duplicates ignored'), result.added ? 'ok' : 'warn');
    return result;
  }

  async function loadRecipes() {
    if (!requireLicense()) return;
    try {
      log(either('Считываю каталог бизнес-планов…', 'Reading the business-plan catalog…'));
      playerDocument = await apiJson('/player/me', 'POST');
      fairDocument = playerDocument;
      await ensureRecipeMetadata();
      const state = recipeState();
      if (!state) throw new Error(either('Откройте в игре «Проектное бюро» → «Каталог» и повторите считывание.', 'Open Project Bureau → Catalog in the game and read again.'));
      currentRecipePlans = plansFromRecipeState(state);
      try { await submitRecipePlans(currentRecipePlans); } catch (error) { log(`${either('Общая база недоступна', 'Shared database unavailable')}: ${error.message}`, 'warn'); }
      renderRecipes();
      log(either(`Каталог считан: планов ${currentRecipePlans.length}`, `Catalog loaded: ${currentRecipePlans.length} plans`), 'ok');
    } catch (error) { log(`${either('Ошибка рецептов', 'Recipe error')}: ${error.message}`, 'bad'); }
  }

  function renderRecipes() {
    if (!recipeCards || !recipeSummary) return;
    const state = recipeState();
    if (!state) {
      recipeCards.innerHTML = `<p class="hk-muted">${tr('recipeReadFirst')}</p>`;
      recipeSummary.textContent = tr('uniqueRecipes',{n:0});
      const run = root?.querySelector('#hk-recipe-run'); if (run) run.disabled = true;
      return;
    }
    currentRecipePlans = plansFromRecipeState(state);
    recipeCards.innerHTML = currentRecipePlans.map(recipePlanHtml).join('') ||
      `<p class="hk-muted">${either('Сейчас все ячейки каталога пусты', 'All catalog slots are currently empty')}</p>`;
    installIconFallbacks(recipeCards);
    bindRecipeDetails(recipeCards, currentRecipePlans);
    const attempts = Math.max(1, Math.trunc(Number(root?.querySelector('#hk-recipe-attempts')?.value || 1)));
    recipeSummary.innerHTML = `<b>${tr('currentRecipePlans')}: ${currentRecipePlans.length}</b><br><small>${tr('recipeCost')}: ${costVisual(state.fair_reroll_cost)} · ${tr('maxCost')}: ${scaledCostVisual(state.fair_reroll_cost,attempts)}</small>`;
    const run = root?.querySelector('#hk-recipe-run'); if (run) run.disabled = recipeRunning;
    const stop = root?.querySelector('#hk-recipe-stop'); if (stop) stop.disabled = !recipeRunning;
  }

  async function runRecipes() {
    if (!requireLicense() || recipeRunning || !recipeState()) return;
    const attempts = Math.max(1, Math.min(100, Math.trunc(Number(root.querySelector('#hk-recipe-attempts').value || 1))));
    let state;
    try {
      playerDocument = await apiJson('/player/me', 'POST');
      fairDocument = playerDocument;
      state = recipeState();
    } catch (error) {
      log(either('Не удалось обновить каталог перед прокруткой','Could not refresh the catalog before rerolling') + ': ' + (error?.message || error),'bad');
      return;
    }
    if (!state) { log(either('Каталог бизнес-планов недоступен','Business-plan catalog is unavailable'),'warn'); return; }
    if (!safeReroll(state.fair_reroll_cost, false)) { alert(either('Прокрутка заблокирована: неизвестная или платная валюта.', 'Reroll blocked: unknown or premium currency.')); return; }
    if (!confirm(either(`Прокрутить каталог бизнес-планов ${attempts} раз?\n\n${tr('maxCost')}: ${clean(root.querySelector('#hk-recipe-summary').textContent)}`,
      `Reroll the business-plan catalog ${attempts} times?\n\n${tr('maxCost')}: ${clean(root.querySelector('#hk-recipe-summary').textContent)}`))) return;
    if (hkRunner.running) { alert(either('Сначала завершите текущую задачу','Finish the current task first')); return; }
    hkRunner.start({title:either('Рецепты','Recipes'),total:attempts,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});
    recipeRunning = true; recipeStop = false; renderRecipes();
    let completed = 0;
    try {
      try { await submitRecipePlans(plansFromRecipeState(state)); } catch (_) {}
      for (let index = 0; index < attempts && !recipeStop; index++) {
        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');
        await hkRunner.waitIfPaused();
        hkRunner.setStep(either('Прокрутка каталога','Catalog reroll'), completed, attempts);
        log(either(`Прокрутка каталога ${index + 1}/${attempts}…`, `Catalog reroll ${index + 1}/${attempts}…`));
        state = recipeState(fairDocument || playerDocument);
        if (!state) throw new Error(either('Каталог бизнес-планов больше недоступен','Business-plan catalog is no longer available'));
        if (!safeReroll(state.fair_reroll_cost, false)) throw new Error(either('Цена прокрутки изменилась и стала небезопасной','Reroll cost changed and became unsafe'));
        const recipeDecision = budgetDecision(state.fair_reroll_cost, 'recipes', 1, playerDocument);
        if (!recipeDecision.allowed) throw new Error(recipeDecision.problems.join('; '));
        const recipeCost = state.fair_reroll_cost;
        const recipeBefore = new Map(costParts(recipeCost).map(part => [part.id, walletAmount(part.id, playerDocument)]));
        fairDocument = await apiJson('/fair/reroll', 'POST', {fair_id:recipeFairId});
        updateWalletFromResponse(fairDocument, recipeCost);
        for (const part of costParts(recipeCost)) appendExpense({section:'recipes', lotId:`recipe-reroll:${recipeFairId}`, name:either('Прокрутка каталога рецептов','Recipe catalog reroll'), currencyId:part.id, amount:part.quantity, balanceBefore:recipeBefore.get(part.id), balanceAfter:walletAmount(part.id, playerDocument), status:'ok', result:'rerolled'});
        state = recipeState(fairDocument);
        if (!state) throw new Error(either('Сервер не вернул каталог бизнес-планов', 'The server did not return the business-plan catalog'));
        currentRecipePlans = plansFromRecipeState(state);
        completed++;
        try { await submitRecipePlans(currentRecipePlans); }
        catch (error) { log(`${either('Общая база недоступна', 'Shared database unavailable')}: ${error.message}`, 'warn'); }
        renderRecipes();
        await gameRetryDelay(550);
      }
      log(either(`Прокрутка завершена: ${completed}`, `Rerolls completed: ${completed}`), 'ok');
      await hkAuthoritativePlayerRead('recipes-complete');
      hkRunner.finish(either('Прокрутка завершена','Rerolls completed'));
    } catch (error) {
      if (error?.name === 'AbortError') { hkRunner.reset(); log(either('Прокрутка остановлена','Reroll stopped'),'warn'); }
      else { hkRunner.fail(error); log(either('Прокрутка остановлена','Reroll stopped') + ': ' + (error?.message || error), 'bad'); }
    }
    finally { recipeRunning = false; recipeStop = false; renderRecipes(); }
  }

  async function loadCommunityRecipes() {
    if (!requireLicense()) return;
    try {
      await ensureRecipeMetadata();
      const result = await recipeServerJson('/list');
      communityRecipes = Array.isArray(result.recipes) ? result.recipes : [];
      renderCommunityRecipes();
      log(tr('uniqueRecipes',{n:communityRecipes.length}), 'ok');
    } catch (error) { log(`${either('Ошибка общей базы', 'Shared database error')}: ${error.message}`, 'bad'); }
  }

  function renderCommunityRecipes() {
    if (!recipeDatabaseBox) return;
    const groups = groupCommunityRecipes(communityRecipes);
    const counter = root?.querySelector('#hk-recipe-db-count'); if (counter) counter.textContent = tr('uniqueRecipeResults',{results:groups.length,plans:communityRecipes.length});
    recipeDatabaseBox.innerHTML = groups.length ? groups.map(communityRecipeGroupHtml).join('') : `<p class="hk-muted">${tr('recipeDatabaseEmpty')}</p>`;
    installIconFallbacks(recipeDatabaseBox);
    bindRecipeDetails(recipeDatabaseBox, communityRecipes);
  }

  function groupCommunityRecipes(rows) {
    const groups = new Map();
    for (const row of rows) {
      const key=String(row?.item_id || ''); if (!key) continue;
      if (!groups.has(key)) groups.set(key,{result:row,recipes:[]});
      const group=groups.get(key);
      if (!group.recipes.some(value=>String(value.plan_id)===String(row.plan_id))) group.recipes.push(row);
      if ((!group.result?.bonuses?.length && row?.bonuses?.length) || (!group.result?.icon && row?.icon)) group.result=row;
    }
    return [...groups.values()];
  }

  function recipeComponentStepHtml(item, index) {
    item = currentRecipeDisplay(item);
    const itemImage=item.icon ? `<img class="hk-icon" src="${escapeHtml(item.icon)}" alt="">` : iconHtml(item.item_id);
    return `<button type="button" class="hk-recipe-step" data-recipe-item="${escapeHtml(item.item_id)}" style="--rank:${escapeHtml(item.color || recipeQuality(item.quality).color)}">
      <b class="hk-component-order">${index + 1}</b><span class="hk-recipe-result">${itemImage}<b class="hk-rank-badge">${escapeHtml(recipeRank(item.rarity))}</b><small>T${escapeHtml(item.tier || '?')}</small></span></button>`;
  }

  function communityRecipeGroupHtml(group) {
    const row=currentRecipeDisplay(group.result); const bonuses=Array.isArray(row.bonuses) ? row.bonuses : [];
    const image=row.icon ? `<img class="hk-icon" src="${escapeHtml(row.icon)}" alt="">` : iconHtml(row.item_id);
    const bonusHtml=bonuses.length ? bonuses.map(value=>`<span>${value.icon ? fairIconHtml(value.icon,'hk-bonus-icon') : ''}<b>${escapeHtml(value.value)}</b> ${escapeHtml(value.caption)}</span>`).join('') : '—';
    const ways=group.recipes.map((recipe,wayIndex)=>{
      const components=Array.isArray(recipe.components) ? recipe.components : [];
      const flow=components.length ? components.map((item,index)=>recipeComponentStepHtml(item,index)).join('<b class="hk-recipe-plus">+</b>') : `<span class="hk-muted">${either('Компоненты ещё не определены','Components have not been identified yet')}</span>`;
      return `<div class="hk-recipe-way"><b class="hk-recipe-way-number">${wayIndex + 1}</b><div class="hk-recipe-way-flow">${flow}</div></div>`;
    }).join('');
    return `<details class="hk-recipe-group hk-recipe-result-group" style="--recipe-rank:${escapeHtml(row.color || recipeQuality(row.quality).color)}"><summary class="hk-recipe-row">
      <span class="hk-recipe-result" data-recipe-item="${escapeHtml(row.item_id)}">${image}<b class="hk-rank-badge">${escapeHtml(recipeRank(row.rarity))}</b><small>T${escapeHtml(row.tier || '?')}</small></span>
      <span class="hk-recipe-bonuses">${bonusHtml}</span><span class="hk-recipe-toggle"><b>${tr('recipeWays',{n:group.recipes.length})}</b><small>${either('Нажмите, чтобы раскрыть','Tap to expand')}</small></span></summary>
      <div class="hk-recipe-ways">${ways}</div></details>`;
  }

  function recipePlanHtml(row) {
    row = currentRecipeDisplay(row);
    const bonuses = Array.isArray(row.bonuses) ? row.bonuses : [];
    const components = Array.isArray(row.components) ? row.components.map(currentRecipeDisplay) : [];
    const image = row.icon ? `<img class="hk-icon" src="${escapeHtml(row.icon)}" alt="">` : iconHtml(row.item_id);
    const bonusHtml = bonuses.length ? bonuses.map(value => `<span>${value.icon ? fairIconHtml(value.icon,'hk-bonus-icon') : ''}<b>${escapeHtml(value.value)}</b> ${escapeHtml(value.caption)}</span>`).join('') : `<small>${either('Свойства будут считаны при следующем обновлении игры', 'Properties will be read after the next game refresh')}</small>`;
    const componentHtml = components.length ? components.map((item, index) => {
      const itemBonuses = Array.isArray(item.bonuses) ? item.bonuses : [];
      const itemImage = item.icon ? `<img class="hk-icon" src="${escapeHtml(item.icon)}" alt="">` : iconHtml(item.item_id);
      return `<button type="button" class="hk-recipe-component" data-recipe-item="${escapeHtml(item.item_id)}" style="--recipe-rank:${escapeHtml(item.color || recipeQuality(item.quality).color)}"><b class="hk-component-order">${index + 1}</b>
        <span class="hk-recipe-result">${itemImage}<b class="hk-rank-badge">${escapeHtml(recipeRank(item.rarity))}</b><small>T${escapeHtml(item.tier || '?')}</small></span>
        <span class="hk-recipe-bonuses">${itemBonuses.map(value => `<span>${value.icon ? fairIconHtml(value.icon,'hk-bonus-icon') : ''}<b>${escapeHtml(value.value)}</b> ${escapeHtml(value.caption)}</span>`).join('') || '—'}</span></button>`;
    }).join('') : `<p class="hk-muted">${either('У этого плана компоненты не считаны', 'Components have not been read for this plan')}</p>`;
    return `<details class="hk-recipe-group" style="--recipe-rank:${escapeHtml(row.color || recipeQuality(row.quality).color)}"><summary class="hk-recipe-row">
      <span class="hk-recipe-result" data-recipe-item="${escapeHtml(row.item_id)}">${image}<b class="hk-rank-badge">${escapeHtml(recipeRank(row.rarity))}</b><small>T${escapeHtml(row.tier || '?')}</small></span>
      <span class="hk-recipe-bonuses">${bonusHtml}</span><span class="hk-recipe-toggle"><b>${either('Компоненты', 'Components')}: ${components.length}</b><small>${either('Нажмите, чтобы раскрыть', 'Tap to expand')}</small></span></summary>
      <div class="hk-recipe-component-list">${componentHtml}</div></details>`;
  }

  function bindRecipeDetails(scope, rows) {
    scope.querySelectorAll('[data-recipe-item]').forEach(button => button.addEventListener('click', event => {
      event.stopPropagation();
      const flat = rows.flatMap(value => [value, ...(Array.isArray(value.components) ? value.components : [])]);
      const row = flat.find(value => String(value.item_id) === button.dataset.recipeItem);
      if (row) showRecipeDetails(row);
    }));
  }

  function showRecipeDetails(row) {
    row = currentRecipeDisplay(row);
    root.querySelector('#hk-recipe-detail')?.remove();
    const bonuses = Array.isArray(row.bonuses) ? row.bonuses : [];
    const modal = document.createElement('div'); modal.id = 'hk-recipe-detail'; modal.className = 'hk-detail-backdrop';
    modal.innerHTML = `<div class="hk-detail-card" style="--recipe-rank:${escapeHtml(row.color || recipeQuality(row.quality).color)}"><button class="hk-detail-close">×</button>
      <div class="hk-detail-title">${row.icon ? `<img class="hk-icon" src="${escapeHtml(row.icon)}" alt="">` : iconHtml(row.item_id)}<span><b>${escapeHtml(row.name || row.item_id)}</b><small>${escapeHtml(recipeRank(row.rarity))} · T${escapeHtml(row.tier || '?')}</small></span></div>
      ${row.description ? `<p>${escapeHtml(row.description)}</p>` : ''}<h4>${either('Свойства', 'Properties')}</h4><div class="hk-detail-bonuses">${bonuses.length ? bonuses.map(value => `<span>${value.icon ? fairIconHtml(value.icon,'hk-bonus-icon') : ''}<b>${escapeHtml(value.value)}</b> ${escapeHtml(value.caption)}</span>`).join('') : '—'}</div></div>`;
    root.appendChild(modal); installIconFallbacks(modal);
    modal.addEventListener('click', event => { if (event.target === modal || event.target.closest('.hk-detail-close')) modal.remove(); });
  }

  function bureauCost(size = bureauSize) {
    return bureauCosts.find(row => row.itemsCount === Number(size))?.cost || {};
  }

  async function loadProjectBureau() {
    if (!requireLicense()) return;
    try {
      log(either('Считываю бизнесы Проектного бюро…', 'Reading Project Bureau businesses…'));
      await ensureRecipeMetadata();
      if (!playerDocument) playerDocument = await apiJson('/player/me', 'POST');
      bureauInventory = normalizeInventory(playerDocument);
      if (!bureauInventory.length) {
        try { playerDocument = await apiJson('/player/me', 'POST'); bureauInventory = normalizeInventory(playerDocument); }
        catch (_) {}
      }
      try {
        const values = await apiJson('/business/values', 'GET');
        bureauCosts = (values?.recipe_costs || []).map(row => ({itemsCount:Math.max(0, Number(row?.business_count || 0)), cost:row?.cost || {}}))
          .filter(row => [2,3].includes(row.itemsCount)).sort((a,b) => a.itemsCount - b.itemsCount);
      } catch (_) {
        bureauCosts = [];
        log(either('Стоимость не считана, но выбор бизнесов доступен', 'Costs unavailable, but business selection is ready'), 'warn');
      }
      if (!bureauInventory.length) throw new Error(either('На складе не найдены доступные бизнесы', 'No available businesses were found in stock'));
      if (!bureauCosts.some(row => row.itemsCount === bureauSize)) bureauSize = bureauCosts[0]?.itemsCount || 2;
      selectedBureauInputs.clear();
      renderProjectBureau();
      log(either(`Проектное бюро: доступно видов бизнеса ${bureauInventory.length}`, `Project Bureau: ${bureauInventory.length} business types available`), 'ok');
    } catch (error) { log(`${either('Ошибка Проектного бюро', 'Project Bureau error')}: ${error.message}`, 'bad'); }
  }

  function renderProjectBureau() {
    if (!bureauCards || !bureauSummary) return;
    const tierSelect = root?.querySelector('#hk-bureau-tier');
    if (tierSelect) {
      tierSelect.innerHTML = `<option value="0">${tr('bureauAllTiers')}</option>` +
        Array.from({length:6}, (_,index) => `<option value="${index + 1}">T${index + 1}</option>`).join('');
      tierSelect.value = String(bureauTier);
    }
    const sizes = root?.querySelector('#hk-bureau-sizes');
    if (sizes) {
      sizes.innerHTML = (bureauCosts.length ? bureauCosts : [{itemsCount:2,cost:{}},{itemsCount:3,cost:{}}]).map(row =>
        `<button class="${row.itemsCount === bureauSize ? 'active' : ''}" data-bureau-size="${row.itemsCount}"><b>${row.itemsCount}</b><span>${scaledCostVisual(row.cost,1)}</span></button>`).join('');
      sizes.querySelectorAll('[data-bureau-size]').forEach(button => button.onclick = () => {
        bureauSize = Number(button.dataset.bureauSize || 2); selectedBureauInputs.clear(); renderProjectBureau();
      });
    }
    if (!bureauInventory.length) {
      bureauCards.innerHTML = `<p class="hk-muted">${tr('readBureau')}</p>`;
      bureauSummary.textContent = tr('bureauSelected',{n:0,max:bureauSize});
      const run = root?.querySelector('#hk-bureau-run'); if (run) run.disabled = true;
      return;
    }
    const visibleInventory = bureauInventory.filter(row => !bureauTier || tier(row.businessId) === bureauTier);
    bureauCards.innerHTML = visibleInventory.map(row => {
      const count = Math.min(row.quantity, Math.max(0, Number(selectedBureauInputs.get(row.businessId) || 0)));
      const details = businessCardDetails(row.businessId);
      return `<div class="hk-bureau-item ${count ? 'selected' : ''}">${iconHtml(row.businessId)}<span><b>${escapeHtml(details.name)}</b><small>T${tier(row.businessId) || '?'} · ${tr('inStock',{n:row.quantity})}</small><small class="hk-bureau-properties">${escapeHtml(details.properties)}</small></span>
        <input type="number" inputmode="numeric" min="0" max="${Math.min(row.quantity,bureauSize)}" value="${count}" data-bureau-input="${escapeHtml(row.businessId)}"></div>`;
    }).join('') || `<p class="hk-muted">${tr('noBusinesses',{n:bureauTier || '?'})}</p>`;
    installIconFallbacks(bureauCards);
    bureauCards.querySelectorAll('[data-bureau-input]').forEach(input => input.onchange = () => {
      const id = input.dataset.bureauInput;
      const stock = bureauInventory.find(row => row.businessId === id)?.quantity || 0;
      const without = [...selectedBureauInputs].reduce((sum,[key,value]) => sum + (key === id ? 0 : Number(value || 0)), 0);
      const count = Math.min(stock, Math.max(0, bureauSize - without), Math.max(0, Math.trunc(Number(input.value || 0))));
      count ? selectedBureauInputs.set(id,count) : selectedBureauInputs.delete(id);
      renderProjectBureau();
    });
    const selectedCount = [...selectedBureauInputs.values()].reduce((sum,value) => sum + Number(value || 0), 0);
    const attempts = Math.max(1, Math.trunc(Number(root?.querySelector('#hk-bureau-attempts')?.value || 1)));
    bureauSummary.innerHTML = `<b>${tr('bureauSelected',{n:selectedCount,max:bureauSize})}</b><br><small>${tr('maxCost')}: ${scaledCostVisual(bureauCost(),attempts)}</small>`;
    const run = root?.querySelector('#hk-bureau-run'); if (run) run.disabled = bureauRunning || selectedCount !== bureauSize || !costParts(bureauCost()).length;
  }

  async function runProjectBureau() {
    if (!requireLicense() || bureauRunning) return;
    const inputs = [...selectedBureauInputs].flatMap(([id,count]) => Array(Math.max(0,Number(count || 0))).fill(id));
    if (inputs.length !== bureauSize) return;
    const attempts = Math.max(1, Math.min(100, Math.trunc(Number(root.querySelector('#hk-bureau-attempts').value || 1))));
    try {
      playerDocument = await apiJson('/player/me', 'POST');
      bureauInventory = normalizeInventory(playerDocument);
      const values = await apiJson('/business/values', 'GET');
      bureauCosts = (values?.recipe_costs || []).map(row => ({itemsCount:Math.max(0, Number(row?.business_count || 0)), cost:row?.cost || {}}))
        .filter(row => [2,3].includes(row.itemsCount)).sort((a,b) => a.itemsCount - b.itemsCount);
    } catch (error) {
      log(either('Не удалось обновить Проектное бюро перед созданием','Could not refresh Project Bureau before crafting') + ': ' + (error?.message || error),'bad');
      renderProjectBureau();
      return;
    }
    const liveBureauCost = bureauCost();
    if (!costParts(liveBureauCost).length) {
      alert(either('Стоимость создания не определена. Создание заблокировано.','Craft cost is unknown. Crafting is blocked.'));
      renderProjectBureau();
      return;
    }
    const projectedBureau = budgetDecision(liveBureauCost, 'bureau', attempts, playerDocument);
    if (!projectedBureau.allowed) {
      alert(projectedBureau.problems.join('\n'));
      renderProjectBureau();
      return;
    }
    const available = new Map(bureauInventory.map(row => [row.businessId,row.quantity]));
    if ([...selectedBureauInputs].some(([id,count]) => Number(count) * attempts > (available.get(id) || 0))) {
      alert(either('На складе недостаточно выбранных бизнесов для такого количества созданий.', 'Not enough selected businesses in stock for this creation count.')); return;
    }
    if (!confirm(either(`Создать бизнес-планы: ${attempts}?\n\n${tr('maxCost')}: ${scaledCostVisual(liveBureauCost,attempts).replace(/<[^>]+>/g,' ')}`,
      `Create business plans: ${attempts}?\n\n${tr('maxCost')}: ${scaledCostVisual(liveBureauCost,attempts).replace(/<[^>]+>/g,' ')}`))) return;
    if (hkRunner.running) { alert(either('Сначала завершите текущую задачу','Finish the current task first')); return; }
    hkRunner.start({title:either('Проектное бюро','Project Bureau'),total:attempts,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});
    bureauRunning = true; renderProjectBureau();
    let completed = 0;
    try {
      for (let index = 0; index < attempts; index++) {
        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');
        await hkRunner.waitIfPaused();
        hkRunner.setStep(either('Создание бизнес-плана','Creating business plan'), completed, attempts);
        log(either(`Создаю бизнес-план ${index + 1}/${attempts}…`, `Creating business plan ${index + 1}/${attempts}…`));
        const bureauDecision = budgetDecision(liveBureauCost, 'bureau', 1, playerDocument);
        if (!bureauDecision.allowed) throw new Error(bureauDecision.problems.join('; '));
        const bureauBefore = new Map(costParts(liveBureauCost).map(part => [part.id, walletAmount(part.id, playerDocument)]));
        playerDocument = await apiJson('/player/business/recipe/craft', 'POST', {businesses:inputs}, true, 0);
        for (const part of costParts(liveBureauCost)) appendExpense({section:'bureau', lotId:'project-bureau', name:either('Проектное бюро','Project Bureau'), currencyId:part.id, amount:part.quantity, balanceBefore:bureauBefore.get(part.id), balanceAfter:walletAmount(part.id, playerDocument), status:'ok', result:'crafted'});
        completed++;
        await gameRetryDelay(450);
      }
      playerDocument = await apiJson('/player/me', 'POST');
      bureauInventory = normalizeInventory(playerDocument);
      selectedBureauInputs.clear();
      log(either(`Создано бизнес-планов: ${completed}`, `Business plans created: ${completed}`), 'ok');
      playerDocument = await hkAuthoritativePlayerRead('bureau-complete');
      bureauInventory = normalizeInventory(playerDocument);
      hkRunner.finish(either('Проектное бюро завершено','Project Bureau completed'));
    } catch (error) {
      if (error?.name === 'AbortError') { hkRunner.reset(); log(either('Проектное бюро остановлено','Project Bureau stopped'),'warn'); }
      else { hkRunner.fail(error); log(either('Проектное бюро остановлено','Project Bureau stopped') + ': ' + (error?.message || error), 'bad'); }
    }
    finally { bureauRunning = false; renderProjectBureau(); }
  }

  function refreshBusinessData() {
    if (!playerDocument) return;
    layout = normalizeLayout(playerDocument)
      .filter(row => row.timer == null || Number(row.timer) === 0)
      .filter(row => row.businessId ? row.status === 'ACTIVE' : ['INACTIVE', '', null].includes(row.status));
    inventory = normalizeInventory(playerDocument);
    selectedSlots = new Set([...selectedSlots].filter(key => layout.some(row => row.key === key)));
    // Empty active slots are destinations, not businesses to remove. They must
    // always increase insertion capacity even when a tier filter hides them.
    if (!preparedBusinessPlan) for (const row of layout) if (!row.businessId) selectedSlots.add(row.key);
    for (const [id, count] of [...selectedStock]) {
      const stock = inventory.find(row => row.businessId === id);
      if (!stock) selectedStock.delete(id); else selectedStock.set(id, Math.min(count, stock.quantity));
    }
    renderBusinessLists();
    renderBusinessOptimizerFilters();
  }

  function businessSelectionCount() {
    return [...selectedStock.values()].reduce((sum, value) => sum + Number(value || 0), 0);
  }

  function clampSelectedStockToSlots() {
    let freeSlots = selectedSlots.size;
    for (const [businessId, count] of [...selectedStock]) {
      const inStock = Math.max(0, Number(inventory.find(row => row.businessId === businessId)?.quantity || 0));
      const allowed = Math.min(inStock, freeSlots, Math.max(0, Number(count || 0)));
      if (allowed) selectedStock.set(businessId, allowed); else selectedStock.delete(businessId);
      freeSlots -= allowed;
    }
  }

  function availableSlotsForBusiness(businessId) {
    const ownCount = Math.max(0, Number(selectedStock.get(businessId) || 0));
    return Math.max(0, selectedSlots.size - Math.max(0, businessSelectionCount() - ownCount));
  }

  function businessCardDetails(businessId) {
    const meta = recipeMetadata(String(businessId || ''));
    const bonuses = Array.isArray(meta.bonuses) ? meta.bonuses : [];
    const properties = bonuses.map(value => `${clean(value.value)} ${clean(value.caption)}`.trim()).filter(Boolean).join(' · ');
    return {
      name:clean(meta.name) || gameText(businessId),
      properties:properties || clean(meta.description) || either('Свойства загружаются…', 'Loading properties…')
    };
  }

  function businessBonusAmount(bonus) {
    const source = String(bonus?.value || '').replace(/\s/g, '').replace(',', '.');
    const match = source.match(/[+-]?\d+(?:\.\d+)?(?:[kкmм])?/i);
    if (!match) return 1;
    const suffix = match[0].slice(-1).toLowerCase();
    let value = Number(match[0].replace(/[kкmм]/i, ''));
    if (!Number.isFinite(value)) return 1;
    if (suffix === 'k' || suffix === 'к') value *= 1000;
    if (suffix === 'm' || suffix === 'м') value *= 1000000;
    return value;
  }

  function bonusPropertyKey(bonus) {
    const label = clean(bonus?.caption);
    const normalized = label.normalize('NFKC').toLocaleLowerCase(locale())
      .replace(/ё/g,'е')
      .replace(/^[\s/\\:;,.+\-–—]+|[\s/\\:;,.+\-–—]+$/g,'')
      .replace(/[\s\u00a0]+/g,' ')
      .trim();
    return normalized || String(bonus?.id || '').toLowerCase();
  }

  function businessEffects(businessId) {
    const meta = recipeMetadata(String(businessId || ''));
    const grouped = new Map();
    const seen = new Set();
    for (const bonus of (meta.bonuses || [])) {
      const id = String(bonus.id || bonus.caption || '');
      const label = clean(bonus.caption) || clean(bonus.id) || businessId;
      const amount = businessBonusAmount(bonus);
      const key = bonusPropertyKey(bonus) || id;
      // Some combined businesses repeat the exact same bonus reference in the
      // response. Count that reference once, but add genuinely different
      // bonuses which have the same visible property.
      const fingerprint = `${id}\u0000${amount}`;
      if (seen.has(fingerprint)) continue;
      seen.add(fingerprint);
      const row = grouped.get(key) || {key,id,label,amount:0,ids:[],search:''};
      row.amount += amount;
      row.ids.push(id);
      row.search += ` ${id} ${bonus.caption || ''}`.toLowerCase();
      grouped.set(key,row);
    }
    return [...grouped.values()];
  }

  function playerHasVip(documentValue = playerDocument) {
    const player = documentValue?.player || documentValue?.data?.player || documentValue || {};
    const applied = player?.vip_status_applied === true || player?.vipStatusApplied === true;
    const timer = player?.vip_status_end_timer ?? player?.vipStatusEndTimer;
    return applied && (timer == null || !Number.isFinite(Number(timer)) || Number(timer) > 0);
  }

  function vipPassiveIncomeMultiplier(documentValue = playerDocument) {
    if (!playerHasVip(documentValue)) return 1;
    const configured = Number(premiumDocument?.passive_income_multiplier || premiumDocument?.passiveIncomeMultiplier || 2);
    return Number.isFinite(configured) && configured > 1 ? configured : 2;
  }

  function isPassiveIncomeEffect(effect) {
    const text = `${effect?.search || ''} ${effect?.id || ''} ${effect?.label || ''}`.toLowerCase();
    return /perhour|per_hour|passive[_\s-]*income|пассивн\w*\s+доход|\/час/.test(text);
  }

  function businessEffectMultiplier(effect, documentValue = playerDocument) {
    return isPassiveIncomeEffect(effect) ? vipPassiveIncomeMultiplier(documentValue) : 1;
  }

  function businessActiveLimit(businessId) {
    const details = businessCardDetails(businessId);
    const text = `${details.properties} ${recipeMetadata(String(businessId || '')).description || ''}`;
    const match = text.match(/(?:лимит\s+активных|limit\s+(?:of\s+)?active)\D{0,8}(\d+)/i);
    return match ? Math.max(1, Number(match[1])) : Number.POSITIVE_INFINITY;
  }

  function optimizerEffectMatches(effect, goal, keyword = '') {
    const text = effect.search;
    if (goal === 'mixed') return true;
    if (goal === 'currency') return Boolean(keyword) && text.includes(keyword.toLowerCase());
    const patterns = {
      pit:['pit','яма','ямы','boss','босс','combat','battle','power','сила','damage'],
      income:['income','доход','perhour','per_hour','passive','пассив','profit','прибыл'],
      energy:['energy','энерг'], rumors:['rumor','слух'], buildings:['building','здан','slot','слот']
    };
    return (patterns[goal] || []).some(value => text.includes(value));
  }

  function optimizerBusinessScore(businessId, goal, keyword = '') {
    const effects = businessEffects(businessId);
    let score = 0;
    let matched = false;
    for (const effect of effects) {
      if (!optimizerEffectMatches(effect, goal, keyword)) continue;
      matched = true;
      const amount = effect.amount * businessEffectMultiplier(effect);
      const weight = Math.log10(1 + Math.abs(amount));
      score += amount < 0 ? -weight : weight;
    }
    // A business without a useful effect for the selected goal must not enter
    // the replacement pool merely because it has a higher tier. Returning zero
    // also keeps the before/after summary finite for unrelated active bonuses.
    if (!matched || score <= 0) return 0;
    // A deterministic, very small tie-breaker keeps stronger visible tiers
    // ahead without overriding the chosen effect.
    return score + Math.max(0, Number(recipeMetadata(businessId).tier || 0)) / 10000;
  }

  function businessHasPositiveGoalEffect(businessId, goal, keyword = '') {
    return businessEffects(businessId).some(effect =>
      optimizerEffectMatches(effect, goal, keyword) &&
      effect.amount * businessEffectMultiplier(effect) > 0
    );
  }

  function businessCounts(ids) {
    const result = new Map();
    for (const id of ids.filter(Boolean)) result.set(id, (result.get(id) || 0) + 1);
    return result;
  }

  function aggregateBusinessEffects(counts) {
    const result = new Map();
    for (const [id,count] of counts) for (const effect of businessEffects(id)) {
      const row = result.get(effect.key) || {label:effect.label, amount:0};
      row.amount += effect.amount * count * businessEffectMultiplier(effect); result.set(effect.key,row);
    }
    return result;
  }

  function optimizerSafety(changeCount) {
    const workers = businessWorkerState(playerDocument);
    const pending = normalizeLayout(playerDocument).filter(row => row.businessId &&
      (row.status !== 'ACTIVE' || Number(row.timer || 0) > 0));
    const canRelease = pending.some(row => Number(row.timer || 0) <= Math.max(0, Number(row.freeSpeedUpTime || 0)));
    const managersAvailable = !changeCount || !workers.max || workers.busy < workers.max || canRelease;
    return {workers, managersAvailable, allowed:managersAvailable,
      reason:managersAvailable ? tr('optimizerSafe') : either('Нет свободного менеджера с бесплатным ускорением','No free manager with a free speed-up')};
  }

  function businessOptimizerPreferences() {
    const stored = load().businessOptimizer || {};
    const legacyTiers = Array.isArray(stored.allowedTiers) ? stored.allowedTiers : [1,2,3,4,5,6];
    const normalizeTiers = values => values.map(Number).filter(value => value >= 1 && value <= 6);
    const removeTiers = normalizeTiers(Array.isArray(stored.removeTiers) ? stored.removeTiers : legacyTiers);
    const insertTiers = normalizeTiers(Array.isArray(stored.insertTiers) ? stored.insertTiers : legacyTiers);
    return {removeTiers:new Set(removeTiers), insertTiers:new Set(insertTiers),
      lockedBusinessIds:new Set(Array.isArray(stored.lockedBusinessIds) ? stored.lockedBusinessIds.map(String) : []),
      excludedInsertBusinessIds:new Set(Array.isArray(stored.excludedInsertBusinessIds) ? stored.excludedInsertBusinessIds.map(String) : [])};
  }

  function optimizerSectionOpen(sectionId) {
    const stored = load().businessOptimizer?.openSections;
    return !stored || stored[sectionId] !== false;
  }

  function saveOptimizerSectionState(sectionId, open) {
    const stored = load().businessOptimizer || {};
    save({businessOptimizer:{...stored, openSections:{...(stored.openSections || {}), [sectionId]:Boolean(open)}}});
  }

  function saveBusinessOptimizerPreferences(removeTiers, insertTiers, lockedBusinessIds, excludedInsertBusinessIds) {
    const stored = load().businessOptimizer || {};
    const excluded = excludedInsertBusinessIds ?? new Set(Array.isArray(stored.excludedInsertBusinessIds) ? stored.excludedInsertBusinessIds.map(String) : []);
    save({businessOptimizer:{...(load().businessOptimizer || {}),
      removeTiers:[...removeTiers].sort((a,b)=>a-b), insertTiers:[...insertTiers].sort((a,b)=>a-b),
      lockedBusinessIds:[...lockedBusinessIds].sort(), excludedInsertBusinessIds:[...excluded].sort()}});
  }

  function renderBusinessOptimizerFilters() {
    const removeTierBox = root?.querySelector('#hk-optimizer-remove-tiers');
    const insertTierBox = root?.querySelector('#hk-optimizer-insert-tiers');
    const replaceBox = root?.querySelector('#hk-optimizer-replaceable');
    const stockBox = root?.querySelector('#hk-optimizer-stock-allowed');
    if (!removeTierBox || !insertTierBox || !replaceBox || !stockBox) return;
    const preferences = businessOptimizerPreferences();
    const tierChoices = (kind, selected) => [1,2,3,4,5,6].map(value => `<label class="hk-tier-choice"><input type="checkbox" data-optimizer-${kind}-tier="${value}" ${selected.has(value)?'checked':''}><b>T${value}</b></label>`).join('');
    removeTierBox.innerHTML = tierChoices('remove',preferences.removeTiers);
    insertTierBox.innerHTML = tierChoices('insert',preferences.insertTiers);
    const installed = [...businessCounts(layout.map(row => row.businessId))].map(([businessId,count]) => ({businessId,count,tier:tier(businessId) || 0,details:businessCardDetails(businessId)}))
      .sort((a,b) => a.tier-b.tier || a.details.name.localeCompare(b.details.name,locale()));
    replaceBox.innerHTML = installed.length ? installed.map(row => {
      const tierAllowed = preferences.removeTiers.has(row.tier);
      const replaceable = tierAllowed && !preferences.lockedBusinessIds.has(row.businessId);
      return `<label class="hk-optimizer-business-choice ${replaceable?'':'locked'} ${tierAllowed?'':'tier-disabled'}"><input type="checkbox" data-optimizer-business="${escapeHtml(row.businessId)}" ${replaceable?'checked':''} ${tierAllowed?'':'disabled'}>${iconHtml(row.businessId)}<span><b>${escapeHtml(row.details.name)}</b><small>T${row.tier || '—'} · ×${row.count}</small></span></label>`;
    }).join('') : `<p class="hk-muted">${tr('optimizerNoPlan')}</p>`;
    const stock = inventory.map(row => ({...row,tier:tier(row.businessId) || 0,details:businessCardDetails(row.businessId)}))
      .sort((a,b) => a.tier-b.tier || a.details.name.localeCompare(b.details.name,locale()));
    stockBox.innerHTML = stock.length ? stock.map(row => {
      const allowed = !preferences.excludedInsertBusinessIds.has(row.businessId);
      return `<label class="hk-optimizer-business-choice ${allowed?'':'locked'}"><input type="checkbox" data-optimizer-stock-business="${escapeHtml(row.businessId)}" ${allowed?'checked':''}>${iconHtml(row.businessId)}<span><b>${escapeHtml(row.details.name)}</b><small>T${row.tier || '—'} · ${tr('inStock',{n:row.quantity})}</small></span></label>`;
    }).join('') : `<p class="hk-muted">${tr('noBusinesses')}</p>`;
    installIconFallbacks(replaceBox); installIconFallbacks(stockBox);
    removeTierBox.querySelectorAll('[data-optimizer-remove-tier]').forEach(input => input.onchange = () => {
      const current = businessOptimizerPreferences();
      const value = Number(input.dataset.optimizerRemoveTier);
      const idsInTier = installed.filter(row => row.tier === value).map(row => row.businessId);
      if (input.checked) {
        current.removeTiers.add(value);
        // Selecting a removable tier immediately enables every installed
        // business of that tier. Individual eligible businesses can still be
        // protected afterwards.
        for (const id of idsInTier) current.lockedBusinessIds.delete(id);
      } else {
        current.removeTiers.delete(value);
        // Businesses outside the selected removable tiers are always
        // protected and their checkboxes are disabled.
        for (const id of idsInTier) current.lockedBusinessIds.add(id);
      }
      saveBusinessOptimizerPreferences(current.removeTiers,current.insertTiers,current.lockedBusinessIds); optimizerResult=null; renderBusinessOptimizerFilters(); renderBusinessOptimizer();
    });
    insertTierBox.querySelectorAll('[data-optimizer-insert-tier]').forEach(input => input.onchange = () => {
      const current = businessOptimizerPreferences();
      const value = Number(input.dataset.optimizerInsertTier);
      if (input.checked) current.insertTiers.add(value); else current.insertTiers.delete(value);
      saveBusinessOptimizerPreferences(current.removeTiers,current.insertTiers,current.lockedBusinessIds); optimizerResult=null; renderBusinessOptimizer();
    });
    replaceBox.querySelectorAll('[data-optimizer-business]').forEach(input => input.onchange = () => {
      if (input.disabled) return;
      const current = businessOptimizerPreferences();
      const id = String(input.dataset.optimizerBusiness || '');
      if (input.checked) current.lockedBusinessIds.delete(id); else current.lockedBusinessIds.add(id);
      saveBusinessOptimizerPreferences(current.removeTiers,current.insertTiers,current.lockedBusinessIds); optimizerResult=null; renderBusinessOptimizerFilters(); renderBusinessOptimizer();
    });
    stockBox.querySelectorAll('[data-optimizer-stock-business]').forEach(input => input.onchange = () => {
      const current = businessOptimizerPreferences();
      const id = String(input.dataset.optimizerStockBusiness || '');
      if (input.checked) current.excludedInsertBusinessIds.delete(id); else current.excludedInsertBusinessIds.add(id);
      saveBusinessOptimizerPreferences(current.removeTiers,current.insertTiers,current.lockedBusinessIds,current.excludedInsertBusinessIds);
      optimizerResult=null; renderBusinessOptimizerFilters(); renderBusinessOptimizer();
    });
  }

  function optimizerExactPairs(desiredIds, protectedSlotKeys = new Set()) {
    const wanted = businessCounts(desiredIds);
    const keep = new Map(wanted);
    let emptyToKeep = desiredIds.filter(id => !id).length;
    const outgoing = [];
    for (const row of layout) if (row.businessId && protectedSlotKeys.has(row.key)) {
      const left = Number(keep.get(row.businessId) || 0);
      if (left > 0) keep.set(row.businessId,left - 1);
    }
    for (const row of layout) {
      if (protectedSlotKeys.has(row.key)) continue;
      const left = row.businessId ? Number(keep.get(row.businessId) || 0) : 0;
      if (row.businessId && left > 0) keep.set(row.businessId,left - 1);
      else if (!row.businessId && emptyToKeep > 0) emptyToKeep--;
      else outgoing.push(row);
    }
    const incoming = [];
    for (const [id,count] of keep) for (let index=0; index<count; index++) incoming.push(id);
    outgoing.sort((a,b) => a.key.localeCompare(b.key));
    incoming.sort((a,b) => Number(tier(a) || 0) - Number(tier(b) || 0) || a.localeCompare(b));
    const result = incoming.map(id => {
      const wantedTier = tier(id);
      outgoing.sort((a,b) => Number(tier(a.businessId) !== wantedTier) - Number(tier(b.businessId) !== wantedTier) || a.key.localeCompare(b.key));
      return [outgoing.shift(),id];
    });
    while (outgoing.length) result.push([outgoing.shift(),'']);
    return result;
  }

  function calculateBusinessOptimizer() {
    if (!layout.length) { optimizerResult = null; renderBusinessOptimizer(); return; }
    const goal = root?.querySelector('#hk-optimizer-goal')?.value || 'pit';
    const keyword = '';
    const preferences = businessOptimizerPreferences();
    if (!preferences.removeTiers.size || !preferences.insertTiers.size) {
      alert(either('Выберите хотя бы один тир для снятия и один тир для вставки.', 'Select at least one tier to remove and one tier to insert.')); return;
    }
    // Passive income is a family of independent hourly resources. Replacing a
    // business that already produces one of them with another income business
    // can raise the combined score while silently reducing restoration tokens,
    // boss invitations or influence funds. For the income goal, preserve every
    // installed positive income producer and improve only the remaining slots.
    const protectedByGoal = row => goal === 'income' && row.businessId && businessHasPositiveGoalEffect(row.businessId,goal,keyword);
    const canRemove = row => !row.businessId || (!protectedByGoal(row) && preferences.removeTiers.has(Number(tier(row.businessId) || 0)) && !preferences.lockedBusinessIds.has(row.businessId));
    const fixedRows = layout.filter(row => !canRemove(row));
    const replaceableRows = layout.filter(canRemove);
    const activeCounts = businessCounts(layout.map(row => row.businessId));
    const available = businessCounts(replaceableRows.map(row => row.businessId));
    for (const row of inventory) available.set(row.businessId,(available.get(row.businessId) || 0) + Math.max(0,Number(row.quantity || 0)));
    const types = [...available].filter(([id]) => preferences.insertTiers.has(Number(tier(id) || 0)) &&
      !preferences.excludedInsertBusinessIds.has(id)).map(([id,count]) => ({id,count,score:optimizerBusinessScore(id,goal,keyword),limit:businessActiveLimit(id),
      active:Number(activeCounts.get(id) || 0)})).filter(row => Number.isFinite(row.score) && row.score > 0)
      .sort((a,b) => b.score-a.score || Number(b.active>0)-Number(a.active>0) || a.id.localeCompare(b.id));
    const optimized = [];
    for (const row of types) {
      const fixedCopies = fixedRows.filter(value => value.businessId === row.id).length;
      const allowedByLimit = Number.isFinite(row.limit) ? Math.max(0,row.limit-fixedCopies) : replaceableRows.length;
      const allowed = Math.min(row.count, allowedByLimit, replaceableRows.length-optimized.length);
      for (let index=0; index<allowed; index++) optimized.push(row.id);
      if (optimized.length >= replaceableRows.length) break;
    }
    // Never remove an installed business merely because the selected tiers do
    // not provide enough replacement candidates. Preserve the remaining
    // replaceable positions instead of turning them into empty slots.
    if (optimized.length < replaceableRows.length) {
      const alreadyUsed = businessCounts(optimized);
      for (const row of replaceableRows.filter(value => value.businessId)) {
        const availableCopies = Number(available.get(row.businessId) || 0);
        const used = Number(alreadyUsed.get(row.businessId) || 0);
        if (used >= availableCopies || optimized.length >= replaceableRows.length) continue;
        optimized.push(row.businessId); alreadyUsed.set(row.businessId,used+1);
      }
    }
    while (optimized.length < replaceableRows.length) optimized.push('');
    const desired = [...fixedRows.map(row => row.businessId), ...optimized];
    const pairs = optimizerExactPairs(desired,new Set(fixedRows.map(row => row.key)));
    const beforeCounts = activeCounts, afterCounts = businessCounts(desired);
    const beforeEffects = aggregateBusinessEffects(beforeCounts), afterEffects = aggregateBusinessEffects(afterCounts);
    const changes = [...new Set([...beforeEffects.keys(),...afterEffects.keys()])].map(id => {
      const before = Number(beforeEffects.get(id)?.amount || 0), after = Number(afterEffects.get(id)?.amount || 0);
      return {id,label:afterEffects.get(id)?.label || beforeEffects.get(id)?.label || id,before,after,diff:after-before};
    }).filter(row => row.diff !== 0).sort((a,b) => Math.abs(b.diff)-Math.abs(a.diff));
    optimizerResult = {goal,keyword,desired,pairs,changes,safety:optimizerSafety(pairs.length),
      beforeScore:[...beforeCounts].reduce((sum,[id,count]) => sum+optimizerBusinessScore(id,goal,keyword)*count,0),
      afterScore:[...afterCounts].reduce((sum,[id,count]) => sum+optimizerBusinessScore(id,goal,keyword)*count,0)};
    renderBusinessOptimizer();
  }

  function renderBusinessOptimizer() {
    const box = root?.querySelector('#hk-optimizer-result'); if (!box) return;
    if (!optimizerResult) { box.innerHTML = `<p class="hk-muted">${tr('optimizerNoPlan')}</p>`; return; }
    const row = optimizerResult, workers = row.safety.workers;
    const changes = row.changes.slice(0,10).map(change => `<li><span>${escapeHtml(change.label)}</span><strong class="${change.diff>0?'positive':'negative'}">${change.diff>0?'+':''}${Number(change.diff).toLocaleString(locale())}</strong></li>`).join('') || `<li><span>${either('Изменений бонусов нет','No bonus changes')}</span><strong>—</strong></li>`;
    const flow = row.pairs.slice(0,6).map(([slot,id]) => `${businessVisual(slot.businessId)}<b>→</b>${businessVisual(id)}`).join('') + (row.pairs.length>6?`<b>+${row.pairs.length-6}</b>`:'');
    const vipMultiplier = vipPassiveIncomeMultiplier();
    const vipNotice = vipMultiplier > 1 ? `<div class="hk-optimizer-safety">${either('VIP учтён','VIP included')}: ×${vipMultiplier} ${either('для почасового пассивного дохода','for hourly passive income')}</div>` : '';
    box.innerHTML = `<div class="hk-optimizer-summary"><span>${tr('optimizerBefore')}<b>${row.beforeScore.toFixed(2)}</b></span><span>${tr('optimizerAfter')}<b>${row.afterScore.toFixed(2)}</b></span><span>${tr('optimizerChanges',{n:row.pairs.length})}<b>${row.pairs.length}</b></span></div><div class="hk-optimizer-flow">${flow || `<span>${either('Перестановка не требуется','No rearrangement needed')}</span>`}</div><b>${tr('optimizerDifference')}</b><ul>${changes}</ul>${vipNotice}<div class="hk-optimizer-safety ${row.safety.allowed?'':'blocked'}">${escapeHtml(row.safety.reason)} · ${tr('optimizerManagers',{busy:workers.busy,max:workers.max||'?'})}</div><button id="hk-optimizer-apply" class="hk-primary" ${row.safety.allowed&&row.pairs.length?'':'disabled'}>${tr('optimizerApply')}</button>`;
    installIconFallbacks(box);
    box.querySelector('#hk-optimizer-apply')?.addEventListener('click',applyBusinessOptimizer);
  }

  function bonusAnalyzerData() {
    const active = businessCounts(layout.map(row => row.businessId));
    const effects = new Map();
    for (const [id,count] of active) for (const effect of businessEffects(id)) {
      const row = effects.get(effect.key) || {id:effect.key,label:effect.label,total:0,sources:[]};
      const multiplier = businessEffectMultiplier(effect);
      row.total += effect.amount * count * multiplier;
      row.sources.push({id,count,amount:effect.amount,multiplier,contribution:effect.amount*count*multiplier,limit:businessActiveLimit(id)});
      effects.set(effect.key,row);
    }
    const rows = [...effects.values()].sort((a,b) => Math.abs(b.total)-Math.abs(a.total) || a.label.localeCompare(b.label));
    const candidates = inventory.filter(row => Number(row.quantity || 0) > 0).map(row => {
      const current = Number(active.get(row.businessId) || 0);
      const limit = businessActiveLimit(row.businessId);
      const limited = Number.isFinite(limit) && current >= limit;
      const effectRows = businessEffects(row.businessId);
      const score = effectRows.reduce((sum,effect) => sum + Math.log10(1 + Math.abs(effect.amount)),0);
      return {...row,current,limit,limited,effectRows,score};
    }).sort((a,b) => Number(a.limited)-Number(b.limited) || b.score-a.score || Number(recipeMetadata(b.businessId).tier||0)-Number(recipeMetadata(a.businessId).tier||0));
    return {rows,candidates,active};
  }

  function renderBonusAnalyzer() {
    const box = root?.querySelector('#hk-bonus-analyzer-result'); if (!box) return;
    if (!layout.length) { box.innerHTML = `<p class="hk-muted">${tr('optimizerNoPlan')}</p>`; return; }
    const data = bonusAnalyzerData();
    const sources = data.rows.map(row => {
      const sourceHtml = row.sources.map(source => {
        const meta = recipeMetadata(source.id), limit = Number.isFinite(source.limit) ? source.limit : '∞';
        const amount = Number(source.amount).toLocaleString(locale());
        const contribution = Number(source.contribution).toLocaleString(locale());
        const vip = source.multiplier > 1 ? ` × VIP ${source.multiplier}` : '';
        return `<span class="hk-bonus-source">${iconHtml(source.id)}<small><b>${escapeHtml(meta.name || source.id)}</b> · ${amount} × ${source.count}${vip} = ${contribution}<br>${tr('bonusActiveCopies',{active:source.count,limit})}</small></span>`;
      }).join('');
      return `<details class="hk-bonus-analysis-row"><summary><span>${escapeHtml(row.label)}</span><b>${Number(row.total).toLocaleString(locale())}</b><small>${tr('bonusDuplicates',{n:row.sources.length})}</small></summary><div>${sourceHtml}</div></details>`;
    }).join('') || `<p class="hk-muted">${tr('bonusZeroEffect')}</p>`;
    const best = data.candidates.find(row => !row.limited && row.score > 0);
    const limited = data.candidates.filter(row => row.limited).slice(0,5).map(row => `<span>${iconHtml(row.businessId)}<small>${escapeHtml(recipeMetadata(row.businessId).name || row.businessId)}</small></span>`).join('');
    box.innerHTML = `<h4>${tr('bonusSources')}</h4><div class="hk-bonus-analysis-list">${sources}</div><h4>${tr('bonusBestNext')}</h4>${best ? `<div class="hk-best-business">${iconHtml(best.businessId)}<span><b>${escapeHtml(recipeMetadata(best.businessId).name || best.businessId)}</b><small>T${recipeMetadata(best.businessId).tier || '—'} · ${escapeHtml(businessCardDetails(best.businessId).properties)}</small></span></div>` : `<p class="hk-muted">${tr('bonusNoCandidate')}</p>`}${limited ? `<h4>${tr('bonusLimited')}</h4><div class="hk-limited-businesses">${limited}</div>` : ''}`;
    installIconFallbacks(box);
  }

  function applyBusinessOptimizer() {
    if (!optimizerResult?.safety?.allowed) return;
    preparedBusinessPlan = optimizerResult.pairs.map(([row,id]) => [{key:row.key,businessId:row.businessId},id]);
    preparedBusinessPlanSource = 'optimizer';
    selectedSlots = new Set(optimizerResult.pairs.map(([row]) => row.key));
    selectedStock.clear();
    for (const [,id] of optimizerResult.pairs) if (id) selectedStock.set(id,(selectedStock.get(id)||0)+1);
    renderBusinessLists();
    root?.querySelector('[data-business-tab="regular"]')?.click();
  }

  function renderBusinessLists() {
    if (!businessLists) return;
    if (!preparedBusinessPlan) for (const row of layout) if (!row.businessId) selectedSlots.add(row.key);
    clampSelectedStockToSlots();
    const removeFilter = Number(document.querySelector('#hk-remove-tier')?.value || 0);
    const insertFilter = Number(document.querySelector('#hk-insert-tier')?.value || 0);
    const outgoing = layout.filter(row => removeFilter === -1 ? !row.businessId :
      !!row.businessId && (!removeFilter || tier(row.businessId) === removeFilter));
    const incoming = inventory.filter(row => !insertFilter || tier(row.businessId) === insertFilter);
    businessLists.innerHTML = `
      <section><h3>${tr('chooseBuildingSlots')}</h3><div class="hk-cards">${outgoing.map(row => {
        const details = row.businessId ? businessCardDetails(row.businessId) : null;
        return `
        <label class="hk-card ${selectedSlots.has(row.key) ? 'selected' : ''} ${row.businessId ? '' : 'empty'}">
          <input type="checkbox" data-slot="${escapeHtml(row.key)}" ${selectedSlots.has(row.key) ? 'checked' : ''}>
          ${row.businessId ? iconHtml(row.businessId) : '<span class="hk-empty-icon">＋</span>'}<span class="hk-business-info">${row.businessId
            ? `<b class="hk-business-name">${escapeHtml(details.name)}</b><small>T${tier(row.businessId) ?? '—'} · ${tr('influence', {n:Number(row.influence).toLocaleString(locale())})}</small><small class="hk-business-properties">${escapeHtml(details.properties)}</small>`
            : `<b>${tr('emptySlot')}</b><small>${escapeHtml(buildingSlotLabel(row))}</small>`}</span>
        </label>`;
      }).join('') || `<p class="hk-muted">${tr('noBusinesses')}</p>`}</div></section>
      <section><h3>${tr('insertFromStock')}</h3><div class="hk-cards">${incoming.map(row => {
        const maximum = Math.min(row.quantity, availableSlotsForBusiness(row.businessId));
        const selected = Math.min(maximum, Number(selectedStock.get(row.businessId) || 0));
        const details = businessCardDetails(row.businessId);
        return `
        <label class="hk-card ${(selectedStock.get(row.businessId) || 0) > 0 ? 'selected' : ''}">
          ${iconHtml(row.businessId)}<span class="hk-business-info"><b class="hk-business-name">${escapeHtml(details.name)}</b><small>T${tier(row.businessId) ?? '—'} · ${tr('inStock', {n:row.quantity})}</small><small class="hk-business-properties">${escapeHtml(details.properties)}</small></span>
          <select data-stock="${escapeHtml(row.businessId)}">${Array.from({length: maximum + 1}, (_, i) => `<option ${i === selected ? 'selected' : ''}>${i}</option>`).join('')}</select>
        </label>`;
      }).join('') || `<p class="hk-muted">${tr('noBusinesses')}</p>`}</div></section>`;
    installIconFallbacks(businessLists);
    businessLists.querySelectorAll('[data-slot]').forEach(input => input.addEventListener('change', () => {
      preparedBusinessPlan = null; preparedBusinessPlanSource = '';
      input.checked ? selectedSlots.add(input.dataset.slot) : selectedSlots.delete(input.dataset.slot);
      renderBusinessLists(); renderPlan();
    }));
    businessLists.querySelectorAll('[data-stock]').forEach(select => select.addEventListener('change', () => {
      preparedBusinessPlan = null; preparedBusinessPlanSource = '';
      const value = Number(select.value || 0);
      value ? selectedStock.set(select.dataset.stock, value) : selectedStock.delete(select.dataset.stock);
      renderBusinessLists(); renderPlan();
    }));
    renderBusinessOptimizer();
    renderBonusAnalyzer();
    renderPlan();
  }

  function selectedIncoming() {
    return [...selectedStock].flatMap(([id, count]) => Array.from({length: count}, () => id));
  }

  function buildingSlotLabel(row) {
    const match = String(row?.buildingId || '').match(/(\d+)(?!.*\d)/);
    const building = match?.[1] || row?.buildingLevel || '—';
    return tr('buildingSlot', {building, slot:row?.slot ?? '—'});
  }

  function businessVisual(id) {
    return id ? iconHtml(id) : '<span class="hk-empty-icon compact">＋</span>';
  }

  function resolvedPreparedBusinessPlan() {
    if (!Array.isArray(preparedBusinessPlan) || !preparedBusinessPlan.length) return null;
    const resolved = [];
    for (const [saved,id] of preparedBusinessPlan) {
      const current = layout.find(row => row.key === saved.key);
      if (!current || String(current.businessId || '') !== String(saved.businessId || '') || !selectedSlots.has(current.key)) return null;
      resolved.push([current,String(id || '')]);
    }
    const expected = businessCounts(resolved.map(([,id]) => id));
    if ([...expected].some(([id,count]) => Number(selectedStock.get(id)||0) !== count) ||
        [...selectedStock].some(([id,count]) => Number(expected.get(id)||0) !== Number(count||0))) return null;
    return resolved;
  }

  function makePlan() {
    const prepared = resolvedPreparedBusinessPlan();
    if (prepared) return prepared;
    const remaining = layout.filter(row => selectedSlots.has(row.key));
    const incoming = selectedIncoming();
    if (!remaining.length || !incoming.length) throw new Error(either(
      'Выберите хотя бы один бизнес для замены и один для вставки',
      'Select at least one business to replace and one business to insert'));
    if (incoming.length > remaining.length) throw new Error(either(
      `Для вставки ${incoming.length} бизнесов выбрано только ${remaining.length} слотов`,
      `Only ${remaining.length} slots are selected for ${incoming.length} incoming businesses`));
    return incoming.map(id => {
      const wantedTier = tier(id);
      remaining.sort((a,b) => Number(tier(a.businessId) !== wantedTier) - Number(tier(b.businessId) !== wantedTier) || a.key.localeCompare(b.key));
      return [remaining.shift(), id];
    });
  }

  function renderPlan() {
    if (!planBox) return;
    const removeCount = selectedSlots.size;
    const insertCount = businessSelectionCount();
    let body = `<div class="hk-count">${tr('selectedPlan', {remove:removeCount, insert:insertCount})}</div>`;
    try {
      const plan = makePlan();
      body += `<div class="hk-plan-row">${plan.slice(0, 4).map(([row,id]) => `${businessVisual(row.businessId)}<b>→</b>${businessVisual(id)}`).join('')}${plan.length > 4 ? `<b>+${plan.length-4}</b>` : ''}</div>`;
      const untouched = Math.max(0, removeCount - plan.length);
      if (untouched) body += `<p class="hk-muted">${escapeHtml(either(
        `${untouched} выбранных бизнесов останутся на своих местах`,
        `${untouched} selected businesses will remain unchanged`))}</p>`;
      body += `<button id="hk-business-run" class="hk-primary">${tr('execute')}</button>`;
    } catch (error) { body += `<p class="hk-muted">${escapeHtml(error.message)}</p>`; }
    planBox.innerHTML = body;
    installIconFallbacks(planBox);
    document.querySelector('#hk-business-run')?.addEventListener('click', executeBusinessPlan);
  }

  async function businessAction(action, row, businessId = null, timer = null) {
    const payload = {business_building_id: row.buildingId, slot_index: Number(row.slot)};
    if (action === 'insert') { payload.business_id = businessId; payload.count = 1; }
    if (action === 'speedUp') payload.timer = Number(timer);
    return apiJson(`/player/business/${action}`,'POST',payload,true,3);
  }

  function findSlot(documentValue, buildingId, slot) {
    return normalizeLayout(documentValue).find(row => row.buildingId === buildingId && row.slot === Number(slot));
  }

  function businessWorkerState(documentValue) {
    let result = null;
    const visit = value => {
      if (result || !value || typeof value !== 'object') return;
      const busyValue = value.business_worker_busy ?? value.pendingBusinesses;
      const maxValue = value.business_worker_max ?? value.maxPendingBusinesses;
      if (busyValue !== undefined || maxValue !== undefined) {
        const busy = Math.max(0, Number(busyValue || 0));
        const max = Math.max(0, Number(maxValue || 0));
        if (Number.isFinite(busy) && Number.isFinite(max)) result = {busy, max};
      }
      if (!result) for (const child of Object.values(value)) visit(child);
    };
    visit(documentValue);
    return result || {busy:0, max:0};
  }

  async function readBusinessSlot(buildingId, slot, accept = null, attempts = 5) {
    let state = null;
    for (let attempt = 0; attempt < attempts; attempt++) {
      if (hkRunner.running) await hkRunner.waitIfPaused();
      playerDocument = await apiJson('/player/me', 'POST');
      state = findSlot(playerDocument, buildingId, slot);
      if (state && (!accept || accept(state))) return state;
    }
    return state;
  }

  function businessSlotIsActive(state, businessId = '') {
    return !!state?.businessId && (!businessId || state.businessId === businessId) &&
      String(state.status || '').toUpperCase() === 'ACTIVE' && Number(state.timer || 0) <= 0;
  }

  async function finishPendingBusiness(row, label = '', useCurrentState = false) {
    let state = useCurrentState ? row : await readBusinessSlot(row.buildingId, row.slot);
    const expectedBusinessId = state?.businessId || row.businessId || '';
    if (!state?.businessId || businessSlotIsActive(state, expectedBusinessId)) return false;
    const remaining = Math.max(0, Number(state.timer || 0));
    const free = Math.max(0, Number(state.freeSpeedUpTime || 0));
    if (remaining > 0) {
      if (free < remaining) throw new Error(either(
        `Менеджер занят: бесплатное ускорение для ${label || buildingSlotLabel(state)} пока недоступно. Кристаллы не потрачены`,
        `A manager is busy: free speed-up is not available yet for ${label || buildingSlotLabel(state)}. No crystals were spent`));
      const response = await businessAction('speedUp', state, null, remaining);
      log(`${either('Бесплатно ускорен', 'Sped up for free')} ${label || `T${tier(state.businessId)}`} (0)`);
      state = findSlot(response, row.buildingId, row.slot) || state;
      if (!state) throw new Error(either('После ускорения сервер не вернул бизнес', 'The server did not return the business after speed-up'));
      const settled = await readBusinessSlot(row.buildingId, row.slot,
        value => value.businessId === expectedBusinessId && Number(value.timer || 0) <= 0, 8);
      if (settled?.businessId === expectedBusinessId) state = settled;
    }
    if (!businessSlotIsActive(state, expectedBusinessId)) {
      await businessAction('activate', state);
      log(`${either('Активирован', 'Activated')} ${label || `T${tier(state.businessId)}`}`);
      state = await readBusinessSlot(row.buildingId, row.slot,
        value => businessSlotIsActive(value, expectedBusinessId), 8);
      if (!businessSlotIsActive(state, expectedBusinessId)) {
        // Retry immediately: each preceding /player/me response already acts
        // as the synchronization point, so an extra fixed pause is unnecessary.
        try { await businessAction('activate', state); }
        catch (error) {
          if (!/HTTP 409|already active|activation time not passed/i.test(error.message)) throw error;
        }
        state = await readBusinessSlot(row.buildingId, row.slot,
          value => businessSlotIsActive(value, expectedBusinessId), 8);
      }
      if (!businessSlotIsActive(state, expectedBusinessId)) throw new Error(either(
        `Не подтверждена активация ${label || `T${tier(expectedBusinessId)}`}`,
        `Activation was not confirmed for ${label || `T${tier(expectedBusinessId)}`}`));
    }
    return true;
  }

  async function releaseFreeBusinessManagers() {
    let workers = businessWorkerState(playerDocument);
    if (!workers.max || workers.busy < workers.max) return;
    const pending = normalizeLayout(playerDocument).filter(row => row.businessId &&
      (row.status !== 'ACTIVE' || Number(row.timer || 0) > 0));
    for (const row of pending) {
      if (hkRunner.running) await hkRunner.waitIfPaused();
      await finishPendingBusiness(row);
      playerDocument = await apiJson('/player/me', 'POST');
      workers = businessWorkerState(playerDocument);
      if (!workers.max || workers.busy < workers.max) return;
    }
    throw new Error(either(
      `Нет свободных бизнес-менеджеров (${workers.busy}/${workers.max}). Завершите текущую вставку в игре`,
      `No free business managers (${workers.busy}/${workers.max}). Finish the current insertion in the game`));
  }

  async function executeBusinessPlan() {
    if (!requireLicense() || businessBusy) return;
    let plan;
    try { plan = makePlan(); } catch (error) { alert(error.message); return; }
    if (!confirm(language === 'en'
      ? `Rearrange ${plan.length} businesses?\n\nOnly the free 0-cost speed-up will be used after insertion. Crystals are prohibited.`
      : `Переставить ${plan.length} бизнесов?\n\nПосле вставки будет использовано только бесплатное ускорение за 0. Кристаллы запрещены.`)) return;
    if (hkRunner.running) { alert(either('Сначала завершите текущую задачу','Finish the current task first')); return; }
    hkRunner.start({title:either('Перестановка бизнесов','Business rearrangement'),total:Math.max(1,plan.length),step:either('Подготовка','Preparing'),pausable:true,stoppable:true});
    businessBusy = true;
    const removed = [], inserted = [];
    try {
      log(either('Проверяю игровую сессию…', 'Checking game session…'));
      try {
        playerDocument = await apiJson('/player/me', 'POST');
        await releaseFreeBusinessManagers();
        playerDocument = await apiJson('/player/me', 'POST');
        refreshBusinessData();
        plan = makePlan();
        const safety = optimizerSafety(plan.length);
        if (!safety.allowed) throw new Error(safety.reason);
      } catch (sessionError) {
        if (/HTTP 401|unauthorized/i.test(sessionError.message)) {
          throw new Error(either('Игровая сессия истекла. Обновите страницу игры, снова откройте HK и повторите перестановку',
            'Game session expired. Refresh the game page, reopen HK, and run the rearrangement again'));
        }
        throw sessionError;
      }
      if (preparedBusinessPlanSource !== 'restore') {
        save({businessOriginalLayout:{savedAt:Date.now(), slots:layout.map(row => ({key:row.key,businessId:row.businessId || ''}))}});
      }
      for (const [row] of plan) {
        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');
        await hkRunner.waitIfPaused();
        hkRunner.setStep(either('Снимаю бизнесы','Removing businesses'), removed.length, Math.max(1,plan.length));
        if (!row.businessId) { log(`Пустой слот: ${buildingSlotLabel(row)}`); continue; }
        log(`Снимаю T${tier(row.businessId)}…`);
        await businessAction('remove', row); removed.push(row);
      }
      for (const [row, id] of plan) {
        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');
        await hkRunner.waitIfPaused();
        hkRunner.setStep(either('Вставляю бизнесы','Inserting businesses'), inserted.length, Math.max(1,plan.length));
        if (!id) { log(`${either('Оставляю пустым','Leaving empty')}: ${buildingSlotLabel(row)}`); continue; }
        log(`Вставляю T${tier(id)}…`);
        const response = await businessAction('insert', row, id); inserted.push([row,id]);
        const state = findSlot(response, row.buildingId, row.slot);
        if (!state) throw new Error('После вставки сервер не вернул новый бизнес');
        if (state.businessId !== id) throw new Error(either('Сервер вернул другой бизнес после вставки', 'The server returned a different business after insertion'));
        await finishPendingBusiness(state, `T${tier(id)}`, true);
      }
      // Do not announce completion until every inserted business, including the
      // last one, is confirmed ACTIVE by /player/me.
      for (const [row, id] of inserted) {
        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');
        await hkRunner.waitIfPaused();
        let state = await readBusinessSlot(row.buildingId, row.slot,
          value => businessSlotIsActive(value, id), 6);
        if (!businessSlotIsActive(state, id)) {
          if (!state || state.businessId !== id) throw new Error(either(
            `Последний контроль: в слоте отсутствует вставленный T${tier(id)}`,
            `Final check: inserted T${tier(id)} is missing from its slot`));
          await finishPendingBusiness(state, `T${tier(id)}`, true);
          state = await readBusinessSlot(row.buildingId, row.slot,
            value => businessSlotIsActive(value, id), 6);
        }
        if (!businessSlotIsActive(state, id)) throw new Error(either(
          `Последний контроль: T${tier(id)} не активирован`,
          `Final check: T${tier(id)} is not active`));
      }
      playerDocument = await hkAuthoritativePlayerRead('business-complete');
      refreshBusinessData();
      hkRunner.finish(either('Перестановка завершена','Rearrangement completed'));
      selectedSlots.clear(); selectedStock.clear(); preparedBusinessPlan = null; preparedBusinessPlanSource = '';
      log('Перестановка завершена', 'ok');
      showVisualNotice(either('Перестановка бизнесов завершена', 'Business rearrangement completed'), either(
        `Все переставленные бизнесы активированы: ${inserted.length}`,
        `All rearranged businesses are active: ${inserted.length}`));
    } catch (error) {
      if (error?.name === 'AbortError') {
        hkRunner.reset();
        log(either('Перестановка остановлена. Текущую схему нужно перечитать.','Rearrangement stopped. Current layout must be reread.'),'warn');
      } else {
      hkRunner.fail(error);
      const changed = removed.length > 0 || inserted.length > 0;
      if (!changed) {
        log(`${either('Ошибка', 'Error')}: ${error.message}. ${either('Изменения не выполнялись', 'No changes were made')}`, 'bad');
      } else if (/HTTP 401|unauthorized|сессия истекла|session expired/i.test(error.message)) {
        log(`${either('Ошибка', 'Error')}: ${error.message}. ${either('Автоматический откат невозможен без новой сессии', 'Automatic rollback is impossible without a new session')}`, 'bad');
        alert(either('Сессия игры истекла во время перестановки. Обновите игру и проверьте здания.', 'The game session expired during rearrangement. Refresh the game and check the buildings.'));
      } else {
        log(`${either('Ошибка', 'Error')}: ${error.message}. ${either('Пробую вернуть исходную схему', 'Trying to restore the original layout')}`, 'bad');
        try {
          for (const [row] of inserted.reverse()) await businessAction('remove', row);
          for (const row of removed) {
            await businessAction('insert', row, row.businessId);
            const restored = await readBusinessSlot(row.buildingId, row.slot, value => value.businessId === row.businessId);
            if (!restored) throw new Error(either('Сервер не вернул восстановленный бизнес', 'The server did not return the restored business'));
            await finishPendingBusiness(restored, `T${tier(row.businessId)}`);
          }
          log('Исходная схема восстановлена', 'ok');
        } catch (rollback) {
          log(`Откат не завершён: ${rollback.message}`, 'bad');
          alert(either('Не удалось полностью вернуть исходную схему. Проверьте здания в игре.', 'Could not fully restore the original layout. Check the buildings in the game.'));
        }
      }
      }
    } finally {
      businessBusy = false;
      renderPlan();
    }
  }

  function prepareOriginalBusinessRestore() {
    const original = load().businessOriginalLayout;
    if (!Array.isArray(original?.slots) || !original.slots.length) {
      alert(either('Сохранённой исходной схемы пока нет.', 'No saved original setup yet.')); return;
    }
    const available = new Map(businessCounts(layout.map(row => row.businessId)));
    for (const row of inventory) available.set(row.businessId,(available.get(row.businessId)||0)+Number(row.quantity||0));
    const needed = businessCounts(original.slots.map(row => row.businessId));
    const missing = [...needed].filter(([id,count]) => Number(available.get(id)||0)<count);
    if (missing.length) {
      alert(either('Не все бизнесы исходной схемы доступны на складе или в зданиях.', 'Not all businesses from the original setup are available.')); return;
    }
    const pairs = [];
    for (const saved of original.slots) {
      const current = layout.find(row => row.key === saved.key); if (!current) continue;
      const wanted = String(saved.businessId || '');
      if (String(current.businessId || '') !== wanted) pairs.push([current,wanted]);
    }
    if (!pairs.length) { alert(either('Исходная схема уже установлена.', 'The original setup is already active.')); return; }
    preparedBusinessPlan = pairs.map(([row,id]) => [{key:row.key,businessId:row.businessId || ''},id]);
    preparedBusinessPlanSource = 'restore';
    selectedSlots = new Set(pairs.map(([row]) => row.key)); selectedStock.clear();
    for (const [,id] of pairs) if (id) selectedStock.set(id,(selectedStock.get(id)||0)+1);
    renderBusinessLists();
  }

  function presets() { return load().presets || {}; }
  function refreshPresets(selectName = '') {
    if (!presetSelect) return;
    const names = Object.keys(presets());
    presetSelect.innerHTML = `<option value="">${tr('savedSets')}</option>${names.map(name => `<option ${name === selectName ? 'selected' : ''}>${escapeHtml(name)}</option>`).join('')}`;
  }

  function savePreset() {
    const name = prompt(either('Название набора:', 'Set name:')); if (!name?.trim()) return;
    const all = presets();
    const destinations = layout.filter(row => selectedSlots.has(row.key));
    all[name.trim()] = {slots: destinations.map(row => ({key:row.key, businessId:row.businessId || ''})),
      remove: destinations.map(row => row.businessId).filter(Boolean), insert: selectedIncoming()};
    save({presets: all}); refreshPresets(name.trim()); log(`Набор «${name.trim()}» сохранён`);
  }

  function loadPreset(name) {
    const preset = presets()[name]; if (!preset) return;
    preparedBusinessPlan = null; preparedBusinessPlanSource = '';
    selectedSlots.clear(); selectedStock.clear();
    if (Array.isArray(preset.slots)) {
      for (const saved of preset.slots) {
        const row = layout.find(item => item.key === saved.key && (saved.businessId ? item.businessId === saved.businessId : !item.businessId));
        if (row) selectedSlots.add(row.key);
      }
    } else {
      const wanted = [...(preset.remove || [])];
      for (const id of wanted) { const row = layout.find(item => item.businessId === id && !selectedSlots.has(item.key)); if (row) selectedSlots.add(row.key); }
    }
    for (const id of preset.insert || []) selectedStock.set(id, (selectedStock.get(id) || 0) + 1);
    refreshBusinessData(); log(`Набор «${name}» выбран`);
  }

  function deletePreset() {
    const name = presetSelect?.value; if (!name || !confirm(`Удалить набор «${name}»?`)) return;
    const all = presets(); delete all[name]; save({presets: all}); refreshPresets();
  }

  function exportPowers() {
    const types=['normal','boss','gang']; const rowsByType=Object.fromEntries(types.map(type=>[type,new Map(combinedPitRows(type).map(row=>[Number(row.level),row]))]));
    const levels=[...new Set(types.flatMap(type=>[...rowsByType[type].keys()]))].sort((a,b)=>a-b);
    if (!levels.length) { alert(either('Пока нет сохранённых данных', 'No saved data yet')); return; }
    const csv = `\uFEFF${either('Уровень;Обычная Яма;Яма боссов;Яма банд', 'Level;Normal Pit;Boss Pit;Gang Pit')}\n` + levels.map(level=>`${level};${types.map(type=>rowsByType[type].get(level)?.enemy_power||'').join(';')}`).join('\n');
    const link = document.createElement('a'); link.href = URL.createObjectURL(new Blob([csv], {type:'text/csv'})); link.download = 'pit_levels_three_pits.csv'; link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  }

  function fillTierFilters() {
    const remove = root?.querySelector('#hk-remove-tier');
    const insert = root?.querySelector('#hk-insert-tier');
    const removeValue = remove?.value || '0';
    const insertValue = insert?.value || '0';
    if (remove) {
      remove.innerHTML = `<option value="0">${tr('removeAll')}</option><option value="-1">${tr('emptySlots')}</option>` +
        Array.from({length:6}, (_,i) => `<option value="${i+1}">${tr('removeTier',{n:i+1})}</option>`).join('');
      remove.value = [...remove.options].some(option => option.value === removeValue) ? removeValue : '0';
    }
    if (insert) {
      insert.innerHTML = `<option value="0">${tr('insertAll')}</option>` +
        Array.from({length:6}, (_,i) => `<option value="${i+1}">${tr('insertTier',{n:i+1})}</option>`).join('');
      insert.value = [...insert.options].some(option => option.value === insertValue) ? insertValue : '0';
    }
  }

  function clanWeekStart(value = new Date()) {
    const date = new Date(value);
    date.setHours(0, 0, 0, 0);
    date.setDate(date.getDate() - ((date.getDay() + 6) % 7));
    return date;
  }

  function clanWeekKey(value = new Date()) {
    const date = clanWeekStart(value);
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  }

  function localDateKey(value = new Date()) {
    const date = new Date(value);
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  }

  function clanSkillStore() {
    const stored = load().clanSkills;
    return stored && typeof stored === 'object' ? stored : {snapshots:[]};
  }

  function clanTimestamp(value) {
    const numeric = Number(value || 0);
    if (!numeric) return 0;
    return numeric < 1e12 ? numeric * 1000 : numeric;
  }

  function clanIdentity(staticDocument = {}, linesDocument = {}, clanDocument = {}) {
    const player = playerDocument?.player || {};
    const candidates = [
      // `/clan/info` is authoritative and common to every member. Prefer its
      // explicit clan_id over nested player objects that may describe the
      // membership rather than the clan itself.
      clanDocument?.clan_id, clanDocument?.clan?.clan_id, clanDocument?.clan?.id,
      clanDocument?.clan_info?.clan_id, clanDocument?.clan_info?.id,
      clanDocument?.player?.clan_id, clanDocument?.player?.clan?.id,
      player.clan_id, player.clanId, player.clan_uuid, player.clan?.clan_id, player.clan?.id,
      staticDocument?.clan?.id, staticDocument?.clan_id, staticDocument?.clanId,
      linesDocument?.clan?.id, linesDocument?.clan_id, linesDocument?.clanId
    ];
    return clean(candidates.find(value => value !== undefined && value !== null && String(value).trim()) || '');
  }

  function normalizeClanSkillSnapshot(staticDocument, linesDocument, historyDocument, clanDocument = {}, membersDocument = {}, statsDocument = {}) {
    const blocksSource = Array.isArray(staticDocument?.clan_blocks) ? staticDocument.clan_blocks : [];
    const lineStateSource = Array.isArray(linesDocument?.clan_skill_lines) ? linesDocument.clan_skill_lines : [];
    const historySource = Array.isArray(historyDocument?.clan_skill_lines_history) ? historyDocument.clan_skill_lines_history : [];
    const lineState = {};
    lineStateSource.forEach(row => {
      const id = String(row.line_id ?? row.id ?? '');
      if (!id) return;
      lineState[id] = {
        level: row.is_locked ? 0 : Number(row.level || 0) + Number(row.uncommited_player_level || 0),
        playerLevel: Number(row.player_level || 0),
        locked: Boolean(row.is_locked)
      };
    });
    const contributions = {};
    historySource.forEach(row => {
      const lineId = String(row.skill_line_id ?? row.line_id ?? '');
      const nickname = clean(row.nickname || row.player_name || row.player_id || either('Неизвестный игрок', 'Unknown player'));
      const level = Number(row.status === 'BUY' && !row.level ? 0 : row.level ?? row.level_delta ?? 0);
      if (!lineId || !level) return;
      contributions[lineId] ||= {};
      contributions[lineId][nickname] ||= {level:0, pending:0};
      contributions[lineId][nickname][row.is_applied === false ? 'pending' : 'level'] += level;
    });
    const blocks = blocksSource.map((block, blockIndex) => {
      const sourceLines = Array.isArray(block.clan_skill_lines) ? block.clan_skill_lines : [];
      const lines = sourceLines.map((line, lineIndex) => ({
        id:String(line.id ?? line.line_id ?? `${blockIndex}-${lineIndex}`),
        name:String(line.meta?.name || line.name || either(`Подветка ${lineIndex + 1}`, `Sub-branch ${lineIndex + 1}`)),
        icon:mediaUrl(line.meta?.icon || line.icon || ''),
        order:Number(line.meta?.order ?? line.order ?? lineIndex)
      })).sort((a,b) => a.order - b.order);
      return {
        id:String(block.id ?? blockIndex),
        name:String(block.meta?.name || block.name || either(`Основная ветка ${blockIndex + 1}`, `Main branch ${blockIndex + 1}`)),
        icon:mediaUrl(block.meta?.image || block.meta?.icon || block.image || lines[0]?.icon || ''),
        order:Number(block.meta?.order ?? block.clan_level ?? blockIndex),
        lines
      };
    }).sort((a,b) => a.order - b.order);
    const historyPlayers = new Map();
    for (const [lineId, players] of Object.entries(contributions)) for (const [nickname, values] of Object.entries(players)) {
      const player = historyPlayers.get(nickname) || {nickname, levels:{}};
      player.levels[lineId] = Math.max(0, Number(values.level || 0) + Number(values.pending || 0));
      historyPlayers.set(nickname, player);
    }
    // This is the same authoritative distribution used by the game's
    // "Clan skills -> Distribution" screen. History is only a recent event
    // log and therefore cannot reconstruct players who upgraded earlier.
    const statsSource = Array.isArray(statsDocument) ? statsDocument
      : Array.isArray(statsDocument?.clan_skill_lines_stats) ? statsDocument.clan_skill_lines_stats
      : Array.isArray(statsDocument?.data?.clan_skill_lines_stats) ? statsDocument.data.clan_skill_lines_stats : [];
    const statsPlayersById = new Map();
    const statsPlayersByNickname = new Map();
    statsSource.forEach(row => {
      const memberId = clean(row.player_id ?? row.member_id ?? row.id ?? '');
      const nickname = clean(row.nickname || row.player_name || '');
      const lineId = String(row.skill_line_id ?? row.line_id ?? '');
      if (!lineId || (!memberId && !nickname)) return;
      let player = (memberId && statsPlayersById.get(memberId)) || (nickname && statsPlayersByNickname.get(nickname));
      if (!player) player = {memberId, nickname, levels:{}};
      if (memberId) player.memberId = memberId;
      if (nickname) player.nickname = nickname;
      player.levels[lineId] = Math.max(0, Number(row.level ?? row.player_level ?? row.value ?? 0));
      if (player.memberId) statsPlayersById.set(player.memberId, player);
      if (player.nickname) statsPlayersByNickname.set(player.nickname, player);
    });
    const membersSource = Array.isArray(membersDocument?.clan_members) ? membersDocument.clan_members : [];
    const directPlayers = membersSource.map(member => {
      const nickname = clean(member.nickname || member.player_name || member.id || either('Неизвестный игрок','Unknown player'));
      const memberId = clean(member.id ?? member.player_id ?? member.member_id ?? '');
      const stats = (memberId && statsPlayersById.get(memberId)) || statsPlayersByNickname.get(nickname);
      const history = historyPlayers.get(nickname);
      const levels = {...(stats?.levels || history?.levels || {})};
      const calculatedTotal = Object.values(levels).reduce((sum, value) => sum + Math.max(0, Number(value || 0)), 0);
      const rawServerTotal = member.skill_line_levels ?? member.skill_levels;
      const serverTotal = Number(rawServerTotal);
      return {player_id:memberId, nickname, levels, total:rawServerTotal !== undefined && Number.isFinite(serverTotal) && serverTotal >= 0 ? serverTotal : calculatedTotal, scanned_at:Math.floor(Date.now()/1000)};
    }).filter(row => row.nickname);
    const included = new Set(directPlayers.map(row => row.nickname));
    for (const player of new Set([...statsPlayersById.values(), ...statsPlayersByNickname.values()])) {
      if (!player.nickname || included.has(player.nickname)) continue;
      const levels = {...player.levels};
      directPlayers.push({player_id:clean(player.memberId || ''), nickname:player.nickname, levels, total:Object.values(levels).reduce((sum,value)=>sum+Math.max(0,Number(value||0)),0), scanned_at:Math.floor(Date.now()/1000)});
      included.add(player.nickname);
    }
    if (!directPlayers.length) for (const player of historyPlayers.values()) {
      const levels = {...player.levels};
      directPlayers.push({...player, levels, total:Object.values(levels).reduce((sum,value)=>sum+Math.max(0,Number(value||0)),0), scanned_at:Math.floor(Date.now()/1000)});
    }
    return {
      weekKey:clanWeekKey(), scannedAt:Date.now(), blocks, lineState, contributions,
      clanKey:clanIdentity(staticDocument, linesDocument, clanDocument), sharedPlayers:[], directPlayers
    };
  }

  function clanCanonicalSnapshot(snapshot) {
    const sourcePlayers = Array.isArray(snapshot?.directPlayers) && snapshot.directPlayers.length
      ? snapshot.directPlayers
      : (Array.isArray(snapshot?.sharedPlayers) ? snapshot.sharedPlayers : []);
    const players = sourcePlayers.map(row => {
      const levels = row?.levels && typeof row.levels === 'object' ? row.levels : {};
      return {
        player_id:clean(row?.player_id ?? row?.playerId ?? row?.memberId ?? ''),
        nickname:clean(row?.nickname || either('Неизвестный игрок','Unknown player')),
        total:Math.max(0, Number(row?.total ?? Object.values(levels).reduce((sum,value)=>sum+Math.max(0,Number(value||0)),0))),
        levels
      };
    }).filter(row => row.nickname);
    return {
      schema_version:2,
      clan_key:String(snapshot?.clanKey || ''),
      week_key:String(snapshot?.weekKey || clanWeekKey()),
      captured_at:Math.floor(Number(snapshot?.scannedAt || Date.now())/1000),
      participants_count:players.length,
      overall:players.map(row => ({player_id:row.player_id,nickname:row.nickname,total:row.total})),
      blocks:(snapshot?.blocks || []).map(block => ({
        id:String(block?.id || ''),
        title:String(block?.name || ''),
        icon:String(block?.icon || ''),
        branches:(block?.lines || []).map(line => ({
          id:String(line?.id || ''),
          title:String(line?.name || ''),
          icon:String(line?.icon || ''),
          total:Math.max(0,Number(snapshot?.lineState?.[line?.id]?.level || 0)),
          player_level:Math.max(0,Number(snapshot?.lineState?.[line?.id]?.playerLevel || 0)),
          participants_count:players.length,
          players:players.map(row => ({
            player_id:row.player_id,
            nickname:row.nickname,
            value:Math.max(0,Number(row.levels?.[line?.id] || 0))
          }))
        }))
      }))
    };
  }

  async function uploadClanCanonicalSnapshot(snapshot) {
    if (!snapshot?.clanKey || !licenseState.allowed) return false;
    const canonical = clanCanonicalSnapshot(snapshot);
    await clanSkillsServerJson('/snapshot', {snapshot:canonical});
    return true;
  }

  async function scanClanSkills(automatic = false) {
    if (clanSkillScanning || !apiHeaders.Authorization) return false;
    if (automatic && hkRunner.running) return false;
    if (!automatic && hkRunner.running) { alert(either('Сначала завершите текущую задачу','Finish the current task first')); return false; }
    const runnerOwned = !automatic;
    if (runnerOwned) hkRunner.start({title:either('Навыки клана','Clan skills'),total:5,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});
    const clanScanCheckpoint = async (step,done=0) => {
      if (!runnerOwned) return;
      if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');
      await hkRunner.waitIfPaused();
      hkRunner.setStep(step,done,5);
    };
    clanSkillScanning = true; renderClanSkills();
    try {
      const readClanDocument = async path => {
        let lastError;
        for (let attempt = 0; attempt < 5; attempt += 1) {
          await clanScanCheckpoint(either('Данные клана','Clan data'),0);
          if (attempt) await gameRetryDelay(1500 * attempt);
          try { return await apiJson(path); }
          catch (error) {
            lastError = error;
            const gameIsBusy = /HTTP 429|Player state is locked by other request/i.test(String(error?.message || error));
            if (!gameIsBusy) throw error;
          }
        }
        throw lastError;
      };
      const readClanStats = async () => {
        let lastError;
        for (let attempt = 0; attempt < 7; attempt += 1) {
          await clanScanCheckpoint(either('Статистика навыков','Skill statistics'),1);
          if (attempt) await gameRetryDelay(1200 * attempt);
          try {
            const documentValue = await apiJson('/clan/skill_lines/stats');
            const rows = Array.isArray(documentValue) ? documentValue
              : Array.isArray(documentValue?.clan_skill_lines_stats) ? documentValue.clan_skill_lines_stats
              : Array.isArray(documentValue?.data?.clan_skill_lines_stats) ? documentValue.data.clan_skill_lines_stats : [];
            if (rows.length) return documentValue;
            lastError = new Error(either('Игра вернула пустую статистику навыков клана', 'The game returned empty clan skill statistics'));
          } catch (error) {
            lastError = error;
            const retryable = /HTTP 409|HTTP 429|Player state is locked|NetworkError|fetch resource/i.test(String(error?.message || error));
            if (!retryable) throw error;
          }
        }
        throw lastError;
      };
      // Clan endpoints lock the player state. Reading them in parallel makes the
      // game reject its own neighbouring requests with HTTP 429.
      // The full distribution is the most important response and is requested
      // before the auxiliary clan documents. Never replace a failed response
      // with the recent history log: that made most members appear as zero.
      const statsDocument = await readClanStats();
      await clanScanCheckpoint(either('Данные клана','Clan data'),2);
      await gameRetryDelay(800);
      let clanDocument = {};
      try { clanDocument = await readClanDocument('/clan/info'); }
      catch (error) { console.warn('[HK] authoritative clan id read failed', error); }
      await clanScanCheckpoint(either('Структура навыков','Skill structure'),3);
      await gameRetryDelay(800);
      const staticDocument = await readClanDocument('/clan/static_info');
      await gameRetryDelay(800);
      const linesDocument = await readClanDocument('/clan/skill_lines');
      await gameRetryDelay(800);
      let historyDocument = {};
      try { historyDocument = await readClanDocument('/clan/skill_lines/history'); }
      catch (error) { console.warn('[HK] clan skill distribution history read failed', error); }
      await sleep(800);
      let membersDocument = {};
      const clanKey = clanIdentity(staticDocument, linesDocument, clanDocument);
      if (clanKey) {
        try { membersDocument = await readClanDocument(`/clan/members?clan_id=${encodeURIComponent(clanKey)}`); }
        catch (error) { console.warn('[HK] clan member distribution read failed', error); }
      }
      const snapshot = normalizeClanSkillSnapshot(staticDocument, linesDocument, historyDocument, clanDocument, membersDocument, statsDocument);
      if (!snapshot.blocks.length) throw new Error(either('В ответе игры нет веток навыков клана', 'The game response contains no clan skill branches'));
      const nickname = clean(playerDocument?.player?.nickname || playerDocument?.player?.name || licenseState.playerId);
      if (snapshot.directPlayers.length) {
        snapshot.sharedPlayers = snapshot.directPlayers;
      } else if (snapshot.clanKey) {
        try {
          const levels = Object.fromEntries(Object.entries(snapshot.lineState).map(([id, row]) => [id, Math.max(0, Number(row.playerLevel || 0))]));
          const shared = await clanSkillsServerJson('/submit', {
            clan_key:snapshot.clanKey, week_key:snapshot.weekKey, nickname, levels
          });
          snapshot.sharedPlayers = Array.isArray(shared.players) ? shared.players : [];
        } catch (error) {
          console.warn('[HK] clan skill sharing failed', error);
          log(`${either('Навыки считаны локально, общая база временно недоступна', 'Skills read locally; shared database is temporarily unavailable')}: ${error.message}`, 'warn');
        }
      } else {
        log(either('Навыки считаны локально, но игра не передала ID клана', 'Skills read locally, but the game did not provide the clan ID'), 'warn');
      }
      if (!snapshot.sharedPlayers.length) {
        const levels = Object.fromEntries(Object.entries(snapshot.lineState).map(([id, row]) => [id, Math.max(0, Number(row.playerLevel || 0))]));
        snapshot.sharedPlayers = [{nickname, levels, total:Object.values(levels).reduce((sum, value) => sum + Number(value || 0), 0), scanned_at:Math.floor(Date.now()/1000)}];
      }
      const stored = clanSkillStore();
      const snapshots = (Array.isArray(stored.snapshots) ? stored.snapshots : []).filter(row => row?.weekKey !== snapshot.weekKey);
      snapshots.push(snapshot);
      snapshots.sort((a,b) => Number(a.scannedAt || 0) - Number(b.scannedAt || 0));
      const next = {...stored, snapshots:snapshots.slice(-12), selectedWeek:snapshot.weekKey};
      if (automatic) next.lastAutomaticClanScan = localDateKey();
      if (!next.selectedBlockId || !snapshot.blocks.some(row => row.id === next.selectedBlockId)) next.selectedBlockId = snapshot.blocks[0].id;
      const selectedBlock = snapshot.blocks.find(row => row.id === next.selectedBlockId) || snapshot.blocks[0];
      if (!next.selectedLineId || !selectedBlock.lines.some(row => row.id === next.selectedLineId)) next.selectedLineId = selectedBlock.lines[0]?.id || '';
      save({clanSkills:next});
      try {
        await uploadClanCanonicalSnapshot(snapshot);
        log(either('Статистика клана синхронизирована с сайтом','Clan statistics synced with the website'), 'ok');
      } catch (syncError) {
        console.warn('[HK] clan website snapshot upload failed', syncError);
        log(`${either('Навыки считаны, но синхронизация с сайтом временно не удалась','Skills were read, but website sync temporarily failed')}: ${syncError.message}`, 'warn');
      }
      log(either(`Навыки клана считаны: веток ${snapshot.blocks.length}, участников ${snapshot.sharedPlayers.length}`,
        `Clan skills read: ${snapshot.blocks.length} branches, ${snapshot.sharedPlayers.length} members`), 'ok');
      if (runnerOwned) hkRunner.finish(either('Навыки клана считаны','Clan skills read'));
      return true;
    } catch (error) {
      if (runnerOwned && error?.name === 'AbortError') {
        hkRunner.reset();
        log(either('Считывание навыков остановлено','Clan skill scan stopped'),'warn');
      } else {
        if (runnerOwned) hkRunner.fail(error);
        log(either('Ошибка чтения навыков клана','Clan skill read error') + ': ' + (error?.message || error), 'error');
      }
      return false;
    } finally {
      clanSkillScanning = false; renderClanSkills();
    }
  }

  async function maybeAutoScanClanSkills() {
    if (clanSkillScanning || !apiHeaders.Authorization || !licenseState.allowed) return;
    const stored = clanSkillStore();
    const today = localDateKey();
    if (stored.lastAutomaticClanScan === today) return;
    await scanClanSkills(true);
  }

  async function refreshSharedClanSkills() {
    if (clanSkillRefreshing || !apiHeaders.Authorization || !licenseState.allowed) return;
    const stored = clanSkillStore();
    const snapshots = Array.isArray(stored.snapshots) ? stored.snapshots : [];
    const snapshot = snapshots[snapshots.length - 1];
    if (Array.isArray(snapshot?.directPlayers) && snapshot.directPlayers.length) return;
    if (!snapshot?.clanKey || !snapshot?.weekKey) return;
    clanSkillRefreshing = true;
    try {
      const shared = await clanSkillsServerJson('/list', {clan_key:snapshot.clanKey, week_key:snapshot.weekKey});
      const sharedPlayers = Array.isArray(shared.players) ? shared.players : [];
      const nextSnapshots = snapshots.map(row => row === snapshot ? {...row, sharedPlayers, sharedUpdatedAt:Date.now()} : row);
      save({clanSkills:{...stored, snapshots:nextSnapshots}});
      renderClanSkills();
    } catch (error) {
      console.warn('[HK] clan skill list refresh failed', error);
    } finally {
      clanSkillRefreshing = false;
    }
  }

  function renderClanSkills() {
    if (!clanBox) return;
    const stored = clanSkillStore();
    const snapshots = Array.isArray(stored.snapshots) ? stored.snapshots : [];
    const snapshot = snapshots[snapshots.length - 1];
    const scanButton = `<button id="hk-clan-scan" class="hk-secondary" ${clanSkillScanning?'disabled':''}>${clanSkillScanning ? either('Считываю…','Reading…') : either('Считать навыки сейчас','Read skills now')}</button>`;
    if (!snapshot) {
      clanBox.innerHTML = `<h3>${either('Навыки клана','Clan skills')}</h3>${scanButton}<p class="hk-muted">${either('Автоматическое считывание выполняется один раз в день при первом открытии игры. Данные ещё не считаны.','Automatic reading runs once a day on the first game opening. No data has been read yet.')}</p>`;
      clanBox.querySelector('#hk-clan-scan').onclick = () => scanClanSkills(false);
      return;
    }
    const block = snapshot.blocks.find(row => row.id === stored.selectedBlockId) || snapshot.blocks[0];
    const line = block?.lines.find(row => row.id === stored.selectedLineId) || block?.lines[0];
    const ownLevels = Object.fromEntries(Object.entries(snapshot.lineState || {}).map(([id,row]) => [id,Math.max(0,Number(row?.playerLevel||0))]));
    const sharedPlayers = Array.isArray(snapshot.sharedPlayers) && snapshot.sharedPlayers.length ? snapshot.sharedPlayers : [{
      nickname:clean(playerDocument?.player?.nickname || playerDocument?.player?.name || licenseState.playerId || either('Текущий игрок','Current player')),
      levels:ownLevels,
      total:Object.values(ownLevels).reduce((sum,value)=>sum+Number(value||0),0)
    }];
    const players = sharedPlayers.map(row => ({
      name:clean(row.nickname || either('Неизвестный игрок','Unknown player')),
      level:Math.max(0, Number(row.levels?.[line?.id] || 0)),
      total:Math.max(0, Number(row.total || Object.values(row.levels || {}).reduce((sum,value)=>sum+Number(value||0),0)))
    })).sort((a,b) => b.level-a.level || b.total-a.total || a.name.localeCompare(b.name));
    const playerRows = players.length ? players.map((row,index) => `<div class="hk-clan-player"><b>${index+1}. ${escapeHtml(row.name)}</b><span>${Number(row.level).toLocaleString(locale())} ${either('ур.','lvl')}</span></div>`).join('') : `<p class="hk-muted">${either('Эту неделю пока не считал ни один участник.','No member has submitted a scan for this week yet.')}</p>`;
    const overallPlayers = sharedPlayers.map(row => ({
      name:clean(row.nickname || either('Неизвестный игрок','Unknown player')),
      total:Math.max(0, Number(row.total || Object.values(row.levels || {}).reduce((sum,value)=>sum+Number(value||0),0)))
    })).sort((a,b) => b.total-a.total || a.name.localeCompare(b.name));
    const overallRows = overallPlayers.map((row,index) => `<div class="hk-clan-player"><b>${index+1}. ${escapeHtml(row.name)}</b><span>${Number(row.total).toLocaleString(locale())} ${either('ур.','lvl')}</span></div>`).join('');
    const branches = snapshot.blocks.map((row,index) => `<button class="hk-clan-branch ${row.id===block?.id?'active':''}" data-clan-block="${escapeHtml(row.id)}" title="${escapeHtml(row.name)}" aria-label="${escapeHtml(row.name)}">${row.icon?`<img src="${escapeHtml(row.icon)}" alt="">`:`<b>${index+1}</b>`}</button>`).join('');
    const lines = (block?.lines || []).map((row,index) => `<button class="hk-clan-line ${row.id===line?.id?'active':''}" data-clan-line="${escapeHtml(row.id)}" title="${either('Уровень','Level')}: ${Number(snapshot.lineState?.[row.id]?.level||0).toLocaleString(locale())}" aria-label="${either('Подветка','Sub-branch')} ${index+1}">${row.icon?`<img src="${escapeHtml(row.icon)}" alt="">`:`<b>${index+1}</b>`}</button>`).join('');
    clanBox.innerHTML = `<div class="hk-clan-head"><div><h3>${either('Навыки клана','Clan skills')}</h3><small>${either('Последнее считывание','Last read')}: ${new Date(snapshot.scannedAt).toLocaleString(locale())}</small></div>${scanButton}</div><p class="hk-muted">${either('Общий вклад и накопленные уровни всех участников считываются напрямую из данных клана в игре и автоматически синхронизируются с сайтом. Автоматическое считывание выполняется один раз в день при первом открытии игры.','Total contribution and accumulated levels for every member are read directly from the clan data in the game and automatically synced with the website. Automatic reading runs once a day on the first game opening.')}</p><details class="hk-clan-overall" open><summary>${either('Общий вклад участников','Total member contribution')} <span>${overallPlayers.length}</span></summary><div class="hk-clan-players">${overallRows}</div></details><div class="hk-clan-branches">${branches}</div><div class="hk-clan-matrix"><aside>${lines}</aside><section><div class="hk-clan-line-summary"><span>${either('Общий уровень','Total level')}<b>${Number(snapshot.lineState?.[line?.id]?.level||0).toLocaleString(locale())}</b></span><span>${either('Твои уровни','Your levels')}<b>${Number(snapshot.lineState?.[line?.id]?.playerLevel||0).toLocaleString(locale())}</b></span><span>${either('Участников','Members')}<b>${players.length}</b></span></div><div class="hk-clan-players">${playerRows}</div></section></div>`;
    clanBox.querySelector('#hk-clan-scan').onclick = () => scanClanSkills(false);
    clanBox.querySelectorAll('[data-clan-block]').forEach(button => button.onclick = () => { const selected=snapshot.blocks.find(row=>row.id===button.dataset.clanBlock); save({clanSkills:{...stored,selectedBlockId:button.dataset.clanBlock,selectedLineId:selected?.lines[0]?.id||''}}); renderClanSkills(); });
    clanBox.querySelectorAll('[data-clan-line]').forEach(button => button.onclick = () => { save({clanSkills:{...stored,selectedLineId:button.dataset.clanLine}}); renderClanSkills(); });
  }

  function growthClonePriority(rows){ return (rows||[]).map(pair=>[Number(pair?.[0]),Number(pair?.[1])]); }
  function growthNormalizePriority(rows){
    if(!Array.isArray(rows)) return growthClonePriority(GROWTH_COPY_PRIORITY_DEFAULT);
    const allowed=new Set(GROWTH_COPY_PRIORITY_DEFAULT.map(pair=>`${pair[0]}/${pair[1]}`)), used=new Set(), out=[];
    for(const pair of rows){ const key=`${Number(pair?.[0])}/${Number(pair?.[1])}`; if(allowed.has(key)&&!used.has(key)){used.add(key);out.push([Number(pair[0]),Number(pair[1])]);} }
    return out;
  }

  function growthSettings() {
    const saved=load().growth||{};
    const pct=(value,fallback=100)=>Math.max(10,Math.min(100,Math.round(Number(value??fallback)/10)*10||fallback));
    const weight=value=>Math.max(1,Math.min(8,Math.floor(Number(value||1))||1));
    return {
      runPreparation:saved.runPreparation!==false,
      runGenerals:saved.runGenerals!==false,
      runHamsters:saved.runHamsters!==false,
      buyGeneralContracts:saved.buyGeneralContracts!==false,
      openAllBalls:saved.openAllBalls!==false,
      openAllBoxes:saved.openAllBoxes!==false,
      generalPitPercent:pct(saved.generalPitPercent ?? saved.pitPercent,100),
      generalMobsterPitWeight:weight(saved.generalMobsterPitWeight),
      generalLevelUpMode:saved.generalLevelUpMode==='fast10'?'fast10':'x1',
      capsPercent:pct(saved.capsPercent ?? saved.nutsPercent,100),
      mobsterPitWeight:weight(saved.mobsterPitWeight),
      copyPriorityEnabled:saved.copyPriorityEnabled!==false,
      excludeCurrentEventHamsters:saved.excludeCurrentEventHamsters===true,
      copyPriority:growthNormalizePriority(saved.copyPriority)
    };
  }

  function saveGrowthSettings(patch={}){
    const next={...growthSettings(),...patch};
    next.copyPriority=growthNormalizePriority(next.copyPriority);
    save({growth:next});
    return next;
  }

  function growthContainers(documentValue=growthState||hkStateStore.snapshot||playerDocument){
    const rows=[documentValue,documentValue?.player,documentValue?.result,documentValue?.data,documentValue?.data?.player].filter(value=>value&&typeof value==='object');
    return [...new Set(rows)];
  }
  function growthArray(key,documentValue=growthState||hkStateStore.snapshot||playerDocument){ for(const value of growthContainers(documentValue)) if(Array.isArray(value?.[key])) return value[key]; return []; }
  function growthResource(id,state=growthState||hkStateStore.snapshot||playerDocument){ return Math.max(0,Number(walletAmount(id,state)||0)); }
  function growthInventoryMap(state=growthState||hkStateStore.snapshot||playerDocument){ const map=new Map(); for(const row of growthArray('items',state)){const id=String(row?.item_id||row?.id||'');if(id)map.set(id,Math.max(0,Math.floor(Number(row?.quantity||0))));} return map; }
  function growthCapCost(cost){ return costParts(cost).filter(row=>row.kind==='currencies'&&row.id===GROWTH_HAMSTER_BUDGET_ID).reduce((sum,row)=>sum+Math.max(0,row.quantity),0); }
  function growthCostText(cost){
    const parts=costParts(cost).filter(row=>row.id&&row.quantity>0);
    return parts.length?parts.map(row=>`${Math.trunc(row.quantity).toLocaleString(locale())} ${paymentLabel(row.id)}`).join(' + '):either('без расхода','no cost');
  }
  function growthPitCost(cost){ return costParts(cost).filter(row=>row.kind==='items'&&row.id===GROWTH_GENERAL_BUDGET_ID).reduce((sum,row)=>sum+Math.max(0,row.quantity),0); }
  function growthSafeCost(cost){ return costParts(cost).every(row=>row.id&&row.quantity>0&&!['cur_prem','cur_hard'].includes(row.id)); }
  function growthCostOnlyUses(cost,allowed){const ids=new Set((allowed||[]).map(String)),parts=costParts(cost).filter(row=>row.id&&row.quantity>0);return parts.length>0&&parts.every(row=>ids.has(String(row.id)));}
  function growthHamsterCostSafe(cost){ return growthSafeCost(cost)&&growthCostOnlyUses(cost,[GROWTH_HAMSTER_BUDGET_ID]); }
  function growthHamsterLevelCostSafe(cost){ return growthHamsterCostSafe(cost)&&growthCapCost(cost)>0; }
  function growthGeneralCostSafe(cost){ return growthSafeCost(cost)&&growthCostOnlyUses(cost,[GROWTH_GENERAL_BUDGET_ID])&&growthPitCost(cost)>0; }
  function growthCanAfford(cost,state=growthState||hkStateStore.snapshot||playerDocument){ return growthSafeCost(cost)&&costParts(cost).every(row=>growthResource(row.id,state)>=row.quantity); }
  function growthHasClanCost(cost){const value=cost?.clan_currency_cost;return Array.isArray(value)?value.length>0:(value&&typeof value==='object'?Object.keys(value).length>0:!!value);}
  function growthGeneralFragmentCost(itemId){const id=String(itemId||'').toLowerCase();return id.includes('hgen')&&(id.includes('fragment')||id.includes('fragmet'));}
  function growthTotalPower(state=growthState||hkStateStore.snapshot||playerDocument){ return growthArray('playerFactions',state).reduce((sum,row)=>sum+Number(row?.power||0),0); }
  function growthHamsterById(state,id){return growthArray('playerHamsters',state).find(row=>String(row?.hamster_id||'')===String(id))||null;}
  function growthGeneralById(state,id){return growthArray('player_hamster_generals',state).find(row=>String(row?.hamster_id||'')===String(id))||null;}

  function growthStateFrom(value,reason='growth',full=true){
    if(value&&typeof value==='object') full?hkStateStore.replace(value,reason):hkStateStore.merge(value,reason);
    growthState=hkStateStore.snapshot||value||growthState||playerDocument;
    if(growthState) playerDocument=growthState;
    return growthState;
  }
  function growthResponseArray(data,key){ for(const value of growthContainers(data)) if(Array.isArray(value?.[key])) return value[key]; return null; }
  function growthMergeMutation(data,reason='growth-mutation'){
    if(data&&typeof data==='object') hkStateStore.merge(data,reason);
    growthState=hkStateStore.snapshot||growthState||data;
    if(growthState) playerDocument=growthState;
    return growthState;
  }
  function growthFindNamed(data,name,id){
    if(Array.isArray(data)){for(const value of data){const found=growthFindNamed(value,name,id);if(found)return found;}return null;}
    if(!data||typeof data!=='object')return null;
    if(Array.isArray(data[name])){const found=data[name].find(row=>String(row?.hamster_id||row?.id||'')===String(id));if(found)return found;}
    for(const value of Object.values(data)){if(value&&typeof value==='object'){const found=growthFindNamed(value,name,id);if(found)return found;}}
    return null;
  }
  function growthResponseHas(data,key){ return !!growthResponseArray(data,key); }
  function growthResponseHasResource(data,id){
    const wanted=String(id||'');
    for(const key of ['items','currencies']){
      const rows=growthResponseArray(data,key);
      if(Array.isArray(rows)&&rows.some(row=>String(row?.item_id||row?.currency_id||row?.id||'')===wanted))return true;
    }
    return false;
  }
  function growthCostSnapshot(cost,state){const map=new Map();for(const part of costParts(cost))if(part.id&&part.quantity>0)map.set(part.id,growthResource(part.id,state));return map;}
  function growthApplyCostFallback(data,cost,state,before=null){
    for(const part of costParts(cost)){
      if(!part.id||part.quantity<=0)continue;
      const serverReported=growthResponseHasResource(data,part.id), previous=before instanceof Map?before.get(part.id):null, current=growthResource(part.id,state);
      // A changed live server balance always wins. If a mutation echoes a stale
      // unchanged resource row, apply the known action cost once locally so the
      // next affordability check cannot loop on a phantom balance.
      if(serverReported&&Number.isFinite(previous)&&current<previous)continue;
      if(serverReported&&before==null)continue;
      const bucket=part.kind==='items'?'items':'currencies';
      debitWallet({[bucket]:[{id:part.id,quantity:part.quantity}]},1,state);
    }
  }
  function growthStateError(error){const status=Number(error?.httpStatus||0),text=String(error?.apiData?.description||error?.apiData?.message||error?.message||'').toLowerCase();return [400,409].includes(status)&&(['not enough','insufficient','currency','currencies','item','items','shard','balance','cost','mismatch','not available','cannot afford','already','invalid state'].some(x=>text.includes(x))||status===409);}

  function growthDisplayName(id){
    const key=String(id||''),meta=growthStaticHamsterMeta(key)||growthStaticItemMeta(key),nameKey=String(meta?.name||'');
    if(nameKey){const localized=gameText(nameKey);if(localized&&localized!==nameKey.replace(/_/g,' '))return localized;}
    return key.replace(/^item_hball_hgen_/,'').replace(/^item_h_ball_/,'').replace(/^item_hball_/,'').replace(/^item_hamsters_ball_/,'').replace(/^item_/,'').replace(/^cur_/,'').replace(/_/g,' ');
  }

  function growthAbortCheck(){if(hkRunner.signal?.aborted)throw new DOMException('Aborted','AbortError');}
  async function growthCheckpoint(step=''){await hkRunner.waitIfPaused();growthAbortCheck();if(step)hkRunner.setStep(step);}

  async function growthStaticJson(path){
    const request=nativeNetworkFetch||window.fetch.bind(window);
    const {response,text}=await gameFetchText(request,`${GROWTH_STATIC_API}/${path}`,{cache:'no-store'},15000);
    if(!response.ok)throw new Error(`${path}: HTTP ${response.status}`);
    try{return JSON.parse(text);}catch(_){throw new Error(`${path}: invalid JSON`);}
  }
  async function growthEnsureStatic(){
    const jobs=[];
    if(!growthItemsDocument) jobs.push(growthStaticJson('items').then(data=>{growthItemsDocument=Array.isArray(data)?data:(data?.items||[]);if(!itemCatalogDocument&&growthItemsDocument.length)itemCatalogDocument=growthItemsDocument;}).catch(async()=>{const data=await apiJson('/items','GET');growthItemsDocument=Array.isArray(data)?data:(data?.items||[]);if(!itemCatalogDocument&&growthItemsDocument.length)itemCatalogDocument=growthItemsDocument;}));
    if(!growthHamstersStaticDocument) jobs.push(growthStaticJson('hamsters/view').then(data=>growthHamstersStaticDocument=data));
    if(!localizationDocument) jobs.push(apiJson(`/localization/${language}`,'GET').then(data=>localizationDocument=data).catch(()=>null));
    if(jobs.length) await Promise.allSettled(jobs);
  }
  function growthStaticHamsters(){return Array.isArray(growthHamstersStaticDocument?.hamsters)?growthHamstersStaticDocument.hamsters:[];}
  function growthStaticHamsterMeta(id){return growthStaticHamsters().find(row=>String(row?.id||'')===String(id))||null;}
  function growthStaticItemMeta(id){return (growthItemsDocument||[]).find(row=>String(row?.id||'')===String(id))||null;}

  async function growthLoadLive({force=false,loadShop=true,loadConfig=false,silent=true}={}){
    if(growthLoadPromise)return growthLoadPromise;
    if(!force&&growthState&&Date.now()-growthLastLoadedAt<8000)return growthState;
    const task=(async()=>{
      growthMenuLoading=true;renderGrowth();
      try{
        // /player/me is the only mandatory request. Static/shop/event config are
        // enrichments: their temporary failure must not make the whole Growth
        // screen look disconnected or block a safe level-up plan.
        const playerPromise=apiJson('/player/me','POST');
        const staticPromise=growthEnsureStatic().catch(error=>{recordDiagnostic('growth-static-error',{error:error?.message||error});return null;});
        const shopPromise=loadShop?apiJson('/shop/view','GET').catch(error=>{recordDiagnostic('growth-shop-error',{error:error?.message||error});return null;}):Promise.resolve(null);
        const configPromise=loadConfig?apiJson('/client_config','GET').catch(error=>{recordDiagnostic('growth-config-error',{error:error?.message||error});return null;}):Promise.resolve(null);
        const player=await playerPromise;
        growthStateFrom(player,'growth-live',true);
        const [,shop,cfg]=await Promise.all([staticPromise,shopPromise,configPromise]);
        if(shop)growthShopDocument=shop;
        if(cfg)growthClientConfigDocument=cfg;
        growthLastLoadedAt=Date.now();
        if(!silent)log(either('Данные развития обновлены автоматически','Growth data refreshed automatically'),'ok');
        renderGrowth();return growthState;
      }catch(error){log(`${either('Ошибка данных развития','Growth data error')}: ${error?.message||error}`,'bad');return null;}
      finally{growthMenuLoading=false;growthLoadPromise=null;renderGrowth();}
    })();
    growthLoadPromise=task;return task;
  }
  function growthAutoOpen(page){
    const settings=growthSettings();
    const needsConfig=page==='growth-hamsters'&&settings.excludeCurrentEventHamsters;
    void growthLoadLive({force:true,loadShop:true,loadConfig:needsConfig,silent:true});
  }
  async function growthRecoverState(reason='state-mismatch'){
    log(either('Состояние изменилось — автоматически перечитываю аккаунт…','State changed — automatically refreshing the account…'),'warn');
    const fresh=await growthLoadLive({force:true,loadShop:true,loadConfig:false,silent:true});
    recordDiagnostic('growth-state-recovery',{reason,ok:!!fresh});
    return fresh||growthState;
  }

  function growthHamsterMaxLevel(hamster){return Math.max(GROWTH_HAMSTER_BASE_MAX_LEVEL,GROWTH_HAMSTER_BASE_MAX_LEVEL+Math.max(0,Math.floor(Number(hamster?.add_bonus_max_level||0))));}
  function growthAccountHamsterMaxLevel(state=growthState){let max=GROWTH_HAMSTER_BASE_MAX_LEVEL;for(const hamster of growthArray('playerHamsters',state))max=Math.max(max,growthHamsterMaxLevel(hamster));return max;}
  function growthCopyPair(hamster){return [Number(hamster?.quantity||0),Number(hamster?.nextUpgrade?.shardsQuantity||0)];}
  function growthCopyCandidates(state,priority){const index=new Map(priority.map((pair,i)=>[`${pair[0]}/${pair[1]}`,i]));return growthArray('playerHamsters',state).filter(h=>{const pair=growthCopyPair(h);return h?.hamster_id&&h?.nextUpgrade&&index.has(`${pair[0]}/${pair[1]}`);}).sort((a,b)=>index.get(growthCopyPair(a).join('/'))-index.get(growthCopyPair(b).join('/'))||String(a.hamster_id).localeCompare(String(b.hamster_id)));}

  function growthSummaryMarkup(){
    const state=growthState||hkStateStore.snapshot||playerDocument, hamsters=growthArray('playerHamsters',state), generals=growthArray('player_hamster_generals',state), settings=growthSettings();
    const caps=growthResource(GROWTH_HAMSTER_BUDGET_ID,state),nuts=growthResource('cur_nut',state),pit=growthResource(GROWTH_GENERAL_BUDGET_ID,state),max=growthAccountHamsterMaxLevel(state),copyTargets=growthCopyCandidates(state,settings.copyPriority).filter(h=>{const [owned,required]=growthCopyPair(h);return required>owned;}).length;
    const live=growthMenuLoading?either('Считываю…','Loading…'):(growthLastLoadedAt?new Date(growthLastLoadedAt).toLocaleTimeString(locale(),{hour:'2-digit',minute:'2-digit',second:'2-digit'}):either('ожидание','waiting'));
    return `<div class="hk-growth-live"><span>● ${either('LIVE','LIVE')} · ${escapeHtml(live)}</span><small>${either('Состояние обновляется автоматически при открытии вкладки и перед запуском.','State refreshes automatically when opening a tab and before a run.')}</small></div><div class="hk-growth-stats"><div><small>${either('Хомяки','Hamsters')}</small><b>${hamsters.length.toLocaleString(locale())}</b></div><div><small>${either('Генералы','Generals')}</small><b>${generals.length.toLocaleString(locale())}</b></div><div><small>${either('Крышки','Caps')}</small><b>${Math.round(caps).toLocaleString(locale())}</b></div><div><small>${either('Орехи','Nuts')}</small><b>${Math.round(nuts).toLocaleString(locale())}</b></div><div><small>${either('Pit Tokens','Pit Tokens')}</small><b>${Math.round(pit).toLocaleString(locale())}</b></div><div><small>${either('AUTO max ур.','AUTO max lvl')}</small><b>${max}</b></div><div><small>${either('Целей копий','Copy targets')}</small><b>${copyTargets}</b></div></div>`;
  }

  function growthPriorityMarkup(settings=growthSettings()){
    if(!settings.copyPriority.length)return `<div class="hk-muted">${either('Приоритет пуст. Нажмите «Сбросить».','Priority is empty. Press Reset.')}</div>`;
    return settings.copyPriority.map((pair,index)=>`<div class="hk-growth-priority" data-growth-priority-index="${index}"><b>${pair[0]} / ${pair[1]}</b><span>${either('копий / нужно для редкости','owned / required for rarity')}</span><div><button class="hk-secondary" data-growth-priority-move="up" ${index===0?'disabled':''}>↑</button><button class="hk-secondary" data-growth-priority-move="down" ${index===settings.copyPriority.length-1?'disabled':''}>↓</button><button class="hk-danger" data-growth-priority-remove>−</button></div></div>`).join('');
  }
  function growthPlanText(settings=growthSettings()){
    const prep=settings.runPreparation?[settings.buyGeneralContracts?either('контракты','contracts'):'',settings.openAllBalls?either('шары','balls'):'',settings.openAllBoxes?either('коробки','boxes'):''].filter(Boolean).join(' → '):either('выкл.','off');
    const general=settings.runGenerals?`${settings.generalPitPercent}% Pit · ${settings.generalLevelUpMode==='fast10'?'×10':'×1'} · ${either('вес Ямы','Pit weight')} ${settings.generalMobsterPitWeight===1?'—':`×${settings.generalMobsterPitWeight}`}`:either('выкл.','off');
    const hamster=settings.runHamsters?`${settings.capsPercent}% ${either('Крышек','Caps')} · ${settings.copyPriorityEnabled?either('копии → редкость → уровни','copies → rarity → levels'):either('редкость → уровни','rarity → levels')} · ${either('цена из live costs','cost from live costs')} · ${either('вес Ямы','Pit weight')} ${settings.mobsterPitWeight===1?'—':`×${settings.mobsterPitWeight}`}`:either('выкл.','off');
    return `<div class="hk-growth-plan"><b>${either('План выполнения','Execution plan')}</b><span>1. ${either('Подготовка','Preparation')}: ${escapeHtml(prep)}</span><span>2. ${either('Генералы','Generals')}: ${escapeHtml(general)}</span><span>3. ${either('Хомяки','Hamsters')}: ${escapeHtml(hamster)}</span><small>${either('Перед стартом состояние считывается заново. После каждого ответа API общий State Store обновляется автоматически.','State is read again before start. Every API response automatically updates the shared State Store.')}</small></div>`;
  }

  function renderGrowth(){
    if(!root)return;
    const settings=growthSettings();
    root.querySelectorAll('[data-growth-summary]').forEach(box=>box.innerHTML=growthSummaryMarkup());
    const setCheck=(id,value)=>{const el=root.querySelector(id);if(el)el.checked=!!value;};
    const setValue=(id,value)=>{const el=root.querySelector(id);if(el)el.value=String(value);};
    setCheck('#hk-growth-run-prep',settings.runPreparation);setCheck('#hk-growth-run-generals',settings.runGenerals);setCheck('#hk-growth-run-hamsters',settings.runHamsters);
    setCheck('#hk-growth-contracts',settings.buyGeneralContracts);setCheck('#hk-growth-balls',settings.openAllBalls);setCheck('#hk-growth-boxes',settings.openAllBoxes);
    setValue('#hk-growth-pit-percent',settings.generalPitPercent);setValue('#hk-growth-general-mode',settings.generalLevelUpMode);setValue('#hk-growth-general-weight',settings.generalMobsterPitWeight);
    setValue('#hk-growth-caps-percent',settings.capsPercent);setValue('#hk-growth-hamster-weight',settings.mobsterPitWeight);setCheck('#hk-growth-copy-enabled',settings.copyPriorityEnabled);setCheck('#hk-growth-exclude-event',settings.excludeCurrentEventHamsters);
    const priority=root.querySelector('#hk-growth-copy-priority');if(priority)priority.innerHTML=growthPriorityMarkup(settings);
    root.querySelectorAll('[data-growth-plan]').forEach(box=>box.innerHTML=growthPlanText(settings));
    root.querySelectorAll('[data-growth-action]').forEach(button=>button.disabled=growthBusy||growthMenuLoading||hkRunner.running);
    root.querySelectorAll('.hk-growth-option input,.hk-growth-option select,.hk-growth-check input').forEach(input=>input.disabled=growthBusy||hkRunner.running);
  }

  function growthReadSettingsFromUi(){
    const base=growthSettings(),check=id=>root?.querySelector(id)?.checked,value=id=>root?.querySelector(id)?.value;
    return saveGrowthSettings({
      runPreparation:check('#hk-growth-run-prep')??base.runPreparation,runGenerals:check('#hk-growth-run-generals')??base.runGenerals,runHamsters:check('#hk-growth-run-hamsters')??base.runHamsters,
      buyGeneralContracts:check('#hk-growth-contracts')??base.buyGeneralContracts,openAllBalls:check('#hk-growth-balls')??base.openAllBalls,openAllBoxes:check('#hk-growth-boxes')??base.openAllBoxes,
      generalPitPercent:Number(value('#hk-growth-pit-percent')||base.generalPitPercent),generalLevelUpMode:value('#hk-growth-general-mode')==='fast10'?'fast10':'x1',generalMobsterPitWeight:Number(value('#hk-growth-general-weight')||base.generalMobsterPitWeight),
      capsPercent:Number(value('#hk-growth-caps-percent')||base.capsPercent),mobsterPitWeight:Number(value('#hk-growth-hamster-weight')||base.mobsterPitWeight),copyPriorityEnabled:check('#hk-growth-copy-enabled')??base.copyPriorityEnabled,excludeCurrentEventHamsters:check('#hk-growth-exclude-event')??base.excludeCurrentEventHamsters
    });
  }

  function growthGeneralContractGroups(shop){
    const rows=(shop?.shop_lots||[]).filter(Boolean),byId=new Map(rows.map(row=>[String(row?.id||''),row])),groups=[];
    for(const lot of rows){
      const id=String(lot?.id||''),view=lot?.lot_view||{};
      if(!id.startsWith('mf_shoplot_hgen_hball_')||String(view?.type||'').toLowerCase()!=='default'||lot?.is_ad===true||lot?.external_cost)continue;
      const reward=(view.content_view||[]).find(row=>row?.type==='item'&&String(row?.id||'').startsWith(GROWTH_GENERAL_BALL_PREFIX));if(!reward)continue;
      const safe=row=>{const cost=row?.cost||{},currencies=Array.isArray(cost.currencies)?cost.currencies:[],items=Array.isArray(cost.items)?cost.items:[];return !row?.external_cost&&!row?.is_ad&&!growthHasClanCost(cost)&&currencies.length===0&&items.length>0&&items.every(part=>growthGeneralFragmentCost(part?.id));};
      if(!safe(lot))continue;
      const bundles=[[Math.max(1,Math.floor(Number(reward.quantity||1))),lot]];
      for(const multiplierId of (Array.isArray(view.multiplier_lots)?view.multiplier_lots:[])){const multiplier=byId.get(String(multiplierId||''));if(!multiplier||!safe(multiplier))continue;const quantity=Math.floor(Number(multiplier?.lot_view?.quantity||0));if(quantity>0)bundles.push([quantity,multiplier]);}
      bundles.sort((a,b)=>b[0]-a[0]);groups.push({rewardItem:String(reward.id),baseLot:lot,bundles});
    }
    groups.sort((a,b)=>a.rewardItem.localeCompare(b.rewardItem));return groups;
  }

  async function growthBuyAllGeneralContractsCore(state){
    const shop=growthShopDocument||await apiJson('/shop/view','GET');growthShopDocument=shop;
    const groups=growthGeneralContractGroups(shop);if(!groups.length){log(either('Контрактов Генералов за фрагменты сейчас нет','No fragment-only General contracts are currently available'),'info');return state;}
    let totalBuys=0;
    for(const group of groups){
      let boughtContracts=0;
      while(totalBuys<1000){
        await growthCheckpoint(either('Покупка контрактов Генералов','Buying General contracts'));
        let chosen=null;for(const [quantity,lot] of group.bundles){if(growthCanAfford(lot?.cost||{},state)){chosen=[quantity,lot];break;}}if(!chosen)break;
        const [quantity,lot]=chosen,view=lot?.lot_view||{};
        try{
          const costBefore=growthCostSnapshot(lot.cost||{},state),data=await apiJson('/shop/buy','POST',{shop_lot_id:String(lot.id||''),payment_type:'INTERNAL',lotName:gameText(view.name||String(lot.id||'')),lotDescription:gameText(view.desc||'')},true,0);
          state=growthMergeMutation(data,'growth-general-contract');growthApplyCostFallback(data,lot.cost||{},state,costBefore);
          boughtContracts+=quantity;totalBuys++;log(`${growthDisplayName(group.rewardItem)} +${quantity}`,'ok');await sleep(250);
        }catch(error){if(error?.name==='AbortError')throw error;if(growthStateError(error))state=await growthRecoverState('general-contract');else log(`${String(lot.id||'')}: ${error.message}`,'warn');break;}
      }
      if(boughtContracts>0)log(`${growthDisplayName(group.rewardItem)} · ${boughtContracts.toLocaleString(locale())}`,'ok');
    }
    return state;
  }

  function growthLootboxDefinitions(kind){
    return new Set((growthItemsDocument||[]).filter(row=>row?.type==='lootbox'&&row?.id).flatMap(row=>{const id=String(row.id).toLowerCase();if(id.includes('passive_income'))return[];const ball=id.startsWith('item_h_ball_')||id.startsWith('item_hball_')||id.startsWith('item_hamsters_ball_');if(kind==='balls')return ball?[String(row.id)]:[];return !ball&&/(^|_)(lootbox|box|chest)(_|$)/.test(id)?[String(row.id)]:[];}));
  }
  async function growthOpenLootboxFamilyCore(state,kind){
    await growthEnsureStatic();const defs=growthLootboxDefinitions(kind);if(!defs.size)return state;
    let inventory=growthInventoryMap(state),blocked=new Set(),retried=new Set();
    if(![...inventory].some(([id,qty])=>qty>0&&defs.has(id))){log(kind==='balls'?either('Шаров для открытия нет','No balls to open'):either('Коробок для открытия нет','No boxes to open'),'info');return state;}
    for(let round=0;round<100;round++){
      const candidates=[...inventory.entries()].filter(([id,qty])=>qty>0&&defs.has(id)&&!blocked.has(id)).sort((a,b)=>a[0].localeCompare(b[0]));if(!candidates.length)break;let didAny=false;
      for(const [itemId] of candidates){
        while(Number(inventory.get(itemId)||0)>0&&!blocked.has(itemId)){
          await growthCheckpoint(`${kind==='balls'?either('Шары','Balls'):either('Коробки','Boxes')} · ${growthDisplayName(itemId)}`);
          const remaining=Math.floor(Number(inventory.get(itemId)||0)),amount=Math.min(remaining,GROWTH_LOOTBOX_BATCH);
          try{
            const data=await apiJson(`/player/boxes/open?item_id=${encodeURIComponent(itemId)}&quantity=${amount}`,'POST',null,true,0),hasItems=growthResponseHas(data,'items');
            state=growthMergeMutation(data,`growth-${kind}`);didAny=true;
            if(hasItems){
              inventory=growthInventoryMap(state);
              const after=Math.floor(Number(inventory.get(itemId)||0));
              if(after>=remaining){
                if(!retried.has(itemId)){
                  retried.add(itemId);
                  state=await growthRecoverState(`lootbox-${kind}-no-progress`);
                  inventory=growthInventoryMap(state);
                  continue;
                }
                blocked.add(itemId);
                log(`${growthDisplayName(itemId)}: ${either('сервер не подтвердил уменьшение остатка — остановлено','server did not confirm inventory decrease — stopped')}`,'warn');
                break;
              }
              retried.delete(itemId);
            }else{
              const left=Math.max(0,remaining-amount);inventory.set(itemId,left);
              const row=growthArray('items',state).find(x=>String(x?.item_id||x?.id||'')===itemId);if(row)row.quantity=left;
              retried.delete(itemId);
            }
            log(`${growthDisplayName(itemId)} ×${amount}`,'ok');await sleep(350);
          }catch(error){if(error?.name==='AbortError')throw error;log(`${growthDisplayName(itemId)} ×${amount}: ${error.message}`,'warn');if(!retried.has(itemId)){retried.add(itemId);state=await growthRecoverState(`lootbox-${kind}`);inventory=growthInventoryMap(state);if(Number(inventory.get(itemId)||0)<=0)break;continue;}blocked.add(itemId);break;}
        }
      }
      if(!didAny&&candidates.every(([id])=>blocked.has(id)))break;
    }
    return state;
  }

  async function growthRefreshEntity(id,state,kind='hamster'){
    try{const data=await apiJson('/player/hamster/lvlUp/view','POST',{hamster_id:id});state=growthMergeMutation(data,'growth-entity-view');return kind==='general'?growthGeneralById(state,id):growthHamsterById(state,id);}catch(_){return null;}
  }

  function growthGeneralWeightedTarget(id){const meta=growthStaticHamsterMeta(id);if(!meta||meta.is_general!==true)return false;const faction=String(meta.faction_id||'').toLowerCase(),classId=String(meta.class_id||'').toLowerCase();return faction==='idol'||faction==='crypto'||classId==='pitgeneral';}
  function growthHamsterWeightedTarget(id){const meta=growthStaticHamsterMeta(id);if(meta){if(meta.is_general===true)return false;return ['idol','crypto','pit_helper'].includes(String(meta.faction_id||'').toLowerCase());}const hid=String(id||'').toLowerCase();return hid.startsWith('idol_')||hid.startsWith('pit_helper_')||hid.startsWith('crypto_')||hid.includes('_crypto_');}

  const GROWTH_NO_PROGRESS_LIMIT = 2;

  function growthBestGeneral(state,blocked,budget,mode='x1',weightValue=1){
    let best=null,bestScore=0;const selectedWeight=Math.max(1,Math.min(8,Math.floor(Number(weightValue||1))||1));
    for(const general of growthArray('player_hamster_generals',state)){
      const id=String(general?.hamster_id||'');if(!id||blocked.has(id)||!general?.nextLevelUp)continue;
      let actionType=null,preview=general.nextLevelUp,costs=preview.costs||{};
      if(mode==='fast10'&&general?.nearest10LevelUp){const fast=general.nearest10LevelUp.costs||{};if(growthGeneralCostSafe(fast)&&growthCanAfford(fast,state)&&budget.spent+growthPitCost(fast)<=budget.limit){actionType='fast10';preview=general.nearest10LevelUp;costs=fast;}}
      const pit=growthPitCost(costs);if(!growthGeneralCostSafe(costs)||pit<=0||!growthCanAfford(costs,state)||budget.spent+pit>budget.limit)continue;
      const gain=Number(preview.diff||0);if(gain<=0)continue;const efficiency=gain/pit,weight=selectedWeight>1&&growthGeneralWeightedTarget(id)?selectedWeight:1,score=efficiency*weight;
      if(score>bestScore){bestScore=score;best={id,pit,gain,efficiency,score,weight,costs,actionType,level:Number(general.level||0)};}
    }
    return best;
  }
  async function growthRunGeneralsCore(state,settings){
    const startPit=growthResource(GROWTH_GENERAL_BUDGET_ID,state),limit=Math.floor(startPit*settings.generalPitPercent/100),budget={limit,spent:0},blocked=new Set();let safety=0,noProgress=0;
    log(`${either('Бюджет Генералов','General budget')}: ${settings.generalPitPercent}% · ${limit.toLocaleString(locale())}/${startPit.toLocaleString(locale())}`,'info');
    while(budget.spent<budget.limit&&safety++<GROWTH_ACTION_SAFETY){
      await growthCheckpoint(either('Оптимизация Генералов','Optimizing Generals'));const best=growthBestGeneral(state,blocked,budget,settings.generalLevelUpMode,settings.generalMobsterPitWeight);if(!best)break;
      try{
        const before=Number(growthGeneralById(state,best.id)?.level??best.level??0),payload={hamster_id:best.id};if(best.actionType)payload.fast_type=best.actionType;
        const costBefore=growthCostSnapshot(best.costs,state),data=await apiJson('/player/hamster/lvlUp','POST',payload,true,0),updated=growthFindNamed(data,'player_hamster_generals',best.id);state=growthMergeMutation(data,'growth-general-level');growthApplyCostFallback(data,best.costs,state,costBefore);budget.spent+=best.pit;
        let live=growthGeneralById(state,best.id);if(!updated||!updated.nextLevelUp){await growthRefreshEntity(best.id,state,'general');state=growthState||state;live=growthGeneralById(state,best.id);}
        const after=Number(live?.level??before);if(after<=before){noProgress+=1;recordDiagnostic('growth-general-no-progress',{id:best.id,before,after,count:noProgress});if(noProgress>=GROWTH_NO_PROGRESS_LIMIT){blocked.add(best.id);break;}}else noProgress=0;const weighted=best.weight>1?` · ×${best.weight}`:'';log(`${growthDisplayName(best.id)} · Lv ${before}→${after} · ${growthCostText(best.costs)} · Power +${best.gain.toLocaleString(locale())} · Eff ${best.efficiency.toFixed(3)}${weighted}`,'ok');await sleep(300);
      }catch(error){if(error?.name==='AbortError')throw error;if(growthStateError(error)){state=await growthRecoverState('general-level');blocked.clear();continue;}log(`${growthDisplayName(best.id)}: ${error.message}`,'warn');blocked.add(best.id);}
    }
    log(`${either('Pit Tokens потрачено','Pit Tokens spent')}: ${budget.spent.toLocaleString(locale())}/${limit.toLocaleString(locale())}`,'ok');return state;
  }

  function growthCopyFamily(id,meta){const group=String(meta?.meta?.group||'').toLowerCase(),faction=String(meta?.faction_id||'').toLowerCase(),vendor=String(meta?.meta?.vendor_page||'').toLowerCase(),hid=String(id||'');if(faction==='crypto'||vendor==='bitquest'||hid.startsWith('crypto_')||hid.includes('_crypto_'))return'crypto';if(group==='1base')return'base';if(group==='2pit')return faction==='pit_helper'?'pit_helper':'pit';if(group==='3event')return'event';if(group==='4influencer')return faction==='building_helper'?'building_helper':'influencer';if(group==='5fair')return'fair';if(group==='6beasthelper')return'beasthelper';if(faction==='idol')return'idol';if(faction==='pit_helper')return'pit_helper';if(faction==='building_helper')return'building_helper';if(['beasthelper','beast_helper'].includes(faction))return'beasthelper';if(hid.startsWith('event_')||vendor==='specialshop')return'event';if(hid.startsWith('pit_helper_'))return'pit_helper';if(hid.startsWith('building_helper_'))return'building_helper';if(hid.startsWith('idol_'))return'idol';if(hid.startsWith('beasthelper_')||hid.startsWith('beast_helper_'))return'beasthelper';return null;}
  function growthCopyRarity(meta,id){const value=Number(meta?.rarity);if(Number.isFinite(value))return value;const match=String(id||'').match(/_r([1-4])(?:_|$)/);return match?Math.max(0,Number(match[1])-1):null;}
  function growthCopyLotId(id,meta){const family=growthCopyFamily(id,meta),rarity=growthCopyRarity(meta,id);if(!family||rarity===null)return null;const tier=rarity>=3?'t2_splus_h_ball':rarity===2?'t1_s_h_ball':'t1_h_ball';return `mf_shoplot_hamsters_collection_copy_dust_${tier}_${family}`;}
  function growthWalkStrings(value,visit,depth=0){if(depth>9||value==null)return;if(typeof value==='string'){visit(value);return;}if(Array.isArray(value)){for(const item of value)growthWalkStrings(item,visit,depth+1);return;}if(typeof value==='object')for(const item of Object.values(value))growthWalkStrings(item,visit,depth+1);}
  function growthExactIds(value,known,out){growthWalkStrings(value,text=>{if(known.has(text))out.add(text);});}
  async function growthDiscoverCurrentEventHamsters(){
    const shop=growthShopDocument||await apiJson('/shop/view','GET');growthShopDocument=shop;const cfg=growthClientConfigDocument||await apiJson('/client_config','GET');growthClientConfigDocument=cfg;
    const tabs=Array.isArray(cfg?.event?.tabs)?cfg.event.tabs:[];let activeKey=String(tabs.find(tab=>String(tab?.type||'')==='shop'&&tab?.tab)?.tab||'');if(!activeKey){const fallback=tabs.find(tab=>String(tab?.type||'')==='quests'&&String(tab?.zone||'').startsWith('event_'));activeKey=String(fallback?.zone||'');}if(!activeKey)return{activeKey:'',ids:new Set()};
    const metaRows=growthStaticHamsters(),meta=new Map(metaRows.map(h=>[String(h?.id||''),h])),known=new Set(meta.keys()),ids=new Set(),tokens=new Set([activeKey]),prefix=`${activeKey}_`;
    for(const [id,row] of meta)if(growthCopyFamily(id,row)==='event'&&(id===activeKey||id.startsWith(prefix)))ids.add(id);
    for(const row of tabs.filter(tab=>String(tab?.tab||'')===activeKey||String(tab?.zone||'')===activeKey)){growthExactIds(row,known,ids);growthWalkStrings(row,text=>{if(text===activeKey||text.startsWith(prefix))tokens.add(text);});}
    for(const lot of shop?.shop_lots||[]){if(String(lot?.lot_view?.tab||'')!==activeKey)continue;growthExactIds(lot,known,ids);}
    for(const [id,row] of meta){if(growthCopyFamily(id,row)!=='event')continue;let matched=false;growthWalkStrings(row,text=>{if(tokens.has(text))matched=true;});if(matched)ids.add(id);}
    return{activeKey,ids};
  }

  function growthCombinedCost(...costs){const maps={items:new Map(),currencies:new Map()};for(const cost of costs)for(const kind of ['items','currencies'])for(const row of cost?.[kind]||[]){if(!row?.id)continue;maps[kind].set(String(row.id),Number(maps[kind].get(String(row.id))||0)+Number(row.quantity||0));}return{items:[...maps.items].map(([id,quantity])=>({id,quantity})),currencies:[...maps.currencies].map(([id,quantity])=>({id,quantity}))};}
  function growthMultiplyCost(cost,multiplier){const out={items:[],currencies:[]};for(const kind of ['items','currencies'])for(const row of cost?.[kind]||[]){const qty=Number(row?.quantity||0)*Math.max(0,Number(multiplier||0));if(row?.id&&qty>0)out[kind].push({id:row.id,quantity:qty});}return out;}
  function growthBudgetAllows(budget,cost){return budget.spent+growthCapCost(cost)<=budget.limit;}

  async function growthRunPriorityCopiesCore(state,settings,budget){
    await growthEnsureStatic();const shop=growthShopDocument||await apiJson('/shop/view','GET');growthShopDocument=shop;const lots=new Map((shop?.shop_lots||[]).filter(Boolean).map(lot=>[String(lot.id||''),lot]));
    const excluded=new Set();if(settings.excludeCurrentEventHamsters){try{const event=await growthDiscoverCurrentEventHamsters();for(const id of event.ids)excluded.add(id);log(excluded.size?`${either('Исключены хомяки текущего события','Current-event Hamsters excluded')}: ${excluded.size}`:either('Точные хомяки текущего события не найдены — ничего не исключено','No exact current-event Hamsters found — nothing excluded'),excluded.size?'info':'warn');}catch(error){log(`${either('Не удалось определить хомяков события','Could not identify event Hamsters')}: ${error.message}`,'warn');}}
    const allowed=new Set(settings.copyPriority.map(pair=>`${pair[0]}/${pair[1]}`));
    for(const original of growthCopyCandidates(state,settings.copyPriority)){
      await growthCheckpoint(either('Приоритет копий Хомяков','Hamster Copy Priority'));const id=String(original.hamster_id);if(excluded.has(id))continue;let hamster=growthHamsterById(state,id);if(!hamster)continue;const [owned,required]=growthCopyPair(hamster),key=`${owned}/${required}`;if(!allowed.has(key)||required<=owned)continue;
      const missing=required-owned,upgradeCost=hamster.nextUpgrade?.costs||{},meta=growthStaticHamsterMeta(id)||{},lotId=growthCopyLotId(id,meta),lot=lots.get(lotId);if(!lot)continue;const view=lot.lot_view||{};if(view.type!=='hamsters_collection'||lot.is_ad===true||lot.external_cost)continue;const copyCost=lot.cost||{};if((copyCost.currencies||[]).some(row=>['cur_prem','cur_hard'].includes(String(row?.id||'')))||!growthHamsterCostSafe(copyCost))continue;
      const full=growthCombinedCost(growthMultiplyCost(copyCost,missing),upgradeCost);if(!growthHamsterCostSafe(full)||!growthCanAfford(full,state)||!growthBudgetAllows(budget,full))continue;
      let failed=false;
      for(let number=0;number<missing;number++){
        await growthCheckpoint(`${growthDisplayName(id)} · ${number+1}/${missing}`);if(!growthCanAfford(copyCost,state)){failed=true;break;}
        try{const before=Number(growthHamsterById(state,id)?.quantity||0),costBefore=growthCostSnapshot(copyCost,state),data=await apiJson('/shop/buy','POST',{shop_lot_id:lotId,payment_type:'INTERNAL',collection_entity_id:id,collection_count:1,lotName:'!!!',lotDescription:'!!!'},true,0);state=growthMergeMutation(data,'growth-copy-buy');growthApplyCostFallback(data,copyCost,state,costBefore);budget.spent+=growthCapCost(copyCost);const live=growthHamsterById(state,id);if(live&&Number(live.quantity||0)<=before)live.quantity=before+1;log(`${growthDisplayName(id)} · ${before}/${required} → ${Number(growthHamsterById(state,id)?.quantity||before+1)}/${required} · ${growthCostText(copyCost)}`,'ok');await sleep(250);}catch(error){if(error?.name==='AbortError')throw error;if(growthStateError(error))state=await growthRecoverState('copy-buy');else log(`${growthDisplayName(id)}: ${error.message}`,'warn');failed=true;break;}
      }
      if(failed)continue;
      hamster=growthHamsterById(state,id);const liveReq=Number(hamster?.nextUpgrade?.shardsQuantity||0),liveQty=Number(hamster?.quantity||0);if(liveQty<liveReq||liveReq!==required)continue;const cost=hamster?.nextUpgrade?.costs||upgradeCost;if(!growthHamsterCostSafe(cost)||!growthCanAfford(cost,state)||!growthBudgetAllows(budget,cost))continue;
      try{const costBefore=growthCostSnapshot(cost,state),data=await apiJson('/player/hamster/upgrade','POST',{hamster_id:id},true,0),updated=growthFindNamed(data,'playerHamsters',id);state=growthMergeMutation(data,'growth-copy-upgrade');growthApplyCostFallback(data,cost,state,costBefore);budget.spent+=growthCapCost(cost);if(!updated||!updated.nextUpgrade){await growthRefreshEntity(id,state,'hamster');state=growthState||state;}log(`${growthDisplayName(id)} · ${either('редкость повышена','rarity upgraded')} · ${growthCostText(cost)}`,'ok');await sleep(350);}catch(error){if(error?.name==='AbortError')throw error;if(growthStateError(error))state=await growthRecoverState('copy-upgrade');else log(`${growthDisplayName(id)}: ${error.message}`,'warn');}
    }
    return state;
  }

  function growthRarityCandidate(state,blocked,budget){for(const hamster of growthArray('playerHamsters',state)){const id=String(hamster?.hamster_id||'');if(!id||blocked.has(id)||!hamster?.nextUpgrade)continue;const required=Number(hamster.nextUpgrade.shardsQuantity||0),owned=Number(hamster.quantity||0),cost=hamster.nextUpgrade.costs||{};if(owned<required||!growthHamsterCostSafe(cost)||!growthCanAfford(cost,state)||!growthBudgetAllows(budget,cost))continue;return{id,cost,required};}return null;}
  async function growthRunRarityCore(state,budget){const blocked=new Set();let safety=0;while(safety++<GROWTH_ACTION_SAFETY){await growthCheckpoint(either('Повышение редкости Хомяков','Hamster rarity upgrades'));const target=growthRarityCandidate(state,blocked,budget);if(!target)break;try{const before=Number(growthHamsterById(state,target.id)?.quantity||0),costBefore=growthCostSnapshot(target.cost,state),data=await apiJson('/player/hamster/upgrade','POST',{hamster_id:target.id},true,0),updated=growthFindNamed(data,'playerHamsters',target.id);state=growthMergeMutation(data,'growth-rarity');growthApplyCostFallback(data,target.cost,state,costBefore);budget.spent+=growthCapCost(target.cost);if(!updated||!updated.nextUpgrade){const refreshed=await growthRefreshEntity(target.id,state,'hamster');state=growthState||state;if(!refreshed)blocked.add(target.id);}log(`${growthDisplayName(target.id)} · ${before}/${target.required} · ${either('редкость повышена','rarity upgraded')} · ${growthCostText(target.cost)}`,'ok');await sleep(300);}catch(error){if(error?.name==='AbortError')throw error;if(growthStateError(error)){state=await growthRecoverState('rarity');blocked.clear();continue;}log(`${growthDisplayName(target.id)}: ${error.message}`,'warn');blocked.add(target.id);}}return state;}

  function growthBestHamster(state,blocked,budget,weightValue=1){
    let best=null,bestScore=0;const selectedWeight=Math.max(1,Math.min(8,Math.floor(Number(weightValue||1))||1));
    for(const hamster of growthArray('playerHamsters',state)){
      const id=String(hamster?.hamster_id||'');if(!id||blocked.has(id))continue;const level=Number(hamster.level||0),max=growthHamsterMaxLevel(hamster);if(level>=max){blocked.add(id);continue;}const next=hamster.nextLevelUp;if(!next)continue;const costs=next.costs||{},caps=growthCapCost(costs),gain=Number(next.diff||0);if(!growthHamsterLevelCostSafe(costs)||gain<=0||!growthCanAfford(costs,state)||!growthBudgetAllows(budget,costs))continue;const efficiency=gain/caps,weight=selectedWeight>1&&growthHamsterWeightedTarget(id)?selectedWeight:1,score=efficiency*weight;if(score>bestScore||(score===bestScore&&best&&caps<best.caps)){bestScore=score;best={id,caps,gain,efficiency,score,weight,max};}
    }
    return best;
  }
  function growthHamsterCurrencyAudit(state=growthState){
    let cap=0,pit=0,other=0;
    for(const hamster of growthArray('playerHamsters',state)){const cost=hamster?.nextLevelUp?.costs;if(!cost)continue;if(growthCapCost(cost)>0)cap++;else if(growthPitCost(cost)>0)pit++;else if(costParts(cost).length)other++;}
    recordDiagnostic('growth-hamster-currency-audit',{cap,pit,other,budgetId:GROWTH_HAMSTER_BUDGET_ID});
    return {cap,pit,other};
  }
  async function growthRunLevelsCore(state,budget,weightValue=1){
    const blocked=new Set();let safety=0,noProgress=0;
    while(budget.spent<budget.limit&&safety++<GROWTH_ACTION_SAFETY){
      await growthCheckpoint(either('Лучшее Power / Крышку','Best Power / Cap'));const best=growthBestHamster(state,blocked,budget,weightValue);if(!best)break;
      let hamster=await growthRefreshEntity(best.id,state,'hamster');state=growthState||state;if(!hamster){blocked.add(best.id);continue;}const current=Number(hamster.level||0),effectiveMax=growthHamsterMaxLevel(hamster),serverMax=Number(hamster.availableMaxLvl||0),next=hamster.nextLevelUp;if(!next||current>=effectiveMax){blocked.add(best.id);continue;}
      let actionType=null,preview=next,costs=next.costs||{};const itemsOk=cost=>growthHamsterLevelCostSafe(cost)&&growthCanAfford(cost,state)&&growthBudgetAllows(budget,cost),serverRemaining=serverMax>current?serverMax-current:0;
      if(serverRemaining>1&&serverRemaining<10&&serverMax<=effectiveMax&&hamster.maxLevelUp&&itemsOk(hamster.maxLevelUp.costs||{})){actionType='max';preview=hamster.maxLevelUp;costs=preview.costs||{};}
      else if(hamster.nearest10LevelUp){const next10=(Math.floor(current/10)+1)*10;if(next10<=effectiveMax&&itemsOk(hamster.nearest10LevelUp.costs||{})){actionType='fast10';preview=hamster.nearest10LevelUp;costs=preview.costs||{};}}
      if(!itemsOk(costs)){blocked.add(best.id);continue;}
      try{const powerBefore=growthTotalPower(state),costBefore=growthCostSnapshot(costs,state),payload={hamster_id:best.id};if(actionType)payload.fast_type=actionType;const data=await apiJson('/player/hamster/lvlUp','POST',payload,true,0),hasFactions=growthResponseHas(data,'playerFactions'),updated=growthFindNamed(data,'playerHamsters',best.id);state=growthMergeMutation(data,'growth-hamster-level');growthApplyCostFallback(data,costs,state,costBefore);budget.spent+=growthCapCost(costs);let live=growthHamsterById(state,best.id);if(!updated||!updated.nextLevelUp){await growthRefreshEntity(best.id,state,'hamster');state=growthState||state;live=growthHamsterById(state,best.id);}const after=Number(live?.level??current);if(after<=current){noProgress+=1;recordDiagnostic('growth-hamster-no-progress',{id:best.id,before:current,after,count:noProgress});if(noProgress>=GROWTH_NO_PROGRESS_LIMIT){blocked.add(best.id);break;}}else noProgress=0;const actualGain=hasFactions?Math.max(0,growthTotalPower(state)-powerBefore):Number(preview.diff||0),weighted=best.weight>1?` · ×${best.weight}`:'';log(`${growthDisplayName(best.id)} · Lv ${current}→${after} · ${growthCostText(costs)} · Крышки/Power ${growthCapCost(costs).toLocaleString(locale())}/${actualGain.toLocaleString(locale())} · Eff ${best.efficiency.toFixed(3)}${weighted}`,'ok');await sleep(350);}catch(error){if(error?.name==='AbortError')throw error;if(growthStateError(error)){state=await growthRecoverState('hamster-level');blocked.clear();continue;}log(`${growthDisplayName(best.id)}: ${error.message}`,'warn');blocked.add(best.id);}
    }
    return state;
  }

  async function growthRunHamstersCore(state,settings){
    const startCaps=growthResource(GROWTH_HAMSTER_BUDGET_ID,state),limit=Math.floor(startCaps*settings.capsPercent/100),budget={limit,spent:0};log(`${either('Бюджет Хомяков в Крышках','Hamster Caps budget')}: ${settings.capsPercent}% · ${limit.toLocaleString(locale())}/${startCaps.toLocaleString(locale())}`,'info');
    if(settings.copyPriorityEnabled)state=await growthRunPriorityCopiesCore(state,settings,budget);else log(either('Приоритет копий выключен','Copy Priority is off'),'info');
    state=await growthRunRarityCore(state,budget);state=await growthRunLevelsCore(state,budget,settings.mobsterPitWeight);log(`${either('Крышек потрачено','Caps spent')}: ${budget.spent.toLocaleString(locale())}/${limit.toLocaleString(locale())}`,'ok');return state;
  }

  function growthPhaseCount(settings,scope='all'){
    let n=0;const all=scope==='all',runPrep=scope==='prep'||(all&&settings.runPreparation),runGenerals=scope==='generals'||(all&&settings.runGenerals),runHamsters=scope==='hamsters'||(all&&settings.runHamsters);
    if(runPrep){if(settings.buyGeneralContracts)n++;if(settings.openAllBalls)n++;if(settings.openAllBoxes)n++;}if(runGenerals)n++;if(runHamsters)n+=settings.copyPriorityEnabled?3:2;return n;
  }
  async function growthRunPlan(scope='all'){
    if(!requireLicense()||hkRunner.running||growthBusy)return;
    const settings=growthReadSettingsFromUi();let phases=growthPhaseCount(settings,scope);if(!phases){log(either('В выбранном плане нет активных действий','No active actions in the selected plan'),'warn');return;}
    hkRunner.start({title:scope==='hamsters'?either('Хомяки','Hamsters'):scope==='generals'?either('Генералы','Generals'):either('Развитие','Growth'),total:phases,step:either('Подготовка актуального состояния','Preparing live state')});growthBusy=true;renderGrowth();
    let state=null,startPower=0,done=0;
    try{
      state=await growthLoadLive({force:true,loadShop:true,loadConfig:settings.excludeCurrentEventHamsters,silent:true});
      growthAbortCheck();
      if(!state)throw new Error(either('Не удалось получить актуальное состояние аккаунта','Could not load the current account state'));
      startPower=growthTotalPower(state);growthHamsterCurrencyAudit(state);
      const all=scope==='all',runPrep=scope==='prep'||(all&&settings.runPreparation),runGenerals=scope==='generals'||(all&&settings.runGenerals),runHamsters=scope==='hamsters'||(all&&settings.runHamsters);
      if(runPrep&&settings.buyGeneralContracts){hkRunner.setStep(either('Контракты Генералов','General contracts'),done,phases);state=await growthBuyAllGeneralContractsCore(state);hkRunner.setStep(either('Контракты готовы','Contracts done'),++done,phases);}
      if(runPrep&&settings.openAllBalls){hkRunner.setStep(either('Открываю шары','Opening balls'),done,phases);state=await growthOpenLootboxFamilyCore(state,'balls');hkRunner.setStep(either('Шары готовы','Balls done'),++done,phases);}
      if(runPrep&&settings.openAllBoxes){hkRunner.setStep(either('Открываю коробки','Opening boxes'),done,phases);state=await growthOpenLootboxFamilyCore(state,'boxes');hkRunner.setStep(either('Коробки готовы','Boxes done'),++done,phases);}
      if(runGenerals){hkRunner.setStep(either('Оптимизация Генералов','Optimizing Generals'),done,phases);state=await growthRunGeneralsCore(state,settings);hkRunner.setStep(either('Генералы готовы','Generals done'),++done,phases);}
      if(runHamsters){
        const startCaps=growthResource(GROWTH_HAMSTER_BUDGET_ID,state),limit=Math.floor(startCaps*settings.capsPercent/100),budget={limit,spent:0};
        if(settings.copyPriorityEnabled){hkRunner.setStep(either('Приоритет копий','Copy Priority'),done,phases);state=await growthRunPriorityCopiesCore(state,settings,budget);hkRunner.setStep(either('Копии готовы','Copies done'),++done,phases);}
        hkRunner.setStep(either('Редкость Хомяков','Hamster rarity'),done,phases);state=await growthRunRarityCore(state,budget);hkRunner.setStep(either('Редкость готова','Rarity done'),++done,phases);
        hkRunner.setStep(either('Уровни Хомяков','Hamster levels'),done,phases);state=await growthRunLevelsCore(state,budget,settings.mobsterPitWeight);hkRunner.setStep(either('Уровни готовы','Levels done'),++done,phases);log(`${either('Крышек потрачено','Caps spent')}: ${budget.spent.toLocaleString(locale())}/${limit.toLocaleString(locale())}`,'ok');
      }
      growthState=state;playerDocument=state;renderGrowth();const gain=Math.max(0,growthTotalPower(state)-startPower);hkRunner.finish(`${either('Готово','Done')} · Power +${gain.toLocaleString(locale())}`);log(`${either('Развитие завершено','Growth completed')} · Power +${gain.toLocaleString(locale())}`,'ok');
    }catch(error){if(error?.name==='AbortError'){hkRunner.reset();log(either('Операция остановлена','Operation stopped'),'warn');}else{hkRunner.fail(error);log(`${either('Развитие','Growth')}: ${error?.message||error}`,'bad');}}
    finally{growthBusy=false;renderGrowth();}
  }

  function growthMovePriority(index,direction){const settings=growthSettings(),rows=growthClonePriority(settings.copyPriority),to=index+(direction==='up'?-1:1);if(index<0||to<0||index>=rows.length||to>=rows.length)return;[rows[index],rows[to]]=[rows[to],rows[index]];saveGrowthSettings({copyPriority:rows});renderGrowth();}
  function growthRemovePriority(index){const settings=growthSettings(),rows=growthClonePriority(settings.copyPriority);if(index<0||index>=rows.length)return;rows.splice(index,1);saveGrowthSettings({copyPriority:rows});renderGrowth();}
  function growthResetPriority(){saveGrowthSettings({copyPriority:growthClonePriority(GROWTH_COPY_PRIORITY_DEFAULT)});renderGrowth();}

  let growthRenderTimer = null;
  function scheduleGrowthRender(){
    if(!root?.querySelector('.hk-page.active[data-content^="growth"]'))return;
    if(growthRenderTimer)return;
    growthRenderTimer=setTimeout(()=>{growthRenderTimer=null;renderGrowth();},hkRunner.running?180:40);
  }
  hkStateStore.subscribe(event=>{
    if(!event?.snapshot)return;growthState=event.snapshot;scheduleGrowthRender();
  });

  let autoRoutineRunning = false;
  let autoRoutineStop = false;
  let autoRoutineCurrent = '';

  const AUTO_ROUTINE_ACTIONS = [
    {id:'daily',ru:'Сегодня — выбранные действия',en:'Today — selected actions',run:()=>runDailySelected()},
    {id:'growth',ru:'Развитие — текущий план',en:'Growth — current plan',run:()=>growthRunPlan('all')},
    {id:'business',ru:'Бизнесы — текущая перестановка',en:'Businesses — current rearrangement',run:()=>executeBusinessPlan()},
    {id:'fair',ru:'Ярмарка — текущие выбранные лоты',en:'Fair — current selected lots',run:()=>runFair()},
    {id:'shop',ru:'Магазин — выбранные покупки',en:'Shop — selected purchases',run:()=>buyRegularShop()},
    {id:'recipes',ru:'Рецепты — текущие прокрутки',en:'Recipes — current rerolls',run:()=>runRecipes()},
    {id:'bureau',ru:'Проектное бюро — текущий рецепт',en:'Project Bureau — current recipe',run:()=>runProjectBureau()},
  ];

  function autoRoutineSelection() {
    const stored=load().autoRoutineSelection;
    return stored&&typeof stored==='object'&&!Array.isArray(stored)?{...stored}:{};
  }

  function saveAutoRoutineSelection(selection) {
    save({autoRoutineSelection:{...selection}});
  }

  function renderAutoRoutines() {
    const box=root?.querySelector('#hk-routines-content');
    if(!box)return;
    const selection=autoRoutineSelection();
    const selectedCount=AUTO_ROUTINE_ACTIONS.filter(row=>selection[row.id]).length;
    const current=AUTO_ROUTINE_ACTIONS.find(row=>row.id===autoRoutineCurrent);
    box.innerHTML=
      '<div class="hk-clan-head"><div><h3>'+either('Авто-рутины','Auto routines')+'</h3>'+
      '<small>'+either('Последовательный запуск уже настроенных модулей','Sequential run of already configured modules')+'</small></div></div>'+
      '<p class="hk-muted">'+either(
        'Рутина не меняет настройки модулей и не обходит их budget guard. Необратимые этапы сохраняют собственное подтверждение перед запуском.',
        'The routine does not change module settings or bypass budget guards. Irreversible stages keep their own confirmation before execution.'
      )+'</p>'+
      '<div class="hk-routine-list">'+AUTO_ROUTINE_ACTIONS.map((row,index)=>
        '<label class="hk-cardbox" style="display:flex;align-items:center;gap:10px;margin:7px 0;padding:10px">'+
        '<input type="checkbox" data-routine-id="'+escapeHtml(row.id)+'" '+(selection[row.id]?'checked':'')+' '+(autoRoutineRunning?'disabled':'')+'>'+
        '<b>'+(index+1)+'. '+escapeHtml(language==='en'?row.en:row.ru)+'</b></label>'
      ).join('')+'</div>'+
      '<div class="hk-toolbar" style="margin-top:10px">'+
        '<button id="hk-routine-run" class="hk-primary" '+(autoRoutineRunning||!selectedCount?'disabled':'')+'>'+either('Запустить цепочку','Run sequence')+'</button>'+
        '<button id="hk-routine-stop" class="hk-danger" '+(!autoRoutineRunning?'disabled':'')+'>'+either('Остановить','Stop')+'</button>'+
      '</div>'+
      '<p class="hk-muted">'+(autoRoutineRunning
        ? either('Текущий этап: ','Current stage: ')+escapeHtml(current?(language==='en'?current.en:current.ru):either('подготовка','preparing'))
        : either('Выбрано этапов: ','Selected stages: ')+selectedCount)+'</p>';

    box.querySelectorAll('[data-routine-id]').forEach(input=>input.onchange=()=>{
      const next=autoRoutineSelection();
      next[input.dataset.routineId]=!!input.checked;
      saveAutoRoutineSelection(next);
      renderAutoRoutines();
    });
    box.querySelector('#hk-routine-run')?.addEventListener('click',()=>void runAutoRoutine());
    box.querySelector('#hk-routine-stop')?.addEventListener('click',()=>stopAutoRoutine());
  }

  function stopAutoRoutine() {
    if(!autoRoutineRunning)return;
    autoRoutineStop=true;
    if(hkRunner.running)hkRunner.stop('auto-routine');
    log(either('Останавливаю авто-рутину после текущего этапа…','Stopping auto routine after the current stage…'),'warn');
    renderAutoRoutines();
  }

  async function runAutoRoutine() {
    if(!requireLicense()||autoRoutineRunning)return;
    if(hkRunner.running){alert(either('Сначала завершите текущую задачу','Finish the current task first'));return;}
    const selection=autoRoutineSelection();
    const queue=AUTO_ROUTINE_ACTIONS.filter(row=>selection[row.id]);
    if(!queue.length)return;
    if(!confirm(either(
      'Запустить авто-рутину из '+queue.length+' этапов?\n\nКаждый этап использует текущие настройки своего раздела. Необратимые операции сохраняют собственные подтверждения и лимиты.',
      'Run an auto routine with '+queue.length+' stages?\n\nEach stage uses the current settings of its module. Irreversible operations keep their own confirmations and limits.'
    )))return;

    autoRoutineRunning=true;
    autoRoutineStop=false;
    autoRoutineCurrent='';
    renderAutoRoutines();
    let completed=0;
    try{
      for(const action of queue){
        if(autoRoutineStop)break;
        if(hkRunner.running)throw new Error(either('Предыдущая задача ещё не завершена','The previous task is still running'));
        autoRoutineCurrent=action.id;
        renderAutoRoutines();
        log(either('Авто-рутина: ','Auto routine: ')+(language==='en'?action.en:action.ru));
        await action.run();
        if(autoRoutineStop)break;
        while(hkRunner.running&&!autoRoutineStop)await sleep(150);
        if(autoRoutineStop)break;
        completed+=1;
        await sleep(250);
      }
      log(autoRoutineStop
        ? either('Авто-рутина остановлена: завершено ','Auto routine stopped: completed ')+completed+'/'+queue.length
        : either('Авто-рутина завершена: ','Auto routine completed: ')+completed+'/'+queue.length,
        autoRoutineStop?'warn':'ok');
    }catch(error){
      log(either('Авто-рутина остановлена ошибкой','Auto routine stopped by an error')+': '+(error?.message||error),'bad');
    }finally{
      autoRoutineRunning=false;
      autoRoutineStop=false;
      autoRoutineCurrent='';
      renderAutoRoutines();
    }
  }

  function applyLanguage() {
    if (!root) return;
    root.querySelectorAll('[data-i18n]').forEach(element => { element.textContent = tr(element.dataset.i18n); });
    root.querySelectorAll('[data-i18n-placeholder]').forEach(element => { element.placeholder = tr(element.dataset.i18nPlaceholder); });
    root.querySelectorAll('[data-nav-ru][data-nav-en]').forEach(element => {
      const label = language === 'en' ? element.dataset.navEn : element.dataset.navRu;
      const target = element.querySelector('.hk-tab-label');
      if (target) target.textContent = label; else if (!element.classList.contains('planned')) element.textContent = label;
      element.title = label; element.setAttribute('aria-label', label);
    });
    root.querySelectorAll('.hk-tab').forEach(element => {
      const groupId=element.dataset.group; const groupHintKey={today:'navTodayHint',battles:'navBattlesHint',city:'navCityHint',business:'navBusinessHint',growth:'navGrowthHint',trade:'navTradeHint',clan:'navClanHint'}[groupId];
      const hint=element.querySelector('.hk-tab-hint'); if(hint&&groupHintKey)hint.textContent=tr(groupHintKey);
    });
    root.querySelectorAll('[data-lang]').forEach(button => button.classList.toggle('active', button.dataset.lang === language));
    fillTierFilters();
    refreshPresets(presetSelect?.value || '');
    refreshFairPresets(fairPresetSelect?.value || '');
    renderBusinessLists();
    renderFair();
    renderShop();
    renderRecipes();
    renderCommunityRecipes();
    renderProjectBureau();
    renderMapIndex();
    renderDailyTasks();
    renderClanSkills();
    renderGrowth();
    renderAutoRoutines();
    updatePitStatus();
    updateLicenseUI();
    if (statusLine) statusLine.textContent = tr('version', {v:VERSION});
  }

  function installFabDragging(fab) {
    if (!fab || !root) return;
    const clamp = (value, minimum, maximum) => Math.min(Math.max(value, minimum), maximum);
    const place = position => {
      const maximumX = Math.max(0, window.innerWidth - fab.offsetWidth);
      const maximumY = Math.max(0, window.innerHeight - fab.offsetHeight);
      const ratioX = Number(position?.ratioX);
      const ratioY = Number(position?.ratioY);
      const savedX = Number(position?.x);
      const savedY = Number(position?.y);
      const x = Number.isFinite(ratioX) ? ratioX * maximumX : Number.isFinite(savedX) ? savedX : maximumX - 12;
      const y = Number.isFinite(ratioY) ? ratioY * maximumY : Number.isFinite(savedY) ? savedY : maximumY - 12;
      root.style.right = 'auto';
      root.style.bottom = 'auto';
      root.style.left = `${clamp(x, 0, maximumX)}px`;
      root.style.top = `${clamp(y, 0, maximumY)}px`;
    };
    const snapshot = () => {
      const rect = fab.getBoundingClientRect();
      const maximumX = Math.max(0, window.innerWidth - rect.width);
      const maximumY = Math.max(0, window.innerHeight - rect.height);
      const x = clamp(rect.left, 0, maximumX);
      const y = clamp(rect.top, 0, maximumY);
      return {x, y, ratioX:maximumX ? x / maximumX : 0, ratioY:maximumY ? y / maximumY : 0};
    };
    place(load().fabPosition);
    let drag = null;
    const savePosition = () => {
      // The launcher position belongs to this screen/device. Keep it local so
      // account settings sync cannot replace it with coordinates from another
      // phone or desktop browser.
      const next = {...load(), fabPosition:snapshot()};
      localStorage.setItem(STORE, JSON.stringify(next));
    };
    const start = event => {
      // Mobile Safari can expose Pointer Events but omit pointermove for an
      // injected userscript. Touch Events below handle that path reliably.
      if (event.pointerType === 'touch' && 'ontouchstart' in window) return;
      if (event.pointerType === 'mouse' && event.button !== 0) return;
      const rect = fab.getBoundingClientRect();
      drag = {pointerId:event.pointerId, startX:event.clientX, startY:event.clientY, left:rect.left, top:rect.top, moved:false};
      fab.classList.add('dragging');
      try { fab.setPointerCapture(event.pointerId); } catch (_) {}
      if (event.cancelable) event.preventDefault();
    };
    const move = event => {
      if (!drag || drag.pointerId !== event.pointerId) return;
      const deltaX = event.clientX - drag.startX;
      const deltaY = event.clientY - drag.startY;
      if (Math.hypot(deltaX, deltaY) >= 4) drag.moved = true;
      if (!drag.moved) return;
      place({x:drag.left + deltaX, y:drag.top + deltaY});
      if (event.cancelable) event.preventDefault();
    };
    const finish = (event, cancelled = false) => {
      if (!drag || drag.pointerId !== event.pointerId) return;
      const moved = drag.moved;
      drag = null;
      fab.classList.remove('dragging');
      try { fab.releasePointerCapture(event.pointerId); } catch (_) {}
      if (moved) savePosition();
      else if (!cancelled) { panel.classList.add('open'); updateWatermark(); }
      if (event.cancelable) event.preventDefault();
    };
    fab.addEventListener('pointerdown', start, {passive:false});
    // Listen on the document as well as the button. This keeps dragging alive
    // when the finger/mouse leaves the 58px circle; older Safari builds do not
    // always honour pointer capture inside an injected userscript.
    document.addEventListener('pointermove', move, {capture:true, passive:false});
    document.addEventListener('pointerup', finish, {capture:true, passive:false});
    document.addEventListener('pointercancel', event => finish(event, true), {capture:true, passive:false});
    const touchById = (list, identifier) => Array.from(list || []).find(touch => touch.identifier === identifier);
    const touchStart = event => {
      if (drag || event.touches.length !== 1) return;
      const touch = event.changedTouches[0];
      const rect = fab.getBoundingClientRect();
      drag = {pointerId:`touch:${touch.identifier}`, touchId:touch.identifier, startX:touch.clientX, startY:touch.clientY, left:rect.left, top:rect.top, moved:false};
      fab.classList.add('dragging');
      if (event.cancelable) event.preventDefault();
      event.stopPropagation();
    };
    const touchMove = event => {
      if (!drag || drag.touchId === undefined) return;
      const touch = touchById(event.touches, drag.touchId) || touchById(event.changedTouches, drag.touchId);
      if (!touch) return;
      const deltaX = touch.clientX - drag.startX;
      const deltaY = touch.clientY - drag.startY;
      if (Math.hypot(deltaX, deltaY) >= 4) drag.moved = true;
      if (drag.moved) place({x:drag.left + deltaX, y:drag.top + deltaY});
      if (event.cancelable) event.preventDefault();
      event.stopPropagation();
    };
    const touchFinish = (event, cancelled = false) => {
      if (!drag || drag.touchId === undefined) return;
      const touch = touchById(event.changedTouches, drag.touchId);
      if (!touch && !cancelled) return;
      const moved = drag.moved;
      drag = null;
      fab.classList.remove('dragging');
      if (moved) savePosition();
      else if (!cancelled) { panel.classList.add('open'); updateWatermark(); }
      if (event.cancelable) event.preventDefault();
      event.stopPropagation();
    };
    fab.addEventListener('touchstart', touchStart, {capture:true, passive:false});
    document.addEventListener('touchmove', touchMove, {capture:true, passive:false});
    document.addEventListener('touchend', touchFinish, {capture:true, passive:false});
    document.addEventListener('touchcancel', event => touchFinish(event, true), {capture:true, passive:false});
    const restoreInsideViewport = () => place(load().fabPosition || snapshot());
    window.addEventListener('resize', restoreInsideViewport);
    window.addEventListener('orientationchange', restoreInsideViewport);
    fab.addEventListener('keydown', event => {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      panel.classList.add('open'); updateWatermark(); event.preventDefault();
    });
    window.addEventListener('resize', () => place(load().fabPosition), {passive:true});
  }

  const MODULE_LIVE_TTL_MS = 12000;
  const moduleLiveState = new Map();
  function moduleMutationBusy(){return !!(hkRunner.running||pitRunning||businessBusy||fairRunning||shopRunning||recipeRunning||bureauRunning||resourceBusy||mapScanning||dailyRunning||clanSkillScanning||growthBusy);}
  async function refreshModuleLive(page, {force=false} = {}) {
    const key = String(page || '');
    if (!key || key.startsWith('growth')) return null;
    if(moduleMutationBusy()){recordDiagnostic('module-live-read-deferred',{page:key});return null;}
    const existing = moduleLiveState.get(key) || {at:0,promise:null};
    if (existing.promise) return existing.promise;
    if (!force && Date.now() - Number(existing.at || 0) < MODULE_LIVE_TTL_MS) return null;
    let liveReadOk=false;
    const task = (async () => {
      try {
        if (!licenseState.allowed) {
          const connected = await bootstrapLateGameConnection();
          if (!connected || !playerDocument) return null;
          await checkLicense(playerDocument.player || {}, true);
          if (!licenseState.allowed) return null;
        }
        if (key === 'daily') {const value=await refreshDailyTasks();liveReadOk=true;return value;}
        if (key === 'resources') {const value=await loadResources(false);liveReadOk=true;return value;}
        if (key === 'fair') {const value=await loadFair();liveReadOk=true;return value;}
        if (key === 'shop') {const value=await loadShop();liveReadOk=true;return value;}
        if (key === 'recipes') {const value=await loadRecipes();liveReadOk=true;return value;}
        if (key === 'business') {
          playerDocument = await apiJson('/player/me','POST');
          await ensureRecipeMetadata();
          refreshBusinessData();
          liveReadOk=true;return playerDocument;
        }
        if (key === 'pit') {
          playerDocument = await apiJson('/player/me','POST');
          acceptPitDocument(`${apiBase}/player/me`,playerDocument);
          updatePitStatus(pitState()); updatePitButtons();
          liveReadOk=true;return playerDocument;
        }
        if (key === 'bosses') {const value=await refreshBosses(false);liveReadOk=true;return value;}
        if (key === 'wars') {const value=await refreshWars(false);liveReadOk=true;return value;}
        if (key === 'clan') {
          playerDocument = await apiJson('/player/me','POST');
          renderClanSkills();
          await refreshSharedClanSkills();
          maybeAutoScanClanSkills();
          liveReadOk=true;return playerDocument;
        }
        if (key === 'buildings') {const value=await refreshBuildings(false);liveReadOk=true;return value;}
        if (key === 'explore') {const value=await refreshExplore(false);liveReadOk=true;return value;}
        if (key === 'maps') {
          playerDocument = await apiJson('/player/me','POST');
          const playerId=playerIdentity(playerDocument?.player||{}),lastByPlayer=Number(load().mapContributionByPlayer?.[playerId]||0);
          if(playerId&&Date.now()-lastByPlayer>86400000&&!initialMapResearchAttempted.has(playerId)){
            initialMapResearchAttempted.add(playerId);
            await submitOwnedMapAreas(true);
          }else await loadMapIndex(false);
          liveReadOk=true;return playerDocument;
        }
        return null;
      } catch (error) {
        recordDiagnostic('module-live-read-error',{page:key,error:error?.message||error});
        log(`${either('Автообновление','Auto refresh')} ${key}: ${error?.message||error}`,'warn');
        return null;
      } finally {
        const row = moduleLiveState.get(key) || {};
        row.at = liveReadOk ? Date.now() : 0; row.promise = null; moduleLiveState.set(key,row);
      }
    })();
    moduleLiveState.set(key,{...existing,promise:task});
    return task;
  }

  function renderRunnerState() {
    if (!root) return;
    const box=root.querySelector('#hk-runner'); if(!box)return;
    const state=hkRunner.state;
    const visibleState=state.status!=='idle'; box.classList.toggle('show',visibleState);
    if(!visibleState)return;
    const labels={running:either('Выполняется','Running'),paused:either('Пауза','Paused'),stopping:either('Остановка','Stopping'),done:either('Готово','Done'),error:either('Ошибка','Error')};
    const percent=state.total?Math.max(0,Math.min(100,(state.done/state.total)*100)):(state.status==='done'?100:0);
    root.querySelector('#hk-runner-title').textContent=state.title||either('Выполнение','Execution');
    root.querySelector('#hk-runner-state').textContent=labels[state.status]||state.status;
    root.querySelector('#hk-runner-step').textContent=state.error||state.step||(state.total?`${state.done} / ${state.total}`:'');
    root.querySelector('#hk-runner-fill').style.width=`${percent}%`;
    const pause=root.querySelector('#hk-runner-pause'); const stop=root.querySelector('#hk-runner-stop');
    pause.textContent=state.status==='paused'?either('Продолжить','Continue'):either('Пауза','Pause');
    pause.disabled=!state.pausable||!['running','paused'].includes(state.status);
    stop.textContent=either('Остановить','Stop'); stop.disabled=!state.stoppable||!['running','paused'].includes(state.status);
  }

  function renderUI() {
    if (!document.body) return;
    if (root?.isConnected && root.querySelector('#hk-fab')) return;
    if (root && !root.isConnected) { root = null; panel = null; }
    // If Safari still has an older duplicate userscript enabled, replace its
    // two-tab panel with this newer build instead of silently aborting.
    document.querySelector('#hk-mobile-root')?.remove();
    const style = document.createElement('style');
    style.textContent = `
      #hk-mobile-root{position:fixed;z-index:2147483647;right:12px;bottom:calc(12px + env(safe-area-inset-bottom));font:15px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#f7f9fc}
      #hk-fab{display:block!important;visibility:visible!important;opacity:1!important;width:58px;height:58px;border:0;border-radius:50%;background:linear-gradient(145deg,#ffb627,#ff7b00);box-shadow:0 8px 28px #0008;color:#15100a;font-size:25px;font-weight:900;touch-action:none;user-select:none;-webkit-user-select:none;-webkit-touch-callout:none;cursor:grab}
      #hk-fab.dragging{cursor:grabbing;transform:scale(1.05);box-shadow:0 10px 32px #000a}
      #hk-panel{position:fixed;inset:0;background:#0b1018ee;backdrop-filter:blur(16px);display:none;overflow:auto;padding:calc(14px + env(safe-area-inset-top)) 14px calc(24px + env(safe-area-inset-bottom));box-sizing:border-box}
      #hk-panel.open{display:block} .hk-head{display:flex;align-items:center;justify-content:space-between;gap:8px}.hk-head h2{margin:0;font-size:22px;flex:1}.hk-close{border:0;background:#253044;color:white;border-radius:12px;padding:10px 14px;font-size:20px}.hk-lang{display:flex;gap:5px}.hk-lang button{border:1px solid #34445c;background:#182230;border-radius:10px;padding:7px 8px;font-size:21px;line-height:1;opacity:.5}.hk-lang button.active{opacity:1;border-color:#ffad1f;background:#3a2b14;box-shadow:0 0 0 2px #ffad1f33}
      .hk-donation{width:100%;margin:12px 0 0;border:1px solid #ff6f91;border-radius:13px;padding:11px;background:linear-gradient(135deg,#7b2947,#b63863);color:#fff;font-weight:900;box-shadow:0 7px 18px #7b294744}.hk-donation:active{transform:scale(.99)}
      #hk-watermark{position:fixed;inset:-40px;z-index:20;pointer-events:none;display:grid;grid-template-columns:repeat(2,minmax(260px,1fr));grid-auto-rows:minmax(120px,1fr);align-items:center;justify-items:center;overflow:hidden;transition:transform .5s ease}#hk-watermark span{display:block;max-width:310px;color:#fff;font:700 11px ui-monospace,monospace;letter-spacing:.4px;opacity:.035;transform:rotate(-24deg);white-space:nowrap;text-shadow:0 1px 2px #000}
      .hk-license{padding:11px;border:1px solid #3b4a61;border-radius:12px;background:#101a28;margin:14px 0;color:#c8d4e5}.hk-license.ok{border-color:#287b60}.hk-license.bad{border-color:#803b49}.hk-update{display:none;margin:0 0 14px;padding:12px;border:1px solid #ffad1f;border-radius:13px;background:#2a2418;color:#fff}.hk-update.required{border-color:#ff6b75;background:#351b22}.hk-update b,.hk-update small{display:block}.hk-update small{margin-top:5px;color:#cbd5e5}.hk-update .hk-primary{margin-top:10px}.hk-locked .hk-tabs,.hk-locked .hk-subnav,.hk-locked .hk-runner,.hk-locked .hk-page{display:none!important}
      .hk-health{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px;margin:0 0 8px}.hk-health-chip{display:grid;grid-template-columns:9px minmax(0,1fr);align-items:center;column-gap:7px;padding:9px 8px;border:1px solid #34445c;border-radius:11px;background:#111a27;color:#d3dbe8;min-width:0}.hk-health-chip:before{content:'';width:8px;height:8px;border-radius:50%;background:#64748b;box-shadow:0 0 0 3px #64748b22}.hk-health-chip.ok{border-color:#24694f;background:#10231d}.hk-health-chip.ok:before{background:#52d296;box-shadow:0 0 0 3px #52d29622}.hk-health-chip.bad{border-color:#7a3443;background:#29151b}.hk-health-chip.bad:before{background:#ff6b7a;box-shadow:0 0 0 3px #ff6b7a22}.hk-health-chip b{font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.hk-health-chip small{grid-column:2;color:#8392a7;font-size:9px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.hk-health-actions{display:flex;gap:7px;margin:0 0 14px}.hk-health-actions button{flex:1;min-height:36px;font-size:12px}@media(max-width:430px){.hk-health{grid-template-columns:repeat(2,minmax(0,1fr))}}
      .hk-tabs{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:16px 0 10px}.hk-tab{display:grid;grid-template-columns:36px minmax(0,1fr);grid-template-rows:auto auto;column-gap:9px;align-items:center;min-width:0;min-height:62px;border:1px solid #30425d;border-radius:15px;padding:9px 10px;background:linear-gradient(145deg,#1d293b,#141e2d);color:#eef4ff;text-align:left;overflow:hidden}.hk-tab:last-child:nth-child(odd){grid-column:1/-1}.hk-tab-icon{grid-row:1/3;display:grid;place-items:center;width:36px;height:36px;border-radius:12px;background:#ffffff0d;border:1px solid #ffffff12;font-size:21px}.hk-tab-label{font-size:13px;font-weight:900;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.hk-tab-hint{font-size:9px;color:#8797ad;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.hk-tab.active{border-color:#ffbd37;background:linear-gradient(145deg,#3a2c15,#282117);box-shadow:0 0 0 2px #ffad1f22,0 5px 14px #0006}.hk-tab.active .hk-tab-icon{background:#ffad1f;color:#1b1308;border-color:#ffca62}.hk-tab.active .hk-tab-hint{color:#d9b96d}.hk-tab-icon img{display:block;width:100%;height:100%;object-fit:cover;border-radius:10px}.hk-tab.active .hk-tab-icon img{filter:saturate(1.08) brightness(1.05)}.hk-subnav{display:flex;gap:7px;overflow-x:auto;padding:1px 0 12px;scrollbar-width:none}.hk-subnav::-webkit-scrollbar{display:none}.hk-subnav button{flex:0 0 auto;border:1px solid #314058;border-radius:999px;padding:8px 12px;background:#111b29;color:#9fb0c6;font-size:11px;font-weight:800;white-space:nowrap}.hk-subnav button.active{border-color:#ffad1f;background:#3b2b13;color:#fff}.hk-subnav button.planned{opacity:.42;border-style:dashed}.hk-runner{display:none;margin:0 0 12px;padding:11px;border:1px solid #36506f;border-radius:14px;background:linear-gradient(145deg,#111c2a,#0d1520)}.hk-runner.show{display:block}.hk-runner-head{display:flex;align-items:center;gap:8px}.hk-runner-head b{flex:1;font-size:12px}.hk-runner-state{font-size:9px;color:#8fa1b8;text-transform:uppercase;letter-spacing:.4px}.hk-runner-step{margin-top:5px;color:#b9c6d7;font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.hk-runner-track{height:6px;margin:9px 0 8px;border-radius:999px;background:#263246;overflow:hidden}.hk-runner-fill{height:100%;width:0;background:linear-gradient(90deg,#ffad1f,#ffd45c);transition:width .2s ease}.hk-runner-actions{display:flex;gap:7px}.hk-runner-actions button{flex:1;min-height:34px;font-size:11px}.hk-roadmap{display:grid;gap:9px}.hk-roadmap-item{padding:12px;border:1px solid #2d3a4e;border-radius:13px;background:#111925}.hk-roadmap-item b{display:block;color:#ffe08a}.hk-roadmap-item small{display:block;margin-top:4px;color:#8d9bb0;line-height:1.35}.hk-growth-stats{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:10px 0}.hk-growth-stats>div{padding:11px;border:1px solid #304057;border-radius:12px;background:#0e1723}.hk-growth-stats small{display:block;color:#8797ad;font-size:10px}.hk-growth-stats b{display:block;margin-top:4px;color:#ffe083;font-size:15px}.hk-growth-actions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.hk-growth-actions button{margin-top:0}.hk-growth-options{display:grid;gap:9px;margin:10px 0}.hk-growth-option{display:grid;grid-template-columns:minmax(0,1fr) 110px;gap:10px;align-items:center;padding:10px;border:1px solid #2d3a4e;border-radius:12px;background:#101927}.hk-growth-option span{display:grid;gap:3px}.hk-growth-option small{color:#8998ad;font-size:10px}.hk-growth-option select{background:#0b111b;color:white;border:1px solid #3b4a61;border-radius:10px;padding:9px}.hk-growth-check{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px;border:1px solid #2d3a4e;border-radius:12px;background:#101927}.hk-growth-check input{width:20px;height:20px;accent-color:#ffad1f}.hk-growth-live{display:grid;gap:3px;padding:9px 10px;border:1px solid #245d48;border-radius:11px;background:#0d211b}.hk-growth-live span{font-size:11px;font-weight:900;color:#6ee7a8}.hk-growth-live small{font-size:9px;color:#8fa89f}.hk-growth-plan{display:grid;gap:6px;margin:4px 0 10px;padding:11px;border:1px solid #3a4659;border-radius:12px;background:#0e1723}.hk-growth-plan>b{color:#ffe083}.hk-growth-plan>span{font-size:11px;color:#d4deea}.hk-growth-plan>small{font-size:9px;color:#8290a4;line-height:1.4}.hk-growth-priority-head{display:flex;align-items:center;justify-content:space-between;gap:8px}.hk-growth-priority-head h3{margin:0}.hk-growth-priority-list{display:grid;gap:7px;margin-top:8px}.hk-growth-priority{display:grid;grid-template-columns:64px minmax(0,1fr) auto;align-items:center;gap:8px;padding:8px;border:1px solid #2d3a4e;border-radius:10px;background:#101927}.hk-growth-priority>b{color:#ffe083}.hk-growth-priority>span{font-size:9px;color:#8797ad}.hk-growth-priority>div{display:flex;gap:4px}.hk-growth-priority button{min-width:30px;margin:0;padding:6px 8px}.hk-growth-stats>div:nth-child(n+5){background:#121a28}@media(max-width:430px){.hk-tab{min-height:58px;padding:8px}.hk-tab-icon{width:32px;height:32px;font-size:19px}}
      .hk-business-tabs{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin:10px 0}.hk-business-tab{border:1px solid #34445b;border-radius:11px;padding:11px;background:#172234;color:#b8c4d6;font-weight:700}.hk-business-tab.active{border-color:#ffad1f;background:#3a2a0f;color:#fff}.hk-business-pane{display:none}.hk-business-pane.active{display:block}
      .hk-page{display:none}.hk-page.active{display:block}.hk-cardbox{background:#151d29;border:1px solid #2a374a;border-radius:16px;padding:14px;margin-bottom:12px}.hk-grid{display:grid;grid-template-columns:1fr 110px;gap:10px;align-items:center}
      input,select,button{font:inherit}.hk-grid input,.hk-grid select,.hk-toolbar select{min-width:0;background:#0b111b;color:white;border:1px solid #3b4a61;border-radius:10px;padding:10px}.hk-primary,.hk-secondary,.hk-danger{width:100%;border:0;border-radius:12px;padding:13px;margin-top:9px;font-weight:800}.hk-primary{background:#ffad1f;color:#16110a}.hk-secondary{background:#28364a;color:white}.hk-danger{background:#642a32;color:#fff}.hk-primary:disabled,.hk-secondary:disabled{opacity:.45}
      .hk-live{padding:10px;border-radius:10px;background:#0d1520;margin:10px 0;color:#cbd5e5}.hk-wallet-forecast{display:grid;gap:7px;margin-top:9px;padding-top:8px;border-top:1px solid #26354a}.hk-wallet-row{display:grid;grid-template-columns:minmax(105px,.65fr) minmax(0,1.35fr);gap:8px;align-items:center;padding:7px 8px;border:1px solid #2b3a50;border-radius:9px;background:#111b29;font-size:12px}.hk-wallet-row.shortage{border-color:#ff6677;background:#301923;color:#ffd6dc}.hk-wallet-currency{display:flex;align-items:center;gap:5px;min-width:0}.hk-wallet-currency b{overflow:hidden;text-overflow:ellipsis}.hk-toolbar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:10px}.hk-toolbar>*{flex:1}.hk-toolbar button{border:0;border-radius:10px;padding:10px;background:#29374a;color:white}.hk-toolbar input{min-width:0;background:#0b111b;color:white;border:1px solid #3b4a61;border-radius:10px;padding:10px}
      .hk-daily-progress{margin:10px 0;padding:10px;border:1px solid #29394f;border-radius:12px;background:#101927}.hk-daily-progress>div{display:flex;justify-content:space-between;gap:9px;font-size:12px}.hk-daily-progress span{color:#aebbd0}.hk-daily-progress i{display:block;height:8px;margin-top:8px;border-radius:8px;overflow:hidden;background:#080d14}.hk-daily-progress em{display:block;height:100%;border-radius:inherit;background:#36d59a;transition:width .2s}.hk-daily-list{list-style:none;padding:0;margin:12px 0;display:grid;gap:8px}.hk-daily-list>li{padding:10px;border:1px solid #29394f;border-radius:11px;background:#0d1520;display:grid;gap:4px}.hk-daily-list>li>b{color:#e7edf7}.hk-daily-list span{font-size:12px;color:#9eabc0}.hk-daily-list ul{list-style:none;margin:5px 0 0;padding:0;display:grid;gap:5px}.hk-daily-list ul li{display:flex;justify-content:space-between;gap:10px;font-size:12px;color:#aebbd0}.hk-daily-list ul li.ready b{color:#6ee7a8}
      .hk-today-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.hk-today-section{margin:9px 0;padding:11px;border:1px solid #29394f;border-radius:12px;background:#0d1520}.hk-today-section h4{margin:0 0 8px;color:#f0f4fb}.hk-today-section p{margin:4px 0;color:#aebbd0}.hk-today-section>ul{list-style:none;margin:0;padding:0;display:grid;gap:5px}.hk-today-section>ul li{display:flex;justify-content:space-between;gap:8px;font-size:12px}.hk-today-section>ul span{color:#9eabc0}.hk-pit-limits{display:grid;gap:6px}.hk-pit-limits>div{display:grid;grid-template-columns:minmax(100px,.8fr) 1.6fr;gap:3px 8px;padding:7px 8px;border-radius:9px;background:#101927}.hk-pit-limits span{font-size:11px;color:#c3cee0}.hk-pit-limits small{grid-column:2;color:#94a3b8}.hk-pit-limits strong{color:#6ee7a8}.hk-pit-enable{display:flex;align-items:center;gap:6px}.hk-pit-enable input{margin:0}.hk-pit-enable span{color:#94a3b8}.hk-pit-move-choice{grid-column:1/3;display:grid;grid-template-columns:minmax(100px,.8fr) minmax(72px,.45fr) 1.6fr;align-items:center;gap:7px;margin-top:4px;padding-top:6px;border-top:1px solid #27364b}.hk-pit-move-choice select{min-width:72px}.hk-pit-move-choice em{font-style:normal;font-size:11px;color:#94a3b8}.hk-pit-move-choice em b{color:#ffbd3f}.hk-today-balances{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:7px}.hk-today-balance{display:grid;grid-template-columns:24px 1fr auto;align-items:center;gap:6px;padding:7px;border-radius:9px;background:#101927}.hk-today-balance span{font-size:11px;color:#aebbd0}.hk-today-action-groups{display:grid;gap:8px;margin-top:9px}.hk-today-action-group{border:1px solid #304057;border-radius:11px;background:#101927;overflow:hidden}.hk-today-action-group>summary{display:flex;justify-content:space-between;align-items:center;gap:8px;cursor:pointer;padding:10px}.hk-today-action-group>summary span{min-width:25px;padding:2px 7px;border-radius:12px;background:#26364c;text-align:center;color:#cbd5e5}.hk-today-action-group>div{padding:0 7px 7px}.hk-today-action{display:grid;grid-template-columns:24px 1fr auto;gap:7px;align-items:center;margin:6px 0;padding:8px;border:1px solid #304057;border-radius:10px;background:#0d1520}.hk-today-action.has-lot-icon{grid-template-columns:24px 58px 1fr auto}.hk-today-action.locked{opacity:.6}.hk-today-action>span{display:grid;gap:4px}.hk-today-action small{display:flex;align-items:center;gap:5px;flex-wrap:wrap;color:#9eabc0}.hk-today-quantity{display:grid;gap:3px;min-width:82px;font-size:10px;color:#9eabc0}.hk-today-quantity select{min-width:76px}.hk-today-lot-visual{width:54px;display:grid!important;justify-items:center;gap:1px}.hk-today-lot-image{width:50px;height:50px;object-fit:contain}.hk-today-lot-visual>small{min-height:12px;font-size:10px;font-weight:800;color:#e8eef8}.hk-action-count{color:#ffbd3f}.hk-free{color:#6ee7a8}.hk-today-plan ol{margin:8px 0;padding-left:24px}.hk-today-plan li{padding:5px 0}.hk-today-plan li>span{display:block;color:#aebbd0;font-size:12px}.hk-today-plan li.blocked{color:#ff8290}.hk-budget summary{cursor:pointer;font-weight:800}.hk-budget-row{margin-top:9px;padding:9px;border:1px solid #304057;border-radius:10px;display:grid;grid-template-columns:1.2fr repeat(3,1fr);gap:7px;align-items:end}.hk-budget-title{display:flex;align-items:center;gap:6px}.hk-budget-row>label{display:grid;gap:4px;font-size:10px;color:#9eabc0}.hk-budget-row>small,.hk-budget-flags{grid-column:1/5}.hk-budget-flags{display:flex;gap:10px;flex-wrap:wrap;font-size:11px}.hk-budget-flags label{display:flex;align-items:center;gap:4px}.hk-budget-flags .premium{color:#62dfff}.hk-expense-journal{list-style:none;padding:0;margin:8px 0;display:grid;gap:5px}.hk-expense-journal li{display:grid!important;grid-template-columns:1fr auto;gap:3px 8px;padding:6px;border-radius:7px;background:#101927}.hk-expense-journal li small{grid-column:1/3;color:#8fa0b8}.hk-expense-journal li.failed{color:#ff8290}.hk-expense-journal li.ok b{color:#6ee7a8}
      .hk-today-store-tabs{display:flex;gap:6px}.hk-today-store-tabs button{display:flex;flex:1 1 0;min-width:0;justify-content:center;align-items:center;gap:5px;padding:9px 6px}.hk-today-store-tabs button.active{border-color:#f3a712;background:#3a2a0e;color:#fff}.hk-today-store-tabs button span{min-width:20px;padding:1px 6px;border-radius:10px;background:#26364c;font-size:10px}.hk-today-store-page{margin-top:7px}.hk-today-action.mandatory{border-color:#2d9a70;background:#10241f}.hk-today-action.mandatory input:disabled,.hk-today-action.mandatory select:disabled{opacity:1}
      @media(max-width:620px){.hk-today-grid{grid-template-columns:1fr}.hk-budget-row{grid-template-columns:1fr 1fr}.hk-budget-row>small,.hk-budget-flags{grid-column:1/3}.hk-today-store-tabs button{font-size:11px;padding:8px 3px;gap:3px}.hk-today-store-tabs button span{min-width:18px;padding:1px 4px}}
      #hk-business-lists{display:grid;grid-template-columns:1fr;gap:12px}h3{font-size:16px;margin:8px 0}.hk-cards{display:grid;gap:8px}.hk-card{display:flex;align-items:center;gap:10px;background:#151d29;border:1px solid #2a374a;border-radius:14px;padding:9px}.hk-card.selected{border-color:#ffad1f;background:#2a2418}.hk-card.empty{border-style:dashed}.hk-card input{width:22px;height:22px}.hk-card select{margin-left:auto;background:#0b111b;color:white;border:1px solid #455672;border-radius:9px;padding:8px;min-width:58px}.hk-card>.hk-business-info{display:flex;flex:1;min-width:0;flex-direction:column}.hk-card small{color:#a9b5c7;margin-top:3px}.hk-business-name{line-height:1.25;overflow-wrap:anywhere}.hk-business-properties{color:#e3c66e!important;font-size:11px;line-height:1.3;overflow-wrap:anywhere}.hk-icon{width:46px;height:46px;object-fit:contain;flex:0 0 46px}.hk-empty-icon{width:46px;height:46px;border:2px dashed #6381a8;border-radius:50%;display:flex!important;align-items:center;justify-content:center;color:#77baff;font-size:27px;flex:0 0 46px}.hk-empty-icon.compact{width:34px;height:34px;flex-basis:34px;font-size:20px}.hk-plan-row{display:flex;align-items:center;gap:6px;overflow:hidden;margin:10px 0}.hk-plan-row .hk-icon{width:34px;height:34px;flex-basis:34px}.hk-count{font-weight:800}.hk-muted{color:#9aa8bc}.hk-log{max-height:150px;overflow:auto;font:12px ui-monospace,monospace;background:#080d14;border-radius:12px;padding:9px;margin-top:12px}.hk-log>div{padding:3px 0;border-bottom:1px solid #182130}.hk-log-ok{color:#6ee7a8}.hk-log-warn{color:#ffd166}.hk-log-bad{color:#ff8792}.hk-status{font-size:12px;color:#aebbd0;margin-top:8px}
      .hk-optimizer{margin:10px 0;padding:11px;border:1px solid #34445b;border-radius:14px;background:#0d1520}.hk-optimizer h3{margin-top:0}.hk-optimizer-controls{display:grid;grid-template-columns:1fr 1fr;gap:8px}.hk-optimizer-controls label{display:grid;gap:4px;color:#aebbd0;font-size:11px}.hk-optimizer-controls select,.hk-optimizer-controls input{min-width:0;background:#0b111b;color:#fff;border:1px solid #43536d;border-radius:9px;padding:9px}.hk-optimizer-filter{display:grid;gap:6px;margin-top:9px;padding:9px;border:1px solid #2d3d54;border-radius:10px;background:#101927}.hk-optimizer-filter>small{color:#8fa0b8}.hk-optimizer-collapsible>summary{display:flex;align-items:center;gap:7px;cursor:pointer;list-style:none}.hk-optimizer-collapsible>summary::-webkit-details-marker{display:none}.hk-optimizer-collapsible>summary:before{content:'▸';color:#ffbd3f;font-size:15px}.hk-optimizer-collapsible[open]>summary:before{content:'▾'}.hk-optimizer-collapsible:not([open])>small,.hk-optimizer-collapsible:not([open])>.hk-optimizer-replaceable{display:none}.hk-optimizer-tiers{display:flex;gap:6px;flex-wrap:wrap}.hk-tier-choice{display:flex;align-items:center;gap:4px;padding:6px 9px;border:1px solid #42536d;border-radius:9px;background:#0b111b}.hk-optimizer-replaceable{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:6px;max-height:250px;overflow:auto}.hk-optimizer-business-choice{display:grid;grid-template-columns:22px 42px 1fr;align-items:center;gap:6px;padding:6px;border:1px solid #34445b;border-radius:9px;background:#0b111b}.hk-optimizer-business-choice.locked{border-color:#a64d5b;background:#27151b}.hk-optimizer-business-choice.tier-disabled{border-color:#34445b;background:#0b111b;opacity:.48;cursor:not-allowed}.hk-optimizer-business-choice.tier-disabled input{pointer-events:none}.hk-optimizer-business-choice .hk-icon{width:40px;height:40px}.hk-optimizer-business-choice>span{display:grid;gap:2px;min-width:0}.hk-optimizer-business-choice b{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.hk-optimizer-business-choice small{color:#9eabc0}.hk-optimizer-actions{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:8px}.hk-optimizer-result{display:grid;gap:8px;margin-top:9px}.hk-optimizer-summary{display:grid;grid-template-columns:repeat(3,1fr);gap:7px}.hk-optimizer-summary span{padding:8px;border-radius:9px;background:#111c2b;color:#aebbd0;font-size:11px}.hk-optimizer-summary b{display:block;color:#f4f7fb;margin-top:3px}.hk-optimizer-result ul{list-style:none;padding:0;margin:0;display:grid;gap:5px}.hk-optimizer-result li{display:flex;justify-content:space-between;gap:8px;padding:6px 8px;border-radius:8px;background:#111c2b;font-size:11px}.hk-optimizer-result li strong.positive{color:#6ee7a8}.hk-optimizer-result li strong.negative{color:#ff8792}.hk-optimizer-safety{padding:8px;border-radius:9px;background:#10281f;color:#6ee7a8}.hk-optimizer-safety.blocked{background:#301820;color:#ff8792}.hk-optimizer-flow{display:flex;align-items:center;gap:5px;overflow-x:auto;padding:4px 0}.hk-optimizer-flow .hk-icon{width:34px;height:34px;flex-basis:34px}@media(max-width:620px){.hk-optimizer-controls,.hk-optimizer-actions{grid-template-columns:1fr}.hk-optimizer-summary{grid-template-columns:1fr 1fr}.hk-optimizer-replaceable{grid-template-columns:1fr}}
      .hk-bonus-analyzer{margin:10px 0;padding:11px;border:1px solid #34445b;border-radius:14px;background:#0d1520}.hk-bonus-analyzer h3,.hk-bonus-analyzer h4{margin:4px 0 8px}.hk-bonus-analysis-list{display:grid;gap:6px}.hk-bonus-analysis-row{background:#111c2b;border:1px solid #2c3b50;border-radius:10px;padding:8px}.hk-bonus-analysis-row summary{display:grid;grid-template-columns:1fr auto;gap:3px 8px;cursor:pointer}.hk-bonus-analysis-row summary small{grid-column:1/3;color:#95a5bc}.hk-bonus-analysis-row>div{display:grid;gap:5px;margin-top:7px}.hk-bonus-source,.hk-limited-businesses>span{display:flex;align-items:center;gap:7px}.hk-bonus-source .hk-icon,.hk-limited-businesses .hk-icon{width:30px;height:30px;flex-basis:30px}.hk-best-business{display:flex;align-items:center;gap:10px;background:#10281f;border:1px solid #286148;border-radius:11px;padding:9px}.hk-best-business span{display:grid;gap:3px}.hk-best-business small{color:#b5c2d4}.hk-limited-businesses{display:flex;gap:8px;overflow-x:auto}.hk-limited-businesses>span{min-width:150px;background:#301820;border-radius:9px;padding:6px;color:#ffb0b7}
      .hk-resource-type-tabs{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-bottom:14px}.hk-resource-type-tabs button{display:grid;gap:3px;padding:11px 8px;border:1px solid #40516a;border-radius:12px;background:#101a28;color:#d7dfeb}.hk-resource-type-tabs button b{font-size:13px;overflow-wrap:anywhere}.hk-resource-type-tabs button small{color:#96a5ba}.hk-resource-type-tabs button.active{border-color:#ffad1f;background:#3a2b14;color:#ffe083;box-shadow:0 0 0 2px #ffad1f2b}.hk-resource-type-tabs button.active small{color:#ffd36a}.hk-resource-head{display:grid;grid-template-columns:minmax(190px,.8fr) minmax(260px,1.4fr) minmax(210px,.48fr);gap:10px;align-items:end}.hk-resource-head h3{margin:0}.hk-resource-head small{display:block;margin-top:4px;color:#96a5ba}.hk-resource-tiers{display:flex;flex-wrap:wrap;justify-content:center;gap:7px;align-self:center}.hk-resource-tiers button{min-width:42px;padding:9px 10px;border:1px solid #40516a;border-radius:50px;background:#101a28;color:#b8c5d8;font-weight:900}.hk-resource-tiers button.active{border-color:#ffad1f;background:#3a2b14;color:#ffe083;box-shadow:0 0 0 2px #ffad1f2b}.hk-resource-repeat{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:12px;padding:10px 12px;border:1px solid #304159;border-radius:10px;background:#101a28}.hk-resource-repeat select{min-width:90px}.hk-resource-maximum{width:100%;margin-top:8px}.hk-resource-buildings{display:grid;gap:10px;margin:12px 0}.hk-resource-building{padding:10px;border:1px solid #304159;border-radius:12px;background:#101a28}.hk-resource-building h4{margin:0 0 8px;color:#f4f7fb}.hk-resource-building h4 small{color:#ffe083}.hk-resource-task{display:grid;grid-template-columns:minmax(150px,1fr) minmax(210px,.9fr) 110px;gap:9px;align-items:center;padding:8px 0;border-top:1px solid #26364b}.hk-resource-task>div{display:grid;gap:3px}.hk-resource-task small{color:#96a5ba}.hk-resource-task.protected{opacity:.6}.hk-resource-task.protected button{border-color:#596578;background:#222c3a;color:#aeb8c8}.hk-resource-task button{padding:10px 6px;border-color:#d99d18;background:#3a2b14;color:#ffe083;font-weight:900}.hk-resource-cost{display:grid;gap:4px;justify-items:end}.hk-resource-balance{display:grid;grid-template-columns:25px auto 8px auto;gap:4px;align-items:center;font-size:10px;color:#aebbd0}.hk-resource-balance .hk-price-icon{width:25px;height:25px}.hk-resource-balance i{display:grid;font-style:normal}.hk-resource-balance em{font-style:normal;color:#748399}.hk-resource-balance b{font-size:12px;color:#f5f7fa}.hk-resource-balance.ok b{color:#72e8ae}.hk-resource-balance.short b{color:#ff8992}.hk-resource-buildings+.hk-primary{width:100%}@media(max-width:820px){.hk-resource-head{grid-template-columns:1fr}.hk-resource-tiers{justify-content:flex-start}}@media(max-width:620px){.hk-resource-type-tabs button{padding:9px 4px}.hk-resource-type-tabs button b{font-size:11px}.hk-resource-type-tabs button small{font-size:10px}.hk-resource-task{grid-template-columns:1fr 110px}.hk-resource-cost{grid-column:1/2;justify-items:start}.hk-resource-task button{grid-column:2;grid-row:1/3}}
      .hk-clan-head{display:grid;grid-template-columns:1fr minmax(170px,.5fr) 130px;gap:8px;align-items:end}.hk-clan-head h3{margin:0}.hk-clan-head small{color:#94a3b8}.hk-clan-head select{min-width:0;background:#0b111b;color:#fff;border:1px solid #3b4a61;border-radius:10px;padding:10px}.hk-clan-overall{border:1px solid #2d3d54;border-radius:12px;background:#0d1520;padding:10px;margin:10px 0}.hk-clan-overall summary{cursor:pointer;font-weight:900}.hk-clan-overall summary span{float:right;color:#6ee7a8}.hk-clan-branches{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:7px;margin:12px 0}.hk-clan-branch,.hk-clan-line{border:1px solid #34445b;border-radius:11px;background:#111a27;color:#d9e2ef;padding:8px;display:grid;place-items:center;gap:5px;min-width:0}.hk-clan-branch{height:72px;overflow:hidden}.hk-clan-branch.active,.hk-clan-line.active{border-color:#ffad1f;background:#3a2b14;color:#fff}.hk-clan-branch img{display:block;width:100%;height:100%;max-width:56px;max-height:56px;object-fit:contain}.hk-clan-matrix{display:grid;grid-template-columns:58px minmax(0,1fr);gap:10px}.hk-clan-matrix aside{display:grid;gap:7px;align-content:start}.hk-clan-line{width:58px;height:58px}.hk-clan-line img{width:42px;height:42px;object-fit:contain}.hk-clan-matrix>section{border:1px solid #2d3d54;border-radius:12px;background:#0d1520;padding:11px}.hk-clan-line-summary{display:grid;grid-template-columns:repeat(3,1fr);gap:7px}.hk-clan-line-summary span{display:grid;gap:3px;padding:8px;border-radius:9px;background:#111c2b;color:#9eabc0;font-size:10px}.hk-clan-line-summary b{font-size:14px;color:#ffe083}.hk-clan-players{display:grid;gap:6px;margin-top:10px}.hk-clan-player{display:flex;justify-content:space-between;gap:9px;padding:8px;border-radius:9px;background:#111c2b}.hk-clan-player span{color:#6ee7a8;font-weight:800}@media(max-width:620px){.hk-clan-head{grid-template-columns:1fr 1fr}.hk-clan-head>div{grid-column:1/3}.hk-clan-branches{grid-template-columns:repeat(5,minmax(0,1fr));gap:5px;overflow:visible}.hk-clan-branch{height:64px;padding:5px}.hk-clan-branch img{max-width:48px;max-height:48px}.hk-clan-matrix{grid-template-columns:58px minmax(0,1fr)}.hk-clan-line-summary{grid-template-columns:1fr 1fr}.hk-clan-line-summary span:last-child{grid-column:1/3}}
      .hk-pit-forecast{margin:10px 0;padding:10px;border:1px solid #304057;border-radius:12px;background:#0d1520}.hk-pit-forecast h4,.hk-pit-forecast p{margin:4px 0}.hk-pit-forecast p{color:#aebbd0}.hk-pit-forecast summary{cursor:pointer;font-weight:800;margin-top:8px;padding:8px 0}.hk-pit-targets{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin:8px 0}.hk-pit-targets>div{display:grid;gap:3px;padding:8px;border:1px solid #304057;border-radius:10px;background:#111c2b}.hk-pit-targets strong{font-size:14px;color:#ffe083}.hk-pit-targets small,.hk-pit-forecast td small{display:block;color:#9eabc0;font-size:9px}.hk-pit-table-wrap{overflow-x:auto}.hk-pit-forecast table{width:100%;min-width:580px;margin-top:6px;border-collapse:collapse}.hk-pit-forecast th,.hk-pit-forecast td{padding:6px 8px;border-bottom:1px solid #28364a;text-align:left;vertical-align:top}.hk-pit-forecast thead th{position:sticky;top:0;background:#121d2c;color:#ffe083}.hk-pit-forecast tbody th{color:#ffe083}@media(max-width:620px){.hk-pit-targets{grid-template-columns:1fr}.hk-pit-forecast table{font-size:10px}}
      .hk-fair-types{display:flex;gap:9px;overflow-x:auto;padding:3px 1px 10px}.hk-fair-type{min-width:92px;border:1px solid #304057;background:#121a26;color:white;border-radius:14px;padding:8px;display:flex;flex-direction:column;align-items:center;gap:5px}.hk-fair-type.selected{border-color:#ffad1f;background:#2a2418}.hk-fair-icon{width:58px;height:58px;object-fit:contain}.hk-fair-type span,.hk-lot span{display:flex;align-items:center;justify-content:center;gap:4px}.hk-price-icon{width:22px;height:22px;object-fit:contain}.hk-fair-lots{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.hk-lot{position:relative;border:1px solid #2d3b50;background:#121a26;color:white;border-radius:15px;padding:10px 6px;display:flex;flex-direction:column;align-items:center;gap:4px}.hk-lot.selected{border:2px solid #3ee0a4;background:#173128}.hk-lot.locked{opacity:.48}.hk-lot small{color:#ff8792}.hk-fair-controls{display:grid;grid-template-columns:1fr 90px;gap:9px;align-items:center}.hk-fair-controls input[type=number],.hk-fair-controls select{background:#0b111b;color:white;border:1px solid #3b4a61;border-radius:10px;padding:10px;min-width:0}.hk-check{display:flex;gap:8px;align-items:center;margin:12px 0}.hk-check input{width:22px;height:22px}
      .hk-fair-currencies{display:flex;gap:7px;overflow-x:auto;padding:0 0 11px}.hk-fair-currencies button{border:1px solid #304057;background:#121a26;color:white;border-radius:11px;padding:7px 9px;display:flex;align-items:center;gap:5px;white-space:nowrap}.hk-fair-currencies button.selected{border-color:#ffad1f;background:#2a2418}.hk-fair-currencies span{font-size:12px}.hk-fair-bonus-lots{margin:9px 0;padding:10px;border:1px solid #304057;border-radius:11px;background:#101a28;display:grid;grid-template-columns:minmax(150px,1fr) auto;align-items:center;gap:8px}.hk-fair-bonus-lots>div{display:flex;gap:8px;flex-wrap:wrap}.hk-fair-bonus-lots .hk-check{margin:0;padding:7px 10px;border:1px solid #ffad1f;border-radius:9px;background:#3a2b14;color:#ffe083}.hk-fair-bonus-lots .hk-check.unavailable{opacity:.38;border-color:#4a5668;background:#192331;color:#9ba8ba}
      #hk-fair-slot-rules{margin:10px 0;padding:11px;background:#0d1520;border:1px solid #2a374a;border-radius:13px}#hk-fair-slot-rules h3{margin-top:0}.hk-slot-rule{display:grid;grid-template-columns:74px 1fr;gap:9px;align-items:center;padding:9px 0;border-top:1px solid #223046}.hk-slot-product{display:flex;align-items:center;gap:5px}.hk-slot-buttons{display:grid;grid-template-columns:repeat(2,minmax(80px,1fr));gap:7px}.hk-slot-buttons button{border:1px solid #3a4a61;border-radius:10px;background:#172130;color:#9eacc0;padding:10px 5px;font-weight:800}.hk-slot-buttons button.selected{border-color:#ffad1f;background:#3a2b14;color:#fff}.hk-slot-buttons button.vip{border-color:#9e7bff;color:#dbcfff}.hk-slot-buttons button.vip.selected{background:#34255b;border-color:#c3a7ff;color:#fff}.hk-slot-buttons button:disabled{opacity:.35}
      .hk-shop-tabs,.hk-shop-groups{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin:10px 0}.hk-shop-tabs button,.hk-shop-groups button{border:1px solid #34445b;border-radius:10px;background:#182230;color:#aebbd0;padding:10px 4px;font-size:12px;font-weight:800}.hk-shop-tabs button.active,.hk-shop-groups button.active{border-color:#ffad1f;background:#3a2b14;color:#fff}.hk-shop-lots{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.hk-shop-lot{position:relative;border:1px solid #2d3b50;background:#121a26;color:white;border-radius:15px;padding:10px 6px;display:flex;flex-direction:column;align-items:center;gap:5px}.hk-shop-lot.selected{border:2px solid #3ee0a4;background:#173128}.hk-shop-lot.locked{opacity:.45}.hk-shop-lot span{display:flex;align-items:center;gap:4px}.hk-shop-lot small{color:#aab7ca}.hk-shop-lot.locked small{color:#ff8792}.hk-shop-pick{width:100%;display:flex;flex-direction:column;align-items:center;gap:5px}.hk-shop-pick>input{position:absolute;top:8px;left:8px;width:21px;height:21px}.hk-shop-quantity{display:grid;grid-template-columns:1fr minmax(72px,100px) 48px;align-items:center;gap:5px;width:100%;font-size:11px}.hk-shop-quantity input{min-width:0;width:100%;box-sizing:border-box;background:#0b111b;color:#fff;border:1px solid #43536d;border-radius:8px;padding:7px 4px;text-align:center}.hk-shop-quantity button{padding:7px 3px;border:1px solid #b67b12;border-radius:8px;background:#3a2b14;color:#ffd76b;font-weight:900}.hk-premium-mark{position:absolute;right:7px;top:7px;font-style:normal;font-size:17px}.hk-lot.premium,.hk-shop-lot.premium{border-color:#9e7bff;box-shadow:inset 0 0 0 1px #9e7bff55}.hk-lot.premium.selected,.hk-shop-lot.premium.selected{border-color:#d2b7ff;background:#302453}#hk-shop-summary img{vertical-align:middle}
      .hk-recipe-tabs{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin-bottom:12px}.hk-recipe-tabs button{border:1px solid #34445b;border-radius:11px;background:#182230;color:#aebbd0;padding:11px 4px;font-size:12px;font-weight:800}.hk-recipe-tabs button.active{border-color:#ffad1f;background:#3a2b14;color:#fff}.hk-recipe-pane{display:none}.hk-recipe-pane.active{display:block}.hk-recipe-plans{display:grid;gap:9px;margin:10px 0}.hk-recipe-row{width:100%;display:grid;grid-template-columns:minmax(115px,1.15fr) 82px minmax(150px,1.25fr) minmax(135px,1fr);gap:10px;align-items:center;text-align:left;color:#f6f8fc;background:#111a27;border:1px solid #35445a;border-left:4px solid var(--recipe-rank);border-radius:14px;padding:10px}.hk-recipe-row:active{transform:scale(.995)}.hk-recipe-id{font-size:10px;color:#93a4bd;overflow-wrap:anywhere}.hk-recipe-result{position:relative;display:grid;justify-items:center;gap:2px}.hk-recipe-result .hk-icon{width:58px;height:58px}.hk-recipe-result small{color:#aebbd0}.hk-rank-badge{position:absolute;left:2px;bottom:18px;background:var(--recipe-rank);color:#111;padding:1px 5px;border-radius:5px;font-size:11px}.hk-recipe-bonuses,.hk-recipe-components,.hk-detail-bonuses{display:grid;gap:6px}.hk-recipe-bonuses span,.hk-detail-bonuses span{display:flex;align-items:center;gap:4px;font-size:11px}.hk-bonus-icon{width:20px;height:20px;object-fit:contain}.hk-component-group{display:flex;align-items:center;gap:5px;font-size:10px}.hk-component-group b{background:var(--rank);color:#111;border-radius:4px;padding:2px 5px}.hk-detail-backdrop{position:fixed;inset:0;z-index:2147483647;background:#02060dcc;display:flex;align-items:center;justify-content:center;padding:20px}.hk-detail-card{position:relative;width:min(480px,100%);max-height:80vh;overflow:auto;background:#111a27;border:1px solid #35445a;border-top:4px solid var(--recipe-rank);border-radius:18px;padding:18px;color:white}.hk-detail-close{position:absolute;right:10px;top:8px;background:#26364d;color:white;border:0;border-radius:9px;font-size:24px;width:38px;height:38px}.hk-detail-title{display:flex;align-items:center;gap:12px;padding-right:42px}.hk-detail-title .hk-icon{width:72px;height:72px}.hk-detail-title span{display:grid;gap:5px}.hk-detail-title small,.hk-recipe-row small{color:#aebbd0}.hk-bureau-sizes{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0}.hk-bureau-sizes button{border:1px solid #35445a;border-radius:11px;background:#111a27;color:white;padding:9px;display:flex;align-items:center;justify-content:center;gap:7px}.hk-bureau-sizes button.active{border-color:#ffad1f;background:#3a2b14}.hk-bureau-sizes span{display:flex;align-items:center;gap:4px}.hk-bureau-list{display:grid;gap:8px;margin:10px 0}.hk-bureau-item{display:grid;grid-template-columns:48px 1fr 64px;align-items:center;gap:9px;border:1px solid #2d3b50;border-radius:13px;background:#111a27;padding:8px}.hk-bureau-item.selected{border-color:#ffad1f;background:#2a2418}.hk-bureau-item span{display:flex;flex-direction:column}.hk-bureau-item small{color:#aebbd0}.hk-bureau-item input{min-width:0;width:100%;background:#0b111b;color:white;border:1px solid #43536d;border-radius:9px;padding:8px;text-align:center}
      .hk-recipe-ways{display:grid;gap:9px;padding:10px}.hk-recipe-way{display:grid;grid-template-columns:28px minmax(0,1fr);align-items:center;gap:8px;border:1px solid #29394f;border-radius:12px;background:#0c1420;padding:8px}.hk-recipe-way-number{display:grid;place-items:center;width:25px;height:25px;border-radius:50%;background:var(--recipe-rank);color:#10151d}.hk-recipe-way-flow{display:flex;align-items:center;gap:8px;overflow-x:auto;padding:2px 0}.hk-recipe-step{position:relative;flex:0 0 78px;display:grid;place-items:center;border:1px solid #35445a;border-bottom:3px solid var(--rank);border-radius:10px;background:#111a27;color:white;padding:6px}.hk-recipe-step .hk-icon{width:48px;height:48px}.hk-recipe-step .hk-rank-badge{bottom:16px;left:1px}.hk-recipe-step .hk-component-order{position:absolute;right:3px;top:3px;z-index:2;background:#25344a;border-radius:5px;padding:1px 4px;font-size:9px}.hk-recipe-plus{flex:0 0 auto;color:#ffbd3f;font-size:22px}.hk-recipe-result-group>.hk-recipe-row{grid-template-columns:82px minmax(150px,1fr) minmax(150px,.8fr)}
      .hk-recipe-step .hk-rank-badge{background:var(--rank)}
      @media(max-width:620px){.hk-recipe-row{grid-template-columns:70px 1fr 1.25fr}.hk-recipe-id{display:none}.hk-recipe-components{grid-column:2/4;border-top:1px solid #25344a;padding-top:7px}.hk-recipe-result-group>.hk-recipe-row{grid-template-columns:70px 1fr}.hk-recipe-result-group .hk-recipe-toggle{grid-column:1/3;border-top:1px solid #25344a;padding-top:7px}.hk-recipe-way{grid-template-columns:24px minmax(0,1fr);padding:6px}.hk-recipe-way-number{width:22px;height:22px;font-size:11px}}
      .hk-recipe-group{border:1px solid #35445a;border-left:4px solid var(--recipe-rank);border-radius:14px;background:#111a27;overflow:hidden}.hk-recipe-group>.hk-recipe-row{grid-template-columns:78px minmax(0,1fr) 120px;border:0;border-left:0;border-radius:0;cursor:pointer;list-style:none}.hk-recipe-group>.hk-recipe-row::-webkit-details-marker{display:none}.hk-recipe-toggle{display:grid;gap:4px;text-align:right}.hk-recipe-toggle small{font-size:9px}.hk-recipe-group[open] .hk-recipe-toggle b{color:#ffad1f}.hk-recipe-component-list{display:grid;gap:7px;padding:0 9px 10px 18px;border-top:1px solid #25344a}.hk-recipe-component{position:relative;width:100%;display:grid;grid-template-columns:65px minmax(0,1fr);gap:10px;align-items:center;text-align:left;color:#f6f8fc;background:#0d1521;border:1px solid #2b394d;border-left:3px solid var(--recipe-rank);border-radius:11px;padding:8px;margin-top:8px}.hk-recipe-component .hk-icon{width:52px;height:52px}.hk-component-order{position:absolute;left:-15px;top:50%;transform:translateY(-50%);display:grid;place-items:center;width:24px;height:24px;border-radius:50%;background:#ffad1f;color:#16100a;font-size:11px}.hk-recipe-component-list>.hk-muted{margin:10px}.hk-recipe-component .hk-rank-badge{bottom:16px}
      @media(max-width:620px){.hk-recipe-group>.hk-recipe-row{grid-template-columns:67px minmax(0,1fr)}.hk-recipe-toggle{grid-column:1/3;border-top:1px solid #25344a;padding-top:7px;text-align:left}.hk-recipe-component{grid-template-columns:58px minmax(0,1fr)}}
      .hk-map-source-tabs{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin:9px 0 12px}.hk-map-source-tabs button{border:1px solid #34445b;border-radius:11px;background:#182230;color:#aebbd0;padding:11px 5px;font-size:12px;font-weight:800}.hk-map-source-tabs button.active{border-color:#ffad1f;background:#3a2b14;color:#fff}.hk-map-controls{display:grid;grid-template-columns:1fr 120px;gap:7px}.hk-map-controls input,.hk-map-controls select,.hk-map-filters select{min-width:0;background:#0b111b;color:white;border:1px solid #3b4a61;border-radius:10px;padding:10px}.hk-map-list{display:grid;gap:7px;margin-top:10px}.hk-map-row{display:grid;grid-template-columns:1.2fr 54px repeat(3,1fr) 58px 48px;gap:6px;align-items:center;text-align:left;background:#111a27;color:white;border:1px solid #35445a;border-radius:11px;padding:10px;font-size:10px}.hk-map-row>b{font-size:12px;color:#ffe083}.hk-map-row strong{color:#35df9e}.hk-progress{background:#35df9e;color:#082117;border-radius:12px;padding:4px;text-align:center;font-weight:900}.hk-map-filters{display:grid;grid-template-columns:repeat(2,1fr);gap:7px;margin:10px 0}.hk-map-legend{display:flex;gap:8px;flex-wrap:wrap;font-size:10px;color:#9eabc0;margin:8px 0}.hk-map-legend span{display:flex;align-items:center;gap:4px}.hk-map-dot{width:10px;height:10px;border-radius:3px;display:inline-block}.hk-map-zoom{display:grid;grid-template-columns:44px 82px 44px;gap:6px;justify-content:end;margin:7px 0}.hk-map-zoom button{padding:8px 4px;font-weight:900}.hk-map-zoom #hk-map-zoom-value{color:#ffe083}.hk-map-visual{height:56vh;min-height:360px;max-height:650px;background:#080d14;border:1px solid #304057;border-radius:13px;overflow:hidden;touch-action:none}.hk-map-visual svg{display:block;width:100%;height:100%;touch-action:none;transform-origin:50% 50%;will-change:transform}.hk-map-shape{cursor:pointer;transition:opacity .15s,stroke-width .15s}.hk-map-shape.dim{opacity:.055;pointer-events:none}.hk-map-shape.match{opacity:.94}.hk-map-shape.selected{stroke:#fff!important;stroke-width:3.2!important;opacity:1}.hk-map-selected{display:grid;grid-template-columns:1.1fr 1fr 55px;gap:7px;align-items:center;margin-top:8px;padding:10px;background:#101927;border:1px solid #304057;border-radius:11px}.hk-map-selected small{grid-column:1/4;color:#93a3b8}.hk-map-selected strong{color:#6deaff}.hk-map-match-count{font-size:11px;color:#9eabc0;margin:6px 0}
      @media(max-width:620px){.hk-map-row{grid-template-columns:1fr 45px 54px}.hk-map-row span:nth-of-type(2),.hk-map-row span:nth-of-type(3){display:none}.hk-map-row strong{grid-column:3}.hk-map-row .hk-progress{grid-column:2}.hk-map-building{grid-template-columns:1fr 55px}.hk-map-building>span{grid-column:1}.hk-map-building small{grid-column:1/3}}
    `;
    document.head.appendChild(style);
    const NAV_GROUPS = [
      {id:'today',label:'navToday',hint:'navTodayHint',image:'today.png',modules:[{page:'daily',ru:'Сегодня',en:'Today'}]},
      {id:'battles',label:'navBattles',hint:'navBattlesHint',image:'clan-war.png',modules:[{page:'pit',ru:'Ямы',en:'Pits'},{page:'bosses',ru:'Боссы',en:'Bosses'},{planned:true,ru:'Районы',en:'Neighborhoods'}]},
      {id:'city',label:'navCity',hint:'navCityHint',image:'maps.png',modules:[{page:'maps',ru:'Карты',en:'Maps'},{page:'resources',ru:'Ресурсы',en:'Resources'},{page:'buildings',ru:'Здания',en:'Buildings'},{page:'explore',ru:'Исследование',en:'Explore'}]},
      {id:'business',label:'navBusiness',hint:'navBusinessHint',image:'businesses.png',modules:[{page:'business',ru:'Бизнесы',en:'Businesses'},{page:'recipes',ru:'Рецепты',en:'Recipes'},{page:'routines',ru:'Авто-рутины',en:'Auto routines'}]},
      {id:'growth',label:'navGrowth',hint:'navGrowthHint',icon:'📈',modules:[{page:'growth',ru:'Обзор',en:'Overview'},{page:'growth-hamsters',ru:'Хомяки',en:'Hamsters'},{page:'growth-generals',ru:'Генералы',en:'Generals'}]},
      {id:'trade',label:'navTrade',hint:'navTradeHint',image:'fair.png',modules:[{page:'fair',ru:'Ярмарка',en:'Fair'},{page:'shop',ru:'Магазин',en:'Shop'},{page:'fair-regular',ru:'Обычная ярмарка',en:'Regular Fair'}]},
      {id:'clan',label:'navClan',hint:'navClanHint',image:'clan.png',modules:[{page:'clan',ru:'Навыки',en:'Skills'},{page:'wars',ru:'Войны',en:'Wars'},{planned:true,ru:'Охота на крыс',en:'Rat Hunt'}]}
    ];
    const menuTabs = NAV_GROUPS.map((group,index)=>`<button class="hk-tab${index===0?' active':''}" data-group="${group.id}" data-nav-ru="${escapeHtml(TEXT.ru[group.label])}" data-nav-en="${escapeHtml(TEXT.en[group.label])}"><span class="hk-tab-icon">${group.image?`<img src="${MENU_ICONS_BASE}/${group.image}" alt="" onerror="this.replaceWith(document.createTextNode('${group.icon||'•'}'))">`:(group.icon||'•')}</span><span class="hk-tab-label">${escapeHtml(tr(group.label))}</span><span class="hk-tab-hint">${escapeHtml(tr(group.hint))}</span></button>`).join('');
    root = document.createElement('div'); root.id = 'hk-mobile-root'; root.dataset.hkRevision = HK_CORE_REVISION;
    root.innerHTML = `<button id="hk-fab">HK</button><div id="hk-panel" class="hk-locked">
      <div id="hk-watermark" aria-hidden="true"></div><div class="hk-head"><h2>Hamster King Mobile <small style="font-size:12px;color:#9aa8bc">v${VERSION}</small></h2><div class="hk-lang"><button data-lang="ru" aria-label="Русский">🇷🇺</button><button data-lang="en" aria-label="English">🇬🇧</button></div><button class="hk-close">×</button></div>
      <button id="hk-donation" class="hk-donation">❤️ <span data-i18n="donation">${tr('donation')}</span></button>
      <div id="hk-license-gate" class="hk-license" data-i18n="checkingLicense">${tr('checkingLicense')}</div>
      <div id="hk-health" class="hk-health">
        <div class="hk-health-chip" data-health="game"><b>${either('Игра','Game')}</b><small>${either('ожидание','waiting')}</small></div>
        <div class="hk-health-chip" data-health="auth"><b>${either('Авторизация','Auth')}</b><small>${either('ожидание','waiting')}</small></div>
        <div class="hk-health-chip" data-health="license"><b>${either('Лицензия','License')}</b><small>${either('ожидание','waiting')}</small></div>
        <div class="hk-health-chip" data-health="server"><b>${either('Сервер','Server')}</b><small>${either('ожидание','waiting')}</small></div>
      </div>
      <div class="hk-health-actions"><button id="hk-health-check" class="hk-secondary">${either('Проверить связь','Check connection')}</button><button id="hk-diagnostic">${either('Диагностика','Diagnostics')}</button></div>
      <div id="hk-update-banner" class="hk-update"></div>
      <div class="hk-tabs">${menuTabs}</div>
      <div id="hk-subnav" class="hk-subnav"></div>
      <div id="hk-runner" class="hk-runner"><div class="hk-runner-head"><b id="hk-runner-title"></b><span id="hk-runner-state" class="hk-runner-state"></span></div><div id="hk-runner-step" class="hk-runner-step"></div><div class="hk-runner-track"><div id="hk-runner-fill" class="hk-runner-fill"></div></div><div class="hk-runner-actions"><button id="hk-runner-pause" class="hk-secondary"></button><button id="hk-runner-stop" class="hk-danger"></button></div></div>
      <div class="hk-page active" data-content="daily">
        <div class="hk-cardbox"><h3 data-i18n="dailyTasks">${tr('dailyTasks')}</h3><div class="hk-toolbar"><button id="hk-daily-refresh" class="hk-secondary" data-i18n="dailyRefresh">${tr('dailyRefresh')}</button><button id="hk-daily-clear" data-i18n="dailyClear">${tr('dailyClear')}</button></div><div id="hk-daily-tasks"></div><button id="hk-daily-run" class="hk-primary" data-i18n="dailyRun" disabled>${tr('dailyRun')}</button></div>
      </div>
      <div class="hk-page" data-content="resources">
        <div id="hk-resource-content" class="hk-cardbox"></div>
      </div>
      <div class="hk-page" data-content="bosses"><div id="hk-boss-content" class="hk-cardbox"><h3>${either('Боссы','Bosses')}</h3><p class="hk-muted">${either('Откройте вкладку, чтобы считать состояние босса.','Open this tab to read boss state.')}</p></div></div>
          <div class="hk-page" data-content="pit">
        <div class="hk-cardbox"><div class="hk-grid">
          <label data-i18n="targetRound">${tr('targetRound')}</label><input id="hk-target" type="number" min="1" value="${settings.target}">
          <label data-i18n="delay">${tr('delay')}</label><input id="hk-interval" type="number" min="0.7" step="0.1" value="${settings.interval}">
          <label data-i18n="activationTokens">${tr('activationTokens')}</label><input id="hk-activation-limit" type="number" min="0" value="${settings.activationLimit}">
          <label data-i18n="restoreTokens">${tr('restoreTokens')}</label><input id="hk-restore-limit" type="number" min="0" value="${settings.restoreLimit}">
          <label data-i18n="allowTokens">${tr('allowTokens')}</label><input id="hk-allow-tokens" type="checkbox" ${settings.allowTokens ? 'checked' : ''}>
          <label data-i18n="pitCollectOnly">${tr('pitCollectOnly')}</label><input id="hk-pit-collect-only" type="checkbox" ${settings.collectOnly ? 'checked' : ''}>
        </div><div id="hk-pit-live" class="hk-live">${tr('round')}: —</div><section id="hk-pit-forecast" class="hk-pit-forecast"></section>
        <button id="hk-pit-start" class="hk-primary" data-i18n="startBattle">${tr('startBattle')}</button><button id="hk-pit-stop" class="hk-danger" data-i18n="stop" disabled>${tr('stop')}</button>
        <button id="hk-export" class="hk-secondary" data-i18n="exportCsv">${tr('exportCsv')}</button></div>
      </div>
      <div class="hk-page" data-content="routines">
        <div id="hk-routines-content" class="hk-cardbox"></div>
      </div>
      <div class="hk-page" data-content="business">
        <div class="hk-cardbox"><div class="hk-toolbar"><button id="hk-refresh-game" data-i18n="refreshGame">${tr('refreshGame')}</button><span id="hk-connect">${tr('waiting')}</span></div>
        <div class="hk-business-tabs"><button class="hk-business-tab active" data-business-tab="regular" data-i18n="businessRegular">${tr('businessRegular')}</button><button class="hk-business-tab" data-business-tab="optimizer" data-i18n="businessOptimizer">${tr('businessOptimizer')}</button></div>
        <div class="hk-business-pane active" data-business-pane="regular"><div class="hk-toolbar"><select id="hk-preset"><option>${tr('savedSets')}</option></select><button id="hk-save-preset" data-i18n="saveNew">${tr('saveNew')}</button><button id="hk-delete-preset" data-i18n="delete">${tr('delete')}</button></div>
        <div class="hk-toolbar"><select id="hk-remove-tier"></select><button id="hk-select-remove" data-i18n="selectAll">${tr('selectAll')}</button></div>
        <div class="hk-toolbar"><select id="hk-insert-tier"></select></div>
        <div id="hk-business-lists"></div><div id="hk-plan" class="hk-cardbox"></div></div>
        <div class="hk-business-pane" data-business-pane="optimizer"><section class="hk-optimizer"><h3 data-i18n="optimizer">${tr('optimizer')}</h3><div class="hk-optimizer-controls"><label><span data-i18n="optimizerGoal">${tr('optimizerGoal')}</span><select id="hk-optimizer-goal"><option value="pit" data-i18n="optimizerPit">${tr('optimizerPit')}</option><option value="income" data-i18n="optimizerIncome">${tr('optimizerIncome')}</option><option value="energy" data-i18n="optimizerEnergy">${tr('optimizerEnergy')}</option><option value="buildings" data-i18n="optimizerBuildings">${tr('optimizerBuildings')}</option></select></label></div><div class="hk-optimizer-filter"><b data-i18n="optimizerRemoveTiers">${tr('optimizerRemoveTiers')}</b><div id="hk-optimizer-remove-tiers" class="hk-optimizer-tiers"></div></div><div class="hk-optimizer-filter"><b data-i18n="optimizerInsertTiers">${tr('optimizerInsertTiers')}</b><div id="hk-optimizer-insert-tiers" class="hk-optimizer-tiers"></div></div><details class="hk-optimizer-filter hk-optimizer-collapsible" data-optimizer-section="replaceable" ${optimizerSectionOpen('replaceable')?'open':''}><summary><b data-i18n="optimizerReplaceable">${tr('optimizerReplaceable')}</b></summary><small data-i18n="optimizerReplaceHint">${tr('optimizerReplaceHint')}</small><div id="hk-optimizer-replaceable" class="hk-optimizer-replaceable"></div></details><details class="hk-optimizer-filter hk-optimizer-collapsible" data-optimizer-section="stock" ${optimizerSectionOpen('stock')?'open':''}><summary><b data-i18n="optimizerStockAllowed">${tr('optimizerStockAllowed')}</b></summary><small data-i18n="optimizerStockHint">${tr('optimizerStockHint')}</small><div id="hk-optimizer-stock-allowed" class="hk-optimizer-replaceable"></div></details><div class="hk-optimizer-actions"><button id="hk-optimizer-calculate" class="hk-secondary" data-i18n="optimizerCalculate">${tr('optimizerCalculate')}</button><button id="hk-optimizer-restore" data-i18n="optimizerRestore">${tr('optimizerRestore')}</button></div><div id="hk-optimizer-result" class="hk-optimizer-result"><p class="hk-muted">${tr('optimizerNoPlan')}</p></div></section>
        <section class="hk-bonus-analyzer"><h3 data-i18n="bonusAnalyzer">${tr('bonusAnalyzer')}</h3><div id="hk-bonus-analyzer-result"><p class="hk-muted">${tr('optimizerNoPlan')}</p></div></section></div></div>
      </div>
      <div class="hk-page" data-content="clan">
        <div id="hk-clan-content" class="hk-cardbox"><h3>${either('Навыки клана','Clan skills')}</h3><p class="hk-muted">${either('Данные ещё не считаны','No data has been read yet')}</p></div>
      </div>
      <div class="hk-page" data-content="fair">
        <div class="hk-cardbox"><button id="hk-fair-load" class="hk-secondary" data-i18n="loadFair">${tr('loadFair')}</button>
          <div class="hk-toolbar" style="margin-top:10px"><select id="hk-fair-preset"><option value="">${tr('fairSavedSettings')}</option></select><button id="hk-fair-save-preset" data-i18n="saveSetting">${tr('saveSetting')}</button></div>
          <div class="hk-toolbar"><button id="hk-fair-update-preset" data-i18n="updateSetting">${tr('updateSetting')}</button><button id="hk-fair-delete-preset" data-i18n="delete">${tr('delete')}</button></div>
          <h3 data-i18n="chooseFair">${tr('chooseFair')}</h3><div id="hk-fair-types" class="hk-fair-types"><p class="hk-muted">${tr('readFirst')}</p></div>
          <div class="hk-toolbar"><input id="hk-fair-search" data-i18n-placeholder="searchLot" placeholder="${tr('searchLot')}"></div>
          <div id="hk-fair-currencies" class="hk-fair-currencies"></div>
          <h3 data-i18n="choosePurchases">${tr('choosePurchases')}</h3><div id="hk-fair-lots" class="hk-fair-lots"></div>
          <div id="hk-fair-selected" class="hk-live">${tr('selectedLots',{n:0})}</div>
          <div id="hk-fair-slot-rules" style="display:none"></div>
          <div class="hk-fair-controls"><label data-i18n="fairExactLots">${tr('fairExactLots')}</label><select id="hk-fair-exact-lots"><option value="0">${tr('no')}</option><option value="3">3</option><option value="6">6</option><option value="9">9</option></select></div>
          <div id="hk-fair-bonus-lots" class="hk-fair-bonus-lots"></div>
          <div class="hk-fair-controls"><label data-i18n="totalPurchases">${tr('totalPurchases')}</label><input id="hk-fair-buy-limit" type="number" min="1" max="999" value="1">
            <label data-i18n="maxRerolls">${tr('maxRerolls')}</label><input id="hk-fair-reroll-limit" type="number" min="0" max="10000" value="50"></div>
          <label class="hk-check"><input id="hk-fair-premium-reroll" type="checkbox"><span data-i18n="allowDiamonds">${tr('allowDiamonds')}</span></label>
          <button id="hk-fair-start" class="hk-primary" data-i18n="findBuy" disabled>${tr('findBuy')}</button><button id="hk-fair-stop" class="hk-danger" data-i18n="stop" disabled>${tr('stop')}</button>
          <p class="hk-muted" data-i18n="fairWarning">${tr('fairWarning')}</p>
        </div>
      </div>
      <div class="hk-page" data-content="shop">
        <div class="hk-cardbox"><h3 data-i18n="shop">${tr('shop')}</h3>
          <div class="hk-shop-tabs"><button class="active" data-shop-section="regular" data-i18n="regularShop">${tr('regularShop')}</button><button data-shop-section="ordinary" data-i18n="ordinaryShop">${tr('ordinaryShop')}</button><button data-shop-section="clan" data-i18n="clanShop">${tr('clanShop')}</button></div>
          <div id="hk-shop-groups" class="hk-shop-groups" style="display:none"><button class="active" data-shop-group="resources" data-i18n="resourcesShop">${tr('resourcesShop')}</button><button data-shop-group="renovation" data-i18n="renovationShop">${tr('renovationShop')}</button><button data-shop-group="invest" data-i18n="investShop">${tr('investShop')}</button></div>
          <button id="hk-shop-load" class="hk-secondary" data-i18n="readShop">${tr('readShop')}</button>
          <button id="hk-shop-select" class="hk-secondary" data-i18n="selectAvailable">${tr('selectAvailable')}</button>
          <div id="hk-shop-cards" class="hk-shop-lots" style="margin-top:10px"><p class="hk-muted">${tr('shopReadFirst')}</p></div>
          <div id="hk-shop-summary" class="hk-live">${tr('selectedPurchases',{n:0})}</div>
          <button id="hk-shop-buy" class="hk-primary" data-i18n="buySelected" disabled>${tr('buySelected')}</button>
          <p class="hk-muted" data-i18n="shopWarning">${tr('shopWarning')}</p>
        </div>
      </div>
      <div class="hk-page" data-content="recipes">
        <div class="hk-cardbox"><div class="hk-recipe-tabs"><button class="active" data-recipe-pane="spin" data-i18n="recipeSpin">${tr('recipeSpin')}</button><button data-recipe-pane="database" data-i18n="recipeDatabase">${tr('recipeDatabase')}</button><button data-recipe-pane="bureau" data-i18n="projectBureau">${tr('projectBureau')}</button></div>
          <div class="hk-recipe-pane active" data-recipe-content="spin">
            <button id="hk-recipe-load" class="hk-secondary" data-i18n="readRecipes">${tr('readRecipes')}</button>
            <h3 data-i18n="currentRecipePlans">${tr('currentRecipePlans')}</h3><div id="hk-recipe-cards" class="hk-recipe-plans"><p class="hk-muted">${tr('recipeReadFirst')}</p></div>
            <div class="hk-grid"><label data-i18n="recipeAttempts">${tr('recipeAttempts')}</label><input id="hk-recipe-attempts" type="number" min="1" max="100" value="1"></div>
            <div id="hk-recipe-summary" class="hk-live">${tr('recipeReadFirst')}</div>
            <button id="hk-recipe-run" class="hk-primary" data-i18n="spinRecipes" disabled>${tr('spinRecipes')}</button><button id="hk-recipe-stop" class="hk-danger" data-i18n="stop" disabled>${tr('stop')}</button>
          </div>
          <div class="hk-recipe-pane" data-recipe-content="database">
            <button id="hk-recipe-db-load" class="hk-secondary" data-i18n="loadRecipeDatabase">${tr('loadRecipeDatabase')}</button>
            <div id="hk-recipe-db-count" class="hk-live">${tr('uniqueRecipes',{n:0})}</div><div id="hk-recipe-database" class="hk-recipe-plans"><p class="hk-muted">${tr('recipeDatabaseEmpty')}</p></div>
            <p class="hk-muted" data-i18n="recipeSharedHint">${tr('recipeSharedHint')}</p>
          </div>
          <div class="hk-recipe-pane" data-recipe-content="bureau">
            <button id="hk-bureau-load" class="hk-secondary" data-i18n="readBureau">${tr('readBureau')}</button>
            <h3 data-i18n="bureauSize">${tr('bureauSize')}</h3><div id="hk-bureau-sizes" class="hk-bureau-sizes"></div>
            <div class="hk-grid"><label data-i18n="bureauTier">${tr('bureauTier')}</label><select id="hk-bureau-tier"><option value="0">${tr('bureauAllTiers')}</option></select></div>
            <div id="hk-bureau-cards" class="hk-bureau-list"><p class="hk-muted">${tr('readBureau')}</p></div>
            <div class="hk-grid"><label data-i18n="bureauAttempts">${tr('bureauAttempts')}</label><input id="hk-bureau-attempts" type="number" min="1" max="100" value="1"></div>
            <div id="hk-bureau-summary" class="hk-live">${tr('bureauSelected',{n:0,max:2})}</div>
            <button id="hk-bureau-run" class="hk-primary" data-i18n="createBusinessPlan" disabled>${tr('createBusinessPlan')}</button>
            <p class="hk-muted" data-i18n="bureauHint">${tr('bureauHint')}</p>
          </div>
        </div>
      </div>
      <div class="hk-page" data-content="growth">
        <div class="hk-cardbox"><h3>${either('Развитие','Growth')}</h3><p class="hk-muted">${either('Живое состояние аккаунта загружается автоматически. Открытие вкладки ничего не покупает и не прокачивает.','Live account state loads automatically. Opening the tab never buys or upgrades anything.')}</p><div data-growth-summary></div></div>
        <div class="hk-cardbox"><h3>${either('Что выполнять','What to run')}</h3><div class="hk-growth-options">
          <label class="hk-growth-check"><span><b>${either('Подготовка','Preparation')}</b><small>${either('Контракты → шары → коробки','Contracts → balls → boxes')}</small></span><input id="hk-growth-run-prep" type="checkbox"></label>
          <label class="hk-growth-check"><span><b>${either('Генералы','Generals')}</b><small>${either('Лучшее Power / Pit Token','Best Power / Pit Token')}</small></span><input id="hk-growth-run-generals" type="checkbox"></label>
          <label class="hk-growth-check"><span><b>${either('Хомяки','Hamsters')}</b><small>${either('Копии → редкость → уровни','Copies → rarity → levels')}</small></span><input id="hk-growth-run-hamsters" type="checkbox"></label>
        </div></div>
        <div class="hk-cardbox"><h3>${either('Подготовка','Preparation')}</h3><div class="hk-growth-options">
          <label class="hk-growth-check"><span><b>${either('Купить все контракты Генералов','Buy all General contracts')}</b><small>${either('Только контракты за фрагменты. Валюты/PREM не расходуются.','Fragment-only contracts. No currency/PREM spending.')}</small></span><input id="hk-growth-contracts" type="checkbox"></label>
          <label class="hk-growth-check"><span><b>${either('Открыть все шары','Open all balls')}</b><small>${either('Все распознанные шары Хомяков/Генералов','All recognized Hamster/General balls')}</small></span><input id="hk-growth-balls" type="checkbox"></label>
          <label class="hk-growth-check"><span><b>${either('Открыть все коробки','Open all boxes')}</b><small>${either('Коробки/lootbox/chest, кроме пассивного дохода','Boxes/lootboxes/chests except passive-income boxes')}</small></span><input id="hk-growth-boxes" type="checkbox"></label>
        </div></div>
        <div class="hk-cardbox"><div data-growth-plan></div><button class="hk-primary" data-growth-action="all">${either('Запустить полный план','Run full plan')}</button></div>
      </div>
      <div class="hk-page" data-content="growth-hamsters">
        <div class="hk-cardbox"><h3>${either('Хомяки','Hamsters')}</h3><p class="hk-muted">${either('Состояние, магазин и справочник Хомяков считываются автоматически. Максимальный уровень определяется из live-данных каждого Хомяка.','State, shop and Hamster metadata are read automatically. Maximum level is derived from each Hamster’s live data.')}</p><div data-growth-summary></div>
          <div class="hk-growth-options">
            <label class="hk-growth-option"><span><b>${either('Бюджет Крышек','Caps budget')}</b><small>${either('Доля текущего баланса Крышек на фазу Хомяков','Share of current Caps balance for the Hamster phase')}</small></span><select id="hk-growth-caps-percent">${[10,20,30,40,50,60,70,80,90,100].map(v=>`<option value="${v}">${v}%</option>`).join('')}</select></label>
            <label class="hk-growth-option"><span><b>${either('Вес Mobster Pit','Mobster Pit weight')}</b><small>${either('Idol / Crypto / помощники Ямы. «—» = ×1','Idol / Crypto / Pit helpers. “—” = ×1')}</small></span><select id="hk-growth-hamster-weight">${[1,2,3,4,5,6,7,8].map(v=>`<option value="${v}">${v===1?'—':'×'+v}</option>`).join('')}</select></label>
            <label class="hk-growth-check"><span><b>${either('Hamster Copy Priority','Hamster Copy Priority')}</b><small>${either('Сначала докупает недостающие копии в заданном порядке, затем повышает редкость','Buys missing copies in the selected order, then upgrades rarity')}</small></span><input id="hk-growth-copy-enabled" type="checkbox"></label>
            <label class="hk-growth-check"><span><b>${either('Исключить Хомяков текущего события','Exclude current-event Hamsters')}</b><small>${either('Определяются автоматически через активное событие игры','Detected automatically from the active game event')}</small></span><input id="hk-growth-exclude-event" type="checkbox"></label>
          </div>
        </div>
        <div class="hk-cardbox"><div class="hk-growth-priority-head"><h3>${either('Приоритет копий','Copy Priority')}</h3><button class="hk-secondary" data-growth-action="reset-priority">${either('Сбросить','Reset')}</button></div><p class="hk-muted">${either('Порядок пар «есть / нужно». Стрелками меняется приоритет, «−» исключает пару.','Order of “owned / required” pairs. Arrows reorder; “−” removes a pair.')}</p><div id="hk-growth-copy-priority" class="hk-growth-priority-list"></div></div>
        <div class="hk-cardbox"><div data-growth-plan></div><button class="hk-primary" data-growth-action="hamsters">${either('Запустить Хомяков','Run Hamsters')}</button></div>
      </div>
      <div class="hk-page" data-content="growth-generals">
        <div class="hk-cardbox"><h3>${either('Генералы','Generals')}</h3><p class="hk-muted">${either('Перед каждым запуском баланс и доступные улучшения считываются заново.','Balance and available upgrades are read again before every run.')}</p><div data-growth-summary></div>
          <div class="hk-growth-options">
            <label class="hk-growth-option"><span><b>${either('Бюджет Pit Tokens','Pit Token budget')}</b><small>${either('Доля текущего баланса для Генералов','Share of current balance for Generals')}</small></span><select id="hk-growth-pit-percent">${[10,20,30,40,50,60,70,80,90,100].map(v=>`<option value="${v}">${v}%</option>`).join('')}</select></label>
            <label class="hk-growth-option"><span><b>${either('Level Up','Level Up')}</b><small>${either('×1 или ближайший шаг ×10, когда сервер его предлагает и бюджет позволяет','×1 or nearest ×10 when the server offers it and budget allows')}</small></span><select id="hk-growth-general-mode"><option value="x1">×1</option><option value="fast10">×10</option></select></label>
            <label class="hk-growth-option"><span><b>${either('Вес Mobster Pit','Mobster Pit weight')}</b><small>${either('Idol / Crypto / Pit General. «—» = ×1','Idol / Crypto / Pit General. “—” = ×1')}</small></span><select id="hk-growth-general-weight">${[1,2,3,4,5,6,7,8].map(v=>`<option value="${v}">${v===1?'—':'×'+v}</option>`).join('')}</select></label>
          </div>
        </div>
        <div class="hk-cardbox"><div data-growth-plan></div><button class="hk-primary" data-growth-action="generals">${either('Запустить Генералов','Run Generals')}</button></div>
      </div>
      <div class="hk-page" data-content="wars">
        <div id="hk-war-content" class="hk-cardbox"><h3>${either('Войны','Wars')}</h3><p class="hk-muted">${either('Откройте вкладку, чтобы считать текущую войну.','Open this tab to read the current war.')}</p></div>
      </div>
      <div class="hk-page" data-content="buildings">
        <div id="hk-buildings-content" class="hk-cardbox"><h3>${either('Здания','Buildings')}</h3></div>
      </div>
      <div class="hk-page" data-content="explore">
        <div id="hk-explore-content" class="hk-cardbox"><h3>${either('Исследование','Explore')}</h3></div>
      </div>
      <div class="hk-page" data-content="maps">
        <div id="hk-map-index" class="hk-cardbox"><h3 data-i18n="mapIndex">${tr('mapIndex')}</h3>
          <div class="hk-map-source-tabs"><button class="active" data-map-source="mine">${tr('myMaps')}</button><button data-map-source="uploaded">${tr('uploadedMaps')}</button></div>
          <div class="hk-map-controls"><input id="hk-map-search" data-i18n-placeholder="mapSearch" placeholder="${tr('mapSearch')}"><select id="hk-map-sort"><option value="rating">${tr('mapRating')}</option><option value="total_rooms">${tr('mapRooms')}</option><option value="progress">${tr('mapProgress')}</option><option value="city">${either('Город','City')}</option></select></div>
          <button id="hk-map-load" class="hk-secondary" style="display:none">${tr('refreshUploadedMaps')}</button><button id="hk-map-scan" class="hk-primary">${tr('scanAccountMaps')}</button>
          <div id="hk-map-list" class="hk-map-list"><p class="hk-muted">${either('Откройте индекс карт','Open the map index')}</p></div></div>
        <div id="hk-map-detail" class="hk-cardbox" style="display:none"><button id="hk-map-back" class="hk-secondary">← ${either('К индексу','Back to index')}</button><h3 id="hk-map-detail-title"></h3>
          <div class="hk-map-filters"><select id="hk-map-status-filter"><option value="all">${either('Все здания','All buildings')}</option><option value="opened">${either('Открытые','Opened')}</option><option value="unknown">${tr('mapUnexplored')}</option></select>
          <select id="hk-map-room-filter"><option value="all">${tr('mapRooms')}: ${tr('all')}</option><option value="0">0 💎</option><option value="1">1 💎</option><option value="2">2 💎</option><option value="3">3 💎</option><option value="4">4 💎</option><option value="5">5+ 💎</option></select>
          <select id="hk-map-type-filter"><option value="all">${either('Все типы','All types')}</option><option value="normal">${either('Обычные','Regular')}</option><option value="invest">${either('Инвестиционные','Investment')}</option></select><select id="hk-map-faction-filter"><option value="all">${either('Все фракции','All factions')}</option></select></div>
          <div class="hk-map-legend"><span><i class="hk-map-dot" style="background:#d7a93d"></i>${either('не исследовано','unresearched')}</span><span><i class="hk-map-dot" style="background:#34435a"></i>0 💎</span><span><i class="hk-map-dot" style="background:#35c77a"></i>1 💎</span><span><i class="hk-map-dot" style="background:#21b8d7"></i>2 💎</span><span><i class="hk-map-dot" style="background:#4285f4"></i>3 💎</span><span><i class="hk-map-dot" style="background:#9b67ed"></i>4 💎</span><span><i class="hk-map-dot" style="background:#78efff"></i>5+ 💎</span><span>◆ ${either('инвестиционное','investment')}</span></div>
          <div id="hk-map-match-count" class="hk-map-match-count"></div><div class="hk-map-zoom"><button id="hk-map-zoom-out" aria-label="${either('Отдалить','Zoom out')}">−</button><button id="hk-map-zoom-value" aria-label="${either('Сбросить масштаб','Reset zoom')}">100%</button><button id="hk-map-zoom-in" aria-label="${either('Приблизить','Zoom in')}">+</button></div><div id="hk-map-visual" class="hk-map-visual"></div><div id="hk-map-selected" class="hk-map-selected"><span>${either('Нажмите на здание на карте','Tap a building on the map')}</span></div></div>
      </div>
      <div id="hk-log" class="hk-log"></div><div id="hk-status" class="hk-status">${tr('version',{v:VERSION})}</div>
    </div>`;
    document.body.appendChild(root);
    hkStartupStage = 'MOUNTED';
    panel = root.querySelector('#hk-panel'); logBox = root.querySelector('#hk-log'); statusLine = root.querySelector('#hk-status');
    businessLists = root.querySelector('#hk-business-lists'); planBox = root.querySelector('#hk-plan'); presetSelect = root.querySelector('#hk-preset'); dailyBox = root.querySelector('#hk-daily-tasks'); clanBox = root.querySelector('#hk-clan-content'); resourceBox = root.querySelector('#hk-resource-content');
    fairTypes = root.querySelector('#hk-fair-types'); fairLots = root.querySelector('#hk-fair-lots'); fairSlotRules = root.querySelector('#hk-fair-slot-rules'); fairPresetSelect = root.querySelector('#hk-fair-preset');
    shopCards = root.querySelector('#hk-shop-cards'); shopSummary = root.querySelector('#hk-shop-summary');
    recipeCards = root.querySelector('#hk-recipe-cards'); recipeSummary = root.querySelector('#hk-recipe-summary'); recipeDatabaseBox = root.querySelector('#hk-recipe-database');
    bureauCards = root.querySelector('#hk-bureau-cards'); bureauSummary = root.querySelector('#hk-bureau-summary');
    mapIndexBox = root.querySelector('#hk-map-index'); mapDetailBox = root.querySelector('#hk-map-detail');
    const permanentFab = root.querySelector('#hk-fab');
    if (!permanentFab?.isConnected) {
      showBootstrap(either('Кнопка HK не смонтирована','HK launcher was not mounted'));
      throw new Error('hk-fab-not-mounted');
    }
    installFabDragging(permanentFab);
    hkStartupStage = 'FAB';
    hideBootstrap();
    root.querySelector('.hk-close').onclick = () => panel.classList.remove('open');
    root.querySelector('#hk-donation').onclick = () => window.open(DONATION_URL, '_blank', 'noopener');
    root.querySelectorAll('[data-lang]').forEach(button => button.onclick = () => {
      language = button.dataset.lang === 'en' ? 'en' : 'ru';
      save({language});
      applyLanguage();
    });
    root.querySelectorAll('[data-optimizer-section]').forEach(section => section.ontoggle = () => {
      saveOptimizerSectionState(section.dataset.optimizerSection, section.open);
    });
    const groupForPage = page => NAV_GROUPS.find(group=>group.modules.some(module=>module.page===page)) || NAV_GROUPS[0];
    const renderGroupSubnav = (groupId, activePage) => {
      const group=NAV_GROUPS.find(row=>row.id===groupId)||NAV_GROUPS[0];
      const box=root.querySelector('#hk-subnav');
      box.innerHTML=group.modules.map(module=>`<button class="${module.page===activePage?'active ':''}${module.planned?'planned':''}" ${module.page?`data-module="${module.page}"`:''} ${module.planned?'disabled':''} data-nav-ru="${escapeHtml(module.ru)}" data-nav-en="${escapeHtml(module.en)}">${escapeHtml(language==='en'?module.en:module.ru)}${module.planned?` · ${either('скоро','soon')}`:''}</button>`).join('');
      box.querySelectorAll('[data-module]:not([disabled])').forEach(button=>button.onclick=()=>activateModule(button.dataset.module,true));
    };
    const activateModule = (page,persist=true) => {
      const regularFairAlias = page === 'fair-regular';
      const contentPage = regularFairAlias ? 'fair' : page;
      const target=root.querySelector(`[data-content="${contentPage}"]`) || root.querySelector('[data-content="daily"]');
      const finalPage=target.dataset.content;
      const navPage=regularFairAlias ? 'fair-regular' : finalPage;
      const group=groupForPage(navPage);
      root.querySelectorAll('.hk-tab').forEach(button=>button.classList.toggle('active',button.dataset.group===group.id));
      root.querySelectorAll('.hk-page').forEach(section=>section.classList.toggle('active',section===target));
      renderGroupSubnav(group.id,navPage);
      if(persist) save({navGroup:group.id,navModule:navPage});
      if (finalPage === 'maps') renderMapIndex();
      if (finalPage === 'business') { renderBusinessLists(); renderBusinessOptimizerFilters(); }
      if (finalPage === 'daily') renderDailyTasks();
      if (finalPage === 'resources') renderResources();
      if (finalPage === 'buildings') renderBuildings();
      if (finalPage === 'explore') renderExplore();
      if (finalPage === 'clan') renderClanSkills();
      if (finalPage === 'wars') renderWars();
      if (finalPage === 'bosses') renderBosses();
      if (finalPage === 'fair') {
        fairViewMode = regularFairAlias ? 'regular' : 'all';
        if (regularFairAlias) {
          selectedFairId = 'fair_default';
          selectedFairLots.clear();
          selectedFairSlotRules.clear();
          selectedFairCurrency = '';
        }
        renderFair();
      }
      if (finalPage === 'shop') renderShop();
      if (finalPage === 'recipes') renderRecipes();
      if (finalPage === 'routines') renderAutoRoutines();
      if (finalPage.startsWith('growth')) { renderGrowth(); growthAutoOpen(finalPage); }
      else if (finalPage !== 'routines') void refreshModuleLive(finalPage);
    };
    root.querySelectorAll('.hk-tab').forEach(tab=>tab.onclick=()=>{
      const group=NAV_GROUPS.find(row=>row.id===tab.dataset.group)||NAV_GROUPS[0];
      const preferred=group.modules.find(module=>module.page && !module.planned)?.page || 'daily';
      activateModule(preferred,true);
    });
    const remembered=clean(load().navModule||'daily');
    activateModule(remembered === 'fair-regular' || root.querySelector(`[data-content="${remembered}"]`) ? remembered : 'daily',false);
    const activateBusinessPane = (paneName, persist = true) => {
      const pane = paneName === 'optimizer' ? 'optimizer' : 'regular';
      root.querySelectorAll('[data-business-tab]').forEach(button => button.classList.toggle('active', button.dataset.businessTab === pane));
      root.querySelectorAll('[data-business-pane]').forEach(section => section.classList.toggle('active', section.dataset.businessPane === pane));
      if (persist) save({businessSubtab:pane});
      if (pane === 'optimizer') {
        renderBusinessOptimizerFilters();
        renderBonusAnalyzer();
      } else {
        renderBusinessLists();
      }
    };
    root.querySelectorAll('[data-business-tab]').forEach(button => button.onclick = () => activateBusinessPane(button.dataset.businessTab));
    activateBusinessPane(load().businessSubtab, false);
    root.querySelector('#hk-health-check').onclick = async () => {
      log(either('Проверяю подключение…','Checking connection…'));
      const gameOk = await bootstrapLateGameConnection();
      const licenseOk = playerDocument ? await checkLicense(playerDocument.player || {}, true) : false;
      renderHealth();
      log(gameOk && licenseOk ? either('Связь проверена: всё работает','Connection check passed') : either('Есть проблема с подключением — скачайте диагностику','Connection problem detected — download diagnostics'), gameOk && licenseOk ? 'ok' : 'warn');
    };
    root.querySelector('#hk-diagnostic').onclick = downloadDiagnosticReport;
    root.querySelector('#hk-runner-pause').onclick = () => hkRunner.state.status==='paused' ? hkRunner.resume() : hkRunner.pause();
    root.querySelector('#hk-runner-stop').onclick = () => hkRunner.stop('user');
    root.addEventListener('click',event=>{
      const actionButton=event.target.closest?.('[data-growth-action]');
      if(actionButton){
        const action=actionButton.dataset.growthAction;
        if(action==='all')void growthRunPlan('all');
        else if(action==='hamsters')void growthRunPlan('hamsters');
        else if(action==='generals')void growthRunPlan('generals');
        else if(action==='prep')void growthRunPlan('prep');
        else if(action==='reset-priority')growthResetPriority();
        return;
      }
      const row=event.target.closest?.('[data-growth-priority-index]');if(!row)return;
      const index=Number(row.dataset.growthPriorityIndex);
      if(event.target.closest('[data-growth-priority-remove]'))growthRemovePriority(index);
      else{const move=event.target.closest('[data-growth-priority-move]')?.dataset.growthPriorityMove;if(move)growthMovePriority(index,move);}
    });
    const growthSettingIds=['#hk-growth-run-prep','#hk-growth-run-generals','#hk-growth-run-hamsters','#hk-growth-contracts','#hk-growth-balls','#hk-growth-boxes','#hk-growth-pit-percent','#hk-growth-general-mode','#hk-growth-general-weight','#hk-growth-caps-percent','#hk-growth-hamster-weight','#hk-growth-copy-enabled','#hk-growth-exclude-event'];
    for(const selector of growthSettingIds)root.querySelector(selector)?.addEventListener('change',()=>{growthReadSettingsFromUi();renderGrowth();if(selector==='#hk-growth-exclude-event'&&root.querySelector(selector)?.checked)void growthLoadLive({force:false,loadShop:true,loadConfig:true,silent:true});});
    renderHealth(); renderRunnerState(); renderGrowth();
    runtime.ensure = () => {
      try {
        if (!root?.isConnected || root.dataset.hkRevision !== HK_CORE_REVISION || !root.querySelector('#hk-fab')) {
          try { root?.remove(); } catch (_) {}
          root = null;
          panel = null;
          startInterface();
        }
        if (root?.isConnected && root.dataset.hkRevision === HK_CORE_REVISION && root.querySelector('#hk-fab')) {
          hideBootstrap();
          return true;
        }
      } catch (_) {}
      return false;
    };
    runtime.open = () => {
      try {
        runtime.ensure?.();
        if (panel?.isConnected) {
          panel.classList.add('open');
          updateWatermark();
        } else {
          showBootstrap();
        }
      } catch (error) {
        showBootstrap(error?.message || either('Не удалось восстановить HK','Could not restore HK'));
      }
    };
    runtime.navigate = page => { try { activateModule(page,true); panel?.classList.add('open'); } catch (_) {} };
    root.querySelector('#hk-daily-refresh').onclick = () => refreshModuleLive('daily',{force:true});
    root.querySelector('#hk-daily-run').onclick = runDailySelected;
    root.querySelector('#hk-daily-clear').onclick = () => { if (logBox) logBox.innerHTML = ''; if (statusLine) statusLine.textContent = tr('dailyReady'); };
    root.querySelector('#hk-pit-start').onclick = async () => {
      if (!requireLicense()) return;
      if (hkRunner.running) { alert(either('Сначала завершите текущую задачу','Finish the current task first')); return; }
      settings = {
        target: Math.max(1, Number(root.querySelector('#hk-target').value || 1)),
        interval: Math.max(.7, Number(root.querySelector('#hk-interval').value || 1.2)),
        activationLimit: Math.max(0, Number(root.querySelector('#hk-activation-limit').value || 0)),
        restoreLimit: Math.max(0, Number(root.querySelector('#hk-restore-limit').value || 0)),
        allowTokens: root.querySelector('#hk-allow-tokens').checked,
        collectOnly: root.querySelector('#hk-pit-collect-only').checked
      };
      save({settings});
      activationSpent = 0;
      restoreSpent = 0;
      pitRunStart = (() => { const state=pitState(); return {round:state.round,power:pitPowerValue(state)}; })();
      hkRunner.start({title:either('Яма','Pit'),step:either('Автобой','Auto battle'),pausable:true,stoppable:true});
      pitRunning = true;
      updatePitButtons();
      log(settings.collectOnly ? either('Запущен безопасный сбор данных Ямы без боя','Started safe Pit data collection without battle') : `Автобой запущен до раунда ${settings.target}`);
      try {
        await pitLoop();
        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');
        hkRunner.finish(either('Яма завершена','Pit completed'));
      } catch (error) {
        if (error?.name === 'AbortError') {
          hkRunner.reset();
          log(either('Автобой остановлен','Auto battle stopped'),'warn');
        } else {
          hkRunner.fail(error);
          log(`${either('Ошибка Ямы','Pit error')}: ${error?.message || error}`,'bad');
        }
      } finally {
        pitRunning = false;
        updatePitButtons();
      }
    };
    root.querySelector('#hk-pit-stop').onclick = () => {
      pitRunning = false;
      hkRunner.stop('pit');
      updatePitButtons();
      log(either('Останавливаю автобой…','Stopping auto battle…'),'warn');
    };
    root.querySelector('#hk-export').onclick = exportPowers;
    root.querySelector('#hk-refresh-game').onclick = () => location.reload();
    root.querySelector('#hk-optimizer-calculate').onclick = calculateBusinessOptimizer;
    root.querySelector('#hk-optimizer-restore').onclick = prepareOriginalBusinessRestore;
    root.querySelector('#hk-remove-tier').onchange = renderBusinessLists;
    root.querySelector('#hk-insert-tier').onchange = renderBusinessLists;
    root.querySelector('#hk-select-remove').onclick = () => {
      preparedBusinessPlan = null; preparedBusinessPlanSource = '';
      const filter = Number(root.querySelector('#hk-remove-tier').value || 0);
      layout.filter(row => filter === 0 ? true : filter === -1 ? !row.businessId : !!row.businessId && tier(row.businessId) === filter)
        .forEach(row => selectedSlots.add(row.key));
      renderBusinessLists();
    };
    root.querySelector('#hk-save-preset').onclick = savePreset;
    root.querySelector('#hk-delete-preset').onclick = deletePreset;
    root.querySelector('#hk-fair-load').onclick = () => refreshModuleLive('fair',{force:true});
    root.querySelector('#hk-fair-save-preset').onclick = () => saveFairPreset();
    root.querySelector('#hk-fair-update-preset').onclick = () => fairPresetSelect?.value ? saveFairPreset(fairPresetSelect.value) : saveFairPreset();
    root.querySelector('#hk-fair-delete-preset').onclick = deleteFairPreset;
    fairPresetSelect.onchange = () => loadFairPreset(fairPresetSelect.value);
    root.querySelector('#hk-fair-search').oninput = renderFair;
    const exactFairLots = root.querySelector('#hk-fair-exact-lots');
    exactFairLots.oninput = exactFairLots.onchange = () => { renderFairBonusChoices(); updateFairControls(); };
    root.querySelector('#hk-fair-buy-limit').oninput = updateFairControls;
    root.querySelector('#hk-fair-reroll-limit').oninput = updateFairControls;
    root.querySelector('#hk-fair-start').onclick = runFair;
    root.querySelector('#hk-fair-stop').onclick = () => { fairStop = true; hkRunner.stop('fair'); log(either('Останавливаю ярмарку…','Stopping fair…'), 'warn'); };
    renderFairBonusChoices();
    root.querySelector('#hk-shop-load').onclick = () => refreshModuleLive('shop',{force:true});
    root.querySelector('#hk-shop-buy').onclick = buyRegularShop;
    root.querySelector('#hk-shop-select').onclick = () => {
      selectedShopLots.clear();
      selectedShopCounts.clear();
      shopRows.filter(row => row.section === selectedShopSection &&
        (selectedShopSection !== 'ordinary' || row.group === selectedShopGroup) && row.safe && row.remaining > 0)
        .forEach(row => { selectedShopLots.add(row.lotId); selectedShopCounts.set(row.lotId, defaultShopPurchaseCount(row)); });
      renderShop();
    };
    root.querySelectorAll('[data-shop-section]').forEach(button => button.onclick = () => {
      selectedShopSection = button.dataset.shopSection;
      selectedShopGroup = selectedShopSection === 'ordinary' ? 'resources' : selectedShopSection === 'clan' ? 'personal' : '';
      selectedShopLots.clear();
      selectedShopCounts.clear();
      root.querySelectorAll('[data-shop-section]').forEach(element => element.classList.toggle('active', element === button));
      renderShop();
    });
    root.querySelectorAll('[data-shop-group]').forEach(button => button.onclick = () => {
      selectedShopGroup = button.dataset.shopGroup;
      selectedShopLots.clear();
      selectedShopCounts.clear();
      root.querySelectorAll('[data-shop-group]').forEach(element => element.classList.toggle('active', element === button));
      renderShop();
    });
    root.querySelectorAll('[data-recipe-pane]').forEach(button => button.onclick = () => {
      root.querySelectorAll('[data-recipe-pane]').forEach(element => element.classList.toggle('active', element === button));
      root.querySelectorAll('[data-recipe-content]').forEach(element => element.classList.toggle('active', element.dataset.recipeContent === button.dataset.recipePane));
      if(button.dataset.recipePane==='spin')void refreshModuleLive('recipes',{force:true});
      if(button.dataset.recipePane==='database')void loadCommunityRecipes();
      if(button.dataset.recipePane==='bureau')void loadProjectBureau();
    });
    root.querySelector('#hk-recipe-load').onclick = () => refreshModuleLive('recipes',{force:true});
    root.querySelector('#hk-recipe-attempts').oninput = renderRecipes;
    root.querySelector('#hk-recipe-run').onclick = runRecipes;
    root.querySelector('#hk-recipe-stop').onclick = () => { recipeStop = true; hkRunner.stop('recipes'); log(either('Останавливаю прокрутку…', 'Stopping rerolls…'), 'warn'); };
    root.querySelector('#hk-recipe-db-load').onclick = loadCommunityRecipes;
    root.querySelector('#hk-bureau-load').onclick = loadProjectBureau;
    root.querySelector('#hk-bureau-tier').onchange = event => { bureauTier = Number(event.target.value || 0); renderProjectBureau(); };
    root.querySelector('#hk-bureau-attempts').oninput = renderProjectBureau;
    root.querySelector('#hk-bureau-run').onclick = runProjectBureau;
    root.querySelector('#hk-map-load').onclick = () => loadMapIndex(false);
    root.querySelector('#hk-map-scan').onclick = () => submitOwnedMapAreas(true);
    root.querySelectorAll('[data-map-source]').forEach(button => button.onclick = () => setMapSource(button.dataset.mapSource));
    root.querySelector('#hk-map-search').oninput = renderMapIndex;
    root.querySelector('#hk-map-sort').onchange = renderMapIndex;
    root.querySelector('#hk-map-back').onclick = renderMapIndex;
    root.querySelector('#hk-map-zoom-out').onclick = () => changeMapZoom(mapZoom / 1.4);
    root.querySelector('#hk-map-zoom-in').onclick = () => changeMapZoom(mapZoom * 1.4);
    root.querySelector('#hk-map-zoom-value').onclick = resetMapZoom;
    ['#hk-map-status-filter','#hk-map-room-filter','#hk-map-type-filter','#hk-map-faction-filter'].forEach(selector => root.querySelector(selector).onchange=renderMapDetail);
    presetSelect.onchange = () => loadPreset(presetSelect.value);
    fillTierFilters(); refreshPresets(); refreshFairPresets(); renderBusinessLists(); renderBusinessOptimizerFilters(); renderDailyTasks(); renderClanSkills(); renderResources();
    if (playerDocument) refreshBusinessData();
    applyLanguage();
    setInterval(() => {
      updatePitStatus();
      const c=root.querySelector('#hk-connect'); if(c)c.textContent=apiHeaders.Authorization?tr('connectedSlots',{n:layout.length}):tr('waiting');
      const token=currentGameBearer(); const exp=jwtExpiration(token);
      setHealth('auth', !!token && exp > Date.now()+5000, token ? (exp > Date.now()+5000 ? 'авторизация активна' : 'токен истёк') : 'нет токена');
    }, 1000);
    setInterval(updateWatermark, 30000);
    hkStartupStage = 'READY';
  }

  function startNetworkCapture() {
    try { installNetworkCapture(); }
    catch (_) { setTimeout(startNetworkCapture, 250); }
  }

  function startInterface() {
    hkStartupStage = document.body ? 'BODY' : 'WAIT_BODY';
    if (root?.isConnected && root.querySelector('#hk-fab')) {
      hideBootstrap();
      return;
    }
    if (root) {
      try { root.remove(); } catch (_) {}
      root = null;
      panel = null;
    }
    try {
      if (document.body) { hkStartupStage = 'RENDER'; renderUI(); }
    } catch (error) {
      try { root?.remove(); } catch (_) {}
      root = null;
      panel = null;
      showBootstrap(error?.message || error);
      setTimeout(startInterface, 500);
      return;
    }
    if (!root?.isConnected || !root.querySelector('#hk-fab')) setTimeout(startInterface, 250);
  }

  // HK_NATIVE_LOGIN_GATE_V1 login-gate-20260920-r1
  const HK_NATIVE_LOGIN_GATE_REV = 'login-gate-hotfix-20260920-r2';
  const HK_UI_PRELOGIN_REV = 'ui-prelogin-20260920-r3';
  const HK_LAUNCHER_HANDOFF_REV = 'launcher-handoff-20260920-r4';
  let hkNativeLoginRuntimeStarted = false;

  function hkNativeGameLoginReady() {
    if (playerDocument && apiHeaders.Authorization) return true;
    try {
      for (const storage of [sessionStorage, localStorage]) {
        const token = String(storage.getItem('token') || '').trim();
        if (token && jwtExpiration(token) > Date.now() + 5000 && gameBearerPlayerId(token)) return true;
      }
    } catch (_) {}
    try {
      const licenseOrigin = new URL(LICENSE_URL).origin;
      for (const entry of performance.getEntriesByType('resource').slice().reverse()) {
        const url = new URL(String(entry?.name || ''), location.href);
        if (url.origin === licenseOrigin) continue;
        if (url.pathname === '/player/me') return true;
      }
    } catch (_) {}

    // The current game city is rendered with Leaflet/OpenStreetMap.  A visible
    // native map is a strong signal that the player is already inside the game,
    // even when the game no longer exposes its bearer token under the old
    // localStorage key expected by the original gate.
    try {
      const nativeMap = document.querySelector('.leaflet-container, .leaflet-map-pane, .leaflet-control-container');
      if (nativeMap && (nativeMap.offsetWidth || nativeMap.offsetHeight || nativeMap.getClientRects().length)) return true;
      const osm = document.querySelector('a[href*="openstreetmap.org"]');
      if (osm && (osm.offsetWidth || osm.offsetHeight || osm.getClientRects().length)) return true;
    } catch (_) {}

    // Also accept observed authenticated game traffic.  The API has changed
    // route/storage details over time, so do not depend on /player/me alone.
    try {
      const licenseOrigin = new URL(LICENSE_URL).origin;
      for (const entry of performance.getEntriesByType('resource').slice().reverse()) {
        const url = new URL(String(entry?.name || ''), location.href);
        if (url.origin === licenseOrigin) continue;
        if (!/(^|\.)hwgame\.cloud$/i.test(url.hostname)) continue;
        if (/\/(player|city|shop|clan|alliance|war|wars|building|business|fair|game_area)(?:\/|$)/i.test(url.pathname)) return true;
      }
    } catch (_) {}

    return false;
  }

  function startAfterNativeGameLogin() {
    if (hkNativeLoginRuntimeStarted) return;
    if (!hkNativeGameLoginReady()) {
      setTimeout(startAfterNativeGameLogin, 500);
      return;
    }
    hkNativeLoginRuntimeStarted = true;
    if (!root?.isConnected || !root.querySelector('#hk-fab')) showBootstrap();
    startNetworkCapture();
    startInterface();
    setTimeout(() => bootstrapLateGameConnection(), 100);
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', startInterface, {once:true});
    setInterval(() => { ensureGameAuthorization(false, 'background').catch(error => recordDiagnostic('auth-background-error',{error:error?.message || error})); }, 30000);
    setInterval(captureActiveEventCode, 1500);
    setTimeout(() => hkGameBridge.discover(false), 1500);
    setInterval(() => { if (!hkGameBridge.ready) hkGameBridge.discover(false); }, 30000);
    setInterval(() => { if (playerDocument) checkLicense(playerDocument.player || {}, true); }, LICENSE_RECHECK_MS);
    setTimeout(() => collectPublicSnapshot(true), 5000);
    setInterval(() => collectPublicSnapshot(), PUBLIC_SNAPSHOT_INTERVAL_MS);
    recordDiagnostic('native-login-gate-open',{revision:'login-gate-20260920-r1'});
  }

  runtime.destroy = () => {
    runtime.active = false;
    try { root?.remove(); } catch (_) {}
    try { bootstrapButton?.remove(); } catch (_) {}
    root = null;
    panel = null;
  };

  startInterface();
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startInterface, {once:true});
  }
  startAfterNativeGameLogin();
  setInterval(() => {
    if (runtime.active) runtime.ensure?.();
  }, 1000);
})();
