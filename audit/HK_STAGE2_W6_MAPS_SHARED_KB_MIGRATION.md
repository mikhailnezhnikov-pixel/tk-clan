# TopKing Stage 2 — W6 Dry-run and migration

Date: 2026-09-21
Stage: W6
Result: **PASS**

## Final dry-run

Evidence:
- `audit/hk-stage2-w6-final-dryrun.json`
- `audit/hk-stage2-w6-final-dryrun-summary.txt`
- `deploy/topking/hk-w6-migration-manifest.json`

Results:
- total website maps: **235**
- safe city+X:Y matches: **25**
- unresolved: **210**
- ambiguous: **0**
- duplicate canonical target groups: **0**
- source points: **2143**
- exact point → existing building matches: **2003**
- unmatched points: **136**
- ambiguous points: **4**
- new canonical building rows required: **0**
- existing NULL room candidates: **1732**
- same room values: **5**
- room conflicts: **266**, all against `game_live`

The 136 unmatched and 4 ambiguous points were not guessed or migrated. All 266 non-null game-live conflicts were preserved by the W5 provenance rules.

## Why W1's 26 became 25

`hk_dubai5335` is no longer safe to auto-link.

Read-only evidence: `audit/hk-stage2-w6-dubai-drift.json`.

Current canonical Dubai area `79cb821a-ecc1-4605-a96d-0d8ee504b74c` is X=53,Y=35. Historical website grid `53:35`, interpreted by the proven Y:X convention, would be X=35,Y=53. W6 therefore leaves Dubai unresolved instead of forcing reversed coordinates.

## OSM resolution

Public Overpass endpoints repeatedly timed out. W6 was split into independent per-map jobs so successful work was retained.

Five dense New York maps were completed through tiled OpenStreetMap `/api/0.6/map` reads:
- `hk_newyork2520`
- `hk_newyork3110`
- `hk_newyork3111`
- `hk_newyork3307`
- `hk_newyork4026`

Run `35518466801`: all five resolver jobs **PASS**.

Only exact point-in-polygon matches against existing canonical closed-way building IDs were accepted. No nearest-building guessing was used.

## HK Maps flag correction found during W6

Private HK Maps decoding proves:
- `crystals = meta & 0x07`
- `investment = bool(meta & 0x08)`

Therefore flag 7 means seven rooms without investment, not -1.

W6 corrected the migration manifest and the W4 website overlay. Hotfix patch:
`deploy/topking/patch_server_maps_flag_bitmask_w6.py`

Hotfix run `35518945365`: **PASS**.

Current live server SHA256:
`8fe91e74f49ecec9ea662e5ec85c32f07854a6dd5ed03864f70a3261a43dc245`

Invalid temporary negative room values were rejected by the importer and were never accepted as canonical room knowledge.

## Live migration

Final migration/verification run:
- run: `35519077891`
- job: `106099902200`
- result: **PASS**

Live status:
`audit/hk-stage2-maps-shared-kb-w6-live-status.txt`

Final verified live state:
- maps total: **235**
- resolved migrated: **25**
- unresolved untouched: **210**
- ambiguous: **0**
- area links: **25**
- point links: **2007**
- safe manifest points: **2003**
- game-live conflicts preserved: **266**
- map areas: **310**
- map buildings: **167690**
- geometry SHA256: `51d8b63e75f41b53c46dc1f6b087eaefb6be05c8004718863310f0d43e69500b`

Backup before the final control run:
`/var/lib/hamsterking-license/licenses.db.bak.w6.20260920-151724`

Several earlier runs failed only in verification after safe partial writes. Each partial state was audited before continuing. By the final PASS run:
- area links before/after: **25 → 25**
- point links before/after: **2007 → 2007**
- remaining NULL targets before final run: **0**
- final run fills: **0**
- second run fills: **0**
- idempotent rerun: **PASS**
- no concurrent area/building delta during final run

This proves the migration is rerunnable without duplicate districts or mappings and without overwriting authoritative non-null `game_live` knowledge.

## Userscript invariants

W6 did not change the userscript.

Current userscript SHA256:
`bddc55fc46bd4fe8da70c37799a35b74f3924015b071a3e692c532f0f7e6d766`

Verified:
- scanner: `maps-parallel-read-20260920-r6-safe5`
- read concurrency: **5**
- coordinates: `maps-coordinates-column-row-20260920-r2`
- coord revision: `column-row-v1`

## Gate

- resolved maps linked — **PASS**
- no duplicate canonical districts — **PASS**
- unresolved/ambiguous maps untouched and reported — **PASS**
- migration rerunnable/idempotent — **PASS**

**W6 = PASS.**

**W7 NOT STARTED.**
