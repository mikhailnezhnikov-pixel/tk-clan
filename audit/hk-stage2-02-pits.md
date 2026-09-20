# HK Stage 2.02 — Pits / Ямы

status: UI_LIVE_READ_PASS_ACTION_PENDING

## Required Stage 2 chain

UI → live read → calculation/plan → action → state update → rerun

## Scope

- Normal Pit
- Boss Pit
- Gang Pit
- free/paid move logic
- token usage limits
- collect-only mode
- battle/start/finish/respawn paths
- reread after mutation
- pause/stop safety

## Next action

Run SOURCE PREFLIGHT against pinned Kokkaras donor and compare donor Pit behavior with current/live 1.17.4.

Do not change gameplay logic before concrete mismatch is identified.


## SOURCE PREFLIGHT result

status: **BLOCKED_DONOR_SOURCE_NOT_FOUND**

Expected pinned donor from `reference/topking/REFERENCE.json`:
- title: `Вставленный текст.txt`
- donor: Kokkaras HK Control Panel
- version: `5.3.22-ui-icons-pit-dim`
- pinned SHA256: `28c3104020ecb7f54d0d51a72d067404d0176bc069d59fcca417d66817d1fcf1`
- expected source: `https://kokkaras.com/hk_maps/panel.js`

File Library searches performed for:
- exact version;
- exact donor name;
- exact SHA256;
- source URL;
- `showPitsMenu` / `runPits` and related Pit anchors.

Result:
- the exact pinned donor was not returned;
- unrelated/current HK files were returned instead;
- no substitute donor was used.

Protocol decision:
- do not compare/modify Pits from memory or a different script;
- do not start implementation until the exact pinned donor source is available again.

Current/live Pits code was **not changed** in this block.


## Donor restored

Exact donor re-uploaded and verified:
- raw upload: CRLF, 1,860,858 bytes, SHA256 `8a5aece8b10dfbaf0b3dd2890de600a9505aa523783cbe0c97ea81331d7e0c7d`
- normalized CRLF → LF: 1,836,359 bytes
- normalized SHA256: `28c3104020ecb7f54d0d51a72d067404d0176bc069d59fcca417d66817d1fcf1`
- version: `5.3.22-ui-icons-pit-dim`

The previous donor-source block is resolved.

Stage 2.02 source preflight resumes from this exact pinned donor.


## Confirmed live regression

Bug ticket:
`audit/hk-stage2-bug-pits-canonical-transfer-gap.md`

Direct live verification:
- workflow run: `35490479912`
- live SHA256: `303f6813d6e001751b53b32d83c6098f307aeedcee6a3cf320887bc93a07a117`
- legacy `pitLoop` active: YES
- canonical `runPits(configs)`: ABSENT
- canonical `pitBuildMenuState`: ABSENT
- canonical `pitReadRunConfigs`: ABSENT
- direct API `executeDailyPit`: orphaned declaration, no active call site

Result:
**BUG_CONFIRMED_FIX_PENDING**

Next block:
port/wire Kokkaras canonical three-Pit behavior into current HK visual/runner architecture.


## Canonical core r1 deployed

Marker:
`HK_PITS_CANON_REV = 'pits-canon-core-20260920-r1'`

Workflow:
`Deploy TopKing Pits Canon Core R1`

Successful run:
`35491426778`

Technical result:
- patch payload SHA verification: PASS
- Python compile: PASS
- exact pre-deploy live SHA verification: PASS
- JS syntax after patch: PASS
- backup/deploy: PASS
- service active: PASS
- public round-trip: PASS
- live/public byte equality: PASS
- version remains: `1.17.4`
- live/public SHA256: `0d6de4888121d5e09d2cd5fa5140ec5941734dd30c23dc70fbbd95a951dcb825`

Core behavior now wired into the visible Pits tab:
- three independent Pit cards: normal / boss / gang;
- live free-pass counts;
- donor Exact / Rounded / Direct / Pit Pass planning;
- target level selector;
- per-Pit maximum Restoration Paws;
- per-Pit Auto-finish plus global Auto-finish all;
- continuation of an already active Pit;
- direct API start/pass/battle/respawn/finish;
- current HK mutation gate and runner pause/stop;
- authoritative player reread before/after mutations;
- cost/balance revalidation before paid mutations;
- legacy single-Pit DOM UI/button bindings removed from active page.

Not yet in this core block:
- sniper mode/payment;
- tournament reward target planning / daily base runs / reward strategy;
- interactive restoration-decision modal.

These stay for the next Pits block after the core UI/live-read is visually confirmed.

Current status:
**CORE_LIVE_CANDIDATE_PENDING_USER_UI_CHECK**


## UI alignment r2

Marker:
`HK_PITS_UI_REV = 'pits-ui-align-20260920-r2'`

