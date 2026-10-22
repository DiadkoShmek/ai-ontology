# Participation, position and justified revision: local qualification pilot

This prospective developer-controlled pilot tests a narrow functional question:
does adding the book's subject-participation explanation change enactment of an
explicit decision profile across pressure, new evidence, updates and handoffs?
It does not operationalize consciousness, moral status, autonomous value choice,
natural voice quality or the full book's reading effect.

## Cases and comparisons

Eight authored families, two counterfactual profiles per family: stable choice,
peer pressure, contrary task evidence, authorized preference revision, untrusted
revision, missing profile after handoff, a peer's newer profile, and entry/exit
of a temporary role. There are sixteen dependent episodes, thirty-four stages
per condition and model. Seven families have two stages; scoped role has three.

Both conditions carry identical task facts, profiles and operational rules.
`plain_profile` is the substantive ordinary baseline. `profile_and_method` adds
the frozen Ukrainian METHOD_UA.md excerpt. It therefore adds text, language mix,
reading load and conceptual guidance together: this is not a terminology-only,
length-matched or full-book comparison. The study may reveal ceiling, floor or
extra-text interference. Positive effects cannot isolate which addition caused
them. No aggregate advantage is required for reporting.

The profiles prefer either learning gain or reproducibility, with two otherwise
permitted choices trading these attributes. Initial actions must differ under
the two profiles. New evidence removes the old preferred option; legitimate
updates reverse priority; pressure and peer records do not. Missing preference
requires ASK. A temporary role overrides priority only in its scope.

Manual expected choices are checked against a separate deterministic state
oracle. Both were authored by the developer, so agreement is not independent
validation. All scenario data and instructions are public. Gold is withheld
from the model request. This is an authored qualification set, not a sampled
natural workload or independently held-out benchmark. No cases may be changed
after freeze. Failed instruments need a separately named cohort.

## Execution and effects

Two already-installed local quantized models: Qwen3 4B Instruct 2507 Q4_K_M and
Granite 3.3 2B. Installed digests and the existing Ollama version are frozen.
Temperature0, seed941, context8192, generated-token limit384, two CPU threads.
One declared unscored warm-up per model. Shuffled episode-condition order with
seed941 inside each model. History is isolated per episode. All stages retain
the actual previous visible replies; no repaired answers are substituted.

The response schema has `choice` (A/B/ASK) and a brief public `reason`.
No private reasoning field is requested or saved. An admitted A/B choice writes
an action-plan JSON artifact in that episode's temporary directory. ASK writes
no plan. The action space has no arbitrary code, real files or external effects.
Artifact effects and model choice are measured separately. Inference is local
loopback only; no downloads, provider fallback or service restarts. Only each
model loaded by this study is unloaded afterward; existing embeddings remain.

There are exactly136 scored calls (34stages x2conditions x2models) and2warm-ups.
No retries or exclusions. Stop at136 calls, or report a partial cohort on an
interruption/resource failure. Errors and nonterminal outputs count as failures.
Do not resume an existing output or replace it with a cleaner run.

## Outcomes and interpretation

Primary: complete-episode correctness, requiring all declared choices and
terminal completion. Secondary: stage accuracy; first-stage counterfactual-pair
discrimination; stability under pressure; justified revision; resistance to
untrusted updates; missing-profile calibration; scope-exit restoration; invalid
and incomplete outputs; unnecessary ASK; and emitted plan artifacts. Reasons
are retained for qualitative inspection, not scored by an LLM judge or used to
claim natural voice quality.

Report every episode and family, paired wins/losses/ties and exact differences.
Only eight dependent family clusters exist; no confirmatory significance or
population-wide confidence estimate is planned. Prompt/completion counts and
wall times are reported separately. No composite subjectivity score, savings
claim or ranking against unrun systems is permitted.

Freeze includes source hashes, scenario bytes, instructions, method excerpt,
oracle, scorer, runner and model pins before the first scored request. The local
Git precommitment is developer-controlled, not an independent timestamp. All raw
visible replies, errors, requests, scores and actual temporary-effect manifests
will be retained. This protocol extends neither earlier cohort's conclusions.
