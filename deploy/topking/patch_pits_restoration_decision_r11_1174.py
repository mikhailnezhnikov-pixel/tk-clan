from pathlib import Path
p=Path('/tmp/HamsterKingMobile.user.js')
s=p.read_text(encoding='utf-8')

BASE="const HK_PITS_SPEED_REV = 'pits-fast-cycle-20260920-r10';"
MARK="const HK_PITS_DECISION_REV = 'pits-restoration-decision-20260920-r11';"
if MARK in s:
    raise SystemExit('already applied')
if BASE not in s:
    raise SystemExit('r10 marker missing')
s=s.replace(BASE, BASE+"\n  "+MARK, 1)

anchor="  function pitCanonFastCycleDelay(def,sniper=false) {\n"
helpers=r"""  const pitCanonDecisionBudget={remember:false,remaining:0};
  function pitCanonDecisionBudgetReset(){
    pitCanonDecisionBudget.remember=false;
    pitCanonDecisionBudget.remaining=0;
  }
  function pitCanonDecisionBudgetCanSpend(cost,hasPaws){
    if(!pitCanonDecisionBudget.remember||!hasPaws)return false;
    if(!Number.isFinite(pitCanonDecisionBudget.remaining))return true;
    return pitCanonDecisionBudget.remaining>=Math.max(0,pitCanonWhole(cost));
  }
  function pitCanonDecisionBudgetApply(decision){
    if(decision?.action!=='spend')return;
    if(decision.remember){
      pitCanonDecisionBudget.remember=true;
      pitCanonDecisionBudget.remaining=decision.extraLimit>0?pitCanonWhole(decision.extraLimit):Number.POSITIVE_INFINITY;
    }else pitCanonDecisionBudgetReset();
  }
  function pitCanonDecisionBudgetConsume(cost){
    if(!pitCanonDecisionBudget.remember||!Number.isFinite(pitCanonDecisionBudget.remaining))return;
    pitCanonDecisionBudget.remaining=Math.max(0,pitCanonDecisionBudget.remaining-Math.max(0,pitCanonWhole(cost)));
    if(pitCanonDecisionBudget.remaining<=0)pitCanonDecisionBudgetReset();
  }

  function pitCanonAskRestorationDecision({def,level,target,cost,paws}){
    return new Promise(resolve=>{
      root?.querySelector('#hk-pit-restoration-decision')?.remove();
      const overlay=document.createElement('div');
      overlay.id='hk-pit-restoration-decision';
      overlay.className='hk-pit-decision-overlay';
      const targetText=target>0?`≥ ${pitCanonWhole(target)}`:either('Как можно дальше','As far as possible');
      overlay.innerHTML=`<div class="hk-pit-decision-card">
        <div class="hk-pit-decision-head"><div><small>${either('Ямы · требуется решение','Pits · decision required')}</small><h3>${escapeHtml(pitCanonDefinitionName(def))}</h3></div><span>🐾</span></div>
        <p class="hk-pit-decision-intro">${either('Выбранная цель ещё не достигнута, а для продолжения требуется восстановление.','The selected target has not been reached and restoration is required to continue.')}</p>
        <div class="hk-pit-decision-grid">
          <div><span>${either('Текущий уровень','Current level')}</span><b>${pitCanonWhole(level)}</b></div>
          <div><span>${either('Выбранная цель','Selected target')}</span><b>${escapeHtml(targetText)}</b></div>
          <div><span>${either('Нужно сейчас','Required now')}</span><b>🐾 ${pitCanonWhole(cost)}</b></div>
          <div><span>${either('Доступно сейчас','Available now')}</span><b>🐾 ${pitCanonWhole(paws)}</b></div>
          <div><span>${either('Останется после траты','Remaining after spend')}</span><b>🐾 ${Math.max(0,pitCanonWhole(paws)-pitCanonWhole(cost))}</b></div>
        </div>
        <div class="hk-pit-decision-budget">
          <label><span>${either('Максимум дополнительных Лап с этого момента','Maximum additional Paws from now')}</span><input id="hk-pit-decision-limit" type="number" min="0" max="${pitCanonWhole(paws)}" value="0"></label>
          <label class="hk-pit-decision-remember"><input id="hk-pit-decision-remember" type="checkbox"><span>${either('Запомнить мой выбор для этого запуска','Remember my choice for this run')}</span></label>
          <small>${either('Если лимит больше 0, выбор запоминается автоматически до исчерпания этого дополнительного лимита.','If the limit is above 0, the choice is remembered automatically until that additional budget is exhausted.')}</small>
        </div>
        <div class="hk-pit-decision-actions">
          <button data-pit-decision="spend" class="hk-primary" ${pitCanonWhole(paws)<pitCanonWhole(cost)?'disabled':''}>${either('Потратить Лапы и продолжить','Spend Paws and continue')} (🐾 ${pitCanonWhole(cost)})</button>
          <button data-pit-decision="collect" class="hk-secondary">${either('Завершить текущий раунд и продолжить','Finish current round and continue')}</button>
          <button data-pit-decision="manual">${either('Оставить Яму для ручного сбора и перейти дальше','Leave Pit for manual collection and continue')}</button>
          <button data-pit-decision="stop" class="hk-danger">${either('Полностью остановить','Stop completely')}</button>
        </div>
      </div>`;
      root?.appendChild(overlay);
      let finished=false;
      let timer=null;
      const finish=action=>{
        if(finished)return;finished=true;
        if(timer)clearInterval(timer);
        const limit=Math.max(0,pitCanonWhole(overlay.querySelector('#hk-pit-decision-limit')?.value));
        const remember=action==='spend'&&(overlay.querySelector('#hk-pit-decision-remember')?.checked===true||limit>0);
        overlay.remove();
        resolve({action,remember,extraLimit:limit});
      };
      overlay.querySelectorAll('[data-pit-decision]').forEach(button=>button.onclick=()=>finish(String(button.dataset.pitDecision||'stop')));
      timer=setInterval(()=>{if(hkRunner.signal?.aborted)finish('stop')},150);
    });
  }

"""
if anchor not in s:
    raise SystemExit('fast cycle anchor missing')
