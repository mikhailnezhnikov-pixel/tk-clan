from pathlib import Path

PATH = Path("/tmp/HamsterKingMobile.user.js")
s = PATH.read_text(encoding="utf-8")

required = [
    "// @version      1.17.13",
    "const BUILD_VERSION = '1.17.13';",
    "const HK_CORE_REVISION = 'core-20260921-r15-late-login-handoff';",
    "const HK_BUILDINGS_CANON_REV = 'buildings-canon-core-20260920-r1';",
    "function renderBuildings()",
    "maps-shared-runtime-20260921-r7-safe5",
    "explore-e3-single-20260920-r9-runner",
    "const HK_MAP_READ_CONCURRENCY = 5;",
]
for marker in required:
    if marker not in s:
        raise SystemExit(f"missing expected marker: {marker}")

s = s.replace("// @version      1.17.13", "// @version      1.17.14", 1)
s = s.replace(
    "// @release-note Исправлено подключение HK, если игра уже успела авторизоваться до запуска панели.",
    "// @release-note Приведён в порядок экран «Здания»: компактные фильтры, план и списки без ломающихся ID.\n"
    "// @release-note Исправлено подключение HK, если игра уже успела авторизоваться до запуска панели.",
    1,
)
s = s.replace("const BUILD_VERSION = '1.17.13';", "const BUILD_VERSION = '1.17.14';", 1)
s = s.replace(
    "const HK_CORE_REVISION = 'core-20260921-r15-late-login-handoff';",
    "const HK_CORE_REVISION = 'core-20260921-r16-buildings-ui';",
    1,
)
s = s.replace(
    "const HK_BUILDINGS_CANON_REV = 'buildings-canon-core-20260920-r1';",
    "const HK_BUILDINGS_CANON_REV = 'buildings-canon-core-20260920-r1';\n"
    "  const HK_BUILDINGS_UI_REV = 'buildings-ui-20260921-r2';",
    1,
)

css_anchor = """      #hk-business-lists{display:grid;grid-template-columns:1fr;gap:12px}h3{font-size:16px;margin:8px 0}.hk-cards{display:grid;gap:8px}.hk-card{display:flex;align-items:center;gap:10px;background:#151d29;border:1px solid #2a374a;border-radius:14px;padding:9px}"""
css_replacement = """      .hk-buildings-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:10px}.hk-buildings-head>div{min-width:0}.hk-buildings-head h3{margin:0}.hk-buildings-head small{display:block;margin-top:3px;color:#94a3b8}.hk-buildings-head .hk-secondary{width:auto;min-width:112px;margin:0;padding:10px 16px;flex:0 0 auto}
      .hk-building-settings{padding:12px}.hk-building-controls{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.hk-building-field{display:grid;gap:5px;min-width:0}.hk-building-field span{font-size:11px;color:#9eabc0}.hk-building-field input,.hk-building-field select{width:100%;min-width:0;box-sizing:border-box;background:#0b111b;color:#fff;border:1px solid #3b4a61;border-radius:10px;padding:10px}
      .hk-building-actions{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}.hk-building-actions button{margin:0}
      .hk-building-plan{margin-bottom:12px}.hk-building-plan-head,.hk-building-section-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:9px}.hk-building-plan-head b,.hk-building-section-head b{font-size:13px}.hk-building-section-head span{font-size:11px;color:#9eabc0}
      .hk-building-stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px;margin-bottom:9px}.hk-building-stat{padding:8px 9px;border:1px solid #2b3a50;border-radius:10px;background:#101927;min-width:0}.hk-building-stat span{display:block;font-size:10px;color:#8fa0b8}.hk-building-stat b{display:block;margin-top:2px;font-size:14px;color:#e7edf7;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
      .hk-buildings-list{display:grid;gap:6px}.hk-building-row,.hk-building-candidate-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:10px;align-items:center;padding:9px 10px;border:1px solid #2a374a;border-radius:11px;background:#111925;min-width:0}.hk-building-row .hk-business-info,.hk-building-candidate-row .hk-business-info{min-width:0}.hk-building-id{display:block;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font:700 12px ui-monospace,SFMono-Regular,Consolas,monospace;color:#e9eef7}.hk-building-meta{display:flex;gap:6px;flex-wrap:wrap;margin-top:5px}.hk-building-meta span{display:inline-flex;align-items:center;min-height:20px;padding:2px 7px;border-radius:999px;background:#202c3d;color:#b8c5d7;font-size:10px;white-space:nowrap}.hk-building-meta .crystal{color:#7dd3fc}.hk-building-meta .invest{color:#ffd166}.hk-building-area{max-width:210px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#8fa0b8;font:11px ui-monospace,SFMono-Regular,Consolas,monospace}.hk-building-read{width:auto!important;min-width:86px;margin:0!important;padding:9px 14px!important}
      .hk-building-empty{padding:12px;border:1px dashed #34445b;border-radius:11px;color:#8fa0b8;text-align:center}.hk-building-more{margin:8px 0 0;color:#8fa0b8;font-size:11px}
      @media(max-width:760px){.hk-building-controls{grid-template-columns:1fr}.hk-building-stats{grid-template-columns:1fr 1fr}.hk-building-actions{grid-template-columns:1fr}.hk-buildings-head{align-items:flex-start}.hk-buildings-head .hk-secondary{min-width:96px}.hk-building-area{max-width:120px}}
      @media(max-width:460px){.hk-buildings-head{display:grid;grid-template-columns:1fr auto}.hk-buildings-head small{grid-column:1/3}.hk-building-stats{grid-template-columns:1fr}.hk-building-row,.hk-building-candidate-row{grid-template-columns:minmax(0,1fr) auto}.hk-building-read{min-width:72px;padding:8px 10px!important}.hk-building-area{display:none}}
      #hk-business-lists{display:grid;grid-template-columns:1fr;gap:12px}h3{font-size:16px;margin:8px 0}.hk-cards{display:grid;gap:8px}.hk-card{display:flex;align-items:center;gap:10px;background:#151d29;border:1px solid #2a374a;border-radius:14px;padding:9px}"""
