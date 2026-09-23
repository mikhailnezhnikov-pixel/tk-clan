from pathlib import Path

PATH = Path("/tmp/HamsterKingMobile.user.js")
s = PATH.read_text(encoding="utf-8")
MARKER = "generals-kokkaras-live-display-20260923-r2"

if MARKER in s:
    print("GENERALS_KOKKARAS_LIVE_DISPLAY_ALREADY_PRESENT")
    raise SystemExit(0)

for required in [
    "// @version      1.17.45",
    "const BUILD_VERSION = '1.17.45';",
    "treasure-guide-pet-skill-selective-20260923-r3",
    "generals-kokkaras-cost-parity-20260923-r1",
    "hamsters-kokkaras-live-state-20260923-r2",
    "hamsters-kokkaras-auth-state-20260923-r3",
]:
    if required not in s:
        raise SystemExit("missing required marker: " + required)

version = "// @version      1.17.45"
note = "// @release-note Generals: отображение прокачки переведено на live-state канон Hamsters; перед показом и запуском проверяются Generals, Орехи и Pit Tokens, а Runner показывает обе части стоимости."
s = s.replace(version, version + "\n" + note, 1)

const_line = "  const HK_GENERALS_KOKKARAS_COST_PARITY_REV = 'generals-kokkaras-cost-parity-20260923-r1';"
s = s.replace(const_line, const_line + "\n  const HK_GENERALS_KOKKARAS_LIVE_DISPLAY_REV = '" + MARKER + "';", 1)

old_state = """  function growthUsableAccountState(state){
    if(!state||typeof state!=='object')return false;
    const hamsters=growthArray('playerHamsters',state);
    const hasWallet=growthContainers(state).some(value=>Array.isArray(value?.currencies));
    return hamsters.length>0&&hasWallet;
  }
  function growthCachedAccountState(){
    for(const state of [growthState,hkStateStore.snapshot,playerDocument])if(growthUsableAccountState(state))return state;
    return null;
  }
"""
new_state = """  function growthUsableAccountState(state,scope='account'){
    if(!state||typeof state!=='object')return false;
    const hamsters=growthArray('playerHamsters',state),generals=growthArray('player_hamster_generals',state),containers=growthContainers(state);
    const hasCurrencies=containers.some(value=>Array.isArray(value?.currencies)),hasItems=containers.some(value=>Array.isArray(value?.items));
    if(scope==='generals')return generals.length>0&&hasCurrencies&&hasItems;
    if(scope==='hamsters')return hamsters.length>0&&hasCurrencies;
    if(scope==='all')return hamsters.length>0&&generals.length>0&&hasCurrencies&&hasItems;
    return (hamsters.length>0||generals.length>0)&&hasCurrencies;
  }
  function growthCachedAccountState(scope='account'){
    for(const state of [growthState,hkStateStore.snapshot,playerDocument])if(growthUsableAccountState(state,scope))return state;
    return null;
  }
"""
if old_state not in s:
    raise SystemExit("old account-state guard missing")
s = s.replace(old_state, new_state, 1)

old = """  async function growthLoadLive({force=false,loadShop=true,loadConfig=false,silent=true}={}){
    if(growthLoadPromise)return growthLoadPromise;
    const cached=growthCachedAccountState();
"""
new = """  async function growthLoadLive({force=false,loadShop=true,loadConfig=false,silent=true,scope='account'}={}){
    if(growthLoadPromise)return growthLoadPromise;
    const cached=growthCachedAccountState(scope);
"""
if old not in s:
    raise SystemExit("growthLoadLive signature missing")
s = s.replace(old, new, 1)

old = "recordDiagnostic('growth-live-cache-hit',{storeUpdatedAt:Number(hkStateStore.updatedAt||0),lastLoadedAt:growthLastLoadedAt});"
new = "recordDiagnostic('growth-live-cache-hit',{scope,storeUpdatedAt:Number(hkStateStore.updatedAt||0),lastLoadedAt:growthLastLoadedAt});"
if old not in s:
    raise SystemExit("cache diagnostic missing")
s = s.replace(old, new, 1)

old = """  function growthAutoOpen(page){
    const settings=growthSettings();
    const needsConfig=page==='growth-hamsters'&&settings.excludeCurrentEventHamsters;
    void growthLoadLive({force:false,loadShop:true,loadConfig:needsConfig,silent:true});
  }
"""
new = """  function growthAutoOpen(page){
    const settings=growthSettings();
    const needsConfig=page==='growth-hamsters'&&settings.excludeCurrentEventHamsters;
    const scope=page==='growth-generals'?'generals':page==='growth-hamsters'?'hamsters':'account';
    void growthLoadLive({force:false,loadShop:true,loadConfig:needsConfig,silent:true,scope});
  }
"""
if old not in s:
    raise SystemExit("growthAutoOpen missing")
s = s.replace(old, new, 1)

