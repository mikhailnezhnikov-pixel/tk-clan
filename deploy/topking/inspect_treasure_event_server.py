import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,page_text FROM treasure_guide_captures
                                        WHERE page_text<>'' ORDER BY id""")]

out=[]
for r in rows:
    text=re.sub(r"\s+"," ",str(r["page_text"] or "")).strip()
    if "Питомцы" not in text or "Понятно" not in text:
        continue
    # Take the final modal-like tail after last HK marker or last section name.
    pos=text.rfind(" HK ")
    tail=text[pos+4:] if pos>=0 else text[-2200:]
    if len(tail)>2200: tail=tail[-2200:]
    out.append({"id":r["id"],"tail":tail})
print("PET_MODAL_TAILS",json.dumps(out,ensure_ascii=False))
