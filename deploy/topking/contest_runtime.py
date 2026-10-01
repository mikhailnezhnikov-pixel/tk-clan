"""Isolated TK Clan competition; no mutations of cabinet membership or licenses."""
import base64
import hashlib
import hmac
import json
import re
import sqlite3
import time
import unicodedata
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit

PREFIX = '/api/v1/cabinet/contest/'
START = 1790856000  # 2026-10-01 21:00 Asia/Yakutsk


class ContestError(Exception):
    def __init__(self, code, status=400):
        self.code, self.status = code, status


class Contest:
    def __init__(self, path, secret, verify_login, cabinet_identity, clock=time.time):
        self.path, self.secret = str(path), secret.encode()
        self.verify_login, self.cabinet_identity, self.clock = verify_login, cabinet_identity, clock
        with self.db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY CHECK(id=1), value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS entrants (
                    mode TEXT NOT NULL, tid TEXT NOT NULL, player_id TEXT NOT NULL, nickname TEXT NOT NULL,
                    PRIMARY KEY(mode,tid), UNIQUE(mode,player_id));
                CREATE TABLE IF NOT EXISTS solves (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, mode TEXT NOT NULL, tid TEXT NOT NULL,
                    stage INTEGER NOT NULL, submitted_ns INTEGER NOT NULL, UNIQUE(mode,tid,stage));
                CREATE INDEX IF NOT EXISTS solve_ranking ON solves(mode,stage,submitted_ns,seq);
                CREATE TABLE IF NOT EXISTS attempts (
                    mode TEXT NOT NULL, tid TEXT NOT NULL, stage INTEGER NOT NULL,
                    count INTEGER NOT NULL, last_at REAL NOT NULL, PRIMARY KEY(mode,tid,stage));
            ''')
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
        return ' '.join(unicodedata.normalize('NFKC',str(answer)).casefold().replace('ё','е').split())

    def digest(self, stage, answer):
        return hmac.new(self.secret, ('contest-answer:'+str(stage)+':'+self.normalize(answer)).encode(),hashlib.sha256).hexdigest()

    def ready(self, cfg):
        return len(cfg['stages'])==3 and all(x['prompt'].strip() and x['digest'] for x in cfg['stages'])

    def generate_draft(self, cfg):
        import itertools
        import secrets
        rng=secrets.SystemRandom()
        grid=[[rng.randrange(1,10) for _ in range(8)] for _ in range(8)]
        y=x=0; total=grid[0][0];directions=[]
        for _ in range(24):
            options=[(dy,dx,name) for dy,dx,name in ((0,1,'вправо'),(0,-1,'влево'),(1,0,'вниз'),(-1,0,'вверх')) if 0<=y+dy<8 and 0<=x+dx<8]
            dy,dx,name=rng.choice(options);y+=dy;x+=dx;total+=grid[y][x];directions.append(name)
        grid_text='\n'.join(' '.join(map(str,row)) for row in grid)
        path='\n'.join(f'{i+1}. {name} на 1 клетку' for i,name in enumerate(directions))
        prompt1=('Первый ключ — маршрут хранителя.\n\nНа карте 8 строк и 8 столбцов. Первая строка сверху, первый столбец слева. Старт — верхняя левая клетка.\n\n'+grid_text+'\n\nВыполните маршрут:\n'+path+'\n\nСложите число стартовой клетки и числа всех 24 клеток, в которые вы пришли. Если клетка посещена повторно, её число снова прибавляется. Умножьте сумму на 7 и прибавьте 13. Ответ — полученное целое число, без других слов. Сохраните его: он понадобится в финале.')
        answer1=str(total*7+13)
        names=['Альфа','Бета','Гамма','Дельта','Эпсилон']
        permutation=list(range(1,6));rng.shuffle(permutation)
        candidates=[]
        for a in range(5):
            for b in range(a+1,5):
                if permutation[a]<permutation[b]:
                    candidates.append((f'{names[a]} стоит левее, чем {names[b]}.',lambda p,a=a,b=b:p[a]<p[b]))
                else:
                    candidates.append((f'{names[b]} стоит левее, чем {names[a]}.',lambda p,a=a,b=b:p[b]<p[a]))
                dist=abs(permutation[a]-permutation[b])
                candidates.append((f'Между {names[a]} и {names[b]} ровно {dist-1} сундуков.',lambda p,a=a,b=b,d=dist:abs(p[a]-p[b])==d))
        rng.shuffle(candidates);solutions=list(itertools.permutations(range(1,6)));clues=[]
        for text,predicate in candidates:
            filtered=[p for p in solutions if predicate(p)]
            if len(filtered)<len(solutions):
                clues.append(text);solutions=filtered
            if len(solutions)==1:break
        assert solutions==[tuple(permutation)]
        answer2=''.join(map(str,permutation))
        prompt2=('Второй ключ — пять сундуков.\n\nСундуки стоят в один ряд и пронумерованы от 1 до 5 слева направо. У каждого один хранитель: Альфа, Бета, Гамма, Дельта и Эпсилон. Каждый хранитель встречается ровно один раз. Все подсказки верны:\n\n'+'\n'.join(f'{i+1}. {clue}' for i,clue in enumerate(clues))+'\n\nВ ответе укажите пять номеров БЕЗ пробелов в порядке: Альфа, Бета, Гамма, Дельта, Эпсилон. Например, 12345 означает, что Альфа у первого сундука, Бета у второго и так далее. Сохраните ответ для финала.')
        alphabet='АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
        words=['КОРОНА','СОКРОВИЩЕ','ХРАНИТЕЛЬ','ПОБЕДА','АЛМАЗ','КЛЮЧ','СУНДУК','ЗАМOК'.replace('O','О')]
        rng.shuffle(words);answer3=' '.join(words[:4])
        shift=(int(answer1)+sum((i+1)*n for i,n in enumerate(permutation)))%len(alphabet)
        encrypted=''.join(alphabet[(alphabet.index(c)+shift)%len(alphabet)] if c in alphabet else c for c in answer3)
        prompt3=('Финальный ключ — королевский шифр.\n\nИспользуйте свои ответы первых двух этапов.\n1. Возьмите число первого этапа.\n2. Пять цифр второго этапа умножьте соответственно на 1, 2, 3, 4 и 5, затем сложите произведения.\n3. Сложите результаты пунктов 1 и 2. Остаток от деления этой суммы на 32 — сдвиг шифра.\n\nАлфавит из 32 букв (без Ё):\n'+alphabet+'\n\nЗашифрованная фраза:\n'+encrypted+'\n\nДля расшифровки сдвиньте каждую букву НАЗАД на вычисленное число позиций. При выходе за начало продолжайте с конца алфавита. Пробелы сохраняются. Ответ — четыре расшифрованных слова в исходном порядке.')
        prompts=[prompt1,prompt2,prompt3];answers=[answer1,answer2,answer3]
        titles=['Маршрут хранителя','Пять сундуков','Королевский шифр']
        cfg['stages']=[dict(title=titles[i],prompt=prompts[i],offset=i*1800,digest=self.digest(i,answers[i]),
                            solution=answers[i]) for i in range(3)]
        cfg['armed']=False
        return cfg

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

    def state(self, db, cfg, identity, mode):
        owner=self.owner(identity,cfg)
        phase=self.phase(cfg)
        visible=owner or phase in ('open','finished')
        result=dict(ok=True,visible=visible,owner=owner,phase=phase,server_at=self.clock(),
                    start_at=cfg['start_at'],end_at=cfg['end_at'],mode=mode,ready=self.ready(cfg))
        if not visible:
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
            if released or owner:
                item['prompt']=x['prompt']
            result['stages'].append(item)
        ranks=self.ranking(db,mode)
        own=next((r for r in ranks if r['tid']==tid),None)
        result['my_place']=own['place'] if own else None
        result['my_completed']=len(solved)
        result['leaderboard']=[{k:v for k,v in r.items() if k!='tid'} for r in ranks[:100]]
        result['ranked_total']=len(ranks)
        result['total']=db.execute('SELECT COUNT(*) FROM entrants WHERE mode=?',(mode,)).fetchone()[0]
        if owner:
            result['admin_config']={k:v for k,v in cfg.items() if k not in ('owner_id','stages')}
            result['admin_config']['stages']=[dict(title=x['title'],prompt=x['prompt'],offset=x['offset'],has_answer=bool(x['digest']),solution=x.get('solution','')) for x in cfg['stages']]
        return result

    def handle(self, method, action, token='', body=None):
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
            if action=='admin/generate' and method=='POST':
                if not owner:
                    raise ContestError('forbidden',403)
                db.execute('BEGIN IMMEDIATE')
                cfg=self.config(db)
                if cfg['armed'] and self.clock()>=cfg['start_at']:
                    raise ContestError('configuration_locked',409)
                cfg=self.generate_draft(cfg)
                db.execute('UPDATE settings SET value=? WHERE id=1',(json.dumps(cfg),))
                for table in ('entrants','solves','attempts'):
                    db.execute('DELETE FROM '+table+' WHERE mode=?',('test',))
                return self.state(db,cfg,identity,'test')
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
                                        solution=answer if answer else cfg['stages'][i].get('solution','')))
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
                for table in ('entrants','solves','attempts'):
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
            if action=='state' and method=='POST':
                return self.state(db,cfg,identity,mode)
            if action not in ('register','answer') or method!='POST':
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
                    db.execute('INSERT OR IGNORE INTO entrants VALUES(?,?,?,?)',(mode,tid,player_id,nickname))
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
        cfg=contest.config(db)
        if cfg['owner_id'] and not any(x['prompt'] for x in cfg['stages']):
            cfg=contest.generate_draft(cfg)
            db.execute('UPDATE settings SET value=? WHERE id=1',(json.dumps(cfg),))
    def dispatch(handler):
        parsed=urlsplit(handler.path)
        if not parsed.path.startswith(PREFIX):
            return False
        action=parsed.path[len(PREFIX):]
        token=handler.headers.get('Authorization','').removeprefix('Bearer ').strip()
        try:
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
