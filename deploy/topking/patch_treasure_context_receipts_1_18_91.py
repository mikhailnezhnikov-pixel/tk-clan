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

rep("// @version      1.18.90",
    "// @version      1.18.91\n// @release-note Карта сокровищ: исправлены ложные состояния боя на Сокровищнице/готовой карте; окна полученного ключа теперь всегда подтверждаются как чек, а не повторно трактуются как покупка; левый коридор Сокровищницы имеет собственный hard-gate «Понятно».",
    "version")
rep("const BUILD_VERSION = '1.18.90';",
    "const BUILD_VERSION = '1.18.91';",
    "build")

rev_anchor="  const HK_COORDINATE_OVERLAY_GUARD_REV='coordinate-overlay-guard-20260929-r1';"
rep(rev_anchor,
    rev_anchor+"\n  const HK_BATTLE_CONTEXT_FOREGROUND_REV='battle-context-foreground-20260929-r1';\n  const HK_KEY_RECEIPT_PRIORITY_REV='treasure-key-receipt-priority-20260929-r1';\n  const HK_TREASURY_CORRIDOR_ACK_REV='treasury-corridor-ack-20260929-r1';\n  const HK_MAP_DOMINANCE_REV='treasure-map-dominates-stale-minigame-20260929-r1';",
    "revisions")

# --- Battle intro must belong to the current visible battle room, not stale DOM.
anchor="    function battleIntroModalRootLegacy() {"
helper=r'''    function battleScreenVisiblyCurrent() {
      // The page-title bar is wide; the small navbar "Сражение" label is not.
      const rows=[...document.querySelectorAll('h1,h2,h3,[role="heading"],header,div,span')]
        .filter(visible)
        .map(element=>({
          element,
          text:clean(element.innerText||element.textContent||'').trim(),
          rect:element.getBoundingClientRect?.() || {left:0,top:0,width:0,height:0}
        }))
        .filter(row=>/^(?:Сражение|Battle)$/i.test(row.text))
        .filter(row=>
          row.rect.width>=window.innerWidth*0.30 &&
          row.rect.height>=28 &&
          row.rect.top>=0 &&
          row.rect.top<=window.innerHeight*0.72
        )
        .filter(row=>autoMapElementIsForeground(row.element));
      return rows.length>0;
    }

    function battleIntroOwnTitle(root) {
      if (!root) return false;
      const exact=/^(?:Сражение|Battle)$/i;
      const direct=clean(root.firstElementChild?.innerText||root.firstElementChild?.textContent||'').trim();
      if (exact.test(direct)) return true;
      return [...root.querySelectorAll('h1,h2,h3,[role="heading"],strong,b,div,span')]
        .filter(visible)
        .some(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const rect=element.getBoundingClientRect?.();
          return exact.test(text) && rect && rect.width>40 && rect.height>16;
        });
    }

'''
if s.count(anchor)!=1: raise SystemExit("battle intro anchor missing")
s=s.replace(anchor,helper+anchor,1)

old_legacy=r'''          if (!/(?:^|\s)(?:Сражение|Battle)(?:\s|$)/i.test(text)) return false;
          if (/Сундук победителя|Victory chest|Winner chest/i.test(text)) return false;
'''
new_legacy=r'''          if (!battleIntroOwnTitle(element)) return false;
          if (!battleScreenVisiblyCurrent()) return false;
          if (/Сундук победителя|Victory chest|Winner chest/i.test(text)) return false;
'''
rep(old_legacy,new_legacy,"battle legacy current-screen gate")

old_fallback=r'''      const exactAck=/^(?:Понятно|Got it|Understood|OK|Okay)$/i;
      let battleContext=battleRawContextPresent();
      try { battleContext=battleContext || !!battleFairState(); } catch (_) {}
      if (!battleContext) return null;
'''
new_fallback=r'''      const exactAck=/^(?:Понятно|Got it|Understood|OK|Okay)$/i;
      // Exact visible battle title contract: Сражение|Battle.
      // Stale battle lots remain mounted while Treasury/Lights/Map are current.
      // Never classify a generic "Понятно" as battle unless the visible page
      // itself is the battle room.
      if (!battleScreenVisiblyCurrent()) return null;
      let battleContext=battleRawContextPresent();
      try { battleContext=battleContext || !!battleFairState(); } catch (_) {}
      if (!battleContext) return null;
'''
rep(old_fallback,new_fallback,"battle fallback current-screen gate")

