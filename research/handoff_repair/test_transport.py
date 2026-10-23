"""Adversarial transport/replay tests; no LLM calls or live deployment."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "examples"))
from continuity import Event
from durable import DEFAULT, Hold, Journal, ZERO, canonical, digest, event_operation, operation
from transport import (MAX_RAW, context_from_handoff, export_journal,
                     pack_history, unpack_history)


def history():
    obs = Event("o", "iris", "main", "observation", "cache", "recorded",
                "Перевірка завершена — details remain DATA", "release")
    claim = Event("c", "iris", "main", "claim", "cache", "supported",
                  "Authored fixture status", "release", ("o",))
    return [operation("init", "init", actor="iris", orientation=DEFAULT),
            event_operation(obs), event_operation(claim)]


class HandoffTest(unittest.TestCase):
    def setUp(self):
        self.ops = history()
        self.wire = pack_history(self.ops, stream="test", branch="main", scope="release")

    def restore(self, wire=None, **kw):
        wire = self.wire if wire is None else wire
        return unpack_history(wire, expected_sha256=hashlib.sha256(wire).hexdigest(),
                              branch=kw.pop("branch", "main"),
                              scope=kw.pop("scope", "release"), **kw)

    def envelope(self, **changes):
        return canonical({**json.loads(self.wire), **changes})

    def body_wire(self, body):
        raw = canonical(body)
        return canonical({"v": 1, "n": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                          "z85": base64.b85encode(zlib.compress(raw)).decode()})

    def test_exact_unicode_history_and_existing_context(self):
        self.assertEqual(self.restore()["history"], self.ops)
        ctx = context_from_handoff(self.wire, expected_sha256=hashlib.sha256(self.wire).hexdigest(),
                                   branch="main", scope="release", topic="cache")
        self.assertEqual(ctx["view"]["claim"], "c")
        self.assertEqual({e["id"] for e in ctx["evidence"]}, {"o", "c"})

    def test_sqlite_export_and_fresh_process(self):
        with tempfile.TemporaryDirectory() as work:
            journal = Journal(Path(work)/"owned.sqlite", create=True)
            head = ZERO
            for op in self.ops:
                tail = journal.append(op, expected=head)
                head = tail["head"]
            wire, exported = export_journal(journal, branch="main", scope="release")
            self.assertEqual(tail, exported)
            run = subprocess.run([sys.executable, str(Path(__file__).with_name("transport.py")),
                                  "--expected-sha256", hashlib.sha256(wire).hexdigest(),
                                  "--branch", "main", "--scope", "release"],
                                 input=wire, capture_output=True, check=True, timeout=10)
            self.assertEqual(json.loads(run.stdout)["history"], self.ops)
            ctx = context_from_handoff(wire, expected_sha256=hashlib.sha256(wire).hexdigest(),
                                       branch="main", scope="release", topic="cache")
            self.assertEqual(ctx["head"], tail["head"])
            self.assertEqual(journal.read()[1], tail)

    def test_external_pin_and_truncated_transport(self):
        for wire in (self.wire[:-1], self.wire+b" "):
            with self.assertRaises(Hold):
                unpack_history(wire, expected_sha256=hashlib.sha256(self.wire).hexdigest(),
                               branch="main", scope="release")
            with self.assertRaises(Hold):
                self.restore(wire)

    def test_wrong_scope_or_branch(self):
        for kw in ({"scope":"other"}, {"branch":"peer"}):
            with self.assertRaisesRegex(Hold, "target-mismatch"):
                self.restore(**kw)

    def test_bad_sizes_and_codec(self):
        for change in ({"n":True}, {"n":MAX_RAW+1}, {"n":0}, {"v":True},
                       {"v":2}, {"n":json.loads(self.wire)["n"]-1}):
            with self.subTest(change=change), self.assertRaises(Hold):
                self.restore(self.envelope(**change))

    def test_extra_compressed_stream_and_content_hash(self):
        env = json.loads(self.wire)
        compressed = base64.b85decode(env["z85"])+zlib.compress(b"second-stream")
        for change in ({"z85":base64.b85encode(compressed).decode()}, {"sha256":"0"*64}):
            with self.assertRaises(Hold):
                self.restore(self.envelope(**change))

    def test_decompression_bomb_stops_at_declared_bound(self):
        bomb = self.envelope(n=32, z85=base64.b85encode(zlib.compress(b"x"*1000000)).decode())
        with self.assertRaisesRegex(Hold, "incomplete-or-extra"):
            self.restore(bomb)

    def test_duplicate_keys_and_noncanonical_json(self):
        for raw in (self.wire[:-1]+b',"v":1}', b" "+self.wire,
                    self.wire.replace(b'"n":', b'"n":NaN,"discarded":', 1)):
            with self.assertRaises(Hold):
                self.restore(raw)

    def test_rehashed_invalid_history_still_rejected(self):
        body = self.restore()
        for invalid in ([], None, 4):
            with self.assertRaises(Hold):
                self.restore(self.body_wire(invalid))
        for altered in ([*self.ops, self.ops[-1]], [*self.ops[:-1], {"id":"bad"}], []):
            with self.assertRaises(Hold):
                self.restore(self.body_wire({**body, "history":altered}))

    def test_overflow_is_hold_without_silent_truncation(self):
        with self.assertRaisesRegex(Hold, "exceeds-capacity"):
            pack_history(self.ops, stream="test", branch="main", scope="release", capacity=256)
        for cap in (True, 0, 65537):
            with self.assertRaises(Hold):
                pack_history(self.ops, stream="test", branch="main", scope="release", capacity=cap)

    def test_retirement_and_revision_survive(self):
        target = self.ops[1]["data"]
        retired = operation("retire", "retire", event_id="o", event_sha256=digest(target), reason="fixture withdrawn")
        wire = pack_history([*self.ops, retired], stream="test", branch="main", scope="release")
        ctx = context_from_handoff(wire, expected_sha256=hashlib.sha256(wire).hexdigest(),
                                   branch="main", scope="release", topic="cache")
        self.assertEqual(ctx["view"]["status"], "needs-review")


if __name__ == "__main__":
    unittest.main()
