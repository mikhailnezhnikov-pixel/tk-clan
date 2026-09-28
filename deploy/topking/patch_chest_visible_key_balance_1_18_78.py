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
    "// @release-note Охота за сундуками: ключевые сундуки больше не пропускаются, если API-кошелёк ключей на мобильном отстал от интерфейса. Для Обычного/Необычного/Эпического сундука учитывается видимый счётчик ключей на самой карточке; открытый доступный сундук блокирует преждевременный выход из комнаты.",
    "version"
)
rep("const BUILD_VERSION = '1.18.77';","const BUILD_VERSION = '1.18.78';","build")

anchor="  const HK_CHEST_KEY_OFFER_REV='chest-key-offer-buy-20260928-r1';"
rep(
    anchor,
    anchor+"\n  const HK_CHEST_VISIBLE_KEY_BALANCE_REV='chest-visible-key-balance-20260928-r1';",
    "visible key balance revision"
)

old_aff="""    function treasureChestAffordable(cost) {
      if (!cost?.id || !(cost.quantity>0)) return false;
      const balance=walletAmount(cost.id);
      return balance!==null && balance>=cost.quantity;
    }
"""
new_aff="""    function treasureChestCardUsable(element) {
      if (!element || !visible(element)) return false;
      const style=getComputedStyle(element);
      const cls=String(element.className||'');
      return !element.disabled &&
        element.getAttribute?.('aria-disabled')!=='true' &&
        style.pointerEvents!=='none' &&
        !/disabled|locked|blocked|bought|activated/i.test(cls);
    }

    function treasureChestVisibleKeyBalance(element,text='') {
      if (!element) return null;
      const values=[];
      const push=value=>{
        const n=Number(value);
        if (Number.isFinite(n) && n>=0 && n<=99999) values.push(n);
      };

      String(text||'').match(/[0-9]{1,5}/g)?.forEach(push);
      [...element.querySelectorAll?.('span,div,p,strong,b')||[]]
        .filter(visible)
        .forEach(node=>{
          const t=clean(node.innerText||node.textContent||'').trim();
          if (/^[0-9]{1,5}$/.test(t)) push(t);
        });

      return values.length ? Math.max(...values) : null;
    }

    function treasureChestAffordable(cost,element=null,text='') {
      if (!cost?.id || !(cost.quantity>0)) return false;
      const balance=walletAmount(cost.id);
      if (balance!==null && balance>=cost.quantity) return true;

      // On mobile the item wallet can lag behind the Chest Hunt UI. The chest
      // card itself shows the current owned-key count (for example 3 under the
      // purple Uncommon/Mysterious chest). Use that visible count only for key
      // gated chests and only while the card remains interactable.
      if (/^item_treasurehunt_key_/.test(String(cost.id||'')) && treasureChestCardUsable(element)) {
        const visibleBalance=treasureChestVisibleKeyBalance(element,text);
        if (visibleBalance!==null && visibleBalance>=cost.quantity) {
          recordDiagnostic('treasure-chest-visible-key-balance',{
            revision:HK_CHEST_VISIBLE_KEY_BALANCE_REV,
            itemId:String(cost.id||''),
            apiBalance:balance,
            visibleBalance,
            required:Number(cost.quantity||0)
          });
          return true;
        }
      }
      return false;
    }
"""
rep(old_aff,new_aff,"visual key affordability")

rep(
"        .filter(row=>row.lotId && !row.activated && row.cost && treasureChestAffordable(row.cost))",
"        .filter(row=>row.lotId && !row.activated && row.cost && treasureChestAffordable(row.cost,row.element,row.text))",
"key offer affordability"
)

rep(
"        if (!cost || !treasureChestAffordable(cost)) return;",
"        if (!cost || !treasureChestAffordable(cost,row.element,row.text)) return;",
"chest target affordability"
)

# The visible card is stronger than a stale fair-state snapshot. Never let a
# stale is_bought=true snapshot suppress an actually visible, interactable chest.
old_unbought="""        const unbought=treasureChestUnboughtCount(lotId);
        if (unbought===0) return;
        const digging=/^mf_treasurelot_chest_digging_spot_sl\\d+$/.test(lotId);
"""
new_unbought="""        const unbought=treasureChestUnboughtCount(lotId);
        if (unbought===0 && !treasureChestCardUsable(row.element)) return;
        if (unbought===0) {
          recordDiagnostic('treasure-chest-visible-overrides-stale-state',{
            revision:HK_CHEST_VISIBLE_KEY_BALANCE_REV,
            lotId,
            text:row.text
          });
        }
        const digging=/^mf_treasurelot_chest_digging_spot_sl\\d+$/.test(lotId);
"""
rep(old_unbought,new_unbought,"visible card overrides stale state")

# Key-gated chests must be consumed before AutoMap can consider leaving the room.
old_priority="""        let priority=digging ? 1000 : 300;
        if (lotId==='mf_treasurelot_chest_type_03') priority+=40;
        else if (lotId==='mf_treasurelot_chest_type_02') priority+=30;
        else if (lotId==='mf_treasurelot_chest_type_015') priority+=20;
        else if (lotId==='mf_treasurelot_chest_type_01') priority=180;
"""
new_priority="""        let priority=digging ? 1000 : 300;
        if (lotId==='mf_treasurelot_chest_type_03') priority=1330;
        else if (lotId==='mf_treasurelot_chest_type_02') priority=1320;
        else if (lotId==='mf_treasurelot_chest_type_015') priority=1310;
        else if (lotId==='mf_treasurelot_chest_type_01') priority=180;
"""
rep(old_priority,new_priority,"key chest priority")

# Fix the escaped text fallbacks introduced with 1.18.77. They are secondary
# fallbacks, but must remain valid on layouts where catalog metadata is absent.
rep("/ключs+сокровищ|treasures+key/i.test(text);","/ключ[ ]+сокровищ|treasure[ ]+key/i.test(text);","key offer text regex")
rep("const m=text.match(/(?:^|s)(d{1,4})(?:s|$)/);","const m=text.match(/(?:^|[^0-9])([0-9]{1,4})(?:[^0-9]|$)/);","key offer numeric regex")
rep("const activated=/активировано|activated|куплено|purchased|получено|taken|выкуплено|solds*out/i.test(text);","const activated=/активировано|activated|куплено|purchased|получено|taken|выкуплено|sold[ ]*out/i.test(text);","key offer activated regex")

export_anchor="      chestKeyOfferRevision:HK_CHEST_KEY_OFFER_REV,"
if s.count(export_anchor)!=1:
    raise SystemExit("chest key offer export anchor missing")
s=s.replace(
    export_anchor,
    export_anchor+"\n      chestVisibleKeyBalanceRevision:HK_CHEST_VISIBLE_KEY_BALANCE_REV,",
    1
)

for marker in [
    "// @version      1.18.78",
    "const BUILD_VERSION = '1.18.78';",
    "chest-visible-key-balance-20260928-r1",
    "function treasureChestVisibleKeyBalance(element,text='')",
    "treasure-chest-visible-key-balance",
    "treasure-chest-visible-overrides-stale-state",
    "priority=1320",
    "chestVisibleKeyBalanceRevision:HK_CHEST_VISIBLE_KEY_BALANCE_REV",
    "chest-key-offer-buy-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

p.write_text(s,encoding="utf-8")
print("CHEST_VISIBLE_KEY_BALANCE_1_18_78=PASS")
