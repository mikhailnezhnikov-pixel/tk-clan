from pathlib import Path

PATH=Path("/tmp/HamsterKingMobile.user.js")
s=PATH.read_text(encoding="utf-8")
MARKER="auto-routines-safe-orchestrator-20260922-r2"

if MARKER in s:
    print("AUTO_ROUTINES_SAFE_ORCHESTRATOR_ALREADY_PRESENT")
    raise SystemExit(0)

for required in [
    "// @version      1.17.33",
    "const BUILD_VERSION = '1.17.33';",
    "clan-shop-dom-history-capture-20260922-r3",
    "auto-routines-20260920-r1",
    "game-api-rate-guard-20260922-r1",
    "public-collector-activity-lease-20260922-r1",
    "businesses-kokkaras-donor-20260922-r1",
    "async function runAutoRoutine()",
    "function stopAutoRoutine()",
    "function notePublicCollectorRunnerActivity(",
]:
    if required not in s:
        raise SystemExit("missing marker: "+required)

s=s.replace("// @version      1.17.33","// @version      1.17.34",1)
s=s.replace("const BUILD_VERSION = '1.17.33';","const BUILD_VERSION = '1.17.34';",1)

release_anchor="// @release-note Clan Shop дополнительно считывает видимые строки журнала покупок с экрана игры, если API-ответ не содержит удобной структуры истории."
release_new="// @release-note Auto Routines теперь fail-closed: следующий этап запускается только после реального Runner=done; error/stop/cancel/no-op останавливают цепочку. Collector lease удерживается непрерывно на всю рутину."
if release_anchor not in s:
    raise SystemExit("release anchor missing")
s=s.replace(release_anchor,release_new+"\n"+release_anchor,1)

rev_anchor="  const HK_AUTO_ROUTINES_REV = 'auto-routines-20260920-r1';"
if rev_anchor not in s:
    raise SystemExit("auto routines revision anchor missing")
s=s.replace(rev_anchor,rev_anchor+"\n  const HK_AUTO_ROUTINES_SAFE_REV = 'auto-routines-safe-orchestrator-20260922-r2';",1)

activity_anchor="  const PUBLIC_COLLECTOR_ACTIVITY_HEARTBEAT_MS = 20 * 1000;"
if activity_anchor not in s:
    raise SystemExit("collector activity anchor missing")
s=s.replace(activity_anchor,activity_anchor+"\n  let autoRoutineLeaseHold = false;",1)

old_note=r'''  function notePublicCollectorRunnerActivity(state=hkRunner.state) {
    const active=['running','paused','stopping'].includes(String(state?.status||''));
    if(active){
      void syncPublicCollectorActivity(true,String(state?.title||'automation'),false);
    }else if(publicCollectorActivityLastActive===true){
      void syncPublicCollectorActivity(false,String(state?.title||'idle'),true);
    }
  }
'''
new_note=r'''  function notePublicCollectorRunnerActivity(state=hkRunner.state) {
    const runnerActive=['running','paused','stopping'].includes(String(state?.status||''));
    const active=runnerActive||autoRoutineLeaseHold;
    if(active){
      const reason=autoRoutineLeaseHold ? 'auto-routine' : String(state?.title||'automation');
      void syncPublicCollectorActivity(true,reason,false);
    }else if(publicCollectorActivityLastActive===true){
      void syncPublicCollectorActivity(false,String(state?.title||'idle'),true);
    }
  }
'''
if old_note not in s:
    raise SystemExit("collector activity function anchor missing")
s=s.replace(old_note,new_note,1)

old_heartbeat="    setInterval(() => { if (hkRunner.running) void syncPublicCollectorActivity(true,String(hkRunner.state.title||'automation'),true); }, PUBLIC_COLLECTOR_ACTIVITY_HEARTBEAT_MS);"
new_heartbeat="    setInterval(() => { if (hkRunner.running||autoRoutineLeaseHold) void syncPublicCollectorActivity(true,autoRoutineLeaseHold?'auto-routine':String(hkRunner.state.title||'automation'),true); }, PUBLIC_COLLECTOR_ACTIVITY_HEARTBEAT_MS);"
if old_heartbeat not in s:
    raise SystemExit("collector activity heartbeat anchor missing")
