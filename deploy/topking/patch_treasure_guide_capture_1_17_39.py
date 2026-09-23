from pathlib import Path

PATH=Path("/tmp/HamsterKingMobile.user.js")
s=PATH.read_text(encoding="utf-8")
MARKER="treasure-guide-passive-capture-20260923-r1"

if MARKER in s:
    print("TREASURE_GUIDE_PASSIVE_CAPTURE_ALREADY_PRESENT")
    raise SystemExit(0)

for required in [
    "// @version      1.17.38",
    "const BUILD_VERSION = '1.17.38';",
    "function installNetworkCapture()",
    "async function licensedServerJson(",
    "clan-shop-dom-history-capture-20260922-r3",
    "maps-manual-scan-only-20260923-r1",
]:
    if required not in s:
        raise SystemExit("missing marker: "+required)

s=s.replace("// @version      1.17.38","// @version      1.17.39",1)
s=s.replace("const BUILD_VERSION = '1.17.38';","const BUILD_VERSION = '1.17.39';",1)
first_release="// @release-note Карты: исследование районов больше не запускается автоматически при открытии вкладки или по 24-часовому таймеру; полный проход запускается только явной кнопкой «Считать карты аккаунта»."
s=s.replace(first_release,
"// @release-note Добавлен пассивный сбор нового события «Карта Сокровищ»: скрипт сохраняет только уже загруженные игрой API-ответы, текст экрана и ссылки на ассеты для построения гайда; дополнительных запросов к игре не делает.\n"+first_release,1)

anchor="  function installNetworkCapture() {\n"
helpers=r'''  const HK_TREASURE_GUIDE_CAPTURE_REV='treasure-guide-passive-capture-20260923-r1';
  let treasureGuideDomTimer=null;
  let treasureGuideLastDomFingerprint='';
  const treasureGuideSentKeys=new Set();

  function treasureGuideHash(text) {
    let hash=2166136261;
    for(let i=0;i<text.length;i++){hash^=text.charCodeAt(i);hash=Math.imul(hash,16777619);}
    return (hash>>>0).toString(16).padStart(8,'0');
  }

  function treasureGuideScreenVisible() {
    const text=String(document.body?.innerText||'');
    return /Карта\s+Сокровищ|Treasure\s+Map|نقشه\s+گنج/i.test(text);
  }

  function treasureGuideAssetUrls() {
    const urls=new Set();
    const add=value=>{
      const url=String(value||'').trim();
      if(/^https?:\/\//i.test(url))urls.add(url);
    };
    try{
      document.querySelectorAll('img').forEach(node=>add(node.currentSrc||node.src));
      document.querySelectorAll('[style*="background"]').forEach(node=>{
        const value=String(node.style?.backgroundImage||node.style?.background||'');
        for(const match of value.matchAll(/url\(["']?([^"')]+)["']?\)/g))add(match[1]);
      });
      performance.getEntriesByType('resource').slice(-500).forEach(entry=>{
        const url=String(entry?.name||'');
        if(!/hwgame\.cloud/i.test(url))return;
        if(/\.(?:png|jpe?g|webp|svg)(?:\?|$)/i.test(url)||/assets\/images|items\//i.test(url))add(url);
      });
    }catch(_){}
    return [...urls].slice(0,220);
  }

  function treasureGuidePayloadText(body) {
    try{
      const value=JSON.stringify(body);
      return value.length<=250000?value:value.slice(0,250000);
    }catch(_){return '';}
  }

  function treasureGuideApiRelevant(path, payloadText) {
    if(!path||path==='/player/me'||path.startsWith('/auth/'))return false;
    const visibleNow=treasureGuideScreenVisible();
    if(/treasure|quest|mission|task|event|adventure/i.test(path))return true;
    if(visibleNow && (
      path==='/events' ||
      path==='/client_config' ||
      path==='/items' ||
      path==='/shop/view' ||
      path.startsWith('/localization/')
    ))return true;
    const sample=String(payloadText||'').slice(0,180000);
    return /treasure[_ -]?map|treasure|карта.{0,20}сокровищ|сокровищ/i.test(sample);
  }

  async function treasureGuideSubmit(documentValue) {
    if(!licenseState.allowed)return;
    const captureKey=String(documentValue?.capture_key||'');
    if(!captureKey||treasureGuideSentKeys.has(captureKey))return;
    treasureGuideSentKeys.add(captureKey);
    if(treasureGuideSentKeys.size>180){
      const first=treasureGuideSentKeys.values().next().value;
      treasureGuideSentKeys.delete(first);
    }
    try{
      await licensedServerJson(
        CLAN_SHOP_FACT_API_BASE,
        '/treasure-guide/capture',
        documentValue,
        false,
        'treasure-guide'
      );
      recordDiagnostic('treasure-guide-capture',{
        source:documentValue.source,
        path:documentValue.path||'',
        assets:Array.isArray(documentValue.assets)?documentValue.assets.length:0
      });
    }catch(error){
      treasureGuideSentKeys.delete(captureKey);
      console.warn('[HK] Treasure guide capture failed',error);
    }
  }

  function acceptTreasureGuideApi(url,body) {
    if(!body||typeof body!=='object')return;
    let path='';
    try{path=new URL(String(url||''),location.href).pathname;}catch(_){return;}
    const payloadJson=treasureGuidePayloadText(body);
    if(!treasureGuideApiRelevant(path,payloadJson))return;
    const key='api:'+path+':'+treasureGuideHash(payloadJson);
    void treasureGuideSubmit({
      capture_key:key,
      source:'api',
      path,
      payload_json:payloadJson,
      page_text:'',
      assets:treasureGuideScreenVisible()?treasureGuideAssetUrls():[]
    });
  }

  function scanTreasureGuideDom() {
    if(!licenseState.allowed||!treasureGuideScreenVisible())return;
    const pageText=String(document.body?.innerText||'').replace(/\u00a0/g,' ').trim().slice(0,35000);
    const assets=treasureGuideAssetUrls();
    const fingerprint=treasureGuideHash(pageText+'\n'+assets.join('\n'));
    if(fingerprint===treasureGuideLastDomFingerprint)return;
    treasureGuideLastDomFingerprint=fingerprint;
    void treasureGuideSubmit({
      capture_key:'dom:'+fingerprint,
      source:'dom',
      path:location.pathname,
      payload_json:'',
      page_text:pageText,
      assets
    });
  }

  function scheduleTreasureGuideDomScan(delay=900) {
    if(treasureGuideDomTimer)clearTimeout(treasureGuideDomTimer);
    treasureGuideDomTimer=setTimeout(()=>{
      treasureGuideDomTimer=null;
      scanTreasureGuideDom();
    },delay);
  }

  function installTreasureGuideCapture() {
    if(window.__HK_TREASURE_GUIDE_CAPTURE__)return;
    window.__HK_TREASURE_GUIDE_CAPTURE__=true;
    const start=()=>{
      if(!document.body){setTimeout(start,300);return;}
      const observer=new MutationObserver(()=>scheduleTreasureGuideDomScan(1000));
      observer.observe(document.body,{childList:true,subtree:true,characterData:true});
      scheduleTreasureGuideDomScan(1200);
      setInterval(()=>{
        if(document.visibilityState==='visible'&&treasureGuideScreenVisible())scheduleTreasureGuideDomScan(250);
      },5000);
    };
    start();
  }

'''
if anchor not in s:
    raise SystemExit("network anchor missing")
