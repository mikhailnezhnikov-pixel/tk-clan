from pathlib import Path

PATH=Path("/tmp/HamsterKingMobile.user.js")
s=PATH.read_text(encoding="utf-8")
MARKER="treasure-guide-bundle-card-dom-20260923-r1"

if MARKER in s:
    print("TREASURE_BUNDLE_CARD_CAPTURE_ALREADY_PRESENT")
    raise SystemExit(0)

for required in [
    "// @version      1.17.78",
    "const BUILD_VERSION = '1.17.78';",
    "treasure-guide-passive-capture-20260923-r1",
    "treasure-guide-priority-bundles-20260923-r1",
    "runtime-smoke-fresh-run-20260923-r1",
    "runtime-smoke-autostart-20260923-r1",
    "function scanTreasureGuideDom()"
]:
    if required not in s:
        raise SystemExit("missing marker: "+required)

s=s.replace("// @version      1.17.78","// @version      1.17.79",1)
s=s.replace("const BUILD_VERSION = '1.17.78';","const BUILD_VERSION = '1.17.79';",1)

pos=s.find("// @release-note ")
if pos>=0:
    s=s[:pos]+"// @release-note Карта Сокровищ: пассивный DOM-захват теперь сохраняет структуру каждой из четырёх ограниченных карточек набора отдельно — текст, порядок узлов и игровые иконки; новых запросов к игре нет.\n"+s[pos:]

anchor="  function scanTreasureGuideDom() {\n"
helpers=r'''  const HK_TREASURE_GUIDE_BUNDLE_CARD_DOM_REV='treasure-guide-bundle-card-dom-20260923-r1';

  function treasureGuideCssUrls(value) {
    const out=[];
    const text=String(value||'');
    for(const match of text.matchAll(/url\(["']?([^"')]+)["']?\)/g)){
      const url=String(match[1]||'').trim();
      if(/^https?:\/\//i.test(url))out.push(url);
    }
    return out;
  }

  function treasureGuideDirectText(element) {
    try{
      return [...element.childNodes]
        .filter(node=>node.nodeType===Node.TEXT_NODE)
        .map(node=>String(node.nodeValue||'').replace(/\u00a0/g,' ').replace(/\s+/g,' ').trim())
        .filter(Boolean)
        .join(' ')
        .slice(0,240);
    }catch(_){return '';}
  }

  function treasureGuideBundleCardFor(anchor,name,names) {
    let node=anchor?.parentElement||anchor;
    let fallback=null;
    for(let depth=0;node&&depth<11;depth++,node=node.parentElement){
      let text='';
      try{text=String(node.innerText||'').replace(/\u00a0/g,' ').replace(/\s+/g,' ').trim();}catch(_){}
      if(!text||!text.includes(name))continue;
      const bundleHits=names.filter(item=>text.includes(item)).length;
      if(bundleHits>1)break;
      if(text.length>1400)continue;
      const quantityHits=(text.match(/x\s*[\d\s., ]+/gi)||[]).length;
      const hasPrice=/(?:^|\s)490(?:\s|$)/.test(text);
      if(quantityHits>=2){
        fallback=node;
        if(hasPrice)return node;
      }
    }
    return fallback;
  }

  function treasureGuideBundleCardSnapshot(card,name) {
    const elements=[card,...card.querySelectorAll('*')].slice(0,180);
    const nodes=[];
    for(let i=0;i<elements.length;i++){
      const el=elements[i];
      const media=[];
      try{
        if(el.tagName==='IMG'){
          const src=String(el.currentSrc||el.src||'').trim();
          if(/^https?:\/\//i.test(src))media.push(src);
        }
        media.push(...treasureGuideCssUrls(el.getAttribute?.('style')||''));
        const css=getComputedStyle(el);
        media.push(...treasureGuideCssUrls(css?.backgroundImage||''));
        media.push(...treasureGuideCssUrls(css?.maskImage||css?.webkitMaskImage||''));
        const before=getComputedStyle(el,'::before');
        media.push(...treasureGuideCssUrls(before?.backgroundImage||''));
        const after=getComputedStyle(el,'::after');
        media.push(...treasureGuideCssUrls(after?.backgroundImage||''));
      }catch(_){}
      const text=treasureGuideDirectText(el);
      const cleanMedia=media.filter((value,index,array)=>array.indexOf(value)===index).slice(0,8);
      if(!text&&!cleanMedia.length)continue;
      nodes.push({
        i,
        tag:String(el.tagName||'').toLowerCase(),
        cls:String(el.className||'').slice(0,220),
        text,
        media:cleanMedia
      });
      if(nodes.length>=120)break;
    }
    return {
      name,
      text:String(card?.innerText||'').replace(/\u00a0/g,' ').replace(/\s+/g,' ').trim().slice(0,1600),
      nodes
    };
  }

  function treasureGuideBundleCards() {
    const names=['Друзья в дорогу','Запас на удачу','Секреты под замком','Золотой урожай'];
    const anchors=new Map();
    try{
      const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
      let node;
      while((node=walker.nextNode())&&anchors.size<names.length){
        const value=String(node.nodeValue||'').replace(/\u00a0/g,' ').replace(/\s+/g,' ').trim();
        if(!value)continue;
        for(const name of names){
          if(!anchors.has(name)&&value.includes(name))anchors.set(name,node);
        }
      }
    }catch(_){}
    const out=[];
    for(const name of names){
      const anchorNode=anchors.get(name);
      if(!anchorNode)continue;
      const card=treasureGuideBundleCardFor(anchorNode,name,names);
      if(!card)continue;
      out.push(treasureGuideBundleCardSnapshot(card,name));
    }
    return out;
  }

'''
if anchor not in s:
    raise SystemExit("scanTreasureGuideDom anchor missing")
s=s.replace(anchor,helpers+anchor,1)

old=r'''  function scanTreasureGuideDom() {
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
'''
new=r'''  function scanTreasureGuideDom() {
    if(!licenseState.allowed||!treasureGuideScreenVisible())return;
    const pageText=String(document.body?.innerText||'').replace(/\u00a0/g,' ').trim().slice(0,35000);
    const assets=treasureGuideAssetUrls();
    const bundleCards=treasureGuideBundleCards();
    let bundleJson='';
    try{bundleJson=JSON.stringify({bundle_cards:bundleCards});}catch(_){bundleJson='';}
    const fingerprint=treasureGuideHash(pageText+'\n'+assets.join('\n')+'\n'+bundleJson);
    if(fingerprint===treasureGuideLastDomFingerprint)return;
    treasureGuideLastDomFingerprint=fingerprint;
    void treasureGuideSubmit({
      capture_key:'dom:'+fingerprint,
      source:'dom',
      path:location.pathname,
      payload_json:bundleJson,
      page_text:pageText,
      assets
    });
  }
'''
if old not in s:
    raise SystemExit("scanTreasureGuideDom exact block missing")
s=s.replace(old,new,1)

for marker in [
    "// @version      1.17.78",
    "const BUILD_VERSION = '1.17.78';",
    "HK_TREASURE_GUIDE_BUNDLE_CARD_DOM_REV='treasure-guide-bundle-card-dom-20260923-r1'",
    "function treasureGuideBundleCards()",
    "payload_json:bundleJson",
    "runtime-smoke-fresh-run-20260923-r1",
    "runtime-smoke-autostart-20260923-r1"
]:
    if marker not in s:
        raise SystemExit("post-patch marker missing: "+marker)

PATH.write_text(s,encoding="utf-8")
print("TREASURE_BUNDLE_CARD_CAPTURE_1_17_79=PASS")
