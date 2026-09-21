from pathlib import Path

PATH = Path("/tmp/HamsterKingMobile.user.js")
s = PATH.read_text(encoding="utf-8")

def require(marker):
    if marker not in s:
        raise SystemExit("missing marker: " + marker)

def replace_once(old,new,label):
    global s
    count=s.count(old)
    if count!=1:
        raise SystemExit(f"{label}: expected 1 match, got {count}")
    s=s.replace(old,new,1)

for marker in [
    "// @version      1.17.24",
    "const HK_CORE_REVISION = 'core-20260921-r27-businesses-runner-canon';",
    "native-play-performance-20260921-r1",
    "puzzle-solver-v3-embedded-20260921-r1",
    "async function reportClanShopActualFacts()",
    "function acceptShopView(url, headers, documentValue)",
    "function acceptPlayerState(url, headers, documentValue, partial = false)",
]:
    require(marker)

release="// @release-note Убраны фоновые лаги: тяжёлый DOM-скан Ям больше не выполняется каждую секунду, а Бизнесы не перерисовываются после каждого нативного действия игры."
replace_once(
    release,
    "// @release-note Clan Shop теперь пассивно отправляет фактические счётчики игрока при уже выполненных игрой /player/me и /shop/view, без дополнительных запросов к игре.\n"+release,
    "release note"
)

replace_once(
    "  let shopViewDocument = null;\n",
    "  let shopViewDocument = null;\n  let clanShopFactSyncTimer = null;\n  let clanShopFactLastFingerprint = '';\n",
    "clan shop passive vars"
)

old_report = """  async function reportClanShopActualFacts() {
    const rows = shopRows.flatMap(row => {
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
    });
    if (!rows.length || !licenseState.allowed) return;
    try {
      await licensedServerJson(CLAN_SHOP_FACT_API_BASE, '/clan-shop-facts/submit', {rows}, false, 'clan-shop-facts');
    } catch (error) {
      console.warn('[HK] Clan Shop actual facts sync failed', error);
    }
  }
"""

new_report = """  const HK_CLAN_SHOP_PASSIVE_FACTS_REV='clan-shop-passive-facts-20260922-r1';
  function clanShopFactRows(sourceRows = shopRows) {
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

  async function reportClanShopActualFacts(sourceRows = shopRows, force = false) {
    const rows = clanShopFactRows(sourceRows);
    if (!rows.length || !licenseState.allowed) return;
    const fingerprint=JSON.stringify(rows.map(row=>[
      row.lot_id,row.item_type,row.shared_purchased,row.shared_maximum,row.player_purchased
    ]));
    if(!force && fingerprint===clanShopFactLastFingerprint) return;
    try {
      await licensedServerJson(CLAN_SHOP_FACT_API_BASE, '/clan-shop-facts/submit', {rows}, false, 'clan-shop-facts');
      clanShopFactLastFingerprint=fingerprint;
      recordDiagnostic('clan-shop-passive-facts',{rows:rows.length});
    } catch (error) {
      console.warn('[HK] Clan Shop actual facts sync failed', error);
    }
  }

  function scheduleClanShopActualFactsSync() {
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
replace_once(old_report,new_report,"passive fact reporter")

old_accept_shop="""  function acceptShopView(url, headers, documentValue) {
    if (!documentValue || typeof documentValue !== 'object' || !Array.isArray(documentValue.shop_lots)) return;
    shopViewDocument = documentValue;
    captureAuthorization(url, headers);
  }
"""
new_accept_shop="""  function acceptShopView(url, headers, documentValue) {
    if (!documentValue || typeof documentValue !== 'object' || !Array.isArray(documentValue.shop_lots)) return;
    shopViewDocument = documentValue;
    captureAuthorization(url, headers);
    scheduleClanShopActualFactsSync();
  }
"""
replace_once(old_accept_shop,new_accept_shop,"shop view passive sync")

old_player_tail="""    // Checking access is required to unlock the panel. This does not scan
    // districts or submit any map data; those actions remain manual.
    checkLicense(player);
    // Never scan or upload map areas automatically. The player must explicitly
"""
new_player_tail="""    // Checking access is required to unlock the panel. This does not scan
    // districts or submit any map data; those actions remain manual.
    checkLicense(player);
    scheduleClanShopActualFactsSync();
    // Never scan or upload map areas automatically. The player must explicitly
"""
replace_once(old_player_tail,new_player_tail,"player state passive sync")

old_license_startup="""      if (licenseState.allowed) setTimeout(() => {
        const startupTasks = [
          ['settings', synchronizeSettings],
          ['pit-observations', flushPitObservations],
          ['shared-pit', loadSharedPitPowers],
          ['clan-skills', refreshSharedClanSkills]
        ];
"""
new_license_startup="""      if (licenseState.allowed) setTimeout(() => {
        scheduleClanShopActualFactsSync();
        const startupTasks = [
          ['settings', synchronizeSettings],
          ['pit-observations', flushPitObservations],
          ['shared-pit', loadSharedPitPowers],
          ['clan-skills', refreshSharedClanSkills]
        ];
"""
replace_once(old_license_startup,new_license_startup,"license startup passive sync")

for marker in [
    "HK_CLAN_SHOP_PASSIVE_FACTS_REV='clan-shop-passive-facts-20260922-r1'",
    "scheduleClanShopActualFactsSync();",
    "clanShopFactLastFingerprint",
    "setTimeout(() => {",
    "},900);",
    "native-play-performance-20260921-r1",
    "puzzle-solver-v3-embedded-20260921-r1",
    "businesses-finalize-single-snapshot-20260921-r1",
]:
    require(marker)

# This feature must not issue any game API calls itself.
block=s[s.index("const HK_CLAN_SHOP_PASSIVE_FACTS_REV"):s.index("async function loadShop()",s.index("const HK_CLAN_SHOP_PASSIVE_FACTS_REV"))]
for forbidden in ["apiJson('/player/me'","apiJson('/shop/view'","nativeNetworkFetch("]:
    if forbidden in block:
        raise SystemExit("passive Clan Shop sync contains game request: "+forbidden)

PATH.write_text(s,encoding="utf-8")
print("CLAN_SHOP_PASSIVE_FACTS_R1=PASS")
