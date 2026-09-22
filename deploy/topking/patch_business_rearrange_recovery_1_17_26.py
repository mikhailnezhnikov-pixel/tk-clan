from pathlib import Path

TARGET=Path("/tmp/HamsterKingMobile.user.js")
s=TARGET.read_text(encoding="utf-8")
MARKER="businesses-rearrange-recovery-20260922-r1"

if MARKER in s:
    print("BUSINESSES_REARRANGE_RECOVERY_ALREADY_PRESENT")
    raise SystemExit(0)

for required in [
    "// @version      1.17.25",
    "const BUILD_VERSION = '1.17.25';",
    "const HK_CORE_REVISION = 'core-20260921-r27-businesses-runner-canon';",
    "const HK_BUSINESSES_RUNNER_UI_REV='businesses-runner-canon-20260921-r1';",
    "const HK_BUSINESSES_FINALIZE_REV='businesses-finalize-single-snapshot-20260921-r1';",
    "async function businessAction(",
    "async function executeBusinessPlan()",
    "function prepareOriginalBusinessRestore()",
]:
    if required not in s:
        raise SystemExit("missing marker: "+required)

s=s.replace("// @version      1.17.25","// @version      1.17.26",1)
s=s.replace("const BUILD_VERSION = '1.17.25';","const BUILD_VERSION = '1.17.26';",1)

release_anchor="// @release-note Clan Shop теперь считывает фактическую историю общих покупок: кто именно купил шар идолов или S+ бизнес, по точному player_id."
release_new="// @release-note Перестановка бизнесов: восстановлены видимые названия, сквозной канонический прогресс и безопасная сверка состояния после тайм-аутов без слепого отката."
if release_anchor not in s:
    raise SystemExit("release note anchor missing")
s=s.replace(release_anchor,release_new+"\n"+release_anchor,1)

rev_anchor="  const HK_BUSINESSES_FINALIZE_REV='businesses-finalize-single-snapshot-20260921-r1';"
s=s.replace(rev_anchor,rev_anchor+"\n  const HK_BUSINESSES_RECOVERY_REV='businesses-rearrange-recovery-20260922-r1';",1)

name_anchor="  function businessBonusAmount(bonus) {"
name_helper=r'''  function businessDisplayName(businessId) {
    const id=String(businessId||'');
    if(!id)return either('Пустой слот','Empty slot');
    const details=businessCardDetails(id);
    return clean(details?.name)||clean(recipeMetadata(id)?.name)||clean(gameText(id))||id;
  }

'''
if name_anchor not in s:
    raise SystemExit("business name helper anchor missing")
s=s.replace(name_anchor,name_helper+name_anchor,1)

visual_anchor="""  function businessVisual(id) {
    return id ? iconHtml(id) : '<span class="hk-empty-icon compact">＋</span>';
  }
"""
if visual_anchor not in s:
    raise SystemExit("business visual anchor missing")
visual_new=visual_anchor+r'''
  function businessPlanVisual(id) {
    if(!id)return '<span class="hk-plan-business empty"><span class="hk-empty-icon compact">＋</span><small>'+escapeHtml(either('Пусто','Empty'))+'</small></span>';
    return '<span class="hk-plan-business">'+iconHtml(id)+'<small>'+escapeHtml(businessDisplayName(id))+'</small></span>';
  }
'''
s=s.replace(visual_anchor,visual_new,1)
s=s.replace("businessVisual(row.businessId)","businessPlanVisual(row.businessId)")
s=s.replace("businessVisual(id)","businessPlanVisual(id)")

css_anchor=".hk-plan-row .hk-icon{width:34px;height:34px;flex-basis:34px}"
if css_anchor not in s:
    raise SystemExit("business plan css anchor missing")
