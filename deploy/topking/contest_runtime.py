"""Isolated TK Clan competition; no mutations of cabinet membership or licenses."""
import base64
import hashlib
import hmac
import json
import re
import sqlite3
import time
import threading
import unicodedata
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit

PREFIX = '/api/v1/cabinet/contest/'
START = 1790861400  # 2026-10-01 16:30 Europe/Moscow / 22:30 Asia/Yakutsk


class ContestError(Exception):
    def __init__(self, code, status=400):
        self.code, self.status = code, status


class Contest:
    def __init__(self, path, secret, verify_login, cabinet_identity, clock=time.time):
        self.path, self.secret = str(path), secret.encode()
        self.write_lock=threading.RLock()
        self.verify_login, self.cabinet_identity, self.clock = verify_login, cabinet_identity, clock
        with self.db() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.executescript('''
                CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY CHECK(id=1), value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS entrants (
                    mode TEXT NOT NULL, tid TEXT NOT NULL, player_id TEXT NOT NULL, nickname TEXT NOT NULL,
                    PRIMARY KEY(mode,tid), UNIQUE(mode,player_id));
                CREATE TABLE IF NOT EXISTS solves (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, mode TEXT NOT NULL, tid TEXT NOT NULL,
                    stage INTEGER NOT NULL, submitted_ns INTEGER NOT NULL, UNIQUE(mode,tid,stage));
                CREATE INDEX IF NOT EXISTS solve_ranking ON solves(mode,stage,submitted_ns,seq);
                CREATE TABLE IF NOT EXISTS checkpoints (
                    mode TEXT NOT NULL, tid TEXT NOT NULL, stage INTEGER NOT NULL,
                    point INTEGER NOT NULL, submitted_ns INTEGER NOT NULL,
                    PRIMARY KEY(mode,tid,stage,point));
                CREATE TABLE IF NOT EXISTS point_attempts (
                    mode TEXT NOT NULL, tid TEXT NOT NULL, stage INTEGER NOT NULL, point INTEGER NOT NULL,
                    last_at REAL NOT NULL, PRIMARY KEY(mode,tid,stage,point));
                CREATE TABLE IF NOT EXISTS attempts (
                    mode TEXT NOT NULL, tid TEXT NOT NULL, stage INTEGER NOT NULL,
                    count INTEGER NOT NULL, last_at REAL NOT NULL, PRIMARY KEY(mode,tid,stage));
            ''')
            if 'created_at' not in {r[1] for r in db.execute('PRAGMA table_info(entrants)')}:
                db.execute('ALTER TABLE entrants ADD COLUMN created_at REAL NOT NULL DEFAULT 0')
            cfg = dict(owner_id='', armed=False, paused=False, start_at=START,
                       end_at=START+7200, audience='all', cooldown=30,
                       stages=[dict(title='Этап '+str(i+1), prompt='', offset=i*1800, digest='') for i in range(3)])
            db.execute('INSERT OR IGNORE INTO settings VALUES(1,?)', (json.dumps(cfg),))

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA busy_timeout=10000')
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def config(self, db):
        return json.loads(db.execute('SELECT value FROM settings WHERE id=1').fetchone()[0])

    def owner(self, identity, cfg):
        return bool(identity and cfg['owner_id'] and str(identity['id']) == cfg['owner_id'])

    def token(self, identity):
        doc = dict(scope='tk-contest-v1', id=str(identity['id']), exp=int(self.clock())+43200,
                   name=str(identity.get('first_name',''))[:100])
        payload = base64.urlsafe_b64encode(json.dumps(doc).encode()).decode().rstrip('=')
        signature = hmac.new(self.secret, ('contest-session:'+payload).encode(), hashlib.sha256).hexdigest()
        return 'ct1.'+payload+'.'+signature

    def identity(self, token):
        if not token or token.startswith('id:'):
            return None
        if not token.startswith('ct1.'):
            # Read-only adapter checks the existing signed subject and active membership.
            return self.cabinet_identity(token)
        try:
            _, payload, signature = token.split('.')
            wanted = hmac.new(self.secret, ('contest-session:'+payload).encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(wanted, signature):
                return None
            doc = json.loads(base64.urlsafe_b64decode(payload+'='*(-len(payload)%4)))
            if doc.get('scope')!='tk-contest-v1' or doc['exp']<=self.clock():
                return None
            if not re.fullmatch(r'[1-9][0-9]{4,19}', str(doc['id'])):
                return None
            return doc
        except (ValueError, KeyError, TypeError, json.JSONDecodeError):
            return None

    def normalize(self, answer):
        value=' '.join(unicodedata.normalize('NFKC',str(answer)).casefold().replace('ё','е').split())
        return re.sub(r'[\s;]+','',value)

    def digest(self, stage, answer):
        return hmac.new(self.secret, ('contest-answer:'+str(stage)+':'+self.normalize(answer)).encode(),hashlib.sha256).hexdigest()

    def ready(self, cfg):
        return len(cfg['stages'])==3 and all(x['prompt'].strip() and x['digest'] for x in cfg['stages'])

    def phase(self, cfg):
        now=self.clock()
        if cfg['paused']:
            return 'paused'
        if not cfg['armed'] or not self.ready(cfg):
            return 'draft'
        if now<cfg['start_at']:
            return 'scheduled'
        return 'open' if now<cfg['end_at'] else 'finished'

    def ranking(self, db, mode):
        rows=db.execute('''SELECT e.tid,e.nickname,e.player_id,COUNT(s.stage) AS completed,
                   MAX(s.submitted_ns) AS last_ns,MAX(s.seq) AS last_seq
                   FROM entrants e JOIN solves s ON s.mode=e.mode AND s.tid=e.tid
                   WHERE e.mode=? GROUP BY e.tid,e.nickname,e.player_id
                   ORDER BY completed DESC,last_ns ASC,last_seq ASC''',(mode,)).fetchall()
        return [dict(place=i+1,nickname=r['nickname'],player_id=r['player_id'],completed=r['completed'],
                     tid=r['tid']) for i,r in enumerate(rows)]

    def timings(self, db, cfg, mode, tid):
        entrant=db.execute('SELECT created_at FROM entrants WHERE mode=? AND tid=?',(mode,tid)).fetchone()
        registered=entrant['created_at'] if entrant else self.clock()
        finishes={r['stage']:r['submitted_ns']/1e9 for r in db.execute('SELECT stage,submitted_ns FROM solves WHERE mode=? AND tid=?',(mode,tid))}
        result=[]
        for i,stage in enumerate(cfg['stages']):
            start=registered if mode=='test' else cfg['start_at']+stage['offset']
            if i:
                start=max(start,finishes.get(i-1,float('inf')))
            active=start<=self.clock()
            end=finishes.get(i,min(self.clock(),cfg['end_at']) if mode=='live' else self.clock())
            result.append(dict(started_at=start if active else None,finished_at=finishes.get(i),elapsed_ms=max(0,round((end-start)*1000)) if active else 0))
        return result

    def speed_ranking(self,db,cfg,mode):
        ranks=self.ranking(db,mode)
        for row in ranks:
            timings=self.timings(db,cfg,mode,row['tid'])
            row['elapsed_ms']=sum(t['elapsed_ms'] for t in timings if t['finished_at'] is not None)
        ranks.sort(key=lambda r:(-r['completed'],r['elapsed_ms'],r['place']))
        for i,r in enumerate(ranks):r['place']=i+1
        return ranks

    def state(self, db, cfg, identity, mode):
        owner=self.owner(identity,cfg)
        phase=self.phase(cfg)
        visible=owner or phase in ('scheduled','open','finished')
        result=dict(ok=True,visible=visible,owner=owner,phase=phase,server_at=self.clock(),
                    start_at=cfg['start_at'],end_at=cfg['end_at'],mode=mode,ready=self.ready(cfg))
        if not visible:
            return result
        if not owner and phase=='scheduled':
            # Public waiting room contains no stage metadata or private materials.
            return result
        if not identity:
            result['login_required']=True
            return result
        tid=str(identity['id'])
        entrant=db.execute('SELECT nickname,player_id FROM entrants WHERE mode=? AND tid=?',(mode,tid)).fetchone()
        solved={r['stage'] for r in db.execute('SELECT stage FROM solves WHERE mode=? AND tid=?',(mode,tid))}
        attempts={r['stage']:r for r in db.execute('SELECT * FROM attempts WHERE mode=? AND tid=?',(mode,tid))}
        result['entrant']=dict(entrant) if entrant else None
        result['stages']=[]
        for i,x in enumerate(cfg['stages']):
            opens=cfg['start_at']+x['offset']
            released=mode=='test' or self.clock()>=opens
            a=attempts.get(i)
            item=dict(index=i,title=x['title'],opens_at=opens,released=released,solved=i in solved,
                      retry_at=(a['last_at']+cfg['cooldown']) if a else 0)
            prior=all(j in solved for j in range(i))
            item['unlocked']=released and prior
            if item['unlocked'] or owner:
                done={r['point'] for r in db.execute('SELECT point FROM checkpoints WHERE mode=? AND tid=? AND stage=?',(mode,tid,i))}
                item['points']=[dict(index=j,title=q['title'],solved=j in done,
                    prompt=q['prompt'] if all(k in done for k in range(j)) else '',
                    unlocked=all(k in done for k in range(j))) for j,q in enumerate(x.get('points',[]))]
                item['final_unlocked']=len(done)==3 if x.get('points') else True
                if item['final_unlocked']:
                    item['prompt']=x['prompt']
            result['stages'].append(item)
        ranks=self.ranking(db,mode)
        own=next((r for r in ranks if r['tid']==tid),None)
        result['my_place']=own['place'] if own else None
        result['my_completed']=len(solved)
        result['timings']=self.timings(db,cfg,mode,tid)
        speed=self.speed_ranking(db,cfg,mode)
        result['speed_leaderboard']=[{k:v for k,v in r.items() if k!='tid'} for r in speed[:100]]
        result['my_speed_place']=next((r['place'] for r in speed if r['tid']==tid),None)
        result['fastest_finalist']=next(({k:v for k,v in r.items() if k!='tid'} for r in speed if r['completed']==3),None)
        result['leaderboard']=[{k:v for k,v in r.items() if k!='tid'} for r in ranks[:100]]
        result['ranked_total']=len(ranks)
        result['total']=db.execute('SELECT COUNT(*) FROM entrants WHERE mode=?',(mode,)).fetchone()[0]
        if owner:
            result['admin_config']={k:v for k,v in cfg.items() if k not in ('owner_id','stages')}
            result['admin_config']['stages']=[dict(title=x['title'],prompt=x['prompt'],offset=x['offset'],has_answer=bool(x['digest']),solution=x.get('solution','')) for x in cfg['stages']]
        return result

    def handle(self, method, action, token='', body=None):
        if method=='POST':
            # Fair local write queue prevents SQLite lock starvation under bursts.
            with self.write_lock:
                return self._handle(method,action,token,body)
        return self._handle(method,action,token,body)

    def _handle(self, method, action, token='', body=None):
        body=body or {}
        if not isinstance(body,dict):
            raise ContestError('invalid_request')
        identity=self.identity(token)
        mode='test' if body.get('mode')=='test' else 'live'
        with self.db() as db:
            cfg=self.config(db)
            owner=self.owner(identity,cfg)
            if method=='GET' and action=='status':
                return self.state(db,cfg,identity,'live')
            if method=='POST' and action=='login':
                candidate=self.verify_login(body.get('telegram'))
                if not candidate:
                    raise ContestError('invalid_telegram_login',401)
                is_owner=self.owner(candidate,cfg)
                if not is_owner and self.phase(cfg) not in ('open','finished'):
                    raise ContestError('contest_hidden',404)
                if not is_owner and cfg['audience']=='members':
                    # An existing cabinet session is required; do not add to its allowlist.
                    if not self.cabinet_identity('id:'+str(candidate['id'])):
                        raise ContestError('members_only',403)
                return dict(ok=True,token=self.token(candidate))
            if not identity:
                raise ContestError('unauthorized',401)
            if action=='admin/config' and method=='POST':
                if not owner:
                    raise ContestError('forbidden',403)
                db.execute('BEGIN IMMEDIATE')
                cfg=self.config(db)
                if cfg['armed'] and self.clock()>=cfg['start_at']:
                    raise ContestError('configuration_locked',409)
                stages=body.get('stages')
                if not isinstance(stages,list) or len(stages)!=3:
                    raise ContestError('three_stages_required')
                updated=[]
                for i,x in enumerate(stages):
                    if not isinstance(x,dict):
                        raise ContestError('invalid_stage')
                    prompt=str(x.get('prompt','')).strip()
                    title=str(x.get('title','')).strip()[:120]
                    offset=int(x.get('offset',i*1800))
                    answer=str(x.get('answer','')).strip()
                    if len(prompt)>12000 or len(answer)>500 or not 0<=offset<=10800:
                        raise ContestError('invalid_stage')
                    updated.append(dict(title=title or 'Этап '+str(i+1),prompt=prompt,offset=offset,
                                        digest=self.digest(i,answer) if answer else cfg['stages'][i]['digest'],
                                        solution=answer if answer else cfg['stages'][i].get('solution',''),points=cfg['stages'][i].get('points',[])))
                if updated[0]['offset']!=0 or updated[1]['offset']<1200 or updated[2]['offset']<updated[1]['offset']+1200:
                    raise ContestError('stage_interval_too_short')
                start=int(body.get('start_at',cfg['start_at']))
                end=int(body.get('end_at',cfg['end_at']))
                if end<=start+updated[-1]['offset'] or end>start+86400:
                    raise ContestError('invalid_deadline')
                cfg.update(stages=updated,start_at=start,end_at=end,audience=body.get('audience','all'))
                if cfg['audience'] not in ('all','members'):
                    raise ContestError('invalid_audience')
                if body.get('armed') and (not self.ready(cfg) or start<=self.clock()):
                    raise ContestError('not_ready_or_start_passed')
                cfg['armed']=bool(body.get('armed'))
                db.execute('UPDATE settings SET value=? WHERE id=1',(json.dumps(cfg),))
                return self.state(db,cfg,identity,'test')
            if action=='admin/pause' and method=='POST':
                if not owner:
                    raise ContestError('forbidden',403)
                db.execute('BEGIN IMMEDIATE')
                cfg=self.config(db)
                cfg['paused']=bool(body.get('paused'))
                db.execute('UPDATE settings SET value=? WHERE id=1',(json.dumps(cfg),))
                return dict(ok=True,paused=cfg['paused'])
            if action=='admin/reset-test' and method=='POST':
                if not owner:
                    raise ContestError('forbidden',403)
                db.execute('BEGIN IMMEDIATE')
                for table in ('entrants','solves','attempts','checkpoints','point_attempts'):
                    db.execute('DELETE FROM '+table+' WHERE mode=?',('test',))
                return dict(ok=True)
            if mode=='test' and not owner:
                raise ContestError('forbidden',403)
            if not owner and self.phase(cfg) not in ('open','finished'):
                raise ContestError('contest_hidden',404)
            if cfg['audience']=='members' and not owner and not identity.get('member'):
                # Contest tokens don't confer cabinet permissions. Check read-only membership.
                if not self.cabinet_identity('id:'+str(identity['id'])):
                    raise ContestError('members_only',403)
            if action=='material' and method=='POST':
                material_path=Path(__file__).parent/'contest_material.json'
                stamp=material_path.stat().st_mtime_ns
                if getattr(self,'_material_stamp',None)!=stamp:
                    self._material_cache=json.loads(material_path.read_text(encoding='utf-8'))
                    self._material_stamp=stamp
                bundle=self._material_cache
                kind=body.get('kind')
                selected_items=[dict(x) for x in bundle['items']] if kind=='items' else None
                selected_recipes=json.loads(json.dumps(bundle['recipes'])) if kind=='recipes' else None
                if kind not in ('items','recipes','map','maps'):
                    raise ContestError('not_found',404)
                if not owner:
                    completed={r['stage'] for r in db.execute('SELECT stage FROM solves WHERE mode=? AND tid=?',(mode,str(identity['id'])))}
                    if kind in ('map','maps') and (1 not in completed or self.clock()<cfg['start_at']+cfg['stages'][2]['offset']):
                        raise ContestError('previous_stage_required',409)
                    if kind=='items' and 1 not in completed:
                        for item in selected_items:
                            item.pop('note',None)
                    if kind=='recipes' and 1 not in completed:
                        for recipe in selected_recipes:
                            for component in recipe.get('components',[]):
                                component.pop('note',None)
                if kind=='map':
                    key=body.get('key','')
                    if key not in bundle['map_data']:
                        raise ContestError('not_found',404)
                    return dict(ok=True,material=bundle['map_data'][key])
                return dict(ok=True,material=selected_items if kind=='items' else selected_recipes if kind=='recipes' else bundle[kind])
            if action=='state' and method=='POST':
                return self.state(db,cfg,identity,mode)
            if action not in ('register','answer','checkpoint') or method!='POST':
                raise ContestError('not_found',404)
            db.execute('BEGIN IMMEDIATE')
            cfg=self.config(db)
            if mode=='live' and self.phase(cfg)!='open':
                raise ContestError('contest_not_open',409)
            tid=str(identity['id'])
            if action=='register':
                player_id=str(body.get('player_id','')).strip()
                nickname=str(body.get('nickname','')).strip()
                if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',player_id) or not 2<=len(nickname)<=60:
                    raise ContestError('invalid_participant')
                old=db.execute('SELECT * FROM entrants WHERE mode=? AND tid=?',(mode,tid)).fetchone()
                if old and (old['player_id']!=player_id or old['nickname']!=nickname):
                    raise ContestError('registration_locked',409)
                try:
                    db.execute('INSERT OR IGNORE INTO entrants(mode,tid,player_id,nickname,created_at) VALUES(?,?,?,?,?)',(mode,tid,player_id,nickname,self.clock()))
                    registered=db.execute('SELECT * FROM entrants WHERE mode=? AND tid=?',(mode,tid)).fetchone()
                    if not registered:
                        raise ContestError('player_already_registered',409)
                except sqlite3.IntegrityError:
                    raise ContestError('player_already_registered',409)
                return self.state(db,cfg,identity,mode)
            try:
                stage=int(body.get('stage',-1))
            except (TypeError,ValueError):
                raise ContestError('invalid_stage')
            if stage not in range(3):
                raise ContestError('invalid_stage')
            if not db.execute('SELECT 1 FROM entrants WHERE mode=? AND tid=?',(mode,tid)).fetchone():
                raise ContestError('registration_required',409)
            if mode=='live' and self.clock()<cfg['start_at']+cfg['stages'][stage]['offset']:
                raise ContestError('stage_not_open',409)
            solved={r['stage'] for r in db.execute('SELECT stage FROM solves WHERE mode=? AND tid=?',(mode,tid))}
            if stage in solved:
                return dict(ok=True,correct=True,already_solved=True,state=self.state(db,cfg,identity,mode))
            if any(i not in solved for i in range(stage)):
                raise ContestError('previous_stage_required',409)
            points=cfg['stages'][stage].get('points',[])
            done={r['point'] for r in db.execute('SELECT point FROM checkpoints WHERE mode=? AND tid=? AND stage=?',(mode,tid,stage))}
            if action=='checkpoint':
                point=body.get('point')
                if type(point) is not int or point not in range(len(points)):
                    raise ContestError('invalid_checkpoint')
                if point in done:
                    return dict(ok=True,correct=True,already_solved=True,state=self.state(db,cfg,identity,mode))
                if any(j not in done for j in range(point)):
                    raise ContestError('previous_checkpoint_required',409)
                previous=db.execute('SELECT last_at FROM point_attempts WHERE mode=? AND tid=? AND stage=? AND point=?',(mode,tid,stage,point)).fetchone()
                if previous and self.clock()<previous['last_at']+cfg['cooldown']:
                    raise ContestError('wait_before_retry',429)
                answer=str(body.get('answer',''))
                if not answer.strip() or len(answer)>500:
                    raise ContestError('invalid_answer')
                correct=hmac.compare_digest(self.digest(f'{stage}.{point}',answer),points[point]['digest'])
                db.execute('INSERT INTO point_attempts VALUES(?,?,?,?,?) ON CONFLICT(mode,tid,stage,point) DO UPDATE SET last_at=excluded.last_at',(mode,tid,stage,point,self.clock()))
                if correct:
                    db.execute('INSERT INTO checkpoints VALUES(?,?,?,?,?)',(mode,tid,stage,point,time.time_ns()))
                return dict(ok=True,correct=correct,state=self.state(db,cfg,identity,mode))
            if points and len(done)!=3:
                raise ContestError('checkpoints_required',409)
            a=db.execute('SELECT * FROM attempts WHERE mode=? AND tid=? AND stage=?',(mode,tid,stage)).fetchone()
            now=self.clock()
            if a and now<a['last_at']+cfg['cooldown']:
                raise ContestError('wait_before_retry',429)
            answer=str(body.get('answer',''))
            if not answer.strip() or len(answer)>500:
                raise ContestError('invalid_answer')
            db.execute('''INSERT INTO attempts VALUES(?,?,?,?,?) ON CONFLICT(mode,tid,stage)
                          DO UPDATE SET count=count+1,last_at=excluded.last_at''',(mode,tid,stage,1,now))
            correct=bool(cfg['stages'][stage]['digest']) and hmac.compare_digest(self.digest(stage,answer),cfg['stages'][stage]['digest'])
            if correct:
                # Time measured inside the serialized transaction; seq resolves exact ties.
                submitted_ns=time.time_ns() if self.clock is time.time else int(self.clock()*1e9)
                db.execute('INSERT INTO solves(mode,tid,stage,submitted_ns) VALUES(?,?,?,?)',(mode,tid,stage,submitted_ns))
            return dict(ok=True,correct=correct,state=self.state(db,cfg,identity,mode))


def install(server):
    import os
    main_db=os.environ.get('HK_LICENSE_DB','/var/lib/hamsterking-license/licenses.db')
    path=Path(main_db).parent/'contest.db'
    def read_only_identity(token):
        if token.startswith('id:'):
            tid=token[3:]
        else:
            doc=server['token_document'](token)
            sub=str((doc or {}).get('sub',''))
            if not sub.startswith('telegram:'):
                return None
            tid=sub[9:]
        if not re.fullmatch(r'[1-9][0-9]{4,19}',tid):
            return None
        with sqlite3.connect('file:'+str(main_db)+'?mode=ro',uri=True,timeout=5) as db:
            db.row_factory=sqlite3.Row
            row=db.execute('SELECT telegram_id,first_name,active FROM clan_members WHERE telegram_id=?',(tid,)).fetchone()
        if not row or not row['active']:
            return None
        return dict(id=tid,first_name=row['first_name'],member=True)
    contest=Contest(path,server['SIGNING_SECRET'],server['verify_telegram_login'],read_only_identity)
    with contest.db() as db:
        needs_content=not any(s.get('points') for s in contest.config(db)['stages'])
    if needs_content and (Path(__file__).parent/'contest_content.json').exists():
        from load_contest_content import load
        load(contest)
    content_path=Path(__file__).parent/'contest_content.json'
    if content_path.exists():
        with contest.write_lock,contest.db() as db:
            cfg=contest.config(db)
            if contest.clock()<cfg['start_at'] and db.execute("SELECT COUNT(*) FROM entrants WHERE mode='live'").fetchone()[0]==0:
                content=json.loads(content_path.read_text(encoding='utf-8'))
                # Refresh approved wording and digests before launch; preserve participant progress.
                for i, stage in enumerate(content):
                    cfg['stages'][i]['prompt']=stage['prompt']
                    cfg['stages'][i]['digest']=contest.digest(i,stage['answer'])
                    for j, point in enumerate(stage['points']):
                        cfg['stages'][i]['points'][j]['prompt']=point['prompt']
                        cfg['stages'][i]['points'][j]['digest']=contest.digest(f'{i}.{j}',point['answer'])
                db.execute('UPDATE settings SET value=? WHERE id=1',(json.dumps(cfg),))
    def dispatch(handler):
        parsed=urlsplit(handler.path)
        if not parsed.path.startswith(PREFIX):
            return False
        action=parsed.path[len(PREFIX):]
        token=handler.headers.get('Authorization','').removeprefix('Bearer ').strip()
        try:
            ip=handler.client_ip()
            if not server['rate_allowed']('contest-requests:'+ip,180,60):
                raise ContestError('rate_limited',429)
            if token and not server['rate_allowed']('contest-session:'+hashlib.sha256(token.encode()).hexdigest(),60,60):
                raise ContestError('rate_limited',429)
            if handler.command=='POST':
                if handler.headers.get('Origin','') not in server['CABINET_ORIGINS']:
                    raise ContestError('origin_not_allowed',403)
                ip=handler.client_ip()
                if action=='login' and not server['rate_allowed']('contest-login:'+ip,30,900):
                    raise ContestError('rate_limited',429)
                body=handler.read_json(48000 if action=='admin/config' else 8192)
            else:
                body={}
            data=contest.handle(handler.command,action,token,body)
            handler.send_cabinet_json(200,data)
        except ContestError as exc:
            handler.send_cabinet_json(exc.status,dict(error=exc.code))
        except (ValueError, TypeError, KeyError, json.JSONDecodeError):
            handler.send_cabinet_json(400,dict(error='invalid_request'))
        except sqlite3.Error:
            handler.send_cabinet_json(503,dict(error='temporarily_unavailable'))
        return True
    return dispatch
