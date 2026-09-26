from pathlib import Path
import sys

target=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=target.read_text(encoding="utf-8")

def need(old,label,count=1):
    actual=s.count(old)
    if actual!=count:
        raise SystemExit(f"{label}: expected {count}, got {actual}")

def rep(old,new,label,count=1):
    global s
    need(old,label,count)
    s=s.replace(old,new,count)

rep(
    "// @version      1.18.08",
    "// @version      1.18.09\n"
    "// @release-note Мини-игры: Тайный торговец получил последовательный автовыкуп всех доступных лотов с приоритетом карт/монет/ягод и защитой от повторной покупки. Рыбалка больше не выбирает уже «Активировано», ждёт сервер между покупками и переживает временные 409/500 через reconcile/backoff вместо мгновенного отключения.",
    "version"
)
rep("const BUILD_VERSION = '1.18.08';","const BUILD_VERSION = '1.18.09';","build")

rep(
    "  const HK_FISHING_CANON_REV = 'fishing-canon-priority-20260926-r2';",
    "  const HK_FISHING_CANON_REV = 'fishing-canon-priority-20260926-r2';\n"
    "  const HK_FISHING_STABILITY_REV = 'fishing-activated-backoff-20260926-r1';\n"
    "  const HK_TRADER_AUTO_REV = 'secret-trader-auto-buy-20260926-r1';\n"
    "  const HK_MINIGAME_HTTP_BACKOFF_REV = 'minigame-http-409-500-backoff-20260926-r1';",
    "stability markers"
)

# Observe native game 409/5xx responses without making any extra game requests.
rep(
    """      const response = await nativeFetch(input, init);
      const path = url ? new URL(url, location.href).pathname : '';
      if (path === '/auth/create' && response.ok) {
""",
    """      const response = await nativeFetch(input, init);
      const path = url ? new URL(url, location.href).pathname : '';
      if (!response.ok && (response.status===409 || response.status>=500) &&
          (path.startsWith('/fair/') || path==='/shop/buy')) {
        window.__HK_MINIGAME_HTTP_ERROR__={
          revision:HK_MINIGAME_HTTP_BACKOFF_REV,
          status:Number(response.status||0),
          path,
          at:Date.now()
        };
        recordDiagnostic('minigame-http-error',window.__HK_MINIGAME_HTTP_ERROR__);
      }
      if (path === '/auth/create' && response.ok) {
""",
    "fetch minigame status observer"
)

rep(
    """        this.addEventListener('load', () => {
          if (this.status >= 200 && this.status < 300) {
""",
    """        this.addEventListener('load', () => {
          try {
            const hkPath=new URL(this.__hkUrl,location.href).pathname;
            if ((this.status===409 || this.status>=500) &&
                (hkPath.startsWith('/fair/') || hkPath==='/shop/buy')) {
              window.__HK_MINIGAME_HTTP_ERROR__={
                revision:HK_MINIGAME_HTTP_BACKOFF_REV,
                status:Number(this.status||0),
                path:hkPath,
                at:Date.now()
              };
              recordDiagnostic('minigame-http-error',window.__HK_MINIGAME_HTTP_ERROR__);
            }
          } catch (_) {}
          if (this.status >= 200 && this.status < 300) {
""",
    "xhr minigame status observer"
)

# Extend puzzle-solver state.
rep(
    """    const FISHING_AUTO_STORAGE_KEY = 'hk:fishing:auto-click:v1';
    const FISHING_ACTION_TIMEOUT_MS = 4200;
    let fishingAutoRunning = false;
    let fishingAutoRunId = 0;
    let fishingAutoToggle = null;
""",
    """    const FISHING_AUTO_STORAGE_KEY = 'hk:fishing:auto-click:v1';
    const FISHING_ACTION_TIMEOUT_MS = 5200;
    const FISHING_MIN_NEXT_ACTION_GAP_MS = 1800;
    const FISHING_RECONCILE_WAIT_MS = 2800;
    let fishingAutoRunning = false;
    let fishingAutoRunId = 0;
    let fishingAutoToggle = null;
    let fishingLastMutationAt = 0;
    let fishingRetryNotBefore = 0;
    let fishingFailureStreak = 0;

    const TRADER_AUTO_STORAGE_KEY = 'hk:trader:auto-buy:v1';
    const TRADER_ACTION_TIMEOUT_MS = 5200;
    const TRADER_MIN_NEXT_ACTION_GAP_MS = 1800;
    const TRADER_MAX_PURCHASES_PER_VISIT = 40;
    let traderAutoRunning = false;
    let traderAutoRunId = 0;
    let traderAutoToggle = null;
    let traderLastMutationAt = 0;
    let traderRetryNotBefore = 0;
    let traderFailureStreak = 0;
    let traderSessionPurchases = 0;
""",
    "trader/fishing state"
)

