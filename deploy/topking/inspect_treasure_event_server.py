import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    row=db.execute("""SELECT id,payload_json FROM treasure_guide_captures
                      WHERE path='/shop/view' AND payload_json<>''
                      ORDER BY id DESC LIMIT 1""").fetchone()

raw=str(row["payload_json"] or "")
print("SHOP_CAPTURE",row["id"],"LEN",len(raw))
start=raw.find('"shop_lots":[')
print("SHOP_LOTS_START",start)
if start<0: raise SystemExit(0)
arr_start=raw.find('[',start)

objs=[]
i=arr_start+1
n=len(raw)
while i<n:
    while i<n and raw[i] in " \r\n\t,": i+=1
    if i>=n or raw[i]!= '{': break
    obj_start=i
    depth=0; in_str=False; esc=False
    j=i
    while j<n:
        ch=raw[j]
        if in_str:
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch=='"': in_str=False
        else:
            if ch=='"': in_str=True
            elif ch=='{': depth+=1
            elif ch=='}':
                depth-=1
                if depth==0:
                    text=raw[obj_start:j+1]
                    try:
                        obj=json.loads(text); objs.append(obj)
                    except Exception as e:
                        print("OBJ_PARSE_ERROR",obj_start,j,repr(e))
                    i=j+1
                    break
        j+=1
    else:
        break

print("PARSED_LOTS",len(objs))
pattern=re.compile(r"treasure|treasury|minigame_(?:trader|fishing|fight|chests)|pet_skill|golden_berry",re.I)
rel=[o for o in objs if pattern.search(str(o.get("id") or ""))]
print("RELEVANT_COUNT",len(rel))
for o in rel:
    print("LOT",json.dumps(o,ensure_ascii=False,separators=(",",":"))[:12000])
