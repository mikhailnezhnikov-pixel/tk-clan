from pathlib import Path

PATH=Path("/tmp/HamsterKingMobile.user.js")
s=PATH.read_text(encoding="utf-8")
MARKER="clan-shop-purchase-history-capture-20260922-r1"

if MARKER in s:
    print("CLAN_SHOP_PURCHASE_HISTORY_CAPTURE_ALREADY_PRESENT")
    raise SystemExit(0)

for required in [
    "// @version      1.17.24",
    "const BUILD_VERSION = '1.17.24';",
    "function installNetworkCapture()",
    "async function licensedServerJson(",
    "const CLAN_SHOP_FACT_API_BASE = 'https://hk-license.89.125.1.71.sslip.io/api/v1';",
]:
    if required not in s:
        raise SystemExit("missing marker: "+required)

s=s.replace("// @version      1.17.24","// @version      1.17.25",1)
s=s.replace("const BUILD_VERSION = '1.17.24';","const BUILD_VERSION = '1.17.25';",1)
release="// @release-note Clan Shop фиксирует игрока по его личному /player/me: шары и S+ записываются по player_id даже если сам магазин не открывался."
s=s.replace(release,"// @release-note Clan Shop теперь считывает фактическую историю общих покупок: кто именно купил шар идолов или S+ бизнес, по точному player_id.\n"+release,1)

anchor="  function installNetworkCapture() {\n"
helpers=r'''  const HK_CLAN_SHOP_PURCHASE_HISTORY_CAPTURE_REV='clan-shop-purchase-history-capture-20260922-r1';
  let clanShopPurchaseHistoryLastFingerprint='';

  function clanShopHistoryTextValue(value) {
    if(value==null)return '';
    if(typeof value==='string'||typeof value==='number')return String(value);
    return '';
  }

  function clanShopHistoryObjectText(row) {
    if(!row||typeof row!=='object')return '';
    const nested=[row,row.shop_lot,row.shopLot,row.lot,row.item,row.reward,row.view,row.lot_view,row.lotView].filter(Boolean);
    const keys=['shop_lot_id','shopLotId','lot_id','lotId','id','name','title','lot_name','lotName','shop_lot_name','shopLotName','reward_id','rewardId'];
    return nested.flatMap(obj=>keys.map(key=>clanShopHistoryTextValue(obj?.[key]))).filter(Boolean).join(' ').toLowerCase();
  }

  function clanShopHistoryItemType(row) {
    const text=clanShopHistoryObjectText(row);
    if(!text)return '';
    if(text.includes('mf_clan_shoplot_lvl20_bonus_hballs')||
       /шар.{0,32}идол|идол.{0,32}шар|idol.{0,32}ball|ball.{0,32}idol/.test(text))return 'idol_orbs';
    if(text.includes('mf_clan_shoplot_random_business_r3_lvl_15')||
       /случайн.{0,24}s\s*\+.{0,24}бизнес|s\s*\+.{0,24}бизнес|s\s*\+.{0,24}business|business.{0,24}s\s*\+/.test(text))return 'splus_businesses';
    return '';
  }

  function clanShopHistoryTimestamp(row) {
    if(!row||typeof row!=='object')return 0;
    const values=[
      row.purchased_at,row.purchasedAt,row.created_at,row.createdAt,row.timestamp,row.time,
      row.purchase_time,row.purchaseTime,row.date,row.datetime,row.date_time,row.dateTime
    ];
    for(const value of values){
      if(value==null||value==='')continue;
      if(typeof value==='number'){
        const ms=value>100000000000?value:value*1000;
        if(Number.isFinite(ms)&&ms>1000000000000-100000000000)return Math.floor(ms/1000);
      }
      const text=String(value).trim();
      if(/^\d+(?:\.\d+)?$/.test(text)){
        let n=Number(text);if(n>100000000000)n/=1000;
        if(Number.isFinite(n)&&n>1000000000)return Math.floor(n);
      }
      const parsed=Date.parse(text);
      if(Number.isFinite(parsed)&&parsed>0)return Math.floor(parsed/1000);
    }
    return 0;
  }

  function clanShopHistoryBuyer(row) {
    if(!row||typeof row!=='object')return {player_id:'',nickname:''};
    const nodes=[row,row.player,row.user,row.buyer,row.purchaser,row.member,row.clan_member,row.clanMember].filter(Boolean);
    const idKeys=['player_id','playerId','buyer_player_id','buyerPlayerId','user_id','userId','purchaser_id','purchaserId'];
    const nameKeys=['nickname','name','username','player_name','playerName','display_name','displayName'];
    let playerId='',nickname='';
    for(const node of nodes){
      if(!playerId){
        for(const key of idKeys){
          const value=String(node?.[key]??'').trim();
          if(/^\d{5,20}$/.test(value)){playerId=value;break;}
        }
        if(!playerId){
          const value=String(node?.id??'').trim();
          if(/^\d{5,20}$/.test(value))playerId=value;
        }
      }
      if(!nickname){
        for(const key of nameKeys){
          const value=String(node?.[key]??'').trim();
          if(value&&!/^\d+$/.test(value)){nickname=value;break;}
        }
      }
    }
    return {player_id:playerId,nickname};
  }

  function clanShopHistoryLot(row) {
    const nodes=[row,row.shop_lot,row.shopLot,row.lot,row.item,row.reward,row.view,row.lot_view,row.lotView].filter(Boolean);
    let lotId='',lotName='';
    for(const node of nodes){
      if(!lotId){
        for(const key of ['shop_lot_id','shopLotId','lot_id','lotId']){
          const value=String(node?.[key]??'').trim();if(value){lotId=value;break;}
        }
        if(!lotId){
          const value=String(node?.id??'').trim();
          if(value&&/shoplot|shop_lot|clan_shop/i.test(value))lotId=value;
        }
      }
      if(!lotName){
        for(const key of ['lot_name','lotName','shop_lot_name','shopLotName','name','title']){
          const value=String(node?.[key]??'').trim();if(value){lotName=value;break;}
        }
      }
    }
    return {lot_id:lotId,lot_name:lotName};
  }

  function clanShopHistoryHash(text) {
    let hash=2166136261;
    for(let i=0;i<text.length;i++){hash^=text.charCodeAt(i);hash=Math.imul(hash,16777619);}
    return (hash>>>0).toString(16).padStart(8,'0');
  }

  function clanShopPurchaseHistoryRows(path,documentValue) {
    if(!documentValue||typeof documentValue!=='object')return [];
    if(['/player/me','/shop/view','/shop/buy'].includes(path))return [];
    const result=[],seenObjects=new Set(),stack=[documentValue];
    while(stack.length&&seenObjects.size<4000){
      const row=stack.pop();
      if(!row||typeof row!=='object'||seenObjects.has(row))continue;
      seenObjects.add(row);
      if(Array.isArray(row)){for(const child of row)if(child&&typeof child==='object')stack.push(child);continue;}
      const itemType=clanShopHistoryItemType(row);
      const purchasedAt=itemType?clanShopHistoryTimestamp(row):0;
      if(itemType&&purchasedAt){
        const buyer=clanShopHistoryBuyer(row);
        const lot=clanShopHistoryLot(row);
        const explicit=String(row.event_id??row.eventId??row.history_id??row.historyId??row.transaction_id??row.transactionId??'').trim();
        const stable=explicit||clanShopHistoryHash(JSON.stringify(row));
        result.push({
          event_key:String(path||'unknown')+':'+stable,
          purchased_at:purchasedAt,
          buyer_player_id:buyer.player_id,
          buyer_nickname:buyer.nickname,
          lot_id:lot.lot_id,
          item_type:itemType,
          lot_name:lot.lot_name,
          source_path:String(path||'')
        });
      }
      for(const child of Object.values(row))if(child&&typeof child==='object')stack.push(child);
    }
    const unique=new Map();
    for(const row of result)unique.set(row.event_key,row);
    return [...unique.values()].slice(0,500);
  }

  async function acceptClanShopPurchaseHistory(url,documentValue) {
    if(!licenseState.allowed||!documentValue||typeof documentValue!=='object')return;
    let path='';try{path=new URL(String(url||''),location.href).pathname;}catch(_){}
    const rows=clanShopPurchaseHistoryRows(path,documentValue);
    if(!rows.length)return;
    const fingerprint=JSON.stringify(rows.map(row=>[row.event_key,row.buyer_player_id,row.item_type,row.purchased_at]));
    if(fingerprint===clanShopPurchaseHistoryLastFingerprint)return;
    try{
      const result=await licensedServerJson(CLAN_SHOP_FACT_API_BASE,'/clan-shop-events/submit',{rows},false,'clan-shop-events');
      clanShopPurchaseHistoryLastFingerprint=fingerprint;
      recordDiagnostic('clan-shop-purchase-history',{path,rows:rows.length,accepted:Number(result?.accepted||0),unresolved:Number(result?.unresolved||0)});
    }catch(error){
      console.warn('[HK] Clan Shop purchase history sync failed',error);
    }
  }

'''
if anchor not in s:
    raise SystemExit("network capture anchor missing")
