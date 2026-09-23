import importlib.util, json, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("SELECT id,path,page_text FROM treasure_guide_captures WHERE page_text<>'' ORDER BY id")]

splus=[]
modals=[]
for r in rows:
    text=re.sub(r"\\s+"," ",str(r.get("page_text") or "")).strip()
    if "СОДЕРЖИТ" in text and re.search(r"·\\s*S\\+",text):
        pos=text.rfind("HK")
        splus.append({"id":r["id"],"text":text[pos+2:] if pos>=0 else text})
    if "Понятно" in text and len(text)<2200:
        pos=text.rfind("HK")
        tail=text[pos+2:] if pos>=0 else text
        if len(tail)<1400:
            modals.append({"id":r["id"],"text":tail})
print("SPLUS",json.dumps(splus[-40:],ensure_ascii=False))
print("MODALS",json.dumps(modals[-120:],ensure_ascii=False))
