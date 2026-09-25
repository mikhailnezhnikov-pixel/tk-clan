from pathlib import Path

TARGET=Path("/tmp/server.py")
s=TARGET.read_text(encoding="utf-8")

def req(value,message):
    if value not in s:
        raise SystemExit(message)

MARKER="# HK_MAP_LOCALIZED_DEDUPE_R1\n"
if MARKER in s:
    print("HK_MAP_LOCALIZED_DEDUPE_R1_ALREADY_PRESENT")
    raise SystemExit(0)

req("# HK_MAP_VISIBILITY_ACCESS_V2\n","visibility wrapper missing")
req("def hydrate_hk_website_map_for_area(","hydration helper missing")

helpers=r'''# HK_MAP_LOCALIZED_DEDUPE_R1
_HK_CITY_LOCALE_ALIASES = {
    "moscow":"moscow","москва":"moscow",
    "new york":"newyork","нью-йорк":"newyork","нью йорк":"newyork",
    "los angeles":"losangeles","лос-анджелес":"losangeles","лос анджелес":"losangeles",
    "lagos":"lagos","лагос":"lagos",
    "london":"london","лондон":"london",
    "berlin":"berlin","берлин":"berlin",
    "paris":"paris","париж":"paris",
    "dubai":"dubai","дубай":"dubai",
    "tokyo":"tokyo","токио":"tokyo",
    "rio de janeiro":"rio","рио-де-жанейро":"rio","рио де жанейро":"rio",
    "saint petersburg":"spb","санкт-петербург":"spb","санкт петербург":"spb",
    "singapore":"singapore","сингапур":"singapore",
    "auckland":"auckland","окленд":"auckland",
    "sydney":"sydney","сидней":"sydney",
    "washington":"washington","вашингтон":"washington",
    "minsk":"minsk","минск":"minsk",
    "boston":"boston","бостон":"boston",
}
_HK_CITY_RU_LABELS = {
    "moscow":"Москва","newyork":"Нью-Йорк","losangeles":"Лос-Анджелес",
    "lagos":"Лагос","london":"Лондон","berlin":"Берлин","paris":"Париж",
    "dubai":"Дубай","tokyo":"Токио","rio":"Рио-де-Жанейро",
    "spb":"Санкт-Петербург","singapore":"Сингапур","auckland":"Окленд",
    "sydney":"Сидней","washington":"Вашингтон","minsk":"Минск","boston":"Бостон",
}


def hk_localized_city_key(value: object) -> str:
    raw=str(value or "").strip().lower().replace("ё","е")
    raw=re.sub(r"\s+"," ",raw)
    return _HK_CITY_LOCALE_ALIASES.get(raw) or map_city_key(value)


def hk_localized_city_label(value: object) -> str:
    key=hk_localized_city_key(value)
    return _HK_CITY_RU_LABELS.get(key) or str(value or "")


def _hk_normalized_grid(value: object) -> str:
    match=re.fullmatch(r"\s*(-?\d+)\s*:\s*(-?\d+)\s*",str(value or ""))
    if not match:
        return ""
    return f"{int(match.group(1))}:{int(match.group(2))}"


def _hk_dedupe_localized_cabinet_rows(rows: list[dict]) -> list[dict]:
    grouped={}
    order=[]
    for original in rows:
        row=dict(original)
        city_key=hk_localized_city_key(row.get("city"))
        grid_key=_hk_normalized_grid(row.get("canonical_grid") or row.get("grid"))
        # Sentinel/tutorial rows and unknown city labels must never be locale-merged.
        if not city_key or not grid_key or grid_key=="-1:-1":
            token=("raw",str(row.get("key") or id(row)))
        else:
            token=("localized",city_key,grid_key)
        if token not in grouped:
            grouped[token]=[]
            order.append(token)
        grouped[token].append(row)

    result=[]
    for token in order:
        variants=grouped[token]
        if token[0]!="localized" or len(variants)==1:
            row=variants[0]
            if token[0]=="localized":
                row["city"]=hk_localized_city_label(row.get("city"))
            result.append(row)
            continue

        # Prefer the source with the most verified house knowledge.  This avoids
        # losing the rich historical map while keeping a newer live scan as a
        # retained variant instead of destructively unioning unrelated IDs.
        primary=max(
            variants,
            key=lambda row:(
                int(row.get("shared_known") or 0),
                int(bool(row.get("open_url"))),
                int(str(row.get("source_kind") or "")=="combined"),
                float(row.get("progress") or 0),
                int(row.get("buildings") or 0),
            ),
        )
        merged=dict(primary)
        merged["city"]=_HK_CITY_RU_LABELS.get(token[1]) or hk_localized_city_label(primary.get("city"))
        merged["canonical_grid"]=token[2]

        website_keys=sorted({
            str(key)
            for row in variants
            for key in (row.get("website_keys") or ([row.get("website_key")] if row.get("website_key") else []))
            if key
        })
        merged["website_keys"]=website_keys
        if not merged.get("website_key") and website_keys:
            merged["website_key"]=website_keys[0]
        if not merged.get("open_url"):
            with_url=next((row for row in variants if row.get("open_url")),None)
            if with_url:
                merged["open_url"]=with_url.get("open_url")
                merged["website_key"]=with_url.get("website_key") or merged.get("website_key")

        merged["localized_variant_count"]=len(variants)
        merged["localized_names"]=sorted({str(row.get("city") or "") for row in variants if row.get("city")})
        merged["localized_variants"]=[
            {
                "key":row.get("key"),
                "website_key":row.get("website_key"),
                "area_id":row.get("area_id"),
                "canonical_area_id":row.get("canonical_area_id"),
                "city":row.get("city"),
                "grid":row.get("grid"),
                "canonical_grid":row.get("canonical_grid"),
                "source_kind":row.get("source_kind"),
                "buildings":int(row.get("buildings") or 0),
                "unknown":int(row.get("unknown") or 0),
                "shared_known":int(row.get("shared_known") or 0),
                "progress":float(row.get("progress") or 0),
                "open_url":row.get("open_url") or "",
            }
            for row in sorted(
                variants,
                key=lambda row:(-int(row.get("shared_known") or 0),str(row.get("key") or "")),
            )
        ]
        merged["research_sources"]=[
            {
                "area_id":row.get("area_id"),
                "known":int(row.get("shared_known") or 0),
                "total":int(row.get("buildings") or 0),
                "unknown":int(row.get("unknown") or 0),
            }
            for row in variants
        ]
        result.append(merged)
    return result


_cabinet_maps_before_localized_dedupe = cabinet_maps


def cabinet_maps(member: dict) -> dict:
    payload=dict(_cabinet_maps_before_localized_dedupe(member))
    before=[dict(row) for row in payload.get("maps") or []]
    after=_hk_dedupe_localized_cabinet_rows(before)
    payload["maps"]=after
    payload["localized_dedupe"]=True
    payload["localized_rows_before"]=len(before)
    payload["localized_rows_after"]=len(after)
    payload["localized_rows_merged"]=max(0,len(before)-len(after))
    return payload


'''

