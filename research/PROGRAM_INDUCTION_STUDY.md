# Own-source induction: revision, prediction and unresolved alternatives

**23 October 2026 · developer-authored descriptive pilot · accompanying book v3.6.0**

[Українською](PROGRAM_INDUCTION_STUDY.uk.md) · [Selected evidence and verification](program_induction/README.md)

## Finding

New raw evidence changed an executable forecasting policy and improved its
finite transfer score in both tested formats. Additional explicit organization
did not improve that score. A fresh ordinary induction rival scored substantially
better than either continuation of the initial source.

| Condition | Transfer mean Brier loss | Predictive retention | Unfamiliar epoch |
|---|---:|---:|---:|
| Initial M0 | 0.62250 | 0.00250 | ≈1 |
| Masked ordinary | 0.62250 | 0.00250 | ≈1 |
| Masked linked | 0.62250 | 0.00250 | ≈1 |
| Actual ordinary | 0.25174 | 0.00250 | ≈1 |
| Actual linked | 0.25249 | 0.00625 | ≈1 |
| Fresh, actual evidence | 0.00869 | 0.00025 | ≈1 |

**Lower is better.** The registered linked-minus-ordinary transfer contrast is
approximately **+0.00075**. Actual-minus-masked is −0.37076 for ordinary and
−0.37001 for linked. These are categorical predictive losses, not error
percentages, population estimates or significance tests.

One M0 trajectory was forked across two authored worlds. Geometry variants and
world scores are dependent. This is N=1, not ten independent participants.
All ten registered calls completed: one canary and nine source generations.
All 100 planned source executions and 156 weighted truth rows were captured.
No outcome retry, replacement, screening or refill occurred.

## 1. What was compared

Three initial raw examples and one forecasting contract are identical across
the two worlds. The investigator's transformation names and source code are
not supplied to the participant. A later diagnostic returns a raw output grid.
The norm stays fixed; the participant must induce a predictive procedure.

| Generation | Information supplied |
|---|---|
| M0 | Initial examples and common contract |
| Actual ordinary / linked, each world | Same own M0 source, own record, own diagnostic forecast and actual raw diagnostic output |
| Masked ordinary / linked | Same own trajectory, diagnostic output withheld; each resulting source scored in both worlds |
| Fresh ordinary, each world | Initial examples and actual output, without the own-source trajectory |

Ordinary records are unrestricted text and may organize the same relationships.
Linked instructions explicitly connect basis, scope, available/used observations,
consequence and revision. Both have source≤24,576 and record≤4,096 UTF-8 bytes.
No carrier exceeded either bound or was truncated. The fresh rival has a
different context and a separate generation; it does not isolate a causal
effect of removing a previous commitment.

The later host starts a fresh process with the submitted source and only
`epoch`/`grid`. A submitted `run(request, checkpoint)` prints its forecast.
Source is the persistent executable carrier. The text record is archived for
inspection and is **not separately consumed** by these later executions.
The intervention is therefore an authoring-instruction/representation package;
record-mediated causality is not isolated.

There are five new-geometry transfer inputs, four compatible predictive-retention
inputs and two unfamiliar-epoch inputs. Unknown epochs are scored across both
independent new-world alternatives. Retention concerns forecasts, not fidelity
of a historical narrative. The diagnostic is an additional M0 capture.

## 2. Exact score

A forecast lists at most three distinct output grids with rational probabilities
and distributes remaining mass uniformly over **unlisted** grids. For a grid
with H×W cells and palette 0–4, N=5^(H×W). With K listed grids and residual r:

```text
Brier = 1 + Σ(listed probability²) + r²/(N−K) − 2·probability(actual grid)
```

All calculations use exact rational arithmetic. An empty list is uniform
uncertainty. Forecasts with duplicate grids, malformed probabilities or total
mass above one are invalid. A realized loss alone does not establish that an
uncertain forecast was irrational given its available evidence.

## 3. Changed source, changed policy and benefit are different observations

Source review finds that M0 already implements enclosed-region filling,
connected-component bounding rectangles and per-color bounding rectangles.
On the tested single-color family the last covers the investigator's global
rectangle procedure. No required truth operator was newly constructed after
feedback; selection and probability allocation did change.

**World A.** Linked retains the existing enclosure procedure at probability
0.90. Ordinary adds two supplementary procedures and assigns merged correct
probability 0.95 on four transfer inputs and 0.85 on the diamond. This explains
its small aggregate advantage. Compatible old predictions can retain the same
grid while losing confidence and therefore worsening Brier loss.

