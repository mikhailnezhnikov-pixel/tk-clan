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

rep("// @version      1.18.88",
    "// @version      1.18.89\n// @release-note Автокарта: после возврата на карту введено окно тишины — новая ячейка не нажимается, пока карта не постоит без модалок 1.4 секунды. Зависшие окна (включая яйцо торговца) закрываются по внешней оболочке модалки и подтверждённому исчезновению.",
    "version")
rep("const BUILD_VERSION = '1.18.88';",
    "const BUILD_VERSION = '1.18.89';",
    "build")

rev_anchor="  const HK_BATTLE_OFFSCREEN_ACTION_REV='battle-offscreen-action-scroll-20260929-r1';"
rep(rev_anchor,
    rev_anchor+"\n  const HK_MAP_QUIET_GATE_REV='treasure-map-quiet-gate-20260929-r1';\n  const HK_STALE_MODAL_SHELL_CLOSE_REV='stale-modal-shell-close-20260929-r1';",
    "revisions")

# Quiet gate state.
rep("    const AUTO_MAP_MAX_ACTIONS=240;",
    "    const AUTO_MAP_MAX_ACTIONS=240;\n    const AUTO_MAP_QUIET_MS=1400;",
    "quiet constant")

rep("    let autoMapTxn={phase:'IDLE',lotId:'',label:'',updatedAt:Date.now()};",
    "    let autoMapTxn={phase:'IDLE',lotId:'',label:'',updatedAt:Date.now()};\n    let autoMapMapQuietSince=0;",
    "quiet state")

# Reset quiet timer when a new cell is selected / transaction leaves the map.
old_txn=r'''      autoMapTxn={
        phase:next,
        lotId:String(data.lotId ?? previous?.lotId ?? ''),
        label:String(data.label ?? previous?.label ?? ''),
        updatedAt:Date.now()
      };
'''
new_txn=r'''      autoMapTxn={
        phase:next,
        lotId:String(data.lotId ?? previous?.lotId ?? ''),
        label:String(data.label ?? previous?.label ?? ''),
        updatedAt:Date.now()
      };
      if (['TARGET_FOUND','CARD_OPENED','ACTION_CONFIRMED','SERVER_UI_STATE_CHANGED','ROOM_COMPLETE','EXIT_CONFIRMED'].includes(next)) {
        autoMapMapQuietSince=0;
      }
'''
rep(old_txn,new_txn,"quiet reset by txn")

old_mark=r'''    function autoMapTxnMarkMapVisible(source='map-visible') {
      if (!treasureGuideScreenVisible()) return false;
      if (autoMapMiniGameForeground()) return false;
      if (treasureModalRoot(null)) return false;
      autoMapTxnSet('MAP_VISIBLE',{source,lotId:'',label:''});
      return true;
    }
'''
new_mark=r'''    function autoMapTxnMarkMapVisible(source='map-visible') {
      if (!treasureGuideScreenVisible()) {
        autoMapMapQuietSince=0;
        return false;
      }
      if (autoMapMiniGameForeground()) {
        autoMapMapQuietSince=0;
        return false;
      }
      if (treasureModalRoot(null)) {
        autoMapMapQuietSince=0;
        return false;
      }

      const now=Date.now();
      if (!autoMapMapQuietSince) {
        autoMapMapQuietSince=now;
        autoMapStatus('карта · жду окна',{
          revision:HK_MAP_QUIET_GATE_REV,
          quietMs:AUTO_MAP_QUIET_MS
        });
        recordDiagnostic('treasure-map-quiet-start',{
          revision:HK_MAP_QUIET_GATE_REV,
          source,
          quietMs:AUTO_MAP_QUIET_MS
        });
        return false;
      }

      const quietFor=now-autoMapMapQuietSince;
      if (quietFor<AUTO_MAP_QUIET_MS) {
        autoMapStatus('карта · стабилизация',{
          revision:HK_MAP_QUIET_GATE_REV,
          quietFor,
          remainingMs:AUTO_MAP_QUIET_MS-quietFor
        });
        return false;
      }

      autoMapTxnSet('MAP_VISIBLE',{source,lotId:'',label:'',quietFor});
      recordDiagnostic('treasure-map-quiet-complete',{
        revision:HK_MAP_QUIET_GATE_REV,
        source,
        quietFor
      });
      return true;
    }
'''
rep(old_mark,new_mark,"map quiet mark")

