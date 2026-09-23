from pathlib import Path
import re, json

root=Path(".")
refs=set()
text_files=0
for p in root.rglob("*"):
    if not p.is_file():
        continue
    if ".git" in p.parts:
        continue
    try:
        if p.stat().st_size > 2000000:
            continue
        s=p.read_text(encoding="utf-8")
    except Exception:
        continue
    text_files+=1
    for m in re.finditer(r"deploy/topking/[A-Za-z0-9_./-]+", s):
        refs.add(m.group(0).rstrip(".,;:'\")] }"))

actual=[]
for p in Path("deploy/topking").rglob("*"):
    if p.is_file():
        actual.append(p.as_posix())

def candidate(path):
    name=Path(path).name
    return (
        "trigger" in name.lower()
        or name.startswith("patch_")
        or name.startswith("install_")
        or name.startswith("audit_")
        or name.endswith(".candidate.user.js")
        or ".patch." in name
        or name.endswith(".patch")
    )

orphans=[p for p in actual if candidate(p) and p not in refs]
referenced=[p for p in actual if p in refs]

print("REPO_CLEANUP_REFERENCE_AUDIT=1")
print("text_files_scanned",text_files)
print("deploy_topking_files",len(actual))
print("referenced_deploy_files",len(referenced))
print("orphan_candidates",len(orphans))
print("ORPHANS_JSON",json.dumps(sorted(orphans),ensure_ascii=False))
