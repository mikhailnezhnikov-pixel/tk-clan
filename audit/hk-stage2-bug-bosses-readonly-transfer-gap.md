# HK Stage 2 Bug — Bosses canonical transfer gap

## Status

**PARTIALLY_RESOLVED_CORE_R1**

## Scope

Stage 2.03 — Bosses / Боссы only.

## Source preflight

Pinned donor:
- file: `скрипт Kokkaras,.txt`
- donor version: `5.3.22-ui-icons-pit-dim`
- canonical SHA256 after CRLF -> LF: `28c3104020ecb7f54d0d51a72d067404d0176bc069d59fcca417d66817d1fcf1`
- source priority: donor -> real API/definitions -> current baseline -> roadmap/TZ -> chat memory

Current baseline:
- `baseline/topking/HamsterKingMobile.current.user.js`
- Bosses marker: `HK_STAGE2J_BOSSES_REV = 'bosses-readonly-20260920-r1'`

## Confirmed gap

Current baseline Bosses module only:
- reads `/player/me`;
- extracts `player_bosses`, `player_regional_bosses`, `boss_battle`;
- renders read-only state rows;
- shows Boss Pit level/power;
- exposes only Refresh.

Pinned donor contains a substantially larger canonical Bosses module including:
- Area Boss + Regional Boss views;
- live plan construction and pass-cost validation;
- FREE / PREM / ITEM payments;
- mass multipliers;
- resume active battle;
- Area `/bosses/battle`;
- Regional `/regional_boss/battle`;
- Regional paid pass `/player/regional_boss/pass`;
- automatic finishing/restoration;
- Restoration Paws decision flow and per-run remembered budget;
- battle result / winrate logging;
- state updates after mutations;
- Area Boss tournament target planning;
- reward-only continuation;
- Area Boss calculator / rewards view.

Key donor entry points observed:
- `bossBuildPlans(kind)`;
- `bossFinishAreaAttempt(...)`;
- `bossFinishRegionalAttempt(...)`;
- `bossRunArea(...)`;
- `bossRunRegional(...)`;
- `runBossBattles(configs)`;
- `renderBossBattleMenu()`;
- `renderBossHub()`.

## Why this is a Stage 2 regression

Stage 2 requires:
`UI -> live read -> calculation -> action -> state update -> rerun`.

Current Bosses implementation only satisfies UI/live-read and therefore cannot reach LIVE PASS.

## Required fix

Transfer the canonical donor Bosses mechanics into the current HK integration while:
- preserving current launcher/runtime/state infrastructure;
- changing Bosses only;
- not changing unrelated modules;
- using donor API/order/guards as source of truth;
- keeping mutations behind explicit user Start;
- preserving pause/stop/error handling;
- validating live plan/cost before spend;
- performing authoritative resulting-state refresh/rerun.

No speculative feature additions.


## Resolution progress — canonical core r1

Core action gap is now transferred and technically live:
- Area/Regional canonical runner: present;
- pass plans and FREE/PREM/ITEM: present;
- active resume: present;
- restoration decision: present;
- action -> authoritative state refresh: present;
- live/public SHA: `571d97f7aa2adf5d747f94275350abf0872f04a63bdaf795c9ec53aed2b393a9`;
- baseline sync: `bac973abc67096f5642fce84ab1df8ba1a16883e`.

Remaining donor gap is limited to the higher-level Area Boss tournament planning/calculator block:
- tournament target/reward planning;
- reward-only continuation;
- Area Boss Calculator / rewards view.

Bug remains open until those donor mechanics and final live paths are verified.
