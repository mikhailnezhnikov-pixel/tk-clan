from pathlib import Path

TARGET = Path('/tmp/HamsterKingMobile.user.js')
s = TARGET.read_text(encoding='utf-8')

REV = 'stage2c-state-20260919-r1'
BT = chr(96)

def require(needle, message):
    if needle not in s:
        raise SystemExit(message)

if '// @version      1.16.1' not in s and '// @version      1.16.2' not in s:
    raise SystemExit('Stage 2C requires Stage 2B 1.16.1 or existing Stage 2C 1.16.2')
require("HK_STAGE2B_RUNNER_REV = 'stage2b-20260919-r1'", 'Stage 2B revision missing')
require('const hkStateStore = (() => {', 'State Store missing')
require('function hkIsMutationRequest(', 'mutation classifier missing')

if f"HK_STAGE2_STATE_REV = '{REV}'" not in s:
    s = s.replace('// @version      1.16.1', '// @version      1.16.2', 1)
    s = s.replace(": '1.16.1';", ": '1.16.2';", 1)

    anchor = "  const HK_STAGE2B_RUNNER_REV = 'stage2b-20260919-r1';"
    require(anchor, 'Stage 2B marker missing')
    s = s.replace(anchor, anchor + f"\n  const HK_STAGE2_STATE_REV = '{REV}';", 1)

    runtime_anchor = '  runtime.legacyRunnerStageB = HK_STAGE2B_RUNNER_REV;'
    require(runtime_anchor, 'Stage 2B runtime marker missing')
    s = s.replace(runtime_anchor, runtime_anchor + "\n  runtime.stateMigrationStage = HK_STAGE2_STATE_REV;", 1)

old_merge = (
    "      if (path === '/player/me') {\n"
    "        const partial = !!(body && Array.isArray(body.arguments));\n"
    "        if (partial) hkStateStore.merge(value, 'api:player/me-partial'); else { hkStateStore.replace(value, 'api:player/me'); value = hkStateStore.snapshot || value; }\n"
    "      } else if (method !== 'GET' && (value.player || value.currencies || value.items || value.data?.player)) {\n"
    "        hkStateStore.merge(value, " + BT + "api:\${path}" + BT + ");\n"
    "      }\n"
    "      hkGameBridge.noteMutation(path, method);\n"
)
new_merge = (
    "      if (path === '/player/me') {\n"
    "        const partial = !!(body && Array.isArray(body.arguments));\n"
    "        if (partial) hkStateStore.merge(value, 'api:player/me-partial'); else { hkStateStore.replace(value, 'api:player/me'); value = hkStateStore.snapshot || value; }\n"
    "        playerDocument = hkStateStore.snapshot || value || playerDocument;\n"
    "      } else if (hkIsMutationRequest(path, method)) {\n"
    "        hkStateStore.merge(value, " + BT + "api:\${path}" + BT + ");\n"
    "        playerDocument = hkStateStore.snapshot || playerDocument;\n"
    "      }\n"
    "      hkGameBridge.noteMutation(path, method);\n"
)
if old_merge in s:
    s = s.replace(old_merge, new_merge, 1)
elif new_merge not in s:
    raise SystemExit('apiJson State Store merge block not found')

helper_anchor = "  function deepObjects(value, depth = 0, output = []) {"
if 'async function hkAuthoritativePlayerRead(' not in s:
    require(helper_anchor, 'deepObjects anchor missing')
    helper = (
        "  async function hkAuthoritativePlayerRead(reason='mutation-group') {\n"
        "    const value = await apiJson('/player/me','POST');\n"
        "    playerDocument = hkStateStore.snapshot || value || playerDocument;\n"
        "    recordDiagnostic('authoritative-player-read',{reason,revision:hkStateStore.exportSummary().revision});\n"
        "    return playerDocument;\n"
        "  }\n\n"
    )
    s = s.replace(helper_anchor, helper + helper_anchor, 1)

replacements = [
    (
        "      hkRunner.finish(either('Покупки завершены','Purchases completed'));\n      selectedShopLots.clear();",
        "      await hkAuthoritativePlayerRead('shop-complete');\n      shopRows = normalizeRegularShop();\n      hkRunner.finish(either('Покупки завершены','Purchases completed'));\n      selectedShopLots.clear();"
    ),
    (
        "      hkRunner.finish(either('Прокрутка завершена','Rerolls completed'));\n",
        "      await hkAuthoritativePlayerRead('recipes-complete');\n      hkRunner.finish(either('Прокрутка завершена','Rerolls completed'));\n"
    ),
    (
        "      hkRunner.finish(either('Проектное бюро завершено','Project Bureau completed'));\n",
        "      playerDocument = await hkAuthoritativePlayerRead('bureau-complete');\n      bureauInventory = normalizeInventory(playerDocument);\n      hkRunner.finish(either('Проектное бюро завершено','Project Bureau completed'));\n"
    ),
    (
        "      hkRunner.finish(either('Ярмарка завершена','Fair completed'));\n",
        "      playerDocument = await hkAuthoritativePlayerRead('fair-complete');\n      fairDocument = playerDocument;\n      hkRunner.finish(either('Ярмарка завершена','Fair completed'));\n"
    )
]
for old, new in replacements:
    if old in s:
        s = s.replace(old, new, 1)

checks = [
    ('// @version      1.16.2', 'Stage 2C version missing'),
    (f"HK_STAGE2_STATE_REV = '{REV}'", 'Stage 2C marker missing'),
    ("else if (hkIsMutationRequest(path, method))", 'all mutation responses are not merged'),
    ("playerDocument = hkStateStore.snapshot || playerDocument;", 'legacy document is not synchronized'),
    ("async function hkAuthoritativePlayerRead(", 'authoritative read helper missing'),
    ("hkAuthoritativePlayerRead('shop-complete')", 'Shop boundary reread missing'),
    ("hkAuthoritativePlayerRead('recipes-complete')", 'Recipes boundary reread missing'),
    ("hkAuthoritativePlayerRead('bureau-complete')", 'Bureau boundary reread missing'),
    ("hkAuthoritativePlayerRead('fair-complete')", 'Fair boundary reread missing'),
    ("GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'", 'Hamster Caps invariant lost'),
    ("GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'", 'General Pit Token invariant lost'),
]
for needle, message in checks:
    require(needle, message)

TARGET.write_text(s, encoding='utf-8')
