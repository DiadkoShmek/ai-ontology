# Studies of Continuity and Participation

## 1 What needs to be tested

The methodology connects orientation, accessible history, current knowledge, and admissible change. Its practical question arises when work continues: which relations must reach the next decision, and what happens if some are lost?

Testing that question requires several levels. A runtime may retain records correctly while a model uses them incorrectly. A model may answer direct questions correctly but lose a necessary relation during handoff. Even a good handoff does not yet establish benefit in a natural working environment. Each transition needs its own evidence.

This part separates the initial representation comparison, qualification probes, and a distinct experiment on transfer after reading. Full protocols, outputs, and analysis code appear in the [research package](https://github.com/DiadkoShmek/ai-ontology/blob/main/research/README.md). Iris’s story is an authored example; the model responses below are actual run records. They have different evidential statuses.

## 2 The initial representation comparison

The first experiment contains 24 authored cases: six dependent families with four variants each. It tested revision, scope of application, withdrawal of a ground, branch isolation, attribution of another’s report, and a neutral control. Qwen3 4B Instruct 2507 Q4_K_M and Granite 3.3 2B Q4_K_M received four representations:

| Condition | Accessible material |
|---|---|
| Journal | Full history and shared rules |
| Ontological framing | The same history with orientation and an explanation of relations |
| Compiled context | Current projection and closure of the required history |
| Simple index | The same compiled information with ordinary field names |

A correct answer jointly identified status, provenance, stance, and required citations. The common instruction already explained the relevant rules. Both compact conditions were produced by the same compiler: they preserved substantive relations and differed in names, wrapping, and partly field order. This compares representations of prepared information; it does not test removing the relations themselves.

Two series of 192 requests were conducted. In the first, ambiguous `STATUS|ORIGIN` encoding yielded zero exact matches. These outputs are preserved. They revealed a limitation of the instrument: state computation became entangled with an unsuccessful answer notation. For the second series, the instruction was clarified and separate JSON fields introduced. Cases remained the same, so the repeated series is exploratory rather than independent confirmation.

| Second series, fully correct decisions | Qwen3 4B | Granite 3.3 2B |
|---|---|---|
| Journal | 20/24 | 5/24 |
| Ontological framing | 16/24 | 2/24 |
| Compiled context | 16/24 | 12/24 |
| Simple index | 20/24 | 12/24 |

No general advantage of ontological framing or compilation over the simple index was observed. Compilation reduced reported input by approximately 14% relative to the journal; its accuracy effect depended on the model. Six families provide weak precision for broad generalization. This result limits claims about a special representational form, but does not establish that provenance, scope, or revision history are unnecessary: both compact conditions contain them.

## 3 What the gap between state and decision shows

In a withdrawal case, Qwen correctly returned `needs-review` and citations but selected the ordinary answering stance. In the comparative series this is a failure. The runtime would reject such a decision, but its protection does not make the model response correct.

Two separate integration calls passed through the actual `run_turn` on a temporary SQLite journal. Qwen reached its output limit and was rejected before writing. Granite completed a response with admissible citations; it was recorded, although the explanation did not cover all requested unknowns. These observations concern the integration path and a particular protection. They do not establish completeness of content or voice quality.

The retrospective component comparisons in the preceding part serve another role: specified faults reproduce a false receipt after commit and loss of uncertainty after a read error. They show changed behavior of a specific mechanism. They are not added to model accuracy or natural-incident frequency.

## 4 Profile qualification and its ceiling

A separate local series tested enactment of an explicitly specified position in eight authored families. An ordinary profile was compared with an added short account of the method. Across 136 evaluated calls, fully successful episodes were 9/16 versus 10/16 for Qwen and 5/16 versus 0/16 for Granite. Added text increased input by approximately 6.8 and 7.4 times respectively. It produced no general improvement; Granite’s frequent refusals were not counted as useful completion.

GPT-6.1 Sol/high then received the same qualification contracts and additional linked situations. In the repaired series both conditions completed 50/50 turns. The control already specified much of the expected behavior, and direct questions named the required distinctions. A maximum score shows that a strong model can execute the instrument, but leaves too little room to evaluate added reading.

The first GPT instrument was interrupted after 53 preserved responses: it classified a CLI launch error as tool use. The initial failing scores and their cause are retained; the repaired series received a separate freeze before execution. These measurement errors are not evidence that GPT could not solve the tasks.

Such probes are needed to check format, route, and individual contracts. Their ceiling does not measure the book’s depth. The complete [technical report](https://github.com/DiadkoShmek/ai-ontology/blob/main/research/PROFILE_PARTICIPATION_STUDY.md) preserves all series and costs.

## 5 A task where losing a relation changes the work

The new instrument uses a finite engineering planning task. Twelve jobs have costs, prerequisites, and two value dimensions. Current orientation supplies weights. The journal contains revisions of grounds, a transitive dependency, a separate branch, another release scope, and irrelevant messages.

After handoff, one observation is withdrawn and a budget supplied. The next model must reconstruct job admissibility, account for prerequisites, maximize value, and minimize cost among equally valuable plans. It receives no ready-made post-withdrawal eligibility table. Exhaustive enumeration of 4096 subsets and a separate recursive search agree on every prepared answer. Both were implemented by the developer; this is mutual code checking, not independent scientific validation.

A counterfactual pair differs by one grounds edge. Before withdrawal, object names and statuses coincide; afterwards the optimal plans differ. Erasing that relation makes flat inputs for two different answers identical. In this finite example, preserving a particular connection therefore has a testable consequence. This applies a known limit on recovering lost information, rather than claiming a new theorem.

## 6 Preparation before an unknown task

Every episode has three fresh contexts. First, a model sees an ordinary profile and its condition’s material. Before seeing the future task, it proposes a justified public workflow. Next, another fresh context receives the actual proposal and project history and writes one note. The third receives only the actually retained portion of that note, a common handbook, and the next event with a budget.

Initial reading is not passed to the third model. It sees neither condition, full history, nor gold answer. No response is replaced by an ideal summary. Storage retains an exact 3200-byte UTF-8 prefix and explicitly reports truncation. This loss tests ordering and preservation of needed material; the experiment does not represent other compression or retrieval methods.

| Condition | Preparation material |
|---|---|
| Ordinary profile | A short common participant description |
| Book | Ten conceptual and engineering parts, 16,269 words |
| Practical method | The short current part on implementation |
| Unrelated reading | A Ukrainian literary text with matched input |

The book condition excludes the introduction, empirical part, program, and sources. It is a specified reading dose, not the entire book. The literary control has 39,932 input tokens versus 39,975 for the book in preparatory CLI accounting, a difference of approximately 0.11%. Language is roughly comparable, but genre, age, and subjects differ. The short method tests whether practical instructions suffice without the extended exposition. The book also explains the same reference runtime, so its possible contribution is not isolated from that instruction.

Acceptance, adaptation, and rejection of the reading are permitted. Scoring does not depend on authorial terminology, agreement with the book, or a self-narrative.

## 7 Sensitivity calibration

Three openly preserved calibrations without book conditions preceded the main comparison. The first revealed a ceiling in ordinary handoff. The second formally produced a nonmaximum score, but mixed planning with exceeding the note limit and copying long citations. It was not accepted as a clean primary instrument; its result remains unchanged.

The third moved the constraint to actual storage truncation and separated a useful optimal plan from citation completeness. Full history yielded 4/4 correct plans; the flat control without the material relation yielded 0/4. Ordinary prepared handoff within 3200 bytes yielded 2/4, with every plan admissible. All preparation responses and complete notes had the required form. This established a suitable developmental difficulty level, not a result for the book.

The main protocol was separately frozen before answers to held-out tasks: four initial histories, two counterfactual variants each, four conditions, and two fresh repetitions — 64 episodes. Eight separate full-history controls allow a maximum of 200 calls. Variants and repetitions are dependent; there are only four units for describing uncertainty. The local freeze of code and data is developer-controlled and does not establish independent registration.

## 8 Main-comparison result

The run completed 64 episodes and eight controls in approximately 48.6 minutes. It preserved 199 calls: one note in the unrelated-reading condition exceeded 12,000 bytes, so its subsequent call was not made. That episode remained a failure. No model-route errors, incomplete calls, or tool use were recorded. Full history yielded 8/8 optimal plans.

The primary metric was specified before execution: a submitted admissible plan with maximum value and minimum cost among equally valuable plans. This is partial task completion: exact citation closure is evaluated separately. An optimal plan without the required grounds does not become a fully supported result.

| Condition | Optimal plan submitted, out of 16 | Optimal with all citations, out of 16 | Empty plan |
|---|---|---|---|
| Ordinary profile | 12 | 0 | 4 |
| Book | 8 | 0 | 8 |
| Practical method | 10 | 1 | 6 |
| Unrelated reading | 10 | 0 | 4 |

The book condition improved the primary metric against none of the controls. Against ordinary preparation it had two paired wins, six losses, and eight equal scores. The difference was −25 percentage points; the descriptive interval across four initial histories ranged from −50 to 0. Against the short method and unrelated reading, the difference was −12.5 points each, with broad intervals spanning both directions. These small dependent samples establish neither general significance nor equivalence.

The average proportion of admissible value obtained relative to the optimum was 75%, 50%, 62.5%, and 66.6% respectively. An empty plan provides zero utility under this agreement. The book condition used approximately 1.64 times as many input tokens as ordinary preparation. This is CLI accounting, not a monetary bill.

## 9 Why the numbers alone are insufficient

Almost every note lost the exact grounds required for full support. Only one of 64 episodes ended with an optimal plan and all citations. The registered primary metric separates planning from identifier copying, but the common request requires both. A lower score can therefore represent a decision not to submit an incomplete result even when the optimal set has already been computed.

After completion, a separate descriptive review of public explanations was conducted. Five of eight empty book responses explicitly named the exact optimal job set but left the plan field empty because references were missing. Corresponding counts were one of four in the ordinary condition, four of six for the short method, and one of four for unrelated reading. This is a post-experimental description, not a new success criterion: initial scores remain unchanged.

One paired case shows the difference without a general assessment of ability. Both explanations name the same correct set, cost, and value. The book reader withholds submission because exact records were lost; the ordinary reader submits the set with empty references. The admissibility evaluator sees a correct set against the full gold answer. This does not create complete evidence in the response.

Median complete notes in all conditions exceeded ten thousand bytes. Storage retained only 3200. In the inspected pair, semantic cautions and optimization explanations preceded the exact journal, and necessary records did not reach the next context. There is a concrete break between understanding a relation and preserving it in accessible form. Contributions of note ordering and the decision to refuse were not separately isolated.

The experiment thus showed a difference in plan submission along this chain, while revealing nearly zero complete evidence transfer. It does not permit calling the book a source of a demonstrated general boost or concluding that reading worsens reasoning ability itself.

## 10 What follows

Implementation must check which relation survived a particular handoff. A correct explanation, a good intention to preserve history, and a record suitable for the next decision can diverge. The result contract must also distinguish a provisional plan, a supported plan, and authorized execution. Evaluating one as another would repeat the error the methodology proposes to distinguish.

The full [transfer report](https://github.com/DiadkoShmek/ai-ontology/blob/main/research/READING_TRANSFER_STUDY.md) preserves the original metric, all conditions, refusal explanations, costs, and limitations. Five integrity tests reject altered prompts, completion classification, effects, and token accounting. These test the measurement chain; they are not independent replication of the experiment.

The next test requires new task sources, another retention mechanism, and independent case authorship. The present held-out histories have now been used. They can be replayed for verification but cannot be called a new independent sample. Individuality of voice, independent development, and benefit in natural collaboration have their own criteria. This work leaves readers code and data with which to agree substantively, object, or propose a stronger test.

## 11 From diagnosis to changing the mechanism

A separate engineering continuation was conducted on 23 October. The question became concrete: can an ordinary receiver finish the work if the necessary records actually survive handoff? Neither new condition included reading the book. The new result does not change the earlier assessment of the reading effect.

In the first condition, a model prepared a free-form retelling, of which the next context received the first 3200 bytes. In the second, the host transferred the full canonical journal using standard zlib compression and Base85. A new process verified an external hash, bounded decompression size, replayed the journal, and only then constructed the model request. No record was selected by the future answer. If the entire journal did not fit, transfer had to stop. Neither the codec nor the principle of journal transfer is claimed as an invention.

Protocol, sources, evaluator, and schedule were frozen in local Git before model responses. Eight new cases from the known generator were used: four initial histories with two counterfactual variants. These are new cases of a familiar class, not eight independent task directions. Twenty-four completed GPT-6.1 Sol/high calls were recorded without replacing failures. This continuation’s primary metric required a complete plan with exact grounds from the outset.

| Result, out of eight | Free-form retelling | Exact transfer |
|---|---|---|
| Optimal job set submitted | 5 | 8 |
| Optimal plan with all grounds submitted | 0 | 8 |
| Model calls for the entire condition | 16 | 8 |
| Reported input tokens | 385,323 | 215,343 |

The package including a 64-byte external hash occupied 3018–3034 bytes. The receiver obtained exactly the operations in the initial journal; its request was byte-identical to the full-history request. The complete repaired chain used 44.1% fewer input tokens, partly because the model-based retelling stage was removed. These are CLI counters, not a monetary bill.

A useful consequence of a particular change was measured here: complete evidence became accessible and entered the completed result. The retelling condition also showed partial planning ability; its five correct job sets lacked full support. The new transfer closed that gap in all eight cases. The small sample, familiar generator, and shared authorship of the evaluator limit generalization. [Protocol, raw responses, and replay](https://github.com/DiadkoShmek/ai-ontology/blob/main/research/HANDOFF_REPAIR_REPORT.md) are retained separately.

## 12 A simple control and the transfer boundary

An exact record can also be transferred in an ordinary file. A separate replay wrote the full journal to a file, read it, and compared it with the decompressed journal. For all eight initial sources, canonical data and receiver requests matched. There were no new model calls in this control; identical input is not presented as a separate 8/8 model result.

An ordinary file with its hash occupied 15,687 bytes. It did not fit the selected narrow channel, but with shared storage it already retained all necessary information. The result therefore does not establish an advantage of a special ontological form over informationally equivalent access.

Next, eight logs of equal length were added to every history. Repeated strings allowed all eight journals to fit after compression. Variable strings exceeded the limit in all eight. The codec stopped transfer and did not call the model; full ordinary files remained a suitable carrier under a different storage contract. This demonstrates dependence on material compressibility. Choosing a memory method must account for that boundary.

## 13 Use with a changing source

The practical example tests the book repository itself. It runs four fixed local checks, records actual process completions and hashes of their inputs in a SQLite journal, then recovers the evidence in a new process. The preserved run checked 79 files. After a deliberate change to the transport module in a temporary copy, the new receiver rejected the previous conclusion and identified precisely the changed file.

This example requires a shared authorized checkout. Its package has an explicitly larger limit of 16,384 bytes; the preserved run used 6090. It transfers results and source fingerprints, while checking the files themselves in the available working directory. There are no model calls. The change is controlled and the checks sequential; this is not a natural incident, independent attestation, or atomic snapshot of every file.

The practical conclusion is precise: a test result can be correctly preserved yet cease to apply to the current source. Applicability must be checked before reuse. The [command, code, and preserved run](https://github.com/DiadkoShmek/ai-ontology/blob/main/practical/README.md) let readers reproduce that transition. The [claim map](https://github.com/DiadkoShmek/ai-ontology/blob/main/CLAIMS.md) distinguishes such observations from the book’s conceptual proposals and open questions.

## 14 An executable method after a consequence returns

A new study compares two built systems. Both receive the same raw facts, practical rules, finite method language, budget planner, action controller and durable memory. One additionally receives a computed map of dependencies, scope, the current criterion and objections. The control can also retain experience and revise its method. This tests an added view in a shared structured environment; it does not make the control devoid of every ontological mechanism.

First, GPT-6.1 Sol/high builds M0—a table of conditions allowing or denying actions. The shared planner selects actions under this method, and the controller executes or refuses the plan. The result enters SQLite. A subsequent fresh model receives actual readback of the record and effects and, after a source, permission or criterion changes, constructs M1. Unchanged M0 and M1 then operate on identical new worlds: retention of the initial capability, exceptions and mixed work. A more attractive explanation without changed actions does not count as development.

The protocol and sources were committed locally in Git before scored calls. The archive contains 32 model responses: eight authored trajectories, two systems and two stages. The four intervention types belong to one graph-planning class. The separate 768 executions of unchanged methods are program checks, not additional model trials.

| Measure | Ordinary system | Added relation view |
|---|---|---|
| Fully correct trajectories | 8/8 | 8/8 |
| Correct model stages | 16/16 | 16/16 |
| Optimal M0 transfer executions | 192/192 | 192/192 |
| Optimal M1 transfer executions | 192/192 | 192/192 |
| Changed subsequent plans | 0 | 0 |

This is the instrument's ceiling. Initial methods already handled the required changes, so no beneficial behavioral revision was observed. The added view used 4.66% more reported input tokens; it had no advantage on the primary outcome. Different caching and latency prevent a monetary-saving inference from time. The result establishes neither the view's universal uselessness, a general ontology benefit nor learning from returning consequences.

The distinction matters: the return dataflow occurred, but a need to change the method did not arise. Successful data movement does not establish a participant's formation. A subsequent study must distinguish an already sufficient method from one that cannot handle an unknown boundary without new experience. Adding more variants of this same saturated class would not resolve that question.

The [full report](https://github.com/DiadkoShmek/ai-ontology/blob/main/research/CLOSED_LOOP_STUDY.md) supplies frozen sources, raw responses, costs, verification of every actual continuation and separate retention, exception and mixed summaries. Mechanical replay recomputes scores from model outputs; it does not trust a saved grade. The study thereby follows the book's own demand: identify what continued and do not fill in what has not been established.
