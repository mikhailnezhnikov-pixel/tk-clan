from pathlib import Path

TARGET=Path('/tmp/HamsterKingMobile.user.js')
s=TARGET.read_text(encoding='utf-8')
REV='stage3c-fair-shop-verify-20260920-r1'

def require(needle,message):
    if needle not in s:
        raise SystemExit(message)

if '// @version      1.16.10' not in s and '// @version      1.16.11' not in s:
    raise SystemExit('Stage 3C requires Stage 3B 1.16.10 or existing 1.16.11')
require("HK_STAGE3B_BUSINESS_REV = 'stage3b-business-verify-20260920-r1'",'Stage 3B marker missing')

if f"HK_STAGE3C_FAIR_SHOP_REV = '{REV}'" not in s:
    s=s.replace('// @version      1.16.10','// @version      1.16.11',1)
    s=s.replace(": '1.16.10';",": '1.16.11';",1)
    marker="  const HK_STAGE3B_BUSINESS_REV = 'stage3b-business-verify-20260920-r1';"
    require(marker,'Stage 3B marker anchor missing')
    s=s.replace(marker,marker+f"\n  const HK_STAGE3C_FAIR_SHOP_REV = '{REV}';",1)
    runtime='  runtime.businessVerificationStage = HK_STAGE3B_BUSINESS_REV;'
    require(runtime,'Stage 3B runtime anchor missing')
    s=s.replace(runtime,runtime+"\n  runtime.fairShopVerificationStage = HK_STAGE3C_FAIR_SHOP_REV;",1)

# Manual Fair and Shop refreshes must never reuse a stale /shop/view catalog.
old="      if (!shopViewDocument) shopViewDocument = await apiJson('/shop/view', 'GET');"
new="      shopViewDocument = await apiJson('/shop/view', 'GET');"
count=s.count(old)
if count:
    s=s.replace(old,new)
elif s.count(new) < 3:
    raise SystemExit('Fair/Shop fresh catalog anchors missing')

# Re-read both balances and the shop catalog before Fair confirmation.
old="    const buyLimit = Math.max(1, Number(root.querySelector('#hk-fair-buy-limit').value || 1));"
new="""    try {
      playerDocument = await apiJson('/player/me', 'POST');
      fairDocument = playerDocument;
      shopViewDocument = await apiJson('/shop/view', 'GET');
      fairCatalog = normalizeFairCatalog(shopViewDocument);
      const missingSelected = [...selectedFairLots].filter(lotId => !fairCatalog.some(row => row.lotId === lotId && row.safe));
      if (missingSelected.length) {
        renderFair();
        alert(either('Каталог ярмарки изменился. Проверьте выбранные лоты ещё раз.','The fair catalog changed. Review the selected lots again.'));
        return;
      }
    } catch (error) {
      log(either('Не удалось обновить ярмарку перед запуском','Could not refresh the fair before starting') + ': ' + (error?.message || error),'bad');
      return;
    }
    const buyLimit = Math.max(1, Number(root.querySelector('#hk-fair-buy-limit').value || 1));"""
if old in s:
    s=s.replace(old,new,1)
elif "const missingSelected = [...selectedFairLots]" not in s:
    raise SystemExit('Fair preflight refresh anchor missing')

# Build the Shop plan only after a fresh /player/me and /shop/view read.
old="""  async function buyRegularShop() {
    if (!requireLicense() || shopRunning) return;
    const plan = shopRows.filter(row => row.section === selectedShopSection &&"""
new="""  async function buyRegularShop() {
    if (!requireLicense() || shopRunning) return;
    try {
      playerDocument = await apiJson('/player/me', 'POST');
      shopViewDocument = await apiJson('/shop/view', 'GET');
      shopRows = normalizeRegularShop();
    } catch (error) {
      log(either('Не удалось обновить магазин перед покупкой','Could not refresh the shop before purchase') + ': ' + (error?.message || error),'bad');
      return;
    }
    const plan = shopRows.filter(row => row.section === selectedShopSection &&"""
if old in s:
    s=s.replace(old,new,1)
elif "Could not refresh the shop before purchase" not in s:
    raise SystemExit('Shop preflight refresh anchor missing')

checks=[
    ('// @version      1.16.11','version missing'),
    (f"HK_STAGE3C_FAIR_SHOP_REV = '{REV}'",'marker missing'),
    ("const missingSelected = [...selectedFairLots]",'Fair fresh preflight missing'),
    ("Could not refresh the shop before purchase",'Shop fresh preflight missing'),
    ("GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'",'Hamster Caps invariant lost'),
    ("GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'",'General Pit Token invariant lost'),
]
for needle,message in checks:
    require(needle,message)

TARGET.write_text(s,encoding='utf-8')
