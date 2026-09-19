from pathlib import Path
import re

TARGET = Path('/tmp/HamsterKingMobile.user.js')
s = TARGET.read_text(encoding='utf-8')

STAGE2_REV = 'stage2a-20260919-r1'

def require(needle, message):
    if needle not in s:
        raise SystemExit(message)

def replace_once(old, new, message):
    global s
    if old not in s:
        raise SystemExit(message)
    s = s.replace(old, new, 1)

def function_slice(source, signature, next_signature):
    start = source.find(signature)
    if start < 0:
        raise SystemExit(f'{signature} not found')
    end = source.find(next_signature, start + len(signature))
    if end < 0:
        raise SystemExit(f'{next_signature} after {signature} not found')
    return start, end, source[start:end]

is_stage1 = '// @version      1.15.0' in s and "HK_MUTATION_GATE_REV = 'stage1-20260919-r4'" in s
is_stage2 = '// @version      1.16.0' in s and f"HK_STAGE2_RUNNER_REV = '{STAGE2_REV}'" in s
if not (is_stage1 or is_stage2):
    raise SystemExit('Stage 2 requires verified Stage 1 1.15.0 / r4 or the same Stage 2 revision')

# Never allow Stage 2 to alter the verified Growth currency split.
require("GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'", 'Hamster budget is not Caps')
require("GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'", 'General budget is not Pit Tokens')
require('const hkRunner = (() => {', 'shared hkRunner missing')
require("stop(reason='user')", 'hkRunner Stop/Abort support missing')
require('async waitIfPaused()', 'hkRunner pause support missing')
require('async function gameRetryDelay', 'abort-aware delay helper missing')
require('async function apiJson', 'API helper missing')

if is_stage1:
    s = s.replace('// @version      1.15.0', '// @version      1.16.0', 1)
    s = s.replace(": '1.15.0';", ": '1.16.0';", 1)

# Revision marker: keep it close to the runtime registration and make the patch idempotent.
runtime_anchor = '  runtime.runner = hkRunner;'
require(runtime_anchor, 'runtime runner registration missing')
if f"  const HK_STAGE2_RUNNER_REV = '{STAGE2_REV}';" not in s:
    s = s.replace(
        runtime_anchor,
        f"  const HK_STAGE2_RUNNER_REV = '{STAGE2_REV}';\n" + runtime_anchor + "\n  runtime.legacyRunnerStage = HK_STAGE2_RUNNER_REV;",
        1,
    )

# ---------- Pit ----------
pit_start, pit_end, pit = function_slice(s, '  async function pitLoop() {', '  function updatePitStatus(')
if 'await hkRunner.waitIfPaused();' not in pit:
    pit = pit.replace(
        '    while (pitRunning) {',
        "    while (pitRunning) {\n      if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');\n      await hkRunner.waitIfPaused();",
        1,
    )
pit = pit.replace('await sleep(Math.max(700, settings.interval * 1000));', 'await gameRetryDelay(Math.max(700, settings.interval * 1000));')
pit = pit.replace('await sleep(500);', 'await gameRetryDelay(500);')
s = s[:pit_start] + pit + s[pit_end:]

pit_handler_pattern = re.compile(
    r"    root\.querySelector\('#hk-pit-start'\)\.onclick = \(\) => \{.*?\n    \};\n"
    r"    root\.querySelector\('#hk-pit-stop'\)\.onclick = \(\) => \{.*?\};",
    re.S,
)
pit_handler_replacement = r"""    root.querySelector('#hk-pit-start').onclick = async () => {
      if (!requireLicense()) return;
      if (hkRunner.running) { alert(either('Сначала завершите текущую задачу','Finish the current task first')); return; }
      settings = {
        target: Math.max(1, Number(root.querySelector('#hk-target').value || 1)),
        interval: Math.max(.7, Number(root.querySelector('#hk-interval').value || 1.2)),
        activationLimit: Math.max(0, Number(root.querySelector('#hk-activation-limit').value || 0)),
        restoreLimit: Math.max(0, Number(root.querySelector('#hk-restore-limit').value || 0)),
        allowTokens: root.querySelector('#hk-allow-tokens').checked,
        collectOnly: root.querySelector('#hk-pit-collect-only').checked
      };
      save({settings});
      activationSpent = 0;
      restoreSpent = 0;
      pitRunStart = (() => { const state=pitState(); return {round:state.round,power:pitPowerValue(state)}; })();
      hkRunner.start({title:either('Яма','Pit'),step:either('Автобой','Auto battle'),pausable:true,stoppable:true});
      pitRunning = true;
      updatePitButtons();
      log(settings.collectOnly ? either('Запущен безопасный сбор данных Ямы без боя','Started safe Pit data collection without battle') : `Автобой запущен до раунда ${settings.target}`);
      try {
        await pitLoop();
        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');
        hkRunner.finish(either('Яма завершена','Pit completed'));
      } catch (error) {
        if (error?.name === 'AbortError') {
          hkRunner.reset();
          log(either('Автобой остановлен','Auto battle stopped'),'warn');
        } else {
          hkRunner.fail(error);
          log(`${either('Ошибка Ямы','Pit error')}: ${error?.message || error}`,'bad');
        }
      } finally {
        pitRunning = false;
        updatePitButtons();
      }
    };
    root.querySelector('#hk-pit-stop').onclick = () => {
      pitRunning = false;
      hkRunner.stop('pit');
      updatePitButtons();
      log(either('Останавливаю автобой…','Stopping auto battle…'),'warn');
    };"""