Workflow:
`Deploy TopKing Pits UI Align R2`

Successful run:
`35492472689`

Result:
- card controls aligned into a bounded grid;
- Restoration Paws checkbox/input alignment corrected;
- Core r1 gameplay/API logic unchanged;
- live/public SHA256 after r2: `a3df20e0996ced42e4efa39baa5f25b9e41af979657854079c8e645e57b16708`.

## Pass-plan + Sniper r3 deployed

Pinned donor used:
- uploaded `скрипт Kokkaras,.txt`;
- version: `5.3.22-ui-icons-pit-dim`;
- canonical CRLF→LF SHA256: `28c3104020ecb7f54d0d51a72d067404d0176bc069d59fcca417d66817d1fcf1`.
- donor file is not committed to the repository by user choice; future chat must use the same exact upload/SHA if donor code is needed again.

Confirmed donor behavior transferred in this block:
- Pit is active only when its state has `is_finish === false`;
- finished Pit snapshots no longer lock the Pass plan merely because an old `mass_multiplier` remains;
- normal Pass plan remains donor-compatible: Exact / Rounded / Direct / Pit Pass;
- Sniper mode is independent per Pit;
- standalone Sniper uses multiplier ×1;
- Sniper payment is selectable as FREE / PREM / ITEM when that payment is live-available;
- Sniper recommended target = `floor(currentLevel / 5) * 5 + 15`;
- Sniper target choices start at the recommended target and higher available target levels;
- active ×1 Pit can preserve Sniper flag, while active non-×1 Pit cannot enable Sniper;
- saved normal Pass plan/target remain separate from Sniper target/payment.

Marker:
`HK_PITS_SNIPER_REV = 'pits-passplan-sniper-20260920-r3'`

Workflow:
`Deploy TopKing Pits PassPlan Sniper R3`

Successful run:
`35493218772`

Technical result:
- exact pre-deploy r2 SHA verification: PASS;
- Python patch compile: PASS;
- donor-transfer anchors: PASS;
- JS syntax: PASS;
- backup/deploy: PASS;
- service active: PASS;
- public round-trip: PASS;
- live/public byte equality: PASS;
- live/public SHA256: `42d39c573c5bb8bf445f8166a72a6b0a16fde14295365a0ebea0ee43e71b6f64`.

Baseline sync:
- workflow: `Sync TopKing Current From Live`;
- run: `35493258548`;
- result: SUCCESS;
- `baseline/topking/HamsterKingMobile.current.user.js` contains the r3 marker.

Current status:
**PASSPLAN_SNIPER_LIVE_CANDIDATE_PENDING_USER_UI_CHECK**

Required user check:
1. reload the game;
2. open HK → Ямы;
3. do NOT start the Pits yet;
4. verify that completed/non-active Pits have a selectable Pass plan;
5. verify Sniper mode appears on each Pit;
6. enable Sniper on one non-active Pit and verify:
   - Pass plan becomes ×1;
   - Pass payment selector appears;
   - target list starts at the recommended Sniper level and allows higher targets.

Do not advance to tournament reward planning, restoration decision logic, or Bosses until this UI/live-read check is confirmed.


## Toolbar clean r4 + user UI confirmation

User confirmation:
- Pass plan: visually OK;
- Sniper mode/payment/target UI: visually OK;
- remaining requested UI change: remove redundant `Обновить данные` button.

r4 change:
- removed only the manual `Обновить данные` / `Refresh live data` button from Pits;
- removed its click handler;
- automatic live refresh on module open remains unchanged;
- no Pits calculation/action logic changed.

Marker:
`HK_PITS_TOOLBAR_REV = 'pits-toolbar-clean-20260920-r4'`

Workflow:
`Deploy TopKing Pits Toolbar Clean R4`

Successful run:
`35493415188`

Technical result:
- exact pre-deploy r3 SHA verification: PASS;
- Python patch compile: PASS;
- JS syntax: PASS;
- backup/deploy: PASS;
- service active: PASS;
- public round-trip: PASS;
- live/public byte equality: PASS;
- live/public SHA256: `003c3a2a47bc2dc97e1e073b14744a57463d936e1fdc20b02e6041b124842223`.

Baseline sync:
- run: `35493446456`;
- result: SUCCESS.

Current Stage 2.02 status:
**UI_LIVE_READ_PASS_ACTION_PENDING**

Passed:
- UI;
- live read;
- normal Pass plan selection;
- Sniper mode/payment/target configuration;
- r4 toolbar cleanup.

Still required before Pits LIVE PASS:
- action execution;
- authoritative state update after action;
- rerun from the resulting state;
- remaining planned donor Pits functionality if still in Stage 2.02 scope.

Do not advance to Bosses yet.
