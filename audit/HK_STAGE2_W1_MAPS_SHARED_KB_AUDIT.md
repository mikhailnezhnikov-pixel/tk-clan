# TopKing Stage 2 — W1 Maps ↔ Website shared knowledge base audit

Date: 2026-09-20  
Stage: W1 — Audit only  
Result: **PASS**  
Live mutation: **NONE**

## Scope and guardrails

This audit was executed from the current Stage 2 checkpoint only. It inspected:

- `map_areas`
- `map_buildings`
- `map_area_aliases`
- `hk_maps_catalog`
- `hk_map_points`
- `/api/v1/maps/list`
- `/api/v1/maps/detail`
- `/api/v1/maps/submit`
- HK Maps / Kokkaras import paths
- Personal Cabinet → Maps read path
- the current 235-map website catalog

No live schema changes, writes, service restart, deploy, userscript change, scanner change, or Explore change were performed.

A temporary GitHub Actions probe was used only to open the live SQLite database with URI `mode=ro` and print counts/match candidates. Run: `35508706970`, job: `106072758285`. The temporary workflow file was removed immediately after the read-only result was collected.

## Preflight sources

Read before the audit:

- `reference/topking/REFERENCE.json`
- `docs/HK_NEW_CHAT_START.md`
- `audit/HK_STAGE2_CHECKPOINT.md`
- current canonical server source/audits
- current TopKing userscript baseline
- pinned Kokkaras/HK Maps donor reference

The donor remains the pinned HK Control Panel / HK Maps source defined in `REFERENCE.json`; mutable upstream content was not treated as authoritative over the pinned reference.

## 1. Current data flow

### A. Userscript / player scans → canonical knowledge layer

The TopKing userscript gathers owned district/building observations from the game and submits them through:

`/api/v1/maps/submit`

The backend path is:

`/maps/submit → submit_map_area() → canonical_map_area() → map_areas + map_buildings + map_area_aliases`

Canonical behavior:

1. incoming `area_id` first resolves through `map_area_aliases`;
2. if no alias exists and coordinates are present, the backend can match an existing canonical area by city identity + exact `x,y`;
3. the canonical district is stored in `map_areas`;
4. building knowledge is stored/enriched in `map_buildings`;
5. source aliases point to the canonical `area_id`.

The current coordinate contract from the live candidate is `column-row-v1`.

### B. Canonical reads used by the userscript

`/api/v1/maps/list` reads the canonical knowledge layer only:

`map_areas LEFT JOIN map_buildings` plus aliases from `map_area_aliases`.

`/api/v1/maps/detail` resolves an alias to a canonical `area_id`, then reads:

- one row from `map_areas`;
- its rows from `map_buildings`.

Therefore the userscript's “uploaded/shared maps” view is currently the canonical `map_areas/map_buildings` index. It is **not** the 235-map Personal Cabinet catalog.

### C. Website 235-map import → website geometry/catalog layer

The historical HK Maps index import uses:

`import_hk_maps_index() → hk_maps_catalog`

The compact point import uses:

`import_hk_map_points() → hk_map_points`

and sets an `open_url` for the website viewer.

This path does **not** call `submit_map_area()` and does **not** write:

- `map_areas`
- `map_buildings`
- `map_area_aliases`

So the 235 website maps currently form a separate data island.

### D. Personal Cabinet → Maps read path

Personal Cabinet calls its cabinet `/maps` route, which reads:

`SELECT * FROM hk_maps_catalog ...`

Map detail/data reads:

`hk_maps_catalog JOIN hk_map_points`

and may additionally return the installed full private geometry package.

The cabinet path currently does **not** join or read `map_areas` / `map_buildings` for crystal-room knowledge.

### E. Kokkaras single-map canonical importer

A separate CLI path exists:

`server.py --import-kokkaras-map FILE.json.gz → import_kokkaras_map() → submit_map_area()`

That importer converts HK Maps building properties into canonical building knowledge, including:

- `building_id`
- `crystals → room_count`
- `is_investment → is_invest`
- `faction`
- `building_generator → building_type`

This is a canonical import path, but it is **not** the path that populated the current 235 website catalog.

## 2. Current live database snapshot

Read-only snapshot result:

| Table | Rows |
|---|---:|
| `map_areas` | 301 |
| `map_buildings` | 162170 |
| `map_area_aliases` | 301 |
| `hk_maps_catalog` | 235 |
| `hk_map_points` | 235 |

