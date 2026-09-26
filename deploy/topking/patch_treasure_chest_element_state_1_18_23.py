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

rep("// @version      1.18.22",
    "// @version      1.18.23\n// @release-note Сундуки: уже активированные карточки «Активировано/Activated» больше не считаются покупаемой целью даже если у другого слота такой же lotId ещё остался некупленным. После верхних сундуков автомодуль продолжает по реально открывшимся клеткам.",
    "version")
rep("const BUILD_VERSION = '1.18.22';",
    "const BUILD_VERSION = '1.18.23';",
    "build")
rep("  const HK_TREASURE_AUTO_MAP_FOREGROUND_TRUTH_REV='treasure-auto-map-foreground-truth-20260926-r7';",
    "  const HK_TREASURE_AUTO_MAP_FOREGROUND_TRUTH_REV='treasure-auto-map-foreground-truth-20260926-r7';\n  const HK_TREASURE_CHEST_ELEMENT_STATE_REV='treasure-chest-element-state-20260927-r1';",
    "revision")

old_elements="""    function treasureChestElements() {
      const selector='[data-lot-id*="mf_treasurelot_chest_"]';
      return [...document.querySelectorAll(selector)]
        .filter(visible)
        .map(element=>({element,lotId:String(element.getAttribute('data-lot-id')||'')}))
        .filter(row=>row.lotId && !row.lotId.includes('_empty_spot') && !row.lotId.includes('_bought_'));
    }
"""
new_elements="""    function treasureChestElements() {
      const selector='[data-lot-id*="mf_treasurelot_chest_"]';
      return [...document.querySelectorAll(selector)]
        .filter(visible)
        .map(element=>{
          const lotId=String(element.getAttribute('data-lot-id')||'');
          const text=clean(element.innerText||element.textContent||'').trim();
          const activated=/^(?:Активировано|Activated)$/i.test(text)
            || /(?:^|\\s)(?:Активировано|Activated)(?:\\s|$)/i.test(text);
          const rect=element.getBoundingClientRect?.() || {left:0,top:0,width:0,height:0};
          return {
            element,
            lotId,
            text,
            activated,
            x:Math.round(rect.left+rect.width/2),
            y:Math.round(rect.top+rect.height/2)
          };
        })
        .filter(row=>row.lotId && !row.lotId.includes('_empty_spot') && !row.lotId.includes('_bought_'));
    }
"""
rep(old_elements,new_elements,"chest elements")

rep("""          return row.lotId+'@'+Math.round(rect.left)+','+Math.round(rect.top)+'#'+clean(row.element.className||'');
""",
"""          return row.lotId+'@'+Math.round(rect.left)+','+Math.round(rect.top)+'#'+clean(row.element.className||'')+'#'+row.text+'#'+(row.activated?'A':'N');
""",
"signature state")

rep("""      rows.forEach((row,index)=>{
        const lotId=row.lotId;
        const cost=treasureChestCost(lotId);
""",
"""      rows.forEach((row,index)=>{
        const lotId=row.lotId;
        if (row.activated) return;
        const cost=treasureChestCost(lotId);
""",
"exclude activated")

rep("""      candidates.sort((a,b)=>b.priority-a.priority || a.index-b.index);
      return candidates[0] || null;
""",
"""      candidates.sort((a,b)=>b.priority-a.priority || a.index-b.index);
      const selected=candidates[0] || null;
      if (!selected && rows.some(row=>row.activated)) {
        recordDiagnostic('treasure-chest-no-target-after-activated',{
          revision:HK_TREASURE_CHEST_ELEMENT_STATE_REV,
          activated:rows.filter(row=>row.activated).map(row=>({
            lotId:row.lotId,
            text:row.text,
            x:row.x,
            y:row.y
          })).slice(0,12),
          visible:rows.map(row=>({
            lotId:row.lotId,
            text:row.text,
            activated:row.activated,
            x:row.x,
            y:row.y
          })).slice(0,24)
        });
      }
      return selected;
""",
"diagnostic no target")

rep("      treasureAutoMapForegroundTruthRevision:HK_TREASURE_AUTO_MAP_FOREGROUND_TRUTH_REV,\n      start,",
    "      treasureAutoMapForegroundTruthRevision:HK_TREASURE_AUTO_MAP_FOREGROUND_TRUTH_REV,\n      treasureChestElementStateRevision:HK_TREASURE_CHEST_ELEMENT_STATE_REV,\n      start,",
    "export revision")

for marker in [
    "// @version      1.18.23",
    "const BUILD_VERSION = '1.18.23';",
    "treasure-chest-element-state-20260927-r1",
    "if (row.activated) return;",
    "treasure-chest-no-target-after-activated",
    "row.text+'#'+(row.activated?'A':'N')",
    "treasure-auto-map-foreground-truth-20260926-r7"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("TREASURE_CHEST_ELEMENT_STATE_1_18_23=PASS")
