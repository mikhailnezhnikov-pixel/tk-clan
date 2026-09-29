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

rep("// @version      1.18.86",
    "// @version      1.18.87\n// @release-note Карта сокровищ: исправлены зависания в окнах мини-игр на мобильном. Сражение теперь находит широкую кнопку атаки даже если игра рисует её как div/span, а системные кнопки Автокарты больше не перехватывают координатные клики по «Понятно» и кнопкам стоимости.",
    "version")
rep("const BUILD_VERSION = '1.18.86';",
    "const BUILD_VERSION = '1.18.87';",
    "build")

rev_anchor="  const HK_BATTLE_PREVIEW_RESUME_REV='battle-preview-resume-20260929-r1';"
rep(rev_anchor,
    rev_anchor+"\n  const HK_MINIGAME_OVERLAY_PASSTHROUGH_REV='minigame-overlay-pass-through-20260929-r1';\n  const HK_BATTLE_ACTION_MODAL_DIV_REV='battle-action-modal-div-20260929-r1';",
    "revisions")

old_action=r'''    function battleActionButton(expectedCost) {
      const costText=String(expectedCost ?? '');
      const candidates=[...document.querySelectorAll('button,[role="button"],a')]
        .filter(element=>element && element!==battleAutoToggle && element.id!=='hkBattleAutoToggle')
        .filter(element=>!element.disabled && visible(element))
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'');
          const images=[...element.querySelectorAll?.('img')||[]]
            .map(img=>String(img.alt||'')+' '+String(img.src||'')).join(' ');
          const rect=element.getBoundingClientRect?.() || {width:0,height:0,top:0};
          let score=0;
          if (text===costText) score+=100;
          else if (costText && new RegExp('(?:^|\s)'+costText+'(?:\s|$)').test(text)) score+=35;
          if (/sword|attack|fight|weapon|blade|меч|атак/i.test(images+' '+text)) score+=50;
          if (rect.width>=120 && rect.height>=36) score+=10;
          if (rect.top>window.innerHeight*0.45) score+=5;
          if (/закрыть|close|×|✕|назад|back/i.test(text)) score-=200;
          return {element,text,score};
        })
        .filter(row=>row.score>0)
        .sort((a,b)=>b.score-a.score);
      return candidates[0]?.element || null;
    }
'''
new_action=r'''    function battleActionButton(expectedCost) {
      const costText=String(expectedCost ?? '');
      if (!costText) return null;
      const costPattern=new RegExp('(?:^|\\s)'+costText+'(?:\\s|$)');
      const overlays=new Set(battleUiOverlays());

      const raw=[...document.querySelectorAll('button,[role="button"],a,[onclick],div,span')]
        .filter(element=>
          element &&
          !overlays.has(element) &&
          !element.disabled &&
          element.getAttribute?.('aria-disabled')!=='true' &&
          visible(element)
        );

      const rows=[];
      const seen=new Set();
      for (const element of raw) {
        let target=element;
        let node=element;
        for (let depth=0;node && depth<6;depth++,node=node.parentElement) {
          if (overlays.has(node)) break;
          if (!visible(node)) continue;
          let actionable=false;
          try {
            const style=getComputedStyle(node);
            actionable=
              node.matches?.('button,[role="button"],a,[onclick]') ||
              !!node.onclick ||
              style.cursor==='pointer';
          } catch (_) {}
          if (actionable) {
            target=node;
            break;
          }
        }
        if (!target || seen.has(target) || overlays.has(target)) continue;
        seen.add(target);

        const text=clean(target.innerText||target.textContent||'').trim();
        const images=[...target.querySelectorAll?.('img')||[]]
          .map(img=>String(img.alt||'')+' '+String(img.src||'')).join(' ');
        const rect=target.getBoundingClientRect?.() || {width:0,height:0,top:0,left:0};
        const cx=rect.left+rect.width/2;
        const cy=rect.top+rect.height/2;
        const viewportArea=Math.max(1,window.innerWidth*window.innerHeight);
        const area=Math.max(0,rect.width*rect.height);

        let score=0;
        if (text===costText) score+=240;
        else if (costPattern.test(text)) score+=110;
        if (/sword|attack|fight|weapon|blade|меч|атак/i.test(images+' '+text)) score+=150;
        if (rect.width>=window.innerWidth*0.28 && rect.width<=window.innerWidth*0.86) score+=90;
        if (rect.height>=36 && rect.height<=150) score+=80;
        if (cy>=window.innerHeight*0.55) score+=80;
        if (Math.abs(cx-window.innerWidth/2)<=window.innerWidth*0.30) score+=60;
        if (area>viewportArea*0.22) score-=420;
        if (text.length>120) score-=260;
        if (/закрыть|close|×|✕|назад|back|понятно|got it|understood/i.test(text)) score-=700;

        rows.push({element:target,text,score,area,rect});
      }

      rows.sort((a,b)=>b.score-a.score || b.area-a.area);
      const best=rows.find(row=>row.score>=240) || null;
      if (best) {
        recordDiagnostic('battle-action-button-found',{
          revision:HK_BATTLE_ACTION_MODAL_DIV_REV,
          expectedCost:Number(expectedCost),
          text:best.text.slice(0,80),
          score:best.score,
          tag:best.element.tagName||'',
          width:Math.round(best.rect.width||0),
          height:Math.round(best.rect.height||0)
        });
      }
      return best?.element || null;
    }
'''
rep(old_action,new_action,"battle action selector")

old_tap=r'''      const leaf=document.elementFromPoint(x,y) || element;'''
rep(old_tap,
    r'''      const leaf=battleElementFromPointIgnoringOverlays(x,y,element) || element;''',
    "dispatch battle tap pass-through",
    count=1)

old_tap_at=r'''      const leaf=document.elementFromPoint(px,py);'''
rep(old_tap_at,
    r'''      const leaf=battleElementFromPointIgnoringOverlays(px,py,null);''',
    "dispatch battle tap-at pass-through",
    count=1)

# Extend wait slightly for animated mobile modals.
rep("    function waitBattleActionButton(expectedCost,runId,timeoutMs=2500) {",
    "    function waitBattleActionButton(expectedCost,runId,timeoutMs=4200) {",
    "battle action wait")

# Expose markers in runtime diagnostics.
rep("      battlePreviewResumeRevision:HK_BATTLE_PREVIEW_RESUME_REV,",
    "      battlePreviewResumeRevision:HK_BATTLE_PREVIEW_RESUME_REV,\n      minigameOverlayPassthroughRevision:HK_MINIGAME_OVERLAY_PASSTHROUGH_REV,\n      battleActionModalDivRevision:HK_BATTLE_ACTION_MODAL_DIV_REV,",
    "diagnostic export")

for marker in [
    "// @version      1.18.87",
    "minigame-overlay-pass-through-20260929-r1",
    "battle-action-modal-div-20260929-r1",
    "button,[role=\"button\"],a,[onclick],div,span",
    "battleElementFromPointIgnoringOverlays(x,y,element)",
    "battleElementFromPointIgnoringOverlays(px,py,null)",
    "timeoutMs=4200",
    "battle-preview-resume-20260929-r1",
    "battle-intro-hard-gate-20260929-r1",
    "battle-visible-point-truth-20260929-r1",
    "lights-confirm-ack-before-board-reward-gate-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

p.write_text(s,encoding="utf-8")
print("MINIGAME_MODAL_ACTIONS_1_18_87=PASS")
