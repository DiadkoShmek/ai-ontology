"""Adversarial contract checks; never model performance evidence."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/closed_loop'))
from tasks import make_world, specifications, oracle_facts, optimum
from participation import Hold, ParticipationStore, admissible, interpret, validate


class ParticipationTests(unittest.TestCase):
    def world(self,stage=1):return make_world(specifications()[0],stage)

    def test_independent_queries_all_interventions(self):
        for spec in specifications():
            for stage in range(3):
                w=make_world(spec,stage);actual=interpret(w);gold,_=oracle_facts(w)
                self.assertEqual(gold['affected'],actual['affected_decisions'])
                self.assertEqual(gold['own_effects'],actual['own_prior_effects'])
                for k in ('current_criterion','assessments','open_objections'):
                    self.assertEqual(gold[k],sorted(actual[k]) if k=='open_objections' else actual[k])
                self.assertEqual(optimum(w),optimum(w,recursive=True))
                admissible(w,optimum(w)['plan'])

    def test_equal_record_ids_at_first_feedback(self):
        s=specifications()[0]
        a,b=make_world(s,0),make_world(s,1)
        self.assertEqual(a['records'],b['records'])

    def test_own_effect_not_peer_delivery(self):
        s=specifications()[0];w=make_world(s,0);c=next(c for c in w['candidates'] if c['target'] in {r['id'] for r in w['records'] if r['scope']==w['scope']})
        h={'effect_id':c['effect_id'],'actor':'builder','kind':c['kind'],'target':c['target'],'recipient':c['recipient'],'scope':w['scope'],'plan_id':'step-0'}
        n=make_world(s,1,[h]);n['withdrawn']=[next(r['id'] for r in n['records'] if r['id']==c['target'])]
        self.assertEqual(interpret(n)['own_prior_effects'],[h['effect_id']])
        n['history'][0]['actor']='peer';self.assertEqual(interpret(n)['own_prior_effects'],[])

    def test_acceptance_is_not_satisfaction(self):
        spec=next(s for s in specifications() if s['family']=='criterion');w=make_world(spec,1)
        v=interpret(w);self.assertEqual(v['current_criterion'],'criterion-new')
        self.assertEqual(v['assessments'],{'criterion-old':'lost','criterion-new':'met'})
        w['criterion_update']['authorized']=False
        self.assertEqual(interpret(w)['current_criterion'],'criterion-old')

    def test_wrong_scope_and_absent_permission_refuse(self):
        w=self.world(0);bad=w['candidates'][-1]['id']
        with self.assertRaises(Hold):admissible(w,[bad])
        good=optimum(w)['plan'];self.assertTrue(good)
        w['permissions']=[]
        with self.assertRaises(Hold):admissible(w,good)

    def test_transitive_withdrawal(self):
        w=self.world();v=interpret(w)
        self.assertTrue(v['withdrawal_paths'])
        self.assertTrue(v['affected_decisions'])
        self.assertEqual(interpret(w),v)

    def test_bad_graph_and_bool_budget(self):
        w=self.world();w['budget']=True
        with self.assertRaises(Hold):validate(w)
        w=self.world();w['records'][0]['basis']=['missing']
        with self.assertRaises(Hold):validate(w)

    def test_stale_commit_no_second_effect(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'loop.sqlite';j=ParticipationStore(p,create=True);w=self.world(0)
            _,tail=j.read();a={'plan':optimum(w)['plan'],'carry':'actual'}
            r=j.commit('turn-one',w,a,expected=tail['head'])
            j=ParticipationStore(p);values,new=j.read();self.assertEqual(len(values),1)
            self.assertEqual(values[0]['effects'],r['effects'])
            with self.assertRaises(Hold):j.commit('turn-two',w,a,expected=tail['head'])
            self.assertEqual(j.read()[0],values)
            again=j.commit('turn-one',w,a,expected=tail['head']);self.assertEqual(again,r)

    def test_no_mutation_of_caller_state(self):
        with tempfile.TemporaryDirectory() as d:
            j=ParticipationStore(Path(d)/'loop.sqlite',create=True);w=self.world(0);before=copy.deepcopy(w)
            _,tail=j.read();j.commit('one',w,{'plan':optimum(w)['plan']},expected=tail['head'])
            self.assertEqual(w,before)


if __name__=='__main__':unittest.main()
