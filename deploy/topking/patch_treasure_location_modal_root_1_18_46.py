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

rep("// @version      1.18.45",
    "// @version      1.18.46\n// @release-note Карта сокровищ: исправлено зависание «ЖДУ ОКНО» после выбора клетки. Для модалки входа в локацию HK теперь сначала определяет реальный центральный диалог по геометрии и кнопке действия (например стоимость 20), а не случайный контейнер вокруг картинки. Поэтому кнопка входа подтверждается сразу, после чего Автокарта продолжает маршрут.",
    "version")
rep("const BUILD_VERSION = '1.18.45';",
    "const BUILD_VERSION = '1.18.46';",
    "build")
rep("  const HK_TREASURE_CHEST_MAP_GUARD_REV='treasure-chest-map-foreground-guard-20260927-r1';",
    "  const HK_TREASURE_CHEST_MAP_GUARD_REV='treasure-chest-map-foreground-guard-20260927-r1';\n  const HK_TREASURE_LOCATION_MODAL_ROOT_REV='treasure-location-modal-root-20260927-r1';",
    "revision")

anchor="""    function treasureModalRoot(cost) {
"""
helper="""    function treasureCenteredModalRoot() {
      const vw=Math.max(1,window.innerWidth);
      const vh=Math.max(1,window.innerHeight);
      const center=document.elementFromPoint?.(vw/2,vh/2);
      if (!center) return null;

      const rows=[];
      let node=center;
      for (let depth=0;node && depth<14;depth++,node=node.parentElement) {
        if (!visible(node)) continue;
        const rect=node.getBoundingClientRect?.();
        if (!rect) continue;
        if (rect.width<Math.min(260,vw*0.30) || rect.height<180) continue;
        if (rect.width>vw*0.94 || rect.height>vh*0.94) continue;

        const centerX=rect.left+rect.width/2;
        const actions=[...node.querySelectorAll('button,[role="button"],a,[onclick],div,span')]
          .filter(element=>element && !element.disabled && visible(element))
          .map(element=>{
            const text=clean(element.innerText||element.textContent||'').trim();
            const r=element.getBoundingClientRect?.() || {left:0,top:0,width:0,height:0};
            const cx=r.left+r.width/2;
            let actionable=false;
            try {
              actionable=
                element.matches?.('button,[role="button"],a,[onclick]') ||
                !!element.onclick ||
                getComputedStyle(element).cursor==='pointer';
            } catch (_) {}
            let score=0;
            if (/^\d{1,4}$/.test(text)) score+=260;
            if (/^(?:▷|▶|►|play|start|open|открыть|получить|забрать|claim|collect)$/i.test(text)) score+=220;
            if (r.top>=rect.top+rect.height*0.48) score+=120;
            if (r.width>=rect.width*0.24 && r.width<=rect.width*0.92) score+=100;
            if (r.height>=34 && r.height<=150) score+=80;
            if (Math.abs(cx-centerX)<=rect.width*0.30) score+=100;
            if (actionable) score+=80;
            if (/закрыть|close|×|✕|назад|back|понятно|ok|okay/i.test(text)) score-=600;
            return {element,text,score};
          })
          .filter(row=>row.score>=420);

        if (!actions.length) continue;

        const text=clean(node.innerText||node.textContent||'').trim();
        if (/завершит текущее путешествие|будет начата новая карта|нельзя будет вернуться/i.test(text)) continue;

        const cx=rect.left+rect.width/2;
        const cy=rect.top+rect.height/2;
        const centered=
          Math.abs(cx-vw/2)<=vw*0.18 &&
          Math.abs(cy-vh/2)<=vh*0.22;
        if (!centered) continue;

        rows.push({
          element:node,
          rect,
          area:rect.width*rect.height,
          actionScore:Math.max(...actions.map(row=>row.score))
        });
      }

      rows.sort((a,b)=>
        a.area-b.area ||
        b.actionScore-a.actionScore
      );
      const selected=rows[0]?.element || null;
      if (selected) {
        const rect=selected.getBoundingClientRect?.();
        recordDiagnostic('treasure-location-modal-root',{
          revision:HK_TREASURE_LOCATION_MODAL_ROOT_REV,
          left:Math.round(rect?.left||0),
          top:Math.round(rect?.top||0),
          width:Math.round(rect?.width||0),
          height:Math.round(rect?.height||0)
        });
      }
      return selected;
    }

"""
if s.count(anchor)!=1:
    raise SystemExit("treasureModalRoot anchor missing")
