#!/usr/bin/env python3
import collections
import datetime
import gzip
import hashlib
import importlib.util
import json
import lzma
import os
from pathlib import Path
import sqlite3
import time

DB_PATH="/var/lib/hamsterking-license/licenses.db"
SERVER_PATH="/opt/hamsterking-license/server.py"
IDS_PATH="/tmp/full235-allids.bin.gz"
ATTRS_PATH="/tmp/full235-attrs2.bin.xz"
ORIGINAL75_PATH="/tmp/full235-original75.json"

IDS_GZ_SHA="470737a9007d45c1e770b422c9a6d507f610225d28bf281863c03b0cd558b411"
IDS_RAW_SHA="1ddcadbb50e5a88555a6772538e56476575a771edc22fb85200299c8cbc28f48"
ATTRS_XZ_SHA="5c1c71cfe4bc620f13524324ecf275ca927575c2d96e2b59cfdb98e21e3eeb9d"
ATTRS_RAW_SHA="728d33fbc57105109cd67f3b46de61d27bc2c4c597b9b88012952c0ad3cf0dbf"
SEMANTIC_SHA="e7c5ea74657289f09bc69049b5e05abf5b5cb3ca577f7d63d67342eccde8f594"
ARCHIVE_SHA="a4b84c5239168182702090efe0b7241b54295942d63e5f020539092694e0a3e1"
EXPORTED_AT="2026-09-19T10:34:26.478Z"
EXPECTED_FACTIONS=["blue","brown","green","khaki","orange","red","turquoise","violet"]
EXPECTED_GENERATORS=[
 "gen_apartment_large","gen_apartment_mandatory","gen_apartment_small",
 "gen_culture_large","gen_culture_mandatory","gen_culture_small",
 "gen_healthcare_large","gen_healthcare_mandatory","gen_healthcare_small",
 "gen_industry_large","gen_industry_mandatory","gen_industry_small",
 "gen_other_apartment_large","gen_other_apartment_small",
 "gen_other_culture_large","gen_other_culture_small",
 "gen_other_healthcare_large","gen_other_healthcare_small",
 "gen_other_industry_large","gen_other_industry_small",
 "gen_other_large","gen_other_police_large","gen_other_police_small",
 "gen_other_small","gen_police_large","gen_police_mandatory","gen_police_small",
 "gen_unique_bar","gen_unique_bar_large","gen_unique_casino",
 "gen_unique_casino_large","gen_unique_factory","gen_unique_factory_large",
 "gen_unique_hospital","gen_unique_hospital_large"
]
EXPECTED_CRYSTALS={None:54023,0:72604,1:18540,2:6270,3:1104,4:51,5:1}
EXPECTED_INVEST=1542

def sha_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def read_varint(buf,pos):
    n=0; shift=0
    while True:
        if pos>=len(buf): raise RuntimeError("truncated varint")
        b=buf[pos]; pos+=1
        n |= (b & 0x7f) << shift
        if not (b & 0x80): return n,pos
        shift += 7
        if shift>63: raise RuntimeError("varint too long")

def read_lp_string(buf,pos):
    n,pos=read_varint(buf,pos)
    end=pos+n
    if end>len(buf): raise RuntimeError("truncated string")
    return buf[pos:end].decode("utf-8"),end

def decode_ids():
    assert sha_file(IDS_PATH)==IDS_GZ_SHA
    raw=gzip.open(IDS_PATH,"rb").read()
    assert hashlib.sha256(raw).hexdigest()==IDS_RAW_SHA
    assert raw[:5]==b"HKID1"
    pos=5; source={}
    while pos<len(raw):
        n,pos=read_varint(raw,pos)
        key=raw[pos:pos+n].decode(); pos+=n
        if key in source: raise RuntimeError("duplicate source map "+key)
        ids=[]
        for prefix in ("way","relation"):
            count,pos=read_varint(raw,pos)
            prev=0
            for _ in range(count):
                delta,pos=read_varint(raw,pos); prev+=delta
                ids.append(prefix+str(prev))
        source[key]=ids
    assert len(source)==235
    assert list(source)==sorted(source), "HKID1 map order must be sorted"
    assert sum(map(len,source.values()))==152593
    union=set()
    for ids in source.values():
        for bid in ids:
            if bid in union: raise RuntimeError("duplicate source building "+bid)
            union.add(bid)
    assert len(union)==152593
    return source,union

