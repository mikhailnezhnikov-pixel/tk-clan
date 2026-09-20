from pathlib import Path
p=Path('/tmp/HamsterKingMobile.user.js')
s=p.read_text(encoding='utf-8')

BASE="const HK_PITS_SNIPER_REV = 'pits-passplan-sniper-20260920-r3';"
MARK="const HK_PITS_TOOLBAR_REV = 'pits-toolbar-clean-20260920-r4';"
if MARK in s:
    raise SystemExit('already applied')
if BASE not in s:
    raise SystemExit('r3 marker missing')

s=s.replace(BASE, BASE+"\n  "+MARK, 1)

old='<div class="hk-pits-toolbar"><button id="hk-pits-refresh" class="hk-secondary">${either(\'Обновить данные\',\'Refresh live data\')}</button><label class="hk-pit-canon-global">'
new='<div class="hk-pits-toolbar"><label class="hk-pit-canon-global">'
if old not in s:
    raise SystemExit('toolbar button anchor missing')
s=s.replace(old,new,1)

old_line="    box.querySelector('#hk-pits-refresh').onclick=()=>refreshModuleLive('pit',{force:true});\n"
if old_line not in s:
    raise SystemExit('refresh handler anchor missing')
s=s.replace(old_line,'',1)

old_css='.hk-pits-toolbar{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:8px;margin-bottom:10px}'
new_css='.hk-pits-toolbar{display:grid;grid-template-columns:minmax(0,1fr);gap:8px;margin-bottom:10px}'
if old_css not in s:
    raise SystemExit('toolbar css anchor missing')
s=s.replace(old_css,new_css,1)

for needle in [MARK,'id="hk-pits-refresh"',"#hk-pits-refresh"]:
    if needle==MARK:
        assert needle in s
    else:
        assert needle not in s

p.write_text(s,encoding='utf-8')
print('PITS_TOOLBAR_CLEAN_R4_PATCH_OK')
