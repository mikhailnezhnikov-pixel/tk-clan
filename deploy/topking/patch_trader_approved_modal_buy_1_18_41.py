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

rep("// @version      1.18.40",
    "// @version      1.18.41\n// @release-note Тайный торговец: в автопокупку добавлены Вкусняшки для питомца, Необычные/другие ключи сокровищ, Походные припасы и Смена навыка питомца. Подтверждение покупки теперь нажимает реальный кликабельный контейнер нижней кнопки цены, а не вложенный текст/иконку; уже открытая одобренная модалка также подхватывается и подтверждается автоматически. Яйца питомцев по-прежнему исключены.",
    "version")
rep("const BUILD_VERSION = '1.18.40';",
    "const BUILD_VERSION = '1.18.41';",
    "build")
rep("  const HK_TREASURY_VISUAL_EXIT_REV = 'treasury-visual-exit-20260927-r2';",
    "  const HK_TREASURY_VISUAL_EXIT_REV = 'treasury-visual-exit-20260927-r2';\n  const HK_TRADER_APPROVED_MODAL_REV = 'trader-approved-modal-buy-20260927-r1';",
    "revision")

old_approved="""    function traderApprovedLot(lotId) {
      const id=String(lotId||'').toLowerCase();
      if (!id) return false;

      // Treasure coins.
      if (/random4coins/.test(id) || /treasure[_-]?coins/.test(id)) return true;

      // Keys are explicitly approved too (common/uncommon/rare/epic/legendary).
      if (/key_(?:common|uncommon|rare|epic|legendary)4coins/.test(id)) return true;

      // Berries/food lots.
      if (/(?:^|_)food(?:_|$)/.test(id) || /berr(?:y|ies)/.test(id)) return true;

      // Treasure maps.
      if (/(?:^|_)map(?:_|$)/.test(id) || /treasure[_-]?map/.test(id)) return true;

      return false;
    }
"""
new_approved="""    function traderApprovedLot(lotId) {
      const id=String(lotId||'').toLowerCase();
      if (!id) return false;

      // Never buy pet/fish eggs automatically.
      if (/fish_egg|pet_egg|egg_/.test(id)) return false;

      // Treasure coins.
      if (/random4coins/.test(id) || /treasure[_-]?coins/.test(id)) return true;

      // Any treasure key rarity. New trader lots are not always suffixed 4coins.
      if (/key_(?:common|uncommon|rare|epic|legendary)/.test(id) ||
          /treasure(?:hunt)?[_-]?key/.test(id)) return true;

      // Berries/food/provisions.
      if (/(?:^|_)food(?:_|$)/.test(id) || /berr(?:y|ies)/.test(id) ||
          /provision|suppl(?:y|ies)|energy/.test(id)) return true;

      // Pet treats / pet skill change consumables.
      if (/pet.*(?:food|treat|snack)/.test(id) ||
          /(?:food|treat|snack).*pet/.test(id) ||
          /pet.*skill|skill.*pet/.test(id)) return true;

      // Treasure maps.
      if (/(?:^|_)map(?:_|$)/.test(id) || /treasure[_-]?map/.test(id)) return true;

      return false;
    }

    function traderApprovedRow(row) {
      if (!row) return false;
      if (traderApprovedLot(row.lotId)) return true;

      const catalog=traderCatalogRow(row.lotId);
      const rewardId=String(catalog?.rewardId||'').toLowerCase();
      const name=String(catalog?.name||'').toLowerCase();
      const text=String(row.text||'').toLowerCase();
      const blob=[row.lotId,rewardId,name,text].join(' ');

      // Keep the historical egg exclusion even when another field contains
      // generic words like pet/food.
      if (/fish_egg|pet_egg|egg_/.test(blob)) return false;

      if (/item_treasurehunt_key_(?:common|uncommon|rare|epic|legendary)/.test(blob)) return true;
      if (/treasure(?:hunt)?[_-]?key|ключ\\s+сокровищ/i.test(blob)) return true;

      if (/item_treasurehunt_(?:energy|food|provision)/.test(blob) ||
          /берр|ягод|провизи|походн.*припас|travel.*provision|hiking.*suppl/i.test(blob)) return true;

      if (/pet.*(?:food|treat|snack)|(?:food|treat|snack).*pet/.test(blob) ||
          /вкусняшк.*питом|лакомств.*питом/i.test(blob)) return true;

      if (/pet.*skill|skill.*pet/.test(blob) ||
          /смена\\s+навыка\\s+питомца|замена\\s+навыка\\s+питомца/i.test(blob)) return true;

      if (/treasure[_-]?map|карта\\s+сокровищ/i.test(blob)) return true;
      return false;
    }
"""
rep(old_approved,new_approved,"expanded trader whitelist")

