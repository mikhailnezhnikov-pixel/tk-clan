from pathlib import Path
import re

TARGET = Path('/tmp/HamsterKingMobile.user.js')
s = TARGET.read_text(encoding='utf-8')

STAGE2A_REV = 'stage2a-20260919-r1'
STAGE2B_REV = 'stage2b-20260919-r1'

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

is_stage2a = '// @version      1.16.0' in s and f"HK_STAGE2_RUNNER_REV = '{STAGE2A_REV}'" in s
is_stage2b = '// @version      1.16.1' in s and f"HK_STAGE2B_RUNNER_REV = '{STAGE2B_REV}'" in s
if not (is_stage2a or is_stage2b):
    raise SystemExit('Stage 2B requires Stage 2A 1.16.0/r1 or the same Stage 2B revision')

require("GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'", 'Hamster budget is not Caps')
require("GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'", 'General budget is not Pit Tokens')
require("hkRunner.stop('pit')", 'Stage 2A Pit migration missing')
require("hkRunner.stop('fair')", 'Stage 2A Fair migration missing')
require('async function gameRetryDelay', 'abort-aware delay helper missing')

if is_stage2a:
    s = s.replace('// @version      1.16.0', '// @version      1.16.1', 1)
    s = s.replace(": '1.16.0';", ": '1.16.1';", 1)

stage2a_anchor = f"  const HK_STAGE2_RUNNER_REV = '{STAGE2A_REV}';"
require(stage2a_anchor, 'Stage 2A revision anchor missing')
if f"  const HK_STAGE2B_RUNNER_REV = '{STAGE2B_REV}';" not in s:
    s = s.replace(stage2a_anchor, stage2a_anchor + f"\n  const HK_STAGE2B_RUNNER_REV = '{STAGE2B_REV}';", 1)
    runtime_anchor = '  runtime.legacyRunnerStage = HK_STAGE2_RUNNER_REV;'
    require(runtime_anchor, 'Stage 2A runtime registration missing')
    s = s.replace(runtime_anchor, runtime_anchor + "\n  runtime.legacyRunnerStageB = HK_STAGE2B_RUNNER_REV;", 1)

# Shop
shop_start, shop_end, shop = function_slice(s, '  async function buyRegularShop() {', '  function dailyLabel(')
if "title:either('Магазин','Shop')" not in shop:
    shop = shop.replace(
        '    shopRunning = true; renderShop();',
        "    if (hkRunner.running) { alert(either('Сначала завершите текущую задачу','Finish the current task first')); return; }\n"
        "    hkRunner.start({title:either('Магазин','Shop'),total:count,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});\n"
        '    shopRunning = true; renderShop();',
        1,
    )
    shop = shop.replace(
        '      for (const {row, count:rowCount} of plan) {',
        "      for (const {row, count:rowCount} of plan) {\n"
        "        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');\n"
        "        await hkRunner.waitIfPaused();\n"
        "        hkRunner.setStep(either('Покупка товаров','Buying items'), completed, count);",
        1,
    )
    purchase_pattern = re.compile(r"(?m)^(\s*)playerDocument = await apiJson\('/shop/buy',")
    def add_purchase_checkpoint(match):
        indent = match.group(1)
        return (
            indent + "if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');\n" +
            indent + "await hkRunner.waitIfPaused();\n" +
            indent + "hkRunner.setStep(either('Покупка товаров','Buying items'), completed, count);\n" +
            indent + "playerDocument = await apiJson('/shop/buy',"
        )
    shop, purchase_count = purchase_pattern.subn(add_purchase_checkpoint, shop)
    if purchase_count < 1:
        raise SystemExit('Shop purchase calls not found')
    success_marker = "      selectedShopLots.clear();\n      selectedShopCounts.clear();"
    if success_marker not in shop:
        raise SystemExit('Shop success marker missing')
    shop = shop.replace(success_marker, "      hkRunner.finish(either('Покупки завершены','Purchases completed'));\n" + success_marker, 1)
    catch_pattern = re.compile(r"    \} catch \(error\) \{\n      log\([^\n]+\);\n    \} finally \{")
    shop, catch_count = catch_pattern.subn(
        "    } catch (error) {\n"
        "      if (error?.name === 'AbortError') { hkRunner.reset(); log(either('Магазин остановлен','Shop stopped'),'warn'); }\n"
        "      else { hkRunner.fail(error); log(either('Остановка магазина','Shop stopped') + ': ' + (error?.message || error), 'bad'); }\n"
        "    } finally {",
        shop,
        count=1,
    )
    if catch_count != 1:
        raise SystemExit('Shop catch/finally block not found')
s = s[:shop_start] + shop + s[shop_end:]

