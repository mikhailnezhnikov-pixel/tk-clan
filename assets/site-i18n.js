(()=>{
  const CORE={
    ru:{home:'Главная',calculators:'Калькуляторы',recipes:'Рецепты',wars:'Клановые войны',ratings:'Рейтинг',information:'Гайд по игре',announcements:'Новости игры',newsCard:'Официальные новости Hamster King, обновления, события и патчноуты.',newsBadge:'Новости',feedback:'Обратная связь',cabinet:'Личный кабинет',menu:'Меню',footer:'Top King · Hamster King',play:'Начать играть',loading:'Загрузка…',updated:'Обновлено',noData:'Данных пока нет',error:'Не удалось загрузить данные.'},
    en:{home:'Home',calculators:'Calculators',recipes:'Recipes',wars:'Clan wars',ratings:'Rankings',information:'Game guide',announcements:'Game news',newsCard:'Official Hamster King news, updates, events and patch notes.',newsBadge:'News',feedback:'Feedback',cabinet:'Member area',menu:'Menu',footer:'Top King · Hamster King',play:'Play now',loading:'Loading…',updated:'Updated',noData:'No data yet',error:'Could not load data.'},
    fa:{home:'خانه',calculators:'محاسبه‌گرها',recipes:'دستورها',wars:'جنگ‌های قبیله‌ای',ratings:'رتبه‌بندی',information:'راهنمای بازی',announcements:'اخبار بازی',newsCard:'اخبار رسمی Hamster King، به‌روزرسانی‌ها، رویدادها و یادداشت‌های نسخه.',newsBadge:'اخبار',feedback:'بازخورد',cabinet:'پنل اعضا',menu:'منو',footer:'Top King · Hamster King',play:'شروع بازی',loading:'در حال بارگذاری…',updated:'به‌روزرسانی',noData:'هنوز داده‌ای وجود ندارد',error:'بارگذاری داده‌ها ممکن نشد.'}
  };
  const supported=['ru','en','fa'];
  const saved=localStorage.getItem('tk-language');
  const browser=(navigator.language||'ru').slice(0,2).toLowerCase();
  let language=supported.includes(saved)?saved:(supported.includes(browser)?browser:'ru');
  const dictionary=lang=>Object.assign({},CORE[lang]||CORE.ru,(window.TK_PAGE_TRANSLATIONS||{})[lang]||{});
  const GAME_FRONT='https://cdn-prod-front-dist.hwgame.cloud/';
  const GAME_ART='https://cdn-prod-art.hwgame.cloud/';
  const OFFICIAL_VISUALS={calculators:'assets/images/ui/boss-fight.png',recipes:'assets/images/ui/collections.png',cabinet:'assets/images/ui/clan-members-icon.png',wars:'assets/images/ui/vs.png',ratings:'assets/images/ui/nominations-1.png',information:'assets/images/ui/info-stars.png',announcements:'assets/images/ui/info-stars.png',feedback:'assets/images/ui/telegram-1.png'};
  function fitGameIcon(img){img.style.objectFit='contain';if(img.closest('.card-icon,.quick-icon'))img.style.padding='5px'}
  function replaceVisuals(){for(const[section,path]of Object.entries(OFFICIAL_VISUALS)){document.querySelectorAll(`a[href*="${section}"] .card-icon img,a[href*="${section}"] .quick-icon img`).forEach(img=>{img.src=GAME_FRONT+path;fitGameIcon(img)})}document.querySelectorAll('.brand img').forEach(img=>{img.src=GAME_FRONT+'assets/images/ui/clan-list-icon.png';fitGameIcon(img)});const icon=document.querySelector('link[rel="icon"]');if(icon)icon.href=GAME_FRONT+'assets/images/ui/clan-list-icon.png'}

  const GUIDE_CONFIRMED_ICON_MAP={
    '101':GAME_ART+'quests/qst_clan_daily_pit_icon.png',
    '100':GAME_ART+'quests/qst_clan_daily_bosspit_icon.png',
    '99':GAME_ART+'quests/qst_clan_daily_mobpit_icon.png',
    '102':GAME_FRONT+'assets/images/ui/boss-fight.png',
    '26':GAME_ART+'currencies/cur_build_icon.png',
    '27':GAME_ART+'currencies/cur_cap_icon.png',
    '28':GAME_ART+'shop_lots/icons_card/mf_divider_resources.png',
    '31':GAME_ART+'items/item_invest_cur_icon.png',
    '32':GAME_ART+'items/item_clan_cur_icon.png',
    '33':GAME_ART+'currencies/cur_prem_icon.png',
    '97':GAME_ART+'currencies/cur_prem_icon.png',
    '104':GAME_ART+'items/item_pit_rat_tokens_icon.png',
    '110':GAME_ART+'items/item_bsn_r2_tier2_trig_rumor_energy_energy_icon.png',
    '123':GAME_ART+'currencies/cur_alliance_icon.png',
    '128':GAME_ART+'bonuses/general_power_bonus_icon.png',
    '129':GAME_ART+'currencies/cur_clan_war_attack_pass_icon.png',
    '131':GAME_ART+'items/item_bsn_reverse_transfig_t5_icon.png',
    '132':GAME_ART+'items/item_bsn_reverse_transfig_t8_icon.png',
    '150':GAME_ART+'items/item_business_dust_icon.png',
    '25':GAME_ART+'currencies/cur_nut_icon.png',
    '115':GAME_ART+'battle_passes/icons/bp_personal_area_boss_paid_01_icon.png'
  };
  const GUIDE_SECTION_ICON_MAP={
    power:GAME_FRONT+'assets/images/ui/hamster-ball.png',
    generals:GAME_ART+'items/item_hball_hgen_beasthelper_g1_ssplus_icon.png',
    battles:GAME_FRONT+'assets/images/ui/fights.png',
    clans:GAME_FRONT+'assets/images/ui/clan-list-icon.png',
    resources:GAME_FRONT+'assets/images/ui/inventory.png',
    business:GAME_ART+'currencies/cur_build_icon.png',
    recipes:GAME_FRONT+'assets/images/ui/collections.png',
    calculators:GAME_FRONT+'assets/images/ui/diary.png',
    maps:GAME_FRONT+'assets/images/menu/city-1.png'
  };
  function styleGuideIcon(img,id){img.dataset.originalGuideIcon=id;img.style.width='24px';img.style.height='24px';img.style.objectFit='contain';img.style.verticalAlign='middle';img.style.margin='0 4px'}
  function makeGameIcon(src,label,id){const img=document.createElement('img');img.className='inline-icon';img.dataset.gameIcon=id||label;img.src=src;img.alt=label;img.title=label;styleGuideIcon(img,id||label);return img}
  function putGameIconBefore(node,src,label,id){
    if(!node)return;
    const marker=id||label;
    if(node.querySelector(`img[data-game-icon="${marker}"]`))return;
    const img=makeGameIcon(src,label,marker);
    const text=(node.textContent||'').replace(/^[^\p{L}\p{N}]+/u,'').trim();
    node.textContent='';
    node.append(img,' ',document.createTextNode(text));
  }
  function replaceLeadingEmoji(node,src,label,id,emojiPattern){
    if(!node)return;
    const marker=id||label;
    if(node.querySelector(`img[data-game-icon="${marker}"]`))return;
    node.innerHTML=node.innerHTML.replace(emojiPattern,'');
    node.prepend(makeGameIcon(src,label,marker),' ');
  }
  function stripLeadingEmoji(node,emojiPattern){if(node)node.innerHTML=node.innerHTML.replace(emojiPattern,'')}
  function upgradeInformationIcons(){
    if(!document.getElementById('guide'))return;
    document.querySelectorAll('#guide img.inline-icon').forEach(img=>{
      const original=img.getAttribute('src')||'';
      const match=original.match(/guide-emoji\/(\d+)\.png(?:\?.*)?$/);
      if(!match)return;
      const replacement=GUIDE_CONFIRMED_ICON_MAP[match[1]];
      if(!replacement)return;
      img.src=replacement;styleGuideIcon(img,match[1]);
    });
    document.querySelectorAll('#battles img.inline-icon,#calculators img.inline-icon').forEach(img=>{
      const original=img.getAttribute('src')||'';
      if(!/guide-emoji\/98\.png(?:\?.*)?$/.test(original))return;
      img.src=GAME_FRONT+'assets/images/ui/regional-bosses.png';styleGuideIcon(img,'98');
    });
    document.querySelectorAll('#battles .guide-row').forEach(row=>{
      const label=row.querySelector('b');
      if(!label||label.textContent.trim()!=='PVP')return;
      if(row.querySelector('img[data-game-icon="pvp-arena"]'))return;
      row.textContent='';
      const strong=document.createElement('b');strong.textContent='PVP';
      row.append(makeGameIcon(GAME_FRONT+'assets/images/ui/pvp-arena.png','PVP','pvp-arena'),' ',strong);
    });

    const resources=document.getElementById('resources');
    if(resources){
      resources.querySelectorAll('.guide-row').forEach(row=>{
        const text=(row.textContent||'').trim();
        if(text.includes('Ярмарка')&&text.includes('Менеджеры')&&text.includes('Бизнес-центры')){
          const img=row.querySelector('img.inline-icon');
          if(img){img.src=GAME_ART+'items/item_invest_cur_icon.png';img.alt='Инвестиционная монета';img.title='Инвестиционная монета';img.dataset.gameIcon='invest-coin-resource';}
        }
      });
    }

    const clans=document.getElementById('clans');
    if(clans){
      clans.querySelectorAll('h3').forEach(h3=>{
        const text=(h3.textContent||'').trim();
        if(text.includes('Клановые войны')){
          putGameIconBefore(h3,GAME_FRONT+'assets/images/ui/war-shields.png','Клановые войны','clan-wars');
        }else if(text.includes('КЛАНОВАЯ ВАЛЮТА И МАГАЗИНЫ')){
          putGameIconBefore(h3,GAME_ART+'items/item_clan_cur_icon.png','Клановая валюта','clan-currency');
        }else if(text.includes('1. Магазин Клана и Общий магазин')){
          putGameIconBefore(h3,GAME_FRONT+'assets/images/menu/shop-1.png','Магазин Клана и Общий магазин','clan-shop');
        }else if(text.includes('2. Магазин Альянса')){
          putGameIconBefore(h3,GAME_FRONT+'assets/images/menu/shop-1.png','Магазин Альянса','alliance-shop');
        }else if(text.includes('3. Магазин')&&text.includes('Трофеи Охоты на крыс')){
          putGameIconBefore(h3,GAME_ART+'bosses/rats_05_icon.png','Крыса','rat-shop');
        }
      });
      clans.querySelectorAll('p > b').forEach(label=>{
        const text=(label.textContent||'').trim();
        if(text==='Магазин Клана'){
          putGameIconBefore(label,GAME_FRONT+'assets/images/menu/shop-1.png','Магазин Клана','clan-shop-label');
        }else if(text==='Общий магазин Клана'){
          putGameIconBefore(label,GAME_FRONT+'assets/images/menu/shop-1.png','Общий магазин Клана','clan-shop-common');
        }
      });
      clans.querySelectorAll('p').forEach(p=>{
        const text=(p.textContent||'').trim();
        if(text.startsWith('💰')&&text.includes('Валюта:')){
          replaceLeadingEmoji(p,GAME_ART+'items/item_invest_cur_icon.png','Инвестиционная монета','clan-currency-line',/^\s*💰\s*/u);
        }else if(text.startsWith('💰')&&text.includes('Покупки осуществляются')){
          replaceLeadingEmoji(p,GAME_ART+'items/item_clan_cur_icon.png','Золото Клана','clan-gold-line',/^\s*💰\s*/u);
        }else if(text.startsWith('💰')&&text.includes('Альянсовая валюта')){
          replaceLeadingEmoji(p,GAME_ART+'currencies/cur_alliance_icon.png','Альянсовая валюта','alliance-currency-line',/^\s*💰\s*/u);
        }else if(text.startsWith('🛒')&&text.includes('Совершать покупки')){
          replaceLeadingEmoji(p,GAME_FRONT+'assets/images/menu/shop-1.png','Магазин','alliance-buy-line',/^\s*🛒\s*/u);
        }else if(text.startsWith('⚔️')&&text.includes('Хвосты добываются')){
          replaceLeadingEmoji(p,GAME_ART+'bosses/rats_05_icon.png','Бой с крысами','rat-fight-line',/^\s*⚔️\s*/u);
        }
      });
    }

    const recipes=document.getElementById('recipes');
    if(recipes){
      recipes.querySelectorAll('p').forEach(p=>{
        const text=(p.textContent||'').trim();
        if(text.startsWith('🔎')&&text.includes('Поиск рецептов')){
          stripLeadingEmoji(p,/^\s*🔎\s*/u);
        }else if(text.startsWith('🏭')&&text.includes('Крафт бизнесов')){
          replaceLeadingEmoji(p,GAME_ART+'shop_lots/icons_modal/craft_result_model_icon.png','Крафт бизнесов','craft-business',/^\s*🏭\s*/u);
        }else if(text.startsWith('🔥')&&text.includes('Приоритет сделать')){
          p.innerHTML=p.innerHTML.replace(/^\s*🔥\s*/u,'');
          const existing=p.querySelector('img[data-original-guide-icon="110"]');
          if(existing){existing.remove();existing.dataset.gameIcon='rumor-business';p.prepend(existing,' ')}
          else replaceLeadingEmoji(p,GAME_ART+'items/item_bsn_r2_tier2_trig_rumor_energy_energy_icon.png','Бизнес на слухи','rumor-business',/^/u);
        }
      });
    }
  }
  function upgradeInformationSectionIcons(){
    if(!document.getElementById('guide'))return;
    for(const[id,src]of Object.entries(GUIDE_SECTION_ICON_MAP)){
      const article=document.getElementById(id),h2=article&&article.querySelector('h2');if(!h2||h2.dataset.gameSectionIcon==='1')continue;
      const raw=(h2.textContent||'').trim();const clean=raw.replace(/^[🎮🗣🚀💪⭐⚔️👑🪙💰🏢🍳📊🗺💡🛠\s]+/u,'').trim()||raw;
      h2.textContent='';const wrap=document.createElement('span');wrap.style.display='inline-flex';wrap.style.alignItems='center';wrap.style.gap='10px';const icon=document.createElement('img');icon.src=src;icon.alt='';icon.style.width='34px';icon.style.height='34px';icon.style.objectFit='contain';icon.style.flex='0 0 auto';const label=document.createElement('span');label.textContent=clean;wrap.append(icon,label);h2.append(wrap);h2.dataset.gameSectionIcon='1';
    }
  }
  function refreshInformationVisuals(){upgradeInformationIcons();upgradeInformationSectionIcons()}
  function watchInformationGuide(){
    const guide=document.getElementById('guide');
    if(!guide||guide.dataset.visualObserver==='1')return;
    guide.dataset.visualObserver='1';
    let queued=false;
    const observer=new MutationObserver(()=>{
      if(queued)return;
      queued=true;
      requestAnimationFrame(()=>{queued=false;refreshInformationVisuals()});
    });
    observer.observe(guide,{childList:true,subtree:true});
  }
  function configureHomepage(){
    const hero=document.querySelector('main .hero');if(!hero)return;
    hero.style.setProperty('background-image','url("assets/home/top-king-clan-hero-approved.jpg")','important');
    const actions=hero.querySelector('.hero-actions');
    if(actions)actions.innerHTML='<a class="button primary" href="https://app.hamsterking.games/app.html" target="_blank" rel="noopener" data-i18n="play">Начать играть</a>';
    if(!document.getElementById('tk-home-responsive')){
      const style=document.createElement('style');
      style.id='tk-home-responsive';
      style.textContent=`
        .hero{
          background-image:url("assets/home/top-king-clan-hero-approved.jpg")!important;
          background-position:58% center!important;
          background-repeat:no-repeat!important;
          background-size:cover!important;
          background-color:#07080b!important;
        }
        .hero-copy{width:min(540px,45%)!important}
        .hero-actions .button{min-width:190px}
        @media(max-width:980px) and (min-width:681px){
          .hero{background-position:56% center!important}
          .hero-copy{width:min(540px,54%)!important}
        }
        @media(max-width:680px){
          body{
            background:
              radial-gradient(ellipse at 55% 7%,rgba(232,182,84,.08),transparent 30%),
              linear-gradient(180deg,#08090d 0%,#07080b 54%,#07080b 100%)!important;
          }
          .hero{
            min-height:900px!important;
            align-items:flex-start!important;
            overflow:hidden!important;
            isolation:isolate!important;
            background-image:none!important;
            background:
              radial-gradient(ellipse at 52% 26%,rgba(232,182,84,.09),transparent 36%),
              linear-gradient(180deg,#090b0f 0%,#07080b 72%)!important;
          }
          .hero::before{
            content:""!important;
            position:absolute!important;
            inset:0 0 auto 0!important;
            height:clamp(350px,78vw,455px)!important;
            z-index:-2!important;
            pointer-events:none!important;
            background:
              linear-gradient(90deg,rgba(5,7,10,.10),rgba(5,7,10,.02) 48%,rgba(5,7,10,.14)),
              url("assets/home/top-king-clan-hero-approved.jpg") 56% top / cover no-repeat!important;
            -webkit-mask-image:linear-gradient(to bottom,#000 0%,#000 56%,rgba(0,0,0,.92) 67%,rgba(0,0,0,.56) 80%,transparent 100%)!important;
            mask-image:linear-gradient(to bottom,#000 0%,#000 56%,rgba(0,0,0,.92) 67%,rgba(0,0,0,.56) 80%,transparent 100%)!important;
          }
          .hero::after{
            content:""!important;
            position:absolute!important;
            inset:0!important;
            z-index:-1!important;
            pointer-events:none!important;
            background:
              radial-gradient(ellipse at 52% 30%,rgba(226,160,48,.12),transparent 30%),
              linear-gradient(180deg,transparent 0%,rgba(7,8,11,.02) 28%,rgba(7,8,11,.32) 43%,rgba(7,8,11,.82) 57%,#07080b 75%,#07080b 100%)!important;
            animation:none!important;
          }
          .hero-inner{
            width:100%!important;
            padding:clamp(315px,72vw,390px) 16px 258px!important;
          }
          .hero-copy{
            width:100%!important;
            max-width:560px!important;
          }
          .hero .eyebrow{
            margin-bottom:11px!important;
            font-size:10px!important;
            letter-spacing:.17em!important;
          }
          .hero h1{
            max-width:540px!important;
            font-size:clamp(39px,10.9vw,50px)!important;
            line-height:.96!important;
            letter-spacing:-.047em!important;
          }
          .hero .lead{
            max-width:540px!important;
            margin-top:16px!important;
            font-size:15px!important;
            line-height:1.52!important;
          }
          .hero-actions{margin-top:20px!important}
          .hero-actions .button{
            width:100%!important;
            min-width:0!important;
            min-height:52px!important;
            flex:1 1 100%!important;
          }
          .quick-panel{
            bottom:16px!important;
            width:calc(100% - 32px)!important;
            gap:8px!important;
          }
          .quick-link{
            min-height:62px!important;
            border-color:rgba(255,255,255,.10)!important;
            background:
              radial-gradient(circle at 93% 0%,rgba(232,182,84,.09),transparent 32%),
              linear-gradient(145deg,rgba(18,22,29,.76),rgba(8,11,16,.70))!important;
            box-shadow:0 14px 38px rgba(0,0,0,.16)!important;
            backdrop-filter:blur(17px) saturate(120%)!important;
            -webkit-backdrop-filter:blur(17px) saturate(120%)!important;
          }
          #sections{
            margin-top:-1px!important;
            padding-top:62px!important;
            background:
              radial-gradient(ellipse at 50% 0%,rgba(232,182,84,.055),transparent 28%),
              linear-gradient(180deg,#07080b 0%,rgba(7,8,11,.98) 100%)!important;
          }
          .portal-card{
            border-color:rgba(255,255,255,.10)!important;
            background:
              radial-gradient(circle at 94% 3%,rgba(232,182,84,.10),transparent 30%),
              linear-gradient(145deg,rgba(18,22,29,.78),rgba(8,11,16,.72))!important;
            box-shadow:0 16px 46px rgba(0,0,0,.17)!important;
            backdrop-filter:blur(18px) saturate(120%)!important;
            -webkit-backdrop-filter:blur(18px) saturate(120%)!important;
          }
        }
        @media(max-width:420px){
          .hero{min-height:875px!important}
          .hero::before{height:350px!important}
          .hero-inner{padding-top:300px!important;padding-bottom:252px!important}
          .hero h1{font-size:clamp(37px,11.3vw,47px)!important}
          .hero .lead{font-size:14.5px!important}
        }
      `;
      document.head.append(style);
    }
  }
  function apply(lang=language){language=supported.includes(lang)?lang:'ru';localStorage.setItem('tk-language',language);const strings=dictionary(language);document.documentElement.lang=language;document.documentElement.dir=language==='fa'?'rtl':'ltr';document.querySelectorAll('[data-i18n]').forEach(node=>{const value=strings[node.dataset.i18n];if(value!=null)node.textContent=value});document.querySelectorAll('[data-i18n-html]').forEach(node=>{const value=strings[node.dataset.i18nHtml];if(value!=null)node.innerHTML=value});document.querySelectorAll('[data-i18n-placeholder]').forEach(node=>{const value=strings[node.dataset.i18nPlaceholder];if(value!=null)node.placeholder=value});document.querySelectorAll('[data-language]').forEach(button=>{const active=button.dataset.language===language;button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active))});if(strings.pageTitle)document.title=strings.pageTitle;document.dispatchEvent(new CustomEvent('tk-language-change',{detail:{language,strings}}))}
  function init(){document.querySelectorAll('[data-language]').forEach(button=>button.addEventListener('click',()=>apply(button.dataset.language)));const toggle=document.querySelector('[data-menu-toggle]'),menu=document.querySelector('[data-mobile-nav]');if(toggle&&menu)toggle.addEventListener('click',()=>{const open=!(menu.classList.contains('open')||menu.classList.contains('is-open'));menu.classList.toggle('open',open);menu.classList.toggle('is-open',open);toggle.setAttribute('aria-expanded',String(open));document.body.classList.toggle('menu-open',open)});replaceVisuals();configureHomepage();apply(language);refreshInformationVisuals();watchInformationGuide();document.addEventListener('tk-language-change',()=>setTimeout(refreshInformationVisuals,0))}
  window.TopKingI18n={apply,get language(){return language},strings:()=>dictionary(language)};document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init,{once:true}):init();
})();