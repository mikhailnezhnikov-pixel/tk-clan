import importlib.util, json, re, time
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

since=int(time.time())-3*3600
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""
      SELECT id,path,payload_json,page_text,captured_at
      FROM treasure_guide_captures
      WHERE captured_at>=?
      ORDER BY id DESC LIMIT 900
    """,(since,))]

terms=["Сундук победителя","сундук победителя","victory chest","winner chest","mf_treasurelot_","fight"]
for r in rows:
    raw=str(r.get("payload_json") or "")
    txt=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
    low=(raw+" "+txt).lower()
    if not any(t.lower() in low for t in terms[:4]) and "mf_treasurelot_" not in raw:
        continue
    if any(t.lower() in low for t in terms[:4]):
        print("CAP",r["id"],r["captured_at"],r["path"],"payload",len(raw),"text",len(txt))
        if txt:
            for term in terms[:4]:
                p=txt.lower().find(term.lower())
                if p>=0:
                    print("TXT",txt[max(0,p-1200):p+5000]); break
        if raw:
            for term in terms[:4]:
                p=raw.lower().find(term.lower())
                if p>=0:
                    print("RAW",raw[max(0,p-3000):p+10000].replace("\n"," ")[:13000]); break
    # Also inspect likely battle-complete lot ids in recent state.
    if "mf_treasurelot_" in raw:
        ids=sorted(set(re.findall(r'mf_treasurelot_[a-zA-Z0-9_]+',raw)))
        interesting=[x for x in ids if any(k in x for k in ("chest","winner","victory","reward","finish","complete","sword","enemy"))]
        if interesting:
            print("IDS",r["id"],r["captured_at"],r["path"],json.dumps(interesting,ensure_ascii=False))
