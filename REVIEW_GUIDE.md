# A short route for technical review

This book combines an ontological framework with a runnable reference architecture. It contains bounded systems tests, a provider-independent model-turn interface and a separate research programme for agent behavior. It does not claim consciousness or measured behavioral benefit. Ukrainian full text; [English abstract](ABSTRACT.en.md).

## The claim to examine

Identity, voice, memory and relationships can be examined as interacting aspects of an agent's organization across tasks. A coherent account should explain both continuity and justified revision. The proposed composition is open to comparison with simpler designs; its practical benefit remains unmeasured.

## A focused reading route

1. [Five central theses](https://diadkoshmek.github.io/ai-ontology/#foundations-3): the conceptual position.
2. [Continuity](https://diadkoshmek.github.io/ai-ontology/#continuity): perspective-specific contracts, witnesses, non-transitivity and information loss.
3. [Implementation](https://diadkoshmek.github.io/ai-ontology/#engineering): mapping to state, context, memory and revision, with concrete failures and costs.
4. [Iris](https://diadkoshmek.github.io/ai-ontology/#iris): one constructed history across multiple kinds of change.
5. [Objections](https://diadkoshmek.github.io/ai-ontology/#cases-7): parsimony, circular evaluation, language, normative choices and identifiability.

## What is executable

```sh
python3 -m unittest discover -s examples -v
python3 examples/durable_demo.py
python3 research/run_runtime_checks.py
```

The included runtime and replay adapter have no network access or external dependencies. An explicitly supplied real model adapter is trusted executable code and must have its own effect and budget policy. Its intentional negative entailment case demonstrates that a valid reference is insufficient to establish support for arbitrary prose. Fixed voice renderers do not evaluate LLM voice. Actor and snapshot labels are not authentication.

## Useful objections

- Does the proposed ontology explain a relevant distinction that a simpler profile and event store do not?
- Does the perspective-specific continuity relation remain useful without pretending to solve numerical identity?
- Are constructed examples clearly separated from observed system behavior?
- Do the research conditions control for extra information, style and resource budget?
- Which concept could be removed without loss, and what concrete counterexample would reveal the loss?

The source of each chapter is listed in [edition.json](edition.json). [Sources and contribution](book/ua/06-references.md) distinguish definitions, arguments, implementation facts and untested hypotheses. [AUTHORS.md](AUTHORS.md) discloses substantial AI-assisted writing. No independent peer review is claimed.

## Engineering entry

Read [the runtime chapter](book/ua/09-runtime.md), [code and run guide](examples/README.md), [test report](research/runtime-results.json), and the actual `durable.py` / `agent_cycle.py` paths. Verify systems correctness separately from source delivery, model behavior and human benefit. The current implementation is bounded full replay; its indexed scaling design is specified, not benchmarked at a million records.