Additional facts:

- canonical areas with coordinates: **301**
- compact website map points: **26378**
- alias rows: **301**
- non-self aliases in this snapshot: **0**
- website maps: **235**
- website point rows: **235**

The current `hk_maps_catalog` schema has no `canonical_area_id` and there is no existing foreign-key relation from a website `map_key` to a canonical district.

## 3. Coordinate interpretation and automatic matching rule

A direct interpretation of website `grid` as canonical `X:Y` produced **0/235** matches.

That is not the correct historical HK Maps convention.

The existing Kokkaras importer explicitly documents that HK Maps labels district coordinates as **Y:X**, while the TopKing canonical/mobile representation is **X:Y**. Its conversion is equivalent to:

- HK Maps `grid = Y:X`
- canonical `map_areas.x = X`
- canonical `map_areas.y = Y`

Therefore discovery for historical website rows must use:

`(normalized city, canonical x = grid second component, canonical y = grid first component)`

Do **not** parse coordinate digits from `map_key`. `map_key` is an opaque website primary key; `city` + `grid` are the discovery fields.

Match safety rule for W2/W6:

1. normalize website city and canonical city identity;
2. parse website `grid` as historical `Y:X`;
3. query exact canonical `(city, x=X, y=Y)`;
4. resolve any result through `map_area_aliases`;
5. exactly one canonical result → safe auto-link candidate;
6. zero → unresolved;
7. more than one → ambiguous, no automatic write.

## 4. Automatic link result for the 235 maps

**Automatically linkable: 26/235**  
**Ambiguous: 0**  
**Not found in current canonical `map_areas`: 209**

All 26 matches resolve to a single canonical area. There are **0 duplicate canonical targets** among these 26 candidates.

### Exact `map_key → canonical_area_id` candidates

| map_key | City | HK Maps grid (Y:X) | canonical_area_id |
|---|---|---:|---|
| `hk_dubai5335` | Dubai | `53:35` | `79cb821a-ecc1-4605-a96d-0d8ee504b74c` |
| `hk_lagos0843` | Lagos | `08:43` | `2e3b1557-06f4-4de7-a541-15626b050a0c` |
| `hk_moscow1226` | Moscow | `12:26` | `9ea6ff78-b881-45b3-b92d-a8f1da8eca05` |
| `hk_newyork0001` | New York | `00:01` | `645322fd-a524-4d49-af9a-4611a156e440` |
| `hk_newyork0002` | New York | `00:02` | `a221e256-54f4-439d-a92e-9c6c64b4ec72` |
| `hk_newyork0438` | New York | `04:38` | `c6445d3c-8413-406c-b53e-adbea4dd88cc` |
| `hk_newyork1437` | New York | `14:37` | `14625896-9b5e-4596-b06d-4491dec39c06` |
| `hk_newyork1706` | New York | `17:06` | `73218a2b-5c84-464b-9576-b330a07598b4` |
| `hk_newyork2508` | New York | `25:08` | `deaa84a5-af53-427b-a5a3-3b22ac130065` |
| `hk_newyork2520` | New York | `25:20` | `7e87da1c-f11b-4de2-8190-cb0a84a46e9b` |
| `hk_newyork2528` | New York | `25:28` | `27e4355e-0b1f-4b16-b0a7-21aba4087dac` |
| `hk_newyork3110` | New York | `31:10` | `aa59c660-6824-444c-92a6-36b4afa8457d` |
| `hk_newyork3111` | New York | `31:11` | `b94ea2a3-a4da-4b69-8ac3-13e5cc88a5f2` |
| `hk_newyork3307` | New York | `33:07` | `7bc95c84-0ace-4ebc-82cf-746d3ebb9205` |
| `hk_newyork3504` | New York | `35:04` | `ed33d8c9-a814-4fdc-827a-496432d2ca7a` |
| `hk_newyork3707` | New York | `37:07` | `c7f9cd65-c03f-4e04-a4cf-1f09b6646da7` |
| `hk_newyork4016` | New York | `40:16` | `65f69e15-b3b4-405c-a00d-839a190f6025` |
| `hk_newyork4026` | New York | `40:26` | `6618d3a0-91c9-44ff-8029-eba045469962` |
| `hk_newyork4617` | New York | `46:17` | `25f3ff88-45ff-427c-a33b-c7f065f10838` |
| `hk_newyork4639` | New York | `46:39` | `51bb9f60-9d96-45bd-8730-c102eac86237` |
| `hk_newyork4727` | New York | `47:27` | `41c07d67-ad0c-486a-abfe-c829367a3da1` |
| `hk_newyork4825` | New York | `48:25` | `4fd66467-4a03-4d0b-9411-fe045f7a97a6` |
| `hk_riodejaneiro0217` | Rio De Janeiro | `02:17` | `241f9996-7efc-491b-8211-1412143d1c71` |
| `hk_riodejaneiro1730` | Rio De Janeiro | `17:30` | `73543631-5b59-4a01-802c-a7ea8edec039` |
| `hk_saintpetersburg0001` | Saint Petersburg | `00:01` | `09e52a7f-da65-4102-9508-40424593ab7b` |
| `hk_saintpetersburg0003` | Saint Petersburg | `00:03` | `fbd2e69c-09fd-44b8-b71f-182c01652d9c` |

