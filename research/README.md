# Scoped continuity: research materials

**Working paper · 22 October 2026 · accompanying book v3.0.0**

[Paper, English](SCOPED_CONTINUITY_STUDY.md) · [PDF](../docs/downloads/scoped-continuity-study-en.pdf) · [Book](https://diadkoshmek.github.io/ai-ontology/#study)

## Result and scope

Two local quantized models, 24 authored cases in six dependent families, four conditions. There are **384 scored model calls across two cohorts**, four unscored warm-ups and two separate integration smoke calls. These counts are distinct from the 49 systems tests and ten design tests.

The first 192 calls reached an output-encoding floor. The exploratory follow-up clarified the instruction and introduced separate schema-constrained fields on the same cases. Exact follow-up scores were 20/16/16/20 for Qwen3 4B and 5/2/12/12 for Granite 3.3 2B across journal, ontology wrapper, compiled context and simple index. No aggregate advantage of compiled ontology presentation over the information-matched simple index was observed. The study does not measure voice, consciousness, book-reading effects or natural-task benefit.

## Materials

| Path | Contents |
|---|---|
| `continuity_pilot/` | First frozen design, 192 raw responses, analysis and instrument diagnosis |
| `continuity_pilot_v2/` | Post-pilot exploratory design, 192 raw responses and analysis |
| `continuity-pilot-history.bundle` | Self-contained Git history preserving exact pre-inference commits |
| `study-summary.json` | Derived tables and source hashes |
| `model-integration-results.json` | Two separately labelled real-model smoke calls |
| `runtime-results.json` | Source-pinned systems checks; zero inference within this test suite |

Every cohort includes `PROTOCOL.md`, `cases.json`, `design.py`, `run.py`, `analyze.py`, `freeze.json`, `responses.jsonl.gz`, `results.json`, `completion.json` and warm-up metadata. Deviation notes preserve changes in the measurement instrument. Raw archives contain final visible responses, prompts and backend metadata, with no private reasoning fields. Scenarios are authored data, not private conversations.

## Offline verification

Python 3.11+ and Git; no model backend, downloads or network calls:

```sh
python3 -m unittest discover -s examples -q
python3 -m unittest discover -s research/continuity_pilot -q
python3 -m unittest discover -s research/continuity_pilot_v2 -q
python3 research/verify_studies.py
```

The verifier losslessly expands each archive, checks frozen input and response hashes, reconstructs prompts, checks all 192 unique case-condition-model combinations, recomputes every field score and reruns the frozen analysis in a temporary directory. It also recomputes the paired comparisons and exploratory intervals. The published runtime contains later validation repairs; the verifier reconstructs the original pinned source where it differs. A temporary Git object store is populated from the local bundle and removed afterward; the repository's Git state is unchanged.

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

`git bundle verify research/continuity-pilot-history.bundle` inspects the history archive. These commits are accessible within it even if publication uses a different commit. The bundle contains public book and experiment history, including the frozen runtime, rather than a new source of instructions or external authority.

A prospective inference rerun should use a separate checkout of the selected input commit, with fresh output paths and the exact model bundles in its freeze file. The runner contacts only `127.0.0.1:11434`, checks model and source pins, uses one declared warm-up per model and refuses to overwrite or silently resume existing results. Model installation and local daemon operation are explicit preparation steps. Fixed parameters do not guarantee identical output bytes across machines. Rerun results must remain a new cohort and must not replace the original archives.

The descriptive figure can be regenerated with the optional packages in `research/requirements.txt` and `python3 research/plot_results.py`. This reads only published scores and makes no model calls.

## Interpretation

The compiler performs deterministic current-state preparation. Its comparison with a complete journal includes that preprocessing. The simple index carries the same substantive compiled information with ordinary field names. The ontology wrapper adds instruction text as well as framing. These distinctions prevent attributing a result to terminology alone.

Six families provide only limited variation. The follow-up is exploratory, developer-run and based on known cases, with no independent evaluator. The full paper reports pairwise outcomes, individual failures, costs, limits and a confirmatory extension. A successful commit or a passing systems check does not establish semantic correctness or useful completion.
