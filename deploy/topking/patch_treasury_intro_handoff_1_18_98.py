from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

def rep(old,new,label,count=1):
    global s
    actual=s.count(old)
    if actual!=count:
        raise SystemExit(f"{label}: expected {count} anchors, got {actual}")
    s=s.replace(old,new,count)

def insert_before(anchor,body,label):
    rep(anchor,body+anchor,label)

rep("// @version      1.18.97",
    "// @version      1.18.98\n// @release-note Сокровищница: восстановление вступительного окна с пустой кнопкой на мобильных, перенос индикатора автокарты с кнопки, подтверждение входа до выбора пути. Смена комнаты сбрасывает устаревший бой и прекращает повторные попытки выхода из уже покинутого сражения.",
    "version")
rep("const BUILD_VERSION = '1.18.97';",
    "const BUILD_VERSION = '1.18.98';",
    "build")
rev="  const HK_EXIT_MAP_PROOF_REV='exit-map-proof-20261001-r1';"
rep(rev,rev+"\n  const HK_TREASURY_INTRO_REV='treasury-intro-mobile-ack-20261001-r1';\n  const HK_TREASURY_BATTLE_HANDOFF_REV='treasury-battle-foreground-handoff-20261001-r1';",
    "revisions")

insert_before("    function autoMapTreasuryCorridorModalRoot() {",
r'''    function autoMapTreasuryForeground() {
      if (battleScreenVisiblyCurrent()) return false;
      return [...document.querySelectorAll('h1,h2,h3,[role="heading"],header,div,span')]
        .filter(visible)
        .filter(element=>/^(?:Сокровищница|Treasury)$/i.test(
          clean(element.innerText||element.textContent||'').trim()
        ))
        .some(autoMapElementIsForeground);
    }

    function autoMapTreasuryIntroAction(root) {
      if (!root) return null;
      const rr=root.getBoundingClientRect?.();
      if (!rr || rr.width<=0 || rr.height<=0) return null;
      const cx=rr.left+rr.width/2;
      const candidates=[...root.querySelectorAll('button,[role="button"],a,[onclick],div,span')]
        .filter(element=>
          element && element!==root && element!==autoMapToggle &&
          element.isConnected && !element.disabled &&
          element.getAttribute?.('aria-disabled')!=='true' && visible(element)
        )
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const rect=element.getBoundingClientRect?.() ||
            {left:0,top:0,width:0,height:0};
          let interactive=false,blocked=false;
          try {
            const style=getComputedStyle(element);
            blocked=style.pointerEvents==='none';
            interactive=element.matches?.('button,[role="button"],a,[onclick]') ||
              !!element.onclick || style.cursor==='pointer';
          } catch (_) {}
          if (blocked || !interactive) return null;
          if (/(?:Закрыть|Close|Назад|Back|×|✕)/i.test(text)) return null;
          if (rect.top<rr.top+rr.height*0.55 ||
              rect.width<rr.width*0.30 || rect.width>rr.width*0.93 ||
              rect.height<30 || rect.height>rr.height*0.26 ||
              Math.abs(rect.left+rect.width/2-cx)>rr.width*0.22) return null;
          const area=rect.width*rect.height;
          const score=
            (element.matches?.('button,[role="button"],a')?180:0) +
            (/(?:Понятно|Продолжить|Войти|Открыть|Got it|Continue|Enter|Open)/i.test(text)?100:0) +
            (rect.top>=rr.top+rr.height*0.62?90:0) +
            (text.length<=30?50:0);
          return {element,score,area};
        })
        .filter(Boolean)
        .sort((a,b)=>b.score-a.score || a.area-b.area);
      return candidates[0]?.element || null;
    }

    function autoMapTreasuryIntroModalRoot() {
      if (!autoMapTreasuryForeground()) return null;
      const vw=Math.max(1,window.innerWidth);
      const vh=Math.max(1,window.innerHeight);
      const rows=[...document.querySelectorAll(
        '[role="dialog"],[aria-modal="true"],[class*="modal"],[class*="popup"],[class*="dialog"],div'
      )]
        .filter(visible)
        .map(element=>{
          const rect=element.getBoundingClientRect?.();
          if (!rect || rect.width<Math.min(220,vw*0.35) || rect.height<180 ||
              rect.width>vw*0.94 || rect.height>vh*0.88) return null;
          const cx=rect.left+rect.width/2;
          const cy=rect.top+rect.height/2;
          if (Math.abs(cx-vw/2)>vw*0.24 ||
              Math.abs(cy-vh/2)>vh*0.27) return null;
          const text=clean(element.innerText||element.textContent||'').trim();
          if (/(?:Левый|Средний|Правый)\s+коридор|(?:Left|Middle|Right)\s+corridor|Сундук\s+победителя|Victory\s+chest/i.test(text)) return null;
          const title=[...element.querySelectorAll('h1,h2,h3,[role="heading"],strong,b,div,span')]
            .filter(visible)
            .find(child=>
              child!==element &&
              /^(?:Сокровищница|Treasury)$/i.test(
                clean(child.innerText||child.textContent||'').trim()
              ) &&
              child.getBoundingClientRect?.().top<=rect.top+rect.height*0.64
            );
          if (!title) return null;
          const foreground=[0.43,0.72].some(y=>{
            const top=battleElementFromPointIgnoringOverlays(
              cx,rect.top+rect.height*y,null
            );
            return !!top && (top===element || element.contains(top));
          });
          if (!foreground) return null;
          return {element,area:rect.width*rect.height,action:!!autoMapTreasuryIntroAction(element)};
        })
        .filter(Boolean)
        .sort((a,b)=>Number(b.action)-Number(a.action) || a.area-b.area);
      return rows[0]?.element || null;
    }

    async function autoMapAcknowledgeTreasuryIntro(source='treasury-intro') {
      if (!autoMapEnabled()) return false;
      const root=autoMapTreasuryIntroModalRoot();
      if (!root) return false;
      const action=autoMapTreasuryIntroAction(root);
      if (!action) {
        autoMapStatus('сокровищница → жду кнопку',{
          revision:HK_TREASURY_INTRO_REV,source
        });
        recordDiagnostic('treasury-intro-action-missing',{
          revision:HK_TREASURY_INTRO_REV,
          source
        });
        setTimeout(()=>void runAutoMapTick('treasury-intro-button-retry'),650);
        return false;
      }

      autoMapStatus('сокровищница → подтверждаю вход',{
        revision:HK_TREASURY_INTRO_REV,source
      });
      await autoMapWaitActionGap();
      if (!autoMapEnabled() || !root.isConnected) return false;
      const accepted=()=>!autoMapTreasuryIntroModalRoot();
      const rect=action.getBoundingClientRect?.();
      recordDiagnostic('treasury-intro-confirm-target',{
        revision:HK_TREASURY_INTRO_REV,source,
        text:clean(action.innerText||action.textContent||'').slice(0,50),
        left:Math.round(rect?.left||0),top:Math.round(rect?.top||0),
        width:Math.round(rect?.width||0),height:Math.round(rect?.height||0)
      });
      autoMapLastActionAt=Date.now();
      let confirmed=false;
      try {
        confirmed=await deviceNeutralActivate(
          action,'treasury-intro-ack-'+source,accepted,1500
        );
      } catch (_) {}
      if (!confirmed && action.isConnected && rect?.width>0 && rect?.height>0) {
        const pointX=rect.left+rect.width/2;
        const pointY=rect.top+rect.height/2;
        const top=battleElementFromPointIgnoringOverlays(pointX,pointY,action);
        if (battlePointBelongsToElement(action,top)) {
          const sent=dispatchMinigameOverlaySafeTapAt(
            pointX,pointY,'treasury-intro-center-'+source
          );
          if (sent) confirmed=await waitDeviceNeutralCondition(accepted,1500,70);
        }
      }

      recordDiagnostic('treasury-intro-acknowledged',{
        revision:HK_TREASURY_INTRO_REV,source,success:!!confirmed
      });
      if (confirmed) {
        lastSignature='';
        autoMapRetryNotBefore=0;
        setTimeout(()=>void runAutoMapTick('treasury-intro-acknowledged'),200);
      } else {
        autoMapStatus('сокровищница → жду подтверждение',{
          revision:HK_TREASURY_INTRO_REV,source
        });
        setTimeout(()=>void runAutoMapTick('treasury-intro-ack-retry'),700);
      }
      return !!confirmed;
    }

''',"treasury mobile intro handlers")

