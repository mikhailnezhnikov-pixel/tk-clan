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

rep("// @version      1.18.21",
    "// @version      1.18.22\n// @release-note Автокарта: исправлено зависание «сундуки» на чистом экране карты. Мини-игра теперь считается передним планом только если её реальные элементы действительно находятся сверху в точках экрана; старые DOM-элементы под картой больше не блокируют выбор следующей ячейки.",
    "version")
rep("const BUILD_VERSION = '1.18.21';",
    "const BUILD_VERSION = '1.18.22';",
    "build")
rep("  const HK_TREASURE_AUTO_MAP_HANDOFF_REV='treasure-auto-map-foreground-handoff-20260926-r6';",
    "  const HK_TREASURE_AUTO_MAP_HANDOFF_REV='treasure-auto-map-foreground-handoff-20260926-r6';\n  const HK_TREASURE_AUTO_MAP_FOREGROUND_TRUTH_REV='treasure-auto-map-foreground-truth-20260926-r7';",
    "revision")

old="""    function autoMapMiniGameForeground() {
      const signature=getSignature();
      return /^(?:LIGHTS|BATTLE|FISHING|TRADER|CHESTS)(?:\\||$|_)/.test(signature);
    }
"""
new="""    function autoMapElementIsForeground(element) {
      if (!element || !visible(element)) return false;
      const rect=element.getBoundingClientRect?.();
      if (!rect || rect.width<=2 || rect.height<=2) return false;
      const points=[
        [rect.left+rect.width*0.50,rect.top+rect.height*0.50],
        [rect.left+rect.width*0.28,rect.top+rect.height*0.32],
        [rect.left+rect.width*0.72,rect.top+rect.height*0.68]
      ];
      return points.some(([x,y])=>{
        const px=Math.max(1,Math.min(window.innerWidth-1,x));
        const py=Math.max(1,Math.min(window.innerHeight-1,y));
        const top=document.elementFromPoint(px,py);
        return !!top && (top===element || element.contains(top) || top.contains(element));
      });
    }

    function autoMapMiniGameForeground() {
      const signature=getSignature();
      let elements=[];

      if (signature.startsWith('BATTLE')) {
        elements=[
          ...document.querySelectorAll('[data-lot-id*="mf_treasurelot_enemy_type_"]'),
          ...document.querySelectorAll('[data-lot-id*="mf_treasurelot_enemy_defeated"]'),
          ...document.querySelectorAll('[data-lot-id^="mf_treasurelot_sword_"]')
        ];
      } else if (signature.startsWith('CHESTS|')) {
        elements=treasureChestElements().map(row=>row.element);
      } else if (signature.startsWith('FISHING|')) {
        elements=fishingElements().map(row=>row.element);
      } else if (signature.startsWith('TRADER|')) {
        elements=traderElements().map(row=>row.element);
      } else if (signature.startsWith('LIGHTS|')) {
        elements=getLightsBoard().filter(Boolean).map(cell=>cell.element).filter(Boolean);
      } else {
        return false;
      }

      const foreground=elements.some(autoMapElementIsForeground);
      if (!foreground && treasureGuideScreenVisible()) {
        recordDiagnostic('treasure-auto-map-stale-minigame-dom',{
          revision:HK_TREASURE_AUTO_MAP_FOREGROUND_TRUTH_REV,
          signature:signature.slice(0,180),
          elements:elements.length,
          activeCells:autoMapActiveCellCount()
        });
      }
      return foreground;
    }
"""
rep(old,new,"foreground truth")

rep("      treasureAutoMapHandoffRevision:HK_TREASURE_AUTO_MAP_HANDOFF_REV,\n      start,",
    "      treasureAutoMapHandoffRevision:HK_TREASURE_AUTO_MAP_HANDOFF_REV,\n      treasureAutoMapForegroundTruthRevision:HK_TREASURE_AUTO_MAP_FOREGROUND_TRUTH_REV,\n      start,",
    "export revision")

for marker in [
    "// @version      1.18.22",
    "const BUILD_VERSION = '1.18.22';",
    "treasure-auto-map-foreground-truth-20260926-r7",
    "function autoMapElementIsForeground(element)",
    "document.elementFromPoint(px,py)",
    "treasure-auto-map-stale-minigame-dom",
    "treasure-auto-map-foreground-handoff-20260926-r6",
    "treasure-auto-map-active-priority-20260926-r5"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("TREASURE_AUTO_MAP_FOREGROUND_TRUTH_1_18_22=PASS")
