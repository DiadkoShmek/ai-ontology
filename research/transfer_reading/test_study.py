import copy
import json
import unittest
from study import (ARMS,field,held_cases,planning_success,prime_prompt,schedule,
                   score,sha,stored_note,brute)


class ReadingStudyTest(unittest.TestCase):
    def test_fixed_coverage_and_schedule_roundtrip(self):
        self.assertEqual(len(held_cases()),8)
        self.assertEqual(len(schedule()),64)
        self.assertEqual(len({tuple(x) for x in schedule()}),64)
        self.assertEqual(json.loads(json.dumps(schedule())),schedule())
        for arm in ARMS:self.assertEqual(sum(x[1]==arm for x in schedule()),16)

    def test_priming_has_no_future_task_or_gold(self):
        prompt=prime_prompt('authored reading fixture')
        for c in held_cases():
            self.assertNotIn(c['id'],prompt)
            self.assertNotIn(c['scope'],prompt)
            self.assertNotIn(c['new_operation']['data']['event_id'],prompt)

    def test_actual_fields_not_repaired(self):
        self.assertEqual(field({'terminal':True,'response':'{"approach":"actual"}'},'approach'),'actual')
        for raw in ('{"approach":"a","approach":"b"}','```json\n{"approach":"a"}\n```','{"wrong":"a"}'):
            self.assertIsNone(field({'terminal':True,'response':raw},'approach'))
        self.assertIsNone(field({'terminal':False,'response':'{"approach":"actual"}'},'approach'))

    def test_primary_and_audit_outcomes_are_separate(self):
        for c in held_cases():
            truth=brute(c);answer={'plan':truth['plans'][0],'evidence':{},'reason':'oracle fixture'}
            judged=score(c,json.dumps(answer),True)
            self.assertTrue(planning_success(judged,c))
            self.assertFalse(judged['traceable'])

    def test_storage_uses_the_actual_draft_prefix(self):
        for limit in (1,2,3,700,3200):
            text='відношення '+('evidence:1234567890 '*300)
            note,cut=stored_note(text,limit)
            self.assertTrue(text.startswith(note))
            self.assertLessEqual(len(note.encode()),limit)
            self.assertEqual(cut,len(text.encode())>limit)


if __name__=='__main__':unittest.main()
