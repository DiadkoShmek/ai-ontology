"""Local source/record tests only; no LLM trials or external trace ingestion."""

from contextlib import redirect_stderr, redirect_stdout
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from ontology import graph
from audit import cli


ROOT = Path(__file__).resolve().parents[1]


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(prefix="ontology-audit-test-")
        self.addCleanup(self.folder.cleanup)
        self.directory = Path(self.folder.name)

    def fixture(self, name="closed-loop"):
        return graph.load(ROOT / "ontology" / "fixtures" / (name + ".json"))

    def write(self, value, name="input.json"):
        path = self.directory / name
        path.write_bytes(json.dumps(value, ensure_ascii=False).encode("utf-8"))
        return path

    def invoke(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = cli.main([str(arg) for arg in args])
        return code, stdout.getvalue(), stderr.getvalue()

    def audited(self, value):
        path = self.write(value)
        loaded, source = cli.load_source(path)
        return cli.report(loaded, source)

    def invalid(self, raw, input_format="graph"):
        path = self.directory / "invalid.input"
        path.write_bytes(raw)
        code, stdout, stderr = self.invoke("report", path, "--format", input_format)
        self.assertEqual(code, 2, (stdout, stderr))
        self.assertEqual(stdout, "")
        error = json.loads(stderr)
        self.assertFalse(error["valid"])
        self.assertEqual(error["status"], "invalid")
        self.assertFalse(error["inference_tested"])
        self.assertNotIn("Traceback", stderr)

    def test_authored_closed_open_and_canonical_query_rows(self):
        for fixture, expected in (("closed-loop", "complete"), ("open-loop", "incomplete")):
            value = self.fixture(fixture)
            report = self.audited(value)
            self.assertEqual(report["status"], expected)
            self.assertTrue(report["valid"])
            self.assertFalse(report["inference_tested"])
            for question in cli.QUESTIONS:
                self.assertEqual(report["queries"][question], graph.answer(value, question))
            self.assertIn("Recorded graph path coverage only", report["boundary"])
            self.assertEqual(report["profile"]["version"], graph.VOCABULARY["version"])

    def test_mixed_complete_incomplete_is_incomplete(self):
        value = self.fixture()
        value["nodes"].append({"id": "effect:second", "type": "Effect", "data": {
            "label": "No return yet", "description": "Authored incomplete path", "state": "unknown"}})
        value["edges"].append({"source": "decision:next", "relation": "hasEffect", "target": "effect:second"})
        report = self.audited(value)
        self.assertEqual(report["status"], "incomplete")
        self.assertEqual(report["coverage"]["recorded_paths"], 2)
        self.assertEqual(report["coverage"]["complete_paths"], 1)
        self.assertEqual(report["coverage"]["incomplete_paths"], 1)

    def test_empty_and_no_effect_records_not_certified(self):
        for value in ({"nodes": [], "edges": []}, {"nodes": [{
                "id": "actor:only", "type": "Actor", "data": {"label": "Only record", "kind": "unknown"}}], "edges": []}):
            report = self.audited(value)
            self.assertEqual(report["status"], "no-recorded-effects")
            self.assertEqual(report["coverage"]["complete_paths"], 0)
            self.assertNotIn("not_applicable", json.dumps(report))
            self.assertFalse(report["inference_tested"])

    def test_orphan_effects_are_incomplete_with_or_without_complete_paths(self):
        orphan = {"id": "effect:orphan", "type": "Effect", "data": {
            "label": "No originating decision edge", "description": "Authored orphan", "state": "reported"}}
        for value in ({"nodes": [orphan], "edges": []}, self.fixture()):
            if orphan not in value["nodes"]:
                value["nodes"].append(copy.deepcopy(orphan))
            report = self.audited(value)
            self.assertEqual(report["status"], "incomplete")
            self.assertEqual(report["gaps"]["orphan_effects"], ["effect:orphan"])
            self.assertGreater(report["coverage"]["effect_records"], 0)

    def test_json_jsonl_equivalence_and_no_inferred_edges(self):
        value = self.fixture()
        value["nodes"][0]["data"]["label"] = "Unicode\u2028separator\u2029is not a record delimiter"
        path = self.write(value)
        projected = self.directory / "projected.jsonl"
        envelopes = [{"kind": kind, "record": record}
                     for key, kind in (("nodes", "node"), ("edges", "edge")) for record in value[key]]
        projected.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in envelopes) + "\n", encoding="utf-8")
        as_graph, graph_source = cli.load_source(path)
        as_jsonl, jsonl_source = cli.load_source(projected, "jsonl")
        self.assertEqual(as_graph, as_jsonl)
        self.assertEqual(as_jsonl, value)
        left, right = cli.report(as_graph, graph_source), cli.report(as_jsonl, jsonl_source)
        self.assertNotEqual(left.pop("source"), right.pop("source"))
        self.assertEqual(left, right)

    def test_gaps_and_claim_statuses_are_recorded_schema_fields_only(self):
        value = self.fixture()
        value["edges"] = [edge for edge in value["edges"] if edge != {
            "source": "decision:first", "relation": "availableEvidence", "target": "observation:source"}]
        report = self.audited(value)
        gaps = report["gaps"]
        self.assertEqual([row["observation"] for row in gaps["available_without_recorded_use"]], ["observation:unused"])
        self.assertEqual([row["observation"] for row in gaps["used_without_recorded_availability"]], ["observation:source"])
        statuses = graph.VOCABULARY["classes"]["Claim"]["fields"]["status"]["enum"]
        self.assertEqual(set(report["claim_status_counts"]), set(statuses))
        self.assertEqual(sum(report["claim_status_counts"].values()),
                         sum(node["type"] == "Claim" for node in value["nodes"]))
        self.assertNotIn("unsupported", report["claim_status_counts"])
        self.assertIn("not publication CLAIMS.md", report["claim_status_scope"])

    def test_no_references_fetched_and_no_input_mutation(self):
        value = self.fixture()
        for node in value["nodes"]:
            if node["type"] == "Observation":
                node["data"]["sourceRef"] = "file:///must-not-be-opened/private.txt"
        before = copy.deepcopy(value)
        path = self.write(value)
        original = path.read_bytes()
        real_open = Path.open

        def input_only(candidate, *args, **kwargs):
            self.assertEqual(candidate, path, "followed a graph reference")
            return real_open(candidate, *args, **kwargs)

        with patch.object(Path, "open", input_only):
            loaded, source = cli.load_source(path)
            report = cli.report(loaded, source, "authority")
        self.assertEqual(source["sha256"], hashlib.sha256(original).hexdigest())
        self.assertEqual(report["question"], "authority")
        self.assertEqual(value, before)
        self.assertEqual(loaded, before)
        self.assertEqual(path.read_bytes(), original)

    def test_invalid_utf8_utf16_duplicate_nonfinite_depth_and_shape(self):
        for raw in (b'\xff', json.dumps({"nodes": [], "edges": []}).encode("utf-16"),
                    b'{"nodes":[],"nodes":[],"edges":[]}',
                    b'{"nodes":[],"edges":[],"x":NaN}',
                    b'{"nodes":[],"edges":[],"x":1e999}',
                    b'[' * 100 + b'0' + b']' * 100,
                    b'{}', b'{', b'{"nodes":["\\ud800"],"edges":[]}'):
            self.invalid(raw)

    def test_malformed_jsonl_envelopes_not_arbitrary_raw_traces(self):
        for raw in (b'{"event":"tool_call","tool":"read"}\n',
                    b'{"kind":"node","record":{},"inferred":true}\n',
                    b'{"kind":"node","kind":"edge","record":{}}\n',
                    b'{"kind":"node","record":NaN}\n',
                    b'{"kind":"edge","record":{}}\n', b'\n', b'null\n'):
            self.invalid(raw, "jsonl")

    def test_total_input_byte_and_projected_record_caps(self):
        cap = graph.VOCABULARY["limits"]["fileBytes"]
        self.invalid(b" " * (cap + 1))
        self.invalid(b" " * (cap + 1), "jsonl")
        node = {"id": "actor:same", "type": "Actor", "data": {"label": "x", "kind": "unknown"}}
        rows = [json.dumps({"kind": "node", "record": node})] * (graph.VOCABULARY["limits"]["nodes"] + 1)
        self.invalid("\n".join(rows).encode(), "jsonl")
        edge = {"source": "x", "relation": "hasEffect", "target": "y"}
        rows = [json.dumps({"kind": "edge", "record": edge})] * (graph.VOCABULARY["limits"]["edges"] + 1)
        self.invalid("\n".join(rows).encode(), "jsonl")

    def test_real_cli_validate_and_valid_incomplete_exit_zero(self):
        path = self.write(self.fixture("open-loop"))
        for command in ("validate", "report"):
            completed = subprocess.run([sys.executable, "-m", "audit.cli", command, str(path)],
                                       cwd=ROOT, capture_output=True, text=True, timeout=10)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(completed.stdout)
            self.assertEqual(result["status"], "valid" if command == "validate" else "incomplete")
        missing = subprocess.run([sys.executable, "-m", "audit.cli", "report", str(path) + ".missing"],
                                 cwd=ROOT, capture_output=True, text=True, timeout=10)
        self.assertEqual(missing.returncode, 2)
        self.assertEqual(json.loads(missing.stderr)["status"], "invalid")

    def test_real_cli_claim_use_is_source_bound_and_does_not_widen_observation_gaps(self):
        value = self.fixture("historical-claim-use")
        path = self.write(value, "historical-claim-use.json")
        original = path.read_bytes()
        completed = subprocess.run([
            sys.executable, "-B", "-m", "audit.cli", "report", str(path), "--question", "claimUse"],
            cwd=ROOT, capture_output=True, text=True, timeout=10)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["question"], "claimUse")
        self.assertEqual(report["source"]["sha256"], hashlib.sha256(original).hexdigest())
        self.assertEqual(report["source"]["bytes"], len(original))
        self.assertEqual(report["queries"]["claimUse"], graph.answer(value, "claimUse"))
        self.assertEqual(report["queries"]["evidenceUse"], [])
        self.assertEqual(report["gaps"]["used_without_recorded_availability"], [])
        self.assertFalse(report["inference_tested"])
        self.assertEqual(report["claim_status_counts"]["accepted"], 1)
        self.assertEqual(path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
