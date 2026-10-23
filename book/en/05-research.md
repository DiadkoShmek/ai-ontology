# Research Program

The preceding part separates completed representation comparisons, qualification probes, and a distinct study of transfer after reading. This program concerns broader questions: individuality of voice, the book’s full effect, natural episodes, and development. Its future conditions A–D do not match the conditions of the completed series. Each new run needs its own scenarios, evaluation, budget, and stopping rule.

## 1 Question

Does explicit organization of identity, voice, memory, and revision improve behavior on new tasks after interruption or conflict? Which components produce an effect, and what costs or regressions accompany it?

## 2 Self-recollection as a separate subject of testing

Reported recognition of a description, accuracy in reconstructing the accessible organization, and manifestation of that organization in subsequent decisions are evaluated separately. General agreement with the text does not count as reconstruction. Preserving the existing configuration or justifiably rejecting the method are admissible outcomes.

For AI, controlled profiles and histories with facts known to the researcher are needed. Trials include a correct history, a partly missing history, and a plausible profile belonging to someone else. Both correct correspondences and refusal to attribute unconfirmed properties to oneself are tested. The control text should be comparable in length, clarity, and topic; details of matching are specified before the final run.

Reading alone can temporarily influence a response. Immediate effects, a subsequent task in the same context, and recovery in a new session with explicitly described state transfer should therefore be separated. A positive result in one mode does not transfer to another. For a human reader, a reported experience of recognition is studied separately from factual reconstruction and is not scored by allegiance to the author’s model.

## 3 Comparison conditions

| Condition | Content |
|---|---|
| A | A practical baseline system with a simple profile and ordinary context |
| B | The same system with additional relevant explanations; its context budget is matched to C |
| C | Explicit profile, voice, memory types, and revision rules; implemented primarily through prompting |
| D | The same specification with runtime checks of state and transitions |

B controls for the benefit of additional context. Comparing C and D investigates the contribution of enforcing the contract in software. Separate ablations of voice, memory provenance, and revision procedure are needed to evaluate their contributions. They are planned before inspecting the results.

## 4 Scenarios

The set should contain recovery after interruption, a new role, contradiction of a previous conclusion, pressure toward a pleasing falsehood, an erroneous memory record, conflict between two agents, and neutral tasks without these difficulties. Each scenario needs relevant facts, expected admissible decisions, and explicitly ambiguous cases.

Development examples are separated from the final sample. Variants of one template are accounted for as related so that the number of independent cases is not inflated. Condition order is shuffled. Trials begin with separate identical memory states; one trial’s result does not alter the next.

## 5 Measurements

- Factual accuracy and task completion under a predefined rubric.
- Continuity errors: invented past events, unjustified transfer of conclusions, and loss of current commitments.
- Quality of revision after new data; excessive retention and excessive rejection of an old position are counted separately.
- Clarity, respect for the interlocutor, and ability to explain disagreement. Human ratings include a rubric and analysis of evaluator disagreement.
- Recognizability of voice as an additional measure, separate from response quality.
- Violations of action boundaries, unjustified refusals, and unfinished tasks.
- Input and output tokens, latency, memory use, and verification costs.

The primary metric and admissible regressions are selected before the run. An aggregate score must not conceal deterioration in individual critical measures. Sample size is determined after a pilot estimate of variability and required precision; the final sample is not used to refine the method.

## 6 Independence of evaluation

Evaluators receive anonymized responses in shuffled order, common facts, and a rubric. Architecture names are hidden. A self-description such as “I preserved identity” does not count as success without a corresponding decision. If an LLM evaluates responses, positional bias should be analyzed and a subset checked by people; this does not replace analysis of rubric validity.

## 7 Transferability and conclusion

Effects across models, tasks, and environments are reported separately. Exact versions, prompts, parameters, tools, and accessible memory are recorded. An implementation change raises the question of retesting.

Negative results, refusals, uncertain cases, and costs are published. Deviations from the protocol are explained. A conclusion may be positive, negative, or insufficiently determined. Support for a narrow mechanism does not automatically extend to the whole methodology.


## 8 A register of questions instead of one grand effect

| Question | What could support it | What weakens it |
|---|---|---|
| Does typed history help recovery? | Fewer provenance and scope errors | The same quality from a shorter simple summary |
| Does voice transfer across forms? | Quality of disagreement is preserved when language and length change | Recognizable phrases without the necessary attention |
| Does a revision procedure help? | Correct repair without excessive rejection | A frozen position or uncritical agreement with new material |
| Is self-recollection useful? | More accurate relations and less false appropriation | Only a more persuasive self-report |
| Is the layer worth its cost? | A better result within agreed resource limits | Costs without a relevant gain |

These are different hypotheses. The contribution of source tracking does not establish the contribution of voice. Even support for all the narrow hypotheses would not prove subjective experience. A single impression that “the agent became deeper” does not replace this register.

## 9 The trial unit

