from pathlib import Path

TARGET = Path("/tmp/HamsterKingMobile.user.js")
REV = "stage3a-today-live-20260920-r2"
MARKER = f"// HK_TODAY_LIVE_VERIFY_V1 {REV}"
REFRESH_REV = "stage3a-today-live-20260920-r3"
REFRESH_MARKER = f"// HK_TODAY_REFRESH_FRESH_V1 {REFRESH_REV}"

def _replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f"Today hotfix anchor missing: {label}")
    return text.replace(old, new, 1)

def _require(text, needle, label):
    if needle not in text:
        raise SystemExit(f"Today hotfix check failed: {label}")

def _fix_today_refresh(text):
    start = text.find("  async function refreshDailyTasks() {")
    end = text.find("\n  function resourceCost(", start)
    if start < 0 or end < 0:
        raise SystemExit("Today refresh function boundaries missing")
    segment = text[start:end]
    old = "      if (!shopViewDocument) shopViewDocument = await apiJson('/shop/view', 'GET');"
    new = "      shopViewDocument = await apiJson('/shop/view', 'GET');"
    if old in segment:
        segment = segment.replace(old, new, 1)
        text = text[:start] + segment + text[end:]
    elif new not in segment:
        raise SystemExit("Today refresh shop anchor missing")
    return text

def _verify_today_refresh(text):
    start = text.find("  async function refreshDailyTasks() {")
    end = text.find("\n  function resourceCost(", start)
    if start < 0 or end < 0:
        raise SystemExit("Today refresh verification boundaries missing")
    segment = text[start:end]
    if "if (!shopViewDocument) shopViewDocument = await apiJson('/shop/view', 'GET');" in segment:
        raise SystemExit("Today refresh still reuses stale shop view")
    if "shopViewDocument = await apiJson('/shop/view', 'GET');" not in segment:
        raise SystemExit("Today refresh fresh shop read missing")

