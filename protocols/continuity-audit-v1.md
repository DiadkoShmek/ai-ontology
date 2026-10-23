# Continuity audit — proposed profile v1, draft 0.1

**23 October 2026 · Artur Onysko · normative scope: supplied records only**
[Methodological note](../papers/inspectable-continuity.md) · [Terms](../docs/TERMS.md) · [Executable vocabulary](../ontology/vocabulary.json)

The requirement identifiers below name this proposed profile. They do not
establish industry adoption, certification or ownership of the underlying ideas.
MUST, SHOULD and MAY express requirements within this document.

## Inputs and effects

- **CA-01 — Input contract.** The auditor MUST accept the existing neutral graph
  wire format. The optional JSONL transport uses one explicit
  `{"kind":"node","record":NODE}` or `{"kind":"edge","record":EDGE}` per
  line, with an optional single trailing LF. Blank lines are invalid. NODE and
  EDGE have exactly the existing profile shapes. This
  is a projected-record interchange, not an arbitrary raw-log parser.
- **CA-02 — Admission.** Input MUST obey the current vocabulary's byte, node,
  edge, field and identifier bounds, strict UTF-8, unique JSON keys and finite
  numbers. Invalid input MUST fail with exit 2; it MUST NOT be silently repaired.
  Validation and queries MUST use the existing `ontology.graph` owner.
- **CA-03 — Provenance.** Reports MUST include the input SHA-256 and local
  profile version. A digest binds bytes, not authenticated origin. Exporters
  SHOULD separately document where declared relations came from.
- **CA-04 — No invented links.** The auditor MUST NOT infer use from availability,
  satisfaction from adoption, formation from storage, or a revision from a
  success receipt. It MUST NOT fetch references or execute source commands.

## Return-path report

For each `Decision.hasEffect`, use the canonical `returnPath` query. It joins
an observation of that effect, an assessment evaluating the effect and based
on such an observation, an accepted revision responding to the effect and
based on such an assessment, and a distinct decision adopting the revision.

- **CA-05 — Coverage.** `complete` requires nonempty returned paths, every path's
  `recordedPathComplete` true, and no orphan Effect nodes. `incomplete` denotes
  missing required links or an Effect with no incoming `Decision.hasEffect`.
  `no-recorded-effects` means zero Effect nodes. Empty data MUST NOT produce
  `not_applicable`, a successful learning verdict or a false-world conclusion.
- **CA-06 — Separate statuses.** A valid incomplete graph MUST exit 0, with its
  coverage status explicit. Process success MUST NOT be interpreted as quality,
  conformance of a foreign runtime or beneficial agent development.
- **CA-07 — Separate evidence levels.** Reports MUST retain canonical evidence
  use, criterion assessment, lesson use, authority and objection rows. Counts
  of graph `Claim.status` MUST NOT be labeled as the publication's `CLAIMS.md`
  status ledger. They are different vocabularies.
- **CA-08 — Bound the inference.** Completeness MUST be described as explicit
  recorded links only. It does not establish chronology, truth, authentic
  authority, causal influence, changed judgment, useful transfer or subjective
  experience. The report MUST state that those inferences were not tested.

`unsupported_inference` is a methodological judgment requiring an identified
assertion and evidence demand. This version does not accept arbitrary prose
claims or implement that judgment. `not_applicable` likewise requires external
task scope. Neither label is guessed from missing records.

## Commands and expected results

From the repository root, Python 3.11+ standard library, no model or network:

```sh
python3 -m audit.cli validate ontology/fixtures/closed-loop.json
python3 -m audit.cli report ontology/fixtures/closed-loop.json
python3 -m audit.cli report ontology/fixtures/open-loop.json
python3 -m unittest audit.test_audit -q
```

The authored closed fixture reports `complete`; the open fixture reports
`incomplete`. Both are valid. They explain the record contract and do not count
as LLM trials. Existing ontology tests separately exercise actual SQLite
commit/reopen/readback through the runtime adapter:

```sh
python3 -m unittest discover -s ontology -p 'test_runtime_adapter.py' -q
python3 ontology/runtime_adapter.py --store PERMITTED_STORE --turn-id TURN_ID --question returnPath
```

The second command reads a compatible existing store. Supply a store you are
authorized to inspect. It does not export arbitrary providers or create missing
links. That adapter can report an incomplete return path despite actual durable
effects. This is a useful distinction, not an auditor failure.

## Extension and change control

An exporter MAY project records from another runtime. It MUST preserve missing
relationships as missing, distinguish source observation from interpretation,
and state which evidence it cannot supply. The optional native LangGraph
checkpoint route preserves actual snapshots as Observations and infers no
participation links. Its authored local example is separate from an LLM trial,
cross-process durability or external adoption. Letta and OpenTelemetry-specific
exporters are not qualified here. An input JSONL file already declaring ontology
relations is not evidence of automatic foreign-log integration.

Changes to these requirements require a dated revision with compatibility and
counterexample notes. Existing frozen studies retain their original contracts.
A local passing suite is implementation evidence, not independent conformance
certification or a guarantee of world truth.
