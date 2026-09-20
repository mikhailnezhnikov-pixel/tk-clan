from pathlib import Path
p=Path('/tmp/HamsterKingMobile.user.js')
s=p.read_text(encoding='utf-8')
BASE="const HK_PITS_PREFLIGHT_REV = 'pits-aggregate-preflight-20260920-r19';"
MARK="const HK_PITS_REWARD_PICKER_REV = 'pits-reward-picker-20260920-r20';"
if MARK in s: raise SystemExit('already applied')
if BASE not in s: raise SystemExit('r19 marker missing')
s=s.replace(BASE,BASE+"\n  "+MARK,1)
anchor="  function pitCanonRender() {\n"
helper=r"""  function pitCanonRewardEntryHtml(entry){
    const id=String(entry?.id||''),count=Math.max(1,pitCanonWhole(entry?.count??1)),folder=id.startsWith('cur_')?'currencies':'items';
    const src=`https://cdn-prod-art.hwgame.cloud/${folder}/${encodeURIComponent(id)}_icon.png`;
    return `<span class="hk-pit-reward-entry" title="${escapeHtml(id)}"><img src="${escapeHtml(src)}" alt="" onerror="this.style.display='none'"><b>×${count.toLocaleString(locale())}</b></span>`;
  }
  function pitCanonRewardTierRange(tier){
    return tier?.maxScore==null?'≥ '+pitCanonWhole(tier?.minScore).toLocaleString(locale()):pitCanonWhole(tier?.minScore).toLocaleString(locale())+'–'+(pitCanonWhole(tier?.maxScore)+1).toLocaleString(locale());
  }
  function pitCanonSetRewardTarget(id,score){
    const defId=String(id||''),stored=pitCanonStored(),old=stored.pits?.[defId]||{},row=pitCanonBuildRows().find(item=>item.definition.id===defId);
    if(!row)return false;
    const value=pitCanonWhole(score);
    if(value>0&&!pitCanonRewardPlan(row,value)?.valid)return false;
    const next={...old,rewardTargetMin:value};
    if(value>0&&old.dailyBaseRuns==null)next.dailyBaseRuns=pitCanonDefaultDailyBaseRuns(row);
    if(value===0&&old.planId==='reward-0')next.planId=row.plans?.[0]?.id||'';
    stored.pits[defId]=next;save({pitsCanon:stored});return true;
  }
  function pitCanonOpenRewardPicker(id){
    pitCanonSaveDom();
    const defId=String(id||''),row=pitCanonBuildRows().find(item=>item.definition.id===defId);
    if(!row)return;
    root?.querySelector('#hk-pit-reward-picker')?.remove();
    const overlay=document.createElement('div');overlay.id='hk-pit-reward-picker';overlay.className='hk-pit-reward-picker-overlay';
    const cards=(row.rewardTiers||[]).map(tier=>{
      const plan=pitCanonRewardPlan(row,tier.minScore),selected=row.rewardTargetMin===tier.minScore,reward=tier.rewardView||{},entries=[...(reward.items||[]),...(reward.currencies||[])];
      const icons=entries.length?entries.map(pitCanonRewardEntryHtml).join(''):'<span>—</span>';
      return `<button type="button" class="hk-pit-reward-card ${selected?'selected':''}" data-pit-reward-score="${tier.minScore}" ${!plan?.valid&&!selected?'disabled':''}><div class="hk-pit-reward-card-top"><strong>${pitCanonRewardTierRange(tier)}</strong><div>${icons}</div></div><div class="hk-pit-reward-card-meta"><span><small>${either('Нужно после базы','Needed after base')}</small><b>${pitCanonWhole(plan?.remainingPoints).toLocaleString(locale())}</b></span><span><small>${either('Доп. x1','Extra x1')}</small><b>${pitCanonWhole(plan?.requiredExtraRuns)}</b></span><span><small>${either('Пропуски Ямы','Pit Passes')}</small><b>🎟 ${pitCanonWhole(plan?.requiredExtraItemCost)}</b></span><span><small>${either('Прогноз очков','Projected points')}</small><b>${pitCanonWhole(plan?.finalScore).toLocaleString(locale())}</b></span></div><div class="hk-pit-reward-card-status ${plan?.valid?'good':'warn'}">${escapeHtml(pitCanonRewardStatus(plan))}</div></button>`;
    }).join('');
    overlay.innerHTML=`<div class="hk-pit-reward-picker-card"><div class="hk-pit-reward-picker-head"><div><small>${either('Ямы · награды турнира','Pits · tournament rewards')}</small><h3>${escapeHtml(pitCanonDefinitionName(row.definition))}</h3></div><button type="button" data-pit-reward-close>×</button></div><div class="hk-pit-reward-picker-live"><span>${either('Очки турнира','Tournament points')} <b>${row.currentScore.toLocaleString(locale())}</b></span><span>${either('До конца','Time left')} <b>${pitCanonFormatRemaining(row.tournamentEndTime)}</b></span></div>${!row.autofinish?`<div class="hk-pit-reward-picker-warning">${either('Включите автозавершение для планирования награды','Enable Auto-finish for reward planning')}</div>`:''}<div class="hk-pit-reward-picker-list">${cards||either('Данные о наградах турнира сейчас недоступны','Tournament reward data is unavailable')}</div><div class="hk-pit-reward-picker-actions"><button type="button" data-pit-reward-clear>${either('Без цели','No target')}</button><button type="button" data-pit-reward-close>${either('Закрыть','Close')}</button></div></div>`;
    overlay.querySelectorAll('[data-pit-reward-close]').forEach(button=>button.onclick=()=>overlay.remove());
    overlay.querySelector('[data-pit-reward-clear]').onclick=()=>{pitCanonSetRewardTarget(defId,0);overlay.remove();pitCanonRender();};
    overlay.querySelectorAll('[data-pit-reward-score]').forEach(button=>button.onclick=()=>{if(!button.disabled&&pitCanonSetRewardTarget(defId,pitCanonWhole(button.dataset.pitRewardScore))){overlay.remove();pitCanonRender();}});
    overlay.addEventListener('click',event=>{if(event.target===overlay)overlay.remove();});root?.appendChild(overlay);
  }

"""
if anchor not in s: raise SystemExit('render anchor missing')
s=s.replace(anchor,helper+anchor,1)
for x in [MARK,"function pitCanonOpenRewardPicker","function pitCanonSetRewardTarget","hk-pit-reward-card"]:
    if x not in s: raise SystemExit('missing r20a invariant: '+x)
p.write_text(s,encoding='utf-8')
print('PITS_REWARD_PICKER_R20A_OK')
