# build-trigger: 1.18.13 treasure run recorder r1
from pathlib import Path
import sys

target=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=target.read_text(encoding="utf-8")

def need(old,label,count=1):
    actual=s.count(old)
    if actual!=count:
        raise SystemExit(f"{label}: expected {count}, got {actual}")

def rep(old,new,label,count=1):
    global s
    need(old,label,count)
    s=s.replace(old,new,count)

rep(
    "// @version      1.18.12",
    "// @version      1.18.13\n"
    "// @release-note Карта Сокровищ: добавлен пассивный рекордер полного ручного прохождения. Кнопка «Запись карты» создаёт отдельную сессию, записывает клики, переходы экранов, видимые lot-id, модальные окна и уже совершённые игрой API-запросы/ответы. Рекордер ничего не нажимает и не отправляет дополнительных запросов в игру.",
    "version"
)
rep("const BUILD_VERSION = '1.18.12';","const BUILD_VERSION = '1.18.13';","build")

rep(
    "  const HK_TREASURE_GUIDE_CAPTURE_REV='treasure-guide-passive-capture-20260923-r1';",
    "  const HK_TREASURE_GUIDE_CAPTURE_REV='treasure-guide-passive-capture-20260923-r1';\n"
    "  const HK_TREASURE_RUN_RECORDER_REV='treasure-run-recorder-20260926-r1';",
    "recorder marker"
)

