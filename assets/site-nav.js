(()=>{
  const labels={
    ru:{home:'Главная',information:'Информация',recipes:'Рецепты',calculators:'Калькуляторы',maps:'Карты',wars:'Клановые войны',ratings:'Рейтинг',feedback:'Обратная связь',cabinet:'Личный кабинет'},
    en:{home:'Home',information:'Information',recipes:'Recipes',calculators:'Calculators',maps:'Maps',wars:'Clan wars',ratings:'Rankings',feedback:'Feedback',cabinet:'Member area'},
    fa:{home:'خانه',information:'اطلاعات',recipes:'دستورها',calculators:'محاسبه‌گرها',maps:'نقشه‌ها',wars:'جنگ‌های قبیله‌ای',ratings:'رتبه‌بندی',feedback:'بازخورد',cabinet:'پنل اعضا'}
  };
  const items=[
    ['home',''],['information','information/'],['recipes','recipes/'],['calculators','calculators/'],['maps','maps/'],['wars','wars/'],['ratings','ratings/'],['feedback','feedback/'],['cabinet','cabinet/']
  ];
  function lang(){const v=localStorage.getItem('tk-language');return labels[v]?v:'ru'}
  function current(){const p=location.pathname.split('/').filter(Boolean);return p[0]||'home'}
  function root(){const p=location.pathname.split('/').filter(Boolean);if(!p.length)return './';return '../'.repeat(p.length)}
  function href(path){return root()+path}
  function anchor(key,path,mobile=false){const a=document.createElement('a');a.href=href(path);a.dataset.siteNav=key;a.textContent=labels[lang()][key];if(current()===key||(key==='home'&&current()==='home'))a.classList.add('active');if(key==='cabinet'){a.classList.add(mobile?'mobile-login':'nav-login')}return a}
  function renderContainer(node,mobile=false){if(!node)return;node.textContent='';for(const [key,path] of items)node.appendChild(anchor(key,path,mobile))}
  function render(){
    document.querySelectorAll('nav.nav,nav.desktop-nav').forEach(n=>renderContainer(n,false));
    document.querySelectorAll('nav.mobile-nav,.mobile-links').forEach(n=>renderContainer(n,true));
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',render,{once:true});else render();
  window.addEventListener('tk-language-change',render);
})();
