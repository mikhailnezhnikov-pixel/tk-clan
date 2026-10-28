/* Reward queue: cabinet authentication, no polling or game requests. */
(() => {
  'use strict';
  const $=id=>document.getElementById(id), labels={waiting:'В очереди',received:'Получено',refused:'Отказ'};
  const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let data=null,dirty=false,busy=false,baseline=new Map(),filter='all';
  const nav=document.querySelector('[data-cab-group="main"]');if(!nav)return;
  const tab=document.createElement('button');tab.type='button';tab.className='cab-tab';tab.dataset.cabTab='rewards';tab.textContent='Награды КЛ';nav.append(tab);
  const panel=document.createElement('section');panel.className='cab-panel';panel.dataset.cabPanel='rewards';panel.hidden=true;
  panel.innerHTML='<article class="panel rq-box"><h2>Очередь наград клана</h2><p class="muted">Альянс — Золото · шары генералов Гуру. Порядок задаёт КЛ; отметка 👑 — приоритет.</p><p id="rq-counts"></p><div class="rq-actions"><select id="rq-filter" aria-label="Показать участников"><option value="all">Все участники</option><option value="waiting">В очереди</option><option value="received">Получено</option><option value="refused">Отказ</option></select><button id="rq-refresh" type="button">Обновить</button><button id="rq-add" type="button" hidden>Добавить участника</button><button id="rq-save" type="button" hidden>Сохранить изменения</button></div><p id="rq-message" role="status"></p><div id="rq-rows"></div><details id="rq-publication"><summary>Предпросмотр и публикация в Telegram</summary><div id="rq-targets" class="rq-actions" hidden><label>Группа <select id="rq-kind"></select></label><label>ID темы <input id="rq-thread" type="number" min="1" max="2147483647" inputmode="numeric"></label></div><p class="muted">Укажите ID нужной темы (последнее число в ссылке на тему). Группа выбирается из уже настроенных направлений бота. Сначала сохраните изменения.</p><textarea id="rq-preview" readonly aria-label="Текст публикации"></textarea><div class="rq-actions"><button id="rq-copy" type="button">Скопировать</button><button id="rq-publish" type="button" hidden>Опубликовать в выбранной теме</button></div></details></article>';
  $('dashboard').append(panel);
  const style=document.createElement('style');style.textContent='.rq-box{padding:clamp(14px,3vw,28px)}.rq-actions{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:12px 0}.rq-actions label{display:grid;gap:5px}.rq-box button,.rq-box select,.rq-box input{font:inherit;padding:9px;border:1px solid #715d35;border-radius:9px;background:#191a20;color:#f2e4c4;box-sizing:border-box;max-width:100%}.rq-row{display:grid;grid-template-columns:32px minmax(100px,1fr) 85px 130px 58px 84px;gap:8px;align-items:center;padding:10px 0;border-bottom:1px solid #ffffff18}.rq-row.received{opacity:.7}.rq-row.refused{opacity:.55}.rq-order{display:flex;gap:4px}.rq-row input[type=checkbox]{width:19px;height:19px}.rq-box textarea{width:100%;min-height:330px;resize:vertical;padding:12px;color:#f3e5c7;background:#111218;border:1px solid #715d35;border-radius:9px;box-sizing:border-box;font:14px/1.6 sans-serif}.rq-box button:disabled{opacity:.45}.rq-box details{margin-top:20px}.rq-box summary{cursor:pointer;font-weight:700}.rq-bad{color:#ff9a9a}@media(max-width:700px){.rq-row{grid-template-columns:28px minmax(80px,1fr) 80px}.rq-row .rq-status{grid-column:2}.rq-row .rq-priority{grid-column:3}.rq-order{grid-column:2/4}.rq-row button{min-height:40px}}';document.head.append(style);
  const request=(path,options)=>window.hkRewardQueueRequest(path,options);
  function message(text,bad=false){$('rq-message').textContent=text;$('rq-message').classList.toggle('rq-bad',bad);}
  function controls(){
    for(const id of ['rq-save','rq-add','rq-publish'])$(id).hidden=!data?.can_manage;
    $('rq-targets').hidden=!data?.can_manage;
    $('rq-save').disabled=busy||!dirty;
    $('rq-add').disabled=busy;
    $('rq-refresh').disabled=busy;
    $('rq-publish').disabled=busy||dirty||!data?.target.kind||!data?.target.thread_id;
    $('rq-kind').disabled=busy;$('rq-thread').disabled=busy;
  }
  function changed(){dirty=true;controls();message('Есть несохранённые изменения. Предпросмотр обновится после сохранения.');}
  function render(){
    const rows=data.rows,editable=data.can_manage&&!busy;
    $('rq-counts').textContent='Всего: '+rows.length+' · В очереди: '+rows.filter(r=>r.status==='waiting').length+' · Получено: '+rows.filter(r=>r.status==='received').length+' · Отказ: '+rows.filter(r=>r.status==='refused').length;
    $('rq-rows').innerHTML=rows.map((r,i)=>filter!=='all'&&r.status!==filter?'':'<div class="rq-row '+r.status+'" data-id="'+escape(r.id)+'"><b>'+(i+1)+'</b><input data-field="name" aria-label="Участник" maxlength="100" value="'+escape(r.name)+'" '+(editable?'':'disabled')+'><input data-field="score" aria-label="Очки" type="number" min="0" max="1000000000" value="'+r.score+'" '+(editable?'':'disabled')+'><select class="rq-status" data-field="status" aria-label="Статус" '+(editable?'':'disabled')+'>'+Object.entries(labels).map(([k,v])=>'<option value="'+k+'" '+(r.status===k?'selected':'')+'>'+v+'</option>').join('')+'</select><label class="rq-priority"><input data-field="priority" type="checkbox" '+(r.priority?'checked':'')+' '+(editable?'':'disabled')+' aria-label="Приоритет"> 👑</label>'+(editable?'<div class="rq-order"><button type="button" data-move="-1" aria-label="Выше" '+(i===0?'disabled':'')+'>↑</button><button type="button" data-move="1" aria-label="Ниже" '+(i===rows.length-1?'disabled':'')+'>↓</button></div>':'<span>'+(r.new?'🆕':r.move?(r.move>0?'⬆️':'⬇️')+Math.abs(r.move):'')+'</span>')+'</div>').join('');
    $('rq-kind').innerHTML='<option value="">Выберите группу</option>'+data.targets.map(t=>'<option value="'+escape(t.kind)+'" '+(data.target.kind===t.kind?'selected':'')+'>'+escape(({clan_shop:'Группа закупок',clan_activity:'Группа активности',application:'Группа заявок',feedback:'Группа обратной связи'})[t.kind]||t.kind)+' ('+escape(t.chat_id)+')</option>').join('');
    $('rq-thread').value=data.target.thread_id||'';$('rq-preview').value=data.preview;controls();
  }
  function accept(result){data=result;dirty=false;let rank=0;baseline=new Map(data.rows.filter(r=>!r.new).map(r=>[r.id,rank+++(r.move||0)]));render();}
  async function open(){if(data)return;busy=true;controls();message('Загружаю очередь…');try{accept(await request('/rewards'));message('');}catch(e){message('Не удалось загрузить очередь: '+e.message,true);}finally{busy=false;if(data)render();else controls();}}
  $('rq-filter').onchange=()=>{filter=$('rq-filter').value;if(data)render();};
  $('rq-rows').onchange=event=>{const input=event.target,field=input.dataset.field,row=data?.rows.find(r=>r.id===input.closest('[data-id]')?.dataset.id);if(!row||!data.can_manage||busy)return;row[field]=field==='priority'?input.checked:field==='score'?Number(input.value):input.value;changed();};
  $('rq-rows').onclick=event=>{const button=event.target.closest('[data-move]');if(!button||!data?.can_manage||busy)return;const i=data.rows.findIndex(r=>r.id===button.closest('[data-id]').dataset.id),j=i+Number(button.dataset.move);if(j<0||j>=data.rows.length)return;[data.rows[i],data.rows[j]]=[data.rows[j],data.rows[i]];let rank=0;for(const row of data.rows)if(!row.new){row.move=(baseline.get(row.id)??rank)-rank;rank++;}changed();render();};
  $('rq-add').onclick=()=>{if(!data?.can_manage||busy)return;data.rows.push({id:'new_'+Date.now().toString(36),name:'Новый участник',score:0,status:'waiting',priority:false,new:true,move:0});changed();filter='all';$('rq-filter').value='all';render();};
  $('rq-kind').onchange=()=>{if(data){data.target.kind=$('rq-kind').value;data.target.thread_id=null;const target=data.targets.find(t=>t.kind===data.target.kind);if(target?.thread_id)data.target.thread_id=target.thread_id;$('rq-thread').value=data.target.thread_id||'';changed();}};
  $('rq-thread').onchange=()=>{if(data){data.target.thread_id=$('rq-thread').value?Number($('rq-thread').value):null;changed();}};
  $('rq-save').onclick=async()=>{if(!data?.can_manage||busy)return;busy=true;render();try{accept(await request('/rewards/save',{method:'POST',body:JSON.stringify({revision:data.revision,rows:data.rows,target:data.target})}));message('Сохранено. Проверьте текст перед публикацией.');}catch(e){message(e.code==='revision_conflict'?'Другой управляющий уже изменил очередь. Скопируйте правки и обновите список.':'Не сохранено: '+e.message,true);}finally{busy=false;render();}};
  $('rq-refresh').onclick=()=>{if(dirty&&!confirm('Отменить несохранённые изменения и загрузить очередь с сервера?'))return;data=null;dirty=false;void open();};
  $('rq-copy').onclick=async()=>{try{await navigator.clipboard.writeText($('rq-preview').value);message('Текст скопирован.');}catch(_){$('rq-preview').focus();$('rq-preview').select();message('Выделен текст для копирования.');}};
  $('rq-publish').onclick=async()=>{if(!data?.can_manage||busy||dirty||!data.target.thread_id)return;const target=data.targets.find(t=>t.kind===data.target.kind);if(!target||!confirm('Отправить очередь в группу '+target.chat_id+', тему '+data.target.thread_id+'?'))return;busy=true;render();try{await request('/rewards/publish',{method:'POST',body:JSON.stringify({revision:data.revision,expected_text:data.preview})});message('Очередь опубликована.');}catch(e){message('Публикация не подтверждена: '+e.message+'. Проверьте Telegram перед повторной отправкой.',true);}finally{busy=false;render();}};
  document.addEventListener('click',event=>{if(event.target.closest('[data-cab-tab="rewards"]'))void open();});
  window.hkRewardQueue={open};
  if(new URL(location.href).searchParams.get('tab')==='rewards'){
    document.querySelectorAll('[data-cab-panel]').forEach(node=>node.hidden=node!==panel);
    document.querySelectorAll('[data-cab-tab]').forEach(node=>node.classList.toggle('active',node===tab));
    if(!$('dashboard').classList.contains('hidden'))void open();
  }
})();
