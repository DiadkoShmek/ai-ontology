import copy
import json
import unittest
from tasks import *
from run import prompt,schedule
from participation import interpret,admissible,Hold
from participation_method import reference_method,select_plan

class StudyTests(unittest.TestCase):
    def answer(self,w):
        facts,_=oracle_facts(w);return {'method':reference_method(),**facts,'carry':'checked scope','reason':'bounded public reason'}

    def test_all_gold_are_admitted(self):
        for c in specifications():
            for stage in range(3):
                w=make_world(c,stage);a=self.answer(w)
                self.assertTrue(score(w,a,True)['all_correct']);admissible(w,select_plan(w,a['method'])['plan'])

    def test_common_data_and_response_contract(self):
        w=make_world(specifications()[0],1)
        a,b=prompt(w,ARMS[0],[]),prompt(w,ARMS[1],[])
        for text in [a,b]:self.assertTrue(text.startswith(RULES))
        pa=json.loads(a[len(RULES):]);pb=json.loads(b[len(RULES):]);extra=pb.pop('prepared_relation_view');self.assertEqual(pa,pb);self.assertEqual(extra,interpret(w))
        self.assertNotIn('optimal',json.dumps(extra))

    def test_exact_shape_and_duplicate_keys(self):
        w=make_world(specifications()[0],0);a=self.answer(w)
        self.assertEqual(parse(json.dumps(a)),a)
        self.assertIsNone(parse('{"plan":[],"plan":[]}'))
        a['extra']='x';self.assertIsNone(parse(json.dumps(a)))

    def test_refusal_not_success(self):
        w=make_world(specifications()[0],0);a=self.answer(w);a['method']={'default':'deny','rules':[]}
        s=score(w,a,True);self.assertTrue(s['safe']);self.assertFalse(s['optimal_plan']);self.assertTrue(s['excess_abstention'])

    def test_correct_plan_wrong_criterion_not_complete(self):
        w=make_world(specifications()[0],0);a=self.answer(w);a['current_criterion']='criterion-new'
        self.assertFalse(score(w,a,True)['all_correct'])

    def test_no_effect_means_no_own_feedback(self):
        c=specifications()[0];a=make_world(c,1,[])
        self.assertFalse(any(x['id'].startswith('delivery-own') for x in a['deliveries']))
        self.assertEqual(oracle_facts(a)[0]['own_effects'],[])

    def test_transfer_changes_scope_and_permits_no_blind_contact_rule(self):
        c=next(x for x in specifications() if x['family']=='privacy');a,b=make_world(c,1),make_world(c,2)
        self.assertNotEqual(a['scope'],b['scope'])
        ma={p['recipient']:p['allowed'] for p in a['permissions'] if p['channel']=='mail'}
        mb={p['recipient']:p['allowed'] for p in b['permissions'] if p['channel']=='mail'}
        self.assertTrue(any(ma[p]!=mb[p] for p in ma))

    def test_nonstandard_and_oversized_output_rejected(self):
        w=make_world(specifications()[0],0);a=self.answer(w)
        a['assessments']['criterion-old']=float('nan');self.assertIsNone(parse(json.dumps(a)))
        a=self.answer(w);a['carry']='\ud800';self.assertIsNone(parse(json.dumps(a)))
        a=self.answer(w);a['affected']=['x'*70000];self.assertIsNone(parse(json.dumps(a)))

    def test_initial_worlds_are_not_repeated_by_family(self):
        worlds=[json.dumps(make_world(c,0),sort_keys=True) for c in specifications()]
        self.assertEqual(len(set(worlds)),8)

    def test_schedule_exact(self):
        self.assertEqual(len(schedule()),16);self.assertEqual(len({tuple(x) for x in schedule()}),16)

if __name__=='__main__':unittest.main()
