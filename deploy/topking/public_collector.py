#!/usr/bin/env python3
import json, os, re, sqlite3, sys, time, urllib.error, urllib.parse, urllib.request

REV = "public-server-collector-20260920-r1"
GAME_API = os.environ.get("HK_PUBLIC_COLLECTOR_GAME_API", "https://hk-game-api.hwgame.cloud").rstrip("/")
DB_PATH = os.environ.get("HK_PUBLIC_COLLECTOR_DB", "/var/lib/hamsterking-license/licenses.db")
STATUS_PATH = os.environ.get("HK_PUBLIC_COLLECTOR_STATUS", "/var/lib/hamsterking-license/public-collector-status.json")
TOKEN = os.environ.get("HK_PUBLIC_COLLECTOR_GAME_TOKEN", "").strip()
REQUEST_GAP = max(0.15, float(os.environ.get("HK_PUBLIC_COLLECTOR_REQUEST_GAP", "0.35")))
SOURCE = "server-collector"
RATING_KINDS = {"influence","power","clans","alliance_power","alliance_influence","alliance_defense"}

def write_status(ok, state, **extra):
    data = {"revision":REV,"ok":bool(ok),"state":state,"at":int(time.time()),**extra}
    try:
        tmp=STATUS_PATH+".tmp"
        with open(tmp,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,separators=(",",":"))
        os.replace(tmp,STATUS_PATH)
    except Exception:
        pass

def log(message):
    print(f"[public-collector] {message}", flush=True)

def clean_name(value, limit=100):
    return re.sub(r"\s+"," ",re.sub(r"[\x00-\x1f\x7f]+"," ",str(value or ""))).strip()[:limit]

def key(value):
    return re.sub(r"\s+"," ",str(value or "").strip().lower())

def first_text(*values):
    for value in values:
        text=clean_name(value)
        if text:return text
    return ""

def finite(*values):
    for value in values:
        if value in (None,""): continue
        try:
            number=float(value)
        except (TypeError,ValueError):
            continue
        if number>=0 and number<1e40:return number
    return None

_last_request=0.0
def game_json(path, method="GET", body=None):
    global _last_request
    if not TOKEN:
        raise RuntimeError("collector token missing")
    wait=REQUEST_GAP-(time.monotonic()-_last_request)
    if wait>0: time.sleep(wait)
    url=GAME_API+path
    token=TOKEN[7:] if TOKEN.lower().startswith("bearer ") else TOKEN
    headers={"Authorization":"Bearer "+token,"Accept":"application/json","User-Agent":"TopKing-Public-Collector/1"}
    data=None
    if body is not None:
        data=json.dumps(body,separators=(",",":")).encode()
        headers["Content-Type"]="application/json"
    delays=(0,3,10,30)
    last=None
    for attempt,delay in enumerate(delays):
        if delay: time.sleep(delay)
        req=urllib.request.Request(url,data=data,headers=headers,method=method)
        try:
            _last_request=time.monotonic()
            with urllib.request.urlopen(req,timeout=20) as response:
                raw=response.read(2_000_000)
                if response.status<200 or response.status>=300:
                    raise RuntimeError(f"HTTP {response.status}")
                return json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last=exc
            if exc.code==429 or exc.code>=500:
                retry=exc.headers.get("Retry-After")
                if retry:
                    try: time.sleep(min(120,max(0,float(retry))))
                    except ValueError: pass
                continue
            raise
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            last=exc
            if attempt+1<len(delays): continue
            raise
    raise last or RuntimeError("request failed")

def lists_in(value, depth=0):
    if depth>5:return []
    if isinstance(value,list):
        result=[value]
        for row in value[:5]:
            if isinstance(row,(dict,list)): result.extend(lists_in(row,depth+1))
        return result
    if isinstance(value,dict):
        result=[]
        preferred=["result","rows","items","leaderboard","players","clans","alliances","data"]
        seen=set()
        for name in preferred:
            child=value.get(name)
            if isinstance(child,(dict,list)):
                seen.add(name); result.extend(lists_in(child,depth+1))
        for name,child in value.items():
            if name in seen: continue
            if isinstance(child,(dict,list)): result.extend(lists_in(child,depth+1))
        return result
    return []

def normalize_ranking(document, kind):
    best=[]
    for rows in lists_in(document):
        normalized=[]
        for index,row in enumerate(rows[:150]):
            if not isinstance(row,dict): continue
            entity=row.get("player") or row.get("user") or row.get("clan") or row.get("alliance") or row.get("member") or row
            if not isinstance(entity,dict): entity=row
            name=first_text(entity.get("nickname"),entity.get("name"),entity.get("title"),row.get("nickname"),row.get("name"),row.get("clan_name"),row.get("alliance_name"))
            rank=finite(row.get("rank"),row.get("place"),row.get("position"),entity.get("rank"))
            if rank is None: rank=index+1
            rank=int(rank)
            if kind=="power":
                value=finite(row.get("power"),entity.get("power"),row.get("value"),row.get("score"),entity.get("hamsters_power"))
            elif kind=="influence":
                value=finite(row.get("influence"),entity.get("influence"),row.get("level"),entity.get("level"),row.get("value"),row.get("score"))
            else:
                value=finite(row.get("score"),row.get("points"),row.get("value"),entity.get("score"),entity.get("points"),entity.get("power"),entity.get("level"))
            if name and 1<=rank<=100 and value is not None:
                normalized.append({"rank":rank,"name":name,"value":int(value) if float(value).is_integer() else value})
        if len(normalized)>len(best): best=normalized[:100]
    return best

