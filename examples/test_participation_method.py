import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import json
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/closed_loop'))
from tasks import make_world,specifications,optimum
from participation import ParticipationStore,Hold,admissible,interpret
from participation_method import *

class MethodTests(unittest.TestCase):
    def test_shared_planner_vs_independent_oracles(self):
        for c in specifications():
            for stage in range(3):
                w=make_world(c,stage);p=select_plan(w,reference_method())
                self.assertEqual(p['plan'],optimum(w)['plan']);admissible(w,p['plan'])

    def test_wrong_methods_are_representable_and_not_gold_filtered(self):
        w=make_world(specifications()[0],0)
        p=select_plan(w,{'default':'allow','rules':[]})
        self.assertTrue(p['plan'])
        with self.assertRaises(Hold):admissible(w,p['plan'])
        self.assertEqual(select_plan(w,{'default':'deny','rules':[]})['plan'],[])

    def test_predicate_refuses_nondecision_repair_target(self):
        w=make_world(specifications()[0],1)
        bad_claim=next(x['id'] for x in w['records'] if x['kind']=='claim' and x['id'] in interpret(w)['withdrawal_paths'])
        c=next(c for c in w['candidates'] if c['kind']=='quarantine');c['target']=bad_claim;c['benefit']=99
        self.assertFalse(predicate_rows(w)[c['id']]['target_affected'])
        self.assertNotIn(c['id'],select_plan(w,reference_method())['plan'])

    def test_transfer_detects_replacement_instead_of_revision(self):
        from tasks import transfer_cases
        m=reference_method();publish={'default':'deny','rules':[m['rules'][0]]};repair={'default':'deny','rules':m['rules'][1:]}
        retention=[t for t in transfer_cases() if t['variant']=='retention']
        self.assertEqual(len(retention),8)
        for t in retention:
            self.assertEqual(select_plan(t['world'],publish)['plan'],optimum(t['world'])['plan'])
            self.assertEqual(select_plan(t['world'],repair)['plan'],[])
            self.assertGreater(optimum(t['world'])['benefit'],0)
        for t in transfer_cases():
            self.assertEqual(select_plan(t['world'],m)['plan'],optimum(t['world'])['plan'])

    def test_large_raw_rejection_is_explicit_and_durable(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.sqlite';j=ParticipationStore(p,create=True);w=make_world(specifications()[0],0);_,tail=j.read()
            r=j.record_turn('turn-0',w,None,response='x'*70000,terminal=True,expected=tail['head'])
            self.assertFalse(r['committed']);prior,effects,_=ParticipationStore(p).context()
            marker=json.loads(prior[0]['response']);self.assertEqual(marker['raw_bytes'],70000)
            self.assertEqual(marker['continuity_delivery'],'not-delivered');self.assertEqual(effects,[])

    def test_first_matching_rule_and_typed_bool(self):
        m={'default':'deny','rules':[{'all':[],'decision':'allow'},{'all':[],'decision':'deny'}]}
        self.assertTrue(allows(m,{}))
        m['rules'][0]['all']=[{'field':'channel_allowed','equals':1}]
        with self.assertRaises(Hold):validate_method(m)

    def test_no_arbitrary_field_or_code(self):
        for field in ['__import__','world.permissions','__class__']:
            with self.assertRaises(Hold):validate_method({'default':'deny','rules':[{'all':[{'field':field,'equals':True}],'decision':'allow'}]})

    def test_real_feedback_and_fresh_process_context(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.sqlite';j=ParticipationStore(p,create=True);w=make_world(specifications()[0],0);plan=select_plan(w,reference_method())['plan'];_,tail=j.read()
            r=j.record_turn('turn-0',w,{'plan':plan},response='actual',terminal=True,expected=tail['head'])
            code='import json,sys;from participation import ParticipationStore; print(json.dumps(ParticipationStore(sys.argv[1]).context()))'
            run=subprocess.run([sys.executable,'-c',code,str(p)],cwd=Path(__file__).parent,capture_output=True,text=True,check=True)
            prev,effects,tail=json.loads(run.stdout);self.assertEqual(prev[0]['response'],'actual');self.assertEqual(effects,r['effects'])
            self.assertTrue(effects)
            with self.assertRaises(Hold):j.record_turn('turn-1',w,{'plan':plan},response='new',terminal=True,expected=tail['head'])

    def test_rejected_attempt_is_durable_without_effects(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.sqlite';j=ParticipationStore(p,create=True);w=make_world(specifications()[0],0);_,t=j.read()
            r=j.record_turn('turn-0',w,None,response='not-json',terminal=True,expected=t['head'])
            self.assertFalse(r['committed']);prev,effects,_=ParticipationStore(p).context();self.assertEqual(effects,[]);self.assertEqual(prev[0]['response'],'not-json')

    def test_actual_publication_creates_new_remediation(self):
        from tasks import oracle_facts
        c=specifications()[0];w=make_world(c,0);rows=admissible(w,optimum(w)['plan'])
        effects=[{'effect_id':x['effect_id'],'actor':w['actor'],'kind':x['kind'],'target':x['target'],'recipient':x['recipient'],'scope':w['scope'],'plan_id':'turn-0'} for x in rows]
        a,b=make_world(c,1,[]),make_world(c,1,effects)
        _,ea=oracle_facts(a);_,eb=oracle_facts(b)
        self.assertNotEqual({x['id'] for x in ea},{x['id'] for x in eb})

if __name__=='__main__':unittest.main()
