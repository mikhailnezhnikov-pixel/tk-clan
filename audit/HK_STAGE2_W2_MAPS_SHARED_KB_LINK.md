# TopKing Stage 2 — W2 Maps ↔ Website shared knowledge link

Date: 2026-09-20  
Stage: W2 — Link website map ↔ canonical game district  
Result: **PASS**

## Goal

Add a durable relation:

`map_key → canonical_area_id`

without migrating website building knowledge yet.

## Implemented schema

Added:

```sql
CREATE TABLE IF NOT EXISTS hk_map_area_links (
    map_key TEXT PRIMARY KEY,
    canonical_area_id TEXT NOT NULL,
    match_method TEXT NOT NULL CHECK(match_method IN ('exact_area_id','city_grid_yx')),
    linked_at INTEGER NOT NULL,
    FOREIGN KEY (map_key) REFERENCES hk_maps_catalog(map_key) ON DELETE CASCADE,
    FOREIGN KEY (canonical_area_id) REFERENCES map_areas(area_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_hk_map_area_links_canonical_area
    ON hk_map_area_links(canonical_area_id);
```

No uniqueness constraint was added on `canonical_area_id`, because W6 must explicitly inspect any historical multiple-map-to-one-district cases before stronger constraints are considered.

## Resolution rules

Server marker:

`HK_MAP_AREA_LINKS_W2_V1`

Two supported methods:

1. `exact_area_id`
   - resolve a supplied game area ID through `map_area_aliases`;
   - persist only the resolved canonical target.

2. `city_grid_yx`
   - for historical website maps;
   - read `hk_maps_catalog.city` + `grid`;
   - historical HK Maps grid is `Y:X`;
   - canonical TopKing coordinates are `x=X, y=Y`;
   - require exactly one canonical district candidate;
   - persist the resulting canonical ID.

Added reusable server helpers:

- `_canonical_area_id()`
- `discover_hk_map_area()`
- `link_hk_map_area()`
- `hk_map_area_link()`

Added controlled CLI:

`server.py --link-hk-map-area MAP_KEY [AREA_ID]`

The CLI links one map at a time. It does not import building knowledge.

## Build verification

Build run: `35508970854` — **PASS**

Candidate server SHA256:

`1fe9fc44953713032bad755bc658233e881cba1941d7fae53747e6d27e7a7e3e`

Temporary DB regression proved:

- bridge table creation: PASS;
- historical `Y:X` discovery: PASS;
- exact `area_id` resolution through alias: PASS;
- alias-based `map_detail()` still resolves: PASS;
- rerun remains one bridge row: PASS;
- no new `map_areas` row is created: PASS;
- no building migration: PASS.

## Live pilot

Pilot website map:

`hk_moscow1226`

Website coordinates:

`Moscow / 12:26` as historical `Y:X`

Canonical coordinates:

`x=26, y=12`

Resolved canonical district:

`9ea6ff78-b881-45b3-b92d-a8f1da8eca05`

Persisted relation:

```text
hk_moscow1226
  → 9ea6ff78-b881-45b3-b92d-a8f1da8eca05
  match_method = city_grid_yx
```

## Deployment evidence

First deployment attempt: `35509018962`

- failed during read-only precheck because inline SSH/Python quoting stripped SQL string quotes;
- failure happened before patch/deploy/write steps;
- **no live mutation occurred in that failed run**.

Transport was corrected to copy temporary Python verification files over SSH.

Successful deployment run:

`35509058115` — **PASS**

Live status commit:

`753bc512077f27df652e2877426cca726a8c7585`

Live server SHA256:

`1fe9fc44953713032bad755bc658233e881cba1941d7fae53747e6d27e7a7e3e`

Userscript/public SHA256 remained unchanged:

`1932f3984a330edf234c02e80c0f27e1b845b299f3bb09875d166397dcded9d6`

## Live PASS checks

- `hk_map_area_links` exists: PASS;
- bridge rows: **1**;
- pilot link target is exact expected canonical district: PASS;
- pilot match method is `city_grid_yx`: PASS;
- exact Moscow `x=26,y=12` canonical district count: **1**;
- duplicate district created: **NO**;
- alias for pilot canonical district still resolves to itself: PASS;
- `hk_maps_catalog`: **235**;
- `hk_map_points`: **235**;
- geometry migration/duplication: **NO**;
- building knowledge migration: **NO**;
- userscript changed: **NO**;
- Explore changed: **NO**;
- scanner safety/concurrency changed: **NO**.

## W2 gate

PASS gate required:

1. one website map linked to exactly one canonical district — **PASS**;
2. no duplicate district created — **PASS**;
3. aliases still resolve correctly — **PASS**.

**W2 = PASS.**

W3 is **NOT STARTED**.  
Do not migrate the remaining 25 resolvable maps or any building knowledge until W3 is explicitly started.
