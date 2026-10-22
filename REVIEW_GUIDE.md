# Technical review guide

*AI Ontology* combines a conceptual methodology, an executable specification and a local exploratory study. The book is in Ukrainian; the [abstract](ABSTRACT.en.md) and [research paper](research/SCOPED_CONTINUITY_STUDY.md) are in English.

## The proposition

Identity, voice, memory and relationships can be examined as interacting aspects of an agent's organization across tasks. A useful account should explain continuity, justified revision, provenance and the conditions of change. Each implemented distinction should reach a concrete transition, and each claimed benefit should survive a simpler matched-information baseline.

## Reading routes

**Methodology:** [conceptual foundations](https://diadkoshmek.github.io/ai-ontology/#foundations) → [continuity](https://diadkoshmek.github.io/ai-ontology/#continuity) → [objections](https://diadkoshmek.github.io/ai-ontology/#cases) → [implementation method](https://diadkoshmek.github.io/ai-ontology/#method).

**Engineering:** [runtime chapter](book/ua/09-runtime.md) → [modules and commands](examples/README.md) → [systems report](research/runtime-results.json) → actual `durable.py` and `agent_cycle.py` contracts.

**Empirical evaluation:** [working paper](research/SCOPED_CONTINUITY_STUDY.md) → [protocols and raw data](research/README.md) → [follow-up results](research/continuity_pilot_v2/results.json) → [offline verifier](research/verify_studies.py).

## Results to challenge

The follow-up exact scores are 20/16/16/20 for Qwen3 4B and 5/2/12/12 for Granite 3.3 2B across journal, ontology wrapper, compiled context and simple index. There is no observed aggregate advantage over the information-matched simple index. Compilation includes deterministic preprocessing; ontology framing adds text. The cases are authored, short, dependent and reused after the first instrument failure.

The 49 systems tests establish bounded transition behavior. The 384 scored model calls evaluate structured decisions. The two integration smoke calls exercise a live adapter path. These are different evidence classes. Voice, the effect of reading, identity, long-run interaction and natural-task benefit are not measured by those counts.

## Reproduce without inference

```sh
python3 -m unittest discover -s examples -q
python3 -m unittest discover -s research/continuity_pilot -q
python3 -m unittest discover -s research/continuity_pilot_v2 -q
python3 research/verify_studies.py
```

Python 3.11+ and Git. These checks make no network or model calls. The verifier reconstructs frozen source from the local history bundle, checks all prompts and scores, and reruns the registered analysis in temporary storage.

## Useful objections

- Which proposed distinction changes a relevant transition, and which can be removed without loss?
- Does the continuity contract remain useful while leaving numerical identity unresolved?
- Are deterministic state guarantees kept separate from model use and useful completion?
- Does the simple index control preserve the information relevant to the stated question?
- Which unseen cases would falsify the proposed practical interpretation?

A valid citation does not establish semantic support. An anchor detects inconsistency with a trusted prefix but does not authenticate every claim. The runtime uses bounded full replay; indexed scaling is a specified extension, not a million-record benchmark. The model adapter is trusted executable code, not a sandbox.

[Chapter sources](edition.json) · [Authorship and AI contribution](AUTHORS.md). Independent review and replication remain welcome; neither is claimed in this edition.
