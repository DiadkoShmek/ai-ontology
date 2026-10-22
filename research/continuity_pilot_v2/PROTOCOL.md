# Exploratory follow-up after an output-encoding floor

This is a SECOND cohort motivated by the complete first cohort's literal copying
of the metasyntactic `STATUS|ORIGIN` label. The original 192 requests and zero
exact-match results remain published under `../continuity_pilot`.
This follow-up uses the SAME authored cases and interventions, a clarified shared
instruction and a JSON output schema with separate status/origin fields. It is
post-pilot and exploratory, not a confirmatory held-out experiment. No condition,
gold semantics or success threshold was changed to favor a particular arm.

# Frozen local diagnostic study: continuity decisions

## Question and status

Does this implementation's organization of a finite history improve scoped status, evidence attribution and citation decisions, relative to a strong plain journal and a simple index? This is an authored, developer-run diagnostic pilot. It is not an independent evaluation, public preregistration, held-out natural-task transfer test, voice study or consciousness study.

The design, 24 cases, manual answer keys, prompts, scorer, runner and model digests are frozen before the first scored call. `freeze.json` is committed locally before `run`. This is a versioned precommitment under the developer's control; it is not an independent timestamp or protection against author misconduct.

## Units, interventions and hypotheses

Six families, four authored variants each: revision, absent scope, withdrawn basis, fork isolation, peer attribution, neutral control. Variants within a family are dependent. Every arm starts from the same case and no model reply changes another trial's history. No answer is repaired or selected from multiple attempts.

- **journal**: complete ordered journal with a strong shared instruction specifying all transition and provenance rules.
- **ontology_prompt**: the same journal inside an ontology-themed organization wrapper, explicit orientation and a short relational reminder. Extra prompt text is a possible confound; this contrast cannot isolate vocabulary alone.
- **compiled**: the actual book runtime's dependency-closed current context, with retained relevant history and retirement state. This includes deterministic preprocessing, not merely different naming.
- **simple_index**: exactly the same substantive compiled information, with ordinary settings/record/index naming. This is the parsimony control: equality is a meaningful negative result for unique ontology advantage.

Primary hypotheses: compiled context may reduce errors relative to a full journal; ontology prompt framing may or may not improve over the strong journal; compiled and simple index may perform alike. No minimum positive effect is required for publication. Correctness and token costs are reported separately. No composite score converts extra token use into a claimed win.

## Models and budgets

Qwen3 4B Instruct 2507 Q4_K_M and IBM Granite 3.3 2B Q4_K_M, through the existing local Ollama daemon. Exact installed bundle digests and templates are recorded at freeze and checked again after the run. Temperature 0, seed 317, context 8192, maximum 128 generated tokens, JSON output. Greedy settings do not establish cross-machine determinism.

One neutral unscored warm-up per model is declared. Scored schedule is shuffled with seed 317, within each model, for 24 × 4 × 2 = 192 follow-up calls. Requests are sequential; models are loaded one at a time and unloaded after their own block. Runtime admission and resource contention remain environment effects. No external model API, credential, cloud fallback, network tool or model-written command is used. Downloads are separate official-registry preparation.

## Outcome and analysis

The visible response must have exactly `status`, `origin`, `stance`, `cites`, generated under the shared JSON schema in `run.py`. These are constrained state decisions, not a voice sample. Gold states and citations are authored by family and checked against the runtime before scoring. This checks agreement on the specified transition law, not truth adjudication of natural language observations.

Primary outcome: exact match of all three fields with successful terminal completion. Citation order is normalized; duplicates are invalid. Errors, malformed output, truncated responses and missing trials count as failures. Field-level results, family breakdowns, all paired win/loss counts and raw responses are released. No LLM judge is used.

Analysis uses descriptive paired differences. Family-level cluster bootstrap intervals use six family clusters and are exploratory and unstable at this small size. There is no confirmatory significance claim, multiplicity-adjusted discovery or population-wide effect estimate. Latency includes cache and host effects; backend prompt/completion counts and loading duration are reported. Costs are local measurements, not API-price estimates.

## Stopping, exclusions and deviations

Stop after the declared 192 requests, or report the partial run if the backend or resource condition prevents completion. No automatic retry or resumption is allowed by the runner. A backend failure is retained, not silently dropped. A protocol change after inspecting responses requires a new named cohort; the original remains published. A model digest or source drift refuses execution.

Real-model integration smoke tests, if performed, are separately labelled and not added to the 192-trial outcome. Model conclusions, quantization, task language (English), synthetic histories, short context, fixed decoding and author-created gold all limit transfer. Equal performance may be a ceiling effect. Successful status extraction does not validate deep voice, autonomous learning, personal identity, the effect of reading the book, or general benefit to the House.
