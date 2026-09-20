# HK Stage 2.01 — Today / Сегодня

status: LIVE_CANDIDATE_R2_PENDING_USER_UI_CHECK

## Donor reference

Pinned Kokkaras:
- version: `5.3.22-ui-icons-pit-dim`
- sha256: `28c3104020ecb7f54d0d51a72d067404d0176bc069d59fcca417d66817d1fcf1`

## User-confirmed regression

Before this patch, current Today did not follow the donor canon:
- Rumor route/coordinates were shown as a separate UI section;
- an unavailable Ads card was shown;
- Pits were mixed into Today although Pits have their own module;
- shop actions were grouped by the previous HK tabs/order rather than the donor order;
- donor Daily Quest reward claims and reward-claim phase were missing from Today.

User requirement:
- preserve current HK visual language;
- remove rumor route display;
- action set/order must follow pinned donor canon.

## Applied live change

Marker:
`HK_TODAY_CANON_REV = 'today-kokkaras-order-20260920-r1'`

Canonical visual/action order now:
1. **Действия**
   - Ads only when actually available;
   - Rumors when route data exists;
   - Daily quests (Ω).
2. **Магазин клана**
3. **Инвестиционные предложения**
4. **Обычные предложения события**
5. **Получение наград**
   - leaderboard rewards for canonical Pit/Boss/Rat families;
   - Area Boss Battle Pass rewards.

Removed from Today UI:
- rumor route / city-coordinate list;
- Pits status/actions;
- unavailable Ads placeholder/card;
- old store-tab grouping.

The visual components/classes remain the existing HK design.

## Canonical execution additions

Added current-architecture equivalents of donor behavior:
- completed daily quest reward claim via `/quest/claim`;
- leaderboard reward discovery/claim via `/leaderboards/view`, `/leaderboard`, `/leaderboard/reward`;
- Area Boss Battle Pass discovery/claim via `/client_config`, `/battlepass`, `/battlepass/claim`.

The shared HK mutation gate, runner, budget checks and reread architecture are preserved.

## Technical verification

Workflow:
`Deploy TopKing Today Canon R1`

Run:
`35489305183`

Result:
- patch: PASS
- syntax: PASS
- deploy: PASS
- service restart/active: PASS
- public round-trip: PASS
- live/public byte equality: PASS
- version remains: `1.17.4`
- live SHA256: `73a8da55150892cabbf2f5bf9f5d2a22fcaa8ad228ff1bee3d793b3429f3c21b`

## Pending user UI verification

Need to confirm after page reload:
- no rumor route/coordinate section;
- no Pits block inside Today;
- no Ads row when account has no ad;
- the five canonical groups appear in order;
- existing HK visual style is preserved;
- module opens/refreshes without error.

Do not advance to Pits until this is confirmed or a concrete Today bug is recorded.


## r2 correction — exact donor event filter and claim wording

User reported that Event Regular Deals contained non-event/exchange-like lots.

Root cause:
- r1 selected every normalized row with `section === 'regular'`;
- Kokkaras does not do that.

Pinned donor filter verified:
- active event shop tab from `client_config.event.tabs`;
- exact `lot_view.tab === activeTab`;
- `lot_view.type !== hidden`;
- no ad / no external cost;
- `lot_view.group` contains `event_repeatable_daily_offers`;
- no `cur_prem` or `cur_hard` cost;
- PLAYER limit with `reset_type === DAILY` and positive total limit;
- priority descending.

Applied marker:
`HK_TODAY_CANON_FILTER_REV = 'today-kokkaras-filter-20260920-r2'`

Reward actions renamed to explicit operations:
- **Собрать награды рейтинга: Ямы / Боссы / Крысы**
- **Собрать награды Battle Pass боссов**

They remain selected actions executed by the common **Выполнить выбранное** button, matching donor behavior.

Technical verification:
- workflow run: `35489608943`
- syntax: PASS
- deploy/service: PASS
- public round-trip: PASS
- live/public SHA256: `3bcf43a3fbc805d81d4e64cd41d13ca0ee1fccd85fded13f877a66c05bbfabae`
