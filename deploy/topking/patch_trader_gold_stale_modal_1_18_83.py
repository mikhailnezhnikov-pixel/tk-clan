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
    "// @version      1.18.82",
    "// @version      1.18.83\n"
    "// @release-note Тайный торговец: «Золотые монеты» теперь блокируются по итоговому товару (cur_gold/название/иконка), а не только по lotId. Если запрещённое окно каким-либо образом уже открылось и даже сохранилось после возврата на Карту сокровищ, Автокарта закрывает его как приоритетный stale-overlay, сбрасывает зависшее состояние и только потом продолжает маршрут.",
    "version"
)
rep("const BUILD_VERSION = '1.18.82';","const BUILD_VERSION = '1.18.83';","build")

anchor="  const HK_TRADER_GOLD_SKIP_REV='trader-gold-currency-skip-20260928-r1';"
rep(
    anchor,
    anchor+"\n  const HK_TRADER_GOLD_STALE_MODAL_REV='trader-gold-stale-modal-reset-20260929-r1';",
    "gold stale modal revision"
)

old_forbidden=r'''    function traderForbiddenGoldLot(lotId) {
      const id=String(lotId||'').toLowerCase();
      if (!id) return false;

      // These trader offers convert Treasure resources into the regular
      // account gold currency (cur_gold). They are intentionally never bought.
      return /verse_gold4(?:coins|food)/.test(id) ||
        /(?:^|_)gold4(?:coins|food)(?:_|$)/.test(id);
    }
'''
new_forbidden=r'''    function traderForbiddenGoldLot(lotId) {
      const id=String(lotId||'').toLowerCase();
      if (!id) return false;

      // These trader offers convert Treasure resources into the regular
      // account gold currency (cur_gold). They are intentionally never bought.
      return /verse_gold4(?:coins|food)/.test(id) ||
        /(?:^|_)gold4(?:coins|food)(?:_|$)/.test(id) ||
        /(?:^|_)cur_gold(?:_|$)/.test(id);
    }

    function traderForbiddenGoldRow(row) {
      if (!row) return false;
      const catalog=traderCatalogRow(row.lotId);
      const assets=[...row.element?.querySelectorAll?.('img')||[]]
        .map(img=>[
          img.getAttribute?.('src')||'',
          img.getAttribute?.('alt')||'',
          img.getAttribute?.('title')||''
        ].join(' '))
        .join(' ');
      const blob=[
        row.lotId,
        row.text,
        catalog?.rewardId,
        catalog?.name,
        catalog?.description,
        catalog?.icon,
        catalog?.image,
        JSON.stringify(catalog?.reward||{}),
        JSON.stringify(catalog?.content||{}),
        assets
      ].map(value=>String(value||'').toLowerCase()).join(' ');

      return traderForbiddenGoldLot(row.lotId) ||
        /(?:^|[_\s-])cur_gold(?:[_\s-]|$)/i.test(blob) ||
        /золотые\s+монеты|gold(?:en)?\s+coins/i.test(blob);
    }
'''
rep(old_forbidden,new_forbidden,"strong gold row denylist")

old_approved_start=r'''    function traderApprovedRow(row) {
      if (!row) return false;
      if (traderApprovedLot(row.lotId)) return true;

      const catalog=traderCatalogRow(row.lotId);
'''
new_approved_start=r'''    function traderApprovedRow(row) {
      if (!row) return false;

      // Deny by the actual reward/name/icon BEFORE any permissive lot-id rule.
      // This prevents a gold lot whose id also contains "food" or "coins" from
      // being accepted by a generic resource whitelist.
      if (traderForbiddenGoldRow(row)) {
        try { row.element.dataset.hkTraderSkip='1'; } catch (_) {}
        return false;
      }

      if (traderApprovedLot(row.lotId)) return true;

      const catalog=traderCatalogRow(row.lotId);
'''
rep(old_approved_start,new_approved_start,"deny before whitelist")

