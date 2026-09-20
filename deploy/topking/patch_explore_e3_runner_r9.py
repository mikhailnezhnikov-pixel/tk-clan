from pathlib import Path

p=Path("/tmp/HamsterKingMobile.user.js")
s=p.read_text()

old_marker="const HK_EXPLORE_CANON_REV='explore-e3-single-20260920-r8';"
new_marker="const HK_EXPLORE_CANON_REV='explore-e3-single-20260920-r9-runner';"
assert s.count(old_marker)==1, s.count(old_marker)
s=s.replace(old_marker,new_marker,1)

# Keep completed Explore runner visible long enough to inspect.
old_finish="""      finish(step='') { if(step)state.step=String(step); state.status='done'; if(state.total)state.done=state.total; recordDiagnostic('runner-finish',{title:state.title}); emit(); setTimeout(()=>{if(state.status==='done'){state.status='idle';emit();}},1800); },"""
new_finish="""      finish(step='') { if(step)state.step=String(step); state.status='done'; if(state.total)state.done=state.total; recordDiagnostic('runner-finish',{title:state.title}); emit(); const keep=String(state.title||'')===either('Исследование · E3','Explore · E3')?15000:1800; setTimeout(()=>{if(state.status==='done'){state.status='idle';emit();}},keep); },"""
assert s.count(old_finish)==1, s.count(old_finish)
s=s.replace(old_finish,new_finish,1)

old_render="""    const visibleState=state.status!=='idle'; box.classList.toggle('show',visibleState);
    box.classList.toggle('pit-run',visibleState&&String(state.title||'')===either('Ямы','Pits'));
    if(!visibleState)return;"""
new_render="""    const visibleState=state.status!=='idle',title=String(state.title||''),exploreRun=visibleState&&title===either('Исследование · E3','Explore · E3'); box.classList.toggle('show',visibleState);
    box.classList.toggle('pit-run',visibleState&&title===either('Ямы','Pits'));
    box.classList.toggle('explore-run',exploreRun);
    if(!visibleState)return;"""
assert s.count(old_render)==1, s.count(old_render)
s=s.replace(old_render,new_render,1)

old_history="""      const rows=Array.isArray(state.history)?state.history:[];
      history.innerHTML=rows.map(row=>'<div class="hk-runner-history-row '+escapeHtml(row.type||'')+'"><span>'+new Date(row.at||Date.now()).toLocaleTimeString(locale(),{hour:'2-digit',minute:'2-digit',second:'2-digit'})+'</span><b>'+escapeHtml(row.text||'')+'</b></div>').join('');
      history.style.display=rows.length?'grid':'none';"""
new_history="""      const rows=Array.isArray(state.history)?state.history:[];
      history.innerHTML=rows.map(row=>{
        if(exploreRun&&row.stageKey){const st=String(row.stageStatus||'pending'),icon=st==='done'?'✓':st==='running'?'▶':st==='skipped'?'—':st==='error'?'×':'○';return '<div class="hk-runner-history-row hk-runner-stage '+escapeHtml('stage-'+st)+'"><span class="hk-runner-stage-icon">'+icon+'</span><b>'+escapeHtml(row.text||'')+'</b></div>';}
        return '<div class="hk-runner-history-row '+escapeHtml(row.type||'')+'"><span>'+new Date(row.at||Date.now()).toLocaleTimeString(locale(),{hour:'2-digit',minute:'2-digit',second:'2-digit'})+'</span><b>'+escapeHtml(row.text||'')+'</b></div>';
      }).join('');
      history.style.display=rows.length?'grid':'none';"""
assert s.count(old_history)==1, s.count(old_history)
s=s.replace(old_history,new_history,1)

