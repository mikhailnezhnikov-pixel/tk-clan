from pathlib import Path

TARGET=Path('/tmp/HamsterKingMobile.user.js')
s=TARGET.read_text(encoding='utf-8')
OLD_REV="maps-active-intersection-20260920-r3"
NEW_REV="maps-parallel-read-20260920-r4"

def require(needle,message):
    if needle not in s:
        raise SystemExit(message)

require(f"HK_MAP_SCANNER_REV = '{OLD_REV}'","scanner r3 missing")
require("HK_MAP_COORDS_REV = 'maps-coordinates-column-row-20260920-r1'","coords r1 missing")
require("HK_BUILDINGS_CANON_REV = 'buildings-canon-core-20260920-r1'","buildings r1 missing")

s=s.replace(f"HK_MAP_SCANNER_REV = '{OLD_REV}'",f"HK_MAP_SCANNER_REV = '{NEW_REV}'",1)

marker=f"  const HK_MAP_SCANNER_REV = '{NEW_REV}';"
s=s.replace(marker,marker+"\n  const HK_MAP_READ_CONCURRENCY = 6;\n  const HK_MAP_SUBMIT_BATCH = 100;",1)

old_submit="""  async function mapSubmitBuildingStudy(buildingId,areaId,roomCount,hasEvents) {
    const id=String(buildingId||''), area=String(areaId||'');
    if(!id||!area||roomCount==null)return false;
    const key=`${area}:${id}:${Number(roomCount)}`;
    const now=Date.now(), previous=Number(mapBuildingStudySubmitDedupe.get(key)||0);
    if(previous&&now-previous<5000)return true;
    mapBuildingStudySubmitDedupe.set(key,now);
    const areaRow=((hkStateStore.snapshot||playerDocument)?.areas?.areas||[]).find(row=>String(row?.gamearea_id||row?.area_id||'')===area);
    if(!areaRow)return false;
    try{
      await mapServerJson('/submit',{area:{area_id:area,city_id:String(areaRow?.city_id||''),expected_buildings:0,buildings:[{building_id:id,opened:true,room_count:Number(roomCount),has_events:!!hasEvents}]}});
      return true;
    }catch(_){
      mapBuildingStudySubmitDedupe.delete(key);
      return false;
    }
  }
"""
new_submit=old_submit+"""
  async function mapSubmitBuildingStudyBatch(areaId,rows) {
    const area=String(areaId||'');
    const cleanRows=(Array.isArray(rows)?rows:[]).filter(row=>row?.buildingId&&row?.roomCount!=null);
    if(!area||!cleanRows.length)return {submitted:0,failed:0};
    const areaRow=((hkStateStore.snapshot||playerDocument)?.areas?.areas||[]).find(row=>String(row?.gamearea_id||row?.area_id||'')===area);
    if(!areaRow)return {submitted:0,failed:cleanRows.length};
    let submitted=0,failed=0;
    for(let offset=0;offset<cleanRows.length;offset+=HK_MAP_SUBMIT_BATCH){
      const chunk=cleanRows.slice(offset,offset+HK_MAP_SUBMIT_BATCH);
      try{
        await mapServerJson('/submit',{area:{
          area_id:area,
          city_id:String(areaRow?.city_id||''),
          expected_buildings:0,
          buildings:chunk.map(row=>({
            building_id:String(row.buildingId),
            opened:true,
            room_count:Number(row.roomCount),
            has_events:!!row.hasEvents
          }))
        }});
        const now=Date.now();
        for(const row of chunk){
          mapBuildingStudySubmitDedupe.set(`${area}:${row.buildingId}:${Number(row.roomCount)}`,now);
        }
        submitted+=chunk.length;
      }catch(_){
        // Preserve reliability: only a failed batch falls back to the old
        // one-building submit path.
        for(const row of chunk){
          if(await mapSubmitBuildingStudy(row.buildingId,area,row.roomCount,row.hasEvents))submitted+=1;
          else failed+=1;
        }
      }
    }
    return {submitted,failed};
  }
"""
require(old_submit,"mapSubmitBuildingStudy anchor missing")
s=s.replace(old_submit,new_submit,1)