# Generic minigame HTTP/backoff helpers.
anchor="""    function fishingAutoEnabled() {
"""
helpers="""    function minigameRecentHttpError(since=0,windowMs=8000) {
      const error=window.__HK_MINIGAME_HTTP_ERROR__;
      if (!error || !Number(error.at)) return null;
      if (Number(error.at)<Number(since||0)-300) return null;
      if (Date.now()-Number(error.at)>windowMs) return null;
      return error;
    }

    function minigameBackoffMs(error,streak=0) {
      const status=Number(error?.status||0);
      if (status>=500) return Math.min(10000,5000+Math.max(0,streak)*1200);
      if (status===409) return Math.min(7000,2800+Math.max(0,streak)*800);
      return Math.min(8000,1800+Math.max(0,streak)*900);
    }

    async function waitMutationGap(lastAt,gapMs) {
      const wait=Math.max(0,Number(lastAt||0)+Number(gapMs||0)-Date.now());
      if (wait>0) await new Promise(resolve=>setTimeout(resolve,wait));
    }

    function clearMinigameHttpError() {
      try { window.__HK_MINIGAME_HTTP_ERROR__=null; } catch (_) {}
    }

"""
need(anchor,"fishing auto anchor")
s=s.replace(anchor,helpers+anchor,1)

# Activated cells are state, never a new fishing target.
old_elements="""    function fishingElements() {
      return [...document.querySelectorAll('[data-lot-id*="mf_treasurelot_is_fishing_"]')]
        .filter(visible)
        .map((element,index)=>({
          element,
          index,
          lotId:String(element.getAttribute('data-lot-id')||'')
        }))
        .filter(row=>row.lotId);
    }
"""
new_elements="""    function fishingElements() {
      return [...document.querySelectorAll('[data-lot-id*="mf_treasurelot_is_fishing_"]')]
        .filter(visible)
        .map((element,index)=>{
          const lotId=String(element.getAttribute('data-lot-id')||'');
          const text=clean(element.innerText||element.textContent||'');
          const activated=/активировано|activated|куплено|purchased|получено|taken/i.test(text);
          return {element,index,lotId,text,activated};
        })
        .filter(row=>row.lotId);
    }
"""
rep(old_elements,new_elements,"fishing activated detection")

rep(
    """      const source=fishingElements();
      const hasCurseTrigger=source.some(row=>/is_fishing_cursed_water$/.test(row.lotId));
      const rows=source.map(row=>{
""",
    """      const source=fishingElements();
      const hasCurseTrigger=source.some(row=>!row.activated && /is_fishing_cursed_water$/.test(row.lotId));
      const rows=source.filter(row=>!row.activated).map(row=>{
""",
    "fishing target excludes activated"
)

rep(
    """    function fishingSignature() {
      return 'FISHING|'+fishingElements()
        .map(row=>row.lotId+'#'+clean(row.element.className||''))
        .join('|');
    }
""",
    """    function fishingSignature() {
      return 'FISHING|'+fishingElements()
        .map(row=>row.lotId+'#'+(row.activated?'1':'0')+'#'+row.text+'#'+clean(row.element.className||''))
        .join('|');
    }

    function fishingTargetResolved(target) {
      if (!target?.element?.isConnected) return true;
      const current=fishingElements().find(row=>row.element===target.element);
      return !current || !!current.activated;
    }
""",
    "fishing signature activated state"
)

