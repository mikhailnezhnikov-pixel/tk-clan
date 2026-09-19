from pathlib import Path
import re

TARGET = Path('/tmp/HamsterKingMobile.user.js')
s = TARGET.read_text(encoding='utf-8')

REV = 'stage2d-resource-business-20260919-r1'

def require(needle, message):
    if needle not in s:
        raise SystemExit(message)

def function_slice(source, signature, next_signature):
    start = source.find(signature)
    if start < 0:
        raise SystemExit(f'{signature} not found')
    end = source.find(next_signature, start + len(signature))
    if end < 0:
        raise SystemExit(f'{next_signature} after {signature} not found')
    return start, end, source[start:end]

if '// @version      1.16.2' not in s and '// @version      1.16.3' not in s:
    raise SystemExit('Stage 2D requires Stage 2C 1.16.2 or existing Stage 2D 1.16.3')
require("HK_STAGE2_STATE_REV = 'stage2c-state-20260919-r1'", 'Stage 2C state migration missing')
require('async function hkAuthoritativePlayerRead(', 'authoritative player read helper missing')
require('const hkRunner = (() => {', 'shared Runner missing')

if f"HK_STAGE2D_RUNNER_REV = '{REV}'" not in s:
    s = s.replace('// @version      1.16.2', '// @version      1.16.3', 1)
    s = s.replace(": '1.16.2';", ": '1.16.3';", 1)
    anchor = "  const HK_STAGE2_STATE_REV = 'stage2c-state-20260919-r1';"
    require(anchor, 'Stage 2C marker missing')
    s = s.replace(anchor, anchor + f"\n  const HK_STAGE2D_RUNNER_REV = '{REV}';", 1)
    runtime_anchor = '  runtime.stateMigrationStage = HK_STAGE2_STATE_REV;'
    require(runtime_anchor, 'Stage 2C runtime marker missing')
    s = s.replace(runtime_anchor, runtime_anchor + "\n  runtime.resourceBusinessRunnerStage = HK_STAGE2D_RUNNER_REV;", 1)

# Resource tasks: preserve the existing planning/exchange logic and only add
# shared Runner ownership, pause/stop checkpoints and a final authoritative read.
start, end, block = function_slice(s, '  async function runResourceEvents(rows) {', '  function exportMobileSettings(')
if "title:either('Ресурсные здания','Resource buildings')" not in block:
    block = block.replace(
        '    resourceBusy = true; renderResources();',
        "    if (hkRunner.running) { alert(either('Сначала завершите текущую задачу','Finish the current task first')); return; }\n"
        "    hkRunner.start({title:either('Ресурсные здания','Resource buildings'),total:ready.length,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});\n"
        '    resourceBusy = true; renderResources();',
        1,
    )
    block = block.replace(
        '      for (const row of ready) {',
        "      for (const row of ready) {\n"
        "        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');\n"
        "        await hkRunner.waitIfPaused();\n"
        "        hkRunner.setStep(row.name || either('Ресурсное задание','Resource task'), completed, ready.length);",
        1,
    )
    block = block.replace(
        '            while (remaining > 0) {',
        "            while (remaining > 0) {\n"
        "              if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');\n"
        "              await hkRunner.waitIfPaused();",
        1,
    )
    success = '      resourceBusy = false;\n      await loadResources(false);'
    replacement = (
        "      resourceBusy = false;\n"
        "      await loadResources(false);\n"
        "      await hkAuthoritativePlayerRead('resources-complete');\n"
        "      hkRunner.finish(either('Ресурсные задания завершены','Resource tasks completed'));"
    )
    if success not in block:
        raise SystemExit('Resource completion anchor missing')
    block = block.replace(success, replacement, 1)

    catch_pattern = re.compile(
        r"    \} catch \(error\) \{\n"
        r"      log\([^\n]+\);\n"
        r"    \} finally \{",
        re.S,
    )
    block, count = catch_pattern.subn(
        "    } catch (error) {\n"
        "      if (error?.name === 'AbortError') { hkRunner.reset(); log(either('Ресурсные задания остановлены','Resource tasks stopped'),'warn'); }\n"
        "      else { hkRunner.fail(error); log(either('Ошибка выполнения ресурсного задания','Resource task error') + ': ' + (error?.message || error),'bad'); }\n"
        "    } finally {",
        block,
        count=1,
    )
    if count != 1:
        raise SystemExit('Resource catch/finally block not found')
