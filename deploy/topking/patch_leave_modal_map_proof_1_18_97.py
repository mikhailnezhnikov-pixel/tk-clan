from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count:
        raise SystemExit(f"{label}: expected {count}, got {n}")
    s=s.replace(old,new,count)

def between(start,end,new,label):
    global s
    a=s.find(start)
    if a<0: raise SystemExit(f"{label}: start anchor missing")
    b=s.find(end,a+len(start))
    if b<0: raise SystemExit(f"{label}: end anchor missing")
    s=s[:a]+new+s[b:]

rep("// @version      1.18.96",
    "// @version      1.18.97\n// @release-note Сражения: окно выхода распознаётся только как реальный передний диалог с отдельной кнопкой 10, а не по надписи «Покинуть локацию» на странице и цифрам в кошельке. Подтверждение выхода считается успешным только после реального возврата на карту. Ложные клики и преждевременный переход к следующей клетке заблокированы.",
    "version")
rep("const BUILD_VERSION = '1.18.96';",
    "const BUILD_VERSION = '1.18.97';",
    "build")

rev="  const HK_BATTLE_OPEN_MODAL_PRIORITY_REV='battle-open-modal-priority-20260930-r1';"
rep(rev,rev+"\n  const HK_LEAVE_MODAL_TRUTH_REV='leave-modal-foreground-truth-20261001-r1';\n  const HK_EXIT_MAP_PROOF_REV='exit-map-proof-20261001-r1';","revisions")

leave_start="    function autoMapLeaveModalRoot() {"
leave_end="    function autoMapPromoteActionTarget(element,root=null) {"
leave_block=r'''    function autoMapReturnMapConfirmed() {
      // The game may leave the underlying "Карта сокровищ" title mounted while
      // a room is open. Only its real foreground cards / journey control prove
      // that exit succeeded. A modal redraw or signature change never does.
      if (!treasureGuideScreenVisible()) return false;
      if (battleScreenVisiblyCurrent()) return false;
      if (autoMapMiniGameForeground()) return false;
      if (autoMapMapIsForeground()) return true;
      const journey=autoMapJourneyButton();
      return !!journey && autoMapElementIsForeground(journey);
    }

    function autoMapLeaveModalRoot() {
      const vw=Math.max(1,window.innerWidth);
      const vh=Math.max(1,window.innerHeight);
      const roots=[...document.querySelectorAll(
        '[role="dialog"],[aria-modal="true"],[class*="modal"],[class*="popup"],[class*="dialog"],div'
      )]
        .filter(visible)
        .map(element=>{
          const rect=element.getBoundingClientRect?.();
          if (!rect || rect.width<Math.min(240,vw*0.48) || rect.height<150 ||
              rect.width>vw*0.94 || rect.height>vh*0.90) return null;

          const cx=rect.left+rect.width/2;
          const cy=rect.top+rect.height/2;
          if (Math.abs(cx-vw/2)>vw*0.23 || Math.abs(cy-vh/2)>vh*0.25) return null;

          // In 1.18.96 the unrestricted div fallback could interpret the
          // battle screen plus "101K" resources as a leave confirmation.
          // A real confirmation has its own price action, not a substring 10
          // in the resource bar or a page-level Leave location button.
          const text=clean(element.innerText||element.textContent||'').trim();
          if (!/Покинуть локацию|Leave location|Exit location/i.test(text)) return null;

          const actionRows=[...element.querySelectorAll('button,[role="button"],a,[onclick],div,span')]
            .filter(child=>child && child!==element && !child.disabled && visible(child))
            .map(child=>{
              const value=clean(child.innerText||child.textContent||'').trim();
              const r=child.getBoundingClientRect?.()||{width:0,height:0,top:0,left:0};
              return {child,value,r};
            });
          const price=actionRows.some(row=>
            /^(?:10|10\s*(?:ягод(?:ы)?|berries|berry))$/i.test(row.value) &&
            row.r.top>=rect.top+rect.height*0.44 &&
            row.r.width>=rect.width*0.23 &&
            row.r.height>=28
          );
          if (!price) return null;

          const hasBack=actionRows.some(row=>/^(?:Назад|Back|Отмена|Cancel)$/i.test(row.value));
          const hasPrompt=/(?:Продолжить\?|Continue\?|Вы уверены|Are you sure)/i.test(text);
          const explicit=element.matches?.(
            '[role="dialog"],[aria-modal="true"],[class*="modal"],[class*="popup"],[class*="dialog"]'
          );
          if (!explicit && !hasPrompt && !hasBack) return null;

          const top=battleElementFromPointIgnoringOverlays(cx,cy,null);
          if (!top || (top!==element && !element.contains(top))) return null;

          return {element,rect,area:rect.width*rect.height,explicit:!!explicit};
        })
        .filter(Boolean)
        .sort((a,b)=>b.explicit-a.explicit || a.area-b.area);

      return roots[0]?.element || null;
    }

'''
between(leave_start,leave_end,leave_block,"real leave modal detection")

rep("      const leaveAccepted=()=> {\n        const current=autoMapLeaveModalRoot();\n        return !current || current!==modal || autoMapStateFingerprint()!==before;\n      };",
    "      const leaveAccepted=()=> {\n        const current=autoMapLeaveModalRoot();\n        return autoMapReturnMapConfirmed() || !current || current!==modal;\n      };",
    "leave activation acknowledgment")

