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
    "// @version      1.18.73",
    "// @version      1.18.74\n"
    "// @release-note Карта сокровищ: убрана служебная плавающая кнопка «Запись карты». Рекордер больше не занимает место на экране; остальная логика Автокарты и мини-игр не менялась.",
    "version"
)
rep("const BUILD_VERSION = '1.18.73';","const BUILD_VERSION = '1.18.74';","build")

anchor="  const HK_PURCHASE_CONFIRM_FAST_GLOBAL_REV='purchase-confirm-fast-global-20260928-r1';"
rep(
    anchor,
    anchor+"\n  const HK_TREASURE_RECORDER_UI_REMOVED_REV='treasure-recorder-ui-removed-20260928-r1';",
    "recorder ui removed revision"
)

old_update="""  function treasureRunRecorderUpdateButton() {
    if(!treasureRunRecorderButton)return;
    const active=treasureRunRecorderActive();
    const show=treasureEventContextVisible();
    const display=show?'block':'none';
    const label=active
      ? 'Запись карты: ВКЛ #'+String(treasureRunRecorderState?.runIndex||'')
      : 'Запись карты: ВЫКЛ';
    const background=active?'#d13b3b':'#292929';
    const borderColor=active?'#ffd5d5':'rgba(255,255,255,.8)';

    if(treasureRunRecorderButton.style.display!==display)treasureRunRecorderButton.style.display=display;
    if(treasureRunRecorderButton.textContent!==label)treasureRunRecorderButton.textContent=label;
    if(treasureRunRecorderButton.style.background!==background)treasureRunRecorderButton.style.background=background;
    if(treasureRunRecorderButton.style.color!=='rgb(255, 255, 255)' && treasureRunRecorderButton.style.color!=='#fff')treasureRunRecorderButton.style.color='#fff';
    if(treasureRunRecorderButton.style.borderColor!==borderColor)treasureRunRecorderButton.style.borderColor=borderColor;
  }
"""
new_update="""  function treasureRunRecorderUpdateButton() {
    // Recorder UI is retired. Keep the recorder internals available for
    // diagnostics/API use, but never leave a floating control on the game UI.
    try {
      if(treasureRunRecorderButton?.isConnected) treasureRunRecorderButton.remove();
      document.getElementById('hkTreasureRunRecorderToggle')?.remove();
    } catch (_) {}
  }
"""
rep(old_update,new_update,"remove recorder button ui")

old_create="""      if(!treasureRunRecorderButton){
        treasureRunRecorderButton=document.createElement('button');
        treasureRunRecorderButton.id='hkTreasureRunRecorderToggle';
        treasureRunRecorderButton.type='button';
        Object.assign(treasureRunRecorderButton.style,{
          position:'fixed',
          left:'12px',
          bottom:'154px',
          zIndex:'2147483646',
          border:'2px solid rgba(255,255,255,.8)',
          borderRadius:'18px',
          padding:'8px 11px',
          fontSize:'12px',
          fontWeight:'900',
          lineHeight:'1',
          boxShadow:'0 4px 14px rgba(0,0,0,.55)',
          WebkitTapHighlightColor:'transparent',
          touchAction:'manipulation'
        });
        treasureRunRecorderButton.addEventListener('click',event=>{
          event.preventDefault();
          event.stopPropagation();
          treasureRunRecorderToggle();
        },true);
        document.body.appendChild(treasureRunRecorderButton);
      }

"""
new_create="""      // Floating recorder control retired in 1.18.74.
      // Remove a stale control left by an older injected build, if present.
      try { document.getElementById('hkTreasureRunRecorderToggle')?.remove(); } catch (_) {}

"""
rep(old_create,new_create,"remove recorder button creation")

export_anchor="      purchaseConfirmFastGlobalRevision:HK_PURCHASE_CONFIRM_FAST_GLOBAL_REV,"
if s.count(export_anchor)!=1:
    raise SystemExit("purchase confirm export anchor missing")
s=s.replace(
    export_anchor,
    export_anchor+"\n      treasureRecorderUiRemovedRevision:HK_TREASURE_RECORDER_UI_REMOVED_REV,",
    1
)

for marker in [
    "// @version      1.18.74",
    "const BUILD_VERSION = '1.18.74';",
    "treasure-recorder-ui-removed-20260928-r1",
    "Floating recorder control retired in 1.18.74",
    "document.getElementById('hkTreasureRunRecorderToggle')?.remove()",
    "treasureRecorderUiRemovedRevision:HK_TREASURE_RECORDER_UI_REMOVED_REV",
    "purchase-confirm-fast-global-20260928-r1",
    "treasure-run-recorder-20260926-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

if "treasureRunRecorderButton=document.createElement('button')" in s:
    raise SystemExit("recorder button creation still present")

p.write_text(s,encoding="utf-8")
print("TREASURE_RECORDER_UI_REMOVED_1_18_74=PASS")
