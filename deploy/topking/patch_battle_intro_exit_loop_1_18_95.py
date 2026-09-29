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

def replace_between(start,end,new,label):
    global s
    a=s.find(start)
    if a<0:
        raise SystemExit(f"{label}: start anchor missing")
    b=s.find(end,a+len(start))
    if b<0:
        raise SystemExit(f"{label}: end anchor missing")
    s=s[:a]+new+s[b:]

rep("// @version      1.18.94",
    "// @version      1.18.95\n// @release-note Сражение: стартовое окно «Сражение → Понятно» теперь определяется по самой модалке и боевому DOM, а не по заголовку страницы под затемнением; подтверждение проходит сквозь HK-оверлеи. После взятого сундука победителя введён отдельный цикл выхода: открыть «Покинуть локацию», подтвердить 10 и считать выход завершённым только после фактического возврата на карту; если окно закрылось, а бой остался, выход повторяется.",
    "version")
rep("const BUILD_VERSION = '1.18.94';",
    "const BUILD_VERSION = '1.18.95';",
    "build")

rev_anchor="  const HK_BATTLE_OPEN_MODAL_CONFIRM_REV='battle-open-modal-confirm-20260930-r1';"
rep(rev_anchor,
    rev_anchor+"\n  const HK_BATTLE_INTRO_OVERLAY_ACK_REV='battle-intro-overlay-ack-20260930-r1';\n  const HK_BATTLE_COMPLETE_EXIT_LOOP_REV='battle-complete-exit-loop-20260930-r1';",
    "new revisions")

intro_start="    function battleIntroModalRoot() {"
intro_end="    function battleIntroTransitionLocked() {"
intro_block=r'''    function battleIntroModalRoot() {
      const exactAck=/^(?:Понятно|Got it|Understood|OK|Okay)$/i;

      // The modal itself is authoritative. On mobile the centered battle modal
      // darkens the page-title bar, so requiring the underlying "Сражение"
      // heading to remain foreground made the exact intro shown by the game
      // impossible to acknowledge.
      const rawBattle=(()=>{
        try { return battleRawContextPresent() || getBattleBoard().some(Boolean); }
        catch (_) { return false; }
      })();

      const rows=[...document.querySelectorAll(
        '[role="dialog"],[aria-modal="true"],[class*="modal"],[class*="popup"],[class*="dialog"],div'
      )]
        .filter(visible)
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const ack=[...element.querySelectorAll('button,[role="button"],a,[onclick],div,span')]
            .find(child=>
              child &&
              !child.disabled &&
              exactAck.test(clean(child.innerText||child.textContent||'').trim()) &&
              visible(child)
            );
          const rect=element.getBoundingClientRect?.() || {left:0,top:0,width:0,height:0};
          const points=[
            [rect.left+rect.width*0.50,rect.top+rect.height*0.48],
            [rect.left+rect.width*0.50,rect.top+rect.height*0.78]
          ];
          const foreground=points.some(([x,y])=>{
            if (x<1 || x>window.innerWidth-1 || y<1 || y>window.innerHeight-1) return false;
            const top=battleElementFromPointIgnoringOverlays(x,y,null);
            return !!top && (top===element || element.contains(top));
          });
          return {
            element,
            text,
            ack,
            rect,
            foreground,
            ownTitle:battleIntroOwnTitle(element),
            area:rect.width*rect.height
          };
        })
        .filter(row=>row.ack && row.ownTitle)
        .filter(row=>!/Сундук победителя|Victory chest|Winner chest|Ключ сокровищ|Treasure key|Золотые монеты|Golden Coins|Gold Coins/i.test(row.text))
        .filter(row=>row.rect.width>=Math.min(220,window.innerWidth*0.30) && row.rect.height>=100)
        .filter(row=>row.rect.width<=window.innerWidth*0.99 && row.rect.height<=window.innerHeight*0.98)
        .filter(row=>row.foreground)
        .filter(row=>rawBattle || battleScreenVisiblyCurrent())
        .sort((a,b)=>a.area-b.area);

      const root=rows[0]?.element || null;
      if (root) {
        battleIntroGateUntil=Math.max(battleIntroGateUntil,Date.now()+5000);
        recordDiagnostic('battle-intro-modal-detected',{
          revision:HK_BATTLE_INTRO_OVERLAY_ACK_REV,
          rawBattle,
          visiblePageTitle:battleScreenVisiblyCurrent()
        });
      }
      return root;
    }

'''
replace_between(intro_start,intro_end,intro_block,"battle intro modal root")

