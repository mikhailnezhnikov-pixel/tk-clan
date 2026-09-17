(()=>{
  const CORE={
    ru:{home:'Главная',calculators:'Калькуляторы',recipes:'Рецепты',wars:'Клановые войны',ratings:'Рейтинг',information:'Информация',feedback:'Обратная связь',cabinet:'Личный кабинет',menu:'Меню',footer:'Top King · Hamster King',loading:'Загрузка…',updated:'Обновлено',noData:'Данных пока нет',error:'Не удалось загрузить данные.'},
    en:{home:'Home',calculators:'Calculators',recipes:'Recipes',wars:'Clan wars',ratings:'Rankings',information:'Information',feedback:'Feedback',cabinet:'Member area',menu:'Menu',footer:'Top King · Hamster King',loading:'Loading…',updated:'Updated',noData:'No data yet',error:'Could not load data.'},
    fa:{home:'خانه',calculators:'محاسبه‌گرها',recipes:'دستورها',wars:'جنگ‌های قبیله‌ای',ratings:'رتبه‌بندی',information:'اطلاعات',feedback:'بازخورد',cabinet:'پنل اعضا',menu:'منو',footer:'Top King · Hamster King',loading:'در حال بارگذاری…',updated:'به‌روزرسانی',noData:'هنوز داده‌ای وجود ندارد',error:'بارگذاری داده‌ها ممکن نشد.'}
  };
  const supported=['ru','en','fa'];
  const saved=localStorage.getItem('tk-language');
  const browser=(navigator.language||'ru').slice(0,2).toLowerCase();
  let language=supported.includes(saved)?saved:(supported.includes(browser)?browser:'ru');
  const dictionary=lang=>Object.assign({},CORE[lang]||CORE.ru,(window.TK_PAGE_TRANSLATIONS||{})[lang]||{});

  const GAME_FRONT='https://cdn-prod-front-dist.hwgame.cloud/';
  const OFFICIAL_VISUALS={
    calculators:'assets/images/ui/boss-fight.png',
    recipes:'assets/images/ui/collections.png',
    cabinet:'assets/images/ui/clan-members-icon.png',
    wars:'assets/images/ui/vs.png',
    ratings:'assets/images/ui/nominations-1.png',
    information:'assets/images/ui/info-stars.png',
    feedback:'assets/images/ui/telegram-1.png'
  };
  function replaceVisuals(){
    for(const [section,path] of Object.entries(OFFICIAL_VISUALS)){
      document.querySelectorAll(`a[href*="${section}"] .card-icon img,a[href*="${section}"] .quick-icon img`).forEach(img=>{
        img.src=GAME_FRONT+path;
        img.style.objectFit='contain';
      });
    }
    document.querySelectorAll('.brand img').forEach(img=>{
      img.src=GAME_FRONT+'assets/images/ui/clan-list-icon.png';
      img.style.objectFit='contain';
    });
    const icon=document.querySelector('link[rel="icon"]');
    if(icon)icon.href=GAME_FRONT+'assets/images/ui/clan-list-icon.png';
    const hero=document.querySelector('.hero');
    if(hero)hero.style.backgroundImage=`url("${GAME_FRONT}assets/images/bg/background.jpg")`;
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
  function init(){
    document.querySelectorAll('[data-language]').forEach(button=>button.addEventListener('click',()=>apply(button.dataset.language)));
    const toggle=document.querySelector('[data-menu-toggle]'),menu=document.querySelector('[data-mobile-nav]');
    if(toggle&&menu)toggle.addEventListener('click',()=>{const open=!menu.classList.contains('open');menu.classList.toggle('open',open);toggle.setAttribute('aria-expanded',String(open))});
    replaceVisuals();
    apply(language);
  }
  window.TopKingI18n={apply,get language(){return language},strings:()=>dictionary(language)};
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init,{once:true}):init();
})();
