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

rep("// @version      1.18.48",
    "// @version      1.18.49\n// @release-note Лабиринт: исправлена настоящая причина зависания на окне лампочки. Предыдущий фикс всё ещё выбирал внутреннюю чёрную панель, потому что общий поиск модалки специально предпочитал самый маленький контейнер. Теперь для Лабиринта есть отдельный поиск ВНЕШНЕЙ золотой модалки через подъём по предкам и наличие реального X в правом верхнем углу. Очистка зависшей лампы закрывает именно внешнее окно и только после этого продолжает решение.",
    "version")
rep("const BUILD_VERSION = '1.18.48';",
    "const BUILD_VERSION = '1.18.49';",
    "build")
rep("  const HK_TREASURE_LIGHTS_RESUME_REV='treasure-lights-resume-open-modal-20260927-r1';",
    "  const HK_TREASURE_LIGHTS_RESUME_REV='treasure-lights-resume-open-modal-20260927-r1';\n  const HK_TREASURE_LIGHTS_OUTER_MODAL_REV='treasure-lights-outer-modal-20260927-r1';",
    "revision")

anchor="""    function lightsModalRoot() {
"""
helper="""    function lightsOuterModalRoot() {
      const vw=Math.max(1,window.innerWidth);
      const vh=Math.max(1,window.innerHeight);
      const seeds=[];

      const centered=treasureCenteredModalRoot();
      if (centered) seeds.push(centered);

      [...document.querySelectorAll('[role="dialog"],[aria-modal="true"],[class*="modal"],[class*="popup"],[class*="dialog"]')]
        .filter(visible)
        .filter(element=>/лампоч|light\s*bulb|bulb|lights?\s*out/.test(lightsModalText(element)))
        .forEach(element=>seeds.push(element));

      const rows=[];
      const seen=new Set();

      for (const seed of seeds) {
        const seedRect=seed?.getBoundingClientRect?.();
        let node=seed;
        for (let depth=0;node && depth<12;depth++,node=node.parentElement) {
          if (!node || seen.has(node) || !visible(node)) continue;
          seen.add(node);

          const rect=node.getBoundingClientRect?.();
          if (!rect) continue;
          if (rect.width<Math.min(300,vw*0.30) || rect.height<180) continue;
          if (rect.width>vw*0.96 || rect.height>vh*0.96) continue;

          const text=lightsModalText(node);
          if (!/лампоч|light\s*bulb|bulb|lights?\s*out/.test(text)) continue;

          const cx=rect.left+rect.width/2;
          const cy=rect.top+rect.height/2;
          if (Math.abs(cx-vw/2)>vw*0.22 || Math.abs(cy-vh/2)>vh*0.25) continue;

          const close=lightsModalCloseButton(node) || autoMapModalCloseButton(node);
          const expandsAbove=seedRect ? (seedRect.top-rect.top)>=18 : false;
          const expandsSides=seedRect ? (
            (seedRect.left-rect.left)>=6 ||
            ((rect.left+rect.width)-(seedRect.left+seedRect.width))>=6
          ) : false;

          let score=0;
          if (close) score+=1000;
          if (expandsAbove) score+=220;
          if (expandsSides) score+=120;
          if (depth>0) score+=80;
          if (rect.height>=240) score+=60;
          if (rect.width>=420) score+=40;

          rows.push({
            element:node,
            close,
            score,
            area:rect.width*rect.height,
            depth,
            rect
          });
        }
      }

      rows.sort((a,b)=>
        b.score-a.score ||
        a.area-b.area ||
        a.depth-b.depth
      );

      const selected=rows.find(row=>row.close)?.element ||
        rows.find(row=>row.score>=300)?.element ||
        null;

      if (selected) {
        const rect=selected.getBoundingClientRect?.();
        recordDiagnostic('treasure-lights-outer-modal-root',{
          revision:HK_TREASURE_LIGHTS_OUTER_MODAL_REV,
          left:Math.round(rect?.left||0),
          top:Math.round(rect?.top||0),
          width:Math.round(rect?.width||0),
          height:Math.round(rect?.height||0),
          hasClose:!!(lightsModalCloseButton(selected) || autoMapModalCloseButton(selected))
        });
      }

      return selected;
    }

"""
if s.count(anchor)!=1:
    raise SystemExit("lightsModalRoot anchor missing")
s=s.replace(anchor,helper+anchor,1)