s=s.replace(anchor,helpers+anchor,1)

css_anchor=".hk-pits-busy{opacity:.88}.hk-pits-busy .hk-pit-canon-card{filter:saturate(.85)}"
css_add=".hk-pit-decision-overlay{position:fixed;inset:0;z-index:250;display:grid;place-items:center;padding:18px;background:#05080dcc;backdrop-filter:blur(8px)}.hk-pit-decision-card{width:min(560px,100%);max-height:calc(100vh - 36px);overflow:auto;border:1px solid #ffad1f;border-radius:16px;background:linear-gradient(145deg,#1d1b16,#101722);box-shadow:0 20px 60px #000b,0 0 0 2px #ffad1f22;padding:14px}.hk-pit-decision-head{display:flex;align-items:center;justify-content:space-between;gap:12px}.hk-pit-decision-head small{color:#ffcf73;font-weight:800}.hk-pit-decision-head h3{margin:3px 0 0;font-size:18px}.hk-pit-decision-head>span{font-size:30px}.hk-pit-decision-intro{margin:10px 0;color:#cbd5e1;font-size:12px}.hk-pit-decision-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px}.hk-pit-decision-grid>div{padding:9px;border:1px solid #34445c;border-radius:10px;background:#0b111b}.hk-pit-decision-grid span{display:block;color:#8fa1b8;font-size:10px}.hk-pit-decision-grid b{display:block;margin-top:3px;font-size:13px}.hk-pit-decision-budget{display:grid;gap:7px;margin:10px 0;padding:10px;border:1px solid #3a4658;border-radius:11px;background:#0a1018}.hk-pit-decision-budget label:not(.hk-pit-decision-remember){display:grid;grid-template-columns:minmax(0,1fr) 100px;gap:8px;align-items:center}.hk-pit-decision-budget input[type=number]{width:100%;box-sizing:border-box}.hk-pit-decision-remember{display:flex;gap:7px;align-items:center}.hk-pit-decision-budget small{color:#8291a5;font-size:9px}.hk-pit-decision-actions{display:grid;gap:7px}.hk-pit-decision-actions button{min-height:42px}.hk-pit-decision-actions button:disabled{opacity:.45}@media(max-width:520px){.hk-pit-decision-grid{grid-template-columns:1fr}.hk-pit-decision-budget label:not(.hk-pit-decision-remember){grid-template-columns:1fr}}"
if css_anchor not in s:
    raise SystemExit('Pits busy css anchor missing')