# Replace hard-disable with safe retry/backoff; only repeated structural failures eventually disable.
old_fail="""    function failFishingAuto(reason,data={}) {
      try { localStorage.setItem(FISHING_AUTO_STORAGE_KEY,'0'); } catch (_) {}
      fishingAutoRunId+=1;
      fishingAutoRunning=false;
      updateFishingAutoToggle();
      recordDiagnostic('fishing-auto-stop',{revision:HK_FISHING_AUTO_REV,reason,...data});
      return false;
    }
"""
new_fail="""    function failFishingAuto(reason,data={}) {
      const error=minigameRecentHttpError(data?.startedAt||0);
      const transient=!!error || ['field-no-change','modal-missing','action-missing'].includes(String(reason||''));
      fishingFailureStreak+=1;
      const backoff=minigameBackoffMs(error,fishingFailureStreak);
      fishingRetryNotBefore=Date.now()+backoff;

      recordDiagnostic('fishing-auto-backoff',{
        revision:HK_FISHING_STABILITY_REV,
        reason,
        transient,
        streak:fishingFailureStreak,
        backoffMs:backoff,
        httpStatus:Number(error?.status||0)||null,
        ...data
      });

      if (!transient && fishingFailureStreak>=4) {
        try { localStorage.setItem(FISHING_AUTO_STORAGE_KEY,'0'); } catch (_) {}
        fishingAutoRunId+=1;
        fishingAutoRunning=false;
        updateFishingAutoToggle();
        recordDiagnostic('fishing-auto-stop',{
          revision:HK_FISHING_STABILITY_REV,
          reason:'repeated-structural-failure',
          streak:fishingFailureStreak
        });
      }
      return false;
    }
"""
rep(old_fail,new_fail,"fishing safe backoff")

# Fishing start respects backoff/pacing and clears stale error.
rep(
    """    async function runFishingAuto() {
      if (!fishingAutoEnabled() || fishingAutoRunning || battleAutoRunning || chestAutoRunning || lightsAutoRunning) return false;
      const target=fishingTarget();
      if (!target) return false;

      fishingAutoRunning=true;
      const runId=++fishingAutoRunId;
      const before=fishingSignature();
""",
    """    async function runFishingAuto() {
      if (!fishingAutoEnabled() || fishingAutoRunning || battleAutoRunning || chestAutoRunning || lightsAutoRunning || traderAutoRunning) return false;
      if (Date.now()<fishingRetryNotBefore) {
        setTimeout(checkPuzzle,Math.max(200,fishingRetryNotBefore-Date.now()+40));
        return false;
      }
      const target=fishingTarget();
      if (!target) return false;

      await waitMutationGap(fishingLastMutationAt,FISHING_MIN_NEXT_ACTION_GAP_MS);
      if (!fishingAutoEnabled()) return false;

      fishingAutoRunning=true;
      const runId=++fishingAutoRunId;
      const before=fishingSignature();
      const startedAt=Date.now();
      clearMinigameHttpError();
""",
    "fishing pace start"
)

rep(
    """        if (!dispatchBattleTap(target.element,'fishing-open-'+target.lotId)) {
          return failFishingAuto('target-tap-failed',{lotId:target.lotId});
        }
""",
    """        if (!dispatchBattleTap(target.element,'fishing-open-'+target.lotId)) {
          return failFishingAuto('target-tap-failed',{lotId:target.lotId,startedAt});
        }
        fishingLastMutationAt=Date.now();
""",
    "fishing initial mutation timestamp"
)

# Direct success gets a server-settle gap and resets failure streak.
rep(
    """            const rewards=await dismissFishingRewards(runId);
            recordDiagnostic('fishing-auto-complete',{
              revision:HK_FISHING_CANON_REV,
              lotId:target.lotId,
              mode:'direct',
              rewardsDismissed:rewards
            });
            return true;
""",
    """            const rewards=await dismissFishingRewards(runId);
            fishingFailureStreak=0;
            fishingRetryNotBefore=0;
            await waitMutationGap(fishingLastMutationAt,FISHING_MIN_NEXT_ACTION_GAP_MS);
            recordDiagnostic('fishing-auto-complete',{
              revision:HK_FISHING_STABILITY_REV,
              lotId:target.lotId,
              mode:'direct',
              rewardsDismissed:rewards
            });
            return true;
""",
    "fishing direct settle"
)

