from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")
def rep(old,new,label,count=1):
    global s
    count_found=s.count(old)
    if count_found!=count: raise SystemExit(f"{label}: expected {count}, got {count_found}")
    s=s.replace(old,new,count)

def rep_in_battle(old,new,label):
    global s
    begin=s.find("    function ensureBattleAutoToggle(isBattle) {")
    end=s.find("    function chestAutoEnabled() {",begin)
    if begin<0 or end<0:raise SystemExit(label+": function boundary unavailable")
    chunk=s[begin:end]
    actual=chunk.count(old)
    if actual!=1:raise SystemExit(f"{label}: expected 1 in battle control, got {actual}")
    s=s[:begin]+chunk.replace(old,new,1)+s[end:]

rep("// @version      1.18.100",
    "// @version      1.18.101\n// @release-note Автокарта и автобой: две компактные кнопки снизу слева/справа со статусом внутри кнопки карты. В карточке бойца нажатие адресовано полноценной кнопке, а не вложенной цифре; неподтверждённые удары не оплачиваются повторно.",
    "version")
rep("const BUILD_VERSION = '1.18.100';","const BUILD_VERSION = '1.18.101';","build")

rev="  const HK_BATTLE_SINGLE_TAP_REV='battle-single-tap-until-receipt-20261001-r1';"
rep(rev,rev+"\n  const HK_BOTTOM_HUD_REV='battle-bottom-hud-status-20261001-r1';\n  const HK_ENEMY_ACTION_PARENT_REV='battle-enemy-action-parent-20261001-r1';","revisions")

# Promote a numeric/icon child to its actual interactive button. A digit-only
# span was scoring above the real purchase control on some mobile layouts.
start=s.find("    function battleEnemyModalActionButton(expectedCost=null) {")
end=s.find("    function battleEnemyModalActionCost(element) {",start)
if start<0 or end<0: raise SystemExit("battle enemy selector missing")
block=s[start:end]
old="""        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const rect=element.getBoundingClientRect?.() || {left:0,top:0,width:0,height:0};
          let actionable=false;"""
new="""        .map(element=>{
          // The visible cost may be a tiny inner span. Prefer its nearest real
          // button / interactive ancestor within the same enemy dialog.
          let target=element;
          for (let node=element,depth=0;node && node!==root && depth<6;
               node=node.parentElement,depth++) {
            if (root.contains && !root.contains(node)) break;
            let interactive=false;
            try {
              interactive=node.matches?.('button,[role="button"],a,[onclick]') ||
                !!node.onclick || getComputedStyle(node).cursor==='pointer';
            } catch (_) {}
            if (interactive) { target=node; break; }
          }
          element=target;
          if (element.disabled || element.getAttribute?.('aria-disabled')==='true') {
            return {element,score:-9999,rect:{width:0,height:0}};
          }
          const text=clean(element.innerText||element.textContent||'').trim();
          const rect=element.getBoundingClientRect?.() || {left:0,top:0,width:0,height:0};
          let actionable=false;"""
if block.count(old)!=1:raise SystemExit("battle enemy selector promotion anchor missing")
block=block.replace(old,new,1)
old="""          if (actionable) score+=120;"""
if block.count(old)!=1: raise SystemExit("actionable bonus anchor missing")
block=block.replace(old,"""          if (actionable) score+=250;""",1)
old="""          const best=rows[0] || null;"""
# no-op: retain existing diagnostics and threshold.
s=s[:start]+block+s[end:]

# Position left/right at the very bottom. Full ongoing status remains visible
# as second line INSIDE the left control, without a third overlay at mid-screen.
rep("""      battleAutoToggle.textContent=enabled ? either('Автобой: ВКЛ','Auto battle: ON') : either('Автобой: ВЫКЛ','Auto battle: OFF');""",
"""      battleAutoToggle.textContent=enabled ? either('Автобой: ВКЛ','Auto battle: ON') : either('Автобой: ВЫКЛ','Auto battle: OFF');
      battleAutoToggle.title=enabled?'Автобой включён':'Автобой выключен';""",
"battle button caption")