s=s.replace(css_anchor,css_anchor+css_add,1)

start=s.find("  async function pitCanonRunOne(config,progress) {")
end=s.find("\n  async function runPitsCanonical()",start)
if start<0 or end<0:
    raise SystemExit('pitCanonRunOne anchors missing')
block=s[start:end]

old="      let restorationSpent=0,battles=0;\n"
new="      let restorationSpent=0,battles=0,forceFinish=false,leaveManual=false;\n"
if old not in block:
    raise SystemExit('round local state anchor missing')
block=block.replace(old,new,1)

old=r"""        if(pitCanonWhole(state.health)<=0){
          const cost=pitCanonRespawnCost(state,chunk),paws=pitCanonResourceQuantity(playerDocument,HK_PIT_RESTORATION_ITEM_ID,'item');
          if(cost<=0||restorationSpent+cost>config.maxRestoration||paws<cost){pitCanonRunnerLog(`${pitCanonDefinitionName(def)}: ${either('остановка по лимиту Лап восстановления','Restoration Paws limit reached')} (${restorationSpent}/${config.maxRestoration})`,'warn');break;}
          hkRunner.setStep(`${pitCanonDefinitionName(def)} · ${either('восстановление','restoration')} 🐾 ${cost}`,progress.done,progress.total);
          pitCanonRunnerLog(`${pitCanonDefinitionName(def)} — ${either('восстановление','restoration')}: 🐾 ${cost} · ${either('потрачено скриптом','spent by script')}: ${restorationSpent+cost}/${config.maxRestoration}`,'warn');
          const respawnResponse=await apiJson(api.respawn,'POST',{payment_type:'ITEM'});restorationSpent+=cost;
          {
            const mutation=pitCanonStateAfterMutation(def,respawnResponse,`pits:${def.id}:after-respawn`);
            state=mutation.state;
            if(mutation.needsReread){playerDocument=await hkAuthoritativePlayerRead(mutation.reason);state=pitRaceSnapshot(def.id,playerDocument);}
          }
          pitCanonRunnerLog(`✓ ${pitCanonDefinitionName(def)} — ${either('восстановлено','restored')} · HP ${pitCanonWhole(state?.health)} · 🐾 ${pitCanonResourceQuantity(playerDocument,HK_PIT_RESTORATION_ITEM_ID,'item')} ${either('осталось','remaining')}`,'ok');
          await sleep(pitCanonFastCycleDelay(def,config.sniper));
          continue;
        }
"""
new=r"""        if(pitCanonWhole(state.health)<=0){
          const cost=pitCanonRespawnCost(state,chunk),paws=pitCanonResourceQuantity(playerDocument,HK_PIT_RESTORATION_ITEM_ID,'item');
          const configuredAllowed=cost>0&&restorationSpent+cost<=config.maxRestoration&&paws>=cost;
          const rememberedAllowed=!configuredAllowed&&pitCanonDecisionBudgetCanSpend(cost,paws>=cost);
          if(!configuredAllowed&&!rememberedAllowed){
            hkRunner.setStep(`${pitCanonDefinitionName(def)} · ${either('нужно решение по восстановлению','restoration decision required')} 🐾 ${cost}`,progress.done,progress.total);
            pitCanonRunnerLog(`${pitCanonDefinitionName(def)} — ${either('нужно решение по Лапам восстановления','Restoration Paws decision required')} · 🐾 ${cost}`,'warn');
            const decision=await pitCanonAskRestorationDecision({def,level,target:config.target,cost,paws});
            if(decision.action==='stop'){
              hkRunner.stop('pit-restoration-decision');
              throw new DOMException('Aborted','AbortError');
            }
            if(decision.action==='manual'){
              leaveManual=true;
              pitCanonRunnerLog(`${pitCanonDefinitionName(def)} — ${either('оставлена для ручного сбора','left for manual collection')}`,'warn');
              break;
            }
            if(decision.action==='collect'){
              forceFinish=true;
              pitCanonRunnerLog(`${pitCanonDefinitionName(def)} — ${either('завершаю текущий раунд и продолжаю','finishing current round and continuing')}`,'info');
              break;
            }
            if(decision.action!=='spend'||cost<=0||paws<cost){
              leaveManual=true;
              break;
            }
            pitCanonDecisionBudgetApply(decision);
          }
          hkRunner.setStep(`${pitCanonDefinitionName(def)} · ${either('восстановление','restoration')} 🐾 ${cost}`,progress.done,progress.total);
          pitCanonRunnerLog(`${pitCanonDefinitionName(def)} — ${either('восстановление','restoration')}: 🐾 ${cost} · ${either('потрачено скриптом','spent by script')}: ${restorationSpent+cost}`,'warn');
          const respawnResponse=await apiJson(api.respawn,'POST',{payment_type:'ITEM'});restorationSpent+=cost;
          if(rememberedAllowed||pitCanonDecisionBudget.remember)pitCanonDecisionBudgetConsume(cost);
          {
            const mutation=pitCanonStateAfterMutation(def,respawnResponse,`pits:${def.id}:after-respawn`);
            state=mutation.state;
            if(mutation.needsReread){playerDocument=await hkAuthoritativePlayerRead(mutation.reason);state=pitRaceSnapshot(def.id,playerDocument);}
          }
          pitCanonRunnerLog(`✓ ${pitCanonDefinitionName(def)} — ${either('восстановлено','restored')} · HP ${pitCanonWhole(state?.health)} · 🐾 ${pitCanonResourceQuantity(playerDocument,HK_PIT_RESTORATION_ITEM_ID,'item')} ${either('осталось','remaining')}`,'ok');
          await sleep(pitCanonFastCycleDelay(def,config.sniper));
          continue;
        }
"""
old=old.replace('`',chr(96)).replace('§'+chr(123),'$'+chr(123))
new=new.replace('`',chr(96)).replace('§'+chr(123),'$'+chr(123))
if old not in block:
    raise SystemExit('old restoration branch missing')
