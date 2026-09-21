from pathlib import Path

PATH=Path("/tmp/HamsterKingMobile.user.js")
s=PATH.read_text(encoding="utf-8")

required=[
    "// @version      1.17.20",
    "const BUILD_VERSION = '1.17.20';",
    "const HK_CORE_REVISION = 'core-20260921-r22-explore-speed-tune';",
    "const HK_EXPLORE_SPEED_REV='explore-e3-speed-20260921-r1';",
    "async function exploreE3ProcessOne(initial,settings)",
    "async function runExploreE3Single()",
    "function renderExplore()",
]
for marker in required:
    if marker not in s:
        raise SystemExit(f"missing expected marker: {marker}")

s=s.replace("// @version      1.17.20","// @version      1.17.21",1)
s=s.replace(
    "// @release-note Исследование E3 слегка ускорено: стандартные паузы между действиями и боями уменьшены без снятия проверок состояния.",
    "// @release-note Добавлена безопасная очередь исследования E4 с лимитом 1 / 5 / 10 / 15 / 20 / все выбранные.\n"
    "// @release-note Исследование E3 слегка ускорено: стандартные паузы между действиями и боями уменьшены без снятия проверок состояния.",
    1,
)
s=s.replace("const BUILD_VERSION = '1.17.20';","const BUILD_VERSION = '1.17.21';",1)
s=s.replace(
    "const HK_CORE_REVISION = 'core-20260921-r22-explore-speed-tune';",
    "const HK_CORE_REVISION = 'core-20260921-r23-explore-e4-queue';",
    1,
)
s=s.replace(
    "const HK_EXPLORE_SPEED_REV='explore-e3-speed-20260921-r1';",
    "const HK_EXPLORE_SPEED_REV='explore-e3-speed-20260921-r1';\n"
    "  const HK_EXPLORE_E4_REV='explore-e4-queue-20260921-r1';",
    1,
)

old_settings_return="""      speedProfileRev:HK_EXPLORE_SPEED_REV,
      exploreTargetTier:targetActionsAllowed,exploreTargetBattles:targetActionsAllowed&&x.exploreTargetBattles===true
    };
"""
new_settings_return="""      speedProfileRev:HK_EXPLORE_SPEED_REV,
      runLimit:[1,5,10,15,20].includes(Number(x.runLimit))||Number(x.runLimit)===0?Number(x.runLimit):1,
      exploreTargetTier:targetActionsAllowed,exploreTargetBattles:targetActionsAllowed&&x.exploreTargetBattles===true
    };
"""
if old_settings_return not in s:
    raise SystemExit("settings return anchor missing")
s=s.replace(old_settings_return,new_settings_return,1)

old_save_tail="""    x.speedProfileRev=HK_EXPLORE_SPEED_REV;
    x.exploreTargetTier=targetActionsAllowed;if(!x.exploreTargetTier)x.exploreTargetBattles=false;
"""
new_save_tail="""    x.speedProfileRev=HK_EXPLORE_SPEED_REV;
    x.runLimit=[1,5,10,15,20].includes(Number(x.runLimit))||Number(x.runLimit)===0?Number(x.runLimit):1;
    x.exploreTargetTier=targetActionsAllowed;if(!x.exploreTargetTier)x.exploreTargetBattles=false;
"""
if old_save_tail not in s:
    raise SystemExit("save tail anchor missing")
s=s.replace(old_save_tail,new_save_tail,1)

old_read_tail="""      buyMissingMaterials:!!b.querySelector('#hk-ex-buy')?.checked,exploreTargetTier:!!b.querySelector('#hk-ex-target-tier')?.checked,
      exploreTargetBattles:!!b.querySelector('#hk-ex-target-battles')?.checked
"""
new_read_tail="""      buyMissingMaterials:!!b.querySelector('#hk-ex-buy')?.checked,
      runLimit:String(b.querySelector('#hk-ex-run-limit')?.value||'1')==='all'?0:Number(b.querySelector('#hk-ex-run-limit')?.value||1),
      exploreTargetTier:!!b.querySelector('#hk-ex-target-tier')?.checked,
      exploreTargetBattles:!!b.querySelector('#hk-ex-target-battles')?.checked
"""
if old_read_tail not in s:
    raise SystemExit("read settings tail anchor missing")
