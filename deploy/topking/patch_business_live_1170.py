from pathlib import Path

TARGET = Path("/tmp/HamsterKingMobile.user.js")
REV = "business-live-verify-20260920-r1"
MARKER = f"// HK_BUSINESS_LIVE_VERIFY_V1 {REV}"

def require(text, needle, message):
    if needle not in text:
        raise SystemExit(message)

def replace_once(text, old, new, label):
    if old in text:
        return text.replace(old, new, 1)
    if new in text:
        return text
    raise SystemExit(f"Business live verification anchor missing: {label}")

def apply_business_live_hotfix(text):
    require(text, "// @version      1.17.0", "Business verification requires live 1.17.0")
    require(text, "HK_PIT_LIVE_VERIFY_V1 pit-live-verify-20260920-r1", "Pit verification marker missing")
    require(text, "HK_MUTATION_RETRY_LIVE_V1 mutation-retry-live-20260920-r1", "Mutation retry safety marker missing")
    require(text, "GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'", "Hamsters must use Caps")
    require(text, "GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'", "Generals must use Pit Tokens")

    text = replace_once(
        text,
        "    for (let attempt = 0; attempt < attempts; attempt++) {\n"
        "      playerDocument = await apiJson('/player/me', 'POST');",
        "    for (let attempt = 0; attempt < attempts; attempt++) {\n"
        "      if (hkRunner.running) await hkRunner.waitIfPaused();\n"
        "      playerDocument = await apiJson('/player/me', 'POST');",
        "business slot polling Pause",
    )
    text = replace_once(
        text,
        "    for (const row of pending) {\n"
        "      await finishPendingBusiness(row);",
        "    for (const row of pending) {\n"
        "      if (hkRunner.running) await hkRunner.waitIfPaused();\n"
        "      await finishPendingBusiness(row);",
        "manager release Pause",
    )

    anchor = "  // HK_PIT_LIVE_VERIFY_V1 pit-live-verify-20260920-r1"
    require(text, anchor, "Business marker anchor missing")
    if MARKER not in text:
        text = text.replace(anchor, anchor + "\n  " + MARKER, 1)

    checks = [
        MARKER,
        "if (hkRunner.running) await hkRunner.waitIfPaused();\n      playerDocument = await apiJson('/player/me', 'POST');",
        "if (hkRunner.running) await hkRunner.waitIfPaused();\n      await finishPendingBusiness(row);",
        "() => apiJsonCore(path, method, body, retryAuthorization, 0)",
        "GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'",
        "GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'",
    ]
    for needle in checks:
        require(text, needle, f"Business verification check failed: {needle}")
    return text

if __name__ == "__main__":
    source = TARGET.read_text(encoding="utf-8")
    TARGET.write_text(apply_business_live_hotfix(source), encoding="utf-8")
    print("BUSINESS_LIVE_1170_VERIFY_OK")
