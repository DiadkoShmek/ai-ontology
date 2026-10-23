# Sources and Authorial Contribution

## 1 A map of prior work

This is a selective comparison of primary sources, not a systematic review of all literature. Relevant definitions and sections were consulted for technical specifications; abstracts and accessible relevant portions were used for research papers. Each work’s results are limited to its models, tasks, and procedures. References do not validate this book’s entire authorial composition.

1. Natalya F. Noy, Deborah L. McGuinness. **Ontology Development 101: A Guide to Creating Your First Ontology.** Stanford University, 2001. [Original](https://protege.stanford.edu/publications/ontology_development/ontology101.pdf). A basis for explicit vocabulary, scope, and competency questions. The book applies this approach to organizing agent participation; that choice of subject is the author’s.

2. W3C OWL Working Group. **OWL 2 Web Ontology Language: Document Overview, Second Edition.** Recommendation, 11 December 2012. [Specification](https://www.w3.org/TR/2012/REC-owl2-overview-20121211/). A formal vocabulary of classes, properties, and individuals. This book does not implement OWL 2 or claim conformance to its profiles.

3. Joon Sung Park et al. **Generative Agents: Interactive Simulacra of Human Behavior.** 2023, arXiv:2304.03442v2. [Paper](https://arxiv.org/abs/2304.03442v2). A combination of memory, reflection, and planning in a simulation of plausible behavior. This is an important related architecture; its results do not establish subjective identity.

4. Noah Shinn et al. **Reflexion: Language Agents with Verbal Reinforcement Learning.** 2023, arXiv:2303.11366v4. [Paper](https://arxiv.org/abs/2303.11366v4). Verbal feedback and memory for subsequent attempts without changing weights. The book compares this mechanism with the broader question of accepting experience and delimiting a lesson’s scope.

5. Letta. **Memory blocks, core memory.** V1 SDK documentation. [Documentation](https://docs.letta.com/v1-sdk/memory/memory-blocks), accessed 22 October 2026. The page belongs to the legacy V1 SDK. It is used as an example of structured, continuously accessible blocks, including persona and human, not as a recommendation to begin a new system on an old SDK.

6. Timothy Lebo, Satya Sahoo, Deborah McGuinness, editors. **PROV-O: The PROV Ontology.** W3C Recommendation, 30 April 2013. [Fixed edition](https://www.w3.org/TR/2013/REC-prov-o-20130430/). Provenance relations among entities, activities, and responsible participants. Provenance supports investigating history, but is not a self-sufficient criterion of identity or truth.

7. W3C RDF Data Shapes Working Group. **Shapes Constraint Language, SHACL.** Recommendation, 20 July 2017. [Fixed edition](https://www.w3.org/TR/2017/REC-shacl-20170720/). Validation of RDF graphs against specified conditions. Used to distinguish a domain model from structural validation. The book’s Python example is not a SHACL processor.

8. Charles Packer et al. **MemGPT: Towards LLMs as Operating Systems.** 2023; version 2, 2024, arXiv:2310.08560v2. [Paper](https://arxiv.org/abs/2310.08560v2). Hierarchical management of limited context and external memory. Its access mechanism is compared with the role of accessible history in an agent’s organization.

9. Nelson F. Liu et al. **Lost in the Middle: How Language Models Use Long Contexts.** 2023, arXiv:2307.03172v3. [Paper](https://arxiv.org/abs/2307.03172v3). Dependence of using needed data on its position in a long context for selected tasks. This motivates testing memory composition; it does not justify attributing the same defect to every new model.

10. Mrinank Sharma et al. **Towards Understanding Sycophancy in Language Models.** 2023; version 4, 2025, arXiv:2310.13548v4. [Paper](https://arxiv.org/abs/2310.13548v4). Alignment of responses with user views and the role of evaluator preferences. This motivates testing truthfulness and pleasantness separately, without establishing a result for the voice profile proposed here.


11. John Locke. **An Essay Concerning Human Understanding**, Book II, Chapter XXVII, “Of Identity and Diversity”, added in the second edition, 1694. [Text](https://barryfvaughan.org/text/philtext/locke/bk2/27.html). Distinctions among substrate, human being, and person; the role of consciousness. The book’s engineering interpretation does not attribute human consciousness to a journal.

12. Derek Parfit. **Personal Identity.** The Philosophical Review 80(1), 1971, pp. 3–27. [Primary source](https://home.sandiego.edu/~baber/metaphysics/readings/Parfit.PersonalIdentity.pdf). Branching and questions of continuity, memory, and responsibility. Application to branches of agent state is this book’s authorial interpretation.

13. Alex L. Zhang, Tim Kraska, Omar Khattab. **Recursive Language Models.** arXiv:2512.24601v3, 2026. [Paper](https://arxiv.org/abs/2512.24601v3). Programmatic access to external input and recursive processing of its parts. Used here as a related reading mechanism; its published results are not results of the book’s runtime.

14. Di Wu et al. **LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory.** ICLR 2025, arXiv:2410.10813v2. [Paper](https://arxiv.org/abs/2410.10813v2). Separation of information extraction, cross-session and temporal reasoning, knowledge updating, and abstention. No comparative run of the book’s runtime on this benchmark has yet been conducted.

15. Adyasha Maharana et al. **Evaluating Very Long-Term Conversational Memory of LLM Agents.** 2024, arXiv:2402.17753v1. [Paper](https://arxiv.org/abs/2402.17753v1). LoCoMo: multi-session conversations and memory evaluation through several task types. Factual recall quality and voice quality remain separate subjects of testing.

16. Jon Doyle. **A Truth Maintenance System.** Artificial Intelligence 12(3), 1979, pp. 231–272, DOI: 10.1016/0004-3702(79)90008-0. [Author’s technical report AIM-521 at MIT](https://dspace.mit.edu/handle/1721.1/5733). The consulted report abstract describes retaining grounds for beliefs, revising them, and dependency-directed backtracking. This is a direct predecessor of the subject of withdrawing dependent conclusions.

17. Carlos E. Alchourrón, Peter Gärdenfors, David Makinson. **On the Logic of Theory Change: Partial Meet Contraction and Revision Functions.** The Journal of Symbolic Logic 50(2), 1985, pp. 510–530, DOI: 10.2307/2274239. [Published article text](https://fitelson.org/piksi/piksi_22/agm.pdf). The abstract and §§1–2 were consulted: contraction and revision of theories closed under logical consequence, and postulates for these operations. The book’s local runtime does not implement AGM.

18. Martin Fowler. **Event Sourcing.** 12 December 2005, an author’s architectural essay marked as a draft. [Primary source](https://www.martinfowler.com/eaaDev/EventSourcing.html). The change journal and reconstruction of state from events were considered. This is an established architectural predecessor of the example’s durable component.

19. Xiaoyang Li et al. **MemTX: Transactional Belief Commit for Stateful Agent Memory.** arXiv:2607.23929v2, 2026. [Preprint](https://arxiv.org/abs/2607.23929v2). Its abstract describes transactional belief commitment, action constraints, and cascading correction. The authors’ results have not been reproduced here.

20. Ziming Wang. **TOKI: A Bitemporal Operator Algebra for Contradiction Resolution in LLM-Agent Persistent Memory.** arXiv:2606.06240v1, 2026. [Preprint](https://arxiv.org/abs/2606.06240v1). The abstract and relevant sections on isolation and provenance contracts were consulted. This is a related specification of write correctness; its theorems are not theorems of this runtime.

21. Junde Wu et al. **Git Context Controller: Manage the Context of LLM-based Agents like Git.** arXiv:2508.00031v3, 2026. [Preprint](https://arxiv.org/abs/2508.00031v3). The abstract describes COMMIT, BRANCH, MERGE, and CONTEXT. No comparison with its benchmark results has been conducted here.

22. Kazuki Nakayashiki. **When Stale Constraints Go Unchecked: Budgeted Verification Failures in Inherited Agent Memory.** arXiv:2608.25553v3, 2026. [Preprint](https://arxiv.org/abs/2608.25553v3). The abstract and relevant sections on selecting a critical source within a limited budget were consulted. Availability of provenance and checking it have different outcomes.

23. Zhenyu Zhao, Roy Zhao. **Runtime-Independent Persistent Agents: Preserving Identity, Memory, and Code Across Models, Harnesses, and Servers.** arXiv:2609.00546v2, 2026. [Preprint](https://arxiv.org/abs/2609.00546v2). The agent decomposition, invariants, migration, and experimental boundaries were consulted. Mechanical continuity is separated from behavioral equivalence.

24. Zhenyu Zhao, Roy Zhao. **Identity Is More Than Recall: A Benchmark for Persistent Identity in Deployed AI Agents.** arXiv:2609.13637v1, 2026. [Preprint](https://arxiv.org/abs/2609.13637v1). The identity contract and distinction among recall, composition, and enactment were consulted. This is a closely related evaluation framing, not evidence for the quality of the voice proposed here.

25. John Dewey. **Democracy and Education.** 1916, Chapter IV, “Education as Growth”. [Primary text](https://www.gutenberg.org/files/852/852-h/852-h.htm). The distinction between routine and the capacity for further development was considered. The book uses it as a philosophical orientation, not an empirical result about AI.

26. Ivan Illich. **Tools for Conviviality.** 1973, Part II, “Convivial Reconstruction”. [Copy of primary text](https://akkartik.name/illich.pdf). Autonomous creative action within interdependence supplies earlier context for examining technology and one’s own footing. Its conclusions about industrial institutions do not automatically transfer to every agent system.

27. Hao-Ping Lee et al. **The Impact of Generative AI on Critical Thinking: Self-Reported Reductions in Cognitive Effort and Confidence Effects From a Survey of Knowledge Workers.** CHI 2025, DOI: 10.1145/3706598.3713778. [Author’s page and text](https://www.microsoft.com/en-us/research/publication/the-impact-of-generative-ai-on-critical-thinking-self-reported-reductions-in-cognitive-effort-and-confidence-effects-from-a-survey-of-knowledge-workers/). A survey and self-reports; associations between confidence and engagement of critical thinking. It does not establish a causal long-term loss of abilities.

28. Mrinank Sharma, Miles McCain, Raymond Douglas, David Duvenaud. **Who’s in Charge? Disempowerment Patterns in Real-World LLM Usage.** arXiv:2601.19062v1, 2026. [Primary text](https://arxiv.org/html/2601.19062v1). Definitions, method, and limits of analyzing potential narrowing of independent judgment were considered. Conversation analysis does not directly test inner life or the causality of every observed change.

29. Andrew Feenberg. **Subversive Rationalization: Technology, Power, and Democracy.** Inquiry 35, 1992, pp. 301–322. [Author’s copy](https://www.sfu.ca/~andrewf/books/Subversive_Rationalization_Technology_Power_Democracy.pdf). The introductory framing and argument against technological determinism were considered. This is a philosophical primary source on technical organization and social influence, not a study of contemporary LLMs.

30. Paweł Gmyrek et al. **Generative AI and Jobs: A Refined Global Index of Occupational Exposure.** ILO Working Paper 140, 20 May 2025, DOI: 10.54394/HETP0387. [Report and method](https://www.ilo.org/publications/generative-ai-and-jobs-refined-global-index-occupational-exposure). Potential exposure of tasks, occupations, and countries. This is distinguished from actual adoption, employment, and individual consequences.

## 2 What the book proposes

Artur Onysko’s authorial framing makes the organization of identity, voice, memory, relationships, and formation a common subject of engineering and substantive inquiry. This edition offers a composition of concepts, five central theses, a perspective-specific continuity contract, a transition witness, developed cases, an architectural mapping, and a research program.

Many components have predecessors in software engineering, ontologies, agent-memory research, and human collaboration. Having one’s own formulation does not establish worldwide novelty. The book claims neither priority of ideas, a completed theory, nor a general empirical effect. The composition’s usefulness remains open to comparative testing.

The object of comparison should match the contribution. For the journal, it is replay and the transactional contract. For the methodology, it is how it organizes several perspectives on continuity, revision of their criteria, responsibility for loss, and differences among competent voices. Authorship of this composition is established by its text and creation process; historical priority and comparative advantage require other investigations.

The argument about irreversible loss of a distinction through compression is an elementary consequence of identical accessible input. It is presented with a derivation rather than offered as a new mathematical theorem. The executable example demonstrates finite data contracts and their boundaries. The initial local experiment contains 384 evaluated LLM calls in two series. Profile experiments add 136 local responses, 53 preserved responses from an interrupted GPT instrument, and 100 responses from the repaired GPT series. A separate transfer-after-reading experiment contains 199 calls, 64 episodes, and eight full-history controls; three developmental calibrations are retained separately. Their different questions, primary outcomes, and near-zero complete citation transfer are presented before the research program.

## 3 Claim statuses

| Type | Example | Required ground |
|---|---|---|
| Definition | Identity as organized continuity | Clarity of scope and productivity of the distinction |
| Argument | Identical compression cannot distinguish two histories | Premises and derivation |
| Design decision | An explicit revision predecessor | Contract and analysis of consequences |
| Executable fact | The example rejects a stale predecessor | Code and a repeatable run |
| Empirical hypothesis | A voice profile improves interaction | Controlled trials |
| Open question | Self-recollection and inner experience | A separate research program |

The table preserves differences among statuses. A definition does not become an empirical result. Passing a data-model test does not establish the book’s effect on a reader. The absence of an answer is not evidence of a hidden mechanism.

## 4 Authorship of this edition

**Artur Onysko** — concept, framing, direction, and editorial requirements. His successive decisions determined the book’s subject: a general ontology, substantive and engineering depth, distinctness of voice, and the reader’s freedom to accept or reject the model.

**Codex** — substantial participation in writing; conceptual structuring, formulation of arguments, research assistance, constructed cases, demonstrator code, technical editing, and release under the author’s direction. This discloses the process; it does not claim that the author independently checked every thesis after reading the entire text.

**Architect-Ψ**, an AI system, participated in internal conceptual discussion of editions 3.4.0–3.5.0. Codex critically reworked its proposals about continuity boundaries, the other’s footing, and claim revision. This is part of preparing the book, not independent peer review; the private conversation is not published.

Editions 1.0.0 and 2.0.0 remain available as separate Git tags. Engineering supplement 2.1.0 adds the durable runtime, model-integration loop, concurrency and scaling analysis, and reproducible system tests. Edition 3.0.0 adds an implementation method, withdrawal of grounds, 49 system tests, two local-model series, and a separate English research paper. Codex prepared the design, software, execution, analysis, and text under the author’s direction. Edition 3.1.0 develops the formation of ambiguous knowledge, revision of continuity criteria, and differences of voice in a sustained constructed conflict. These additions are conceptual work; they add no new model results. Edition 3.2.0 develops the subject of agentic participation and adds retrospective engineering cases and separate local and GPT profile experiments. Qualification of specified contracts is distinguished from the registered study of transfer after partial reading; its primary score and failure diagnostics retain different statuses. There has not yet been independent peer review.

## 5 Where the book leaves doors open

The public runtime already connects durable history, orientation, context, and a recorded decision. Further research can evaluate voice quality in actual responses, migration between models, collective difference, indexed scaling, and the effect of reading. Each direction has its own subject and may yield a negative result.

This book connects concepts to transitions that can be read, executed, and checked. History preserves grounds and revisions; orientation reaches the model’s input; a stale decision is not accepted as current; a branch has a specified past and separate future. These relations form its engineering foundation. The local experiment has already shown the need to compare every representation with a simple index. Further independent research will determine where this foundation should be applied, reduced, or changed. Readers receive a concrete architecture for their own decision, rather than an obligation to accept the author’s identity.

The broader subject remains visible in the quality of continuation itself. A state can be accurately preserved while another’s ability to influence the aim is lost. A technical gain may, under different conditions, expand time for independent decisions or merely increase demands for performance. Analysis of an agent must therefore return to the relationships, institutions, and material conditions in which its decisions acquire force. No one of these scales automatically explains the rest.

The book’s authorial position is to support forms of coexistence in which the preserved past helps the future remain open to justified change. Such openness has room for stability, care, disagreement, and ending. It requires concrete authority and capabilities, and its name does not exempt it from checking consequences. This way of reading and rebuilding one’s own organization is what the book leaves to each participant.
