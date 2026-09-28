from pathlib import Path
import sys,re

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count:
        raise SystemExit(f"{label}: expected {count} got {n}")
    s=s.replace(old,new,count)

rep(
    "// @version      1.18.70",
    "// @version      1.18.71\n"
    "// @release-note Тайный торговец: после успешной покупки окно получения награды с кнопкой «Понятно» теперь является обязательным этапом. Автомат находит реальный кликабельный контейнер кнопки, подтверждает награду с touch/click fallback и только после закрытия окна продолжает покупки или выходит из комнаты.",
    "version"
)
rep("const BUILD_VERSION = '1.18.70';","const BUILD_VERSION = '1.18.71';","build")

anchor="  const HK_TRADER_APPROVED_MODAL_REV = 'trader-approved-modal-buy-20260927-r1';"
rep(
    anchor,
    anchor+"\n  const HK_TRADER_RECEIPT_ACK_REV = 'trader-receipt-ack-20260928-r1';",
    "trader receipt revision"
)

helper_anchor="    async function traderResumeApprovedModal() {"
if s.count(helper_anchor)!=1:
    raise SystemExit("traderResumeApprovedModal anchor missing")

helper=r'''    function traderReceiptAcknowledgeButton(root) {
      if (!root) return null;
      const exact=/^(?:Понятно|Got it|Understood|OK|Okay)$/i;
      const rr=root.getBoundingClientRect?.();
      const rows=[...root.querySelectorAll('button,[role="button"],a,[onclick],div,span')]
        .filter(element=>element && !element.disabled && visible(element))
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const rect=element.getBoundingClientRect?.() || {left:0,top:0,width:0,height:0};
          let actionable=false;
          try {
            actionable=
              element.matches?.('button,[role="button"],a,[onclick]') ||
              !!element.onclick ||
              getComputedStyle(element).cursor==='pointer';
          } catch (_) {}
          let score=0;
          if (exact.test(text)) score+=600;
          if (actionable) score+=220;
          if (rr && rect.top>=rr.top+rr.height*0.55) score+=140;
          if (rect.width>=80 && rect.height>=32) score+=80;
          return {
            element:traderClickableTarget(element,root) || element,
            text,
            rect,
            score
          };
        })
        .filter(row=>exact.test(row.text) && row.rect.width>0 && row.rect.height>0)
        .sort((a,b)=>b.score-a.score || a.rect.width*a.rect.height-b.rect.width*b.rect.height);
      return rows[0]?.element || null;
    }

    function traderReceiptModalRoot() {
      const candidates=[...document.querySelectorAll('[role="dialog"],[aria-modal="true"],[class*="modal"],[class*="popup"],[class*="dialog"]')]
        .filter(visible)
        .map(element=>({
          element,
          rect:element.getBoundingClientRect?.()
        }))
        .filter(row=>row.rect && row.rect.width>=Math.min(240,window.innerWidth*0.46) && row.rect.height>=180)
        .filter(row=>!!traderReceiptAcknowledgeButton(row.element))
        .sort((a,b)=>a.rect.width*a.rect.height-b.rect.width*b.rect.height);
      return candidates[0]?.element || null;
    }

    async function traderAcknowledgeReceipt(source='trader-purchase') {
      if (!traderAutoEnabled()) return false;
      const root=traderReceiptModalRoot();
      if (!root) return false;
      const ack=traderReceiptAcknowledgeButton(root);
      if (!ack) return false;

      await traderHumanPause('reward',{module:'trader',mode:'receipt-ack',source});
      if (!traderAutoEnabled()) return false;

      const accepted=()=> {
        const current=traderReceiptModalRoot();
        return !current || current!==root || !traderReceiptAcknowledgeButton(current);
      };

      const clickTarget=traderClickableTarget(ack,root) || ack;
      let ok=false;
      try {
        ok=await deviceNeutralActivate(
          clickTarget,
          'trader-receipt-ack-'+source,
          accepted,
          1500
        );
      } catch (_) {}

      if (!ok && clickTarget?.isConnected) {
        const sent=dispatchAutoMapTap(clickTarget,'trader-receipt-ack-fallback-'+source);
        if (sent) {
          try { ok=await waitDeviceNeutralCondition(accepted,1600,70); } catch (_) {}
        }
      }

      if (!ok && clickTarget?.isConnected) {
        const rect=clickTarget.getBoundingClientRect?.();
        if (rect && rect.width>0 && rect.height>0) {
          const sent=dispatchBattleTapAt(
            rect.left+rect.width/2,
            rect.top+rect.height/2,
            'trader-receipt-ack-center-'+source
          );
          if (sent) {
            try { ok=await waitDeviceNeutralCondition(accepted,1600,70); } catch (_) {}
          }
        }
      }

      recordDiagnostic('trader-receipt-acknowledged',{
        revision:HK_TRADER_RECEIPT_ACK_REV,
        source,
        success:!!ok
      });

      if (ok) {
        traderFailureStreak=0;
        traderRetryNotBefore=0;
        lastSignature='';
        await new Promise(resolve=>setTimeout(resolve,120));
      }
      return !!ok;
    }

'''
s=s.replace(helper_anchor,helper+helper_anchor,1)