rep("""      const enemyModalOpen=!!battleEnemyModalRoot();
      const battleHudTop=enemyModalOpen?'132px':'auto';
      const battleHudBottom=enemyModalOpen?'auto':'154px';
      if (battleAutoToggle.style.top!==battleHudTop) battleAutoToggle.style.top=battleHudTop;
      if (battleAutoToggle.style.bottom!==battleHudBottom) battleAutoToggle.style.bottom=battleHudBottom;""",
"""      // The status is on the left. Keep this control on the right, well
      // below the centre of any enemy purchase modal.
      battleAutoToggle.style.top='auto';
      battleAutoToggle.style.bottom='calc(env(safe-area-inset-bottom, 0px) + 8px)';
      battleAutoToggle.style.left='auto';
      battleAutoToggle.style.right='8px';""",
"battle fixed bottom-right")

rep_in_battle("""          right:'14px',
          bottom:'154px',
          zIndex:'2147483646',
          border:'2px solid rgba(255,255,255,.75)',
          borderRadius:'18px',
          padding:'8px 11px',
          fontSize:'12px',
          fontWeight:'900',
          lineHeight:'1',""",
"""          right:'8px',
          bottom:'calc(env(safe-area-inset-bottom, 0px) + 8px)',
          maxWidth:'45vw',
          zIndex:'2147483646',
          border:'2px solid rgba(255,255,255,.75)',
          borderRadius:'14px',
          padding:'6px 8px',
          fontSize:'11px',
          fontWeight:'900',
          lineHeight:'1.12',
          whiteSpace:'normal',""",
"battle button compact style")

rep("""      const label=enabled
        ? 'Автокарта: ВКЛ'+(autoMapLastStatus?' · '+autoMapLastStatus:'')
        : 'Автокарта: ВЫКЛ';""",
"""      const label=enabled
        ? 'Автокарта: ВКЛ'+(autoMapLastStatus?'\\n'+autoMapLastStatus:'')
        : 'Автокарта: ВЫКЛ';
      autoMapToggle.title=autoMapLastStatus||'Автокарта';""",
"map diagnostic status on second line")

rep("""      const treasuryIntro=autoMapTreasuryIntroModalRoot();
      const enemyModalOpen=!!battleEnemyModalRoot();
      const hudBottom=(treasuryIntro||enemyModalOpen)?'auto':'202px';
      const hudTop=(treasuryIntro||enemyModalOpen)?'85px':'auto';
      if (autoMapToggle.style.bottom!==hudBottom) autoMapToggle.style.bottom=hudBottom;
      if (autoMapToggle.style.top!==hudTop) autoMapToggle.style.top=hudTop;""",
"""      autoMapToggle.style.top='auto';
      autoMapToggle.style.bottom='calc(env(safe-area-inset-bottom, 0px) + 8px)';
      autoMapToggle.style.left='8px';
      autoMapToggle.style.right='auto';""",
"map fixed bottom-left")

rep("""        right:'14px',
        bottom:'202px',
        zIndex:'2147483646',
        border:'2px solid rgba(255,255,255,.8)',
        borderRadius:'18px',
        padding:'8px 11px',
        fontSize:'12px',
        fontWeight:'900',
        lineHeight:'1',""",
"""        left:'8px',
        right:'auto',
        bottom:'calc(env(safe-area-inset-bottom, 0px) + 8px)',
        maxWidth:'46vw',
        zIndex:'2147483646',
        border:'2px solid rgba(255,255,255,.8)',
        borderRadius:'14px',
        padding:'6px 8px',
        fontSize:'10px',
        fontWeight:'900',
        lineHeight:'1.15',
        whiteSpace:'pre-line',
        overflowWrap:'anywhere',""",
"map button compact style")

revexport="      battleSingleTapRevision:HK_BATTLE_SINGLE_TAP_REV,"
rep(revexport,revexport+"\n      bottomHudRevision:HK_BOTTOM_HUD_REV,\n      battleEnemyActionParentRevision:HK_ENEMY_ACTION_PARENT_REV,","revision exports")

p.write_text(s,encoding="utf-8")
print("PATCH_BOTTOM_HUD_ENEMY_BUTTON_1_18_101=PASS")
