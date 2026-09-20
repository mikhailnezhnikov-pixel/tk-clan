# Authorized HK map uploads

W7 upload files are gzip-compressed JSON and contain **no login/session/cookie data**.

Required top-level fields:

- `catalog` — HK Maps catalog row; must contain `key`, `city`, `grid`.
- `points` — compact delta point array: `[dLon,dLat,meta,...]`.
- `meta` — canonical district metadata:
  - `area_id`
  - `city_id`
  - `city_name`
  - `x`, `y`
  - `coord_revision`: `column-row-v1`, `canonical-xy`, or explicitly `historical-yx`.
- `buildingsGeoJSON` — authorized full source GeoJSON. Game features must preserve `properties.building_id`; `crystals`, `is_investment`, `faction`, and `building_generator` are consumed when present.
- optional `point_links` — exact `point_index → building_id` pairs. When omitted, the server derives only unique point-in-polygon matches from the supplied full geometry.

Import command:

`server.py --import-hk-authorized-map FILE.json.gz`

The import is idempotent and performs website storage + canonical relation + shared knowledge write in the same import path. It does not require a later synchronization job. Existing non-null `game_live` knowledge remains authoritative.
