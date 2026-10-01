import concurrent.futures
import json
import tempfile
import unittest
from pathlib import Path
from contest_runtime import Contest,ContestError,START

class ContestTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.now=START-3600
        self.owner=dict(id='552583086',first_name='Owner')
        self.c=Contest(Path(self.tmp.name)/'contest.db','test-secret',lambda x:x if isinstance(x,dict) and x.get('signed') else None,
                       lambda t:dict(id='11111111',member=True) if t in ('cabinet-member','id:11111111') else None,lambda:self.now)
        self.owner_token=self.c.token(self.owner)
        with self.c.db() as db:
            cfg=self.c.config(db);cfg['owner_id']=self.owner['id'];db.execute('UPDATE settings SET value=?',(json.dumps(cfg),))
        self.tasks=[dict(title='Stage '+str(i),prompt='Test puzzle '+str(i),answer=' Key '+str(i)+' ',offset=i*1800) for i in range(3)]
        self.config()
    def tearDown(self):
        self.tmp.cleanup()
    def config(self,**kw):
        body=dict(stages=self.tasks,start_at=START,end_at=START+7200,armed=True,audience='all',**kw)
        return self.c.handle('POST','admin/config',self.owner_token,body)
    def token(self,i=11111111):
        return self.c.token(dict(id=str(i)))
    def call(self,action,token=None,**body):
        return self.c.handle('POST',action,token or self.token(),body)
    def assertCode(self,code,action,token=None,**body):
        with self.assertRaises(ContestError) as ctx:self.call(action,token,**body)
        self.assertEqual(ctx.exception.code,code)
    def register(self,token=None,mode='live',pid='game-1'):
        return self.call('register',token,mode=mode,player_id=pid,nickname='Игрок '+pid)
    def test_hidden_and_owner_only(self):
        state=self.c.handle('GET','status')
        self.assertFalse(state['visible']);self.assertNotIn('stages',state);self.assertNotIn('leaderboard',state)
        self.assertTrue(self.c.handle('GET','status',self.owner_token)['owner'])
        self.assertCode('forbidden','state',mode='test')
        self.assertCode('forbidden','admin/reset-test')
        self.assertCode('contest_hidden','login',telegram=dict(id='11111111',signed=True))
        for raw in ('id:11111111',self.token()[:-1]+'x','ct1.bad.bad'):
            self.assertIsNone(self.c.identity(raw))
    def test_schedule_order_wrong_retry_and_duplicate(self):
        self.now=START
        self.register()
        self.assertCode('stage_not_open','answer',stage=1,answer='Key 1')
        wrong=self.call('answer',stage=0,answer='wrong');self.assertFalse(wrong['correct'])
        self.assertCode('wait_before_retry','answer',stage=0,answer='key 0')
        self.now+=30
        first=self.call('answer',stage=0,answer='  KEY 0  ');self.assertTrue(first['correct']);self.assertEqual(first['state']['my_place'],1)
        with self.c.db() as db:timestamp=db.execute('SELECT submitted_ns FROM solves').fetchone()[0]
        self.now+=30
        self.assertTrue(self.call('answer',stage=0,answer='key 0')['already_solved'])
        with self.c.db() as db:self.assertEqual(timestamp,db.execute('SELECT submitted_ns FROM solves').fetchone()[0])
        self.now=START+1800
        self.call('answer',stage=1,answer='key 1')
        self.now=START+3600
        self.assertEqual(self.call('answer',stage=2,answer='key 2')['state']['my_completed'],3)
        self.now=START+7200
        self.assertCode('contest_not_open','answer',stage=2,answer='key 2')
    def test_test_isolation_and_reset(self):
        self.register(self.owner_token,'test')
        self.call('answer',self.owner_token,mode='test',stage=0,answer='key 0')
        live=self.c.handle('GET','status',self.owner_token)
        self.assertEqual(live['total'],0);self.assertEqual(live['leaderboard'],[])
        self.now=START;self.register();self.call('answer',stage=0,answer='key 0')
        self.call('admin/reset-test',self.owner_token)
        with self.c.db() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM solves WHERE mode='test'").fetchone()[0],0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM solves WHERE mode='live'").fetchone()[0],1)
    def test_unique_player_and_sequential_stages(self):
        self.now=START+3600;self.register()
        self.assertCode('player_already_registered','register',self.token(22222222),player_id='game-1',nickname='Another')
        self.assertCode('registration_locked','register',player_id='game-2',nickname='Another')
        self.assertCode('previous_stage_required','answer',stage=2,answer='key 2')
    def test_config_and_answers_do_not_leak(self):
        self.now=START
        self.register()
        text=json.dumps(self.call('state'))
        self.assertNotIn('digest',text);self.assertNotIn('admin_config',text);self.assertNotIn('Test puzzle 1',text)
        self.assertCode('configuration_locked','admin/config',self.owner_token,stages=self.tasks)
        self.assertCode('forbidden','admin/config',stages=self.tasks)
    def test_pause(self):
        self.now=START;self.register()
        self.call('admin/pause',self.owner_token,paused=True)
        self.assertCode('contest_hidden','answer',stage=0,answer='key 0')
        self.call('admin/pause',self.owner_token,paused=False)
        self.assertTrue(self.call('answer',stage=0,answer='key 0')['correct'])
    def test_300_concurrent_participants_and_stable_ties(self):
        self.now=START
        def solve(i):
            t=self.token(10000000+i);self.register(t,pid='player-'+str(i));self.call('answer',t,stage=0,answer='key 0')
        with concurrent.futures.ThreadPoolExecutor(max_workers=24) as pool:
            list(pool.map(solve,range(300)))
        with self.c.db() as db:
            ranking=self.c.ranking(db,'live');self.assertEqual(len(ranking),300)
            self.assertEqual(len({r['place'] for r in ranking}),300)
            self.assertEqual(ranking,self.c.ranking(db,'live'))
        self.now=START+1800
        t=self.token(10000000);self.call('answer',t,stage=1,answer='key 1')
        self.assertEqual(self.call('state',t)['my_place'],1)
    def test_generated_draft_private_solutions_and_closed_schedule(self):
        self.assertCode('forbidden','admin/generate')
        generated=self.call('admin/generate',self.owner_token)
        self.assertFalse(generated['admin_config']['armed'])
        self.assertEqual(generated['phase'],'draft')
        solutions=[x['solution'] for x in generated['admin_config']['stages']]
        self.assertTrue(all(solutions))
        self.register(self.owner_token,'test')
        for i,answer in enumerate(solutions):
            self.assertTrue(self.call('answer',self.owner_token,mode='test',stage=i,answer=answer)['correct'])
        self.assertNotIn('admin_config',self.c.handle('GET','status'))
        self.assertNotIn('stages',self.c.handle('GET','status'))
    def test_pausing_does_not_unlock_tasks_after_start(self):
        self.now=START
        self.call('admin/pause',self.owner_token,paused=True)
        self.assertCode('configuration_locked','admin/generate',self.owner_token)
        self.assertCode('configuration_locked','admin/config',self.owner_token,stages=self.tasks)

if __name__=='__main__':unittest.main()
