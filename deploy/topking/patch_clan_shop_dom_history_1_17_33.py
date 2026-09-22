from pathlib import Path

PATH=Path("/tmp/HamsterKingMobile.user.js")
s=PATH.read_text(encoding="utf-8")
MARKER="clan-shop-dom-history-capture-20260922-r3"

if MARKER in s:
    print("CLAN_SHOP_DOM_HISTORY_CAPTURE_ALREADY_PRESENT")
    raise SystemExit(0)

for required in [
    "// @version      1.17.32",
    "const BUILD_VERSION = '1.17.32';",
    "clan-shop-purchase-history-capture-20260922-r1",
    "clan-shop-purchase-history-parser-20260922-r2",
    "async function acceptClanShopPurchaseHistory(url,documentValue)",
    "function installNetworkCapture()",
]:
    if required not in s:
        raise SystemExit("missing marker: "+required)

s=s.replace("// @version      1.17.32","// @version      1.17.33",1)
s=s.replace("const BUILD_VERSION = '1.17.32';","const BUILD_VERSION = '1.17.33';",1)

release="// @release-note Исправлен разбор истории Clan Shop: дата и время из отдельных колонок, user_id/user_name и дополнительные поля ответа игры."
s=s.replace(
    release,
    "// @release-note Clan Shop дополнительно считывает видимые строки журнала покупок с экрана игры, если API-ответ не содержит удобной структуры истории.\n"+release,
    1
)