ack_start="    async function runBattleIntroAcknowledge() {"
ack_end="    async function autoMapSkipBattleWithoutFight() {"
ack_block=r'''    async function runBattleIntroAcknowledge() {
      if ((!battleAutoEnabled() && !autoMapEnabled()) || battleAutoRunning) return false;
      if (autoMapEnabled() && !battleAutoEnabled()) setBattleAutoEnabled(true);
      const root=battleIntroModalRoot();
      const button=battleIntroAcknowledgeButton(root);
      if (!root || !button) return false;

      battleFinalRewardClaimed=false;
      battleFinalRewardClaimedAt=0;
      battleAutoRunning=true;
      const runId=++battleAutoRunId;
      try {
        recordDiagnostic('battle-intro-ack-start',{
          revision:HK_BATTLE_INTRO_OVERLAY_ACK_REV,
          hasModal:true
        });

        const accepted=()=>{
          const current=battleIntroModalRoot();
          return !current || current!==root || !battleIntroAcknowledgeButton(current);
        };

        let success=false;
        const br=button.getBoundingClientRect?.();
        if (br && br.width>0 && br.height>0) {
          const sent=dispatchMinigameOverlaySafeTapAt(
            br.left+br.width/2,
            br.top+br.height/2,
            'battle-intro-ack-overlay-safe'
          );
          if (sent) {
            try { success=await waitDeviceNeutralCondition(accepted,1700,70); }
            catch (_) {}
          }
        }

        if (!success && button.isConnected) {
          try {
            success=await deviceNeutralActivate(
              button,
              'battle-intro-ack-device-neutral',
              accepted,
              1700
            );
          } catch (_) {}
        }

        if (!success && root.isConnected) {
          const rr=root.getBoundingClientRect?.();
          if (rr && rr.width>0 && rr.height>0) {
            for (const fraction of [0.84,0.88,0.80]) {
              if (runId!==battleAutoRunId || !battleAutoEnabled()) return false;
              const sent=dispatchMinigameOverlaySafeTapAt(
                rr.left+rr.width/2,
                rr.top+rr.height*fraction,
                'battle-intro-ack-fallback-'+String(fraction)
              );
              if (!sent) continue;
              try { success=await waitDeviceNeutralCondition(accepted,900,70); }
              catch (_) {}
              if (success) break;
            }
          }
        }

        if (success) {
          battleIntroGateUntil=Date.now()+1800;
          lastSignature='';
          recordDiagnostic('battle-intro-ack-complete',{
            revision:HK_BATTLE_INTRO_OVERLAY_ACK_REV,
            success:true
          });
          setTimeout(()=>{
            checkPuzzle();
            if (autoMapEnabled()) void runAutoMapTick('battle-intro-ack-complete');
          },100);
          return true;
        }

        recordDiagnostic('battle-intro-ack-complete',{
          revision:HK_BATTLE_INTRO_OVERLAY_ACK_REV,
          success:false
        });
        setTimeout(()=>{
          checkPuzzle();
          if (autoMapEnabled()) void runAutoMapTick('battle-intro-ack-retry');
        },420);
        return false;
      } finally {
        if (runId===battleAutoRunId) battleAutoRunning=false;
        lastSignature='';
      }
    }

'''
replace_between(ack_start,ack_end,ack_block,"battle intro acknowledge")