anchor="""  function installTreasureGuideCapture() {
"""
helpers=r'''  const TREASURE_RUN_RECORDER_ENABLED_KEY='hk:treasure-run-recorder:enabled:v1';
  const TREASURE_RUN_RECORDER_STATE_KEY='hk:treasure-run-recorder:state:v1';
  const TREASURE_RUN_RECORDER_COUNTER_KEY='hk:treasure-run-recorder:counter:v1';
  const TREASURE_RUN_RECORDER_BATCH_MAX=16;
  const TREASURE_RUN_RECORDER_FLUSH_MS=10000;
  const TREASURE_RUN_RECORDER_MAX_PENDING=96;
  let treasureRunRecorderState=null;
  let treasureRunRecorderButton=null;
  let treasureRunRecorderSnapshotTimer=null;
  let treasureRunRecorderFlushTimer=null;
  let treasureRunRecorderFlushPromise=null;
  let treasureRunRecorderLastFingerprint='';
  let treasureRunRecorderObserver=null;

  function treasureRunRecorderEnabled() {
    try{return localStorage.getItem(TREASURE_RUN_RECORDER_ENABLED_KEY)==='1';}
    catch(_){return false;}
  }

  function treasureRunRecorderReadState() {
    try{
      const raw=localStorage.getItem(TREASURE_RUN_RECORDER_STATE_KEY);
      if(!raw)return null;
      const value=JSON.parse(raw);
      if(!value||typeof value!=='object'||!value.sessionId)return null;
      value.events=Array.isArray(value.events)?value.events:[];
      value.seq=Number(value.seq||0);
      value.batch=Number(value.batch||0);
      return value;
    }catch(_){return null;}
  }

  function treasureRunRecorderPersist() {
    if(!treasureRunRecorderState)return;
    const safe={
      sessionId:treasureRunRecorderState.sessionId,
      runIndex:treasureRunRecorderState.runIndex,
      startedAt:treasureRunRecorderState.startedAt,
      startedAtMs:treasureRunRecorderState.startedAtMs,
      seq:treasureRunRecorderState.seq,
      batch:treasureRunRecorderState.batch,
      events:treasureRunRecorderState.events.slice(-TREASURE_RUN_RECORDER_MAX_PENDING)
    };
    try{localStorage.setItem(TREASURE_RUN_RECORDER_STATE_KEY,JSON.stringify(safe));}catch(_){}
  }

  function treasureRunRecorderNextIndex() {
    let value=0;
    try{value=Math.max(0,Number(localStorage.getItem(TREASURE_RUN_RECORDER_COUNTER_KEY)||0));}catch(_){}
    value+=1;
    try{localStorage.setItem(TREASURE_RUN_RECORDER_COUNTER_KEY,String(value));}catch(_){}
    return value;
  }

  function treasureRunRecorderSessionId(runIndex) {
    const rand=Math.random().toString(36).slice(2,8);
    return 'tr-'+String(runIndex)+'-'+Date.now().toString(36)+'-'+rand;
  }

  function treasureRunRecorderScreen() {
    try{
      const visibleLots=[...document.querySelectorAll('[data-lot-id]')].filter(visible);
      const ids=visibleLots.map(node=>String(node.getAttribute('data-lot-id')||''));
      if(treasureGuideScreenVisible())return 'treasure-map';
      if(ids.some(id=>/^mf_treasurelot_sword_/.test(id)) && ids.some(id=>/mf_treasurelot_enemy_type_/.test(id)))return 'battle';
      if(ids.some(id=>/mf_treasurelot_is_fishing_/.test(id)))return 'fishing';
      if(ids.some(id=>/^mf_fairlot_minigame_trader_/.test(id)))return 'trader';
      if(ids.filter(id=>/^mf_fairlot_lights_out_sl/.test(id)).length>=3)return 'lights';
      if(ids.some(id=>/mf_treasurelot_chest_(?:type|digging_spot)/.test(id)))return 'chests';
      const text=String(document.body?.innerText||'');
      if(/Лабиринт|Labyrinth/i.test(text))return 'labyrinth';
      if(/Сражение|Battle/i.test(text) && ids.some(id=>/enemy|sword/i.test(id)))return 'battle';
      if(/Необычный\s+Водоем|Необычный\s+Водоём|Fishing|Водоем|Водоём/i.test(text) && ids.some(id=>/fishing/i.test(id)))return 'fishing';
      if(/Тайный\s+Торговец|Secret\s+Trader/i.test(text))return 'trader';
      return 'other';
    }catch(_){return 'unknown';}
  }

  function treasureRunRecorderVisibleLots() {
    const rows=[];
    try{
      const nodes=[...document.querySelectorAll('[data-lot-id]')].filter(visible).slice(0,140);
      for(const node of nodes){
        const rect=node.getBoundingClientRect?.();
        rows.push({
          lotId:String(node.getAttribute('data-lot-id')||'').slice(0,220),
          text:String(node.innerText||node.textContent||'').replace(/\u00a0/g,' ').replace(/\s+/g,' ').trim().slice(0,420),
          cls:String(node.className||'').slice(0,220),
          x:rect?Math.round(rect.left+rect.width/2):null,
          y:rect?Math.round(rect.top+rect.height/2):null,
          w:rect?Math.round(rect.width):null,
          h:rect?Math.round(rect.height):null
        });
      }
    }catch(_){}
    return rows;
  }

  function treasureRunRecorderModalTexts() {
    const out=[];
    const seen=new Set();
    try{
      const nodes=[...document.querySelectorAll('[role="dialog"],[aria-modal="true"],[class*="modal"],[class*="popup"],[class*="dialog"]')].filter(visible);
      for(const node of nodes){
        const text=String(node.innerText||node.textContent||'').replace(/\u00a0/g,' ').replace(/\s+/g,' ').trim().slice(0,1800);
        if(!text||seen.has(text))continue;
        seen.add(text);out.push(text);
        if(out.length>=8)break;
      }
    }catch(_){}
    return out;
  }

  function treasureRunRecorderHeadings() {
    const out=[];
    try{
      for(const node of [...document.querySelectorAll('h1,h2,h3,.page-title,.section-title')].filter(visible)){
        const text=String(node.innerText||node.textContent||'').replace(/\s+/g,' ').trim();
        if(text&&!out.includes(text))out.push(text.slice(0,300));
        if(out.length>=8)break;
      }
    }catch(_){}
    return out;
  }

  function treasureRunRecorderSanitize(value,depth=0,seen=new WeakSet()) {
    if(value==null||typeof value==='number'||typeof value==='boolean')return value;
    if(typeof value==='string')return value.slice(0,8000);
    if(depth>7)return '[depth-limit]';
    if(typeof value!=='object')return String(value).slice(0,1000);
    if(seen.has(value))return '[circular]';
    seen.add(value);
    if(Array.isArray(value)){
      const out=[];
      for(const item of value.slice(0,120))out.push(treasureRunRecorderSanitize(item,depth+1,seen));
      return out;
    }
    const out={};
    let count=0;
    for(const key of Object.keys(value)){
      if(count>=120)break;
      if(/^(?:authorization|password|passwd|secret|access_token|refresh_token|token)$/i.test(key)){
        out[key]='[redacted]';
        continue;
      }
      out[key]=treasureRunRecorderSanitize(value[key],depth+1,seen);
      count+=1;
    }
    return out;
  }

  function treasureRunRecorderPayload(value,limit=18000) {
    let safe=value;
    try{safe=treasureRunRecorderSanitize(value);}catch(_){safe=String(value||'');}
    let text='';
    try{text=JSON.stringify(safe);}catch(_){text=String(safe||'');}
    if(text.length<=limit)return safe;
    return {truncated:true,preview:text.slice(0,limit),originalLength:text.length};
  }

  function treasureRunRecorderActive() {
    return treasureRunRecorderEnabled() && !!treasureRunRecorderState?.sessionId;
  }

  function treasureRunRecorderEvent(type,data={}) {
    if(!treasureRunRecorderActive())return null;
    const state=treasureRunRecorderState;
    const now=Date.now();
    const event={
      seq:++state.seq,
      at:new Date(now).toISOString(),
      t:Math.max(0,now-Number(state.startedAtMs||now)),
      type:String(type||'event'),
      screen:treasureRunRecorderScreen(),
      data:treasureRunRecorderPayload(data,22000)
    };
    state.events.push(event);
    if(state.events.length>TREASURE_RUN_RECORDER_MAX_PENDING)state.events=state.events.slice(-TREASURE_RUN_RECORDER_MAX_PENDING);
    treasureRunRecorderPersist();
    if(state.events.length>=TREASURE_RUN_RECORDER_BATCH_MAX)void treasureRunRecorderFlush('batch-full');
    else treasureRunRecorderScheduleFlush();
    return event;
  }

  function treasureRunRecorderScheduleFlush(delay=TREASURE_RUN_RECORDER_FLUSH_MS) {
    if(treasureRunRecorderFlushTimer)clearTimeout(treasureRunRecorderFlushTimer);
    treasureRunRecorderFlushTimer=setTimeout(()=>{
      treasureRunRecorderFlushTimer=null;
      void treasureRunRecorderFlush('timer');
    },delay);
  }

  async function treasureRunRecorderFlush(reason='manual',force=false) {
    if(treasureRunRecorderFlushPromise)return treasureRunRecorderFlushPromise;
    if(!treasureRunRecorderState?.sessionId)return false;
    if(!force&&!treasureRunRecorderActive())return false;
    if(!treasureRunRecorderState.events.length)return true;

    treasureRunRecorderFlushPromise=(async()=>{
      const state=treasureRunRecorderState;
      const batchEvents=state.events.slice(0,TREASURE_RUN_RECORDER_BATCH_MAX);
      const seqs=new Set(batchEvents.map(event=>event.seq));
      const batchNo=state.batch+1;
      const payload={
        schema:'treasure-run-trace-v1',
        revision:HK_TREASURE_RUN_RECORDER_REV,
        session_id:state.sessionId,
        run_index:state.runIndex,
        started_at:state.startedAt,
        batch:batchNo,
        flush_reason:reason,
        page:{origin:location.origin,pathname:location.pathname},
        viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio||1},
        events:batchEvents
      };
      const payloadJson=JSON.stringify(payload);
      const documentValue={
        capture_key:'trace:'+state.sessionId+':'+String(batchNo)+':'+treasureGuideHash(payloadJson),
        source:'dom',
        path:'trace/'+state.sessionId+'/'+String(batchNo),
        payload_json:payloadJson,
        page_text:'',
        assets:[]
      };
      try{
        await licensedServerJson(
          CLAN_SHOP_FACT_API_BASE,
          '/treasure-guide/capture',
          documentValue,
          true,
          'treasure-run-recorder'
        );
        state.events=state.events.filter(event=>!seqs.has(event.seq));
        state.batch=batchNo;
        treasureRunRecorderPersist();
        recordDiagnostic('treasure-run-recorder-flush',{
          revision:HK_TREASURE_RUN_RECORDER_REV,
          sessionId:state.sessionId,
          batch:batchNo,
          events:batchEvents.length,
          reason
        });
        if(state.events.length)treasureRunRecorderScheduleFlush(1200);
        return true;
      }catch(error){
        recordDiagnostic('treasure-run-recorder-flush-error',{
          revision:HK_TREASURE_RUN_RECORDER_REV,
          sessionId:state.sessionId,
          batch:batchNo,
          reason,
          error:String(error?.message||error||'unknown')
        });
        treasureRunRecorderScheduleFlush(5000);
        return false;
      }
    })().finally(()=>{treasureRunRecorderFlushPromise=null;});
    return treasureRunRecorderFlushPromise;
  }

  function treasureRunRecorderSnapshot(reason='dom') {
    if(!treasureRunRecorderActive())return;
    const pageText=String(document.body?.innerText||'').replace(/\u00a0/g,' ').replace(/\s+/g,' ').trim().slice(0,6500);
    const data={
      reason,
      screen:treasureRunRecorderScreen(),
      headings:treasureRunRecorderHeadings(),
      modals:treasureRunRecorderModalTexts(),
      lots:treasureRunRecorderVisibleLots(),
      pageText
    };
    const fingerprint=treasureGuideHash(JSON.stringify(data));
    if(fingerprint===treasureRunRecorderLastFingerprint)return;
    treasureRunRecorderLastFingerprint=fingerprint;
    treasureRunRecorderEvent('snapshot',data);
    treasureRunRecorderUpdateButton();
  }

  function treasureRunRecorderScheduleSnapshot(reason='mutation',delay=350) {
    if(!treasureRunRecorderActive())return;
    if(treasureRunRecorderSnapshotTimer)clearTimeout(treasureRunRecorderSnapshotTimer);
    treasureRunRecorderSnapshotTimer=setTimeout(()=>{
      treasureRunRecorderSnapshotTimer=null;
      treasureRunRecorderSnapshot(reason);
    },delay);
  }

  function treasureRunRecorderTargetInfo(target) {
    if(!target)return {};
    const element=target instanceof Element?target:target.parentElement;
    if(!element)return {};
    const actionable=element.closest?.('[data-lot-id],button,[role="button"],a') || element;
    const lotNode=element.closest?.('[data-lot-id]');
    const rect=actionable.getBoundingClientRect?.();
    return {
      lotId:String(lotNode?.getAttribute?.('data-lot-id')||'').slice(0,220),
      tag:String(actionable.tagName||'').toLowerCase(),
      id:String(actionable.id||'').slice(0,120),
      cls:String(actionable.className||'').slice(0,260),
      text:String(actionable.innerText||actionable.textContent||'').replace(/\u00a0/g,' ').replace(/\s+/g,' ').trim().slice(0,900),
      x:rect?Math.round(rect.left+rect.width/2):null,
      y:rect?Math.round(rect.top+rect.height/2):null,
      w:rect?Math.round(rect.width):null,
      h:rect?Math.round(rect.height):null
    };
  }

  function treasureRunRecorderObserveClick(event) {
    if(!treasureRunRecorderActive())return;
    const element=event.target instanceof Element?event.target:null;
    if(element?.closest?.('#hkTreasureRunRecorderToggle'))return;
    treasureRunRecorderEvent('click',{
      pointerType:String(event.pointerType||''),
      clientX:Number.isFinite(event.clientX)?Math.round(event.clientX):null,
      clientY:Number.isFinite(event.clientY)?Math.round(event.clientY):null,
      target:treasureRunRecorderTargetInfo(event.target)
    });
    treasureRunRecorderScheduleSnapshot('after-click',250);
    setTimeout(()=>treasureRunRecorderScheduleSnapshot('after-click-settle',120),900);
  }

  function treasureRunRecorderParseBody(value) {
    if(value==null)return null;
    if(typeof value==='string'){
      const text=value.slice(0,22000);
      try{return treasureRunRecorderPayload(JSON.parse(text),16000);}catch(_){return text;}
    }
    if(typeof URLSearchParams!=='undefined' && value instanceof URLSearchParams)return value.toString().slice(0,16000);
    if(typeof FormData!=='undefined' && value instanceof FormData){
      const out={};
      try{
        for(const [key,item] of value.entries()){
          if(typeof item==='string')out[key]=item.slice(0,3000);
          else out[key]='[binary]';
        }
      }catch(_){}
      return treasureRunRecorderPayload(out,16000);
    }
    return treasureRunRecorderPayload(value,16000);
  }

  function treasureRunRecorderNetworkImportant(path,method,status) {
    if(Number(status)>=400)return true;
    if(String(method||'GET').toUpperCase()!=='GET')return true;
    return /fair|treasure|shop|event|minigame|mission|quest|adventure/i.test(String(path||''));
  }

  function treasureRunRecorderObserveNetwork(url,method,status,requestBody,responseBody) {
    if(!treasureRunRecorderActive())return;
    let path='';
    try{path=new URL(String(url||''),location.href).pathname;}catch(_){return;}
    if(!path||path.startsWith('/auth/'))return;
    const statusNumber=Number(status||0);
    const methodValue=String(method||'GET').toUpperCase();
    const important=treasureRunRecorderNetworkImportant(path,methodValue,statusNumber);
    treasureRunRecorderEvent('network',{
      path,
      method:methodValue,
      status:statusNumber,
      request:important?treasureRunRecorderParseBody(requestBody):null,
      response:important?treasureRunRecorderPayload(responseBody,18000):null
    });
    treasureRunRecorderScheduleSnapshot('after-network',400);
  }

  function treasureRunRecorderUpdateButton() {
    if(!treasureRunRecorderButton)return;
    const active=treasureRunRecorderActive();
    const show=active || treasureGuideScreenVisible();
    treasureRunRecorderButton.style.display=show?'block':'none';
    treasureRunRecorderButton.textContent=active
      ? 'Запись карты: ВКЛ #'+String(treasureRunRecorderState?.runIndex||'')
      : 'Запись карты: ВЫКЛ';
    treasureRunRecorderButton.style.background=active?'#d13b3b':'#292929';
    treasureRunRecorderButton.style.color='#fff';
    treasureRunRecorderButton.style.borderColor=active?'#ffd5d5':'rgba(255,255,255,.8)';
  }

  function treasureRunRecorderStart() {
    if(treasureRunRecorderActive())return treasureRunRecorderState;
    const previous=treasureRunRecorderReadState();
    let state=null;
    if(treasureRunRecorderEnabled() && previous?.sessionId && Date.now()-Number(previous.startedAtMs||0)<8*60*60*1000){
      state=previous;
    }
    if(!state){
      const runIndex=treasureRunRecorderNextIndex();
      const now=Date.now();
      state={
        sessionId:treasureRunRecorderSessionId(runIndex),
        runIndex,
        startedAt:new Date(now).toISOString(),
        startedAtMs:now,
        seq:0,
        batch:0,
        events:[]
      };
    }
    treasureRunRecorderState=state;
    try{localStorage.setItem(TREASURE_RUN_RECORDER_ENABLED_KEY,'1');}catch(_){}
    treasureRunRecorderPersist();
    treasureRunRecorderLastFingerprint='';
    treasureRunRecorderEvent(state.seq?'session-resume':'session-start',{
      revision:HK_TREASURE_RUN_RECORDER_REV,
      version:BUILD_VERSION,
      pathname:location.pathname,
      userAgent:navigator.userAgent,
      language:navigator.language
    });
    treasureRunRecorderSnapshot('session-start');
    treasureRunRecorderUpdateButton();
    return state;
  }

  async function treasureRunRecorderStop() {
    if(!treasureRunRecorderState?.sessionId){
      try{localStorage.setItem(TREASURE_RUN_RECORDER_ENABLED_KEY,'0');}catch(_){}
      treasureRunRecorderUpdateButton();
      return;
    }
    if(treasureRunRecorderActive()){
      treasureRunRecorderSnapshot('session-stop');
      treasureRunRecorderEvent('session-stop',{
        revision:HK_TREASURE_RUN_RECORDER_REV,
        durationMs:Math.max(0,Date.now()-Number(treasureRunRecorderState.startedAtMs||Date.now()))
      });
    }
    try{localStorage.setItem(TREASURE_RUN_RECORDER_ENABLED_KEY,'0');}catch(_){}
    treasureRunRecorderUpdateButton();
    for(let i=0;i<4 && treasureRunRecorderState.events.length;i++){
      const ok=await treasureRunRecorderFlush('session-stop',true);
      if(!ok)break;
    }
    treasureRunRecorderPersist();
  }

  function treasureRunRecorderToggle() {
    if(treasureRunRecorderActive())void treasureRunRecorderStop();
    else treasureRunRecorderStart();
  }

  function installTreasureRunRecorder() {
    if(window.__HK_TREASURE_RUN_RECORDER_INSTALLED__)return;
    window.__HK_TREASURE_RUN_RECORDER_INSTALLED__=true;
    const restored=treasureRunRecorderReadState();
    if(treasureRunRecorderEnabled() && restored?.sessionId && Date.now()-Number(restored.startedAtMs||0)<8*60*60*1000){
      treasureRunRecorderState=restored;
    }else{
      try{localStorage.setItem(TREASURE_RUN_RECORDER_ENABLED_KEY,'0');}catch(_){}
      treasureRunRecorderState=restored;
    }

    const start=()=>{
      if(!document.body){setTimeout(start,300);return;}
      if(!treasureRunRecorderButton){
        treasureRunRecorderButton=document.createElement('button');
        treasureRunRecorderButton.id='hkTreasureRunRecorderToggle';
        treasureRunRecorderButton.type='button';
        Object.assign(treasureRunRecorderButton.style,{
          position:'fixed',
          left:'12px',
          bottom:'154px',
          zIndex:'2147483646',
          border:'2px solid rgba(255,255,255,.8)',
          borderRadius:'18px',
          padding:'8px 11px',
          fontSize:'12px',
          fontWeight:'900',
          lineHeight:'1',
          boxShadow:'0 4px 14px rgba(0,0,0,.55)',
          WebkitTapHighlightColor:'transparent',
          touchAction:'manipulation'
        });
        treasureRunRecorderButton.addEventListener('click',event=>{
          event.preventDefault();
          event.stopPropagation();
          treasureRunRecorderToggle();
        },true);
        document.body.appendChild(treasureRunRecorderButton);
      }

      document.addEventListener('click',treasureRunRecorderObserveClick,true);
      if(!treasureRunRecorderObserver){
        treasureRunRecorderObserver=new MutationObserver(()=>{
          treasureRunRecorderUpdateButton();
          treasureRunRecorderScheduleSnapshot('mutation',450);
        });
        treasureRunRecorderObserver.observe(document.body,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['class','style','data-lot-id']});
      }
      document.addEventListener('visibilitychange',()=>{
        if(document.visibilityState==='hidden')void treasureRunRecorderFlush('visibility-hidden',true);
        else if(treasureRunRecorderActive())treasureRunRecorderScheduleSnapshot('visibility-visible',250);
      });
      window.addEventListener('pagehide',()=>{
        treasureRunRecorderPersist();
        void treasureRunRecorderFlush('pagehide',true);
      });
      setInterval(()=>{
        treasureRunRecorderUpdateButton();
        if(treasureRunRecorderActive())treasureRunRecorderScheduleSnapshot('heartbeat',250);
      },4000);

      if(treasureRunRecorderState?.sessionId && treasureRunRecorderEnabled()){
        treasureRunRecorderStart();
      }else{
        treasureRunRecorderUpdateButton();
      }
    };
    start();

    window.__HK_TREASURE_RUN_RECORDER__={
      revision:HK_TREASURE_RUN_RECORDER_REV,
      start:treasureRunRecorderStart,
      stop:treasureRunRecorderStop,
      flush:()=>treasureRunRecorderFlush('api',true),
      snapshot:()=>treasureRunRecorderSnapshot('api'),
      get active(){return treasureRunRecorderActive();},
      get sessionId(){return treasureRunRecorderState?.sessionId||'';},
      get runIndex(){return treasureRunRecorderState?.runIndex||0;},
      get pending(){return treasureRunRecorderState?.events?.length||0;}
    };
  }

'''
need(anchor,"install treasure guide anchor")
s=s.replace(anchor,helpers+anchor,1)

