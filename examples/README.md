# Finite continuity projection example

Python 3.11+, standard library only. No installation, network, LLM calls, tool execution, database, or automatic profile changes.

From repository root:

```sh
python3 -m unittest discover -s examples -v
python3 examples/continuity.py
```

The fixture is authored data, not observed agent behavior. The model demonstrates explicit revisions, retained history, scoped claims, immutable branch states, duplicate delivery and conflict handling. Two fixed renderers preserve the same status text. Neither renderer evaluates voice or interaction quality.

The negative entailment test is intentional: arbitrary prose with an existing basis passes structural checks. This explicitly demonstrates the gap between reference validation and semantic support. `supported` is an input label, not an independent truth verdict.

Snapshot names are caller labels. The code does not authenticate actors, verify external evidence, prove identity, enforce permissions, persist state, handle concurrent writers or measure consciousness. The in-memory guarantees assume callers use these public constructors and functions; they do not establish a security boundary against arbitrary Python code.

Full explanation: [Ukrainian chapter](../book/ua/08-model.md).
