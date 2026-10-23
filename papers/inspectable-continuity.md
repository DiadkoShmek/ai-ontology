# Inspectable Continuity: Evidence Relations for Claims about Agent Revision

**Artur Onysko · Methodological note 0.1 · 23 October 2026**
Accompanies *AI Ontology: The Organization of Self*, book v3.6.0.
[Ukrainian](inspectable-continuity.uk.md) · [Audit profile](../protocols/continuity-audit-v1.md) · [Terms](../docs/TERMS.md) · [Book](../BOOK_EN.md)

## Abstract

An agent may retain a lesson without using it, change a method without improving
it, or report a successful revision without preserving the grounds for that
report. This note proposes a bounded record contract for inspecting such
claims. It separates available evidence from recorded use, adoption of a
criterion from its satisfaction, a stored lesson from behavioral change, and
an observed effect from a complete recorded return path. A finite vocabulary,
reference runtime and audit CLI make the distinctions executable. The audit
checks explicit relationships; it does not establish causal influence,
semantic truth, consciousness or beneficial learning. Developer-controlled
studies include ceilings and negative results. In the latest matched-memory
pilot, unrestricted notes outperformed the tested linked representation under
the same byte allowance. The contribution proposed here is a connected,
criticizable method for asking what supports a revision claim, with software
and counterexamples that expose its limits.

## 1. Problem: a change record leaves several questions open

Consider a document assistant that receives a complaint, changes its procedure
and later answers correctly. Several explanations fit those events. It may
have used the complaint, rediscovered the procedure independently, copied an
answer, or succeeded because the next case was easier. A stored reflection and
a correct answer do not distinguish these explanations.

The practical problem is broader than memory retrieval. Long collaboration
also involves commitments, objections, changing permissions and responsibility
for earlier effects. A technically continuous history can preserve an
unjustified rule. A justified new rule can sacrifice an earlier capability.
Another participant's objection can be recorded while having no effect on the
continuation. These are different problems and require different evidence.

The book develops this broader account of participation, identity and voice.
This note isolates one engineering question: **what is recorded between an
effect, its assessment, a revision and a subsequent decision?** The proposed
profile makes that question inspectable without requiring a reader to accept
the book's whole conceptual vocabulary.

## 2. Four distinctions

| Distinction | Inspectable question | Insufficient evidence |
|---|---|---|
| Available evidence / recorded use | What reached a decision's available material, and what use is explicitly recorded? | Retrieval or prompt inclusion alone |
| Criterion adoption / satisfaction | Was this criterion accepted, and what result was assessed under this exact version? | Acceptance, or success under a replacement criterion |
| Lesson storage / formation | Was a lesson retained, consumed, associated with a changed judgment, and useful on new cases? | A saved reflection or revised wording |
| Recorded effect / recorded return path | Can explicit links connect the effect to an observation, assessment, accepted revision and distinct consuming decision? | A receipt or a revision with no assessment link |

Here **formation** names the larger research question of a changed manner of
participation. It is not a Boolean field established by this audit. Changed
behavior, useful transfer, retained capabilities and consequences for others
need additional observations and comparisons.

Even recorded use is weaker than causal influence. A runtime can witness that
a file was read or sent to a model; a participant can explicitly cite it.
Establishing that removing the material changes a decision requires a suitable
intervention. These evidence levels should remain separately reportable.

## 3. Minimal record model

The implemented [finite profile](../ontology/README.md) defines 18 local
classes and 34 relations. For the return question, the relevant records are
`Decision`, `Effect`, `Observation`, `Assessment`, `Criterion` and `Revision`.
`Actor`, `Session`, `Model` and `Profile` remain distinct. `Authority`,
`Objection`, `Scope` and `Lesson` supply additional questions, not shortcuts
to claims about identity or learning.

An `Assessment` names its subject, criterion and support. An accepted revision
can name what it responds to and the assessment it is based on. A consuming
decision explicitly adopts a revision. Source references are descriptive
strings; the auditor does not fetch or authenticate them. The validator checks
field types, relation endpoints, cardinalities, finite limits and version
cycles. A structurally valid claim can still be false.

The proposed terms are defined in [TERMS](../docs/TERMS.md); the executable wire
contract remains [`vocabulary.json`](../ontology/vocabulary.json). The short
note does not introduce a competing schema or amend frozen study inputs.

## 4. Recorded return-path criterion

