"""Lossless, bounded journal transport; a standard zlib/Base85 codec.

The host restores exact operations before constructing model input. This is
neither semantic compression nor encryption. The external digest is supplied by
the caller through a trusted path; a self-reported hash cannot authenticate data.
No network, providers, filesystem writes, arbitrary code or fallback retrieval.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import sys
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "examples"))
from durable import (Hold, MAX_BYTES, MAX_OPS, ZERO, canonical, closed, digest,
                     packet, reduce, text)

VERSION = "journal-handoff/1"
MAX_RAW = 262144


def _capacity(value):
    if type(value) is not int or not 256 <= value <= MAX_BYTES:
        raise Hold("invalid-handoff-capacity")


def _load(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise Hold("duplicate-handoff-key")
            result[key] = value
        return result

    def constant(_value):
        raise Hold("nonfinite-handoff-number")

    try:
        value = json.loads(raw, object_pairs_hook=unique, parse_constant=constant)
        if canonical(value) != raw:
            raise Hold("noncanonical-handoff")
        return value
    except (ValueError, TypeError, RecursionError, UnicodeError) as exc:
        if isinstance(exc, Hold):
            raise
        raise Hold("invalid-handoff-json") from exc


def _replay(body):
    closed(body, ("schema", "branch", "scope", "stream", "history"))
    if body["schema"] != VERSION:
        raise Hold("handoff-version-mismatch")
    for key in ("branch", "scope", "stream"):
        text(body[key], 256)
    history = body["history"]
    if type(history) is not list or not 1 <= len(history) <= MAX_OPS:
        raise Hold("handoff-operation-limit")
    world, seen, previous = {}, set(), ZERO
    try:
        for seq, op in enumerate(history, 1):
            if len(canonical(op)) > MAX_BYTES:
                raise Hold("operation-byte-limit")
            if type(op) is not dict or type(op.get("id")) is not str:
                raise Hold("invalid-operation-id")
            if op["id"] in seen:
                raise Hold("duplicate-journal-operation")
            seen.add(op["id"])
            world = reduce(world, op, previous)
            previous = digest({"stream": body["stream"], "seq": seq,
                               "previous": previous, "operation": op})
    except (KeyError, TypeError, ValueError, RecursionError) as exc:
        if isinstance(exc, Hold):
            raise
        raise Hold("invalid-handoff-history") from exc
    if body["branch"] not in world:
        raise Hold("unknown-branch")
    return world, {"stream": body["stream"], "seq": len(history), "head": previous}


def pack_history(history, *, stream, branch, scope, capacity=3200):
    """Pack the whole supplied history or raise; never truncate or choose facts.

    Budget and the future operation are deliberately absent from this API.
    Payload bytes, including every event's text, basis and revision, survive.
    """
    _capacity(capacity)
    try:
        raw = canonical({"schema": VERSION, "branch": branch, "scope": scope,
                         "stream": stream, "history": history})
    except (TypeError, ValueError, RecursionError) as exc:
        raise Hold("invalid-handoff-input") from exc
    if len(raw) > MAX_RAW:
        raise Hold("handoff-raw-limit")
    _replay(_load(raw))
    wire = canonical({"v": 1, "n": len(raw),
                      "sha256": hashlib.sha256(raw).hexdigest(),
                      "z85": base64.b85encode(zlib.compress(raw, 9)).decode("ascii")})
    if len(wire) > capacity:
        raise Hold("complete-handoff-exceeds-capacity")
    return wire


def unpack_history(wire, *, expected_sha256, branch, scope, capacity=3200):
    """Verify bounded transport and replay, then return the exact decoded DATA.

    A valid snapshot says nothing about a source's subsequent changes. Live
    decision admission still requires the owning Journal's current-head CAS.
    """
    _capacity(capacity)
    if type(wire) is not bytes or len(wire) > capacity:
        raise Hold("handoff-wire-limit")
    if (type(expected_sha256) is not str or len(expected_sha256) != 64
            or hashlib.sha256(wire).hexdigest() != expected_sha256):
        raise Hold("handoff-anchor-mismatch")
    envelope = _load(wire)
    closed(envelope, ("v", "n", "sha256", "z85"))
    if type(envelope["v"]) is not int or envelope["v"] != 1:
        raise Hold("handoff-codec-mismatch")
    size = envelope["n"]
    if type(size) is not int or not 1 <= size <= MAX_RAW:
        raise Hold("handoff-raw-limit")
    if type(envelope["z85"]) is not str:
        raise Hold("invalid-handoff-encoding")
    try:
        compressed = base64.b85decode(envelope["z85"].encode("ascii"))
        if base64.b85encode(compressed).decode("ascii") != envelope["z85"]:
            raise Hold("noncanonical-handoff-encoding")
        decoder = zlib.decompressobj()
        raw = decoder.decompress(compressed, size + 1)
    except (ValueError, UnicodeError, zlib.error) as exc:
        raise Hold("invalid-handoff-encoding") from exc
    if (len(raw) != size or not decoder.eof or decoder.unconsumed_tail
            or decoder.unused_data):
        raise Hold("incomplete-or-extra-handoff-data")
    if hashlib.sha256(raw).hexdigest() != envelope["sha256"]:
        raise Hold("handoff-content-mismatch")
    body = _load(raw)
    closed(body, ("schema", "branch", "scope", "stream", "history"))
    if body.get("branch") != branch or body.get("scope") != scope:
        raise Hold("handoff-target-mismatch")
    _replay(body)
    return body


def export_journal(journal, *, branch, scope, capacity=3200, anchor=None):
    """Capture and validate one SQLite read transaction; do not change the DB."""
    with journal.connect() as db:
        db.execute("BEGIN")
        _world, tail, seen = journal._read(db, anchor)
        history = [json.loads(raw) for raw in seen.values()]
        wire = pack_history(history, stream=tail["stream"], branch=branch,
                            scope=scope, capacity=capacity)
    return wire, tail


def context_from_handoff(wire, *, expected_sha256, branch, scope, topic,
                         capacity=3200, context_budget=8192):
    """Existing context builder consumes the restored state, not a new reducer."""
    body = unpack_history(wire, expected_sha256=expected_sha256,
                          branch=branch, scope=scope, capacity=capacity)
    world, tail = _replay(body)
    return packet(world, branch, topic, scope, tail["head"], context_budget)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--capacity", type=int, default=3200)
    args = parser.parse_args()
    _capacity(args.capacity)
    wire = sys.stdin.buffer.read(args.capacity + 1)
    body = unpack_history(wire, expected_sha256=args.expected_sha256,
                          branch=args.branch, scope=args.scope,
                          capacity=args.capacity)
    sys.stdout.buffer.write(canonical(body))


if __name__ == "__main__":
    main()
