from pathlib import Path

PATH=Path("/tmp/HamsterKingMobile.user.js")
s=PATH.read_text(encoding="utf-8")
MARKER="treasure-guide-priority-lots-20260923-r1"

if MARKER in s:
    print("TREASURE_PRIORITY_LOTS_ALREADY_PRESENT")
    raise SystemExit(0)

for required in [
    "// @version      1.17.52",
    "const BUILD_VERSION = '1.17.52';",
    "treasure-guide-selective-extract-20260923-r2",
    "function treasureGuideSendSelective(path,body)",
]:
    if required not in s:
        raise SystemExit("missing marker: "+required)

s=s.replace("// @version      1.17.52","// @version      1.17.53",1)
s=s.replace("const BUILD_VERSION = '1.17.52';","const BUILD_VERSION = '1.17.53';",1)

release_pos=s.find("// @release-note ")
if release_pos>=0:
    s=s[:release_pos]+"// @release-note Карта Сокровищ: приоритетно сохраняются полные lot-объекты сундуков и трёх путей сокровищницы из уже загруженного /shop/view без новых запросов к игре.\n"+s[release_pos:]

anchor="  function treasureGuideSendSelective(path,body) {\n"
helper=r'''  const HK_TREASURE_GUIDE_PRIORITY_LOTS_REV='treasure-guide-priority-lots-20260923-r1';

  function treasureGuidePriorityRows(path,body) {
    if(path!=='/shop/view'||!Array.isArray(body?.shop_lots))return [];
    const rows=[];
    const wanted=/^(?:mf_fair_treasury_room_choose_way_[123]|mf_treasurelot_chest_type_(?:01|015|02|03)|mf_treasurelot_chest_digging_spot_sl[4-9])$/;
    for(let i=0;i<body.shop_lots.length;i++){
      const lot=body.shop_lots[i];
      if(!lot||typeof lot!=='object'||!wanted.test(String(lot.id||'')))continue;
      rows.push({path:'$.shop_lots['+i+']',payload:lot});
    }
    return rows;
  }

'''
if anchor not in s:
    raise SystemExit("treasureGuideSendSelective anchor missing")
s=s.replace(anchor,helper+anchor,1)

old="    const rows=treasureGuideCompactObject(body);\n    if(!rows.length)return;\n"
new="    const priorityRows=treasureGuidePriorityRows(path,body);\n    const rows=[...priorityRows,...treasureGuideCompactObject(body)];\n    if(!rows.length)return;\n"
if old not in s:
    raise SystemExit("selective rows anchor missing")
s=s.replace(old,new,1)

for marker in [
    "// @version      1.17.53",
    "const BUILD_VERSION = '1.17.53';",
    "HK_TREASURE_GUIDE_PRIORITY_LOTS_REV='treasure-guide-priority-lots-20260923-r1'",
    "const priorityRows=treasureGuidePriorityRows(path,body);",
]:
    if marker not in s:
        raise SystemExit("post-patch marker missing: "+marker)

PATH.write_text(s,encoding="utf-8")
print("TREASURE_PRIORITY_LOTS_1_17_53=PASS")