# Improve stale modal close by finding the shell that actually owns the X.
old_close=r'''    async function autoMapCloseLingeringModal(reason='stale-modal') {
      if (autoMapMiniGameForeground()) return false;
      const root=treasureModalRoot(null);
      if (!root) return false;
      let close=autoMapModalCloseButton(root);
      let tapped=false;
      if (close) {
        tapped=dispatchAutoMapTap(close,'close-'+reason);
      } else {
        const rr=root.getBoundingClientRect?.();
        if (rr && rr.width>0 && rr.height>0) {
          tapped=dispatchMinigameOverlaySafeTapAt(
            rr.right-Math.max(18,Math.min(30,rr.width*0.05)),
            rr.top+Math.max(18,Math.min(30,rr.height*0.06)),
            'close-corner-'+reason
          );
        }
      }
      if (!tapped) {
        autoMapStatus('жду окно',{reason});
        return false;
      }

      autoMapLastActionAt=Date.now();
      recordDiagnostic('treasure-auto-map-modal-close',{
        revision:HK_STALE_MODAL_HARD_GATE_REV,
        reason
      });

      const started=Date.now();
      while (Date.now()-started<2600) {
        if (!autoMapEnabled()) return false;
        const current=treasureModalRoot(null);
        if (!current || current!==root) {
          recordDiagnostic('treasure-stale-modal-hard-gate-clear',{
            revision:HK_STALE_MODAL_HARD_GATE_REV,
            reason,
            elapsedMs:Date.now()-started
          });
          return true;
        }
        await new Promise(resolve=>setTimeout(resolve,90));
      }

      autoMapStatus('жду закрытие окна',{reason});
      recordDiagnostic('treasure-stale-modal-hard-gate-block',{
        revision:HK_STALE_MODAL_HARD_GATE_REV,
        reason
      });
      return false;
    }
'''
new_close=r'''    function autoMapModalShell(root) {
      if (!root) return {root:null,close:null};
      const vw=Math.max(1,window.innerWidth), vh=Math.max(1,window.innerHeight);
      const rows=[];
      let node=root;
      for (let depth=0;node && depth<10;depth++,node=node.parentElement) {
        if (!visible(node)) continue;
        const rect=node.getBoundingClientRect?.();
        if (!rect || rect.width<220 || rect.height<140) continue;
        if (rect.width>vw*0.99 || rect.height>vh*0.98) continue;
        const close=autoMapModalCloseButton(node);
        rows.push({root:node,close,rect,depth,area:rect.width*rect.height});
      }
      const withClose=rows.filter(row=>row.close)
        .sort((a,b)=>b.depth-a.depth || b.area-a.area)[0];
      if (withClose) return withClose;
      const outer=rows.sort((a,b)=>b.area-a.area)[0];
      return outer || {root,close:null};
    }

    async function autoMapCloseLingeringModal(reason='stale-modal') {
      if (autoMapMiniGameForeground()) return false;
      const inner=treasureModalRoot(null);
      if (!inner) return false;

      autoMapMapQuietSince=0;
      const shellInfo=autoMapModalShell(inner);
      const root=shellInfo.root || inner;
      let close=shellInfo.close || autoMapModalCloseButton(root);
      const accepted=()=> {
        const current=treasureModalRoot(null);
        return !current || !visible(current);
      };

      let ok=false;
      if (close) {
        try {
          ok=await deviceNeutralActivate(
            close,
            'stale-modal-shell-close-'+reason,
            accepted,
            1500
          );
        } catch (_) {}
        if (!ok && close.isConnected) {
          const sent=dispatchMinigameOverlaySafeTapAt(
            close.getBoundingClientRect().left+close.getBoundingClientRect().width/2,
            close.getBoundingClientRect().top+close.getBoundingClientRect().height/2,
            'stale-modal-close-safe-'+reason
          );
          if (sent) {
            try { ok=await waitDeviceNeutralCondition(accepted,1500,70); } catch (_) {}
          }
        }
      }

      if (!ok && root?.isConnected) {
        const rr=root.getBoundingClientRect?.();
        if (rr && rr.width>0 && rr.height>0) {
          for (const fx of [0.965,0.94,0.91]) {
            const x=rr.left+rr.width*fx;
            const y=rr.top+Math.max(18,Math.min(34,rr.height*0.055));
            const sent=dispatchMinigameOverlaySafeTapAt(
              x,y,'stale-modal-shell-corner-'+String(fx)+'-'+reason
            );
            if (sent) {
              try { ok=await waitDeviceNeutralCondition(accepted,900,70); } catch (_) {}
              if (ok) break;
            }
          }
        }
      }

      if (!ok) {
        autoMapStatus('жду закрытие окна',{
          reason,
          revision:HK_STALE_MODAL_SHELL_CLOSE_REV
        });
        recordDiagnostic('treasure-stale-modal-hard-gate-block',{
          revision:HK_STALE_MODAL_SHELL_CLOSE_REV,
          reason,
          hasClose:!!close
        });
        return false;
      }

      autoMapLastActionAt=Date.now();
      autoMapMapQuietSince=0;
      recordDiagnostic('treasure-stale-modal-hard-gate-clear',{
        revision:HK_STALE_MODAL_SHELL_CLOSE_REV,
        reason,
        hasClose:!!close
      });
      return true;
    }
'''
rep(old_close,new_close,"stale shell close")