s=s.replace(old_heartbeat,new_heartbeat,1)

auto_anchor="  let autoRoutineRunning = false;\n  let autoRoutineStop = false;\n  let autoRoutineCurrent = '';\n"
auto_new=auto_anchor+"  let autoRoutineLastResult = null;\n"
if auto_anchor not in s:
    raise SystemExit("auto routine state anchor missing")
s=s.replace(auto_anchor,auto_new,1)

stop_start=s.index("  function stopAutoRoutine() {")
run_start=s.index("  async function runAutoRoutine() {",stop_start)
apply_start=s.index("  function applyLanguage() {",run_start)
if stop_start<0 or run_start<0 or apply_start<0:
    raise SystemExit("auto routine function slice missing")

safe_module=r'''  function stopAutoRoutine() {
    if(!autoRoutineRunning)return;
    autoRoutineStop=true;
    if(hkRunner.running)hkRunner.stop('auto-routine');
    log(either('Останавливаю авто-рутину после текущего этапа…','Stopping auto routine after the current stage…'),'warn');
    renderAutoRoutines();
  }

  function autoRoutineActionLabel(action) {
    return language==='en' ? String(action?.en||action?.id||'stage') : String(action?.ru||action?.id||'этап');
  }

  function autoRoutineRunnerSnapshot() {
    return {
      status:String(hkRunner.state?.status||'idle'),
      title:String(hkRunner.state?.title||''),
      step:String(hkRunner.state?.step||''),
      error:String(hkRunner.state?.error||''),
      startedAt:Number(hkRunner.state?.startedAt||0),
      done:Number(hkRunner.state?.done||0),
      total:Number(hkRunner.state?.total||0),
    };
  }

  function autoRoutineStageError(action,message,status='error') {
    const label=autoRoutineActionLabel(action);
    const error=new Error(label+': '+String(message||either('этап не завершён','stage did not complete')));
    error.name='HKAutoRoutineStageError';
    error.stageId=String(action?.id||'');
    error.stageStatus=status;
    return error;
  }

  async function autoRoutineRunStage(action) {
    if(gameApiCooldownRemainingMs()>0){
      const seconds=Math.max(1,Math.ceil(gameApiCooldownRemainingMs()/1000));
      throw autoRoutineStageError(action,either(
        'Game API на cooldown ещё '+seconds+' сек.',
        'Game API cooldown has '+seconds+' sec. remaining'
      ),'cooldown');
    }

    const before=autoRoutineRunnerSnapshot();
    await action.run();

    if(autoRoutineStop)return {status:'stopped',started:false,snapshot:autoRoutineRunnerSnapshot()};

    while(hkRunner.running&&!autoRoutineStop)await sleep(150);
    if(autoRoutineStop)return {status:'stopped',started:true,snapshot:autoRoutineRunnerSnapshot()};

    const after=autoRoutineRunnerSnapshot();
    const started=after.startedAt>0&&after.startedAt!==before.startedAt;
    if(!started){
      return {
        status:'not-started',
        started:false,
        snapshot:after,
        message:either(
          'этап не запустился: отменено подтверждение, нет выбранных действий или не выполнены условия запуска',
          'stage did not start: confirmation was cancelled, no actions are selected, or preconditions were not met'
        )
      };
    }
    if(after.status==='done')return {status:'done',started:true,snapshot:after};
    if(after.status==='error'){
      return {status:'error',started:true,snapshot:after,message:after.error||either('ошибка этапа','stage error')};
    }
    if(after.status==='idle'){
      return {status:'stopped',started:true,snapshot:after,message:either('этап был остановлен','stage was stopped')};
    }
    return {
      status:after.status||'unknown',
      started:true,
      snapshot:after,
      message:after.error||after.step||either('неизвестный финальный статус этапа','unknown final stage status')
    };
  }

  async function autoRoutineAcquireCollectorLease() {
    autoRoutineLeaseHold=true;
    if(!licenseState.publicCollectorAuthSync)return true;
    const ok=await syncPublicCollectorActivity(true,'auto-routine',true);
    if(ok)return true;
    autoRoutineLeaseHold=false;
    return false;
  }

  async function autoRoutineReleaseCollectorLease(reason='auto-routine-finished') {
    autoRoutineLeaseHold=false;
    if(licenseState.publicCollectorAuthSync)await syncPublicCollectorActivity(false,reason,true);
  }

  async function runAutoRoutine() {
    if(!requireLicense()||autoRoutineRunning)return;
    if(hkRunner.running){alert(either('Сначала завершите текущую задачу','Finish the current task first'));return;}
    if(gameApiCooldownRemainingMs()>0){
      const seconds=Math.max(1,Math.ceil(gameApiCooldownRemainingMs()/1000));
      alert(either(
        'Game API ещё на cooldown. Подождите '+seconds+' сек. перед запуском авто-рутины.',
        'Game API is still cooling down. Wait '+seconds+' sec. before starting the auto routine.'
      ));
      return;
    }

    const selection=autoRoutineSelection();
    const queue=AUTO_ROUTINE_ACTIONS.filter(row=>selection[row.id]);
    if(!queue.length)return;
    if(!confirm(either(
      'Запустить авто-рутину из '+queue.length+' этапов?\n\nСледующий этап начнётся только если предыдущий реально завершился успешно. Ошибка, Stop, отмена подтверждения или незапущенный этап остановят цепочку.',
      'Run an auto routine with '+queue.length+' stages?\n\nThe next stage starts only after the previous stage actually completes successfully. Error, Stop, cancelled confirmation, or a stage that did not start will stop the sequence.'
    )))return;

    autoRoutineRunning=true;
    autoRoutineStop=false;
    autoRoutineCurrent='';
    autoRoutineLastResult=null;
    renderAutoRoutines();

    let completed=0;
    let leaseAcquired=false;
    try{
      leaseAcquired=await autoRoutineAcquireCollectorLease();
      if(!leaseAcquired)throw new Error(either(
        'Не удалось поставить server collector на паузу. Авто-рутина не запущена.',
        'Could not pause the server collector. Auto routine was not started.'
      ));

      for(const action of queue){
        if(autoRoutineStop)break;
        if(hkRunner.running)throw new Error(either('Предыдущая задача ещё не завершена','The previous task is still running'));

        autoRoutineCurrent=action.id;
        renderAutoRoutines();
        const label=autoRoutineActionLabel(action);
        log(either('Авто-рутина: ','Auto routine: ')+label);

        const result=await autoRoutineRunStage(action);
        autoRoutineLastResult={...result,actionId:action.id,label,at:Date.now()};
        renderAutoRoutines();

        if(result.status==='stopped'){
          autoRoutineStop=true;
          log(either('Авто-рутина остановлена на этапе: ','Auto routine stopped at stage: ')+label,'warn');
          break;
        }
        if(result.status!=='done'){
          throw autoRoutineStageError(action,result.message||result.status,result.status);
        }

        completed+=1;
        log(either('Этап подтверждён: ','Stage confirmed: ')+label,'ok');
        if(completed<queue.length)await sleep(500);
      }

      log(autoRoutineStop
        ? either('Авто-рутина остановлена: завершено ','Auto routine stopped: completed ')+completed+'/'+queue.length
        : either('Авто-рутина завершена: ','Auto routine completed: ')+completed+'/'+queue.length,
        autoRoutineStop?'warn':'ok');
    }catch(error){
      autoRoutineLastResult={
        status:'error',
        actionId:autoRoutineCurrent,
        label:autoRoutineActionLabel(AUTO_ROUTINE_ACTIONS.find(row=>row.id===autoRoutineCurrent)),
        message:String(error?.message||error),
        at:Date.now()
      };
      log(either('Авто-рутина остановлена ошибкой','Auto routine stopped by an error')+': '+(error?.message||error),'bad');
    }finally{
      if(leaseAcquired||autoRoutineLeaseHold){
        try{await autoRoutineReleaseCollectorLease(autoRoutineStop?'auto-routine-stopped':'auto-routine-finished');}
        catch(error){recordDiagnostic('auto-routine-lease-release-error',{error:error?.message||error});}
      }
      autoRoutineRunning=false;
      autoRoutineStop=false;
      autoRoutineCurrent='';
      renderAutoRoutines();
    }
  }

'''
s=s[:stop_start]+safe_module+s[apply_start:]