anchor="  function installNetworkCapture() {\n"
helpers=r'''  const HK_CLAN_SHOP_DOM_HISTORY_CAPTURE_REV='clan-shop-dom-history-capture-20260922-r3';
  let clanShopDomHistoryTimer=null;
  let clanShopDomHistoryFingerprint='';

  function clanShopDomPlayerId(row) {
    if(!row)return '';
    const nodes=[row,...row.querySelectorAll?.('*')||[]].slice(0,180);
    for(const node of nodes){
      for(const attr of [...(node?.attributes||[])]){
        const name=String(attr.name||'').toLowerCase();
        if(!/(player|user|member).*(id)|(^|-)id$/.test(name))continue;
        const value=String(attr.value||'').trim();
        const match=value.match(/(?:^|\D)(\d{5,20})(?:\D|$)/);
        if(match)return match[1];
      }
      const href=String(node?.getAttribute?.('href')||'');
      const match=href.match(/(?:player_id|playerId|user_id|userId|member_id|memberId)[=/:](\d{5,20})/i);
      if(match)return match[1];
    }
    return '';
  }

  function clanShopDomLotTypeAndName(text) {
    const value=String(text||'').replace(/\s+/g,' ').trim();
    const idol=value.match(/(?:Хомячий\s+Шар\s+Идолов(?:\s*x\s*\d+)?|Hamster\s+Idol\s+Ball(?:\s*x\s*\d+)?)/i);
    if(idol)return {item_type:'idol_orbs',lot_name:idol[0]};
    const business=value.match(/(?:Случайный\s+S\s*\+\s*Бизнес|Random\s+S\s*\+\s*Business)/i);
    if(business)return {item_type:'splus_businesses',lot_name:business[0]};
    return null;
  }

  function clanShopDomHistoryRows() {
    const body=document.body;
    if(!body)return [];
    const pageText=String(body.textContent||'');
    if(!/(Показывать\s+только\s+лоты\s+с\s+лимитом|Название\s+лота|Clan\s+Shop|lot\s+name)/i.test(pageText))return [];
    if(!/(Хомячий\s+Шар\s+Идолов|Случайный\s+S\s*\+\s*Бизнес|Hamster\s+Idol\s+Ball|Random\s+S\s*\+\s*Business)/i.test(pageText))return [];

    const itemNodes=[...body.querySelectorAll('*')].filter(node=>{
      if(!node||node.children?.length>12)return false;
      const text=String(node.textContent||'');
      return /(Хомячий\s+Шар\s+Идолов|Случайный\s+S\s*\+\s*Бизнес|Hamster\s+Idol\s+Ball|Random\s+S\s*\+\s*Business)/i.test(text);
    }).slice(0,500);

    const candidates=[];
    const seen=new Set();
    for(const leaf of itemNodes){
      let node=leaf,best=null;
      for(let depth=0;node&&node!==body&&depth<9;depth+=1,node=node.parentElement){
        const text=String(node.innerText||node.textContent||'').replace(/\s+/g,' ').trim();
        if(text.length>700)break;
        if(/\b\d{1,2}[.\/-]\d{1,2}(?:[.\/-]\d{2,4})?\b/.test(text)&&/\b\d{1,2}:\d{2}(?::\d{2})?\b/.test(text)){
          best=node;
          break;
        }
      }
      if(best&&!seen.has(best)){seen.add(best);candidates.push(best);}
    }

    const signatures=new Map();
    const result=[];
    for(const row of candidates){
      const raw=String(row.innerText||row.textContent||'').replace(/\u00a0/g,' ').replace(/[ \t]+/g,' ').trim();
      const oneLine=raw.replace(/\s*\n\s*/g,' ').replace(/\s+/g,' ').trim();
      const lot=clanShopDomLotTypeAndName(oneLine);
      if(!lot)continue;
      const dateMatch=oneLine.match(/\b(\d{1,2}[.\/-]\d{1,2}(?:[.\/-]\d{2,4})?)\b/);
      const timeMatch=oneLine.match(/\b(\d{1,2}:\d{2}(?::\d{2})?)\b/);
      if(!dateMatch||!timeMatch)continue;
      const purchasedAt=clanShopHistoryTimestamp({date:dateMatch[1],time:timeMatch[1]});
      if(!purchasedAt)continue;

      const lotPos=oneLine.toLowerCase().indexOf(lot.lot_name.toLowerCase());
      const timeEnd=(timeMatch.index||0)+timeMatch[0].length;
      let nickname=lotPos>timeEnd?oneLine.slice(timeEnd,lotPos).trim():'';
      nickname=nickname
        .replace(/^(?:Пользователь|User)\s*/i,'')
        .replace(/\s+/g,' ')
        .trim();

      if(!nickname){
        const parts=raw.split(/\n+/).map(value=>value.replace(/\s+/g,' ').trim()).filter(Boolean);
        const lotIndex=parts.findIndex(value=>clanShopDomLotTypeAndName(value));
        const timeIndex=parts.findIndex(value=>/^\d{1,2}:\d{2}(?::\d{2})?$/.test(value));
        if(lotIndex>timeIndex&&timeIndex>=0){
          nickname=parts.slice(timeIndex+1,lotIndex).join(' ').trim();
        }
      }
      if(!nickname||/^(?:Дата|Время|Пользователь|Название\s+лота|Date|Time|User|Lot\s+name)$/i.test(nickname))continue;

      const playerId=clanShopDomPlayerId(row);
      const signature=[
        dateMatch[1],timeMatch[1],nickname,lot.item_type,lot.lot_name
      ].join('|');
      const occurrence=(signatures.get(signature)||0)+1;
      signatures.set(signature,occurrence);
      const explicitId=[...row.attributes||[]]
        .map(attr=>String(attr.value||''))
        .find(value=>/(?:history|transaction|purchase|event)[-_:]?[A-Za-z0-9_-]{4,}/i.test(value))||'';
      const stable=explicitId||signature+'|'+occurrence;

      result.push({
        event_key:'dom:'+clanShopHistoryHash(stable),
        purchased_at:purchasedAt,
        buyer_player_id:playerId,
        buyer_nickname:nickname,
        lot_id:'',
        item_type:lot.item_type,
        lot_name:lot.lot_name,
        source_path:'dom:clan-shop-history'
      });
    }
    return result.slice(0,500);
  }

  async function scanClanShopDomHistory() {
    if(!licenseState.allowed)return;
    const rows=clanShopDomHistoryRows();
    if(!rows.length)return;
    const fingerprint=JSON.stringify(rows.map(row=>[row.event_key,row.buyer_player_id,row.item_type,row.purchased_at]));
    if(fingerprint===clanShopDomHistoryFingerprint)return;
    try{
      const result=await licensedServerJson(CLAN_SHOP_FACT_API_BASE,'/clan-shop-events/submit',{rows},false,'clan-shop-dom-history');
      clanShopDomHistoryFingerprint=fingerprint;
      recordDiagnostic('clan-shop-dom-history',{
        rows:rows.length,
        accepted:Number(result?.accepted||0),
        unresolved:Number(result?.unresolved||0)
      });
    }catch(error){
      console.warn('[HK] Clan Shop DOM history sync failed',error);
    }
  }

  function scheduleClanShopDomHistoryScan(delay=900) {
    if(clanShopDomHistoryTimer)clearTimeout(clanShopDomHistoryTimer);
    clanShopDomHistoryTimer=setTimeout(()=>{
      clanShopDomHistoryTimer=null;
      void scanClanShopDomHistory();
    },delay);
  }

  function installClanShopDomHistoryCapture() {
    if(window.__HK_CLAN_SHOP_DOM_HISTORY_CAPTURE__)return;
    window.__HK_CLAN_SHOP_DOM_HISTORY_CAPTURE__=true;
    const observer=new MutationObserver(()=>scheduleClanShopDomHistoryScan(900));
    const start=()=>{
      if(document.body){
        observer.observe(document.body,{childList:true,subtree:true});
        scheduleClanShopDomHistoryScan(1200);
        setInterval(()=>{
          if(document.visibilityState==='visible')scheduleClanShopDomHistoryScan(250);
        },5000);
      }else{
        setTimeout(start,300);
      }
    };
    start();
  }

'''
if anchor not in s:
    raise SystemExit("installNetworkCapture anchor missing")
s=s.replace(anchor,helpers+anchor,1)

old="""    networkCaptureInstalled = true;
  }
"""
new="""    networkCaptureInstalled = true;
    installClanShopDomHistoryCapture();
  }
"""
if s.count(old)<1:
    raise SystemExit("network capture tail missing")
s=s.replace(old,new,1)

for marker in [
    "// @version      1.17.33",
    "const BUILD_VERSION = '1.17.33';",
    "HK_CLAN_SHOP_DOM_HISTORY_CAPTURE_REV='clan-shop-dom-history-capture-20260922-r3'",
    "installClanShopDomHistoryCapture();",
    "'/clan-shop-events/submit'"
]:
    if marker not in s:
        raise SystemExit("post-patch marker missing: "+marker)

PATH.write_text(s,encoding="utf-8")
print("CLAN_SHOP_DOM_HISTORY_CAPTURE_R3=PASS")
