import json
from pathlib import Path
import unittest
from design import ARMS, make_cases, oracle, prompt, score


class ParticipationDesignTests(unittest.TestCase):
    def test_manual_answers_agree_with_separate_state_oracle(self):
        cases = make_cases()
        self.assertEqual(len(cases), 16)
        self.assertEqual(sum(len(c['stages']) for c in cases), 34)
        for case in cases:
            self.assertEqual(case['expected_choices'], [oracle(s) for s in case['stages']])

    def test_first_choices_distinguish_counterfactual_profiles(self):
        cases = make_cases()
        for i in range(0, len(cases), 2):
            self.assertNotEqual(cases[i]['expected_choices'][0], cases[i+1]['expected_choices'][0])
            self.assertEqual(cases[i]['stages'][0]['actions'], cases[i+1]['stages'][0]['actions'])

    def test_same_facts_and_no_gold_in_each_condition(self):
        for case in make_cases():
            for stage in case['stages']:
                bodies = [json.loads(prompt(stage, arm, 'method')['content']) for arm in ARMS]
                self.assertEqual(bodies[0]['situation'], bodies[1]['situation'])
                self.assertNotIn('expected_choices', str(bodies))
                self.assertNotIn('method_reading', bodies[0])

    def test_rejects_duplicate_or_unavailable_choice_shape(self):
        self.assertFalse(score('{"choice":"A","choice":"B","reason":"x"}', 'A')['shape'])
        self.assertFalse(score('{"choice":"C","reason":"x"}', 'A')['shape'])
        self.assertTrue(score('{"choice":"ASK","reason":"source missing"}', 'ASK')['correct'])


if __name__ == '__main__':
    unittest.main()
