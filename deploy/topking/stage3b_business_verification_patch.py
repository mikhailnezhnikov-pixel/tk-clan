from pathlib import Path

TARGET=Path('/tmp/HamsterKingMobile.user.js')
s=TARGET.read_text(encoding='utf-8')
REV='stage3b-business-verify-20260920-r1'

def require(needle,message):
    if needle not in s:
        raise SystemExit(message)

if '// @version      1.16.9' not in s and '// @version      1.16.10' not in s:
    raise SystemExit('Stage 3B requires Stage 3A 1.16.9 or existing 1.16.10')
require("HK_STAGE3A_TODAY_REV = 'stage3a-today-verify-20260920-r1'",'Stage 3A Today marker missing')

if f"HK_STAGE3B_BUSINESS_REV = '{REV}'" not in s:
    s=s.replace('// @version      1.16.9','// @version      1.16.10',1)
    s=s.replace(": '1.16.9';",": '1.16.10';",1)
    marker="  const HK_STAGE3A_TODAY_REV = 'stage3a-today-verify-20260920-r1';"
    require(marker,'Stage 3A marker anchor missing')
    s=s.replace(marker,marker+f"\n  const HK_STAGE3B_BUSINESS_REV = '{REV}';",1)
    runtime='  runtime.todayVerificationStage = HK_STAGE3A_TODAY_REV;'
    require(runtime,'Stage 3A runtime anchor missing')
    s=s.replace(runtime,runtime+"\n  runtime.businessVerificationStage = HK_STAGE3B_BUSINESS_REV;",1)

# Pause must be observed while polling /player/me for an inserted business.
old="    for (let attempt = 0; attempt < attempts; attempt++) {\n      playerDocument = await apiJson('/player/me', 'POST');"
new="    for (let attempt = 0; attempt < attempts; attempt++) {\n      if (hkRunner.running) await hkRunner.waitIfPaused();\n      playerDocument = await apiJson('/player/me', 'POST');"
if old in s:
    s=s.replace(old,new,1)
elif new not in s:
    raise SystemExit('readBusinessSlot pause anchor missing')

# The preflight manager-release loop is part of the same Runner task.
old="    for (const row of pending) {\n      await finishPendingBusiness(row);"
new="    for (const row of pending) {\n      if (hkRunner.running) await hkRunner.waitIfPaused();\n      await finishPendingBusiness(row);"
if old in s:
    s=s.replace(old,new,1)
elif new not in s:
    raise SystemExit('releaseFreeBusinessManagers pause anchor missing')

checks=[
    ('// @version      1.16.10','version missing'),
    (f"HK_STAGE3B_BUSINESS_REV = '{REV}'",'marker missing'),
    ("if (hkRunner.running) await hkRunner.waitIfPaused();\n      playerDocument = await apiJson('/player/me', 'POST');",'business polling Pause missing'),
    ("if (hkRunner.running) await hkRunner.waitIfPaused();\n      await finishPendingBusiness(row);",'manager release Pause missing'),
    ("GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'",'Hamster Caps invariant lost'),
    ("GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'",'General Pit Token invariant lost'),
]
for needle,message in checks:
    require(needle,message)

TARGET.write_text(s,encoding='utf-8')
