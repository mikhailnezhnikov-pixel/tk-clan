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
    "// @version      1.18.79",
    "// @version      1.18.80\n"
    "// @release-note Сражение: исправлен мобильный клик по нижним врагам. Перед ударом выбранная карточка теперь обязательно прокручивается в безопасную центральную область, скрипт ждёт завершения прокрутки и проверяет, что точка клика действительно принадлежит карточке врага, а не закреплённой кнопке «Покинуть локацию».",
    "version"
)
rep("const BUILD_VERSION = '1.18.79';","const BUILD_VERSION = '1.18.80';","build")

anchor="  const HK_BATTLE_EGG_BERRY_REV='battle-egg-one-berry-buy-20260928-r1';"
rep(
    anchor,
    anchor+"\n  const HK_BATTLE_TARGET_SCROLL_REV='battle-target-safe-scroll-20260928-r1';",
    "scroll revision"
)

old_scroll=r'''    function battleElementInViewport(element) {
      if (!element || !element.isConnected) return false;
      const rect=element.getBoundingClientRect?.();
      if (!rect || rect.width<=0 || rect.height<=0) return false;
      const cx=rect.left+rect.width/2;
      const cy=rect.top+rect.height/2;
      return cx>=1 && cx<=window.innerWidth-1 && cy>=1 && cy<=window.innerHeight-1;
    }

    function battleScrollTargetIntoViewport(element,label='battle-target') {
      if (!element || !element.isConnected) return false;
      if (battleElementInViewport(element)) return true;
      try {
        element.scrollIntoView({behavior:'auto',block:'center',inline:'center'});
      } catch (_) {
        try { element.scrollIntoView(); } catch (_) {}
      }
      const inViewport=battleElementInViewport(element);
      recordDiagnostic('battle-target-scroll',{
        revision:HK_BATTLE_VIEWPORT_RESUME_REV,
        label,
        success:inViewport
      });
      return inViewport;
    }

    function dispatchBattleOverlaySafeTap(element,label='battle-overlay-safe-tap') {
      if (!element || !element.isConnected) return false;
      battleScrollTargetIntoViewport(element,label);
      const rect=element.getBoundingClientRect?.();
      if (!rect || rect.width<=0 || rect.height<=0) return false;

      if (!battleElementInViewport(element)) {
        try {
          element.click?.();
          recordDiagnostic('battle-native-offscreen-click',{
            revision:HK_BATTLE_VIEWPORT_RESUME_REV,
            label
          });
          return true;
        } catch (_) {
          return false;
        }
      }

      const x=Math.max(1,Math.min(window.innerWidth-1,rect.left+rect.width/2));
      const y=Math.max(1,Math.min(window.innerHeight-1,rect.top+rect.height/2));
      const leaf=battleElementFromPointIgnoringOverlays(x,y,element) || element;
      if (!leaf) return false;
      const options={bubbles:true,cancelable:true,clientX:x,clientY:y,screenX:x,screenY:y,button:0,buttons:1,pointerId:1,pointerType:'touch',isPrimary:true};
      try { leaf.dispatchEvent(new PointerEvent('pointerdown',options)); } catch (_) {}
      try { leaf.dispatchEvent(new MouseEvent('mousedown',{...options,buttons:1})); } catch (_) {}
      try { leaf.dispatchEvent(new PointerEvent('pointerup',{...options,buttons:0})); } catch (_) {}
      try { leaf.dispatchEvent(new MouseEvent('mouseup',{...options,buttons:0})); } catch (_) {}
      try { leaf.click?.(); } catch (_) {}
      recordDiagnostic('battle-overlay-safe-tap',{
        revision:HK_BATTLE_VIEWPORT_RESUME_REV,
        label,
        x:Math.round(x),
        y:Math.round(y),
        tag:leaf.tagName||'',
        overlaysIgnored:battleUiOverlays().length,
        autoScrolled:true
      });
      return true;
    }
'''