css_extra=".hk-plan-business{display:grid;grid-template-columns:34px;justify-items:center;gap:3px;min-width:72px;max-width:112px}.hk-plan-business small{width:100%;color:#d7e0ec;font-size:9px;line-height:1.15;text-align:center;white-space:normal;overflow-wrap:anywhere}.hk-plan-business.empty small{color:#8fa0b8}.hk-plan-business .hk-icon{width:34px;height:34px;flex-basis:34px}"
s=s.replace(css_anchor,css_anchor+css_extra,1)

execute_anchor="  async function executeBusinessPlan() {\n"
if execute_anchor not in s:
    raise SystemExit("execute anchor missing")

helpers=r'''  function businessMutationUncertain(error) {
    if(!error||error?.name==='AbortError')return false;
    const text=String(error?.message||error||'').toLowerCase();
    return error?.name==='HKNetworkTimeout'||/тайм-аут|timed out|timeout|failed to fetch|load failed|networkerror|network request failed|fetch failed/.test(text);
  }

  async function businessSlotSnapshot(row, reason) {
    playerDocument=await hkAuthoritativePlayerRead(reason);
    return findSlot(playerDocument,row.buildingId,row.slot);
  }

  function businessSlotConflict(state, expectedBusinessId, actionLabel) {
    const current=String(state?.businessId||'');
    if(!current||current===String(expectedBusinessId||''))return null;
    return new Error(either(
      actionLabel+': в слоте уже другой бизнес — '+businessDisplayName(current),
      actionLabel+': another business is already in the slot — '+businessDisplayName(current)
    ));
  }

  async function businessRemoveConfirmed(row, expectedBusinessId=row.businessId, label='') {
    const expected=String(expectedBusinessId||row.businessId||'');
    const name=label||businessDisplayName(expected);
    try{
      return await businessAction('remove',row);
    }catch(error){
      if(!businessMutationUncertain(error))throw error;
      hkRunner.note(either('Тайм-аут снятия «'+name+'»: сверяю фактический слот','Remove timeout for “'+name+'”: checking the actual slot'),'warn');
      recordDiagnostic('business-remove-timeout-reconcile',{buildingId:row.buildingId,slot:row.slot,businessId:expected});
      let state=await businessSlotSnapshot(row,'business-remove-timeout-check-1');
      if(!state?.businessId){
        hkRunner.note(either('Снятие подтверждено по состоянию игры','Removal confirmed from game state'),'ok');
        return {__hk_reconciled:true};
      }
      const conflict=businessSlotConflict(state,expected,either('Снятие','Removal'));
      if(conflict)throw conflict;
      await gameRetryDelay(900);
      state=await businessSlotSnapshot(row,'business-remove-timeout-check-2');
      if(!state?.businessId){
        hkRunner.note(either('Снятие подтверждено после ожидания','Removal confirmed after waiting'),'ok');
        return {__hk_reconciled:true};
      }
      const secondConflict=businessSlotConflict(state,expected,either('Снятие','Removal'));
      if(secondConflict)throw secondConflict;
      hkRunner.note(either('Слот дважды подтверждён без изменений — повторяю снятие один раз','Slot was confirmed unchanged twice — retrying removal once'),'info');
      try{
        return await businessAction('remove',state);
      }catch(retryError){
        if(!businessMutationUncertain(retryError))throw retryError;
        state=await businessSlotSnapshot(row,'business-remove-timeout-retry-check');
        if(!state?.businessId){
          hkRunner.note(either('Повторное снятие подтверждено по состоянию игры','Retried removal confirmed from game state'),'ok');
          return {__hk_reconciled:true};
        }
        const retryConflict=businessSlotConflict(state,expected,either('Снятие','Removal'));
        if(retryConflict)throw retryConflict;
        throw new Error(either(
          'Не удалось подтвердить снятие «'+name+'» после тайм-аута. Слот остался без изменений',
          'Could not confirm removal of “'+name+'” after timeout. The slot remained unchanged'
        ));
      }
    }
  }

  async function businessInsertConfirmed(row, businessId, label='') {
    const expected=String(businessId||'');
    const name=label||businessDisplayName(expected);
    const verify=async(reason)=>{
      const state=await businessSlotSnapshot(row,reason);
      if(state?.businessId===expected)return state;
      if(state?.businessId)throw businessSlotConflict(state,expected,either('Вставка','Insertion'));
      return state;
    };
    try{
      const response=await businessAction('insert',row,expected);
      let state=findSlot(response,row.buildingId,row.slot);
      if(state?.businessId===expected)return state;
      state=await verify('business-insert-response-check');
      if(state?.businessId===expected)return state;
      throw new Error(either(
        'После вставки игра не подтвердила «'+name+'»',
        'The game did not confirm “'+name+'” after insertion'
      ));
    }catch(error){
      if(!businessMutationUncertain(error))throw error;
      hkRunner.note(either('Тайм-аут вставки «'+name+'»: сверяю фактический слот','Insert timeout for “'+name+'”: checking the actual slot'),'warn');
      recordDiagnostic('business-insert-timeout-reconcile',{buildingId:row.buildingId,slot:row.slot,businessId:expected});
      let state=await verify('business-insert-timeout-check-1');
      if(state?.businessId===expected){
        hkRunner.note(either('Вставка подтверждена по состоянию игры','Insertion confirmed from game state'),'ok');
        return state;
      }
      await gameRetryDelay(900);
      state=await verify('business-insert-timeout-check-2');
      if(state?.businessId===expected){
        hkRunner.note(either('Вставка подтверждена после ожидания','Insertion confirmed after waiting'),'ok');
        return state;
      }
      hkRunner.note(either('Слот дважды подтверждён пустым — повторяю вставку один раз','Slot was confirmed empty twice — retrying insertion once'),'info');
      try{
        const response=await businessAction('insert',row,expected);
        state=findSlot(response,row.buildingId,row.slot);
        if(state?.businessId===expected)return state;
        state=await verify('business-insert-timeout-retry-response');
        if(state?.businessId===expected)return state;
        throw new Error(either('Повторная вставка не подтверждена','Retried insertion was not confirmed'));
      }catch(retryError){
        if(!businessMutationUncertain(retryError))throw retryError;
        state=await verify('business-insert-timeout-retry-check');
        if(state?.businessId===expected){
          hkRunner.note(either('Повторная вставка подтверждена по состоянию игры','Retried insertion confirmed from game state'),'ok');
          return state;
        }
        throw new Error(either(
          'Не удалось подтвердить вставку «'+name+'» после тайм-аута. Слот остался пустым',
          'Could not confirm insertion of “'+name+'” after timeout. The slot remained empty'
        ));
      }
    }
  }

  async function rollbackBusinessPlan(plan, inserted, removed) {
    const targetByKey=new Map((plan||[]).map(pair=>[pair[0]?.key,String(pair[1]||'')]));
    playerDocument=await hkAuthoritativePlayerRead('business-rollback-start');
    for(const pair of [...inserted].reverse()){
      const row=pair[0],id=String(pair[1]||'');
      let current=findSlot(playerDocument,row.buildingId,row.slot);
      if(!current?.businessId||current.businessId===row.businessId)continue;
      if(current.businessId!==id)throw new Error(either(
        'Откат остановлен: в '+buildingSlotLabel(row)+' обнаружен неожиданный бизнес '+businessDisplayName(current.businessId),
        'Rollback stopped: an unexpected business '+businessDisplayName(current.businessId)+' was found in '+buildingSlotLabel(row)
      ));
      await businessRemoveConfirmed(current,id,businessDisplayName(id));
      playerDocument=await hkAuthoritativePlayerRead('business-rollback-remove');
    }
    for(const row of removed){
      let current=findSlot(playerDocument,row.buildingId,row.slot);
      if(current?.businessId===row.businessId){
        if(!businessSlotIsActive(current,row.businessId))await finishPendingBusiness(current,businessDisplayName(row.businessId),true);
        continue;
      }
      if(current?.businessId){
        const planned=String(targetByKey.get(row.key)||'');
        if(!planned||current.businessId!==planned)throw new Error(either(
          'Откат остановлен: слот '+buildingSlotLabel(row)+' уже изменён вне плана',
          'Rollback stopped: slot '+buildingSlotLabel(row)+' has already changed outside the plan'
        ));
        await businessRemoveConfirmed(current,current.businessId,businessDisplayName(current.businessId));
        playerDocument=await hkAuthoritativePlayerRead('business-rollback-clear-target');
        current=findSlot(playerDocument,row.buildingId,row.slot);
      }
      if(current?.businessId===row.businessId)continue;
      if(current?.businessId)throw new Error(either('Не удалось освободить слот для отката','Could not clear the slot for rollback'));
      const restored=await businessInsertConfirmed(row,row.businessId,businessDisplayName(row.businessId));
      await finishPendingBusiness(restored,businessDisplayName(row.businessId),true);
      playerDocument=await hkAuthoritativePlayerRead('business-rollback-restored');
    }
  }

'''
s=s.replace(execute_anchor,helpers+execute_anchor,1)

