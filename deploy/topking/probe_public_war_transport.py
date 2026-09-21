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

# Safe token metadata: no token bytes are printed.
try:
    import base64
    payload=token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    claims=json.loads(base64.urlsafe_b64decode(payload.encode()).decode())
    safe_claims={k:claims.get(k) for k in ("exp","iat","iss","aud","sub") if k in claims}
    print("token_claims",json.dumps(safe_claims,separators=(",",":")))
except Exception:
    print("token_claims unavailable")

probe("war","/clan/active_battles")
probe("clan_leaderboard","/leaderboard","POST",{"leaderboard_type":"clan_player_level_lb"})

# Read one /player/me document and only print sanitized auth method metadata.
try:
    time.sleep(2)
    req=urllib.request.Request(
        api+"/player/me",
        data=b"{}",
        headers={**headers,"Content-Type":"application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req,timeout=20) as response:
        doc=json.loads(response.read(5_000_000).decode("utf-8-sig"))
    methods=doc.get("auth_methods") if isinstance(doc,dict) else None
    if not isinstance(methods,list) and isinstance(doc,dict) and isinstance(doc.get("player"),dict):
        methods=doc["player"].get("auth_methods")
    safe=[]
    for row in methods or []:
        if not isinstance(row,dict): continue
        keep={}
        for k,v in row.items():
            lk=str(k).lower()
            if any(s in lk for s in ("token","secret","data","email","phone","id")): continue
            if isinstance(v,(str,int,float,bool)) or v is None:
                keep[k]=v
        safe.append(keep)
    print("player_auth_methods",json.dumps(safe,ensure_ascii=False,separators=(",",":")))
except urllib.error.HTTPError as exc:
    print("player_me http_error",exc.code)
except Exception as exc:
    print("player_me transport_error",type(exc).__name__)
