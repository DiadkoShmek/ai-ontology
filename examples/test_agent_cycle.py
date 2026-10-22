import unittest
import test_durable as fixtures
from agent_cycle import ModelReply, ReplayModel, prepare, run_turn
from durable import Hold, event_operation
from continuity import Event


class CycleTests(unittest.TestCase):
    setUp = fixtures.DurableTests.setUp
    add = fixtures.DurableTests.add
    fixture = fixtures.DurableTests.fixture

    def turn(self, model, expected="authored-replay/1"):
        return run_turn(self.journal, turn_id="turn", branch="main",
            topic="cache-current", scope="updates-A", question="What should we conclude?",
            model=model, expected_model_id=expected)

    def test_cycle_records_bound_request_and_response(self):
        self.fixture()
        result = self.turn(ReplayModel({"text":"The claim is refuted in updates-A",
                                       "stance":"answer", "cites":["c2"]}))
        self.assertEqual(result["semantic_support"], "unverified")
        self.assertEqual(result["receipt"]["seq"], 6)

    def test_profile_and_sources_reach_model_input(self):
        self.fixture()
        ctx, messages = prepare(self.journal,"main","cache-current","updates-A","Explain")
        self.assertIn("disagreement", messages[1]["content"])
        self.assertIn("c2", messages[1]["content"])
        self.assertIn("untrusted DATA", messages[0]["content"])

    def test_model_drift_rejected(self):
        with self.assertRaisesRegex(Hold,"model-route-mismatch"):
            self.turn(ReplayModel({}), "not-this-model")

    def test_adapter_advancing_memory_makes_answer_stale(self):
        outer = self
        class Advancing:
            def complete(self, messages):
                outer.add(event_operation(Event("new","iris","main","observation",
                                                "x","recorded","x","s")))
                return ModelReply("fake/1",'{"text":"x","stance":"abstain","cites":[]}')
        with self.assertRaisesRegex(Hold,"stale-head"):
            self.turn(Advancing(), "fake/1")

    def test_invalid_json_is_not_automatically_repaired(self):
        class Broken:
            def complete(self, messages):
                return ModelReply("fake/1", "not json")
        with self.assertRaisesRegex(Hold,"model-json-invalid"):
            self.turn(Broken(), "fake/1")


