(()=>{
  const labels={
    ru:{home:'Главная',information:'Гайд по игре',announcements:'Новости игры',recipes:'Рецепты',calculators:'Калькуляторы',maps:'Карты',wars:'Клановые войны',ratings:'Рейтинг',feedback:'Обратная связь',cabinet:'Личный кабинет',game:'Игра',clan:'Клан',contact:'Связь'},
    en:{home:'Home',information:'Game guide',announcements:'Game news',recipes:'Recipes',calculators:'Calculators',maps:'Maps',wars:'Clan wars',ratings:'Rankings',feedback:'Feedback',cabinet:'Member area',game:'Game',clan:'Clan',contact:'Contact'},
    fa:{home:'خانه',information:'راهنمای بازی',announcements:'اخبار بازی',recipes:'دستورها',calculators:'محاسبه‌گرها',maps:'نقشه‌ها',wars:'جنگ‌های قبیله‌ای',ratings:'رتبه‌بندی',feedback:'بازخورد',cabinet:'پنل اعضا',game:'بازی',clan:'قبیله',contact:'ارتباط'}
  };
  const items=[['home',''],['information','information/'],['announcements','cabinet/?tab=announcements'],['recipes','recipes/'],['calculators','calculators/'],['maps','maps/'],['wars','wars/'],['ratings','ratings/'],['feedback','feedback/'],['cabinet','cabinet/']];
  const desktopGroups=[
    {label:'game',items:[['information','information/'],['announcements','cabinet/?tab=announcements'],['recipes','recipes/'],['calculators','calculators/'],['maps','maps/']]},
    {label:'clan',items:[['wars','wars/'],['ratings','ratings/']]},
    {label:'contact',items:[['feedback','feedback/']]}
  ];
  function lang(){const v=localStorage.getItem('tk-language');return labels[v]?v:'ru'}
  function parts(){return location.pathname.split('/').filter(Boolean)}
  function current(){const p=parts();return p[0]||'home'}
  function root(){const p=parts();if(!p.length)return './';return '../'.repeat(p.length)}
  function href(path){return root()+path}
  function ensureTheme(){
    if(current()==='home')return;
    const has=[...document.querySelectorAll('link[rel="stylesheet"]')].some(x=>(x.getAttribute('href')||'').includes('assets/public.css'));
    if(!has){const link=document.createElement('link');link.rel='stylesheet';link.href=href('assets/public.css');document.head.appendChild(link)}
    document.body.classList.add('tk-main-theme');
  }
  function anchor(key,path,mobile=false){
    const a=document.createElement('a');a.href=href(path);a.dataset.siteNav=key;a.textContent=labels[lang()][key];
    const tab=new URLSearchParams(location.search).get('tab')||'';
    const active=key==='announcements'
      ? current()==='cabinet'&&tab==='announcements'
      : key==='cabinet'
        ? current()==='cabinet'&&tab!=='announcements'
        : current()===key||(key==='home'&&current()==='home');
    if(active)a.classList.add('active');
    if(key==='cabinet')a.classList.add(mobile?'mobile-login':'nav-login');
    return a;
  }
  function renderContainer(node,mobile=false){
    if(!node)return;
    node.textContent='';
    if(mobile){
      for(const [key,path] of items)node.appendChild(anchor(key,path,true));
      return;
    }
    node.appendChild(anchor('home','',false));
    for(const group of desktopGroups){
      const wrap=document.createElement('div');wrap.className='nav-group';
      const button=document.createElement('button');button.type='button';button.className='nav-group-toggle';
      button.textContent=labels[lang()][group.label]+' ▾';
      button.setAttribute('aria-expanded','false');
      const menu=document.createElement('div');menu.className='nav-group-menu';
      for(const [key,path] of group.items){
        const a=anchor(key,path,false);
        if(a.classList.contains('active'))button.classList.add('active');
        menu.appendChild(a);
      }
      wrap.append(button,menu);
      node.appendChild(wrap);
    }
    node.appendChild(anchor('cabinet','cabinet/',false));
  }
  function ensureNavStyles(){
    if(document.getElementById('tk-grouped-nav-style'))return;
    const style=document.createElement('style');
    style.id='tk-grouped-nav-style';
    style.textContent=`
      .nav-group{position:relative;display:flex;align-items:center;flex:0 0 auto}
      .nav-group-toggle{min-height:42px;padding:10px 12px;border:0;border-radius:12px;background:transparent;color:#cbd0d8;font:700 14px/1.2 Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;cursor:pointer;transition:color .2s ease,background .2s ease,transform .2s ease}
      .nav-group-toggle:hover,.nav-group-toggle.active,.nav-group.open>.nav-group-toggle{color:#fff;background:rgba(255,255,255,.075);transform:translateY(-1px)}
      .nav-group-menu{position:absolute;top:calc(100% + 8px);left:0;z-index:100;display:none;min-width:220px;padding:7px;border:1px solid rgba(255,255,255,.10);border-radius:14px;background:rgba(8,11,16,.98);box-shadow:0 18px 52px rgba(0,0,0,.42);backdrop-filter:blur(18px) saturate(130%);-webkit-backdrop-filter:blur(18px) saturate(130%)}
      .nav-group.open>.nav-group-menu{display:grid;gap:3px}
      .nav-group-menu a{display:block!important;width:100%;margin:0!important;padding:10px 11px!important;border:0!important;border-radius:9px!important;background:transparent!important;color:#cbd0d8!important;font-size:13px!important;white-space:nowrap}
      .nav-group-menu a:hover,.nav-group-menu a.active{color:#fff!important;background:rgba(255,255,255,.075)!important;transform:none!important}
      .nav-group-menu a.active{color:#ffe3a0!important;background:rgba(232,182,84,.10)!important}
      @media (hover:hover) and (pointer:fine){
        .nav-group:hover>.nav-group-menu{display:grid;gap:3px}
      }
    `;
    document.head.appendChild(style);
  }

  function ensureCabinetTabGroups(){
    if(current()!=='cabinet')return;
    const tabs=document.querySelector('.cab-tabs');
    if(!tabs)return;
    if(tabs.querySelector('[data-cab-group="main"]')&&tabs.querySelector('[data-cab-group="sections"]'))return;
    const specs=[
      {name:'main',label:'Основное',keys:['overview','stats','clan-shop']},
      {name:'sections',label:'Разделы',keys:['announcements','maps','install']}
    ];
    const byKey=new Map([...tabs.querySelectorAll('[data-cab-tab]')].map(button=>[button.dataset.cabTab,button]));
    if(!specs.some(group=>group.keys.some(key=>byKey.has(key))))return;
    tabs.textContent='';
    for(const spec of specs){
      const group=document.createElement('div');
      group.className='cab-tab-group';
      group.dataset.cabGroup=spec.name;
      const label=document.createElement('span');
      label.className='cab-tab-group-label';
      label.textContent=spec.label;
      group.appendChild(label);
      for(const key of spec.keys){
        const button=byKey.get(key);
        if(button)group.appendChild(button);
      }
      if(group.querySelector('[data-cab-tab]'))tabs.appendChild(group);
    }
    tabs.classList.add('tk-cab-tabs-grouped');
    if(!document.getElementById('tk-cabinet-group-fallback-style')){
      const style=document.createElement('style');
      style.id='tk-cabinet-group-fallback-style';
      style.textContent=`
        .cab-tabs.tk-cab-tabs-grouped{display:grid!important;grid-template-columns:minmax(0,1.05fr) minmax(0,.95fr)!important;gap:8px!important;overflow:visible!important}
        .cab-tabs.tk-cab-tabs-grouped .cab-tab-group{min-width:0;display:flex;align-items:center;gap:5px;padding:3px;border:1px solid rgba(255,255,255,.055);border-radius:13px;background:rgba(255,255,255,.018)}
        .cab-tabs.tk-cab-tabs-grouped .cab-tab-group-label{flex:0 0 auto;padding:0 7px;color:#727c89;font-size:10px;font-weight:900;letter-spacing:.08em;text-transform:uppercase;white-space:nowrap}
        @media(max-width:760px){
          .cab-tabs.tk-cab-tabs-grouped{grid-template-columns:1fr!important;gap:7px!important}
          .cab-tabs.tk-cab-tabs-grouped .cab-tab-group{width:100%;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:5px;overflow:visible;padding:5px}
          .cab-tabs.tk-cab-tabs-grouped .cab-tab-group-label{grid-column:1/-1;padding:0 3px 2px;background:transparent;font-size:9px}
        }
      `;
      document.head.appendChild(style);
    }
  }
  function createHeader(){
    if(current()==='home'||document.querySelector('.topbar,.site-header'))return;
    const header=document.createElement('header');header.className='topbar tk-generated-header';
    header.innerHTML=`<div class="shell topbar-inner"><a class="brand" href="${href('')}"><img src="https://cdn-prod-front-dist.hwgame.cloud/assets/images/ui/clan-list-icon.png" alt=""><span>TOP KING</span></a><nav class="nav" aria-label="Navigation"></nav><button class="menu-toggle" type="button" data-menu-toggle aria-expanded="false" aria-label="Menu">☰</button></div><nav class="mobile-nav" data-mobile-nav></nav>`;
    document.body.prepend(header);document.body.classList.add('tk-synthetic-header');
  }
  function normalizeExistingHeader(){
    document.querySelectorAll('.topbar .brand img').forEach(img=>img.src='https://cdn-prod-front-dist.hwgame.cloud/assets/images/ui/clan-list-icon.png');
    document.querySelectorAll('nav.tabs[aria-label="Разделы сайта"]').forEach(n=>n.classList.add('tk-legacy-site-nav'));
  }
  function portalMobileMenus(){
    document.querySelectorAll('[data-mobile-nav]').forEach(menu=>{
      if(menu.parentElement!==document.body){
        menu.dataset.tkMobilePortal='1';
        document.body.appendChild(menu);
      }
    });
  }
  function closeMobileMenu(){
    const menu=document.querySelector('[data-mobile-nav]');
    document.querySelectorAll('[data-menu-toggle]').forEach(toggle=>toggle.setAttribute('aria-expanded','false'));
    if(menu)menu.classList.remove('open');
    document.body.classList.remove('menu-open');
  }
  function wireDesktopGroups(){
    document.querySelectorAll('.nav-group').forEach(group=>{
      if(group.dataset.tkWired==='1')return;
      group.dataset.tkWired='1';
      const toggle=group.querySelector('.nav-group-toggle');
      const close=()=>{group.classList.remove('open');toggle?.setAttribute('aria-expanded','false')};
      toggle?.addEventListener('click',event=>{
        event.preventDefault();
        event.stopPropagation();
        const next=!group.classList.contains('open');
        document.querySelectorAll('.nav-group.open').forEach(other=>{
          if(other!==group){
            other.classList.remove('open');
            other.querySelector('.nav-group-toggle')?.setAttribute('aria-expanded','false');
          }
        });
        group.classList.toggle('open',next);
        toggle.setAttribute('aria-expanded',String(next));
      });
      group.addEventListener('mouseleave',close);
    });
    if(document.documentElement.dataset.tkDesktopNavClose!=='1'){
      document.documentElement.dataset.tkDesktopNavClose='1';
      document.addEventListener('click',event=>{
        if(event.target.closest('.nav-group'))return;
        document.querySelectorAll('.nav-group.open').forEach(group=>{
          group.classList.remove('open');
          group.querySelector('.nav-group-toggle')?.setAttribute('aria-expanded','false');
        });
      });
    }
  }

  function wireGeneratedMenu(){
    document.querySelectorAll('[data-menu-toggle]').forEach(toggle=>{
      if(toggle.dataset.tkWired==='1')return;toggle.dataset.tkWired='1';
      toggle.addEventListener('click',event=>{
        event.preventDefault();
        event.stopPropagation();
        const menu=document.querySelector('[data-mobile-nav]');if(!menu)return;
        const open=!menu.classList.contains('open');
        if(open){
          menu.classList.add('open');
          toggle.setAttribute('aria-expanded','true');
          document.body.classList.add('menu-open');
          menu.scrollTop=0;
        }else{
          closeMobileMenu();
        }
      });
    });
    const menu=document.querySelector('[data-mobile-nav]');
    if(menu&&menu.dataset.tkLinksWired!=='1'){
      menu.dataset.tkLinksWired='1';
      menu.addEventListener('click',event=>{
        if(event.target.closest('a,button'))closeMobileMenu();
      });
    }
    if(document.documentElement.dataset.tkMenuEscape!=='1'){
      document.documentElement.dataset.tkMenuEscape='1';
      document.addEventListener('keydown',event=>{if(event.key==='Escape')closeMobileMenu()});
    }
  }
  function render(){
    ensureTheme();ensureNavStyles();createHeader();normalizeExistingHeader();ensureCabinetTabGroups();
    document.querySelectorAll('nav.nav,nav.desktop-nav').forEach(n=>renderContainer(n,false));
    document.querySelectorAll('nav.mobile-nav,.mobile-links').forEach(n=>renderContainer(n,true));
    portalMobileMenus();
    wireDesktopGroups();
    wireGeneratedMenu();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',render,{once:true});else render();
  window.addEventListener('tk-language-change',render);
})();