old_css=""".hk-runner.show{display:block}.hk-runner.pit-run{border-color:#ffad1f;background:linear-gradient(145deg,#302411,#17170f);box-shadow:0 0 0 2px #ffad1f26,0 8px 24px #0006}.hk-runner-head"""
new_css=""".hk-runner.show{display:block}.hk-runner.pit-run{border-color:#ffad1f;background:linear-gradient(145deg,#302411,#17170f);box-shadow:0 0 0 2px #ffad1f26,0 8px 24px #0006}.hk-runner.explore-run{border-color:#ffad1f;background:linear-gradient(145deg,#1d2635,#111820);box-shadow:0 0 0 2px #ffad1f24,0 8px 24px #0007}.hk-runner.explore-run .hk-runner-head b{color:#ffe08a}.hk-runner.explore-run .hk-runner-history{border-color:#46566d;background:#090e1599}.hk-runner.explore-run .hk-runner-stage{grid-template-columns:24px minmax(0,1fr);align-items:center;min-height:27px;border:1px solid #2b394d;background:#0d1520}.hk-runner.explore-run .hk-runner-stage-icon{display:grid;place-items:center;width:20px;height:20px;border-radius:50%;font:900 12px/1 Arial;color:#718197;background:#172131}.hk-runner.explore-run .hk-runner-stage.stage-running{border-color:#b27b27;background:#2a2114;box-shadow:0 0 0 1px #ffad1f22 inset}.hk-runner.explore-run .hk-runner-stage.stage-running .hk-runner-stage-icon{color:#171006;background:#ffb42b}.hk-runner.explore-run .hk-runner-stage.stage-running b{color:#ffe0a0}.hk-runner.explore-run .hk-runner-stage.stage-done{border-color:#285d49;background:#10221b}.hk-runner.explore-run .hk-runner-stage.stage-done .hk-runner-stage-icon{color:#092116;background:#67d9a0}.hk-runner.explore-run .hk-runner-stage.stage-done b{color:#8ee6b8}.hk-runner.explore-run .hk-runner-stage.stage-skipped{opacity:.72}.hk-runner.explore-run .hk-runner-stage.stage-skipped .hk-runner-stage-icon{color:#362a0e;background:#d6b65c}.hk-runner.explore-run .hk-runner-stage.stage-error{border-color:#7b3544;background:#28151b}.hk-runner.explore-run .hk-runner-stage.stage-error .hk-runner-stage-icon{color:#2b0b11;background:#ff7e8e}.hk-runner.explore-run .hk-runner-stage.stage-error b{color:#ff9ca8}.hk-runner-head"""
assert s.count(old_css)==1, s.count(old_css)
s=s.replace(old_css,new_css,1)

anchor="""  let exploreE3Tiers=null,exploreE3ShopLots=null;

  function exploreE3Building(doc){"""
insert="""  let exploreE3Tiers=null,exploreE3ShopLots=null;

  function exploreE3Stage(key,label,status='pending',detail=''){
    const state=hkRunner.state,rows=Array.isArray(state.history)?[...state.history]:[],stageKey=String(key||''),stageStatus=['pending','running','done','skipped','error'].includes(String(status))?String(status):'pending';
    const text=String(label||'')+(detail?' · '+String(detail):''),type=stageStatus==='done'?'ok':stageStatus==='error'?'bad':stageStatus==='skipped'?'warn':stageStatus==='running'?'info':'';
    const row={stageKey,stageStatus,text,type,at:Date.now()},index=rows.findIndex(x=>String(x?.stageKey||'')===stageKey);
    if(index>=0)rows[index]=row;else rows.push(row);state.history=rows.slice(-12);renderRunnerState();return row;
  }
  function exploreE3InitStages(candidate,total){
    const target=exploreTierLabel(exploreSettings().targetTier);
    exploreE3Stage('prepare',either('Чтение состояния здания','Read building state'),'running',either('тест 1 из ','test 1 of ')+total);
    exploreE3Stage('events',either('Исследование событий','Explore events'),'pending');
    exploreE3Stage('battles',either('Бои','Battles'),'pending');
    exploreE3Stage('tier',either('Переход по тирам','Tier progression'),'pending',either('цель ','target ')+target);
    exploreE3Stage('verify',either('Финальная проверка','Final verification'),'pending');
  }
  function exploreE3CloseRunning(status='error',detail=''){
    const rows=Array.isArray(hkRunner.state.history)?[...hkRunner.state.history]:[];
    for(const row of rows)if(row?.stageKey&&row.stageStatus==='running')exploreE3Stage(row.stageKey,String(row.text||'').split(' · ')[0],status,detail);
  }

  function exploreE3Building(doc){"""
assert s.count(anchor)==1, s.count(anchor)
s=s.replace(anchor,insert,1)

old_process_start="""  async function exploreE3ProcessOne(initial,settings){
    const buildingId=String(initial?.id||'');if(!buildingId)throw new Error(either('Нет ID здания','Missing building ID'));let current=await exploreE3Detail(buildingId);
    if(settings.targetTier===8){"""
