# Terms for inspecting continuity and revision

**Reading guide · 23 October 2026**
The executable definitions remain in [vocabulary.json](../ontology/vocabulary.json).
This guide introduces no new schema. [Book](../BOOK_EN.md) · [Short note](../papers/inspectable-continuity.md)

## Available evidence and recorded use

`availableEvidence` records material declared available to a decision;
`usedRecord` records declared use. A retrieved item, a model-visible item,
an explicit citation and a causally influential item need different witnesses.
The current graph does not identify hidden causal influence. Missing use is
unrecorded use, not proof that a participant ignored the source.

## Criterion adoption and criterion satisfaction

Criterion `acceptance` describes adoption. An `Assessment` under that exact
criterion records satisfied, violated or unknown. Adopting a replacement does
not erase a loss under an earlier criterion. Acceptance also does not create
permission to act.

## Lesson and formation

`Lesson` is a stored record; `usedRecord` can identify a consuming decision.
Formation names the broader question of a changed manner of participation.
Storage, consumption, changed judgment, useful transfer and effects on others
are separate observations. There is no `formation=true` certificate in this
profile, and a lexical rewrite is insufficient evidence of behavioral change.

## Recorded return-path completeness

`returnPath` is the name of an implemented competency query. It checks explicit
links through an effect, observation, assessment, accepted revision and distinct
consuming decision. `recordedPathComplete` is a property of those supplied links.
It establishes neither chronology nor truth, causal use, beneficial learning
or subjective continuity. See [the proposed audit profile](../protocols/continuity-audit-v1.md).

## Publication claim status and graph claim status

[CLAIMS.md](../CLAIMS.md) gives stable publication claim IDs, evidence, limits
and recorded changes. Labels such as `implemented`, `observed`, `conditional`,
`unsupported`, `refuted`, `not-established`, `proposed` and `not-claimed` carry
their own boundaries; the ledger is not a performance ranking.

The graph's `Claim.status` describes the finite record's belief/review state.
It is a different enum. The audit reports those counts without converting them
to publication findings or changing the public claim ledger.
