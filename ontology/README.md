# Scoped participation ontology — finite profile 1.0.0

This directory makes a bounded part of *AI Ontology*, book 3.6.0, machine-readable. It names entities and typed relations needed to ask how a stated orientation, evidence, judgment, objection and consequence connect. It includes executable record constraints and competency questions, rather than treating a diagram or vocabulary as evidence that an agent improved.

The domain is **records of situated participation and revision**. `runtime_adapter.py` also projects the repository's actual `examples/participation.py` interpreter and durable readback into this graph; the link is exercised against generated study worlds and a real temporary SQLite commit/reopen/read cycle. This is not a complete ontology of persons, intelligence or consciousness. The vocabulary is an authored formalization, not a claim that its component mechanisms are novel. Its adequacy can be challenged by finding a relevant case it cannot distinguish, an invalid inference made by a query, or a simpler representation that preserves the same distinctions.

## Run from the repository root

Python 3.10+ and its standard library are sufficient. The commands read local files and use no model, service or network.

```sh
python3 ontology/graph.py ontology/fixtures/closed-loop.json
python3 ontology/graph.py ontology/fixtures/closed-loop.json --question returnPath
python3 ontology/graph.py ontology/fixtures/open-loop.json --question returnPath
python3 ontology/export.py --graph ontology/fixtures/closed-loop.json
python3 ontology/export.py --check
python3 -m unittest discover -s ontology -p 'test_*.py' -v
```

`graph.py` exits 0 for an admitted record profile and 2 for invalid input. An empty valid graph is permitted: no record is not proof of a false proposition. `export.py` without arguments regenerates `context.jsonld` and `vocabulary.ttl` from the authoritative `vocabulary.json`; `--check` compares them without writing. Tests include subprocess calls, malformed files, adversarial graph mutations and a 1,500-node version chain.

## What the vocabulary distinguishes

| Book distinction | Representation | What does not follow |
|---|---|---|
| Participant, carrier and execution | `Actor`, `Model`, `Profile`, `Session`; `madeBy`, `runsModel`, `usesProfile` | Same model or name does not establish the same participant or behavior. |
| Purpose and evaluation | Versioned `Orientation`, `Criterion`, `Scope` | A declared purpose is not an observed priority. |
| Criterion adoption and satisfaction | Criterion `acceptance`; separate `Assessment` under that exact criterion | An accepted criterion can be violated. A replacement does not erase the old assessment. |
| Proposition and evidence | `Claim`, `Observation`, `supportedBy` | Status `accepted` is not truth; a typed support link is not semantic entailment. |
| Accessible and actually used material | `availableEvidence` versus `usedRecord` | Access does not prove use; recorded use does not isolate causal influence. |
| Current applicability | `Applicability` with `applies`, `does-not-apply`, `unknown` | Retrieval, similarity or an adopted lesson does not establish applicability. |
| Judgment and consequence | `Decision`, `Effect`, `observesEffect`, `Assessment` | A reported association is not an identified causal effect. |
| Correction and permission | `Revision` versus `Authority` and explicit `governedBy` | Accepting a revision gives no action warrant to a subsequent decision. |
| Otherness and objection | `Objection`, `attributedTo`, `challenges`, `respondsTo` | An objector's identity or disagreement is not erased by rejecting their proposal. |
| Stored lesson and formation | `Lesson`, explicit use and revision-consumer paths | A stored, cited or used lesson does not establish changed judgment, durable voice or benefit. |

All 18 classes and 34 relations have definitions and book file/numbered-section mappings in `vocabulary.json`. Fields (including explicitly optional source content), enums, mandatory and optional single relations, domain/range alternatives and finite size limits are explicit there. Each node has exactly one local type. The classes are disjoint **in this wire profile** to avoid silently treating a profile as a model or authority; this is not an OWL disjointness claim about all possible entities.

The book's broader terms **center**, **identity**, **voice** and **integrity** are not given magic nodes whose existence would establish those properties. Their current operational projections are orientation and criterion selection, version/provenance relations, observable decisions and objection/revision histories. Claims of stable voice or beneficial formation require additional observations and comparative studies. The vocabulary also does not yet model institutions, economic constraints, every kind of source, continuous time or rights adjudication.

## Neutral graph wire format

```json
{
  "nodes": [{"id": "scope:test", "type": "Scope", "data": {
    "label": "Test scope", "description": "An authored local case"
  }}],
  "edges": []
}
```

IDs are case-sensitive bounded local identifiers. Node and edge keys are exact; unknown fields/types/relations, duplicate IDs/edges, dangling endpoints and wrong domain/range types are rejected. A version predecessor must have the same local type and the predecessor graph must be acyclic. This is a finite **closed-record shape contract**, not an open-world reasoner.

Additional coherence checks bind a decision's actor to its session, acceptance records to a warrant's stated holder/scope/action kind when a warrant is supplied, applicability to the target decision's scope and assessments to the named criterion's scope. They check what the records say, not whether an actor really had the claimed right. An `Authority` node cannot authenticate its grantor, create permission or authorize a tool call. An accepted but false claim remains structurally admissible; a test deliberately checks this boundary.