s=s.replace(old_read_tail,new_read_tail,1)

old_init="""  function exploreE3InitStages(candidate,total){
    const target=exploreTierLabel(exploreSettings().targetTier);
    exploreE3Stage('prepare',either('Чтение состояния здания','Read building state'),'running',either('тест 1 из ','test 1 of ')+total);
"""
new_init="""  function exploreE3InitStages(candidate,total,index=1){
    const target=exploreTierLabel(exploreSettings().targetTier);
    exploreE3Stage('prepare',either('Чтение состояния здания','Read building state'),'running',either('здание ','building ')+index+'/'+total);
"""
if old_init not in s:
    raise SystemExit("E3 init stages anchor missing")
s=s.replace(old_init,new_init,1)

delay_anchor="""  async function exploreE3Delay(settings,type){
    const ms=type==='battle'?Math.max(0,Number(settings?.battleDelayMs||0)):exploreE3Random(settings?.actionDelayMinMs,settings?.actionDelayMaxMs);
    if(ms>0)await sleep(ms);await hkRunner.waitIfPaused();
  }
"""
delay_new=delay_anchor+"""  async function exploreE4BetweenDelay(settings){
    const ms=exploreE3Random(settings?.betweenBuildingsDelayMinMs,settings?.betweenBuildingsDelayMaxMs);
    if(ms>0)await sleep(ms);
    await hkRunner.waitIfPaused();
  }
"""
if delay_anchor not in s:
    raise SystemExit("delay anchor missing")
s=s.replace(delay_anchor,delay_new,1)

single_end="""    finally{exploreBusy=false;renderExplore();}
  }

  function explorePrOptions"""
if single_end not in s:
    raise SystemExit("single runner end anchor missing")

