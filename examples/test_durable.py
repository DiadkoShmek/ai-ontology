"""Adversarial runtime tests, not trials of LLM behavior."""
from dataclasses import asdict, replace
import copy
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from continuity import Event, knowledge, read_fixture
from durable import (DEFAULT, ZERO, Hold, Journal, canonical, digest,
                     event_operation, operation)

HERE = str(Path(__file__).parent)


class DurableTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "state.sqlite"
        self.journal = Journal(self.path, create=True)
        self.head = self.journal.append(operation("genesis", "init", actor="iris",
            orientation=DEFAULT), expected=ZERO)["head"]

    def add(self, op):
        result = self.journal.append(op, expected=self.head)
        self.head = result["head"]
        return result

    def fixture(self):
        for e in read_fixture():
            self.add(event_operation(e))

    def test_new_process_reconstructs_revision_and_orientation(self):
        self.fixture()
        code = ("import json,sys;from durable import Journal;"
                "print(json.dumps(Journal(sys.argv[1]).context('main','cache-current','updates-A')))" )
        result = subprocess.run([sys.executable, "-c", code, str(self.path)],
                                cwd=HERE, capture_output=True, text=True, timeout=10, check=True)
        ctx = json.loads(result.stdout)
        self.assertEqual(ctx["view"]["status"], "refuted")
        self.assertEqual({e["id"] for e in ctx["evidence"]}, {"o1", "c1", "o2", "c2"})
        self.assertEqual(ctx["profile"], DEFAULT)

    def test_parallel_processes_have_exactly_one_winner(self):
        code = """import sys
from durable import Journal,operation,Hold
from continuity import Event
from durable import event_operation
j=Journal(sys.argv[1]);e=Event(sys.argv[3],'iris','main','observation','race','recorded','x','s')
print('ready',flush=True);sys.stdin.readline()
try:j.append(event_operation(e),expected=sys.argv[2]);print('committed')
except Hold as exc:print(str(exc))
"""
        children = [subprocess.Popen([sys.executable, "-u", "-c", code, str(self.path),
                    self.head, "r" + str(n)], cwd=HERE, stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for n in range(2)]
        try:
            for p in children:
                self.assertEqual(p.stdout.readline().strip(), "ready")
            results = [p.communicate("go\n", timeout=10) for p in children]
            self.assertCountEqual([x[0].strip() for x in results], ["committed", "stale-head"])
            self.assertEqual(self.journal.read()[1]["seq"], 2)
        finally:
            for p in children:
                if p.poll() is None:
                    p.kill()
                    p.communicate()

    def test_exact_retry_after_later_event_does_not_duplicate(self):
        a, b = read_fixture()[:2]
        old = self.head
        self.add(event_operation(a))
        last = self.add(event_operation(b))
        self.assertEqual(self.journal.append(event_operation(a), expected=old), last)

    def test_id_collision_rejected(self):
        a = read_fixture()[0]
        self.add(event_operation(a))
        with self.assertRaisesRegex(Hold, "operation-id-collision"):
            self.add(event_operation(replace(a, text="other")))

    def test_invalid_event_transaction_does_not_advance_head(self):
        before = self.journal.read()[1]
        with self.assertRaises(Hold):
            self.add(event_operation(read_fixture()[1]))
        self.assertEqual(before, self.journal.read()[1])

    def test_process_death_with_uncommitted_insert_rolls_back(self):
        code = """import os,sqlite3,sys
db=sqlite3.connect(sys.argv[1]);db.execute('BEGIN IMMEDIATE')
db.execute('INSERT INTO journal VALUES (2,?,?)',(b'partial','bad'))
os._exit(17)
"""
        p = subprocess.run([sys.executable, "-c", code, str(self.path)], timeout=10)
        self.assertEqual(p.returncode, 17)
        self.assertEqual(self.journal.read()[1]["seq"], 1)

    def test_tampered_bytes_rejected(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            raw = db.execute("SELECT raw FROM journal").fetchone()[0]
            op = json.loads(raw)
            op["data"]["actor"] = "other"
            db.execute("UPDATE journal SET raw=?", (canonical(op),))
        with self.assertRaisesRegex(Hold, "journal-hash-mismatch"):
            self.journal.read()

    def test_tail_deletion_requires_anchor_to_detect(self):
        self.fixture()
        _, anchor = self.journal.read()
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("DELETE FROM journal WHERE seq=?", (anchor["seq"],))
        # Valid prefix alone is indistinguishable from an earlier valid store.
        self.assertEqual(self.journal.read()[1]["seq"], anchor["seq"] - 1)
        with self.assertRaisesRegex(Hold, "anchor-mismatch"):
            self.journal.read(anchor=anchor)

    def test_old_anchor_accepts_valid_append(self):
        _, anchor = self.journal.read()
        self.add(event_operation(read_fixture()[0]))
        self.assertEqual(self.journal.read(anchor=anchor)[1]["seq"], 2)

    def test_coherent_rewrite_without_anchor_is_not_authentication(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            op = json.loads(db.execute("SELECT raw FROM journal").fetchone()[0])
            op["data"]["actor"] = "forged"
            stream = db.execute("SELECT id FROM meta").fetchone()[0]
            h = digest({"stream": stream, "seq": 1, "previous": ZERO, "operation": op})
            db.execute("UPDATE journal SET raw=?,hash=?", (canonical(op), h))
        self.assertEqual(self.journal.read()[0]["main"][0].actor, "forged")

    def test_fork_retains_origin_but_no_future_sibling_events(self):
        self.fixture()
        self.add(operation("fork", "fork", "review", **{"from": "main"}))
        self.add(event_operation(Event("future", "iris", "main", "observation",
                                       "other", "recorded", "new", "s")))
        world, _ = self.journal.read()
        self.assertNotIn("future", world["review"][0].events)
        self.assertEqual(world["review"][0].events["c2"].branch, "main")

    def test_changed_profile_needs_explicit_revision(self):
        revised = {**DEFAULT, "purpose": "Investigate and explain to a new audience"}
        self.add(operation("orient", "orient", previous_sha256=digest(DEFAULT),
                           orientation=revised, reason="changed audience", approved_by="operator"))
        self.assertEqual(self.journal.context("main", "x", "s")["profile"], revised)
        with self.assertRaisesRegex(Hold, "stale-orientation"):
            self.add(operation("orient2", "orient", previous_sha256=digest(DEFAULT),
                               orientation=DEFAULT, reason="stale", approved_by="operator"))

    def test_scope_missing_is_unknown(self):
        self.fixture()
        self.assertEqual(self.journal.context("main", "cache-current", "production")["view"]["status"], "unknown")

    def test_budget_failure_is_explicit(self):
        self.fixture()
        with self.assertRaisesRegex(Hold, "required-context-exceeds-budget"):
            self.journal.context("main", "cache-current", "updates-A", budget=512)

    def decision(self, ctx, cites=None, content="Evidence refutes this scoped claim"):
        return operation("answer", "decision", context=ctx, question="What changed?",
                         model={"id":"authored-fixture", "request_sha256":"fixture", "response_sha256":"fixture"},
                         response={"text": content, "stance": "answer", "cites": cites or ["c2"]})

    def test_current_decision_commits(self):
        self.fixture()
        ctx = self.journal.context("main", "cache-current", "updates-A")
        self.add(self.decision(ctx))

    def test_stale_context_rejected_even_if_caller_refreshes_head(self):
        self.fixture()
        ctx = self.journal.context("main", "cache-current", "updates-A")
        self.add(event_operation(Event("new", "iris", "main", "observation", "x", "recorded", "x", "s")))
        with self.assertRaisesRegex(Hold, "stale-or-forged-context"):
            self.add(self.decision(ctx))

    def test_forged_context_rejected(self):
        self.fixture()
        ctx = self.journal.context("main", "cache-current", "updates-A")
        before = self.journal.read()[1]
        for mutation in ("status", "boolean-count", "float-count"):
            with self.subTest(mutation=mutation):
                changed = copy.deepcopy(ctx)
                if mutation == "status":
                    changed["view"]["status"] = "supported"
                    changed["context_sha256"] = "forged"
                else:
                    self.assertEqual(changed["omitted_event_count"], 0)
                    changed["omitted_event_count"] = False if mutation == "boolean-count" else 0.0
                with self.assertRaisesRegex(Hold, "stale-or-forged-context"):
                    self.add(self.decision(changed))
                self.assertEqual(self.journal.read()[1], before)

    def test_unavailable_citation_rejected(self):
        self.fixture()
        ctx = self.journal.context("main", "cache-current", "updates-A")
        with self.assertRaisesRegex(Hold, "citation-outside-context"):
            self.add(self.decision(ctx, ["not-present"]))

    def test_semantically_wrong_prose_can_pass_structural_guard(self):
        self.fixture()
        ctx = self.journal.context("main", "cache-current", "updates-A")
        self.add(self.decision(ctx, content="Every number is even"))


if __name__ == "__main__":
    unittest.main()