# In preflight, do not mark the map visible and then immediately continue.
old_pre=r'''      if (treasureGuideScreenVisible() && !autoMapMiniGameForeground() && !treasureModalRoot(null)) {
        autoMapTxnMarkMapVisible('tick-preflight');
      }

      if (Date.now()<autoMapRetryNotBefore) {
'''
new_pre=r'''      if (treasureGuideScreenVisible() && !autoMapMiniGameForeground() && !treasureModalRoot(null)) {
        const mapReady=autoMapTxnMarkMapVisible('tick-preflight');
        if (!mapReady) {
          setTimeout(()=>void runAutoMapTick('map-quiet-gate'),180);
          return false;
        }
      }

      if (Date.now()<autoMapRetryNotBefore) {
'''
rep(old_pre,new_pre,"quiet preflight stop")

# Export revisions.
export_anchor="      battleOffscreenActionRevision:HK_BATTLE_OFFSCREEN_ACTION_REV,"
rep(export_anchor,
    export_anchor+"\n      mapQuietGateRevision:HK_MAP_QUIET_GATE_REV,\n      staleModalShellCloseRevision:HK_STALE_MODAL_SHELL_CLOSE_REV,",
    "export revisions")

for marker in [
    "// @version      1.18.89",
    "treasure-map-quiet-gate-20260929-r1",
    "stale-modal-shell-close-20260929-r1",
    "const AUTO_MAP_QUIET_MS=1400",
    "autoMapMapQuietSince",
    "function autoMapModalShell(root)",
    "deviceNeutralActivate(",
    "stale-modal-shell-corner-",
    "setTimeout(()=>void runAutoMapTick('map-quiet-gate'),180)",
    "treasure-transaction-gate-20260929-r1",
    "chest-lot-hard-gate-20260929-r1",
    "battle-offscreen-action-scroll-20260929-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

p.write_text(s,encoding="utf-8")
print("MAP_QUIET_STALE_MODAL_1_18_89=PASS")
