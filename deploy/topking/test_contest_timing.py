from test_contest_checkpoints import CheckpointTests
from contest_runtime import START

class TimingTests(CheckpointTests):
    def finish(self,stage):
        for point in range(3):self.call('checkpoint',stage=stage,point=point,answer=f'answer-{point}')
        self.call('answer',stage=stage,answer='final')
    def test_waiting_is_excluded_and_reload_cannot_reset(self):
        self.now=START+600;self.finish(0)
        state=self.call('state');self.assertEqual(state['timings'][0]['elapsed_ms'],600000)
        self.now=START+1800+180;self.finish(1)
        self.now=START+3600+1200+7;self.finish(2)
        state=self.call('state')
        self.assertEqual([t['elapsed_ms'] for t in state['timings']],[600000,180000,1207000])
        self.assertEqual(state['speed_leaderboard'][0]['elapsed_ms'],1987000)
        self.now+=500;self.assertEqual(self.call('state')['speed_leaderboard'][0]['elapsed_ms'],1987000)
    def test_late_previous_stage_starts_next_when_completed(self):
        self.now=START+2100;self.finish(0)
        self.now+=180;self.finish(1)
        self.assertEqual(self.call('state')['timings'][1]['elapsed_ms'],180000)
