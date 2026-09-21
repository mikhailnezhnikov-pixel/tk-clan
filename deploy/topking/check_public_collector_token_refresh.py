#!/usr/bin/env python3
import fcntl
import importlib.util
import json
import os
import subprocess
import sys
import time

LIVE_COLLECTOR="/opt/hamsterking-license/public_collector.py"
LOCK_PATH="/run/hamsterking-public-collector.lock"

spec=importlib.util.spec_from_file_location("hk_public_collector_refresh_test", LIVE_COLLECTOR)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def yes(value):
    return "yes" if bool(value) else "no"

before=mod._load_token()
before_exp=mod._token_expiry(before)
now=int(time.time())
print("refresh_test_revision=PUBLIC_COLLECTOR_TOKEN_REFRESH_TEST_R1")
print("bootstrap_present="+yes(os.path.getsize(mod.AUTH_BOOTSTRAP_FILE)>0 if os.path.exists(mod.AUTH_BOOTSTRAP_FILE) else False))
print("before_token_present="+yes(before))
print("before_seconds_left="+str(before_exp-now if before_exp else 0))

lock=open(LOCK_PATH,"a+")
deadline=time.monotonic()+30
locked=False
while time.monotonic()<deadline:
    try:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        locked=True
        break
    except BlockingIOError:
        time.sleep(1)
if not locked:
    print("refresh_lock_acquired=no")
    raise SystemExit(2)
print("refresh_lock_acquired=yes")

try:
    refreshed=bool(mod.refresh_game_token(force=True))
finally:
    fcntl.flock(lock.fileno(),fcntl.LOCK_UN)
    lock.close()

after=mod._load_token()
after_exp=mod._token_expiry(after)
now2=int(time.time())
print("refresh_result="+yes(refreshed))
print("token_changed="+yes(bool(before and after and before!=after)))
print("after_token_present="+yes(after))
print("after_seconds_left="+str(after_exp-now2 if after_exp else 0))
print("refresh_backoff_present="+yes(os.path.exists(mod.AUTH_REFRESH_STATUS_FILE)))

if not refreshed or not after or before==after or not after_exp or after_exp<=now2+600:
    raise SystemExit(3)

run=subprocess.run(
    [sys.executable,LIVE_COLLECTOR,"war"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    timeout=120,
)
print("post_refresh_war_exit="+str(run.returncode))
status={}
try:
    status=json.load(open(mod.STATUS_PATH,encoding="utf-8"))
except Exception:
    pass
print("post_refresh_collector_state="+str(status.get("state","")))
print("post_refresh_war_state="+str(status.get("war_state","")))
print("post_refresh_status_ok="+yes(status.get("ok")))

if run.returncode!=0 or not status.get("ok"):
    raise SystemExit(4)

print("PUBLIC_COLLECTOR_TOKEN_REFRESH_TEST=PASS")