# Promote a text/icon child to the real clickable control before confirmation.
leave_btn_anchor=r'''    function autoMapLeaveConfirmButton(root=autoMapLeaveModalRoot(),cost=10) {
      if (!root) return null;

      const shared=treasureActionButton(root,{id:'',quantity:Number(cost)});
      if (shared && visible(shared) && !shared.disabled) return shared;
'''
leave_btn_new=r'''    function autoMapPromoteActionTarget(element,root=null) {
      if (!element) return null;
      let node=element;
      for (let depth=0;node && depth<7;depth++,node=node.parentElement) {
        if (root && node!==root && !root.contains(node)) break;
        if (!visible(node) || node.disabled || node.getAttribute?.('aria-disabled')==='true') continue;
        let actionable=false;
        try {
          const style=getComputedStyle(node);
          actionable=
            node.matches?.('button,[role="button"],a,[onclick]') ||
            !!node.onclick ||
            style.cursor==='pointer';
        } catch (_) {}
        if (actionable) return node;
        if (node===root) break;
      }
      return element;
    }

    function autoMapLeaveConfirmButton(root=autoMapLeaveModalRoot(),cost=10) {
      if (!root) return null;

      const shared=treasureActionButton(root,{id:'',quantity:Number(cost)});
      if (shared && visible(shared) && !shared.disabled) {
        return autoMapPromoteActionTarget(shared,root);
      }
'''
rep(leave_btn_anchor,leave_btn_new,"promote leave confirm")

# Tighten the final target return to the clickable ancestor.
old_return="      return candidates[0]?.element || null;\n    }\n\n    async function autoMapRecoverOpenLeaveModal"
new_return="      return candidates[0]?.element ? autoMapPromoteActionTarget(candidates[0].element,root) : null;\n    }\n\n    async function autoMapRecoverOpenLeaveModal"
rep(old_return,new_return,"leave confirm return promote")

# Ensure generic leave recovery never silently stalls after its confirmation loop.
old_tail=r'''      autoMapRetryNotBefore=Date.now()+800;
      return false;
    }

    function autoMapModalPrimaryButton'''
new_tail=r'''      autoMapRetryNotBefore=Date.now()+800;
      setTimeout(()=>void runAutoMapTick('leave-modal-still-in-room'),900);
      return false;
    }

    async function autoMapRecoverCompletedBattleExit(source='battle-complete') {
      if (!autoMapEnabled()) return false;
      if (!battleRecoverFinalRewardClaimed(source) && !battleFinalRewardClaimed) return false;

      const roomGone=()=>treasureGuideScreenVisible();
      const attempts=3;

      for (let attempt=1;attempt<=attempts;attempt++) {
        if (!autoMapEnabled()) return false;
        if (roomGone()) {
          autoMapRetryNotBefore=0;
          autoMapCurrentLot='';
          lastSignature='';
          recordDiagnostic('battle-complete-exit-done',{
            revision:HK_BATTLE_COMPLETE_EXIT_LOOP_REV,
            source,
            attempt,
            result:'map-visible'
          });
          return true;
        }

        let modal=autoMapLeaveModalRoot();
        if (!modal) {
          const exit=autoMapExitButton();
          if (!exit) {
            recordDiagnostic('battle-complete-exit-wait',{
              revision:HK_BATTLE_COMPLETE_EXIT_LOOP_REV,
              source,
              attempt,
              reason:'exit-button-missing'
            });
            await new Promise(resolve=>setTimeout(resolve,360));
            continue;
          }

          autoMapStatus('сражение → выход',{
            revision:HK_BATTLE_COMPLETE_EXIT_LOOP_REV,
            attempt
          });

          const er=exit.getBoundingClientRect?.();
          let sent=false;
          if (er && er.width>0 && er.height>0) {
            sent=dispatchMinigameOverlaySafeTapAt(
              er.left+er.width/2,
              er.top+er.height/2,
              'battle-complete-exit-open-'+String(attempt)
            );
          }
          if (!sent) sent=dispatchAutoMapTap(exit,'battle-complete-exit-open-'+String(attempt));
          if (!sent) {
            await new Promise(resolve=>setTimeout(resolve,300));
            continue;
          }

          const modalDeadline=Date.now()+2200;
          while (Date.now()<modalDeadline && autoMapEnabled()) {
            if (roomGone()) return true;
            modal=autoMapLeaveModalRoot();
            if (modal) break;
            await new Promise(resolve=>setTimeout(resolve,80));
          }
          if (roomGone()) return true;
          if (!modal) {
            await new Promise(resolve=>setTimeout(resolve,260));
            continue;
          }
        }

        const button=autoMapLeaveConfirmButton(modal,10);
        if (!button) {
          recordDiagnostic('battle-complete-exit-wait',{
            revision:HK_BATTLE_COMPLETE_EXIT_LOOP_REV,
            source,
            attempt,
            reason:'confirm-button-missing'
          });
          await new Promise(resolve=>setTimeout(resolve,320));
          continue;
        }

        autoMapStatus('сражение → подтверждаю выход 10',{
          revision:HK_BATTLE_COMPLETE_EXIT_LOOP_REV,
          attempt
        });

        const br=button.getBoundingClientRect?.();
        let sent=false;
        if (br && br.width>0 && br.height>0) {
          sent=dispatchMinigameOverlaySafeTapAt(
            br.left+br.width/2,
            br.top+br.height/2,
            'battle-complete-exit-confirm-'+String(attempt)
          );
        }
        if (!sent) {
          try {
            sent=await deviceNeutralActivate(
              button,
              'battle-complete-exit-confirm-device-'+String(attempt),
              ()=>roomGone() || !autoMapLeaveModalRoot(),
              1500
            );
          } catch (_) {}
        }

        const leaveDeadline=Date.now()+3600;
        while (Date.now()<leaveDeadline && autoMapEnabled()) {
          if (roomGone()) {
            autoMapRetryNotBefore=0;
            autoMapCurrentLot='';
            lastSignature='';
            autoMapReturnNotBefore=Date.now()+300;
            recordDiagnostic('battle-complete-exit-done',{
              revision:HK_BATTLE_COMPLETE_EXIT_LOOP_REV,
              source,
              attempt,
              result:'map-visible'
            });
            setTimeout(()=>void runAutoMapTick('battle-complete-map-visible'),340);
            return true;
          }
          await new Promise(resolve=>setTimeout(resolve,90));
        }

        // If confirmation merely closed its modal but the battle room is still
        // visible, do not treat that as success. Loop back and press Leave again.
        recordDiagnostic('battle-complete-exit-retry',{
          revision:HK_BATTLE_COMPLETE_EXIT_LOOP_REV,
          source,
          attempt,
          modalStillOpen:!!autoMapLeaveModalRoot(),
          battleTitle:battleScreenVisiblyCurrent()
        });
        await new Promise(resolve=>setTimeout(resolve,260));
      }

      autoMapRetryNotBefore=Date.now()+650;
      setTimeout(()=>void runAutoMapTick('battle-complete-exit-retry'),760);
      return false;
    }

    function autoMapModalPrimaryButton'''
