#!/usr/bin/env python3
import json
import sqlite3
import time
import urllib.error
import urllib.request

DB="/var/lib/hamsterking-license/licenses.db"
PUBLIC="https://hk-license.89.125.1.71.sslip.io"
SITE="https://tk-clan.ru"
KINDS=("influence","power","clans","alliance_power","alliance_influence","alliance_defense")

def yes(v):
    return "yes" if bool(v) else "no"

def get_json(url):
    req=urllib.request.Request(
        url,
        headers={
            "Accept":"application/json",
            "Origin":SITE,
            "User-Agent":"TopKing-Public-E2E-Check/1",
        },
        method="GET",
    )
    with urllib.request.urlopen(req,timeout=25) as response:
        body=json.loads(response.read(2_000_000).decode("utf-8"))
        return int(response.status),body,response.headers.get("Access-Control-Allow-Origin","")

def get_text(url):
    req=urllib.request.Request(
        url,
        headers={"Accept":"text/html","User-Agent":"TopKing-Public-E2E-Check/1"},
        method="GET",
    )
    with urllib.request.urlopen(req,timeout=25) as response:
        return int(response.status),response.read(2_000_000).decode("utf-8","replace")

now=int(time.time())
db=sqlite3.connect(DB)
db.row_factory=sqlite3.Row

war_row=db.execute(
    "SELECT snapshot_json,updated_at FROM public_clan_war_snapshot WHERE singleton=1"
).fetchone()
db_war_updated=int(war_row["updated_at"] or 0) if war_row else 0
db_war_active=False
if war_row:
    try:
        db_war_active=bool(json.loads(war_row["snapshot_json"] or "{}"))
    except Exception:
        pass

print("e2e_revision=PUBLIC_OUTPUT_E2E_R1")
print("db_war_present="+yes(war_row))
print("db_war_active="+yes(db_war_active))
print("db_war_age_seconds="+str(max(0,now-db_war_updated) if db_war_updated else 0))

war_status,war_doc,war_cors=get_json(PUBLIC+"/api/v1/public/clan-war")
api_war_updated=int(war_doc.get("updated_at") or 0) if isinstance(war_doc,dict) else 0
print("api_war_status="+str(war_status))
print("api_war_ok="+yes(isinstance(war_doc,dict) and war_doc.get("ok")))
print("api_war_active="+yes(isinstance(war_doc,dict) and war_doc.get("active")))
print("api_war_stale="+yes(isinstance(war_doc,dict) and war_doc.get("stale")))
print("api_war_cors_site="+yes(war_cors==SITE))
print("api_war_matches_db_updated_at="+yes(api_war_updated==db_war_updated and api_war_updated>0))
print("api_war_age_seconds="+str(max(0,now-api_war_updated) if api_war_updated else 0))

ratings_all_ok=True
for kind in KINDS:
    row=db.execute(
        "SELECT COUNT(*) AS n,MAX(updated_at) AS updated_at FROM public_rating_snapshots WHERE kind=?",
        (kind,),
    ).fetchone()
    db_count=int(row["n"] or 0)
    db_updated=int(row["updated_at"] or 0)
    status,doc,cors=get_json(PUBLIC+"/api/v1/public/ratings?kind="+kind)
    rows=doc.get("rows") if isinstance(doc,dict) and isinstance(doc.get("rows"),list) else []
    api_updated=int(doc.get("updated_at") or 0) if isinstance(doc,dict) else 0
    ranks=[]
    for item in rows:
        try:
            ranks.append(int(item.get("rank")))
        except Exception:
            pass
    sorted_unique=(ranks==sorted(ranks) and len(ranks)==len(set(ranks)))
    kind_ok=(
        status==200
        and bool(doc.get("ok"))
        and db_count>0
        and len(rows)==db_count
        and api_updated==db_updated
        and api_updated>0
        and sorted_unique
        and cors==SITE
    )
    ratings_all_ok=ratings_all_ok and kind_ok
    print("rating_"+kind+"_status="+str(status))
    print("rating_"+kind+"_db_count="+str(db_count))
    print("rating_"+kind+"_api_count="+str(len(rows)))
    print("rating_"+kind+"_matches_db="+yes(len(rows)==db_count and api_updated==db_updated and db_count>0))
    print("rating_"+kind+"_ranks_sorted_unique="+yes(sorted_unique))
    print("rating_"+kind+"_cors_site="+yes(cors==SITE))
    print("rating_"+kind+"_stale="+yes(doc.get("stale") if isinstance(doc,dict) else True))
    print("rating_"+kind+"_age_seconds="+str(max(0,now-api_updated) if api_updated else 0))

db.close()

wars_status,wars_html=get_text(SITE+"/wars/")
ratings_status,ratings_html=get_text(SITE+"/ratings/")
print("site_wars_status="+str(wars_status))
print("site_wars_public_api_marker="+yes("/api/v1/public/clan-war" in wars_html))
print("site_wars_refresh_marker="+yes("setInterval(load,60000)" in wars_html.replace(" ","")))
print("site_ratings_status="+str(ratings_status))
print("site_ratings_public_api_marker="+yes("/api/v1/public/ratings?kind=" in ratings_html))
print("site_ratings_alliance_controls="+yes("alliance_power" in ratings_html and "alliance_influence" in ratings_html and "alliance_defense" in ratings_html))
print("site_ratings_refresh_marker="+yes("setInterval(load,300000)" in ratings_html.replace(" ","")))

war_ok=(
    war_status==200
    and bool(war_doc.get("ok"))
    and api_war_updated==db_war_updated
    and api_war_updated>0
    and war_cors==SITE
)
site_ok=(
    wars_status==200
    and ratings_status==200
    and "/api/v1/public/clan-war" in wars_html
    and "/api/v1/public/ratings?kind=" in ratings_html
)
print("war_e2e="+("PASS" if war_ok else "FAIL"))
print("ratings_e2e="+("PASS" if ratings_all_ok else "FAIL"))
print("site_binding_e2e="+("PASS" if site_ok else "FAIL"))

if not (war_ok and ratings_all_ok and site_ok):
    raise SystemExit(2)

print("PUBLIC_OUTPUT_E2E=PASS")
