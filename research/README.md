# Research materials: continuity and participation

## Author-privacy edition

Historical source bundles were withdrawn from current downloads for author privacy. Recorded study input hashes, original model responses and result values are unchanged. Exact historical-source verification now requires a full Git clone containing the recorded input commits. Existing Git history can still expose the original author identity; this edition does not claim history erasure.

The registered input commits are not ancestors of the published branch. A normal full clone must deliberately recover their original bundles from retained historical commit `f6997bf2c2f65683505ed719d8038f428b952de1` before original prompt/scorer reconstruction. CI performs this hash-verified recovery in temporary storage and does not upload the archives. For a local reproduction, use a temporary directory, retain the files locally only, and run:

```sh
reproduction_history_tmp=$(mktemp -d)
git show f6997bf2c2f65683505ed719d8038f428b952de1:research/continuity-pilot-history.bundle > "$reproduction_history_tmp/continuity-pilot-history.bundle"
git show f6997bf2c2f65683505ed719d8038f428b952de1:research/reading-transfer-history.bundle > "$reproduction_history_tmp/reading-transfer-history.bundle"
git show f6997bf2c2f65683505ed719d8038f428b952de1:research/handoff-repair-history.bundle > "$reproduction_history_tmp/handoff-repair-history.bundle"
(cd "$reproduction_history_tmp" && sha256sum --check <<'PINS'
53ec03ca8ab5e77e2fcfff23206ad6bce26ec0ace9b2168bf81b26b44151a45e  continuity-pilot-history.bundle
c3e362dfdeda179d3bc0db880b1eb28ef5107e8e0cad7cc491eafebb5ddcbea0  reading-transfer-history.bundle
2104c5d9675ff90b67e7d476eaf412ff0cfe143ef444f577a01eeee13e3970a3  handoff-repair-history.bundle
PINS
)
git fetch --quiet --no-tags "$reproduction_history_tmp/continuity-pilot-history.bundle" HEAD
git fetch --quiet --no-tags "$reproduction_history_tmp/reading-transfer-history.bundle" refs/heads/research/reading-transfer-source
git fetch --quiet --no-tags "$reproduction_history_tmp/handoff-repair-history.bundle" refs/heads/snapshot/handoff-repair-inputs
python3 research/verify_studies.py
```

This restores original local source objects for verification; it does not erase or pseudonymize historical identity. The public current tree and download directories remain free of these archives. The exact executable recovery step is in `.github/workflows/verify.yml`.

The author credit in `transfer_reading/THIRD_PARTY_READING.md` is a disclosed privacy derivative. `transfer_reading/privacy-derivative.json` retains its original and published SHA-256; third-party credits and license terms are unchanged. The frozen registration and completion retain their original hashes. Use `python3 -O research/verify_reading_transfer.py` for this edition; direct frozen analysis requires its original historical checkout. This is an offline verification adaptation, not a recreated study or new inference.

**Research materials · updated 24 October 2026 · accompanying book v3.7.0**