e4_func="""    finally{exploreBusy=false;renderExplore();}
  }

  async function runExploreE4Queue(){
    if(!requireLicense()||exploreBusy||hkRunner.running)return;
    const settings=exploreReadSettings();
    exploreBusy=true;exploreE3ShopLots=null;renderExplore();
    try{
      explorePlan=await exploreBuildPlan();
      const source=Array.isArray(explorePlan?.selected)?explorePlan.selected:[];
      if(!source.length){log(either('Нет зданий для очереди E4','No buildings for the E4 queue'),'warn');return;}
      const limit=Number(settings.runLimit);
      const queue=limit===0?source:source.slice(0,Math.max(1,limit||1));
      const ok=confirm(either(
        'E4: обработать '+queue.length+' из '+source.length+' выбранных зданий последовательно?',
        'E4: process '+queue.length+' of '+source.length+' selected buildings sequentially?'
      ));
      if(!ok)return;

      hkRunner.start({title:either('Исследование · E4','Explore · E4'),total:queue.length,step:either('Подготовка очереди','Preparing queue'),pausable:true,stoppable:true});
      let completed=0,skipped=0,failed='';
      for(let i=0;i<queue.length;i++){
        await hkRunner.waitIfPaused();
        const candidate=queue[i];
        hkRunner.setStep(either('Здание ','Building ')+(i+1)+'/'+queue.length,i,queue.length);
        hkRunner.state.history=[];
        exploreE3InitStages(candidate,queue.length,i+1);

        const result=await exploreE3ProcessOne(candidate,settings);
        exploreE3Stage('verify',either('Финальная проверка','Final verification'),'running');
        await exploreE3Reconcile(String(candidate.id||''),'explore:e4-final-'+(i+1));

        if(result.status==='completed'){
          completed++;
          exploreE3Stage('verify',either('Финальная проверка','Final verification'),'done',either('состояние подтверждено','state confirmed'));
          hkRunner.advance(either('Здание ','Building ')+(i+1)+'/'+queue.length+' · '+either('готово','done'));
        }else if(result.status==='skipped'){
          skipped++;
          const msg=result.reason||either('пропущено','skipped');
          exploreE3CloseRunning('skipped',msg);
          exploreE3Stage('verify',either('Финальная проверка','Final verification'),'skipped',msg);
          hkRunner.advance(either('Здание ','Building ')+(i+1)+'/'+queue.length+' · '+either('пропущено','skipped'));
          log(either('E4: здание пропущено: ','E4: building skipped: ')+msg,'warn');
        }else{
          failed=result.reason||result.status||either('Неизвестная ошибка','Unknown error');
          const st=result.status==='resources_exhausted'?'skipped':'error';
          exploreE3CloseRunning(st,failed);
          exploreE3Stage('verify',either('Финальная проверка','Final verification'),st,failed);
          break;
        }

        if(i<queue.length-1)await exploreE4BetweenDelay(settings);
      }

      exploreMeta=await exploreLoadMeta(true,exploreState());
      explorePlan=null;

      if(failed){
        hkRunner.fail(new Error(failed));
        log(either('E4 остановлен: ','E4 stopped: ')+failed,'warn');
      }else{
        hkRunner.finish(either('E4 завершён','E4 completed')+' · '+completed+' '+either('готово','done')+(skipped?' · '+skipped+' '+either('пропущено','skipped'):''));
        log(either('E4: очередь завершена','E4: queue completed')+' · '+completed+'/'+queue.length,'ok');
      }
    }catch(e){
      if(e?.name==='AbortError'){
        exploreE3CloseRunning('skipped',either('остановлено пользователем','stopped by user'));
        exploreE3Stage('verify',either('Финальная проверка','Final verification'),'skipped',either('остановлено','stopped'));
        hkRunner.fail(new Error(either('Остановлено пользователем','Stopped by user')));
        log(either('E4 остановлен пользователем','E4 stopped by user'),'warn');
      }else{
        exploreE3CloseRunning('error',e?.message||String(e));
        exploreE3Stage('verify',either('Финальная проверка','Final verification'),'error',e?.message||String(e));
        hkRunner.fail(e);
        log(either('Ошибка E4: ','E4 error: ')+(e?.message||e),'bad');
      }
    }finally{
      exploreBusy=false;
      renderExplore();
    }
  }

  function explorePrOptions"""
s=s.replace(single_end,e4_func,1)

old_render_head="""  function renderExplore(){
    const box=root?.querySelector('#hk-explore-content');if(!box)return;const s=exploreSettings(),p=explorePlan,st=exploreState(),ready=!!st?.player&&(Array.isArray(st?.buildings)||Array.isArray(st?.player?.buildings)),active=ready?exploreActive(st):[],c=p?.consigliere||(ready?exploreConsigliere(st):null);
"""
new_render_head="""  function renderExplore(){
    const box=root?.querySelector('#hk-explore-content');if(!box)return;const s=exploreSettings(),p=explorePlan,st=exploreState(),ready=!!st?.player&&(Array.isArray(st?.buildings)||Array.isArray(st?.player?.buildings)),active=ready?exploreActive(st):[],c=p?.consigliere||(ready?exploreConsigliere(st):null);
    const queueCount=p?Math.min(p.selected.length,s.runLimit===0?Number.MAX_SAFE_INTEGER:s.runLimit):0;
"""
if old_render_head not in s:
    raise SystemExit("render head anchor missing")
s=s.replace(old_render_head,new_render_head,1)

