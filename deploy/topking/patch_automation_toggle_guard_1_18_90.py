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

rep("// @version      1.18.89",
    "// @version      1.18.90\n// @release-note Исправлено самопроизвольное выключение Автокарты/Автоламп/Автосундуков: служебные кнопки теперь реагируют только на реальный пользовательский тап. Все координатные fallback-клики торговца, сундуков и финальной награды проходят сквозь HK-оверлеи.",
    "version")
rep("const BUILD_VERSION = '1.18.89';",
    "const BUILD_VERSION = '1.18.90';",
    "build")

rev_anchor="  const HK_STALE_MODAL_SHELL_CLOSE_REV='stale-modal-shell-close-20260929-r1';"
rep(rev_anchor,
    rev_anchor+"\n  const HK_AUTOMATION_TOGGLE_TRUST_REV='automation-toggle-trusted-input-20260929-r1';\n  const HK_COORDINATE_OVERLAY_GUARD_REV='coordinate-overlay-guard-20260929-r1';",
    "revisions")

handlers=[
("battleAutoToggle","setBattleAutoEnabled(!battleAutoEnabled());"),
("chestAutoToggle","setChestAutoEnabled(!chestAutoEnabled());"),
("lightsAutoToggle","setLightsAutoEnabled(!lightsAutoEnabled());"),
("fishingAutoToggle","setFishingAutoEnabled(!fishingAutoEnabled());"),
("traderAutoToggle","setTraderAutoEnabled(!traderAutoEnabled());"),
("autoMapToggle","setAutoMapEnabled(!autoMapEnabled());"),
]
for toggle,setter in handlers:
    old=f"""        {toggle}.addEventListener('click',event=>{{
          event.preventDefault();
          event.stopPropagation();
          {setter}
        }},true);"""
    new=f"""        {toggle}.addEventListener('click',event=>{{
          event.preventDefault();
          event.stopPropagation();
          if (!event.isTrusted) {{
            recordDiagnostic('automation-toggle-synthetic-blocked',{{
              revision:HK_AUTOMATION_TOGGLE_TRUST_REV,
              toggle:'{toggle}'
            }});
            return;
          }}
          {setter}
        }},true);"""
    # autoMap indentation is 6 spaces, not 8.
    if s.count(old)!=1 and toggle=="autoMapToggle":
        old=f"""      {toggle}.addEventListener('click',event=>{{
        event.preventDefault();
        event.stopPropagation();
        {setter}
      }},true);"""
        new=f"""      {toggle}.addEventListener('click',event=>{{
        event.preventDefault();
        event.stopPropagation();
        if (!event.isTrusted) {{
          recordDiagnostic('automation-toggle-synthetic-blocked',{{
            revision:HK_AUTOMATION_TOGGLE_TRUST_REV,
            toggle:'{toggle}'
          }});
          return;
        }}
        {setter}
      }},true);"""
    rep(old,new,"trusted toggle "+toggle)

# No automated coordinate action may ever resolve onto our floating HK controls.
# Keep the shared legacy dispatcher intact for compatibility, but route every
# live fallback call through the overlay-safe resolver.
pairs=[
("dispatchBattleTapAt(x,y,'trader-forbidden-gold-close-corner-'+source)",
 "dispatchMinigameOverlaySafeTapAt(x,y,'trader-forbidden-gold-close-corner-'+source)"),
("""dispatchBattleTapAt(
            rect.left+rect.width/2,
            rect.top+rect.height/2,
            'trader-receipt-ack-center-'+source
          )""",
 """dispatchMinigameOverlaySafeTapAt(
            rect.left+rect.width/2,
            rect.top+rect.height/2,
            'trader-receipt-ack-center-'+source
          )"""),
("""dispatchBattleTapAt(
            rect.left+rect.width/2,
            rect.top+rect.height/2,
            'trader-approved-modal-confirm-center'
          )""",
 """dispatchMinigameOverlaySafeTapAt(
            rect.left+rect.width/2,
            rect.top+rect.height/2,
            'trader-approved-modal-confirm-center'
          )"""),
("""dispatchBattleTapAt(
                rect.left+rect.width/2,
                rect.top+rect.height/2,
                'trader-confirm-center-'+target.lotId
              )""",
 """dispatchMinigameOverlaySafeTapAt(
                rect.left+rect.width/2,
                rect.top+rect.height/2,
                'trader-confirm-center-'+target.lotId
              )"""),
("dispatchBattleTapAt(x,rr.top+rr.height*fraction,'chest-action-fallback-'+fraction)",
 "dispatchMinigameOverlaySafeTapAt(x,rr.top+rr.height*fraction,'chest-action-fallback-'+fraction)"),
("dispatchBattleTapAt(x,rr.top+rr.height*fraction,'victory-fallback-'+fraction)",
 "dispatchMinigameOverlaySafeTapAt(x,rr.top+rr.height*fraction,'victory-fallback-'+fraction)"),
]
for idx,(old,new) in enumerate(pairs,1):
    rep(old,new,f"overlay-safe coordinate fallback {idx}")

# Export markers.
export_anchor="      staleModalShellCloseRevision:HK_STALE_MODAL_SHELL_CLOSE_REV,"
rep(export_anchor,
    export_anchor+"\n      automationToggleTrustRevision:HK_AUTOMATION_TOGGLE_TRUST_REV,\n      coordinateOverlayGuardRevision:HK_COORDINATE_OVERLAY_GUARD_REV,",
    "revision export")

for marker in [
    "// @version      1.18.90",
    "automation-toggle-trusted-input-20260929-r1",
    "coordinate-overlay-guard-20260929-r1",
    "automation-toggle-synthetic-blocked",
    "if (!event.isTrusted)",
    "dispatchMinigameOverlaySafeTapAt(x,rr.top+rr.height*fraction,'chest-action-fallback-'",
    "dispatchMinigameOverlaySafeTapAt(x,rr.top+rr.height*fraction,'victory-fallback-'",
    "treasure-map-quiet-gate-20260929-r1",
    "chest-lot-hard-gate-20260929-r1",
    "lights-confirm-ack-before-board-reward-gate-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

p.write_text(s,encoding="utf-8")
print("AUTOMATION_TOGGLE_GUARD_1_18_90=PASS")
