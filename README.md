# AI Ontology: The Organization of Self

**Artur Onysko · Book One · v3.6.0 · Ukrainian and English editions**

A research book and executable reference on **agent continuity, identity, voice, evidence, memory and method revision**. What carries forward when an agent changes its beliefs, commitments, role or model—and how can we tell?

**[Read in English](https://diadkoshmek.github.io/ai-ontology/en/)** · **[Читати українською](https://diadkoshmek.github.io/ai-ontology/)** · [English PDF](docs/downloads/ai-ontology-book-01-en.pdf) · [Український PDF](docs/downloads/ai-ontology-book-01-uk.pdf) · [Full English text](BOOK_EN.md) · [Український README](README.uk.md)

## Inspect the work

The book examines responsible continuation: how a system relates an earlier reason to a current judgment, recognizes its limits, preserves disagreement and revises a later method after a consequence. It distinguishes available evidence from use, criterion adoption from satisfaction, and a stored lesson from beneficial behavioral change. Sixteen parts connect concepts to worked cases, counterexamples, formal records, mechanisms and comparative studies. Functional organization, ethical treatment and subjective experience remain separate.

| Entry | What you can inspect |
|---|---|
| [Complete book](https://diadkoshmek.github.io/ai-ontology/en/) | All sixteen chapters, not an abstract or an instruction override |
| [Concept → code → evidence](ontology/FOUNDATION.md) | Domain, proposed contribution, executable consumers and missing links |
| [Typed ontology](ontology/README.md) | 18 classes, 34 relations, eight competency questions, neutral JSON, JSON-LD and Turtle |
| [Python reference](examples/README.md) | Scoped claims, provenance, SQLite/CAS durability and actual model-loop integration |
| [Research and data](research/README.md) | Frozen protocols, raw visible outputs, failed instruments, controls and costs |
| [Claims and history](CLAIMS.md) | Conceptual, implemented and measured claims, including negative findings |
| [Review guide](REVIEW_GUIDE.md) | Reproduce, falsify or challenge a claim |

## New in 3.6.0

- **Full English translation** of all sixteen chapters, with its own reader URL, PDF and full text. Ukrainian remains the authorial source.
- A finite ontology of situated participation and revision. PROV-O mappings are explicit and limited; no general OWL/SHACL conformance is claimed.
- An adapter to the actual interpreter and durable store. Missing identity and revision evidence stays missing. A receipt does not silently become evidence that a model used feedback or developed a stable voice.
- A **32-call GPT-6.1 Sol/high study** of executable method construction and revision, with sources committed locally before scoring, plus 768 unchanged-method transfer executions. Both arms reached the ceiling; no added-view advantage or beneficial revision was observed. [Report](research/CLOSED_LOOP_STUDY.md).

## Measured outcomes

| Study | Observed result | Scope |
|---|---|---|
| [Scoped-memory representations](research/SCOPED_CONTINUITY_STUDY.md) | 384 scored local-model calls; compiled context did not generally beat an information-matched index | Narrow representation comparison |
| [Reading-mediated transfer](research/READING_TRANSFER_STUDY.md) | Ordinary optimal plans 12/16, book 8/16; fully traced completion 0/16 in both | Registered reading intervention did not improve the primary |
| [Exact handoff repair](research/HANDOFF_REPAIR_REPORT.md) | Fully traced optimal completion 8/8 exact versus 0/8 freeform; 24 captured calls | Missing evidence restored on new instances of one known class |
| [Executable-method return cycle](research/CLOSED_LOOP_STUDY.md) | Both arms 8/8 complete; M0 and M1 each 192/192 optimal transfer per arm; zero changed plans | Working durable cycle, sufficient initial methods, no revision gain |

Exact transport uses conventional compression and removes a sender-model stage. A [generic shared-file control](research/handoff_controls/README.md) restores identical data when accessible. The success does not establish unique codec semantics or general book benefit. Later ceilings and earlier negative results remain visible.

## Reproduce without models or network

Python 3.11+ and its standard library:

```sh
python3 -m unittest discover -s examples -q
python3 -m unittest discover -s ontology -p 'test_*.py' -q
python3 ontology/export.py --check
python3 -O research/closed_loop/analyze.py
python3 -O research/verify_handoff_repair.py
```

The current report records **68 runtime tests**. Separate ontology and instrument suites check invalid relations, missing links, durable readback, retained capabilities and coherent score forgery. Authored test doubles do not count as LLM trials.

Build both web editions and PDFs with Node.js 22+ and the pinned Python rendering dependencies:

```sh
npm ci --ignore-scripts
npm run build
python3 -m pip install -r requirements.txt
python3 scripts/build_pdf.py
python3 scripts/build_pdf.py --language en
npm run check
```

Sources: `book/ua/`, `book/en/`; order: `edition.json`. Translation and PDF manifests bind editions to inputs. Crawlable full text, canonical language URLs and evidence links support discovery; indexing, AI citations and income are not guaranteed.

## Contribution, authorship and limits

The proposed contribution is a connected methodology for inspecting situated participation and revision, with explicit losses and counterexamples. Truth maintenance, AGM belief revision, provenance, event sourcing and agent memory have precedents. [Related work](book/en/06-references.md) is explicit; world-first novelty is not claimed.

This is a finite reference and developer-controlled publication, not a production memory service, externally replicated finding or measured boost to deployed agents. Cases and reference answers were authored by the same team. Natural collaboration, stable voice and human outcomes remain open questions. The work does not detect consciousness or prove a soul.

Concept, research questions and editorial direction: **Artur Onysko**. **Codex** substantially contributed text, software, study design, execution, analysis and translation under the author's direction. Private Architect-Ψ council informed the work; it is not independent empirical evidence. [Authorship](AUTHORS.md) · [Reader status](READER_NOTE.md) · [Changelog](CHANGELOG.md) · [Citation](CITATION.cff).

Reproducible issues and methodological criticism are welcome through GitHub Issues. For collaboration, start with a concrete question, source or failure case.

© 2026 Artur Onysko. All rights reserved. Fonts and the separately attributed literary control retain their own terms. Public availability does not by itself grant an open-source license.