# Stale battle reward/sword DOM must never overtake the foreground Treasury
# page, but a real visible battle heading still outranks a cached Treasury title.
rep("""      if (realMapForeground || completedMapForeground) {
        return 'NONE';
      }
      const lightsReward=lightsRewardElement();""",
    """      if (realMapForeground || completedMapForeground) {
        return 'NONE';
      }
      if (autoMapTreasuryForeground()) return 'NONE';
      const lightsReward=lightsRewardElement();""",
    "signature treasury priority")

# Existing battle exit coroutine may already be awaiting confirmation while
# the UI transitions to Treasury. Stop it on authoritative room handoff.
rep("""      const roomGone=()=>autoMapReturnMapConfirmed();
      const attempts=3;""",
    """      const roomGone=()=>autoMapReturnMapConfirmed();
      const treasuryHandoff=()=>autoMapTreasuryForeground();
      const handoff=()=>{
        if (!treasuryHandoff()) return false;
        battleFinalRewardClaimed=false;
        battleFinalRewardClaimedAt=0;
        autoMapRetryNotBefore=0;
        lastSignature='';
        autoMapStatus('сокровищница → вход',{
          revision:HK_TREASURY_BATTLE_HANDOFF_REV,source
        });
        recordDiagnostic('battle-exit-treasury-handoff',{
          revision:HK_TREASURY_BATTLE_HANDOFF_REV,source
        });
        setTimeout(()=>void runAutoMapTick('battle-handoff-treasury'),120);
        return true;
      };
      const attempts=3;""",
    "battle exit treasury handoff helper")
