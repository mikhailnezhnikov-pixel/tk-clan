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

rep("// @version      1.18.91",
    "// @version      1.18.92\n// @release-note Карта сокровищ: восстановление зависаний по полевым отчётам — бой дожимает открытую карточку бойца, выход из Лабиринта/Сражения подтверждается device-neutral с retry, выкуп найденного ключа подтверждается по фактической смене модалки, карта сама прокручивает активную ячейку в видимую область перед нажатием.",
    "version")
rep("const BUILD_VERSION = '1.18.91';",
    "const BUILD_VERSION = '1.18.92';",
    "build")

rev_anchor="  const HK_MAP_DOMINANCE_REV='treasure-map-dominates-stale-minigame-20260929-r1';"
rep(rev_anchor,
    rev_anchor+"\n  const HK_MAP_TARGET_SCROLL_REV='treasure-map-target-scroll-20260929-r1';\n  const HK_EXIT_CONFIRM_RETRY_REV='treasure-exit-confirm-retry-20260929-r1';\n  const HK_BATTLE_MODAL_ACTION_RECOVERY_REV='battle-modal-action-recovery-20260929-r1';\n  const HK_KEY_PURCHASE_ACTIVATION_REV='treasure-key-purchase-activation-20260929-r1';",
    "revisions")

# ---------------------------------------------------------------------------
# Battle: if a fighter card is already open, prefer the action button inside
# that exact foreground modal. This avoids waiting forever on generic DOM
# scoring while AutoMap only shows "мини-игра".
# ---------------------------------------------------------------------------
battle_anchor="    function battleActionButton(expectedCost) {"
battle_helper=r'''    function battleEnemyModalActionButton(expectedCost) {
      const costText=String(expectedCost ?? '');
      if (!costText || !battleScreenVisiblyCurrent()) return null;
      const exactCost=new RegExp('(?:^|\\s)'+costText+'(?:\\s|$)');

      const roots=[...document.querySelectorAll(
        '[role="dialog"],[aria-modal="true"],[class*="modal"],[class*="popup"],[class*="dialog"],div'
      )]
        .filter(visible)
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const rect=element.getBoundingClientRect?.() || {left:0,top:0,width:0,height:0};
          return {element,text,rect,area:rect.width*rect.height};
        })
        .filter(row=>/МОЖНО\s+ОТЫСКАТЬ|CAN\s+BE\s+FOUND/i.test(row.text))
        .filter(row=>row.rect.width>=Math.min(260,window.innerWidth*0.40) && row.rect.height>=220)
        .filter(row=>row.rect.width<=window.innerWidth*0.99 && row.rect.height<=window.innerHeight*0.98)
        .sort((a,b)=>a.area-b.area);

      const root=roots[0]?.element || null;
      if (!root) return null;
      const rr=root.getBoundingClientRect?.();
      if (!rr) return null;

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
          const cx=rect.left+rect.width/2;
          let score=0;
          if (text===costText) score+=520;
          else if (exactCost.test(text) && text.length<=16) score+=260;
          if (rect.top>=rr.top+rr.height*0.60) score+=220;
          if (Math.abs(cx-(rr.left+rr.width/2))<=rr.width*0.32) score+=150;
          if (rect.width>=rr.width*0.28 && rect.width<=rr.width*0.90) score+=110;
          if (rect.height>=34 && rect.height<=150) score+=90;
          if (actionable) score+=120;
          if (/закрыть|close|×|✕|назад|back|понятно|got it|understood/i.test(text)) score-=900;
          return {element,score,rect,text};
        })
        .filter(row=>row.score>=650)
        .sort((a,b)=>b.score-a.score || b.rect.width*b.rect.height-a.rect.width*a.rect.height);

      const best=rows[0] || null;
      if (best) {
        recordDiagnostic('battle-modal-action-recovered',{
          revision:HK_BATTLE_MODAL_ACTION_RECOVERY_REV,
          expectedCost:Number(expectedCost),
          text:best.text.slice(0,80)
        });
      }
      return best?.element || null;
    }

'''
if s.count(battle_anchor)!=1:
    raise SystemExit("battle action anchor missing")
s=s.replace(battle_anchor,battle_helper+battle_anchor,1)

rep("""    function battleActionButton(expectedCost) {
      const costText=String(expectedCost ?? '');
""",
"""    function battleActionButton(expectedCost) {
      const modalAction=battleEnemyModalActionButton(expectedCost);
      if (modalAction) return modalAction;
      const costText=String(expectedCost ?? '');
""","battle direct modal action")