start=s.find(execute_anchor)
end=s.find("  function prepareOriginalBusinessRestore() {",start)
if start<0 or end<0:
    raise SystemExit("execute function slice missing")
block=s[start:end]

old_start="    hkRunner.start({title:either('Перестановка бизнесов','Business rearrangement'),total:Math.max(1,plan.length),step:either('Подготовка','Preparing'),pausable:true,stoppable:true});\n    businessBusy = true;\n    const removed = [], inserted = [];"
new_start="    const initialRemovalWork=plan.filter(pair=>!!pair[0]?.businessId).length;\n    const initialTotalWork=Math.max(1,initialRemovalWork+plan.length);\n    hkRunner.start({title:either('Перестановка бизнесов','Business rearrangement'),total:initialTotalWork,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});\n    businessBusy = true;\n    const removed = [], inserted = [];\n    let workDone=0,totalWork=initialTotalWork;"
if old_start not in block:
    raise SystemExit("runner start block missing")
block=block.replace(old_start,new_start,1)

session_anchor="        playerDocument = await apiJson('/player/me', 'POST');\n        await releaseFreeBusinessManagers();"
if session_anchor not in block:
    raise SystemExit("business session anchor missing")
block=block.replace(session_anchor,"        playerDocument = await apiJson('/player/me', 'POST');\n        await ensureRecipeMetadata();\n        await releaseFreeBusinessManagers();",1)

