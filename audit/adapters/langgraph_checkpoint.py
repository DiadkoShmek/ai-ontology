"""Native checkpoint record interchange, not a semantic participation interpreter.

Raw exports are declarations, not authenticated provenance. A source digest
binds exact supplied bytes; it does not attest their producer or truth. No input
reference is opened. Existing ontology and audit owners remain authoritative.
"""

import hashlib
import json
from urllib.parse import urlencode


from ontology import graph as ontology_graph
from audit.adapters.jsonl_trace import parse_json


SCHEMA = "langgraph-native-state-history-export-v1"
PRODUCER_KEYS = {"langgraph", "langgraph-checkpoint", "langchain-core"}
SNAPSHOT_KEYS = {"values", "next", "config", "metadata", "created_at",
                 "parent_config", "tasks", "interrupts"}
TASK_KEYS = {"id", "name", "path", "error", "interrupts", "state", "result"}
LIMITS = ontology_graph.VOCABULARY["limits"]
BOUNDARY = (
    "One Observation per supplied native snapshot; zero inferred relations. "
    "Availability means available to this adapter, not available to an agent's "
    "decision. Thread/checkpoint identifiers and producer versions are supplied "
    "source labels, not authenticated identity or authority. Checkpoint storage, "
    "task results and lineage do not establish Decision, external Effect, "
    "evidence use, accepted revision, learning, benefit or cross-process durability."
)


def require(condition, message):
    ontology_graph.require(condition, message)


def _check_json(value):
    """No object conversion, truncation, repr fallback or permissive serialization."""
    stack = [(value, 0, False)]
    active = set()
    while stack:
        item, depth, exiting = stack.pop()
        if exiting:
            active.remove(id(item))
            continue
        require(depth <= 64, "native export depth limit")
        kind = type(item)
        if kind is str:
            require(len(item) <= LIMITS["stringCharacters"], "native export string limit")
            try:
                item.encode("utf-8", "strict")
            except UnicodeError as exc:
                raise ontology_graph.InvalidGraph("native export Unicode") from exc
        elif item is None or kind in (bool, int):
            continue
        elif kind is float:
            # Shared audit parser also rejects overflow/nonfinite values.
            import math
            require(math.isfinite(item), "native export nonfinite number")
        elif kind in (dict, list):
            # A parsed JSON tree cannot cycle; encoder callers still must not
            # give us a graph-shaped Python object and wait for recursion failure.
            if id(item) in active:
                raise ontology_graph.InvalidGraph("native export cyclic container")
            active.add(id(item))
            stack.append((item, depth, True))
            if kind is dict:
                require(all(type(key) is str for key in item), "native export string keys")
                stack.extend((key, depth + 1, False) for key in item)
                stack.extend((child, depth + 1, False) for child in item.values())
            else:
                stack.extend((child, depth + 1, False) for child in item)
        else:
            raise ontology_graph.InvalidGraph("native export unsupported JSON payload")


def encode_export(envelope):
    """Serialize an already JSON-safe native capture; unsupported payload refuses."""
    _check_json(envelope)
    try:
        raw = json.dumps(envelope, ensure_ascii=True, allow_nan=False,
                         sort_keys=True, separators=(",", ":")).encode("ascii")
    except (ValueError, TypeError, RecursionError) as exc:
        raise ontology_graph.InvalidGraph("native export serialization") from exc
    require(len(raw) <= LIMITS["fileBytes"], "native export byte limit")
    return raw


def _checkpoint_key(config):
    require(type(config) is dict and type(config.get("configurable")) is dict,
            "native checkpoint config")
    configurable = config["configurable"]
    keys = ("thread_id", "checkpoint_ns", "checkpoint_id")
    require(all(type(configurable.get(key)) is str for key in keys), "native checkpoint keys")
    require(bool(configurable["thread_id"]) and bool(configurable["checkpoint_id"]),
            "native checkpoint identity missing")
    return tuple(configurable[key] for key in keys)


def project(raw):
    """Return (existing ontology graph, exact raw-export source metadata)."""
    require(type(raw) is bytes, "native export bytes required")
    require(len(raw) <= LIMITS["fileBytes"], "native export byte limit")
    try:
        envelope = parse_json(raw.decode("utf-8", "strict"))
    except UnicodeError as exc:
        raise ontology_graph.InvalidGraph("native export UTF-8") from exc
    _check_json(envelope)
    require(type(envelope) is dict and set(envelope) == {"schema", "producer", "snapshots"},
            "native export envelope keys")
    require(envelope["schema"] == SCHEMA, "native export schema")
    producer, snapshots = envelope["producer"], envelope["snapshots"]
    require(type(producer) is dict and set(producer) == PRODUCER_KEYS,
            "native export producer keys")
    require(all(type(version) is str and bool(version.strip()) for version in producer.values()),
            "native export producer versions")
    require(type(snapshots) is list and len(snapshots) <= LIMITS["nodes"],
            "native export snapshot limit")
    digest = hashlib.sha256(raw).hexdigest()
    projected = {"nodes": [], "edges": []}
    seen = set()
    for index, snapshot in enumerate(snapshots):
        require(type(snapshot) is dict and set(snapshot) == SNAPSHOT_KEYS,
                "native snapshot fields")
        key = _checkpoint_key(snapshot["config"])
        require(key not in seen, "duplicate native checkpoint")
        seen.add(key)
        require(type(snapshot["next"]) is list and
                all(type(name) is str for name in snapshot["next"]), "native next names")
        require(snapshot["metadata"] is None or type(snapshot["metadata"]) is dict,
                "native metadata")
        require(snapshot["created_at"] is None or type(snapshot["created_at"]) is str,
                "native timestamp")
        if snapshot["parent_config"] is not None:
            _checkpoint_key(snapshot["parent_config"])
        require(type(snapshot["tasks"]) is list and type(snapshot["interrupts"]) is list,
                "native task/interrupt arrays")
        task_ids = set()
        for task in snapshot["tasks"]:
            require(type(task) is dict and set(task) == TASK_KEYS, "native task fields")
            require(type(task["id"]) is str and bool(task["id"]) and
                    type(task["name"]) is str and bool(task["name"]), "native task identity")
            require(task["id"] not in task_ids, "duplicate native task")
            task_ids.add(task["id"])
            require(type(task["path"]) is list and type(task["interrupts"]) is list,
                    "native task path/interrupts")
        content = json.dumps({"producer": producer, "snapshot": snapshot}, ensure_ascii=True,
                             allow_nan=False, sort_keys=True, separators=(",", ":"))
        reference = ("langgraph-checkpoint:sha256:" + digest + "?" + urlencode({
            "thread_id": key[0], "checkpoint_ns": key[1], "checkpoint_id": key[2]})
            + "#/snapshots/" + str(index))
        projected["nodes"].append({
            "id": "observation:lg:" + digest + ":" + str(index), "type": "Observation",
            "data": {"label": "Native StateSnapshot " + str(index), "sourceRef": reference,
                     "availability": "available", "content": content},
        })
    ontology_graph.validate(projected)
    require(len(json.dumps(projected, ensure_ascii=True, separators=(",", ":")).encode("ascii"))
            <= LIMITS["fileBytes"], "projected graph byte limit")
    return projected, {"sha256": digest, "bytes": len(raw), "format": SCHEMA,
                       "producer": dict(producer), "adapter_boundary": BOUNDARY}