rep("""        if (!autoMapLeaveModalRoot()) {
          if (treasureGuideScreenVisible() || autoMapStateFingerprint()!==before) {
            autoMapRetryNotBefore=0;
            autoMapCurrentLot='';
            lastSignature='';
            autoMapReturnNotBefore=Date.now()+300;
            recordDiagnostic('leave-modal-confirm-complete',{
              revision:HK_TREASURY_LEFT_PATH_REV,
              source,
              result:'closed'
            });
            setTimeout(()=>void runAutoMapTick('leave-modal-confirm-complete'),360);
            return true;
          }
        }""",
    """        if (autoMapReturnMapConfirmed()) {
          autoMapRetryNotBefore=0;
          autoMapCurrentLot='';
          lastSignature='';
          autoMapReturnNotBefore=Date.now()+300;
          recordDiagnostic('leave-modal-confirm-complete',{
            revision:HK_EXIT_MAP_PROOF_REV,
            source,
            result:'map-foreground-confirmed'
          });
          setTimeout(()=>void runAutoMapTick('leave-modal-confirm-complete'),360);
          return true;
        }""",
    "leave confirmed only by map")

rep("""      autoMapRetryNotBefore=Date.now()+800;
      setTimeout(()=>void runAutoMapTick('leave-modal-still-in-room'),900);
      return false;""",
    """      recordDiagnostic('leave-modal-return-not-confirmed',{
        revision:HK_EXIT_MAP_PROOF_REV,
        source,
        modalStillOpen:!!autoMapLeaveModalRoot(),
        battleTitle:battleScreenVisiblyCurrent()
      });
      autoMapStatus('выход → жду карту',{revision:HK_EXIT_MAP_PROOF_REV,source});
      autoMapRetryNotBefore=Date.now()+800;
      setTimeout(()=>void runAutoMapTick('leave-modal-still-in-room'),900);
      return false;""",
    "leave retry without false success")

rep("      const roomGone=()=>treasureGuideScreenVisible();",
    "      const roomGone=()=>autoMapReturnMapConfirmed();",
    "completed battle real map proof")

# Generic AutoMap exits share the same incorrect fingerprint-based early success.
# Opening the confirmation dialog is not proof that the room has been exited.
rep("""        if (autoMapStateFingerprint()!==before) {
          autoMapTxnSet('SERVER_UI_STATE_CHANGED',{label:String(label||''),lotId:autoMapCurrentLot,mode:'direct'});
          return true;
        }""",
    """        if (autoMapStateFingerprint()!==before) {
          if (/(?:leave|exit)/i.test(String(label||''))) {
            if (autoMapReturnMapConfirmed()) {
              autoMapTxnSet('SERVER_UI_STATE_CHANGED',{label:String(label||''),lotId:autoMapCurrentLot,mode:'map-confirmed'});
              return true;
            }
            // This may be the just-opened leave dialog; keep waiting for it.
          } else {
            autoMapTxnSet('SERVER_UI_STATE_CHANGED',{label:String(label||''),lotId:autoMapCurrentLot,mode:'direct'});
            return true;
          }
        }""",
    "generic exit early success")

rep("""        modal=treasureModalRoot(null);
        if (modal) {
          autoMapTxnSet('CARD_OPENED',{label:String(label||''),lotId:autoMapCurrentLot});
          break;
        }""",
    """        modal=/(?:leave|exit)/i.test(String(label||''))
          ? autoMapLeaveModalRoot()
          : treasureModalRoot(null);
        if (modal) {
          autoMapTxnSet('CARD_OPENED',{label:String(label||''),lotId:autoMapCurrentLot});
          break;
        }""",
    "generic exit real dialog")

rep("""        action=autoMapModalPrimaryButton(modal,costHint);
        if (!action) {
          const centered=treasureCenteredModalRoot();""",
    """        action=/(?:leave|exit)/i.test(String(label||''))
          ? autoMapLeaveConfirmButton(modal,10)
          : autoMapModalPrimaryButton(modal,costHint);
        if (!action && !/(?:leave|exit)/i.test(String(label||''))) {
          const centered=treasureCenteredModalRoot();""",
    "generic exit own confirm control")

rep("""        if (autoMapStateFingerprint()!==before) {
          autoMapTxnSet('SERVER_UI_STATE_CHANGED',{label:String(label||''),lotId:autoMapCurrentLot});
          await minigameHumanPause('settle',{module:'auto-map',label});
          return true;
        }""",
    """        if (
          (/(?:leave|exit)/i.test(String(label||'')) && autoMapReturnMapConfirmed()) ||
          (!/(?:leave|exit)/i.test(String(label||'')) && autoMapStateFingerprint()!==before)
        ) {
          autoMapTxnSet('SERVER_UI_STATE_CHANGED',{label:String(label||''),lotId:autoMapCurrentLot});
          await minigameHumanPause('settle',{module:'auto-map',label});
          return true;
        }""",
    "generic exit settle map proof")

export_anchor="      battleOpenModalPriorityRevision:HK_BATTLE_OPEN_MODAL_PRIORITY_REV,"
rep(export_anchor,
    export_anchor+"\n      leaveModalTruthRevision:HK_LEAVE_MODAL_TRUTH_REV,\n      exitMapProofRevision:HK_EXIT_MAP_PROOF_REV,",
    "debug exports")

p.write_text(s,encoding="utf-8")
print("PATCH_LEAVE_MODAL_MAP_PROOF_1_18_97=PASS")
