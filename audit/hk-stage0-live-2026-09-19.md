# HK Stage 0 live audit — 2026-09-19

Source: live server export `/opt/hamsterking-license/HamsterKingMobile.user.js`.
Observed live version: **1.14.4**.

## Confirmed foundation
- Shared `hkStateStore` exists.
- Entity row merge keys include currencies, items, buildings, playerHamsters and player_hamster_generals.
- Full `/player/me` replaces full arrays; mutation responses merge rows.
- Timestamp guard prevents older responses from overwriting newer fields.
- Growth tabs auto-load `/player/me`; execution force-rereads state before mutations.
- `apiJson` retries 401/403 auth once, transient 408/425/429/5xx, and `player state is locked`.
- Shared `hkRunner` supports Pause / Continue / Stop with AbortController.
- Growth mutations update State Store and can trigger native game UI refresh bridge.

## Growth mechanics found in live 1.14.4
### Hamsters
- View: `POST /player/hamster/lvlUp/view {hamster_id}`
- Level: `POST /player/hamster/lvlUp {hamster_id[, fast_type]}`
- Rarity: `POST /player/hamster/upgrade {hamster_id}`
- Priority copy purchase: `POST /shop/buy`
- Copy lots are derived from `mf_shoplot_hamsters_collection_copy_dust_...`
- Premium/hard-currency copy purchases are explicitly excluded.
- Current budget implementation: `cur_cap` (Caps).
- UI also reads `cur_nut` (Nuts), but Nuts are not the current hamster budget limiter.
- Hamster actions explicitly reject Pit Token costs.

### Generals
- Stored under `player_hamster_generals`, keyed by `hamster_id`.
- Uses the same hamster level endpoints.
- Current budget implementation: `item_pit_token`.
- Supports x1 and server-provided nearest x10 mode.

## Stage 0 discrepancies against target architecture
1. **Unified Runner is not global yet.** `hkRunner.start` is used only by Today and Growth. Pit, Fair, Shop, Recipes, Bureau and other mutation loops still use local flags such as `pitRunning`, `fairRunning/fairStop`, `recipeRunning/recipeStop`.
2. **State Store is not the single source everywhere.** Many legacy modules still assign `playerDocument = await apiJson(...)` directly and retain module-local documents.
3. **No WebSocket implementation exists in the live userscript.** No `WebSocket` constructor/use was found. Real-time event invalidation is therefore not implemented at the common engine level.
4. **Post-mutation reread is inconsistent outside Growth.** Growth has targeted entity refresh/recovery; legacy modules vary between direct response assignment and explicit `/player/me` rereads.
5. **Growth currency naming needs source verification.** Live 1.14.4 uses Caps (`cur_cap`) for the hamster percentage budget while displaying Nuts separately. This must be checked against the KKras source/mechanic before changing it; it is not Pit Tokens.
6. **Global mutation serialization is incomplete.** The shared Runner blocks concurrent Runner tasks, but modules outside Runner can still mutate independently. This leaves a remaining path to `player state is locked`.

## Stage 1 entry condition
Stage 0 confirms the next required change is a global mutation execution layer: all state-changing modules must serialize through one Runner/queue, preserve module-specific Stop semantics, and feed every successful mutation into State Store before UI refresh.


## Stage 1 implementation contract
The global mutation runner must own every state-changing request, not only Today/Growth. Required invariants:
- one mutation task globally at a time;
- FIFO queue for independent modules;
- one AbortController per active task;
- Pause blocks before the next mutation but never interrupts an already accepted server mutation;
- Stop aborts pending network work, removes queued work for that task, and prevents subsequent mutations;
- transient lock/429/5xx retry remains centralized in apiJson;
- successful mutation response is merged into hkStateStore before module UI callbacks;
- optional authoritative reread runs after mutation groups;
- read-only requests are not globally serialized.

Migration order for Stage 1: Growth/Today compatibility wrapper → Pit → Fair → Shop → Recipes/Bureau → remaining mutation loops. Legacy module flags remain only as UI compatibility state until each module is migrated.