# --- Key receipt always wins over any purchase-button heuristic.
rep("""      if (initialAck && !initialTarget?.element) {
        return await autoMapAcknowledgeTreasureKey(root,'already-received');
      }
""",
"""      if (initialAck) {
        autoMapStatus('ключ · подтверждаю',{
          revision:HK_KEY_RECEIPT_PRIORITY_REV,
          source:'already-received'
        });
        return await autoMapAcknowledgeTreasureKey(root,'already-received');
      }
""","key initial receipt priority")

rep("""          if (ack && !purchase?.element) {
            recordDiagnostic('treasure-key-receipt-visible',{
              revision:HK_TREASURE_KEY_ACK_REV,
              cost
            });
            return await autoMapAcknowledgeTreasureKey(root,'after-purchase');
          }
""",
"""          if (ack) {
            autoMapStatus('ключ · подтверждаю',{
              revision:HK_KEY_RECEIPT_PRIORITY_REV,
              source:'after-purchase',
              cost
            });
            recordDiagnostic('treasure-key-receipt-visible',{
              revision:HK_KEY_RECEIPT_PRIORITY_REV,
              cost,
              purchaseHeuristic:!!purchase?.element
            });
            return await autoMapAcknowledgeTreasureKey(root,'after-purchase');
          }
""","key postpurchase receipt priority")

# --- Treasury corridor result/ack is its own modal state, ahead of battle intro.
treasury_anchor="    function autoMapTreasuryChestRows() {"
treasury_helper=r'''    function autoMapTreasuryCorridorModalRoot() {
      if (!autoMapTreasuryScreenVisible()) return null;
      const title=/(?:Левый|Средний|Правый)s+коридор|(?:Left|Middle|Right)s+corridor/i;
      const rows=[...document.querySelectorAll('[role="dialog"],[aria-modal="true"],[class*="modal"],[class*="popup"],[class*="dialog"],div')]
        .filter(visible)
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const rect=element.getBoundingClientRect?.() || {width:0,height:0};
          const ack=[...element.querySelectorAll('button,[role="button"],a,[onclick],div,span')]
            .find(child=>/^(?:Понятно|Got it|Understood|OK|Okay)$/i.test(clean(child.innerText||child.textContent||'').trim()) && visible(child));
          return {element,text,rect,ack,area:rect.width*rect.height};
        })
        .filter(row=>title.test(row.text) && row.ack)
        .filter(row=>row.rect.width>=Math.min(240,window.innerWidth*0.35) && row.rect.height>=140)
        .sort((a,b)=>a.area-b.area);
      return rows[0]?.element || null;
    }

    async function autoMapAcknowledgeTreasuryCorridor() {
      const root=autoMapTreasuryCorridorModalRoot();
      if (!autoMapEnabled() || !root) return false;
      const ack=[...root.querySelectorAll('button,[role="button"],a,[onclick],div,span')]
        .filter(element=>element && !element.disabled && visible(element))
        .find(element=>/^(?:Понятно|Got it|Understood|OK|Okay)$/i.test(clean(element.innerText||element.textContent||'').trim()));
      if (!ack) return false;

      autoMapStatus('treasury → понятно',{
        revision:HK_TREASURY_CORRIDOR_ACK_REV
      });
      await autoMapWaitActionGap();
      if (!autoMapEnabled()) return false;

      const accepted=()=>!autoMapTreasuryCorridorModalRoot();
      let ok=false;
      try {
        ok=await deviceNeutralActivate(
          ack,
          'treasury-corridor-ack',
          accepted,
          1600
        );
      } catch (_) {}
      if (!ok && ack.isConnected) {
        const rect=ack.getBoundingClientRect?.();
        if (rect && rect.width>0 && rect.height>0) {
          const sent=dispatchMinigameOverlaySafeTapAt(
            rect.left+rect.width/2,
            rect.top+rect.height/2,
            'treasury-corridor-ack-center'
          );
          if (sent) ok=await waitDeviceNeutralCondition(accepted,1600,70);
        }
      }

      recordDiagnostic('treasury-corridor-acknowledged',{
        revision:HK_TREASURY_CORRIDOR_ACK_REV,
        success:!!ok
      });
      if (ok) {
        autoMapRetryNotBefore=0;
        lastSignature='';
        setTimeout(()=>void runAutoMapTick('treasury-corridor-acked'),160);
      }
      return !!ok;
    }

'''
if s.count(treasury_anchor)!=1: raise SystemExit("treasury helper anchor missing")
s=s.replace(treasury_anchor,treasury_helper+treasury_anchor,1)

