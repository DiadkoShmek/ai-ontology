# From a concept to a checkable relation

The domain of this implementation is **situated participation and revision**.
It asks what must remain distinguishable when a participant receives a report,
acts under a rule, encounters a consequence and changes a subsequent method.
The book's larger account of identity and coexistence is not reduced to the
existence of a database row.

## A working architecture

```text
source material -> scoped interpretation -> candidate judgments
                        |                         |
                  evidence/status             finite method M0
                                                  |
                                   budget planner -> action guard
                                                  |
                                            durable local effect
                                                  |
                                 reopen -> actual recorded return
                                                  |
                                           finite method M1
                                                  |
                              identical new worlds: M0 versus M1
```

The important unit is a **relation whose removal could change a judgment**.
"Do not publish because this version contains private data" contains a scope,
a condition and a reason. Replacing it with "never publish" changes the rule.
A delivered record and an acknowledged record are different observations.
An absent response does not establish refusal, approval or a broken participant.
These distinctions must be defined for the actual channel. A transport receipt
may confirm transport only; it must not silently become proof of reading.

## Concepts, representation, execution, evidence

| Question | Representation | Executable consumer | Evidence boundary |
|---|---|---|---|
| Who participated? | Actor, model, profile and session are distinct. | Typed graph validation and identity query. | A configured service/session identifier does not establish stable behavior or subjective identity. |
| What supports this decision here? | Scoped claims and dependencies. | `participation.interpret` propagates withdrawal; method predicates read current scope. | Caller assertions can be wrong; semantic entailment is not authenticated. |
| Did a criterion change or was it met? | Acceptance, warrant and separate old/new assessments. | Common current-criterion and assessment rules. | Accepting a new threshold does not erase a violated old threshold. |
| Was evidence available or used? | Separate `availableEvidence`/`usedRecord`. | Explicit graph joins. | A prompt proves availability, not a hidden causal use. |
| Which version did a past decision use? | Exact `usedRecord` Claim target, reported Effect and affected Actor. | `claimUse` retains historical use beside independent successor grounds. | No inferred delivery, remedy, current invalidity or right to act. |
| Did a proposed action occur? | Candidate, decision and effect are distinct. | Shared admission guard and durable readback. | Local receipt rows are simulated effects, not external delivery or human benefit. |
| Did an experience change a method? | Versioned executable method with a recorded return. | M0/M1 finite decision tables run unchanged on matched new worlds. | Changed prose or rule syntax alone earns no behavioral credit. |
| Did the change help? | Separate assessments and outcomes. | Independent recursive oracle and transfer replay. | Improvement can coexist with regression. One authored class cannot establish broad learning. |
| What remains unresolved? | Objections retain their identifiers and provenance. | Explicit open-objection scoring. | Recording disagreement does not establish its correctness or settle normative conflicts. |

The formal profile has 18 classes, 34 relations, nine competency questions,
explicit limits, domain/range alternatives and a neutral JSON wire format.
JSON-LD and Turtle exports expose the vocabulary to other implementations.
PROV-O mappings use provenance meanings; they are not equivalence axioms or
claims that an AI is a person. See [the exact profile](README.md).

## What the actual adapter can and cannot establish

`runtime_adapter.py` projects the actual interpreter and SQLite readback.
Every supplied world field remains traceable to source content. Missing model,
session, source authorship or adoption evidence stays missing. A rejected turn
does not acquire a successful effect node. Tests reopen a real temporary store
and inspect its actual bytes.

The runtime records the dataflow needed for the study's return cycle. It does
not yet assert every semantic link required by the stronger `returnPath` graph
query. In particular, presenting feedback does not establish that a particular
assessment was the model's reason for revision. The adapter leaves that path
incomplete rather than deriving it from a carry note. A separate authored
positive fixture explains the stronger record contract. These two evidence
levels must not be merged.

## Comparison and precedents

Persistence, transactions, provenance, truth maintenance, belief revision and
reflection have prior literatures. Their presence here is not a novelty claim.
The proposed contribution is a connected method for making the transition
from source interpretation to situated judgment and revision inspectable,
together with explicit counterexamples and experiments that may reject its
practical advantage.

The new [closed-loop protocol](../research/closed_loop/PROTOCOL.md) asks a
narrower empirical question than the book: does a prepared relation view help
a strong model construct and revise an executable method, within a shared
ordinary runtime? It does not remove facts, memory, rules or revision rights
from the baseline. Both systems can compute the same relations. Nor does a
positive result demonstrate that the formal vocabulary is necessary.

## A reusable engineering lesson

During instrument development, a repair-only revised method initially appeared
successful because transfer contained only repair tasks. Adding retention and
mixed worlds exposed its lost publication capability. The revised instrument
checks both corrected errors and regressions before any scored cohort.

This is a documented change in the research method, embodied in executable
tests. It is not evidence of model-weight learning. Future studies should
separately investigate feedback ablation, longer repeated revision, uncertain
source interpretation, independent task authorship and natural collaborators.

Run without models or network:

```sh
python3 research/run_foundation_checks.py
python3 -m unittest discover -s examples -q
python3 ontology/export.py --check
```
