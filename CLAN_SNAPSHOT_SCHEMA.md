# Clan snapshot contract

This file defines the canonical payload used to mirror the **Clan** tab from
HamsterKingMobile into the Top King member cabinet.

The script is the source of truth. The website must not recalculate or infer
the clan tree when a canonical snapshot is available.

## Update rule

Whenever the script finishes its normal Clan refresh successfully:

1. Build one complete snapshot from the exact data already rendered by the Clan tab.
2. Send the complete snapshot to the server.
3. The server validates it.
4. The server atomically replaces the previous snapshot for that clan.
5. The cabinet dashboard returns the latest complete snapshot unchanged.

Never merge a partial refresh into the latest complete snapshot.

## Canonical JSON

```json
{
  "schema_version": 2,
  "clan_key": "TK",
  "captured_at": 1789780000,
  "participants_count": 40,
  "overall": [
    {
      "player_id": "123",
      "nickname": "[TK] Лилюшкин",
      "total": 38
    }
  ],
  "blocks": [
    {
      "id": "clan_block_1",
      "title": "Block title",
      "localization_key": "clanblock_...",
      "icon": "https://...",
      "branches": [
        {
          "id": "branch_1",
          "title": "Branch title",
          "localization_key": "clanbranch_...",
          "icon": "https://...",
          "total": 942,
          "participants_count": 40,
          "players": [
            {
              "player_id": "123",
              "nickname": "[TK] Лилюшкин",
              "value": 38
            }
          ]
        }
      ]
    }
  ]
}
```

## Required invariants

- `overall` contains the same participant rows shown by “Общий вклад участников”.
- `blocks` preserves the same block order as the script UI.
- `branches` preserves the same branch order inside each block.
- `players` preserves every participant/value pair known by the script for that branch.
- A zero value is data and must not be dropped.
- `player_id` is preferred as the stable identity; nickname is display text.
- `captured_at` is the time of the completed Clan refresh, not the website view time.
- The server stores the full payload without flattening it to per-player totals.

## Cabinet response

The existing cabinet dashboard may return the snapshot either as:

```json
{ "clan": { "snapshot": { "...": "canonical payload" } } }
```

or directly in `clan` during migration. The current cabinet frontend supports
both forms.