plan_anchor="        refreshBusinessData();\n        plan = makePlan();\n        const safety = optimizerSafety(plan.length);"
if plan_anchor not in block:
    raise SystemExit("replanned business anchor missing")
block=block.replace(plan_anchor,"        refreshBusinessData();\n        plan = makePlan();\n        totalWork=Math.max(1,plan.filter(pair=>!!pair[0]?.businessId).length+plan.length);\n        workDone=0;\n        hkRunner.setStep(either('Подготовка','Preparing'),workDone,totalWork);\n        const safety = optimizerSafety(plan.length);",1)

remove_start=block.find("      for (const [row] of plan) {")
remove_end=block.find("      let processedInsertRows = 0;",remove_start)
if remove_start<0 or remove_end<0:
    raise SystemExit("remove loop slice missing")
remove_loop=r'''      for (const [row] of plan) {
        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');
        await hkRunner.waitIfPaused();
        if (!row.businessId) { log(either('Пустой слот: ','Empty slot: ')+buildingSlotLabel(row)); continue; }
        const removeName=businessDisplayName(row.businessId);
        hkRunner.setStep(either('Снимаю: ','Removing: ')+removeName+' · T'+(tier(row.businessId)??'—'),workDone,totalWork);
        log(either('Снимаю ','Removing ')+removeName+' · T'+(tier(row.businessId)??'—')+'…');
        await businessRemoveConfirmed(row,row.businessId,removeName);
        removed.push(row);
        workDone+=1;
        hkRunner.setStep(either('Снят: ','Removed: ')+removeName,workDone,totalWork);
      }
'''
block=block[:remove_start]+remove_loop+block[remove_end:]