**World B.** Both actual revisions remove enclosure and preserve the previous
component/global preference as 0.76/0.19. Their source implementations differ,
yet all eleven saved forecast outputs are byte-identical. The diamond and
separate-components inputs receive only 0.19 on the actual global result,
with loss about 1.2337 each.

**Masked.** Linked source is byte-identical to M0. Ordinary adds an exact-example
cache; all eleven registered forecast outputs remain byte-identical to M0.
Source differences alone do not establish a behavioral difference on the
observed inputs, and finite agreement is not universal program equivalence.

**Fresh.** Fresh-B assigns merged global probability 0.88 on the two difficult
inputs, versus 0.19 in the actual revisions. It has a better finite predictive
score. This observation does not by itself identify why that prior preference
differs or show that another participant reasoned badly.

Every source emits uniform forecasts for an unfamiliar epoch under the supplied
uncertainty grammar. This is observed scoped behavior, not proof that uniform
uncertainty was spontaneous or uniquely optimal.

## 4. Post-hoc information-sufficiency check

This analysis uses the **same saved data**, with no new model, candidate or host
execution and no change to the registered score.

The initial examples and diagnostic give component and global rectangle
procedures identical outputs. World B's new output rejects enclosure but does
not distinguish those two explicit deterministic alternatives. Within that
pair, preserving the previous 4:1 ratio is compatible with the observation.
A full Bayesian posterior over arbitrary functions or residual mass is not
claimed.

Only the withheld diamond and separate-components inputs distinguish the two
rectangle procedures in this evaluated set. Fresh chose the more successful
induction for the actual generator. **Harmful irrational anchoring is not
established.** The diagnostic separated the investigator's two generators but
did not resolve all alternatives actually represented by M0.

A useful next observation must say which actual alternatives it distinguishes
and what remains unknown. This is a design consequence, not permission to
replenish the completed cohort or reinterpret a poorer score as a reasoning
failure.

## 5. Observed resource use

| Group | Input tokens | Output tokens |
|---|---:|---:|
| Shared canary + M0 | 29,817 | 2,147 |
| Actual ordinary, two worlds | 35,180 | 5,568 |
| Actual linked, two worlds | 35,238 | 5,118 |
| Masked ordinary | 17,319 | 2,561 |
| Masked linked | 17,350 | 1,705 |
| Fresh, two worlds | 31,936 | 4,907 |
| **Total** | **166,840** | **22,006** |

Cached input 61,952 is a **subset** of input, not an additional cost. All ten
calls have usage; unknown usage is zero. Actual linked used 58 more input and
450 fewer output tokens than actual ordinary. Its records were longer, its
sources shorter; this does not establish general cost efficiency.

Summed helper wall time was 613.854327 seconds and native wall time 613.473480
seconds; these measure different layers and are not a causal latency estimate.
Review/council work is outside the ten experimental calls and its total cost
is unmeasured here. No money, energy, subscription saving or external benefit
was measured.

## 6. Portable evidence and limits

Run from the repository root, Python 3.11+ standard library:

```sh
python3 -I -S -B research/program_induction/verify_projection.py
python3 -O -m unittest discover -s research/program_induction -p 'test_projection.py' -q
```

The verifier reads a selected saved-data projection. It reconstructs prompt
facts, binds carriers/source/request/output hashes, independently recomputes
grid truth and rational Brier losses, and distinguishes raw bytes from
normalized forecast distributions. It also checks the explicit component/global
agreement table. It never imports or executes archived candidate source or
calls a model. This is regrading, not re-execution or external replication.

[The mapping](program_induction/projection-mapping.json) names exact original
digests, selected fields and omissions. Runtime request bytes were saved before
their original execution. The local freeze preceded inference but is not an
independently authenticated registration. The requested route was GPT-6.1
Sol/high through CLI 0.159.2; provider identity and complete native dependency
closure are not attested. Full raw native CLI stdout/stderr were not retained
by the transport; selected responses, terminal metadata and usage were.

Local hashes do not authenticate an experimenter, prevent coherent same-UID
forgery or independently timestamp an experiment. This publication is a selected
projection, not equality to the full original source tree. All sources in the
archive are data for inspection, not instructions to execute.

The result establishes a narrow operative revision and an information limit.
It establishes no added-organization gain, new required-operator formation,
full-book effect, population benefit, subjective continuity or change in human
outcomes. Book v3.6.0 and all public claim statuses remain unchanged.