# ---------------------------------------------------------------------------
# Found treasure key: a raw .click() can leave the purchase modal frozen.
# Treat the click as committed only after the receipt, modal replacement,
# disappearance or another authoritative UI-state change is observed.
# ---------------------------------------------------------------------------
old_key=r'''      if (!dispatchAutoMapTap(target.element,'treasure-key-buy-'+String(cost??'unknown'))) return false;

      const started=Date.now();
'''
new_key=r'''      const purchaseRoot=root;
      const purchaseAccepted=()=> {
        const current=autoMapTreasureKeyModalRoot();
        if (!current || current!==purchaseRoot) return true;
        if (autoMapTreasureKeyAcknowledgeButton(current)) return true;
        return autoMapStateFingerprint()!==before;
      };

      let purchaseSent=false;
      try {
        purchaseSent=await deviceNeutralActivate(
          target.element,
          'treasure-key-buy-'+String(cost??'unknown'),
          purchaseAccepted,
          1800
        );
      } catch (_) {}

      if (!purchaseSent && target.element?.isConnected) {
        const tr=target.element.getBoundingClientRect?.();
        if (tr && tr.width>0 && tr.height>0) {
          const sent=dispatchMinigameOverlaySafeTapAt(
            tr.left+tr.width/2,
            tr.top+tr.height/2,
            'treasure-key-buy-center-'+String(cost??'unknown')
          );
          if (sent) {
            try {
              purchaseSent=await waitDeviceNeutralCondition(purchaseAccepted,1800,70);
            } catch (_) {}
          }
        }
      }

      if (!purchaseSent) {
        recordDiagnostic('treasure-key-purchase-activation-failed',{
          revision:HK_KEY_PURCHASE_ACTIVATION_REV,
          cost
        });
        autoMapRetryNotBefore=Date.now()+650;
        setTimeout(()=>void runAutoMapTick('treasure-key-purchase-activation-retry'),720);
        return false;
      }

      const started=Date.now();
'''
rep(old_key,new_key,"key purchase activation")

# ---------------------------------------------------------------------------
# Map: before tapping an active route cell, bring it into the viewport and
# prove the center belongs to that card while ignoring HK floating controls.
# ---------------------------------------------------------------------------
map_tap_anchor="    async function autoMapTapAndConfirm(element,label,costHint=null) {"
map_helper=r'''    async function autoMapPrepareMapTarget(element,label='map-target') {
      if (!element || !element.isConnected) return false;
      try {
        element.scrollIntoView({block:'center',inline:'center',behavior:'auto'});
      } catch (_) {
        try { element.scrollIntoView(); } catch (_) {}
      }

      await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
      await new Promise(resolve=>setTimeout(resolve,100));

      if (!element.isConnected || !visible(element)) return false;
      const rect=element.getBoundingClientRect?.();
      if (!rect || rect.width<=0 || rect.height<=0) return false;

      const x=Math.max(1,Math.min(window.innerWidth-1,rect.left+rect.width/2));
      const y=Math.max(1,Math.min(window.innerHeight-1,rect.top+rect.height/2));
      const leaf=battleElementFromPointIgnoringOverlays(x,y,element);
      const ready=!!leaf && (leaf===element || element.contains(leaf) || leaf.contains(element));

      recordDiagnostic('treasure-map-target-prepared',{
        revision:HK_MAP_TARGET_SCROLL_REV,
        label:String(label||''),
        ready,
        x:Math.round(x),
        y:Math.round(y)
      });
      return ready;
    }

'''
if s.count(map_tap_anchor)!=1:
    raise SystemExit("map tap anchor missing")
s=s.replace(map_tap_anchor,map_helper+map_tap_anchor,1)

old_map_dispatch=r'''      if (!dispatchAutoMapTap(element,'auto-map-'+label)) {
        autoMapStatus('клик не прошёл',{label});
        return false;
      }
'''
new_map_dispatch=r'''      let firstTap=false;
      if (/^map-/.test(String(label||''))) {
        const ready=await autoMapPrepareMapTarget(element,label);
        if (ready) {
          const er=element.getBoundingClientRect?.();
          if (er && er.width>0 && er.height>0) {
            firstTap=dispatchMinigameOverlaySafeTapAt(
              er.left+er.width/2,
              er.top+er.height/2,
              'auto-map-visible-'+label
            );
          }
        }
      } else {
        firstTap=dispatchAutoMapTap(element,'auto-map-'+label);
      }

      if (!firstTap) {
        autoMapStatus('клик не прошёл',{label});
        if (/^map-/.test(String(label||''))) {
          autoMapRetryNotBefore=Date.now()+420;
          setTimeout(()=>void runAutoMapTick('map-target-tap-retry'),520);
        }
        return false;
      }
'''
rep(old_map_dispatch,new_map_dispatch,"map target visible tap")

