import json
from test_contest_checkpoints import CheckpointTests
from contest_runtime import START, ContestError

class WaitingTests(CheckpointTests):
    def test_waiting_room_reveals_only_schedule(self):
        self.now=START-1
        public=self.c.handle('GET','status')
        self.assertTrue(public['visible'])
        self.assertEqual(public['phase'],'scheduled')
        self.assertEqual(public['start_at'],1790861400)
        for token in ('',self.token,'ct1.forged.fake'):
            data=self.c.handle('GET','status',token)
            self.assertFalse({'stages','admin_config','entrant','leaderboard'} & data.keys())
            self.assertNotIn('secret',json.dumps(data))
        for action,body in [('material',{'kind':'items'}),('checkpoint',{'stage':0,'point':0,'answer':'answer-0'}),('answer',{'stage':0,'answer':'final'})]:
            with self.assertRaises(ContestError) as error:
                self.call(action,**body)
            self.assertEqual(error.exception.code,'contest_hidden')
        self.now=START
        self.assertTrue(self.call('state')['stages'][0]['unlocked'])
        self.assertFalse(self.call('state')['stages'][1]['unlocked'])

if __name__=='__main__':
    import unittest
    unittest.main()