def active_war():
    me=game_json("/player/me","POST",{})
    own=first_text(
        (me.get("player") or {}).get("clan_name") if isinstance(me,dict) else "",
        ((me.get("player") or {}).get("clan") or {}).get("name") if isinstance((me.get("player") or {}).get("clan"),dict) else "",
        (me.get("clan") or {}).get("name") if isinstance(me.get("clan"),dict) else "",
        "Top King",
    )
    value=game_json("/clan/active_battles")
    attack=value.get("alliance_attack_war") if isinstance(value,dict) else None
    if isinstance(attack,dict):
        timer=finite(attack.get("end_timer")) or 0
        war={"our_clan":own,"opponent":first_text(attack.get("name"),attack.get("defender_clan_name"),"—"),"our_score":0,"opponent_score":0,"status":"active","started_at":0,"ends_at":int(time.time()+timer/1000)}
        cur=finite(attack.get("health")); maximum=finite(attack.get("initial_health"))
        if cur is not None: war["opponent_hp"]=round(cur)
        if maximum and maximum>0: war["opponent_hp_max"]=round(maximum)
        return True,war
    defenses=value.get("clan_defense_wars") if isinstance(value,dict) else None
    if isinstance(defenses,list) and defenses:
        defenses=[x for x in defenses if isinstance(x,dict)]
        defenses.sort(key=lambda x: finite(x.get("end_timer")) or 0)
        defense=defenses[0]
        timer=finite(defense.get("end_timer")) or 0
        war={"our_clan":own,"opponent":first_text(defense.get("name"),defense.get("attacker_alliance_name"),"—"),"our_score":0,"opponent_score":0,"status":"active","started_at":0,"ends_at":int(time.time()+timer/1000)}
        cur=finite(defense.get("health")); maximum=finite(defense.get("initial_health"))
        if cur is not None: war["our_hp"]=round(cur)
        if maximum and maximum>0: war["our_hp_max"]=round(maximum)
        return True,war
    return True,None

def alliance_list(document):
    rows=document.get("result") if isinstance(document,dict) else None
    if not isinstance(rows,list) and isinstance(document,dict) and isinstance(document.get("data"),dict):
        rows=document["data"].get("result")
    result=[]
    for row in rows or []:
        if not isinstance(row,dict): continue
        ident=str(row.get("id") or "")
        name=first_text(row.get("name"),row.get("title"))
        if ident and name:
            result.append({"id":ident,"name":name,"defense":finite(row.get("defense_point")) or 0,
                           "power":finite(row.get("total_power"),row.get("power")),
                           "influence":finite(row.get("total_influence"),row.get("influence"))})
    return result[:100]

def alliance_clans(document):
    if not isinstance(document,dict): return []
    raw=[]
    if isinstance(document.get("core_clan"),dict): raw.append(document["core_clan"])
    if isinstance(document.get("satellite_clans"),list): raw.extend(document["satellite_clans"])
    out=[]; seen=set()
    for row in raw:
        if not isinstance(row,dict): continue
        name=first_text(row.get("name"),row.get("clan_name"),row.get("title"))
        ident=str(row.get("id") or row.get("clan_id") or "")
        k=key(name)
        if not ident or not name or k in seen: continue
        seen.add(k)
        out.append({"id":ident,"name":name,"key":k,
                    "defense":finite(row.get("defense_point")) or 0,
                    "power":finite(row.get("hamsters_power"),row.get("power"),row.get("total_power")),
                    "influence":finite(row.get("influence"),row.get("total_influence"),row.get("player_level_sum"))})
    return out

def rank_totals(rows, metric):
    usable=[row for row in rows if row.get(metric) is not None and row.get(metric)>0]
    usable.sort(key=lambda row:(-row[metric],row["name"].lower()))
    return [{"rank":i+1,"name":row["name"],"value":int(row[metric]) if float(row[metric]).is_integer() else row[metric]} for i,row in enumerate(usable[:100])]

