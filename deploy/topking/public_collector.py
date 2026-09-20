#!/usr/bin/env python3
import json, os, re, sqlite3, sys, time, urllib.error, urllib.parse, urllib.request, fcntl, hashlib

REV = "public-server-collector-20260921-r2-war-safe"
GAME_API = os.environ.get("HK_PUBLIC_COLLECTOR_GAME_API", "https://hk-game-api.hwgame.cloud").rstrip("/")
DB_PATH = os.environ.get("HK_PUBLIC_COLLECTOR_DB", "/var/lib/hamsterking-license/licenses.db")
STATUS_PATH = os.environ.get("HK_PUBLIC_COLLECTOR_STATUS", "/var/lib/hamsterking-license/public-collector-status.json")
TOKEN = os.environ.get("HK_PUBLIC_COLLECTOR_GAME_TOKEN", "").strip()
REQUEST_GAP = max(1.5, float(os.environ.get("HK_PUBLIC_COLLECTOR_REQUEST_GAP", "1.5")))
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
def game_json(path, method="GET", body=None, retry_delays=None):
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
    delays=tuple(retry_delays) if retry_delays is not None else (0,3,10,30)
    if not delays:
        delays=(0,)
    last=None
    for attempt,delay in enumerate(delays):
        if delay: time.sleep(delay)
        req=urllib.request.Request(url,data=data,headers=headers,method=method)
        try:
            _last_request=time.monotonic()
            with urllib.request.urlopen(req,timeout=20) as response:
                raw=response.read(5_000_000)
                if response.status<200 or response.status>=300:
                    raise RuntimeError(f"HTTP {response.status}")
                text=raw.decode("utf-8-sig").strip("\x00\r\n\t ")
                try:
                    return json.loads(text)
                except json.JSONDecodeError as exc:
                    log(
                        f"json decode path={path} status={response.status} "
                        f"ctype={response.headers.get('Content-Type','')} bytes={len(raw)} "
                        f"sha16={hashlib.sha256(raw).hexdigest()[:16]} "
                        f"error={exc.msg}@{exc.pos}"
                    )
                    raise
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

def normalize_ranking(document, kind, max_rank=100, limit=100):
    best=[]
    scan_limit=max(150,int(limit or max_rank),int(max_rank))
    for rows in lists_in(document):
        normalized=[]
        for index,row in enumerate(rows[:scan_limit]):
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
            if name and 1<=rank<=max_rank and value is not None:
                normalized.append({"rank":rank,"name":name,"value":int(value) if float(value).is_integer() else value})
        if len(normalized)>len(best):
            best=normalized[:limit]
    return best

def active_war():
    # Lightweight path: exactly one Game API request per scheduled war run.
    # If the game is throttling us, defer to the next timer instead of retrying
    # several times and increasing pressure on the upstream API.
    own=clean_name(os.environ.get("HK_PUBLIC_COLLECTOR_CLAN_NAME","Top🏆King")) or "Top King"
    value=game_json("/clan/active_battles",retry_delays=(0,))
    if not isinstance(value,dict):
        raise RuntimeError("active_battles invalid document")
    if value.get("_error"):
        raise RuntimeError("active_battles error document")
    if "alliance_attack_war" not in value or "clan_defense_wars" not in value:
        raise RuntimeError("active_battles incomplete schema")

    attack=value.get("alliance_attack_war")
    if attack is not None and not isinstance(attack,dict):
        raise RuntimeError("active_battles attack schema invalid")
    if isinstance(attack,dict) and attack:
        timer=finite(attack.get("end_timer")) or 0
        war={
            "our_clan":own,
            "opponent":first_text(attack.get("name"),attack.get("defender_clan_name"),"—"),
            "our_score":0,
            "opponent_score":0,
            "status":"active",
            "started_at":0,
            "ends_at":int(time.time()+timer/1000),
        }
        cur=finite(attack.get("health"))
        maximum=finite(attack.get("initial_health"))
        if cur is not None:
            war["opponent_hp"]=round(cur)
        if maximum and maximum>0:
            war["opponent_hp_max"]=round(maximum)
        return True,war

    defenses=value.get("clan_defense_wars")
    if not isinstance(defenses,list):
        raise RuntimeError("active_battles defense schema invalid")
    if defenses:
        valid=[x for x in defenses if isinstance(x,dict)]
        if not valid:
            raise RuntimeError("active_battles defense rows invalid")
        valid.sort(key=lambda x: finite(x.get("end_timer")) or 0)
        defense=valid[0]
        timer=finite(defense.get("end_timer")) or 0
        war={
            "our_clan":own,
            "opponent":first_text(defense.get("name"),defense.get("attacker_alliance_name"),"—"),
            "our_score":0,
            "opponent_score":0,
            "status":"active",
            "started_at":0,
            "ends_at":int(time.time()+timer/1000),
        }
        cur=finite(defense.get("health"))
        maximum=finite(defense.get("initial_health"))
        if cur is not None:
            war["our_hp"]=round(cur)
        if maximum and maximum>0:
            war["our_hp_max"]=round(maximum)
        return True,war

    # Canonical empty response. store_snapshot() still protects an unexpired
    # server snapshot from being erased by a suspicious temporary empty read.
    return True,None