s=s.replace(anchor,helpers+anchor,1)

old_fetch="if(response.ok && isGameApiRequest(url) && path!=='/player/me') response.clone().json().then(body=>{acceptSharedGameResponse(url,body);void acceptClanShopPurchaseHistory(url,body);}).catch(()=>{});"
new_fetch="if(response.ok && isGameApiRequest(url) && path!=='/player/me') response.clone().json().then(body=>{acceptSharedGameResponse(url,body);void acceptClanShopPurchaseHistory(url,body);acceptTreasureGuideApi(url,body);}).catch(()=>{});"
if old_fetch not in s:
    raise SystemExit("fetch observer target missing")
s=s.replace(old_fetch,new_fetch,1)

old_xhr="if(path!=='/player/me'){acceptSharedGameResponse(this.__hkUrl,body);void acceptClanShopPurchaseHistory(this.__hkUrl,body);}"
new_xhr="if(path!=='/player/me'){acceptSharedGameResponse(this.__hkUrl,body);void acceptClanShopPurchaseHistory(this.__hkUrl,body);acceptTreasureGuideApi(this.__hkUrl,body);}"
if old_xhr not in s:
    raise SystemExit("xhr observer target missing")
s=s.replace(old_xhr,new_xhr,1)

old_tail="""    networkCaptureInstalled = true;
    installClanShopDomHistoryCapture();
  }
"""
new_tail="""    networkCaptureInstalled = true;
    installClanShopDomHistoryCapture();
    installTreasureGuideCapture();
  }
"""
if old_tail not in s:
    raise SystemExit("network tail missing")
s=s.replace(old_tail,new_tail,1)

for marker in [
    "// @version      1.17.39",
    "const BUILD_VERSION = '1.17.39';",
    "HK_TREASURE_GUIDE_CAPTURE_REV='treasure-guide-passive-capture-20260923-r1'",
    "'/treasure-guide/capture'",
    "installTreasureGuideCapture();",
    "maps-manual-scan-only-20260923-r1",
]:
    if marker not in s:
        raise SystemExit("post-patch marker missing: "+marker)

PATH.write_text(s,encoding="utf-8")
print("TREASURE_GUIDE_PASSIVE_CAPTURE_1_17_39=PASS")
