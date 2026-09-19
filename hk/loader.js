(()=>{try{
  if(location.hostname!=='app.hamsterking.games'){
    alert('Откройте https://app.hamsterking.games и нажмите закладку HK ещё раз.');
    return;
  }
  if(window.__HK_BOOKMARKLET_LOADING__)return;
  if(window.__HK_MOBILE_LOADED__){
    alert('HK уже запущен на этой странице. Для загрузки новой версии обновите игру и снова нажмите закладку.');
    return;
  }
  window.__HK_BOOKMARKLET_LOADING__=true;
  let badge=document.getElementById('tk-hk-loader-badge');
  if(!badge){
    badge=document.createElement('div');
    badge.id='tk-hk-loader-badge';
    badge.style.cssText='position:fixed;right:16px;bottom:20px;z-index:2147483647;padding:11px 14px;border-radius:12px;background:#17130d;color:#f4cf75;border:1px solid #b68a35;font:700 13px Arial,sans-serif;box-shadow:0 8px 28px #0009';
    document.documentElement.appendChild(badge);
  }
  badge.textContent='HK · загружаю актуальную версию…';
  const script=document.createElement('script');
  script.src='https://hk-license.89.125.1.71.sslip.io/panel.js?v='+Date.now();
  script.async=true;
  script.onload=()=>{badge.textContent='HK · запущен';setTimeout(()=>badge.remove(),2200);window.__HK_BOOKMARKLET_LOADING__=false;};
  script.onerror=()=>{badge.textContent='HK · ошибка загрузки';window.__HK_BOOKMARKLET_LOADING__=false;alert('Не удалось загрузить HK. Проверьте интернет и попробуйте ещё раз.');};
  (document.head||document.documentElement).appendChild(script);
}catch(error){window.__HK_BOOKMARKLET_LOADING__=false;alert('HK: '+(error&&error.message||error));}})();