block=block.replace(old,new,1)

old="      state=pitRaceSnapshot(def.id,playerDocument);\n      if(state&&state.is_finish===false&&config.autofinish){\n"
new="      state=pitRaceSnapshot(def.id,playerDocument);\n      if(leaveManual)return;\n      if(state&&state.is_finish===false&&(config.autofinish||forceFinish)){\n"
if old not in block:
    raise SystemExit('finish gate anchor missing')
block=block.replace(old,new,1)
s=s[:start]+block+s[end:]

start_anchor="    hkRunner.start({title:either('Ямы','Pits'),step:either('Подготовка','Preparing'),total,pausable:true,stoppable:true});\n    pitCanonSetBusy(true);\n"
start_new="    hkRunner.start({title:either('Ямы','Pits'),step:either('Подготовка','Preparing'),total,pausable:true,stoppable:true});\n    pitCanonDecisionBudgetReset();\n    pitCanonSetBusy(true);\n"
if start_anchor not in s:
    raise SystemExit('run start reset anchor missing')
s=s.replace(start_anchor,start_new,1)

for needle in [
    MARK,
    "function pitCanonAskRestorationDecision",
    "pitCanonDecisionBudgetReset();",
    "pitCanonDecisionBudgetCanSpend",
    'id="hk-pit-restoration-decision"',
    'data-pit-decision="spend"',
    "decision.action==='manual'",
    "decision.action==='collect'",
    "(config.autofinish||forceFinish)"
]:
    if needle not in s:
        raise SystemExit('missing r11 invariant: '+needle)

p.write_text(s,encoding='utf-8')
print('PITS_RESTORATION_DECISION_R11_PATCH_OK')