# Strengthen modal detection and provide a robust close target for icon-only X.
old_modal_close=r'''    function traderForbiddenGoldModalRoot() {
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
'''
new_modal_close=r'''    function traderForbiddenGoldModalRoot() {
      const candidates=[...document.querySelectorAll('[role="dialog"],[aria-modal="true"],[class*="modal"],[class*="popup"],[class*="dialog"],div')]
        .filter(visible)
        .map(element=>{
          const rect=element.getBoundingClientRect?.();
          const text=clean(element.innerText||element.textContent||'');
          const assets=[...element.querySelectorAll?.('img')||[]]
            .map(img=>String(img.src||'')+' '+String(img.alt||'')+' '+String(img.title||''))
            .join(' ');
          return {element,rect,blob:(text+' '+assets).toLowerCase()};
        })
        .filter(row=>row.rect && row.rect.width>=Math.min(240,window.innerWidth*0.35) && row.rect.height>=180)
        .filter(row=>
          /золотые\s+монеты|gold(?:en)?\s+coins/i.test(row.blob) ||
          /(?:^|[_\s/-])cur_gold(?:[_\s/.-]|$)/i.test(row.blob)
        )
        .filter(row=>row.rect.width<=window.innerWidth*0.99 && row.rect.height<=window.innerHeight*0.98)
        .sort((a,b)=>a.rect.width*a.rect.height-b.rect.width*b.rect.height);
      return candidates[0]?.element || null;
    }

    function traderForbiddenGoldCloseButton(root=traderForbiddenGoldModalRoot()) {
      if (!root) return null;
      const rr=root.getBoundingClientRect?.();
      if (!rr) return null;

      const generic=autoMapModalCloseButton(root);
      if (generic && visible(generic) && !generic.disabled) return generic;

      const rows=[...root.querySelectorAll('button,[role="button"],a,[onclick],div,span,svg')]
        .filter(element=>element && !element.disabled && visible(element))
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const aria=clean(
            element.getAttribute?.('aria-label') ||
            element.getAttribute?.('title') ||
            element.getAttribute?.('data-tooltip') ||
            ''
          ).trim();
          const rect=element.getBoundingClientRect?.() || {left:0,top:0,width:0,height:0};
          let actionable=false;
          try {
            actionable=
              element.matches?.('button,[role="button"],a,[onclick]') ||
              !!element.onclick ||
              getComputedStyle(element).cursor==='pointer';
          } catch (_) {}
          const topRight=
            rect.top<=rr.top+rr.height*0.28 &&
            rect.left>=rr.left+rr.width*0.66;
          const small=
            rect.width>0 && rect.width<=110 &&
            rect.height>0 && rect.height<=110;
          let score=0;
          if (/^(?:×|✕|✖|Закрыть|Close|Назад|Back)$/i.test(text)) score+=800;
          if (/close|закрыть|back|назад/i.test(aria)) score+=700;
          if (topRight) score+=260;
          if (small) score+=140;
          if (actionable) score+=180;
          if (element.querySelector?.('svg,img,use,path')) score+=80;
          if (/^\d{1,5}$/.test(text)) score-=900;
          return {
            element:traderClickableTarget(element,root)||element,
            score,
            rect
          };
        })
        .filter(row=>row.score>=500)
        .sort((a,b)=>b.score-a.score || a.rect.width*a.rect.height-b.rect.width*b.rect.height);
      return rows[0]?.element || null;
    }

    async function traderDismissForbiddenGoldModal(source='trader') {
      const root=traderForbiddenGoldModalRoot();
      if (!root) return false;
      const close=traderForbiddenGoldCloseButton(root);
      const accepted=()=>!traderForbiddenGoldModalRoot();
      let ok=false;

      if (close) {
        try {
          ok=await deviceNeutralActivate(
            close,
            'trader-forbidden-gold-close-'+source,
            accepted,
            1200
          );
        } catch (_) {}
        if (!ok && close.isConnected) {
          const sent=dispatchAutoMapTap(close,'trader-forbidden-gold-close-fallback-'+source);
          if (sent) {
            try { ok=await waitDeviceNeutralCondition(accepted,1300,70); } catch (_) {}
          }
        }
      }

      // Icon-only X can be rendered as a pseudo-element with no actionable
      // child node. Last-resort tap the modal's own top-right close zone.
      if (!ok && root.isConnected) {
        const rr=root.getBoundingClientRect?.();
        if (rr && rr.width>0 && rr.height>0) {
          const x=rr.right-Math.max(18,Math.min(28,rr.width*0.04));
          const y=rr.top+Math.max(18,Math.min(28,rr.height*0.06));
          const sent=dispatchBattleTapAt(x,y,'trader-forbidden-gold-close-corner-'+source);
          if (sent) {
            try { ok=await waitDeviceNeutralCondition(accepted,1500,70); } catch (_) {}
          }
        }
      }

      recordDiagnostic('trader-forbidden-gold-modal-reset',{
        revision:HK_TRADER_GOLD_STALE_MODAL_REV,
        source,
        success:!!ok,
        hasClose:!!close
      });

      if (ok) {
        traderRetryNotBefore=0;
        autoMapRetryNotBefore=0;
        autoMapCurrentLot='';
        lastSignature='';
        await new Promise(resolve=>setTimeout(resolve,100));
      }
      return !!ok;
    }

    function traderCloseForbiddenGoldModal(root=traderForbiddenGoldModalRoot()) {
      if (!root) return false;
      const close=traderForbiddenGoldCloseButton(root);
      if (!close) return false;
      const ok=dispatchAutoMapTap(close,'trader-forbidden-gold-close');
      recordDiagnostic('trader-forbidden-gold-modal',{
        revision:HK_TRADER_GOLD_STALE_MODAL_REV,
        action:ok?'closed':'close-failed'
      });
      return !!ok;
    }
'''
rep(old_modal_close,new_modal_close,"robust forbidden gold modal close")