new_scroll=r'''    function battleElementInViewport(element) {
      if (!element || !element.isConnected) return false;
      const rect=element.getBoundingClientRect?.();
      if (!rect || rect.width<=0 || rect.height<=0) return false;
      const cx=rect.left+rect.width/2;
      const cy=rect.top+rect.height/2;
      return cx>=1 && cx<=window.innerWidth-1 && cy>=1 && cy<=window.innerHeight-1;
    }

    function battlePointBelongsToElement(element,leaf) {
      if (!element || !leaf) return false;
      if (leaf===element) return true;
      try {
        if (element.contains?.(leaf)) return true;
        if (leaf.contains?.(element)) return true;
      } catch (_) {}
      return false;
    }

    function battleElementTapProbe(element) {
      if (!element || !element.isConnected) return {ready:false,reason:'missing'};
      const rect=element.getBoundingClientRect?.();
      if (!rect || rect.width<=0 || rect.height<=0) return {ready:false,reason:'no-box'};
      const x=rect.left+rect.width/2;
      const y=rect.top+rect.height/2;
      if (x<1 || x>window.innerWidth-1 || y<1 || y>window.innerHeight-1) {
        return {ready:false,reason:'offscreen',x,y,rect};
      }
      const leaf=battleElementFromPointIgnoringOverlays(x,y,null);
      if (!battlePointBelongsToElement(element,leaf)) {
        return {
          ready:false,
          reason:'occluded',
          x,
          y,
          rect,
          leaf,
          leafTag:leaf?.tagName||'',
          leafText:clean(leaf?.innerText||leaf?.textContent||'').slice(0,80)
        };
      }
      return {ready:true,reason:'ready',x,y,rect,leaf};
    }

    function battleTargetSafeBand(element) {
      const probe=battleElementTapProbe(element);
      if (!probe.ready) return false;
      const cy=probe.y;
      // Keep enemy cards away from the sticky game footer / Safari toolbar and
      // away from the top navigation. The middle of the visual viewport is the
      // only device-neutral click area shared by iPhone, tablet and desktop.
      const top=Math.max(90,window.innerHeight*0.24);
      const bottom=Math.min(window.innerHeight-140,window.innerHeight*0.68);
      return cy>=top && cy<=Math.max(top+40,bottom);
    }

    function battleNextPaint() {
      return new Promise(resolve=>{
        try {
          requestAnimationFrame(()=>requestAnimationFrame(resolve));
        } catch (_) {
          setTimeout(resolve,40);
        }
      });
    }

    async function battleScrollTargetIntoViewportAsync(element,label='battle-target',runId=null) {
      if (!element || !element.isConnected) return false;
      if (battleTargetSafeBand(element)) return true;

      const before=element.getBoundingClientRect?.();
      try {
        element.scrollIntoView({behavior:'auto',block:'center',inline:'nearest'});
      } catch (_) {
        try { element.scrollIntoView(); } catch (_) {}
      }
      await battleNextPaint();
      await new Promise(resolve=>setTimeout(resolve,120));
      if (runId!==null && (runId!==battleAutoRunId || !battleAutoEnabled())) return false;

      let probe=battleElementTapProbe(element);
      if (!probe.ready || !battleTargetSafeBand(element)) {
        const host=battleScrollHost();
        const isWindowHost=!host ||
          host===document.scrollingElement ||
          host===document.documentElement ||
          host===document.body;

        try {
          const rect=element.getBoundingClientRect?.();
          if (rect) {
            const center=rect.top+rect.height/2;
            if (isWindowHost) {
              const desired=Math.max(120,Math.min(window.innerHeight-180,window.innerHeight*0.48));
              window.scrollBy({top:center-desired,left:0,behavior:'auto'});
            } else {
              const hostRect=host.getBoundingClientRect?.();
              const desired=(hostRect?.top||0)+Math.max(80,Math.min((hostRect?.height||window.innerHeight)*0.48,window.innerHeight*0.52));
              host.scrollTop+=center-desired;
            }
          }
        } catch (_) {}

        await battleNextPaint();
        await new Promise(resolve=>setTimeout(resolve,120));
        if (runId!==null && (runId!==battleAutoRunId || !battleAutoEnabled())) return false;
        probe=battleElementTapProbe(element);
      }

      const success=probe.ready && battleTargetSafeBand(element);
      const after=element.getBoundingClientRect?.();
      recordDiagnostic('battle-target-safe-scroll',{
        revision:HK_BATTLE_TARGET_SCROLL_REV,
        label,
        success,
        reason:probe.reason,
        beforeTop:Math.round(before?.top||0),
        afterTop:Math.round(after?.top||0),
        centerY:Math.round(probe.y||0),
        viewportHeight:window.innerHeight,
        blockerTag:probe.leafTag||'',
        blockerText:probe.leafText||''
      });
      return success;
    }

    function dispatchBattleOverlaySafeTap(element,label='battle-overlay-safe-tap') {
      if (!element || !element.isConnected) return false;
      const probe=battleElementTapProbe(element);
      if (!probe.ready) {
        recordDiagnostic('battle-overlay-safe-tap-blocked',{
          revision:HK_BATTLE_TARGET_SCROLL_REV,
          label,
          reason:probe.reason,
          blockerTag:probe.leafTag||'',
          blockerText:probe.leafText||''
        });
        return false;
      }

      const x=Math.max(1,Math.min(window.innerWidth-1,probe.x));
      const y=Math.max(1,Math.min(window.innerHeight-1,probe.y));
      const leaf=probe.leaf || element;
      const options={bubbles:true,cancelable:true,clientX:x,clientY:y,screenX:x,screenY:y,button:0,buttons:1,pointerId:1,pointerType:'touch',isPrimary:true};
      try { leaf.dispatchEvent(new PointerEvent('pointerdown',options)); } catch (_) {}
      try { leaf.dispatchEvent(new MouseEvent('mousedown',{...options,buttons:1})); } catch (_) {}
      try { leaf.dispatchEvent(new PointerEvent('pointerup',{...options,buttons:0})); } catch (_) {}
      try { leaf.dispatchEvent(new MouseEvent('mouseup',{...options,buttons:0})); } catch (_) {}
      try { leaf.click?.(); } catch (_) {}
      recordDiagnostic('battle-overlay-safe-tap',{
        revision:HK_BATTLE_TARGET_SCROLL_REV,
        label,
        x:Math.round(x),
        y:Math.round(y),
        tag:leaf.tagName||'',
        overlaysIgnored:battleUiOverlays().length,
        verifiedTarget:true
      });
      return true;
    }
'''
rep(old_scroll,new_scroll,"safe async enemy scrolling")

