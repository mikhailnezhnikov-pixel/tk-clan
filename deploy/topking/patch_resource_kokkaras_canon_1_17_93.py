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

rep("// @version      1.17.92",
    "// @version      1.17.93\n"
    "// @release-note Ресурсы: механика обмена выровнена по закреплённому Kokkaras 5.3.22-ui-icons-pit-dim. Для событий используются канонические API-тиры 1/2/3/4/5 (0/1/2/3/5), POST /player/event с event_building_id + side_event_id + number_of_completions; уровни 4+/5+ больше не отправляются как event tier. Убрано зависание на /player/me перед обменом.",
    "version")
rep("const BUILD_VERSION = '1.17.92';","const BUILD_VERSION = '1.17.93';","build")

anchor="  const HK_RESOURCE_MAXIMUM_RUN_REV='resource-maximum-run-stable-20260925-r1';"
rep(anchor,anchor+"\n  const HK_RESOURCE_KOKKARAS_CANON_REV='resources-kokkaras-5.3.22-20260925-r1';\n  const RESOURCE_CANONICAL_TIERS=[0,1,2,3,5];","resource canon marker")

tier_fn="""  function resourceTierLabel(tier) {
    return ['1','2','3','4','4+','5','5+','MAX'][Math.max(0,Math.trunc(Number(tier)))] || `T${Math.max(0,Math.trunc(Number(tier))) + 1}`;
  }
"""
tier_new=tier_fn+"""
  function resourceCanonicalTier(tier) {
    const value=Math.max(0,Math.trunc(Number(tier)||0));
    if(value>=5)return 5;
    if(value>=3)return 3;
    if(value>=2)return 2;
    if(value>=1)return 1;
    return 0;
  }
"""
rep(tier_fn,tier_new,"canonical tier helper")

rep(
"    const tierButtons = activeBuilding ? Array.from({length:maximumTier + 1},(_,tier)=>`<button data-resource-tier="${tier}" class="${tier===activeTier?'active':''}" ${resourceBusy?'disabled':''}>${resourceTierLabel(tier)}</button>`).join('') : '';",
"    const tierButtons = activeBuilding ? RESOURCE_CANONICAL_TIERS.filter(tier=>tier<=maximumTier).map(tier=>`<button data-resource-tier="${tier}" class="${tier===resourceCanonicalTier(activeTier)?'active':''}" ${resourceBusy?'disabled':''}>${resourceTierLabel(tier)}</button>`).join('') : '';",
"canonical resource tier buttons")

rep(
"      const storedTier=Number(savedResourceTiers()[resourceSelectedKind]);\n      const requestedTier=Number.isSafeInteger(Number(resourceBuildings[0]?.tier)) ? Number(resourceBuildings[0].tier) : Number.isSafeInteger(storedTier) ? storedTier : null;",
"      const storedTier=Number(savedResourceTiers()[resourceSelectedKind]);\n      const requestedTier=Number.isSafeInteger(Number(resourceBuildings[0]?.tier)) ? resourceCanonicalTier(resourceBuildings[0].tier) : Number.isSafeInteger(storedTier) ? resourceCanonicalTier(storedTier) : null;",
"load canonical tier")

rep(
"    const selectedTier=Math.max(0,Math.trunc(Number(tier)));",
"    const selectedTier=resourceCanonicalTier(tier);",
"tier switch canonicalization")

start=s.find("  async function runResourceEvents(rows) {")
end=s.find("\n\n  function exportMobileSettings()",start)
if start<0 or end<0:
    raise SystemExit("runResourceEvents block missing")

