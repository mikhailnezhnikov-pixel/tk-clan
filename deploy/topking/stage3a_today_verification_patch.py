from pathlib import Path

TARGET=Path('/tmp/HamsterKingMobile.user.js')
s=TARGET.read_text(encoding='utf-8')
REV='stage3a-today-verify-20260920-r1'

def require(needle,message):
    if needle not in s:
        raise SystemExit(message)

if '// @version      1.16.8' not in s and '// @version      1.16.9' not in s:
    raise SystemExit('Stage 3A Today fix requires live 1.16.8 or existing 1.16.9')

if f"HK_STAGE3A_TODAY_REV = '{REV}'" not in s:
    s=s.replace('// @version      1.16.8','// @version      1.16.9',1)
    s=s.replace(": '1.16.8';",": '1.16.9';",1)
    marker="  const HK_STAGE2I_BUILDINGS_REV = 'stage2i-buildings-explore-20260919-r1';"
    require(marker,'Stage 2I Buildings marker missing')
    s=s.replace(marker,marker+f"\n  const HK_STAGE3A_TODAY_REV = '{REV}';",1)
    runtime='  runtime.buildingsExploreStage = HK_STAGE2I_BUILDINGS_REV;'
    require(runtime,'Stage 2I runtime marker missing')
    s=s.replace(runtime,runtime+"\n  runtime.todayVerificationStage = HK_STAGE3A_TODAY_REV;",1)

# Force a fresh shop read on every Today refresh.
old="      if (!shopViewDocument) shopViewDocument = await apiJson('/shop/view', 'GET');"
new="      shopViewDocument = await apiJson('/shop/view', 'GET');"
if old in s:
    s=s.replace(old,new,1)
elif new not in s:
    raise SystemExit('Today shop refresh anchor missing')

# Abort is a clean stop, not a skipped action.
old="        } catch (error) {\n          skipped++;"
new="        } catch (error) {\n          if (error?.name === 'AbortError' || hkRunner.signal?.aborted) break;\n          skipped++;"
if old in s:
    s=s.replace(old,new,1)
elif new not in s:
    raise SystemExit('Today action catch anchor missing')

# Reset the aborted runner before final reconciliation reads, then refresh shop too.
old="        await sleep(300);\n      }\n      playerDocument = await apiJson('/player/me', 'POST');\n      dailyShopRows = normalizeRegularShop();"
new="        await sleep(300);\n      }\n      const stopped=!!hkRunner.signal?.aborted;\n      if (stopped) hkRunner.reset();\n      playerDocument = await apiJson('/player/me', 'POST');\n      shopViewDocument = await apiJson('/shop/view', 'GET');\n      dailyShopRows = normalizeRegularShop();"
if old in s:
    s=s.replace(old,new,1)
elif new not in s:
    raise SystemExit('Today completion reconciliation anchor missing')

old="      const stopped=!!hkRunner.signal?.aborted;\n      log(stopped ?"
new="      log(stopped ?"
if old in s:
    s=s.replace(old,new,1)
elif new not in s:
    raise SystemExit('Today duplicate stopped anchor missing')

old="      if (stopped) hkRunner.reset(); else hkRunner.finish(either('План выполнен','Plan completed'));"
new="      if (!stopped) hkRunner.finish(either('План выполнен','Plan completed'));"
if old in s:
    s=s.replace(old,new,1)
elif new not in s:
    raise SystemExit('Today stop completion anchor missing')


# Daily Pit launched from Today must honor Pause inside a single Pit action,
# not only between top-level Today actions.
old="    while (!pitRaceFinished(state)) {\n      if (++battles > 1000)"
new="    while (!pitRaceFinished(state)) {\n      if (hkRunner.running) await hkRunner.waitIfPaused();\n      if (++battles > 1000)"
if old in s:
    s=s.replace(old,new,1)
elif new not in s:
    raise SystemExit('Daily Pit battle pause anchor missing')

old="    for (let attempt = 0; attempt < 3; attempt++) {\n      try {"
new="    for (let attempt = 0; attempt < 3; attempt++) {\n      if (hkRunner.running) await hkRunner.waitIfPaused();\n      try {"
if old in s:
    s=s.replace(old,new,1)
elif new not in s:
    raise SystemExit('Daily Pit finish pause anchor missing')

old="    for (const part of pitMovePlan(remainingRequested)) for (let index = 0; index < part.count; index++) {\n      // Re-read the wallet before every batch."
new="    for (const part of pitMovePlan(remainingRequested)) for (let index = 0; index < part.count; index++) {\n      if (hkRunner.running) await hkRunner.waitIfPaused();\n      // Re-read the wallet before every batch."
if old in s:
    s=s.replace(old,new,1)
elif new not in s:
    raise SystemExit('Daily Pit batch pause anchor missing')

checks=[
    ('// @version      1.16.9','version missing'),
    (f"HK_STAGE3A_TODAY_REV = '{REV}'",'marker missing'),
    ("shopViewDocument = await apiJson('/shop/view', 'GET');",'fresh shop read missing'),
    ("if (error?.name === 'AbortError' || hkRunner.signal?.aborted) break;",'abort break missing'),
    ("if (stopped) hkRunner.reset();",'pre-reconciliation reset missing'),
    ("if (!stopped) hkRunner.finish(either('План выполнен','Plan completed'));",'clean stop completion missing'),
    ("if (hkRunner.running) await hkRunner.waitIfPaused();",'Daily Pit pause checkpoint missing'),
    ("GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'",'Hamster Caps invariant lost'),
    ("GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'",'General Pit Token invariant lost'),
]
for needle,message in checks:
    require(needle,message)

TARGET.write_text(s,encoding='utf-8')