def ratings_snapshot():
    ratings={}
    clan_influence=[]
    for leaderboard_type,kind,out_kind in [
        ("player_level_lb","influence","influence"),
        ("hamsters_power_lb","power","power"),
        ("clan_player_level_lb","clans","clans"),
    ]:
        try:
            rows=normalize_ranking(game_json("/leaderboard","POST",{"leaderboard_type":leaderboard_type}),kind)
            if rows:
                ratings[out_kind]=rows
                if out_kind=="clans": clan_influence=rows
        except Exception as exc:
            log(f"leaderboard {leaderboard_type} failed: {type(exc).__name__}")
    clan_power=[]
    for leaderboard_type in ("clan_hamsters_power_lb","clan_hamster_power_lb","clan_power_lb","clans_hamsters_power_lb"):
        try:
            rows=normalize_ranking(game_json("/leaderboard","POST",{"leaderboard_type":leaderboard_type}),"clans")
            if rows:
                clan_power=rows; break
        except Exception:
            continue
    influence_map={key(row["name"]):float(row["value"]) for row in clan_influence}
    power_map={key(row["name"]):float(row["value"]) for row in clan_power}

    try:
        alliances=alliance_list(game_json("/alliance/list"))
    except Exception as exc:
        log(f"alliance list failed: {type(exc).__name__}")
        alliances=[]

    totals=[]
    for index,alliance in enumerate(alliances):
        clans=[]
        try:
            clans=alliance_clans(game_json("/alliance/members?alliance_id="+urllib.parse.quote(alliance["id"])))
        except Exception as exc:
            log(f"alliance detail {index+1}/{len(alliances)} failed: {type(exc).__name__}")
        if not clans:
            totals.append({"name":alliance["name"],"defense":alliance["defense"] or None,
                           "influence":alliance["influence"],"power":alliance["power"]})
            continue
        influence=0.0; ic=0; power=0.0; pc=0
        for clan in clans:
            iv=influence_map.get(clan["key"],clan.get("influence"))
            pv=power_map.get(clan["key"],clan.get("power"))
            if iv is not None: influence+=float(iv); ic+=1
            if pv is not None: power+=float(pv); pc+=1
        defense=alliance["defense"] or sum(float(c.get("defense") or 0) for c in clans)
        totals.append({"name":alliance["name"],"defense":defense or None,
                       "influence":influence if ic==len(clans) else alliance["influence"],
                       "power":power if pc==len(clans) else alliance["power"]})
    for metric in ("defense","influence","power"):
        rows=rank_totals(totals,metric)
        if rows: ratings["alliance_"+metric]=rows
    return ratings

def store_snapshot(war_read,war,ratings):
    now=int(time.time())
    db=sqlite3.connect(DB_PATH,timeout=30)
    try:
        db.execute("PRAGMA busy_timeout=30000")
        db.execute("BEGIN IMMEDIATE")
        if war_read:
            db.execute("DELETE FROM public_clan_war_snapshot")
            if war:
                db.execute("""INSERT INTO public_clan_war_snapshot(singleton,snapshot_json,source_player_id,updated_at)
                              VALUES(1,?,?,?)""",(json.dumps(war,ensure_ascii=False,separators=(",",":")),SOURCE,now))
        saved=[]
        for kind,rows in ratings.items():
            if kind not in RATING_KINDS or not rows: continue
            clean=[]
            used=set()
            for row in rows[:100]:
                try: rank=int(row.get("rank")); value=float(row.get("value"))
                except (TypeError,ValueError): continue
                name=clean_name(row.get("name"))
                if not (1<=rank<=100) or rank in used or not name or value<0: continue
                used.add(rank); clean.append((kind,rank,name,int(value) if value.is_integer() else value,SOURCE,now))
            if not clean: continue
            db.execute("DELETE FROM public_rating_snapshots WHERE kind=?",(kind,))
            db.executemany("""INSERT INTO public_rating_snapshots(kind,rank,name,value,source_player_id,updated_at)
                              VALUES(?,?,?,?,?,?)""",clean)
            saved.append(kind)
        db.commit()
        return saved
    except Exception:
        db.rollback(); raise
    finally:
        db.close()

def main():
    if not TOKEN:
        write_status(True,"disabled_no_token")
        log("disabled: HK_PUBLIC_COLLECTOR_GAME_TOKEN is not configured")
        return 0
    started=time.time()
    try:
        war_read=False; war=None
        try:
            war_read,war=active_war()
        except Exception as exc:
            log(f"war read failed: {type(exc).__name__}")
        ratings=ratings_snapshot()
        if not war_read and not ratings:
            raise RuntimeError("no public data collected")
        saved=store_snapshot(war_read,war,ratings)
        write_status(True,"ok",duration_sec=round(time.time()-started,2),war=bool(war),ratings=saved)
        log(f"success: war={'active' if war else 'none' if war_read else 'unchanged'} ratings={','.join(saved) or 'unchanged'}")
        return 0
    except Exception as exc:
        write_status(False,"error",error=type(exc).__name__,duration_sec=round(time.time()-started,2))
        log(f"failed: {type(exc).__name__}: {exc}")
        return 1

if __name__=="__main__":
    sys.exit(main())