rep(
    """        if (!modal) return failFishingAuto('modal-missing',{lotId:target.lotId});
""",
    """        if (!modal) {
          await new Promise(resolve=>setTimeout(resolve,FISHING_RECONCILE_WAIT_MS));
          if (fishingTargetResolved(target)) {
            fishingFailureStreak=0;
            fishingRetryNotBefore=0;
            return true;
          }
          return failFishingAuto('modal-missing',{lotId:target.lotId,startedAt});
        }
""",
    "fishing modal reconcile"
)

rep(
    """        if (!action || !dispatchBattleTap(action,'fishing-confirm-'+target.lotId)) {
          return failFishingAuto('action-missing',{lotId:target.lotId,cost:target.cost});
        }

        const changed=await waitFishingChange(before,runId);
""",
    """        if (!action || !dispatchBattleTap(action,'fishing-confirm-'+target.lotId)) {
          return failFishingAuto('action-missing',{lotId:target.lotId,cost:target.cost,startedAt});
        }
        fishingLastMutationAt=Date.now();

        const changed=await waitFishingChange(before,runId);
""",
    "fishing confirm timestamp"
)

rep(
    """        if (!changed && rewards===0) {
          return failFishingAuto('field-no-change',{lotId:target.lotId});
        }

        recordDiagnostic('fishing-auto-complete',{
          revision:HK_FISHING_CANON_REV,
""",
    """        if (!changed && rewards===0) {
          await new Promise(resolve=>setTimeout(resolve,FISHING_RECONCILE_WAIT_MS));
          if (!fishingTargetResolved(target)) {
            return failFishingAuto('field-no-change',{lotId:target.lotId,startedAt});
          }
        }

        fishingFailureStreak=0;
        fishingRetryNotBefore=0;
        await waitMutationGap(fishingLastMutationAt,FISHING_MIN_NEXT_ACTION_GAP_MS);
        recordDiagnostic('fishing-auto-complete',{
          revision:HK_FISHING_STABILITY_REV,
""",
    "fishing field reconcile"
)