def decode_attrs(source):
    assert sha_file(ATTRS_PATH)==ATTRS_XZ_SHA
    raw=lzma.decompress(Path(ATTRS_PATH).read_bytes())
    assert len(raw)==306001
    assert hashlib.sha256(raw).hexdigest()==ATTRS_RAW_SHA
    assert raw[:4]==b"HKA2"
    pos=4
    nf,pos=read_varint(raw,pos)
    factions=[]
    for _ in range(nf):
        s,pos=read_lp_string(raw,pos); factions.append(s)
    ng,pos=read_varint(raw,pos)
    generators=[]
    for _ in range(ng):
        s,pos=read_lp_string(raw,pos); generators.append(s)
    assert factions==EXPECTED_FACTIONS,(factions,EXPECTED_FACTIONS)
    assert generators==EXPECTED_GENERATORS,(generators,EXPECTED_GENERATORS)
    count,pos=read_varint(raw,pos)
    assert count==152593,count
    assert len(raw)-pos==count*2,(len(raw),pos,count)
    meta=raw[pos:pos+count]
    genplane=raw[pos+count:]
    rows_by_map={}
    crystals=collections.Counter()
    invest=0
    semantic=hashlib.sha256()
    i=0
    for key in sorted(source):
        rows=[]
        for bid in source[key]:
            b=meta[i]; gi=genplane[i]; i+=1
            fi=(b>>4)&0x0f
            inv=bool(b&0x08)
            cc=b&0x07
            if fi>=len(factions) or gi>=len(generators) or cc==6:
                raise RuntimeError(("invalid attrs code",key,bid,b,gi))
            room=None if cc==7 else int(cc)
            faction=factions[fi]
            generator=generators[gi]
            crystals[room]+=1
            invest+=int(inv)
            fields=[key,bid,"N" if room is None else str(room),"1" if inv else "0",faction,generator]
            semantic.update(("\0".join(fields)+"\n").encode())
            rows.append([bid,room,inv,faction,generator])
        rows_by_map[key]=rows
    assert i==count
    assert dict(crystals)==EXPECTED_CRYSTALS,(crystals,EXPECTED_CRYSTALS)
    assert invest==EXPECTED_INVEST,invest
    assert semantic.hexdigest()==SEMANTIC_SHA,semantic.hexdigest()
    print("FULL235_COMPACT_SEMANTICS=PASS")
    return rows_by_map

def table_exists(db,name):
    return bool(db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(name,)).fetchone())

def alias_resolver(db):
    aliases={str(r["source_area_id"]):str(r["canonical_area_id"]) for r in db.execute(
        "SELECT source_area_id,canonical_area_id FROM map_area_aliases")}
    def canon(a):
        a=str(a or ""); seen=set()
        while a in aliases and aliases[a]!=a and a not in seen:
            seen.add(a); a=aliases[a]
        return a
    return canon