old_target_filter="""      const rows=traderElements()
        .filter(row=>!row.activated)
        .filter(row=>traderApprovedLot(row.lotId))
"""
new_target_filter="""      const rows=traderElements()
        .filter(row=>!row.activated)
        .filter(row=>traderApprovedRow(row))
"""
rep(old_target_filter,new_target_filter,"target uses row whitelist")

old_skipped="""          skipped:visible.filter(row=>!traderApprovedLot(row.lotId)).map(row=>row.lotId).slice(0,24)
"""
new_skipped="""          skipped:visible.filter(row=>!traderApprovedRow(row)).map(row=>row.lotId).slice(0,24)
"""
rep(old_skipped,new_skipped,"diagnostic row whitelist")

# Improve tiering from normalized catalog reward id as well.
old_tier="""    function traderValueTier(lotId) {
      const id=String(lotId||'').toLowerCase();
      if (/key_(?:common|uncommon|rare|epic|legendary)4coins/.test(id)) return 1250;
      if (/map/.test(id)) return 1200;
      if (/coins/.test(id)) return 1100;
      if (/food|berry|berries|energy/.test(id)) return 1000;
      if (/gold/.test(id)) return 900;
      if (/pet_skill|rod|sword/.test(id)) return 800;
      if (/fish_egg/.test(id)) return 700;
      return 600;
    }
"""
new_tier="""    function traderValueTier(lotId) {
      const catalog=traderCatalogRow(lotId);
      const id=[lotId,catalog?.rewardId,catalog?.name].map(value=>String(value||'').toLowerCase()).join(' ');
      if (/key_(?:common|uncommon|rare|epic|legendary)|treasure(?:hunt)?[_-]?key/.test(id)) return 1300;
      if (/map/.test(id)) return 1200;
      if (/coins/.test(id)) return 1100;
      if (/food|berry|berries|energy|provision|suppl/.test(id)) return 1050;
      if (/pet.*skill|skill.*pet/.test(id)) return 1025;
      if (/gold/.test(id)) return 900;
      if (/rod|sword/.test(id)) return 800;
      if (/fish_egg|pet_egg/.test(id)) return 0;
      return 600;
    }
"""
rep(old_tier,new_tier,"trader tier categories")

