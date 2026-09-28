from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count:
        raise SystemExit(f"{label}: expected {count} got {n}")
    s=s.replace(old,new,count)

rep(
    "// @version      1.18.77",
    "// @version      1.18.78\n"
    "// @release-note Охота за сундуками: видимый неактивированный сундук теперь всегда считается незавершённой целью. Красный/таинственный и другие найденные сундуки забираются раньше оставшихся раскопок; backend-флаг is_bought больше не может ошибочно скрыть уже открытый на поле сундук. Добавлено распознавание новых типов ключей и стоимости прямо с карточки.",
    "version"
)
rep("const BUILD_VERSION = '1.18.77';","const BUILD_VERSION = '1.18.78';","build")

anchor="  const HK_CHEST_KEY_OFFER_REV='chest-key-offer-buy-20260928-r1';"
rep(
    anchor,
    anchor+"\n  const HK_CHEST_VISIBLE_CLAIM_REV='chest-visible-claim-priority-20260928-r1';",
    "visible chest revision"
)

# Fix two escaping regressions from 1.18.77 while touching this module.
rep(
    "/ключs+сокровищ|treasures+key/i.test(text);",
    r"/ключ\s+сокровищ|treasure\s+key/i.test(text);",
    "key offer title regex"
)
rep(
    "const m=text.match(/(?:^|s)(d{1,4})(?:s|$)/);",
    r"const m=text.match(/(?:^|\s)(\d{1,4})(?:\s|$)/);",
    "key offer visual cost regex"
)
rep(
    "/активировано|activated|куплено|purchased|получено|taken|выкуплено|solds*out/i.test(text);",
    r"/активировано|activated|куплено|purchased|получено|taken|выкуплено|sold\s*out/i.test(text);",
    "key offer activated regex"
)

# Resolve a visible chest's cost from live catalog first, then from the actual
# card asset/text. This keeps future chest/key rarities working without a new
# hard-coded branch.
anchor2="""    function treasureChestSignature() {
"""
helper=r'''    function treasureChestVisibleCost(row) {
      if (!row) return null;
      const catalog=treasureChestCost(row.lotId);
      if (catalog) return catalog;

      const text=String(row.text||clean(row.element?.innerText||row.element?.textContent||'')).trim();
      const assets=[...row.element?.querySelectorAll?.('img')||[]]
        .map(img=>String(img.alt||'')+' '+String(img.src||'')).join(' ').toLowerCase();

      const ids=[
        'item_treasurehunt_key_legendary',
        'item_treasurehunt_key_epic',
        'item_treasurehunt_key_rare',
        'item_treasurehunt_key_uncommon',
        'item_treasurehunt_key_common',
        'item_treasurehunt_energy'
      ];
      const itemId=ids.find(id=>assets.includes(id)) || null;
      const m=text.match(/(?:^|\s)(\d{1,4})(?:\s|$)/);
      const quantity=m?Number(m[1]):null;
      if (!itemId || !Number.isFinite(quantity) || quantity<=0) return null;
      return {id:itemId,quantity};
    }

'''
if s.count(anchor2)!=1:
    raise SystemExit("treasureChestSignature anchor missing")
s=s.replace(anchor2,helper+anchor2,1)

# Include all known and future key balances in the signature.
rep(
"""        'item_treasurehunt_key_common',
        'item_treasurehunt_key_uncommon',
        'item_treasurehunt_key_epic'
""",
"""        'item_treasurehunt_key_common',
        'item_treasurehunt_key_uncommon',
        'item_treasurehunt_key_rare',
        'item_treasurehunt_key_epic',
        'item_treasurehunt_key_legendary'
""",
"key balances"
)

