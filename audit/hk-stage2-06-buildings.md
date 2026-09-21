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

## Buildings UI r2 — userscript 1.17.14 (2026-09-21)

User screenshot exposed a presentation regression in the Buildings page:
- generic `.hk-secondary{width:100%}` made the per-building `Считать` button consume almost the whole row;
- the building UUID column collapsed to a few pixels and wrapped one character per line;
- active-building rows became extremely tall and visually unusable.

UI-only fix:
- userscript `1.17.14`;
- core `core-20260921-r16-buildings-ui`;
- marker `buildings-ui-20260921-r2`;
- dedicated Buildings header instead of generic Clan grid;
- compact 3-field settings grid;
- two-column action row;
- separate Opening plan block with candidate/active/mapped counters;
- compact candidate rows;
- separate Active buildings section;
- building IDs stay on one line with ellipsis + full value in tooltip;
- per-building `Считать` is a compact right-side button;
- responsive mobile rules added.

Safety:
- `runBuildingsCanonical()` action block remained byte-identical during the patch;
- no Buildings mutation logic changed;
- Maps shared runtime + concurrency 5 preserved;
- Explore E3 r9 preserved;
- passive auth safety preserved.

Verification:
- predeploy run `35565025652`: PASS;
- deploy/public round-trip run `35565072034`: PASS;
- loader aligned to core r16; public loader verification: PASS;
- Buildings live technical revalidation run `35565201926`: PASS;
- public E2E run `35565212100`: PASS.

Current status:
**UI_R2_LIVE_CANDIDATE_USER_VISUAL_AND_ACTION_CHECK_PENDING**

Next:
1. reload game and HK;
2. open City → Buildings;
3. visually confirm layout;
4. calculate candidates;
5. perform one controlled eligible-building open;
6. rerun plan and confirm opened building is removed from candidates and appears among active buildings.

## Buildings UI r3 — active list removed (2026-09-21)

User requested that the page not display the full list of already-active buildings.

Delivered in userscript `1.17.15`:
- core `core-20260921-r17-buildings-ui-compact`;
- marker `buildings-ui-20260921-r3`;
- removed the full Active buildings list;
- removed per-active-building Read buttons from this page;
- retained only the useful active-slot count in the Opening plan;
- candidate list and all opening/favorite logic unchanged.

Safety:
- `runBuildingsCanonical()` action block remained byte-identical;
- Maps shared runtime + concurrency 5 preserved;
- Explore E3 r9 preserved;
- passive auth safety preserved.

Verification:
- predeploy run `35565570357`: PASS;
- deploy/public round-trip run `35565665494`: PASS;
- public loader core-r17 verification run `35565756294`: PASS;
- Buildings live verification run `35565811595`: PASS;
- `buildings_active_list_hidden=PASS`;
- `buildings_active_count_kept=PASS`;
- public E2E run `35565773961`: PASS.

Current status:
**UI_R3_LIVE_CANDIDATE_USER_VISUAL_AND_ACTION_CHECK_PENDING**

## Buildings active-slot semantics r1 — userscript 1.17.16 (2026-09-21)

User live test exposed a real contradiction:
- calculated plan showed **92 candidates**;
- the same page showed **Active 2175/698**;
- pressing Open then reported that no eligible unopened buildings existed.

Root cause confirmed from a read-only live `/player/me` schema diagnostic:
- top-level `buildings` contains **2175 known building records**, not only active buildings;
- `player.max_buildings=698`;
- `player.player_active_building=467`;
- exactly **467** building rows have numeric `next_tier_level`;
- the old helper treated all 2175 known rows as active;
- therefore free capacity became 0 and the runner sliced the 92-plan down to an empty execution list.

Fix delivered in userscript `1.17.16`:
- core: `core-20260921-r18-buildings-active-fix`;
- marker: `buildings-active-semantics-20260921-r1`;
- active-slot count uses authoritative `player_active_building`;
- row-level active IDs use `next_tier_level` only when that row count agrees with the authoritative active count;
- schema mismatch fails closed instead of guessing;
- free slots now use `max_buildings - player_active_building`;
- candidates and no-free-slots are now separate states/messages.

Live evidence:
- schema diagnostic run `35567254035`: PASS;
- refined activity diagnostic run `35567342973`: PASS;
- observed schema: 2175 known / 467 active / max 698;
- predeploy fixture run `35567569494`: PASS;
- expected fixture result: 467 active, 698 max, **231 free**;
- deploy/public round-trip run `35567837973`: PASS;
- loader core-r18 verification run `35567970830`: PASS;
- Buildings live verification run `35567975463`: PASS;
- `buildings_active_semantics=PASS`;
- `buildings_capacity_reported_active=PASS`;
- public E2E retry run `35568104811`: **PASS**;
- Wars/Ratings/site/timers/userscript safety: PASS;
- Maps/Explore protected invariants: PASS.

Current status:
**ACTIVE_SEMANTICS_R1_LIVE_CANDIDATE_USER_ACTION_CHECK_PENDING**

Remaining live gate:
1. reload game and HK;
2. open Buildings and calculate candidates;
3. confirm Active shows the real active/max count rather than all known building records;
4. click Open eligible;
5. confirm the runner no longer converts a non-empty plan into “no candidates”;
6. complete at least one controlled building open, then recalculate and confirm that building disappears from candidates.

Do not advance Explore to E4 until this action/state/rerun gate and Explore E3 single-building gate are confirmed.

## Buildings open-limit + runner UI r1 — userscript 1.17.17 (2026-09-21)

User live feedback identified two usability/safety gaps:
- the global runner block visually did not follow the current Buildings UI canon;
- there was no explicit cap on how many eligible buildings a run could open.

Delivered in userscript `1.17.17`:
- core: `core-20260921-r19-buildings-limit-runner`;
- marker: `buildings-open-limit-20260921-r1`;
- marker: `buildings-runner-ui-20260921-r1`;
- new **Open limit** selector: `1 / 10 / 15 / 20 / All available`;
- default limit is **1** for safe manual/live validation;
- selected limit is persisted in Buildings settings;
- execution list is clipped by both free active slots and the selected limit;
- confirmation now states the exact run size versus total candidates;
- plan now shows **To open / К запуску** separately from total candidates;
- run button reflects the limit, e.g. `Открыть до 10`;
- Buildings runner has its own compact canonical styling;
- runner state shows progress like `Выполняется · 3/10`;
- runner action buttons are compact on desktop and responsive on mobile.

Safety:
- Buildings active-slot semantics r1 preserved;
- opening/favorite mutation path preserved;
- default run cannot accidentally open the full candidate set;
- Maps shared runtime + concurrency 5 preserved;
- Explore E3 r9 preserved;
- passive auth safety preserved.

Verification:
- predeploy run `35569077513`: PASS;
- deploy/public round-trip run `35569168241`: PASS;
- loader core-r19 verification run `35569276675`: PASS;
- Buildings live verification run `35569279946`: PASS;
- `buildings_open_limit=PASS`;
- `buildings_runner_canon=PASS`;
- public E2E run `35569283445`: PASS.

Current status:
**LIMIT_RUNNER_R1_LIVE_CANDIDATE_USER_ACTION_CHECK_PENDING**

Next live gate:
1. reload game/HK;
2. open Buildings;
3. confirm Open limit defaults to 1 and offers 1/10/15/20/All available;
4. calculate candidates and confirm `К запуску` matches the selected limit/free slots;
5. run with limit 1;
6. verify canonical runner appearance and one-building execution;
7. recalculate and confirm the opened building is no longer offered.

