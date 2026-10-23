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
compatible SQLite readback.

## Native LangGraph checkpoint observations

The optional [local example](../examples/integrations/langgraph_checkpoint.py)
executes ordinary deterministic nodes in an installed LangGraph runtime,
collects actual `get_state_history` snapshots and writes a JSON export to stdout.
It invokes no model. The example was exercised with LangGraph 1.0.8,
langgraph-checkpoint 4.0.0 and langchain-core 1.2.12. These optional packages are
needed to run the example, not to audit an existing export.

```sh
python3 -B examples/integrations/langgraph_checkpoint.py > local-checkpoints.json
python3 -m audit.cli report local-checkpoints.json --format langgraph
python3 -m unittest audit.test_langgraph_checkpoint -q
```

Expected for that authored run: four native snapshots and four `Observation`
records, no inferred edges, `no-recorded-effects`. Completed task outputs are
retained in `tasks[*].result`; `metadata.writes` is not required. This is a
working native-source ingestion route, not evidence of a complete revision
path or of a learning agent. InMemorySaver is RAM storage, not a cross-process
durability demonstration.

The [adapter](adapters/langgraph_checkpoint.py) binds exact input bytes and
checkpoint identity, preserves the permitted JSON payload and refuses unsupported
types or size overflow. It does not turn a thread into a participant, scheduling
into judgment, state updates into external effects, or prose about revision
into an accepted revision. Source identifiers are supplied labels, not
authenticated origin. The capture example uses authored nonsensitive data;
full checkpoint payloads from another application require a separate privacy
review before disclosure. The auditor itself does not upload them.