# runTraderAuto must close and verify the forbidden modal, not just fire one tap.
old_run=r'''      const forbiddenGoldModal=traderForbiddenGoldModalRoot();
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
'''
new_run=r'''      const forbiddenGoldModal=traderForbiddenGoldModalRoot();
      if (forbiddenGoldModal) {
        traderAutoRunning=true;
        const blockedRunId=++traderAutoRunId;
        try {
          const closed=await traderDismissForbiddenGoldModal('trader-runner');
          recordDiagnostic('trader-forbidden-gold-skip',{
            revision:HK_TRADER_GOLD_STALE_MODAL_REV,
            closed:!!closed
          });
          return !!closed;
        } finally {
          if (blockedRunId===traderAutoRunId) traderAutoRunning=false;
          lastSignature='';
          setTimeout(checkPuzzle,120);
        }
      }
'''
rep(old_run,new_run,"verified trader modal dismissal")

# Generic AutoMap confirmation must refuse this modal even if it was opened by
# a stale/wrong card click from a previous scan.
modal_guard_anchor=r'''      if (!modal) {
        // No modal + no observed change: do not retry the same element immediately.
'''
modal_guard=r'''      const forbiddenGoldModal=traderForbiddenGoldModalRoot();
      if (forbiddenGoldModal) {
        recordDiagnostic('auto-map-forbidden-gold-confirm-blocked',{
          revision:HK_TRADER_GOLD_STALE_MODAL_REV,
          label:String(label||'')
        });
        await traderDismissForbiddenGoldModal('auto-map-confirm-guard');
        autoMapCurrentLot='';
        lastSignature='';
        return false;
      }

'''
if s.count(modal_guard_anchor)!=1:
    raise SystemExit("autoMap modal guard anchor missing")
s=s.replace(modal_guard_anchor,modal_guard+modal_guard_anchor,1)

# Global preflight: stale gold modal outranks leave-confirm, map traversal,
# module ownership, cooldowns, and new-map detection.
tick_anchor=r'''      ensureAutoMapToggle();

      // A leave-confirmation modal can survive a redraw/retry. It is always
'''
tick_guard=r'''      ensureAutoMapToggle();

      const forbiddenGoldModal=traderForbiddenGoldModalRoot();
      if (forbiddenGoldModal) {
        autoMapRunning=true;
        const blockedRunId=autoMapRunId;
        traderAutoRunId+=1;
        traderAutoRunning=false;
        autoMapCurrentLot='';
        autoMapRetryNotBefore=0;
        lastSignature='';
        autoMapStatus('закрываю Золотые монеты',{
          revision:HK_TRADER_GOLD_STALE_MODAL_REV,
          source
        });
        try {
          const closed=await traderDismissForbiddenGoldModal('auto-map-preflight');
          if (!closed) {
            setTimeout(()=>void runAutoMapTick('forbidden-gold-modal-retry'),300);
          } else {
            setTimeout(()=>{
              checkPuzzle();
              void runAutoMapTick('forbidden-gold-modal-cleared');
            },140);
          }
          return !!closed;
        } finally {
          if (blockedRunId===autoMapRunId) autoMapRunning=false;
        }
      }

      // A leave-confirmation modal can survive a redraw/retry. It is always
'''
rep(tick_anchor,tick_guard,"global gold modal preflight")

# checkPuzzle must wake up the recovery path even when the current screen
# signature has already fallen back to NONE/map and would otherwise be cached.
check_anchor=r'''    function checkPuzzle() {
      ensureAutoMapToggle();

      // The intro overlay can hide the board completely, so its handling must
'''
check_guard=r'''    function checkPuzzle() {
      ensureAutoMapToggle();

      const forbiddenGoldModal=traderForbiddenGoldModalRoot();
      if (forbiddenGoldModal) {
        lastSignature='';
        if (autoMapEnabled() && !autoMapRunning) {
          void runAutoMapTick('forbidden-gold-overlay');
          return;
        }
        if (traderAutoEnabled() && !traderAutoRunning) {
          void traderDismissForbiddenGoldModal('check-puzzle');
          return;
        }
      }

      // The intro overlay can hide the board completely, so its handling must
'''
rep(check_anchor,check_guard,"checkPuzzle gold overlay recovery")

export_anchor="      traderGoldSkipRevision:HK_TRADER_GOLD_SKIP_REV,"
rep(
    export_anchor,
    export_anchor+"\n      traderGoldStaleModalRevision:HK_TRADER_GOLD_STALE_MODAL_REV,",
    "debug export"
)

for marker in [
    "// @version      1.18.83",
    "const BUILD_VERSION = '1.18.83';",
    "trader-gold-stale-modal-reset-20260929-r1",
    "function traderForbiddenGoldRow(row)",
    "if (traderForbiddenGoldRow(row))",
    "function traderForbiddenGoldCloseButton",
    "async function traderDismissForbiddenGoldModal",
    "trader-forbidden-gold-close-corner-",
    "auto-map-forbidden-gold-confirm-blocked",
    "forbidden-gold-modal-retry",
    "forbidden-gold-overlay",
    "traderGoldStaleModalRevision:HK_TRADER_GOLD_STALE_MODAL_REV",
    "battle-visible-point-truth-20260929-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

p.write_text(s,encoding="utf-8")
print("TRADER_GOLD_STALE_MODAL_1_18_83=PASS")
