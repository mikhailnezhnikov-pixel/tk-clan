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

spec=importlib.util.spec_from_file_location("hk_refresh_failure_test",LIVE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

print("refresh_failure_revision=PUBLIC_COLLECTOR_REFRESH_FAILURE_R1")

with tempfile.TemporaryDirectory(prefix="hk-refresh-failure-") as td:
    token_path=os.path.join(td,"token")
    bootstrap_path=os.path.join(td,"auth.json")
    identity_path=os.path.join(td,"identity.sha256")
    status_path=os.path.join(td,"refresh.json")

    originals={
        "TOKEN_FILE":mod.TOKEN_FILE,
        "AUTH_BOOTSTRAP_FILE":mod.AUTH_BOOTSTRAP_FILE,
        "IDENTITY_FILE":mod.IDENTITY_FILE,
        "AUTH_REFRESH_STATUS_FILE":mod.AUTH_REFRESH_STATUS_FILE,
        "TOKEN":mod.TOKEN,
        "_direct_json":mod._direct_json,
    }
    try:
        mod.TOKEN_FILE=token_path
        mod.AUTH_BOOTSTRAP_FILE=bootstrap_path
        mod.IDENTITY_FILE=identity_path
        mod.AUTH_REFRESH_STATUS_FILE=status_path
        mod.TOKEN="old-token"

        bootstrap={"auth_type":"Yandex","auth_data":"synthetic-auth-data","platform":"WEB","updated_at":int(time.time())}
        mod._write_private(token_path,"old-token\n")
        mod._write_private(bootstrap_path,json.dumps(bootstrap,separators=(",",":"))+"\n")
        test_player="synthetic-technical-player"
        mod._write_private(identity_path,hashlib.sha256(test_player.encode()).hexdigest()+"\n")

        fail_calls=[]
        def fail_direct(url,method="GET",body=None,token=""):
            fail_calls.append(url)
            raise OSError("synthetic upstream failure")
        mod._direct_json=fail_direct

        failed=mod.refresh_game_token(force=True)
        token_after_fail=mod._read_text(token_path)
        bootstrap_after_fail=json.loads(mod._read_text(bootstrap_path) or "{}")
        backoff_after_fail=os.path.exists(status_path)
        print("failed_refresh_result_false="+yes(failed is False))
        print("failed_refresh_attempted_once="+yes(len(fail_calls)==1))
        print("failed_refresh_preserved_token="+yes(token_after_fail=="old-token"))
        print("failed_refresh_preserved_bootstrap="+yes(bootstrap_after_fail.get("auth_data")=="synthetic-auth-data"))
        print("failed_refresh_backoff_created="+yes(backoff_after_fail))

        blocked_calls=[]
        def blocked_direct(url,method="GET",body=None,token=""):
            blocked_calls.append(url)
            raise AssertionError("backoff should prevent network call")
        mod._direct_json=blocked_direct
        blocked=mod.refresh_game_token(force=True)
        print("backoff_second_refresh_result_false="+yes(blocked is False))
        print("backoff_prevents_repeat_request="+yes(len(blocked_calls)==0))

        mod._write_private(status_path,json.dumps({"failed_at":int(time.time())-3601},separators=(",",":")))

        success_calls=[]
        def success_direct(url,method="GET",body=None,token=""):
            success_calls.append(url)
            if url.endswith("/auth/create?"+url.split("/auth/create?",1)[-1]) and "/auth/create?" in url:
                return {"token":"replacement-token"}
            if url.endswith("/player/me"):
                return {"player":{"id":test_player}}
            raise AssertionError("unexpected synthetic URL")
        mod._direct_json=success_direct

        recovered=mod.refresh_game_token(force=True)
        token_after_success=mod._read_text(token_path)
        bootstrap_after_success=json.loads(mod._read_text(bootstrap_path) or "{}")
        status_cleared=not os.path.exists(status_path)
        token_mode=stat.S_IMODE(os.stat(token_path).st_mode)
        bootstrap_mode=stat.S_IMODE(os.stat(bootstrap_path).st_mode)

        print("recovery_refresh_result_true="+yes(recovered is True))
        print("recovery_made_auth_and_identity_checks="+yes(len(success_calls)==2))
        print("recovery_replaced_token="+yes(token_after_success=="replacement-token"))
        print("recovery_preserved_bootstrap="+yes(bootstrap_after_success.get("auth_data")=="synthetic-auth-data"))
        print("recovery_cleared_backoff="+yes(status_cleared))
        print("recovery_token_private_mode="+yes(token_mode==0o600))
        print("recovery_bootstrap_private_mode="+yes(bootstrap_mode==0o600))

        all_ok=all((
            failed is False,
            len(fail_calls)==1,
            token_after_fail=="old-token",
            bootstrap_after_fail.get("auth_data")=="synthetic-auth-data",
            backoff_after_fail,
            blocked is False,
            len(blocked_calls)==0,
            recovered is True,
            len(success_calls)==2,
            token_after_success=="replacement-token",
            bootstrap_after_success.get("auth_data")=="synthetic-auth-data",
            status_cleared,
            token_mode==0o600,
            bootstrap_mode==0o600,
        ))
        if not all_ok:
            raise SystemExit(2)
    finally:
        mod.TOKEN_FILE=originals["TOKEN_FILE"]
        mod.AUTH_BOOTSTRAP_FILE=originals["AUTH_BOOTSTRAP_FILE"]
        mod.IDENTITY_FILE=originals["IDENTITY_FILE"]
        mod.AUTH_REFRESH_STATUS_FILE=originals["AUTH_REFRESH_STATUS_FILE"]
        mod.TOKEN=originals["TOKEN"]
        mod._direct_json=originals["_direct_json"]

print("PUBLIC_COLLECTOR_REFRESH_FAILURE=PASS")