new_process_start="""  async function exploreE3ProcessOne(initial,settings){
    const buildingId=String(initial?.id||'');if(!buildingId)throw new Error(either('Нет ID здания','Missing building ID'));let current=await exploreE3Detail(buildingId);
    exploreE3Stage('prepare',either('Чтение состояния здания','Read building state'),'done',exploreTierLabel(Number(current?.tier||0)));
    if(settings.targetTier===8){
      exploreE3Stage('events',either('Исследование событий','Explore events'),'skipped',either('Instant MAX','Instant MAX'));
      exploreE3Stage('battles',either('Бои','Battles'),'skipped',either('Instant MAX','Instant MAX'));
      exploreE3Stage('tier',either('Переход по тирам','Tier progression'),'running',either('Instant MAX','Instant MAX'));"""
assert s.count(old_process_start)==1, s.count(old_process_start)
s=s.replace(old_process_start,new_process_start,1)

old_instant_success="""      if(Number(current?.tier||0)<7)return {status:'failed',reason:(res.error?.message||either('MAX не достигнут','MAX was not reached')),building:current};return {status:'completed',building:current};"""
new_instant_success="""      if(Number(current?.tier||0)<7)return {status:'failed',reason:(res.error?.message||either('MAX не достигнут','MAX was not reached')),building:current};exploreE3Stage('tier',either('Переход по тирам','Tier progression'),'done','MAX');return {status:'completed',building:current};"""
assert s.count(old_instant_success)==1, s.count(old_instant_success)
s=s.replace(old_instant_success,new_instant_success,1)

old_events="""      if(!exploreE3EventsFinished(Array.isArray(current?.events)?current.events:[])){
        if(exploreTierModes(Number(exploreState()?.player?.level||0))[tier]!=='fast')return {status:'skipped',reason:either('На этом тире недоступно быстрое исследование','Fast completion is unavailable at this tier'),building:current};
        hkRunner.setStep(either('Проверка стоимости быстрого исследования','Checking fast-completion cost'),0,1);const costDoc=await apiJson('/player/building/fast_completion/cost','POST',{building_id:buildingId}),costData=costDoc?.fast_building_completion_cost||{};"""
new_events="""      if(!exploreE3EventsFinished(Array.isArray(current?.events)?current.events:[])){
        exploreE3Stage('events',either('Исследование событий','Explore events'),'running',exploreTierLabel(tier));
        if(exploreTierModes(Number(exploreState()?.player?.level||0))[tier]!=='fast')return {status:'skipped',reason:either('На этом тире недоступно быстрое исследование','Fast completion is unavailable at this tier'),building:current};
        hkRunner.setStep(either('Проверка стоимости быстрого исследования','Checking fast-completion cost'),0,1);const costDoc=await apiJson('/player/building/fast_completion/cost','POST',{building_id:buildingId}),costData=costDoc?.fast_building_completion_cost||{};"""
assert s.count(old_events)==1, s.count(old_events)
s=s.replace(old_events,new_events,1)

old_fast_done="""        if(res.error&&!exploreE3EventsFinished(current?.events||[]))return {status:'failed',reason:res.error?.message||String(res.error),building:current};await exploreE3Delay(settings,'action');continue;
      }
      if(atTarget&&!settings.exploreTargetBattles)return {status:'completed',building:current};"""
new_fast_done="""        if(res.error&&!exploreE3EventsFinished(current?.events||[]))return {status:'failed',reason:res.error?.message||String(res.error),building:current};if(exploreE3EventsFinished(current?.events||[]))exploreE3Stage('events',either('Исследование событий','Explore events'),'done',exploreTierLabel(tier));await exploreE3Delay(settings,'action');continue;
      }
      exploreE3Stage('events',either('Исследование событий','Explore events'),'done',exploreTierLabel(tier));
      if(atTarget&&!settings.exploreTargetBattles){exploreE3Stage('battles',either('Бои','Battles'),'skipped',either('отключены на целевом тире','disabled at target tier'));exploreE3Stage('tier',either('Переход по тирам','Tier progression'),'done',exploreTierLabel(tier));return {status:'completed',building:current};}"""
assert s.count(old_fast_done)==1, s.count(old_fast_done)
s=s.replace(old_fast_done,new_fast_done,1)

