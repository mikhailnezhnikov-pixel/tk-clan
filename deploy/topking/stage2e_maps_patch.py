from pathlib import Path
import re

TARGET = Path('/tmp/HamsterKingMobile.user.js')
s = TARGET.read_text(encoding='utf-8')

REV = 'stage2e-maps-20260919-r1'

def require(needle, message):
    if needle not in s:
        raise SystemExit(message)

if '// @version      1.16.3' not in s and '// @version      1.16.4' not in s:
    raise SystemExit('Stage 2E requires Stage 2D 1.16.3 or existing Stage 2E 1.16.4')
require("HK_STAGE2D_RUNNER_REV = 'stage2d-resource-business-20260919-r1'", 'Stage 2D missing')
require('async function submitOwnedMapAreas(', 'map contribution loop missing')
require('const hkRunner = (() => {', 'shared Runner missing')

if f"HK_STAGE2E_RUNNER_REV = '{REV}'" not in s:
    s = s.replace('// @version      1.16.3', '// @version      1.16.4', 1)
    s = s.replace(": '1.16.3';", ": '1.16.4';", 1)
    anchor = "  const HK_STAGE2D_RUNNER_REV = 'stage2d-resource-business-20260919-r1';"
    require(anchor, 'Stage 2D marker missing')
    s = s.replace(anchor, anchor + f"\n  const HK_STAGE2E_RUNNER_REV = '{REV}';", 1)
    runtime_anchor = '  runtime.resourceBusinessRunnerStage = HK_STAGE2D_RUNNER_REV;'
    require(runtime_anchor, 'Stage 2D runtime marker missing')
    s = s.replace(runtime_anchor, runtime_anchor + "\n  runtime.mapRunnerStage = HK_STAGE2E_RUNNER_REV;", 1)

start = s.find('  async function submitOwnedMapAreas(all = true) {')
end = s.find('  async function loadMapIndex(', start)
if start < 0 or end < 0:
    raise SystemExit('map contribution function boundaries missing')
block = s[start:end]

if "title:either('Исследование районов','District research')" not in block:
    block = block.replace(
        '    mapScanning = true;',
        "    if (hkRunner.running) { alert(either('Сначала завершите текущую задачу','Finish the current task first')); return; }\n"
        "    mapScanning = true;",
        1,
    )
    plan_anchor = "      const selected = all ? owned : owned.filter(row => String(row.gamearea_id) === currentId).slice(0,1);"
    if plan_anchor not in block:
        raise SystemExit('map selected districts anchor missing')
    block = block.replace(
        plan_anchor,
        plan_anchor + "\n"
        "      hkRunner.start({title:either('Исследование районов','District research'),total:selected.length,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});",
        1,
    )
    block = block.replace(
        '      for (let index=0; index<selected.length; index++) {',
        "      for (let index=0; index<selected.length; index++) {\n"
        "        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');\n"
        "        await hkRunner.waitIfPaused();\n"
        "        hkRunner.setStep(either('Исследование района','Researching district'),index,selected.length);",
        1,
    )
    block = block.replace('        await sleep(180);', '        await gameRetryDelay(180);', 1)
    completion = '      await loadMapIndex(false);'
    if completion not in block:
        raise SystemExit('map completion anchor missing')
    block = block.replace(
        completion,
        completion + "\n      hkRunner.finish(either('Исследование районов завершено','District research completed'));",
        1,
    )

    catch_pattern = re.compile(
        r"    \} catch \(error\) \{ log\([^\n]+\); \}\n"
        r"    finally \{ mapScanning=false; \}"
    )
    replacement = (
        "    } catch (error) {\n"
        "      if (error?.name === 'AbortError') { hkRunner.reset(); log(either('Исследование районов остановлено','District research stopped'),'warn'); }\n"
        "      else { hkRunner.fail(error); log(either('Ошибка исследования карт','Map research error') + ': ' + (error?.message || error),'bad'); }\n"
        "    }\n"
        "    finally { mapScanning=false; }"
    )
    block, count = catch_pattern.subn(replacement, block, count=1)
    if count != 1:
        raise SystemExit('map catch/finally anchor missing')

s = s[:start] + block + s[end:]

checks = [
    ('// @version      1.16.4', 'Stage 2E version missing'),
    (f"HK_STAGE2E_RUNNER_REV = '{REV}'", 'Stage 2E marker missing'),
    ("title:either('Исследование районов','District research')", 'map scan not routed to Runner'),
    ('await hkRunner.waitIfPaused();', 'map pause checkpoint missing'),
    ('await gameRetryDelay(180);', 'map delay not abort aware'),
    ("GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'", 'Hamster Caps invariant lost'),
    ("GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'", 'General Pit Token invariant lost'),
]
for needle, message in checks:
    require(needle, message)

TARGET.write_text(s, encoding='utf-8')
