# Top King / HK — DONOR / REFERENCE SOURCE

## Purpose

This directory is reserved for the **external script/source from which HK mechanics, data extraction, API behavior and feature logic are copied**.

This is deliberately separate from:

`baseline/topking/`

because that directory contains **our implementation**, not the donor.

## Mandatory rule

When a task says to transfer, copy, restore, align, reproduce or verify an existing mechanic:

1. Read the exact donor/reference script in this directory first.
2. Determine its actual behavior from code.
3. Identify the exact API calls, fields, ordering, guards and calculations it uses.
4. Then open our current implementation in `baseline/topking/HamsterKingMobile.current.user.js`.
5. Port the donor behavior with the smallest possible change.
6. Never recreate the donor mechanic from chat description or memory.

## Important

Do not place one of our old HamsterKingMobile versions here and call it the donor unless it is confirmed to be the external source.

Historical versions of our own script are implementation history, not automatically the external reference.

## Current status

The exact donor is now **pinned by metadata** in `reference/topking/REFERENCE.json`.

Pinned source:
- name: Kokkaras HK Control Panel;
- File Library title: `Вставленный текст.txt`;
- pinned SHA256: `28c3104020ecb7f54d0d51a72d067404d0176bc069d59fcca417d66817d1fcf1`;
- donor version: `5.3.22-ui-icons-pit-dim`;
- source URL embedded in donor: `https://kokkaras.com/hk_maps/panel.js`.

Important: the public URL is mutable and changed after the user's capture. **Never replace the pinned uploaded revision with whatever the live URL currently returns.**

## Mandatory stage preflight

When the user says `начни этап N` or `продолжи этап N`:

1. Read `reference/topking/REFERENCE.json`.
2. Locate the pinned donor in ChatGPT File Library using the exact title/file id and identity anchors.
3. Read the donor code relevant to the requested stage.
4. Only then read `baseline/topking/BASELINE.json` and `baseline/topking/HamsterKingMobile.current.user.js`.
5. Read only the requested stage in `docs/HK_MASTER_ROADMAP.md`.
6. Execute only that stage.

If the exact donor cannot be located, report `DONOR SOURCE NOT FOUND` and do not reconstruct behavior from memory, screenshots, roadmap prose or old HK builds.