def terminal_verify(source,original75,expected_targets=None):
    db=sqlite3.connect("file:"+DB_PATH+"?mode=ro",uri=True); db.row_factory=sqlite3.Row
    try:
        areas=db.execute("SELECT COUNT(*) FROM map_areas").fetchone()[0]
        links=db.execute("SELECT COUNT(*) FROM hk_map_area_links").fetchone()[0]
        full_links=db.execute("SELECT COUNT(*) FROM hk_full_map_import_links").fetchone()[0] if table_exists(db,"hk_full_map_import_links") else 0
        if links!=235 or full_links!=235:
            return None
        canon=alias_resolver(db)
        linkmap={str(r["map_key"]):canon(r["canonical_area_id"]) for r in db.execute(
            "SELECT map_key,canonical_area_id FROM hk_map_area_links")}
        if set(linkmap)!=set(source): raise RuntimeError("terminal map-link key mismatch")
        for key,area_id in original75.items():
            if linkmap.get(key)!=canon(area_id):
                raise RuntimeError(("terminal original75 link mismatch",key,linkmap.get(key),area_id))
            if not db.execute("SELECT 1 FROM map_areas WHERE area_id=?",(area_id,)).fetchone():
                raise RuntimeError(("terminal original75 area missing",key,area_id))
        if expected_targets:
            for key,target in expected_targets.items():
                if linkmap.get(key)!=canon(target):
                    raise RuntimeError(("terminal target mismatch",key,linkmap.get(key),target))
        if areas!=385:
            raise RuntimeError(("terminal canonical area count",areas))
        return {"areas":areas,"area_links":links,"full_import_links":full_links,
                "buildings":db.execute("SELECT COUNT(*) FROM map_buildings").fetchone()[0]}
    finally:
        db.close()

def exact_preflight(source,union,original75):
    db=sqlite3.connect("file:"+DB_PATH+"?mode=ro",uri=True); db.row_factory=sqlite3.Row
    try:
        assert db.execute("SELECT COUNT(*) FROM hk_maps_catalog").fetchone()[0]==235
        canon=alias_resolver(db)
        bid_areas={}
        ids=sorted(union)
        for start in range(0,len(ids),700):
            part=ids[start:start+700]
            q=",".join("?" for _ in part)
            for r in db.execute(f"SELECT building_id,area_id FROM map_buildings WHERE building_id IN ({q})",part):
                bid_areas.setdefault(str(r["building_id"]),set()).add(canon(r["area_id"]))
        links={str(r["map_key"]):canon(r["canonical_area_id"]) for r in db.execute(
            "SELECT map_key,canonical_area_id FROM hk_map_area_links")}
        exact={}; new={}; conflicts=[]
        for key in sorted(source):
            counts=collections.Counter()
            for bid in source[key]:
                owners=bid_areas.get(bid,set())
                if len(owners)>1:
                    conflicts.append((key,"building_multiple",bid,sorted(owners))); break
                for aid in owners: counts[aid]+=1
            if conflicts and conflicts[-1][0]==key: continue
            if len(counts)==1:
                area_id,_=next(iter(counts.items()))
                if links.get(key)!=area_id:
                    conflicts.append((key,"existing_link_mismatch",links.get(key),area_id))
                else: exact[key]=area_id
            elif len(counts)==0:
                target=original75.get(key)
                if not target:
                    conflicts.append((key,"no_original75")); continue
                target=canon(target)
                area=db.execute("SELECT 1 FROM map_areas WHERE area_id=?",(target,)).fetchone()
                alias=db.execute("SELECT canonical_area_id FROM map_area_aliases WHERE source_area_id=?",(target,)).fetchone()
                linked=links.get(key)
                if area or alias or linked:
                    conflicts.append((key,"original_not_free",bool(area),bool(alias),linked))
                else: new[key]=target
            else:
                conflicts.append((key,"multiple_overlaps",counts.most_common(5)))
        if conflicts: raise RuntimeError(("FULL235 preflight conflicts",conflicts[:10]))
        assert len(exact)==160,(len(exact),len(new))
        assert len(new)==75,(len(exact),len(new))
        assert len(links)==160,len(links)
        assert set(new)==set(original75)
        assert db.execute("SELECT COUNT(*) FROM map_areas").fetchone()[0]==310
        if table_exists(db,"hk_full_map_import_links"):
            assert db.execute("SELECT COUNT(*) FROM hk_full_map_import_links").fetchone()[0]==0
        if table_exists(db,"hk_full_import_stage"):
            assert db.execute("SELECT COUNT(*) FROM hk_full_import_stage").fetchone()[0]==0
        catalog={str(r["map_key"]):(str(r["city"]),str(r["grid"])) for r in db.execute(
            "SELECT map_key,city,grid FROM hk_maps_catalog")}
        assert set(catalog)==set(source),(len(catalog),len(source))
        print("FULL235_PREWRITE_MATCH=PASS")
        return {**exact,**new},catalog
    finally:
        db.close()

