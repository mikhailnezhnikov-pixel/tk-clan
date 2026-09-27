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

rep("// @version      1.18.46",
    "// @version      1.18.47\n// @release-note Автокарта теперь является владельцем дочерних автоматизаций на время прохождения. Если Автолампы/Автосундуки/Авторыбалка/Автоторговец сами выключились из-за временного UI-сбоя, Автокарта поднимет нужный модуль обратно и продолжит комнату. Для лампочек ошибки закрытия модалки переведены из фатальных в восстанавливаемые; математические ошибки плана по-прежнему блокируют повторные траты. Добавлен обязательный regression contract для уже исправленных этапов Карты сокровищ.",
    "version")
rep("const BUILD_VERSION = '1.18.46';",
    "const BUILD_VERSION = '1.18.47';",
    "build")
rep("  const HK_TREASURE_LOCATION_MODAL_ROOT_REV='treasure-location-modal-root-20260927-r1';",
    "  const HK_TREASURE_LOCATION_MODAL_ROOT_REV='treasure-location-modal-root-20260927-r1';\n  const HK_TREASURE_AUTOMAP_OWNERSHIP_REV='treasure-automap-module-ownership-20260927-r1';",
    "revision")

anchor="""    function autoMapCaptureModes() {
"""
ownership="""    function autoMapEnsureOwnedModule(signature=getSignature()) {
      if (!autoMapEnabled()) return false;

      const sig=String(signature||'');
      let name='';
      let enabled=null;
      let enable=null;

      if (sig.startsWith('LIGHTS|')) {
        name='lights';
        enabled=lightsAutoEnabled;
        enable=()=>setLightsAutoEnabled(true);
      } else if (sig.startsWith('CHESTS|')) {
        name='chests';
        enabled=chestAutoEnabled;
        enable=()=>setChestAutoEnabled(true);
      } else if (sig.startsWith('FISHING|')) {
        name='fishing';
        enabled=fishingAutoEnabled;
        enable=()=>setFishingAutoEnabled(true);
      } else if (sig.startsWith('TRADER|')) {
        name='trader';
        enabled=traderAutoEnabled;
        enable=()=>setTraderAutoEnabled(true);
      } else {
        return false;
      }

      const state=autoMapEnsureOwnedModule.state || (autoMapEnsureOwnedModule.state={
        rearmedAt:Object.create(null),
        blockedUntil:Object.create(null),
        blockReason:Object.create(null)
      });
      const now=Date.now();
      const blockedUntil=Number(state.blockedUntil[name]||0);
      if (blockedUntil>now) {
        autoMapStatus(name+' · защита',{
          revision:HK_TREASURE_AUTOMAP_OWNERSHIP_REV,
          module:name,
          reason:String(state.blockReason[name]||'hard-failure'),
          waitMs:blockedUntil-now
        });
        return false;
      }
      if (blockedUntil) {
        delete state.blockedUntil[name];
        delete state.blockReason[name];
      }

      if (enabled()) return false;

      const last=Number(state.rearmedAt[name]||0);
      if (now-last<1000) return false;
      state.rearmedAt[name]=now;

      enable();
      lastSignature='';
      recordDiagnostic('treasure-automap-module-rearm',{
        revision:HK_TREASURE_AUTOMAP_OWNERSHIP_REV,
        module:name,
        signature:sig.slice(0,180)
      });
      autoMapStatus(name+' · восстановление',{
        revision:HK_TREASURE_AUTOMAP_OWNERSHIP_REV,
        module:name
      });
      setTimeout(()=>{
        lastSignature='';
        checkPuzzle();
      },80);
      return true;
    }

    function autoMapBlockOwnedModule(name,reason,ms=30000) {
      const key=String(name||'');
      if (!key) return;
      const state=autoMapEnsureOwnedModule.state || (autoMapEnsureOwnedModule.state={
        rearmedAt:Object.create(null),
        blockedUntil:Object.create(null),
        blockReason:Object.create(null)
      });
      state.blockedUntil[key]=Date.now()+Math.max(1000,Number(ms)||30000);
      state.blockReason[key]=String(reason||'hard-failure');
      recordDiagnostic('treasure-automap-module-block',{
        revision:HK_TREASURE_AUTOMAP_OWNERSHIP_REV,
        module:key,
        reason:String(reason||'hard-failure'),
        waitMs:Math.max(1000,Number(ms)||30000)
      });
    }

"""
if s.count(anchor)!=1:
    raise SystemExit("autoMapCaptureModes anchor missing")