s = s[:start] + block + s[end:]

# Business rearrangement: keep the existing remove/insert/activation/rollback
# algorithm. Runner only serializes it, pauses between confirmed operations,
# and aborts the current HTTP request on Stop.
start, end, block = function_slice(s, '  async function executeBusinessPlan() {', '  function prepareOriginalBusinessRestore(')
if "title:either('Перестановка бизнесов','Business rearrangement')" not in block:
    block = block.replace(
        '    businessBusy = true;',
        "    if (hkRunner.running) { alert(either('Сначала завершите текущую задачу','Finish the current task first')); return; }\n"
        "    hkRunner.start({title:either('Перестановка бизнесов','Business rearrangement'),total:Math.max(1,plan.length),step:either('Подготовка','Preparing'),pausable:true,stoppable:true});\n"
        '    businessBusy = true;',
        1,
    )
    block = block.replace(
        '      for (const [row] of plan) {',
        "      for (const [row] of plan) {\n"
        "        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');\n"
        "        await hkRunner.waitIfPaused();\n"
        "        hkRunner.setStep(either('Снимаю бизнесы','Removing businesses'), removed.length, Math.max(1,plan.length));",
        1,
    )
    block = block.replace(
        '      for (const [row, id] of plan) {',
        "      for (const [row, id] of plan) {\n"
        "        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');\n"
        "        await hkRunner.waitIfPaused();\n"
        "        hkRunner.setStep(either('Вставляю бизнесы','Inserting businesses'), inserted.length, Math.max(1,plan.length));",
        1,
    )
    block = block.replace(
        '      for (const [row, id] of inserted) {',
        "      for (const [row, id] of inserted) {\n"
        "        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');\n"
        "        await hkRunner.waitIfPaused();",
        1,
    )

    success = "      selectedSlots.clear(); selectedStock.clear(); preparedBusinessPlan = null; preparedBusinessPlanSource = '';"
    if success not in block:
        raise SystemExit('Business success anchor missing')
    block = block.replace(
        success,
        "      playerDocument = await hkAuthoritativePlayerRead('business-complete');\n"
        "      refreshBusinessData();\n"
        "      hkRunner.finish(either('Перестановка завершена','Rearrangement completed'));\n"
        + success,
        1,
    )

    catch_anchor = "    } catch (error) {\n      const changed = removed.length > 0 || inserted.length > 0;"
    if catch_anchor not in block:
        raise SystemExit('Business catch anchor missing')
    block = block.replace(
        catch_anchor,
        "    } catch (error) {\n"
        "      if (error?.name === 'AbortError') {\n"
        "        hkRunner.reset();\n"
        "        log(either('Перестановка остановлена. Текущую схему нужно перечитать.','Rearrangement stopped. Current layout must be reread.'),'warn');\n"
        "      } else {\n"
        "      hkRunner.fail(error);\n"
        "      const changed = removed.length > 0 || inserted.length > 0;",
        1,
    )
    final_pos = block.rfind("    } finally {")
    if final_pos < 0:
        raise SystemExit('Business final finally missing')
    block = block[:final_pos] + "      }\n" + block[final_pos:]
s = s[:start] + block + s[end:]

checks = [
    ('// @version      1.16.3', 'Stage 2D version missing'),
    (f"HK_STAGE2D_RUNNER_REV = '{REV}'", 'Stage 2D marker missing'),
    ("title:either('Ресурсные здания','Resource buildings')", 'Resource tasks are not on Runner'),
    ("hkAuthoritativePlayerRead('resources-complete')", 'Resource authoritative reread missing'),
    ("title:either('Перестановка бизнесов','Business rearrangement')", 'Business rearrangement is not on Runner'),
    ("hkAuthoritativePlayerRead('business-complete')", 'Business authoritative reread missing'),
    ("GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'", 'Hamster Caps invariant lost'),
    ("GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'", 'General Pit Token invariant lost'),
]
for needle, message in checks:
    require(needle, message)

TARGET.write_text(s, encoding='utf-8')