def source_game_live_signature(union):
    db=sqlite3.connect("file:"+DB_PATH+"?mode=ro",uri=True); db.row_factory=sqlite3.Row
    try:
        canon=alias_resolver(db)
        rows=[]
        ids=sorted(union)
        for start in range(0,len(ids),700):
            part=ids[start:start+700]
            q=",".join("?" for _ in part)
            for r in db.execute(f"""SELECT area_id,building_id,room_count,has_events,last_player_id,
                    knowledge_source,knowledge_observed_at
                    FROM map_buildings WHERE building_id IN ({q})
                    AND knowledge_source='game_live' AND room_count IS NOT NULL""",part):
                rows.append((str(r["building_id"]),canon(r["area_id"]),r["room_count"],r["has_events"],
                             str(r["last_player_id"] or ""),str(r["knowledge_source"] or ""),
                             r["knowledge_observed_at"]))
        rows.sort(key=lambda x:(x[0],x[1]))
        h=hashlib.sha256()
        for row in rows:
            h.update((json.dumps(row,separators=(",",":"),ensure_ascii=False)+"\n").encode())
        return len(rows),h.hexdigest()
    finally:
        db.close()

def backup_db():
    stamp=time.strftime("%Y%m%d-%H%M%S",time.gmtime())
    dest=DB_PATH+".bak.full235-prestage."+stamp
    src=sqlite3.connect(DB_PATH)
    dst=sqlite3.connect(dest)
    try:
        src.backup(dst)
    finally:
        dst.close(); src.close()
    if os.path.getsize(dest)<=0: raise RuntimeError("empty backup")
    print("FULL235_PRESTAGE_BACKUP=PASS",dest)
    return dest

def load_server():
    text=Path(SERVER_PATH).read_text(encoding="utf-8")
    for marker in ("HK_FULL235_IMPORT_V1","HK_FULL235_ORIGINAL75_V2","def full235_import_apply"):
        if marker not in text: raise RuntimeError("live importer marker missing: "+marker)
    spec=importlib.util.spec_from_file_location("hk_live_server",SERVER_PATH)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    for name in ("full235_import_start","full235_import_chunk","full235_import_resolve","full235_import_apply"):
        if not hasattr(mod,name): raise RuntimeError("live importer function missing: "+name)
    return mod

def verify_source_ownership(source,targets):
    db=sqlite3.connect("file:"+DB_PATH+"?mode=ro",uri=True); db.row_factory=sqlite3.Row
    try:
        canon=alias_resolver(db)
        ids=[bid for key in sorted(source) for bid in source[key]]
        owner={}
        for start in range(0,len(ids),700):
            part=ids[start:start+700]
            q=",".join("?" for _ in part)
            for r in db.execute(f"SELECT building_id,area_id FROM map_buildings WHERE building_id IN ({q})",part):
                owner.setdefault(str(r["building_id"]),set()).add(canon(r["area_id"]))
        for key in sorted(source):
            target=canon(targets[key])
            for bid in source[key]:
                got=owner.get(bid,set())
                if got!={target}: raise RuntimeError(("source ownership mismatch",key,bid,sorted(got),target))
        assert len(owner)==152593,len(owner)
        print("FULL235_SOURCE_OWNERSHIP=PASS")
    finally:
        db.close()

