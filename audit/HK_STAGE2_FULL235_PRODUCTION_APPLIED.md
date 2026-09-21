# FULL235 production apply — verified

- Applied: 2026-09-21
- GitHub Actions run: 35564678695
- Job: 106224055713
- Result: PASS
- One-time arm: CONSUMED

## Source proof

- Maps: 235
- Source building IDs: 152593
- Source archive gzip SHA-256: a4b84c5239168182702090efe0b7241b54295942d63e5f020539092694e0a3e1
- HKID1 raw SHA-256: 1ddcadbb50e5a88555a6772538e56476575a771edc22fb85200299c8cbc28f48
- HKA2 raw SHA-256: 728d33fbc57105109cd67f3b46de61d27bc2c4c597b9b88012952c0ad3cf0dbf
- Semantic row SHA-256: e7c5ea74657289f09bc69049b5e05abf5b5cb3ca577f7d63d67342eccde8f594
- Compact semantic decode: PASS
- Exact pre-write resolver: 160 existing + 75 original UUID, conflicts 0

## Safety gates

- Pre-write exact building-ID match: PASS
- Pre-stage DB backup: /var/lib/hamsterking-license/licenses.db.bak.full235-prestage.20260921-053018
- Built-in apply DB backup: /var/lib/hamsterking-license/licenses.db.bak.full235.20260921-053021
- Server resolver: PASS
- Stage purge after apply: PASS
- game_live priority: PASS
- Protected game_live rows checked: 17410
- Source ownership for all 152593 IDs: PASS
- Idempotency terminal gate: PASS
- OSM/Overpass: NOT USED

## Production result

- Canonical areas: 385
- HK map area links: 235
- Full import provenance links: 235
- map_buildings rows: 222153
- Website maps without canonical link: 0
- Site+Script canonical areas: 235
- Script-only canonical areas: 150
- Site-only canonical areas: 0
- Unified canonical rows: 385

## Code safety

- Live server SHA before: 4c98d3dee4f76dddbff073293688e665cc596171d05ae04d9e159849c7c4f753
- Live server SHA after: 4c98d3dee4f76dddbff073293688e665cc596171d05ae04d9e159849c7c4f753
- Server code unchanged: PASS
- Userscript/backend rollback: NO
