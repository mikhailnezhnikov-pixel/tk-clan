from pathlib import Path

TARGET=Path('/tmp/HamsterKingMobile.user.js')
s=TARGET.read_text(encoding='utf-8')
REV='stage3e-resources-verify-20260920-r1'

def require(needle,message):
    if needle not in s:
        raise SystemExit(message)

if '// @version      1.16.12' not in s and '// @version      1.16.13' not in s:
    raise SystemExit('Stage 3E requires Stage 3D 1.16.12 or existing 1.16.13')
require("HK_STAGE3D_RECIPES_BUREAU_REV = 'stage3d-recipes-bureau-verify-20260920-r1'",'Stage 3D marker missing')

if f"HK_STAGE3E_RESOURCES_REV = '{REV}'" not in s:
    s=s.replace('// @version      1.16.12','// @version      1.16.13',1)
    s=s.replace(": '1.16.12';",": '1.16.13';",1)
    marker="  const HK_STAGE3D_RECIPES_BUREAU_REV = 'stage3d-recipes-bureau-verify-20260920-r1';"
    require(marker,'Stage 3D marker anchor missing')
    s=s.replace(marker,marker+f"\n  const HK_STAGE3E_RESOURCES_REV = '{REV}';",1)
    runtime='  runtime.recipesBureauVerificationStage = HK_STAGE3D_RECIPES_BUREAU_REV;'
    require(runtime,'Stage 3D runtime anchor missing')
    s=s.replace(runtime,runtime+"\n  runtime.resourcesVerificationStage = HK_STAGE3E_RESOURCES_REV;",1)

# /player/event performs resource exchanges and must pass through the mutation gate.
old="    '/clan/skill_lines/stats',\n    '/player/event'"
new="    '/clan/skill_lines/stats'"
if old in s:
    s=s.replace(old,new,1)
elif "    '/player/event'" in s:
    raise SystemExit('/player/event is still classified read-only')

# Always rebuild the selected resource rows from a fresh building document before confirmation.
old="""  async function runResourceEvents(rows) {
    const totalCompletions = 1000 * resourceRepeatCount;
    const maximumMode = resourceMaximumMode;
    const ready = (rows || []).filter(row => row?.atMax && row?.affordable > 0 && !resourceEventIsExcluded(row)).map(row => {"""
new="""  async function runResourceEvents(rows) {
    if (!requireLicense() || resourceBusy) return;
    const wanted = (rows || []).map(row => ({buildingId:String(row?.buildingId || ''), roomId:String(row?.roomId || ''), sideEventId:String(row?.sideEventId || ''), eventId:String(row?.eventId || '')}));
    if (!wanted.length) return;
    const refreshed = await loadResources(false);
    if (!refreshed) return;
    const freshEvents = allResourceEvents();
    const sourceRows = wanted.map(key => freshEvents.find(row => String(row?.buildingId || '') === key.buildingId && String(row?.roomId || '') === key.roomId && String(row?.sideEventId || '') === key.sideEventId && String(row?.eventId || '') === key.eventId)).filter(Boolean);
    const totalCompletions = 1000 * resourceRepeatCount;
    const maximumMode = resourceMaximumMode;
    const ready = sourceRows.filter(row => row?.atMax && row?.affordable > 0 && !resourceEventIsExcluded(row)).map(row => {"""
if old in s:
    s=s.replace(old,new,1)
elif "const freshEvents = allResourceEvents();" not in s:
    raise SystemExit('Resources fresh-row preflight anchor missing')

# The old duplicate guard is now handled before the refresh above.
old="    if (!requireLicense() || resourceBusy || !ready.length) return;"
new="    if (!ready.length) return;"
if old in s:
    s=s.replace(old,new,1)
elif new not in s:
    raise SystemExit('Resources ready guard anchor missing')

# Fail before confirmation if the current spend already violates reserve/limits.
old="    const lines = ready.map((row,index) => `${index + 1}. ${row.buildingName} — ${row.name} ×${row.plannedCompletions}`);"
new="""    const projectedProblems = ready.flatMap(row => budgetDecision(row.cost, 'resources', row.plannedCompletions, playerDocument).problems);
    if (projectedProblems.length) {
      alert(`${either('Ресурсный обмен заблокирован единым бюджетом','Resource exchange blocked by unified budget')}:\n\n${[...new Set(projectedProblems)].join('\n')}`);
      return;
    }
    const lines = ready.map((row,index) => `${index + 1}. ${row.buildingName} — ${row.name} ×${row.plannedCompletions}`);"""
if old in s:
    s=s.replace(old,new,1)
elif "Resource exchange blocked by unified budget" not in s:
    raise SystemExit('Resources projected budget anchor missing')

# Every irreversible exchange is non-retriable, budget-checked and journalled.
old="""        const request = numberOfCompletions => apiJson('/player/event','POST',{
          event_building_id:row.roomId,
          tier:row.tier,
          side_event_id:row.sideEventId || undefined,
          number_of_completions:numberOfCompletions
        });"""
new="""        const request = async numberOfCompletions => {
          const quantity = Math.max(1, Math.trunc(Number(numberOfCompletions || 0)));
          const decision = budgetDecision(row.cost, 'resources', quantity, playerDocument);
          if (!decision.allowed) throw new Error(decision.problems.join('; '));
          const before = new Map(costParts(row.cost).map(part => [part.id, walletAmount(part.id, playerDocument)]));
          const value = await apiJson('/player/event','POST',{
            event_building_id:row.roomId,
            tier:row.tier,
            side_event_id:row.sideEventId || undefined,
            number_of_completions:quantity
          },true,0);
          for (const part of costParts(row.cost)) appendExpense({section:'resources', lotId:`resource:${row.buildingId}:${row.roomId}:${row.sideEventId || row.eventId}`, name:row.name || either('Ресурсный обмен','Resource exchange'), currencyId:part.id, amount:part.quantity * quantity, balanceBefore:before.get(part.id), balanceAfter:walletAmount(part.id, playerDocument), status:'ok', result:`completed ${quantity}`});
          return value;
        };"""
if old in s:
    s=s.replace(old,new,1)
elif "const value = await apiJson('/player/event','POST'" not in s:
    raise SystemExit('Resources safe request anchor missing')

checks=[
    ('// @version      1.16.13','version missing'),
    (f"HK_STAGE3E_RESOURCES_REV = '{REV}'",'marker missing'),
    ("const freshEvents = allResourceEvents();",'fresh resource data missing'),
    ("budgetDecision(row.cost, 'resources'",'resource budget checks missing'),
    ("apiJson('/player/event','POST'",'resource action missing'),
    ('},true,0);','resource mutation network retries not disabled'),
    ("appendExpense({section:'resources'",'resource expense journal missing'),
    ("GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'",'Hamster Caps invariant lost'),
    ("GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'",'General Pit Token invariant lost'),
]
for needle,message in checks:
    require(needle,message)
if "    '/player/event'" in s:
    raise SystemExit('/player/event remained in read-only POST paths')

TARGET.write_text(s,encoding='utf-8')
