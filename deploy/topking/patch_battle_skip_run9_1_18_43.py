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

rep("// @version      1.18.42",
    "// @version      1.18.43\n// @release-note Сражение/Автокарта: по записи #9 сражения теперь пропускаются без проведения боя. После входа в комнату HK закрывает стартовое «Понятно», нажимает «Покинуть локацию», подтверждает стоимость 10 и ждёт возврата на Карту сокровищ. Пока Автокарта включена, боевой решатель не делает ни одного удара.",
    "version")
rep("const BUILD_VERSION = '1.18.42';",
    "const BUILD_VERSION = '1.18.43';",
    "build")
rep("  const HK_TREASURE_EVENT_UI_SCOPE_REV = 'treasure-event-ui-scope-20260927-r1';",
    "  const HK_TREASURE_EVENT_UI_SCOPE_REV = 'treasure-event-ui-scope-20260927-r1';\n  const HK_BATTLE_SKIP_CANON_REV = 'battle-skip-run9-20260927-r1';",
    "revision")

# Do not let checkPuzzle launch attacks while AutoMap owns the room.
old_runbattle="""    function runBattle() {
      const maxAttack = getBattleAttack();
"""
new_runbattle="""    function runBattle() {
      if (autoMapEnabled()) {
        recordDiagnostic('battle-auto-skip-owned-by-map',{
          revision:HK_BATTLE_SKIP_CANON_REV
        });
        setTimeout(()=>void runAutoMapTick('battle-skip-owned-by-map'),20);
        return true;
      }

      const maxAttack = getBattleAttack();
"""
rep(old_runbattle,new_runbattle,"battle owned by automap")

# Add exact intro acknowledgement and canonical leave flow before generic exit handler.
anchor="""    function autoMapCurrentModuleComplete() {
      const signature=getSignature();
"""
helper="""    function battleIntroAcknowledgeButton() {
      const exact=/^(?:Понятно|Got it|Understood|OK|Okay)$/i;
      const rows=[...document.querySelectorAll('button,[role="button"],a,[onclick],div,span')]
        .filter(element=>element && !element.disabled && visible(element))
        .map(element=>({
          element,
          text:clean(element.innerText||element.textContent||'').trim(),
          rect:element.getBoundingClientRect?.()
        }))
        .filter(row=>exact.test(row.text))
        .filter(row=>row.rect && row.rect.width>0 && row.rect.height>0)
        .sort((a,b)=>a.rect.width*a.rect.height-b.rect.width*b.rect.height);
      return rows[0]?.element || null;
    }

    async function autoMapSkipBattleWithoutFight() {
      if (!autoMapEnabled()) return false;
      const signature=getSignature();
      if (!signature.startsWith('BATTLE')) return false;

      // Record #9 canonical sequence:
      // enter battle -> acknowledge intro -> Leave location -> confirm 10 -> map.
      const ack=battleIntroAcknowledgeButton();
      if (ack) {
        autoMapStatus('сражение → пропуск',{
          revision:HK_BATTLE_SKIP_CANON_REV,
          step:'ack'
        });
        dispatchAutoMapTap(ack,'battle-skip-intro-ack');
        autoMapLastActionAt=Date.now();
        await new Promise(resolve=>setTimeout(resolve,260));
      }

      if (!autoMapEnabled()) return false;

      let exit=autoMapExitButton();
      if (!exit) {
        const started=Date.now();
        while (Date.now()-started<1800) {
          if (!autoMapEnabled()) return false;
          exit=autoMapExitButton();
          if (exit) break;
          await new Promise(resolve=>setTimeout(resolve,80));
        }
      }

      if (!exit) {
        autoMapRetryNotBefore=Date.now()+700;
        autoMapStatus('сражение → жду выход',{
          revision:HK_BATTLE_SKIP_CANON_REV
        });
        setTimeout(()=>void runAutoMapTick('battle-skip-exit-retry'),780);
        return false;
      }

      autoMapStatus('сражение → выход',{
        revision:HK_BATTLE_SKIP_CANON_REV
      });

      const left=await autoMapTapAndConfirm(exit,'battle-skip-leave-location',10);
      if (!left) {
        autoMapRetryNotBefore=Math.max(autoMapRetryNotBefore,Date.now()+700);
        setTimeout(()=>void runAutoMapTick('battle-skip-confirm-retry'),820);
        return false;
      }

      const waitStarted=Date.now();
      while (Date.now()-waitStarted<4200) {
        if (!autoMapEnabled()) return false;
        if (treasureGuideScreenVisible() && !getSignature().startsWith('BATTLE')) {
          autoMapCurrentLot='';
          autoMapReturnNotBefore=Date.now()+300;
          lastSignature='';
          recordDiagnostic('battle-skip-complete',{
            revision:HK_BATTLE_SKIP_CANON_REV,
            result:'returned-to-map'
          });
          setTimeout(()=>{
            checkPuzzle();
            void runAutoMapTick('battle-skip-map-visible');
          },360);
          return true;
        }
        await new Promise(resolve=>setTimeout(resolve,90));
      }

      recordDiagnostic('battle-skip-complete',{
        revision:HK_BATTLE_SKIP_CANON_REV,
        result:'action-confirmed-waiting-map'
      });
      return true;
    }

"""
if s.count(anchor)!=1:
    raise SystemExit("autoMapCurrentModuleComplete anchor missing")
