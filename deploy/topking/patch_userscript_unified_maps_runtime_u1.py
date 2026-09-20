from pathlib import Path

TARGET=Path("/tmp/HamsterKingMobile.user.js")
s=TARGET.read_text(encoding="utf-8")

def req(x,msg):
    if x not in s:
        raise SystemExit(msg)

s=s.replace(
    "const HK_MAP_SCANNER_REV = 'maps-parallel-read-20260920-r6-safe5';",
    "const HK_MAP_SCANNER_REV = 'maps-shared-runtime-20260921-r7-safe5';\n  const HK_MAP_SHARED_RUNTIME_REV = 'maps-shared-knowledge-20260921-r1';",
    1,
)
s=s.replace(
    "runtime.mapScannerStage = HK_MAP_SCANNER_REV;\n  runtime.mapCoordsStage = HK_MAP_COORDS_REV;",
    "runtime.mapScannerStage = HK_MAP_SCANNER_REV;\n  runtime.mapSharedRuntimeStage = HK_MAP_SHARED_RUNTIME_REV;\n  runtime.mapCoordsStage = HK_MAP_COORDS_REV;",
    1,
)

anchor="  async function mapServerJson(path, body = {}, retry = true) { return licensedServerJson(MAP_API_BASE, path, body, retry, 'maps'); }\n"
req(anchor,"mapServerJson anchor missing")
s=s.replace(anchor,anchor+"""  function mapSharedKnowledgeEnabled() {
    return load().mapUseSharedKnowledge !== false;
  }

""",1)

backfill="  async function mapBackfillActiveBuildingStudies(selectedAreaIds=null) {\n"
req(backfill,"backfill anchor missing")
helper="""  async function mapSharedKnownBuildingRooms(selectedAreaIds=null) {
    const known=new Map();
    if(!mapSharedKnowledgeEnabled())return known;
    const selected=selectedAreaIds instanceof Set?selectedAreaIds:ownedMapIds();
    if(!selected.size)return known;
    try{
      const index=await mapServerJson('/list');
      mapRows=Array.isArray(index?.maps)?index.maps:[];
      const targets=mapRows.filter(row=>{
        const ids=[String(row?.area_id||''),...(Array.isArray(row?.aliases)?row.aliases.map(String):[])];
        return ids.some(id=>selected.has(id));
      });
      let cursor=0;
      const worker=async()=>{
        while(cursor<targets.length){
          const row=targets[cursor++];
          try{
            const result=await mapServerJson('/detail',{area_id:String(row?.area_id||'')});
            for(const building of (result?.detail?.buildings||[])){
              const buildingId=String(building?.building_id||'');
              if(!buildingId||building?.room_count==null)continue;
              known.set(buildingId,{roomCount:Number(building.room_count),source:String(building?.knowledge_source||'shared'),areaId:String(row?.area_id||'')});
            }
          }catch(_){}
        }
      };
      const workers=Math.min(4,Math.max(1,targets.length));
      await Promise.all(Array.from({length:workers},()=>worker()));
    }catch(_){
      log(either('Общая база карт временно недоступна — читаю здания напрямую','Shared map knowledge is temporarily unavailable — reading buildings directly'),'warn');
    }
    return known;
  }

"""
s=s.replace(backfill,helper+backfill,1)

line="    const unique=[...new Map(rows.map(row=>[row.buildingId,row])).values()];"
req(line,"unique rows anchor missing")
s=s.replace(line,line+"""
    const sharedKnown=await mapSharedKnownBuildingRooms(selected);
    const pending=mapSharedKnowledgeEnabled()?unique.filter(row=>!sharedKnown.has(row.buildingId)):unique;
    const sharedKnownCount=unique.length-pending.length;""",1)