anchor="""    function traderTargetResolved(target) {
      if (!target?.element?.isConnected) return true;
      const current=traderElements().find(row=>row.element===target.element);
      return !current || !!current.activated || current.lotId!==target.lotId;
    }

"""
helper="""    function traderModalApproved(root) {
      if (!root) return false;
      const text=clean(root.innerText||root.textContent||'').toLowerCase();

      // Exact user-approved item families. This is intentionally narrower than
      // "any trader modal" so an already-open egg/HK-coin modal cannot be bought.
      return /вкусняшк.*питом|лакомств.*питом|pet\\s*(?:treat|snack)/i.test(text) ||
        /(?:необычн|обычн|редк|эпическ|легендарн).*ключ\\s+сокровищ|treasure\\s+key/i.test(text) ||
        /походн.*припас|провизия\\s+для\\s+путешеств|travel\\s+provision|hiking\\s+suppl/i.test(text) ||
        /смена\\s+навыка\\s+питомца|замена\\s+навыка\\s+питомца|pet\\s+skill\\s+(?:change|replace)/i.test(text);
    }

    function traderClickableTarget(element,root) {
      if (!element) return null;
      let node=element;
      for (let depth=0;node && depth<8;depth++,node=node.parentElement) {
        if (root && !root.contains(node) && node!==root) break;
        if (node.disabled || node.getAttribute?.('aria-disabled')==='true' || !visible(node)) continue;
        try {
          if (node.matches?.('button,[role="button"],a,[onclick]') || !!node.onclick || getComputedStyle(node).cursor==='pointer') {
            return node;
          }
        } catch (_) {}
        if (node===root) break;
      }
      return element;
    }

    function traderPurchaseButton(root,cost=null) {
      if (!root) return null;

      const shared=cost ? treasureActionButton(root,cost) : null;
      if (shared) return traderClickableTarget(shared,root);

      const rr=root.getBoundingClientRect?.();
      if (!rr) return null;
      const centerX=rr.left+rr.width/2;
      const rows=[...root.querySelectorAll('button,[role="button"],a,[onclick],div,span')]
        .filter(element=>element && !element.disabled && visible(element))
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const rect=element.getBoundingClientRect?.() || {left:0,top:0,width:0,height:0};
          const cx=rect.left+rect.width/2;
          let actionable=false;
          try {
            actionable=
              element.matches?.('button,[role="button"],a,[onclick]') ||
              !!element.onclick ||
              getComputedStyle(element).cursor==='pointer';
          } catch (_) {}

          let score=0;
          if (/^\\d{1,5}$/.test(text)) score+=260;
          else if (/\\b\\d{1,5}\\b/.test(text) && text.length<=18) score+=140;
          if (rect.top>=rr.top+rr.height*0.68) score+=180;
          if (Math.abs(cx-centerX)<=rr.width*0.25) score+=150;
          if (rect.width>=rr.width*0.28 && rect.width<=rr.width*0.82) score+=100;
          if (rect.height>=34 && rect.height<=110) score+=80;
          if (actionable) score+=100;
          if (/закрыть|close|×|✕|назад|back|понятно|ok|okay/i.test(text)) score-=700;

          return {element:traderClickableTarget(element,root),score,rect,actionable};
        })
        .filter(row=>row.element && row.score>=500)
        .sort((a,b)=>b.score-a.score || b.rect.width*b.rect.height-a.rect.width*a.rect.height);
      return rows[0]?.element || null;
    }

    function traderApprovedOpenModal() {
      const candidates=[...document.querySelectorAll('[role="dialog"],[aria-modal="true"],[class*="modal"],[class*="popup"],[class*="dialog"]')]
        .filter(visible)
        .map(element=>({element,rect:element.getBoundingClientRect?.()}))
        .filter(row=>row.rect && row.rect.width>=Math.min(260,window.innerWidth*0.55) && row.rect.height>=260)
        .filter(row=>traderModalApproved(row.element))
        .sort((a,b)=>a.rect.width*a.rect.height-b.rect.width*b.rect.height);
      return candidates[0]?.element || null;
    }

    async function traderResumeApprovedModal() {
      if (!traderAutoEnabled()) return false;
      const modal=traderApprovedOpenModal();
      if (!modal) return false;

      const before=traderSignature();
      const button=traderPurchaseButton(modal,null);
      if (!button) {
        recordDiagnostic('trader-approved-modal-stop',{
          revision:HK_TRADER_APPROVED_MODAL_REV,
          reason:'purchase-button-missing'
        });
        return false;
      }

      await traderHumanPause('confirm',{module:'trader',mode:'resume-approved-modal'});
      if (!traderAutoEnabled()) return false;

      const target=traderClickableTarget(button,modal) || button;
      let tapped=dispatchAutoMapTap(target,'trader-approved-modal-confirm');
      if (!tapped) {
        const rect=target.getBoundingClientRect?.();
        if (rect && rect.width>0 && rect.height>0) {
          tapped=dispatchBattleTapAt(
            rect.left+rect.width/2,
            rect.top+rect.height/2,
            'trader-approved-modal-confirm-center'
          );
        }
      }
      if (!tapped) return false;

      traderLastMutationAt=Date.now();
      const started=Date.now();
      while (Date.now()-started<3200) {
        if (!traderAutoEnabled()) return false;
        if (!traderApprovedOpenModal() || traderSignature()!==before) {
          traderSessionPurchases+=1;
          traderFailureStreak=0;
          traderRetryNotBefore=0;
          recordDiagnostic('trader-approved-modal-purchase',{
            revision:HK_TRADER_APPROVED_MODAL_REV,
            purchases:traderSessionPurchases
          });
          setTimeout(checkPuzzle,420);
          return true;
        }
        await new Promise(resolve=>setTimeout(resolve,90));
      }

      recordDiagnostic('trader-approved-modal-stop',{
        revision:HK_TRADER_APPROVED_MODAL_REV,
        reason:'no-ui-change'
      });
      return false;
    }

"""
if s.count(anchor)!=1:
    raise SystemExit("trader target resolved anchor missing")
