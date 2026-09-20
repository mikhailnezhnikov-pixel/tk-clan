# HK / Top King — CANONICAL BASELINE

This directory is the source of truth for further HK userscript work.

## Files

- `HamsterKingMobile.current.user.js` — exact byte-for-byte copy of the currently accepted live script.
- `HamsterKingMobile.<version>-<sha>.user.js` — immutable snapshot of that accepted baseline.
- `BASELINE.json` — version, SHA256 and capture metadata.

## Mandatory development rule

For every new chat/session/task that changes the HK userscript:

1. Read `baseline/topking/BASELINE.json`.
2. Read `baseline/topking/HamsterKingMobile.current.user.js`.
3. Treat that file as the implementation source of truth.
4. Do NOT reconstruct mechanics from chat descriptions, memories, roadmap text, screenshots or assumptions.
5. Do NOT rewrite already-working mechanics unless a concrete regression is demonstrated.
6. If historical behavior must be restored, compare the canonical baseline against the preserved old script/source before changing code.
7. Apply the smallest targeted patch to the canonical baseline.
8. Validate syntax and the exact affected runtime path.
9. Deploy and verify public delivery.
10. Only after the user confirms the new live build works may the canonical baseline be refreshed.

## Priority of sources

When sources disagree, use this order:

1. Current accepted canonical baseline in this directory.
2. Verified preserved historical working script/source.
3. Real live game API/definitions.
4. Roadmap/task text.
5. Chat memory/context.

Chat text is never sufficient by itself to redefine existing working mechanics.

## New-chat instruction

Use:

> Work from the canonical HK baseline in `baseline/topking/`. First read `BASELINE.json` and `HamsterKingMobile.current.user.js`. Do not recreate or reinterpret existing mechanics from text. Make only the requested change against this exact baseline.