def alliance_list(document):
    rows=document.get("result") if isinstance(document,dict) else None
    if not isinstance(rows,list) and isinstance(document,dict) and isinstance(document.get("data"),dict):
        rows=document["data"].get("result")
    result=[]
    for row in rows or []:
        if not isinstance(row,dict):
            continue
        ident=str(row.get("id") or "")
        name=first_text(row.get("name"),row.get("title"))
        if ident and name:
            result.append({
                "id":ident,
                "name":name,
                "defense":finite(row.get("defense_point")) or 0,
                "members":int(finite(row.get("members_count")) or 0),
                "power":finite(row.get("total_power"),row.get("power")),
                "influence":finite(row.get("total_influence"),row.get("influence")),
            })
    return result

def all_alliances():
    result=[]
    seen=set()
    offset=0
    while True:
        document=game_json(f"/alliance/list?offset={offset}&limit=50")
        batch=alliance_list(document)
        for row in batch:
            if row["id"] in seen:
                continue
            seen.add(row["id"])
            result.append(row)
        pagination=document.get("pagination") if isinstance(document,dict) and isinstance(document.get("pagination"),dict) else {}
        total=int(finite(pagination.get("total")) or len(result))
        limit=int(finite(pagination.get("limit")) or max(1,len(batch)))
        current_offset=int(finite(pagination.get("offset")) or offset)
        has_next=bool(pagination.get("hasNextPage"))
        if not has_next or not batch or current_offset+limit>=total:
            break
        offset=current_offset+limit
        if offset>=5000:
            break
    return result

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

    # Public player tables remain top-100.
    try:
        rows=normalize_ranking(game_json("/leaderboard","POST",{"leaderboard_type":"player_level_lb"}),"influence",100,100)
        if rows:
            ratings["influence"]=rows
    except Exception as exc:
        log(f"leaderboard player_level_lb failed: {type(exc).__name__}")

    try:
        rows=normalize_ranking(game_json("/leaderboard","POST",{"leaderboard_type":"hamsters_power_lb"}),"power",100,100)
        if rows:
            ratings["power"]=rows
    except Exception as exc:
        log(f"leaderboard hamsters_power_lb failed: {type(exc).__name__}")

    # Alliance aggregation needs the full clan leaderboard returned by the game
    # (currently top-500), not only the public top-100 slice.
    clan_influence_all=[]
    try:
        clan_influence_all=normalize_ranking(
            game_json("/leaderboard","POST",{"leaderboard_type":"clan_player_level_lb"}),
            "clans",500,500
        )
        if clan_influence_all:
            ratings["clans"]=clan_influence_all[:100]
    except Exception as exc:
        log(f"leaderboard clan_player_level_lb failed: {type(exc).__name__}")

    clan_power_all=[]
    for leaderboard_type in ("clan_hamsters_power_lb","clan_hamster_power_lb","clan_power_lb","clans_hamsters_power_lb"):
        try:
            rows=normalize_ranking(
                game_json("/leaderboard","POST",{"leaderboard_type":leaderboard_type}),
                "clans",500,500
            )
            if rows:
                clan_power_all=rows
                break
        except Exception:
            continue

    influence_map={key(row["name"]):float(row["value"]) for row in clan_influence_all}
    power_map={key(row["name"]):float(row["value"]) for row in clan_power_all}

    try:
        alliances=all_alliances()
        log(f"alliances discovered: {len(alliances)}")
    except Exception as exc:
        log(f"alliance list failed: {type(exc).__name__}")
        alliances=[]

    totals=[]
    complete_influence=0
    complete_power=0
    for index,alliance in enumerate(alliances):
        clans=[]
        try:
            clans=alliance_clans(game_json("/alliance/members?alliance_id="+urllib.parse.quote(alliance["id"])))
        except Exception as exc:
            log(f"alliance detail {index+1}/{len(alliances)} failed: {type(exc).__name__}")

        if not clans:
            totals.append({
                "name":alliance["name"],
                "defense":alliance["defense"] or None,
                "influence":alliance["influence"],
                "power":alliance["power"],
            })
            continue

        influence=0.0
        influence_covered=0
        power=0.0
        power_covered=0
        for clan in clans:
            iv=influence_map.get(clan["key"],clan.get("influence"))
            pv=power_map.get(clan["key"],clan.get("power"))
            if iv is not None:
                influence+=float(iv)
                influence_covered+=1
            if pv is not None:
                power+=float(pv)
                power_covered+=1

        influence_value=influence if influence_covered==len(clans) else alliance["influence"]
        power_value=power if power_covered==len(clans) else alliance["power"]
        if influence_value is not None:
            complete_influence+=1
        if power_value is not None:
            complete_power+=1

        totals.append({
            "name":alliance["name"],
            # defense_point on /alliance/list is already the alliance total.
            "defense":alliance["defense"] or None,
            "influence":influence_value,
            "power":power_value,
        })

    log(
        f"alliance metric coverage: total={len(totals)} "
        f"influence={complete_influence} power={complete_power} "
        f"clan_influence_rows={len(clan_influence_all)} clan_power_rows={len(clan_power_all)}"
    )

    for metric in ("defense","influence","power"):
        rows=rank_totals(totals,metric)
        if rows:
            ratings["alliance_"+metric]=rows
    return ratings

