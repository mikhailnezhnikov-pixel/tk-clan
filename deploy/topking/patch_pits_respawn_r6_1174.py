from pathlib import Path
p=Path('/tmp/HamsterKingMobile.user.js')
s=p.read_text(encoding='utf-8')

BASE="const HK_PITS_START_REV = 'pits-start-config-snapshot-20260920-r5';"
MARK="const HK_PITS_RESPAWN_REV = 'pits-respawn-cost-20260920-r6';"
if MARK in s:
    raise SystemExit('already applied')
if BASE not in s:
    raise SystemExit('r5 marker missing')

s=s.replace(BASE, BASE+"\n  "+MARK, 1)

anchor="""  function pitCanonDirectPassCost(state,mass,payment) {
    const prem=payment==='PREM';
    const row=(state?.pass_costs||[]).find(entry=>entry?.is_prem===prem&&pitCanonWhole(entry?.mass_multiplier)===pitCanonWhole(mass));
    if(!row)return null;
    return pitCanonCostQuantity(row?.cost,prem?'cur_prem':HK_PIT_PASS_ITEM_ID,prem?'currency':'item');
  }

"""
if anchor not in s:
    raise SystemExit('direct pass helper anchor missing')

helper="""  function pitCanonDirectPassCost(state,mass,payment) {
    const prem=payment==='PREM';
    const row=(state?.pass_costs||[]).find(entry=>entry?.is_prem===prem&&pitCanonWhole(entry?.mass_multiplier)===pitCanonWhole(mass));
    if(!row)return null;
    return pitCanonCostQuantity(row?.cost,prem?'cur_prem':HK_PIT_PASS_ITEM_ID,prem?'currency':'item');
  }

  function pitCanonRespawnCost(state,chunk=1) {
    const options=Array.isArray(state?.respawn_costs)?state.respawn_costs:[];
    const option=options.find(row=>row?.is_prem===false);
    const quantity=pitCanonCostQuantity(option,HK_PIT_RESTORATION_ITEM_ID,'item');
    return pitCanonWhole(quantity)||Math.max(1,pitCanonWhole(chunk));
  }

"""
s=s.replace(anchor,helper,1)

for needle in [
    MARK,
    "function pitCanonRespawnCost(state,chunk=1)",
    "const option=options.find(row=>row?.is_prem===false);",
    "return pitCanonWhole(quantity)||Math.max(1,pitCanonWhole(chunk));",
    "const cost=pitCanonRespawnCost(state,chunk)"
]:
    if needle not in s:
        raise SystemExit('missing invariant: '+needle)

p.write_text(s,encoding='utf-8')
print('PITS_RESPAWN_R6_PATCH_OK')
