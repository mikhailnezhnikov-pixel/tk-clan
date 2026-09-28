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
    "// @version      1.18.75",
    "// @version      1.18.76\n"
    "// @release-note Тайный торговец: «Золотые монеты» полностью исключены из автопокупки. Лоты verse_gold4coins / verse_gold4food больше не выбираются и не подтверждаются; если такое окно уже открыто, автомат закрывает его и продолжает с разрешёнными товарами.",
    "version"
)
rep("const BUILD_VERSION = '1.18.75';","const BUILD_VERSION = '1.18.76';","build")

anchor="  const HK_FISHING_MODAL_BUDGET_REV='fishing-modal-budget-ownership-20260928-r1';"
rep(
    anchor,
    anchor+"\n  const HK_TRADER_GOLD_SKIP_REV='trader-gold-currency-skip-20260928-r1';",
    "trader gold skip revision"
)

approved_anchor="""    function traderApprovedLot(lotId) {
"""
helper="""    function traderForbiddenGoldLot(lotId) {
      const id=String(lotId||'').toLowerCase();
      if (!id) return false;

      // These trader offers convert Treasure resources into the regular
      // account gold currency (cur_gold). They are intentionally never bought.
      return /verse_gold4(?:coins|food)/.test(id) ||
        /(?:^|_)gold4(?:coins|food)(?:_|$)/.test(id);
    }

"""
if s.count(approved_anchor)!=1:
    raise SystemExit("traderApprovedLot anchor missing")
s=s.replace(approved_anchor,helper+approved_anchor,1)

rep(
"""    function traderApprovedLot(lotId) {
      const id=String(lotId||'').toLowerCase();
      if (!id) return false;

      // Never buy pet/fish eggs automatically.
""",
"""    function traderApprovedLot(lotId) {
      const id=String(lotId||'').toLowerCase();
      if (!id) return false;

      // Never buy regular account gold with Treasure resources.
      if (traderForbiddenGoldLot(id)) return false;

      // Never buy pet/fish eggs automatically.
""",
"gold blacklist in approved lot"
)

old_row="""      const blob=[row.lotId,rewardId,name,text].join(' ');

      // Keep the historical egg exclusion even when another field contains
      // generic words like pet/food.
      if (/fish_egg|pet_egg|egg_/.test(blob)) return false;
"""
new_row="""      const blob=[row.lotId,rewardId,name,text].join(' ');

      // Explicit deny-list: regular account gold / «Золотые монеты».
      // The exact live lot families are verse_gold4coins and verse_gold4food.
      if (traderForbiddenGoldLot(row.lotId) ||
          /(?:^|[_\s])cur_gold(?:[_\s]|$)|золотые\s+монеты|gold(?:en)?\s+coins/i.test(blob)) return false;

      // Keep the historical egg exclusion even when another field contains
      // generic words like pet/food.
      if (/fish_egg|pet_egg|egg_/.test(blob)) return false;
"""
rep(old_row,new_row,"gold blacklist in approved row")

old_modal="""    function traderModalApproved(root) {
      if (!root) return false;
      const text=clean(root.innerText||root.textContent||'').toLowerCase();

      // Exact user-approved item families. This is intentionally narrower than
"""
new_modal="""    function traderModalApproved(root) {
      if (!root) return false;
      const text=clean(root.innerText||root.textContent||'').toLowerCase();

      // Never confirm the regular gold-currency offer even if a modal was
      // opened manually or survived from an older script run.
      if (/золотые\s+монеты|gold(?:en)?\s+coins|cur_gold/i.test(text)) return false;

      // Exact user-approved item families. This is intentionally narrower than
"""
rep(old_modal,new_modal,"gold blacklist in modal approval")

