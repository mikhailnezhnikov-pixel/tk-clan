from pathlib import Path
import sys

base=Path("deploy/topking/patch_map_preview_battle_intro_1_18_85.py")
src=base.read_text(encoding="utf-8")
old='''rep("    let battleAutoRunning=false;\\n",
    "    let battleAutoRunning=false;\\n    let battleIntroGateUntil=0;\\n",
    "battle state")'''
new='''rep("    let battleAutoRunning = false;\\n",
    "    let battleAutoRunning = false;\\n    let battleIntroGateUntil = 0;\\n",
    "battle state")'''
if old not in src:
    raise SystemExit("wrapper: battle state patch block missing")
src=src.replace(old,new,1)

target=sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js"
old_argv=sys.argv[:]
try:
    sys.argv=[str(base),target]
    scope={"__name__":"__main__","__file__":str(base)}
    exec(compile(src,str(base),"exec"),scope,scope)
finally:
    sys.argv=old_argv