new_func=r'''  async function runResourceEvents(rows) {
    if (!requireLicense()) {
      log(either('Ресурсы: лицензия не активна.','Resources: license is not active.'),'warn');
      return;
    }
    if (resourceBusy) {
      log(either('Ресурсы: уже выполняется чтение или обмен.','Resources: a read or exchange is already running.'),'warn');
      return;
    }
    if (hkRunner.running) {
      alert(either('Сначала завершите текущую задачу','Finish the current task first'));
      return;
    }

    const selected=resourceBuildings[0];
    if(!selected?.id){
      log(either('Ресурсы: ресурсное здание не выбрано.','Resources: no resource building is selected.'),'warn');
      return;
    }

    const requestedTier=resourceCanonicalTier(selected.tier);
    const maximumMode=resourceMaximumMode;
    const totalCompletions=1000*resourceRepeatCount;

    hkRunner.start({
      title:resourceTypeName(resourceSelectedKind),
      total:1,
      step:either('Читаю канонический тир Kokkaras','Reading Kokkaras canonical tier'),
      pausable:true,
      stoppable:true
    });
    resourceBusy=true;
    renderResources();

    let completedTasks=0,totalRuns=0;
    try{
      // Kokkaras canon: read the exact event tier from /player/building.
      // Plus-levels (4+/5+) are building progression levels, not /player/event tiers.
      const tierDoc=await apiJson(
        `/player/building?building_id=${encodeURIComponent(selected.id)}&tier=${encodeURIComponent(requestedTier)}`,
        'POST'
      );
      const proof=savedResourceBuildingProofs();
      const parsed=exactResourceBuildingData(tierDoc,selected.kind,String(proof[selected.kind]||'')===String(selected.id));
      if(!parsed?.building)throw new Error(either('Игра не вернула данные выбранного тира.','The game did not return the selected tier data.'));

      const canonicalRow={...selected,tier:requestedTier,document:tierDoc};
      const options=resourceEvents(canonicalRow)
        .filter(row=>row?.atMax&&!resourceEventIsExcluded(row)&&costParts(row.cost).length===1)
        .map(row=>{
          const part=costParts(row.cost)[0];
          const balance=walletAmount(part.id,playerDocument);
          const affordable=balance==null||part.quantity<=0?0:Math.max(0,Math.floor(balance/part.quantity));
          return {...row,tier:requestedTier,affordable,plannedCompletions:maximumMode?affordable:Math.min(totalCompletions,affordable)};
        })
        .filter(row=>row.plannedCompletions>0);

      if(!options.length)throw new Error(either(
        `Для тира ${resourceTierLabel(requestedTier)} нет MAX-заданий с доступными материалами.`,
        `Tier ${resourceTierLabel(requestedTier)} has no MAX tasks with available materials.`
      ));

      const lines=options.map((row,index)=>`${index+1}. ${resourceDisplayName(row)} ×${row.plannedCompletions.toLocaleString(locale())}`);
      const heading=maximumMode
        ? either('Выполнить рассчитанный максимальный обмен?','Run the calculated maximum exchange?')
        : either(`Выполнить ресурсные задания? Лимит ×${totalCompletions}.`,`Run resource tasks? Limit ×${totalCompletions}.`);
      if(!confirm(`${heading}\n\n${lines.join('\n')}`)){
        hkRunner.reset();
        log(either('Ресурсный обмен отменён пользователем.','Resource exchange cancelled by the user.'),'warn');
        return;
      }

      hkRunner.state.total=options.length;
      hkRunner.setStep(either('Запускаю обмен','Starting exchange'),0,options.length);

      // Kokkaras ranks resource options by how many completions the current
      // inventory can afford and sends the whole allowed amount in one request.
      const pending=[...options];
      while(pending.length){
        if(hkRunner.signal?.aborted)throw new DOMException('Aborted','AbortError');
        await hkRunner.waitIfPaused();

        pending.sort((a,b)=>Number(b.plannedCompletions||0)-Number(a.plannedCompletions||0));
        const row=pending.shift();
        const part=costParts(row.cost)[0];
        const liveBalance=walletAmount(part.id,playerDocument);
        const liveAffordable=liveBalance==null||part.quantity<=0?0:Math.max(0,Math.floor(liveBalance/part.quantity));
        const quantity=Math.max(0,Math.min(row.plannedCompletions,maximumMode?liveAffordable:Math.min(totalCompletions,liveAffordable)));
        if(quantity<=0)continue;

        const name=resourceDisplayName(row);
        hkRunner.setStep(`${resourceTierLabel(requestedTier)} · ${name} · ×${quantity.toLocaleString(locale())}`,completedTasks,options.length);
        log(either(
          `${resourceTypeName(resourceSelectedKind)} · T${resourceTierLabel(requestedTier)} · ${name}: обмен ×${quantity.toLocaleString(locale())}…`,
          `${resourceTypeName(resourceSelectedKind)} · T${resourceTierLabel(requestedTier)} · ${name}: exchange ×${quantity.toLocaleString(locale())}…`
        ));

        const decision=budgetDecision(row.cost,'resources',quantity,playerDocument);
        if(!decision.allowed)throw new Error(decision.problems.join('; '));
        const before=walletAmount(part.id,playerDocument);

        let response;
        try{
          response=await apiJson('/player/event','POST',{
            event_building_id:row.roomId,
            tier:Number(requestedTier),
            side_event_id:row.sideEventId,
            number_of_completions:Number(quantity)
          },true,0);
        }catch(error){
          const message=String(error?.apiData?.description||error?.message||error||'').toLowerCase();
          if(Number(error?.httpStatus||0)===409&&message.includes('event is locked')){
            log(either(`${name}: событие заблокировано игрой, пропускаю.`,`${name}: event is locked by the game, skipping.`),'warn');
            continue;
          }
          throw error;
        }

        hkStateStore.merge(response,'resources-event');
        playerDocument=hkStateStore.snapshot||playerDocument;
        const after=walletAmount(part.id,playerDocument);
        if(before!=null && (after==null || Number(after)>=Number(before))){
          debitWallet(row.cost,quantity,playerDocument);
        }

        appendExpense({
          section:'resources',
          lotId:`resource:${row.buildingId}:${row.roomId}:${row.sideEventId||row.eventId}`,
          name,
          currencyId:part.id,
          amount:part.quantity*quantity,
          balanceBefore:before,
          balanceAfter:walletAmount(part.id,playerDocument),
          status:'ok',
          result:`completed ${quantity}`
        });

        totalRuns+=quantity;
        completedTasks+=1;
        hkRunner.setStep(`${name} · ${either('готово','done')} ×${quantity.toLocaleString(locale())}`,completedTasks,options.length);
        log(either(
          `✓ ${name}: выполнено ×${quantity.toLocaleString(locale())}`,
          `✓ ${name}: completed ×${quantity.toLocaleString(locale())}`
        ),'ok');
      }

      if(!totalRuns)throw new Error(either('Игра не выполнила ни одного доступного обмена.','The game did not complete any available exchange.'));

      log(either(
        `${resourceTypeName(resourceSelectedKind)}: обмен завершён · заданий ${completedTasks} · выполнений ${totalRuns.toLocaleString(locale())}`,
        `${resourceTypeName(resourceSelectedKind)}: exchange complete · tasks ${completedTasks} · completions ${totalRuns.toLocaleString(locale())}`
      ),'ok');

      hkGameBridge.noteMutation?.();
      hkRunner.finish(either('Ресурсный обмен завершён','Resource exchange completed'));
      resourceBusy=false;
      await loadResources(false,{playerMaxAgeMs:RESOURCE_PLAYER_CACHE_MS});
    }catch(error){
      if(error?.name==='AbortError'){
        hkRunner.reset();
        log(either('Ресурсный обмен остановлен','Resource exchange stopped'),'warn');
      }else{
        hkRunner.fail(error);
        log(either('Ошибка ресурсного обмена','Resource exchange error')+': '+(error?.message||error),'bad');
      }
    }finally{
      resourceBusy=false;
      renderResources();
    }
  }'''

s=s[:start]+new_func+s[end:]

for marker in [
    "// @version      1.17.93",
    "const BUILD_VERSION = '1.17.93';",
    "resources-kokkaras-5.3.22-20260925-r1",
    "const RESOURCE_CANONICAL_TIERS=[0,1,2,3,5];",
    "function resourceCanonicalTier(tier)",
    "event_building_id:row.roomId",
    "tier:Number(requestedTier)",
    "side_event_id:row.sideEventId",
    "number_of_completions:Number(quantity)",
    "resources-event",
]:
    if marker not in s: raise SystemExit("missing marker: "+marker)

if "resources:run-preflight" in s:
    raise SystemExit("old /player/me resource preflight still present")

target.write_text(s,encoding="utf-8")
print("RESOURCE_KOKKARAS_CANON_1_17_93=PASS")
print("version=1.17.93")