## 5. Ambiguous maps

**None.**

No website map produced more than one canonical candidate under the correct historical `Y:X → X:Y` conversion.

## 6. Not-found maps (209)

These maps have no current canonical `map_areas` row with the same normalized city and converted coordinates.

- **Auckland (11)**: `hk_auckland0115` (`01:15`), `hk_auckland0211` (`02:11`), `hk_auckland0224` (`02:24`), `hk_auckland0312` (`03:12`), `hk_auckland0902` (`09:02`), `hk_auckland1405` (`14:05`), `hk_auckland1515` (`15:15`), `hk_auckland1925` (`19:25`), `hk_auckland2220` (`22:20`), `hk_auckland2816` (`28:16`), `hk_auckland2922` (`29:22`)
- **Berlin (21)**: `hk_berlin1427` (`14:27`), `hk_berlin1717` (`17:17`), `hk_berlin1718` (`17:18`), `hk_berlin1818` (`18:18`), `hk_berlin1819` (`18:19`), `hk_berlin1915` (`19:15`), `hk_berlin2218` (`22:18`), `hk_berlin2315` (`23:15`), `hk_berlin2317` (`23:17`), `hk_berlin2319` (`23:19`), `hk_berlin2412` (`24:12`), `hk_berlin2417` (`24:17`), `hk_berlin2513` (`25:13`), `hk_berlin2514` (`25:14`), `hk_berlin2616` (`26:16`), `hk_berlin2620` (`26:20`), `hk_berlin2621` (`26:21`), `hk_berlin3417` (`34:17`), `hk_berlin3530` (`35:30`), `hk_berlin3626` (`36:26`), `hk_berlin3917` (`39:17`)
- **Dubai (15)**: `hk_dubai2961` (`29:61`), `hk_dubai4229` (`42:29`), `hk_dubai4329` (`43:29`), `hk_dubai4433` (`44:33`), `hk_dubai4632` (`46:32`), `hk_dubai5216` (`52:16`), `hk_dubai5315` (`53:15`), `hk_dubai5316` (`53:16`), `hk_dubai5414` (`54:14`), `hk_dubai6210` (`62:10`), `hk_dubai6212` (`62:12`), `hk_dubai6308` (`63:08`), `hk_dubai6409` (`64:09`), `hk_dubai6808` (`68:08`), `hk_dubai7003` (`70:03`)
- **Lagos (20)**: `hk_lagos0228` (`02:28`), `hk_lagos0242` (`02:42`), `hk_lagos2029` (`20:29`), `hk_lagos2150` (`21:50`), `hk_lagos2234` (`22:34`), `hk_lagos2256` (`22:56`), `hk_lagos2314` (`23:14`), `hk_lagos2549` (`25:49`), `hk_lagos2712` (`27:12`), `hk_lagos2750` (`27:50`), `hk_lagos3141` (`31:41`), `hk_lagos3228` (`32:28`), `hk_lagos3235` (`32:35`), `hk_lagos3322` (`33:22`), `hk_lagos4005` (`40:05`), `hk_lagos4134` (`41:34`), `hk_lagos4213` (`42:13`), `hk_lagos4401` (`44:01`), `hk_lagos4815` (`48:15`), `hk_lagos4822` (`48:22`)
- **London (18)**: `hk_london0711` (`07:11`), `hk_london1834` (`18:34`), `hk_london3025` (`30:25`), `hk_london3031` (`30:31`), `hk_london3124` (`31:24`), `hk_london3125` (`31:25`), `hk_london3324` (`33:24`), `hk_london3327` (`33:27`), `hk_london3423` (`34:23`), `hk_london3424` (`34:24`), `hk_london3516` (`35:16`), `hk_london3608` (`36:08`), `hk_london3740` (`37:40`), `hk_london3817` (`38:17`), `hk_london3924` (`39:24`), `hk_london4224` (`42:24`), `hk_london4827` (`48:27`), `hk_london4837` (`48:37`)
- **Los Angeles (14)**: `hk_losangeles1325` (`13:25`), `hk_losangeles1411` (`14:11`), `hk_losangeles1832` (`18:32`), `hk_losangeles1839` (`18:39`), `hk_losangeles3031` (`30:31`), `hk_losangeles3222` (`32:22`), `hk_losangeles3428` (`34:28`), `hk_losangeles3524` (`35:24`), `hk_losangeles3638` (`36:38`), `hk_losangeles3734` (`37:34`), `hk_losangeles4037` (`40:37`), `hk_losangeles4136` (`41:36`), `hk_losangeles4137` (`41:37`), `hk_losangeles5334` (`53:34`)
- **Minsk (3)**: `hk_minsk1204` (`12:04`), `hk_minsk1306` (`13:06`), `hk_minsk1512` (`15:12`)
- **Moscow (23)**: `hk_moscow0100` (`01:00`), `hk_moscow0112` (`01:12`), `hk_moscow1107` (`11:07`), `hk_moscow1207` (`12:07`), `hk_moscow1208` (`12:08`), `hk_moscow1409` (`14:09`), `hk_moscow1601` (`16:01`), `hk_moscow1702` (`17:02`), `hk_moscow1817` (`18:17`), `hk_moscow1819` (`18:19`), `hk_moscow1820` (`18:20`), `hk_moscow1918` (`19:18`), `hk_moscow1919` (`19:19`), `hk_moscow1921` (`19:21`), `hk_moscow2018` (`20:18`), `hk_moscow2019` (`20:19`), `hk_moscow2021` (`20:21`), `hk_moscow2118` (`21:18`), `hk_moscow2120` (`21:20`), `hk_moscow2121` (`21:21`), `hk_moscow2218` (`22:18`), `hk_moscow2221` (`22:21`), `hk_moscow2827` (`28:27`)
- **New York (26)**: `hk_newyork0332` (`03:32`), `hk_newyork0426` (`04:26`), `hk_newyork1108` (`11:08`), `hk_newyork1608` (`16:08`), `hk_newyork2315` (`23:15`), `hk_newyork2325` (`23:25`), `hk_newyork2332` (`23:32`), `hk_newyork2333` (`23:33`), `hk_newyork2421` (`24:21`), `hk_newyork2422` (`24:22`), `hk_newyork2440` (`24:40`), `hk_newyork2518` (`25:18`), `hk_newyork2521` (`25:21`), `hk_newyork2522` (`25:22`), `hk_newyork2620` (`26:20`), `hk_newyork2819` (`28:19`), `hk_newyork3030` (`30:30`), `hk_newyork3208` (`32:08`), `hk_newyork3210` (`32:10`), `hk_newyork3226` (`32:26`), `hk_newyork3314` (`33:14`), `hk_newyork3507` (`35:07`), `hk_newyork3528` (`35:28`), `hk_newyork3830` (`38:30`), `hk_newyork3832` (`38:32`), `hk_newyork4933` (`49:33`)
- **Paris (12)**: `hk_paris1402` (`14:02`), `hk_paris2115` (`21:15`), `hk_paris2822` (`28:22`), `hk_paris3022` (`30:22`), `hk_paris3122` (`31:22`), `hk_paris3222` (`32:22`), `hk_paris3223` (`32:23`), `hk_paris3322` (`33:22`), `hk_paris3323` (`33:23`), `hk_paris3324` (`33:24`), `hk_paris3718` (`37:18`), `hk_paris4949` (`49:49`)
- **Rio De Janeiro (6)**: `hk_riodejaneiro1435` (`14:35`), `hk_riodejaneiro3430` (`34:30`), `hk_riodejaneiro3530` (`35:30`), `hk_riodejaneiro4326` (`43:26`), `hk_riodejaneiro5437` (`54:37`), `hk_riodejaneiro5441` (`54:41`)
- **Saint Petersburg (11)**: `hk_saintpetersburg1819` (`18:19`), `hk_saintpetersburg1917` (`19:17`), `hk_saintpetersburg1921` (`19:21`), `hk_saintpetersburg2020` (`20:20`), `hk_saintpetersburg2121` (`21:21`), `hk_saintpetersburg2218` (`22:18`), `hk_saintpetersburg2219` (`22:19`), `hk_saintpetersburg2220` (`22:20`), `hk_saintpetersburg2320` (`23:20`), `hk_saintpetersburg2517` (`25:17`), `hk_saintpetersburg2607` (`26:07`)
- **Singapore (5)**: `hk_singapore3416` (`34:16`), `hk_singapore3611` (`36:11`), `hk_singapore3818` (`38:18`), `hk_singapore4014` (`40:14`), `hk_singapore4111` (`41:11`)
- **Sydney (9)**: `hk_sydney0412` (`04:12`), `hk_sydney0526` (`05:26`), `hk_sydney0527` (`05:27`), `hk_sydney0627` (`06:27`), `hk_sydney1133` (`11:33`), `hk_sydney1415` (`14:15`), `hk_sydney1520` (`15:20`), `hk_sydney2105` (`21:05`), `hk_sydney2107` (`21:07`)
- **Tokyo (5)**: `hk_tokyo2210` (`22:10`), `hk_tokyo2314` (`23:14`), `hk_tokyo2512` (`25:12`), `hk_tokyo2714` (`27:14`), `hk_tokyo3919` (`39:19`)
- **Washington (10)**: `hk_washington0019` (`00:19`), `hk_washington0310` (`03:10`), `hk_washington0402` (`04:02`), `hk_washington0727` (`07:27`), `hk_washington1418` (`14:18`), `hk_washington1511` (`15:11`), `hk_washington1710` (`17:10`), `hk_washington1819` (`18:19`), `hk_washington2207` (`22:07`), `hk_washington2518` (`25:18`)

