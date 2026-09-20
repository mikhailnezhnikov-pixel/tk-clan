# HK Stage 2.06 — Buildings / Здания

## Status

**CANONICAL_TRANSFER_GAP_CONFIRMED**

Pinned donor: exact uploaded Kokkaras file.

Historical `stage2i-buildings-explore-20260919-r1` technical roundtrip only verified the read-only Buildings page and district/map Explore page. It does not establish donor functional parity.

Bug:
`audit/hk-stage2-bug-buildings-canonical-transfer-gap.md`

Next:
transfer canonical Buildings automation only, deploy, then perform live-path checks before moving to Explore.


## Canonical core r1

Transferred from pinned Kokkaras donor into current HK runtime:
- donor defaults: minimum crystals 3, favorite threshold 2, normal buildings;
- candidate planning restricted to player-owned districts;
- shared HK map detail used for known crystal-room count and normal/investment type, avoiding any runtime dependency on Kokkaras;
- already active buildings are excluded;
- explicit candidate preview before mutation;
- fresh authoritative `/player/me` before each open;
- opening `/player/building?building_id=...` is forced through `hkMutationGate` even though the same endpoint is read-only for already active building study;
- 409 active-building capacity stops the run safely;
- actual opened building events are re-read and crystal/event metrics recalculated;
- favorites use `/player/building/favorite/add` only after actual crystal count reaches the configured threshold;
- favorite capacity failure disables further favorite requests for the run;
- Runner pause/stop support;
- donor 3–8 second between-building pacing;
- authoritative state reread after each successful open and at completion.

Marker:
`HK_BUILDINGS_CANON_REV = 'buildings-canon-core-20260920-r1'`

Deploy verification:
- exact input live SHA256: `0e168e81ff6e4ee42400f99aaad8a4fb9359bcfbdc051d56c981d0adcbf247e7`;
- Python compile: PASS;
- patch invariants: PASS;
- JS syntax: PASS;
- backup/deploy: PASS;
- service active: PASS;
- public byte equality: PASS;
- live/public SHA256: `0931ee3eb65a16f9dd768fe51b9a84b897620e011c51ee9e0226d92f37b9e686`;
- baseline sync: PASS.

Technical evidence:
`audit/hk-stage2-06-buildings-r1-live-status.txt`

Current status:
**CANON_CORE_R1_LIVE_CANDIDATE**

Required live user check before Stage 2.06 LIVE PASS:
1. open Buildings and calculate candidates;
2. verify filters/candidate list;
3. open at least one eligible building;
4. if crystal threshold matches, verify favorite action;
5. refresh/rerun and confirm the opened building disappears from candidates and appears in active Buildings.
