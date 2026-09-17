(()=>{
  const labels={
    ru:{home:'Главная',information:'Информация',recipes:'Рецепты',calculators:'Калькуляторы',maps:'Карты',wars:'Клановые войны',ratings:'Рейтинг',feedback:'Обратная связь',cabinet:'Личный кабинет'},
    en:{home:'Home',information:'Information',recipes:'Recipes',calculators:'Calculators',maps:'Maps',wars:'Clan wars',ratings:'Rankings',feedback:'Feedback',cabinet:'Member area'},
    fa:{home:'خانه',information:'اطلاعات',recipes:'دستورها',calculators:'محاسبه‌گرها',maps:'نقشه‌ها',wars:'جنگ‌های قبیله‌ای',ratings:'رتبه‌بندی',feedback:'بازخورد',cabinet:'پنل اعضا'}
  };
  const items=[['home',''],['information','information/'],['recipes','recipes/'],['calculators','calculators/'],['maps','maps/'],['wars','wars/'],['ratings','ratings/'],['feedback','feedback/'],['cabinet','cabinet/']];
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
    if(current()===key||(key==='home'&&current()==='home'))a.classList.add('active');
    if(key==='cabinet')a.classList.add(mobile?'mobile-login':'nav-login');
    return a;
  }
  function renderContainer(node,mobile=false){if(!node)return;node.textContent='';for(const [key,path] of items)node.appendChild(anchor(key,path,mobile))}
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
  function wireMenu(){
    document.querySelectorAll('[data-menu-toggle]').forEach(toggle=>{
      if(toggle.dataset.tkWired==='1')return;toggle.dataset.tkWired='1';
      toggle.addEventListener('click',()=>{
        const header=toggle.closest('header')||document;
        const menu=header.querySelector('[data-mobile-nav]')||document.querySelector('[data-mobile-nav]');if(!menu)return;
        const open=!menu.classList.contains('open');menu.classList.toggle('open',open);toggle.setAttribute('aria-expanded',String(open));document.body.classList.toggle('menu-open',open);
      });
    });
  }
  function render(){
    ensureTheme();createHeader();normalizeExistingHeader();
    document.querySelectorAll('nav.nav,nav.desktop-nav').forEach(n=>renderContainer(n,false));
    document.querySelectorAll('nav.mobile-nav,.mobile-links').forEach(n=>renderContainer(n,true));
    wireMenu();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',render,{once:true});else render();
  window.addEventListener('tk-language-change',render);
})();