# Install after the final visibility wrapper and before the following map_index.
marker_pos=s.find("# HK_MAP_VISIBILITY_ACCESS_V2\n")
if marker_pos<0:
    raise SystemExit("visibility marker position missing")
anchor_pos=s.find("def map_index() -> list[dict]:\n",marker_pos)
if anchor_pos<0:
    raise SystemExit("map_index after visibility wrapper missing")
s=s[:anchor_pos]+helpers+s[anchor_pos:]

# Locale-aware website hydration prevents future RU/EN scans from missing their
# historical website row only because the game returned another display language.
s=s.replace(
    "city_key = map_city_key(area.get(\"city_name\")) or map_city_key(area.get(\"city_id\"))",
    "city_key = hk_localized_city_key(area.get(\"city_name\")) or hk_localized_city_key(area.get(\"city_id\"))",
    1,
)
s=s.replace(
    "row_city = map_city_key(row[\"city\"])",
    "row_city = hk_localized_city_key(row[\"city\"])",
    1,
)

for check in (
    "HK_MAP_LOCALIZED_DEDUPE_R1",
    "def hk_localized_city_key",
    "def _hk_dedupe_localized_cabinet_rows",
    "_cabinet_maps_before_localized_dedupe = cabinet_maps",
    'payload["localized_rows_merged"]',
    'city_key = hk_localized_city_key(area.get("city_name"))',
    'row_city = hk_localized_city_key(row["city"])',
):
    req(check,"missing localized dedupe marker: "+check)

TARGET.write_text(s,encoding="utf-8")
print("HK_MAP_LOCALIZED_DEDUPE_R1_PATCH=PASS")