old_plan="""    const planHtml=p?'<div class="hk-cardbox"><b>'+either('План','Plan')+'</b><p><strong>'+either('Будет обработано зданий: ','Buildings to process: ')+p.selected.length+'</strong></p><p class="hk-muted">'+either('После фильтров','After filters')+': '+p.filteredCount+' · '+either('кандидатов','candidates')+': '+p.candidates.length+'</p>'+
"""
new_plan="""    const planHtml=p?'<div class="hk-cardbox"><b>'+either('План','Plan')+'</b><p><strong>'+either('Выбрано планом: ','Selected by plan: ')+p.selected.length+' · '+either('К запуску E4: ','E4 queue: ')+queueCount+'</strong></p><p class="hk-muted">'+either('После фильтров','After filters')+': '+p.filteredCount+' · '+either('кандидатов','candidates')+': '+p.candidates.length+'</p>'+
"""
if old_plan not in s:
    raise SystemExit("plan html anchor missing")
s=s.replace(old_plan,new_plan,1)

old_grid="'#hk-explore-content .hk-ex-filter-grid{display:grid;grid-template-columns:repeat(4,minmax(150px,1fr));gap:10px;margin-top:10px}'+"
new_grid="'#hk-explore-content .hk-ex-filter-grid{display:grid;grid-template-columns:repeat(5,minmax(140px,1fr));gap:10px;margin-top:10px}'+"
if old_grid not in s:
    raise SystemExit("filter grid css anchor missing")
s=s.replace(old_grid,new_grid,1)

old_filter_tail="""            '<label class="hk-ex-field"><span>'+either('Максимум зданий','Maximum buildings')+'</span><input id="hk-ex-max" type="number" min="1" max="5000" value="'+s.maxBuildings+'"></label>'+
          '</div>'+
"""
new_filter_tail="""            '<label class="hk-ex-field"><span>'+either('Максимум зданий','Maximum buildings')+'</span><input id="hk-ex-max" type="number" min="1" max="5000" value="'+s.maxBuildings+'"></label>'+
            '<label class="hk-ex-field"><span>'+either('Лимит запуска E4','E4 run limit')+'</span><select id="hk-ex-run-limit"><option value="1" '+(s.runLimit===1?'selected':'')+'>1</option><option value="5" '+(s.runLimit===5?'selected':'')+'>5</option><option value="10" '+(s.runLimit===10?'selected':'')+'>10</option><option value="15" '+(s.runLimit===15?'selected':'')+'>15</option><option value="20" '+(s.runLimit===20?'selected':'')+'>20</option><option value="all" '+(s.runLimit===0?'selected':'')+'>'+either('Все выбранные','All selected')+'</option></select></label>'+
          '</div>'+
"""
if old_filter_tail not in s:
    raise SystemExit("filter grid tail anchor missing")
s=s.replace(old_filter_tail,new_filter_tail,1)

old_actions="""        '<div class="hk-ex-actions"><button id="hk-ex-plan" class="hk-primary" '+(exploreBusy?'disabled':'')+'>'+(exploreBusy?either('Считаю…','Calculating…'):either('Рассчитать план','Calculate plan'))+'</button><button id="hk-ex-run-one" class="hk-secondary" '+(exploreBusy||!p?.selected?.length?'disabled':'')+'>'+either('Запустить тест E3 · 1 здание','Run E3 test · 1 building')+'</button><span id="hk-ex-dirty" class="hk-muted hk-ex-dirty"></span></div>'+
"""
new_actions="""        '<div class="hk-ex-actions"><button id="hk-ex-plan" class="hk-primary" '+(exploreBusy?'disabled':'')+'>'+(exploreBusy?either('Считаю…','Calculating…'):either('Рассчитать план','Calculate plan'))+'</button><button id="hk-ex-run-one" class="hk-secondary" '+(exploreBusy||!p?.selected?.length?'disabled':'')+'>'+either('Тест E3 · 1 здание','E3 test · 1 building')+'</button><button id="hk-ex-run-queue" class="hk-primary" '+(exploreBusy||!p?.selected?.length?'disabled':'')+'>'+(s.runLimit===0?either('Запустить E4 · все выбранные','Run E4 · all selected'):either('Запустить E4 · до '+s.runLimit,'Run E4 · up to '+s.runLimit))+'</button><span id="hk-ex-dirty" class="hk-muted hk-ex-dirty"></span></div>'+
"""
if old_actions not in s:
    raise SystemExit("Explore actions anchor missing")
