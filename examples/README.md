# Continuity reference package

Python 3.11+, standard library only. No installation, network, live LLM calls, service startup or automatic profile changes. The durable examples create a task-owned SQLite database; the demo uses and removes only its own temporary directory.

From repository root:

```sh
python3 -m unittest discover -s examples -v
python3 examples/durable_demo.py
python3 research/run_runtime_checks.py
```

## Modules and actual guarantees

`continuity.py` is the finite in-memory belief reducer: explicit revisions, scoped claims, preserved history and immutable branches. `durable.py` reuses that reducer inside a SQLite transaction. It adds verified replay, a bounded hash-chained journal, retry identity, a global CAS head, versioned orientation, source retirement, context construction and decision admission.

`agent_cycle.py` delivers orientation and evidence in model messages, snapshots the request hash before calling the adapter, rejects adapter mutations, checks the explicitly selected model ID, parses a structured response, rejects unavailable citations and commits only while the original context is current. The request hash binds the input supplied to the adapter, not an authenticated provider transmission. Its `Model` protocol is a real integration seam. The supplied `ReplayModel` is an authored test double and performs no inference. A supplied external adapter is trusted code, not sandboxed by the protocol.

`durable_demo.py` reconstructs a scoped revision after reopening the database, then records a replay answer with bound request and response hashes. `test_durable.py` additionally uses real child processes for concurrent writes, fresh-process recovery and termination before commit. These are systems tests, not behavioral LLM trials.

## Integration example

With `examples/` on Python's import path, a caller explicitly supplies its chosen adapter:

```python
from agent_cycle import run_turn
from durable import Journal

# `chosen_model` is supplied by your application. Its complete(messages)
# method returns ModelReply with the exact selected route's model_id.
result = run_turn(
    Journal("your-owned-existing.sqlite"),
    turn_id="unique-turn-id", branch="main",
    topic="cache-current", scope="updates-A",
    question="What changed and what remains unknown?",
    model=chosen_model, expected_model_id="your-pinned-model-route",
)
```

The adapter owns provider authorization, credentials, data consent, deadline, cancellation, token and cost budgets. No adapter is installed, downloaded or selected automatically. Invalid or stale output is rejected without silent provider fallback or repair. The runtime does not execute model-proposed tools.

## Contract limits

The fixture is authored data, not observed agent behavior. The old fixed renderers demonstrate only textual form. The new orientation and prompt path make voice policy available to a model; they do not establish that it is enacted well. The book defines a separate behavioral rubric.

The negative entailment test is intentional: arbitrary prose with an existing basis passes structural checks. This explicitly demonstrates the gap between reference validation and semantic support. `supported` is an input label, not an independent truth verdict.

Actor names and `approved_by` are trusted caller assertions, not authenticated identities. Paths must be operator-owned. The SQLite runtime supports cooperative local writers and process-crash recovery. It does not establish a security boundary against arbitrary same-user Python/SQL, authenticate model providers or perform external-effect transactions. A valid chain alone cannot detect suffix deletion or coherent rewriting; an independently protected anchor can detect inconsistency with its known prefix.

The reference implementation is bounded to 4096 operations, 64 KiB per operation and 512–65536 bytes per context. Full replay and immutable dictionary copies favor inspectability at this size. They are not a million-record implementation. The book specifies a distinct indexed scaling path.

`research/runtime-results.json` records the checked Python source and JSON fixture hashes, test names and measured run. Publication checks reject missing inputs and changed fixture bytes. Reproduction overwrites only that report and may produce different timing and environment metadata. Neither hashes nor 68 current passing checks establish consciousness, identity or general behavioral benefit.

Full explanation: [finite reducer](../book/ua/08-model.md), [runtime architecture](../book/ua/09-runtime.md), [behavioral research protocol](../book/ua/05-research.md).

The separately operated [research adapter and study](../research/README.md) contain actual local model calls. They are not invoked by these examples or systems tests.

## Executable participation methods

`participation.py` interprets scoped dependency worlds and persists actual model attempts, refusals and local simulated effects in the existing SQLite/CAS journal. `participation_method.py` supplies a bounded decision-table language and operational budget planner; it never calls the study oracle. These add 19 checks to the earlier 49. [Full finite profile and source mapping](../ontology/FOUNDATION.md) · [32-call closed-loop study](../research/CLOSED_LOOP_STUDY.md). The graph adapter leaves unsupported semantic revision links absent. Neither a stored effect nor changed prose establishes beneficial formation.