# Add a compact last-result line to the existing Auto Routines UI.
ui_anchor=r'''      '<p class="hk-muted">'+(autoRoutineRunning
        ? either('Текущий этап: ','Current stage: ')+escapeHtml(current?(language==='en'?current.en:current.ru):either('подготовка','preparing'))
        : either('Выбрано этапов: ','Selected stages: ')+selectedCount)+'</p>';
'''
ui_new=r'''      '<p class="hk-muted">'+(autoRoutineRunning
        ? either('Текущий этап: ','Current stage: ')+escapeHtml(current?(language==='en'?current.en:current.ru):either('подготовка','preparing'))
        : either('Выбрано этапов: ','Selected stages: ')+selectedCount)+'</p>'+
      (autoRoutineLastResult
        ? '<p class="hk-muted">'+escapeHtml(
            (autoRoutineLastResult.status==='done'?either('Последний этап ✓ ','Last stage ✓ '):either('Последний результат: ','Last result: '))+
            String(autoRoutineLastResult.label||'')+
            (autoRoutineLastResult.message?' · '+String(autoRoutineLastResult.message):'')
          )+'</p>'
        : '');
'''
if ui_anchor not in s:
    raise SystemExit("auto routine UI result anchor missing")
s=s.replace(ui_anchor,ui_new,1)