def main():
    source,union=decode_ids()
    rows_by_map=decode_attrs(source)
    original75=json.load(open(ORIGINAL75_PATH,encoding="utf-8"))
    assert len(original75)==75
    assert set(original75).issubset(source)

    terminal=terminal_verify(source,original75)
    if terminal:
        print("FULL235_ALREADY_APPLIED_SAFE=PASS")
        print("FULL235_TERMINAL_STATE="+json.dumps(terminal,sort_keys=True))
        return

    targets,catalog=exact_preflight(source,union,original75)
    before_live=source_game_live_signature(union)
    print("FULL235_GAME_LIVE_BEFORE="+json.dumps({"rows":before_live[0],"sha256":before_live[1]},sort_keys=True))
    prestage_backup=backup_db()

    s=load_server()
    mgr={"telegram_id":"full235-production-migration","maps_manage":1,"maps_access":1}
    start=s.full235_import_start(mgr,{
        "format":"HK Maps Full Export","version":3,"maps_found":235,"maps_exported":235,
        "errors_count":0,"exported_at":EXPORTED_AT,"archive_sha256":ARCHIVE_SHA})
    batch=start["batch_id"]
    docs=[]
    for key in sorted(source):
        city,grid=catalog[key]
        docs.append({"key":key,"city":city,"grid":grid,"buildings":rows_by_map[key]})
    for i in range(0,len(docs),10):
        result=s.full235_import_chunk(mgr,{"batch_id":batch,"maps":docs[i:i+10]})
        if int(result.get("received_maps",0))!=min(i+10,235):
            raise RuntimeError(("stage count mismatch",i,result))
    print("FULL235_STAGE_235=PASS")

    report=s.full235_import_resolve(mgr,{"batch_id":batch})
    if not report.get("ready_to_apply"):
        raise RuntimeError(("resolver not ready",report.get("status_counts"),report.get("duplicate_targets"),
                            report.get("metadata_mismatches"),report.get("missing_catalog_maps")))
    assert int(report.get("maps_received",0))==235
    assert int(report.get("archive_total_buildings",0))==152593
    assert int(report.get("unique_archive_building_ids",0))==152593
    assert report.get("status_counts")=={"matched_link":160,"new_original":75},report.get("status_counts")
    assert int(report.get("original_area_id_catalog",0))==75
    assert int(report.get("original_area_id_maps_seen",0))==75
    assert not report.get("duplicate_targets")
    print("FULL235_SERVER_RESOLVE=PASS")

    # Resolver targets must equal the independently established targets.
    for item in report.get("maps") or []:
        key=str(item["map_key"]); target=str(item["target_area_id"])
        if targets.get(key)!=target:
            raise RuntimeError(("resolver target mismatch",key,targets.get(key),target))

    try:
        result=s.full235_import_apply(mgr,{"batch_id":batch,"confirm":"IMPORT_235"})
    except Exception as exc:
        # Apply commits before cabinet summary generation. If a post-commit presentation
        # error happens, accept only a fully verified terminal state.
        terminal=terminal_verify(source,original75,targets)
        if not terminal:
            raise
        result={"post_commit_exception":repr(exc),"terminal_recovered":True}
        print("FULL235_POSTCOMMIT_RECOVERY=PASS")

    terminal=terminal_verify(source,original75,targets)
    if not terminal: raise RuntimeError("terminal state not reached")
    assert terminal["areas"]==385
    assert terminal["area_links"]==235
    assert terminal["full_import_links"]==235

    db=sqlite3.connect("file:"+DB_PATH+"?mode=ro",uri=True)
    try:
        if table_exists(db,"hk_full_import_stage"):
            assert db.execute("SELECT COUNT(*) FROM hk_full_import_stage WHERE batch_id=?",(batch,)).fetchone()[0]==0
    finally:
        db.close()
    print("FULL235_STAGE_PURGE=PASS")

    after_live=source_game_live_signature(union)
    if after_live!=before_live:
        raise RuntimeError(("game_live priority regression",before_live,after_live))
    print("FULL235_GAME_LIVE_PRIORITY=PASS")

    verify_source_ownership(source,targets)

    # The same guard used at program start must now recognize the terminal state,
    # proving that a retry will be a no-write safe exit.
    retry_state=terminal_verify(source,original75,targets)
    assert retry_state==terminal
    print("FULL235_IDEMPOTENCY_GATE=PASS")
    print("FULL235_PRESTAGE_BACKUP_PATH="+prestage_backup)
    if isinstance(result,dict) and result.get("backup"):
        print("FULL235_BUILTIN_BACKUP_PATH="+str(result["backup"]))
    print("FULL235_FINAL="+json.dumps(terminal,sort_keys=True))
    print("FULL235_PRODUCTION_APPLY=PASS")

if __name__=="__main__":
    main()
