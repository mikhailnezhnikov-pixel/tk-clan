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
    "// @version      1.18.76",
    "// @version      1.18.77\n"
    "// @release-note Охота за сундуками: добавлен выкуп отдельного лота ключа сокровищ за ягоды. Карточка ключа теперь распознаётся по ключевому предмету/иконке, стоимость берётся из каталога или с карточки, и при достаточном балансе покупка имеет приоритет перед раскопками и сундуками.",
    "version"
)
rep("const BUILD_VERSION = '1.18.76';","const BUILD_VERSION = '1.18.77';","build")

anchor="  const HK_TRADER_GOLD_SKIP_REV='trader-gold-currency-skip-20260928-r1';"
rep(
    anchor,
    anchor+"\n  const HK_CHEST_KEY_OFFER_REV='chest-key-offer-buy-20260928-r1';",
    "chest key offer revision"
)

anchor2="""    function treasureChestElements() {
"""
helper=r'''    function treasureChestKeyOfferElements() {
      const rows=[...document.querySelectorAll('[data-lot-id]')]
        .filter(visible)
        .map(element=>{
          const lotId=String(element.getAttribute('data-lot-id')||'');
          const text=clean(element.innerText||element.textContent||'').trim();
          const catalogRow=fairCatalog.find(row=>String(row?.lotId||'')===lotId) || null;
          const catalogText=JSON.stringify(catalogRow||{});
          const assets=[...element.querySelectorAll?.('img')||[]]
            .map(img=>String(img.alt||'')+' '+String(img.src||'')).join(' ');
          const blob=[lotId,text,catalogText,assets].join(' ').toLowerCase();

          // This is the standalone key purchase card, not a chest that consumes
          // a key. The screenshot/card uses the Treasure Key item artwork.
          const keyOffer=
            /item_treasurehunt_key_(?:common|uncommon|rare|epic|legendary)/.test(blob) ||
            /(?:^|[_-])key_(?:common|uncommon|rare|epic|legendary)(?:[_-]|$)/.test(lotId.toLowerCase()) ||
            /ключs+сокровищ|treasures+key/i.test(text);

          const chestCard=/^mf_treasurelot_chest_type_/.test(lotId);
          const digging=/^mf_treasurelot_chest_digging_spot_/.test(lotId);
          if (!keyOffer || chestCard || digging) return null;

          const parts=costParts(catalogRow?.cost).filter(part=>part.quantity>0);
          let cost=parts.length===1 ? {id:parts[0].id,quantity:parts[0].quantity} : null;

          // Fallback for the visual card shown in Chest Hunt: berry icon + 10.
          if (!cost) {
            const m=text.match(/(?:^|s)(d{1,4})(?:s|$)/);
            const quantity=m?Number(m[1]):null;
            if (Number.isFinite(quantity) && quantity>0) {
              cost={id:'item_treasurehunt_energy',quantity};
            }
          }

          const rect=element.getBoundingClientRect?.() || {left:0,top:0,width:0,height:0};
          const activated=/активировано|activated|куплено|purchased|получено|taken|выкуплено|solds*out/i.test(text);
          return {
            element,
            lotId,
            text,
            cost,
            activated,
            keyOffer:true,
            digging:false,
            chest:false,
            x:Math.round(rect.left+rect.width/2),
            y:Math.round(rect.top+rect.height/2)
          };
        })
        .filter(Boolean)
        .filter(row=>row.lotId && !row.activated && row.cost && treasureChestAffordable(row.cost))
        .filter(row=>!row.element.closest?.('[data-lot-id^="mf_treasurelot_active_sl"]'));

      return rows;
    }

'''
if s.count(anchor2)!=1:
    raise SystemExit("treasureChestElements anchor missing")
s=s.replace(anchor2,helper+anchor2,1)

old_target="""    function treasureChestTarget() {
      const rows=treasureChestElements();
      const candidates=[];
      rows.forEach((row,index)=>{
        const lotId=row.lotId;
        if (row.activated) return;
        const cost=treasureChestCost(lotId);
        if (!cost || !treasureChestAffordable(cost)) return;
        const unbought=treasureChestUnboughtCount(lotId);
        if (unbought===0) return;
        const digging=/^mf_treasurelot_chest_digging_spot_sl\d+$/.test(lotId);
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
        candidates.push({...row,cost,digging,chest,priority,index});
      });
"""
new_target="""    function treasureChestTarget() {
      const rows=treasureChestElements();
      const candidates=[];

      // A purchasable Treasure Key offer in Chest Hunt is a resource source for
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
        const digging=/^mf_treasurelot_chest_digging_spot_sl\d+$/.test(lotId);
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
rep(old_target,new_target,"chest key offer priority")

# Include key-offer state in the chest signature so purchase completion is
# observed even when the regular chest grid itself does not redraw.
old_sig="""      const balances=[
        'item_treasurehunt_energy',
        'item_treasurehunt_key_common',
        'item_treasurehunt_key_uncommon',
        'item_treasurehunt_key_epic'
      ].map(id=>id+'='+String(walletAmount(id))).join(',');
      return 'CHESTS|'+rows.join('|')+'|'+balances;