# Finalizer honors backoff instead of hammering every 300 ms.
rep(
    """      } finally {
        if (runId===fishingAutoRunId) fishingAutoRunning=false;
        lastSignature='';
        setTimeout(checkPuzzle,300);
      }
    }

    function lightsBoardSignature(board = null) {
""",
    """      } finally {
        if (runId===fishingAutoRunId) fishingAutoRunning=false;
        lastSignature='';
        const delay=Math.max(300,fishingRetryNotBefore-Date.now()+40);
        setTimeout(checkPuzzle,delay);
      }
    }

    // ----- Secret trader: buy all available offers sequentially -----
    function traderAutoEnabled() {
      try {
        const saved=localStorage.getItem(TRADER_AUTO_STORAGE_KEY);
        return saved===null ? true : saved==='1';
      } catch (_) { return true; }
    }

    function updateTraderAutoToggle(isTrader=null) {
      if (!traderAutoToggle) return;
      const enabled=traderAutoEnabled();
      traderAutoToggle.textContent=enabled ? either('Автоторговец: ВКЛ','Auto trader: ON') : either('Автоторговец: ВЫКЛ','Auto trader: OFF');
      traderAutoToggle.style.background=enabled ? '#40c85a' : '#2b2b2b';
      traderAutoToggle.style.color=enabled ? '#071b0a' : '#fff';
      if (isTrader!==null) traderAutoToggle.style.display=isTrader?'block':'none';
    }

    function setTraderAutoEnabled(enabled) {
      const value=!!enabled;
      try { localStorage.setItem(TRADER_AUTO_STORAGE_KEY,value?'1':'0'); } catch (_) {}
      if (!value) {
        traderAutoRunId+=1;
        traderAutoRunning=false;
      } else {
        traderFailureStreak=0;
        traderRetryNotBefore=0;
        lastSignature='';
        setTimeout(checkPuzzle,0);
      }
      updateTraderAutoToggle();
      recordDiagnostic('trader-auto-toggle',{revision:HK_TRADER_AUTO_REV,enabled:value});
      return value;
    }

    function ensureTraderAutoToggle(isTrader) {
      if (!traderAutoToggle) {
        traderAutoToggle=document.createElement('button');
        traderAutoToggle.id='hkTraderAutoToggle';
        traderAutoToggle.type='button';
        Object.assign(traderAutoToggle.style,{
          position:'fixed',
          right:'14px',
          bottom:'154px',
          zIndex:'2147483646',
          border:'2px solid rgba(255,255,255,.75)',
          borderRadius:'18px',
          padding:'8px 11px',
          fontSize:'12px',
          fontWeight:'900',
          lineHeight:'1',
          boxShadow:'0 4px 14px rgba(0,0,0,.55)',
          WebkitTapHighlightColor:'transparent',
          touchAction:'manipulation'
        });
        traderAutoToggle.addEventListener('click',event=>{
          event.preventDefault();
          event.stopPropagation();
          setTraderAutoEnabled(!traderAutoEnabled());
        },true);
        (document.body || document.documentElement)?.appendChild(traderAutoToggle);
      }
      updateTraderAutoToggle(!!isTrader);
    }

    function traderElements() {
      return [...document.querySelectorAll('[data-lot-id^="mf_fairlot_minigame_trader_"]')]
        .filter(visible)
        .map((element,index)=>{
          const lotId=String(element.getAttribute('data-lot-id')||'');
          const text=clean(element.innerText||element.textContent||'');
          const activated=/активировано|activated|куплено|purchased|получено|taken|выкуплено|sold\\s*out/i.test(text);
          return {element,index,lotId,text,activated};
        })
        .filter(row=>row.lotId && !/locked|empty/i.test(row.lotId));
    }

    function traderCatalogRow(lotId) {
      return fairCatalog.find(item=>String(item?.lotId||'')===String(lotId||'')) || null;
    }

    function traderCost(row) {
      const catalogRow=traderCatalogRow(row?.lotId);
      const rawCost=catalogRow?.cost || null;
      const parts=costParts(rawCost).filter(part=>part.quantity>0);
      return {
        raw:rawCost,
        primary:parts.length===1 ? {id:parts[0].id,quantity:parts[0].quantity} : null,
        parts
      };
    }

    function traderAffordable(cost) {
      if (!cost?.parts?.length) return true;
      for (const part of cost.parts) {
        const amount=walletAmount(part.id);
        if (amount!==null && amount<part.quantity) return false;
      }
      return true;
    }

    function traderValueTier(lotId) {
      const id=String(lotId||'').toLowerCase();
      if (/map/.test(id)) return 1200;
      if (/coins/.test(id)) return 1100;
      if (/food|berry|berries|energy/.test(id)) return 1000;
      if (/gold/.test(id)) return 900;
      if (/pet_skill|rod|sword/.test(id)) return 800;
      if (/fish_egg/.test(id)) return 700;
      return 600;
    }

    function traderTarget() {
      const rows=traderElements()
        .filter(row=>!row.activated)
        .map(row=>{
          const cost=traderCost(row);
          return {...row,cost,tier:traderValueTier(row.lotId)};
        })
        .filter(row=>traderAffordable(row.cost));

      rows.sort((a,b)=>
        b.tier-a.tier ||
        (a.cost.primary?.quantity||999999)-(b.cost.primary?.quantity||999999) ||
        a.index-b.index
      );
      return rows[0] || null;
    }

    function traderSignature() {
      return 'TRADER|'+traderElements()
        .map(row=>row.lotId+'#'+(row.activated?'1':'0')+'#'+row.text+'#'+clean(row.element.className||''))
        .join('|');
    }

    function traderTargetResolved(target) {
      if (!target?.element?.isConnected) return true;
      const current=traderElements().find(row=>row.element===target.element);
      return !current || !!current.activated || current.lotId!==target.lotId;
    }

    async function waitTraderChange(before,target,runId,timeoutMs=TRADER_ACTION_TIMEOUT_MS) {
      const started=Date.now();
      while (Date.now()-started<timeoutMs) {
        if (runId!==traderAutoRunId || !traderAutoEnabled()) return false;
        if (traderSignature()!==before || traderTargetResolved(target)) return true;
        await new Promise(resolve=>setTimeout(resolve,100));
      }
      return false;
    }

    function traderBackoff(reason,data={}) {
      const error=minigameRecentHttpError(data?.startedAt||0);
      traderFailureStreak+=1;
      const backoff=minigameBackoffMs(error,traderFailureStreak);
      traderRetryNotBefore=Date.now()+backoff;
      recordDiagnostic('trader-auto-backoff',{
        revision:HK_TRADER_AUTO_REV,
        reason,
        streak:traderFailureStreak,
        backoffMs:backoff,
        httpStatus:Number(error?.status||0)||null,
        ...data
      });
      return false;
    }

    async function runTraderAuto() {
      if (!traderAutoEnabled() || traderAutoRunning || fishingAutoRunning || battleAutoRunning || chestAutoRunning || lightsAutoRunning) return false;
      if (Date.now()<traderRetryNotBefore) {
        setTimeout(checkPuzzle,Math.max(200,traderRetryNotBefore-Date.now()+40));
        return false;
      }
      if (traderSessionPurchases>=TRADER_MAX_PURCHASES_PER_VISIT) {
        recordDiagnostic('trader-auto-stop',{
          revision:HK_TRADER_AUTO_REV,
          reason:'visit-purchase-limit',
          purchases:traderSessionPurchases
        });
        return false;
      }

      const target=traderTarget();
      if (!target) {
        recordDiagnostic('trader-auto-complete',{
          revision:HK_TRADER_AUTO_REV,
          purchases:traderSessionPurchases,
          reason:'no-affordable-lots'
        });
        return false;
      }

      await waitMutationGap(traderLastMutationAt,TRADER_MIN_NEXT_ACTION_GAP_MS);
      if (!traderAutoEnabled()) return false;

      traderAutoRunning=true;
      const runId=++traderAutoRunId;
      const before=traderSignature();
      const startedAt=Date.now();
      clearMinigameHttpError();

      recordDiagnostic('trader-auto-start',{
        revision:HK_TRADER_AUTO_REV,
        lotId:target.lotId,
        cost:target.cost.parts,
        tier:target.tier,
        purchaseIndex:traderSessionPurchases+1
      });

      try {
        if (!dispatchBattleTap(target.element,'trader-open-'+target.lotId)) {
          return traderBackoff('target-tap-failed',{lotId:target.lotId,startedAt});
        }
        traderLastMutationAt=Date.now();

        // Some trader lots execute directly; most open the standard lot modal.
        const directStarted=Date.now();
        while (Date.now()-directStarted<750) {
          if (runId!==traderAutoRunId || !traderAutoEnabled()) return false;
          if (traderSignature()!==before || traderTargetResolved(target)) {
            traderSessionPurchases+=1;
            traderFailureStreak=0;
            traderRetryNotBefore=0;
            await dismissTreasureRewards(runId);
            await waitMutationGap(traderLastMutationAt,TRADER_MIN_NEXT_ACTION_GAP_MS);
            recordDiagnostic('trader-auto-purchase',{
              revision:HK_TRADER_AUTO_REV,
              lotId:target.lotId,
              mode:'direct',
              purchases:traderSessionPurchases
            });
            return true;
          }
          await new Promise(resolve=>setTimeout(resolve,80));
        }

        const modal=await (async()=>{
          const started=Date.now();
          while (Date.now()-started<2400) {
            if (runId!==traderAutoRunId || !traderAutoEnabled()) return null;
            const root=treasureModalRoot(target.cost.primary);
            if (root) return root;
            await new Promise(resolve=>setTimeout(resolve,80));
          }
          return null;
        })();

        if (!modal) {
          await new Promise(resolve=>setTimeout(resolve,2200));
          if (traderTargetResolved(target)) {
            traderSessionPurchases+=1;
            traderFailureStreak=0;
            traderRetryNotBefore=0;
            return true;
          }
          try { target.element.dataset.hkTraderSkip='1'; } catch (_) {}
          return traderBackoff('modal-missing',{lotId:target.lotId,startedAt});
        }

        const action=await (async()=>{
          const started=Date.now();
          while (Date.now()-started<2000) {
            if (runId!==traderAutoRunId || !traderAutoEnabled()) return null;
            const button=treasureActionButton(modal,target.cost.primary);
            if (button) return button;
            await new Promise(resolve=>setTimeout(resolve,80));
          }
          return null;
        })();

        if (!action || !dispatchBattleTap(action,'trader-confirm-'+target.lotId)) {
          try { target.element.dataset.hkTraderSkip='1'; } catch (_) {}
          return traderBackoff('action-missing',{lotId:target.lotId,cost:target.cost.parts,startedAt});
        }
        traderLastMutationAt=Date.now();

        const changed=await waitTraderChange(before,target,runId);
        await new Promise(resolve=>setTimeout(resolve,240));
        const rewards=await dismissTreasureRewards(runId);

        if (!changed && rewards===0) {
          await new Promise(resolve=>setTimeout(resolve,2600));
          if (!traderTargetResolved(target)) {
            return traderBackoff('field-no-change',{lotId:target.lotId,startedAt});
          }
        }

        traderSessionPurchases+=1;
        traderFailureStreak=0;
        traderRetryNotBefore=0;
        if (target.cost.raw) debitWallet(target.cost.raw,1);
        await waitMutationGap(traderLastMutationAt,TRADER_MIN_NEXT_ACTION_GAP_MS);

        recordDiagnostic('trader-auto-purchase',{
          revision:HK_TRADER_AUTO_REV,
          lotId:target.lotId,
          cost:target.cost.parts,
          rewardsDismissed:rewards,
          purchases:traderSessionPurchases
        });
        return true;
      } finally {
        if (runId===traderAutoRunId) traderAutoRunning=false;
        lastSignature='';
        const delay=Math.max(350,traderRetryNotBefore-Date.now()+40);
        setTimeout(checkPuzzle,delay);
      }
    }

    function lightsBoardSignature(board = null) {
""",
    "fishing finalizer + trader auto"
)

