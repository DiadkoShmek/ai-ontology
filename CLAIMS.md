# Claims and their evidence

This map separates the book's conceptual proposal, implemented mechanisms and
observed outcomes. It is an entry point for criticism, not a quality rating.

| Claim | Evidence and reproduction | Status and boundary |
|---|---|---|
| Scope, revision, provenance and retirement must remain distinguishable when a later decision depends on them. | [Finite reducer](examples/continuity.py), [durable runtime](examples/durable.py), [systems tests](research/runtime-results.json). Run `python3 -m unittest discover -s examples -q`. | Implemented finite transition rules and authored counterexamples. These mechanisms have predecessors in TMS, AGM, event sourcing and provenance systems; structural validity is not semantic truth. |
| Different histories can become indistinguishable after removing a decision-relevant edge. | Counterfactual source pairs and flat control in [transfer tasks](research/transfer_calibration_v3/tasks.py). | A finite information-loss witness. It is not a new information-theoretic theorem or a general theory of identity. |
| Reading the supplied conceptual/engineering chapters improves later task performance. | [Reading-transfer study](research/READING_TRANSFER_STUDY.md): ordinary 12/16, book 8/16 submitted optimal plans; fully traced completion 0/16 in both. | **Not supported in the registered setting.** The result concerns the supplied dose and lossy workflow, not the usefulness of every idea or general reasoning ability. |
| Exact accessible evidence can repair the demonstrated handoff failure. | [Repair report](research/HANDOFF_REPAIR_REPORT.md): 8/8 fully traced optimal completions versus 0/8 freeform, 24 captured calls. Run `python3 -O research/verify_handoff_repair.py`. | Observed on eight new instances of one known generator, developer-controlled. The intervention uses conventional compression and removes the sender-model stage. |
| The codec improves on a generic shared file with the same data. | [File control and limits](research/handoff_controls/README.md). | **No such superiority is established.** Where both restore the full history, canonical data and receiver prompts are identical. The measured codec advantage is fitting the chosen narrow transport, not uniquely useful semantics. |
| Exact transport always fits a small context. | [Fixed-capacity cases](research/handoff_controls/results.json). | **False.** Eight variable-log additions exceed the 3200-byte cap; transmission stops. Larger history requires an explicitly different storage contract. |
| A real repository's checks can survive a process boundary without silently certifying changed source. | [Practical continuation](practical/README.md), [captured check and drift result](practical/publication-handoff-results.json). | Actual offline gates and per-file readback on this repository, with controlled drift in a temporary copy. Shared checkout required; no natural LLM trial, global atomic source snapshot or independent attestation. |
| A stable voice can be expressed through attention, disagreement and revision rather than characteristic phrases. | [Conceptual core](book/ua/01-core.md), [Iris and Orion](book/ua/07-iris.md), [research programme](book/ua/05-research.md). | Conceptual definition and authored cases. Stable individual voice in natural model use remains an empirical question. |
| A change may satisfy a new criterion while losing a property required by the old one. | [Continuity](book/ua/04-continuity.md), [method](book/ua/10-method.md). | Conditional argument and proposed recording discipline. No universal automatic evaluator of arbitrary normative criteria is implemented. |
| Functional continuity proves subjective experience or a soul. | The book distinguishes functional organization, normative treatment and subjective experience. | **Not claimed.** The tests do not detect consciousness or private feeling. |
| The implementation is a production memory system or a measured boost to the live House. | [Package bounds](examples/README.md), [transport bounds](research/handoff_repair/README.md). | **Not established.** Bounded reference implementation, finite checks and explicit experimental adapters; no million-record benchmark or live House adoption claim. |

## How to challenge a claim

Name the row and exact source revision, give the smallest reproducible failure,
and state which conclusion it contradicts. A failed mechanism test, an empirical
counterexample and a disagreement with a normative proposal call for different
repairs. New outcomes remain separate from older cohorts; a later positive
engineering result does not replace a negative reading result.

Concept and editorial direction: Artur Onysko. Codex substantially contributed
text, software, study design, execution and analysis under the author's direction.
[Authorship](AUTHORS.md) and [review route](REVIEW_GUIDE.md) remain explicit.