These rows must remain unlinked in W2. They are not evidence that the website data is invalid; they simply have no current canonical district row to attach to.

## 7. Exact durable relation proposed for W2

To keep website geometry and canonical game knowledge separate, use an explicit bridge table rather than embedding building knowledge into `hk_maps_catalog`:

```sql
CREATE TABLE hk_map_area_links (
    map_key TEXT PRIMARY KEY,
    canonical_area_id TEXT NOT NULL,
    match_method TEXT NOT NULL,
    linked_at INTEGER NOT NULL,
    FOREIGN KEY (map_key) REFERENCES hk_maps_catalog(map_key) ON DELETE CASCADE,
    FOREIGN KEY (canonical_area_id) REFERENCES map_areas(area_id) ON DELETE CASCADE
);

CREATE INDEX idx_hk_map_area_links_canonical_area
    ON hk_map_area_links(canonical_area_id);
```

Cardinality for W2:

- each `map_key` has **0 or 1** canonical link;
- unresolved/ambiguous maps have no link row;
- `canonical_area_id` is always the resolved canonical target, never an alias source ID;
- do **not** add `UNIQUE(canonical_area_id)` in W2; W6 must explicitly report historical duplicate-map cases before any stronger constraint is considered.

Recommended `match_method` values for the staged work:

