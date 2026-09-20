from pathlib import Path
p=Path('/tmp/HamsterKingMobile.user.js')
s=p.read_text(encoding='utf-8')
MARK="const HK_PITS_REWARD_PICKER_REV = 'pits-reward-picker-20260920-r20';"
if MARK not in s: raise SystemExit('r20a marker missing')

needle="""<label><span>§{either('Цель по награде','Reward target')}</span><select data-pit-reward-target="§{def.id}" §{row.tournamentActive?'':'disabled'}>§{rewardOptions}</select></label>"""
replace="""<label><span>§{either('Цель по награде','Reward target')}</span><select data-pit-reward-target="§{def.id}" §{row.tournamentActive?'':'disabled'}>§{rewardOptions}</select><button type="button" data-pit-reward-open="§{def.id}" §{row.tournamentActive?'':'disabled'}>§{either('Карточки наград','Reward cards')}</button></label>"""
needle=needle.replace('§{','$'+'{');replace=replace.replace('§{','$'+'{')
if needle not in s: raise SystemExit('reward target control anchor missing')
s=s.replace(needle,replace,1)

needle="    box.querySelector('#hk-pits-start').onclick=runPitsCanonical;\n"
replace="    box.querySelectorAll('[data-pit-reward-open]').forEach(button=>button.onclick=()=>pitCanonOpenRewardPicker(button.dataset.pitRewardOpen));\n"+needle
if needle not in s: raise SystemExit('start handler anchor missing')
s=s.replace(needle,replace,1)

old="[data-pit-reward-target],[data-pit-daily-base-runs]"
new="[data-pit-reward-target],[data-pit-reward-open],[data-pit-daily-base-runs]"
if old not in s: raise SystemExit('busy selector anchor missing')
s=s.replace(old,new,1)

for x in ["data-pit-reward-open","pitCanonOpenRewardPicker(button.dataset.pitRewardOpen)"]:
    if x not in s: raise SystemExit('missing r20b invariant: '+x)
p.write_text(s,encoding='utf-8')
print('PITS_REWARD_PICKER_R20B_OK')