if css_anchor not in s:
    raise SystemExit("CSS anchor not found")
s = s.replace(css_anchor, css_replacement, 1)

start = s.index("  function renderBuildings() {")
end = s.index("\n\n  async function refreshBuildings", start)
old_render = s[start:end]
new_render = r"""  function renderBuildings() {
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
    const candidateRows=(plan?.candidates||[]).slice(0,12).map(row=>{
      const id=String(row.buildingId||'');
      const area=String(row.areaId||'');
      return '<div class="hk-building-candidate-row"><div class="hk-business-info"><b class="hk-building-id" title="'+escapeHtml(id)+'">'+escapeHtml(id)+'</b><div class="hk-building-meta">'+
        '<span class="crystal">💎 '+Number(row.crystals).toLocaleString(locale())+'</span>'+
        '<span class="'+(row.isInvest?'invest':'')+'">'+(row.isInvest?either('◆ Инвест','◆ Investment'):either('Обычное','Normal'))+'</span>'+
        '</div></div><span class="hk-building-area" title="'+escapeHtml(area)+'">'+escapeHtml(area)+'</span></div>';
    }).join('');

    const activeValue=capacity.active+(capacity.max===null?'':'/'+capacity.max);
    const planSummary=plan?
      '<div class="hk-cardbox hk-building-plan">'+
        '<div class="hk-building-plan-head"><b>'+either('План открытия','Opening plan')+'</b><span class="hk-muted">'+new Date(plan.at||Date.now()).toLocaleTimeString(locale(),{hour:'2-digit',minute:'2-digit'})+'</span></div>'+
        '<div class="hk-building-stats">'+
          '<div class="hk-building-stat"><span>'+either('Кандидаты','Candidates')+'</span><b>'+plan.candidates.length+'</b></div>'+
          '<div class="hk-building-stat"><span>'+either('Активные','Active')+'</span><b>'+activeValue+'</b></div>'+
          '<div class="hk-building-stat"><span>'+either('Карты районов','Mapped districts')+'</span><b>'+plan.mappedAreas+'/'+plan.ownedAreas+'</b></div>'+
        '</div>'+
        (plan.unknownMetric?'<p class="hk-muted">'+either('Без данных о кристальных комнатах','Unknown crystal-room count')+': '+plan.unknownMetric+'</p>':'')+
        '<div class="hk-buildings-list">'+(candidateRows||'<div class="hk-building-empty">'+either('Подходящих кандидатов нет','No eligible candidates')+'</div>')+'</div>'+
        (plan.candidates.length>12?'<p class="hk-building-more">… +'+(plan.candidates.length-12)+' '+either('кандидатов','candidates')+'</p>':'')+
      '</div>':
      '<div class="hk-cardbox hk-building-plan"><div class="hk-building-empty">'+either('Нажмите «Рассчитать кандидатов», чтобы увидеть план открытия.','Press “Calculate candidates” to see the opening plan.')+'</div></div>';

    box.innerHTML=
      '<div class="hk-buildings-head"><div><h3>'+either('Здания','Buildings')+'</h3><small>'+either('Подбор и открытие зданий по известным кристальным комнатам','Select and open buildings by known crystal rooms')+'</small></div><button id="hk-buildings-refresh" class="hk-secondary" '+(buildingCanonBusy?'disabled':'')+'>'+either('Обновить','Refresh')+'</button></div>'+
      '<div class="hk-cardbox hk-building-settings">'+
        '<div class="hk-building-controls">'+
          '<label class="hk-building-field"><span>'+either('Минимум кристаллов','Minimum crystals')+'</span><input id="hk-building-min-crystals" type="number" min="0" step="1" value="'+settings.minCrystals+'"></label>'+
          '<label class="hk-building-field"><span>'+either('В избранное от','Favorite from')+'</span><input id="hk-building-favorite-from" type="number" min="0" step="1" value="'+settings.favoriteFrom+'"></label>'+
          '<label class="hk-building-field"><span>'+either('Тип здания','Building type')+'</span><select id="hk-building-type"><option value="normal" '+(settings.buildingType==='normal'?'selected':'')+'>'+either('Обычные','Normal')+'</option><option value="investment" '+(settings.buildingType==='investment'?'selected':'')+'>'+either('Инвестиционные','Investment')+'</option><option value="all" '+(settings.buildingType==='all'?'selected':'')+'>'+either('Все','All')+'</option></select></label>'+
        '</div>'+
        '<div class="hk-building-actions"><button id="hk-building-plan" class="hk-secondary" '+(buildingCanonBusy?'disabled':'')+'>'+either('Рассчитать кандидатов','Calculate candidates')+'</button><button id="hk-building-run" class="hk-primary" '+(buildingCanonBusy||!plan?.candidates?.length?'disabled':'')+'>'+either('Открыть подходящие','Open eligible')+'</button></div>'+
      '</div>'+
      planSummary+
      '<div class="hk-cardbox"><div class="hk-building-section-head"><b>'+either('Активные здания','Active buildings')+'</b><span>'+rows.length+'</span></div><div class="hk-buildings-list">'+content+'</div></div>';

    const saveControls=()=>{buildingCanonSaveSettings(buildingCanonReadSettingsFromDom());buildingCanonPlan=null;renderBuildings();};
    box.querySelector('#hk-buildings-refresh')?.addEventListener('click',()=>void refreshBuildings(true));
    box.querySelector('#hk-building-plan')?.addEventListener('click',()=>{buildingCanonSaveSettings(buildingCanonReadSettingsFromDom());buildingCanonPlan=null;void buildingCanonPreparePlan(true);});
    box.querySelector('#hk-building-run')?.addEventListener('click',()=>void runBuildingsCanonical());
    box.querySelector('#hk-building-min-crystals')?.addEventListener('change',saveControls);
    box.querySelector('#hk-building-favorite-from')?.addEventListener('change',saveControls);
    box.querySelector('#hk-building-type')?.addEventListener('change',saveControls);
    box.querySelectorAll('[data-building-read]').forEach(button=>button.addEventListener('click',()=>void readBuildingStudy(button.dataset.buildingRead)));
  }"""