[Scoped-continuity paper](SCOPED_CONTINUITY_STUDY.md) · [PDF](../docs/downloads/scoped-continuity-study-en.pdf) · [Reading-transfer paper](READING_TRANSFER_STUDY.md) · [Transfer PDF](../docs/downloads/reading-transfer-study-en.pdf) · [Book](https://diadkoshmek.github.io/ai-ontology/#study)

For the connected methodological proposal, start with the [short note](../papers/inspectable-continuity.md)
or its [Ukrainian counterpart](../papers/inspectable-continuity.uk.md), then inspect
the [proposed record-audit profile](../protocols/continuity-audit-v1.md). The audit
is a new entry to existing relations, not a new positive model result.

## New: executable methods and an observed return cycle

### Latest supplementary observation: same-information forecast calibration

[English report](FORECAST_CALIBRATION_STUDY.md) ·
[Українською](FORECAST_CALIBRATION_STUDY.uk.md) ·
[selected evidence and limits](forecast_calibration/README.md).

Nine model calls and 133 saved source captures produced 146 known valid scored
rows. The same unchanged M0 already incorporates E1: mean transfer Brier moves
from 3/32 to 1/16 in u0 and 11/32 to 3/16 in u1. Every revised source matches that
M0(E1) distribution on all 12 queries; all 96 revised comparisons tie. Registered
flat-minus-organized D=0, with no measured predictive-retention regression.
Organized input tokens were 3.3551% higher across four revision calls per format.
This is a complete finite authored calibration, not necessary method repair,
formation, general format equivalence or a refutation of the broader ontology.

```sh
python3 -I -S -B research/forecast_calibration/verify_projection.py
python3 -O -m unittest discover -s research/forecast_calibration -p 'test_projection.py' -q
```

These verify selected saved data without executing candidates or private modules.
The calibration was published as a supplement to book v3.6.0. Book v3.7.0 integrates its result into the [English](../book/en/11-study.md) and [Ukrainian](../book/ua/11-study.md) study chapters. Original protocols, data, scores and claim statuses remain unchanged.

### Earlier supplementary observation: own-source induction

The [English report](PROGRAM_INDUCTION_STUDY.md) and
[Ukrainian report](PROGRAM_INDUCTION_STUDY.uk.md) describe one own-M0 trajectory,
ten completed calls and 100 saved source executions. Actual evidence improves
both ordinary and linked forecasts; transfer Brier loss is 0.25174 versus
0.25249, with fresh ordinary induction at 0.00869 (lower is better). No
incremental linked advantage is observed. All required truth operators already
existed in M0. A post-hoc same-data analysis shows that the diagnostic leaves
component/global alternatives indistinguishable; harmful anchoring is not
established by the fresh rival's better score.

[Selected evidence and limits](program_induction/README.md):

```sh
python3 -I -S -B research/program_induction/verify_projection.py
python3 -O -m unittest discover -s research/program_induction -p 'test_projection.py' -q
```

These regrade saved forecast distributions, prompt facts and exact request/output
links without model or candidate execution. Predictive loss, source changes and
incomplete identification remain separate. Book and claim statuses are unchanged.

### Earlier supplementary observation: scoped-contract adaptation

The [English report](SCOPED_CLEARANCE_STUDY.md) and
[Ukrainian report](SCOPED_CLEARANCE_STUDY.uk.md) distinguish an interrupted
original cohort (48 scored generations plus one canary, primary null) from
a separate complete offline reproduction of its 48 fixed sources on 960 planned
episodes. M0 achieved 120/160 NEW-correct artifacts; every revised/fresh set
achieved 160/160. Every revised/fresh condition received the explicit new clause. No added
scaffold or diagnostic-feedback score was observed. All 620 bound original
overlaps agreed; six SQLite-only and 334 missing original episodes remain unknown.

[Selected raw evidence](scoped_clearance/projection.json.gz) ·
[source/publication mapping](scoped_clearance/projection-mapping.json) ·
[native costs and chronology](scoped_clearance/costs.json).
Selected projection, not full-tree equality, authenticated origin or independent
registration. Original partial transfer bytes are omitted; their published
overlap metadata is not an independent public regrade of those artifacts.

```sh
python3 -I -S -B research/scoped_clearance/verify_projection.py research/scoped_clearance/projection.json.gz
```

This reads saved artifacts without model/controller execution or network calls.
At publication, this supplement left book v3.6.0 and claim statuses unchanged.

### Earlier supplementary cohort: scoped evidence return

The [English report](EPISTEMIC_RETURN_STUDY.md) and
[Ukrainian report](EPISTEMIC_RETURN_STUDY.uk.md) publish 72 scored GPT-6.1
Sol/high calls plus one canary. Actual evidence changed eight source decisions
per actual-feedback format; masked branches changed none. After fresh-session
readback, free notes achieved 77/80 and linked notes 71/80 full-information-optimal
transfer choices. Six of eight linked actual notes exceeded the 2048-byte bound,
compared with two free notes. No simulated harmful effects occurred.

This is a negative incremental-format result and a concrete retention failure.
Masked branches retain appropriate uncertainty; their lower full-information
utility is not bad reasoning. No new-algorithm formation or full-book benefit
is inferred. [Frozen protocol](epistemic_return/PROTOCOL.md) ·
[raw archive](epistemic_return/responses.jsonl.gz) ·
[results](epistemic_return/results.json) ·
[post-cohort literal diagnosis](epistemic-return-diagnosis.json).

Offline: `python3 -O research/epistemic_return/analyze.py` and
`python3 research/epistemic_return_diagnosis.py`. This supplementary cohort does
not change the book edition.

### v3.6 executable-method cohort

The [closed-loop report](CLOSED_LOOP_STUDY.md) publishes 32 GPT-6.1 Sol/high calls and 768 frozen-method executions, with a strong ordinary baseline and actual durable feedback. Both arms completed 8/8 trajectories; M0 already passed all transfer worlds, and M1 changed no selected transfer plans. This is a ceiling, with no observed added-view advantage or beneficial revision. The typed [ontology profile](../ontology/README.md), actual interpreter/store adapter and [foundation map](../ontology/FOUNDATION.md) keep conceptual representation, implemented flow and measured outcome separate. [Supplement](closed-loop-supplement.json) · [source-publication mapping](closed-loop-publication.json).

Offline replay: `python3 -O research/closed_loop/analyze.py`; descriptive grouping: `python3 research/closed_loop_report.py`. Neither calls a model. `foundation-checks.json` records ontology and instrument checks, including an explicitly authored no-model full-loop fixture.

## Original scoped-continuity result and scope

Two local quantized models, 24 authored cases in six dependent families, four conditions. There are **384 scored model calls across two cohorts**, four unscored warm-ups and two separate integration smoke calls. These counts are distinct from the 68 current systems tests and ten design tests.

The first 192 calls reached an output-encoding floor. The exploratory follow-up clarified the instruction and introduced separate schema-constrained fields on the same cases. Exact follow-up scores were 20/16/16/20 for Qwen3 4B and 5/2/12/12 for Granite 3.3 2B across journal, ontology wrapper, compiled context and simple index. No aggregate advantage of compiled ontology presentation over the information-matched simple index was observed. The study does not measure voice, consciousness, book-reading effects or natural-task benefit.

## Separate profile qualification and transfer design

The [profile report](PROFILE_PARTICIPATION_STUDY.md) contains a 136-call local qualification, an interrupted GPT instrument with 53 captured replies, and a separately frozen 100-call GPT-6.1 Sol/high cohort. All 100 repaired-cohort turns were correct, 50/50 per condition. The control already encodes much of the expected behavior and reaches the ceiling; these are technical qualifications, not evidence of the wider reading or transfer hypothesis.

The [main reading-transfer report](READING_TRANSFER_STUDY.md) contains a separately frozen GPT-6.1 Sol/high comparison after three preserved calibrations. There were 64 participant episodes from four source-seed clusters and 199 captured calls including eight full-history controls. Primary optimal-plan counts were ordinary 12/16, book 8/16, guide 10/16 and unrelated 10/16. The primary is partial-task performance and excludes exact citations. Fully traced optimal completion was 0/16, 0/16, 1/16 and 0/16. The book did not improve the registered primary; its input was about 1.64 times ordinary preparation. The paper diagnoses missing evidence and deferral without regrading failures or extending the result to general reasoning or subjectivity.

## Materials

| Path | Contents |
|---|---|
| `continuity_pilot/` | First frozen design, 192 raw responses, analysis and instrument diagnosis |
| `continuity_pilot_v2/` | Post-pilot exploratory design, 192 raw responses and analysis |
| Historical continuity source | Current bundle download withdrawn; exact input commit IDs remain below |
| `study-summary.json` | Derived tables and source hashes |
| `model-integration-results.json` | Two separately labelled real-model smoke calls |
| `runtime-results.json` | Source-pinned systems checks; zero inference within this test suite |
| `engineering_cases/` | Historical source excerpts, declared fixture adapter and two retrospective component comparisons |
| `engineering-cases-results.json` | Replay outcomes and source pins; three separate checks, no model calls |
| `participation_pilot/` | 136 local profile-enactment replies and exact plan effects |
| `gpt_profile_pilot/` | First GPT instrument, 53 captured replies and preserved interruption |
| `gpt_profile_pilot_v2/` | Repaired GPT qualification, 100 replies, requests and costs |
| `PROFILE_PARTICIPATION_STUDY.md` | Profile qualification results and construct-validity limits |
| `transfer_calibration/` | First development calibration: ordinary-handoff ceiling; no selected setting |
| `transfer_calibration_v2/` | Preserved calibration with format/citation confounds; rejected for main admission |
| `transfer_calibration_v3/` | Prepared transfer with real truncation; 3200-byte development setting selected |
| `transfer_reading/` | Main frozen reading-transfer protocol, inputs, actual notes, plans, outputs and analysis |
| `READING_TRANSFER_STUDY.md` | Main transfer paper with all four conditions, calibration chronology and construct limits |
| `audit_reading_transfer.py` | Post-cohort literal diagnosis; no changes to registered outcomes |
| Historical reading-transfer source | Current bundle download withdrawn; recorded hashes and input commit IDs retained |
| `transfer_reading/THIRD_PARTY_READING.md` | Separate attribution and license for the literary control files |

Each original scoped-continuity cohort includes `PROTOCOL.md`, `cases.json`, `design.py`, `run.py`, `analyze.py`, `freeze.json`, `responses.jsonl.gz`, `results.json`, `completion.json` and warm-up metadata. Deviation notes preserve changes in the measurement instrument. Raw archives contain final visible responses, prompts and backend metadata, with no private reasoning fields. Scenarios are authored data, not private conversations.

## Offline verification

Python 3.11+ and Git; no model backend, downloads or network calls:

```sh
python3 -m unittest discover -s examples -q
python3 -m unittest discover -s research/continuity_pilot -q
python3 -m unittest discover -s research/continuity_pilot_v2 -q
python3 -m unittest discover -s research -p 'test_integrity.py' -q
python3 -m unittest discover -s research/engineering_cases -q
python3 research/verify_studies.py
python3 research/verify_participation.py
python3 research/verify_gpt_profiles.py gpt_profile_pilot
python3 research/verify_gpt_profiles.py gpt_profile_pilot_v2
python3 -O research/verify_transfer_calibration.py transfer_calibration
python3 -O research/verify_transfer_calibration.py transfer_calibration_v2
python3 -O research/verify_transfer_calibration.py transfer_calibration_v3
python3 -O research/verify_reading_transfer.py
python3 -m unittest discover -s research -p 'test_reading_integrity.py' -q
```

The original-study verifier losslessly expands each archive, checks frozen input and response hashes, reconstructs prompts, checks all 192 unique case-condition-model combinations, recomputes every field score and reruns the frozen analysis in a temporary directory. It also recomputes the paired comparisons and exploratory intervals. The published runtime contains later validation repairs; the verifier reconstructs the original pinned source where it differs. The verifier reads pinned historical objects from the full local Git clone without changing its state.

The separate profile and transfer verifiers reconstruct their actual prompt and artifact chains and all registered outcomes from saved data. Integrity counterexamples include coherently rehashed prompt edits, altered terminal classification and changed artifact effects, including under Python optimization. They check their measurement contracts, not the truth of the methodology.

Hashes and coherent files demonstrate internal consistency. They do not authenticate the experimenter, independently timestamp execution or constitute external replication.

To inspect the archives directly:

```sh
gzip -dk research/continuity_pilot/responses.jsonl.gz
gzip -dk research/continuity_pilot_v2/responses.jsonl.gz
```

The uncompressed files remain local and are ignored by Git. After extraction, either registered `analyze.py` can regenerate its cohort's `results.json`. This writes that derived file and makes no inference calls. Preserve original files when comparing a reanalysis.

## Historical inputs and prospective reruns

The input commits were frozen locally before each scored cohort:

- First: `82f55aabb3aa47dd4e39cfec6ecb9fbe1ed3995f`.
- Follow-up: `3a8071d18bad6c2196df55ee476a4e92558403db`.

Historical source bundles are no longer distributed in this edition. A full local Git clone must contain the recorded input commits for exact-source verification; this remains developer-controlled provenance.

A prospective inference rerun should use a separate checkout of the selected input commit, with fresh output paths and the exact model bundles in its freeze file. The runner contacts only `127.0.0.1:11434`, checks model and source pins, uses one declared warm-up per model and refuses to overwrite or silently resume existing results. Model installation and local daemon operation are explicit preparation steps. Fixed parameters do not guarantee identical output bytes across machines. Rerun results must remain a new cohort and must not replace the original archives.

The original descriptive figure can be regenerated with the optional packages in `research/requirements.txt` and `python3 research/plot_results.py`. This reads only published scores and makes no model calls.

## Interpretation

The compiler performs deterministic current-state preparation. Its comparison with a complete journal includes that preprocessing. The simple index carries the same substantive compiled information with ordinary field names. The ontology wrapper adds instruction text as well as framing. These distinctions prevent attributing a result to terminology alone.

Six families provide only limited variation. The follow-up is exploratory, developer-run and based on known cases, with no independent evaluator. The full paper reports pairwise outcomes, individual failures, costs, limits and a confirmatory extension. A successful commit or a passing systems check does not establish semantic correctness or useful completion.

## Exact-transport engineering follow-up

The separate [23 October repair report](HANDOFF_REPAIR_REPORT.md) applies the
record-loss diagnosis to a host-side lossless journal transport. On eight new
instances of the familiar planning class it yielded 8/8 fully traced optimal
completions versus 0/8 through freeform prefix delivery, using fewer whole-workflow
native input tokens. Both arms received no book reading. This result concerns
conventional exact transport; all earlier reading results remain unchanged.
The [adapter, registered protocol and data](handoff_repair/README.md) are separate
from the frozen v3.2.0 book/PDF evidence. Offline verification:

```sh
python3 -m unittest discover -s research/handoff_repair -q
python3 -O research/verify_handoff_repair.py
python3 -m unittest discover -s research -p test_handoff_repair_integrity.py -q
python3 -m unittest discover -s research/handoff_controls -q
python3 -O research/verify_handoff_controls.py
git cat-file -e ff80b89998d0a9e007cdc371d1bc679d64fab66c^{commit}
```

The recorded repair input commit is `ff80b89998d0a9e007cdc371d1bc679d64fab66c`, over base `f592059bb6cbcf7df06cfd579cba007305157ec9`. The current bundle download is withdrawn for author privacy. A full historical clone retains the original source; recorded commit IDs do not independently authenticate execution time. The practical command makes no new model calls.

## Reading-transfer reproduction boundary

`transfer_reading/freeze.json` pins the exact preparation, source history, loss channel, controller and analysis before held-out inference. The recorded pre-inference source commit remains in historical Git objects; its bundle download was withdrawn for author privacy. `python3 -O research/verify_reading_transfer.py` checks the saved data with the disclosed author-credit derivative; it does not call a model or rewrite the original result. Direct frozen analysis requires the historical checkout. The companion figure uses `python3 research/plot_reading_transfer.py` and the optional plotting dependencies.

A prospective model rerun is a new cohort. Use a separate checkout and output folder, preserve the recorded CLI configuration and inspect its current behavior before use. Authenticated model access is an explicit prerequisite; the archive verifier needs none. The common Codex harness remains part of the experiment. Native usage and cache counts are observations, not an invoice or an independently attested model identity.