old_target="""      // A purchasable Treasure Key offer in Chest Hunt is a resource source for
      // later chests. Buy it before spending actions on digging/chests.
      treasureChestKeyOfferElements().forEach((row,index)=>{
        candidates.push({...row,priority:1400,index:-1000+index});
      });

      rows.forEach((row,index)=>{
        const lotId=row.lotId;
        if (row.activated) return;
        const cost=treasureChestCost(lotId);
        if (!cost || !treasureChestAffordable(cost)) return;
        const unbought=treasureChestUnboughtCount(lotId);
        if (unbought===0) return;
        const digging=/^mf_treasurelot_chest_digging_spot_sl\\d+$/.test(lotId);
        const chest=/^mf_treasurelot_chest_type_(?:01|015|02|03)$/.test(lotId);
        if (!digging && !chest) return;
        // Canon: completely excavate every currently affordable digging spot
        // before spending time/resources on already uncovered chests.
        // Key chests remain available as a recovery path when energy is below 5;
        // if they return energy, digging immediately becomes the top priority again.
        let priority=digging ? 1000 : 300;
        if (lotId==='mf_treasurelot_chest_type_03') priority+=40;
        else if (lotId==='mf_treasurelot_chest_type_02') priority+=30;
        else if (lotId==='mf_treasurelot_chest_type_015') priority+=20;
        else if (lotId==='mf_treasurelot_chest_type_01') priority=180;
        candidates.push({...row,cost,digging,chest,keyOffer:false,priority,index});
      });
"""
new_target=r'''      // A purchasable Treasure Key offer is useful, but an already revealed
      // chest is the most urgent unfinished state in this room.
      treasureChestKeyOfferElements().forEach((row,index)=>{
        candidates.push({...row,priority:1400,index:-1000+index});
      });

      rows.forEach((row,index)=>{
        const lotId=row.lotId;
        if (row.activated) return;

        const digging=/^mf_treasurelot_chest_digging_spot_sl\d+$/.test(lotId);
        const chest=/^mf_treasurelot_chest_type_[a-z0-9]+$/i.test(lotId);
        if (!digging && !chest) return;

        const cost=treasureChestVisibleCost(row);
        if (!cost || !treasureChestAffordable(cost)) return;

        // fair_slots.is_bought is reliable for a digging action, but a revealed
        // chest can stay visibly claimable while backend state already reports
        // the slot as bought. For visible chest cards the DOM state is canonical.
        const unbought=treasureChestUnboughtCount(lotId);
        if (digging && unbought===0) return;

        let priority=digging ? 1000 : 1500;
        if (chest) {
          if (lotId==='mf_treasurelot_chest_type_03') priority+=60;
          else if (lotId==='mf_treasurelot_chest_type_02') priority+=50;
          else if (lotId==='mf_treasurelot_chest_type_015') priority+=40;
          else if (lotId==='mf_treasurelot_chest_type_01') priority+=30;
        }

        candidates.push({...row,cost,digging,chest,keyOffer:false,priority,index});
      });
'''
rep(old_target,new_target,"visible chest targeting")

# Diagnostics identify when a visible chest wins over remaining digs.
rep(
"""      const selected=candidates[0] || null;
      if (!selected && rows.some(row=>row.activated)) {
""",
"""      const selected=candidates[0] || null;
      if (selected?.chest) {
        recordDiagnostic('treasure-chest-visible-claim-target',{
          revision:HK_CHEST_VISIBLE_CLAIM_REV,
          lotId:selected.lotId,
          cost:selected.cost,
          priority:selected.priority,
          remainingDigging:candidates.filter(row=>row.digging).length
        });
      }
      if (!selected && rows.some(row=>row.activated)) {
""",
"visible chest diagnostic"
)

export_anchor="      chestKeyOfferRevision:HK_CHEST_KEY_OFFER_REV,"
if s.count(export_anchor)!=1:
    raise SystemExit("chest key export anchor missing")
s=s.replace(
    export_anchor,
    export_anchor+"\n      chestVisibleClaimRevision:HK_CHEST_VISIBLE_CLAIM_REV,",
    1
)

for marker in [
    "// @version      1.18.78",
    "const BUILD_VERSION = '1.18.78';",
    "chest-visible-claim-priority-20260928-r1",
    "function treasureChestVisibleCost(row)",
    "item_treasurehunt_key_rare",
    "item_treasurehunt_key_legendary",
    "const chest=/^mf_treasurelot_chest_type_[a-z0-9]+$/i.test(lotId);",
    "if (digging && unbought===0) return;",
    "let priority=digging ? 1000 : 1500;",
    "treasure-chest-visible-claim-target",
    "chestVisibleClaimRevision:HK_CHEST_VISIBLE_CLAIM_REV",
    r"/ключ\s+сокровищ|treasure\s+key/i.test(text);",
    "chest-key-offer-buy-20260928-r1",
    "purchase-confirm-fast-global-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

# Visible chests must no longer be rejected by backend is_bought.
if "if (unbought===0) return;\n        const digging=" in s:
    raise SystemExit("old backend gate still present before chest classification")

p.write_text(s,encoding="utf-8")
print("CHEST_VISIBLE_CLAIM_1_18_78=PASS")