old_battles="""      if(Number(current?.battle_level||0)<Number(current?.max_battle_level||0)){
        const before=Number(current?.battle_level||0),auto=exploreAutoTier(exploreConsigliere(exploreState()));"""
new_battles="""      if(Number(current?.battle_level||0)<Number(current?.max_battle_level||0)){
        exploreE3Stage('battles',either('Бои','Battles'),'running',Number(current?.battle_level||0)+'/'+Number(current?.max_battle_level||0));
        const before=Number(current?.battle_level||0),auto=exploreAutoTier(exploreConsigliere(exploreState()));"""
assert s.count(old_battles)==1, s.count(old_battles)
s=s.replace(old_battles,new_battles,1)

old_auto_continue="""          if(Number(current?.battle_level||0)>before){await exploreE3Delay(settings,'battle');continue;}"""
new_auto_continue="""          if(Number(current?.battle_level||0)>before){if(Number(current?.battle_level||0)>=Number(current?.max_battle_level||0))exploreE3Stage('battles',either('Бои','Battles'),'done',Number(current?.battle_level||0)+'/'+Number(current?.max_battle_level||0));else exploreE3Stage('battles',either('Бои','Battles'),'running',Number(current?.battle_level||0)+'/'+Number(current?.max_battle_level||0));await exploreE3Delay(settings,'battle');continue;}"""
assert s.count(old_auto_continue)==1, s.count(old_auto_continue)
s=s.replace(old_auto_continue,new_auto_continue,1)

old_manual_loop="""      await hkRunner.waitIfPaused();const before=Number(current?.battle_level||0);hkRunner.setStep(either('Ручной бой','Manual battle')+' · '+before+'/'+Number(current?.max_battle_level||0),0,1);"""
new_manual_loop="""      await hkRunner.waitIfPaused();const before=Number(current?.battle_level||0);exploreE3Stage('battles',either('Бои','Battles'),'running',before+'/'+Number(current?.max_battle_level||0));hkRunner.setStep(either('Ручной бой','Manual battle')+' · '+before+'/'+Number(current?.max_battle_level||0),0,1);"""
assert s.count(old_manual_loop)==1, s.count(old_manual_loop)
s=s.replace(old_manual_loop,new_manual_loop,1)

old_manual_return="""    return {ok:Number(current?.battle_level||0)>=Number(current?.max_battle_level||0),building:current,reason:either('Бои не завершены','Battles not completed')};"""
new_manual_return="""    const ok=Number(current?.battle_level||0)>=Number(current?.max_battle_level||0);exploreE3Stage('battles',either('Бои','Battles'),ok?'done':'error',Number(current?.battle_level||0)+'/'+Number(current?.max_battle_level||0));return {ok,building:current,reason:either('Бои не завершены','Battles not completed')};"""
assert s.count(old_manual_return)==1, s.count(old_manual_return)
s=s.replace(old_manual_return,new_manual_return,1)

old_after_battle="""        const manual=await exploreE3ManualBattles(current,settings);if(!manual.ok)return {status:'skipped',reason:manual.reason,building:manual.building||current};current=manual.building;continue;
      }
      if(!exploreE3EventsFinished(current?.events||[])){current=await exploreE3Detail(buildingId);continue;}
      if(atTarget)return {status:'completed',building:current};
      hkRunner.setStep(either('Подготовка следующего тира','Preparing next tier'),0,1);"""
new_after_battle="""        const manual=await exploreE3ManualBattles(current,settings);if(!manual.ok)return {status:'skipped',reason:manual.reason,building:manual.building||current};current=manual.building;continue;
      }
      exploreE3Stage('battles',either('Бои','Battles'),'done',Number(current?.battle_level||0)+'/'+Number(current?.max_battle_level||0));
      if(!exploreE3EventsFinished(current?.events||[])){current=await exploreE3Detail(buildingId);continue;}
      if(atTarget){exploreE3Stage('tier',either('Переход по тирам','Tier progression'),'done',exploreTierLabel(tier));return {status:'completed',building:current};}
      exploreE3Stage('tier',either('Переход по тирам','Tier progression'),'running',exploreTierLabel(tier)+' → '+exploreTierLabel(tier+1));
      hkRunner.setStep(either('Подготовка следующего тира','Preparing next tier'),0,1);"""
assert s.count(old_after_battle)==1, s.count(old_after_battle)
s=s.replace(old_after_battle,new_after_battle,1)

