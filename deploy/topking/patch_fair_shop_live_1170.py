from pathlib import Path

TARGET = Path("/tmp/HamsterKingMobile.user.js")
REV = "fair-shop-live-verify-20260920-r1"
MARKER = f"// HK_FAIR_SHOP_LIVE_VERIFY_V1 {REV}"

def require(text, needle, message):
    if needle not in text:
        raise SystemExit(message)

def replace_once(text, old, new, label):
    if old in text:
        return text.replace(old, new, 1)
    if new in text:
        return text
    raise SystemExit(f"Fair/Shop live verification anchor missing: {label}")

def scoped_replace(text, start_token, end_token, old, new, label):
    start = text.find(start_token)
    end = text.find(end_token, start)
    if start < 0 or end < 0:
        raise SystemExit(f"Fair/Shop function bounds missing: {label}")
    segment = text[start:end]
    if old in segment:
        segment = segment.replace(old, new, 1)
        return text[:start] + segment + text[end:]
    if new in segment:
        return text
    raise SystemExit(f"Fair/Shop scoped anchor missing: {label}")

def apply_fair_shop_live_hotfix(text):
    require(text, "// @version      1.17.0", "Fair/Shop verification requires live 1.17.0")
    require(text, "HK_BUSINESS_LIVE_VERIFY_V1 business-live-verify-20260920-r1", "Business verification marker missing")
    require(text, "HK_MUTATION_RETRY_LIVE_V1 mutation-retry-live-20260920-r1", "Mutation retry safety marker missing")
    require(text, "GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'", "Hamsters must use Caps")
    require(text, "GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'", "Generals must use Pit Tokens")

    old_lazy = "      if (!shopViewDocument) shopViewDocument = await apiJson('/shop/view', 'GET');"
    fresh = "      shopViewDocument = await apiJson('/shop/view', 'GET');"
    text = scoped_replace(text, "  async function loadFair() {", "\n  function costVisual(", old_lazy, fresh, "loadFair fresh catalog")
    text = scoped_replace(text, "  async function loadShop() {", "\n  function ", old_lazy, fresh, "loadShop fresh catalog")

    old_fair = "    const buyLimit = Math.max(1, Number(root.querySelector('#hk-fair-buy-limit').value || 1));"
    new_fair = """    try {
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
    text = replace_once(text, old_fair, new_fair, "Fair preflight refresh")

    old_shop = """  async function buyRegularShop() {
    if (!requireLicense() || shopRunning) return;
    const plan = shopRows.filter(row => row.section === selectedShopSection &&"""
    new_shop = """  async function buyRegularShop() {
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
    text = replace_once(text, old_shop, new_shop, "Shop preflight refresh")

    anchor = "  // HK_BUSINESS_LIVE_VERIFY_V1 business-live-verify-20260920-r1"
    require(text, anchor, "Fair/Shop marker anchor missing")
    if MARKER not in text:
        text = text.replace(anchor, anchor + "\n  " + MARKER, 1)

    checks = [
        MARKER,
        "const missingSelected = [...selectedFairLots]",
        "Could not refresh the shop before purchase",
        "() => apiJsonCore(path, method, body, retryAuthorization, 0)",
        "GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'",
        "GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'",
    ]
    for needle in checks:
        require(text, needle, f"Fair/Shop verification check failed: {needle}")
    return text

if __name__ == "__main__":
    source = TARGET.read_text(encoding="utf-8")
    TARGET.write_text(apply_fair_shop_live_hotfix(source), encoding="utf-8")
    print("FAIR_SHOP_LIVE_1170_VERIFY_OK")
