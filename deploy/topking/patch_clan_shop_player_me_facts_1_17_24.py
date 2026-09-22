from pathlib import Path

PATH=Path("/tmp/HamsterKingMobile.user.js")
s=PATH.read_text(encoding="utf-8")
MARKER="clan-shop-player-me-facts-20260922-r2"

if MARKER in s:
    print("CLAN_SHOP_PLAYER_ME_FACTS_R2_ALREADY_PRESENT")
    raise SystemExit(0)

required=[
    "clan-shop-passive-facts-20260922-r1",
    "function clanShopFactRows(sourceRows = shopRows)",
    "function scheduleClanShopActualFactsSync()",
    "function acceptPlayerState(url, headers, documentValue, partial = false)",
]
for marker in required:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

old="""  function clanShopFactRows(sourceRows = shopRows) {
    return (Array.isArray(sourceRows) ? sourceRows : []).flatMap(row => {
      const itemType = clanShopActualFactType(row);
      if (!itemType) return [];
      return [{
        lot_id:String(row.lotId || ''),
        item_type:itemType,
        lot_name:gameText(row.name || '') || String(row.name || ''),
        reward_id:String(row.rewardId || ''),
        shared_purchased:Math.max(0, Number(row.sharedPurchased || 0)),
        shared_maximum:Math.max(0, Number(row.sharedMaximum || 0)),
        player_purchased:Math.max(0, Number(row.bought || 0))
      }];
    }).sort((a,b)=>a.lot_id.localeCompare(b.lot_id));
  }
"""

new="""  const HK_CLAN_SHOP_PLAYER_ME_FACTS_REV='clan-shop-player-me-facts-20260922-r2';
  const CLAN_SHOP_FACT_TARGETS={
    mf_clan_shoplot_lvl20_bonus_hballs:{
      item_type:'idol_orbs',
      lot_name:'item h ball idol all',
      reward_id:'item_h_ball_idol_all'
    },
    mf_clan_shoplot_random_business_r3_lvl_15:{
      item_type:'splus_businesses',
      lot_name:'clan shoplot random business splus',
      reward_id:'item_bsn_r3t2_max_taphballs'
    }
  };

  function clanShopPlayerFactRows(documentValue = playerDocument) {
    const limits=documentValue?.shop_lot_limits || documentValue?.player?.shop_lot_limits || [];
    const byId=new Map((Array.isArray(limits)?limits:[]).map(row=>[
      String(row?.shop_lot_id || ''),
      Math.max(0,Number(row?.number_of_purchase || 0))
    ]));
    return Object.entries(CLAN_SHOP_FACT_TARGETS).map(([lotId,target])=>({
      lot_id:lotId,
      item_type:target.item_type,
      lot_name:target.lot_name,
      reward_id:target.reward_id,
      shared_purchased:0,
      shared_maximum:0,
      player_purchased:byId.get(lotId) || 0
    }));
  }

  function clanShopFactRows(sourceRows = shopRows, documentValue = playerDocument) {
    const merged=new Map(clanShopPlayerFactRows(documentValue).map(row=>[row.lot_id,{...row}]));
    for(const row of (Array.isArray(sourceRows)?sourceRows:[])){
      const itemType=clanShopActualFactType(row);
      if(!itemType) continue;
      const lotId=String(row.lotId || '');
      const current=merged.get(lotId) || {
        lot_id:lotId,
        item_type:itemType,
        lot_name:gameText(row.name || '') || String(row.name || ''),
        reward_id:String(row.rewardId || ''),
        shared_purchased:0,
        shared_maximum:0,
        player_purchased:Math.max(0,Number(row.bought || 0))
      };
      current.item_type=itemType;
      current.lot_name=gameText(row.name || '') || String(row.name || '') || current.lot_name;
      current.reward_id=String(row.rewardId || '') || current.reward_id;
      current.shared_purchased=Math.max(current.shared_purchased||0,Math.max(0,Number(row.sharedPurchased || 0)));
      current.shared_maximum=Math.max(current.shared_maximum||0,Math.max(0,Number(row.sharedMaximum || 0)));
      current.player_purchased=Math.max(current.player_purchased||0,Math.max(0,Number(row.bought || 0)));
      merged.set(lotId,current);
    }
    return [...merged.values()].sort((a,b)=>a.lot_id.localeCompare(b.lot_id));
  }
"""

if s.count(old)!=1:
    raise SystemExit(f"clanShopFactRows block expected once, got {s.count(old)}")
s=s.replace(old,new,1)

old_schedule="""  function scheduleClanShopActualFactsSync() {
    if (!shopViewDocument || !playerDocument) return;
    if (clanShopFactSyncTimer) clearTimeout(clanShopFactSyncTimer);
    clanShopFactSyncTimer=setTimeout(() => {
      clanShopFactSyncTimer=null;
      if(!licenseState.allowed || !shopViewDocument || !playerDocument) return;
      const passiveRows=normalizeRegularShop(shopViewDocument,playerDocument);
      void reportClanShopActualFacts(passiveRows,false);
    },900);
  }
"""

new_schedule="""  function scheduleClanShopActualFactsSync() {
    if (!playerDocument) return;
    if (clanShopFactSyncTimer) clearTimeout(clanShopFactSyncTimer);
    clanShopFactSyncTimer=setTimeout(() => {
      clanShopFactSyncTimer=null;
      if(!licenseState.allowed || !playerDocument) return;
      const passiveRows=shopViewDocument ? normalizeRegularShop(shopViewDocument,playerDocument) : [];
      void reportClanShopActualFacts(passiveRows,false);
    },900);
  }
"""

if s.count(old_schedule)!=1:
    raise SystemExit(f"schedule block expected once, got {s.count(old_schedule)}")
s=s.replace(old_schedule,new_schedule,1)

# Mark the release note without touching version/core compatibility.
release="// @release-note Clan Shop теперь пассивно отправляет фактические счётчики игрока при уже выполненных игрой /player/me и /shop/view, без дополнительных запросов к игре."
if release in s:
    s=s.replace(
        release,
        "// @release-note Clan Shop фиксирует игрока по его личному /player/me: шары и S+ записываются по player_id даже если сам магазин не открывался.\n"+release,
        1
    )

# The passive block itself must still make zero game API requests.
block=s[s.index("const HK_CLAN_SHOP_PLAYER_ME_FACTS_REV"):s.index("async function loadShop()",s.index("const HK_CLAN_SHOP_PLAYER_ME_FACTS_REV"))]
for forbidden in ["apiJson('/player/me'","apiJson('/shop/view'","nativeNetworkFetch("]:
    if forbidden in block:
        raise SystemExit("player-me fact sync contains game request: "+forbidden)

for marker in [
    "HK_CLAN_SHOP_PLAYER_ME_FACTS_REV='clan-shop-player-me-facts-20260922-r2'",
    "CLAN_SHOP_FACT_TARGETS",
    "function clanShopPlayerFactRows(",
    "if (!playerDocument) return;",
    "native-play-performance-20260921-r1",
    "puzzle-solver-v3-embedded-20260921-r1",
]:
    if marker not in s:
        raise SystemExit("post-patch marker missing: "+marker)

PATH.write_text(s,encoding="utf-8")
print("CLAN_SHOP_PLAYER_ME_FACTS_R2=PASS")