rep(old_tail,new_tail,"battle completed exit helper")

old_preflight=r'''        autoMapRunning=true;
        const exitRunId=autoMapRunId;
        try {
          const left=await autoMapHandleExitOrContinue();
          if (!left) {
            autoMapRetryNotBefore=Math.max(autoMapRetryNotBefore,Date.now()+450);
            setTimeout(()=>void runAutoMapTick('battle-activated-exit-retry'),560);
          }
          return left;
        } finally {
          if (exitRunId===autoMapRunId) autoMapRunning=false;
        }'''
new_preflight=r'''        autoMapRunning=true;
        const exitRunId=autoMapRunId;
        try {
          const left=await autoMapRecoverCompletedBattleExit('automap-activated-reward');
          if (!left) {
            autoMapRetryNotBefore=Math.max(autoMapRetryNotBefore,Date.now()+450);
            setTimeout(()=>void runAutoMapTick('battle-activated-exit-retry'),560);
          }
          return left;
        } finally {
          if (exitRunId===autoMapRunId) autoMapRunning=false;
        }'''
rep(old_preflight,new_preflight,"battle completed preflight exit")

export_anchor="      battleOpenModalConfirmRevision:HK_BATTLE_OPEN_MODAL_CONFIRM_REV,"
rep(export_anchor,
    export_anchor+"\n      battleIntroOverlayAckRevision:HK_BATTLE_INTRO_OVERLAY_ACK_REV,\n      battleCompleteExitLoopRevision:HK_BATTLE_COMPLETE_EXIT_LOOP_REV,",
    "debug revisions")

p.write_text(s,encoding="utf-8")
print("PATCH_BATTLE_INTRO_EXIT_LOOP_1_18_95=PASS")