if STAGE2_REV not in s or "hkRunner.stop('pit')" not in s:
    s, count = pit_handler_pattern.subn(lambda _: pit_handler_replacement, s, count=1)
    if count != 1:
        raise SystemExit('Pit Start/Stop handler block not found')

# ---------- Fair ----------
fair_start, fair_end, fair = function_slice(s, '  async function runFair() {', '  function ordinaryShopGroup(')
if "title:either('Ярмарка','Fair')" not in fair:
    fair = fair.replace(
        "    fairRunning = true; fairStop = false; updateFairControls();",
        "    if (hkRunner.running) { alert(either('Сначала завершите текущую задачу','Finish the current task first')); return; }\n"
        "    hkRunner.start({title:either('Ярмарка','Fair'),total:buyLimit,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});\n"
        "    fairRunning = true; fairStop = false; updateFairControls();",
        1,
    )
    fair = fair.replace(
        "      while (!fairStop && bought < buyLimit) {",
        "      while (!fairStop && bought < buyLimit) {\n"
        "        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');\n"
        "        await hkRunner.waitIfPaused();\n"
        "        hkRunner.setStep(either('Поиск и покупка лотов','Searching and buying lots'), bought, buyLimit);",
        1,
    )
    fair = fair.replace('        await sleep(550);', '        await gameRetryDelay(550);')
    fair = fair.replace(
        "      log(`Ярмарка завершена: выбранных покупок ${bought}, бонусных ${bonusBought}, прокруток ${rerolls}`, 'ok');",
        "      hkRunner.finish(either('Ярмарка завершена','Fair completed'));\n"
        "      log(`Ярмарка завершена: выбранных покупок ${bought}, бонусных ${bonusBought}, прокруток ${rerolls}`, 'ok');",
        1,
    )
    old_catch = "    } catch (error) { log(`Аварийная остановка ярмарки: ${error.message}`, 'bad'); }\n    finally { fairRunning = false; fairStop = false; renderFair(); }"
    new_catch = "    } catch (error) {\n"
    new_catch += "      if (error?.name === 'AbortError') { hkRunner.reset(); log(either('Ярмарка остановлена','Fair stopped'),'warn'); }\n"
    new_catch += "      else { hkRunner.fail(error); log(`Аварийная остановка ярмарки: ${error.message}`, 'bad'); }\n"
    new_catch += "    } finally { fairRunning = false; fairStop = false; renderFair(); }"
    if old_catch not in fair:
        raise SystemExit('Fair catch/finally block not found')
    fair = fair.replace(old_catch, new_catch, 1)
s = s[:fair_start] + fair + s[fair_end:]

old_fair_stop = "    root.querySelector('#hk-fair-stop').onclick = () => { fairStop = true; log('Останавливаю ярмарку после текущего запроса…', 'warn'); };"
new_fair_stop = "    root.querySelector('#hk-fair-stop').onclick = () => { fairStop = true; hkRunner.stop('fair'); log(either('Останавливаю ярмарку…','Stopping fair…'), 'warn'); };"
if old_fair_stop in s:
    s = s.replace(old_fair_stop, new_fair_stop, 1)
elif "hkRunner.stop('fair')" not in s:
    raise SystemExit('Fair Stop handler not found')

# Final Stage 2A invariants.
checks = [
    ('// @version      1.16.0', 'Stage 2 version missing'),
    (f"HK_STAGE2_RUNNER_REV = '{STAGE2_REV}'", 'Stage 2 revision missing'),
    ("GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'", 'Hamster Caps invariant lost'),
    ("GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'", 'General Pit Token invariant lost'),
    ("hkRunner.stop('pit')", 'Pit Stop is not routed to hkRunner'),
    ("title:either('Яма','Pit')", 'Pit is not routed to hkRunner'),
    ("title:either('Ярмарка','Fair')", 'Fair is not routed to hkRunner'),
    ("hkRunner.stop('fair')", 'Fair Stop is not routed to hkRunner'),
    ("await hkRunner.waitIfPaused();", 'Pause checkpoints missing'),
    ("await gameRetryDelay(Math.max(700, settings.interval * 1000));", 'Pit delay is not abort-aware'),
    ("await gameRetryDelay(550);", 'Fair delay is not abort-aware'),
]
for needle, message in checks:
    require(needle, message)

# No Stage 2 migration may reintroduce the obsolete Hamster budget paths.
if 'hk-growth-nuts-percent' in s or 'growthNutCost' in s:
    raise SystemExit('obsolete Hamster Nuts budget path reintroduced')

TARGET.write_text(s, encoding='utf-8')
