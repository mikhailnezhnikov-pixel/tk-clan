(()=>{
  'use strict';
  const HOST='app.hamsterking.games';
  const CORE_URL='https://hk-license.89.125.1.71.sslip.io/panel.js';
  const LOCK_KEY='__HK_BOOKMARKLET_RUNTIME__';
  const LOADER_REV='loader-20260921-r25';
  const EXPECTED_CORE_REV='core-20260921-r28-businesses-finalize';
  const TIMEOUTS=[3500,6000,12000,20000];
  const RETRY_DELAYS=[700,1800,4000];
  const runtime=window[LOCK_KEY]||{active:false,promise:null,events:[],startedAt:'',revision:LOADER_REV};
  runtime.revision=LOADER_REV;

  function redact(value,limit=1200){return String(value??'').replace(/Bearer\s+[A-Za-z0-9._~-]+/gi,'Bearer [REDACTED]').replace(/eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/g,'[REDACTED_JWT]').slice(0,limit)}
  function record(type,data={}){let safe={};try{safe=JSON.parse(JSON.stringify(data,(_k,v)=>typeof v==='string'?redact(v):v))}catch{safe={value:redact(data)}}runtime.events.push({at:new Date().toISOString(),type,data:safe});if(runtime.events.length>100)runtime.events.shift()}
  function sleep(ms){return new Promise(resolve=>setTimeout(resolve,ms))}
  function badge(){let el=document.getElementById('tk-hk-loader-badge');if(!el){el=document.createElement('div');el.id='tk-hk-loader-badge';el.style.cssText='position:fixed;right:16px;bottom:20px;z-index:2147483647;max-width:min(360px,calc(100vw - 32px));padding:11px 14px;border-radius:13px;background:#17130d;color:#f4cf75;border:1px solid #b68a35;font:700 13px/1.3 Arial,sans-serif;box-shadow:0 8px 28px #0009;cursor:default';(document.body||document.documentElement).appendChild(el)}return el}
  function setBadge(text,state='loading'){const el=badge();el.textContent=text;el.style.borderColor=state==='ok'?'#3aa978':state==='bad'?'#bd5361':'#b68a35';el.style.color=state==='ok'?'#a7f3cf':state==='bad'?'#ffd0d5':'#f4cf75';return el}
  function report(){const payload={schema:'topking-hk-loader-diagnostic-v2',loaderRevision:LOADER_REV,expectedCoreRevision:EXPECTED_CORE_REV,startedAt:runtime.startedAt||new Date().toISOString(),exportedAt:new Date().toISOString(),page:{origin:location.origin,pathname:location.pathname},browser:{userAgent:navigator.userAgent,language:navigator.language,onLine:navigator.onLine},viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio||1},core:{version:window.__HK_MOBILE_VERSION__||'',revision:window.__HK_MOBILE_REVISION__||window.__HK_MOBILE_RUNTIME__?.revision||'',active:!!window.__HK_MOBILE_RUNTIME__?.active},events:runtime.events};const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json;charset=utf-8'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=`HK_loader_diagnostic_${new Date().toISOString().replace(/[:.]/g,'-')}.json`;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1200)}
  function coreIsCurrent(){const core=window.__HK_MOBILE_RUNTIME__;return !!(core?.active&&core.revision===EXPECTED_CORE_REV)}
  function purgeLegacyUi(){
    try{document.getElementById('hk-mobile-root')?.remove()}catch{}
    try{document.getElementById('hk-bootstrap-button')?.remove()}catch{}
    try{
      document.querySelectorAll('button').forEach(button=>{
        const label=String(button.textContent||'').trim();
        const inline=String(button.getAttribute('style')||'');
        if(/^HK(?:…|\.\.\.|!)?$/.test(label)&&inline.includes('position:fixed')&&inline.includes('width:58px')&&inline.includes('height:58px'))button.remove();
      });
    }catch{}
  }
  function resetStaleCore(reason='stale'){
    const core=window.__HK_MOBILE_RUNTIME__;
    record('core-reset',{reason,version:core?.version||'',revision:core?.revision||window.__HK_MOBILE_REVISION__||'',active:!!core?.active});
    try{core?.destroy?.()}catch{}
    try{if(core)core.active=false}catch{}
    purgeLegacyUi();
    try{delete window.__HK_MOBILE_RUNTIME__}catch{window.__HK_MOBILE_RUNTIME__=null}
    try{delete window.__HK_MOBILE_LOADED__}catch{window.__HK_MOBILE_LOADED__=false}
    try{delete window.__HK_MOBILE_VERSION__}catch{window.__HK_MOBILE_VERSION__=''}
    try{delete window.__HK_MOBILE_REVISION__}catch{window.__HK_MOBILE_REVISION__=''}
  }
  function loadOnce(timeoutMs,attempt){return new Promise((resolve,reject)=>{const script=document.createElement('script');let done=false;const finish=(error)=>{if(done)return;done=true;clearTimeout(timer);script.onload=null;script.onerror=null;script.remove();error?reject(error):resolve()};script.async=true;script.crossOrigin='anonymous';script.referrerPolicy='no-referrer';script.src=`${CORE_URL}?v=${encodeURIComponent(EXPECTED_CORE_REV)}&t=${Date.now()}&a=${attempt}`;script.onload=()=>finish();script.onerror=()=>finish(new Error('core-load-error'));const timer=setTimeout(()=>finish(new Error(`core-load-timeout-${timeoutMs}`)),timeoutMs);(document.head||document.documentElement).appendChild(script)})}

  async function start(){
    runtime.startedAt=new Date().toISOString();runtime.events=[];record('start',{loaderRevision:LOADER_REV,expectedCoreRevision:EXPECTED_CORE_REV});
    if(location.hostname!==HOST){setBadge('HK · откройте Hamster King','bad');alert('Откройте https://app.hamsterking.games и нажмите закладку HK ещё раз.');return}

    if(coreIsCurrent()){
      record('core-current',{version:window.__HK_MOBILE_RUNTIME__.version||'',revision:window.__HK_MOBILE_RUNTIME__.revision||''});
      try{window.__HK_MOBILE_RUNTIME__.open?.()}catch{}
      setBadge('HK · актуальная версия уже запущена','ok');
      setTimeout(()=>badge().remove(),1600);
      return;
    }

    if(window.__HK_MOBILE_RUNTIME__?.active||window.__HK_MOBILE_LOADED__){
      setBadge('HK · заменяю старую версию…');
      resetStaleCore('revision-mismatch');
      await sleep(80);
    }

    setBadge('HK · загружаю актуальную версию…');
    let lastError=null;
    for(let i=0;i<TIMEOUTS.length;i++){
      const timeoutMs=TIMEOUTS[i];const started=performance.now();record('load-attempt',{attempt:i+1,timeoutMs});
      try{
        await loadOnce(timeoutMs,i+1);
        await sleep(180);
        const core=window.__HK_MOBILE_RUNTIME__;
        if(!core?.active)throw new Error('core-loaded-without-active-runtime');
        if(core.revision!==EXPECTED_CORE_REV)throw new Error(`core-revision-mismatch:${core.revision||'missing'}`);
        window.__HK_LOADER_CORE_REVISION__=EXPECTED_CORE_REV;
        record('load-success',{attempt:i+1,durationMs:Math.round(performance.now()-started),version:core.version||'',revision:core.revision||''});
        try{core.ensure?.()}catch{}
        setBadge(`HK · запущен · ${core.version||''}`,'ok');
        setTimeout(()=>badge().remove(),2200);
        return;
      }catch(error){
        lastError=error;
        record('load-error',{attempt:i+1,timeoutMs,durationMs:Math.round(performance.now()-started),error:error?.message||error,version:window.__HK_MOBILE_RUNTIME__?.version||'',revision:window.__HK_MOBILE_RUNTIME__?.revision||'',online:navigator.onLine});
        if(!coreIsCurrent())resetStaleCore('load-retry');
        if(i<TIMEOUTS.length-1){setBadge(`HK · повтор загрузки ${i+2}/${TIMEOUTS.length}…`);await sleep(RETRY_DELAYS[Math.min(i,RETRY_DELAYS.length-1)])}
      }
    }
    const el=setBadge('HK · ошибка загрузки · нажмите для отчёта','bad');el.style.cursor='pointer';el.onclick=report;record('failed',{error:lastError?.message||lastError||'unknown'});
    alert(`Не удалось загрузить актуальный HK (${EXPECTED_CORE_REV}). Нажмите на сообщение HK внизу экрана, чтобы скачать диагностический отчёт.`);
  }

  if(runtime.active&&runtime.promise)return;
  runtime.active=true;window[LOCK_KEY]=runtime;
  runtime.promise=start().finally(()=>{runtime.active=false;runtime.promise=null});
})().catch?.(()=>{});