# Exclude locally skipped trader card until React refreshes it.
rep(
    """.filter(row=>row.lotId && !/locked|empty/i.test(row.lotId));
    }
""",
    """.filter(row=>row.lotId && !/locked|empty/i.test(row.lotId))
        .filter(row=>row.element?.dataset?.hkTraderSkip!=='1');
    }
""",
    "trader skip marker"
)

# Detect trader context before chests.
rep(
    """      const fishingRows=fishingElements();
      if (fishingRows.length>=3) return fishingSignature();

      const chestRows=treasureChestElements();
""",
    """      const fishingRows=fishingElements();
      if (fishingRows.length>=3) return fishingSignature();

      const traderRows=traderElements();
      if (traderRows.length>=1) return traderSignature();

      const chestRows=treasureChestElements();
""",
    "trader signature detection"
)

# Add trader context to checkPuzzle and keep per-visit counter scoped to page.
rep(
    """      const isFishing=signature.startsWith('FISHING|');
      const isChests=signature.startsWith('CHESTS|');
      const battleContext=isBattle || isBattleReward || !!document.querySelector('[data-lot-id^="mf_treasurelot_sword_"]');
      ensureBattleAutoToggle(battleContext);
      ensureChestAutoToggle(isChests);
      ensureLightsAutoToggle(isLights);
      ensureFishingAutoToggle(isFishing);
      if (battleAutoRunning || chestAutoRunning || lightsAutoRunning || fishingAutoRunning) return;
""",
    """      const isFishing=signature.startsWith('FISHING|');
      const isTrader=signature.startsWith('TRADER|');
      const isChests=signature.startsWith('CHESTS|');
      const battleContext=isBattle || isBattleReward || !!document.querySelector('[data-lot-id^="mf_treasurelot_sword_"]');
      ensureBattleAutoToggle(battleContext);
      ensureChestAutoToggle(isChests);
      ensureLightsAutoToggle(isLights);
      ensureFishingAutoToggle(isFishing);
      ensureTraderAutoToggle(isTrader);
      if (!isTrader) traderSessionPurchases=0;
      if (battleAutoRunning || chestAutoRunning || lightsAutoRunning || fishingAutoRunning || traderAutoRunning) return;
""",
    "trader check context"
)

