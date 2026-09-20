(() => {
'use strict';

const GATEWAY_URL='https://kokkaras.com/hk_maps/panel_secure.php';
const GAME_API_URL='https://hk-game-api.hwgame.cloud';
const LOAD_KEY='__HK_SECURE_PANEL_LOADING__';
const LOADER_VERSION='4.9.0';
const AUTH_REFRESH_EARLY_SECONDS=60;
const diagnostic={startedAt:new Date().toISOString(),events:[]};
let authCreatePromise=null;

function decodeJwt(token){
  try{
    const part=String(token||'').split('.')[1].replace(/-/g,'+').replace(/_/g,'/');
    return JSON.parse(atob(part.padEnd(Math.ceil(part.length/4)*4,'=')));
  }catch{return null}
}

function tokenFingerprint(token){
  let hash=2166136261;
  const value=String(token||'');
  for(let i=0;i<value.length;i++){
    hash^=value.charCodeAt(i);
    hash=Math.imul(hash,16777619);
  }
  return `fnv1a-${(hash>>>0).toString(16).padStart(8,'0')}`;
}

function redact(value,limit=2400){
  return String(value??'')
    .replace(/Bearer\s+[A-Za-z0-9._~-]+/gi,'Bearer [REDACTED]')
    .replace(/eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/g,'[REDACTED_JWT]')
    .slice(0,limit);
}

function tokenSummary(token,sources=[]){
  const payload=decodeJwt(token)||{};
  const now=Math.floor(Date.now()/1000);
  const exp=Number(payload.exp||0)||null;
  const safe=value=>value===undefined||value===null?'':String(value).slice(0,160);
  return {
    fingerprint:tokenFingerprint(token),length:String(token||'').length,segments:String(token||'').split('.').length,
    sources:[...new Set(sources)].slice(0,30),
    claims:{exp,iat:Number(payload.iat||0)||null,nbf:Number(payload.nbf||0)||null,secondsUntilExpiry:exp===null?null:exp-now,auth_type:safe(payload.auth_type),platform:safe(payload.platform),region:safe(payload.region),sub:safe(payload.sub),player_id:safe(payload.id||payload.player_id||payload.playerId||payload.user_id)}
  };
}

function record(type,data={}){
  diagnostic.events.push({at:new Date().toISOString(),type,data:JSON.parse(JSON.stringify(data,(key,value)=>typeof value==='string'?redact(value):value))});
  if(diagnostic.events.length>200)diagnostic.events.shift();
}

function sessionBearerToken(){
  try{return String(sessionStorage.getItem('token')||'').trim()}catch{return ''}
}

function saveSessionBearer(token){
  const value=String(token||'').trim();
  if(!value)return '';
  try{sessionStorage.setItem('token',value)}catch{}
  return value;
}

function bearerNeedsRefresh(token){
  const exp=Number(decodeJwt(String(token||''))?.exp||0);
  if(!exp)return true;
  return exp*1000-Date.now()<=AUTH_REFRESH_EARLY_SECONDS*1000;
}

function bearerPlayerId(token){
  const payload=decodeJwt(String(token||''))||{};
  return String(payload.id||payload.player_id||payload.playerId||payload.user_id||'').trim();
}

function bearerIdentityMatches(expectedToken,newToken){
  const expectedId=bearerPlayerId(expectedToken);
  if(!expectedId)return true;
  return bearerPlayerId(newToken)===expectedId;
}

function readNativeAuthCreateParams(){
  try{
    const webApp=window.Telegram?.WebApp;
    const initData=String(webApp?.initData||'');
    if(webApp && webApp.platform && webApp.platform!=='unknown' && initData){
      return {authType:'MiniApp',authData:initData.replaceAll('&','%26'),platform:'TG',source:'telegram-mini-app'};
    }
  }catch{}

  try{
    const stored=JSON.parse(localStorage.getItem('auth-data')||'null');
    const authType=String(stored?.params?.auth_type||'').trim();
    const authData=String(stored?.params?.auth_data||'').trim();
    const remembered=String(localStorage.getItem('remember-me')||'').trim();
    if(!authType || !authData || remembered!==authType)return null;
    return {authType,authData,platform:'WEB',source:'localStorage:auth-data'};
  }catch{
    return null;
  }
}

async function checkBearer(token){
  const response=await fetch(GAME_API_URL+'/auth/check',{
    method:'POST',
    cache:'no-store',
    headers:{'Authorization':'Bearer '+token,'Accept':'application/json, text/plain, */*'}
  });
  record('auth-check-response',{status:response.status,ok:response.ok,candidate:tokenSummary(token,['sessionStorage:token'])});
  if(response.ok)return true;
  if(response.status===401 || response.status===403 || response.status===500)return false;
  throw new Error(`Auth check failed: HTTP ${response.status}`);
}

async function createFreshBearer(reason='loader-auth-create',expectedToken=''){
  if(authCreatePromise)return authCreatePromise;

  authCreatePromise=(async()=>{
    const params=readNativeAuthCreateParams();
    if(!params){
      record('auth-create-unavailable',{reason});
      return '';
    }

    if(String(params.authType||'')==='Google'){
      const googlePayload=decodeJwt(String(params.authData||''))||{};
      const googleExp=Number(googlePayload?.exp||0);
      const googleNeedsRefresh=!googleExp || googleExp*1000-Date.now()<=AUTH_REFRESH_EARLY_SECONDS*1000;
      if(googleNeedsRefresh){
        const previousAuthData=String(params.authData||'');
        const googlePrompt=window.google?.accounts?.id?.prompt;
        if(typeof googlePrompt==='function'){
          try{googlePrompt.call(window.google.accounts.id)}catch{}
          const deadline=Date.now()+8000;
          while(Date.now()<deadline){
            await new Promise(resolve=>setTimeout(resolve,200));
            const refreshed=readNativeAuthCreateParams();
            if(String(refreshed?.authType||'')!=='Google')continue;
            const refreshedData=String(refreshed?.authData||'');
            const refreshedExp=Number(decodeJwt(refreshedData)?.exp||0);
            if(refreshedData&&refreshedData!==previousAuthData&&refreshedExp*1000>Date.now()){
              params=refreshed;
              break;
            }
          }
        }
        const latest=readNativeAuthCreateParams();
        const latestData=String(latest?.authData||'');
        const latestExp=Number(decodeJwt(latestData)?.exp||0);
        if(String(latest?.authType||'')==='Google'&&latestData&&latestExp*1000>Date.now())params=latest;
        else{
          record('google-auth-refresh-unavailable',{reason});
          return '';
        }
      }
    }

    const url=new URL(GAME_API_URL+'/auth/create');
    url.searchParams.set('auth_type',params.authType);
    url.searchParams.set('auth_data',params.authData);
    url.searchParams.set('platform',params.platform);

    record('auth-create-start',{reason,authType:params.authType,platform:params.platform,source:params.source});
    const response=await fetch(url,{method:'POST',cache:'no-store',headers:{'Accept':'application/json, text/plain, */*'}});
    const data=await response.json().catch(()=>null);
    const token=String(data?.token||'').trim();
    record('auth-create-response',{reason,status:response.status,ok:response.ok,hasToken:!!token});
    if(!response.ok || !token)return '';
    if(expectedToken && !bearerIdentityMatches(expectedToken,token)){
      record('auth-create-identity-mismatch',{reason,expectedPlayerId:bearerPlayerId(expectedToken),receivedPlayerId:bearerPlayerId(token)});
      return '';
    }
    saveSessionBearer(token);
    record('auth-create-success',{reason,candidate:tokenSummary(token,['sessionStorage:token'])});
    return token;
  })();

  try{
    return await authCreatePromise;
  }finally{
    authCreatePromise=null;
  }
}

async function resolveInitialBearer(){
  let token=sessionBearerToken();
  if(token && !bearerNeedsRefresh(token)){
    const valid=await checkBearer(token);
    if(valid)return token;
  }

  token=await createFreshBearer(token?'initial-near-expiry-or-invalid':'initial-missing-token',token);
  return token;
}

function storageSnapshot(){
  const result={};
  for(const [name,storage] of [['sessionStorage',sessionStorage],['localStorage',localStorage]]){
    try{
      const items=[];
      for(let i=0;i<storage.length;i++){
        const key=String(storage.key(i)||'');
        const value=String(storage.getItem(key)||'');
        items.push({key,length:value.length,jwtCount:(value.match(/eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/g)||[]).length});
      }
      result[name]={accessible:true,count:items.length,items:items.slice(0,200)};
    }catch(error){result[name]={accessible:false,error:redact(error?.message||error)}}
  }
  return result;
}

function environmentSnapshot(){
  const connection=navigator.connection||navigator.mozConnection||navigator.webkitConnection||null;
  return {
    page:{origin:location.origin,pathname:location.pathname,protocol:location.protocol,hostname:location.hostname},
    browser:{userAgent:navigator.userAgent,language:navigator.language,languages:[...(navigator.languages||[])],platform:navigator.platform,cookieEnabled:navigator.cookieEnabled,onLine:navigator.onLine},
    viewport:{width:innerWidth,height:innerHeight,devicePixelRatio:devicePixelRatio||1},
    document:{visibilityState:document.visibilityState,readyState:document.readyState},
    timezone:Intl.DateTimeFormat().resolvedOptions().timeZone||'',
    connection:connection?{effectiveType:connection.effectiveType||'',downlink:connection.downlink??null,rtt:connection.rtt??null,saveData:!!connection.saveData}:null,
    serviceWorkerControlled:!!navigator.serviceWorker?.controller
  };
}

const REQUEST_RETRY_DELAYS_MS=[5000,15000,30000];
const SCRIPT_LOAD_TIMEOUTS_MS=[3000,3000,5000,5000,10000,10000,20000];

async function loaderFetchWithRetry(url,options={}){
  let lastError=null;
  for(let attempt=0;attempt<=REQUEST_RETRY_DELAYS_MS.length;attempt++){
    try{
      const response=await fetch(url,options);
      const status=Number(response.status||0);
      if(!(status===408 || status===425 || status===429 || status>=500))return response;
      lastError=new Error(`HTTP ${status}`);
      if(attempt>=REQUEST_RETRY_DELAYS_MS.length){
        record('gateway-retry-exhausted',{status,attempts:attempt+1});
        throw lastError;
      }
      const delayMs=REQUEST_RETRY_DELAYS_MS[attempt];
      record('gateway-retry',{status,delayMs,attempt:attempt+2,totalAttempts:REQUEST_RETRY_DELAYS_MS.length+1});
      await new Promise(resolve=>setTimeout(resolve,delayMs));
    }catch(error){
      if(attempt>=REQUEST_RETRY_DELAYS_MS.length){
        record('gateway-retry-exhausted',{error:String(error?.message||error),attempts:attempt+1});
        throw error;
      }
      lastError=error;
      const delayMs=REQUEST_RETRY_DELAYS_MS[attempt];
      record('gateway-retry',{error:String(error?.message||error),delayMs,attempt:attempt+2,totalAttempts:REQUEST_RETRY_DELAYS_MS.length+1});
      await new Promise(resolve=>setTimeout(resolve,delayMs));
    }
  }
  throw lastError||new Error('Request failed after retries');
}

async function requestScriptUrl(token,source='resolved-auth'){
  const summary=tokenSummary(token,[source]);
  const started=performance.now();
  record('gateway-request-start',{candidate:summary});
  try{
    const response=await loaderFetchWithRetry(GATEWAY_URL,{
      method:'POST',mode:'cors',credentials:'omit',cache:'no-store',
      headers:{'Authorization':'Bearer '+token,'Accept':'application/json','Content-Type':'application/json'},
      body:'{}'
    });
    let raw='';
    try{raw=await response.clone().text()}catch{}
    record('gateway-response',{fingerprint:summary.fingerprint,status:response.status,statusText:response.statusText,ok:response.ok,contentType:response.headers.get('content-type')||'',durationMs:Math.round(performance.now()-started),body:response.ok?'':redact(raw)});
    if(!response.ok)return {url:'',status:response.status};
    const payload=await response.json().catch(error=>{record('gateway-json-error',{fingerprint:summary.fingerprint,error:String(error?.message||error)});return null});
    if(!payload || payload.ok!==true || typeof payload.script_url!=='string'){
      record('gateway-invalid-payload',{fingerprint:summary.fingerprint,hasPayload:!!payload,okValue:payload?.ok??null,hasScriptUrl:typeof payload?.script_url==='string'});
      return {url:'',status:response.status};
    }
    const scriptUrl=new URL(payload.script_url,GATEWAY_URL);
    const gateway=new URL(GATEWAY_URL);
    if(scriptUrl.origin!==gateway.origin || scriptUrl.pathname!==gateway.pathname){
      record('gateway-invalid-script-url',{fingerprint:summary.fingerprint,origin:scriptUrl.origin,pathname:scriptUrl.pathname});
      return {url:'',status:response.status};
    }
    return {url:scriptUrl.href,status:response.status};
  }catch(error){
    record('gateway-network-error',{fingerprint:summary.fingerprint,name:String(error?.name||''),error:String(error?.message||error),durationMs:Math.round(performance.now()-started)});
    return {url:'',status:0};
  }
}

function loadScript(url,timeoutMs){
  return new Promise((resolve,reject)=>{
    const script=document.createElement('script');
    let settled=false;
    let timer=0;
    const finish=(error=null)=>{
      if(settled)return;
      settled=true;
      if(timer)clearTimeout(timer);
      script.onload=null;
      script.onerror=null;
      script.remove();
      if(error)reject(error);
      else resolve();
    };
    script.src=url;
    script.async=true;
    script.referrerPolicy='no-referrer';
    script.onload=()=>finish();
    script.onerror=()=>{
      const error=new Error('Secure panel script could not be loaded.');
      error.code='load-error';
      finish(error);
    };
    timer=setTimeout(()=>{
      const error=new Error(`Secure panel script timed out after ${timeoutMs} ms.`);
      error.code='timeout';
      finish(error);
    },timeoutMs);
    (document.head||document.documentElement).appendChild(script);
  });
}

function knownTokens(){
  const token=sessionBearerToken();
  return token?[tokenSummary(token,['sessionStorage:token'])]:[];
}

function reportPayload(){
  return {
    schema:'hk-bearer-loader-diagnostic-v2',loaderVersion:LOADER_VERSION,startedAt:diagnostic.startedAt,exportedAt:new Date().toISOString(),
    environment:environmentSnapshot(),storage:storageSnapshot(),knownTokens:knownTokens(),events:diagnostic.events
  };
}

function downloadReport(){
  const blob=new Blob([JSON.stringify(reportPayload(),null,2)],{type:'application/json;charset=utf-8'});
  const url=URL.createObjectURL(blob);
  const anchor=document.createElement('a');
  anchor.href=url;
  anchor.download=`hk_bearer_token_loader_report_${new Date().toISOString().replace(/[:.]/g,'-')}.json`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(()=>URL.revokeObjectURL(url),1500);
}

function showFailureReporter(){
  const russian=(navigator.language||'').toLowerCase().startsWith('ru');
  const old=document.getElementById('__hk_bearer_report_button');
  if(old)old.remove();
  const button=document.createElement('button');
  button.id='__hk_bearer_report_button';
  button.type='button';
  button.textContent='🧾';
  button.title=russian?'Скачать диагностический отчёт Bearer Token':'Download Bearer Token diagnostic report';
  button.setAttribute('aria-label',button.title);
  Object.assign(button.style,{position:'fixed',right:'18px',top:'18px',zIndex:'2147483647',width:'46px',height:'46px',borderRadius:'14px',border:'1px solid rgba(255,100,116,.75)',background:'rgba(35,12,17,.94)',color:'#fff',fontSize:'23px',cursor:'pointer',boxShadow:'0 8px 28px rgba(0,0,0,.42)'});
  button.onclick=downloadReport;
  (document.body||document.documentElement).appendChild(button);
  alert(russian
    ? 'Не удалось проверить сессию Hamster King. Нажмите значок отчёта и отправьте скачанный JSON для проверки.'
    : 'The Hamster King session could not be verified. Tap the report icon and send the downloaded JSON for inspection.');
}

async function start(){
  const existing=document.getElementById('__hk_control_panel_host');
  if(existing)existing.remove();
  const oldReport=document.getElementById('__hk_bearer_report_button');
  if(oldReport)oldReport.remove();

  let token='';
  try{
    token=await resolveInitialBearer();
  }catch(error){
    record('initial-auth-error',{name:String(error?.name||''),error:String(error?.message||error)});
  }
  if(!token){
    showFailureReporter();
    return;
  }

  let gateway=await requestScriptUrl(token);
  if(!gateway.url && gateway.status===401){
    const renewed=await createFreshBearer('gateway-401',token).catch(error=>{record('gateway-auth-create-error',{error:String(error?.message||error)});return ''});
    if(renewed && renewed!==token){
      token=renewed;
      gateway=await requestScriptUrl(token,'auth-create:gateway-401');
    }
  }

  if(!gateway.url){
    showFailureReporter();
    return;
  }

  let scriptLoaded=false;
  let lastScriptError=null;
  const scriptLoadStarted=performance.now();

  for(let attempt=0;attempt<SCRIPT_LOAD_TIMEOUTS_MS.length;attempt++){
    const attemptNumber=attempt+1;
    const timeoutMs=SCRIPT_LOAD_TIMEOUTS_MS[attempt];

    if(attempt>0){
      record('panel-script-ticket-refresh-start',{attempt:attemptNumber,totalAttempts:SCRIPT_LOAD_TIMEOUTS_MS.length,fingerprint:tokenFingerprint(token)});
      gateway=await requestScriptUrl(token,`panel-script-retry:${attemptNumber}`);
      record('panel-script-ticket-refresh-result',{attempt:attemptNumber,totalAttempts:SCRIPT_LOAD_TIMEOUTS_MS.length,fingerprint:tokenFingerprint(token),status:gateway.status,granted:!!gateway.url});
      if(document.getElementById('__hk_control_panel_host')){
        record('panel-script-loaded-late',{attempt:attemptNumber-1,totalAttempts:SCRIPT_LOAD_TIMEOUTS_MS.length,fingerprint:tokenFingerprint(token)});
        scriptLoaded=true;
        break;
      }
      if(!gateway.url){
        lastScriptError=new Error(`Fresh script ticket could not be obtained (HTTP ${gateway.status||0}).`);
        lastScriptError.code='ticket-error';
        continue;
      }
    }

    const attemptStarted=performance.now();
    record('panel-script-load-attempt',{attempt:attemptNumber,totalAttempts:SCRIPT_LOAD_TIMEOUTS_MS.length,timeoutMs,fingerprint:tokenFingerprint(token)});
    try{
      await loadScript(gateway.url,timeoutMs);
      record('panel-script-loaded',{attempt:attemptNumber,totalAttempts:SCRIPT_LOAD_TIMEOUTS_MS.length,timeoutMs,durationMs:Math.round(performance.now()-attemptStarted),totalDurationMs:Math.round(performance.now()-scriptLoadStarted),fingerprint:tokenFingerprint(token)});
      scriptLoaded=true;
      break;
    }catch(error){
      lastScriptError=error;
      record('panel-script-load-attempt-error',{attempt:attemptNumber,totalAttempts:SCRIPT_LOAD_TIMEOUTS_MS.length,timeoutMs,durationMs:Math.round(performance.now()-attemptStarted),reason:String(error?.code||'load-error'),name:String(error?.name||''),error:String(error?.message||error),online:navigator.onLine,visibilityState:document.visibilityState});
      if(document.getElementById('__hk_control_panel_host')){
        record('panel-script-loaded-late',{attempt:attemptNumber,totalAttempts:SCRIPT_LOAD_TIMEOUTS_MS.length,fingerprint:tokenFingerprint(token)});
        scriptLoaded=true;
        break;
      }
    }
  }

  if(!scriptLoaded){
    record('panel-script-load-error',{fingerprint:tokenFingerprint(token),attempts:SCRIPT_LOAD_TIMEOUTS_MS.length,totalDurationMs:Math.round(performance.now()-scriptLoadStarted),reason:String(lastScriptError?.code||'load-error'),error:String(lastScriptError?.message||lastScriptError||'Secure panel script could not be loaded.')});
    showFailureReporter();
  }
}

if(window[LOAD_KEY])return;
window[LOAD_KEY]=start().finally(()=>{delete window[LOAD_KEY]});
})();
