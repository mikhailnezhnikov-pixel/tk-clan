from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")
MARKER = "CLAN_SHOP_WEEKLY_DELTA_V9"

if MARKER in s:
    print("CLAN_SHOP_WEEKLY_DELTA_V9_ALREADY_PRESENT")
    raise SystemExit(0)

if "CLAN_SHOP_LINKED_PLAYER_ID_V8" not in s:
    raise SystemExit("Clan Shop identity V8 not found")

anchor = """    players_by_lot = {}
    for row in player_rows:
        key = (str(row["week_start"]), str(row["lot_id"]))
        players_by_lot.setdefault(key, []).append(row)

    aggregated = {}
"""
replacement = """    # CLAN_SHOP_WEEKLY_DELTA_V9
    # Game counters are cumulative. Weekly history must use the increase from
    # the previous stored week, not the raw cumulative value.
    def counter_delta(current: int, previous: int | None) -> int:
        current = max(0, int(current or 0))
        if previous is None:
            return current
        previous = max(0, int(previous or 0))
        return current - previous if current >= previous else current

    previous_shared = {}
    lot_history = {}
    for row in lots:
        lot_id = str(row["lot_id"])
        lot_history.setdefault(lot_id, []).append(row)
    for lot_id, rows in lot_history.items():
        rows.sort(key=lambda row: str(row["week_start"]))
        prev = None
        for row in rows:
            week = str(row["week_start"])
            previous_shared[(week, lot_id)] = prev
            prev = max(0, int(row["shared_purchased"] or 0))

    previous_player = {}
    player_history = {}
    for row in player_rows:
        lot_id = str(row["lot_id"])
        player_id = str(row["player_id"])
        player_history.setdefault((lot_id, player_id), []).append(row)
    for key, rows in player_history.items():
        rows.sort(key=lambda row: str(row["week_start"]))
        prev = None
        for row in rows:
            week = str(row["week_start"])
            previous_player[(week, key[0], key[1])] = prev
            prev = max(0, int(row["quantity"] or 0))

    players_by_lot = {}
    for row in player_rows:
        key = (str(row["week_start"]), str(row["lot_id"]))
        players_by_lot.setdefault(key, []).append(row)

    aggregated = {}
"""
if s.count(anchor) != 1:
    raise SystemExit(f"history aggregation anchor expected once, got {s.count(anchor)}")
s = s.replace(anchor, replacement, 1)

old_qty = """            quantity = max(0, int(row["quantity"] or 0))
            if quantity <= 0:
                continue
"""
new_qty = """            raw_quantity = max(0, int(row["quantity"] or 0))
            previous_quantity = previous_player.get((week, lot_id, str(row["player_id"])))
            # If this player has no prior baseline while the lot itself does,
            # do not assign a cumulative historic count to the current week.
            quantity = 0 if previous_quantity is None and previous_shared.get((week, lot_id)) is not None \
                else counter_delta(raw_quantity, previous_quantity)
            if quantity <= 0:
                continue
"""
if s.count(old_qty) != 1:
    raise SystemExit(f"player quantity block expected once, got {s.count(old_qty)}")
s = s.replace(old_qty, new_qty, 1)

old_shared = """        shared_total = max(0, int(lot["shared_purchased"] or 0))
        actual_total = max(shared_total, known_total)
"""
new_shared = """        raw_shared_total = max(0, int(lot["shared_purchased"] or 0))
        shared_total = counter_delta(raw_shared_total, previous_shared.get((week, lot_id)))
        actual_total = max(shared_total, known_total)
"""
if s.count(old_shared) != 1:
    raise SystemExit(f"shared total block expected once, got {s.count(old_shared)}")
s = s.replace(old_shared, new_shared, 1)

old_return = """    return {"ok": True, "source": "game_actual", "items": items}
"""
new_return = """    return {
        "ok": True,
        "source": "game_actual",
        "counter_mode": "weekly_delta",
        "items": items,
    }
"""
if s.count(old_return) != 1:
    raise SystemExit(f"history return expected once, got {s.count(old_return)}")
s = s.replace(old_return, new_return, 1)

path.write_text(s, encoding="utf-8")
print("CLAN_SHOP_WEEKLY_DELTA_V9_PATCH_OK")
