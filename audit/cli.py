"""Validate or report PROJECTED records with the existing ontology.graph owner.

Completeness is recorded-path coverage only. It certifies neither truth,
authenticated authority, behavioral learning, performance nor causal benefit.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from ontology import graph
from audit.adapters.jsonl_trace import parse_json, project


QUESTIONS = tuple(item["id"] for item in json.loads(
    (graph.HERE / "competency-questions.json").read_text(encoding="utf-8"))["questions"])
BOUNDARY = (
    "Recorded graph path coverage only; absence means unrecorded. Structural "
    "validity and complete paths do not establish truth, authenticated authority, "
    "chronology, actual learning, performance, consciousness or causal benefit. No references "
    "are fetched; JSONL input is projected record interchange, not raw trace interpretation. "
    "Native checkpoint observations do not establish participation or revision semantics."
)


def load_source(path, input_format="graph"):
    """Read once for a source-bound digest; all graph semantics remain canonical."""
    graph.require(input_format in ("graph", "jsonl", "langgraph"), "unknown input format")
    cap = graph.VOCABULARY["limits"]["fileBytes"]
    with Path(path).open("rb") as source:
        raw = source.read(cap + 1)
    graph.require(len(raw) <= cap, "file byte limit")
    if input_format == "langgraph":
        from audit.adapters.langgraph_checkpoint import project as project_native
        return project_native(raw)
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeError as exc:
        raise graph.InvalidGraph("input must be UTF-8") from exc
    value = parse_json(text) if input_format == "graph" else project(text)
    graph.validate(value)
    return value, {"sha256": hashlib.sha256(raw).hexdigest(),
                   "bytes": len(raw), "format": input_format}


def _base(value, source):
    return {
        "schema": "ai-ontology-record-audit-v1",
        "profile": {"schema": graph.VOCABULARY["schema"],
                    "version": graph.VOCABULARY["version"],
                    "bookVersion": graph.VOCABULARY["bookVersion"]},
        "source": dict(source), "valid": True,
        "counts": {"nodes": len(value["nodes"]), "edges": len(value["edges"])},
        "inference_tested": False, "boundary": BOUNDARY,
    }


def report(value, source, question="returnPath"):
    """Summarize existing competency-query rows, never infer missing relations."""
    graph.validate(value)
    graph.require(question in QUESTIONS, "unknown competency question")
    queries = {name: graph.answer(value, name) for name in QUESTIONS}
    paths = queries["returnPath"]
    effect_ids = {node["id"] for node in value["nodes"] if node["type"] == "Effect"}
    orphan_effects = sorted(effect_ids - {row["effect"] for row in paths})
    complete = sum(row["recordedPathComplete"] is True for row in paths)
    status = ("no-recorded-effects" if not effect_ids else
              "complete" if paths and complete == len(paths) and not orphan_effects
              else "incomplete")
    output = _base(value, source)
    output.update({
        "status": status,
        "coverage": {"effect_records": len(effect_ids),
                     "recorded_paths": len(paths), "complete_paths": complete,
                     "incomplete_paths": len(paths) - complete},
        "question": question, "queries": queries,
        "gaps": {
            "orphan_effects": orphan_effects,
            "available_without_recorded_use": [row for row in queries["evidenceUse"]
                                               if row["availableEdge"] and not row["usedEdge"]],
            "used_without_recorded_availability": [row for row in queries["evidenceUse"]
                                                   if row["usedEdge"] and not row["availableEdge"]],
        },
    })
    counts = Counter(node["data"]["status"] for node in value["nodes"] if node["type"] == "Claim")
    statuses = graph.VOCABULARY["classes"]["Claim"]["fields"]["status"]["enum"]
    output["claim_status_counts"] = {status: counts[status] for status in statuses}
    output["claim_status_scope"] = "Claim.data.status only; not publication CLAIMS.md statuses"
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "report"):
        command = commands.add_parser(name)
        command.add_argument("file")
        command.add_argument("--format", choices=("graph", "jsonl", "langgraph"), default="graph")
        if name == "report":
            command.add_argument("--question", choices=QUESTIONS, default="returnPath")
    args = parser.parse_args(argv)
    try:
        value, source = load_source(args.file, args.format)
        if args.command == "report":
            output = report(value, source, args.question)
        else:
            output = _base(value, source)
            output["status"] = "valid"
        print(json.dumps(output, ensure_ascii=True, sort_keys=True, indent=2))
        return 0
    except (graph.InvalidGraph, OSError, ValueError, RecursionError) as exc:
        print(json.dumps({"valid": False, "status": "invalid",
                          "error": str(exc)[:512], "inference_tested": False},
                         ensure_ascii=True, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
