# HK Stage 2.05 — Resources / Ресурсы

## Status

**LIVE PASS**

## Canonical implementation

Current runtime:
- `HK_STAGE2D_RUNNER_REV = 'stage2d-resource-business-20260919-r1'`
- resource hotfix marker: `bureau-resources-live-20260920-r1`

Resource kinds:
- Nut / Supply Station;
- Tools / Industrial Hub;
- Pit Tokens / Sports Pavilion.

Current live path:
- authoritative `/player/me`;
- automatic owned-district scan via `/game_area/{id}/buildings`;
- exact building verification via `/player/building`;
- live task/cost calculation;
- protected-resource guard;
- unified budget guard;
- explicit confirmation before mutation;
- Runner pause/stop support;
- `/player/event` mutation with mutation retry disabled;
- large exchanges split safely only after server rejects the combined request;
- post-run `loadResources(false)`;
- authoritative `/player/me` reread after completion.

## Existing build/live evidence

1.17.1 Bureau + Resources repair was built and deployed separately.

Build verification:
- revision: `bureau-resources-live-20260920-r1`;
- build status: PASS;
- syntax: PASS;
- idempotent: yes;
- verified build SHA256: `6767915e46703b4c08426886d1be24ebfeb7b37755a62953bb90798df7f6f49c`.

Evidence:
- `audit/hk-1171-build-status.txt`;
- deploy history: `Deploy TopKing 1.17.1 Bureau and Resources fixes`;
- post-deploy verification history: `Verify live TopKing 1.17.1 after Bureau Resources deploy`.

## Stage 2 matrix

- UI: PASS
- live read: PASS
- cost/availability calculation: PASS
- budget guard: PASS
- explicit confirmation: PASS
- action: PASS
- pause/stop: PASS
- state update: PASS
- authoritative reread: PASS
- rerun path: PASS

No confirmed Resources regression was found in the current synchronized baseline.
No new Resources patch is required.

Final status:
**LIVE PASS**
