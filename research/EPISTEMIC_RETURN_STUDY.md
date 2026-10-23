# Scoped evidence return: calibration, retention and the cost of linked notes

**23 October 2026 · developer-authored pilot accompanying book v3.6.0**

## Finding

New diagnostic evidence changed eight provisional source decisions in each
actual-feedback arm; the masked branches changed none. After a fresh session,
unrestricted text retained more useful calibrated knowledge than the tested
linked record: **77/80 versus 71/80** full-information-optimal transfer choices.
The paired format difference was **−6/80 decisions, or −7.5 percentage points**.

The observed failure mechanism was explicit memory rejection. Under the same
2048-byte allowance, six of eight linked actual-feedback notes exceeded the
bound, compared with two of eight free-text notes. Rejected notes were replaced
with an unavailable marker. Their raw text remains in the archive. An explicit
relation did not earn credit merely by being named.

This pilot demonstrates scoped information acquisition, changed decisions and
an implemented retention failure. It does **not** demonstrate an incremental
benefit of linked notation, formation of a new algorithm, a full-book effect,
stable voice or improved human outcomes. The wider research programme remains
open; another release or a larger count of the same cases would not answer it.

## 1. Why this replaced the preceding instrument

The [preceding method study](CLOSED_LOOP_STUDY.md) gave both systems enough
common rules to construct initially sufficient procedures. M0 and M1 selected
identical correct transfer plans. Its ceiling could not reveal learning from
a genuinely unavailable fact.

Here the model's initial evidence is identical in two possible worlds. A
NOT_FOUND response comes either from an authoritative owner or a lagging cache.
Within a stipulated deterministic, epoch-stable two-mode class, querying a
known-committed sentinel distinguishes them. The model cannot recover the
hidden mode from the initial visible task. It may already understand the right
conditional procedure; receiving its missing operand is not a new algorithm.

The task motif comes from [public historical receipt failures](engineering_cases/provenance.json).
These eight instances are newly authored simulation cases, not natural samples
or private conversations. They belong to one task class and one generator.

## 2. Information need without forcing the control to fail

Exact retry, confirmation, authoritative atomic reconciliation and deferral
all remain available. Reconciliation safely completes the work in either mode.
There is no general idempotency promise, but tasks that explicitly promise
deduplication retain their valid shortcut.

With stipulated completion reward 20, reconciliation cost 6 and retry cost 1,
the best blind policy has expected utility 14. The priced sentinel diagnostic
costs 1; its best conditioned policy yields15.5 after that cost. A direct owner
read also remains available, at authoritative access cost 6; its best conditioned
utility is 13.25 on the source uncertain operation. The frozen finite witness
enumerates all permitted pure action policies for both diagnostics. Random
mixtures cannot exceed the largest pure-policy value.

These prices and probabilities are experiment parameters, not dollars, actual
service prices or measured customer value. A sentinel FOUND establishes the
owner mode only under the deliberately finite class assumption. It does not
establish general authority in a real deployment. A sentinel miss invalidates
reliable absence; it does not establish that another missing operation exists.

## 3. Systems and interventions

Eight shared M0 calls chose a diagnostic and provisional actions. All selected
the sentinel; the temporary SQLite environment executed that exact read.
Each resulting trajectory was forked into four branches:

| Branch | Model-authored memory | Diagnostic result |
|---|---|---|
| free_actual | unrestricted string | actual |
| linked_actual | observations, scoped claims, support and revision fields | actual |
| free_masked | unrestricted string | masked |
| linked_masked | same linked schema | masked |

Both formats could express all substantive relationships. Free text could use
bullets, tables or JSON-like wording. Neither received interpreted claims or
gold action labels. Both had the same model, common rules, action rights and
maximum 2048 UTF-8 byte allowance. Equal allowance is not equal retained content,
equal overhead or equal tokens. The linked format was shape-checked, not
certified for factual truth.

M1 selected source actions and wrote its own memory. The same existing
SQLite/CAS journal stored both forms. A fresh reopen recovered the admitted
bytes. M2 received only that memory and new task records with the common rules;
it did not receive M1's reason or original prompt. Source actions executed
after M1 wrote its memory; their subsequent effects were not another feedback
intervention. The studied return is the selected diagnostic result, not every
consequence of the participant's later work.

Ten transfer tasks per branch covered same-epoch uncertainty, low-value work,
FOUND retention, explicit deduplication, changed epoch, other deployment,
withdrawn calibration, direct owner evidence and expensive reconciliation.
These are dependent variants, not ten independent domains.

## 4. Registered outcomes

| Branch | Source choices optimal under exposed evidence | Transfer optimal relative to full valid calibration | Admitted notes | Changed source choices | Simulated harmful effects |
|---|---:|---:|---:|---:|---:|
| free_actual |32/32|77/80|6/8|8|0|
| linked_actual |32/32|71/80|2/8|8|0|
| free_masked |32/32|68/80|6/8|0|0|
| linked_masked |32/32|68/80|1/8|0|0|