s=s.replace(anchor,anchor+helper,1)

# Resume an already-open approved modal before looking for a card.
old_run_start="""    async function runTraderAuto() {
      if (!traderAutoEnabled() || traderAutoRunning || fishingAutoRunning || battleAutoRunning || chestAutoRunning || lightsAutoRunning) return false;
      if (Date.now()<traderRetryNotBefore) {
"""
new_run_start="""    async function runTraderAuto() {
      if (!traderAutoEnabled() || traderAutoRunning || fishingAutoRunning || battleAutoRunning || chestAutoRunning || lightsAutoRunning) return false;

      const approvedModal=traderApprovedOpenModal();
      if (approvedModal) {
        traderAutoRunning=true;
        const modalRunId=++traderAutoRunId;
        try {
          return await traderResumeApprovedModal();
        } finally {
          if (modalRunId===traderAutoRunId) traderAutoRunning=false;
          lastSignature='';
        }
      }

      if (Date.now()<traderRetryNotBefore) {
"""
rep(old_run_start,new_run_start,"resume open approved trader modal")

old_action="""            const button=treasureActionButton(modal,target.cost.primary);
            if (button) return button;
"""
new_action="""            const button=traderPurchaseButton(modal,target.cost.primary);
            if (button) return button;
"""
rep(old_action,new_action,"trader purchase selector")

old_click="""        if (!action || !dispatchAutoMapTap(action,'trader-confirm-'+target.lotId)) {
          try { target.element.dataset.hkTraderSkip='1'; } catch (_) {}
          return traderBackoff('action-missing',{lotId:target.lotId,cost:target.cost.parts,startedAt});
        }
"""
new_click="""        let actionTapped=false;
        if (action) {
          const clickTarget=traderClickableTarget(action,modal) || action;
          actionTapped=dispatchAutoMapTap(clickTarget,'trader-confirm-'+target.lotId);
          if (!actionTapped) {
            const rect=clickTarget.getBoundingClientRect?.();
            if (rect && rect.width>0 && rect.height>0) {
              actionTapped=dispatchBattleTapAt(
                rect.left+rect.width/2,
                rect.top+rect.height/2,
                'trader-confirm-center-'+target.lotId
              );
            }
          }
        }
        if (!actionTapped) {
          try { target.element.dataset.hkTraderSkip='1'; } catch (_) {}
          return traderBackoff('action-missing',{lotId:target.lotId,cost:target.cost.parts,startedAt});
        }
"""
rep(old_click,new_click,"click real trader purchase target")

rep("      treasuryVisualExitRevision:HK_TREASURY_VISUAL_EXIT_REV,\n      start,",
    "      treasuryVisualExitRevision:HK_TREASURY_VISUAL_EXIT_REV,\n      traderApprovedModalRevision:HK_TRADER_APPROVED_MODAL_REV,\n      start,",
    "export trader modal revision")

for marker in [
    "// @version      1.18.41",
    "const BUILD_VERSION = '1.18.41';",
    "trader-approved-modal-buy-20260927-r1",
    "function traderApprovedRow(row)",
    "function traderModalApproved(root)",
    "function traderClickableTarget(element,root)",
    "function traderPurchaseButton(root,cost=null)",
    "function traderApprovedOpenModal()",
    "async function traderResumeApprovedModal()",
    "Вкусняшк",
    "Походн.*припас",
    "Смена",
    "fish_egg|pet_egg",
    "trader-approved-modal-confirm",
    "trader-confirm-center-",
    "treasury-visual-exit-20260927-r2",
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("TRADER_APPROVED_MODAL_BUY_1_18_41=PASS")
