# HK Stage 2.02 — Pits / Ямы

status: BLOCKED_DONOR_SOURCE_NOT_FOUND

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
