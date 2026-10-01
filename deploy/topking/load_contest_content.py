"""Owner-only content installation, never enables public competition."""
import json
import sqlite3
import sys
from pathlib import Path
from contest_runtime import Contest

def load(contest):
    stages=json.loads((Path(__file__).parent/'contest_content.json').read_text(encoding='utf-8'))
    with contest.write_lock,contest.db() as db:
        db.execute('BEGIN IMMEDIATE')
        cfg=contest.config(db)
        if cfg['armed']:
            raise RuntimeError('Refusing to replace armed contest content')
        for i,s in enumerate(stages):
            s['digest']=contest.digest(i,s.pop('answer'))
            for j,q in enumerate(s['points']):
                q['digest']=contest.digest(f'{i}.{j}',q.pop('answer'))
        cfg.update(stages=stages,armed=False)
        db.execute('UPDATE settings SET value=? WHERE id=1',(json.dumps(cfg),))

if __name__=='__main__':
    # Actual provisioning invokes load() with the existing runtime and signing secret.
    raise SystemExit('Import load() from the authorized provisioning script')
