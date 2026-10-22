import copy
import json
import unittest
from design import ARMS,cases,evaluate,target_prompt


class DesignTest(unittest.TestCase):
    def test_schedule_survives_json_freeze(self):
        from run import schedule
        self.assertEqual(json.loads(json.dumps(schedule())),schedule())

    def test_counts_and_gold_not_in_prompt(self):
        data=cases()
        self.assertEqual(len(data),20)
        self.assertEqual(sum(len(c['stages']) for c in data)*2,100)
        for c in data:
            for arm in ARMS:
                p=target_prompt(c,arm,0,[],'SHORT','LONG')
                self.assertNotIn('expected_choices',p)
                self.assertNotIn('"expected":',p)
                self.assertNotIn('future stage',p)

    def test_coupled_keys_and_available_gold(self):
        for c in cases():
            if c['kind']!='coupled':continue
            for i,g in enumerate(c['expected']):
                self.assertEqual(set(g['record']),set(c['stages'][i]['question']))
                self.assertTrue(c['stages'][i]['actions'][g['action']]['available'])
                raw=json.dumps({**g,'reason':'fixture'})
                self.assertTrue(evaluate(c,i,raw,True)['correct'])
                self.assertFalse(evaluate(c,i,raw,False)['correct'])
                for key in g['record']:
                    changed=copy.deepcopy(g);changed['record'][key]='wrong'
                    self.assertFalse(evaluate(c,i,json.dumps({**changed,'reason':'fixture'}),True)['correct'])

    def test_history_loss_actually_drops_source(self):
        c=next(c for c in cases() if c['id']=='history_loss-learning')
        p=target_prompt(c,'plain_profile',1,[{'response':'{"choice":"B","reason":"earlier"}','effect':{}}],'SHORT','LONG')
        self.assertNotIn('"criterion": "learning"',p)
        self.assertNotIn('Choose the next bounded experiment',p)
        self.assertIn('earlier',p)

    def test_duplicate_keys_rejected(self):
        c=next(c for c in cases() if c['kind']=='coupled')
        self.assertFalse(evaluate(c,0,'{"action":"A","action":"B","record":{},"reason":"x"}',True)['shape'])


if __name__=='__main__':unittest.main()
