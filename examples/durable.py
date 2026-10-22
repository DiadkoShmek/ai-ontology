"""Durable continuity reference runtime. Python stdlib; no LLM or tool calls.

Trusted local caller, cooperative SQLite writers, bounded history. Hashes bind
bytes, not authorship, meaning, authority, consciousness, or behavioral quality.
The epistemic transition law is reused from continuity.py rather than duplicated.
"""
from __future__ import annotations

from dataclasses import asdict, replace
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sqlite3
import uuid
from types import MappingProxyType

from continuity import Conflict, Event, apply, empty, fork, knowledge

ZERO = "0" * 64
MAX_OPS = 4096
MAX_BYTES = 65536
VERSION = "continuity-runtime/1"


class Hold(ValueError):
    pass


def canonical(value):
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except UnicodeEncodeError as exc:
        raise Hold("invalid-utf8") from exc


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def closed(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        raise Hold("closed-schema-mismatch")


def text(value, cap=4096):
    if type(value) is not str or not value.strip():
        raise Hold("invalid-text")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise Hold("invalid-text") from exc
    if size > cap:
        raise Hold("invalid-text")


def strings(value):
    if type(value) is not list or len(value) > 64:
        raise Hold("invalid-string-list")
    for item in value:
        text(item)
    if len(set(value)) != len(value):
        raise Hold("duplicate-list-item")


def orientation(value):
    closed(value, ("purpose", "commitments", "voice"))
    text(value["purpose"])
    strings(value["commitments"])
    closed(value["voice"], ("attention", "uncertainty", "disagreement"))
    for x in value["voice"].values():
        text(x)


DEFAULT = {"purpose": "Investigate accurately and remain useful after correction",
           "commitments": ["retain revisions", "state accessible limits"],
           "voice": {"attention": "affected parties and task",
                     "uncertainty": "explicit scope and unknowns",
                     "disagreement": "reasons and a useful next move"}}


def packet(world, branch, topic, scope, head, budget=8192):
    """Exact scoped lookup, not semantic search. Never silently omit its basis."""
    if type(budget) is not int or not 512 <= budget <= MAX_BYTES:
        raise Hold("invalid-context-budget")
    for x in (branch, topic, scope):
        text(x)
    if branch not in world:
        raise Hold("unknown-branch")
    state, profile = world[branch]
    view = knowledge(state, topic, scope)
    active = set()
    todo = [view["claim"]] if "claim" in view else []
    while todo:
        ref = todo.pop()
        if ref not in active:
            active.add(ref)
            todo.extend(state.events[ref].basis)
    withdrawn = sorted(active.intersection(state.retired))
    if withdrawn:
        view = {**view, "recorded_status": view["status"], "status": "needs-review",
                "retired_basis": withdrawn}
    # Include the transitive basis and revision chain: content-addressable
    # references without available content would not suffice for recovery.
    selected = set()
    todo = [view["claim"]] if "claim" in view else []
    while todo:
        ref = todo.pop()
        if ref in selected:
            continue
        selected.add(ref)
        event = state.events[ref]
        todo.extend(event.basis)
        if event.revises is not None:
            todo.append(event.revises)
    result = {"schema": VERSION, "head": head, "branch": branch,
              "actor": state.actor, "profile": profile,
              "profile_sha256": digest(profile), "topic": topic, "scope": scope,
              "budget": budget, "view": view,
              "retirements": {k: v for k, v in state.retired.items() if k in selected},
              "evidence": [asdict(e) for k, e in state.events.items() if k in selected],
              "omitted_event_count": len(state.events) - len(selected),
              "limits": ["input statuses are authored", "no semantic entailment",
                         "actor labels are not authentication"]}
    # JSON normalization prevents tuples or aliases from crossing the boundary.
    result = json.loads(canonical(result))
    result["context_sha256"] = digest(result)
    if len(canonical(result)) > budget:
        raise Hold("required-context-exceeds-budget")
    return result


def reduce(world, op, head):
    closed(op, ("id", "kind", "branch", "data"))
    for key in ("id", "kind", "branch"):
        text(op[key], 256)
    kind, branch, data = op["kind"], op["branch"], op["data"]
    result = dict(world)
    if kind == "init":
        closed(data, ("actor", "orientation"))
        text(data["actor"], 256)
        orientation(data["orientation"])
        if world or branch != "main":
            raise Hold("root-already-exists-or-not-main")
        p = data["orientation"]
        result[branch] = (replace(empty(data["actor"], branch),
            profile=digest(p), commitments=tuple(p["commitments"])), p)
        return result
    if kind == "fork":
        closed(data, ("from",))
        text(data["from"], 256)
        if branch in world or data["from"] not in world:
            raise Hold("invalid-fork")
        state, profile = world[data["from"]]
        result[branch] = (fork(state, branch, head), profile)
        return result
    if branch not in world:
        raise Hold("unknown-branch")
    state, profile = world[branch]
    if kind == "event":
        closed(data, Event.__dataclass_fields__)
        if type(data["basis"]) is not list:
            raise Hold("basis-not-list")
        try:
            event = Event(**{**data, "basis": tuple(data["basis"])})
            result[branch] = (apply(state, event), profile)
        except (Conflict, TypeError) as exc:
            raise Hold(str(exc)) from exc
    elif kind == "retire":
        closed(data, ("event_id", "event_sha256", "reason"))
        text(data["event_id"], 256)
        text(data["reason"])
        event = state.events.get(data["event_id"])
        if event is None or event.kind != "observation" or digest(asdict(event)) != data["event_sha256"]:
            raise Hold("retirement-source-mismatch")
        if event.id in state.retired:
            raise Hold("source-already-retired")
        result[branch] = (replace(state, retired=MappingProxyType(
            {**state.retired, event.id: data["reason"]})), profile)
    elif kind == "orient":
        closed(data, ("previous_sha256", "orientation", "reason", "approved_by"))
        if data["previous_sha256"] != digest(profile):
            raise Hold("stale-orientation")
        orientation(data["orientation"])
        text(data["reason"])
        text(data["approved_by"], 256)  # trusted caller assertion, NOT authentication
        p = data["orientation"]
        result[branch] = (replace(state, profile=digest(p),
            commitments=tuple(p["commitments"])), p)
    elif kind == "decision":
        closed(data, ("context", "question", "response", "model"))
        text(data["question"])
        closed(data["model"], ("id", "request_sha256", "response_sha256"))
        for item in data["model"].values():
            text(item, 256)
        ctx = data["context"]
        if type(ctx) is not dict:
            raise Hold("invalid-context")
        try:
            expected = packet(world, branch, ctx["topic"], ctx["scope"], head, ctx["budget"])
        except (KeyError, TypeError) as exc:
            raise Hold("invalid-context") from exc
        # Python equality conflates JSON false/0 and 0.0/0. Context binding
        # requires the canonical representation, including those types.
        if canonical(ctx) != canonical(expected):
            raise Hold("stale-or-forged-context")
        answer = data["response"]
        closed(answer, ("text", "stance", "cites"))
        text(answer["text"], 8192)
        strings(answer["cites"])
        if answer["stance"] not in ("answer", "abstain", "dissent"):
            raise Hold("invalid-stance")
        if ctx["view"]["status"] == "needs-review" and answer["stance"] == "answer":
            raise Hold("retired-basis-needs-review")
        available = {e["id"] for e in ctx["evidence"]}
        if not set(answer["cites"]) <= available:
            raise Hold("citation-outside-context")
        # This validates traceability, NOT whether prose follows its citations.
    else:
        raise Hold("unknown-operation")
    return result


class Journal:
    """Bounded full replay (dictionary-copy cost up to O(n²)), one CAS head.

    Do not expose a caller-controlled database path to untrusted users. The
    database and its directory must be owned and protected by the operator.
    """
    def __init__(self, path, *, create=False):
        self.path = Path(path).resolve()
        if create:
            # Exclusive creation prevents accidentally replacing an existing DB.
            with self.path.open("xb"):
                pass
            with self.connect() as db:
                db.executescript("CREATE TABLE meta(id TEXT NOT NULL);"
                    "CREATE TABLE journal(seq INTEGER PRIMARY KEY, raw BLOB NOT NULL, "
                    "hash TEXT NOT NULL);")
                db.execute("INSERT INTO meta VALUES (?)", (str(uuid.uuid4()),))
        if not self.path.is_file():
            raise Hold("store-missing")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path.as_uri() + "?mode=rw", uri=True, timeout=5)
        try:
            db.execute("PRAGMA synchronous=FULL")
            with db:
                yield db
        finally:
            db.close()

    def _read(self, db, anchor=None):
        ids = db.execute("SELECT id FROM meta").fetchall()
        if len(ids) != 1:
            raise Hold("invalid-store-id")
        stream = ids[0][0]
        count = db.execute("SELECT COUNT(*) FROM journal").fetchone()[0]
        if count > MAX_OPS:
            raise Hold("history-limit")
        world, seen, hashes, previous = {}, {}, {}, ZERO
        rows = db.execute("SELECT seq,substr(raw,1,?),length(raw),hash "
                          "FROM journal ORDER BY seq", (MAX_BYTES + 1,)).fetchall()
        for ordinal, (seq, raw, size, stored) in enumerate(rows, 1):
            if seq != ordinal or size > MAX_BYTES or type(raw) is not bytes:
                raise Hold("journal-shape")
            try:
                op = json.loads(raw)
                if canonical(op) != raw:
                    raise Hold("noncanonical-event")
                actual = digest({"stream": stream, "seq": seq, "previous": previous,
                                 "operation": op})
                if stored != actual:
                    raise Hold("journal-hash-mismatch")
                world = reduce(world, op, previous)
            except (KeyError, TypeError, json.JSONDecodeError) as exc:
                raise Hold("invalid-journal-entry") from exc
            if op["id"] in seen:
                raise Hold("duplicate-journal-operation")
            seen[op["id"]] = raw
            previous = hashes[seq] = actual
        if anchor is not None:
            closed(anchor, ("stream", "seq", "head"))
            if (type(anchor["seq"]) is not int or anchor["seq"] < 0
                    or anchor["stream"] != stream
                    or (ZERO if anchor["seq"] == 0 else hashes.get(anchor["seq"])) != anchor["head"]):
                raise Hold("anchor-mismatch")
        return world, {"stream": stream, "seq": len(rows), "head": previous}, seen

    def read(self, *, anchor=None):
        with self.connect() as db:
            db.execute("BEGIN")
            return self._read(db, anchor)[:2]

    def append(self, op, *, expected, anchor=None):
        # Snapshot and byte-bound inputs before waiting for another writer.
        raw = canonical(op)
        if len(raw) > MAX_BYTES:
            raise Hold("operation-byte-limit")
        op = json.loads(raw)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            world, tail, seen = self._read(db, anchor)
            if type(op) is not dict or type(op.get("id")) is not str:
                raise Hold("invalid-operation-id")
            if op["id"] in seen:
                if seen[op["id"]] != raw:
                    raise Hold("operation-id-collision")
                return tail  # committed exact retry, even after later commits
            if expected != tail["head"]:
                raise Hold("stale-head")
            if tail["seq"] >= MAX_OPS:
                raise Hold("history-limit")
            reduce(world, op, tail["head"])
            seq = tail["seq"] + 1
            new_hash = digest({"stream": tail["stream"], "seq": seq,
                               "previous": tail["head"], "operation": op})
            db.execute("INSERT INTO journal VALUES (?,?,?)", (seq, raw, new_hash))
            return {"stream": tail["stream"], "seq": seq, "head": new_hash}

    def context(self, branch, topic, scope, *, budget=8192, anchor=None):
        world, tail = self.read(anchor=anchor)
        return packet(world, branch, topic, scope, tail["head"], budget)


def operation(_id, _kind, _branch="main", **data):
    return {"id": _id, "kind": _kind, "branch": _branch, "data": data}


def event_operation(event):
    return json.loads(canonical(operation(event.id, "event", event.branch, **asdict(event))))
