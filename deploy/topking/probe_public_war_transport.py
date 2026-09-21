#!/usr/bin/env python3
import json, urllib.request, urllib.error, hashlib

env={}
for line in open("/etc/hamsterking-public-collector.env",encoding="utf-8"):
    line=line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k,v=line.split("=",1); env[k]=v

token=env.get("HK_PUBLIC_COLLECTOR_GAME_TOKEN","").strip()
if token.lower().startswith("bearer "): token=token[7:]
base=env.get("HK_PUBLIC_COLLECTOR_GAME_API","https://hk-game-api.hwgame.cloud").rstrip("/")
assert token

def probe(label,path,method="GET",body=None,max_read=1024):
    headers={"Authorization":"Bearer "+token,"Accept":"application/json","User-Agent":"TopKing-Public-Probe/2"}
    data=None
    if body is not None:
        data=json.dumps(body,separators=(",",":")).encode()
        headers["Content-Type"]="application/json"
    request=urllib.request.Request(base+path,data=data,headers=headers,method=method)
    try:
        with urllib.request.urlopen(request,timeout=20) as response:
            raw=response.read(max_read)
            print(label,"status",response.status,"ctype",response.headers.get("Content-Type",""),
                  "bytes_read",len(raw),"sha16",hashlib.sha256(raw).hexdigest()[:16])
    except urllib.error.HTTPError as exc:
        raw=exc.read(2048)
        print(label,"http_error",exc.code,"ctype",exc.headers.get("Content-Type",""),
              "bytes",len(raw),"sha16",hashlib.sha256(raw).hexdigest()[:16],
              "retry_after",exc.headers.get("Retry-After",""))
    except Exception as exc:
        print(label,"transport_error",type(exc).__name__)

probe("war","/clan/active_battles")
probe("clan_leaderboard","/leaderboard","POST",{"leaderboard_type":"clan_player_level_lb"})
probe("player_me","/player/me","POST",{},max_read=1024)