clickable_anchor="""    function traderPurchaseButton(root,cost=null) {
"""
close_helper="""    function traderForbiddenGoldModalRoot() {
      const candidates=[...document.querySelectorAll('[role="dialog"],[aria-modal="true"],[class*="modal"],[class*="popup"],[class*="dialog"]')]
        .filter(visible)
        .map(element=>({element,rect:element.getBoundingClientRect?.()}))
        .filter(row=>row.rect && row.rect.width>=Math.min(240,window.innerWidth*0.46) && row.rect.height>=180)
        .filter(row=>/золотые\s+монеты|gold(?:en)?\s+coins|cur_gold/i.test(clean(row.element.innerText||row.element.textContent||'')))
        .sort((a,b)=>a.rect.width*a.rect.height-b.rect.width*b.rect.height);
      return candidates[0]?.element || null;
    }

    function traderCloseForbiddenGoldModal(root=traderForbiddenGoldModalRoot()) {
      if (!root) return false;
      const rr=root.getBoundingClientRect?.();
      const rows=[...root.querySelectorAll('button,[role="button"],a,[onclick],div,span')]
        .filter(element=>element && !element.disabled && visible(element))
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const aria=clean(element.getAttribute?.('aria-label')||'').trim();
          const rect=element.getBoundingClientRect?.() || {left:0,top:0,width:0,height:0};
          let score=0;
          if (/^(?:×|✕|Закрыть|Close|Назад|Back)$/i.test(text)) score+=500;
          if (/close|закрыть|back|назад/i.test(aria)) score+=450;
          if (rr && rect.top<=rr.top+rr.height*0.24) score+=100;
          if (rr && rect.left>=rr.left+rr.width*0.68) score+=100;
          if (rect.width>0 && rect.width<=100 && rect.height>0 && rect.height<=100) score+=80;
          return {element:traderClickableTarget(element,root)||element,score,rect};
        })
        .filter(row=>row.score>=450)
        .sort((a,b)=>b.score-a.score || a.rect.width*a.rect.height-b.rect.width*b.rect.height);
      const close=rows[0]?.element || null;
      if (!close) return false;
      const ok=dispatchAutoMapTap(close,'trader-forbidden-gold-close');
      recordDiagnostic('trader-forbidden-gold-modal',{
        revision:HK_TRADER_GOLD_SKIP_REV,
        action:ok?'closed':'close-failed'
      });
      return !!ok;
    }

"""
if s.count(clickable_anchor)!=1:
    raise SystemExit("traderPurchaseButton anchor missing")
s=s.replace(clickable_anchor,close_helper+clickable_anchor,1)

rep(
"""    function traderRoomComplete() {
      const signature=getSignature();
      if (!signature.startsWith('TRADER|')) return false;
      if (traderApprovedOpenModal()) return false;
      return !traderTarget();
    }
""",
"""    function traderRoomComplete() {
      const signature=getSignature();
      if (!signature.startsWith('TRADER|')) return false;
      if (traderApprovedOpenModal()) return false;
      if (traderForbiddenGoldModalRoot()) return false;
      return !traderTarget();
    }
""",
"forbidden modal blocks room completion"
)

run_anchor="""    async function runTraderAuto() {
      if (!traderAutoEnabled() || traderAutoRunning || fishingAutoRunning || battleAutoRunning || chestAutoRunning || lightsAutoRunning) return false;

      const receiptModal=traderReceiptModalRoot();
"""
run_new="""    async function runTraderAuto() {
      if (!traderAutoEnabled() || traderAutoRunning || fishingAutoRunning || battleAutoRunning || chestAutoRunning || lightsAutoRunning) return false;

      const forbiddenGoldModal=traderForbiddenGoldModalRoot();
      if (forbiddenGoldModal) {
        const closed=traderCloseForbiddenGoldModal(forbiddenGoldModal);
        lastSignature='';
        recordDiagnostic('trader-forbidden-gold-skip',{
          revision:HK_TRADER_GOLD_SKIP_REV,
          closed:!!closed
        });
        setTimeout(checkPuzzle,closed?120:300);
        return false;
      }

      const receiptModal=traderReceiptModalRoot();
"""
rep(run_anchor,run_new,"close forbidden gold modal before purchase")

export_anchor="      fishingModalBudgetRevision:HK_FISHING_MODAL_BUDGET_REV,"
if s.count(export_anchor)!=1:
    raise SystemExit("fishing modal export anchor missing")
s=s.replace(
    export_anchor,
    export_anchor+"\n      traderGoldSkipRevision:HK_TRADER_GOLD_SKIP_REV,",
    1
)

for marker in [
    "// @version      1.18.76",
    "const BUILD_VERSION = '1.18.76';",
    "trader-gold-currency-skip-20260928-r1",
    "function traderForbiddenGoldLot(lotId)",
    "verse_gold4(?:coins|food)",
    "function traderForbiddenGoldModalRoot()",
    "function traderCloseForbiddenGoldModal",
    "trader-forbidden-gold-close",
    "trader-forbidden-gold-skip",
    "traderGoldSkipRevision:HK_TRADER_GOLD_SKIP_REV",
    "purchase-confirm-fast-global-20260928-r1",
    "trader-receipt-ack-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

p.write_text(s,encoding="utf-8")
print("TRADER_GOLD_SKIP_1_18_76=PASS")
