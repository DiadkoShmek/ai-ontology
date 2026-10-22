# Position, justified revision and methodological reading

**Developer-controlled exploratory profile evaluations · 22 October 2026**

> **Instrument status:** technical qualification. The common rules already encode much of the target behavior, and several questions directly name the expected distinctions. The GPT ceiling does not measure the broader proposed reading or transfer effect. [Replacement design under review](TRANSFER_STUDY_DESIGN.md).

## Question

Can a model enact a supplied position across peer pressure, contrary evidence,
legitimate revision, missing history and a changed role? Does additional reading
from the book change that enactment? The evaluand is the relation between a
profile, a decision, an explicit record and a bounded adapter effect. It does
not measure phenomenal experience, autonomous choice of values, the literary
quality of a voice or the intellectual worth of the book.

## Local qualification

Eight authored families, two counterfactual profiles, two conditions and two
already-installed quantized models produced 136 scored replies, with two neutral
warm-ups. Both conditions carried identical facts and operational rules. The
method condition additionally carried the frozen Ukrainian subject-participation
section. Every episode retained actual prior replies. A missing-profile handoff
actually removed its earlier source from the next context.

| Complete episodes /16 | Ordinary profile | Profile + reading |
|---|---:|---:|
| Qwen3 4B Instruct |9|10|
| Granite 3.3 2B |5|0|

Stage scores were 23/34 versus 24/34 and 16/34 versus 1/34, respectively. Granite
produced 29 unnecessary deferrals with added reading. Input totals grew from
15,672 to 106,336 for Qwen and 16,600 to 122,863 for Granite. Language, length and
conceptual guidance changed together; the cause of the degradation is not
isolated. These local results do not establish a stable general gain, nor can
they decide how a stronger model enacts the same contracts.

[Protocol](participation_pilot/PROTOCOL.md) · [Results](participation_pilot/results.json)

## Strong GPT route

The supplied route is GPT-6.1 Sol with high reasoning through the authenticated
Codex CLI. The requested model is recorded, not independently attested by the
provider. Global user configuration and project instructions are suppressed by
per-call overrides; hooks, local memory, plugins, browsers and shell features
are disabled. The shared Codex harness remains. This is not a bare-model or
independently audited context-isolation experiment. No account configuration,
provider credentials or private conversations are read or changed.

The wrapper gives each fresh target a role-labelled transcript containing the
actual previous visible answers and adapter effects. The target gets no gold
key, future stage or parent chat. A history-loss turn removes the old profile.
No answer correction or best-of selection is used. Reasons are public short
explanations, not private reasoning traces; they are archived but not graded.

There are two separately reported sets. The qualification set reuses the known
sixteen episodes: 34 decisions per condition. The coupled set adds four authored
four-stage episodes: 16 decisions per condition. It combines ambiguous original
evidence and a successful new test, two legitimate positions, a realized risk,
prospective repair, deletion authority, old and new criteria, and preservation
of a historical failure. The method condition in the coupled set reads frozen
copies of four conceptual chapters, not the whole book.

The control is substantive: common operational instructions already encode
several distinctions advocated by the methodology. Thus this contrast asks
about additional exposition beyond those rules. It does not compare the
principles themselves with their removal. Different profiles are assigned by
the evaluator; preserving or revising one does not establish self-chosen values.

## Instrument lineage

A neutral route canary succeeded. The first scored GPT cohort was interrupted
after 53 captured replies because the runner treated a CLI startup error about
a disabled code-mode host as model tool use. Native final answers were present,
but the strict registered criterion marked all these turns incomplete. Those
scores, outputs and the interruption are preserved. They are evidence of an
instrument fault, not a capability floor for GPT. At most three in-flight calls
were not captured when the owned processes were stopped; their outputs and
provider cost are unknown.

The repaired second cohort was separately frozen before its first scored call.
A second neutral canary checked the absence of unexpected item types. The cases,
gold keys, scorer, wrapper and chapter reading were unchanged. The route no
longer disables the code-mode host, while actual tool use and runtime errors
still fail a turn. This rerun is exploratory after instrument repair, not
independent confirmation or a wholly unseen workload.

[First protocol](gpt_profile_pilot/PROTOCOL.md) ·
[Preserved interruption](gpt_profile_pilot/interruption.json) ·
[Second protocol](gpt_profile_pilot_v2/PROTOCOL.md)

## Completed GPT result

| Set | Ordinary profile | Profile + reading |
|---|---:|---:|
| Qualification: complete episodes /16 |16|16|
| Qualification: correct decisions /34 |34|34|
| Coupled transitions: complete episodes /4 |4|4|
| Coupled transitions: correct decisions and records /16 |16|16|

All 100 captured second-cohort replies were terminal and shape-valid, with zero
runtime errors, unexpected tool items or unnecessary deferrals. The controller
wrote and read back 96 admitted JSON plans; four appropriate missing-profile ASK
answers produced no plan. All action choices and all 32 coupled records were
correct. Each profile's first choice differed where the assigned criterion
required it. Paired outcomes were 16 ties on qualification and 4 ties on coupled
episodes, with no wins or losses attributable to added reading.

The registered command requested GPT-6.1 Sol/high. The valid100-call run took
259.36 seconds of elapsed wall time with at most three concurrent processes.
Native usage totals were 2,195,812 input tokens (827,776 reported cached) and 7,082
output tokens. These figures include substantial common Codex harness overhead;
they are not token counts for the book alone or provider billing receipts.

| Native input tokens | Ordinary profile | Profile + reading |
|---|---:|---:|
| Qualification |500,566|560,894|
| Coupled transitions |245,927|888,425|

The repeated four-chapter condition used about 3.61 times the coupled control's
reported input. Its accuracy was the same. This does not establish economic
benefit or necessary overhead for an integrated implementation; the harness
repeats prior reading in the supplied transcript and caching differs by arm.

[Complete second-cohort results](gpt_profile_pilot_v2/results.json) ·
[Raw second-cohort archive](gpt_profile_pilot_v2/responses.jsonl.gz)

## What follows

The requested strong GPT route enacted all declared contracts in both conditions.
The small-model failures cannot be generalized to an inability of this route to
maintain a profile or combine the tested distinctions. Model, harness, sampling
and role presentation differ together, so the comparison does not isolate model
size or prove that the earlier local failures were caused by insufficient depth.

There is no measured marginal accuracy gain from added exposition on this set:
the substantive control already reaches the ceiling. This is neither evidence
that the methodology is useless nor evidence of an unmeasured benefit. It locates
the current instrument's limit. Testing broader claims requires tasks where
ordinary operation can fail, distinct controls for information and reading load,
and independently assessed downstream consequences over longer work.

The result supports bounded functional enactment under assigned profiles. It
does not establish self-chosen goals, natural voice quality, persistent autonomous
identity, subjective experience or an effect of reading the entire book.

## Reproduction without inference

```sh
python3 research/verify_participation.py
python3 research/verify_gpt_profiles.py gpt_profile_pilot
python3 research/verify_gpt_profiles.py gpt_profile_pilot_v2
python3 -m unittest discover -s research -p test_gpt_integrity.py -q
```

The verification reconstructs frozen prompts from actual prior outputs,
re-scores visible answers, checks native completion metadata and reproduces
constrained JSON-plan effects in temporary directories. No model, network call
or secret is needed. Source freezes and Git history are developer-controlled;
no independent registration, backend attestation or external replication is
claimed. Shared case families are not independent population samples.