start=s.index("  async function mapBackfillActiveBuildingStudies")
end=s.index("\n  async function mapAreaPayload",start)
old_backfill=s[start:end]
new_backfill="""  async function mapBackfillActiveBuildingStudies(selectedAreaIds=null) {
    const state=hkStateStore.snapshot||playerDocument||{};
    const active=activePlayerBuildingIds(state);
    const selected=selectedAreaIds instanceof Set?selectedAreaIds:null;
    const crystalIds=await ensureCrystalEventCatalog();
    if(!crystalIds.size)log(either(
      'Каталог /events недоступен: здания без прямого crystal-маркера останутся неизвестными, ложный 0 не записывается.',
      '/events catalog is unavailable: buildings without a direct crystal marker stay unknown; false zero is not stored.'
    ),'warn');
    const rows=[];
    // Strict safe intersection:
    // building must be active in /player/me AND mapped by /game_area/{area}/buildings.
    for(const buildingId of active){
      const areaId=String(mapBuildingAreas.get(buildingId)||'');
      if(!areaId||(selected&&!selected.has(areaId)))continue;
      rows.push({buildingId,areaId});
    }
    const unique=[...new Map(rows.map(row=>[row.buildingId,row])).values()];
    let studied=0,known=0,failed=0,completed=0,cursor=0;
    const observations=[];
    const baseDone=hkRunner.state.done||0;
    const total=baseDone+unique.length;
    hkRunner.setStep(either('Считываю открытые здания','Reading active buildings'),baseDone,total);

    const worker=async()=>{
      while(true){
        if(hkRunner.signal?.aborted)throw new DOMException('Aborted','AbortError');
        await hkRunner.waitIfPaused();
        const index=cursor++;
        if(index>=unique.length)return;
        const {buildingId,areaId}=unique[index];
        try{
          let value=buildingStudyCache.get(buildingId)||null;
          let roomCount=value?crystalRoomCount(value,crystalIds):null;
          if(roomCount==null){
            value=await apiJson(`/player/building?building_id=${encodeURIComponent(buildingId)}`,'POST');
            buildingStudyCache.set(buildingId,value);
            roomCount=crystalRoomCount(value,crystalIds);
          }else known+=1;
          if(roomCount!=null){
            const rooms=buildingRooms(value);
            observations.push({buildingId,areaId,roomCount,hasEvents:rooms.length>0||roomCount>0});
          }else failed+=1;
        }catch(error){
          if(error?.name==='AbortError')throw error;
          failed+=1;
        }finally{
          completed+=1;
          hkRunner.setStep(`${either('Считано зданий','Buildings read')}: ${completed}/${unique.length}`,baseDone+completed,total);
        }
      }
    };

    const workers=Math.min(HK_MAP_READ_CONCURRENCY,Math.max(1,unique.length));
    await Promise.all(Array.from({length:workers},()=>worker()));

    const grouped=new Map();
    for(const row of observations){
      if(!grouped.has(row.areaId))grouped.set(row.areaId,[]);
      grouped.get(row.areaId).push(row);
    }
    for(const [areaId,areaRows] of grouped){
      if(hkRunner.signal?.aborted)throw new DOMException('Aborted','AbortError');
      await hkRunner.waitIfPaused();
      const result=await mapSubmitBuildingStudyBatch(areaId,areaRows);
      studied+=result.submitted;
      failed+=result.failed;
    }
    return {total:unique.length,studied,known,failed,workers};
  }
"""
s=s[:start]+new_backfill+s[end:]

require(f"HK_MAP_SCANNER_REV = '{NEW_REV}'","scanner r4 marker missing")
require("const HK_MAP_READ_CONCURRENCY = 6;","parallel read constant missing")
require("const HK_MAP_SUBMIT_BATCH = 100;","submit batch constant missing")
require("async function mapSubmitBuildingStudyBatch(","batch submit function missing")
require("Promise.all(Array.from({length:workers},()=>worker()))","parallel workers missing")
require("activePlayerBuildingIds(state)","safe active intersection lost")
require("ensureCrystalEventCatalog()","event catalog guard lost")
require("hkMutationGate.run('/player/building'","explicit building opening gate lost")
require("HK_MAP_COORDS_REV = 'maps-coordinates-column-row-20260920-r1'","coords invariant lost")
require("HK_BUILDINGS_CANON_REV = 'buildings-canon-core-20260920-r1'","buildings invariant lost")
require("HK_STAGE2J_BOSSES_REV = 'bosses-area-target-20260920-r2'","bosses invariant lost")
require("HK_PITS_REWARD_PICKER_REV = 'pits-reward-picker-20260920-r20'","pits invariant lost")

TARGET.write_text(s,encoding='utf-8')