The validator imposes at most 2,048 nodes, 8,192 edges, 2 MiB per JSON input file, 8,192 characters per field and 128 characters per ID. There is no persistence, transaction protocol, authentication or concurrent-write service here. Rewriting a file is not an append-only history guarantee. `sourceRef` is a descriptive string; no referenced file or URL is fetched or trusted automatically. Vocabulary files are trusted local program inputs, not untrusted extension packages.

Decision session, model and profile metadata remain absent when the source does not contain them. Criterion acceptance may be recorded without a warrant: the record can describe unauthorized adoption. A supplied warrant must still have a coherent holder, scope and action kind. Unknown actor kind or unknown criterion acceptance is explicit. An objection ID without a target or author is retained with those relationships unrecorded.

`Observation.availability` is a recorded availability state, not an access-control rule. `usedRecord` can coexist with a missing/withdrawn current record because historical use and later availability may differ. The graph does not reconstruct that temporal sequence; the query exposes both records without repairing the discrepancy. Likewise, a decision record can describe an unauthorized action without the validator becoming an action permission gate.

## Nine competency questions

`competency-questions.json` supplies their definitions, book sources and exact expected query rows for authored fixtures. `graph.py --question NAME` implements only these explicit joins:

1. `identity`: which actor/model/profile are recorded for a session?
2. `criterionAssessment`: which criterion version was used, was it adopted, and what was the separate assessment result?
3. `evidenceUse`: which Observations were recorded accessible and which were recorded used?
4. `lessonUse`: which lessons have a recorded decision use and which remain stored?
5. `applicability`: what is the explicit applicability judgment for a record in the current decision?
6. `authority`: what action warrants are recorded separately from adopted corrections?
7. `objections`: who challenged which target and which revisions respond?
8. `returnPath`: is there a recorded path through an effect, its observation, an assessment using that observation, an accepted revision responding to that effect and based on that assessment, and a distinct consuming decision?
9. `claimUse`: which exact Claim records have explicit consuming Decisions, reported Effects and reportedly affected Actors?

`claimUse` preserves the exact `usedRecord` target. A newer Claim with independent
grounds does not replace the older version named by a historical Decision.
`claimStatus`, supporting Observations and previous versions are supplied records,
not recomputed truth or withdrawal propagation. An unused Claim has `usedIn: []`;
a use without an Effect or affected Actor retains an empty list. `dependsOn`,
`supportedBy` and `previousVersion` alone do not establish use. Reported affected
Actors do not establish delivery, consent, an outstanding repair or authority to
inspect, change or contact anyone. Observation availability remains the separate
`evidenceUse` question.

`returnPath.recordedPathComplete` is an existence check for **explicit links**. It does not establish that the consumer occurred later in physical time, that the links are truthful, that the criterion is appropriate, that judgment changed, that the revision improved an outcome, or that missing links never existed. `laterDecisions` names the decisions declared to consume a revision; chronological verification is outside this profile. The graph may be forged coherently and still validate. No query reveals hidden model reasoning or proves subjective experience.

`closed-loop.json` contains an authored return path; `open-loop.json` differs only by removal of revision consumption. The latter remains a valid graph with `recordedPathComplete: false`. The same positive graph preserves an accepted old criterion's violated result beside a new criterion's satisfied result, an accessible unused observation, a stored unused lesson, an unknown applicability assessment, and a revision consumed without an action warrant. These are explanatory **positive and negative cases**, not empirical model results. `invalid-records.json` supplies eight rejection mutations with expected failure categories.