# Install recorder together with existing passive capture.
rep(
    """      const observer=new MutationObserver(()=>scheduleTreasureGuideDomScan(1000));
      observer.observe(document.body,{childList:true,subtree:true,characterData:true});
      scheduleTreasureGuideDomScan(1200);
""",
    """      const observer=new MutationObserver(()=>scheduleTreasureGuideDomScan(1000));
      observer.observe(document.body,{childList:true,subtree:true,characterData:true});
      installTreasureRunRecorder();
      scheduleTreasureGuideDomScan(1200);
""",
    "install recorder"
)

# Fetch observer: capture the game's already-completed request/response; no extra game request.
old_fetch="""      const response = await nativeFetch(input, init);
      const path = url ? new URL(url, location.href).pathname : '';
"""
new_fetch="""      const response = await nativeFetch(input, init);
      const path = url ? new URL(url, location.href).pathname : '';
      if(treasureRunRecorderActive() && isGameApiRequest(url) && !path.startsWith('/auth/')){
        const method=String(init?.method || input?.method || 'GET').toUpperCase();
        const requestBody=init?.body ?? null;
        const clone=response.clone();
        clone.text().then(text=>{
          let body=text;
          try{body=JSON.parse(text);}catch(_){}
          treasureRunRecorderObserveNetwork(url,method,response.status,requestBody,body);
        }).catch(()=>treasureRunRecorderObserveNetwork(url,method,response.status,requestBody,null));
      }
"""
rep(old_fetch,new_fetch,"fetch recorder observer")