# ---------------------------------------------------------------------------
# Exit confirmations (Labyrinth/Battle/Treasury/etc): the modal action is not
# considered clicked until its modal/state actually changes. One coordinate
# retry is allowed under the HK overlay before yielding to the next tick.
# ---------------------------------------------------------------------------
old_confirm=r'''      await minigameHumanPause('confirm',{module:'auto-map',label});
      if (runId!==autoMapRunId || !autoMapEnabled()) return false;
      autoMapLastActionAt=Date.now();
      if (!dispatchAutoMapTap(action,'auto-map-confirm-'+label)) {
        autoMapRetryNotBefore=Date.now()+1400;
        return false;
      }
      autoMapTxnSet('ACTION_CONFIRMED',{label:String(label||''),lotId:autoMapCurrentLot});
'''
new_confirm=r'''      await minigameHumanPause('confirm',{module:'auto-map',label});
      if (runId!==autoMapRunId || !autoMapEnabled()) return false;
      autoMapLastActionAt=Date.now();

      let confirmationSent=false;
      if (/(?:leave|exit)/i.test(String(label||''))) {
        const confirmationRoot=modal;
        const accepted=()=> {
          const current=treasureModalRoot(null);
          return !current || current!==confirmationRoot || autoMapStateFingerprint()!==before;
        };
        try {
          confirmationSent=await deviceNeutralActivate(
            action,
            'auto-map-confirm-'+label,
            accepted,
            1700
          );
        } catch (_) {}
        if (!confirmationSent && action.isConnected) {
          const ar=action.getBoundingClientRect?.();
          if (ar && ar.width>0 && ar.height>0) {
            const sent=dispatchMinigameOverlaySafeTapAt(
              ar.left+ar.width/2,
              ar.top+ar.height/2,
              'auto-map-confirm-center-'+label
            );
            if (sent) {
              try {
                confirmationSent=await waitDeviceNeutralCondition(accepted,1500,70);
              } catch (_) {}
            }
          }
        }
        recordDiagnostic('treasure-exit-confirm-activation',{
          revision:HK_EXIT_CONFIRM_RETRY_REV,
          label:String(label||''),
          success:!!confirmationSent
        });
      } else {
        confirmationSent=dispatchAutoMapTap(action,'auto-map-confirm-'+label);
      }

      if (!confirmationSent) {
        autoMapRetryNotBefore=Date.now()+650;
        if (/(?:leave|exit)/i.test(String(label||''))) {
          setTimeout(()=>void runAutoMapTick('exit-confirm-retry'),740);
        }
        return false;
      }
      autoMapTxnSet('ACTION_CONFIRMED',{label:String(label||''),lotId:autoMapCurrentLot});
'''
rep(old_confirm,new_confirm,"exit device-neutral confirm")

# The pre-existing open leave modal recovery uses the same robust activation,
# so an earlier failed exit does not remain forever on "подтверждаю выход 10".
old_leave=r'''      autoMapLastActionAt=Date.now();
      if (!dispatchAutoMapTap(button,'leave-modal-confirm-10-'+source)) return false;

      const started=Date.now();
'''
new_leave=r'''      autoMapLastActionAt=Date.now();
      const leaveAccepted=()=> {
        const current=autoMapLeaveModalRoot();
        return !current || current!==modal || autoMapStateFingerprint()!==before;
      };

      let leaveConfirmed=false;
      try {
        leaveConfirmed=await deviceNeutralActivate(
          button,
          'leave-modal-confirm-10-'+source,
          leaveAccepted,
          1700
        );
      } catch (_) {}

      if (!leaveConfirmed && button.isConnected) {
        const br=button.getBoundingClientRect?.();
        if (br && br.width>0 && br.height>0) {
          const sent=dispatchMinigameOverlaySafeTapAt(
            br.left+br.width/2,
            br.top+br.height/2,
            'leave-modal-confirm-10-center-'+source
          );
          if (sent) {
            try { leaveConfirmed=await waitDeviceNeutralCondition(leaveAccepted,1500,70); }
            catch (_) {}
          }
        }
      }

      recordDiagnostic('leave-modal-confirm-activation',{
        revision:HK_EXIT_CONFIRM_RETRY_REV,
        source,
        success:!!leaveConfirmed
      });

      if (!leaveConfirmed && autoMapLeaveModalRoot()) {
        autoMapRetryNotBefore=Date.now()+480;
        setTimeout(()=>void runAutoMapTick('leave-modal-confirm-retry'),560);
        return false;
      }

      const started=Date.now();
'''
rep(old_leave,new_leave,"open leave modal retry")

# Export revisions.
export_anchor="      mapDominanceRevision:HK_MAP_DOMINANCE_REV,"
rep(export_anchor,
    export_anchor+"\n      mapTargetScrollRevision:HK_MAP_TARGET_SCROLL_REV,\n      exitConfirmRetryRevision:HK_EXIT_CONFIRM_RETRY_REV,\n      battleModalActionRecoveryRevision:HK_BATTLE_MODAL_ACTION_RECOVERY_REV,\n      keyPurchaseActivationRevision:HK_KEY_PURCHASE_ACTIVATION_REV,",
    "revision exports")

for marker in [
    "// @version      1.18.92",
    "treasure-map-target-scroll-20260929-r1",
    "treasure-exit-confirm-retry-20260929-r1",
    "battle-modal-action-recovery-20260929-r1",
    "treasure-key-purchase-activation-20260929-r1",
    "function battleEnemyModalActionButton(expectedCost)",
    "function autoMapPrepareMapTarget(element,label='map-target')",
    "treasure-key-purchase-activation-retry",
    "exit-confirm-retry",
    "battle-context-foreground-20260929-r1",
    "treasury-corridor-ack-20260929-r1",
    "automation-toggle-trusted-input-20260929-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

p.write_text(s,encoding="utf-8")
print("TREASURE_RECOVERY_1_18_92=PASS")