s=s.replace(anchor,helpers+anchor,1)

old_fetch="""      if(response.ok && isGameApiRequest(url) && path!=='/player/me') response.clone().json().then(body=>acceptSharedGameResponse(url,body)).catch(()=>{});"""
new_fetch="""      if(response.ok && isGameApiRequest(url) && path!=='/player/me') response.clone().json().then(body=>{acceptSharedGameResponse(url,body);void acceptClanShopPurchaseHistory(url,body);}).catch(()=>{});"""
if old_fetch not in s:
    raise SystemExit("fetch observer anchor missing")
s=s.replace(old_fetch,new_fetch,1)

old_xhr="""              if(path!=='/player/me')acceptSharedGameResponse(this.__hkUrl,body);"""
new_xhr="""              if(path!=='/player/me'){acceptSharedGameResponse(this.__hkUrl,body);void acceptClanShopPurchaseHistory(this.__hkUrl,body);}"""
if old_xhr not in s:
    raise SystemExit("xhr observer anchor missing")
s=s.replace(old_xhr,new_xhr,1)

for marker in [
    "HK_CLAN_SHOP_PURCHASE_HISTORY_CAPTURE_REV='clan-shop-purchase-history-capture-20260922-r1'",
    "'/clan-shop-events/submit'",
    "// @version      1.17.25",
    "const BUILD_VERSION = '1.17.25';"
]:
    if marker not in s:
        raise SystemExit("post-patch marker missing: "+marker)

PATH.write_text(s,encoding="utf-8")
print("CLAN_SHOP_PURCHASE_HISTORY_CAPTURE_R1=PASS")
