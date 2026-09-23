from pathlib import Path

PATH=Path("/tmp/HamsterKingMobile.user.js")
s=PATH.read_text(encoding="utf-8")
MARKER="treasure-guide-selective-extract-20260923-r2"

if MARKER in s:
    print("TREASURE_GUIDE_SELECTIVE_EXTRACT_ALREADY_PRESENT")
    raise SystemExit(0)

for required in [
    "// @version      1.17.40",
    "const BUILD_VERSION = '1.17.40';",
    "treasure-guide-passive-capture-20260923-r1",
    "function acceptTreasureGuideApi(url,body)",
]:
    if required not in s:
        raise SystemExit("missing marker: "+required)

s=s.replace("// @version      1.17.40","// @version      1.17.41",1)
s=s.replace("const BUILD_VERSION = '1.17.40';","const BUILD_VERSION = '1.17.41';",1)

release="// @release-note Hamsters: выровнен cost-parity с закреплённым Kokkaras donor — бюджет по-прежнему считается по Орехам, но допустимые дополнительные non-premium/non-hard компоненты стоимости больше не отбрасываются."
s=s.replace(
    release,
    "// @release-note Карта Сокровищ: крупные ответы /quests, /shop/view и /client_config теперь дополнительно режутся на компактные treasure-only срезы без новых запросов к игре.\n"+release,
    1
)

anchor="  function acceptTreasureGuideApi(url,body) {\n"
helper=r'''  const HK_TREASURE_GUIDE_SELECTIVE_REV='treasure-guide-selective-extract-20260923-r2';

  function treasureGuideLooksRelevant(value) {
    return /treasure|treasurehunt|minigame|event_treasures|fair_treasures|pet_mission|golden_berry|карта.{0,16}сокровищ|сокровищ/i.test(String(value||''));
  }

  function treasureGuideCompactObject(value,path='$',out=[],seen=new Set(),depth=0) {
    if(!value||typeof value!=='object'||seen.has(value)||depth>14||out.length>=700)return out;
    seen.add(value);
    if(Array.isArray(value)){
      for(let i=0;i<value.length&&i<2500&&out.length<700;i++)treasureGuideCompactObject(value[i],path+'['+i+']',out,seen,depth+1);
      return out;
    }
    let scalarText='';
    const keys=Object.keys(value);
    for(const key of keys){
      const item=value[key];
      if(item==null||typeof item==='string'||typeof item==='number'||typeof item==='boolean'){
        scalarText+=' '+key+' '+String(item);
      }
    }
    if(treasureGuideLooksRelevant(keys.join(' ')+' '+scalarText)){
      let payload=null;
      try{
        const full=JSON.stringify(value);
        if(full.length<=18000)payload=value;
      }catch(_){}
      if(!payload){
        payload={};
        for(const key of keys){
          const item=value[key];
          if(item==null||typeof item==='string'||typeof item==='number'||typeof item==='boolean'){
            payload[key]=item;
          }else if(Array.isArray(item)&&item.length<=20&&item.every(v=>v==null||['string','number','boolean'].includes(typeof v))){
            payload[key]=item;
          }else if(item&&typeof item==='object'&&!Array.isArray(item)){
            try{
              const text=JSON.stringify(item);
              if(text.length<=5000)payload[key]=item;
            }catch(_){}
          }
        }
      }
      out.push({path,payload});
    }
    for(const key of keys){
      const item=value[key];
      if(item&&typeof item==='object')treasureGuideCompactObject(item,path+'.'+key,out,seen,depth+1);
      if(out.length>=700)break;
    }
    return out;
  }

  function treasureGuideSendSelective(path,body) {
    if(!['/quests','/shop/view','/client_config','/items','/events'].includes(path) &&
       !path.startsWith('/battlepass') &&
       !path.startsWith('/fair/'))return;
    const rows=treasureGuideCompactObject(body);
    if(!rows.length)return;
    let chunk=[],size=2,index=1;
    const flush=()=>{
      if(!chunk.length)return;
      const payloadJson=JSON.stringify({source_path:path,rows:chunk});
      const key='api-selective:'+path+':'+index+':'+treasureGuideHash(payloadJson);
      void treasureGuideSubmit({
        capture_key:key,
        source:'api',
        path:path+'#treasure-'+index,
        payload_json:payloadJson,
        page_text:'',
        assets:treasureGuideScreenVisible()?treasureGuideAssetUrls():[]
      });
      index+=1;chunk=[];size=2;
    };
    for(const row of rows){
      let text='';
      try{text=JSON.stringify(row);}catch(_){continue;}
      if(text.length>45000)continue;
      if(size+text.length+1>185000)flush();
      chunk.push(row);size+=text.length+1;
    }
    flush();
  }

'''
if anchor not in s:
    raise SystemExit("acceptTreasureGuideApi anchor missing")
s=s.replace(anchor,helper+anchor,1)

old="""    const payloadJson=treasureGuidePayloadText(body);
    if(!treasureGuideApiRelevant(path,payloadJson))return;
"""
new="""    const payloadJson=treasureGuidePayloadText(body);
    treasureGuideSendSelective(path,body);
    if(!treasureGuideApiRelevant(path,payloadJson))return;
"""
if old not in s:
    raise SystemExit("api capture body missing")
s=s.replace(old,new,1)

for marker in [
    "// @version      1.17.41",
    "const BUILD_VERSION = '1.17.41';",
    "HK_TREASURE_GUIDE_SELECTIVE_REV='treasure-guide-selective-extract-20260923-r2'",
    "treasureGuideSendSelective(path,body);",
]:
    if marker not in s:
        raise SystemExit("post-patch marker missing: "+marker)

PATH.write_text(s,encoding="utf-8")
print("TREASURE_GUIDE_SELECTIVE_EXTRACT_1_17_41=PASS")
