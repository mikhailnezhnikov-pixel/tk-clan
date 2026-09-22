from pathlib import Path

PATH=Path("/tmp/HamsterKingMobile.user.js")
s=PATH.read_text(encoding="utf-8")
MARKER="clan-shop-purchase-history-parser-20260922-r2"

if MARKER in s:
    print("CLAN_SHOP_PURCHASE_HISTORY_PARSER_R2_ALREADY_PRESENT")
    raise SystemExit(0)

for required in [
    "// @version      1.17.31",
    "const BUILD_VERSION = '1.17.31';",
    "clan-shop-purchase-history-capture-20260922-r1",
    "function clanShopHistoryTimestamp(row)",
    "function clanShopHistoryBuyer(row)",
]:
    if required not in s:
        raise SystemExit("missing marker: "+required)

s=s.replace("// @version      1.17.31","// @version      1.17.32",1)
s=s.replace("const BUILD_VERSION = '1.17.31';","const BUILD_VERSION = '1.17.32';",1)
release="// @release-note Clan Shop теперь считывает фактическую историю общих покупок: кто именно купил шар идолов или S+ бизнес, по точному player_id."
s=s.replace(release,"// @release-note Исправлен разбор истории Clan Shop: дата и время из отдельных колонок, user_id/user_name и дополнительные поля ответа игры.\n"+release,1)

old_ts=r'''  function clanShopHistoryTimestamp(row) {
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
'''
new_ts=r'''  const HK_CLAN_SHOP_PURCHASE_HISTORY_PARSER_REV='clan-shop-purchase-history-parser-20260922-r2';
  function clanShopHistoryTimestamp(row) {
    if(!row||typeof row!=='object')return 0;
    const values=[
      row.purchased_at,row.purchasedAt,row.created_at,row.createdAt,row.timestamp,
      row.purchase_time,row.purchaseTime,row.datetime,row.date_time,row.dateTime,
      row.purchase_date_time,row.purchaseDateTime
    ];
    for(const value of values){
      if(value==null||value==='')continue;
      if(typeof value==='number'){
        const ms=value>100000000000?value:value*1000;
        if(Number.isFinite(ms)&&ms>900000000000)return Math.floor(ms/1000);
      }
      const text=String(value).trim();
      if(/^\d+(?:\.\d+)?$/.test(text)){
        let n=Number(text);if(n>100000000000)n/=1000;
        if(Number.isFinite(n)&&n>1000000000)return Math.floor(n);
      }
      const parsed=Date.parse(text);
      if(Number.isFinite(parsed)&&parsed>0)return Math.floor(parsed/1000);
    }

    const dateText=String(
      row.date??row.purchase_date??row.purchaseDate??row.created_date??row.createdDate??''
    ).trim();
    const timeText=String(
      row.time??row.purchase_time_text??row.purchaseTimeText??row.created_time??row.createdTime??''
    ).trim();
    if(dateText){
      const match=dateText.match(/^(\d{1,2})[.\/-](\d{1,2})(?:[.\/-](\d{2,4}))?$/);
      if(match){
        const day=Number(match[1]),month=Number(match[2]);
        let year=match[3]?Number(match[3]):new Date().getFullYear();
        if(year<100)year+=2000;
        let hour=0,minute=0,second=0;
        const tm=timeText.match(/^(\d{1,2}):(\d{2})(?::(\d{2}))?$/);
        if(tm){hour=Number(tm[1]);minute=Number(tm[2]);second=Number(tm[3]||0);}
        const local=new Date(year,month-1,day,hour,minute,second,0);
        if(Number.isFinite(local.getTime())&&local.getFullYear()===year&&local.getMonth()===month-1&&local.getDate()===day){
          return Math.floor(local.getTime()/1000);
        }
      }
    }
    return 0;
  }
'''
if s.count(old_ts)!=1:
    raise SystemExit(f"timestamp block expected once, got {s.count(old_ts)}")
s=s.replace(old_ts,new_ts,1)

old_buyer=r'''  function clanShopHistoryBuyer(row) {
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
'''
new_buyer=r'''  function clanShopHistoryBuyer(row) {
    if(!row||typeof row!=='object')return {player_id:'',nickname:''};
    const objectNodes=[row,row.player,row.buyer,row.purchaser,row.member,row.clan_member,row.clanMember,
      row.user&&typeof row.user==='object'?row.user:null,
      row.author&&typeof row.author==='object'?row.author:null].filter(Boolean);
    const idKeys=[
      'player_id','playerId','buyer_player_id','buyerPlayerId','user_id','userId',
      'purchaser_id','purchaserId','member_id','memberId','author_id','authorId'
    ];
    const nameKeys=[
      'nickname','name','username','user_name','userName','player_name','playerName',
      'display_name','displayName','buyer_name','buyerName','purchaser_name','purchaserName'
    ];
    let playerId='',nickname='';
    for(const node of objectNodes){
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
    if(!nickname){
      for(const key of ['user','author','buyer','purchaser']){
        const value=row?.[key];
        if(typeof value==='string'&&value.trim()&&!/^\d+$/.test(value.trim())){nickname=value.trim();break;}
      }
    }
    return {player_id:playerId,nickname};
  }
'''
if s.count(old_buyer)!=1:
    raise SystemExit(f"buyer block expected once, got {s.count(old_buyer)}")
s=s.replace(old_buyer,new_buyer,1)

# Expand item text keys seen in UI-oriented history payloads.
s=s.replace(
"const keys=['shop_lot_id','shopLotId','lot_id','lotId','id','name','title','lot_name','lotName','shop_lot_name','shopLotName','reward_id','rewardId'];",
"const keys=['shop_lot_id','shopLotId','lot_id','lotId','id','name','title','label','text','lot_name','lotName','shop_lot_name','shopLotName','reward_id','rewardId'];",
1)

for marker in [
    "// @version      1.17.32",
    "const BUILD_VERSION = '1.17.32';",
    "HK_CLAN_SHOP_PURCHASE_HISTORY_PARSER_REV='clan-shop-purchase-history-parser-20260922-r2'"
]:
    if marker not in s:
        raise SystemExit("post-patch marker missing: "+marker)

PATH.write_text(s,encoding="utf-8")
print("CLAN_SHOP_PURCHASE_HISTORY_PARSER_R2=PASS")