s=s.replace(anchor,ownership+anchor,1)

old_fatal="""      const fatalReasons=new Set([
        'state-cycle',
        'transition-mismatch',
        'plan-state-drift',
        'plan-exhausted-not-solved',
        'step-limit',
        'stale-modal-blocking',
        'modal-not-closed-after-change'
      ]);

      if (autoMapOwnsLights && !fatalReasons.has(reason)) {
"""
new_fatal="""      const fatalReasons=new Set([
        'state-cycle',
        'transition-mismatch',
        'plan-state-drift',
        'plan-exhausted-not-solved',
        'step-limit'
      ]);

      if (autoMapOwnsLights && fatalReasons.has(reason)) {
        autoMapBlockOwnedModule('lights',reason,30000);
      }

      if (autoMapOwnsLights && !fatalReasons.has(reason)) {
"""
rep(old_fatal,new_fatal,"lights recoverable UI failures")

old_running_gate="""      if (autoMapModulesRunning()) {
        const minigameForeground=autoMapMiniGameForeground();
"""
new_running_gate="""      const ownedSignature=getSignature();
      if (autoMapEnsureOwnedModule(ownedSignature)) {
        return false;
      }

      if (autoMapModulesRunning()) {
        const minigameForeground=autoMapMiniGameForeground();
"""
rep(old_running_gate,new_running_gate,"owned module watchdog")

old_check="""      const battleContext=isBattle || isBattleReward;
      ensureBattleAutoToggle(battleContext);
      ensureChestAutoToggle(isChests);
      ensureLightsAutoToggle(isLights);
      ensureFishingAutoToggle(isFishing);
      ensureTraderAutoToggle(isTrader);
      if (!isTrader) traderSessionPurchases=0;
      if (battleAutoRunning || chestAutoRunning || lightsAutoRunning || fishingAutoRunning || traderAutoRunning) return;
"""
new_check="""      const battleContext=isBattle || isBattleReward;
      ensureBattleAutoToggle(battleContext);
      ensureChestAutoToggle(isChests);
      ensureLightsAutoToggle(isLights);
      ensureFishingAutoToggle(isFishing);
      ensureTraderAutoToggle(isTrader);
      if (!isTrader) traderSessionPurchases=0;

      // AutoMap is the parent controller. Child toggles are implementation
      // details while a room is owned by AutoMap and may not remain OFF after a
      // recoverable UI failure.
      if (autoMapEnsureOwnedModule(signature)) return;

      if (battleAutoRunning || chestAutoRunning || lightsAutoRunning || fishingAutoRunning || traderAutoRunning) return;
"""
rep(old_check,new_check,"checkPuzzle owned module watchdog")

rep("      treasureLocationModalRootRevision:HK_TREASURE_LOCATION_MODAL_ROOT_REV,\n      traderWhitelistRevision:HK_TRADER_WHITELIST_REV,",
    "      treasureLocationModalRootRevision:HK_TREASURE_LOCATION_MODAL_ROOT_REV,\n      treasureAutoMapOwnershipRevision:HK_TREASURE_AUTOMAP_OWNERSHIP_REV,\n      traderWhitelistRevision:HK_TRADER_WHITELIST_REV,",
    "export ownership revision")

for marker in [
    "// @version      1.18.47",
    "const BUILD_VERSION = '1.18.47';",
    "treasure-automap-module-ownership-20260927-r1",
    "function autoMapEnsureOwnedModule(",
    "function autoMapBlockOwnedModule(",
    "treasure-automap-module-rearm",
    "treasure-automap-module-block",
    "setLightsAutoEnabled(true)",
    "setChestAutoEnabled(true)",
    "setFishingAutoEnabled(true)",
    "setTraderAutoEnabled(true)",
    "if (autoMapEnsureOwnedModule(signature)) return;",
    "if (autoMapEnsureOwnedModule(ownedSignature))",
    "autoMapBlockOwnedModule('lights',reason,30000)",
    "treasure-location-modal-root-20260927-r1",
    "treasure-chest-map-foreground-guard-20260927-r1"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("TREASURE_AUTOMAP_MODULE_OWNERSHIP_1_18_47=PASS")
