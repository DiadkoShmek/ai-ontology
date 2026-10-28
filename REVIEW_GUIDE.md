# Technical review guide

*AI Ontology* combines a conceptual methodology, an executable specification and several bounded evaluations. The complete book is available in [Ukrainian](BOOK_UA.md) and [English](BOOK_EN.md); the [abstract](ABSTRACT.en.md) and research papers on [scoped continuity](research/SCOPED_CONTINUITY_STUDY.md) and [reading-mediated transfer](research/READING_TRANSFER_STUDY.md) are also in English. The [reader note](READER_NOTE.md) distinguishes this work from other projects by the author and from generic descriptions of ontology or evidence gating.

## The proposition

Identity, voice, memory and relationships can be examined as interacting aspects of an agent's organization across tasks. A useful account should explain continuity, justified revision, provenance and the conditions of change. Each implemented distinction should reach a concrete transition, and each claimed benefit should survive a simpler matched-information baseline.

## Reading routes

**Methodology:** [conceptual foundations](https://diadkoshmek.github.io/ai-ontology/#foundations) → [continuity](https://diadkoshmek.github.io/ai-ontology/#continuity) → [objections](https://diadkoshmek.github.io/ai-ontology/#cases) → [implementation method](https://diadkoshmek.github.io/ai-ontology/#method).

**Formation:** [event, lesson and judgment](book/ua/05-formation.md) → the exact historical reports linked in that part → the current claim map's C12. Distinguish the observed source repair, an authored explanatory case and a claim about a model's changed behavior. The part makes no inference from editorial continuity to general model learning.

**Engineering:** [runtime chapter](book/ua/09-runtime.md) → [modules and commands](examples/README.md) → [systems report](research/runtime-results.json) → actual `durable.py` and `agent_cycle.py` contracts.

**Practice:** [historical function excerpts and replay](research/engineering_cases/receipt_replay.py) → [extraction provenance](research/engineering_cases/provenance.json) → [two reproduced failure comparisons](research/engineering-cases-results.json). These are retrospective component tests with injected faults around real temporary SQLite/file effects, separate from the constructed Iris dialogue and the LLM cohorts.

**Empirical evaluation:** [working paper](research/SCOPED_CONTINUITY_STUDY.md) → [protocols and raw data](research/README.md) → [follow-up results](research/continuity_pilot_v2/results.json) → [offline verifier](research/verify_studies.py).

**Instrument validity:** [profile qualification](research/PROFILE_PARTICIPATION_STUDY.md) → [replacement transfer design](research/TRANSFER_STUDY_DESIGN.md) → [accepted V3 calibration](research/transfer_calibration_v3/PROTOCOL.md) → [main registered pipeline](research/transfer_reading/PROTOCOL.md). The 100/100 GPT ceiling does not validate the broader book-reading hypothesis.

## Results to challenge

[Claims and evidence](CLAIMS.md) is the short route from each assertion to its
status, executable check and limit. The [transport repair](research/HANDOFF_REPAIR_REPORT.md)
has a separate 24-call cohort: 8/8 fully traced completions versus 0/8 freeform,
with 5/8 freeform planning-only successes. Neither arm read the book. The
[generic-file control](research/handoff_controls/README.md) establishes input
parity without new model calls and exposes a capacity failure. The
[practical command](practical/README.md) exercises actual repository gates and
controlled source drift, with a larger explicit transport bound and a shared
checkout. These observations do not replace the negative reading result below.

The reading-transfer primary is a partial-task measure: ordinary 12/16, book 8/16, guide 10/16, unrelated 10/16. Fully traced optimal completion is 0/16, 0/16, 1/16 and 0/16. Five empty book answers name the optimal work set while withholding the plan for missing citations. Challenge the endpoint’s construct validity and the lossy communication channel as well as the observed condition difference. The post-cohort diagnosis does not replace registered scores.

The follow-up exact scores are 20/16/16/20 for Qwen3 4B and 5/2/12/12 for Granite 3.3 2B across journal, ontology wrapper, compiled context and simple index. There is no observed aggregate advantage over the information-matched simple index. Compilation includes deterministic preprocessing; ontology framing adds text. The cases are authored, short, dependent and reused after the first instrument failure.

Both compact conditions use the same compiler and preserve the substantive relations. This is a presentation control, not an independent memory implementation or a test of removing provenance, scope and revision. Sorted keys also leave naming and ordering confounded.

The 49 systems tests establish bounded transition behavior. The original 384 scored model calls evaluate structured decisions. A separate 136-call local qualification and 100-call completed GPT qualification retain their own denominators; a 53-reply interrupted GPT instrument is preserved. The main reading-transfer study has a separate denominator, actual preparation before the unseen task, and a common receiver behind a truncated handoff. It concerns ten selected book parts, not the entire book. Original-count references below are scoped to the continuity study. The two integration smoke calls exercise a live adapter path. These are different evidence classes. Natural voice, subjective identity, long-run interaction and natural-task benefit are not measured by those earlier counts. The reading-transfer estimand is narrower than those questions.

## Reproduce without inference

```sh
python3 -m unittest discover -s examples -q
python3 -m unittest discover -s research/continuity_pilot -q
python3 -m unittest discover -s research/continuity_pilot_v2 -q
python3 -m unittest discover -s research -p 'test_integrity.py' -q
python3 -m unittest discover -s research/engineering_cases -q
python3 research/verify_studies.py
python3 research/verify_participation.py
python3 research/verify_gpt_profiles.py gpt_profile_pilot
python3 research/verify_gpt_profiles.py gpt_profile_pilot_v2
python3 -O research/verify_reading_transfer.py
```

Python 3.11+ and Git. These checks make no network or model calls. The verifier reconstructs frozen source from the full local historical Git clone (bundle downloads withdrawn for author privacy), checks all prompts and scores, and reruns the registered analysis in temporary storage.

## Useful objections

The [living-participation chapter](book/ua/03-living.md) develops a conceptual
and normative distinction between preserving the agent and sustaining another
participant's possibilities. Its workshops are constructed cases, not human
trials. Challenge the criterion itself: ongoing assistance can increase agency,
and competent use of a system need not end in independence from it. The book's
LLM cohorts do not measure these human outcomes.

Claim IDs and their status history live in [the existing map](CLAIMS.md).
To propose a status revision, preserve previous entries, name a newer edition,
give a reason and cite evidence at an existing full Git commit. The build
rejects broken history and unavailable source paths. It does not judge semantic
support or silently validate a changed meaning. Nine editorial checks include
an intentionally accepted unsupported assertion with an existing source path.

- Which proposed distinction changes a relevant transition, and which can be removed without loss?
- Does the continuity contract remain useful while leaving numerical identity unresolved?
- Are deterministic state guarantees kept separate from model use and useful completion?
- Does the simple index control preserve the information relevant to the stated question?
- Does the reading result depend on preparation, reference-runtime rehearsal, truncation order or exact citation copying?
- Which unseen cases would falsify the proposed practical interpretation?
- Can continuity pass while the other participant loses influence over the ends?
- Does an appeal to care itself override an informed, legitimate choice?

A valid citation does not establish semantic support. An anchor detects inconsistency with a trusted prefix but does not authenticate every claim. The runtime uses bounded full replay; indexed scaling is a specified extension, not a million-record benchmark. The model adapter is trusted executable code, not a sandbox.

[Chapter sources](edition.json) · [Authorship and AI contribution](AUTHORS.md). Independent review and replication remain welcome; neither is claimed in this edition.