s=s.replace(old_actions,new_actions,1)

old_listener="""    box.querySelector('#hk-ex-run-one')?.addEventListener('click',()=>void runExploreE3Single());
    box.querySelector('#hk-ex-target')?.addEventListener('change',syncDependencies);
"""
new_listener="""    box.querySelector('#hk-ex-run-one')?.addEventListener('click',()=>void runExploreE3Single());
    box.querySelector('#hk-ex-run-queue')?.addEventListener('click',()=>void runExploreE4Queue());
    box.querySelector('#hk-ex-target')?.addEventListener('change',syncDependencies);
"""
if old_listener not in s:
    raise SystemExit("Explore listener anchor missing")
s=s.replace(old_listener,new_listener,1)

old_finish_line="""      finish(step='') { if(step)state.step=String(step); state.status='done'; if(state.total)state.done=state.total; recordDiagnostic('runner-finish',{title:state.title}); emit(); const keep=String(state.title||'')===either('Исследование · E3','Explore · E3')?15000:1800; setTimeout(()=>{if(state.status==='done'){state.status='idle';emit();}},keep); },
"""
new_finish_line="""      finish(step='') { if(step)state.step=String(step); state.status='done'; if(state.total)state.done=state.total; recordDiagnostic('runner-finish',{title:state.title}); emit(); const exploreTitle=[either('Исследование · E3','Explore · E3'),either('Исследование · E4','Explore · E4')].includes(String(state.title||'')); const keep=exploreTitle?15000:1800; setTimeout(()=>{if(state.status==='done'){state.status='idle';emit();}},keep); },
"""
if old_finish_line not in s:
    raise SystemExit("runner finish anchor missing")
s=s.replace(old_finish_line,new_finish_line,1)

old_render_runner="""    const visibleState=state.status!=='idle',title=String(state.title||''),exploreRun=visibleState&&title===either('Исследование · E3','Explore · E3'),buildingsRun=visibleState&&title===either('Здания','Buildings'); box.classList.toggle('show',visibleState);
"""
new_render_runner="""    const visibleState=state.status!=='idle',title=String(state.title||''),exploreRun=visibleState&&[either('Исследование · E3','Explore · E3'),either('Исследование · E4','Explore · E4')].includes(title),buildingsRun=visibleState&&title===either('Здания','Buildings'); box.classList.toggle('show',visibleState);
"""
if old_render_runner not in s:
    raise SystemExit("render runner explore title anchor missing")
s=s.replace(old_render_runner,new_render_runner,1)

old_state_line="root.querySelector('#hk-runner-state').textContent=buildingsRun&&state.total?"
idx=s.find(old_state_line)
if idx<0:
    raise SystemExit("runner state progress anchor missing")
line_end=s.find("\n",idx)
old_line=s[idx:line_end]
new_line=old_line.replace("buildingsRun&&state.total","(buildingsRun||exploreRun)&&state.total")
s=s[:idx]+new_line+s[line_end:]

for marker in [
    "// @version      1.17.21",
    "const BUILD_VERSION = '1.17.21';",
    "core-20260921-r23-explore-e4-queue",
    "explore-e4-queue-20260921-r1",
    "async function runExploreE4Queue()",
    "const queue=limit===0?source:source.slice(0,Math.max(1,limit||1));",
    "await exploreE4BetweenDelay(settings);",
    "id=\"hk-ex-run-limit\"",
    "id=\"hk-ex-run-queue\"",
    "Запустить E4",
    "Explore · E4",
    "buildings-native-sync-20260921-r1",
    "maps-shared-runtime-20260921-r7-safe5",
    "AUTH_PASSIVE_SAFETY_R1",
]:
    if marker not in s:
        raise SystemExit(f"post-patch marker missing: {marker}")

PATH.write_text(s,encoding="utf-8")
print("EXPLORE_E4_QUEUE_R1_PATCH=PASS")
