# HK Stage 1 — Checkpoint

## Purpose

This file is the single resume point for Stage 1.

If a chat is interrupted, expires, or returns `Stream cache expired`, the next session must read this file first and continue from the recorded block.

## Execution mode

Stage 1 is executed in short, self-contained blocks.

Each block must:
1. run SOURCE PREFLIGHT;
2. read the pinned donor reference;
3. inspect only the scope of the current block;
4. write the result to its audit file;
5. update this checkpoint;
6. stop and report the checkpoint to the user.

Do not run the full Stage 1 in one long session.

## Current state

- stage: 1
- SOURCE PREFLIGHT: PASS
- pinned donor: Kokkaras HK Control Panel
- donor version: 5.3.22-ui-icons-pit-dim
- donor SHA256: 28c3104020ecb7f54d0d51a72d067404d0176bc069d59fcca417d66817d1fcf1
- prior migration audits: FOUND / READ
- current block: 1C
- current block status: READY_TO_START
- next action: audit donor -> current/live automation, mutation paths and hidden helpers
- overall Stage 1 status: IN_PROGRESS

## Resume command

User can write:

> Продолжай Этап 1 с последнего checkpoint.

Then:
1. read this file;
2. run SOURCE PREFLIGHT again;
3. continue only the block named in `current block`.


## Completed blocks

- 1A — functions: PASS
  - historical genuinely untransferred functions: 0
  - donor-only Neighborhoods and Rat Hunt retained as later-stage references
  - no gameplay code changed


- 1B — endpoints/constants: PASS
  - historical missing real endpoints: 0
  - historical missing constants: 0
  - /city/{id}/game_area confirmed present
  - Kokkaras service/storage constants classified as architecture-specific reference
  - no gameplay code changed