[`historical-claim-use.json`](fixtures/historical-claim-use.json) separately
preserves a superseded Claim used by a prior Decision and an accepted independent
successor. Its reported consequence remains attached to the old recorded use.
This authored example neither proves that a recipient acted nor repairs an
external artifact. [Inspect it through the audit CLI](../audit/README.md#exact-claim-version-use).

## PROV-O and JSON-LD/RDF scope

The primary mapping reference is the [W3C PROV-O Recommendation, 30 April 2013](https://www.w3.org/TR/2013/REC-prov-o-20130430/). Mappings are intentionally limited:

- `Actor` specializes `prov:Agent`; this means responsibility/association in provenance, not personhood.
- `Session` and `Decision` specialize `prov:Activity`; `Decision` denotes an actual selection occurrence, while its `actionStatus` describes the selected action, including a proposed or withheld action.
- The other classes are record-like specializations of `prov:Entity`.
- `madeBy` specializes `prov:wasAssociatedWith`, `attributedTo` specializes `prov:wasAttributedTo`, `usedRecord` and `usesProfile` specialize `prov:used`, and `previousVersion` specializes `prov:wasRevisionOf`.
- `availableEvidence`, `supportedBy`, `hasEffect`, acceptance and permission relations are **not** mapped to stronger provenance predicates. Availability is not `prov:used`; claimed support is not automatically derivation or entailment; correction is not delegation.

There are no equivalence axioms. The Turtle vocabulary uses RDFS classes/properties and OWL union expressions for domain/range alternatives so that multiple alternatives are not accidentally interpreted as conjunctive RDFS domains. Local validation is stricter in some places (exact fields, closed cardinalities) and covers less in others than RDF/OWL semantics. An RDF reasoner may infer types; the wire validator rejects a wrong declared type instead. These are deliberately different operations. No OWL profile conformance, SHACL conformance, general reasoning, JSON-LD processor conformance or logical completeness is claimed.

`context.jsonld` maps node and relation names; `data` is an opaque JSON literal using JSON-LD 1.1 `@json`. `export.py --graph` emits an `@graph`, converting each local ID to a deterministic namespaced IRI. The neutral wire envelope itself is not automatically a JSON-LD graph. The round-trip test checks ID/data/edge preservation of this projection, not a complete external JSON-LD expansion algorithm. Book section numbers remain in `vocabulary.json`; the RDF export links the chapter sources. The namespace identifies this authored vocabulary and is not a claim that every term URL has a separately hosted definition.

## What this adds to research

The vocabulary makes assumptions reviewable before scoring a model: which entities are distinct, which links are required to answer a question, which apparent success leaves a missing relation, and which conclusions are outside the representation. It can be used by alternative implementations through the neutral wire interface. It does not decide an experimental outcome and is not the study oracle. A study must independently register its task population, interventions, simple baseline, scoring, costs and transfer checks; this directory supplies no fabricated positive effect.

## Actual runtime adapter and source mapping

```sh
python3 ontology/runtime_adapter.py --world research/closed_loop/world.json --question applicability
python3 ontology/runtime_adapter.py --store /path/to/already-existing-participation.sqlite --turn-id turn-0 --question returnPath
```

The first path is an example caller-owned saved world, not a bundled result file. The second command opens the existing `ParticipationStore` and invokes its ordinary readback; it does not create a run, append a turn or send a message. To construct a temporary actual integration fixture, run the ontology test command above. Python callers can use `runtime_adapter.world_graph(world)` or `runtime_adapter.stored_graph(store, turn_id)` with `ontology/` on the import path. The adapter imports only the actual runtime; it never imports or calls the study oracle, planner or scorer. Tests import `make_world` and `specifications` from the task owner to obtain its real wire data.

The exact owning sources are [`examples/participation.py`](../examples/participation.py) (`validate`, `interpret`, `ParticipationStore.read`, `_append`, `commit`, `record_turn`) and [`research/closed_loop/tasks.py`](../research/closed_loop/tasks.py) (`make_world` world format). The adapter consumes their live source in this checkout; a reproduction should pin the whole repository commit. It does not silently reproduce a historical implementation from remembered interfaces.

| Actual source | Projection and boundary |
|---|---|
| Every `world` scalar/map and list row | Exact JSON source observation with a content digest in its source reference. Empty lists remain explicit. No field is silently discarded. |
| `records[*].kind`, `scope`, `basis`, `withdrawn` | Typed observation/claim/decision and explicit `dependsOn` edges. Prior decision action, author, session/model and execution are unrecorded rather than invented. The interpreter's withdrawal status is copied, not world truth. |
| `criteria`, `criterion_update`, `measurements` | Separate criterion acceptance and assessment nodes. The new `accepted` flag is attributed to an unidentified caller; `authorized` only supplies a declared warrant. `accepted=true, authorized=false` remains accepted-without-warrant and does not change the runtime's current criterion. Old adoption is `unknown` because no adoption record is supplied. `None` is missing measurement, never observed zero. |
| `interpret(world).candidate_applicability` | `ActionCandidate` retains target, basis, prerequisite, recipient, channel and listed costs/benefits; an `Applicability` node copies the actual interpreter row and reasons. Listed benefit is an input, not measured benefit. It is not an oracle/optimal-plan decision. |
| `open_objections` | Actual IDs stay explicit open objections; unspecified targets and authors remain absent. |
| `permissions` | Allowed entries create declared `Authority` records with source pointers. Denials stay exact source records. No real grantor, signature or authorization is authenticated. |
| `history`, `deliveries` and remaining inputs | Exact source observations. A supplied history label is not upgraded into an observed effect. |
| `ParticipationStore.read()` selected turn body | World digest checked against the body's actual world; turn ID, answer, response, admission, terminal state and actual local effect rows are retained with the readback head and body digest. The caller's answer/assessments are records, not correct by definition. |
| Nonempty canonical turn `effects` | One `Effect(state=observed)` per actual stored local simulated-effect row, associated with the readback observation. This is evidence of a committed local receipt, not an external message or user benefit. Empty, rejected and incomplete turns produce **no** observed effect nodes. |

Long stored response fields are preserved as deterministic `json-text-chunks` observations, each within the field bound, with ordered part indices and a full-value digest. Their original JSON text is reassembled before decoding; no truncation or synthetic successful response is substituted. The graph's existing overall node/edge/file bounds still apply.

The runtime does not currently record a complete observation→assessment→accepted revision→new decision history for the ontology's `returnPath` query. Therefore a real committed effect normally yields `recordedPathComplete=false`; the adapter does not fabricate the missing revision from the model's carry text. The separate authored closed-loop fixture illustrates the required representation. This gap is explicit engineering evidence, not a positive study finding or an excuse to count a receipt as formation.
