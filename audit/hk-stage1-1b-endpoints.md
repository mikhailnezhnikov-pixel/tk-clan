# HK Stage 1B — Endpoints and constants audit

status: PASS

## Scope

Audit:
- historical migration endpoints/constants;
- pinned Kokkaras donor endpoint/config reference;
- current implementation endpoint/constants;
- only transfer completeness, no new development.

## SOURCE PREFLIGHT

Pinned donor confirmed:
- Kokkaras HK Control Panel
- version: `5.3.22-ui-icons-pit-dim`
- sha256: `28c3104020ecb7f54d0d51a72d067404d0176bc069d59fcca417d66817d1fcf1`

Important donor base/config values:
- `baseUrl = https://kokkaras.com/hk_maps/`
- `apiUrl = https://hk-game-api.hwgame.cloud`
- `gatewayUrl = https://kokkaras.com/hk_maps/panel_secure.php`
- `realtimeUrl = wss://ws.kokkaras.com/socket`
- `staticApiUrl = https://cdn-prod-static-api.hwgame.cloud`
- `assetUrl = https://cdn-prod-front-dist.hwgame.cloud/assets/images/`
- `artAssetUrl = https://cdn-prod-art.hwgame.cloud/`
- donor also owns its own localStorage namespace and Athens reset/timezone settings.

These donor-service URLs and donor storage keys are reference implementation details, not values that must be copied verbatim into our deployment.

## Historical migration result

Source: `audit/hk-migration-completeness.json`.

Historical parser result:
- missing constants: **0**
- parser-reported missing endpoints: **1**
  - `/city/{…}/game_area`

The endpoint report was already classified as a parser false-positive in `audit/hk-migration-final-baseline.txt`.

Current implementation contains the concrete live call:

`apiJson('/city/' + encodeURIComponent(cityId) + '/game_area', 'GET')`

Therefore:

**historically missing real endpoints = 0**

## Current endpoint/base evidence

Current HK uses:

| Purpose | Current value/path | Status |
|---|---|---|
| game API fallback | `https://hk-game-api.hwgame.cloud` | PRESENT |
| static definitions | `https://cdn-prod-static-api.hwgame.cloud` | PRESENT |
| art/items | `https://cdn-prod-art.hwgame.cloud/items` and art CDN paths | PRESENT |
| player state | `/player/me` | PRESENT |
| shop purchase | `/shop/buy` | PRESENT |
| shop read | `/shop/view` | PRESENT |
| fair reroll | `/fair/reroll` | PRESENT |
| city districts | `/city/{id}/game_area` | PRESENT |
| district buildings | `/game_area/{id}/buildings` | PRESENT |
| clan wars | `/clan/active_battles`, `/clan/active_defense_wars` | PRESENT |
| alliance | `/alliance/list`, `/alliance/members?alliance_id=...` | PRESENT |
| clan members/info | `/clan/info`, `/clan/members?clan_id=...` | PRESENT |
| pits | normal/boss/gang view/start/battle/finish/pass/respawn paths | PRESENT |
| building mutation/read | `/player/building`, `/player/building?building_id=...` | PRESENT |
| business craft | `/player/business/recipe/craft` | PRESENT |
| hamster actions | `/player/hamster/lvlUp`, `/player/hamster/upgrade` | PRESENT |
| rumors | current server/game rumor paths including `/rumors/search` | PRESENT |

Current game endpoint extraction found **48 explicit game-path strings** in the baseline, plus dynamic routes.

## Current deployment/service constants

Current HK intentionally differs from Kokkaras for our own service layer:

- `LICENSE_URL = https://hk-license.89.125.1.71.sslip.io/api/v1/check`
- `RECIPE_API_BASE = .../api/v1/recipes`
- `MAP_API_BASE = .../api/v1/maps`
- `PIT_API_BASE = .../api/v1/pits`
- `SETTINGS_API_BASE = .../api/v1/settings`
- `CLAN_SKILLS_API_BASE = .../api/v1/clan-skills`
- `PUBLIC_SNAPSHOT_API = .../api/v1/public-snapshot`
- `RUMOR_API_BASE = .../api/v1/rumors`
- `STORE = hk_mobile_v1`

Classification: **ARCHITECTURE DIFFERENCE / NOT A MIGRATION DEFECT**.

Kokkaras uses its own PHP gateway, websocket, meta/buildings files and many per-feature localStorage keys. Our HK uses its own backend and consolidated storage/state design. Stage 1 checks function/behavior coverage, not server identity or storage-key name equality.

## Important current constants verified

Examples present in current:
- `GAME_API_FALLBACK`
- `GROWTH_STATIC_API`
- `GROWTH_HAMSTER_BUDGET_ID = cur_cap`
- `GROWTH_GENERAL_BUDGET_ID = item_pit_token`
- `PIT_MAX_LEVEL = 200`
- `MODULE_LIVE_TTL_MS = 12000`
- mutation/state/runtime revision constants
- protected resource/cost IDs

Historical constants audit reported no missing constants, and no contrary evidence was found in current.

## r9 note

The current live r9 candidate changes startup error-trap scoping only. It does not alter game endpoints, service base URLs, storage schema or gameplay constants, so it does not change the Stage 1B result.

## Stage 1B conclusion

- historical missing real endpoints: **0**
- historical missing constants: **0**
- `/city/{id}/game_area`: **confirmed present**
- Kokkaras-only gateway/realtime/storage/timezone constants: **reference-only / architecture-specific**
- new gameplay code added in this block: **0**

**Stage 1B: PASS**

Next block: **1C — automation / mutation / hidden helpers audit**.