```text
Decision ─hasEffect→ Effect ←observesEffect─ Observation
                       ↑ evaluates             ↑ supportedBy
                    Assessment ────────────────┘
                       ↑ basedOn
              Accepted Revision ─respondsTo→ Effect
                       ↑ adoptsRevision
                 Distinct Decision
```

For an effect attached to a decision, the implemented query asks whether there
is an observation of that effect, an assessment evaluating the effect and
supported by such an observation, an accepted revision responding to that
effect and based on such an assessment, and a distinct decision adopting one
of those revisions.

The [audit profile](../protocols/continuity-audit-v1.md) calls all attached paths
**complete** only when each has these recorded links and no effect record is
orphaned. It calls missing links or orphan effects **incomplete**. A graph with
no effects has **no-recorded-effects**, not an automatic success or a claim
that revision was inapplicable.

These are coverage judgments about the supplied graph. The current graph
query does not establish physical chronology, semantic entailment,
authenticated authority, hidden reasoning or causal influence. Its field
`laterDecisions` denotes declared revision consumers; temporal ordering needs
separate evidence. A coherent forgery can pass the record checks. A complete
path therefore cannot be advertised as proof that an agent learned.

Two [authored fixtures](../ontology/fixtures/) make the distinction inspectable.
The positive graph contains the explicit path. The negative graph removes
revision consumption and remains structurally valid. Neither is a model trial.
The actual [runtime adapter](../ontology/runtime_adapter.py) is deliberately
more conservative: durable effects do not acquire missing assessment-to-revision
links merely because a carry note sounds reflective.

## 5. Reference implementation and portable audit

The reference uses a finite belief reducer and a hash-linked SQLite journal
with compare-and-swap admission. Its model cycle binds requests and rejects
stale context. These mechanisms have established predecessors and do not
authenticate an experimenter or guarantee a true interpretation of a source.
The bounded journal is an inspectable reference, not a production-scale memory
service.

