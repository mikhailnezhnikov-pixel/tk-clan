#!/usr/bin/env python3
import json, urllib.request, urllib.error, hashlib

env={}
for line in open("/etc/hamsterking-public-collector.env",encoding="utf-8"):
    line=line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k,v=line.split("=",1)
    env[k]=v

token=env.get("HK_PUBLIC_COLLECTOR_GAME_TOKEN","").strip()
if token.lower().startswith("bearer "):
    token=token[7:]
base=env.get("HK_PUBLIC_COLLECTOR_GAME_API","https://hk-game-api.hwgame.cloud").rstrip("/")
assert token

def probe(label,path,method="GET",body=None,ua="TopKing-Public-Collector/1"):
    headers={"Authorization":"Bearer "+token,"Accept":"application/json","User-Agent":ua}
    data=None
    if body is not None:
        data=json.dumps(body,separators=(",",":")).encode()
        headers["Content-Type"]="application/json"
    request=urllib.request.Request(base+path,data=data,headers=headers,method=method)
    try:
        with urllib.request.urlopen(request,timeout=20) as response:
            raw=response.read(2500000)
            ctype=response.headers.get("Content-Type","")
            enc=response.headers.get("Content-Encoding","")
            digest=hashlib.sha256(raw).hexdigest()[:16]
            try:
                value=json.loads(raw.decode("utf-8"))
                parsed=True
                keys=sorted(value.keys()) if isinstance(value,dict) else []
            except Exception as exc:
                parsed=False
                keys=[]
                print(label,"decode_error",type(exc).__name__)
            print(label,"status",response.status,"ctype",ctype,"encoding",enc,"bytes",len(raw),"sha16",digest,"json",parsed,"keys",keys[:40])
    except urllib.error.HTTPError as exc:
        raw=exc.read(500000)
        print(label,"http_error",exc.code,"ctype",exc.headers.get("Content-Type",""),"bytes",len(raw),"sha16",hashlib.sha256(raw).hexdigest()[:16])
    except Exception as exc:
        print(label,"transport_error",type(exc).__name__)

for ua_label,ua in [
    ("collector_ua","TopKing-Public-Collector/1"),
    ("diagnose_ua","TopKing-Public-Diagnose/1"),
    ("browser_ua","Mozilla/5.0"),
]:
    probe(ua_label+"_war","/clan/active_battles",ua=ua)

probe("collector_player_me","/player/me",method="POST",body={},ua="TopKing-Public-Collector/1")
