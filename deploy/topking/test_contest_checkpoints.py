import json
import tempfile
import unittest
from pathlib import Path
from contest_runtime import Contest,ContestError,START

class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.now=START+4000
        self.c=Contest(Path(self.tmp.name)/'contest.db','fixture',lambda _:None,lambda _:None,lambda:self.now)
        self.token=self.c.token(dict(id='11111111'))
        with self.c.db() as db:
            cfg=self.c.config(db);cfg.update(armed=True)
            for i,s in enumerate(cfg['stages']):
                s.update(prompt=f'final-{i}',digest=self.c.digest(i,'final'),points=[dict(title=f'point-{j}',prompt=f'secret-{i}-{j}',digest=self.c.digest(f'{i}.{j}',f'answer-{j}')) for j in range(3)])
            db.execute('UPDATE settings SET value=?',(json.dumps(cfg),))
        self.call('register',player_id='fixture',nickname='Participant')
    def tearDown(self):self.tmp.cleanup()
    def call(self,action,**kw):return self.c.handle('POST',action,self.token,kw)
    def blocked(self,code,action,**kw):
        with self.assertRaises(ContestError) as e:self.call(action,**kw)
        self.assertEqual(e.exception.code,code)
    def test_no_skipping_even_after_all_release_times(self):
        self.blocked('previous_stage_required','checkpoint',stage=1,point=0,answer='answer-0')
        self.blocked('previous_stage_required','answer',stage=2,answer='final')
        self.blocked('checkpoints_required','answer',stage=0,answer='final')
        self.blocked('previous_checkpoint_required','checkpoint',stage=0,point=2,answer='answer-2')
        state=json.dumps(self.call('state'),ensure_ascii=False)
        self.assertNotIn('final-1',state);self.assertNotIn('secret-0-1',state);self.assertNotIn('digest',state)
        for i in range(3):
            for j in range(3):
                self.assertTrue(self.call('checkpoint',stage=i,point=j,answer=f'answer-{j}')['correct'])
                self.assertTrue(self.call('checkpoint',stage=i,point=j,answer='wrong')['already_solved'])
            self.assertTrue(self.call('answer',stage=i,answer='final')['correct'])
        self.assertEqual(self.call('state')['my_completed'],3)
        with self.c.db() as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM checkpoints').fetchone()[0],9)
    def test_wrong_answer_cooldown_and_persistent_progress(self):
        self.assertFalse(self.call('checkpoint',stage=0,point=0,answer='wrong')['correct'])
        self.blocked('wait_before_retry','checkpoint',stage=0,point=0,answer='answer-0')
        self.now+=30;self.call('checkpoint',stage=0,point=0,answer='answer-0')
        c2=Contest(self.c.path,'fixture',lambda _:None,lambda _:None,lambda:self.now)
        state=c2.handle('POST','state',self.token,{})
        self.assertTrue(state['stages'][0]['points'][0]['solved'])
        self.assertFalse(state['stages'][0]['final_unlocked'])

if __name__=='__main__':unittest.main()