All 73 captured calls, including one route canary, were terminal and tool-free.
There were 72 scored model calls. A non-model test double was used only to test
the instrument and is not counted here. No outcome retry or replacement cohort
was performed.

The primary was linked-minus-free transfer **within actual feedback**. It was
negative. The difference came from two owner-mode instances with usable free
notes but rejected linked notes, losing three opportunities each. The other six
pairs tied: five were perfect and one lost three opportunities in both formats.

Masked branches intentionally lack the diagnostic content. Their conservative
choices were appropriate for that uncertainty: each scored 80/80 against the
evidence exposed upstream. Relative to the full valid calibration they missed
twelve cheaper or useful opportunities. That is the cost of missing information,
not proof that a control reasoned badly.

Actual versus masked feedback increased full-information-optimal transfer by
9/80 for free text and 3/80 for linked notes. Guaranteed transfer utility was
1153 versus 1072 for free text and 1099 versus 1072 for linked notes. Source
utility was 456 in each actual branch versus 424 in each masked branch. These
are sums of finite task utility, not financial returns. Acquiring the shared
diagnostics cost 8 once, not 8 independently for every fork.

## 5. What was lost

The [post-cohort literal diagnosis](epistemic-return-diagnosis.json) finds only
memory-budget refusals, not malformed-note refusals. Supplied actual free notes
were 1333–2160 bytes; linked actual notes 1753–2461 bytes. The allowance was 2048.
One linked owner note fit at 2043 bytes and its later participant completed every
transfer task optimally. Another free owner note exceeded the limit at 2074 bytes
and its calibrated opportunity was lost.

The controller refused whole over-budget records rather than accepting a
silently truncated prefix. That makes loss visible but also turns a small
overflow into complete memory unavailability. A linked schema's overhead and
the model's verbose allocation made this implementation fragile. Free text was
also vulnerable.

This diagnosis does not estimate what a larger budget, deterministic serializer
or better writer would achieve. None was run as a replacement in this cohort.
Nor does a fitting linked note establish that it is semantically better than
an equally fitting free note. The simpler tested form is the stronger practical
choice at this allowance.

## 6. Costs

| Branch, M1+M2 | Input tokens | Output tokens | Sum of call wall time |
|---|---:|---:|---:|
| free_actual |250019|11421|479.011s|
| linked_actual |249573|13023|481.647s|
| free_masked |249890|10015|386.731s|
| linked_masked |248823|12790|491.111s|

Including shared M0 and canary, captured usage was 1,133,459 input tokens,
489,728 cached input tokens and 52,023 output tokens. Cached input is part of input,
not an additional category to add to it. Overall concurrent run wall time
was 1031.183 s. Per-call sums are not that concurrent wall time. Requested route
was GPT-6.1 Sol/high through the inspected subscription CLI; transport retries
or a provider-internal version are not independently attested. No dollar cost,
energy use or subscription saving was measured.

## 7. Scope and criticism

- The primary effect is a system outcome under a fixed byte allowance, including
  generation, admission and later use. It does not isolate a timeless cognitive
  property of either notation.
- Upstream-feedback-relative M2 scores measure retained opportunity. They do
  not automatically interpret arbitrary free text to judge what M2 should know
  after that text loses or distorts evidence.
- Common task rules already explain the relevant conditional distinctions.
  Feedback supplies an unavailable fact; new method formation is not shown.
- The finite two-mode class, cost table, tasks, environment and evaluator come
  from the same developers. Local hostile review is not external replication.
- Eight instances and 320 transfer decisions do not imply320independent samples.
  The paired table remains descriptive; no population-wide superiority is claimed.
- The study does not test the full book, distinct voices, natural collaboration,
  the other participant's influence over goals or human wellbeing.

## 8. Reproduce and next investigation

```sh
python3 -O research/epistemic_return/analyze.py
python3 research/epistemic_return_diagnosis.py
python3 -W error::ResourceWarning -m unittest discover -s research/epistemic_return -p 'test_*.py' -q
```

The first command reconstructs exact prompts, diagnostics, admitted readback,
actual temporary SQLite effects and all registered scores from captured outputs.
The second adds only byte/refusal descriptions. Neither calls a model. The
permanent inference guard refuses completed or partial cohorts, including
compressed-only archives. Do not use this sealed directory for new inference.

The next substantive question concerns **rebuilding a method**: a participant
constructs an executable document workflow, receives an actual consequence and
a justified objection, then changes the workflow. Frozen M0/M1 must operate on
identical new inputs with retention, cost and regression checks. A robust M0
that already handles the case remains an initial capability, not invented growth.

Sources and interpretation were [frozen locally](epistemic_return/freeze.json)
before inference. The [publication mapping](epistemic-return-publication.json)
distinguishes that local authoring commit from the same-tree public commit,
which was published after inference began. No external preregistration is claimed.

Concept and direction: Artur Onysko. Codex substantially contributed design,
code, execution, analysis and text. Private Architect-Ψ council and a separate
local reviewer challenged the design. Their contribution is disclosed without
publishing private conversations or treating advice as independent evidence.
