from pathlib import Path
import sys

target = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/HamsterKingMobile.user.js")
s = target.read_text(encoding="utf-8")

def need(old, label, count=1):
    actual = s.count(old)
    if actual != count:
        raise SystemExit(f"{label}: expected {count}, got {actual}")

def replace(old, new, label, count=1):
    global s
    need(old, label, count)
    s = s.replace(old, new, count)

replace(
    "// @version      1.17.89",
    "// @version      1.17.90\n"
    "// @release-note Магазин: массовый выкуп больше не штурмует /shop/buy без пауз. Добавлен безопасный темп запросов, автоматическое ожидание 429 и продолжение покупки после cooldown без двойного списания; Runner показывает ожидание и текущий лот.",
    "metadata version",
)
replace(
    "const BUILD_VERSION = '1.17.89';",
    "const BUILD_VERSION = '1.17.90';",
    "build version",
)

marker = "const HK_SHOP_BUY_FAST_PATH_REV = 'shop-buy-fast-path-20260923-r1';"
replace(
    marker,
    marker + "\n  const HK_SHOP_RATE_LIMIT_RESUME_REV = 'shop-rate-limit-resume-20260925-r1';\n"
             "  const SHOP_BUY_MIN_GAP_MS = 700;\n"
             "  const SHOP_BUY_POST_429_GAP_MS = 1500;",
    "shop rate-limit marker",
)

replace(
    "      const fastShopBuy=normalizedPath==='/shop/buy';\n"
    "      const gapMs=fastShopBuy?0:gameApiCurrentGapMs();\n"
    "      gameApiNextRequestAt=Date.now()+gapMs;\n"
    "      recordDiagnostic('game-rate-gate',{path,method,gapMs,fastShopBuy,slowUntil:gameApiSlowUntil});",
    "      const fastShopBuy=normalizedPath==='/shop/buy';\n"
    "      const shopBuyGap=Date.now()<gameApiSlowUntil?SHOP_BUY_POST_429_GAP_MS:SHOP_BUY_MIN_GAP_MS;\n"
    "      const gapMs=fastShopBuy?shopBuyGap:gameApiCurrentGapMs();\n"
    "      gameApiNextRequestAt=Date.now()+gapMs;\n"
    "      recordDiagnostic('game-rate-gate',{path,method,gapMs,fastShopBuy,slowUntil:gameApiSlowUntil});",
    "shop request pacing",
)

anchor = "  async function buyRegularShop() {"
helper = """  function shopLotDisplayName(row) {
    return String(gameText(row?.name) || row?.name || row?.rewardId || row?.lotId || either('Лот','Lot'));
  }

  function shopRateLimitError(error) {
    return error?.name === 'HKRateLimitError' || Number(error?.httpStatus) === 429;
  }

  async function shopBuyWithRateLimitResume(body, label = '') {
    let rateHits = 0;
    while (true) {
      if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');
      await hkRunner.waitIfPaused();
      try {
        return await apiJson('/shop/buy', 'POST', body, true, 0);
      } catch (error) {
        if (!shopRateLimitError(error)) throw error;
        rateHits += 1;
        const waitMs = Math.max(
          1000,
          Number(error?.retryAfterMs || 0),
          gameApiCooldownRemainingMs(),
          GAME_API_429_FALLBACK_COOLDOWN_MS
        ) + 1200;
        const seconds = Math.ceil(waitMs / 1000);
        hkRunner.setStep(either(
          'Лимит игры · жду ' + seconds + ' сек.' + (label ? ' · ' + label : ''),
          'Game limit · waiting ' + seconds + ' sec.' + (label ? ' · ' + label : '')
        ));
        if (rateHits === 1 || rateHits % 3 === 0) {
          log(either(
            'Магазин: лимит 429. Жду ' + seconds + ' сек. и продолжу автоматически' + (label ? ' · ' + label : ''),
            'Shop: 429 rate limit. Waiting ' + seconds + ' sec. and resuming automatically' + (label ? ' · ' + label : '')
          ), 'warn');
        }
        recordDiagnostic('shop-rate-limit-resume',{label,rateHits,waitMs});
        await gameRetryDelay(waitMs);
      }
    }
  }

"""
replace(anchor, helper + anchor, "shop 429 helper")

replace(
    "              playerDocument = await apiJson('/shop/buy', 'POST', {\n"
    "                ...requestBody,\n"
    "                collection_entity_id:row.rewardId,\n"
    "                collection_count:batchMultiplier\n"
    "              }, true, 0);",
    "              playerDocument = await shopBuyWithRateLimitResume({\n"
    "                ...requestBody,\n"
    "                collection_entity_id:row.rewardId,\n"
    "                collection_count:batchMultiplier\n"
    "              }, shopLotDisplayName(row));",
    "batch shop buy",
)

replace(
    "            playerDocument = await apiJson('/shop/buy', 'POST', requestBody, true, 0);",
    "            playerDocument = await shopBuyWithRateLimitResume(requestBody, shopLotDisplayName(row));",
    "single shop buy",
)

replace(
    "            hkRunner.setStep(either('Покупка товаров','Buying items'), completed, count);\n"
    "            playerDocument = await shopBuyWithRateLimitResume(requestBody, shopLotDisplayName(row));",
    "            hkRunner.setStep(either('Покупка: ','Buying: ') + shopLotDisplayName(row), completed, count);\n"
    "            playerDocument = await shopBuyWithRateLimitResume(requestBody, shopLotDisplayName(row));",
    "single runner lot name",
)

for marker in [
    "// @version      1.17.90",
    "const BUILD_VERSION = '1.17.90';",
    "shop-rate-limit-resume-20260925-r1",
    "const SHOP_BUY_MIN_GAP_MS = 700;",
    "const SHOP_BUY_POST_429_GAP_MS = 1500;",
    "async function shopBuyWithRateLimitResume",
    "Магазин: лимит 429",
    "shopLotDisplayName(row)",
]:
    if marker not in s:
        raise SystemExit("missing marker: " + marker)

if "const gapMs=fastShopBuy?0:gameApiCurrentGapMs();" in s:
    raise SystemExit("zero-gap /shop/buy fast path still present")

target.write_text(s, encoding="utf-8")
print("SHOP_RATE_LIMIT_RESUME_1_17_90=PASS")
print("version=1.17.90")