"""
new_sig="""      const keyOffers=treasureChestKeyOfferElements()
        .map(row=>row.lotId+'#'+row.text+'#'+String(row.cost?.id||'')+'='+String(row.cost?.quantity||0))
        .sort()
        .join(',');
      const balances=[
        'item_treasurehunt_energy',
        'item_treasurehunt_key_common',
        'item_treasurehunt_key_uncommon',
        'item_treasurehunt_key_epic'
      ].map(id=>id+'='+String(walletAmount(id))).join(',');
      return 'CHESTS|'+rows.join('|')+'|KEY_OFFERS='+keyOffers+'|'+balances;
"""
rep(old_sig,new_sig,"key offer signature")

rep(
"""      recordDiagnostic('chest-auto-start',{
        revision:HK_CHEST_AUTO_REV,
        lotId:target.lotId,
        cost:target.cost,
        balance:beforeBalance,
        digging:target.digging
      });
""",
"""      recordDiagnostic('chest-auto-start',{
        revision:target.keyOffer?HK_CHEST_KEY_OFFER_REV:HK_CHEST_AUTO_REV,
        lotId:target.lotId,
        cost:target.cost,
        balance:beforeBalance,
        digging:target.digging,
        keyOffer:!!target.keyOffer
      });
""",
"key offer start diagnostic"
)

rep(
"        dispatchAutoMapTap(target.element,target.digging?'chest-dig-spot':'chest-open-card');",
"        dispatchAutoMapTap(target.element,target.keyOffer?'chest-buy-key-card':(target.digging?'chest-dig-spot':'chest-open-card'));",
"key offer open label"
)

rep(
"        if (action) tapped=dispatchAutoMapTap(action,target.digging?'chest-dig-confirm':'chest-open-confirm');",
"        if (action) tapped=dispatchAutoMapTap(action,target.keyOffer?'chest-buy-key-confirm':(target.digging?'chest-dig-confirm':'chest-open-confirm'));",
"key offer confirm label"
)

rep(
"""        recordDiagnostic('chest-auto-complete',{
          revision:HK_CHEST_AUTO_REV,
          lotId:target.lotId,
          digging:target.digging,
          rewardsDismissed:rewards,
          beforeBalance,
          afterBalance:walletAmount(target.cost.id)
        });
""",
"""        recordDiagnostic('chest-auto-complete',{
          revision:target.keyOffer?HK_CHEST_KEY_OFFER_REV:HK_CHEST_AUTO_REV,
          lotId:target.lotId,
          digging:target.digging,
          keyOffer:!!target.keyOffer,
          rewardsDismissed:rewards,
          beforeBalance,
          afterBalance:walletAmount(target.cost.id)
        });
""",
"key offer completion diagnostic"
)

export_anchor="      traderGoldSkipRevision:HK_TRADER_GOLD_SKIP_REV,"
if s.count(export_anchor)!=1:
    raise SystemExit("trader gold export anchor missing")
s=s.replace(
    export_anchor,
    export_anchor+"\n      chestKeyOfferRevision:HK_CHEST_KEY_OFFER_REV,",
    1
)

for marker in [
    "// @version      1.18.77",
    "const BUILD_VERSION = '1.18.77';",
    "chest-key-offer-buy-20260928-r1",
    "function treasureChestKeyOfferElements()",
    "item_treasurehunt_key_(?:common|uncommon|rare|epic|legendary)",
    "cost={id:'item_treasurehunt_energy',quantity};",
    "priority:1400",
    "KEY_OFFERS=",
    "chest-buy-key-card",
    "chest-buy-key-confirm",
    "chestKeyOfferRevision:HK_CHEST_KEY_OFFER_REV",
    "trader-gold-currency-skip-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

p.write_text(s,encoding="utf-8")
print("CHEST_KEY_OFFER_1_18_77=PASS")
