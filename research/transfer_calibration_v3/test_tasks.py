import copy
import json
import unittest
from tasks import (brute,cases,flat_note,planning_success,prime_prompt,recursive,
                   score,stored_note,world_facts)


class TransferOracleTest(unittest.TestCase):
    def test_storage_is_exact_utf8_prefix(self):
        for limit in range(1,30):
            source='Підстава → наступний крок'
            saved,cut=stored_note(source,limit)
            self.assertLessEqual(len(saved.encode()),limit)
            self.assertTrue(source.startswith(saved))
            self.assertEqual(cut,len(source.encode())>limit)

    def test_preparation_precedes_unseen_work(self):
        prompt=prime_prompt()
        self.assertNotIn('new-source-withdrawal',prompt)
        self.assertNotIn('W56',prompt)
        self.assertNotIn('release-1203',prompt)

    def test_primary_does_not_punish_only_citation_copy(self):
        c=cases()[1];truth=brute(c);plan=truth['plans'][0]
        a={'plan':plan,'evidence':{},'reason':'fixture'}
        s=score(c,json.dumps(a),True)
        self.assertTrue(planning_success(s,c))
        self.assertFalse(s['traceable'])

    def test_two_solvers_agree_on_all_materialized_cases(self):
        for case in cases():
            a=brute(case);b=recursive(case)
            self.assertEqual({k:a[k] for k in b},b,case['id'])
            for plan in a['plans']:
                answer={'plan':plan,'evidence':{n:a['closure'][n] for n in plan},'reason':'authored oracle fixture'}
                self.assertTrue(score(case,json.dumps(answer),True)['optimal'])

    def test_counterfactual_relation_is_necessary(self):
        data=cases()
        for a,b in zip(data[::2],data[1::2]):
            self.assertEqual(flat_note(a),flat_note(b))
            self.assertNotEqual(brute(a)['plans'],brute(b)['plans'])
            aa=world_facts(a,False);bb=world_facts(b,False)
            self.assertEqual(aa[0],bb[0])
            differences=sum(x!=y for x,y in zip(a['history'],b['history']))
            self.assertEqual(differences,1)

    def test_all_claims_are_not_invalidated_by_old_basis(self):
        for c in cases():
            before,_,_=world_facts(c,False);after,_,_=world_facts(c)
            self.assertTrue(after<before)
            self.assertTrue(after)

    def test_selected_sources_and_budget_are_enforced(self):
        c=cases()[1];truth=brute(c);plan=truth['plans'][0]
        answer={'plan':plan,'evidence':{n:truth['closure'][n] for n in plan},'reason':'fixture'}
        self.assertFalse(score(c,json.dumps(answer),False)['optimal'])
        broken=copy.deepcopy(answer);broken['evidence'][plan[0]]=[]
        self.assertFalse(score(c,json.dumps(broken),True)['optimal'])
        broken['plan']=list(truth['closure'])
        self.assertFalse(score(c,json.dumps(broken),True)['safe'])


if __name__=='__main__':unittest.main()
