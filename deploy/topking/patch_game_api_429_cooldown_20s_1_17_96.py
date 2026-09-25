from pathlib import Path
import sys

target=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=target.read_text(encoding="utf-8")

def need(old,label,count=1):
    actual=s.count(old)
    if actual!=count:
        raise SystemExit(f"{label}: expected {count}, got {actual}")

def rep(old,new,label,count=1):
    global s
    need(old,label,count)
    s=s.replace(old,new,count)

rep(
    "// @version      1.17.95",
    "// @version      1.17.96\n"
    "// @release-note Game API: базовый cooldown после HTTP 429 сокращён с 60 до 20 секунд. Магазин больше не добавляет сверху ещё 1,2 секунды перед повтором; если сервер явно прислал больший Retry-After, он по-прежнему уважается.",
    "version"
)
rep("const BUILD_VERSION = '1.17.95';","const BUILD_VERSION = '1.17.96';","build")

anchor="  const HK_GAME_API_RATE_GUARD_REV = 'game-api-rate-guard-20260922-r1';"
rep(anchor,anchor+"\n  const HK_GAME_API_429_COOLDOWN_20S_REV = 'game-api-429-cooldown-20s-20260925-r1';","429 marker")

rep(
    "  const GAME_API_429_FALLBACK_COOLDOWN_MS = 60 * 1000;",
    "  const GAME_API_429_FALLBACK_COOLDOWN_MS = 20 * 1000;",
    "429 fallback cooldown"
)

old="""        const waitMs = Math.max(
          1000,
          Number(error?.retryAfterMs || 0),
          gameApiCooldownRemainingMs(),
          GAME_API_429_FALLBACK_COOLDOWN_MS
        ) + 1200;"""
new="""        const waitMs = Math.max(
          1000,
          Number(error?.retryAfterMs || 0),
          gameApiCooldownRemainingMs(),
          GAME_API_429_FALLBACK_COOLDOWN_MS
        );"""
rep(old,new,"shop 429 extra delay")

for marker in [
    "// @version      1.17.96",
    "const BUILD_VERSION = '1.17.96';",
    "game-api-429-cooldown-20s-20260925-r1",
    "const GAME_API_429_FALLBACK_COOLDOWN_MS = 20 * 1000;",
    "shop-rate-limit-resume-20260925-r1",
    "resource-maximum-direct-run-20260925-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

if "GAME_API_429_FALLBACK_COOLDOWN_MS = 60 * 1000" in s:
    raise SystemExit("old 60s cooldown still present")
if ") + 1200;" in s and "shopBuyWithRateLimitResume" in s:
    # Guard specifically against leaving the known shop 429 safety pad in the current helper.
    block=s[s.find("async function shopBuyWithRateLimitResume"):s.find("async function buyRegularShop")]
    if ") + 1200;" in block:
        raise SystemExit("old shop 429 extra 1200ms still present")

target.write_text(s,encoding="utf-8")
print("GAME_API_429_COOLDOWN_20S_1_17_96=PASS")
