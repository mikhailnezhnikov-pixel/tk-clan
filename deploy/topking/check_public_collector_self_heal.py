#!/usr/bin/env python3
import hashlib
import importlib.util
import json
import os
import stat
import tempfile
import time

LIVE="/opt/hamsterking-license/public_collector.py"

def yes(v): return "yes" if bool(v) else "no"

spec=importlib.util.spec_from_file_location("hk_self_heal_test",LIVE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

print("self_heal_revision=PUBLIC_COLLECTOR_BOOTSTRAP_SELF_HEAL_TEST_R1")
print("live_self_heal_marker="+yes("PUBLIC_COLLECTOR_BOOTSTRAP_SELF_HEAL_R1" in open(LIVE,encoding="utf-8").read()))

with tempfile.TemporaryDirectory(prefix="hk-self-heal-") as td:
    originals={
        "TOKEN_FILE":mod.TOKEN_FILE,
        "AUTH_BOOTSTRAP_FILE":mod.AUTH_BOOTSTRAP_FILE,
        "IDENTITY_FILE":mod.IDENTITY_FILE,
        "AUTH_REFRESH_STATUS_FILE":mod.AUTH_REFRESH_STATUS_FILE,
        "TOKEN":mod.TOKEN,
        "_direct_json":mod._direct_json,
    }
    old_env=os.environ.pop("HK_PUBLIC_COLLECTOR_GAME_TOKEN",None)
    try:
        mod.TOKEN_FILE=os.path.join(td,"token")
        mod.AUTH_BOOTSTRAP_FILE=os.path.join(td,"auth.json")
        mod.IDENTITY_FILE=os.path.join(td,"identity.sha256")
        mod.AUTH_REFRESH_STATUS_FILE=os.path.join(td,"refresh.json")
        mod.TOKEN=""

        player="synthetic-self-heal-player"
        mod._write_private(mod.AUTH_BOOTSTRAP_FILE,json.dumps({
            "auth_type":"Yandex",
            "auth_data":"synthetic-auth-data",
            "platform":"WEB",
            "updated_at":int(time.time()),
        },separators=(",",":"))+"\n")
        mod._write_private(mod.IDENTITY_FILE,hashlib.sha256(player.encode()).hexdigest()+"\n")

        calls=[]
        def synthetic_direct(url,method="GET",body=None,token=""):
            calls.append(url)
            if "/auth/create?" in url:
                return {"token":"self-healed-token"}
            if url.endswith("/player/me"):
                return {"player":{"id":player}}
            raise AssertionError("unexpected URL")
        mod._direct_json=synthetic_direct

        result=mod.ensure_game_token()
        stored=mod._read_text(mod.TOKEN_FILE)
        mode=stat.S_IMODE(os.stat(mod.TOKEN_FILE).st_mode) if os.path.exists(mod.TOKEN_FILE) else 0
        backoff=mod._auth_refresh_backed_off()

        print("missing_token_self_heal_result="+yes(result))
        print("missing_token_auth_create_called="+yes(len(calls)>=1 and "/auth/create?" in calls[0]))
        print("missing_token_identity_check_called="+yes(len(calls)==2 and calls[1].endswith("/player/me")))
        print("missing_token_file_created="+yes(stored=="self-healed-token"))
        print("missing_token_file_private="+yes(mode==0o600))
        print("missing_token_no_backoff="+yes(not backoff))

        if not (result and len(calls)==2 and stored=="self-healed-token" and mode==0o600 and not backoff):
            raise SystemExit(2)
    finally:
        mod.TOKEN_FILE=originals["TOKEN_FILE"]
        mod.AUTH_BOOTSTRAP_FILE=originals["AUTH_BOOTSTRAP_FILE"]
        mod.IDENTITY_FILE=originals["IDENTITY_FILE"]
        mod.AUTH_REFRESH_STATUS_FILE=originals["AUTH_REFRESH_STATUS_FILE"]
        mod.TOKEN=originals["TOKEN"]
        mod._direct_json=originals["_direct_json"]
        if old_env is not None:
            os.environ["HK_PUBLIC_COLLECTOR_GAME_TOKEN"]=old_env

print("PUBLIC_COLLECTOR_BOOTSTRAP_SELF_HEAL_TEST=PASS")
