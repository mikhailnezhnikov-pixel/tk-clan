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

rep("// @version      1.18.43",
    "// @version      1.18.44\n// @release-note Сокровищница: путь теперь выбирается строго по фактической позиции на экране — всегда левый видимый вариант, а не по номеру lot-id. Также исправлено зависание на окне «Покинуть локацию»: уже открытая модалка подхватывается без повторного нажатия выхода, кнопка стоимости 10 ищется отдельно и подтверждается один раз, после чего HK ждёт возврата на Карту сокровищ.",
    "version")
rep("const BUILD_VERSION = '1.18.43';",
    "const BUILD_VERSION = '1.18.44';",
    "build")
rep("  const HK_BATTLE_SKIP_CANON_REV = 'battle-skip-run9-20260927-r1';",
    "  const HK_BATTLE_SKIP_CANON_REV = 'battle-skip-run9-20260927-r1';\n  const HK_TREASURY_LEFT_PATH_REV = 'treasury-left-path-exit-recovery-20260927-r1';",
    "revision")

old_choice="""    function autoMapTreasuryChoice() {
      return [...document.querySelectorAll('[data-lot-id^="mf_fair_treasury_room_choose_way_"]')]
        .filter(visible)
        .map(element=>{
          const lotId=String(element.getAttribute('data-lot-id')||'');
          const m=lotId.match(/choose_way_(\\d+)/);
          const text=clean(element.innerText||element.textContent||'').trim();
          const costMatch=text.match(/(?:^|\\s)(\\d{1,4})(?:\\s|$)/);
          return {element,lotId,index:m?Number(m[1]):999,cost:costMatch?Number(costMatch[1]):null};
        })
        .sort((a,b)=>a.index-b.index)[0] || null;
    }
"""
new_choice="""    function autoMapTreasuryChoice() {
      const rows=[...document.querySelectorAll('[data-lot-id^="mf_fair_treasury_room_choose_way_"]')]
        .filter(visible)
        .map(element=>{
          const lotId=String(element.getAttribute('data-lot-id')||'');
          const m=lotId.match(/choose_way_(\\d+)/);
          const text=clean(element.innerText||element.textContent||'').trim();
          const costMatch=text.match(/(?:^|\\s)(\\d{1,4})(?:\\s|$)/);
          const rect=element.getBoundingClientRect?.() || {left:99999,top:99999,width:0,height:0};
          return {
            element,
            lotId,
            index:m?Number(m[1]):999,
            cost:costMatch?Number(costMatch[1]):null,
            x:rect.left+rect.width/2,
            y:rect.top+rect.height/2
          };
        })
        .filter(row=>Number.isFinite(row.x) && row.x>=0)
        .sort((a,b)=>a.x-b.x || a.y-b.y || a.index-b.index);

      const choice=rows[0] || null;
      if (choice) {
        recordDiagnostic('treasury-left-path-selected',{
          revision:HK_TREASURY_LEFT_PATH_REV,
          lotId:choice.lotId,
          index:choice.index,
          x:Math.round(choice.x),
          y:Math.round(choice.y),
          visibleChoices:rows.map(row=>({
            lotId:row.lotId,
            index:row.index,
            x:Math.round(row.x),
            y:Math.round(row.y)
          }))
        });
      }
      return choice;
    }
"""
rep(old_choice,new_choice,"leftmost treasury choice")

anchor="""    function autoMapModalPrimaryButton(root,costHint=null) {
"""
helper="""    function autoMapLeaveModalRoot() {
      const roots=[...document.querySelectorAll('[role="dialog"],[aria-modal="true"],[class*="modal"],[class*="popup"],[class*="dialog"],div')]
        .filter(visible)
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const rect=element.getBoundingClientRect?.() || {width:0,height:0};
          return {element,text,rect,area:rect.width*rect.height};
        })
        .filter(row=>/Покинуть локацию|Leave location|Exit location/i.test(row.text))
        .filter(row=>/Продолжить\\?|Continue\\?|10|Назад|Back/i.test(row.text))
        .filter(row=>row.rect.width>=Math.min(260,window.innerWidth*0.50) && row.rect.height>=180)
        .sort((a,b)=>a.area-b.area);
      return roots[0]?.element || null;
    }

    function autoMapLeaveConfirmButton(root=autoMapLeaveModalRoot(),cost=10) {
      if (!root) return null;

      const shared=treasureActionButton(root,{id:'',quantity:Number(cost)});
      if (shared && visible(shared) && !shared.disabled) return shared;

      const rr=root.getBoundingClientRect?.();
      if (!rr) return null;
      const centerX=rr.left+rr.width/2;

      const candidates=[...root.querySelectorAll('button,[role="button"],a,[onclick],div,span')]
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
          if (text===String(cost)) score+=500;
          else if (new RegExp('(?:^|\\\\s)'+String(cost)+'(?:\\\\s|$)').test(text) && text.length<=12) score+=280;
          if (rect.top>=rr.top+rr.height*0.48) score+=180;
          if (Math.abs(cx-centerX)<=rr.width*0.30) score+=160;
          if (rect.width>=rr.width*0.36 && rect.width<=rr.width*0.92) score+=140;
          if (rect.height>=36 && rect.height<=130) score+=90;
          if (actionable) score+=100;
          if (/Назад|Back|Закрыть|Close|×|✕/i.test(text)) score-=900;

          return {element,score,rect};
        })
        .filter(row=>row.score>=650)
        .sort((a,b)=>b.score-a.score || b.rect.width*b.rect.height-a.rect.width*a.rect.height);

      return candidates[0]?.element || null;
    }

    async function autoMapRecoverOpenLeaveModal(source='leave-modal-recovery') {
      if (!autoMapEnabled()) return false;
      const modal=autoMapLeaveModalRoot();
      if (!modal) return false;

      const button=autoMapLeaveConfirmButton(modal,10);
      if (!button) {
        autoMapStatus('жду подтверждение выхода',{
          revision:HK_TREASURY_LEFT_PATH_REV,
          source
        });
        return false;
      }

      const before=autoMapStateFingerprint();
      const rect=button.getBoundingClientRect?.();
      autoMapStatus('подтверждаю выход 10',{
        revision:HK_TREASURY_LEFT_PATH_REV,
        source
      });
      recordDiagnostic('leave-modal-confirm-target',{
        revision:HK_TREASURY_LEFT_PATH_REV,
        source,
        text:clean(button.innerText||button.textContent||'').trim(),
        left:Math.round(rect?.left||0),
        top:Math.round(rect?.top||0),
        width:Math.round(rect?.width||0),
        height:Math.round(rect?.height||0)
      });

      autoMapLastActionAt=Date.now();
      if (!dispatchAutoMapTap(button,'leave-modal-confirm-10-'+source)) return false;

      const started=Date.now();
      while (Date.now()-started<4500) {
        if (!autoMapEnabled()) return false;
        if (!autoMapLeaveModalRoot()) {
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
        }
        await new Promise(resolve=>setTimeout(resolve,90));
      }

      autoMapRetryNotBefore=Date.now()+800;
      return false;
    }

"""
if s.count(anchor)!=1:
    raise SystemExit("autoMapModalPrimaryButton anchor missing")
