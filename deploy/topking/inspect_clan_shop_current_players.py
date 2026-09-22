import sqlite3, json, os
db=sqlite3.connect("/var/lib/hamsterking-license/licenses.db"); db.row_factory=sqlite3.Row
print("ACTUAL_CURRENT")
for r in db.execute("""SELECT p.week_start,p.player_id,p.item_type,SUM(p.quantity) quantity,
                              m.note,m.first_name,m.username,m.active
                       FROM clan_shop_actual_players p
                       LEFT JOIN clan_members m ON m.linked_player_id=p.player_id
                       WHERE p.week_start=(SELECT MAX(week_start) FROM clan_shop_actual_players)
                       GROUP BY p.week_start,p.player_id,p.item_type,m.note,m.first_name,m.username,m.active
                       ORDER BY p.player_id,p.item_type"""):
    print(dict(r))
print("LINKED_ACTIVE")
for r in db.execute("""SELECT linked_player_id,note,first_name,username
                       FROM clan_members
                       WHERE active=1 AND linked_player_id IS NOT NULL AND TRIM(linked_player_id)<>'' 
                       ORDER BY note"""):
    print(dict(r))