s=s.replace(anchor,helper+anchor,1)

old_battle_branch="""        if (signature.startsWith('BATTLE')) {
          // Battle module owns the room. It may leave the location itself when
          // the full-clear guard proves that the remaining swords cannot clear all mobs.
          // AutoMap must not press the persistent exit button independently.
          autoMapReturnNotBefore=Date.now()+AUTO_MAP_RETURN_SETTLE_MS;
          autoMapStatus('сражение');
          lastSignature='';
          setTimeout(checkPuzzle,20);
          return true;
        }
"""
new_battle_branch="""        if (signature.startsWith('BATTLE')) {
          // Canon from recording #9: do not perform any fight while AutoMap owns
          // the room. Acknowledge the intro, leave the location, pay 10, resume map.
          if (battleAutoRunning) {
            battleAutoRunId+=1;
            battleAutoRunning=false;
            recordDiagnostic('battle-auto-cancel-for-skip',{
              revision:HK_BATTLE_SKIP_CANON_REV
            });
          }
          return await autoMapSkipBattleWithoutFight();
        }
"""
rep(old_battle_branch,new_battle_branch,"automap battle skip branch")

# checkPuzzle should never call runBattle attacks when AutoMap is active.
old_check="""      if (isBattle) {
        runBattle();
        return;
      }
"""
new_check="""      if (isBattle) {
        if (autoMapEnabled()) {
          recordDiagnostic('battle-skip-dispatch',{
            revision:HK_BATTLE_SKIP_CANON_REV
          });
          setTimeout(()=>void runAutoMapTick('battle-skip-check-puzzle'),20);
          return;
        }
        runBattle();
        return;
      }
"""
rep(old_check,new_check,"checkPuzzle battle skip")

rep("      treasureEventUiScopeRevision:HK_TREASURE_EVENT_UI_SCOPE_REV,\n      start,",
    "      treasureEventUiScopeRevision:HK_TREASURE_EVENT_UI_SCOPE_REV,\n      battleSkipCanonRevision:HK_BATTLE_SKIP_CANON_REV,\n      start,",
    "export battle skip revision")

for marker in [
    "// @version      1.18.43",
    "const BUILD_VERSION = '1.18.43';",
    "battle-skip-run9-20260927-r1",
    "function battleIntroAcknowledgeButton()",
    "async function autoMapSkipBattleWithoutFight()",
    "battle-skip-intro-ack",
    "battle-skip-leave-location",
    "battle-skip-complete",
    "battle-auto-cancel-for-skip",
    "battle-skip-dispatch",
    "trader-exit-handoff-20260927-r1",
    "treasure-event-ui-scope-20260927-r1"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("BATTLE_SKIP_RUN9_1_18_43=PASS")
