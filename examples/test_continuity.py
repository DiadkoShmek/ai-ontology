import unittest
from dataclasses import replace
from continuity import Conflict, Event, apply, empty, fork, knowledge, read_fixture, render, replay


class ContinuityContract(unittest.TestCase):
    def setUp(self):
        self.events = read_fixture()
        self.before = replay(empty(), self.events[:2])
        self.after = replay(self.before, self.events[2:])

    def test_revision_preserves_history_and_commitments(self):
        self.assertEqual(knowledge(self.before, "cache-current", "updates-A")["status"], "hypothesis")
        self.assertEqual(knowledge(self.after, "cache-current", "updates-A")["status"], "refuted")
        self.assertEqual(self.after.events["c1"], self.before.events["c1"])
        self.assertEqual(self.before.commitments, self.after.commitments)

    def test_exact_delivery_repeat_is_idempotent(self):
        self.assertEqual(replay(self.after, self.events), self.after)

    def test_collision_cannot_replace_history(self):
        with self.assertRaisesRegex(Conflict, "event-id-collision"):
            apply(self.after, replace(self.events[0], text="other"))

    def test_forward_reference_is_not_silently_accepted(self):
        with self.assertRaisesRegex(Conflict, "missing-basis"):
            replay(empty(), (self.events[1], self.events[0]))

    def test_missing_history_stays_unknown(self):
        self.assertEqual(knowledge(empty(), "cache-current", "updates-A")["status"], "unknown")

    def test_scope_does_not_silently_generalize(self):
        self.assertEqual(knowledge(self.after, "cache-current", "other-corpus")["status"], "unknown")

    def test_fork_knows_inherited_origin(self):
        branch = fork(self.after, "review", "snapshot-1")
        v = knowledge(branch, "cache-current", "updates-A")
        self.assertEqual((v["recorded_in_branch"], v["current_branch"]), ("main", "review"))

    def test_new_branch_event_does_not_reach_sibling(self):
        a = fork(self.after, "A", "snapshot-1")
        b = fork(self.after, "B", "snapshot-1")
        newer = replace(self.events[2], id="o3", branch="A")
        changed = apply(a, newer)
        self.assertIn("o3", changed.events)
        self.assertNotIn("o3", b.events)
        self.assertNotIn("o3", self.after.events)

    def test_wrong_actor_or_branch_rejected(self):
        for event in (replace(self.events[2], actor="orion"), replace(self.events[2], branch="elsewhere")):
            with self.subTest(event=event), self.assertRaisesRegex(Conflict, "wrong-actor-or-branch"):
                apply(self.before, event)

    def test_conflicting_head_requires_explicit_revision(self):
        with self.assertRaisesRegex(Conflict, "explicit-revision-required"):
            apply(self.after, replace(self.events[1], id="c3"))

    def test_stale_predecessor_cannot_overwrite_new_head(self):
        with self.assertRaisesRegex(Conflict, "stale-predecessor"):
            apply(self.after, replace(self.events[3], id="c3"))

    def test_revision_cannot_change_topic_or_scope(self):
        for event in (replace(self.events[3], topic="other"), replace(self.events[3], scope="other")):
            with self.subTest(event=event), self.assertRaisesRegex(Conflict, "revision-changed-subject"):
                apply(apply(self.before, self.events[2]), event)

    def test_failed_batch_leaves_caller_unchanged(self):
        original = dict(self.before.events)
        with self.assertRaises(Conflict):
            replay(self.before, (self.events[2], replace(self.events[3], basis=("absent",))))
        self.assertEqual(dict(self.before.events), original)
        self.assertNotIn("o2", self.before.events)

    def test_fixed_voice_rendering_preserves_status_text(self):
        for status in ("hypothesis", "supported", "refuted", "unknown"):
            view = {"status": status, "text": "тест", "basis": []}
            self.assertTrue(render(view, "warm").endswith(render(view, "brief")))

    def test_invalid_status_and_missing_basis_refused(self):
        for event in (replace(self.events[1], status="certain"), replace(self.events[1], basis=())):
            with self.subTest(event=event), self.assertRaises(Conflict):
                replay(empty(), (self.events[0], event))

    def test_structural_validity_does_not_check_entailment(self):
        # Negative capability: the fixture's existing observation need not
        # support arbitrary prose. Passing shape checks cannot prove truth.
        arbitrary = replace(self.events[1], text="усі числа парні", status="supported")
        state = replay(empty(), (self.events[0], arbitrary))
        self.assertEqual(knowledge(state, arbitrary.topic, arbitrary.scope)["status"], "supported")

    def test_malformed_event_is_typed_conflict(self):
        for event in (None, replace(self.events[0], id=[]), replace(self.events[1], basis=([],)),
                      replace(self.events[1], basis=("o1", "o1")), replace(self.events[1], revises=[])):
            with self.subTest(event=event), self.assertRaises(Conflict):
                apply(self.before, event)

    def test_lossy_summary_cannot_distinguish_two_histories(self):
        histories = ({"staging": True, "production": False}, {"staging": False, "production": True})
        summaries = ["one environment awaits a test" for _ in histories]
        self.assertEqual(summaries[0], summaries[1])
        self.assertNotEqual(histories[0]["staging"], histories[1]["staging"])
        # Any Boolean deterministic answer keyed only by that summary fails
        # one of these two incompatible authored cases.
        for answer in (True, False):
            self.assertEqual(sum(answer == h["staging"] for h in histories), 1)


if __name__ == "__main__":
    unittest.main()