for marker in [
    "// @version      1.17.34",
    "const BUILD_VERSION = '1.17.34';",
    "HK_AUTO_ROUTINES_SAFE_REV = 'auto-routines-safe-orchestrator-20260922-r2'",
    "let autoRoutineLeaseHold = false;",
    "runnerActive||autoRoutineLeaseHold",
    "hkRunner.running||autoRoutineLeaseHold",
    "let autoRoutineLastResult = null;",
    "function autoRoutineRunnerSnapshot()",
    "function autoRoutineStageError(",
    "async function autoRoutineRunStage(",
    "async function autoRoutineAcquireCollectorLease(",
    "async function autoRoutineReleaseCollectorLease(",
    "result.status!=='done'",
    "after.startedAt!==before.startedAt",
    "clan-shop-dom-history-capture-20260922-r3",
    "game-api-rate-guard-20260922-r1",
    "public-collector-activity-lease-20260922-r1",
    "businesses-kokkaras-donor-20260922-r1",
]:
    if marker not in s:
        raise SystemExit("post-patch marker missing: "+marker)

# Old unsafe completion rule must be gone from Auto Routines block.
auto_start=s.index("  let autoRoutineRunning = false;")
auto_end=s.index("  function applyLanguage() {",auto_start)
auto_block=s[auto_start:auto_end]
if "completed+=1;\n        await sleep(250);" in auto_block:
    raise SystemExit("old blind completion rule still present")
if "while(hkRunner.running&&!autoRoutineStop)await sleep(150);" not in auto_block:
    raise SystemExit("runner wait missing")
if "if(result.status!=='done')" not in auto_block:
    raise SystemExit("fail-closed stage gate missing")

PATH.write_text(s,encoding="utf-8")
print("AUTO_ROUTINES_SAFE_ORCHESTRATOR_R2=PASS")
