"""Enable the explicitly approved schedule after private content installation."""
import json,os,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,'/opt/hamsterking-license')
from contest_runtime import Contest,START
owner=sys.argv[1]
pid=subprocess.check_output(['systemctl','show','hamsterking-license.service','-p','MainPID','--value'],text=True).strip()
process=Path('/proc/'+pid)
env=dict(x.split(b'=',1) for x in (process/'environ').read_bytes().split(b'\0') if b'=' in x)
main=env.get(b'HK_LICENSE_DB',b'/var/lib/hamsterking-license/licenses.db').decode()
c=Contest(Path(main).parent/'contest.db','schedule-only',lambda _:None,lambda _:None)
with c.db() as db:
    cfg=c.config(db)
    assert cfg['owner_id']==owner,'Owner mismatch'
    assert c.ready(cfg) and all(len(s.get('points',[]))==3 for s in cfg['stages']),'Incomplete content'
    if time.time()>=START:
        assert cfg['armed'] and cfg['start_at']==START,'Refuse a new late launch'
        print('EXISTING_SCHEDULE_PRESERVED=PASS')
        sys.exit(0)
    assert db.execute("SELECT COUNT(*) FROM solves WHERE mode='live'").fetchone()[0]==0,'Live solves exist'
    content=json.loads(Path('/opt/hamsterking-license/contest_content.json').read_text(encoding='utf-8'))
    # Apply only the approved wording, retaining answers, progress and schedule.
    cfg['stages'][2]['points'][0]['prompt']=content[2]['points'][0]['prompt']
    cfg.update(start_at=START,end_at=START+7200,armed=True,paused=False)
    assert [s['offset'] for s in cfg['stages']]==[0,1800,3600]
    db.execute('UPDATE settings SET value=? WHERE id=1',(json.dumps(cfg),))
print('APPROVED_SCHEDULE_ARMED=PASS; 16:30 Moscow; no private content logged')