old_ensure=r'''    async function battleEnsureLotElement(lotId,slot,runId) {
      let element=battleFindLotElement(lotId);
      if (element) return element;

      const host=battleScrollHost();
      if (!host) return null;
      const isWindowHost=host===document.scrollingElement || host===document.documentElement || host===document.body;
      const max=Math.max(0,(isWindowHost?document.documentElement.scrollHeight:host.scrollHeight)-
        (isWindowHost?window.innerHeight:host.clientHeight));
      const original=isWindowHost ? window.scrollY : host.scrollTop;
      const row=Math.max(0,Math.min(BATTLE_ROWS-1,Math.floor((Number(slot)-BATTLE_FIRST_SLOT)/BATTLE_COLS)));
      const preferred=max*(row/Math.max(1,BATTLE_ROWS-1));
      const positions=[preferred,0,max*0.34,max*0.67,max];

      for (const position of positions) {
        if (runId!==battleAutoRunId || !battleAutoEnabled()) return null;
        try {
          if (isWindowHost) window.scrollTo(0,Math.max(0,position));
          else host.scrollTop=Math.max(0,position);
        } catch (_) {}
        await new Promise(resolve=>setTimeout(resolve,90));
        element=battleFindLotElement(lotId);
        if (element) {
          recordDiagnostic('battle-target-auto-mounted',{
            revision:HK_BATTLE_FULL_STATE_REV,
            lotId,
            slot:Number(slot)||0,
            scrollPosition:Math.round(position)
          });
          return element;
        }
      }

      try {
        if (isWindowHost) window.scrollTo(0,original);
        else host.scrollTop=original;
      } catch (_) {}
      return null;
    }

    async function battleEnsureElementForSlot(slot,runId) {
      const row=getBattleBoard()[Number(slot)-BATTLE_FIRST_SLOT];
      const lotId=String(row?.lotId||'');
      let element=battleElementForSlot(slot);
      if (element) return element;
      if (!lotId) return null;
      return await battleEnsureLotElement(lotId,slot,runId);
    }
'''

