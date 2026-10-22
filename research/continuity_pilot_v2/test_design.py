import json
from pathlib import Path
import unittest
from design import ARMS,make_cases,material,messages,score


class DesignTests(unittest.TestCase):
    def test_all_manual_answers_agree_with_transition_contract(self):
        for c in make_cases():material(c)

    def test_committed_cases_equal_generator(self):
        self.assertEqual(json.loads(Path(__file__).with_name('cases.json').read_text()),make_cases())

    def test_compiled_and_indexed_have_same_substantive_information(self):
        for case in make_cases():
            c=json.loads(messages(case,'compiled')[1]['content'])['continuity_context']
            d=json.loads(messages(case,'simple_index')[1]['content'])['indexed_record']
            renamed={('profile' if k=='settings' else 'view' if k=='current_record' else 'evidence' if k=='records' else k):v for k,v in d.items()}
            self.assertEqual(c,renamed)

    def test_duplicate_keys_and_extra_fields_fail(self):
        gold=make_cases()[0]['gold']
        self.assertFalse(score('{"status":"x","status":"y"}',gold)['exact'])
        self.assertFalse(score(json.dumps({**gold,'extra':True}),gold)['exact'])

    def test_order_normalized_but_duplicate_citations_fail(self):
        gold=make_cases()[0]['gold']
        self.assertTrue(score(json.dumps({**gold,'cites':list(reversed(gold['cites']))}),gold)['exact'])
        self.assertFalse(score(json.dumps({**gold,'cites':gold['cites']*2}),gold)['exact'])


if __name__=='__main__':unittest.main()
