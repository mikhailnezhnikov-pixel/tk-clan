from pathlib import Path
import sys

target=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=target.read_text(encoding="utf-8")

def need(old,label,count=1):
    actual=s.count(old)
    if actual!=count:
        raise SystemExit(f"{label}: expected {count}, got {actual}")

def rep(old,new,label,count=1):
    global s
    need(old,label,count)
    s=s.replace(old,new,count)

rep(
    "// @version      1.17.90",
    "// @version      1.17.91\n"
    "// @release-note Здания: запуск больше не пересчитывает заново все карты районов перед открытием. Используется уже рассчитанный план, выполняется только свежая проверка аккаунта и свободных слотов; запуск реагирует сразу и показывает подготовку в журнале.",
    "metadata version"
)
rep("const BUILD_VERSION = '1.17.90';","const BUILD_VERSION = '1.17.91';","build version")

anchor="  let buildingCanonPlan = null;\n  let buildingCanonBusy = false;"
rep(
    anchor,
    "  const HK_BUILDINGS_RUN_CACHED_PLAN_REV='buildings-run-cached-plan-20260925-r1';\n"
    "  let buildingCanonPlan = null;\n"
    "  let buildingCanonBusy = false;",
    "buildings cached-plan marker"
)

old_start="""  async function runBuildingsCanonical() {
    if(!requireLicense()||buildingCanonBusy)return;
    if(hkRunner.running){alert(either('Сначала завершите текущую задачу','Finish the current task first'));return;}
    buildingCanonSaveSettings(buildingCanonReadSettingsFromDom());
    buildingCanonBusy=true;renderBuildings();
    let opened=0,favorites=0,errors=0,capacityStopped=false,favoriteEnabled=true;
    const openedIds=[],favoriteIds=[];
    try{
      buildingCanonPlan=await buildingCanonBuildPlan(true);
      const capacity=buildingCanonPlan.capacity;
      const source=buildingCanonPlan.candidates;"""
new_start="""  async function runBuildingsCanonical() {
    if(!requireLicense()){
      log(either('Здания: лицензия не активна.','Buildings: license is not active.'),'warn');
      return;
    }
    if(buildingCanonBusy){
      log(either('Здания: уже выполняется подготовка или открытие.','Buildings: preparation or opening is already running.'),'warn');
      return;
    }
    if(hkRunner.running){alert(either('Сначала завершите текущую задачу','Finish the current task first'));return;}

    const runSettings=buildingCanonReadSettingsFromDom();
    buildingCanonSaveSettings(runSettings);
    log(either('Здания: проверяю рассчитанный план перед запуском…','Buildings: validating the calculated plan before start…'),'info');
    buildingCanonBusy=true;renderBuildings();

    let opened=0,favorites=0,errors=0,capacityStopped=false,favoriteEnabled=true;
    const openedIds=[],favoriteIds=[];
    try{
      const cachedPlan=buildingCanonPlan;
      if(cachedPlan?.candidates?.length){
        playerDocument=await hkAuthoritativePlayerRead('buildings:run-preflight');
        const ownedNow=buildingCanonOwnedIds(playerDocument);
        const filtered=cachedPlan.candidates.filter(row=>!ownedNow.has(String(row?.buildingId||'')));
        buildingCanonPlan={
          ...cachedPlan,
          at:Date.now(),
          settings:{...cachedPlan.settings,...runSettings},
          candidates:filtered,
          capacity:buildingCanonCapacity(playerDocument)
        };
        recordDiagnostic('buildings-run-cached-plan',{
          revision:HK_BUILDINGS_RUN_CACHED_PLAN_REV,
          cached:candidateCount(cachedPlan?.candidates),
          remaining:filtered.length,
          mappedAreas:Number(cachedPlan?.mappedAreas||0)
        });
      }else{
        log(either('Здания: готового плана нет, пересчитываю кандидатов…','Buildings: no prepared plan, recalculating candidates…'),'info');
        buildingCanonPlan=await buildingCanonBuildPlan(true);
      }
      const capacity=buildingCanonPlan.capacity;
      const source=buildingCanonPlan.candidates;"""
# candidateCount doesn't exist. avoid helper by replacing before final.
new_start=new_start.replace("candidateCount(cachedPlan?.candidates)","Array.isArray(cachedPlan?.candidates)?cachedPlan.candidates.length:0")
rep(old_start,new_start,"run buildings cached plan")

# Make buttons explicitly non-submit and make the run click observable/prevent default.
rep(
    '<button id="hk-buildings-refresh" class="hk-secondary" ',
    '<button type="button" id="hk-buildings-refresh" class="hk-secondary" ',
    "buildings refresh button type"
)
rep(
    '<button id="hk-building-plan" class="hk-secondary" ',
    '<button type="button" id="hk-building-plan" class="hk-secondary" ',
    "buildings plan button type"
)
rep(
    '<button id="hk-building-run" class="hk-primary" ',
    '<button type="button" id="hk-building-run" class="hk-primary" ',
    "buildings run button type"
)

rep(
    "    box.querySelector('#hk-building-run')?.addEventListener('click',()=>void runBuildingsCanonical());",
    "    box.querySelector('#hk-building-run')?.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();void runBuildingsCanonical();});",
    "buildings run click handler"
)

for marker in [
    "// @version      1.17.91",
    "const BUILD_VERSION = '1.17.91';",
    "buildings-run-cached-plan-20260925-r1",
    "Здания: проверяю рассчитанный план перед запуском",
    "buildings:run-preflight",
    "recordDiagnostic('buildings-run-cached-plan'",
    'type="button" id="hk-building-run"',
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

if "buildingCanonPlan=await buildingCanonBuildPlan(true);\n      const capacity=buildingCanonPlan.capacity;" in s:
    raise SystemExit("old unconditional full-plan rebuild is still present")

target.write_text(s,encoding="utf-8")
print("BUILDINGS_RUN_CACHED_PLAN_1_17_91=PASS")
print("version=1.17.91")