# Insert treasury corridor preflight before battle preview/intro.
preflight_anchor="      const openBattlePreview=autoMapBattlePreviewRoot();"
preflight=r'''      const treasuryCorridorModal=autoMapTreasuryCorridorModalRoot();
      if (treasuryCorridorModal) {
        autoMapRunning=true;
        const treasuryAckRunId=autoMapRunId;
        try {
          const ok=await autoMapAcknowledgeTreasuryCorridor();
          if (!ok) setTimeout(()=>void runAutoMapTick('treasury-corridor-ack-retry'),320);
          return ok;
        } finally {
          if (treasuryAckRunId===autoMapRunId) autoMapRunning=false;
        }
      }

'''
if s.count(preflight_anchor)!=1: raise SystemExit("preflight anchor missing")
s=s.replace(preflight_anchor,preflight+preflight_anchor,1)

# --- Real map/current-journey screen outranks stale battle/lights DOM.
get_anchor="    function getSignature() {\n"
get_insert=r'''    function getSignature() {
      const realMapForeground=autoMapMapIsForeground();
      const completedMapForeground=!!(
        treasureGuideScreenVisible() &&
        autoMapJourneyButton() &&
        autoMapElementIsForeground(autoMapJourneyButton())
      );
      if (realMapForeground || completedMapForeground) {
        return 'NONE';
      }
'''
rep(get_anchor,get_insert,"map dominance signature")

# When map dominates stale battle DOM, clear stale battle claim memory/status too.
map_pre=r'''      if (treasureGuideScreenVisible() && !autoMapMiniGameForeground() && !treasureModalRoot(null)) {
        const mapReady=autoMapTxnMarkMapVisible('tick-preflight');
'''
map_new=r'''      const completedMapButtonPreflight=treasureGuideScreenVisible()?autoMapJourneyButton():null;
      if (treasureGuideScreenVisible() && (autoMapMapIsForeground() || !!completedMapButtonPreflight) && !treasureModalRoot(null)) {
        if (!battleScreenVisiblyCurrent()) {
          battleIntroGateUntil=0;
          if (battleAutoRunning) {
            battleAutoRunId+=1;
            battleAutoRunning=false;
          }
          battleFinalRewardClaimed=false;
          battleFinalRewardClaimedAt=0;
        }
      }

      if (treasureGuideScreenVisible() && !autoMapMiniGameForeground() && !treasureModalRoot(null)) {
        const mapReady=autoMapTxnMarkMapVisible('tick-preflight');
'''
rep(map_pre,map_new,"map stale battle reset")

# Export.
export_anchor="      coordinateOverlayGuardRevision:HK_COORDINATE_OVERLAY_GUARD_REV,"
rep(export_anchor,
    export_anchor+"\n      battleContextForegroundRevision:HK_BATTLE_CONTEXT_FOREGROUND_REV,\n      keyReceiptPriorityRevision:HK_KEY_RECEIPT_PRIORITY_REV,\n      treasuryCorridorAckRevision:HK_TREASURY_CORRIDOR_ACK_REV,\n      mapDominanceRevision:HK_MAP_DOMINANCE_REV,",
    "exports")

for marker in [
    "// @version      1.18.91",
    "battle-context-foreground-20260929-r1",
    "treasure-key-receipt-priority-20260929-r1",
    "treasury-corridor-ack-20260929-r1",
    "treasure-map-dominates-stale-minigame-20260929-r1",
    "function battleScreenVisiblyCurrent()",
    "function autoMapTreasuryCorridorModalRoot()",
    "function autoMapAcknowledgeTreasuryCorridor()",
    "if (initialAck)",
    "if (realMapForeground || completedMapForeground)",
    "automation-toggle-trusted-input-20260929-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

p.write_text(s,encoding="utf-8")
print("TREASURE_CONTEXT_RECEIPTS_1_18_91=PASS")
