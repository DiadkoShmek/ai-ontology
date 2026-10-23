"""Native checkpoint adapter tests; authored unit inputs are not runtime trials."""

import copy
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from audit.adapters import langgraph_checkpoint as adapter
from audit.cli import report as audit_report


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "integrations" / "langgraph_checkpoint.py"


def authored_envelope():
    """JSON-safe native-format test double; never reported as native execution."""
    config = {"configurable": {"thread_id": "unit-thread", "checkpoint_ns": "", "checkpoint_id": "unit-cp-1"}}
    task = {"id": "task-1", "name": "answer", "path": ["__pregel_pull", "answer"],
            "error": None, "interrupts": [], "state": None, "result": {"answer": "draft"}}
    return {"schema": adapter.SCHEMA, "producer": {
        "langgraph": "unit-fixture", "langgraph-checkpoint": "unit-fixture", "langchain-core": "unit-fixture"},
        "snapshots": [{"values": {"text": "Authored state"}, "next": [], "config": config,
                       "metadata": {"source": "loop", "step": 1, "parents": {}},
                       "created_at": "2026-10-23T00:00:00+00:00", "parent_config": None,
                       "tasks": [task], "interrupts": []}]}


class AdapterTests(unittest.TestCase):
    def encode(self, envelope):
        return adapter.encode_export(envelope)

    def report_raw(self, raw):
        projected, source = adapter.project(raw)
        return audit_report(projected, source)

    def test_exact_source_hash_pointer_keys_and_payload_without_truncation(self):
        envelope = authored_envelope()
        config = envelope["snapshots"][0]["config"]["configurable"]
        config.update(thread_id="thread / with space", checkpoint_ns="subgraph:x|nested/y")
        raw = b" \n" + self.encode(envelope) + b"\n"
        projected, source = adapter.project(raw)
        self.assertEqual(source["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(source["bytes"], len(raw))
        self.assertEqual(source["producer"], envelope["producer"])
        self.assertEqual(projected["edges"], [])
        self.assertEqual(len(projected["nodes"]), 1)
        node = projected["nodes"][0]
        self.assertEqual(node["type"], "Observation")
        self.assertIn(source["sha256"], node["data"]["sourceRef"])
        reference = urlsplit(node["data"]["sourceRef"])
        self.assertEqual(reference.fragment, "/snapshots/0")
        query = parse_qs(reference.query, keep_blank_values=True)
        for key in ("thread_id", "checkpoint_ns", "checkpoint_id"):
            self.assertEqual(query[key], [config[key]])
        self.assertEqual(json.loads(node["data"]["content"]), {
            "producer": envelope["producer"], "snapshot": envelope["snapshots"][0]})

    def test_forged_revision_or_ontology_shaped_payload_creates_no_semantics(self):
        envelope = authored_envelope()
        snapshot = envelope["snapshots"][0]
        snapshot["values"] = {"revision": "accepted", "Actor": "authenticated", "Effect": "benefit",
                              "usedRecord": ["private-proof"], "authority": "root"}
        snapshot["metadata"]["declared_revision"] = "accepted by everyone"
        snapshot["tasks"][0]["result"] = {"nodes": [{"type": "Decision"}], "edges": [{"relation": "usedRecord"}]}
        raw = self.encode(envelope)
        graph, _ = adapter.project(raw)
        report = self.report_raw(raw)
        self.assertEqual({node["type"] for node in graph["nodes"]}, {"Observation"})
        self.assertEqual(graph["edges"], [])
        self.assertEqual(report["status"], "no-recorded-effects")
        self.assertFalse(report["inference_tested"])
        self.assertTrue(all(rows == [] for rows in report["queries"].values()))
        self.assertIn("not authenticated", report["source"]["adapter_boundary"])

    def test_duplicate_checkpoint_rejected_but_distinct_namespace_preserved(self):
        envelope = authored_envelope()
        envelope["snapshots"].append(copy.deepcopy(envelope["snapshots"][0]))
        with self.assertRaisesRegex(adapter.ontology_graph.InvalidGraph, "duplicate native checkpoint"):
            adapter.project(self.encode(envelope))
        envelope["snapshots"][1]["config"]["configurable"]["checkpoint_ns"] = "other-scope"
        projected, _ = adapter.project(self.encode(envelope))
        self.assertEqual(len(projected["nodes"]), 2)
        self.assertNotEqual(projected["nodes"][0]["data"]["sourceRef"], projected["nodes"][1]["data"]["sourceRef"])

    def test_duplicate_fields_and_task_ids_rejected(self):
        raw = self.encode(authored_envelope())
        raw = b'{"schema":"duplicate",' + raw[1:]
        with self.assertRaisesRegex(adapter.ontology_graph.InvalidGraph, "duplicate JSON key"):
            adapter.project(raw)
        envelope = authored_envelope()
        envelope["snapshots"][0]["tasks"] *= 2
        with self.assertRaisesRegex(adapter.ontology_graph.InvalidGraph, "duplicate native task"):
            adapter.project(self.encode(envelope))

    def test_closed_fields_and_required_native_identities(self):
        changes = [lambda e: e.update(revision="accepted"),
                   lambda e: e["snapshots"][0].pop("metadata"),
                   lambda e: e["snapshots"][0].update(inferred_effect={}),
                   lambda e: e["producer"].update(unknown="version"),
                   lambda e: e["snapshots"][0]["config"]["configurable"].pop("checkpoint_id"),
                   lambda e: e["snapshots"][0]["tasks"][0].pop("result")]
        for change in changes:
            envelope = authored_envelope()
            change(envelope)
            with self.subTest(change=change), self.assertRaises(adapter.ontology_graph.InvalidGraph):
                adapter.project(self.encode(envelope))

    def test_metadata_writes_not_required_and_unknown_native_metadata_preserved(self):
        envelope = authored_envelope()
        envelope["snapshots"][0]["metadata"]["later_native_metadata"] = {"value": 3}
        self.assertNotIn("writes", envelope["snapshots"][0]["metadata"])
        projected, _ = adapter.project(self.encode(envelope))
        content = json.loads(projected["nodes"][0]["data"]["content"])
        self.assertEqual(content["snapshot"]["metadata"], envelope["snapshots"][0]["metadata"])
        self.assertEqual(content["snapshot"]["tasks"][0]["result"], {"answer": "draft"})

    def test_native_lineage_retained_without_previous_version_edge(self):
        envelope = authored_envelope()
        parent = copy.deepcopy(envelope["snapshots"][0]["config"])
        parent["configurable"]["checkpoint_id"] = "not-in-this-export"
        envelope["snapshots"][0]["parent_config"] = parent
        projected, _ = adapter.project(self.encode(envelope))
        content = json.loads(projected["nodes"][0]["data"]["content"])
        self.assertEqual(content["snapshot"]["parent_config"], parent)
        self.assertEqual(projected["edges"], [])

    def test_non_json_nonfinite_unicode_depth_and_cycle_refused(self):
        for invalid in (object(), ("native tuple not converted by producer",), float("nan"), float("inf"), "\ud800"):
            envelope = authored_envelope()
            envelope["snapshots"][0]["values"] = invalid
            with self.subTest(invalid=type(invalid)), self.assertRaises(adapter.ontology_graph.InvalidGraph):
                self.encode(envelope)
        for raw in (b"\xff", b'{"x":NaN}', b'{"x":1e999}', b"[" * 70 + b"0" + b"]" * 70):
            with self.assertRaises(adapter.ontology_graph.InvalidGraph):
                adapter.project(raw)
        envelope = authored_envelope()
        envelope["snapshots"][0]["values"] = envelope
        with self.assertRaisesRegex(adapter.ontology_graph.InvalidGraph, "cyclic"):
            self.encode(envelope)

    def test_profile_caps_refuse_instead_of_truncate(self):
        with self.assertRaisesRegex(adapter.ontology_graph.InvalidGraph, "byte limit"):
            adapter.project(b" " * (adapter.LIMITS["fileBytes"] + 1))
        envelope = authored_envelope()
        envelope["snapshots"] *= adapter.LIMITS["nodes"] + 1
        with self.assertRaisesRegex(adapter.ontology_graph.InvalidGraph, "snapshot limit"):
            adapter.project(self.encode(envelope))
        envelope = authored_envelope()
        envelope["snapshots"][0]["values"] = "x" * (adapter.LIMITS["stringCharacters"] + 1)
        with self.assertRaisesRegex(adapter.ontology_graph.InvalidGraph, "string limit"):
            self.encode(envelope)
        envelope["snapshots"][0]["values"] = "x" * adapter.LIMITS["stringCharacters"]
        with self.assertRaisesRegex(adapter.ontology_graph.InvalidGraph, "string limit"):
            adapter.project(self.encode(envelope))

    def test_projection_no_input_mutation_or_reference_fetch(self):
        envelope = authored_envelope()
        envelope["snapshots"][0]["values"] = {"sourceRef": "file:///never-open/private", "endpoint": "https://never-fetch.invalid"}
        before = copy.deepcopy(envelope)
        raw = self.encode(envelope)
        with patch.object(Path, "open", side_effect=AssertionError("reference opened")):
            self.report_raw(raw)
        self.assertEqual(envelope, before)
        self.assertEqual(raw, self.encode(before))

    def test_empty_export_is_no_effects_not_inapplicable(self):
        envelope = authored_envelope()
        envelope["snapshots"] = []
        report = self.report_raw(self.encode(envelope))
        self.assertEqual(report["status"], "no-recorded-effects")
        self.assertEqual(report["counts"], {"nodes": 0, "edges": 0})
        self.assertNotIn("not_applicable", json.dumps(report))


class NativeIntegrationTests(unittest.TestCase):
    def test_actual_installed_native_execution_under_guards(self):
        required = {"langgraph": "1.0.8", "langgraph-checkpoint": "4.0.0", "langchain-core": "1.2.12"}
        try:
            installed = {name: importlib.metadata.version(name) for name in required}
        except importlib.metadata.PackageNotFoundError as exc:
            self.skipTest("Optional actual LangGraph proof dependency missing: " + str(exc))
        self.assertEqual(installed, required, "Version drift requires explicit requalification, not a silent skip")
        completed = subprocess.run([sys.executable, "-B", str(EXAMPLE)],
                                   cwd=ROOT, capture_output=True, timeout=15)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        envelope = json.loads(completed.stdout)
        self.assertEqual(set(envelope), {"schema", "producer", "snapshots"})
        self.assertEqual(envelope["schema"], adapter.SCHEMA)
        self.assertEqual(envelope["producer"], required)
        self.assertEqual(len(envelope["snapshots"]), 4)
        self.assertEqual(sum(task["result"] is not None for snapshot in envelope["snapshots"]
                             for task in snapshot["tasks"]), 3)
        projected, source = adapter.project(completed.stdout)
        self.assertEqual(hashlib.sha256(completed.stdout).hexdigest(), source["sha256"])
        report = audit_report(projected, source)
        self.assertEqual(report["status"], "no-recorded-effects")
        self.assertEqual(report["counts"], {"nodes": 4, "edges": 0})
        self.assertFalse(report["inference_tested"])
        self.assertTrue(all(rows == [] for rows in report["queries"].values()))
        self.assertTrue(all(set(snapshot["metadata"]) == {"source", "step", "parents"}
                            for snapshot in envelope["snapshots"]))



if __name__ == "__main__":
    unittest.main()
