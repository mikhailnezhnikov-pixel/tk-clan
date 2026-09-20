#!/usr/bin/env python3
import glob, json, sys
from collections import Counter, defaultdict

classification=json.load(open(sys.argv[1],encoding="utf-8"))
map_dir=sys.argv[2]
out_json=sys.argv[3]
out_summary=sys.argv[4]

files=glob.glob(map_dir.rstrip("/")+"/w6-*.json")
results=[json.load(open(f,encoding="utf-8")) for f in files]
bykey={r["map_key"]:r for r in results}

unique_keys={m["map_key"] for m in classification["maps"] if len(m["candidates"])==1}
if set(bykey)!=unique_keys:
    raise SystemExit(f"expected {len(unique_keys)} map results, got {len(bykey)}; missing={sorted(unique_keys-set(bykey))}")

metrics=Counter()
targets=defaultdict(list)
for m in classification["maps"]:
    c=m["candidates"]
    if len(c)==1:
        metrics["city_grid_yx_matches"]+=1
        targets[c[0]].append(m["map_key"])
    elif len(c)==0:
        metrics["unresolved_maps"]+=1
    else:
        metrics["ambiguous_maps"]+=1

metrics["exact_area_id_matches"]=sum(
    1 for x in classification.get("existing_links",[])
    if x.get("match_method")=="exact_area_id"
)
duplicate_targets={area:keys for area,keys in targets.items() if len(keys)>1}

for r in results:
    metrics["source_positive_points"]+=r["point_count"]
    metrics["point_unique_matches"]+=len(r["points"])
    metrics["point_unmatched"]+=len(r["unmatched"])
    metrics["point_ambiguous"]+=len(r["ambiguous"])
    metrics["osm_query_failures"]+=len(r.get("osm_query_failures") or [])
    for p in r["points"]:
        if not p["existing"]:
            metrics["building_rows_to_add"]+=1
            continue
        metrics["building_rows_already_known"]+=1
        cur=p.get("canonical_room_count")
        if cur is None:
            metrics["existing_null_fill_candidates"]+=1
        elif int(cur)==int(p["room_count"]):
            metrics["room_count_same"]+=1
        else:
            metrics["room_count_conflicts_total"]+=1
            metrics["room_count_conflicts_"+str(p.get("canonical_source"))]+=1

report={
    "stage":"W6",
    "dry_run":True,
    "dry_run_complete":metrics["osm_query_failures"]==0,
    "total_maps":classification["total_maps"],
    "existing_links_before":len(classification.get("existing_links",[])),
    "exact_area_id_matches":metrics["exact_area_id_matches"],
    "city_grid_yx_matches":metrics["city_grid_yx_matches"],
    "unresolved_maps":metrics["unresolved_maps"],
    "ambiguous_maps":metrics["ambiguous_maps"],
    "duplicate_target_groups":len(duplicate_targets),
    "duplicate_target_maps":sum(len(v) for v in duplicate_targets.values()),
    "duplicate_targets":duplicate_targets,
    "source_positive_points":metrics["source_positive_points"],
    "point_unique_matches":metrics["point_unique_matches"],
    "point_unmatched":metrics["point_unmatched"],
    "point_ambiguous":metrics["point_ambiguous"],
    "osm_query_failures":metrics["osm_query_failures"],
    "building_rows_to_add":metrics["building_rows_to_add"],
    "building_rows_already_known":metrics["building_rows_already_known"],
    "existing_null_fill_candidates":metrics["existing_null_fill_candidates"],
    "room_count_same":metrics["room_count_same"],
    "room_count_conflicts_total":metrics["room_count_conflicts_total"],
    "room_count_conflicts_by_source":{
        "game_live":metrics["room_count_conflicts_game_live"],
        "hk_maps_import":metrics["room_count_conflicts_hk_maps_import"],
        "legacy":metrics["room_count_conflicts_legacy"],
    },
    "classification_maps":classification["maps"],
    "migration_manifest":sorted(results,key=lambda x:x["map_key"]),
}
assert report["total_maps"]==235
assert report["city_grid_yx_matches"]==26
assert report["unresolved_maps"]==209
assert report["ambiguous_maps"]==0

open(out_json,"w",encoding="utf-8").write(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True))
summary={k:v for k,v in report.items() if k not in ("classification_maps","migration_manifest","duplicate_targets")}
open(out_summary,"w",encoding="utf-8").write("\n".join(f"{k}={v}" for k,v in summary.items())+"\n")
print(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True))