def apply_today_hotfix(text):
    _require(text, "// @version      1.17.0", "live version 1.17.0")
    _require(text, "GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'", "Hamsters must use Caps")
    _require(text, "GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'", "Generals must use Pit Tokens")
    if MARKER in text:
        text = _fix_today_refresh(text)
        if REFRESH_MARKER not in text:
            marker_anchor = f"  {MARKER}\n  async function refreshDailyTasks() {{"
            marker_new = f"  {MARKER}\n  {REFRESH_MARKER}\n  async function refreshDailyTasks() {{"
            if marker_anchor not in text:
                raise SystemExit("Today refresh follow-up marker anchor missing")
            text = text.replace(marker_anchor, marker_new, 1)
        _verify_today_refresh(text)
        _require(text, "if (error?.name === 'AbortError' || hkRunner.signal?.aborted) break;", "Today Stop classification")
        _require(text, "if (!stopped) hkRunner.finish(either('План выполнен','Plan completed'));", "Today clean Stop completion")
        _require(text, "GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'", "Hamsters invariant after hotfix")
        _require(text, "GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'", "Generals invariant after hotfix")
        return text

    # Today refresh must never reuse stale shop counters/prices.
    text = _fix_today_refresh(text)

    # Fair purchases launched from Today must honor Pause and propagate Stop.
    text = _replace_once(
        text,
        "      for (const target of action.slots || []) {\n        try {",
        "      for (const target of action.slots || []) {\n        if (hkRunner.running) await hkRunner.waitIfPaused();\n        try {",
        "Today Fair pause checkpoint",
    )
    text = _replace_once(
        text,
        "        } catch (error) {\n          errors.push(error.message);\n          log(`${action.label}: ${error.message}`, 'warn');\n        }",
        "        } catch (error) {\n          if (error?.name === 'AbortError' || hkRunner.signal?.aborted) throw error;\n          errors.push(error.message);\n          log(`${action.label}: ${error.message}`, 'warn');\n        }",
        "Today Fair Stop propagation",
    )

    # Multi-copy shop purchases must re-read both balance and shop counters
    # before every irreversible purchase, including the first one.
    text = _replace_once(
        text,
        "    for (let index = 0; index < requested; index++) {\n"
        "      // Reload both the player balance and the live shop counters before every\n"
        "      // purchase. A changed price, exhausted lot or budget limit skips the\n"
        "      // remaining copies instead of spending by stale data.\n"
        "      if (index > 0) playerDocument = await apiJson('/player/me', 'POST');\n"
        "      dailyShopRows = normalizeRegularShop();",
        "    for (let index = 0; index < requested; index++) {\n"
        "      if (hkRunner.running) await hkRunner.waitIfPaused();\n"
        "      // Reload both the player balance and the live shop counters before every\n"
        "      // purchase. A changed price, exhausted lot or budget limit skips the\n"
        "      // remaining copies instead of spending by stale data.\n"
        "      playerDocument = await apiJson('/player/me', 'POST');\n"
        "      shopViewDocument = await apiJson('/shop/view', 'GET');\n"
        "      dailyShopRows = normalizeRegularShop();",
        "fresh state before each Today shop purchase",
    )

    # Abort/Stop is not a failed/skipped purchase and must exit the Today loop.
    text = _replace_once(
        text,
        "          completed++;\n        } catch (error) {\n          skipped++;",
        "          completed++;\n        } catch (error) {\n"
        "          if (error?.name === 'AbortError' || hkRunner.signal?.aborted) break;\n"
        "          skipped++;",
        "Today Stop classification",
    )

    # Reset an aborted signal before authoritative reconciliation, and refresh
    # both player state and live shop state before rendering the final UI.
    text = _replace_once(
        text,
        "      playerDocument = await apiJson('/player/me', 'POST');\n"
        "      dailyShopRows = normalizeRegularShop();\n"
        "      dailySnapshot = {checkedAt:Date.now(), playerId:playerIdentity(playerDocument?.player || {}), periodStart:gamePeriodBounds().dayStart};",
        "      const stopped=!!hkRunner.signal?.aborted;\n"
        "      if (stopped) hkRunner.reset();\n"
        "      playerDocument = await apiJson('/player/me', 'POST');\n"
        "      shopViewDocument = await apiJson('/shop/view', 'GET');\n"
        "      dailyShopRows = normalizeRegularShop();\n"
        "      dailySnapshot = {checkedAt:Date.now(), playerId:playerIdentity(playerDocument?.player || {}), periodStart:gamePeriodBounds().dayStart};",
        "Today final authoritative reconciliation",
    )
    text = _replace_once(
        text,
        "      const stopped=!!hkRunner.signal?.aborted;\n"
        "      log(stopped ?",
        "      log(stopped ?",
        "remove duplicate Today stopped flag",
    )
    text = _replace_once(
        text,
        "      if (stopped) hkRunner.reset(); else hkRunner.finish(either('План выполнен','Plan completed'));",
        "      if (!stopped) hkRunner.finish(either('План выполнен','Plan completed'));",
        "Today clean Stop completion",
    )

    # Long Pit work launched from Today must pause at safe internal boundaries.
    text = _replace_once(
        text,
        "    while (!pitRaceFinished(state)) {\n      if (++battles > 1000)",
        "    while (!pitRaceFinished(state)) {\n"
        "      if (hkRunner.running) await hkRunner.waitIfPaused();\n"
        "      if (++battles > 1000)",
        "Daily Pit battle pause",
    )
    text = _replace_once(
        text,
        "    for (let attempt = 0; attempt < 3; attempt++) {\n      try {",
        "    for (let attempt = 0; attempt < 3; attempt++) {\n"
        "      if (hkRunner.running) await hkRunner.waitIfPaused();\n"
        "      try {",
        "Daily Pit finish pause",
    )
    text = _replace_once(
        text,
        "    for (const part of pitMovePlan(remainingRequested)) for (let index = 0; index < part.count; index++) {\n"
        "      // Re-read the wallet before every batch.",
        "    for (const part of pitMovePlan(remainingRequested)) for (let index = 0; index < part.count; index++) {\n"
        "      if (hkRunner.running) await hkRunner.waitIfPaused();\n"
        "      // Re-read the wallet before every batch.",
        "Daily Pit move pause",
    )

    if MARKER not in text:
        anchor = "  async function refreshDailyTasks() {"
        if anchor not in text:
            raise SystemExit("Today hotfix marker anchor missing")
        text = text.replace(anchor, f"  {MARKER}\n  {REFRESH_MARKER}\n{anchor}", 1)

    _verify_today_refresh(text)
    checks = [
        MARKER,
        REFRESH_MARKER,
        "      shopViewDocument = await apiJson('/shop/view', 'GET');",
        "if (error?.name === 'AbortError' || hkRunner.signal?.aborted) break;",
        "if (stopped) hkRunner.reset();",
        "if (!stopped) hkRunner.finish(either('План выполнен','Plan completed'));",
        "if (hkRunner.running) await hkRunner.waitIfPaused();",
        "GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'",
        "GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'",
    ]
    for needle in checks:
        _require(text, needle, needle)
    return text

if __name__ == "__main__":
    source = TARGET.read_text(encoding="utf-8")
    TARGET.write_text(apply_today_hotfix(source), encoding="utf-8")
    print("TODAY_LIVE_1170_HOTFIX_OK")