# Recipes
recipe_start, recipe_end, recipe = function_slice(s, '  async function runRecipes() {', '  async function loadCommunityRecipes(')
if "title:either('Рецепты','Recipes')" not in recipe:
    recipe = recipe.replace(
        '    recipeRunning = true; recipeStop = false; renderRecipes();',
        "    if (hkRunner.running) { alert(either('Сначала завершите текущую задачу','Finish the current task first')); return; }\n"
        "    hkRunner.start({title:either('Рецепты','Recipes'),total:attempts,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});\n"
        '    recipeRunning = true; recipeStop = false; renderRecipes();',
        1,
    )
    recipe = recipe.replace(
        '      for (let index = 0; index < attempts && !recipeStop; index++) {',
        "      for (let index = 0; index < attempts && !recipeStop; index++) {\n"
        "        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');\n"
        "        await hkRunner.waitIfPaused();\n"
        "        hkRunner.setStep(either('Прокрутка каталога','Catalog reroll'), completed, attempts);",
        1,
    )
    recipe = recipe.replace('        await sleep(550);', '        await gameRetryDelay(550);')
    outer_catch = '    } catch (error) {'
    if outer_catch not in recipe:
        raise SystemExit('Recipe outer catch missing')
    recipe = recipe.replace(outer_catch, "      hkRunner.finish(either('Прокрутка завершена','Rerolls completed'));\n" + outer_catch, 1)
    catch_pattern = re.compile(r"    \} catch \(error\) \{ log\([^\n]+\); \}\n    finally \{")
    recipe, catch_count = catch_pattern.subn(
        "    } catch (error) {\n"
        "      if (error?.name === 'AbortError') { hkRunner.reset(); log(either('Прокрутка остановлена','Reroll stopped'),'warn'); }\n"
        "      else { hkRunner.fail(error); log(either('Прокрутка остановлена','Reroll stopped') + ': ' + (error?.message || error), 'bad'); }\n"
        "    }\n    finally {",
        recipe,
        count=1,
    )
    if catch_count != 1:
        raise SystemExit('Recipe catch/finally block not found')
s = s[:recipe_start] + recipe + s[recipe_end:]

recipe_stop_old = "    root.querySelector('#hk-recipe-stop').onclick = () => { recipeStop = true; log(either('Останавливаю после текущей прокрутки…', 'Stopping after the current reroll…'), 'warn'); };"
recipe_stop_new = "    root.querySelector('#hk-recipe-stop').onclick = () => { recipeStop = true; hkRunner.stop('recipes'); log(either('Останавливаю прокрутку…', 'Stopping rerolls…'), 'warn'); };"
if recipe_stop_old in s:
    s = s.replace(recipe_stop_old, recipe_stop_new, 1)
elif "hkRunner.stop('recipes')" not in s:
    raise SystemExit('Recipe Stop handler not found')

# Project Bureau
bureau_start, bureau_end, bureau = function_slice(s, '  async function runProjectBureau() {', '  function refreshBusinessData(')
if "title:either('Проектное бюро','Project Bureau')" not in bureau:
    bureau = bureau.replace(
        '    bureauRunning = true; renderProjectBureau();',
        "    if (hkRunner.running) { alert(either('Сначала завершите текущую задачу','Finish the current task first')); return; }\n"
        "    hkRunner.start({title:either('Проектное бюро','Project Bureau'),total:attempts,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});\n"
        '    bureauRunning = true; renderProjectBureau();',
        1,
    )
    bureau = bureau.replace(
        '      for (let index = 0; index < attempts; index++) {',
        "      for (let index = 0; index < attempts; index++) {\n"
        "        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');\n"
        "        await hkRunner.waitIfPaused();\n"
        "        hkRunner.setStep(either('Создание бизнес-плана','Creating business plan'), completed, attempts);",
        1,
    )
    bureau = bureau.replace('        await sleep(450);', '        await gameRetryDelay(450);')
    outer_catch = '    } catch (error) {'
    if outer_catch not in bureau:
        raise SystemExit('Project Bureau outer catch missing')
    bureau = bureau.replace(outer_catch, "      hkRunner.finish(either('Проектное бюро завершено','Project Bureau completed'));\n" + outer_catch, 1)
    catch_pattern = re.compile(r"    \} catch \(error\) \{ log\([^\n]+\); \}\n    finally \{")
    bureau, catch_count = catch_pattern.subn(
        "    } catch (error) {\n"
        "      if (error?.name === 'AbortError') { hkRunner.reset(); log(either('Проектное бюро остановлено','Project Bureau stopped'),'warn'); }\n"
        "      else { hkRunner.fail(error); log(either('Проектное бюро остановлено','Project Bureau stopped') + ': ' + (error?.message || error), 'bad'); }\n"
        "    }\n    finally {",
        bureau,
        count=1,
    )
    if catch_count != 1:
        raise SystemExit('Project Bureau catch/finally block not found')
s = s[:bureau_start] + bureau + s[bureau_end:]

checks = [
    ('// @version      1.16.1', 'Stage 2B version missing'),
    (f"HK_STAGE2B_RUNNER_REV = '{STAGE2B_REV}'", 'Stage 2B revision missing'),
    ("GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'", 'Hamster Caps invariant lost'),
    ("GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'", 'General Pit Token invariant lost'),
    ("title:either('Магазин','Shop')", 'Shop is not routed to hkRunner'),
    ("title:either('Рецепты','Recipes')", 'Recipes are not routed to hkRunner'),
    ("hkRunner.stop('recipes')", 'Recipe Stop is not routed to hkRunner'),
    ("title:either('Проектное бюро','Project Bureau')", 'Project Bureau is not routed to hkRunner'),
    ('await gameRetryDelay(550);', 'Recipe delay is not abort-aware'),
    ('await gameRetryDelay(450);', 'Project Bureau delay is not abort-aware'),
]
for needle, message in checks:
    require(needle, message)

if 'hk-growth-nuts-percent' in s or 'growthNutCost' in s:
    raise SystemExit('obsolete Hamster Nuts budget path reintroduced')

TARGET.write_text(s, encoding='utf-8')
