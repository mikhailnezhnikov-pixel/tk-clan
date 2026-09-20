from pathlib import Path

p=Path('/tmp/HamsterKingMobile.user.js')
s=p.read_text(encoding='utf-8')

BASE_MARKER="const HK_PITS_CANON_REV = 'pits-canon-core-20260920-r1';"
UI_MARKER="const HK_PITS_UI_REV = 'pits-ui-align-20260920-r2';"

if UI_MARKER in s:
    raise SystemExit('already applied')
if BASE_MARKER not in s:
    raise SystemExit('Pits Core r1 marker missing')

s=s.replace(BASE_MARKER, BASE_MARKER+"\n  "+UI_MARKER, 1)

old=".hk-pit-canon-grid{display:grid;gap:8px}.hk-pit-canon-grid>label{display:grid;grid-template-columns:minmax(0,1fr) 145px;gap:8px;align-items:center}.hk-pit-canon-grid>label>span{font-size:10px;color:#b9c6d7;line-height:1.25}.hk-pit-canon-grid select,.hk-pit-canon-grid input[type=number]{width:100%;min-width:0;background:#0b111b;color:#fff;border:1px solid #3b4a61;border-radius:10px;padding:8px;font-size:10px}.hk-pit-canon-check input{justify-self:end;width:18px;height:18px}"
new=".hk-pit-canon-grid{display:grid;gap:9px;max-width:820px}.hk-pit-canon-grid>label{display:grid;grid-template-columns:minmax(190px,260px) minmax(220px,360px);gap:12px;align-items:center;justify-content:start}.hk-pit-canon-grid>label>span{font-size:10px;color:#b9c6d7;line-height:1.25}.hk-pit-canon-grid select,.hk-pit-canon-grid input[type=number]{width:100%;min-width:0;background:#0b111b;color:#fff;border:1px solid #3b4a61;border-radius:10px;padding:8px;font-size:10px}.hk-pit-canon-check input{justify-self:start;width:18px;height:18px}"

if old not in s:
    raise SystemExit('Pits grid CSS anchor missing')
s=s.replace(old,new,1)

old_mobile="@media(max-width:430px){.hk-pits-summary{grid-template-columns:1fr 1fr}.hk-pits-summary>div:last-child{grid-column:1/-1}.hk-pits-toolbar{grid-template-columns:1fr}.hk-pit-canon-grid>label{grid-template-columns:1fr}.hk-pit-canon-head{grid-template-columns:38px minmax(0,1fr)}"
new_mobile="@media(max-width:760px){.hk-pit-canon-grid{max-width:none}.hk-pit-canon-grid>label{grid-template-columns:minmax(150px,220px) minmax(0,1fr)}}@media(max-width:430px){.hk-pits-summary{grid-template-columns:1fr 1fr}.hk-pits-summary>div:last-child{grid-column:1/-1}.hk-pits-toolbar{grid-template-columns:1fr}.hk-pit-canon-grid>label{grid-template-columns:1fr}.hk-pit-canon-head{grid-template-columns:38px minmax(0,1fr)}"

if old_mobile not in s:
    raise SystemExit('Pits mobile CSS anchor missing')
s=s.replace(old_mobile,new_mobile,1)

for needle in [BASE_MARKER,UI_MARKER,'.hk-pit-canon-grid{display:grid;gap:9px;max-width:820px}','justify-self:start;width:18px;height:18px']:
    if needle not in s:
        raise SystemExit('missing invariant: '+needle)

p.write_text(s,encoding='utf-8')
print('PITS_UI_ALIGN_R2_PATCH_OK')
