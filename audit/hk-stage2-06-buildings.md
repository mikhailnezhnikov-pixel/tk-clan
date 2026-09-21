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

## Technical revalidation on userscript 1.17.12 — 2026-09-21

Read-only live verification run: `35563675405` — **PASS**.

Verified after the later Maps/auth changes:
- live userscript = public `panel.js` = repository baseline: PASS;
- userscript version `1.17.12`: PASS;
- `buildings-canon-core-20260920-r1` marker: PASS;
- plan filters and candidate calculation: PASS;
- already-active building exclusion: PASS;
- building open path remains behind `hkMutationGate`: PASS;
- favorite threshold uses actual post-open crystal metrics: PASS;
- authoritative rereads before open, after open, on completion and on error: PASS;
- Pause/Stop runner wiring: PASS;
- Buildings UI plan/run wiring: PASS;
- protected Maps shared runtime + concurrency 5: PASS;
- protected Explore E3 r9 marker: PASS.

No building was opened and no player state was mutated by this verification.

Current status:
**TECHNICAL_REVALIDATION_PASS_USER_ACTION_PENDING**

Only remaining gate before Stage 2.06 LIVE PASS:
1. open Buildings and calculate candidates;
2. verify the candidate list/filters;
3. open one eligible building through the confirmed UI;
4. if its actual crystal-room count reaches the configured threshold, verify favorite behavior;
5. rerun the plan and confirm the opened building is no longer offered and is present in active Buildings.

Do not advance Explore to E4 until this live action/state/rerun gate and Explore E3 single-building gate are confirmed.

## Userscript 1.17.13 startup handoff revalidation — 2026-09-21

After fixing the late-start BOOT deadlock:
- userscript version: `1.17.13`;
- core: `core-20260921-r15-late-login-handoff`;
- read-only Buildings verification run `35564647224`: **PASS**;
- live = public = baseline: PASS;
- Buildings canonical plan/action contract: PASS;
- Maps shared runtime and concurrency 5 preserved: PASS;
- Explore E3 r9 preserved: PASS.

Public E2E run `35564651904`: **PASS**.
Wars, Ratings, collector isolation, passive auth safety, Maps and Explore protected invariants all passed.

Current status remains:
**TECHNICAL_REVALIDATION_PASS_USER_ACTION_PENDING**

Only the real one-building user action/state/rerun confirmation remains before Stage 2.06 LIVE PASS.

