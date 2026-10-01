(()=>{'use strict';
const API='https://hk-license.89.125.1.71.sslip.io/api/v1/cabinet/contest/';
const KEY='tk_clan_contest_session';
const $=id=>document.getElementById(id);
const safe=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let token=localStorage.getItem(KEY)||localStorage.getItem('tk_clan_cabinet_session')||'';
let state=null,test=false,pending=false,adminDirty=false,loginMounted=false,stageSignature='';
const errors={checkpoints_required:'Сначала пройдите три мини-этапа.',previous_checkpoint_required:'Сначала пройдите предыдущую контрольную точку.',invalid_checkpoint:'Эта контрольная точка недоступна.',unauthorized:'Войдите через Telegram.',forbidden:'Этот раздел доступен только владельцу.',contest_hidden:'Конкурс пока закрыт.',contest_not_open:'Приём ответов сейчас закрыт.',invalid_telegram_login:'Не удалось подтвердить вход. Повторите вход через Telegram.',invalid_participant:'Проверьте игровой ID и ник: ник должен содержать от 2 до 60 символов.',player_already_registered:'Этот игровой ID уже зарегистрирован.',registration_locked:'Регистрация уже сохранена; игровой ID и ник нельзя изменить.',registration_required:'Сначала зарегистрируйтесь.',stage_not_open:'Этот этап ещё не открыт.',previous_stage_required:'Сначала решите предыдущий этап.',wait_before_retry:'Подождите 30 секунд между попытками.',configuration_locked:'После старта задания менять нельзя.',three_stages_required:'Нужны три этапа.',stage_interval_too_short:'Первый этап открывается на старте; между этапами должно быть не меньше 20 минут.',invalid_deadline:'Окончание должно быть позже открытия третьего этапа.',not_ready_or_start_passed:'Заполните все задания и ответы. Время старта должно быть в будущем.',members_only:'Для этого конкурса нужен действующий доступ к кабинету TK Clan.',temporarily_unavailable:'Сервис временно недоступен. Попробуйте ещё раз.',invalid_answer:'Введите ответ длиной до 500 символов.'};
const show=(id,yes)=>$(id).classList.toggle('hidden',!yes);
function message(id,text,bad=false){$(id).textContent=text;$(id).className='message '+(bad?'bad':'good');}
const date=ts=>new Date(ts*1000).toLocaleString('ru-RU',{timeZone:'Asia/Yakutsk',day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'});
function localDate(ts){return new Date(ts*1000+9*3600000).toISOString().slice(0,16);}
function timestamp(value){return Date.parse(value+':00+09:00')/1000;}
async function request(action,body,method='POST'){
const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),15000);
try{const response=await fetch(API+action,{method,cache:'no-store',signal:controller.signal,headers:{'Content-Type':'application/json',...(token?{Authorization:'Bearer '+token}:{})},...(method==='POST'?{body:JSON.stringify(body||{})}:{})});
const data=await response.json();if(!response.ok)throw new Error(errors[data.error]||'Не удалось выполнить действие. Повторите попытку.');return data;
}finally{clearTimeout(timeout);}}
async function mountLogin(){
if(loginMounted)return;loginMounted=true;
try{const response=await fetch(API.replace(/contest\/$/,'config'),{cache:'no-store'});const cfg=await response.json();
if(!cfg.enabled||!cfg.bot_username)throw new Error('Вход временно недоступен.');
window.tkContestLogin=async user=>{try{const result=await request('login',{telegram:user});token=result.token;localStorage.setItem(KEY,token);await refresh();}catch(e){message('login-error',e.message,true);}};
const script=document.createElement('script');script.src='https://telegram.org/js/telegram-widget.js?22';script.async=true;script.dataset.telegramLogin=cfg.bot_username;script.dataset.size='large';script.dataset.onauth='tkContestLogin(user)';script.dataset.userpic='false';$('telegram-login').appendChild(script);
}catch(e){loginMounted=false;message('login-error',e.message,true);}}
function drawAdmin(data){if(adminDirty)return;const cfg=data.admin_config;if(!cfg)return;
$('start-at').value=localDate(cfg.start_at);$('end-at').value=localDate(cfg.end_at);$('audience').value=cfg.audience;$('armed').checked=cfg.armed;
$('stage-editors').innerHTML=cfg.stages.map((x,i)=>`<fieldset class="editor"><legend>Этап ${i+1}</legend><label>Название<input data-field="title" data-stage="${i}" maxlength="120" value="${safe(x.title)}"></label><label>Задание<textarea data-field="prompt" data-stage="${i}" maxlength="12000">${safe(x.prompt)}</textarea></label><label>Верный ответ<input data-field="answer" data-stage="${i}" maxlength="500" autocomplete="off" placeholder="${x.has_answer?'Ответ сохранён. Оставьте пустым, чтобы сохранить его.':'Введите верный ответ'}"></label><label>Открыть через минут после старта<input data-field="offset" data-stage="${i}" type="number" min="0" max="180" value="${x.offset/60}"></label></fieldset>`).join('');
$('stage-editors').querySelectorAll('.editor').forEach((editor,i)=>{if(cfg.stages[i].solution){const p=document.createElement('p');p.className='muted';p.textContent='Ответ для проверки (виден только вам): '+cfg.stages[i].solution;editor.appendChild(p);}});
$('pause').textContent=cfg.paused?'Возобновить конкурс':'Приостановить конкурс';}
function drawStages(data){
const signature=JSON.stringify([test,data.phase,data.stages.map(x=>[x.index,x.title,x.prompt,x.released,x.solved,x.points,x.final_unlocked,x.unlocked])]);
if(signature===stageSignature)return;stageSignature=signature;
const existing={};$('stages').querySelectorAll('[data-stage-form]').forEach(f=>{existing[f.dataset.stageForm]=f.querySelector('input').value;});
const focus=document.activeElement?.closest('[data-stage-form]')?.dataset.stageForm;
const canAnswer=test||data.phase==='open';
$('stages').innerHTML=(data.stages||[]).map((x,i)=>{
const prior=(data.stages||[]).slice(0,i).every(s=>s.solved),enabled=x.released&&!x.solved&&prior&&canAnswer&&x.final_unlocked;
return `<section class="card"><h2>${safe(x.title)}</h2><p class="stage-status ${x.solved?'solved':''}">${x.solved?'✓ Этап пройден':x.released?'Этап открыт':'Откроется '+safe(date(x.opens_at))+' по Якутску'}</p>${x.unlocked?'<div class="stage-prompt">'+safe(x.prompt)+'</div>':''}${(x.unlocked?x.points||[]:[]).map(q=>`<section class="checkpoint"><h3>${q.solved?'✓ ':''}${safe(q.title)}</h3>${q.unlocked?'<div class="stage-prompt">'+safe(q.prompt)+'</div>':'<p>Пройдите предыдущую точку.</p>'}${q.unlocked&&!q.solved&&prior&&x.released&&canAnswer?`<form data-point-form="${i}" data-point="${q.index}"><label>Ответ на мини-этап<input name="answer" maxlength="500" required autocomplete="off"></label><button>Отметить прохождение</button></form>`:''}<p id="point-message-${i}-${q.index}" role="status"></p></section>`).join('')}${enabled?`<form class="stage-form" data-stage-form="${i}"><label>Итоговый ответ<input name="answer" maxlength="500" autocomplete="off" required value="${safe(existing[i]||'')}"></label><button type="submit">Проверить ответ</button></form>`:x.released&&!x.solved&&!prior?'<p class="muted">Сначала пройдите предыдущий этап.</p>':''}<p id="stage-message-${i}" class="message" role="status"></p></section>`;
}).join('');
if(focus!==undefined)$('stages').querySelector(`[data-stage-form="${focus}"] input`)?.focus();
}
function render(data){state=data;
const phaseText={draft:'Закрытое тестирование',scheduled:'Начало '+date(data.start_at)+' по Якутску',open:'Конкурс открыт · окончание '+date(data.end_at)+' по Якутску',finished:'Приём ответов завершён',paused:'Конкурс приостановлен'};
$('phase').textContent=phaseText[data.phase]||'Конкурс закрыт';
const logged=!!data.stages;
show('login-panel',!logged);if(!logged)mountLogin();
show('owner-panel',data.owner&&logged);show('rules',data.visible&&logged);show('register-panel',logged&&!data.entrant&&(test||data.phase==='open'));show('competition',logged&&!!data.entrant);
if(!logged){$('stages').textContent='';$('ranking').textContent='';return;}
if(data.owner){drawAdmin(data);$('test-mode').checked=test;}
if(!data.entrant)return;
$('participant').textContent=data.entrant.nickname+' · '+data.entrant.player_id;
$('my-position').textContent=data.my_place?`Вы сейчас на ${data.my_place}-м месте · пройдено ${data.my_completed} из 3 этапов`:'Пока нет места в рейтинге. Решите первый этап.';
$('mode-note').textContent=test?'Тестовый режим: результаты видны только вам и не участвуют в конкурсе.':'Место обновляется по мере прохождения этапов участниками.';
drawStages(data);
$('ranking').innerHTML=data.leaderboard.length?data.leaderboard.map(x=>`<tr><td>${x.place}</td><td>${safe(x.nickname)}</td><td>${x.completed} / 3</td></tr>`).join(''):'<tr><td colspan="3">Первые результаты скоро появятся.</td></tr>';
$('count').textContent=data.total+' участников';$('rating-note').textContent=data.ranked_total>100?'Показаны первые 100 мест. Ваше место отображается выше.':'';
}
async function refresh(){if(pending||document.hidden)return;
try{const data=await request('status',null,'GET');if(data.owner){test=$('test-mode').checked;render(await request('state',{mode:test?'test':'live'}));}else if(data.visible&&token){test=false;render(await request('state',{mode:'live'}));}else render(data);$('global-error').textContent='';}catch(e){message('global-error',e.message,true);}}
$('register-form').addEventListener('submit',async e=>{e.preventDefault();if(pending)return;pending=true;try{const form=new FormData(e.target);render(await request('register',{mode:test?'test':'live',player_id:form.get('player_id'),nickname:form.get('nickname')}));}catch(err){message('register-message',err.message,true);}finally{pending=false;}});
$('stages').addEventListener('submit',async e=>{const form=e.target.closest('[data-point-form]');if(!form)return;e.preventDefault();if(pending)return;pending=true;const stage=Number(form.dataset.pointForm),point=Number(form.dataset.point);try{const result=await request('checkpoint',{mode:test?'test':'live',stage,point,answer:new FormData(form).get('answer')});render(result.state);const target=$('point-message-'+stage+'-'+point);if(target){target.textContent=result.correct?'✓ Контрольная точка пройдена.':'Неправильный ответ, ищите дальше. Повторная попытка через 30 секунд.';}}catch(err){const target=$('point-message-'+stage+'-'+point);if(target)target.textContent=err.message;}finally{pending=false;}});
$('stages').addEventListener('submit',async e=>{const form=e.target.closest('[data-stage-form]');if(!form)return;e.preventDefault();if(pending)return;pending=true;const stage=Number(form.dataset.stageForm),button=form.querySelector('button');button.disabled=true;
try{const result=await request('answer',{mode:test?'test':'live',stage,answer:new FormData(form).get('answer')});render(result.state);message('stage-message-'+stage,result.correct?`Верный ответ! Вы сейчас на ${result.state.my_place}-м месте.`:'Неправильный ответ, ищите дальше. Следующая попытка — через 30 секунд.',!result.correct);}catch(err){message('stage-message-'+stage,err.message,true);}finally{pending=false;button.disabled=false;}});
$('config-form').addEventListener('input',()=>{adminDirty=true;});
$('config-form').addEventListener('submit',async e=>{e.preventDefault();if(pending)return;pending=true;const button=e.target.querySelector('button[type="submit"]');button.disabled=true;
try{const stages=[0,1,2].map(i=>{const get=field=>e.target.querySelector(`[data-stage="${i}"][data-field="${field}"]`).value;return {title:get('title'),prompt:get('prompt'),answer:get('answer'),offset:Number(get('offset'))*60};});
const data=await request('admin/config',{stages,start_at:timestamp($('start-at').value),end_at:timestamp($('end-at').value),audience:$('audience').value,armed:$('armed').checked});adminDirty=false;render(data);message('admin-message',$('armed').checked?'Сохранено. Конкурс откроется автоматически по расписанию.':'Сохранено. Конкурс остаётся в закрытом режиме.');}catch(err){message('admin-message',err.message,true);}finally{pending=false;button.disabled=false;}});
$('test-mode').addEventListener('change',()=>{test=$('test-mode').checked;refresh();});
$('reset-test').addEventListener('click',async()=>{if(!confirm('Очистить только ваши тестовые ответы? Настоящие результаты сохранятся.'))return;try{await request('admin/reset-test');await refresh();}catch(e){message('admin-message',e.message,true);}});
$('pause').addEventListener('click',async()=>{try{await request('admin/pause',{paused:state.phase!=='paused'});adminDirty=false;await refresh();}catch(e){message('admin-message',e.message,true);}});
$('logout').addEventListener('click',()=>{localStorage.removeItem(KEY);token='';test=false;refresh();});
setInterval(refresh,15000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});refresh();
})();