run_anchor="""    async function runTraderAuto() {
      if (!traderAutoEnabled() || traderAutoRunning || fishingAutoRunning || battleAutoRunning || chestAutoRunning || lightsAutoRunning) return false;
"""
if s.count(run_anchor)!=1:
    raise SystemExit("runTraderAuto anchor missing")
run_new=run_anchor+"""
      const receiptModal=traderReceiptModalRoot();
      if (receiptModal) {
        traderAutoRunning=true;
        const receiptRunId=++traderAutoRunId;
        try {
          return await traderAcknowledgeReceipt('resume');
        } finally {
          if (receiptRunId===traderAutoRunId) traderAutoRunning=false;
          lastSignature='';
          setTimeout(checkPuzzle,120);
        }
      }

"""
s=s.replace(run_anchor,run_new,1)

# The normal trader path already calls the generic reward dismiss helper.
# Add the trader-specific acknowledgement immediately afterwards because the
# game's receipt button can be a clickable div rather than a button/a element.
run_start=s.find("    async function runTraderAuto() {")
run_end=s.find("\n    function ",run_start+20)
if run_end<0:
    run_end=s.find("\n    async function ",run_start+20)
if run_end<0:
    raise SystemExit("runTraderAuto end not found")
run=s[run_start:run_end]
needle="const rewards=await dismissTreasureRewards(runId);"
if needle not in run:
    raise SystemExit("trader reward dismiss anchor missing")
run=run.replace(
    needle,
    needle+"\n        await traderAcknowledgeReceipt('post-purchase');",
    1
)
s=s[:run_start]+run+s[run_end:]

# Export the revision so diagnostics can prove the live core contains the fix.
export_anchor="      traderApprovedModalRevision:HK_TRADER_APPROVED_MODAL_REV,"
if s.count(export_anchor)!=1:
    raise SystemExit("trader export anchor missing")
s=s.replace(
    export_anchor,
    export_anchor+"\n      traderReceiptAckRevision:HK_TRADER_RECEIPT_ACK_REV,",
    1
)

for marker in [
    "// @version      1.18.71",
    "const BUILD_VERSION = '1.18.71';",
    "trader-receipt-ack-20260928-r1",
    "function traderReceiptAcknowledgeButton(root)",
    "function traderReceiptModalRoot()",
    "async function traderAcknowledgeReceipt(source='trader-purchase')",
    "traderAcknowledgeReceipt('resume')",
    "traderAcknowledgeReceipt('post-purchase')",
    "trader-receipt-ack-center-",
    "traderReceiptAckRevision:HK_TRADER_RECEIPT_ACK_REV",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

p.write_text(s,encoding="utf-8")
print("TRADER_RECEIPT_ACK_1_18_71=PASS")
