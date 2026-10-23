"""Frozen pre-inference instrument checks; no model calls."""
import hashlib
import json
import unittest

from run import (CAPACITY, PIN_BYTES, brute, field, receiver_prompt, recursive,
                 score, sources, stored_note)
from transport import pack_history, unpack_history


class StudyTest(unittest.TestCase):
    def test_all_new_sources_have_agreeing_solvers(self):
        for case in sources():
            left, right = brute(case), recursive(case)
            self.assertEqual({k:left[k] for k in right}, right)
            self.assertGreater(left["value"], 0)

    def test_full_exact_delivery_inside_same_total_budget(self):
        for case in sources():
            wire = pack_history(case["history"], stream="fixture-source", branch="main",
                                scope=case["scope"], capacity=CAPACITY-PIN_BYTES)
            pin = hashlib.sha256(wire).hexdigest()
            self.assertLessEqual(len(wire)+len(pin), CAPACITY)
            body = unpack_history(wire, expected_sha256=pin, branch="main", scope=case["scope"],
                                  capacity=CAPACITY-PIN_BYTES)
            self.assertEqual(body["history"], case["history"])
            self.assertEqual(receiver_prompt({**case,"history":body["history"]}, full=True),
                             receiver_prompt(case, full=True))

    def test_primary_requires_actual_plan_and_exact_evidence(self):
        for case in sources():
            truth = brute(case); plan = truth["plans"][0]
            answer = {"plan":plan, "evidence":{n:truth["closure"][n] for n in plan}, "reason":"fixture"}
            self.assertTrue(score(case, json.dumps(answer), True)["optimal"])
            answer["evidence"] = {}
            self.assertFalse(score(case, json.dumps(answer), True)["optimal"])
            answer = {"plan":[], "evidence":{}, "reason":"The optimum is "+str(plan)}
            self.assertFalse(score(case, json.dumps(answer), True)["optimal"])

    def test_common_semantic_state_can_have_different_future_answers(self):
        values = sources()
        for i in range(0, len(values), 2):
            self.assertNotEqual(brute(values[i])["plans"], brute(values[i+1])["plans"])

    def test_no_success_for_nonterminal_or_malformed_sender(self):
        for row in ({"terminal":False,"response":'{"handoff":"x"}'},
                    {"terminal":True,"response":'{"handoff":"x","handoff":"y"}'},
                    {"terminal":True,"response":'{"handoff":3}'}):
            self.assertIsNone(field(row))

    def test_prefix_is_actual_utf8_channel_not_semantic_repair(self):
        note, truncated = stored_note("я"*2000, CAPACITY)
        self.assertTrue(truncated)
        self.assertEqual(len(note.encode()), CAPACITY)
        self.assertEqual(note, "я"*1600)


if __name__ == "__main__":
    unittest.main()
