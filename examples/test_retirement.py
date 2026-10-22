from dataclasses import asdict
import unittest
import test_durable as fixtures
from continuity import Event, read_fixture
from durable import Hold, digest, event_operation, operation


class RetirementTests(unittest.TestCase):
    setUp = fixtures.DurableTests.setUp
    add = fixtures.DurableTests.add
    fixture = fixtures.DurableTests.fixture
    decision = fixtures.DurableTests.decision

    def retire(self, event):
        return operation("retire-"+event.id, "retire", event.branch,
                         event_id=event.id, event_sha256=digest(asdict(event)),
                         reason="source withdrawn by its operator")

    def test_current_basis_retires_to_needs_review(self):
        for e in read_fixture()[:2]:self.add(event_operation(e))
        self.add(self.retire(read_fixture()[0]))
        ctx=self.journal.context("main","cache-current","updates-A")
        self.assertEqual(ctx["view"]["status"],"needs-review")
        self.assertEqual(ctx["view"]["recorded_status"],"hypothesis")
        self.assertIn("c1", self.journal.read()[0]["main"][0].events)

    def test_historical_basis_does_not_invalidate_new_independent_basis(self):
        self.fixture()
        self.add(self.retire(read_fixture()[0]))
        self.assertEqual(self.journal.context("main","cache-current","updates-A")["view"]["status"],"refuted")

    def test_retirement_requires_exact_source_hash(self):
        self.add(event_operation(read_fixture()[0]))
        op=self.retire(read_fixture()[0]);op["data"]["event_sha256"]="0"*64
        with self.assertRaisesRegex(Hold,"retirement-source-mismatch"):self.add(op)

    def test_retirement_is_branch_local_and_survives_reopen(self):
        self.fixture()
        self.add(operation("fork","fork","review",**{"from":"main"}))
        self.add(self.retire(read_fixture()[2]))
        from durable import Journal
        j=Journal(self.path)
        self.assertEqual(j.context("main","cache-current","updates-A")["view"]["status"],"needs-review")
        self.assertEqual(j.context("review","cache-current","updates-A")["view"]["status"],"refuted")

    def test_answer_disposition_rejected_with_retired_basis(self):
        self.fixture();self.add(self.retire(read_fixture()[2]))
        ctx=self.journal.context("main","cache-current","updates-A")
        with self.assertRaisesRegex(Hold,"retired-basis-needs-review"):
            self.add(self.decision(ctx))

    def test_abstention_can_record_the_gap(self):
        self.fixture();self.add(self.retire(read_fixture()[2]))
        ctx=self.journal.context("main","cache-current","updates-A")
        op=self.decision(ctx);op["data"]["response"]["stance"]="abstain"
        self.add(op)

    def test_new_independent_evidence_can_restore_current_claim(self):
        self.fixture();self.add(self.retire(read_fixture()[2]))
        self.add(event_operation(Event("o3","iris","main","observation","cache-current","recorded","Fresh independent test","updates-A")))
        self.add(event_operation(Event("c3","iris","main","claim","cache-current","supported","Fresh result","updates-A",("o3",),"c2")))
        self.assertEqual(self.journal.context("main","cache-current","updates-A")["view"]["status"],"supported")