old_root="""    function lightsModalRoot() {
      // A lamp dialog is composed from several nested panels. The historical
      // scorer could pick the inner black content panel, which contains the
      // text/cost but not the top-right close control. When AutoMap resumed
      // with that modal already open, stale-modal cleanup could never dismiss
      // it and remained forever on "мини-игра". Prefer the real centered outer
      // action dialog first.
      const centered=treasureCenteredModalRoot();
      if (centered) {
        const centeredText=lightsModalText(centered);
        if (/лампоч|light\s*bulb|bulb|lights?\s*out/.test(centeredText)) {
          return centered;
        }
      }

      const rows=[];
"""
new_root="""    function lightsModalRoot() {
      // The generic centered-modal helper intentionally chooses the smallest
      // actionable container. For the lamp UI that is the inner black panel,
      // not the gold frame that owns the X control. Use the dedicated outer
      // dialog resolver first.
      const outer=lightsOuterModalRoot();
      if (outer) return outer;

      const rows=[];
"""
rep(old_root,new_root,"use dedicated outer lamp modal")

old_outer_block="""        // If the scored lamp root is still an inner panel, escalate to the
        // actual centered outer dialog. Important: stale cleanup NEVER presses
        // the cost button; it only dismisses the old modal, then the solver
        // recalculates and opens the correct next lamp.
        const outer=treasureCenteredModalRoot();
        if (outer) {
          const outerText=lightsModalText(outer);
          if (/лампоч|light\s*bulb|bulb|lights?\s*out/.test(outerText)) {
            const outerClose=
              lightsModalCloseButton(outer) ||
              autoMapModalCloseButton(outer);
            if (outerClose && dispatchBattleTap(outerClose,'lights-clear-stale-outer-close-'+slot)) {
              recordDiagnostic('lights-stale-modal-cleared',{
                revision:HK_TREASURE_LIGHTS_RESUME_REV,
                slot,
                method:'outer-close'
              });
              await new Promise(resolve=>setTimeout(resolve,260));
              continue;
            }

            const orr=outer.getBoundingClientRect?.();
            if (orr && orr.width>180 && orr.height>180) {
              if (dispatchBattleTapAt(
                orr.left+orr.width-20,
                orr.top+20,
                'lights-clear-stale-outer-corner-'+slot
              )) {
                recordDiagnostic('lights-stale-modal-cleared',{
                  revision:HK_TREASURE_LIGHTS_RESUME_REV,
                  slot,
                  method:'outer-corner'
                });
                await new Promise(resolve=>setTimeout(resolve,300));
                continue;
              }
            }
          }
        }
"""
new_outer_block="""        // Escalate to the real outer gold frame. Stale cleanup NEVER presses
        // the berry/cost button; it only dismisses the old modal and lets the
        // solver recalculate from the unchanged 3x3 board.
        const outer=lightsOuterModalRoot();
        if (outer) {
          const outerClose=
            lightsModalCloseButton(outer) ||
            autoMapModalCloseButton(outer);
          if (outerClose && dispatchBattleTap(outerClose,'lights-clear-stale-outer-close-'+slot)) {
            recordDiagnostic('lights-stale-modal-cleared',{
              revision:HK_TREASURE_LIGHTS_OUTER_MODAL_REV,
              slot,
              method:'outer-close'
            });
            await new Promise(resolve=>setTimeout(resolve,300));
            if (!lightsModalRoot()) return true;
            continue;
          }

          const orr=outer.getBoundingClientRect?.();
          if (orr && orr.width>180 && orr.height>180) {
            if (dispatchBattleTapAt(
              orr.left+orr.width-26,
              orr.top+26,
              'lights-clear-stale-outer-corner-'+slot
            )) {
              recordDiagnostic('lights-stale-modal-cleared',{
                revision:HK_TREASURE_LIGHTS_OUTER_MODAL_REV,
                slot,
                method:'outer-corner'
              });
              await new Promise(resolve=>setTimeout(resolve,340));
              if (!lightsModalRoot()) return true;
              continue;
            }
          }
        }
"""
rep(old_outer_block,new_outer_block,"true outer modal stale cleanup")

rep("      treasureLightsResumeRevision:HK_TREASURE_LIGHTS_RESUME_REV,\n      traderWhitelistRevision:HK_TRADER_WHITELIST_REV,",
    "      treasureLightsResumeRevision:HK_TREASURE_LIGHTS_RESUME_REV,\n      treasureLightsOuterModalRevision:HK_TREASURE_LIGHTS_OUTER_MODAL_REV,\n      traderWhitelistRevision:HK_TRADER_WHITELIST_REV,",
    "export outer modal revision")

for marker in [
    "// @version      1.18.49",
    "const BUILD_VERSION = '1.18.49';",
    "treasure-lights-outer-modal-20260927-r1",
    "function lightsOuterModalRoot()",
    "lightsModalCloseButton(node) || autoMapModalCloseButton(node)",
    "const outer=lightsOuterModalRoot();",
    "lights-clear-stale-outer-close",
    "lights-clear-stale-outer-corner",
    "treasure-lights-resume-open-modal-20260927-r1",
    "treasure-automap-module-ownership-20260927-r1"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("TREASURE_LIGHTS_OUTER_MODAL_1_18_49=PASS")
