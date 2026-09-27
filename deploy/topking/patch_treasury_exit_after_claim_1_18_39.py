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

rep("// @version      1.18.38",
    "// @version      1.18.39\n// @release-note Сокровищница: после получения большого сундука Автокарта больше не пытается нажимать уже «Активировано». Завершённая центральная награда имеет приоритет над оставшимся DOM комнаты: скрипт сразу находит реальную нижнюю кнопку «Покинуть локацию», нажимает её и возвращается на Карту Сокровищ.",
    "version")
rep("const BUILD_VERSION = '1.18.38';",
    "const BUILD_VERSION = '1.18.39';",
    "build")
rep("  const HK_TRADER_KEYS_FAST_REV = 'trader-keys-fast-20260927-r1';",
    "  const HK_TRADER_KEYS_FAST_REV = 'trader-keys-fast-20260927-r1';\n  const HK_TREASURY_EXIT_AFTER_CLAIM_REV = 'treasury-exit-after-claim-20260927-r1';",
    "revision")

old_chest="""    function autoMapTreasuryChest() {
      return [...document.querySelectorAll('[data-lot-id*="mf_fairlot_minigame_treasury_room_big_chest"]')]
        .filter(visible)[0] || null;
    }
"""
new_chest="""    function autoMapTreasuryChestRows() {
      return [...document.querySelectorAll('[data-lot-id*="mf_fairlot_minigame_treasury_room_big_chest"]')]
        .filter(visible)
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const cls=String(element.className||'');
          const activated=
            /(?:^|\\s)(?:Активировано|Activated|Получено|Claimed)(?:\\s|$)/i.test(text) ||
            /activated|claimed|completed|bought/i.test(cls);
          return {element,text,cls,activated};
        });
    }

    function autoMapTreasuryChest() {
      return autoMapTreasuryChestRows()
        .find(row=>!row.activated)?.element || null;
    }

    function autoMapTreasuryCompleted() {
      return autoMapTreasuryChestRows().some(row=>row.activated);
    }
"""
rep(old_chest,new_chest,"treasury completion state")

old_exit="""    function autoMapExitButton() {
      return autoMapFindTextButton(/^(?:Покинуть локацию|Покинуть локацию\\s*›?|Leave location|Exit location)$/i);
    }
"""
new_exit="""    function autoMapExitButton() {
      const pattern=/^(?:Покинуть локацию|Leave location|Exit location)(?:\\s*[›>»→])?$/i;
      const nodes=[...document.querySelectorAll('button,[role="button"],a,[onclick],div,span')]
        .filter(element=>element && element!==autoMapToggle && !element.disabled && visible(element));

      const rows=[];
      for (const element of nodes) {
        const text=clean(element.innerText||element.textContent||'').trim();
        if (!pattern.test(text)) continue;

        let target=element;
        let node=element;
        for (let depth=0;node && depth<6;depth++,node=node.parentElement) {
          if (!visible(node)) continue;
          let actionable=false;
          try {
            actionable=
              node.matches?.('button,[role="button"],a,[onclick]') ||
              !!node.onclick ||
              getComputedStyle(node).cursor==='pointer';
          } catch (_) {}
          if (actionable) {
            target=node;
            break;
          }
        }

        const rect=target.getBoundingClientRect?.() || {left:0,top:0,width:0,height:0};
        const cx=rect.left+rect.width/2;
        const cy=rect.top+rect.height/2;
        let score=0;
        if (rect.width>=window.innerWidth*0.28) score+=160;
        if (rect.height>=38 && rect.height<=150) score+=80;
        if (cy>=window.innerHeight*0.65) score+=120;
        if (Math.abs(cx-window.innerWidth/2)<=window.innerWidth*0.32) score+=80;
        rows.push({element:target,score,area:rect.width*rect.height});
      }

      rows.sort((a,b)=>b.score-a.score || b.area-a.area);
      return rows[0]?.element || null;
    }
"""
rep(old_exit,new_exit,"robust exit button")