rep(
    """      if (isBattleReward && battleAutoEnabled()) { void runBattleVictoryClaim(); return; }
      if (isFishing && fishingAutoEnabled()) { void runFishingAuto(); return; }
      if (isChests && chestAutoEnabled()) void runTreasureChestAuto();
""",
    """      if (isBattleReward && battleAutoEnabled()) { void runBattleVictoryClaim(); return; }
      if (isFishing && fishingAutoEnabled()) { void runFishingAuto(); return; }
      if (isTrader && traderAutoEnabled()) { void runTraderAuto(); return; }
      if (isChests && chestAutoEnabled()) void runTreasureChestAuto();
""",
    "trader auto dispatch"
)

# Stop/export trader cleanly.
rep(
    """      fishingAutoRunId += 1;
      fishingAutoRunning = false;
      clearNumbers();
      try { battleAutoToggle?.remove(); } catch (_) {}
      try { chestAutoToggle?.remove(); } catch (_) {}
      try { lightsAutoToggle?.remove(); } catch (_) {}
      try { fishingAutoToggle?.remove(); } catch (_) {}
      battleAutoToggle = null;
      chestAutoToggle = null;
      lightsAutoToggle = null;
      fishingAutoToggle = null;
""",
    """      fishingAutoRunId += 1;
      fishingAutoRunning = false;
      traderAutoRunId += 1;
      traderAutoRunning = false;
      clearNumbers();
      try { battleAutoToggle?.remove(); } catch (_) {}
      try { chestAutoToggle?.remove(); } catch (_) {}
      try { lightsAutoToggle?.remove(); } catch (_) {}
      try { fishingAutoToggle?.remove(); } catch (_) {}
      try { traderAutoToggle?.remove(); } catch (_) {}
      battleAutoToggle = null;
      chestAutoToggle = null;
      lightsAutoToggle = null;
      fishingAutoToggle = null;
      traderAutoToggle = null;
""",
    "trader stop state"
)

