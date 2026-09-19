from pathlib import Path

REV='auto-routines-20260920-r1'
MARKER=f"HK_AUTO_ROUTINES_REV = '{REV}'"

def require(text, needle, message):
    if needle not in text:
        raise SystemExit(message)

def replace_once(text, old, new, message):
    if new in text:
        return text
    if old not in text:
        raise SystemExit(message)
    return text.replace(old,new,1)

def apply_hotfix(text):
    s=text
    if MARKER in s:
        s=s.replace('// @version      1.17.3','// @version      1.17.4',1)
        s=s.replace(": '1.17.3';",": '1.17.4';",1)
        return validate(s)

    require(s,'// @version      1.17.3','Auto Routines requires live 1.17.3')
    require(s,"HK_REGULAR_FAIR_REV = 'regular-fair-ui-20260920-r1'",'Regular Fair 1.17.3 marker missing')
    require(s,"{planned:true,ru:'Авто-рутины',en:'Auto routines'}",'Auto routines planned nav anchor missing')
    require(s,'      <div class="hk-page" data-content="business">','Business page anchor missing')
    require(s,"const activateModule = (page,persist=true) => {",'activateModule anchor missing')
    require(s,"  function applyLanguage() {",'applyLanguage anchor missing')
    for fn in [
        "async function runDailySelected()",
        "async function runFair()",
        "async function buyRegularShop()",
        "async function runRecipes()",
        "async function runProjectBureau()",
        "async function growthRunPlan(",
        "async function executeBusinessPlan()",
    ]:
        require(s,fn,f'Auto routines dependency missing: {fn}')

    s=s.replace('// @version      1.17.3','// @version      1.17.4',1)
    s=s.replace(": '1.17.3';",": '1.17.4';",1)

    regular_marker="  const HK_REGULAR_FAIR_REV = 'regular-fair-ui-20260920-r1';"
    require(s,regular_marker,'Regular Fair runtime marker anchor missing')
    s=s.replace(regular_marker,regular_marker+"\n  const "+MARKER+";",1)

    s=replace_once(
        s,
        "{page:'business',ru:'Бизнесы',en:'Businesses'},{page:'recipes',ru:'Рецепты',en:'Recipes'},{planned:true,ru:'Авто-рутины',en:'Auto routines'}",
        "{page:'business',ru:'Бизнесы',en:'Businesses'},{page:'recipes',ru:'Рецепты',en:'Recipes'},{page:'routines',ru:'Авто-рутины',en:'Auto routines'}",
        'Auto routines nav replacement missing'
    )

    page_anchor='      <div class="hk-page" data-content="business">'
    page=r'''      <div class="hk-page" data-content="routines">
        <div id="hk-routines-content" class="hk-cardbox"></div>
      </div>
'''
    s=replace_once(s,page_anchor,page+page_anchor,'Auto routines page anchor missing')

    module=r'''  let autoRoutineRunning = false;
  let autoRoutineStop = false;
  let autoRoutineCurrent = '';

  const AUTO_ROUTINE_ACTIONS = [
    {id:'daily',ru:'Сегодня — выбранные действия',en:'Today — selected actions',run:()=>runDailySelected()},
    {id:'growth',ru:'Развитие — текущий план',en:'Growth — current plan',run:()=>growthRunPlan('all')},
    {id:'business',ru:'Бизнесы — текущая перестановка',en:'Businesses — current rearrangement',run:()=>executeBusinessPlan()},
    {id:'fair',ru:'Ярмарка — текущие выбранные лоты',en:'Fair — current selected lots',run:()=>runFair()},
    {id:'shop',ru:'Магазин — выбранные покупки',en:'Shop — selected purchases',run:()=>buyRegularShop()},
    {id:'recipes',ru:'Рецепты — текущие прокрутки',en:'Recipes — current rerolls',run:()=>runRecipes()},
    {id:'bureau',ru:'Проектное бюро — текущий рецепт',en:'Project Bureau — current recipe',run:()=>runProjectBureau()},
  ];

  function autoRoutineSelection() {
    const stored=load().autoRoutineSelection;
    return stored&&typeof stored==='object'&&!Array.isArray(stored)?{...stored}:{};
  }

  function saveAutoRoutineSelection(selection) {
    save({autoRoutineSelection:{...selection}});
  }

  function renderAutoRoutines() {
    const box=root?.querySelector('#hk-routines-content');
    if(!box)return;
    const selection=autoRoutineSelection();
    const selectedCount=AUTO_ROUTINE_ACTIONS.filter(row=>selection[row.id]).length;
    const current=AUTO_ROUTINE_ACTIONS.find(row=>row.id===autoRoutineCurrent);
    box.innerHTML=
      '<div class="hk-clan-head"><div><h3>'+either('Авто-рутины','Auto routines')+'</h3>'+
      '<small>'+either('Последовательный запуск уже настроенных модулей','Sequential run of already configured modules')+'</small></div></div>'+
      '<p class="hk-muted">'+either(
        'Рутина не меняет настройки модулей и не обходит их budget guard. Необратимые этапы сохраняют собственное подтверждение перед запуском.',
        'The routine does not change module settings or bypass budget guards. Irreversible stages keep their own confirmation before execution.'
      )+'</p>'+
      '<div class="hk-routine-list">'+AUTO_ROUTINE_ACTIONS.map((row,index)=>
        '<label class="hk-cardbox" style="display:flex;align-items:center;gap:10px;margin:7px 0;padding:10px">'+
        '<input type="checkbox" data-routine-id="'+escapeHtml(row.id)+'" '+(selection[row.id]?'checked':'')+' '+(autoRoutineRunning?'disabled':'')+'>'+
        '<b>'+(index+1)+'. '+escapeHtml(language==='en'?row.en:row.ru)+'</b></label>'
      ).join('')+'</div>'+
      '<div class="hk-toolbar" style="margin-top:10px">'+
        '<button id="hk-routine-run" class="hk-primary" '+(autoRoutineRunning||!selectedCount?'disabled':'')+'>'+either('Запустить цепочку','Run sequence')+'</button>'+
        '<button id="hk-routine-stop" class="hk-danger" '+(!autoRoutineRunning?'disabled':'')+'>'+either('Остановить','Stop')+'</button>'+
      '</div>'+
      '<p class="hk-muted">'+(autoRoutineRunning
        ? either('Текущий этап: ','Current stage: ')+escapeHtml(current?(language==='en'?current.en:current.ru):either('подготовка','preparing'))
        : either('Выбрано этапов: ','Selected stages: ')+selectedCount)+'</p>';

    box.querySelectorAll('[data-routine-id]').forEach(input=>input.onchange=()=>{
      const next=autoRoutineSelection();
      next[input.dataset.routineId]=!!input.checked;
      saveAutoRoutineSelection(next);
      renderAutoRoutines();
    });
    box.querySelector('#hk-routine-run')?.addEventListener('click',()=>void runAutoRoutine());
    box.querySelector('#hk-routine-stop')?.addEventListener('click',()=>stopAutoRoutine());
  }

  function stopAutoRoutine() {
    if(!autoRoutineRunning)return;
    autoRoutineStop=true;
    if(hkRunner.running)hkRunner.stop('auto-routine');
    log(either('Останавливаю авто-рутину после текущего этапа…','Stopping auto routine after the current stage…'),'warn');
    renderAutoRoutines();
  }

  async function runAutoRoutine() {
    if(!requireLicense()||autoRoutineRunning)return;
    if(hkRunner.running){alert(either('Сначала завершите текущую задачу','Finish the current task first'));return;}
    const selection=autoRoutineSelection();
    const queue=AUTO_ROUTINE_ACTIONS.filter(row=>selection[row.id]);
    if(!queue.length)return;
    if(!confirm(either(
      'Запустить авто-рутину из '+queue.length+' этапов?\n\nКаждый этап использует текущие настройки своего раздела. Необратимые операции сохраняют собственные подтверждения и лимиты.',
      'Run an auto routine with '+queue.length+' stages?\n\nEach stage uses the current settings of its module. Irreversible operations keep their own confirmations and limits.'
    )))return;

    autoRoutineRunning=true;
    autoRoutineStop=false;
    autoRoutineCurrent='';
    renderAutoRoutines();
    let completed=0;
    try{
      for(const action of queue){
        if(autoRoutineStop)break;
        if(hkRunner.running)throw new Error(either('Предыдущая задача ещё не завершена','The previous task is still running'));
        autoRoutineCurrent=action.id;
        renderAutoRoutines();
        log(either('Авто-рутина: ','Auto routine: ')+(language==='en'?action.en:action.ru));
        await action.run();
        if(autoRoutineStop)break;
        while(hkRunner.running&&!autoRoutineStop)await sleep(150);
        if(autoRoutineStop)break;
        completed+=1;
        await sleep(250);
      }
      log(autoRoutineStop
        ? either('Авто-рутина остановлена: завершено ','Auto routine stopped: completed ')+completed+'/'+queue.length
        : either('Авто-рутина завершена: ','Auto routine completed: ')+completed+'/'+queue.length,
        autoRoutineStop?'warn':'ok');
    }catch(error){
      log(either('Авто-рутина остановлена ошибкой','Auto routine stopped by an error')+': '+(error?.message||error),'bad');
    }finally{
      autoRoutineRunning=false;
      autoRoutineStop=false;
      autoRoutineCurrent='';
      renderAutoRoutines();
    }
  }

'''
    s=replace_once(s,"  function applyLanguage() {",module+"  function applyLanguage() {",'Auto routines module anchor missing')

    old="""      if (finalPage === 'recipes') renderRecipes();
      if (finalPage.startsWith('growth')) { renderGrowth(); growthAutoOpen(finalPage); }
      else void refreshModuleLive(finalPage);"""
    new="""      if (finalPage === 'recipes') renderRecipes();
      if (finalPage === 'routines') renderAutoRoutines();
      if (finalPage.startsWith('growth')) { renderGrowth(); growthAutoOpen(finalPage); }
      else if (finalPage !== 'routines') void refreshModuleLive(finalPage);"""
    s=replace_once(s,old,new,'Auto routines activation anchor missing')

    # Keep language changes reflected while the routines page is open.
    old="    renderClanSkills();\n    renderGrowth();"
    new="    renderClanSkills();\n    renderGrowth();\n    renderAutoRoutines();"
    s=replace_once(s,old,new,'applyLanguage routines anchor missing')

    return validate(s)

