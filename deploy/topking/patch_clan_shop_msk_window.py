from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text()
MARKER = "CLAN_SHOP_MSK_WINDOW_V21"
if MARKER in s:
    print("CLAN_SHOP_MSK_WINDOW_ALREADY_PRESENT")
    raise SystemExit(0)

old = '''    # CLAN_SHOP_REQUESTS_V2
    # Clan Shop week closes Sunday at 21:00 Moscow time (UTC+3).
    tz = _dt.timezone(_dt.timedelta(hours=3))
    now_value = int(now_ts if now_ts is not None else utc_now())
    local_now = _dt.datetime.fromtimestamp(now_value, _dt.timezone.utc).astimezone(tz)
    days_until_sunday = (6 - local_now.weekday()) % 7
    deadline_date = local_now.date() + _dt.timedelta(days=days_until_sunday)
    deadline = _dt.datetime.combine(deadline_date, _dt.time(21, 0), tzinfo=tz)
    if local_now >= deadline:
        deadline += _dt.timedelta(days=7)
    week_start_date = deadline.date() + _dt.timedelta(days=1)
    week_end_date = week_start_date + _dt.timedelta(days=6)
'''
new = '''    # CLAN_SHOP_REQUESTS_V2
    # CLAN_SHOP_MSK_WINDOW_V21
    # Requests close Sunday at 21:00 Moscow time (UTC+3).
    # From Sunday 21:00 until midnight the closed list still targets
    # the Monday that begins in a few hours. A fresh cycle starts Monday.
    tz = _dt.timezone(_dt.timedelta(hours=3))
    now_value = int(now_ts if now_ts is not None else utc_now())
    local_now = _dt.datetime.fromtimestamp(now_value, _dt.timezone.utc).astimezone(tz)
    if local_now.weekday() == 6 and local_now.time() >= _dt.time(21, 0):
        deadline_date = local_now.date()
    else:
        days_until_sunday = (6 - local_now.weekday()) % 7
        deadline_date = local_now.date() + _dt.timedelta(days=days_until_sunday)
    deadline = _dt.datetime.combine(deadline_date, _dt.time(21, 0), tzinfo=tz)
    week_start_date = deadline.date() + _dt.timedelta(days=1)
    week_end_date = week_start_date + _dt.timedelta(days=6)
'''
if old not in s:
    raise SystemExit("current Moscow clan shop window block not found")
s = s.replace(old, new, 1)
path.write_text(s)
print("CLAN_SHOP_MSK_WINDOW_PATCH_OK")
