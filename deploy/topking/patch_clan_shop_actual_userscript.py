# Deploy trigger: actual Clan Shop telemetry v1
from pathlib import Path
import re

p=Path("/tmp/HamsterKingMobile.user.js")
s=p.read_text()
MARKER="HK_CLAN_SHOP_ACTUAL_FACTS_V1"
if MARKER in s:
    print("CLAN_SHOP_USERSCRIPT_ALREADY_PATCHED")
    raise SystemExit(0)

s_version, n_version = re.subn(r"^// @version\s+\S+.*$", "// @version      1.17.0", s, count=1, flags=re.M)
if n_version != 1:
    raise SystemExit("userscript version metadata missing")
s = s_version

anchor="  const CLAN_SKILLS_API_BASE = 'https://hk-license.89.125.1.71.sslip.io/api/v1/clan-skills';\n"
if anchor not in s:
    raise SystemExit("CLAN_SKILLS_API_BASE anchor missing")
s=s.replace(anchor,anchor+"  const CLAN_SHOP_FACT_API_BASE = 'https://hk-license.89.125.1.71.sslip.io/api/v1';\n",1)

old="""        bought, maximum:bought + remaining, remaining, unlimited, section, clanGroup,
        icon:mediaUrl(view.icon_card || view.icon || content.icon_card || content.icon, rewardId)}];"""
new="""        bought, maximum:bought + remaining, remaining, unlimited, section, clanGroup,
        sharedPurchased:sharedLimit ? Math.max(0, Number(sharedLimit.value || 0)) : 0,
        sharedMaximum:sharedLimit ? Math.max(0, Number(sharedLimit.limit || 0) + Number(sharedLimit.bonus || 0)) : 0,
        icon:mediaUrl(view.icon_card || view.icon || content.icon_card || content.icon, rewardId)}];"""
if old not in s:
    raise SystemExit("normalize row anchor missing")
s=s.replace(old,new,1)

anchor="  async function loadShop() {\n"
helper=r"""  // HK_CLAN_SHOP_ACTUAL_FACTS_V1
  function clanShopActualFactType(row) {
    if (row?.section !== 'clan' || row?.clanGroup !== 'shared') return '';
    const label = clean(String(gameText(row?.name || '') || '') + ' ' + String(row?.name || '') + ' ' + String(row?.rewardId || '') + ' ' + String(row?.lotId || '')).toLowerCase();
    if (/шар.{0,24}идол|идол.{0,24}шар|idol.{0,24}ball|ball.{0,24}idol|guru.{0,24}ball|ball.{0,24}guru/.test(label)) return 'idol_orbs';
    if (/s\s*\+.{0,24}бизнес|бизнес.{0,24}s\s*\+|s\s*\+.{0,24}business|business.{0,24}s\s*\+|splus.{0,24}business|business.{0,24}splus/.test(label)) return 'splus_businesses';
    return '';
  }

  async function reportClanShopActualFacts() {
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
if anchor not in s:
    raise SystemExit("loadShop anchor missing")
s=s.replace(anchor,helper+anchor,1)

old="""      shopRows = normalizeRegularShop();
      selectedShopLots = new Set([...selectedShopLots].filter(id => shopRows.some(row => row.lotId === id && row.safe && row.remaining > 0)));"""
new="""      shopRows = normalizeRegularShop();
      void reportClanShopActualFacts();
      selectedShopLots = new Set([...selectedShopLots].filter(id => shopRows.some(row => row.lotId === id && row.safe && row.remaining > 0)));"""
if old not in s:
    raise SystemExit("loadShop normalize anchor missing")
s=s.replace(old,new,1)

old="""      await hkAuthoritativePlayerRead('shop-complete');
      shopRows = normalizeRegularShop();
      hkRunner.finish(either('Покупки завершены','Purchases completed'));"""
new="""      await hkAuthoritativePlayerRead('shop-complete');
      try { shopViewDocument = await apiJson('/shop/view', 'GET'); } catch (_) {}
      shopRows = normalizeRegularShop();
      void reportClanShopActualFacts();
      hkRunner.finish(either('Покупки завершены','Purchases completed'));"""
if old not in s:
    raise SystemExit("buy completion anchor missing")
s=s.replace(old,new,1)

p.write_text(s)
print("CLAN_SHOP_USERSCRIPT_PATCH_OK")