new_ensure=r'''    async function battleEnsureLotElement(lotId,slot,runId) {
      let element=battleFindLotElement(lotId);
      if (element) {
        const ready=await battleScrollTargetIntoViewportAsync(
          element,
          'battle-lot-'+String(slot||''),
          runId
        );
        return ready ? element : null;
      }

      const host=battleScrollHost();
      if (!host) return null;
      const isWindowHost=host===document.scrollingElement || host===document.documentElement || host===document.body;
      const max=Math.max(0,(isWindowHost?document.documentElement.scrollHeight:host.scrollHeight)-
        (isWindowHost?window.innerHeight:host.clientHeight));
      const original=isWindowHost ? window.scrollY : host.scrollTop;
      const row=Math.max(0,Math.min(BATTLE_ROWS-1,Math.floor((Number(slot)-BATTLE_FIRST_SLOT)/BATTLE_COLS)));
      const preferred=max*(row/Math.max(1,BATTLE_ROWS-1));
      const positions=[preferred,max*0.34,max*0.67,max,0];

      for (const position of positions) {
        if (runId!==battleAutoRunId || !battleAutoEnabled()) return null;
        try {
          if (isWindowHost) window.scrollTo(0,Math.max(0,position));
          else host.scrollTop=Math.max(0,position);
        } catch (_) {}
        await battleNextPaint();
        await new Promise(resolve=>setTimeout(resolve,90));
        element=battleFindLotElement(lotId);
        if (element) {
          const ready=await battleScrollTargetIntoViewportAsync(
            element,
            'battle-mounted-'+String(slot||''),
            runId
          );
          recordDiagnostic('battle-target-auto-mounted',{
            revision:HK_BATTLE_TARGET_SCROLL_REV,
            lotId,
            slot:Number(slot)||0,
            scrollPosition:Math.round(position),
            ready
          });
          if (ready) return element;
        }
      }

      try {
        if (isWindowHost) window.scrollTo(0,original);
        else host.scrollTop=original;
      } catch (_) {}
      return null;
    }

    async function battleEnsureElementForSlot(slot,runId) {
      const row=getBattleBoard()[Number(slot)-BATTLE_FIRST_SLOT];
      const lotId=String(row?.lotId||'');
      let element=battleElementForSlot(slot);
      if (element) {
        const ready=await battleScrollTargetIntoViewportAsync(
          element,
          'battle-enemy-slot-'+String(slot),
          runId
        );
        if (ready) return element;
      }
      if (!lotId) return null;
      return await battleEnsureLotElement(lotId,slot,runId);
    }
'''
rep(old_ensure,new_ensure,"ensure selected enemy visible and unoccluded")

# Make the attack runner explicitly assert the selected card is still hit-ready
# after the scroll settles, before opening it.
old_runner=r'''        const expectedCost=battleCostForElement(element);
        const before=getSignature();

        // Mobile Safari/game handlers are not guaranteed to react to a raw
'''
new_runner=r'''        const expectedCost=battleCostForElement(element);
        const targetProbe=battleElementTapProbe(element);
        if (!targetProbe.ready || !battleTargetSafeBand(element)) {
          recordDiagnostic('battle-auto-stop',{
            revision:HK_BATTLE_TARGET_SCROLL_REV,
            reason:'target-not-safe-after-scroll',
            slot,
            expectedCost,
            probeReason:targetProbe.reason,
            blockerTag:targetProbe.leafTag||'',
            blockerText:targetProbe.leafText||''
          });
          return false;
        }
        const before=getSignature();

        // Mobile Safari/game handlers are not guaranteed to react to a raw
'''
rep(old_runner,new_runner,"runner safe target assertion")

export_anchor="      battleEggBerryRevision:HK_BATTLE_EGG_BERRY_REV,"
rep(
    export_anchor,
    export_anchor+"\n      battleTargetScrollRevision:HK_BATTLE_TARGET_SCROLL_REV,",
    "debug export"
)

for marker in [
    "// @version      1.18.80",
    "const BUILD_VERSION = '1.18.80';",
    "battle-target-safe-scroll-20260928-r1",
    "function battlePointBelongsToElement",
    "function battleElementTapProbe",
    "function battleTargetSafeBand",
    "async function battleScrollTargetIntoViewportAsync",
    "battle-target-safe-scroll",
    "await battleScrollTargetIntoViewportAsync(",
    "reason:'target-not-safe-after-scroll'",
    "verifiedTarget:true",
    "battleTargetScrollRevision:HK_BATTLE_TARGET_SCROLL_REV",
    "battle-full-fair-state-20260928-r1",
    "battle-egg-one-berry-buy-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

if "battle-native-offscreen-click" in s:
    raise SystemExit("unsafe native offscreen click fallback still present")

p.write_text(s,encoding="utf-8")
print("BATTLE_SAFE_SCROLL_1_18_80=PASS")
