# Audit a permitted projected run

This thin standard-library entry uses the existing ontology validator and
competency queries. It does not require the reference runtime or a model.
[Proposed profile and requirements](../protocols/continuity-audit-v1.md) ·
[Short note](../papers/inspectable-continuity.md)

```sh
python3 -m audit.cli validate ontology/fixtures/closed-loop.json
python3 -m audit.cli report ontology/fixtures/closed-loop.json
python3 -m audit.cli report ontology/fixtures/open-loop.json
python3 -m unittest audit.test_audit -q
```

Expected coverage: `complete` then `incomplete`. Both fixtures are authored
examples, not real-model observations. Valid input exits 0 even when incomplete;
malformed input exits 2. Read `status`, not only the exit code.

## Export interface

A producer can supply the [neutral graph](../ontology/README.md) or explicit
JSONL envelopes, one per line:

```json
{"kind":"node","record":{"id":"scope:demo","type":"Scope","data":{"label":"Demo","description":"An authored example"}}}
```

Edges use `{"kind":"edge","record":{"source":"...","relation":"...","target":"..."}}`.
The same canonical graph constraints apply. Select `--format jsonl`. A Scope
alone has `no-recorded-effects`; that is neither failure nor proof that revision
is inapplicable. JSONL is already-projected record transport: source-specific
instrumentation must supply its own justified nodes and links. Unrecognized
raw provider events are rejected rather than converted into guessed relations.

Every report includes the input digest, profile, all eight query row sets,
orphan effects, available/use gaps and the limited graph Claim status counts.
No URLs or file references are followed. Record completeness does not establish
chronology, causal influence, behavioral change, benefit, permission or truth.
The [runtime adapter](../ontology/runtime_adapter.py) separately projects actual
compatible SQLite readback. A framework-specific exporter remains future work.