old_fp="""      const treasury=[
        ...document.querySelectorAll('[data-lot-id^="mf_fair_treasury_room_choose_way_"],[data-lot-id*="mf_fairlot_minigame_treasury_room_big_chest"]')
      ].filter(visible).map(el=>el.getAttribute('data-lot-id')).join(',');
"""
new_fp="""      const treasury=[
        ...document.querySelectorAll('[data-lot-id^="mf_fair_treasury_room_choose_way_"],[data-lot-id*="mf_fairlot_minigame_treasury_room_big_chest"]')
      ].filter(visible).map(el=>[
        el.getAttribute('data-lot-id'),
        clean(el.innerText||el.textContent||'').trim(),
        clean(el.className||'')
      ].join('#')).join(',');
"""
rep(old_fp,new_fp,"treasury fingerprint state")

old_branch="""        // Treasury room after the boss: first choose route 1 (recorded canonical run),
        // then open the big chest, collect reward and leave normally.
        const choice=autoMapTreasuryChoice();
        if (choice) {
          autoMapStatus('treasury путь');
          return autoMapTapAndConfirm(choice.element,'treasury-'+choice.lotId,choice.cost);
        }
        const treasuryChest=autoMapTreasuryChest();
        if (treasuryChest) {
          autoMapStatus('treasury сундук');
          return autoMapTapAndConfirm(treasuryChest,'treasury-big-chest',null);
        }
"""
new_branch="""        // Treasury room after the boss. Once the big chest is visibly Activated,
        // the room is complete even if its DOM tile remains present. Exit must
        // win before route/chest selectors so the claimed chest is never re-opened.
        if (autoMapTreasuryCompleted()) {
          const exit=autoMapExitButton();
          if (exit) {
            autoMapStatus('treasury выход',{
              revision:HK_TREASURY_EXIT_AFTER_CLAIM_REV
            });
            const left=await autoMapTapAndConfirm(exit,'treasury-leave-location',null);
            if (left) {
              autoMapCurrentLot='';
              lastSignature='';
              autoMapReturnNotBefore=Date.now()+350;
              recordDiagnostic('treasury-exit-after-claim',{
                revision:HK_TREASURY_EXIT_AFTER_CLAIM_REV,
                result:'clicked'
              });
              setTimeout(()=>void runAutoMapTick('treasury-left-location'),420);
            }
            return left;
          }

          autoMapStatus('treasury жду выход',{
            revision:HK_TREASURY_EXIT_AFTER_CLAIM_REV
          });
          return false;
        }

        const choice=autoMapTreasuryChoice();
        if (choice) {
          autoMapStatus('treasury путь');
          return autoMapTapAndConfirm(choice.element,'treasury-'+choice.lotId,choice.cost);
        }
        const treasuryChest=autoMapTreasuryChest();
        if (treasuryChest) {
          autoMapStatus('treasury сундук');
          return autoMapTapAndConfirm(treasuryChest,'treasury-big-chest',null);
        }
"""
rep(old_branch,new_branch,"treasury exit priority")

rep("      traderKeysFastRevision:HK_TRADER_KEYS_FAST_REV,\n      start,",
    "      traderKeysFastRevision:HK_TRADER_KEYS_FAST_REV,\n      treasuryExitAfterClaimRevision:HK_TREASURY_EXIT_AFTER_CLAIM_REV,\n      start,",
    "export treasury revision")

for marker in [
    "// @version      1.18.39",
    "const BUILD_VERSION = '1.18.39';",
    "treasury-exit-after-claim-20260927-r1",
    "function autoMapTreasuryChestRows()",
    "function autoMapTreasuryCompleted()",
    "treasury выход",
    "treasury-leave-location",
    "treasury-exit-after-claim",
    "lights-fast-confirm-20260927-r1",
    "trader-keys-fast-20260927-r1",
    "lights-cost10-exit-20260927-r1"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("TREASURY_EXIT_AFTER_CLAIM_1_18_39=PASS")

# trigger build after workflow installation