# XHR observer: record any status, including 409/500, then existing success handlers continue unchanged.
old_xhr="""        this.addEventListener('load', () => {
          try {
            const hkPath=new URL(this.__hkUrl,location.href).pathname;
"""
new_xhr="""        this.addEventListener('load', () => {
          try {
            const hkPath=new URL(this.__hkUrl,location.href).pathname;
            if(treasureRunRecorderActive() && !hkPath.startsWith('/auth/')){
              let recorderBody=this.responseText;
              try{recorderBody=JSON.parse(this.responseText);}catch(_){}
              treasureRunRecorderObserveNetwork(this.__hkUrl,this.__hkMethod||'GET',this.status,args[0]??null,recorderBody);
            }
"""
rep(old_xhr,new_xhr,"xhr recorder observer")

for marker in [
    "// @version      1.18.13",
    "const BUILD_VERSION = '1.18.13';",
    "treasure-run-recorder-20260926-r1",
    "treasure-run-trace-v1",
    "Запись карты: ВКЛ",
    "Запись карты: ВЫКЛ",
    "session-start",
    "session-stop",
    "treasureRunRecorderObserveClick",
    "treasureRunRecorderObserveNetwork",
    "trace/'+state.sessionId",
    "installTreasureRunRecorder();",
    "treasure-guide-passive-capture-20260923-r1",
    "battle-visible-board-active-20260926-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

target.write_text(s,encoding="utf-8")
print("TREASURE_RUN_RECORDER_1_18_13=PASS")
