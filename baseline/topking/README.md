# HK / Top King — CURRENT IMPLEMENTATION BASELINE

This directory stores our currently accepted HK implementation.

It is **NOT** the primary source of truth for copied mechanics or data behavior.

## Files

- `HamsterKingMobile.current.user.js` — exact byte-for-byte copy of our currently accepted live implementation.
- `HamsterKingMobile.<version>-<sha>.user.js` — immutable snapshot of that implementation.
- `BASELINE.json` — version, SHA256 and capture metadata.

## Role of this directory

Use this baseline to understand:

- what our script currently contains;
- where a feature is integrated;
- what must not be accidentally broken;
- what exact code is currently deployed.

Do **not** use this file to invent or redefine the behavior of a feature that is being copied from an external donor/reference script.

For copied mechanics, the donor/reference source has priority. See:

`reference/topking/`

## Development rule

For every task:

1. Read the donor/reference source first when the task concerns copied mechanics/data/API behavior.
2. Read this current implementation baseline second.
3. Compare donor behavior against our implementation.
4. Apply the smallest targeted change to our implementation.
5. Do not reconstruct donor mechanics from chat text, memory, screenshots, or assumptions.
6. Validate syntax and the affected runtime path.
7. Deploy and verify.
8. Refresh this implementation baseline only after the new live build is accepted.

## Source priority

When working on copied functionality:

1. Exact donor/reference script.
2. Real game API/definitions when needed to understand donor behavior.
3. Current implementation baseline in this directory.
4. Roadmap/task wording.
5. Chat memory/context.

When working only on our own integration/UI/bugs:

1. Current implementation baseline.
2. Real runtime/live behavior.
3. Roadmap/task wording.
4. Chat memory/context.