def store_snapshot(war_read,war,ratings):
    now=int(time.time())
    db=sqlite3.connect(DB_PATH,timeout=30)
    try:
        db.execute("PRAGMA busy_timeout=30000")
        db.execute("BEGIN IMMEDIATE")
        war_state="unchanged"
        if war_read:
            if war:
                db.execute("DELETE FROM public_clan_war_snapshot")
                db.execute("""INSERT INTO public_clan_war_snapshot(singleton,snapshot_json,source_player_id,updated_at)
                              VALUES(1,?,?,?)""",(json.dumps(war,ensure_ascii=False,separators=(",",":")),SOURCE,now))
                war_state="active"
            else:
                # Do not erase a still-unexpired server snapshot merely because
                # one upstream read said "no battle". This protects against
                # throttling/anti-abuse responses that are syntactically valid
                # but temporarily empty. Old client-generated anon rows are not
                # treated as authoritative server cache.
                existing=db.execute(
                    "SELECT snapshot_json,source_player_id,updated_at FROM public_clan_war_snapshot WHERE singleton=1"
                ).fetchone()
                preserve=False
                if existing and existing[1]==SOURCE:
                    try:
                        previous=json.loads(existing[0])
                    except Exception:
                        previous={}
                    previous_ends=finite(previous.get("ends_at")) if isinstance(previous,dict) else None
                    preserve=bool(
                        isinstance(previous,dict)
                        and previous.get("status")=="active"
                        and previous_ends is not None
                        and previous_ends>now
                    )
                if preserve:
                    war_state="preserved_unexpired"
                    log("war empty read ignored: unexpired server snapshot preserved")
                else:
                    db.execute("DELETE FROM public_clan_war_snapshot")
                    war_state="none"

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
        return saved,war_state
    except Exception:
        db.rollback(); raise
    finally:
        db.close()
def main():
    if not TOKEN:
        write_status(True,"disabled_no_token")
        log("disabled: HK_PUBLIC_COLLECTOR_GAME_TOKEN is not configured")
        return 0

    mode=(sys.argv[1].strip().lower() if len(sys.argv)>1 else "all")
    if mode not in {"all","war","ratings"}:
        raise SystemExit("usage: public_collector.py [all|war|ratings]")

    lock_path="/run/hamsterking-public-collector.lock"
    lock=open(lock_path,"a+")
    try:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:
        write_status(True,"skipped_busy",mode=mode)
        log(f"skipped: mode={mode} another public collector is running")
        lock.close()
        return 0

    started=time.time()
    try:
        war_read=False
        war=None
        ratings={}

        if mode in {"all","war"}:
            try:
                war_read,war=active_war()
            except Exception as exc:
                log(f"war read failed: {type(exc).__name__}")

        if mode in {"all","ratings"}:
            ratings=ratings_snapshot()

        if not war_read and not ratings:
            if mode=="war":
                write_status(True,"deferred",mode=mode,duration_sec=round(time.time()-started,2))
                log("deferred: war endpoint temporarily unavailable; previous cache preserved")
                return 0
            raise RuntimeError("no public data collected")

        saved,war_state=store_snapshot(war_read,war,ratings)
        write_status(
            True,"ok",
            mode=mode,
            duration_sec=round(time.time()-started,2),
            war=bool(war),
            war_state=war_state,
            ratings=saved,
        )
        log(
            f"success: mode={mode} "
            f"war={war_state} "
            f"ratings={','.join(saved) or 'unchanged'}"
        )
        return 0
    except Exception as exc:
        write_status(False,"error",mode=mode,error=type(exc).__name__,duration_sec=round(time.time()-started,2))
        log(f"failed: mode={mode} {type(exc).__name__}: {exc}")
        return 1
    finally:
        try:
            fcntl.flock(lock.fileno(),fcntl.LOCK_UN)
        except Exception:
            pass
        lock.close()

if __name__=="__main__":
    sys.exit(main())