s=s.replace(
    "    let studied=0,known=0,failed=0,completed=0,cursor=0;",
    "    let studied=0,known=sharedKnownCount,failed=0,completed=sharedKnownCount,cursor=0;",
    1,
)
s=s.replace(
    "    hkRunner.setStep(either('Считываю открытые здания','Reading active buildings'),baseDone,total);",
    "    hkRunner.setStep(either('Считываю открытые здания','Reading active buildings'),baseDone+completed,total);",
    1,
)
s=s.replace("        if(index>=unique.length)return;","        if(index>=pending.length)return;",1)
s=s.replace("        const {buildingId,areaId}=unique[index];","        const {buildingId,areaId}=pending[index];",1)
s=s.replace(
    "    const workers=Math.min(HK_MAP_READ_CONCURRENCY,Math.max(1,unique.length));\n    await Promise.all(Array.from({length:workers},()=>worker()));",
    "    const workers=pending.length?Math.min(HK_MAP_READ_CONCURRENCY,pending.length):0;\n    if(workers)await Promise.all(Array.from({length:workers},()=>worker()));",
    1,
)
s=s.replace(
    "    return {total:unique.length,studied,known,failed,workers};",
    "    return {total:unique.length,studied,known,sharedKnown:sharedKnownCount,directReads:pending.length,failed,workers};",
    1,
)

payload_tail="      expected_buildings:Math.max(buildings.length, Number(full?.meta?.buildings_total || 0)), buildings};"
req(payload_tail,"mapAreaPayload tail missing")
s=s.replace(
    payload_tail,
    """      expected_buildings:Math.max(buildings.length, Number(full?.meta?.buildings_total || 0)), buildings,
      _website_hydrate:mapSharedKnowledgeEnabled(),
      _website_geometry:mapSharedKnowledgeEnabled()?(full?.geo_json_buildings||null):null};""",
    1,
)

s=s.replace("uploadedMaps:'Загруженные карты'","uploadedMaps:'Общая база'",1)
s=s.replace("refreshUploadedMaps:'Обновить загруженные карты'","refreshUploadedMaps:'Обновить общую базу'",1)
s=s.replace("uploadedMaps:'Uploaded maps'","uploadedMaps:'Shared maps'",1)
s=s.replace("refreshUploadedMaps:'Refresh uploaded maps'","refreshUploadedMaps:'Refresh shared maps'",1)

ui_marker='          <div class="hk-map-controls">'
req(ui_marker,"maps UI marker missing")
ui='''          <label class="hk-map-shared-setting" style="display:flex;align-items:flex-start;gap:10px;margin:10px 0;padding:10px 12px;border:1px solid #2f4058;border-radius:12px;background:#111a27">
            <input id="hk-map-shared-knowledge" type="checkbox" style="margin-top:3px">
            <span><b>Использовать общую базу карт</b><small style="display:block;opacity:.72;margin-top:3px">Подгружать знания сайта и игроков. Уже известные активные здания повторно не считываются.</small></span>
          </label>
'''
s=s.replace(ui_marker,ui+ui_marker,1)

event_anchor="""    root.querySelector('#hk-map-load').onclick = () => loadMapIndex(false);
    root.querySelector('#hk-map-scan').onclick = () => submitOwnedMapAreas(true);
"""
req(event_anchor,"map event anchor missing")
event_new=event_anchor+"""    const mapSharedToggle=root.querySelector('#hk-map-shared-knowledge');
    if(mapSharedToggle){
      mapSharedToggle.checked=mapSharedKnowledgeEnabled();
      mapSharedToggle.onchange=()=>{
        save({mapUseSharedKnowledge:!!mapSharedToggle.checked});
        log(mapSharedToggle.checked?either('Общая база карт включена','Shared map knowledge enabled'):either('Общая база карт отключена — здания будут считываться напрямую','Shared map knowledge disabled — buildings will be read directly'),'ok');
        if(mapSharedToggle.checked)void loadMapIndex(false);
      };
    }
"""
s=s.replace(event_anchor,event_new,1)

for marker in (
    "maps-shared-runtime-20260921-r7-safe5",
    "HK_MAP_SHARED_RUNTIME_REV",
    "function mapSharedKnowledgeEnabled()",
    "async function mapSharedKnownBuildingRooms",
    "_website_hydrate:mapSharedKnowledgeEnabled()",
    "sharedKnown:sharedKnownCount",
    "hk-map-shared-knowledge",
):
    req(marker,"missing shared runtime marker: "+marker)

TARGET.write_text(s,encoding="utf-8")
