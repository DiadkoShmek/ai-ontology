# AI Ontology: The Organization of Self

**Artur Onysko · Book v3.6.0 · English and Ukrainian**

A research book, proposed audit profile and executable reference for inspecting claims about **agent continuity, evidence and revision**. Which grounds reached a decision? What followed from it? Did a consequence enter a subsequent method, and what evidence supports that claim?

**[Short methodological note](papers/inspectable-continuity.md)** · **[Audit a projected run](audit/README.md)** · [Proposed profile](protocols/continuity-audit-v1.md) · [Terms](docs/TERMS.md) · [Claims](CLAIMS.md)

**[Read the complete English book](https://diadkoshmek.github.io/ai-ontology/en/)** · **[Читати українською](https://diadkoshmek.github.io/ai-ontology/)** · [English PDF](docs/downloads/ai-ontology-book-01-en.pdf) · [Український PDF](docs/downloads/ai-ontology-book-01-uk.pdf) · [Український README](README.uk.md)

## Four distinctions

| Keep separate | Question |
|---|---|
| Available evidence / recorded use | Was material accessible, or is its use actually recorded? |
| Criterion adoption / satisfaction | Was this version accepted, and was it met? |
| Stored lesson / formation | Did anything change beyond the memory record, and did that help? |
| Recorded effect / complete recorded return path | Are the intervening assessment, revision and consumer links present? |

```text
Decision → Effect → Observation → Assessment → Accepted revision → Distinct consuming decision
```

The diagram summarizes required relations; it does not prove chronology or causality. The graph's `recordedPathComplete` checks explicit links. A complete path does not establish beneficial learning, truth, authenticated authority or subjective experience. The book's broader questions of identity, voice and participation remain distinct from this finite audit.

## Try it without a model

Python 3.11+ standard library; run from the repository root:

```sh
python3 -m audit.cli report ontology/fixtures/closed-loop.json
python3 -m audit.cli report ontology/fixtures/open-loop.json
python3 -m unittest audit.test_audit -q
```

Expected coverage: **complete** then **incomplete**. Both authored fixtures are valid and exit 0; invalid input exits 2. They are explanatory cases, not LLM trials. Reports include source SHA-256, missing links and eight competency queries. Projected JSONL is supported; arbitrary raw logs and framework-specific exports require an explicit adapter. [Contract and limits](protocols/continuity-audit-v1.md).

An optional [native LangGraph example](audit/README.md) captures actual checkpoint history from authored deterministic nodes. Its adapter preserves Observations and leaves participation links unrecorded. No model or external effect is implied.

## What is implemented

- [Finite ontology](ontology/README.md): 18 classes, 34 relations, eight queries, neutral JSON and JSON-LD/Turtle exports. No general OWL reasoner or SHACL processor.
- [Python reference](examples/README.md): scoped claims, provenance, bounded SQLite/CAS durability and a model cycle. The [actual-store adapter](ontology/runtime_adapter.py) preserves missing evidence.
- [Book](BOOK_EN.md): sixteen parts on identity, voice, memory, relationships and revision, with separate Ukrainian and English editions.
- [Concept-to-code map](ontology/FOUNDATION.md) and [review guide](REVIEW_GUIDE.md).

This is a developer-controlled research reference and proposed profile, not a production memory service, adopted standard or independently replicated finding. Structural validity is not semantic entailment. Persistent records do not detect consciousness or prove a soul.

## Results remain visible

| Study | Observed result | Boundary |
|---|---|---|
| [Scoped-memory presentation](research/SCOPED_CONTINUITY_STUDY.md) | 384 scored local-model calls; compiled context did not generally beat an information-matched index | Narrow representation comparison |
| [Reading-mediated transfer](research/READING_TRANSFER_STUDY.md) | Ordinary optimal plans 12/16, book 8/16; fully traced completion 0/16 in both | Registered reading intervention did not improve the primary |
| [Exact handoff repair](research/HANDOFF_REPAIR_REPORT.md) | Fully traced optimal completion 8/8 exact versus 0/8 freeform | One known class; an accessible generic file restores the same data |
| [Executable-method cycle](research/CLOSED_LOOP_STUDY.md) | Both arms reached the ceiling; M0 and M1 each 192/192 optimal transfer per arm; zero changed plans | No beneficial revision or added-view advantage observed |
| [Scoped evidence return](research/EPISTEMIC_RETURN_STUDY.md) | 72 scored GPT calls plus one canary; free notes 77/80, linked notes 71/80 | Same 2048-byte allowance; 6/8 versus 2/8 actual-feedback notes admitted |

The latest linked-format result is negative. Notes exceeding the bound were unavailable, not silently truncated. Actual feedback changed source decisions; masked branches retained appropriate uncertainty. No simulated harmful effects occurred. This is a concrete retention failure, not proof of a new algorithm or general ontology benefit. [Ukrainian report](research/EPISTEMIC_RETURN_STUDY.uk.md).

[Protocols, raw outputs, costs and offline reanalysis](research/README.md) are available. The supplementary data do not change book v3.6.0. Claim IDs include **C03 unsupported**, **C06 refuted** and **C10 not-claimed**; see [the exact ledger and history](CLAIMS.md).

## Reproduce and inspect

```sh
python3 -m unittest discover -s examples -q
python3 -m unittest discover -s ontology -p 'test_*.py' -q
python3 ontology/export.py --check
python3 -O research/epistemic_return/analyze.py
```

Book sources: `book/ua/`, `book/en/`; ordering: `edition.json`. Build both web editions with Node.js 22+: `npm ci --ignore-scripts`, `npm run build`, `npm run check`. [PDF build and full research instructions](research/README.md).

## Authorship and participation

Conceptual direction, research questions and editorial intent: **Artur Onysko**. **Codex** substantially contributed writing, software, study design, execution, analysis and translation. Private Architect-Ψ council informed the work; it is not independent empirical replication. [Authorship](AUTHORS.md) · [Reader note](READER_NOTE.md) · [Changelog](CHANGELOG.md) · [Book citation](CITATION.cff) · [Note citation](papers/inspectable-continuity.bib).

The proposed connected methodology has precedents in truth maintenance, AGM belief revision, provenance, event sourcing and reflective agents. World-first novelty is not claimed. Reproducible issues, objections and permitted failure cases are welcome through GitHub Issues.

© 2026 Artur Onysko. All rights reserved. Public availability does not itself grant an open-source license.