s=s.replace(anchor,helper+anchor,1)

# Treasury exit: recover a pre-opened leave modal before trying the exit button again.
old_direct_start="""    async function autoMapDirectTreasuryExit() {
      if (!autoMapEnabled() || !autoMapTreasuryDone()) return false;
      const exit=autoMapExitButton();
      if (!exit) return false;

      await autoMapWaitActionGap();
"""
new_direct_start="""    async function autoMapDirectTreasuryExit() {
      if (!autoMapEnabled() || !autoMapTreasuryDone()) return false;

      if (autoMapLeaveModalRoot()) {
        return await autoMapRecoverOpenLeaveModal('treasury-preopen');
      }

      const exit=autoMapExitButton();
      if (!exit) return false;

      await autoMapWaitActionGap();
"""
rep(old_direct_start,new_direct_start,"treasury preopen leave recovery")

# Replace generic modal confirmation inside treasury direct exit with exact leave-confirm resolver.
old_modal_confirm="""        if (!modalConfirmed) {
          const modal=treasureModalRoot(null);
          if (modal) {
            const action=autoMapModalPrimaryButton(modal,null);
            if (action) {
              modalConfirmed=dispatchAutoMapTap(action,'treasury-leave-confirm-direct');
              if (modalConfirmed) {
                autoMapLastActionAt=Date.now();
                recordDiagnostic('treasury-exit-confirm',{
                  revision:HK_TREASURY_VISUAL_EXIT_REV
                });
              }
            }
          }
        }
"""
new_modal_confirm="""        if (!modalConfirmed) {
          const modal=autoMapLeaveModalRoot() || treasureModalRoot(null);
          if (modal) {
            const action=autoMapLeaveConfirmButton(modal,10) || autoMapModalPrimaryButton(modal,10);
            if (action) {
              modalConfirmed=dispatchAutoMapTap(action,'treasury-leave-confirm-direct-10');
              if (modalConfirmed) {
                autoMapLastActionAt=Date.now();
                recordDiagnostic('treasury-exit-confirm',{
                  revision:HK_TREASURY_LEFT_PATH_REV,
                  cost:10
                });
              }
            }
          }
        }
"""
rep(old_modal_confirm,new_modal_confirm,"strict treasury leave confirm")

# Early recovery before retry cooldown so a currently open modal can never deadlock.
old_tick_head="""      ensureAutoMapToggle();

      // A completed Treasury is a navigation handoff, not another chest
"""
new_tick_head="""      ensureAutoMapToggle();

      // A leave-confirmation modal can survive a redraw/retry. It is always
      // higher priority than route selection or generic cooldowns.
      if (autoMapLeaveModalRoot()) {
        autoMapRunning=true;
        const modalRunId=autoMapRunId;
        try {
          return await autoMapRecoverOpenLeaveModal('tick-preflight');
        } finally {
          if (modalRunId===autoMapRunId) autoMapRunning=false;
        }
      }

      // A completed Treasury is a navigation handoff, not another chest
"""
rep(old_tick_head,new_tick_head,"leave modal preflight")

rep("      battleSkipCanonRevision:HK_BATTLE_SKIP_CANON_REV,\n      start,",
    "      battleSkipCanonRevision:HK_BATTLE_SKIP_CANON_REV,\n      treasuryLeftPathRevision:HK_TREASURY_LEFT_PATH_REV,\n      start,",
    "export treasury left revision")

for marker in [
    "// @version      1.18.44",
    "const BUILD_VERSION = '1.18.44';",
    "treasury-left-path-exit-recovery-20260927-r1",
    "treasury-left-path-selected",
    "function autoMapLeaveModalRoot()",
    "function autoMapLeaveConfirmButton(",
    "async function autoMapRecoverOpenLeaveModal(",
    "treasury-preopen",
    "tick-preflight",
    "treasury-leave-confirm-direct-10",
    "battle-skip-run9-20260927-r1"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("TREASURY_LEFT_PATH_EXIT_RECOVERY_1_18_44=PASS")
