from pathlib import Path
p=Path('/tmp/HamsterKingMobile.user.js')
s=p.read_text(encoding='utf-8')

BASE="const HK_PITS_RESPAWN_REV = 'pits-respawn-cost-20260920-r6';"
MARK="const HK_PITS_POWER_TABLE_REV = 'pits-power-table-collapsed-20260920-r7';"
if MARK in s:
    raise SystemExit('already applied')
if BASE not in s:
    raise SystemExit('r6 marker missing')

s=s.replace(BASE, BASE+"\n  "+MARK, 1)

old="  let pitPowerTableOpen = true;"
new="  let pitPowerTableOpen = false;"
if old not in s:
    raise SystemExit('pitPowerTableOpen anchor missing')
s=s.replace(old,new,1)

if "let pitPowerTableOpen = true;" in s:
    raise SystemExit('old default remains')
if new not in s or MARK not in s:
    raise SystemExit('r7 invariant missing')

p.write_text(s,encoding='utf-8')
print('PITS_POWER_TABLE_R7_PATCH_OK')
