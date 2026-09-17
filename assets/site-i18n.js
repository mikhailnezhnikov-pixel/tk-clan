(()=>{
  const CORE={
    ru:{home:'Главная',calculators:'Калькуляторы',recipes:'Рецепты',wars:'Клановые войны',ratings:'Рейтинг',information:'Информация',feedback:'Обратная связь',cabinet:'Личный кабинет',menu:'Меню',footer:'Top King · Hamster King',play:'Начать играть',loading:'Загрузка…',updated:'Обновлено',noData:'Данных пока нет',error:'Не удалось загрузить данные.'},
    en:{home:'Home',calculators:'Calculators',recipes:'Recipes',wars:'Clan wars',ratings:'Rankings',information:'Information',feedback:'Feedback',cabinet:'Member area',menu:'Menu',footer:'Top King · Hamster King',play:'Play now',loading:'Loading…',updated:'Updated',noData:'No data yet',error:'Could not load data.'},
    fa:{home:'خانه',calculators:'محاسبه‌گرها',recipes:'دستورها',wars:'جنگ‌های قبیله‌ای',ratings:'رتبه‌بندی',information:'اطلاعات',feedback:'بازخورد',cabinet:'پنل اعضا',menu:'منو',footer:'Top King · Hamster King',play:'شروع بازی',loading:'در حال بارگذاری…',updated:'به‌روزرسانی',noData:'هنوز داده‌ای وجود ندارد',error:'بارگذاری داده‌ها ممکن نشد.'}
  };
  const supported=['ru','en','fa'];
  const saved=localStorage.getItem('tk-language');
  const browser=(navigator.language||'ru').slice(0,2).toLowerCase();
  let language=supported.includes(saved)?saved:(supported.includes(browser)?browser:'ru');
  const dictionary=lang=>Object.assign({},CORE[lang]||CORE.ru,(window.TK_PAGE_TRANSLATIONS||{})[lang]||{});

  const GAME_FRONT='https://cdn-prod-front-dist.hwgame.cloud/';
  const GAME_ART='https://cdn-prod-art.hwgame.cloud/';
  const OFFICIAL_VISUALS={
    calculators:'assets/images/ui/boss-fight.png',
    recipes:'assets/images/ui/collections.png',
    cabinet:'assets/images/ui/clan-members-icon.png',
    wars:'assets/images/ui/vs.png',
    ratings:'assets/images/ui/nominations-1.png',
    information:'assets/images/ui/info-stars.png',
    feedback:'assets/images/ui/telegram-1.png'
  };
  function fitGameIcon(img){
    img.style.objectFit='contain';
    if(img.closest('.card-icon,.quick-icon'))img.style.padding='5px';
  }
  function replaceVisuals(){
    for(const [section,path] of Object.entries(OFFICIAL_VISUALS)){
      document.querySelectorAll(`a[href*="${section}"] .card-icon img,a[href*="${section}"] .quick-icon img`).forEach(img=>{
        img.src=GAME_FRONT+path;
        fitGameIcon(img);
      });
    }
    document.querySelectorAll('.brand img').forEach(img=>{
      img.src=GAME_FRONT+'assets/images/ui/clan-list-icon.png';
      fitGameIcon(img);
    });
    const icon=document.querySelector('link[rel="icon"]');
    if(icon)icon.href=GAME_FRONT+'assets/images/ui/clan-list-icon.png';
  }

  // Inline replacements in the restored Information guide.
  // Anything not listed here stays exactly as the original guide icon.
  const GUIDE_CONFIRMED_ICON_MAP={
    '101':GAME_FRONT+'assets/images/ui/pit-rewards-rhomb-icon.png',
    '100':GAME_ART+'items/item_boss_pass_ticket_icon.png',
    '99':GAME_ART+'items/item_pit_rat_tokens_icon.png',
    '102':GAME_FRONT+'assets/images/ui/boss-fight.png',
    '104':GAME_ART+'bosses/rats_05_icon.png',
    '129':GAME_FRONT+'assets/images/ui/vs.png',
    '28':GAME_FRONT+'assets/images/ui/favorite-buildings-counter.png',
    '97':GAME_FRONT+'assets/images/menu/shop-1.png',
    '25':GAME_FRONT+'assets/images/ui/hamster-ball.png',
    '115':GAME_ART+'battle_passes/icons/bp_personal_area_boss_paid_01_icon.png'
  };

  // User-approved section visuals from the 1–9 review.
  const GUIDE_SECTION_ICON_MAP={
    power:GAME_FRONT+'assets/images/ui/hamster-ball.png',
    generals:GAME_ART+'items/item_hball_hgen_beasthelper_g1_ssplus_icon.png',
    battles:GAME_FRONT+'assets/images/ui/fights.png',
    clans:GAME_FRONT+'assets/images/ui/clan-list-icon.png',
    resources:GAME_FRONT+'assets/images/ui/inventory.png',
    business:'../assets/guide-emoji/26.png',
    maps:GAME_FRONT+'assets/images/menu/city-1.png'
  };

  function styleGuideIcon(img,id){
    img.dataset.originalGuideIcon=id;
    img.style.width='24px';
    img.style.height='24px';
    img.style.objectFit='contain';
    img.style.verticalAlign='middle';
    img.style.margin='0 4px';
  }

  function upgradeInformationIcons(){
    if(!document.getElementById('guide'))return;
    document.querySelectorAll('#guide img.inline-icon').forEach(img=>{
      const original=img.getAttribute('src')||'';
      const match=original.match(/guide-emoji\/(\d+)\.png(?:\?.*)?$/);
      if(!match)return;
      const replacement=GUIDE_CONFIRMED_ICON_MAP[match[1]];
      if(!replacement)return;
      img.src=replacement;
      styleGuideIcon(img,match[1]);
    });

    // ID 98 has two meanings in the legacy guide. In Battles it is Regional Boss,
    // while next to Beasts it remains the user's approved first image.
    document.querySelectorAll('#battles img.inline-icon').forEach(img=>{
      const original=img.getAttribute('src')||'';
      if(!/guide-emoji\/98\.png(?:\?.*)?$/.test(original))return;
      img.src=GAME_FRONT+'assets/images/ui/regional-bosses.png';
      styleGuideIcon(img,'98');
    });

    // IDs 27, 33, 26 and 150 are explicitly user-approved as their original
    // uploaded/local guide images, so they are intentionally not replaced.
  }

  function upgradeInformationSectionIcons(){
    if(!document.getElementById('guide'))return;
    for(const [id,src] of Object.entries(GUIDE_SECTION_ICON_MAP)){
      const article=document.getElementById(id);
      const h2=article&&article.querySelector('h2');
      if(!h2)continue;
      const raw=(h2.textContent||'').trim();
      const clean=raw.replace(/^[🎮🚀💪⭐⚔️👑💰🏢🍳📊🗺🛠\s]+/u,'').trim()||raw;
      h2.textContent='';
      const wrap=document.createElement('span');
      wrap.style.display='inline-flex';
      wrap.style.alignItems='center';
      wrap.style.gap='10px';
      const icon=document.createElement('img');
      icon.src=src;
      icon.alt='';
      icon.style.width='34px';
      icon.style.height='34px';
      icon.style.objectFit='contain';
      icon.style.flex='0 0 auto';
      const label=document.createElement('span');
      label.textContent=clean;
      wrap.append(icon,label);
      h2.append(wrap);
    }
  }

  function configureHomepage(){
    const hero=document.querySelector('main .hero');
    if(!hero)return;
    hero.style.setProperty('background-image','url("assets/home/top-king-clan-hero-approved.jpg")','important');
    const actions=hero.querySelector('.hero-actions');
    if(actions){
      actions.innerHTML='<a class="button primary" href="https://app.hamsterking.games/app.html" target="_blank" rel="noopener" data-i18n="play">Начать играть</a>';
    }
    if(!document.getElementById('tk-home-responsive')){
      const style=document.createElement('style');
      style.id='tk-home-responsive';
      style.textContent=`
        .hero{background-image:url("assets/home/top-king-clan-hero-approved.jpg")!important;background-position:50% center!important;background-repeat:no-repeat!important;background-color:#07080b!important;}
        .hero-copy{width:min(540px,45%)!important}.hero-actions .button{min-width:190px}
        @media (max-width:980px) and (min-width:821px){.hero{background-position:53% center!important}.hero-copy{width:min(520px,52%)!important}}
        @media (max-width:820px) and (min-width:681px){.hero{min-height:900px!important;align-items:flex-start!important;background-size:100% auto!important;background-position:center top!important}.hero-inner{width:100%!important;padding-top:clamp(410px,58vw,465px)!important;padding-bottom:175px!important}.hero-copy{width:min(620px,88%)!important}}
        @media (max-width:680px){.hero{min-height:920px!important;align-items:flex-start!important;background-size:100% auto!important;background-position:center top!important}.hero-inner{width:100%!important;padding:clamp(250px,68vw,300px) 16px 270px!important}.hero-copy{width:100%!important}.hero-actions{margin-top:22px!important}.hero-actions .button{width:100%;min-width:0;flex:1 1 100%}.quick-panel{bottom:18px!important}}
        @media (max-width:420px){.hero{min-height:900px!important}.hero-inner{padding-top:250px!important;padding-bottom:262px!important}.hero h1{font-size:clamp(40px,12vw,50px)!important}.hero .lead{font-size:15px!important;line-height:1.48!important}}
      `;
      document.head.append(style);
    }
  }

  function apply(lang=language){
    language=supported.includes(lang)?lang:'ru'; localStorage.setItem('tk-language',language);
    const strings=dictionary(language); document.documentElement.lang=language; document.documentElement.dir=language==='fa'?'rtl':'ltr';
    document.querySelectorAll('[data-i18n]').forEach(node=>{const value=strings[node.dataset.i18n];if(value!=null)node.textContent=value});
    document.querySelectorAll('[data-i18n-html]').forEach(node=>{const value=strings[node.dataset.i18nHtml];if(value!=null)node.innerHTML=value});
    document.querySelectorAll('[data-i18n-placeholder]').forEach(node=>{const value=strings[node.dataset.i18nPlaceholder];if(value!=null)node.placeholder=value});
    document.querySelectorAll('[data-language]').forEach(button=>{const active=button.dataset.language===language;button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active))});
    if(strings.pageTitle)document.title=strings.pageTitle;
    document.dispatchEvent(new CustomEvent('tk-language-change',{detail:{language,strings}}));
  }
  function refreshInformationVisuals(){
    upgradeInformationIcons();
    upgradeInformationSectionIcons();
  }
  function init(){
    document.querySelectorAll('[data-language]').forEach(button=>button.addEventListener('click',()=>apply(button.dataset.language)));
    const toggle=document.querySelector('[data-menu-toggle]'),menu=document.querySelector('[data-mobile-nav]');
    if(toggle&&menu)toggle.addEventListener('click',()=>{const open=!menu.classList.contains('open');menu.classList.toggle('open',open);toggle.setAttribute('aria-expanded',String(open))});
    replaceVisuals();
    configureHomepage();
    apply(language);
    refreshInformationVisuals();
    document.addEventListener('tk-language-change',()=>setTimeout(refreshInformationVisuals,0));
  }
  window.TopKingI18n={apply,get language(){return language},strings:()=>dictionary(language)};
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init,{once:true}):init();
})();
