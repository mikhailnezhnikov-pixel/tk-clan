from pathlib import Path

PATH = Path("/tmp/HamsterKingMobile.user.js")
s = PATH.read_text(encoding="utf-8")
original = s

required = [
    "// @version      1.17.14",
    "const BUILD_VERSION = '1.17.14';",
    "const HK_CORE_REVISION = 'core-20260921-r16-buildings-ui';",
    "const HK_BUILDINGS_UI_REV = 'buildings-ui-20260921-r2';",
    "function renderBuildings()",
    "async function runBuildingsCanonical()",
]
for marker in required:
    if marker not in s:
        raise SystemExit(f"missing expected marker: {marker}")

s = s.replace("// @version      1.17.14", "// @version      1.17.15", 1)
s = s.replace(
    "// @release-note Приведён в порядок экран «Здания»: компактные фильтры, план и списки без ломающихся ID.",
    "// @release-note На экране «Здания» убран лишний перечень всех активных зданий; оставлен только счётчик.\n"
    "// @release-note Приведён в порядок экран «Здания»: компактные фильтры и план без ломающихся ID.",
    1,
)
s = s.replace("const BUILD_VERSION = '1.17.14';", "const BUILD_VERSION = '1.17.15';", 1)
s = s.replace(
    "const HK_CORE_REVISION = 'core-20260921-r16-buildings-ui';",
    "const HK_CORE_REVISION = 'core-20260921-r17-buildings-ui-compact';",
    1,
)
s = s.replace(
    "const HK_BUILDINGS_UI_REV = 'buildings-ui-20260921-r2';",
    "const HK_BUILDINGS_UI_REV = 'buildings-ui-20260921-r3';",
    1,
)

start = s.index("  function renderBuildings() {")
end = s.index("\n\n  async function refreshBuildings", start)
old_render = s[start:end]

# Remove active-building row generation entirely.
old_head = """  function renderBuildings() {
    const box=root?.querySelector('#hk-buildings-content');
    if(!box)return;
    const rows=accountBuildingRows(),settings=buildingCanonSettings(),plan=buildingCanonPlan;
    const content=rows.length?rows.map(row=>{
      const crystal=row.crystalRooms==null?'?':Number(row.crystalRooms).toLocaleString(locale());
      const id=String(row.id||'');
      return '<div class="hk-building-row"><div class="hk-business-info"><b class="hk-building-id" title="'+escapeHtml(id)+'">'+escapeHtml(id)+'</b><div class="hk-building-meta">'+
        '<span>'+either('Тир','Tier')+' '+Number(row.tier)+'</span>'+
        '<span>'+either('Ур.','Lvl')+' '+Number(row.level)+'</span>'+
        '<span>'+either('Комнат','Rooms')+' '+Number(row.roomCount)+'</span>'+
        '<span class="crystal">💎 '+crystal+'</span>'+
        '</div></div><button class="hk-secondary hk-building-read" data-building-read="'+escapeHtml(id)+'" '+(buildingCanonBusy?'disabled':'')+'>'+either('Считать','Read')+'</button></div>';
    }).join(''):'<div class="hk-building-empty">'+either('Активные здания пока не считаны.','Active buildings have not been read yet.')+'</div>';

    const capacity=plan?.capacity||buildingCanonCapacity(playerDocument);
"""
new_head = """  function renderBuildings() {
    const box=root?.querySelector('#hk-buildings-content');
    if(!box)return;
    const settings=buildingCanonSettings(),plan=buildingCanonPlan;
    const capacity=plan?.capacity||buildingCanonCapacity(playerDocument);
"""
if old_head not in s:
    raise SystemExit("active buildings render block not found")
s = s.replace(old_head, new_head, 1)

old_tail = """      '</div>'+
      planSummary+
      '<div class="hk-cardbox"><div class="hk-building-section-head"><b>'+either('Активные здания','Active buildings')+'</b><span>'+rows.length+'</span></div><div class="hk-buildings-list">'+content+'</div></div>';

    const saveControls=()=>{buildingCanonSaveSettings(buildingCanonReadSettingsFromDom());buildingCanonPlan=null;renderBuildings();};
"""
new_tail = """      '</div>'+
      planSummary;

    const saveControls=()=>{buildingCanonSaveSettings(buildingCanonReadSettingsFromDom());buildingCanonPlan=null;renderBuildings();};
"""
if old_tail not in s:
    raise SystemExit("active buildings section tail not found")
s = s.replace(old_tail, new_tail, 1)

read_handler = "    box.querySelectorAll('[data-building-read]').forEach(button=>button.addEventListener('click',()=>void readBuildingStudy(button.dataset.buildingRead)));\n"
if read_handler not in s:
    raise SystemExit("active building read handler not found")
s = s.replace(read_handler, "", 1)

# No active-building read buttons should remain in renderBuildings.
render = s[s.index("  function renderBuildings() {"):s.index("\n\n  async function refreshBuildings", s.index("  function renderBuildings() {"))]
for forbidden in ["data-building-read", "Активные здания", "Active buildings", "const rows=accountBuildingRows()", "const content=rows.length"]:
    if forbidden in render:
        raise SystemExit(f"active list residue remains: {forbidden}")

# Keep the active count in the plan.
if "either('Активные','Active')" not in render or "activeValue" not in render:
    raise SystemExit("active count was removed unexpectedly")

# Canonical action logic must be byte-identical.
def block(text, a, b):
    i=text.index(a)
    j=text.index(b,i)
    return text[i:j]

old_action = block(original, "  async function runBuildingsCanonical() {", "\n  function accountBuildingRows()")
new_action = block(s, "  async function runBuildingsCanonical() {", "\n  function accountBuildingRows()")
if old_action != new_action:
    raise SystemExit("Buildings action logic changed unexpectedly")

for marker in [
    "// @version      1.17.15",
    "const BUILD_VERSION = '1.17.15';",
    "core-20260921-r17-buildings-ui-compact",
    "buildings-ui-20260921-r3",
    "maps-shared-runtime-20260921-r7-safe5",
    "explore-e3-single-20260920-r9-runner",
    "const HK_MAP_READ_CONCURRENCY = 5;",
    "AUTH_PASSIVE_SAFETY_R1",
]:
    if marker not in s:
        raise SystemExit(f"post-patch marker missing: {marker}")

PATH.write_text(s, encoding="utf-8")
print("BUILDINGS_UI_R3_COMPACT_PATCH=PASS")
