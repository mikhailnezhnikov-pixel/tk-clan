from pathlib import Path

TARGET = Path('/tmp/HamsterKingMobile.user.js')
s = TARGET.read_text(encoding='utf-8')

REV = 'stage2f-clan-20260919-r1'

def require(needle, message):
    if needle not in s:
        raise SystemExit(message)

if '// @version      1.16.4' not in s and '// @version      1.16.5' not in s:
    raise SystemExit('Stage 2F requires Stage 2E 1.16.4 or existing Stage 2F 1.16.5')
require("HK_STAGE2E_RUNNER_REV = 'stage2e-maps-20260919-r1'", 'Stage 2E missing')
require('async function scanClanSkills(automatic = false)', 'Clan scan function missing')
require('const hkRunner = (() => {', 'shared Runner missing')

if f"HK_STAGE2F_RUNNER_REV = '{REV}'" not in s:
    s = s.replace('// @version      1.16.4', '// @version      1.16.5', 1)
    s = s.replace(": '1.16.4';", ": '1.16.5';", 1)

    anchor = "  const HK_STAGE2E_RUNNER_REV = 'stage2e-maps-20260919-r1';"
    require(anchor, 'Stage 2E marker missing')
    s = s.replace(anchor, anchor + f"\n  const HK_STAGE2F_RUNNER_REV = '{REV}';", 1)

    runtime_anchor = '  runtime.mapRunnerStage = HK_STAGE2E_RUNNER_REV;'
    require(runtime_anchor, 'Stage 2E runtime marker missing')
    s = s.replace(runtime_anchor, runtime_anchor + "\n  runtime.clanRunnerStage = HK_STAGE2F_RUNNER_REV;", 1)

start = s.find('  async function scanClanSkills(automatic = false) {')
end = s.find('  async function maybeAutoScanClanSkills()', start)
if start < 0 or end < 0:
    raise SystemExit('Clan scan boundaries missing')
block = s[start:end]

if "title:either('Навыки клана','Clan skills')" not in block:
    old_head = (
        "  async function scanClanSkills(automatic = false) {\n"
        "    if (clanSkillScanning || !apiHeaders.Authorization) return false;\n"
        "    clanSkillScanning = true; renderClanSkills();"
    )
    new_head = (
        "  async function scanClanSkills(automatic = false) {\n"
        "    if (clanSkillScanning || !apiHeaders.Authorization) return false;\n"
        "    if (automatic && hkRunner.running) return false;\n"
        "    if (!automatic && hkRunner.running) { alert(either('Сначала завершите текущую задачу','Finish the current task first')); return false; }\n"
        "    const runnerOwned = !automatic;\n"
        "    if (runnerOwned) hkRunner.start({title:either('Навыки клана','Clan skills'),total:5,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});\n"
        "    const clanScanCheckpoint = async (step,done=0) => {\n"
        "      if (!runnerOwned) return;\n"
        "      if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');\n"
        "      await hkRunner.waitIfPaused();\n"
        "      hkRunner.setStep(step,done,5);\n"
        "    };\n"
        "    clanSkillScanning = true; renderClanSkills();"
    )
    if old_head not in block:
        raise SystemExit('Clan scan header anchor missing')
    block = block.replace(old_head, new_head, 1)

    block = block.replace(
        "          if (attempt) await sleep(1500 * attempt);",
        "          await clanScanCheckpoint(either('Данные клана','Clan data'),0);\n"
        "          if (attempt) await gameRetryDelay(1500 * attempt);",
        1
    )
    block = block.replace(
        "          if (attempt) await sleep(1200 * attempt);",
        "          await clanScanCheckpoint(either('Статистика навыков','Skill statistics'),1);\n"
        "          if (attempt) await gameRetryDelay(1200 * attempt);",
        1
    )

    fixed_waits = [
        "      await clanScanCheckpoint(either('Данные клана','Clan data'),2);\n      await gameRetryDelay(800);",
        "      await clanScanCheckpoint(either('Структура навыков','Skill structure'),3);\n      await gameRetryDelay(800);",
        "      await gameRetryDelay(800);",
        "      await gameRetryDelay(800);",
    ]
    for replacement in fixed_waits:
        if '      await sleep(800);' not in block:
            break
        block = block.replace('      await sleep(800);', replacement, 1)

    # The final true return in this function is the successful completion path.
    success_return = block.rfind('      return true;')
    if success_return < 0:
        raise SystemExit('Clan scan success return missing')
    block = (
        block[:success_return]
        + "      if (runnerOwned) hkRunner.finish(either('Навыки клана считаны','Clan skills read'));\n"
        + block[success_return:]
    )

    catch_start = block.rfind('    } catch (error) {')
    finally_start = block.find('    } finally {', catch_start)
    if catch_start < 0 or finally_start < 0:
        raise SystemExit('Clan scan catch/finally boundaries missing')
    catch_replacement = (
        "    } catch (error) {\n"
        "      if (runnerOwned && error?.name === 'AbortError') {\n"
        "        hkRunner.reset();\n"
        "        log(either('Считывание навыков остановлено','Clan skill scan stopped'),'warn');\n"
        "      } else {\n"
        "        if (runnerOwned) hkRunner.fail(error);\n"
        "        log(either('Ошибка чтения навыков клана','Clan skill read error') + ': ' + (error?.message || error), 'error');\n"
        "      }\n"
        "      return false;\n"
    )
    block = block[:catch_start] + catch_replacement + block[finally_start:]

s = s[:start] + block + s[end:]

checks = [
    ('// @version      1.16.5', 'Stage 2F version missing'),
    (f"HK_STAGE2F_RUNNER_REV = '{REV}'", 'Stage 2F marker missing'),
    ("title:either('Навыки клана','Clan skills')", 'Manual clan scan not routed to Runner'),
    ("if (automatic && hkRunner.running) return false;", 'Automatic scan does not defer to active Runner'),
    ("const runnerOwned = !automatic;", 'Clan runner ownership missing'),
    ("await gameRetryDelay(1500 * attempt);", 'Clan retry delay is not abort-aware'),
    ("await gameRetryDelay(1200 * attempt);", 'Clan stats retry delay is not abort-aware'),
    ("GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'", 'Hamster Caps invariant lost'),
    ("GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'", 'General Pit Token invariant lost'),
]
for needle, message in checks:
    require(needle, message)

TARGET.write_text(s, encoding='utf-8')