s=s.replace(anchor,helper+anchor,1)

old_root="""    function treasureModalRoot(cost) {
      const needle=String(cost?.id||'');
      const imgs=[...document.querySelectorAll('img')].filter(img=>visible(img) && (!needle || String(img.src||'').includes(needle)));
"""
new_root="""    function treasureModalRoot(cost) {
      // Generic AutoMap/location modals have many decorative images. Choosing
      // the smallest image ancestor could land inside the reward preview and
      // exclude the real bottom action button. For cost-less lookups prefer the
      // centered dialog that actually contains a usable action.
      if (!cost) {
        const centered=treasureCenteredModalRoot();
        if (centered) return centered;
      }

      const needle=String(cost?.id||'');
      const imgs=[...document.querySelectorAll('img')].filter(img=>visible(img) && (!needle || String(img.src||'').includes(needle)));
"""
rep(old_root,new_root,"prefer centered modal")

# If a modal is found but its initially selected root still cannot expose an
# action, retry against the centered dialog before declaring "жду подтверждение".
old_action_loop="""      let action=null;
      const actionDeadline=Date.now()+1800;
      while (Date.now()<actionDeadline) {
        if (runId!==autoMapRunId || !autoMapEnabled()) return false;
        action=autoMapModalPrimaryButton(modal,costHint);
        if (action) break;
        await new Promise(resolve=>setTimeout(resolve,80));
      }
"""
new_action_loop="""      let action=null;
      const actionDeadline=Date.now()+1800;
      while (Date.now()<actionDeadline) {
        if (runId!==autoMapRunId || !autoMapEnabled()) return false;
        action=autoMapModalPrimaryButton(modal,costHint);
        if (!action) {
          const centered=treasureCenteredModalRoot();
          if (centered && centered!==modal) {
            const centeredAction=autoMapModalPrimaryButton(centered,costHint);
            if (centeredAction) {
              modal=centered;
              action=centeredAction;
              recordDiagnostic('treasure-location-modal-action-recovered',{
                revision:HK_TREASURE_LOCATION_MODAL_ROOT_REV,
                label,
                costHint:Number.isFinite(costHint)?Number(costHint):null
              });
            }
          }
        }
        if (action) break;
        await new Promise(resolve=>setTimeout(resolve,80));
      }
"""
rep(old_action_loop,new_action_loop,"centered action recovery")

rep("      treasureChestMapGuardRevision:HK_TREASURE_CHEST_MAP_GUARD_REV,\n      traderWhitelistRevision:HK_TRADER_WHITELIST_REV,",
    "      treasureChestMapGuardRevision:HK_TREASURE_CHEST_MAP_GUARD_REV,\n      treasureLocationModalRootRevision:HK_TREASURE_LOCATION_MODAL_ROOT_REV,\n      traderWhitelistRevision:HK_TRADER_WHITELIST_REV,",
    "export modal root revision")

for marker in [
    "// @version      1.18.46",
    "const BUILD_VERSION = '1.18.46';",
    "treasure-location-modal-root-20260927-r1",
    "function treasureCenteredModalRoot()",
    "treasure-location-modal-root",
    "treasure-location-modal-action-recovered",
    "const centered=treasureCenteredModalRoot();",
    "treasure-chest-map-foreground-guard-20260927-r1",
    "treasury-left-path-exit-recovery-20260927-r1"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("TREASURE_LOCATION_MODAL_ROOT_1_18_46=PASS")