old_remort_done="""      if(Number(current?.tier||0)<=beforeTier)return {status:'failed',reason:res.error?.message||either('Тир не повысился','Tier did not increase'),building:current};await exploreE3Delay(settings,'action');"""
new_remort_done="""      if(Number(current?.tier||0)<=beforeTier)return {status:'failed',reason:res.error?.message||either('Тир не повысился','Tier did not increase'),building:current};exploreE3Stage('tier',either('Переход по тирам','Tier progression'),'done',exploreTierLabel(Number(current?.tier||0)));await exploreE3Delay(settings,'action');"""
assert s.count(old_remort_done)==1, s.count(old_remort_done)
s=s.replace(old_remort_done,new_remort_done,1)

old_run_start="""      hkRunner.start({title:either('Исследование · E3','Explore · E3'),total:1,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});
      const result=await exploreE3ProcessOne(candidate,settings);
      await exploreE3Reconcile(String(candidate.id||''),'explore:e3-final');
      if(result.status==='completed'){hkRunner.advance(either('Здание завершено','Building completed'));hkRunner.note(either('Тестовое здание успешно обработано','Test building processed successfully'),'ok');hkRunner.finish(either('E3 завершён','E3 completed'));log(either('E3: одно здание успешно обработано','E3: one building processed successfully'),'ok');}
      else{const msg=(result.reason||result.status);hkRunner.note(msg,result.status==='skipped'||result.status==='resources_exhausted'?'warn':'bad');hkRunner.fail(new Error(msg));log(either('E3 остановлен: ','E3 stopped: ')+msg,'warn');}"""
new_run_start="""      hkRunner.start({title:either('Исследование · E3','Explore · E3'),total:1,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});
      exploreE3InitStages(candidate,total);
      const result=await exploreE3ProcessOne(candidate,settings);
      exploreE3Stage('verify',either('Финальная проверка','Final verification'),'running');
      await exploreE3Reconcile(String(candidate.id||''),'explore:e3-final');
      if(result.status==='completed'){exploreE3Stage('verify',either('Финальная проверка','Final verification'),'done',either('состояние подтверждено','state confirmed'));hkRunner.advance(either('Здание завершено','Building completed'));hkRunner.finish(either('E3 завершён','E3 completed'));log(either('E3: одно здание успешно обработано','E3: one building processed successfully'),'ok');}
      else{const msg=(result.reason||result.status),st=result.status==='skipped'||result.status==='resources_exhausted'?'skipped':'error';exploreE3CloseRunning(st,msg);exploreE3Stage('verify',either('Финальная проверка','Final verification'),st,msg);hkRunner.fail(new Error(msg));log(either('E3 остановлен: ','E3 stopped: ')+msg,'warn');}"""
assert s.count(old_run_start)==1, s.count(old_run_start)
s=s.replace(old_run_start,new_run_start,1)

old_catch="""    }catch(e){if(e?.name==='AbortError'){hkRunner.reset();log(either('E3 остановлен пользователем','E3 stopped by user'),'warn');}else{hkRunner.fail(e);log(either('Ошибка E3: ','E3 error: ')+(e?.message||e),'bad');}}"""
new_catch="""    }catch(e){if(e?.name==='AbortError'){exploreE3CloseRunning('skipped',either('остановлено пользователем','stopped by user'));exploreE3Stage('verify',either('Финальная проверка','Final verification'),'skipped',either('остановлено','stopped'));hkRunner.fail(new Error(either('Остановлено пользователем','Stopped by user')));log(either('E3 остановлен пользователем','E3 stopped by user'),'warn');}else{exploreE3CloseRunning('error',e?.message||String(e));exploreE3Stage('verify',either('Финальная проверка','Final verification'),'error',e?.message||String(e));hkRunner.fail(e);log(either('Ошибка E3: ','E3 error: ')+(e?.message||e),'bad');}}"""
assert s.count(old_catch)==1, s.count(old_catch)
s=s.replace(old_catch,new_catch,1)

assert "explore-e3-single-20260920-r9-runner" in s
assert "box.classList.toggle('explore-run'" in s
assert "function exploreE3Stage(" in s
assert "stage-running" in s and "stage-done" in s
assert "const HK_MAP_READ_CONCURRENCY = 5;" in s
p.write_text(s)