rep("""      for (let attempt=1;attempt<=attempts;attempt++) {
        if (!autoMapEnabled()) return false;
        if (roomGone()) {""",
    """      for (let attempt=1;attempt<=attempts;attempt++) {
        if (!autoMapEnabled()) return false;
        if (handoff()) return true;
        if (roomGone()) {""",
    "battle exit next attempt handoff")
rep("""          while (Date.now()<modalDeadline && autoMapEnabled()) {
            if (roomGone()) return true;""",
    """          while (Date.now()<modalDeadline && autoMapEnabled()) {
            if (handoff()) return true;
            if (roomGone()) return true;""",
    "battle exit waiting modal handoff")
rep("""        const leaveDeadline=Date.now()+3600;
        while (Date.now()<leaveDeadline && autoMapEnabled()) {
          if (roomGone()) {""",
    """        const leaveDeadline=Date.now()+3600;
        while (Date.now()<leaveDeadline && autoMapEnabled()) {
          if (handoff()) return true;
          if (roomGone()) {""",
    "battle exit waiting leave handoff")

# The visible HUD must not cover the blank/outlined bottom action of the
# Treasury popup. All other rooms keep the user's existing toggle position.
rep("""      if (autoMapToggle.style.display!==display) autoMapToggle.style.display=display;
      if (autoMapToggle.textContent!==label) autoMapToggle.textContent=label;""",
    """      const treasuryIntro=autoMapTreasuryIntroModalRoot();
      const hudBottom=treasuryIntro?'auto':'202px';
      const hudTop=treasuryIntro?'85px':'auto';
      if (autoMapToggle.style.bottom!==hudBottom) autoMapToggle.style.bottom=hudBottom;
      if (autoMapToggle.style.top!==hudTop) autoMapToggle.style.top=hudTop;
      if (autoMapToggle.style.display!==display) autoMapToggle.style.display=display;
      if (autoMapToggle.textContent!==label) autoMapToggle.textContent=label;""",
    "treasury HUD avoid button occlusion")

# Treasury gets ownership before the battle/reward preflight, even if the
# previous module left an async runner alive.
rep("""      const treasuryCorridorModal=autoMapTreasuryCorridorModalRoot();
      if (treasuryCorridorModal) {""",
    """      const treasuryForeground=autoMapTreasuryForeground();
      if (treasuryForeground) {
        const interrupted=autoMapCancelStaleRunners('treasury-foreground-handoff');
        if (battleFinalRewardClaimed || battleIntroGateUntil) {
          battleFinalRewardClaimed=false;
          battleFinalRewardClaimedAt=0;
          battleIntroGateUntil=0;
          lastSignature='';
        }
        if (interrupted.length) recordDiagnostic('treasury-foreground-handoff',{
          revision:HK_TREASURY_BATTLE_HANDOFF_REV,
          interrupted,source
        });
        const treasuryIntro=autoMapTreasuryIntroModalRoot();
        if (treasuryIntro) {
          autoMapRunning=true;
          const introRunId=autoMapRunId;
          try {
            return await autoMapAcknowledgeTreasuryIntro('tick-preflight');
          } finally {
            if (introRunId===autoMapRunId) autoMapRunning=false;
          }
        }
      }

      const treasuryCorridorModal=autoMapTreasuryCorridorModalRoot();
      if (treasuryCorridorModal) {""",
    "treasury foreground tick handoff before battle")

# A persistent Treasury intro must also force polling after a browser resume;
# do not wait for the stale battle signature to change.
rep("""    function checkPuzzle() {
      ensureAutoMapToggle();

      const forbiddenGoldModal=traderForbiddenGoldModalRoot();""",
    """    function checkPuzzle() {
      ensureAutoMapToggle();

      if (autoMapEnabled() && !autoMapRunning && autoMapTreasuryIntroModalRoot()) {
        void runAutoMapTick('treasury-intro-overlay');
        return;
      }

      const forbiddenGoldModal=traderForbiddenGoldModalRoot();""",
    "puzzle entry treasury intro dispatch")

# A Treasury page itself is not the map even if an old map heading remains
# mounted underneath it.
rep("""    function autoMapReturnMapConfirmed() {
      // The game may leave""",
    """    function autoMapReturnMapConfirmed() {
      if (autoMapTreasuryForeground()) return false;
      // The game may leave""",
    "map proof treasury guard")

revexport="      exitMapProofRevision:HK_EXIT_MAP_PROOF_REV,"
rep(revexport,revexport+"\n      treasuryIntroRevision:HK_TREASURY_INTRO_REV,\n      treasuryBattleHandoffRevision:HK_TREASURY_BATTLE_HANDOFF_REV,",
    "revision exports")

p.write_text(s,encoding='utf-8')
print("PATCH_TREASURY_INTRO_HANDOFF_1_18_98=PASS")
