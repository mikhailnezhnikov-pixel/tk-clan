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

The exact external donor script has **not yet been captured into this repository**.

Past work refers to another script/source that was used to copy behavior, and for alliance metrics the user explicitly referred to the external Patreon source as the reference for how totals are determined. However, there is currently no exact donor filename/URL/content committed here.

Until the exact donor is captured, do not substitute our current or historical HamsterKingMobile scripts for it.

## Intended files

Once the exact donor is available, store:

- `REFERENCE.json` — source name/version/SHA/origin;
- `donor.current.js` or the exact original filename;
- immutable snapshot with version/SHA;
- optional `NOTES.md` describing provenance only, not reinterpreting mechanics.
