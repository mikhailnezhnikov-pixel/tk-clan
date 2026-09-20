# HK Stage 2.01 — Today / Сегодня

status: TECHNICAL_CHECK_RUNNING

## Donor reference

Pinned Kokkaras:
- version: 5.3.22-ui-icons-pit-dim
- file id: file_0000000006d08243a84499c0fe6f08c7

Relevant donor flow:
- showDailyTasksMenu()
- live auth/player
- shop catalog
- client_config
- static items/currencies/localization
- selected actions preview
- runDailyTasks()
- ads / rumors / daily quests / purchases / rewards

## Required Stage 2 chain

UI → live read → calculation/plan → action → state update → rerun

## Current structural evidence

Current HK has:
- renderDailyTasks()
- refreshDailyTasks()
- selectedDailyActions()
- dailyPlanTotals()
- runDailySelected()
- runDailyAd()
- runDailyRumors()
- runDailyClanPurchases()

refreshDailyTasks() explicitly rereads:
- POST /player/me
- GET /shop/view
- rumor route
and rebuilds/render daily state.

runDailySelected():
- validates budget;
- requires confirmation;
- uses shared runner;
- supports pause/abort;
- dispatches action by kind;
- after execution rereads /player/me and /shop/view;
- rebuilds selection/snapshot and rerenders.

## Pending

- exact live/public code verification
- authenticated browser UI/read/action/state/rerun confirmation