def validate(s):
    checks=[
        '// @version      1.17.4',
        ": '1.17.4';",
        MARKER,
        "{page:'routines',ru:'Авто-рутины',en:'Auto routines'}",
        'data-content="routines"',
        "const AUTO_ROUTINE_ACTIONS = [",
        "async function runAutoRoutine()",
        "function stopAutoRoutine()",
        "run:()=>runDailySelected()",
        "run:()=>growthRunPlan('all')",
        "run:()=>executeBusinessPlan()",
        "run:()=>runFair()",
        "run:()=>buyRegularShop()",
        "run:()=>runRecipes()",
        "run:()=>runProjectBureau()",
        "if(hkRunner.running)hkRunner.stop('auto-routine')",
        "else if (finalPage !== 'routines') void refreshModuleLive(finalPage);",
        "HK_NATIVE_LOGIN_GATE_V1 login-gate-20260920-r1",
        "GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'",
        "GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'",
    ]
    for needle in checks:
        require(s,needle,f'Auto routines validation missing: {needle}')
    if "{planned:true,ru:'Авто-рутины',en:'Auto routines'}" in s:
        raise SystemExit('Auto routines is still planned')
    return s

if __name__=='__main__':
    p=Path('/tmp/HamsterKingMobile.user.js')
    s=p.read_text(encoding='utf-8')
    p.write_text(apply_hotfix(s),encoding='utf-8')
    print('HK_AUTO_ROUTINES_1174_OK')