- `exact_area_id` — preferred when a future/new import carries the real game area ID;
- `city_grid_yx` — historical 235-map discovery using `city + grid(Y:X)`.

The 26 W1 candidates were discovered with `city_grid_yx` only. **No relation was persisted during W1.**

## 8. Root architectural gap

The live server already contains both layers in the same SQLite database, but they are logically disconnected:

`hk_maps_catalog/hk_map_points`  
**no relation**  
`map_areas/map_buildings/map_area_aliases`

That is why:

- player scans enrich the userscript canonical map view but do not automatically update the Personal Cabinet map knowledge;
- the 235 website maps can render geometry but their known room/crystal values do not automatically become shared userscript knowledge;
- the website currently cannot ask “which canonical district does this `map_key` represent?”

W2 should add only the durable relation and a one-map pilot. No building migration should happen until W3/W6.

## 9. W1 gate

- exact current flow: **PASS**
- 235-map count verified live: **PASS**
- automatic link count: **26**
- ambiguous count: **0**
- unresolved count: **209**
- exact 26 mappings recorded: **PASS**
- exact relation design recorded: **PASS**
- live mutation: **NONE**
- schema mutation: **NONE**
- deploy/restart: **NONE**
- Explore touched: **NO**

**W1 = PASS. W2 NOT STARTED. Stop here until explicit user instruction.**