s = s[:start] + new_render + s[end:]

for marker in [
    "// @version      1.17.14",
    "const BUILD_VERSION = '1.17.14';",
    "core-20260921-r16-buildings-ui",
    "buildings-ui-20260921-r2",
    "class=\"hk-buildings-head\"",
    "class=\"hk-building-row\"",
    "class=\"hk-building-id\"",
    "class=\"hk-building-actions\"",
    "maps-shared-runtime-20260921-r7-safe5",
    "explore-e3-single-20260920-r9-runner",
    "const HK_MAP_READ_CONCURRENCY = 5;",
]:
    if marker not in s:
        raise SystemExit(f"post-patch marker missing: {marker}")

# Canonical Buildings action logic must be byte-identical after render-only patch.
def block(text, a, b):
    i=text.index(a)
    j=text.index(b,i)
    return text[i:j]

old_action = block(PATH.read_text(encoding="utf-8"), "  async function runBuildingsCanonical() {", "\n  function accountBuildingRows()")
new_action = block(s, "  async function runBuildingsCanonical() {", "\n  function accountBuildingRows()")
if old_action != new_action:
    raise SystemExit("Buildings action logic changed unexpectedly")

PATH.write_text(s, encoding="utf-8")
print("BUILDINGS_UI_R2_PATCH=PASS")