rep(
    """      fishingAutoRevision:HK_FISHING_AUTO_REV,
      start,
""",
    """      fishingAutoRevision:HK_FISHING_AUTO_REV,
      fishingStabilityRevision:HK_FISHING_STABILITY_REV,
      traderAutoRevision:HK_TRADER_AUTO_REV,
      start,
""",
    "trader export revisions"
)

rep(
    """      get autoFishingEnabled(){return fishingAutoEnabled();},
      setAutoFishingEnabled:setFishingAutoEnabled,
      get running(){return intervalId !== null;}
""",
    """      get autoFishingEnabled(){return fishingAutoEnabled();},
      setAutoFishingEnabled:setFishingAutoEnabled,
      get autoTraderEnabled(){return traderAutoEnabled();},
      setAutoTraderEnabled:setTraderAutoEnabled,
      get running(){return intervalId !== null;}
""",
    "trader export controls"
)

for marker in [
    "// @version      1.18.09",
    "const BUILD_VERSION = '1.18.09';",
    "fishing-activated-backoff-20260926-r1",
    "secret-trader-auto-buy-20260926-r1",
    "minigame-http-409-500-backoff-20260926-r1",
    "активировано|activated",
    "FISHING_MIN_NEXT_ACTION_GAP_MS = 1800",
    "fishingRetryNotBefore",
    "fishingTargetResolved",
    "Автоторговец: ВКЛ",
    "TRADER_MIN_NEXT_ACTION_GAP_MS = 1800",
    "TRADER_MAX_PURCHASES_PER_VISIT = 40",
    "mf_fairlot_minigame_trader_",
    "traderValueTier",
    "trader-auto-purchase",
    "TRADER|",
    "response.status===409 || response.status>=500",
    "this.status===409 || this.status>=500",
    "fishing-canon-priority-20260926-r2",
    "minigame-flow-fixes-20260926-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

target.write_text(s,encoding="utf-8")
print("TRADER_FISHING_STABILITY_1_18_09=PASS")
