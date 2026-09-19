from pathlib import Path
import importlib.util
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
STAGE2A_PATCH = HERE / 'stage2_runner_patch.py'
STAGE2B_PATCH = HERE / 'stage2b_runner_patch.py'
STAGE2A_FIXTURE = HERE / 'test_stage2_runner_fixture.py'
TARGET = Path('/tmp/HamsterKingMobile.user.js')

spec = importlib.util.spec_from_file_location('stage2a_fixture', STAGE2A_FIXTURE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
FIXTURE = module.FIXTURE

def run(path):
    subprocess.run([sys.executable, str(path)], cwd=ROOT, check=True)

def validate(text):
    required = [
        '// @version      1.16.1',
        "HK_STAGE2_RUNNER_REV = 'stage2a-20260919-r1'",
        "HK_STAGE2B_RUNNER_REV = 'stage2b-20260919-r1'",
        "GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'",
        "GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'",
        "title:either('Магазин','Shop')",
        "title:either('Рецепты','Recipes')",
        "hkRunner.stop('recipes')",
        "title:either('Проектное бюро','Project Bureau')",
        "await gameRetryDelay(550);",
        "await gameRetryDelay(450);",
    ]
    for needle in required:
        if needle not in text:
            raise AssertionError(f'missing: {needle}')
    for needle in [
        "HK_STAGE2B_RUNNER_REV = 'stage2b-20260919-r1'",
        "title:either('Магазин','Shop')",
        "title:either('Рецепты','Recipes')",
        "hkRunner.stop('recipes')",
        "title:either('Проектное бюро','Project Bureau')",
    ]:
        if text.count(needle) != 1:
            raise AssertionError(f'duplicated: {needle}')
    if 'hk-growth-nuts-percent' in text or 'growthNutCost' in text:
        raise AssertionError('obsolete Hamster budget path found')

def main():
    original = TARGET.read_bytes() if TARGET.exists() else None
    try:
        TARGET.write_text(FIXTURE, encoding='utf-8')
        run(STAGE2A_PATCH)

        # Extend the compact Stage 2A fixture with the three current legacy modules.
        text = TARGET.read_text(encoding='utf-8')
        insert_at = text.rfind('})();')
        if insert_at < 0:
            raise AssertionError('fixture wrapper end missing')
        modules = r"""
  let shopRunning=false,shopRows=[],selectedShopSection='ordinary',selectedShopGroup='resources';
  const selectedShopLots=new Set(['lot']),selectedShopCounts=new Map([['lot',1]]);
  const SHOP_UNLIMITED_RUN_MAX=100;
  const budgetDocument=()=>({});
  const isRenovationBatch=()=>false;
  const renovationBatchCount=(row,count)=>count;
  const renovationBatchMultiplier=()=>1;
  const normalizeRegularShop=()=>[];
  const renderShop=()=>{};
  const language='ru';
  const selectedShopRows=[];
  async function buyRegularShop() {
    if (!requireLicense() || shopRunning) return;
    const plan = [{row:{section:'ordinary',group:'resources',lotId:'lot',safe:true,remaining:1,cost:{},name:'Lot'},count:1}];
    if (!plan.length) return;
    const count = 1;
    const budgetSection = 'shop';
    const projectedProblems = [];
    if (projectedProblems.length) return;
    const crystalCost = 0;
    if (!confirm('buy')) return;
    shopRunning = true; renderShop();
    let completed = 0;
    try {
      playerDocument = await apiJson('/player/me', 'POST');
      for (const {row, count:rowCount} of plan) {
        const requestCount = 1;
        const before = new Map();
        const requestBody = {shop_lot_id:row.lotId};
        let purchasedRow = 0;
        try {
          for (let index = 0; index < requestCount; index += 1) {
            playerDocument = await apiJson('/shop/buy', 'POST', requestBody, true, 0);
            purchasedRow += 1;
            completed += 1;
          }
        } finally {}
      }
      selectedShopLots.clear();
      selectedShopCounts.clear();
      log('done','ok');
    } catch (error) {
      log('shop: ' + error.message, 'bad');
    } finally {
      shopRunning = false;
      shopRows = normalizeRegularShop();
      renderShop();
    }
  }
  function dailyLabel(){}

  let recipeRunning=false,recipeStop=false,recipeFairId='recipe',currentRecipePlans=[];
  const recipeState=()=>({fair_reroll_cost:{}});
  const safeReroll=()=>true;
  const tr=x=>x;
  const clean=x=>x;
  const plansFromRecipeState=()=>[];
  const submitRecipePlans=async()=>{};
  const renderRecipes=()=>{};
  async function runRecipes() {
    if (!requireLicense() || recipeRunning || !recipeState()) return;
    const attempts = 1;
    let state = recipeState();
    if (!safeReroll(state.fair_reroll_cost, false)) return;
    if (!confirm('recipes')) return;
    recipeRunning = true; recipeStop = false; renderRecipes();
    let completed = 0;
    try {
      try { await submitRecipePlans(plansFromRecipeState(state)); } catch (_) {}
      for (let index = 0; index < attempts && !recipeStop; index++) {
        fairDocument = await apiJson('/fair/reroll', 'POST', {fair_id:recipeFairId});
        state = recipeState(fairDocument);
        currentRecipePlans = plansFromRecipeState(state);
        completed++;
        try { await submitRecipePlans(currentRecipePlans); }
        catch (error) { log('db: ' + error.message, 'warn'); }
        renderRecipes();
        await sleep(550);
      }
      log('recipes done','ok');
    } catch (error) { log('recipes: ' + error.message, 'bad'); }
    finally { recipeRunning = false; recipeStop = false; renderRecipes(); }
  }
  async function loadCommunityRecipes(){}

  let bureauRunning=false,bureauSize=2,bureauInventory=[{businessId:'x',quantity:2}];
  const selectedBureauInputs=new Map([['x',2]]);
  const renderProjectBureau=()=>{};
  const normalizeInventory=()=>[];
  async function runProjectBureau() {
    if (!requireLicense() || bureauRunning) return;
    const inputs = ['x','x'];
    if (inputs.length !== bureauSize) return;
    const attempts = 1;
    const available = new Map([['x',2]]);
    if (!confirm('bureau')) return;
    bureauRunning = true; renderProjectBureau();
    let completed = 0;
    try {
      for (let index = 0; index < attempts; index++) {
        playerDocument = await apiJson('/player/business/recipe/craft', 'POST', {businesses:inputs});
        completed++;
        await sleep(450);
      }
      playerDocument = await apiJson('/player/me', 'POST');
      bureauInventory = normalizeInventory(playerDocument);
      selectedBureauInputs.clear();
      log('bureau done','ok');
    } catch (error) { log('bureau: ' + error.message, 'bad'); }
    finally { bureauRunning = false; renderProjectBureau(); }
  }
  function refreshBusinessData(){}

"""
        text = text[:insert_at] + modules + text[insert_at:]
        text = text.replace(
            "    root.querySelector('#hk-fair-start').onclick = runFair;",
            "    root.querySelector('#hk-fair-start').onclick = runFair;\n"
            "    root.querySelector('#hk-recipe-stop').onclick = () => { recipeStop = true; log(either('Останавливаю после текущей прокрутки…', 'Stopping after the current reroll…'), 'warn'); };"
        )
        TARGET.write_text(text, encoding='utf-8')

        run(STAGE2B_PATCH)
        first = TARGET.read_text(encoding='utf-8')
        validate(first)
        subprocess.run(['node', '--check', str(TARGET)], check=True)

        run(STAGE2B_PATCH)
        second = TARGET.read_text(encoding='utf-8')
        validate(second)
        subprocess.run(['node', '--check', str(TARGET)], check=True)
        if first != second:
            raise AssertionError('Stage 2B patch is not byte-idempotent')
        print('STAGE2B_RUNNER_FIXTURE_TEST_OK')
    finally:
        if original is None:
            TARGET.unlink(missing_ok=True)
        else:
            TARGET.write_bytes(original)

if __name__ == '__main__':
    main()
