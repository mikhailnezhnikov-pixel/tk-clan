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
    "// @version      1.18.16",
    "// @version      1.18.17\n"
    "// @release-note Автокарта: после подтверждения клетки теперь ждёт фактического изменения карты/комнаты, а не только закрытия модального окна. Минимальный темп замедлен; при 409 текущая клетка временно исключается и выполняется новый пересчёт вместо повторного клика.",
    "version"
)
rep("const BUILD_VERSION = '1.18.16';","const BUILD_VERSION = '1.18.17';","build")

rep(
    "  const HK_TREASURE_AUTO_MAP_REV='treasure-auto-map-orchestrator-20260926-r1';",
    "  const HK_TREASURE_AUTO_MAP_REV='treasure-auto-map-orchestrator-20260926-r1';\n"
    "  const HK_TREASURE_AUTO_MAP_STABILITY_REV='treasure-auto-map-stability-20260926-r2';",
    "stability marker"
)

rep(
    "    const AUTO_MAP_ACTION_GAP_MS=850;",
    "    const AUTO_MAP_ACTION_GAP_MS=1450;",
    "safer action gap"
)

rep(
    """    let autoMapCurrentLot='';
    let autoMapPreviousModes=null;
""",
    """    let autoMapCurrentLot='';
    const autoMapSkipLotsUntil=new Map();
    let autoMapPreviousModes=null;
""",
    "skip lot state"
)

rep(
    """        .filter(row=>row.lotId && !row.disabled)
        .sort((a,b)=>a.slot-b.slot || (a.cost??9999)-(b.cost??9999));
""",
    """        .filter(row=>{
          if (!row.lotId || row.disabled) return false;
          const until=Number(autoMapSkipLotsUntil.get(row.lotId)||0);
          if (until>Date.now()) return false;
          if (until) autoMapSkipLotsUntil.delete(row.lotId);
          return true;
        })
        .sort((a,b)=>a.slot-b.slot || (a.cost??9999)-(b.cost??9999));
""",
    "skip conflicted map lot"
)

rep(
    """      const wait=status===409 ? 1200 :
        status===429 ? 3200 :
        status>=500 ? 5200 : 1800;
      autoMapRetryNotBefore=Date.now()+wait;
""",
    """      const wait=status===409 ? 1800 :
        status===429 ? 3600 :
        status>=500 ? 5600 : 2200;
      if (status===409 && autoMapCurrentLot) {
        autoMapSkipLotsUntil.set(autoMapCurrentLot,Date.now()+6500);
      }
      autoMapRetryNotBefore=Date.now()+wait;
""",
    "409 skip and backoff"
)

# The critical fix: modal disappearance alone is not success after confirmation.
rep(
    """        if (autoMapStateFingerprint()!==before || !treasureModalRoot(null)) {
          await new Promise(resolve=>setTimeout(resolve,180));
          return true;
        }
""",
    """        if (autoMapStateFingerprint()!==before) {
          await new Promise(resolve=>setTimeout(resolve,260));
          return true;
        }
""",
    "require actual state change"
)

rep(
    """      autoMapRetryNotBefore=Date.now()+1800;
      autoMapStatus('пересканирую',{label,reason:'no-state-change'});
""",
    """      if (autoMapCurrentLot) {
        autoMapSkipLotsUntil.set(autoMapCurrentLot,Date.now()+4200);
      }
      autoMapRetryNotBefore=Date.now()+2200;
      autoMapStatus('пересканирую',{label,reason:'no-state-change'});
""",
    "no state change skip"
)

rep(
    """      autoMapRetryNotBefore=0;
      autoMapCurrentLot='';
""",
    """      autoMapRetryNotBefore=0;
      autoMapCurrentLot='';
      if (!value) autoMapSkipLotsUntil.clear();
""",
    "clear skips on stop"
)

rep(
    """          revision:HK_TREASURE_AUTO_MAP_REV,
          status:value,
""",
    """          revision:HK_TREASURE_AUTO_MAP_STABILITY_REV,
          status:value,
""",
    "status stability revision"
)

for marker in [
    "// @version      1.18.17",
    "const BUILD_VERSION = '1.18.17';",
    "treasure-auto-map-orchestrator-20260926-r1",
    "treasure-auto-map-stability-20260926-r2",
    "AUTO_MAP_ACTION_GAP_MS=1450",
    "autoMapSkipLotsUntil",
    "Date.now()+6500",
    "rumors-hunter-coordinator-kokkaras-v40-20260926-r4",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

target.write_text(s,encoding="utf-8")
print("TREASURE_AUTO_MAP_STABILITY_1_18_17=PASS")