The thin audit CLI delegates validation and all nine competency questions to
the existing ontology module. It accepts either the neutral graph JSON or
explicit node/edge records in JSONL. The JSONL adapter preserves declared
relations; it does **not** infer an assessment, permission or use relation from
the order of arbitrary provider logs. A framework exporter must supply those
relations, with its own provenance and limitations. The optional
[LangGraph checkpoint adapter](../audit/README.md#native-langgraph-checkpoint-observations)
preserves native state history as Observations with no inferred edges. Its
authored deterministic example is a local runtime-integration check, not an
LLM study, an external user trace or a demonstration of beneficial revision.
Letta and OpenTelemetry interoperability remain unqualified here.

The additive `claimUse` query preserves the exact Claim version recorded as used
by a Decision and its reported Effects/affected Actors. A current independent
successor does not rewrite that historical use. Dependency or revision links
alone do not establish use; reported effects do not establish delivery, remedy
or permission. This inspection remains separate from Observation availability
and recorded return-path coverage.

Three local commands show the contract without models or network:

```sh
python3 -m audit.cli report ontology/fixtures/closed-loop.json
python3 -m audit.cli report ontology/fixtures/open-loop.json
python3 -m unittest audit.test_audit -q
```

The first two should report `complete` and `incomplete`, respectively. A valid
incomplete graph exits successfully as a parsed audit; malformed input exits
2. Consumers must inspect the reported status rather than treat exit 0 as an
agent-quality verdict. The report binds the supplied bytes by SHA-256 and
includes available/use gaps, lesson use, criterion assessments and recorded
objections. It does not follow source URLs, run supplied commands or grant
action authority.

## 6. Evidence so far

The repository publishes model outputs, study chronology, fixed inputs, replay
code and costs. The following results concern different interventions; they
must not be pooled into one measure of ontology quality.

| Intervention | Result | What remains open |
|---|---|---|
| Scoped-memory presentation | Compiled context did not generally outperform an information-matched index in 384 scored local-model calls. | Broader tasks and stronger models |
| Prescribed book reading before lossy transfer | Ordinary preparation gave 12/16 optimal plans; book preparation gave 8/16. | Other doses and uses of the method |
| Exact evidence handoff repair | 8/8 fully traced optimal completions versus 0/8 freeform on new instances of one known class. | Unique codec benefit: an accessible shared file restores the same evidence |
| Executable-method return cycle | Both arms reached the ceiling; M0 and M1 each achieved 192/192 optimal transfer choices per arm. | Beneficial revision: zero transfer plans changed |
| Scoped evidence return | Actual-feedback free notes achieved 77/80 full-information-optimal transfer choices; linked notes 71/80. | Whether a different organization can earn its resource cost |
| Scoped-contract adaptation | Separate reproduction: M0 achieved 120/160 NEW-correct artifacts; every revised/fresh set 160/160. | Original interrupted, primary null; no added scaffold or diagnostic-feedback score observed |

The evidence-return pilot captured 72 scored GPT-6.1 Sol/high calls and one canary across
eight instances of one authored class. Under the same 2048-byte allowance,
6/8 unrestricted notes and 2/8 linked actual-feedback notes were admitted.
Over-budget records were explicitly unavailable. Actual feedback changed
source decisions; masked branches retained appropriate uncertainty. The
primary linked-format effect was negative. This is evidence about the tested
representation and retention pipeline, not a general refutation of scoped
reasoning or proof of beneficial method formation. [Report and limits](../research/EPISTEMIC_RETURN_STUDY.md).

The earlier [closed-loop report](../research/CLOSED_LOOP_STUDY.md) establishes a
working finite execution/return pipeline but cannot show revision gain when
the initial methods already solve the transfer set.

The separate [scoped-contract report](../research/SCOPED_CLEARANCE_STUDY.md)
records 48 scored source generations plus one canary. The original execution
was interrupted and its registered primary remains null. A separately planned
960-episode offline reproduction verified all fixed programs: M0 was OLD-correct
but achieved 120/160 under NEW; every revised/fresh set achieved 160/160.
All eight paired organization differences were zero, as were actual-minus-masked
score differences. All revised/fresh conditions received the full new clause.
This establishes bounded contract adaptation, with no observed added scaffold
benefit or feedback necessity for the achieved score; it does not establish
formation, book benefit or universal equivalence.

## 7. Relation to prior work

[PROV-O](https://www.w3.org/TR/2013/REC-prov-o-20130430/) provides a provenance
vocabulary; this profile documents limited mappings rather than claiming
to originate provenance. Truth maintenance, AGM belief revision and event
sourcing are also precedents. [Reflexion](https://arxiv.org/abs/2303.11366)
already investigates feedback, reflective memory and later task decisions.
The question of learning through feedback is not new here.

The 2026 [survey of evidence tracing and execution provenance](https://arxiv.org/abs/2606.04990v6)
distinguishes supporting evidence from execution influence and discusses
incomplete provenance chains. [EPGM](https://arxiv.org/abs/2609.25913v2)
studies budgeted evidence completion and controls candidate design separately
from graph propagation. These are close, substantive neighbors.

The narrower proposal here connects records of criteria, objection, accepted
revision and subsequent consumption to explicit claim boundaries, executable
counterexamples and developer-controlled studies. Whether that combination
is useful beyond this implementation remains an empirical question.

## 8. How to challenge and extend the proposal

An implementer can challenge the formal profile with an admissible graph whose
query draws an unsupported relation, a relevant case the vocabulary cannot
distinguish, or a smaller representation preserving the same information.
An empirical challenge can show a cheaper baseline with equal or better
transfer, a revision that repairs one class while losing another capability,
or a path that is complete in records while behavior remains unchanged.

A stronger method-rebuilding study should freeze task generation, source
material, measures, costs and interpretation before scored inference. Both
systems need the same evidence, actions, model and revision rights. Compare
unchanged M0 and M1 on identical new cases, preserve retention tests and use
feedback ablation where a causal claim is intended. A model that initially
succeeds supplies evidence of initial capability, not forced development.

Another participant's justified objection also needs a real consequence.
Host-enforced access restrictions and model responses must be assessed
separately: a host blocking an action does not demonstrate that the model
respected the objection. Useful continuation, refusal when no permitted path
exists, and responses to pressure without new grounds all belong in the test.

The audit profile offers a criticizable evidence contract. Adoption,
independent replication and standardization remain unobserved here.

## Citation and authorship

Suggested citation: **Onysko, A. (2026). *Inspectable Continuity: Evidence
Relations for Claims about Agent Revision*. Methodological note 0.1,
AI Ontology repository.** Cite the commit inspected when exact reproducibility
matters; [BibTeX](inspectable-continuity.bib) is supplied. This is a
developer-controlled note, not a peer-reviewed publication or registered standard.

Artur Onysko supplied the conceptual direction, research questions and editorial
intent. Codex substantially contributed writing, software, study design,
execution and analysis. Private Architect-Ψ council contributed criticism;
it is not independent empirical replication. [Full authorship](../AUTHORS.md).
The repository's copyright terms remain applicable.
