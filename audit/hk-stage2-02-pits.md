# HK Stage 2.02 — Pits / Ямы

status: CORE_LIVE_CANDIDATE_PENDING_USER_UI_CHECK

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