insert_start=block.find("      let processedInsertRows = 0;")
insert_end=block.find("\n\n      // All mutation rows have been processed.",insert_start)
if insert_start<0 or insert_end<0:
    raise SystemExit("insert loop slice missing")
insert_loop=r'''      for (const [row, id] of plan) {
        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');
        await hkRunner.waitIfPaused();
        if (!id) {
          hkRunner.setStep(either('Оставляю слот пустым: ','Leaving slot empty: ')+buildingSlotLabel(row),workDone,totalWork);
          log(either('Оставляю пустым: ','Leaving empty: ')+buildingSlotLabel(row));
          workDone+=1;
          hkRunner.setStep(either('Пустой слот подтверждён','Empty slot confirmed'),workDone,totalWork);
          continue;
        }
        const insertName=businessDisplayName(id);
        hkRunner.setStep(either('Вставляю: ','Inserting: ')+insertName+' · T'+(tier(id)??'—'),workDone,totalWork);
        log(either('Вставляю ','Inserting ')+insertName+' · T'+(tier(id)??'—')+'…');
        const state=await businessInsertConfirmed(row,id,insertName);
        inserted.push([row,id]);
        await finishPendingBusiness(state,insertName,true);
        workDone+=1;
        hkRunner.setStep(either('Активирован: ','Activated: ')+insertName,workDone,totalWork);
      }'''
block=block[:insert_start]+insert_loop+block[insert_end:]

old_verify="      hkRunner.setStep(either('Проверяю результат','Verifying result'), Math.max(1,plan.length), Math.max(1,plan.length));"
if old_verify not in block:
    raise SystemExit("final verify progress anchor missing")
block=block.replace(old_verify,"      hkRunner.setStep(either('Проверяю результат','Verifying result'),workDone,totalWork);",1)

rollback_start=block.find("        try {\n          for (const [row] of inserted.reverse())")
rollback_done="          log('Исходная схема восстановлена', 'ok');"
rollback_end=block.find(rollback_done,rollback_start)
if rollback_start<0 or rollback_end<0:
    raise SystemExit("legacy rollback block missing")
rollback_end+=len(rollback_done)
rollback_new="""        try {
          await rollbackBusinessPlan(plan,inserted,removed);
          log('Исходная схема восстановлена', 'ok');"""
block=block[:rollback_start]+rollback_new+block[rollback_end:]

s=s[:start]+block+s[end:]

for marker in [
    "// @version      1.17.26",
    "const BUILD_VERSION = '1.17.26';",
    "HK_BUSINESSES_RECOVERY_REV='businesses-rearrange-recovery-20260922-r1'",
    "function businessDisplayName(",
    "function businessPlanVisual(",
    "function businessMutationUncertain(",
    "async function businessRemoveConfirmed(",
    "async function businessInsertConfirmed(",
    "async function rollbackBusinessPlan(",
    "initialTotalWork",
    "workDone,totalWork",
    "await ensureRecipeMetadata();",
    "await rollbackBusinessPlan(plan,inserted,removed);",
]:
    if marker not in s:
        raise SystemExit("post-patch marker missing: "+marker)

if "for (const [row] of inserted.reverse())" in block:
    raise SystemExit("blind rollback loop still present")
if "let processedInsertRows = 0;" in block:
    raise SystemExit("phase-reset insert progress still present")
if "businessVisual(row.businessId)" in s or "businessVisual(id)" in s:
    raise SystemExit("unnamed business plan visual still present")

TARGET.write_text(s,encoding="utf-8")
print("BUSINESSES_REARRANGE_RECOVERY_R1=PASS")