old = "      state=await growthLoadLive({force:false,loadShop:true,loadConfig:settings.excludeCurrentEventHamsters,silent:true});"
new = """      const liveScope=scope==='generals'?'generals':scope==='hamsters'?'hamsters':scope==='all'?'all':'account';
      state=await growthLoadLive({force:false,loadShop:true,loadConfig:settings.excludeCurrentEventHamsters,silent:true,scope:liveScope});"""
if old not in s:
    raise SystemExit("growthRunPlan live load missing")
s = s.replace(old, new, 1)

old = "      if(runGenerals){const generalRows=growthArray('player_hamster_generals',state),generalReady=generalRows.filter(row=>row?.nextLevelUp).length,startPit=growthResource(GROWTH_GENERAL_BUDGET_ID,state),pitLimit=Math.floor(startPit*settings.generalPitPercent/100);"
new = "      if(runGenerals){growthNormalizeDonorState(state,state,{full:false});const generalRows=growthArray('player_hamster_generals',state),generalReady=generalRows.filter(row=>row?.nextLevelUp).length,startPit=growthResource(GROWTH_GENERAL_BUDGET_ID,state),startNuts=growthResource(GROWTH_HAMSTER_BUDGET_ID,state),pitLimit=Math.floor(startPit*settings.generalPitPercent/100);"
if old not in s:
    raise SystemExit("general runner state block missing")
s = s.replace(old, new, 1)

old = " · Pit Tokens: ${startPit.toLocaleString(locale())} · ${either('бюджет','budget')}: ${pitLimit.toLocaleString(locale())}"
new = " · ${either('Орехи','Nuts')}: ${startNuts.toLocaleString(locale())} · Pit Tokens: ${startPit.toLocaleString(locale())} · ${either('Pit-бюджет','Pit budget')}: ${pitLimit.toLocaleString(locale())}"
if old not in s:
    raise SystemExit("general runner note missing")
s = s.replace(old, new, 1)

old = """  async function growthRunGeneralsCore(state,settings){
    const startPit=growthResource(GROWTH_GENERAL_BUDGET_ID,state),limit=Math.floor(startPit*settings.generalPitPercent/100),budget={limit,spent:0},blocked=new Set();let safety=0,noProgress=0;
"""
new = """  async function growthRunGeneralsCore(state,settings){
    growthNormalizeDonorState(state,state,{full:false});
    const startPit=growthResource(GROWTH_GENERAL_BUDGET_ID,state),startNuts=growthResource(GROWTH_HAMSTER_BUDGET_ID,state),limit=Math.floor(startPit*settings.generalPitPercent/100),budget={limit,spent:0},blocked=new Set();let safety=0,noProgress=0;
"""
if old not in s:
    raise SystemExit("general core header missing")
s = s.replace(old, new, 1)

old = "${either('Бюджет Генералов','General budget')}: ${settings.generalPitPercent}% · ${limit.toLocaleString(locale())}/${startPit.toLocaleString(locale())}"
new = "${either('Бюджет Генералов по Pit Tokens','General Pit Token budget')}: ${settings.generalPitPercent}% · ${limit.toLocaleString(locale())}/${startPit.toLocaleString(locale())} · ${either('Орехи','Nuts')}: ${startNuts.toLocaleString(locale())} · ${either('полная цена из live costs','full cost from live costs')}"
if old not in s:
    raise SystemExit("general core log missing")
s = s.replace(old, new, 1)

s = s.replace(
    "Перед каждым запуском баланс и доступные улучшения считываются заново.",
    "Перед каждым запуском заново проверяются Генералы, Орехи, Pit Tokens и доступные live-улучшения.",
    1,
)
s = s.replace(
    "Balance and available upgrades are read again before every run.",
    "Generals, Nuts, Pit Tokens and available live upgrades are revalidated before every run.",
    1,
)
s = s.replace(
    "Доля текущего баланса для Генералов",
    "Лимит задаётся по Pit Tokens; полная цена улучшения берётся из live costs и учитывает Орехи + Pit Tokens",
    1,
)
s = s.replace(
    "Share of current balance for Generals",
    "Limit is based on Pit Tokens; full upgrade cost comes from live costs and includes Nuts + Pit Tokens",
    1,
)

checks = [
    MARKER,
    "function growthUsableAccountState(state,scope='account')",
    "if(scope==='generals')return generals.length>0&&hasCurrencies&&hasItems;",
    "const scope=page==='growth-generals'?'generals'",
    "const liveScope=scope==='generals'?'generals'",
    "startNuts=growthResource(GROWTH_HAMSTER_BUDGET_ID,state)",
    "Pit-бюджет",
    "полная цена из live costs",
    "полная цена улучшения берётся из live costs",
]
for marker in checks:
    if marker not in s:
        raise SystemExit("post patch marker missing: " + marker)

PATH.write_text(s, encoding="utf-8")
print("GENERALS_KOKKARAS_LIVE_DISPLAY_1_17_45=PASS")
