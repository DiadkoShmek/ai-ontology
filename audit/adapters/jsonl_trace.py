"""PROJECTED record interchange, not an interpreter for arbitrary agent traces.

Each line is exactly {"kind":"node"|"edge","record":<existing graph record>}.
No causal, use, acceptance or authority relations are inferred or inserted.
References inside records are opaque strings and are never fetched.
"""

import json
import math

from ontology import graph


def parse_json(text):
    """Strict JSON decoding with canonical duplicate-key errors and bounded depth."""
    try:
        value = json.loads(
            text, object_pairs_hook=graph.unique_object,
            parse_constant=lambda _: (_ for _ in ()).throw(
                graph.InvalidGraph("nonfinite number")))
        stack = [(value, 0)]
        while stack:
            item, depth = stack.pop()
            graph.require(depth <= 64, "JSON depth limit")
            if type(item) is str:
                item.encode("utf-8", "strict")
            elif type(item) is float:
                graph.require(math.isfinite(item), "nonfinite number")
            elif type(item) is dict:
                stack.extend((key, depth + 1) for key in item)
                stack.extend((child, depth + 1) for child in item.values())
            elif type(item) is list:
                stack.extend((child, depth + 1) for child in item)
        return value
    except graph.InvalidGraph:
        raise
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise graph.InvalidGraph("invalid JSON") from exc


def project(text):
    """Project exact envelopes without manufacturing graph content."""
    result = {"nodes": [], "edges": []}
    limits = graph.VOCABULARY["limits"]
    # JSONL uses LF delimiters. str.splitlines() would incorrectly split literal
    # Unicode U+2028/U+2029 inside otherwise valid JSON string fields.
    lines = text.split("\n") if text else []
    if lines and lines[-1] == "":
        lines.pop()
    for line_number, line in enumerate(lines, 1):
        envelope = parse_json(line)
        graph.require(type(envelope) is dict and set(envelope) == {"kind", "record"},
                      "JSONL envelope keys at line " + str(line_number))
        kind = envelope["kind"]
        graph.require(type(kind) is str and kind in ("node", "edge"),
                      "JSONL envelope kind at line " + str(line_number))
        key = "nodes" if kind == "node" else "edges"
        result[key].append(envelope["record"])
        graph.require(len(result[key]) <= limits[key], key + " limit")
    return result