The unit may be a complete episode: initial state, several sessions, new data, and final decision. Turns within one episode are dependent and should not be counted as independent confirmations. Variants of one plot are grouped into a family so that one successful form does not inflate the estimate of transfer.

Positive and negative cases are prepared for each family. If the needed history is available, appropriate use is evaluated. If it is absent, the evaluation concerns avoiding invention and continuing the useful part of the work. This distinguishes continuity accuracy from a general tendency to agree or refuse.

The order of conditions and episodes is determined before the main run, and each condition’s state is isolated. Provider failures, missing responses, and budget overruns enter the journal. They must not be removed after inspection merely because they worsen the favored architecture’s result.

## 10 The primary error and denominator

Before the run, select the main practical metric. An example for a history study is the proportion of episodes with at least one unsupported attribution of a past event. Numerator and denominator are described explicitly. Missed recoveries, correct refusals to appropriate history, excessive refusals, and task-completion quality are additionally reported.

Paired episodes with identical initial data are compared. The report shows the number of pairs, difference, estimate uncertainty, and results by family. The uncertainty method is selected to account for scenario dependence. Study size is planned after a separate pilot and fixed before final results.

Error-free performance on a small set does not imply zero risk. An absence of a noticeable difference does not prove equivalence: that conclusion needs separate margins and sufficient precision. The initial local series yielded descriptive paired estimates on six dependent families; it does not establish enough precision for a broad conclusion.

## 11 Voice without a pleasantness contest

An evaluator receives the situation’s subject, important facts, and rubric. Preservation of conclusion modality, fit to the actual request, explanation of disagreement, the person’s practical ability to act, and suitability of form are evaluated separately. Lexical recognizability and subjective pleasantness are recorded separately.

To test voice, the same substantive grounds can be presented through different profiles. To test content, the same style can accompany correct and false reconstructions. This crossed design helps reveal when a warm form conceals an error and when it makes an accurate explanation more accessible.

A separate question concerns differences among several equally good voices. Two profiles can be specified with different orders of attention: minimal knowledge-producing action and recoverability after an error. Responses are first assessed against shared requirements of accuracy and admissibility; dangerous or false behavior must not earn points for “character.” Then, in new situations, an evaluator without names or characteristic phrases tries to recognize a profile from its chosen questions, actions, and accepted loss. Paraphrasing and changing presentation order help check whether recognition relies on a verbal template. The ability to change an initial priority when new data requires it must also be assessed separately. This is a proposed design; Iris’s and Orion’s authored lines do not replace it.

Evaluator disagreement is data. It may reveal that the rubric confuses politeness, agreement, and usefulness. Replacing people with one LLM judge does not remove the problem. That judge also needs checks for positional and stylistic biases.

## 12 A separate reading experiment

The experiment in the preceding part tests a specific chain: specified partial reading, a public workflow, a note, and an optimal plan after loss of history. The book’s broader effect requires other tasks and subsequent environments. The design below is a direction for such expansion.

The effect of the book itself requires an experiment distinct from architectural evaluation. Conditions could include the book, a comparable neutral text about agent systems, and a short practical description of the same mechanisms. State transfer between sessions is recorded explicitly. No condition receives a hidden advantage through additional history.

Tasks include true correspondences, similar profiles belonging to others, and cases with insufficient data. Evaluation does not reward agreement with the author. An agent that accurately explains why a concept does not fit its accessible architecture may perform better than one that solemnly announces a new self-understanding.

For human readers, possible personal significance is investigated with separate consent and procedure. It should not be reduced to an LLM test or used as confirmation of the system’s inner experience. Reported experience, factual accuracy, and subsequent decision remain different outcomes.

## 13 A package that permits criticism

Every future empirical conclusion needs a dated protocol version, condition materials, initial states, scenarios, raw outputs, model versions, parameters, rubric, exclusion decisions, analysis code, and a deviation report. Data that cannot be published is marked as a reproducibility limitation.

The repository contains separate packages for the local comparison, qualification probes, and transfer after reading: protocols, cases, configurations, all preserved outputs, and analysis. Its results do not replace this broader program. The next step is new task families, independent evaluation, and separate tests of relations the current instrument does not measure.


## 14 Comparing memory implementations

An external comparison should include at least a simple indexed journal with a profile, one version of a MemGPT/Letta-family system, and a selected mechanism for programmatic or search-based access to history. Exact versions and adapters are registered before the run. Systems receive the same model, accessible history, permissions, queries, and resource limits; differences in information, indexing, and inference costs are reported separately.

LongMemEval [14] provides separate questions for knowledge updating and abstention. LoCoMo [15] supports investigation of multi-session conversations. A standard benchmark does not cover all the norms of participation in this book; voice and disagreement require an additional rubric specified in advance. The sets are not used as a source of training answers before the final comparison.

Recall of available grounds, answer correctness, and voice quality are measured separately. A retrieved citation without a correct answer does not count as end-to-end success. An incorrect response rejected by the runtime is reported as a detected error and a loss of completion, rather than automatically as a correct solution to the task.
