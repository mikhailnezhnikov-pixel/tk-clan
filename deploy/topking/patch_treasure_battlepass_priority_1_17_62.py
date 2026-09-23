from pathlib import Path

PATH=Path("/tmp/HamsterKingMobile.user.js")
s=PATH.read_text(encoding="utf-8")
MARKER="treasure-guide-priority-battlepass-lines-20260923-r1"

if MARKER in s:
    print("TREASURE_BATTLEPASS_PRIORITY_ALREADY_PRESENT")
    raise SystemExit(0)

for required in [
    "// @version      1.17.61",
    "const BUILD_VERSION = '1.17.61';",
    "treasure-guide-priority-lots-20260923-r1",
    "treasure-guide-priority-trader-lots-20260923-r1",
    "function treasureGuidePriorityRows(path,body)",
]:
    if required not in s:
        raise SystemExit("missing marker: "+required)

s=s.replace("// @version      1.17.61","// @version      1.17.62",1)
s=s.replace("const BUILD_VERSION = '1.17.61';","const BUILD_VERSION = '1.17.62';",1)

pos=s.find("// @release-note ")
if pos>=0:
    s=s[:pos]+"// @release-note Карта Сокровищ: определения трёх линеек наград приоритетно сохраняются из уже загруженных данных события без дополнительных запросов к игре.\n"+s[pos:]

anchor="  const HK_TREASURE_GUIDE_PRIORITY_TRADER_REV='treasure-guide-priority-trader-lots-20260923-r1';\n"
insert=anchor+"  const HK_TREASURE_GUIDE_PRIORITY_BATTLEPASS_REV='treasure-guide-priority-battlepass-lines-20260923-r1';\n"
if anchor not in s:
    raise SystemExit("priority trader anchor missing")
s=s.replace(anchor,insert,1)

old="""  function treasureGuidePriorityRows(path,body) {
    if(path!=='/shop/view'||!Array.isArray(body?.shop_lots))return [];
    const rows=[];
    const wanted=/^(?:mf_fair_treasury_room_choose_way_[123]|mf_treasurelot_chest_type_(?:01|015|02|03)|mf_treasurelot_chest_digging_spot_sl[4-9]|mf_fairlot_minigame_trader_(?:01|02|03)_.+|mf_treasurelot_trader_type_(?:01|02|03)_active_rep_5)$/;
    for(let i=0;i<body.shop_lots.length;i++){
      const lot=body.shop_lots[i];
      if(!lot||typeof lot!=='object'||!wanted.test(String(lot.id||'')))continue;
      rows.push({path:'$.shop_lots['+i+']',payload:lot});
    }
    return rows;
  }
"""
new="""  function treasureGuidePriorityRows(path,body) {
    const rows=[];
    if(path==='/shop/view'&&Array.isArray(body?.shop_lots)){
      const wanted=/^(?:mf_fair_treasury_room_choose_way_[123]|mf_treasurelot_chest_type_(?:01|015|02|03)|mf_treasurelot_chest_digging_spot_sl[4-9]|mf_fairlot_minigame_trader_(?:01|02|03)_.+|mf_treasurelot_trader_type_(?:01|02|03)_active_rep_5)$/;
      for(let i=0;i<body.shop_lots.length;i++){
        const lot=body.shop_lots[i];
        if(!lot||typeof lot!=='object'||!wanted.test(String(lot.id||'')))continue;
        rows.push({path:'$.shop_lots['+i+']',payload:lot});
      }
    }
    if(path==='/client_config'||path==='/battlepass'){
      const wantedIds=new Set(['bp_event_minigame','bp_event_minigame_line_free','bp_event_minigame_line_paid_01','bp_event_minigame_line_paid_02']);
      const stack=[['$',body]];
      const seen=new WeakSet();
      while(stack.length){
        const [p,v]=stack.pop();
        if(!v||typeof v!=='object')continue;
        if(seen.has(v))continue;
        seen.add(v);
        if(!Array.isArray(v)&&wantedIds.has(String(v.id||''))){
          try{
            const text=JSON.stringify(v);
            if(text.length<=44000)rows.push({path:p,payload:v});
          }catch(_){}
        }
        if(Array.isArray(v)){
          for(let i=0;i<v.length;i++)if(v[i]&&typeof v[i]==='object')stack.push([p+'['+i+']',v[i]]);
        }else{
          for(const k of Object.keys(v)){
            const child=v[k];
            if(child&&typeof child==='object')stack.push([p+'.'+k,child]);
          }
        }
      }
    }
    return rows;
  }
"""
if old not in s:
    raise SystemExit("priority function exact block missing")
s=s.replace(old,new,1)

for marker in [
    "// @version      1.17.62",
    "const BUILD_VERSION = '1.17.62';",
    "HK_TREASURE_GUIDE_PRIORITY_BATTLEPASS_REV='treasure-guide-priority-battlepass-lines-20260923-r1'",
    "wantedIds=new Set(['bp_event_minigame','bp_event_minigame_line_free','bp_event_minigame_line_paid_01','bp_event_minigame_line_paid_02'])",
]:
    if marker not in s:
        raise SystemExit("post-patch marker missing: "+marker)

PATH.write_text(s,encoding="utf-8")
print("TREASURE_BATTLEPASS_PRIORITY_1_17_62=PASS")
