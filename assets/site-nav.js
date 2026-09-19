(()=>{
  const labels={
    ru:{home:'Главная',information:'Гайд по игре',announcements:'Новости игры',recipes:'Рецепты',calculators:'Калькуляторы',maps:'Карты',wars:'Клановые войны',ratings:'Рейтинг',feedback:'Обратная связь',cabinet:'Личный кабинет',game:'Игра',clan:'Клан',contact:'Связь'},
    en:{home:'Home',information:'Game guide',announcements:'Game news',recipes:'Recipes',calculators:'Calculators',maps:'Maps',wars:'Clan wars',ratings:'Rankings',feedback:'Feedback',cabinet:'Member area',game:'Game',clan:'Clan',contact:'Contact'},
    fa:{home:'خانه',information:'راهنمای بازی',announcements:'اخبار بازی',recipes:'دستورها',calculators:'محاسبه‌گرها',maps:'نقشه‌ها',wars:'جنگ‌های قبیله‌ای',ratings:'رتبه‌بندی',feedback:'بازخورد',cabinet:'پنل اعضا',game:'بازی',clan:'قبیله',contact:'ارتباط'}
  };
  const items=[['home',''],['information','information/'],['announcements','news/'],['recipes','recipes/'],['calculators','calculators/'],['maps','maps/'],['wars','wars/'],['ratings','ratings/'],['feedback','feedback/'],['cabinet','cabinet/']];
  const desktopGroups=[
    {label:'game',items:[['information','information/'],['announcements','news/'],['recipes','recipes/'],['calculators','calculators/'],['maps','maps/']]},
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
      ? current()==='news'
      : key==='cabinet'
        ? current()==='cabinet'
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
      button.setAttribute('aria-haspopup','true');
      const menu=document.createElement('div');menu.className='nav-group-menu';menu.setAttribute('role','menu');
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
      /* One desktop header geometry on every public page. */
      @media(min-width:981px){
        .site-header .shell.header-inner,.topbar .shell.topbar-inner{
          width:min(1200px,calc(100% - 48px))!important;
          min-height:78px!important;
          margin-inline:auto!important;
          display:grid!important;
          grid-template-columns:300px minmax(0,1fr) 300px!important;
          align-items:center!important;
          gap:0!important;
          justify-content:initial!important;
        }
        .site-header .brand,.topbar .brand{
          width:auto!important;
          margin:0!important;
          justify-self:start!important;
        }
        .site-header nav.desktop-nav,.topbar nav.nav{
          width:100%!important;
          min-width:0!important;
          margin:0!important;
          display:flex!important;
          align-items:center!important;
          justify-content:center!important;
          gap:3px!important;
          justify-self:center!important;
        }
        .site-header .tk-header-actions,.topbar .tk-header-actions{
          width:300px!important;
          margin:0!important;
          display:flex!important;
          align-items:center!important;
          justify-content:flex-end!important;
          gap:12px!important;
          justify-self:end!important;
        }
      }
      .tk-header-actions{display:flex;align-items:center;gap:12px;flex:0 0 auto;margin-inline-start:auto}
      .tk-header-actions .tk-desktop-cabinet{min-height:46px;display:inline-flex;align-items:center;justify-content:center;padding:11px 20px;border:1px solid rgba(232,182,84,.45);border-radius:14px;color:#ffe3a0!important;background:rgba(232,182,84,.08);font-size:14px;font-weight:800;text-decoration:none;white-space:nowrap;transition:transform .2s ease,border-color .2s ease,background .2s ease}
      .tk-header-actions .tk-desktop-cabinet:hover,.tk-header-actions .tk-desktop-cabinet.active{color:#fff!important;border-color:rgba(255,220,135,.72);background:rgba(232,182,84,.13);transform:translateY(-1px)}
      @media(max-width:980px){.tk-header-actions .tk-desktop-cabinet{display:none!important}.tk-header-actions{margin-inline-start:auto}}
      .nav-group{position:relative;display:flex;align-items:center;flex:0 0 auto}
      .nav-group-toggle{min-height:42px;padding:10px 12px;border:0;border-radius:12px;background:transparent;color:#cbd0d8;font:700 14px/1.2 Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;cursor:pointer;transition:color .2s ease,background .2s ease,transform .2s ease}
      .nav-group-toggle:hover,.nav-group-toggle.active,.nav-group.open>.nav-group-toggle{color:#fff;background:rgba(255,255,255,.075);transform:translateY(-1px)}
      .nav-group-menu{
        position:absolute;
        top:calc(100% + 5px);
        left:0;
        z-index:100;
        display:none;
        min-width:232px;
        padding:7px;
        border:1px solid rgba(255,255,255,.10);
        border-radius:14px;
        background:rgba(8,11,16,.985);
        box-shadow:0 18px 52px rgba(0,0,0,.42);
        backdrop-filter:blur(18px) saturate(130%);
        -webkit-backdrop-filter:blur(18px) saturate(130%);
      }
      .nav-group-menu::before{
        content:"";
        position:absolute;
        left:-4px;
        right:-4px;
        top:-12px;
        height:14px;
        background:transparent;
      }
      .nav-group.open>.nav-group-menu{display:grid;gap:3px}
      .nav-group-menu a{display:block!important;width:100%;margin:0!important;padding:11px 12px!important;border:0!important;border-radius:9px!important;background:transparent!important;color:#cbd0d8!important;font-size:13px!important;white-space:nowrap}
      .nav-group-menu a:hover,.nav-group-menu a.active{color:#fff!important;background:rgba(255,255,255,.075)!important;transform:none!important}
      .nav-group-menu a.active{color:#ffe3a0!important;background:rgba(232,182,84,.10)!important}
      @media (hover:hover) and (pointer:fine){
        .nav-group:hover>.nav-group-menu{display:grid;gap:3px}
      }
    `;
    document.head.appendChild(style);
  }

  function placeDesktopCabinet(){
    document.querySelectorAll('.site-header .header-inner,.topbar .topbar-inner').forEach(row=>{
      const nav=row.querySelector('nav.desktop-nav,nav.nav');
      if(!nav)return;
      const login=nav.querySelector('a.nav-login[data-site-nav="cabinet"],a.nav-login');
      if(!login)return;
      let actions=row.querySelector('.tk-header-actions');
      if(!actions){
        actions=document.createElement('div');
        actions.className='tk-header-actions';
        const menu=row.querySelector('[data-menu-toggle]');
        row.insertBefore(actions,menu||null);
      }
      const language=row.querySelector('.language-switch,.languages');
      if(language&&language.parentElement!==actions)actions.appendChild(language);
      login.classList.add('tk-desktop-cabinet');
      actions.appendChild(login);
    });
  }
  function ensureCabinetTabGroups(){
    if(current()!=='cabinet')return;
    const tabs=document.querySelector('.cab-tabs');
    if(!tabs)return;
    if(tabs.querySelector('[data-cab-group="main"]')&&tabs.querySelector('[data-cab-group="sections"]'))return;
    const specs=[
      {name:'main',label:'Основное',keys:['overview','stats','clan-shop']},
      {name:'sections',label:'Разделы',keys:['maps','install']}
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
    const closeGroup=group=>{
      if(!group)return;
      group.classList.remove('open');
      group.querySelector('.nav-group-toggle')?.setAttribute('aria-expanded','false');
    };
    const closeOthers=currentGroup=>{
      document.querySelectorAll('.nav-group.open').forEach(other=>{
        if(other!==currentGroup)closeGroup(other);
      });
    };

    document.querySelectorAll('.nav-group').forEach(group=>{
      if(group.dataset.tkWired==='1')return;
      group.dataset.tkWired='1';
      const toggle=group.querySelector('.nav-group-toggle');
      let closeTimer=0;

      const cancelClose=()=>{
        if(closeTimer){clearTimeout(closeTimer);closeTimer=0}
      };
      const open=()=>{
        cancelClose();
        closeOthers(group);
        group.classList.add('open');
        toggle?.setAttribute('aria-expanded','true');
      };
      const scheduleClose=(delay=420)=>{
        cancelClose();
        closeTimer=setTimeout(()=>{
          closeTimer=0;
          if(group.matches(':hover')||group.contains(document.activeElement))return;
          closeGroup(group);
        },delay);
      };

      toggle?.addEventListener('click',event=>{
        event.preventDefault();
        event.stopPropagation();
        const next=!group.classList.contains('open');
        if(next)open();else closeGroup(group);
      });

      // Mouse users get a forgiving corridor and a short grace period.
      group.addEventListener('pointerenter',()=>{
        if(matchMedia('(hover:hover) and (pointer:fine)').matches)open();
      });
      group.addEventListener('pointerleave',()=>{
        if(matchMedia('(hover:hover) and (pointer:fine)').matches)scheduleClose(480);
      });

      // Keyboard navigation keeps the menu open while focus is inside it.
      group.addEventListener('focusin',open);
      group.addEventListener('focusout',()=>scheduleClose(180));
    });

    if(document.documentElement.dataset.tkDesktopNavClose!=='1'){
      document.documentElement.dataset.tkDesktopNavClose='1';
      document.addEventListener('click',event=>{
        if(event.target.closest('.nav-group'))return;
        document.querySelectorAll('.nav-group.open').forEach(closeGroup);
      });
      document.addEventListener('keydown',event=>{
        if(event.key!=='Escape')return;
        document.querySelectorAll('.nav-group.open').forEach(closeGroup);
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
    document.querySelectorAll('.tk-desktop-cabinet').forEach(a=>a.remove());
    document.querySelectorAll('nav.nav,nav.desktop-nav').forEach(n=>renderContainer(n,false));
    document.querySelectorAll('nav.mobile-nav,.mobile-links').forEach(n=>renderContainer(n,true));
    placeDesktopCabinet();
    portalMobileMenus();
    wireDesktopGroups();
    wireGeneratedMenu();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',render,{once:true});else render();
  window.addEventListener('tk-language-change',render);
})();
