from pathlib import Path

TARGET=Path("/tmp/server.py")
s=TARGET.read_text(encoding="utf-8")

def req(value,message):
    if value not in s:
        raise SystemExit(message)

MARKER="# HK_MAP_CITY_LANGUAGE_R2\n"
if MARKER in s:
    print("HK_MAP_CITY_LANGUAGE_R2_ALREADY_PRESENT")
    raise SystemExit(0)

req("# HK_MAP_LOCALIZED_DEDUPE_R1\n","localized dedupe R1 missing")
req("def hk_localized_city_label(value: object) -> str:\n","localized city label helper missing")
req("def cabinet_maps(member: dict) -> dict:\n","cabinet maps missing")

insert=r'''# HK_MAP_CITY_LANGUAGE_R2
# Personal Cabinet has one display language for city names (Russian).
# This is display-only normalization: no areas/buildings are merged or deleted.
_cabinet_maps_before_city_language_r2 = cabinet_maps


def cabinet_maps(member: dict) -> dict:
    payload=dict(_cabinet_maps_before_city_language_r2(member))
    rows=[]
    latin_before=[]
    for original in payload.get("maps") or []:
        row=dict(original)
        raw=str(row.get("city") or "")
        if re.search(r"[A-Za-z]",raw):
            latin_before.append(raw)
        row["city"]=hk_localized_city_label(raw)
        rows.append(row)
    payload["maps"]=rows
    payload["city_display_language"]="ru"
    payload["city_names_normalized"]=True
    payload["city_latin_names_before"]=sorted(set(latin_before))
    payload["city_latin_names_after"]=sorted({
        str(row.get("city") or "")
        for row in rows
        if re.search(r"[A-Za-z]",str(row.get("city") or ""))
    })
    return payload


'''
# Install after R1 wrapper, before the following map_index.
marker_pos=s.find("# HK_MAP_LOCALIZED_DEDUPE_R1\n")
if marker_pos<0:
    raise SystemExit("localized marker position missing")
anchor_pos=s.find("def map_index() -> list[dict]:\n",marker_pos)
if anchor_pos<0:
    raise SystemExit("map_index anchor after localized dedupe missing")
s=s[:anchor_pos]+insert+s[anchor_pos:]

for check in (
    "HK_MAP_CITY_LANGUAGE_R2",
    "_cabinet_maps_before_city_language_r2 = cabinet_maps",
    'payload["city_display_language"]="ru"',
    'payload["city_names_normalized"]=True',
):
    req(check,"missing city language R2 marker: "+check)

TARGET.write_text(s,encoding="utf-8")
print("HK_MAP_CITY_LANGUAGE_R2_PATCH=PASS")
