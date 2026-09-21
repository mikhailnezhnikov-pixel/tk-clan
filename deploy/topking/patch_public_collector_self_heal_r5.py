from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text()
MARKER="PUBLIC_COLLECTOR_BOOTSTRAP_SELF_HEAL_R1"
if MARKER in s:
    print(MARKER+"_ALREADY_PRESENT")
    raise SystemExit(0)

s=s.replace(
    'REV = "public-server-collector-20260921-r4-auto-auth"',
    'REV = "public-server-collector-20260921-r5-bootstrap-self-heal"',
    1,
)

old='''def ensure_game_token():
    global TOKEN
    file_token=_load_token()
    if file_token and file_token!=TOKEN:
        TOKEN=file_token
    expiry=_token_expiry(TOKEN)
    if TOKEN and expiry and expiry<=int(time.time())+60:
        refresh_game_token(force=False)
    return bool(TOKEN)
'''
new='''# PUBLIC_COLLECTOR_BOOTSTRAP_SELF_HEAL_R1
def ensure_game_token():
    global TOKEN
    file_token=_load_token()
    if file_token and file_token!=TOKEN:
        TOKEN=file_token
    if not TOKEN:
        refresh_game_token(force=False)
    expiry=_token_expiry(TOKEN)
    if TOKEN and expiry and expiry<=int(time.time())+60:
        refresh_game_token(force=False)
    return bool(TOKEN)
'''
if s.count(old)!=1:
    raise SystemExit(f"ensure_game_token anchor count={s.count(old)}")
s=s.replace(old,new,1)
path.write_text(s)
print(MARKER+"_PATCH_OK")
